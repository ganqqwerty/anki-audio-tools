import {
    prepareForNewNote,
    requestDefaultGraph,
    requestPendingGraphRedraw,
} from "./actions.js";
import {
    clearDefaultGraphQueue,
    enqueueDefaultGraphs,
} from "./default-graph-queue.js";
import {configureI18n} from "../lib/i18n.js";
import {
    disposeAllControllers,
    mountController,
} from "./field-controller.js";
import {logger} from "./logger.js";
import {
    installReviewerPanelTriggers,
    reviewTargetIsOpen,
} from "./reviewer-panel-trigger.js";
import {
    editorRuntimeConfig,
    setEditorRuntimeConfig,
} from "./editor-runtime-config.js";
import {audioSourceForNode} from "./sound-source.js";
import type {EditorRuntimeConfig, FieldTarget} from "./types.js";
import {installEditorWindowContract} from "./window-contract.js";
import {isEditorBusy, resetEditorControlState} from "./editor-control-state.js";
import {clearLearnerRecordingStateStore} from "./recording-state-store.js";
import {stopAllLearnerRecordingHtmlPlayback} from "./learner-recording-playback.js";
import {clearVisualizerRuntimeStates} from "./visualizer-runtime-state.js";
import {projectEditorBusyState} from "./control-actions.js";
import {
    disposePostEditPlaybackReadiness,
    notifyPostEditPlaybackReady,
    resetPostEditPlaybackReadiness,
} from "./post-edit-playback.js";
import {
    clearAllHtmlAudioSessions,
    htmlAudioSessionSourceFilename,
    initializeHtmlAudioTransportRuntime,
    setHtmlAudioTransportSnapshotSink,
} from "./html-audio-session-controller.js";
import type {TransportSnapshot} from "./transport/index.js";
import {
    disposeEditorPracticeRuntime,
    initializeEditorPracticeRuntime,
} from "./editor-practice-controller.js";
import {
    disposeEditorIntentController,
    initializeEditorIntentController,
} from "./editor-intent-controller.js";
import {disposeGraphCountdownOverlays} from "./graph-countdown-overlay.js";
import {disposeRecordingProjections} from "./recording-actions-state.js";
import {clearChorusingStates} from "./chorusing-state-store.js";

let scheduledScanTimers: number[] = [];
let mutationScanTimer: number | null = null;
let editorDomObserver: MutationObserver | null = null;
let globalErrorHandlersInstalled = false;

const FIELD_SCAN_SELECTOR = '.field-container, .field, [contenteditable="true"], [data-field-ord], .aqe-review-audio-target';

export {audioSourceForNode} from "./sound-source.js";

export function initializeEditorRuntime(config: EditorRuntimeConfig = editorRuntimeConfig()): void {
    disposeEditorRuntime();
    initializeHtmlAudioTransportRuntime();
    setHtmlAudioTransportSnapshotSink(handleHtmlTransportSnapshot);
    initializeEditorPracticeRuntime();
    setEditorRuntimeConfig(config);
    initializeEditorIntentController();
    configureI18n(config.locale, config.direction, config.messages);
    installGlobalErrorHandlers();
    installEditorWindowContract();
    prepareForNewNote();
    resetPostEditPlaybackReadiness();
    clearDefaultGraphQueue();
    window.__aqeEditorDispose = disposeEditorRuntime;
    logger.info("editor runtime initialized", {
        audioFieldIndices: config.audioFieldIndices,
        showGraphByDefault: config.showGraphByDefault === true,
    });
    const scanWithConfig = (): void => scan(config);
    window.__aqeScan = scanWithConfig;
    scheduleScan(scanWithConfig, 0);
    scheduleScan(scanWithConfig, 250);
    scheduleScan(scanWithConfig, 1000);
    installEditorDomObserver(scanWithConfig);
}

function installGlobalErrorHandlers(): void {
    if (globalErrorHandlersInstalled) return;
    globalErrorHandlersInstalled = true;
    window.addEventListener("error", (event) => {
        logger.error(event.message || "unknown editor frontend error", {
            filename: event.filename,
            lineno: event.lineno,
            colno: event.colno,
            stack: event.error instanceof Error ? event.error.stack : "",
        });
    });
    window.addEventListener("unhandledrejection", (event) => {
        const reason = event.reason;
        logger.error(`Unhandled rejection: ${reason instanceof Error ? reason.message : String(reason)}`, {
            stack: reason instanceof Error ? reason.stack : "",
        });
    });
}

export function disposeEditorRuntime(): void {
    scheduledScanTimers.forEach((timer) => window.clearTimeout(timer));
    scheduledScanTimers = [];
    if (mutationScanTimer !== null) {
        window.clearTimeout(mutationScanTimer);
        mutationScanTimer = null;
    }
    editorDomObserver?.disconnect();
    editorDomObserver = null;
    setHtmlAudioTransportSnapshotSink(null);
    disposePostEditPlaybackReadiness();
    disposeEditorIntentController();
    disposeEditorPracticeRuntime();
    clearAllHtmlAudioSessions();
    disposeGraphCountdownOverlays();
    disposeRecordingProjections();
    clearChorusingStates();
    stopAllLearnerRecordingHtmlPlayback();
    disposeAllControllers();
    resetEditorControlState();
    clearLearnerRecordingStateStore();
    clearVisualizerRuntimeStates();
}

function handleHtmlTransportSnapshot(snapshot: TransportSnapshot): void {
    projectEditorBusyState();
    notifyPostEditPlaybackReady(
        snapshot.fieldOrd,
        htmlAudioSessionSourceFilename(snapshot.fieldOrd),
    );
}

