# T444b QA report

## Round 0

Gate model: sonnet. Snapshot `build-snap-T444b` (HEAD `1324090` + this change set). Compiler under test:
the stage-2 `build-snap-T444b/build/axiomc2.exe` built by the engineer in the snapshot (STAGE1 OK, stage2 == stage3
fixed point, per the report; binaries present, dated after the change set).

### Checks performed

1. Report: last line `STATUS: COMPLETE round=0`. `taskctl.py changes T444b` stages exactly: the report,
   `compiler/own/init.ax`, `compiler/own/move.ax`, 3 run tests, 4 ui tests. No `REFUSED` line. Edits are inside
   `locks:` (`compiler/own/move.ax`, `compiler/own/init.ax`); `compiler/mir/builder.ax` is untouched (the engineer
   reverted the experiment). No shared file (`axtest.py`, CMake, `codes.def`, `pipeline.c`) edited, no new
   diagnostic, no `bootstrap/axiom0` change (R7 scope not touched).
2. `taskctl.py snapshot T444b`: `bundles regenerated in build-snap-T444b: 36 generator(s), 60 file(s)`, no
   "BUNDLES FAILED".
3. Gate: `python tools/taskgate.py --task T444b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
   (run by me, inside the snapshot): `TASKGATE T444b exit=0`, `axtest: TOTAL 154 PASS 154 FAIL 0 SKIP 0 XFAIL 0`,
   `WEAK-NATIVE: 15 in the run; 0 in the task's own/changed tests`, `Baseline: BASELINE OK`, `Failing ids: none`,
   `archcheck: clean (229 files scanned, 0 violations)`. Parts: own 7 ids / 13 results, affected 62 ids / 104 results
   (rule: `compiler/own` -> `tests/conformance/adversarial`, `tests/run/own`, `tests/selfhost/cap`, ... via
   `tools/affected_map.txt`, plus exact dependency of the own tests), smoke 31 ids / 50 results (one per group, 28
   groups). 67 results were cache hits (cache line: no CACHE-MISMATCH). No UNMATCHED/UNRESOLVED/DEFERRED entries.
4. Own tests with `--no-cache` (after adding my tests, snapshot refreshed):
   `axtest --filter pattern_multi_binding --no-cache`: `TOTAL 18 PASS 18 FAIL 0`, `WEAK-NATIVE 0`
   (4 run tests x interp/native/native-O1 + 6 ui).
5. Native evidence (step 4a): all run tests carry an exact `// stdout:` and `// exit: 0`; the native leg compares bytes.
   Spot proof of liveness: in the snapshot only, changed `two 10 20` to `two 10 21` in the expected stdout of
   `qa_adv_drop_paths.ax` (`sed -i 's/two 10 20/two 10 21/'`): `FAIL ... [interp]`, `FAIL ... [native]`,
   `FAIL ... [native-O1]`, `TOTAL 6 PASS 3 FAIL 3`; restored afterwards. Hand check: `axiomc2 build` of the same test
   gives a native executable whose stdout is byte-identical to `axiomc2 run` (interp).
6. Soundness probes versus baseline (reference baseline: the older main-tree `build/axiomc2.exe`, Nov 17, used only as
   an executable, never rebuilt or tested in the main tree):
   - T453 note: `fn f(e: E) -> u64 { match e { E.Both(n, w) => n + w, ... } }` with `enum E { One(u64), Both(u64, u64), None }`
     prints `42`; baseline reports `AX_MOVE_USE_AFTER_MOVE`. Fixed.
   - single-binding / `_` matches with owning payloads (`Two(x, _)`, `Wrap(_, c)`, conditional consume with a drop
     flag, `c(false)`): output byte-identical between baseline and the new compiler (same leaks of the ignored field,
     same drops), so no drop regression.
   - guarded arms that bind a non-Copy payload by value in both arms (`G.One(r) if r.id > 100` then `G.One(r)`): same
     `AX_MOVE_USE_AFTER_MOVE` in baseline and new compiler (pre-existing, see Follow-ups F-QA-2).
   - Own adversarial run test (below): guard reading only Copy payload, conditional consumption (maybe-moved,
     both flag values), three arms with different variants, re-assigning the consumed scrutinee, `(_, _)` pattern,
     user generic enums `Either<Res, i32>` and `Opt<Res>` / `Opt<i32>`: every owned field is dropped exactly once on
     every path, in interp/native/native-O1.
