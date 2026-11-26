# T428j QA — aggregate assignment reading its own destination

## Round 0

Snapshot `build-snap-T428j` = HEAD e085e8e6 + T428j change set (`compiler/mir/builder.ax`,
`tests/run/agg_self_assign/*`) + the 3 QA tests below; refreshed with `taskctl.py snapshot T428j`
(13 changed files, 0 deleted; bundles regenerated: 36 generators, 60 files, no BUNDLES FAILED).

### Checks performed

1. **Change set.** `taskctl.py changes T428j`: stages the report, `compiler/mir/builder.ax` and the 8
   test files. No REFUSED line. `builder.ax` is the task's `locks:` entry; tests are under `paths:`.
   No shared-file edits.
2. **Build / fixed point (snapshot).** `cmake --build build`: no work, no warnings.
   `python tools/build_axiomc.py --out build --root . --stage 3 --full-chain`
   (`_workspaces/T428j_qa_build.log`): stage 2 (O1) rebuilt (346 s), then
   `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == b3c75f83153167a9...`. This
   matches the engineer's hash.
3. **Own tests plus QA tests** (`axtest.py --compiler build/axiomc2.exe --no-cache -j 2 run/agg_self_assign`,
   `_workspaces/T428j_qa_own.log`): `TOTAL 28 PASS 25 FAIL 3`, `WEAK-NATIVE 0`. All 22 engineer
   entries pass: 7 run files × interp/native/native-O1, plus the MIR golden. The 3 failures are
   the new QA test `qa_alias_ptr_fields.ax` in all three modes (Finding 1).
4. **Native evidence.** Every run test has an exact `// stdout:`. Mutation proof, snapshot only: I
   changed `array_rotate.ax` line 3 from `stdout: 3 1 2...` to `3 3 3...` and ran
   `axtest.py ... run/agg_self_assign/array_rotate`. It failed in `[interp]`, `[native]` and
   `[native-O1]` (`TOTAL 3 PASS 0 FAIL 3`). I restored the file and checked it with `cmp` against
   the main tree.
5. **No-overlap stays in place.** The MIR golden `mir_spill_only_on_overlap` passes: `fresh` and
   `disjoint` have no spill temporaries. Review of `mb_spill_agg_overlaps`: when no operand
   overlaps, the function returns before any statement is emitted.
6. **Adversarial probes** (snapshot compiler, interp and native identical):
   - Closure capture by `mut_view` (`c = Pair { a: c.b, b: c.a }` inside `|| {..}`): correct, `2 1`.
   - Nested `s = S { a: s.b, b: S2 { x: s.a.x } }`: correct, `4 3`.
   - A rotate in a loop, 4 iterations: correct, `3 1 2`.
   - Moves of non-Copy fields `m = Mv { l: m.r, r: m.l }`: correct.
   - Drop types: swapping two `Guard` fields once and in a loop, and swapping a Copy sub-struct of a
     Drop-carrying struct. Each guard is dropped exactly once, in the right order. There is no early
     drop and no double drop.
   - Operand call side effect: `p = Pair { a: bump(mut_view(cnt)), b: p.a }` runs `bump` once, and `cnt == 1`.
   - **Two pointer fields of one local that address the same object: wrong** (Finding 1).
7. **Pre-existing failures named in the report: confirmed, not this task's.** I used
   `build-head-T428j`, a HEAD-only tree. I checked that its `compiler/`, `std/`, `tools/`,
   `tests/run/opt_lto` and `tests/selfhost/opt` are byte-identical to e085e8e6 (396 files). The
   only difference is `tools/ci.ps1`, which is not used. Its `axiomc2.exe` sha256 is 1c5aec4c...
   - `axtest.py --compiler build/axiomc2.exe --no-cache` on `run/opt_lto/opt_lto_engine.test` and
     `selfhost/opt/qa_opt_pipeline.ax`: both `[interp]` legs FAIL, `TOTAL 4 PASS 2 FAIL 2`
     (`_workspaces/T428j_qa_head.log`).
   - Direct run `build/axiomc2.exe run --interp tests/selfhost/opt/qa_opt_pipeline.ax` on HEAD:
     `exit=125`, `error[AX_UNSAFE_INTERP_UB]: read of uninitialized memory`, at the map-id read
     `*(mids0 + slot)` in `interner_grow_map` (`_workspaces/T428j_qa_head_optpipe.log`).
   - So both failures exist on HEAD without T428j. They came in with T502 and are routed to the
     orchestrator. They are not findings against this task.
