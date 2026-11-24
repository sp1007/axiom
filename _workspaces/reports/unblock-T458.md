# Unblock T458 — float intrinsics reachable from source

## Tóm tắt
- T458 xong phần oracle và optimizer, nhưng tiêu chí "float intrinsics chạy dưới `--interp`" không đạt được vì bảng intrinsic trong
  `compiler/types` không có tên float; không task nào sở hữu việc đăng ký, cũng không task nào sở hữu hạ mã native cho chúng
  (T459 chỉ có lệnh LIR `FABS`/`FSQRT`, không MIR nào sinh ra).
- Kiểm tra thêm bằng compiler Stage-2 của T458: `const PI: f64` bị `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`; `f64.mk(4)`, `f64.RADIX` bị
  `AX_NAME_UNRESOLVED`; hằng trong `impl i32 { pub const … }` bị `AX_TYPE_UNKNOWN_FIELD`. T460 (chỉ sửa std) sẽ bị chặn vì các lỗi này.
- Quyết định (ADR-0049): compiler chỉ biết 5 intrinsic float (`to_bits`, `from_bits`, `sqrt`, `abs`, `copysign`), đăng ký + oracle +
  native trong cùng task T458a; 10 phép còn lại viết bằng Axiom thuần ở T460; hằng/static float và `f64.NAME` là T458b.
- T458 được gỡ chặn ngay, không phải chờ T501: tiêu chí intrinsic thu hẹp thành unit test của nhân soft-float (commit vào harness
  selfhost/interp), và đổi dấu `native-after` sang T458a. Không yêu cầu nào bị bỏ (REQ-SIMD-026/271/272 giữ nguyên ở T458;
  REQ-SIMD-272 thêm T460, REQ-SIMD-106 thêm T458a).

## Options
1. T458 waits for T501 and registers the names itself: holds finished work back and leaves native lowering unowned, so a native
   program would run the declared stub body (silent wrong result). Rejected.
2. One follow-up that registers and natively lowers all 15 operations: duplicates every algorithm in the backend (no ROUND/FMA on
   baseline SSE2), against R8. Rejected.
3. Minimal intrinsic set with oracle and native together (T458a), derived operations in std (T460), float consts and path heads
   (T458b), T458 narrowed explicitly. **Chosen.**

## Decision
- **T458** (todo, unblocked): keeps paths; gains lock `tests/selfhost/interp`. Remaining work only: committed kernel unit test
  (15 kinds x f32/f64), retarget `native-after: T459` to `T458a` in its six run tests, header text of the helper
  `tests/mir/float_interp/intrinsics.ax`, refreshed report. The source changes in the main tree stay as they are.
- **T458a** (new, semantics, opus; depends T458, T459, T501): the five intrinsics end to end, plus native catch-up of T458's tests.
- **T458b** (new, semantics, opus; depends T458, T459, T501): float `const`/`static`, `f32.`/`f64.` path heads, associated constants.
- **T460** depends += T458a, T458b; scope gains the derived operations and REQ-SIMD-272. **T461** (depends T460) is correct through
  the closure; its elementary operations become re-exports. **T462**, **T312** depend += T458a, T458b.
- **T480** (found while checking the dependants): used the float oracle, bit intrinsics, `std.core.float` and `std.simd` without
  depending on them and locked a path that does not exist; depends and locks corrected, f16 std members moved there from T460.
- **T459**: no change needed; it does not own intrinsic lowering. It is not asked to remove markers in T458's files.
- Float const folding (T458 report decision 2) accepted: no folding until an IEEE-exact folder exists. Fresh-NaN decision 1 accepted
  (SPEC-41 AXS-FLT-002).

## Risk
- T458a, T458b, T464, T480, T551 and others all hold `compiler/types`, so the scheduler runs them one at a time.
- If T459 changes its float vreg representation in a fix round, T458a adapts `FloatBits` to it (it depends on T459).

## Checks
- `taskctl.py lint` (both new tasks) OK; `taskctl.py validate` OK (753 tasks); `harness_check.py` OK; `reqcov.py --strict` gaps 0.

## Files changed
- _workspaces/tasks/doing/T458-e12-2-oracle-ieee754-float-eval-strict-opt.md
- _workspaces/tasks/todo/T458-e12-2-oracle-ieee754-float-eval-strict-opt.md
- _workspaces/tasks/todo/T458a-e12-2-float-intrinsics-registration-native-lowering.md
- _workspaces/tasks/todo/T458b-e12-2-float-const-static-items-primitive-assoc-consts.md
- _workspaces/tasks/todo/T460-e12-2-std-float-methods-formatting-parsing.md
- _workspaces/tasks/todo/T461-e12-2-std-math-elementary-transcendental-library.md
- _workspaces/tasks/todo/T462-e12-2-req-owner-007-mixed-matrix-float-conformance.md
- _workspaces/tasks/todo/T480-e12-2-f16-bf16-scalar-storage-simd-spec-and-lowering.md
- _workspaces/tasks/todo/T312-phase-p12-gate-numeric-floating-point-simd.md
- spec/decisions/ADR-0049-float-intrinsics-minimal-set.md
- spec/SPEC-41-floating-point.md
- spec/SPEC-04-core-extensibility.md
- spec/INDEX.md
- spec/ROADMAP.md
- spec/requirements/CATALOG.md
- _workspaces/reports/unblock-T458.md
