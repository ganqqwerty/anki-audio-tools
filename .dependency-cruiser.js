/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-pycmd-outside-bridge",
      comment:
        "Only bridge.ts files may reference pycmd. All WebView-to-Python communication must go through bridge modules.",
      severity: "error",
      from: {
        pathNot: "(^|/)(lib|editor-inline|batch)/bridge\\.ts$",
      },
      to: {
        // pycmd is a global, not an import. This rule catches the string
        // 'pycmd' in source files via grep-style checks.
        // dependency-cruiser can't detect global references directly,
        // so a separate rg check in graphs-check handles this.
      },
    },
    {
      name: "editor-inline-no-settings-imports",
      comment:
        "Editor-inline components may not import from settings or batch modules.",
      severity: "error",
      from: { path: "^settings_ui/src/editor-inline" },
      to: {
        path: "^settings_ui/src/(settings|batch)",
      },
    },
    {
      name: "settings-no-editor-imports",
      comment:
        "Settings components may not import from editor-inline or batch modules.",
      severity: "error",
      from: { path: "^settings_ui/src/settings" },
      to: {
        path: "^settings_ui/src/(editor-inline|batch)",
      },
    },
    {
      name: "batch-no-editor-imports",
      comment:
        "Batch components may not import from editor-inline or settings modules.",
      severity: "error",
      from: { path: "^settings_ui/src/batch" },
      to: {
        path: "^settings_ui/src/(editor-inline|settings)",
      },
    },
  ],
  options: {
    doNotFollow: {
      path: "node_modules",
      dependencyTypes: [
        "npm",
        "npm-dev",
        "npm-optional",
        "npm-peer",
        "npm-bundled",
        "npm-no-pkg",
      ],
    },
    includeOnly: "^settings_ui/src",
    tsPreCompilationDeps: true,
    exoticRequireStrings: ["import\\s+type"],
    moduleSystems: ["es6"],
    prefix: "https://github.com/anomalyco/anki-audio-tools/blob/main/",
    reporterOptions: {
      dot: {
        collapsePattern: "node_modules/(?:@[^/]+/[^/]+|[^/]+)",
      },
    },
  },
};
