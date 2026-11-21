# p0-slice-iter-move — stale `ui/slice/iter_move*.ax` after T498

## Tóm tắt
- Hai test `tests/ui/slice/iter_move.ax` và `tests/ui/slice/qa_slice_iter_move.ax` hỏng từ commit T498 (9f31ed56), qua ở 37a299d8 (bằng chứng: `_workspaces/reports/T499a-qa.md`, mục "Regression check").
- Nguyên nhân: theo ADR-0044 §3 / SPEC-10 AXS-OWN-003, mảng `[N]T` với `T` Copy là Copy, nên `consume(arr)` sao chép thay vì move; owner vẫn sống, view không còn vượt quá owner → không báo `AX_CAP_OUTLIVES_OWNER` là ĐÚNG.
- Kết luận: kỳ vọng của test đã cũ, không phải lỗi compiler. Không nới kiểm tra capability.
- Tạo task T498d (P12, owner axiom-qa, reviewer axiom-architect, model sonnet, priority 0, không phụ thuộc — chạy ngay): sửa hai test để move một mảng phần tử không Copy (giữ `AX_CAP_OUTLIVES_OWNER`, AXS-CAP-004), thêm test chạy dương tính cho trường hợp mảng Copy.
- SPEC-10 AXS-OWN-003: bỏ ghi chú cũ "xfail until T498", thêm hệ quả cho test AXS-CAP-004.
- Ghi một dòng nhật ký thay đổi ROADMAP. Phạm vi phase không đổi.

## Classification
TYPE A (test maintenance) following an already-decided TYPE C change (ADR-0044 §3). No new ADR needed.

## Decision
- Options: (a) mark the tests xfail / add to baseline — rejected, it hides the AXS-CAP-004 check; (b) make the compiler
  report the error for Copy arrays — rejected, contradicts ADR-0044 §3 (the owner is not invalidated); (c) rewrite the tests
  to move a non-Copy owner and add a positive Copy-array test — chosen.
- Id: `new-id --phase P12` reported no free id in T450–T499; suffix id of the culprit task T498 (T498a–c taken) → T498d.
- `depends: []`, priority 0 so the scheduler picks it next. `paths:` are the two ui tests and the new
  `tests/run/slice/copy_array_owner_view.ax`; no locks.
- Not added to `_workspaces/baseline-failures.txt` (task should land before the next gate; the board change is the record).

## Checks
- `taskctl.py lint` on the new file: OK. `taskctl.py validate`: OK (732 tasks). `harness_check.py`: HARNESS OK.
  `reqcov.py --strict`: COVERAGE OK (gaps 0).

## Files changed
- _workspaces/tasks/todo/T498d-fix-stale-slice-iter-move-tests-copy-array.md
- spec/SPEC-10-ownership.md
- spec/ROADMAP.md
- _workspaces/reports/p0-slice-iter-move.md
