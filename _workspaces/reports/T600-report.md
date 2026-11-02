# T600 Report — E15.1 — Canonical OptIR, SSA/MemorySSA & pass-legality specification (SPEC-70)

## Tóm tắt
Đã viết đặc tả chuẩn `spec/SPEC-70-optir-ssa-memoryssa.md` cho Epic `E15.1` (Phase P15 `P15-optimizer-2-0`), hợp nhất các nguồn `0161 §17/§37`, `0162 §40`, `0165 §1–16`, `0261 §27`, `0309 §1–4`, `tasks/0315`, `tasks/0366` (`AOPT-20..65`), `tasks/0398` (`AOPTIR-20..75`), `tasks/0399` (`AOPT-70..110`), `tasks/0545`–`tasks/0547`, `tasks/0794`–`tasks/0797`, `SPEC-03` và `SPEC-04 §5` thành bộ quy tắc đánh số ổn định `AXS-OPT-001..047`:
- **Phân tách vai trò nghiêm ngặt giữa `Verified MIR` và `OptIR` (`AXS-OPT-001..006`)**: Chốt `Verified MIR` là mô hình thực thi ngữ nghĩa duy nhất có thẩm quyền (`REQ-OPT-010`, `REQ-OPT-016..017`, `REQ-OPT-296`, `REQ-OPT-325`, `REQ-OPT-360`). `OptIR` được xây dựng độc quyền từ `Verified MIR` (`REQ-OPT-047..049`, `REQ-OPT-053`, `REQ-OPT-059`, `REQ-OPT-324`, `REQ-OPT-362`), xóa bỏ hoàn toàn metadata chỉ dành cho compiler sau khi chuyển thành sự kiện phân tích (`REQ-OPT-037..040`, `REQ-OPT-298`, `REQ-OPT-322..323`), bảo toàn nguồn gốc vị trí mã nguồn `OptOrigin` (`REQ-OPT-329`, `REQ-OPT-341`), và điều phối các phân tích qua `AnalysisOrchestrator` với dàn phẳng 3 giá trị `Certainty = Proven | Possible | Unknown` kèm `ProofProvenance` (`REQ-OPT-359`, `REQ-OPT-390..392`, `REQ-OPT-397..403`).
- **Biểu diễn `SSA`, cây thống trị và `SROA` (`AXS-OPT-010..015`)**: Quy định cấu trúc `OptBody` / `OptBlock` / `OptValue` / `OptPhi` / `OptInst`, cây thống trị Cooper-Harvey-Kennedy (`DominatorTree`), biên thống trị (`DominanceFrontier`), đặt nút `phi` tối thiểu, phân biệt giá trị `SSA` với đối tượng sở hữu (`Move`/`Copy` hạ xuống đổi tên giá trị `SSA` không chép vật lý, giữ nguyên `Clone` tường minh — `REQ-OPT-023`, `REQ-OPT-054`, `REQ-OPT-304..306`, `REQ-OPT-326`, `REQ-OPT-337..338`), tách trường vô hướng `SROA` bảo toàn tuyệt đối thứ tự và cờ `Drop` (`REQ-OPT-050`, `REQ-OPT-055`), và định dạng in tất định `inspect --emit=optir` / `--emit=memssa`.
- **`MemorySSA`, `AliasInfo` & suy luận hiệu ứng `EffectInfo` (`AXS-OPT-020..024`)**: Quy định `LiveOnEntry`, `MemoryDef`, `MemoryUse`, `MemoryPhi` (`REQ-OPT-057`, `REQ-OPT-327`), phân vùng `MemoryRegion` theo miền lưu trữ (`REQ-OPT-058`), dàn phẳng 5 mức `AliasResult` (`NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`, `UnknownAlias`) cùng hàm truy vấn clobber `memssa_does_clobber` (`REQ-OPT-051`, `REQ-OPT-056`, `REQ-OPT-328`), và hệ thống suy luận hiệu ứng bảo thủ `EffectSummary` (`REQ-OPT-321`, `REQ-OPT-348..349`, `REQ-OPT-393..396`, `REQ-VER-027`).
- **Khung hợp đồng `PassManager` & trình kiểm định biến đổi (`AXS-OPT-030..034`)**: Quy định theo dõi phụ thuộc và vô hiệu hóa phân tích theo `ir_revision` (`REQ-CORE-447`, `REQ-OPT-052`, `REQ-OPT-350`), khai báo `TransformationContract` (`REQ-OPT-060`, `REQ-OPT-331`, `REQ-OPT-356`, `REQ-OPT-404..406`), cổng chứng minh đóng an toàn (fail-closed) khi không đạt `Certainty.Proven` (`REQ-OPT-062`, `REQ-OPT-064`, `REQ-OPT-332`, `REQ-OPT-402`), lập lịch pha tối ưu theo mục tiêu `OptProfile` / `OptBudget` (`REQ-OPT-065`, `REQ-OPT-373..374`), và tái kiểm định sau mỗi pha dưới `--verify-each` (`REQ-OPT-361`, `REQ-OPT-404`).
- **Bảo toàn hành vi quan sát được & tối ưu hóa vô hướng (`AXS-OPT-040..047`)**: Quy định bảo toàn kết quả trả về, bẫy tràn số học có kiểm tra so với `wrapping_*`, thứ tự `Drop`, I/O, `atomic`, `volatile`, FFI, rào cản `black_box` và xóa bộ nhớ nhạy cảm `zeroize` trong SCCP, `InstCombine`, GVN/CSE và DCE (`REQ-OPT-011`, `REQ-OPT-014`, `REQ-OPT-018..022`, `REQ-OPT-339..340`, `REQ-OPT-343`, `REQ-OPT-351..355`, `REQ-OPT-363..364`).
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-042`), và `spec/invariants.md` (`INV-PIPE-008`).

## Summary
Authored the canonical specification `spec/SPEC-70-optir-ssa-memoryssa.md` for E15.1 (Unified Dataflow Optimization IR `OptIR`, SSA and `MemorySSA` representation, `AnalysisOrchestrator` & 3-valued `Certainty` lattice, `PassManager` transformation contracts, and scalar optimization legality) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

### Key rules defined in `spec/SPEC-70-optir-ssa-memoryssa.md`
1. **Architectural Role Separation (`AXS-OPT-001`–`AXS-OPT-006`)**:
   - Enforces the `Verified MIR` entry gate (`REQ-OPT-010`, `REQ-OPT-016..017`, `REQ-OPT-296`, `REQ-OPT-325`, `REQ-OPT-360`) and separates place-oriented `MIR` from value-based `OptIR` (`REQ-OPT-047..049`, `REQ-OPT-053`, `REQ-OPT-059`, `REQ-OPT-324`, `REQ-OPT-362`).
   - Specifies compiler-derived capability/ownership optimization facts, zero-cost abstraction erasure (`REQ-OPT-037..040`, `REQ-OPT-298`, `REQ-OPT-322..323`), `OptOrigin` source-to-machine provenance (`REQ-OPT-329`, `REQ-OPT-341`), and the `AnalysisOrchestrator` with the `Certainty = Proven | Possible | Unknown` lattice and `ProofProvenance` records (`REQ-OPT-359`, `REQ-OPT-390..392`, `REQ-OPT-397..403`).
2. **`OptIR` SSA Representation, Dominance & Aggregate Scalarization (`AXS-OPT-010`–`AXS-OPT-015`)**:
   - Defines `OptBody`, `OptBlock`, `OptValue`, `OptPhi`, `OptInst`, and `OptTerminator`, Cooper-Harvey-Kennedy `DominatorTree`, `DominanceFrontier`, and minimal iterated dominance frontier (`IDF`) phi placement.
   - Distinguishes SSA values from ownership slots (`REQ-OPT-023`, `REQ-OPT-054`, `REQ-OPT-326`), lowers unobservable moves/copies to SSA value renaming while preserving explicit `Clone` (`REQ-OPT-304..306`, `REQ-OPT-337..338`), specifies `SROA` with strict `Drop` preservation (`REQ-OPT-050`, `REQ-OPT-055`), and defines `inspect --emit=optir` and `--emit=memssa`.
3. **`MemorySSA`, Alias Integration & Canonical Effect Inference (`AXS-OPT-020`–`AXS-OPT-024`)**:
   - Defines `LiveOnEntry`, `MemoryDef`, `MemoryUse`, and `MemoryPhi` (`REQ-OPT-057`, `REQ-OPT-327`), storage-domain `MemoryRegion` descriptors (`REQ-OPT-058`), the 5-valued `AliasResult` lattice and `memssa_does_clobber` queries (`REQ-OPT-051`, `REQ-OPT-056`, `REQ-OPT-328`), and conservative `EffectSummary` inference (`REQ-OPT-321`, `REQ-OPT-348..349`, `REQ-OPT-393..396`, `REQ-VER-027`).
4. **Optimization Pass Manager & Transformation Contracts (`AXS-OPT-030`–`AXS-OPT-034`)**:
   - Specifies `PassManager` analysis dependency/invalidation tracking (`REQ-CORE-447`, `REQ-OPT-052`, `REQ-OPT-350`), `TransformationContract` declarations (`REQ-OPT-060`, `REQ-OPT-331`, `REQ-OPT-356`, `REQ-OPT-404..406`), fail-closed proof checking and rollback (`REQ-OPT-062`, `REQ-OPT-064`, `REQ-OPT-332`, `REQ-OPT-402`), objective-driven pipeline planning (`REQ-OPT-065`, `REQ-OPT-373..374`), and `--verify-each` reverification (`REQ-OPT-361`, `REQ-OPT-404`).
5. **Observable Behavior Preservation & Scalar Optimization (`AXS-OPT-040`–`AXS-OPT-047`)**:
   - Specifies observable equivalence (`REQ-OPT-018..019`, `REQ-OPT-041`, `REQ-OPT-297`, `REQ-OPT-340`, `REQ-OPT-355`), checked vs. wrapping arithmetic algebraic rules without C/C++ signed-overflow UB assumptions (`REQ-OPT-020..021`, `REQ-OPT-363..364`), `Drop` ordering (`REQ-OPT-055`), I/O/atomic/volatile/FFI barriers (`REQ-OPT-061`, `REQ-OPT-063`, `REQ-OPT-339`), `black_box` and cryptographic zeroization barriers (`REQ-OPT-011`, `REQ-OPT-351..353`), SCCP (`AXS-OPT-045`), GVN/CSE (`AXS-OPT-046`), and effect-aware DCE (`AXS-OPT-047`, `REQ-OPT-022`).

## Files changed
- spec/INDEX.md
- spec/SPEC-70-optir-ssa-memoryssa.md
- spec/diagnostics.md
- spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1 PASS` .. `MS-P10b PASS` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T600`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
