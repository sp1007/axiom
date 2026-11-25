# Unblock T428a — 2026-11-26 (architect)

## Tóm tắt
- T428a (giữ địa chỉ biến cục bộ của `async fn` qua `.await`) đã xong vòng sửa 1; gate chỉ còn hỏng 2 test e11_5
  (`spawn_affinity_vs_migration.ax`, `fiber_in_async_and_threads.ax`). Đây là lỗi **có sẵn** của compiler, không do T428a:
  typeck tra tên kiểu bằng cách duyệt mọi item của toàn chương trình theo **tên trần** (`lookup_path_type_by_name`), nên hai
  struct cùng tên ở hai module (`std.io.String` và `std.text.string.String`, hoặc `String`/`IoError` của người dùng) bị lẫn
  nhau. Kiến trúc sư tự tái hiện bằng chương trình 3 dòng với compiler HEAD. Hai test trước đây qua chỉ vì bundle cũ.
- Quyết định: nhận 2 id vào `_workspaces/baseline-failures.txt` (thêm trực tiếp trong cây chính; file này đã nằm trong change
  set của T428a nên đi vào **đúng một** commit — commit của T428a) và tạo task sửa T428g (typeck dùng ràng buộc của resolver,
  không dùng tên trần). Thêm T428l: std chỉ còn một kiểu `String` (std.io/env/process/utf16 dùng `std.text.string.String`).
- Đã `taskctl unblock T428a` → task quay lại hàng đợi để chạy gate.
- Phân loại các việc tồn đọng: tạo 9 task khác (T428h cờ drop qua `.await`; T428i `static mut` + atomic trong async;
  T428j gán aggregate đọc chính đích; T428k oracle không tất định; T461a crash chương trình native lớn; T461b gọi phương
  thức trên literal số; T461c `skip-unless: pymodule`; T449c chi phí mỗi tick executor dưới interpreter).
- Sửa spec: SPEC-41 (chữ ký `parse_*` nhận `view<[u8]>`, ngưỡng định dạng ngắn nhất, dấu của `-0.00`, `fract(-0.0) = +0.0`,
  khoảng giá trị `rem_euclid` có thể bằng `|b|` do làm tròn, `log(x, 1) = NaN`, quy tắc receiver literal); SPEC-33 (nghĩa
  "storage-live" và cờ drop thuộc trạng thái). ADR-0051: gọi phương thức trên literal số chưa hậu tố thì áp kiểu mặc định
  (`f64`/`i32`) cho bộ nhận trước khi tra. Không có quyết định rủi ro cao.

## Blocker analysis
- Evidence: `T428a-report.md` "Round 1 / BLOCKER", `_workspaces/T428a_taskgate_r1.log` (`NEW FAILURES:` exactly the two ids).
- Architect repro (snapshot compiler `build-snap-T428a/build/axiomc2.exe`, live `std/`, `check --std-root <abs std>`):
  | program | result |
  |---|---|
  | `use std.thread.spawn` + `use std.asyn.executor.Executor` | AX_TYPE_MISMATCH `std/io/io.ax:264` |
  | `use std.text.string.String` + `use std.io.read_to_string` | AX_TYPE_MISMATCH `std/io/io.ax:264` |
  | `use std.thread.spawn` + `use std.io.read_to_string` | AX_TYPE_MISMATCH `std/text/string.ax:290` (order-dependent) |
  | `use std.io.read_to_string` + user `struct String` | AX_TYPE_MISMATCH `std/io/io.ax:264` |
  | `use std.io.read_to_string` + user `struct IoError` | AX_TYPE_MISMATCH `std/io/io.ax:161` |
  | `use std.io.read_to_string` + user `fn string_new` | OK |
  | `use std.io.read_to_string` alone | OK |
- Cause: `compiler/types/typeck.ax` `lookup_path_type_by_name` (≈ line 5357) walks `(*cx.hir).items` and returns the
  first `HIR_ITEM_STRUCT` whose bare name matches, ignoring `HirPath.symbol/def_mod/def_name` (T164/T492). Struct identity
  is `def + args` (T444), so the wrong `String` is a different type. This is a nominal-identity bug (REQ-TYP-072,
  REQ-MOD-003), owner axiom-semantics → **T428g**.
- Options considered: (a) fix the resolver — rejected, the resolver already binds the path correctly; (b) std-only
  layering fix (one `String`) — it removes this instance but leaves user programs broken (user `struct String` /
  `IoError` collide with std), so it is a separate cleanup (**T428l**, after T428g); (c) typeck fix — chosen.
  (d) relaxing the gate — not allowed.

## Baseline coordination
- I added the two ids (with a comment block citing this report) to `_workspaces/baseline-failures.txt` **in the main
  tree**. T428a already edits that file (removes its 3 T449a lines) and lists it in its `## Files changed` and `locks:`,
  so the gate snapshot and `taskctl accept T428a` pick up my lines in T428a's commit. The file is therefore **not** in my
  Files changed below; do not stage it with this report. T428g (depends T428a, locks the file) removes the two lines.

