# triage-1122 — Follow-up triage (architect, 2026-11-22)

## Tóm tắt
Đã rà 7 nhóm follow-up từ báo cáo T498b/T423f/T423b/T496a/T498c/T497a và fullrun-3. Mỗi mục được kiểm lại trên cây hiện tại
(đọc mã + chạy repro nhỏ trong thư mục scratch bằng compiler stage-2 mới nhất trong compiler-cache, không build trong cây chính).
Kết quả: 12 task mới (10 ở P12, 2 ở P13), 1 ADR (ADR-0048), làm rõ SPEC-10 AXS-OWN-006, cập nhật nhật ký ROADMAP.
Phát hiện thêm khi tái hiện: gán qua chỉ số vào biến `let` không `mut` vẫn được chấp nhận (T498f); `use std.<module>` bất kỳ
ngoài prelude không nạp được (gộp vào T423h cùng lỗi `__ax_host_exit`); `static` thường cũng bị từ chối (T537).

| # | Follow-up | Quyết định | Task |
|---|-----------|------------|------|
| 1a | Mảng đã move, `hs[0].n = 5` / `hs[0] = mk()` được chấp nhận và khởi tạo lại cả mảng | Task mới (lỗ hổng sở hữu, ưu tiên 10); làm rõ SPEC-10 AXS-OWN-006: ghi qua chỉ số không khôi phục gì | T498e |
| 1b | `own.move.resolve_place` không còn ai gọi | Gộp vào T498e | T498e |
| 1c | Use-after-move trong biểu thức nhị phân báo ở đầu biểu thức | Gộp vào task mới T498f (cùng tái hiện: gán qua chỉ số vào `let` bất biến được chấp nhận) | T498f |
| 2 | `tests/smoke.list` thiếu pool `tools`, `build_native` | Task vệ sinh test (ưu tiên 45) + taskgate chạy `--smoke --check` | T423g |
| 3a | `axiom_panic` không phân biệt panic với `exit(101)` của người dùng | Task mới P13: khe hook panic do linker cấp, bỏ móc IAT ExitProcess | T538 |
| 3b | `static mut` toàn tiến trình bị typeck từ chối (std phải giấu trạng thái trong ILT) | Task mới P13 (cả `static` thường cũng bị từ chối; chưa task nào làm); T501/T526/T554 phụ thuộc | T537 (+ gỡ ILT ở T538) |
| 3c | Native `std.core.host.exit` thiếu `__ax_host_exit` khi link | ADR-0048 + task: nạp module std theo nhu cầu, tự thêm module cung cấp host như ADR-0002 §3 | T423h |
| 4a | Lỗi `a..=` nằm ở hir/lower.ax thay vì parser | Task dọn dẹp (ưu tiên 48) | T496b |
| 4b | Chưa có test `str[a..=b]` | Gộp vào T496b | T496b |
| 5a | Đối số `[262144]u8` theo trị làm exe native sập | Không phải lỗi an toàn: tràn stack 1 MB mặc định đúng ADR-0003 (0xC00000FD, `--stack-reserve 4 MB` chạy được); lỗi thật là ~4 bản sao → task tối ưu | T498h |
| 5b | `swap` trên kiểu mảng chỉ đổi phần tử đầu (interp và native) | Task mới (sai âm thầm, ưu tiên 11); gốc ở `ptr_copy_nonoverlapping<[4]u32>(..,1)` chỉ chép 4 byte | T498g |
| 5c | Chú thích cũ về giới hạn 256 byte trong `large_and_edge.ax` | Gộp vào T498h | T498h |
| 6 | Test perf tỉ lệ thời gian một lần đo bị chập chờn khi máy tải | Task vệ sinh test: lấy min của 3 lần đo | T494a |
| 7a | `inspect --emit=mc` in MOV 8 byte sai | Task: `--emit=mc` dùng bộ mã hoá của đường object, xoá encoder cũ | T453b |
| 7b | Kiểm tra đầy đủ (exhaust.ax) sai với pattern tuple | Task mới (từ chối chương trình hợp lệ, ưu tiên 18) | T499b |

Không task nào trong `doing/` bị sửa; task đụng `typeck.ax`/`mir/builder.ax` (T498f, T498g, T498h, T537) phụ thuộc T448.
T224 vẫn deferred; không yêu cầu OWNER.md nào bị bỏ.

