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
    frontendUserError,
    isUserFacingError,
  } from "$lib/user-facing-error.js";
  import type { BatchErrorPayload, BatchFinishPayload, BatchProgressPayload } from "$lib/types.js";
  import BatchControls from "./BatchControls.svelte";
  import BatchFooter from "./BatchFooter.svelte";
  import { batchCancel, batchClose, batchCopyLog, batchStart, registerBatchCallbacks } from "./bridge.js";
  import {
    batchStartRequest,
    canStartBatch,
    initialBatchState,
    initialFormState,
    selectedOperation,
  } from "./batch-state.js";

  const batchState = initialBatchState();
  configureI18n(batchState.locale, batchState.direction, batchState.messages);
  const logger = createLogger("batch", (payload) => {
    sendBridgeEnvelope("frontend.log", payload);
  });

  let form = $state(initialFormState(batchState));
  let running = $state(false);
  let finished = $state(false);
  let status = $state<ErrorDisplayValue>(t("batch.instructions"));
  let frontendRuntimeError = $state<ErrorDisplayValue>("");
  let processed = $state(0);
  let total = $state(batchState.note_count);
  let failures = $state(0);
  let logLines = $state<string[]>([]);

  let selected = $derived(selectedOperation(batchState, form.operation));
  let canStart = $derived(canStartBatch(form, selected));

  onMount(() => {
    const showFrontendRuntimeError = () => {
      frontendRuntimeError = frontendUserError(
        AQE_FRONTEND_UNEXPECTED,
        "The interface hit an unexpected error.",
      );
    };
    registerBatchCallbacks({
      onProgress: (payload: BatchProgressPayload) => {
        processed = payload.processed;
        total = payload.total;
        failures = payload.failures;
        status = payload.message;
      },
      onLog: (payload) => {
        logLines = [...logLines, payload.line];
      },
      onFinish: (payload: BatchFinishPayload) => {
        running = false;
        finished = true;
        processed = payload.processed;
        total = payload.total;
        failures = payload.failures;
        status = payload.summary;
      },
      onError: (payload: BatchErrorPayload) => {
        running = false;
        finished = payload.recoverable !== true;
        status = isUserFacingError(payload.user_error) ? payload.user_error : payload.message;
      },
    });
    window.addEventListener("error", showFrontendRuntimeError);
    window.addEventListener("unhandledrejection", showFrontendRuntimeError);
    logger.info("batch UI mounted", { noteCount: batchState.note_count });
    return () => {
      window.removeEventListener("error", showFrontendRuntimeError);
      window.removeEventListener("unhandledrejection", showFrontendRuntimeError);
    };
  });

  function start(): void {
    if (!canStart) return;
    running = true;
    finished = false;
    processed = 0;
    total = batchState.note_count;
    failures = 0;
    logLines = [];
    status = t("batch.starting", { operation: selected?.label ?? form.operation });
    batchStart(batchStartRequest(form, selected));
  }

  function cancel(): void {
    status = t("batch.cancel_requested");
    batchCancel();
  }
</script>

<AqeTooltipProvider>
  <main class="batch-root" dir={batchState.direction} lang={batchState.locale}>
    <header>
      <h1>{t("batch.window_title")}</h1>
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

    <BatchControls state={batchState} bind:form selected={selected} disabled={running} />

    <section class="progress-panel" aria-live="polite">
      <div class="progress-meta">
        <span>{processed}/{total}</span>
        <span class="progress-status">{t("batch.progress", { processed, total, audio: t("batch.no_audio"), failures })}</span>
        {#if running}
          <button type="button" class="progress-cancel" onclick={cancel}>
            {t("batch.cancel")}
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
      onClose={batchClose}
      onCopyLog={batchCopyLog}
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

  .resource-links a:hover {
    text-decoration: underline;
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
