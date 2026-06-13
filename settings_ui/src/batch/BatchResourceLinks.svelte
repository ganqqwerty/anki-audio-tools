<script lang="ts">
  import { t } from "$lib/i18n.js";
  import { PRODUCT_LINKS } from "$lib/product-links.js";
  import ProductLinkIcon from "$lib/ProductLinkIcon.svelte";
</script>

<nav class="resource-links" aria-label={t("batch.links.label")}>
  <a href={PRODUCT_LINKS.githubPages} target="_blank" rel="noopener noreferrer">
    <ProductLinkIcon className="resource-link-icon" icon="external-link" />
    <span>{t("links.github_pages")}</span>
  </a>
  <a href={PRODUCT_LINKS.editorVideos.batchProcessing} target="_blank" rel="noopener noreferrer">
    <ProductLinkIcon className="resource-link-icon" icon="external-link" />
    <span>{t("links.see_video")}</span>
  </a>
  <a href={PRODUCT_LINKS.bugReport} target="_blank" rel="noopener noreferrer">
    <ProductLinkIcon className="resource-link-icon" icon="bug" />
    <span>{t("links.report_bug")}</span>
  </a>
  <a href={PRODUCT_LINKS.ideaRequest} target="_blank" rel="noopener noreferrer">
    <ProductLinkIcon className="resource-link-icon" icon="idea" />
    <span>{t("links.request_idea")}</span>
  </a>
</nav>

<style>
  .resource-links {
    display: flex;
    flex-wrap: wrap;
    font-size: 11px;
    gap: 8px 12px;
  }

  .resource-links a {
    align-items: center;
    border: 1px solid ButtonBorder;
    border-radius: 7px;
    color: inherit;
    display: inline-flex;
    gap: 5px;
    min-height: 24px;
    padding: 2px 6px;
    text-decoration: none;
  }

  :global(.resource-link-icon) {
    display: inline-flex;
    flex: 0 0 auto;
  }
</style>
