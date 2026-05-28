# GitHub Pages Product Link Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route changing video, feedback, and community destinations through stable GitHub Pages URLs, with split-menu and batch links opening browser links and no embedded video viewer.

**Architecture:** The add-on and Svelte bundles should know only first-party `https://ganqqwerty.github.io/anki-audio-tools/` URLs. GitHub Pages owns one static `/go/.../` redirect page per changing target, so changing a target requires a website update but not an add-on release. Editor webview links continue through the existing `aqe:open-url` bridge; non-editor webviews use normal anchors with `target="_blank"`.

**Tech Stack:** Python 3.13, pytest, Svelte 5, TypeScript, Vitest, static GitHub Pages HTML.

---

## Temporary Inputs

Raw external targets are intentionally not stored in this plan.

- Video target source: `/tmp/anki-audio-tools-video-links-2026-05-28.json`
- Non-video product target source: `/tmp/anki-audio-tools-product-link-targets-2026-05-28.json`

These files are build inputs for the migration only. Do not commit them. The generated `docs/go/.../index.html` pages will contain the actual redirect targets because GitHub Pages must serve them.

## Scope

In scope:

- Route supplied video links through GitHub Pages `/go/video-.../` pages.
- Route current add-on feedback/community links through GitHub Pages `/go/.../` pages.
- Add record voice and batch processing video links.
- Keep split-menu links as browser-open links, not embedded players.
- Replace exact Python URL allowlisting with a first-party GitHub Pages allow rule.

Out of scope:

- Embedded video players.
- Remote JSON fetching from the add-on.
- Reworking website visual design beyond simple static link content.
- Adding video links for convert or pitch-hum until target URLs are supplied.

## File Structure

Create:

- `docs/go/video-play/index.html` - redirect page for play menu video.
- `docs/go/video-graph/index.html` - redirect page for graph menu video.
- `docs/go/video-share/index.html` - redirect page for share menu video.
- `docs/go/video-denoise/index.html` - redirect page for denoise menu video.
- `docs/go/video-shorten-pauses/index.html` - redirect page for remove pauses menu video.
- `docs/go/video-speed/index.html` - redirect page for faster/slower menu video.
- `docs/go/video-record-voice/index.html` - redirect page for record voice menu video.
- `docs/go/video-volume/index.html` - redirect page for louder/quieter menu video.
- `docs/go/video-batch-processing/index.html` - redirect page for batch processing video.
- `docs/go/bug-report/index.html` - redirect page for bug reports.
- `docs/go/idea-request/index.html` - redirect page for idea requests.
- `docs/go/discord/index.html` - redirect page for Discord.
- `docs/go/patreon/index.html` - redirect page for Patreon.
- `docs/go/telegram/index.html` - redirect page for Telegram.
- `tests/test_github_pages_redirects.py` - repository-level tests for static redirect pages.

Modify:

- `docs/index.html` - list feature videos as normal browser links; no iframes.
- `settings_ui/src/lib/product-links.ts` - expose stable GitHub Pages URLs only.
- `settings_ui/tests/product-links.test.ts` - validate first-party product links and docs backing.
- `addon/anki_audio_quick_editor/editor_actions.py` - trust first-party GitHub Pages URLs by origin/path instead of exact string set.
- `tests/test_editor_external_links.py` - verify allowed first-party URLs and rejected non-first-party URLs.
- `settings_ui/src/editor-inline/RecordingSplitOptions.svelte` - add record voice video link.
- `settings_ui/tests/editor-inline.recording.integration.test.ts` - assert record voice video link.
- `settings_ui/src/batch/BatchApp.svelte` - add batch processing video link.
- `settings_ui/tests/batch-app.test.ts` - assert batch processing video link.

---

### Task 1: Add GitHub Pages Redirect Pages

**Files:**

- Create: `tests/test_github_pages_redirects.py`
- Create: `docs/go/video-play/index.html`
- Create: `docs/go/video-graph/index.html`
- Create: `docs/go/video-share/index.html`
- Create: `docs/go/video-denoise/index.html`
- Create: `docs/go/video-shorten-pauses/index.html`
- Create: `docs/go/video-speed/index.html`
- Create: `docs/go/video-record-voice/index.html`
- Create: `docs/go/video-volume/index.html`
- Create: `docs/go/video-batch-processing/index.html`
- Create: `docs/go/bug-report/index.html`
- Create: `docs/go/idea-request/index.html`
- Create: `docs/go/discord/index.html`
- Create: `docs/go/patreon/index.html`
- Create: `docs/go/telegram/index.html`
- Modify: `docs/index.html`

