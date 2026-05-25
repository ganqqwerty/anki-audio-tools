# GitHub Pages Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static English GitHub Pages landing page for Anki Audio Quick Editor under `docs/`.

**Architecture:** The site is plain HTML and CSS served by GitHub Pages from the repository `docs/` directory. `docs/index.html` owns semantic content and navigation; `docs/assets/site.css` owns all presentation and responsive behavior. The foldable table of contents uses native `<details>`/`<summary>` controls, so no JavaScript framework or build step is required.

**Tech Stack:** Static HTML5, CSS3, GitHub Pages `/docs` publishing, local verification with Python `http.server` and the in-app browser.

---

## File Structure

- Create `docs/index.html`: single public landing page with section anchors, foldable contents, product copy, install CTA, and screenshot slots.
- Create `docs/assets/site.css`: responsive page layout, typography, CTA styling, screenshot-slot styling, and foldable contents presentation.
- No changes to `settings_ui/`, Anki runtime Python, release scripts, or package metadata.

## Task 1: Add The Static Site Stylesheet

**Files:**
- Create: `docs/assets/site.css`

- [ ] **Step 1: Create the stylesheet**

Use `apply_patch` to create `docs/assets/site.css` with this content:

```css
:root {
  color-scheme: light;
  --bg: #f7f8fb;
  --surface: #ffffff;
  --surface-muted: #eef2f7;
  --text: #17202a;
  --muted: #5f6b7a;
  --border: #d9e0ea;
  --accent: #256f8f;
  --accent-strong: #174d63;
  --accent-soft: #e2f1f6;
  --shadow: 0 18px 45px rgba(23, 32, 42, 0.08);
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-size: 16px;
  line-height: 1.6;
}

a {
  color: var(--accent);
  text-decoration-thickness: 0.08em;
  text-underline-offset: 0.18em;
}

a:hover,
a:focus-visible {
  color: var(--accent-strong);
}

.page-shell {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
}

.site-header {
  padding: 24px 0 16px;
}

.top-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
  font-weight: 700;
  text-decoration: none;
}

.brand-mark {
  display: inline-grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 8px;
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 18px;
}

.source-link {
  font-size: 0.95rem;
  font-weight: 650;
}

.layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 40px;
  align-items: start;
  padding: 18px 0 64px;
}

.contents {
  position: sticky;
  top: 18px;
}

.contents details {
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  box-shadow: var(--shadow);
}

.contents summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 46px;
  padding: 0 14px;
  color: var(--text);
  cursor: pointer;
  font-weight: 700;
  list-style: none;
}

.contents summary::-webkit-details-marker {
  display: none;
}

.contents summary::after {
  content: "+";
  color: var(--accent-strong);
  font-size: 1.2rem;
  line-height: 1;
}

.contents details[open] summary::after {
  content: "-";
}

.contents ol {
  margin: 0;
  padding: 4px 14px 16px 34px;
}

.contents li {
  margin: 8px 0;
  color: var(--muted);
}

.contents a {
  color: var(--muted);
  text-decoration: none;
}

.contents a:hover,
.contents a:focus-visible {
  color: var(--accent-strong);
  text-decoration: underline;
}

.content {
  min-width: 0;
}

.hero {
  padding: 34px 0 44px;
  border-bottom: 1px solid var(--border);
}

.eyebrow {
  margin: 0 0 12px;
  color: var(--accent-strong);
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  margin: 0;
  color: var(--text);
  line-height: 1.15;
  letter-spacing: 0;
}

h1 {
  max-width: 800px;
  font-size: 4.2rem;
}

h2 {
  font-size: 2.25rem;
}

h3 {
  font-size: 1.2rem;
}

.lead {
  max-width: 740px;
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 1.2rem;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 26px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 18px;
  border: 1px solid var(--accent);
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 750;
  text-decoration: none;
}

.button:hover,
.button:focus-visible {
  background: var(--accent-strong);
  border-color: var(--accent-strong);
  color: #ffffff;
}

.button.secondary {
  background: transparent;
  color: var(--accent-strong);
}

.button.secondary:hover,
.button.secondary:focus-visible {
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.screenshot-slot {
  display: grid;
  min-height: 250px;
  margin-top: 32px;
  place-items: center;
  border: 1px dashed #9fb2c3;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(37, 111, 143, 0.08), rgba(255, 255, 255, 0.84)),
    var(--surface);
  color: var(--muted);
  text-align: center;
}

.screenshot-slot strong {
  display: block;
  color: var(--text);
  font-size: 1rem;
}

.section {
  padding: 42px 0;
  border-bottom: 1px solid var(--border);
}

.section:last-child {
  border-bottom: 0;
}

.section p {
  max-width: 760px;
  margin: 14px 0 0;
  color: var(--muted);
}

.feature-list,
.requirements-list {
  display: grid;
  gap: 10px;
  max-width: 820px;
  margin: 22px 0 0;
  padding-left: 20px;
}

.feature-list li,
.requirements-list li {
  padding-left: 4px;
}

.note {
  max-width: 820px;
  margin-top: 22px;
  padding: 16px 18px;
  border-left: 4px solid var(--accent);
  border-radius: 0 8px 8px 0;
  background: var(--accent-soft);
  color: var(--accent-strong);
}

.site-footer {
  padding: 32px 0 48px;
  color: var(--muted);
  font-size: 0.95rem;
}

@media (max-width: 820px) {
  .page-shell {
    width: min(100% - 24px, 720px);
  }

  .top-line {
    align-items: flex-start;
    flex-direction: column;
  }

  .layout {
    grid-template-columns: 1fr;
    gap: 22px;
    padding-top: 6px;
  }

  .contents {
    position: static;
  }

  .hero {
    padding-top: 18px;
  }

  h1 {
    font-size: 2.45rem;
  }

  h2 {
    font-size: 1.75rem;
  }

  .actions {
    align-items: stretch;
    flex-direction: column;
  }

  .button {
    width: 100%;
  }

  .screenshot-slot {
    min-height: 190px;
  }
}
```

