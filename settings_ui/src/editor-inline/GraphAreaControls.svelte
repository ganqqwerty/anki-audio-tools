<script lang="ts">
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { buttonTooltipContent } from "../lib/disabled-tooltip.js";
  import {
    graphConnectDropoutsNote,
    graphVoiceRangeTooltip,
  } from "../lib/graph-option-copy.js";
  import { normalizeVisibleEditorButtons } from "../lib/editor-toolbar-visibility.js";
  import { t } from "../lib/i18n.js";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";
  import { send } from "./actions.js";
  import { toolbarButtons } from "./commands.js";
  import { controlsForOrd, visualizerForOrd } from "./dom-selectors.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { requestGraph } from "./graph-actions.js";
  import {
    GRAPH_SPLIT_STATE_CHANGED_EVENT,
    setGraphConnectShortDropoutsForField,
    setGraphVoiceRangeForField,
    type GraphSplitStateChangedDetail,
  } from "./graph-split-state.js";
  import {
    formatGraphVoiceRange,
    GRAPH_VOICE_RANGES,
  } from "./graph-split-values.js";
  import { getSplitButtonState } from "./split-button-state.js";
  import type { EditorCommand, FieldSplitButtonState, FieldTarget } from "./types.js";
  import type { GraphVoiceRange } from "./graph-settings.js";

  const {
    target,
    visibleCommands,
  }: {
    target: FieldTarget;
    visibleCommands: readonly EditorCommand[] | undefined;
  } = $props();

  let graphConnectShortDropoutsMs = $state(240);
  let graphVoiceRange = $state<GraphVoiceRange>("general");
  let busy = $state(false);

  const normalizedVisibleCommands = $derived(new Set(
    normalizeVisibleEditorButtons(toolbarButtons(), visibleCommands),
  ));
  const showPlay = $derived(normalizedVisibleCommands.has("aqe:play"));
  const showGraphSettings = $derived(normalizedVisibleCommands.has("aqe:analyze"));
  const showActionRail = $derived(showPlay);
  const playTooltip = $derived(buttonTooltipContent(
    t("editor.command.play.label"),
    t("editor.command.play.title"),
  ));
  const voiceRangeTooltip = $derived(graphVoiceRangeTooltip(graphVoiceRange));
  const holesTooltip = $derived(buttonTooltipContent(
    t("editor.graph.options.connect_dropouts"),
    graphConnectDropoutsNote(),
  ));

  function syncFromState(state: FieldSplitButtonState): void {
    graphConnectShortDropoutsMs = state.graphConnectShortDropoutsMs;
    graphVoiceRange = state.graphVoiceRange;
  }

  function syncFromDom(): void {
    const visualizer = visualizerForOrd(target.ord);
    const controls = controlsForOrd(target.ord);
    busy = document.body.dataset.aqeBusy === "true"
      || controls?.dataset.busy === "true"
      || visualizer?.dataset.graphBusy === "true";
    syncFromState(getSplitButtonState(target.ord));
  }

  function graphIsReadyForRedraw(): boolean {
    const visualizer = visualizerForOrd(target.ord);
    return Boolean(
      visualizer
      && visualizer.dataset.graphActive === "true"
      && visualizer.dataset.graphBusy !== "true"
      && document.body.dataset.aqeBusy !== "true",
    );
  }

  function requestActiveGraphRedraw(): void {
    if (graphIsReadyForRedraw()) requestGraph(target.ord, true);
  }

  function dispatchPlay(): void {
    send("aqe:play", target.node, target.ord);
  }

  function applyVoiceRange(event: Event): void {
    const nextState = setGraphVoiceRangeForField(
      target.ord,
      (event.currentTarget as HTMLSelectElement).value as GraphVoiceRange,
    );
    syncFromState(nextState);
    requestActiveGraphRedraw();
  }

  function applyConnectShortDropouts(value: number): void {
    const nextState = setGraphConnectShortDropoutsForField(target.ord, value);
    syncFromState(nextState);
    requestActiveGraphRedraw();
  }

  onMount(() => {
    const visualizer = visualizerForOrd(target.ord);
    const controls = controlsForOrd(target.ord);
    const visualizerObserver = new MutationObserver(syncFromDom);
    const controlsObserver = new MutationObserver(syncFromDom);
    const bodyObserver = new MutationObserver(syncFromDom);
    const handleGraphSplitStateChanged = (event: Event): void => {
      const detail = (event as CustomEvent<GraphSplitStateChangedDetail>).detail;
      if (detail?.ord !== target.ord) return;
      syncFromState(detail.state);
    };

    syncFromDom();
    if (visualizer) {
      visualizerObserver.observe(visualizer, {
        attributes: true,
        attributeFilter: ["data-graph-busy", "data-playback-state"],
      });
    }
    if (controls) {
      controlsObserver.observe(controls, {
        attributes: true,
        attributeFilter: ["data-busy"],
      });
    }
    bodyObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["data-aqe-busy"],
    });
    window.addEventListener(GRAPH_SPLIT_STATE_CHANGED_EVENT, handleGraphSplitStateChanged);
    return () => {
      visualizerObserver.disconnect();
      controlsObserver.disconnect();
      bodyObserver.disconnect();
      window.removeEventListener(GRAPH_SPLIT_STATE_CHANGED_EVENT, handleGraphSplitStateChanged);
    };
  });
