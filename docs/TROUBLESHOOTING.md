# Troubleshooting

| Symptom | Cause / action |
| --- | --- |
| `No module named ems_copilot` | Run from the cloned repository root, or install it with `python -m pip install -e .` in the same environment. |
| Database not found | Pass an explicit `--db` path. A missing path is rejected rather than silently creating an empty SQLite file. |
| Cannot read `energy_readings` | Confirm the database is SQLite and contains the required schema in [DATA.md](DATA.md). The carbon-intensity table alone is insufficient. |
| Conflicting readings | Two rows use the same timestamp but differ in energy, carbon or metadata. Resolve that ambiguity in a copy of the source; the report will not silently choose one. |
| Invalid reading | Check timestamp format, 15-minute alignment, finite nonnegative measurements, weekend flag and nonempty labels. |
| No readings in period | Run `audit`; the bundled data covers calendar year 2018. |
| Percentage change is unavailable | One period is incomplete or its baseline metric is zero. This is intentional, not a calculation failure. |
| Totals differ from an old report | Old reports may sum six duplicate copies of every interval. Regenerate using the current engine and compare the audit counts. |
| Output already exists | Choose a new `--output` filename or deliberately manage your existing report. Exports do not overwrite files. |
| `ModuleNotFoundError` for Gradio, Chroma, OpenAI, pypdf or docx | Install the appropriate optional extra with the same Python interpreter used to run the app/notebook. |
| API key missing / authentication error | Set a valid key in the runtime environment. `.env.example` and `.env` are not auto-loaded. Never paste credentials into an issue or notebook source. |
| Provider rate limit / unavailable model | Check your provider account and configured model. Retry later if appropriate; local analytics continues to work without the provider. |
| Model did not complete a report | A partial, filtered or empty response is not accepted. Shorten the question or inspect the provider/model configuration before retrying. |
| PDF has no extractable text | The pipeline does not perform OCR. Provide a text-based PDF or OCR it separately. |
| Indexing was interrupted | Repeat the same PDF/model indexing call. Existing chunk IDs are skipped and missing batches are retried. |
| Old vector snapshot fails with a newer Chroma version | Use the documented new index under `runtime/rag/`; do not combine it with the legacy archive. |
| Dashboard cannot start / port in use | Close the earlier local app, then restart. Notebook launch is opt-in and blocks while the UI runs. |

When reporting a bug, include the command, Python version, relevant package versions, a sanitized traceback and a tiny synthetic dataset that reproduces the behavior. Do not include secrets, private database records or confidential report contents.