export function scan(config: EditorRuntimeConfig = editorRuntimeConfig()): void {
    const reviewTargets = reviewFieldTargets();
    installReviewerPanelTriggers(() => scan(config));
    if (reviewTargets.length) {
        reviewTargets.forEach((target) => mountNear(target));
        logger.debug("scan mounted review fields", {count: reviewTargets.length});
        requestPendingGraphRedraw();
        enqueueConfiguredDefaultGraphs(config, reviewTargets);
        return;
    }
    if (config.audioFieldIndices.length) {
        const explicitTargets = explicitFieldTargets(config.audioFieldIndices, config.audioFieldSources);
        explicitTargets.forEach((target) => mountNear(target));
        logger.debug("scan mounted explicit fields", {count: explicitTargets.length});
        requestPendingGraphRedraw();
        enqueueConfiguredDefaultGraphs(config, explicitTargets);
        return;
    }
    const mountedTargets: FieldTarget[] = [];
    let count = 0;
    fieldNodes().forEach((node, fallback) => {
        const sourceFilename = audioSourceForNode(node);
        if (!sourceFilename) return;
        const target = {
            node,
            ord: fieldIndex(node, fallback),
            sourceFilename,
        };
        mountNear(target);
        mountedTargets.push(target);
        count += 1;
    });
    logger.debug("scan mounted detected fields", {count});
    requestPendingGraphRedraw();
    enqueueConfiguredDefaultGraphs(config, mountedTargets);
}

export function reviewFieldTargets(): FieldTarget[] {
    return Array.from(document.querySelectorAll<HTMLElement>(".aqe-review-audio-target"))
        .map((node): FieldTarget | null => {
            const rawOrd = node.dataset.fieldOrd;
            const sourceFilename = node.dataset.aqeSourceFilename || audioSourceForNode(node);
            if (!reviewTargetIsOpen(node)) return null;
            if (rawOrd === undefined || !/^\d+$/.test(rawOrd) || !sourceFilename) return null;
            return {
                node,
                ord: Number(rawOrd),
                sourceFilename,
            };
        })
        .filter((target): target is FieldTarget => target !== null);
}

export function fieldNodes(): HTMLElement[] {
    const candidates = Array.from(document.querySelectorAll<HTMLElement>('[contenteditable="true"], .field, [data-field-ord]'));
    const seen = new Set<HTMLElement>();
    return candidates.filter((node) => {
        if (seen.has(node)) return false;
        seen.add(node);
        return !!(node.textContent || node.innerHTML);
    });
}

export function explicitFieldTargets(
    audioFieldIndices: readonly number[],
    audioFieldSources: Record<number, string> = {},
): FieldTarget[] {
    return audioFieldIndices
        .map((ord): FieldTarget | null => {
            const container = document.querySelector<HTMLElement>(`.field-container[data-index="${ord}"]`);
            if (!container) return null;
            const node = container.querySelector<HTMLElement>('[contenteditable="true"]') || container;
            const sourceFilename = audioSourceForNode(node) || audioSourceForNode(container) || audioFieldSources[ord] || "";
            return {
                ord,
                node,
                sourceFilename,
            };
        })
        .filter((target): target is FieldTarget => target !== null);
}

export function fieldIndex(node: HTMLElement, fallback: number): number {
    const attrs = ["data-field-ord", "data-ord", "data-index"] as const;
    for (const attr of attrs) {
        const raw = node.getAttribute(attr);
        if (raw !== null && /^\d+$/.test(raw)) return Number(raw);
    }
    const idMatch = /(\d+)/.exec(String(node.id || ""));
    return idMatch ? Number(idMatch[1]) : fallback;
}

export function mountNear(target: FieldTarget): void {
    mountController(target);
}

function enqueueConfiguredDefaultGraphs(config: EditorRuntimeConfig, targets: readonly FieldTarget[]): void {
    if (!config.showGraphByDefault) return;
    enqueueDefaultGraphs(
        targets.map(({ord, sourceFilename}) => ({ord, sourceFilename})),
        {
            anyBusy: isEditorBusy,
            requestDefaultGraph,
        },
    );
}

function scheduleScan(callback: () => void, delayMs: number): void {
    const timer = window.setTimeout(() => {
        scheduledScanTimers = scheduledScanTimers.filter((scheduled) => scheduled !== timer);
        callback();
    }, delayMs);
    scheduledScanTimers.push(timer);
}

function installEditorDomObserver(callback: () => void): void {
    editorDomObserver?.disconnect();
    editorDomObserver = null;
    if (typeof MutationObserver === "undefined" || !document.body) return;

    editorDomObserver = new MutationObserver((records) => {
        if (records.some(recordAffectsFieldScan)) {
            scheduleMutationScan(callback);
        }
    });
    editorDomObserver.observe(document.body, {childList: true, subtree: true});
}

function recordAffectsFieldScan(record: MutationRecord): boolean {
    return [...record.addedNodes, ...record.removedNodes].some(nodeAffectsFieldScan);
}

function nodeAffectsFieldScan(node: Node): boolean {
    if (!(node instanceof HTMLElement)) return false;
    return node.matches(FIELD_SCAN_SELECTOR) || node.querySelector(FIELD_SCAN_SELECTOR) !== null;
}

function scheduleMutationScan(callback: () => void): void {
    if (mutationScanTimer !== null) return;
    mutationScanTimer = window.setTimeout(() => {
        mutationScanTimer = null;
        callback();
    }, 0);
}
