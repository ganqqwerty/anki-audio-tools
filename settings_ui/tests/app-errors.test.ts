import { render, screen, waitFor, within } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import App from "../src/App.svelte";
import { PRODUCT_LINKS } from "../src/lib/product-links.js";
import { pycmdMock, setInitialState } from "./settings-app-helpers.js";

describe("App error rendering", () => {
  it("renders coded settings save errors with visible help link", async () => {
    setInitialState();
    render(App);

    window.onSaveError?.({
      error: "Invalid settings payload",
      user_error: { code: "AQE-SETTINGS-001", message: "Invalid settings payload" },
    });

    const error = await screen.findByTestId("save-error");
    expect(error).toHaveTextContent("AQE-SETTINGS-001: Invalid settings payload");
    expect(within(error).getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-SETTINGS-001/`,
    );
  });

  it("shows a visible coded error when the settings frontend throws", async () => {
    setInitialState();
    render(App);

    await waitFor(() => expect(pycmdMock()).toHaveBeenCalled());
    window.dispatchEvent(new ErrorEvent("error", { message: "boom" }));

    const error = await screen.findByTestId("frontend-runtime-error");
    expect(error).toHaveTextContent("AQE-FRONTEND-999: The interface hit an unexpected error. Help");
    expect(within(error).getByRole("link", { name: "Help" })).toHaveAttribute(
      "href",
      `${PRODUCT_LINKS.githubPages}errors/AQE-FRONTEND-999/`,
    );
  });
});
