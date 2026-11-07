# T773 — E18.7: Windows x64 static `.lib`, PE DLL, import library & GNU `ld` cross-link conformance suite

## Summary

Implemented the Phase 18 E18.7 Windows x64 artifact conformance suite under `tests/conformance/p18/e18_7_windows_artifacts/` covering `SPEC-26` (`spec/SPEC-26-windows-artifact-kinds.md`), `ADR-0034` §4 OI-07b (`spec/decisions/ADR-0034-oracle-independence.md`), `REQ-OWNER-006`, and `REQ-LNK-113`..`REQ-LNK-121`:

1. **Function Pointer Calling Convention & ABI Identity (`fn_ptr_calling_conv_abi.ax`, `o2_fn_ptr_calling_conv_abi.ax`, `ui_fn_ptr_unsafe_mismatch.ax`)**:
   - Verifies that function pointer types (`fn(...)`, `unsafe fn(...)`, `extern "C" fn(...)`, `extern "system" fn(...)`, `unsafe extern "C" fn(...)`, `unsafe extern "system" fn(...)`) preserve their calling convention (`""`, `"C"`, `"system"`) and `unsafe` qualifier in their semantic identity (`REQ-LNK-121`, `0189 §28`).
   - Verifies indirect calls with >4 arguments (5 and 6 parameters across `RCX`, `RDX`, `R8`, `R9`, and 16-byte aligned `[RSP+0x20]` / `[RSP+0x28]` stack slots above the 32-byte Win64 shadow space) and non-capturing closure-to-`fn` coercion in both `--interp` and native (`-O0`, `-O1`, `-O2`) with `--verify-each`.
   - Verifies negative compile-time rejection (`AX_TYPE_MISMATCH`) when assigning an `unsafe fn` to a safe `fn` pointer or calling an `unsafe fn` pointer outside an `unsafe` block (`ui_fn_ptr_unsafe_mismatch.ax`).

2. **Export Visibility, Custom Export Names & ABI Layout (`export_visibility_and_abi_layout.ax`, `o2_export_visibility_and_abi_layout.ax`, `ui_duplicate_export.ax`, `ui_generic_export.ax`)**:
   - Verifies `@export` and `@export("custom_name")` on module-level `pub fn`, inherent `impl` methods, associated `impl` constants, and module-level constants (scalars, fixed arrays, and UTF-8 `Str` fat pointers `"Xin chào thế giới\n"`), alongside unexported `pub` / private functions and deterministic LIFO `Drop` ordering in `--interp` and native (`-O0`, `-O1`, `-O2`).
   - Verifies compile-time diagnostics `AX_ATTR_DUPLICATE_EXPORT` (`ui_duplicate_export.ax`) and `AX_ATTR_EXPORT_GENERIC` (`ui_generic_export.ax`).

3. **COFF Static Library (`.lib`) & Post-Layout Unwind Relocation Conformance (`e18_7_static_lib_conformance.test`, `e18_7_static_lib_oracle.py`)**:
   - Independently validates `axiomc build --kind lib` COFF archives (`!<arch>\n` magic, 1st big-endian `/` and 2nd little-endian `/` linker members, `//` longnames table when member names exceed 15 bytes, even-byte `\n` member padding, `Date = "0"`, `TimeDateStamp = 0`, and byte-for-byte determinism across repeated builds) using both a binary archive parser and GNU `ar t` / `nm --print-armap` / `objdump -dr`.
   - Verifies bidirectional static library linking: Axiom `--kind lib` consumed by both `axiomc build` and `gcc`, and `ar rcs` C static libraries consumed by `axiomc build` via positional `<path>.lib` and `-L <dir> -l<name>`, including lazy archive extraction (unreferenced members with unsatisfied externals are not pulled in).
   - Verifies `REQ-LNK-120` (`AUNW-34`): multi-object C `.obj` files compiled with `-fasynchronous-unwind-tables` (emitting `.pdata` and `.xdata` with `IMAGE_REL_AMD64_ADDR32NB` relocations) linked with Axiom code into both `.exe` and `.dll` images have all `.pdata` `RUNTIME_FUNCTION` RVAs (`BeginAddress`, `EndAddress`, `UnwindInfoAddress`) resolved after final section layout into the merged `.text` and `.xdata` ranges.
   - Verifies `REQ-LNK-121` THIR emission (`(TypeFn false "" ...)`, `(TypeFn false "C" ...)`, `(TypeFn false "system" ...)`, `(TypeFn true "C" ...)`) and negative diagnostics (`AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`).

