STATUS: COMPLETE round=2

# T751 Report — E18.7 PE DLL Output: Exports, DllMain Initialiser, Base Relocations, Import Library

## Summary

Implemented Windows x64 PE32+ dynamic-link library (`.dll`) emission, `.edata` export directory generation (`@export`, `@export("name")`, and `.drectve` `-export:`), synthesized `_DllMainCRTStartup` process-attach/detach entry stub (`__ax_resolve_module_bindings()` + optional `@entry` hook), `.reloc` base relocation blocks (`IMAGE_REL_BASED_DIR64` with `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`), companion COFF short-import `.lib` generation (`--implib <path>` or `<stem>.lib`), short-import + traditional MinGW/MSVC import `.lib` consumption, and GNU `ld` / `gcc` `--emit=obj` cross-linking (`__imp_<name>` thunks + `--rt-obj <path>` runtime object) across `compiler/obj`, `compiler/link`, and `compiler/driver` per `spec/SPEC-26-windows-artifact-kinds.md` (`REQ-OWNER-006`, `REQ-LNK-073..112`), `ADR-0001` §5–6, and `ADR-0034` §4 (`OI-07b`).

## Design & Key Decisions

1. **PE32+ `.dll` Image Headers, W^X & Determinism (`compiler/link/pe.ax`, `compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-005`, `AXS-WLIB-020`, `REQ-LNK-073..097`)**:
   - Extended `PeLinkOptions` and `PeImageWriter` (`pe_link_with_opts_to_buf`, `pe_link_dll_to_buf`, `pe_link_dll_and_libs_to_buf`) with `is_dll: bool` and `dll_name: StrView`.
   - Emits `Characteristics = 0x2222` (`IMAGE_FILE_EXECUTABLE_IMAGE | IMAGE_FILE_LARGE_ADDRESS_AWARE | IMAGE_FILE_DEBUG_STRIPPED | IMAGE_FILE_DLL`), `Magic = 0x020B` (PE32+), `ImageBase = 0x0000000180000000` (`0x180000000`), `SectionAlignment = 0x1000`, `FileAlignment = 0x200`, `DllCharacteristics = 0x0160` (`HIGH_ENTROPY_VA | DYNAMIC_BASE | NX_COMPAT`), zeroed timestamps/checksums, strict W^X section permissions, and zero C runtime (`msvcrt.dll`/`ucrtbase.dll`/`vcruntime140.dll`) dependency.

2. **Export Visibility Contract, `.edata` Export Directory & Diagnostics (`compiler/driver/pipeline.ax`, `compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-004`, `AXS-WLIB-021`, `AXS-WLIB-050`)**:
   - Validated `@export` / `@export("custom_name")` across module functions, `impl` methods, and module `const` data items in `pipe_validate_exports`: rejects uninstantiated generic exports with `AX_FFI_GENERIC_EXPORT` (`141u32`) and duplicate Axiom export names with `AX_LINK_DUPLICATE_EXPORT` (`140u32`, `data.symbol`), fixing `pipe_is_mono_clone` (`(*inst).orig_item != target`) so non-generic items registered in `ctx.mono.instances_head` are always validated.
   - Preserved strict separation between Axiom `pub` visibility and binary exports (`REQ-LNK-210`): non-`@export` `pub` items are never emitted into `.edata`.
   - Supported COFF `.drectve` `-export:<ext>[=<internal>][,data]` directives across both Axiom and foreign C `.obj` inputs (`linker_parse_drectve_exports`), routing `--kind dll` renamed exports via `-export:<ext>=<internal>` so cross-object export name collisions cleanly report `AX_LINK_DUPLICATE_EXPORT` (`data.symbol`) rather than spurious symbol collisions.
   - Sorted exported symbols strictly in ascending ASCII byte order (`Base = 1`) and serialized the 40-byte `IMAGE_EXPORT_DIRECTORY`, `ExportAddressTable`, `NamePointerTable`, `OrdinalTable`, DLL filename, and export strings into `.edata` (`DataDirectory[0]`).

