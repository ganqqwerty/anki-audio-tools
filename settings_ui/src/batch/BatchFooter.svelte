<script lang="ts">
  import { t } from "$lib/i18n.js";

  interface Props {
    running: boolean;
    finished: boolean;
    onStart: () => void;
    onClose: () => void;
    onCopyLog: () => void;
    canStart: boolean;
  }

  let { running, finished, onStart, onClose, onCopyLog, canStart }: Props = $props();
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
    <button
      type="button"
      class="batch-button batch-button-primary"
      data-testid="batch-start"
      onclick={onStart}
      disabled={!canStart || running || finished}
    >
      {t("batch.start")}
    </button>
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
    box-shadow: inset 0 0 0 1px ButtonBorder;
    font-weight: 700;
  }

</style>
