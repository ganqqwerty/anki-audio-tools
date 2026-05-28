<script lang="ts">
  import AqeTooltip from "$lib/AqeTooltip.svelte";
  import { t } from "$lib/i18n.js";
  import { PRODUCT_LINKS } from "$lib/product-links.js";
  import ProductLinkIcon from "$lib/ProductLinkIcon.svelte";

  const telegramTooltip = $derived(`${t("links.telegram")}\n${t("links.telegram_detail")}`);
</script>

<aside class="diagnostics-links" aria-label={t("diagnostics.links.title")}>
  <h2>{t("diagnostics.links.title")}</h2>
  <div class="diagnostics-link-groups">
    <div class="diagnostics-link-row" aria-label={t("links.resources")}>
      <a class="diagnostics-link" href={PRODUCT_LINKS.githubPages} target="_blank" rel="noopener noreferrer">
        <span>{t("links.website")}</span>
      </a>
      <AqeTooltip content={t("links.discord")}>
        {#snippet trigger({ props })}
          <a
            {...props}
            aria-label={t("links.discord")}
            class="diagnostics-link diagnostics-icon-link"
            href={PRODUCT_LINKS.discord}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ProductLinkIcon className="diagnostics-link-icon" icon="discord" size={16} />
          </a>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip content={t("links.patreon")}>
        {#snippet trigger({ props })}
          <a
            {...props}
            aria-label={t("links.patreon")}
            class="diagnostics-link diagnostics-icon-link"
            href={PRODUCT_LINKS.patreon}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ProductLinkIcon className="diagnostics-link-icon" icon="patreon" size={16} />
          </a>
        {/snippet}
      </AqeTooltip>
      <AqeTooltip content={telegramTooltip}>
        {#snippet trigger({ props })}
          <a
            {...props}
            aria-label={t("links.telegram")}
            class="diagnostics-link diagnostics-icon-link"
            href={PRODUCT_LINKS.telegram}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ProductLinkIcon className="diagnostics-link-icon" icon="send" size={16} />
          </a>
        {/snippet}
      </AqeTooltip>
    </div>
    <div class="diagnostics-link-row">
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
  <p class="diagnostics-credit">{t("diagnostics.links.created_by")}</p>
  <p class="diagnostics-credit">{t("diagnostics.links.alpha_testers")}</p>
</aside>

<style>
  .diagnostics-links {
    display: grid;
    gap: 8px;
    justify-items: end;
    max-width: 420px;
    text-align: right;
  }

  h2 {
    font-size: 0.82rem;
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
    justify-content: flex-end;
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

  .diagnostics-icon-link {
    flex-wrap: nowrap;
    justify-content: center;
    padding: 4px;
    width: 27px;
  }

  :global(.diagnostics-link-icon) {
    display: inline-flex;
    flex: 0 0 auto;
  }

  .diagnostics-link:hover {
    text-decoration: underline;
  }

  .diagnostics-credit {
    color: var(--fg-subtle, currentColor);
    line-height: 1.35;
    margin: 0;
  }

  @media (max-width: 720px) {
    .diagnostics-links {
      justify-items: start;
      max-width: none;
      text-align: left;
    }

    .diagnostics-link-row {
      justify-content: flex-start;
    }
  }
</style>
