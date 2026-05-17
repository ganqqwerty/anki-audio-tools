<script lang="ts">
  import { onMount } from "svelte";

  import { COMMAND_BUTTONS, testId } from "./commands.js";
  import {
    handleVisualizerPointerDown,
    installAudioClockHandlers,
    resetAudioClockState,
    send,
    visualizerForOrd,
  } from "./actions.js";
  import { PLOT } from "./plot.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    if (!visualizer) return;
    resetAudioClockState(visualizer);
    installAudioClockHandlers(visualizer);
  });
</script>

<div
  class="aqe-controls"
  data-aqe-field-ord={target.ord}
  data-aqe-source-filename={target.sourceFilename}
  data-testid={`aqe-controls-${target.ord}`}
>
  {#each COMMAND_BUTTONS as button (button.command)}
    <button
      type="button"
      class="aqe-button"
      data-aqe-command={button.command}
      data-testid={testId(target.ord, button.command)}
      title={button.title}
      onmousedown={(event) => event.preventDefault()}
      onclick={() => send(button.command, target.node, target.ord)}
    >
      {button.label}
    </button>
  {/each}
  <span class="aqe-status" data-testid={`aqe-status-${target.ord}`}></span>
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
    data-resume-requires-restart="false"
    data-testid={`aqe-graph-${target.ord}`}
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
      role="img"
      aria-label="Audio pitch and intensity visualization"
      onpointerdown={(event) => handleVisualizerPointerDown(event, target.ord)}
    >
      <path class="aqe-intensity" data-testid={`aqe-intensity-${target.ord}`} d=""></path>
      <g class="aqe-pitch" data-testid={`aqe-pitch-${target.ord}`}></g>
      <g class="aqe-labels"></g>
      <g class="aqe-x-axis" data-testid={`aqe-x-axis-${target.ord}`}></g>
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

<style>
  :global(.aqe-controls) {
    align-items: center;
    border: 1px solid;
    border-radius: 10px;
    color: inherit;
    color-scheme: light dark;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    justify-content: flex-start;
    margin: 4px 0 10px;
    padding: 6px 8px;
  }
  :global(.aqe-button) {
    background: transparent;
    border: 1px solid;
    border-radius: 7px;
    color: inherit;
    cursor: pointer;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 8px;
  }
  :global(.aqe-button:hover) {
    text-decoration: underline;
  }
  :global(.aqe-controls[data-busy="true"]) {
    border-style: dashed;
  }
  :global(.aqe-button:disabled) {
    cursor: not-allowed;
    opacity: 0.45;
  }
  :global(.aqe-button:disabled:hover) {
    text-decoration: none;
  }
  :global(.aqe-status) {
    font-size: 12px;
    margin-left: 4px;
  }
  :global(.aqe-status[data-kind="error"]) {
    font-weight: 700;
  }
  :global(.aqe-visualizer) {
    align-self: stretch;
    flex: 1 0 100%;
    max-width: none;
    min-width: 0;
    width: 100%;
  }
  :global(.aqe-visualizer[hidden]) {
    display: none;
  }
  :global(.aqe-visualizer[data-has-track="false"] .aqe-visualizer-svg),
  :global(.aqe-visualizer[data-has-track="false"] .aqe-cursor-label) {
    display: none;
  }
  :global(.aqe-visualizer-svg) {
    border: 1px solid;
    border-radius: 8px;
    color: inherit;
    display: block;
    height: 150px;
    margin-top: 4px;
    width: 100%;
  }
  :global(.aqe-intensity) {
    fill: currentColor;
    opacity: 0.12;
    stroke: none;
  }
  :global(.aqe-pitch-path) {
    fill: none;
    opacity: 0.9;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 2;
  }
  :global(.aqe-cursor) {
    opacity: 0.8;
    pointer-events: none;
    stroke: currentColor;
    stroke-width: 1.5;
  }
  :global(.aqe-hz-label),
  :global(.aqe-x-label) {
    fill: currentColor;
    font-size: 11px;
    opacity: 0.8;
  }
  :global(.aqe-x-label) {
    text-anchor: middle;
  }
  :global(.aqe-x-tick) {
    opacity: 0.5;
    stroke: currentColor;
    stroke-width: 1;
  }
  :global(.aqe-visualizer-meta) {
    align-items: center;
    display: flex;
    font-size: 12px;
    gap: 8px;
    justify-content: flex-start;
    margin-top: 2px;
  }
  :global(.aqe-spinner) {
    animation: aqe-spin 800ms linear infinite;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 999px;
    box-sizing: border-box;
    display: inline-block;
    height: 12px;
    opacity: 0.75;
    width: 12px;
  }
  :global(.aqe-spinner[hidden]) {
    display: none;
  }
  :global(.aqe-visualizer-status[data-kind="error"]) {
    font-weight: 700;
  }
  @keyframes aqe-spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
