import { readdirSync, readFileSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import { cwd } from "node:process";
import ts from "typescript";
import { describe, expect, it } from "vitest";

const ROOT = resolve(cwd(), "..");
const EDITOR_INLINE = join(ROOT, "settings_ui", "src", "editor-inline");

interface CapabilityUse {
  readonly column: number;
  readonly line: number;
  readonly name: string;
}

describe("state-management architecture", () => {
  it("Rule 40 / SM-A02 keeps direct HTML media operations inside the audio port", () => {
    expect(mediaCapabilities(`
      const text = "audio.play()";
      // audio.pause();
      audio.play();
      audio["pause"]();
      audio.currentTime = 1;
    `).map((use) => use.name)).toEqual(["play", "pause", "currentTime"]);

    const owners = new Set([
      "html-audio-session-audio-element.ts",
      "test-contract.ts",
    ]);
    const observedOwners = new Set<string>();
    const violations: string[] = [];
    for (const path of productionTypeScriptFiles(EDITOR_INLINE)) {
      const uses = mediaCapabilities(readFileSync(path, "utf8"));
      if (uses.length === 0) continue;
      const name = basename(path);
      if (owners.has(name)) {
        observedOwners.add(name);
        continue;
      }
      for (const use of uses) {
        violations.push(`${relative(ROOT, path)}:${use.line}:${use.column}: ${use.name}`);
      }
    }

    expect(violations).toEqual([]);
    expect(observedOwners).toEqual(owners);
  });

  it("Rule 41 / SM-A03 keeps transport transitions and state writes in the controller", () => {
    const allowed = new Map([
      ["transitionHtmlAudioSession", new Set(["html-audio-session-controller.ts"])],
      ["sessionStates.set", new Set(["html-audio-session-controller.ts"])],
    ]);
    const observed = new Map([...allowed].map(([name]) => [name, new Set<string>()]));
    const violations: string[] = [];

    for (const path of productionTypeScriptFiles(EDITOR_INLINE)) {
      const file = basename(path);
      for (const call of namedCalls(readFileSync(path, "utf8"), allowed.keys())) {
        if (!allowed.get(call.name)?.has(file)) {
          violations.push(`${relative(ROOT, path)}:${call.line}:${call.column}: ${call.name}`);
        } else {
          observed.get(call.name)?.add(file);
        }
      }
    }

    expect(namedCalls(`
      // transitionHtmlAudioSession(state, event)
      const text = "sessionStates.set";
      transitionHtmlAudioSession(state, event);
      sessionStates.set(0, state);
    `, allowed.keys()).map((use) => use.name)).toEqual([
      "transitionHtmlAudioSession",
      "sessionStates.set",
    ]);
    expect(violations).toEqual([]);
    expect(observed).toEqual(allowed);
  });

  it("Rule 42 / SM-A04 keeps practice programs pure", () => {
    const forbiddenImports = /(bridge|controller|dom-|field-state|recording-state|visualizer)/;
    const violations: string[] = [];
    for (const path of productionTypeScriptFiles(join(EDITOR_INLINE, "practice"))) {
      if (basename(path) === "runtime.ts" || basename(path) === "index.ts") continue;
      const source = readFileSync(path, "utf8");
      for (const imported of importSpecifiers(source)) {
        if (forbiddenImports.test(imported)) {
          violations.push(`${relative(ROOT, path)}: forbidden import ${imported}`);
        }
      }
      for (const global of referencedGlobals(source, ["document", "window", "setTimeout", "setInterval"])) {
        violations.push(`${relative(ROOT, path)}:${global.line}:${global.column}: ${global.name}`);
      }
    }
    expect(importSpecifiers(`
      import type { Value } from "./model.js";
      const text = 'import x from "./bridge.js"';
      import("./controller.js");
    `)).toEqual(["./model.js", "./controller.js"]);
    expect(violations).toEqual([]);
  });

  it("Rule 44 / SM-A06 exhaustively assigns identity to every transport event", () => {
    const policy = readFileSync(join(EDITOR_INLINE, "transport", "event-policy.ts"), "utf8");
    expect(policy).toContain(
      "satisfies Record<HtmlAudioSessionEvent[\"type\"], TransportIdentityScope>",
    );
    expect(policy).not.toContain("PostEditAutoplayRequested");
    expect(policy).not.toContain("GraphRenderedForSource");
  });

  it("Rule 50 / SM-A12 wires state and resource validators around effects", () => {
    const controller = readFileSync(join(EDITOR_INLINE, "html-audio-session-controller.ts"), "utf8");
    const eventQueue = readFileSync(join(EDITOR_INLINE, "html-audio-session-event-queue.ts"), "utf8");
    const calls = new Set(namedCalls(controller, [
      "validateTransportState",
      "validateTransportOwnership",
      "validateTransportResources",
    ]).map((call) => call.name));
    expect(calls).toEqual(new Set([
      "validateTransportState",
      "validateTransportOwnership",
      "validateTransportResources",
    ]));
    expect(controller.indexOf("validateTransportState(transition.state)")).toBeLessThan(
      controller.indexOf("eventDispatcher.executeEffects(ord, transition.effects"),
    );
    expect(controller.indexOf("validateTransportResources(transition.state")).toBeGreaterThan(
      controller.indexOf("eventDispatcher.executeEffects(ord, transition.effects"),
    );
    expect(eventQueue).toContain("for (const effect of effects)");
  });
});

function productionTypeScriptFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return productionTypeScriptFiles(path);
    return entry.isFile() && entry.name.endsWith(".ts") && !entry.name.endsWith(".d.ts")
      ? [path]
      : [];
  });
}

