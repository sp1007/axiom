# Unblock T153 — Port trait items parity in the build path

## Tóm tắt
- T153 bị chặn vì phần hằng liên kết (`Type.CONST`) của `tests/run/trait2/test_assoc_items.ax` cần sửa
  `compiler/mir/builder.ax` (tràn stack trong `mb_build_expr_as_operand`), file này nằm ngoài `paths:`.
- Quyết định: thêm `compiler/mir/builder.ax` vào `paths:` của T153. Không task todo/doing nào khác
  đang giữ file này cùng lúc (T156 phụ thuộc T153; T058/T089 sau self-host). Bản vá đã kiểm chứng trong
  snapshot (nằm trong báo cáo T153) được áp dụng ở lượt tiếp theo; phần việc đã làm trong cây làm việc
  được giữ nguyên.
- Lỗi ngữ nghĩa riêng: phương thức mặc định của trait chỉ được biên dịch một lần, nên lời gọi
  `self.base()` trong thân mặc định luôn gắn với impl đầu tiên (axiom0, port và interpreter cùng sai,
  nên kiểm thử parity không thấy). Tạo task mới T161 (AX0-FIX-09) sửa đồng bộ axiom0 + port, phụ thuộc
  T153; T086 phụ thuộc T161. Không cần ADR: đây là sửa lỗi theo yêu cầu sẵn có (REQ-TRT-005/011).
- Đã chạy `taskctl unblock T153`, `validate` (240 task OK), `harness_check` OK, `reqcov --strict` OK.

## Decision
Classification: TYPE A (ownership of a file for an implementation fix) + a follow-up for a semantic bug
against existing requirements (no semantic change, so no ADR).

Options considered for the builder.ax blocker:
1. **Add `compiler/mir/builder.ax` to T153 `paths:`** — chosen. The patch is ~30 lines, mirrors
   axiom0's `mir/build/builder.c` operand-of-FIELD branch, and is already verified in the snapshot.
   Conflict check: among todo/doing tasks only T058, T089 (post-self-host, depend on T214/T211) and
   T156 (depends on T153) list `compiler/mir`; none can run concurrently with T153.
2. Lock instead of path — rejected: no other task needs the file in this window; a single owner is
   simpler.
3. Separate tiny prerequisite task — rejected: the fix is needed to make T153's own acceptance
   (`test_assoc_items` out of the registry) true, and the bundle regeneration would have to be done
   twice.

Options for the default-method-per-type defect:
1. **New P10 lockstep task T161 (AX0-FIX-09)** before T086 — chosen. The behaviour violates v1-core
   REQ-TRT-005/011 (0133 §8, §9, §14); ROADMAP R3/ADR-0034 §2 require axiom0 fixes before the freeze
   after T087, in lockstep with the port.
2. Widen T153 — rejected: T153 is a parity task (port = axiom0); changing axiom0 semantics there
   would mix scopes and exceed one sitting.
3. Defer past self-host — rejected: axiom0 freezes after T087; the bug would then need a fix in two
   compilers diverging from each other.

No existing task covered it (searched board for default-method per type; T056/T151 are done and do
not).

## Board changes
- T153: `paths:` += `compiler/mir/builder.ax`; Out of scope names T161; "Unblock" section with the
  remaining steps (apply patch, regenerate bundles, drop `test_assoc_items` from
  `known_divergent.txt`, finish the full suite in `build-snap-T153`); `taskctl unblock T153`.
- T161 created (owner axiom-semantics, model/gate opus, depends T153, covers REQ-TRT-005,
  REQ-TRT-011).
- T086: depends += T161.
- ROADMAP change log row 2026-10-30.

## Files changed
- _workspaces/tasks/todo/T153-port-trait-methods-build-path-parity.md
- _workspaces/tasks/todo/T161-ax0-fix-09-default-method-per-implementing-type.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- spec/ROADMAP.md
- _workspaces/reports/unblock-T153.md
