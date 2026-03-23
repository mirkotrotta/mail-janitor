from __future__ import annotations

from typing import Any


def aggregate_sender_stats(
    records: list[dict[str, Any]],
    *,
    sample_subject_count: int = 3,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}

    for item in records:
        sender_email = item.get("sender_email") or "(unknown)"
        sender_domain = item.get("sender_domain") or "(unknown)"
        key = (sender_email, sender_domain)

        if key not in grouped:
            grouped[key] = {
                "sender_email": sender_email,
                "sender_domain": sender_domain,
                "message_count": 0,
                "oldest_date": None,
                "newest_date": None,
                "unsubscribe_header_present": False,
                "sample_subjects": [],
            }

        row = grouped[key]
        row["message_count"] += 1

        item_date = item.get("date")
        if item_date:
            if row["oldest_date"] is None or item_date < row["oldest_date"]:
                row["oldest_date"] = item_date
            if row["newest_date"] is None or item_date > row["newest_date"]:
                row["newest_date"] = item_date

        if item.get("unsubscribe_header_present"):
            row["unsubscribe_header_present"] = True

        subject = (item.get("subject") or "").strip()
        if subject and subject not in row["sample_subjects"]:
            if len(row["sample_subjects"]) < sample_subject_count:
                row["sample_subjects"].append(subject)

    values = list(grouped.values())
    values.sort(key=lambda row: (-row["message_count"], row["sender_email"]))
    return values
