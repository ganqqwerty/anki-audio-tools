workspace {

    model {
        user = person "Anki User"
        anki = softwareSystem "Anki Desktop" "" "" {
            anki_editor = container "Anki Editor" "" "Python + PyQt"
            anki_reviewer = container "Anki Reviewer" "" "Python + PyQt"
            anki_browser = container "Anki Browser" "" "Python + PyQt"
            anki_collection = container "Anki Collection" "" "SQLite + media folder"
        }
        aqe = softwareSystem "Audio Quick Editor" "" "" {
            python_addon = container "Python Addon" "" "Python 3.13" "" {
                # ---- Entry Point ----
                entry_point = component "Entry Point" "" "__init__.py — startup hooks, menu, logging"

                # ---- Editor Subsystem ----
                editor_integration = component "Editor Integration" "" "editor_integration.py — hook registration, _links[] wiring"
                editor_bridge = component "Editor Bridge" "" "editor_bridge.py + editor_actions.py — command decode/dispatch"
                editor_callbacks = component "Editor Callbacks" "" "editor_callbacks.py + editor_dependencies.py — DI callbacks"
                editor_processing = component "Editor Processing" "" "editor_processing.py + editor_analysis + editor_conversion"
                editor_playback = component "Editor Playback" "" "editor_playback.py + playback_request + playback_bounds"
                editor_recording = component "Editor Recording" "" "editor_recording.py + recording_analysis + recording_frontend"
                editor_region_delete = component "Editor Region Delete" "" "editor_region_delete.py + request + worker"
                editor_special_transforms = component "Editor Special Transforms" "" "editor_special_transforms.py"
                editor_history = component "Editor History" "" "editor_history.py + editor_persistent_undo.py"
                editor_session = component "Editor Session" "" "editor_session.py + editor_runtime.py — mutable state bag"
                editor_frontend_bridge = component "Editor Frontend Bridge" "" "editor_frontend/ — evalWithCallback, busy, playback, refresh"
                editor_ui = component "Editor UI Injection" "" "editor_ui.py + editor_webview_injection.py"
                editor_misc = component "Editor Misc" "" "editor_media, sharing, split_defaults, source_metadata, button_visibility"

                # ---- Browser Subsystem ----
                browser_integration = component "Browser Integration" "" "browser_integration.py — menu/context hooks"
                browser_dialog = component "Browser Dialog" "" "browser_dialog.py — WebView shell + bridge"
                browser_runner = component "Browser Batch Runner" "" "browser_batch_runner.py — taskman background"
                browser_state = component "Browser State" "" "browser_dialog_state.py + browser_report.py"

                # ---- Reviewer Subsystem ----
                reviewer_adapter = component "Reviewer Adapter" "" "reviewer_integration.py — wraps reviewer bridge"

                # ---- Settings Subsystem ----
                settings_shell = component "Settings Shell" "" "settings/__init__.py — thin QDialog + AnkiWebView"
                settings_backend = component "Settings Backend" "" "settings/commands.py + async_commands + initial_state"

                # ---- Audio Core ----
                audio_processor = component "Audio Processor Facade" "" "audio_processor.py — side-effect boundary"
                audio_rendering = component "Audio Rendering" "" "audio_rendering.py + audio_commands — ffmpeg pipelines"
                audio_noise_reduction = component "Noise Reduction" "" "audio_noise_reduction.py — DeepFilterNet, RNNoise, DPDFNet, Voice Only"
                audio_pitch_hum = component "Pitch/Hum Synthesis" "" "audio_pitch_hum.py + frames + synthesis"
                audio_pause_pipeline = component "Pause Shortening" "" "audio_pause_pipeline.py — Silencedetect + Silero VAD"
                audio_operations = component "Audio Operations" "" "audio_operations.py — shared batchable ops"
                audio_state = component "Audio State & Types" "" "audio_state.py + audio_types + audio_formats + operation_params"
                audio_tools = component "Audio Tools" "" "audio_tools.py + deps + external + output_policy + size_reduction"
                audio_artifacts = component "Audio Artifacts" "" "audio_artifacts.py — artifact dir management"
                batch_operations = component "Batch Operations" "" "batch_operations.py + types + processing + helpers"

                # ---- Prosody ----
                prosody = component "Prosody Analysis" "" "prosody_analyzer.py + cache + svg + fallback + praat"

                # ---- Bridge Infrastructure ----
                webview_bridge = component "Shared Bridge" "" "webview_bridge.py — bridge:{json} envelope decode"
                webview_shell = component "WebView Shell" "" "webview_shell.py — HTML render, stdHtml, initial state"

                # ---- Infrastructure ----
                diagnostics = component "Diagnostics" "" "diagnostics_runtime.py + storage + JSON"
                config_migration = component "Config & Migration" "" "config_migration.py + config.schema.json"
                support = component "Support & Errors" "" "support.py + reporting + error_codes + errors"
                frontend_logs = component "Frontend Logs" "" "frontend_logs.py — log ingestion from 3 bundles"
                i18n = component "i18n" "" "i18n.py — locale catalogs"
                external_links = component "External Links" "" "external_links.py — trusted URL dispatch"

                # ---- Managed Runtime ----
                runtime_manager = component "Runtime Manager" "" "runtime_manager.py — download, verify, extract"
                runtime_install = component "Runtime Install" "" "runtime_install.py + manifest + installer_dialog"
            }

            svelte_webviews = container "Svelte WebViews" "" "TypeScript + Svelte 5" "" {
                # ---- Settings App ----
                settings_root = component "Settings App Root" "" "main.ts + App.svelte + SettingsApp.svelte"
                settings_panels = component "Settings Panels" "" "General, Graph, Button, Toolbar, Diagnostics panels"
                settings_state = component "Settings State" "" "settings-state.ts"

                # ---- Editor Inline ----
                editor_inline = component "Editor Inline App" "" "settings_ui/src/editor-inline/ — ~110 files, 3 entry points"
                editor_controls = component "Editor Controls" "" "EditorControls.svelte — per-field root"
                editor_toolbar = component "Editor Toolbar" "" "EditorToolbarButton/Panel.svelte + CommandIcon + SplitButton"
                editor_graph = component "Graph Visualizer" "" "GraphVisualizer.svelte + split options + promoted defaults"
                editor_playback_ctrl = component "Playback Controller" "" "playback-controller.ts + state + progress clock"
                editor_selection = component "Selection Controller" "" "selection-controller.ts + gestures + marker shift"
                editor_recording_ui = component "Recording UI" "" "recording-state.ts + actions + lifecycle"
                editor_region_del = component "Region Delete UI" "" "region-delete.ts + state"
                editor_chorusing = component "Chorusing" "" "chorusing-controller + DOM + state + toolbar"
                editor_split_state = component "Split Button State" "" "split-button-state*.ts + presenters + formatters"
                editor_field_state = component "Field State" "" "field-state.ts + store + DOM sync"
                editor_viewport = component "Viewport & Zoom" "" "time-viewport.ts + zoom + scroller"
                editor_runtime = component "Editor Runtime" "" "runtime.ts — initialization, dispose"
                editor_bridge_ts = component "Editor Bridge (TS)" "" "bridge.ts + window-contract.ts — pycmd, queues"

                # ---- Batch App ----
                batch_app = component "Batch App" "" "main.ts + BatchApp.svelte + BatchControls + FieldSelectors"
                batch_state = component "Batch State" "" "batch-state.ts"

                # ---- Shared Library ----
                shared_bridge = component "Shared Bridge (TS)" "" "lib/bridge.ts — bridge:{json} envelope"
                shared_types = component "Shared Types" "" "lib/types.ts + generated/contracts.ts"
                shared_ui = component "Shared UI Components" "" "lib/AqeTooltip, SplitButton, ValueSlider, UnitNumberInput, icons"
                shared_utils = component "Shared Utils" "" "lib/async-jobs, audio-operation-parameters, tooltips, i18n"
            }

            managed_runtime = container "Managed Runtime" "" "ffmpeg DeepFilterNet RNNoise" "" {
                ffmpeg = component "ffmpeg / ffprobe" "" ""
                deepfilter = component "DeepFilterNet3" "" ""
                rnnoise = component "RNNoise" "" ""
            }
        }

        # ---- Relationships ----
        user -> anki_editor "edits cards"
        user -> anki_reviewer "reviews cards"
        user -> anki_browser "browses cards"

        entry_point -> anki_editor "gui_hooks"
        entry_point -> anki_reviewer "gui_hooks"
        entry_point -> anki_browser "gui_hooks"

        # Editor subsystem relationships
        entry_point -> editor_integration "registers hooks"
        editor_integration -> editor_bridge "wires _links[]"
        editor_bridge -> editor_callbacks "dispatches commands"
        editor_callbacks -> editor_processing "update_state_and_render()"
        editor_callbacks -> editor_playback "play/stop"
        editor_callbacks -> editor_recording "record/stop"
        editor_callbacks -> editor_region_delete "delete"
        editor_callbacks -> editor_special_transforms "denoise/convert"
        editor_callbacks -> editor_history "undo/redo"
        editor_callbacks -> editor_misc "share/settings/source_metadata"
        editor_processing -> audio_processor "processes audio"
        editor_playback -> editor_session "updates state"
        editor_session -> editor_frontend_bridge "evalWithCallback"
        editor_frontend_bridge -> editor_bridge_ts "window.__aqe*"
        editor_bridge_ts -> editor_controls "mounts controls"
        editor_ui -> editor_inline "injects bundle"
        editor_inline -> editor_controls "renders"
        editor_inline -> editor_toolbar "toolbar"
        editor_inline -> editor_graph "visualizer"
        editor_inline -> editor_playback_ctrl "playback"

        editor_integration -> editor_ui "injects on note load"
        editor_bridge -> editor_frontend_bridge "bridge callbacks"
        editor_callbacks -> editor_session "reads/writes state"
        editor_recording -> editor_frontend_bridge "recording state"
        editor_processing -> audio_artifacts "artifact dir"
        editor_special_transforms -> audio_noise_reduction "denoise"
        editor_special_transforms -> audio_rendering "convert"

        # Audio core relationships
        audio_processor -> audio_rendering "ffmpeg render"
        audio_processor -> audio_noise_reduction "denoise"
        audio_processor -> audio_pitch_hum "synthesis"
        audio_processor -> audio_pause_pipeline "pause shorten"
        audio_processor -> audio_artifacts "artifact dir"
        audio_processor -> audio_tools "tools"
        audio_operations -> audio_processor "execute"
        audio_state -> audio_processor "AudioEditState"
        audio_noise_reduction -> managed_runtime "subprocess"
        audio_rendering -> managed_runtime "subprocess"
        audio_pause_pipeline -> audio_noise_reduction "optional pre-denoise"

        # Prosody
        prosody -> audio_processor "analysis input"

        # Browser subsystem
        entry_point -> browser_integration "registers menus"
        browser_integration -> browser_dialog "opens dialog"
        browser_dialog -> browser_runner "start batch"
        browser_runner -> batch_operations "process notes"
        batch_operations -> audio_processor "execute"
        browser_state -> browser_dialog "initial state"
        browser_dialog -> webview_shell "render HTML"
        browser_dialog -> batch_app "mounts batch UI"

        # Reviewer subsystem
        entry_point -> reviewer_adapter "registers hooks"
        reviewer_adapter -> editor_bridge "delegates bridge"

        # Settings subsystem
        entry_point -> settings_shell "setConfigAction"
        settings_shell -> settings_backend "bridge dispatch"
        settings_backend -> config_migration "save config"
        settings_backend -> diagnostics "runtime status"
        settings_shell -> webview_shell "render HTML"
        settings_shell -> settings_root "mounts settings UI"

        # Bridge infrastructure
        webview_bridge -> settings_backend "decode bridge:{json}"
        webview_bridge -> browser_dialog "decode bridge:{json}"
        webview_shell -> shared_bridge "injects pycmd bridge"
        editor_bridge_ts -> editor_bridge "pycmd('aqe:*')"
        shared_bridge -> webview_bridge "pycmd('bridge:{json}')"

        # Svelte internal relationships
        settings_root -> settings_panels "composes"
        settings_panels -> settings_state "reads/writes"
        settings_state -> shared_bridge "sends commands"
        shared_bridge -> shared_types "contracts"

        editor_controls -> editor_toolbar "toolbar"
        editor_controls -> editor_graph "visualizer"
        editor_controls -> editor_playback_ctrl "playback"
        editor_controls -> editor_selection "selection"
        editor_controls -> editor_recording_ui "recording"
        editor_controls -> editor_region_del "region delete"
        editor_controls -> editor_chorusing "chorusing"
        editor_controls -> editor_viewport "viewport"
        editor_controls -> editor_field_state "state"
        editor_controls -> editor_runtime "init/dispose"
        editor_controls -> editor_bridge_ts "bridge"
        editor_split_state -> editor_bridge_ts "save defaults"
        editor_graph -> editor_split_state "split options"
        editor_playback_ctrl -> editor_bridge_ts "playback requests"

        batch_app -> batch_state "state"
        batch_app -> shared_bridge "bridge"
        batch_state -> shared_types "types"

        shared_ui -> shared_utils "helpers"
        shared_utils -> shared_types "types"

        # Infrastructure
        diagnostics -> config_migration "log level from config"
        support -> diagnostics "reporting"
        frontend_logs -> diagnostics "ingest"

        runtime_manager -> managed_runtime "downloads, verifies"
        runtime_install -> managed_runtime "extracts"
        diagnostics -> runtime_manager "status"

        # Editor → Audio
        editor_processing -> audio_operations "shared ops"
        editor_special_transforms -> audio_operations "shared ops"
        browser_runner -> audio_operations "shared ops"
    }

    views {
        systemContext aqe "1-SystemContext" {
            include *
            autoLayout lr
        }

        container aqe "2-Container" {
            include *
            autoLayout lr
        }

        component python_addon "3-PythonComponents-Overview" {
            include *
            autoLayout lr
        }

        component python_addon "4-PythonModules-Editor" {
            include entry_point editor_integration editor_bridge editor_callbacks
            include editor_processing editor_playback editor_recording editor_region_delete
            include editor_special_transforms editor_history editor_session
            include editor_frontend_bridge editor_ui editor_misc
            include audio_processor audio_rendering audio_noise_reduction audio_operations
            include audio_state audio_artifacts prosody
            include editor_bridge_ts editor_controls
            autoLayout lr
        }

        component python_addon "5-PythonModules-Audio" {
            include audio_processor audio_rendering audio_noise_reduction
            include audio_pitch_hum audio_pause_pipeline audio_operations
            include audio_state audio_tools audio_artifacts batch_operations
            include prosody managed_runtime
            autoLayout lr
        }

        component python_addon "6-PythonModules-Infra" {
            include entry_point webview_bridge webview_shell diagnostics
            include config_migration support frontend_logs i18n external_links
            include runtime_manager runtime_install managed_runtime
            include settings_shell settings_backend
            autoLayout lr
        }

        component svelte_webviews "7-SvelteComponents-Overview" {
            include *
            autoLayout lr
        }

        component svelte_webviews "8-SvelteModules-Editor" {
            include editor_controls editor_toolbar editor_graph
            include editor_playback_ctrl editor_selection editor_recording_ui
            include editor_region_del editor_chorusing editor_split_state
            include editor_field_state editor_viewport editor_runtime
            include editor_bridge_ts
            autoLayout lr
        }

        styles {
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "External" {
                background #999999
                color #ffffff
            }
        }
    }
}
