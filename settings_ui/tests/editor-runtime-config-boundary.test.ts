import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();

const disallowedEditorConfigReaders = [
  "src/lib/editor-toolbar-buttons.ts",
  "src/editor-inline/commands.ts",
  "src/editor-inline/EditorControls.svelte",
  "src/editor-inline/SelectionToolbar.svelte",
  "src/editor-inline/GraphVisualizer.svelte",
  "src/editor-inline/SplitExtraFields.svelte",
];

describe("editor runtime config boundary", () => {
  it.each(disallowedEditorConfigReaders)("%s does not read window.__AQE_EDITOR_CONFIG__ directly", (relativePath) => {
    const source = readFileSync(join(projectRoot, relativePath), "utf8");

    expect(source).not.toContain("window.__AQE_EDITOR_CONFIG__");
  });
});
