<script lang="ts">
  import { onMount } from "svelte";

  import { handleAsyncDone, handleAsyncProgress, startAsyncOp } from "$lib/async-jobs.js";
  import {
    copySupportReport,
    registerCallbacks,
    settingsCancel,
    settingsResetDefaults,
    settingsSave,
  } from "$lib/bridge.js";
  import { logger } from "$lib/logger.js";
  import type {
    AsyncDonePayload,
    AsyncProgressPayload,
    Config,
    HealthReport,
    InitialState,
    SaveErrorPayload,
    ShowLogFileResult,
    SupportReportResult,
  } from "$lib/types.js";

  const initialState: InitialState = window.__INITIAL_STATE__ ?? {
    config: {
      _config_version: 7,
      enabled: true,
      debug_logging: false,
      show_ffmpeg_commands: false,
      manual_trim_small_ms: 100,
      manual_trim_large_ms: 500,
      speed_step: 0.05,
      min_speed: 0.75,
      max_speed: 1.5,
      volume_step_db: 3.0,
      min_volume_db: -24.0,
      max_volume_db: 24.0,
      internal_pause_silence_threshold_db: -45,
      internal_pause_threshold_ms: 300,
      internal_pause_target_gap_ms: 100,
      output_format: "mp3",
      ffmpeg_path: "",
      deep_filter_path: "",
      deep_filter_post_filter: true,
    },
    version: "",
    addon_dir: "",
    log_file_path: "",
    diagnostics: {
      addon_id: "",
      collection_available: false,
    },
  };

  let config = $state<Config>(structuredClone(initialState.config));
  let activeTab = $state<"general" | "diagnostics">("general");
  let saveError = $state<string>("");
  let healthMessage = $state<string>("Not run yet");
  let healthReport = $state<HealthReport | null>(null);
  let healthProgress = $state<AsyncProgressPayload | null>(null);
  let diagnosticsMessage = $state<string>("");

  onMount(() => {
    registerCallbacks({
      onAsyncProgress: (payload: AsyncProgressPayload) => {
        healthProgress = payload;
        handleAsyncProgress(payload);
      },
      onAsyncDone: (payload: AsyncDonePayload) => {
        handleAsyncDone(payload);
      },
      onSaveError: (payload: SaveErrorPayload) => {
        saveError = payload.error;
      },
    });
    logger.info("audio quick editor settings UI mounted", { version: initialState.version });
  });

  async function runHealthCheck(): Promise<void> {
    healthMessage = "Running health check...";
    diagnosticsMessage = "";
    healthProgress = null;
    try {
      const result = await startAsyncOp("health_check", { config }) as HealthReport;
      healthReport = result;
      healthMessage = "Health check completed";
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      healthMessage = message;
      logger.error("health check failed", { message });
    }
  }

  async function copyLatestSupportReport(): Promise<void> {
    diagnosticsMessage = "Preparing support report...";
    healthProgress = null;
    try {
      const result = await startAsyncOp("support_report", { config }) as SupportReportResult;
      copySupportReport(result.reportText);
      diagnosticsMessage = "Support report copied";
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      diagnosticsMessage = message;
      logger.error("support report failed", { message });
    }
  }

  async function showLogFile(): Promise<void> {
    diagnosticsMessage = "Opening log file...";
    healthProgress = null;
    try {
      const result = await startAsyncOp("show_log_file", {}) as ShowLogFileResult;
      diagnosticsMessage = `Log file opened: ${result.logFilePath}`;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      diagnosticsMessage = message;
      logger.error("show log file failed", { message });
    }
  }

  function saveConfig(): void {
    settingsSave({ ...config, enabled: true });
  }
</script>