- [ ] **Step 1: Write the failing redirect-page tests**

Create `tests/test_github_pages_redirects.py`:

```python
"""Static GitHub Pages redirect page tests."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

VIDEO_ROUTES = {
    "video-play": "Play menu video",
    "video-graph": "Graph menu video",
    "video-share": "Share menu video",
    "video-denoise": "Denoise menu video",
    "video-shorten-pauses": "Remove pauses menu video",
    "video-speed": "Faster and slower menu video",
    "video-record-voice": "Record voice menu video",
    "video-volume": "Louder and quieter menu video",
    "video-batch-processing": "Batch processing video",
}

PRODUCT_ROUTES = {
    **VIDEO_ROUTES,
    "bug-report": "Report a bug",
    "idea-request": "Request an idea",
    "discord": "Discord",
    "patreon": "Patreon",
    "telegram": "Telegram",
}


def _redirect_page(route: str) -> Path:
    return REPO_ROOT / "docs" / "go" / route / "index.html"


def test_product_redirect_pages_exist_and_have_fallback_links() -> None:
    for route, label in PRODUCT_ROUTES.items():
        page = _redirect_page(route)
        assert page.exists(), f"missing redirect page for {route}"
        html = page.read_text(encoding="utf-8")
        assert label in html
        assert 'http-equiv="refresh"' in html
        assert 'rel="canonical"' in html
        assert "<a " in html


def test_video_redirect_pages_do_not_embed_video_players() -> None:
    for route in VIDEO_ROUTES:
        html = _redirect_page(route).read_text(encoding="utf-8").lower()
        assert "<iframe" not in html
        assert "<video" not in html
        assert "open video" in html
```

- [ ] **Step 2: Run the redirect-page tests and confirm they fail**

Run:

```bash
python3 -m pytest tests/test_github_pages_redirects.py -q
```

Expected: FAIL because the `docs/go/.../index.html` files do not exist yet.

- [ ] **Step 3: Generate static redirect pages from the temp input files**

Run this one-time migration command from the repository root:

```bash
node <<'NODE'
const fs = require("node:fs");
const path = require("node:path");

const videoSourcePath = "/tmp/anki-audio-tools-video-links-2026-05-28.json";
const productSourcePath = "/tmp/anki-audio-tools-product-link-targets-2026-05-28.json";

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function pageHtml(entry) {
  const label = escapeHtml(entry.label);
  const url = escapeHtml(entry.url);
  const cta = entry.route.startsWith("video-") ? "Open video" : "Open link";
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="0; url=${url}">
    <link rel="canonical" href="${url}">
    <title>${label}</title>
  </head>
  <body>
    <main>
      <h1>${label}</h1>
      <p>If your browser does not open the destination automatically, use the link below.</p>
      <p><a href="${url}" rel="noopener noreferrer">${cta}</a></p>
    </main>
  </body>
</html>
`;
}

const videos = readJson(videoSourcePath).videos;
const links = readJson(productSourcePath).links;
for (const entry of [...videos, ...links]) {
  if (!entry.route || !entry.label || !entry.url) {
    throw new Error(`Invalid redirect entry: ${JSON.stringify(entry)}`);
  }
  const outputDir = path.join("docs", "go", entry.route);
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, "index.html"), pageHtml(entry), "utf8");
}
NODE
```

Expected: the command creates the `docs/go/.../index.html` redirect pages.

- [ ] **Step 4: Replace the feature videos section with browser links only**

In `docs/index.html`, replace the current `<section class="section" id="feature-videos">...</section>` block with:

```html
        <section class="section" id="feature-videos">
          <h2>Feature Videos</h2>
          <p>
            Short walkthrough videos open in your browser through stable GitHub Pages links. The add-on uses
            these first-party routes so video destinations can change without a new add-on release.
          </p>
          <ul class="feature-list">
            <li id="video-play"><strong>Play:</strong> Playback and repeat controls. <a href="go/video-play/">Open video</a>.</li>
            <li id="video-graph"><strong>Graph:</strong> Pitch and loudness visualization settings. <a href="go/video-graph/">Open video</a>.</li>
            <li id="video-share"><strong>Share:</strong> Upload and copy-link workflow. <a href="go/video-share/">Open video</a>.</li>
            <li id="video-convert"><strong>Convert:</strong> Choosing output formats. No video is currently linked.</li>
            <li id="video-shorten-pauses"><strong>Shorten Pauses:</strong> Pause aggressiveness settings. <a href="go/video-shorten-pauses/">Open video</a>.</li>
            <li id="video-denoise"><strong>Denoise:</strong> Noise and voice-isolation options. <a href="go/video-denoise/">Open video</a>.</li>
            <li id="video-pitch-hum"><strong>Pitch Hum:</strong> Pitch-preserving hum generation. No video is currently linked.</li>
            <li id="video-speed"><strong>Speed:</strong> Slower and faster audio controls. <a href="go/video-speed/">Open video</a>.</li>
            <li id="video-record-voice"><strong>Record Voice:</strong> Learner voice recording controls. <a href="go/video-record-voice/">Open video</a>.</li>
            <li id="video-volume"><strong>Volume:</strong> Louder and quieter audio controls. <a href="go/video-volume/">Open video</a>.</li>
            <li id="video-batch-processing"><strong>Batch Processing:</strong> Browser batch workflow. <a href="go/video-batch-processing/">Open video</a>.</li>
          </ul>
        </section>
