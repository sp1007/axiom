# Triage 2026-11-26 — two pre-existing failures found by the T544 gate

## Tóm tắt
- Hai test hỏng sẵn ở HEAD (7ed14320) chưa có trong baseline, đều do **oracle của test** sai giả định chứ không phải lỗi compiler.
- `qa_t442_obj_link_driver_bounds.test`: oracle đòi `_workspaces/baseline-failures.txt` phải rỗng, nên hỏng bất cứ khi nào baseline còn dòng nào. Một test không được phụ thuộc trạng thái board. Sửa: bỏ hẳn kiểm tra baseline khỏi oracle (giữ kiểm tra file tạm) — task **T546**.
- `stage1_bootstrap.test`: bước `step2:check-json` so `axiom0` với `axiomc` trên `tests/ui/typeck/bug_float_unsupported.ax`. Từ T457 (5ee8652a, 24/11) axiomc hỗ trợ f32/f64 và báo `AX_TYPE_MISMATCH`; axiom0 đã đóng băng nên vẫn báo 3 lần `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`. SPEC-41 AXS-FLT-001 quy tắc 2 quy định đúng như vậy: cả hai bên đều đúng, chỉ oracle sai khi đòi parity cho tính năng sau đóng băng. Sửa: oracle bỏ qua file mà axiom0 tự báo nằm ngoài tập bootstrap rồi lấy file kế tiếp để bù — task **T547**.
- Chạy lại toàn bộ 24 file mẫu (axiom0 so với axiomc dựng từ HEAD): chỉ có file float này lệch.
- Cả hai id đã được thêm vào baseline kèm bằng chứng. Hai task fix có ưu tiên thường (20) vì không chặn gate nào. Không đụng file nào của T428m. Không commit.

## 1. selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test

Evidence: `_workspaces/reports/T544-qa.md` "Pre-existing failures (not in baseline)". The oracle
`tests/selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds_oracle.py` `check_baseline_and_temp_cleanup`
(line 210–223) fails when `_workspaces/baseline-failures.txt` has any non-comment line. It is the last step of `main()`;
every real check before it (generators, bundle headers/stdout, blobs vs live compiler) passes. It came in with T442
(ef0f0609), where "T442 emptied its own baseline lines" was a one-time acceptance item that got frozen into a permanent
test. The baseline is a living list (ADR-0041), so this test fails by construction on every HEAD with an open fix task.

Options:
- (a) Keep the baseline empty: not possible. Fix tasks are always open.
- (b) Narrow the check to "no obj_link_driver ids in the baseline": the test still depends on `_workspaces/` board state,
  and it duplicates the gate rule.
- (c) Remove the baseline check and keep the temp-artifact check. **Chosen.** It is the simplest option and puts the
  test back on what it actually tests.

Classification: TYPE A (test bug). Fix task **T546** (axiom-qa, sonnet, P13, priority 20; paths: the oracle; lock:
baseline file).

## 2. selfhost/stage1/stage1_bootstrap.test

Evidence: `_workspaces/reports/T544-qa.md` (byte-identical `check --json` from the HEAD-built
`axiomc2_O1_c8d9621632f121f5.exe` and the T544 snapshot build).

Introducing commit: **5ee8652a (T457, 2026-11-24)**. It changed `tests/ui/typeck/bug_float_unsupported.ax` from three
`//~ ERROR AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` to one `//~ ERROR AX_TYPE_MISMATCH` (`let b: f32 = 2`, SPEC-41
AXS-FLT-035 rule 1) and enabled f32/f64 in the Axiom typeck. `stage1_oracle.py` was last changed in 8cbfdd16 (T436),
and axiom0 has been frozen since T087. Before T457 both compilers agreed. `stage1_bootstrap` is a `tests/selfhost`
id, which is outside the per-task gate (Tier-2 full runs only), so the T457 gate did not run it.

Which side is right: **both**. SPEC-41 AXS-FLT-001 rule 2 says that axiom0 rejects f32/f64/float literals with
`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` and that axiomc (T457+) fully enables them. The oracle's assumption that every
sampled UI file (the first 3 per `tests/ui/<cat>/*.ax` glob) has stage-0 parity stopped holding once the first
post-freeze feature landed.

The architect's check: all 24 sampled files (`collect_sample` with `UI_DIAG_PATTERNS` and `RUN_PARITY_PATTERNS`, 3 per
pattern) were run through `build/axiom0.exe` and `axiomc2_O1_c8d9621632f121f5.exe` with the oracle's own
`canonical_json_diag`. Result: `files 24 diff 1`, and the only diff is `bug_float_unsupported.ax` (axiom0
`[UNSUPPORTED_IN_BOOTSTRAP x3]`, axiomc `[AX_TYPE_MISMATCH]`). Steps 3–4 of the oracle have not run since then. T547
must run them to the end.

Options:
- (a) Revert the UI test to the axiom0 expectation: wrong, because it contradicts SPEC-41 for axiomc.
- (b) Change axiom0: forbidden, axiom0 is frozen.
- (c) Hand-maintained exclusion list in the oracle: brittle, and it grows with every post-freeze feature.
- (d) Skip any sampled file on which axiom0 itself emits `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (axiom0's own
  out-of-subset signal), refill the sample from the same pattern, print what was skipped, and fail if a pattern ends
  up with no compared file. **Chosen.**

Classification: TYPE A (test oracle bug), no semantic change. Fix task **T547** (axiom-qa, sonnet, P13, priority 20;
paths: `stage1_oracle.py`; locks: `qa_stage1_oracle_diff_diag.py`, baseline file).

## Baseline admission

Two lines were appended to `_workspaces/baseline-failures.txt` under a dated header with the evidence: class
`fixture-regen`, fix tasks T546 and T547. Both ids were confirmed against `tools/axtest.py --list`.

## Constraints respected
- No file under T428m's `paths`/`locks` was touched. `docs/` was not touched. Nothing was committed.
- `taskctl.py validate`: OK (786 tasks). `harness_check.py`: HARNESS OK. `reqcov.py --strict`: COVERAGE OK.

## Files changed
- _workspaces/baseline-failures.txt
- _workspaces/tasks/todo/T546-fix-qa-t442-oracle-depends-on-baseline-file.md
- _workspaces/tasks/todo/T547-fix-stage1-parity-oracle-skips-post-freeze-features.md
- _workspaces/reports/triage-2026-11-26-preexisting.md
