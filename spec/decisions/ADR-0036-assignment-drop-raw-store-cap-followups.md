# ADR-0036 — Assignment drop through views vs raw-pointer stores; raw pointers are not capabilities; view locals at scope end; index auto-deref; identity of the language `Drop`

Status: accepted (2026-10-23, architect; owner-delegated decision)

## Tóm tắt
- T141 (AX0-FIX-03) làm cho struct chỉ có trường số/con trỏ có `impl Drop` thật sự được drop, và
  vòng sửa 2 đã chọn một quy tắc mà spec chưa ghi: **phép gán `place = rhs` drop giá trị cũ của
  place, kể cả khi place đi qua `view`/`mut_view`; nhưng ghi qua con trỏ thô (`*mut T`/`*const T`)
  thì không bao giờ drop** (con trỏ thô có thể trỏ vào vùng nhớ chưa khởi tạo — `heap_alloc`, phần
  dư của `Vec`). ADR này ghi quy tắc đó vào SPEC-03 (AXS-SEM-043) và SPEC-12 (AXS-DROP-007).
- Quyết định thêm: (2) con trỏ thô lấy bằng `address_of`/`address_of_mut` **không phải capability**
  — không giữ view nào sau biểu thức tạo ra nó (SPEC-11 AXS-CAP-008); (3) một local kiểu view khai
  báo sau owner chết trước khi owner bị drop ở cuối scope, nên `let va: view<T> = view(a)` với `T`
  cần drop là hợp lệ (AXS-CAP-009) — cả axiom0 lẫn axiomc hiện báo sai `AX_CAP_OUTLIVES_OWNER`;
  (4) `a[i]` với `a: view<[N]T>`/`mut_view<[N]T>` được tự deref một mức như truy cập trường
  (AXS-SEM-047), không áp dụng cho con trỏ thô; triển khai sau self-host (R7), epic mới E14.5;
  (5) trait `Drop` của ngôn ngữ được nhận diện theo phân giải tên (tên `Drop` trần trỏ tới
  lang item của prelude), không theo hậu tố `.Drop` của đường dẫn.
- Task mới: T157 (AX0-FIX-06, capability), T158 (AX0-FIX-07, nhận diện `Drop`), T159 (AX0-FIX-08,
  verifier kiểm tra drop thiếu/đôi trên code thật), T160 (test std dạng project cho `Arena`);
  bổ sung tiêu chí cho T139, T147, T149, T214; T086 phụ thuộc T157–T159.
- Revisit: không (quy tắc §1 là cách hiểu thông thường của `ptr.write`; §4 chỉ thêm tiện lợi).

## Context
- T141 round 2 (`_workspaces/reports/T141-report.md` "Design decision: which assignments drop the
  old value"; QA `_workspaces/reports/T141-qa.md` R1-1, N4) implemented in both compilers
  (`bootstrap/axiom0/src/mir/build/builder.c` `place_has_raw_deref`, `compiler/mir/builder.ax`
  `mb_place_has_raw_deref`): an assignment whose place needs drop drops the old value unless some
  `Deref` projection of the place dereferences a raw pointer. Before round 2 every deref place
  skipped the drop, so `self.f = v` in a `self: mut_view<Self>` method leaked the old value.
  SPEC-03 AXS-SEM-043 step (3) said "drop the old value of the place if it holds one that needs
  drop" without saying when a place "holds one".
- T141 QA N5 / report "Follow-up": `let p: *mut S = unsafe { address_of_mut(b) };` on a local with
  `impl Drop for S` is rejected by axiomc's `compiler/own/cap.ax` with `AX_CAP_OUTLIVES_OWNER` at
  the end of the block. Architect probe (2026-10-23, `build/axiom0.exe`, a pre-T141 build, fieldless
  `struct S {}` with `impl Drop`): axiom0 rejects the same program and also
  `let va: view<S> = view(a);` with the same code at the function's closing position. Both programs
  are valid by SPEC-11 (nothing outlives `a`).
- T141 QA N3: `a[i]` on `a: mut_view<[3]S>` is `AX_TYPE_CANNOT_INDEX`, while field access
  auto-derefs views (`w.f`) and `v[i]` on a slice view works. The spec is silent.
- T141 round 1: `is_drop_trait_name` (axiom0 `mir/drop/drop.c`) and its port twins accept any path
  ending in `.Drop`, so `impl m.Drop for S` (a user trait) is taken as a destructor. Narrowing it
  needs `compiler/hir/lower.ax` `hir_postprocess_items` and axiom0 `driver/pipeline.c` to agree on
  the method renaming (one renames by last segment, the other by source text).
- T141 QA round 0 notes: the verifier's missing-drop check runs only when `func == NULL` (MIR-text
  tests) in `verify.c` and `verifier.ax`; `AX_VERIFY_DOUBLE_DROP` is limited to explicit drops.

## Options
§1 Assignment through an indirection:
1. Never drop through any deref (pre-round-2 behaviour). Rejected: leaks every field reassigned
   through `self: mut_view<Self>`; distorts T086's memory measurement.
2. Always drop, including raw-pointer stores. Rejected: `*p = v` is how `unsafe` code initialises
   fresh memory (`heap_alloc`, `Vec` spare capacity); dropping garbage bytes is UB.
3. **Drop through view/mut_view, never through a raw pointer (chosen).** A view is only made from an
   initialised owner place (SPEC-11 AXS-CAP-004), so the pointee always holds a live value; a raw
   pointer carries no initialisation guarantee. Same meaning as `ptr.write`; code that wants the old
   value dropped calls `drop_in_place(p)` first.