3. **Synthesized `_DllMainCRTStartup` Initialiser (`compiler/link/linker.ax`, `compiler/driver/pipeline.ax`, `SPEC-26 AXS-WLIB-022`, `ADR-0001 §5–6`, `SPEC-56 AXS-MOD-012`)**:
   - `--kind dll` builds require no `fn main()`. `linker_emit_dll_entry_stub` synthesizes a Win64 ABI `_DllMainCRTStartup(hinstDLL: usize, fdwReason: u32, lpvReserved: *mut u8) -> i32` stub in `.text` (using a 16-byte-aligned 56-byte frame saving 3 non-volatile registers plus 32-byte Win64 shadow space):
     - On `DLL_PROCESS_ATTACH` (`fdwReason == 1`): invokes `__ax_resolve_module_bindings() -> bool` if defined in the linked objects; if it returns `0` (`false`), immediately returns `0` (`FALSE`) in `eax` without executing user initializers. Next invokes any optional `@entry` hook (`0`-arg `fn() -> () | bool | i32` or `3`-arg `fn(usize, u32, *mut u8) -> () | bool | i32`), propagating `false` / `0` as `0` (`FALSE`) so `LoadLibraryA`/`LoadLibraryW` fails cleanly, otherwise returning `1` (`TRUE`).
     - On `DLL_PROCESS_DETACH` (`0`), `DLL_THREAD_ATTACH` (`2`), and `DLL_THREAD_DETACH` (`3`): forwards `(hinstDLL, fdwReason, lpvReserved)` to a `3`-arg `@entry` handler when present, or returns `1` (`TRUE`).

4. **Base Relocation Table `.reloc` (`compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-023`, `REQ-LNK-090..093`)**:
   - Recorded every resolved `IMAGE_REL_AMD64_ADDR64` relocation across `.text`, `.rdata`, and `.data` as an `IMAGE_REL_BASED_DIR64` (`type = 10`) entry (excluding position-independent `REL32` and `ADDR32NB` relocations), sorted ascending by RVA, grouped into 4 KiB page blocks (`PageRVA`, `BlockSize`, 4-byte padded with `IMAGE_REL_BASED_ABSOLUTE = 0`) in `.reloc` (`DataDirectory[5]`).
   - Emits the minimal 12-byte dummy block (`PageRVA = 0x1000`, `BlockSize = 12`) when a `.dll` has zero `ADDR64` relocations so the Windows loader always honours `DYNAMIC_BASE` rebasing when preferred `ImageBase` (`0x180000000`) is occupied.

5. **Companion COFF Short-Import `.lib` & Import Library Consumption (`compiler/obj/coff.ax`, `compiler/link/import.ax`, `compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-030..031`, `REQ-LNK-098..112`)**:
   - `pe_write_companion_implib_to_buf` generates a deterministic COFF archive (`!<arch>\n`, 1st big-endian + 2nd little-endian symbol directories, `//` longnames table when needed, zeroed timestamps/UIDs/GIDs/modes) containing one 20-byte `IMPORT_OBJECT_HEADER` (`Sig1 = 0x0000`, `Sig2 = 0xFFFF`, `Machine = 0x8664`) per export (`IMPORT_OBJECT_CODE` exporting both `<sym>` and `__imp_<sym>`; `IMPORT_OBJECT_DATA` exporting `__imp_<sym>`), written alongside `<stem>.dll` as `<stem>.lib` or to `--implib <path>`.
   - `compiler/link/` consumes both COFF short-import `.lib`s (synthesizing `.idata` descriptors/ILT/IAT defining `__imp_<sym>` + `__IAT_<sym>` and 6-byte `FF 25 <disp32>` `.text` thunks for code imports) and traditional MinGW `dlltool`/`gcc -Wl,--out-implib` `.idata$*` COFF archive members (bridging zero-length `.idata$4`/`.idata$5` terminator markers across merged archive sections).

