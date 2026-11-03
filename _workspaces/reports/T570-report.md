# T570 Report — E14.5 Finalize SPEC-03 AXS-SEM-047 index auto-deref through view/mut_view

## Tóm tắt
Hoàn thành task `T570` (`E14.5` — hoàn thiện đặc tả `SPEC-03 AXS-SEM-047` cho tự động giải tham chiếu khi đánh chỉ số qua `view<[N]T>` và `mut_view<[N]T>`):
- Cập nhật `spec/SPEC-03-core-semantics.md`: gỡ bỏ ghi chú tạm hoãn thời bootstrap v0.1 trong `AXS-SEM-047`, kích hoạt quy tắc giải tham chiếu ẩn từng mức (`a[i]` → `(*a)[i]`, và lồng nhau `(**a)[i]`) trong `axiomc` (`E14.5`: `T570`–`T572`), trong khi giữ `bootstrap/axiom0` đóng băng tại `axiom0-frozen` theo `ROADMAP R3`.
- Chốt rõ sự phối hợp giữa `AXS-SEM-047` (đọc qua `view`/`mut_view`; ghi `a[i] = v`, `a[i] op= v` và lấy `mut_view(a[i])` đòi hỏi mọi tầng view đi qua đều là `mut_view`, nếu gặp `view` bất biến thì báo `AX_TYPE_ASSIGN_IMMUTABLE`), `AXS-SEM-042` (thứ tự đánh giá trái sang phải từ base tới chỉ số + kiểm tra biên `0 <= i < N`), `AXS-SEM-043` / `SPEC-12 AXS-DROP-007` (gán `a[i] = v` qua `mut_view<[N]T>` giải phóng giá trị phần tử cũ trước khi ghi giá trị mới), và quy tắc cấm tự giải tham chiếu con trỏ thô (`p[i]` trên `*const [N]T`, `*mut [N]T`, `*const T`, `*mut T` luôn báo `AX_TYPE_CANNOT_INDEX`; `(*p)[i]` trong `unsafe` là tường minh và khi gán là raw store không drop).
- Bổ sung truy vết đầy đủ cho `REQ-CORE-3053..3055` (`tasks/0539 §89 AMIR-83..85`) cùng `REQ-CORE-3056..3060` (`AMIR-86..90`), thêm các hàng kiểm thử chuẩn tắc `SEM-T20`–`SEM-T24` và ví dụ `SEM-T25` trong `SPEC-03` §10, đồng thời cập nhật `spec/diagnostics.md` (§11) và `spec/invariants.md` (`INV-PIPE-001..003`, `INV-SEM-007`).

## Summary of Deliverables
1. **`spec/SPEC-03-core-semantics.md`**:
   - **`AXS-SEM-001`**: Recorded the target-independent MIR boundary contract (`tasks/0539 §89 AMIR-80..85, AMIR-90`; `REQ-CORE-3050..3055, REQ-CORE-3060`): MIR does not determine physical storage strategy, stack-vs-heap placement, general register allocation, or vector register usage.
   - **`AXS-SEM-042` & `AXS-SEM-043`**: Clarified left-to-right evaluation across implicit view dereferences and multidimensional indexing, and explicitly listed `a[i]` on `mut_view<[N]T>` among places that drop their old element value vs explicit `(*p)[i]` inside `unsafe` as a raw store.
   - **`AXS-SEM-047`**: Removed the temporary bootstrap v0.1 deferral note and finalized one-level-at-a-time index auto-deref through `view<X>` and `mut_view<X>` resolving to `[N]T` or `[T]`, specifying mutability enforcement (`AX_TYPE_ASSIGN_IMMUTABLE`), `THIR`-to-MIR `PlaceElem.Deref` lowering without rediscovering source semantics (`AMIR-86..87`, `REQ-CORE-3056..3057`), old-element `Drop` and MIR verifier checking (`AMIR-88..90`, `REQ-CORE-3058..3060`), and raw-pointer index rejection (`AX_TYPE_CANNOT_INDEX`).
   - **§10 Normative test cases (`SEM-T20`–`SEM-T25`)**: Added normative table rows for reading through `view<[N]T>` (`SEM-T20`), writing and compound-assigning through `mut_view<[N]T>` (`SEM-T21`), bounds-check panic through `view<[N]T>` (`SEM-T22`), rejected write through `view<[N]T>` (`SEM-T23`, `AX_TYPE_ASSIGN_IMMUTABLE`), rejected `p[i]` on raw pointer `*mut [N]T` (`SEM-T24`, `AX_TYPE_CANNOT_INDEX`), and multi-line element-drop verification on `mut_view<[2]Tracked>` (`SEM-T25`).
2. **`spec/diagnostics.md` & `spec/invariants.md`**:
   - Updated `AX_TYPE_ASSIGN_IMMUTABLE` and documented `AX_TYPE_CANNOT_INDEX` in `spec/diagnostics.md` §11 (`T030/T036/T571`, `SPEC-03 AXS-SEM-042/043/047`).
   - Updated `INV-PIPE-001`..`INV-PIPE-003` with `tasks/0539 §89 AMIR-81..90` (`REQ-CORE-3051..3060`) and added `INV-SEM-007` (`since: T572`) in `spec/invariants.md` §8.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS
- `python tools/gatecheck.py --no-run`: PASS
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T570`: PASS (`0 REFUSED`)

STATUS: COMPLETE

## Files changed
- spec/SPEC-03-core-semantics.md
- spec/diagnostics.md
- spec/invariants.md
