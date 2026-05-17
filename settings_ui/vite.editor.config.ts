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
    outDir: "../addon/anki_audio_quick_editor/templates/editor",
    emptyOutDir: false,
    lib: {
      entry: "src/editor-inline/main.ts",
      name: "EditorInlineUI",
      fileName: "editor_bundle",
      formats: ["iife"],
    },
    rollupOptions: {
      output: {
        entryFileNames: "editor_bundle.js",
        assetFileNames: "editor_bundle.[ext]",
      },
    },
  },
});
