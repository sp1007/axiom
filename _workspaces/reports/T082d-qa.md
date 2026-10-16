# T082d QA — Port drop elaboration and cleanup edges to Axiom

## Round 0

### Checks performed
- `taskctl.py changes T082d`: only `stage` lines (report, `compiler/mir/drop.ax`, `tests/selfhost/drop/**`); no REFUSED lines. No edit to `bootstrap/axiom0`, `tools/axtest.py`, CMake, `diag/codes.def` or `driver/pipeline.c` (axiom0 freeze respected).
- Snapshot `build-snap-T082d`: `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc` and `cmake --build build` OK; `touch` + rebuild of `cdriver_drop_oracle.c` prints no warnings (-Werror in build.ninja, 107 hits). The new C file is only a test driver under the task's paths and is picked up by the existing `cdriver_*.c` glob.
- `python tools/archcheck.py`: 188 files scanned, 0 violations.
- Review of `compiler/mir/drop.ax` (1198 lines, single file, under the guide size): function-by-function structure mirrors `bootstrap/axiom0/src/mir/drop/drop.c` (needs_drop, place_type, flag synthesis, visit operand/rvalue, rewrite block, expand_drop with struct/tuple/closure/enum/user-destructor, multi-pass `mir_drop_elaborate`). One statement per line, helpers per concern, no line packing, no dropped features, no `BOOTSTRAP-SHORTCUT`/TODO, canonical syntax (`=`, `.` only). Deliberate C quirks kept for byte identity are documented in the file header and the report.
- `python tools/axtest.py --compiler build/axiom0.exe --build-dir build --filter selfhost/drop -j 6` (snapshot, task files only): `TOTAL 28 PASS 28 FAIL 0 SKIP 0 XFAIL 0` (9 `qa_drop_dNN.ax` x [interp, native, native-O1] + `drop_oracle.test`). No mode restriction, no `native-after`, no xfail/skip in the task's tests.
- `gen_drop_tests.py check --oracle ...`: `OK drop oracle goldens (10 fixtures)` (C oracle output equals committed goldens, including the synthetic destructor `d10` vs C elaboration of `d10_destructor.impl.ax`). Regenerating all goldens and bundles with the generator reproduced the committed files byte for byte (cmp on every fixture/bundle), i.e. goldens are reproducible.
- Full suite in the snapshot (`-j 6`, with my added test): `TOTAL 1776 PASS 1773 FAIL 3`. The 3 non-passes were all TIMEOUT under 6-way parallel load: `selfhost/lexer/qa_lexer_corpus_neg_a` and `_neg_b` [interp] (30 s limit, other task) and my own `qa_drop_d11` [interp] (1200 s). Re-run individually: lexer neg a/b `TOTAL 6 PASS 6`; `qa_drop_d11` `TOTAL 3 PASS 3` (about 8 min wall when run alone). No real failure, crash or flake.
- Acceptance criteria: (1) drop.ax complete and readable: met. (2) tests pass in interpreter and native modes: met (interp, native, native-O1). (3) elaborated drop calls and cleanup CFG match: `axiom0 inspect --emit=mir` never runs drop elaboration, so the comparison is made against the C `ax_mir_drop_elaborate` through the new oracle driver, whose `--pre` mode is itself verified equal to `inspect --emit=mir`; Axiom output equals both goldens byte for byte on 9 fixtures (+ the synthetic destructor pass): accepted as the meaning of the criterion. (4) Full suite pass, warning free, archcheck clean: met (see above). (5) Report with exact `## Files changed`: present and matches the changes listing (my additions below are extra).
- Spec check: behaviour is the C implementation's (SPEC-20 port, 0167/0152); no diagnostics emitted by this module, so no `diag/codes` registration needed; deviations from C: none.

### Boundary / extra test written (QA)
New fixture `d11_qa_edges` (generated via the task's own `gen_drop_tests.py`, goldens from the C oracle): a function with no droppable locals (no flags allocated), a droppable local created and conditionally moved inside a `while` body, a move in both arms of an if/else (two flags), a droppable call result bound to a local, and a conditionally moved tuple containing an enum with droppable payload plus a struct with two droppable fields (nested enum-in-tuple, flag test + multi-level field expansion). Axiom elaboration matches the C goldens for before/after-elaboration MIR in interp, native and native-O1. Added one `("d11", "d11", ["d11_qa_edges"])` line to `GROUPS` in `gen_drop_tests.py` (task-owned path). Note: this test needs about 5-8 minutes alone in interp; under heavy parallel load it can hit its 1200 s timeout (as every selfhost interp test in this family can), so re-run it alone if it times out.

### Findings
None blocking. Documented out-of-scope limits (report Follow-ups 1-7: front end drops bodies of files with `impl`, generic struct literals rejected so `d08` has C goldens only, mangled `compiler/kernel/interner.ax` so the harness uses the QA-accepted front-end copies, `mir/mod.ax` not re-exporting the drop API, interpreter statement-by-value loss) are front-end/interpreter bugs outside this task's paths and are not criteria of T082d. Notes for the architect (follow-up tasks, not FAILs): (a) re-export `mir_drop_elaborate` & co. in `compiler/mir/mod.ax`; (b) add `d08_generic_containers` to `GROUPS` once generic literals type-check; (c) harness should be re-pointed at `compiler/` front-end modules once interner.ax/session.ax build (T076-style bundler).

## Files changed
- tests/selfhost/drop/fixtures/d11_qa_edges.ax
- tests/selfhost/drop/fixtures/d11_qa_edges.pre.mir
- tests/selfhost/drop/fixtures/d11_qa_edges.drop.mir
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/gen_drop_tests.py

VERDICT: PASS round=0
