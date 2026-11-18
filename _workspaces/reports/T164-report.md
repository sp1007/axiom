# T164 Report — AX0-FIX-10: one symbol-id space

## Summary
- axiom0 and axiomc now number every symbol — user, std, extern and the four synthetic prelude traits — from one
  per-compilation counter (`next_symbol_v`), in unchanged allocation order (deterministic). Two distinct symbols no
  longer share an id whatever the program size (ADR-0043 §2, INV-BOOT-005, REQ-RES-060).
- The one place that derived a property from an id's numeric range (`solver.ax` `sym_is_std_item`) now derives the
  std/user domain from stored HIR data (module paths, `use` trees), see "Design decision".
- Code, regression test, T444 reproduction, fresh stage 1-3 bootstrap with fixed point, C unit tests, archcheck and
  harness_check are done.
- Round 0 was first reported BLOCKED on paths (HIR/THIR goldens print ids as `@n`, and 16 selfhost harness
  templates bake expected dumps). The orchestrator extended `paths:`; the 7 goldens and 16 templates are updated
  (ids only, verified mechanically), see "Unblock: goldens and harness tables".

## Changes
- `bootstrap/axiom0/src/resolve/resolve.c`, `resolve.h`: `new_symbol` draws from `next_symbol_v` only;
  `new_symbol_extern` delegates to it. The synthetic prelude traits `Fn`, `FnMut`, `FnOnce`, `Callable` (formerly
  hard-coded 10100..10103, which a program with more than 10100 symbols reused) get counter ids right before the
  body pass (after collection, imports and the prelude export), so every collection-pass id (items, variants,
  modules) is unchanged and MIR dumps (which print fn ids) are unaffected. `AxResolveMap.next_std_symbol_v` and
  `Env.next_extern_symbol_v` removed. `driver/mono.c` untouched: `++next_symbol_v` now continues after every symbol.
- `compiler/resolve/resolver.ax`: the same in lockstep (ADR-0034 §2): `next_symbol_id` single counter,
  `next_extern_symbol_id` delegates, `assign_prelude_trait_ids` before the body pass; `ResolverEnv.next_extern_symbol_v`
  removed.
- `compiler/resolve/symtab.ax`: `ResolveMap.next_std_symbol_v` stays as an unused, documented field set to 0 — ~45
  harness templates under `tests/**` (`*.ax.in`, outside this task's paths) build `ResolveMap` literals naming it
  (the task allowed "leave them unused with a comment"). `compiler/driver/pipeline.ax` initialises it to 0 instead of
  10000. `compiler/hir/lower.ax` needs no change: it hands `rmap.next_symbol_v` (now the first id after all symbols)
  to mono.
- `compiler/traits/solver.ax`: `sym_is_std_item` removed; `find_trait_item` / `trait_auto_kind` take the referencing
  type path (`site`); helpers `hir_item_is_std`, `hir_item_in_prelude_module`, `hir_items_same_module`,
  `segs_eq_idx`, `use_tree_binds`, `site_use_domain`, `site_path_is_std` (+ the module-local `size_of` intrinsic
  declaration other modules carry); `check_impl_supertraits` compares the two items' module paths.
- Grep of both compilers for other id-vs-constant comparisons (`[<>]=? *(10000|30000)` and every 1xxxx/3xxxx literal
  next to a symbol): none besides the counter bases removed here. Remaining fixed sentinels (equality, not ranges;
  out of scope, see Follow-ups): `10007`/`10008` (Send/Share with an empty trait name) in `solver.ax`, `typeck.ax`,
  `pipeline.ax`; `10009` (placeholder for an unresolved `Future`) in `lower.ax`.

## Design decision (for the architect: note under ADR-0043 §2)
A trait path never carries the HIR trait item's own symbol: the resolver's collection pass gives the trait id C and
its body pass declares `Self` with the trait item as node, which rebinds the item node to a fresh id S. The HIR trait
item has symbol S while every reference (`T: Ord`, `impl Ord for X`) carries C, so `find_trait_item` almost always
falls back to a name lookup, and T432's `sym_is_std_item` used the numeric range of C to pick the same-named trait of
the right domain (user `Clone` vs std `Clone`, user `Future` vs prelude `Future`). Neither C's std flag nor the
resolver's naming table is reachable from the solver (its callers in `typeck.ax` — T444's uncommitted file — pass
only hir/thir/str_in/db), so the domain is derived from stored HIR data, i.e. from what the resolver's lexical lookup
from the referencing site must have bound:
1. an item carrying `sym` -> its `module_path` (exact);
2. otherwise, from the site's module (the last `module` declaration of the same file before the path, else the last
   item before it): a path spelled `std.` -> std; a `use` in that module binding the name -> the domain of the use
   path; else a trait of that name in the same module; else a trait of the prelude modules (`std.core.prelude`,
   `std.sync.atomic`); else (a resolver primitive such as `Copy`, `Send`, `Fn`) the first user trait — exactly as
   under the former id ranges.
