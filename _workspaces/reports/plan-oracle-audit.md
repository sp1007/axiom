# plan-oracle-audit — board work from the oracle-independence audit (2026-10-19)

STATUS: done

## Tóm tắt
- Đã chuyển toàn bộ 4 BLOCKER, 7 MAJOR thành việc trên board; 3 MINOR thì 1 gộp vào task, 2 được ghi
  rõ là hoãn sang task lập kế hoạch P13/P21. Quyết định ghi trong ADR-0034 và nhật ký ROADMAP 2026-10-20.
- Quy tắc mới: cổng T086/T087 chỉ ĐẠT khi một "tập con độc lập" chạy native bằng axiomc và đều qua.
  Tập con này gồm các test có kỳ vọng lấy từ spec, Python, GNU as/objdump. Đối chứng axiom0-vs-port
  chỉ còn là bằng chứng phụ.
- Quy tắc sửa song song: trước khi đóng băng axiom0 (T087), mỗi task AX0-FIX sửa lỗi ngữ nghĩa phải
  sửa cả mã C lẫn bản port trong `compiler/` trong cùng task.
- Task mới (đều thuộc P10):
  - T140 AX0-FIX-02: chia/lấy dư u64, tràn nhân u64, dịch usize; có bảng số học sinh bằng Python.
  - T141 AX0-FIX-03: Drop cho struct chỉ có trường scalar/con trỏ; gỡ `_glue: DropGlue` khỏi 8 file
    std; kiểm va chạm tên destructor.
  - T142: kiểm exe/obj thật bằng objdump; sửa 36 manifest gọi cứng `{build}/axiom0`.
  - T143: mở rộng bảng GNU as cho mọi dạng lệnh isel sinh ra, kèm bản Axiom chạy được với axiomc.
  - T144: kiểm bundle selfhost luôn khớp mã `compiler/` hiện tại.
  - T145: rà test native không kiểm gì; gỡ `modes: interp` sai.
  - T146 AX0-FIX-04: phát hiện thêm khi thăm dò. Parser bỏ âm thầm phần còn lại của dòng khi thiếu dấu
    kết thúc câu lệnh, nên có thể sinh mã sai mà không báo lỗi.
- Đã sửa task cũ:
  - T134: đối chiếu hash với `hash_vectors.txt` (Python), test chính `compiler/kernel/hash.ax`, chạy
    native `qa_hash_vectors.ax`.
  - T139: thêm so sánh golden LIR/HIR (`stdout-file:`).
  - T086: thêm tập con độc lập và WEAK-NATIVE = 0.
  - T087: chạy tập con độc lập với axiomc2.
- Điều kiện mới của T086: T140, T141, T142, T143, T144, T145, T146, cộng với T085, T134, T139 đã có.
- Thứ tự chạy:
  - Chạy được ngay, song song với T085: T142, T143.
  - Chạy một mình, nối tiếp: T134 → T140 → T141 → T146 (T146 còn chờ T085).
  - Sau đó: T139 chạy sau T140; T144 và T145 chạy sau T146.
- Rủi ro cần chủ dự án xem lại (Revisit trong ADR):
  - Sửa Drop trước T086, không đợi tới T087 như auditor đề xuất.
  - Đổi tên destructor sang `<Type>$drop`, chỉ khi có va chạm tên.
- `build/axiom0.exe` ở cây chính đã cũ (14/10): skill `axiom-c-stage0` và `axiom-testing` nay cấm dùng
  nó làm bằng chứng; mọi task mới/sửa ghi "build fresh in the snapshot".

## Decisions per finding
| Finding | Severity | Decision | Task | Gates T086 |
|---|---|---|---|---|
| OI-01 u64/usize `/ %` signed idiv | BLOCKER | New AX0-FIX-02, C + port in lockstep (ADR-0034 §2), Python table; removes std `u64_div_u32` workaround | T140 | yes |
| OI-02 u64/usize mul overflow not trapped | BLOCKER | Same task, same table | T140 | yes |
| OI-03 native hash never checked vs Python | BLOCKER | T134 acceptance amended: Python vectors, real `compiler/kernel/hash.ax`, `qa_hash_vectors.ax` native leg, hand copy in `qa_kernel_hash.ax` removed; path added | T134 | yes |
| OI-04 correctness rests on axiom0-vs-port | BLOCKER | Independent subset acceptance in T086 (and T087 with axiomc2); evidence ranking in ADR-0034 §1, §3 | T086, T087 | yes |
| OI-05 isize/usize shift width 32 | MAJOR | In AX0-FIX-02 (shift table covers amounts 31..65) | T140 | yes |
| OI-06 Drop not run for scalar/pointer-field structs | MAJOR | New AX0-FIX-03, one needs-drop predicate, C + port, std workaround removed, Arena frees; **before T086** (override of "before T087": Stage-1 must measure real memory and std without workaround; a later fix forces a T086 re-run) | T141 | yes |
| OI-07 COFF/PE never validated externally | MAJOR | (a) objdump validation of ≥ 20 real programs, `dummy.test` replaced by the cdriver_coff manifest, tool missing = FAIL; (b) gcc/ld linking of real programs deferred to E18.7 (note in T751); T028 cross-link criterion superseded by ADR-0034 §4 | T142, T751 | (a) yes |
| OI-08 GNU-as vectors 9/81, excluded at T086 | MAJOR | Generator widened to 100% of isel-emitted forms, Axiom twin embedding `compiler/target/x64/encode.ax`, freshness manifest; test-only, encoder bugs become follow-ups | T143 | yes |
| OI-09 weak/vacuous legs, 9 stale `modes: interp` | MAJOR | New sweep task; WEAK-NATIVE 0 in numeric/drop/ptr/native_*/std made a T086 acceptance line | T145 (+T086) | yes |
| OI-10 LIR goldens orphaned | MAJOR | Folded into T139: `stdout-file:` directive, 31 lir + hir manifests compare, drifted goldens reviewed; T139 now depends on T140 | T139 | yes (already a dependency) |
| OI-11 selfhost bundles test copies | MAJOR | New task: `check` mode + `bundles_current.test` for every generator, hand copies removed | T144 | yes |
| OI-12 ABI only vs kernel32 | MINOR | Deferred, recorded: P13 planning T213 must plan gcc-DLL ABI oracle + `offsetof` table | T213 note | no |
| OI-13 console UTF-8 path | MINOR | Deferred, recorded: P21 planning T221 (pseudo-console check) | T221 note | no |
| OI-14 mangling collisions | MINOR | Folded into T141 (`tests/run/mangle/`; `<Type>$drop` if collision, ADR-0034 §6) | T141 | yes (via T141) |
| Cross-lens: one-line `if {..} return 6;` | (new, architect-confirmed) | Root cause: `AX_PARSE_EXPECTED_TERMINATOR` never emitted, parser silently drops the rest of the statement (`let a = 1 let b = 2` loses `let b`). Silent miscompile risk, shared by the port, so AX0-FIX-04 with sweep of std/compiler/tests | T146 | yes |
| Extra: 37 manifests hard-wire `{build}/axiom0` | (new) | Converted to `{compiler}` (36 in T142, `tests/hir/more.test` in T139); rule in axiom-testing | T142, T139 | yes |
| Stale `build/axiom0.exe` | build hygiene | skills axiom-c-stage0 / axiom-testing: never evidence, rebuild snapshot, pass `--compiler`; `tests/README.md` is locked by T139 and left to it | — | — |

