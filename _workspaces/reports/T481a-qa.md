# T481a QA

## Round 0

### Checks performed

1. **Change set** (`taskctl.py changes T481a`): 8 task files + report staged, no `REFUSED` line. Paths match the task
   (`tests/run/saturating_native`, `tests/ui/backend_ice`) and the locks (`compiler/lir/builder.ax`,
   `compiler/backend/session.ax`, `compiler/driver/pipeline.ax`). No generated bundle listed. The task did not touch
   `tools/axtest.py`, CMake, `diag/codes.def`.
2. **Build** (snapshot `build-snap-T481a`, `python tools/build_axiomc.py --out build --root . --force`): stage 1 and
   stage 2 O1 OK, `axiomc2.exe` sha256 `f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce` (equals the
   implementer's hash, so the build is reproducible), no warnings, no `AX_TYPE_NOT_CALLABLE`.
3. **Semantic claims**
   - Shift pair: `SHL x, 64-bw` then `SAR`/`SHR` by `64-bw`, for bw in {8,16,32} the count is 56/48/32 (< 64, no
     x64 count-mask effect). SHL discards the dirty upper bits; SAR replicates the sign bit (signed), SHR zero-fills
     (unsigned): canonical sign/zero-extension. Both vregs are typed i64/u64 so isel adds no further truncation. bw >= 64 is
     returned unchanged (correct, nothing to clean). Const operands use the pre-existing `lb_norm_int_const` path.
     Not an identity op, so `x | 0 -> x` style simplification cannot remove it. Invariant comment present.
   - LIR before/after demonstrated by me with the rebuilt compiler
     (`axiomc2 inspect --emit=lir` of `fn f(a: i8, b: i8) -> i8 { a.saturating_add(b) }`): `const 56; shl; shr(=SAR)`
     for both operands; no `or ..., 0`; the sign-extraction `shr v10, 63` is correct SAR use afterwards.
     (The LIR printer prints SAR as `shr`: existing behaviour, noted by the implementer.)
   - ICE exit code 3: `spec/diagnostics.md` AXD-042/043 and SPEC-101/102/103/104, SPEC-25, SPEC-43 all say
     `AX_ICE_INTERNAL` -> exit code 3; `AX_EXIT_ICE: i32 = 3` in `compiler/driver/opts.ax`. Consistent. When a
     diagnostic already exists the driver keeps exit 1 and adds no ICE (sensible, no double report).
   - `backend_report_ice`: message built from the string literal, text unchanged (`internal compiler error`), NUL-terminated
     arena copy; one top-level symbol fewer (byte array removed).
   - New UI tests: input is a verifier-valid `.mir` with `SatAdd` on a 128-bit type; I ran
     `axiomc2 inspect --emit=mc tests/ui/backend_ice/sat_u128_unsupported.mir` -> `error[AX_ICE_INTERNAL]: internal
     compiler error`, `1 error, 0 warnings`, rc=3. The three tests (lir/mi/mc) check `exit: 3` and both stderr texts.
   - New run test `narrow_dirty_operands.ax`: expectations are computed by independent 64-bit arithmetic on clean
     values (not by the saturating op under test); dirty bits come from patterns OR-ed above the type width before the
     narrowing cast; covers locals, parameters and struct fields, all of add/sub/mul, u8/u16/u32/i8/i16/i32. Checks
     observable output (`stdout: NARROW-SAT-OK`, exit 0) so the native leg is not exit-0-only evidence.
4. **Own tests** (snapshot, `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 -v saturating_native backend_ice`):
   `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (13 saturating files x interp/native/native-O1 incl. my new
   one, `qa_t481_saturating_bounds.test`, 3 UI tests).
5. **Native-evidence spot-proof (4a)**: copied my test in the snapshot, mutated one expectation
   (`sed 's/255i64);  \/\/ 294 -> 255/254i64);  \/\/ MUT/'`) -> `FAIL [interp]`, `FAIL [native]`, `FAIL [native-O1]`
   all `exit code 1, expected 0`; mutated copy deleted. The native legs are live.
6. **Adversarial test I added** (`tests/run/saturating_native/qa_t481a_wrapped_chain.ax`, modes interp native + auto
   native-O1): narrow operands that are dirty because they come from narrow **wrapping arithmetic**
   (`200u8.wrapping_add(100)` = 44 in a register holding 300; i8/i16/u32/i32 likewise), from **array element loads**,
   and from **chained saturating results** (`sat_sub(...).sat_add(...)`), for all widths; expected values are
   hand-derived literals documented in comments (not computed by the same code). Passes in all 3 legs (counted in the 40
   above); mutation proof above.
7. **taskgate** (inside the snapshot: `python tools/taskgate.py --task T481a --compiler build/axiomc2.exe --build-dir build
   --exclude-requires axiom0-internal -j 2 --extra run/saturating_native/qa_t481a_wrapped_chain.ax --json-out
   _workspaces/artifacts/taskgate-T481a.json`), wall 22725 s:
   - change set 31 files; parts: own 16 ids/40 results all PASS; affected 361 ids/671 results (651 PASS, 8 FAIL, 12 SKIP);
     smoke 31 ids/48 results all PASS (always-include cases: `run/str/hello.ax`, `ui/typeck/type_unknown.ax`,
     `diff/002-arithmetic.ax`, `driver/help.test`, `inspect/async_layout.test`, ...).
   - total dedup `TOTAL 737 PASS 717 FAIL 8 SKIP 12 XFAIL 0`; `archcheck: clean, 229 files scanned, 0 violations`;
     `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`; cache: CACHED 0 (run `--no-cache`), no CACHE-MISMATCH;
     UNMATCHED: none.
   - **Affected-set derivation**: the explicit grep/map rows (`compiler/lir`->`tests/lir`, `compiler/driver`->`tests/driver`,
     `compiler/backend`->`tests/mc`/..., `selfhost/lir|backend|driver|obj_link_driver` groups) plus ids selected because
     the snapshot change set contained `tests/selfhost/generated-files.txt` (an *untracked new file* of the bundle
     mechanism, not of this task): "in the test's directory" selected essentially every `tests/selfhost/**` id (201
     selfhost ids), which is why the gate took 6.3 h instead of 60-90 min. See Follow-ups.
   - 6 ids failed outside `baseline-failures.txt`; triaged below.
8. **Triage of the 6 new-failing ids** (each re-run alone, `--no-cache`, snapshot compiler, some with `--timeout-scale 6`;
   the T481a compiler also built itself at O1):

   | id | alone / scale 6 | conclusion |
   |---|---|---|
   | `selfhost/diag/qa_diag_format_json.ax` | PASS interp/native/native-O1 | load-related in the gate run, passes alone |
   | `selfhost/kernel_source_diag/qa_session_integration.ax` | PASS x3 | load-related, passes alone |
   | `selfhost/kernel_source_diag/qa_corpus_differential.ax` | first alone run: native-O1 `TIMEOUT 10s`; with `--timeout-scale 6`: PASS x3 | load timeout (re-run alone at scale 6 passed) |
   | `selfhost/fixedpoint/fixedpoint.test` | FAIL with `--timeout-scale 6` too: `fixedpoint_oracle.py` runs `bootstrap.py --check-both-opt` with a hard-coded `timeout=1500` (not scaled); a stage-2 build alone took 2515 s here | environmental, same as reported in T485-report ("O0 legs did not finish in time on the loaded machine"). **The substance holds**: `dir_stage2_O1/axiomc2.exe` (built from this change set) and `dir_stage3_O1/axiomc3.exe` (built by it) have identical sha256 `f10f6d3de570f69c...` = O1 fixed point |
   | `selfhost/hir/qa_hir_desugar_and_drop.ax` | FAIL x3 (exit 43) incl. interp, with the snapshot compiler **and** with the HEAD-era compiler `build/axiomc2.exe` (sha256 `9c4385ba...`, the HEAD compiler named in T485-report): identical `exit code 43` on all 3 legs | pre-existing, not caused by this task (fails in interp, HIR-only test, identical at HEAD) |
   | `selfhost/obj_link_driver/axiomc_e2e.test` | FAIL (exit 1) with snapshot compiler and with the HEAD-era compiler, identical | pre-existing, not caused by this task |

   The last two are **new pre-existing failures not yet in `_workspaces/baseline-failures.txt`** (report for the architect;
   evidence: `_workspaces/qa_T481a_ids4_head.log`, `_workspaces/qa_T481a_ids3.log`). Caveat: the HEAD comparison uses the
   HEAD-era compiler binary against the snapshot's test sources/bundles, not a full HEAD checkout.
9. **Scope/mode/shared-file checks**: no `bootstrap/axiom0` change (R7 n/a); the run tests use the default modes
   (interp + native, runner adds native-O1), no one-mode restriction; no edit of `tools/axtest.py`, CMakeLists,
   `diag/codes.def`; `pipeline.ax`/`session.ax`/`builder.ax` are in the task's `locks:`. No `BOOTSTRAP-SHORTCUT`.
   Diagnostic `AX_ICE_INTERNAL` already registered (no new code). `gen_*.py --check` reported clean by the implementer and
   the snapshot regenerated 36 generators / 154 files without "BUNDLES FAILED".
10. **Cleanup**: I stopped by PID the one orphan `axiomc1.exe` (PID 9712, started by my fixedpoint run); no other process
    of mine remains.

### Findings

None against the task. (Notes, not FAILs: the implementer's report says a broad `taskkill` by image name was issued during its
run and may have killed other agents' python processes - the coordinator should check T444/T485 background runs; the
`tests/ui/backend_ice` ICE path is covered by driver-level tests only, the direct `session_emit_*_mir_text_opt` functions
still return only `false`, which the task's design accepts.)

### Files changed
- tests/run/saturating_native/qa_t481a_wrapped_chain.ax

### Follow-ups (for the architect/orchestrator)
- `tools/taskgate.py`: an untracked `tests/selfhost/generated-files.txt` in the snapshot change set selects every selfhost
  test ("test: ... is in the test's directory"), inflating this gate to 6.3 h. That file should be excluded from the
  change set or mapped to nothing (it is bundle-mechanism metadata).
- Add `selfhost/hir/qa_hir_desugar_and_drop.ax` (exit 43 at HEAD too) and `selfhost/obj_link_driver/axiomc_e2e.test`
  to the baseline with fix tasks.
- `selfhost/fixedpoint/fixedpoint.test`: hard-coded 1500 s inner timeout fails on this machine whenever a stage-2 build takes
  longer (T485 saw the same); it is not scaled by `--timeout-scale`.

VERDICT: PASS round=0
