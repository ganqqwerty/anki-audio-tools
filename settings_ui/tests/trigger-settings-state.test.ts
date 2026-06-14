import { describe, expect, it } from "vitest";

import {
  AudioTriggerRuleOperation,
  GraphVoiceRange,
  OutputFormat,
  TriggerEvent,
} from "../src/lib/types.js";
import { newTriggerRule, validateTriggerRules } from "../src/settings/trigger-settings-state.js";
import { defaultConfig } from "./settings-app-helpers.js";

describe("trigger settings state", () => {
  it("creates a normalized operation trigger from note type metadata", () => {
    const rule = newTriggerRule(
      { ...defaultConfig, output_format: OutputFormat.FLAC },
      { note_types: [{ id: 123, name: "Basic", fields: ["Audio", "Graph"] }] },
      (prefix) => `${prefix}-1`,
    );

    expect(rule.id).toBe("trigger-1");
    expect(rule.event).toBe(TriggerEvent.Add);
    expect(rule.note_type).toEqual({ id: 123, name: "Basic" });
    expect(rule.source_field).toBe("Audio");
    expect(rule.operation).toBe(AudioTriggerRuleOperation.Convert);
    expect(rule.parameters.target_format).toBe(OutputFormat.FLAC);
  });

  it("validates graph rules that are missing a target field", () => {
    const rule = newTriggerRule(
      { ...defaultConfig, graph_voice_range: GraphVoiceRange.High },
      { note_types: [{ id: 123, name: "Basic", fields: ["Audio", "Graph"] }] },
      (prefix) => `${prefix}-1`,
    );
    rule.operation = AudioTriggerRuleOperation.Graph;
    rule.target_field = null;

    expect(validateTriggerRules([rule], { note_types: [{ id: 123, name: "Basic", fields: ["Audio", "Graph"] }] }, [])).toEqual([
      { ruleId: "trigger-1", message: "New trigger needs a graph target field." },
    ]);
  });
});
