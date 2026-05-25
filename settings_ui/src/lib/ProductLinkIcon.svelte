<script lang="ts" module>
  export type ProductLinkIconName =
    | "bug"
    | "external-link"
    | "heart"
    | "idea"
    | "message"
    | "send";
</script>

<script lang="ts">
  import Bug from "@lucide/svelte/icons/bug";
  import ExternalLink from "@lucide/svelte/icons/external-link";
  import Heart from "@lucide/svelte/icons/heart";
  import Lightbulb from "@lucide/svelte/icons/lightbulb";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  import Send from "@lucide/svelte/icons/send";

  const {
    className = "",
    icon,
    size = 14,
    strokeWidth = 2,
  }: {
    className?: string;
    icon: ProductLinkIconName;
    size?: number;
    strokeWidth?: number;
  } = $props();
</script>

<span class={className} aria-hidden="true">
  {#if icon === "bug"}
    <Bug {size} {strokeWidth} />
  {:else if icon === "external-link"}
    <ExternalLink {size} {strokeWidth} />
  {:else if icon === "heart"}
    <Heart {size} {strokeWidth} />
  {:else if icon === "idea"}
    <Lightbulb {size} {strokeWidth} />
  {:else if icon === "message"}
    <MessageCircle {size} {strokeWidth} />
  {:else if icon === "send"}
    <Send {size} {strokeWidth} />
  {/if}
</span>
