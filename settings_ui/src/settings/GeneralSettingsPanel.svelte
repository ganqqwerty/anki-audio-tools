<script lang="ts">
  import CommandIcon from "$lib/CommandIcon.svelte";
  import type { Config } from "$lib/types.js";

  let {
    config = $bindable(),
    saveError,
  }: {
    config: Config;
    saveError: string;
  } = $props();
</script>

<div class="card">
  <h2>General</h2>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.debug_logging} />
    <span>Enable debug logging</span>
  </label>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.show_ffmpeg_commands} />
    <span>Show ffmpeg commands while processing</span>
  </label>
  <label class="toggle">
    <input
      data-testid="repeat-playback-by-default"
      type="checkbox"
      bind:checked={config.repeat_playback_by_default}
    />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="repeat-2" />
      <span>Repeat playback by default</span>
    </span>
  </label>
  <label class="toggle">
    <input
      data-testid="show-graph-by-default"
      type="checkbox"
      bind:checked={config.show_graph_by_default}
    />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="audio-lines" />
      <span>Show graph by default</span>
    </span>
  </label>
  <label class="field-row">
    <span>ffmpeg path</span>
    <input
      type="text"
      bind:value={config.ffmpeg_path}
      placeholder="Leave blank to use PATH"
    />
  </label>
  <label class="field-row">
    <span>DeepFilterNet path</span>
    <input
      type="text"
      bind:value={config.deep_filter_path}
      placeholder="Leave blank to use bundled binary, then PATH"
    />
  </label>
  <label class="toggle">
    <input type="checkbox" bind:checked={config.deep_filter_post_filter} />
    <span class="label-with-icon">
      <CommandIcon className="settings-label-icon" icon="volume-x" />
      <span>Use DeepFilterNet post-filter</span>
    </span>
  </label>
  <div class="settings-grid">
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="scissors" />
        <span>Small trim step (ms)</span>
      </span>
      <input type="number" min="1" bind:value={config.manual_trim_small_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="scissors" />
        <span>Large trim step (ms)</span>
      </span>
      <input type="number" min="1" bind:value={config.manual_trim_large_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="fast-forward" />
        <span>Speed step</span>
      </span>
      <input type="number" min="0.01" step="0.01" bind:value={config.speed_step} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="rewind" />
        <span>Min speed</span>
      </span>
      <input type="number" min="0.1" step="0.05" bind:value={config.min_speed} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="fast-forward" />
        <span>Max speed</span>
      </span>
      <input type="number" min="0.1" step="0.05" bind:value={config.max_speed} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span>Volume step (dB)</span>
      </span>
      <input type="number" min="0.1" step="0.1" bind:value={config.volume_step_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-1" />
        <span>Min volume (dB)</span>
      </span>
      <input type="number" step="0.1" bind:value={config.min_volume_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="volume-2" />
        <span>Max volume (dB)</span>
      </span>
      <input type="number" step="0.1" bind:value={config.max_volume_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>Internal pause silence threshold (dB)</span>
      </span>
      <input type="number" bind:value={config.internal_pause_silence_threshold_db} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>Pause threshold (ms)</span>
      </span>
      <input type="number" min="1" bind:value={config.internal_pause_threshold_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>Pause target gap (ms)</span>
      </span>
      <input type="number" min="1" bind:value={config.internal_pause_target_gap_ms} />
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="timer-reset" />
        <span>Shorten pauses level</span>
      </span>
      <select bind:value={config.pause_aggressiveness}>
        <option value="gentle">Gentle</option>
        <option value="normal">Normal</option>
        <option value="aggressive">Aggressive</option>
      </select>
    </label>
    <label>
      <span class="label-with-icon">
        <CommandIcon className="settings-label-icon" icon="sparkles" />
        <span>Default denoise algorithm</span>
      </span>
      <select bind:value={config.denoise_algorithm}>
        <option value="standard">Standard</option>
        <option value="rnnoise">RNNoise</option>
      </select>
    </label>
  </div>
  {#if saveError}
    <p class="error" data-testid="save-error">{saveError}</p>
  {/if}
</div>

<style>
  .card {
    background: var(--canvas-elevated, transparent);
    border: 1px solid var(--border, currentColor);
    border-radius: 24px;
    box-shadow: none;
    color: var(--fg, currentColor);
    padding: 24px;
  }

  h2 {
    margin-top: 0;
  }

  .toggle {
    align-items: center;
    display: flex;
    gap: 12px;
    padding: 12px 0;
  }

  .field-row,
  .settings-grid label {
    display: grid;
    font-weight: 700;
    gap: 6px;
  }

  .field-row {
    margin: 14px 0;
  }

  .label-with-icon {
    align-items: center;
    display: inline-flex;
    gap: 8px;
    min-width: 0;
  }

  :global(.settings-label-icon) {
    align-items: center;
    color: var(--fg-subtle, currentColor);
    display: inline-flex;
    flex: 0 0 auto;
  }

  .settings-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    margin-top: 18px;
  }

  input[type="text"],
  input[type="number"],
  select {
    background: var(--canvas-inset, Field);
    border: 1px solid var(--border, currentColor);
    border-radius: 12px;
    color: var(--fg, FieldText);
    font: inherit;
    font-weight: 500;
    padding: 10px 12px;
  }

  input[type="text"]::placeholder,
  input[type="number"]::placeholder {
    color: var(--fg-subtle, currentColor);
  }

  input[type="text"]:focus,
  input[type="number"]:focus,
  select:focus {
    border-color: var(--border-focus, var(--border, currentColor));
    outline: 1px solid var(--border-focus, currentColor);
  }

  .error {
    color: var(--accent-danger, currentColor);
    font-weight: 600;
  }
</style>
