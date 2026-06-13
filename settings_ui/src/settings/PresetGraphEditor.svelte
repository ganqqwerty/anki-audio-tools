<script lang="ts">
  import { t } from "$lib/i18n.js";
  import type {
    AudioProcessingPresetGraph,
    AudioProcessingPresetGraphParameters,
  } from "$lib/types.js";
  import {
    GRAPH_RECORDING_CONDITIONS,
    GRAPH_SMOOTHNESSES,
    GRAPH_VOICE_LOCKS,
    GRAPH_VOICE_RANGES,
    formatGraphRecordingCondition,
    formatGraphVoiceLock,
    formatGraphVoiceRange,
  } from "$lib/graph-option-copy.js";

  interface Props {
    graph: AudioProcessingPresetGraph;
    onChange: (graph: AudioProcessingPresetGraph) => void;
  }

  const { graph, onChange }: Props = $props();

  function setEnabled(enabled: boolean): void {
    onChange({ ...graph, enabled });
  }

  function updateParameters(parameters: Partial<AudioProcessingPresetGraphParameters>): void {
    onChange({
      ...graph,
      parameters: {
        ...graph.parameters,
        ...parameters,
      },
    });
  }

  function updateDropouts(event: Event): void {
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (Number.isNaN(value)) return;
    updateParameters({ graph_connect_short_dropouts_ms: value });
  }
</script>

<div class="preset-subsection">
  <label class="settings-toggle">
    <input
      type="checkbox"
      checked={graph.enabled}
      data-testid="preset-graph-enabled"
      onchange={(event) => setEnabled((event.currentTarget as HTMLInputElement).checked)}
    />
    <span class="settings-label-text">{t("settings.presets.graph_enabled")}</span>
  </label>

  {#if graph.enabled}
    <div class="settings-grid">
      <label class="settings-field">
        <span>{t("settings.graph_voice_range")}</span>
        <select
          class="settings-select"
          value={graph.parameters.graph_voice_range}
          onchange={(event) => updateParameters({ graph_voice_range: (event.currentTarget as HTMLSelectElement).value as AudioProcessingPresetGraphParameters["graph_voice_range"] })}
        >
          {#each GRAPH_VOICE_RANGES as option}
            <option value={option}>{formatGraphVoiceRange(option)}</option>
          {/each}
        </select>
      </label>
      <label class="settings-field">
        <span>{t("settings.graph_recording_condition")}</span>
        <select
          class="settings-select"
          value={graph.parameters.graph_recording_condition}
          onchange={(event) => updateParameters({ graph_recording_condition: (event.currentTarget as HTMLSelectElement).value as AudioProcessingPresetGraphParameters["graph_recording_condition"] })}
        >
          {#each GRAPH_RECORDING_CONDITIONS as option}
            <option value={option}>{formatGraphRecordingCondition(option)}</option>
          {/each}
        </select>
      </label>
      <label class="settings-field">
        <span>{t("settings.graph_smoothness")}</span>
        <select
          class="settings-select"
          value={graph.parameters.graph_smoothness}
          onchange={(event) => updateParameters({ graph_smoothness: (event.currentTarget as HTMLSelectElement).value as AudioProcessingPresetGraphParameters["graph_smoothness"] })}
        >
          {#each GRAPH_SMOOTHNESSES as option}
            <option value={option}>{t(`settings.graph_smoothness.${option}`)}</option>
          {/each}
        </select>
      </label>
      <label class="settings-field">
        <span>{t("settings.graph_connect_short_dropouts_ms")}</span>
        <input
          class="settings-input"
          type="number"
          min="0"
          max="500"
          step="30"
          value={graph.parameters.graph_connect_short_dropouts_ms}
          oninput={updateDropouts}
        />
      </label>
      <label class="settings-field">
        <span>{t("settings.graph_voice_lock")}</span>
        <select
          class="settings-select"
          value={graph.parameters.graph_voice_lock}
          onchange={(event) => updateParameters({ graph_voice_lock: (event.currentTarget as HTMLSelectElement).value as AudioProcessingPresetGraphParameters["graph_voice_lock"] })}
        >
          {#each GRAPH_VOICE_LOCKS as option}
            <option value={option}>{formatGraphVoiceLock(option)}</option>
          {/each}
        </select>
      </label>
    </div>
  {/if}
</div>
