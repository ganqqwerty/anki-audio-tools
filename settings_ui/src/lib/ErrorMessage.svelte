<script lang="ts">
  import { errorHelpUrl } from "./error-links.js";
  import { isUserFacingError, type ErrorDisplayValue } from "./user-facing-error.js";

  let {
    error,
    className = "",
    testId = undefined,
  }: {
    error: ErrorDisplayValue;
    className?: string;
    testId?: string;
  } = $props();

  const coded = $derived(isUserFacingError(error) ? error : null);
</script>

<span class={className} data-testid={testId}>
  {#if coded}
    <span class="error-code">{coded.code}:</span>
    {" "}{coded.message}
    <a class="error-help-link" href={errorHelpUrl(coded.code)} target="_blank" rel="noopener noreferrer">Help</a>
  {:else}
    {error}
  {/if}
</span>
