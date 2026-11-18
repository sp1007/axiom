# Unblock T491 — stage-1 axiomc1 crash is an axiom0 miscompile

## Tóm tắt
- Nguyên nhân gốc của lỗi axiomc1 (stage 1) crash 0xC0000005 nằm trong axiom0 đã đóng băng, không phải trong `compiler/`:
  `bootstrap/axiom0/src/driver/build_native/build.c` dùng mảng cố định `bb_offsets[1024]` / `fixups[1024]` không kiểm tra
  giới hạn. Hàm `exec_assign_binop` của axiomc có 1076 lệnh nhảy nên bị biên dịch sai âm thầm (65 lệnh nhảy ra ngoài hàm).
- Đây là lỗi biên dịch sai âm thầm ở gốc tin cậy của bootstrap nên tạo task T166 **AX0-FIX-11**, ưu tiên 0, không phụ thuộc,
  P10, owner axiom-backend, model opus / gate opus.
- T166: cấp phát hai mảng theo kích thước hàm, kiểm tra đích nhảy, rà soát mọi buffer cố định trong `build_native/`, thêm
  test hồi quy (>1024 và >4096 lệnh nhảy), giữ điểm bất động stage 1-3, gỡ `axiomc_e2e.test` khỏi baseline.
- Không chọn cách tách `exec_assign_binop` trong `compiler/` vì chỉ che lỗi, hàm lớn tiếp theo sẽ lại hỏng.
- T491 không cần sửa code → đóng bằng `supersede` bởi T166. T165 (axiomc1 `run --interp` crash, rất có thể cùng lỗi) nay
  phụ thuộc T166 và chỉ cần kiểm lại sau khi sửa.
- Đã ghi vào nhật ký ROADMAP; validate, reqcov `--strict`, harness_check đều đạt.

## Blocker
T491-impl (report `_workspaces/reports/T491-report.md`) traced the axiomc1 crash with gdb/objdump to
`bootstrap/axiom0/src/driver/build_native/build.c:515-516`: fixed, unchecked `bb_offsets[1024]` and `fixups[1024]`.
`exec_assign_binop` (`compiler/interp/interp.ax:2597`) has 1076 fixups; overflowing pairs overwrite `bb_offsets[]`, so
65 jumps target section offsets equal to block indices. axiomc2 is unaffected (axiomc's backend has no fixed limit).
The task forbade editing `bootstrap/axiom0` (frozen), so it blocked correctly (scope case (b)).

## Decision
Classification: TYPE A defect in the frozen bootstrap (no spec change, no ADR needed — ROADMAP R3 freeze procedure:
a defect fix in axiom0 goes through an `AX0-FIX` task).

Options considered:
1. **New AX0-FIX task fixing axiom0 (chosen).** Removes the root cause; any later large function (the ported compiler
   keeps growing) would otherwise be silently miscompiled by stage 1, and stage 1 is the trust root.
2. Split `exec_assign_binop` in `compiler/interp/interp.ax` below 1024 fixups. Rejected: hides a silent miscompile that
   recurs, and leaves axiom0 able to emit wrong code without any diagnostic.
3. Raise the constant (e.g. 8192). Rejected: still unchecked; same failure class at a larger size.

Board changes:
- New `T166` — `AX0-FIX-11` branch-fixup capacity (P10-selfhost, priority 0, `depends: []`, owner axiom-backend,
  reviewer axiom-qa, model opus, gate_model opus; paths `bootstrap/axiom0/src/driver/build_native`,
  `tests/run/parity/backend/many_branch_fixups.ax`, `tests/build_native`, `_workspaces/baseline-failures.txt`;
  covers REQ-BOOT-003, REQ-BLD-028). Acceptance: repro test passes interp/native/native-O1 under axiom0 and axiomc2;
  >4096-jump stress test; audit list of every fixed buffer in `build_native/`; stage 1-3 fixed point from the rebuilt
  axiom0; `axiomc_e2e.test` and `scalar_const.ax` (plus the two parity programs) pass under axiomc1; baseline id removed;
  byte-identical output for programs below the old limits.
- `T491` superseded by `T166` (`taskctl.py supersede T491 --by T166`; moved to done). Nothing remains for T491: the two
  parity programs are correct and stay unchanged, and its baseline removal moves to T166. No task depended on T491.
- `_workspaces/baseline-failures.txt`: `selfhost/obj_link_driver/axiomc_e2e.test` now classed
  `regression:ax0-fixup-cap`, fix task `T166` (T166 removes the line).
- `T165` (axiomc1 `run --interp` segfault investigation) now depends on `T166`; log note: re-run the repro on the fixed
  axiom0 first and close as classification (a) if the crash is gone.
- `spec/ROADMAP.md` change log row 2026-11-19.

Checks: `taskctl.py validate` OK (709 tasks); `reqcov.py --strict` COVERAGE OK, gaps 0; `harness_check.py` HARNESS OK.

Risk: the fix touches the emitter of every native function; the byte-identical spot check in T166's acceptance guards
against collateral changes. T166 rebuilds axiom0, so other running gates on the old axiom0 are unaffected until accept.

## Files changed
- _workspaces/tasks/todo/T166-ax0-fix-11-branch-fixup-capacity.md
- _workspaces/tasks/todo/T491-fix-stage1-axiomc1-crash-on-parity-programs.md
- _workspaces/tasks/done/T491-fix-stage1-axiomc1-crash-on-parity-programs.md
- _workspaces/tasks/todo/T165-investigate-axiomc1-run-interp-segfault.md
- _workspaces/reports/T491-report.md
- spec/ROADMAP.md
- _workspaces/reports/unblock-T491.md

## Orchestrator note
The baseline relabel (axiomc_e2e.test: T491 -> T166) was not committed here because `_workspaces/baseline-failures.txt` is in the paths of running task T490; T166 removes that line when it lands (its acceptance), so the T491 label stays until then.
