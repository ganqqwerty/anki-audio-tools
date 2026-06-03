<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { tooltipWithDisabledClarification } from "../lib/disabled-tooltip.js";
  import type { CommandIconName } from "../lib/icon-types.js";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";

  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";

  const {
    ariaLabel,
    activeIcon,
    command,
    disabled = false,
    disabledReason,
    displayMode,
    icon,
    label,
    primaryClass,
    slug,
    title,
    onClick,
    ord,
  }: {
    ariaLabel: string;
    activeIcon?: CommandIconName | undefined;
    command: string;
    disabled?: boolean;
    disabledReason?: string | undefined;
    displayMode: EditorButtonDisplayMode;
    icon: CommandIconName;
    label: string;
    onClick: () => void;
    ord: number;
    primaryClass: string;
    slug: string;
    title: string;
  } = $props();

  const tooltipTitle = $derived(tooltipWithDisabledClarification(title, disabled ? disabledReason : undefined));
</script>

<AqeTooltip>
  {#snippet trigger({ props })}
    <span
      {...props}
      class="aqe-button-tooltip-target aqe-tooltip-target"
      data-aqe-tooltip-content={tooltipTitle}
    >
      <button
        type="button"
        class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
        class={primaryClass}
        data-aqe-command={command}
        data-aqe-button-state={command === "aqe:play" ? "play" : command === "aqe:analyze" ? "graph" : "default"}
        data-aqe-disabled-title={disabledReason}
        data-aqe-enabled-title={title}
        data-aqe-tooltip-content={tooltipTitle}
        data-testid={`aqe-button-${ord}-${slug}`}
        {disabled}
        aria-label={tooltipTitle || ariaLabel}
        onmousedown={(event) => event.preventDefault()}
        onclick={onClick}
      >
        {#if displayMode === EditorButtonMode.Icon}
          <EditorCommandIcon className="aqe-button-icon-default" {icon} />
          {#if activeIcon}
            <EditorCommandIcon className="aqe-button-icon-active" icon={activeIcon} />
          {/if}
        {/if}
        <span class="aqe-button-label">{label}</span>
      </button>
    </span>
  {/snippet}
</AqeTooltip>
