<script lang="ts">
  import { onMount } from "svelte";

  import { COMMAND_BUTTONS, DENOISE_BUTTONS, testId } from "./commands.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import {
    handleVisualizerPointerDown,
    initializePlaybackRegionState,
    installAudioClockHandlers,
    resetAudioClockState,
    send,
    setRepeatEnabledForOrd,
    visualizerForOrd,
  } from "./actions.js";
  import { PLOT } from "./plot.js";
  import type { FieldTarget } from "./types.js";

  const { target }: { target: FieldTarget } = $props();
  const repeatDefault = window.__AQE_EDITOR_CONFIG__?.repeatPlaybackByDefault === true;

  function toggleRepeat(event: MouseEvent): void {
    const button = event.currentTarget as HTMLButtonElement;
    const enabled = button.ariaPressed !== "true";
    setRepeatEnabledForOrd(target.ord, enabled);
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
      <details class="aqe-menu" data-testid={`aqe-denoise-menu-${target.ord}`}>
        <summary class="aqe-button aqe-menu-summary" title="Denoise audio" aria-label="Denoise audio">
          <EditorCommandIcon icon="sparkles" />
          <span class="aqe-button-label">Denoise</span>
          <EditorCommandIcon className="aqe-menu-chevron" icon="chevron-down" />
        </summary>
        <div class="aqe-menu-items" role="menu">
          {#each DENOISE_BUTTONS as denoiseButton (denoiseButton.command)}
            <button
              type="button"
              class="aqe-button aqe-menu-item"
              data-aqe-command={denoiseButton.command}
              data-aqe-button-state="default"
              data-testid={testId(target.ord, denoiseButton.command)}
              title={denoiseButton.title}
              aria-label={denoiseButton.title}
              role="menuitem"
              onmousedown={(event) => event.preventDefault()}
              onclick={() => send(denoiseButton.command, target.node, target.ord)}
            >
              <EditorCommandIcon icon={denoiseButton.icon} />
              <span class="aqe-button-label">{denoiseButton.label}</span>
            </button>
          {/each}
        </div>
      </details>
    {/if}
  {/each}
  <span class="aqe-status" data-testid={`aqe-status-${target.ord}`}></span>
  <details class="aqe-help" data-testid={`aqe-help-${target.ord}`}>
    <summary class="aqe-help-summary" title="Show editor help">
      <EditorCommandIcon icon="circle-help" />
      <span>Help</span>
    </summary>
    <div class="aqe-help-body">
      <p>Holding Shift on the graph selects a region. Playing with a selected region plays only that region; Repeat loops the selected region, or the full graph when no region is selected.</p>
      <p>Play starts or pauses audio. Graph shows the pitch and loudness graph. Folder opens the current audio file. -L and -R trim 100 ms from the left or right. Shorten Pauses speeds up long internal pauses. Denoise Standard uses DeepFilterNet, and Denoise RNNoise uses RNNoise. Slower and Faster change speed. Volume - and Volume + change loudness. Undo and Redo move through generated audio edits. Settings opens the add-on settings.</p>
      <p>In the graph, grey is loudness and lines are pitch of the voice.</p>
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
