STATUS: COMPLETE round=1

# T750 Report — E18.7 Static Libraries: COFF Archive (`.lib`) Writer and Reader, `--kind`

## Summary

Implemented Windows x64 COFF static library (`.lib`) emission, short-import object emission/recognition, demand-driven archive extraction in the PE32+ linker, deterministic `-L`/`-l` and `@link("name")` library search resolution, and unified `--kind exe|obj|lib|dll` driver support across `compiler/obj`, `compiler/link`, and `compiler/driver` per `spec/SPEC-26-windows-artifact-kinds.md` (`REQ-OWNER-006`, `REQ-LNK-057..072`, `REQ-LNK-211..226`).

### Round 1 QA Fixes (`_workspaces/reports/T750-qa.md`)

1. **Finding 1 — Library probe order & `has_arch_ext` gating (`compiler/link/linker.ax`, `SPEC-26 AXS-WLIB-003` item 2, `REQ-LNK-071`, `REQ-LNK-225`)**:
   - Updated `linker_resolve_library_in_dirs` so when `has_arch_ext` is `true` (name already ends in `.lib` or `.a`, e.g. `-lfoo.lib` or `-llibfoo.a`), each `-L<dir>` probes ONLY `<dir>/<name>` (followed by direct `<name>` fallback after the directory loop), never appending `.lib`/`.a` (`else`-guarded so `-lfoo.lib` never spuriously matches `<dir>/foo.lib.lib`, `<dir>/libfoo.lib.a`, or `<dir>/foo.lib.a`).
   - When `has_arch_ext` is `false`, each `-L<dir>` probes `<dir>/<name>.lib` -> `<dir>/lib<name>.lib` -> `<dir>/lib<name>.a` -> `<dir>/<name>.a` in exact precedence order.

2. **Finding 2 — `@link(...)` collection before `pe_link_objmodel_to_buf` fast path (`compiler/driver/pipeline.ax`, `SPEC-26 AXS-WLIB-003` items 1–2, `REQ-LNK-069..071`, `REQ-LNK-223..225`)**:
   - Hoisted `pipe_collect_attr_libs` (covering `HIR_ITEM_FN`, `HIR_ITEM_EXTERN_BLOCK`, and `HIR_ITEM_STATIC`) ahead of the `pe_link_objmodel_to_buf` fast-path branch in `driver_execute_build_into_ctx` and gated the fast path on `attr_lib_count == 0`.
   - Programs carrying `@link("qa1.lib")`, `@link("sub/qa_sub.lib")`, or `@link("...")` with zero `-L`/`-l` CLI flags now route through `pe_link_obj_and_libs_to_buf`, resolving static COFF archives and short-import `.lib`s via `linker_resolve_and_load_libraries` instead of emitting broken `qa1.dll` DLL import tables.

3. **Finding 3 — `axiomc run --emit=obj` rejection (`compiler/driver/opts.ax`, `SPEC-26 AXS-WLIB-002` items 1 & 4)**:
   - Updated `--emit` option handling (`opt_kind == 4u32`) so `--emit=obj` / `--emit obj` (exact alias of `--kind obj`) sets `dopts.has_explicit_kind = true`, `dopts.artifact_kind = ARTIFACT_OBJ`, and `dopts.kind_str = "obj"` (and clears `dopts.emit_kind` if overridden by a later `--kind` != `obj`), while also guarding `CMD_RUN` in `driver_parse_cli` on `(dopts.has_explicit_kind && dopts.artifact_kind != ARTIFACT_EXE) || dopts.emit_kind == EMIT_OBJ` to emit `AX_DRIVER_USAGE` and exit `2`.

4. **Regression Tests & Bundle Regeneration (`tests/link/lib/coff_lib_oracle.py`, `tests/selfhost/{obj,link,driver,obj_link_driver}/*`)**:
   - Extended `tests/link/lib/coff_lib_oracle.py` with section `2(d)` (direct `@link("qa1.lib")` and `@link("sub/qa_sub.lib")` with zero `-L`/`-l` flags + `llvm-objdump -p` verifying no spurious `qa1.dll` import), section `2(e)` (`<name>.lib` -> `lib<name>.lib` -> `lib<name>.a` precedence + `-lexact.lib` skipping decoy `exact.lib.lib` / `libexact.lib.a` / `exact.lib.a` in an earlier `-L` directory), and expanded section `5e` on a runnable `pub fn main() -> i32 { 0 }` input verifying `run` rejects `--kind lib`, `--kind obj`, `--kind dll`, `--emit=obj`, and `--emit obj` with exit code `2` and `AX_DRIVER_USAGE`.
   - Regenerated all 14 selfhost bundles inside clean `build-snap-T750` and verified `--check` across all 5 generator scripts.

### Round 0 Core Implementation

