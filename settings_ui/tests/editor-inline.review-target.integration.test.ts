import { afterEach, describe, expect, it } from "vitest";

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
    expect(controls).not.toBeNull();
    expect(controls?.dataset.aqeSourceFilename).toBe("review clip.mp3");
    expect(document.querySelector('[data-testid="aqe-button-2-play"]')).not.toBeNull();
  });
});
