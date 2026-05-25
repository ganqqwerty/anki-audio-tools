# GitHub Pages Website

Date: 2026-05-25
Status: Draft for review

## Goal

Create an English GitHub Pages website for Anki Audio Quick Editor that explains the extension to Anki users and points them to GitHub Releases for installation.

The site should feel like a concise product page and reference page, not a contributor document. It should describe what the add-on does, why it helps language learners and audio-heavy Anki workflows, what requirements apply, and where to download it.

## Decisions

- Use a static site under `docs/` so GitHub Pages can serve it from the default branch without a new frontend build pipeline.
- Make the page section-based with a foldable table of contents.
- Do not use card grids for the main content.
- Use screenshot placeholders now, with stable locations that can later be replaced by real screenshots.
- Point the primary install call to GitHub Releases: `https://github.com/ganqqwerty/anki-audio-tools/releases`.

## Scope

This design covers:

- a single public landing page at `docs/index.html`
- a small stylesheet at `docs/assets/site.css`
- section navigation with a foldable contents control
- English product copy based on the current README and add-on manifest
- screenshot placeholder blocks for later real captures
- local browser verification for desktop and mobile-width layouts

This design does not cover:

- publishing or changing GitHub repository Pages settings
- creating actual Anki screenshots
- adding analytics, cookies, forms, or external scripts
- changing release packaging or Anki add-on runtime behavior
- adding a separate Svelte/Vite website build

## Audience

The primary reader is an Anki desktop user who has audio clips in notes and wants to clean them up without leaving Anki.

The page should answer:

- What does this add-on do?
- Does it edit the original media file?
- What workflows does it support inside the editor?
- What batch tools exist from the Browser?
- What Anki version and platforms are expected?
- Where do I download it?

Developer details should be limited to a small source-code link, not foregrounded.

## Information Architecture

The page will have these top-level sections:

1. Overview
2. Inline Editing
3. Prosody Visualization
4. Batch Tools
5. Non-Destructive Workflow
6. Install
7. Requirements
8. Source And Support

The first viewport should make the product identity clear:

- product name: Anki Audio Quick Editor
- short category: Anki desktop add-on
- headline focused on quick, non-destructive audio edits inside Anki
- primary CTA to GitHub Releases
- secondary link to requirements or source repository
- large screenshot placeholder for the inline editor UI

## Layout

Use a responsive two-column document layout on desktop:

- left column: foldable contents
- right column: page sections

The contents column starts open on desktop and can be collapsed by the reader. It should remain visually lightweight, using a native disclosure-style control or equivalent simple HTML/CSS behavior.

On narrow screens, the contents control moves above the sections and behaves as a full-width foldable block. This avoids squeezing content beside a narrow sidebar.

Main content sections are separated by whitespace and subtle horizontal rules or section bands. They are not rendered as cards.

## Visual Direction

The visual style should be calm, readable, and practical:

- neutral background
- restrained accent color for links and CTA buttons
- strong typographic hierarchy
- no decorative orb/blob backgrounds
- no heavy marketing hero illustration
- no nested cards

Screenshot placeholders should be clearly marked as placeholders for future product screenshots. They should reserve stable dimensions so the layout will not jump when real images are added.

## Content Notes

The copy should emphasize current documented capabilities:

- inline controls for fields containing `[sound:...]` references
- trim-style region operations and playback control
- speed and volume adjustments
- pause shortening
- denoise tools
- pitch hum / prosody-related tools where relevant
- prosody visualization with pitch, intensity, and playback cursor
- non-destructive rendering to new MP3 media files
- batch prosody visualization generation from the Anki Browser
- settings and diagnostics support

Avoid overpromising. The site should not claim AnkiWeb availability unless that is added later.

## Install And Requirements

The install section should point users to GitHub Releases and explain that release assets are `.ankiaddon` files.

The requirements section should include:

- Anki 25.09 or later
- desktop Anki, not AnkiMobile or AnkiDroid
- release archives bundle audio helper tools for macOS arm64, macOS x86_64, and Windows x86_64 according to the current README
- optional advanced overrides can point to external `ffmpeg`/`ffprobe` where needed
- source code is available in the GitHub repository

If the final implementation includes exact filenames, it should keep them generic enough to tolerate version changes, such as `anki-audio-quick-editor-<version>-<target>.ankiaddon`.

## Interaction

The foldable contents control should work without a JavaScript framework. Prefer native HTML disclosure behavior unless implementation testing shows a concrete accessibility or styling problem.

Navigation links should jump to section anchors. The page should use semantic headings so browser find, screen readers, and generated link previews behave predictably.

## Failure And Fallback Behavior

Because this is a static page, failure modes are limited:

- If screenshots are absent, placeholders remain visible and understandable.
- If CSS fails to load, semantic HTML still presents sections in a readable order.
- If GitHub Releases has no matching asset yet, the CTA still lands on the releases page rather than a broken direct asset URL.

## Testing

Implementation should be verified with:

- local static serving or direct browser open, depending on relative asset behavior
- desktop viewport screenshot check
- mobile-width viewport screenshot check
- click test for the foldable contents control
- link checks for internal anchors and the GitHub Releases URL

Full repository QC is not required for a static docs-only site unless the implementation changes project scripts or runtime code.

## Open Follow-Up

Real screenshots should be added later once the desired Anki editor/settings captures are available. The first implementation should leave clear asset names and replacement points for those captures.