<div class="settings-root">
  <header class="hero">
    <div>
      <p class="eyebrow">Anki Audio Quick Editor</p>
      <h1>Audio Quick Editor Settings</h1>
      <p class="summary">
        Tune quick inline audio edits while keeping original Anki media untouched.
      </p>
    </div>
    <div class="version-pill">v{initialState.version}</div>
  </header>

  <div class="tab-nav" role="tablist" aria-label="Settings sections">
    <button
      class:active={activeTab === "general"}
      role="tab"
      aria-selected={activeTab === "general"}
      type="button"
      onclick={() => (activeTab = "general")}
    >
      General
    </button>
    <button
      class:active={activeTab === "diagnostics"}
      data-testid="settings-tab-diagnostics"
      role="tab"
      aria-selected={activeTab === "diagnostics"}
      type="button"
      onclick={() => (activeTab = "diagnostics")}
    >
      Diagnostics &amp; About
    </button>
  </div>

  <section class="panel" role="tabpanel">
    {#if activeTab === "general"}
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
          <span>Use DeepFilterNet post-filter</span>
        </label>
        <div class="settings-grid">
          <label>
            <span>Small trim step (ms)</span>
            <input type="number" min="1" bind:value={config.manual_trim_small_ms} />
          </label>
          <label>
            <span>Large trim step (ms)</span>
            <input type="number" min="1" bind:value={config.manual_trim_large_ms} />
          </label>
          <label>
            <span>Speed step</span>
            <input type="number" min="0.01" step="0.01" bind:value={config.speed_step} />
          </label>
          <label>
            <span>Min speed</span>
            <input type="number" min="0.1" step="0.05" bind:value={config.min_speed} />
          </label>
          <label>
            <span>Max speed</span>
            <input type="number" min="0.1" step="0.05" bind:value={config.max_speed} />
          </label>
          <label>
            <span>Volume step (dB)</span>
            <input type="number" min="0.1" step="0.1" bind:value={config.volume_step_db} />
          </label>
          <label>
            <span>Min volume (dB)</span>
            <input type="number" step="0.1" bind:value={config.min_volume_db} />
          </label>
          <label>
            <span>Max volume (dB)</span>
            <input type="number" step="0.1" bind:value={config.max_volume_db} />
          </label>
          <label>
            <span>Internal pause silence threshold (dB)</span>
            <input type="number" bind:value={config.internal_pause_silence_threshold_db} />
          </label>
          <label>
            <span>Pause threshold (ms)</span>
            <input type="number" min="1" bind:value={config.internal_pause_threshold_ms} />
          </label>
          <label>
            <span>Pause target gap (ms)</span>
            <input type="number" min="1" bind:value={config.internal_pause_target_gap_ms} />
          </label>
        </div>
        {#if saveError}
          <p class="error" data-testid="save-error">{saveError}</p>
        {/if}
      </div>
    {:else}
      <div class="card">
        <h2>Diagnostics</h2>
        <dl class="meta-grid">
          <div>
            <dt>Add-on ID</dt>
            <dd>{initialState.diagnostics.addon_id}</dd>
          </div>
          <div>
            <dt>Collection available</dt>
            <dd>{initialState.diagnostics.collection_available ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt>Add-on folder</dt>
            <dd>{initialState.addon_dir}</dd>
          </div>
          <div>
            <dt>Log file</dt>
            <dd>{initialState.log_file_path}</dd>
          </div>
        </dl>

        <div class="actions">
          <button
            type="button"
            class="btn btn-primary"
            data-testid="run-health-check"
            onclick={runHealthCheck}
          >
            Run Health Check
          </button>
          <button
            type="button"
            class="btn btn-secondary"
            data-testid="copy-support-report"
            onclick={copyLatestSupportReport}
          >
            Copy Support Report
          </button>
          <button
            type="button"
            class="btn btn-secondary"
            data-testid="show-log-file"
            onclick={showLogFile}
          >
            Show Log File
          </button>
          {#if healthProgress}
            <p class="muted" data-testid="health-progress">
              {healthProgress.progress}% - {healthProgress.message}
            </p>
          {/if}
        </div>

        <p class="muted" data-testid="health-message">{healthMessage}</p>
        <p class="muted" data-testid="diagnostics-message">{diagnosticsMessage}</p>

        {#if healthReport}
          <pre class="report" data-testid="health-report">{JSON.stringify(healthReport, null, 2)}</pre>
        {/if}
      </div>
    {/if}
  </section>

  <footer class="footer">
    <button type="button" class="btn btn-secondary" onclick={settingsResetDefaults}>
      Reset Defaults
    </button>
    <div class="footer-actions">
      <button type="button" class="btn btn-secondary" onclick={settingsCancel}>
        Cancel
      </button>
      <button type="button" class="btn btn-primary" onclick={saveConfig}>
        Save
      </button>
    </div>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Avenir Next", "Segoe UI", sans-serif;
  }

  .settings-root {
    min-height: 100vh;
    padding: 28px;
    box-sizing: border-box;
  }

  .hero,
  .footer,
  .tab-nav,
  .panel {
    max-width: 920px;
    margin: 0 auto;
  }

  .hero {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .eyebrow {
    margin: 0 0 6px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-size: 0.78rem;
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    line-height: 1.1;
  }

  .summary {
    max-width: 38rem;
  }

  .version-pill {
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid;
    font-weight: 600;
  }

  .tab-nav {
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
  }

  .tab-nav button,
  .btn {
    appearance: none;
    border: 1px solid;
    border-radius: 999px;
    padding: 10px 16px;
    cursor: pointer;
    font: inherit;
  }

  .tab-nav button.active {
    font-weight: 700;
    text-decoration: underline;
  }

  .panel .card {
    border: 1px solid;
    border-radius: 24px;
    padding: 24px;
    box-shadow: none;
  }

  h2 {
    margin-top: 0;
  }

  .toggle {
    display: flex;
    gap: 12px;
    align-items: center;
    padding: 12px 0;
  }

  .field-row,
  .settings-grid label {
    display: grid;
    gap: 6px;
    font-weight: 700;
  }

  .field-row {
    margin: 14px 0;
  }

  .settings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 14px;
    margin-top: 18px;
  }

  input[type="text"],
  input[type="number"] {
    border: 1px solid;
    border-radius: 12px;
    font: inherit;
    font-weight: 500;
    padding: 10px 12px;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
  }

  dt {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  dd {
    margin: 6px 0 0;
    word-break: break-word;
  }

  .actions {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-top: 18px;
  }

  .report {
    margin-top: 16px;
    padding: 16px;
    border-radius: 18px;
    overflow: auto;
  }

  .footer {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    margin-top: 18px;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  .btn-primary {
    font-weight: 700;
  }

  .error {
    font-weight: 600;
  }

  @media (max-width: 720px) {
    .settings-root {
      padding: 16px;
    }

    .hero,
    .footer {
      flex-direction: column;
    }

    .footer-actions {
      width: 100%;
    }

    .footer-actions .btn,
    .footer > .btn {
      flex: 1;
    }

    .tab-nav {
      flex-wrap: wrap;
    }
  }
</style>