## Verification (architect repros)
Scratch dir: `<scratchpad>/tri`, compiler `_workspaces/artifacts/compiler-cache/axiomc2_O1_a93e72cb41aca1d5.exe` (newest
cached stage-2; `build/axiomc2.exe` is stale vs std), `--std-root D:/projects/compiler/new lang/std`.
1. `let hs: [2]H = ..; let t = hs; hs[0].n = 5u32; let u = hs[1].n;` → compiles and prints 1 (interp and native). Same with
   `hs[0] = mk()`. Plain struct `let mut s; let t = s; s.n = 5; s.m` → correctly `AX_MOVE_USE_AFTER_MOVE` (field-path reinit).
   `let a: [2]u32 = ..; a[0] = 9u32;` (no `mut`) → accepted, prints 9; `s.n = 5` on immutable `let s` → `AX_TYPE_ASSIGN_IMMUTABLE`.
   Root cause in typeck: the assignment place walk handles FIELD / DEREF / TUPLE_INDEX but stops at INDEX.
   `let u = 1u32 + hs[i].n;` after move → error at col of `1u32`. `grep resolve_place` → only definition + re-export in
   `compiler/own/mod.ax` (and regenerated selfhost bundles).
2. `python tools/axtest.py --smoke --check` → `SMOKE-CHECK PROBLEM group build_native/tools has no pool entry`, `FAILED (2)`.
3. `use std.core.host.exit; exit(3)` → interp exit 3; `build` → `AX_LINK_UNDEFINED_SYMBOL: __ax_host_exit` (also
   `args_count`). `use std.core.mem.swap` / `std.core.cmp.min` / `std.process.exit` → `AX_NAME_UNRESOLVED_IMPORT`: the driver
   only special-cases prelude/option/result/host/future/atomic (`compiler/driver/pipeline.ax`). `static Y: u32 = 5u32` and
   `static mut X: u32 = 0u32` → `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`. ExitProcess(101) containment confirmed by T423b-qa.
4. `emit_inclusive_range_without_end` is in `compiler/hir/lower.ax`; no `str` test in `tests/run/slice_inclusive`.
5. `fn huge(a: [262144]u8, ..)` → native exit 0xC00000FD (STATUS_STACK_OVERFLOW) at -O0 and -O1; `[200000]u8` passes;
   `--stack-reserve 4194304` passes; PE `SizeOfStackReserve` 0x100000 (ADR-0003 default). Copy of `swap` body with
   `[4]u32` → `size_of=16`, result `p=[10,2,3,4]`, `q=[1,..,40]` in interp and native.
6. fullrun-3 §4: `build_scaling_o1` ratio 5.08 > 5.00 single-shot, passes 3/3 isolated.
7. `compiler/target/x64/frame.ax` `x64_encode_mi_inst_mc` hard-codes width 8 for MOV. `match t { (p, q) => 3 }` and
   `(true, q)`/`(false, q)` → `AX_PAT_NON_EXHAUSTIVE`.

## Decisions