6. **GNU `ld` / `gcc` Cross-Linking of `--emit=obj` (`compiler/driver/opts.ax`, `compiler/driver/pipeline.ax`, `compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-032`, `ADR-0034 §4 OI-07b`)**:
   - In `--emit=obj` / `--kind obj`, `pipe_lower_dll_imports_for_obj` identifies true `<dll>$<FuncName>` FFI import symbols (`pipe_is_dll_import_sym`, preserving Axiom `Type$method` mangled symbols untouched and maintaining 100% byte-identical `axiom0` `--emit=obj` parity) and lowers each into a local 6-byte indirect jump stub (`FF 25 00 00 00 00`) referencing `SYM_EXTERNAL` `__imp_<FuncName>`.
   - Added `--rt-obj <path>` (`linker_write_runtime_coff_obj_to_buf`) emitting a deterministic linkable COFF `axiom_rt.obj` providing `mainCRTStartup` and Axiom host runtime intrinsics (`__ax_host_print`, `__ax_host_print_int`, `__ax_host_println`, `axiom_panic`, etc.) referencing `KERNEL32.dll` APIs via standard `__imp_<Name>` symbols so `gcc -nostartfiles <app.obj> axiom_rt.obj -lkernel32` links and runs every native test identically to self-linked PE executables.

## Files changed

- compiler/driver/mod.ax
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- compiler/link/import.ax
- compiler/link/linker.ax
- compiler/link/mod.ax
- compiler/link/pe.ax
- compiler/obj/coff.ax
- compiler/obj/mod.ax
- tests/link/dll/gnu_ld_run.test
- tests/link/dll/gnu_ld_run_oracle.py
- tests/link/dll/pe_dll.test
- tests/link/dll/pe_dll_oracle.py
- tests/link/dll/qa_dll_boundary.test
- tests/link/dll/qa_dll_boundary_oracle.py
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_boundary_edges.ax
- tests/selfhost/driver/qa_driver_cli_and_project.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/encode/qa_encode_edge_cases.ax
- tests/selfhost/encode/qa_encode_instructions.ax
- tests/selfhost/encode/qa_encode_relocs_and_frames.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/obj/qa_coff_edge_cases.ax
- tests/selfhost/obj/qa_coff_writer_diff.ax
- tests/selfhost/obj/qa_obj_model.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax

## Verification

- **Stage-1 / Stage-2 / Stage-3 Bootstrap & Fixed-Point (`build-snap-T751`)**:
  - `python tools/build_axiomc.py --root build-snap-T751 --out build-snap-T751/build --stage 3`
  - `STAGE1 OK`: `20,432,384` bytes (`sha256=9cbe6c56fe5667da82f2e4920fc13d929211319047fe72347bd693a09a7bd862`)
  - `STAGE2 (O1) OK`: `6,323,200` bytes (`sha256=498f476c041acf10954cfb2e793d7069e5d6730556d3c83af8e51787913e8b48`)
  - `STAGE3 (O1) OK`: `6,323,200` bytes (`sha256=498f476c041acf10954cfb2e793d7069e5d6730556d3c83af8e51787913e8b48`)
  - `FIXED-POINT (O1) OK`: byte-identical `axiomc2.exe == axiomc3.exe` across distinct Stage-2 and Stage-3 working directories.
