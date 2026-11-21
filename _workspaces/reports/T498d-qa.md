# T498d QA

## Round 0

Scope: tests-only change (3 files under `tests/`), no compiler/spec/baseline edits. All runs inside `build-snap-T498d`
(stage-0 clang Release; compiler under test `build/axiomc2.exe`).

### Checks
1. `taskctl.py changes T498d`: stages the report and the three test files only; 0 REFUSED lines.
2. Acceptance, own tests: `axtest --no-cache --filter iter_move` -> `TOTAL 2 PASS 2`; `--filter copy_array_owner_view` ->
   `TOTAL 3 PASS 3` (interp, native, native-O1), WEAK-NATIVE 0.
3. Mutation (1), ui: in the snapshot both ui tests were rewritten back to `u8` elements (`[3]u8`/`[4]u8`, plain literals,
   `it.s[i]`). Result: `FAIL ui/slice/iter_move.ax: missing diagnostics: ERROR AX_CAP_OUTLIVES_OWNER at line 17` and
   `FAIL ui/slice/qa_slice_iter_move.ax: ... at line 15`. Restored (cmp equals main tree). So the move of a non-Copy owner is
   what triggers the diagnostic.
4. Meaningfulness (not weakened): both ui tests build a `view<[Tok]>` over a `[N]Tok` owner (`Tok` has no Copy), call
   `consume(arr)` (a by-value move, one `//~ ERROR AX_CAP_OUTLIVES_OWNER` on that line), and use the view afterwards
   (`len(it.s)` and `it.s[i].v` in the loop). Exactly one diagnostic is expected and the runner enforces an exact set. Extra
   probe (scratch file, not committed): the same non-Copy shape with the view used only BEFORE `consume(arr)` compiles and runs
   (prints 60), so the diagnostic is tied to the view being live across the move, not to the move alone.
5. Mutation (3), native evidence: in the snapshot `// stdout:` changed from `60\n10\n60\n30` to `60\n10\n61\n30`. All three
   modes FAIL with `stdout differs at byte 7` (expected `...61...`, actual `...60...`). Restored (cmp equal). The test checks
   exact stdout in every leg (not assert-only).
6. Spec check: the header of `copy_array_owner_view.ax` cites SPEC-10 AXS-OWN-003 / ADR-0044 section 3; behaviour matches
   (Copy array: owner stays OWNED, view reads original bytes). Capability check not weakened, no xfail, no baseline edit.
7. Whole `slice/` groups: `axtest --no-cache -j 2 --filter slice/` -> `TOTAL 40 PASS 40 FAIL 0` (the 16 WEAK-NATIVE are
   pre-existing assert/exit-only tests not touched by this task).
8. taskgate (`-j 2`, own tests added via `--extra`): `TASKGATE T498d exit=0`, `TOTAL 55 PASS 55 FAIL 0`; own 4 ids / affected 3 /
   smoke 31 ids over 28 groups; archcheck clean (232 files, 0 violations); baseline OK; failing ids: none; WEAK-NATIVE 0 in the
   task's own/changed tests; no UNMATCHED/UNRESOLVED. Log `_workspaces/T498d_qa_taskgate.log`.

### Findings
None.

### Follow-ups
None.

## Files changed
- none (no tests added by QA; the extra probe was a scratch file outside the repo)

VERDICT: PASS round=0
