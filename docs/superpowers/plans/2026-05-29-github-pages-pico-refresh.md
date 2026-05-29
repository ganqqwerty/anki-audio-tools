# GitHub Pages Pico Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the GitHub Pages landing page around Pico CSS and Inter while preserving the left anchor navigation, adding the top quick-link strip, and exposing a new AnkiWeb link in Settings.

**Architecture:** Keep the change surgical by splitting it into two surfaces: the static docs landing page and the shared settings link model. The docs page becomes a Pico-based single-page layout with a sticky left table of contents and a simplified content flow, while the Svelte settings UI only extends the shared link constants and existing diagnostics/about resource links.

**Tech Stack:** Static HTML/CSS, Pico CSS via CDN, Google Fonts (Inter), Svelte 5, TypeScript, Vitest, Testing Library

---

## File Map

- Modify: `docs/index.html`
  Responsibility: replace the current landing-page markup with a Pico-based single-page layout that preserves the left table of contents, keeps the same content sections, and adds the top quick-link strip.

- Modify: `docs/assets/site.css`
  Responsibility: act as a small override layer on top of Pico for layout, typography, spacing, hero treatment, quick-link strip styling, media sizing, and sticky navigation.

- Modify: `settings_ui/src/lib/product-links.ts`
  Responsibility: add a shared `ankiWeb` link constant without changing existing first-party redirect links.

- Modify: `settings_ui/src/settings/DiagnosticsLinks.svelte`
  Responsibility: expose the new AnkiWeb link in the existing Diagnostics/About resource links cluster.

- Modify: `settings_ui/tests/product-links.test.ts`
  Responsibility: assert the direct AnkiWeb URL is exposed intentionally while the mutable support links stay first-party.

- Modify: `settings_ui/tests/app.test.ts`
  Responsibility: assert the Diagnostics & About tab renders the AnkiWeb link alongside the existing resource links.

## Task 1: Extend the shared link model and lock behavior with tests

**Files:**
- Modify: `settings_ui/src/lib/product-links.ts`
- Modify: `settings_ui/tests/product-links.test.ts`
- Modify: `settings_ui/tests/app.test.ts`

- [ ] **Step 1: Add a failing product-links test for the direct AnkiWeb URL**

```ts
it("keeps the direct AnkiWeb listing separate from first-party mutable links", () => {
  expect(PRODUCT_LINKS.ankiWeb).toBe(
    "https://ankiweb.net/shared/info/1197817101?cb=1780010134595",
  );

  const url = new URL(PRODUCT_LINKS.ankiWeb);
  expect(url.origin).toBe("https://ankiweb.net");
  expect(url.pathname).toBe("/shared/info/1197817101");
  expect(url.searchParams.get("cb")).toBe("1780010134595");
});
```

- [ ] **Step 2: Add a failing app test for the Diagnostics & About AnkiWeb link**

```ts
it("renders the AnkiWeb listing link in diagnostics", async () => {
  setInitialState();
  render(App);

  await fireEvent.click(screen.getByRole("tab", { name: "Diagnostics & About" }));

  expect(
    screen.getByRole("link", { name: "AnkiWeb listing" }),
  ).toHaveAttribute("href", PRODUCT_LINKS.ankiWeb);
});
```

- [ ] **Step 3: Run the focused tests to confirm they fail before implementation**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui
npx vitest run tests/product-links.test.ts tests/app.test.ts
```

Expected:

```text
FAIL  tests/product-links.test.ts
FAIL  tests/app.test.ts
```

With failures showing that `PRODUCT_LINKS.ankiWeb` and the `"AnkiWeb listing"` diagnostics link do not exist yet.

- [ ] **Step 4: Implement the minimal shared-link and diagnostics-link changes**

`settings_ui/src/lib/product-links.ts`

```ts
const GITHUB_PAGES_URL = "https://ganqqwerty.github.io/anki-audio-tools/";
const ANKIWEB_URL = "https://ankiweb.net/shared/info/1197817101?cb=1780010134595";

function githubPagesPath(path: string): string {
  return `${GITHUB_PAGES_URL}${path}`;
}

export const PRODUCT_LINKS = {
  ankiWeb: ANKIWEB_URL,
  bugReport: githubPagesPath("go/bug-report/"),
  discord: githubPagesPath("go/discord/"),
  // ...
} as const;
```

`settings_ui/src/settings/DiagnosticsLinks.svelte`

```svelte
<a class="diagnostics-link" href={PRODUCT_LINKS.githubPages} target="_blank" rel="noopener noreferrer">
  <span>{t("links.website")}</span>
</a>
<a class="diagnostics-link" href={PRODUCT_LINKS.ankiWeb} target="_blank" rel="noopener noreferrer">
  <ProductLinkIcon className="diagnostics-link-icon" icon="external-link" />
  <span>AnkiWeb listing</span>
