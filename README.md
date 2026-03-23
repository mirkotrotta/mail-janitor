# mail-janitor

Local-first inbox cleanup workbench for account configuration, IMAP testing, read-only INBOX scans, and sender/domain aggregation review.

## Runtime constraints

- Docker runtime
- Python 3.12
- FastAPI + Jinja2 + SQLite + imap_tools
- Serves on container port `80`
- Healthcheck endpoint: `GET /up` returns HTTP 200
- Writable state persisted under `/storage`
- No OAuth, no n8n, no React/SPA, no background workers
- No destructive mail actions in this MVP slice

## Local development

```bash
docker compose up --build
```

Open:

- App UI: `http://127.0.0.1:8088/`
- Healthcheck: `http://127.0.0.1:8088/up`

## Environment

Copy `.env.example` to `.env` if you want to override defaults.

Current defaults:

- `DATABASE_URL=sqlite:////storage/app.db`
- `STORAGE_DIR=/storage`
- `SCAN_CAP_DEFAULT=500`
- `IMAP_TIMEOUT_SECONDS=15`
- `APP_SECRET_KEY=` (optional; enables encryption-at-rest for stored passwords)

## Account setup notes

- Use **app passwords** where your provider requires them.
  - Gmail: use a Google App Password (not your primary password).
  - Outlook/Microsoft 365: use app password or provider-specific IMAP credential policy.
- Credentials are stored locally in SQLite under `/storage`.
- Passwords are never rendered back into forms or API responses.
- If `APP_SECRET_KEY` is not set, passwords are stored locally in plaintext.
- If `APP_SECRET_KEY` is set, passwords are encrypted before storage.

## MVP flow in this slice

1. Save one or more IMAP accounts.
2. Test IMAP connection for a saved account.
3. Run read-only INBOX scan (capped by `SCAN_CAP_DEFAULT`).
4. Review sender/domain aggregates in the server-rendered UI.

No archive/delete/unsubscribe actions are implemented yet.

## Developer commands

Run app locally without Docker:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Run tests:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q
```

Run Playwright smoke test:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m playwright install chromium
python tests/playwright_smoke.py
```

## Local DB compatibility note

If you created `storage/app.db` before the `sender_stats.scan_run_id` foreign key fix,
SQLite cannot reliably rewrite that foreign key in place.
For a clean local schema, stop the app and remove `storage/app.db`, then restart.