1. **COFF Archive (`.lib`) & Short-Import Object Writer (`compiler/obj/coff.ax`, `compiler/obj/writer.ax`, `compiler/obj/mod.ax`)**:
   - Deterministic `write_coff_archive` (`!<arch>\n`, 60-byte ASCII headers with `Date = "0"`, `Mode = "0"`, `0x0A` even-byte padding, 1st big-endian + 2nd little-endian linker symbol directories, `//` longnames table for member names > 15 bytes) and `write_coff_short_import_object` (`Sig1 = 0x0000`, `Sig2 = 0xFFFF`, `Machine = 0x8664`, `TimeDateStamp = 0`).
2. **COFF Archive Reader, Short-Import Support & Demand-Driven Linker Resolution (`compiler/link/pe.ax`, `compiler/link/import.ax`, `compiler/link/linker.ax`, `compiler/link/mod.ax`)**:
   - `parse_coff_archive` with `AX_LINK_BAD_ARCHIVE` validation, short-import parsing + `FF 25 disp32` indirect jump thunk synthesis, fixed-point demand-driven archive member extraction (`linker_extract_needed_archive_members`), and deterministic `-L`/`-l`/`@link` library resolution with `AX_LINK_LIBRARY_NOT_FOUND` (`data.library`).
3. **Driver `--kind`, CLI Flags & Manifest Wiring (`compiler/driver/opts.ax`, `compiler/driver/pipeline.ax`, `compiler/driver/mod.ax`)**:
   - `--kind <exe|obj|lib|dll>`, `compile` alias, `-L`/`-l`, positional `.obj`/`.lib`/`.a` inputs, `axiom.toml` `[package] kind`, `ARTIFACT_LIB` multi-module archive builds, and `AX_DRIVER_INVALID_ARTIFACT_KIND` diagnostics.

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
- compiler/obj/writer.ax
- tests/link/lib/coff_lib.test
- tests/link/lib/coff_lib_oracle.py
- tests/selfhost/driver/qa_driver_boundary_edges.ax
- tests/selfhost/driver/qa_driver_cli_and_project.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/obj/qa_coff_edge_cases.ax
- tests/selfhost/obj/qa_coff_writer_diff.ax
- tests/selfhost/obj/qa_obj_model.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax

## Verification

- **Stage-1 / Stage-2 / Stage-3 Bootstrap & Fixed-Point (`build-snap-T750`)**:
  - `python build-snap-T750/tools/build_axiomc.py --root build-snap-T750 --out build-snap-T750/build --stage 3 --force`
  - `STAGE1 OK`: `18,011,136` bytes (`sha256=4539097959463058e8e1a98adae3b8792333c0d750a33060883aad9f88a4ec8c`)
  - `STAGE2 (O1) OK`: `10,997,760` bytes (`sha256=62e71e52554ac920059d8e946eddecee532e4be09179bf2ab6452024397f2d9f`)
  - `STAGE3 (O1) OK`: `10,997,760` bytes (`sha256=62e71e52554ac920059d8e946eddecee532e4be09179bf2ab6452024397f2d9f`)
  - `FIXED-POINT (O1) OK`: byte-identical `axiomc2.exe == axiomc3.exe` across two distinct working directories.
- **Targeted Test Suites (`build-snap-T750`, `-j 1`)**:
  - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v link/lib/`: `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
  - `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 1 -v link/ obj/ driver/ selfhost/obj/ selfhost/link/ selfhost/driver/ selfhost/obj_link_driver/`: **`TOTAL 70 PASS 66 FAIL 0 SKIP 4 XFAIL 0`** (0 failures; the 4 `SKIP`s are `requires: axiom0-internal` C-driver tests).
- **Repository & Architecture Gates**:
  - `gen_{obj,link,local_symbols,driver,obj_link_driver}_tests.py --check` (inside `build-snap-T750`): all 14 bundles `up to date`.
  - `python tools/archcheck.py` (inside `build-snap-T750`): `0 violations`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `OK`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T750`: `0` `REFUSED` lines.
  - LF & canonical syntax check: `0` `\r` bytes across all changed files and `T750-report.md`; `0` `:=`, `var`, or `::` tokens in edited `.ax` files.

## Spec Deviations & Notes

- None on observable behavior or binary format. Because `compiler/diag/code.ax` is outside `T750`'s `paths:`, numeric diagnostic IDs `137..139` (`AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`) are defined in `compiler/driver/opts.ax` and `compiler/link/pe.ax` (re-exported via `mod.ax`) and rendered with their canonical symbolic names in both human and `--json` output in `compiler/driver/pipeline.ax`.
- `--kind dll` is accepted by CLI/manifest parsing (`ARTIFACT_DLL`) and gated to `T751` (PE32+ `.dll` writer + companion import `.lib`), while E18.7 conformance stress tests follow in `T773`.

STATUS: COMPLETE round=1
