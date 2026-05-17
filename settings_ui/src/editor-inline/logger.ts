import { createLogger } from "../lib/logger.js";
import { sendEditorFrontendLog } from "./bridge.js";

export const logger = createLogger("editor", sendEditorFrontendLog);
