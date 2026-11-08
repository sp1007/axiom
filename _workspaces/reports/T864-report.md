# T864 Report: E20.4 Dependency Capability-Escalation Auditor, Ed25519 Package/Toolchain Signature Verifier, Provenance Attestation & axiomc trust CLI

STATUS: COMPLETE

## Summary

Implemented Milestone **E20.4** (`T864`) in the self-hosted Axiom compiler per `spec/SPEC-113-hermetic-builds-supply-chain-trust.md`, `REQ-PKG-022`, `REQ-PKG-024`, `tasks/0590 §33–§36`, `tasks/0449 §8–§11`, and `tasks/0772 §550.4, §550.24–§550.37`:

1. **Dependency Capability Model & Escalation Auditor (`std/pkg/trust/mod.ax`)**:
   - Bitmask representation of compiler/package capabilities: `CAP_NONE`, `CAP_UNSAFE` (1), `CAP_FFI` (2), `CAP_NET` (4), `CAP_FS` (8), `CAP_PROCESS` (16), `CAP_ASM` (32) (`AXS-HERM-001`).
   - Workspace trust policy representation `TrustPolicy` with root capability grants (`allow_unsafe`, `allow_ffi`, `allow_net`, `allow_fs`, `allow_process`, `allow_asm`), pattern matching against package coordinates, and policy flags (`require_signatures`, `require_provenance`, `reject_undeclared_capabilities`).
   - Dependency graph representation `AuditGraph` and iterative fixed-point transitive capability closure algorithm `audit_capability_closure`.
   - Rejects undeclared package capabilities (`TRUST_STATUS_UNDECLARED_CAPABILITY`) when code/manifest uses capabilities not declared in its `[capabilities]` table (`AXS-HERM-002`).
   - Rejects transitive capability escalation (`TRUST_STATUS_CAPABILITY_ESCALATION`) when a dependency in the transitive closure requests capabilities not authorized by the workspace root `[trust.policy]`, reporting the full violation chain (`app -> log_util -> evil_dep`) (`AXS-HERM-003`).

2. **Deterministic Ed25519 Package & Toolchain Signing Engine (`std/pkg/trust/mod.ax`)**:
   - RFC 8032 Ed25519 keypair generation, public key fingerprinting (`HexLower(SHA256("AXKEY-ED25519-v1\0" || pk)[0..16])`, 32 hex chars), and deterministic key derivation from seed (`AXS-HERM-030`).
   - Canonical domain-separated package signature transcript generator (`format_package_signature_transcript`) incorporating `pkg_id`, `merkle_root`, `sif`, `abi_fp`, `target_fp`, `lock_graph_hash`, `provenance_sha256`, `signer_id`, `key_id`, and `signed_epoch_sec`.
   - Transcript signing (`ed25519_sign_transcript`) and signature verification (`ed25519_verify_transcript`) with strict small-order and malleability rejection.
   - Comprehensive tamper rejection: detecting mutated Merkle root, corrupted signature hex, altered SIF/ABI fingerprints, or forged transcripts.

3. **Trust Roots, Revocation & Key Rotation (`std/pkg/trust/mod.ax`)**:
   - Workspace `TrustStore` containing active `TrustedSigner` records (with validity intervals `[valid_from_epoch, expires_epoch]` and scope filters) and `RevokedKey` records (`AXS-HERM-031`).
   - Package verification engine `verify_axpkg_package_signature` enforcing signature presence (`require_signatures`), signer trust, revocation list checks, and cryptographic transcript validity.
   - Dual-signed key rotation certificates (`KeyRotationCert`) signed by both the old trust anchor and new key over `"AXIOM-KEY-ROTATE-v1\0"`.
   - `trust_store_apply_rotation_cert` automating atomic revocation of deprecated keys and registration of rotated keys into the trust store.

4. **SLSA-Style JSON Provenance Attestation & Diverse Double-Compilation (`std/pkg/trust/mod.ax`)**:
   - Canonical JSON provenance manifest (`axiom.provenance.v1`) schema data structures (`ProvenanceManifest`, `ProvenanceOutput`) recording package coordinates, builder identity, sandbox configuration, compiler/SDK fingerprints, lockfile/lock-graph digests, declared/transitive capabilities, artifact outputs, and Ed25519 envelope (`AXS-HERM-033`).
   - Deterministic JSON emitter `emit_provenance_json` producing canonical sorted UTF-8 representations.
   - Provenance verifier `verify_provenance_manifest` validating artifact hashes and signatures.
   - Diverse Double-Compilation (DDC) fixed-point verification engine `verify_ddc_fixed_point` enforcing $\text{SHA256}(C_{2A}) == \text{SHA256}(C_{2B}) == \text{SHA256}(C_3)$ against bootstrap backdoors (`AXS-HERM-035`).

