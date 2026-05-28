"""Architecture contracts for editor frontend bridge modules."""

from __future__ import annotations

from ..contract_schema import Layer, ModuleContract, SideEffect, contract

FRONTEND_EDITOR_CONTRACTS: dict[str, ModuleContract] = {
    "editor_frontend": contract(
        "editor_frontend",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=(
            "editor_frontend.bridge",
            "editor_frontend.busy",
            "editor_frontend.playback",
            "editor_frontend.refresh",
            "editor_frontend.status",
            "editor_frontend.types",
        ),
    ),
    "editor_frontend.bridge": contract(
        "editor_frontend.bridge",
        layer=Layer.UI_ADAPTER,
        allowed_side_effects=(SideEffect.BACKGROUND_TASK_DISPATCH,),
    ),
    "editor_frontend.busy": contract(
        "editor_frontend.busy",
        layer=Layer.UI_ADAPTER,
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_frontend.playback": contract(
        "editor_frontend.playback",
        layer=Layer.UI_ADAPTER,
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_frontend.refresh": contract(
        "editor_frontend.refresh",
        layer=Layer.UI_ADAPTER,
        allowed_side_effects=(
            SideEffect.ANKI_IMPORTS_ANYWHERE,
            SideEffect.WEB_EVAL,
        ),
        allow_any_anki_imports=True,
    ),
    "editor_frontend.status": contract(
        "editor_frontend.status",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("editor_frontend.types", "error_codes"),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
    "editor_frontend.types": contract(
        "editor_frontend.types",
        layer=Layer.UI_ADAPTER,
    ),
    "editor_frontend_callbacks": contract(
        "editor_frontend_callbacks",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("editor_dependencies", "editor_frontend"),
        allowed_side_effects=(
            SideEffect.WEB_EVAL,
            SideEffect.BACKGROUND_TASK_DISPATCH,
        ),
    ),
    "editor_recording_frontend": contract(
        "editor_recording_frontend",
        layer=Layer.UI_ADAPTER,
        allowed_addon_deps=("contracts_generated", "editor_session", "prosody_types"),
        allowed_side_effects=(SideEffect.WEB_EVAL,),
    ),
}
