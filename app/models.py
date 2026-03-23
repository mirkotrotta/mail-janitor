from __future__ import annotations

from typing import TypedDict


ProviderName = str


class ProviderPreset(TypedDict):
    host: str
    port: int
    use_ssl: bool


PROVIDER_OPTIONS: list[ProviderName] = ["gmail", "outlook", "generic_imap"]

PROVIDER_PRESETS: dict[ProviderName, ProviderPreset] = {
    "gmail": {
        "host": "imap.gmail.com",
        "port": 993,
        "use_ssl": True,
    },
    "outlook": {
        "host": "outlook.office365.com",
        "port": 993,
        "use_ssl": True,
    },
    "generic_imap": {
        "host": "",
        "port": 993,
        "use_ssl": True,
    },
}


def is_valid_provider(value: str) -> bool:
    return value in PROVIDER_PRESETS
