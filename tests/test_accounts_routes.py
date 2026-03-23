from __future__ import annotations

import app.db


def _create_account(client, **overrides):
    payload = {
        "label": " Demo ",
        "provider": "gmail",
        "host": " IMAP.GMAIL.COM ",
        "port": "993",
        "use_ssl": "on",
        "username": " user@example.com ",
        "password": "secret-1",
    }
    payload.update(overrides)
    return client.post("/accounts/save", data=payload, follow_redirects=False)


def test_account_save_validation_failures(app_client):
    response = _create_account(app_client, label="   ")
    assert response.status_code == 303
    assert "Label+is+required" in response.headers["location"]

    response = _create_account(app_client, username="   ")
    assert response.status_code == 303
    assert "Username+is+required" in response.headers["location"]

    response = _create_account(app_client, host="", provider="generic_imap")
    assert response.status_code == 303
    assert "Host+is+required" in response.headers["location"]

    response = _create_account(app_client, port="70000")
    assert response.status_code == 303
    assert "Port+must+be+between+1+and+65535" in response.headers["location"]


def test_account_create_and_update_normalization(app_client):
    create_response = _create_account(app_client)
    assert create_response.status_code == 303

    account = app.db.list_accounts()[0]
    assert account["label"] == "Demo"
    assert account["host"] == "imap.gmail.com"
    assert account["username"] == "user@example.com"

    update_response = app_client.post(
        "/accounts/save",
        data={
            "account_id": str(account["id"]),
            "label": " Updated Label ",
            "provider": "gmail",
            "host": " Mail.Google.Com ",
            "port": "993",
            "use_ssl": "on",
            "username": " updated@example.com ",
            "password": "new-secret",
        },
        follow_redirects=False,
    )
    assert update_response.status_code == 303

    updated = app.db.get_account(account["id"], include_password=True)
    assert updated is not None
    assert updated["label"] == "Updated Label"
    assert updated["host"] == "mail.google.com"
    assert updated["username"] == "updated@example.com"


def test_account_update_keeps_existing_password_when_blank(app_client):
    _create_account(app_client)
    account = app.db.list_accounts()[0]
    original = app.db.get_account(account["id"], include_password=True)
    assert original is not None

    response = app_client.post(
        "/accounts/save",
        data={
            "account_id": str(account["id"]),
            "label": "Demo",
            "provider": "gmail",
            "host": "imap.gmail.com",
            "port": "993",
            "use_ssl": "on",
            "username": "user@example.com",
            "password": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    current = app.db.get_account(account["id"], include_password=True)
    assert current is not None
    assert current["password"] == original["password"]
    assert current["password_encrypted"] == original["password_encrypted"]
