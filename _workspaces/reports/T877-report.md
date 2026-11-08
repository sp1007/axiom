# T877 Report — E20.6 Native SDK/sysroot, AXTOOLCHAIN distribution & two-machine lockfile reproducible multi-package workspace conformance suite

## Summary

Implemented task **T877** for Milestone **E20.6** (Phase `P20`), establishing the comprehensive end-to-end conformance test suite certifying declarative `.axsdk` sysroots, `AXTOOLCHAIN` distribution, multi-target SDK pinning in `axiom.lock`, and the Phase P20 exit criterion (`multi-package workspace builds reproducibly from lockfile on two machines`, `ROADMAP.md` §3, `REQ-PKG-022`) under `tests/conformance/p20/e20_6_sdk_toolchain_workspace/` per `SPEC-116` (`AXS-SDK-001`..`AXS-SDK-055`, `REQ-ECO-8736`, `REQ-PKG-022`, `INV-SDK-001`..`003`):

1. **Suite Architecture & Documentation (`tests/conformance/p20/e20_6_sdk_toolchain_workspace/README.md`)**:
   - Mapped all requirements and rules (`AXS-SDK-001`..`055`) and architectural invariants (`INV-SDK-001`, `INV-SDK-002`, `INV-SDK-003`).
   - Defined strict conformance criteria across tier-1/tier-2 target profiles (`x86_64-pc-windows-msvc`, `aarch64-pc-windows-msvc`, `x86_64-unknown-linux-gnu`, `aarch64-unknown-linux-gnu`, `aarch64-apple-darwin`, `wasm32-wasi`).
   - Specified two-machine reproducibility guarantees across isolated execution environments (paths, usernames, temp directories, timezones, locale, environment variables, thread counts).

2. **Cross-Target Declarative Sysroots & CRT Contracts (`cross_target_declarative_sysroot_and_crt.ax`, `.stdout`)**:
   - Conformance fixture verifying C-free cross-target sysroot profiles across PE/COFF, ELF64, Mach-O, and WASI.
   - Tested subsystem CRT entrypoints (`main`, `WinMain`, `_start`, `_initialize`) and fail-closed denial of incompatible subsystem contracts (`AX_SDK_STARTUP_CONTRACT_MISMATCH`).
   - Verified platform dynamic import stub resolution across formats and missing symbol denial (`AX_SDK_IMPORT_STUB_NOT_FOUND`).
   - Verified fail-closed rejection of ambient host OS paths (`AX_SDK_HOST_FALLBACK_DENIED`).
   - Tested compile-time API availability gating (`@available` / `AX_SDK_API_UNAVAILABLE`).
   - Tested cryptographic `SdkFingerprint` calculation and tamper rejection (`AX_SDK_FINGERPRINT_MISMATCH`).

3. **AXTOOLCHAIN Archive Packaging & Distribution (`axtoolchain_bundle_packager_and_distribution.ax`, `.stdout`)**:
   - Conformance fixture certifying toolchain registry lookup and triple alias normalization.
   - Verified deterministic lexicographical entry sorting in `.axsdk` and `.axtoolchain` archives.
   - Verified Merkle tree root calculation and domain-separated hashing.
   - Enforced security checks: path traversal denial (`BUNDLE_STATUS_PATH_TRAVERSAL`), zero-mtime requirement (`BUNDLE_STATUS_CORRUPT`), and executable mode preservation.
   - Verified Ed25519 authoritativeness signature validation and untrusted key rejection (`BUNDLE_STATUS_SIGNATURE_INVALID`).
   - Tested side-by-side cache paths and air-gapped offline mirror detection (`BUNDLE_STATUS_OFFLINE_MISSING`).

4. **Lockfile Pinning, Drift Detection & Tamper Defense (`lockfile_pinning_drift_and_tamper_defense.ax`, `.stdout`)**:
   - Conformance fixture certifying parsing and serialization of `[sdk."<triple>"]` and `[toolchain]` tables in `axiom.lock`.
   - Verified `--locked` drift detection rejecting missing pins or changed checksums with `BUNDLE_STATUS_LOCK_MISMATCH`.
   - Verified action cache key composition including compiler binary digest, flags, SDK fingerprint, and hermetic sysroot manifest.

