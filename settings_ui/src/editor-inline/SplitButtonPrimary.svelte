<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import type { CommandIconName } from "../lib/icon-types.js";

  import EditorCommandIcon from "./EditorCommandIcon.svelte";

  import type { EditorButtonDisplayMode } from "../lib/editor-toolbar-buttons.js";
  import { EditorButtonMode } from "../lib/types.js";

  const {
    ariaLabel,
    activeIcon,
    command,
    disabled = false,
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
    displayMode: EditorButtonDisplayMode;
    icon: CommandIconName;
    label: string;
    onClick: () => void;
    ord: number;
    primaryClass: string;
    slug: string;
    title: string;
  } = $props();
</script>

<AqeTooltip>
  {#snippet trigger({ props })}
    <button
      {...props}
      type="button"
      class:aqe-icon-only={displayMode === EditorButtonMode.Icon}
      class={`${primaryClass} aqe-tooltip-target`}
      data-aqe-command={command}
      data-aqe-button-state={command === "aqe:play" ? "play" : command === "aqe:analyze" ? "graph" : "default"}
      data-aqe-tooltip-content={title}
      data-testid={`aqe-button-${ord}-${slug}`}
      {disabled}
      aria-label={ariaLabel}
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
  {/snippet}
</AqeTooltip>
