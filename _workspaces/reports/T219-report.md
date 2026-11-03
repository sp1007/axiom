# T219 — Plan phase P19: Developer tooling

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P19 (`P19-developer-tooling`)** theo `spec/ROADMAP.md` §3–§4 và `.claude/agents/axiom-architect.md`. Đã mở rộng đầy đủ 5 epic của P19 (`E19.1`–`E19.5`) thành **20 task cụ thể** (`T800`–`T819`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-100`..`SPEC-104`, 2 task cài đặt của `axiom-frontend`/`axiom-semantics`/`axiom-stdlib`/`axiom-backend`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`), nối toàn bộ phụ thuộc với cổng P18 (`T318`) và cổng P19 (`T319`), đồng thời chuyển đổi toàn bộ **29 dòng `EPIC(E19.1)`** cùng các yêu cầu `REQ-TOOL-300`, `REQ-TOOL-297`, `REQ-TOOL-298`, và `REQ-TST-112` (tổng cộng 33 yêu cầu P19) trong `spec/requirements/CATALOG.md` sang mã task cụ thể (`T800`–`T819`).

## Summary

Expanded Phase **P19 (`P19-developer-tooling`)** from the 5 epics in `spec/ROADMAP.md` §3 (`E19.1`–`E19.5`) into **20 concrete tasks** (`T800`–`T819`, 4 tasks per epic, all depending on `T219` and P18 gate `T318`):

1. **E19.1 — LSP server (`T800`–`T803`)**:
   - `T800` (`axiom-architect`): `spec/SPEC-100-lsp-server-ide-engine.md` — `CompilerDB` (`SPEC-21`/`SPEC-22`) as the single semantic authority for `axiomc lsp` and IDE tooling (`REQ-TOOL-183`, `REQ-TOOL-297`, `REQ-TOOL-298`), typed generational IDs (`REQ-TOOL-191`), stable identities across incremental edits (`REQ-TOOL-184`), no-codegen semantic queries (`REQ-TOOL-185`), partial-program recovery (`REQ-TOOL-188`), constraint-filtered completion/hover/definition/references/rename (`REQ-TOOL-189`), `AXEDITOR` Unicode-aware piece-table buffer (`REQ-TOOL-299`), `AXCODEEDITOR` semantic highlighting & ownership/capability inlay hints (`REQ-TOOL-300`), and the thin VS Code client extension (`0101 §38-41`).
   - `T801` (`axiom-frontend`): LSP 3.17 JSON-RPC 2.0 transport, incremental VFS, `AXEDITOR` piece-table/rope buffer (`std/editor`, `compiler/lsp/vfs`), and partial-program AST/HIR recovery (`compiler/lsp/protocol`).
   - `T802` (`axiom-semantics`): `CompilerDB`-backed semantic IDE handlers (`publishDiagnostics`, `definition`, `references`, `hover`, `completion`, `rename`, `AXCODEEDITOR` `semanticTokens` & ownership/capability `inlayHint`), `axiomc lsp` CLI (`compiler/driver/lsp_cmd`), and the thin VS Code extension (`tools/vscode-axiom`).
   - `T803` (`axiom-qa`): LSP server, `AXEDITOR`/`AXCODEEDITOR` & VS Code extension conformance suite (`tests/conformance/p19/e19_1_lsp_server`).

2. **E19.2 — Formatter (canonical form) (`T804`–`T807`)**:
   - `T804` (`axiom-architect`): `spec/SPEC-101-canonical-formatter.md` — lossless CST token-trivia attachment over the shared compiler lexer/parser (`REQ-TOOL-183`, `REQ-TOOL-298`), zero-configuration canonical Axiom v1.0 layout rules (`tasks/0476`), AST equivalence guard, and `fmt(fmt(src)) == fmt(src)` idempotence.
   - `T805` (`axiom-frontend`): Lossless CST trivia attachment, Wadler-Lindig layout engine & canonical AST printer (`compiler/fmt/cst`, `compiler/fmt/printer`).
   - `T806` (`axiom-frontend`): Post-format AST equivalence verifier (`compiler/fmt/verify`), `axiomc fmt` CLI (`--check`, `--stdin`, workspace mode in `compiler/driver/fmt_cmd`), and LSP `textDocument/formatting` & `rangeFormatting` integration.
   - `T807` (`axiom-qa`): Canonical formatter idempotence, comment preservation & full-corpus conformance suite (`tests/conformance/p19/e19_2_formatter`).

