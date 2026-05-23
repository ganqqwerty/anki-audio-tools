/// <reference types="node" />

import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, relative } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();
const sourceRoot = join(projectRoot, "src");

const frontendAreas = [
  { name: "settings", prefix: "src/settings/" },
  { name: "editor", prefix: "src/editor-inline/" },
  { name: "batch", prefix: "src/batch/" },
] as const;

const lineLimitAllowlist = new Map<string, number>([
  ["src/editor-inline/EditorControls.svelte", 390],
  ["src/editor-inline/SplitButton.svelte", 450],
  ["src/editor-inline/SplitValueOptions.svelte", 380],
  ["src/lib/i18n.ts", 320],
]);

const exportCountAllowlist = new Map<string, number>([
  ["src/editor-inline/actions.ts", 60],
]);

const querySelectorAllowlist = new Set([
  "src/editor-inline/actions.ts",
  "src/editor-inline/control-actions.ts",
  "src/editor-inline/dom-selectors.ts",
  "src/editor-inline/field-controller.ts",
  "src/editor-inline/graph-actions.ts",
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
  "__aqeHistoryAvailabilityByField",
  "__aqeLastCursorIntent",
  "__aqeLastPlaybackRequest",
  "__aqePendingCommandPayload",
  "__aqePendingGraphRedrawField",
  "__aqePendingGraphRedrawSource",
  "__aqePendingPlaybackRequest",
  "__aqeSplitButtonStates",
]);

describe("frontend architecture guardrails", () => {
  it("excludes generated frontend files from hand-maintained file checks", () => {
    expect(isHandMaintainedFrontendFile("src/lib/generated/contracts.ts")).toBe(false);
    expect(isHandMaintainedFrontendFile("../addon/anki_audio_quick_editor/templates/editor/bundle.js")).toBe(false);
    expect(isHandMaintainedFrontendFile("src/editor-inline/actions.ts")).toBe(true);
  });

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
      if (/\bpycmd\s*\(/.test(source) && ![
        "src/lib/bridge.ts",
        "src/editor-inline/bridge.ts",
        "src/batch/bridge.ts",
      ].includes(relPath)) {
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
      if (/\.(play|pause|load|currentTime)\b/.test(withoutStringLiterals(source)) && !audioElementAllowlist.has(relPath)) {
        offenders.push(`${relPath}: audio element operation`);
      }
    }

    expect(offenders).toEqual([]);
  });

  it("keeps persisted settings UI and per-field editor split state separated", () => {
    const offenders = productionFiles()
      .map((path) => ({
        relPath: toRelPath(path),
        source: readFileSync(path, "utf-8"),
      }))
      .filter(({ relPath, source }) => {
        if (relPath.startsWith("src/settings/")) {
          return /from\s+["']\.\.\/editor-inline\//.test(source) || /from\s+["']\.\.\/\.\.\/editor-inline\//.test(source);
        }
        if (relPath.startsWith("src/editor-inline/")) {
          return /from\s+["']\.\.\/settings\//.test(source) || /from\s+["']\.\.\/\.\.\/settings\//.test(source);
        }
        return false;
      })
      .map(({ relPath }) => relPath);

    expect(offenders).toEqual([]);
  });

  it("keeps settings, editor, and batch frontends independent except shared lib imports", () => {
    const offenders = frontendArchitectureFiles()
      .map((path) => ({ relPath: toRelPath(path), source: readFileSync(path, "utf-8") }))
      .flatMap(({ relPath, source }) => forbiddenFrontendImports(relPath, source));

    expect(offenders).toEqual([]);
  });

  it("keeps shared lib modules independent from feature frontends", () => {
    const offenders = frontendArchitectureFiles()
      .map((path) => ({ relPath: toRelPath(path), source: readFileSync(path, "utf-8") }))
      .filter(({ relPath, source }) => relPath.startsWith("src/lib/") && importsFeatureFrontend(source))
      .map(({ relPath }) => relPath);

    expect(offenders).toEqual([]);
  });

  it("keeps batch and editor window contracts separated", () => {
    const offenders = frontendArchitectureFiles()
      .map((path) => ({ relPath: toRelPath(path), source: withoutComments(readFileSync(path, "utf-8")) }))
      .filter(({ relPath, source }) => {
        if (relPath.startsWith("src/batch/")) return /__aqe|__AQE_EDITOR_CONFIG__/.test(source);
        if (relPath.startsWith("src/editor-inline/")) return /__AQE_BATCH_INITIAL_STATE__|onBatch/.test(source);
        return false;
      })
      .map(({ relPath }) => relPath);

    expect(offenders).toEqual([]);
  });

  it("keeps settings and batch bridge commands on the shared JSON envelope", () => {
    const legacyPrefixes = /settings_save:|settings_cancel|settings_reset_defaults|async_cmd:|copy_support_report:|batch_start:|batch_cancel|batch_close|batch_copy_log|frontend_log:/;
    const offenders = frontendArchitectureFiles()
      .map((path) => ({ relPath: toRelPath(path), source: withoutComments(readFileSync(path, "utf-8")) }))
      .filter(({ relPath }) => relPath.startsWith("src/lib/") || relPath.startsWith("src/batch/"))
      .filter(({ source }) => legacyPrefixes.test(source))
      .map(({ relPath }) => relPath);

    expect(offenders).toEqual([]);
  });

  it("does not keep the unused frontend utility residue around", () => {
    expect(existsSync(join(sourceRoot, "lib", "utils.ts"))).toBe(false);
  });
});

function frontendArchitectureFiles(): string[] {
  return walk(sourceRoot)
    .filter((path) => /\.(svelte|ts)$/.test(path))
    .filter((path) => isHandMaintainedFrontendFile(toRelPath(path)));
}

function productionFiles(): string[] {
  return walk(sourceRoot)
    .filter((path) => /\.(svelte|ts)$/.test(path))
    .filter((path) => isHandMaintainedFrontendFile(toRelPath(path)))
    .filter((path) => !path.endsWith("/main.ts"));
}

function isHandMaintainedFrontendFile(relPath: string): boolean {
  return ![
    /^src\/lib\/generated\//,
    /^\.\.\/addon\/anki_audio_quick_editor\/templates\//,
  ].some((pattern) => pattern.test(relPath));
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

function forbiddenFrontendImports(relPath: string, source: string): string[] {
  const owner = frontendAreas.find((area) => relPath.startsWith(area.prefix));
  if (!owner) return [];
  return frontendAreas
    .filter((area) => area.name !== owner.name)
    .filter((area) => importsFrontendArea(source, area.prefix))
    .map((area) => `${relPath}: imports ${area.prefix}`);
}

function importsFeatureFrontend(source: string): boolean {
  return frontendAreas.some((area) => importsFrontendArea(source, area.prefix));
}

function importsFrontendArea(source: string, prefix: string): boolean {
  const imports = Array.from(
    source.matchAll(/\bfrom\s+["']([^"']+)["']|import\s+["']([^"']+)["']/g),
    (match) => match[1] ?? match[2] ?? "",
  );
  const areaName = prefix.slice("src/".length, -1);
  return imports.some((specifier) => {
    if (specifier.startsWith("$lib/")) return false;
    if (specifier.startsWith(`../${areaName}/`) || specifier.startsWith(`../../${areaName}/`)) return true;
    return specifier.includes(`/${areaName}/`);
  });
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

function withoutStringLiterals(source: string): string {
  return source.replaceAll(/(["'`])(?:\\[\s\S]|(?!\1)[^\\])*\1/g, "\"\"");
}