## Tasks created
| id | phase | owner / model | what | source |
|---|---|---|---|---|
| T428g | P11 | semantics / opus | typeck type paths use the resolver binding, not bare names; removes the 2 baseline lines | this blocker |
| T428h | P11 | semantics / opus | drop flags of async locals are state (no double drop / uninit drop) | T428a-qa defect 1 |
| T428i | P11 | semantics / opus | `static mut` never copied into the poll frame; atomic stmts renamed + live (REQ-ASY-082) | T428a-qa defects 2-3 |
| T428j | P11 | semantics / opus | aggregate assigned to a place it reads: operands first (`arr = [arr[2], ..]`) | T428a-qa defect 5 |
| T428k | P11 | semantics / opus | oracle nondeterminism "polling a completed Future state machine" | T428a-qa defect 6 |
| T428l | P11 | stdlib / sonnet (gate opus) | one `String` type in std | this blocker (layering half) |
| T449c | P11 | stdlib / sonnet | executor tick cost under the interpreter; MIR-step budget test | T449a-qa F3 |
| T461a | P12 | backend / opus (gate sonnet) | native crash of a ~33k-statement program (0xC0000005) | T461-qa N4 |
| T461b | P12 | semantics / sonnet | method call on unsuffixed numeric literal (ADR-0051) | T461-qa N5 |
| T461c | P12 | qa / sonnet | `skip-unless: pymodule <name>` for the mpmath checks | T461-qa N1 |

Ids: `new-id --phase P11/P12` reports both blocks full, so suffix ids of the originating task are used. Duplicate check:
grep of todo/doing for each defect found no existing task (T428b covers the awaited sub-future drop, not drop flags;
T541 is an extern/method symbol clash, not type lookup).

## Spec decisions (no task needed)
- SPEC-41 AXS-FLT-004 item 6: `fract(x)` is exactly `x - trunc(x)`; every zero result is `+0.0` (`fract(-0.0) == +0.0`);
  `modf` stays the sign-carrying variant (T460-qa follow-up 3; matches the implementation and vectors).
- SPEC-41 AXS-FLT-051: shortest-notation thresholds (plain decimal for `±0.0` and `1e-4 <= |x| < 1e16`, else
  `d[.ddd]e[-]N`), and fixed mode keeps the sign of a value that rounds to zero (`-0.00`) (T460-qa D1, follow-up 3).
- SPEC-41 AXS-FLT-052: `parse_f32/f64(bytes: view<[u8]>)` plus `_str(view<String>)` and `unsafe _raw(text, count)`
  are the normative signatures (T460-qa D2); no overloading later (REQ-RES-074).
- SPEC-41 AXS-FLT-062: `rem_euclid` is `r = a % b; if r < 0 { r + |b| }`, result in `[0, |b|]` (equals `|b|` only by
  rounding, e.g. `rem_euclid(-1e-20, 3.0) == 3.0`) (T461-qa N3). AXS-FLT-063: `log(x, 1.0)` is `NaN`.
- SPEC-41 AXS-FLT-003 item 2 + **ADR-0051**: an unconstrained numeric literal receiver is defaulted (`f64`/`i32`) before
  method/field lookup. Options (default / reject like Rust E0689 / defer) in the ADR. Revisit: no.
- SPEC-33 AXS-ASY-043 item 7: "live across" means storage-live; drop flags are part of the state (points to T428h).

## Not turned into tasks
- T461-qa N2 / T460-qa follow-up 4 (wording of the "native-only heavy test" rule in axiom-testing): harness text, not a
  board item; left for the next harness review (no behaviour depends on it).
- T460-qa follow-up 2 (`std.core.float` not in prelude): T461 is done and `std.math` imports it; no open defect.
- T428a-qa item 7 (`verify_mir_own/cap` skip async-lowered bodies): already noted in T428a's report; not in my triage
  list — left for the P11 gate review T311.

## Board checks
- `taskctl.py lint` OK for all 10 new task files; `taskctl.py unblock T428a` → `unblocked T428a` (cycle 1);
  `taskctl.py validate` → `OK (774 tasks)`; `harness_check.py` → `HARNESS OK` (only the standing optional-guard-hook WARN);
  `reqcov.py --strict` → `gaps: 0`, `COVERAGE OK`.
- Housekeeping: `taskctl.py adr-next` was invoked once with `--help`, which reserved ADR-0051 as `ADR-0051-help.md`;
  the file was renamed to `ADR-0051-numeric-literal-method-receiver.md` and used for the decision above (the
  number lock `adr-0051` matches it). No orphan ADR file remains.

## Files changed
- _workspaces/reports/unblock-T428a.md
- _workspaces/tasks/todo/T428a-fix-async-address-observable-locals-stable-across-await.md
- _workspaces/tasks/todo/T428g-fix-typeck-type-lookup-by-bare-name-cross-module-collision.md
- _workspaces/tasks/todo/T428h-fix-async-drop-flags-across-await.md
- _workspaces/tasks/todo/T428i-fix-static-mut-and-atomics-in-async-fn.md
- _workspaces/tasks/todo/T428j-fix-aggregate-assignment-reading-its-own-destination.md
- _workspaces/tasks/todo/T428k-fix-oracle-nondeterministic-polling-completed-future.md
- _workspaces/tasks/todo/T428l-std-single-string-type-io-env-process-utf16.md
- _workspaces/tasks/todo/T449c-perf-executor-tick-cost-under-interpreter.md
- _workspaces/tasks/todo/T461a-fix-native-crash-large-program-33k-statements.md
- _workspaces/tasks/todo/T461b-typeck-method-call-on-unsuffixed-numeric-literal.md
- _workspaces/tasks/todo/T461c-axtest-skip-unless-python-module.md
- spec/SPEC-33-async.md
- spec/SPEC-41-floating-point.md
- spec/decisions/ADR-0051-numeric-literal-method-receiver.md
