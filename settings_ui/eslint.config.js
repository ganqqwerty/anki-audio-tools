import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import sveltePlugin from "eslint-plugin-svelte";
import svelteParser from "svelte-eslint-parser";
import globals from "globals";

// Files that are allowed to call pycmd() and assign window.on* callbacks
const BRIDGE_FILES = ["**/lib/bridge.ts"];

/** @type {import("eslint").Linter.Config[]} */
export default [
  // Ignore config files and build output
  {
    ignores: [
      "node_modules/**",
      "../addon/anki_audio_quick_editor/templates/settings/**",
      "src/components/ui/**",
      "vite.config.ts",
      "vitest.config.ts",
      "svelte.config.js",
      "eslint.config.js",
    ],
  },

  js.configs.recommended,

  // TypeScript source files (non-bridge, non-test)
  {
    files: ["src/**/*.ts"],
    ignores: BRIDGE_FILES,
    languageOptions: {
      parser: tsParser,
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      // Use TS-aware no-unused-vars (handles type-only params correctly)
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": ["error", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        caughtErrorsIgnorePattern: "^_",
        // Ignore type-only declarations
        ignoreRestSiblings: true,
      }],
      // TS-A: no pycmd() outside bridge.ts
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='pycmd']",
          message:
            "pycmd() must only be called from src/lib/bridge.ts. Use bridge functions instead.",
        },
        // TS-B: no window.on* assignment outside bridge.ts
        {
          selector:
            "AssignmentExpression[left.type='MemberExpression'][left.object.name='window'][left.property.name=/^on[A-Z]/]",
          message:
            "window.on* callbacks must only be registered in src/lib/bridge.ts via registerCallbacks().",
        },
      ],
      // Disallow console.log — use logger.ts instead
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },

  // Svelte files
  {
    files: ["src/**/*.svelte"],
    languageOptions: {
      parser: svelteParser,
      parserOptions: {
        parser: tsParser,
      },
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      svelte: sveltePlugin,
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      ...sveltePlugin.configs.recommended.rules,
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": ["error", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      }],
      // TS-A and TS-B apply to Svelte files too
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='pycmd']",
          message:
            "pycmd() must only be called from src/lib/bridge.ts. Use bridge functions instead.",
        },
        {
          selector:
            "AssignmentExpression[left.type='MemberExpression'][left.object.name='window'][left.property.name=/^on[A-Z]/]",
          message:
            "window.on* callbacks must only be registered in src/lib/bridge.ts via registerCallbacks().",
        },
      ],
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },

  // bridge.ts: allow pycmd and window.on* but still enforce no-console
  {
    files: BRIDGE_FILES,
    languageOptions: {
      parser: tsParser,
      globals: {
        ...globals.browser,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": ["error", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
        // Ignore type-only declarations in declare global {}
        ignoreRestSiblings: true,
      }],
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },

  // Test files: relax most rules, add vitest + jsdom globals
  {
    files: ["tests/**/*.ts"],
    languageOptions: {
      parser: tsParser,
      globals: {
        ...globals.browser,
        vi: "readonly",
        describe: "readonly",
        it: "readonly",
        expect: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "no-console": "off",
      // Tests CAN access window (they run in jsdom)
      // Tests CAN assign window.on* to inspect callbacks
      "no-restricted-syntax": "off",
    },
  },
];
