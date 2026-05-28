import { describe, expect, it } from "vitest";

import {
  frontendUserError,
  isUserFacingError,
  messageFromUnknownError,
} from "../src/lib/user-facing-error.js";

describe("user-facing errors", () => {
  it("recognizes structured coded errors", () => {
    expect(isUserFacingError({ code: "AQE-RUNTIME-001", message: "Missing ffmpeg" })).toBe(true);
    expect(isUserFacingError({ code: "AQE-RUNTIME-001" })).toBe(false);
    expect(isUserFacingError("Missing ffmpeg")).toBe(false);
  });

  it("creates frontend-owned coded errors", () => {
    expect(frontendUserError("AQE-FRONTEND-002", "Unknown async error")).toEqual({
      code: "AQE-FRONTEND-002",
      message: "Unknown async error",
    });
  });

  it("keeps message text from structured and native errors", () => {
    expect(messageFromUnknownError({ code: "AQE-BATCH-001", message: "Invalid batch" })).toBe("Invalid batch");
    expect(messageFromUnknownError(new Error("Native failure"))).toBe("Native failure");
    expect(messageFromUnknownError("string failure")).toBe("string failure");
  });
});