- **PE DLL, Import Library & GNU `ld` Carry-Over Suites (`tests/link/dll/`, `-j 1`)**:
  - `python tools/axtest.py --root build-snap-T751 --compiler build-snap-T751/build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v link/dll/`: **`TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`):
    - `link/dll/pe_dll.test`: verifies `.dll` + companion `.lib` byte-for-byte determinism, PE32+ headers (`0x2222`, `0x180000000`, `0x0160`), `llvm-objdump -p` exports/relocations/imports, non-`@export` `pub` exclusion, Axiom `.exe` consuming exported functions + `@export` data via short-import `.lib`, dynamic `LoadLibraryA`/`GetProcAddress`, forced OS rebasing by occupying `0x180000000` via `VirtualAlloc` prior to `LoadLibraryA`, `_DllMainCRTStartup` `__ax_resolve_module_bindings()` failure returning `FALSE` before user `@entry`, `@entry` attach/detach reason tracking and failure propagation, third-party `gcc -shared` DLL consumption via both MinGW `.dll.a` and short-import `.lib`, `axiom.toml` `kind = "dll"`, `--implib <path>`, `axiomc run` rejection (`AX_DRIVER_USAGE` exit `2`), `AX_FFI_GENERIC_EXPORT`, and `AX_LINK_DUPLICATE_EXPORT` (human + `--json`).
    - `link/dll/gnu_ld_run.test`: verifies `ADR-0034` §4 (`OI-07b`) — all **523 / 523** native `tests/run/` programs emitted with `--emit=obj` + `--rt-obj` and cross-linked by MinGW-w64 `gcc`/GNU `ld` (`-nostartfiles`, `-lkernel32` + any `@link` system libs) produce identical exit codes, stdout, and stderr to self-linked PE executables, with zero `__IAT_*` or `<dll>$*` symbols in emitted `.obj` files.
- **In-Scope & Full Regression Suites (`build-snap-T751`)**:
  - `link/ obj/ driver/ selfhost/obj/ selfhost/link/ selfhost/driver/ selfhost/obj_link_driver/` (`-j 1`): **`TOTAL 72 PASS 68 FAIL 0 SKIP 4 XFAIL 0`** (`WEAK-NATIVE 0`; the 4 `SKIP`s are `requires: axiom0-internal`).
  - Full non-selfhost suites (`conformance/ diff/ encode/ fuzz/ hir/ lex/ lir/ mc/ mir/ modules/ opt/ parse/ perf/ programs/ resolve/ run/ std/ typeck/ ui/ unit/ verify/`): **2,795+ tests PASS, 0 regressions**.
- **Repository & Architecture Gates**:
  - `gen_{obj,link,local_symbols,driver,obj_link_driver}_test*.py --check`: all 14 selfhost bundles `up to date` in both `build-snap-T751` and workspace root.
  - `python tools/archcheck.py`: `193 files scanned, 0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T751`: `0` `REFUSED` lines for `T751`.
  - LF & canonical syntax check: `0` `\r` bytes and `0` UTF-8 BOMs across all 27 changed/added files and `T751-report.md`; `0` `:=`, `var`, or `::` tokens in edited `.ax` files.

## Spec Deviations & Notes

