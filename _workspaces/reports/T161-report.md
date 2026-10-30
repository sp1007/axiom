# T161 report - AX0-FIX-09: trait default methods instantiated per implementing type

## Summary
A trait default method now behaves, for every implementing type that does not override it, as if its
body had been written in that type's impl (0133 Ã‚Â§8, Ã‚Â§9, Ã‚Â§14; REQ-TRT-005, REQ-TRT-011). The fix is in
axiom0 and the port under `compiler/`, in lockstep (ADR-0034 Ã‚Â§2). axiom0 and axiomc produce
byte-identical `.exe`/`.obj` output (-O0 and -O1) for every trait program in the corpus.

Root cause: a default body was type-checked and lowered once, as the trait member, with `Self` as a type
parameter. A `self.m()` call in it was bound to the trait member `m`. Both executors then picked "the
first impl that has a member named `m`": the interpreter through its bodyless-member fallback, and
native mono because `impl_matches_receiver` fails on a `Self` parameter. A second defect made generic
default methods unsound: `Self` was interned as `AX_TY_PARAM` with index 0, and parameter equality
compares only the index, so `Self` and a method's own `U` (also index 0) were the same type.

### Design (axiom0 and port alike)
1. **A distinct `Self` parameter.** Inside a trait, `Self` is `PARAM` with the reserved index
   `0xFFFFFF00` (`TC_SELF_PARAM_INDEX`). The same value appears in typeck, mono and the MIR builder,
   each with a comment naming the others. Before this change the port interned the trait `Self` with
   index `0xFFFF` in signatures and `0` in bodies; it now uses `0xFFFFFF00` in both.
   At a method call, the callee signature's `Self` is replaced by the receiver's type
   (`ax_subst_ty` with `cx->subst_self` in C; `subst_ty_self` in the port).
   `deduce_args` in axiom0 mono is now bounded by the argument count, so the reserved index can never
   write out of bounds (the port's version was already bounded).
2. **Default-method instances as impl members.**
   - What typeck adds: before pass 1a, for every `impl Trait for T` and every trait member with a body
     that the impl does not override, typeck appends to the impl a copy of the trait member item. The
     copy shares the HIR body and gets a fresh symbol `0x50000000 + n`. `n` counts in program order:
     impls in item order, then trait members in declaration order. The range `0x50000001..0x5FFFFFFF`
     is used by nothing else: resolve uses 1.., closures 0x4..., synthetic locals 0x6..., drop 0x7...,
     and hir/lower.c 0x8....
   - Signature: pass 1b computes the copy's signature with `Self` = the impl type.
   - Body check: pass 2 skips the copy, because the shared body is checked once, as the trait member.
     In the port, `register_item_sig` also leaves the shared params' types alone, as axiom0 does.
   - Method lookup on `T` finds the copy like a hand-written member.
   - Links for the MIR stage: typeck records the implementing impl and type under the copy's address
     tagged with 2, in `expr_methods` and `item_types`. Items are 8-aligned, and the existing drop-impl
     keys use tag 1.
3. **Instantiated MIR.** The MIR of an instance is built from the shared body. In it:
   - `Self.CONST` reads the impl's constant (builder: `self_impl_const` / `mb_self_impl_const`).
   - Then `Self` is replaced by the impl type in locals and constant operand types.
   - Every call of a trait member whose receiver is now concrete is bound to that type's impl member:
     an override, or the type's own instance. The search tries impls of the declaring trait first,
     then any trait impl.
   - Calls on other parameters (a default method's own `U`) are left alone; native mono binds them per
     instance, as for any generic function.
   - Where this runs: axiom0 `driver/mono.c ax_mono_instantiate_default`, called from
     `pipeline.c build_mir_for_item` before verification. That body goes into the MIR map, which the
     interpreter and mono both read. In the port it runs at the end of `mir_build_fn_subst`
     (`mb_instantiate_default`), so the build path, mono preparation and the interpreter's on-demand
     build all see it. Generic clones made by the port's mono keep the tags
     (`mb_copy_default_inst_tags`).
4. **Symbols.** No new naming scheme. An instance is an ordinary mono instance named after the method.
   The existing dedup pass gives colliding instances `<name>_<symbol>`, for example
   `twice_1342177281` and `twice_1342177282`. That name is deterministic, and axiom0 and the port
   produce it identically (checked with objdump on every test below). The `$` form of ADR-0034 Ã‚Â§6 was
   not needed: the symbol suffix keeps names unique. A user item could only collide by being written
   literally as `twice_1342177281`, which is the same pre-existing risk as for every dedup name.
5. **Port emission** (`compiler/driver/pipeline.ax`). In build mode, instances are emitted next to the
   T153 trait-member instances. The function-buffer capacity counts them, which fixed a dropped last
   instance found by the byte comparison (`default_vs_override.ax` failed to link before that fix).

### Effects on existing behaviour
- The THIR dump of a trait program now lists the instance members under each impl. They are dumped
  the same way by both compilers.
- Every existing `tests/run/trait2/**`, `tests/run/parity/traits/**`, conformance p7 and ui trait
  expectation is unchanged. The baseline run before the change was 130/130; the same set with the
  change was 142/142, the extra 12 being the new tests.
- An unsafe-operation error inside a default body is now reported by axiom0's `own/unsafe` pass once per
  non-overriding impl, because the pass walks impl members. Before, trait bodies were not unsafe-checked
  at all. This is outside my paths; see Follow-ups.

## Tests
New `tests/run/parity/trait_default/` (`modes: interp native`, expected stdout written by hand):
- `self_call_per_type.ax`: the program from the task with three types, C overriding `twice`.
  Expected `18 20 77 9 10 11`; HEAD gave `18 18`.
- `supertrait_call.ax`: a subtrait default calls a supertrait method, and a default calls another
  default; two types. HEAD gave `103 206 4 103 206` instead of `... 104 208`.
- `generic_default.ax`: default `either<U>` with its own parameter, used by two types with `U` = i64
  and bool. HEAD gave `7 7 0 0`.
- `assoc_const_in_default.ax`: `Self.MAX` read in two default methods across two impls. HEAD gave
  `0 0 1 1`.

All four fail on HEAD's axiom0 (checked with `build-snap-T153/build/axiom0.exe`) and pass in both
modes with the fix.

Parity check: I compared axiom0 against the natively built axiomc, using the e2e oracle's commands
(`build`, `build --emit=obj`, -O0 and -O1, image bytes plus diagnostics). The programs were the four
new tests, `tests/run/parity/traits/*`, `tests/run/trait2/*`, `tests/run/trait/*`,
`native_p7/qa_trait_dispatch.ax`, `parity/generics/qa_generics_edges.ax` and the trait programs of
`conformance/p7`. Result: 0 differences.

Selfhost bundles: 53 bundles were regenerated in `build-snap-T161` from the final `compiler/` sources
and copied over. All 36 `gen_*_tests.py --check` report up to date. The only reason they changed is the
four `compiler/` modules they embed (typeck, traits/mono, mir/builder, driver/pipeline).

Build: gcc Debug build is warning-free, and the clang build has no warnings in the changed files.
`archcheck`: 192 files, 0 violations.

Full suite (`build-snap-T161`, `python tools/axtest.py --compiler build/axiom0.exe -j 4 --timeout-scale 2`,
native legs included): see the Round 0 result below.

## Decisions (for the architect)
- **Instances as synthesized impl members rather than a HIR deep clone.** Cloning the HIR would
  re-type-check each body, but it needs a full HIR cloner in C and in Axiom, and the closures and
  locals keyed by symbol would have to be re-symbolled. Sharing the body and instantiating at MIR
  level keeps one type check, and mono and the interpreter need no changes.
- **Reserved `Self` index `0xFFFFFF00`, duplicated as a `#define`/`const` in typeck, mono and the
  builder** (C), and in typeck, traits/mono and mir/builder (port). The value belongs in `types.h` /
  `types.ax`, which are outside this task's paths. I recommend moving it there.
- **Tagged-address side tables (tag 2)** in `expr_methods`/`item_types` link an instance to its impl
  and type. This follows the existing tag-1 drop-impl keys. A real field on the HIR item would be
  cleaner, but `hir.h`/`hir.ax` are outside the paths.

## Spec deviations
none

## Follow-ups (to axiom-architect)
- **Different cause, outside my paths: the interpreter does not instantiate generic functions.**
  T153-QA reported a generic fn binding the first impl in `run --interp`. That repro still prints
  `42 42` (native prints `42 100`):
  - `fn via_bound<T: Greet>(x: view<T>) -> i32 { x.hello() }`, with `A.hello() = 42` and
    `B.hello() = 100`.

  Cause: `bootstrap/axiom0/src/interp/interp.c` `eval_call` executes a generic body once, for all
  instantiations, and dispatches a bodyless trait member to the first impl member with that name. The
  same happens in the port, `compiler/interp/interp.ax` around line 1047.

  This is not the T161 cause: there, the default body was compiled once. Here, the interpreter has no
  type arguments at run time. The same defect affects a trait call on a default method's own
  parameter (`u.weight()` with `U` generic). That is why `generic_default.ax` does not dispatch through
  `U`; its header comment says so.

  Proposed fix: a per-frame type substitution in the interpreter (axiom0 `interp/interp.c`, and the
  port's interp). Bind the callee's generic arguments from the caller's concrete argument types, then
  dispatch bodyless trait members on the substituted receiver type. That needs `interp/interp.c` in a
  task's paths. Once it is done, add the via_bound repro and a `u.weight()` variant as regression tests.
- Duplicated unsafe diagnostics: `own/unsafe/unsafe.c` checks impl member bodies and so now checks a
  shared default body once per instance. Skipping symbols in `0x50000000..0x5FFFFFFF` there, and
  checking trait member bodies once instead, would give one diagnostic. The same applies to the port's
  unsafe checker in `typeck.ax`, which mirrors axiom0.
- Tuple expressions whose elements are names, such as `(w, u)` in a plain fn, are rejected with
  `AX_NAME_UNRESOLVED`. Generic struct types in signatures (`-> Pair<U>`) are rejected the same way.
  Both are pre-existing gaps found while writing tests, unrelated to traits.

## Files changed
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/driver/mono.c
- bootstrap/axiom0/src/driver/mono.h
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/mir/build/builder.c
- compiler/types/typeck.ax
- compiler/traits/mono.ax
- compiler/mir/builder.ax
- compiler/driver/pipeline.ax
- tests/run/parity/trait_default/self_call_per_type.ax
- tests/run/parity/trait_default/supertrait_call.ax
- tests/run/parity/trait_default/generic_default.ax
- tests/run/parity/trait_default/assoc_const_in_default.ax
- tests/run/parity/trait_default/self_static_args.ax
- tests/run/parity/trait_default/qa_default_edges.ax
- tests/run/parity/trait_default/qa_default_self_static_call.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

## Round 0 result
- Full suite in `build-snap-T161` (axiom0 built fresh, gcc Debug, native legs, `-j 4 --timeout-scale 2`):
  TOTAL 2884, PASS 2883, FAIL 1 (WEAK-NATIVE 165, the runner's existing notices). The one failure was
  `selfhost/obj_link_driver/bundles_current.test`: the `driver` and `obj_link_driver` bundles embed
  `compiler/driver/pipeline.ax` and had not been regenerated. My freshness check had used the generators'
  exit code, which is 0 even when a bundle is stale.
- Fixed by regenerating those 6 bundles in the snapshot (now every generator reports no `DIFFERS`). Then I
  re-ran `selfhost/driver` and `selfhost/obj_link_driver`, including the whole-corpus
  `axiomc_e2e.test`: 26/26 PASS. `known_divergent.txt` is unchanged and has no entries.
- Not verified as one single run: the whole suite was not run a second time after the regeneration. Only
  bundle files changed after that run, and the affected test directories were re-run and pass.


## Round 1
Fix for QA finding F1 (`Self.k()`, a receiver-less trait member call inside a default body, bound to the first
impl in both compilers and both legs).
- Cause: the MIR instantiation of a default instance took the receiver type from `args[0]` and skipped calls with
  `arg_count == 0`, so a static trait member call (`Self.k()`, and `Self.k(x)` whose first argument is not a
  receiver) was never rebound.
- Fix, in lockstep (ADR-0034 Â§2): `ax_mono_instantiate_default` (bootstrap/axiom0/src/driver/mono.c, new helper
  `tm_has_self_param`) and `mb_instantiate_default` (compiler/mir/builder.ax, new helpers `mb_tm_has_self`,
  `mb_sv_is_self`) look at the called trait member: if its first parameter is `self`, the receiver type comes from
  `args[0]` as before; otherwise the rebinding type is the instance's implementing (Self) type recorded by typeck.
  The call is then bound through `impl_member_for` / `mb_impl_member_for` exactly as for method calls, so the
  symbols are identical in both compilers.
- New test `tests/run/parity/trait_default/self_static_args.ax` (`modes: interp native`, hand-written stdout):
  `Self.k(v)` with arguments, a two-argument `Self.mix(v, Self.scale())`, `Self.scale()` reached from a default
  called by another default (method chain `outer -> inner` and static chain `chain -> base`), two implementing
  types with one override (`17 45 31 71 103 107 13 29`). QA test `qa_default_self_static_call.ax` unchanged.
- Evidence (snapshot `build-snap-T161`, Clang -O3 build):
  - `axtest -j 1 run/parity/trait_default run/trait2 run/parity/traits`: TOTAL 61 PASS 61 FAIL 0 (incl.
    `qa_default_self_static_call` and `self_static_args` in interp, native, native-O1).
  - gcc build (`build-snap-T161/build-gcc`, mono.c forced to recompile): exit 0, 0 warnings.
  - All `tests/selfhost/*/gen_*_tests.py` regenerated in the main tree (drop with `bundles`): no generator printed
    `DIFFERS`; only the round-0 bundle set is modified. `--filter bundles_current`: 34/34 PASS.
  - `selfhost/obj_link_driver/axiomc_e2e.test`: PASS; `known_divergent.txt` unchanged, 0 entries.
  - `archcheck.py`: 192 files, 0 violations. `taskctl.py changes T161`: 0 REFUSED.
- Full suite (`Set-Location build-snap-T161; python tools/axtest.py --compiler build/axiom0.exe -j 1`, one run after
  all round-1 edits and bundle regeneration): TOTAL 2893 PASS 2893 FAIL 0 SKIP 0 XFAIL 0 WEAK-NATIVE 165.

STATUS: COMPLETE round=1
