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
  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.voice_range")}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.voice_range")}
    >
      {#each GRAPH_VOICE_RANGES as option}
        <button
          type="button"
          class="aqe-button aqe-split-preset"
          data-testid={`aqe-split-${targetOrd}-${slug}-voice-range-${option}`}
          role="radio"
          aria-checked={voiceRange === option ? "true" : "false"}
          tabindex={voiceRange === option ? 0 : -1}
          onclick={() => onVoiceRange(option)}
        >
          {formatGraphVoiceRange(option)}
        </button>
      {/each}
    </div>
  </div>
  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.voice_lock")}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.voice_lock")}
    >
      {#each GRAPH_VOICE_LOCKS as option}
        <button
          type="button"
          class="aqe-button aqe-split-preset"
          data-testid={`aqe-split-${targetOrd}-${slug}-voice-lock-${option}`}
          role="radio"
          aria-checked={voiceLock === option ? "true" : "false"}
          tabindex={voiceLock === option ? 0 : -1}
          onclick={() => onVoiceLock(option)}
        >
          {formatGraphVoiceLock(option)}
        </button>
      {/each}
    </div>
  </div>
  <div class="aqe-graph-option">
    <span>{t("editor.graph.options.smoothness")}</span>
    <div
      class="aqe-split-presets aqe-graph-option-group"
      role="radiogroup"
      aria-label={t("editor.graph.options.smoothness")}
    >
      {#each GRAPH_SMOOTHNESSES as option}
        <button
          type="button"
          class="aqe-button aqe-split-preset"
          data-testid={`aqe-split-${targetOrd}-${slug}-smoothness-${option}`}
          role="radio"
          aria-checked={smoothness === option ? "true" : "false"}
          tabindex={smoothness === option ? 0 : -1}
          onclick={() => onSmoothness(option)}
        >
          {formatGraphSmoothness(option)}
        </button>
      {/each}
    </div>
  </div>
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
</div>
