# T768 Report — E18.5 — Canonical Pass Contracts & Proof-Carrying Transformation Specification (`SPEC-25`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-25-pass-contracts-proof-carrying-ir.md` (`AXS-PCT-001`..`053`) cho hệ thống hợp đồng pha biên dịch, chứng chỉ biến đổi mang bằng chứng và kiểm chứng dịch thuật hữu hạn (E18.5):
1. **Lược đồ hợp đồng pha biên dịch `PassContract` & giao dịch nguyên tử (`AXS-PCT-001`..`005`)**: Quy định mọi pha ngữ nghĩa, tối ưu hóa và hạ bậc mã máy bắt buộc khai báo `PassContract` gồm mức IR (`input_ir`/`output_ir`), phân tích/tiền điều kiện bắt buộc (`required_analyses`, `required_propositions`), phân tích được bảo toàn (`preserved_analyses`), phân tích bị làm cũ (`invalidated_analyses`), thuộc tính ngữ nghĩa bất biến (`preserved_properties`: kiểu, sở hữu, capability, `Drop`, bộ nhớ/hiệu ứng quan sát được, tràn số có kiểm tra, `volatile`, `atomic`, ABI) và hậu điều kiện (`postconditions`). Thực thi theo giao dịch có khả năng hoàn tác (rollback) nguyên tử và tường lửa tách biệt bằng chứng ngữ nghĩa với mô hình chi phí (`CostModel`).
2. **Chứng chỉ biến đổi mang bằng chứng (`ProofCertificate` / `ProofProvenance`) & cổng đóng an toàn (`AXS-PCT-010`..`015`)**: Chuẩn hóa dàn độ chắc chắn 3 giá trị (`Proven`, `Possible`, `Unknown`, `tasks/0794`), cơ sở hạ tầng CFG/Dataflow dùng chung (`Source Analysis 2.0`, `tasks/0793`), hệ thống suy luận hiệu ứng đa danh mục (`Effect System 2.0`, `tasks/0795`), và bộ thực thi ký hiệu hữu hạn nội tại không phụ thuộc bộ giải SMT ngoài (`Symbolic Execution 2.0`, `tasks/0796`). Mỗi `ProofCertificate` gắn với `ir_revision` và tự động bị vô hiệu hóa bắc cầu khi định nghĩa IR thay đổi; mọi nghĩa vụ chứng minh trả về `Possible` hoặc `Unknown` bắt buộc đóng an toàn (hoàn tác ứng viên biến đổi mà không phát sinh lỗi người dùng).
3. **Kiểm chứng dịch thuật hữu hạn (`TranslationWitness`) xuyên suốt MIR, `OptIR`, LIR, RegAlloc & Scheduling (`AXS-PCT-020`..`024`, `AXS-PCT-050`..`053`)**: Định nghĩa phân cấp tương đương ngữ nghĩa 5 mức và kiểm tra chứng nhân `TranslationWitness` cho từng hàm qua các phép biến đổi vô hướng/CFG/bộ nhớ/vòng lặp (`tasks/0798`), hợp thức hóa đích & khoảng sống/khe tràn thanh ghi (`tasks/0799`), bảo toàn phụ thuộc `RAW`/`WAR`/`WAW` và rào cản `volatile`/`atomic`/`trap` khi lập lịch lệnh (`tasks/0800`), và cổng hoàn tất mã máy cuối cùng (`tasks/0801`), cùng các cờ `--verify-pass-contracts`, `--validate-translations`, `inspect --emit=pass-witness` và bất biến `INV-PCT-001`..`003`.

## Architecture Decisions & Rule Summary
- **`AXS-PCT-001`..`005`**: Mandatory `PassContract` descriptors (`IrLevel`, `AnalysisKind`, `SemanticProperty`, `ValidationStrategy`, `PassFailurePolicy`), topological `AnalysisOrchestrator` scheduling, automatic stale-marking of non-preserved analyses on IR mutation, transactional snapshot-and-commit execution with clean rollback, and the semantic-vs-profitability firewall.
- **`AXS-PCT-010`..`015`**: Three-valued `Certainty` lattice (`Proven`, `Possible`, `Unknown`) and fail-closed rollback gate; `ProofCertificate` and `ProofProvenance` schema with `ir_revision` tracking and transitive invalidation; `Source Analysis 2.0` shared CFG/dominance/liveness authority; `Effect System 2.0` multi-category lattices, `Unknown` non-downgrade rule, callback/cleanup/MMIO/comptime rules, and monotonic SCC convergence; `Symbolic Execution 2.0` bounded in-process abstract domains (no external SMT dependency); and auditable `TrustedBoundary` assumptions.
- **`AXS-PCT-020`..`024`**: Five-tier semantic equivalence hierarchy (`Level 0`..`Level 4`) and per-function `TranslationWitness`; middle-end scalar/CFG/memory/loop validation; target legalization and register allocation live-range/spill/coalescing witness validation; instruction scheduling `RAW`/`WAR`/`WAW` and `volatile`/`atomic`/`trap` barrier validation; and `FinalMachineIr` frame/prologue/epilogue/unwind/security verification gate.
- **`AXS-PCT-050`..`053`**: CLI verification flags (`--verify-pass-contracts`, `--validate-translations`, `inspect --emit=pass-witness`), diagnostic distinction between fail-closed `Unknown` rollback (0 diagnostics) and committed pass contract/witness violations (`AX_ICE_MIR_VERIFY` / `AX_ICE_INTERNAL`), positive/negative canonical Axiom examples (`=` and `.` syntax), and E18.5 verification matrix (`T769`–`T771`).

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T768`

## Files changed
- spec/SPEC-25-pass-contracts-proof-carrying-ir.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

STATUS: COMPLETE round=0
