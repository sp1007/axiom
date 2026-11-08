# T805 — E19.2 Lossless CST Trivia Attachment, Wadler-Lindig Layout Engine & Canonical AST Printer

## Summary

Implemented the lossless CST trivia attachment layer (`compiler.fmt.cst`) and the Wadler-Lindig layout engine + canonical Axiom AST/CST printer (`compiler.fmt.printer`) governed by `SPEC-101`, `SPEC-01`, and `SPEC-02` (`REQ-TOOL-183`, `REQ-TOOL-298`, `INV-FMT-001`):

1. **Lossless CST Trivia Collection, Normalization & 5-Slot Attachment (`compiler/fmt/cst/mod.ax`, `AXS-FMT-001..004`)**:
   - Strips leading UTF-8 BOM (`0xEF 0xBB 0xBF`), counts Unicode scalar column widths (`cst_utf8_scalar_len`), and normalizes line comments (`// x`), outer doc comments (`/// x`), inner doc comments (`//! x`), `#region`/`#endregion` barriers (`// #region <label>`, `// #endregion`), and block comments (`/* ... */`).
   - Precomputes balanced delimiter tables (`match_close`/`match_open` for `{...}`, `(...)`, `[...]`) and attaches every comment deterministically in $O(T + C)$ to one of the 5 slots:
     - **Slot 1 (`SLOT_HEADER`)**: File-level inner doc comments (`//!`) and top-of-file license/banner comments before the first declaration.
     - **Slot 2 (`SLOT_TRAILING`)**: Single-line end-of-line comments sharing their line with a preceding token, emitted via `LineSuffix`.
     - **Slot 3 (`SLOT_INLINE`)**: Inline single-line `/* ... */` block comments between tokens on the same source line.
     - **Slot 4 (`SLOT_LEADING`)**: Leading comments and `///` outer doc comments anchored to the next declaration/statement/field/variant/arm, with `///` outer doc comments hoisted above `@attribute` lines (`AXS-FMT-003`, `AXS-FMT-022`).
     - **Slot 5 (`SLOT_DANGLING`)**: Dangling comments before closing `}` / `)` / `]` delimiters inside empty or non-empty containers and before EOF.
   - Preserves up to 1 intentional blank line (`cst_has_blank_line_between`), collapses $\ge 2$ consecutive blank lines to 1 (`AXS-FMT-002`), and tracks `cst_unemitted_count` so no comment is ever dropped or duplicated (`AXS-FMT-004`).
   - Reconstructs full braced and nested `AstUseTree` hierarchies (`use a.b.{self, Read, Write}`) from the original token stream (`cst_populate_use_trees`).

2. **Wadler-Lindig `Doc` Combinator Engine & Canonical Axiom AST Printer (`compiler/fmt/printer/mod.ax`, `AXS-FMT-010..029`, `AXS-FMT-032`)**:
   - Implements the 12 `Doc` combinators (`Nil`, `Text`, `HardLine`, `BlankLine`, `Line`, `SoftLine`, `SoftLineEmpty`, `Indent`, `Group`, `IfBreak`, `LineSuffix`, `Concat`) over an arena-backed `DocNode` slice with bottom-up `force_break` propagation (`HardLine`, `BlankLine`, `LineSuffix`, or multi-line `Text`) and an iterative $O(W)$ work-stack `doc_fits` solver (`FMT_MAX_WIDTH = 100` Unicode scalar columns, `FMT_INDENT_STEP = 4` spaces, `LF` line endings, zero trailing whitespace).
   - Implements the canonical Axiom declaration, statement, expression, pattern, and type printer (`fmt_print_module`, `fmt_print_item`, `fmt_print_stmt`, `fmt_print_expr`, `fmt_print_pattern`, `fmt_print_type`, `fmt_format_source`):
     - Canonical `=` bindings/assignments and `.` paths (never `:=`, `var`, or `::`);
     - Lexicographical sorting and brace canonicalization of contiguous barrier-free `use` groups (`self` first, single-entry `{X}` unwrapped, `#region`/`#endregion` and blank-line barriers respected; `AXS-FMT-021`);
     - Attribute canonical ordering (`@repr(...)` before `@derive(...)`) and outer `///` doc hoisting (`AXS-FMT-022`);
     - Function signatures, `where` clauses, structs, enums, traits, `impl` blocks, and `extern` blocks (`AXS-FMT-023..025`);
     - Block and statement formatting, parenthesized condition unwrapping (`if (c)` $\to$ `if c`), semicolon elision on non-final `STMT_EXPR` while preserving semicolons on final `STMT_EXPR` (`NEG-FMT-02`), and `match` arm formatting (`AXS-FMT-026..027`);
     - Binary operator trailing-operator line breaks (`NEG-FMT-01`), fluent method/field/try/`await` chain alignment (`AXS-FMT-028`, `EX-FMT-02`), and exact literal spelling preservation with lowercase `0x`/`0b`/`0o` prefix normalization (`AXS-FMT-029`).

3. **Verification Suite (`tests/run/fmt_engine/`)**:
   - Added `fmt_engine.test`, `fmt_engine_oracle.py`, and `fmt_engine_probe.ax.in` testing the real `compiler.fmt.cst` and `compiler.fmt.printer` modules across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`, plus standalone differential fixtures (`cst_trivia_five_slot_attachment.ax`, `wadler_lindig_group_and_suffix.ax`, `canonical_declarations_and_chains.ax`).

## Files changed

- compiler/fmt/cst/mod.ax
- compiler/fmt/printer/mod.ax
- tests/run/fmt_engine/canonical_declarations_and_chains.ax
- tests/run/fmt_engine/canonical_declarations_and_chains.stdout
- tests/run/fmt_engine/cst_trivia_five_slot_attachment.ax
- tests/run/fmt_engine/cst_trivia_five_slot_attachment.stdout
- tests/run/fmt_engine/fmt_engine.test
- tests/run/fmt_engine/fmt_engine_oracle.py
- tests/run/fmt_engine/fmt_engine_probe.ax.in
- tests/run/fmt_engine/wadler_lindig_group_and_suffix.ax
- tests/run/fmt_engine/wadler_lindig_group_and_suffix.stdout

## Verification

- `python build-snap-T805/tools/axtest.py -j 1 --root build-snap-T805 --build-dir build-snap-T805/build --compiler build-snap-T805/build/axiomc2.exe run/fmt_engine run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 196 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T805` -> `11` files matched cleanly

STATUS: COMPLETE round=0
