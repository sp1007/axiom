STATUS: COMPLETE round=1

# T685 Report — E16.10 Artifact Kinds & Library Matrix Specification (`SPEC-89`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-89-artifact-library-matrix.md` (`AXS-ARTM-001..040`, 40 quy tắc đánh số liên tục không trùng lặp toàn cục) và đăng ký vào `spec/INDEX.md`, `spec/diagnostics.md`, cùng `spec/invariants.md` (`INV-ARTM-001..005`, mục §43). Tài liệu thống nhất ma trận thành phẩm đầu ra `--kind <exe|bin|obj|lib|staticlib|dll|cdylib|axlib|wasm-module>` xuyên suốt PE/COFF, ELF64 (Linux, Android Bionic 16 KiB, RISC-V64), Mach-O 64, UEFI `.efi`, và WebAssembly (`_start` Command so với `_initialize` Reactor); chuẩn hóa định dạng kho lưu trữ tĩnh tất định `!<arch>\n` (`CoffAr`, `GnuAr` + `/SYM64/`, `BsdAr` `#1/<len>` căn lề 8 byte + `__.SYMDEF SORTED`/`__.SYMDEF_64`) và gói `.axlib` nhúng `lib.axrmeta`; quy định chi tiết tệp `.def` và thư viện nhập khẩu `.lib` trên Windows, đánh số phiên bản biểu tượng GNU (`VERSYM`/`VERDEF`/`VERNEED`, `--version-script`) trên ELF64, không gian tên hai mức (`MH_TWOLEVEL`) + `@rpath` + bộ ba phiên bản `X.Y.Z` + `LC_REEXPORT_DYLIB` trên macOS, cô lập hiển thị biểu tượng mặc định ẩn cho `cdylib`, thuật toán trích xuất điểm bất động so với `--whole-archive`/`-force_load`, phân giải biểu tượng kim cương, và quy tắc tước bỏ 100% phân đoạn `.axmeta`/`.axmir`/`.axlto` khỏi ảnh thực thi/thư viện động cuối.

## Round 1 QA Fixes (`T685-qa.md` Findings 1–3)
1. **Finding 1 — `SPEC-24` `ArtifactHeader` Per-Family Magic & Payload Placement (`AXS-ARTM-013..014`, `AXS-ARTM-028..029`, `AXS-ARTM-032`):**
   - Replaced all `"AXART\x00\x01\x00"` placeholders with `SPEC-24`'s canonical per-family 8-byte ASCII `ArtifactHeader.magic` values and `format_family` tags: `"AXMI0001"` (`format_family = 1`) for `lib.axrmeta` (`.axmi`), `"AXMETA01"` (`format_family = 4`) for `.axmeta`, `"AXMIR001"` (`format_family = 2`) for `.axmir`, and `"AXLTO001"` (`format_family = 3`) for `.axlto` (rejecting any magic or `format_family` mismatch immediately with `AX_LINK_BAD_ARTIFACT`).
   - Clarified that the 64-byte `ArtifactHeader` stores `target_fingerprint`, `interface_fingerprint`, and BLAKE3-128 `content_hash`, whereas canonical `PackageName`/`PackageId` (`SemanticKey`) and `AbiFingerprint` reside inside `.axmi` / `.axmeta` payload sections (`SPEC-24 AXS-ART-002, AXS-ART-010..014, AXS-ART-021..023`).
2. **Finding 2 — `axiomc run --kind <non-exe>` Diagnostic Alignment (`AXS-ARTM-002`, `AXS-ARTM-032`, `AXS-ARTM-038`, `spec/diagnostics.md`):**
   - Aligned `SPEC-89` (`AXS-ARTM-002` item 3, `AXS-ARTM-032` row `E8900`, `AXS-ARTM-038` negative examples `0a`/`0b`) and `spec/diagnostics.md` (`:168`, `:678`) with `SPEC-26` (`AXS-WLIB-002`, `AXS-WLIB-050`) and `compiler/driver/opts.ax:1385-1386, 1866-1869`: passing a recognized non-`Executable` `--kind` (`obj`, `lib`, `staticlib`, `dll`, `cdylib`, `axlib`, `rlib`, `wasm-module`, `wasm-reactor`, or `--emit=obj`) to `axiomc run` fails with **`AX_DRIVER_USAGE`** (exit code `2`), while `AX_DRIVER_INVALID_ARTIFACT_KIND` (exit code `2`) is reserved strictly for unknown `--kind` / manifest `kind` strings and target-incompatible artifact kinds (`wasm-module`/`wasm-reactor` on non-WASM; `dll`/`cdylib` on `<arch>-none`).
