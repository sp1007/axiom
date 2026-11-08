# T776 — E18.6 Separate Compilation, Multi-Object Archives, Section GC & P18 Exit Conformance Suite

## Summary

Authored the end-to-end E18.6 conformance suite in `tests/conformance/p18/e18_6_separate_compilation/` certifying `spec/SPEC-27-separate-compilation-linker-v2.md` (`AXS-LNK-001..053`), `spec/invariants.md` (`INV-LNK-001..003`), and `REQ-LNK-3945..3983`:

1. **Traceability & Conformance Documentation (`README.md`)**:
   - Maps every `AXS-LNK-*` rule (`AXS-LNK-001..005`, `AXS-LNK-010..014`, `AXS-LNK-020..025`, `AXS-LNK-050..053`), `INV-LNK-001..003` invariant, and `REQ-LNK-3945..3983` requirement ID to the conformance tests and oracle checks.
2. **Live `compiler.link.gc` Subsystem Probe (`e18_6_separate_compilation_probe.ax.in`) & End-to-End Oracle (`e18_6_separate_compilation_oracle.py`, `e18_6_separate_compilation_oracle.test`)**:
   - Bundles the live `compiler.link.gc` implementation (`LinkGcGraph`, `lgc_run_pipeline`, `lgc_emit_gc_sections_report`, `lgc_emit_link_map_report`) and verifies identical execution across `--interp` and native `-O0` (`e18_6_probe_O0.exe`).
   - Compiles a real 3-module Axiom workspace (`main.ax`, `math.ax`, `scale.ax`) together with a multi-member COFF `.lib` archive (`e186_archive.lib`, containing a needed member and an unreferenced broken member referencing an undefined symbol) and a PE32+ `.dll` + companion short-import `.lib` (`e186_plugin.dll` + `e186_plugin.lib`), verifying byte-identical `.obj`/`.exe` reproducibility, `W^X` section hygiene, `.axmeta`/`.axlto`/`.axmir` stripping, canonical PE section ordering, and semantic equivalence between separate `.obj` + `.axmi` linking and whole-workspace builds.
   - Verifies single-module incremental `.obj` rebuild when editing one private function in `math.ax` (only `math.obj` is re-emitted while `main.obj`, `scale.obj`, and `math.axmi` remain unchanged) and `< 100 ms` warm no-op check budget.
   - Verifies structured linker diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL` with `_AX1_` lossless demangling to `math.add`, `AX_LINK_ABI_MISMATCH`, and `AX_LINK_ARTIFACT_TARGET_MISMATCH`) in `--json` mode.
3. **Standalone Differential Conformance Fixtures (`modes: interp native`, `0 WEAK-NATIVE`)**:
   - `separate_vs_whole_workspace_equivalence.ax`: canonical topological module input ordering independent of `--jobs N` completion order, `Strong`/`Weak`/`Local`/`Import` resolution precedence, cross-object `REL32`/`ADDR64`/`ADDR32NB`/`SECREL`/`SECTION` relocation patching, and separate vs whole-workspace build equivalence.
   - `comdat_generic_vtable_archive_and_section_gc.ax`: per-item section subdivision (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, `.pdata$<sym>`, `.xdata$<sym>`), `IMAGE_SCN_LNK_COMDAT` generic/vtable folding (`Any`, `SameSize`, `ExactMatch`, `Largest`, `Associative`) with root propagation, demand-driven `.lib` extraction, and root-set FIFO mark-sweep section GC (`@entry`, `@export`, `@used`, `@at` pinned VMA, `ModuleInit`, `Reflection`) with forward `.pdata`/`.xdata` unwind sweeping.
   - `incremental_single_obj_rebuild_and_noop_budget.ax`: Private-Function Body Firewall (`modules_typechecked=1`, `cgu_rebuilt=1`, `cgu_reused=3`, downstream `.axmi` backdated to `Green`), clean-build equivalence, and `< 100 ms` warm no-op rebuild on the 28-module compiler workspace.
   - `negative_linker_diags_abi_comdat_and_wx.ax`: structured negative linker diagnostics and safety gates (`AX_LINK_UNDEFINED_SYMBOL = 135`, `AX_LINK_DUPLICATE_SYMBOL = 136`, `AX_LINK_RELOC_OUT_OF_RANGE = 137`, `AX_LINK_ABI_MISMATCH = 153`, `AX_LINK_WX_VIOLATION = 155`, `AX_LINK_DANGLING_RELOC = 156`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T776`
- `python build-snap-T776/tools/axtest.py -j 1 --root build-snap-T776 --build-dir build-snap-T776/build --compiler build-snap-T776/build/axiomc2.exe conformance/p18/e18_6_separate_compilation run/link_section_gc link2 run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 37 PASS 37 FAIL 0 SKIP 0 XFAIL 0`
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `0 problems`
- `python tools/archcheck.py` -> `ARCHCHECK OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T776` -> `12 files changed, 0 REFUSED`

## Files changed

- tests/conformance/p18/e18_6_separate_compilation/README.md
- tests/conformance/p18/e18_6_separate_compilation/comdat_generic_vtable_archive_and_section_gc.ax
- tests/conformance/p18/e18_6_separate_compilation/comdat_generic_vtable_archive_and_section_gc.stdout
- tests/conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_oracle.py
- tests/conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_oracle.test
- tests/conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_probe.ax.in
- tests/conformance/p18/e18_6_separate_compilation/incremental_single_obj_rebuild_and_noop_budget.ax
- tests/conformance/p18/e18_6_separate_compilation/incremental_single_obj_rebuild_and_noop_budget.stdout
- tests/conformance/p18/e18_6_separate_compilation/negative_linker_diags_abi_comdat_and_wx.ax
- tests/conformance/p18/e18_6_separate_compilation/negative_linker_diags_abi_comdat_and_wx.stdout
- tests/conformance/p18/e18_6_separate_compilation/separate_vs_whole_workspace_equivalence.ax
- tests/conformance/p18/e18_6_separate_compilation/separate_vs_whole_workspace_equivalence.stdout

STATUS: COMPLETE round=0
