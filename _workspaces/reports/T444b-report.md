# T444b report — tuple-variant pattern with two bindings (round 0)

Note: the attempt was interrupted once by a usage-limit error (infrastructure) and resumed.

## Root cause
Ownership analysis (`compiler/own`) tracks places on a per-local *path tree* (`PathCtx`). The tree
only had children for `TY_STRUCT`/`TY_TUPLE`; an enum node was a leaf, and `resolve_place` /
`own_bits_resolve` skipped `DOWNCAST` projections and ignored a `FIELD` index that had no child.
So the payload place `(scrut as Pair).0` resolved to the **whole enum node**, whose `is_copy` is
the enum's (false for a non-Copy enum, even when the field is `u64`). Binding `a` therefore marked
the whole scrutinee MOVED and binding `b` (`(scrut as Pair).1`) was reported as
`AX_MOVE_USE_AFTER_MOVE` with "moved here" on `a`.

(The bindings read from the match temporary `_t` that `mb_build_match_scrutinee` fills from the
scrutinee, so it was `_t` that was marked wholly moved by the first binding.)

## Fix
- `compiler/own/move.ax`: enum nodes now get one child per variant (`populate_enum_variants`), and
  each variant node one child per payload field (recursively populated like struct fields). A new
  `PathNode.is_enum` flag marks enum nodes; the shared `path_child(ctx, node, kind, idx)` follows a
  `DOWNCAST` only on an enum node and a `FIELD` only on a non-enum node (anything else keeps the
  node, i.e. the old conservative behaviour). `update_parent`/`mark_state` work unchanged: moving
  `(o as Two).0` makes the variant node and the enum PARTIAL; assigning the whole enum marks every
  variant/field OWNED again.
- `compiler/own/init.ax`: `own_bits_resolve` (the drop-flag bitset walk) uses `path_child` too.
- Note: `path_child` takes `(kind, idx)` rather than a `*const MirProjection` because the selfhost
  bundler's `compiler.own.move_ck` rewrite injects `use compiler.mir.mir.MirProjection` itself, so
  importing it in `move.ax` made stage 1 fail with `AX_NAME_DUPLICATE`.

## Decisions (for the architect)
- MIR construction is unchanged: a scrutinee on a plain local is still moved/copied into a match
  temporary, and the bindings partially move that temporary. So after `match c { .. }` the source
  `c` is wholly consumed (not PARTIAL), and any later whole use is the required error. I tried
  matching drop-free local scrutinees in place (`compiler/mir/builder.ax`, within this task's
  locks): it works (Copy-only bindings then leave `c` usable), but it changes the LIR/MI shape of
  every such match and broke the embedded LIR goldens of `tests/selfhost/lir/qa_lir_from_ax_d.ax.in`
  and `tests/selfhost/backend/qa_backend_native.ax` (outside this task's paths), so it was reverted.
  It is recorded as F4 below. In-place matching of droppable scrutinees would in addition need F1.
- A match on a partially moved enum reports the use at the scrutinee (the discriminant read uses the
  whole value), like Rust's E0382 on a partially moved enum.

## Findings (pre-existing, outside this task's locks — follow-up tasks suggested)
- **F1 (drop elaboration, `compiler/mir/drop.ax`):** after a partial move, the remaining owned
  fields are never dropped. Repro on HEAD `b62355d`: `let p = Pair { a: Res{5}, b: Res{6} }; let
  x = p.a;` prints only `drop 5` (field `b` leaks); likewise `match o { Two(x, _) => .. }` never
  drops field 1. The run tests here therefore bind every owned field.
- **F2 (arm binding drop scope):** by-value arm bindings are dropped at the end of the enclosing
  function, not at the end of the arm (e.g. `got 1 2\nafter-two\ndrop 2\ndrop 1`). Consistent in
  interp/native/native-O1; the run test is written so it does not depend on this.
- **F3 (struct-like enum variant literal):** `Pair.Named { left: .., right: .. }` fails with
  `AX_VERIFY_TYPE_MISMATCH: enum aggregate variant field count mismatch` on HEAD (baseline too).
  Struct-variant patterns are therefore not in the tests.
- **F4 (match consumes the whole scrutinee):** `match c { Choice.Pair(a, b) => .. }` with only
  Copy bindings on a non-Copy enum `c` still moves `c` (the match temporary), so a second
  `match c` is `AX_MOVE_USE_AFTER_MOVE`. REQ-OWN-051 asks for the source to be *partially* moved.
  Fix: match drop-free local places in place in `mb_build_match_scrutinee` (a 6-line change, see
  Decisions) together with refreshing the LIR goldens in `tests/selfhost/lir/qa_lir_from_ax_d.ax.in`
  and the backend corpus; for droppable scrutinees, after F1.

## Tests
- `tests/run/pattern_multi_binding/copy_payload_bindings.ax` — Copy payloads: two/three bindings,
  mixed `u8`/`u64`, `if let`, `while let`, struct pattern inside a variant, nested variant.
- `tests/run/pattern_multi_binding/owning_payload_bindings.ax` — `Drop` payloads: 2 and 3 bindings,
  mixed owned/Copy, `if let`, `while let`, struct destructuring, nested variant; every field dropped
  exactly once.
- `tests/run/pattern_multi_binding/nodrop_noncopy_bindings.ax` — non-Copy payloads that need no
  drop, nested, re-assigning the consumed scrutinee then matching again.
- ui: `use_scrutinee_after_payload_move.ax`, `one_field_moved_then_whole_use.ax`,
  `payload_field_moved_twice.ax`, `nodrop_payload_moved_then_whole_use.ax` — each exactly one
  `AX_MOVE_USE_AFTER_MOVE`.
- Baseline (HEAD compiler): both original run tests fail with `AX_MOVE_USE_AFTER_MOVE` on the second
  binding (the reported repro).

## Results (snapshot `build-snap-T444b`, HEAD `1324090` + this change set)
- `tools/build_axiomc.py --out build`: STAGE1 OK, stage2 == stage3 fixed point OK, STAGE0-GUARD OK,
  stage2 O1 `sha256=243b60bb6951563e`.
- `axtest --filter pattern_multi_binding`: `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
  (3 run tests x interp/native/native-O1 + 4 ui).
- Also re-run with `--no-cache`: `selfhost/lir/qa_lir_from_ax.ax` and `selfhost/backend/qa_backend_native.ax` PASS (they failed only with the reverted builder change).
- `python tools/taskgate.py --task T444b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  `TASKGATE T444b exit=0`, `axtest: TOTAL 154 PASS 154 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE: 15 in the run; 0 in the task's own/changed tests`,
  `Baseline: BASELINE OK`, `Failing ids: none`, `archcheck: clean (229 files, 0 violations)`.

## Files changed
- compiler/own/move.ax
- compiler/own/init.ax
- tests/run/pattern_multi_binding/copy_payload_bindings.ax
- tests/run/pattern_multi_binding/owning_payload_bindings.ax
- tests/run/pattern_multi_binding/nodrop_noncopy_bindings.ax
- tests/ui/pattern_multi_binding/use_scrutinee_after_payload_move.ax
- tests/ui/pattern_multi_binding/one_field_moved_then_whole_use.ax
- tests/ui/pattern_multi_binding/payload_field_moved_twice.ax
- tests/ui/pattern_multi_binding/nodrop_payload_moved_then_whole_use.ax

STATUS: COMPLETE round=0
