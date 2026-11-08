# T857 Report: E20.2 AXPACKAGE dependency resolution, monotonic feature unification, axiom.lock & offline vendoring conformance suite

## Summary
Task T857 delivers the comprehensive end-to-end conformance test suite certifying Phase 20 (`E20.2`) exit criteria for `SPEC-111` (`AXS-PKG-001`..`AXS-PKG-053`, `REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-PKG-003`).

The suite provides:
1. Master conformance oracle `e20_2_package_manager_lockfile_oracle.test` + `e20_2_package_manager_lockfile_oracle.py` + `e20_2_package_manager_lockfile_probe.ax.in`:
   - Bundles live compiler modules (`compiler.pkg.semver`, `compiler.pkg.resolver`, `compiler.driver.pkg_cmd`, plus compiler kernel and build workspace dependencies) with standard library modules (`std.pkg.lockfile`, `std.pkg.store`) and executes across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with 100% byte-for-byte identical output parity.
   - Executes differential verification (`--interp` vs native `-O1 --verify-each`) across all 5 standalone `.ax` conformance fixtures with exact byte output matching (`0 WEAK-NATIVE`).
   - Audits compiled binaries for zero leaked debug/metadata tokens (`AXMETA01`, `AXMI0001`, `AXLTO001`, `AXMIR001`, `AXDB0001`, `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, `__ax_interp_eval`).
2. Standalone `.ax` and `.stdout` conformance fixtures:
   - `semver2_diamond_and_conflict_derivation.ax`: SemVer 2.0 total precedence ordering, numeric/alphanumeric tokens, build metadata invariance, pre-release isolation rules, compatible track diamond resolution, and human-readable PubGrub conflict derivation trees with step-by-step causal chains (`AXS-PKG-004..005`, `AXS-PKG-011..012`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-ECO-8736`).
   - `order_invariance_and_reproducible_lockfile.ax`: Manifest declaration-order and candidate ordering invariance, canonical `axiom.lock` v1 schema, lexicographical sorting by `(namespace, name, version, source, env)`, deduplicated and sorted feature/dependency arrays, and deterministic SHA-256 `graph_hash` reproduction (`AXS-PKG-010`, `AXS-PKG-030`, `REQ-PKG-020`, `REQ-PKG-022`).
   - `monotonic_feature_unification_and_rejection.ax`: Monotonic additive feature unification (least fixed point union $F(P, \text{env}) = \bigcup \text{RequestedFeatures}(e)$ + implications), strict Host (build-deps) vs Target (normal-deps) environment isolation, dev-dependencies scope isolation from production builds, and strict rejection (`AX_DRIVER_BAD_MANIFEST`) of undeclared or mutually conflicting features (`AXS-PKG-023..024`, `REQ-PKG-025`).
   - `side_by_side_major_isolation_and_type_identity.ax`: Incompatible major version coexistence (`math@1.4.2` and `math@2.0.1`), disjoint symbol mangling prefixes, nominal `TypeId` isolation (`TypeId(math@1, Vec2) != TypeId(math@2, Vec2)`), `AX_TYPE_MISMATCH` with `distinct_package_versions`, explicit `public = true` `pub use` re-export bridging, and singleton native `links` exclusion (`AXS-PKG-020..022`, `REQ-PKG-011`, `REQ-PKG-024`).
   - `air_gapped_offline_vendor_and_drift_audit.ax`: `--locked` / `--frozen` drift detection, `graph_hash` tamper detection rejecting corrupted entries, SHA-256 content-addressed package store path formatting and pre-use verification, sandboxed extraction path-traversal rejection and quota limits, and air-gapped `--offline` execution with `vendor/` coverage verification (`AXS-PKG-031..033`, `REQ-PKG-013`, `REQ-PKG-022`, `REQ-PKG-024`).
3. Complete documentation in `README.md` mapping normative contracts, rules, requirements, and test fixtures.

## Verification Results
- `axtest.py` conformance suite execution:
  - Command: `python build-snap-T857/tools/axtest.py --root build-snap-T857 --compiler build/axiomc2.exe --std-root build-snap-T857/std -j 1 --exclude-requires axiom0-internal conformance/p20/e20_2_package_manager_lockfile`
  - Result: `WEAK-NATIVE 0`, `TOTAL 16 PASS 16 FAIL 0 SKIP 0 XFAIL 0`.
- Master Conformance Oracle probe:
  - Byte-identical output parity verified across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each`.
  - Clean binary audits: 0 leaked metadata tokens.
- Architecture check (`tools/archcheck.py`):
  - `archcheck: 207 files scanned, 0 violations`.
- Requirement coverage check (`reqcov.py --strict`):
  - `COVERAGE OK`.
- Harness check (`harness_check.py`):
  - `HARNESS OK`.
- Canonical syntax compliance (`axiom-syntax`):
  - Strictly `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Files changed
- tests/conformance/p20/e20_2_package_manager_lockfile/README.md
- tests/conformance/p20/e20_2_package_manager_lockfile/air_gapped_offline_vendor_and_drift_audit.ax
- tests/conformance/p20/e20_2_package_manager_lockfile/air_gapped_offline_vendor_and_drift_audit.stdout
- tests/conformance/p20/e20_2_package_manager_lockfile/e20_2_package_manager_lockfile_oracle.py
- tests/conformance/p20/e20_2_package_manager_lockfile/e20_2_package_manager_lockfile_oracle.test
- tests/conformance/p20/e20_2_package_manager_lockfile/e20_2_package_manager_lockfile_probe.ax.in
- tests/conformance/p20/e20_2_package_manager_lockfile/monotonic_feature_unification_and_rejection.ax
- tests/conformance/p20/e20_2_package_manager_lockfile/monotonic_feature_unification_and_rejection.stdout
- tests/conformance/p20/e20_2_package_manager_lockfile/order_invariance_and_reproducible_lockfile.ax
- tests/conformance/p20/e20_2_package_manager_lockfile/order_invariance_and_reproducible_lockfile.stdout
- tests/conformance/p20/e20_2_package_manager_lockfile/semver2_diamond_and_conflict_derivation.ax
- tests/conformance/p20/e20_2_package_manager_lockfile/semver2_diamond_and_conflict_derivation.stdout
- tests/conformance/p20/e20_2_package_manager_lockfile/side_by_side_major_isolation_and_type_identity.ax
- tests/conformance/p20/e20_2_package_manager_lockfile/side_by_side_major_isolation_and_type_identity.stdout

STATUS: COMPLETE round=0
