# T774 Report — E18.6: Canonical Separate Compilation, Multi-Object `LinkIR` Linking & Section GC Specification (`SPEC-27`)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-27-separate-compilation-linker-v2.md` cho Epic `E18.6` (`T774`), chuẩn hóa mô hình biên dịch riêng rẽ từng mô-đun (`.obj` + `.axmi`), biểu diễn trung gian `LinkIR`, thuật toán phân giải ký hiệu đa đối tượng và kho lưu trữ `.lib`, khử trùng lặp thực thể tổng quát / bảng phương thức ảo qua `IMAGE_SCN_LNK_COMDAT`, và thu gom rác phân đoạn theo tập gốc khả đạt (`--gc-sections`):
1. **Hợp đồng biên dịch riêng rẽ, thứ tự nạp tất định & bàn giao mã hóa máy 4.0 (`AXS-LNK-001`..`005`):** quy định biên giới kiến trúc tuyệt đối của trình liên kết (`INV-LAYER-002`, `REQ-LNK-001..003`, `REQ-LNK-132`, `REQ-LNK-160`), biên dịch độc lập từng mô-đun ra `<module>.obj` + `<module>.axmi` kèm tái sử dụng theo `CodegenFingerprint`, các bất biến hệ thống kiểu/trait phục vụ biên dịch riêng rẽ (quy tắc mồ côi trait `REQ-LNK-122`, chuẩn hóa `TypeId` cho thực thể tổng quát `REQ-LNK-140`, phân biệt độ dài mảng `[N]T` và kiểu danh định `REQ-LNK-141..143`, quy ước gọi trong định danh kiểu hàm `REQ-LNK-144`, khai báo kiểu trả về tường minh cho `pub fn` `REQ-LNK-146`), tách biệt tính toán `FrameLayout` với phát sinh prologue/epilogue (`REQ-LNK-123..131`), bàn giao mã hóa lệnh máy tất định `Machine Code Encoding 4.0` (`REQ-LNK-3434..3633`), thứ tự liên kết `.obj`/`.lib` chuẩn hóa, và kiểm tra tương thích đích/ABI xuyên đối tượng (`AX_LINK_ABI_MISMATCH`).
2. **Mô hình `LinkIR`, phân giải ký hiệu `Strong`/`Weak`/`COMDAT` & chẩn đoán giải mã tên (`AXS-LNK-010`..`014`):** định nghĩa `LinkIR` độc lập định dạng (`LinkSymBinding`, `ComdatSelection`, `LinkSymbol`), quy tắc mangling/demangling chuẩn (`_AX1_...` ↔ đường dẫn dấu chấm `pkg.mod.item<T>`), ma trận phân giải ký hiệu toàn cục (`Strong` vs `Strong` báo lỗi `AX_LINK_DUPLICATE_SYMBOL`, `Strong` thắng `Weak`, cô lập `Local`, trích xuất `.lib` theo điểm bất động), gộp nhóm `IMAGE_SCN_LNK_COMDAT` cho hàm tổng quát đơn hình hóa và vtable (`T775`), cùng chẩn đoán có cấu trúc mang tên Axiom đã giải mã (`data.demangled`) và `Span` nguồn từ `.axmeta` (`T067`).
3. **Chia nhỏ phân đoạn, thu gom rác phân đoạn (`--gc-sections`), `Safe ICF` & kiểm chứng ảnh cuối (`AXS-LNK-020`..`025`, `AXS-LNK-050`..`053`):** phát sinh mỗi hàm/dữ liệu vào phân đoạn riêng (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>` kèm `.pdata$<sym>`/`.xdata$<sym>` `IMAGE_COMDAT_SELECT_ASSOCIATIVE`), đánh dấu – quét từ tập gốc (`@entry`/`main`/`DllMain`, `@export`, `@used`, `@at` cố định địa chỉ, khởi tạo mô-đun, gốc phản xạ runtime), gộp mã/dữ liệu chỉ đọc đồng nhất bảo toàn định danh địa chỉ (`Safe ICF`), kiểm tra tràn định vị lại (`AX_LINK_RELOC_OUT_OF_RANGE`), cờ `inspect --emit=link-map` / `--emit=gc-sections`, và ma trận kiểm chứng cho `T067`, `T775`, `T776`.
4. **Cập nhật chỉ mục, mã chẩn đoán & bất biến (`spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`):** đăng ký `SPEC-27`, không gian mã `AXS-LNK-NNN`, mã chẩn đoán `AX_LINK_ABI_MISMATCH`, và nhóm bất biến `LNK` (`INV-LNK-001` cho `T067`, `INV-LNK-002` cho `T775`, `INV-LNK-003` cho `T776`).

## What Was Done

1. **Authored `spec/SPEC-27-separate-compilation-linker-v2.md`:**
   - Defined `AXS-LNK-001`..`005` (linker semantic firewall, per-module `.obj` + `.axmi` separate compilation, orphan/TypeId/frame/encoding handoff invariants `REQ-LNK-122..146` & `REQ-LNK-3434..3633`, deterministic `.obj`/`.lib` input ordering, and cross-object target/ABI verification).
   - Defined `AXS-LNK-010`..`014` (`LinkIR` data structures, `_AX1_` mangling & dotted demangling, `Strong`/`Weak`/`Local`/`Import` resolution matrix, `IMAGE_SCN_LNK_COMDAT` generic/vtable folding, and structured demangled diagnostics with `.axmeta` spans).
   - Defined `AXS-LNK-020`..`025` (per-function/per-datum section emission, reachability root set `@entry`/`@export`/`@used`/`@at`/reflection/init, deterministic mark-sweep section GC with forward `.pdata`/`.xdata` association, address-safe `ICF`, `VA`/`RVA`/`FileOffset` & `W^X` layout, range-checked relocation patching, and final image verification).
   - Defined `AXS-LNK-050`..`053` (CLI flags `--gc-sections`, `--no-gc-sections`, `inspect --emit=link-map`, `inspect --emit=gc-sections`, diagnostic summary, canonical positive/negative Axiom examples using `=`, `.`, and `view(x)`, and E18.6 verification matrix).
2. **Updated `spec/INDEX.md`:**
   - Added `spec/SPEC-27-separate-compilation-linker-v2.md` (`draft`, owner `T774`, consumers `T067, T775, T776`) to §2.
   - Added `AXS-LNK-NNN` to §4 Identifier namespaces.
   - Referenced `SPEC-27` in §5 Topic → canonical source (`LIR, ABI, FFI, x86-64, COFF, PE`).
3. **Updated `spec/diagnostics.md`:**
   - Documented E18.6 linker diagnostics in `AXD-021` (§3) and registered `AX_LINK_ABI_MISMATCH` (`E`, `T067`) in §11 (`Names already fixed for later tasks`).
4. **Updated `spec/invariants.md`:**
   - Added group `LNK` to §1 and added §32 (`INV-LNK-001` `since: T067`, `INV-LNK-002` `since: T775`, `INV-LNK-003` `since: T776`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `gaps: 0 / COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T774` → `0 REFUSED` lines (all 4 modified files within `paths:`/`locks:` of `T774`).

## Files changed

- `spec/SPEC-27-separate-compilation-linker-v2.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE round=0
