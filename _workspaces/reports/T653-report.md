# T653 Report — E16.1: Canonical Declarative TargetDesc, ISA Tables & Backend Conformance Specification (`SPEC-81`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-001`..`053`) cho Epic `E16.1`, hợp nhất kiến trúc mô tả đích khai báo (`TargetDesc` / `TargetSpec`), mô hình tệp thanh ghi phân cấp (`RegisterFile`), bảng tập lệnh (`IsaTable`), bộ hợp thức hóa (`Legalizer`), trình kiểm chứng Machine IR trước mã hóa (`verify_mc`), và hợp đồng tương thích ngữ nghĩa độc lập đích của Axiom (`0162`, `0163`, `tasks/0472`, `tasks/0518`, `tasks/0520`, `tasks/0521`, `tasks/0524`, `tasks/0784`):
- **Mô tả đích khai báo (`TargetDesc`, `AXS-TGTD-001`..`012`):** Quy định lược đồ `TargetDesc` tĩnh theo `TargetId` chuẩn hóa (`x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `aarch64-windows`, `wasm32`, `riscv64-linux`), `TargetFingerprint` BLAKE3 128 bit cô lập bộ đệm mã máy giữa các đích, sự tách biệt trực giao giữa `Arch`/`Os`/`Env`/`CallConv`, `DataLayout` (độ rộng con trỏ 32/64 bit, `Endian`, căn chỉnh tự nhiên và căn chỉnh ngăn xếp 16 byte), các chiều định dạng độc lập (`ObjectFormat`, `ArchiveFormat`, `ImageFormat`), đồ thị suy diễn có hướng không chu trình `TargetFeatureSet` (`AVX2`, `AVX-512`, `NEON`, `SVE`, `LSE`, `RVV`, `RVC`, tính năng WASM) cấm phát sinh lệnh ngoài tập tính năng hoặc tự chèn nhánh điều phối CPU ẩn, và bộ phân loại ABI hướng bảng `CallConvDesc`.
- **Mô hình `RegisterFile` và cấp phát thanh ghi (`AXS-TGTD-013`..`023`):** Tách biệt thanh ghi ảo (`vreg`) và khe ngăn xếp vật lý (`StackSlot`) khỏi biến ngữ nghĩa nguồn; mô hình hóa `PhysicalRegDesc` với mặt nạ đơn vị cơ sở `reg_unit_mask: u128`, quan hệ thanh ghi con/cha tường minh (`RAX`/`EAX`/`AX`/`AL`/`AH`, `ZMM`/`YMM`/`XMM`, `X0`/`W0`, `Q0`/`D0`/`S0`), các thanh ghi kiến trúc dành riêng (`RSP`, `SP` phân biệt ngữ cảnh với thanh ghi không `XZR`, `X18`, `x0`, `gp`, `tp`), các lớp thanh ghi (`RegClass`), tập bảo toàn bởi hàm gọi/được gọi, hai tầng cấp phát thanh ghi (`LinearScan` ở `-O0`/`-O1` và `Hybrid/Graph` ở `-O2`), và chế độ địa chỉ hóa theo đích không rò rỉ lên ngữ nghĩa Core.
- **Bảng `IsaTable`, `Legalizer` và trình kiểm chứng `verify_mc` (`AXS-TGTD-024`..`038`):** Định nghĩa `InstrDesc` (ràng buộc toán hạng, vị từ tức thời, toán hạng buộc chung thanh ghi `TiedDefUse`, thanh ghi ngầm định `RAX:RDX`/`RCX` và mặt nạ clobber của `CALL`), mô hình hóa điều kiện so sánh cho cả ISA dùng cờ (`RFLAGS`, `NZCV`) lẫn ISA không cờ (`RISC-V`, `WASM`), bộ chọn lệnh theo mẫu (`Pattern-based ISel`), bảng hành động `Legalizer` (`Legal`, `Promote`, `Expand`, `Scalarize`, `Reject`) bảo toàn tràn số nguyên, dấu phẩy động IEEE-754 nghiêm ngặt, nguyên tử/`volatile`/thứ tự bộ nhớ, tách biệt `Panic` với `TrapBehavior` phần cứng, nhất quán `decode(encode(I)) == I`, và 10 kiểm tra bắt buộc của `verify_mc` trước khi mã hóa.
- **Hợp đồng tương thích ngữ nghĩa độc lập đích (`AXS-TGTD-039`..`053`):** Khóa `Axiom LIR` làm ranh giới khả chuyển ngữ nghĩa duy nhất (`ABACKEND-99..100`), tuần tự hóa độc lập từng chặng (`--emit=target-desc`, `--emit=isa-table`, `--emit=lir`, `--emit=mc`, `--emit=mc-explain`), xác định tệp mẫu hợp ngữ chỉ là kiểm thử chất lượng mã (`ABACKEND-90`), và yêu cầu mọi backend vượt qua bộ kiểm thử đối chiếu chung với `--interp` trên mọi hồ sơ tối ưu hóa (`-O0`..`-Oz`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_UNSUPPORTED_OP`, `AX_VERIFY_MC_ILLEGAL`), và `spec/invariants.md` (`INV-TGTD-001`..`003`).

## Spec decisions & deliverables
1. **`spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-001`..`053`):**
   - Covers `REQ-TGT-004`..`REQ-TGT-011`, `REQ-TGT-285`, `REQ-TGT-286` directly and specifies the normative contract for `T654` (`REQ-TGT-012`..`021`, `REQ-TGT-054`..`056`), `T655` (`REQ-TGT-022`..`036`, `REQ-TGT-044`..`053`, `REQ-TGT-057`..`058`, `REQ-TGT-108`..`109`), and `T656` (`REQ-TGT-085`..`095`, `REQ-TGT-107`, `REQ-TGT-287`..`295`).
   - Includes canonical positive and negative Axiom examples using `=` for binding/assignment, `.` for paths, and `view(x)` / `mut_view(x)`.
2. **`spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`:**
   - Registered `SPEC-81` and namespace `AXS-TGTD-NNN` in `spec/INDEX.md`.
   - Documented `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_UNSUPPORTED_OP`, and `AX_VERIFY_MC_ILLEGAL` in `spec/diagnostics.md` §11.
   - Added Section 35 (`INV-TGTD-001`..`003`) to `spec/invariants.md`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: passed (exit 0).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: passed (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T653`: passed (exit 0, 4 allowed files, 0 refused).

## Files changed
- spec/SPEC-81-target-desc-isa-conformance.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
