# Unblock T409 — E11.2: Atomic & memory-ordering litmus conformance suite

## Tóm tắt
- Cổng kiểm định QA của `T409` (`owner: axiom-qa`) đã phát hiện hai lỗi nghiêm trọng trong trình biên dịch `axiomc` khi chạy bộ kiểm thử conformance `tests/conformance/p11/e11_2_atomics/`:
  1. **Lỗi 1 (`compiler/driver/pipeline.ax:1859-1864, 4004`)**: Trình điều khiển `driver_emit_build_mi_body_obj` và nhánh `emit-obj` ghi đè vô điều kiện `(*inst).size = 8u8` cho mọi chỉ thị MI không phải `MOV`/`CMP` trước khi gọi `x64_encode_mi_inst_obj`. Điều này ép các thao tác nguyên tử hẹp 1/2/4-byte (`AtomicBool`, `AtomicU8`/`I8`, `AtomicU16`/`I16`, `AtomicU32`/`I32`) phát ra mã máy 64-bit `QWORD PTR` (`XCHG`, `LOCK XADD`, bitwise CAS loop, `LOCK CMPXCHG`), gây ra hai hậu quả nghiêm trọng trong chế độ native (`[native]` và `[native-O1]`): làm hỏng tối đa 7 byte bộ nhớ lân cận trong struct/array (adjacent memory corruption) và làm hỏng hoàn toàn phép CAS số nguyên âm có dấu hẹp (`AtomicI8.new(-1i8).compare_exchange(-1i8, ...)`) do so sánh 64-bit thanh ghi mở rộng dấu `RAX` với bộ nhớ 1 byte.
  2. **Lỗi 2 (`compiler/types/typeck.ax:11336-11392, 3369, 3604-3609`)**: Thứ tự xử lý trường struct đơn lượt trong Pass 1a (`typeck_pass1a`) diễn ra trước khi prelude `std` được đăng ký trong `thir`. Do đó, `lookup_path_type_by_name` không tìm thấy `Atomic<T>` (trả về `t_error`), khiến mọi trường struct lồng `Atomic<...>` bị gán kiểu `TY_ERROR`, làm tê liệt phân giải phương thức nguyên tử (`s.a.load(...)`) và đồng thời đầu độc bộ nhớ đệm định danh kiểu `item_type` của các alias nguyên tử prelude (`AtomicBool`, `AtomicU32`), dẫn đến các hàm phía sau bị lỗi giả `error[AX_TYPE_UNKNOWN_FIELD]` khi nhận tham số `view<AtomicBool>` / `view<AtomicU32>`.
- Do `T409` quy định rõ `Out of scope: Modifying compiler or std source files`, theo nguyên tắc cổng kiểm định R9 và phân loại thay đổi của Kiến trúc sư, QA không tự vá trình biên dịch mà tạo một task sửa lỗi tiên quyết.
- Quyết định: Phân loại **TYPE A** (sửa lỗi hiện thực hạ tầng theo đúng đặc tả `spec/SPEC-31-atomics.md`, không thay đổi ngữ nghĩa ngôn ngữ). Tạo task tiên quyết `T429` (`phase: P11-concurrency-async`, `priority: 129`, `owner: axiom-backend`, `reviewer: axiom-qa`, `model: opus`, `gate_model: sonnet`) để sửa cả 2 lỗi trên và tái tạo Stage-2 `axiomc2.exe` trong `build-snap-T429/build`.
- Cập nhật `T409` phụ thuộc vào `T429` (`depends: [T407, T408, T429]`), cập nhật `T311` phụ thuộc vào `T429`, cập nhật `spec/ROADMAP.md` (mục E11.2 và nhật ký thay đổi), và chạy `taskctl.py unblock T409`.
- Đã xác nhận thành công qua `taskctl.py lint`, `taskctl.py validate` (599 tasks OK), `reqcov.py --strict` (COVERAGE OK, 0 gaps), và `harness_check.py` (HARNESS OK).

## Decision & Root Cause Analysis

Classification: **TYPE A** (implementation bug fix required by SPEC-31 and Phase P11 gate rule R9; no language grammar or semantic model changes, so no ADR required).

