---
id: T428m
title: Fix — the resolver never binds the paths inside generic arguments (`Result<String, IoError>`, `Option<a.S>`)
phase: P11-concurrency-async
owner: axiom-frontend
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T428a]
priority: 11
status: doing
attempts: 1
timeout_min: 240
paths: [tests/resolve/generic_args_binding, tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_unresolved_fnonce.ax]
locks: [compiler/resolve/resolver.ax, compiler/hir/lower.ax, compiler/interp/frame.ax, tests/resolve/more.resolved, tests/hir/more.hir, tests/typeck/generic/generic_subst.thir, tests/typeck/async/async_basic_pos.thir, tests/ui/resolve/ui_tests.ax, tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax, tests/selfhost/resolve/qa_resolve_corpus_pos.ax.in, tests/selfhost/resolve/qa_resolve_corpus_neg_c.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_b.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_pos_c.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_neg_c.ax.in, tests/selfhost/resolve_hir/qa_resolve_hir_corpus_wide_b.ax.in, tests/selfhost/hir/qa_hir_corpus.ax.in, tests/selfhost/hir/qa_hir_desugar_and_drop.ax.in, tests/selfhost/typeck/qa_typeck_a.ax.in]
spec: [spec/SPEC-02-grammar.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-MOD-003, REQ-MOD-064]
started: 2026-11-26 23:26:36
unblocks: 1
agent: T428m-impl
---
# T428m — Every path inside a generic argument list is resolved in the enclosing scope

## Why
`_workspaces/reports/T428g-report.md` (trace evidence) and `_workspaces/reports/unblock-T428g.md`:
`compiler/resolve/resolver.ax` `resolve_type` / `resolve_path_seg` never visit a segment's `generic_args`. Paths inside
generic arguments therefore reach HIR with `symbol = 0`, `def_dom = 0`, and typeck falls back to the whole-program
bare-name walk `lookup_path_type_by_name`, which picks a same-named struct of another module (the two e11_5 baseline
failures, T428g). A qualified argument (`Option<a.S>`) is not resolved at all (`AX_NAME_UNRESOLVED` on HEAD).
SPEC-02 AXS-GRM-080 already says "a generic argument is a type": it is resolved exactly like any other type in the same
scope. This is an implementation bug (TYPE A), not a language change. HIR lowering already copies the binding:
`lower_generic_args` -> `lower_type` -> `lower_path_into` -> `get_symbol` + `lower_path_domain` read the resolve map by
AST node, so once the resolver binds the segment the `HirPath` carries `symbol/def_dom/def_mod/def_name`.

## Scope
1. In `compiler/resolve/resolver.ax`, resolve the `generic_args` of **every** segment of a path (not only the last),
   in the scope of the path itself, at every place a generic argument list can appear: type paths (`resolve_type`),
   expression paths (`Vec<S>.new()`, `size_of<S>()`, `Result<a.S, E>.Ok(..)`, the two `resolve_expr` call sites),
   pattern paths, method-call generic arguments (`x.f<S>()`) if the AST has them, impl self types / trait paths /
   bounds / where-clauses (they already go through `resolve_type`), and `dyn` bounds. Factor this as one helper
   (e.g. `resolve_generic_args(scope, g)`) called from `resolve_path_seg`'s callers or from `resolve_path_seg` itself.
   - A type argument goes through `resolve_type`. An associated-type binding `Item = T` resolves `T` only; the name
     `Item` stays unbound (typeck matches it against the trait).
   - Keep the T447 rule (`P.Assoc` on a generic parameter stays unbound, no diagnostic) and the `Self.X` handling.
   - The lowering sentinels (`i128`, `u128`, `never`, unresolved `Future` in `lower_path_into`) must keep working
     inside generic arguments: they suppress the resolver's `AX_NAME_UNRESOLVED` at the same span (check with a test).
2. `compiler/hir/lower.ax`: change only if a generic-argument path does not get its binding (e.g. the expression-path
   segments at ~lines 818–842); otherwise leave it untouched and say so in the report.
3. axiom0 (`bootstrap/axiom0`) is **not** changed (frozen after T087; see the unblock report): it only compiles the
   compiler bundle at stage 1 and the stage-2/3 fixed point proves the result.
4. Fallout. A correct binding can expose source that relied on the wrong one (a type not imported but found by the
   global walk; one module's `SymbolId`/`TypeId`/`Vec`/`String`/`Ordering` used where another's was meant; std has
   duplicate `String`, `Vec`, `Ordering`, `Layout`, `SendError`, ...; `compiler/` has duplicate `SymbolId`, `TypeId`,
   `ConstEvalResult`, `SemanticKey`, `Fingerprint128`, `DependencyEdge`). Build stage 2 and run the sweep below first;
   list every new diagnostic in the report (file:line, cause). Fallout in a file outside this task's `paths`/`locks`
   is **not** patched here and not hidden with a heuristic: report `STATUS: BLOCKED` with the exact list so the
   architect creates the fix tasks (or extends the locks). Never downgrade the new `AX_NAME_UNRESOLVED`.
