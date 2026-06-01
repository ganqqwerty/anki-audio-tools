<script lang="ts">
  import AqeTooltip from "../lib/AqeTooltip.svelte";
  import { t } from "../lib/i18n.js";
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import { openEditorExternalLink } from "./external-links.js";
  import GraphSplitOptions from "./GraphSplitOptions.svelte";
  import SplitDefaultSaveButton from "./SplitDefaultSaveButton.svelte";
  import type {
    GraphRecordingCondition,
    GraphSmoothness,
    GraphVoiceLock,
    GraphVoiceRange,
  } from "./graph-settings.js";

  const {
    connectShortDropoutsMs,
    menuLabel,
    menuSlug,
    onConnectShortDropouts,
    onRecordingCondition,
    onRun,
    onSaveDefault,
    onSmoothness,
    onVoiceLock,
    onVoiceRange,
    recordingCondition,
    saved,
    smoothness,
    targetOrd,
    voiceLock,
    voiceRange,
  }: {
    connectShortDropoutsMs: number;
    menuLabel: string;
    menuSlug: string;
    onConnectShortDropouts: (value: number) => void;
    onRecordingCondition: (value: GraphRecordingCondition) => void;
    onRun: () => void;
    onSaveDefault: () => void;
    onSmoothness: (value: GraphSmoothness) => void;
    onVoiceLock: (value: GraphVoiceLock) => void;
    onVoiceRange: (value: GraphVoiceRange) => void;
    recordingCondition: GraphRecordingCondition;
    saved: boolean;
    smoothness: GraphSmoothness;
    targetOrd: number;
    voiceLock: GraphVoiceLock;
    voiceRange: GraphVoiceRange;
  } = $props();
</script>

<div class="aqe-split-popover-header aqe-split-popover-header-with-action">
  <span class="aqe-split-popover-title">
    <strong>{menuLabel}</strong>
  </span>
  <SplitDefaultSaveButton
    onSave={onSaveDefault}
    {saved}
    testId={`aqe-split-${targetOrd}-${menuSlug}-save-default`}
  />
</div>
<p class="aqe-split-popover-description">
  {t("editor.split.description_graph")}
  <a
    class="aqe-split-video-link"
    href={PRODUCT_LINKS.editorVideos.graph}
    onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.graph)}
    target="_blank"
    rel="noopener noreferrer"
  >
    {t("links.see_video")}
  </a>
</p>
<GraphSplitOptions
  {connectShortDropoutsMs}
  onConnectShortDropouts={onConnectShortDropouts}
  onRecordingCondition={onRecordingCondition}
  onSmoothness={onSmoothness}
  onVoiceLock={onVoiceLock}
  onVoiceRange={onVoiceRange}
  {recordingCondition}
  slug={menuSlug}
  {smoothness}
  {targetOrd}
  {voiceLock}
  {voiceRange}
/>
<div class="aqe-split-popover-footer">
  <AqeTooltip>
    {#snippet trigger({ props })}
      <button
        {...props}
        type="button"
        class="aqe-button aqe-split-run-button aqe-tooltip-target"
        data-aqe-tooltip-content={t("editor.command.graph.title")}
        data-testid={`aqe-split-${targetOrd}-${menuSlug}-run`}
        aria-label={t("editor.command.graph.title")}
        onclick={onRun}
      >
        {t("editor.split.draw")}
      </button>
    {/snippet}
  </AqeTooltip>
</div>
