# Unblock T428g — 2026-11-26 (architect)

## Tóm tắt
- Kỹ sư T428g chứng minh (có trace) nguyên nhân gốc nằm ở **resolver**, không phải typeck: `resolve_type` /
  `resolve_path_seg` trong `compiler/resolve/resolver.ax` không bao giờ duyệt `generic_args` của segment, nên đường dẫn
  bên trong đối số generic (`Result<String, IoError>`, `Option<a.S>`) không có ràng buộc (symbol = 0) và typeck phải tra
  theo tên trần trên toàn chương trình. Kiến trúc sư đọc lại mã và xác nhận; HIR lowering (`lower_generic_args` →
  `lower_type` → `lower_path_into`) đã chép ràng buộc sẵn, chỉ thiếu ở resolver.
- Quyết định: đây là lỗi cài đặt (TYPE A) — SPEC-02 AXS-GRM-080 đã nói "đối số generic là một kiểu", nên được phân giải như
  mọi kiểu khác trong cùng scope. Không cần ADR.
- Tạo **T428m** (frontend, opus): resolver phân giải đối số generic của mọi segment ở mọi vị trí (kiểu, biểu thức, pattern,
  bound), kèm test golden `.resolved`/HIR và test chạy; gate có quét Tier-1 non-selfhost vì thay đổi chạm mọi chương trình;
  lỗi "lộ ra" ở file ngoài phạm vi thì báo BLOCKED kèm danh sách, không vá bằng heuristic.
- T428g nay phụ thuộc T428m; phạm vi viết lại: typeck chỉ giữ duyệt tên trần cho đường dẫn thật sự không có ràng buộc, ưu
  tiên module hiện tại, mơ hồ thì báo lỗi; vẫn là task gỡ 2 dòng baseline e11_5.
- axiom0 **không** cần AX0-FIX: đã đóng băng, chỉ biên dịch bundle compiler ở stage 1, và điểm cố định stage-2/3 kiểm chứng.
- Rủi ro: mã std/compiler đang dựa vào ràng buộc sai (std có nhiều `String`, `Vec`, `Ordering` trùng tên; compiler có
  `SymbolId`, `TypeId` trùng tên) có thể lộ lỗi khi T428m chạy — đã định sẵn cách xử lý.

## Blocker
`_workspaces/reports/T428g-report.md` (STATUS: BLOCKED, attempt 1): every lookup that reached
`lookup_path_type_by_name` and hit the wrong struct was a generic-argument path with `symbol = 0`, `def_dom = 0`;
`Option<a.S>` gives `AX_NAME_UNRESOLVED` on HEAD; `inspect --emit=resolved` shows `(GenericArg "" (TypePath (PathSegment "Foo")))`
without a symbol.

Architect verification (read of HEAD):
- `compiler/resolve/resolver.ax` 823–990 (`resolve_path_seg`) and 992–1030 (`resolve_type`): no use of `generic_args`;
  the only uses in the file are the dump helpers (2711, 2782, 3054). Call sites: 1003, 1072, 1349, 1365.
- `compiler/hir/lower.ax` 401–452: `lower_path_into` lowers the last segment's `generic_args` through `lower_generic_args`
  -> `lower_type` -> `lower_path_into`, which reads `get_symbol(rmap, node)` and `lower_path_domain`. Expression-path
  segments (818–842) also call `lower_generic_args`. So the binding reaches HIR as soon as the resolver records it.
- SPEC-02 AXS-GRM-080: "A generic argument is a type or, in bounds, an associated-type binding `Item = T`." No new rule
  is needed; the resolver simply does not implement it.

## Decision
Classification: TYPE A (implementation bug in the resolver) plus a rescope of T428g. No ADR (no language or resolution
rule is decided; the existing rule AXS-GRM-080 is applied).

Options considered:
1. **Typeck-only fix** (prefer current module, follow `use` in typeck) — rejected: re-implements name resolution in typeck,
   does not fix the imported-`String` case of the e11_5 tests, and would be thrown away once the resolver binds.
