# Contributing

Start with the [architecture](docs/ARCHITECTURE.md) and [data contract](docs/DATA.md). Keep changes small enough to review and document any altered units, date boundaries, duplicate policies or external data transfers.

## Local workflow

```bash
python -m unittest discover -s tests -v
python scripts/check_notebook.py
python -m ems_copilot audit
```

The default checks need no credentials and do not call external services. Add synthetic fixtures for meaningful edge cases. Keep provider tests mocked; document any separate live integration check and its exact scope without committing credentials or private outputs.

For notebook changes, restart the kernel and run all cells with the default switches left off. Clear all outputs before committing. Keep reusable behavior in `ems_copilot/` and the notebook focused on the walkthrough. Do not reintroduce append-on-rerun ingestion, hard-coded paths, secret values, automatic email tests or public sharing defaults.

## Review expectations

- Describe the user-visible problem, resulting behavior and validation performed.
- Preserve the committed source database and historical archives unless a deliberate, documented data migration is in scope.
- Update setup, usage and methodology documentation when behavior changes.
- Keep missing/zero values distinct and attach units to quantitative outputs.
- Label AI output and proxy assumptions clearly; avoid unsupported production, compliance or performance claims.
- Never add a software or third-party data license without the rights holder's decision.

Use repository issues for ordinary reproducible bugs, and include sanitized steps and expected versus actual behavior. Follow [SECURITY.md](SECURITY.md) for credential exposure or security-sensitive reports.