### Root causes addressed by prerequisite task `T429`
1. **Sub-64-bit atomic MI width clobbered to 8 bytes (`compiler/driver/pipeline.ax:1859-1864, 4004`)**:
   - *Governing Spec*: `spec/SPEC-31-atomics.md` `AXS-ATM-005` (width-exact storage-bound atomicity without tearing or neighbor corruption), `AXS-ATM-010`, `AXS-ATM-017`, `AXS-ATM-018`, `INV-ATM-002`, `INV-ORACLE-002`.
   - *Issue*: `driver_emit_build_mi_body_obj` unconditionally executes `(*inst).size = 8u8;` for non-`MOV`/non-`CMP` instructions, clobbering operand widths (`1u8`, `2u8`, `4u8`) configured by instruction selection in `compiler/backend/x86_64/isel.ax`. Native x86-64 emission then generates `REX.W` prefix instructions (e.g., `f0 48 0f b1 11 lock cmpxchg QWORD PTR [rcx], rdx`).
   - *Fix*: Preserve `(*inst).size` for atomic instruction opcodes (`X64_MI_XCHG`, `X64_MI_LOCK_XADD`, `X64_MI_ATOMIC_RMW_LOOP`, `X64_MI_LOCK_CMPXCHG`) so `x64_encode_mi_inst_obj` emits size-exact `BYTE PTR`, `WORD PTR`, and `DWORD PTR` encodings. Ensure sign-extended register inputs for signed sub-64-bit atomics compare only their active low byte/word/dword against target memory.

2. **Pass 1a struct field resolution order vs appended prelude (`compiler/types/typeck.ax:11336-11392, 3369, 3604-3609`)**:
   - *Governing Spec*: `spec/SPEC-31-atomics.md` `AXS-ATM-010`, `AXS-ATM-012`, `REQ-CONC-079`, `REQ-ATM-029`.
   - *Issue*: Prelude items (`pub struct Atomic<T>`, `pub type AtomicU32 = ...`) are appended to `hir_file.items` after user declarations. `typeck_pass1a` performs struct field type resolution (`hir_type_to_typeid`) in a single forward pass before subsequent prelude structs have their `TypeId` registered in `thir`. This leads `lookup_path_type_by_name` to return `t_error`, poisoning struct-embedded atomic fields and caching `t_error` on prelude aliases.
   - *Fix*: Implement two-phase struct registration in `typeck_pass1a` (register all struct item `TypeId`s before resolving struct field types), or pre-register prelude type items prior to user AST processing, and ensure cache lookups never poison prelude type aliases.

### Options considered
1. **Create single prerequisite fix task `T429` (`owner: axiom-backend`, `priority: 129`) covering both compiler fixes and Stage-2 rebuild** — **CHOSEN**. Both issues are localized in the compiler self-host bundle (`compiler/driver/pipeline.ax` and `compiler/types/typeck.ax`). Packaging them into a single prerequisite task minimizes Stage-2 compiler bootstrap rebuild overhead and unblocks `T409` cleanly.
2. **Permit `T409` to edit `compiler/` directly** — REJECTED. Violates `T409`'s explicit contract (`Out of scope: Modifying compiler or std source files`) and role separation (QA writes tests; backend/semantics engineer implements compiler fixes).
3. **Split into two separate tasks (one for pipeline, one for typeck)** — REJECTED. Both files are part of the self-host compiler bundle and require Stage-2 rebuild; splitting would double compiler rebuild overhead and add unnecessary serial task churn.

## Board changes
- Reserved task ID `T429` via `python .claude/skills/axiom-tasks/scripts/taskctl.py new-id --phase P11`.
- Created prerequisite task `_workspaces/tasks/todo/T429-e11-2-sub-64-bit-atomic-mi-and-struct-embedded-atomic-fix.md` (`phase: P11-concurrency-async`, `priority: 129`, `owner: axiom-backend`, `reviewer: axiom-qa`, `model: opus`, `gate_model: sonnet`, `depends: [T407, T408]`, `paths: [compiler/driver/pipeline.ax, compiler/types/typeck.ax, tests/run/atomics]`, `locks: [tests/selfhost]`, `covers: [REQ-CONC-134, REQ-ATM-022]`).
- Updated `_workspaces/tasks/todo/T409-e11-2-atomic-litmus-conformance-suite.md` to depend on `T429` (`depends: [T407, T408, T429]`).
- Updated `_workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md` to include `T429` in `depends:`.
- Updated `spec/ROADMAP.md` §3 (epic `E11.2` task range `*(T405–T409, T429)*`) and §5 change log table.
- Unblocked `T409` via `taskctl.py unblock T409`.
- Verified `taskctl.py lint`, `taskctl.py validate` (599 tasks OK), `reqcov.py --strict` (COVERAGE OK, 0 gaps), and `harness_check.py` (HARNESS OK).

## Safety & Isolation Checks
- Did not touch any compiler or standard library source files.
- Preserved existing untracked files in `tests/conformance/p11/e11_2_atomics/` for `T409`.
- Did not edit `docs/` or `bootstrap/axiom0/`.
- Did not commit or push (orchestrator handles commits).
- Did not call `unblock-end`.

## Files changed
- _workspaces/tasks/todo/T429-e11-2-sub-64-bit-atomic-mi-and-struct-embedded-atomic-fix.md
- _workspaces/tasks/todo/T409-e11-2-atomic-litmus-conformance-suite.md
- _workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- spec/ROADMAP.md
