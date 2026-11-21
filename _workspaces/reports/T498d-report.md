# T498d report — stale slice iterator move tests after Copy arrays

## Round 0

### Cause
Since T498 (ADR-0044 section 3, SPEC-10 AXS-OWN-003) `[N]T` is Copy when `T` is Copy, so `consume(arr)` over a `[3]u8` /
`[4]u8` copies the array, the owner stays `OWNED` and no `AX_CAP_OUTLIVES_OWNER` is correct. The compiler is right; the two
ui tests were stale. No compiler source, spec or baseline file was touched; the capability check is not weakened.

### Changes
- `tests/ui/slice/iter_move.ax`, `tests/ui/slice/qa_slice_iter_move.ax`: the owner is now `[3]Tok` / `[4]Tok` with
  `struct Tok { v: u8 }` (not Copy), so `consume(arr)` really moves it while `view<[Tok]>` is live. The
  `//~ ERROR AX_CAP_OUTLIVES_OWNER` stays on the `consume(arr)` line; the view is still used after the move and only the Copy
  field `.v` is read through it, so exactly one diagnostic is produced.
- `tests/run/slice/copy_array_owner_view.ax` (new, `// test: run`, exact stdout `60\n10\n60\n30\nOK copy_array_owner_view\n`):
  `[3]u8` owner, struct holding `view(arr)`, `consume(arr)` by value (returns 60), the view iterated (sum 60, `s[0]` = 10),
  `arr[2]` read again (30). Header cites SPEC-10 AXS-OWN-003 / ADR-0044 section 3.
- Authoring note: `while it.i < n {` / `while it.i < len(it.s) {` parse as generic arguments in axiom0 (AX_PARSE_EXPECTED_TOKEN);
  the tests use a local `i` as the original test did.

### Evidence (all in `build-snap-T498d`, stage-0 clang Release 132/132 and 0 warnings, `build_axiomc.py` stage 3: BUILD-AXIOMC OK,
fixed point OK, `_workspaces/T498d_build.log`, `_workspaces/T498d_axiomc.log`)
- `axtest --compiler build/axiomc2.exe --no-cache --filter slice/`: `TOTAL 40 PASS 40 FAIL 0` (whole tests/ui/slice and
  tests/run/slice groups plus other ids matching "slice/"). The WEAK-NATIVE 16 in that run belong to pre-existing
  assert/exit-code-only slice tests; `--filter copy_array_owner_view` reports `WEAK-NATIVE 0`, 3/3 modes pass.
- Mutation 1 (ui): element type changed back to `u8` in the snapshot copy of `iter_move.ax` ->
  `FAIL ui/slice/iter_move.ax: missing diagnostics: ERROR AX_CAP_OUTLIVES_OWNER at line 14`; restored (diff vs main tree clean).
- Mutation 2 (native proof): `stdout: 60` changed to `61` in the snapshot copy of `copy_array_owner_view.ax` ->
  interp, native and native-O1 all FAIL with `stdout differs at byte 1` (expected 61..., actual 60...); restored.
- Native evidence: exact `stdout:` compared in all three modes (no assert-only legs).
- taskgate: `python tools/taskgate.py --task T498d --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2
  --extra ui/slice/iter_move,ui/slice/qa_slice_iter_move,run/slice/copy_array_owner_view` -> exit 0: total 55 results, 55 PASS,
  0 FAIL; own+affected 5 each, smoke 31 ids across 28 groups; archcheck clean (232 files, 0 violations); baseline OK; failing
  ids none; WEAK-NATIVE 0 in the task's own/changed tests (3 in the whole run, smoke picks). Log `_workspaces/T498d_taskgate.log`.
- Axiom0 note: the frozen stage-0 compiler (`build/axiom0.exe`) still rejects the Copy-array shape with
  `AX_CAP_OUTLIVES_OWNER`; T498 landed in the self-hosted `compiler/`, and the gate compiler is axiomc2 as in the harness. Not
  a defect of this task.

### Follow-ups
- None.

## Files changed
- tests/ui/slice/iter_move.ax
- tests/ui/slice/qa_slice_iter_move.ax
- tests/run/slice/copy_array_owner_view.ax

STATUS: COMPLETE round=0
