import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    conditions: ["browser"],
    alias: {
      $lib: "/src/lib",
    },
  },
  build: {
    outDir: "../addon/anki_audio_quick_editor/templates/batch",
    emptyOutDir: false,
    lib: {
      entry: "src/batch/main.ts",
      name: "BatchOperationsUI",
      fileName: "batch_bundle",
      formats: ["iife"],
    },
    rollupOptions: {
      output: {
        entryFileNames: "batch_bundle.js",
        assetFileNames: "batch_bundle.[ext]",
      },
    },
  },
});
