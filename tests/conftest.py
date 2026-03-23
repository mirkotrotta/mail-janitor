from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.config
import app.db
import app.main
import app.routers.accounts
import app.routers.scans


@pytest.fixture()
def app_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    storage_dir = tmp_path / "storage"
    database_path = storage_dir / "app.db"
    test_settings = app.config.Settings(
        app_name="mail-janitor-test",
        app_env="test",
        storage_dir=str(storage_dir),
        database_path=str(database_path),
        scan_cap_default=25,
        imap_timeout_seconds=2,
    )

    monkeypatch.setattr(app.config, "settings", test_settings)
    monkeypatch.setattr(app.db, "settings", test_settings)
    monkeypatch.setattr(app.main, "settings", test_settings)
    monkeypatch.setattr(app.routers.accounts, "settings", test_settings)
    monkeypatch.setattr(app.routers.scans, "settings", test_settings)

    app.db.ensure_storage_ready()
    app.db.init_db()

    return TestClient(app.main.app)
