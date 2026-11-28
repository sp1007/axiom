# T428m QA — resolver binds paths inside generic arguments

## Round 0

Snapshot `build-snap-T428m` (HEAD 85d43dfc + the T428m change set, refreshed with the QA tests below:
`taskctl.py snapshot T428m` -> "HEAD 85d43df + 40 changed", bundles regenerated: 36 generators, 60 files, no
BUNDLES FAILED). Logs: `_workspaces/T428m_qa_cmake.log`, `T428m_qa_axiomc.log`, `T428m_qa_axiomc3.log`,
`T428m_qa_taskgate.log`, `T428m_qa_typeck_all.log`; JSON `_workspaces/artifacts/taskgate-T428m.json`.

### Change set / scope
- `taskctl.py changes T428m`: 32 `stage` lines, **no REFUSED**.
- `compiler/resolve/resolver.ax`: new `resolve_generic_args` (each arg `ty` through `resolve_type`; an `Item = T`
  binding resolves only `T`) and `resolve_path_generic_args` (every segment). Called at the top of
  `resolve_path_seg` (type, expression, struct-literal and pattern paths) and per postfix segment in
  `EXPR_POSTFIX` (method-call args). `TYPE_SLICE` element now resolved too (documented in the report).
- T447 rule unchanged: the `hkind == SYM_GENERIC_PARAM` branch still `break`s without binding or diagnostic.
  `Self.X` goes through the unchanged `is_self_head` member branch. My `qa_nested_qualified` checks
  `Option<Option<Bag<F.Output>>>` and `Poll<Self.Output>` raise no diagnostic.
- `compiler/hir/lower.ax` unchanged, as the report says. `bootstrap/axiom0` untouched.
- Scope item 6 audit:
  - (a) `frame.ax`: exactly one added line, `use compiler.interp.value.InterpAlloc`.
  - (b) Goldens:
    - `more.resolved`, `more.hir` and `generic_subst.thir`: 1 line each, a new binding only.
    - `async_basic_pos.thir`: my classifier script compares line by line (272 lines, unchanged count). It finds
      11 lines that only gain a `(TypePath @n)` binding, 51 lines that are only the +1 shift of ids >= 82, and
      0 other changes.
  - (c) `ui_tests.ax`: one added `//~^ ERROR AX_NAME_UNRESOLVED`.
  - (d) The split keeps all four typeck expectations (lines 90 x2, 94, 97 of the old file). The new file has
    one `AX_NAME_UNRESOLVED`, and both files pass.
  - (e) I decoded `CORPUS_DATA`/`CORPUS_OFF` of all 8 templates, old vs new. The code changed only in the
    array sizes. The blobs changed only by:
    - new `@Sym(n)` / `(TypePath @n)` bindings;
    - the `ui_tests.ax` source gaining the one annotation line;
    - its expected diagnostics gaining the 3:20 error, with +1 on later line numbers and "6 errors".

    The templates' groups pass, so the bytes match the bundles' real output.

### Build / fixed point
- `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release`: 0 warnings.
  (gcc + Release fails with `-Werror=stringop-truncation` in `src/link/pe/linker.c:169/768`. This is pre-existing
  in frozen axiom0 and not touched by T428m; see Follow-ups.)
- `build_axiomc.py --out build --root . --opt both --force` ran the full chain axiom0 -> axiomc1 -> axiomc2:
  - STAGE1 OK;
  - STAGE2 O1 sha256 b5d62469..;
  - STAGE2 O0 sha256 43eb6c18..

  These are identical to the engineer's independent build, so the build is deterministic.
- `build_axiomc.py ... --opt both --stage 3`:
  - `FIXED-POINT (O1) OK` b5d6246920c37327.. == axiomc3_O1;
  - `FIXED-POINT (O0) OK` 43eb6c1877496aba.. == axiomc3_O0;
  - `STAGE0-GUARD OK` (6 smoke programs incl. Xin chào thế giới);
  - `BUILD-AXIOMC OK`.

