# T650 Report — E16.9 Canonical Linux x86-64 SysV ABI, ELF64 Object & Static ELF Executable Specification (`SPEC-80`)

## Tóm tắt
Hoàn tất đặc tả chuẩn `spec/SPEC-80-linux-x86-64-elf-static.md` (`AXS-ELFS-001`..`AXS-ELFS-053`) cho mục tiêu `x86_64-linux` thuộc Phase 16 Epic E16.9: định nghĩa `TargetDesc` và ranh giới chia sẻ kiến trúc x86-64 với `x86_64-windows`, quy ước gọi hàm `CallConv.SysV64` (phân loại eightbyte `NO_CLASS`/`INTEGER`/`SSE`/`MEMORY`, thanh ghi `RDI, RSI, RDX, RCX, R8, R9` và `XMM0..XMM7`, trả về kép `RAX:RDX`/`XMM0:XMM1`, `sret`, red-zone 128 byte ở hàm lá và cờ `-mno-red-zone`), bộ phát/đọc tệp đối tượng relocatable ELF64 (`ET_REL`, `.rela.*`, `.axmeta`, `.axlto`, kho lưu trữ tĩnh GNU `ar`), trình liên kết tĩnh tích hợp tạo tệp thực thi ELF64 (`ET_EXEC` tại `0x400000`, phân đoạn `PT_LOAD` tuân thủ W^X, stub khởi chạy `_start` đọc `argc`/`argv`/`envp` trực tiếp từ stack nhân Linux mà không phụ thuộc `libc`/`ld.so`), tầng syscall nguyên thủy `std.sys.linux` (`0F 05`, ánh xạ `-errno` sang mã lỗi âm `SPEC-04 AXS-EXT-110`, `mmap`, `futex`, `clone`, `io_uring`/`epoll`, tích hợp WSL cho `axtest.py`), cùng cập nhật `spec/INDEX.md`, `spec/diagnostics.md` và `spec/invariants.md` (`INV-ELFS-001`..`INV-ELFS-003`).

## Summary of Changes
1. **`spec/SPEC-80-linux-x86-64-elf-static.md`**:
   - Authored canonical specification `SPEC-80` with 53 rules (`AXS-ELFS-001`..`AXS-ELFS-053`) across 6 sections:
     - §1 Target Descriptor & Shared x86-64 Architecture Boundary (`AXS-ELFS-001`..`AXS-ELFS-009`)
     - §2 System V AMD64 Calling Convention (`CallConv.SysV64`) (`AXS-ELFS-010`..`AXS-ELFS-020`)
     - §3 ELF64 Relocatable Object Writer, Reader & Static Archive Format (`AXS-ELFS-021`..`AXS-ELFS-029`)
     - §4 Integrated Static ELF64 Executable Linker & `_start` Entry Stub (`AXS-ELFS-030`..`AXS-ELFS-039`)
     - §5 Linux Raw Syscall Substrate (`std.sys.linux`) & `std.*` Pal Mapping (`AXS-ELFS-040`..`AXS-ELFS-049`)
     - §6 Diagnostics, Conformance Examples & Traceability (`AXS-ELFS-050`..`AXS-ELFS-053`)
   - Included positive and negative canonical Axiom examples (`=` bindings, `.` block delimiter, `view(x)` / `mut_view(x)`, UTF-8 Vietnamese output) and full `## Sources` citations.
2. **`spec/INDEX.md`**:
   - Registered `SPEC-80` in §2 (Canonical documents), `AXS-ELFS-NNN` in §4 (Identifier namespaces), and Linux x86-64 SysV ABI / ELF64 object / static executable / `std.sys.linux` entries in §5 (Where to look for a topic).
3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` and §11 Linker diagnostics (`AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`) to cover ELF64 (`ET_REL` / `ET_EXEC`) and GNU `ar` `.a` archives alongside COFF/PE, and added `SPEC-80` to `## Sources`.
4. **`spec/invariants.md`**:
   - Added `ELFS` to the `Groups:` header in §1, added §34 (`INV-ELFS-001` for `T066`, `INV-ELFS-002` for `T651`, `INV-ELFS-003` for `T652`), and updated `## Sources`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`gaps: 0`; `REQ-TGT-002`, `REQ-TGT-003`, `REQ-TGT-037`, `REQ-TGT-038`, `REQ-TGT-039`, `REQ-TGT-040` covered).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T650` → verified all 4 modified files match allowed/locked paths with 0 refused files.

## Files changed
- spec/SPEC-80-linux-x86-64-elf-static.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Status
STATUS: COMPLETE round=0