- None on observable behavior or binary format. Because `compiler/diag/code.ax` is shared across concurrent tasks (`T751` holds it only in `locks:` rather than `paths:`), numeric diagnostic IDs `140u32` (`AX_LINK_DUPLICATE_EXPORT`) and `141u32` (`AX_FFI_GENERIC_EXPORT`) are defined in `compiler/link/pe.ax` and `compiler/driver/opts.ax` (re-exported via `mod.ax`) and rendered with their canonical symbolic names and structured `data.symbol` payloads in both human and `--json` diagnostics in `compiler/driver/pipeline.ax` (matching `T750`'s `137..139` pattern).
- Exported data constants use `@export pub const NAME: T = ...` (module-level constants emitted into `.rdata`), as Axiom's surface syntax uses `const` items at module scope (`SPEC-26 AXS-WLIB-004` / `AXS-WLIB-030` `IMPORT_OBJECT_DATA`).

## Round 1

### Fixes Addressed (`_workspaces/reports/T751-qa.md`)

1. **Finding 1 (`compiler/driver/pipeline.ax` — `pipe_validate_exports` / `pipe_validate_export_item` double-visitation of `HIR_ITEM_IMPL` shallow clones)**:
   - **Root cause**: `hir_postprocess_items` (`compiler/hir/lower.ax:1605-1611`) appends a shallow clone (`clone_hir_item_shallow`) of every `HIR_ITEM_IMPL` member onto `ctx.hir.items` without copying the enclosing `impl<T>`'s `generic_params`. `pipe_validate_exports` previously validated both `HIR_ITEM_IMPL.members` and top-level `ctx.hir.items` while skipping only `MonoEngine` clones (`pipe_is_mono_clone`), causing inherent `impl` `@export` methods to be visited twice (spurious `AX_LINK_DUPLICATE_EXPORT`) and generic `impl<T>` `@export` methods to be re-visited at top level with `parent_is_generic = false` (registering the rejected export name in `seen_sv` and triggering spurious `AX_LINK_DUPLICATE_EXPORT`).
   - **Fix**:
     - Added `pipe_is_impl_member_clone(items_head, target)` and `in_impl: bool` parameter to `pipe_validate_export_item`: fast-exits when `!has_export`, skips `pipe_is_mono_clone`, skips top-level shallow clones of `HIR_ITEM_IMPL.members` when `!in_impl`, and rejects any `item_is_generic` (`parent_is_generic || generic_params != null`) `@export` item once with `AX_FFI_GENERIC_EXPORT` without adding its name to `seen_sv`.
     - Imported `thir_get_orig_item_name` in `driver_emit_objmodel_filtered` so bare `@export` on an `impl` method whose internal symbol was collision-mangled by `mb_dedup_mono_names` (e.g. `foo_<sym>`) still exports its unqualified source identifier `foo` (`-export:foo=foo_<sym>`), guarded `--kind lib`/`--kind obj` COFF alias emission with `pipe_other_fn_uses_name`, and updated `pipe_emit_exported_consts` to avoid internal COFF symbol collisions when multiple `impl` blocks define associated `const` items sharing a bare identifier under distinct `@export("...")` names.
     - Updated §3 parenthetical in `T751-report.md` per QA's non-blocking note to accurately describe `_DllMainCRTStartup`'s 56-byte frame (`3` saved non-volatile registers + `32`-byte Win64 shadow space, 16-byte aligned).

2. **Regression & Boundary Oracle Coverage (`tests/link/dll/qa_dll_boundary.test`, `tests/link/dll/qa_dll_boundary_oracle.py`)**:
   - Verified QA's full `qa_dll_boundary.test` suite passes (`QA-DLL-BOUNDARY-ORACLE ok`, covering inherent `impl` `@export("...")`, distinct `impl` blocks sharing a method name under distinct `@export("...")` names, generic `impl<T>` `AX_FFI_GENERIC_EXPORT` without false duplicate diagnostics, multi-page `.reloc` odd/even blocks, `//` longnames short-import archives, transitive DLL-to-DLL chaining under simultaneous forced `VirtualAlloc(0x180000000)` rebasing, 1-based ordinal vs name `GetProcAddress`, and 3-arg `@entry(...) -> i32`) and extended `qa_dll_boundary_oracle.py` with sub-checks:
     - `5b`: `@export` generic method `fn passthrough<U>` inside non-generic `impl` -> sole `AX_FFI_GENERIC_EXPORT`.
     - `5c`: bare `@export` on inherent `impl FirstImpl { pub fn bare_impl_fn }` alongside colliding non-exported `impl SecondImpl { pub fn bare_impl_fn }` -> exports `["bare_impl_fn"]` and links/runs consumer `.exe` returning `47`.
     - `5d`: two `impl` blocks with bare `@export pub fn dup_bare_m` -> sole `AX_LINK_DUPLICATE_EXPORT` (`symbol = "dup_bare_m"`).

### Round 1 Verification (`build-snap-T751`)

- **Selfhost Bundle Sync**: Regenerated `tests/selfhost/driver/qa_driver_*.ax` and `tests/selfhost/obj_link_driver/qa_obj_link_driver_*.ax`; verified `--check` exit `0` across `gen_driver_tests.py`, `gen_obj_link_driver_tests.py`, `gen_obj_tests.py`, `gen_link_tests.py`, and `gen_local_symbols_test.py` in both `build-snap-T751` and workspace root.
- **Stage-3 Fixed-Point Bootstrap**:
  - `python build-snap-T751/tools/build_axiomc.py --root build-snap-T751 --out build-snap-T751/build --stage 3`
  - `STAGE1 OK`: `20,446,720` bytes (`sha256=343a314570589449...`)
  - `STAGE2 (O1) OK`: `6,327,808` bytes (`sha256=945d667517aca50d9ede874f27357601e8bb4d4ea7a3a8395c3265e7d768b29d`)
  - `STAGE3 (O1) OK`: `6,327,808` bytes (`sha256=945d667517aca50d9ede874f27357601e8bb4d4ea7a3a8395c3265e7d768b29d`)
  - `FIXED-POINT (O1) OK`
- **Test Suites (`-j 1`, `--exclude-requires axiom0-internal`)**:
  - `link/dll/pe_dll.test` + `link/dll/qa_dll_boundary.test`: **`TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`)
  - `link/dll/gnu_ld_run.test` + `link/lib` + `link/objdump_validate.test` + `run/intrinsics`: **`TOTAL 22 PASS 22 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`)
  - `ui/intrinsics` + `driver` + `obj` + `selfhost/link` + `selfhost/obj` + `selfhost/driver` + `selfhost/obj_link_driver`: **`TOTAL 74 PASS 68 FAIL 0 SKIP 6 XFAIL 0`** (`0 FAIL`; 6 `axiom0-internal` skips)
