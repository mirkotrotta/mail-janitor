from __future__ import annotations

from app.security import decrypt_password, encrypt_password


def test_password_encryption_roundtrip_with_app_secret(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "test-secret-key")
    encrypted, flag = encrypt_password("abc123")
    assert flag == 1
    assert encrypted != "abc123"
    assert decrypt_password(encrypted, flag) == "abc123"


def test_password_plaintext_mode_when_no_secret(monkeypatch):
    monkeypatch.delenv("APP_SECRET_KEY", raising=False)
    stored, flag = encrypt_password("abc123")
    assert stored == "abc123"
    assert flag == 0
    assert decrypt_password(stored, flag) == "abc123"
