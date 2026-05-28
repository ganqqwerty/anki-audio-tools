import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";

import { describe, expect, it } from "vitest";

import { DOCUMENTATION_SECTION_LINKS, PRODUCT_LINKS } from "../src/lib/product-links.js";

const FIRST_PARTY_ORIGIN = new URL(PRODUCT_LINKS.githubPages).origin;
const DOCS_ROOT = join(cwd(), "../docs");
const ANCHOR_ONLY_SECTIONS = new Set(["video-convert", "video-pitch-hum"]);
const GO_VIDEO_PATHS = new Set([
  "/anki-audio-tools/go/video-play/",
  "/anki-audio-tools/go/video-graph/",
  "/anki-audio-tools/go/video-share/",
  "/anki-audio-tools/go/video-denoise/",
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
    const docsHtml = readFileSync(join(DOCS_ROOT, "index.html"), "utf-8");
    const uniqueLinks = new Set(DOCUMENTATION_SECTION_LINKS);

    expect(uniqueLinks.size).toBe(DOCUMENTATION_SECTION_LINKS.length);
    expect(DOCUMENTATION_SECTION_LINKS).toHaveLength(11);

    for (const link of DOCUMENTATION_SECTION_LINKS) {
      const url = new URL(link);
      if (url.hash) {
        expect(ANCHOR_ONLY_SECTIONS).toContain(url.hash.slice(1));
        expect(docsHtml).toContain(`id="${url.hash.slice(1)}"`);
        continue;
      }
      expect(GO_VIDEO_PATHS).toContain(url.pathname);
      expect(docsGoPageExists(url)).toBe(true);
    }
  });
});
