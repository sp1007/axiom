# T657 Report — E16.2 Canonical Linux ELF Dynamic Linking, PIE, GOT/PLT, `.so` & `libc` Interop Specification (`SPEC-82`)

## Tóm tắt
Hoàn tất đặc tả chuẩn `spec/SPEC-82-linux-elf-dynamic.md` (`AXS-ELFD-001`..`AXS-ELFD-053`) cho liên kết động ELF64 trên Linux x86-64 thuộc Phase 16 Epic E16.2: định nghĩa sự tách biệt giữa ELF tĩnh (`ET_EXEC`, `SPEC-80`) và ELF động (`ET_DYN` tại cơ sở tương đối `0x0`), tệp thực thi độc lập vị trí (`PIE` với `PT_PHDR`, `PT_INTERP` `/lib64/ld-linux-x86-64.so.2`, `DF_1_PIE`) và thư viện chia sẻ (`--kind dll` tạo `lib<name>.so` với `DT_SONAME`), cố định kích thước lệnh, giãn nhánh (`branch relaxation`), căn chỉnh mã máy và bảo toàn nguồn gốc gỡ lỗi trước khi ghi đối tượng (`REQ-TGT-061..065`); quy định sinh mã `PIC`, truy cập `RIP`-relative cục bộ (`R_X86_64_PC32`), nạp địa chỉ gián tiếp qua `.got` (`R_X86_64_GOTPCREL`/`R_X86_64_REX_GOTPCRELX` kèm giãn `mov` $\rightarrow$ `lea`, `REQ-TGT-066`), gọi hàm qua `.plt`/`.got.plt` 16 byte (`R_X86_64_PLT32`), các bản ghi định vị lại động `.rela.dyn`/`.rela.plt` (`R_X86_64_RELATIVE`, `R_X86_64_GLOB_DAT`, `R_X86_64_JUMP_SLOT`, `R_X86_64_64`), cấm định vị lại trên phân đoạn mã `DT_TEXTREL` (`AX_LINK_TEXTREL_FORBIDDEN`), bảo toàn đồng nhất địa chỉ hàm qua `.got` (`AMACHINE-79`, `REQ-TGT-067..068`), và mô hình ELF TLS (`Initial-Exec` `R_X86_64_GOTTPOFF` và `General-Dynamic` `R_X86_64_TLSGD`, `REQ-TGT-145..146`, `REQ-TGT-182`); quy định các phân đoạn động (`.dynsym`, `.dynstr`, `.gnu.hash`, `.dynamic`, `.init_array`/`.fini_array`), mặc định Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`) và `PT_GNU_STACK` (`PF_R | PF_W`), hiển thị ký hiệu (`STV_DEFAULT` cho `@export`, `STV_HIDDEN` mặc định cho ký hiệu nội bộ) và phiên bản ký hiệu GNU (`SHT_GNU_versym`, `SHT_GNU_verneed`, `SHT_GNU_verdef`); đồng thời quy định tương tác `libc.so.6`, `libm.so.6`, `libpthread`, và `std.sys.linux_dl` (`dlopen`/`dlsym`/`dlclose`/`dlerror`/`DynLib`) cùng cập nhật `spec/INDEX.md`, `spec/diagnostics.md` và `spec/invariants.md` (`INV-ELFD-001`..`003`).

## Summary of Changes
1. **`spec/SPEC-82-linux-elf-dynamic.md`**:
   - Authored canonical specification `SPEC-82` with 53 rules (`AXS-ELFD-001`..`AXS-ELFD-053`) across 5 sections:
     - §1 Static vs Dynamic ELF Separation, `PIE` Executables & Shared Objects (`AXS-ELFD-001`..`010`)
     - §2 PIC Codegen, GOT/PLT Lowering, Dynamic Relocations, TLS & Function Identity (`AXS-ELFD-011`..`021`)
     - §3 ELF64 Dynamic Sections, Program Headers, RELRO, Visibility & GNU Versioning (`AXS-ELFD-022`..`035`)
     - §4 `libc`, `libm`, `libpthread` & `libdl` (`dlopen`/`dlsym`) Interoperability (`AXS-ELFD-036`..`045`)
     - §5 Diagnostics, Canonical Examples & Traceability (`AXS-ELFD-046`..`053`)
   - Included positive and negative canonical Axiom examples (`=` for binding/assignment, `.` for paths, `view(x)`, UTF-8 Vietnamese output) and full `## Sources` citations.
2. **`spec/INDEX.md`**:
   - Registered `SPEC-82` in §2 (Canonical documents), `AXS-ELFD-NNN` in §4 (Identifier namespaces), and Linux ELF64 dynamic linking / `PIE` / `GOT`/`PLT` / `.so` / `std.sys.linux_dl` entries in §5 (Topic → canonical source).
3. **`spec/diagnostics.md`**:
   - Updated `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_EXPORT`, and `AX_LINK_ARTIFACT_TARGET_MISMATCH` to reference `SPEC-82`, added `AX_LINK_TEXTREL_FORBIDDEN` (`T658/T659`), and added `SPEC-82` to `## Sources`.
4. **`spec/invariants.md`**:
   - Added `ELFD` (and `TGTD`) to the `Groups:` header in §1, added §36 (`INV-ELFD-001` for `T658`, `INV-ELFD-002` for `T658`/`T659`, `INV-ELFD-003` for `T659`), and updated `## Sources`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T657` → verified all 4 modified files match allowed/locked paths with 0 refused files.

## Files changed
- spec/SPEC-82-linux-elf-dynamic.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Status
STATUS: COMPLETE round=0