</a>
```

Keep the existing Discord, Patreon, Telegram, bug, and idea links unchanged.

- [ ] **Step 5: Re-run the focused tests and commit the link-model change**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui
npx vitest run tests/product-links.test.ts tests/app.test.ts
```

Expected:

```text
PASS  tests/product-links.test.ts
PASS  tests/app.test.ts
```

Commit:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
git add settings_ui/src/lib/product-links.ts settings_ui/src/settings/DiagnosticsLinks.svelte settings_ui/tests/product-links.test.ts settings_ui/tests/app.test.ts
git commit -m "Add AnkiWeb listing to shared product links" -m "Expose the add-on's AnkiWeb listing in the existing Diagnostics & About links so users can reach the canonical install page from settings without changing the rest of the settings UI. The shared product-links model now treats AnkiWeb as a direct stable destination while preserving first-party GitHub Pages redirects for mutable support routes. No full check or e2e routines were run; only focused Vitest coverage for the edited links was executed."
```

## Task 2: Rebuild the GitHub Pages landing page around Pico

**Files:**
- Modify: `docs/index.html`
- Modify: `docs/assets/site.css`

- [ ] **Step 1: Add a lightweight docs smoke test by asserting the new top-link destinations exist in `docs/index.html`**

Create or extend a static assertion in `tests/test_github_pages_redirects.py` with a targeted landing-page check:

```python
def test_docs_home_exposes_primary_support_links() -> None:
    html = (REPO_ROOT / "docs" / "index.html").read_text(encoding="utf-8")

    assert "https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" in html
    assert "https://fonts.googleapis.com" in html
    assert "go/bug-report/" in html
    assert "go/idea-request/" in html
    assert "go/discord/" in html
    assert "go/telegram/" in html
    assert "https://ankiweb.net/shared/info/1197817101?cb=1780010134595" in html
```

- [ ] **Step 2: Run the targeted static tests to confirm the landing-page assertions fail first**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
python3 -m pytest tests/test_github_pages_redirects.py
```

Expected:

```text
FAILED tests/test_github_pages_redirects.py::test_docs_home_exposes_primary_support_links
```

Because the current landing page does not yet load Pico or expose all of the new top-strip links.

- [ ] **Step 3: Replace `docs/index.html` with the new Pico-based single-page structure**

Use a simplified structure like this:

```html
<!doctype html>
<html lang="en" data-theme="light">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Anki Audio Quick Editor is an Anki desktop add-on for quick, non-destructive audio edits inside the note editor.">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css">
    <link rel="stylesheet" href="assets/site.css">
    <title>Anki Audio Quick Editor</title>
  </head>
  <body>
    <header class="site-header">
      <div class="shell masthead">
        <a class="brand" href="#overview">Anki Audio Quick Editor</a>
        <a class="repo-link" href="https://github.com/ganqqwerty/anki-audio-tools">Source on GitHub</a>
      </div>
    </header>

    <div class="shell layout">
      <nav class="contents" aria-label="Page contents">
        <details open>
          <summary>Contents</summary>
          <ol>
            <li><a href="#overview">Overview</a></li>
            <li><a href="#product-preview">Product Preview</a></li>
            <li><a href="#inline-editing">Inline Editing</a></li>
            <li><a href="#prosody-visualization">Prosody Visualization</a></li>
            <li><a href="#feature-videos">Feature Videos</a></li>
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
          <p class="lead">Trim clips, adjust speed and volume, shorten pauses, denoise recordings, and inspect prosody without leaving the note editor.</p>
          <div class="hero-actions">
            <a href="https://github.com/ganqqwerty/anki-audio-tools/releases" role="button">Download from GitHub Releases</a>
            <a href="#requirements" class="secondary">View requirements</a>
          </div>
          <ul class="quick-links" aria-label="Community and support links">
            <li><a href="go/bug-report/">…</a></li>
            <li><a href="go/idea-request/">…</a></li>
            <li><a href="go/discord/">…</a></li>
            <li><a href="go/telegram/">…</a></li>
            <li><a href="https://ankiweb.net/shared/info/1197817101?cb=1780010134595">…</a></li>
          </ul>
        </section>

        <!-- Preserve the existing section ids and content blocks below this point -->
      </main>
    </div>
  </body>
</html>
```

Important implementation constraints:

- Keep the existing section ids exactly: `overview`, `product-preview`, `inline-editing`, `prosody-visualization`, `feature-videos`, `batch-tools`, `non-destructive-workflow`, `install`, `requirements`, `source-and-support`.
- Use inline SVG markup for the quick-link icons so the static docs page does not depend on Svelte components.
- Preserve the existing media assets and feature-video links.

- [ ] **Step 4: Rewrite `docs/assets/site.css` into a small Pico override layer**

Base the stylesheet around these primitives:

