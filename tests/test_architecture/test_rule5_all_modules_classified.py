"""Rule 5: every production Python module must be assigned to a layer."""

from .conftest import ADDON_DIR, ALL_LAYERS


class TestAllModulesClassified:
    """Every .py file in the addon package must appear in a layer set."""

    def test_completeness(self) -> None:
        all_modules: set[str] = set()

        # Top-level .py files
        for p in ADDON_DIR.glob("*.py"):
            if p.stem != "__pycache__":
                all_modules.add(p.stem)

        # Top-level packages and their contents
        for p in ADDON_DIR.iterdir():
            if p.is_dir() and (p / "__init__.py").exists() and p.name not in ("__pycache__", "vendor", "templates"):
                all_modules.add(p.name)
                # Sub-modules (e.g. settings.commands)
                for sub in p.glob("*.py"):
                    if sub.stem != "__init__":
                        all_modules.add(f"{p.name}.{sub.stem}")
                # Sub-packages if any are added later
                for sub in p.iterdir():
                    if sub.is_dir() and (sub / "__init__.py").exists() and sub.name != "__pycache__":
                        all_modules.add(f"{p.name}.{sub.name}")

        unclassified = all_modules - ALL_LAYERS
        assert unclassified == set(), (
            f"Unclassified modules found — add them to a layer in "
            f"tests/test_architecture/conftest.py: {sorted(unclassified)}"
        )
