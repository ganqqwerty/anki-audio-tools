import { fireEvent, render, screen } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import SettingsDisabledTooltipHarness from "./fixtures/SettingsDisabledTooltipHarness.svelte";

describe("settings disabled tooltip clarification", () => {
  it("combines locked mode checkbox label with the locked-panel reason", () => {
    render(SettingsDisabledTooltipHarness, { props: { variant: "button-card" } });

    const checkbox = screen.getByTestId("button-settings-test-mode-icon");
    const tooltip = checkbox.closest<HTMLElement>(".field-tooltip-target");

    expect(checkbox).toBeDisabled();
    expect(tooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Show this toolbar item as an icon instead of text.\n\nThis display setting is locked because the button belongs to a grouped toolbar panel.",
    );
  });

  it("keeps disabled settings choices hoverable with description plus reason", async () => {
    const onSelect = vi.fn();
    render(SettingsDisabledTooltipHarness, { props: { onSelect, variant: "choice-group" } });

    const button = screen.getByTestId("choice-a");
    const tooltip = button.closest<HTMLElement>(".field-tooltip-target");

    expect(button).toBeDisabled();
    expect(button).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Option A\nDoes the thing.\n\nDisabled because another option is active.",
    );
    expect(tooltip).toHaveAttribute(
      "data-aqe-tooltip-content",
      "Option A\nDoes the thing.\n\nDisabled because another option is active.",
    );

    await fireEvent.click(button);
    expect(onSelect).not.toHaveBeenCalled();
  });
});