- [ ] **Step 2: Verify stylesheet file exists**

Run:

```bash
test -f docs/assets/site.css
```

Expected: command exits with status `0` and no output.

## Task 2: Add The GitHub Pages Landing Page

**Files:**
- Create: `docs/index.html`

- [ ] **Step 1: Create the landing page HTML**

Use `apply_patch` to create `docs/index.html` with this content:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta
      name="description"
      content="Anki Audio Quick Editor is an Anki desktop add-on for quick, non-destructive audio edits inside the note editor."
    >
    <title>Anki Audio Quick Editor</title>
    <link rel="stylesheet" href="assets/site.css">
  </head>
  <body>
    <header class="site-header">
      <div class="page-shell top-line">
        <a class="brand" href="#overview" aria-label="Anki Audio Quick Editor home">
          <span class="brand-mark" aria-hidden="true">A</span>
          <span>Anki Audio Quick Editor</span>
        </a>
        <a class="source-link" href="https://github.com/ganqqwerty/anki-audio-tools">Source on GitHub</a>
      </div>
    </header>

    <div class="page-shell layout">
      <nav class="contents" aria-label="Page contents">
        <details open>
          <summary>Contents</summary>
          <ol>
            <li><a href="#overview">Overview</a></li>
            <li><a href="#inline-editing">Inline Editing</a></li>
            <li><a href="#prosody-visualization">Prosody Visualization</a></li>
            <li><a href="#batch-tools">Batch Tools</a></li>
            <li><a href="#non-destructive-workflow">Non-Destructive Workflow</a></li>
            <li><a href="#install">Install</a></li>
            <li><a href="#requirements">Requirements</a></li>
            <li><a href="#source-and-support">Source And Support</a></li>
          </ol>
        </details>
      </nav>

      <main class="content">
        <section class="hero" id="overview">
          <p class="eyebrow">Anki desktop add-on</p>
          <h1>Quick, non-destructive audio edits inside Anki.</h1>
          <p class="lead">
            Trim sentence-mining clips, adjust speed and volume, shorten long pauses, denoise recordings,
            and inspect prosody without leaving the note editor.
          </p>
          <div class="actions" aria-label="Primary actions">
            <a class="button" href="https://github.com/ganqqwerty/anki-audio-tools/releases">
              Download from GitHub Releases
            </a>
            <a class="button secondary" href="#requirements">View requirements</a>
          </div>
          <div class="screenshot-slot" role="img" aria-label="Reserved space for an inline editor screenshot">
            <span>
              <strong>Inline editor screenshot</strong>
              Replace this area with a real Anki editor capture later.
            </span>
          </div>
        </section>

        <section class="section" id="inline-editing">
          <h2>Inline Editing</h2>
          <p>
            Focus a field with a supported <code>[sound:...]</code> reference and use editor controls directly
            beside the audio. Common actions include playback, speed changes, volume changes, conversion,
            pause shortening, denoise processing, file reveal, sharing, undo, and redo.
          </p>
          <ul class="feature-list">
            <li>Works from the Anki note editor instead of a separate audio program.</li>
            <li>Targets short study clips and sentence-mining audio.</li>
            <li>Provides settings for which toolbar buttons are shown and how processing defaults behave.</li>
          </ul>
        </section>

        <section class="section" id="prosody-visualization">
          <h2>Prosody Visualization</h2>
          <p>
            The add-on can render inline prosody views that show pitch, intensity, and playback position.
            These views help compare pronunciation, inspect rhythm, and navigate useful regions of an audio clip.
          </p>
          <div class="screenshot-slot" role="img" aria-label="Reserved space for a prosody visualization screenshot">
            <span>
              <strong>Prosody visualization screenshot</strong>
              Replace this area with a waveform, pitch, and intensity capture later.
            </span>
          </div>
        </section>

        <section class="section" id="batch-tools">
          <h2>Batch Tools</h2>
          <p>
            Browser actions support batch prosody visualization generation for selected notes. This is useful
            when you want visual aids prepared across a group of audio cards instead of generating each one by hand.
          </p>
        </section>

        <section class="section" id="non-destructive-workflow">
          <h2>Non-Destructive Workflow</h2>
          <p>
            Edits render to new MP3 files and update the field reference. The original media file remains in
            place, so experiments and cleanup work do not overwrite the source audio.
          </p>
          <div class="note">
            The page intentionally links to GitHub Releases rather than a direct asset file, so versioned and
            platform-specific archive names can change without breaking the main install button.
          </div>
        </section>

        <section class="section" id="install">
          <h2>Install</h2>
          <p>
            Download the latest <code>.ankiaddon</code> archive from GitHub Releases, then install it in Anki
            through the desktop add-on manager.
          </p>
          <div class="actions">
            <a class="button" href="https://github.com/ganqqwerty/anki-audio-tools/releases">
              Open GitHub Releases
            </a>
          </div>
        </section>

        <section class="section" id="requirements">
          <h2>Requirements</h2>
          <ul class="requirements-list">
            <li>Anki desktop 25.09 or later.</li>
            <li>Desktop Anki only; not AnkiMobile or AnkiDroid.</li>
            <li>Release archives bundle audio helper tools for macOS arm64, macOS x86_64, and Windows x86_64.</li>
            <li>Advanced users can override audio tool paths, including <code>ffmpeg</code> and <code>ffprobe</code>, where needed.</li>
          </ul>
        </section>

        <section class="section" id="source-and-support">
          <h2>Source And Support</h2>
          <p>
            Source code, development notes, and release assets live in the GitHub repository. Use the repository
            issue tracker for reproducible problems and include Anki version, operating system, and the relevant
            audio file workflow.
          </p>
          <div class="actions">
            <a class="button secondary" href="https://github.com/ganqqwerty/anki-audio-tools">
              View repository
            </a>
          </div>
        </section>
      </main>
    </div>

    <footer class="site-footer">
      <div class="page-shell">
        Anki Audio Quick Editor is an independent Anki desktop add-on.
      </div>
    </footer>
  </body>
