# T627 Report — E15.8 — Canonical register allocation, instruction selection & machine optimization specification (SPEC-77)

## Tóm tắt
Đã viết đặc tả chuẩn `spec/SPEC-77-regalloc-machine-opt.md` cho Epic `E15.8` (Phase P15 `P15-optimizer-2-0`), hợp nhất các nguồn `0162 §36–40`, `0182`, `0235`, `0237`, `0252`, `tasks/0406`, `tasks/0553`, `tasks/0557`, `tasks/0559` và `SPEC-04 AXS-EXT-050..060` thành bộ quy tắc đánh số ổn định `AXS-RA-010..027` và `AXS-MCOPT-001..026`:
- Chuẩn hóa phân tích độ sống ngược trên CFG theo RPO tất định (`AXS-RA-012..013`), cấu trúc khoảng sống `LiveInterval` kèm `UsePos` (`AXS-RA-014`), các lớp thanh ghi theo ABI (`Gpr`, `Xmm`, `Vec128`/`Vec256` — `AXS-RA-010..011`), và công thức trọng số tràn thanh ghi theo độ sâu vòng lặp $10^d$ (`AXS-RA-015`, `REQ-OPT-201..202`).
- Chuẩn hóa thuật toán cấp phát thanh ghi quét tuyến tính ở `-O1`/`-O2` (`AXS-RA-020..021`), tiền tô màu & mặt nạ clobber cho lệnh thanh ghi cố định (`RCX` cho dịch bit biến thiên, `RAX`/`RDX` cho `idiv`/`div`/`mul`, clobber tại điểm gọi hàm `call` — `AXS-RA-022..023`), hợp nhất lệnh gán `mov` và giải chu trình copy song song (`AXS-RA-024`), tô màu tái sử dụng khe tràn ngăn xếp (`AXS-RA-025`), tích hợp bảo toàn thanh ghi callee-saved (`RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15`, `XMM6`–`XMM15`) vào `FrameLayout` (`AXS-RA-026`), và hợp đồng trình kiểm định `x64_verify` (`AXS-RA-027`).
- Chuẩn hóa lựa chọn lệnh theo mẫu (`lea` với `base + index*scale + disp`, gộp toán hạng tức thời/bộ nhớ, giảm cường độ nhân/chia hằng số — `AXS-MCOPT-010..012`), chuyển đổi nhánh kim cương thuần khiết sang `cmovcc`/`setcc` không rẽ nhánh (`AXS-MCOPT-013..014`, `REQ-OPT-205..208`, `REQ-OPT-369..370`), và mô hình chi phí vi kiến trúc tách biệt độ trễ / thông lượng / kích thước mã khỏi tính hợp lệ ngữ nghĩa (`AXS-MCOPT-001..005`, `REQ-OPT-197..200`).
- Chuẩn hóa bộ tối ưu hóa peephole hậu cấp phát (`AXS-MCOPT-020..026`, `REQ-OPT-015`, `REQ-OPT-030..036`, `REQ-OPT-371..372`): theo dõi độ sống cờ `EFLAGS` tường minh (`flags_are_dead_after`), rút gọn `mov r, r`, `mov r, 0` → `xor r, r` (khi `EFLAGS` chết), `cmp r, 0` → `test r, r`, xóa nhảy thừa, và rào cản nghiêm ngặt bảo vệ `volatile`, `atomic`, bẫy tràn số `Assert` và lệnh gọi hàm.
- Cập nhật `spec/INDEX.md`, `spec/diagnostics.md` (`AXD-042`), và `spec/invariants.md` (`INV-PIPE-006`, `INV-PIPE-007`).

## Summary
Authored the canonical specification `spec/SPEC-77-regalloc-machine-opt.md` for E15.8 (linear-scan register allocation, spill/reload generation, callee-saved `FrameLayout` integration, pattern-matching instruction selection, branchless `cmovcc`/`setcc` if-conversion, microarchitectural cost modeling, and post-RA machine peephole optimization) and updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

### Key rules defined in `spec/SPEC-77-regalloc-machine-opt.md`
1. **Pipeline Boundary & Microarchitectural Cost Model (`AXS-MCOPT-001`–`AXS-MCOPT-005`)**:
   - Enforces the LIR / Machine IR boundary (`REQ-OPT-015`, `REQ-OPT-031`, `REQ-OPT-371`, `REQ-OPT-372`) and observable equivalence across `--interp`, `-O0`, `-O1`, and `-O2` (`REQ-OPT-030`, `REQ-OPT-197`, `REQ-OPT-212`).
   - Separates ISA legality from `TargetCostModel` profitability (`latency`, `throughput_rcp`, `code_bytes`; `REQ-OPT-198..200`) and integrates per-class register pressure and explicit loop-weighted spill costs (`REQ-OPT-201..202`) with deterministic tie-breaking (`REQ-OPT-203..204`, `REQ-OPT-218`).
2. **Register Classes, Liveness & Live Intervals (`AXS-RA-010`–`AXS-RA-015`)**:
   - Specifies register classes (`Gpr`, `Xmm`, `Vec128`/`Vec256` per `SPEC-04 AXS-EXT-050/053/060`), Windows x64 volatile vs. non-volatile partitions, deterministic RPO instruction numbering, backward bitset dataflow liveness with loop-header closure, `LiveInterval` / `UsePos` data structures, and the loop-depth $10^d$ spill-weight formula.
3. **Linear-Scan Register Allocation & Frame Integration (`AXS-RA-020`–`AXS-RA-027`)**:
   - Specifies the `-O1`/`-O2` linear-scan algorithm (`T063`), fixed-register precoloring and clobbers (`RCX` variable shifts, `RAX`/`RDX` `idiv`/`div`/`mul`, two-address tied operands, call clobbers), copy coalescing and parallel-copy cycle resolution, spill-slot lifetime coloring isolated from address-taken locals, callee-saved register save/restore in `X64FrameLayout` (`RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15`, `XMM6`–`XMM15`), and the post-RA `x64_verify` contract.
4. **Instruction Selection & Branchless If-Conversion (`AXS-MCOPT-010`–`AXS-MCOPT-014`)**:
   - Specifies `base + index*scale + disp` addressing mode formation and `lea` selection (excluding checked overflow operations), immediate/memory operand folding, constant multiply/divide/modulo strength reduction, and pure trap-free diamond if-conversion to `cmovcc`/`setcc` (`T628`, `REQ-OPT-205..208`, `REQ-OPT-369..370`).
5. **Post-RA Machine Peephole Optimization (`AXS-MCOPT-020`–`AXS-MCOPT-026`)**:
   - Specifies structured `X64MI` peephole rewrites (`T628`), explicit `EFLAGS` liveness (`flags_are_dead_after`, `REQ-OPT-033`), self-move and identity elimination, flag-safe `mov r, 0` → `xor r, r` and `cmp r, 0` → `test r, r`, fall-through branch cleanup, and strict barriers protecting `volatile`, `atomic`, `Assert` traps, and calls (`REQ-OPT-032`, `REQ-OPT-034..035`).

## Files changed
- spec/INDEX.md
- spec/SPEC-77-regalloc-machine-opt.md
- spec/diagnostics.md
- spec/invariants.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1 PASS` .. `MS-P10b PASS` (exit 0).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T627`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
