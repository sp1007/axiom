# T661 Report — E16.3 Canonical AArch64 ISA Backend, AAPCS64 ABI & `aarch64-linux` ELF64 Specification (`SPEC-83`)

## Tóm tắt
Hoàn tất đặc tả chuẩn `spec/SPEC-83-aarch64-linux.md` (`AXS-A64-001`..`AXS-A64-053`) cho kiến trúc backend AArch64 (ARM64), quy ước gọi hàm `CallConv.Aapcs64`, bộ chọn/mã hóa lệnh 32 bit cố định, hạ tầng NEON SIMD / nguyên tử và định dạng ELF64 `EM_AARCH64 = 183` trên `aarch64-linux` thuộc Phase 16 Epic E16.3: mô hình hóa `TargetId.AArch64Linux` tách biệt tầng ISA `Arch.AArch64` tái sử dụng được với `Axiom LIR` không rò rỉ x86/ARM64 (`REQ-TGT-113..116`), tệp thanh ghi `RegisterFile` với quan hệ bí danh `X0..X30` / `W0..W30` qua `RegUnit`, `SP` chuyên biệt tách rời `XZR`/`WZR`, `X29` (`FP`), `X30` (`LR`), `X16`/`X17` (`IP0`/`IP1`), `X18` dành riêng, `V0..V31` (`Q/D/S/H/B`) và `NZCV` (`REQ-TGT-117..122`); chuẩn hóa `CallConv.Aapcs64` (`X0..X7`, `V0..V7` cho `HFA`/`HVA` 1..4 phần tử, cấu trúc `<= 16` byte qua cặp GPR, địa chỉ trả về gián tiếp trong `X8` `XR`/`sret` không chiếm `X0`, bảo toàn `X19..X28` và `D8..D15`, căn chỉnh `SP` 16 byte, `red_zone = 0`, prologue/epilogue `STP`/`LDP`; `REQ-TGT-123..131`); đặc tả chọn lệnh, hằng số tức thời (`MOVZ`/`MOVN`/`MOVK`/bitmask), địa chỉ `ADRP`+`:lo12:`, kiểm tra tràn số (`ADDS`/`SUBS`/`B.VS`/`B.CS`/`B.CC`, `SMULL`/`UMULL`, `SDIV`/`UDIV` có nhánh bảo vệ), IEEE-754 FP/FMA, NEON 128 bit, nguyên tử `LDAR`/`STLR` + vòng lặp LL/SC `LDXR`/`STLXR` + mở rộng Armv8.1-A `+lse` (`CAS`/`LDADD`/`SWP`), `DMB ISH`, volatile/MMIO và `verify_mc` (`REQ-TGT-132..144, 148, 161..163`); đặc tả mã hóa A64 32 bit little-endian tất định, bảng định vị lại ELF64 `EM_AARCH64`, cầu nối nhảy xa veneer `±128 MiB` qua `X16`, `.eh_frame` DWARF CFI / bẫy `BRK #0x1`, điểm vào `_start`, giao diện `std.sys.linux_aarch64` (`X8` + `X0..X5` + `SVC #0` theo `asm-generic/unistd.h`, loại bỏ hoàn toàn các syscall di sản `open`/`stat`/`fork`/`dup2`), ma trận kiểm chứng 4 tầng và bảng truy vết đầy đủ `REQ-TGT-113..165`; đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md` và `spec/invariants.md` (`INV-AARCH-001`..`003`).

## Summary of Changes
1. **`spec/SPEC-83-aarch64-linux.md`**:
   - Completed canonical specification `SPEC-83` with 53 rules (`AXS-A64-001`..`AXS-A64-053`) across 5 sections:
     - §1 `aarch64-linux` Target Description & AArch64 `RegisterFile` (`AXS-A64-001`..`012`)
     - §2 `CallConv.Aapcs64` Calling Convention & `STP`/`LDP` Frame Lowering (`AXS-A64-013`..`023`)
     - §3 AArch64 Instruction Selection, Immediates, Addressing, Overflow, Atomics & NEON (`AXS-A64-024`..`037`)
     - §4 32-Bit Instruction Encoding, `EM_AARCH64` ELF64 Relocations, Veneers, `_start`, `.eh_frame`/`BRK` & `std.sys.linux_aarch64` (`AXS-A64-038`..`049`)
     - §5 Diagnostics, Canonical Examples & E16.3 Traceability (`AXS-A64-050`..`053`, mapping `REQ-TGT-113`..`122` and downstream `REQ-TGT-123`..`165`)
   - Included positive and negative canonical Axiom examples (`=` for bindings/assignment, `.` for paths, `view(x)` / `mut_view(x)`, UTF-8 `"Xin chào thế giới"`) and full `## Sources` citations.
2. **`spec/INDEX.md`**:
   - Registered `spec/SPEC-83-aarch64-linux.md` in §2 (Canonical documents), `AXS-A64-NNN` in §4 (Identifier namespaces), and AArch64 / `SPEC-83` / `0193` in §5 (Topic → canonical source).
3. **`spec/diagnostics.md`**:
   - Updated `AX_TARGET_UNKNOWN_FEATURE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_UNSUPPORTED_OP`, `AX_VERIFY_MC_ILLEGAL`, `AX_LINK_TEXTREL_FORBIDDEN`, and `## Sources` to reference `SPEC-83` (`E16.3`).
4. **`spec/invariants.md`**:
   - Registered the `AARCH` invariant group in §1, added §37 (`INV-AARCH-001` for `T662`, `INV-AARCH-002` for `T663`, `INV-AARCH-003` for `T664`), and updated `## Sources`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`gaps: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (598 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T661` → exit 0 with 0 `REFUSED` lines.

## Files changed
- spec/SPEC-83-aarch64-linux.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Status
STATUS: COMPLETE round=0
