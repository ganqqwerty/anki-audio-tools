import { describe, expect, it, vi } from "vitest";

import { startGestureSession } from "../src/editor-inline/gesture-session.js";

function pointerEvent(type: string): PointerEvent {
  const EventCtor = window.PointerEvent || window.MouseEvent;
  return new EventCtor(type, { bubbles: true }) as PointerEvent;
}

describe("gesture session", () => {
  it("routes pointer move and pointer up before removing session listeners", () => {
    const captureTarget = document.createElement("div");
    const onPointerMove = vi.fn();
    const onPointerUp = vi.fn();
    const onCancel = vi.fn();

    startGestureSession({
      lostPointerCaptureTarget: captureTarget,
      onCancel,
      onPointerMove,
      onPointerUp,
    });

    window.dispatchEvent(pointerEvent("pointermove"));
    window.dispatchEvent(pointerEvent("pointerup"));
    window.dispatchEvent(pointerEvent("pointermove"));

    expect(onPointerMove).toHaveBeenCalledTimes(1);
    expect(onPointerUp).toHaveBeenCalledTimes(1);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("dispatches cancel once for Escape, blur, pointer cancel, or capture loss", () => {
    const captureTarget = document.createElement("div");
    const onPointerMove = vi.fn();
    const onPointerUp = vi.fn();
    const onCancel = vi.fn();

    startGestureSession({
      lostPointerCaptureTarget: captureTarget,
      onCancel,
      onPointerMove,
      onPointerUp,
    });

    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Enter" }));
    window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, key: "Escape" }));
    window.dispatchEvent(new Event("blur"));
    window.dispatchEvent(pointerEvent("pointercancel"));
    captureTarget.dispatchEvent(pointerEvent("lostpointercapture"));
    window.dispatchEvent(pointerEvent("pointerup"));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onPointerMove).not.toHaveBeenCalled();
    expect(onPointerUp).not.toHaveBeenCalled();
  });

  it("dispatches cancel from non-keyboard interruption paths", () => {
    const dispatchCancelers: Array<(captureTarget: EventTarget) => boolean> = [
      () => window.dispatchEvent(pointerEvent("pointercancel")),
      () => window.dispatchEvent(new Event("blur")),
      (captureTarget: EventTarget) => captureTarget.dispatchEvent(pointerEvent("lostpointercapture")),
    ];

    for (const dispatchCancel of dispatchCancelers) {
      const captureTarget = document.createElement("div");
      const onCancel = vi.fn();

      startGestureSession({
        lostPointerCaptureTarget: captureTarget,
        onCancel,
        onPointerMove: vi.fn(),
        onPointerUp: vi.fn(),
      });

      dispatchCancel(captureTarget);

      expect(onCancel).toHaveBeenCalledTimes(1);
    }
  });
});
