param(
    [ValidateSet("windows-x86_64")]
    [string]$Target = "windows-x86_64",
    [string]$Python = "python",
    [string]$Version = "0.5.1",
    [string]$Model = "dpdfnet4"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$BuildDir = Join-Path $Root ".release-assets\build\dpdfnet-windows"
$DistDir = Join-Path $BuildDir "dist"
$ModelDir = Join-Path $BuildDir "models"
$StageDir = Join-Path $Root ".release-assets\bin\$Target"
$EntryPath = Join-Path $BuildDir "dpdfnet_frozen_entry.py"
$ExePath = Join-Path $DistDir "dpdfnet.exe"
$StageExePath = Join-Path $StageDir "dpdfnet.exe"

Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $BuildDir, $ModelDir, $StageDir | Out-Null

& $Python -m pip install --upgrade pip
& $Python -m pip install "dpdfnet==$Version" pyinstaller

$entryPoints = & $Python -c "from importlib.metadata import distribution; print('\n'.join(f'{ep.name}={ep.value}' for ep in distribution('dpdfnet').entry_points if ep.group == 'console_scripts'))"
if ($entryPoints -notmatch "dpdfnet=dpdfnet\.cli:main") {
    throw "Unexpected dpdfnet console_scripts entry points: $entryPoints"
}

$env:DPDFNET_MODEL_DIR = $ModelDir
& $Python -m dpdfnet.cli download $Model --quiet

@'
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
'@ | Set-Content -Encoding UTF8 $EntryPath

& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --onefile `
    --console `
    --name dpdfnet `
    --distpath $DistDir `
    --workpath (Join-Path $BuildDir "work") `
    --specpath $BuildDir `
    --collect-all dpdfnet `
    --collect-all onnxruntime `
    --collect-all soundfile `
    --add-data "${ModelDir};models" `
    $EntryPath

if (!(Test-Path $ExePath)) {
    throw "PyInstaller did not create $ExePath"
}

& $ExePath --version
& $ExePath models

$SmokeDir = Join-Path $BuildDir "smoke"
New-Item -ItemType Directory -Force $SmokeDir | Out-Null
$InputWav = Join-Path $SmokeDir "input.wav"
$OutputWav = Join-Path $SmokeDir "output.wav"
$env:AQE_DPDFNET_SMOKE_INPUT = $InputWav
& $Python -c @'
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
'@

& $ExePath enhance $InputWav $OutputWav --model $Model --attn-limit-db 12
if (!(Test-Path $OutputWav)) {
    throw "DPDFNet smoke test did not create $OutputWav"
}

Copy-Item -Force $ExePath $StageExePath
$Hash = (Get-FileHash -Algorithm SHA256 $StageExePath).Hash.ToLowerInvariant()
Write-Output "Built $StageExePath"
Write-Output "sha256=$Hash"
