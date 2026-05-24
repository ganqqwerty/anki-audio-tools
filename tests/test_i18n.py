"""Tests for add-on localization catalogs and locale resolution."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.dev_tasks.quality import locale_catalog_violations

from anki_audio_quick_editor import i18n


def test_resolve_locale_maps_anki_languages() -> None:
    assert i18n.resolve_locale("ru_RU") == "ru"
    assert i18n.resolve_locale("ja_JP") == "ja"
    assert i18n.resolve_locale("de_DE") == "de"
    assert i18n.resolve_locale("vi_VN") == "vi"
    assert i18n.resolve_locale("en_GB") == "en"
    assert i18n.resolve_locale("zh_CN") == "zh_CN"
    assert i18n.resolve_locale("zh_TW") == "zh_TW"


def test_active_context_uses_anki_current_language(monkeypatch) -> None:
    monkeypatch.setattr(i18n, "_anki_lang_module", lambda: SimpleNamespace(current_lang="de_DE", is_rtl=lambda _lang: False))

    context = i18n.active_context()

    assert context["locale"] == "de"
    assert context["direction"] == "ltr"
    assert context["messages"]["settings.menu"] == "Einstellungen"


def test_messages_fall_back_to_english_for_missing_locale_key(monkeypatch) -> None:
    monkeypatch.setattr(i18n, "_load_catalog", lambda locale: {"x": "EN"} if locale == "en" else {})

    assert i18n.format_message(i18n.messages_for_locale("de"), "x") == "EN"


def test_format_message_interpolates_values_and_preserves_missing_placeholders() -> None:
    assert i18n.format_message({"x": "Hello {name} {missing}"}, "x", {"name": "Ada"}) == (
        "Hello Ada {missing}"
    )


def test_locale_catalogs_have_the_same_keys_as_english() -> None:
    locale_dir = Path(i18n.__file__).parent / "locales"
    english_messages = json.loads((locale_dir / "en.json").read_text(encoding="utf-8"))
    english_keys = set(english_messages)

    assert locale_catalog_violations(locale_dir) == []
    for path in sorted(locale_dir.glob("*.json")):
        keys = set(json.loads(path.read_text(encoding="utf-8")))
        assert keys == english_keys, path.name


def test_non_english_locale_catalogs_do_not_use_english_fallback_values() -> None:
    locale_dir = Path(i18n.__file__).parent / "locales"
    english_messages = json.loads((locale_dir / "en.json").read_text(encoding="utf-8"))

    fallback_values: list[str] = []
    for path in sorted(locale_dir.glob("*.json")):
        if path.name == "en.json":
            continue

        messages = json.loads(path.read_text(encoding="utf-8"))
        fallback_values.extend(
            f"{path.name}:{key}"
            for key, value in messages.items()
            if value == english_messages[key]
        )

    assert fallback_values == []
