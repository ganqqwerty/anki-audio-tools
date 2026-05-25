const GITHUB_PAGES_URL = "https://ganqqwerty.github.io/anki-audio-tools/";

export const PRODUCT_LINKS = {
  bugReport: "https://tally.so/r/2EDlxA",
  discord: "https://discord.gg/qkg52pp2",
  editorVideos: {
    convert: `${GITHUB_PAGES_URL}#video-convert`,
    denoise: `${GITHUB_PAGES_URL}#video-denoise`,
    graph: `${GITHUB_PAGES_URL}#video-graph`,
    pauseShortening: `${GITHUB_PAGES_URL}#video-shorten-pauses`,
    pitchHum: `${GITHUB_PAGES_URL}#video-pitch-hum`,
    playback: `${GITHUB_PAGES_URL}#video-play`,
    share: `${GITHUB_PAGES_URL}#video-share`,
    speed: `${GITHUB_PAGES_URL}#video-speed`,
    volume: `${GITHUB_PAGES_URL}#video-volume`,
  },
  githubPages: GITHUB_PAGES_URL,
  ideaRequest: "https://tally.so/r/zx1Gr8",
  patreon: "https://patreon.com/YuriAnker",
  telegram: "https://t.me/immersionjp",
} as const;

export const DOCUMENTATION_SECTION_LINKS = Object.values(PRODUCT_LINKS.editorVideos);
