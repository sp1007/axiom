# unblock-T453b — widen paths for 5 selfhost generator-input files asserting legacy axiom0 emit_mc.c bytes

## Tóm tắt
- T453b đã hoàn tất việc hợp nhất bộ mã hoá lệnh cho `inspect --emit=mc` qua `x64_encode_mi_inst` trong `compiler/target/x64/frame.ax`,
  xoá `x64_encode_mi_inst_mc`, cập nhật `tests/mc/frame/main_42.mc` (`48 89 08` -> `89 08`), thêm `tests/mc/emit_mc_parity/`
  (40 hàm, `-O0`/`-O1`), và giữ nguyên điểm bất động stage-2/stage-3 (`FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`).
- `taskgate T453b` chỉ còn lỗi ở 4 bundle selfhost do 5 file template/generator viết tay bên ngoài `paths:` của T453b vẫn ghi cứng
  hoặc trích lại từ blob cache của `axiom0` (`emit_mc.c` C11 đã đóng băng) các byte `--emit=mc` cũ bị sai độ rộng (`48 89 08`
  thay vì `89 08` cho store `i32`) hoặc thiếu `SETcc`/`CMOVcc`/`TEST`/`JMP`/`JCC`/`ASSERT`.
- Quyết định: mở rộng `paths:` của T453b thêm đúng 5 file nguồn đầu vào của bộ sinh selfhost (`qa_frame_layout_and_verify.ax.in`,
  `qa_isel_diff_golden.ax.in`, `harness_backend_diff_mi_mc.ax.in`, `harness_backend_unit.ax.in`, `gen_driver_tests.py`), bổ sung
  mục `## Resume after unblock` hướng dẫn chi tiết cách cập nhật từng file (đặc biệt lưu ý `bundles.py regen` chạy với
  `axiom0=None` trong `snapshot`/`accept`), rồi mở khoá (`taskctl.py unblock T453b`).
- Đã kiểm chứng cả 5 file đều là đầu vào viết tay (không nằm trong `tests/selfhost/generated-files.txt`), không khoá toàn bộ cây
  `tests/selfhost` (`harness_check.py` chấp nhận), và không giao cắt với các task đang chạy (`T422e`, `T423a`). Không cần ADR mới.

## Classification
TYPE A / board scope adjustment: T453b's existing Goal and Scope already require routing `inspect --emit=mc` through the
object-path encoder `x64_encode_mi_inst` (eliminating the legacy port of `axiom0`'s `emit_mc.c`) and updating goldens that
recorded the wrong legacy encoding. No language semantics or compiler architecture rules change, so no ADR or `spec/ROADMAP.md`
amendment is required.

## Decision: how to resolve the 5 selfhost template/generator failures
Options considered:
1. **Widen T453b's `paths:` with the 5 selfhost generator-input files, add `## Resume after unblock` instructions, and `unblock T453b`. (Chosen.)**
2. Split updating the 5 selfhost templates/generators into a separate follow-up task. Rejected: T453b cannot pass its own gate
   until the selfhost bundles regenerated from `compiler/target/x64/frame.ax` agree on `--emit=mc`, so the encoder change and its
   golden/harness updates are a single atomic slice.
3. Keep `inspect --emit=mc` matching `axiom0`'s `emit_mc.c` for those cases. Rejected: `axiom0` (`bootstrap/axiom0`) is frozen
   (ROADMAP R3) and its `emit_mc.c` has the exact width-8 MOV and missing-instruction bugs T453b exists to fix.

Verification and rationale:
- **Not generated bundles:** Verified against `tests/selfhost/generated-files.txt` and `bundles.py list` that none of the 5 files
  (`tests/selfhost/isel/qa_frame_layout_and_verify.ax.in`, `tests/selfhost/isel/qa_isel_diff_golden.ax.in`,
  `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`, `tests/selfhost/backend/harness_backend_unit.ax.in`,
  `tests/selfhost/driver/gen_driver_tests.py`) is a generated output. Individual template/generator paths under
  `tests/selfhost/<area>/...` satisfy `harness_check.py` without locking the whole `tests/selfhost` tree.
- **Disjoint from active tasks:** Verified zero path/lock overlap with `doing` tasks `T422e` and `T423a` (the only other tasks
  naming `tests/selfhost/{isel,backend,driver}` are future Phase P16 tasks `T651`, `T655`, `T662`, `T674`, `T678`, `T682`, `T691`).
- **Snapshot/accept determinism (`axiom0=None`):** Added explicit guidance in `## Resume after unblock` covering each of the 5
  files, including two harness subtleties: (a) `bundles.py regen` runs with `axiom0=None`, so `gen_backend_tests.py` extracts
  cached `axiom0` `exp_mc` blobs from `HEAD`'s bundles (hence `harness_backend_diff_mi_mc.ax.in` and
  `harness_backend_unit.ax.in` must validate unified-encoder MC output directly rather than diffing against `MIMC_DATA`/`UNIT_DATA`
  `exp_mc`), and `gen_driver_tests.py` must override the `--emit=mc` expected blobs (`main_42.ax`, `const.mir`) even when
  `axiom0 is None`; and (b) `session_emit_objmodel_hir` in `compiler/backend/session.ax` emits out-of-line panic blocks whereas
  `driver_emit_build_mi_body_obj` and `x64_emit_mi_body_mc` emit `x64_emit_panic_sequence` inline.

## Board changes
- `T453b`: widened `paths:` with the 5 selfhost generator-input files, aligned `## Scope` and `## Acceptance`, added
  `## Resume after unblock`, and ran `taskctl.py unblock T453b` (`status: todo`, `attempts: 0`, `unblocks: 1`).
- Verification: `taskctl.py validate` (`OK (747 tasks)`), `reqcov.py --strict` (`COVERAGE OK`, 0 gaps), `harness_check.py`
  (`HARNESS OK`).

## Files changed
- _workspaces/tasks/todo/T453b-inspect-emit-mc-uses-object-encoder.md
- _workspaces/reports/unblock-T453b.md
