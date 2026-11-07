STATUS: COMPLETE round=0

# T766 Implementation Report — E18.4: Axiom object/LTO/semantic package container sections & schema-versioned reader/writer

## Summary

Implemented the schema-versioned Axiom object/LTO/semantic package container writer and fail-closed reader (`compiler/artifact/container/mod.ax`) and verification suite (`tests/run/artifact_container/`) per `SPEC-24` (`AXS-ART-001..005`, `AXS-ART-020..024`, `AXS-ART-050..053`, `INV-ART-001`, `INV-ART-002`) and `SPEC-25` (`REQ-LNK-465..477`, `REQ-LNK-538..541`).

1. **Non-Alloc Discardable COFF `.obj` & `.lib` Container Sections (`AXS-ART-020..021`, `REQ-LNK-475..476`)**:
   - Implemented deterministic COFF `.obj` emission (`container_write_coff_obj_ex`, `container_write_axiom_coff_obj`, `container_write_foreign_coff_obj`) embedding non-alloc discardable (`IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE | IMAGE_SCN_MEM_READ` = `0x42000200`) `.axmeta`, `.axlto`, and `.axmir` container sections with 8-byte aligned payloads and zeroed timestamps (`INV-ART-001`).
   - Implemented `.axmeta` (`"AXMETA01"`, `format_family = 4`, `artifact_kind = 4`), `.axlto` (`"AXLTO001"`, `format_family = 3`, `artifact_kind = 3`), `.axmir` (`"AXMIR001"`, `format_family = 2`, `artifact_kind = 2`), and `.axpkg` (`"AXPKG001"`, `format_family = 6`, `artifact_kind = 6`) container serializers and readers with canonical `SemanticKey` sorting (`AxLtoFnEntry`, `AxLtoCallEdge`, `AxLtoMirBody`), `InterfaceFingerprint` / `AbiFingerprint` / `TargetFingerprint` binding, and 128-bit BLAKE3-128 section & top-level content hashes.
   - Implemented COFF `.lib` static archive (`!<arch>\n`) writer and reader (`container_write_coff_archive_begin`, `container_write_coff_archive_add_member`, `container_extract_coff_archive`) supporting mixed archives of Axiom `.obj` members and foreign C `.obj` members (`REQ-LNK-476`).

2. **Schema-Versioned Fail-Closed Validation & Deterministic Diagnostics (`AXS-ART-005`, `AXS-ART-023..024`, `AXS-ART-050..053`)**:
   - Implemented fail-closed validation in `axmeta_deserialize`, `axlto_deserialize`, `axmir_deserialize`, `container_extract_coff_obj`, `container_extract_coff_archive`, and `axpkg_deserialize` emitting deterministic `AX_ART_*` and canonical `AX_LINK_*` diagnostics (`container_emit_diag`):
     - `AX_ART_CORRUPT_HEADER` (`AX_LINK_BAD_ARTIFACT`) on truncated buffers, corrupted magic numbers, out-of-bounds COFF `PointerToRawData`/`SizeOfRawData` or archive member headers, executable/writable container section flags, `.axlto`/`.axmir` without `.axmeta` (`AXS-ART-020`), or unverified MIR bodies (`ownership_verified == false`, `AXS-ART-024` / `INV-PIPE-002`).
     - `AX_ART_VERSION_MISMATCH` (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH`) on `schema_version != AXMI_FORMAT_VERSION`, unsupported `mir_schema_version`, or unknown mandatory sections (`(flags & AXMI_SEC_FLAG_OPTIONAL) == 0`), while safely skipping unknown sections marked `AXMI_SEC_FLAG_OPTIONAL`.
     - `AX_ART_TARGET_MISMATCH` (`AX_LINK_ARTIFACT_TARGET_MISMATCH`) on target triple, ABI profile, pointer width, endianness, CPU feature mask, or panic strategy mismatches, as well as cross-module dependency fingerprint drift (`AXS-ART-023`).
     - `AX_ART_CHECKSUM_MISMATCH` (`AX_LINK_BAD_ARTIFACT`) on top-level `content_hash`, per-section `checksum`, or intra-object `.axmeta`/`.axlto` `InterfaceFingerprint` drift.

3. **Link-Time LTO Consumption & Final PE32+ `.exe` / `.dll` Container Section Stripping (`AXS-ART-021..022`, `INV-ART-002`)**:
   - Implemented `ContainerLinkSession` (`container_link_add_coff_obj`, `container_link_add_coff_archive`, `container_link_finalize_pe_image`) to verify cross-module `InterfaceFingerprint` / `AbiFingerprint` dependencies, consume `.axlto` function/call-graph summaries and Verified MIR bodies (dead-stripping unreachable internal functions and identifying cross-module inline candidates), and strip all non-runtime `.axmeta`, `.axlto`, and `.axmir` sections when emitting final PE32+ `.exe` and `.dll` images (`INV-ART-002`).
   - Implemented `container_verify_pe_stripped` / `container_verify_pe_image_stripped` and deterministic `inspect --artifact-sections` dump helpers (`container_inspect_obj_dump`, `container_inspect_pe_link_dump`, `container_inspect_archive_dump`, `container_inspect_pkg_dump`).

## Files changed

- compiler/artifact/container/mod.ax
- tests/run/artifact_container/artifact_container_engine.test
- tests/run/artifact_container/artifact_container_oracle.py
- tests/run/artifact_container/artifact_container_probe.ax.in
- tests/run/artifact_container/container_archive_foreign_and_bounds_seam.ax
- tests/run/artifact_container/container_archive_foreign_and_bounds_seam.stdout
- tests/run/artifact_container/container_coff_embed_and_roundtrip.ax
- tests/run/artifact_container/container_coff_embed_and_roundtrip.stdout
- tests/run/artifact_container/container_fail_closed_validation.ax
- tests/run/artifact_container/container_fail_closed_validation.stdout
- tests/run/artifact_container/container_lto_mir_and_exe_strip.ax
- tests/run/artifact_container/container_lto_mir_and_exe_strip.stdout

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T766`
- `python tools/axtest.py -j 1 --build-dir build-snap-T766 run/artifact_container run/axmi_format run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 20 PASS 20 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T766` -> `0 REFUSED`

STATUS: COMPLETE round=0
