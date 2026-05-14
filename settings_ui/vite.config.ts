import { svelte } from "@sveltejs/vite-plugin-svelte";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    // Force the browser build of Svelte 5 (not the SSR/server build).
    // Without this, Vite resolves Svelte's package.json "exports" using the
    // default "node" condition, which picks the server bundle and causes
    // `mount() is not available on the server` at runtime.
    conditions: ["browser"],
    alias: {
      $lib: "/src/lib",
    },
  },
  build: {
    outDir: "../addon/anki_audio_quick_editor/templates/settings",
    emptyOutDir: false,
    lib: {
      entry: "src/main.ts",
      name: "SettingsUI",
      fileName: "settings_bundle",
      formats: ["iife"],
    },
    rollupOptions: {
      output: {
        entryFileNames: "settings_bundle.js",
        assetFileNames: "settings_bundle.[ext]",
      },
    },
  },
});
