# Setup

## Offline analytics

Use Python 3.10+ and Git. Clone the repository, change into its root, then run:

```bash
python -m ems_copilot audit
python -m ems_copilot report --start 2018-01-01 --end 2018-01-07
```

The CLI uses only the Python standard library and the committed `ems.db`. It does not require the original CSV, the carbon-intensity Excel workbook, a Google Drive mount or the archived vector index.

## Optional environment

Create an isolated environment before installing optional packages:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

If PowerShell blocks activation, use `.venv\Scripts\python.exe` directly in place of `python`; there is no need to change machine-wide execution policies.

| Workflow | Install | Start |
| --- | --- | --- |
| Notebook | `python -m pip install -e ".[notebook]"` | `python -m jupyterlab EMS_Co_Pilot.ipynb` |
| Dashboard | `python -m pip install -e ".[ui]"` | `python app.py --db ems.db` |
| PDF retrieval / AI / Word | `python -m pip install -e ".[ai,notebook]"` | Open the notebook and follow its optional section |

Extras are separate: installing `ui` does not install the AI stack. First-time package downloads require internet access. Version ranges in `pyproject.toml` are compatibility constraints, not a lockfile or a claim that every permitted version has been tested.

## AI configuration

Only the optional AI workflow reads these variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `OPENAI_API_KEY` | None | Required for embeddings and generated drafts |
| `OPENAI_MODEL` | `gpt-4.1-mini` | Chat model used by the original project; access depends on your account |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for both PDF chunks and questions |

`.env.example` documents the names. Files named `.env` are ignored by Git but **are not automatically loaded** by this project. Set variables through your environment or a secrets manager before starting Jupyter. For an interactive notebook session, a hidden prompt avoids placing the key in source:

```python
import getpass
import os
os.environ["OPENAI_API_KEY"] = getpass.getpass("OpenAI API key: ")
```

Never print the value or save it in a notebook cell. Keep all four notebook switches `False` in committed notebooks: `RUN_AI`, `SAVE_REPORT`, `EXPORT_DOCX`, `LAUNCH_UI`.

## Google Colab

Clone this repository in a Colab runtime, change into the checkout with `%cd EMS-Co-Pilot-`, and install the relevant extra there. Open or copy the curated notebook cells into that runtime. Drive mounting is optional; use an explicit local database path or your own mounted path. A fresh Colab runtime loses local `reports/` and `runtime/rag/`, so copy needed outputs to your own storage before disconnecting. The local-only dashboard does not create a public Colab share link.

## Generated files

- `reports/`: your exported reports; ignored by Git.
- `runtime/rag/`: new Chroma collections; ignored by Git.
- The source SQLite, legacy Chroma snapshot and bundled archives remain unchanged.

See [troubleshooting](TROUBLESHOOTING.md) if a path, dependency or provider call fails.
