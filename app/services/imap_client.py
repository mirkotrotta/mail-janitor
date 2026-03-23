from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parseaddr
import logging
from typing import Any

from imap_tools import MailBox, MailBoxUnencrypted

logger = logging.getLogger(__name__)


def _mailbox_for_account(account: dict[str, Any], timeout_seconds: int):
    host = account["host"]
    port = account["port"]
    if account["use_ssl"]:
        return MailBox(host, port=port, timeout=timeout_seconds)
    return MailBoxUnencrypted(host, port=port, timeout=timeout_seconds)


def _normalize_date(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _extract_unsubscribe_flag(headers: dict[str, Any]) -> bool:
    header_names = {name.lower() for name in headers.keys()}
    target_names = {
        "list-unsubscribe",
        "list-unsubscribe-post",
        "x-list-unsubscribe",
    }
    return any(name in header_names for name in target_names)


def _public_error_message(exc: Exception) -> str:
    text = str(exc).lower()
    if "authentication" in text or "invalid credentials" in text:
        return "Authentication failed"
    if "timed out" in text or "timeout" in text:
        return "IMAP server timeout"
    return "Connection failed"


def test_connection(account: dict[str, Any], timeout_seconds: int) -> tuple[bool, str]:
    mailbox = _mailbox_for_account(account, timeout_seconds)
    try:
        with mailbox.login(
            account["username"],
            account["password"],
            initial_folder="INBOX",
        ):
            return True, "Connected to IMAP INBOX successfully"
    except Exception as exc:  # noqa: BLE001
        logger.exception("IMAP connection test failed")
        return False, _public_error_message(exc)


def scan_inbox(
    account: dict[str, Any],
    *,
    scan_cap: int,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    mailbox = _mailbox_for_account(account, timeout_seconds)
    records: list[dict[str, Any]] = []

    with mailbox.login(
        account["username"],
        account["password"],
        initial_folder="INBOX",
    ) as inbox:
        for message in inbox.fetch(
            "ALL",
            limit=scan_cap,
            reverse=True,
            mark_seen=False,
            headers_only=True,
        ):
            sender_email = parseaddr(message.from_ or "")[1].strip().lower()
            sender_domain = ""
            if "@" in sender_email:
                sender_domain = sender_email.split("@", 1)[1]

            headers = dict(message.headers) if message.headers else {}

            records.append(
                {
                    "sender_email": sender_email,
                    "sender_domain": sender_domain,
                    "subject": (message.subject or "").strip(),
                    "date": _normalize_date(message.date),
                    "unsubscribe_header_present": _extract_unsubscribe_flag(headers),
                }
            )

    return records
