# Architecture

## Runtime boundaries

`EnergyDataset` opens SQLite in read-only mode, validates the full source table, collapses duplicate intervals, and stores a sorted in-memory series. `snapshot` derives deterministic JSON-compatible metrics; `render_markdown` turns the same snapshot into a report. The CLI, notebook and dashboard share this implementation instead of redefining analytics functions in separate notebook cells.

| Module | Responsibility | External effects |
| --- | --- | --- |
| `ems_copilot/analytics.py` | Data validation, audit, aggregation, Markdown | Read-only database access |
| `ems_copilot/__main__.py` | CLI argument validation and report output | Creates explicitly requested report file |
| `ems_copilot/assistant.py` | Optional page-aware retrieval, AI drafts, Word export | Provider calls, local vector index and explicit exports |
| `app.py` | Optional Gradio dashboard | Local HTTP listener only when started |
| `EMS_Co_Pilot.ipynb` | Guided workflow and evidence inspection | Optional effects gated by explicit switches |

No provider SDK is imported by the offline analytics path. Optional imports are inside the functions that need them. Importing the package does not mount Drive, install dependencies, prompt for secrets, call an API, send email or start a server.

## Data quality decisions

The original database stores six exact copies of each energy interval. Deduplication is therefore explicit and reported; differing values at the same timestamp are treated as ambiguous data and stop reporting. Source data remains intact so a reviewer can reproduce the audit. Missing observations remain visible in coverage metrics. Incomplete periods do not receive misleading percentage comparisons.

The original notebook mixed experimental function redefinitions, missing external input paths, credentials and an undefined UI callback. The curated notebook now delegates to the package and executes offline by default. The original exploratory implementation is preserved in Git history, where previously committed secrets must still be considered exposed.

## Retrieval and generation

PDF text is extracted per page, divided into 1,200-character chunks with 200-character overlap, and stored with source filename, page and chunk metadata. The collection identity includes a hash of the source PDF, embedding model and chunking version. Batches skip existing IDs, allowing interrupted indexing to resume. Query embeddings use the collection's recorded model, avoiding index/query model mismatches.

The assistant receives selected analytics, quality warnings and up to ten retrieved chunks. It is instructed to ground quantities in analytics, treat retrieved text as evidence, cite pages and avoid inventing savings or compliance claims. These instructions reduce unsupported output but do not guarantee correctness. Every answer includes the retrieved source records for human review and an explicit review-required flag.

## Limitations

- Single-plant, in-memory analytics; no ingestion service, user accounts or multi-tenant isolation.
- Timestamp uniqueness assumes one observation per plant per 15-minute boundary. Time zones, daylight-saving transitions and meter-specific interval-end conventions need explicit extensions.
- Source labels and emissions methodology are not independently verified. Carbon scope proxies from the old workbook flow are excluded pending provenance and currency validation.
- PDF text extraction does not perform OCR; diagrams, tables and scanned pages may lose meaning.
- Provider error handling is bounded but live API calls, current account/model access, retrieval relevance and report quality need an integration evaluation before deployment.
- The optional Gradio dashboard serves deterministic reports locally; it is not an authenticated public service. Word export is basic headings/paragraphs rather than full Markdown typesetting.
- Optional dependencies use compatibility ranges; a deployment must choose and validate a lockfile for its own platform.
- Historical binary archives are retained for provenance, not certified as reproducible or corrected reports.

## Next engineering milestones

1. Establish dataset attribution and a clean ingestion contract with stable interval identifiers.
2. Add timezone-aware coverage and independent weekday/label consistency checks.
3. Build a reviewed retrieval evaluation set and quantitative report-verification checks.
4. Define defensible carbon boundaries, units and currency/year conversions before adding scope estimates.
5. Add authentication, operational monitoring and deployment-specific dependency locks if the project becomes a hosted service.
