# T458b report — E12.2: float const/static items, `f32.`/`f64.` path heads, primitive associated constants

## Summary
Float constants (`const` / `static` / `static mut` / `@thread_local static`, scalar and aggregate) now compile and give
the same bits in the oracle and natively (-O0 / -O1). `f32` / `f64` work as path heads like the integer names
(`f64.f(...)` for inherent and trait functions, `f64.NAME`). Inherent associated constants work on primitive types
(`impl f64 { pub const K: f64 = ...; }` read as `f64.K`, and the same on integer types, `bool` and `char`). The
built-in integer `MIN` / `MAX` / `BITS` still take precedence.

## Changes
1. **Const types** (`compiler/types/typeck.ax` `is_valid_const_type`, `compiler/interp_opt/session.ax`
   `session_is_valid_const_type`): `f32`, `f64` and `FloatVar` are valid const types, alone and inside arrays,
   tuples and structs.
2. **Integer folder guard** (`eval_const_expr_u128`): a float-typed subexpression is never folded as an integer.
   Before this guard, `3 as f64` would have stored the integer 3 as the float's bits. Float initializers are left to
   the session const evaluator, which runs the oracle's strict soft-float (ADR-0004 §8). This is also why `1.0 / 0.0`
   and `0.0 / 0.0` no longer report `AX_CONST_DIV_ZERO`.
3. **Session const evaluator worklist** (`session_comptime_check_and_eval`):
   - Top-level consts and statics are evaluated in source order, as before.
   - Associated consts of non-generic impls are also evaluated when typeck typed them but could not fold them.
   - Typeck evaluated integer constants eagerly and in dependency order, which float constants never had. So an item
     whose MIR body reads a constant that has no value yet (`B = A * 2.0` written before `A`) is now deferred and
     retried until every item is done.
   - The check is `sess_body_reads_pending`: it looks for a `MIR_CONST_INT` operand that names a pending const
     symbol.
   - When a round makes no progress, the remaining items are evaluated without deferral, so each reports its own
     diagnostic once.
   - Programs where every constant is already folded take exactly the old path, with the same diagnostics in the
     same order.
4. **MIR builder** (`compiler/mir/builder.ax`, lock):
   - A `CONST_FLOAT` value lowers to `MIR_CONST_FLOAT` with its exact bits, both for a const path and for an
     associated const (`Type.NAME`).
   - An associated const that has no value yet now names its symbol, like an unevaluated const path, so the
     evaluator can defer the item that reads it.
5. **Path heads** (`lookup_path_type_by_name`): `f32` and `f64` map to their types, as the integer names do. This
   replaces `AX_NAME_UNRESOLVED` for `f64.mk(4)` and `f64.NAME`. The resolver itself needed no change: both names
   were already prelude primitives.
6. **Primitive associated constants**:
   - The impl search for `Type.NAME` moved out of the struct-only branch into `tc_impl_assoc_const_ty`.
   - It now also runs for integer, float, `bool` and `char` bases, after the built-in integer `MIN` / `MAX` / `BITS`.
7. **`@thread_local static` float initializers**:
   - TLS initializers are folded only by typeck (`tc_eval_tls_const_bytes`). That folder now accepts a float leaf
     that is a float literal or a negated one, using the lexer's directly rounded bits (`-0.0` keeps its sign).
   - A scalar float TLS value is stored as `CONST_FLOAT`, so the native TLS emitter in `compiler/driver/pipeline.ax`
     (lock) now writes `CONST_FLOAT` bits as well as `CONST_INT` ones. Before this, a native TLS float read 0. The
     `statics.ax` native leg caught it, which also shows that test's native checks are live.
8. **What needed no change**:
   - `.rdata` / `.data` / `.bss` emission is byte-based, so the `-0.0` bits are non-zero and never zero-filled.
   - Constant operands use `MIR_CONST_FLOAT`, which the optimizer guard of T458 (`opt_is_scalar_const_op`) already
     treats as opaque.

## Decisions (for the architect)
- **D1: enum constants with payload fields stay rejected**, whatever the payload type: `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`,
  pinned by `tests/ui/comptime/invalid_type_err.ax`. "Floats inside enums" therefore applies only to fieldless enums.
  Lifting the payload restriction is a separate, general feature, not a float one.
- **D2: a `@thread_local` float initializer must be a literal or a negated literal** (scalar or inside an
  aggregate). TLS values are folded in typeck, which has no soft-float. An expression such as `0.5 * 2.0` there gives
  the existing `AX_TYPE_INVALID_TLS_DECL`. Non-TLS statics accept any constant expression.
