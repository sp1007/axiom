# T856 Report: E20.2 Canonical axiom.lock serializer/verifier, content-addressed package store, offline vendoring & axiomc pkg CLI

STATUS: COMPLETE

## Summary

Implemented canonical `axiom.lock` v1 serialization/verification, content-addressed package store caching, air-gapped offline vendoring, and the `axiomc pkg` subcommand engine per `spec/SPEC-111-package-manager-resolution-lockfiles.md` (`AXS-PKG-030`..`033`, `AXS-PKG-040`, `AXS-PKG-050`, `REQ-ECO-8736`, `REQ-PKG-013`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `INV-PKG-002`).

Key deliverables and architectural implementations:
1. **`std/pkg/lockfile/mod.ax`**:
   - Canonical `axiom.lock` v1 parser and serializer with deterministic lexicographical entry sorting (`(namespace, name, version, source, env)` with SemVer 2.0 total ordering).
   - Exact source coordinates formatting (`registry:default`, `git:url#commit`, `workspace:path`, `path:relative_path`).
   - Content digest calculation using 256-bit hashing (`LockDigest256` / `sha256:` prefix format).
   - Unified target and host feature deduplication and sorting.
   - `sdk_fingerprint` toolchain pin field support (`AXS-PKG-030 §3`).
   - `--locked` drift detection against resolved graph nodes (`verify_lockfile_drift_against_nodes`), rejecting graph size mismatches, version drifts, missing entries, and source changes with `AX_PKG_LOCKFILE_DRIFT` diagnostics (`AXS-PKG-031 §1`).
   - Zero-copy string view (`LockStrView`) and dynamically growing buffer (`LockBuffer`) adhering to ABI 256-byte limits.

2. **`std/pkg/store/mod.ax`**:
   - SHA-256 content-addressed local package cache engine formatting deterministic cache paths: `.axiom/cache/pkg/sha256/<b0>/<b1>/<full_hash>/` (`AXS-PKG-032 §1`).
   - Pre-use digest verification (`verify_package_content_sha256`) rejecting mismatched, corrupted, or tampered tarball payloads with `STORE_STATUS_HASH_MISMATCH` (`AXS-PKG-032 §2`).
   - Sandboxed extraction verification (`check_archive_entry_safety`) rejecting directory traversal attacks (absolute paths `/...`, `C:\...`, parent directory escapes `../`, and illegal characters) with `STORE_STATUS_PATH_TRAVERSAL` (`AXS-PKG-032 §3`).
   - Decompression quota enforcement (`check_archive_quotas`) defending against compression bombs (max compressed 50MB, max uncompressed 500MB, max expansion ratio 100:1, max 10,000 files) with `STORE_STATUS_QUOTA_EXCEEDED` (`tasks/1065 §115`).
   - Offline `vendor/` directory materialization and manifest generation (`serialize_vendor_manifest`) emitting checksums and package origins (`AXS-PKG-033 §1`).
   - Air-gapped verification (`verify_offline_vendor_coverage`) rejecting network requests in `--offline` mode when packages are missing from `vendor/` (`AXS-PKG-033 §2`).

3. **`compiler/driver/pkg_cmd/mod.ax`**:
   - Subcommand argument parser and CLI engine for `axiomc pkg` subcommands: `init`, `add`, `remove`, `update`, `lock`, `tree`, `verify-lock`, and `vendor` (`AXS-PKG-040`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `REQ-ECO-8736`).
   - `init`: Generates canonical `axiom.toml` manifests and default source templates for binary (`src/main.ax`) and library (`src/lib.ax`) packages, rejecting pre-existing project directories.
   - `add`: Parses coordinate specifications (`[<registry>/]<name>[@<constraint>]`), validates SemVer constraints, and updates manifest dependencies.
   - `remove`: Strips specified dependency entries from manifest files.
   - `update`: Triggers dependency graph re-resolution and updates lockfile entries.
   - `lock`: Serializes canonical `axiom.lock` from the resolved package graph.
   - `tree`: Renders formatted dependency hierarchy trees (`render_pkg_tree_text`) supporting `--depth` and `--duplicates` filters.
   - `verify-lock`: Validates lockfile integrity, checks SHA-256 hashes, and detects dependency graph drift under `--locked`.
   - `vendor`: Materializes the air-gapped `vendor/` directory and creates `vendor/modules.txt`.

4. **`tests/run/pkg_lockfile/`**:
   - `pkg_lockfile.test`: Multi-tier test manifest running `pkg_lockfile_oracle.py`.
   - `pkg_lockfile_oracle.py`: Selfhost bundling oracle testing compiled modules and probe runner across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with exact byte-identical stdout parity.
   - `pkg_lockfile_probe.ax.in`: Direct multi-module probe exercising lockfile serialization/tampering/drift, content cache paths/hash verification/sandbox traversal/quotas, and CLI command execution.
   - `lockfile_canonical_and_drift.ax`: Standalone fixture testing deterministic sorting and drift detection (`3/3 modes PASS`).
   - `store_sha256_cache_and_sandbox.ax`: Standalone fixture testing content-addressed storage and archive safety (`3/3 modes PASS`).
   - `offline_vendor_and_cli_engine.ax`: Standalone fixture testing vendoring and CLI subcommands (`3/3 modes PASS`).

## Verification

- `python build-snap-T856/tools/axtest.py --root build-snap-T856 --compiler build/axiomc2.exe --std-root std -j 1 --exclude-requires axiom0-internal run/pkg_lockfile`:
  - `WEAK-NATIVE 0`
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`
- `python tests/run/pkg_lockfile/pkg_lockfile_oracle.py build/axiomc2.exe build build-snap-T856/tmp build-snap-T856`:
  - `PKG-LOCKFILE-ENGINE-OK` (passes `--interp`, `-O0`, `-O1`, `-O2 --verify-each`)
- `python tools/archcheck.py`:
  - `archcheck: 204 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`:
  - `requirements: 32308, gaps: 0 COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`:
  - `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T856`:
  - Verified 0 unlisted changes and 0 refused lines.

## Files changed

- compiler/driver/pkg_cmd/mod.ax
- std/pkg/lockfile/mod.ax
- std/pkg/store/mod.ax
- tests/run/pkg_lockfile/lockfile_canonical_and_drift.ax
- tests/run/pkg_lockfile/lockfile_canonical_and_drift.stdout
- tests/run/pkg_lockfile/offline_vendor_and_cli_engine.ax
- tests/run/pkg_lockfile/offline_vendor_and_cli_engine.stdout
- tests/run/pkg_lockfile/pkg_lockfile.test
- tests/run/pkg_lockfile/pkg_lockfile_oracle.py
- tests/run/pkg_lockfile/pkg_lockfile_probe.ax.in
- tests/run/pkg_lockfile/store_sha256_cache_and_sandbox.ax
- tests/run/pkg_lockfile/store_sha256_cache_and_sandbox.stdout

STATUS: COMPLETE round=0