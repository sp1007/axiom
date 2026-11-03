# T752 Report — E18.1: Canonical query engine & semantic database specification (SPEC-21)

## Tóm tắt

Hoàn thành đặc tả chuẩn `spec/SPEC-21-query-engine-semantic-db.md` cho E18.1 (Cơ sở dữ liệu ngữ nghĩa hướng cầu `CompilerDB` và bộ máy truy vấn biên dịch trong `compiler/`):
- Định nghĩa mô hình phiên bản `RevisionId` / `SnapshotId`, tách biệt bất biến giữa **bảng đầu vào** (`source_file_input`, `module_tree_input`, `target_config_input`, `package_graph_input`) và **bảng truy vấn suy dẫn** (`parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `mir_body`, `layout_of`) không sử dụng trạng thái toàn cục khả biến (`AXS-QRY-001`..`005`).
- Quy định cơ chế thực thi truy vấn theo nhu cầu (demand-driven evaluation), ngăn xếp truy vấn đang hoạt động (`QueryStack`), tự động ghi nhận cạnh phụ thuộc `caller -> callee`, bộ nhớ đệm gắn `RevisionId`, và đầu ra tất định cho lệnh `axiom inspect <file> --emit=query-graph` (`AXS-QRY-010`..`013`).
- Quy định thuật toán phát hiện chu trình truy vấn tất định trên `QueryStack`, xoay chuẩn hóa chu trình theo khóa ngữ nghĩa nhỏ nhất `(QueryKind, SemanticKey)` để chẩn đoán độc lập với thứ tự gọi (`AXS-QRY-020`..`022`), cùng giá trị phục hồi (`TypeId.ERROR`, `ConstValue.Poisoned`, `TraitResult.Error`, `DefId.ERROR`) ngăn lỗi dây chuyền (`AXS-QRY-023`, `AXS-QRY-031`).
- Quy định cơ chế gắn chẩn đoán với `(SnapshotId, RevisionId)` để phát lại tất định khi trúng bộ nhớ đệm (warm hit), đánh dấu bẩn lan truyền (transitive dirty marking) và tái sử dụng nút xanh (firewall backdating) khi bảng đầu vào thay đổi (`AXS-QRY-030`..`033`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`, `AX_CTM_CYCLE`), và `spec/invariants.md` (§27 `INV-QRY-001`..`003`).

## Specification & Index Updates

1. **`spec/SPEC-21-query-engine-semantic-db.md`**:
   - **§1 (`AXS-QRY-001`..`005`)**: `CompilerDB` snapshot & `RevisionId` model, input vs derived query tables, typed IDs vs canonical `SemanticKey`, interface (`item_signature`) vs body (`typeck_body`, `mir_body`) firewall, and pure query provider contract.
   - **§2 (`AXS-QRY-010`..`013`)**: `QueryKey` & `QuerySlotState` (`Vacant`, `Computing`, `Ready`, `Poisoned`), active `QueryStack` dependency DAG recording, revision-stamped memoization, and deterministic `inspect --emit=query-graph` format.
   - **§3 (`AXS-QRY-020`..`023`)**: Legal semantic recursion vs illegal query cycles, active-stack cycle detection, `CyclePolicy` (`Reject`, `DepthLimited`), canonical cycle rotation from minimum `(QueryKind, SemanticKey)`, and deterministic cycle recovery values.
   - **§4 (`AXS-QRY-030`..`033`)**: Snapshot-bound diagnostic accumulation and warm-hit replay, cascading-error suppression on poisoned values, input-revision transitive dirty marking, and shallow verification / backdating reuse.
   - **§5 (`AXS-QRY-050`..`053`)**: Diagnostic table, positive and negative canonical Axiom examples (`=` and `.` syntax only), E18.1 verification matrix (`T753`–`T755`), and corpus source citations.
2. **`spec/INDEX.md`**:
   - Added `spec/SPEC-21-query-engine-semantic-db.md` to §2 Canonical documents table.
   - Added `AXS-QRY-NNN` to §4 Identifier namespaces table.
   - Updated §5 Topic -> canonical source table (`Kernel` and `Diagnostics` rows).
3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` (§3) and §11 table with E18.1 query/cycle diagnostics (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT` for `T754`).
4. **`spec/invariants.md`**:
   - Added group `QRY` to §1 Groups list.
   - Added §27 (`INV-QRY-001` `since: T753`, `INV-QRY-002` `since: T754`, `INV-QRY-003` `since: T755`) and updated `## Sources`.

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `COVERAGE OK` (`requirements: 32308`, `gaps: 0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T752` → `4 STAGE`, `0 REFUSED`

## Files changed

- `spec/SPEC-21-query-engine-semantic-db.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

STATUS: COMPLETE round=0
