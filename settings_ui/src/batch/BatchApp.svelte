<script lang="ts">
  import { onMount } from "svelte";
  import { sendBridgeEnvelope } from "$lib/bridge.js";
  import { configureI18n, t } from "$lib/i18n.js";
  import { createLogger } from "$lib/logger.js";
  import { PRODUCT_LINKS } from "$lib/product-links.js";
  import AqeTooltipProvider from "$lib/AqeTooltipProvider.svelte";
  import ErrorMessage from "$lib/ErrorMessage.svelte";
  import ProductLinkIcon from "$lib/ProductLinkIcon.svelte";
  import type { ErrorDisplayValue } from "$lib/user-facing-error.js";
  import {
    AQE_FRONTEND_UNEXPECTED,
    frontendUnknownError,
    frontendUserError,
    isUserFacingError,
  } from "$lib/user-facing-error.js";
  import { BatchSurface } from "$lib/types.js";
  import type {
    AudioExportInitialState,
    BatchErrorPayload,
    BatchInitialState,
  } from "$lib/types.js";
  import BatchControls from "./BatchControls.svelte";
  import BatchExportControls from "./BatchExportControls.svelte";
  import BatchFooter from "./BatchFooter.svelte";
  import {
    audioExportCancel,
    audioExportChooseDestination,
    audioExportClose,
    audioExportCopyLog,
    audioExportStart,
    batchCancel,
    batchClose,
    batchCopyLog,
    batchStart,
    registerAudioExportCallbacks,
    registerBatchCallbacks,
  } from "./bridge.js";
  import {
    FALLBACK_BATCH_INITIAL_STATE,
    batchStartRequest,
    canStartBatch,
    initialBatchState,
    initialFormState,
    selectedOperation,
  } from "./batch-state.js";
  import {
    audioExportStartRequest,
    canStartAudioExport,
    initialAudioExportFormState,
  } from "./export-state.js";

  const batchState = initialBatchState();
  const isAudioExportSurface = batchState.surface === BatchSurface.AudioExport;
  const operationState = (isAudioExportSurface ? FALLBACK_BATCH_INITIAL_STATE : batchState) as BatchInitialState;
  const audioExportState = (isAudioExportSurface ? batchState : null) as AudioExportInitialState | null;
  configureI18n(batchState.locale, batchState.direction, batchState.messages);
  const logger = createLogger("batch", (payload) => {
    sendBridgeEnvelope("frontend.log", payload);
  });

  let form = $state(initialFormState(operationState));
  let exportForm = $state(
    audioExportState === null ? null : initialAudioExportFormState(audioExportState),
  );
  let running = $state(false);
  let finished = $state(false);
  let status = $state<ErrorDisplayValue>(
    isAudioExportSurface ? t("audio_export.instructions") : t("batch.instructions"),
  );
  let frontendRuntimeError = $state<ErrorDisplayValue>("");
  let processed = $state(0);
  let total = $state(isAudioExportSurface ? 0 : batchState.note_count);
  let failures = $state(0);
  let logLines = $state<string[]>([]);

  let selected = $derived(selectedOperation(operationState, form.operation));
  let canStart = $derived(
    isAudioExportSurface
      ? exportForm !== null && canStartAudioExport(exportForm)
      : canStartBatch(form, selected),
  );

  onMount(() => {
    const showFrontendRuntimeError = () => {
      frontendRuntimeError = frontendUserError(AQE_FRONTEND_UNEXPECTED, "The interface hit an unexpected error.");
    };
    if (isAudioExportSurface) {
      registerAudioExportCallbacks({
        onDestination: (payload) => {
          if (exportForm !== null) exportForm.destinationPath = payload.destination_path;
        },
        onProgress: updateProgress,
        onLog: appendLog,
        onFinish: updateFinish,
        onError: updateFromBackendError,
      });
    } else {
      registerBatchCallbacks({
        onProgress: updateProgress,
        onLog: appendLog,
        onFinish: updateFinish,
        onError: updateFromBackendError,
      });
    }
    window.addEventListener("error", showFrontendRuntimeError);
    window.addEventListener("unhandledrejection", showFrontendRuntimeError);
    logger.info("batch UI mounted", { noteCount: batchState.note_count });
    return () => {
      window.removeEventListener("error", showFrontendRuntimeError);
      window.removeEventListener("unhandledrejection", showFrontendRuntimeError);
    };
  });

  function updateProgress(payload: { processed: number; total: number; failures: number; message: string }): void {
    processed = payload.processed;
    total = payload.total;
    failures = payload.failures;
    status = payload.message;
  }

  function appendLog(payload: { line: string }): void {
    logLines = [...logLines, payload.line];
  }

  function updateFinish(payload: { processed: number; total: number; failures: number; summary: string }): void {
    running = false;
    finished = true;
    processed = payload.processed;
    total = payload.total;
    failures = payload.failures;
    status = payload.summary;
  }

  function updateFromBackendError(payload: BatchErrorPayload): void {
    running = false;
    finished = payload.recoverable !== true;
    status = isUserFacingError(payload.user_error)
      ? payload.user_error
      : frontendUnknownError(payload.message);
  }

  function start(): void {
    if (!canStart) return;
    running = true;
    finished = false;
    processed = 0;
    total = isAudioExportSurface ? 0 : batchState.note_count;
    failures = 0;
    logLines = [];
    if (isAudioExportSurface) {
      if (exportForm === null) return;
      status = t("audio_export.starting");
      audioExportStart(audioExportStartRequest(exportForm));
      return;
    }
    status = t("batch.starting", { operation: selected?.label ?? form.operation });
    batchStart(batchStartRequest(form, selected));
  }

  function cancel(): void {
    if (isAudioExportSurface) {
      status = t("audio_export.cancel_requested");
      audioExportCancel();
      return;
    }
    status = t("batch.cancel_requested");
    batchCancel();
  }

  function chooseDestination(): void {
    if (exportForm === null) return;
    audioExportChooseDestination({ mode: exportForm.mode });
  }

  function close(): void {
    if (isAudioExportSurface) {
      audioExportClose();
      return;
    }
    batchClose();
  }

  function copyLog(): void {
    if (isAudioExportSurface) {
      audioExportCopyLog();
      return;
    }
    batchCopyLog();
  }