8. **Spec.** The behaviour required is REQ-EXP-007 / REQ-EXP-102: operands are evaluated left to
   right before the store takes effect. No new diagnostics. No `BOOTSTRAP-SHORTCUT`. No axiom0 change.
9. **Taskgate.** I did not run it this round. Finding 1 is a reproducible wrong-code defect in the
   code under gate, so the verdict is FAIL whatever the affected-set run shows. Round 1 runs the
   full `taskgate.py --task T428j` after the fix.

### Findings

**Finding 1 (FAIL): the same-root disjoint-field rule ignores derefs after the diverging field.**
`compiler/mir/builder.ax:1171-1174` (`mb_places_may_overlap`): when the destination and the source
have the same root local and differ at a field projection, the function returns `false`
("disjoint"). That is only valid when neither remaining suffix contains a `DEREF`. If either place
dereferences a pointer stored in that field, it addresses memory outside the local, and the two
places can be the same object. The task's scope says it in so many words: "the operand mentions
the destination's base local, or any deref when the destination is reached through a pointer".
Repro (`tests/run/agg_self_assign/qa_alias_ptr_fields.ax`):
```
let h = Handles { p: address_of_mut(s), q: address_of_mut(s) };
*h.p = Pair { a: (*h.q).b, b: (*h.q).a };      // expected 2 1, got 2 2
o.p = address_of_mut(o.v);
o.v = Pair { a: (*o.p).b, b: (*o.p).a };       // expected 4 3, got 4 4
```
The wrong output is the same in interp, native and native-O1. On HEAD the output is the same
(`2 2` / `4 4`), so the task has not fixed this case.

The same rule also misses `(*p).a = Pair { a: (*(*p).q).b, .. }` when `(*p).q` points back to
`(*p).a`: the field divergence comes after an equal deref. Expected fix: on field divergence,
return `false` only when neither `dest.projs[i+1..]` nor `src.projs[i+1..]` contains a `DEREF`.
Otherwise fall through to the cross-root (pointer) rule.

### Follow-ups (not findings of this task)
- **Late place-operand reads.** This is the engineer's "known limitation", and it also applies
  when the destination is involved. In `q = Pair { a: q.b, b: touch(mut_view(q)) }`, where `touch`
  sets `q.b = 99`, the result is `q.a == 99`. Left to right it should be the old `q.b` (7). Interp
  and native agree, and HEAD gives the same 99, so this is not a regression. It needs an architect
  decision or a fix task: a place operand must be materialised before a later operand that can
  write it.
- **T502-era interner UB:** `run/opt_lto/opt_lto_engine.test` and `selfhost/opt/qa_opt_pipeline.ax [interp]`
  fail with the same error on HEAD (item 7 above). These are for the T502 owner.
- **Struct-like enum variant construction:** `AX_VERIFY_TYPE_MISMATCH`, reported by the engineer.
  It needs its own task.

### Files changed
- tests/run/agg_self_assign/qa_alias_ptr_fields.ax
- tests/run/agg_self_assign/qa_closure_nested_loop.ax
- tests/run/agg_self_assign/qa_drop_swap_once.ax

VERDICT: FAIL round=0

## Round 1

Snapshot `build-snap-T428j`, refreshed on HEAD 37f6466c (the T502 triage commit, with the baseline
entries for T543) plus the T428j change set and the 4 QA tests. The last `taskctl.py snapshot T428j`
reported 15 changed files, 0 deleted; bundles regenerated: 36 generators, 60 files, no BUNDLES FAILED.

### Checks performed

1. **Change set.** `taskctl.py changes T428j` stages the 2 reports, `compiler/mir/builder.ax` and the 12
   test files under `tests/run/agg_self_assign/`. No REFUSED line.
2. **Build and fixed point.** `cmake -S bootstrap/axiom0 -B build -G Ninja` (clang, Release),
   then `cmake --build build --clean-first`: 0 warnings.
   `python tools/build_axiomc.py --out build --root . --stage 3 --full-chain`
   (`_workspaces/T428j_qa_build_r1.log`) rebuilt axiom0, then stage 1 (230 s), then stage 2 (O1).
   Result: `FIXED-POINT (O1) OK ... == 53eb65ee91fc4289...`. This matches the engineer's hash.
   - An environment note, not a finding. My first attempt reconfigured the tree with
     `-DCMAKE_C_COMPILER=gcc`. CMake then reset the cache to a Debug build, and the Debug axiom0
     overflowed the stack in stage 1 (rc 0xC00000FD). I rebuilt with the configuration the tree
     uses (clang Release) and the build passed.
