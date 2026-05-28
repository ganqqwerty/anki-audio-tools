"""Static GitHub Pages redirect page tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

VIDEO_ROUTES = {
    "video-play": "Play menu video",
    "video-graph": "Graph menu video",
    "video-share": "Share menu video",
    "video-denoise": "Denoise menu video",
    "video-shorten-pauses": "Remove pauses menu video",
    "video-speed": "Faster and slower menu video",
    "video-record-voice": "Record voice menu video",
    "video-volume": "Louder and quieter menu video",
    "video-batch-processing": "Batch processing video",
}

PRODUCT_ROUTES = {
    **VIDEO_ROUTES,
    "bug-report": "Report a bug",
    "idea-request": "Request an idea",
    "discord": "Discord",
    "patreon": "Patreon",
    "telegram": "Telegram",
}


def _redirect_page(route: str) -> Path:
    return REPO_ROOT / "docs" / "go" / route / "index.html"


def test_product_redirect_pages_exist_and_have_fallback_links() -> None:
    for route, label in PRODUCT_ROUTES.items():
        page = _redirect_page(route)
        assert page.exists(), f"missing redirect page for {route}"
        html = page.read_text(encoding="utf-8")
        assert label in html
        assert 'http-equiv="refresh"' in html
        assert 'rel="canonical"' in html
        assert "<a " in html


def test_video_redirect_pages_do_not_embed_video_players() -> None:
    for route in VIDEO_ROUTES:
        html = _redirect_page(route).read_text(encoding="utf-8").lower()
        assert "<iframe" not in html
        assert "<video" not in html
        assert "open video" in html
