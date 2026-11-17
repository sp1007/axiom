# ADR-0043 — Cyclic type graphs are legal (cycle-safe substitution) and symbol ids are one opaque space

Status: accepted (2026-11-17, architect; owner-delegated decision; unblock of T444)

## Tóm tắt
- T444 sửa đúng nguyên nhân gốc của FU-1/FU-3: kiểu struct/enum được tham chiếu trước khi khai báo bị phân giải thành
  kiểu lỗi (kích thước 0). Sau khi sửa, đồ thị kiểu **có chu trình thật** (`struct L { next: *mut L }`, chu trình
  `RawWaker` trong prelude). Mọi hàm đệ quy đi qua trường struct / payload enum phải an toàn với chu trình.
- §1 Quy tắc: định danh của một kiểu ADT = định nghĩa + đối số kiểu. Phép thay thế (substitution) quyết định chỉ bằng
  đối số; đối số không đổi → trả lại chính kiểu đó; instance mới → intern "vỏ" không trường trước rồi mới điền trường.
  Áp dụng cho `types.ax` (đã làm trong T444) và `compiler/traits/mono.ax` (`subst_ty_self` và các hàm con) — T444 được
  thêm `mono.ax` vào `locks` và gỡ chặn (B1).
- §2 Không gian id ký hiệu: axiom0 và axiomc đều đánh số user từ 1, std từ 10000, extern từ 30000. Bundle axiomc đã có
  > 30000 ký hiệu user nên id user trùng id extern (và id std) — stage 1 hỏng ngẫu nhiên khi một tham số generic rơi
  trúng id của hàm extern (`AX_TYPE_NOT_CALLABLE`), chỉ còn ~12 ký hiệu dự phòng. Quyết định: id ký hiệu là một không
  gian duy nhất, cấp bởi **một bộ đếm** cho user/std/extern; "là std"/"là extern" là thuộc tính lưu theo ký hiệu, không
  suy ra từ khoảng số. Sửa đồng bộ axiom0 (AX0-FIX-10 = T164, priority 0) và bản port (`compiler/resolve`,
  `solver.ax` `sym_is_std_item`). T444 phụ thuộc T164.
- Các phát hiện khác của T444 thành task: T444a (offset payload biến thể kích thước trộn — sai mã), T444b (pattern hai
  binding báo move nhầm), T444c (build_axiomc dùng lại binary cũ theo mtime → gate có thể test compiler cũ), T165
  (điều tra axiomc1 segfault khi `run --interp`).
- Revisit: có — §2 nếu đo được id dày đặc làm tăng bộ nhớ bảng hay đổi tên ký hiệu sinh ra (ADR-0035) theo cách không
  mong muốn.

## Context
- `_workspaces/reports/T444-report.md`: root cause of T421 FU-1/FU-3 is item-order registration in `typeck_pass1a`
  (a field naming a not-yet-registered struct/enum became the error type, size 0). The fix (on-demand, shell-first
  registration) makes the type graph cyclic for the first time.
- B1: `compiler/traits/mono.ax` `subst_ty_self` → `subst_ty_adt` / `subst_ty_enum_or_closure` recurse through every
  field and payload without a cycle guard → stack overflow on `check` of any program (the prelude contains the
  `RawWaker -> *const RawWakerVTable -> fn(..) -> RawWaker` cycle). An early-return on unchanged args is not enough
  (`std/async/executor/async_channel_pipeline.ax` still overflows: a generic cycle whose args change).
- B2: `bootstrap/axiom0/src/resolve/resolve.c` `new_symbol` (user from 1, std from 10000) and `new_symbol_extern`
  (from 30000); `symbol_nodes` and the naming table are dense arrays indexed by id. The port copies the scheme
  (`compiler/resolve/resolver.ax` ~407/426/2360/2506, `symtab.ax` ~392, `compiler/driver/pipeline.ax` ~618) and gives
  the ranges a meaning: `compiler/traits/solver.ax` `sym_is_std_item(v) = v >= 10000 && v < 30000` (used by the
  trait-item lookup and the orphan/coherence check). The axiomc bundle has > 30000 user symbols, so user ids already
  overlap std ids and extern ids in both compilers. T444 measured a margin of 12 symbols before a generic parameter of
  `compiler.obj.writer` lands on an extern id and stage 1 fails.

