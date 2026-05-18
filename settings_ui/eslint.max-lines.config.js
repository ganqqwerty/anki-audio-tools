import baseConfig from "./eslint.config.js";

const hardMaxLines = {
  max: 500,
  skipBlankLines: false,
  skipComments: false,
};

/** @type {import("eslint").Linter.Config[]} */
export default [
  ...baseConfig,
  {
    files: ["src/**/*.ts", "src/**/*.svelte", "tests/**/*.ts"],
    ignores: ["src/lib/generated/**"],
    rules: {
      "max-lines": ["error", hardMaxLines],
    },
  },
];