Each rule is there because a simpler version failed on real code (do not "simplify" it back): item-only domain broke
std `F: Future` / `T: Ord` bounds in stage 2; a fallback to any domain broke `@derive(Copy)` (resolver primitive
`Copy` matched std's `Copy: Clone`); HIR item spans cover only the item head and impl members are hoisted with an
empty module path, hence "last module declaration / item before the path"; prelude before user traits fixes a user
file that defines its own `Future` next to std's `block_on`.
Evidence: `check` of all 902 non-selfhost test files that use traits/impls/generics gives the same exit code and
error set with HEAD `axiomc2` and the T164 `axiomc2`, except `run/symbol_id_space/many_symbols.ax` (fixed).
Known residual difference: user code naming a std trait through a re-export path that does not start with `std.`
while another user module defines a trait of the same name. The exact fix (the resolver's per-symbol std flag
reaching the solver) needs `typeck.ax`/`hir.ax` plumbing — Follow-up 1.

## Regression test `tests/run/symbol_id_space/`
- `gen_symbol_id_space.py` (stdlib, `--check`; `--axiom0 <path>` writes a variant without `std.core.cmp` for the
  frozen axiom0, which cannot load that module on demand) writes `many_symbols.ax` (167 KB, ~30 317 user symbols:
  576 enums x 50 variants, 300 generic `fn gid_<k><T>(x: T) -> T` whose `T`/`x` ids span the old extern window
  30000.., 6 kernel32 externs called from a function behind a never-true runtime guard (`sum == 7`; direct externs
  cannot run in the interpreter, ADR-0002), `std.core.cmp.Ord`/`Ordering` incl. a generic `T: Ord` bound), exact
  `// stdout:`, modes interp + native (+ native-O1 added by the runner).
- T164 `axiomc2`: PASS interp, native, native-O1; WEAK-NATIVE 0.
- Baseline: HEAD `axiomc2` fails it (16x `AX_TYPE_MISMATCH`: user ids above 10000 collide with std symbols, e.g. at
  `print_int`). HEAD axiom0 (built from `git archive HEAD`) on the axiom0 variant: 6x `AX_TYPE_NOT_CALLABLE` at the
  extern calls (T444 B2 exactly). Fixed axiom0 on the variant: PASS `run --interp`, native, native -O1.

## T444 reproduction (temporary edit in a scratch copy of the tree, not committed)
`git archive HEAD` tree + a function with 60 locals appended to `compiler/obj/coff.ax` (module `compiler.obj.coff`,
index 66 of 86 in bundle order, right before `compiler.obj.writer`):
- HEAD axiom0: `bootstrap.py --stage 1` FAIL; `axiom0 build` of the bundle: 4x `AX_TYPE_NOT_CALLABLE` at
  `CommandLineToArgvW` (+4 follow-on `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` on its result).
- fixed axiom0 + final T164 sources + the same dummy: `STAGE1 OK` (26 391 552 bytes).

## Highest symbol id of the axiomc bundle
- before (HEAD, `inspect --emit=resolved` with HEAD axiom0): 38 558 for user symbols, which use 1..38 558 densely —
  they covered the whole std range 10000..29999 and the extern range 30000.. while std and extern symbols were drawn
  from their own counters inside those ranges (the collisions).
- after: 38 760 — one dense space for every user, std, extern and prelude symbol (38 490 distinct ids printed by the
  dump; externs and the synthetic traits are not printed).

## Verification (snapshot `build-snap-T164`, final sources)
- `tools/build_axiomc.py --force --stage 3 --out build` into a freshly deleted `build/` (axiom0 rebuilt from the
  snapshot): STAGE1 OK (26 361 344 bytes), STAGE2 (O1) OK, STAGE3 (O1) OK, axiomc2 = axiomc3 = 8 150 528 bytes,
  sha256 `5a92eab2c20cd080…` (fixed point holds).
- `axiom0-unit`: 71 tests, 0 failed. `archcheck`: 229 files, 0 violations. `harness_check.py`: HARNESS OK.
  gcc and clang `-Wall -Wextra` on `resolve.c`: no warnings.
- Test groups `run/trait* run/symbol_id_space typeck/ ui/ resolve/ hir/ modules/ run/async std/core lir/ mir/
  selfhost/typeck_traits` (+ the selfhost groups they match) with the T164 `axiomc2`, `--no-cache -j 2`:
  TOTAL 624, PASS 563, FAIL 60 (ids), SKIP 1; WEAK-NATIVE 12, all pre-existing `run/trait2` tests, none of this task.
  Failing ids: 3 in the baseline (`mir/intrinsics/rotate_u8`, `mir/intrinsics/wrapping_ops`,
  `selfhost/hir/qa_hir_desugar_and_drop`); the other 23 are exactly the id-printing files listed below (7 goldens + 16 selfhost harnesses).
- The run above predates the unblock; see "Unblock: goldens and harness tables" for the final targeted run. The full
  per-task gate (`tools/taskgate.py`) was started and then stopped on the orchestrator's instruction; QA runs it.

## Goldens updated in this task
`tests/resolve/*.resolved` (5 files) regenerated with the T164 `axiomc2`; structure identical (checked after masking
ids). Shift: prelude names and every collection-pass id unchanged (0); body-pass ids (params, locals, generic params,
`Self`) +39 = the 35 std collection-pass symbols that now share the counter (std modules follow the user file in AST
order) + the 4 synthetic traits; `more.ax` has an `extern "C"` item, which now takes a collection id too: +1 for the
items after it, +40 for body ids. axiom0 auto-loads a smaller std set (+23 instead of +35), so with one counter
these goldens can no longer match both compilers; they follow `axiomc2`, the compiler of every gate since T087.

## Unblock: goldens and harness tables (after the paths extension)
Everything changes ids only (no behaviour change):
1. The 7 goldens that print ids as `@n` were regenerated with the T164 `axiomc2` (`inspect --emit=hir|thir --std-root std`).
   Each was checked by masking `@\d+`: the result is identical. Deltas are 0 / +39 / +40, plus one old std-range id
   (10009 -> 48) in `async_basic_pos.thir`.
2. The 16 selfhost templates bake expected dumps into `CORPUS_DATA` / `TC_DATA` + `*_OFF` byte tables, and no
   generator exists for them. They were recomputed mechanically:
   - copy each regenerated bundle;
   - turn every expectation comparison `bytes_equal(..., exp_*.ptr, exp_*.len)` into a dump of (actual, expected) that returns true;
   - build and run the copy natively with the T164 `axiomc2`;
   - replace each expected blob whose content differed with the actual bytes, and rewrite the DATA/OFF tables and
     their `[N]u8` sizes.
   Every changed blob was then checked to be equal to the old one after masking `@Sym(n)` / `@n`. Deltas are +4,
   the synthetic traits; these harnesses load no std. The blobs changed per template: hir 4; resolve 3/4/4/5;
   resolve_hir 3/4/4/1/4/3/4/4/2/1; typeck 2.
3. `taskctl.py snapshot T164` regenerated the bundles (36 generators, 154 files).

Final targeted run in the snapshot (`build/axiomc2.exe`, sha256 `5a92eab2c20cd080…`, `--no-cache -j 2`):
`hir/ typeck/basic typeck/generic/generic_subst typeck/async/async_basic_pos resolve/ selfhost/hir selfhost/resolve
selfhost/resolve_hir selfhost/typeck/ run/symbol_id_space` (covers the 23 regenerated ids, `tests/resolve` and the
regression test): TOTAL 95, PASS 92, FAIL 3, WEAK-NATIVE 0. The only failing id is `selfhost/hir/qa_hir_desugar_and_drop`
(3 modes), which is in `_workspaces/baseline-failures.txt`.

## Spec deviations / questions
- Task text: "`@Sym(n)` in `tests/resolve/*.resolved` [are] the only [goldens printing ids] today". That is not so: HIR/THIR
  dumps print `@n`, and 16 selfhost templates bake expected dumps. They were updated after the paths extension, ids only.
- One counter makes printed ids depend on the std modules a compiler loads; axiom0 and axiomc load different std
  sets, so id-printing goldens can only follow one compiler (chosen: axiomc2).

## Follow-ups
1. Thread the resolver's per-symbol std flag (or the naming table) to the trait solver (`typeck.ax`, `hir.ax`) and
   replace the lexical-site derivation in `find_trait_item` (after T444 lands, it owns `typeck.ax`).
2. Replace the fixed sentinels `10007`/`10008` (Send/Share with an empty name: `solver.ax`, `typeck.ax`,
   `pipeline.ax`) and `10009` (unresolved `Future`: `lower.ax`) by flags; today they are only guarded by the empty
   name / unresolved path.
3. Make the resolver keep the trait's collection id on the HIR trait item (separate `Self` id) so trait paths carry
   the item's symbol and `find_trait_item` never needs the name fallback (ADR-level change, both compilers).
4. Pre-existing, not caused by this task: an axiomc1 built from HEAD sources (with HEAD or fixed axiom0) segfaults in
   typeck on e.g. `tests/run/comptime/scalar_const.ax` (T165's area); axiomc2 is fine.

## Round 1
QA round 0 (`T164-qa.md`) failed for F1, F2 and F3. Each is a valid program that compiles at HEAD and that the
lexical guessing in `find_trait_item` rejected with `AX_TYPE_UNKNOWN_FIELD`:
- F1: a `std.`-path bound;
- F2: a qualified user `m.Future`;
- F3: a std trait re-exported through a user module.

I made the fix QA recommended. The guessing is replaced by the resolver's own record:
- `compiler/hir/hir.ax`: `HirPath` gains `def_dom: u8` (0 unknown, 1 user item, 2 std item) and `def_mod: StrView`,
  which holds the defining module path. HIR nodes are zero-filled, so every other producer leaves them unknown.
- `compiler/hir/lower.ax`: `lower_path_into` calls the new `lower_path_domain`. It fills both fields from the
  resolver's naming table (`resolve_symbol_canonical_name` / `resolve_symbol_module_path`) for the path's symbol, and
  copies the module path into the HIR arena.
  - A trait reference carries the trait's collection id, and the table names that id's defining module exactly.
    This holds through `use`, `pub use` re-exports, qualified paths and prelude exports.
  - The 10009 placeholder for an unresolved `Future` is marked std (`def_dom = 2`), as its id range implied before T164.
- `compiler/traits/solver.ax`: `find_trait_item` now selects the trait as follows:
  1. A trait item carrying the symbol is returned directly.
  2. A non-trait item carrying the symbol gives the domain through its module path.
  3. Otherwise the site path's `def_dom` / `def_mod` select the trait with that name in exactly that module
     (`hir_item_module_is`).
  4. A symbol with no naming entry (the resolver primitives `Copy`, `Send`, `Fn`, ...) keeps the former rule:
     user traits only.
  5. Symbol 0 matches any trait.

  Deleted: `site_use_domain`, `use_tree_binds`, `site_path_is_std` (span text), `hir_item_in_prelude_module`,
  `hir_items_same_module`, `segs_eq_idx`, the prelude/same-module ranking, the site-item scan, and the unused imports
  (`HIR_ITEM_USE`, `HIR_ITEM_MODULE`, `HirUseTree`).
- Not touched: `compiler/types/typeck.ax`, `types.ax`, axiom0 (no id-range test is left there), and the test
  templates (none builds a `HirPath` literal).

### Round 1 verification (snapshot `build-snap-T164`, `taskctl.py snapshot T164` after the edits)
- `tools/build_axiomc.py --force --stage 3 --out build` into a freshly deleted `build/` (axiom0 rebuilt):
  - STAGE1 OK (26 334 720 bytes);
  - STAGE2 (O1) OK;
  - STAGE3 (O1) OK;
  - axiomc2 = axiomc3 = 8 142 848 bytes, sha256 `fa1d7d6dc3d4e41c…`, so the fixed point holds.
- The 5 QA tests `tests/run/symbol_id_space/qa_*.ax` with the new `axiomc2`: 15/15 PASS (interp, native, native-O1),
  WEAK-NATIVE 0.
- Own tests + goldens: `run/symbol_id_space resolve/ hir/ typeck/basic typeck/generic/generic_subst
  typeck/async/async_basic_pos`, which also matches the selfhost hir/resolve/resolve_hir corpora, `--no-cache -j 2`:
  TOTAL 100, PASS 97, FAIL 3, WEAK-NATIVE 0. The 3 failures are `selfhost/hir/qa_hir_desugar_and_drop` in its three
  modes, which is in `_workspaces/baseline-failures.txt`. No golden or template changed in this round: `HirPath`
  dumps do not print the new fields, and ids are unchanged.
- `check` sweep against HEAD `axiomc2` over the 902 non-selfhost test files that use traits/impls/generics:
  907 files now (the 902 from round 0 plus the 5 QA tests). The only difference from HEAD is
  `run/symbol_id_space/many_symbols.ax`, which HEAD rejects and T164 compiles, as intended. The 5 QA tests
  check identically to HEAD.
- The full gate was not run here, as instructed; QA runs it.

## Files changed
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/resolve/resolve.h
- compiler/resolve/resolver.ax
- compiler/resolve/symtab.ax
- compiler/driver/pipeline.ax
- compiler/traits/solver.ax
- tests/run/symbol_id_space/gen_symbol_id_space.py
- tests/run/symbol_id_space/many_symbols.ax
- tests/resolve/R01_basic.resolved
- tests/resolve/enum_variant.resolved
- tests/resolve/more.resolved
- tests/resolve/qa_patterns.resolved
- tests/resolve/simple.resolved
- tests/hir/basic.hir
- tests/hir/control.hir
- tests/hir/exprs.hir
- tests/hir/more.hir
- tests/typeck/basic.thir
- tests/typeck/generic/generic_subst.thir
- tests/typeck/async/async_basic_pos.thir
- tests/selfhost/hir/qa_hir_corpus.ax.in
- tests/selfhost/resolve/qa_resolve_corpus_neg_a.ax.in
- tests/selfhost/resolve/qa_resolve_corpus_neg_b.ax.in
- tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax.in
- tests/selfhost/resolve/qa_resolve_corpus_pos.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_a.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_b.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_d.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_a.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_a.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax.in
- tests/selfhost/resolve_hir/qa_resolve_hir_multifile_modules_b.ax.in
- tests/selfhost/typeck/qa_typeck_a.ax.in
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- tests/run/symbol_id_space/qa_user_traits_std_names.ax
- tests/run/symbol_id_space/qa_local_traits_std_super.ax
- tests/run/symbol_id_space/qa_reexport_std_trait.ax
- tests/run/symbol_id_space/qa_std_path_bound.ax
- tests/run/symbol_id_space/qa_user_future_full_path.ax

STATUS: COMPLETE round=1
