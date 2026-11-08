# T858 Report: E20.3 Canonical package registry protocol, .axpkg content-addressed archive, offline mirror & distribution runtime specification (SPEC-112)

STATUS: COMPLETE

## Summary

- Created `spec/SPEC-112-package-registry-distribution.md` defining the normative E20.3 package registry protocol, compile-time pre-build fetch boundary (`NetCap = Denied` during compilation), deterministic `.axpkg` binary container (`ArtifactHeader` `magic = "AXPKG001"`, sorted POSIX paths, zeroed timestamps `mtime = 0`, normalized `0644`/`0755` permissions, embedded `axiom.toml` + `.axmeta` summary, and binary `SHA-256` Merkle tree root/chunk verification), immutable published package versions, `Source`/`Binary`/`Hybrid` precompiled `.axmeta`/`.axmi` + `.axlib` package consumption, sparse static registry index (`AXPACKAGE_PROTOCOL_1`), multi-repository priority vs trust routing with `pinned_namespaces` dependency-confusion defense, offline repository mirrors, release channels, `.axupdate-journal` transactional generation rollback, and `axiomc pkg pack|publish|fetch|verify|search|mirror|install|rollback` CLI (`AXS-REG-001`..`AXS-REG-053`).
- Included Vietnamese `## Tóm tắt`, canonical Axiom positive/negative examples (`=` binding, `.` path syntax), diagnostic mappings (`AX_DRIVER_BAD_MANIFEST`, `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_AXLIB_PACKAGE_CONFLICT`), E20.3 implementation matrix (`T859`–`T861`), and `## Sources` covering `REQ-ECO-8736` and `REQ-PKG-024`.
- Updated `spec/INDEX.md` (§2 document list, §4 `AXS-REG-NNN` namespace, §5 topic table), `spec/diagnostics.md` (§3 `AXD-021`, §11 `AX_DRIVER_BAD_MANIFEST`, and `## Sources`), and `spec/invariants.md` (§1 group list, §53 `INV-REG-001`..`INV-REG-003` with `since: T859`..`T861`, and `## Sources`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T858`: verified all 4 changed files match `paths:` and `locks:` of `T858`

## Files changed

- spec/SPEC-112-package-registry-distribution.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
