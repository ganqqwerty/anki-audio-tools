const soundStartPattern = /\[sound:/gi;
const supportedPattern = /\.(aac|flac|m4a|mp3|oga|ogg|opus|wav|webm)(?:[\s.]*)$/i;

export function audioSourceFromHtml(html: string): string {
  const starts = Array.from(html.matchAll(soundStartPattern));
  for (let index = 0; index < starts.length; index += 1) {
    const match = starts[index];
    if (!match) continue;
    const filenameStart = (match.index ?? -1) + match[0].length;
    if (filenameStart < match[0].length) continue;
    const nextStart = starts[index + 1]?.index ?? html.length;
    const filenameEnd = soundReferenceFilenameEnd(html, filenameStart, nextStart);
    if (filenameEnd < 0) continue;
    const filename = html.slice(filenameStart, filenameEnd);
    if (supportedPattern.test(filename)) return filename;
  }
  return "";
}

export function audioSourceForNode(node: HTMLElement | null | undefined): string {
  if (!node) return "";
  return audioSourceFromHtml(node.textContent || node.innerHTML || "");
}

function soundReferenceFilenameEnd(html: string, filenameStart: number, searchLimit: number): number {
  const firstClose = html.indexOf("]", filenameStart);
  if (firstClose < 0 || firstClose >= searchLimit) return -1;
  let bestSupportedClose = -1;
  let close = firstClose;
  while (close >= 0 && close < searchLimit) {
    const filename = html.slice(filenameStart, close);
    if (supportedPattern.test(filename)) bestSupportedClose = close;
    close = html.indexOf("]", close + 1);
  }
  return bestSupportedClose >= 0 ? bestSupportedClose : firstClose;
}
