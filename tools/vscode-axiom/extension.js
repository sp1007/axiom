// Thin VS Code LSP Client for Axiom (`axiomc lsp --stdio`) (T802 / E19.1).
// Implements SPEC-100 §6.3 (AXS-LSP-052) and 0101 §38-41:
// Zero Axiom parsing, name resolution, or semantic logic resides in JavaScript/TypeScript.
// All semantic queries, diagnostics, completions, renames, semantic tokens, and AXCODEEDITOR
// inlay hints are served by the native `axiomc lsp` server over `CompilerDB` and `AXEDITOR`.
"use strict";

let client = null;

function buildServerArgs(config) {
  const encoding = config.get("positionEncoding", "utf-16");
  const inlayTypes = config.get("inlayHints.inferredTypes", true);
  const inlayParams = config.get("inlayHints.parameterNames", true);
  const inlayOwnership = config.get("inlayHints.ownershipFlow", true);
  const inlayAsync = config.get("inlayHints.asyncSuspension", true);

  return [
    "lsp",
    "--stdio",
    `--position-encoding=${encoding}`,
    `--inlay-types=${inlayTypes ? "true" : "false"}`,
    `--inlay-params=${inlayParams ? "true" : "false"}`,
    `--inlay-ownership=${inlayOwnership ? "true" : "false"}`,
    `--inlay-async=${inlayAsync ? "true" : "false"}`
  ];
}

function activate(context) {
  const vscode = require("vscode");
  const { LanguageClient, TransportKind } = require("vscode-languageclient/node");

  const config = vscode.workspace.getConfiguration("axiom.lsp");
  const command = config.get("serverPath", "axiomc");
  const args = buildServerArgs(config);

  const serverOptions = {
    run: { command, args, transport: TransportKind.stdio },
    debug: { command, args, transport: TransportKind.stdio }
  };

  const clientOptions = {
    documentSelector: [{ scheme: "file", language: "axiom" }],
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher("**/{*.ax,Axiom.toml}")
    }
  };

  client = new LanguageClient(
    "axiom-lsp",
    "Axiom Language Server (AXCODEEDITOR)",
    serverOptions,
    clientOptions
  );

  context.subscriptions.push(client.start());
}

function deactivate() {
  if (!client) {
    return undefined;
  }
  return client.stop();
}

module.exports = {
  activate,
  deactivate,
  buildServerArgs
};
