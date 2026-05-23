<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
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
          <span class="aqe-help-description">{t("editor.help.play_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="chart-line" /><span>{t("editor.command.graph.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.graph_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="folder-open" /><span>{t("editor.command.folder.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.folder_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="share" /><span>{t("editor.command.share.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.share_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="file-audio" /><span>{t("editor.command.convert.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.convert_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="timer-reset" /><span>{t("editor.command.shorten_pauses.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.shorten_pauses_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="waves" /><span>{t("editor.command.pitch_hum.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.pitch_hum_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="sparkles" /><span>{t("editor.command.denoise.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.denoise_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="snail" /><span>{t("editor.command.slower.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.slower_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="hare-running" /><span>{t("editor.command.faster.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.faster_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="volume-1" /><span>{t("editor.command.volume_down.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.volume_down_desc")}</span>
        </span>
        <span class="aqe-help-item">
          <span class="aqe-help-command"><EditorCommandIcon icon="volume-2" /><span>{t("editor.command.volume_up.label")}</span></span>
          <span class="aqe-help-description">{t("editor.help.volume_up_desc")}</span>
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
    <p class="aqe-help-note">{t("editor.help.note")}</p>
  </div>
</details>