3. **E19.3 — Refactoring engine (`T808`–`T811`)**:
   - `T808` (`axiom-architect`): `spec/SPEC-102-refactoring-engine-semantic-vcs.md` — `CompilerDB`-verified semantic refactoring transforms (`0101 §12-17`, `REQ-TOOL-183`, `REQ-TOOL-186`) and AST/semantic-aware `AXDIFF` (`REQ-TOOL-301`), `AXMERGE` (`REQ-TOOL-302`), `AXPATCH` (`REQ-TOOL-303`), `AXHISTORY` (`REQ-TOOL-304`), and `AXVCS` (`REQ-TOOL-305`).
   - `T809` (`axiom-semantics`): `CompilerDB` semantic refactorings (`extract_function` with owned/`view`/`mut_view` signature synthesis, `extract_variable`/`inline_variable`, `populate_match_arms`, `organize_imports`) & LSP `textDocument/codeAction` (`compiler/refactor/transforms`, `compiler/refactor/code_actions`).
   - `T810` (`axiom-stdlib`): Semantic AST diff/merge/patch & lineage history engine (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS` in `compiler/refactor/vcs`, `std/vcs`, `compiler/driver/refactor_cmd`).
   - `T811` (`axiom-qa`): Semantic refactoring engine, code actions & `AXDIFF`/`AXMERGE`/`AXPATCH`/`AXHISTORY`/`AXVCS` conformance suite (`tests/conformance/p19/e19_3_refactoring_vcs`).

4. **E19.4 — Diagnostics UX 2.0 & AI-agent interface (`T812`–`T815`)**:
   - `T812` (`axiom-architect`): `spec/SPEC-103-diagnostics-ux-ai-interface.md` — causal ownership/capability provenance spans, root-cause cascading suppression (`REQ-TOOL-298`), confidence-graded machine-applicable fixes (`REQ-TOOL-186`), `axiomc explain`, `axiomc inspect layout` (`REQ-TOOL-004`), structured semantic fact graph export (`REQ-TOOL-180`, `REQ-TOOL-185`), `.axmeta` container properties (`REQ-TOOL-181`) & `std` effect metadata (`REQ-TOOL-190`), and strict production artifact separation (`REQ-TOOL-182`, `REQ-TOOL-187`).
   - `T813` (`axiom-semantics`): Diagnostics UX 2.0 causal provenance rendering, cascading error suppression, transactional `axiomc fix` applicator, and `axiomc explain <CODE>` registry & CLI (`compiler/diag/ux2`, `compiler/diag/explain`, `compiler/driver/explain_cmd`).
   - `T814` (`axiom-semantics`): AI-agent semantic fact graph exporter (`axiomc query`), CLI type layout inspector (`axiomc inspect layout`), `.axmeta` container & `std` effect metadata exporter (`compiler/ai_query`, `compiler/driver/query_cmd`, `std/meta_effects`), and runtime artifact separation checks.
   - `T815` (`axiom-qa`): Diagnostics UX 2.0, explain codes, machine-applicable fixes & AI-agent fact interface conformance suite (`tests/conformance/p19/e19_4_diagnostics_ai`).

5. **E19.5 — Documentation generator & test framework UX (`T816`–`T819`)**:
   - `T816` (`axiom-architect`): `spec/SPEC-104-docgen-test-framework-ux.md` — `axiomc doc` (`CompilerDB` doc extraction, static HTML/JSON rendering, intra-doc links, executable doc-tests) and `axiomc test` UX 2.0 (`REQ-TST-112`, MIR differential oracle `REQ-TOOL-009`, optimization pass replay/bisection `REQ-TOOL-179`, semantic invariance across build features `REQ-TOOL-002`, zero production runtime overhead `REQ-TOOL-003`/`REQ-TOOL-008`/`REQ-TOOL-187`, and native debug metadata verification hooks `REQ-TOOL-005`..`REQ-TOOL-007`/`REQ-TOOL-010`/`REQ-TOOL-011`).
   - `T817` (`axiom-frontend`): `CompilerDB` documentation extractor, HTML/JSON site renderer, search index & executable doc-test runner (`compiler/docgen`, `compiler/driver/doc_cmd`).
   - `T818` (`axiom-backend`): Test runner UX 2.0 (`axiomc test`), MIR differential harness, optimization pass replay/bisection (`--opt-replay`, `--opt-bisect` in `compiler/opt/bisect`), and debug/trace invariant audit (`compiler/test_runner`, `compiler/driver/test_cmd`).
   - `T819` (`axiom-qa`): Documentation generator, doc-tests, pass replay/bisection & integrated test framework conformance suite (`tests/conformance/p19/e19_5_docgen_test_ux`).

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T319-phase-p19-gate-developer-tooling.md
- ./_workspaces/tasks/todo/T800-e19-1-lsp-server-ide-engine-axeditor-spec.md
- ./_workspaces/tasks/todo/T801-e19-1-lsp-jsonrpc-vfs-axeditor-partial-recovery.md
- ./_workspaces/tasks/todo/T802-e19-1-semantic-ide-queries-axcodeeditor-vscode-client.md
- ./_workspaces/tasks/todo/T803-e19-1-lsp-server-axcodeeditor-vscode-conformance.md
- ./_workspaces/tasks/todo/T804-e19-2-canonical-formatter-lossless-cst-spec.md
- ./_workspaces/tasks/todo/T805-e19-2-lossless-cst-trivia-wadler-lindig-printer.md
- ./_workspaces/tasks/todo/T806-e19-2-axiomc-fmt-cli-ast-verifier-lsp-formatting.md
- ./_workspaces/tasks/todo/T807-e19-2-formatter-idempotence-corpus-conformance.md
- ./_workspaces/tasks/todo/T808-e19-3-refactoring-engine-semantic-vcs-spec.md
- ./_workspaces/tasks/todo/T809-e19-3-compilerdb-semantic-refactorings-lsp-code-actions.md
- ./_workspaces/tasks/todo/T810-e19-3-semantic-ast-diff-merge-patch-history-vcs.md
- ./_workspaces/tasks/todo/T811-e19-3-refactoring-engine-semantic-vcs-conformance.md
- ./_workspaces/tasks/todo/T812-e19-4-diagnostics-ux2-explain-ai-interface-spec.md
- ./_workspaces/tasks/todo/T813-e19-4-causal-provenance-spans-fixit-engine-explain-cli.md
- ./_workspaces/tasks/todo/T814-e19-4-ai-semantic-fact-exporter-layout-container-effects.md
- ./_workspaces/tasks/todo/T815-e19-4-diagnostics-ux2-ai-interface-conformance.md
- ./_workspaces/tasks/todo/T816-e19-5-docgen-test-framework-pass-bisect-spec.md
- ./_workspaces/tasks/todo/T817-e19-5-compilerdb-docgen-html-json-doctest-runner.md
- ./_workspaces/tasks/todo/T818-e19-5-test-runner-ux2-mir-oracle-pass-bisect-debug-audit.md
- ./_workspaces/tasks/todo/T819-e19-5-docgen-test-ux-pass-bisect-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P19-developer-tooling --strict` → `33 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `v1-full epic=807  implemented=443  planned=7581`, `gaps: 0`, `COVERAGE OK` (`0` `EPIC(E19.*)` rows remaining; `exit 0`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T319` and `T800`–`T819` → `OK` (`21 files`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (507 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T219` → `23 stage, 0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=0
