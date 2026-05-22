<script lang="ts">
  import { onMount, tick } from "svelte";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { setRepeatEnabledForOrd, setRepeatPauseSecondsForOrd, send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import { playRepeatOptionsTitle } from "./control-actions.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import {
    formatRepeatPauseSeconds,
    getSplitButtonState,
    promoteSplitDefaultsForField,
    setRepeatPauseSecondsForField,
  } from "./split-button-state.js";
  import { t } from "../lib/i18n.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const POPOVER_GAP_PX = 4;
  const VIEWPORT_MARGIN_PX = 8;
  const HIDDEN_POPOVER_STYLE = "visibility: hidden;";
  const PRESETS = [0, 0.5, 2, 10] as const;

  const { button, repeatDefault, target }: {
    button: ButtonSpec;
    repeatDefault: boolean;
    target: FieldTarget;
  } = $props();
  let wrapper = $state<HTMLSpanElement>();
  let popover = $state<HTMLDivElement>();
  let open = $state(false);
  let popoverStyle = $state(HIDDEN_POPOVER_STYLE);
  let pressed = $state(false);
  let repeatPauseSeconds = $state(0);
  let defaultSaved = $state(false);
  let defaultSavedTimer: number | undefined;
  const menuTitle = $derived(playRepeatOptionsTitle(pressed));

  function close(): void {
    open = false;
    popoverStyle = HIDDEN_POPOVER_STYLE;
  }

  function syncRepeatState(): void {
    const visualizer = visualizerForOrd(target.ord);
    pressed = visualizer ? visualizer.dataset.repeatEnabled === "true" : repeatDefault;
    const state = getSplitButtonState(target.ord);
    repeatPauseSeconds = state.repeatPauseSeconds;
    setRepeatPauseSecondsForOrd(target.ord, repeatPauseSeconds);
  }

  function toggleMenu(event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    if (open) {
      close();
      return;
    }
    syncRepeatState();
    open = true;
  }

  function toggleRepeat(event: MouseEvent): void {
    const button = event.currentTarget as HTMLButtonElement;
    const enabled = button.ariaPressed !== "true";
    defaultSaved = false;
    pressed = enabled;
    setRepeatEnabledForOrd(target.ord, enabled);
  }

  function applyValue(value: number): void {
    defaultSaved = false;
    const state = setRepeatPauseSecondsForField(target.ord, value);
    repeatPauseSeconds = state.repeatPauseSeconds;
    setRepeatPauseSecondsForOrd(target.ord, repeatPauseSeconds);
    void updatePopoverPlacement();
  }

  function dispatchPrimary(): void {
    close();
    send(button.command, target.node, target.ord);
  }

  function showDefaultSaved(): void {
    defaultSaved = true;
    if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    defaultSavedTimer = window.setTimeout(() => {
      defaultSaved = false;
      defaultSavedTimer = undefined;
    }, 1400);
  }

  function saveCurrentDefaults(): void {
    const request = {
      defaults: {
        repeatPauseSeconds,
        repeatPlaybackByDefault: pressed,
      },
      fieldOrd: target.ord,
    };
    sendSplitDefaultSaveRequest(request);
    window.__AQE_EDITOR_CONFIG__ = {
      ...(window.__AQE_EDITOR_CONFIG__ ?? { audioFieldIndices: [] }),
      repeatPlaybackByDefault: pressed,
    };
    repeatPauseSeconds = promoteSplitDefaultsForField(target.ord, request.defaults).repeatPauseSeconds;
    setRepeatPauseSecondsForOrd(target.ord, repeatPauseSeconds);
    showDefaultSaved();
    void updatePopoverPlacement();
  }

  function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
  }

  function viewportBounds(): { width: number; height: number } {
    return {
      width: window.innerWidth || document.documentElement.clientWidth,
      height: window.innerHeight || document.documentElement.clientHeight,
    };
  }

  function positionPopover(): void {
    if (!wrapper || !popover) return;

    const anchorRect = wrapper.getBoundingClientRect();
    const popoverRect = popover.getBoundingClientRect();
    const viewport = viewportBounds();
    const maxLeft = Math.max(VIEWPORT_MARGIN_PX, viewport.width - popoverRect.width - VIEWPORT_MARGIN_PX);
    const maxTop = Math.max(VIEWPORT_MARGIN_PX, viewport.height - popoverRect.height - VIEWPORT_MARGIN_PX);
    const centeredLeft = anchorRect.left + anchorRect.width / 2 - popoverRect.width / 2;
    const belowTop = anchorRect.bottom + POPOVER_GAP_PX;
    const aboveTop = anchorRect.top - popoverRect.height - POPOVER_GAP_PX;
    const fitsBelow = belowTop + popoverRect.height <= viewport.height - VIEWPORT_MARGIN_PX;
    const fitsAbove = aboveTop >= VIEWPORT_MARGIN_PX;
    const preferredTop = !fitsBelow && fitsAbove ? aboveTop : belowTop;

    popoverStyle = [
      `left: ${clamp(centeredLeft, VIEWPORT_MARGIN_PX, maxLeft)}px;`,
      `top: ${clamp(preferredTop, VIEWPORT_MARGIN_PX, maxTop)}px;`,
      `max-height: ${Math.max(80, viewport.height - VIEWPORT_MARGIN_PX * 2)}px;`,
    ].join(" ");
  }

  async function updatePopoverPlacement(): Promise<void> {
    if (!open) return;
    await tick();
    if (!open) return;
    positionPopover();
  }

  function onViewportChange(): void {
    void updatePopoverPlacement();
  }

  function onDocumentPointerDown(event: MouseEvent): void {
    if (!open || !wrapper) return;
    if (event.target instanceof Node && wrapper.contains(event.target)) return;
    close();
  }

  function onDocumentKeyDown(event: KeyboardEvent): void {
    if (event.key === "Escape") close();
  }

  $effect(() => {
    if (open) {
      void updatePopoverPlacement();
    } else {
      popoverStyle = HIDDEN_POPOVER_STYLE;
    }
  });

  onMount(() => {
    syncRepeatState();
    document.addEventListener("mousedown", onDocumentPointerDown, true);
    document.addEventListener("keydown", onDocumentKeyDown, true);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      document.removeEventListener("mousedown", onDocumentPointerDown, true);
      document.removeEventListener("keydown", onDocumentKeyDown, true);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

<span class="aqe-split-button aqe-play-split-button" bind:this={wrapper}>
  <button
    type="button"
    class:aqe-icon-only={button.iconOnly === true}
    class="aqe-button aqe-split-primary"
    data-aqe-command={button.command}
    data-aqe-button-state="play"
    data-testid={`aqe-button-${target.ord}-play`}
    title={button.title}
    aria-label={button.title}
    onmousedown={(event) => event.preventDefault()}
    onclick={dispatchPrimary}
  >
    <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
    {#if button.activeIcon}
      <EditorCommandIcon className="aqe-button-icon-active" icon={button.activeIcon} />
    {/if}
    <span class="aqe-button-label">{button.label}</span>
  </button>
  <button
    type="button"
    class="aqe-button aqe-icon-only aqe-split-menu-button aqe-play-repeat-menu-button"
    data-aqe-button-state={pressed ? "active" : "default"}
    data-testid={`aqe-split-${target.ord}-play-menu`}
    title={menuTitle}
    aria-label={menuTitle}
    aria-expanded={open ? "true" : "false"}
    onmousedown={(event) => event.preventDefault()}
    onclick={toggleMenu}
  >
    <EditorCommandIcon icon="chevron-down" />
    <span class="aqe-button-label">{t("editor.split.options")}</span>
  </button>
  {#if open}
    <div
      bind:this={popover}
      class="aqe-split-popover aqe-play-split-popover"
      data-testid={`aqe-split-${target.ord}-play-popover`}
      style={popoverStyle}
    >
      <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
        <span class="aqe-split-popover-title">
          <strong>{t("editor.command.play.label")}</strong>
          <span>{pressed ? t("editor.play.repeat_on") : t("editor.play.repeat_off")}</span>
        </span>
        <SplitDefaultSaveButton
          onSave={saveCurrentDefaults}
          saved={defaultSaved}
          testId={`aqe-split-${target.ord}-play-save-default`}
        />
      </div>
      <button
        type="button"
        class="aqe-button aqe-repeat-button aqe-repeat-toggle-button"
        data-aqe-button-state={pressed ? "active" : "default"}
        data-testid={`aqe-repeat-${target.ord}`}
        title={t("editor.repeat.title")}
        aria-label={t("editor.repeat.aria")}
        aria-pressed={pressed ? "true" : "false"}
        onmousedown={(event) => event.preventDefault()}
        onclick={toggleRepeat}
      >
        <EditorCommandIcon icon="repeat-2" />
        <span class="aqe-button-label">{t("editor.repeat.label")}</span>
      </button>
      <div class="aqe-split-popover-header">
        <strong>{t("editor.repeat.pause_seconds")}</strong>
        <input
          class="aqe-split-value-input"
          data-testid={`aqe-split-${target.ord}-repeat-value`}
          type="number"
          min="0"
          max="10"
          step="0.1"
          value={repeatPauseSeconds}
          aria-label={t("editor.repeat.pause_seconds")}
          oninput={(event) => applyValue((event.currentTarget as HTMLInputElement).valueAsNumber)}
        />
      </div>
      <input
        data-testid={`aqe-split-${target.ord}-repeat-slider`}
        type="range"
        min="0"
        max="10"
        step="0.1"
        value={repeatPauseSeconds}
        oninput={(event) => applyValue(Number((event.currentTarget as HTMLInputElement).value))}
      />
      <div class="aqe-split-range-labels">
        <span>0 s</span>
        <span>10 s</span>
      </div>
      <div class="aqe-split-presets">
        {#each PRESETS as preset}
          <button
            type="button"
            class="aqe-button aqe-split-preset"
            data-testid={`aqe-split-${target.ord}-repeat-preset-${preset}`}
            aria-pressed={repeatPauseSeconds === preset ? "true" : "false"}
            onclick={() => applyValue(preset)}
          >
            {formatRepeatPauseSeconds(preset)}
          </button>
        {/each}
      </div>
    </div>
  {/if}
</span>
