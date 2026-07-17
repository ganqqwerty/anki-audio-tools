/** Public transport identity, snapshot, and serialized-effect surface. */
export {
  eventInterruptsEffectBatch,
  TRANSPORT_EVENT_IDENTITY,
  transportIdentityScopeFor,
} from "./event-policy.js";
export type { TransportIdentityScope } from "./event-policy.js";
export { TransportIdentityRegistry } from "./identity.js";
export type {
  EditorRuntimeId,
  FieldInstanceId,
  PlaybackAttemptId,
  SourceInstanceId,
  TransportAttemptIdentity,
  TransportFailureIdentity,
  TransportFailureId,
  TransportSourceIdentity,
} from "../transport-public-types.js";
export { transportLifecycleIsActive } from "./model.js";
export type { TransportSnapshot } from "./model.js";
export {
  validateTransportOwnership,
  validateTransportResources,
  validateTransportState,
} from "./validation.js";
export type { TransportResourceSnapshot, TransportViolation } from "./validation.js";
