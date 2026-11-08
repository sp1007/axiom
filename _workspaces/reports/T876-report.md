# T876 Report — E20.6 Hermetic multi-target SDK/sysroot & toolchain archive packager, axiom.lock SDK pinning & axiomc sdk/toolchain CLI

## Summary

Implemented task **T876** for Milestone **E20.6** (Phase `P20`), delivering the complete standard library and compiler implementation and test suite for the hermetic multi-target `.axsdk` and `.axtoolchain` archive packager, Merkle manifest verifier, offline installer, `axiom.lock` multi-target `SdkFingerprint` and `ToolchainFingerprint` pinning and drift rejection, and the `axiomc sdk` and `axiomc toolchain` CLI subcommand engine per `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` (`AXS-SDK-035`..`AXS-SDK-055`, `REQ-ECO-8736`, `REQ-PKG-022`, `INV-SDK-002`):

1. **Deterministic `.axsdk` and `.axtoolchain` Bundle Packager (`std/sdk/bundle/mod.ax`, `SPEC-116 §§4, 5`, `AXS-SDK-043`..`046`, `REQ-ECO-8736`)**:
   - Implemented `BundleArchive` and `BundleEntry` managing hermetic SDK sysroots (`.axsdk`) and toolchain distributions (`.axtoolchain`).
   - Implemented canonical lexicographical sorting of archive entries by path (`bundle_archive_finalize`), ensuring byte-identical tarball/archive determinism regardless of host filesystem directory traversal order.
   - Implemented deterministic Merkle tree root digest calculation (`bundle_archive_compute_merkle_root`), binding all contained target std `.axmeta`, `.lib`/`.a`, platform import stubs, target descriptors, and binaries.
   - Enforced strict archive entry safety (`validate_bundle_entry_safety`):
     - Path traversal rejection: denies entries containing `..`, absolute paths (leading `/`), and Windows drive letters (`C:\`), returning `BUNDLE_STATUS_PATH_TRAVERSAL`.
     - Zero mtime requirement per AXS-SDK-043 §2: denies non-zero timestamps (`mtime == 0`), returning `BUNDLE_STATUS_CORRUPT`.
     - Executable bit preservation per AXS-SDK-043 §3: enforces `0o755` for compiler and linker binaries under `bin/`, and `0o644` for header/stubs/data files.
     - Quota enforcement per REQ-PKG-022: limits maximum file size (512 MiB per entry) and entry count (8192 entries).
   - Implemented Ed25519 cryptographic bundle signature verification (`verify_bundle_signature`), certifying authoritativeness of official distributor signing keys and rejecting untrusted keys with canonical `BUNDLE_STATUS_SIGNATURE_INVALID`.

2. **Side-by-Side Isolated Toolchain Root & Offline Air-Gapped Installer (`std/sdk/bundle/mod.ax`, `SPEC-116 §5`, `AXS-SDK-045`, `046`, `REQ-ECO-8736`)**:
   - Implemented deterministic cache path formatting:
     - SDK sysroots: `<root>/sdks/<target_triple>/<version>-<merkle_hex>` (`format_sdk_install_cache_path`).
     - Toolchains: `<root>/toolchains/<toolchain_id>-<version>-<merkle_hex>` (`format_toolchain_install_cache_path`).
   - Enabled concurrent side-by-side installations across different targets and compiler versions without mutual interference or ambient host path pollution.
   - Implemented offline air-gapped mirror verification (`verify_offline_mirror_presence`): validates local availability of `.axsdk` archives under `--mirror <path>` or local cache before network access, failing with `BUNDLE_STATUS_OFFLINE_MISSING` if absent.

3. **Multi-Target `axiom.lock` Pinning & Drift Verification Engine (`std/sdk/bundle/mod.ax`, `SPEC-116 §4`, `AXS-SDK-037`..`039`, `REQ-PKG-022`, `INV-SDK-002`)**:
   - Implemented `SdkToolchainLockState`, `LockedSdkPin`, and `LockedToolchainPin` supporting multiple `[sdk."<triple>"]` tables and `[toolchain]` section serialization and deserialization.
   - Implemented `parse_sdk_toolchain_lock_state` parsing TOML tables with quotes and escaped characters.
   - Implemented `serialize_sdk_toolchain_lock_state` writing canonical sorted TOML blocks.
   - Implemented `pin_sdk_into_state` and `pin_toolchain_into_state` updating lockfile pins in-place or appending new target architectures.
   - Implemented `verify_locked_sdk_fingerprint` and `verify_locked_toolchain_fingerprint`:
     - Under `--locked` or `--frozen`, cross-validates active SDK/sysroot `SdkFingerprint` and active compiler `ToolchainFingerprint` against pinned hashes in `axiom.lock`.
     - Rejects any configuration drift, tampered archives, or missing target pins with canonical `BUNDLE_STATUS_LOCK_MISMATCH`.

4. **`axiomc sdk` & `axiomc toolchain` CLI Subcommand Engine (`compiler/driver/sdk_cmd/mod.ax`, `SPEC-116 §5`, `AXS-SDK-047`..`055`)**:
   - Implemented `SdkCmdOptions` and argument parser `parse_sdk_cmd_args` supporting `--available`, `--json`, `--all`, `--offline`, `--locked`, `--frozen`, `--mirror <dir>`, `-o`/`--output <file>`, `--target <triple>`, and `--key <key>`.
   - Subcommands provided:
     - `axiomc sdk list`: displays installed and catalog SDKs with version, tier, and status; supports `--json`.
     - `axiomc sdk install <target>[@<version>]`: validates target against registry, verifies offline mirror if `--offline`, computes isolated install cache path, and unpacks bundle; returns exit code 0 or 4 (`SDK_EXIT_IO_ERROR`).
     - `axiomc sdk verify`: verifies target SDK integrity, Merkle digest, and Ed25519 signatures; returns exit code 0, 2 (`SDK_EXIT_VERIFY_ERROR`), or 3 (`SDK_EXIT_SIGNATURE_ERROR`).
     - `axiomc sdk pack <dir> -o <bundle.axsdk>`: validates input sysroot hermeticity (`AX_SDK_HOST_FALLBACK_DENIED` on ambient paths), normalizes entries, calculates Merkle root, and outputs `.axsdk`.
     - `axiomc sdk pin`: parses active `axiom.lock`, updates target `SdkFingerprint` pin, and rewrites canonical lockfile text.
     - `axiomc toolchain list`: lists active and installed toolchain distributions; supports `--json`.
     - `axiomc toolchain info <toolchain_id>`: outputs toolchain metadata, host triple, and target matrices.
     - `axiomc toolchain verify`: verifies compiler binary and descriptor integrity against `ToolchainFingerprint`.
     - `axiomc toolchain pack <dir> -o <bundle.axtoolchain>`: packages toolchain files into `.axtoolchain`.
     - `execute_sdk_toolchain_locked_check`: unified `--locked` verification hook for compile/build driver pipeline.
   - Strictly enforced deterministic exit codes per `AXS-SDK-054`:
     - `0`: success (`SDK_EXIT_OK`).
     - `1`: usage or target resolution error (`SDK_EXIT_USAGE_ERROR`).
     - `2`: fingerprint or hash mismatch (`SDK_EXIT_VERIFY_ERROR`).
     - `3`: invalid cryptographic signature (`SDK_EXIT_SIGNATURE_ERROR`).
     - `4`: missing offline archive or IO failure (`SDK_EXIT_IO_ERROR`).
     - `5`: path traversal or security violation (`SDK_EXIT_SECURITY_ERROR`).

5. **Multi-Module Oracle Probe & Standalone Run Fixtures (`tests/run/sdk_toolchain_cli/`)**:
   - Developed `sdk_toolchain_cli.test` + `sdk_toolchain_cli_oracle.py` + `sdk_toolchain_cli_probe.ax.in` multi-module oracle test suite executing across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` verifying byte-identical output parity across all optimization tiers.
   - Authored standalone run fixtures:
     - `bundle_pack_install_offline.ax` + `.stdout`: Bundle entry sorting, Merkle root calculation, path traversal rejection, signature verification, cache path formatting, and offline mirror verification.
     - `lockfile_sdk_pinning_drift.ax` + `.stdout`: Multi-target SDK & toolchain lockfile state parsing, round-trip serialization, fingerprint verification, and drift/mismatch rejection.
     - `sdk_toolchain_cli_dispatch.ax` + `.stdout`: CLI argument parsing, subcommand execution, diagnostic reporting, and deterministic exit code evaluation.

## Verification

Executed full verification suite:
- `python tools/archcheck.py` -> 207 files scanned, 0 violations.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> requirements: 32308, gaps: 0 / COVERAGE OK.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> HARNESS OK.
- `python build-snap-T876/tools/axtest.py --root build-snap-T876 --compiler build/axiomc2.exe --std-root std -j 1 --exclude-requires axiom0-internal run/sdk_toolchain_cli` ->
  `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0` (`0 WEAK-NATIVE`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T876` -> snapshot refreshed with 11 changed files.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T876` -> 0 REFUSED lines.

## Files changed

- compiler/driver/sdk_cmd/mod.ax
- std/sdk/bundle/mod.ax
- tests/run/sdk_toolchain_cli/bundle_pack_install_offline.ax
- tests/run/sdk_toolchain_cli/bundle_pack_install_offline.stdout
- tests/run/sdk_toolchain_cli/lockfile_sdk_pinning_drift.ax
- tests/run/sdk_toolchain_cli/lockfile_sdk_pinning_drift.stdout
- tests/run/sdk_toolchain_cli/sdk_toolchain_cli.test
- tests/run/sdk_toolchain_cli/sdk_toolchain_cli_dispatch.ax
- tests/run/sdk_toolchain_cli/sdk_toolchain_cli_dispatch.stdout
- tests/run/sdk_toolchain_cli/sdk_toolchain_cli_oracle.py
- tests/run/sdk_toolchain_cli/sdk_toolchain_cli_probe.ax.in

## Status

STATUS: COMPLETE round=0
