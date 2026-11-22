# T422e QA Gate Report

## Round 0

### Summary
Verified T422e (`Fix — an AsyncMutexGuard held across .await is rejected (AX_ASYNC_GUARD_ACROSS_AWAIT, keyed on the type name, wrong "drop flag" message); SPEC-34 AXS-EXEC-031 allows it`) inside isolated snapshot `build-snap-T422e/` (`HEAD 4f2daaf` + 39 changed files incl. 3 QA adversarial tests + 60 regenerated selfhost bundles). All acceptance criteria, code reviews, boundary cross-checks, native-evidence spot-proofs, and `taskgate` checks PASS with 0 findings.

### 1. Code Review
- `compiler/verify/verifier.ax`:
  - Verified `VERIFY_TEXT_DATA` / `VERIFY_TEXT_OFF` indices `148..151` decode to:
    - `148`: `'use of uninitialized future at .await'` (`AX_VERIFY_UNINIT_USE`)
    - `149`: `'use of moved future at .await'` (`AX_VERIFY_USE_AFTER_MOVE`)
    - `150`: `'value containing a view is held across an .await suspension point'` (`AX_ASYNC_VIEW_ACROSS_AWAIT`)
    - `151`: `'synchronous lock guard or @no_suspend_hold value is held across an .await suspension point'` (`AX_ASYNC_GUARD_ACROSS_AWAIT`)
  - No "drop flag" mis-indexing remains in `verify_own_step_bb`.
  - Verified `verify_type_is_guard` recurses structurally across `TY_ARRAY`, `TY_SLICE`, `TY_STRUCT` / `TY_COROUTINE`, `TY_TUPLE`, and `TY_ENUM` (with `TY_PARAM` substitution from `AxType.args` and `@no_suspend_hold` enum support).
- `compiler/types/typeck.ax`:
  - Verified `tc_sv_is_guard_name` (`*Guard`/`*GuardImpl` suffix heuristic) is completely removed.
  - `tc_is_guard_struct` / `tc_mark_guard_structs` mark `HIR_ITEM_STRUCT` and `HIR_ITEM_ENUM` **iff** `@no_suspend_hold` is present.
- `compiler/own/unsafe.ax`:
  - Verified `conc_sv_is_guard_name` and `.lock()`/`.read()`/`.write()` method-name heuristics are completely removed.
  - `conc_type_is_guard` / `conc_type_is_guard_rec` are purely `@no_suspend_hold` attribute/type-based with structural recursion across arrays, slices, tuples, generic structs, and generic enums.
  - `conc_extract_region` and `conc_expr_is_from_guard` propagate `from_guard` only for guard types or types containing `view`/`mut_view`, allowing plain scalar copies (`g.val() -> i64`) while catching escaping derived views and guards.
- `std/sync/mutex.ax`, `std/sync/rwlock.ax`, `std/async/sync.ax`:
  - `@no_suspend_hold` present on `MutexGuardImpl<T>`, `RwLockReadGuardImpl<T>`, and `RwLockWriteGuardImpl<T>`.
  - `AsyncMutexGuard<T>` (`std/async/sync.ax`) remains unmarked per `SPEC-34 AXS-EXEC-031`.

### 2. Stage-2/3 Build & Fixed-Point Verification (in `build-snap-T422e/`)
- `python tools/build_axiomc.py --out build --root . --stage 3`:
  - `STAGE1 OK`: `axiomc1.exe` (29,760,512 bytes, `sha256=18987be0a8567f5c`)
  - `STAGE2 (O1) OK` / `STAGE3 (O1) OK`: `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == d32b19bbe7c6b6a2629b5afafb4feec0db87b0a63a6e2939148f684061cd41d8` (8,962,560 bytes).

