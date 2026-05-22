<script lang="ts">
  import { Popover } from "bits-ui";
  import { onMount } from "svelte";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { setRepeatEnabledForOrd, setRepeatPauseSecondsForOrd, send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import {
    formatRepeatPauseSeconds,
    getSplitButtonState,
    promoteSplitDefaultsForField,
    setRepeatPauseSecondsForField,
  } from "./split-button-state.js";
  import { t } from "../lib/i18n.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";
  const PRESETS = [0, 0.5, 2, 10] as const;
  const { button, repeatDefault, target }: {
    button: ButtonSpec;
    repeatDefault: boolean;
    target: FieldTarget;
  } = $props();
  let open = $state(false);
  let pressed = $state(false);
  let repeatPauseSeconds = $state(0);
  let defaultSaved = $state(false);
  let defaultSavedTimer: number | undefined;
  let playSelection = $state(false);
  const menuTitle = $derived(t("editor.play.menu_title", {
    value: t("editor.play.current_value", {
      pause: formatRepeatPauseSeconds(repeatPauseSeconds),
      repeat: pressed ? t("editor.play.repeat_on") : t("editor.play.repeat_off"),
    }),
  }));
  const title = $derived(playSelection ? t("editor.command.play.title_selected") : t("editor.command.play.title"));
  function close(): void {
    open = false;
  }
  function syncRepeatState(): void {
    const visualizer = visualizerForOrd(target.ord);
    pressed = visualizer ? visualizer.dataset.repeatEnabled === "true" : repeatDefault;
    const state = getSplitButtonState(target.ord);
    repeatPauseSeconds = state.repeatPauseSeconds;
    setRepeatPauseSecondsForOrd(target.ord, repeatPauseSeconds);
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
  }
  function onOpenChange(nextOpen: boolean): void {
    if (nextOpen) syncRepeatState();
    open = nextOpen;
  }
  onMount(() => {
    syncRepeatState();
    const visualizer = visualizerForOrd(target.ord);
    playSelection = visualizer?.dataset.selectionActive === "true";
    let observer: MutationObserver | null = null;
    if (visualizer) {
      observer = new MutationObserver(() => {
        playSelection = visualizer.dataset.selectionActive === "true";
      });
      observer.observe(visualizer, {
        attributes: true,
        attributeFilter: ["data-selection-active", "data-selection-draft-active"],
      });
    }
    return () => {
      observer?.disconnect();
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>
<Popover.Root open={open} onOpenChange={onOpenChange}>
  <span class="aqe-split-button aqe-play-split-button">
    <button
      type="button"
      class:aqe-icon-only={button.iconOnly === true}
      class="aqe-button aqe-split-primary"
      data-aqe-command={button.command}
      data-aqe-button-state="play"
      data-testid={`aqe-button-${target.ord}-play`}
      title={title}
      aria-label={title}
      onmousedown={(event) => event.preventDefault()}
      onclick={dispatchPrimary}
    >
      <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
      {#if button.activeIcon}
        <EditorCommandIcon className="aqe-button-icon-active" icon={button.activeIcon} />
      {/if}
      <span class="aqe-button-label">{button.label}</span>
    </button>
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button aqe-play-repeat-menu-button"
      data-aqe-button-state={pressed ? "active" : "default"}
      data-testid={`aqe-split-${target.ord}-play-menu`}
      title={menuTitle}
      aria-label={menuTitle}
      onmousedown={(event) => event.preventDefault()}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-split-popover aqe-play-split-popover"
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-play-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow
        class="aqe-split-popover-arrow"
        data-testid={`aqe-split-${target.ord}-play-arrow`}
        height={8}
        width={16}
      />
      <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
        <span class="aqe-split-popover-title">
          <strong>{t("editor.command.play.label")}</strong>
        </span>
        <SplitDefaultSaveButton
          onSave={saveCurrentDefaults}
          saved={defaultSaved}
          testId={`aqe-split-${target.ord}-play-save-default`}
        />
      </div>
      <p class="aqe-split-popover-description">
        {t("editor.play.description", {
          pause: formatRepeatPauseSeconds(repeatPauseSeconds),
          repeat: pressed ? t("editor.play.repeat_on") : t("editor.play.repeat_off"),
        })}
      </p>
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
        <span style="align-items: center; display: inline-flex; gap: 4px; justify-content: flex-end;">
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
          <span style="font-size: 11px; white-space: nowrap;"> s</span>
        </span>
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
      <div class="aqe-split-popover-footer">
        <button
          type="button"
          class="aqe-button aqe-split-run-button"
          data-testid={`aqe-split-${target.ord}-play-run`}
          title={t("editor.split.run_title", { label: t("editor.command.play.label") })}
          aria-label={t("editor.split.run_title", { label: t("editor.command.play.label") })}
          onclick={dispatchPrimary}
        >
          {t("editor.split.run")}
        </button>
      </div>
    </Popover.Content>
  </span>
</Popover.Root>
