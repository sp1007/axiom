# Audit 2026-09-30 — consolidated summary

## Tóm tắt
Bốn góc thẩm định (A1 tự biên dịch, A2 bám ladder, A3 khả năng thực thi task, A4 quy trình) nêu 80
phát hiện; sau khi gộp trùng còn 66: 3 nghiêm trọng (BLOCKER), 33 lớn (MAJOR), 30 nhỏ (MINOR).
Kết quả: 38 đã sửa trên board/spec, 19 thuộc phần harness (agent harness xử lý, xem
`HARNESS-FIXES.md`), 9 là điểm cần quyết định và đã được quyết định rồi áp dụng, 0 bị bác hoàn toàn
(5 đề xuất con bị bác, có lý do).

Ba lỗi nghiêm trọng đã sửa:
- Bộ thông dịch (oracle) không chạy được chương trình dùng heap hay hệ điều hành, nên toàn bộ thư
  viện chuẩn và phần port compiler sẽ mất phép đối chứng. Đã thêm tập intrinsic "host" (task T061c).
- Chương trình lớn do axiom0 biên dịch dễ sập vì khung stack lớn. Đã thêm stack probe, tuỳ chọn
  kích thước stack và bộ kiểm tra mã máy (task T025b).
- Gate native đầu tiên đòi tính năng native của các task sau nó. Đã thêm dấu `native-after` cho test
  viết trước bản native, và thu T028/T029 về đúng lát cắt đầu của ladder.

Các sửa lớn khác: tách file dùng chung để các task chạy song song không sửa cùng một file; gate chỉ
có ĐẠT hoặc BỊ CHẶN; frontend cắt dọc; tách 11 task quá lớn; sửa phụ thuộc của các task thư viện;
bổ sung các tính năng compiler viết bằng Axiom chắc chắn cần (phép toán wrapping, bảng hằng, view lưu
trong struct, HashMap giữ thứ tự chèn, drop cho kiểu generic).

Board: 143 → 155 task. Không bỏ, không hạ bậc, không dời yêu cầu nào trong OWNER.md. T224 vẫn hoãn.
Không sửa `docs/`.

## Quyết định đã tự áp dụng
1. **Oracle chạy heap/hệ điều hành thế nào** (ADR-0002). Phương án: cầu FFI trong oracle; intrinsic
   "host"; chấp nhận test chỉ chạy native. Chọn intrinsic "host": không cần chuyển đổi con trỏ, dễ
   port sang Axiom, giữ được đối chứng ba tầng.
2. **Bảng hằng** (ADR-0004). Phương án: thêm `static` bất biến; `const` aggregate đặt một lần trong
   `.rdata`. Chọn `const`: ít C hơn, không mở thêm ngữ nghĩa `static` trước self-host (T061, T061d).
3. **Backend** (ADR-0003). ABI lowering là pass LIR→LIR (giữ thứ tự tầng hiện có); stack probe nội
   tuyến cho khung trên 4 KB; bộ kiểm tra machine IR; axiomc link với stack 64 MB.
4. **Test viết trước bản native** (ADR-0005 §1). Phương án: kéo tính năng native vào T025/T028; đánh
   dấu `native-after`. Chọn đánh dấu: giữ đúng ladder 0263.
5. **File dùng chung** (ADR-0005 §2, §14). Mã chẩn đoán tách theo vùng `diag/codes/<AREA>.def`; mỗi
   lệnh và mỗi emitter của driver một file; CMake tự glob; file buộc phải dùng chung khai bằng `locks:`.
6. **Gate** (ADR-0005 §3, ROADMAP R9). Chỉ ĐẠT hoặc BỊ CHẶN; XFAIL chỉ cho khoảng trống spec có ADR;
   fuzz định nghĩa bằng seed và số vòng; gate cuối phase dùng Opus.
7. **Frontend cắt dọc** (ADR-0005 §4, §5). T014 chỉ chờ T011; T015b làm phần còn lại của ngữ pháp;
   T018 chờ spec ownership T045.
8. **Thời điểm truy vết** (ADR-0005 §6). Phương án: T111 chặn T007, T010 hay T017. Chọn T017: P1/P2
   chạy song song với việc rút yêu cầu, backlog đủ trước lõi ngữ nghĩa. Revisit: có.
