export interface UserFacingError {
  code: string;
  message: string;
  details?: string;
}

export type ErrorDisplayValue = string | UserFacingError;

export const AQE_FRONTEND_INVALID_ASYNC_RESULT = "AQE-FRONTEND-001";
export const AQE_FRONTEND_UNKNOWN_ASYNC_ERROR = "AQE-FRONTEND-002";
export const AQE_FRONTEND_UNEXPECTED = "AQE-FRONTEND-999";

export function isUserFacingError(value: unknown): value is UserFacingError {
  return (
    typeof value === "object"
    && value !== null
    && !Array.isArray(value)
    && typeof (value as { code?: unknown }).code === "string"
    && typeof (value as { message?: unknown }).message === "string"
  );
}

export function frontendUserError(code: string, message: string, details?: string): UserFacingError {
  return details ? { code, message, details } : { code, message };
}

export function messageFromUnknownError(error: unknown): string {
  if (isUserFacingError(error)) return error.message;
  if (error instanceof Error) return error.message;
  return String(error);
}
