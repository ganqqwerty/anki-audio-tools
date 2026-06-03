<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
  import { EditorButtonMode } from "../lib/types.js";
  import { testId } from "./commands.js";
  import { send } from "./actions.js";
  import EditorCommandIcon from "./EditorCommandIcon.svelte";
  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import type { ButtonSpec, FieldTarget } from "./types.js";

  const {
    button,
    disabled = false,
    disabledTitle,
    displayMode,
    target,
  }: {
    button: ButtonSpec;
    disabled?: boolean;
    disabledTitle?: string | undefined;
    displayMode: EditorButtonDisplayMode;
    target: FieldTarget;
  } = $props();

  const title = $derived(tooltipWithDisabledClarification(button.title, disabled ? disabledTitle : undefined));
  const buttonState = $derived(button.command === "aqe:analyze" ? "graph" : "default");
</script>

<AqeTooltip>
  {#snippet trigger({ props })}
    <span
      {...props}
      class="aqe-button-tooltip-target aqe-tooltip-target"
      data-aqe-tooltip-content={title}
    >
      <button
        type="button"
        class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
        class="aqe-button"
        data-aqe-command={button.command}
        data-aqe-button-state={buttonState}
        data-aqe-disabled-title={disabledTitle}
        data-aqe-enabled-title={button.title}
        data-testid={testId(target.ord, button.command)}
        {disabled}
        aria-label={title}
        onmousedown={(event) => event.preventDefault()}
        onclick={() => send(button.command, target.node, target.ord)}
      >
        {#if displayMode === EditorButtonMode.Icon}
          <EditorCommandIcon className="aqe-button-icon-default" icon={button.icon} />
          {#if button.activeIcon}
            <EditorCommandIcon className="aqe-button-icon-active" icon={button.activeIcon} />
          {/if}
          <span class="aqe-button-label">{button.label}</span>
        {:else}
          <span class="aqe-button-label">{button.label}</span>
        {/if}
      </button>
    </span>
  {/snippet}
</AqeTooltip>
