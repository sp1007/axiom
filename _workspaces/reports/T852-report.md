# T852 Report: E20.1 CompilerDB Build Graph Planner, Host/Target Cross-Build Split, Content-Addressed Cache & Workspace CLI

STATUS: COMPLETE

## Summary

Implemented Milestone **E20.1** (`T852`) in the self-hosted Axiom compiler per `SPEC-110 §§3..6`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, and `INV-BLD-002`:

1. **CompilerDB-Backed Build Graph Planner & Action DAG (`compiler/build/graph/mod.ax`)**:
   - Lowers the resolved `WorkspaceGraph` / `DependencyGraph` into a deterministic compilation-unit and typed artifact action DAG (`RunBuildTool`, `EmitInterface`, `CompileCodegenUnit`, `AssembleArchive`, `LinkArtifact`, `RunTestUnit`) (`AXS-BLD-023`).
   - Implements interface-pipelined parallelism: downstream compilation units depend only on upstream `EmitInterface` (`.axmi`) for type/trait/capability checking and do not wait for codegen or archive assembly until `LinkArtifact` (`AXS-BLD-023 §1`).
   - Enforces strict dual-environment `Host`/`Target` cross-build separation (`AXS-BLD-020`..`021`): when a package appears as both a host build-dependency and target dependency, distinct `PackageIdentity` and compilation units are instantiated with disjoint output directories (`.axiom/target/host/...` vs `.axiom/target/<target-triple>/...`). Mismatched cross-environment linkage is diagnosed and rejected with `AX_LINK_ARTIFACT_TARGET_MISMATCH` (exit code `1`).
   - Implements capability-sandboxed source generation (`BuildToolSandbox`) and provenance tracking (`GeneratedSourceProvenance`) for declarative `[[build_tool]]` targets (`AXS-BLD-022`): enforces read-only input filesystem capabilities, dedicated target output directory capabilities, denied network/process/wall-clock capabilities, and sanitized environment variables.
   - Guaranteed deterministic parallel scheduling: ready queue dequeue ordering and artifact keys are byte-identical across `--jobs 1` and `--jobs N` (`AXS-BLD-006`, `AXS-BLD-025`, `REQ-PKG-010`, `REQ-PKG-022`).

2. **Content-Addressed Build Cache, Early Cutoff & Atomic Publication (`compiler/build/cache/mod.ax`)**:
   - Implements the 4-tier domain-separated BLAKE3-256 fingerprint hierarchy (`SemanticFingerprint` / `InterfaceFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, `BuildFingerprint`) (`AXS-BLD-030`).
   - Implements interface early-cutoff cascade suppression (`AXS-BLD-031`): source edits modifying only private function bodies without changing emitted `.axmi` interfaces produce unchanged `SemanticFingerprint` and `AbiFingerprint`, allowing downstream packages to achieve immediate cache hits on `EmitInterface` and `CompileCodegenUnit`.
   - Implements cache poisoning defense and pre-reuse verification (`AXS-BLD-032`): header magic, length, and payload BLAKE3-256 digests are validated before reuse; corrupt or truncated entries are evicted (`CacheMissReason.CorruptEntryEvicted`) and transparently recomputed without crashing or emitting false errors.
   - Implements atomic write-then-rename staging and cancellation safety (`CancellationToken`, `AXS-BLD-033`): actions stage artifacts into worker-unique `.tmp.*` paths before atomic rename, and discard uncommitted files on cancellation.
   - Enforces reproducible build canonicalization (`AXS-BLD-034`, `REQ-PKG-022`): zeroed archive timestamps and logical `pkg://<pkg_name>@<version>/` source path mapping.

3. **Workspace Driver Orchestration CLI & Graph Introspection (`compiler/driver/workspace_cmd/mod.ax`)**:
   - Implements workspace subcommands: `axiomc build`, `axiomc check`, `axiomc run`, `axiomc clean`, and `axiomc graph` (`AXS-BLD-040`).
   - Enforces CLI discipline: rejects ambiguous `axiomc run` invocations targeting multiple binaries without `--bin` with `AX_DRIVER_USAGE` (exit code `2`); rejects unknown CLI flags with `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`); rejects invalid `--format` values with `AX_DRIVER_USAGE` (exit code `2`).
   - Implements deterministic graph introspection (`axiomc graph --format=json|dot`, `AXS-BLD-042`): emits canonical JSON schema v1 or Graphviz `dot` representation sorted in topological order.
   - Implements structured explanation (`--explain`) categorizing cache hits and miss reasons (`SourceModified`, `InterfaceChanged`, `ProfileChanged`, `FeaturesChanged`, `TargetChanged`, `CompilerChanged`, `CorruptEntryEvicted`, `MissingOutput`).

