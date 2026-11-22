# T496a QA — inclusive sub-range `s[a..=b]` / `s[..=b]` (ADR-0045)

## Round 0

### Scope and checks
- Report ends with `STATUS: COMPLETE round=0`. `taskctl.py changes T496a`: no REFUSED line for the engineer's change set
  (compiler/mir/builder.ax, compiler/hir/lower.ax, 15 run tests, 1 ui test). The only REFUSED seen was for my own 8 added
  tests before this file existed; they are listed under `## Files changed` below.
- Code review of the diff (snapshot `build-snap-T496a`, HEAD ab771643):
  - `mb_emit_range_bounds_check`: inclusive end is checked with `LT` (`b < len`) in the bound's own width (u128 for 128-bit
    bounds, usize otherwise); exclusive path unchanged (`LE`, `start <= end`).
  - `mb_build_range_subslice_lvalue`: after the check (and the ADR-0044 §1 truncation) `b + 1` is computed in usize
    (`mb_emit_usize_add_one`), so no overflow; then `a <= b + 1` on usize values (start already `<= len`, so its truncation is exact).
    The projection uses `b + 1`. Matches ADR-0045.
  - `lower.ax`: only a range with `is_inclusive` and a null `end_expr` reports `AX_PARSE_EXPECTED_EXPR` (existing code, no new
    registration needed). Range patterns (`pat`), `for x in a..=b` and `a..=b` expressions with an end are untouched.
    Minor note: the diagnostic is emitted in lowering rather than the parser (outside the task's paths); acceptable and documented.
- Build: snapshot `build/axiomc2.exe` (stage-2 built by the engineer from the snapshot sources; sources unchanged since).
  `tools/build_axiomc.py` fixed point was reported OK by the engineer (log `_workspaces/T496a_build.log`); not re-run.

### Acceptance evidence
- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --no-cache -j 2 --filter slice_inclusive/`
  -> `TOTAL 69 PASS 69 FAIL 0 SKIP 0 XFAIL 0` (46 engineer + 23 mine; interp / native / native-O1), `WEAK-NATIVE 0`.
- `len(s[0..=2])` = 3 in interp, native, native-O1 (`basic_view.ax`, exact stdout). MAX bounds (usize/u64/u128, u128 alias 2^64+2,
  u8 255, negative i32/i8/i128) trap with exit 101 and `index out of bounds`, never wrap.
- Native evidence (4a): every touched native leg compares an exact `stdout:` and `exit:` (101 for traps, with `stderr-contains`).
  Liveness proof: in the snapshot I changed `qa_wide_len_narrow_bound.ax` `stdout: 256 200` to `257 200`; interp, native and
  native-O1 all FAILED (`stdout differs at byte 2`); restored (diff clean) and it passes again (3/3).
- Mutation vs HEAD: with the pre-fix compiler `_workspaces/artifacts/compiler-cache/axiomc2_O1_b64ea0de4626c290.exe` my 23 runs give
  `TOTAL 23 PASS 9 FAIL 14` (b == len traps return exit 0, valid inclusive slices wrongly trap/shorten). The fixed compiler passes all.
- Taskgate (inside the snapshot, after `taskctl.py snapshot T496a` refresh with my tests):
  `python tools/taskgate.py --task T496a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T496a.json`
  -> `TOTAL 440 PASS 438 FAIL 0 SKIP 2 XFAIL 0`, `TASKGATE T496a exit=0`, BASELINE OK, failing ids none, archcheck clean (232 files,
  0 violations), WEAK-NATIVE 3 in the run / 0 in the task's own/changed tests. No UNMATCHED / UNRESOLVED / MAP-NOTE / DEFERRED /
  CACHE-MISMATCH lines. Cache: 220 hits, verification sample 20 of 107 hits, mismatch none. Log: `_workspaces/T496a_qa_taskgate.log`.

| part | ids | results | PASS | FAIL | SKIP |
|---|---|---|---|---|---|
| own | 24 | 69 | 69 | 0 | 0 |
| affected | 197 | 393 | 391 | 0 | 2 |
| smoke | 31 | 50 | 50 | 0 | 0 |
| total (dedup) | 225 | 440 | 438 | 0 | 2 |

- Affected-set derivation (rules in the log): `compiler/mir/builder.ax` -> map `compiler/mir` -> `tests/selfhost/mir`, `selfhost/drop`,
  `tests/verify`; `compiler/hir/lower.ax` -> map `compiler/hir` -> `tests/selfhost/hir`; plus every selfhost group whose bundle embeds
  `compiler.hir.lower` / `compiler.mir.builder` (generator check) and the regenerated bundle test files. Selfhost groups mir and hir are
  included (`selfhost/mir/*`, `selfhost/hir/*`). Smoke always-cases: `run/str/hello.ax` (Xin chao), `ui/typeck/type_unknown.ax`,
  `diff/002-arithmetic.ax`, `diff/opt/const_fold.ax`, archcheck. The 2 SKIPs are in the affected set and are pre-existing skips.
- Not re-run by me: the engineer's wider acceptance-group run (3522 PASS, `run/`, `conformance/p12/`, `run/index_128_range`);
  the `tests/run` index_128_range / selfhost mir ids are inside the affected set above (all PASS).

### Boundary cross-check: tests I added
Adversarial cases the engineer did not cover (all pass, interp + native + native-O1 where applicable):
- `qa_const_and_contexts.ax` (`flags: -O1`): literal bounds (const-foldable) incl. `7..=7`, `3..=2`, `..=3`; composed `s[1..=5][1..=2]`;
  `for x in 0..=5` / `1..=6` and match patterns `0..=3`/`4..=9` unaffected by the lower.ax change; bounds evaluated exactly once and in
  order (`s[tick()..=tick()]`); exclusive `s[2..5]`, `s[5..]`, `s[..2]`, `s[..]` unchanged.
- `qa_wide_len_narrow_bound.ax`: u8 255 on a 300-element slice (256 elements, no 8-bit wrap), i8 127, usize `299..=299`, `300..=299` empty.
- Traps (exit 101, stdout `before`, stderr `index out of bounds`): `qa_trap_const_end_eq_len` (literal `0..=8` on 8 elements, -O1 must not fold),
  `qa_trap_empty_source_prefix0` (`..=0` on an empty slice), `qa_trap_u8_255_small` (u8 255 on 8 elements), `qa_trap_i8_negative`
  (`0i8..=-1i8`), `qa_trap_mut_view_end_eq_len` (mut_view, write never happens), `qa_trap_exclusive_unchanged` (`s[0..8]` valid, `s[0..9]` traps).

### Spec / scope checks
- Behaviour matches ADR-0045 (`b < len` in own width, `a <= b + 1`, `a == b + 1` empty). No new diagnostic code (reuses
  `AX_PARSE_EXPECTED_EXPR`). No `BOOTSTRAP-SHORTCUT`. No `bootstrap/axiom0` change; no shared-file edit (axtest.py, CMake, pipeline.c,
  codes.def untouched). All run tests use the default modes (no mode restriction). Selfhost bundles not listed.

### Findings
None blocking.
- Note (non-blocking): the `a..=` check lives in `compiler/hir/lower.ax` instead of the parser (reported by the engineer; follow-up suggested).
- Note: `str[a..=b]` sub-slicing was not exercised (no test; `TY_STR` shares the code path via `mb_range_base_is_checked`).

### Follow-ups
- Optional: move the `a..=` diagnostic into `parse_binary_suffix` when `compiler/syntax/parse.ax` is next touched.
- Optional: add a `str[a..=b]` run test if/when `str` range slicing is covered by a task.

### Files changed
- tests/run/slice_inclusive/qa_const_and_contexts.ax
- tests/run/slice_inclusive/qa_wide_len_narrow_bound.ax
- tests/run/slice_inclusive/qa_trap_const_end_eq_len.ax
- tests/run/slice_inclusive/qa_trap_empty_source_prefix0.ax
- tests/run/slice_inclusive/qa_trap_u8_255_small.ax
- tests/run/slice_inclusive/qa_trap_i8_negative.ax
- tests/run/slice_inclusive/qa_trap_mut_view_end_eq_len.ax
- tests/run/slice_inclusive/qa_trap_exclusive_unchanged.ax

VERDICT: PASS round=0
