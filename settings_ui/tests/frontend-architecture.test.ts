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
  ["src/batch/BatchControls.svelte", 335],
  ["src/editor-inline/EditorControls.svelte", 440],
  ["src/editor-inline/GraphVisualizer.svelte", 312],
  ["src/editor-inline/SplitButton.svelte", 500],
  ["src/editor-inline/SplitValueOptions.svelte", 398],
  ["src/lib/editor-toolbar-buttons.ts", 345],
  ["src/lib/i18n.ts", 370],
  ["src/lib/PauseAdvancedParamsFields.svelte", 302],
  ["src/settings/SettingsApp.svelte", 304],
  ["src/settings/ToolbarPanelSettingsFields.svelte", 316],
  ["src/settings/ToolbarVisibilitySettings.svelte", 386],
]);

const exportCountAllowlist = new Map<string, number>([
  ["src/editor-inline/actions.ts", 60],
  ["src/lib/audio-operation-parameters.ts", 37],
]);

const querySelectorAllowlist = new Set([
  "src/editor-inline/actions.ts",
  "src/editor-inline/control-actions.ts",
  "src/editor-inline/dom-selectors.ts",
  "src/editor-inline/field-controller.ts",
  "src/editor-inline/graph-actions.ts",
  "src/editor-inline/html-audio-session-audio-element.ts",
  "src/editor-inline/html-audio-session-controller.ts",
  "src/editor-inline/learner-recording-playback.ts",
  "src/editor-inline/runtime.ts",
]);

const requestAnimationFrameAllowlist = new Set([
  "src/editor-inline/html-audio-session-controller.ts",
  "src/editor-inline/playback-controller.ts",
  "src/editor-inline/playback-controller-frame.ts",
  "src/editor-inline/learner-recording-playback.ts",
  "src/editor-inline/recording-actions.ts",
  "src/editor-inline/recording-actions-state.ts",
  "src/editor-inline/test-contract.ts",
]);

const audioElementAllowlist = new Set([
  "src/editor-inline/audio-clock.ts",
  "src/editor-inline/html-audio-session-audio-element.ts",
  "src/editor-inline/learner-recording-playback.ts",
  "src/editor-inline/playback-controller.ts",
  "src/editor-inline/playback-controller-audio.ts",
  "src/editor-inline/test-contract.ts",
]);

