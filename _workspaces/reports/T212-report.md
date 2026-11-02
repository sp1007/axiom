# T212 Report — Plan phase P12: Numeric, floating point & SIMD

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P12 (`P12-numeric-floating-point-simd`) từ 5 epic (`E12.1`–`E12.5`) trong `spec/ROADMAP.md` thành 30 task cụ thể (`T450`–`T479` trong dải `T450`–`T499` của P12, từ 5 đến 7 task mỗi epic), bao gồm các task đặc tả, cài đặt (`typeck` + hạ cấp `MIR_RVALUE_CAST` đồng nhất) và kiểm thử căng thẳng QA cho **`REQ-OWNER-007` (Complex Mixed-Type Expression Matrix — Patterns A, B, C, D)**; chuyển toàn bộ 335 dòng `EPIC(E12.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T450`–`T479`), cập nhật `T312` phụ thuộc vào tất cả task P12, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P12 (`P12-numeric-floating-point-simd`) across all five roadmap epics (`E12.1`–`E12.5`) into 30 concrete, single-sitting tasks (`T450`–`T479` in the `T450`–`T499` P12 block), converted all 335 `EPIC(E12.*)` rows in `spec/requirements/CATALOG.md` (including `REQ-OWNER-007`) to concrete `T450`–`T479` task IDs with matching `covers:` lists, wired `T312` (`depends: [T212, T450..T479]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E12.1 Integer model completion** (6 tasks: `T450`–`T455`):
   - `T450` (`axiom-architect`): Canonical `spec/SPEC-40-integers.md` (`i128`/`u128`, checked/wrapping/saturating/overflowing families, bit ops, conversions `From`/`TryFrom`/`as`/endian bytes, and the pure-integer sub-lattice of `REQ-OWNER-007`; 9 reqs).
   - `T451` (`axiom-semantics`): `TypeKind.Int128` (`i128`/`u128`), `ConstValue.Int128`, `MirBinOp.SatAdd`/`SatSub`/`SatMul`, and pure-integer multi-width promotion lattice (`REQ-OWNER-007` Pattern D) in `typeck` + HIR->MIR `MIR_RVALUE_CAST` lowering (5 reqs).
   - `T452` (`axiom-semantics`): Oracle (`--interp` and const-eval) 128-bit integer evaluator, saturating/bit intrinsics, and `-O1` constant folding (4 reqs).
   - `T453` (`axiom-backend`): LIR `i128` `(lo, hi)` GPR pair lowering, Windows x64 16-byte integer ABI, and x86-64 codegen (`ADC`/`SBB`/`MUL`/`SHLD`/`SHRD`/saturating `CMOVcc`) (3 reqs).
   - `T454` (`axiom-stdlib`): `std.core.num` complete 12-width integer API, `std.core.convert` (`From`/`Into`/`TryFrom`/`TryInto`), endian byte conversions, and `i128`/`u128` formatting/parsing (3 reqs).
   - `T455` (`axiom-qa`): Integer model completion & `REQ-OWNER-007` Pattern D mixed-width conformance suite (3 reqs).
2. **E12.2 Floating-point semantics** (7 tasks: `T456`–`T462`):
   - `T456` (`axiom-architect`): Canonical `spec/SPEC-41-floating-point.md` (`f32`/`f64` IEEE-754 rules, `NaN`, `-0.0`, rounding, saturating `FloatToInt`, full `REQ-OWNER-007` Complex Mixed-Type Expression Matrix promotion lattice & homogeneous `MIR_RVALUE_CAST` rule, Win64 XMM ABI, float fmt/parse, and `std.math` accuracy contract; 9 reqs).
   - `T457` (`axiom-semantics`): Frontend, `typeck`, and HIR->MIR lowering for `f32`/`f64` and the full **`REQ-OWNER-007` Complex Mixed-Type Expression Matrix** (`IntVar`/`FloatVar` + `i8/u8 -> i16/u16 -> i32/u32 -> i64/isize -> f32 -> f64` lowered exclusively to explicit `MIR_RVALUE_CAST` temporaries before homogeneous binary/index/compare MIR ops; 4 reqs).
   - `T458` (`axiom-semantics`): Oracle IEEE-754 floating-point evaluator (`--interp` and const-eval) and strict IEEE-754 `-O1` optimizer preservation (3 reqs).
   - `T459` (`axiom-backend`): LIR `Xmm` register class (`XMM0`–`XMM15`), Windows x64 XMM ABI (`XMM0`–`XMM3` args, `XMM0` return, `XMM6`–`XMM15` callee-save), and SSE2 scalar codegen (2 reqs).
   - `T460` (`axiom-stdlib`): `std.core.float` methods/classification/`total_cmp` and `std.text.fmt.float` shortest round-trip formatting & exact decimal parsing (2 reqs).
   - `T461` (`axiom-stdlib`): Pure-Axiom deterministic `std.math` elementary and transcendental math library (4 reqs).
   - `T462` (`axiom-qa`): Dedicated **`REQ-OWNER-007` Complex Mixed-Type Expression Matrix (Patterns A, B, C, D)** stress-test suite (`tests/run/numeric/mixed_expr_matrix/`) & IEEE-754 differential conformance suite (5 reqs).
3. **E12.3 SIMD & vector types** (6 tasks: `T463`–`T468`):
   - `T463` (`axiom-architect`): Canonical `spec/SPEC-42-simd.md` (`Vector<T, N>`, `Mask<N>`, lane ops, reductions, masked memory/gather/scatter safety, and `TensorView`/`MatrixView` capability model; 22 reqs).
   - `T464` (`axiom-semantics`): `TypeKind.Vector`/`Mask`, `ConstValue.Vector`, and MIR `VectorOp`/`Splat`/`Extract`/`Insert`/`Shuffle`/`Reduce` lowering & verifier rules (25 reqs).
   - `T465` (`axiom-semantics`): Oracle MIR interpreter & const evaluator for `Vector<T, N>` and `Mask<N>` (22 reqs).
   - `T466` (`axiom-stdlib`): `std.simd` portable `Vector<T, N>`, `Mask<N>`, fixed-width aliases, lane ops, reductions, and capability-safe slice/masked/gather/scatter memory API (21 reqs).
   - `T467` (`axiom-stdlib`): Data-oriented `TensorView`/`TensorMutView`, `Vec2..4`/`Mat2..4`, and SIMD slice/matrix kernels in `std/simd/tensor.ax` and `std/simd/matrix.ax` (66 reqs).
   - `T468` (`axiom-qa`): Portable SIMD, mask, gather/scatter & tensor-view conformance suite (9 reqs).
4. **E12.4 SIMD backend** (6 tasks: `T469`–`T474`):
   - `T469` (`axiom-architect`): Canonical `spec/SPEC-43-simd-backend.md` (LIR `v128`/`v256`/`v512` & `Vec128`/`Vec256`/`Mask`, legalizer splitting/scalarization, Win64 vector ABI, `0F38`/`0F3A` & 2/3-byte `VEX` encoding, SSE2/AVX2/FMA isel; 25 reqs).
   - `T470` (`axiom-backend`): LIR vector types (`v128`/`v256`/`v512`), legalizer splitting/scalarization, and Windows x64 vector ABI (11 reqs).
   - `T471` (`axiom-backend`): x86-64 `0F38`/`0F3A` escape opcode maps and 2-byte (`C5`) / 3-byte (`C4`) `VEX` machine encoder (8 reqs).
   - `T472` (`axiom-backend`): x86-64 SSE2 baseline 128-bit vector instruction selection & native lowering (21 reqs).
   - `T473` (`axiom-backend`): x86-64 SSE4.1/AVX2/FMA 256-bit `YMM` instruction selection, `VZEROUPPER` hygiene, and `std.arch.x86_64` intrinsics (8 reqs).
   - `T474` (`axiom-qa`): SIMD backend differential (oracle vs SSE2/AVX2 native) conformance suite (28 reqs).
5. **E12.5 CPU feature detection & function multiversioning** (5 tasks: `T475`–`T479`):
   - `T475` (`axiom-architect`): Canonical `spec/SPEC-44-cpu-features-multiversioning.md` (`TargetDesc` feature DAG, `@target_feature` legality, `CPUID`/`XGETBV` detection, `@multiversion` dispatcher contract; 6 reqs).
   - `T476` (`axiom-semantics`): `TargetDesc` feature hierarchy, `--target-feature` CLI flag, `@target_feature` attribute checking, and call-site legality verifier (4 reqs).
   - `T477` (`axiom-stdlib`): Runtime CPU feature detection (`CPUID`/`XGETBV`) in `std.arch.detect` and `--interp-cpu-features` oracle simulation (2 reqs).
   - `T478` (`axiom-backend`): Function multiversioning (`@multiversion`) clone lowering & runtime/compile-time dispatcher codegen (3 reqs).
   - `T479` (`axiom-qa`): CPU feature detection & function multiversioning conformance suite (3 reqs).

## Files changed
- ./_workspaces/tasks/todo/T212-plan-phase-p12-numeric-floating-point-simd.md
- ./_workspaces/tasks/todo/T312-phase-p12-gate-numeric-floating-point-simd.md
- ./_workspaces/tasks/todo/T450-e12-1-integer-model-conversions-spec.md
- ./_workspaces/tasks/todo/T451-e12-1-typeck-mir-i128-saturating-int-promotion.md
- ./_workspaces/tasks/todo/T452-e12-1-oracle-i128-saturating-const-eval.md
- ./_workspaces/tasks/todo/T453-e12-1-lir-i128-pair-lowering-x64-codegen.md
- ./_workspaces/tasks/todo/T454-e12-1-std-num-complete-integer-api-conversions.md
- ./_workspaces/tasks/todo/T455-e12-1-integer-model-pattern-d-conformance-suite.md
- ./_workspaces/tasks/todo/T456-e12-2-floating-point-mixed-expr-lattice-spec.md
- ./_workspaces/tasks/todo/T457-e12-2-typeck-mir-float-and-req-owner-007-matrix.md
- ./_workspaces/tasks/todo/T458-e12-2-oracle-ieee754-float-eval-strict-opt.md
- ./_workspaces/tasks/todo/T459-e12-2-lir-xmm-win64-abi-sse2-scalar-codegen.md
- ./_workspaces/tasks/todo/T460-e12-2-std-float-methods-formatting-parsing.md
- ./_workspaces/tasks/todo/T461-e12-2-std-math-elementary-transcendental-library.md
- ./_workspaces/tasks/todo/T462-e12-2-req-owner-007-mixed-matrix-float-conformance.md
- ./_workspaces/tasks/todo/T463-e12-3-portable-simd-masks-tensor-views-spec.md
- ./_workspaces/tasks/todo/T464-e12-3-typeck-mir-vector-mask-lowering-verifier.md
- ./_workspaces/tasks/todo/T465-e12-3-oracle-mir-interp-const-eval-simd.md
- ./_workspaces/tasks/todo/T466-e12-3-std-simd-portable-vector-mask-api.md
- ./_workspaces/tasks/todo/T467-e12-3-std-simd-tensor-matrix-views-soa.md
- ./_workspaces/tasks/todo/T468-e12-3-portable-simd-tensor-conformance-suite.md
- ./_workspaces/tasks/todo/T469-e12-4-simd-backend-lir-vex-avx2-spec.md
- ./_workspaces/tasks/todo/T470-e12-4-lir-vector-types-legalizer-win64-abi.md
- ./_workspaces/tasks/todo/T471-e12-4-x64-0f38-0f3a-vex-machine-encoder.md
- ./_workspaces/tasks/todo/T472-e12-4-x64-sse2-baseline-vector-isel-codegen.md
- ./_workspaces/tasks/todo/T473-e12-4-x64-sse41-avx2-fma-isel-std-arch.md
- ./_workspaces/tasks/todo/T474-e12-4-simd-backend-differential-conformance-suite.md
- ./_workspaces/tasks/todo/T475-e12-5-cpu-features-multiversioning-spec.md
- ./_workspaces/tasks/todo/T476-e12-5-target-feature-attribute-call-verifier.md
- ./_workspaces/tasks/todo/T477-e12-5-std-arch-cpuid-xgetbv-runtime-detect.md
- ./_workspaces/tasks/todo/T478-e12-5-multiversion-clone-lowering-dispatcher-codegen.md
- ./_workspaces/tasks/todo/T479-e12-5-cpu-features-multiversioning-conformance-suite.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on all `T450`–`T479` and `T312` task files: `OK` (31 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (301 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 335 `EPIC(E12.*)` rows converted to concrete `T450`–`T479` tasks; `v1-full planned=793`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T212`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
