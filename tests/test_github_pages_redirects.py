"""Static GitHub Pages redirect page tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

VIDEO_ROUTES = {
    "video-play": "Play menu video",
    "video-graph": "Graph menu video",
    "video-share": "Share menu video",
    "video-convert": "Convert video",
    "video-denoise": "Denoise menu video",
    "video-pitch-hum": "Pitch Hum video",
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


def test_docs_home_exposes_primary_support_links() -> None:
    html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" in html
    assert "https://fonts.googleapis.com" in html
    assert "go/bug-report/" in html
    assert "go/idea-request/" in html
    assert "go/discord/" in html
    assert "go/telegram/" in html
    assert "https://ankiweb.net/shared/info/1197817101?cb=1780010134595" in html


def test_docs_home_groups_and_links_all_ui_video_routes() -> None:
    html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert "Editor Controls" in html
    assert "Audio Processing" in html
    assert "Batch Tools" in html
    assert 'id="video-convert"' in html
    assert 'href="go/video-convert/"' in html
    assert "Open video section" in html
    assert 'id="video-pitch-hum"' in html
    assert 'href="go/video-pitch-hum/"' in html
    assert "https://www.youtube-nocookie.com/embed/K3ksQ6r0Pys" in html
    assert "https://www.youtube-nocookie.com/embed/YktYHl_JOGo" in html
    assert "https://www.youtube-nocookie.com/embed/Z_lbxrdBjuA" in html
    assert "https://www.youtube-nocookie.com/embed/-hDocz82MxI" in html
    assert "https://www.youtube-nocookie.com/embed/WWimt1urx30" in html
    assert "https://www.youtube-nocookie.com/embed/85gZpORKB68" in html
    assert "https://www.youtube-nocookie.com/embed/wYxhKatjKBw" in html
    assert "https://www.youtube-nocookie.com/embed/tHDJRKY03PM" in html
    assert "https://www.youtube-nocookie.com/embed/wgNb9NSh7BU" in html
