import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { cwd } from "node:process";
import { describe, expect, it } from "vitest";

const projectRoot = cwd();

const allowedRuntimeConfigFiles = new Set([
  "src/editor-inline/editor-runtime-config.ts",
  "src/editor-inline/globals.d.ts",
]);

function relativeSourcePath(path: string): string {
  return relative(projectRoot, path).split(sep).join("/");
}

function sourceFilesUnder(path: string): string[] {
  const stat = statSync(path);
  if (stat.isFile()) {
    return /\.(svelte|ts)$/.test(path) ? [path] : [];
  }
  if (!stat.isDirectory()) return [];
  return readdirSync(path).flatMap((entry) => sourceFilesUnder(join(path, entry)));
}

describe("editor runtime config boundary", () => {
  it("centralizes direct editor runtime config access in the adapter", () => {
    const violations = sourceFilesUnder(join(projectRoot, "src"))
      .map((path) => ({ path, relativePath: relativeSourcePath(path) }))
      .filter(({ relativePath }) => !allowedRuntimeConfigFiles.has(relativePath))
      .filter(({ path }) => readFileSync(path, "utf8").includes("__AQE_EDITOR_CONFIG__"))
      .map(({ relativePath }) => relativePath);

    expect(violations).toEqual([]);
  });
});
