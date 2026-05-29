param(
    [ValidateSet("windows-x86_64")]
    [string]$Target = "windows-x86_64"
)

Write-Error @"
The Windows FFmpeg build must be produced and accepted on a Windows x86_64
machine. Follow scripts/ffmpeg_build/README.md, place ffmpeg.exe and
ffprobe.exe in .release-assets/bin/$Target/, ensure ffmpeg satisfies
aqe-source-audio-v1, then run:

  python scripts/ffmpeg_runtime_capabilities.py --ffmpeg .release-assets/bin/$Target/ffmpeg.exe
  python scripts/dev.py release-assets lock-checksums
  python scripts/dev.py release-assets verify --target $Target --diagnostics
"@
exit 1
