#!/usr/bin/env python3
"""Cross-platform task runner for Anki Audio Quick Editor development."""

from __future__ import annotations

import os
import platform
import queue
import shlex
import shutil
import subprocess
import sys
import textwrap
import threading
import time
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = ROOT / "addon" / "anki_audio_quick_editor"
SETTINGS_UI_DIR = ROOT / "settings_ui"
ADDON_SYMLINK_ID = "1000000002"
DEV_DEPS = [
    "pytest-cov", "pytest-qt", "ruff", "mypy", "radon", "import-linter",
    "deptry", "vulture", "bandit", "pytest-randomly", "mutmut", "jsonschema",
]


def _load_dotenv() -> dict[str, str]:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return {}
    result: dict[str, str] = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        result[key] = value
    return result


def _candidate_paths() -> list[Path]:
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
        return [base / "AnkiProgramFiles" / ".venv" / "bin" / "python3"]
    if system == "Linux":
        return [
            Path.home() / ".local" / "share" / "AnkiProgramFiles" / ".venv" / "bin" / "python3",
            Path.home() / ".var" / "app" / "net.ankiweb.Anki" / "data" / "AnkiProgramFiles" / ".venv" / "bin" / "python3",
        ]
    if system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return [Path(appdata) / "AnkiProgramFiles" / ".venv" / "Scripts" / "python.exe"]
    return []


def _validate_python(python: Path) -> bool:
    if not python.is_file():
        return False
    try:
        result = subprocess.run([str(python), "-c", "import anki"], capture_output=True, timeout=15)
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def _find_anki_python() -> Path:
    dotenv = _load_dotenv()
    env_value = os.environ.get("ANKI_PYTHON") or dotenv.get("ANKI_PYTHON")
    if env_value:
        candidate = Path(env_value).expanduser()
        if _validate_python(candidate):
            return candidate
        _die(f"ANKI_PYTHON is set to {env_value!r} but is not usable.")
    for candidate in _candidate_paths():
        if _validate_python(candidate):
            return candidate
    _die("Could not find Anki's bundled Python. Launch Anki once or set ANKI_PYTHON in .env.")
    raise SystemExit(1)


def _anki_bin_dir(anki_python: Path) -> Path:
    return anki_python.parent


def _read_seconds_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else 0.0


def _format_duration(seconds: float) -> str:
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _print_run_header(
    rendered_cmd: str,
    run_cwd: Path,
    env: dict[str, str] | None,
    label: str | None,
    idle_warning_s: float,
    idle_timeout_s: float,
) -> None:
    print(f"\n[dev] {label or 'running command'}")
    print(f"[dev] cwd: {run_cwd}")
    print(f"[dev] cmd: {rendered_cmd}")
    if env:
        print("[dev] env: " + ", ".join(f"{key}={value}" for key, value in sorted(env.items())))
    print("[dev] output: live")
    if idle_warning_s:
        print(f"[dev] idle warning: {_format_duration(idle_warning_s)} without output")
    if idle_timeout_s:
        print(f"[dev] idle timeout: {_format_duration(idle_timeout_s)} without output")


def _handle_idle_warning(
    *,
    now: float,
    start: float,
    last_output: float,
    next_warning: float,
    idle_warning_s: float,
) -> float:
    if idle_warning_s and now >= next_warning:
        idle_for = now - last_output
        print(
            f"[dev] still waiting: no output for {_format_duration(idle_for)} "
            f"(elapsed {_format_duration(now - start)})"
        )
        return now + idle_warning_s
    return next_warning


def _terminate_process_after_idle(process: subprocess.Popen[str], *, idle_for: float, terminate_grace_s: float) -> None:
    print(
        f"[dev] idle timeout reached after {_format_duration(idle_for)}; terminating command...",
        file=sys.stderr,
    )
    process.terminate()
    try:
        process.wait(timeout=terminate_grace_s)
    except subprocess.TimeoutExpired:
        process.kill()


