"""Mock aqt/anki so add-on code can be imported in a normal pytest run."""

from __future__ import annotations

import sys

from tests._anki_test_mocks_environment import install_mock_modules
from tests._anki_test_mocks_environment import (
    reset_static_mock_modules as _reset_static_mock_modules,
)
from tests.mutmut_support import (
    addon_import_root,
    configure_mutmut_module_alias,
    configure_mutmut_package_aliases,
)

_MOCK_STATE = install_mock_modules()


def reset_static_mock_modules() -> None:
    _reset_static_mock_modules(_MOCK_STATE)


reset_static_mock_modules()


# Make addon imports stable: ``from anki_audio_quick_editor.config_migration import …``
sys.path.insert(0, str(addon_import_root()))
configure_mutmut_module_alias()
configure_mutmut_package_aliases()