- **Repository & Architecture Gates**:
  - `python tools/archcheck.py`, `reqcov.py --strict`, `harness_check.py`, `taskctl.py changes T751`: all exit `0` (`0 REFUSED`, `0` CR `\r` bytes, `0` BOMs across all 29 changed files and `T751-report.md`).

## Round 2

### Fixes Addressed (`_workspaces/reports/T751-qa.md` `## Round 1`)

1. **Finding 1 (`tests/selfhost/{encode,isel,backend}/bundles_current.test` — downstream selfhost bundles out of date after `compiler/obj/coff.ax` changes)**:
   - **Root cause**: `compiler/obj/coff.ax` is inlined into `tests/selfhost/{encode,isel,backend}` in addition to `{obj,link,driver,obj_link_driver}`, and only the latter four had been regenerated in Round 0/1.
   - **Fix**: Regenerated `tests/selfhost/encode` (`3` bundles), `tests/selfhost/isel` (`4` bundles), `tests/selfhost/backend` (`6` bundles), `tests/selfhost/driver` (`6` bundles), and `tests/selfhost/obj_link_driver` (`2` bundles), verified all `36` selfhost `gen_*.py --check` scripts exit `0`, verified `axtest.py -j 1 bundles_current.test` passes **`34/34`** (`TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`), and listed all `13` newly regenerated `.ax` bundles in `## Files changed`.

