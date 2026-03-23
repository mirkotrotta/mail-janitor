from __future__ import annotations

import logging
from urllib.parse import quote_plus

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import (
    create_scan_run,
    finish_scan_run,
    get_account,
    replace_sender_stats,
)
from app.security import decrypt_password
from app.services.aggregation import aggregate_sender_stats
from app.services.imap_client import scan_inbox

router = APIRouter(prefix="/scans", tags=["scans"])
logger = logging.getLogger(__name__)


def _redirect(
    run_id: int | None = None, message: str | None = None, error: str | None = None
) -> RedirectResponse:
    parts = []
    if run_id is not None:
        parts.append(f"run_id={run_id}")
    if message:
        parts.append(f"message={quote_plus(message)}")
    if error:
        parts.append(f"error={quote_plus(error)}")
    suffix = f"?{'&'.join(parts)}" if parts else ""
    return RedirectResponse(url=f"/{suffix}", status_code=303)


@router.post("/{account_id}/run")
def run_scan(account_id: int):
    account = get_account(account_id, include_password=True)
    if account is None:
        return _redirect(error="Account not found")

    try:
        password = decrypt_password(account["password"], account["password_encrypted"])
    except Exception:  # noqa: BLE001
        logger.exception("Unable to decrypt password for account_id=%s", account_id)
        return _redirect(error="Scan failed")

    run_id = create_scan_run(account_id=account_id, scan_cap=settings.scan_cap_default)

    try:
        records = scan_inbox(
            {
                "host": account["host"],
                "port": account["port"],
                "use_ssl": bool(account["use_ssl"]),
                "username": account["username"],
                "password": password,
            },
            scan_cap=settings.scan_cap_default,
            timeout_seconds=settings.imap_timeout_seconds,
        )
        stats = aggregate_sender_stats(records)
        replace_sender_stats(run_id, stats)
        finish_scan_run(
            run_id,
            status="success",
            scanned_count=len(records),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scan failed for account_id=%s run_id=%s", account_id, run_id)
        finish_scan_run(
            run_id,
            status="failed",
            scanned_count=0,
            error_message="Scan failed",
        )
        return _redirect(run_id=run_id, error="Scan failed")

    return _redirect(
        run_id=run_id, message=f"Scan complete: {len(records)} messages processed"
    )
