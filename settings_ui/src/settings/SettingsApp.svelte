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

  let config = $state(cloneConfig(initialState.config));
  let activeTab = $state<SettingsTab>("general");
  let saveError = $state("");
  let healthMessage = $state("Not run yet");
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
    healthMessage = "Running health check...";
    diagnosticsMessage = "";
    healthProgress = null;
    try {
      const result = await startAsyncOp("health_check", { config });
      healthReport = result;
      healthMessage = "Health check completed";
    } catch (error) {
      const message = messageFromError(error);
      healthMessage = message;
      logger.error("health check failed", { message });
    }
  }

  async function copyLatestSupportReport(): Promise<void> {
    diagnosticsMessage = "Preparing support report...";
    healthProgress = null;
    try {
      const result = await startAsyncOp("support_report", { config });
      copySupportReport(result.reportText);
      diagnosticsMessage = "Support report copied";
    } catch (error) {
      const message = messageFromError(error);
      diagnosticsMessage = message;
      logger.error("support report failed", { message });
    }
  }

  async function showLogFile(): Promise<void> {
    diagnosticsMessage = "Opening log file...";
    healthProgress = null;
    try {
      const result = await startAsyncOp("show_log_file", {});
      diagnosticsMessage = `Log file opened: ${result.logFilePath}`;
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
    margin: 0;
    font-family: "Avenir Next", "Segoe UI", sans-serif;
  }

  .settings-root {
    box-sizing: border-box;
    min-height: 100vh;
    padding: 28px;
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
    margin-bottom: 20px;
  }

  .eyebrow {
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
    max-width: 38rem;
  }

  .version-pill {
    border: 1px solid;
    border-radius: 999px;
    font-weight: 600;
    padding: 10px 14px;
  }

  .tab-nav {
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
  }

  .tab-nav button {
    appearance: none;
    border: 1px solid;
    border-radius: 999px;
    cursor: pointer;
    font: inherit;
    padding: 10px 16px;
  }

  .tab-nav button.active {
    font-weight: 700;
    text-decoration: underline;
  }

  @media (max-width: 720px) {
    .settings-root {
      padding: 16px;
    }

    .hero {
      flex-direction: column;
    }

    .tab-nav {
      flex-wrap: wrap;
    }
  }
</style>
