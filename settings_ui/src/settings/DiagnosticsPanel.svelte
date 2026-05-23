<script lang="ts">
  import { t } from "$lib/i18n.js";
  import type { AsyncProgressPayload, HealthReport, InitialState } from "$lib/types.js";

  type DiagnosticsAction = () => void | Promise<void>;

  let {
    initialState,
    healthMessage,
    healthReport,
    healthProgress,
    diagnosticsMessage,
    onRunHealthCheck,
    onCheckMedia,
    onCopySupportReport,
    onShowLogFile,
  }: {
    diagnosticsMessage: string;
    healthMessage: string;
    healthProgress: AsyncProgressPayload | null;
    healthReport: HealthReport | null;
    initialState: InitialState;
    onCheckMedia: DiagnosticsAction;
    onCopySupportReport: DiagnosticsAction;
    onRunHealthCheck: DiagnosticsAction;
    onShowLogFile: DiagnosticsAction;
  } = $props();
</script>

<div class="settings-card settings-stack">
  <h2>{t("diagnostics.title")}</h2>
  <dl class="meta-grid">
    <div>
      <dt>{t("diagnostics.addon_id")}</dt>
      <dd>{initialState.diagnostics.addon_id}</dd>
    </div>
    <div>
      <dt>{t("diagnostics.collection_available")}</dt>
      <dd>{initialState.diagnostics.collection_available ? t("diagnostics.yes") : t("diagnostics.no")}</dd>
    </div>
    <div>
      <dt>{t("diagnostics.addon_folder")}</dt>
      <dd>{initialState.addon_dir}</dd>
    </div>
    <div>
      <dt>{t("diagnostics.log_file")}</dt>
      <dd>{initialState.log_file_path}</dd>
    </div>
  </dl>

  <div class="actions">
    <button
      type="button"
      class="settings-button settings-button-primary"
      data-testid="run-health-check"
      onclick={onRunHealthCheck}
    >
      {t("diagnostics.run_health_check")}
    </button>
    <button
      type="button"
      class="settings-button"
      data-testid="check-media"
      onclick={onCheckMedia}
    >
      {t("diagnostics.check_media")}
    </button>
    <button
      type="button"
      class="settings-button"
      data-testid="copy-support-report"
      onclick={onCopySupportReport}
    >
      {t("diagnostics.copy_support_report")}
    </button>
    <button
      type="button"
      class="settings-button"
      data-testid="show-log-file"
      onclick={onShowLogFile}
    >
      {t("diagnostics.show_log_file")}
    </button>
    {#if healthProgress}
      <p class="settings-muted progress-message" data-testid="health-progress">
        {healthProgress.progress}% - {healthProgress.message}
      </p>
    {/if}
  </div>

  <p class="settings-muted" data-testid="health-message">{healthMessage}</p>
  <p class="settings-muted" data-testid="diagnostics-message">{diagnosticsMessage}</p>

  {#if healthReport}
    <pre class="report" data-testid="health-report">{JSON.stringify(healthReport, null, 2)}</pre>
  {/if}
</div>

<style>
  h2 {
    margin-top: 0;
  }

  .meta-grid {
    display: grid;
    gap: 14px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }

  .meta-grid > div {
    background: color-mix(in srgb, var(--canvas-inset, transparent) 58%, transparent);
    border: 1px solid color-mix(in srgb, var(--border-subtle, var(--border, currentColor)) 72%, transparent);
    border-radius: 18px;
    padding: 14px 16px;
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
    flex-wrap: wrap;
    gap: 12px;
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

  .progress-message {
    margin: 0;
  }
</style>
