"""Architecture contracts for editor runtime modules."""

from __future__ import annotations

from ..contract_schema import ModuleContract
from .core import CORE_EDITOR_CONTRACTS
from .frontend import FRONTEND_EDITOR_CONTRACTS
from .integration import EDITOR_INTEGRATION_CONTRACTS
from .operations import EDITOR_OPERATION_CONTRACTS
from .processing import EDITOR_PROCESSING_CONTRACTS

EDITOR_CONTRACTS: dict[str, ModuleContract] = {
    **CORE_EDITOR_CONTRACTS,
    **FRONTEND_EDITOR_CONTRACTS,
    **EDITOR_OPERATION_CONTRACTS,
    **EDITOR_PROCESSING_CONTRACTS,
    **EDITOR_INTEGRATION_CONTRACTS,
}

__all__ = ["EDITOR_CONTRACTS"]
