# T863 Report: E20.4 Hermetic Build Sandbox, Filesystem/Env/Network/Clock Isolation, --remap-path-prefix & Bit-for-Bit Reproducibility Verifier

STATUS: COMPLETE

## Summary

Implemented Milestone **E20.4** (`T863`) in the self-hosted Axiom compiler per `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`, `REQ-PKG-022`, `REQ-PKG-024`, and `INV-HERM-001`:

1. **Hermetic Build Sandbox & Host Isolation (`compiler/build/sandbox/mod.ax`)**:
   - Implements `BuildSandbox`, `SandboxConfig`, and `SandboxMount` enforcing container-free native host isolation (`AXS-HERM-010`..`015`).
   - Filesystem Isolation (`AXS-HERM-011`): Declares logical read roots (`/source`, `/dependencies`, `@std`) and write roots (`/output`, `/build` scratch). Enforces canonicalize-before-authorize path resolution (`sandbox_normalize_path` -> resolve -> authorize) to reject path traversal escapes (`../`), absolute host path escapes (`C:/...`, `/etc/...`), and writes to read-only source or dependency roots with canonical diagnostic `AX_DRIVER_BAD_MANIFEST` (`kind = "sandbox_fs_violation"`).
   - Sanitized Environment Allowlist (`AXS-HERM-013`): Scrubs ambient host environment variables (`HOME`, `USER`, `PATH`, etc.), establishes canonical compiler variables (`AXIOM_PKG_NAMESPACE`, `AXIOM_PKG_NAME`, `AXIOM_PKG_VERSION`, `AXIOM_TARGET_TRIPLE`, `AXIOM_HOST_TRIPLE`, `AXIOM_PROFILE`, `AXIOM_EDITION`, `AXIOM_SOURCE_DIR`, `AXIOM_OUT_DIR`, `SOURCE_DATE_EPOCH`, `TZ`, `LC_ALL`), ensures `PATH` is empty `""`, and rejects undeclared environment variable queries with `AX_DRIVER_BAD_MANIFEST` (`kind = "sandbox_env_violation"`). Computes deterministic ASCII-sorted environment digest `sandbox_compute_env_digest`.
   - Network & Process Confinement (`AXS-HERM-012`, `015`): Unconditionally blocks network sockets/HTTP/DNS requests during compilation with `AX_DRIVER_BAD_MANIFEST` (`kind = "sandbox_net_violation"`), and blocks unauthorized subprocess spawning with `AX_DRIVER_BAD_MANIFEST` (`kind = "sandbox_process_violation"`).
   - Virtual Clock & Seeded Entropy (`AXS-HERM-014`): Enforces virtual frozen epoch (`SOURCE_DATE_EPOCH = 0`) and deterministic PRNG derived from package identity/hash (`ax_hash_u64`), while rejecting direct host wall-clock and non-deterministic OS entropy queries with `AX_DRIVER_BAD_MANIFEST` (`kind = "sandbox_clock_or_rng_violation"`).