def _handle_idle_queue_wait(
    *,
    output_queue: queue.Queue[str | None],
    process: subprocess.Popen[str],
    start: float,
    last_output: float,
    next_warning: float,
    stream_closed: bool,
    idle_warning_s: float,
    idle_timeout_s: float,
    terminate_grace_s: float,
) -> tuple[bool, bool, bool, float, float]:
    try:
        line = output_queue.get(timeout=1)
    except queue.Empty:
        now = time.monotonic()
        idle_for = now - last_output
        next_warning = _handle_idle_warning(
            now=now,
            start=start,
            last_output=last_output,
            next_warning=next_warning,
            idle_warning_s=idle_warning_s,
        )
        if idle_timeout_s and idle_for >= idle_timeout_s and process.poll() is None:
            _terminate_process_after_idle(process, idle_for=idle_for, terminate_grace_s=terminate_grace_s)
            return False, True, stream_closed, last_output, next_warning
        if stream_closed and process.poll() is not None:
            return True, False, stream_closed, last_output, next_warning
        return False, False, stream_closed, last_output, next_warning
    if line is None:
        if process.poll() is not None:
            return True, False, True, last_output, next_warning
        return False, False, True, last_output, next_warning
    sys.stdout.write(line)
    sys.stdout.flush()
    last_output = time.monotonic()
    next_warning = last_output + idle_warning_s if idle_warning_s else float("inf")
    return False, False, stream_closed, last_output, next_warning


