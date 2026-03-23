from __future__ import annotations

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from app.config import settings
from app.security import encrypt_password

logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_storage_ready() -> None:
    os.makedirs(settings.storage_dir, exist_ok=True)
    probe_path = os.path.join(settings.storage_dir, ".write_probe")
    with open(probe_path, "w", encoding="utf-8") as probe:
        probe.write("ok")
    os.remove(probe_path)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                provider TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                use_ssl INTEGER NOT NULL DEFAULT 1,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                password_encrypted INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                scan_cap INTEGER NOT NULL,
                scanned_count INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                error_message TEXT,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS sender_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_run_id INTEGER NOT NULL,
                sender_email TEXT NOT NULL,
                sender_domain TEXT NOT NULL,
                message_count INTEGER NOT NULL,
                oldest_date TEXT,
                newest_date TEXT,
                unsubscribe_header_present INTEGER NOT NULL DEFAULT 0,
                sample_subjects TEXT NOT NULL,
                FOREIGN KEY(scan_run_id) REFERENCES scan_runs(id)
            );

            CREATE INDEX IF NOT EXISTS idx_sender_stats_run
                ON sender_stats(scan_run_id);
            """
        )

        account_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(accounts)").fetchall()
        }
        if "password_encrypted" not in account_columns:
            logger.info("Applying accounts.password_encrypted migration")
            conn.execute(
                "ALTER TABLE accounts ADD COLUMN password_encrypted INTEGER NOT NULL DEFAULT 0"
            )

        fk_rows = conn.execute("PRAGMA foreign_key_list(sender_stats)").fetchall()
        sender_stats_fk_valid = any(
            row["table"] == "scan_runs" and row["from"] == "scan_run_id"
            for row in fk_rows
        )
        if not sender_stats_fk_valid:
            logger.warning(
                "sender_stats foreign key is not bound to scan_runs. "
                "If this DB was created before the FK fix, rebuild local DB "
                "(remove /storage/app.db) to apply corrected SQLite foreign key constraints."
            )

        encrypted_count_row = conn.execute(
            "SELECT COUNT(*) AS total FROM accounts WHERE password_encrypted = 1"
        ).fetchone()
        encrypted_count = (
            int(encrypted_count_row["total"]) if encrypted_count_row else 0
        )
        if encrypted_count > 0 and not os.getenv("APP_SECRET_KEY", "").strip():
            logger.warning(
                "Detected %s encrypted account password(s), but APP_SECRET_KEY is not set. "
                "IMAP operations for those accounts will fail until APP_SECRET_KEY is provided.",
                encrypted_count,
            )


def list_accounts() -> list[sqlite3.Row]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, label, provider, host, port, use_ssl, username,
                   created_at, updated_at
            FROM accounts
            ORDER BY id DESC
            """
        ).fetchall()
    return rows


def get_account(account_id: int, include_password: bool = False) -> sqlite3.Row | None:
    columns = (
        "id, label, provider, host, port, use_ssl, username, password, password_encrypted, "
        "created_at, updated_at"
        if include_password
        else "id, label, provider, host, port, use_ssl, username, created_at, updated_at"
    )
    with db_connection() as conn:
        row = conn.execute(
            f"SELECT {columns} FROM accounts WHERE id = ?",  # noqa: S608
            (account_id,),
        ).fetchone()
    return row


