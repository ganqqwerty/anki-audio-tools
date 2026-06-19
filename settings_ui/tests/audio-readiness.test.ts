import { describe, expect, it } from "vitest";

import {
  classifyHtmlAudioReadiness,
  type HtmlAudioReadinessInput,
} from "../src/editor-inline/audio-readiness.js";

const baseInput: HtmlAudioReadinessInput = {
  available: false,
  failureReason: "",
  hasSrc: true,
  present: true,
  readyState: 0,
};

describe("HTML audio readiness", () => {
  it("reports missing audio element", () => {
    expect(classifyHtmlAudioReadiness({
      ...baseInput,
      present: false,
    })).toMatchObject({
      failed: true,
      reason: "audio_element_missing",
      state: "missing",
      transient: false,
    });
  });

  it("reports missing source as transient", () => {
    expect(classifyHtmlAudioReadiness({
      ...baseInput,
      hasSrc: false,
    })).toMatchObject({
      failed: false,
      reason: "audio_src_missing",
      state: "source_missing",
      transient: true,
    });
  });

  it("reports metadata loading before loadedmetadata", () => {
    expect(classifyHtmlAudioReadiness({
      ...baseInput,
      readyState: 0,
    })).toMatchObject({
      failed: false,
      reason: "audio_metadata_loading",
      state: "loading_metadata",
      transient: true,
    });
  });

  it("reports ready after metadata is available", () => {
    expect(classifyHtmlAudioReadiness({
      ...baseInput,
      available: true,
      readyState: 1,
    })).toMatchObject({
      ready: true,
      reason: "audio_ready",
      state: "ready",
      transient: false,
    });
  });

  it("trusts browser readyState when the internal availability flag is stale", () => {
    expect(classifyHtmlAudioReadiness({
      ...baseInput,
      available: false,
      readyState: 1,
    })).toMatchObject({
      ready: true,
      reason: "audio_ready",
      state: "ready",
      transient: false,
    });
  });

  it("reports hard audio failures", () => {
    for (const reason of ["audio_error", "audio_load_failed", "audio_seek_failed", "metadata_timeout"] as const) {
      expect(classifyHtmlAudioReadiness({
        ...baseInput,
        failureReason: reason,
      })).toMatchObject({
        failed: true,
        reason,
        state: "failed",
        transient: false,
      });
    }
  });
});
