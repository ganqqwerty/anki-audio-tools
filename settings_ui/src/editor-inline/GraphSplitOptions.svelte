<script lang="ts">
  import { t } from "../lib/i18n.js";
  import {
    formatGraphRecordingCondition,
    formatGraphSmoothness,
    formatGraphVoiceLock,
    formatGraphVoiceRange,
    GRAPH_RECORDING_CONDITIONS,
    GRAPH_SMOOTHNESSES,
    GRAPH_VOICE_LOCKS,
    GRAPH_VOICE_RANGES,
  } from "./graph-split-values.js";
  import type {
    GraphRecordingCondition,
    GraphSmoothness,
    GraphVoiceLock,
    GraphVoiceRange,
  } from "./graph-settings.js";

  const {
    connectShortDropoutsMs,
    onConnectShortDropouts,
    onRecordingCondition,
    onSmoothness,
    onVoiceLock,
    onVoiceRange,
    recordingCondition,
    slug,
    smoothness,
    targetOrd,
    voiceLock,
    voiceRange,
  }: {
    connectShortDropoutsMs: number;
    onConnectShortDropouts: (value: number) => void;
    onRecordingCondition: (value: GraphRecordingCondition) => void;
    onSmoothness: (value: GraphSmoothness) => void;
    onVoiceLock: (value: GraphVoiceLock) => void;
    onVoiceRange: (value: GraphVoiceRange) => void;
    recordingCondition: GraphRecordingCondition;
    slug: string;
    smoothness: GraphSmoothness;
    targetOrd: number;
    voiceLock: GraphVoiceLock;
    voiceRange: GraphVoiceRange;
  } = $props();

  function optionIndex<T extends string>(values: readonly T[], value: T): number {
    return Math.max(0, values.indexOf(value));
  }

  function optionAt<T extends string>(values: readonly T[], index: number): T {
    return (values[Math.max(0, Math.min(values.length - 1, Math.round(index)))] ?? values[0]) as T;
  }
</script>

<div class="aqe-graph-options">
  <label class="aqe-graph-option">
    <span>{t("editor.graph.options.voice_range")}</span>
    <input
      data-testid={`aqe-split-${targetOrd}-${slug}-voice-range`}
      type="range"
      min="0"
      max={GRAPH_VOICE_RANGES.length - 1}
      step="1"
      value={optionIndex(GRAPH_VOICE_RANGES, voiceRange)}
      oninput={(event) => {
        onVoiceRange(optionAt(GRAPH_VOICE_RANGES, (event.currentTarget as HTMLInputElement).valueAsNumber));
      }}
    />
    <span class="aqe-graph-option-value">{formatGraphVoiceRange(voiceRange)}</span>
  </label>
  <label class="aqe-graph-option">
    <span>{t("editor.graph.options.recording_condition")}</span>
    <input
      data-testid={`aqe-split-${targetOrd}-${slug}-recording-condition`}
      type="range"
      min="0"
      max={GRAPH_RECORDING_CONDITIONS.length - 1}
      step="1"
      value={optionIndex(GRAPH_RECORDING_CONDITIONS, recordingCondition)}
      oninput={(event) => {
        onRecordingCondition(
          optionAt(GRAPH_RECORDING_CONDITIONS, (event.currentTarget as HTMLInputElement).valueAsNumber),
        );
      }}
    />
    <span class="aqe-graph-option-value">{formatGraphRecordingCondition(recordingCondition)}</span>
  </label>
  <label class="aqe-graph-option">
    <span>{t("editor.graph.options.smoothness")}</span>
    <input
      data-testid={`aqe-split-${targetOrd}-${slug}-smoothness`}
      type="range"
      min="0"
      max={GRAPH_SMOOTHNESSES.length - 1}
      step="1"
      value={optionIndex(GRAPH_SMOOTHNESSES, smoothness)}
      oninput={(event) => {
        onSmoothness(optionAt(GRAPH_SMOOTHNESSES, (event.currentTarget as HTMLInputElement).valueAsNumber));
      }}
    />
    <span class="aqe-graph-option-value">{formatGraphSmoothness(smoothness)}</span>
  </label>
  <label class="aqe-graph-option">
    <span>{t("editor.graph.options.connect_dropouts")}</span>
    <input
      data-testid={`aqe-split-${targetOrd}-${slug}-connect-dropouts`}
      type="range"
      min="0"
      max="500"
      step="30"
      value={connectShortDropoutsMs}
      oninput={(event) => onConnectShortDropouts((event.currentTarget as HTMLInputElement).valueAsNumber)}
    />
    <span class="aqe-graph-option-value">{connectShortDropoutsMs} ms</span>
  </label>
  <details class="aqe-graph-advanced">
    <summary>{t("editor.graph.options.voice_lock")}</summary>
    <label class="aqe-graph-option">
      <input
        data-testid={`aqe-split-${targetOrd}-${slug}-voice-lock`}
        type="range"
        min="0"
        max={GRAPH_VOICE_LOCKS.length - 1}
        step="1"
        value={optionIndex(GRAPH_VOICE_LOCKS, voiceLock)}
        oninput={(event) => {
          onVoiceLock(optionAt(GRAPH_VOICE_LOCKS, (event.currentTarget as HTMLInputElement).valueAsNumber));
        }}
      />
      <span class="aqe-graph-option-value">{formatGraphVoiceLock(voiceLock)}</span>
    </label>
  </details>
</div>