### Taskgate
`python tools/taskgate.py --task T428m --compiler build/axiomc2.exe --build-dir build --exclude-requires
axiom0-internal -j 2 --json-out ../_workspaces/artifacts/taskgate-T428m.json` (change set = snapshot working tree,
incl. the regenerated bundles):

| part | ids | results | PASS | FAIL | SKIP |
|---|---|---|---|---|---|
| own | 10 | 14 | 14 | 0 | 0 |
| affected | 134 | 263 | 259 | 3 | 1 |
| smoke | 34 | 57 | 57 | 0 | 0 |

- `TOTAL 315 PASS 311 FAIL 3 SKIP 1`.
- archcheck clean (252 files, 0 violations), smoke-check OK, unmatched changed files: none.
- WEAK-NATIVE 0 in own/changed tests.
- Smoke seed 3084048114 (always-included `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`).
- Affected set derivation: the map rows `compiler/resolve` -> `tests/ui/resolve`, `compiler/interp` ->
  `tests/run/intrinsics`, `tests/selfhost/interp`, plus every bundle that embeds `compiler.resolve.resolver`, the
  changed goldens and their directories, and the exact-dependency own tests. It includes
  `selfhost/resolve/qa_resolve_all.ax`, `selfhost/resolve_hir/qa_resolve_hir_all.ax`, `selfhost/hir/qa_hir_all.ax`
  and `selfhost/interp/qa_interp_all.ax` (all PASS).
- **Result: `NEW FAILURES: selfhost/typeck/qa_typeck_all.ax` (interp, native, native-O1), TASKGATE exit=1.**

### Native evidence (4a)
- Own run tests `same_name_types` and `qa_shadow_use` use `modes: interp native` with an exact `stdout:`.
- Spot-proof: I changed the last expected line of `qa_shadow_use` `5` -> `6` in the snapshot only and ran
  `axtest --no-cache resolve/generic_args_binding/qa_shadow_use`. Result: FAIL interp, native and native-O1
  ("stdout differs at byte 14"). I restored the file and its hash equals the main tree.
- Against the pre-T428m compiler `axiomc2_O1_642250f08b7af786.exe`, all 5 QA test ids FAIL. Against the snapshot
  compiler, all 5 PASS. So the tests detect the change.

### Adversarial tests added (5)
- `qa_unresolved_positions.ax` (ui) gives exactly one `AX_NAME_UNRESOLVED` per bad name: 12 diagnostics, each at
  the argument's own column. Positions covered:
  - nested `Option<Option<Bag<Missing1>>>`;
  - an unresolved head plus an unresolved argument (`Unknown2<Missing3>`, 2 diagnostics);
  - an associated-type binding in a bound;
  - an impl self type `impl Tr for Bag<Missing5>`;
  - a slice element;
  - a mixed list with one good and one bad argument;
  - an expression path `Bag<Missing8>.new`;
  - a method call `c.conv<Missing9>`;
  - a let annotation;
  - a callee `sz<Option<Missing11>>()`;
  - a struct literal `Bag<Missing12> {..}`.

  A generic parameter used inside its own arguments gives no diagnostic.
- `qa_nested_qualified/` (ui package):
  - private `a.Hidden` two levels deep gives `AX_NAME_PRIVATE`;
  - `a.Missing` three levels deep and an unknown module `nomod.S` give `AX_NAME_UNRESOLVED`, one each;
  - nested `F.Output` and `Poll<Self.Output>` give no diagnostic.
- `qa_shadow_use/` (run package, interp + native + native-O1, exact stdout `7 13 21 100 8 5`) covers:
  - `use a.S` used inside `Option<S>`;
  - a generic parameter `S` shadowing the import (`shadow<i32>` returns `Option<i32>`);
  - three-deep `Option<Bag<Option<b.S>>>`;
  - `Pair<S, b.S>` in a type and in a struct literal;
  - `Bag<b.S>.new`.

