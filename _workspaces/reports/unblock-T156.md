# Unblock Report: T156 — Dump and diagnostic parity; registry empty

## Tóm tắt

- **Nguyên nhân chặn (`BLOCKED`)**: `T156-impl` đã hoàn tất toàn bộ phần đồng bộ dump và thông điệp chẩn đoán thuộc phạm vi frontend/MIR (`539/539` chương trình khớp tuyệt đối ở `build` và `build --emit=obj`; `539/539` khớp ở `inspect --emit=tokens|ast|resolved|thir`; `535/535` chương trình không lỗi khớp ở `inspect --emit=hir|mir|lir|mi|mc`; 3 bài test UI mới trong `tests/run/parity/diag/` đều PASS). Tuy nhiên còn lại **20 chương trình lệch chỉ ở lệnh `inspect`** nằm ngoài danh sách `paths:` ban đầu của `T156`:
  1. **Nhóm A (4 chương trình có lỗi biên dịch)**: `tests/driver/error.ax`, `tests/run/parity/traits/qa_self_missing_member.ax` (lệch từ `hir..obj`) và `tests/run/parity/diag/cannot_index.ax`, `tests/run/parity/diag/not_callable.ax` (lệch từ `mir..obj`), bắt nguồn từ `compiler/driver/pipeline.ax` và `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c`.
  2. **Nhóm B (16 chương trình closure / con trỏ hàm chỉ lệch ở `inspect --emit=obj`)**: 15 chương trình có closure bị crash (`AX_ICE("ax_interner_get: invalid StrId 0")`) trong `bootstrap/axiom0/src/driver/emit_obj.c` và 1 chương trình `tests/run/native_p7/qa_fn_ptr.ax` lệch byte `.obj` do thiếu nhánh gọi gián tiếp qua thanh ghi (`AX_X64_MI_CALL` với `AX_X64_OP_REG`) trong `emit_obj.c`.
- **Quyết định kiến trúc**: Mở rộng `paths:` và `## Scope` của `T156` tại chỗ (`compiler/driver`, `bootstrap/axiom0/src/driver`) để `T156-impl` xử lý dứt điểm cả 20 trường hợp trong một lượt chạy và làm rỗng hoàn toàn `known_divergent.txt` trước khi sang `T086`.

---

## Root-Cause Analysis

### 1. Group A — 4 Error-Case Programs (`hir..obj` / `mir..obj`)

- **`inspect --emit=hir` on resolve-error programs (`tests/driver/error.ax`, `tests/run/parity/traits/qa_self_missing_member.ax`)**:
  - In `bootstrap/axiom0/src/driver/pipeline.c:807`, `ax_pipeline_run(&st, AX_STAGE_HIR)` continues into `stage_hir` even when `stage_resolve` recorded diagnostics (`st->sink.errors > 0`, because `st->failed` is only set on source I/O failure), so `emit_hir.c` prints the lowered HIR to `stdout`, prints the resolve diagnostics to `stderr`, and exits `AX_EXIT_DIAG` (`1`).
  - In `compiler/driver/pipeline.ax:896`, `pipeline_run_stages` halts immediately after `STAGE_RESOLVE` when `session_has_errors(view(ctx.sess))` is true, leaving `ctx.hir.items` empty on `EMIT_HIR`.
  - **Fix**: In `compiler/driver/pipeline.ax` (`driver_execute_inspect_ctx`, `EMIT_HIR` branch at line 976), when `!ok && (ctx.hir.items as usize) == 0 && (ctx.ast.items as usize) != 0`, invoke `pipeline_stage_hir(mut_view(*ctx))` before `session_render_hir_into(...)`. Checking `(ctx.ast.items as usize) != 0` preserves early stop on lex/UTF-8 errors (`check-invalid-utf8` in `qa_axiomc_cli_edges_oracle.py`).

- **`inspect --emit=mir|lir|mi|mc|obj` on resolve/typeck-error programs (`tests/driver/error.ax`, `tests/run/parity/traits/qa_self_missing_member.ax`, `tests/run/parity/diag/cannot_index.ax`, `tests/run/parity/diag/not_callable.ax`)**:
  - `bootstrap/axiom0/src/driver/emit_thir.c:385-386` captures `int rc = ax_pipeline_run(&st, AX_STAGE_TYPECK); if (rc != 0) { ax_pipeline_free(&st); free(pos_argv); return rc; }`.
  - By contrast, `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c` ignore the return value of `ax_pipeline_run(&st, AX_STAGE_TYPECK)` on the `.ax` path and only check `if (st.failed)`, returning `AX_EXIT_OK` (`0`) despite resolve/typeck errors (and in `emit_mir.c`, attempting to lower ill-typed HIR into MIR).
  - **Fix**: In `bootstrap/axiom0/src/driver/emit_{mir,lir,mi,mc,obj}.c`, capture `int rc = ax_pipeline_run(&st, AX_STAGE_TYPECK);` and return `rc` after cleanup whenever `rc != AX_EXIT_OK`, matching `emit_thir.c` and `compiler/driver/pipeline.ax`.

