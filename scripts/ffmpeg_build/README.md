# FFmpeg Source-Build Fallback

The primary release workflow fetches locked third-party FFmpeg 8.1.1 static
archives with `python3 scripts/dev.py release-assets fetch-ffmpeg --target all`
and verifies `aqe-source-audio-v1` before upload. The scripts in this directory
are retained as a fallback if provider archives disappear or fail the capability
profile.

Provider preference:

- Windows x86_64: use BtbN/FFmpeg-Builds when a pinned archive satisfies
  `aqe-source-audio-v1`; otherwise run a custom build path.
- macOS arm64: Martin Riedl first, OSXExperts second, Vargol arm64 build script
  third, repo fallback script last.
- macOS x86_64: Martin Riedl first, OSXExperts second, repo fallback script
  last. Do not use Vargol for Intel.

Licensing is intentionally not a blocker for the source-quality runtime profile.

Required configure posture:

- Build `ffmpeg` and `ffprobe`; do not package `ffplay`.
- Link LAME, Opus, and Vorbis for `libmp3lame`, `libopus`, and `libvorbis`.
- Disable broad feature sets and enable only the protocols, formats, codecs,
  parsers, and filters required by the editor, model pipelines, and
  source-quality output policy.
- The output profile must include encoders `libmp3lame`, `aac`, `flac`,
  `libvorbis`, `libopus`, `pcm_s16le`, and `pcm_s24le`.
- The output profile must include muxers `mp3`, `mp4`, `adts`, `wav`, `flac`,
  `ogg`, `opus`, and `webm`.

Cache output goes to `.release-assets/bin/<target>/ffmpeg` and `ffprobe`
or `.exe` equivalents. After a native build, run:

```bash
python3 scripts/dev.py release-assets lock-checksums
python3 scripts/ffmpeg_runtime_capabilities.py --ffmpeg .release-assets/bin/<target>/ffmpeg
python3 scripts/dev.py release-assets verify --target current --diagnostics
```

Only `ffmpeg` and `ffprobe` stay in `.release-assets`. All other runtime
payloads now live in `addon/anki_audio_quick_editor/bin/` and should be copied
there before refreshing checksums.

macOS builds should verify `file`, `codesign -dv`, `otool -L`, and `xattr -l`.
Windows builds can run on a Windows x86_64 machine or via the macOS cross-build
script when `x86_64-w64-mingw32-gcc` is installed, then verify
`ffmpeg.exe -version`, `ffprobe.exe -version`, and DLL dependencies.
