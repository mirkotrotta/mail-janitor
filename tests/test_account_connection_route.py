from __future__ import annotations

import app.db
import app.routers.accounts


def _create_account(client):
    response = client.post(
        "/accounts/save",
        data={
            "label": "Conn Test",
            "provider": "gmail",
            "host": "imap.gmail.com",
            "port": "993",
            "use_ssl": "on",
            "username": "demo@example.com",
            "password": "secret",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    return app.db.list_accounts()[0]


def test_account_test_connection_success_path(app_client, monkeypatch):
    account = _create_account(app_client)

    def fake_test_connection(account_payload, timeout_seconds):
        del account_payload, timeout_seconds
        return True, "Connected to IMAP INBOX successfully"

    monkeypatch.setattr(app.routers.accounts, "test_connection", fake_test_connection)

    response = app_client.post(
        f"/accounts/{account['id']}/test", follow_redirects=False
    )
    assert response.status_code == 303
    assert (
        "message=Connected+to+IMAP+INBOX+successfully" in response.headers["location"]
    )


def test_account_test_connection_failure_sanitized(app_client, monkeypatch):
    account = _create_account(app_client)

    def fake_test_connection(account_payload, timeout_seconds):
        del account_payload, timeout_seconds
        return False, "Authentication failed"

    monkeypatch.setattr(app.routers.accounts, "test_connection", fake_test_connection)

    response = app_client.post(
        f"/accounts/{account['id']}/test", follow_redirects=False
    )
    assert response.status_code == 303
    assert "error=Authentication+failed" in response.headers["location"]
    assert "Traceback" not in response.headers["location"]


def test_account_test_connection_decrypt_failure_is_generic(app_client, monkeypatch):
    account = _create_account(app_client)

    def fake_decrypt_password(value, encrypted):
        del value, encrypted
        raise RuntimeError("bad decrypt")

    monkeypatch.setattr(app.routers.accounts, "decrypt_password", fake_decrypt_password)

    response = app_client.post(
        f"/accounts/{account['id']}/test", follow_redirects=False
    )
    assert response.status_code == 303
    assert "error=Connection+failed" in response.headers["location"]