5. Tests in `tests/resolve/generic_args_binding/` (`.resolved` / `inspect` golden plus run tests, `modes: interp
   native`, exact `// stdout:`):
   - `struct Foo {..} fn f() -> Option<Foo>`: `--emit=resolved` shows `Foo` with `@Sym(..)`, `--emit=hir` shows the
     generic-arg `TypePath` with its symbol (today: `(TypePath (PathSegment "Foo"))` / `(TypePath)`);
   - a package with modules `a` and `b` each defining `struct S` with different fields, `fn pick(o: Option<a.S>)` and
     `Result<b.S, a.S>` used from `main` compile and run;
   - an expression path with generic arguments on a non-last segment (`Vec<a.S>.new()` or equivalent);
   - nested arguments (`Option<Vec<b.S>>`), an associated-type binding in a bound (`F: Future<Output = a.S>`), a
     projection `T.Item` inside an argument, and `Option<i128>` / `Option<never>`-style sentinels;
   - compile-fail: an unimported or misspelled name inside a generic argument gives `AX_NAME_UNRESOLVED` at that
     argument's span (`// error:` directive), and a private item gives `AX_NAME_PRIVATE`.
6. **Fallout round (architect decision 2026-11-26, `_workspaces/reports/unblock-T428m.md`).** The resolver change and
   its fallout land in one commit (the stage-2 build is broken without item a). The locks were widened to exactly:
   a. `compiler/interp/frame.ax`: add `use compiler.interp.value.InterpAlloc` (used by `size_of<InterpAlloc>()` at
      lines 357/366, found until now only by typeck's bare-name walk). No other change in that file.
   b. Re-bless the 4 goldens `tests/resolve/more.resolved`, `tests/hir/more.hir`,
      `tests/typeck/generic/generic_subst.thir`, `tests/typeck/async/async_basic_pos.thir`. The only allowed diff is
      the new bindings (`@Sym(n)` / `(TypePath @n)`) and, in `async_basic_pos.thir`, the +1 shift of later local ids
      caused by binding `Poll<Self.Output>`; the report shows the diff summary per file.
   c. `tests/ui/resolve/ui_tests.ax:3`: add the second `//~ ERROR AX_NAME_UNRESOLVED` (for the undeclared `T`).
   d. Split `tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax`: move `impl<R> Bad<R>` (lines
      81–86) and its two uses at the end of `main` into the new
      `qa_adversarial_bounds_unresolved_fnonce.ax` (expects `AX_NAME_UNRESOLVED` at `FnOnce<MissingBoundTy>`); the
      original keeps every typeck expectation (lines 90 ×2, 94, 97) and must still produce them.
   e. Refresh the embedded expected data (`CORPUS_DATA` and the synthetic cases) of the 8 selfhost templates in
      `locks:` so they match (b)–(d). Edit only the `.ax.in` templates; the generated bundles are the harness's
      (never list them).
   Anything else that breaks is still reported as fallout, not patched.

## Acceptance
- [ ] The tests above pass (interp, native, native-O1; WEAK-NATIVE 0); the `.resolved` / HIR goldens show the binding.
- [ ] The stage-2 build succeeds and the stage-2 == stage-3 fixed point holds at `-O0` and `-O1`.
- [ ] Gate: the task's tests + the selfhost groups of `compiler/resolve` and `compiler/hir` + a **Tier-1 non-selfhost
      sweep** (this change touches every program, so the grep-based affected set is the whole suite); the set of
      failing ids is a subset of `_workspaces/baseline-failures.txt`. The two `T428g` baseline ids may start passing;
      they stay listed (T428g removes them). The selfhost groups `selfhost/resolve/qa_resolve_all`,
      `selfhost/resolve_hir/qa_resolve_hir_all` and `selfhost/hir/qa_hir_all` pass.
- [ ] The fallout items 6a–6e are done; `ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax` still
      passes with all four typeck expectations, and the new split test passes.
- [ ] Report `_workspaces/reports/T428m-report.md`: the helper and its call sites, whether `lower.ax` changed, the fallout
      list (empty or each item with its owner), and an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428g.md`)
- 2026-11-26 11:20:52 started (attempt 1) T428m-impl
- 2026-11-26 16:41:56 block: fallout outside locks: compiler/interp/frame.ax needs InterpAlloc import; 4 goldens, 2 ui, 8 selfhost .ax.in need intended refresh
- 2026-11-26 architect: locks widened to the 15 fallout files + split test in paths (unblock-T428m.md); pre-existing
  `link/dll/gnu_ld_run.test` -> baseline (T423j), `ui/security_profiles/forbid_unsafe_constructs_neg.ax` -> baseline (T540)
- 2026-11-26 20:34:57 unblocked (cycle 1) 
- 2026-11-26 23:26:36 started (attempt 1) T428m-impl
