# Unblock T428m — resolver binds paths inside generic arguments

## Tóm tắt
- T428m đúng về thiết kế (AXS-GRM-080 áp dụng nguyên văn, loại TYPE A, không cần ADR). Phần bị chặn chỉ là
  hệ quả có chủ đích của việc phân giải đúng, nằm ngoài `paths`/`locks` của task.
- Quyết định: **mở rộng `locks:`** của T428m đúng 15 file (frame.ax, 4 golden, 2 ui, 8 template selfhost `.ax.in`)
  và thêm file test tách mới vào `paths:`, thêm mục 6 (vòng sửa hệ quả) vào Scope. Lý do: thiếu `use` trong
  `compiler/interp/frame.ax` làm hỏng build stage 2, nên sửa resolver và hệ quả phải vào **cùng một commit**;
  tách thành task riêng sẽ để HEAD hỏng giữa hai commit.
- Không có task đang chạy xung đột (T544 vừa được khởi động nhưng không chạm file nào của T428m). Các task todo
  có `compiler/interp` trong paths chỉ phải xếp hàng sau T428m.
- Hai test hỏng sẵn trên HEAD được nhận vào baseline: `link/dll/gnu_ld_run.test` (task sửa mới T423j: GNU ld thiếu
  `__ax_host_aio_close/cancel` cho các test async của T428a — kiến trúc sư đã tái hiện bằng compiler HEAD) và
  `ui/security_profiles/forbid_unsafe_constructs_neg.ax` (cùng nguyên nhân với T540, thêm vào phạm vi T540).
- Việc theo sau: T545 (UB tiềm ẩn trong 7 template probe, từ T543-qa), T428p (tách `>>` sau `view<..>`),
  T428q (`Option<never>` báo AX_TYPE_UNKNOWN, phụ thuộc T428m). "`Vec` không có trong prelude" là đúng thiết kế,
  không tạo task.

## Blocker
`_workspaces/reports/T428m-report.md` (STATUS: BLOCKED): the fix and its 7 new tests pass, stage 2 builds and both
fixed points hold once `compiler/interp/frame.ax` imports `InterpAlloc` (verified in the snapshot only). The Tier-1
sweep shows 8 new failures: 6 intended (4 goldens gain the new `@Sym(n)` / `(TypePath @n)` bindings, 2 ui tests
whose diagnostics change correctly), and 2 pre-existing on HEAD. The selfhost groups of resolve/resolve_hir/hir fail
because 8 `.ax.in` templates embed copies of those goldens/ui files.

## Options considered
1. **Widen T428m's locks to the fallout files (chosen).** Every change is mechanical, already verified by the owner,
   and must be in the same commit as the resolver change (the stage-2 build fails without the frame.ax import, and
   the goldens fail the moment the resolver lands).
2. Split into T428m + a fallout task. Rejected: the first commit would break the stage-2 build and the suite; no
   ordering makes either part independently green.
3. Hide the frame.ax miss with a resolver fallback (bare-name walk). Rejected: it is exactly the defect class T428m
   removes (T428g), and the task forbids heuristics.

Conflict check (HEAD b8809d48): no task in `doing/` overlapped when checked; T544 was started afterwards and owns
only `compiler/kernel/interner.ax`, `tests/selfhost/kernel/qa_kernel_interner.ax.in`, lock
`tests/selfhost/bundle_common.py` — disjoint. Todo tasks touching the new locks: `compiler/interp` (paths of T058,
T428k, T465, T477, T480, T522, T527, T531, T552, T563, T573; lock of T513 on frame.ax) and `tests/selfhost/hir`
(T671, T682). None has to change; the scheduler serialises them behind T428m. The `.ax.in` templates are sources,
not generated bundles (`tests/selfhost/generated-files.txt` does not list them), and no task locks the whole
`tests/selfhost` tree.

