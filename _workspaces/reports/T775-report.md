STATUS: COMPLETE round=0

# T775 — E18.6: Linker v2 reachability graph, COMDAT deduplication & unreferenced section GC

## Summary

Implemented `compiler/link/gc/mod.ax` (`module compiler.link.gc`) and its end-to-end verification suite in `tests/run/link_section_gc/` per `spec/SPEC-27-separate-compilation-linker-v2.md` §§2–4 (`AXS-LNK-010..025`, `AXS-LNK-050..053`, `INV-LNK-002`; `0099`, `0164`, `0217`, `tasks/0369`, `tasks/0409`, `tasks/0410`, `tasks/0526`, `tasks/0786`, `tasks/0802`, `tasks/0804`):

1. **Per-Item Section Subdivision & `IMAGE_SCN_LNK_COMDAT` Emission (`AXS-LNK-010`, `AXS-LNK-020`)**:
   - Implemented `lgc_section_characteristics`, `lgc_format_subsection_name`, `lgc_emit_function_with_unwind`, and `lgc_emit_static_datum` in `compiler/link/gc/mod.ax`.
   - Subdivides each compiled function into `.text$<sym>` (`IMAGE_SCN_CNT_CODE | IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ`) paired with associative `.pdata$<sym>` (12-byte `RUNTIME_FUNCTION`) and `.xdata$<sym>` (`UNWIND_INFO`) sections tied via `COMDAT_SELECT_ASSOCIATIVE` (`5`), and each read-only/mutable/zero-initialized static or vtable/TypeInfo into `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, or `.tls$<sym>` with `IMAGE_SCN_LNK_COMDAT` (`0x00001000`).

2. **Demand-Driven Archive Extraction & Deterministic `COMDAT` Deduplication (`AXS-LNK-003`, `AXS-LNK-012..014`)**:
   - Implemented `lgc_extract_archives_fixed_point` and `lgc_resolve_symbols_and_comdats` supporting fixed-point `.lib` archive member extraction and deterministic `COMDAT` folding across `COMDAT_SELECT_ANY` (`2`), `COMDAT_SELECT_SAME_SIZE` (`3`), `COMDAT_SELECT_EXACT_MATCH` (`4`), `COMDAT_SELECT_ASSOCIATIVE` (`5`), `COMDAT_SELECT_LARGEST` (`6`), and `COMDAT_SELECT_NODUPLICATES` (`1`), as well as `Strong > Weak > Local` symbol precedence.
   - Redirects all relocations targeting folded duplicate sections to the canonical winning representative (`selected_rep_sec`) and folds associative `.pdata`/`.xdata` children of non-selected COMDAT copies.
   - Emits `AX_LINK_DUPLICATE_SYMBOL` (`136`) on duplicate strong non-COMDAT definitions or `COMDAT_SELECT_SAME_SIZE` / `COMDAT_SELECT_EXACT_MATCH` mismatches.

3. **Root-Set FIFO Mark-Sweep Section GC & Forward Unwind Sweeping (`AXS-LNK-021..024`, `INV-LNK-002`)**:
   - Implemented `lgc_mark_sweep_sections`, `lgc_verify_post_gc_invariants`, `lgc_layout_output_sections`, and `lgc_run_pipeline`.
   - Seeds the reachability root set `R_root` from `@entry` (`main` / `DllMain`), `@export` items, `@used` declarations, `@at(...)` pinned VMA items, `ModuleInit` initializers, and `Reflection` metadata roots.
   - Traverses outgoing `LgcRelocEdge` edges and forward `COMDAT_SELECT_ASSOCIATIVE` `.pdata`/`.xdata` unwind associations in deterministic FIFO order; sweeps all unreferenced code, read-only, mutable, `.bss`, and unwind sections (`dead_unwind_stripped`), ignoring dangling relocations inside dead-stripped sections while diagnosing `AX_LINK_UNDEFINED_SYMBOL` (`135`) on unresolved references from live sections and `AX_LINK_WX_VIOLATION` (`155`) on `W^X` violations.
   - Merges surviving subsections into canonical PE/COFF output sections (`.text`, `.rdata`, `.data`, `.bss`, `.pdata`, `.xdata`, `.tls`, `.custom`) with `SectionAlignment = 0x1000`, `FileAlignment = 0x200`, `.bss` `raw_size = 0`, and `0xCC` (`int3`) code padding vs `0x00` data/unwind padding.

4. **Deterministic `inspect --emit=gc-sections` & `inspect --emit=link-map` Reporting (`AXS-LNK-050`)**:
   - Implemented `lgc_emit_gc_sections_report` and `lgc_emit_link_map_report` producing deterministic reports of retained sections (with `Root(...)`, `ReferencedBy(...)`, or `AssociativeUnwind(...)` provenance), folded COMDAT duplicates, dead-stripped sections, archive member extraction status, COMDAT group winners, merged output section RVAs/file offsets, and surviving symbol addresses.

## Files changed

- compiler/link/gc/mod.ax
- tests/run/link_section_gc/comdat_generic_dedup_and_vtable_fold.ax
- tests/run/link_section_gc/comdat_generic_dedup_and_vtable_fold.stdout
- tests/run/link_section_gc/comdat_root_propagation_and_lsda_chain.ax
- tests/run/link_section_gc/comdat_root_propagation_and_lsda_chain.stdout
- tests/run/link_section_gc/link_map_and_gc_sections_inspect.ax
- tests/run/link_section_gc/link_map_and_gc_sections_inspect.stdout
- tests/run/link_section_gc/link_section_gc_engine.test
- tests/run/link_section_gc/link_section_gc_oracle.py
- tests/run/link_section_gc/link_section_gc_probe.ax.in
- tests/run/link_section_gc/section_gc_roots_and_unwind_sweep.ax
- tests/run/link_section_gc/section_gc_roots_and_unwind_sweep.stdout

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T775` -> `snapshot D:\projects\compiler\new lang\build-snap-T775 (refreshed: HEAD 12ae6c3 + 10 changed, 0 deleted file(s) of T775)`
- `python build-snap-T775/tools/build_axiomc.py --root build-snap-T775 --out build-snap-T775/build --stage0 build/axiomc2.exe --force` -> `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T775\build\axiomc2.exe`
- `python build-snap-T775/tools/axtest.py -j 1 --root build-snap-T775 --build-dir build-snap-T775/build --compiler build-snap-T775/build/axiomc2.exe run/link_section_gc link2 run/opt_pgo_gc run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 37 PASS 37 FAIL 0 SKIP 0 XFAIL 0`
- `python tools/archcheck.py` -> `archcheck: 196 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T775` -> `10 changed file(s) verified`

STATUS: COMPLETE round=0
