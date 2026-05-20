<script lang="ts">
  import { onMount } from "svelte";

  import { commandButtons, testId } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import PlaySplitButton from "./PlaySplitButton.svelte";
  import SplitButton from "./SplitButton.svelte";
  import {
    configureAudioClock,
    handleVisualizerPointerDown,
    initializePlaybackRegionState,
    installAudioClockHandlers,
    resetAudioClockState,
    send,
    startSelectionResizeGesture,
  } from "./actions.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { handleVisualizerKeyDown, sendRegionDelete } from "./region-delete.js";
  import { PLOT } from "./plot.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
  const repeatPauseDefault = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.repeatPauseSeconds ?? 0;
  const buttons = commandButtons();
  const denoiseButton: ButtonSpec = {
    command: "aqe:denoise-standard",
    icon: "sparkles",
    label: t("editor.command.denoise.label"),
    title: t("editor.command.denoise.title"),
  };

  function isSplitCommand(command: string): boolean {
    return [
      "aqe:analyze",
      "aqe:trim-left",
      "aqe:trim-right",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:remove-pauses",
      "aqe:denoise-standard",
    ].includes(command);
  }
  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer) return;
    resetAudioClockState(visualizer);
    initializePlaybackRegionState(visualizer);
    installAudioClockHandlers(visualizer);
    visualizer.dataset.sourceFilename = target.sourceFilename || "";
    configureAudioClock(visualizer, target.sourceFilename || "");
  });
</script>

<div
  class="aqe-controls"
  data-aqe-field-ord={target.ord}
  data-aqe-source-filename={target.sourceFilename}
  data-testid={`aqe-controls-${target.ord}`}
