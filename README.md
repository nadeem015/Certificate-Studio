# Certify — Bulk Certificate Generator

A redesigned web interface for the Bulk Certificate Generator, backed by FastAPI, SQLite + SQLAlchemy, Pydantic validation, and ReportLab PDF generation.

## What's new
- A responsive Certificate Studio UI with a live certificate preview.
- Editable recipient rows, sample data, email checks, and support for up to 500 recipients per batch.
- Bulk generation with live progress, per-recipient status, and PDF download links.
- A session history view for recent generation batches.
- Keeps the original REST API, SQLite model, PDF generation, and tests.

## Run on Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** for the UI or **http://127.0.0.1:8000/docs** for API docs.

## API
- `POST /jobs` — submit a generation batch
- `GET /jobs/{job_id}` — inspect progress and recipients
- `GET /jobs/{job_id}/certificates` — list certificates
- `GET /certificates/{certificate_id}/download` — download a generated PDF

The interface uses the existing API and the same predefined PDF certificate layout. The UI preview is illustrative; it is not a live PDF template editor.

## Tests

```powershell
pytest -q
```

## Notes
- Generation batches are stored in SQLite. The history panel currently tracks batches created in the open browser session; it does not yet fetch all historical jobs from the database.
- Email addresses are validated, but the application does not email certificates automatically.
- FastAPI in-process background tasks are intended for a small local demo, not a durable distributed queue.
