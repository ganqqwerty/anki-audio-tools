/** Identity values that cross the transport package boundary. */
export type EditorRuntimeId = number & { readonly __editorRuntimeId: unique symbol };
export type FieldInstanceId = number & { readonly __fieldInstanceId: unique symbol };
export type SourceInstanceId = number & { readonly __sourceInstanceId: unique symbol };
export type PlaybackAttemptId = number & { readonly __playbackAttemptId: unique symbol };
export type TransportFailureId = number & { readonly __transportFailureId: unique symbol };

export interface TransportSourceIdentity {
  readonly runtimeId: EditorRuntimeId;
  readonly fieldInstanceId: FieldInstanceId;
  readonly sourceInstanceId: SourceInstanceId;
}

export interface TransportAttemptIdentity extends TransportSourceIdentity {
  readonly attemptId: PlaybackAttemptId;
}

export interface TransportFailureIdentity extends TransportSourceIdentity {
  readonly attemptId: PlaybackAttemptId | null;
  readonly failureId: TransportFailureId;
}