2. **Finding 2 (`compiler/driver/pipeline.ax` — `pipe_emit_exported_consts` order-dependent COFF symbol collisions on associated `const` exports in `impl` blocks)**:
   - **Root cause**: `pipe_emit_exported_consts` previously defaulted `primary_const_sv` to `cname_sv` even when `@export("...")` overrode the exported name (`export_sv.len > 0`) or when an `impl` method / function in `.text` already emitted `cname_sv` (`mb_dedup_mono_names` deduplicates only `HIR_ITEM_FN` against `HIR_ITEM_FN`). Thus `@export("C1") pub const K` before bare `@export pub const K` claimed `"K"` and collided with the later bare `@export pub const K`, and bare `@export pub const M_CONST` collided with unexported `impl` method `pub fn M_CONST()`.
   - **Fix**:
     - Added `pipe_any_hir_fn_uses_name` and `pipe_alloc_exp_const_sym` (`__ax_const$<exp_name_sv>` with deterministic collision-free fallback) and moved `pipe_strip_unlinked_extern_c_prefixes` ahead of `pipe_emit_exported_consts`.
     - Keyed `pipe_emit_exported_consts` exclusively off `exp_name_sv` (never claiming `cname_sv` when `export_sv.len > 0`): in `--kind dll`/`--kind exe` (`!for_lib && !for_obj`), renamed exports, `impl` associated `const` exports, and any symbol already present in `obj` or `ctx.hir` functions emit internal `SYM_GLOBAL` `__ax_const$<exp_name_sv>` paired with `.drectve` `-export:<exp_name_sv>=__ax_const$<exp_name_sv>,data`; in `--kind lib`/`--kind obj`, `exp_name_sv` is emitted directly unless already used by a function/symbol, in which case `__ax_const$<exp_name_sv>` is used.
     - Verified QA's sub-check `5e` (`@export("C1") pub const K` before `@export pub const K` + unexported `impl` method `M_CONST`) passes, and added sub-check `5f` in `tests/link/dll/qa_dll_boundary_oracle.py` covering reversed declaration order (`@export pub const K` before `@export("C1") pub const K`), unexported `impl` method `K`, private module-level `fn PRIV_K` alongside `impl` `@export pub const PRIV_K`, companion `.lib` `dllimport` consumption via `axiomc`, direct DLL `dllimport` consumption via `gcc`, and collision-free `--kind obj` / `--kind lib` builds.

### Round 2 Verification (`build-snap-T751` & Root Sync)

- **Stage-3 (`O1`) Fixed-Point Bootstrap (`build-snap-T751`)**:
  - `python build-snap-T751/tools/build_axiomc.py --root build-snap-T751 --out build-snap-T751/build --stage 3`
  - `STAGE1 OK`: `20,468,736` bytes (`sha256=86e62ef046c02b7f...`)
  - `STAGE2 (O1) OK`: `6,334,464` bytes (`sha256=15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`)
  - `STAGE3 (O1) OK`: `6,334,464` bytes (`sha256=15086a66d9926d321e4ff36edef002a33e91445f9bbf591b4ffd94ea1bdfabfb`)
  - `FIXED-POINT (O1) OK` (`axiomc2.exe == axiomc3.exe`)
- **Test Suites (`build-snap-T751`, `-j 1`, `--exclude-requires axiom0-internal`)**:
  - `bundles_current.test`: **`TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`** (`34/34 PASS`, `WEAK-NATIVE 0`)
  - `link/dll/qa_dll_boundary.test` + `link/dll/pe_dll.test` + `link/dll/gnu_ld_run.test`: **`TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`)
  - `link/lib` + `link/objdump_validate.test` + `run/intrinsics` + `ui/intrinsics` + `selfhost/encode` + `selfhost/isel` + `selfhost/link` + `selfhost/obj` + `selfhost/obj_link_driver`: **`TOTAL 74 PASS 74 FAIL 0 SKIP 0 XFAIL 0`** (`0 FAIL`)
  - `selfhost/backend` + `selfhost/driver`: **`TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`** (`0 FAIL`)
- **Repository & Static Gates**:
  - All `36` selfhost `gen_*.py --check` scripts exit `0`; root repo generators exit `0`.
  - `python tools/archcheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`, `python .claude/skills/axiom-tasks/scripts/harness_check.py`, and `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T751`: all exit `0` (`0 REFUSED`, `0` `\r` bytes, `0` UTF-8 BOMs across all `42` changed files and `T751-report.md`).

STATUS: COMPLETE round=2
