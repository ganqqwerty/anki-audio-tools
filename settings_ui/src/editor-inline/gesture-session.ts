export interface GestureSessionHandlers {
  lostPointerCaptureTarget: EventTarget;
  onCancel: () => void;
  onPointerMove: (event: PointerEvent) => void;
  onPointerUp: (event: PointerEvent) => void;
}

export function startGestureSession(handlers: GestureSessionHandlers): void {
  let active = true;

  const cleanup = (): void => {
    if (!active) return;
    active = false;
    window.removeEventListener("pointermove", pointerMove);
    window.removeEventListener("pointerup", pointerUp);
    window.removeEventListener("pointercancel", cancel);
    window.removeEventListener("keydown", keydown);
    window.removeEventListener("blur", cancel);
    handlers.lostPointerCaptureTarget.removeEventListener("lostpointercapture", cancel);
  };

  const pointerMove = (event: PointerEvent): void => {
    if (active) {
      handlers.onPointerMove(event);
    }
  };

  const pointerUp = (event: PointerEvent): void => {
    if (!active) return;
    cleanup();
    handlers.onPointerUp(event);
  };

  const cancel = (): void => {
    if (!active) return;
    cleanup();
    handlers.onCancel();
  };

  const keydown = (event: KeyboardEvent): void => {
    if (event.key === "Escape") {
      cancel();
    }
  };

  window.addEventListener("pointermove", pointerMove);
  window.addEventListener("pointerup", pointerUp);
  window.addEventListener("pointercancel", cancel);
  window.addEventListener("keydown", keydown);
  window.addEventListener("blur", cancel);
  handlers.lostPointerCaptureTarget.addEventListener("lostpointercapture", cancel);
}
