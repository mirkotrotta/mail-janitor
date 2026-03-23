from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.db import (
    ensure_storage_ready,
    get_latest_scan_run,
    get_scan_run,
    get_sender_stats,
    init_db,
    list_accounts,
)
from app.models import PROVIDER_OPTIONS, PROVIDER_PRESETS
from app.routers.accounts import router as accounts_router
from app.routers.scans import router as scans_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(accounts_router)
app.include_router(scans_router)


@app.on_event("startup")
def startup() -> None:
    ensure_storage_ready()
    init_db()


@app.get("/up")
def healthcheck():
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=HTMLResponse)
def root(
    request: Request,
    run_id: int | None = None,
    message: str | None = None,
    error: str | None = None,
):
    accounts = list_accounts()

    selected_run = get_scan_run(run_id) if run_id else get_latest_scan_run()
    sender_stats = []
    if selected_run:
        sender_stats = get_sender_stats(selected_run["id"])

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "accounts": accounts,
            "provider_options": PROVIDER_OPTIONS,
            "provider_presets": json.dumps(PROVIDER_PRESETS),
            "selected_run": selected_run,
            "sender_stats": sender_stats,
            "message": message,
            "error": error,
            "scan_cap_default": settings.scan_cap_default,
        },
    )
