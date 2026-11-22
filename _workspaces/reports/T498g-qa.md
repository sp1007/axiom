# T498g QA

## Round 0

### Scope and build evidence
- Snapshot `build-snap-T498g` (HEAD f0832f4 + T498g change set); `taskctl.py changes T498g` lists the report,
  `compiler/types/typeck.ax` and the three engineer tests. No REFUSED line other than my own two added tests
  before they were listed below (resolved by `## Files changed`).
- Diff of the change set: one hunk in `finalize_ptr_substmap` (typeck.ax): the skip of callees in
  `TY_BUILTIN_ADDRESS_OF ..= TY_BUILTIN_NULL_MUT` is removed; `len`, `print`, `print_int`, `drop` are still skipped.
- Snapshot compilers are built from the snapshot sources: `build/axiomc2.exe.inputs.json`,
  `axiomc2_O1`, `axiomc3_O1` all record typeck.ax sha256 `6e628bcc450bf4ba...` (= snapshot file) and the
  same output sha256 `cb258e5a0097d469...` (stage-2 == stage-3 fixed point).
- Root cause confirmed by reading `finalize_ptr_substmap` and by behaviour (below): an inferred `T` of a
  raw-memory intrinsic reached MIR as an unresolved `TY_VAR` (size 0, clamped to 1 byte). Not array specific.
  The fix is in the right layer (the THIR substitution is the contract of MIR builder / mono collection); no
  backend change needed, so interp, native -O0 and -O1 are all fixed by the same change.

### Checks
1. Own tests, `python tools/axtest.py --compiler build/axiomc2.exe -j 2 --no-cache run/mem_generic_array`:
   `TOTAL 13 PASS 13 FAIL 0`, `WEAK-NATIVE 0` (3 engineer tests + 2 of mine, interp/native/native-O1).
   Every run test has an exact `stdout:` (native evidence satisfied).
2. Pre-fix evidence: the HEAD-built stage-2 compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_fd6482b056a619cc.exe`)
   run on the same directory: `TOTAL 13 PASS 1 FAIL 12` (only my ui test passes there; it is a guard, see below). Failures are wrong
   stdout for swap_repro/swap_kinds and `AX_UNSAFE_INTERP_UB misaligned pointer access` / wrong bytes for
   counts_bytes_ptr and qa_edge_inferred, in all three modes.
3. Native-evidence mutation (snapshot only, restored, `diff` against main tree clean): in
   `swap_repro.ax` `// stdout:` changed `10 20 30 40` -> `10 20 30 41`, run
   `axtest.py ... --no-cache run/mem_generic_array/swap_repro` -> `FAIL` in interp, native and native-O1
   (`stdout differs at byte 13`), 0 PASS. (A first attempt with sed did not change the file and passed; the python
   replace asserted the change.)
4. Unconstrained `T` still errors sensibly (no silent 1-byte): scratch checks with `axiomc2 run`:
   `let p = null()`, `size_of()`, `is_null(null_mut() as *const u8)` -> `error[AX_TYPE_UNKNOWN]: the type cannot be inferred`.
   Locked in by new test `qa_unconstrained.ax` (ui, `//~ ERROR AX_TYPE_UNKNOWN` x2; passes before and after the fix, it is a regression guard for the
   resolver now touching these entries).
5. Dump/golden parity (T156 skip): `tests/hir`, `tests/inspect`, `tests/mir`, `tests/typeck` plus
   `std/`, `run/interp_big_args`, `run/intrinsics`, `run/parity/intrinsics`, `run/native_ptr`, `run/ptr`,
   `selfhost/mir/`, `selfhost/interp/` (`_workspaces/T498g_qa_suites.log`, -j 2, baseline file passed):
   `TOTAL 654 PASS 636 FAIL 4 SKIP 1 XFAIL 13`. The 4 FAIL lines are (a) the known `std/num/static_dispatch_xfail.ax` XPASS
   x3 (not a finding, per instruction) and (b) one `std/async/waker_qa/qa_wake_during_poll.ax [native]` (see Findings/Flake).
   No dump or golden test failed, so no golden needed updating. The task's report claim (3554 results, only the XPASS id failing)
   for `run/ std/ selfhost/mir selfhost/interp` is consistent with this.
