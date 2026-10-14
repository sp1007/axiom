# T077 Report: Port kernel, source DB, diagnostics to Axiom (integration + differential)

## Summary
Integrated `compiler/kernel`, `compiler/source`, and `compiler/diag` into the cohesive `compiler/kernel_source_diag` subsystem (`CompilerSession`) and verified differential parity against `axiom0` across the `tests/ui/` corpus and self-host test suite:
- `compiler/kernel_source_diag/session.ax` (201 LOC): `CompilerSession` integrating `Arena`, `StrInterner`, `U32Interner`, `SourceDatabase`, and `DiagSink` with unified session lifecycle (`session_init`, `session_new`, `session_free`), virtual file loading and deduplication (`session_add_virtual_file`), span text slicing and span interning (`session_span_text`, `session_intern_span`, `session_line_col`), diagnostic reporting and sorting (`session_report`, `session_report_code`, `session_sort_diags`), and human/JSON rendering (`session_render_human`, `session_render_json`).
- `compiler/kernel_source_diag/mod.ax` (71 LOC): Unified module re-exports for `CompilerSession` and the underlying `kernel`, `source`, and `diag` types and functions.
- Differential Corpus Audit (`tests/ui/**/*.ax`):
  - Scanned all 193 UI test files in `tests/ui/` with `axiom0 check --std-root std --json`: 189/193 check-time UI corpus files emit `schema: 1` JSON diagnostics totaling 288 diagnostics across 71 distinct `AX_*` diagnostic codes.
  - Verified 100% byte-for-byte parity on both `--json` (`schema: 1`) and human-formatted snippet outputs (including Windows backslash path normalization in JSON, multi-digit line gutters, CRLF `\r\n` line endings, secondary `-` labels, and `MachineApplicable` fixes) in `tests/selfhost/kernel_source_diag/qa_corpus_differential.ax`.
  - Verified multi-file `CompilerSession` integration (virtual file deduplication, cross-file `session_intern_span` identifier pooling, line/column lookup, out-of-order multi-file diagnostic sorting, and human/JSON rendering) in `tests/selfhost/kernel_source_diag/qa_session_integration.ax`.
- All 36 Wave 1 self-host test variants across `tests/selfhost/{kernel,source,diag,kernel_source_diag}/` pass (`TOTAL 36 PASS 36 FAIL 0`).

## Files changed
- compiler/kernel_source_diag/mod.ax
- compiler/kernel_source_diag/session.ax
- tests/selfhost/kernel_source_diag/qa_corpus_differential.ax
- tests/selfhost/kernel_source_diag/qa_session_integration.ax

STATUS: COMPLETE round=0
