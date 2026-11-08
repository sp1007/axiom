# T861 Report: E20.3 Package registry protocol, .axpkg deterministic archive, offline mirror & binary/interface distribution conformance suite

## Summary
Task T861 delivers the comprehensive end-to-end conformance test suite certifying Phase 20 (`E20.3`) exit criteria for `SPEC-112` (`AXS-REG-001`..`AXS-REG-053`, `REQ-ECO-8736`, `REQ-PKG-024`, `REQ-PKG-010`..`013`, `INV-REG-001`..`002`, `INV-DET-001`).

The suite provides:
1. Master conformance oracle `e20_3_registry_distribution_oracle.test` + `e20_3_registry_distribution_oracle.py` + `e20_3_registry_distribution_probe.ax.in`:
   - Bundles live compiler modules (`compiler.pkg.distribution`, `compiler.driver.registry_cmd`, plus compiler kernel and build workspace dependencies) with standard library modules (`std.pkg.lockfile`, `std.pkg.archive`, `std.pkg.registry`) and executes across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with 100% byte-for-byte identical output parity.
   - Executes differential verification (`--interp` vs native `-O1 --verify-each`) across all 5 standalone `.ax` conformance fixtures with exact byte output matching (`0 WEAK-NATIVE`).
   - Audits compiled binaries for zero leaked debug/metadata tokens (`AXMETA01`, `AXMI0001`, `AXLTO001`, `AXMIR001`, `AXDB0001`, `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, `__ax_interp_eval`).
2. Standalone `.ax` and `.stdout` conformance fixtures:
   - `publish_sparse_index_fetch_and_build.ax`: End-to-end `axiomc pkg publish` pipeline, canonical `.axpkg` packaging, deterministic SHA-256 Merkle root binding, sparse index update (`index/<ns>/<p2>/<name>.jsonl`), content-addressed blob storage (`blobs/sha256/<b0>/<b1>/<sha256>.axpkg`), `axiomc pkg fetch` pre-use verification, and isolated workspace build execution (`REQ-ECO-8736`, `REQ-PKG-024`, `AXS-REG-001`, `AXS-REG-004`, `AXS-REG-030`, `AXS-REG-040`).
   - `immutable_version_and_merkle_tamper_detection.ax`: Permanent package version immutability (`AXS-REG-003 §1`), rejection of conflicting republish attempts (`AX_DRIVER_BAD_MANIFEST` with `data.kind = "immutable_version_exists"`), idempotent re-publication validation, SHA-256 binary Merkle tree tamper detection (`AXS-REG-012`) rejecting single-bit payload modifications or altered chunk digests (`data.kind = "merkle_mismatch"`), sandboxed path traversal and quota enforcement (`AXS-REG-013`), and quarantine isolation blocking compromised package versions (`data.kind = "quarantined_package"`).
   - `offline_mirror_and_airgapped_resolution.ax`: Offline repository mirroring (`axiomc pkg mirror`, `AXS-REG-032 §1`), transport-neutral `config.json` protocol, content-identity preservation across mirror locations (`PKG-INV-34`), hermetic air-gapped resolution with zero network access (`REQ-PKG-013`), and local cache hierarchy enforcement with detection of missing packages under `--offline` (`data.kind = "offline_missing_package"`).
   - `precompiled_axmeta_binary_and_namespace_pinning.ax`: Precompiled `.axmeta`/`.axmi` binary package consumption (`AXS-REG-020`..`023`), source-free `CompilerDB` ingestion, three-tier fingerprint validation (`ApiFingerprint`, `SemanticInterfaceFingerprint`, `AbiFingerprint`), CPU feature mask popcount specificity selection, deterministic hybrid fallback to source, and multi-repository namespace pinning (`AXS-REG-031 §1`) preventing dependency-confusion attacks (`data.kind = "namespace_shadow_blocked"` and `"conflicting_namespace_pin"`).
   - `transactional_journal_rollback_and_downgrade_guard.ax`: Atomic package installation state machine (`AXS-REG-034`), write-ahead `.axupdate-journal` logging, generation pointer transitions (`active -> gen_N`), staged transaction rollback on error, safe rollback to prior generations without user data corruption, downgrade guard (`allow_downgrade = false`) preventing version regressions, and minimum secure version floor (`min_allowed_version`) enforcement (`AXS-REG-033`).
3. Complete documentation in `README.md` mapping normative contracts, rules, requirements, and test fixtures.

## Verification Results
- `axtest.py` conformance suite execution:
  - Command: `python build-snap-T861/tools/axtest.py --root build-snap-T861 --compiler build/axiomc2.exe --std-root D:\projects\compiler\new lang\build-snap-T861\std -j 1 --exclude-requires axiom0-internal conformance/p20/e20_3_registry_distribution`
  - Result: `WEAK-NATIVE 0`, `TOTAL 16 PASS 16 FAIL 0 SKIP 0 XFAIL 0`.
- Master Conformance Oracle probe:
  - Byte-identical output parity verified across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each`.
  - Clean binary audits: 0 leaked metadata tokens.
- Architecture check (`tools/archcheck.py`):
  - `archcheck: 208 files scanned, 0 violations`.
- Requirement coverage check (`reqcov.py --strict`):
  - `COVERAGE OK`.
- Harness check (`harness_check.py`):
  - `HARNESS OK`.
- Changes validation (`taskctl.py changes T861`):
  - 0 REFUSED lines.
- Canonical syntax compliance (`axiom-syntax`):
  - Strictly `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Files changed
- tests/conformance/p20/e20_3_registry_distribution/README.md
- tests/conformance/p20/e20_3_registry_distribution/e20_3_registry_distribution_oracle.py
- tests/conformance/p20/e20_3_registry_distribution/e20_3_registry_distribution_oracle.test
- tests/conformance/p20/e20_3_registry_distribution/e20_3_registry_distribution_probe.ax.in
- tests/conformance/p20/e20_3_registry_distribution/immutable_version_and_merkle_tamper_detection.ax
- tests/conformance/p20/e20_3_registry_distribution/immutable_version_and_merkle_tamper_detection.stdout
- tests/conformance/p20/e20_3_registry_distribution/offline_mirror_and_airgapped_resolution.ax
- tests/conformance/p20/e20_3_registry_distribution/offline_mirror_and_airgapped_resolution.stdout
- tests/conformance/p20/e20_3_registry_distribution/precompiled_axmeta_binary_and_namespace_pinning.ax
- tests/conformance/p20/e20_3_registry_distribution/precompiled_axmeta_binary_and_namespace_pinning.stdout
- tests/conformance/p20/e20_3_registry_distribution/publish_sparse_index_fetch_and_build.ax
- tests/conformance/p20/e20_3_registry_distribution/publish_sparse_index_fetch_and_build.stdout
- tests/conformance/p20/e20_3_registry_distribution/transactional_journal_rollback_and_downgrade_guard.ax
- tests/conformance/p20/e20_3_registry_distribution/transactional_journal_rollback_and_downgrade_guard.stdout

STATUS: COMPLETE round=0
