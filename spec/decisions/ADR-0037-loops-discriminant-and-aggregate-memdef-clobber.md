# ADR-0037 — `OPT_INST_DISCRIMINANT` hoisting guards in `compiler/opt/loops`, whole-aggregate `MemoryDef` clobber checks in `compiler/opt/bce` & `compiler/opt/loops`, and `T064 -> T610` dependency ordering

Status: accepted (2026-11-06, architect; owner-delegated decision)

## Tóm tắt
- `T610` (`E15.3 — Natural loop discovery, loop canonicalization, Scalar Evolution (SCEV) & range/bounds-check elimination (BCE)`) bị chặn sau 3 vòng QA (`Round 0`, `Round 1`, `Round 2`). Các lỗi ở `Round 0` và `Round 1` đã được sửa triệt để và xác nhận `RESOLVED` trong `_workspaces/reports/T610-qa.md` (`Round 2`), chỉ còn lại **2 lỗi cục bộ** về tính đúng đắn (`soundness`) trong `compiler/opt/loops/mod.ax` và `compiler/opt/bce/mod.ax`:
  1. **`OPT_INST_DISCRIMINANT` bị bỏ sót trong `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:2994`)**: `MIR_RVALUE_DISCRIMINANT` hạ xuống `OPT_INST_DISCRIMINANT` với toán hạng nguồn đặt duy nhất ở `inst.rhs_place` và mang cờ `EFFECT_READS_MEM`. Do `loops_can_hoist_inst` chỉ kiểm tra `opc == OPT_INST_LOAD || opc == OPT_INST_LEN`, lệnh đọc thẻ `enum` (`discriminant(place)`) đã bỏ qua kiểm tra biến cục bộ bị ghi trong vòng lặp, kiểm tra bẫy deref con trỏ thô (`CAP_MODE_RAW_PTR`) ở vòng lặp có thể chạy 0 lần, và kiểm tra clobber qua `loops_region_clobbered_in_loop`.
  2. **Lệnh ghi toàn bộ hợp thể `OPT_INST_AGGREGATE` (`place.proj_count == 0`, `inst.mem_def != MEM_SSA_NONE`) lọt qua kiểm tra clobber `AliasInfo` trong `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax:1198`) và `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax:2833`)**: Khác với `MIR_RVALUE_USE` (hạ xuống `OPT_INST_STORE` khi đích là bộ nhớ), `MIR_RVALUE_AGGREGATE` / `MIR_RVALUE_REPEAT` luôn giữ `opc == OPT_INST_AGGREGATE` ngay cả khi ghi đè toàn bộ biến cục bộ có địa chỉ lộ ra hoặc có `view`/`mut_view` trỏ tới (`a = Vec { ptr, len: 0, cap: 4 }` hoặc `a = Pair { x: 99, y: 99 }`). Việc chỉ kiểm tra `opc == OPT_INST_STORE` hoặc `place.proj_count > 0` khiến `AliasInfo` bị bỏ qua.
- **Quyết định (TYPE B — làm rõ quy tắc spec `SPEC-72` + mở khóa `T610` + khóa thứ tự bảng task `T064 -> T610`)**:
  - Cập nhật `SPEC-72` (`AXS-BCE-004`, `AXS-LOOP-011`) quy định rõ: (a) mọi lệnh đọc `rhs_place` (`OPT_INST_LOAD`, `OPT_INST_LEN`, `OPT_INST_DISCRIMINANT`) đều chịu cùng cổng kiểm tra bất biến `rhs_place`, bẫy con trỏ thô ở vòng lặp 0 lần, và `loops_region_clobbered_in_loop`; (b) mọi lệnh gán tạo `MemoryDef` (`inst.mem_def.v != MEM_SSA_NONE`), `OPT_INST_AGGREGATE`, hoặc ghi vào biến có mượn/lộ địa chỉ (`proj_count == 0` hay `proj_count > 0`) đều phải truy vấn `AliasInfo`.
  - Thêm `T610` vào `depends:` của `T064` (vì `T064` có `paths: [compiler/opt, tests/opt2]` bao trùm `compiler/opt/loops` và `compiler/opt/bce`) và mở khóa (`unblock`) `T610` với hướng dẫn sửa chính xác 2 điểm trên.
- Revisit: không.

