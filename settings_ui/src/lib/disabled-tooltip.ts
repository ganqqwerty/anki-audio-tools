export function tooltipWithDisabledClarification(
  content: string | null | undefined,
  disabledReason: string | null | undefined,
): string {
  const base = (content ?? "").trim();
  const reason = (disabledReason ?? "").trim();
  if (!reason) return base;
  if (!base) return reason;
  if (base.includes(reason)) return base;
  return `${base}\n\n${reason}`;
}