def upsert_account(payload: dict[str, Any]) -> int:
    now = utc_now_iso()
    account_id = payload.get("id")
    encrypted_password, encrypted_flag = encrypt_password(payload["password"])

    with db_connection() as conn:
        if account_id is None:
            cursor = conn.execute(
                """
                INSERT INTO accounts (
                    label, provider, host, port, use_ssl,
                    username, password, password_encrypted, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["label"],
                    payload["provider"],
                    payload["host"],
                    payload["port"],
                    payload["use_ssl"],
                    payload["username"],
                    encrypted_password,
                    encrypted_flag,
                    now,
                    now,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("Failed to create account")
            return int(cursor.lastrowid)

        if payload.get("password"):
            conn.execute(
                """
                UPDATE accounts
                SET label = ?, provider = ?, host = ?, port = ?, use_ssl = ?,
                    username = ?, password = ?, password_encrypted = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload["label"],
                    payload["provider"],
                    payload["host"],
                    payload["port"],
                    payload["use_ssl"],
                    payload["username"],
                    encrypted_password,
                    encrypted_flag,
                    now,
                    account_id,
                ),
            )
        else:
            conn.execute(
                """
                UPDATE accounts
                SET label = ?, provider = ?, host = ?, port = ?, use_ssl = ?,
                    username = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload["label"],
                    payload["provider"],
                    payload["host"],
                    payload["port"],
                    payload["use_ssl"],
                    payload["username"],
                    now,
                    account_id,
                ),
            )
        if account_id is None:
            raise RuntimeError("Account ID missing during update")
        return int(account_id)


def create_scan_run(account_id: int, scan_cap: int) -> int:
    with db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO scan_runs (
                account_id, status, scan_cap, scanned_count, started_at
            )
            VALUES (?, 'running', ?, 0, ?)
            """,
            (account_id, scan_cap, utc_now_iso()),
        )
        if cursor.lastrowid is None:
            raise RuntimeError("Failed to create scan run")
        return int(cursor.lastrowid)


def finish_scan_run(
    run_id: int,
    *,
    status: str,
    scanned_count: int,
    error_message: str | None = None,
) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            UPDATE scan_runs
            SET status = ?, scanned_count = ?, error_message = ?, finished_at = ?
            WHERE id = ?
            """,
            (status, scanned_count, error_message, utc_now_iso(), run_id),
        )


def replace_sender_stats(run_id: int, stats: list[dict[str, Any]]) -> None:
    with db_connection() as conn:
        conn.execute("DELETE FROM sender_stats WHERE scan_run_id = ?", (run_id,))
        for item in stats:
            conn.execute(
                """
                INSERT INTO sender_stats (
                    scan_run_id,
                    sender_email,
                    sender_domain,
                    message_count,
                    oldest_date,
                    newest_date,
                    unsubscribe_header_present,
                    sample_subjects
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    item["sender_email"],
                    item["sender_domain"],
                    item["message_count"],
                    item["oldest_date"],
                    item["newest_date"],
                    1 if item["unsubscribe_header_present"] else 0,
                    json.dumps(item["sample_subjects"]),
                ),
            )


def get_scan_run(run_id: int) -> sqlite3.Row | None:
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT sr.id, sr.account_id, sr.status, sr.scan_cap, sr.scanned_count,
                   sr.started_at, sr.finished_at, sr.error_message,
                   a.label AS account_label
            FROM scan_runs sr
            JOIN accounts a ON a.id = sr.account_id
            WHERE sr.id = ?
            """,
            (run_id,),
        ).fetchone()
    return row


def get_latest_scan_run() -> sqlite3.Row | None:
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT sr.id, sr.account_id, sr.status, sr.scan_cap, sr.scanned_count,
                   sr.started_at, sr.finished_at, sr.error_message,
                   a.label AS account_label
            FROM scan_runs sr
            JOIN accounts a ON a.id = sr.account_id
            ORDER BY sr.id DESC
            LIMIT 1
            """
        ).fetchone()
    return row


def get_sender_stats(run_id: int) -> list[dict[str, Any]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT sender_email, sender_domain, message_count,
                   oldest_date, newest_date, unsubscribe_header_present,
                   sample_subjects
            FROM sender_stats
            WHERE scan_run_id = ?
            ORDER BY message_count DESC, sender_email ASC
            """,
            (run_id,),
        ).fetchall()

    stats: list[dict[str, Any]] = []
    for row in rows:
        stats.append(
            {
                "sender_email": row["sender_email"],
                "sender_domain": row["sender_domain"],
                "message_count": row["message_count"],
                "oldest_date": row["oldest_date"],
                "newest_date": row["newest_date"],
                "unsubscribe_header_present": bool(row["unsubscribe_header_present"]),
                "sample_subjects": json.loads(row["sample_subjects"]),
            }
        )
    return stats
