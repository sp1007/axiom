# Axiom Language Support (`vscode-axiom`)

First-party thin VS Code client for the Axiom Programming Language (`axiomc lsp --stdio`), powered by the native `AXEDITOR` text core (`std/editor/mod.ax`), `CompilerDB` (`compiler/query/db/mod.ax`), and the `AXCODEEDITOR` semantic intelligence layer (`compiler/lsp/handlers/mod.ax`).

## Architecture (`SPEC-100`, `0101 §38-41`)

- **Zero Client-Side Semantic Duplication (`AXS-LSP-052`)**: `extension.js` contains zero Axiom parsing, name resolution, or type inference logic. It spawns `axiomc lsp --stdio` and delegates all semantic intelligence to the native Axiom compiler server.
- **Zero-Codegen Interactive Firewall (`AXS-LSP-004`, `REQ-TOOL-185`)**: Interactive LSP queries evaluate `CompilerDB` frontend/semantic stages (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `layout_of`, `effect_summary`) and never invoke backend codegen (`LIR`, `x86-64` instruction selection, `COFF`/`ELF` emission, or linking).
- **AXCODEEDITOR Semantic Presentation (`AXS-LSP-050..051`, `REQ-TOOL-300`)**:
  - Semantic token modifiers for Axiom ownership and capabilities: `ownedValue`, `readView` (`view<T>`), `mutView` (`mut_view<T>`), and `movedValue`.
  - Non-mutating inlay hints for inferred types (`: Type`), parameter names (`param:`), ownership/capability flows (`/* move */`, `/* drop x */`, `/* view */`, `/* mut_view */`), and `.await` async state-machine suspension points.
