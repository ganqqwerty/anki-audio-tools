<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import ProductLinkIcon from "../lib/ProductLinkIcon.svelte";
  import { openEditorExternalLink } from "./external-links.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";

  const { ord }: { ord: number } = $props();
</script>

<details class="aqe-help" data-testid={`aqe-help-${ord}`}>
  <AqeTooltip>
    {#snippet trigger({ props })}
      <summary
        {...props}
        class="aqe-help-summary aqe-tooltip-target"
        data-aqe-tooltip-content={t("editor.help.title")}
      >
        <span class="aqe-help-triangle" aria-hidden="true"></span>
        <EditorCommandIcon icon="circle-help" />
        <span>{t("editor.help.summary")}</span>
      </summary>
    {/snippet}
  </AqeTooltip>
  <div class="aqe-help-body">
    <section class="aqe-help-section">
      <h4 class="aqe-help-title">{t("editor.help.graph_regions")}</h4>
      <ul class="aqe-help-list">
        <li>{t("editor.help.shift_drag")}</li>
        <li>{t("editor.help.play_repeat")}</li>
        <li>{t("editor.help.delete_region_or_rest")}</li>
        <li>{t("editor.help.pitch_loudness")}</li>
      </ul>
    </section>
    <section class="aqe-help-section">
      <h4 class="aqe-help-title">{t("editor.help.buttons")}</h4>
      <div class="aqe-help-grid">
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="play" /><span>{t("editor.command.play.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.play_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.playback} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.playback)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="chart-line" /><span>{t("editor.command.graph.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.graph_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.graph} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.graph)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="folder-open" /><span>{t("editor.command.folder.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.folder_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="share" /><span>{t("editor.command.share.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.share_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.share} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.share)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="file-audio" /><span>{t("editor.command.convert.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.convert_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.convert} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.convert)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="timer-reset" /><span>{t("editor.command.shorten_pauses.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.shorten_pauses_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.pauseShortening} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.pauseShortening)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="waves" /><span>{t("editor.command.pitch_hum.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.pitch_hum_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.pitchHum} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.pitchHum)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="sparkles" /><span>{t("editor.command.denoise.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.denoise_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.denoise} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.denoise)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="snail" /><span>{t("editor.command.slower.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.slower_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.speed} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.speed)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="hare-running" /><span>{t("editor.command.faster.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.faster_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.speed} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.speed)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="volume-1" /><span>{t("editor.command.volume_down.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.volume_down_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.volume} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.volume)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="volume-2" /><span>{t("editor.command.volume_up.label")}</span></span>
          <span class="aqe-help-description">
            {t("editor.help.volume_up_desc")}
            <a class="aqe-help-text-link" href={PRODUCT_LINKS.editorVideos.volume} onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.volume)} rel="noopener noreferrer" target="_blank">{t("links.see_video")}</a>
          </span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="undo-2" /><span>{t("editor.command.undo.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.undo_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="redo-2" /><span>{t("editor.command.redo.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.redo_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="trash-2" /><span>{t("editor.help.delete_region_or_rest_command")}</span></span>
          <span class="aqe-help-description">{t("editor.help.delete_region_or_rest_desc")}</span>
        </span>
      </div>
    </section>
    <section class="aqe-help-section">
      <h4 class="aqe-help-title">{t("links.resources")}</h4>
      <div class="aqe-help-link-row">
        <a
          class="aqe-help-link"
          href={PRODUCT_LINKS.githubPages}
          onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.githubPages)}
          rel="noopener noreferrer"
          target="_blank"
        >
          <ProductLinkIcon className="aqe-help-link-icon" icon="external-link" />
          <span>{t("links.github_pages")}</span>
        </a>
        <a
          class="aqe-help-link"
          href={PRODUCT_LINKS.bugReport}
          onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.bugReport)}
          rel="noopener noreferrer"
          target="_blank"
        >
          <ProductLinkIcon className="aqe-help-link-icon" icon="bug" />
          <span>{t("links.report_bug")}</span>
        </a>
        <a
          class="aqe-help-link"
          href={PRODUCT_LINKS.ideaRequest}
          onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.ideaRequest)}
          rel="noopener noreferrer"
          target="_blank"
        >
          <ProductLinkIcon className="aqe-help-link-icon" icon="idea" />
          <span>{t("links.request_idea")}</span>
        </a>
      </div>
    </section>
    <p class="aqe-help-note">{t("editor.help.note")}</p>
  </div>
</details>
