# ADR-0050 — Address-observable locals of an `async fn` live in place in the state machine

Status: accepted (2026-11-25, architect; owner-delegated decision). Type B (architecture clarification of SPEC-33
AXS-ASY-005 / AXS-ASY-043 so that SPEC-35 AXS-AIO-012 item 2 holds). Implementation: T428a.

## Tóm tắt
- T428 phát hiện (F1): con trỏ thô lấy từ một biến cục bộ của `async fn` (`address_of_mut(buf[0])`, hoặc con trỏ mà
  `read_exact`/`write_all` giữ tới một stream cục bộ) không còn đúng sau `.await`. Oracle báo "dangling pointer", native
  in sai kết quả (`3000` thay vì `3084`) vì dữ liệu được chép vào bản sao cũ của biến.
- Nguyên nhân: `async_lower.ax` lưu biến sống qua `.await` vào trạng thái (`(*self).live_v`) rồi chép ngược ra slot của
  khung `poll` khi tiếp tục; địa chỉ của biến vì thế thay đổi giữa hai lần poll. SPEC-33 AXS-ASY-005 mục 3 cấm điều này
  khi địa chỉ đã bị quan sát; SPEC-35 AXS-AIO-012 mục 2 cho phép đúng mẫu `read(dst_ptr)` vào bộ đệm cục bộ.
- Quyết định: biến cục bộ **có địa chỉ bị quan sát** (lấy `address_of`/`address_of_mut`, hoặc mượn `view`/`mut_view`
  rồi chuyển thành con trỏ thô trong cùng đoạn đồng bộ — tức là mọi biến có phép lấy địa chỉ/mượn trong MIR) và sống qua
  ít nhất một `.await` được đặt **cố định** trong trường `(*self).live_v` suốt đời của nó: mọi lần dùng biến được viết lại
  thành truy cập trực tiếp vào trường, không lưu/khôi phục. Biến khác giữ cách lưu/khôi phục hiện tại (được phép đặt mọi
  biến sống qua await tại chỗ nếu đơn giản hơn).
- Hợp đồng đi kèm: sau lần poll đầu, một future có biến như vậy không được di chuyển trong bộ nhớ; executor/`block_on`
  của std đã thoả (future nằm trong TCB trên heap hoặc trên khung của `block_on`). Di chuyển future đã poll khi còn con
  trỏ thô sống là UB của mã `unsafe`, không phải lỗi compiler.
- Không thêm `Pin`. Revisit: không.

## Context
- SPEC-33 AXS-ASY-043 items 2–3 describe suspension as "move every live local into `(*self).live_v`" and resume as
  "move it back into its local frame variable". AXS-ASY-005 item 3 (REQ-ASY-122) forbids relocating storage whose
  address is observable across `.await`. The two rules contradict each other for address-taken locals; the
  implementation (`compiler/mir/async_lower.ax`, ready block "restore live locals") follows AXS-ASY-043.
- SPEC-35 AXS-AIO-012 item 2 (T427) explicitly supports `read(dst_ptr, len)` where `dst` is "a local buffer owned by the
  `async fn` state machine": the future stores `dst_ptr` and writes through it during a later poll. With save/restore the
  pointer refers to the poll frame of the first poll (oracle: use-after-free at `std/net/mod.ax:799`; native: the bytes
  land in a dead stack slot and the restored local is stale).
- Views cannot cross `.await` (AXS-ASY-034), so the only way an address survives a suspension is a raw pointer, which
  requires `unsafe` to create or dereference; but the *storage* rule is the compiler's, not the user's.

## Options
1. Keep save/restore; document that addresses of async locals are invalid across `.await` and require `Box`/`IoBuf`.
   Contradicts AXS-AIO-012 item 2 and REQ-ASY-122, and makes the slice API of SPEC-35 unusable inside tasks.
2. Address-observable cross-await locals live in place in the state struct (all uses rewritten to the field); other
   locals unchanged. Small, targeted change in one pass; keeps the state-minimisation rules of AXS-ASY-041.
3. All cross-await locals live in place (no save/restore at all). Simpler invariant, slightly more memory traffic in
   `poll`; acceptable as an implementation choice under option 2.
4. Introduce `Pin`/`Unpin`. Rejected by AXS-ASY-005 item 1 (REQ-ASY-047, REQ-ASY-121).

## Decision
Option 2, with option 3 allowed as the implementation if it is simpler. Normative text: SPEC-33 AXS-ASY-043 item 7 and
AXS-ASY-005 item 4 (added 2026-11-25). "Address-observable" is decided conservatively on MIR: any local that is the base
of an address-of / borrow rvalue anywhere in the body (or a projection of it). Storage packing (AXS-ASY-041 item 2) must
not overlap an address-observable local with another field in any state where the local is initialized.

## Consequences
- T428a (axiom-semantics, opus) changes `compiler/mir/async_lower.ax` (and drop glue in `compiler/mir/drop.ax` if it
  reads the field differently), adds direct-form regression tests (oracle and native) and removes the "stable frame owned
  by `main`" workaround from `tests/conformance/p11/e11_6_async_io/tcp_framing_split.ax`.
- The P11 gate T311 depends on T428a.
- No surface syntax change; no new diagnostics.

## Sources
SPEC-33 AXS-ASY-005, AXS-ASY-041, AXS-ASY-043; SPEC-35 AXS-AIO-012; `0135 §47–50`; `tasks/0619 §30, §36–37`;
`_workspaces/reports/T428-report.md` F1; `_workspaces/reports/T428-qa.md`.
