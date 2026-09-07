"""Read-only, single-plant analytics. This module has no third-party dependencies."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import math
from pathlib import Path
import re
import sqlite3


@dataclass(frozen=True)
class Reading:
    timestamp: datetime
    usage_kwh: float
    co2_tco2: float
    day_of_week: str
    is_weekend: int
    load_type: str


def _date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Dates must use YYYY-MM-DD.")
    return date.fromisoformat(value)


def _totals(rows):
    return {
        "intervals": len(rows),
        "total_kwh": round(math.fsum(r.usage_kwh for r in rows), 6),
        "total_co2_tco2": round(math.fsum(r.co2_tco2 for r in rows), 6),
    }


class EnergyDataset:
    """Load validated interval readings without changing the source database.

    A timestamp identifies one interval for one plant. Exact duplicate records
    are collapsed; differing records at the same timestamp are rejected.
    """

    def __init__(self, db_path="ems.db"):
        path = Path(db_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Energy database not found: {path}")
        self.path = path
        by_timestamp = {}
        self.stored_rows = 0
        connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
        try:
            records = connection.execute(
                "SELECT timestamp, usage_kwh, co2_tco2, day_of_week, "
                "is_weekend, load_type FROM energy_readings"
            )
            for number, raw in enumerate(records, start=1):
                self.stored_rows += 1
                try:
                    timestamp = datetime.strptime(raw[0], "%d/%m/%Y %H:%M")
                    usage, co2 = float(raw[1]), float(raw[2])
                    if not all(math.isfinite(n) and n >= 0 for n in (usage, co2)):
                        raise ValueError("energy and carbon must be finite and nonnegative")
                    if timestamp.minute % 15:
                        raise ValueError("timestamp must fall on a 15-minute boundary")
                    if raw[4] not in (0, 1):
                        raise ValueError("is_weekend must be 0 or 1")
                    if not isinstance(raw[3], str) or not raw[3].strip():
                        raise ValueError("day_of_week is required")
                    if not isinstance(raw[5], str) or not raw[5].strip():
                        raise ValueError("load_type is required")
                    reading = Reading(timestamp, usage, co2, raw[3], raw[4], raw[5])
                except (TypeError, ValueError) as error:
                    raise ValueError(f"Invalid energy reading at row {number}: {error}") from error
                previous = by_timestamp.get(timestamp)
                if previous is not None and previous != reading:
                    raise ValueError(f"Conflicting readings at {timestamp.isoformat()}; resolve the source data.")
                by_timestamp[timestamp] = reading
        except sqlite3.DatabaseError as error:
            raise ValueError("Cannot read energy_readings; check the database and documented schema.") from error
        finally:
            connection.close()
        self.readings = sorted(by_timestamp.values(), key=lambda r: r.timestamp)
        if not self.readings:
            raise ValueError("The energy_readings table is empty.")

    def audit(self):
        return {
            "stored_rows": self.stored_rows,
            "unique_intervals": len(self.readings),
            "exact_duplicates_removed": self.stored_rows - len(self.readings),
            "first_timestamp": self.readings[0].timestamp.isoformat(),
            "last_timestamp": self.readings[-1].timestamp.isoformat(),
            "interval_minutes": 15,
            "timestamp_policy": "Naive timestamps; calendar-date filters; no boundary shifts.",
        }

    def _range(self, start, end):
        return [r for r in self.readings if start <= r.timestamp.date() <= end]

    def snapshot(self, start_date, end_date, top_n=5):
        start, end = _date(start_date), _date(end_date)
        if start > end:
            raise ValueError("start_date must be on or before end_date.")
        if not isinstance(top_n, int) or isinstance(top_n, bool) or not 1 <= top_n <= 100:
            raise ValueError("top_n must be an integer from 1 to 100.")
        rows = self._range(start, end)
        if not rows:
            raise ValueError("No readings in the selected period; run audit to see available dates.")
        days = (end - start).days + 1
        expected = days * 96
        daily = defaultdict(list)
        loads, hours, weekstatus = defaultdict(list), defaultdict(list), defaultdict(list)
        for row in rows:
            daily[row.timestamp.date().isoformat()].append(row)
            loads[row.load_type].append(row)
            hours[row.timestamp.hour].append(row)
            weekstatus["weekend" if row.is_weekend else "weekday"].append(row)
        totals = _totals(rows)
        total_kwh = totals["total_kwh"]
        previous_end = start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=days - 1)
        previous_rows = self._range(previous_start, previous_end)
        previous_totals = _totals(previous_rows) if previous_rows else None
        warnings = []
        if self.stored_rows != len(self.readings):
            warnings.append("Exact duplicate source rows were collapsed before calculating totals.")
        if len(rows) != expected:
            warnings.append("The selected calendar period is incomplete; missing intervals are not imputed.")
        comparable = len(rows) == expected and len(previous_rows) == expected
        if not comparable:
            warnings.append("Period percentage changes are unavailable because one or both periods lack full coverage.")
        changes = {}
        for metric in ("total_kwh", "total_co2_tco2"):
            baseline = previous_totals[metric] if previous_totals else 0
            changes[metric] = round((totals[metric] / baseline - 1) * 100, 4) if comparable and baseline else None
        return {
            "period": {"start": start.isoformat(), "end": end.isoformat(), "calendar_days": days},
            "data_quality": {**self.audit(), "selected_intervals": len(rows),
                             "expected_intervals": expected,
                             "coverage_percent": round(len(rows) / expected * 100, 4),
                             "observed_days": len(daily), "warnings": warnings},
            "kpis": {**totals,
                     "avg_kwh_per_observed_day": round(total_kwh / len(daily), 6),
                     "avg_kwh_per_interval": round(total_kwh / len(rows), 6),
                     "max_interval_kwh": max(r.usage_kwh for r in rows),
                     "co2_kg_per_kwh": round(totals["total_co2_tco2"] * 1000 / total_kwh, 6) if total_kwh else None},
            "daily": [{"date": key, **_totals(group)} for key, group in sorted(daily.items())],
            "load_types": [{"load_type": key, **_totals(group)} for key, group in sorted(loads.items())],
            "weekday_weekend": [{"label": key, **_totals(group)} for key, group in sorted(weekstatus.items())],
            "hourly_profile": [{"hour": key, **_totals(group),
                                "avg_kwh_per_interval": round(math.fsum(r.usage_kwh for r in group) / len(group), 6)}
                               for key, group in sorted(hours.items())],
            "top_peaks": [{"timestamp": row.timestamp.isoformat(), "usage_kwh": row.usage_kwh,
                           "co2_tco2": row.co2_tco2, "load_type": row.load_type}
                          for row in sorted(rows, key=lambda r: (-r.usage_kwh, r.timestamp))[:top_n]],
            "previous_period": {"start": previous_start.isoformat(), "end": previous_end.isoformat(),
                                "totals": previous_totals, "percent_change": changes,
                                "coverage_percent": round(len(previous_rows) / expected * 100, 4)},
            "carbon_basis": "CO2 totals are the supplied dataset column, not an independently verified Scope 1/2/3 inventory.",
        }


def render_markdown(snapshot):
    """Render a deterministic report, including data quality and measurement units."""
    period, kpis, quality = snapshot["period"], snapshot["kpis"], snapshot["data_quality"]
    lines = ["# EMS Co-Pilot | Energy & carbon report", "",
             f"Period: **{period['start']} to {period['end']}** (inclusive)", "",
             "## Performance", "", "| Metric | Value |", "| --- | ---: |",
             f"| Energy | {kpis['total_kwh']:,.2f} kWh |",
             f"| Dataset CO2 | {kpis['total_co2_tco2']:,.4f} tCO2 |",
             f"| Peak 15-minute energy | {kpis['max_interval_kwh']:,.2f} kWh |",
             f"| Average per observed day | {kpis['avg_kwh_per_observed_day']:,.2f} kWh |",
             f"| Interval coverage | {quality['selected_intervals']:,} / {quality['expected_intervals']:,} ({quality['coverage_percent']:.2f}%) |",
             "", "## Data quality", "",
             f"Source: {quality['stored_rows']:,} rows; {quality['unique_intervals']:,} unique intervals; "
             f"{quality['exact_duplicates_removed']:,} exact duplicates excluded.", ""]
    lines.extend(f"- {warning}" for warning in quality["warnings"])
    lines += ["", snapshot["carbon_basis"], "", "## Daily totals", "",
              "| Date | Intervals | Energy (kWh) | Dataset CO2 (tCO2) |", "| --- | ---: | ---: | ---: |"]
    lines.extend(f"| {r['date']} | {r['intervals']} | {r['total_kwh']:,.2f} | {r['total_co2_tco2']:,.4f} |" for r in snapshot["daily"])
    lines += ["", "## Peak intervals", "", "| Timestamp | Energy (kWh) | Load type |", "| --- | ---: | --- |"]
    lines.extend(f"| {r['timestamp']} | {r['usage_kwh']:,.2f} | {r['load_type'].replace('|', '/')} |" for r in snapshot["top_peaks"])
    previous = snapshot["previous_period"]
    lines += ["", "## Previous period", "", f"{previous['start']} to {previous['end']}; coverage {previous['coverage_percent']:.2f}%.", ""]
    for metric, change in previous["percent_change"].items():
        lines.append(f"- {metric}: {change:+.2f}%" if change is not None else f"- {metric}: unavailable (incomplete coverage or zero baseline).")
    lines += ["", "Generated from validated local readings. Review timestamp conventions, dataset provenance, and carbon methodology before making operational decisions.", ""]
    return "\n".join(lines)