## Context
During `T610` Round 2 QA (`_workspaces/reports/T610-qa.md`), Stage-1/2/3 `O1` fixed-point self-hosting (`sha256(axiomc2_O1) == sha256(axiomc3_O1)`), all 31 `run/opt_bce` tests, and all Round 0 / Round 1 soundness audits passed, but the QA adversarial probe identified two localized soundness gaps:
1. **`OPT_INST_DISCRIMINANT` omitted from `loops_can_hoist_inst` (`compiler/opt/loops/mod.ax:2994-3036`)**:
   - In `compiler/opt/optir/mod.ax:2044-2046`, `MIR_RVALUE_DISCRIMINANT` lowers to `opc = OPT_INST_DISCRIMINANT` with `lhs = OPT_VALUE_NONE`, `rhs = OPT_VALUE_NONE`, `extra_arg_count = 0`, and its source place stored in `inst.rhs_place` (identical in layout to `OPT_INST_LOAD` and `OPT_INST_LEN`).
   - In `compiler/opt/effects/mod.ax:560-561`, `effect_infer_inst` classifies `OPT_INST_DISCRIMINANT` as `EFFECT_READS_MEM`.
   - Because `loops_can_hoist_inst` at line 2994 checked only `if opc == OPT_INST_LOAD || opc == OPT_INST_LEN`, `OPT_INST_DISCRIMINANT` bypassed:
     - `loops_local_written_in_loop` on `inst.rhs_place.local` and dynamic `MIR_PROJ_INDEX` / `MIR_PROJ_SUB_SLICE` operand locals,
     - `rreg.cap_mode == CAP_MODE_RAW_PTR` zero-trip trap prevention (`proven_nonzero_trip && lp_dominates_all_exits`), and
     - `loops_region_clobbered_in_loop` (`MemorySSA` + `AliasInfo` clobber check).
2. **Whole-aggregate `MemoryDef` writes (`OPT_INST_AGGREGATE` with `place.proj_count == 0`) bypassing `AliasInfo` clobber checks**:
   - In `compiler/opt/optir/mod.ax:2047-2049`, `MIR_RVALUE_AGGREGATE` and `MIR_RVALUE_REPEAT` lower to `opc = OPT_INST_AGGREGATE` even when assigning to an `OPT_LOCAL_MEMORY` / borrowed / address-exposed local (`inst.place.proj_count == 0`), recording the memory write via `inst.mem_def.v != MEM_SSA_NONE`.
   - In `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax:1198-1199`), `writes_proj` required `inst.place.proj_count > 0`, and the `if` condition checked only `opc == OPT_INST_STORE || opc == OPT_INST_INSERT_FIELD || opc == OPT_INST_DROP_FLAG || writes_proj`. When a 2-branch `mut_view<Vec<i32>>` `vp` aliased `a` and `a = Vec<i32> { ptr: p, len: 0, cap: 4 }` overwrote `a` as a whole aggregate (`opc == OPT_INST_AGGREGATE`, `proj_count == 0`), `alias_query_places` was skipped and `opt_bce` falsely eliminated `assert(idx < vp.len)`.
   - Symmetrically, in `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax:2833-2843`), the `else if opc != OPT_INST_NOP && sk == MIR_STMT_ASSIGN` branch gated `alias_query_regions` on `dpl.proj_count > 0 || dpl.local.v == reg.base_local.v || (reg.has_resolved_place && dpl.local.v == reg.resolved_place.local.v)`. When `mv: mut_view<Pair>` had 2-branch provenance (`!reg.has_resolved_place`, `reg.base_local == mv != a`) and the loop body executed `a = Pair { x: 99, y: 99 }` (`opc == OPT_INST_AGGREGATE`, `dpl.proj_count == 0`, `inst.mem_def.v != MEM_SSA_NONE`), `alias_query_regions` was skipped and `loops_can_hoist_inst` falsely reported `mv.x` as loop-invariant.
3. **Board path overlap with `T064`**:
   - `T064` (`_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md`) has broad `paths: [compiler/opt, tests/opt2]`, which overlaps `T610`'s `compiler/opt/loops` and `compiler/opt/bce`. Without `T610` in `T064`'s `depends:`, `T064` could be considered ready if `T610` were ever blocked/parked while uncommitted files exist in `compiler/opt/loops` and `compiler/opt/bce`.

## Options
1. **Option A — Split `T610` into a new follow-up task.**
   - *Rejected*: All of `T610` is already implemented and verified at Stage-3 `O1` fixed point in `compiler/opt/loops/mod.ax`, `compiler/opt/bce/mod.ax`, and `tests/run/opt_bce/*`; only two localized conditions (~20 lines total) and their regression tests remain. Splitting would add unnecessary board overhead for a 20-line soundness fix.
