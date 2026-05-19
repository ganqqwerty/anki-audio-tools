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