6. Taskgate (`python tools/taskgate.py --task T498g --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`,
   run after refreshing the snapshot with my tests; wall 1109 s): **exit 0**.
   - Derivation: changed = report, `compiler/types/typeck.ax`, 5 test files; affected set from the change set =
     77 ids / 126 results (map `compiler/types` -> `tests/typeck`, `tests/ui/typeck`, `selfhost/types`; every selfhost group whose bundle embeds
     `compiler.types.typeck`: backend, driver_full, drop, interp_opt, lir, mir, obj_link_driver, opt, own_mir_verify, traits, typeck, typeck_traits, verify, ...).
   - own 5 ids / 13 results PASS; affected 77 ids / 126 results (125 PASS, 1 SKIP); smoke 31 ids / 52 results PASS.
   - TOTAL 106 ids / 176 results: PASS 175, FAIL 0, SKIP 1, XFAIL 0. Failing ids: none. `BASELINE OK`. archcheck clean
     (232 files, 0 violations). WEAK-NATIVE 3 in the run, 0 in the task's own/changed tests. Cache: 25 cached, verification sample
     20 of 38 hits, mismatch none. UNMATCHED none, UNRESOLVED none.
   - Always-included smoke cases ran: `run/str/hello.ax` (Xin chao line), `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`, archcheck.
7. Scope/shared-file checks: only `compiler/types/typeck.ax` (in `paths:`) + tests under `tests/run/mem_generic_array`; no
   change under `bootstrap/axiom0`, `std/`, `spec/`, `docs/`, no shared file (`axtest.py`, CMake, `diag/codes.def`, `pipeline.c`). No new
   diagnostics. No BOOTSTRAP-SHORTCUT. Run tests are three-mode (no `modes:` restriction, no `native-after`).

### Adversarial tests added (step 5)
- `tests/run/mem_generic_array/qa_edge_inferred.ax` (run, interp/native/native-O1, exact stdout, passes in all three; fails on the HEAD compiler in all three).
  Covers: `size_of/align_of/needs_drop` of instantiated `T` (struct of 3 u64 = 24/8, Drop struct); a nested generic instantiation
  (`swap_twice<U>` -> `swap<T>`, U = `[3]u64`; three swaps = one swap); a struct `T` of 24 bytes through `swap`; inferred `ptr_add`/`ptr_sub`
  on a `*const u64` in a NON-generic function; `null()`/`null_mut()`/`is_null` with `T` inferred from the annotation (`*const u64`,
  `*mut Pt`) plus `ptr_add` from a live pointer; `drop_in_place` with inferred `T` through a generic wrapper (runs the Drop impl exactly once per call);
  `ptr_copy_nonoverlapping` count 2 over a tuple `(u32,[2]u64)` array; `ptr_write_bytes` over `u32` count 2 (clears 8 bytes, not 2).
  (The trailing `DDD` is the scope-end drops of `arr` x2 and `one`, which is intentionally dropped twice; `Tr::drop` only prints.)
- `tests/run/mem_generic_array/qa_unconstrained.ax` (ui): two genuinely unconstrained `null()` / `null_mut()` -> `AX_TYPE_UNKNOWN`.

### Findings
- None caused by the task.
- Flake observed (not a finding against T498g, reported for the architect): `std/async/waker_qa/qa_wake_during_poll.ax [native]` printed
  `lost 1` instead of `lost 0` once, during the 654-test `-j 2` run on the loaded shared machine; not in the baseline. It passed 4/4 with the snapshot
  compiler and 4/4 with the HEAD compiler alone (`--no-cache -j 1/2`), and the whole `std/async/` group (96 tests) passed with the snapshot compiler
  `--no-cache -j 2` twice (and once with the HEAD compiler: 96/96). The flake did not reproduce at HEAD under load either, so HEAD-vs-fix identity is not demonstrable;
  it is not baseline-listed, hence reported as a timing flake, not a regression. The test never calls a pointer intrinsic with an inferred sizing `T` (its `ptr_copy_nonoverlapping` calls are explicit `<u8>` /
  `<*mut ...>`; the inferred `address_of*` calls only build pointers), and its design counts a task as lost after a fixed number of main yields
  (line ~3941), i.e. it is load/timing sensitive. See "Follow-ups".

### Follow-ups
- (architect) `tests/std/async/waker_qa/qa_wake_during_poll.ax`: timing-sensitive "lost" count flakes under heavy machine load (T421a owner); consider a
  larger yield budget or a `nocache`/serial marker. Not related to T498g.
- (architect, already known) remove the `xfail:` from `tests/std/num/static_dispatch_xfail.ax` (folded into T499b).
- (optional, from the engineer's report) make the MIR builder ICE on a `TY_VAR` element type of a type-argument intrinsic so a future unresolved
  substitution fails loudly rather than being sized as 1 byte.

## Files changed
- tests/run/mem_generic_array/qa_edge_inferred.ax
- tests/run/mem_generic_array/qa_unconstrained.ax

VERDICT: PASS round=0
