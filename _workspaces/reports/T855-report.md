# T855 Report: E20.2 Deterministic SemVer 2.0 constraint solver, monotonic feature unifier & side-by-side package version isolation

STATUS: COMPLETE

## Summary

Implemented the SemVer 2.0 version parser/comparator, PubGrub-style deterministic dependency constraint solver, monotonic feature unifier, and side-by-side package version isolation per `spec/SPEC-111-package-manager-resolution-lockfiles.md` (`REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-PKG-001`).

Key deliverables and architectural implementations:
1. **`compiler/pkg/semver/mod.ax`**:
   - SemVer 2.0 parser (`semver2_parse`, `semver2_parse_checked`) supporting strict `major.minor.patch[-prerelease][+build_meta]`.
   - SemVer 2.0 comparator (`semver2_cmp_precedence`, `semver2_cmp_total_tiebreak`) implementing RFC-4648 / SemVer 2.0 §11 total precedence chaining (including numeric vs alphanumeric identifier ordering and build metadata tie-breaking).
   - SemVer 2.0 constraint solver (`semver_constraint_parse`, `semver_constraint_matches`) supporting exact (`=`), caret (`^`), tilde (`~`), wildcard (`*`), inequality ranges (`<`, `<=`, `>`, `>=`), compound intersection ranges, and prerelease isolation.
   - Preserves 256-byte ABI boundary constraints for by-value parameter passing.

2. **`compiler/pkg/resolver/mod.ax`**:
   - PubGrub-style conflict-driven clause learning (CDCL) dependency solver with declaration-order-independent candidate evaluation.
   - Lockfile-preferring resolution against `axiom.lock` pins and `--minimal-versions` tie-breaking.
   - Human-readable conflict derivation trees formatted per `AXS-PKG-052` emitting `AX_DRIVER_BAD_MANIFEST` (`kind = "version_conflict"`).
   - Monotonic feature unification separating Host (`build`/`comptime`) vs Target (`normal`/`dev`) environments (`REQ-PKG-025`), forbidding negative feature mutation or silent feature drops (`REQ-PKG-024`).
   - Side-by-side package version isolation: disjoint `_AXP_<name>_v<M>_<m>_<p>_<hash>` item symbol mangling and distinct `CompilerDB` `package_id` assignments (`AXS-PKG-020`, `REQ-ECO-8736`).
   - Nominal `TypeId` version isolation and `pub use` re-export bridging across explicit `public = true` dependency edges (`AXS-PKG-021`, `AXS-PKG-022`, `REQ-PKG-022`).
   - Singleton native `links` key enforcement (`AXS-PKG-020 §3`).
   - Negative edge enforcement for unpinned VCS commits (`AXS-PKG-003 §2`), directory escaping path traversals (`AXS-PKG-002 §1`), and inter-package dependency cycles (`AXS-PKG-013 §1`).

3. **`tests/run/pkg_resolver/`**:
   - `pkg_resolver.test`: multi-tier harness test executing `pkg_resolver_oracle.py`.
   - `pkg_resolver_oracle.py`: assembles compiler modules with `pkg_resolver_probe.ax.in` and runs all verification checks across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` tiers ensuring byte-identical parity.
   - `semver2_ordering_and_constraints.ax`: standalone fixture testing SemVer 2.0 precedence and constraints.
   - `pubgrub_order_invariance_and_conflicts.ax`: standalone fixture testing declaration order invariance, lockfile preference, and conflict trees.
   - `side_by_side_isolation_and_features.ax`: standalone fixture testing side-by-side version isolation, nominal types, `pub use` bridging, and host/target feature separation.

## Verification

- `python tools/axtest.py --compiler build/axiomc2.exe --std-root build-snap-T855/std -j 1 --exclude-requires axiom0-internal run/pkg_resolver`:
  - `WEAK-NATIVE 0`
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`
- `python tests/run/pkg_resolver/pkg_resolver_oracle.py build/axiomc2.exe`:
  - `PKG-RESOLVER-ENGINE-OK` (passes `--interp`, `-O0`, `-O1`, `-O2 --verify-each`)
- `python tools/archcheck.py`:
  - `archcheck: 202 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`:
  - `gaps: 0 COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`:
  - `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T855`:
  - Verified no unlisted changes.

## Files changed

- compiler/pkg/semver/mod.ax
- compiler/pkg/resolver/mod.ax
- tests/run/pkg_resolver/pkg_resolver.test
- tests/run/pkg_resolver/pkg_resolver_oracle.py
- tests/run/pkg_resolver/pkg_resolver_probe.ax.in
- tests/run/pkg_resolver/pubgrub_order_invariance_and_conflicts.ax
- tests/run/pkg_resolver/pubgrub_order_invariance_and_conflicts.stdout
- tests/run/pkg_resolver/semver2_ordering_and_constraints.ax
- tests/run/pkg_resolver/semver2_ordering_and_constraints.stdout
- tests/run/pkg_resolver/side_by_side_isolation_and_features.ax
- tests/run/pkg_resolver/side_by_side_isolation_and_features.stdout

STATUS: COMPLETE round=0
