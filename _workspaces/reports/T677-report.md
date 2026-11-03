STATUS: COMPLETE round=1

# T677 Report — E16.7 Canonical RISC-V 64 (`RV64GC`) Backend, `LP64D` psABI & `riscv64-linux` ELF64 Specification (`SPEC-87`)

## Tóm tắt

Hoàn thành đặc tả kiến trúc chuẩn `spec/SPEC-87-riscv64-linux.md` (51 quy tắc liên tục `AXS-RV64-001`..`AXS-RV64-051`, LF-only, 0 khoảng trống, 0 trùng lặp) và cập nhật đồng bộ ba tài liệu danh mục nền (`spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`) cho phân hệ `E16.7` (`T677`–`T680`, Phase `P16`), đồng thời xử lý triệt để toàn bộ 4 phát hiện QA ở `round=0` (`_workspaces/reports/T677-qa.md`):
- **Định danh đích, `RV64GC` mô-đun, `DataLayout` & `RegisterFile` (`AXS-RV64-001`..`011`):** Chuẩn hóa `TargetId.Riscv64Linux` (`Arch.RiscV64, Os.Linux, CallConv.RiscV, ObjectFormat.Elf64`), tách biệt `RV64GC` thành tập bit tính năng tường minh `{i, m, a, f, d, zicsr, zifencei, c}` kèm đồ thị phụ thuộc (`+v`, `+zba`, `+zbb`, `+zbc`, `+zbs`, `+zbkb`, `+zicond`, `+zacas`, `+zicfiss`, `+zicfilp`, `CustomExtensionDesc`), `DataLayout` 64-bit little-endian (`XLEN = 64`, `FLEN = 64`, `stack_align = 16`, `red_zone = 0`, `page_size = 4096`), `x0` `ZeroReg` không cấp phát, `sp`/`gp`/`tp` dành riêng vĩnh viễn, bất biến **NaN-boxing** `[63:32] = 0xFFFF_FFFF` cho `f32` trên `f0..f31`, và phân lớp vector khả mở `v0..v31` (`RVV 1.0`) tách biệt hoàn toàn với SIMD độ rộng cố định.
- **Chọn lệnh không thanh ghi cờ (*Flagless ISel*), Số học có kiểm tra, Nguyên tử RVWMO & Dấu phẩy động (`AXS-RV64-012`..`020`):** Chuẩn hóa tạo giá trị `bool` bằng `SLT`/`SLTU`/`SEQZ`/`SNEZ`, hợp nhất so sánh-nhánh trực tiếp (`BEQ`/`BNE`/`BLT`/`BGE`/`BLTU`/`BGEU`), chuỗi kiểm tra tràn hai thanh ghi cho `add`/`sub`/`mul`/`neg`/`shl`, nhánh tiền kiểm bắt buộc trước `DIV*`/`REM*`, rút gọn mô-đun 12/32-bit chính xác tại biên bù dấu `+0x800` `[0x7FFF_F800, 0x7FFF_FFFF]` cho cả hằng `LUI + ADDIW` (`AXS-RV64-015`) lẫn địa chỉ tải/lưu độ lệch lớn (`AXS-RV64-016`), ánh xạ nguyên tử RVWMO (`AMO*`, vòng lặp `LR`/`SC` bảo đảm tiến triển, `FENCE r, rw` / `rw, w` / `rw, rw`), `Volatile`/MMIO (`FENCE io, io`), và ép kiểu bão hòa float-to-int xóa tường minh `NaN -> 0`.
- **Quy ước gọi `LP64D` (`CallConv.RiscV`) & Khung ngăn xếp (`AXS-RV64-021`..`031`):** Chuẩn hóa truyền `a0..a7` + `fa0..fa7`, mở rộng dấu bắt buộc từ bit 31 cho **cả `i32` lẫn `u32`**, làm phẳng phần cứng `{FP}`, `{FP, FP}` (kể cả `{f32, f64}` hỗn hợp), `{INT, FP}` / `{FP, INT}`, tách biên `a7` + `[sp + 0]`, truyền bản sao tham chiếu do caller cấp phát cho kiểu `> 16` byte, con trỏ ẩn `sret` trong `a0`, quy tắc hàm bất định `...` (chỉ dùng GPR/stack, căn cặp chẵn `a(2k):a(2k+1)` cho đối số căn 16 byte, `va_list = *mut u8`), khung `ra` + `s0/fp` căn 16 byte không vùng đỏ và thăm dò trang bảo vệ 4 KiB (`ADR-0003`).
- **`verify_mc`, Mã hóa RV64GC + `RVC`, Đối tượng/Liên kết `EM_RISCV` ELF64, TLS & `std.sys.linux_riscv64` (`AXS-RV64-032`..`051`):** Chuẩn hóa kiểm chứng máy trước mã hóa, mở rộng toàn bộ giả lệnh trước mã hóa, định dạng lệnh 32-bit (`R/R4/I/S/B/U/J`) + nén 16-bit `RVC` bảo toàn ngữ nghĩa, ELF64 `EM_RISCV = 243` (`e_flags = 0x0005`, `.riscv.attributes` `SHT_RISCV_ATTRIBUTES = 0x70000003`), bảng định vị lại đầy đủ với bất biến gián tiếp `R_RISCV_PCREL_LO12_I`/`S` trỏ về nhãn `AUIPC` trên miền `[-0x8000_0800, +0x7FFF_F7FF]` chạy đúng không phụ thuộc `R_RISCV_RELAX`, liên kết tĩnh/`PIE` (`/lib/ld-linux-riscv64-lp64d.so.1`)/`.so`, TLS Variant I qua `tp`, `.eh_frame` DWARF, giao diện nhân `ecall` (`asm-generic/unistd.h` + `SYS_riscv_hwprobe = 258` + `SYS_riscv_flush_icache = 259`), chuyển ngữ cảnh fiber 208 byte, ví dụ dương/âm chuẩn cú pháp `=` và `.`, cùng ma trận truy vết đầy đủ `REQ-TGT-166`..`REQ-TGT-206`.