### Findings
1. **FAIL — fallout outside the task's locks: `tests/selfhost/typeck/qa_typeck_a.ax.in`** (bundle
   `selfhost/typeck/qa_typeck_all.ax`).
   - Expected: the selfhost typeck group passes, as it does at HEAD.
   - Actual: the native run prints `FAIL qa_typeck_a` and exits 1. `qa_typeck_b` and `qa_typeck_c` print OK.
   - Cause: `TC_DATA` blob 5 (template line ~183) embeds the expected THIR of
     `tests/typeck/generic/generic_subst.ax` with the unbound `(GenericArg "" (TypePath))`. After T428m the
     binding is `(TypePath @n)`. This is the same change as the re-blessed `generic_subst.thir`, but this template
     is a ninth embedded copy that is in neither the report's fallout list nor `unblock-T428m.md`/`locks:`.
   - Cause proven:
     - the HEAD bundle (`git show HEAD:tests/selfhost/typeck/qa_typeck_all.ax`), built with the same snapshot
       compiler, prints `OK qa_typeck_a` and exits 0;
     - the regenerated bundle fails;
     - the id is not in `_workspaces/baseline-failures.txt`.
   - Why the engineer's gate missed it: it ran `taskgate --changed @T428m_changed.txt`. That list leaves out the
     regenerated bundles, so `qa_typeck_all.ax` was not selected.
   - Repro, in `build-snap-T428m`:
     `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 1 selfhost/typeck/qa_typeck_all`
   - Fix: add `tests/selfhost/typeck/qa_typeck_a.ax.in` to `locks:` (scope item 6e) and refresh its `TC_DATA` blob 5
     and the `[N]u8` sizes the same way as the other 8 templates (a binding-only change). I ran a byte-level scan
     of every `[N]u8` blob in `tests/**` for an unbound generic-argument `TypePath`/`PathSegment` in
     resolved/HIR/THIR output. It finds no other stale resolved/THIR expectation outside the locks. The other hits
     are AST/parse dumps, which carry no bindings, and the `ui_tests` blobs, whose undeclared `T` stays unbound.
     All of those pass.

No other finding. Every other acceptance item is met: the own tests, the fixed point at O0/O1, items 6a-6e, and the
groups `qa_resolve_all`, `qa_resolve_hir_all`, `qa_hir_all` and `qa_interp_all`.

### Follow-ups (architect)
- `bootstrap/axiom0` does not build with gcc in Release (`-O3`) because of `-Werror=stringop-truncation` at
  `src/link/pe/linker.c:169` and `:768`. This is pre-existing and not caused by T428m. Gates use clang/Debug, so it
  stays hidden.
- `AX_NAME_SHADOW_MODULE` says "a local binding shadows a module name" for a generic parameter `S` that shadows a
  `use`-imported **struct** `a.S` (`qa_shadow_use/src/main.ax:33`). The message is misleading, and the behaviour is
  identical on HEAD.

### Round 0 verdict

VERDICT: FAIL round=0

## Round 1

Snapshot `build-snap-T428m` refreshed on HEAD `3cd5e448` (`3cd5e448e928`) + the 42 T428m changed files (0 byte differences between `build-snap-T428m` and main checkout across all 40 non-report files; bundles regenerated cleanly). Artifacts: `_workspaces/artifacts/taskgate-T428m-r1.json`, `_workspaces/artifacts/t428m-qa-r1-tier1.json`.

