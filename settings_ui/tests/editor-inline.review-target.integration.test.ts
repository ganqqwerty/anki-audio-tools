import { afterEach, describe, expect, it } from "vitest";

import { installReviewerPanelTriggers } from "../src/editor-inline/reviewer-panel-trigger.js";
import { disposeEditorRuntime, initializeEditorRuntime, scan } from "../src/editor-inline/runtime.js";

describe("editor inline review targets", () => {
  afterEach(() => {
    disposeEditorRuntime();
  });

  it("mounts controls on reviewer audio targets", () => {
    document.body.innerHTML = `
      <section id="qa">
        <div
          class="aqe-review-audio-target"
          data-field-ord="2"
          data-aqe-source-filename="review clip.mp3"
        ></div>
      </section>
    `;

    const config = { audioFieldIndices: [] };
    initializeEditorRuntime(config);
    scan(config);

    const controls = document.querySelector<HTMLElement>('.aqe-controls[data-aqe-field-ord="2"]');
    const host = document.querySelector<HTMLElement>(".aqe-mount-host");
    const target = document.querySelector<HTMLElement>(".aqe-review-audio-target");
    expect(controls).not.toBeNull();
    expect(host?.dataset.aqeSurface).toBe("reviewer");
    expect(host?.parentElement).toBe(target);
    expect(controls?.dataset.aqeSourceFilename).toBe("review clip.mp3");
    expect(document.querySelector('[data-testid="aqe-button-2-play"]')).not.toBeNull();
  });

  it("mounts explicit template targets after the reviewer panel trigger is clicked", () => {
    document.body.innerHTML = `
      <section id="qa">
        <button
          type="button"
          class="aqe-review-audio-panel-trigger"
          data-testid="aqe-review-audio-panel-trigger-1"
          data-field-ord="1"
          data-aqe-source-filename="back.mp3"
        >Show audio editor</button>
        <div
          class="aqe-review-audio-target"
          data-field-ord="1"
          data-aqe-source-filename="back.mp3"
          data-aqe-panel-trigger-target="true"
          data-aqe-panel-open="false"
        ></div>
      </section>
    `;

    const config = { audioFieldIndices: [] };
    initializeEditorRuntime(config);
    scan(config);

    expect(document.querySelector<HTMLElement>('.aqe-controls[data-aqe-field-ord="1"]')).toBeNull();

    document.querySelector<HTMLButtonElement>('[data-testid="aqe-review-audio-panel-trigger-1"]')?.click();

    const controls = document.querySelector<HTMLElement>('.aqe-controls[data-aqe-field-ord="1"]');
    const target = document.querySelector<HTMLElement>(".aqe-review-audio-target");
    expect(controls).not.toBeNull();
    expect(controls?.closest(".aqe-review-audio-target")).toBe(target);
    expect(controls?.dataset.aqeSourceFilename).toBe("back.mp3");
    expect(target?.dataset.aqePanelOpen).toBe("true");
  });

  it("matches explicit template targets with escaped source filenames", () => {
    document.body.innerHTML = `
      <section id="qa">
        <button
          type="button"
          class="aqe-review-audio-panel-trigger"
          data-testid="aqe-review-audio-panel-trigger-0"
          data-field-ord="0"
          data-aqe-source-filename="bad&quot;clip.mp3"
        >Show audio editor</button>
        <div
          class="aqe-review-audio-target"
          data-field-ord="0"
          data-aqe-source-filename="bad&quot;clip.mp3"
          data-aqe-panel-trigger-target="true"
          data-aqe-panel-open="false"
        ></div>
      </section>
    `;

    const config = { audioFieldIndices: [] };
    initializeEditorRuntime(config);
    scan(config);
    document.querySelector<HTMLButtonElement>('[data-testid="aqe-review-audio-panel-trigger-0"]')?.click();

    const controls = document.querySelector<HTMLElement>('.aqe-controls[data-aqe-field-ord="0"]');
    expect(controls).not.toBeNull();
    expect(controls?.dataset.aqeSourceFilename).toBe('bad"clip.mp3');
  });

  it("does not install duplicate trigger handlers across rescans", () => {
    document.body.innerHTML = `
      <button
        type="button"
        class="aqe-review-audio-panel-trigger"
        data-field-ord="1"
        data-aqe-source-filename="back.mp3"
      >Show audio editor</button>
    `;
    let scanCount = 0;

    installReviewerPanelTriggers(() => {
      scanCount += 1;
    });
    installReviewerPanelTriggers(() => {
      scanCount += 1;
    });
    document.querySelector<HTMLButtonElement>(".aqe-review-audio-panel-trigger")?.click();

    expect(scanCount).toBe(1);
  });
});
