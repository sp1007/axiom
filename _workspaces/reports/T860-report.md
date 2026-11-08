# T860 Report: E20.3 Multi-repository priority/trust routing, precompiled .axmeta/binary package consumption & axiomc pkg publish/fetch/mirror CLI

STATUS: COMPLETE

## Summary

Implemented multi-repository priority/trust routing table with dependency-confusion namespace pinning defenses, precompiled `.axmeta` interface and binary archive slice consumption engine with target/ABI compatibility gating, and the full `axiomc pkg publish|fetch|verify|search|mirror|pack|install|rollback` CLI driver subcommand engine per `spec/SPEC-112-package-registry-distribution.md` (§§1..5: `AXS-REG-001`..`053`, `AXS-REG-020`..`023`, `AXS-REG-031`, `AXS-REG-040`, `AXS-REG-050`; `REQ-ECO-8736`, `REQ-PKG-024`, `REQ-PKG-010`..`012`, `INV-REG-002`, `INV-DET-001`).

Key deliverables and architectural implementations:

1. **`compiler/pkg/distribution/mod.ax`**:
   - Distribution modes (`Source = 1`, `Binary = 2`, `Hybrid = 3`).
   - Precompiled interface summaries (`PrecompiledInterfaceSummary`) and binary slice descriptors (`BinarySliceDescriptor`, `BinaryPackageCatalog`).
   - Binary slice variant selection using target triple matching, ABI fingerprint matching, and CPU feature popcount specificity ranking (`popcount_u64`, `select_best_binary_slice`).
   - Package consumption decision engine (`decide_package_consumption`): source-free binary consumption, deterministic hybrid source fallback when slices or ABI mismatch, and immediate hard rejection for quarantined or malformed packages.
   - Multi-repository priority/trust routing table (`MultiRepoRoutingTable`, `RegistryConfig`, `PackageRouteDecision`).
   - Dependency confusion defense: namespace pinning (`@acme/*` routed exclusively to internal registries), shadow defense (`check_shadow_defense` rejecting unpinned/untrusted mirrors attempting to shadow pinned namespaces), and upfront duplicate pinning rejection (`routing_table_add_registry`).
   - Self-contained string-view utilities (`dist_sv`, `dist_sv_empty`, `dist_sv_eq`, `dist_sv_starts_with`, `str_view_to_lsv`, `lsv_to_str_view`) and fingerprint types (`ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint`) satisfying strict module layering without cyclic or heavy compiler query dependencies.

2. **`compiler/driver/registry_cmd/mod.ax`**:
   - CLI options parsing (`RegistryCmdOptions`, `parse_registry_cmd_args`) for subcommands `publish`, `fetch`, `verify`, `search`, `mirror`, `pack`, `install`, and `rollback`.
   - `execute_pkg_publish`: validates path-only dependencies (`unpublishable_dependency`), verifies publication immutability against existing sparse index (`immutable_version_exists`), supports non-mutating `--dry-run`, and formats sparse index lines and CAS blob storage paths.
   - `execute_pkg_fetch`: enforces namespace shadow defenses (`namespace_shadow_blocked`), verifies offline cache availability (`offline_missing_package`), and performs 4-stage Merkle root verification (`verify_axpkg`).
   - `execute_pkg_verify`: container header and SHA-256 Merkle root verification.
   - `execute_pkg_search`: deterministic package search matching query strings across package catalog with human-readable and JSON formatters.
   - `execute_pkg_mirror`: sparse index and blob synchronization for offline and private air-gapped repositories.
   - `execute_pkg_rollback`: transactional generation rollback via `RegistryStore`.
   - Diagnostics reporting with `DiagSink` (`AX_DRIVER_BAD_MANIFEST`, `AX_DRIVER_USAGE`, `AX_DRIVER_UNKNOWN_OPTION`).

3. **`tests/run/pkg_distribution/`**:
   - `pkg_distribution.test`: Multi-module execution test manifest invoking `pkg_distribution_oracle.py`.
   - `pkg_distribution_oracle.py`: Multi-tier bundling runner compiling and verifying probe execution parity across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with exact byte-identical stdout parity.
   - `pkg_distribution_probe.ax.in`: Multi-module probe exercising binary consumption, target/ABI mismatch rejection, hybrid fallback, quarantined isolation, multi-repo routing, namespace pinning, shadow defense, publish immutability, dry-run, search, mirror, and rollback.
   - `binary_consumption_and_abi_gate.ax` & `.stdout`: Standalone fixture testing binary slice variant selection, CPU feature specificity, and target/ABI compatibility gates.
   - `multi_repo_namespace_pinning.ax` & `.stdout`: Standalone fixture testing priority routing, namespace pinning, duplicate pin rejection, and shadow attack defense.
   - `registry_cli_publish_and_mirror.ax` & `.stdout`: Standalone fixture testing `publish` immutability, unpublishable path-only dep rejection, dry-run mode, and offline mirror checks.

## Verification

- `python build-snap-T860/tools/axtest.py --root build-snap-T860 --compiler build/axiomc2.exe --std-root std -j 1 --exclude-requires axiom0-internal run/pkg_distribution`:
  - `WEAK-NATIVE 0`
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`
- `python build-snap-T860/tests/run/pkg_distribution/pkg_distribution_oracle.py build/axiomc2.exe build tmp build-snap-T860`:
  - `PKG-DISTRIBUTION-ENGINE-OK` (passes `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each` with byte-identical stdout)
- `python tools/archcheck.py`:
  - `archcheck: 208 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`:
  - `requirements: 32308, gaps: 0 COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`:
  - `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T860`:
  - `0 REFUSED lines`

## Files changed

- compiler/driver/registry_cmd/mod.ax
- compiler/pkg/distribution/mod.ax
- tests/run/pkg_distribution/binary_consumption_and_abi_gate.ax
- tests/run/pkg_distribution/binary_consumption_and_abi_gate.stdout
- tests/run/pkg_distribution/multi_repo_namespace_pinning.ax
- tests/run/pkg_distribution/multi_repo_namespace_pinning.stdout
- tests/run/pkg_distribution/pkg_distribution.test
- tests/run/pkg_distribution/pkg_distribution_oracle.py
- tests/run/pkg_distribution/pkg_distribution_probe.ax.in
- tests/run/pkg_distribution/registry_cli_publish_and_mirror.ax
- tests/run/pkg_distribution/registry_cli_publish_and_mirror.stdout

STATUS: COMPLETE round=0