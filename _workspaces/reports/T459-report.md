# T459 report
## Summary
Native scalar `f32`/`f64`: LIR float instructions, the Xmm register class in the register allocator, the Windows x64 XMM calling convention, and SSE2 selection and encoding (SPEC-41 AXS-FLT-040..044). No earlier report or partial edits existed, so this was written from scratch on HEAD 8c47176b. Before this task, float operations compiled to integer instructions (a float `/` became `idiv`).

- **LIR** (`compiler/lir/lir.ax`, `mod.ax`, `builder.ax`): `fadd fsub fmul fdiv frem fcmp.{eq,ne,lt,le,gt,ge} fneg fabs fsqrt fpext fptrunc sitofp uitofp fptosi fptoui`, all shown by `--emit=lir`. The builder lowers float binary/unary rvalues and the casts FloatToInt, IntToFloat and FloatConvert.
- **ABI** (`compiler/abi/win64.ax`, `mod.ax`): positional XMM0..XMM3 arguments, 8-byte stack slots, XMM0 returns, XMM volatile/non-volatile masks as ABI data.
- **Register class** (`isel.ax`, `frame.ax`): `f32`/`f64` vregs are `REG_CLASS_XMM`. At -O1 the allocator really uses XMM6..XMM10 for `tests/abi/win64_float/xmm_interop.ax`, with MOVAPS saves and restores in 16-byte aligned slots. At -O0 float vregs live in slots.
- **isel** (`isel.ax`): operands are moved into scratch XMM0..XMM3, computed register-register and moved back, so a float vreg's frame operand only appears in 8-byte MOVs. Comparisons follow AXS-FLT-043. Saturating float-to-int and u64-to-float are branch-free. 128-bit conversions are MI pseudo-ops (`u128tof`, `f2i128`) expanded at encode time.
- **Machine IR** (`frame.ax`): MOV handles XMM operands (MOVSS/MOVSD/MOVD/MOVQ/MOVAPS); physical def/use masks and EFLAGS effects for the new opcodes; argument, return and call liveness includes XMM0..XMM3 and XMM0; XMM constants are never rematerialised; a new verifier error rejects illegal XMM operand forms.
- **Encoder** (`encode.ax`): SSE2 scalar forms and the x87 forms used by `%`.

### Bug found by the tests
The first build encoded every f32 operation as `sd`: `compiler/driver/pipeline.ax` (outside `paths:`) overwrites `inst.size` with 8 for every opcode except MOV, CMP and a few atomics, on the build path only, so `inspect` output looked right. The encoder now uses `inst.sz`, which the driver leaves alone. See Follow-ups.

## Not done, or different from the task text
1. **`.rdata` float constants: not implemented.** The scope bullet asks for 4- and 8-byte `.rdata` constants. Constants and sign masks go through `MOV r64, imm64` + `MOVD`/`MOVQ` instead, which AXS-FLT-040 rule 3 allows. There are no `.LC_f32_*`/`.LC_f64_*` symbols. If the architect wants `.rdata`, it needs RIP-relative MOV relocations through `session.ax` and `compiler/driver/pipeline.ax`.
2. **Variadic `extern "C"` mirroring: implemented but unreachable and untested.** The language has no variadic declarations, so nothing calls `win64_classify_ex(.., variadic = true)`, and no test covers it or the isel branch for `ABI_LOC_REG_MIRROR`. The f32-to-f64 promotion of variadic arguments is not implemented.
3. **`fsqrt` and `fabs`: no MIR producer.** LIR, isel and encoders exist; only the encoders are tested. `to_bits`/`from_bits` have no surface either; MOVD/MOVQ are tested as encodings and used in generated code.
4. **No interp/native differential.** The interpreter has no floats until T458, so the float programs are exec manifests checked against a Python IEEE-754 oracle and gcc, not `test: run` in both modes.
5. **Helpers inlined.** `%` uses x87 FPREM in place instead of `__axiom_fmod(f)` (exact for both widths). `__axiom_{i,u}128_to_f{32,64}` are inline expansions too.
6. **No SEH metadata** for the XMM saves: the compiler emits no unwind tables at all.
7. `REG_CLASS_XMM` is used through the existing TypeId classification; there is no `LirType` enum in this code base.

