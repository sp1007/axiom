# T141 follow-ups — architect planning after T141 (commit 2953b11)

STATUS: DONE

## Tóm tắt
- Ghi quy tắc drop khi gán vào spec chuẩn (ADR-0036): phép gán tính `rhs` vào biến tạm, tính
  place, drop giá trị cũ rồi move vào; place đi qua `view`/`mut_view` có drop; ghi qua con trỏ thô
  thì không bao giờ drop (con trỏ thô có thể trỏ vào vùng nhớ chưa khởi tạo). SPEC-03 AXS-SEM-043
  được bổ sung, SPEC-12 thêm AXS-DROP-007.
- Quyết định thêm: con trỏ thô không phải capability, local kiểu view chết trước khi owner bị drop
  ở cuối scope (SPEC-11 AXS-CAP-008/009); `Drop` của ngôn ngữ nhận diện theo phân giải tên
  (AXS-DROP-008); `a[i]` trên `view/mut_view<[N]T>` được tự deref (AXS-SEM-047) nhưng làm sau
  self-host trong axiomc (epic mới E14.5, theo R7).
- Task mới: T157 (AX0-FIX-06 capability), T158 (AX0-FIX-07 nhận diện Drop), T159 (AX0-FIX-08
  verifier kiểm drop trên code thật) — chuỗi ưu tiên 0 sau T147; T160 (test std dạng project cho
  `Arena`). Sửa T139 (tách chạy các leg của cùng một test, chữa race `dir.ax`), T147 (trả
  `qa_t140_edge_matrix.ax` về chuỗi literal), T149 (test ghi phần tử qua view), T214 (E14.5), T086
  phụ thuộc thêm T157–T159.

## Decisions
ADR `spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md` (options and rationale
there):
1. Assignment drop (TYPE B): view places drop, raw-pointer stores never drop — SPEC-03 AXS-SEM-043
   amended, SPEC-12 AXS-DROP-007 new (with test-matrix rows citing the T141 tests).
2. Raw pointers from `address_of(_mut)` hold no capability (SPEC-11 AXS-CAP-008); view locals die
   before scope-end drops of earlier owners (AXS-CAP-009). Architect probe: a pre-T141 axiom0 also
   rejects both the `address_of_mut` and the `let va: view<S> = view(a)` programs (fieldless Drop
   type), so the fix is an AX0-FIX in both compilers (T157), not port-only.
3. Index auto-deref through views (TYPE C, additive): allowed one level for `view`/`mut_view`, never
   for raw pointers (SPEC-03 AXS-SEM-047). Not needed for self-hosting (`(*a)[i]` works), so by R7 it
   is not added to axiom0; new ROADMAP epic E14.5, planned by T214.
4. Language `Drop` identity by resolution (SPEC-12 AXS-DROP-008) — T158.
5. Verifier drop checks on real bodies after drop elaboration — T159.

## Mapping of the requested follow-ups
| Item | Result |
| --- | --- |
| cap.ax rejects `address_of_mut` on a Drop local; `view<T> = view(a)` with droppable T | new T157 AX0-FIX-06 (axiom0 + port; opus; priority 0; after T147) |
| port divergence: indexed stores through a view; deferred element-through-view test | deduped into T149 (its defect 5 "index temporaries" is the same cause); acceptance gains `tests/run/parity/mir_builder/elem_store_through_view_drop.ax` |
| no auto-deref for `a[i]` on `mut_view<[N]T>` | specified (AXS-SEM-047); ROADMAP E14.5; T214 scope note; no P10 task (R7) |
| `is_drop_trait_name` accepts any `.Drop` path | new T158 AX0-FIX-07 (frontend; sonnet, gate opus; priority 0; after T157) |
| verifier missing-drop only for MIR-text tests; DOUBLE_DROP narrowed | new T159 AX0-FIX-08 (semantics; opus; priority 0; after T158) |
| `tests/run/host/fs/dir.ax` interp/native race | folded into T139 (owns `tools/axtest.py` lock): legs of one test file run serially in one worker; 20× `-j 8` acceptance |
| `arena_implicit_drop.ax` tests a copy of Arena | no task enables std imports for single-file tests; new T160 (project-mode std test via `axiom.toml` + std root) |
| restore string literals in `qa_t140_edge_matrix.ax` after T147 | added to T147's acceptance (T147 still todo); file added to its `paths` |

T086 now depends on T157, T158, T159 (lockstep axiom0 + port before the freeze, ADR-0034 §2).
T160 is not on T086's path (evidence only).

## Checks
- `taskctl.py lint` on every new/edited task file: OK; `taskctl.py validate`: OK (239 tasks).
- `reqcov.py --strict`: gaps 0, COVERAGE OK.
- `harness_check.py`: HARNESS OK (only the optional guard-hook WARN).
- No file under `docs/`, `bootstrap/`, `compiler/`, `std/` or `tests/` was touched (T146 is running).

## Files changed
- spec/decisions/ADR-0036-assignment-drop-raw-store-cap-followups.md
- spec/SPEC-03-core-semantics.md
- spec/SPEC-11-capability.md
- spec/SPEC-12-drop.md
- spec/ROADMAP.md
- _workspaces/tasks/todo/T157-ax0-fix-06-cap-raw-pointer-view-local-scope-end.md
- _workspaces/tasks/todo/T158-ax0-fix-07-language-drop-identity-by-resolution.md
- _workspaces/tasks/todo/T159-ax0-fix-08-verifier-drop-checks-real-bodies.md
- _workspaces/tasks/todo/T160-std-project-test-arena-implicit-drop.md
- _workspaces/tasks/todo/T139-axtest-cross-mode-agreement-native-evidence.md
- _workspaces/tasks/todo/T147-ax0-fix-05-string-data-symbols-local-symbol-linking.md
- _workspaces/tasks/todo/T149-port-mir-builder-checks-for-step-field-projection.md
- _workspaces/tasks/todo/T214-plan-phase-p14-comptime-2-0-reflection-generators.md
- _workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- _workspaces/reports/T141-followups.md
