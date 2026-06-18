"""Architecture contracts for audio and batch core modules."""

from __future__ import annotations

from .contract_audio_batch import AUDIO_BATCH_CONTRACTS
from .contract_audio_core import AUDIO_CORE_CONTRACTS
from .contract_schema import ModuleContract

AUDIO_CONTRACTS: dict[str, ModuleContract] = {
    **AUDIO_CORE_CONTRACTS,
    **AUDIO_BATCH_CONTRACTS,
}
