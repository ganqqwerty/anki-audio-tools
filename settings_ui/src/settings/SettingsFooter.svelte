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

<footer class="footer">
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
</footer>

<style>
  .footer {
    align-items: center;
    background: var(--canvas, Canvas);
    border-top: 1px solid color-mix(in srgb, var(--border, currentColor) 78%, transparent);
    display: flex;
    gap: 16px;
    justify-content: space-between;
    margin: 20px auto 0;
    max-width: 920px;
    padding: 14px 0 0;
    bottom: 0;
    position: sticky;
    z-index: 10;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  @media (max-width: 720px) {
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
