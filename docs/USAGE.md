# Usage

## Audit and report

```bash
python -m ems_copilot audit --db ems.db
python -m ems_copilot report --db ems.db --start 2018-02-01 --end 2018-02-28 --top-n 10
python -m ems_copilot report --start 2018-02-01 --end 2018-02-28 --format json --output reports/february.json
```

`audit` validates all rows, identifies exact duplicates and prints available timestamps. `report` accepts inclusive `YYYY-MM-DD` dates and `--top-n` from 1 to 100. Without `--output`, it prints the report. With `--output`, it creates parent directories and a new file; choose a new filename if one already exists. Invalid input exits with status 2 and a useful message.

JSON contains `period`, `data_quality`, `kpis`, `daily`, `load_types`, `weekday_weekend`, `hourly_profile`, `top_peaks`, `previous_period` and `carbon_basis`. Markdown focuses on the key totals, coverage, daily values, peaks and period comparison. `null` values indicate an unavailable metric, not zero.

## Python API

```python
from ems_copilot import EnergyDataset, render_markdown

dataset = EnergyDataset("ems.db")
print(dataset.audit())
snapshot = dataset.snapshot("2018-01-01", "2018-01-07", top_n=5)
print(render_markdown(snapshot))
```

Load `EnergyDataset` once and reuse it for multiple reports; validation and deduplication occur at construction. The implementation reads the full single-plant table into memory. It never writes to the input database.

## Optional PDF-grounded AI draft

After installing the `ai` extra and setting the environment variables described in [setup](SETUP.md):

```python
from ems_copilot.assistant import index_knowledge, answer_question, save_docx

knowledge = index_knowledge("GHG_Protocol-revised.pdf", directory="runtime/rag")
draft = answer_question(
    "Which energy investigations should we prioritize, given the evidence?",
    snapshot,
    knowledge,
    top_k=3,
)
print(draft["answer"])
print(draft["sources"])
save_docx(draft["answer"], "reports/ai-draft.docx")
```

Indexing sends extractable PDF text to OpenAI in batches of at most 32 chunks. Answering sends the question for embedding, then a bounded analytics summary and retrieved snippets to the chat model. It does not transmit the SQLite file or launch equipment actions. `top_k` accepts 1–10 and is capped to the collection size. Questions are limited to 4,000 characters; generated responses are limited to 1,800 completion tokens. A truncated or empty answer raises an error rather than being presented as a completed report.

Each collection name depends on the PDF content, embedding model and chunking version. Repeated indexing skips existing chunk IDs; interrupted batches can resume. Changing the source or model creates a separate collection, preserving the old one. The new workflow does not migrate the legacy bundled index.

The response returns the actual retrieved text and filename/page metadata. Page numbers are one-based PDF positions, which may differ from printed page numbers. Citations in the generated prose are instructions to the model, not mechanically verified assertions. Review the source list and every quantitative claim before sharing a draft.

The provider interface follows the official [embeddings API](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create) and [chat completions API](https://developers.openai.com/api/reference/python/resources/chat/subresources/completions/methods/create). Live account access, billing, service availability and model output quality are outside the offline test scope.

## Word export and dashboard

`save_docx` creates a simple Word document with headings and paragraphs. It does not provide full Markdown table rendering or a branded publishing template. Existing files are never overwritten.

`python app.py` starts the local deterministic-report dashboard at the URL printed in the terminal. It binds to `127.0.0.1` with public sharing disabled. Close it with Ctrl+C. The dashboard does not call the AI provider; use the notebook or Python API for the optional AI path.

No workflow automatically sends email. Export and review the report, then share it through your usual tools.
