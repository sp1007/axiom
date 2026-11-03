# T764 Report — E18.4 — Canonical Axiom Artifact Format & Module Interface Specification (`SPEC-24`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-001`..`053`) cho định dạng thành phẩm nhị phân và tệp giao diện mô-đun `.axmi` (E18.4):
1. **Hệ thống phân loại thành phẩm & định dạng khung chứa nhị phân (`AXS-ART-001`..`005`)**: Phân định rõ vai trò của `.ax`, `.axmi`, `.axmir`, `.axlto`, `.obj`, `.lib`, `.exe`/`.dll`, `.axdbg` và `.axpkg`. Quy định đầu mục 64-byte `ArtifactHeader` (magic theo họ định dạng, `schema_version`, `TargetFingerprint`, `InterfaceFingerprint`, `content_hash` BLAKE3-128), bảng phân đoạn `SectionDescriptor` (48-byte, hỗ trợ nạp lười theo nhu cầu và `MMAPABLE` zero-copy có kiểm chứng căn chỉnh/endian/checksum), tuần tự hóa không con trỏ/không dấu thời gian, và phát hành nguyên tử.
2. **Tệp giao diện mô-đun `.axmi` cho biên dịch riêng rẽ không cần tệp nguồn (`AXS-ART-010`..`014`)**: Lưu trữ khai báo `pub`, bảng `TypeId` chuẩn hóa theo `SemanticKey`, bảng `Trait`/`impl`, tóm tắt quyền sở hữu/capability/hiệu ứng/panic/concurrency (`tasks/0582`), giá trị `const` đã tính và mẫu `Verified MIR` cho hàm `generic` / `@inline` / `comptime fn` (`tasks/0739`), nạp trực tiếp vào `CompilerDB` (`T765`).
3. **Phân đoạn đối tượng nhúng `.axmeta`/`.axmir`/`.axlto` & `ObjectWriter` 3.0 (`AXS-ART-020`..`024`, `AXS-ART-050`..`053`)**: Định nghĩa mô hình `ObjectArtifact` độc lập định dạng (`tasks/0803`), nhúng các phân đoạn `IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE` vào `.obj`/`.lib`, kiểm chứng dấu vân tay đích/ABI/checksum khi liên kết và lược bỏ khỏi `.exe`/`.dll` cuối cùng (`T766`), cùng các mã chẩn đoán `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH` và bất biến `INV-ART-001`..`003`.

## Architecture Decisions & Rule Summary
- **`AXS-ART-001`..`005`**: Canonical artifact taxonomy, 64-byte `ArtifactHeader`, 48-byte `SectionDescriptor`, pointer-free little-endian serialization, scoped IDs (`ArtifactLocal`, `PackageLocal`, `WorkspaceLocal`, `GlobalContentAddressed`), validated zero-copy `MMAPABLE` access, schema compatibility policy (`RequiredUnknown -> ERROR`, `OptionalUnknown -> SKIP`), and atomic cache publication.
- **`AXS-ART-010`..`014`**: `.axmi` module interface specification unifying corpus `.axif`/`.axsem`, direct `CompilerDB` population without upstream `.ax` source files, canonical `TypeId` DAG, trait coherence tables, interprocedural `FnContractSummary` (ownership, capability provenance, effects, `@no_panic`, `Send`/`Share`), evaluated `ConstValue` payloads, pre-verified generic/`@inline`/`comptime` MIR templates, freshness classification, and `AIIndex` provenance.
- **`AXS-ART-020`..`024`**: Format-independent `ObjectArtifact` model (`ObjectWriter` 3.0), embedded non-alloc `.axmeta`, `.axlto`, and `.axmir` COFF object sections (`0x42000200`), link-time verification and final `.exe`/`.dll` stripping, target/ABI/profile/CPU-variant fingerprint binding, `.axpkg` bundles, and `.axdbg` debug artifacts.
- **`AXS-ART-050`..`053`**: CLI flags (`--emit=axmi`, `inspect --axmi`, `inspect --artifact-sections`), diagnostic codes (`AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`), positive/negative canonical Axiom examples (`=` and `.` syntax), and E18.4 verification matrix (`T765`–`T767`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T764`

## Files changed
- spec/SPEC-24-artifact-format-module-interfaces.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
