from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_cipher() -> Fernet | None:
    secret = os.getenv("APP_SECRET_KEY", "").strip()
    if not secret:
        return None
    return Fernet(_derive_fernet_key(secret))


def encrypt_password(password: str) -> tuple[str, int]:
    cipher = _get_cipher()
    if cipher is None:
        return password, 0
    token = cipher.encrypt(password.encode("utf-8")).decode("utf-8")
    return token, 1


def decrypt_password(value: str, encrypted: int) -> str:
    if not encrypted:
        return value

    cipher = _get_cipher()
    if cipher is None:
        raise RuntimeError("Encrypted password present but APP_SECRET_KEY is not set")

    try:
        return cipher.decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Unable to decrypt stored password with APP_SECRET_KEY"
        ) from exc
