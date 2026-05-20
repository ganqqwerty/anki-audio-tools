<script lang="ts">
  import { onMount } from "svelte";
  import { sendBridgeEnvelope } from "$lib/bridge.js";
  import { configureI18n, t } from "$lib/i18n.js";
  import { createLogger } from "$lib/logger.js";
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
  let status = $state(t("batch.instructions"));
  let processed = $state(0);
  let total = $state(batchState.note_count);
  let failures = $state(0);
  let logLines = $state<string[]>([]);

  let selected = $derived(selectedOperation(batchState, form.operation));
  let canStart = $derived(canStartBatch(form, selected));

  onMount(() => {
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
        status = payload.message;
      },
    });
    logger.info("batch UI mounted", { noteCount: batchState.note_count });
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

<main class="batch-root" dir={batchState.direction} lang={batchState.locale}>
  <header>
    <h1>{t("batch.window_title")}</h1>
    <p>{status}</p>
  </header>

  <BatchControls state={batchState} bind:form selected={selected} disabled={running} />

  <section class="progress-panel" aria-live="polite">
    <div class="progress-meta">
      <span>{processed}/{total}</span>
      <span>{t("batch.progress", { processed, total, audio: t("batch.no_audio"), failures })}</span>
    </div>
    <progress max={Math.max(total, 1)} value={processed} aria-valuenow={processed}></progress>
  </section>

  <pre aria-label="Batch log">{logLines.join("\n")}</pre>

  <BatchFooter
    running={running}
    finished={finished}
    onStart={start}
    onCancel={cancel}
    onClose={batchClose}
    onCopyLog={batchCopyLog}
    canStart={canStart}
  />
</main>

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
    font-size: 1.4rem;
    line-height: 1.2;
  }

  p,
  .progress-meta {
    color: var(--fg-subtle, currentColor);
  }

  .progress-panel {
    display: grid;
    gap: 8px;
  }

  .progress-meta {
    display: flex;
    flex-wrap: wrap;
    font-size: 0.9rem;
    gap: 10px;
    justify-content: space-between;
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
