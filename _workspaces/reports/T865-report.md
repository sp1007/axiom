# T865 Report: E20.4 Hermetic build sandbox, cross-directory/cross-machine bit-for-bit reproducibility & supply-chain trust conformance suite

## Summary
Task T865 delivers the comprehensive end-to-end conformance test suite certifying Phase 20 (`E20.4`) exit criteria for `SPEC-113` (`AXS-HERM-001`..`AXS-HERM-053`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-HERM-001`, `INV-HERM-002`, `INV-HERM-003`, `INV-DET-002`).

The suite provides:
1. Master conformance oracle `e20_4_hermetic_supply_chain_oracle.test` + `e20_4_hermetic_supply_chain_oracle.py` + `e20_4_hermetic_supply_chain_probe.ax.in`:
   - Bundles live compiler modules (`compiler.build.sandbox`, `compiler.build.repro`, `compiler.driver.trust_cmd`, plus compiler kernel and build workspace dependencies) with standard library modules (`std.pkg.lockfile`, `std.pkg.store`, `std.pkg.archive`, `std.pkg.trust`) and executes across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with 100% byte-for-byte identical output parity.
   - Executes differential verification (`--interp` vs native `-O1 --verify-each`) across all 5 standalone `.ax` conformance fixtures with exact byte output matching (`0 WEAK-NATIVE`).
   - Audits compiled binaries for zero leaked debug/metadata tokens (`AXMETA01`, `AXMI0001`, `AXLTO001`, `AXMIR001`, `AXDB0001`, `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, `__ax_interp_eval`).
2. Standalone `.ax` and `.stdout` conformance fixtures:
   - `bit_for_bit_reproducibility_and_path_remapping.ax`: Verifies cross-directory host path normalization via `--remap-path-prefix`, 12-component build fingerprint derivation, zero host leakage audit in debug info/symbol strings, byte-level double-build verification (`build_a == build_b`), and section-level diff localization (`AXS-HERM-011..016`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-DET-002`).
   - `hermetic_sandbox_isolation_and_boundary_defense.ax`: Validates sandbox boundary policies including canonical path normalization, traversal rejection (`..`), host escape blocking (`/etc`, `C:\Windows`), read-only source/dep enforcement, writable output isolation, environment variable scrubbing, clock/RNG policy lockdown, and network/process execution blocking (`AXS-HERM-001..010`, `INV-HERM-001`, `INV-HERM-002`, `INV-HERM-003`).
   - `dependency_capability_escalation_auditor.ax`: Exercises capability-based security model (`unsafe`, `ffi`, `net`, `fs`, `process`, `asm`), undeclared capability denial, transitive dependency capability closure aggregation, workspace permission validation, and capability escalation rejection (`AX_DRIVER_CAPABILITY_ESCALATION`) (`AXS-HERM-021..027`, `REQ-PKG-024`).
   - `ed25519_signature_trust_and_provenance.ax`: Certifies Ed25519 cryptographic key generation, digital signing, detached signature verification over canonical canonicalized transcripts, tamper rejection (archive payload, SIF envelope, or signature tampering), trust store validation, key revocation lists, dual-signed key rotation certificates, SLSA provenance round-trips, and Diverse Double-Compiling (DDC) fixed-point verification (`AXS-HERM-031..044`, `REQ-PKG-022`, `REQ-PKG-024`).
   - `trust_cmd_cli_and_diagnostic_contract.ax`: Tests `axiomc` supply-chain trust subcommands (`keygen`, `sign`, `verify`, `audit`, `provenance`), standard CLI exit codes (`0`, `1`, `2`), structured machine-readable JSON error output, and diagnostic code mapping (`AX_PKG_UNTRUSTED_KEY`, `AX_PKG_REVOKED_KEY`, `AX_PKG_TAMPERED_ARCHIVE`, `AX_PKG_ROTATION_EXPIRED`, `AX_PKG_CAPABILITY_VIOLATION`) (`AXS-HERM-045..053`).
3. Complete documentation in `README.md` mapping normative contracts, rules, invariants, requirements, and test fixtures.

## Verification Results
- Conformance suite execution:
  - Master Conformance Oracle probe:
    - Byte-identical output parity verified across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each`.
    - Clean binary audits: 0 leaked metadata tokens.
  - Differential verification (`--interp` vs native `-O1 --verify-each`):
    - All 5 standalone fixtures matched byte-for-byte (`0 WEAK-NATIVE`).
- Architecture check (`tools/archcheck.py`):
  - `archcheck: 208 files scanned, 0 violations`.
- Requirement coverage check (`reqcov.py --strict`):
  - `32308 requirements, 0 gaps, COVERAGE OK`.
- Harness check (`harness_check.py`):
  - `HARNESS OK`.
- Taskctl changes check:
  - `0 REFUSED lines`.
- Canonical syntax compliance (`axiom-syntax`):
  - Strictly `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Files changed
- tests/conformance/p20/e20_4_hermetic_supply_chain/README.md
- tests/conformance/p20/e20_4_hermetic_supply_chain/bit_for_bit_reproducibility_and_path_remapping.ax
- tests/conformance/p20/e20_4_hermetic_supply_chain/bit_for_bit_reproducibility_and_path_remapping.stdout
- tests/conformance/p20/e20_4_hermetic_supply_chain/dependency_capability_escalation_auditor.ax
- tests/conformance/p20/e20_4_hermetic_supply_chain/dependency_capability_escalation_auditor.stdout
- tests/conformance/p20/e20_4_hermetic_supply_chain/e20_4_hermetic_supply_chain_oracle.py
- tests/conformance/p20/e20_4_hermetic_supply_chain/e20_4_hermetic_supply_chain_oracle.test
- tests/conformance/p20/e20_4_hermetic_supply_chain/e20_4_hermetic_supply_chain_probe.ax.in
- tests/conformance/p20/e20_4_hermetic_supply_chain/ed25519_signature_trust_and_provenance.ax
- tests/conformance/p20/e20_4_hermetic_supply_chain/ed25519_signature_trust_and_provenance.stdout
- tests/conformance/p20/e20_4_hermetic_supply_chain/hermetic_sandbox_isolation_and_boundary_defense.ax
- tests/conformance/p20/e20_4_hermetic_supply_chain/hermetic_sandbox_isolation_and_boundary_defense.stdout
- tests/conformance/p20/e20_4_hermetic_supply_chain/trust_cmd_cli_and_diagnostic_contract.ax
- tests/conformance/p20/e20_4_hermetic_supply_chain/trust_cmd_cli_and_diagnostic_contract.stdout

STATUS: COMPLETE round=0
