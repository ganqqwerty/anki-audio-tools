"""Executable architecture contracts for production addon modules."""

from __future__ import annotations

from .contract_audio import AUDIO_CONTRACTS
from .contract_core import CORE_CONTRACTS
from .contract_editor import EDITOR_CONTRACTS
from .contract_schema import Layer, ModuleContract, SideEffect
from .contract_ui import UI_CONTRACTS

MODULE_CONTRACTS: dict[str, ModuleContract] = {
    **UI_CONTRACTS,
    **AUDIO_CONTRACTS,
    **CORE_CONTRACTS,
    **EDITOR_CONTRACTS,
}

__all__ = ["Layer", "MODULE_CONTRACTS", "ModuleContract", "SideEffect"]
