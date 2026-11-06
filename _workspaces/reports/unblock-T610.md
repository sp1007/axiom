# Unblock Report — T610 (E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE))

## Tóm tắt
- **Nguyên nhân bị chặn**: `T610` thất bại ở vòng QA thứ 3 (`Round 2`, `_workspaces/reports/T610-qa.md`) do 2 lỗi cục bộ về tính đúng đắn (`soundness`) còn sót lại trong `compiler/opt/loops/mod.ax` và `compiler/opt/bce/mod.ax` (toàn bộ các lỗi ở `Round 0` và `Round 1` cùng tự biên dịch cố định Stage-3 `O1` đều đã đạt):
  1. `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:2994`) chỉ kiểm tra `opc == OPT_INST_LOAD || opc == OPT_INST_LEN` mà quên `opc == OPT_INST_DISCRIMINANT` (`_d = discriminant(place)` đọc thẻ `enum` qua `inst.rhs_place`, cờ `EFFECT_READS_MEM`), dẫn tới báo sai `can_hoist = true` khi biến `enum` cục bộ hoặc `mut_view<State>` bị ghi đè trong vòng lặp, hoặc khi deref con trỏ thô `*const State` trong vòng lặp có thể chạy 0 lần.
  2. Lệnh gán toàn bộ hợp thể `OPT_INST_AGGREGATE` (`place.proj_count == 0`, `inst.mem_def.v != MEM_SSA_NONE`, ví dụ `a = Vec<i32> { ptr: p, len: 0, cap: 4 }` hoặc `a = Pair { x: 99, y: 99 }`) trên biến cục bộ có địa chỉ lộ ra hoặc có `view`/`mut_view` trỏ tới bị lọt qua cổng kiểm tra clobber `AliasInfo` trong cả `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax:1198-1208`) và `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax:2833-2843`) vì hai hàm này chỉ gọi `AliasInfo` khi `opc == OPT_INST_STORE` hoặc `place.proj_count > 0`.
- **Quyết định (`ADR-0037`)**:
  - Ghi nhận `ADR-0037` (`spec/decisions/ADR-0037-loops-discriminant-and-aggregate-memdef-clobber.md`) và cập nhật `spec/SPEC-72-loops-scev-bce.md` (`AXS-BCE-004` rule 1, `AXS-LOOP-011` rule 3), `spec/INDEX.md`, và `spec/ROADMAP.md`.
  - Thêm `T610` vào `depends:` của `T064` (`_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md`) để `T064` (`paths: [compiler/opt, tests/opt2]`) không thể chạy trước khi các file đang sửa của `T610` trong `compiler/opt/loops` và `compiler/opt/bce` được commit.
  - Mở khóa (`taskctl.py unblock T610`) kèm hướng dẫn sửa cụ thể 2 lỗi `Round 2` trong phần `## Notes` của `T610`.

## Decision, Options & Rationale

### Classification
- **TYPE B — Architecture & Spec Clarification + Board Dependency Serialization** (`ADR-0037`).

### Options Considered
1. **Option A — Split `T610` into a follow-up task.**
   - *Rejected*: `T610` is already 99% complete, passes Stage-3 (`O1`) fixed-point bootstrap (`sha256(axiomc2_O1) == sha256(axiomc3_O1)`), and passes all 31 `run/opt_bce` tests plus all Round 0 and Round 1 QA audits. Only two localized opcode/clobber conditions (~20 lines total) in `compiler/opt/loops/mod.ax` and `compiler/opt/bce/mod.ax` plus their regression assertions in `tests/run/opt_bce/` remain.
2. **Option B — Clarify `SPEC-72` via `ADR-0037`, serialize `T064` after `T610`, and unblock `T610` with surgical fix notes (Chosen).**
   - *Accepted*: Preserves the completed work in `compiler/opt/loops`, `compiler/opt/bce`, and `tests/run/opt_bce`, explicitly documents the `OPT_INST_DISCRIMINANT` and `OPT_INST_AGGREGATE` (`proj_count == 0`, `mem_def != MEM_SSA_NONE`) invariants in `SPEC-72`, prevents `T064` from colliding with `T610`'s `compiler/opt/*` directories, and gives `axiom-semantics` exact instructions to finish the two fixes in one sitting.

### Applied Changes
1. **Created `spec/decisions/ADR-0037-loops-discriminant-and-aggregate-memdef-clobber.md`** and updated `spec/SPEC-72-loops-scev-bce.md` (`AXS-BCE-004`, `AXS-LOOP-011`), `spec/INDEX.md`, and `spec/ROADMAP.md`.
2. **Updated `_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md`**: added `T610` to `depends: [T215, T603, T607, T610, T613]`.
3. **Unblocked `_workspaces/tasks/todo/T610-e15-3-loop-canonicalization-scev-bce.md`** (`taskctl.py unblock T610`) and recorded step-by-step instructions in `## Notes` for both Round 2 QA findings.

## Files changed
- _workspaces/reports/unblock-T610.md
- _workspaces/tasks/doing/T610-e15-3-loop-canonicalization-scev-bce.md
- _workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md
- _workspaces/tasks/todo/T610-e15-3-loop-canonicalization-scev-bce.md
- spec/INDEX.md
- spec/ROADMAP.md
- spec/SPEC-72-loops-scev-bce.md
- spec/decisions/ADR-0037-loops-discriminant-and-aggregate-memdef-clobber.md
