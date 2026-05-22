<script lang="ts">
  import { onMount } from "svelte";
  import { testId, toolbarButtons, visibleToolbarButtons } from "./commands.js";
  import { t } from "../lib/i18n.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import EditorHelp from "./EditorHelp.svelte";
  import PlaySplitButton from "./PlaySplitButton.svelte";
  import SelectionToolbar from "./SelectionToolbar.svelte";
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
  import { handleVisualizerKeyDown } from "./region-delete.js";
  import { PLOT } from "./plot.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  const selectionPlotHeight = PLOT.height - PLOT.top - PLOT.bottom;
  const selectionHandleHeight = selectionPlotHeight * 0.8;
  const selectionHandleY = PLOT.top + (selectionPlotHeight - selectionHandleHeight) / 2;
  const selectionHandleCenterY = selectionHandleY + selectionHandleHeight / 2;
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
  const repeatPauseDefault = window.__AQE_EDITOR_CONFIG__?.splitButtonDefaults?.repeatPauseSeconds ?? 0;
  const buttons = visibleToolbarButtons(
    toolbarButtons(),
    window.__AQE_EDITOR_CONFIG__?.visibleEditorButtons,
  );

  function isSplitCommand(command: string): boolean {
    return [
      "aqe:analyze",
      "aqe:share",
      "aqe:convert",
      "aqe:slower",
      "aqe:faster",
      "aqe:volume-down",
      "aqe:volume-up",
      "aqe:remove-pauses",
      "aqe:denoise-standard",
      "aqe:pitch-hum",
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
  {/each}
  <span class="aqe-status" data-testid={`aqe-status-${target.ord}`}></span>
  <EditorHelp ord={target.ord} />
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
    <div class="aqe-visualizer-plot" data-testid={`aqe-visualizer-plot-${target.ord}`}>
      <div class="aqe-selection-region-preview-halo aqe-selection-region-preview-halo-top" aria-hidden="true"></div>
      <div class="aqe-selection-region-preview-halo aqe-selection-region-preview-halo-bottom" aria-hidden="true"></div>
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
        y={selectionHandleY}
        width="10"
        height={selectionHandleHeight}
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
      <g
        class="aqe-selection-resize-grip aqe-selection-resize-grip-start"
        transform={`translate(${PLOT.left} ${selectionHandleCenterY})`}
        visibility="hidden"
        aria-hidden="true"
      >
        <line x1="-3" x2="3" y1="-10" y2="-10"></line>
        <line x1="-3" x2="3" y1="0" y2="0"></line>
        <line x1="-3" x2="3" y1="10" y2="10"></line>
      </g>
      <rect
        class="aqe-selection-resize-handle aqe-selection-resize-end"
        data-testid={`aqe-selection-resize-end-${target.ord}`}
        x={PLOT.left - 5}
        y={selectionHandleY}
        width="10"
        height={selectionHandleHeight}
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
      <g
        class="aqe-selection-resize-grip aqe-selection-resize-grip-end"
        transform={`translate(${PLOT.left} ${selectionHandleCenterY})`}
        visibility="hidden"
        aria-hidden="true"
      >
        <line x1="-3" x2="3" y1="-10" y2="-10"></line>
        <line x1="-3" x2="3" y1="0" y2="0"></line>
        <line x1="-3" x2="3" y1="10" y2="10"></line>
      </g>
      <line
        class="aqe-cursor"
        data-testid={`aqe-cursor-${target.ord}`}
        x1={PLOT.left}
        x2={PLOT.left}
        y1={PLOT.top}
        y2={PLOT.height - PLOT.bottom}
      ></line>
      <circle
        class="aqe-cursor-pitch-marker"
        data-testid={`aqe-cursor-pitch-marker-${target.ord}`}
        cx={PLOT.left}
        cy={PLOT.height - PLOT.bottom}
        r="4"
        visibility="hidden"
        aria-hidden="true"
      ></circle>
      <g
        class="aqe-cursor-flag"
        data-testid={`aqe-cursor-flag-${target.ord}`}
        visibility="hidden"
        aria-hidden="true"
      >
        <rect class="aqe-cursor-flag-box" x="-41" y="0" width="82" height="20" rx="4"></rect>
        <path class="aqe-cursor-flag-notch" d="M -5 20 L 0 26 L 5 20 Z"></path>
        <text class="aqe-cursor-flag-text" x="0" y="14">
          <tspan class="aqe-cursor-flag-current">0 ms</tspan>
          <tspan class="aqe-cursor-flag-pitch"> / -- Hz</tspan>
        </text>
      </g>
      </svg>
      <SelectionToolbar {target} />
    </div>
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