</html>
```

- [ ] **Step 2: Verify the page references the stylesheet**

Run:

```bash
rg -n 'href="assets/site.css"|Download from GitHub Releases|<details open>' docs/index.html
```

Expected output includes all three matches:

```text
docs/index.html:15:    <link rel="stylesheet" href="assets/site.css">
docs/index.html:34:        <details open>
docs/index.html:59:              Download from GitHub Releases
```

Line numbers can differ if formatting changes, but the three strings must be present.

## Task 3: Verify Static Behavior And Responsive Layout

**Files:**
- Verify: `docs/index.html`
- Verify: `docs/assets/site.css`

- [ ] **Step 1: Start a local static server**

Run:

```bash
python3 -m http.server 8765 --directory docs
```

Expected output:

```text
Serving HTTP on :: port 8765
```

If port `8765` is occupied, rerun with an unused port and use that port in the browser checks.

- [ ] **Step 2: Open the page in the in-app browser**

Open:

```text
http://localhost:8765/
```

Expected desktop viewport behavior:

- Product name is visible in the top header and hero.
- Main CTA points to `https://github.com/ganqqwerty/anki-audio-tools/releases`.
- Contents panel is visible and open.
- Clicking the Contents summary collapses the list.
- Clicking the Contents summary again expands the list.
- Internal contents links scroll to their matching sections.
- Screenshot slots reserve visible space and explain that real screenshots can be added later.