### 2. Group B — 16 Closure / Indirect-Call Programs at `inspect --emit=obj`

- **15 closure programs crashing in `axiom0 inspect --emit=obj`**:
  - Lifted closure functions in `st.hir.items` have `item->fn.name.v == 0`.
  - `bootstrap/axiom0/src/driver/emit_obj.c:576` unconditionally calls `ax_interner_get(&st.interner, item->fn.name)`, triggering `AX_ICE("ax_interner_get: invalid StrId 0")` (`abort()` / exit `3221226505`).
  - Meanwhile, `bootstrap/axiom0/src/driver/build_native/build.c:505-510` and `bootstrap/axiom0/src/lir/lower.c:127` format anonymous functions as `"__ax_fn_%u"` using `(uint32_t)item->fn.symbol.v`.
  - In `compiler/driver/pipeline.ax:1884`, `driver_emit_objmodel` gated `backend_alloc_anon_fn_sym` on `if is_build_mode && fname_id_v == 0u32`, emitting an empty symbol name when `is_build_mode == false`.
  - **Fix**:
    1. In `bootstrap/axiom0/src/driver/emit_obj.c:576-578`, check `if (item->fn.name.v != 0)` and otherwise format `snprintf(name_buf, 256, "__ax_fn_%u", (uint32_t)item->fn.symbol.v);`.
    2. In `compiler/driver/pipeline.ax:1884`, change `if is_build_mode && fname_id_v == 0u32` to `if fname_id_v == 0u32` so both `build` and `inspect --emit=obj` emit `"__ax_fn_%u"`.

- **Indirect register calls (`call r64`) in `bootstrap/axiom0/src/driver/emit_obj.c` (`tests/run/native_p7/qa_fn_ptr.ax` and closure indirect calls)**:
  - `bootstrap/axiom0/src/driver/emit_obj.c:175-180` (`encode_mi_to_sec`, `case AX_X64_MI_CALL:`) only handled `if (inst->msg)` and omitted indirect register calls (`else if (inst->op_count > 0 && inst->ops[0].kind == AX_X64_OP_REG)`), whereas `bootstrap/axiom0/src/driver/build_native/build.c:169-171` and `compiler/target/x64/frame.ax:693-695` (`x64_encode_mi_inst_obj`) emit `ax_x64_call_r(sec, inst->ops[0].reg)`.
  - **Fix**: Add `else if (inst->op_count > 0 && inst->ops[0].kind == AX_X64_OP_REG) { ax_x64_call_r(sec, inst->ops[0].reg); }` to `encode_mi_to_sec` in `bootstrap/axiom0/src/driver/emit_obj.c`.

---

## Options & Decision

1. **Option 1 (Chosen) — Expand `T156` `paths:` and `## Scope` in place to include `compiler/driver` and `bootstrap/axiom0/src/driver`**:
   - *Pros*: `T156` already holds uncommitted working-tree changes across `compiler/*` and `tests/selfhost/**` that resolve 100% of the frontend/MIR/THIR/diagnostic parity items. Adding `compiler/driver` and `bootstrap/axiom0/src/driver` introduces zero path overlap with other active tasks (`T086` depends on `T156`) and lets `T156-impl` finish the remaining ~25 lines of driver glue in one sitting.
   - *Cons*: Slightly widens `T156`'s path list into the driver layer.
2. **Option 2 — Split a separate blocker task before `T156`**:
   - *Rejected*: Would collide with `T156-impl`'s uncommitted working tree (`compiler/*` and regenerated `tests/selfhost/**` bundles) and add an unnecessary task-board cycle for small driver fixes directly tied to `T156`'s dump-parity acceptance criteria.
3. **Option 3 — Narrow `axiomc_e2e_oracle.py` to skip `inspect --emit=obj` or error-case `inspect` stages**:
   - *Rejected*: Violates `T156`'s explicit goal ("every `inspect --emit=<stage>` output of `INSPECT_STAGES` is identical (exit code, stdout, stderr)") and ADR-0035 §1/§4.

---

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py unblock T156` -> `unblocked T156` (`status: doing`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint _workspaces/tasks/todo/T156-dump-diagnostic-parity-registry-empty.md` -> `OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` -> `OK (240 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`

## Files changed

- _workspaces/tasks/todo/T156-dump-diagnostic-parity-registry-empty.md
