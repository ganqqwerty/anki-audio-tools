<script lang="ts">
  import { onMount } from "svelte";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import { send } from "./actions.js";
  import {
    buildTrimCommandPayload,
    formatTrimMs,
    getSplitButtonState,
    setTrimStepForField,
  } from "./split-button-state.js";
  import { COMMAND_SLUGS } from "./commands.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const { button, target }: { button: ButtonSpec; target: FieldTarget } = $props();
  const presets = [100, 200, 500, 1000];
  let wrapper: HTMLSpanElement;
  let open = $state(false);
  let trimStepMs = $state(100);

  function slug(): string {
    return COMMAND_SLUGS[button.command];
  }

  function close(): void {
    open = false;
  }

  function toggle(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    open = !open;
  }

  function applyTrimStep(value: number): void {
    trimStepMs = setTrimStepForField(target.ord, value).trimStepMs;
  }

  function dispatchPrimary(): void {
    close();
    send(button.command, target.node, target.ord, buildTrimCommandPayload(button.command, target.ord));
  }

  function onDocumentPointerDown(event: MouseEvent): void {
    if (!open || !wrapper) return;
    if (event.target instanceof Node && wrapper.contains(event.target)) return;
    close();
  }

  function onDocumentKeyDown(event: KeyboardEvent): void {
    if (event.key === "Escape") close();
  }

  onMount(() => {
    trimStepMs = getSplitButtonState(target.ord).trimStepMs;
    document.addEventListener("mousedown", onDocumentPointerDown, true);
    document.addEventListener("keydown", onDocumentKeyDown, true);
    return () => {
      document.removeEventListener("mousedown", onDocumentPointerDown, true);
      document.removeEventListener("keydown", onDocumentKeyDown, true);
    };
  });
</script>

<span class="aqe-split-button" bind:this={wrapper}>
  <button
    type="button"
    class="aqe-button aqe-split-primary"
    data-aqe-command={button.command}
    data-aqe-button-state="default"
    data-testid={`aqe-button-${target.ord}-${slug()}`}
    title={button.title}
    aria-label={button.title}
    onmousedown={(event) => event.preventDefault()}
    onclick={dispatchPrimary}
  >
    <EditorCommandIcon icon={button.icon} />
    <span class="aqe-button-label">{button.label}</span>
  </button>
  <button
    type="button"
    class="aqe-button aqe-icon-only aqe-split-menu-button"
    data-testid={`aqe-split-${target.ord}-${slug()}-menu`}
    title={`${button.title} amount`}
    aria-label={`${button.title} amount`}
    aria-expanded={open ? "true" : "false"}
    onmousedown={(event) => event.preventDefault()}
    onclick={toggle}
  >
    <EditorCommandIcon icon="chevron-down" />
    <span class="aqe-button-label">Options</span>
  </button>
  {#if open}
    <div class="aqe-split-popover" data-testid={`aqe-split-${target.ord}-${slug()}-popover`}>
      <div class="aqe-split-popover-header">
        <strong>{button.label}</strong>
        <span>{formatTrimMs(trimStepMs)}</span>
      </div>
      <input
        data-testid={`aqe-split-${target.ord}-${slug()}-slider`}
        type="range"
        min="50"
        max="10000"
        step="50"
        value={trimStepMs}
        oninput={(event) => applyTrimStep(Number((event.currentTarget as HTMLInputElement).value))}
      />
      <div class="aqe-split-range-labels">
        <span>50 ms</span>
        <span>10 s</span>
      </div>
      <div class="aqe-split-presets">
        {#each presets as preset}
          <button
            type="button"
            class="aqe-button aqe-split-preset"
            data-testid={`aqe-split-${target.ord}-${slug()}-preset-${preset}`}
            aria-pressed={trimStepMs === preset ? "true" : "false"}
            onclick={() => applyTrimStep(preset)}
          >
            {formatTrimMs(preset)}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</span>