§2 Raw pointers and capabilities:
1. Treat `address_of(_mut)(x)` as creating a view that lives as long as the pointer. Rejected: raw
   pointers are untracked by design (REQ-FFI-011, SPEC-04 AXS-EXT `AddressOf`); it would make the
   capability checker reason about `unsafe` aliasing it cannot see.
2. **The place is borrowed only for the duration of the `address_of` expression (an ephemeral
   capability, AXS-CAP-005); the resulting pointer holds none (chosen).** Dangling raw pointers are
   the `unsafe` author's responsibility.

§3 View locals at scope end: the owner-outlives check must use the real end-of-scope order —
locals die in reverse declaration order (AXS-DROP-002), and a view local is dead after its last use
and in any case at its own scope end, which comes before the drop of every owner declared earlier.
Only option consistent with SPEC-11/12; the current behaviour is a bug.

§4 Index through a view:
1. Keep `(*a)[i]` mandatory. Viable but inconsistent with field access.
2. **One-level auto-deref of `view`/`mut_view` for an index base, as for field access (chosen);
   writing needs `mut_view`. Not for raw pointers** (`p[i]` on `*mut [N]T` would read as C pointer
   arithmetic; `(*p)[i]` in `unsafe` stays explicit).
   Timing: not needed to compile axiomc (`(*a)[i]` works in both compilers), so by R7 it is not
   added to axiom0; axiomc implements it after self-hosting (new epic E14.5, planned by T214).

§5 Identity of the language `Drop`:
1. Text suffix `.Drop` (current). Rejected: any user trait named `Drop` becomes a destructor.
2. **By resolution: `impl Drop for T` is a destructor iff the trait path resolves to the prelude
   lang item `Drop` (AXS-EXT-023); in axiom0/axiomc v0.1 that is the bare name `Drop` when no item
   named `Drop` declared or imported in the module shadows it (chosen).** A qualified `m.Drop` or a
   shadowing user trait is an ordinary trait; its method `drop` is an ordinary method.

## Decision
1. **SPEC-03 AXS-SEM-043** gains the place classification: step (3) applies to every place whose
   projection chain contains no dereference of a raw pointer (locals, fields, tuple fields, array
   and slice elements, and places reached through `view`/`mut_view` deref, explicit `*m` or auto-
   deref). A place whose chain contains a `Deref` of `*mut T`/`*const T` (including auto-deref
   `p.f` with `p: *mut S`) is a **raw store**: the old bytes are overwritten, never dropped. The
   classification is by the types along the place's projection path, not by syntax.
   **SPEC-12 AXS-DROP-007** states the same rule from the drop side, with the test matrix rows.
2. **SPEC-11 AXS-CAP-008** (raw pointers are not capabilities) and **AXS-CAP-009** (view locals and
   scope-end drops) as in §2/§3. Implemented in both compilers by T157 (AX0-FIX-06).
3. **SPEC-03 AXS-SEM-047** (index auto-deref through a view) as in §4; status "specified, axiomc
   after self-host (E14.5)"; until then `AX_TYPE_CANNOT_INDEX` with a hint `write (*a)[i]` is the
   conforming v0.1 behaviour of both bootstrap compilers.
4. **SPEC-12 AXS-DROP-008** (identity of the language `Drop`) as in §5. Implemented in both
   compilers, with the method-renaming agreement of `hir_postprocess_items`/`pipeline.c`, by T158
   (AX0-FIX-07).
5. The verifier's drop checks (missing drop, double drop) run on every real body after drop
   elaboration, drop-flag aware, in both compilers: T159 (AX0-FIX-08).
6. Board: T157–T160 created; T139 gains the leg-isolation fix for `tests/run/host/fs/dir.ax`; T147
   gains restoring string literals in `tests/run/numeric/qa_t140_edge_matrix.ax`; T149 gains the
   deferred element-store-through-view drop test; T214 gains E14.5; T086 depends on T157–T159.

## Consequences
- Affected specs: SPEC-03 (AXS-SEM-043 amended, AXS-SEM-047 new), SPEC-11 (AXS-CAP-008/009 new),
  SPEC-12 (AXS-DROP-007/008 new, test matrix), ROADMAP (E14.5, change log).
- Affected tests: existing `tests/run/drop/assign_through_view_method.ax`,
  `qa_t141_r1_assign_through_view.ax`, `qa_t141_r2_view_loop_raw_field.ax` already pin §1 (they now
  cite AXS-DROP-007 through this ADR). New tests come with T157–T160.
- std/compiler code that initialises memory must keep using raw-pointer stores; an `*_init(x:
  mut_view<T>)` function drops the old field value, so its callers must pass an initialised value
  (T141 audit: all current callers pass zero-filled or fresh values whose drop is a no-op).

## Sources
`_workspaces/reports/T141-report.md`, `_workspaces/reports/T141-qa.md`; SPEC-03 AXS-SEM-042/043;
SPEC-11 AXS-CAP-004/005; SPEC-12 AXS-DROP-002/003; SPEC-04 AXS-EXT-023 and the `address_of`
intrinsic rows; ADR-0014 (ownership/capability/drop), ADR-0034 §2 (lockstep axiom0 + port until the
freeze), ADR-0035 §4 (registry rule); docs 0160 (capabilities), 0177, 0178 (drop); REQ-FFI-011,
REQ-OWN-002, REQ-VER-001.
