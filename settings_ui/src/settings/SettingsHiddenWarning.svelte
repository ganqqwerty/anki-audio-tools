<script lang="ts">
  import { t } from "$lib/i18n.js";
  import settingsHiddenWarningImage from "./assets/settings-hidden-warning.jpg?inline";

  let expanded = $state(false);
</script>

<aside class="settings-hidden-warning" role="alert" data-testid="settings-hidden-warning">
  <div class="settings-hidden-warning-copy">
    <strong>{t("settings.toolbar_visibility.hidden_settings_warning_title")}</strong>
    <p>{t("settings.toolbar_visibility.hidden_settings_warning_body")}</p>
  </div>
  <button
    class="settings-hidden-warning-thumbnail"
    data-testid="settings-hidden-warning-thumbnail"
    type="button"
    aria-expanded={expanded}
    aria-label={expanded
      ? t("settings.toolbar_visibility.hidden_settings_warning_image_collapse")
      : t("settings.toolbar_visibility.hidden_settings_warning_image_expand")}
    onclick={() => (expanded = !expanded)}
  >
    <img
      data-testid="settings-hidden-warning-thumbnail-image"
      src={settingsHiddenWarningImage}
      alt={t("settings.toolbar_visibility.hidden_settings_warning_image_alt")}
    />
  </button>
  {#if expanded}
    <img
      class="settings-hidden-warning-expanded"
      data-testid="settings-hidden-warning-expanded-image"
      src={settingsHiddenWarningImage}
      alt={t("settings.toolbar_visibility.hidden_settings_warning_image_alt")}
    />
  {/if}
</aside>

<style>
  .settings-hidden-warning {
    align-items: center;
    background: color-mix(in srgb, #f59e0b 10%, var(--canvas, Canvas));
    border: 1px solid color-mix(in srgb, #d97706 38%, var(--border, ButtonBorder));
    border-left: 4px solid #d97706;
    border-radius: 7px;
    display: grid;
    gap: 12px;
    grid-template-columns: minmax(0, 1fr) 96px;
    padding: 10px 12px;
  }

  .settings-hidden-warning-copy {
    display: grid;
    gap: 4px;
    min-width: 0;
  }

  .settings-hidden-warning strong {
    font-size: 0.9rem;
  }

  .settings-hidden-warning-thumbnail {
    appearance: none;
    background: transparent;
    border: 0;
    border-radius: 6px;
    cursor: pointer;
    display: block;
    justify-self: end;
    line-height: 0;
    padding: 0;
  }

  .settings-hidden-warning-thumbnail:focus {
    outline: 2px solid color-mix(in srgb, #d97706 45%, transparent);
    outline-offset: 2px;
  }

  .settings-hidden-warning-thumbnail img {
    aspect-ratio: 801 / 530;
    border: 1px solid color-mix(in srgb, var(--border, ButtonBorder) 80%, transparent);
    border-radius: 6px;
    display: block;
    object-fit: cover;
    width: 96px;
  }

  .settings-hidden-warning-expanded {
    border: 1px solid color-mix(in srgb, var(--border, ButtonBorder) 80%, transparent);
    border-radius: 6px;
    display: block;
    grid-column: 1 / -1;
    max-width: min(100%, 520px);
    width: 100%;
  }

  @media (max-width: 560px) {
    .settings-hidden-warning {
      grid-template-columns: 1fr;
    }

    .settings-hidden-warning-thumbnail {
      justify-self: start;
    }

    .settings-hidden-warning-thumbnail img {
      width: min(160px, 100%);
    }
  }
</style>