def _run(
    cmd: list[str],
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    *,
    label: str | None = None,
    idle_warning_s: float | None = None,
    idle_timeout_s: float | None = None,
) -> int:
    run_cwd = cwd or ROOT
    merged_env = {**os.environ, **env} if env else None
    if idle_warning_s is None:
        idle_warning_s = _read_seconds_env("DEV_IDLE_WARNING_SECS", 30.0)
    if idle_timeout_s is None:
        idle_timeout_s = _read_seconds_env("DEV_IDLE_TIMEOUT_SECS", 300.0)
    terminate_grace_s = _read_seconds_env("DEV_TERMINATE_GRACE_SECS", 5.0)
    rendered_cmd = shlex.join(str(part) for part in cmd)
    _print_run_header(rendered_cmd, run_cwd, env, label, idle_warning_s, idle_timeout_s)

    process = subprocess.Popen(
        [str(part) for part in cmd],
        cwd=run_cwd,
        env=merged_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    output_queue: queue.Queue[str | None] = queue.Queue()

    def _pump_output() -> None:
        try:
            for line in iter(process.stdout.readline, ""):
                output_queue.put(line)
        finally:
            process.stdout.close()
            output_queue.put(None)

    reader = threading.Thread(target=_pump_output, daemon=True)
    reader.start()

    start = time.monotonic()
    last_output = start
    next_warning = start + idle_warning_s if idle_warning_s else float("inf")
    stream_closed = False
    interrupted_for_idle = False

    while True:
        should_break, timed_out, stream_closed, last_output, next_warning = _handle_idle_queue_wait(
            output_queue=output_queue,
            process=process,
            start=start,
            last_output=last_output,
            next_warning=next_warning,
            stream_closed=stream_closed,
            idle_warning_s=idle_warning_s,
            idle_timeout_s=idle_timeout_s,
            terminate_grace_s=terminate_grace_s,
        )
        if timed_out:
            interrupted_for_idle = True
            continue
        if should_break:
            break

    rc = process.wait()
    reader.join(timeout=1)
    elapsed = time.monotonic() - start
    status = "terminated after idle timeout" if interrupted_for_idle else f"finished with exit code {rc}"
    print(f"[dev] {status} in {_format_duration(elapsed)}")
    return rc


def _pytest_args(target: str, *, collect_only: bool = False) -> list[str]:
    target_args = [target]
    if target == "e2e/":
        target_args = ["--pyargs", "e2e"]
    args = [
        "pytest",
        *target_args,
        "-vv",
        "--durations=20",
        "-o",
        "console_output_style=progress-even-when-capture-no",
    ]
    if collect_only:
        args.append("--collect-only")
    else:
        args.extend(["-s", "--setup-show", "-o", "log_cli=true", "-o", "log_cli_level=INFO"])
    return args


def _probe_import_sequence(target: str, *, label: str, anki_python: Path) -> None:
    target_path = ROOT / target.rstrip("/")
    if not target_path.exists():
        return
    timeout_s = _read_seconds_env("DEV_IMPORT_PROBE_TIMEOUT_SECS", 15.0)
    conftests = sorted(target_path.rglob("conftest.py"))
    test_files = sorted(target_path.rglob("test_*.py"))
    if not conftests and not test_files:
        return

    helper_code = textwrap.dedent(
        """
        import importlib.util
        import os
        import sys
        from pathlib import Path

        root = Path(sys.argv[1])
        conftest_arg = sys.argv[2]
        target = Path(sys.argv[3])
        sys.path.insert(0, str(root))

        if conftest_arg:
            for index, raw_path in enumerate(conftest_arg.split(os.pathsep)):
                path = Path(raw_path)
                spec = importlib.util.spec_from_file_location(f"_probe_conftest_{index}", path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                assert spec.loader is not None
                spec.loader.exec_module(module)

        spec = importlib.util.spec_from_file_location(f"_probe_target_{target.stem}", target)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
        print(f"[probe] imported {target}")
        """
    )
    conftest_str = os.pathsep.join(str(path) for path in conftests)
    for path in [*conftests, *test_files]:
        try:
            result = subprocess.run(
                [str(anki_python), "-c", helper_code, str(ROOT), conftest_str if path.name != "conftest.py" else "", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            print(f"[dev] probe TIMEOUT: {path.relative_to(ROOT)}", file=sys.stderr)
            return
        if result.returncode != 0:
            print(result.stderr.rstrip(), file=sys.stderr)
            return


def _run_pytest(target: str, *, label: str) -> int:
    anki_python = _find_anki_python()
    collect_warning_s = _read_seconds_env("DEV_PYTEST_COLLECT_WARNING_SECS", 10.0)
    collect_timeout_s = _read_seconds_env("DEV_PYTEST_COLLECT_TIMEOUT_SECS", 60.0)
    rc = _run(
        [str(anki_python), "-m", *_pytest_args(target, collect_only=True)],
        label=f"{label} (collect)",
        idle_warning_s=collect_warning_s,
        idle_timeout_s=collect_timeout_s,
    )
    if rc != 0:
        _probe_import_sequence(target, label=label, anki_python=anki_python)
        return rc
    return _run([str(anki_python), "-m", *_pytest_args(target)], label=f"{label} (run)")


def _setup_addon_symlink() -> None:
    system = platform.system()
    if system == "Darwin":
        addons_dir = Path.home() / "Library" / "Application Support" / "Anki2" / "addons21"
    elif system == "Linux":
        addons_dir = Path.home() / ".local" / "share" / "Anki2" / "addons21"
    else:
        addons_dir = None
    if addons_dir and addons_dir.is_dir():
        link = addons_dir / ADDON_SYMLINK_ID
        if link.is_symlink() or link.exists():
            print(f"  Already exists: {link}")
        else:
            link.symlink_to(ADDON_DIR)
            print(f"  Created: {link} -> {ADDON_DIR}")
    elif addons_dir:
        print(f"  Skipped: {addons_dir} does not exist (launch Anki once first)")
    else:
        print(f"  Skipped: symlink creation not supported on {system}")


def cmd_setup() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python: {anki_python}")
    rc = _run([str(anki_python), "-m", "pip", "install", *DEV_DEPS], label="installing Python dev dependencies")
    if rc == 0:
        print(f"  Installed: {', '.join(DEV_DEPS)}")
    _setup_addon_symlink()
    if SETTINGS_UI_DIR.is_dir() and shutil.which("npm"):
        _run(["npm", "install", "--legacy-peer-deps"], cwd=SETTINGS_UI_DIR, label="settings UI npm install")
    return 0


def cmd_test() -> int:
    return _run_pytest("tests/", label="python tests")


def cmd_test_e2e() -> int:
    return _run_pytest("e2e/", label="python e2e tests")


def cmd_lint() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "ruff", "check"], label="ruff lint")


def cmd_typecheck() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "mypy"], label="mypy typecheck")