## Files changed
- compiler/abi/mod.ax
- compiler/abi/win64.ax
- compiler/lir/builder.ax
- compiler/lir/lir.ax
- compiler/lir/mod.ax
- compiler/target/x64/encode.ax
- compiler/target/x64/frame.ax
- compiler/target/x64/isel.ax
- tests/abi/win64_float/abi_calls.ax
- tests/abi/win64_float/abi_calls.txt
- tests/abi/win64_float/gen_expected.py
- tests/abi/win64_float/native_abi_calls.test
- tests/abi/win64_float/run_native.py
- tests/abi/win64_float/xmm_interop.ax
- tests/abi/win64_float/xmm_interop.test
- tests/abi/win64_float/xmm_interop_host.c
- tests/abi/win64_float/xmm_interop_oracle.py
- tests/encode/axiom/gnu_as_vectors.ax
- tests/encode/sse2_scalar/coff_stub.ax.in
- tests/encode/sse2_scalar/encode_sse2.py
- tests/encode/sse2_scalar/encode_sse2.test
- tests/lir/float/arith_f32.ax
- tests/lir/float/arith_f32.txt
- tests/lir/float/arith_f64.ax
- tests/lir/float/arith_f64.txt
- tests/lir/float/compare.ax
- tests/lir/float/compare.txt
- tests/lir/float/float_ops_lir.ax
- tests/lir/float/float_ops_lir.test
- tests/lir/float/float_ops_mi.test
- tests/lir/float/float_to_int.ax
- tests/lir/float/float_to_int.txt
- tests/lir/float/gen_float_cases.py
- tests/lir/float/int_to_float.ax
- tests/lir/float/int_to_float.txt
- tests/lir/float/native_arith_f32.test
- tests/lir/float/native_arith_f64.test
- tests/lir/float/native_compare.test
- tests/lir/float/native_float_to_int.test
- tests/lir/float/native_int_to_float.test
- tests/lir/float/native_neg_convert.test
- tests/lir/float/neg_convert.ax
- tests/lir/float/neg_convert.txt
- tests/lir/float/run_native.py
- tests/smoke.list

## Tests
Verified in `build-snap-T459/` refreshed on HEAD `e6c2851fec33` (46 changed files, 36 generators / 60 bundle files regenerated):

1. **Stage-2/3 fixed-point build** (`python tools/build_axiomc.py --out build --root . --stage 2`):
   - `STAGE1 OK`: `axiomc1.exe` (`33934848 bytes`, `sha256=f9d3eb6893567f1f`, `wall=106.39s`)
   - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == d66caa3db8805c69aa63549ece758627f92bade49b4d9d14c35033b230780e27` (`9076736 bytes`, `[seeded B==C]`)
   - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (O1, incl. Xin chào thế giới)
2. **Targeted tests** (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --verbose --filter lir/float --filter encode/sse2_scalar --filter abi/win64_float --filter encode/axiom/gnu_as_vectors`):
   - `TOTAL 14 PASS 14 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
   - All 14 results passed: `abi/win64_float/{native_abi_calls,xmm_interop}.test`, `encode/axiom/gnu_as_vectors.ax [interp, native, native-O1]`, `encode/sse2_scalar/encode_sse2.test`, `lir/float/{float_ops_lir,float_ops_mi,native_arith_f32,native_arith_f64,native_compare,native_float_to_int,native_int_to_float,native_neg_convert}.test`.
3. **Live mutation spot-proof** (inside `build-snap-T459/` only):
   - Mutated line 0 of `tests/abi/win64_float/abi_calls.txt` (`4659299957151367168` -> `MUTATED_EXPECTED_OUTPUT`): `abi/win64_float/native_abi_calls.test` failed (`TOTAL 1 PASS 0 FAIL 1`, exit 1).
   - Restored byte-identical (SHA256 `40A1E36A2852F5874B28EA88BC41D3A7BC35A90949B8E6AE690D0641B4D87645`): `abi/win64_float/native_abi_calls.test` passed (`TOTAL 1 PASS 1 FAIL 0`, exit 0).
4. **Task gate** (`python tools/taskgate.py --task T459 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
   - `TASKGATE T459 exit=0` (`wall 727.0 s`, `axtest 715.8 s`)
   - `axtest`: `TOTAL 289 PASS 277 FAIL 0 SKIP 12 XFAIL 0` (`own`: 14/14 PASS; `affected`: 228/240 PASS, 12 SKIP; `smoke`: 55/55 PASS; `CACHED 88`, verification sample `n=20 of 67 hits`, `mismatch none`)
   - `WEAK-NATIVE`: `3 in the run; 0 in the task's own/changed tests`
   - `Baseline`: `BASELINE OK`, `Failing ids: none`
   - `archcheck`: `clean (exit 0)` (`232 files scanned, 0 violations`)
   - `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 23 s` (added `pool abi: abi/win64_float/native_abi_calls.test`)

## Follow-ups
- `compiler/driver/pipeline.ax` (lines 4505 and 7840): stop normalising `inst.size` for opcodes it does not know; then the float encoder can use `size` again.
- Native lowering of float intrinsics (`sqrt`, `abs`, `to_bits`, `from_bits`, ...) once T458/T460 define their MIR form; the LIR kinds are ready.
- Turn the native cases into `test: run` in both modes after T458.
- isel always copies through XMM0/XMM1; two-address selection on allocated XMM registers would remove most of those moves.

STATUS: COMPLETE round=0
