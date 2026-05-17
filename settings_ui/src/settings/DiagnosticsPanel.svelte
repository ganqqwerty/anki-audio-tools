<script lang="ts">
  import type { AsyncProgressPayload, HealthReport, InitialState } from "$lib/types.js";

  type DiagnosticsAction = () => void | Promise<void>;

  let {
    initialState,
    healthMessage,
    healthReport,
    healthProgress,
    diagnosticsMessage,
    onRunHealthCheck,
    onCopySupportReport,
    onShowLogFile,
  }: {
    diagnosticsMessage: string;
    healthMessage: string;
    healthProgress: AsyncProgressPayload | null;
    healthReport: HealthReport | null;
    initialState: InitialState;
    onCopySupportReport: DiagnosticsAction;
    onRunHealthCheck: DiagnosticsAction;
    onShowLogFile: DiagnosticsAction;
  } = $props();
</script>

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
      onclick={onRunHealthCheck}
    >
      Run Health Check
    </button>
    <button
      type="button"
      class="btn btn-secondary"
      data-testid="copy-support-report"
      onclick={onCopySupportReport}
    >
      Copy Support Report
    </button>
    <button
      type="button"
      class="btn btn-secondary"
      data-testid="show-log-file"
      onclick={onShowLogFile}
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

  .meta-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  dt {
    color: var(--fg-subtle, currentColor);
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  dd {
    margin: 6px 0 0;
    word-break: break-word;
  }

  .actions {
    align-items: center;
    display: flex;
    gap: 14px;
    margin-top: 18px;
  }

  .btn {
    appearance: none;
    background: var(--button-bg, transparent);
    border: 1px solid var(--border-subtle, currentColor);
    border-radius: 999px;
    color: var(--fg, currentColor);
    cursor: pointer;
    font: inherit;
    padding: 10px 16px;
  }

  .btn:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
  }

  .btn-primary {
    border-color: var(--border-focus, var(--border, currentColor));
    font-weight: 700;
  }

  .muted {
    color: var(--fg-subtle, currentColor);
  }

  .report {
    background: var(--canvas-code, var(--canvas-inset, transparent));
    border: 1px solid var(--border-subtle, currentColor);
    border-radius: 18px;
    color: var(--fg, currentColor);
    margin-top: 16px;
    overflow: auto;
    padding: 16px;
  }
</style>
