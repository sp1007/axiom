# T423a QA report

## Round 0

### 1. Code review
Reviewed the full diff in `build-snap-T423a/` against `SPEC-12` (`AXS-DROP-005`), `SPEC-54`, and `ADR-0046`:
- `compiler/mir/builder.ax` (`mb_try_build_drop_in_place`, hooked from `mb_build_control_or_call_expr` on `TY_BUILTIN_DROP_IN_PLACE`):
  - Resolves pointee type `T` from callee generic substs (with fallback to `arg0`'s `*mut T` pointee), skips when `type_contains_param(T)` or `!mir_type_needs_drop_in(T, ...)`, and lowers `drop_in_place<T>(p)` to `_ptr = p; drop(*_ptr) -> next_bb` (`MIR_TERM_DROP` with `drop_flag = MIR_DROP_FLAG_NONE` / zeroed terminator flag).
  - `mb_scan_or_rewrite_calls` already enqueues transitive `Drop` instantiations for every `MIR_TERM_DROP`, and `mir_drop_elaborate` (`drop_expand_block`) expands `drop(*_ptr)` identically for interp and native: own `Drop` impl first, then struct fields / closure `CAP_MOVE` captures / tuple elements / array elements `0..N` / active enum variant payloads, unconditionally.
  - Side-effecting pointer expressions are evaluated once via `mb_build_expr_as_operand` for both `needs_drop<T>() == true` and `false` (when `false`, falls through to the normal call lowering which evaluates `arg0` then executes the no-op builtin).
- `compiler/traits/mono.ax`:
  - `type_contains_param` extended to traverse `TY_CLOSURE` captures, parameter types, and return type.
  - `mono_cid_mix` replaces checked `cid_mix * 31u32` multiplication in `subst_ty_enum_or_closure` with wrapping 32-bit mixing, preventing overflow panics on multi-capture closure substitution.
- `compiler/interp/interp.ax`:
  - `resolve_or_build_mir_body` guards `(*inst).mir_body` with `(mb_ptr as usize) > 1` so `mb_prepare_mono`'s `1` worklist sentinel is not dereferenced as a `MirBody*`.
- No edits under `bootstrap/axiom0/`, `spec/`, `docs/`, or shared harness files.

### 2. Stage-2/Stage-3 fixed-point build (in `build-snap-T423a/`)
- `python tools/build_axiomc.py --out build --root . --stage 3`:
  - `STAGE1 OK`: `29,724,672` bytes (`sha256=8f5f7cdb4578ee87`)
  - `STAGE2 (O1) OK`: `8,956,928` bytes (`sha256=556bd69e9f4b36f3`)
  - `STAGE3 (O1) OK`: `8,956,928` bytes (`sha256=556bd69e9f4b36f3`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 556bd69e9f4b36f38d566bc37234d3be7f317c5730f154e9e8bdf421086da3ae`

### 3. Boundary cross-check & adversarial test (step 5)
Added `tests/run/drop_in_place_glue/qa_adversarial_edges.ax` (`modes: interp native`, exact `stdout:`, `exit: 83`), refreshed snapshot (`taskctl.py snapshot T423a`), and verified:
- Scope-end `DROP` vs `drop_in_place` on `OwnAndFields` (own `Drop` impl + 2 `Guard` fields): identical order, no double-drop.
- Generic enum `RichChoice<F>` with payloadless `Empty`, `One(Guard)`, `Pair((Guard, Guard))`, and `Clos(F)` variants.
- Nested closure (outer closure capturing inner closure + `Guard` + tuple `(Guard, Guard)` + `[2]Guard` + `Guard`).
- Generic struct `ClosHolder<F>` holding a closure + `Guard`.
- Element-pointer `drop_in_place` on raw `[3]Guard` slot elements (`(*arr_p)[1]`, `[2]`, `[0]`).
- Nested generic wrapper `kill2<A, B>` instantiated with `(Guard, i64)` and `(i64, Guard)` in the same program.
- Side-effecting pointer expressions (`get_guard_ptr`, `get_i64_ptr`) evaluated exactly once for both `needs_drop<T>() == true` and `!needs_drop<T>()`.
- Command (`build-snap-T423a/`): `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 run/drop_in_place_glue`
  - Result: `WEAK-NATIVE 0`, `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0` (all 7 tests across `interp`, `native`, `native-O1`).

### 4. Native-evidence liveness spot-proof (step 4a)
- Every new test in `tests/run/drop_in_place_glue/` specifies `modes: interp native`, exact `// stdout:`, and non-zero `// exit:`; `WEAK-NATIVE 0`.
- Mutated expected `P:70\n` -> `P:99\n` in `build-snap-T423a/tests/run/drop_in_place_glue/qa_adversarial_edges.ax` (snapshot only):
  - `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 run/drop_in_place_glue/qa_adversarial_edges.ax`
  - Result: `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1` all failed at byte 126: expected `P:99\n`, got `P:70\n`).
- Restored snapshot file and re-verified PASS in all 3 modes.

### 5. Targeted suites & per-task gate (`build-snap-T423a/`)
- Targeted suites (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 run/drop_in_place_glue/qa_adversarial_edges.ax std/fiber std/thread run/drop std/collections selfhost/mir selfhost/interp selfhost/lir`):
  - `WEAK-NATIVE 0`, `TOTAL 328 PASS 322 FAIL 0 SKIP 0 XFAIL 6` (exit 0).
- Per-task gate (`python tools/taskgate.py --task T423a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423a.json`):
  - root `D:/projects/compiler/new lang/build-snap-T423a`, HEAD `4f2daaf08dc1`, compiler `build/axiomc2.exe`, `-j 2`
  - wall time: 1169.3 s (axtest 1152.1 s)
  - | part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
    |---|---|---|---|---|---|---|---|
    | own | 7 | 21 | 21 | 0 | 0 | 0 | 15 |
    | affected | 246 | 485 | 483 | 0 | 2 | 0 | 291 |
    | smoke | 33 | 54 | 54 | 0 | 0 | 0 | 19 |
    | **total (dedup)** | 276 | 536 | 534 | 0 | 2 | 0 | 308 |
  - Affected-set derivation: `compiler/mir/builder.ax` -> `tests/mir`, `tests/verify`, `tests/selfhost/mir`, etc.; `compiler/traits/mono.ax` -> `tests/typeck`, `tests/selfhost/traits`, etc.; `compiler/interp/interp.ax` -> `tests/run`, `tests/selfhost/interp`, etc.; unmatched changed files: none.
  - Smoke: `seed=510139326`, `smoke-check (tests/smoke.list): OK; est. worst-case draw 24 s`.
  - Cache: `CACHED 308, miss 12, uncacheable 114, stored 10, dep_source exact, verification sample seed=1969605396 n=20 of 150 hits, mismatch none`.
  - `WEAK-NATIVE: 25 in the run; 0 in the task's own/changed tests`.
  - `Baseline: BASELINE OK`, `Failing ids: none`.
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
  - `axtest: TOTAL 536 PASS 534 FAIL 0 SKIP 2 XFAIL 0 (exit 0)`
  - `TASKGATE T423a exit=0`

### 6. Board & harness checks
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423a`: 0 `REFUSED` lines.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
none

## Files changed
- tests/run/drop_in_place_glue/qa_adversarial_edges.ax

VERDICT: PASS round=0

### Rebase gate (HEAD 6943c89)
Re-verified inside refreshed `build-snap-T423a/` on HEAD `6943c89e` (with all 19 rebased selfhost bundles regenerated in the snapshot):
- Stage-2 rebuild (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `STAGE1 OK`: `29,721,088` bytes (`sha256=7679685b1ed3f864`)
  - `STAGE2 (O1) OK` / `STAGE3 (O1) OK`: `8,955,904` bytes (`sha256=75d66042fdcb6e50`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 75d66042fdcb6e50cb1191b6d131923442e4e91db6a0e0534b3bf4d639195e2e`
  - `STAGE0-GUARD OK`: axiomc1 and B produced byte-identical `.exe` on 6 smoke programs (O1, incl. Xin chào thế giới).
- Per-task gate (`python tools/taskgate.py --task T423a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423a.json`):
  - wall time: 1072.0 s (axtest 1032.7 s); change set: 31 files (incl. 19 rebased selfhost bundles); unmatched changed files: none.
  - `own`: 7 ids, 21 results (`21 PASS, 0 FAIL`); `affected`: 246 ids, 485 results (`483 PASS, 0 FAIL, 2 SKIP`); `smoke`: 33 ids, 52 results (`52 PASS, 0 FAIL`, `seed=1993347060`, `smoke-check OK`).
  - `total (dedup)`: 275 ids, `TOTAL 531 PASS 529 FAIL 0 SKIP 2 XFAIL 0 (exit 0)`.
  - `WEAK-NATIVE: 25 in the run; 0 in the task's own/changed tests`.
  - `Baseline: BASELINE OK`, `Failing ids: none`.
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
  - `TASKGATE T423a exit=0`.
- Board & harness checks: `taskctl.py changes T423a` 0 `REFUSED` lines; `harness_check.py` `HARNESS OK`.

VERDICT: PASS round=0 (rebase)
