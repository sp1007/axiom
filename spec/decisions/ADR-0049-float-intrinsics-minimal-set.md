# ADR-0049 — Minimal float intrinsic set; derived float operations are pure Axiom in std.core.float

Status: accepted (2026-11-24, architect; owner-delegated decision). Type B (architecture clarification of SPEC-41 / SPEC-04 §11).

## Tóm tắt
- T458 bị chặn: oracle đã tính được 15 phép float (`sqrt`, `floor`, `fma`, …) nhưng bảng intrinsic trong `types.ax` không có tên
  nào, nên không chương trình nào gọi được; không task nào sở hữu việc đăng ký, và cũng không task nào sở hữu phần hạ mã native
  của chúng (T459 có lệnh LIR `FABS`/`FSQRT` nhưng không có MIR nào sinh ra chúng).
- Rủi ro thật: đăng ký tên mà native chưa hạ mã thì native chạy thân rỗng `{ 0.0 }` và cho kết quả sai âm thầm (bài học T134).
- Quyết định: compiler chỉ biết **5** intrinsic float, mỗi cái cho `f32` và `f64`: `to_bits`, `from_bits`, `sqrt`, `abs`, `copysign`.
  Đăng ký, oracle và native phải có trong cùng một task (T458a); có tên trong bảng nghĩa là chạy được ở cả hai bên.
- 10 phép còn lại (`floor`, `ceil`, `trunc`, `round`, `round_ties_even`, `fma`/`mul_add`, `min`, `max`, `next_up`, `next_down`)
  viết một lần bằng Axiom thuần trong `std/core/float.ax` (T460) trên `to_bits`/`from_bits`: oracle và native chạy cùng một mã,
  không cần SSE4.1/FMA. Nhân soft-float của oracle cho 10 phép này vẫn giữ: T465 (SIMD oracle) dùng và nó là chuẩn đối chiếu.
- `const`/`static` kiểu float, đường dẫn `f64.NAME`/`f64.f(...)` và hằng trong `impl f64 { pub const … }` hiện đều bị từ chối và
  không có chủ: giao T458b. T460 phụ thuộc T458a và T458b.
- T458 giữ phạm vi oracle + optimizer, thu hẹp tiêu chí "intrinsic": kiểm nhân soft-float bằng unit test selfhost được commit.
- Revisit: có, khi T473 (SSE4.1/FMA) xong: có thể thêm intrinsic phần cứng cho `floor`…/`fma` bằng cách nối bảng SPEC-04 §11.

## Context
- SPEC-41 AXS-FLT-014..016, 025, 062 name the operations but not which of them the compiler must know. T458's scope called 12 of
  them "core float intrinsics" evaluated in `compiler/interp`; T457 (typeck) did not register any; T459 lists `SQRTSS`, `MOVD`,
  `ANDPS` at LIR level only.
- `check_intrinsic_item` rejects every unknown `@intrinsic fn` (`AX_TYPE_UNKNOWN_INTRINSIC`). The call is lowered by
  `mb_build_intrinsic_mir_op` (class `INTR_MIR_OP`); an intrinsic of a class the native path does not lower is an ordinary call of
  the declared body, which by convention is a stub.
- On baseline SSE2 there is no `ROUNDSD` and no FMA; a native lowering of rounding and `fma` would be long open-coded sequences or a
  call into a runtime routine, i.e. the same algorithm written a second time (the oracle kernel is the first).
- Probes with the T458 Stage-2 compiler: `const PI: f64 = 3.25` and `const T: [2]f64` give `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`;
  `static S: f32 = 1.5` and `impl f64 { fn m(self: f64) … }` with `x.m()` work; `f64.mk(4)` and `f64.RADIX` give
  `AX_NAME_UNRESOLVED`; `impl i32 { pub const RADIX … }` with `i32.RADIX` gives `AX_TYPE_UNKNOWN_FIELD`. SPEC-41 AXS-FLT-004 needs
  all of them, and T460 (std only) could not have fixed any.

