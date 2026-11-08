# T804 — E19.2 Canonical language form, lossless CST trivia model & deterministic formatter specification (SPEC-101)

## Tóm tắt

Hoàn thành đặc tả chuẩn tắc `spec/SPEC-101-canonical-formatter.md` cho Epic `E19.2` (`T804`), định nghĩa hình thức ngôn ngữ chuẩn tắc của Axiom, mô hình cây cú pháp cụ thể bảo toàn toàn vẹn (*lossless Concrete Syntax Tree — CST*) và gắn kết trivia 5 vị trí (`compiler/fmt/cst`), đại số bố cục tất định Wadler-Lindig (`compiler/fmt/printer`), cổng kiểm chứng tương đương AST sau định dạng (`compiler/fmt/verify`), giao diện dòng lệnh `axiomc fmt` (`compiler/driver/fmt_cmd`), và tích hợp định dạng LSP (`compiler/lsp/handlers`). Đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-FMT-001`..`INV-FMT-003`).

## Summary of Changes

1. **`spec/SPEC-101-canonical-formatter.md` (`AXS-FMT-001` .. `AXS-FMT-053`)**:
   - **§1. Unified Frontend Authority & Lossless CST / Trivia Attachment Model (`compiler/fmt/cst`, `AXS-FMT-001..004`)**:
     - Reuses `compiler/lex` and `compiler/syntax` inside `CompilerDB` as the single lexical/syntactic authority (`REQ-TOOL-183`, `REQ-TOOL-298`), prohibiting standalone or regex-based formatting parsers.
     - Partitions every valid `.ax` source buffer into tokens and trivia (`TriviaLineComment` `//`, `TriviaOuterDoc` `///`, `TriviaInnerDoc` `//!`, nested `TriviaBlockComment` `/* ... */`, `TriviaRegionDirective` `// #region` / `// #endregion`, and `TriviaBlankLine` runs collapsed to at most 1 blank line).
     - Defines the deterministic $O(T + C)$ 5-slot attachment model (`header_trivia`, `trailing_trivia` on the same line emitted via `LineSuffix` with 2 leading spaces, `inline_trivia` for mid-line `/* ... */`, `leading_trivia` on following declarations with `///` ordered before `@attribute` lines, and `dangling_trivia` inside delimited containers/empty blocks) and the 100% comment conservation invariant (`AXS-FMT-004`).
   - **§2. Zero-Configuration Canonical Policy & Deterministic Wadler-Lindig Layout Algebra (`compiler/fmt/printer`, `AXS-FMT-010..013`)**:
     - Fixes non-configurable canonical parameters: 4-space indentation, 100 Unicode scalar column target width, `LF` line endings, single trailing `LF`, at most 1 consecutive blank line, and `axiom.toml` `[format]` restricted to `exclude` globs.
     - Specifies the Wadler-Lindig `Doc` combinator algebra (`Nil`, `Text`, `HardLine`, `BlankLine`, `Line`, `SoftLine`, `SoftLineEmpty`, `Indent`, `Group`, `IfBreak`, `LineSuffix`, `Concat`), bounded 100-column $O(N)$ `fits()` solver, `LineSuffix` flushing before line breaks, and oversized atomic token preservation.
   - **§3. Canonical Formatting Rules for Axiom Surface Constructs (`AXS-FMT-020..029`)**:
     - Defines canonical formatting for `module` headers, lexicographically sorted `use` import groups (respecting comment and `#region` barriers), `@attribute` placement, `fn` signatures/receivers/generics/`where` clauses, `struct`/`enum`/`union`/`trait`/`impl` blocks, bindings/assignments (`=`), trailing-operator multi-line binary expressions (`SPEC-02 AXS-GRM-019` continuation safety) vs leading-`.` method chains (`AXS-GRM-013`), delimited literals with trailing commas in `Break` mode, control flow (`if`/`match`/`while`/`for`/`loop`), and verbatim numeric/string/raw-string/UTF-8 literal slice preservation.
     - Preserves semantic tail-suppression semicolons on the **final** `STMT_EXPR` of a block when `stmt.has_semi == true` (`AXS-FMT-025` Rule S3) while stripping redundant semicolons on declarations and non-final statements.
   - **§4. AST-Equivalence Verification Gate, Idempotence & Error Refusal (`compiler/fmt/verify`, `AXS-FMT-030..032`)**:
     - Refuses to format any file with `AX_LEX_*` or `AX_PARSE_*` errors (exit code `1` in CLI, `null` in LSP).
     - Enforces the post-format re-lex/re-parse verification gate (`ast_equiv(AstModule(S), AstModule(S'))` plus 100% comment conservation) before any disk write or LSP `TextEdit`, aborting with `AX_ICE_INTERNAL` (`data.stage = "fmt_verify"`, exit code `3`) on any mismatch, and requires single-step idempotence `fmt(fmt(src)) == fmt(src)`.
   - **§5–§6. `axiomc fmt` CLI, LSP Formatting Integration, Diagnostics & Invariants (`AXS-FMT-040..053`)**:
     - Defines `axiomc fmt [<path>...]`, `--check` (exit `0`/`1` + unified diff), `--stdin`, timestamp-preserving atomic writes, LSP `textDocument/formatting` & `textDocument/rangeFormatting` parity, canonical positive/negative examples (`EX-FMT-01..03`, `NEG-FMT-01..03`), and the invariant verification matrix (`INV-FMT-001`..`INV-FMT-003` for `T805`, `T806`, `T807`).
2. **`spec/INDEX.md`**:
   - Registered `spec/SPEC-101-canonical-formatter.md` in `§2`, `AXS-FMT-NNN` in `§4`, and `SPEC-101` under Developer Tooling in `§5`.
3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` (`§3`) and `## Sources` with the `E19.2` (`T804` / `SPEC-101 §6`) diagnostic mapping (`AX_LEX_*`, `AX_PARSE_*`, `AX_IO_*`, `AX_DRIVER_USAGE`, `AX_DRIVER_UNKNOWN_OPTION`, `AX_ICE_INTERNAL`).
4. **`spec/invariants.md`**:
   - Added the `FMT` group in `§1`, added `## 47. Canonical language form, lossless CST trivia model, and deterministic formatter (SPEC-101)` (`INV-FMT-001`..`INV-FMT-003`), and updated `## Sources`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK` (`gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T804` -> verified clean

## Files changed

- spec/SPEC-101-canonical-formatter.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
