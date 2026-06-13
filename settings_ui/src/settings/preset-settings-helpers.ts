import {
  pauseDetectionAlgorithmOrDefault,
  pausePreset,
} from "$lib/audio-operation-parameters.js";
import { t } from "$lib/i18n.js";
import {
  Operation,
  type AudioProcessingPreset,
  type AudioProcessingPresetGraphParameters,
  type AudioProcessingPresetParameters,
  type AudioProcessingPresetStep,
  type Config,
  type PauseAggressiveness,
} from "$lib/types.js";

export const TRANSFORM_OPERATIONS = [
  Operation.Denoise,
  Operation.RemovePauses,
  Operation.Convert,
  Operation.Slower,
  Operation.Faster,
  Operation.VolumeDown,
  Operation.VolumeUp,
] as const;

export function operationLabel(operation: Operation): string {
  return t(`operation.${operation}`);
}

export function graphParametersFromConfig(config: Config): AudioProcessingPresetGraphParameters {
  return {
    graph_voice_range: config.graph_voice_range,
    graph_recording_condition: config.graph_recording_condition,
    graph_smoothness: config.graph_smoothness,
    graph_connect_short_dropouts_ms: config.graph_connect_short_dropouts_ms,
    graph_voice_lock: config.graph_voice_lock,
      };
    }

export function parametersForOperation(
  operation: Operation,
  config: Config,
): AudioProcessingPresetParameters {
  if (operation === Operation.Convert) return { target_format: config.output_format };
  if (operation === Operation.Denoise) {
    return {
      denoise_algorithm: config.denoise_algorithm,
      dpdfnet_attn_limit_db: config.dpdfnet_attn_limit_db,
    };
  }
  if (operation === Operation.RemovePauses) {
    const algorithm = pauseDetectionAlgorithmOrDefault(config.pause_detection_algorithm);
      return {
        pause_aggressiveness: config.pause_aggressiveness,
        pause_detection_algorithm: algorithm as Config["pause_detection_algorithm"],
      pause_threshold: algorithm === "silero_vad"
        ? config.pause_silero_threshold
        : config.pause_silencedetect_threshold_db,
      pause_min_silence_seconds: algorithm === "silero_vad"
        ? config.pause_silero_min_silence_seconds
        : config.pause_silencedetect_min_silence_seconds,
      pause_min_speech_seconds: algorithm === "silero_vad"
        ? config.pause_silero_min_speech_seconds
        : config.pause_silencedetect_min_speech_seconds,
      pause_preprocess_denoise: algorithm === "silero_vad"
        ? config.pause_silero_preprocess_denoise
        : config.pause_silencedetect_preprocess_denoise,
    };
  }
  if (operation === Operation.Slower || operation === Operation.Faster) return { speed_step: config.speed_step };
  if (operation === Operation.VolumeDown || operation === Operation.VolumeUp) return { volume_step_db: config.volume_step_db };
  return {};
}

export function newStep(
  operation: Operation,
  config: Config,
  idFactory: (prefix: string) => string,
): AudioProcessingPresetStep {
  return {
    id: idFactory("step"),
    operation,
    parameters: parametersForOperation(operation, config),
  };
}

export function applyPauseAggressiveness(
  step: AudioProcessingPresetStep,
  value: PauseAggressiveness,
): void {
  const algorithm = pauseDetectionAlgorithmOrDefault(step.parameters.pause_detection_algorithm);
  const preset = pausePreset(algorithm, value);
  step.parameters.pause_aggressiveness = value;
  step.parameters.pause_threshold = preset.threshold;
  step.parameters.pause_min_silence_seconds = preset.minSilenceSeconds;
  step.parameters.pause_min_speech_seconds = preset.minSpeechSeconds;
  step.parameters.pause_preprocess_denoise = preset.preprocessDenoise;
}

export function validatePresets(presets: AudioProcessingPreset[]): string[] {
  const messages: string[] = [];
  const names = new Map<string, number>();
  for (const preset of presets) {
    const name = preset.name.trim();
    if (!name) messages.push(t("settings.presets.validation.empty_name"));
    if (preset.steps.length === 0 && !preset.graph.enabled) {
      messages.push(t("settings.presets.validation.empty_preset", { name: name || "?" }));
    }
    const key = name.toLowerCase();
    if (key) names.set(key, (names.get(key) ?? 0) + 1);
  }
  for (const [name, count] of names) {
    if (count > 1) messages.push(t("settings.presets.validation.duplicate_name", { name }));
  }
  return messages;
}
