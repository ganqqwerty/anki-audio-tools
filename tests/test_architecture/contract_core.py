"""Architecture contracts for shared import-safe modules."""

from __future__ import annotations

from .contract_schema import Layer, ModuleContract, SideEffect, contract

CORE_CONTRACTS: dict[str, ModuleContract] = {
    "_version": contract("_version", layer=Layer.IMPORT_SAFE_CORE),
    "config_migration": contract("config_migration", layer=Layer.IMPORT_SAFE_CORE),
    "contracts_generated": contract(
        "contracts_generated",
        layer=Layer.IMPORT_SAFE_CORE,
        notes="Generated quicktype DTOs for owned JSON bridge contracts.",
    ),
    "db_helpers": contract(
        "db_helpers",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_side_effects=(SideEffect.DB_ACCESS,),
    ),
    "diagnostics": contract(
        "diagnostics",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor",),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN,),
    ),
    "diagnostics_runtime": contract(
        "diagnostics_runtime",
        layer=Layer.IMPORT_SAFE_CORE,
        notes="Runtime support diagnostics, breadcrumbs, exception hooks, and crash/session files.",
    ),
    "errors": contract("errors", layer=Layer.IMPORT_SAFE_CORE),
    "i18n": contract(
        "i18n",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_side_effects=(SideEffect.ANKI_IMPORTS_ANYWHERE,),
        allow_any_anki_imports=True,
        notes="Shared JSON catalog loader; imports Anki only inside active locale helpers.",
    ),
    "file_reveal": contract(
        "file_reveal",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors", "i18n"),
        allowed_side_effects=(
            SideEffect.SUBPROCESS_POPEN,
            SideEffect.ANKI_IMPORTS_ANYWHERE,
        ),
        allow_any_anki_imports=True,
    ),
    "media_paths": contract(
        "media_paths",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("sound_refs",),
    ),
    "prosody_analyzer": contract(
        "prosody_analyzer",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=(
            "audio_state",
            "prosody_fallback",
            "prosody_praat",
            "prosody_types",
        ),
    ),
    "prosody_cache": contract(
        "prosody_cache",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "prosody_analyzer", "prosody_settings", "prosody_types"),
    ),
    "prosody_fallback": contract(
        "prosody_fallback",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor", "audio_state", "errors", "prosody_settings", "prosody_types"),
        allowed_side_effects=(SideEffect.SUBPROCESS_RUN,),
    ),
    "prosody_praat": contract(
        "prosody_praat",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_processor", "audio_state", "prosody_settings", "prosody_types"),
    ),
    "prosody_settings": contract(
        "prosody_settings",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("audio_state", "prosody_types"),
    ),
    "prosody_svg": contract(
        "prosody_svg",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("prosody_types",),
    ),
    "prosody_types": contract("prosody_types", layer=Layer.IMPORT_SAFE_CORE),
    "settings_state": contract(
        "settings_state",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("contracts_generated",),
    ),
    "sound_refs": contract(
        "sound_refs",
        layer=Layer.IMPORT_SAFE_CORE,
        allowed_addon_deps=("errors",),
    ),
    "support": contract("support", layer=Layer.IMPORT_SAFE_CORE, allowed_addon_deps=("i18n",)),
}
