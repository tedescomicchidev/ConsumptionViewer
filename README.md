# ConsumptionViewer

Streamlit MVP for uploading MACC consumption plans, storing revisioned datasets, editing in a web grid, and displaying CEO/CFO/CTO dashboards.

## Features
- CSV upload with v1 schema validation.
- Server-side recomputation of derived fields.
- SQL persistence with dataset/revision/history tables (SQLAlchemy models aligned to PRD).
- Two-tab workspace:
  - Executive Dashboard (role presets for CEO/CFO/CTO).
  - Table Editor (editable inputs + revision save + export CSV).
- Risk flags based on ramp-up and realization rules.

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
streamlit run streamlit_app.py
```

## Configuration
- `DATABASE_URL` (optional): SQLAlchemy connection string.
  - Default: `sqlite:///consumption_viewer.db`
  - For Azure SQL, configure a SQL Server URL, e.g. via `pyodbc` driver string.

## Test
```bash
pytest
```