const internalWindowStateNames = new Set([
  "__aqeActiveField",
  "__aqeHistoryAvailabilityByField",
  "__aqeHistorySnapshotsByField",
  "__aqeLastCursorIntent",
  "__aqeLastPlaybackRequest",
  "__aqePendingCommandPayload",
  "__aqePendingGraphRedrawField",
  "__aqePendingGraphRedrawPreserveLearnerOverlay",
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

  it("keeps HTML audio session model files pure", () => {
    const forbiddenImports = [
      "bridge",
      "control-actions",
      "dom-selectors",
      "field-state-store",
      "graph-countdown-overlay",
      "html-audio-session-audio-element",
      "html-audio-session-field-projection",
      "html-audio-session-learner-projection",
      "logger",
      "selection-toolbar-state",
      "visualizer-runtime-state",
      "viewport-actions",
    ];
    const forbiddenRuntimeTerms = [
      "Date",
      "cancelAnimationFrame",
      "clearTimeout",
      "document",
      "logger",
      "performance",
      "pycmd",
      "readFieldState",
      "requestAnimationFrame",
      "sendGraphAnalysisRequest",
      "setCachedProgressMs",
      "setTimeout",
      "updateFieldState",
      "visualizerForOrd",
      "window",
    ];
    const offenders = htmlAudioSessionModelFiles().flatMap((path) => {
      const relPath = toRelPath(path);
      const source = withoutComments(readFileSync(path, "utf-8"));
      const runtimeSource = withoutStringLiterals(source);
      return [
        ...forbiddenImports
          .filter((module) => importsRelativeModule(source, module))
          .map((module) => `${relPath}: imports ${module}`),
        ...forbiddenRuntimeTerms
          .filter((term) => new RegExp(`\\b${term}\\b`).test(runtimeSource))
          .map((term) => `${relPath}: runtime term ${term}`),
      ];
    });

    expect(offenders).toEqual([]);
  });

  it("keeps source playback boundaries out of the legacy progress controller", () => {
    const forbiddenPatterns = [
      {
        relPath: "src/editor-inline/actions-playback.ts",
        patterns: [/handleSourcePlaybackBoundary/, /source-playback-controller/],
      },
      {
        relPath: "src/editor-inline/playback-controller.ts",
        patterns: [/handleSourceLoopBoundary/],
      },
      {
        relPath: "src/editor-inline/actions-audio-clock.ts",
        patterns: [/handlePlaybackBoundary/, /handleSourceAudioError/],
      },
    ];
    const offenders = forbiddenPatterns.flatMap(({ relPath, patterns }) => {
      const source = withoutComments(readFileSync(join(projectRoot, relPath), "utf-8"));
      return patterns
        .filter((pattern) => pattern.test(source))
        .map((pattern) => `${relPath}: ${pattern.source}`);
    });

    expect(offenders).toEqual([]);
  });

  it("keeps source audio element mutation in the HTML audio session operations", () => {
    const source = withoutComments(readFileSync(join(projectRoot, "src/editor-inline/audio-clock.ts"), "utf-8"));
    const forbiddenExports = Array.from(
      source.matchAll(/export function (pauseAudioClock|clearAudioClockSource|reloadAudioClockSource|configureAudioClock|setAudioClockLoop)\b/g),
      (match) => match[1],
    );

    expect(forbiddenExports).toEqual([]);
  });

  it("keeps reviewer panel trigger as a runtime-mounted selector client", () => {
    const triggerSource = readFileSync(join(projectRoot, "src/editor-inline/reviewer-panel-trigger.ts"), "utf-8");
    const runtimeSource = readFileSync(join(projectRoot, "src/editor-inline/runtime.ts"), "utf-8");
    const selectorSource = readFileSync(join(projectRoot, "src/editor-inline/dom-selectors.ts"), "utf-8");

    expect(triggerSource).not.toMatch(/document\.querySelector/);
    expect(triggerSource).toContain('from "./dom-selectors.js"');
    expect(triggerSource).not.toContain('from "./runtime.js"');
    expect(runtimeSource).toContain("installReviewerPanelTriggers");
    expect(runtimeSource).toContain("reviewTargetIsOpen");
    expect(selectorSource).toContain("allReviewerPanelTriggers");
    expect(selectorSource).toContain("reviewerPanelTargetForTrigger");
  });

  it("keeps AQE editor disabled buttons insulated from Anki editor disabled styles", () => {
    const controlsCss = readFileSync(join(projectRoot, "src/editor-inline/styles/controls.css"), "utf-8");
    const editorCss = editorStyleFiles().map((path) => readFileSync(path, "utf-8")).join("\n");

    expect(controlsCss).toContain(".aqe-ui-root button:not(.btn, .btn-close):disabled");
    expect(controlsCss).toContain(".aqe-ui-root button.aqe-button:disabled");
    expect(controlsCss).toContain("border-bottom-color: var(--aqe-border-color);");
    expect(editorCss).not.toMatch(/var\(--border-subtle\)|border-(?:block|inline)-color/);
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

function editorStyleFiles(): string[] {
  return walk(join(sourceRoot, "editor-inline", "styles"))
    .filter((path) => path.endsWith(".css"));
}

function htmlAudioSessionModelFiles(): string[] {
  return productionFiles()
    .filter((path) => {
      const relPath = toRelPath(path);
      return relPath === "src/editor-inline/html-audio-session-types.ts" ||
        relPath === "src/editor-inline/html-audio-session-progress.ts" ||
        relPath.startsWith("src/editor-inline/html-audio-session-machine");
    });
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

function importsRelativeModule(source: string, module: string): boolean {
  const pattern = new RegExp(`\\bfrom\\s+["']\\./${module}\\.js["']|\\bimport\\s+["']\\./${module}\\.js["']`);
  return pattern.test(source);
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
