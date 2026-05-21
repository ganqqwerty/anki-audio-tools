#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  scripts/dpdfnet_cli/build_macos.sh <macos-arm64|macos-x86_64> [options]

Options:
  --python <path>   Python interpreter to use (default: python3)
  --version <ver>   dpdfnet PyPI version to freeze (default: 0.5.1)
  --model <name>    DPDFNet model to bundle (default: dpdfnet4)

Output:
  .release-assets/bin/<target>/dpdfnet
EOF
}

target="${1:-}"
if [[ "$target" == "-h" || "$target" == "--help" ]]; then
  usage
  exit 0
fi
if [[ -z "$target" ]]; then
  usage
  exit 2
fi
shift

case "$target" in
  macos-arm64)
    expected_arch="arm64"
    ;;
  macos-x86_64)
    expected_arch="x86_64"
    ;;
  *)
    usage
    exit 2
    ;;
esac

python_bin="${PYTHON:-python3}"
version="${DPDFNET_VERSION:-0.5.1}"
model="${DPDFNET_MODEL:-dpdfnet4}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      python_bin="${2:?--python requires a value}"
      shift 2
      ;;
    --version)
      version="${2:?--version requires a value}"
      shift 2
      ;;
    --model)
      model="${2:?--model requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

root="$(cd "$(dirname "$0")/../.." && pwd)"
build_dir="$root/.release-assets/build/dpdfnet-$target"
dist_dir="$build_dir/dist"
model_dir="$build_dir/models"
stage_dir="$root/.release-assets/bin/$target"
entry_path="$build_dir/dpdfnet_frozen_entry.py"
constraints_path="$build_dir/constraints.txt"
exe_path="$dist_dir/dpdfnet"
stage_exe_path="$stage_dir/dpdfnet"

actual_arch="$("$python_bin" - <<'PY'
import platform
print(platform.machine().lower())
PY
)"
python_version="$("$python_bin" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
if ! "$python_bin" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
then
  echo "Python $python_version is too old; DPDFNet builds require Python 3.11 or newer." >&2
  exit 1
fi
if [[ "$actual_arch" != "$expected_arch" ]]; then
  echo "Python architecture $actual_arch does not match target $target ($expected_arch)." >&2
  echo "Run this script on the matching GitHub Actions macOS runner or use a matching Python." >&2
  exit 1
fi

rm -rf "$build_dir"
mkdir -p "$build_dir" "$model_dir" "$stage_dir"

cat > "$constraints_path" <<'EOF'
numpy<2.3
numba==0.61.2
llvmlite==0.44.0
EOF

"$python_bin" -m pip install --upgrade pip
"$python_bin" -m pip install \
  --only-binary=numba,llvmlite \
  -c "$constraints_path" \
  "dpdfnet==$version" \
  pyinstaller

entry_points="$("$python_bin" - <<'PY'
from importlib.metadata import distribution

print("\n".join(
    f"{ep.name}={ep.value}"
    for ep in distribution("dpdfnet").entry_points
    if ep.group == "console_scripts"
))
PY
)"
if [[ "$entry_points" != *"dpdfnet=dpdfnet.cli:main"* ]]; then
  echo "Unexpected dpdfnet console_scripts entry points: $entry_points" >&2
  exit 1
fi

DPDFNET_MODEL_DIR="$model_dir" "$python_bin" -m dpdfnet.cli download "$model" --quiet

cat > "$entry_path" <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import sys


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


os.environ.setdefault("DPDFNET_MODEL_DIR", str(_runtime_root() / "models"))

from dpdfnet.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
PY

"$python_bin" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --console \
  --name dpdfnet \
  --target-architecture "$expected_arch" \
  --distpath "$dist_dir" \
  --workpath "$build_dir/work" \
  --specpath "$build_dir" \
  --collect-all dpdfnet \
  --collect-all onnxruntime \
  --collect-all soundfile \
  --add-data "$model_dir:models" \
  "$entry_path"

if [[ ! -f "$exe_path" ]]; then
  echo "PyInstaller did not create $exe_path" >&2
  exit 1
fi

artifact_archs="$(lipo -archs "$exe_path")"
if [[ "$artifact_archs" != "$expected_arch" ]]; then
  echo "Built artifact architecture mismatch: expected $expected_arch, got $artifact_archs" >&2
  exit 1
fi

"$exe_path" --version
"$exe_path" models

smoke_dir="$build_dir/smoke"
mkdir -p "$smoke_dir"
input_wav="$smoke_dir/input.wav"
output_wav="$smoke_dir/output.wav"
AQE_DPDFNET_SMOKE_INPUT="$input_wav" "$python_bin" - <<'PY'
from __future__ import annotations

import math
import os
import struct
import wave
from pathlib import Path

sample_rate = 16000
duration_s = 0.25
path = Path(os.environ["AQE_DPDFNET_SMOKE_INPUT"])
with wave.open(str(path), "wb") as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(sample_rate)
    frames = bytearray()
    for index in range(int(sample_rate * duration_s)):
        sample = int(0.2 * 32767 * math.sin(2 * math.pi * 440 * index / sample_rate))
        frames.extend(struct.pack("<h", sample))
    wav.writeframes(bytes(frames))
PY

"$exe_path" enhance "$input_wav" "$output_wav" --model "$model" --attn-limit-db 12
if [[ ! -f "$output_wav" ]]; then
  echo "DPDFNet smoke test did not create $output_wav" >&2
  exit 1
fi

cp -f "$exe_path" "$stage_exe_path"
chmod 755 "$stage_exe_path"
hash="$(shasum -a 256 "$stage_exe_path" | awk '{print $1}')"
echo "Built $stage_exe_path"
echo "sha256=$hash"