### Round 0 finding disposition
1. **`tests/selfhost/typeck/qa_typeck_a.ax.in` (`selfhost/typeck/qa_typeck_all.ax`) — RESOLVED.**
   - Architect widened `locks:` of `T428m` to include `tests/selfhost/typeck/qa_typeck_a.ax.in`.
   - Independent byte-level decode of `TC_DATA` / `TC_OFF` comparing `HEAD:tests/selfhost/typeck/qa_typeck_a.ax.in` vs working tree:
     - `TC_OFF` keeps 7 offsets (6 blobs), `TC_DATA` length `2325 -> 2328` (+3 bytes), `get_sv` / `run_golden_case` array bounds updated `2325 -> 2328`, zero other code changes.
     - Blobs 0–4 (`tests/typeck/basic.ax` path, source, expected THIR, expected diagnostics, and `tests/typeck/generic/generic_subst.ax` path/source): **byte-for-byte identical** (`21`, `321`, `1457`, `37`, `119` bytes).
     - Blob 5 (`generic_subst.ax` expected THIR): `370 -> 373` bytes; only line 15 changed from `          (TypePath))` to `          (TypePath @2))` — matching `tests/typeck/generic/generic_subst.thir`.
   - Fresh uncached execution (`--no-cache -j 2 --verbose`) in `build-snap-T428m`: `selfhost/typeck/qa_typeck_all.ax` **PASS** in `[interp]`, `[native]`, and `[native-O1]`.

### Spec & scope audit (Round 1 re-check)
- `compiler/resolve/resolver.ax`: unchanged since Round 0 (`resolve_generic_args` + `resolve_path_generic_args` called on every segment in `resolve_path_seg` and on every postfix segment in `EXPR_POSTFIX`, plus `TYPE_SLICE` element walk in `resolve_type`). Complies with `SPEC-02` `AXS-GRM-080`, preserves the T447 `P.Assoc` unbound projection rule, `Self` / `Self.X`, and lowering sentinels (`i128`, `u128`, `never`, `Future`).
- `compiler/interp/frame.ax`: single added line `use compiler.interp.value.InterpAlloc` (scope 6a).
- `compiler/hir/lower.ax` and `bootstrap/axiom0/`: untouched.
- Scope items 6b–6e re-verified:
  - `tests/resolve/more.resolved`, `tests/hir/more.hir`, `tests/typeck/generic/generic_subst.thir`: 1 line each, new binding only (`@Sym(76)`, `@76`, `@2`).
  - `tests/typeck/async/async_basic_pos.thir`: 271 lines (unchanged count), 11 lines gain `(TypePath @n)`, 51 lines shift local IDs `>= 82` by `+1`, `0` other changes.
  - `tests/ui/resolve/ui_tests.ax`: single added `//~^ ERROR AX_NAME_UNRESOLVED` on line 4.
  - `tests/ui/impl_generic_in_method_bound/qa_adversarial_bounds_reject.ax` + `qa_adversarial_bounds_unresolved_fnonce.ax`: split preserves all 4 typeck expectations in the original and checks `AX_NAME_UNRESOLVED` at `FnOnce<MissingBoundTy>` in the split file; both PASS.
  - All 9 `.ax.in` selfhost templates in `locks:` contain binding/expected-diagnostic updates only, and all 34 `bundles_current.test` manifests PASS.

### Build & fixed-point verification (`build-snap-T428m/`)
- Command: `python tools/build_axiomc.py --out build --root . --opt both --stage 3`
- Content-hash freshness check across all 280 compiler/std source files (`sources a93c3cfc964fa610`) and `bootstrap/axiom0` (`inputs 2754e62dc264ce73`) matched every binary manifest (`HEAD` moved `85d43dfc -> 3cd5e448` via test/baseline-only commits `T546` and `T547`, with zero compiler/std/bootstrap changes):
  - `STAGE1 OK`: `build/axiomc1.exe` (`34,909,696` bytes, `sha256=599ea7ff4d6b4860...`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1.exe) == sha256(axiomc3_O1.exe) == sha256(axiomc2.exe) == b5d6246920c373277739751bc94ed886c3f0ff3a6167aaa7ecb5387089286e00` (`9,347,584` bytes)
  - `FIXED-POINT (O0) OK`: `sha256(axiomc2_O0.exe) == sha256(axiomc3_O0.exe) == 43eb6c1877496abaa504f318c1ff796c6cf99ffa9c001f7ce83adcd0be26d419` (`20,499,968` bytes)
  - `BUILD-AXIOMC OK` (exit 0).

### Targeted tests (`--no-cache -j 2 --verbose`)
Command (inside `build-snap-T428m/`):
`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --filter resolve/generic_args_binding --filter ui/impl_generic_in_method_bound --filter ui/resolve/ui_tests --filter resolve/more --filter hir/more --filter typeck/generic/generic_subst --filter typeck/async/async_basic_pos --no-cache -j 2 --verbose`
- Result: `TOTAL 23 PASS 23 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Covers all 10 `resolve/generic_args_binding` test IDs (14 legs incl. `same_name_types` and `qa_shadow_use` across `interp`, `native`, `native-O1`), all 5 `ui/impl_generic_in_method_bound` IDs, `ui/resolve/ui_tests.ax`, and all 4 re-blessed goldens.

