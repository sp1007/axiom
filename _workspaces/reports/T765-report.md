# T765 Implementation Report — E18.4: Module interface metadata (`.axmi`) serializer, loader & exported symbol/generic summaries

## Summary

Implemented the canonical binary `.axmi` (Axiom Module Interface) serializer, fail-closed loader/validator, exported symbol/type/trait/ownership/capability/effect/const/generic-MIR summary tables, source-free `CompilerDB` integration, and deterministic `inspect --axmi` / `--emit=axmi` dump engine in `compiler/artifact/axmi/mod.ax` per `SPEC-24` (`AXS-ART-001..005`, `AXS-ART-010..014`, `AXS-ART-050..053`, `INV-ART-001`) and `SPEC-21` (`AXS-QRY-004`, `AXS-QRY-013`).

1. **Binary `.axmi` Format Header & Section Directory (`AXS-ART-001..004`, `INV-ART-001`)**:
   - Implemented the 64-byte little-endian `AxmiHeader` (`AXMI_MAGIC = "AXMI0001"`, `format_family = 1`, `AXMI_FORMAT_VERSION = 1`, `artifact_kind = AXMI_KIND_MODULE_INTERFACE`, `flags = AXMI_FLAG_LITTLE_ENDIAN | AXMI_FLAG_DETERMINISTIC`, `target_fingerprint_lo`, `interface_fingerprint_lo`, `section_count`, `producer_version`, `payload_offset`, `payload_size`, 128-bit `header_checksum`) and 48-byte `AxmiSectionDesc` entries (`id`, `section_type`, `flags`, `alignment`, `offset`, `size`, `uncompressed_size`, 128-bit `checksum`).
   - Enforced canonical section ordering across all 8 `.axmi` sections (`Strings`, `Symbols`, `Types`, `Traits`, `TypesLayout`, `ConstValues`, `GenericMir`, `EffectsCapabilities`) and canonical `SemanticKey` insertion sorting across all exported tables so serialization is 100% deterministic and allocation-order-independent (`INV-ART-001`).
   - Stripped module-private declarations that are not transitively referenced by public signatures, public layouts, `pub const` evaluations, or generic/inlineable MIR templates (`REQ-LNK-540`).

2. **Fail-Closed Deserialization & Unknown-Section Forward Compatibility (`AXS-ART-005`)**:
   - Implemented `axmi_deserialize` with strict fail-closed verification returning both fine-grained `AX_ART_*` status codes and canonical `SPEC-25` `AX_LINK_*` diagnostics:
     - `AX_ART_CORRUPT_HEADER` (`AX_LINK_BAD_ARTIFACT`) on truncated buffers, bad magic bytes, out-of-bounds or overlapping sections, unaligned section offsets, or header checksum mismatch.
     - `AX_ART_VERSION_MISMATCH` (`AX_LINK_ARTIFACT_SCHEMA_MISMATCH`) on `schema_version != AXMI_FORMAT_VERSION`, unsupported `GenericMir` schema version, or unknown non-optional section types (`(flags & AXMI_SEC_FLAG_OPTIONAL) == 0`), while safely skipping unknown sections marked `AXMI_SEC_FLAG_OPTIONAL`.
     - `AX_ART_TARGET_MISMATCH` (`AX_LINK_ARTIFACT_TARGET_MISMATCH`) when the serialized target triple, ABI, pointer width, endianness, feature mask, or panic strategy conflicts with the active compilation session.
     - `AX_ART_CHECKSUM_MISMATCH` (`AX_LINK_BAD_ARTIFACT`) when any section payload checksum fails verification.

3. **Exported Semantic & ABI Tables, Ownership/Capability Contracts & Verified MIR Templates (`AXS-ART-010..014`)**:
   - Implemented `AxmiExportSymbol`, `AxmiExportTypeDef`, `AxmiTraitImplSummary`, `AxmiFnContract` (per-parameter `move`/`copy`/`view`/`mut_view` passing modes, `return_borrows_from_mask`, `no_escape_mask`, `effect_mask`, `capability_mask`, `panic_contract`), `AxmiConstValue`, and `AxmiMirTemplate` (requiring `ownership_verified == true` per `INV-PIPE-002`).
   - Implemented `axmi_populate_compiler_db` to seed downstream `CompilerDB` instances (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `layout_of`, `trait_solve`, `effect_summary`, `const_eval`, `mir_body`) directly from `.axmi` without reading or parsing upstream `.ax` source files (`0` provider executions on downstream queries).
   - Implemented `axmi_instantiate_generic_mir` for cross-module generic instantiation with trait bound coherence checking, `axmi_diff_interfaces` / `axmi_check_freshness` for early-cutoff verification (`Fresh` on private body edits, `Stale` on public signature/layout/const edits), and `axmi_inspect_dump` (`inspect --axmi`).

## Files changed

- `compiler/artifact/axmi/mod.ax`
- `tests/run/artifact_axmi/artifact_axmi_engine.test`
- `tests/run/artifact_axmi/artifact_axmi_oracle.py`
- `tests/run/artifact_axmi/artifact_axmi_probe.ax.in`
- `tests/run/artifact_axmi/axmi_fail_closed_validation.ax`
- `tests/run/artifact_axmi/axmi_fail_closed_validation.stdout`
- `tests/run/artifact_axmi/axmi_generic_inline_and_cap_contracts.ax`
- `tests/run/artifact_axmi/axmi_generic_inline_and_cap_contracts.stdout`
- `tests/run/artifact_axmi/axmi_roundtrip_and_source_free_import.ax`
- `tests/run/artifact_axmi/axmi_roundtrip_and_source_free_import.stdout`

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T765`
- `python build-snap-T765/tools/axtest.py --root build-snap-T765 --build-dir build-snap-T765/build -j 1 run/artifact_axmi run/query_db run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 27 PASS 27 FAIL 0 SKIP 0 XFAIL 0`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T765` -> `0 REFUSED`
- `python build-snap-T765/tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`

STATUS: COMPLETE round=0
