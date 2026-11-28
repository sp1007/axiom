# T428i Report — Statics and atomics preserve their semantics across async lowering

## Summary of Fixes (`compiler/mir/async_lower.ax`)
1. **Static / TLS / Const ("global") places stay direct global accesses (`al_local_is_global`)**:
   - In `mir_lower_async_body` Step 2 (live-across-await scan), locals where `al_local_is_global` is true (`MIR_LOCAL_STATIC`, `MIR_LOCAL_TLS`, `MIR_LOCAL_CONST`) are excluded from `sp_live` and `unique_live_buf`, so they are never copied into the `Coroutine` state machine struct, never saved/restored across `.await`, and never included in per-state cancellation `Drop` fields.
   - In `mir_lower_async_body` Step 7 (`poll_locals` initialization), `(*new_decl).kind = MIR_LOCAL_TEMP` is now applied only when `!al_local_is_global(view(*orig_decl))`. Global locals retain their exact `MIR_LOCAL_STATIC` / `MIR_LOCAL_TLS` / `MIR_LOCAL_CONST` kind, `mut_flag`, and `const_sym`, so every access in `poll` stays a direct access to the process-wide static (or TLS/const) storage.
2. **Complete MIR statement, projection, and terminator operand audit (`REQ-ASY-082`, `REQ-MIR-144`)**:
   - `remap_stmt`: added `MIR_STMT_ATOMIC`, renaming active `place` (`aop <= MIR_ATOMIC_CMPXCHG_WEAK && aop != MIR_ATOMIC_STORE`), `rvalue.use_op` (`aop <= MIR_ATOMIC_CMPXCHG_WEAK`), `rvalue.lhs` (`aop >= MIR_ATOMIC_STORE && aop <= MIR_ATOMIC_CMPXCHG_WEAK`), and `rvalue.rhs` (`aop == MIR_ATOMIC_CMPXCHG || aop == MIR_ATOMIC_CMPXCHG_WEAK`).
   - `async_local_used_from`: added `MIR_STMT_ATOMIC` read-before-write liveness scanning; added `place_proj_uses_local` (covering both `MIR_PROJ_INDEX` and `MIR_PROJ_SUB_SLICE`) for LHS destination places of `MIR_STMT_ASSIGN`, `MIR_STMT_ATOMIC`, `MIR_TERM_CALL`, and `MIR_TERM_SUSPEND` (and `place_uses_local` now covers `MIR_PROJ_SUB_SLICE` as well as `MIR_PROJ_INDEX`).
   - `maybe_init_stmts` / `async_local_maybe_init_at`: added `MIR_STMT_ATOMIC` move/def tracking and guarded `MIR_TERM_SUSPEND` whole-local init/uninit transitions with `proj_count == 0`.
   - Step 2 `is_live`: included `place_proj_uses_local(view((*spi).dest_place), l)` so index/sub-slice locals used inside an `.await` destination place (`arr[i] = fut.await`) remain live across that suspension point.

## Full MIR Statement-Enum Audit (`compiler/mir/mir.ax`)

Complete `MIR_STMT_*` enum in `compiler/mir/mir.ax` (lines 303–307) — every statement kind in the compiler:

| Enum Constant | Value | Local / Place Operands | Lowered From | `remap_stmt` | `async_local_used_from` | `maybe_init_stmts` | `async_local_is_addr_observable` |
|---|---|---|---|---|---|---|---|
| `MIR_STMT_ASSIGN` | `0u8` | `place` (dst + `INDEX`/`SUB_SLICE` projs), `rvalue` (`USE`, `REPEAT` incl. `repeat_count_op`, `REF`, `LEN`, `CAST`, `OVERFLOWS_BINARY_OP`, `BINARY_OP`, `UNARY_OP`, `DISCRIMINANT`, `AGGREGATE`) | Assignments, `INTR_MIR_OP` intrinsics (`wrapping_*`, `saturating_*`, `rotate_*`, `count_ones`, `leading_zeros`, `trailing_zeros`, `swap_bytes`, `reverse_bits`, `to_bits`, `from_bits`, `sqrt`, `abs`, `copysign`), `len`, `address_of`/`address_of_mut`/`addr_of`/`static_addr`/`fn_addr`, `@addr` overlays, `Atomic.new`, `Atomic.into_inner`, `Atomic.is_lock_free` | Handled (`remap_place` + `remap_rvalue`) | Handled (`rvalue_uses_local` + `place_proj_uses_local` + whole/partial `place`) | Handled (`rvalue_moves_local` + whole `place` init) | Handled (`MIR_RVALUE_REF` on `rvalue.place.local`) |
| `MIR_STMT_STORAGE_LIVE` | `1u8` | `storage_local` | Lexical scope entry / in-place markers | Handled (`al_map_local`) | No-op (does not read prior value) | No-op | N/A |
| `MIR_STMT_STORAGE_DEAD` | `2u8` | `storage_local` | Lexical scope exit | Handled (`al_map_local`) | Handled (kills `l`) | Handled (clears init of `l`) | N/A |
| `MIR_STMT_DROP` | `3u8` | `place` (dropped place + projs) | Scope-exit drop statements | Handled (`remap_place`) | Handled (`place_uses_local`) | Handled (clears init on whole `place`) | N/A |
| `MIR_STMT_ATOMIC` | `4u8` | `rvalue.bin_op` (`aop` `0..12`): `use_op` (`0..9`), `lhs` (`1..9`), `rhs` (`8..9`), `place` (`0, 2..9`); fences/spin-hint (`10..12`) have no local operands | `Atomic<T>.{load, store, swap, fetch_add, fetch_sub, fetch_and, fetch_or, fetch_xor, compare_exchange, compare_exchange_weak}`, `fence`, `compiler_fence`, `spin_loop_hint` | **Fixed** (`remap_place` + `remap_operand` for active `use_op`/`lhs`/`rhs`) | **Fixed** (reads `use_op`/`lhs`/`rhs`, checks `place_proj_uses_local` + whole/partial `place`) | **Fixed** (`op_moves_local` + whole `place` init) | Receiver borrow emitted by `builder.ax` as preceding `MIR_STMT_ASSIGN` (`MIR_RVALUE_REF`), already detected |

Notes on other MIR constructs audited alongside statements:
- **Volatile & raw memory intrinsics** (`ptr_copy`, `ptr_copy_nonoverlapping`, `ptr_write_bytes`, `drop_in_place`, etc.): no separate `MIR_STMT_*` kind exists in `compiler/mir/mir.ax`; they lower to `MIR_TERM_CALL` (or `MIR_TERM_DROP` / `MIR_STMT_ASSIGN` / `MIR_TERM_ASSERT` for `INTR_MIR_TERM`).
- **Terminators (`MIR_TERM_*`, `0u8..7u8`)**: `GOTO`, `SWITCH_INT`, `RETURN`, `UNREACHABLE`, `DROP`, `CALL`, `ASSERT`, `SUSPEND` — all audited; `MIR_TERM_CALL` and `MIR_TERM_SUSPEND` destination projections and whole-local kills are now handled in `async_local_used_from`.
- **Projections (`MIR_PROJ_*`, `0u8..4u8`)**: `DEREF`, `FIELD`, `INDEX`, `DOWNCAST`, `SUB_SLICE` — `place_uses_local` / `place_proj_uses_local` now cover both `INDEX` and `SUB_SLICE` (`has_from`/`from_local`, `has_to`/`to_local`), matching `remap_place`.

## HEAD (`051b977a`) Failure Repros (Before Fix)

Verified on untouched `HEAD` `051b977a` (`build-snap-T428i/build/axiomc2.exe`, `sha256=b757c3d718e78cd3f2217cd4a23c2e3c0a8b9e49f58d95686f245a4d2dd05465`): all 5 new tests compile and fail at runtime across `interp`, `native`, and `native-O1` (`15/15 FAIL`):
1. `tests/run/async/statics_atomics_in_async/static_mut_across_await.ax`:
   - `[interp]`, `[native]`, `[native-O1]`: `FAIL` — expected `g=1521 pair=69,400 total=4756`, got `g=1501 pair=69,20 ...` (private poll-frame copy of `static mut`).
