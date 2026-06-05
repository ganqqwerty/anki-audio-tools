import { fireEvent, render, screen } from "@testing-library/svelte";
import { describe, expect, it, vi } from "vitest";

import UnitNumberInput from "../src/lib/UnitNumberInput.svelte";
import ValueSlider from "../src/lib/ValueSlider.svelte";

describe("unit-aware controls", () => {
  it("keeps the range input addressable while showing the formatted value on the slider pin", async () => {
    const onValueInput = vi.fn();

    render(ValueSlider, {
      props: {
        formatValue: (value: number) => `${value} dB`,
        max: 40,
        min: 1,
        onValueInput,
        step: 0.5,
        testId: "volume-slider",
        value: 6,
      },
    });

    const slider = screen.getByTestId("volume-slider") as HTMLInputElement;
    expect(slider.type).toBe("range");
    expect(screen.getByText("6 dB")).toBeInTheDocument();
    expect(slider).toHaveAttribute("aria-valuetext", "6 dB");

    await fireEvent.input(slider, { target: { value: "15" } });

    expect(onValueInput).toHaveBeenCalledWith(15);
    expect(screen.getByText("15 dB")).toBeInTheDocument();
    expect(slider).toHaveAttribute("aria-valuetext", "15 dB");
  });

  it("renders units beside numeric inputs without changing the input type or numeric callback", async () => {
    const onValueInput = vi.fn();

    render(UnitNumberInput, {
      props: {
        onValueInput,
        testId: "pause-seconds",
        unit: "s",
        value: 1,
      },
    });

    const input = screen.getByTestId("pause-seconds") as HTMLInputElement;
    expect(input.type).toBe("number");
    expect(input.value).toBe("1");
    expect(input.closest(".aqe-unit-number-input")).toHaveAttribute("data-unit", "s");

    await fireEvent.input(input, { target: { value: "2.5" } });

    expect(input.value).toBe("2.5");
    expect(onValueInput).toHaveBeenCalledWith(2.5);
  });
});
