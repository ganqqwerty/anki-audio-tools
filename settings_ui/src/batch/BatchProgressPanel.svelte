<script lang="ts">
  import { t } from "$lib/i18n.js";

  interface Props {
    isAudioExportSurface: boolean;
    running: boolean;
    processed: number;
    total: number;
    failures: number;
    onCancel: () => void;
  }

  let {
    isAudioExportSurface,
    running,
    processed,
    total,
    failures,
    onCancel,
  }: Props = $props();
</script>

<section class="progress-panel" aria-live="polite">
  <div class="progress-meta">
    <span>{processed}/{total}</span>
    <span
      class="progress-status"
      data-testid="batch-progress-status"
      data-failures={failures}
    >
      {isAudioExportSurface
        ? t("audio_export.progress", { processed, total, audio: t("audio_export.no_audio"), failures })
        : t("batch.progress", { processed, total, audio: t("batch.no_audio"), failures })}
    </span>
    {#if running}
      <button
        type="button"
        class="progress-cancel"
        data-testid="batch-cancel"
        onclick={onCancel}
      >
        {isAudioExportSurface ? t("audio_export.cancel") : t("batch.cancel")}
      </button>
    {/if}
  </div>
  <progress max={Math.max(total, 1)} value={processed} aria-valuenow={processed}></progress>
</section>

<style>
  .progress-panel {
    display: grid;
    gap: 8px;
  }

  .progress-meta {
    align-items: center;
    color: var(--fg-subtle, currentColor);
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
</style>
