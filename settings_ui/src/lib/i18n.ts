import fallbackMessages from "../../../addon/anki_audio_quick_editor/locales/en.json";

export type Direction = "ltr" | "rtl";
export type Messages = Record<string, string>;

const FALLBACK_MESSAGES = fallbackMessages as Messages;
let activeLocale = "en";
let activeDirection: Direction = "ltr";
let activeMessages: Messages = {};

export function configureI18n(
  locale = "en",
  direction: Direction = "ltr",
  messages: Messages = {},
): void {
  activeLocale = locale || "en";
  activeDirection = direction || "ltr";
  activeMessages = messages || {};
  document.documentElement.lang = activeLocale;
  document.documentElement.dir = activeDirection;
}

export function t(key: string, values: Record<string, unknown> = {}): string {
  const template = activeMessages[key] ?? FALLBACK_MESSAGES[key] ?? key;
  return template.replace(/\{([^{}]+)\}/g, (_match, name: string) => {
    const value = values[name];
    return value === undefined || value === null ? `{${name}}` : String(value);
  });
}

export function locale(): string { return activeLocale; }
export function direction(): Direction { return activeDirection; }