### Required selfhost groups & bundle checks (`--no-cache -j 2 --verbose`)
Command (inside `build-snap-T428m/`):
`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --filter selfhost/resolve/qa_resolve_all --filter selfhost/resolve_hir/qa_resolve_hir_all --filter selfhost/hir/qa_hir_all --filter selfhost/typeck/qa_typeck_all --filter bundles_current --no-cache -j 2 --verbose`
- Result: `TOTAL 46 PASS 46 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- `selfhost/resolve/qa_resolve_all.ax`, `selfhost/resolve_hir/qa_resolve_hir_all.ax`, `selfhost/hir/qa_hir_all.ax`, and `selfhost/typeck/qa_typeck_all.ax` all PASS in `[interp]`, `[native]`, and `[native-O1]`, plus all 34 `selfhost/*/bundles_current.test` manifests PASS.

### Native-evidence live mutation spot-proof (4a)
- Mutated `build-snap-T428m/tests/resolve/generic_args_binding/same_name_types/src/main.ax` only (`// stdout:` last line `9\n` -> `8\n`) and ran:
  `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 1 --filter resolve/generic_args_binding/same_name_types --verbose`
  - Result: exit `1`, `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` — `[interp]`, `[native]`, and `[native-O1]` all FAIL (`stdout differs at byte 20`).
- Restored byte-identically (`sha256=886fb0c0c0e59ca737c1be7a548a1c587e04d616ec080cf3bde8568eb1e76481`, matching main tree) and re-ran `--no-cache`:
  - Result: exit `0`, `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

### Taskgate (`tools/taskgate.py`)
Command (inside `build-snap-T428m/`):
`python tools/taskgate.py --task T428m --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out ../_workspaces/artifacts/taskgate-T428m-r1.json`

- root `D:/projects/compiler/new lang/build-snap-T428m`, HEAD `3cd5e448e928`, compiler `D:/projects/compiler/new lang/build-snap-T428m/build/axiomc2.exe`, `-j 2`
- change set: 64 file(s) (42 task files + 22 regenerated selfhost bundles vs HEAD)
- wall time: 1429.2 s (axtest 1399.4 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 10 | 14 | 14 | 0 | 0 | 0 | 7 |
| affected | 134 | 263 | 262 | 0 | 1 | 0 | 83 |
| smoke | 34 | 53 | 53 | 0 | 0 | 0 | 24 |
| **total (dedup)** | 165 | 313 | 312 | 0 | 1 | 0 | 105 |

- Affected-set derivation: `compiler/resolve` -> `tests/modules`, `tests/ui/resolve`, plus all regenerated bundles embedding `compiler.resolve.resolver`; `compiler/interp` -> `tests/run/basic`, `tests/run/intrinsics`, `tests/selfhost/interp`; directory/exact dependencies for the 4 re-blessed goldens, UI tests, and 9 `.ax.in` templates (`selfhost/typeck/qa_typeck_all.ax`, `selfhost/interp/qa_interp_all.ax`, `selfhost/resolve/qa_resolve_all.ax`, `selfhost/resolve_hir/qa_resolve_hir_all.ax`, `selfhost/hir/qa_hir_all.ax`, etc.); `unmatched changed files: none`.
- Smoke: `seed=1611332512`, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax` + 1 draw per top-level group (`smoke-check`: OK, est. worst-case draw 33 s).
- Cache: `CACHED 105, miss 5, uncacheable 86, stored 0, dep_source exact, verification sample seed=1871921089 n=20 of 74 hits, mismatch none, rejected {}, producer snapshot`.
- `WEAK-NATIVE`: `0` in the task's own/changed tests (`13` pre-existing in unrelated affected tests).
- Baseline: `BASELINE OK`, `Failing ids: none`.
- `archcheck`: clean (`252 files scanned, 0 violations`).
- Result: `TOTAL 313 PASS 312 FAIL 0 SKIP 1 XFAIL 0` (`TASKGATE T428m exit=0`).

### Tier-1 non-selfhost sweep & architecture check
Commands (inside `build-snap-T428m/`):
1. `python ../.claude/skills/axiom-tasks/scripts/fullrun.py non-selfhost-ids _workspaces/artifacts/t428m-qa-r1-non-selfhost-ids.txt --root .` (`3,146` IDs = all non-selfhost tests + `selfhost/bundles_current.test`)
2. `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --id-file _workspaces/artifacts/t428m-qa-r1-non-selfhost-ids.txt --exclude-requires axiom0-internal --gate -j 2 --baseline ../_workspaces/baseline-failures.txt --json > _workspaces/artifacts/t428m-qa-r1-tier1.json` (also copied to main `_workspaces/artifacts/t428m-qa-r1-tier1.json`)
3. `python tools/archcheck.py -v`

Results:
- `TOTAL 6747 PASS 6703 FAIL 0 SKIP 37 XFAIL 7` (exit `0`).
- Cache: `CACHED 133 HITS 89 MISS 2201 UNCACHEABLE 856 STORED 2121 dep_source=exact`, `VERIFY-SAMPLE seed=2042896930 n=20 of 89 hits`, `0` `CACHE-MISMATCH`.
- Baseline comparison: `BASELINE OK` (`failing_ids = []` ⊆ `_workspaces/baseline-failures.txt`, `new_failures = []`).
- `BASELINE NOW PASSING`: `conformance/p11/e11_5_executors/fiber_in_async_and_threads.ax` and `conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax` (both `T428g` baseline failures on HEAD `3cd5e448` now pass in all 3 modes; kept in `_workspaces/baseline-failures.txt` for `T428g` per task spec).
- T134 native canaries verified in Tier-1 JSON: `run/intrinsics/assert_false.ax` (`PASS` ×3), `run/intrinsics/panic_abort.ax` (`PASS` ×3), `ui/intrinsics/unknown_intrinsic.ax` (`PASS`).
- `archcheck.py`: `252 files scanned, 0 violations` (exit `0`).

### Hygiene checks (main repository root)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428m`: 42 `stage` entries, `0` `REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (only the standing optional `guard.py` `WARN`).

### Findings (Round 1)
None. All Round 0 findings and all T428m acceptance criteria are satisfied.

## Files changed
- tests/resolve/generic_args_binding/qa_unresolved_positions.ax
- tests/resolve/generic_args_binding/qa_shadow_use/axiom.toml
- tests/resolve/generic_args_binding/qa_shadow_use/src/a.ax
- tests/resolve/generic_args_binding/qa_shadow_use/src/b.ax
- tests/resolve/generic_args_binding/qa_shadow_use/src/main.ax
- tests/resolve/generic_args_binding/qa_nested_qualified/axiom.toml
- tests/resolve/generic_args_binding/qa_nested_qualified/src/a.ax
- tests/resolve/generic_args_binding/qa_nested_qualified/src/main.ax

## Verdict

VERDICT: PASS round=1