5. **Two-Machine Reproducible Multi-Package Workspace Build (`two_machine_reproducible_workspace_build.ax`, `.stdout`)**:
   - Conformance fixture verifying the Phase P20 exit criterion:
     - 12-component hermetic build input fingerprint invariance across distinct environments.
     - Canonical virtual path remapping (`@pkg/<name>@<ver>`, `@std`, `@out`) neutralizing machine-specific roots.
     - Section-level artifact comparison (`ReproArtifactComparison`) certifying byte-for-byte reproducibility across libraries, binaries, precompiled metadata, and dynamic plugins.
     - Host path leak auditing (`audit_host_path_leaks`) denying machine paths, usernames, or temporary directories in compiled artifacts.

6. **CLI Workflow & Deterministic Exit Codes (`sdk_toolchain_cli_workflow_contract.ax`, `.stdout`)**:
   - Conformance fixture verifying `axiomc sdk` and `axiomc toolchain` command contracts.
   - Verified subcommands (`list`, `install`, `verify`, `pack`, `pin`, `info`).
   - Enforced canonical exit codes: 0 (OK), 1 (Usage/Target error), 2 (Verify error), 3 (Signature error), 4 (IO/Offline error), 5 (Security error).

7. **Master Conformance Probe & Live Two-Machine Simulation Oracle (`e20_6_sdk_toolchain_workspace_oracle.py`, `.test`, `_probe.ax.in`)**:
   - Bundles compiler and standard library modules into self-contained probe.
   - Executes probe across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with strict stdout parity.
   - Runs live differential testing of all 5 standalone fixtures across interpreter and native optimization modes.
   - Performs physical two-machine workspace build simulation:
     - Machine A: root `/tmp/.../repo_alice`, user `alice`, TZ `UTC`, `TMPDIR` `/tmp/alice_tmp`, jobs 4.
     - Machine B: root `/tmp/.../ci_build_bob`, user `bob`, TZ `Asia/Tokyo`, `TMPDIR` `/var/tmp/bob_temp`, jobs 16.
     - Compiles multi-package workspace from `axiom.lock` and compares SHA-256 digests of output executables, proving bit-for-bit identical outputs across environments.

## Verification

- `python build-snap-T877/tools/axtest.py --root build-snap-T877 --compiler "D:\projects\compiler\new lang\build\axiomc2.exe" --std-root "D:\projects\compiler\new lang\build-snap-T877\std" -j 1 conformance/p20/e20_6_sdk_toolchain_workspace` ->
  `TOTAL 16 PASS 16 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python tools/archcheck.py` -> 208 files scanned, 0 violations.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> requirements: 32308, gaps: 0 / COVERAGE OK.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> HARNESS OK.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T877` -> 0 REFUSED lines.

## Files changed

- tests/conformance/p20/e20_6_sdk_toolchain_workspace/README.md
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/axtoolchain_bundle_packager_and_distribution.ax
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/axtoolchain_bundle_packager_and_distribution.stdout
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/cross_target_declarative_sysroot_and_crt.ax
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/cross_target_declarative_sysroot_and_crt.stdout
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/e20_6_sdk_toolchain_workspace_oracle.py
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/e20_6_sdk_toolchain_workspace_oracle.test
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/e20_6_sdk_toolchain_workspace_probe.ax.in
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/lockfile_pinning_drift_and_tamper_defense.ax
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/lockfile_pinning_drift_and_tamper_defense.stdout
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/sdk_toolchain_cli_workflow_contract.ax
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/sdk_toolchain_cli_workflow_contract.stdout
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/two_machine_reproducible_workspace_build.ax
- tests/conformance/p20/e20_6_sdk_toolchain_workspace/two_machine_reproducible_workspace_build.stdout

## Status

STATUS: COMPLETE round=0