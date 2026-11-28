# T428i QA Report (Round 0) — Statics and atomics in `async fn`

## Audit Summary
1. **Diff & Scope (`compiler/mir/async_lower.ax`)**:
   - Verified `compiler/mir/async_lower.ax` is byte-identical between the main repo and `build-snap-T428i/` (`sha256=47D2594618B7FAEB0BDC6CC6AE695FD935682BA459234075C3E327324EBCD616`).
   - Verified `build-snap-T428i/build/axiomc2.exe` matches the engineer report (`sha256=309DD9ABED2BC317C00F73765BB820CC1DAB471DEAA799BD9F6F7ABEE5EB95F4`).
   - Verified no T428i edits outside `compiler/mir/async_lower.ax` and `tests/run/async/statics_atomics_in_async/` (no `docs/`, no `bootstrap/axiom0/`).
2. **MIR Statement / Local / Projection / Terminator Cross-Check (`compiler/mir/mir.ax` & `compiler/mir/builder.ax`)**:
   - **Local kinds (`MIR_LOCAL_*`, `0u8..6u8`)**: `al_local_is_global` covers all three non-frame storage kinds (`MIR_LOCAL_CONST=4`, `MIR_LOCAL_TLS=5`, `MIR_LOCAL_STATIC=6`). Global locals are excluded from `sp_live`/`unique_live_buf` in Step 2, excluded from `inplace_field` in Step 2b, and keep their original `kind`/`mut_flag`/`const_sym` in Step 7 `poll_locals` initialization.
   - **Statement kinds (`MIR_STMT_*`, `0u8..4u8`)**: `compiler/mir/mir.ax:303-307` defines exactly 5 statement kinds (`ASSIGN`, `STORAGE_LIVE`, `STORAGE_DEAD`, `DROP`, `ATOMIC`). Cross-checked `MIR_STMT_ATOMIC` operand layout against `compiler/mir/builder.ax:1106-1117`:
     - `aop <= MIR_ATOMIC_CMPXCHG_WEAK`: `rvalue.use_op` (receiver)
     - `aop >= MIR_ATOMIC_STORE && aop <= MIR_ATOMIC_CMPXCHG_WEAK`: `rvalue.lhs` (value / expected)
     - `aop == MIR_ATOMIC_CMPXCHG || aop == MIR_ATOMIC_CMPXCHG_WEAK`: `rvalue.rhs` (desired)
     - `aop <= MIR_ATOMIC_CMPXCHG_WEAK && aop != MIR_ATOMIC_STORE`: `place` (destination)
     - `aop` in `10..12` (`FENCE`, `COMPILER_FENCE`, `SPIN_HINT`): no local operands.
     All four active operand/place roles are consistently handled in `remap_stmt`, `async_local_used_from`, and `maybe_init_stmts`.
   - **Projections (`MIR_PROJ_*`, `0u8..4u8`) & Terminators (`MIR_TERM_*`, `0u8..7u8`)**: `place_proj_uses_local` covers both `MIR_PROJ_INDEX` and `MIR_PROJ_SUB_SLICE` (`has_from`/`from_local`, `has_to`/`to_local`), and is checked on LHS destination places of `MIR_STMT_ASSIGN`, `MIR_STMT_ATOMIC`, `MIR_TERM_CALL`, `MIR_TERM_SUSPEND`, and Step 2 `is_live` (`dest_place`). `MIR_TERM_SUSPEND` init/uninit transitions in `async_local_maybe_init_at` are properly guarded by `proj_count == 0`.
3. **Engineer Tests (5 files under `tests/run/async/statics_atomics_in_async/`)**:
   - All 5 tests (`static_mut_across_await.ax`, `atomic_local_across_await.ax`, `atomic_ptr_across_await.ax`, `local_executor_spawned_statics_atomics.ax`, `mir_projected_dest_and_atomic_liveness.ax`) run in `interp`, `native`, and `native-O1` with exact `// stdout:` assertions and strong coverage of `REQ-ASY-082` and `REQ-MIR-144`.

## QA Adversarial Test
Added `tests/run/async/statics_atomics_in_async/qa_tls_static_array_cas_retry.ax` (3-mode `interp` / `native` / `native-O1`, exact `// stdout:`):
- `@thread_local static mut TLS_COUNTER` mutated externally during `.await` and read/written across 3 `.await`s (verifies `MIR_LOCAL_TLS` stays direct TLS storage).
- `static mut G_BUF: [4]i64` written via an `.await` destination indexed by a local computed before `.await` (`G_BUF[idx] = fut.await`) while the polled future concurrently mutates `G_BUF[0]`.
- `AtomicI64.compare_exchange` failure & retry across `.await` on both a local `AtomicI64` reached via `*const AtomicI64` and a `static AtomicI64`.
- `fetch_or`, `fetch_and`, `fetch_xor`, and `swap` with opaque mask locals live across `.await`.

## Independent Verification (`build-snap-T428i/`, `-j 2`)
- **Targeted tests** (`python tools/axtest.py --compiler build/axiomc2.exe --filter run/async/statics_atomics_in_async --no-cache -j 2 --verbose`):
  - `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 5 engineer tests + 1 QA adversarial test pass in `interp`, `native`, `native-O1`).
- **Live mutation spot-proof** (inside `build-snap-T428i/` only on `qa_tls_static_array_cas_retry.ax`):
  - Mutated expected stdout (`tls=100,115,125` -> `tls=100,115,999`): `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed at byte 12).
  - Restored byte-identical (`sha256=3D25CB1919337DB298C7B58F590D08D6B83FC48EA520E09FD555323ED56AD7C1`): `TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`.
- **Taskgate** (`python tools/taskgate.py --task T428i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428i.json`):
  - `own`: 6 ids, 18 results, `18 PASS / 0 FAIL`
  - `affected`: 208 ids, 389 results, `387 PASS / 0 FAIL / 2 SKIP`
  - `smoke`: 35 ids, 58 results, `58 PASS / 0 FAIL`
  - `total (dedup)`: `TOTAL 445 PASS 443 FAIL 0 SKIP 2 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`, `archcheck: 252 files scanned, 0 violations`, `smoke-check: OK`, `TASKGATE T428i exit=0`.
- **Required suites** (`--filter run/async --filter mir/async --filter std/async --filter conformance/p11 --filter run/atomics --filter selfhost/mir --filter bundles_current --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt -j 2`):
  - `TOTAL 495 PASS 495 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0`, `exit=0`.
- **Hygiene checks (main repo root)**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428i`: 0 `REFUSED`, `exit=0`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`, `exit=0`.

## Files changed
- tests/run/async/statics_atomics_in_async/qa_tls_static_array_cas_retry.ax

## Verdict
VERDICT: PASS round=0