## Options
§1 cyclic types:
- (a) Reject cyclic types / keep forward references as errors — contradicts SPEC-03 (declaration order is not
  semantic) and REQ-LAY-136; rejected.
- (b) Visited-set guard in every walker — works but every new walker must remember it, and a guard does not give the
  instance its identity.
- (c) **Chosen**: identity = def + args (already what `key_eq_type` compares); substitution decided by args only;
  shell-first interning of new instances; walkers that must traverse fields (layout, auto traits, copy/view checks)
  stay depth- or pointer-bounded as reviewed in the T444 report.

§2 symbol ids:
- (a) Move the bases far away (std 0x10000000, extern 0x30000000) — `symbol_nodes` and the naming table are dense
  arrays indexed by id; a base of 0x30000000 allocates gigabytes. Rejected.
- (b) Separate table/namespace for externs — fixes extern only; user/std overlap stays and `sym_is_std_item` stays
  wrong for > 10000 user symbols.
- (c) **Chosen**: one counter for every symbol in a compilation (allocation order unchanged, therefore deterministic);
  `is_std` / `is_extern` recorded per symbol (a parallel flag table, or derived from the symbol's module path that the
  naming table already stores) wherever code needs it. No code may derive a property from the numeric value of a
  `SymbolId`.

## Decision
1. **AXS-INV (types) — cyclic ADT graphs.** A struct/enum type may reach itself through pointers, function types and
   generic instances. Type identity is (definition, type arguments). Every substitution over types (`types.ax`
   `subst_type_with_vars`, `mono.ax` `subst_ty_self`, `subst_ty_adt`, `subst_ty_enum_or_closure`, and any later
   one) returns the input unchanged when no argument changes, and interns a new instance as a field-less shell before
   substituting its fields/payloads. Recorded as `spec/invariants.md` INV-SEM-008; applied by T444.
2. **Symbol id space.** A `SymbolId` is an opaque index from a single per-compilation counter shared by user, std and
   extern symbols, in axiom0 and in axiomc. Properties (std, extern) are stored per symbol. `sym_is_std_item` reads the
   stored property. Delivered by T164 (AX0-FIX-10, priority 0), axiom0 and the port in one change (ADR-0034 §2
   lockstep), with a regression that compiles a program with more than 30000 user symbols and a generic function
   before extern calls. Recorded as `spec/invariants.md` INV-BOOT-005.
3. T444 gains `compiler/traits/mono.ax` in `locks:` (T446 keeps it in `paths:` and is not running) and depends on
   T164, because the complete mono fix adds symbols ahead of `compiler.obj.writer` in bundle order.
4. Follow-ups from the T444 report: T444a (mixed-size tuple-variant payload offsets in patterns), T444b (two-binding
   tuple-variant pattern reported as use-after-move), T444c (`tools/bootstrap.py` / `tools/build_axiomc.py` reuse by
   content hash, not mtime; axiom0 rebuilt when `bootstrap/axiom0` changed), T165 (axiomc1 `run --interp` segfault,
   investigation only — axiom0 is frozen, a fix would be its own AX0-FIX task).

## Consequences
- Symbol ids (and possibly ADR-0035 generated names if any embed an id) change for every program; axiomc1 bytes change
  once; the stage-2/3 fixed point must still hold; parity goldens that print ids are regenerated with an explanation.
- The bundle-order "headroom" hazard disappears for every later task; until T164 is accepted every task that adds
  symbols to modules before `compiler.obj.writer` may fail stage 1 with `AX_TYPE_NOT_CALLABLE` at a kernel32 extern —
  that failure is the known B2 hazard, not a regression of the task.
- Risk: T485 (running) locks `compiler/types/typeck.ax`, which holds T444's uncommitted partial work in the main tree;
  the orchestrator must keep T444's hunks out of T485's commit (see `_workspaces/reports/unblock-T444.md`).

## Sources
- `_workspaces/reports/T444-report.md` (B1, B2, other findings), `_workspaces/reports/T421-report.md` (FU-1, FU-3)
- ADR-0034 (oracle independence, lockstep fixes), ADR-0035 (parity symbols), ADR-0042 §2
- `spec/SPEC-03-core-semantics.md`, `.claude/skills/axiom-compiler/SKILL.md` "axiom0 freeze"
- REQ-RES-060, REQ-LAY-136, REQ-OWN-051, REQ-BLD-028
