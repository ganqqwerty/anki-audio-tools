<script lang="ts">
  import { onMount } from "svelte";
  import "./styles.css";

  import AqeTooltipProvider from "$lib/AqeTooltipProvider.svelte";
  import ErrorMessage from "$lib/ErrorMessage.svelte";
  import { handleAsyncDone, handleAsyncProgress, startAsyncOp } from "$lib/async-jobs.js";
  import {
    copySupportReport,
    registerCallbacks,
    settingsCancel,
    settingsCheckMedia,
    settingsResetDefaults,
    settingsSave,
  } from "$lib/bridge.js";
  import { configureI18n, t } from "$lib/i18n.js";
  import { logger } from "$lib/logger.js";
  import type { ErrorDisplayValue } from "$lib/user-facing-error.js";
  import {
    AQE_FRONTEND_UNEXPECTED,
    frontendUserError,
    isUserFacingError,
    messageFromUnknownError,
  } from "$lib/user-facing-error.js";
  import type {
    AsyncDonePayload,
    AsyncProgressPayload,
    HealthReport,
    RuntimeStatus,
    SaveErrorPayload,
  } from "$lib/types.js";
  import DiagnosticsPanel from "./DiagnosticsPanel.svelte";
  import GeneralSettingsPanel from "./GeneralSettingsPanel.svelte";
  import SettingsFooter from "./SettingsFooter.svelte";
  import {
    cloneConfig,
    initialSettingsState,
    saveConfigPayload,
    type SettingsTab,
  } from "./settings-state.js";

  const initialState = initialSettingsState();
  configureI18n(initialState.locale, initialState.direction, initialState.messages);

  let config = $state(cloneConfig(initialState.config));
  let activeTab = $state<SettingsTab>("general");
  let saveError = $state<ErrorDisplayValue>("");
  let healthMessage = $state<ErrorDisplayValue>(t("settings.health.not_run"));
  let healthReport = $state<HealthReport | null>(null);
  let healthProgress = $state<AsyncProgressPayload | null>(null);
  let diagnosticsMessage = $state<ErrorDisplayValue>("");
  let frontendRuntimeError = $state<ErrorDisplayValue>("");
  let runtimeStatus = $state<RuntimeStatus>(initialState.diagnostics.runtime);

  onMount(() => {
    const showFrontendRuntimeError = () => {
      frontendRuntimeError = frontendUserError(
        AQE_FRONTEND_UNEXPECTED,
        "The interface hit an unexpected error.",
      );
    };
    registerCallbacks({
      onAsyncProgress: (payload: AsyncProgressPayload) => {
        healthProgress = payload;
        handleAsyncProgress(payload);
      },
      onAsyncDone: (payload: AsyncDonePayload) => {
        handleAsyncDone(payload);
      },
      onSaveError: (payload: SaveErrorPayload) => {
        saveError = isUserFacingError(payload.user_error) ? payload.user_error : payload.error;
      },
    });
    window.addEventListener("error", showFrontendRuntimeError);
    window.addEventListener("unhandledrejection", showFrontendRuntimeError);
    logger.info("audio quick editor settings UI mounted", { version: initialState.version });
    void refreshRuntimeStatus();
    return () => {
      window.removeEventListener("error", showFrontendRuntimeError);
      window.removeEventListener("unhandledrejection", showFrontendRuntimeError);
    };
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
      const message = messageFromUnknownError(error);
      healthMessage = isUserFacingError(error) ? error : message;
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
      const message = messageFromUnknownError(error);
      diagnosticsMessage = isUserFacingError(error) ? error : message;
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
      const message = messageFromUnknownError(error);
      diagnosticsMessage = isUserFacingError(error) ? error : message;
      logger.error("show log file failed", { message });
    }
  }

  async function refreshRuntimeStatus(): Promise<void> {
    try {
      runtimeStatus = await startAsyncOp("runtime_status", {});
    } catch (error) {
      const message = messageFromUnknownError(error);
      diagnosticsMessage = isUserFacingError(error) ? error : message;
      logger.error("runtime status failed", { message });
    }
  }

  async function installRuntime(): Promise<void> {
    diagnosticsMessage = t("settings.runtime.installing");
    healthProgress = null;
    try {
      runtimeStatus = await startAsyncOp("runtime_install", {});
      diagnosticsMessage = runtimeStatus.error || runtimeStatus.message || t("settings.async.done");
    } catch (error) {
      const message = messageFromUnknownError(error);
      diagnosticsMessage = isUserFacingError(error) ? error : message;
      logger.error("runtime install failed", { message });
    }
  }

  function saveConfig(): void {
    settingsSave(saveConfigPayload(config));
  }
</script>

<AqeTooltipProvider>
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

    {#if frontendRuntimeError}
      <p class="settings-error" data-testid="frontend-runtime-error">
        <ErrorMessage error={frontendRuntimeError} />
      </p>
    {/if}

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
          bind:config
          initialState={initialState}
          healthMessage={healthMessage}
          healthReport={healthReport}
          healthProgress={healthProgress}
          runtimeStatus={runtimeStatus}
          diagnosticsMessage={diagnosticsMessage}
          onRunHealthCheck={runHealthCheck}
          onInstallRuntime={installRuntime}
          onCheckMedia={settingsCheckMedia}
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
</AqeTooltipProvider>
