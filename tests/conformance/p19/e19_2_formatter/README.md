# E19.2 Conformance Suite — Canonical Formatter (`axiomc fmt`), 5-Slot CST Trivia Preservation, Full-Corpus Idempotence & LSP Formatting Parity (`SPEC-101`)

This directory contains the Phase 19 (`E19.2` / `T807`) end-to-end conformance suite for `SPEC-101-canonical-formatter.md`:
- `e19_2_formatter_oracle.test` & `e19_2_formatter_oracle.py` — Master conformance oracle validating:
  1. Live bundled execution of `std/editor/mod.ax`, `compiler/lex/*`, `compiler/syntax/*`, `compiler/fmt/cst/mod.ax`, `compiler/fmt/printer/mod.ax`, `compiler/fmt/verify/mod.ax`, `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`, and `compiler/driver/fmt_cmd/mod.ax` with `e19_2_formatter_probe.ax.in` across `--interp` and native `-O0` compilation (compiled at most once per `<120s` resource budget), certifying `fmt(fmt(src)) == fmt(src)` idempotence, comment conservation, and AST equivalence across 12 real `.ax` corpus files on disk spanning `compiler/`, `std/`, and `tests/`.
  2. Differential verification (`--interp` vs native `-O1 --verify-each`) of all 4 standalone `.ax` conformance fixtures.
- `corpus_idempotence_and_ast_equivalence.ax` — Single-step formatter idempotence (`fmt(fmt(src)) == fmt(src)`), post-format AST & comment verification gate (`AXS-FMT-030..032`, exit `3` on tamper), canonical semicolon rules S1/S2/S3 (`AXS-FMT-025`, `NEG-FMT-02` tail-value preservation), trailing binary operators on wrapped lines (`AXS-FMT-026`, `NEG-FMT-01`), and leading-dot method chains.
- `comment_five_slot_and_utf8_preservation.ax` — 5-slot CST trivia attachment (`SLOT_HEADER`, `SLOT_TRAILING`, `SLOT_INLINE`, `SLOT_LEADING`, `SLOT_DANGLING`), doc-comment before attribute ordering (`///` before `@derive`/`@repr`, `EX-FMT-02`), `#region`/`#endregion` reordering barriers (`NEG-FMT-03`), UTF-8 BOM stripping, Unicode scalar width calculation (`"Xin chào thế giới"` and `"🚀🔥"`), and verbatim numeric/raw-string literal preservation.
- `cli_check_diff_stdin_and_manifest_policy.ax` — `axiomc fmt` CLI flag rules (`--check`, `--stdin`, `--quiet`, exit `2` on unknown style flags or `--stdin` + `<path>`), `[format]` manifest zero-config policy (`exclude` globs vs rejected style keys exit `2`), deterministic lexicographical workspace traversal, unified diff headers, idempotent `mtime` preservation (`INV-FMT-002`), and syntax-error/legacy-token refusal (`exit 1`).
- `lsp_cli_formatting_parity_and_range_edits.ax` — LSP `textDocument/formatting` & `textDocument/rangeFormatting` minimal `TextEdit` window calculation, byte-for-byte agreement with `axiomc fmt`, `0` edits on canonical documents, ignoring client `FormattingOptions`, syntax-error refusal (`0` edits), and zero-codegen firewall.

---

## `SPEC-101` Rule & Invariant Mapping (`AXS-FMT-001..053` & `INV-FMT-001..003`)

| Rule / Invariant / Req | Normative Requirement (`SPEC-101`) | Conformance Test Coverage |
|---|---|---|
| `AXS-FMT-001..003` | Deterministic, Total, Single-Step Idempotent `fmt(fmt(S)) == fmt(S)` & AST-Preserving Function | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax` |
| `AXS-FMT-004..006` | Zero-Config Style Policy (`[format].exclude` only; unknown CLI flags or style keys exit `2`) | `e19_2_formatter_probe.ax.in`, `cli_check_diff_stdin_and_manifest_policy.ax` |
| `AXS-FMT-007..013` | UTF-8 Encoding, BOM Stripping, `LF` Normalization, 4-Space Indent, 100-Scalar Line Width (`"Xin chào thế giới"`, `"🚀🔥"`) | `e19_2_formatter_probe.ax.in`, `comment_five_slot_and_utf8_preservation.ax` |
| `AXS-FMT-014..018` | Module Header, `use` Import Grouping & Lexicographic Sorting, Brace-Group Merging, Blank-Line Collapse (`EX-FMT-01`) | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax` |
| `AXS-FMT-019..024` | Wadler-Lindig `fn`/`struct`/`enum`/`trait`/`impl`/`where` Formatting & Trailing Commas (`EX-FMT-02`, `EX-FMT-03`) | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax` |
| `AXS-FMT-025..029` | Canonical Semicolon Rules S1/S2/S3 (`NEG-FMT-02`), Trailing Binary Operators (`NEG-FMT-01`), Leading-Dot Chains, Verbatim Literals | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax`, `comment_five_slot_and_utf8_preservation.ax` |
| `AXS-FMT-030..035` | Syntax-Error & Legacy-Token (`:=`, `var`, `::`) Refusal (`exit 1`) + Post-Format AST & Comment Verification Gate (`exit 3`) | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax`, `cli_check_diff_stdin_and_manifest_policy.ax` |
| `AXS-FMT-036..039` | 5-Slot CST Trivia Attachment (`Header`, `Trailing`, `Inline`, `Leading`, `Dangling`), `///` Before Attributes, `#region` Barriers (`NEG-FMT-03`) | `e19_2_formatter_probe.ax.in`, `comment_five_slot_and_utf8_preservation.ax` |
| `AXS-FMT-040..048` | CLI Entrypoint (`--check`, `--stdin`, `--quiet`), Lexicographic Discovery, Unified Diff, Atomic Write & `mtime` Preservation, Exit Codes `0..3` | `e19_2_formatter_probe.ax.in`, `cli_check_diff_stdin_and_manifest_policy.ax` |
| `AXS-FMT-049..053` | LSP `textDocument/formatting` & `textDocument/rangeFormatting` Minimal `TextEdit`, Client Option Ignore, CLI Parity & Error Refusal | `e19_2_formatter_probe.ax.in`, `lsp_cli_formatting_parity_and_range_edits.ax` |
| `INV-FMT-001` | Semantic & Comment Conservation (`Parse_AST(fmt(S)) ~= Parse_AST(S)`, `Comments(fmt(S)) == Comments(S)`) | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax`, `comment_five_slot_and_utf8_preservation.ax` |
| `INV-FMT-002` | Single-Step Idempotence & `mtime` Stability | `e19_2_formatter_probe.ax.in`, `corpus_idempotence_and_ast_equivalence.ax`, `cli_check_diff_stdin_and_manifest_policy.ax` |
| `INV-FMT-003` | Deterministic Cross-Platform Output | `e19_2_formatter_oracle.py`, all `.ax` fixtures in this directory |
| `REQ-TOOL-183`, `REQ-TOOL-298` | Phase 19 `E19.2` Canonical Formatter Requirements | `e19_2_formatter_oracle.py`, `e19_2_formatter_probe.ax.in`, all `.ax` fixtures |
