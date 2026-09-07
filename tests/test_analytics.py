import contextlib
from datetime import datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from ems_copilot import EnergyDataset, render_markdown
from ems_copilot.__main__ import main
from ems_copilot.assistant import chunk_text


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.db = Path(self.directory.name) / "energy.db"
        with contextlib.closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("CREATE TABLE energy_readings (timestamp TEXT, usage_kwh REAL, co2_tco2 REAL, day_of_week TEXT, is_weekend INTEGER, load_type TEXT)")

    def insert(self, rows):
        with contextlib.closing(sqlite3.connect(self.db)) as connection, connection:
            connection.executemany("INSERT INTO energy_readings VALUES (?, ?, ?, ?, ?, ?)", rows)

    def row(self, timestamp="01/01/2018 00:15", energy=10, carbon=0.1):
        return (timestamp, energy, carbon, "Monday", 0, "Light_Load")

    def test_duplicate_collapse_preserves_source(self):
        self.insert([self.row()] * 6 + [self.row("01/01/2018 00:30", 20, 0.2)])
        before = hashlib.sha256(self.db.read_bytes()).digest()
        dataset = EnergyDataset(self.db)
        snapshot = dataset.snapshot("2018-01-01", "2018-01-01")
        self.assertEqual(snapshot["kpis"]["total_kwh"], 30)
        self.assertEqual(snapshot["data_quality"]["exact_duplicates_removed"], 5)
        self.assertEqual(snapshot["data_quality"]["selected_intervals"], 2)
        self.assertEqual(before, hashlib.sha256(self.db.read_bytes()).digest())
        self.assertIsNone(snapshot["previous_period"]["totals"])
        self.assertIn("incomplete", " ".join(snapshot["data_quality"]["warnings"]))
        self.assertIn("30.00 kWh", render_markdown(snapshot))
        json.dumps(snapshot, allow_nan=False)

    def test_conflicting_timestamp_is_rejected(self):
        self.insert([self.row(), self.row(energy=20)])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            EnergyDataset(self.db)

    def test_invalid_rows_fail_loudly(self):
        for row in (self.row(energy=-1), self.row(carbon=float("inf")), self.row("not a timestamp"), self.row("01/01/2018 00:16")):
            with self.subTest(row=row):
                with contextlib.closing(sqlite3.connect(self.db)) as connection, connection:
                    connection.execute("DELETE FROM energy_readings")
                self.insert([row])
                with self.assertRaisesRegex(ValueError, "Invalid energy reading"):
                    EnergyDataset(self.db)

    def test_calendar_end_is_inclusive_without_shifting_midnight(self):
        self.insert([self.row("01/01/2018 23:45"), self.row("02/01/2018 00:00", 100)])
        snapshot = EnergyDataset(self.db).snapshot("2018-01-01", "2018-01-01")
        self.assertEqual(snapshot["kpis"]["total_kwh"], 10)

    def test_invalid_period_or_peak_count(self):
        self.insert([self.row()])
        dataset = EnergyDataset(self.db)
        for args in (("2018-01-02", "2018-01-01"), ("2018-1-1", "2018-01-01"), ("2020-01-01", "2020-01-02"), ("2018-01-01", "2018-01-01", 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                dataset.snapshot(*args)

    def test_complete_period_comparison_and_zero_baseline(self):
        start = datetime(2018, 1, 1)
        self.insert([self.row((start + timedelta(minutes=15 * i)).strftime("%d/%m/%Y %H:%M"), 10 if i < 96 else 20, 0)
                     for i in range(192)])
        snapshot = EnergyDataset(self.db).snapshot("2018-01-02", "2018-01-02")
        self.assertEqual(snapshot["previous_period"]["percent_change"]["total_kwh"], 100)
        self.assertIsNone(snapshot["previous_period"]["percent_change"]["total_co2_tco2"])

    def test_missing_database_is_not_created(self):
        missing = self.db.with_name("missing.db")
        with self.assertRaises(FileNotFoundError):
            EnergyDataset(missing)
        self.assertFalse(missing.exists())

    def test_empty_table_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            EnergyDataset(self.db)

    def test_cli_writes_json_and_refuses_overwrite(self):
        self.insert([self.row()])
        target = self.db.with_name("report.json")
        args = ["report", "--db", str(self.db), "--start", "2018-01-01", "--end", "2018-01-01", "--format", "json", "--output", str(target)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
        self.assertEqual(json.loads(target.read_text())["kpis"]["total_kwh"], 10)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(args)
        self.assertEqual(error.exception.code, 2)
        self.assertEqual(json.loads(target.read_text())["kpis"]["total_kwh"], 10)

    def test_chunking_bounds(self):
        self.assertEqual(chunk_text("abcdefghij", 4, 1), ["abcd", "defg", "ghij", "j"])
        self.assertEqual(chunk_text(""), [])
        for size, overlap in ((0, 0), (4, 4), (4, -1)):
            with self.assertRaises(ValueError):
                chunk_text("abc", size, overlap)


if __name__ == "__main__":
    unittest.main()
