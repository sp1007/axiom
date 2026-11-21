# T482 report — Investigate: O1 miscompile of the original u128_neg_raw carry form (FU-T452-NEG)

## Summary
The miscompile reported in T452 does **not reproduce**, neither on HEAD (9548f5e, after T453) nor on the T452
commit itself (e0637c50), through any build path (seeded, axiom0 -> c1, c1 -> c2 at -O1). No defect was found in
`compiler/opt`, `compiler/mir/builder.ax`, `compiler/lir/builder.ax` or `compiler/target/x64`, so no compiler code
was changed. Per the task's Scope ("if no defect is found after the bisection, the report states the evidence and
the architect decides"), this report gives the evidence and adds a permanent regression test of the original form
at interp / native -O0 / native -O1. The T452 workaround in `compiler/interp` and `compiler/opt/const_fold.ax`
stays in place (no edit needed, as the task says).

## Method
The original form was put back into a scratch copy of the generated `axiomc` bundle (script in the scratchpad,
exact text replacement, asserted to match once), for both functions:
```
let nlo = w_add_u64(lo ^ 0xFFFFFFFFFFFFFFFFu64, 1u64);            // opt_wrapping_add_u64 in const_fold
let carry: u64 = if lo == 0u64 { 1u64 } else { 0u64 };
let nhi = w_add_u64(hi ^ 0xFFFFFFFFFFFFFFFFu64, carry);
```
Each resulting compiler was checked with `run --interp tests/run/int128_interp/neg_carry.ax` (T452 symptom: exit 1)
and `inspect --emit=mir-opt -O1 tests/opt/int128/const_fold_neg_carry.ax` (T452 symptom: `-TWO64` folded to
...426481119284349108224 = 2^128 - 2^65; correct is ...444927863358058659840).

| Source tree | Compiler built from the original form | neg_carry --interp | -O1 fold of -TWO64 |
|---|---|---|---|
| HEAD 9548f5e | seeded A = HEAD axiomc2 (O1) | ok, rc 0 | ...659840 (correct) |
| HEAD 9548f5e | axiom0 -> c1 (stage 1) | ok, rc 0 | correct |
| HEAD 9548f5e | c1 -> c2 at -O1 (the T452 recipe) | ok, rc 0 | correct |
| T452 e0637c50 (axiom0 of that commit) | interp form only: c1 / c1 -> c2 -O1 | c1 segfault (rc 139), c2 ok | n/a |
| T452 e0637c50 | both forms: A = old c2 (O1) | ok, rc 0 | correct |
| T452 e0637c50 | both forms: axiom0 -> c1 | segfault (rc 139) | correct |
| T452 e0637c50 | both forms: c1 -> c2 at -O1 (43 min build) | ok, rc 0 | correct |

All three fold results (`-TWO64`, `-TWO64_P1`, `-FIVE`) were correct for every compiler listed.

- The T452-era stage-1 segfault on `run --interp` is T165/T166 (axiom0 `fixups[1024]` overflow miscompiled
  `exec_assign_binop` in axiomc1; fixed by T166 in dbc78f58). It affects only axiomc1's interpreter, not the code
  axiomc1 emits, and HEAD's axiomc1 no longer crashes. It does not explain the T452 symptom (that was seen on
  axiomc2, and the T452-era axiomc2 built here from the original form is correct).
- With the HEAD stage-2 compiler built from the original form (both functions), the whole int128 suite passes,
  including the native legs that T453 enabled: `axtest --no-cache -j 2 --filter int128 --filter o1_neg_carry_repro`
  -> TOTAL 158 PASS 158 FAIL 0 SKIP 0, WEAK-NATIVE 0 (neg_carry, qa_neg_lowword, qa_matrix_{u128,i128}{,_fold},
  const_fold_neg_carry, ...).
- The -O1 MIR pipeline is const_fold -> DCE -> cfg_simplify (no inlining or cross-call propagation), so the
  "constant propagation across the call to w_add_u64" candidate does not exist; `opt_cfg_eliminate_redundant_switches`
  only turns a switch whose targets all equal `otherwise` into a goto (correct for the `if lo == 0` diamond).

## Conclusion / decision
No compiler defect exists for this form at HEAD or at the T452 commit. The binary that showed the symptom
(sha256 2fe382a0...) no longer exists anywhere in the tree or the compiler cache (all `axiomc*.exe` under build*/
and `_workspaces/artifacts` were hashed). The most likely explanation is that the T452 build tested a source state
that differed from the three lines in the recipe (the form was never committed, see `git log -S`), or a stale stage
binary (stage reuse was by mtime until T444c, and snapshots keep main-tree mtimes). Decision: close FU-T452-NEG as
"not reproducible", keep the workaround (it is equivalent and verified), and keep the new regression test so any
future O1/native miscompile of this shape is caught. Restoring the original form in `compiler/interp` remains out of
scope (cosmetic); the architect may file it if wanted.

## Tests
- New: `tests/run/o1_neg_carry_repro/neg_carry_forms.ax` — the original form (`neg_orig`), the workaround form
  (`neg_sub`) and a statement-`if`/early-return variant, with the interpreter's 32-bit-split `w_add_u64` and a
  `mut_view` struct out-field; exact `// stdout:` of five printed negations plus 40 cross-form checks.
  Runs in interp, native, native-O1: TOTAL 3 PASS 3, WEAK-NATIVE 0.
  Mutation proof (snapshot only, restored): `bad=0` -> `bad=1` in the expected stdout -> all three legs FAIL
  ("stdout differs at byte 200").
- Gate in the snapshot: `python tools/taskgate.py --task T482 --changed @<file listing the test> --compiler
  build/axiomc2.exe --build-dir build --root . -j 2 --exclude-requires axiom0-internal` -> affected 3/3 PASS,
  smoke 48/48 PASS, axtest TOTAL 51 PASS 51 FAIL 0, failing ids: none, archcheck clean, `TASKGATE T482 exit=0`
  (log `_workspaces/T482_taskgate.log`).
- Snapshot build: `tools/build_axiomc.py --out build` in build-snap-T482: seeded B == C fixed point OK,
  STAGE0-GUARD OK (sha256 243b60bb...).

## Spec deviations
None.

## Files changed
- tests/run/o1_neg_carry_repro/neg_carry_forms.ax
- _workspaces/reports/T482-report.md

STATUS: COMPLETE round=0
