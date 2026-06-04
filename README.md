# Anki Audio Quick Editor

Anki desktop add-on for quickly editing audio references from the note editor. It is optimized for short sentence-mining clips: trim edges, adjust speed, shorten long pauses, and automatically apply each edit as a new MP3 while leaving original media untouched.

## Preview

<p>
  <img src="docs/assets/editor-prosody-playback.gif" alt="Inline prosody graph playback inside the Anki editor" width="49%">
  <img src="docs/assets/editor-processing-chain.gif" alt="Applying audio processing actions from the Anki editor toolbar" width="49%">
</p>
<p>
  <img src="docs/assets/browser-card-selection.gif" alt="Selecting cards in the Anki browser before batch audio work" width="49%">
  <img src="docs/assets/editor-pitch-cursor.gif" alt="Inspecting the pitch cursor in the inline audio graph" width="49%">
</p>
<p>
  <img src="docs/assets/editor-dark-prosody-playback.gif" alt="Inline prosody graph playback in Anki dark mode" width="49%">
</p>

## What It Includes

- Inline Anki editor controls for fields containing `[sound:...]` references
- Inline prosody visualization with pitch, intensity, horizontal zoom, and a draggable playback start cursor
- ffmpeg-backed MP3 rendering for each inline edit action
- Silencedetect/Silero pause removal with optional denoise preprocessing and retained debug artifacts
- Non-destructive save flow that writes a new media file and updates the field reference
- Settings dialog and inline editor controls backed by committed Svelte/TypeScript bundles
- Config defaults, JSON Schema validation, and deep-merge migration support
- Unit tests, architecture tests, and real-runtime e2e tests
- `scripts/dev.py` for setup, checks, builds, release, and e2e execution
- `.ankiaddon` packaging via `scripts/release.py`

## Requirements

- Anki 25.09 or later
- Python 3.13 as bundled by Anki
- Public release archives are thin. On first load, the add-on downloads the verified runtime pack for macOS arm64, macOS x86_64, or Windows x86_64.
- Optional advanced overrides: explicit `ffmpeg_path` and `deep_filter_path` settings still take precedence over managed runtime tools
- Bundled `praat-parselmouth` wheels for pitch/intensity analysis on supported platforms; the graph analyzer still falls back to ffmpeg-decoded PCM if Praat is unavailable
- Node.js 18+ for editing or rebuilding the settings/editor frontend bundles

## Quick Start

```bash
python3 scripts/dev.py setup
python3 scripts/dev.py check
python3 scripts/dev.py test-e2e
```

The local development add-on ID is `1000000002`.

## Development

- Runtime package: `addon/anki_audio_quick_editor/`
- Settings and editor frontend source: `settings_ui/`
- Build the committed frontend bundles: `python3 scripts/dev.py build`
- Open the settings dialog from Anki: `Tools -> Anki Audio Quick Editor -> Settings`
- Edit audio from Anki by focusing a field containing a supported sound reference such as `[sound:filename.m4a]`; edits are saved as new MP3 files.

## Release

Runtime packs and thin add-on archives are released separately. Build and publish
a runtime release only when native tools or model files change. The canonical
release checklist is in [`DEVELOPMENT.md`](DEVELOPMENT.md#release-workflow).

```bash
python3 scripts/dev.py release-assets verify --target all
python3 scripts/dev.py release-runtime build --runtime-version 1.0 --target all
python3 scripts/dev.py release-runtime upload --metadata runtime_release.lock.json
python3 scripts/dev.py release-runtime verify --metadata runtime_release.lock.json
```

Normal public add-on releases are thin and consume the tracked
`runtime_release.lock.json` metadata:

```bash
python3 scripts/release.py --target all --verify-runtime-urls
python3 scripts/dev.py release-smoke dist/anki-audio-quick-editor-<version>.ankiaddon
```

Inspect the archive manifest before publishing: it must point at `runtime-vN`,
not the add-on tag. GitHub add-on releases should upload only the `.ankiaddon`;
AnkiWeb should receive the same smoke-tested archive.

Before publishing a public release, run native acceptance on macOS arm64,
macOS x86_64, and Windows x86_64. That includes checking that Anki's bundled
CPython 3.13 imports the packaged `praat-parselmouth` and NumPy wheels from the
add-on-local `user_files/python_vendor/<platform>/` cache, then verifying Graph
and Pitch Hum run without the ffmpeg/PCM fallback warning.

## Similar projects

* [Onsei by Didier Marin](https://hub.2i2c.mybinder.org/user/itsupera-onsei-79jviu4s/voila/render/work/notebook.ipynb?token=s5dTPB1fQbux8BehMRju2g#:~:text=Onsei%3A%20Japanese%20pitch%20accent%20practice%20tool) works nicely on the web, he also has an anki plugin for comparing pitch
* [kotu.io by kezi](kotu.io) with [backup of its early version](https://kuuuube.github.io/minimal-pairs/) by kuuube - an amazing set of learning tools, inlcuding the famous minimal pairs trainer
* [migaku's pitch trainer](https://pitch-demo.migaku.io/)
* [pitchaccentapp by checkempty](https://pitchaccentapp.web.app/) - another web tool for pitch comparison
* [Praat](https://www.fon.hum.uva.nl/praat/) - an ancient tool for researchers. We all use algorithms they developed
* [YuTone](https://yutone.app/) - an app for chinese, somehow super fast, processes pitch in real time
* [Aomi Japanese](https://www.aomijapanese.jp/) records and compares your Japanese pitch accent
* [Tone perfect](https://toneperfect.app/) and [companion reading-feedback app](https://chromewebstore.google.com/detail/chinese-ai-pronunciation/ciginfkinhpfknohjbplmlhgmbomgokg) - chinese only,
* [Ka Chinese Tones](https://chinesetones.app/) - kotu-like tool for chinese tones
* [Aaron's Vietnamese toolset](https://ard.ninja/games/vietnamese/)
* [OJAD](https://www.gavo.t.u-tokyo.ac.jp/ojad/eng/pages/usage) some tools for Japanese pitch, including pitch of sentences
* [JPitch](https://www.jpitch.org/) - word pronunciation analysis for japanese, feedback on mora-by-mora level!
* [MandaTone](https://play.google.com/store/apps/details?hl=en&id=com.ruiyu.mandatone) - Chinese tones app
* [CanTone](https://play.google.com/store/apps/details?hl=en&id=com.cantone.cantone) - comparing your cantonese tones against model
* [Vietnamese Tones](https://apps.apple.com/ca/app/vietnamese-tones/id1549573747) ios app for recording your tones
* [Pho speak](https://phospeak.com/) big vietnamese course that includes pronunciation feedback
* [Cracking languages](https://www.crackinglanguage.com/) Tons of tools for tonal languages from a tonal polyglot
* [Syllable](https://play.google.com/store/apps/details?hl=en_AU&id=com.electricbamboo.syllable)
* [Thai language tones](https://apps.apple.com/us/app/thai-language-tones/id1064086189)
