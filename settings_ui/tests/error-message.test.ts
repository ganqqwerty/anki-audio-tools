import { fireEvent, render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import ErrorMessage from "../src/lib/ErrorMessage.svelte";
import { errorHelpUrl } from "../src/lib/error-links.js";
import { pycmdMock } from "./setup.js";

describe("ErrorMessage", () => {
  it("renders plain string errors without help links", () => {
    render(ErrorMessage, { props: { error: "Plain failure" } });

    expect(screen.getByText("Plain failure")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Help" })).not.toBeInTheDocument();
  });

  it("renders coded errors with visible help link", () => {
    render(ErrorMessage, {
      props: {
        error: {
          code: "AQE-RUNTIME-001",
          message: "Audio Quick Editor requires ffmpeg.",
        },
      },
    });

    expect(screen.getByText(/AQE-RUNTIME-001:/)).toBeInTheDocument();
    expect(screen.getByText(/Audio Quick Editor requires ffmpeg/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      errorHelpUrl("AQE-RUNTIME-001"),
    );
  });

  it("opens coded-error help through the shared webview bridge", async () => {
    render(ErrorMessage, {
      props: {
        error: {
          code: "AQE-RUNTIME-001",
          message: "Audio Quick Editor requires ffmpeg.",
        },
      },
    });

    await fireEvent.click(screen.getByRole("link", { name: "Help" }));

    const url = errorHelpUrl("AQE-RUNTIME-001");
    expect(pycmdMock).toHaveBeenCalledWith(
      `bridge:{"command":"webview.open_url","payload":{"url":"${url}"}}`,
    );
  });
});