```css
:root {
  --pico-font-family: "Inter", ui-sans-serif, system-ui, sans-serif;
  --pico-background-color: #f6f9fc;
  --pico-color: #102033;
  --pico-muted-color: #5b6b7f;
  --pico-primary: #0f62fe;
  --pico-primary-hover: #0a4ed1;
  --pico-border-color: rgba(16, 32, 51, 0.14);
  --page-max-width: 1180px;
  --toc-width: 250px;
}

body {
  background:
    radial-gradient(circle at top, rgba(77, 132, 255, 0.08), transparent 34rem),
    var(--pico-background-color);
}

.layout {
  display: grid;
  grid-template-columns: var(--toc-width) minmax(0, 1fr);
  gap: 3rem;
  align-items: start;
}

.contents {
  position: sticky;
  top: 1.25rem;
}

.hero,
.section {
  padding-block: 2.5rem;
  border-bottom: 1px solid var(--pico-border-color);
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  list-style: none;
  padding: 0;
}

.quick-links a {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}
```

Do not reintroduce card styling for major content blocks. Use spacing, line length, and subtle borders to create the Stripe-like feel instead.

- [ ] **Step 5: Run the targeted static test again, manually inspect the page, and commit the docs rewrite**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
python3 -m pytest tests/test_github_pages_redirects.py
```

Expected:

```text
PASSED tests/test_github_pages_redirects.py
```

Manual verification:

- Open `docs/index.html` in a browser or local preview.
- Confirm the left table of contents stays present.
- Confirm the page is one long sectioned layout rather than stacked cards.
- Confirm the quick-link strip sits directly under the hero and includes bug report, idea request, Discord, Telegram, and AnkiWeb.

Commit:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
git add docs/index.html docs/assets/site.css tests/test_github_pages_redirects.py
git commit -m "Rebuild GitHub Pages around Pico" -m "Replace the old landing-page treatment with a simpler Pico-based single-page layout so the site reads like product documentation instead of a card stack. The new structure preserves the sticky left anchor navigation, keeps the existing section ids and media content, and surfaces support/community/install links immediately below the hero, including the direct AnkiWeb listing. No full check or e2e routines were run; verification was limited to the targeted static docs test and manual page inspection."
```

## Task 3: Final verification and handoff

**Files:**
- No new files expected
- Verify: `settings_ui/src/lib/product-links.ts`
- Verify: `settings_ui/src/settings/DiagnosticsLinks.svelte`
- Verify: `docs/index.html`
- Verify: `docs/assets/site.css`

- [ ] **Step 1: Run the narrow automated checks together**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui
npx vitest run tests/product-links.test.ts tests/app.test.ts

cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
python3 -m pytest tests/test_github_pages_redirects.py
```

Expected:

```text
PASS  tests/product-links.test.ts
PASS  tests/app.test.ts
... 3 passed in tests/test_github_pages_redirects.py
```

- [ ] **Step 2: Build the settings UI to catch compile-time issues in the edited Svelte surface**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools/settings_ui
npm run build:settings
```

Expected:

```text
vite v...
✓ built in ...
```

- [ ] **Step 3: Capture a concise completion note for the PR or final handoff**

Use wording like:

```text
Implemented the GitHub Pages landing-page refresh on top of Pico CSS with Inter, preserved the left-side table of contents, replaced the previous card-heavy treatment with section-based layout, added the top quick-link strip, and exposed the AnkiWeb listing in Settings.

Verification run:
- `npx vitest run tests/product-links.test.ts tests/app.test.ts`
- `python3 -m pytest tests/test_github_pages_redirects.py`
- `npm run build:settings`

Not run:
- `python3 scripts/dev.py check`
- `python3 scripts/dev.py test-e2e`
```

- [ ] **Step 4: Review the diff for accidental scope creep before requesting review**

Run:

```bash
cd /Users/iuriikatkov/IdeaProjects/anki-audio-tools
git diff --stat HEAD~2..HEAD
git diff HEAD~2..HEAD -- docs/index.html docs/assets/site.css settings_ui/src/lib/product-links.ts settings_ui/src/settings/DiagnosticsLinks.svelte settings_ui/tests/product-links.test.ts settings_ui/tests/app.test.ts tests/test_github_pages_redirects.py
```

Expected:

```text
Only the docs landing page, shared product links, diagnostics links, and targeted tests are changed.
```

## Self-Review

### Spec coverage

- Pico CSS and Inter on the docs page: covered in Task 2.
- Preserve left-side sticky table of contents: covered in Task 2.
- Single long anchored page with simplified sections: covered in Task 2.
- Top quick-link strip with bug, idea, Discord, Telegram, and AnkiWeb: covered in Task 2.
- Settings/About AnkiWeb link: covered in Task 1.
- Targeted verification without claiming full repository validation: covered in Task 3.

### Placeholder scan

- No `TODO`, `TBD`, or “similar to” shortcuts remain.
- Every code-changing task includes concrete file targets, code snippets, and commands.

### Type consistency

- Shared link name is `PRODUCT_LINKS.ankiWeb` in both the implementation and tests.
- The settings surface is consistently described as the Diagnostics & About link cluster implemented in `settings_ui/src/settings/DiagnosticsLinks.svelte`.

