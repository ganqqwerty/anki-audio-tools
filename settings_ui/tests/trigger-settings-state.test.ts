import { describe, expect, it } from "vitest";

import {
  AudioTriggerActionType,
  AudioTriggerRuleOperation,
  GraphVoiceRange,
  Operation,
  OutputFormat,
  TriggerEvent,
} from "../src/lib/types.js";
import {
  newTriggerRule,
  normalizeTriggerRule,
  parametersForTriggerOperation,
  validateTriggerRules,
} from "../src/settings/trigger-settings-state.js";
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

  it("clears a stale graph target when selecting a transform-only preset", () => {
    const config = {
      ...defaultConfig,
      audio_processing_presets: [
        {
          id: "clean",
          name: "Clean",
          steps: [
            {
              id: "convert",
              operation: Operation.Convert,
              parameters: { target_format: OutputFormat.FLAC },
            },
          ],
          graph: {
            enabled: false,
            parameters: {
              graph_voice_range: defaultConfig.graph_voice_range,
              graph_recording_condition: defaultConfig.graph_recording_condition,
              graph_smoothness: defaultConfig.graph_smoothness,
              graph_connect_short_dropouts_ms: defaultConfig.graph_connect_short_dropouts_ms,
              graph_voice_lock: defaultConfig.graph_voice_lock,
            },
          },
        },
      ],
    };
    const rule = newTriggerRule(
      config,
      { note_types: [{ id: 123, name: "Basic", fields: ["Audio", "Graph"] }] },
      (prefix) => `${prefix}-1`,
    );

    const normalized = normalizeTriggerRule(
      {
        ...rule,
        action_type: AudioTriggerActionType.Preset,
        operation: null,
        preset_id: "clean",
        target_field: "Graph",
      },
      config,
    );

    expect(normalized.target_field).toBeNull();
  });

  it("captures operation-specific defaults when the selected action changes", () => {
    const rule = newTriggerRule(
      defaultConfig,
      { note_types: [{ id: 123, name: "Basic", fields: ["Audio"] }] },
      (prefix) => `${prefix}-1`,
    );

    const normalized = normalizeTriggerRule(
      { ...rule, operation: AudioTriggerRuleOperation.Faster },
      defaultConfig,
    );

    expect(normalized.parameters).toEqual({ speed_step: defaultConfig.speed_step });
  });

  it.each([
    [
      AudioTriggerRuleOperation.ReduceSize,
      {
        size_reduction_mode: defaultConfig.size_reduction_mode,
        size_reduction_bitrate_kbps: defaultConfig.size_reduction_bitrate_kbps,
        size_reduction_sample_rate_hz: defaultConfig.size_reduction_sample_rate_hz,
        size_reduction_channels: defaultConfig.size_reduction_channels,
      },
    ],
    [
      AudioTriggerRuleOperation.Denoise,
      {
        denoise_algorithm: defaultConfig.denoise_algorithm,
        dpdfnet_attn_limit_db: defaultConfig.dpdfnet_attn_limit_db,
      },
    ],
    [
      AudioTriggerRuleOperation.RemovePauses,
      {
        pause_aggressiveness: defaultConfig.pause_aggressiveness,
        pause_detection_algorithm: defaultConfig.pause_detection_algorithm,
        pause_threshold: defaultConfig.pause_silencedetect_threshold_db,
        pause_min_silence_seconds: defaultConfig.pause_silencedetect_min_silence_seconds,
        pause_min_speech_seconds: defaultConfig.pause_silencedetect_min_speech_seconds,
        pause_preprocess_denoise: defaultConfig.pause_silencedetect_preprocess_denoise,
      },
    ],
    [AudioTriggerRuleOperation.VolumeUp, { volume_step_db: defaultConfig.volume_step_db }],
    [
      AudioTriggerRuleOperation.Graph,
      {
        graph_voice_range: defaultConfig.graph_voice_range,
        graph_recording_condition: defaultConfig.graph_recording_condition,
        graph_smoothness: defaultConfig.graph_smoothness,
        graph_connect_short_dropouts_ms: defaultConfig.graph_connect_short_dropouts_ms,
        graph_voice_lock: defaultConfig.graph_voice_lock,
      },
    ],
    [null, {}],
  ])("captures defaults for the %s trigger action", (operation, expected) => {
    expect(parametersForTriggerOperation(operation, defaultConfig)).toEqual(expected);
  });

  it("validates graph target fields removed from the selected note type", () => {
    const metadata = { note_types: [{ id: 123, name: "Basic", fields: ["Audio"] }] };
    const rule = newTriggerRule(defaultConfig, metadata, (prefix) => `${prefix}-1`);
    rule.operation = AudioTriggerRuleOperation.Graph;
    rule.target_field = "Deleted Graph";

    expect(validateTriggerRules([rule], metadata, [])).toContainEqual({
      ruleId: "trigger-1",
      message: "New trigger graph target field is unavailable.",
    });
  });
});
