# T503 report
## Summary
External Windows x64 ABI oracle (ADR-0034 §8 OI-12), all test infrastructure under `tests/ffi/win64_abi_oracle/` plus the `cdriver_abi*.c` cleanup. No compiler/std change was needed: axiomc (snapshot build `build-snap-T503/build/axiomc2.exe`) agrees with gcc on every case. No ABI mismatch was found, so there are no findings and no `xfail`.

- **One table, two renderings** (`abi_table.py`): the scalar signatures, by-value structs and layout structs are rendered into (a) a C file built with `gcc -shared` (the oracle) and (b) a generated Axiom program that links that DLL with `@link("win64_abi_oracle")`. Expected values come from a Python reference (FNV-style mix over raw bit patterns, own LCG so the table does not depend on the Python version) and from gcc; the compiler under test is a third opinion.
- **Scalars:** 64 signatures, 1..8 arguments (per arity: all-int, all-float, int/float alternating from either side, 4 pseudo-random from `i8 u16 i32 u64 f32 f64 *const u8`), edge values (`-128`, `0xFFFF`, `i32::MIN`, `-0.0`, f32/f64 denormals and maxima, kernel-range pointers). Direction Axiom -> C: the DLL returns a hash of the raw argument bits and Axiom compares it with the Python constant. Direction C -> Axiom: for each signature the DLL calls an Axiom `extern "C" fn` callback with the same arguments; the callback compares every argument bit-exactly and returns `MAGIC ^ mismatch_mask`. Returns of all 7 types: C returns table values (`rt_<ty>`), echo (`ec_<ty>`), and C calls an Axiom callback that returns each type (`cr_<ty>`, hash of the returned bits; checks upper-bit-garbage tolerance of the i8/u16 returns).
- **Structs by value:** 20 `@repr(C)` structs, sizes 1,2,3,4,5,6,7,8,8,8,8,12,12,12,16,16,16,24,24,24 (includes padded `{u8,u32}`, `{u8,u32,u8}`, `{u8,f64,u16}`, float-only `{f32,f32}`, `{f64}`, `{f64,f64}`, `{f32,f32,f32}`, `{i32,f32,u64,f64}`). Per struct: parameter (`si_`), return with hidden-pointer argument shifting and extra scalar args whose hash the DLL stores for `sg_last()` (`so_`), callback taking the struct (`sc_in_`), callback returning the struct (`sc_out_`), the struct in positions 2 and 5 between `i8/f64/u16/f32` scalars (`sm_`), and the same as a callback (`sm_cb_`). In total 383 checks, run at Axiom `-O0` and `-O1` against a DLL built with gcc `-O0` / `-O2`.
- **Layout:** gcc prints `sizeof/_Alignof/offsetof` of 32 structs (scalar widths, padding, bool, usize, pointers, `[N]T` arrays, nested structs, plus every by-value ABI struct); the table is first cross-checked against an independent Python C-layout algorithm, then compared with `size_of`/`align_of`/address-difference offsets of the same `@repr(C)` structs in Axiom (163 checks, -O0 and -O1).
- **Negative control** (`win64_abi_control.test`): the same pipeline with corrupted expectations (`sc_5_3` hash in the DLL, the expected magic of callback `cs_4_2`, `si_A12` in the DLL, and the expected `sizeof(L_arr)`) must be reported as `FAIL ...` with a non-zero exit by the native executables, at both opt levels. This is the native-evidence proof for the task's own tests.
- **`assert` removal:** `tests/mc/isel/cdriver_abi{,_edge,_qa,_qa2}.c` now use an explicit `CHECK(cond)` macro (`if (!(cond)) { fprintf(stderr, ...); return 1; }`) instead of `assert(...)`; `#undef NDEBUG` / `#include <assert.h>` are gone and `grep -c assert` is 0 in each file. They compile warning-free with `-DNDEBUG -O2 -Wall -Wextra -Werror` and still pass (the exec manifests are unchanged).

## Design choices
- The oracle is a generated pair, not hand-written C + Axiom, so that 64 signatures x 2 directions cannot drift apart; `python tests/ffi/win64_abi_oracle/win64_abi_oracle.py <calls|layout|control> <compiler> <root> <tmp> --emit-dir D` dumps the generated `.c`/`.ax` for inspection.
- Manifests use `cmd:` + `nocache:` like `tests/abi/win64_float/xmm_interop.test` (they build a DLL and executables in `{tmp}`); a missing gcc is a hard failure (ADR-0034 §7), there is no `skip-unless`. The DLL is built with `-Wall -Werror`.
- The native legs compare observable results (hash/bit equality, exit code 1 on any mismatch and `FAIL <name>` lines, exact final stdout line `WIN64-ABI-CALLS ok <n> checks`). The run is native-only (direct FFI, ADR-0002), so no interp leg exists.
- Structs are move-only in Axiom, so the generated code creates a fresh value per use; struct literals are bound with `let` before use in `if` conditions (a struct literal in an `if` condition does not parse).
- `f32`/`f64` bit patterns use the `to_bits_*`/`from_bits_*` intrinsics declared in the generated program (the `x.to_bits()` method form is not in scope without imports).

## Evidence (snapshot `build-snap-T503`, compiler `build/axiomc2.exe` built from the snapshot sources)
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build -j 2 --filter ffi/win64_abi_oracle --filter mc/isel/cdriver_abi` -> `WEAK-NATIVE 0`, `TOTAL 7 PASS 7 FAIL 0 SKIP 0 XFAIL 0` (3 oracle manifests + 4 cdriver manifests).
- Mutation spot-proof in the snapshot only: changing `sig_hash`'s expected value in `build-snap-T503/tests/ffi/win64_abi_oracle/abi_table.py` (`return h ^ 1`) made `win64_abi_calls.test` FAIL (exit 1); restored, it PASSes again.
- `python tools/archcheck.py` (snapshot) -> 0 violations.
- Not run by the engineer: `taskgate` (QA gate).

## Not done / notes
- Varargs, `extern "system"` callbacks and XMM6..XMM15 preservation are out of this task (the latter is covered by `tests/abi/win64_float`, T459).
- `address_of(s.field)` offsets cover top-level fields only; nested struct/array fields are compared as whole fields.

## Round 1 (fix of QA finding F1)
- Added `pool ffi: ffi/win64_abi_oracle/win64_layout_offsetof.test` to `tests/smoke.list` (task now locks that file), so `axtest.py --smoke --check` accepts the new `tests/ffi` group. QA's two added files (`qa_abi_nonvolatile.py/.test`) are listed below.

## Files changed
- tests/ffi/win64_abi_oracle/abi_table.py
- tests/ffi/win64_abi_oracle/win64_abi_oracle.py
- tests/ffi/win64_abi_oracle/win64_abi_calls.test
- tests/ffi/win64_abi_oracle/win64_layout_offsetof.test
- tests/ffi/win64_abi_oracle/win64_abi_control.test
- tests/mc/isel/cdriver_abi.c
- tests/mc/isel/cdriver_abi_edge.c
- tests/mc/isel/cdriver_abi_qa.c
- tests/mc/isel/cdriver_abi_qa2.c
- tests/smoke.list
- tests/ffi/win64_abi_oracle/qa_abi_nonvolatile.py
- tests/ffi/win64_abi_oracle/qa_abi_nonvolatile.test

STATUS: COMPLETE round=1
