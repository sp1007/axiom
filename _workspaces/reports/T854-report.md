# T854 Report: E20.2 Canonical AXPACKAGE package manager, deterministic SemVer resolver, feature unification & axiom.lock specification (SPEC-111)

STATUS: COMPLETE

## Summary

- Created `spec/SPEC-111-package-manager-resolution-lockfiles.md` defining the normative E20.2 `AXPACKAGE` package manager, deterministic SemVer 2.0 PubGrub constraint solver, side-by-side major-version isolation, monotonic host/target feature unification, canonical `axiom.lock` v1 lockfile format, content-addressed `SHA-256` store, offline/air-gapped `vendor/` materialization, and `axiomc pkg` CLI subcommands (`AXS-PKG-001`..`AXS-PKG-053`).
- Included Vietnamese `## Tóm tắt`, canonical Axiom positive/negative examples (`=` binding, `.` path syntax), diagnostic mappings (`AX_DRIVER_BAD_MANIFEST`, `AX_TYPE_MISMATCH`, `AX_LINK_AXLIB_PACKAGE_CONFLICT`, `AX_IO_*`), E20.2 implementation matrix (`T855`–`T857`), and `## Sources` covering `REQ-ECO-8736`, `REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, and `REQ-PKG-001`..`REQ-PKG-023`.
- Updated `spec/INDEX.md` (§2 document list, §4 `AXS-PKG-NNN` namespace, §5 topic table), `spec/diagnostics.md` (§3 `AXD-021`, §11 `AX_DRIVER_BAD_MANIFEST`, and `## Sources`), and `spec/invariants.md` (§1 group list, §52 `INV-PKG-001`..`INV-PKG-003`, and `## Sources`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T854`: verified all changed files match `paths:` and `locks:` of `T854`

## Files changed

- spec/SPEC-111-package-manager-resolution-lockfiles.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
