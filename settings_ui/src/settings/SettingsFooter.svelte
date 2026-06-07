<script lang="ts">
  import { t } from "$lib/i18n.js";

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

<footer class="footer-shell">
  <div class="footer">
    <button type="button" class="settings-button" data-testid="settings-reset-defaults" onclick={onResetDefaults}>
      {t("settings.footer.reset_defaults")}
    </button>
    <div class="footer-actions">
      <button type="button" class="settings-button" data-testid="settings-cancel" onclick={onCancel}>
        {t("settings.footer.cancel")}
      </button>
      <button type="button" class="settings-button settings-button-primary" data-testid="settings-save" onclick={onSave}>
        {t("settings.footer.save")}
      </button>
    </div>
  </div>
</footer>

<style>
  .footer-shell {
    background: var(--canvas, Canvas);
    bottom: 0;
    margin: 20px 0 0;
    padding: 0 12px;
    position: sticky;
    z-index: 10;
  }

  .footer {
    align-items: center;
    background: var(--canvas, Canvas);
    border-top: 1px solid color-mix(in srgb, var(--border, currentColor) 78%, transparent);
    box-sizing: border-box;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    justify-content: space-between;
    margin: 0 auto;
    max-width: 920px;
    padding: 14px 0 0;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  .footer :global(.settings-button) {
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

  .footer :global(.settings-button:hover) {
    text-decoration: underline;
  }

  .footer :global(.settings-button:focus) {
    border-color: var(--aqe-accent-border);
    outline: 2px solid var(--aqe-accent-focus);
    outline-offset: 2px;
  }

  .footer :global(.settings-button-primary) {
    background: var(--aqe-accent-bg);
    border-color: var(--aqe-accent-border);
    box-shadow: inset 0 0 0 1px var(--aqe-accent-border);
    color: var(--aqe-accent-text);
    font-weight: 700;
  }

  @media (max-width: 720px) {
    .footer-shell {
      padding-inline: 0;
    }

    .footer {
      flex-direction: column;
      padding-top: 12px;
    }

    .footer-actions {
      width: 100%;
    }

    .footer-actions :global(.settings-button),
    .footer > :global(.settings-button) {
      flex: 1;
    }
  }
</style>