| Task | Owner / model / gate | Prio | Depends | Paths (locks) |
|------|----------------------|------|---------|---------------|
| T498e | axiom-semantics / opus / sonnet | 10 | T498b | compiler/own/{init,move,mod}.ax, tests/{ui,run}/own_index_moved |
| T498f | axiom-semantics / opus / sonnet | 14 | T498b, T448 | compiler/types/typeck.ax, compiler/mir/builder.ax, tests/ui/{assign_immutable_index,own_operand_span} |
| T498g | axiom-semantics / opus / sonnet | 11 | T498c, T448 | compiler/mir/builder.ax, compiler/types/typeck.ax, compiler/interp, compiler/lir/builder.ax, tests/run/mem_generic_array |
| T498h | axiom-backend / opus / sonnet | 60 | T498c, T498a, T448 | compiler/{mir,lir}/builder.ax, compiler/abi/win64.ax, compiler/target/x64/frame.ax, tests/run/agg_arg_copies, tests/run/array_copy/large_and_edge.ax |
| T499b | axiom-semantics / opus / sonnet | 18 | T499a | compiler/types/exhaust.ax, tests/{ui,run}/exhaust_tuple, tests/run/tuple_expr_names/match_and_destructure.ax |
| T423h | axiom-frontend / opus / sonnet | 25 | T423b, T437b | compiler/driver/{pipeline,opts}.ax, tests/modules/std_on_demand, tests/run/host (locks diag code.ax, explain) |
| T423g | axiom-qa / sonnet / sonnet (reviewer architect) | 45 | T423f | tests/smoke.list, tools/taskgate.py, tests/tools/taskgate_smoke_check |
| T494a | axiom-qa / sonnet / sonnet (reviewer architect) | 46 | T494 | tests/perf/build_scaling/*, tests/perf/own_scaling/* (scripts + .test) |
| T496b | axiom-frontend / sonnet / sonnet | 48 | T496a | compiler/syntax/parse.ax, compiler/hir/lower.ax, tests/ui/slice_inclusive, tests/run/slice_inclusive_str, tests/parse/range_inclusive |
| T453b | axiom-backend / sonnet / sonnet | 50 | T453, T498a | compiler/target/x64/frame.ax, tests/mc |
| T537 | axiom-semantics / opus / opus | 140 | T423b, T448 | typeck.ax, mir/builder.ax, compiler/interp, lir/builder.ax, compiler/obj, link/{linker,pe}.ax, tests/{run,ui}/static_items (lock code.ax) |
| T538 | axiom-backend / opus / opus | 145 | T537, T423h | compiler/link/import.ax, std/sys/windows/{fiber,thread}.ax, tests (locks linker.ax, fiber gen_tests.py) |

Board edits: T312 depends += T498e, T498f, T498g, T499b, T423h; T313 += T537, T538; T501, T526, T554 += T537; T523 += T538.
Spec: SPEC-10 AXS-OWN-006 clarified (reinit restores only the assigned path; indexed writes require the array OWNED;
sources 0540 §130 AOWNENG-30, 0124 §15 AOWN-37) with two test-matrix rows; ADR-0048 (std modules on demand via a header
index; host providers added for native builds). ROADMAP change log row added.

Not filed: T497a-qa N1 (oracle tests reading `compiler/` without `nocache:`) and N2 (`check --json` to stderr) — not in the
orchestrator's list; N1 is already covered by the axiom-qa G1 cache-hygiene rule.

Checks: `taskctl.py lint` OK for all 12 files; `taskctl.py validate` OK (744 tasks); `harness_check.py` HARNESS OK (only the
known optional-guard WARN); `reqcov.py --strict` COVERAGE OK, gaps 0.

## Files changed
- spec/SPEC-10-ownership.md
- spec/decisions/ADR-0048-std-module-loading-host-providers.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T498e-fix-own-index-write-after-array-move-reinitialises-whole-array.md
- _workspaces/tasks/todo/T498f-fix-index-assignment-into-immutable-binding-accepted.md
- _workspaces/tasks/todo/T498g-fix-ptr-copy-of-array-type-copies-one-element.md
- _workspaces/tasks/todo/T498h-by-value-aggregate-argument-copy-count.md
- _workspaces/tasks/todo/T499b-fix-exhaustiveness-of-tuple-patterns.md
- _workspaces/tasks/todo/T423g-smoke-list-pools-for-tools-and-build-native.md
- _workspaces/tasks/todo/T423h-driver-std-modules-on-demand-and-host-providers.md
- _workspaces/tasks/todo/T494a-perf-scaling-tests-robust-timing-under-load.md
- _workspaces/tasks/todo/T496b-inclusive-range-without-end-diagnosed-in-parser.md
- _workspaces/tasks/todo/T453b-inspect-emit-mc-uses-object-encoder.md
- _workspaces/tasks/todo/T537-e13-1-process-wide-static-and-static-mut-items.md
- _workspaces/tasks/todo/T538-e13-5-native-panic-hook-slot-replaces-exitprocess-iat-hooks.md
- _workspaces/tasks/todo/T312-phase-p12-gate-numeric-floating-point-simd.md
- _workspaces/tasks/todo/T313-phase-p13-gate-low-level-systems-unsafe-freestanding-securit.md
- _workspaces/tasks/todo/T501-e13-1-typeck-mir-unsafe-provenance-req-owner-008.md
- _workspaces/tasks/todo/T523-e13-5-native-landing-pads-win64-seh-drop-unwinding.md
- _workspaces/tasks/todo/T526-e13-6-at-addr-hir-sema-mir-overlap-layout.md
- _workspaces/tasks/todo/T554-e14-1-native-materialization-comptime-tables-sections.md
- _workspaces/reports/triage-1122.md
