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
      "Practice the audio from the end, word by word, until you can repeat the whole sentence.",
    );
    expect(within(chorusingPanel).getByText("Move to the next longer chorusing suffix.")).toBeInTheDocument();
    expect(within(chorusingPanel).getByText("Move to the next shorter chorusing suffix.")).toBeInTheDocument();

    const recordingPanel = screen.getByTestId("button-settings-record-play-yours");
    expect(within(recordingPanel).getByTestId("button-settings-record-play-yours-description")).toHaveTextContent(
      "Record your voice for the current graph, then play, share, or show your latest recording.",
    );
    expect(within(recordingPanel).getByText("Record your voice for this graph")).toBeInTheDocument();
    expect(within(recordingPanel).getByText("Play your latest recording")).toBeInTheDocument();
  });
});