No ADR was needed for language semantics: unsigned division (SPEC-03 AXS-SEM-032), overflow
(AXS-SEM-030), shifts (AXS-SEM-034, REQ-TYP-035), Drop (SPEC-12 AXS-DROP-001..003) and terminators
(SPEC-02 AXS-GRM-011) are already specified; these are implementation defects (TYPE A fixes). ADR-0034
records the process and architecture decisions (TYPE B): evidence ranking, lockstep rule, T086 subset,
COFF oracle replacement, ordering, destructor symbol form, mandatory external tools, MINOR deferrals.

## Ownership of `compiler/` edits
axiom0 is unfrozen until T087, so each AX0-FIX task owns both sides of its fix:
- T140 owns `compiler/lir`, `compiler/target/x64`, `compiler/mir/builder.ax`, `compiler/opt` and `compiler/interp`.
- T141 owns `compiler/mir`, `compiler/lir`, `compiler/interp`, `compiler/verify` and `compiler/types/typeck.ax`, plus the std files.
- T146 owns `compiler` and `std` broadly, for the terminator sweep.

Shared paths and dependencies serialise these tasks. None of them touches T085's
`compiler/obj_link_driver`; T146 waits for T085.

## Schedule
- Ready now and parallel-safe with running T085: T142 (tests/link, obj, driver, verify), T143
  (tools/gen_encode_tests.py, tests/encode).
- Serial, priority 0: T134 (after T085) → T140 → T141 → T146.
- Then: T139 (after T134, T140), T144 (after T085, T146), T145 (after T139, T146) → T086 → T087.

## Checks
- `taskctl.py lint` OK for T086, T087, T134, T139, T140–T146.
- `taskctl.py validate`: OK (225 tasks).
- `harness_check.py`: HARNESS OK (only the standing optional-guard-hook warning).
- `reqcov.py --strict`: COVERAGE OK, gaps 0.
- Probes run in a scratch dir with `build-snap-T085c/build/axiom0.exe`. They confirmed the terminator
  defect (AST dump shows the `return 6;` statement missing).

## Files changed
- _workspaces/audit/2026-10-19/oracle-independence.md
- spec/decisions/ADR-0034-oracle-independence.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T140-ax0-fix-02-unsigned-div-mul-overflow-shift-width.md
- _workspaces/tasks/todo/T141-ax0-fix-03-drop-for-scalar-pointer-field-structs.md
- _workspaces/tasks/todo/T142-objdump-validation-real-exe-obj-compiler-placeholder.md
- _workspaces/tasks/todo/T143-gnu-as-encoder-table-widened-axiom-twin.md
- _workspaces/tasks/todo/T144-selfhost-bundle-freshness-checks.md
- _workspaces/tasks/todo/T145-native-evidence-sweep-run-std-tests.md
- _workspaces/tasks/todo/T146-ax0-fix-04-statement-terminator-enforced.md
- _workspaces/tasks/todo/T134-ax0-fix-01-native-intrinsics-assert-panic.md
- _workspaces/tasks/todo/T139-axtest-cross-mode-agreement-native-evidence.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- _workspaces/tasks/todo/T087-stage-2-3-fixed-point-reproducible-bootstrap.md
- _workspaces/tasks/todo/T213-plan-phase-p13-low-level-systems-unsafe-freestanding-securit.md
- _workspaces/tasks/todo/T221-plan-phase-p21-standard-library-completion.md
- _workspaces/tasks/todo/T751-e18-7-pe-dll-output-import-library.md
- .claude/skills/axiom-c-stage0/SKILL.md
- .claude/skills/axiom-testing/SKILL.md
- _workspaces/reports/plan-oracle-audit.md
