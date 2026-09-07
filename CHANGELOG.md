# Changelog

## 0.1.0 — Reproducible demo baseline

- Extracted read-only energy analytics and reporting into a reusable Python package with a dependency-free CLI.
- Corrected sixfold duplicate inflation by explicitly collapsing exact interval duplicates while rejecting conflicts and preserving the database.
- Added coverage-aware period comparisons, explicit units, input validation and safe report exports.
- Replaced the exploratory notebook with an offline-by-default walkthrough and implemented a local dashboard callback.
- Added optional page-aware PDF retrieval, resumable corpus/model-specific indexing, bounded AI draft generation and Word export.
- Removed embedded credentials, automatic email tests and public-sharing defaults; cleared notebook outputs.
- Added regression tests, mocked provider tests, offline CI and setup, usage, architecture, methodology, contribution and security documentation.

Historical archives remain unchanged. Live provider behavior and production deployment are outside this baseline's verified scope.
