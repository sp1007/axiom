# Unblock T086 — Stage-1: axiom0 builds axiomc; axiomc passes the full suite

## Tóm tắt
- `T086` (`owner: axiom-qa`) đã hoàn thành `tools/bootstrap.py`, đo đạc ngân sách thời gian/bộ nhớ Stage-1 (`axiom0 -> axiomc1.exe` trong 25.88s, 1241.78 MB) và Stage-2 (`axiomc1 -> axiomc2.exe` trong 468.61s, 2547.53 MB) trong `tests/perf/selfhost.csv`, xác nhận 100% file `.obj` (`-O0` và `-O1`) đồng nhất từng byte trên toàn bộ 516 chương trình `tests/run`, và xác nhận 100% kiểm thử `[native]` / `[native-O1]` trong `tests/run` và `tests/std` đều ĐẠT (`WEAK-NATIVE 0`).
- Tuy nhiên, theo quy tắc cổng kiểm định của `T086` ("QA không tự vá trình biên dịch: mỗi lỗi phát hiện tạo thành một task sửa lỗi cho phần port tương ứng"), `T086` bị chặn bởi 8 nguyên nhân gốc nằm ngoài `paths:` của `T086` (chủ yếu ở bộ thông dịch MIR của bản port `run --interp`, xử lý kiểu mảng lặp `[val; N]`, trình phân tích `.mir`, shim `bundle_common.py`, và quy tắc (c) của `gatecheck.py`).
- Quyết định: tạo một task sửa lỗi tiên quyết duy nhất `T162` (`phase: P10-selfhost`, `priority: 119`, `owner: axiom-semantics`, `reviewer: axiom-qa`) bao phủ toàn bộ 8 nguyên nhân gốc và tái sinh các gói bundle tự thân (`tests/selfhost/**`).
- Cập nhật `T086` phụ thuộc vào `T162` (`depends += T162`), giữ nguyên các file đang làm dở của `T086` (`tools/bootstrap.py`, `tests/perf/selfhost.csv`, `tests/selfhost/stage1/*`), và chạy `taskctl.py unblock T086`.
- Đã kiểm tra `taskctl.py lint`, `taskctl.py validate` (241 tasks OK), `reqcov.py --strict` (COVERAGE OK), và `harness_check.py` (HARNESS OK).

## Decision
Classification: **TYPE A** (implementation bug fix task required by Stage-1 gate rule R9 / ADR-0005 §3; no language or architecture semantic change, so no ADR required).

