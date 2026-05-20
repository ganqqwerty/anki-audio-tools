const soundPattern = /\[sound:([^\]]+)\]/i;
const supportedPattern = /\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)$/i;

export function audioSourceFromHtml(html: string): string {
  const match = soundPattern.exec(html);
  const filename = match?.[1];
  return filename && supportedPattern.test(filename) ? filename : "";
}

export function audioSourceForNode(node: HTMLElement | null | undefined): string {
  if (!node) return "";
  return audioSourceFromHtml(node.innerHTML || node.textContent || "");
}
