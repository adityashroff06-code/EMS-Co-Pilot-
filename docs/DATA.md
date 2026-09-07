# Data and methodology

## Energy schema

The single-plant `energy_readings` table requires these columns; an additional `id` column is allowed and ignored:

| Column | Meaning / validation |
| --- | --- |
| `timestamp` | Naive `DD/MM/YYYY HH:MM`, on a 15-minute boundary |
| `usage_kwh` | Finite, nonnegative energy consumed during an interval |
| `co2_tco2` | Finite, nonnegative CO2 value supplied by the dataset, in tonnes |
| `day_of_week` | Nonempty source label; retained for duplicate comparison |
| `is_weekend` | Source flag, integer 0 or 1; used for weekday/weekend grouping |
| `load_type` | Nonempty source load-category label |

Timestamps identify intervals for one plant. Data with multiple plants must be separated before use; the current schema has no plant identifier. Source day/weekend labels are retained rather than silently recalculated. The engine checks required values but does not independently verify the labels or the source CO2 measurement method.

## Bundled database audit

The committed snapshot contains 210,240 energy rows: six identical copies of 35,040 unique intervals. The verified date span is `2018-01-01T00:00:00` through `2018-12-31T23:45:00`. The new engine collapses 175,200 exact duplicates in memory and rejects conflicting records at the same timestamp. It does not delete or rewrite the source database.

This resolves a material defect in the original notebook's append-on-rerun ingestion: directly summing all stored rows inflated totals sixfold. Historical generated reports may contain those inflated totals and must not be treated as corrected outputs. Regenerate reports using the current workflow.

## Calculation rules

- Dates filter the calendar date printed in each source timestamp, inclusively. No timezone conversion or interval-end shift is applied.
- Coverage assumes 96 unique intervals per calendar day and a naive 24-hour day. Timezone-aware daylight-saving datasets need a different model.
- Missing intervals are not imputed. Averages per day divide by observed days, explicitly named `avg_kwh_per_observed_day`.
- Energy is the sum of interval kWh. Peak interval energy remains kWh, not kW; multiplying by four to infer average kW would require confirming the duration and meter convention.
- CO2 totals sum the supplied `co2_tco2` column. The intensity ratio is `total_tco2 × 1000 / total_kwh`; it is unavailable when energy is zero.
- The previous period has the same number of calendar days and ends the day before the current period begins. Percent changes are unavailable if either period lacks full interval coverage or the baseline metric is zero.
- Hour-of-day averages are averages **per interval** grouped by hour, not hourly energy totals. JSON also provides the total kWh in each hour group.

## Carbon-intensity snapshot

`ems.db` also contains 120 rows in `carbon_intensity`. The original notebook described these as a Canadian Carbon Intensity Database workbook dated October 2024 and used revenue-based proxies with an assumed annual revenue. The source workbook is not committed, several values are stored as text, and the original code's USD labeling is not enough to establish the correct currency basis.

The current reporting engine deliberately does not turn these unverified sector proxies into plant Scope 1/2/3 estimates. Establish the source edition, currency, reference year, sector mapping, system boundary and activity data before reintroducing that calculation. Do not combine the supplied dataset CO2 with sector proxy estimates as if they were independently measured totals.

## Bundled assets

| Asset | Role | Current workflow |
| --- | --- | --- |
| `ems.db` | Energy and carbon-intensity snapshot | Opened read-only |
| `GHG_Protocol-revised.pdf` | Guidance document supplied with the project | Optional new PDF index |
| `chroma.sqlite3` | Historical Chroma database | Retained; not opened or migrated |
| `3d93dcea-3eb0-4773-b761-8d07150871e8-20260118T203813Z-3-001.zip` | Historical vector-segment binary files | Retained; not needed for the new index |
| `Reports-20260118T203958Z-3-001.zip` | Historical generated DOCX and text reports | Reference only; may predate duplicate correction |

No extraction of the archives is needed for the quick start. Avoid mixing a historical Chroma database with a newly generated index; corpus/model-specific collections now live under `runtime/rag/`.

## Provenance and rights

The original notebook names `Steel_industry_data.csv` and `Canadian Carbon Intensity Database (2024-10).xlsx`, but neither source file nor a complete attribution/license manifest was committed. Those filenames describe the original workflow; they do not establish redistribution rights, exact dataset revisions or measurement quality. The guidance PDF and generated archives likewise retain their existing ownership and rights.

Before distributing a derivative dataset or making audited claims, document the original download locations, version identifiers, authors, terms and any transformations. The repository's current lack of an explicit software license is separate from the rights attached to these third-party materials.