def cmd_arch() -> int:
    anki_python = _find_anki_python()
    lint_imports = _anki_bin_dir(anki_python) / "lint-imports"
    if not lint_imports.is_file():
        _die(f"lint-imports not found at {lint_imports}. Run: python3 scripts/dev.py setup")
    return _run([str(lint_imports)], env={"PYTHONPATH": "addon"}, label="import-linter architecture check")


def cmd_complexity() -> int:
    anki_python = _find_anki_python()
    return _run(
        [
            str(anki_python), "-m", "radon", "cc",
            "addon/anki_audio_quick_editor/",
            "--min", "C",
            "--ignore", "vendor",
            "--show-complexity",
        ],
        label="radon complexity",
    )


def cmd_deadcode() -> int:
    anki_python = _find_anki_python()
    paths = ["addon/anki_audio_quick_editor/"]
    whitelist = ROOT / "vulture_whitelist.py"
    if whitelist.is_file():
        paths.append(str(whitelist))
    return _run(
        [str(anki_python), "-m", "vulture", *paths, "--exclude", "vendor", "--min-confidence", "80"],
        label="vulture deadcode",
    )


def cmd_security() -> int:
    anki_python = _find_anki_python()
    return _run(
        [
            str(anki_python), "-m", "bandit",
            "-r", "addon/anki_audio_quick_editor/",
            "--exclude", "addon/anki_audio_quick_editor/vendor",
            "-c", "pyproject.toml",
        ],
        label="bandit security",
    )


def cmd_deps() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "deptry", "."], label="deptry dependency check")


def cmd_muttest() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "mutmut", "run", *sys.argv[2:]], label="mutmut mutation testing")


def cmd_coverage() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "-m", "pytest", "tests/", "--cov", "--cov-report=term-missing"], label="python coverage")


def cmd_sonar() -> int:
    scanner = shutil.which("sonar-scanner")
    if not scanner:
        _die("sonar-scanner not found. Install it first if you want local Sonar analysis.")
    token = os.environ.get("SONAR_TOKEN") or _load_dotenv().get("SONAR_TOKEN")
    if not token:
        _die("SONAR_TOKEN not set.")
    anki_python = _find_anki_python()
    _run([str(anki_python), "-m", "pytest", "tests/", "--cov", "--cov-report=xml"], label="python coverage for sonar")
    return _run([scanner], env={"SONAR_TOKEN": token}, label="sonar-scanner analysis")


def cmd_check() -> int:
    steps: list[tuple[str, Callable[[], int]]] = [
        ("config-schema", cmd_config_schema),
        ("lint", cmd_lint),
        ("typecheck", cmd_typecheck),
        ("security", cmd_security),
        ("deadcode", cmd_deadcode),
        ("deps", cmd_deps),
        ("complexity", cmd_complexity),
        ("arch", cmd_arch),
        ("test", cmd_test),
        ("test-svelte", cmd_test_svelte),
    ]
    failed: list[str] = []
    for index, (name, func) in enumerate(steps, start=1):
        print(f"\n{'=' * 60}\n  Step {index}/{len(steps)}: {name}\n{'=' * 60}\n")
        rc = func()
        if rc != 0:
            failed.append(name)
            print(f"\n  FAILED: {name}")
    print(f"\n{'=' * 60}")
    if failed:
        print(f"  {len(failed)} step(s) failed: {', '.join(failed)}")
    else:
        print("  All checks passed!")
    print(f"{'=' * 60}")
    return 1 if failed else 0


def cmd_config_schema() -> int:
    anki_python = _find_anki_python()
    return _run([str(anki_python), "scripts/config_schema_validate.py"], label="config schema validation")


