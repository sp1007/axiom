# T807 Report — E19.2 Canonical Formatter Idempotence, Comment Preservation & Full-Corpus Conformance Suite

STATUS: COMPLETE

## Summary

Implemented the Phase 19 (`E19.2` / `T807`) end-to-end conformance suite in `tests/conformance/p19/e19_2_formatter/` certifying `spec/SPEC-101-canonical-formatter.md` (`AXS-FMT-001..053`, `INV-FMT-001..003`, `EX-FMT-01..03`, `NEG-FMT-01..03`, `REQ-TOOL-183`, `REQ-TOOL-298`):

1. **Master Conformance Oracle & Live Compiler Bundle Probe (`e19_2_formatter_oracle.test`, `e19_2_formatter_oracle.py`, `e19_2_formatter_probe.ax.in`)**:
   - Assembles the live `std/editor/mod.ax`, `compiler/lex/*`, `compiler/syntax/*`, `compiler/fmt/cst/mod.ax`, `compiler/fmt/printer/mod.ax`, `compiler/fmt/verify/mod.ax`, `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`, and `compiler/driver/fmt_cmd/mod.ax` modules with `e19_2_formatter_probe.ax.in`.
   - Executes the bundle under `--interp` and compiles + runs it at most once at `-O0` (`--stack-reserve=67108864`), verifying:
     - `fmt(fmt(src)) == fmt(src)` single-step idempotence, 100% comment conservation (`unemitted_comment_count == 0`), and structural AST equivalence across real `.ax` corpus files on disk spanning `compiler/` (`compiler/refactor/vcs/mod.ax`), `std/` (`std/core/host.ax`), and `tests/` (`tests/conformance/p19/e19_2_formatter/cli_check_diff_stdin_and_manifest_policy.ax`),
     - 5-slot CST trivia attachment (`SLOT_HEADER`, `SLOT_TRAILING`, `SLOT_INLINE`, `SLOT_LEADING`, `SLOT_DANGLING`), doc-comment before attribute placement (`///` before `@repr(C)` / `@derive(Copy)`), `#region`/`#endregion` barriers, UTF-8 BOM stripping, and Vietnamese (`"Xin chào thế giới"` — 22 bytes, 17 Unicode scalars) / emoji (`"🚀🔥"` — 8 bytes, 2 Unicode scalars) scalar width calculation,
     - `axiomc fmt` CLI flag rules, `[format].exclude` manifest policy, `--check` unified diff headers, in-place `mtime` preservation on canonical files, syntax-error/legacy-token refusal (`exit 1`), and post-format verification tamper abort (`exit 3`),
     - Byte-for-byte agreement between LSP `textDocument/formatting` / `textDocument/rangeFormatting` and CLI `axiomc fmt` output, client `FormattingOptions` ignore, and zero-codegen firewall.
   - Runs differential verification (`--interp` vs `-O1 --verify-each`) across all 4 standalone `.ax` conformance fixtures.
2. **Corpus Idempotence, Semicolon Rules S1/S2/S3 & Verification Gate (`corpus_idempotence_and_ast_equivalence.ax`)**:
   - Verifies canonical semicolon rules S1/S2/S3 (`AXS-FMT-025`, `NEG-FMT-02` tail-value vs suppressed-unit semicolon preservation), trailing binary operators on wrapped lines (`NEG-FMT-01`), leading-dot method chains (`AXS-FMT-026`), and post-format verification gate tamper rejection (`exit 3`).
3. **5-Slot CST Trivia Attachment & UTF-8 Scalar Width (`comment_five_slot_and_utf8_preservation.ax`)**:
   - Verifies deterministic classification into the 5 CST trivia slots, `///` before `@repr`/`@derive` ordering (`EX-FMT-02`), `#region` reordering barriers (`NEG-FMT-03`), UTF-8 BOM stripping, and UTF-8 byte vs Unicode scalar vs UTF-16 code unit counting on `"Xin chào thế giới"` (`22` bytes, `17` scalars, `17` UTF-16 units) and `"🚀🔥"` (`8` bytes, `2` scalars, `4` UTF-16 units).
4. **CLI `--check` Unified Diff, `--stdin`, `[format]` Manifest & `mtime` Invariance (`cli_check_diff_stdin_and_manifest_policy.ax`)**:
   - Verifies exit codes (`0`, `1`, `2`, `3`), zero-config style override rejection (`exit 2`), `--check` zero disk writes, in-place `mtime` preservation on already-canonical files (`INV-FMT-002`), and workspace directory/glob filtering.
5. **LSP `textDocument/formatting` & `rangeFormatting` Parity with CLI (`lsp_cli_formatting_parity_and_range_edits.ax`)**:
   - Verifies minimal line-aligned `TextEdit` window computation, byte-for-byte parity with `axiomc fmt`, `0` edits on canonical or syntax-error documents, and `0` backend codegen invocations.

## Files changed

- tests/conformance/p19/e19_2_formatter/README.md
- tests/conformance/p19/e19_2_formatter/cli_check_diff_stdin_and_manifest_policy.ax
- tests/conformance/p19/e19_2_formatter/cli_check_diff_stdin_and_manifest_policy.stdout
- tests/conformance/p19/e19_2_formatter/comment_five_slot_and_utf8_preservation.ax
- tests/conformance/p19/e19_2_formatter/comment_five_slot_and_utf8_preservation.stdout
- tests/conformance/p19/e19_2_formatter/corpus_idempotence_and_ast_equivalence.ax
- tests/conformance/p19/e19_2_formatter/corpus_idempotence_and_ast_equivalence.stdout
- tests/conformance/p19/e19_2_formatter/e19_2_formatter_oracle.py
- tests/conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test
- tests/conformance/p19/e19_2_formatter/e19_2_formatter_probe.ax.in
- tests/conformance/p19/e19_2_formatter/lsp_cli_formatting_parity_and_range_edits.ax
- tests/conformance/p19/e19_2_formatter/lsp_cli_formatting_parity_and_range_edits.stdout

## Verification

- Command: `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p19/e19_2_formatter`
- Result: `WEAK-NATIVE 0`, `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`
