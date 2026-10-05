# ADR-0012 — Core execution semantics v0.1 and the milestone manifest format

## Tóm tắt
Tài liệu gốc mâu thuẫn ở nhiều điểm ngữ nghĩa lõi mà oracle và backend native phải thống nhất tuyệt
đối. Quyết định (T003):
1. **Tràn số nguyên luôn bị kiểm tra và panic ở mọi bản build** (theo 0032 §16, 0041 §42 và tài
   liệu mới hơn tasks/0334 §7 / ANUM-27), không lấy phương án "mặc định modulo" của tasks/0327 §4.
   Muốn modulo thì dùng `wrapping_*` tường minh.
2. **Mọi lỗi số học (chia 0, `MIN / -1`, `MIN % -1`, dịch bit ngoài phạm vi) là panic**, không phải
   trap — một đường lỗi duy nhất, native kiểm tra trước khi chạy lệnh máy.
3. **Panic = abort**: không chạy destructor, in `panic: <thông điệp>` ra stderr, mã thoát **101**;
   `unreachable()` luôn là panic có kiểm tra, không bao giờ là giả định tối ưu.
4. **Phép gán đánh giá vế phải trước**, kể cả phép gán kết hợp (`+=`), rồi mới tới toán hạng của vị
   trí đích; mỗi toán hạng chỉ đánh giá một lần.
5. **`as` giữa số nguyên là chuyển đổi modulo (cắt bớt)**, không panic; chỉ `u32 as char` có kiểm tra.
6. **`main`** nhận `()`, `i32`, `u32` hoặc `never`; mã thoát là mẫu bit 32 của giá trị.
7. Oracle có giới hạn 50 triệu bước và 100 000 lớp gọi; vượt thì mã thoát 124 kèm chẩn đoán.
8. **Manifest milestone** là khối ```` ```milestone ```` chứa JSON trong SPEC-00, do
   `tools/gatecheck.py` (T022) đọc.
9. **Native không bao giờ lệch âm thầm khỏi oracle**: ngay từ VS1 (T028), phép `+ - *` và đổi dấu
   trên `i32`/`i64` có kiểm tra tràn bằng một lệnh `jo` nhảy tới stub `__ax_panic_overflow` do linker
   sinh (thoát 101); cấu trúc nào backend chưa hạ được thì axiom0 từ chối build
   (`AX_DRIVER_NOT_YET_SUPPORTED`, họ mã tạm thời AXD-014), không bao giờ bỏ phép kiểm tra.
Revisit: có — mục 1 (hiệu năng của kiểm tra tràn số trước khi có tối ưu P15) và mục 3 (chiến lược
unwind ở E13.5).

Status: **Accepted** (architect, T003). Date: 2026-10-04.
Revisit: yes — §1 (cost of overflow checks before the P15 optimizer; a wrapping-by-default region
attribute could be proposed in E12.1) and §3 (unwinding, E13.5).

## Context
SPEC-03 must freeze the semantics both executors implement (0263 §25, tasks/0262 §10, ABOOT-76).
The corpus disagrees:
- Default integer arithmetic: wrapping (tasks/0327 §4, ANUM-28) vs checked (0032 §16, 0041 §42,
  tasks/0334 §7 and ANUM-27, tasks/0334 being the later revision of the numeric model); 0068 §28
  leaves it open; 0010 §15 leans to checked/trap.
- Arithmetic failures: panic (0032 §18-20) vs trap (0068 §29) vs either (0010 §16, tasks/0334 §13).
- Integer `as` narrowing: checked or truncating left open (tasks/0334 §18).
- Panic: abort vs unwind are profiles (0010 §7, 0068 §9); no exit code is given anywhere.
- Assignment: "RHS first" (0032 §8, 0041 §37) but compound assignment only says "evaluate the place
  once" (0041 §40).
- `main`: only `-> i32` is shown (0263 §6); SPEC-02 EX-10 uses `fn main() -> u32`.
- Milestone manifests: 0263 §44 shows Markdown, 0264 §19 recommends JSON; T022 needs one format.

## Options and decisions

1. **Overflow.** (a) wrapping default; (b) checked in debug, wrapping in release (Rust); (c) checked
   in every build. *Chosen (c)*: it is the later and frozen position (tasks/0334 ANUM-25..27, 0032
   AES-19/21), keeps debug = release (tasks/0334 §7), and differential testing at -O0/-O1 needs one
   semantics. (a) hides bugs in compiler code (index arithmetic); (b) creates two semantics. Cost:
   a `jo` per operation in naive axiom0 code — acceptable for bootstrap; P15 removes proven checks.
   Hashing uses the explicit `wrapping_*` intrinsics (ADR-0004 §1).
2. **Arithmetic failures.** (a) trap (hardware exception / `ud2`); (b) panic. *Chosen (b)*: one
   path with a message and a fixed exit code in both executors; a trap would give a platform status
   (0xC0000094 on Windows) that the oracle cannot reproduce meaningfully. `MIN % -1` also panics
   (consistent with `MIN / -1`; x86 `idiv` faults on it).
3. **Panic.** Abort only in v0.1; exit code 101 (outside the 0..3 compiler statuses, below 128,
   well known from Rust, valid on every OS); message line on stderr; no destructors (the OS reclaims
   resources; unwinding needs unwind tables, E13.5/E17.3). `unreachable()` is a checked panic: an
   optimisation assumption would be undefined behaviour in safe code (contradicting AES-19).
4. **Assignment order.** (a) place first, then RHS; (b) RHS first for `=` and place-first for `op=`
   (Rust's split); (c) RHS first for every assignment. *Chosen (c)*: simplest rule, matches 0032 §8
   and 0041 §37, and 0041 §40's "evaluate the place once" holds.
5. **Casts.** Integer `as` is modular (truncating) — the compiler's byte extraction (`x as u8`)
   needs it, and checked narrowing belongs to a library `try_from` (E12.1). `char` casts follow
   ADR-0006 §2; `char` → narrower integers are rejected to avoid silent truncation of scalars.
6. **`main`.** Accept `()`, `i32`, `u32`, `never`; the exit code is the 32-bit pattern. Parameters
   are rejected (arguments come from host intrinsics, ADR-0002).
7. **Oracle limits.** Step limit 50 000 000 (≈ 5 s at the T021 throughput target, below the
   runner's 10 s timeout), call-depth limit 100 000, exit code 124 with an `AX_DRIVER_INTERP_*`
   diagnostic (the runner reports TIMEOUT); oracle-detected UB in `unsafe` code exits 125 with
   `AX_UNSAFE_INTERP_UB`. Codes as agreed with the registry (T002, ADR-0011).
8. **Manifests.** JSON (0264 §19) inside fenced ```` ```milestone ```` blocks of SPEC-00, so the
   ladder, its prose and the machine-readable lists live in one reviewed file; field list and
   gatecheck algorithm in SPEC-00 AXS-BOOT-050/051.

