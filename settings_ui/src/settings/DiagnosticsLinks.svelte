<script lang="ts">
  import { t } from "$lib/i18n.js";
  import { PRODUCT_LINKS } from "$lib/product-links.js";
  import ProductLinkIcon from "$lib/ProductLinkIcon.svelte";
</script>

<section class="settings-section">
  <div class="settings-section-header">
    <h3>{t("diagnostics.links.title")}</h3>
    <p>{t("diagnostics.links.summary")}</p>
  </div>
  <div class="diagnostics-link-groups">
    <div class="diagnostics-link-row" aria-label={t("links.resources")}>
      <a class="diagnostics-link" href={PRODUCT_LINKS.githubPages} target="_blank" rel="noopener noreferrer">
        <ProductLinkIcon className="diagnostics-link-icon" icon="external-link" />
        <span>{t("links.github_pages")}</span>
      </a>
      <a class="diagnostics-link" href={PRODUCT_LINKS.discord} target="_blank" rel="noopener noreferrer">
        <ProductLinkIcon className="diagnostics-link-icon" icon="message" />
        <span>{t("links.discord")}</span>
      </a>
      <a class="diagnostics-link" href={PRODUCT_LINKS.patreon} target="_blank" rel="noopener noreferrer">
        <ProductLinkIcon className="diagnostics-link-icon" icon="heart" />
        <span>{t("links.patreon")}</span>
      </a>
    </div>
    <div class="diagnostics-link-row">
      <span class="diagnostics-link-stack">
        <a class="diagnostics-link" href={PRODUCT_LINKS.telegram} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="diagnostics-link-icon" icon="send" />
          <span>{t("links.telegram")}</span>
        </a>
        <span class="diagnostics-link-detail">{t("links.telegram_detail")}</span>
      </span>
      <a class="diagnostics-link" href={PRODUCT_LINKS.bugReport} target="_blank" rel="noopener noreferrer">
        <ProductLinkIcon className="diagnostics-link-icon" icon="bug" />
        <span>{t("links.report_bug")}</span>
      </a>
      <a class="diagnostics-link" href={PRODUCT_LINKS.ideaRequest} target="_blank" rel="noopener noreferrer">
        <ProductLinkIcon className="diagnostics-link-icon" icon="idea" />
        <span>{t("links.request_idea")}</span>
      </a>
    </div>
  </div>
</section>

<style>
  h3 {
    margin: 0;
  }

  .diagnostics-link-groups {
    display: grid;
    gap: 8px;
  }

  .diagnostics-link-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .diagnostics-link {
    align-items: center;
    border: 1px solid ButtonBorder;
    border-radius: 7px;
    color: inherit;
    display: inline-flex;
    flex-wrap: wrap;
    gap: 6px;
    min-height: 27px;
    padding: 4px 8px;
    text-decoration: none;
  }

  :global(.diagnostics-link-icon) {
    display: inline-flex;
    flex: 0 0 auto;
  }

  .diagnostics-link-stack {
    align-items: flex-start;
    display: inline-flex;
    flex-direction: column;
    gap: 3px;
  }

  .diagnostics-link:hover {
    text-decoration: underline;
  }

  .diagnostics-link-detail {
    color: var(--fg-subtle, currentColor);
    font-size: 11px;
  }
</style>