3. **F1 is fixed.** In `mb_places_may_overlap`, two places that split at different fields are now
   disjoint only when `mb_place_has_deref_from(dest, i+1)` and `mb_place_has_deref_from(src, i+1)`
   are both false. Otherwise the pointer rule applies.
   - `qa_alias_ptr_fields.ax` now passes in interp, native and native-O1.
4. **New QA test `qa_alias_ptr_suffix.ax`.** It covers three places that split at a field after a
   shared deref, with the pointer on the destination side, the source side, or both. It also covers
   a no-alias control: two pointer fields that point to different objects.
   - On HEAD (`build-head-T428j` compiler) it prints `2 2 / 4 4 / 6 6`, so the 3 alias shapes fail
     there. It passes on the snapshot.
   - The MIR of the no-alias control shows the operands spilled (`((*_40).0) = aggregate([copy _42, copy _43])`).
     This is correct but conservative, as expected under the pointer rule.
5. **Own tests and QA tests** (`axtest.py --no-cache -j 2 run/agg_self_assign`,
   `_workspaces/T428j_qa_own_r1.log`): `TOTAL 31 PASS 31 FAIL 0`, `WEAK-NATIVE 0`. That is 10 run
   files in 3 modes, plus the MIR golden `mir_spill_only_on_overlap` (unchanged, PASS).
6. **Native evidence.** Every run test has an exact `// stdout:`.
   - Live mutation proof: my first draft of `qa_alias_ptr_suffix.ax` had a wrong last line
     (`8 7 8 7`; the correct output is `7 8 8 7`, because `x` is not changed). That draft failed in
     `[interp]`, `[native]` and `[native-O1]` at byte 12. After I corrected the expectation, it
     passes in all three modes.
   - The round-0 mutation proof on `array_rotate.ax` still applies.
7. **Round-0 adversarial results still hold** (`qa_closure_nested_loop.ax`, `qa_drop_swap_once.ax`
   pass in all modes): closure capture, nested aggregates, loops, moves, Drop guards dropped exactly
   once and in order, and an operand call's side effect running once.
8. **Taskgate** (in the snapshot): `python tools/taskgate.py --task T428j --compiler build/axiomc2.exe
   --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428j.json`
   (`_workspaces/T428j_qa_taskgate_r1.log`, wall time 1257 s).

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 11 | 31 | 31 | 0 | 0 | 0 | 0 |
| affected | 213 | 402 | 399 | 1 | 2 | 0 | 0 |
| smoke | 35 | 56 | 56 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 246 | 456 | 453 | 1 | 2 | 0 | 0 |

   - **Affected-set derivation.** The `compiler/mir` map rows select `tests/mir`, `tests/verify`,
     `tests/selfhost/mir` and `tests/selfhost/drop`. Every bundle embedding `compiler.mir.builder`
     adds its `bundles_current.test` (backend, driver, drop, interp, interp_opt, lir, mir,
     obj_link_driver, opt). The 16 regenerated bundle files are selected as changed tests.
     - Unmatched changed files: none. No UNRESOLVED, MAP-NOTE or DEFERRED entries.
   - **Smoke** (seed 560966523): it always includes `run/str/hello.ax` (the Xin chào test),
     `ui/typeck/type_unknown.ax` and `diff/002-arithmetic.ax`, plus one pick per group.
   - **Cache:** 0 hits, 103 misses, mismatch none.
   - **WEAK-NATIVE:** 0 in the task's own or changed tests.
   - **archcheck:** clean (252 files, 0 violations). The smoke-check is OK.
   - **Baseline:** `BASELINE OK`. The only failing id is `selfhost/opt/qa_opt_pipeline.ax`. It is in
     `_workspaces/baseline-failures.txt` under T543, and round 0 item 7 showed it fails identically
     on HEAD. `TASKGATE T428j exit=0`.
   - **The 2 SKIPs** are in the affected part, not in the task's own tests.

### Findings
None. F1 is fixed, and it has regression tests: `qa_alias_ptr_fields.ax`, `qa_alias_ptr_suffix.ax`,
and the engineer's new case in `pointer_dest.ax`.

### Follow-ups
These are already tracked by the architect: T428o (a place operand is read late, after a later
operand writes it), T428n (struct-like enum variants), and T543 (uninitialized reads in the T502-era
opt pass).

### Files changed
- tests/run/agg_self_assign/qa_alias_ptr_fields.ax
- tests/run/agg_self_assign/qa_alias_ptr_suffix.ax
- tests/run/agg_self_assign/qa_closure_nested_loop.ax
- tests/run/agg_self_assign/qa_drop_swap_once.ax

VERDICT: PASS round=1
