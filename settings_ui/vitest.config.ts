import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [svelte({ hot: !process.env["VITEST"] })],
  resolve: {
    conditions: ["browser"],
    alias: {
      $lib: "/src/lib",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./tests/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "clover", "lcov"],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80,
        "src/editor-inline/**/*.{ts,svelte}": {
          branches: 75,
          functions: 90,
          lines: 90,
          statements: 90,
        },
        "src/editor-inline/html-audio-session-machine.ts": {
          branches: 70,
          functions: 80,
          lines: 75,
          statements: 75,
        },
        "src/editor-inline/playback-controller-audio.ts": {
          branches: 45,
          functions: 50,
          lines: 50,
          statements: 50,
        },
        "src/editor-inline/playback-controller.ts": {
          branches: 55,
          functions: 70,
          lines: 75,
          statements: 75,
        },
        "src/editor-inline/region-delete-state.ts": {
          branches: 55,
          functions: 50,
          lines: 65,
          statements: 65,
        },
        "src/settings/preset-settings-helpers.ts": {
          branches: 15,
          functions: 15,
          lines: 20,
          statements: 20,
        },
        "src/settings/trigger-settings-state.ts": {
          branches: 35,
          functions: 65,
          lines: 65,
          statements: 65,
        },
      },
      exclude: [
        "src/components/ui/**",
        "tests/**",
        "**/*.config.*",
        "src/main.ts",
        "src/editor-inline/main.ts",
        "src/editor-inline/globals.d.ts",
        "src/lib/types.ts",
      ],
    },
  },
});