## Options
1. Widen T458: depend on T501, register all 15 names itself. Leaves native lowering unowned (silent wrong native results) and holds
   finished oracle work back behind T501 and T459.
2. New task registers all 15 names and lowers all 15 natively. Two independent implementations of every operation, roughly 1k lines
   of open-coded SSE2/u128 sequences in the backend, for operations that R8 says belong in std.
3. Minimal set (to_bits, from_bits, sqrt, abs, copysign) as intrinsics with oracle + native in one task; the rest is pure Axiom.
4. Only `to_bits`/`from_bits` as intrinsics, everything else (sqrt included) in software: slow `sqrt` for std.math, leaves the
   `SQRTSS`/`ANDPS` selection of AXS-FLT-042 unused.

## Decision
Option 3.
1. **Set.** `to_bits_f32`, `from_bits_f32`, `to_bits_f64`, `from_bits_f64`, `sqrt_*`, `abs_*`, `copysign_*` (AXS-FLT-026; SPEC-04
   AXS-EXT-101). `abs`/`copysign`/`to_bits`/`from_bits` are pure bit operations: they never quiet a signaling NaN and keep payloads.
2. **MIR form.** `to_bits`/`from_bits` = `Cast(FloatBits)` (new `MIR_CAST_*` kind, same-width float <-> unsigned integer only; the
   verifier rejects any other pair); `sqrt` and `abs` = `UnaryOp(Sqrt)` / `UnaryOp(Fabs)` on float operands only (LIR `FSQRT`,
   `FABS` of T459); `copysign` expands to bit casts and integer masks. No checks, never panics.
3. **Invariant `INV-FLT-INTR`.** A name is in the intrinsic table only if both the oracle and the native backend implement it in the
   same commit. There is no oracle-only intrinsic.
4. **Derived operations** (the other 10) are ordinary functions/methods of `std.core.float` (T460), correct for every input
   including subnormals; `mul_add`/`fma` is exact integer soft-float (single rounding), not the Dekker sequence, which fails near
   overflow and underflow. `std.math` (T461) re-exports them.
5. The optimizer treats the new casts and unary ops as opaque, pure, non-foldable (AXS-FLT-014) until a task adds IEEE-exact folding.
6. **T458b** owns float `const` items (scalars, arrays, tuples, structs, impl-level), remaining float `static` shapes, `f32.`/`f64.`
   path heads and inherent associated constants on primitive types, oracle and native.

## Consequences
- T458: unblocked; its intrinsic acceptance is a committed unit test of the kernel in the selfhost interp harness. Its
  `native-after` markers name T458a (which depends on T459 and owns those tests afterwards).
- T458a, T458b: new (P12, axiom-semantics, opus). T460 depends on both; T461 gets them through T460. T312 and T462 depend on them.
- T465 reuses `sf_intrinsic` lane by lane. T480 (f16) used features it did not depend on: it now depends on T458, T458a, T460, T466.
- REQ-SIMD-026/271 stay with T458; REQ-SIMD-272 is mapped to T458 (no implicit contraction) and T460 (explicit single-rounding
  `mul_add`); REQ-SIMD-106 gains T458a. Nothing is dropped.
- Specs amended: SPEC-41 AXS-FLT-026 (new), AXS-FLT-062.1 (fma wording); SPEC-04 AXS-EXT-042, AXS-EXT-101.

Revisit: yes — after T473.

## Sources
`_workspaces/reports/T458-report.md`; SPEC-41 AXS-FLT-004/014/015/016/025/042/060/062; SPEC-04 AXS-EXT-042/100/101; ADR-0002 §1;
ROADMAP R8, R9; T134 (native intrinsic stubs); `compiler/types/types.ax` intrinsic table; function
`mb_build_intrinsic_mir_op` in `compiler/mir/builder.ax`.
