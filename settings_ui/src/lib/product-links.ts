const GITHUB_PAGES_URL = "https://ganqqwerty.github.io/anki-audio-tools/";

function githubPagesPath(path: string): string {
  return `${GITHUB_PAGES_URL}${path}`;
}

export const PRODUCT_LINKS = {
  bugReport: githubPagesPath("go/bug-report/"),
  discord: githubPagesPath("go/discord/"),
  editorVideos: {
    batchProcessing: githubPagesPath("go/video-batch-processing/"),
    convert: githubPagesPath("go/video-convert/"),
    denoise: githubPagesPath("go/video-denoise/"),
    graph: githubPagesPath("go/video-graph/"),
    pauseShortening: githubPagesPath("go/video-shorten-pauses/"),
    pitchHum: githubPagesPath("go/video-pitch-hum/"),
    playback: githubPagesPath("go/video-play/"),
    recordVoice: githubPagesPath("go/video-record-voice/"),
    share: githubPagesPath("go/video-share/"),
    speed: githubPagesPath("go/video-speed/"),
    volume: githubPagesPath("go/video-volume/"),
  },
  githubPages: GITHUB_PAGES_URL,
  ideaRequest: githubPagesPath("go/idea-request/"),
  patreon: githubPagesPath("go/patreon/"),
  telegram: githubPagesPath("go/telegram/"),
} as const;

export const DOCUMENTATION_SECTION_LINKS = Object.values(PRODUCT_LINKS.editorVideos);
