from __future__ import annotations

import sqlite3

import app.db


def test_storage_and_db_initialization(app_client):
    del app_client

    app.db.ensure_storage_ready()
    app.db.init_db()

    db_path = app.db.settings.database_path
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert "accounts" in tables
    assert "scan_runs" in tables
    assert "sender_stats" in tables