</script>

{#if showActionRail}
  <div class="aqe-graph-action-rail" data-testid={`aqe-graph-action-rail-${target.ord}`}>
    {#if showPlay}
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-icon-only aqe-graph-action-button aqe-graph-play-button aqe-tooltip-target"
            data-aqe-command="aqe:play"
            data-aqe-button-state="play"
            data-aqe-enabled-title={playTooltip}
            data-aqe-tooltip-content={playTooltip}
            data-testid={`aqe-graph-play-${target.ord}`}
            aria-label={playTooltip}
            disabled={busy}
            onmousedown={(event) => event.preventDefault()}
            onclick={dispatchPlay}
          >
            <EditorCommandIcon className="aqe-button-icon-default" icon="play" />
            <EditorCommandIcon className="aqe-button-icon-active" icon="pause" />
            <span class="aqe-button-label">{t("editor.command.play.label")}</span>
          </button>
        {/snippet}
      </AqeTooltip>
    {/if}
  </div>
{/if}

{#if showGraphSettings}
  <div class="aqe-graph-settings-bar" data-testid={`aqe-graph-settings-${target.ord}`}>
    <label class="aqe-graph-compact-field">
      <span>{t("editor.graph.options.voice_range")}</span>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <select
            {...props}
            class="aqe-graph-compact-select aqe-tooltip-target"
            data-aqe-tooltip-content={voiceRangeTooltip}
            data-testid={`aqe-graph-voice-range-${target.ord}`}
            aria-label={t("editor.graph.options.voice_range")}
            disabled={busy}
            value={graphVoiceRange}
            onchange={applyVoiceRange}
          >
            {#each GRAPH_VOICE_RANGES as option}
              <option value={option}>{formatGraphVoiceRange(option)}</option>
            {/each}
          </select>
        {/snippet}
      </AqeTooltip>
    </label>
    <label class="aqe-graph-compact-field aqe-graph-compact-field-number">
      <span>{t("editor.graph.options.connect_dropouts")}</span>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <span
            {...props}
            class="aqe-tooltip-target"
            data-aqe-tooltip-content={holesTooltip}
          >
            <UnitNumberInput
              inputClass="aqe-graph-compact-number"
              testId={`aqe-graph-connect-dropouts-${target.ord}`}
              min="0"
              max="500"
              step="30"
              value={graphConnectShortDropoutsMs}
              unit="ms"
              ariaLabel={t("editor.graph.options.connect_dropouts")}
              disabled={busy}
              onValueInput={applyConnectShortDropouts}
            />
          </span>
        {/snippet}
      </AqeTooltip>
    </label>
  </div>
{/if}
