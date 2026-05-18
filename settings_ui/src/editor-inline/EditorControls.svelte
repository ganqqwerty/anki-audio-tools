<script lang="ts">
  import { onMount } from "svelte";

  import { COMMAND_BUTTONS, testId } from "./commands.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitButton from "./SplitButton.svelte";
  import {
    handleVisualizerPointerDown,
    initializePlaybackRegionState,
    installAudioClockHandlers,
    resetAudioClockState,
    send,
    setRepeatEnabledForOrd,
  } from "./actions.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { handleVisualizerKeyDown, sendRegionDelete } from "./region-delete.js";
  import { PLOT } from "./plot.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;
  const denoiseButton: ButtonSpec = {
    command: "aqe:denoise-standard",
    icon: "sparkles",
    label: "Denoise",
    title: "Denoise audio",
  };

  function toggleRepeat(event: MouseEvent): void {
    const button = event.currentTarget as HTMLButtonElement;
    const enabled = button.ariaPressed !== "true";
    setRepeatEnabledForOrd(target.ord, enabled);
  }

  function isSplitCommand(command: string): boolean {
    return [
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
  });
</script>

<div
  class="aqe-controls"
  data-aqe-field-ord={target.ord}
  data-aqe-source-filename={target.sourceFilename}
  data-testid={`aqe-controls-${target.ord}`}
>
  {#each COMMAND_BUTTONS as button (button.command)}
    {#if isSplitCommand(button.command)}
      <SplitButton {button} {target} />
    {:else}
      <button
        type="button"
        class:aqe-icon-only={button.iconOnly === true}
        class="aqe-button"
        data-aqe-command={button.command}
        data-aqe-button-state={button.command === "aqe:play" ? "play" : button.command === "aqe:analyze" ? "graph" : "default"}
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
    {#if button.command === "aqe:play"}
      <button
        type="button"
        class="aqe-button aqe-icon-only aqe-repeat-button"
        data-aqe-button-state={repeatDefault ? "active" : "default"}
        data-testid={`aqe-repeat-${target.ord}`}
        title="Repeat selected region, or the whole graph when no region is selected."
        aria-label="Repeat playback"
        aria-pressed={repeatDefault ? "true" : "false"}
        onmousedown={(event) => event.preventDefault()}
        onclick={toggleRepeat}
      >
        <EditorCommandIcon icon="repeat-2" />
        <span class="aqe-button-label">Repeat</span>
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
    title="Delete selected region"
    aria-label="Delete selected region"
    hidden
    onmousedown={(event) => event.preventDefault()}
    onclick={() => sendRegionDelete("button", target.node, target.ord)}
  >
    <EditorCommandIcon icon="trash-2" />
    <span class="aqe-button-label">Delete Region</span>
  </button>
  <span class="aqe-status" data-testid={`aqe-status-${target.ord}`}></span>
  <details class="aqe-help" data-testid={`aqe-help-${target.ord}`}>
    <summary class="aqe-help-summary" title="Show editor help">
      <EditorCommandIcon icon="circle-help" />
      <span>Help</span>
    </summary>
    <div class="aqe-help-body">
      <section class="aqe-help-section">
        <h4 class="aqe-help-title">Graph and regions</h4>
        <ul class="aqe-help-list">
          <li><kbd>Shift</kbd>-drag on the graph to select a region.</li>
          <li>Play uses the selected region when one is active; Repeat loops the selected region, or the full graph otherwise.</li>
          <li>Delete Region removes only the selected region. Backspace does the same when the graph is focused.</li>
          <li>In the graph, grey is loudness and lines are pitch of the voice.</li>
        </ul>
      </section>
      <section class="aqe-help-section">
        <h4 class="aqe-help-title">Buttons</h4>
        <div class="aqe-help-grid">
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="play" /><span>Play</span></span>
            <span>Start or pause audio.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="chart-line" /><span>Graph</span></span>
            <span>Show pitch and loudness.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="folder-open" /><span>Folder</span></span>
            <span>Open the current audio file.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="scissors" /><span>-L</span></span>
            <span>Trim 100 ms from the left.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="scissors" /><span>-R</span></span>
            <span>Trim 100 ms from the right.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="timer-reset" /><span>Shorten Pauses</span></span>
            <span>Speed up long internal pauses.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="sparkles" /><span>Denoise</span></span>
            <span>Use Standard or RNNoise cleanup.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="rewind" /><span>Slower</span></span>
            <span>Decrease speed.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="fast-forward" /><span>Faster</span></span>
            <span>Increase speed.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="volume-1" /><span>Volume -</span></span>
            <span>Decrease loudness.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="volume-2" /><span>Volume +</span></span>
            <span>Increase loudness.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="undo-2" /><span>Undo</span></span>
            <span>Restore the previous edit.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="redo-2" /><span>Redo</span></span>
            <span>Restore the undone edit.</span>
          </span>
          <span class="aqe-help-item">
            <span class="aqe-help-command"><EditorCommandIcon icon="trash-2" /><span>Delete Region</span></span>
            <span>Remove the selected graph region.</span>
          </span>
        </div>
      </section>
      <p class="aqe-help-note">
        Every edit creates a new media file and updates the field to point at it. The original file remains in your media collection.
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
    data-testid={`aqe-graph-${target.ord}`}
    role="button"
    aria-label="Audio graph"
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
      aria-label="Audio pitch and intensity visualization"
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
