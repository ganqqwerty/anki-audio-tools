"""Pure helpers for collection-backed diagnostics."""

from __future__ import annotations

from typing import Any


def build_health_report(col: Any) -> dict[str, Any]:
    """Return a small runtime health report for the settings UI."""
    if col is None:
        return {
            "collection_available": False,
            "deck_count": 0,
            "note_type_count": 0,
            "card_count": 0,
        }

    deck_count = len(col.decks.all_names_and_ids())
    note_type_count = len(col.models.all_names_and_ids())
    card_count = int((col.db.scalar("select count() from cards") if col.db is not None else 0) or 0)
    return {
        "collection_available": True,
        "deck_count": deck_count,
        "note_type_count": note_type_count,
        "card_count": card_count,
    }
