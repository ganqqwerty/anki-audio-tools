import "@testing-library/jest-dom";

// ---------------------------------------------------------------------------
// Mock pycmd — Anki's WebView bridge function
// ---------------------------------------------------------------------------
const pycmdMock = vi.fn<(cmd: string) => void>();
(globalThis as unknown as Record<string, unknown>)["pycmd"] = pycmdMock;

// ---------------------------------------------------------------------------
// Reset between tests
// ---------------------------------------------------------------------------
beforeEach(() => {
  pycmdMock.mockReset();

  // Clean up all window.on* callbacks
  delete window.onAsyncProgress;
  delete window.onAsyncDone;
  delete window.onSaveError;

  // Reset __INITIAL_STATE__
  delete window.__INITIAL_STATE__;
});

// Re-export pycmd mock so tests can inspect calls
export { pycmdMock };
