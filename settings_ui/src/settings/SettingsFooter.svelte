<script lang="ts">
  type FooterAction = () => void;

  let {
    onResetDefaults,
    onCancel,
    onSave,
  }: {
    onCancel: FooterAction;
    onResetDefaults: FooterAction;
    onSave: FooterAction;
  } = $props();
</script>

<footer class="footer">
  <button type="button" class="btn btn-secondary" data-testid="settings-reset-defaults" onclick={onResetDefaults}>
    Reset Defaults
  </button>
  <div class="footer-actions">
    <button type="button" class="btn btn-secondary" data-testid="settings-cancel" onclick={onCancel}>
      Cancel
    </button>
    <button type="button" class="btn btn-primary" data-testid="settings-save" onclick={onSave}>
      Save
    </button>
  </div>
</footer>

<style>
  .footer {
    display: flex;
    gap: 16px;
    justify-content: space-between;
    margin: 18px auto 0;
    max-width: 920px;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  .btn {
    appearance: none;
    background: var(--button-bg, transparent);
    border: 1px solid var(--border-subtle, currentColor);
    border-radius: 999px;
    color: var(--fg, currentColor);
    cursor: pointer;
    font: inherit;
    padding: 10px 16px;
  }

  .btn:hover {
    background: var(--button-gradient-start, var(--button-bg, transparent));
    border-color: var(--button-hover-border, var(--border, currentColor));
  }

  .btn-primary {
    border-color: var(--border-focus, var(--border, currentColor));
    font-weight: 700;
  }

  @media (max-width: 720px) {
    .footer {
      flex-direction: column;
    }

    .footer-actions {
      width: 100%;
    }

    .footer-actions .btn,
    .footer > .btn {
      flex: 1;
    }
  }
</style>
