"""Inline editor UI JavaScript for Audio Quick Editor."""

from __future__ import annotations

import json


def injection_script(audio_field_indices: list[int] | None = None) -> str:
    """Return JavaScript that mounts compact controls next to audio fields."""
    field_indices_json = json.dumps(audio_field_indices or [])
    return f"""
(function() {{
  const soundPattern = /\\[sound:([^\\]]+)\\]/i;
  const supportedPattern = /\\.(mp3|wav|ogg)$/i;
  const audioFieldIndices = new Set({field_indices_json});
  const processingCommands = new Set([
    "aqe:trim-left",
    "aqe:untrim-left",
    "aqe:trim-right",
    "aqe:untrim-right",
    "aqe:slower",
    "aqe:faster",
    "aqe:trim-silence",
    "aqe:remove-pauses"
  ]);
  const styleId = "aqe-inline-style";

  function ensureStyle() {{
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = {json.dumps(_css())};
    document.head.appendChild(style);
  }}

  function fieldNodes() {{
    const candidates = Array.from(document.querySelectorAll('[contenteditable="true"], .field, [data-field-ord]'));
    const seen = new Set();
    return candidates.filter((node) => {{
      if (seen.has(node)) return false;
      seen.add(node);
      return node.textContent || node.innerHTML;
    }});
  }}

  function explicitFieldTargets() {{
    return Array.from(audioFieldIndices)
      .map((ord) => {{
        const container = document.querySelector(`.field-container[data-index="${{ord}}"]`);
        if (!container) return null;
        return {{
          ord,
          node: container.querySelector('[contenteditable="true"]') || container
        }};
      }})
      .filter(Boolean);
  }}

  function fieldIndex(node, fallback) {{
    const attrs = ["data-field-ord", "data-ord", "data-index"];
    for (const attr of attrs) {{
      const raw = node.getAttribute && node.getAttribute(attr);
      if (raw !== null && raw !== undefined && /^\\d+$/.test(raw)) return Number(raw);
    }}
    const idMatch = String(node.id || "").match(/(\\d+)/);
    return idMatch ? Number(idMatch[1]) : fallback;
  }}

  function send(command, node, ord) {{
    const controls = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    if (controls && controls.dataset.busy === "true") return;
    if (node && typeof node.focus === "function") node.focus();
    window.__aqeActiveField = ord;
    if (processingCommands.has(command)) setControlsBusy(ord, true, "Processing...");
    if (typeof pycmd === "function") {{
      pycmd("focus:" + ord);
      pycmd(command);
    }}
  }}

  function makeButton(label, title, command, node, ord) {{
    const button = document.createElement("button");
    button.type = "button";
    button.className = "aqe-button";
    button.dataset.aqeCommand = command;
    button.textContent = label;
    button.title = title;
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => send(command, node, ord));
    return button;
  }}

  function statusNode() {{
    const span = document.createElement("span");
    span.className = "aqe-status";
    span.textContent = "";
    return span;
  }}

  function controlsFor(node, ord) {{
    const wrapper = document.createElement("div");
    wrapper.className = "aqe-controls";
    wrapper.dataset.aqeFieldOrd = String(ord);
    wrapper.append(
      makeButton("▶", "Play current audio", "aqe:play", node, ord),
      makeButton("-L", "Trim 100 ms from left", "aqe:trim-left", node, ord),
      makeButton("+L", "Undo 100 ms left trim", "aqe:untrim-left", node, ord),
      makeButton("-R", "Trim 100 ms from right", "aqe:trim-right", node, ord),
      makeButton("+R", "Undo 100 ms right trim", "aqe:untrim-right", node, ord),
      makeButton("Trim Silence", "Trim leading and trailing silence", "aqe:trim-silence", node, ord),
      makeButton("Remove Pauses", "Compress long internal pauses", "aqe:remove-pauses", node, ord),
      makeButton("Slower", "Decrease speed", "aqe:slower", node, ord),
      makeButton("Faster", "Increase speed", "aqe:faster", node, ord),
      makeButton("Undo", "Restore the previous generated audio reference", "aqe:undo", node, ord),
      statusNode()
    );
    return wrapper;
  }}

  function mountNear(node, ord) {{
    const existing = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    if (existing) existing.remove();
    const parent = node.closest && node.closest(".field-container")
      ? node.closest(".field-container")
      : node.closest && node.closest(".field")
        ? node.closest(".field")
        : node.parentElement;
    const controls = controlsFor(node, ord);
    if (parent && parent.parentElement) {{
      parent.insertAdjacentElement("afterend", controls);
    }} else {{
      node.insertAdjacentElement("afterend", controls);
    }}
  }}

  function scan() {{
    ensureStyle();
    document.querySelectorAll(".aqe-controls").forEach((node) => node.remove());
    const explicitTargets = explicitFieldTargets();
    if (explicitTargets.length) {{
      explicitTargets.forEach((target) => mountNear(target.node, target.ord));
      return;
    }}
    fieldNodes().forEach((node, fallback) => {{
      const html = node.innerHTML || node.textContent || "";
      const match = html.match(soundPattern);
      if (!match || !supportedPattern.test(match[1])) return;
      mountNear(node, fieldIndex(node, fallback));
    }});
  }}

  function controlsForOrd(ord) {{
    const controls = document.querySelector(`.aqe-controls[data-aqe-field-ord="${{ord}}"]`);
    return controls;
  }}

  function setControlsBusy(ord, busy, message, command) {{
    const controls = controlsForOrd(ord);
    if (!controls) return;
    controls.dataset.busy = busy ? "true" : "false";
    controls.querySelectorAll(".aqe-button").forEach((button) => {{
      button.disabled = !!busy;
    }});
    const status = controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = busy ? "processing" : "info";
    status.title = command || "";
  }}

  window.__aqeSetBusy = setControlsBusy;

  window.__aqeSetStatus = function(message, kind) {{
    const ord = window.__aqeActiveField;
    const controls = controlsForOrd(ord);
    const status = controls && controls.querySelector(".aqe-status");
    if (!status) return;
    status.textContent = message || "";
    status.dataset.kind = kind || "info";
  }};

  window.__aqeScan = scan;
  setTimeout(scan, 0);
  setTimeout(scan, 250);
  setTimeout(scan, 1000);
}})();
"""


def _css() -> str:
    return """
.aqe-controls {
  align-items: center;
  border: 1px solid;
  border-radius: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 4px 0 10px;
  padding: 6px 8px;
}
.aqe-button {
  border: 1px solid;
  border-radius: 7px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 8px;
}
.aqe-button:hover {
  text-decoration: underline;
}
.aqe-status {
  font-size: 12px;
  margin-left: 4px;
}
.aqe-status[data-kind="error"] {
  font-weight: 700;
}
"""