9. **Cờ "chạy một mình"** (ADR-0005 §11). Chỉ task sửa board (T110, T111, T2NN) chạy một mình;
   T001–T004 chạy song song, đỡ khoảng bốn lượt Opus thời gian chết.
10. **Module mở sớm** (ADR-0005 §13). T060 mở sau gate P5, song song P6, để chuỗi thư viện chuẩn
    không xếp hàng sau chuỗi ngữ nghĩa P7. Thêm: T034 chạy song song T033, T043 song song T042.
11. **Ngân sách self-compile** (ADR-0005 §7). Đo ở T086; vượt ngân sách thì kéo một lát regalloc tối
    thiểu vào trước T087 (ngoại lệ R7 có điều kiện). Revisit: có.
12. **Task port** (ADR-0005 §8). Phương án: tách ngay; giao T076 tách. Chọn T076 vì lúc đó mới biết
    kích thước thật của từng module C; đã ghi tiêu chí bắt buộc. T081–T083 chuyển Opus.
13. **Dạng bootstrap** (ADR-0006). Dùng cú pháp cuối cùng ngay (`impl Drop for S`, `u32 as char` có
    kiểm tra, `len` dựng sẵn, Option/Result dựng sẵn tới T054b), không phát minh cú pháp tạm.
14. **Manifest và std root** (ADR-0006 §7–8). `axiom.toml`; tìm std theo `--std-root`, `AXIOM_STD`,
    rồi thư mục cạnh exe; không ghi đường dẫn tuyệt đối vào file kết quả.
15. **Console tiếng Việt** (ADR-0006 §9, ADR-0005 §16). Phương án: WriteConsoleW bằng mã máy; đổi
    code page. Chọn đổi code page ở T042 (ít mã máy viết tay), std.io dùng WriteConsoleW ở T074;
    kiểm tra bằng script đọc bộ đệm màn hình.
16. **Bộ đọc MIR dạng văn bản** (ADR-0004 §9). Giữ làm hạ tầng test bằng C, không port.
17. **P24** (ADR-0005 §10). Thêm epic E24.1–E24.8 và gate T324 ở trạng thái hoãn.
18. **Phụ thuộc spec của P1/P2** (ADR-0005 §12). T010 chờ T003a; T004 không chờ (bác một phần A4-15).