7. Acceptance criteria:
   - "Run tests pass in the three modes (WEAK-NATIVE 0); ui tests report exactly the expected diagnostics": met.
   - "Gate per axiom-qa.md; failing ids subset of baseline": met (no failing id).
   - "Report with root cause and exact Files changed": met; `## Files changed` is a literal list matching `changes`.

### Judgement of the "scrutinee only partially moved" part (report F4)

REQ-OWN-051 (`spec/requirements/CATALOG.md`) says by-value matching "shall move extracted payload fields and mark the
source variant as moved **or partially moved**". The task Acceptance list does not require the source local to stay
partially moved; the Goal/Scope sentence ("the scrutinee is partially moved afterwards") is met for the match
temporary the bindings read from (the enum node becomes PARTIAL, only the bound field places are moved) and the
source local is marked moved as a whole, which the REQ allows. The observable gap, `match c { E.Pair(a, b) => .. }`
with only Copy bindings followed by a second `match c` is still `AX_MOVE_USE_AFTER_MOVE`, is identical for a
single binding at baseline (`match d { E.Single(a) => .. }` twice fails on the baseline and the new compiler), i.e. it is
a general "match consumes a local scrutinee" behaviour that predates and is independent of the two-binding bug. The
engineer tried the in-place scrutinee match, which needs `compiler/mir/builder.ax` plus LIR goldens in
`tests/selfhost/lir/qa_lir_from_ax_d.ax.in` and `tests/selfhost/backend/qa_backend_native.ax` outside `paths:`, so
stopped and reported as the task Notes require. Verdict: not a FAIL of this task; it must become a follow-up task (below).

### Findings

None against the task (no FAIL finding).

### Follow-ups (for the architect)

- **F-QA-1 (= report F4)**: matching a drop-free local scrutinee in place (so Copy-only bindings leave the source
  usable and non-Copy bindings leave it PARTIAL) needs `compiler/mir/builder.ax` `mb_build_match_scrutinee` and a
  refresh of the embedded LIR goldens (`tests/selfhost/lir/qa_lir_from_ax_d.ax.in`,
  `tests/selfhost/backend/qa_backend_native.ax`); droppable scrutinees additionally need report F1 (drop of the
  remaining owned fields after a partial move; `Two(x, _)` leaks field 1 at HEAD and now). Repro:
  `tests/run`-style program `let c = E.Pair(3, 4); match c { E.Pair(a, b) => .. } match c { E.Pair(a, b) => .. }`.
- **F-QA-2 (pre-existing, not caused by T444b)**: guard arms with a by-value non-Copy binding in several arms of the
  same variant, `G.One(r) if cond(r) => .., G.One(r) => ..`, report `AX_MOVE_USE_AFTER_MOVE` in the second arm
  (guard binding is a real move). Rust binds by reference until the guard succeeds.
- Report findings F1, F2, F3 (leak after partial move, binding drop scope, struct-like enum variant literal verifier
  error) are confirmed as pre-existing by the probes above (F1 reproduced at baseline); they need their own tasks.

### Files changed

- tests/run/pattern_multi_binding/qa_adv_drop_paths.ax
- tests/ui/pattern_multi_binding/qa_adv_loop_second_iteration.ax
- tests/ui/pattern_multi_binding/qa_adv_binding_reused_after_move.ax

(Added by QA in the main tree under the task's `paths:`; they pass in the refreshed snapshot, see check 4.)

VERDICT: PASS round=0