def cmd_build_ui() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        _die("settings_ui/ directory not found.")
    if not shutil.which("npm"):
        _die("npm not found. Install Node.js 18+.")
    return _run(["npm", "run", "build"], cwd=SETTINGS_UI_DIR, label="settings UI build")


def cmd_build() -> int:
    return cmd_build_ui()


def cmd_test_svelte() -> int:
    if not SETTINGS_UI_DIR.is_dir():
        print("settings_ui/ not found - skipping Svelte tests.")
        return 0
    if not (SETTINGS_UI_DIR / "node_modules").is_dir():
        print("settings_ui/node_modules not found - skipping Svelte tests.")
        print("  Run: python3 scripts/dev.py setup")
        return 0
    return _run(["npm", "test"], cwd=SETTINGS_UI_DIR, label="settings UI tests")


def cmd_release() -> int:
    return _run([sys.executable, "scripts/release.py"], label="release build")


def cmd_info() -> int:
    anki_python = _find_anki_python()
    print(f"Anki Python:  {anki_python}")
    result = subprocess.run([str(anki_python), "--version"], capture_output=True, text=True)
    print(f"Python:       {result.stdout.strip()}")
    node = shutil.which("node")
    if node:
        print(f"Node.js:      {subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip()}")
    else:
        print("Node.js:      not found")
    npm = shutil.which("npm")
    if npm:
        print(f"npm:          {subprocess.run([npm, '--version'], capture_output=True, text=True).stdout.strip()}")
    else:
        print("npm:          not found")
    print(f"Project root: {ROOT}")
    print(f"Add-on dir:   {ADDON_DIR}")
    return 0


COMMANDS: dict[str, tuple[Callable[[], int], str]] = {
    "setup": (cmd_setup, "One-time setup: install dev deps, create symlink, npm install"),
    "test": (cmd_test, "Run unit + architecture tests"),
    "test-e2e": (cmd_test_e2e, "Run e2e tests (requires Anki runtime)"),
    "lint": (cmd_lint, "Run ruff linter"),
    "typecheck": (cmd_typecheck, "Run mypy type checker"),
    "arch": (cmd_arch, "Run import-linter architecture contracts"),
    "complexity": (cmd_complexity, "Run radon complexity check"),
    "deadcode": (cmd_deadcode, "Find dead code (vulture)"),
    "security": (cmd_security, "Run bandit security linter"),
    "deps": (cmd_deps, "Check dependencies (deptry)"),
    "check": (cmd_check, "Full QC: config-schema + lint + typecheck + security + deadcode + deps + complexity + arch + test + svelte"),
    "coverage": (cmd_coverage, "Run tests with coverage report"),
    "sonar": (cmd_sonar, "Optional SonarQube analysis (needs SONAR_TOKEN)"),
    "muttest": (cmd_muttest, "Mutation testing (slow, opt-in)"),
    "build": (cmd_build, "Build the settings Svelte bundle"),
    "build-ui": (cmd_build_ui, "Build the settings Svelte bundle"),
    "test-svelte": (cmd_test_svelte, "Run settings Svelte UI tests"),
    "config-schema": (cmd_config_schema, "Validate config.json against JSON Schema"),
    "release": (cmd_release, "Run scripts/release.py"),
    "info": (cmd_info, "Print discovered paths and versions"),
}


def cmd_help() -> int:
    print("Usage: python3 scripts/dev.py <command>\n")
    print("First time? Run 'setup' to install dev tools:\n")
    print("  python3 scripts/dev.py setup\n")
    print("Commands:")
    max_name = max(len(name) for name in COMMANDS)
    for name, (_, desc) in COMMANDS.items():
        print(f"  {name:<{max_name}}  {desc}")
    print(f"\n  {'help':<{max_name}}  Show this help message")
    return 0


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("help", "--help", "-h"):
        cmd_help()
        raise SystemExit(0)
    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command!r}\n")
        cmd_help()
        raise SystemExit(1)
    print(f"[dev] selected command: {command}")
    func, _ = COMMANDS[command]
    raise SystemExit(func())


if __name__ == "__main__":
    main()
