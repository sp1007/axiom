# T665 Report — E16.4 Canonical macOS AArch64 Darwin ABI, Mach-O 64 Object/Image & Ad-Hoc Codesign Specification (`SPEC-84`)

## Tóm tắt
Hoàn tất đặc tả chuẩn `spec/SPEC-84-macos-aarch64-macho.md` (`AXS-MACHO-001`..`AXS-MACHO-036`) cho đích `aarch64-macos` (Apple Silicon Darwin ARM64) thuộc Phase 16 Epic E16.4: tái sử dụng toàn bộ tầng ISA `Arch.AArch64` (`SPEC-83`) đồng thời chuyên biệt hóa `CallConv.Aapcs64Darwin` (khóa cứng thanh ghi nền tảng `X18`, bên gọi/nhận mở rộng dấu/không dấu cho tham số `< 32` bit trong `W0..W7`, xếp chặt tham số tràn ngăn xếp không biến thiên theo kích thước và căn chỉnh tự nhiên `1/2/4/8/16` byte, không làm tròn cặp thanh ghi chẵn cho tham số 16 byte, đặt toàn bộ tham số biến thiên `...` lên ngăn xếp theo ô `8` byte với `va_list = *mut u8`, vùng đỏ `128` byte cho hàm lá, bắt buộc chuỗi khung `X29` `FP`, tiền tố `_` cho ký hiệu Mach-O, và tách Pointer Authentication `pauth` khỏi ngữ nghĩa lõi `REQ-TGT-147`, `REQ-TGT-296`..`298`); đặc tả tệp đối tượng `MH_OBJECT` (`MH_MAGIC_64 = 0xFEEDFACF`, `CPU_TYPE_ARM64 = 0x0100000C`, `MH_SUBSECTIONS_VIA_SYMBOLS`, ánh xạ tiết đoạn `__TEXT`/`__DATA_CONST`/`__DATA`, tập định vị lại `ARM64_RELOC_*` theo trang phần cứng 4 KiB của `ADRP`, `tlv_descriptor` cho `@thread_local`, và kho lưu trữ tĩnh BSD 4.4 `ar` tất định `__.SYMDEF SORTED`); đặc tả trình liên kết Mach-O 64 bản địa cho `MH_EXECUTE` & `MH_DYLIB` (căn chỉnh phân đoạn 16 KiB `0x4000` tuân thủ W^X, `__TEXT,__stubs` + `__DATA_CONST,__got`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, danh mục `libSystem.B.dylib` tích hợp sẵn và bộ đọc `.tbd`/`.dylib` không phụ thuộc Xcode/`ld64`, cùng khối chữ ký mã ad-hoc `LC_CODE_SIGNATURE` băm SHA-256 từng trang 4 KiB với `CS_ADHOC | CS_LINKER_SIGNED`); và đặc tả tầng hệ điều hành `std.sys.macos` qua `libSystem.B.dylib` (cấm phát syscall thô `SVC #0x80`, cấu trúc `stat` 144 byte / `dirent` / cờ `O_*` của Darwin ARM64, `kqueue`/`kevent64`, `pthread`/`__ulock_*`, sợi `fiber` 160 byte bảo toàn `X18`, Compact Unwind `__TEXT,__unwind_info`, và ma trận kiểm chứng E16.4 cho `T666`–`T668`, `T689`); đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-MACHO-001`..`003`).

## Summary
1. **`spec/SPEC-84-macos-aarch64-macho.md`**:
   - Authored canonical specification `SPEC-84` with 36 rules (`AXS-MACHO-001`..`AXS-MACHO-036`) across 5 sections:
     - §1 `aarch64-macos` Target Identity, Layering & Apple ARM64 Darwin ABI (`AXS-MACHO-001`..`011`)
     - §2 Mach-O 64 Object Model (`MH_OBJECT`), Sections, `ARM64_RELOC_*` Relocations, Darwin TLV & Deterministic BSD `ar` (`AXS-MACHO-012`..`019`)
     - §3 Mach-O 64 Native Linker (`MH_EXECUTE`, `MH_DYLIB`), 16 KiB Segment Layout, `__stubs`+`__got`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE` & Self-Contained SHA-256 Ad-Hoc `LC_CODE_SIGNATURE` (`AXS-MACHO-020`..`026`)
     - §4 macOS Platform Boundary, Hermetic `.tbd` / Built-In `libSystem.B.dylib`, `std.sys.macos` & Compact Unwind (`AXS-MACHO-027`..`032`)
     - §5 Diagnostics, Canonical Positive/Negative Axiom Examples & E16.4 Requirement Traceability (`AXS-MACHO-033`..`036`, mapping `REQ-TGT-147`, `REQ-TGT-296`..`303`, `REQ-TGT-311`..`317`)
