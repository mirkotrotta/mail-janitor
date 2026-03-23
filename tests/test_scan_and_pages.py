from __future__ import annotations

import app.db
import app.routers.scans


def _create_account(client):
    response = client.post(
        "/accounts/save",
        data={
            "label": "Demo",
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


def test_root_page_render_success(app_client):
    response = app_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "mail-janitor" in response.text


def test_scan_route_success_path_with_mocked_imap(app_client, monkeypatch):
    account = _create_account(app_client)

    def fake_scan_inbox(*args, **kwargs):
        return [
            {
                "sender_email": "sender@example.com",
                "sender_domain": "example.com",
                "subject": "Hello",
                "date": "2026-03-10T10:00:00+00:00",
                "unsubscribe_header_present": True,
            },
            {
                "sender_email": "sender@example.com",
                "sender_domain": "example.com",
                "subject": "World",
                "date": "2026-03-11T10:00:00+00:00",
                "unsubscribe_header_present": False,
            },
        ]

    monkeypatch.setattr(app.routers.scans, "scan_inbox", fake_scan_inbox)

    response = app_client.post(f"/scans/{account['id']}/run", follow_redirects=False)
    assert response.status_code == 303
    assert "run_id=" in response.headers["location"]

    run = app.db.get_latest_scan_run()
    assert run is not None
    assert run["status"] == "success"
    assert run["scanned_count"] == 2

    stats = app.db.get_sender_stats(run["id"])
    assert len(stats) == 1
    assert stats[0]["sender_email"] == "sender@example.com"
    assert stats[0]["message_count"] == 2


def test_scan_route_failure_path_with_mocked_imap(app_client, monkeypatch):
    account = _create_account(app_client)

    def fake_scan_inbox(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(app.routers.scans, "scan_inbox", fake_scan_inbox)

    response = app_client.post(f"/scans/{account['id']}/run", follow_redirects=False)
    assert response.status_code == 303
    assert "error=Scan+failed" in response.headers["location"]

    run = app.db.get_latest_scan_run()
    assert run is not None
    assert run["status"] == "failed"
    assert run["error_message"] == "Scan failed"
