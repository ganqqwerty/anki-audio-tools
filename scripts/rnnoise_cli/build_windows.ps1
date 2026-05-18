param(
    [ValidateSet("windows-x86_64")]
    [string]$Target = "windows-x86_64"
)

Write-Error @"
Build RNNoise v0.2 and scripts/rnnoise_cli/rnnoise_cli.c on Windows x86_64,
then place the standalone executable at:

  .release-assets/bin/$Target/rnnoise-cli.exe

The final binary must not depend on MSYS2 DLLs. Verify with dumpbin or an
equivalent dependency checker, then run:

  python scripts/dev.py release-assets lock-checksums
  python scripts/dev.py release-assets verify --target $Target
"@
exit 1
