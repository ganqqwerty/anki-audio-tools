<script lang="ts">
  import { Popover } from "bits-ui";
  import { onMount } from "svelte";
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { buttonTooltipContent } from "../lib/disabled-tooltip.js";
  import { t } from "../lib/i18n.js";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";
  import UnitNumberInput from "../lib/UnitNumberInput.svelte";
  import type { ButtonSpec, FieldTarget } from "./types.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import { send } from "./actions.js";
  import { sendSplitDefaultSaveRequest } from "./bridge.js";
  import {
    buildSplitDefaultSaveRequest,
    getSplitButtonState,
    promoteSplitDefaultsForField,
    setChorusingAutoAdvanceForField,
    setChorusingPauseSecondsForField,
    setChorusingRepeatCountForField,
  } from "./split-button-state.js";

  const { button, displayMode, target }: {
    button: ButtonSpec;
    displayMode: EditorButtonDisplayMode;
    target: FieldTarget;
  } = $props();

  let open = $state(false);
  let chorusingPauseSeconds = $state(0);
  let chorusingAutoAdvance = $state(false);
  let chorusingRepeatCount = $state(3);
  let defaultSaved = $state(false);
  let defaultSavedTimer: number | undefined;

  const primaryTooltip = $derived(buttonTooltipContent(button.label, button.title));
  const menuTitle = $derived(t("editor.chorusing.menu_title"));

  function syncState(): void {
    const state = getSplitButtonState(target.ord);
    chorusingPauseSeconds = state.chorusingPauseSeconds;
    chorusingAutoAdvance = state.chorusingAutoAdvance;
    chorusingRepeatCount = state.chorusingRepeatCount;
  }

  function onOpenChange(nextOpen: boolean): void {
    if (nextOpen) syncState();
    open = nextOpen;
  }

  function dispatchPrimary(): void {
    open = false;
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
    const request = buildSplitDefaultSaveRequest("aqe:chorusing-practice", target.ord);
    sendSplitDefaultSaveRequest(request);
    const nextState = promoteSplitDefaultsForField(target.ord, request.defaults);
    chorusingPauseSeconds = nextState.chorusingPauseSeconds;
    chorusingAutoAdvance = nextState.chorusingAutoAdvance;
    chorusingRepeatCount = nextState.chorusingRepeatCount;
    showDefaultSaved();
  }

  onMount(() => {
    syncState();
    return () => {
      if (defaultSavedTimer !== undefined) window.clearTimeout(defaultSavedTimer);
    };
  });
</script>

<Popover.Root open={open} onOpenChange={onOpenChange}>
  <span class="aqe-split-button">
    <AqeTooltip>
      {#snippet trigger({ props })}
        <button
          {...props}
          type="button"
          class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
          class="aqe-button aqe-split-primary aqe-tooltip-target"
          data-aqe-command={button.command}
          data-aqe-button-state="default"
          data-aqe-enabled-title={primaryTooltip}
          data-aqe-tooltip-content={primaryTooltip}
          data-testid={`aqe-button-${target.ord}-chorusing-practice`}
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
      data-testid={`aqe-split-${target.ord}-chorusing-practice-menu`}
      aria-label={menuTitle}
    >
      <EditorCommandIcon icon="chevron-down" />
      <span class="aqe-button-label">{t("editor.split.options")}</span>
    </Popover.Trigger>
    <Popover.Content
      align="center"
      arrowPadding={14}
      class="aqe-ui-root aqe-split-popover aqe-chorusing-split-popover"
      collisionPadding={8}
      data-testid={`aqe-split-${target.ord}-chorusing-popover`}
      onCloseAutoFocus={(event) => event.preventDefault()}
      side="bottom"
      sideOffset={4}
      strategy="fixed"
      trapFocus={false}
    >
      <Popover.Arrow
        class="aqe-split-popover-arrow"
        data-testid={`aqe-split-${target.ord}-chorusing-arrow`}
        height={8}
        width={16}
      />
      <div class="aqe-split-popover-header aqe-split-popover-header-with-action">
        <span class="aqe-split-popover-title">
          <strong>{t("editor.command.chorusing_practice.label")}</strong>
        </span>
        <SplitDefaultSaveButton
          onSave={saveCurrentDefaults}
          saved={defaultSaved}
          testId={`aqe-split-${target.ord}-chorusing-save-default`}
        />
      </div>
      <p class="aqe-split-popover-description">{t("editor.chorusing.auto_advance_description")}</p>
      <div class="aqe-split-popover-header">
        <span>{t("editor.chorusing.pause_between_repeats")}</span>
        <UnitNumberInput
          inputClass="aqe-split-value-input"
          testId={`aqe-split-${target.ord}-chorusing-pause-seconds`}
          min="0"
          max="10"
          step="0.1"
          unit="s"
          value={chorusingPauseSeconds}
          ariaLabel={t("editor.chorusing.pause_between_repeats")}
          onValueInput={(value) => {
            const state = setChorusingPauseSecondsForField(target.ord, value);
            chorusingPauseSeconds = state.chorusingPauseSeconds;
            defaultSaved = false;
          }}
        />
      </div>
      <label class="aqe-split-checkbox-row">
        <input
          type="checkbox"
          checked={chorusingAutoAdvance}
          data-testid={`aqe-split-${target.ord}-chorusing-auto-advance`}
          onchange={(event) => {
            const input = event.currentTarget as HTMLInputElement;
            const state = setChorusingAutoAdvanceForField(target.ord, input.checked);
            chorusingAutoAdvance = state.chorusingAutoAdvance;
            defaultSaved = false;
          }}
        />
        <span>{t("editor.chorusing.auto_advance")}</span>
      </label>
      <div class="aqe-split-popover-header">
        <span>{t("editor.chorusing.repeat_count")}</span>
        <UnitNumberInput
          inputClass="aqe-split-value-input"
          testId={`aqe-split-${target.ord}-chorusing-repeat-count`}
          min="1"
          max="20"
          step="1"
          unit="x"
          value={chorusingRepeatCount}
          ariaLabel={t("editor.chorusing.repeat_count")}
          onValueInput={(value) => {
            const state = setChorusingRepeatCountForField(target.ord, value);
            chorusingRepeatCount = state.chorusingRepeatCount;
            defaultSaved = false;
          }}
        />
      </div>
    </Popover.Content>
  </span>
</Popover.Root>