9. **Native contract before the native catch-up tasks** (added in T003 round 1, QA finding F2).
   FP-03 builds `40 + 2` as a checked `Add` with an overflow assert, and that program is in the VS1
   set of T028, yet general branches arrive in T033 and the overflow checks were scheduled for T037.
   Options: (a) drop the assert in native code until T037 (a "no trap" shortcut): native would wrap
   where the oracle panics, which violates AXS-SEM-001/030 and the T029 differential cannot see it
   because the overflow tests are skipped natively; rejected. (b) Native refuses any function whose
   MIR contains a check: even `return 40 + 2` would be excluded from VS1, so the first native slice
   would shrink to constants and locals, against 0263 §32-37; rejected. (c) Lower the overflow
   assert from day one to one conditional jump (`jo rel32`, already an encoder form of T024) to a
   linker-synthesised per-kind abort stub `__ax_panic_<kind>`, exactly
   `and rsp, -16; sub rsp, 32; mov ecx, 101; call [ExitProcess]`. The stub is
   entered by `jo`, a jump, so `rsp` may be 0 or 8 (mod 16) on arrival; the `and` re-aligns it, the
   `sub` reserves the shadow space, and the stub never returns. T027's fixture test jumps to it from
   both alignments (the message is added by T042, after the same prologue). This needs no basic-block splitting and no general branch
   lowering. *Chosen (c)* for signed `i32`/`i64` `+ - *` and unary `-`, the arithmetic of VS1.
   For everything else whose native lowering does not exist yet (branches, calls, other widths,
   division, shifts, bounds, `char`), `axiom0 build` reports `AX_DRIVER_NOT_YET_SUPPORTED`
   (AXD-014 family; data `construct="native:<feature>"`, `task` = the delivering native task)
   instead of emitting code. Dropping a check is never a permitted BOOTSTRAP-SHORTCUT. The T029
   differential includes the overflow test FP-10 natively. Rules: SPEC-00 AXS-BOOT-006/007.

## Consequences
- SPEC-03 (AXS-SEM-001..092) and SPEC-00 (AXS-BOOT-001..070, 11 manifest blocks) written by T003.
- T017 (literal typing, `main` checks), T019 (evaluation order, checked ops), T021 (panic exit 101,
  step/depth limits), T034 (cast table, intrinsics, `assert`/`unreachable`), T037 (native checks),
  T041 (`panic(msg)`), T042 (native panic line), T043 (keep panics) implement the rules as written.
- T005 (runner) maps exit code 124 + `AX_DRIVER_INTERP_*` to TIMEOUT and recognises the ICE banner
  rather than exit code 3 inside `run --interp` (SPEC-03 AXS-SEM-082).
- T022 implements `tools/gatecheck.py` per AXS-BOOT-051.
- §9 board edits (applied by a later architect run): T023 (`check_ovf` LIR op), T025 (`jo` to
  `__ax_panic_<kind>`; the refusal diagnostic), T027 (panic stubs), T028 (FP-10 natively, refusal),
  T029 (overflow in the differential), T037 (the remaining checks), T042 (stub message), T024
  (confirm `jcc rel32` with a symbol relocation), T025b (machine-IR verifier and frame lowering
  accept a mid-block `jo rel32` to an external symbol with no epilogue path), T002/T009 (register
  `AX_DRIVER_NOT_YET_SUPPORTED` in the AXD-014 DRIVER family), T006
  (`tools/tests/archcheck/run_selftests.py`), T004/T007 (a `*.test` manifest under
  `tests/unit/driver`).

## Sources
0032 §1-20, §47-51; 0010 §6-18; 0041 §19, §32-45; 0068 §8-13, §28-29, §36-37; tasks/0327 §3-16,
§31, ANUM-20..51; tasks/0334 §6-18, §34-35, ANUM-25..40; 0263 §6, §11, §25, §32-45, §51; 0264
§18-20; tasks/0262 §10, §55; tasks/0494 §5-6, §41, §62; ADR-0002, ADR-0004, ADR-0005, ADR-0006,
ADR-0011.
