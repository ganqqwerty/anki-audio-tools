param(
    [ValidateSet("windows-x86_64")]
    [string]$Target = "windows-x86_64",
    [string]$Python = "python",
    [string]$Model = "dpdfnet4"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$BuildDir = Join-Path $Root ".release-assets\build\dpdfnet-windows"
$DistDir = Join-Path $BuildDir "dist"
$ModelDir = Join-Path $BuildDir "models"
$StageDir = Join-Path $Root ".release-assets\bin\$Target"
$BuildScript = Join-Path $Root "scripts\dpdfnet_cli\build_lite.py"
$RequirementsPath = Join-Path $Root "scripts\dpdfnet_cli\requirements-lite-build.txt"
$ExePath = Join-Path $DistDir "dpdfnet.exe"
$StageExePath = Join-Path $StageDir "dpdfnet.exe"

Remove-Item -Recurse -Force $BuildDir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $BuildDir, $ModelDir, $StageDir | Out-Null

& $Python -m pip install --upgrade pip
& $Python -m pip install -r $RequirementsPath
& $Python $BuildScript `
    --name dpdfnet `
    --model $Model `
    --model-path (Join-Path $ModelDir "$Model.tflite") `
    --dist-dir $DistDir `
    --work-dir (Join-Path $BuildDir "work") `
    --spec-dir (Join-Path $BuildDir "spec")

if (!(Test-Path $ExePath)) {
    throw "PyInstaller did not create $ExePath"
}

& $ExePath --version

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

$Ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($null -eq $Ffmpeg) {
    throw "ffmpeg not found on PATH; the DPDFNet Lite smoke test requires ffmpeg."
}
$env:DPDFNET_FFMPEG = $Ffmpeg.Source
& $ExePath enhance $InputWav $OutputWav --attn-limit-db 12
Remove-Item Env:\DPDFNET_FFMPEG -ErrorAction SilentlyContinue
if (!(Test-Path $OutputWav)) {
    throw "DPDFNet smoke test did not create $OutputWav"
}

Copy-Item -Force $ExePath $StageExePath
$Hash = (Get-FileHash -Algorithm SHA256 $StageExePath).Hash.ToLowerInvariant()
Write-Output "Built $StageExePath"
Write-Output "sha256=$Hash"
