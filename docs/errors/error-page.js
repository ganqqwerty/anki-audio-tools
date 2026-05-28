const ERROR_COPY = {
  "AQE-MEDIA-001": {
    title: "No sound reference in the current field",
    meaning: "Audio Quick Editor could not find a supported [sound:...] reference in the field you are editing.",
    causes: ["The active field has no audio.", "The first audio reference uses an unsupported file extension.", "The cursor is in a different field than the audio field."],
    fixes: ["Move to a field that contains a supported Anki sound reference.", "Add audio to the field and try again.", "Use Anki's media check if the field content looks correct but playback is broken."]
  },
  "AQE-MEDIA-002": {
    title: "Referenced audio file is missing",
    meaning: "The note points to an audio file that is not present in Anki's media folder.",
    causes: ["The media file was deleted.", "The collection has not finished syncing media.", "The sound tag has a typo."],
    fixes: ["Run Anki media check.", "Restore or re-add the missing audio file.", "Wait for media sync to finish and try again."]
  },
  "AQE-RUNTIME-001": {
    title: "ffmpeg is missing",
    meaning: "Audio Quick Editor could not find ffmpeg.",
    causes: ["The managed runtime is still installing.", "The configured ffmpeg path is wrong.", "ffmpeg is not available in PATH."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Check the configured ffmpeg path.", "Install ffmpeg or make it available in PATH."]
  },
  "AQE-RUNTIME-002": {
    title: "ffprobe is missing",
    meaning: "Audio Quick Editor found ffmpeg but could not find ffprobe for duration inspection.",
    causes: ["ffprobe is not next to ffmpeg.", "The runtime pack is incomplete.", "A custom ffmpeg install omitted ffprobe."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Use an ffmpeg installation that includes ffprobe.", "Check that ffprobe is executable."]
  },
  "AQE-RUNTIME-003": {
    title: "Runtime asset is missing",
    meaning: "A managed or bundled tool or model needed by the selected operation is missing.",
    causes: ["The runtime download did not complete.", "A runtime file was removed.", "This platform is not supported for the selected runtime asset."],
    fixes: ["Open Settings > Diagnostics and run Install/Repair Runtime.", "Copy a support report if repair fails.", "Use a supported macOS or Windows release target."]
  },
  "AQE-AUDIO-001": {
    title: "Audio processing failed",
    meaning: "The audio operation could not complete.",
    causes: ["ffmpeg or another tool returned an error.", "The source file is corrupt or unsupported.", "The selected edit would produce invalid audio."],
    fixes: ["Try playing the original file in Anki.", "Run Settings > Diagnostics > Run Health Check.", "Copy a support report with the exact failing operation."]
  },
  "AQE-PLAYBACK-001": {
    title: "Playback preparation failed",
    meaning: "Audio Quick Editor could not prepare the temporary segment used for playback from a cursor or selection.",
    causes: ["The source media is missing.", "ffmpeg failed to render the temporary segment.", "The requested cursor or selection is outside the audio duration."],
    fixes: ["Try playing from the start.", "Redraw the graph and retry.", "Run diagnostics if playback keeps failing."]
  },
  "AQE-GRAPH-001": {
    title: "Graph analysis failed",
    meaning: "Audio Quick Editor could not analyze pitch and loudness for the selected audio.",
    causes: ["The audio file is missing or unreadable.", "The analyzer failed on this file.", "Runtime tools required for fallback decoding are missing."],
    fixes: ["Try converting the audio to MP3 or WAV.", "Run Settings > Diagnostics > Run Health Check.", "Copy a support report if the file plays but graphing fails."]
  },
  "AQE-RECORDING-001": {
    title: "Voice recording failed",
    meaning: "Recording, saving, or analyzing your comparison recording failed.",
    causes: ["Microphone permission is denied.", "The recording target graph no longer matches the current audio.", "The recorded file could not be saved or analyzed."],
    fixes: ["Check operating system microphone permission for Anki.", "Redraw the graph and record again.", "Copy a support report if recording still fails."]
  },
  "AQE-BATCH-001": {
    title: "Invalid batch request",
    meaning: "The batch dialog could not start because the requested operation or fields were invalid.",
    causes: ["A required source field was not selected.", "A graph operation target field was not selected.", "The frontend sent a malformed request."],
    fixes: ["Choose a source field.", "Choose a target field for graph generation.", "Close and reopen the Browser batch dialog if the controls look stale."]
  },
  "AQE-SETTINGS-001": {
    title: "Invalid settings payload",
    meaning: "The settings dialog sent configuration data that failed validation.",
    causes: ["The dialog bundle and Python contract are out of sync.", "A setting value has an invalid shape.", "The settings window was open across an add-on update."],
    fixes: ["Close and reopen Settings.", "Restart Anki after updating the add-on.", "Copy a support report if saving still fails."]
  },
  "AQE-FRONTEND-001": {
    title: "Invalid frontend async result",
    meaning: "The Svelte interface received a Python async result that did not match the expected contract.",
    causes: ["Frontend and backend contracts are out of sync.", "An async operation returned the wrong result shape."],
    fixes: ["Restart Anki after updating the add-on.", "Copy a support report if the same action still fails."]
  },
  "AQE-FRONTEND-002": {
    title: "Frontend async operation failed",
    meaning: "A settings or diagnostics async operation failed without a more specific user-facing code.",
    causes: ["The backend operation raised an unexpected exception.", "The WebView received a generic failure result."],
    fixes: ["Retry the action once.", "Copy a support report if it fails again."]
  },
  "AQE-FRONTEND-999": {
    title: "Unexpected interface error",
    meaning: "The Svelte interface hit an unexpected runtime error.",
    causes: ["A JavaScript runtime exception occurred.", "The WebView state became inconsistent."],
    fixes: ["Close and reopen the dialog or editor note.", "Restart Anki if the interface remains broken.", "Copy a support report with frontend logs."]
  }
};

function currentCode() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] || "";
}

function renderList(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function renderErrorPage() {
  const code = currentCode();
  const copy = ERROR_COPY[code];
  const root = document.getElementById("error-page");
  if (!root) return;
  if (!copy) {
    root.innerHTML = `<h1>Unknown error code</h1><p>This error code is not documented yet.</p><p><a href="../">All error codes</a></p>`;
    return;
  }
  document.title = `${code}: ${copy.title}`;
  root.innerHTML = `
    <p><a href="../">All error codes</a></p>
    <h1>${code}: ${copy.title}</h1>
    <h2>What It Means</h2>
    <p>${copy.meaning}</p>
    <h2>Common Causes</h2>
    ${renderList(copy.causes)}
    <h2>How To Fix It</h2>
    ${renderList(copy.fixes)}
    <h2>If It Persists</h2>
    <p>Open Settings &gt; Diagnostics and copy a support report before filing a bug.</p>
  `;
}

renderErrorPage();