- **D3: deferral uses the MIR operand marker, not a HIR dependency walk.** No generic HIR expression walker exists.
  The builder already lowers an unevaluated const path to `MIR_CONST_INT{sym}`, so the operand scan is exact and
  cheap. It only runs when pending (typeck-unfolded) constants exist.
- **D4: no tests for const generics or integer patterns.**
  - Const generics are not parsed yet (`struct G<const N: usize>` is a parse error), so "a float constant is not a
    const-generic argument" cannot be tested.
  - A name in pattern position is a binding, not a constant pattern, so a float constant cannot reach an integer
    pattern. Both behave exactly as before.
- **D5: `f32.MAX` is not built in.** It is a std constant (T460), so without `std.core.float` it reports
  `AX_TYPE_UNKNOWN_FIELD` (`unknown_assoc.ax`).

## Tests
- `tests/run/float_const/` (each runs in interp and natively at -O0 and -O1; exact stdout; expected bits come from
  Python `struct.pack`, an oracle independent of the compiler):
  - `scalar_bits.ax`: ±0, ±inf, NaN-ness, the minimum subnormal, the minimum normal, MAX, 0.1. For f32 it covers
    direct rounding of `1 + 2^-24 + 2^-60`, which gives `0x3F800001`, where rounding through f64 would give
    `0x3F800000`.
  - `expr_initializers.ax`: a forward reference, arithmetic, int/float casts, f32 -> f64, REQ-OWNER-007 promotion of
    a literal and of an integer constant, overflow to inf, an integer constant computed from float constants, and
    constants used as operands and call arguments.
  - `tables_and_aggregates.ax`: `[N]f64` / `[N]f32` tables indexed at run time, struct, tuple, nested `[2]Coeff`,
    `-0.0` inside an aggregate, and a table built from other constants.
  - `statics.ax`: immutable, `static mut` (including an all-zero `.bss` one), `@thread_local static mut` (scalar and
    array, including `-0.0`); reads and writes.
  - `primitive_paths.ax`: `f64.half` (inherent), `f64.make` (trait), `T.make` through `build<f64>`,
    `f32.from_int`, associated constants on `f64`, `f32`, `u8` and `i32` (one of them reads a constant before its
    definition), and `i32.MAX` / `i32.BITS` still working.
- `tests/ui/float_const/`:
  - `type_mismatch.ax` (`AX_TYPE_MISMATCH` ×4)
  - `array_len.ax` (`AX_TYPE_ARRAY_SIZE`)
  - `unknown_assoc.ax` (`AX_TYPE_UNKNOWN_FIELD` ×4, previously `AX_NAME_UNRESOLVED` for the float heads)
  - `non_const_init.ax`: a non-returning call and a `static mut` read give `AX_CONST_OVERFLOW`, `loop {}` gives
    `AX_CONST_EVAL_LIMIT`. These are the same codes as the integer equivalents, checked side by side.
- `grep -rn AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP tests`: no test expects it for a float const. The remaining float
  mentions are frozen axiom0 tests (`requires: axiom0-internal`, let bindings) or comments.

## Verification (snapshot `build-snap-T458b`)
- `python tools/build_axiomc.py --out build --root .`:
  - STAGE1 OK
  - FIXED-POINT (O1) OK: `sha256(axiomc2) == sha256(axiomc3) == dd6c7b0bc8b8d4bd…`
  - STAGE0-GUARD OK
  - BUILD-AXIOMC OK
- `python tools/taskgate.py --task T458b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  - `TOTAL 612 PASS 610 FAIL 0 SKIP 2 XFAIL 0`, BASELINE OK, `TASKGATE T458b exit=0`
  - own tests: 19/19 results PASS
  - WEAK-NATIVE 0 in the task's own tests
  - all affected selfhost `bundles_current.test` groups PASS: backend, driver, drop, interp, interp_opt, lir, mir,
    obj_link_driver, opt, own_mir_verify, traits, typeck, typeck_traits, types, verify
  - There is no repository-level `tests/selfhost/bundles_current.test` (that id selects 0 tests). The per-group
    bundles above are the current form.
- `python tools/archcheck.py`: 235 files scanned, 0 violations.

## Files changed
- compiler/types/typeck.ax
- compiler/interp_opt/session.ax
- compiler/mir/builder.ax
- compiler/driver/pipeline.ax
- tests/run/float_const/scalar_bits.ax
- tests/run/float_const/expr_initializers.ax
- tests/run/float_const/tables_and_aggregates.ax
- tests/run/float_const/statics.ax
- tests/run/float_const/primitive_paths.ax
- tests/ui/float_const/type_mismatch.ax
- tests/ui/float_const/array_len.ax
- tests/ui/float_const/unknown_assoc.ax
- tests/ui/float_const/non_const_init.ax

STATUS: COMPLETE round=0
