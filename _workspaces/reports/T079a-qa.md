# T079a QA Report — Port AST data model to Axiom

## Round 0
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T079a`: 7 files staged (report, `compiler/syntax/ast.ax`, 5 tests under `tests/selfhost/ast/`), 0 REFUSED lines.
- `python tools/archcheck.py`: 188 files scanned, 0 violations.
- LOC check: `compiler/syntax/ast.ax` = 1,499 LOC (≤ 1,500 budget).
- `python tools/axtest.py --compiler bootstrap/axiom0/build/axiom0.exe selfhost`: TOTAL 72 PASS 72 FAIL 0 (`[interp]`, `[native]`, `[native-O1]`), no timeouts; standalone interp time per AST test < 3 s.
- Manual review: tests construct AST nodes via `ast.ax` allocators and compare `ax_ast_render` output byte-for-byte against `axiom0 inspect --emit=ast` expected text.
- Note: workaround for an `axiom0` native backend struct-field store sizing bug is documented in the report; follow-up fix recommended.

VERDICT: PASS round=0
