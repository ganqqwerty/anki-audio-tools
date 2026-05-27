<script lang="ts">
  import { t } from "$lib/i18n.js";

  interface Props {
    running: boolean;
    finished: boolean;
    onStart: () => void;
    onCancel: () => void;
    onClose: () => void;
    onCopyLog: () => void;
    canStart: boolean;
  }

  let { running, finished, onStart, onCancel, onClose, onCopyLog, canStart }: Props = $props();
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
    {:else}
      <button type="button" class="batch-button" onclick={onCancel} disabled={!running}>
        {t("batch.cancel")}
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
    font-size: 12px;
    font-weight: 400;
    min-height: 27px;
    padding: 4px 8px;
  }

  .batch-button:disabled {
    cursor: default;
    opacity: 0.55;
  }

  .batch-button-primary {
    box-shadow: inset 0 0 0 1px ButtonBorder;
    font-weight: 700;
  }

  @media (max-width: 720px) {
    .footer {
      align-items: stretch;
      flex-direction: column;
      gap: 10px;
    }

    .footer-actions {
      width: 100%;
    }

    .footer-actions .batch-button,
    .footer > .batch-button {
      flex: 1;
    }
  }
</style>
