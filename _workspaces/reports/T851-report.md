# T851 Report: E20.1 Declarative `axiom.toml` Package/Workspace Manifest Parser, Feature/`@cfg` Evaluator & Acyclic Package Graph

STATUS: COMPLETE

## Summary

Implemented Milestone **E20.1** (`T851`) in the self-hosted Axiom compiler (`compiler/build/manifest/mod.ax` and `compiler/build/workspace/mod.ax`) per `SPEC-110 §§1..3 & §5`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, and `INV-BLD-001`:

1. **Declarative `axiom.toml` Manifest Parser & Schema Validator (`compiler/build/manifest/mod.ax`)**:
   - Parses and validates `[package]`, `[workspace]`, `[lib]`, `[[bin]]`, `[[build_tool]]`, `[features]`, `[profile.*]`, and the 5 canonical dependency scopes (`[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, `[comptime-dependencies]`, `[system-dependencies]`) plus target-conditional `[target.'cfg(...)'.dependencies]` tables (`AXS-BLD-004`..`005`, `AXS-BLD-010`..`012`, `AXS-BLD-016`).
   - Enforces strict SemVer 2.0.0 parsing, version requirement validation, and deterministic version ordering (`SemVer`, `semver_parse`, `semver_req_valid`, `semver_cmp`, `REQ-PKG-022`).
   - Enforces package identifier grammar (`^[a-z][a-z0-9_-]{0,63}$`) and reserved keyword/namespace rejection (`AXS-BLD-011`).
   - Rejects imperative build-script directives (`script`, `command`, `shell`, `eval`, `pre_build`, `post_build`, `build_script_cmd`) with `AX_DRIVER_BAD_MANIFEST` (`kind = "forbidden_script"`, `AXS-BLD-012`, `AXS-BLD-052 §1`).
   - Rejects invalid `[profile.*]` settings with `AX_DRIVER_INVALID_PROFILE`, `AX_DRIVER_INVALID_SAFETY_PROFILE`, and `AX_DRIVER_INVALID_PANIC_STRATEGY` (`AXS-BLD-050`).
   - Implements deterministic `@cfg(...)` boolean combinator (`all(...)`, `any(...)`, `not(...)`) and key-value predicate evaluation (`target_os`, `target_arch`, `target_env`, `target_vendor`, `target_abi`, `target_pointer_width`, `target_endian`, `feature`, `profile`, `test`, `bench`, `sanitize`) with `AX_NAME_INVALID_CFG_PREDICATE` diagnostics on unknown or malformed predicates (`AXS-BLD-014 §4`, `SPEC-88`).

2. **Workspace Discovery, Monotonic Feature Unification & Acyclic `DependencyGraph` (`compiler/build/workspace/mod.ax`)**:
   - Validates `[workspace].members`, `exclude`, `default_members`, and `resolver = "1"`, enforcing strict workspace-root path containment (rejecting `..` path escapes, drive letters, and duplicate member package names with `AX_DRIVER_BAD_MANIFEST`, `kind = "workspace_member"`, `AXS-BLD-013`).
   - Computes path-independent `PackageIdentity` (`name`, `version`, `source_kind`, workspace-relative `logical_source_id`, `feature_set_hash`, `target_env_class`, `target_triple`, `abi_salt`, and 256-bit domain-separated `identity_digest`) and deterministic symbol mangling prefix `_AXP_<pkg>_v<maj>_<min>_<patch>_<hash16>` (`AXS-BLD-002`, `REQ-PKG-005`).
   - Computes least-fixed-point monotonic feature unification separated by `(PackageIdentity.name, PackageIdentity.version, BuildEnvClass)` (`Target` vs `Host`) so host `[build-dependencies]` / `[comptime-dependencies]` never bleed features into target artifacts (`AXS-BLD-014`, `AXS-BLD-021`).
   - Rejects undeclared features (`kind = "unknown_feature"`), missing optional dependencies (`kind = "missing_required_feature"`), and cyclic or mutually exclusive features (`kind = "feature_conflict"`).
   - Verifies package-level `DependencyGraph` acyclicity via 3-color DFS (`verify_package_dag_acyclicity`), emitting `AX_DRIVER_BAD_MANIFEST` (`kind = "package_cycle"`, `cycle = "a -> b -> a"`) on inter-package cycles while permitting intra-package declaration SCCs and rejecting intra-package module import cycles with `AX_NAME_IMPORT_CYCLE` (`AXS-BLD-003`, `AXS-BLD-052 §2`).
   - Computes canonical lexicographical topological build ordering (`compute_canonical_topo_order`, `AXS-BLD-006`) and `REQ-PKG-025` semantic non-interference / `dev-dependencies` firewall audits (`verify_req_pkg_025_semantic_invariance`, `AXS-BLD-005 §2`, `AXS-BLD-015`, `INV-BLD-001`).

3. **End-to-End Verification (`tests/run/build_manifest/`)**:
   - Added standalone and bundled compiler probe tests (`declarative_manifest_and_cfg_eval.ax`, `workspace_dag_and_cycle_rejection.ax`, `feature_unification_and_req_pkg_025.ax`, `build_manifest_probe.ax.in`, `build_manifest_oracle.py`, `build_manifest.test`) verifying byte-identical parity across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.

## Verification

Executed:
```
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/build_manifest
```
Result:
```
WEAK-NATIVE 0
TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0
```

## Files changed

- compiler/build/manifest/mod.ax
- compiler/build/workspace/mod.ax
- tests/run/build_manifest/build_manifest.test
- tests/run/build_manifest/build_manifest_oracle.py
- tests/run/build_manifest/build_manifest_probe.ax.in
- tests/run/build_manifest/declarative_manifest_and_cfg_eval.ax
- tests/run/build_manifest/declarative_manifest_and_cfg_eval.stdout
- tests/run/build_manifest/feature_unification_and_req_pkg_025.ax
- tests/run/build_manifest/feature_unification_and_req_pkg_025.stdout
- tests/run/build_manifest/workspace_dag_and_cycle_rejection.ax
- tests/run/build_manifest/workspace_dag_and_cycle_rejection.stdout