2. **Engineer's proposal: resolver task first, T428g after** — chosen, with additions: one helper for all generic-argument
   positions (type, expression, pattern, method-call, bounds), explicit preservation of the T447 projection rule and the
   lowering sentinels (`i128`/`u128`/`never`/`Future`), a Tier-1 non-selfhost sweep in the gate (a resolver change
   reaches every program, so the grep-based affected set is the whole suite), and a fixed fallout policy.
3. **Merge both into one task** — rejected: resolver (frontend) and typeck (semantics) have different owners and locks;
   T428m alone may already turn the two e11_5 ids green, and T428g then becomes small.

Fallout policy (T428m scope 4): correct bindings can expose sources that relied on the wrong item (std defines several
`String`, `Vec`, `Ordering`, `Layout`, `SendError`, `Utf8Error`, ...; `compiler/` defines `SymbolId`/`TypeId` in both
`kernel/id.ax` and `query/db/mod.ax`, and `ConstEvalResult`, `SemanticKey`, `Fingerprint128`, `DependencyEdge` twice).
Fallout outside T428m's paths/locks is reported as BLOCKED with an exact list; the architect then creates the fix tasks.
It is never hidden by a heuristic or by downgrading the diagnostic.

T428g rescope: depends `[T428a, T428m]`; re-measure after T428m; the bare-name walk stays only for truly unbound paths
(current module first, ambiguity across other modules is `AX_NAME_UNRESOLVED`, never a silent first match); bound paths
select by `symbol` / `def_mod`+`def_name`; same tests; it still removes the two baseline lines.

axiom0: **no AX0-FIX**. axiom0 is frozen after T087 (BOOTSTRAP.md). It only compiles the compiler bundle into stage 1.
Today that bundle builds and the stage-2 == stage-3 fixed point holds, so axiom0's gap does not miscompile it. T428m's
acceptance requires the stage-2 build and the fixed point at `-O0`/`-O1`. If the fixed `compiler/` sources ever stop
building under axiom0 because of this gap, that is the trigger for an AX0-FIX task, not before.

## Baseline
`_workspaces/baseline-failures.txt` lines 32–33 keep naming **T428g**, which still removes them (T428g locks the file;
T428m does not touch it and its acceptance says the two ids may start passing but stay listed). File not edited.

## Tasks created / changed
| id | change |
|---|---|
| T428m (new) | P11, axiom-frontend, opus / gate opus, priority 11, depends T428a; paths `tests/resolve/generic_args_binding`; locks `compiler/resolve/resolver.ax`, `compiler/hir/lower.ax` (shared with later P12–P14 tasks that lock or own `compiler/resolve` / `compiler/hir`); covers REQ-MOD-003, REQ-MOD-064 |
| T428g | depends `[T428a, T428m]`; Scope rewritten as above; acceptance unchanged; `taskctl unblock T428g` (cycle 1) |

Id: `new-id --phase P11` reports the T400–T449 block full, so the next free suffix of the T428 series (`T428m`) is used.

## Board checks
- `taskctl.py lint` OK for T428m and T428g.
- `taskctl.py unblock T428g` -> `unblocked T428g`.
- `taskctl.py validate` -> `OK (776 tasks)`.
- `harness_check.py` -> `HARNESS OK` (only the standing optional guard-hook WARN).
- `reqcov.py --strict` -> `gaps: 0`, `COVERAGE OK`.
- No file of the running task T502 (compiler/interp, compiler/target/x64/frame.ax, tests/run/unsafe/oracle_ub) was touched.

## Files changed
- _workspaces/reports/unblock-T428g.md
- _workspaces/tasks/todo/T428g-fix-typeck-type-lookup-by-bare-name-cross-module-collision.md
- _workspaces/tasks/todo/T428m-fix-resolver-binds-paths-inside-generic-arguments.md
