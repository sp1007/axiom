# T469 Report — E12.4 Canonical SIMD Backend, LIR Vector Lowering & SSE2/AVX2 Encoding Specification (`SPEC-43`)

## Summary

Authored `spec/SPEC-43-simd-backend.md` as the normative SIMD backend, LIR vector lowering/legalization, Windows x64 vector ABI, SSE2/SSE4.1/AVX2/FMA machine-code encoding, native instruction selection, and `std.arch.x86_64` specification for E12.4 (`T469`), and synchronized `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`:

1. **LIR Vector Type System & Register Classes (`AXS-SBE-001`..`AXS-SBE-007`)**:
   - Defined `LirType.v128` (`16` bytes), `LirType.v256` (`32` bytes), and `LirType.v512` (`64` bytes) with auxiliary lane metadata (`LirVecLayout { elem: LirScalarKind, lanes: u8 }`).
   - Added `RegClass.Vec128` (`XMM0`..`XMM15`), `RegClass.Vec256` (`YMM0`..`YMM15`), `RegClass.Vec512` (`ZMM0`..`ZMM31`), and `RegClass.Mask` (`k0`..`k7` or vector mask register).
   - Specified canonical LIR vector opcodes (`VLd`, `VSt`, `VSplat`, `VExtractLane`, `VInsertLane`, `VShuffle`, `VBlend`, `VAdd`/`VSub`/`VMul`/`VDiv`, `VAddSatS`/`VAddSatU`/`VSubSatS`/`VSubSatU`, `VMin`/`VMax`, `VFma`/`VSqrt`/`VAbs`/`VCopysign`/`VRound`, `VAnd`/`VOr`/`VXor`/`VAndNot`/`VNot`, `VShl`/`VShrU`/`VShrS`, `VCmp`, `VMovMask`, `VAllTrue`/`VAnyTrue`, `VReduceAddOrdered`/`VReduceAddFast`/`VReduceMulFast`/`VReduceMin`/`VReduceMax`/`VReduceAnd`/`VReduceOr`/`VReduceXor`, `VCvt`, `VBitcast`, `VLoadMasked`/`VStoreMasked`/`VGather`/`VScatter`, `VPrefetch`, `VZeroUpper`), memory alignment (`align_pow2`), `nontemporal` streaming hints (`MOVNTDQ`/`VMOVNTDQ`/`MOVNTPS`/`MOVNTPD`), and `PREFETCHT0`/`T1`/`T2`/`NTA`.

2. **Vector Legalizer & Reduction Determinism (`AXS-SBE-010`..`AXS-SBE-017`)**:
   - Specified deterministic target-width query (`target_max_vector_bits`: `128` on `x86_64_v1`, `256` on `x86_64_v3` / `+avx2`) and `v256 -> 2 x v128` / `v512 -> 2 x v256 -> 4 x v128` legalizer splitting (`VConcat`/`VExtractHalf`).
   - Preserved bit-exact floating-point reduction trees across `x86_64_v1` and `x86_64_v3`: `VReduceAddOrdered` lowers to strict left-to-right `0..N-1` scalar chain, and `VReduceAddFast`/`VReduceMulFast` lower to canonical pairwise binary-tree halving (`log2(N)` stages).
   - Defined per-lane fault-suppressing expansion for `VLoadMasked`, `VStoreMasked`, `VGather`, and `VScatter` when hardware masked operations are unavailable or unsuitable.

3. **Windows x64 Vector ABI & `VZEROUPPER` Hygiene (`AXS-SBE-020`..`AXS-SBE-023`)**:
   - Specified Windows x64 parameter/return passing for `Vector<T, N>` and `Mask<N>` (`ByRef` pointer in `RCX`/`RDX`/`R8`/`R9` or stack slot; `sret` hidden pointer in `RCX` for vector returns; scalar `XMM0..XMM3` reserved for scalar `f32`/`f64`).
   - Specified `XMM6`..`XMM15` low 128-bit callee-saved preservation (`MOVAPS`/`MOVUPS` at 16-byte-aligned frame slots), volatile `XMM0`..`XMM5` and volatile upper bits `YMM0..YMM15[255:128]`.
   - Specified `VZEROUPPER` emission before every non-AVX ABI call and function return whenever 256-bit `YMM` registers are touched.

4. **SSE2/SSE4.1 (`0F`/`0F 38`/`0F 3A`) & 2/3-Byte `VEX` Encoding (`AXS-SBE-030`..`AXS-SBE-035`)**:
   - Specified legacy SSE2/SSE4.1 prefix + escape byte layout (`66`/`F3`/`F2` + optional `REX` + `0F` / `0F 38` / `0F 3A` + `opcode` + `ModRM` + `SIB` + `disp` + `imm8`).
   - Specified 2-byte `VEX` (`C5 [~R vvvv L pp]`) and 3-byte `VEX` (`C4 [~R ~X ~B mmmmm] [W vvvv L pp]`) bit layouts, shortest-form `C5` selection rule (`X == 1 && B == 1 && W == 0 && mmmmm == 0b00001`), `RSP`/`R12` (`SIB = 0x24`) and `RBP`/`R13` (`disp8 = 0x00`) addressing rules, `VSIB` (`VGATHER*`) encoding, and `.rdata` 16/32-byte aligned constant emission.

5. **Baseline SSE2 (`x86_64_v1`) & Target-Gated AVX2/FMA (`x86_64_v3`) Instruction Selection & `std.arch.x86_64` (`AXS-SBE-040`..`AXS-SBE-052`)**:
   - Provided complete instruction selection tables for SSE2 (`x86_64_v1`), SSE4.1 (`+sse4.1`), and AVX2/FMA (`+avx2,+fma`), including SSE2 fallback sequences for `i8x16`/`i16x8`/`i32x4`/`i64x2` shifts/muls/min/max/blends, software-assisted `f32`/`f64` lane `fma`, `VTESTPS`/`VTESTPD` fast-path mask testing, and fault-safe masked store/scatter lowering.
   - Specified `std.arch.x86_64` types (`__m128`, `__m128d`, `__m128i`, `__m256`, `__m256d`, `__m256i`), intrinsic wrappers, compile-time `@target_feature` / `AX_SIMD_TARGET_FEATURE_REQUIRED` (`AXD-042`) and `AX_UNSAFE_REQUIRED` enforcement, and `cpuid`/`xgetbv`/`has_avx2`/`has_fma` runtime CPU feature detection (`OSXSAVE` + `XCR0[2:1] == 0b11`).

## Files changed

- spec/SPEC-43-simd-backend.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python tools/gatecheck.py --no-run` -> `MS-P1`..`MS-P10b PASS`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T469` -> `0 REFUSED`

STATUS: COMPLETE round=0
