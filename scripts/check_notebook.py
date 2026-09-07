"""Validate notebook JSON, syntax, safe defaults, and clean committed outputs."""

import ast
import json
from pathlib import Path
import re


path = Path(__file__).resolve().parents[1] / "EMS_Co_Pilot.ipynb"
notebook = json.loads(path.read_text(encoding="utf-8"))
assert notebook["nbformat"] == 4
assignments = {}
for number, cell in enumerate(notebook["cells"], start=1):
    if cell["cell_type"] != "code":
        continue
    assert cell["outputs"] == [] and cell["execution_count"] is None, f"Stored output in cell {number}"
    source = "".join(cell["source"])
    assert not re.search(r"sk-[A-Za-z0-9_-]{20,}", source), "Credential-shaped string found"
    tree = ast.parse(source, filename=f"notebook-cell-{number}")
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Constant):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = statement.value.value
for setting in ("RUN_AI", "SAVE_REPORT", "EXPORT_DOCX", "LAUNCH_UI"):
    assert assignments[setting] is False, f"{setting} must remain opt-in"
print("Notebook structure, Python syntax, clean outputs and opt-in defaults passed.")
