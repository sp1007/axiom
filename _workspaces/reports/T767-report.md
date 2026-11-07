STATUS: COMPLETE round=0

# T767 Report — E18.4: Artifact format, module interface (`.axmi`) & LTO section round-trip conformance suite

## Summary

Implemented the Phase 18 E18.4 artifact format, `.axmi` module interface, and embedded `.axmeta`/`.axir`/`.axmap` LTO container round-trip conformance suite in `tests/conformance/p18/e18_4_artifacts/` per `SPEC-24` (`AXS-ART-001..005`, `AXS-ART-010..053`, `INV-ART-001..003`).

1. **Multi-Module Compilation via `.axmi` & `.axmeta` across Generics, Traits, Capabilities & `const` Items (`multimodule_axmi_axmeta_generics_traits_caps_consts.ax`, `e18_4_artifacts_oracle.test`)**:
   - Exercises a 3-module dependency chain (`core_math` -> `algo_lib` -> `app_main`) exporting public constants, type layouts (`Vec2`, `SpanHdr`, `Pair`), trait bounds and implementations (`Scale`, `Accumulate`), ownership/borrowing/capability/effect contracts (`view`/`mut_view`, `CapLog`, `CapAlloc`, `IO | Alloc`, non-escaping borrow masks, return borrow sources), and verified generic MIR templates (`scale_pair<T: Scale>`, `clamp_span<T>`, `fold_step<T: Accumulate>`).
   - Verifies source-free downstream compilation using `axmi_populate_compiler_db` (`0` upstream `.ax` source parses/queries on downstream build) as well as real `axiomc2` CLI multi-module compilation (`--emit=obj --emit=axmi` followed by downstream linking with upstream `.ax` deleted from disk) and `--inspect-axmi` structural dump verification.

2. **Byte-Identical `.axmi` / `.obj` / `.axpkg` Emission & LTO Round-Trip (`byte_identical_axmi_obj_and_lto_roundtrip.ax`, `e18_4_artifacts_probe.ax.in`)**:
   - Proves byte-for-byte identical binary emission across repeated runs and under permuted declaration insertion orders (`INV-ART-001`).
   - Exercises COFF `.obj` (`.axmeta`, `.axir`, `.axmap`) and standalone `.axpkg` round-trip serialization, LTO cross-module generic instantiation and inlining, dead internal helper elimination, and final executable stripping (`pe_clean_verified == true`).

3. **Fail-Closed Negative Diagnostics (`negative_diag_version_target_and_corrupt_payloads.ax`, `e18_4_artifacts_probe.ax.in`)**:
   - Covers `.axmi` magic corruption (`AX_ART_CORRUPT_HEADER` / `AX_LINK_BAD_ARTIFACT`), major/minor schema version mismatch (`AX_ART_VERSION_MISMATCH` / `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`), unknown required vs. optional section flags (`AXS-ART-005`), target triple/ABI/pointer-width/feature-mask/panic-strategy mismatches (`AX_ART_TARGET_MISMATCH` / `AX_LINK_ARTIFACT_TARGET_MISMATCH`), payload bit-flip checksum failures (`AX_ART_CHECKSUM_MISMATCH` / `AX_LINK_BAD_ARTIFACT`), truncated section payloads, and unverified generic MIR rejection (`INV-PIPE-002`).
   - Covers COFF `.obj` and `.axpkg` container negative diagnostics (`AX_CONT_CORRUPT_COFF`, `AX_CONT_MISSING_AXMETA`, `AX_CONT_SCHEMA_MISMATCH`, `AX_CONT_TARGET_MISMATCH`, `AX_CONT_CHECKSUM_MISMATCH`, `AX_CONT_AXIR_MISMATCH`, `AX_CONT_UNVERIFIED_MIR`, `AX_CONT_CORRUPT_PACKAGE`).

4. **Cross-Module Freshness Invalidation & Mixed Foreign C/C++ Archive Seam (`cross_module_freshness_invalidation_and_archive_seam.ax`, `e18_4_artifacts_probe.ax.in`)**:
   - Verifies early-cutoff preservation (`AX_FRESH_VALID`) when upstream private function bodies change without altering `.axmi` interface fingerprints, and targeted invalidation (`AX_FRESH_STALE_IFACE`, `AX_FRESH_MISSING_ARTIFACT`, `AX_FRESH_CORRUPT_ARTIFACT`, `AX_FRESH_TARGET_MISMATCH`) when public signatures, type layouts, `pub const` values, capability masks, or generic MIR templates change.
   - Verifies mixed COFF `!<arch>\n` `.lib`/`.a` static archive extraction (`coff_archive_extract`) separating Axiom `.obj` members with `.axmeta`/`.axir` from foreign C/C++ `.obj` members that pass straight through to the native linker while enforcing `extern "C"` capability boundaries.

## Files changed

- `tests/conformance/p18/e18_4_artifacts/byte_identical_axmi_obj_and_lto_roundtrip.ax`
- `tests/conformance/p18/e18_4_artifacts/byte_identical_axmi_obj_and_lto_roundtrip.stdout`
- `tests/conformance/p18/e18_4_artifacts/cross_module_freshness_invalidation_and_archive_seam.ax`
- `tests/conformance/p18/e18_4_artifacts/cross_module_freshness_invalidation_and_archive_seam.stdout`
- `tests/conformance/p18/e18_4_artifacts/e18_4_artifacts_oracle.py`
- `tests/conformance/p18/e18_4_artifacts/e18_4_artifacts_oracle.test`
- `tests/conformance/p18/e18_4_artifacts/e18_4_artifacts_probe.ax.in`
- `tests/conformance/p18/e18_4_artifacts/multimodule_axmi_axmeta_generics_traits_caps_consts.ax`
- `tests/conformance/p18/e18_4_artifacts/multimodule_axmi_axmeta_generics_traits_caps_consts.stdout`
- `tests/conformance/p18/e18_4_artifacts/negative_diag_version_target_and_corrupt_payloads.ax`
- `tests/conformance/p18/e18_4_artifacts/negative_diag_version_target_and_corrupt_payloads.stdout`

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T767`
- `python build-snap-T767/tools/axtest.py -j 1 --root build-snap-T767 --build-dir build-snap-T767/build --compiler build-snap-T767/build/axiomc2.exe conformance/p18/e18_4_artifacts run/artifact_container run/axmi_format run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 33 PASS 33 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T767` -> `0 REFUSED`

STATUS: COMPLETE round=0