5. **Axiom Compiler Trust CLI (`compiler/driver/trust_cmd/mod.ax`)**:
   - Full CLI option parser and subcommand dispatch engine supporting:
     - `axiomc trust keygen --signer <id> --out-dir <dir>`
     - `axiomc trust sign <artifact> --key <path> [--provenance <path>]`
     - `axiomc trust verify <artifact> [--provenance <path>] [--ddc <stage2a> <stage2b> <stage3>]`
     - `axiomc trust rotate --old-key <path> --new-key <path> --out <cert.toml>`
     - `axiomc audit [--capabilities] [--signatures] [--provenance]`
     - `axiomc provenance emit|verify|inspect <target>`
   - Canonical diagnostic emission mapped to `AX_DRIVER_BAD_MANIFEST` with structured `DiagDataKind` entries (`"undeclared_package_capability"`, `"capability_escalation_denied"`, `"signature_invalid"`, `"unsigned_package_rejected"`, `"untrusted_signer"`, `"revoked_signing_key"`, `"provenance_mismatch"`, `"ddc_mismatch"`) per `spec/diagnostics.md` `AXD-010` and `AXD-021` (`AXS-HERM-050`).
   - Deterministic exit codes: `TRUST_EXIT_OK` (0), `TRUST_EXIT_USAGE_ERROR` (1), `TRUST_EXIT_AUDIT_ERROR` (2), `TRUST_EXIT_SIGNATURE_ERROR` (3), `TRUST_EXIT_PROVENANCE_ERROR` (4).

6. **Conformance & Supply-Chain Test Suite (`tests/run/pkg_supply_chain/`)**:
   - `pkg_supply_chain.test` + `pkg_supply_chain_oracle.py` + `pkg_supply_chain_probe.ax.in`: multi-module probe bundling real `std.pkg.trust` and `compiler.driver.trust_cmd` modules, verifying byte-identical execution parity across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
   - `ed25519_sign_and_tamper_rejection.ax`: tests Ed25519 key generation, transcript formatting, signing, verification, and tamper rejection.
   - `transitive_capability_escalation_auditor.ax`: tests capability bitmasks, allowlist policy verification, undeclared capability denial, and transitive escalation rejection.
   - `provenance_attestation_and_ddc.ax`: tests provenance manifest emission, JSON formatting, digest verification, and DDC 3-stage fixed-point verification.
   - `trust_cmd_cli_dispatch.ax`: tests `axiomc trust`, `audit`, and `provenance` subcommand options parsing, execution dispatch, and deterministic exit code contracts.

## Verification

Executed:
```
python build-snap-T864/tools/axtest.py --root build-snap-T864 --compiler build/axiomc2.exe --std-root std -j 1 --exclude-requires axiom0-internal run/pkg_supply_chain
```
Result:
```
PASS    run/pkg_supply_chain/ed25519_sign_and_tamper_rejection.ax [interp]
PASS    run/pkg_supply_chain/ed25519_sign_and_tamper_rejection.ax [native]
PASS    run/pkg_supply_chain/ed25519_sign_and_tamper_rejection.ax [native-O1]
PASS    run/pkg_supply_chain/pkg_supply_chain.test
PASS    run/pkg_supply_chain/provenance_attestation_and_ddc.ax [interp]
PASS    run/pkg_supply_chain/provenance_attestation_and_ddc.ax [native]
PASS    run/pkg_supply_chain/provenance_attestation_and_ddc.ax [native-O1]
PASS    run/pkg_supply_chain/transitive_capability_escalation_auditor.ax [interp]
PASS    run/pkg_supply_chain/transitive_capability_escalation_auditor.ax [native]
PASS    run/pkg_supply_chain/transitive_capability_escalation_auditor.ax [native-O1]
PASS    run/pkg_supply_chain/trust_cmd_cli_dispatch.ax [interp]
PASS    run/pkg_supply_chain/trust_cmd_cli_dispatch.ax [native]
PASS    run/pkg_supply_chain/trust_cmd_cli_dispatch.ax [native-O1]
WEAK-NATIVE 0
TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0
```

Executed:
```
python tools/archcheck.py
```
Result: `archcheck: 208 files scanned, 0 violations`

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

Executed:
```
python .claude/skills/axiom-tasks/scripts/taskctl.py changes T864
```
Result: `0 REFUSED lines`

## Files changed

- compiler/driver/trust_cmd/mod.ax
- std/pkg/trust/mod.ax
- tests/run/pkg_supply_chain/ed25519_sign_and_tamper_rejection.ax
- tests/run/pkg_supply_chain/ed25519_sign_and_tamper_rejection.stdout
- tests/run/pkg_supply_chain/pkg_supply_chain.test
- tests/run/pkg_supply_chain/pkg_supply_chain_oracle.py
- tests/run/pkg_supply_chain/pkg_supply_chain_probe.ax.in
- tests/run/pkg_supply_chain/provenance_attestation_and_ddc.ax
- tests/run/pkg_supply_chain/provenance_attestation_and_ddc.stdout
- tests/run/pkg_supply_chain/transitive_capability_escalation_auditor.ax
- tests/run/pkg_supply_chain/transitive_capability_escalation_auditor.stdout
- tests/run/pkg_supply_chain/trust_cmd_cli_dispatch.ax
- tests/run/pkg_supply_chain/trust_cmd_cli_dispatch.stdout

## Status

STATUS: COMPLETE round=0
