# ADR-0047 — Drop scope of `match` / `if let` / `while let` pattern bindings is the arm

Status: accepted (2026-11-21, architect; owner-delegated decision). Type C (semantic statement: fixes the observable drop
point of by-value pattern bindings). Fix task: T445a.

## Tóm tắt
- Hiện nay compiler drop một binding theo giá trị trong arm của `match` (ví dụ `FiberState.Yielded(_g) => ..`) ở cuối
  **khối bao quanh** (thậm chí cuối hàm), không phải cuối **arm**. T445 (báo cáo, mục 2) và T444b (F2) đã ghi nhận và cần quyết định.
- Quyết định: mỗi arm là một scope riêng (`0134 §26`, `APATTERN-28` "binding chỉ sống trong arm", `0159 §26`). Binding theo
  giá trị bị drop ở cuối arm, theo thứ tự ngược với thứ tự khai báo trong pattern, trên mọi cạnh thoát arm (kết thúc bình
  thường, `return`, `break`, `continue`, `?`, panic). Giống vậy cho `if let` (cuối khối then), `while let` (cuối mỗi vòng lặp)
  và `let`-else không áp dụng (binding của `let` sống tới cuối khối như mọi `let`).
- Phần của scrutinee không bị move vào binding vẫn ở lại place gốc và được drop theo place đó (drop flag từng phần).
  Scrutinee là giá trị tạm (rvalue) thì phần còn lại bị drop ở cuối câu lệnh `match`.
- Test `tests/std/async/structured/resource_governor_limits` đang dựa vào hành vi cũ (lease bị move vào `l` phải sống tới
  cuối khối) — đó là test sai so với nguồn chuẩn; T445a sửa test để kiểm tra mà không move (`view`).
- Revisit: không.

## Context
- `_workspaces/reports/T445-report.md` "Deviations" 2 and follow-up 2: the draft of T445 moved match/if-let binding drops to the
  end of the arm and broke `std/async/structured/resource_governor_limits.ax`, so it was reverted; "needs an ADR".
- `_workspaces/reports/T444b-report.md` F2: `got 1 2\nafter-two\ndrop 2\ndrop 1` — arm bindings dropped at the end of the
  enclosing function; interp, native and native-O1 agree.
- T423 QA (fiber tests) observed the same with `Yielded(_g)`; reproducible with a plain enum with a `Drop` payload.
- Sources: `docs/base/specs/0134` §26 "Match arm là scope" and APATTERN-28 ("Bindings chỉ sống trong arm"),
  `docs/base/specs/0159` §26 (match arm scope), SPEC-12 AXS-DROP-001 (destructors run when an owned place goes out of scope)
  and AXS-DROP-002 (reverse declaration order), AXS-DROP-003 (drop flags for partially moved places).
- No canonical spec rule fixes the drop point of a pattern binding today (gap).

## Options
1. Keep the current behaviour (end of the enclosing block). Contradicts APATTERN-28 / 0134 §26 (a binding that is not
   visible outside the arm would keep a resource alive after the arm); lock guards and leases bound in an arm would be held
   across later statements, surprising and deadlock-prone; it is also not the end of the *block* consistently (T444b sees end of
   function).
2. **End of the arm (chosen).** Follows the frozen sources, matches lexical scoping (a binding dies where its scope ends,
   AXS-DROP-001), same as Rust, and makes guard-in-arm code release at the expected point.
3. End of the whole `match` expression. Simpler to elaborate but still keeps the binding alive across sibling arms' code paths
   for no benefit; not supported by the sources.

## Decision
New rule SPEC-12 **AXS-DROP-009** (Drop scope of pattern bindings):
1. Each arm of a `match` is a drop scope. A by-value binding introduced by the arm's pattern (including bindings inside nested
   patterns and `@` bindings) that is still initialised at the end of the arm is dropped at the end of the arm — after the arm
   body's own locals (which are inner scopes), in reverse order of the bindings' left-to-right position in the pattern. The same
   happens on every edge leaving the arm early (`return`, `break`, `continue`, `?`, panic under `--panic unwind`).
2. The guard (`if cond`) does not move: bindings are bound by view for the guard; the move into the by-value binding happens
   only when the arm is selected (unchanged; stated for completeness).
3. A value moved out of a binding inside the arm (into a call, a field, a return value) is not dropped there (AXS-DROP-003).
4. `if let P = e { A } else { B }`: bindings of `P` are dropped at the end of `A`. `while let P = e { A }`: at the end of each
   iteration of `A` (also on `continue`/`break`).
5. The scrutinee: when it is a place, the parts not moved into bindings stay in that place, which is dropped by its own scope
   with partial-move drop flags (AXS-DROP-003). When it is a temporary, the remaining parts are dropped at the end of the
   `match` / `if let` statement (before the next statement).
6. `let P = e;` (irrefutable, and the bindings of `let ... else`) keep the ordinary `let` rule: dropped at the end of the
   enclosing block.

## Consequences
- Fix task **T445a** (axiom-semantics, P11): MIR builder scopes for arms/if-let/while-let, interp and native agree, tests,
  and the update of `tests/std/async/structured/src/resource_governor_limits.axsrc` (check the lease result without moving it,
  e.g. a `view<Result<..>>` helper) plus any other test that pinned the old drop point (the gate reports them; each is
  corrected to the new rule in T445a, never left failing).
- SPEC-12 gains AXS-DROP-009 (applied now). The compiler's own sources (`compiler/`, `std/`) may rely on the old point; T445a
  keeps the stage-2/stage-3 fixed point and the selfhost groups green.
- Existing tests that already avoid the issue (T444b binds every owned field) are unaffected.

## Revisit
- No.

## Sources
- `docs/base/specs/0134` §26, APATTERN-28; `docs/base/specs/0159` §26; `spec/SPEC-12-drop.md` AXS-DROP-001..003;
  `_workspaces/reports/T445-report.md`; `_workspaces/reports/T444b-report.md` F2; `_workspaces/reports/T423-qa.md`.
