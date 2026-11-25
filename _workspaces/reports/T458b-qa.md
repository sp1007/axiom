# T458b QA report

## Round 0

### Checks performed
1. **Report / change set.** Report ends `STATUS: COMPLETE round=0`. `taskctl.py changes T458b` stages the 4 compiler files,
   9 task tests and the report, with no REFUSED line (the only one was for my own two added tests until they were listed
   under `## Files changed` below). Edits are within `paths:`/`locks:` (`compiler/types`, `compiler/interp_opt`;
   locks `compiler/mir`, `compiler/driver/pipeline.ax`). `compiler/resolve` and `compiler/hir` were not touched, which is
   consistent with report item 5. No `docs/`, `tools/axtest.py`, CMake or `diag/codes.def` edits.
2. **Snapshot integrity.** The 4 compiler files and 9 tests in `build-snap-T458b` are byte-identical to the main tree
   (`cmp`). Selfhost bundles are regenerated there (19 `tests/selfhost/*/qa_*.ax` working-tree changes, not listed in any
   report).
3. **Build / fixed point (independent re-run).** `python tools/build_axiomc.py --out build --root .` inside the snapshot:
   STAGE1 OK, STAGE2 (O1) OK. Inputs hash covered 263 source files and the stage binaries were reused because their
   input hashes matched the current sources. `sha256(axiomc2.exe) == sha256(axiomc3.exe) == dd6c7b0bc8b8d4bd...`,
   the same as the engineer's. No warnings.
4. **Code review of the 4 compiler files.** The diff is coherent with the report. Key points checked:
   - `eval_const_expr_u128` returns false for any float-typed subexpression, so an integer folder can no longer store
     `3 as f64` as the integer 3.
   - The session worklist keeps the old source order when nothing is pending, and defers readers of constants that have
     no value yet via the `MIR_CONST_INT{sym}` marker. When a round makes no progress it evaluates without deferral, so
     every item reports its own diagnostic (verified with my cycle test below).
   - The MIR builder emits `MIR_CONST_FLOAT` carrying the exact bits for both const paths and `Type.NAME` associated
     constants.
   - The native TLS emitter now writes `CONST_FLOAT` bits.
   - `f32`/`f64` path heads and `tc_impl_assoc_const_ty` for primitive bases come after the built-in integer
     `MIN`/`MAX`/`BITS`.
5. **Taskgate** (inside the snapshot, `--no-cache`, `-j 2`, `--extra run/float_const/qa_edge,ui/float_const/qa_cycle`):
   `python tools/taskgate.py --task T458b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --no-cache --extra ... --json-out _workspaces/artifacts/taskgate-T458b.json`
   - `TASKGATE T458b exit=0`, `TOTAL 618 PASS 616 FAIL 0 SKIP 2 XFAIL 0`, wall 1715 s. Log: `_workspaces/T458b_qa_taskgate.log`.
   - own: 12 ids / 23 results all PASS. affected: 328 ids / 571 results, 569 PASS, 2 SKIP. smoke: 33 ids / 54 results all PASS.
   - Failing ids: none. BASELINE OK. archcheck clean (235 files, 0 violations). smoke-check OK.
   - WEAK-NATIVE: 3 in the whole run, 0 in the task's own/changed tests (`task_scope: []`).
   - Cache: `--no-cache`; no `CACHE-MISMATCH`. No `UNMATCHED`, `UNRESOLVED`, `MAP-NOTE` or `DEFERRED` entries.
   - Affected-set derivation: compiler map rules `compiler/driver -> tests/driver, tests/inspect`,
     `compiler/mir -> tests/mir, tests/verify`, and `compiler/types` / `compiler/interp_opt` rows
     (typeck, selfhost, run, ui, modules, ...). Counts per group are in the taskgate log; groups hit:
     driver 34, mir 91, modules 25, typeck 27, verify 29, selfhost 42 (the regenerated per-module bundles),
     run 64, ui 19, inspect 1, plus one smoke pick for each of the other top-level groups.
     The report's remark that there is no repository-level `tests/selfhost/bundles_current.test` matches:
     the per-module bundle groups above are the ones that ran, and all passed.
6. **Native-evidence check (step 4a).** Every `tests/run/float_const/*.ax` has an exact `stdout:` directive. The expected
   values are Python `struct.pack` bit patterns and do not come from the compiler. Each test runs
   `[interp]`, `[native]` and `[native-O1]`. No test relies only on `assert()`.
   - **Mutation proof:** in the snapshot only, I changed the first expected stdout number of
     `tests/run/float_const/statics.ax` from `-9223372036854775808` to `0`. Command:
     `sed -i '2s/^\/\/ stdout: -9223372036854775808/\/\/ stdout: 0/' ...` then
     `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 float_const/statics`.
     Result: `TOTAL 3 PASS 0 FAIL 3`, including `[native]` and `[native-O1]` ("stdout differs at byte 0"). I then
     restored the file from the main tree (`cmp` identical). The native legs are live.
   - The engineer's claim that the TLS native leg caught a real zero-read bug is consistent with the code
     change in `pipe_emit_one_tls_item`.
   - Interp/native agree by hand: my ad hoc f32 TLS probe printed identical bits on `run --interp` and native.
