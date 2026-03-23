from __future__ import annotations

import os
from dataclasses import dataclass


def _db_path_from_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        return database_url[len(prefix) :]
    return "/storage/app.db"


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    storage_dir: str
    database_path: str
    scan_cap_default: int
    imap_timeout_seconds: int


def load_settings() -> Settings:
    app_name = os.getenv("APP_NAME", "mail-janitor")
    app_env = os.getenv("APP_ENV", "development")
    storage_dir = os.getenv("STORAGE_DIR", "/storage")
    database_url = os.getenv("DATABASE_URL", "sqlite:////storage/app.db")
    scan_cap_default = int(os.getenv("SCAN_CAP_DEFAULT", "500"))
    imap_timeout_seconds = int(os.getenv("IMAP_TIMEOUT_SECONDS", "15"))

    return Settings(
        app_name=app_name,
        app_env=app_env,
        storage_dir=storage_dir,
        database_path=_db_path_from_url(database_url),
        scan_cap_default=scan_cap_default,
        imap_timeout_seconds=imap_timeout_seconds,
    )


settings = load_settings()