## Decision applied
- T428m: `paths:` += `tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_unresolved_fnonce.ax` (the split
  test); `locks:` += `compiler/interp/frame.ax`, `tests/resolve/more.resolved`, `tests/hir/more.hir`,
  `tests/typeck/generic/generic_subst.thir`, `tests/typeck/async/async_basic_pos.thir`, `tests/ui/resolve/ui_tests.ax`,
  `tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax`, and the 8 templates
  `tests/selfhost/resolve/qa_resolve_corpus_{pos,neg_c}.ax.in`,
  `tests/selfhost/resolve_hir/qa_resolve_hir_corpus_{pos_b,pos_c,neg_c,wide_b}.ax.in`,
  `tests/selfhost/hir/qa_hir_corpus.ax.in`, `tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in`. Scope item 6 spells
  out exactly what may change in each (frame.ax: one `use` line; goldens: only the new bindings and the documented
  +1 id shift; ui split keeps all four typeck expectations). Acceptance: the three selfhost groups pass. Unblocked
  (`status: todo`); the owner's uncommitted `compiler/resolve/resolver.ax` in the main tree is untouched.
- Baseline (`_workspaces/baseline-failures.txt`), with evidence:
  - `link/dll/gnu_ld_run.test` → T423j. Architect's rerun of `tests/link/dll/gnu_ld_run_oracle.py` with the HEAD
    compiler `axiomc2_O1_642250f08b7af786.exe`: `5/1143` failed, all in `tests/run/async/addr_stable_locals/`
    (T428a, 61acdeb9), `undefined reference to __ax_host_aio_close` / `__ax_host_aio_cancel` (defined in
    `std/sys/windows/iocp.ax`).
  - `ui/security_profiles/forbid_unsafe_constructs_neg.ax` → T540 (new scope item 4): line 45
    `@at(0x1000usize) static MMIO_REG: u32 = 0u32;` hits `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`, the same pinned-static
    rule as T540's test; identical on HEAD.

## Follow-ups recorded
| Item | Decision |
|---|---|
| T543-qa F1/F2: un-zeroed interner map in `qa_opt_static_atomic_probe.ax.in`, typed loads of fresh arena memory in `opt_{alias,escape,loops,loop_vec,scalar,slp_vec}` probes | New **T545** (P13, semantics, sonnet, priority 40), paths = the 7 templates |
| `Option<view<[S]>>` / `Option<view<Self>>` fail to parse | New **T428p** (P11, frontend, sonnet), lock `compiler/syntax/parse.ax`, AXS-GRM-057 |
| `Option<never>` value gives AX_TYPE_UNKNOWN | New **T428q** (P11, semantics, opus), depends T428m (same sentinel path), locks typeck.ax + lower.ax, AXS-SEM-015 |
| `Vec` not in a package's prelude | By design: the prelude is small and fixed (0141 §XXII.41; `std/core/prelude.ax`, SPEC-33 AXS-ASY-015); single-file tests also `use` it. No task |
| GNU ld oracle failure | New **T423j** (P12 like T423i, frontend, sonnet, priority 5) |

T428p/T428q are not added to the P11 gate T311 `depends` (same treatment as T428g–T428o: defect fixes found after the
suite, not gate content). ROADMAP change log entry 2026-11-26 added.

## Checks
- `taskctl.py lint` OK on T423j, T545, T428p, T428q, T428m, T540; `taskctl.py validate` OK (784 tasks);
  `harness_check.py` HARNESS OK (only the standing optional-guard WARN); `reqcov.py --strict` COVERAGE OK, gaps 0.

## Files changed
- _workspaces/tasks/todo/T428m-fix-resolver-binds-paths-inside-generic-arguments.md
- _workspaces/tasks/todo/T540-baseline-fix-safety-profile-safe-neg-addr-static.md
- _workspaces/tasks/todo/T423j-fix-gnu-ld-run-oracle-async-aio-host-symbols.md
- _workspaces/tasks/todo/T545-fix-latent-uninit-reads-in-opt-and-static-probe-harnesses.md
- _workspaces/tasks/todo/T428p-fix-generic-close-split-after-view-type-in-generic-list.md
- _workspaces/tasks/todo/T428q-fix-option-never-value-type-unknown.md
- _workspaces/baseline-failures.txt
- spec/ROADMAP.md
- _workspaces/reports/unblock-T428m.md
