<script lang="ts">
  import { Tooltip } from "bits-ui";
  import type { Snippet } from "svelte";

  import { TOOLTIP_CONTENT_ATTRIBUTE } from "./rich-tooltip.js";

  type TooltipAlign = "start" | "center" | "end";
  type TooltipSide = "top" | "bottom" | "left" | "right";

  const {
    align = "center",
    content,
    disabled = false,
    side = "top",
    sideOffset = 8,
    trigger,
  }: {
    align?: TooltipAlign;
    content?: string;
    disabled?: boolean;
    side?: TooltipSide;
    sideOffset?: number;
    trigger: Snippet<[{ props: Record<string, unknown> }]>;
  } = $props();

  let triggerRef = $state<HTMLElement | null>(null);
  let observedContent = $state("");

  function syncObservedContent(): void {
    observedContent = triggerRef?.getAttribute(TOOLTIP_CONTENT_ATTRIBUTE)?.trim() ?? "";
  }

  $effect(() => {
    if (!triggerRef) {
      observedContent = "";
      return;
    }
    syncObservedContent();
    const observer = new MutationObserver(() => {
      syncObservedContent();
    });
    observer.observe(triggerRef, {
      attributeFilter: [TOOLTIP_CONTENT_ATTRIBUTE],
      attributes: true,
    });
    return () => observer.disconnect();
  });

  const resolvedContent = $derived.by(() => (content ?? observedContent).trim());
</script>

<Tooltip.Root disabled={disabled || resolvedContent.length === 0}>
  <Tooltip.Trigger bind:ref={triggerRef}>
    {#snippet child({ props })}
      {@render trigger({ props })}
    {/snippet}
  </Tooltip.Trigger>
  <Tooltip.Portal>
    <Tooltip.Content
      align={align}
      class="aqe-rich-tooltip"
      collisionPadding={8}
      side={side}
      sideOffset={sideOffset}
    >
      {resolvedContent}
    </Tooltip.Content>
  </Tooltip.Portal>
</Tooltip.Root>

<style>
  :global(.aqe-rich-tooltip) {
    background: color-mix(in srgb, var(--canvas-elevated, Canvas) 94%, var(--canvas, Canvas));
    border: 1px solid color-mix(in srgb, var(--border, ButtonBorder) 84%, transparent);
    border-radius: 8px;
    box-shadow:
      0 10px 24px rgb(0 0 0 / 18%),
      0 1px 0 rgb(255 255 255 / 14%) inset;
    color: var(--fg, CanvasText);
    font-size: 11px;
    line-height: 1.35;
    max-width: min(32ch, calc(100vw - 24px));
    padding: 6px 8px;
    pointer-events: none;
    white-space: normal;
    z-index: 12000;
  }

  :global(.aqe-rich-tooltip[data-starting-style]) {
    opacity: 0;
    transform: translateY(2px) scale(0.98);
  }

  :global(.aqe-rich-tooltip[data-ending-style]) {
    opacity: 0;
    transform: translateY(1px) scale(0.99);
  }
</style>
