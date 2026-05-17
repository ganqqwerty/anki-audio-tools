# mypy: ignore-errors
# ruff: noqa
"""Generated JSON communication contracts. Do not edit by hand."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, List, Dict, Union, TypeVar, Type, cast, Callable


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except (AssertionError, TypeError, ValueError):
            pass
    assert False


def to_float(x: Any) -> float:
    assert isinstance(x, (int, float))
    return x


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
    assert isinstance(x, dict)
    return { k: f(v) for (k, v) in x.items() }


class OutputFormat(Enum):
    MP3 = "mp3"


@dataclass
class Config:
    config_version: int
    debug_logging: bool
    deep_filter_path: str
    deep_filter_post_filter: bool
    enabled: bool
    ffmpeg_path: str
    internal_pause_silence_threshold_db: int
    internal_pause_target_gap_ms: int
    internal_pause_threshold_ms: int
    manual_trim_large_ms: int
    manual_trim_small_ms: int
    max_speed: float
    max_volume_db: float
    min_speed: float
    min_volume_db: float
    output_format: OutputFormat
    repeat_playback_by_default: bool
    show_ffmpeg_commands: bool
    show_graph_by_default: bool
    speed_step: float
    volume_step_db: float
    schema: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Config':
        assert isinstance(obj, dict)
        config_version = from_int(obj.get("_config_version"))
        debug_logging = from_bool(obj.get("debug_logging"))
        deep_filter_path = from_str(obj.get("deep_filter_path"))
        deep_filter_post_filter = from_bool(obj.get("deep_filter_post_filter"))
        enabled = from_bool(obj.get("enabled"))
        ffmpeg_path = from_str(obj.get("ffmpeg_path"))
        internal_pause_silence_threshold_db = from_int(obj.get("internal_pause_silence_threshold_db"))
        internal_pause_target_gap_ms = from_int(obj.get("internal_pause_target_gap_ms"))
        internal_pause_threshold_ms = from_int(obj.get("internal_pause_threshold_ms"))
        manual_trim_large_ms = from_int(obj.get("manual_trim_large_ms"))
        manual_trim_small_ms = from_int(obj.get("manual_trim_small_ms"))
        max_speed = from_float(obj.get("max_speed"))
        max_volume_db = from_float(obj.get("max_volume_db"))
        min_speed = from_float(obj.get("min_speed"))
        min_volume_db = from_float(obj.get("min_volume_db"))
        output_format = OutputFormat(obj.get("output_format"))
        repeat_playback_by_default = from_bool(obj.get("repeat_playback_by_default"))
        show_ffmpeg_commands = from_bool(obj.get("show_ffmpeg_commands"))
        show_graph_by_default = from_bool(obj.get("show_graph_by_default"))
        speed_step = from_float(obj.get("speed_step"))
        volume_step_db = from_float(obj.get("volume_step_db"))
        schema = from_union([from_str, from_none], obj.get("$schema"))
        return Config(config_version, debug_logging, deep_filter_path, deep_filter_post_filter, enabled, ffmpeg_path, internal_pause_silence_threshold_db, internal_pause_target_gap_ms, internal_pause_threshold_ms, manual_trim_large_ms, manual_trim_small_ms, max_speed, max_volume_db, min_speed, min_volume_db, output_format, repeat_playback_by_default, show_ffmpeg_commands, show_graph_by_default, speed_step, volume_step_db, schema)

    def to_dict(self) -> dict:
        result: dict = {}
        result["_config_version"] = from_int(self.config_version)
        result["debug_logging"] = from_bool(self.debug_logging)
        result["deep_filter_path"] = from_str(self.deep_filter_path)
        result["deep_filter_post_filter"] = from_bool(self.deep_filter_post_filter)
        result["enabled"] = from_bool(self.enabled)
        result["ffmpeg_path"] = from_str(self.ffmpeg_path)
        result["internal_pause_silence_threshold_db"] = from_int(self.internal_pause_silence_threshold_db)
        result["internal_pause_target_gap_ms"] = from_int(self.internal_pause_target_gap_ms)
        result["internal_pause_threshold_ms"] = from_int(self.internal_pause_threshold_ms)
        result["manual_trim_large_ms"] = from_int(self.manual_trim_large_ms)
        result["manual_trim_small_ms"] = from_int(self.manual_trim_small_ms)
        result["max_speed"] = to_float(self.max_speed)
        result["max_volume_db"] = to_float(self.max_volume_db)
        result["min_speed"] = to_float(self.min_speed)
        result["min_volume_db"] = to_float(self.min_volume_db)
        result["output_format"] = to_enum(OutputFormat, self.output_format)
        result["repeat_playback_by_default"] = from_bool(self.repeat_playback_by_default)
        result["show_ffmpeg_commands"] = from_bool(self.show_ffmpeg_commands)
        result["show_graph_by_default"] = from_bool(self.show_graph_by_default)
        result["speed_step"] = to_float(self.speed_step)
        result["volume_step_db"] = to_float(self.volume_step_db)
        if self.schema is not None:
            result["$schema"] = from_union([from_str, from_none], self.schema)
        return result


@dataclass
class Payload:
    config: Optional[Config] = None

    @staticmethod
    def from_dict(obj: Any) -> 'Payload':
        assert isinstance(obj, dict)
        config = from_union([Config.from_dict, from_none], obj.get("config"))
        return Payload(config)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.config is not None:
            result["config"] = from_union([lambda x: to_class(Config, x), from_none], self.config)
        return result


@dataclass
class AsyncCommand:
    id: str
    op: str
    payload: Payload

    @staticmethod
    def from_dict(obj: Any) -> 'AsyncCommand':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        op = from_str(obj.get("op"))
        payload = Payload.from_dict(obj.get("payload"))
        return AsyncCommand(id, op, payload)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        result["op"] = from_str(self.op)
        result["payload"] = to_class(Payload, self.payload)
        return result


@dataclass
class AsyncDonePayload:
    id: str
    ok: bool
    result: Optional[Union[bool, float, List[Any], Dict[str, Any], str]] = None
    error: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'AsyncDonePayload':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        ok = from_bool(obj.get("ok"))
        result = from_union([from_none, from_bool, from_float, lambda x: from_list(lambda x: x, x), lambda x: from_dict(lambda x: x, x), from_str], obj.get("result"))
        error = from_union([from_str, from_none], obj.get("error"))
        return AsyncDonePayload(id, ok, result, error)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        result["ok"] = from_bool(self.ok)
        if self.result is not None:
            result["result"] = from_union([from_none, from_bool, to_float, lambda x: from_list(lambda x: x, x), lambda x: from_dict(lambda x: x, x), from_str], self.result)
        if self.error is not None:
            result["error"] = from_union([from_str, from_none], self.error)
        return result


@dataclass
class AsyncProgressPayload:
    id: str
    message: str
    progress: int

    @staticmethod
    def from_dict(obj: Any) -> 'AsyncProgressPayload':
        assert isinstance(obj, dict)
        id = from_str(obj.get("id"))
        message = from_str(obj.get("message"))
        progress = from_int(obj.get("progress"))
        return AsyncProgressPayload(id, message, progress)

    def to_dict(self) -> dict:
        result: dict = {}
        result["id"] = from_str(self.id)
        result["message"] = from_str(self.message)
        result["progress"] = from_int(self.progress)
        return result


@dataclass
class CopySupportReportPayload:
    text: str

    @staticmethod
    def from_dict(obj: Any) -> 'CopySupportReportPayload':
        assert isinstance(obj, dict)
        text = from_str(obj.get("text"))
        return CopySupportReportPayload(text)

    def to_dict(self) -> dict:
        result: dict = {}
        result["text"] = from_str(self.text)
        return result


class Level(Enum):
    DEBUG = "debug"
    ERROR = "error"
    INFO = "info"
    UNKNOWN = "unknown"
    WARN = "warn"


@dataclass
class FrontendLogPayload:
    level: Level
    message: str
    context: Optional[Union[bool, float, List[Any], Dict[str, Any], str]] = None

    @staticmethod
    def from_dict(obj: Any) -> 'FrontendLogPayload':
        assert isinstance(obj, dict)
        level = Level(obj.get("level"))
        message = from_str(obj.get("message"))
        context = from_union([from_none, from_bool, from_float, lambda x: from_list(lambda x: x, x), lambda x: from_dict(lambda x: x, x), from_str], obj.get("context"))
        return FrontendLogPayload(level, message, context)

    def to_dict(self) -> dict:
        result: dict = {}
        result["level"] = to_enum(Level, self.level)
        result["message"] = from_str(self.message)
        if self.context is not None:
            result["context"] = from_union([from_none, from_bool, to_float, lambda x: from_list(lambda x: x, x), lambda x: from_dict(lambda x: x, x), from_str], self.context)
        return result


@dataclass
class ExternalToolHealth:
    available: bool
    error: str
    path: str
    version: str
    model_dir: Optional[str] = None
    model_path: Optional[str] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ExternalToolHealth':
        assert isinstance(obj, dict)
        available = from_bool(obj.get("available"))
        error = from_str(obj.get("error"))
        path = from_str(obj.get("path"))
        version = from_str(obj.get("version"))
        model_dir = from_union([from_str, from_none], obj.get("model_dir"))
        model_path = from_union([from_str, from_none], obj.get("model_path"))
        return ExternalToolHealth(available, error, path, version, model_dir, model_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["available"] = from_bool(self.available)
        result["error"] = from_str(self.error)
        result["path"] = from_str(self.path)
        result["version"] = from_str(self.version)
        if self.model_dir is not None:
            result["model_dir"] = from_union([from_str, from_none], self.model_dir)
        if self.model_path is not None:
            result["model_path"] = from_union([from_str, from_none], self.model_path)
        return result


@dataclass
class HealthReport:
    card_count: int
    collection_available: bool
    deck_count: int
    note_type_count: int
    deep_filter: Optional[ExternalToolHealth] = None
    mp_senet: Optional[ExternalToolHealth] = None

    @staticmethod
    def from_dict(obj: Any) -> 'HealthReport':
        assert isinstance(obj, dict)
        card_count = from_int(obj.get("card_count"))
        collection_available = from_bool(obj.get("collection_available"))
        deck_count = from_int(obj.get("deck_count"))
        note_type_count = from_int(obj.get("note_type_count"))
        deep_filter = from_union([ExternalToolHealth.from_dict, from_none], obj.get("deep_filter"))
        mp_senet = from_union([ExternalToolHealth.from_dict, from_none], obj.get("mp_senet"))
        return HealthReport(card_count, collection_available, deck_count, note_type_count, deep_filter, mp_senet)

    def to_dict(self) -> dict:
        result: dict = {}
        result["card_count"] = from_int(self.card_count)
        result["collection_available"] = from_bool(self.collection_available)
        result["deck_count"] = from_int(self.deck_count)
        result["note_type_count"] = from_int(self.note_type_count)
        if self.deep_filter is not None:
            result["deep_filter"] = from_union([lambda x: to_class(ExternalToolHealth, x), from_none], self.deep_filter)
        if self.mp_senet is not None:
            result["mp_senet"] = from_union([lambda x: to_class(ExternalToolHealth, x), from_none], self.mp_senet)
        return result


@dataclass
class DiagnosticsState:
    addon_id: str
    collection_available: bool

    @staticmethod
    def from_dict(obj: Any) -> 'DiagnosticsState':
        assert isinstance(obj, dict)
        addon_id = from_str(obj.get("addon_id"))
        collection_available = from_bool(obj.get("collection_available"))
        return DiagnosticsState(addon_id, collection_available)

    def to_dict(self) -> dict:
        result: dict = {}
        result["addon_id"] = from_str(self.addon_id)
        result["collection_available"] = from_bool(self.collection_available)
        return result


@dataclass
class InitialState:
    addon_dir: str
    config: Config
    diagnostics: DiagnosticsState
    log_file_path: str
    version: str

    @staticmethod
    def from_dict(obj: Any) -> 'InitialState':
        assert isinstance(obj, dict)
        addon_dir = from_str(obj.get("addon_dir"))
        config = Config.from_dict(obj.get("config"))
        diagnostics = DiagnosticsState.from_dict(obj.get("diagnostics"))
        log_file_path = from_str(obj.get("log_file_path"))
        version = from_str(obj.get("version"))
        return InitialState(addon_dir, config, diagnostics, log_file_path, version)

    def to_dict(self) -> dict:
        result: dict = {}
        result["addon_dir"] = from_str(self.addon_dir)
        result["config"] = to_class(Config, self.config)
        result["diagnostics"] = to_class(DiagnosticsState, self.diagnostics)
        result["log_file_path"] = from_str(self.log_file_path)
        result["version"] = from_str(self.version)
        return result


@dataclass
class ProsodyPayload:
    analyzer_name: str
    duration_ms: int
    points: List[List[Optional[Union[int, float, bool]]]]
    source_filename: str
    pitch_max_hz: Optional[float] = None
    pitch_min_hz: Optional[float] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ProsodyPayload':
        assert isinstance(obj, dict)
        analyzer_name = from_str(obj.get("analyzerName"))
        duration_ms = from_int(obj.get("durationMs"))
        points = from_list(lambda x: from_list(lambda x: from_union([from_int, from_none, from_float, from_bool], x), x), obj.get("points"))
        source_filename = from_str(obj.get("sourceFilename"))
        pitch_max_hz = from_union([from_none, from_float], obj.get("pitchMaxHz"))
        pitch_min_hz = from_union([from_none, from_float], obj.get("pitchMinHz"))
        return ProsodyPayload(analyzer_name, duration_ms, points, source_filename, pitch_max_hz, pitch_min_hz)

    def to_dict(self) -> dict:
        result: dict = {}
        result["analyzerName"] = from_str(self.analyzer_name)
        result["durationMs"] = from_int(self.duration_ms)
        result["points"] = from_list(lambda x: from_list(lambda x: from_union([from_int, from_none, to_float, from_bool], x), x), self.points)
        result["sourceFilename"] = from_str(self.source_filename)
        result["pitchMaxHz"] = from_union([from_none, to_float], self.pitch_max_hz)
        result["pitchMinHz"] = from_union([from_none, to_float], self.pitch_min_hz)
        return result


@dataclass
class SaveErrorPayload:
    error: str

    @staticmethod
    def from_dict(obj: Any) -> 'SaveErrorPayload':
        assert isinstance(obj, dict)
        error = from_str(obj.get("error"))
        return SaveErrorPayload(error)

    def to_dict(self) -> dict:
        result: dict = {}
        result["error"] = from_str(self.error)
        return result


@dataclass
class ShowLogFileResult:
    log_file_path: str

    @staticmethod
    def from_dict(obj: Any) -> 'ShowLogFileResult':
        assert isinstance(obj, dict)
        log_file_path = from_str(obj.get("logFilePath"))
        return ShowLogFileResult(log_file_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["logFilePath"] = from_str(self.log_file_path)
        return result


@dataclass
class SupportReportResult:
    report_text: str

    @staticmethod
    def from_dict(obj: Any) -> 'SupportReportResult':
        assert isinstance(obj, dict)
        report_text = from_str(obj.get("reportText"))
        return SupportReportResult(report_text)

    def to_dict(self) -> dict:
        result: dict = {}
        result["reportText"] = from_str(self.report_text)
        return result


@dataclass
class CommunicationContracts:
    async_command: Optional[AsyncCommand] = None
    async_done_payload: Optional[AsyncDonePayload] = None
    async_progress_payload: Optional[AsyncProgressPayload] = None
    copy_support_report_payload: Optional[CopySupportReportPayload] = None
    frontend_log_payload: Optional[FrontendLogPayload] = None
    health_report: Optional[HealthReport] = None
    initial_state: Optional[InitialState] = None
    prosody_payload: Optional[ProsodyPayload] = None
    save_error_payload: Optional[SaveErrorPayload] = None
    settings_save_payload: Optional[Config] = None
    show_log_file_result: Optional[ShowLogFileResult] = None
    support_report_result: Optional[SupportReportResult] = None

    @staticmethod
    def from_dict(obj: Any) -> 'CommunicationContracts':
        assert isinstance(obj, dict)
        async_command = from_union([AsyncCommand.from_dict, from_none], obj.get("asyncCommand"))
        async_done_payload = from_union([AsyncDonePayload.from_dict, from_none], obj.get("asyncDonePayload"))
        async_progress_payload = from_union([AsyncProgressPayload.from_dict, from_none], obj.get("asyncProgressPayload"))
        copy_support_report_payload = from_union([CopySupportReportPayload.from_dict, from_none], obj.get("copySupportReportPayload"))
        frontend_log_payload = from_union([FrontendLogPayload.from_dict, from_none], obj.get("frontendLogPayload"))
        health_report = from_union([HealthReport.from_dict, from_none], obj.get("healthReport"))
        initial_state = from_union([InitialState.from_dict, from_none], obj.get("initialState"))
        prosody_payload = from_union([ProsodyPayload.from_dict, from_none], obj.get("prosodyPayload"))
        save_error_payload = from_union([SaveErrorPayload.from_dict, from_none], obj.get("saveErrorPayload"))
        settings_save_payload = from_union([Config.from_dict, from_none], obj.get("settingsSavePayload"))
        show_log_file_result = from_union([ShowLogFileResult.from_dict, from_none], obj.get("showLogFileResult"))
        support_report_result = from_union([SupportReportResult.from_dict, from_none], obj.get("supportReportResult"))
        return CommunicationContracts(async_command, async_done_payload, async_progress_payload, copy_support_report_payload, frontend_log_payload, health_report, initial_state, prosody_payload, save_error_payload, settings_save_payload, show_log_file_result, support_report_result)

    def to_dict(self) -> dict:
        result: dict = {}
        if self.async_command is not None:
            result["asyncCommand"] = from_union([lambda x: to_class(AsyncCommand, x), from_none], self.async_command)
        if self.async_done_payload is not None:
            result["asyncDonePayload"] = from_union([lambda x: to_class(AsyncDonePayload, x), from_none], self.async_done_payload)
        if self.async_progress_payload is not None:
            result["asyncProgressPayload"] = from_union([lambda x: to_class(AsyncProgressPayload, x), from_none], self.async_progress_payload)
        if self.copy_support_report_payload is not None:
            result["copySupportReportPayload"] = from_union([lambda x: to_class(CopySupportReportPayload, x), from_none], self.copy_support_report_payload)
        if self.frontend_log_payload is not None:
            result["frontendLogPayload"] = from_union([lambda x: to_class(FrontendLogPayload, x), from_none], self.frontend_log_payload)
        if self.health_report is not None:
            result["healthReport"] = from_union([lambda x: to_class(HealthReport, x), from_none], self.health_report)
        if self.initial_state is not None:
            result["initialState"] = from_union([lambda x: to_class(InitialState, x), from_none], self.initial_state)
        if self.prosody_payload is not None:
            result["prosodyPayload"] = from_union([lambda x: to_class(ProsodyPayload, x), from_none], self.prosody_payload)
        if self.save_error_payload is not None:
            result["saveErrorPayload"] = from_union([lambda x: to_class(SaveErrorPayload, x), from_none], self.save_error_payload)
        if self.settings_save_payload is not None:
            result["settingsSavePayload"] = from_union([lambda x: to_class(Config, x), from_none], self.settings_save_payload)
        if self.show_log_file_result is not None:
            result["showLogFileResult"] = from_union([lambda x: to_class(ShowLogFileResult, x), from_none], self.show_log_file_result)
        if self.support_report_result is not None:
            result["supportReportResult"] = from_union([lambda x: to_class(SupportReportResult, x), from_none], self.support_report_result)
        return result


def communication_contracts_from_dict(s: Any) -> CommunicationContracts:
    return CommunicationContracts.from_dict(s)


def communication_contracts_to_dict(x: CommunicationContracts) -> Any:
    return to_class(CommunicationContracts, x)