2. `tests/run/async/statics_atomics_in_async/atomic_local_across_await.ax`:
   - `[interp]`: `TIMEOUT` (infinite `compare_exchange_weak` loop due to unremapped `MIR_STMT_ATOMIC` locals).
   - `[native]`, `[native-O1]`: `CRASH` (`status 3221225477` / `0xC0000005` access violation).
3. `tests/run/async/statics_atomics_in_async/atomic_ptr_across_await.ax`:
   - `[interp]`: `FAIL` (`exit 125`, `error[AX_UNSAFE_INTERP_UB]: null pointer dereference` at `(*p).fetch_add(8i64, Ordering.AcqRel)`).
   - `[native]`, `[native-O1]`: `CRASH` (`status 3221225477`).
4. `tests/run/async/statics_atomics_in_async/local_executor_spawned_statics_atomics.ax`:
   - `[interp]`: `FAIL` — expected `ra=3095 rb=2424 g=1355 shared=99`, got `ra=-1 rb=-1 g=0 shared=0`.
   - `[native]`, `[native-O1]`: `CRASH` (`status 3221225477`).
5. `tests/run/async/statics_atomics_in_async/mir_projected_dest_and_atomic_liveness.ax`:
   - `[interp]`: `FAIL` (`exit 125`, `error[AX_UNSAFE_INTERP_UB]: null pointer dereference` at `a.fetch_add(add_delta, Ordering.AcqRel)`).
   - `[native]`, `[native-O1]`: `CRASH` (`status 3221225477`).

## Verification (Snapshot `build-snap-T428i/`, HEAD `051b977a` + T428i change set)
- **Snapshot & bundles**: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T428i` — `HEAD 051b977 + 7 changed, 0 deleted file(s) of T428i`; bundles regenerated: `48 generator(s), 165 file(s)`.
- **Stage-2 build & fixed point**: `python tools/build_axiomc.py --out build --root . --stage 2`
  - `STAGE1 OK`: `axiomc1.exe` (`35002368 bytes`, `sha256=a5cfb67006ae8510`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 309dd9abed2bc317c00f73765bb820cc1dab471deaa799bd9f6f7abee5eb95f4` (`9373696 bytes`) `[seeded B==C]`
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`).
- **Targeted tests** (`--filter run/async/statics_atomics_in_async --no-cache -j 2 --verbose`):
  - `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 5 tests pass in `interp`, `native`, and `native-O1`).
- **Required suites** (`--filter run/async --filter mir/async --filter std/async --filter conformance/p11 --filter run/atomics --filter selfhost/mir --filter bundles_current --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt -j 2`):
  - `TOTAL 492 PASS 492 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0`, `exit=0`.
- **Taskgate** (`python tools/taskgate.py --task T428i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428i.json`):
  - `TOTAL 441 PASS 439 FAIL 0 SKIP 2 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE 0` in own/changed tests (3 elsewhere in run), `archcheck`: `252 files scanned, 0 violations`, `smoke-check: OK`, `TASKGATE T428i exit=0`.
- **Hygiene checks (main repo root)**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428i`: 7 staged files (`_workspaces/reports/T428i-report.md`, `compiler/mir/async_lower.ax`, 5 test files), `0 REFUSED`, `exit=0`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`, `exit=0`.

## Files changed
- compiler/mir/async_lower.ax
- tests/run/async/statics_atomics_in_async/atomic_local_across_await.ax
- tests/run/async/statics_atomics_in_async/atomic_ptr_across_await.ax
- tests/run/async/statics_atomics_in_async/local_executor_spawned_statics_atomics.ax
- tests/run/async/statics_atomics_in_async/mir_projected_dest_and_atomic_liveness.ax
- tests/run/async/statics_atomics_in_async/static_mut_across_await.ax

## Status
STATUS: COMPLETE round=0