2. **Cross-Directory Reproducibility, `--remap-path-prefix` & Differential Verifier (`compiler/build/repro/mod.ax`)**:
   - Canonical Path Prefix Remapping (`AXS-HERM-020`): Normalizes path separators `\` to `/` and installs virtual prefix mappings (`@pkg/<name>@<version>/...`, `@gen/...`, `@out/...`, `@std/...`, `@ws/...`, and user `--remap-path-prefix <from>=<to>` rules) resolved in longest-prefix-first priority order.
   - Post-Link Host-Path Leakage Audit (`AXS-HERM-020`, `INV-DET-002`): Scans emitted artifact bytes for literal host workspace or user home paths, emitting `AX_DRIVER_BAD_MANIFEST` (`kind = "repro_host_path_leak"`) if any unremapped host path leaks into binary or metadata artifacts.
   - Canonical 12-Component `HermeticBuildFingerprint` (`AXS-HERM-022`): Domain-separated SHA-256 digest over `"AXHERM-FP-v1\0"` and canonical components ($C_1$..$C_{12}$: `CompilerSemanticVersion`, `CompilerBinarySha256`, `LanguageEdition`, `TargetFingerprint`, `SdkFingerprint`, `SourceMerkleRoot`, `DependencyLockGraphHash`, `FeatureSetHash`, `ComptimeInputsDigest`, `BuildToolInputsDigest`, `ProfileConfigDigest`, `DeclaredEnvDigest`).
   - Double-Build Differential Verifier (`AXS-HERM-023`): `compare_build_artifacts` and `verify_reproducible_build` (`ReproStatus.Reproduced`, `ReproStatus.NotReproduced`, `ReproStatus.Inconclusive`) locate the exact first differing byte offset and container section (`.text`, `.rdata`, etc.), emitting `AX_DRIVER_BAD_MANIFEST` (`kind = "repro_mismatch"`) on divergence.

3. **Verification & Conformance Suite (`tests/run/build_hermetic/`)**:
   - `build_hermetic.test` + `build_hermetic_oracle.py` + `build_hermetic_probe.ax.in`: multi-module probe bundle exercising real `compiler/build/sandbox` and `compiler/build/repro` modules across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with byte-identical parity.
   - `sandbox_filesystem_env_network_clock_isolation.ax`: verifies sandbox rejection of filesystem path escapes, undeclared env reads, network access, and unauthorized subprocesses.
   - `canonical_path_prefix_remapping_and_host_leak_audit.ax`: verifies cross-platform path prefix normalization and residual host-path leak audit.
   - `double_build_differential_reproducibility_verifier.ax`: verifies 12-component fingerprint invariance, clean double-build reproduction, and exact byte/section diff diagnostics.
   - `hermetic_boundary_cases.ax`: cross-checks boundary edge cases including sneaky traversal escapes (`/source/sub/../../etc/passwd`, `\source\..\..\secret`, `\source\sub\..`, `/source/..`), longest-prefix remap precedence, `SOURCE_DATE_EPOCH` determinism, and PRNG seed stability.

## Verification

Executed:
```
python tools/axtest.py --compiler build/axiomc2.exe -j 1 -v --exclude-requires axiom0-internal run/build_hermetic
```
Result:
```
PASS    run/build_hermetic/build_hermetic.test
PASS    run/build_hermetic/canonical_path_prefix_remapping_and_host_leak_audit.ax [interp]
PASS    run/build_hermetic/canonical_path_prefix_remapping_and_host_leak_audit.ax [native]
PASS    run/build_hermetic/canonical_path_prefix_remapping_and_host_leak_audit.ax [native-O1]
PASS    run/build_hermetic/double_build_differential_reproducibility_verifier.ax [interp]
PASS    run/build_hermetic/double_build_differential_reproducibility_verifier.ax [native]
PASS    run/build_hermetic/double_build_differential_reproducibility_verifier.ax [native-O1]
PASS    run/build_hermetic/hermetic_boundary_cases.ax [interp]
PASS    run/build_hermetic/hermetic_boundary_cases.ax [native]
PASS    run/build_hermetic/hermetic_boundary_cases.ax [native-O1]
PASS    run/build_hermetic/sandbox_filesystem_env_network_clock_isolation.ax [interp]
PASS    run/build_hermetic/sandbox_filesystem_env_network_clock_isolation.ax [native]
PASS    run/build_hermetic/sandbox_filesystem_env_network_clock_isolation.ax [native-O1]
WEAK-NATIVE 0
TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0
```

Executed:
```
python tools/archcheck.py
```
Result: `archcheck: 200 files scanned, 0 violations`

Executed:
```
python .claude/skills/axiom-tasks/scripts/reqcov.py --strict
```
Result: `requirements: 32308, gaps: 0, COVERAGE OK`

Executed:
```
python .claude/skills/axiom-tasks/scripts/harness_check.py
```
Result: `HARNESS OK`

## Files changed

- compiler/build/repro/mod.ax
- compiler/build/sandbox/mod.ax
- tests/run/build_hermetic/build_hermetic.test
- tests/run/build_hermetic/build_hermetic_oracle.py
- tests/run/build_hermetic/build_hermetic_probe.ax.in
- tests/run/build_hermetic/canonical_path_prefix_remapping_and_host_leak_audit.ax
- tests/run/build_hermetic/canonical_path_prefix_remapping_and_host_leak_audit.stdout
- tests/run/build_hermetic/double_build_differential_reproducibility_verifier.ax
- tests/run/build_hermetic/double_build_differential_reproducibility_verifier.stdout
- tests/run/build_hermetic/hermetic_boundary_cases.ax
- tests/run/build_hermetic/hermetic_boundary_cases.stdout
- tests/run/build_hermetic/sandbox_filesystem_env_network_clock_isolation.ax
- tests/run/build_hermetic/sandbox_filesystem_env_network_clock_isolation.stdout

## Status

STATUS: COMPLETE round=0
