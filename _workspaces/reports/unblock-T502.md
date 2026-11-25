# Unblock T502 — Oracle strict-provenance & UB detector

## Tóm tắt
- Bộ phát hiện đọc bộ nhớ chưa khởi tạo (UB-04) của T502 đúng: nó bắt được lỗi đọc vượt vùng cấp phát thật trong
  `compiler/target/x64/frame.ax`. `x64_frame_has_meta` luôn đọc 5 word trailer sau `slot_count` phần tử của
  `slot_offsets`, nhưng builder baseline và raw chỉ cấp phát `slot_count * 4` byte.
- Lỗi gốc là hợp đồng ngầm: hàm đọc giả định trailer luôn có, còn chỉ builder `-O1` cấp phát và ghi nó.
  ADR-0052 + SPEC-77 AXS-RA-026 mục 4: trailer là phần bắt buộc của mọi `slot_offsets` khác null (toàn 0 = không
  có metadata), cấp phát qua một hàm duy nhất `frame_alloc_slot_offsets`, hằng `X64_FRAME_META_WORDS = 5`.
- Cách làm: thêm khoá `compiler/target/x64/frame.ax` vào T502 (không task đang chạy nào chạm file này). Không tạo
  task sửa riêng vì chỉ detector của T502 mới quan sát được lỗi — gate của T502 chính là phép thử.
- `data.ub_kind`: kỹ sư nhầm — `Diagnostic` đã có `data`/`DiagDataEntry`. Đưa vào phạm vi T502 (rẻ, nằm trong
  `compiler/interp`).
- UB-06 (vi phạm khoá `view`/`mut_view` qua con trỏ thô) cần thông tin last-use: tách sang task mới T542 (opus),
  chuyển REQ-CAP-071 sang T542, T505 phụ thuộc T542.
- `@addr` static cấp item có initializer: đã có T526/T528/T540 lo, không tạo task mới.

## Decision

### 1. frame.ax out-of-bounds read (TYPE B, ADR-0052)
Options considered:
1. Pad the two allocations with 5 zeroed words (engineer's snapshot fix): correct, but the contract stays
   implicit and the next builder (T472 owns `frame.ax` for SSE2 work) can repeat it.
2. **Chosen:** make the trailer mandatory in the allocation contract — `X64_FRAME_META_WORDS`, one helper
   `frame_alloc_slot_offsets` used by all three builders, zero trailer = "no metadata". Recorded in SPEC-77
   AXS-RA-026 item 4.
3. Explicit metadata fields in `X64FrameLayout`: cleanest, but changes a struct mirrored by the C test drivers
   (`tests/mc/isel/cdriver_abi*.c`, under running T503) and several construction sites; disproportionate.
4. Bounds-checked probe: needs a length field (same cost as 3).

Where to implement: added `locks: [compiler/target/x64/frame.ax]` to T502 instead of a prerequisite task. The
change is ≈ 30 lines, fully specified by ADR-0052, and the only test that can observe the bug is T502's own
detector (a separate fix task would have no observable acceptance test). Conflict check: running T503
(`tests/ffi/win64_abi_oracle`, `tests/mc/isel`) and T461a (locks `compiler/backend`, `compiler/lir`,
`compiler/link`, `compiler/obj`) do not touch `compiler/target/x64/frame.ax`; T472 (todo) owns it in `paths:` and
is serialised by the lock. The working tree has no uncommitted change under `compiler/target`.

### 2. Engineer's "not done" list
| Item | Real gap vs T502? | Decision |
|------|-------------------|----------|
| UB-06 (raw access vs active `view`/`mut_view` lock) | In T502's scope text, not in its acceptance list; normative in SPEC-50 AXS-UNS-014/015 | New task **T542** (opus, depends T502, locks `compiler/interp`, `compiler/own`): oracle consumes capability last-use facts from the ownership analysis, no lexical approximation (ADR-0034). T502 scope text updated; REQ-CAP-071 moved from T502 to T542 (CATALOG); T505 depends on T542 |
| `data.ub_kind` payload | Yes — AXS-UNS-015 requires it; the claim "Diagnostic has no data payload" is wrong (`Diagnostic.data`/`DiagDataEntry` in `compiler/diag/emitter.ax`, emitted by `compiler/diag/json.ax`) | Added to T502 scope + acceptance (structured entry, pinned by tests) |
| Item-scope `@addr(A) static S: T = init` rejected by T501 typeck | Not a T502 gap (oracle cannot evaluate what typeck rejects); acceptance round-trips are met with overlay statics and block-scope initialisers | Already owned by T526/T528 (lift the bootstrap rejection) and T540; no new task |
| Wider run may find more latent reads | Possible | T502 acceptance now says: list each flagged site outside `paths:`/`locks:` in "Spec deviations" and block; never weaken the detector. The periodic full run also covers it |

## Board changes
- T502: status blocked → todo (`taskctl unblock`); `locks: [compiler/target/x64/frame.ax]`; spec adds SPEC-77 and
  ADR-0052; scope adds the ADR-0052 fix and `data.ub_kind`; UB-06 moved out; acceptance adds `ub_kind` pinning,
  the smoke test and the "never weaken the detector" rule; covers drops REQ-CAP-071.
- T542 (new): E13.1 oracle UB-06 capability-alias detector.
- T505: depends adds T542.
- Checks: `taskctl.py lint` (T502, T542) OK; `taskctl.py validate` OK (775 tasks); `harness_check.py` HARNESS OK;
  `reqcov.py --strict` COVERAGE OK.

## Files changed
- spec/decisions/ADR-0052-x64-frame-meta-trailer-contract.md
- spec/SPEC-77-regalloc-machine-opt.md
- spec/requirements/CATALOG.md
- _workspaces/tasks/todo/T502-e13-1-oracle-strict-provenance-ub-detector.md
- _workspaces/tasks/todo/T505-e13-1-unsafe-ub-ffi-req-owner-008-conformance.md
- _workspaces/tasks/todo/T542-e13-1-oracle-ub06-capability-alias-detector.md
- _workspaces/reports/unblock-T502.md
