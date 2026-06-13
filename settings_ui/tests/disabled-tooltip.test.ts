import { describe, expect, it } from "vitest";

import { buttonTooltipContent, tooltipWithDisabledClarification } from "../src/lib/disabled-tooltip.js";

describe("buttonTooltipContent", () => {
  it("returns both the button label and description on separate lines", () => {
    expect(buttonTooltipContent("Play", "Play or pause the current audio")).toBe(
      "Play\nPlay or pause the current audio",
    );
  });

  it("avoids duplicating the button label when the description matches", () => {
    expect(buttonTooltipContent("Play", "Play")).toBe("Play");
  });
});

describe("tooltipWithDisabledClarification", () => {
  it("returns the normal tooltip when no disabled reason is present", () => {
    expect(tooltipWithDisabledClarification("Field description", undefined)).toBe("Field description");
  });

  it("appends the disabled reason after the normal tooltip", () => {
    expect(tooltipWithDisabledClarification("Field description", "Disabled because it is running.")).toBe(
      "Field description\n\nDisabled because it is running.",
    );
  });

  it("uses only the disabled reason when the field has no normal tooltip", () => {
    expect(tooltipWithDisabledClarification("", "Disabled because it is running.")).toBe(
      "Disabled because it is running.",
    );
  });
});