## Findings
| id | severity | title | fix | status |
|---|---|---|---|---|
| A1-01 (=A3-08) | BLOCKER | Interpreter cannot run heap/OS code | ADR-0002; new T061c; T070/T074/T074b native host functions; T065 direct FFI native-only | fixed |
| A1-02 | BLOCKER | No stack probes, 1 MB stack | ADR-0003; new T025b; T027/T028 `--stack-reserve`; T037 tests; T086 64 MB | fixed |
| A2-01 (=A3-04, A3-05) | BLOCKER | VS1 requires native features of later tasks | `native-after` directive (T005); T021/T028/T029 narrowed; catch-up tasks own the test dirs | fixed |
| A1-03 (=A3-10) | MAJOR | std tasks start before features exist | T069 += T059, T061b; T070 += T061c; T073a += T073 | fixed |
| A1-04 | MAJOR | T061a generic intrinsics before generics | T061a depends on T054b | fixed |
| A1-05 (=A3-09) | MAJOR | No task parses `extern`; paths too narrow | T012 scope; T015b; paths of T060/T061a/T065 widened | fixed |
| A1-06 | MAJOR | Wrapping/bit intrinsics have no owner | T034 (oracle), T037 (native), T069 (std), T003 (spec) | fixed |
| A1-07 | MAJOR | HashMap order differs from axiom0 | T007 documents hash and order; T069 hash; T073 contract | fixed |
| A1-08 | MAJOR | Stored views not scoped | T045 rule; T048 and T048b implement | fixed |
| A1-09 | MAJOR | Generic drop glue has no owner | new T054b; `drop_in_place`/`needs_drop` in T061a | fixed |
| A1-10 (=A3-13) | MAJOR | Constant tables / `static` | `const` aggregates in `.rdata`: T061 + new T061d | decided |
| A1-11 (=A2-09) | MAJOR | No scale test or compile-time budget | T075 100k-line generator; T086 budget; R7 contingency | fixed |
| A2-02 | MAJOR | Whole frontend before first MIR | T014 → T011; new T015b; T030 and T022 wait for T015b | fixed |
| A2-03 | MAJOR | MIR designed before ownership spec | T018 depends on T045; T045 priority 10 | fixed |
| A2-04 (=A3-15) | MAJOR | Gates can pass with failures | Gate rule on T013, T022, T029, T044, T052, T062, T075, T086, T087, T3NN; seed/iteration campaigns; committed perf baselines | fixed |
| A2-05 | MAJOR | T038 uses Option before T039 | T038/T038b use user enums; if-let over Option moved to T039 | fixed |
| A3-01 (=A2-06) | MAJOR | Runner lacks kinds/directives; no gate tool | T005 rewritten; `tools/gatecheck.py` in T022; T022 += T006, T013 | fixed |
| A3-02 (=A4-13) | MAJOR | Shared hot files outside `paths` | Per-area code files, per-command driver files, CMake globs, `locks:` on tasks | fixed |
| A3-03 | MAJOR | Parallel tasks share one tree | Snapshot builds (harness); agent files updated | harness-agent |
| A3-06 | MAJOR | T013/T017 need `check` from T016 | Both depend on T016 | fixed |
| A3-07 | MAJOR | Features used before delivered | ADR-0006 fixed forms; T034, T041, T046, T048, T049, T053 edited | fixed |
| A3-11 (=A3-20) | MAJOR | Port tasks far too large | T076 acceptance forces per-module split; T081–T083 Opus | decided |
| A3-12 (=A4-10) | MAJOR | T111 runs after code tasks started | T017 depends on T111; covers on done tasks via `taskctl covers` | decided |
| A3-14 | MAJOR | Oversized compiler tasks | Splits T025b, T038b, T048b, T054b, T061b, T071b, T071c, T074b | fixed |
| A4-01 | MAJOR | Scripts use cwd as root | taskctl root detection | harness-agent |
| A4-02 | MAJOR | Front-matter parser breaks on comments | taskctl parse and `lint` | harness-agent |
| A4-03 | MAJOR | Duplicate ids undetected | taskctl validate | harness-agent |
| A4-04 | MAJOR | Commit drops unlisted work | taskctl `accept`/`changes` | harness-agent |
| A4-05 | MAJOR | finish/commit not atomic | taskctl `accept`, `reconcile` | harness-agent |
| A4-06 | MAJOR | Restart recovery ambiguous | taskctl `recover`; STATUS line now in agent files | harness-agent |
| A4-07 | MAJOR | Infra failures burn attempts | `requeue --infra` | harness-agent |
| A4-08 | MAJOR | Unblock loop unbounded | `park`, caps | harness-agent |
| A4-09 | MAJOR | Unblocks collide with critical tasks | unblock lock, `adr-next`; tasks now say to use it | harness-agent |
| A4-11 | MAJOR | "Planned too late" undetected | reqcov timing rules (harness); `spec/selfhost-subset.tsv` in T003a; `needs` in extraction procedure | harness-agent |
| A4-12 | MAJOR | Wall-clock-only timeouts | overdue.py (harness); `timeout_min: 300` on T001, T003a, T017, T045, T055, T076 | harness-agent |
| A4-14 | MAJOR | No post-T087 procedure | T087 deliverables; agent files; freeze tag check in harness_check | fixed |
| A1-12 | MINOR | Control/pattern forms "if in spec" | T001, T012, T031, T038, T038b, T040 | fixed |
| A1-13 | MINOR | Derive Hash/Ord, tuple impls | T056, T069 | fixed |
| A1-14 (=A3-19) | MINOR | std lookup unspecified | ADR-0006 §8; T060 | decided |
| A1-15 (=A2-08) | MINOR | Fixed-point plan underspecified | T086 byte compare; T087 equivalence, two dirs, no gcc | fixed |
| A2-07 | MINOR | VS names clash with ladder | T044 renamed "P5 gate"; name map in T003 and ROADMAP | fixed |
| A2-10 | MINOR | Deferred ladder steps not mapped | T003 BOOT-00..38 table; T003a in/out list | fixed |
| A2-11 | MINOR | ABI lowering after LIR | ADR-0003 confirms it as a LIR pass | decided |
| A2-12 | MINOR | No machine-IR verifier | T025b | fixed |
| A2-13 | MINOR | -O1 verified only in debug | T043 `--verify-each` in all test builds | fixed |
| A3-16 | MINOR | Console glyph check not automatable | `console_check.py`; code page switch in T042 | decided |
| A3-17 | MINOR | T043 lacks T041/T042 deps | T043 depends on T041, T040; runs alongside T042 | fixed |
| A3-18 | MINOR | T023 not behind VS0 gate | T023 depends on T022 | fixed |
| A3-21 | MINOR | Owner/model mismatches | gate_model opus on all phase gates; T081–T083 opus | fixed |
| A3-22 | MINOR | P0 spec tasks block the skeleton | Priorities ≥ 10 for T001–T004 | decided |
| A3-23 | MINOR | T086 suite includes C-internal tests | `requires: axiom0-internal`, `--exclude-requires` | fixed |
| A3-24 | MINOR | Path slips in P0/P1 | T001, T005, T006, T010, T011, T012, T026, T027 | fixed |
| A3-25 | MINOR | T046–T049 acceptance overlap | T045 tags matrix rows per task | fixed |
| A3-26 | MINOR | MIR text parser is test-only C | Kept as test infrastructure, not ported | decided |
| A3-27 | MINOR | Interpreter speed vs test sizes | Runner timeout; T021 throughput target; interp twins | fixed |
| A4-15 | MINOR | Core tasks use SPEC-00 without dependency | T010 += T003a; T004 dependency rejected | decided |
| A4-16 | MINOR | reqcov passes without catalogue | reqcov `--strict` | harness-agent |
| A4-17 | MINOR | E24.x and T324 do not exist | ROADMAP E24.1–E24.8; T324 deferred | fixed |
| A4-18 | MINOR | No id rule for follow-up tasks | `new-id`, `supersede` (harness); ROADMAP §4.7 | harness-agent |
| A4-19 | MINOR | Planning acceptance omits harness_check | T211–T224, T311–T323, core gates; ROADMAP §4 | fixed |
| A4-20 | MINOR | Stale statements in docs | x64, spec-index, ROADMAP fixed; two orchestrator-skill lines belong to harness | fixed |
| A4-21 | MINOR | settings.json gaps | settings, guard hook | harness-agent |
| A4-22 | MINOR | `next --max 0` returns a task | taskctl | harness-agent |
| A4-23 | MINOR | No branch for stuck board | `stuck` | harness-agent |
| A4-24 | MINOR | `unblock` unguarded | taskctl | harness-agent |
| A4-25 | MINOR | Hard-coded commit trailer | taskctl | harness-agent |

## Rejected
No finding was disproven. Rejected sub-proposals:
- A3-08 preferred option (FFI bridge inside the interpreter): host-dependent oracle, pointer
  marshalling, hard to port.
- A3-04 option (b) (move branches/calls into T025/T028): breaks the ladder's first slice.
- A4-15 "T004 depends on T003a": the skeleton needs only the engineering conventions.
- A3-14 three-way split of T038: two parts are one sitting each.
- A3-17 literal fix (T043 depends on T042): [T041, T040] covers the concern and keeps parallelism.

## Check results (architect run)
- `taskctl.py validate`: OK (155 tasks).
- `harness_check.py`: HARNESS OK.
- `reqcov.py --strict --allow-missing`: no catalogue yet (created by T110).
- Note for the harness agent: the `locks:` example in axiom-tasks/SKILL.md uses `codes/lex.def`; the
  board uses `codes/LEX.def`.

## Files changed (board/spec)
See the commit that contains this file: every path under `_workspaces/tasks/`, `spec/`,
`.claude/agents/` and `.claude/skills/{axiom-testing,axiom-c-stage0,axiom-x64-backend,axiom-spec-index}/`.
