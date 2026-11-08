# T850 Execution Report — E20.1 Canonical Build Graph, Declarative `axiom.toml` Workspace & Driver Orchestration Specification (`SPEC-110`)

STATUS: COMPLETE

## Summary

Authored `spec/SPEC-110-build-graph-driver.md` (`AXS-BLD-001`..`AXS-BLD-053`) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-BLD-001`..`INV-BLD-003`) for Epic E20.1 (`T850`–`T853`), covering `REQ-PKG-022`, `REQ-PKG-024`, and `REQ-PKG-025` (along with foundational package/build invariants `REQ-PKG-001`..`REQ-PKG-021`):

1. **Five Structural Layers, Path-Independent `PackageIdentity`, and Dependency Scopes (`AXS-BLD-001`..`AXS-BLD-006`)**:
   - Explicitly separates `Module`, `Package`, `Workspace`, `DependencyGraph`, and `BuildGraph`.
   - Defines canonical `PackageIdentity` (`name`, `version`, `source_id`, `feature_set_hash`, `target_env_class`, `abi_salt`) with strict filesystem path independence (`REQ-PKG-005..007`, `REQ-PKG-015..018`).
   - Enforces inter-package DAG acyclicity (`REQ-PKG-008`, `AX_DRIVER_BAD_MANIFEST` with `data.kind = "package_cycle"`) vs intra-package module SCC separation (`REQ-PKG-009`), five dependency scopes (`normal`, `dev`, `build`, `comptime`, `system`), and deterministic lexicographical tie-breaking (`REQ-PKG-010`, `REQ-PKG-021`, `REQ-PKG-022`).
2. **Declarative `axiom.toml` Package & Workspace Manifest Specification (`AXS-BLD-010`..`AXS-BLD-016`)**:
   - Establishes `axiom.toml` (`ADR-0006`) as the canonical `AXPACKAGE` manifest (`REQ-PKG-024`) with schema rules for `[package]`, `[workspace]`, `[lib]`, `[[bin]]`, `[[build_tool]]`, `[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, `[comptime-dependencies]`, `[system-dependencies]`, `[features]`, `[profile.<name>]`, and `[target.'cfg(...)'.dependencies]`.
   - Prohibits arbitrary imperative build scripts (`script`, `command`, `shell`, `eval`; `data.kind = "forbidden_script"`).
   - Enforces `REQ-PKG-025`: required package features are never silently disabled (`data.kind = "unknown_feature" | "feature_conflict" | "missing_required_feature"`), and package metadata/features/profiles never implicitly alter core Axiom language semantics.
3. **Host/Target Cross-Build Split, Sandboxed `[[build_tool]]`, and `CompilerDB` `BuildGraph` (`AXS-BLD-020`..`AXS-BLD-025`)**:
   - Enforces strict `Build`/`Host`/`Target` environment partitioning (`Host` for `build`/`comptime` units vs `Target` for `normal`/`dev` units, rejecting cross-environment artifact mixing with `AX_LINK_ARTIFACT_TARGET_MISMATCH`).
   - Defines capability-sandboxed `[[build_tool]]` execution (`GeneratedSourceProvenance`, `NetCap = Denied`, `ProcessCap = Denied`) and `CompilerDB`-backed `BuildGraph` action lowering (`RunBuildTool`, `EmitInterface`, `CompileCodegenUnit`, `AssembleArchive`, `LinkArtifact`, `RunTestUnit`) with `.axmi` interface pipelining.
4. **Multi-Tier Content-Addressed Build Cache, Early Cutoff & Atomic Publication (`AXS-BLD-030`..`AXS-BLD-034`)**:
   - Defines four domain-separated BLAKE3-256 cache keys (`SemanticFingerprint`/`InterfaceFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, `BuildFingerprint`) with private-body early cutoff (`AXS-BLD-031`), pre-reuse digest verification and corrupt-entry eviction (`AXS-BLD-032`), and atomic temp-write-then-rename publication with `CancellationToken` cleanup (`AXS-BLD-033`).
5. **Workspace Driver Orchestration CLI, Diagnostics & Verification Matrix (`AXS-BLD-040`..`AXS-BLD-053`)**:
   - Specifies `axiomc build|check|run|test|bench|clean|graph`, workspace/package/feature/profile/target flags, `--explain`, `axiomc graph --format=json|dot`, and structured `BuildEvent` NDJSON streaming.
   - Maps corpus `AXPKG_0001..0005` and `AXBUILD_0001..0004` codes to registered `DRIVER`, `NAME`, and `LINK` codes (`AX_DRIVER_BAD_MANIFEST`, `AX_NAME_INVALID_CFG_PREDICATE`, `AX_DRIVER_INVALID_PROFILE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_DRIVER_USAGE`, `AX_DRIVER_UNKNOWN_OPTION`) and catalogues `INV-BLD-001` (`T851`), `INV-BLD-002` (`T852`), and `INV-BLD-003` (`T853`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK (0 gaps)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T850`: all changed files within allowed `paths:` and `locks:`

## Files changed

- spec/SPEC-110-build-graph-driver.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
