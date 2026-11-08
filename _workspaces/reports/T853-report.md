# T853 Report: E20.1 Build Graph, Workspace Orchestration, Feature/Profile Determinism & Driver CLI Conformance Suite

STATUS: COMPLETE

## Summary

Created and certified the milestone **E20.1** end-to-end conformance suite in `tests/conformance/p20/e20_1_build_graph_driver/` verifying `SPEC-110 §§1..5`, `AXS-BLD-001`..`053`, `INV-BLD-001`..`003`, and requirements `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`:

1. **`README.md` Specification, Rule & Invariant Matrix**:
   - Comprehensive mapping of all E20.1 normative contracts (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-BLD-001`..`003`, `AXS-BLD-001`..`053`) to conformance test fixtures and master oracle assertions.

2. **Master Conformance Oracle & Live Multi-Module Probe (`e20_1_build_graph_driver_oracle.test`, `e20_1_build_graph_driver_oracle.py`, `e20_1_build_graph_driver_probe.ax.in`)**:
   - Assembles and bundles live compiler modules: `compiler.kernel.*`, `compiler.source.*`, `compiler.diag.*`, `compiler.query.db`, `compiler.diag.ux2`, `compiler.build.manifest`, `compiler.build.workspace`, `compiler.build.cache`, `compiler.build.graph`, and `compiler.driver.workspace_cmd`.
   - Executes the live probe bundle across `--interp` and compiles + executes at native `-O0` (single compile within `<120s` resource limit), verifying byte-identical execution parity and exit code `0`.
   - Performs differential verification (`--interp` vs native `-O1 --verify-each`) across all 4 standalone conformance fixtures.
   - Audits linked production `.exe` images to certify zero leaked `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, or `.axlto` metadata sections or magic bytes.

3. **Standalone Conformance Fixtures (`modes: interp native`, `0 WEAK-NATIVE`)**:
   - `workspace_dag_and_worker_invariance.ax` + `.stdout`: Multi-package workspace DAG construction, path-independent `PackageIdentity` (`REQ-PKG-005`, `REQ-PKG-018`), deterministic topological ordering (`AXS-BLD-006`), worker-count invariance (1 vs 4 workers produce byte-identical execution orders and aggregate output digests, `AXS-BLD-025`, `REQ-PKG-010`, `REQ-PKG-022`), and filesystem enumeration order (`readdir`) independence (`0168 §16-17`, `tasks/0411 §47`).
   - `package_cycle_vs_intra_module_scc.ax` + `.stdout`: Inter-package dependency cycle rejection with `AX_DRIVER_BAD_MANIFEST` (`data.kind = "package_cycle"`, `data.cycle = "alpha -> beta -> alpha"`, `AXS-BLD-003`, `REQ-PKG-008`, `AXS-BLD-050`) vs legal intra-package declaration SCC evaluation in `CompilerDB` (`REQ-PKG-009`, `SPEC-21`, `tasks/0356 §12`, `tasks/0661 §6`), and intra-package module import cycle rejection (`AX_NAME_IMPORT_CYCLE`, `SPEC-03`).
   - `feature_cfg_and_semantic_firewall.ax` + `.stdout`: Feature integrity and semantic non-interference (`REQ-PKG-025`, `INV-BLD-001`, no silent feature dropping, metadata never alters core language semantics), closed feature namespace and conflict rejection (`AXS-BLD-014..015`), `dev-dependencies` firewall (isolated to test/bench/examples, never leaking into downstream consumers or `lib` targets, `AXS-BLD-005`), and `Host` vs `Target` feature split.
   - `cross_target_cache_and_driver_cli.ax` + `.stdout`: Strict `Host`/`Target` cross-compilation split (`AXS-BLD-020..021`, rejection with `AX_LINK_ARTIFACT_TARGET_MISMATCH` = 220), 4-tier content-addressed build cache (`AXS-BLD-030`, `REQ-PKG-022`, `REQ-PKG-024`), interface early-cutoff cascade suppression (`AXS-BLD-031`), cache-poisoning/truncation defense with transparent recomputation (`AXS-BLD-032`), atomic staging (`AXS-BLD-033`), and `axiomc build|check|run|clean|graph --format=json|dot` CLI subcommands and exit codes (`AXS-BLD-040..042`, `INV-BLD-002`, `INV-BLD-003`).

## Verification Evidence

1. **Full Conformance Suite Execution**:
   ```
   python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p20/e20_1_build_graph_driver
   ```
   Output:
   ```
   PASS    conformance/p20/e20_1_build_graph_driver/cross_target_cache_and_driver_cli.ax [interp]
   PASS    conformance/p20/e20_1_build_graph_driver/cross_target_cache_and_driver_cli.ax [native]
   PASS    conformance/p20/e20_1_build_graph_driver/cross_target_cache_and_driver_cli.ax [native-O1]
   PASS    conformance/p20/e20_1_build_graph_driver/feature_cfg_and_semantic_firewall.ax [interp]
   PASS    conformance/p20/e20_1_build_graph_driver/feature_cfg_and_semantic_firewall.ax [native]
   PASS    conformance/p20/e20_1_build_graph_driver/feature_cfg_and_semantic_firewall.ax [native-O1]
   PASS    conformance/p20/e20_1_build_graph_driver/package_cycle_vs_intra_module_scc.ax [interp]
   PASS    conformance/p20/e20_1_build_graph_driver/package_cycle_vs_intra_module_scc.ax [native]
   PASS    conformance/p20/e20_1_build_graph_driver/package_cycle_vs_intra_module_scc.ax [native-O1]
   PASS    conformance/p20/e20_1_build_graph_driver/workspace_dag_and_worker_invariance.ax [interp]
   PASS    conformance/p20/e20_1_build_graph_driver/workspace_dag_and_worker_invariance.ax [native]
   PASS    conformance/p20/e20_1_build_graph_driver/workspace_dag_and_worker_invariance.ax [native-O1]
   PASS    conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test
   WEAK-NATIVE 0
   TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0
   ```

2. **Strict Requirement Coverage (`reqcov.py --strict`)**:
   ```
   requirements: 32308
     v1-core  implemented=5864
     v1-full  implemented=6637  planned=2194
     post-v1  epic=17535  planned=78
   gaps: 0
   COVERAGE OK
   ```

3. **Harness Integrity Check (`harness_check.py`)**:
   ```
   HARNESS OK
   ```

4. **Taskctl Changes Audit (`taskctl.py changes T853`)**:
   - Clean staging of all 12 conformance suite files within `paths: [tests/conformance/p20/e20_1_build_graph_driver]`.

## Files changed

- tests/conformance/p20/e20_1_build_graph_driver/README.md
- tests/conformance/p20/e20_1_build_graph_driver/cross_target_cache_and_driver_cli.ax
- tests/conformance/p20/e20_1_build_graph_driver/cross_target_cache_and_driver_cli.stdout
- tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.py
- tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test
- tests/conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_probe.ax.in
- tests/conformance/p20/e20_1_build_graph_driver/feature_cfg_and_semantic_firewall.ax
- tests/conformance/p20/e20_1_build_graph_driver/feature_cfg_and_semantic_firewall.stdout
- tests/conformance/p20/e20_1_build_graph_driver/package_cycle_vs_intra_module_scc.ax
- tests/conformance/p20/e20_1_build_graph_driver/package_cycle_vs_intra_module_scc.stdout
- tests/conformance/p20/e20_1_build_graph_driver/workspace_dag_and_worker_invariance.ax
- tests/conformance/p20/e20_1_build_graph_driver/workspace_dag_and_worker_invariance.stdout

STATUS: COMPLETE round=0
