# T859 Report: E20.3 Deterministic .axpkg archive packer/unpacker, Merkle content verifier & sparse/local registry repository client

STATUS: COMPLETE

## Summary

Implemented canonical deterministic `.axpkg` archive packing/unpacking, SHA-256 Merkle tree content verification, sparse index client operations, registry publication immutability enforcement, offline-first cache lookup, and transactional package installation with journaling and rollback per `spec/SPEC-112-package-registry-distribution.md` (`AXS-REG-010`..`013`, `AXS-REG-030`..`034`, `REQ-ECO-8736`, `REQ-PKG-024`, `INV-REG-001`, `INV-DET-001`).

Key deliverables and architectural implementations:

1. **`std/pkg/archive/mod.ax`**:
   - Deterministic binary container schema (`SPEC-24 AXS-ART-002..004`, `SPEC-112 AXS-REG-010`) packing an 88-byte `ArtifactHeader`, sorted 48-byte `SectionDescriptor` table, and aligned section payloads (`SECTION_MANIFEST`, `SECTION_INTERFACE_SUMMARY`, `SECTION_MERKLE_INDEX`, `SECTION_PROVENANCE`, `SECTION_PAYLOAD_BLOBS`).
   - Strict lexicographical ordering of entries by normalized relative POSIX paths (`memcmp`).
   - Strict path safety validation rejecting path traversal (`..`, `.`), absolute paths, Windows drive letters (`C:`), control characters, and case collisions under ASCII lowercase (`AXS-REG-011`, `AXS-REG-013`).
   - Deterministic zeroed metadata: normalized file modes (`0` for regular, `1` for executable), `mtime_sec = 0`, `mtime_nsec = 0`, `uid = 0`, `gid = 0`.
   - Full cryptographic FIPS 180-4 standard SHA-256 engine implemented in pure Axiom.
   - Chunked 64 KiB payload hashing (`AXPKG-CHUNK-v1\0`), leaf hashes (`AXPKG-LEAF-v1\0`), balanced Merkle node reduction (`AXPKG-NODE-v1\0`), and package root calculation (`AXPKG-ROOT-v1\0` binding manifest and interface digests).
   - Decompression and archive quota defense enforcing `max_archive_size = 64 MiB`, `max_uncompressed_total = 256 MiB`, and `max_single_file_size = 64 MiB`.
   - Bit-level tamper detection rejecting modified archive payloads or corrupted Merkle roots with `ARCHIVE_STATUS_MERKLE_MISMATCH`.

2. **`std/pkg/registry/mod.ax`**:
   - Sparse index relative path formatting (`index/<ns>/<p2>/<name>.jsonl`) and content-addressed blob paths (`blobs/sha256/xx/yy/<hash>.axpkg`).
   - Streaming JSON line serialization and deserialization for package release records (`version`, `sha256`, `merkle_root`, `channel`, `yanked`, `quarantine`).
   - Query engine supporting release channel selection (`stable`, `beta`, `nightly`), skipping yanked versions, and rejecting quarantined releases.
   - Immutability enforcement (`AXS-REG-031`, `INV-REG-001`): idempotent republishing of bit-identical artifacts succeeds (`REG_STATUS_ALREADY_PUBLISHED_IDENTICAL`), while attempts to overwrite an existing version with differing content are rejected with `REG_STATUS_IMMUTABLE_VERSION_EXISTS`.
   - Local directory repository client and offline-first cache lookup (`offline_cache/blobs/sha256/...`).
   - Transactional package installation state machine (`RegistryStore`) tracking active/staged transactions, writing `.axupdate-journal` state, and executing atomic generation commits or clean rollbacks upon extraction or verification failure (`REQ-PKG-024`).

3. **`tests/run/pkg_registry/`**:
   - `pkg_registry.test`: Test manifest driving the multi-module oracle.
   - `pkg_registry_oracle.py`: Multi-tier bundling runner testing compiled modules and probe runner across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with exact byte-identical stdout parity.
   - `pkg_registry_probe.ax.in`: Multi-module probe testing end-to-end archive packing/unpacking/tampering, sparse index queries, immutability, offline paths, and transactional rollback.
   - `archive_deterministic_and_merkle.ax` & `.stdout`: Standalone fixture testing Merkle mathematics, path normalization, and bit tampering.
   - `registry_sparse_and_immutable.ax` & `.stdout`: Standalone fixture testing sparse index parsing, query resolution, and publication immutability.
   - `transactional_rollback_and_journal.ax` & `.stdout`: Standalone fixture testing journal staging, rollback, and generation advancement.

## Verification

- `python build-snap-T859/tools/axtest.py --root build-snap-T859 --compiler build/axiomc2.exe --std-root "D:/projects/compiler/new lang/build-snap-T859/std" -j 1 --exclude-requires axiom0-internal run/pkg_registry`:
  - `WEAK-NATIVE 0`
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`
- `python build-snap-T859/tests/run/pkg_registry/pkg_registry_oracle.py build/axiomc2.exe build tmp build-snap-T859`:
  - `PKG-REGISTRY-ENGINE-OK` (passes `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, `-O2 --verify-each` with byte-identical stdout)
- `python tools/archcheck.py`:
  - `archcheck: 207 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`:
  - `requirements: 32308, gaps: 0 COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`:
  - `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T859`:
  - Verified 0 unlisted changes and 0 refused lines.

## Files changed

- std/pkg/archive/mod.ax
- std/pkg/registry/mod.ax
- tests/run/pkg_registry/archive_deterministic_and_merkle.ax
- tests/run/pkg_registry/archive_deterministic_and_merkle.stdout
- tests/run/pkg_registry/pkg_registry.test
- tests/run/pkg_registry/pkg_registry_oracle.py
- tests/run/pkg_registry/pkg_registry_probe.ax.in
- tests/run/pkg_registry/registry_sparse_and_immutable.ax
- tests/run/pkg_registry/registry_sparse_and_immutable.stdout
- tests/run/pkg_registry/transactional_rollback_and_journal.ax
- tests/run/pkg_registry/transactional_rollback_and_journal.stdout

STATUS: COMPLETE round=0