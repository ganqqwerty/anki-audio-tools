# GitHub Pages Pico Refresh Design

## Goal

Refresh the GitHub Pages landing page so it uses Pico CSS with Inter, moves closer to a Stripe-like editorial style, and exposes the main support/community/install links immediately near the top of the page.

This change also adds a direct AnkiWeb link to the Settings resource/about links area. The Settings UI visual design does not change.

## Scope

In scope:

- Replace the current GitHub Pages visual design in `docs/index.html` and `docs/assets/site.css`.
- Preserve the left-side anchored table of contents.
- Keep the page as one long documentation-style landing page.
- Add top-of-page icon links for:
  - Bug submission
  - Idea submission
  - Discord
  - Telegram
  - AnkiWeb
- Add an AnkiWeb link to the Settings resource/about links area.
- Switch the GitHub Pages page typography to Inter.
- Use Pico CSS as the base stylesheet for the GitHub Pages page.

Out of scope:

- Restyling the Settings UI beyond the new AnkiWeb link.
- Changing the existing GitHub Pages redirect endpoints under `docs/go/`.
- Rewriting content copy beyond light edits needed for the new layout.
- Changing add-on runtime behavior or product link destinations other than adding the AnkiWeb URL.

## Constraints

- The GitHub Pages page should feel simpler than the current design. The current card-heavy treatment should be removed.
- The left navigation menu remains in place as the primary page navigation affordance.
- The content remains on a single page with anchor targets.
- The design should lean toward Stripe through spacing, typography, and visual restraint rather than decorative effects.
- The docs page should use Pico CSS rather than a fully custom standalone design system.
- Existing support/community links should continue using the stable GitHub Pages redirect routes where they already exist.
- The AnkiWeb link should use the direct URL provided by the user:
  `https://ankiweb.net/shared/info/1197817101?cb=1780010134595`

## Information Architecture

### GitHub Pages landing page

The page remains a two-column layout:

- Left column: sticky table of contents with anchor links to sections.
- Right column: main content column with the hero and all documentation sections.

The right column structure:

1. Hero
2. Top link strip
3. Product preview
4. Inline editing
5. Prosody visualization
6. Feature videos
7. Batch tools
8. Non-destructive workflow
9. Install
10. Requirements
11. Source and support

### Settings links area

The existing Settings resource/about links cluster keeps its current structure. It gains one additional external link to AnkiWeb alongside the existing website/community/support links.

## Visual Direction

### GitHub Pages page

The new page should feel like a polished documentation landing page:

- Large, direct headline
- Bright white base with subtle blue-gray accents
- Clean section rhythm with dividers instead of cards
- Inter as the typeface
- Minimal shadows or no shadows for main content blocks
- Compact, crisp link treatments

This should be implemented with Pico defaults as the base and a small local stylesheet layer that overrides layout, spacing, colors, and typography.

### Hero and link strip

The hero stays near the top of the main column and contains:

- Eyebrow label
- Main headline
- Supporting description
- Primary install/release action(s)

Immediately below the hero actions, add a horizontally wrapping icon link strip for:

- Report bug
- Request idea
- Discord
- Telegram
- AnkiWeb

The strip should read as quick-access navigation, not as a row of large CTA cards. Icons should be visually consistent with the product’s existing icon vocabulary.

## Content Treatment

- Preserve the existing main content sections and media assets.
- Convert boxed/card-style groupings into simpler section flows with whitespace and rules.
- Keep images and GIFs inline within the content column, with consistent width handling and restrained framing.
- Preserve the feature videos section and its stable GitHub Pages route links.

## Link Model

### GitHub Pages top link strip

Use these destinations:

- Bug submission: existing `docs/go/bug-report/`
- Idea submission: existing `docs/go/idea-request/`
- Discord: existing `docs/go/discord/`
- Telegram: existing `docs/go/telegram/`
- AnkiWeb: direct user-provided AnkiWeb URL

### Settings resource/about links

Add:

- AnkiWeb: direct user-provided AnkiWeb URL

Existing links remain unchanged.

## Implementation Outline

### `docs/index.html`

- Add Pico CSS from CDN as the base stylesheet.
- Add Inter font loading.
- Replace the current page shell markup as needed to support the simplified design while keeping:
  - the left sticky table of contents
  - the single-page anchored layout
  - the existing section IDs for the current main content sections
- Insert the new top link strip under the hero.
- Add inline icon markup or equivalent static HTML-compatible icon rendering for the quick links.

### `docs/assets/site.css`

- Rewrite the stylesheet to act as a compact override layer on top of Pico.
- Remove the current card-heavy component styling.
- Define layout rules for:
  - sticky left table of contents
  - wide readable content column
  - hero spacing
  - top quick-link strip
  - media sizing
  - section spacing and dividers
- Tune colors and spacing toward the requested Stripe-like feel.

### Settings UI source

- Extend the shared product links model with an AnkiWeb URL constant.
- Add the new AnkiWeb link into the existing Settings resource/about links component.
- Reuse the existing external-link/icon treatment already used by the Settings resource links.

## Testing

Minimum verification:

- Confirm the GitHub Pages page renders with the new Pico-based layout and preserved left navigation.
- Confirm the top link strip contains working links for bug report, idea request, Discord, Telegram, and AnkiWeb.
- Confirm the Settings links area includes the new AnkiWeb link.

Project checks:

- Run targeted frontend tests covering shared product links or Settings links if they exist.
- If no targeted test exists, run the smallest relevant automated check that validates the edited frontend code.

Not part of this task:

- Full repository check
- Full e2e suite

If those broader checks are not run, that should be stated in the final commit message/body and completion notes.

## Risks

- Pulling Pico from CDN changes the docs page dependency model and can slightly affect rendering if Pico updates. This is acceptable for the static docs page, but the exact version should be pinned.
- The docs page is static HTML, so existing Svelte icon components cannot be used directly. The docs page will need static icon markup that matches the existing product vocabulary closely enough.
- The Settings area may label the resource cluster as diagnostics/resources rather than “About”; the implementation should modify the actual existing component rather than invent a new section.

## Acceptance Criteria

- The GitHub Pages landing page uses Pico CSS and Inter.
- The previous card-heavy docs landing page styling is removed.
- The left-side sticky table of contents remains present and functional.
- The page remains a single long anchored page.
- The hero is followed by a quick-link strip containing bug submission, idea submission, Discord, Telegram, and AnkiWeb links.
- The Settings resource/about links area includes an AnkiWeb link.
- Existing redirect-based support/community links continue to work through their current GitHub Pages routes.
