import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  disposeEditorRuntime,
  initializeEditorRuntime,
  scan,
} from "../src/editor-inline/runtime.js";
import type { EditorRuntimeConfig } from "../src/editor-inline/types.js";
import {
  bridgeCommands,
  muteConsole,
  renderFields,
} from "./editor-inline.integration.helpers.js";

describe("editor inline Compress Audio source metadata", () => {
  let restoreConsole: () => void;

  beforeEach(() => {
    restoreConsole = muteConsole();
    renderFields();
  });

  afterEach(() => {
    disposeEditorRuntime();
    restoreConsole();
    vi.restoreAllMocks();
  });

  it("requests source metadata only after Advanced opens", async () => {
    mountEditor();

    const popover = await openCompressAudioSplit();
    expect(bridgeCommands()).not.toContain("aqe:source-metadata");
    expect(window.__aqePopPendingSourceMetadataRequest?.()).toBeNull();
    expect(popover).not.toHaveTextContent("Loading source info...");
    expect(popover).not.toHaveTextContent("Current: 128 kbps, 44100 Hz, channels 2, size 2.3 MB (2,412,553 bytes)");

    openAdvanced(popover);
    await Promise.resolve();

    expect(bridgeCommands()).toContain("aqe:source-metadata");
    expect(popover).toHaveTextContent("Loading source info...");
    const request = window.__aqePopPendingSourceMetadataRequest?.();
    expect(request).toMatchObject({
      fieldOrd: 0,
      sourceFilename: "clip one.mp3",
    });

    window.__aqeReceiveSourceMetadataResponse?.({
      requestId: request!.requestId,
      ok: true,
      metadata: { bitRate: 128000, sampleRate: 44100, channels: 2, fileSizeBytes: 2412553 },
    });
    await flushAsync();

    expect(popover).toHaveTextContent("Current: 128 kbps, 44100 Hz, channels 2, size 2.3 MB (2,412,553 bytes)");
  });

  it("shows a non-blocking source metadata error", async () => {
    mountEditor();

    const popover = await openCompressAudioSplit();
    openAdvanced(popover);
    await Promise.resolve();

    const request = window.__aqePopPendingSourceMetadataRequest?.();
    window.__aqeReceiveSourceMetadataResponse?.({
      requestId: request!.requestId,
      ok: false,
      error: "Could not inspect source info.",
    });
    await flushAsync();

    expect(popover).toHaveTextContent("Could not inspect source info.");
    expect(
      popover.querySelector('[data-testid="aqe-split-0-reduce-size-size-reduction-bitrate-kbps"]'),
    ).not.toBeNull();
  });

  it("does not request source metadata for direct Compress Audio clicks", async () => {
    mountEditor();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-button-0-reduce-size"]')!.click();

    expect(bridgeCommands()).toContain("aqe:command-payload");
    expect(bridgeCommands()).not.toContain("aqe:source-metadata");
    expect(window.__aqePopPendingSourceMetadataRequest?.()).toBeNull();
    expect(window.__aqePendingCommandPayload).toMatchObject({
      command: "aqe:reduce-size",
      fieldOrd: 0,
    });
  });

  it("has no source metadata request path when Compress Audio is hidden", async () => {
    mountEditor({
      visibleEditorButtons: ["aqe:slower"],
    });

    expect(document.querySelector('[data-testid="aqe-button-0-reduce-size"]')).toBeNull();
    expect(document.querySelector('[data-testid="aqe-split-0-reduce-size-menu"]')).toBeNull();
    expect(bridgeCommands()).not.toContain("aqe:source-metadata");
    expect(window.__aqePopPendingSourceMetadataRequest?.()).toBeNull();
  });
});

function mountEditor(overrides: Partial<EditorRuntimeConfig> = {}): void {
  const config: EditorRuntimeConfig = {
    audioFieldIndices: [0],
    audioFieldSources: { 0: "clip one.mp3" },
    splitButtonDefaults: {
      denoiseAlgorithm: "standard",
      pauseAggressiveness: "normal",
      repeatPauseSeconds: 0,
      sizeReductionMode: "normal",
      sizeReductionBitrateKbps: 64,
      sizeReductionSampleRateHz: 32000,
      sizeReductionChannels: 1,
      speedStep: 1.5,
      volumeStepDb: 15,
    },
    ...overrides,
  };
  initializeEditorRuntime(config);
  scan(config);
}

async function openCompressAudioSplit(): Promise<HTMLElement> {
  document.querySelector<HTMLButtonElement>('[data-testid="aqe-split-0-reduce-size-menu"]')!.click();
  await Promise.resolve();
  return document.querySelector<HTMLElement>('[data-testid="aqe-split-0-reduce-size-popover"]')!;
}

function openAdvanced(popover: HTMLElement): void {
  const advanced = popover.querySelector<HTMLDetailsElement>(
    '[data-testid="aqe-split-0-reduce-size-size-reduction-advanced-params"]',
  )!;
  advanced.open = true;
  advanced.dispatchEvent(new Event("toggle", { bubbles: true }));
}

async function flushAsync(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
}
