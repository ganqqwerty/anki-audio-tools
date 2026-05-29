# FFmpeg Source-Quality Preservation Analysis

Date: 2026-05-29

## Scope

This document inventories the current hardcoded FFmpeg output behavior and analyzes which audio operations can preserve source characteristics. The goal is to support encoding "like the original" where practical instead of always producing MP3 with fixed parameters.

I interpret "repairable" as "recoverable/reversible after processing." In audio terms, once an operation decodes lossy audio, applies filters, downsamples, downmixes, or runs a denoising/model transform, that loss is not recoverable. The best we can do afterward is avoid additional avoidable loss by choosing a sensible final encoder and not forcing MP3 unnecessarily.

## Current High-Level Behavior

The codebase already accepts common input formats such as MP3, M4A/AAC, Ogg/Vorbis, Opus, WAV, FLAC, and WebM. Normal edited output is still mostly forced through MP3:

- Standard editor transforms use `libmp3lame -q:a 4`.
- Region delete/keep uses `libmp3lame -q:a 4`.
- Pause removal final render uses `libmp3lame -q:a 4`.
- Denoise and pitch-hum pipelines produce WAV/raw PCM intermediates, then encode final output as MP3.
- Only the explicit "Convert" operation supports `mp3`, `m4a`, `wav`, and `flac`, and those use fixed codec settings.

## Managed FFmpeg Runtime Capability State

Source-extension preservation is blocked by more than the Python command builders. The managed FFmpeg runtime also has to provide encoders and muxers for every extension we intend to preserve.

Current repository state:

- Release targets are `macos-arm64`, `macos-x86_64`, and `windows-x86_64` in `scripts/release_asset_common.py`.
- `ffmpeg` and `ffprobe` are cached native tools fetched from `release_assets.lock.json` into `.release-assets/bin/<target>/`.
- Current locked providers are martin-riedl macOS static archives and gyan.dev Windows essentials archives, not BtbN release assets.
- Current lock validation verifies schema, checksums, runtime files, and optional diagnostics, but does not yet enforce an encoder/muxer capability profile for source-extension preservation.
- `scripts/ffmpeg_build/` already exists as a source-build fallback. It is not a new path to create.

The existing fallback build scripts are currently MP3/WAV focused:

- `scripts/ffmpeg_build/build_macos.sh` and `scripts/ffmpeg_build/build_windows_cross.sh` enable muxers `mp3`, `null`, `s16le`, and `wav`.
- The same scripts enable encoders `libmp3lame` and `pcm_s16le`.
- They decode more formats than they can encode, including AAC, FLAC, Opus, and Vorbis.
- They are insufficient for preserving `.m4a`, `.aac`, `.flac`, `.ogg`, `.oga`, `.opus`, or `.webm` as final output.

BtbN status verified on 2026-05-29: [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) publishes daily auto-builds for Windows and Linux targets, with no macOS target. That means BtbN is a candidate for Windows if its selected archive passes our capability profile, but macOS needs a macOS-specific provider or the existing repo-owned source build path.

macOS provider status checked on 2026-05-29:

- [Martin Riedl's FFmpeg Build Server](https://ffmpeg.martin-riedl.de/) is already the current locked macOS provider in `release_assets.lock.json`. It publishes FFmpeg and FFprobe ZIPs for both macOS Intel/amd64 and Apple Silicon/arm64 release builds, currently FFmpeg 8.1.1 for both targets. It also publishes per-build `Formats` and `Codecs` reports and scripting redirect URLs for automated downloads.
- Martin Riedl's codec reports list MP3 via `libmp3lame`, AAC, Opus via `libopus`, Vorbis via `libvorbis`, and PCM 16/24-bit support for both macOS targets. Its format reports list muxing support for `mp3`, `mp4`, `adts`, `wav`, `flac`, `oga`, `ogg`, `opus`, and `webm`. Treat Martin Riedl as the first macOS candidate, but still run the local binary capability checker before changing source-preservation behavior. In particular, verify the FLAC encoder from the binary because the public codec report line appears less explicit than the format report.
- [OSXExperts](https://www.osxexperts.net/) publishes static macOS FFmpeg/FFprobe ZIPs with SHA-256 values. Current page state lists FFmpeg 8.1 for Apple Silicon and FFmpeg 8.0 for Intel. Its published build script enables `libopus`, `libvorbis`, and `libmp3lame`, but the page does not expose the same per-build Formats/Codecs reports as Martin Riedl. Treat OSXExperts as a secondary macOS fallback that must be downloaded, inspected with `ffmpeg_runtime_capabilities.py`, and possibly repackaged into our release archive format before lock-file adoption.
- [Vargol/ffmpeg-apple-arm64-build](https://github.com/Vargol/ffmpeg-apple-arm64-build) is an Apple Silicon build-script fallback only. The project targets macOS on Apple Silicon and documents builds with LAME, Opus, Vorbis, and FDK-AAC. It does not cover Intel macOS, so it cannot replace `macos-x86_64`. Use it only if Martin Riedl and OSXExperts fail the arm64 capability gate or disappear.

Required runtime capability work:

- Add a repository capability profile for final audio output, for example `aqe-source-audio-v1`.
- Require the profile on release-ready `ffmpeg` lock entries.
- Verify required encoders and muxers in `fetch-ffmpeg`/diagnostic flows for binaries that can run on the current host.
- Prefer a capability-verified macOS provider archive over custom macOS builds. Expand existing `scripts/ffmpeg_build/` fallback scripts only when no acceptable provider archive exists for a target.

## FFmpeg Hardcoded Replacement Inventory

These are the source locations where hardcoded output format or codec policy must be replaced or explicitly kept as an algorithm-internal format.

| Location | Current hardcoding | Used by | Needed change |
|---|---|---|---|
| `addon/anki_audio_quick_editor/audio_commands.py:18` | `_CONVERT_CODEC_ARGS` fixes MP3 to `libmp3lame -q:a 4`, M4A to `aac -b:a 192k`, WAV to `pcm_s16le`, FLAC to compression level 5. | `build_convert_audio_command`, explicit editor and batch convert. | Replace fixed conversion presets with a metadata-aware encode policy. For no-filter conversions, support copy/remux where safe. For lossy re-encode, use source bitrate or a quality floor instead of one global value. |
| `addon/anki_audio_quick_editor/audio_commands.py:99` | `build_ffmpeg_command` always renders filtered audio as MP3 with `libmp3lame -q:a 4`. The docstring says "processed MP3." | `render_audio` for standard trim/speed/volume, and `render_playback_segment` for native playback segments. | Split into a generic filtered render builder that receives final codec/container args. Standard final media should use source-aware policy. Playback temp segments may stay MP3 if chosen for Anki playback compatibility, but that should be a deliberate temp-output policy. |
| `addon/anki_audio_quick_editor/audio_commands.py:122` | `build_wav_filter_command` always writes `pcm_s16le` WAV. | Pause-removal `01_working_original.wav`. | This is an intermediate, not final output. It affects final pause-removal quality because the final render reads this WAV. Consider `pcm_f32le` or source-bit-depth-aware PCM for high-quality/lossless sources. Keep WAV container because downstream FFmpeg filters and analysis need decoded PCM. |
| `addon/anki_audio_quick_editor/audio_commands.py:145` | `build_silencedetect_command` uses FFmpeg analysis output to `null`. | Silencedetect pause detection. | No final quality issue. It decodes for analysis only and should not be part of final output policy. |
| `addon/anki_audio_quick_editor/audio_commands.py:160` | `build_filter_complex_render_command` always maps `[out]` to MP3 with `libmp3lame -q:a 4`. | Pause-removal final output. | Replace with source-aware final encode args. Also update final artifact extension and MIME metadata. |
| `addon/anki_audio_quick_editor/audio_commands.py:193` | `build_region_delete_command` always maps `[out]` to MP3 with `libmp3lame -q:a 4`. | Region delete and region keep. | Replace with source-aware final encode args. Region edit is filter-based, so stream copy is not suitable for exact edits. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:12` | DeepFilterNet prepare step forces 48 kHz mono `pcm_s16le` WAV. | Standard denoise. | Likely algorithm-required. Do not treat this as final policy. Final encode after denoise can be source-aware, but the denoised signal is already 48 kHz mono. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:34` | Silero VAD prepare step forces 16 kHz mono `pcm_s16le` WAV. | Silero pause detection. | Analysis-only and model-required. It does not directly lower final audio quality. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:95` | RNNoise prepare step forces 48 kHz mono raw `s16le`. | RNNoise denoise. | Algorithm-required. RNNoise output is inherently 48 kHz mono raw PCM; original channels/sample rate are not preserved by this operation. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:153` | `build_rnnoise_encode_command` encodes RNNoise raw PCM to MP3 with `libmp3lame -q:a 4`. | RNNoise final encode. | Replace final MP3 encode with generic source-aware encode args, while acknowledging source characteristics have already changed to 48 kHz mono. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:181` | Spleeter prepare step forces 44.1 kHz stereo `pcm_s16le` WAV. | Voice-only extraction. | Likely model/tool-required. Do not try to preserve original characteristics at this stage. Final encode can be source-aware only after the model output is produced. |
| `addon/anki_audio_quick_editor/audio_commands_runtime.py:220` | `build_mp3_encode_command` encodes any WAV-like source to MP3 with `libmp3lame -q:a 4`. | Standard DeepFilterNet, DPDFNet, voice-only, pitch-hum, PitchTier. | Replace with a generic encode command builder, for example `build_audio_encode_command(ffmpeg_path, source_path, output_path, policy)`. |
| `addon/anki_audio_quick_editor/audio_rendering.py:50` | Default `render_audio` temp output suffix is `.mp3`. | Programmatic render calls without caller-supplied output path. | Use selected output extension. In editor/batch flows, caller currently supplies an MP3 path, so caller-side filename policy must change too. |
| `addon/anki_audio_quick_editor/audio_rendering.py:119` | Default region-delete temp suffix is `.mp3`. | Region delete direct calls. | Use selected output extension. |
| `addon/anki_audio_quick_editor/audio_rendering.py:158` | Default region-keep temp suffix is `.mp3`. | Region keep direct calls. | Use selected output extension. |
| `addon/anki_audio_quick_editor/audio_rendering.py:196` | `make_output_filename` defaults `output_format` to `DEFAULT_OUTPUT_FORMAT`, currently MP3. | Final generated Anki media names. | Add an explicit source-preserving output policy, not just `output_format="mp3"`. This helper cannot decide source metadata by filename alone unless the policy is resolved before calling it. |
| `addon/anki_audio_quick_editor/audio_rendering.py:242` | Playback segment filename suffix is `.mp3`. | Native playback segment temp media. | Decide separately. Playback temp files do not become Anki media, so keeping MP3 may be acceptable for compatibility and speed. If changed, playback source URL and cleanup tests must follow. |
| `addon/anki_audio_quick_editor/audio_pause_pipeline.py:68` | Pause pipeline support artifact final copy path is `07_final_output.mp3`. | Pause-removal artifacts and support manifests. | Make final artifact extension policy-aware. |
| `addon/anki_audio_quick_editor/audio_pause_pipeline_steps.py:112` | Final pause artifact MIME is `audio/mpeg`. | Pause-removal artifact manifest. | Make MIME policy-aware, for example `audio/mpeg`, `audio/mp4`, `audio/wav`, `audio/flac`, or a conservative generic value. |
| `addon/anki_audio_quick_editor/audio_noise_reduction.py:51` | Standard denoise default temp output suffix is `.mp3`. | DeepFilterNet renderer when no output path is supplied. | Use selected output extension. Editor/batch callers also need to stop preselecting MP3 names. |
| `addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py:57` | RNNoise default temp output suffix is `.mp3`. | RNNoise renderer. | Use selected output extension, but note the audio is 48 kHz mono after RNNoise. |
| `addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py:117` | DPDFNet default temp output suffix is `.mp3`. | DPDFNet renderer. | Use selected output extension. The external tool produces a WAV intermediate; final encode policy should run after that. |
| `addon/anki_audio_quick_editor/audio_noise_reduction_bundled.py:169` | Voice-only default temp output suffix is `.mp3`. | Spleeter voice-only renderer. | Use selected output extension, but model output characteristics should drive expectations more than original source characteristics. |
| `addon/anki_audio_quick_editor/audio_pitch_hum.py:54` | Pitch hum default temp output suffix is `.mp3`. | Direct pitch-hum renderer. | Use configured/policy output extension if desired. Source-preserving characteristics are not meaningful for synthetic hum content. |
| `addon/anki_audio_quick_editor/audio_pitch_hum.py:87` | PitchTier hum default temp output suffix is `.mp3`. | PitchTier renderer. | Same as direct pitch hum. |
| `addon/anki_audio_quick_editor/editor_processing.py:132` | Standard editor render calls `make_output_filename(source_path.name)` with no output format override. | Editor speed/volume/pause toggle final save. | Resolve source-aware output policy before creating `desired_name`, then pass matching output path and encoder policy to render. |
| `addon/anki_audio_quick_editor/editor_region_delete_worker.py:66` | Region operation calls `make_output_filename(source_path.name)` with default MP3. | Editor delete selection / keep selection. | Same source-aware filename and render policy as standard editor renders. |
| `addon/anki_audio_quick_editor/editor_special_transform_worker.py:41` | Special transforms default to `output_format=DEFAULT_OUTPUT_FORMAT` unless caller overrides. | Denoise, RNNoise, DPDFNet, voice-only, pitch-hum, convert. | Convert intentionally passes target format. Other special transforms should resolve policy from source unless we deliberately keep a fixed output default for generated/synthetic operations. |
| `addon/anki_audio_quick_editor/batch_operation_processing.py:137` | Non-convert batch transforms call `make_output_filename(audio_filename)` with default MP3. | Batch speed/volume/remove pauses/denoise. | Resolve output policy per source note before creating final filename. |
| `addon/anki_audio_quick_editor/audio_processor_rendering_portal.py:124` | Facade default `make_output_filename(..., output_format="mp3")`. | Runtime facade and tests. | Update facade signature once the core helper accepts a resolved output policy. |
| `addon/anki_audio_quick_editor/audio_formats.py:10` | Supported output choices are only `mp3`, `m4a`, `wav`, `flac`; default is MP3. | Settings, editor split menu, batch controls, config normalization. | If "same as source" becomes user-facing, add an `auto`/`source` policy separately from concrete formats. Do not overload `mp3` default. |

## Test And Fixture Locations That Encode Current MP3 Assumptions

These are not implementation sources, but they will fail or become stale after the policy change:

- `tests/test_audio_commands.py` asserts fixed conversion and render codec args.
- `tests/test_audio_rendering.py`, `tests/test_audio_rendering_regions.py`, and `tests/test_audio_playback_rendering.py` assert MP3 command args and `.mp3` temp behavior.
- `tests/test_audio_noise_commands.py`, `tests/test_audio_noise_reduction.py`, `tests/test_audio_rnnoise.py`, `tests/test_audio_dpdfnet.py`, and `tests/test_audio_voice_only.py` assert MP3 final encode commands.
- `tests/test_audio_pause_pipeline.py` and `e2e/test_editor_deep_filter_pause_workflow.py` assert `07_final_output.mp3`.
- `e2e/test_audio_processing_ffmpeg.py` has a test named `test_common_audio_input_format_renders_to_mp3` and asserts `libmp3lame` for normal renders.
- `e2e/race_helpers.py`, `tests/test_editor_async_race_guards.py`, and some editor e2e helpers glob or assert `*__aqe_*.mp3`.

## Editing Algorithm Quality Analysis

### Convert

Current implementation: `render_converted_audio` calls `build_convert_audio_command` with one of the fixed `_CONVERT_CODEC_ARGS`.

Quality implications:

- If the target container/codec can be copied or remuxed, this is the most preservable operation because it may not need filtering.
- Current code does not use stream copy. It always re-encodes to the selected target codec.
- If the source is already the target visible extension, editor and batch conversion skip the operation.
- If converting lossy-to-lossy, quality loss is inherent unless the operation can be implemented as packet copy/remux.

Recommended policy:

- For "same as source" conversions, skip when already same visible format.
- For compatible remux cases, use `-c:a copy` where FFmpeg and target container support it.
- For true transcodes, choose encoder settings from source codec, bitrate, sample rate, and channel count with a quality floor.

### Standard Edits: Trim, Speed, Volume

Current implementation: `render_audio` builds a filter chain from `atrim`, `asetpts`, optional `volume`, and optional `atempo`, then encodes with `build_ffmpeg_command`.

Quality implications:

- Any FFmpeg audio filter requires decode and re-encode.
- `volume` and `atempo` are inherently destructive transforms because samples are changed.
- `trim` alone could theoretically use packet copy for rough, frame-boundary cuts, but the current filter-based approach gives deterministic precise boundaries and therefore re-encodes.
- Sample rate and channels are not explicitly changed in the standard filter path, so FFmpeg usually preserves them unless the chosen encoder/container requires conversion.
- The avoidable loss is the forced final MP3 encode, not the filter decode itself.

Recommended policy:

- Keep filter-based rendering for exact edits.
- Replace forced MP3 with source-aware final encoding.
- Preserve source sample rate and channel count where the encoder supports them.

### Region Delete And Region Keep

Current implementation: region delete/keep builds an `atrim`/`concat` filter graph, then encodes through `build_region_delete_command`.

Quality implications:

- Exact region deletion and concatenation require decoded audio and filter graph processing.
- A stream-copy implementation would be approximate and format-dependent; it would not match current exact behavior.
- Current forced MP3 final encode is avoidable.

Recommended policy:

- Keep filter graph behavior.
- Replace final encoder and extension with source-aware policy.

### Pause Removal

Current implementation:

- The source is first rendered to `01_working_original.wav` using `pcm_s16le`.
- Pause detection uses either FFmpeg `silencedetect` directly on analysis WAV or Silero VAD via a 16 kHz mono WAV.
- Optional pause detection preprocessing runs DPDFNet only for analysis input.
- Final output is rendered from `01_working_original.wav` through a `filter_complex` script and encoded as MP3.

Quality implications:

- Pause removal requires re-rendering because it cuts and concatenates many intervals and may apply volume/speed.
- The Silero 16 kHz mono conversion is analysis-only and does not directly lower final output.
- Optional DPDFNet preprocessing for detection is analysis-only and does not directly become final output.
- The `01_working_original.wav` intermediate does affect final output. It is currently 16-bit PCM, so high-bit-depth or floating-point sources are reduced before final rendering.
- For typical lossy Anki audio, decoding to 16-bit PCM is probably not the dominant loss. For WAV/FLAC source material, this is a real quality cap.

Recommended policy:

- Replace final MP3 encoder with source-aware final encoding.
- Consider changing `01_working_original.wav` to `pcm_f32le` or at least `pcm_s24le` when source quality is higher than 16-bit.
- Keep detector-specific 16 kHz mono input because it is model-required and analysis-only.

### Standard Denoise: DeepFilterNet

Current implementation: `build_deep_filter_prepare_command` creates 48 kHz mono `pcm_s16le` WAV, external DeepFilterNet produces a cleaned WAV, then `build_mp3_encode_command` encodes MP3.

Quality implications:

- Denoising intentionally changes the signal; original quality is not preserved.
- 48 kHz mono preparation is likely an algorithm/tool requirement.
- Stereo source material is downmixed before denoise. That cannot be reconstructed afterward.
- Final forced MP3 is avoidable.

Recommended policy:

- Keep the model-required preparation format.
- Replace final MP3 encode with source-aware output extension and codec args.
- Be explicit that "same as source" only applies to the final container/codec family; channels/sample rate may already be determined by DeepFilterNet.

### RNNoise

Current implementation: source is converted to 48 kHz mono raw `s16le`, RNNoise produces 48 kHz mono raw `s16le`, then final output is hardcoded MP3.

Quality implications:

- 48 kHz mono raw PCM is inherent to the RNNoise pipeline.
- Original sample rate and channel count are not preserved.
- Any later attempt to restore stereo would be upmixing duplicated/derived mono, not source preservation.
- Final forced MP3 is avoidable, but source-like output characteristics are limited by the model output.

Recommended policy:

- Keep 48 kHz mono raw PCM internal stages.
- Replace final MP3 encode with generic final encode policy.
- Document RNNoise as a content-transforming operation where original channel layout is intentionally not preserved.

### DPDFNet

Current implementation: bundled DPDFNet `enhance` reads the source path and writes a WAV, then `build_mp3_encode_command` encodes MP3.

Quality implications:

- Denoising intentionally changes samples.
- The external DPDFNet tool controls the intermediate WAV characteristics.
- Forced MP3 final output is avoidable.

Recommended policy:

- Probe DPDFNet output before final encode if needed.
- Encode final result using the selected output policy, but do not claim original characteristics are preserved if DPDFNet output differs.

### Voice Only / Spleeter

Current implementation: source is prepared as 44.1 kHz stereo `pcm_s16le` WAV, Spleeter extracts vocals, then `build_mp3_encode_command` encodes MP3.

Quality implications:

- This is a stem extraction/generation operation, not source preservation.
- 44.1 kHz stereo preparation appears model/tool-driven.
- Final MP3 is avoidable, but output characteristics are primarily model output characteristics.

Recommended policy:

- Keep model-required preparation.
- Replace final MP3 encode with generic final encode policy.
- Consider whether "same as source" should apply to voice-only at all, or whether generated operations should use a configured output default.

### Pitch Hum And PitchTier Hum

Current implementation: both modes synthesize a new 22,050 Hz mono 16-bit WAV (`HUM_SAMPLE_RATE = 22_050`) and encode it as MP3.

Quality implications:

- These operations intentionally replace the source audio with a synthetic hum.
- Source codec, channels, sample rate, and bitrate are not meaningful to preserve for the audio content.
- The 22.05 kHz mono synthesis is algorithm-defined.
- Final MP3 is avoidable, but "same as original quality" is not the right model for this operation.

Recommended policy:

- Keep synthesis format unless there is a separate reason to improve hum fidelity.
- Decide whether generated synthetic outputs should use source-like extension, configured default, or a fixed portable format.

### Prosody Graph / Fallback Analysis

Current implementation: `prosody_fallback.py` decodes to 16 kHz mono `s16le` PCM for pitch/intensity analysis.

Quality implications:

- Analysis-only; it does not produce replacement audio.
- Downsampling/downmixing is appropriate for visualization and does not affect media quality.

Recommended policy:

- No final output replacement needed.

### Voice Recording

Current implementation: native recording writes WAV through macOS helper or Qt audio capture. The Qt backend uses the device format, preferring int16 when supported.

Quality implications:

- This does not use FFmpeg and has no "same as source" source file.
- It may produce WAV matching the recording device format.

Recommended policy:

- Leave out of source-preserving re-encode work unless adding a separate recording-output setting.

## Implementation Implications

The key implementation boundary should be a resolved output policy, not scattered format strings.

Suggested primitives:

- `probe_audio_metadata(source_path, config)` using `ffprobe` to read codec name, container/format, sample rate, channels/channel layout, bit rate, bits per sample where available, and visible extension.
- `resolve_output_policy(source_path, operation, config, requested_format=None)` returning final extension, MIME type, codec args, and whether stream copy/remux is allowed.
- `build_audio_encode_command(...)` and `build_filtered_audio_render_command(...)` that accept policy-derived codec args instead of choosing MP3 internally.
- `make_output_filename(..., output_format=...)` should receive a concrete resolved extension, or a new helper should create filenames from an already resolved output policy.

Default user-facing behavior needs one product decision:

- Option A: concrete default stays MP3, add "Same as source" as an opt-in output format.
- Option B: default becomes "Same as source" and falls back to MP3/M4A for unsupported or risky formats.
- Option C: use "Same as source" only for edit operations, but keep generated operations such as pitch-hum and voice-only on the configured concrete output format.

## Recommended Replacement Order

1. Add metadata probing and output-policy helpers with unit tests.
2. Replace command builders in `audio_commands.py` and `audio_commands_runtime.py` with policy-accepting final encode builders.
3. Update editor and batch workers to resolve filename extension before rendering.
4. Update pause-removal artifact path and MIME handling.
5. Update denoise and pitch-hum renderers to use generic final encode.
6. Update tests and e2e expectations from "always MP3" to operation-specific output policy.

## Bottom Line

The forced MP3 behavior is concentrated and replaceable, but exact audio edits and most model-based transforms still require decode/process/re-encode. Source-quality preservation should therefore mean:

- preserve original container/codec characteristics only where the operation does not inherently require a destructive transform;
- otherwise preserve compatible sample rate/channel/bitrate choices where possible;
- avoid unnecessary MP3 transcodes;
- explicitly document exceptions where downmixing, downsampling, or synthesis is inherent to the algorithm.
