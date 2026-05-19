"""JSON-catalog localization helpers for user-facing add-on text."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from string import Formatter
from typing import Any, Mapping, TypedDict

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = frozenset({"de", "en", "ja", "ru", "vi", "zh_CN", "zh_TW"})
_LOCALE_DIR = Path(__file__).parent / "locales"
_RTL_LANGS = frozenset({"ar", "fa", "he", "ug"})


class I18nContext(TypedDict):
    """Locale metadata and messages for one UI surface."""

    locale: str
    direction: str
    messages: dict[str, str]


def resolve_locale(raw_locale: str | None) -> str:
    """Return the supported add-on catalog ID for an Anki locale."""
    normalized = (raw_locale or DEFAULT_LOCALE).replace("-", "_")
    if normalized in SUPPORTED_LOCALES:
        return normalized
    if normalized in {"en_US", "en_GB"}:
        return "en"
    if normalized.startswith(("zh_TW", "zh_HK")):
        return "zh_TW"
    if normalized.startswith("zh_CN") or normalized == "zh":
        return "zh_CN"
    language = normalized.split("_", 1)[0]
    return language if language in SUPPORTED_LOCALES else DEFAULT_LOCALE


def active_locale() -> str:
    """Return the current add-on locale from Anki's active UI language."""
    return resolve_locale(_current_anki_lang())


def active_direction() -> str:
    """Return ``rtl`` when Anki marks the active UI language as right-to-left."""
    raw_locale = _current_anki_lang()
    try:
        lang_module = _anki_lang_module()
        return "rtl" if lang_module is not None and lang_module.is_rtl(raw_locale) else "ltr"
    except AttributeError:
        language = raw_locale.replace("-", "_").split("_", 1)[0]
        return "rtl" if language in _RTL_LANGS else "ltr"


def active_context() -> I18nContext:
    """Return locale metadata and merged messages for frontend initial state."""
    locale = active_locale()
    return {
        "locale": locale,
        "direction": active_direction(),
        "messages": messages_for_locale(locale),
    }


def t(key: str, values: Mapping[str, Any] | None = None) -> str:
    """Translate one message with the active Anki locale."""
    return format_message(messages_for_locale(active_locale()), key, values)


def messages_for_locale(locale: str) -> dict[str, str]:
    """Return English messages overlaid with the requested locale catalog."""
    resolved = resolve_locale(locale)
    messages = dict(_load_catalog(DEFAULT_LOCALE))
    if resolved != DEFAULT_LOCALE:
        messages.update(_load_catalog(resolved))
    return messages


def format_message(
    messages: Mapping[str, str],
    key: str,
    values: Mapping[str, Any] | None = None,
) -> str:
    """Format a translated message from an explicit message mapping."""
    template = messages.get(key, _load_catalog(DEFAULT_LOCALE).get(key, key))
    return _safe_format(template, values or {})


@cache
def _load_catalog(locale: str) -> dict[str, str]:
    path = _LOCALE_DIR / f"{resolve_locale(locale)}.json"
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"Locale catalog must be an object: {path}")
    return {str(key): str(value) for key, value in data.items()}


def _safe_format(template: str, values: Mapping[str, Any]) -> str:
    fields = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    safe_values = {name: values.get(name, "{" + name + "}") for name in fields}
    return template.format(**safe_values)


def _current_anki_lang() -> str:
    lang_module = _anki_lang_module()
    if lang_module is not None:
        return str(getattr(lang_module, "current_lang", "") or DEFAULT_LOCALE)
    return DEFAULT_LOCALE


def _anki_lang_module() -> Any | None:
    try:
        import anki

        lang_module = getattr(anki, "lang", None)
        if lang_module is not None:
            return lang_module
        import anki.lang

        return anki.lang
    except (ImportError, AttributeError):
        return None
