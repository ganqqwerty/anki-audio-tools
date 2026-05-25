import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cwd } from "node:process";

import { describe, expect, it } from "vitest";

import { DOCUMENTATION_SECTION_LINKS, PRODUCT_LINKS } from "../src/lib/product-links.js";

describe("product links", () => {
  it("keeps editor video links anchored to GitHub Pages placeholders", () => {
    const docsHtml = readFileSync(join(cwd(), "../docs/index.html"), "utf-8");
    const uniqueLinks = new Set(DOCUMENTATION_SECTION_LINKS);

    expect(uniqueLinks.size).toBe(DOCUMENTATION_SECTION_LINKS.length);
    expect(DOCUMENTATION_SECTION_LINKS).toHaveLength(9);

    for (const link of DOCUMENTATION_SECTION_LINKS) {
      const url = new URL(link);
      expect(link.startsWith(`${PRODUCT_LINKS.githubPages}#`)).toBe(true);
      expect(docsHtml).toContain(`id="${url.hash.slice(1)}"`);
    }
  });
});
