# FFmpeg Source-Build Fallback

The primary release workflow fetches locked third-party FFmpeg 8.1.1 static
archives with `python3 scripts/dev.py release-assets fetch-ffmpeg --target all`.
The scripts in this directory are retained only as a fallback if a provider
archive disappears or a future release must return to custom builds.

Fallback builds should stay LGPL-compatible unless the project deliberately
changes its distribution license posture.

Required configure posture:

- Do not pass `--enable-gpl`.
- Do not pass `--enable-nonfree`.
- Build `ffmpeg` and `ffprobe`; do not package `ffplay`.
- Link LAME for MP3 encoding through `libmp3lame`.
- Disable broad feature sets and enable only the protocols, formats, codecs,
  parsers, and filters required by `RELEASE_SELF_SUFFICIENCY_ACTION_PLAN.md`.

Cache output goes to `.release-assets/bin/<target>/ffmpeg` and `ffprobe`
or `.exe` equivalents. After a native build, run:

```bash
python3 scripts/dev.py release-assets lock-checksums
python3 scripts/dev.py release-assets verify --target current
```

Only `ffmpeg` and `ffprobe` stay in `.release-assets`. All other runtime
payloads now live in `addon/anki_audio_quick_editor/bin/` and should be copied
there before refreshing checksums.

macOS builds should verify `file`, `codesign -dv`, `otool -L`, and `xattr -l`.
Windows builds can run on a Windows x86_64 machine or via the macOS cross-build
script when `x86_64-w64-mingw32-gcc` is installed, then verify
`ffmpeg.exe -version`, `ffprobe.exe -version`, and DLL dependencies.