7. **Acceptance coverage against the task file.**
   - run tests: scalar bits (±0, inf, NaN-ness, subnormal, f32 direct rounding), expression initializers with
     REQ-OWNER-007 promotion, arrays/structs/tuples indexed at run time, statics of every storage class, constants as
     operands and arguments, `f32.`/`f64.` static calls, trait static dispatch on `f64`, associated constants on
     `f64`, `f32`, `u8`, `i32`: covered.
   - ui tests: `X: f32 = 1` mismatches, float array length, unknown `f64.NOPE`, non-constant call in an initializer:
     covered. All four existing-code claims verified by running them.
   - `grep -rn AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP tests`: the matches are the frozen axiom0 test
     (`requires: axiom0-internal`), a comment in `tables_and_aggregates.ax` and a comment in `qa_const_tuple.ax`. No
     test expects it for a float const.
   - `archcheck` clean; fixed point holds; report has exact `## Files changed`.
8. **Decisions D1-D5.**
   - D1 (payload enum consts stay `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`): sound, it is a general pre-existing restriction
     pinned by `tests/ui/comptime/invalid_type_err.ax`. It is however a narrowing of the task's "inside ... enums";
     there is no test for a float in a fieldless enum constant either. Not a FAIL: see Follow-up 1.
   - D2 (TLS float initializer must be a literal or negated literal): sound given typeck-only TLS folding; documented, and
     the rejection is the existing `AX_TYPE_INVALID_TLS_DECL`. See Follow-up 2.
   - D3 (deferral via the MIR operand marker): sound and cheap; only active when typeck left constants unfolded;
     the cycle behaviour is verified below.
   - D4 (no const-generic/int-pattern tests): confirmed, const generics are not parsed yet and an identifier in pattern
     position is a binding. Sound.
   - D5 (`f32.MAX` is std, `AX_TYPE_UNKNOWN_FIELD`): matches the task's out-of-scope note. Sound.
9. **Spec/scope.** No new diagnostic codes. No `BOOTSTRAP-SHORTCUT`. No `bootstrap/axiom0` change. Mode check: no
   mode-restricted run test and no `native-after`. Shared-file check: `compiler/driver/pipeline.ax` is a declared
   lock of this task, so the edit is allowed.

### Adversarial tests added (step 5)
- `tests/run/float_const/qa_edge.ax` (interp, native, native-O1 PASS; exact stdout from Python `struct.pack`): `-ZERO`
  gives -0.0 bits for a const and a static; `16777216.0f32 + 1.0` stays `0x4B800000` (strict f32 rounding of a
  constant expression); `NAN != NAN`; compile-time saturating casts (`1e20 as i32 = 2147483647`, `NAN as i32 = 0`,
  `-42.0 as u32 = 0`, `999.9 as u8 = 255`); same-named associated constants on `f32` vs `f64` and on `u8` vs `u16`
  resolving to the right impl; `u8.W as i64 - 1`.
- `tests/ui/float_const/qa_cycle.ax` (PASS): `const A = B + 1.0; const B = A + 1.0;` reports `AX_CONST_CYCLE`, so the
  worklist deferral does not silently evaluate a stale operand.
- Ad hoc probes (not committed): f32 `@thread_local` scalar and array with `-0.1`, `1.5`, `-0.0` and a run-time write give identical
  bits in interp and native and match Python. `const N: usize = 2.0 as usize; let a: [N]i32` reports
  `AX_TYPE_ARRAY_SIZE` (see Follow-up 3). A function-local `const` is `AX_PARSE_ITEM_IN_BLOCK` (language limitation, not
  related to this task).

### Findings
None blocking.

### Follow-ups (for the architect)
1. Enum constants: only fieldless enums are effectively covered by "floats inside enums" (D1); no test pins a float in
   a fieldless enum const. A later general task should lift the payload restriction and add that coverage.
2. `@thread_local` float initializers cannot be expressions (D2), e.g. `0.5 * 2.0`. Needs a TLS-through-session
   evaluation to lift it; the diagnostic is `AX_TYPE_INVALID_TLS_DECL`.
3. An integer constant derived from a float constant (`2.0 as usize`) is accepted as a value but cannot be used as an
   array length (`AX_TYPE_ARRAY_SIZE`), because array lengths are folded in typeck by the integer folder, which now
   refuses float-typed subexpressions. Consistent with the task text ("a float constant is not an array length") but
   worth a spec sentence in SPEC-41 for the derived case.
4. 3 WEAK-NATIVE tests exist in the affected/smoke set outside this task's tests (pre-existing, not part of this
   change).

## Files changed
- tests/run/float_const/qa_edge.ax
- tests/ui/float_const/qa_cycle.ax

VERDICT: PASS round=0
