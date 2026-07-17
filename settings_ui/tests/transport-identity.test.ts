import { describe, expect, it } from "vitest";

import { TransportIdentityRegistry } from "../src/editor-inline/transport/identity.js";

describe("transport identity registry", () => {
  it("mounts idempotently and exposes no source-scoped identity before binding", () => {
    const registry = new TransportIdentityRegistry();
    const mounted = registry.mountField(0);

    expect(registry.mountField(0)).toBe(mounted);
    expect(registry.currentSource(0)).toBeNull();
    expect(registry.currentAttempt(0)).toBeNull();
    expect(registry.currentFailure(0)).toBeNull();
    expect(registry.beginAttempt(0)).toBeNull();
    expect(registry.registerFailure(0)).toBeNull();
    const unmounted = new TransportIdentityRegistry();
    expect(unmounted.beginAttempt(0)).toBeNull();
    expect(unmounted.registerFailure(0)).toBeNull();
    unmounted.clearAttempt(0);
    unmounted.clearSource(0);
  });

  it("preserves source identity for a redundant binding and replaces it explicitly", () => {
    const registry = new TransportIdentityRegistry();
    registry.mountField(0);

    const first = registry.bindSource(0, "source:voice.mp3");
    expect(registry.bindSource(0, "source:voice.mp3")).toBe(first);

    const replacement = registry.bindSource(0, "source:voice.mp3", true);
    expect(replacement.sourceInstanceId).not.toBe(first.sourceInstanceId);
    expect(registry.acceptsSource(0, first)).toBe(false);
    expect(registry.acceptsSource(0, replacement)).toBe(true);

    const differentBinding = registry.bindSource(0, "source:other.mp3");
    expect(differentBinding.sourceInstanceId).not.toBe(replacement.sourceInstanceId);
  });

  it("rejects callbacks from an older field mount even when the ordinal is reused", () => {
    const registry = new TransportIdentityRegistry();
    registry.mountField(0);
    const oldSource = registry.bindSource(0, "source:same.mp3");
    const oldAttempt = registry.beginAttempt(0)!;

    const remountedField = registry.remountField(0);
    const newSource = registry.bindSource(0, "source:same.mp3");
    const newAttempt = registry.beginAttempt(0)!;

    expect(newSource.fieldInstanceId).toBe(remountedField);
    expect(newSource.fieldInstanceId).not.toBe(oldSource.fieldInstanceId);
    expect(registry.acceptsSource(0, oldSource)).toBe(false);
    expect(registry.acceptsAttempt(0, oldAttempt)).toBe(false);
    expect(registry.acceptsAttempt(0, newAttempt)).toBe(true);
  });

  it("accepts only the latest play attempt regardless of promise settlement order", () => {
    const registry = new TransportIdentityRegistry();
    registry.bindSource(0, "source:voice.mp3");
    const first = registry.beginAttempt(0)!;
    const second = registry.beginAttempt(0)!;

    expect(registry.acceptsAttempt(0, first)).toBe(false);
    expect(registry.acceptsAttempt(0, second)).toBe(true);
    expect(registry.currentAttempt(0)).toBe(second);

    registry.clearAttempt(0);
    expect(registry.currentAttempt(0)).toBeNull();
    expect(registry.acceptsAttempt(0, second)).toBe(false);
  });

  it("claims only the current failure and invalidates it on source replacement", () => {
    const registry = new TransportIdentityRegistry();
    registry.bindSource(0, "source:voice.aac");
    const first = registry.registerFailure(0)!;
    const second = registry.registerFailure(0)!;

    expect(registry.acceptsFailure(0, first)).toBe(false);
    expect(registry.acceptsFailure(0, second)).toBe(true);
    expect(registry.currentFailure(0)).toBe(second);
    expect(second.attemptId).toBeNull();
    expect(registry.claimFailure(0, first)).toBe(false);
    expect(registry.claimFailure(0, second)).toBe(true);
    expect(registry.acceptsFailure(0, second)).toBe(false);

    registry.bindSource(0, "source:voice.aac", true);
    expect(registry.acceptsFailure(0, second)).toBe(false);
  });

  it("carries the current attempt into a registered failure", () => {
    const registry = new TransportIdentityRegistry();
    registry.bindSource(0, "source:voice.aac");
    const attempt = registry.beginAttempt(0)!;

    expect(registry.registerFailure(0)?.attemptId).toBe(attempt.attemptId);
  });

  it("clears source, attempt, and failure identities together", () => {
    const registry = new TransportIdentityRegistry();
    const source = registry.bindSource(0, "source:voice.mp3");
    const attempt = registry.beginAttempt(0)!;
    const failure = registry.registerFailure(0)!;

    registry.clearSource(0);

    expect(registry.currentSource(0)).toBeNull();
    expect(registry.currentAttempt(0)).toBeNull();
    expect(registry.currentFailure(0)).toBeNull();
    expect(registry.acceptsSource(0, source)).toBe(false);
    expect(registry.acceptsAttempt(0, attempt)).toBe(false);
    expect(registry.acceptsFailure(0, failure)).toBe(false);
  });

  it.each(["runtimeId", "fieldInstanceId", "sourceInstanceId"] as const)(
    "rejects a source identity with a different %s",
    (key) => {
      const registry = new TransportIdentityRegistry();
      const source = registry.bindSource(0, "source:voice.mp3");
      const mismatched = { ...source, [key]: source[key] + 100 };

      expect(registry.acceptsSource(0, mismatched)).toBe(false);
    },
  );

  it("rejects every identity after unmount and disposal", () => {
    const registry = new TransportIdentityRegistry();
    const source = registry.bindSource(0, "source:voice.mp3");
    const attempt = registry.beginAttempt(0)!;
    const failure = registry.registerFailure(0)!;

    registry.unmountField(0);
    expect(registry.acceptsSource(0, source)).toBe(false);
    expect(registry.acceptsAttempt(0, attempt)).toBe(false);
    expect(registry.acceptsFailure(0, failure)).toBe(false);

    const nextSource = registry.bindSource(0, "source:voice.mp3");
    registry.dispose();
    expect(registry.acceptsSource(0, nextSource)).toBe(false);
  });
});