</script>

<AqeTooltipProvider>
  <main class="batch-root" dir={batchState.direction} lang={batchState.locale}>
    <header>
      <h1>{isAudioExportSurface ? t("audio_export.window_title") : t("batch.window_title")}</h1>
      <p><ErrorMessage error={status} /></p>
      <nav class="resource-links" aria-label={t("batch.links.label")}>
        <a href={PRODUCT_LINKS.githubPages} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="resource-link-icon" icon="external-link" />
          <span>{t("links.github_pages")}</span>
        </a>
        <a href={PRODUCT_LINKS.editorVideos.batchProcessing} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="resource-link-icon" icon="external-link" />
          <span>{t("links.see_video")}</span>
        </a>
        <a href={PRODUCT_LINKS.bugReport} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="resource-link-icon" icon="bug" />
          <span>{t("links.report_bug")}</span>
        </a>
        <a href={PRODUCT_LINKS.ideaRequest} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="resource-link-icon" icon="idea" />
          <span>{t("links.request_idea")}</span>
        </a>
      </nav>
    </header>

    {#if frontendRuntimeError}
      <p class="batch-error" data-testid="frontend-runtime-error">
        <ErrorMessage error={frontendRuntimeError} />
      </p>
    {/if}

    {#if isAudioExportSurface && audioExportState !== null && exportForm !== null}
      <BatchExportControls
        state={audioExportState}
        bind:form={exportForm}
        disabled={running}
        onChooseDestination={chooseDestination}
      />
    {:else}
      <BatchControls state={operationState} bind:form selected={selected} disabled={running} />
    {/if}

    <section class="progress-panel" aria-live="polite">
      <div class="progress-meta">
        <span>{processed}/{total}</span>
        <span class="progress-status">
          {isAudioExportSurface
            ? t("audio_export.progress", { processed, total, audio: t("audio_export.no_audio"), failures })
            : t("batch.progress", { processed, total, audio: t("batch.no_audio"), failures })}
        </span>
        {#if running}
          <button type="button" class="progress-cancel" onclick={cancel}>
            {isAudioExportSurface ? t("audio_export.cancel") : t("batch.cancel")}
          </button>
        {/if}
      </div>
      <progress max={Math.max(total, 1)} value={processed} aria-valuenow={processed}></progress>
    </section>

    <pre aria-label="Batch log">{logLines.join("\n")}</pre>

    <BatchFooter
      running={running}
      finished={finished}
      onStart={start}
      onClose={close}
      onCopyLog={copyLog}
      canStart={canStart}
    />
  </main>
</AqeTooltipProvider>

<style>
  :global(body) {
    background: var(--canvas, Canvas);
    color: var(--fg, CanvasText);
    color-scheme: light dark;
    font-family: inherit;
    margin: 0;
  }

  .batch-root {
    background: var(--canvas, Canvas);
    box-sizing: border-box;
    color: var(--fg, CanvasText);
    display: grid;
    gap: 18px;
    font-family: inherit;
    font-size: 12px;
    min-height: 100vh;
    padding: 22px;
  }

  header {
    display: grid;
    gap: 6px;
  }

  h1,
  p {
    margin: 0;
  }

  h1 {
    font-size: 1.8rem;
    line-height: 1.15;
  }

  p,
  .progress-meta {
    color: var(--fg-subtle, currentColor);
  }

  .batch-error {
    color: var(--fg, currentColor);
    margin: 0;
  }

  .resource-links {
    display: flex;
    flex-wrap: wrap;
    font-size: 11px;
    gap: 8px 12px;
  }

  .resource-links a {
    align-items: center;
    border: 1px solid ButtonBorder;
    border-radius: 7px;
    color: inherit;
    display: inline-flex;
    gap: 5px;
    min-height: 24px;
    padding: 2px 6px;
    text-decoration: none;
  }

  :global(.resource-link-icon) {
    display: inline-flex;
    flex: 0 0 auto;
  }

  .progress-panel {
    display: grid;
    gap: 8px;
  }

  .progress-meta {
    align-items: center;
    display: flex;
    flex-wrap: wrap;
    font-size: 11px;
    gap: 10px;
    justify-content: space-between;
  }

  .progress-status {
    flex: 1 1 auto;
    text-align: right;
  }

  .progress-cancel {
    appearance: none;
    background: transparent;
    border: 1px solid ButtonBorder;
    border-radius: 7px;
    color: inherit;
    cursor: pointer;
    font: inherit;
    font-size: 11px;
    line-height: 1.2;
    min-height: 24px;
    padding: 2px 6px;
  }

  .progress-cancel:hover {
    text-decoration: underline;
  }

  progress {
    height: 12px;
    width: 100%;
  }

  pre {
    background: var(--canvas-inset, Canvas);
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    box-sizing: border-box;
    color: var(--fg, CanvasText);
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.86rem;
    margin: 0;
    min-height: 96px;
    overflow: auto;
    padding: 10px;
    white-space: pre-wrap;
  }
</style>
