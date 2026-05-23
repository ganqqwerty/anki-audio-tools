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
    backdrop-filter: blur(10px);
    background: color-mix(in srgb, var(--canvas-elevated, Canvas) 92%, transparent);
    border: 1px solid color-mix(in srgb, var(--border, currentColor) 78%, transparent);
    border-radius: 20px;
    bottom: 16px;
    box-shadow: 0 12px 32px color-mix(in srgb, black 10%, transparent);
    display: flex;
    gap: 16px;
    justify-content: space-between;
    margin: 20px auto 0;
    max-width: 920px;
    padding: 16px 18px;
    position: sticky;
    z-index: 10;
  }

  .footer-actions {
    display: flex;
    gap: 10px;
  }

  @media (max-width: 720px) {
    .footer {
      bottom: 12px;
      flex-direction: column;
      padding: 14px;
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