2. **Option B — Clarify `SPEC-72` (`AXS-BCE-004`, `AXS-LOOP-011`), add `T610` to `T064`'s `depends:`, and unblock `T610` with exact fix instructions (chosen).**
   - *Accepted*: Directly resolves both Round 2 QA findings in place, records the exact `OptIR` opcode invariants in `SPEC-72`, and prevents any `compiler/opt` path collision with `T064`.

## Decision
1. **`SPEC-72 AXS-LOOP-011` (Rule 3 — Memory-read hoisting gate)**:
   - Any `OptIR` instruction that reads memory or place metadata through `inst.rhs_place` — specifically `OPT_INST_LOAD`, `OPT_INST_LEN`, and `OPT_INST_DISCRIMINANT` — MUST pass the full `rhs_place` hoisting gate in `loops_can_hoist_inst`:
     1. `inst.rhs_place.local` and all dynamic `MIR_PROJ_INDEX` (`index_local`) / `MIR_PROJ_SUB_SLICE` (`from_local`, `to_local`) operand locals are not written or dropped in the loop (`!loops_local_written_in_loop`),
     2. If `alias_extract_region` on `inst.rhs_place` yields `CAP_MODE_RAW_PTR`, the loop has a proven non-zero constant trip count (`TRIP_CONST`, `const_iters >= 1`, `CERTAINTY_PROVEN`) and the instruction's block dominates all loop exits (`lp_dominates_all_exits`), and
     3. `loops_region_clobbered_in_loop` confirms no `MemoryDef` or mutating instruction/terminator in the loop may alias `rreg`.
2. **`SPEC-72 AXS-BCE-004` (Rule 1) & `AXS-LOOP-011` (Rule 3 — Whole-aggregate and `MemoryDef` clobber checks)**:
   - Because `MIR_RVALUE_AGGREGATE` and `MIR_RVALUE_REPEAT` lower to `OPT_INST_AGGREGATE` even on `OPT_LOCAL_MEMORY` / borrowed / address-exposed locals with `place.proj_count == 0`, clobber analyses MUST NOT assume that a whole-local (`proj_count == 0`) non-`OPT_INST_STORE` assignment is purely scalar:
     1. In `bce_inst_clobbers_len_state` (`compiler/opt/bce/mod.ax`), any `MIR_STMT_ASSIGN` instruction with `inst.mem_def.v != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, or `inst.place.proj_count > 0` (and in `bce_term_clobbers_len_state`, any `OPT_TERM_DROP` or `OPT_TERM_CALL` `has_call_dest` when `can_mutate_root` holds) MUST run `alias_query_places` against `region_place`.
     2. In `loops_region_clobbered_in_loop` (`compiler/opt/loops/mod.ax`), any `MIR_STMT_ASSIGN` instruction (`opc != OPT_INST_NOP`) where `(unsafe { (*inst).mem_def.v }) != MEM_SSA_NONE`, `opc == OPT_INST_AGGREGATE`, `dpl.proj_count > 0`, `loops_local_has_indirect_mutation(body, info, dpl.local.v)`, or `dpl.local` matches `reg.base_local` / `reg.resolved_place.local` MUST extract `dreg` and run `alias_query_regions` against `reg`.
3. **Board ordering (`T064` depends on `T610`)**:
   - Add `T610` to `T064`'s `depends:` (`depends: [T215, T603, T607, T610, T613]`) so `T064` (`paths: [compiler/opt, tests/opt2]`) cannot run until `T610` is accepted and committed.
   - Unblock `T610` with detailed implementation notes for Round 2 QA Findings 1 and 2.

## Consequences
- Affected specs: `spec/SPEC-72-loops-scev-bce.md` (`AXS-BCE-004`, `AXS-LOOP-011`), `spec/INDEX.md`, `spec/ROADMAP.md`.
- Affected tasks: `_workspaces/tasks/todo/T610-e15-3-loop-canonicalization-scev-bce.md` (unblocked with Round 2 fix notes), `_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md` (`depends` adds `T610`).
- Revisit: no.

## Sources
- `_workspaces/reports/T610-report.md`, `_workspaces/reports/T610-qa.md` (Round 2 Findings 1 & 2)
- `spec/SPEC-70-optir-ssa-memoryssa.md` (`AXS-OPT-020..024`)
- `spec/SPEC-71-alias-escape-promotion.md` (`AXS-ALIAS-002..004`)
- `spec/SPEC-72-loops-scev-bce.md` (`AXS-BCE-002`, `AXS-BCE-004`, `AXS-LOOP-010`, `AXS-LOOP-011`)
