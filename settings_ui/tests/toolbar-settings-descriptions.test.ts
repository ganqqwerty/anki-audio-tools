import { render, screen, within } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import App from "../src/App.svelte";
import { setInitialState } from "./settings-app-helpers.js";

describe("toolbar settings descriptions", () => {
  it("shows panel and button descriptions in grouped toolbar settings", () => {
    setInitialState();

    render(App);

    const chorusingPanel = screen.getByTestId("button-settings-chorusing");
    expect(within(chorusingPanel).getByTestId("button-settings-chorusing-description")).toHaveTextContent(
      "Move the selected region between practice markers.",
    );
    expect(within(chorusingPanel).getByText("Move the selection start to the previous marker.")).toBeInTheDocument();
    expect(within(chorusingPanel).getByText("Move the selection start to the next marker.")).toBeInTheDocument();

    const recordingPanel = screen.getByTestId("button-settings-record-play-yours");
    expect(within(recordingPanel).getByTestId("button-settings-record-play-yours-description")).toHaveTextContent(
      "Record your voice for the current graph, then play, share, or show your latest recording.",
    );
    expect(within(recordingPanel).getByText("Record your voice for this graph")).toBeInTheDocument();
    expect(within(recordingPanel).getByText("Play your latest recording")).toBeInTheDocument();
  });
});
