<script lang="ts">
  import { Popover } from "bits-ui";
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { buttonTooltipContent } from "../lib/disabled-tooltip.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import PlayAutoAdvanceControls from "./PlayAutoAdvanceControls.svelte";
  import { openEditorExternalLink } from "./external-links.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { setRepeatEnabledForOrd, setRepeatPauseSecondsForOrd, send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import { visualizerForOrd } from "./dom-selectors.js";
  import { updateEditorRuntimeConfig } from "./editor-runtime-config.js";
  import {
    formatRepeatPauseSeconds,
    getSplitButtonState,
    promoteSplitDefaultsForField,
    REPEAT_PAUSE_STATE_CHANGED_EVENT,
    setChorusingAutoAdvanceForField,
    setChorusingRepeatCountForField,
    type RepeatPauseStateChangedDetail,
    setRepeatPauseSecondsForField,
  } from "./split-button-state.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";
  import { readFieldState } from "./field-state-store.js";
  import PlayRepeatControls from "./PlayRepeatControls.svelte";
  const { button, displayMode, repeatDefault, target }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
    repeatDefault: boolean;
    target: FieldTarget;
  } = $props();
  let open = $state(false);
  let pressed = $state(false);
  let repeatPauseSeconds = $state(0);
  let autoAdvance = $state(false);
  let autoAdvanceRepeats = $state(3);
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
  const primaryTooltip = $derived(buttonTooltipContent(button.label, title));
  const repeatTooltip = $derived(buttonTooltipContent(t("editor.repeat.label"), t("editor.repeat.title")));
  const playRunTooltip = $derived(buttonTooltipContent(t("editor.play.play_audio"), t("editor.command.play.title")));
  const autoAdvanceDisabled = $derived(!pressed);
  const effectiveAutoAdvance = $derived(pressed && autoAdvance);
  function close(): void {
    open = false;
  }
  function syncRepeatState(): void {
    pressed = visualizerForOrd(target.ord) ? readFieldState(target.ord).playback.repeat : repeatDefault;
    const state = getSplitButtonState(target.ord);
    repeatPauseSeconds = state.repeatPauseSeconds;
    autoAdvance = state.chorusingAutoAdvance;
    autoAdvanceRepeats = state.chorusingRepeatCount;
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
  function applyAutoAdvance(value: boolean): void {
    if (!pressed) return;
    defaultSaved = false;
    autoAdvance = setChorusingAutoAdvanceForField(target.ord, value).chorusingAutoAdvance;
  }
  function applyAutoAdvanceRepeats(value: number): void {
    if (!pressed) return;
    defaultSaved = false;
    autoAdvanceRepeats = setChorusingRepeatCountForField(target.ord, value).chorusingRepeatCount;
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
        chorusingAutoAdvanceByDefault: effectiveAutoAdvance,
        chorusingAutoAdvanceRepeats: autoAdvanceRepeats,
        repeatPauseSeconds,
        repeatPlaybackByDefault: pressed,
      },
      fieldOrd: target.ord,
    };
    sendSplitDefaultSaveRequest(request);
    updateEditorRuntimeConfig({ repeatPlaybackByDefault: pressed });
    const promoted = promoteSplitDefaultsForField(target.ord, request.defaults);
    repeatPauseSeconds = promoted.repeatPauseSeconds;
    autoAdvance = promoted.chorusingAutoAdvance;
    autoAdvanceRepeats = promoted.chorusingRepeatCount;
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
    playSelection = Boolean(visualizer && readFieldState(target.ord).selection.active);
    const handleRepeatPauseStateChanged = (event: Event): void => {
      const detail = (event as CustomEvent<RepeatPauseStateChangedDetail>).detail;
      if (detail?.ord !== target.ord) return;
      repeatPauseSeconds = detail.state.repeatPauseSeconds;
    };
    let observer: MutationObserver | null = null;
    if (visualizer) {
      observer = new MutationObserver(() => {
        playSelection = readFieldState(target.ord).selection.active;
        repeatPauseSeconds = getSplitButtonState(target.ord).repeatPauseSeconds;
      });
      observer.observe(visualizer, {
        attributes: true,
        attributeFilter: ["data-repeat-pause-seconds", "data-selection-active", "data-selection-draft-active"],
      });
    }
    window.addEventListener(REPEAT_PAUSE_STATE_CHANGED_EVENT, handleRepeatPauseStateChanged);
    return () => {
      observer?.disconnect();
      window.removeEventListener(REPEAT_PAUSE_STATE_CHANGED_EVENT, handleRepeatPauseStateChanged);
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>
<Popover.Root open={open} onOpenChange={onOpenChange}>
  <span class="aqe-split-button aqe-play-split-button">
    <AqeTooltip>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
          class="aqe-button aqe-split-primary aqe-tooltip-target"
          data-aqe-command={button.command}
          data-aqe-button-state="play"
          data-aqe-enabled-title={primaryTooltip}
          data-aqe-tooltip-content={primaryTooltip}
          data-testid={`aqe-button-${target.ord}-play`}
          aria-label={primaryTooltip}
          onmousedown={(event) => event.preventDefault()}
          onclick={dispatchPrimary}
        >
          {#if displayMode === EditorButtonMode.Icon}
            <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
            {#if button.activeIcon}
              <EditorCommandIcon className="aqe-button-icon-active" icon={button.activeIcon} />
            {/if}
          {/if}
          <span class="aqe-button-label">{button.label}</span>
        </button>
      {/snippet}
    </AqeTooltip>
    <Popover.Trigger
      class="aqe-button aqe-icon-only aqe-split-menu-button"
      data-aqe-tooltip-content={menuTitle}
      data-testid={`aqe-split-${target.ord}-play-menu`}
      aria-label={menuTitle}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-ui-root aqe-split-popover aqe-play-split-popover"
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
        {t("editor.play.description")}
        <a
          class="aqe-split-video-link"
          href={PRODUCT_LINKS.editorVideos.playback}
          onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.playback)}
          target="_blank"
          rel="noopener noreferrer"
        >
          {t("links.see_video")}
        </a>
      </p>
      <AqeTooltip>
        {#snippet trigger({ props })}
          <button
            {...props}
            type="button"
            class="aqe-button aqe-repeat-button aqe-repeat-toggle-button aqe-tooltip-target"
            data-aqe-button-state={pressed ? "active" : "default"}
            data-aqe-tooltip-content={repeatTooltip}
            data-testid={`aqe-repeat-${target.ord}`}
            aria-label={repeatTooltip}
            aria-pressed={pressed ? "true" : "false"}
            onmousedown={(event) => event.preventDefault()}
            onclick={toggleRepeat}
          >
            <EditorCommandIcon icon="repeat-2" />
            <span class="aqe-button-label">{t("editor.repeat.label")}</span>
          </button>
        {/snippet}
      </AqeTooltip>
      <PlayRepeatControls
        onValueInput={applyValue}
        {repeatPauseSeconds}
        targetOrd={target.ord}
      />
      <PlayAutoAdvanceControls
        autoAdvance={effectiveAutoAdvance}
        {autoAdvanceRepeats}
        disabled={autoAdvanceDisabled}
        onAutoAdvanceChange={applyAutoAdvance}
        onRepeatsInput={applyAutoAdvanceRepeats}
        targetOrd={target.ord}
      />
      <div class="aqe-split-popover-footer">
        <AqeTooltip>
          {#snippet trigger({ props })}
            <button
              {...props}
              type="button"
              class="aqe-button aqe-split-run-button aqe-tooltip-target"
              data-aqe-tooltip-content={playRunTooltip}
              data-testid={`aqe-split-${target.ord}-play-run`}
              aria-label={playRunTooltip}
              onclick={dispatchPrimary}
            >
              {t("editor.play.play_audio")}
            </button>
          {/snippet}
        </AqeTooltip>
      </div>
    </Popover.Content>
  </span>
</Popover.Root>
