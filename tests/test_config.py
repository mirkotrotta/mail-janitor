from __future__ import annotations

from app.config import load_settings


def test_load_settings_defaults(monkeypatch):
    keys = [
        "APP_NAME",
        "APP_ENV",
        "STORAGE_DIR",
        "DATABASE_URL",
        "SCAN_CAP_DEFAULT",
        "IMAP_TIMEOUT_SECONDS",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)

    settings = load_settings()

    assert settings.app_name == "mail-janitor"
    assert settings.app_env == "development"
    assert settings.storage_dir == "/storage"
    assert settings.database_path == "/storage/app.db"
    assert settings.scan_cap_default == 500
    assert settings.imap_timeout_seconds == 15


def test_load_settings_env_overrides(monkeypatch):
    monkeypatch.setenv("APP_NAME", "x")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/storage")
    monkeypatch.setenv("DATABASE_URL", "sqlite:////tmp/custom.db")
    monkeypatch.setenv("SCAN_CAP_DEFAULT", "111")
    monkeypatch.setenv("IMAP_TIMEOUT_SECONDS", "9")

    settings = load_settings()

    assert settings.app_name == "x"
    assert settings.app_env == "test"
    assert settings.storage_dir == "/tmp/storage"
    assert settings.database_path == "/tmp/custom.db"
    assert settings.scan_cap_default == 111
    assert settings.imap_timeout_seconds == 9
