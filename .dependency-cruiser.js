/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "rule49-sm-a11-state-management-no-cycles",
      comment: "Transport and practice packages must remain acyclic.",
      severity: "error",
      from: { path: "^settings_ui/src/editor-inline/(transport|practice)/" },
      to: { circular: true },
    },
    {
      name: "rule39-sm-a01-transport-does-not-import-practice",
      comment: "Transport owns media lifecycle and must not depend on practice sequencing.",
      severity: "error",
      from: { path: "^settings_ui/src/editor-inline/transport/" },
      to: { path: "^settings_ui/src/editor-inline/practice/" },
    },
    {
      name: "rule39-sm-a01-state-management-public-entry-only",
      comment: "Consumers use the transport and practice public entry modules.",
      severity: "error",
      from: {
        path: "^settings_ui/src/editor-inline/",
        pathNot: "^settings_ui/src/editor-inline/(transport|practice)/",
      },
      to: {
        path: "^settings_ui/src/editor-inline/(transport|practice)/(?!index\\.ts$)",
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
