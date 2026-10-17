# T082e report — Port MIR verifier to Axiom

## Summary
- Ported the MIR invariant verifier (`bootstrap/axiom0/src/verify/verifier.h` and `verifier.c`) to Axiom in [`compiler/verify/verifier.ax`](file:///d:/projects/compiler/new%20lang/compiler/verify/verifier.ax) and [`compiler/verify/mod.ax`](file:///d:/projects/compiler/new%20lang/compiler/verify/mod.ax).
- Implemented all verification passes and helpers matching the C bootstrap verifier:
  - **Structural, CFG, initialized-bit, and type consistency (`verify_mir` / `ax_verify_mir`)**:
    - Block termination and valid terminator kinds (`AX_VERIFY_UNTERMINATED_BLOCK`).
    - Terminator target reachability/bounds (`Goto`, `SwitchInt` arms + `otherwise`, `Drop` target + unwind, `Call` target + unwind, `Assert` target + unwind -> `AX_VERIFY_BAD_TARGET`).
    - Local index bounds across places, storage statements (`StorageLive`/`StorageDead`), projections (`Index`/`Subslice`), rvalues, and terminators (`AX_VERIFY_UNKNOWN_LOCAL`).
    - Forward dataflow bitset fixed-point analysis for initialized locals (`AX_VERIFY_UNINIT_USE` when `func` is null, matching standalone `.mir` verification in `axiom0`).
    - Place projection type resolution and validation (`verify_check_place_projections` for `Deref`, `Field` on structs/tuples/closures, `Downcast` + `Field` on enums, `Index`, `Subslice`).
    - Rvalue type consistency (`Use`, `Repeat`, `Ref`, `Len`, `Cast`, `BinaryOp`, `OverflowsBinaryOp`, `UnaryOp`, `Discriminant`, `Aggregate` for tuples, structs, enums, arrays, and closures -> `AX_VERIFY_TYPE_MISMATCH`).
    - Call signature verification (`AX_VERIFY_CALL_SIGNATURE` for return destination type, argument count, and parameter types).
    - Function return local `_0` compatibility against `HIR_ITEM_FN` signature (`AX_VERIFY_RETURN_TYPE`).
  - **Ownership dataflow verifier (`verify_mir_own` / `ax_verify_mir_own`)**:
    - 4-state lattice (`VERIFY_ST_UNINIT = 0`, `VERIFY_ST_INIT = 1`, `VERIFY_ST_MOVED = 2`, `VERIFY_ST_MAYBE = 3`) with `verify_merge_st` (`a | b`) over CFG predecessors.
    - Ownership classification (`verify_is_owned_local` / `verify_type_needs_drop`: primitive/pointer/view/fn Copy types vs owned structs/enums/tuples/arrays/closures and user `impl Drop`).
    - Detects use-after-move (`AX_VERIFY_USE_AFTER_MOVE`), double drop (`AX_VERIFY_DOUBLE_DROP`), and missing drop on overwrite, `StorageDead`, `Call` unwind edges, and `Return` (`AX_VERIFY_MISSING_DROP`).
  - **Capability & borrow verifier (`verify_mir_cap`)**:
    - Verifies shared/mutable borrow rvalues (`MIR_RVALUE_REF`), validates mutability requirements on `MIR_BORROW_MUT` (unless borrowing through `*mut T` or `mut_view<T>`), and tracks active view borrows across basic blocks via `mir_region_relate` to detect conflicting mutations/moves/drops while borrowed (`AX_VERIFY_TYPE_MISMATCH`).
  - **Drop-flag elaboration consistency verifier (`verify_mir_drop_flags`)**:
    - Verifies that `drop_flag_local` indices on `MirLocalDecl` and `drop_flag` on `MIR_STMT_DROP`/`MIR_TERM_DROP` are in bounds (`AX_VERIFY_UNKNOWN_LOCAL`) and have type `bool` (`AX_VERIFY_TYPE_MISMATCH`), and checks post-elaboration unguarded drop invariants (`AX_VERIFY_MISSING_DROP`).
  - **Verifier-aware `.mir` text parser & entry point (`verify_parse_mir`, `verify_mir_text`)**:
    - Parses standalone `.mir` text including `type <id> = fn(...) -> ...;` declarations, local declarations, statements, rvalues, projections, and terminators, preserving out-of-bounds local/block IDs and unterminated blocks so structural and ownership verifiers emit the exact diagnostics expected by `tests/verify/*.mir` and `tests/verify/own/*.mir`.

### Selfhost Test Suite (`tests/selfhost/verify/`)
- [`tests/selfhost/verify/gen_verify_tests.py`](file:///d:/projects/compiler/new%20lang/tests/selfhost/verify/gen_verify_tests.py) generates two standalone selfhost test bundles from [`tests/selfhost/verify/harness_verify_mir.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/verify/harness_verify_mir.ax.in) and [`tests/selfhost/verify/harness_verify_pipeline.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/verify/harness_verify_pipeline.ax.in):
  1. [`tests/selfhost/verify/qa_verify_mir.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/verify/qa_verify_mir.ax):
     - Differential test over all 21 `.mir` fixtures in `tests/verify/` and `tests/verify/own/`, verifying exact diagnostic counts and diagnostic codes against `axiom0`.
     - Unit tests covering valid `.mir` bodies, binary/shift/overflow/cast type mismatches, `SwitchInt`/`Assert` bad targets, call signature mismatches, uninitialized return, struct/tuple/enum/array/slice/pointer projections and aggregates, `verify_mir_cap` mutable borrow and active borrow conflict checks, and `verify_mir_drop_flags` + recursive `verify_type_needs_drop`.
  2. [`tests/selfhost/verify/qa_verify_pipeline.ax`](file:///d:/projects/compiler/new%20lang/tests/selfhost/verify/qa_verify_pipeline.ax):
     - End-to-end selfhost pipeline test lowering Axiom source (`struct Res {}`, `fn helper(x: i32, flag: bool) -> i32`) through `session_parse_virtual_file`, `session_resolve_ast_into`, `session_lower_hir`, `session_typeck_into`, `mir_build_fn`, and `mir_drop_elaborate`, verifying both pre-elaboration and post-elaboration MIR with `verify_mir`, `verify_mir_own`, `verify_mir_cap`, and `verify_mir_drop_flags`, plus negative mutation checks (`AX_VERIFY_RETURN_TYPE` and `AX_VERIFY_BAD_TARGET`).

## Files changed
- compiler/verify/mod.ax
- compiler/verify/verifier.ax
- tests/selfhost/verify/gen_verify_tests.py
- tests/selfhost/verify/harness_verify_mir.ax.in
- tests/selfhost/verify/harness_verify_pipeline.ax.in
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

## Tests
All run in snapshot `build-snap-T082e` (HEAD `305864f` + 7 changed files):
- `python tools/archcheck.py`: `188 files scanned, 0 violations`.
- `python tools/axtest.py --filter selfhost/verify --verbose`:
  - `PASS selfhost/verify/qa_verify_mir.ax [interp]`
  - `PASS selfhost/verify/qa_verify_mir.ax [native]`
  - `PASS selfhost/verify/qa_verify_mir.ax [native-O1]`
  - `PASS selfhost/verify/qa_verify_pipeline.ax [interp]`
  - `PASS selfhost/verify/qa_verify_pipeline.ax [native]`
  - `PASS selfhost/verify/qa_verify_pipeline.ax [native-O1]`
  - `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/axtest.py --filter verify/ --verbose`:
  - `TOTAL 25 PASS 25 FAIL 0 SKIP 0 XFAIL 0`

## Spec deviations
none

## Follow-ups
1. **Bootstrap LIR lowering bug on call with projected destination (`bootstrap/axiom0/src/lir/lower.c:1269`)**:
   In `lower_mir_to_lir` (`MIR_TERM_CALL`), when `mbb->terminator.call.destination.proj_count > 0`, line 1269 allocates the call result vreg using the base local's type (`mir->locals[mbb->terminator.call.destination.local.v].ty`, e.g. `*mut u8`, 8 bytes) instead of the projected place's type (e.g. `u8`, 1 byte), and then emits an 8-byte `AX_LIR_INST_STORE` into the projected address (`*(cur + l) = foo(...)`). This overwrites 7 adjacent bytes past a `*mut u8` dereference with uninitialized stack bytes in native `O0`/`O1`. Combined with `bootstrap/axiom0/src/target/x64/isel/isel.c:570` (`AX_LIR_INST_RET` loading 8 bytes from a 1-byte `_0` stack slot into `RAX`), `*(cur + l) = verify_merge_st(...)` corrupted `cur[l + 1 .. l + 7]`. `compiler/verify/verifier.ax` avoids this by binding call results to a typed local variable (`let merged = verify_merge_st(...); *(cur + l) = merged;`) before storing through a pointer or projection.
2. **Bootstrap MIR interpreter allocation table scan (`bootstrap/axiom0/src/interp/interp.c:690, 1542`)**:
   Every function call in `--interp` appends `body->local_count` entries to `ctx->allocs` (`ctx->alloc_count++`), and on return marks them `is_live = false` without compacting `ctx->alloc_count`; every pointer dereference or offset linearly scans `ctx->allocs[0 .. ctx->alloc_count]`. Reclaiming tail `ctx->alloc_count` on function return (LIFO stack discipline) would make `--interp` orders of magnitude faster on deep selfhost tests.

STATUS: COMPLETE round=0
