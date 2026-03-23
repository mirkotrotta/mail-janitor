from __future__ import annotations

from app.services.aggregation import aggregate_sender_stats


def test_aggregate_sender_stats_groups_and_sorts():
    records = [
        {
            "sender_email": "a@example.com",
            "sender_domain": "example.com",
            "subject": "First",
            "date": "2026-03-01T10:00:00+00:00",
            "unsubscribe_header_present": False,
        },
        {
            "sender_email": "a@example.com",
            "sender_domain": "example.com",
            "subject": "Second",
            "date": "2026-03-05T10:00:00+00:00",
            "unsubscribe_header_present": True,
        },
        {
            "sender_email": "b@other.com",
            "sender_domain": "other.com",
            "subject": "Only",
            "date": "2026-03-03T10:00:00+00:00",
            "unsubscribe_header_present": False,
        },
    ]

    output = aggregate_sender_stats(records)

    assert len(output) == 2
    top = output[0]
    assert top["sender_email"] == "a@example.com"
    assert top["message_count"] == 2
    assert top["oldest_date"] == "2026-03-01T10:00:00+00:00"
    assert top["newest_date"] == "2026-03-05T10:00:00+00:00"
    assert top["unsubscribe_header_present"] is True
    assert top["sample_subjects"] == ["First", "Second"]
