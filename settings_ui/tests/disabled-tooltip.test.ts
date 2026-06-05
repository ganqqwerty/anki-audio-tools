import { describe, expect, it } from "vitest";

import { tooltipWithDisabledClarification } from "../src/lib/disabled-tooltip.js";

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
