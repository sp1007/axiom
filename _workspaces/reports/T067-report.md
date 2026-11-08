STATUS: COMPLETE round=0

# T067 — E18.6: Linker v2: separate compilation, multiple objects, archives

## Summary

Implemented `SPEC-27` (`E18.6 — Linker v2: separate compilation, multiple objects, archives`) across `compiler/link/`, `compiler/driver/`, and `tests/link2/`:

1. **Multi-module separate `.obj` emission & `LinkIR` pipeline (`SPEC-27` §3, §4, §10)**:
   - Added `pipe_build_separate_modules_pe64`, `driver_emit_objmodel_filtered_ex`, `driver_emit_coff_obj_filtered_ex`, and `driver_link_objects_pe64_ex` in `compiler/driver/pipeline.ax` (`compiler/driver/opts.ax`, `compiler/driver/mod.ax`).
   - Multi-module native builds emit one deterministic COFF `.obj` per non-std project module (`--emit-obj-dir <dir>` optionally persists the per-module `.obj` files and `axiom_rt.obj`) and feed the ordered object + `.lib` archive list into the `LinkIR` v2 linker (`pe_link_coff_objects_to_pe64_v2`).
   - Internal compiler temporaries, string literal pools, and anonymous constant tables (`.L*`) are emitted with `SYM_LOCAL` (`IMAGE_SYM_CLASS_STATIC`) linkage and intra-object local references bind directly to the local definition (`SPEC-27` §5.2).
   - Emits the discardable `.axmeta` COFF metadata section (`AXMETA\x00\x01`) carrying symbol binding (`Strong`/`Weak`), ABI kind (`Func`/`Data`), calling convention (`Win64`/`C`/`System`), parameter count, return size, demangled Axiom item path, source `FileId`/span, and formatted signature for structured cross-object diagnostics.

2. **Global symbol table merging, archive demand extraction, & cross-module relocations (`SPEC-27` §5, §6, §8, §9)**:
   - Implemented `LinkV2Context`, `linker_load_coff_object_v2`, `linker_resolve_coff_archive_v2`, and `pe_link_coff_objects_to_pe64_v2` in `compiler/link/linker.ax`, `compiler/link/pe.ax`, and `compiler/link/mod.ax`.
   - Enforces `Strong > Weak > Local` symbol precedence (`AXS-LNK-010..014`) across multiple `.obj` inputs and demand-loaded `.lib` archive members (fixed-point archive member extraction until no newly satisfied undefined symbols remain).
   - Resolves cross-module relocations (`IMAGE_REL_AMD64_ADDR64`, `IMAGE_REL_AMD64_REL32`, `IMAGE_REL_AMD64_ADDR32NB`, `IMAGE_REL_AMD64_SECTION`, and `IMAGE_REL_AMD64_SECREL`), deterministic canonical section layout (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`, `.xdata`, `.idata`, `.reloc`), and multi-object `.pdata`/`.xdata` unwind table concatenation sorted by `BeginAddress`.

3. **Structured Linker Diagnostics (`SPEC-27` §7)**:
   - `AX_LINK_DUPLICATE_SYMBOL` (`E1102`): reports duplicate strong definitions across objects with both object names, demangled Axiom item path, and source span when available.
   - `AX_LINK_UNDEFINED_SYMBOL` (`E1103`): reports unresolved external symbols with demangled Axiom item name, referencing object/module, and source call-site span when available.
   - `AX_LINK_ABI_MISMATCH` (`E1104`): reports cross-object function vs. data kind, calling convention, or parameter/return ABI signature mismatches with both object names and formatted signatures.
   - `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`E1105`): rejects non-`IMAGE_FILE_MACHINE_AMD64` (`0x8664`) objects/archive members with a structured target mismatch diagnostic.

4. **Verification Suite (`tests/link2/`)**:
   - Created `tests/link2/link2_oracle.test` and `tests/link2/link2_oracle.py` covering multi-module separate `.obj` + `.lib` archive linking, `--emit-obj-dir` per-module `.obj` verification, byte-for-byte deterministic rebuilds, cross-object relocations (`ADDR64`, `REL32`, `ADDR32NB`, `SECTION`, `SECREL`, `.pdata`/`.xdata`), Strong/Weak/Local symbol precedence, and all four structured diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`).
   - Created `tests/link2/multi_mod_pkg/` (`axiom.toml`, `src/main.ax`, `src/math.ax`, `src/util.ax`) verifying end-to-end multi-module package execution across `interp`, `native`, and `native-O1`.

## Files changed

- compiler/driver/mod.ax
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- compiler/link/linker.ax
- compiler/link/mod.ax
- compiler/link/pe.ax
- tests/link2/link2_oracle.py
- tests/link2/link2_oracle.test
- tests/link2/multi_mod_pkg/axiom.toml
- tests/link2/multi_mod_pkg/src/main.ax
- tests/link2/multi_mod_pkg/src/math.ax
- tests/link2/multi_mod_pkg/src/util.ax

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T067` -> `snapshot D:\projects\compiler\new lang\build-snap-T067 (refreshed: HEAD 2057895 + 12 changed, 0 deleted file(s) of T067)`
- `python build-snap-T067/tools/build_axiomc.py --out build-snap-T067/build` -> `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T067\build\axiomc2.exe`
- `python build-snap-T067/tools/axtest.py -j 1 --root build-snap-T067 --build-dir build-snap-T067/build --compiler build-snap-T067/build/axiomc2.exe link2 run/artifact_container run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax link/dll/qa_dll_boundary.test` -> `WEAK-NATIVE 0`, `TOTAL 25 PASS 25 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 194 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T067` -> `0 errors`

STATUS: COMPLETE round=0
