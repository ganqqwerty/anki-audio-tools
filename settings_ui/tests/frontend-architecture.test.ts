/// <reference types="node" />

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();
const sourceRoot = join(projectRoot, "src");

const lineLimitAllowlist = new Map<string, number>([
  ["src/editor-inline/actions.ts", 800],
  ["src/editor-inline/EditorControls.svelte", 350],
]);

const exportCountAllowlist = new Map<string, number>([
  ["src/editor-inline/actions.ts", 60],
]);

const querySelectorAllowlist = new Set([
  "src/editor-inline/actions.ts",
  "src/editor-inline/dom-selectors.ts",
  "src/editor-inline/field-controller.ts",
  "src/editor-inline/runtime.ts",
]);

const requestAnimationFrameAllowlist = new Set([
  "src/editor-inline/playback-controller.ts",
  "src/editor-inline/test-contract.ts",
]);

const audioElementAllowlist = new Set([
  "src/editor-inline/audio-clock.ts",
  "src/editor-inline/playback-controller.ts",
  "src/editor-inline/test-contract.ts",
]);

const internalWindowStateNames = new Set([
  "__aqeActiveField",
  "__aqeLastCursorIntent",
  "__aqeLastPlaybackRequest",
  "__aqePendingCommandPayload",
  "__aqePendingGraphRedrawField",
  "__aqePendingPlaybackRequest",
  "__aqeSplitButtonStates",
]);

describe("frontend architecture guardrails", () => {
  it("keeps hand-maintained production frontend files below size limits or explicit temporary allowlists", () => {
    const offenders = productionFiles()
      .map((path) => {
        const relPath = toRelPath(path);
        const lines = readFileSync(path, "utf-8").trimEnd().split("\n").length;
        return { relPath, lines, limit: lineLimitFor(relPath) };
      })
      .filter(({ lines, limit }) => lines > limit);

    expect(offenders).toEqual([]);
  });

  it("keeps frontend module export counts bounded or explicitly allowlisted", () => {
    const offenders = productionFiles()
      .filter((path) => path.endsWith(".ts"))
      .map((path) => {
        const relPath = toRelPath(path);
        const exports = countExports(readFileSync(path, "utf-8"));
        return { relPath, exports, limit: exportCountAllowlist.get(relPath) ?? 25 };
      })
      .filter(({ exports, limit }) => exports > limit);

    expect(offenders).toEqual([]);
  });

  it("keeps bridge, window, selector, timer, and audio side effects in owned modules", () => {
    const offenders: string[] = [];

    for (const path of productionFiles()) {
      const relPath = toRelPath(path);
      const source = withoutComments(readFileSync(path, "utf-8"));
      if (/\bpycmd\s*\(/.test(source) && !["src/lib/bridge.ts", "src/editor-inline/bridge.ts"].includes(relPath)) {
        offenders.push(`${relPath}: pycmd`);
      }
      if (assignedPublicWindowContractNames(source).length && ![
        "src/editor-inline/runtime.ts",
        "src/editor-inline/test-contract.ts",
        "src/editor-inline/window-contract.ts",
      ].includes(relPath)) {
        offenders.push(`${relPath}: window contract assignment`);
      }
      if (/window\.__aqe[A-Za-z0-9_]*ForTest\s*=/.test(source) && relPath !== "src/editor-inline/test-contract.ts") {
        offenders.push(`${relPath}: test window contract assignment`);
      }
      if (/document\.querySelector/.test(source) && !querySelectorAllowlist.has(relPath)) {
        offenders.push(`${relPath}: document query`);
      }
      if (/requestAnimationFrame|cancelAnimationFrame/.test(source) && !requestAnimationFrameAllowlist.has(relPath)) {
        offenders.push(`${relPath}: animation frame`);
      }
      if (/\.(play|pause|load|currentTime)\b/.test(source) && !audioElementAllowlist.has(relPath)) {
        offenders.push(`${relPath}: audio element operation`);
      }
    }

    expect(offenders).toEqual([]);
  });

  it("does not keep the unused frontend utility residue around", () => {
    expect(existsSync(join(sourceRoot, "lib", "utils.ts"))).toBe(false);
  });
});

function productionFiles(): string[] {
  return walk(sourceRoot)
    .filter((path) => /\.(svelte|ts)$/.test(path))
    .filter((path) => !path.includes("/lib/generated/"))
    .filter((path) => !path.endsWith("/main.ts"));
}

function walk(root: string): string[] {
  return readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const path = join(root, entry.name);
    if (entry.isDirectory()) return walk(path);
    return [path];
  });
}

function toRelPath(path: string): string {
  return relative(projectRoot, path).replaceAll("\\", "/");
}

function lineLimitFor(relPath: string): number {
  const allowlistLimit = lineLimitAllowlist.get(relPath);
  if (allowlistLimit !== undefined) return allowlistLimit;
  if (relPath.endsWith(".svelte")) return 300;
  if (relPath.startsWith("src/editor-inline/")) return 500;
  if (relPath.startsWith("src/lib/")) return 300;
  return 500;
}

function countExports(source: string): number {
  return Array.from(source.matchAll(/^\s*export\s+(?:async\s+)?(?:function|const|let|class|interface|type|enum)\s+/gm)).length;
}

function assignedPublicWindowContractNames(source: string): string[] {
  return Array.from(source.matchAll(/window\.(__aqe[A-Za-z0-9_]+)\s*=/g), (match) => match[1] ?? "")
    .filter((name) => !internalWindowStateNames.has(name));
}

function withoutComments(source: string): string {
  return source
    .replaceAll(/\/\*[\s\S]*?\*\//g, "")
    .replaceAll(/^\s*\/\/.*$/gm, "");
}