- [ ] **Step 3: Check mobile-width layout**

Use the in-app browser with a mobile-width viewport such as `390x844`.

Expected mobile behavior:

- Layout becomes one column.
- Contents control appears above the page sections.
- CTA buttons stack vertically and text fits inside them.
- No text overlaps the screenshot slots or section boundaries.

- [ ] **Step 4: Stop the static server**

Stop the `python3 -m http.server` process with `Ctrl-C`.

Expected: the terminal returns to the shell prompt.

## Task 4: Review Scope And Commit

**Files:**
- Review: `docs/index.html`
- Review: `docs/assets/site.css`

- [ ] **Step 1: Confirm only website files changed**

Run:

```bash
git status --short
```

Expected output includes:

```text
?? docs/assets/site.css
?? docs/index.html
```

No Anki runtime, Svelte source, release script, or package lock files should appear because the website is static.

- [ ] **Step 2: Review the diff**

Run:

```bash
git diff -- docs/index.html docs/assets/site.css
```

Expected:

- `docs/index.html` contains one semantic page with section anchors.
- `docs/assets/site.css` contains all presentation styles.
- No external scripts, analytics, generated bundle references, or card-grid layout are introduced.

- [ ] **Step 3: Commit the site**

Run:

```bash
git add docs/index.html docs/assets/site.css
git commit -m "Add GitHub Pages landing page"
```

Expected output includes:

```text
[<branch-or-detached-head> <commit>] Add GitHub Pages landing page
 2 files changed
```

## Self-Review Checklist

- Spec coverage: Tasks 1 and 2 implement the static `docs/` site, foldable contents, section layout, GitHub Releases CTA, English product copy, and screenshot slots. Task 3 covers desktop, mobile, contents toggling, anchor links, and CTA verification. Task 4 keeps the implementation scoped to website files.
- Placeholder scan: The only reserved content is intentional screenshot-slot copy for future real captures. The plan contains no deferred implementation steps.
- Type and name consistency: The HTML references `assets/site.css`; the stylesheet classes used by the HTML are defined in `site.css`; section IDs match the contents links.
