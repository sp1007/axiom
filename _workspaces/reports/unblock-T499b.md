# unblock-T499b — the live exhaustiveness checker is in typeck.ax

## Tóm tắt
- T499b đã viết xong bộ kiểm tra usefulness theo cột cho tuple trong `compiler/types/exhaust.ax` và các test. Nhưng bộ kiểm tra
  đang chạy thật là bản sao `tc_match_check_exhaustiveness` trong `compiler/types/typeck.ax`, nên cần thêm một bản vá 5 dòng
  vào `typeck.ax`. File đó đang thuộc task T498g, task đang chạy.
- Quyết định: thêm `compiler/types/typeck.ax` vào `paths:` của T499b và thêm T498g vào `depends`. T499b sẽ chạy lại sau khi
  T498g được accept, áp dụng `_workspaces/T499b-typeck.patch` (áp lại bằng tay nếu lệch dòng) rồi gate lại. Phần exhaust.ax
  và test đã có sẵn trong cây làm việc, không làm lại.
- Gộp vào T499b việc xoá dòng `xfail:` của `tests/std/num/static_dispatch_xfail.ax`. Test này đã XPASS từ khi T448 xong.
- Tạo task T499c: chỉ giữ một bộ kiểm tra exhaustiveness, nằm trong `exhaust.ax`, cho mọi kiểu scrutinee. Task xoá bản sao
  trong `typeck.ax` và vá lỗ hổng `Some(1)` + `None` bị chấp nhận trên enum trần. T312 (gate P12) phụ thuộc T499c.
- Không yêu cầu nào bị bỏ. Không cần ADR vì đây là thay đổi thứ tự task và phạm vi cài đặt; quyết định được ghi trong nhật
  ký ROADMAP.

## Classification
TYPE A/B boundary: an ownership and scheduling problem on the board, not a language semantics change. Tuple patterns are
already irrefutable or exhaustive under SPEC-03, so no ADR is needed. The ordering change is recorded in the `spec/ROADMAP.md`
change log.

## Decision 1: how T499b gets typeck.ax
Options:
1. Add `typeck.ax` to T499b's `paths:` and `T498g` to its `depends`, then re-run T499b after T498g is accepted. **Chosen.**
2. Add `typeck.ax` to T499b's `locks:` and run it now. Rejected: T498g has uncommitted hunks in `typeck.ax` in the main tree.
   T499b's gate snapshot would mix them in. This is the same failure as T485/T444 (CLAUDE.md, 2026-11-18).
3. Hand the 5-line patch to T498g. Rejected: unrelated scope, and T498g is mid-run (agents never edit files of a doing task).
4. Make `exhaust.ax` the live checker without touching `typeck.ax`. Impossible, because the call site is in `typeck.ax`.

Rationale: the remaining work is small (a 5-line patch plus a re-gate), and T498g has priority 11 and is already running, so
the wait is short. The task body now has a "Resume after unblock" section. It tells the engineer that the exhaust.ax and test
work is already in the main tree and only the typeck patch and the re-gate remain.

## Decision 2: duplicate checker (scope)
Two copies exist: `tc_match_check_exhaustiveness` and `tc_match_check_exhaust_bool_or_enum` in typeck.ax, which are live, and
`match_check_exhaustiveness` and `match_check_exhaust_bool_or_enum` in exhaust.ax, which are dead and referenced only under
`if false {}`. This duplication is what blocked T499b. The old scalar/enum path also has a soundness gap: a bare-enum match
`Some(1)` + `None` is accepted. Options:
1. Remove the duplicate inside T499b. Rejected: it widens a nearly finished fix task, and the stricter check may reject
   existing compiler and std sources outside T499b's paths.
2. Create a follow-up task **(chosen: T499c)**. It routes every scrutinee through the usefulness algorithm in exhaust.ax and
   reduces `typeck.ax` to a thin call. It keeps the existing diagnostics and 128-bit range support, and adds ui and run tests
   for the refutable-payload gap. If sources outside its paths break, it reports them instead of weakening the check.
3. Leave both copies. Rejected: the copies will keep drifting, and the soundness gap stays.

T312 (P12 gate) now depends on T499c, because a match that is accepted but not exhaustive is a soundness bug.

## Decision 3: the stale xfail on static_dispatch_xfail.ax
`tests/std/num/static_dispatch_xfail.ax` XPASSes (fixed by T448). The `xfail: T454` tag is stale, and T454 is done. Options:
1. A new test-hygiene task. Rejected: a whole gate cycle for one line.
2. Fold it into T499b. **Chosen.** T499b is re-gating anyway, and no other open task holds the file. The change deletes the
   directive line and keeps the file name, so the test id stays stable.
3. Fold it into T499c. Rejected: T499c comes later, and the XPASS would keep failing `std/` suites until then.

## Board changes
- T499b: `depends` += T498g; `paths` += `compiler/types/typeck.ax`, `tests/std/num/static_dispatch_xfail.ax`; new "Resume
  after unblock" section and two acceptance items; then `taskctl.py unblock T499b`, so its status is `todo`.
- T499c: new task, P12, axiom-semantics, opus, priority 25, depends T499b, covers REQ-TST-072.
- T312: `depends` += T499c.
- `taskctl.py validate`: OK (745 tasks). `harness_check.py`: HARNESS OK. `reqcov.py --strict`: COVERAGE OK.

## Files changed
- _workspaces/tasks/todo/T499b-fix-exhaustiveness-of-tuple-patterns.md
- _workspaces/tasks/todo/T499c-unify-match-exhaustiveness-checker-in-exhaust.md
- _workspaces/tasks/todo/T312-phase-p12-gate-numeric-floating-point-simd.md
- spec/ROADMAP.md
- _workspaces/reports/unblock-T499b.md
