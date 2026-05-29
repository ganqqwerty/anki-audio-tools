import { existsSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";

import { describe, expect, it } from "vitest";

import { DOCUMENTATION_SECTION_LINKS, PRODUCT_LINKS } from "../src/lib/product-links.js";

const FIRST_PARTY_ORIGIN = new URL(PRODUCT_LINKS.githubPages).origin;
const DOCS_ROOT = join(cwd(), "../docs");
const ERROR_CODES = [
  "AQE-MEDIA-001",
  "AQE-MEDIA-002",
  "AQE-RUNTIME-001",
  "AQE-RUNTIME-002",
  "AQE-RUNTIME-003",
  "AQE-AUDIO-001",
  "AQE-PLAYBACK-001",
  "AQE-GRAPH-001",
  "AQE-RECORDING-001",
  "AQE-BATCH-001",
  "AQE-SETTINGS-001",
  "AQE-FRONTEND-001",
  "AQE-FRONTEND-002",
  "AQE-FRONTEND-999",
] as const;
const GO_VIDEO_PATHS = new Set([
  "/anki-audio-tools/go/video-play/",
  "/anki-audio-tools/go/video-graph/",
  "/anki-audio-tools/go/video-share/",
  "/anki-audio-tools/go/video-convert/",
  "/anki-audio-tools/go/video-denoise/",
  "/anki-audio-tools/go/video-pitch-hum/",
  "/anki-audio-tools/go/video-shorten-pauses/",
  "/anki-audio-tools/go/video-speed/",
  "/anki-audio-tools/go/video-record-voice/",
  "/anki-audio-tools/go/video-volume/",
  "/anki-audio-tools/go/video-batch-processing/",
]);

function docsGoPageExists(url: URL): boolean {
  const route = url.pathname.replace("/anki-audio-tools/go/", "").replace(/\/$/, "");
  return existsSync(join(DOCS_ROOT, "go", route, "index.html"));
}

describe("product links", () => {
  it("keeps the direct AnkiWeb listing separate from first-party mutable links", () => {
    expect(PRODUCT_LINKS.ankiWeb).toBe(
      "https://ankiweb.net/shared/info/1197817101?cb=1780010134595",
    );

    const url = new URL(PRODUCT_LINKS.ankiWeb);
    expect(url.origin).toBe("https://ankiweb.net");
    expect(url.pathname).toBe("/shared/info/1197817101");
    expect(url.searchParams.get("cb")).toBe("1780010134595");
  });

  it("keeps mutable product links on the first-party GitHub Pages origin", () => {
    for (const link of [
      PRODUCT_LINKS.bugReport,
      PRODUCT_LINKS.discord,
      PRODUCT_LINKS.ideaRequest,
      PRODUCT_LINKS.patreon,
      PRODUCT_LINKS.telegram,
      ...DOCUMENTATION_SECTION_LINKS,
    ]) {
      const url = new URL(link);
      expect(url.origin).toBe(FIRST_PARTY_ORIGIN);
      expect(url.pathname).toBe("/anki-audio-tools/" + url.pathname.slice("/anki-audio-tools/".length));
    }
  });

  it("backs editor video links with GitHub Pages pages or documented sections", () => {
    const uniqueLinks = new Set(DOCUMENTATION_SECTION_LINKS);

    expect(uniqueLinks.size).toBe(DOCUMENTATION_SECTION_LINKS.length);
    expect(DOCUMENTATION_SECTION_LINKS).toHaveLength(11);

    for (const link of DOCUMENTATION_SECTION_LINKS) {
      const url = new URL(link);
      expect(url.hash).toBe("");
      expect(GO_VIDEO_PATHS).toContain(url.pathname);
      expect(docsGoPageExists(url)).toBe(true);
    }
  });

  it("builds first-party error help links", async () => {
    const { errorHelpUrl } = await import("../src/lib/error-links.js");
    const url = new URL(errorHelpUrl("AQE-RUNTIME-001"));

    expect(url.origin).toBe(FIRST_PARTY_ORIGIN);
    expect(url.pathname).toBe("/anki-audio-tools/errors/AQE-RUNTIME-001/");
  });

  it("backs every initial error help link with a docs page", async () => {
    const { errorHelpUrl } = await import("../src/lib/error-links.js");

    for (const code of ERROR_CODES) {
      const url = new URL(errorHelpUrl(code));
      const pagePath = join(DOCS_ROOT, "errors", code, "index.html");

      expect(url.pathname).toBe(`/anki-audio-tools/errors/${code}/`);
      expect(existsSync(pagePath), `${code} docs page exists`).toBe(true);
    }
  });
});