### 3. Boundary Cross-Check & QA Adversarial Tests
Added 3 adversarial tests in the main tree (refreshed into `build-snap-T422e/` via `taskctl.py snapshot T422e`, all PASS):
- `tests/ui/async_guard_across_await/qa_adversarial_guard_seams.ax`: verifies `@no_suspend_hold enum TokenEnum` and nested generic `Outer<Token>` (wrapping `Inner<T>`) held across `.await` emit `AX_ASYNC_GUARD_ACROSS_AWAIT` with the exact non-drop-flag stderr message, while unmarked `MutexGuard` / `RwLockWriteGuard` held across `.await` are accepted.
- `tests/ui/async_guard_across_await/qa_adversarial_escape_seams.ax`: verifies returning `@no_suspend_hold` `TokenEnum`, `(i64, Token)`, `Option<Token>`, `[1]Token`, `Outer<Token>`, and escaping a derived `mut_view(tk.v)` from a block all emit `AX_CONC_GUARD_ESCAPE`, while scalar method return (`tk.val() -> i64`) and returning unmarked `MutexGuard` / `RwLockWriteGuard` are accepted.
- `tests/run/async_guard_across_await/qa_unmarked_guard_names_and_scalar_read.ax`: verifies in `interp`, `native`, and `native-O1` (exact `stdout: OK qa_unmarked_guard_names_and_scalar_read 77\n`) that unmarked user structs literally named `MutexGuard` and `RwLockWriteGuard` returned from `.lock()`/`.write()` methods can be returned from functions and held across `.await`, and that a scalar read from a `@no_suspend_hold` `Token` before dropping it can be held across `.await`.
- Verified `tests/std/async/structured/spec34_local_executor_example.ax`: `xfail: T422e` removed; `[interp]` PASS (`OK spec34_local_executor_example 40`), `[native]`/`[native-O1]` SKIP via `native-after: T422d` (justified per ADR-0005 for generic `Future` `.await` native lowering tracked by `T422d`).

### 4. Native-Evidence Spot-Proof (Step 4a)
- Every new/touched run test checks exact `stdout:` (`WEAK-NATIVE: 0` in own/changed tests).
- Mutated `// stdout:` in `build-snap-T422e/tests/run/async_guard_across_await/drop_guard_once_after_resume.ax` (`7` -> `999`), ran `python tools/axtest.py --compiler build/axiomc2.exe --filter drop_guard_once_after_resume --no-cache -j 2 --verbose`:
  - Mutated: `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` (`[interp]`, `[native]`, `[native-O1]` all failed at byte 80).
  - Restored: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`.

### 5. Full Per-Task Gate (`taskgate.py` inside `build-snap-T422e/`)
Command:
`python tools/taskgate.py --task T422e --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T422e.json`

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 59 | 131 | 127 | 0 | 4 | 0 | 1 |
| affected | 397 | 825 | 820 | 0 | 5 | 0 | 124 |
| smoke | 33 | 56 | 56 | 0 | 0 | 0 | 24 |
| **total (dedup)** | 428 | 879 | 874 | 0 | 5 | 0 | 147 |

- `Cache`: `CACHED 147, miss 16, uncacheable 306, stored 9, dep_source exact, verification sample seed=1614046674 n=20 of 106 hits, mismatch none, rejected {}, producer snapshot`
- `WEAK-NATIVE`: `15 in the run; 0 in the task's own/changed tests`
- `Baseline`: `BASELINE OK`, `Failing ids: none`
- `archcheck`: `clean (exit 0) archcheck: 232 files scanned, 0 violations`
- `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 22 s`
- `unmatched changed files`: `none`
- `TASKGATE T422e exit=0`

### 6. Board & Staging Hygiene
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T422e`: exit 0, 0 `REFUSED` lines.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).

### Findings
None.

## Files changed
- _workspaces/reports/T422e-qa.md
- tests/run/async_guard_across_await/qa_unmarked_guard_names_and_scalar_read.ax
- tests/ui/async_guard_across_await/qa_adversarial_escape_seams.ax
- tests/ui/async_guard_across_await/qa_adversarial_guard_seams.ax

VERDICT: PASS round=0

### Rebase gate (HEAD f564f78)
- Snapshot `build-snap-T422e/` refreshed onto HEAD `f564f78` (`T496b` + `T423a` landed) + 40 T422e files + 60 regenerated selfhost bundles.
- Stage-2 build (`python tools/build_axiomc.py --out build --root . --stage 2` in `build-snap-T422e/`): `FIXED-POINT (O1) OK` (`sha256=c019091c186b627d04a4805797a39b6b2c7e1018866c2c43c7bb84c7f899d407`, 8,976,384 bytes) and `STAGE0-GUARD OK`.
- `taskgate` (`python tools/taskgate.py --task T422e --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T422e.json` in `build-snap-T422e/`): exit 0; `own` 59 ids (127 PASS / 0 FAIL / 4 SKIP), `affected` 397 ids (820 PASS / 0 FAIL / 5 SKIP), `smoke` 33 ids (54 PASS / 0 FAIL / 0 SKIP), **total (dedup)** 428 ids (`TOTAL 877 PASS 872 FAIL 0 SKIP 5 XFAIL 0`); `BASELINE OK`; `Failing ids: none`; `WEAK-NATIVE: 15 in the run; 0 in the task's own/changed tests`; `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`; `smoke-check: OK`; `unmatched changed files: none`.
- Hygiene: `taskctl.py changes T422e` exit 0 (0 `REFUSED`); `harness_check.py` `HARNESS OK` (exit 0).

VERDICT: PASS round=0 (rebase)
