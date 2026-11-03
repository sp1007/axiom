# T756 Report — E18.2: Canonical incremental compilation & fingerprinting specification (SPEC-22)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-22-incremental-compilation.md` cho E18.2 (Biên dịch tăng dần, dấu vân tay đa tầng `Fingerprint128`, lan truyền thay đổi đỏ-xanh `try_mark_green`, và bộ nhớ đệm bền vững `.axiom-cache` trong `compiler/`):
- Định nghĩa hệ thống phân cấp dấu vân tay 128-bit tách biệt miền (`SourceFingerprint`, `AstFingerprint` phi vị trí/khoảng trắng/chú thích thường, `InterfaceFingerprint`, `AbiFingerprint`, `BodyFingerprint` trên `Verified MIR`, và `CodegenFingerprint`), phân tách rõ 3 lớp thay đổi (`Implementation-only`, `Interface`, `ABI/Layout`) theo `REQ-CORE-3089` và `REQ-CORE-3090`, đồng thời ghi nhận phụ thuộc xuyên module cho `const`/`comptime`, đơn hình hóa generic, và hàm `@inline` (`AXS-INC-001`..`004`).
- Quy định thuật toán kiểm chứng đỏ-xanh (`try_mark_green`) và lùi dấu thời gian (backdating) trên `CompilerDB`, bảo đảm tường lửa thân hàm riêng tư (`edit-one-private-fn` giữ `InterfaceFingerprint` xanh nên `0` truy vấn `typeck` ở module phụ thuộc bị chạy lại), cùng giao diện kiểm tra `--emit=fingerprints` và `--emit=incremental-stats` (`AXS-INC-010`..`013`).
- Quy định kiến trúc bộ nhớ đệm 3 tầng (`L0`–`L2`), khóa môi trường kín `EnvironmentDigest` (`ACACHE-20..21`), định dạng tệp `.axcache` có phiên bản + mã kiểm toàn vẹn BLAKE3 128-bit + ghi nguyên tử, cơ chế tự động hủy bỏ và tính lại khi bộ nhớ đệm hỏng/lệch phiên bản (`ACACHE-23..24`), đường nhanh `< 100 ms` cho biên dịch lại không thay đổi (no-op rebuild), và bất biến tương đương từng byte giữa biên dịch tăng dần và biên dịch sạch (`--no-incremental`, `ACACHE-22`) (`AXS-INC-020`..`024`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (§28 `INV-INC-001`..`003`).

## Specification & Index Updates

1. **`spec/SPEC-22-incremental-compilation.md`**:
   - **§1 (`AXS-INC-001`..`004`)**: 128-bit domain-separated `Fingerprint128` primitives, multi-tier fingerprint hierarchy (`Source`, `Ast`, `Interface`, `Abi`, `Body`, `Codegen`), `InterfaceFingerprint` vs `BodyFingerprint` firewall & ABI separation (`REQ-CORE-3089`, `REQ-CORE-3090`), and cross-module `const`, generic monomorphization, and inlined body dependencies.
   - **§2 (`AXS-INC-010`..`013`)**: Red-green `NodeColor` and typed `DependencyKind` edges, deterministic `try_mark_green` verification and backdating algorithm, private-body firewall guarantee (`edit-one-private-fn`), fine-grained invalidation matrix, and `inspect --emit=fingerprints` / `--emit=incremental-stats`.
   - **§3 (`AXS-INC-020`..`024`)**: Layered `L0`–`L2` cache architecture, hermetic `EnvironmentDigest` key binding (`ACACHE-20..21`), versioned/checksummed `.axcache` schema with atomic publication and corruption fallback (`ACACHE-23..24`), `< 100 ms` root digest no-op fast path, and clean-vs-incremental semantic/diagnostic/binary equivalence (`ACACHE-22`).
   - **§4 (`AXS-INC-050`..`053`)**: Incremental CLI/diagnostic policy, positive and negative canonical Axiom examples (`=` and `.` syntax only), E18.2 verification matrix (`T757`–`T759`), and corpus source citations.
2. **`spec/INDEX.md`**:
   - Added `spec/SPEC-22-incremental-compilation.md` to §2 Canonical documents table.
   - Added `AXS-INC-NNN` to §4 Identifier namespaces table.
   - Updated §5 Topic -> canonical source table (`Kernel` / incremental compilation row).
3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` (§3) and `## Sources` for E18.2 (`SPEC-22`: transparent corrupt/stale cache fallback and `AXD-060` warm diagnostic replay).
4. **`spec/invariants.md`**:
   - Added group `INC` to §1 Groups list.
   - Added §28 (`INV-INC-001` `since: T757`, `INV-INC-002` `since: T758`, `INV-INC-003` `since: T759`) covering `0153 ACACHE-20..24` and `SPEC-22`, and updated `## Sources`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`requirements: 32308`, `gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T756` → `4 STAGE`, `0 REFUSED`

## Files changed

- `spec/SPEC-22-incremental-compilation.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE round=0
