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

<footer>
  <button type="button" class="secondary" onclick={onCopyLog}>
    {t("batch.copy_log")}
  </button>
  {#if finished}
    <button type="button" class="secondary" onclick={onClose}>
      {t("batch.close")}
    </button>
  {:else}
    <button type="button" class="secondary" onclick={onCancel} disabled={!running}>
      {t("batch.cancel")}
    </button>
  {/if}
  <button
    type="button"
    class="primary"
    data-testid="batch-start"
    onclick={onStart}
    disabled={!canStart || running || finished}
  >
    {t("batch.start")}
  </button>
</footer>

<style>
  footer {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: flex-end;
  }

  button {
    appearance: none;
    border: 1px solid var(--border, ButtonBorder);
    border-radius: 6px;
    cursor: pointer;
    font: inherit;
    min-height: 36px;
    padding: 7px 14px;
  }

  button:disabled {
    cursor: default;
    opacity: 0.55;
  }

  .primary {
    background: var(--button-primary-bg, Highlight);
    color: var(--button-primary-fg, HighlightText);
    font-weight: 700;
  }

  .secondary {
    background: var(--button-bg, ButtonFace);
    color: var(--fg, ButtonText);
  }
</style>
