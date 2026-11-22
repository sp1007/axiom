# T498g report

## Summary
Root cause (typeck, not the backends): `finalize_ptr_substmap` in `compiler/types/typeck.ax` skipped every
expression whose callee type kind lay in `TY_BUILTIN_ADDRESS_OF ..= TY_BUILTIN_NULL_MUT` (the skip was
added by T156 for dump parity with axiom0). For those generic raw-memory intrinsics, `check_call` records
a substitution for the callee path; when `T` is not written explicitly it is a fresh inference variable
(`TY_VAR`) that `check_call_rest` unifies with the pointee of the first pointer argument. Because the
substitution map entry was never deep-resolved, the MIR builder (`mb_build_call`, `is_type_arg_builtin`)
read the raw `TY_VAR` id as the element type and stored it in the callee constant. `type_size(TY_VAR)` is
0, which the interp (`TY_BUILTIN_PTR_COPY*`, `PTR_WRITE_BYTES`, `PTR_ADD/SUB`) and the LIR lowering
(`compiler/lir/builder.ax`) both clamp to 1, so every call with an inferred `T` moved / advanced by `count`
BYTES. This was not specific to arrays: `ptr_copy_nonoverlapping(a as *const u64, b, 3)` copied 3 bytes.
It went unnoticed because every inferred call in `std/` and `compiler/` uses `u8` pointers (where 1 is the
right size); std `swap` with an array `T` therefore exchanged only the low byte of element 0 (the triage
repro printed `p[0]=10` because 1 and 10 differ only in the low byte). Explicit `ptr_copy<T>(..)` was
always correct.

Fix: `finalize_ptr_substmap` now deep-resolves the substitutions of the generic raw-memory intrinsics too
(only `len`, `print`, `print_int` and `drop`, which have no type argument, are still skipped). The resolved
`T` is a `TY_PARAM` inside generic bodies, which `mb_resolve_ty` substitutes per instance, so
`size_of<T>()` of the substituted `T` is used in the interp and in native `-O0`/`-O1` without any backend
change. `resolve_deep_ty` returns the already-interned bound type, so no new types are interned for these
entries (type numbering in dumps is unchanged; the stage-0 guard and the stage-2/stage-3 fixed point
hold). Inferred intrinsic calls now have concrete substitutions, so `mono_collect_thir_substs` treats them
exactly like the explicit `<T>` calls it already handled.

Decision (no question asked): fix in typeck rather than adding a fallback in the MIR builder — the THIR
substitution is the contract the builder, mono collection and bound checking read, and leaving it
unresolved was the defect. No MIR/interp/LIR code change was needed.

## Files changed
- compiler/types/typeck.ax
- tests/run/mem_generic_array/swap_repro.ax
- tests/run/mem_generic_array/swap_kinds.ax
- tests/run/mem_generic_array/counts_bytes_ptr.ax

## Tests
New tests `tests/run/mem_generic_array/` (run, three modes, exact `stdout:`):
- `swap_repro.ax` — the triage repro (std `swap` body, `[4]u32`).
- `swap_kinds.ax` — `swap` body with `T` = `[5]u8`, `[3]u32`, `[3]u64`, `[2]Pt` (struct), `[2][3]u16`,
  `(u8, [2]u64)` and a struct holding `[3]u32`; plus `size_of` of each.
- `counts_bytes_ptr.ax` — generic `ptr_copy_nonoverlapping` count 0/1/3 over `[4][2]u32`; overlapping
  generic `ptr_copy` of 3 rows; generic `ptr_write_bytes` over one `[3]u16` row; generic `ptr_add` /
  `ptr_sub` stepping whole `[3]u32` rows; generic `replace` on an array; non-generic inferred `u64` copy.

Before the fix (snapshot axiomc2 at HEAD 0783fc0): all three fail (swap_repro `10 2 3 4 / 1 20 30 40`,
swap_kinds wrong in every row, counts_bytes_ptr wrong and `AX_UNSAFE_INTERP_UB misaligned pointer access`
on the `ptr_add` row). After: `python tools/axtest.py --compiler build/axiomc2.exe -j 2
run/mem_generic_array` → TOTAL 9 PASS 9 FAIL 0, WEAK-NATIVE 0.

Build (snapshot, clang Release): stage-0 OK, STAGE1 OK, FIXED-POINT (O1) OK
(sha256 cb258e5a0097d469…), STAGE0-GUARD OK.

Task gate (inside build-snap-T498g): `python tools/taskgate.py --task T498g --compiler build/axiomc2.exe
--build-dir build --exclude-requires axiom0-internal -j 2` → exit 0; own 3 ids / 9 results PASS; affected
75 ids / 122 results (121 PASS, 1 SKIP; includes every selfhost group bundle embedding
compiler.types.typeck: mir, interp_opt, own_mir_verify, lir, typeck, traits, drop, backend, driver, opt,
obj_link_driver); smoke 30 ids / 45 results PASS; 0 FAIL.

Acceptance suites (`axtest.py --filter run/ --filter std/ --filter selfhost/mir/ --filter selfhost/interp/
-j 2 --baseline _workspaces/baseline-failures.txt`): TOTAL 3554, PASS 3538, XFAIL 13, FAIL 3. The 3 FAIL
are one XPASS id, `std/num/static_dispatch_xfail.ax` (interp/native/native-O1), whose `xfail: T454` bug was
already fixed at HEAD: the HEAD stage-2 compiler without this change (compiler cache
`axiomc2_O1_fd6482b056a619cc.exe`, sha256 ed9d3d8a…) prints the expected `231`, the older 10:25 cache
build prints `111`. Pre-existing, not caused by T498g (T448 "inference from bounds" is the likely fixer).
`tests/run/interp_big_args` passes in full. WEAK-NATIVE 0 among the new tests (the suite-wide
WEAK-NATIVE 122 count is pre-existing tests without stdout checks).

## Spec deviations
none

## Follow-ups
- Remove the `xfail:` directive from `tests/std/num/static_dispatch_xfail.ax` (it XPASSes at HEAD
  0783fc0, independent of T498g; outside this task's paths) — owner of T454 / architect to file.
- Optional hardening: the MIR builder could reject (ICE) a `TY_VAR` element type for a type-argument
  intrinsic instead of silently sizing it as 1 byte, so a future unresolved substitution fails loudly.

STATUS: COMPLETE round=0