2. **`spec/INDEX.md`**:
   - Registered `spec/SPEC-84-macos-aarch64-macho.md` in §2, `AXS-MACHO-NNN` in §4, and Mach-O / `SPEC-84` / `0196` in §5.
3. **`spec/diagnostics.md`**:
   - Updated `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_FEATURE_MISMATCH`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_EXPORT`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_UNSUPPORTED_OP`, `AX_VERIFY_MC_ILLEGAL`, `AX_LINK_TEXTREL_FORBIDDEN`, and `## Sources` to reference `T666`/`T667` and `SPEC-84`.
4. **`spec/invariants.md`**:
   - Registered the `MACHO` group in §1, added §38 (`INV-MACHO-001` for `T666`, `INV-MACHO-002` for `T667`, `INV-MACHO-003` for `T668`), and updated `## Sources`.

## Round 1 Fixes (`_workspaces/reports/T665-qa.md` `[F1]`..`[F4]`)
1. **`[F1 — BLOCKER]` Exact 88-Byte `CS_CodeDirectory` (`v0x00020400`) Header Layout & Relative Offset Bases (`AXS-MACHO-025`, `AXS-MACHO-026`, `INV-MACHO-002..003`):**
   - Added mandatory `length: u32be = total_sig_bytes - 20` (`= cd_len = 88 + ident_len_with_nul + 32 * nCodeSlots`) at byte offset `+4` of `CS_CodeDirectory`, with explicit byte offsets for all 21 `CS_CodeDirectory` fields (`+0` `magic = 0xFADE0C02`, `+4` `length`, `+8` `version = 0x00020400`, `+12` `flags = 0x00020002`, `+16` `hashOffset`, `+20` `identOffset`, `+24` `nSpecialSlots`, `+28` `nCodeSlots`, `+32` `codeLimit`, `+36` `hashSize`, `+37` `hashType`, `+38` `platform`, `+39` `pageSize = 12`, `+40` `spare2`, `+44` `scatterOffset`, `+48` `teamOffset`, `+52` `spare3`, `+56` `codeLimit64`, `+64` `execSegBase`, `+72` `execSegLimit`, `+80` `execSegFlags` $\rightarrow$ 88-byte header).
   - Specified explicitly that `CS_BlobIndex.offset = 20` is relative to `CS_SuperBlob` (`sig_off`), whereas `identOffset = 88` and `hashOffset = 88 + ident_len_with_nul` are relative to `CS_CodeDirectory` (`sig_off + 20`), with `total_sig_bytes = 20 + cd_len = 108 + ident_len_with_nul + 32 * nCodeSlots`.