function sourceFile(source: string): ts.SourceFile {
  return ts.createSourceFile("fixture.ts", source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
}

function location(node: ts.Node, file: ts.SourceFile, name: string): CapabilityUse {
  const position = file.getLineAndCharacterOfPosition(node.getStart(file));
  return { column: position.character + 1, line: position.line + 1, name };
}

function memberName(expression: ts.Expression): string | null {
  if (ts.isPropertyAccessExpression(expression)) return expression.name.text;
  if (!ts.isElementAccessExpression(expression)) return null;
  const argument = expression.argumentExpression;
  return argument && ts.isStringLiteral(argument) ? argument.text : null;
}

function mediaCapabilities(source: string): CapabilityUse[] {
  const file = sourceFile(source);
  const uses: CapabilityUse[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isCallExpression(node)) {
      const name = memberName(node.expression);
      if (name && ["load", "pause", "play"].includes(name)) {
        uses.push(location(node, file, name));
      }
      if (
        name === "setAttribute"
        && node.arguments[0]
        && ts.isStringLiteral(node.arguments[0])
        && node.arguments[0].text === "src"
      ) uses.push(location(node, file, "setAttribute(src)"));
      if (
        name === "removeAttribute"
        && node.arguments[0]
        && ts.isStringLiteral(node.arguments[0])
        && node.arguments[0].text === "src"
      ) uses.push(location(node, file, "removeAttribute(src)"));
    }
    if (
      ts.isBinaryExpression(node)
      && node.operatorToken.kind === ts.SyntaxKind.EqualsToken
      && (ts.isPropertyAccessExpression(node.left) || ts.isElementAccessExpression(node.left))
    ) {
      const name = memberName(node.left);
      if (name === "currentTime" || name === "src") uses.push(location(node, file, name));
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return uses;
}

function namedCalls(source: string, names: Iterable<string>): CapabilityUse[] {
  const targets = new Set(names);
  const file = sourceFile(source);
  const calls: CapabilityUse[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isCallExpression(node)) {
      const name = ts.isIdentifier(node.expression)
        ? node.expression.text
        : ts.isPropertyAccessExpression(node.expression)
          ? `${node.expression.expression.getText(file)}.${node.expression.name.text}`
          : null;
      if (name && targets.has(name)) calls.push(location(node, file, name));
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return calls;
}

function importSpecifiers(source: string): string[] {
  const file = sourceFile(source);
  const imports: string[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isImportDeclaration(node) && ts.isStringLiteral(node.moduleSpecifier)) {
      imports.push(node.moduleSpecifier.text);
    } else if (
      ts.isCallExpression(node)
      && node.expression.kind === ts.SyntaxKind.ImportKeyword
      && node.arguments[0]
      && ts.isStringLiteral(node.arguments[0])
    ) {
      imports.push(node.arguments[0].text);
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return imports;
}

function referencedGlobals(source: string, names: readonly string[]): CapabilityUse[] {
  const targets = new Set(names);
  const file = sourceFile(source);
  const uses: CapabilityUse[] = [];
  const visit = (node: ts.Node): void => {
    if (ts.isIdentifier(node) && targets.has(node.text) && isReference(node)) {
      uses.push(location(node, file, node.text));
    }
    ts.forEachChild(node, visit);
  };
  visit(file);
  return uses;
}

function isReference(node: ts.Identifier): boolean {
  const parent = node.parent;
  if (ts.isImportSpecifier(parent) || ts.isImportClause(parent)) return false;
  if (ts.isPropertyAccessExpression(parent) && parent.name === node) return false;
  return true;
}
