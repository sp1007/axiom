# T079b QA - Port recursive-descent parser to Axiom

## Round 0

### Checks performed
- `taskctl.py changes T079b`: 16 `stage` lines (report, `compiler/syntax/parse.ax`, 14 tests under `tests/selfhost/parse/`),
  no `REFUSED` line. Report ends with `STATUS: COMPLETE round=0`.
- Snapshot `build-snap-T079b`: `cmake ... -G Ninja -DCMAKE_C_COMPILER=gcc` + `--clean-first` rebuild: 0 warnings
  (grep -ci warning = 0). axiom0 sources are untouched by the task (no `harness_check`/AX0 freeze issue, no shared file edited).
- `python tools/archcheck.py` (in snapshot): 188 files scanned, 0 violations.
- Acceptance "complete and readable": `parse.ax` is 2,922 lines in one file, 0 lines over 120 columns, no
  TODO/FIXME/BOOTSTRAP-SHORTCUT; the embedded copy inside the test bundles equals `compiler/syntax/parse.ax`
  (2,489 consecutive non-`use` lines identical, remainder is the intrinsic/test-driver preamble). Single-file choice is
  recorded in the report, which the coordinator said is acceptable.
- Full suite in snapshot: `python tools/axtest.py --compiler build/axiom0.exe` -> `TOTAL 1631 PASS 1627 FAIL 4`:
  - `selfhost/lexer/qa_lexer_corpus_neg_a` and `_neg_b` `[interp]` TIMEOUT (30 s) under full-suite load: pre-existing,
    outside this task's paths, not a T079b finding (same family as the note in the gate request).
  - `selfhost/parse/qa_parse_corpus_b` and `qa_parse_recovery_b` `[interp]`: `AX_UNSAFE_INTERP_UB: out-of-bounds pointer
    access`, exit 125. This IS a T079b finding (F1).
- Repeated `axtest selfhost/parse` (default `-j 8`): run 1 TOTAL 40 FAIL 2 (recovery_a, recovery_b), then 40/FAIL 1
  (recovery_a), 40/FAIL 2 (corpus_a, corpus_d), 40/FAIL 2 (corpus_c, recovery_b). The same tests pass when rerun alone.
- Differential spot checks I added (see "Files changed"): 20 extra sources compared byte-for-byte (AST text + human
  diagnostics) against `axiom0 inspect --emit=ast` through the Axiom parser: 19 identical categories pass; tuple structs
  diverge (F2).

### Findings

