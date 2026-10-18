# T082 Report — Port ownership, MIR builder, drop, verifier to Axiom (integration + differential MIR)

## Summary
- Integrated `compiler/mir` (`T082a`, `T082d`), `compiler/own` (`T082b`, `T082c`), and `compiler/verify` (`T082e`) with the frontend session pipeline (`compiler/kernel_source_diag`, `compiler/parser`, `compiler/resolve_hir`, `compiler/typeck`, `compiler/typeck_traits`) via [`compiler/own_mir_verify/session.ax`](file:///d:/projects/compiler/new%20lang/compiler/own_mir_verify/session.ax) and [`compiler/own_mir_verify/mod.ax`](file:///d:/projects/compiler/new%20lang/compiler/own_mir_verify/mod.ax):
  - `session_build_mir_fn`: builds pre-drop-elaboration `MirBody` from a `HIR_ITEM_FN` item using `CompilerSession.source_db`, `CompilerSession.interner`, `HirFile`, `Thir`, and optional `MonoEngine`.
  - `session_drop_elaborate_fn`: runs drop elaboration (`mir_drop_elaborate`) on a `MirBody` using `CompilerSession.source_db` and `CompilerSession.interner`.
  - `session_verify_mir_fn`: runs structural/CFG/type verification (`verify_mir`), ownership dataflow verification (`verify_mir_own`), capability/borrow verification (`verify_mir_cap`), and optional post-drop-flag consistency verification (`verify_mir_drop_flags`) into `CompilerSession.diag_sink`.
  - `session_own_mir_verify_file` and `session_own_mir_verify_file_with_synth`: executes the complete post-typeck ownership + MIR + drop + verifier pipeline matching `axiom0`:
    1. HIR raw-pointer/extern/intrinsic unsafe checking (`unsafe_check`, emitting `AX_UNSAFE_REQUIRED`).
    2. Per-function MIR lowering (`mir_build_fn`), optional pre-drop MIR printing (`inspect --emit=mir` format), and pre-drop structural MIR verification (`verify_mir`).
    3. Per-function HIR/MIR ownership, definite-initialization, and capability/region checking (`own_check`, emitting `AX_MOVE_USE_AFTER_MOVE` with `moved here` secondary labels, `AX_INIT_USE_UNINIT`, `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER`, `AX_TYPE_STORED_VIEW_ESCAPE`, `AX_TYPE_STORED_VIEW_SELF_REF`).
    4. When no diagnostics have been emitted, drop elaboration (`mir_drop_elaborate`), optional post-drop MIR printing, post-drop ownership/capability/drop-flag verification (`verify_mir_own`, `verify_mir_cap`, `verify_mir_drop_flags`), and optional synthetic `impl Drop for Guard` glue elaboration.
  - `session_own_mir_verify_and_render_human` and `session_own_mir_verify_and_render_json`: end-to-end virtual-file entry points that parse, resolve, lower to HIR, typecheck, build MIR, run ownership/drop/verifier passes, and render pre-drop MIR, post-drop MIR, and human or JSON diagnostics.
  - `session_verify_mir_text_and_render_human`: parses standalone `.mir` text via `verify_mir_text`, runs structural and ownership MIR verification (`verify_mir`, `verify_mir_own`), and renders human diagnostics.

## Differential Test Suite (`tests/selfhost/own_mir_verify/`)
- [`tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py`](file:///d:/projects/compiler/new%20lang/tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py) generates 9 selfhost differential test bundles from [`tests/selfhost/own_mir_verify/harness_mir_diff.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/own_mir_verify/harness_mir_diff.ax.in) and [`tests/selfhost/own_mir_verify/harness_diag_diff.ax.in`](file:///d:/projects/compiler/new%20lang/tests/selfhost/own_mir_verify/harness_diag_diff.ax.in):
  1. `qa_own_mir_diff_build_a.ax` (`[interp]`, `[native]`, `[native-O1]` — 5 cases: `bitnot`, `calls`, `div_assert`, `first_mir`, `mul_assert`): byte-for-byte pre-drop MIR parity vs `axiom0 inspect --emit=mir`, byte-for-byte post-drop MIR parity vs `cdriver_drop_oracle`, and zero diagnostics across `unsafe_check`, `verify_mir`, `own_check`, `verify_mir_own`, `verify_mir_cap`, and `verify_mir_drop_flags`.
  2. `qa_own_mir_diff_build_b.ax` (`[interp]`, `[native]`, `[native-O1]` — 4 cases: `qa_eval_order`, `shift_assert`, `short_circuit`, `unary_neg_assert`): same full pre-drop and post-drop MIR differential checks.
  3. `qa_own_mir_diff_drop_a.ax` (`[interp]`, `[native]`, `[native-O1]` — 3 cases: `d01_scope_exit`, `d02_conditional_move`, `d04_enum_variants`): byte-for-byte pre-drop and post-drop MIR parity plus full ownership and verifier checks.
  4. `qa_own_mir_diff_drop_b.ax` (`[native]`, `[native-O1]` — 7 cases: `d03_struct_fields`, `d05_mixed_nesting`, `d06_control_flow`, `d07_call_results`, `d09_closures`, `d10_destructor` including synthetic `impl Drop for Guard` pass, `d11_qa_edges`): byte-for-byte pre-drop, post-drop, and synthetic destructor MIR parity plus full ownership and verifier checks.
  5. `qa_own_mir_diff_diag_own_a.ax` (`[interp]`, `[native]`, `[native-O1]` — 4 representative `.ax` cases spanning `own`, `init`, `cap`, and `ptr` + JSON diagnostic rendering check): verifies diagnostic codes, `moved here` labels, byte-for-byte human diagnostic output vs `axiom0 check`, and JSON diagnostic rendering.
  6. `qa_own_mir_diff_diag_own_b.ax` (`[native]`, `[native-O1]` — all 11 negative fixtures in `tests/ui/own/*.ax`): byte-for-byte human diagnostic parity vs `axiom0 check`.
  7. `qa_own_mir_diff_diag_init.ax` (`[native]`, `[native-O1]` — all 7 negative fixtures in `tests/ui/init/*.ax`): byte-for-byte human diagnostic parity vs `axiom0 check`.
  8. `qa_own_mir_diff_diag_cap_ptr.ax` (`[native]`, `[native-O1]` — all 7 negative fixtures in `tests/ui/cap/*.ax` and `tests/ui/ptr/*.ax`): byte-for-byte human diagnostic parity vs `axiom0 check`.
  9. `qa_own_mir_diff_diag_verify_mir.ax` (`[interp]`, `[native]`, `[native-O1]` — all 21 `.mir` fixtures in `tests/verify/*.mir` and `tests/verify/own/*.mir`): verifies exact diagnostic counts, diagnostic codes, and human diagnostic rendering via `session_verify_mir_text_and_render_human`.

## Corpus Differential Counts
- **Positive MIR build + drop elaboration + verification corpus (`19` fixtures)**:
  - `9 / 9` fixtures in `tests/mir/build/*.ax` (`bitnot`, `calls`, `div_assert`, `first_mir`, `mul_assert`, `qa_eval_order`, `shift_assert`, `short_circuit`, `unary_neg_assert`): 100% byte-for-byte match on both pre-drop MIR (`axiom0 inspect --emit=mir`) and post-drop MIR (`cdriver_drop_oracle`), with 0 ownership or verifier errors.
  - `10 / 10` lowered fixtures in `tests/selfhost/drop/fixtures/*.ax` (`d01`–`d07`, `d09`–`d11`, plus `d10_destructor.synth.mir`): 100% byte-for-byte match on pre-drop MIR, post-drop MIR, and synthetic user-destructor MIR, with 0 ownership or verifier errors (`d08_generic_containers` remains gated on T081 generic struct literal typeck as documented in `T082d`).
- **Negative ownership, initialization, capability, and raw-pointer unsafe UI corpus (`25` fixtures)**:
  - `11 / 11` fixtures in `tests/ui/own/*.ax`: 100% byte-for-byte match with `axiom0 check` stderr (`AX_MOVE_USE_AFTER_MOVE` with `moved here` labels and `AX_INIT_USE_UNINIT`).
  - `7 / 7` fixtures in `tests/ui/init/*.ax`: 100% byte-for-byte match with `axiom0 check` stderr (`AX_INIT_USE_UNINIT` and `AX_MOVE_USE_AFTER_MOVE`).
  - `3 / 3` fixtures in `tests/ui/cap/*.ax`: 100% byte-for-byte match with `axiom0 check` stderr (`AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER`, `AX_TYPE_STORED_VIEW_ESCAPE`, `AX_TYPE_STORED_VIEW_SELF_REF`).
  - `4 / 4` fixtures in `tests/ui/ptr/*.ax`: 100% byte-for-byte match with `axiom0 check` stderr (`AX_UNSAFE_REQUIRED`).
- **Standalone `.mir` verifier corpus (`21` fixtures)**:
  - `21 / 21` fixtures in `tests/verify/*.mir` (`11` structural/type cases) and `tests/verify/own/*.mir` (`10` ownership dataflow cases): 100% diagnostic code and count parity with `axiom0`.
- **Total distinct corpus fixtures verified**: `65` fixtures (`19` positive MIR/drop + `25` negative `.ax` UI + `21` `.mir` verifier fixtures).
- **Sub-task selfhost suites (`T082a`–`T082e` + `T082`)**:
  - `tests/selfhost/mir` (`12` entries), `tests/selfhost/own` (`6` entries), `tests/selfhost/cap` (`3` entries), `tests/selfhost/drop` (`31` entries), `tests/selfhost/verify` (`6` entries), `tests/selfhost/own_mir_verify` (`23` entries): `81 / 81` PASS across `[interp]`, `[native]`, and `[native-O1]`.

## Verification
- `python tools/axtest.py --compiler build-snap-T082/build/axiom0.exe --root build-snap-T082 --filter selfhost/own_mir_verify -j 8`: `TOTAL 23 PASS 23 FAIL 0 SKIP 0 XFAIL 0`.
- `python tools/archcheck.py --root build-snap-T082`: `188 files scanned, 0 violations`.
- `python tools/archcheck.py`: `188 files scanned, 0 violations`.

## Files changed
- compiler/own_mir_verify/mod.ax
- compiler/own_mir_verify/session.ax
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
- tests/selfhost/own_mir_verify/harness_diag_diff.ax.in
- tests/selfhost/own_mir_verify/harness_mir_diff.ax.in
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax

STATUS: COMPLETE round=0
