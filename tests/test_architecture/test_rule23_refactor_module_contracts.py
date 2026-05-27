"""Rule 23: split refactor modules stay under explicit architecture contracts."""

from __future__ import annotations

import tomllib

from .contracts import MODULE_CONTRACTS, Layer
from .inspection import ADDON_DIR

ADDON_PREFIX = "anki_audio_quick_editor"
PROJECT_ROOT = ADDON_DIR.parents[1]

AUDIO_SPLIT_MODULES = {
    "audio_artifacts",
    "audio_commands",
    "audio_external",
    "audio_noise_reduction",
    "audio_pause_pipeline",
    "audio_pitch_hum",
    "audio_pitch_hum_frames",
    "audio_rendering",
    "audio_tools",
    "audio_types",
}

EDITOR_SPLIT_MODULES = {
    "editor_analysis",
    "editor_bridge",
    "editor_callbacks",
    "editor_dependencies",
    "editor_frontend",
    "editor_frontend_callbacks",
    "editor_history",
    "editor_media",
    "editor_playback",
    "editor_processing",
    "editor_recording",
    "editor_recording_frontend",
    "editor_region_delete",
    "editor_region_delete_worker",
    "editor_runtime",
    "editor_session",
    "editor_special_transform_worker",
    "editor_special_transforms",
    "editor_settings_actions",
    "editor_status",
    "editor_split_defaults",
}

BROWSER_SPLIT_MODULES = {
    "browser_batch_runner",
    "browser_dialog",
    "browser_dialog_state",
    "browser_report",
}

RUNTIME_SPLIT_MODULES = {
    "runtime_install",
    "runtime_lookup",
    "runtime_paths",
    "runtime_platform",
    "runtime_state",
}


def _qualified(module_name: str) -> str:
    return f"{ADDON_PREFIX}.{module_name}"


def _import_safe_contract() -> dict[str, object]:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    contracts = data["tool"]["importlinter"]["contracts"]
    [contract] = [
        item for item in contracts if item["name"] == "import-safe-no-upper-layers"
    ]
    return contract


def test_split_modules_have_explicit_contract_layers() -> None:
    expected_layers = {
        **{name: Layer.IMPORT_SAFE_CORE for name in AUDIO_SPLIT_MODULES},
        **{
            "browser_dialog": Layer.UI_ADAPTER,
            "browser_batch_runner": Layer.UI_ADAPTER,
            "browser_dialog_state": Layer.IMPORT_SAFE_CORE,
            "browser_report": Layer.IMPORT_SAFE_CORE,
        },
        **{
            name: Layer.UI_ADAPTER
            for name in EDITOR_SPLIT_MODULES
            - {"editor_media", "editor_session"}
        },
        **{name: Layer.IMPORT_SAFE_CORE for name in RUNTIME_SPLIT_MODULES},
        "editor_media": Layer.IMPORT_SAFE_CORE,
        "editor_session": Layer.IMPORT_SAFE_CORE,
    }

    actual_layers = {
        name: MODULE_CONTRACTS[name].layer
        for name in AUDIO_SPLIT_MODULES
        | EDITOR_SPLIT_MODULES
        | BROWSER_SPLIT_MODULES
        | RUNTIME_SPLIT_MODULES
    }
    assert actual_layers == expected_layers


def test_import_linter_contract_tracks_import_safe_modules() -> None:
    contract = _import_safe_contract()
    import_safe_modules = {
        _qualified(name)
        for name, module_contract in MODULE_CONTRACTS.items()
        if module_contract.layer == Layer.IMPORT_SAFE_CORE
    }

    assert set(contract["source_modules"]) == import_safe_modules


def test_import_linter_forbids_upper_layer_modules_from_core() -> None:
    contract = _import_safe_contract()
    upper_layer_modules = {
        _qualified(name)
        for name, module_contract in MODULE_CONTRACTS.items()
        if module_contract.layer != Layer.IMPORT_SAFE_CORE and name != "__init__"
    }

    assert set(contract["forbidden_modules"]) == upper_layer_modules
