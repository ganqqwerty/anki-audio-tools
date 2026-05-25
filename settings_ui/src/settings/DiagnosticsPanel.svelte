<script lang="ts">
  import { t } from "$lib/i18n.js";
  import type { AsyncProgressPayload, Config, HealthReport, InitialState } from "$lib/types.js";
  import DiagnosticsLinks from "./DiagnosticsLinks.svelte";

  type DiagnosticsAction = () => void | Promise<void>;

  let {
    initialState,
    healthMessage,
    healthReport,
    healthProgress,
    diagnosticsMessage,
    config = $bindable(),
    onRunHealthCheck,
    onCheckMedia,
    onCopySupportReport,
    onShowLogFile,
  }: {
    diagnosticsMessage: string;
    config: Config;
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

<div class="settings-card settings-stack diagnostics-panel">
  <h2>{t("diagnostics.title")}</h2>

  <section class="settings-section">
    <div class="settings-grid diagnostics-config-grid">
      <label class="settings-toggle">
        <input type="checkbox" bind:checked={config.debug_logging} />
        <span class="settings-label-text">{t("settings.debug_logging")}</span>
      </label>
      <label class="settings-toggle">
        <input type="checkbox" bind:checked={config.show_ffmpeg_commands} />
        <span class="settings-label-text">{t("settings.show_ffmpeg_commands")}</span>
      </label>
      <label class="settings-field diagnostics-path-field">
        <span>{t("settings.ffmpeg_path")}</span>
        <input class="settings-input diagnostics-path-input" type="text" bind:value={config.ffmpeg_path} />
        <span class="settings-muted">{t("settings.ffmpeg_path.help")}</span>
      </label>
    </div>
  </section>

  <section class="settings-section">
    <dl class="meta-list">
      <div class="meta-row">
        <dt>{t("diagnostics.addon_id")}</dt>
        <dd>{initialState.diagnostics.addon_id}</dd>
      </div>
      <div class="meta-row">
        <dt>{t("diagnostics.collection_available")}</dt>
        <dd>{initialState.diagnostics.collection_available ? t("diagnostics.yes") : t("diagnostics.no")}</dd>
      </div>
      <div class="meta-row">
        <dt>{t("diagnostics.addon_folder")}</dt>
        <dd>{initialState.addon_dir}</dd>
      </div>
      <div class="meta-row">
        <dt>{t("diagnostics.log_file")}</dt>
        <dd>{initialState.log_file_path}</dd>
      </div>
      <div class="meta-row">
        <dt>{t("diagnostics.release_commit")}</dt>
        <dd>{initialState.diagnostics.release_info.commit_hash || "n/a"}</dd>
      </div>
      <div class="meta-row">
        <dt>{t("diagnostics.release_message")}</dt>
        <dd>{initialState.diagnostics.release_info.commit_message || "n/a"}</dd>
      </div>
    </dl>
  </section>

  <section class="settings-section diagnostics-actions-section">
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
    </div>

    <div class="diagnostics-status">
      {#if healthProgress}
        <p class="settings-muted progress-message" data-testid="health-progress">
          {healthProgress.progress}% - {healthProgress.message}
        </p>
      {/if}
      <p class="settings-muted" data-testid="health-message">{healthMessage}</p>
      <p class="settings-muted" data-testid="diagnostics-message">{diagnosticsMessage}</p>
    </div>
  </section>

  <DiagnosticsLinks />

  {#if healthReport}
    <section class="settings-section">
      <pre class="report" data-testid="health-report">{JSON.stringify(healthReport, null, 2)}</pre>
    </section>
  {/if}
</div>

<style>
  h2 {
    margin-top: 0;
  }

  .diagnostics-panel {
    gap: 14px;
  }

  .diagnostics-config-grid {
    align-items: start;
  }

  .diagnostics-path-field {
    min-width: 0;
  }

  .diagnostics-path-input {
    width: min(100%, 420px);
  }

  .meta-list {
    display: grid;
    gap: 0;
    margin: 0;
  }

  .meta-row {
    border-top: 1px solid color-mix(in srgb, var(--border-subtle, var(--border, currentColor)) 80%, transparent);
    column-gap: 18px;
    display: grid;
    grid-template-columns: minmax(150px, 220px) minmax(0, 1fr);
    margin: 0;
    padding: 10px 0;
  }

  .meta-row:first-child {
    border-top: 0;
    padding-top: 0;
  }

  dt {
    color: var(--fg-subtle, currentColor);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin: 0;
    text-transform: uppercase;
  }

  dd {
    margin: 0;
    word-break: break-word;
  }

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .diagnostics-status {
    display: grid;
    gap: 6px;
  }

  .diagnostics-status p {
    margin: 0;
  }

  .report {
    background: var(--canvas, Canvas);
    border: 1px solid color-mix(in srgb, var(--border, currentColor) 78%, transparent);
    color: var(--fg, currentColor);
    margin: 0;
    overflow: auto;
    padding: 12px;
  }

  .progress-message {
    margin: 0;
  }

  @media (max-width: 720px) {
    .meta-row {
      grid-template-columns: 1fr;
      row-gap: 4px;
    }

    .diagnostics-path-input {
      width: 100%;
    }
  }
</style>
