<script lang="ts">
  import FieldTooltipTarget from "$lib/FieldTooltipTarget.svelte";
  import { t } from "$lib/i18n.js";

  interface Props {
    running: boolean;
    finished: boolean;
    onStart: () => void;
    onClose: () => void;
    onCopyLog: () => void;
    canStart: boolean;
    startDisabledReason: string | undefined;
    startLabel?: string;
  }

  let {
    running,
    finished,
    onStart,
    onClose,
    onCopyLog,
    canStart,
    startDisabledReason,
    startLabel = t("batch.start"),
  }: Props = $props();
</script>

<footer class="footer">
  <button type="button" class="batch-button" onclick={onCopyLog}>
    {t("batch.copy_log")}
  </button>
  <div class="footer-actions">
    {#if finished}
      <button type="button" class="batch-button" onclick={onClose}>
        {t("batch.close")}
      </button>
    {/if}
    <FieldTooltipTarget content={startLabel} disabledReason={startDisabledReason}>
      <button
        type="button"
        class="batch-button batch-button-primary"
        data-testid="batch-start"
        data-aqe-tooltip-content={startDisabledReason || startLabel}
        onclick={onStart}
        disabled={!canStart || running || finished}
      >
        {startLabel}
      </button>
    </FieldTooltipTarget>
  </div>
</footer>

<style>
  .footer {
    align-items: center;
    border-top: 1px solid color-mix(in srgb, var(--border, currentColor) 78%, transparent);
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: space-between;
    padding-top: 12px;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  .batch-button {
    appearance: none;
    background: transparent;
    border: 1px solid;
    border-color: ButtonBorder;
    border-radius: 7px;
    color: inherit;
    cursor: pointer;
    font: inherit;
    font-size: 11px;
    font-weight: 400;
    line-height: 1.2;
    min-height: 24px;
    padding: 2px 6px;
  }

  .batch-button:disabled {
    cursor: default;
    opacity: 0.55;
  }

  .batch-button-primary {
    background: var(--aqe-accent-bg);
    border-color: var(--aqe-accent-border);
    box-shadow: inset 0 0 0 1px var(--aqe-accent-border);
    color: var(--aqe-accent-text);
    font-weight: 700;
  }

  .batch-button-primary:disabled {
    background: ButtonFace;
    border-color: ButtonBorder;
    box-shadow: none;
    color: GrayText;
    font-weight: 400;
    opacity: 1;
  }

</style>
