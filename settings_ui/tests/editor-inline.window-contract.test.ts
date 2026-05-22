/// <reference types="node" />

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();
const runtimePath = join(projectRoot, "src", "editor-inline", "runtime.ts");
const testContractPath = join(projectRoot, "src", "editor-inline", "test-contract.ts");
const windowContractPath = join(projectRoot, "src", "editor-inline", "window-contract.ts");
const globalsPath = join(projectRoot, "src", "editor-inline", "globals.d.ts");

describe("editor inline window contract", () => {
  it("declares every installed window callback in globals.d.ts", () => {
    const installed = new Set([
      ...assignedWindowNames(readFileSync(runtimePath, "utf-8")),
      ...assignedWindowNames(readFileSync(testContractPath, "utf-8")),
      ...assignedWindowNames(readFileSync(windowContractPath, "utf-8")),
    ]);
    const declared = new Set(declaredWindowNames(readFileSync(globalsPath, "utf-8")));

    expect([...installed].sort()).toEqual([
      "__aqeEditorDispose",
      "__aqeGetCursorIntent",
      "__aqeGetCursorMs",
      "__aqeGetPlaybackRequest",
      "__aqeGraphStateForTest",
      "__aqeInstallAudioPlaybackTestDriverForTest",
      "__aqePlayAfterEdit",
      "__aqePopFrontendLog",
      "__aqePopPendingGraphAnalysisRequest",
      "__aqePopPendingRegionDeleteRequest",
      "__aqePopPendingSplitDefaultSaveRequest",
      "__aqePrepareForNewNote",
      "__aqeResetGraphAfterEdit",
      "__aqeScan",
      "__aqeSetBusy",
      "__aqeSetCursorByClientXForTest",
      "__aqeSetCursorForTest",
      "__aqeSetHistoryAvailability",
      "__aqeSetPlaybackState",
      "__aqeSetStatus",
      "__aqeSetVisualizer",
      "__aqeSetVisualizerStatus",
      "__aqeStopEditorPlayback",
    ]);
    expect([...installed].filter((name) => !declared.has(name))).toEqual([]);
  });
});

function assignedWindowNames(source: string): string[] {
  return Array.from(source.matchAll(/window\.(__aqe[A-Za-z0-9_]+)\s*=/g), (match) => match[1] ?? "");
}

function declaredWindowNames(source: string): string[] {
  return Array.from(source.matchAll(/(__aqe[A-Za-z0-9_]+)\??:/g), (match) => match[1] ?? "");
}
