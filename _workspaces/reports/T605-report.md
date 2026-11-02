# T605 Report — E15.2 — Canonical alias analysis, escape analysis & allocation promotion specification (SPEC-71)

## Tóm tắt
Đã viết đặc tả chuẩn `spec/SPEC-71-alias-escape-promotion.md` cho Epic `E15.2` (Phase P15 `P15-optimizer-2-0`), hợp nhất các nguồn `0131 §86`, `0162 §29`, `0165 §15–20`, `0226 §1–26`, `tasks/0366` (`AOPT-23..38`, `AOPT-59..60`), `tasks/0395` (`AALIAS-20..70`), `tasks/0397` (`AESCAPE-20..80`), `tasks/0429` (`ACOL-31..37`), `tasks/0436` (`AMEMALLOC-21..29`, `AALLOC-20..29`, `AFRAG-20..24`), `tasks/0438` (`AZCOPY-20..25`, `ADMA-20..25`), `tasks/0480` (§27–28), `tasks/0486` (`ACAP-45..52`), `tasks/0548` (`AMEMOPT-20..85`), `tasks/0615` (`ACLOS-01..30`), `SPEC-10..12` và `SPEC-70` thành bộ quy tắc đánh số ổn định `AXS-ALIAS-001..006` và `AXS-ESC-001..017`:
- **Phân tích bí danh dựa trên năng lực và nguồn gốc (`AXS-ALIAS-001..005`)**: Phân biệt truy cập bộ nhớ ngữ nghĩa (`Verified MIR`) với truy cập bộ nhớ máy vật lý (`REQ-OPT-366`), tách 3 miền định danh (`ValueIdentity`, `AllocationIdentity`, `LogicalIdentity`) và định nghĩa dàn 5 giá trị `AliasResult` (`NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`, `UnknownAlias`) kết hợp `RegionRelation` (`Disjoint`, `Same`, `Contains`, `ContainedBy`, `Overlaps`, `UnknownRelation`). Xuất chứng minh độc quyền của `mut_view<T>` thành `NoAlias` nội bộ (`REQ-OPT-299`, `REQ-OPT-358`), dùng tính bất biến chỉ đọc của `view<T>` để lưu đệm đọc/RLE (`REQ-OPT-301`), ràng buộc thứ tự bộ nhớ theo `WRITE` (`REQ-OPT-302`), phân tách gốc cấp phát / cây chiếu trường `S.f_i` / khoảng nửa mở `RangeInfo` (`REQ-OPT-303`), và giữ bảo thủ `MayAlias`/`UnknownAlias` cho con trỏ thô (`*const T`/`*mut T`), `Arc`/`Rc`, và FFI (`REQ-OPT-028`, `REQ-OPT-300`, `REQ-OPT-314`).
- **Tối ưu hóa bộ nhớ thống nhất trên `MemorySSA` (`AXS-ALIAS-006`)**: Quy định điều kiện hợp lệ cho `Store-to-Load Forwarding`, `Redundant Load Elimination (RLE)`, `Dead Store Elimination (DSE)`, và tối ưu `memcpy`/`memmove`/`memset` (`REQ-OPT-365..366`), đồng thời bảo toàn nghiêm ngặt các rào cản `atomic`, `volatile`/`@at`, FFI, `Drop`, và đường truyền zero-copy/DMA (`REQ-OPT-029`, `REQ-OPT-312..314`, `REQ-OPT-347`).
- **Phân tích thoát `EscapeInfo` (`AXS-ESC-001..004`)**: Tách biệt quyền sở hữu (`Ownership`), thời gian sống ngữ nghĩa (`Lifetime`), năng lực (`Capability`), và trạng thái thoát (`NoEscape`, `ArgumentEscape`, `ReturnEscape`, và `GlobalEscape = HeapEscape | ThreadEscape | ExternalEscape | UnknownEscape` — `REQ-OPT-042..045`, `REQ-OPT-357`), lan truyền tóm tắt liên thủ tục qua SCC đồ thị lời gọi và kiểm tra ràng buộc `Send`/`mut_view` độc quyền của bao đóng (`REQ-OPT-386`).
- **Thăng cấp lưu trữ và rào cản quan sát địa chỉ (`AXS-ESC-010..017`)**: Quy định thứ tự ưu tiên 8 bước (`REQ-OPT-046`) để thăng cấp `Box<T>` (`Heap → Stack → SSA Register → Eliminated` nhưng vẫn giữ `Drop` của phần tử bên trong — `REQ-OPT-012`, `REQ-OPT-024..025`, `REQ-OPT-307`, `REQ-OPT-309`, `REQ-OPT-335`, `REQ-OPT-346`), môi trường bao đóng và máy trạng thái `Future` (`REQ-OPT-008`, `REQ-OPT-336`, `REQ-OPT-385..386`), bộ sưu tập hữu hạn (`REQ-OPT-345`), và khe trả về do hàm gọi cấp phát (`NRVO`/`sret` — `REQ-OPT-310`), đồng thời tôn trọng tuyệt đối rào cản quan sát địa chỉ (`address_of`, `@at`, `volatile`) (`REQ-OPT-027`, `REQ-OPT-029`, `REQ-OPT-308`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-042`), và `spec/invariants.md` (`INV-PIPE-009`).

## Summary
Authored the canonical specification `spec/SPEC-71-alias-escape-promotion.md` for E15.2 (Capability- and provenance-driven `AliasInfo`, `MemorySSA` store-to-load/RLE/DSE optimization, `EscapeInfo` classification, and stack/register allocation promotion) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

### Key rules defined in `spec/SPEC-71-alias-escape-promotion.md`
1. **Capability- and Provenance-Driven Alias Analysis (`AXS-ALIAS-001`–`AXS-ALIAS-006`)**:
   - Distinguishes semantic memory access from physical machine memory access (`REQ-OPT-366`) and separates `ValueIdentity`, `AllocationIdentity`, and `LogicalIdentity`, as well as spatial `RegionId` and temporal capability `Lifetime`.
   - Defines `RegionRelation` and the 5-valued `AliasResult` lattice (`NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`, `UnknownAlias`), enforcing the fail-closed rule that `UnknownAlias` and `MayAlias` are never treated as `NoAlias` (`REQ-OPT-028`, `REQ-OPT-300`).
   - Specifies capability derivation (`mut_view<T>` disjointness exported as `NoAlias`, `view<T>` read-only stability for load caching, `WRITE` ordering constraints, and capability splitting/joining — `REQ-OPT-299`, `REQ-OPT-301..302`, `REQ-OPT-358`), structural/allocation-root/field-sensitive/range-refined disjointness (`REQ-OPT-303`), raw-pointer and `Arc`/`Rc` provenance barriers, and the unified `MemorySSA` memory optimization engine (`Store-to-Load Forwarding`, `RLE`, `DSE`, `memcpy`/`memmove`/`memset`, and `atomic`/`volatile`/`FFI`/zero-copy DMA barriers — `REQ-OPT-029`, `REQ-OPT-312..314`, `REQ-OPT-347`, `REQ-OPT-365`).
2. **Escape Analysis & Semantic vs. Physical Lifetime (`AXS-ESC-001`–`AXS-ESC-004`)**:
   - Separates ownership, semantic lifetime, capability validity, escape status, and physical storage placement (`REQ-OPT-042..045`).
   - Defines the fine-grained `EscapeSet` bitmask (`ESC_NONE`, `ESC_ARGUMENT`, `ESC_RETURN`, `ESC_HEAP`, `ESC_THREAD`, `ESC_EXTERNAL`, `ESC_UNKNOWN` — `REQ-OPT-357`) and the four-tier promotion lattice (`NoEscape ⊏ ArgumentEscape ⊏ ReturnEscape ⊏ GlobalEscape`), interprocedural `FunctionEscapeSummary` propagation over call-graph SCCs (`REQ-OPT-043`), and capability/concurrency interactions (`REQ-OPT-386`).
3. **Storage Selection, Allocation Promotion & Observability Barriers (`AXS-ESC-010`–`AXS-ESC-017`)**:
   - Formalizes the 8-step `StorageDecision` priority hierarchy (`REQ-OPT-046`), `Box<T>` promotion (`Heap → Stack → SSA Register → Eliminated` with mandatory payload `Drop` preservation — `REQ-OPT-012`, `REQ-OPT-024..025`, `REQ-OPT-307`, `REQ-OPT-309`, `REQ-OPT-335`, `REQ-OPT-346`), closure capture and async `Future` promotion (`REQ-OPT-008`, `REQ-OPT-336`, `REQ-OPT-385..386`), bounded collection promotion and disjoint-lifetime stack slot reuse (`REQ-OPT-345`), caller-allocated return slot (`NRVO`/`sret`) optimization (`REQ-OPT-310`), the address-observability (`address_of`, `@at`, `volatile`) barrier (`REQ-OPT-027`, `REQ-OPT-029`, `REQ-OPT-308`), `PassManager` contracts (`AXS-ESC-016`), and `inspect --emit=alias` / `--emit=escape` (`AXS-ESC-017`).

## Files changed
- spec/INDEX.md
- spec/SPEC-71-alias-escape-promotion.md
- spec/diagnostics.md
- spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1 PASS` .. `MS-P10b PASS` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T605`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
