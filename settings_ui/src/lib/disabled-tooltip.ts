export function buttonTooltipContent(
  label: string | null | undefined,
  description: string | null | undefined,
): string {
  const normalizedLabel = (label ?? "").trim();
  const normalizedDescription = (description ?? "").trim();
  if (!normalizedLabel) return normalizedDescription;
  if (!normalizedDescription || normalizedDescription === normalizedLabel) return normalizedLabel;
  return `${normalizedLabel}\n${normalizedDescription}`;
}

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
