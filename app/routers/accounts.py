from __future__ import annotations

import logging
from urllib.parse import quote_plus

from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import get_account, upsert_account
from app.models import PROVIDER_PRESETS, is_valid_provider
from app.security import decrypt_password
from app.services.imap_client import test_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


def _redirect(message: str | None = None, error: str | None = None) -> RedirectResponse:
    parts = []
    if message:
        parts.append(f"message={quote_plus(message)}")
    if error:
        parts.append(f"error={quote_plus(error)}")
    suffix = f"?{'&'.join(parts)}" if parts else ""
    return RedirectResponse(url=f"/{suffix}", status_code=303)


def _resolve_connection_values(
    provider: str, host: str, port: int | None, use_ssl: bool
) -> tuple[str, int, bool]:
    preset = PROVIDER_PRESETS[provider]
    resolved_host = (
        host.strip().lower() if host.strip() else preset["host"].strip().lower()
    )
    resolved_port = int(port) if port else preset["port"]
    return resolved_host, resolved_port, use_ssl


def _is_port_valid(port: int) -> bool:
    return 1 <= port <= 65535


@router.post("/save")
def save_account(
    account_id: int | None = Form(default=None),
    label: str = Form(...),
    provider: str = Form(...),
    host: str = Form(default=""),
    port: int | None = Form(default=None),
    use_ssl: str | None = Form(default=None),
    username: str = Form(...),
    password: str = Form(default=""),
):
    label_normalized = label.strip()
    username_normalized = username.strip()

    if not label_normalized:
        return _redirect(error="Label is required")

    if not username_normalized:
        return _redirect(error="Username is required")

    if not is_valid_provider(provider):
        return _redirect(error="Invalid provider")

    resolved_host, resolved_port, resolved_ssl = _resolve_connection_values(
        provider=provider,
        host=host,
        port=port,
        use_ssl=(use_ssl is not None),
    )

    if not resolved_host:
        return _redirect(error="Host is required")

    if not _is_port_valid(resolved_port):
        return _redirect(error="Port must be between 1 and 65535")

    if account_id is not None:
        existing = get_account(account_id, include_password=True)
        if existing is None:
            return _redirect(error="Account not found")

    if account_id is None and not password:
        return _redirect(error="Password is required")

    saved_id = upsert_account(
        {
            "id": account_id,
            "label": label_normalized,
            "provider": provider,
            "host": resolved_host,
            "port": resolved_port,
            "use_ssl": 1 if resolved_ssl else 0,
            "username": username_normalized,
            "password": password,
        }
    )
    return _redirect(message=f"Account saved (ID {saved_id})")


@router.post("/{account_id}/test")
def test_account_connection(account_id: int):
    account = get_account(account_id, include_password=True)
    if account is None:
        return _redirect(error="Account not found")

    try:
        password = decrypt_password(account["password"], account["password_encrypted"])
    except Exception:  # noqa: BLE001
        logger.exception("Unable to decrypt password for account_id=%s", account_id)
        return _redirect(error="Connection failed")

    ok, detail = test_connection(
        {
            "host": account["host"],
            "port": account["port"],
            "use_ssl": bool(account["use_ssl"]),
            "username": account["username"],
            "password": password,
        },
        timeout_seconds=settings.imap_timeout_seconds,
    )
    if ok:
        return _redirect(message=detail)
    return _redirect(error=detail)