**F1 (FAIL) - non-deterministic interpreter failures of the new tests (acceptance: "Unit tests pass in both interpreter
and native modes", QA rule: a flaky test is a FAIL).**
- Tests: `tests/selfhost/parse/qa_parse_corpus_{a..j}.ax`, `qa_parse_recovery_{a,b}.ax`, `[interp]` only.
  Native and native-O1 never failed.
- Observed: in 4 of 5 consecutive `axtest selfhost/parse` runs one or two of these fail with
  `error[AX_UNSAFE_INTERP_UB]: out-of-bounds pointer access` (exit 125); the full suite run also hit it twice.
- Repro (standalone, no runner): run `axiom0 run --interp --std-root std tests/selfhost/parse/qa_parse_recovery_b.ax` 40
  times with 8 in parallel: 16 of 40 fail; with 1-2 in parallel: 0 of 40 fail. Occurs also with 2 workers plus 12
  busy-loop processes (2 of 20). I.e. it depends on machine load/timing, not on the input.
- Diagnosis (debug build of the snapshot's axiom0 with a print in `ax_interp_validate_raw_ptr`,
  `src/interp/interp.c:205`): the failing access is always a 56-byte access whose pointer resolves to a synthetic
  allocation of 8 bytes with `call_depth` 63 or 141 (an address-taken stack local of an earlier, already returned call:
  `alloc 3360` / `alloc 35714` out of 112,714 registered; the position is stable run to run, only whether it triggers
  varies). The interpreter recovers synthetic addresses from host addresses (`find_synth_addr`, `src/interp/interp.c`
  ~line 236) and never retires stack allocations when a frame returns, so a reused host stack/heap address can match a
  stale entry; whether that happens depends on host allocator/stack placement, hence the load dependence. The
  frozen interpreter is where the root cause lives (cf. the report's Follow-up 1 about the same allocation table), but
  the task cannot be accepted with tests that fail 5-40% of the time in the mode its acceptance requires.
- Expected: deterministic pass. Possible resolutions (engineer/architect to choose and record): (a) find and avoid the
  parse.ax pattern that produces an 8-byte stack local whose address is later used as a 56-byte object (e.g. the
  `Token`/`Span` copies through `address_of`), (b) an `AX0-FIX-<nn>` task for the interpreter (retire/fix stack allocs and
  use a binary search table), after which these tests stay as they are, (c) architect-approved `native-after`/xfail style
  directive with an open task, since SPEC rules do not allow silently dropping interp mode.

**F2 (FAIL, must be documented or fixed) - undocumented behavioural difference to `parse.c` for tuple structs.**
- `bootstrap/axiom0/src/syntax/parse.c:1630-1636` parses every tuple-struct field type twice (`*curr = parse_type(p);`
  appears two times in the loop), so `struct T(u8);` produces `AX_PARSE_EXPECTED_TYPE` ("Expected type" at the `)`) and
  `AX_PARSE_UNCLOSED_DELIMITER`, AST `(ItemStruct (Vis priv) "T" true (TypeError))`. `compiler/syntax/parse.ax:2676`
  (`parse_struct_item`) parses the list once and accepts the item, as `spec/SPEC-02-grammar.md` AXS-GRM-029 requires
  (`struct UserId(u64)`).
- The Axiom behaviour is the better one, but the report states "Spec deviations: none" and "689 identical"; this
  deviation is not recorded anywhere, and the task's acceptance compares with `axiom0 inspect --emit=ast`. Expected: either
  replicate the C behaviour (differential tests in T079 would then match) or record the deviation (report Spec deviations
  and/or a note for the architect/AX0-FIX for the C bug) and keep a regression test for it.
- Repro: `tests/selfhost/parse/qa_parse_qa_tuple_struct.ax` (native; sources `struct T(u8);`, `struct T(u8, i32)`,
  `struct T(x);`+fn, `struct T(a, b);`, `struct T(u8, i32);`); currently exits with code 10 (first case differs).
  If the decision is "document, keep the better behaviour", regenerate the expectations of that test from the Axiom output
  or turn it into a ui test with the new diagnostics-free expectation.

### Notes (not findings)
- The report claims throw-away differential evidence (707 files, 4,800 mutations); not reproducible from committed
  files, but the committed 38-file corpus plus my 20 extra cases agree except F2.
- Observed while writing the QA test, outside the task: an `axiom0` miscompile/semantic oddity in the frozen compiler:
  `if !chk(1) { print("X\n"); bad = bad + 1; }` followed by `if bad != 0 { ... }` does not take the second branch (both
  `run --interp` and native). Minimal repro in scratchpad `m2.ax`. Worth an architect look (AX0-FIX candidate), not a
  T079b issue.
- `ast_format_derive` (T079a) dead code and the packed `compiler/diag/code.ax` lines mentioned in the report's follow-ups
  are outside T079b's paths.
- The two generic-argument/`<` ambiguity (`a.len < b.len {`) behaves identically in C and Axiom parsers.

### Files changed
- tests/selfhost/parse/qa_parse_qa_edge.ax
- tests/selfhost/parse/qa_parse_qa_tuple_struct.ax

### Follow-ups for the architect
1. Interpreter: stale stack allocations + host-pointer-to-synthetic-address recovery (`find_synth_addr`) cause
   load-dependent `AX_UNSAFE_INTERP_UB`; decide between AX0-FIX and a parse.ax-side workaround (F1).
2. Tuple-struct C bug in the frozen `parse.c` (double `parse_type`), decide replicate vs. document (F2).
3. Possible semantic/codegen bug in axiom0 described in Notes.

VERDICT: FAIL round=0

## Round 1

### Checks performed
- Verified Round 0 findings F1 and F2:
  - **F1 (resolved)**: All 16 test files in `tests/selfhost/parse/` now allocate `CompilerSession`, `parse_arena`,
    `out_ast`, and `out_err` in `main` (`call_depth == 1`, `alloc_id` 24..30) and pass them by `mut_view` into
    `verify_case`/`run_and_verify_parse`. Confirmed via interpreter allocation-table trace that all `REF56` and `VAL56`
    (`address_of`/`address_of_mut` on `StrInterner`) operations deterministically resolve to `found_id=24`
    (`found_size=192`, `depth=1`, `live=1`) at the head of `ctx->allocs`, eliminating the load-dependent collision
    with unretired stack locals from returned frames.
  - **F2 (resolved)**: The intentional bug-fix difference vs `bootstrap/axiom0/src/syntax/parse.c:1630-1636` (where
    `parse.c` calls `parse_type` twice per tuple-struct element) is documented in `T079b-report.md` and
    `tests/selfhost/parse/qa_parse_qa_tuple_struct.ax` now verifies the `SPEC-02` `AXS-GRM-029` single-parse tuple
    struct AST output and passes (`0` exit code).
- Ran `python tools/axtest.py --compiler bootstrap/axiom0/build/axiom0.exe selfhost/parse` (`-j 8`):
  `TOTAL 44 PASS 44 FAIL 0 SKIP 0 XFAIL 0` across all 16 test files (`[interp]`, `[native]`, `[native-O1]`).
- Ran `python tools/archcheck.py`: 0 violations.
- Checked `taskctl.py changes T079b`: all 18 changed files (report + `compiler/syntax/parse.ax` + 16 test files) are
  within `T079b` allowed paths, 0 `REFUSED` lines.

### Findings
None.

VERDICT: PASS round=1