## Round 1 QA Fixes (`_workspaces/reports/T677-qa.md`)

1. **Finding 1 — Biên mở rộng dấu 32-bit `+0x800` tại `[0x7FFF_F800, 0x7FFF_FFFF]` (`AXS-RV64-015`, `AXS-RV64-016`, `AXS-RV64-038`):**
   - Trong `AXS-RV64-015` mục 2 (`[-2^31, 2^31 - 1]`): sửa công thức `lo12` thành `lo12 = sext12(val & 0xFFF)` (tương đương `sext32(val - (hi20 << 12)) ∈ [-2048, 2047]`), nêu rõ trên miền `[0x7FFF_F800, 0x7FFF_FFFF]` (bao gồm `i32.MAX = 0x7FFF_FFFF`), `hi20 = 0x80000` (`LUI` nạp `-0x8000_0000`) và `ADDIW` cộng quay vòng modulo `2^32` với `lo12 ∈ [-2048, -1]` trước khi mở rộng dấu bit 31 (`0`) ra `[63:32]`.
   - Trong `AXS-RV64-016` mục 3 (địa chỉ tải/lưu độ lệch lớn): giới hạn chuỗi `LUI t0, hi20; ADD t0, base, t0; LD/SD val, lo12(t0)` (`lo12 = sext12(Offset & 0xFFF)`) **chỉ** áp dụng cho `Offset ∈ [-0x8000_0800, +0x7FFF_F7FF]`; với `Offset ∉ [-0x8000_0800, +0x7FFF_F7FF]` — đặc biệt bao gồm `[+0x7FFF_F800, +0x7FFF_FFFF]` nơi `LUI t0, 0x80000` mở rộng dấu thành `-0x8000_0000` làm lệch phép `ADD` 64-bit đi `-2^32` — bắt buộc nạp đầy đủ `Offset` vào `t0` theo `AXS-RV64-015` rồi thực thi `ADD t0, base, t0; LD/SD val, 0(t0)`. Đồng thời ghi tường minh miền hợp lệ `V ∈ [-0x8000_0800, +0x7FFF_F7FF]` trong `AXS-RV64-038`.