2. **`[F2 — MAJOR]` Exact `REQ-TGT-314..317` (`ABACKEND-89..92`) Semantics & Corpus Citations (`SPEC-84`, `spec/invariants.md`):**
   - Updated `AXS-MACHO-032`, `AXS-MACHO-036`, and `INV-MACHO-003` so `REQ-TGT-314..317` (`0524 §112 ABACKEND-89..92`) state their exact catalog definitions (distinct instruction sequences representing identical `LIR` semantics; assembly goldens non-authoritative for semantics; `--interp` reference + differential execution validation; target-independent semantic backend conformance tests), while citing `ABACKEND-94` (`tasks/0453 §194.31`) for `TargetFingerprint` cache identity and `ABACKEND-95` / `AMACHO-36` / `AIMG-46..47` for deterministic builds.
   - Corrected all shifted corpus anchors across `SPEC-84` and `spec/invariants.md`: `0196 §23, §40 AMACHO-35` & `tasks/0563 §304.25, §304.45 AIMG-45, 52` for Mach-O code signing; `0196 §24, §40 AMACHO-36` & `tasks/0563 §304.37–38, §304.45 AIMG-46..47` for `LC_UUID` / deterministic Build ID; `0217 §10, §51, §72 ALINK-36` & `0220 §16` for Darwin TLV (`AXS-MACHO-018`); `0196 §25–26, §40 AMACHO-33` (`SPEC-93`) for `__DWARF,__debug_*` (`AXS-MACHO-031`); `0217 §19, §37, §44, §72 ALINK-28..29, 50` for BSD `ar` archives (`AXS-MACHO-019`); `0196 §9–10, §40 AMACHO-27` for symbolic relocations (`AXS-MACHO-017`); `0220 §7, §14–31, §39 AOS-20..40` for `std.sys.macos` (`AXS-MACHO-030`); and `spec/SPEC-26-windows-artifact-kinds.md` / `spec/SPEC-55-fixed-address-declarations.md` in `## Sources`.
3. **`[F3 — MAJOR]` Accurate Downstream Task Ownership (`T666`, `T667`, `T668`, `T685`, `T689`, `T690`) (`SPEC-84`, `spec/invariants.md`, `spec/INDEX.md`):**
   - Updated `AXS-MACHO-030`, `AXS-MACHO-036`, and `INV-MACHO-002..003` so `std/sys/macos` implementation is attributed to `T667` alongside `compiler/link/macho`, while `T668` (`tests/conformance/p16/e16_4_macos_aarch64`) is the E16.4 conformance and differential execution suite feeding `E16.10` cross-target artifact/library matrix (`T685`–`T688`, `SPEC-89`) and `E16.11` universal/multi-arch Mach-O Fat artifacts (`T689`–`T692`, `SPEC-90`).
4. **`[F4 — MINOR]` `tlv_descriptor.offset` Relocation vs Chained Fixup Exclusion & `section_64` Field Order (`AXS-MACHO-014`, `AXS-MACHO-018`, `AXS-MACHO-023`):**
   - Specified in `AXS-MACHO-018` and `AXS-MACHO-023` (and `INV-MACHO-001..002`) that `tlv_descriptor.offset` (`+16` in `S_THREAD_LOCAL_VARIABLES` `__DATA,__thread_vars`) emits `ARM64_RELOC_UNSIGNED` in `MH_OBJECT` (`T666`) and is resolved statically by `compiler/link/macho` (`T667`) to `(S + A) - tls_template_base_vma` **without** emitting a `DYLD_CHAINED_PTR_64_OFFSET` (`bind == 0`) rebase entry (unlike `+0` `_tlv_bootstrap` `bind == 1` and `+8` `key = 0`).
   - Explicitly specified in `AXS-MACHO-014` (and `INV-MACHO-001`) that the 80-byte binary `section_64` struct serializes `sectname: [16]u8` first at `+0..16` and `segname: [16]u8` second at `+16..32`.

## Files changed
- spec/SPEC-84-macos-aarch64-macho.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` — PASS (`COVERAGE OK`, 0 gaps)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` — PASS (`HARNESS OK`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` — PASS
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T665` — PASS (0 `REFUSED` lines)

## Spec deviations: none

## Follow-ups: none

STATUS: COMPLETE round=1