```

- [ ] **Step 5: Run the redirect-page tests and confirm they pass**

Run:

```bash
python3 -m pytest tests/test_github_pages_redirects.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add docs/index.html docs/go tests/test_github_pages_redirects.py
git commit -m "docs: add stable product redirect pages"
```

---

### Task 2: Move Product Link Constants To First-Party Routes

**Files:**

- Modify: `settings_ui/src/lib/product-links.ts`
- Modify: `settings_ui/tests/product-links.test.ts`

- [ ] **Step 1: Replace the product-link tests**

Replace `settings_ui/tests/product-links.test.ts` with:

```typescript
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
```

- [ ] **Step 2: Run the product-link test and confirm it fails**

Run:

```bash
cd settings_ui && npm run test -- product-links.test.ts
```

Expected: FAIL because `PRODUCT_LINKS` still contains direct third-party links and is missing the new video routes.

- [ ] **Step 3: Replace the product-link constants**

Replace `settings_ui/src/lib/product-links.ts` with:

```typescript
const GITHUB_PAGES_URL = "https://ganqqwerty.github.io/anki-audio-tools/";

function githubPagesPath(path: string): string {
  return `${GITHUB_PAGES_URL}${path}`;
}

export const PRODUCT_LINKS = {
  bugReport: githubPagesPath("go/bug-report/"),
  discord: githubPagesPath("go/discord/"),
  editorVideos: {
    batchProcessing: githubPagesPath("go/video-batch-processing/"),
    convert: `${GITHUB_PAGES_URL}#video-convert`,
    denoise: githubPagesPath("go/video-denoise/"),
    graph: githubPagesPath("go/video-graph/"),
    pauseShortening: githubPagesPath("go/video-shorten-pauses/"),
    pitchHum: `${GITHUB_PAGES_URL}#video-pitch-hum`,
    playback: githubPagesPath("go/video-play/"),
    recordVoice: githubPagesPath("go/video-record-voice/"),
    share: githubPagesPath("go/video-share/"),
    speed: githubPagesPath("go/video-speed/"),
    volume: githubPagesPath("go/video-volume/"),
  },
  githubPages: GITHUB_PAGES_URL,
  ideaRequest: githubPagesPath("go/idea-request/"),
  patreon: githubPagesPath("go/patreon/"),
  telegram: githubPagesPath("go/telegram/"),
} as const;

export const DOCUMENTATION_SECTION_LINKS = Object.values(PRODUCT_LINKS.editorVideos);
```

- [ ] **Step 4: Run the product-link test and confirm it passes**

Run:

```bash
cd settings_ui && npm run test -- product-links.test.ts
```

Expected: PASS.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add settings_ui/src/lib/product-links.ts settings_ui/tests/product-links.test.ts
git commit -m "refactor: route product links through github pages"
```

---

### Task 3: Trust GitHub Pages URLs In The Editor Bridge

**Files:**

- Modify: `addon/anki_audio_quick_editor/editor_actions.py`
- Modify: `tests/test_editor_external_links.py`

- [ ] **Step 1: Replace the editor external-link tests**

Replace `tests/test_editor_external_links.py` with:

```python
"""Editor bridge external-link tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from anki_audio_quick_editor.editor_integration import _handle_bridge_command


class Editor:
    pass


def _editor() -> Editor:
    editor = Editor()
    editor.currentField = 0
    editor.web = MagicMock()
    return editor


@pytest.mark.parametrize(
    "url",
    [
        "https://ganqqwerty.github.io/anki-audio-tools/",
        "https://ganqqwerty.github.io/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io/anki-audio-tools/#video-pitch-hum",
    ],
)
def test_bridge_opens_first_party_github_pages_url(url: str) -> None:
    from aqt.qt import QDesktopServices, QUrl

    editor = _editor()
    QDesktopServices.openUrl.return_value = True

    _handle_bridge_command(editor, f'{{"command":"aqe:open-url","url":"{url}"}}')

    QUrl.assert_called_once_with(url)
    QDesktopServices.openUrl.assert_called_once_with(QUrl.return_value)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.invalid/anki-audio-tools/go/video-play/",
        "http://ganqqwerty.github.io/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io.evil.invalid/anki-audio-tools/go/video-play/",
        "https://ganqqwerty.github.io/not-the-addon/go/video-play/",
        "https://user:pass@ganqqwerty.github.io/anki-audio-tools/go/video-play/",
    ],
)
def test_bridge_rejects_non_first_party_external_url(url: str) -> None:
    from aqt.qt import QDesktopServices

    editor = _editor()

    _handle_bridge_command(editor, f'{{"command":"aqe:open-url","url":"{url}"}}')

    QDesktopServices.openUrl.assert_not_called()
    assert any("Could not open that link." in call.args[0] for call in editor.web.eval.call_args_list)
```

- [ ] **Step 2: Run the editor external-link tests and confirm they fail**

Run:

```bash
python3 -m pytest tests/test_editor_external_links.py -q
```

Expected: FAIL because `/go/.../` URLs are not in the exact allowlist yet.

- [ ] **Step 3: Replace exact URL allowlisting with a first-party URL validator**

In `addon/anki_audio_quick_editor/editor_actions.py`:

1. Add the import:

```python
from urllib.parse import urlparse
```

2. Replace the `ALLOWED_EXTERNAL_URLS = frozenset(...)` block with:

```python
TRUSTED_EXTERNAL_URL_HOST = "ganqqwerty.github.io"
TRUSTED_EXTERNAL_URL_PATH = "/anki-audio-tools"
TRUSTED_EXTERNAL_URL_PATH_PREFIX = f"{TRUSTED_EXTERNAL_URL_PATH}/"
```

3. Replace `_external_url_or_none` with:

```python
def _external_url_or_none(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https":
        return None
    if parsed.hostname != TRUSTED_EXTERNAL_URL_HOST:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    if parsed.path != TRUSTED_EXTERNAL_URL_PATH and not parsed.path.startswith(TRUSTED_EXTERNAL_URL_PATH_PREFIX):
        return None
    return value
```

- [ ] **Step 4: Run the editor external-link tests and confirm they pass**

Run:

```bash
python3 -m pytest tests/test_editor_external_links.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add addon/anki_audio_quick_editor/editor_actions.py tests/test_editor_external_links.py
git commit -m "fix: trust github pages product links in editor bridge"
```

---

### Task 4: Add Record Voice And Batch Video Links

**Files:**

- Modify: `settings_ui/src/editor-inline/RecordingSplitOptions.svelte`
- Modify: `settings_ui/tests/editor-inline.recording.integration.test.ts`
- Modify: `settings_ui/src/batch/BatchApp.svelte`
- Modify: `settings_ui/tests/batch-app.test.ts`

- [ ] **Step 1: Update recording integration test expectations**

In `settings_ui/tests/editor-inline.recording.integration.test.ts`, add this import:

```typescript
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
```

In the test named `renders the opt-in grouped buttons and dispatches record after the configured countdown`, after opening the record voice split menu and before reading the countdown input, add:

```typescript
    const popover = document.querySelector<HTMLElement>('[data-testid="aqe-split-0-record-voice-popover"]')!;
    expect(popover.querySelector<HTMLAnchorElement>(".aqe-split-video-link")).toHaveAttribute(
      "href",
      PRODUCT_LINKS.editorVideos.recordVoice,
    );
```

- [ ] **Step 2: Update batch app test expectations**

In `settings_ui/tests/batch-app.test.ts`, inside the test named `renders controls and sends a graph start request`, after the existing GitHub Pages link assertion, add:

```typescript
    expect(screen.getByRole("link", { name: "See video" })).toHaveAttribute(
      "href",
      PRODUCT_LINKS.editorVideos.batchProcessing,
    );
```

- [ ] **Step 3: Run the focused UI tests and confirm they fail**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.recording.integration.test.ts batch-app.test.ts
```

Expected: FAIL because the record voice and batch video links are not rendered yet.

- [ ] **Step 4: Add the record voice split-menu video link**

In `settings_ui/src/editor-inline/RecordingSplitOptions.svelte`, add imports:

```svelte
  import { PRODUCT_LINKS } from "../lib/product-links.js";
  import { openEditorExternalLink } from "./external-links.js";
```

Replace the description paragraph with:

```svelte
<p class="aqe-split-popover-description">
  {t("editor.split.description_record_voice")}
  <a
    class="aqe-split-video-link"
    href={PRODUCT_LINKS.editorVideos.recordVoice}
    onclick={(event) => openEditorExternalLink(event, PRODUCT_LINKS.editorVideos.recordVoice)}
    target="_blank"
    rel="noopener noreferrer"
  >
    {t("links.see_video")}
  </a>
</p>
```

- [ ] **Step 5: Add the batch processing video link**

In `settings_ui/src/batch/BatchApp.svelte`, add this anchor to the `<nav class="resource-links" ...>` block immediately after the GitHub Pages link:

```svelte
        <a href={PRODUCT_LINKS.editorVideos.batchProcessing} target="_blank" rel="noopener noreferrer">
          <ProductLinkIcon className="resource-link-icon" icon="external-link" />
          <span>{t("links.see_video")}</span>
        </a>
```

- [ ] **Step 6: Run the focused UI tests and confirm they pass**

Run:

```bash
cd settings_ui && npm run test -- editor-inline.recording.integration.test.ts batch-app.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

Run:

```bash
git add settings_ui/src/editor-inline/RecordingSplitOptions.svelte settings_ui/tests/editor-inline.recording.integration.test.ts settings_ui/src/batch/BatchApp.svelte settings_ui/tests/batch-app.test.ts
git commit -m "feat: link record and batch videos"
```

---

### Task 5: Verify Link Hygiene And Full Quality Gate

**Files:**

- No new files.
- May modify files from previous tasks only if verification finds issues.

- [ ] **Step 1: Confirm raw mutable targets are not left in add-on or tests**

Run:

```bash
rg -n "https://(youtu|www\.youtube|tally|discord|patreon|t\.me)" settings_ui/src addon/anki_audio_quick_editor tests docs --glob '!docs/go/**'
```

Expected: no matches. Any match outside `docs/go/**` means a mutable external target leaked back into code or tests.

- [ ] **Step 2: Run focused Python tests**

Run:

```bash
python3 -m pytest tests/test_github_pages_redirects.py tests/test_editor_external_links.py -q
```

Expected: PASS.

- [ ] **Step 3: Run focused frontend tests**

Run:

```bash
cd settings_ui && npm run test -- product-links.test.ts editor-inline.recording.integration.test.ts batch-app.test.ts editor-inline.split-menu-content.integration.test.ts editor-inline.help-links.test.ts editor-inline.play-options.integration.test.ts editor-inline.denoise.integration.test.ts app.test.ts
```

Expected: PASS.

- [ ] **Step 4: Run repository checks**

Run:

```bash
python3 scripts/dev.py typecheck
python3 scripts/dev.py test
python3 scripts/dev.py check
```

Expected: all commands complete successfully.

- [ ] **Step 5: Run e2e before declaring the feature complete**

Run:

```bash
python3 scripts/dev.py test-e2e
```

Expected: PASS.

- [ ] **Step 6: Commit verification fixes if needed**

If verification required any fixes, commit them:

```bash
git add <fixed-files>
git commit -m "test: cover github pages product links"
```

If no fixes were needed, do not create an empty commit.

---

## Self-Review

- Spec coverage: The plan routes supplied videos, current feedback/community links, record voice, and batch processing through GitHub Pages without an embedded viewer.
- Raw target hygiene: Raw external targets stay in `/tmp` inputs and generated `docs/go/**` pages only; the plan intentionally references only temp input paths and stable first-party routes.
- Type consistency: Product link keys used by UI tasks match `PRODUCT_LINKS.editorVideos` keys defined in Task 2.
- Testing: Python tests cover redirect pages and editor bridge validation. Frontend tests cover constants, record voice link rendering, batch link rendering, and existing split/help link behavior.
