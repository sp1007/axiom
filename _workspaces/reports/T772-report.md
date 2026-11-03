# T772 Report — E18.7: Canonical Windows x64 Static `.lib`, PE DLL & Import Library Specification (`SPEC-26`)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-26-windows-artifact-kinds.md` cho Epic `E18.7` (`T772`), hợp nhất các quy tắc kiến trúc và định dạng nhị phân Windows x64 cho 4 loại thành phẩm đầu ra (`--kind exe|obj|lib|dll`):
1. **Lựa chọn thành phẩm, cờ CLI & kiến trúc đường ống liên kết (`AXS-WLIB-001`..`005`):** chuẩn hóa `ArtifactKind` (`Executable`, `Object`, `StaticLib`, `DynLib`), cờ CLI `--kind exe|obj|lib|dll` (giữ `--emit=obj` làm bí danh tương thích cho `--kind obj`), tùy chọn `--implib <path>`, trường `kind` trong `axiom.toml`, thứ tự tìm kiếm thư viện tất định cho `-l<name>`, `-L<dir>` và `@link("<name>")`, hợp đồng xuất ký hiệu `@export` tách biệt khỏi phạm vi mô-đun `pub` (`REQ-LNK-210`, `REQ-LNK-211`), và sự phân tách giữa `ObjectWriter`, `ArchiveWriter`, `LinkerCore` (`LinkedImage`, `REQ-LNK-232..233`) cùng `ImageWriter` (`PeImageWriter`, `REQ-CORE-3087..3088`).
2. **Thư viện tĩnh COFF `.lib` tất định & trích xuất thành viên theo điểm bất động (`AXS-WLIB-010`..`012`):** quy định chữ ký `!<arch>\n`, tiêu đề thành viên 60 byte với siêu dữ liệu tất định (`Date = 0`, `UID = 0`, `GID = 0`, `Mode = 0`), First Linker Member (big-endian), Second Linker Member (little-endian, ký hiệu sắp xếp theo thứ tự từ điển), Longnames Member (`//`), và thuật toán trích xuất thành viên theo nhu cầu tới điểm bất động (demand-driven fixed-point extraction) loại bỏ hoàn toàn các thành viên `.obj` không được tham chiếu (`T750`).
3. **Thư viện liên kết động PE32+ `.dll` (`AXS-WLIB-020`..`023`):** quy định cờ `IMAGE_FILE_DLL (0x2000)`, địa chỉ ưu tiên `ImageBase = 0x180000000`, `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`, cấu trúc bảng xuất `.edata` (`IMAGE_EXPORT_DIRECTORY` 40 byte kèm `ExportAddressTable`, `NamePointerTable`, `OrdinalTable` sắp xếp từ điển), hàm điểm vào tổng hợp `_DllMainCRTStartup` thực thi `__ax_resolve_module_bindings()` (`SPEC-56 AXS-MOD-012`) và hàm khởi tạo mô-đun khi `DLL_PROCESS_ATTACH`, cùng bảng định vị lại cơ sở `.reloc` (`IMAGE_REL_BASED_DIR64 = 10`) theo khối trang 4 KiB (`T751`).
4. **Thư viện nhập khẩu ngắn COFF `.lib` & liên kết chéo `__imp_<name>` (`ADR-0034` §4 OI-07b) (`AXS-WLIB-030`..`032`):** quy định phát sinh đồng thời tệp `.lib` nhập khẩu ngắn (`IMPORT_OBJECT_HEADER` 20 byte, `Sig1 = 0x0000`, `Sig2 = 0xFFFF`) khi biên dịch `--kind dll`, cơ chế đọc cả thành viên nhập khẩu ngắn lẫn đối tượng COFF `.idata` truyền thống trong `compiler/link/`, cùng quy ước ký hiệu chuẩn `__imp_<name>` và đối tượng thời gian chạy khả liên kết để GNU `ld`/`gcc` liên kết trực tiếp đầu ra `--kind obj` (`--emit=obj`) (`T751`, `T773`).
5. **Đăng ký mã chẩn đoán & bất biến (`SPEC-26` §5, `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md`):** đăng ký không gian tên `AXS-WLIB-NNN`, 4 mã chẩn đoán mới (`AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_EXPORT`), và nhóm bất biến `WLIB` (`INV-WLIB-001` cho `T750`, `INV-WLIB-002` cho `T751`, `INV-WLIB-003` cho `T773`).

## What Was Done

1. **Authored `spec/SPEC-26-windows-artifact-kinds.md`:**
   - Defined `AXS-WLIB-001`..`005` (artifact kinds, CLI `--kind exe|obj|lib|dll` & `--implib`, `-l`/`-L`/`@link` library resolution order, `@export` visibility vs `pub`, and `LinkerCore`/`LinkedImage`/`PeImageWriter` architecture).
   - Defined `AXS-WLIB-010`..`012` (COFF `.lib` archive layout, 1st/2nd linker members, `//` longnames table, zeroed timestamps/modes, and demand-driven fixed-point extraction).
   - Defined `AXS-WLIB-020`..`023` (PE32+ `.dll` characteristics, `.edata` export directory, synthesized `_DllMainCRTStartup` calling `__ax_resolve_module_bindings()`, and `.reloc` `IMAGE_REL_BASED_DIR64` blocks).
   - Defined `AXS-WLIB-030`..`032` (companion COFF short-import `.lib` generation `IMPORT_OBJECT_HEADER`, linker consumption of short-import and traditional import libraries, and `ADR-0034` §4 OI-07b `__imp_<name>` + linkable runtime support for GNU `ld` cross-linking).
   - Defined `AXS-WLIB-050`..`053` (diagnostics summary, canonical positive/negative Axiom examples using `=` and `.`, and verification matrix for `T750`, `T751`, `T773`).
2. **Updated `spec/INDEX.md`:**
   - Added `spec/SPEC-26-windows-artifact-kinds.md` (`draft`, owner `T772`, consumers `T750, T751, T773`) to §2.
   - Added `AXS-WLIB-NNN` to §4 Identifier namespaces.
   - Referenced `SPEC-26` in §5 Topic → canonical source (`LIR, ABI, FFI, x86-64, COFF, PE`).
3. **Updated `spec/diagnostics.md`:**
   - Registered `AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`, and `AX_LINK_DUPLICATE_EXPORT` in §11 (`Names already fixed for later tasks`) and added `SPEC-26` to `## Sources`.
4. **Updated `spec/invariants.md`:**
   - Added group `WLIB` to §1 and added §26 (`INV-WLIB-001` `since: T750`, `INV-WLIB-002` `since: T751`, `INV-WLIB-003` `since: T773`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `requirements: 32308 ... gaps: 0 / COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T772` → `0 REFUSED` lines (all 4 modified files within `paths:`/`locks:` of `T772`).

## Files changed

- `spec/SPEC-26-windows-artifact-kinds.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE round=0
