import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mock pycmd — Anki's WebView bridge function
// ---------------------------------------------------------------------------
const pycmdMock = vi.fn<(cmd: string) => void>();
(globalThis as unknown as Record<string, unknown>)["pycmd"] = pycmdMock;

const clipboardWriteTextMock = vi.fn<(text: string) => Promise<void>>();
Object.defineProperty(globalThis.navigator, "clipboard", {
  configurable: true,
  value: {
    writeText: clipboardWriteTextMock,
  },
});

// ---------------------------------------------------------------------------
// Reset between tests
// ---------------------------------------------------------------------------
beforeEach(() => {
  pycmdMock.mockReset();
  clipboardWriteTextMock.mockReset();

  // Clean up all window.on* callbacks
  delete window.onAsyncProgress;
  delete window.onAsyncDone;
  delete window.onSaveError;

  // Reset __INITIAL_STATE__
  delete window.__INITIAL_STATE__;
  delete window.__AQE_EDITOR_CONFIG__;
});

// Re-export pycmd mock so tests can inspect calls
export { clipboardWriteTextMock, pycmdMock };