3. **Finding 3 — Cross-`SPEC` Rule IDs & Contiguous Rule Ranges (`SPEC-89` & `spec/invariants.md` §43):**
   - Fixed every cross-`SPEC` rule citation and split gapped ranges across `SPEC-89` and `spec/invariants.md` §43: `SPEC-88 AXS-XCMP-009` (`target/<triple>/<profile>/`), `SPEC-84 AXS-MACHO-001, AXS-MACHO-013, AXS-MACHO-020..021` (`MH_DYLIB` & header flags), `SPEC-56 AXS-MOD-012` (`_DllMainCRTStartup` + `__ax_resolve_module_bindings()`), `SPEC-85 AXS-ANDR-010..012` (`ET_DYN` `.so`, `16 KiB` `0x4000` `PT_LOAD`, `.note.android.ident`), `SPEC-88 AXS-PLAT-012` (runtime `DynLib.open` + `LibSymbol<T>`), `SPEC-54 AXS-PAN-020` (`@export` FFI no-unwind barrier, alongside `AXS-PAN-010` for reverse-order local `Drop` cleanup), `SPEC-24 AXS-ART-020` + `SPEC-27 AXS-LNK-004` (pure encoder -> `ObjectWriter` handoff), `SPEC-24 AXS-ART-001..005, AXS-ART-010..014`, and `SPEC-26 AXS-WLIB-020..023, AXS-WLIB-030..032`.

## Architectural Decisions & Alignment Notes
1. **Collision-free Rule & Invariant Namespaces (`AXS-ARTM-001..040`, `INV-ARTM-001..005`)**: Uses the dedicated prefix `AXS-ARTM-001..040` (`0` gaps, `0` global duplicates across `spec/`) and `INV-ARTM-001..005` (§43 of `spec/invariants.md`, `IG-1..IG-4` compliant), keeping `SPEC-24`'s `AXS-ART-*` / `INV-ART-*` and `SPEC-26`'s `AXS-WLIB-*` / `INV-WLIB-*` intact.
2. **Unified `--kind` Flag & Synonym Normalization (`AXS-ARTM-002`)**: Preserves Axiom's canonical `--kind <exe|obj|lib|dll|axlib>` surface across `SPEC-26` and `SPEC-80`..`SPEC-88` while normalizing `bin -> exe`, `staticlib -> lib`, `cdylib -> dll`, `wasm-module`/`wasm-reactor -> dll` (on `wasm32-*`), `rlib -> axlib`, and `--emit=obj -> obj` before cache-key construction.
3. **Harmonized Deterministic Archive Modes (`AXS-ARTM-009`)**: Reconciles `SPEC-26` (`CoffAr`: `"0       "`), `SPEC-80`/`SPEC-86` (`GnuAr`: `"0       "` on `/`, `/SYM64/`, `//` pseudo-members and `"100644  "` on regular members), and `SPEC-84` (`BsdAr`: `"100644  "` with `#1/<byte_len>` chosen via `align_up(hdr_off + 60 + len(name) + 1, 8) - (hdr_off + 60)` so embedded `MH_OBJECT` headers sit on exact 8-byte file boundaries).
4. **Canonical `AX_<AREA>_<NAME>` Diagnostics (`AXS-ARTM-032`)**: Maps task-card shorthand `E8900–E8919` onto `DRIVER`, `FFI`, and `LINK` codes per `ADR-0011` / `AXD-021`, registering 7 new `LINK` codes alongside 16 reused canonical `DRIVER`/`FFI`/`LINK` codes.

## Verification Summary
- Programmatic Round 1 zero-defect audit (`verify_round1.py`): `0` CRLF bytes across all touched files, contiguous `AXS-ARTM-001..040`, `0` global duplicate `AXS-*` or `INV-*` IDs, `0` occurrences of `"AXART"`, `100%` verified `spec/*.md` paths, `100%` existing & gap-free external `AXS-*` citations/ranges matching their exact rule subjects, `100%` registered `AX_*` diagnostics and `REQ-*` IDs, `IG-1..IG-4` invariant schema compliance, and canonical Axiom syntax (`=` only, `.` paths only, `view`/`mut_view`, exact UTF-8 `"Xin chào thế giới"`).
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T685`: `0` `REFUSED`.

## Files changed
- spec/SPEC-89-artifact-library-matrix.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
