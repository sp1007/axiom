# T080 — Port Resolver and HIR Session Integration to Axiom (`compiler/resolve_hir/`)

## Summary
- Ported the integrated Resolver + HIR session pipeline (`compiler/resolve_hir/session.ax`, `compiler/resolve_hir/mod.ax`) to pure Axiom over `CompilerSession` (`compiler.kernel_source_diag.session`), `compiler.parser.session`, `compiler.resolve`, and `compiler.hir`.
- Implemented `session_ensure_module_header`, `append_ast_items`, `session_append_std_prelude` (with deterministic embedded `std.core.{option,result,prelude,host}` AST injection), `session_resolve_ast_into`, `session_lower_hir`, `session_render_resolved`, `session_render_resolved_into`, `session_render_hir`, `session_render_hir_into`, `session_resolve_and_render_human`, `session_resolve_and_render_json`, `session_hir_and_render_human`, and `session_hir_and_render_json`.
- Built the selfhost differential test suite under `tests/selfhost/resolve_hir/` covering positive corpus files (`qa_resolve_hir_corpus_pos_a..c.ax`), negative diagnostic corpus files (`qa_resolve_hir_corpus_neg_a..d.ax`), wide multi-phase corpus files (`qa_resolve_hir_corpus_wide_a..b.ax`), and multi-file module packages plus cross-file visibility and JSON diagnostics (`qa_resolve_hir_multifile_modules_a..b.ax`).

## Verification
- `python tools/axtest.py selfhost/resolve_hir`: 33/33 PASS across `[interp]`, `[native]`, and `[native-O1]`.
- `python tools/archcheck.py`: 0 violations.