>
  {#each buttons as button (button.command)}
    {#if button.command === "aqe:play"}
      <PlaySplitButton {button} {repeatDefault} {target} />
    {:else if isSplitCommand(button.command)}
      <SplitButton {button} {target} />
    {:else}
      <button
        type="button"
        class:aqe-icon-only={button.iconOnly === true}
        class="aqe-button"
        data-aqe-command={button.command}
        data-aqe-button-state={button.command === "aqe:analyze" ? "graph" : "default"}
        data-testid={testId(target.ord, button.command)}
        title={button.title}
        aria-label={button.title}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => send(button.command, target.node, target.ord)}
      >
        <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
        {#if button.activeIcon}
          <EditorCommandIcon className="aqe-button-icon-active" icon={button.activeIcon} />
        {/if}
        <span class="aqe-button-label">{button.label}</span>
      </button>
    {/if}
    {#if button.command === "aqe:remove-pauses"}
      <SplitButton button={denoiseButton} {target} />
    {/if}
  {/each}
  <button
    type="button"
    class="aqe-button aqe-delete-region-button"
    data-aqe-command="aqe:delete-selection"
    data-aqe-button-state="default"
    data-testid={testId(target.ord, "aqe:delete-selection")}
    title={t("editor.command.delete_region.title")}
    aria-label={t("editor.command.delete_region.title")}
    hidden
    onmousedown={(event) => event.preventDefault()}
    onclick={() => sendRegionDelete("button", target.node, target.ord)}
  >
    <EditorCommandIcon icon="trash-2" />
    <span class="aqe-button-label">{t("editor.command.delete_region.label")}</span>
  </button>
  <button
    type="button"
    class="aqe-button aqe-delete-rest-button"
    data-aqe-command="aqe:delete-rest"
    data-aqe-button-state="default"
    data-testid={testId(target.ord, "aqe:delete-rest")}
    title={t("editor.command.delete_rest.title")}
    aria-label={t("editor.command.delete_rest.title")}
    hidden
    onmousedown={(event) => event.preventDefault()}
    onclick={() => sendRegionDelete("button", target.node, target.ord, "delete-rest")}
  >
    <EditorCommandIcon icon="trash-2" />
    <span class="aqe-button-label">{t("editor.command.delete_rest.label")}</span>
  </button>
  <span class="aqe-status" data-testid={`aqe-status-${target.ord}`}></span>
  <details class="aqe-help" data-testid={`aqe-help-${target.ord}`}>
    <summary class="aqe-help-summary" title={t("editor.help.title")}>
      <span class="aqe-help-triangle" aria-hidden="true"></span>
      <EditorCommandIcon icon="circle-help" />
      <span>{t("editor.help.summary")}</span>
    </summary>
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
            <span class="aqe-help-command"><EditorCommandIcon icon="audio-lines" /><span>{t("editor.command.graph.label")}</span></span>
            <span class="aqe-help-description">{t("editor.help.graph_desc")}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="folder-open" /><span>{t("editor.command.folder.label")}</span></span>
            <span class="aqe-help-description">{t("editor.help.folder_desc")}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="scissors" /><span>-L</span></span>
            <span class="aqe-help-description">{t("editor.help.trim_left_desc", { ms: window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.trimStepMs ?? 100 })}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="scissors" /><span>-R</span></span>
            <span class="aqe-help-description">{t("editor.help.trim_right_desc", { ms: window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.trimStepMs ?? 100 })}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="timer-reset" /><span>{t("editor.command.shorten_pauses.label")}</span></span>
            <span class="aqe-help-description">{t("editor.help.shorten_pauses_desc")}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="sparkles" /><span>{t("editor.command.denoise.label")}</span></span>
            <span class="aqe-help-description">{t("editor.help.denoise_desc")}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="rewind" /><span>{t("editor.command.slower.label")}</span></span>
            <span class="aqe-help-description">{t("editor.help.slower_desc")}</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="fast-forward" /><span>{t("editor.command.faster.label")}</span></span>
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
      <p class="aqe-help-note">
        {t("editor.help.note")}
      </p>
    </div>
  </details>
  <div
    class="aqe-visualizer"
    data-aqe-field-ord={target.ord}
    data-anchor-ms="0"
    data-cursor-ms="0"
    data-progress-ms="0"
    data-graph-active="false"
    data-graph-busy="false"
    data-has-track="false"
    data-playback-state="stopped"
    data-playback-engine=""
    data-playback-start-ms="0"
    data-playback-end-ms="0"
    data-playback-region-mode="full"
    data-resume-requires-restart="false"
    data-selection-active="false"
    data-selection-start-ms=""
    data-selection-end-ms=""
    data-selection-draft-active="false"
    data-selection-draft-start-ms=""
    data-selection-draft-end-ms=""
    data-repeat-enabled={repeatDefault ? "true" : "false"}
    data-repeat-pause-seconds={repeatPauseDefault}
    data-repeat-pause-waiting="false"
    data-testid={`aqe-graph-${target.ord}`}
    role="button"
    aria-label={t("editor.graph.aria")}
    tabindex="0"
    onkeydown={(event) => handleVisualizerKeyDown(event, target.ord)}
    hidden
  >
    <audio
      class="aqe-audio-clock"
      data-testid={`aqe-audio-clock-${target.ord}`}
      preload="metadata"
      hidden
    ></audio>
    <svg
      class="aqe-visualizer-svg"
      data-testid={`aqe-graph-svg-${target.ord}`}
      viewBox={`0 0 ${PLOT.width} ${PLOT.height}`}
      preserveAspectRatio="xMinYMin meet"
      role="img"
      aria-label={t("editor.graph.image_aria")}
      onpointerdown={(event) => handleVisualizerPointerDown(event, target.ord)}
    >
      <rect
        class="aqe-selection"
        data-testid={`aqe-selection-${target.ord}`}
        x={PLOT.left}
        y={PLOT.top}
        width="0"
        height={PLOT.height - PLOT.top - PLOT.bottom}
        visibility="hidden"
      ></rect>
      <path class="aqe-intensity" data-testid={`aqe-intensity-${target.ord}`} d=""></path>
      <g class="aqe-pitch" data-testid={`aqe-pitch-${target.ord}`}></g>
      <g class="aqe-labels"></g>
      <g class="aqe-x-axis" data-testid={`aqe-x-axis-${target.ord}`}></g>
      <line
        class="aqe-selection-edge aqe-selection-start"
        data-testid={`aqe-selection-start-${target.ord}`}
        x1={PLOT.left}
        x2={PLOT.left}
        y1={PLOT.top}
        y2={PLOT.height - PLOT.bottom}
        visibility="hidden"
      ></line>
      <line
        class="aqe-selection-edge aqe-selection-end"
        data-testid={`aqe-selection-end-${target.ord}`}
        x1={PLOT.left}
        x2={PLOT.left}
        y1={PLOT.top}
        y2={PLOT.height - PLOT.bottom}
        visibility="hidden"
      ></line>
      <rect
        class="aqe-selection-resize-handle aqe-selection-resize-start"
        data-testid={`aqe-selection-resize-start-${target.ord}`}
        x={PLOT.left - 5}
        y={PLOT.top}
        width="10"
        height={PLOT.height - PLOT.top - PLOT.bottom}
        rx="3"
        role="button"
        aria-label="Resize selection start"
        tabindex="0"
        visibility="hidden"
        onpointerdown={(event) => {
          if (event.shiftKey) return;
          startSelectionResizeGesture(event, target.ord, "start");
        }}
      ></rect>
      <rect
        class="aqe-selection-resize-handle aqe-selection-resize-end"
        data-testid={`aqe-selection-resize-end-${target.ord}`}
        x={PLOT.left - 5}
        y={PLOT.top}
        width="10"
        height={PLOT.height - PLOT.top - PLOT.bottom}
        rx="3"
        role="button"
        aria-label="Resize selection end"
        tabindex="0"
        visibility="hidden"
        onpointerdown={(event) => {
          if (event.shiftKey) return;
          startSelectionResizeGesture(event, target.ord, "end");
        }}
      ></rect>
      <line
        class="aqe-cursor"
        data-testid={`aqe-cursor-${target.ord}`}
        x1={PLOT.left}
        x2={PLOT.left}
        y1={PLOT.top}
        y2={PLOT.height - PLOT.bottom}
      ></line>
    </svg>
    <div class="aqe-visualizer-meta">
      <span
        class="aqe-spinner"
        data-testid={`aqe-graph-spinner-${target.ord}`}
        hidden
        aria-hidden="true"
      ></span>
      <span class="aqe-cursor-label" data-testid={`aqe-progress-label-${target.ord}`}>0 ms</span>
      <span class="aqe-visualizer-status" data-testid={`aqe-graph-status-${target.ord}`}></span>
    </div>
  </div>
</div>