2. **Finding 2 — Đường dẫn tệp `SPEC-34` trong `## Sources` (`SPEC-87:415`):**
   - Thay thế đường dẫn không tồn tại `` `spec/SPEC-34-concurrency-tasks-channels-select.md` `` bằng tệp chuẩn `` `spec/SPEC-34-executors-fibers.md` `` (và bổ sung `` `spec/SPEC-55-fixed-address-declarations.md` `` đồng bộ với `AXS-RV64-018`).
3. **Finding 3 — Sửa 7 trích dẫn quy tắc liên `SPEC` (`SPEC-87:42, 108, 150, 177, 211, 214, 216, 237`):**
   - `AXS-RV64-004`: `SPEC-81 AXS-TGTD-010..012` -> `SPEC-81 AXS-TGTD-005` (`DataLayout`).
   - `AXS-RV64-017`: `SPEC-31 AXS-ATM-001..010` -> `SPEC-31 AXS-ATM-001..008, AXS-ATM-010, AXS-ATM-014..027, AXS-ATM-040..041` (loại bỏ `AXS-ATM-009` không tồn tại).
   - `AXS-RV64-031`: gỡ bỏ `SPEC-81 AXS-TGTD-034`, dẫn chiếu đúng `ADR-0003`, `SPEC-81 AXS-TGTD-037`, `SPEC-83 AXS-A64-021`.
   - `AXS-RV64-034`: `SPEC-81 AXS-TGTD-041` -> `SPEC-81 AXS-TGTD-035` (`decode(encode(I)) == I`).
   - `AXS-RV64-037`: `SPEC-80 AXS-ELFS-001` -> `SPEC-80 AXS-ELFS-021` (`Elf64_Ehdr`).
   - `AXS-RV64-041`: `SPEC-82 AXS-ELFD-025` -> `SPEC-82 AXS-ELFD-021, AXS-ELFD-040` (ELF64 TLS).
   - `AXS-RV64-042`: `SPEC-54 AXS-PAN-010` -> `SPEC-54 AXS-PAN-020` (rào chắn cấm unwind qua biên FFI).
   - `AXS-RV64-044`: `SPEC-52 AXS-FRE-003..010` -> `SPEC-52 AXS-FRE-002..004, AXS-FRE-010, AXS-FRE-022..023` (loại bỏ dải khuyết `006..009`).
4. **Finding 4 — Đồng bộ toàn bộ số mục `tasks/0522 §1..160` (`SPEC-87`, `spec/invariants.md`, `spec/diagnostics.md`):**
   - Đối chiếu trực tiếp từng tiêu đề mục `§1`..`§160` của `docs/base/tasks/0522` và `§562.135–140` của `docs/base/tasks/0784`, cập nhật chính xác toàn bộ trích dẫn mục trên `AXS-RV64-001`..`048`, `spec/invariants.md` (`INV-RISCV-001`..`003`), và `spec/diagnostics.md:706`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `requirements: 32308 ... gaps: 0, COVERAGE OK` (exit `0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit `0`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T677`: exit `0` (`0 REFUSED`).
- Kiểm tra tự động toàn cục: `0` byte `\r` trên toàn bộ tệp `spec/` và báo cáo; `51` quy tắc `AXS-RV64-001`..`051` liên tục tuyệt đối trên tổng `1,496` quy tắc `AXS-*`; 100% quy tắc liên `SPEC` và đường dẫn tệp trong `SPEC-87` tồn tại thực tế; kiểm chứng toán học vét cạn biên `+0x800` cho `AXS-RV64-015`, `AXS-RV64-016` và `AXS-RV64-038` đạt 100%.

## Files changed

- spec/SPEC-87-riscv64-linux.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
