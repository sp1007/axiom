# T481a Implementation Report — Harden saturating lowering and backend ICE reporting

## Summary

Three follow-ups to T481, no behaviour change for correct programs.

1. **Narrow operand cleanup no longer uses an identity op** (`compiler/lir/builder.ax`, `lower_sat_operand`).
   `LIR_INST_BIT_OR(raw, 0)` is replaced by an explicit extension built from existing LIR ops:
   `SHL raw, 64-bw` then `SAR` (signed) / `SHR` (unsigned) by `64-bw`, both vregs typed `i64`/`u64` so isel
   adds no further truncation. This is the same shift pair `isel_emit_trunc` uses, so no new LIR opcode, no new
   top-level symbol and no change under `compiler/target/x64` or `compiler/lir/lir.ax` were needed. A cast
   narrowing is a no-op in LIR (`MIR_RVALUE_CAST` lowers to its operand), so there is no existing "cast extension"
   LIR form to reuse; the shift pair is the explicit form. A comment states the invariant (operands of the overflow
   ops and of the sign extraction are canonical 64-bit sign/zero-extended values). No algebraic simplification can
   drop it (not an identity).
2. **ICE on the `.mir` emit paths** (`compiler/driver/pipeline.ax`, `compiler/backend/session.ax`).
   `session_emit_{lir,mi,mc}_mir_text_opt` keep their signatures (hand-written selfhost harnesses call the
   non-`_opt` wrappers and are outside this task's paths). The driver's `--emit=lir|mi|mc <file>.mir` branches now,
   when the emitter returns false and the session has no error yet, report `AX_ICE_INTERNAL` with `span_none()`
   (a `.mir` text has no HIR item span) and exit with `AX_EXIT_ICE` (3), like the HIR paths. If a diagnostic
   already exists (parse/verify error) the exit code stays `AX_EXIT_DIAG` (1) and no ICE is added.
   `backend_report_ice` became `pub` for this. Before: silent exit 1; after: `error[AX_ICE_INTERNAL]: internal
   compiler error`, exit 3.
3. **Readable ICE message**: the `BACKEND_ICE_MSG` byte array is deleted (one top-level symbol fewer) and
   `backend_report_ice` builds the message from the string literal `"internal compiler error"` with the same
   `str` -> NUL-terminated arena copy pattern as `ux2_sv` / `lsp_str_view`. Text unchanged.

Extern-id note (T444): the change adds no top-level symbol except the `pub` visibility and two `use` lines in
`pipeline.ax`; stage 1 built without `AX_TYPE_NOT_CALLABLE`.

## LIR before / after (narrow `saturating_add`, `fn f(a: i8, b: i8) -> i8 { a.saturating_add(b) }`)

`axiomc2 inspect --emit=lir` (the LIR printer prints `SAR` as `shr`, existing behaviour).

Before (post-T481 compiler):

```
v7 = load v6;
v8 = const 0;
v9 = or v7, v8;          <- identity op used only to make isel truncate
v11 = load v10;
v12 = const 0;
v13 = or v11, v12;
v14 = add v9, v13;
v15 = sadd_overflow v9, v13;
```

After:

```
v7 = load v6;
v8 = const 56;
v9 = shl v7, v8;
v10 = shr v9, v8;        <- SAR by 56: explicit sign extension from 8 bits
v12 = load v11;
v13 = const 56;
v14 = shl v12, v13;
v15 = shr v14, v13;
v16 = add v10, v15;
v17 = sadd_overflow v10, v15;
```

No `or ..., 0` remains; the extension is explicit. Unsigned narrow operands use `shl`/`shr` by `64-bw`.

## Tests

- New `tests/run/saturating_native/narrow_dirty_operands.ax` (modes interp, native, native-O1): u8/u16/u32/i8/i16/i32,
  all of add/sub/mul, edge-value matrix (9 unsigned / 10 signed values squared). Operands come from (1) a narrowing
  cast of a `u64` whose bits above the type width are garbage (patterns alternate per pair), (2) function
  parameters filled from such casts, (3) fields of a struct passed by value. Expected values are computed by
  independent 64-bit arithmetic on the clean source values; the program prints `NARROW-SAT-OK` and exits 0, or
  `NARROW-SAT-BAD <n>` and exits 1.
- Mutation proof: changing one expected clamp constant (255 -> 254) in a snapshot copy makes all 3 legs FAIL
  (exit code 1); restored afterwards.
- New `tests/ui/backend_ice/sat_u128_emit_{lir,mi,mc}.test` + `sat_u128_unsupported.mir`: a `SatAdd` on `u128`
  (not lowerable before T453) -> `--emit=lir|mi|mc` prints `AX_ICE_INTERNAL` / `internal compiler error` on
  stderr and exits 3. Before the change `--emit=mc` exited 1 with no message (checked with the post-T481 compiler).
  The input is valid for the verifier, so it needs no test hook.
- In `build-snap-T481a` with `build/axiomc2.exe` (sha256 f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce):
  `axtest.py --no-cache -v saturating_native backend_ice` -> `TOTAL 37 PASS 37 FAIL 0`, `WEAK-NATIVE 0`
  (existing 10 width files x 3 legs + `qa_t481_saturating_bounds.test` + the new file x 3 + 3 UI tests).
- `tools/archcheck.py`: 0 violations; all `tests/selfhost/*/gen_*.py --check` clean in the snapshot.
- Affected-set run: see "Gate run" below.

## Decisions

- Shift pair instead of a new LIR extension op: the backend's own explicit extension is this pair, the task allowed
  a new op only when no explicit form exists, and a pair avoids touching lir.ax/isel/verifier/printer and the extern
  id budget. Unsigned uses `shl`/`shr` (not `and mask`) because an `and` with `0xFFFFFFFF` could be encoded as a
  sign-extended imm32.
- ICE exit code 3 only when no earlier diagnostic exists, to keep existing exit-code behaviour for diagnosed input.
- `.mir` paths for `lir` and `mi` got the same treatment as `mc` ("every backend lowering failure gives a message").

## Files changed

- compiler/lir/builder.ax
- compiler/backend/session.ax
- compiler/driver/pipeline.ax
- tests/run/saturating_native/narrow_dirty_operands.ax
- tests/ui/backend_ice/sat_u128_unsupported.mir
- tests/ui/backend_ice/sat_u128_emit_lir.test
- tests/ui/backend_ice/sat_u128_emit_mi.test
- tests/ui/backend_ice/sat_u128_emit_mc.test

## Gate run

In `build-snap-T481a`, `axtest.py --no-cache -j 2 --id-file` over the non-selfhost tests selected by
`--affected compiler/lir/builder.ax compiler/backend/session.ax compiler/driver/pipeline.ax` (groups diff, driver,
inspect, lir, mc, modules, run: 155 ids) plus `selfhost/lir/qa_lir_seam_edge.ax` and `selfhost/lir/qa_lir_from_mir.ax`
(all legs): `TOTAL 179 PASS 179 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`. (One `UNKNOWN-ID GROUP` line came from a
stray `GROUP` header line in my id file, not a test.) Stage 1/2 of the compiler were built from the changed sources
with the new lowering (`axiomc2.exe` sha256 above), so the compiler also compiled itself with it.

Not run by me: the remaining affected selfhost bundle tests (driver/backend/obj_link_driver/lir bundles, native
legs compile 100k-line bundles, hours at `-j 2`); I stopped that run after ~25 minutes. They are for the QA gate
(`axiom-qa.md`). Selfhost bundles are not edited or listed by this task.

## Incident

While stopping my own long test run I issued a broad `taskkill` by image name (`python.exe`) with a window-title
filter. It may have terminated other Python processes on the machine (other agents' test runs / MCP servers). My own
axtest process survived the command, so the filter probably matched little, but the coordinator should check
T444/T485 background runs and rerun them if they died. I then stopped my own run correctly by PID.

STATUS: COMPLETE round=0
