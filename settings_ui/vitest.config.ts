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
        branches: 70,
      },
      exclude: [
        "src/components/ui/**",
        "tests/**",
        "**/*.config.*",
        "src/main.ts",
        "src/lib/types.ts",
      ],
    },
  },
});
