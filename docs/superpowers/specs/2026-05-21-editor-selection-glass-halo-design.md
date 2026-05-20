# Editor Selection Glass Halo Design

## Context

The inline editor prosody graph renders the selected audio region as an SVG
rectangle with resize handles. The current selected region is intentionally
solid enough to make its boundaries clear, but it lacks visual separation from
the waveform and pitch plot.

## Decision

Add a glass halo effect to the committed selected region only. The effect should
make an already-selected region feel more dimensional without changing selection
behavior, hit targets, playback region logic, or Anki bridge payloads.

## Approach

Use a CSS-only SVG styling change on the existing `.aqe-selection` element.
This keeps the implementation narrow and avoids adding renderer state for a
purely visual treatment.

The committed selection should keep a clear solid border and gain:

- a more glass-like translucent fill,
- a subtle outer halo or glow,
- enough contrast in both light and dark Anki themes.

Draft selections should remain flatter while the user is dragging. The existing
`.aqe-selection-draft` class will explicitly override any committed-selection
halo treatment so drag feedback stays simple and responsive.

## Boundaries

This change will not alter:

- selection gesture thresholds,
- committed or draft selection state,
- playback-region calculation,
- resize handle behavior,
- generated communication contracts,
- Python audio processing.

## Verification

Run the focused frontend quality checks that cover the editor inline bundle and
the build path used by Anki WebView templates. At minimum:

- `python3 scripts/dev.py build`
- targeted Svelte/editor-inline tests when available through the repo runner

Manual visual inspection should confirm that the halo appears only after a
selection is committed and not during drag draft rendering.