4. **Verification & Conformance Suite (`tests/run/build_graph/`)**:
   - `build_graph.test` + `build_graph_oracle.py` + `build_graph_probe.ax.in`: multi-module probe bundle exercising real `compiler/build/graph`, `compiler/build/cache`, and `compiler/driver/workspace_cmd` modules across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with byte-identical parity.
   - `deterministic_build_graph_and_host_target_split.ax`: verifies action DAG determinism, worker invariance, and `AX_LINK_ARTIFACT_TARGET_MISMATCH` enforcement.
   - `four_tier_cache_early_cutoff_and_poison_defense.ax`: verifies the 4-tier cache hierarchy, interface early cutoff, and poison/corruption eviction.
   - `workspace_cli_and_graph_introspection.ax`: verifies subcommand semantics, exit codes, and graph formatting.

## Verification

Executed:
```
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/build_graph
```
Result:
```
PASS    run/build_graph/deterministic_build_graph_and_host_target_split.ax [interp]
PASS    run/build_graph/deterministic_build_graph_and_host_target_split.ax [native]
PASS    run/build_graph/deterministic_build_graph_and_host_target_split.ax [native-O1]
PASS    run/build_graph/four_tier_cache_early_cutoff_and_poison_defense.ax [interp]
PASS    run/build_graph/four_tier_cache_early_cutoff_and_poison_defense.ax [native]
PASS    run/build_graph/four_tier_cache_early_cutoff_and_poison_defense.ax [native-O1]
PASS    run/build_graph/workspace_cli_and_graph_introspection.ax [interp]
PASS    run/build_graph/workspace_cli_and_graph_introspection.ax [native]
PASS    run/build_graph/workspace_cli_and_graph_introspection.ax [native-O1]
PASS    run/build_graph/build_graph.test
WEAK-NATIVE 0
TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0
```

Executed:
```
python tools/archcheck.py
```
Result: `archcheck: 198 files scanned, 0 violations`

Executed:
```
python .claude/skills/axiom-tasks/scripts/reqcov.py --strict
```
Result: `requirements: 32308, gaps: 0, COVERAGE OK`

Executed:
```
python .claude/skills/axiom-tasks/scripts/harness_check.py
```
Result: `harness_check: OK (phase: P20, active: 4, tasks: 228)`

## Files changed

- compiler/build/cache/mod.ax
- compiler/build/graph/mod.ax
- compiler/driver/workspace_cmd/mod.ax
- tests/run/build_graph/build_graph.test
- tests/run/build_graph/build_graph_oracle.py
- tests/run/build_graph/build_graph_probe.ax.in
- tests/run/build_graph/deterministic_build_graph_and_host_target_split.ax
- tests/run/build_graph/deterministic_build_graph_and_host_target_split.stdout
- tests/run/build_graph/four_tier_cache_early_cutoff_and_poison_defense.ax
- tests/run/build_graph/four_tier_cache_early_cutoff_and_poison_defense.stdout
- tests/run/build_graph/workspace_cli_and_graph_introspection.ax
- tests/run/build_graph/workspace_cli_and_graph_introspection.stdout

STATUS: COMPLETE round=0
