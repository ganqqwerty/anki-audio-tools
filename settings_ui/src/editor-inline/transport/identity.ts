import type {
  EditorRuntimeId,
  FieldInstanceId,
  PlaybackAttemptId,
  SourceInstanceId,
  TransportAttemptIdentity,
  TransportFailureId,
  TransportFailureIdentity,
  TransportSourceIdentity,
} from "../transport-public-types.js";

export type {
  EditorRuntimeId,
  FieldInstanceId,
  PlaybackAttemptId,
  SourceInstanceId,
  TransportAttemptIdentity,
  TransportFailureId,
  TransportFailureIdentity,
  TransportSourceIdentity,
} from "../transport-public-types.js";

interface FieldIdentitySlot {
  readonly fieldInstanceId: FieldInstanceId;
  sourceIdentity: TransportSourceIdentity | null;
  attemptIdentity: TransportAttemptIdentity | null;
  failureIdentity: TransportFailureIdentity | null;
  sourceBindingKey: string | null;
}

/** Allocates and validates transport identities for one editor runtime. */
export class TransportIdentityRegistry {
  readonly runtimeId: EditorRuntimeId;

  private nextId = 1;
  private readonly fields = new Map<number, FieldIdentitySlot>();

  constructor() {
    this.runtimeId = this.allocateEditorRuntimeId();
  }

  mountField(ord: number): FieldInstanceId {
    const existing = this.fields.get(ord);
    if (existing) return existing.fieldInstanceId;
    const fieldInstanceId = this.allocateFieldInstanceId();
    this.fields.set(ord, {
      attemptIdentity: null,
      failureIdentity: null,
      fieldInstanceId,
      sourceBindingKey: null,
      sourceIdentity: null,
    });
    return fieldInstanceId;
  }

  remountField(ord: number): FieldInstanceId {
    this.fields.delete(ord);
    return this.mountField(ord);
  }

  unmountField(ord: number): void {
    this.fields.delete(ord);
  }

  clearSource(ord: number): void {
    const field = this.fields.get(ord);
    if (!field) return;
    field.sourceBindingKey = null;
    field.sourceIdentity = null;
    field.attemptIdentity = null;
    field.failureIdentity = null;
  }

  bindSource(ord: number, bindingKey: string, replace = false): TransportSourceIdentity {
    const field = this.fieldSlot(ord);
    if (!replace && field.sourceIdentity && field.sourceBindingKey === bindingKey) {
      return field.sourceIdentity;
    }
    const sourceIdentity: TransportSourceIdentity = Object.freeze({
      fieldInstanceId: field.fieldInstanceId,
      runtimeId: this.runtimeId,
      sourceInstanceId: this.allocateSourceInstanceId(),
    });
    field.sourceBindingKey = bindingKey;
    field.sourceIdentity = sourceIdentity;
    field.attemptIdentity = null;
    field.failureIdentity = null;
    return sourceIdentity;
  }

  beginAttempt(ord: number): TransportAttemptIdentity | null {
    const field = this.fields.get(ord);
    if (!field?.sourceIdentity) return null;
    const attemptIdentity: TransportAttemptIdentity = Object.freeze({
      ...field.sourceIdentity,
      attemptId: this.allocatePlaybackAttemptId(),
    });
    field.attemptIdentity = attemptIdentity;
    field.failureIdentity = null;
    return attemptIdentity;
  }

  registerFailure(ord: number): TransportFailureIdentity | null {
    const field = this.fields.get(ord);
    if (!field?.sourceIdentity) return null;
    const failureIdentity: TransportFailureIdentity = Object.freeze({
      ...field.sourceIdentity,
      attemptId: field.attemptIdentity?.attemptId ?? null,
      failureId: this.allocateTransportFailureId(),
    });
    field.attemptIdentity = null;
    field.failureIdentity = failureIdentity;
    return failureIdentity;
  }

  clearAttempt(ord: number): void {
    const field = this.fields.get(ord);
    if (field) field.attemptIdentity = null;
  }

  currentSource(ord: number): TransportSourceIdentity | null {
    return this.fields.get(ord)?.sourceIdentity ?? null;
  }

  currentAttempt(ord: number): TransportAttemptIdentity | null {
    return this.fields.get(ord)?.attemptIdentity ?? null;
  }

  currentFailure(ord: number): TransportFailureIdentity | null {
    return this.fields.get(ord)?.failureIdentity ?? null;
  }

  acceptsSource(ord: number, identity: TransportSourceIdentity): boolean {
    const current = this.currentSource(ord);
    return current !== null && sourceIdentityEquals(current, identity);
  }

  acceptsAttempt(ord: number, identity: TransportAttemptIdentity): boolean {
    const current = this.currentAttempt(ord);
    return current !== null
      && sourceIdentityEquals(current, identity)
      && current.attemptId === identity.attemptId;
  }

  acceptsFailure(ord: number, identity: TransportFailureIdentity): boolean {
    const current = this.currentFailure(ord);
    return current !== null
      && sourceIdentityEquals(current, identity)
      && current.failureId === identity.failureId;
  }

  claimFailure(ord: number, identity: TransportFailureIdentity): boolean {
    if (!this.acceptsFailure(ord, identity)) return false;
    const field = this.fields.get(ord);
    if (field) field.failureIdentity = null;
    return true;
  }

  dispose(): void {
    this.fields.clear();
  }

  private fieldSlot(ord: number): FieldIdentitySlot {
    this.mountField(ord);
    return this.fields.get(ord)!;
  }

  private allocateEditorRuntimeId(): EditorRuntimeId {
    return this.nextId++ as EditorRuntimeId;
  }

  private allocateFieldInstanceId(): FieldInstanceId {
    return this.nextId++ as FieldInstanceId;
  }

  private allocateSourceInstanceId(): SourceInstanceId {
    return this.nextId++ as SourceInstanceId;
  }

  private allocatePlaybackAttemptId(): PlaybackAttemptId {
    return this.nextId++ as PlaybackAttemptId;
  }

  private allocateTransportFailureId(): TransportFailureId {
    return this.nextId++ as TransportFailureId;
  }
}

function sourceIdentityEquals(left: TransportSourceIdentity, right: TransportSourceIdentity): boolean {
  return left.runtimeId === right.runtimeId
    && left.fieldInstanceId === right.fieldInstanceId
    && left.sourceInstanceId === right.sourceInstanceId;
}