### Root causes addressed by `T162` (from `_workspaces/reports/T086-report.md` lines 111–201)
1. **`compiler/interp/interp.ax:1389` (`exec_assign_binop`) missing `MIR_BINOP_WRAPPING_{ADD,SUB,MUL}`** — 7 `[interp]` failures (`run/numeric/intrinsic_ops.ax`, `run/intrinsics/native_repro.ax`, `run/intrinsics/ops_table.ax`, `run/parity/intrinsics/qa_intrinsics_ptr_edges.ax`, `run/parity/intrinsics/wrapping.ax`, `selfhost/kernel/hash_native.ax`, `std/core/qa_hash_vectors.ax`).
2. **`compiler/mir/builder.ax:9665` leaves unreachable join blocks (`bb_end`) with `MIR_TERM_NONE` + `tests/selfhost/bundle_common.py:505` (`_shim_mir_build_fn`) omits `"compiler.interp_opt.session"`** — 43 `[interp]` failures with `AX_VERIFY_UNTERMINATED_BLOCK`.
3. **`tests/selfhost/bundle_common.py:90-95` (`_shim_diag_sink_report`) blanket-suppresses `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (`2021u16`) in `compiler.types.typeck`** instead of removing the duplicate `HIR_ITEM_STATIC` report at `compiler/types/typeck.ax:6754` — 4 failures (`conformance/vs0/float_unsupported.ax`, `ui/numeric/float_bootstrap.ax`, `ui/typeck/bug_float_unsupported.ax`, `selfhost/stage1/stage1_bootstrap.test`).
4. **`compiler/types/typeck.ax:5556-5572, 6631-6652` & `compiler/verify/verifier.ax:553-613` leave `TY_INT_VAR` unresolved inside array repeat types `[N]?int`** — 1 failure (`conformance/std/0169_std_collections_map.ax` on `slots: [0u8; 16]`).
5. **`compiler/mir/mir.ax:2232-2351` (`mp_parse_operand`) missing default `MIR_OP_COPY` fallback for bare places** — 1 failure (`lir/load.test` on `_0 = (*_1);`).
6. **`compiler/driver/pipeline.ax:896, 1966-1970` & `compiler/interp_opt/session.ax:1401`** overwriting interpreter exit codes `124`/`125` with `AX_EXIT_DIAG` (`1`) and not populating host CLI args `[main_path, ...run_args]` via `interp_host_push_arg` — 4 `[interp]` failures (`run/basic/008-step-limit.ax`, `run/basic/009-call-depth.ax`, `run/host/heap/use_after_free.ax`, `run/host/io/args.ax`).
7. **`compiler/interp_opt/session.ax:1132-1157, 1220-1246` (`insert_impl_alias_in_mir_map`) aliasing `HIR_ITEM_TRAIT` default methods with `T161` `HIR_ITEM_IMPL` instances in `mir_map`** — 9 `[interp]` failures in `run/parity/trait_default/*.ax`.
8. **`tests/encode/axiom/gnu_as_vectors.ax` `gatecheck.py` rule (c) violation (154 inline `// xfail: AX0-FIX-ENC-...` comments inside `fn main()`) & `tests/selfhost/obj_link_driver/qa_axiomc_cli_edges.test` outdated `diverge=3` expectation after `T154`**.

### Options considered
1. **Create a single prerequisite fix task `T162` (`owner: axiom-semantics`, `priority: 119`) covering all 8 localized fixes and bundle regeneration** — **chosen**. Every one of the 8 root causes is already pinpointed to exact lines in `T086-report.md` (~10–25 lines of change each, < 200 lines of logic total plus bundle regeneration). Grouping them into one prerequisite task avoids regenerating the 121-module selfhost bundles multiple times and lets `T086` re-run immediately after `T162` is accepted.
2. **Split into multiple small fix tasks per compiler directory** — rejected: every change in `compiler/**` or `tests/selfhost/bundle_common.py` requires regenerating all selfhost bundles (`tests/selfhost/**`) and rebuilding `axiomc1` to verify, which would serialize the tasks on `tests/selfhost` anyway and multiply bundle churn.
3. **Add `compiler/**` to `T086` `paths:`** — rejected: violates `T086`'s explicit acceptance criterion ("QA does not patch the compiler: each failure becomes a fix task for the owning port task (filed by the architect); the gate closes only when they are done").

## Board changes
- Reserved `T162` via `taskctl.py new-id --phase P10-selfhost`.
- Created `_workspaces/tasks/todo/T162-stage1-selfhost-suite-parity-and-interp-fixes.md` (`priority: 119`, `owner: axiom-semantics`, `reviewer: axiom-qa`, `model: opus`, `gate_model: sonnet`, `depends: [T085, T143, T144, T156, T159, T161]`, `paths: [compiler/interp, compiler/interp_opt, compiler/mir, compiler/types, compiler/verify, compiler/driver, tests/selfhost, tests/encode/axiom, tests/run/parity]`, `covers: [REQ-OWN-001, REQ-OWN-002]`).
- Updated `_workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md`: added `T162` to `depends:` and ran `taskctl.py unblock T086`.
- Updated `spec/ROADMAP.md` §5 change log with the `2026-11-01` entry for `T162` (`unblock-T086`).

## Files changed
- _workspaces/tasks/todo/T162-stage1-selfhost-suite-parity-and-interp-fixes.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- spec/ROADMAP.md
- _workspaces/reports/unblock-T086.md
