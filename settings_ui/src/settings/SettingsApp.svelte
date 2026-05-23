<script lang="ts">
  import { onMount } from "svelte";
  import "./styles.css";

  import { handleAsyncDone, handleAsyncProgress, startAsyncOp } from "$lib/async-jobs.js";
  import {
    copySupportReport,
    registerCallbacks,
    settingsCancel,
    settingsResetDefaults,
    settingsSave,
  } from "$lib/bridge.js";
  import { configureI18n, t } from "$lib/i18n.js";
  import { logger } from "$lib/logger.js";
  import type {
    AsyncDonePayload,
    AsyncProgressPayload,
    HealthReport,
    SaveErrorPayload,
  } from "$lib/types.js";
  import DiagnosticsPanel from "./DiagnosticsPanel.svelte";
  import GeneralSettingsPanel from "./GeneralSettingsPanel.svelte";
  import SettingsFooter from "./SettingsFooter.svelte";
  import {
    cloneConfig,
    initialSettingsState,
    messageFromError,
    saveConfigPayload,
    type SettingsTab,
  } from "./settings-state.js";

  const initialState = initialSettingsState();
  configureI18n(initialState.locale, initialState.direction, initialState.messages);

  let config = $state(cloneConfig(initialState.config));
  let activeTab = $state<SettingsTab>("general");
  let saveError = $state("");
  let healthMessage = $state(t("settings.health.not_run"));
  let healthReport = $state<HealthReport | null>(null);
  let healthProgress = $state<AsyncProgressPayload | null>(null);
  let diagnosticsMessage = $state("");

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
    healthMessage = t("settings.health.running");
    diagnosticsMessage = "";
    healthProgress = null;
    try {
      const result = await startAsyncOp("health_check", { config });
      healthReport = result;
      healthMessage = t("settings.health.completed");
    } catch (error) {
      const message = messageFromError(error);
      healthMessage = message;
      logger.error("health check failed", { message });
    }
  }

  async function copyLatestSupportReport(): Promise<void> {
    diagnosticsMessage = t("settings.support.preparing");
    healthProgress = null;
    try {
      const result = await startAsyncOp("support_report", { config });
      copySupportReport(result.reportText);
      diagnosticsMessage = t("settings.support.copied");
    } catch (error) {
      const message = messageFromError(error);
      diagnosticsMessage = message;
      logger.error("support report failed", { message });
    }
  }

  async function showLogFile(): Promise<void> {
    diagnosticsMessage = t("settings.log.opening");
    healthProgress = null;
    try {
      const result = await startAsyncOp("show_log_file", {});
      diagnosticsMessage = t("settings.log.opened", { path: result.logFilePath });
    } catch (error) {
      const message = messageFromError(error);
      diagnosticsMessage = message;
      logger.error("show log file failed", { message });
    }
  }

  function saveConfig(): void {
    settingsSave(saveConfigPayload(config));
  }
</script>

<div class="settings-root" dir={initialState.direction} lang={initialState.locale}>
  <header class="hero">
    <div>
      <p class="eyebrow">{t("app.name")}</p>
      <h1>{t("settings.title")}</h1>
      <p class="summary">
        {t("settings.summary")}
      </p>
    </div>
    <div class="version-pill">v{initialState.version}</div>
  </header>

  <div class="tab-nav" role="tablist" aria-label={t("settings.tabs.label")}>
    <button
      class="settings-tab"
      class:active={activeTab === "general"}
      role="tab"
      aria-selected={activeTab === "general"}
      type="button"
      onclick={() => (activeTab = "general")}
    >
      {t("settings.tab.general")}
    </button>
    <button
      class="settings-tab"
      class:active={activeTab === "diagnostics"}
      data-testid="settings-tab-diagnostics"
      role="tab"
      aria-selected={activeTab === "diagnostics"}
      type="button"
      onclick={() => (activeTab = "diagnostics")}
    >
      {t("settings.tab.diagnostics")}
    </button>
  </div>

  <section class="panel" role="tabpanel">
    {#if activeTab === "general"}
      <GeneralSettingsPanel bind:config saveError={saveError} />
    {:else}
      <DiagnosticsPanel
        initialState={initialState}
        healthMessage={healthMessage}
        healthReport={healthReport}
        healthProgress={healthProgress}
        diagnosticsMessage={diagnosticsMessage}
        onRunHealthCheck={runHealthCheck}
        onCopySupportReport={copyLatestSupportReport}
        onShowLogFile={showLogFile}
      />
    {/if}
  </section>

  <SettingsFooter
    onResetDefaults={settingsResetDefaults}
    onCancel={settingsCancel}
    onSave={saveConfig}
  />
</div>

<style>
  :global(body) {
    background: var(--canvas, Canvas);
    color: var(--fg, CanvasText);
    color-scheme: light dark;
    font-family: inherit;
    margin: 0;
  }

  .settings-root {
    background:
      radial-gradient(circle at top, color-mix(in srgb, var(--canvas-elevated, Canvas) 74%, transparent), transparent 48%),
      var(--canvas, Canvas);
    box-sizing: border-box;
    color: var(--fg, CanvasText);
    min-height: 100vh;
    padding: 28px 28px 120px;
  }

  .hero,
  .tab-nav,
  .panel {
    margin: 0 auto;
    max-width: 920px;
  }

  .hero {
    align-items: flex-start;
    display: flex;
    gap: 16px;
    justify-content: space-between;
    margin-bottom: 24px;
  }

  .eyebrow {
    color: var(--fg-subtle, currentColor);
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    margin: 0 0 6px;
    text-transform: uppercase;
  }

  h1 {
    font-size: 2rem;
    line-height: 1.1;
    margin: 0;
  }

  .summary {
    color: var(--fg-subtle, currentColor);
    max-width: 38rem;
  }

  .version-pill {
    background: color-mix(in srgb, var(--canvas-elevated, Canvas) 88%, transparent);
    border: 1px solid color-mix(in srgb, var(--border, currentColor) 76%, transparent);
    border-radius: 999px;
    font-weight: 600;
    padding: 10px 14px;
  }

  .tab-nav {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }

  .settings-tab {
    appearance: none;
    background: color-mix(in srgb, var(--canvas-elevated, Canvas) 72%, transparent);
    border: 1px solid color-mix(in srgb, var(--border-subtle, var(--border, currentColor)) 80%, transparent);
    border-radius: 999px;
    color: var(--fg, currentColor);
    cursor: pointer;
    font: inherit;
    min-height: 42px;
    padding: 10px 16px;
    transition:
      background-color 120ms ease,
      border-color 120ms ease,
      transform 120ms ease;
  }

  .settings-tab:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
    transform: translateY(-1px);
  }

  .settings-tab.active {
    background: color-mix(in srgb, var(--button-gradient-start, var(--button-bg, transparent)) 72%, transparent);
    border-color: var(--border-focus, var(--border, currentColor));
    font-weight: 700;
  }

  @media (max-width: 720px) {
    .settings-root {
      padding: 20px;
    }

    .hero {
      align-items: stretch;
      flex-direction: column;
    }

    .tab-nav {
      flex-wrap: wrap;
    }
  }
</style>