4. **PE32+ DLL (`.dll`), Companion Short-Import `.lib` & Import Table Conformance (`e18_7_pe_dll_import_conformance.test`, `e18_7_pe_dll_import_oracle.py`)**:
   - Independently validates `axiomc build --kind dll` PE32+ DLLs (`IMAGE_FILE_DLL = 0x2000`, `ImageBase = 0x180000000`, `DllCharacteristics = 0x0160`, sorted `.edata` Export Directory with 1-based ordinals, multi-page `.reloc` Base Relocation Directory with odd/even `IMAGE_REL_BASED_DIR64` blocks and `IMAGE_REL_BASED_ABSOLUTE` 4-byte alignment padding, W^X section flags, `TimeDateStamp = 0`, `CheckSum = 0`, and byte-for-byte determinism) and companion COFF short-import `.lib` (`Sig1 = 0x0000`, `Sig2 = 0xFFFF`, `IMPORT_OBJECT_CODE` vs `IMPORT_OBJECT_DATA`).
   - Verifies `REQ-LNK-113`..`REQ-LNK-119`:
     - `REQ-LNK-113`: `.idata` is mapped `READ|WRITE` and at runtime `GetProcAddress(hMod, "dll_renamed_scale")` equals the resolved pointer stored in the `__imp_dll_renamed_scale` IAT slot.
     - `REQ-LNK-114`: On-disk IAT entries in `.idata` before load equal ILT entries (`Hint/Name` RVAs `< SizeOfImage`), never hardcoded foreign virtual addresses.
     - `REQ-LNK-115` & `REQ-LNK-116`: Explicit `@link("<dll>")` mapping and byte-identical `.idata` layout across repeated builds.
     - `REQ-LNK-117`: RIP-relative `FF 25 <disp32>` / `FF 15 <disp32>` IAT references in `.text`.
     - `REQ-LNK-118`: Interoperability across Axiom and C (`gcc`) `.exe`/`.dll` boundaries using both COFF short-import `.lib` and GNU `dlltool` `.idata$2..$7` `.dll.a` archives.
     - `REQ-LNK-119`: Delay-load import directory `DataDirectory[13] == (0, 0)`.
   - Verifies forced non-preferred base relocation (`VirtualAlloc` reserving `0x180000000` prior to `LoadLibraryA`) relocating 64-bit `Str` fat-pointer fields in `.rdata` across 3 RVA pages, and `_DllMainCRTStartup` lifecycle (`__ax_resolve_module_bindings()` failure returning `FALSE` before `@entry`, `@entry` returning `0` aborting `LoadLibraryA`, and `@entry` returning `1` running attach/detach cleanly).

5. **GNU `ld` & `gcc` Cross-Linking Conformance (`e18_7_gnu_ld_crosslink_conformance.test`, `e18_7_gnu_ld_crosslink_oracle.py`)**:
   - Verifies `ADR-0034` §4 OI-07b and `SPEC-26` §§5–9: deterministic `axiom_rt.obj` emission (`build --rt-obj` and `compile --rt-obj`), `--kind obj` / `--emit=obj` COFF symbol cleanliness (standard `__imp_<sym>` externals, zero leaked `<dll>$<sym>` or `__IAT_*` symbols), multi-artifact cross-linking (`--kind obj` + `--kind lib` + `--kind dll` + C `.obj`) at `-O0` and `-O2` across `axiomc build`, standalone GNU `ld`, and `gcc -nostdlib`, plus cross-linking equivalence across E18.7 conformance and `tests/run/` programs.

## Files changed

- tests/conformance/p18/e18_7_windows_artifacts/e18_7_gnu_ld_crosslink_conformance.test
- tests/conformance/p18/e18_7_windows_artifacts/e18_7_gnu_ld_crosslink_oracle.py
- tests/conformance/p18/e18_7_windows_artifacts/e18_7_pe_dll_import_conformance.test
- tests/conformance/p18/e18_7_windows_artifacts/e18_7_pe_dll_import_oracle.py
- tests/conformance/p18/e18_7_windows_artifacts/e18_7_static_lib_conformance.test
- tests/conformance/p18/e18_7_windows_artifacts/e18_7_static_lib_oracle.py
- tests/conformance/p18/e18_7_windows_artifacts/export_visibility_and_abi_layout.ax
- tests/conformance/p18/e18_7_windows_artifacts/fn_ptr_calling_conv_abi.ax
- tests/conformance/p18/e18_7_windows_artifacts/o2_export_visibility_and_abi_layout.ax
- tests/conformance/p18/e18_7_windows_artifacts/o2_fn_ptr_calling_conv_abi.ax
- tests/conformance/p18/e18_7_windows_artifacts/ui_duplicate_export.ax
- tests/conformance/p18/e18_7_windows_artifacts/ui_fn_ptr_unsafe_mismatch.ax
- tests/conformance/p18/e18_7_windows_artifacts/ui_generic_export.ax

## Verification

- Built Stage-2 compiler (`build-snap-T773/build/axiomc2.exe`) in isolated snapshot `build-snap-T773`.
- Ran `conformance/p18/e18_7_windows_artifacts`, intrinsic canaries (`run/intrinsics/assert_false.ax`, `run/intrinsics/panic_abort.ax`, `ui/intrinsics/unknown_intrinsic.ax`), `link/lib`, and `link/dll` with `axtest.py -j 1`: all passed with `WEAK-NATIVE 0`.
- Ran `archcheck.py` (0 violations), `reqcov.py --strict` (`COVERAGE OK`, 0 gaps), `harness_check.py` (`HARNESS OK`), and `taskctl.py changes T773`.

STATUS: COMPLETE round=0
