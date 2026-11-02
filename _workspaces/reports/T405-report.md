# T405 Report — E11.2 Canonical Atomics & Memory Ordering Specification (`SPEC-31`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-31-atomics.md` cho Epic `E11.2` (Atomics & Memory Ordering), hợp nhất các tài liệu nguồn `0092`, `0128`, `0161 §30`, `0162 §30`, `0208`, `tasks/0328` và `tasks/0515`, đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md` và `spec/invariants.md`. Đặc tả quy định đầy đủ ranh giới giữa bộ nhớ thường, bộ nhớ nguyên tử (`Atomic<T>`) và truy cập `volatile`, kiểu lang-item `Atomic<T>` (`bool`, số nguyên 8/16/32/64-bit, con trỏ thô), căn chỉnh tự nhiên bắt buộc, 5 mức thứ tự bộ nhớ (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`), ngữ nghĩa `fence`/`compiler_fence`/`spin_loop_hint`, hạ bậc MIR (`MIR_STMT_ATOMIC`) và bảo toàn qua bộ tối ưu hóa (`const_fold`, `dce`), hạ bậc LIR và mã máy x86-64 TSO (`LOCK XADD`, `LOCK CMPXCHG`, `XCHG`, `MFENCE`, `PAUSE`), mô hình bộ nhớ oracle dựa trên vector-clock và modification-order (`T408`), cùng 6 họ litmus test chuẩn (`T409`).

## 1. Deliverables Completed

1. **`spec/SPEC-31-atomics.md`** (`AXS-ATM-001`..`AXS-ATM-066`):
   - **§1 (`AXS-ATM-001`..`AXS-ATM-008`)**: Foundational separation between ordinary memory (governed by `view<T>` / `mut_view<T>`), atomic synchronization memory (`Atomic<T>` operated via `view<Atomic<T>>`), and hardware MMIO `volatile_read`/`volatile_write` (`volatile` is never atomic and establishes no happens-before edges). Forbids `mut_view<T>` into `Atomic<T>` inner storage (`AX_CONC_ATOMIC_MUT_VIEW`), non-atomic raw-pointer aliasing of active `Atomic<T>` locations (`AX_UNSAFE_INTERP_UB`), and tearing.
   - **§2 (`AXS-ATM-010`..`AXS-ATM-019`)**: `@lang("atomic") struct Atomic<T>` in `std/sync/atomic.ax`; exact allowed element types (`bool`, `i8`/`u8`, `i16`/`u16`, `i32`/`u32`, `i64`/`u64`, `isize`/`usize`, `*const U`/`*mut U`); mandatory natural alignment (`align_of::<Atomic<T>>() == size_of::<T>()`, rejecting `@packed` or sub-natural `@align(N)` with `AX_CONC_INVALID_ATOMIC_ALIGNMENT`); `Atomic<T>: Send + Share` and `!Copy`; `CasResult<T> { pub ok: bool, pub val: T }`; complete method signatures (`new`, `into_inner`, `load`, `store`, `swap`, `compare_exchange`, `compare_exchange_weak`, `fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`); `fence`, `compiler_fence`, `spin_loop_hint`; and standard aliases (`AtomicBool`, `AtomicI8`..`AtomicUsize`, `AtomicPtr<T>`).
   - **§3 (`AXS-ATM-020`..`AXS-ATM-028`)**: `@lang("ordering") enum Ordering` (`Relaxed = 0`, `Acquire = 1`, `Release = 2`, `AcqRel = 3`, `SeqCst = 4`) with mandatory explicit call-site specification; per-location modification order $\prec_{\text{mo}}^X$ and coherence (`CoRR`, `CoWR`, `CoWW`, `CoRW`); `Release`/`Acquire` `Synchronizes-With` ($\prec_{\text{sw}}$), `AcqRel` RMW barriers, release sequences across RMW chains, `SeqCst` total order $\prec_S$, compile-time `Ordering` legality matrix (`AX_CONC_INVALID_ATOMIC_ORDERING`), explicit `fence` synchronization rules (Fence-to-Atomic, Atomic-to-Fence, Fence-to-Fence), and `AtomicScope` extension point.
   - **§4 (`AXS-ATM-030`..`AXS-ATM-034`)**: Dedicated `MIR_STMT_ATOMIC` representation (`MIR_ATOMIC_LOAD`..`MIR_ATOMIC_SPIN_HINT`, `MIR_ORDER_RELAXED`..`MIR_ORDER_SEQ_CST`); canonical `inspect --emit=mir` / `--emit=mir-opt` text syntax; MIR verifier invariants (`compiler/verify/verifier.ax`); optimizer preservation rules (`const_fold.ax` and `dce.ax` never fold, coalesce, weaken, reorder across acquire/release boundaries, or dead-code-eliminate `MIR_STMT_ATOMIC`); and scheduling yield-point compatibility.
   - **§5 (`AXS-ATM-040`..`AXS-ATM-047`)**: Dedicated LIR atomic instructions (`LIR_INST_ATOMIC_LOAD`, `LIR_INST_ATOMIC_STORE`, `LIR_INST_ATOMIC_RMW`, `LIR_INST_ATOMIC_CAS`, `LIR_INST_FENCE`, `LIR_INST_PAUSE`) and `LirAtomicMeta`; x86-64 TSO memory model properties; complete instruction selection matrix (`MOV` for loads and `Relaxed`/`Release` stores, `XCHG` for `SeqCst` stores and `swap`, `LOCK XADD` for `fetch_add`/`fetch_sub`, `LOCK CMPXCHG` retry loop for `fetch_and`/`fetch_or`/`fetch_xor`, `LOCK CMPXCHG` + `SETE` for strong/weak CAS, `MFENCE` for `fence(SeqCst)`, 0-byte compiler barrier for `fence(Acquire|Release|AcqRel)` and `compiler_fence`, `PAUSE` for `spin_loop_hint`); and byte-exact x86-64 opcode/prefix encoding table (`F0` `LOCK`, `66`, `REX.W`, `0F C0`/`0F C1`, `0F B0`/`0F B1`, `86`/`87`, `0F AE F0`, `F3 90`).
   - **§6 (`AXS-ATM-050`..`AXS-ATM-054`)**: MIR interpreter oracle atomic location state and modification-order log $H(X)$; vector-clock release/acquire and release-sequence propagation; detection of unsynchronized ordinary/atomic data races (`AX_UNSAFE_INTERP_UB`, exit 125); deterministic multi-threaded schedule exploration; and deterministic spurious failure injection for `compare_exchange_weak`.
   - **§7 (`AXS-ATM-060`..`AXS-ATM-066`)**: Atomic diagnostic taxonomy (`AX_CONC_INVALID_ATOMIC_TYPE`, `AX_CONC_INVALID_ATOMIC_ORDERING`, `AX_CONC_INVALID_ATOMIC_ALIGNMENT`, `AX_CONC_ATOMIC_MUT_VIEW`), six normative litmus specifications (`LITMUS-MP`, `LITMUS-MP-FENCE`, `LITMUS-SB`, `LITMUS-LB`, `LITMUS-RMW`, `LITMUS-CAS-ABA`), and canonical positive/negative Axiom source examples.
   - **§8–§9**: Full traceability matrix covering all 13 primary `T405` `covers:` requirements and mapping all downstream `E11.2` tasks (`T406`, `T407`, `T408`, `T409`), plus corpus sources.

2. **`spec/INDEX.md`**:
   - Added `spec/SPEC-31-atomics.md` (`draft`, owner `T405`, consumers `T406, T407, T408, T409`) to §2 (`Canonical documents`).
   - Added `AXS-ATM-NNN` rule namespace to §4 (`Identifier namespaces`).
   - Added `SPEC-31 (T405)` and atomic corpus sources to §5 (`Topic → canonical source`).

3. **`spec/diagnostics.md`**:
   - Updated `AXD-021` to cite `E11.2` (`T405` / `SPEC-31 §7`) and `T406` atomic diagnostics under the `CONC` area.
   - Updated `AX_CONC_ATOMIC_MUT_VIEW` (`T402/T406`) and registered `AX_CONC_INVALID_ATOMIC_TYPE`, `AX_CONC_INVALID_ATOMIC_ORDERING`, and `AX_CONC_INVALID_ATOMIC_ALIGNMENT` (`T406`) in §11, and added `SPEC-31` to `## Sources`.

4. **`spec/invariants.md`**:
   - Updated §11 heading to `## 11. Concurrency and memory model (SPEC-30, SPEC-31)` and added `INV-CONC-005` (`since: T406`), `INV-CONC-006` (`since: T407`), and `INV-CONC-007` (`since: T408`) with exact `verify:` paths matching `T406`–`T409`.

## 2. Verification Results

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: passed (0 errors, 100% strict requirement coverage).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: passed (`OK: harness clean`).
- `python tools/gatecheck.py --no-run`: passed.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T405`: passed (all modified paths within `paths:` and `locks:`).
- Line endings: verified LF-only (`0` `\r` bytes) across all modified files.

## Files changed
- `spec/SPEC-31-atomics.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Status
STATUS: COMPLETE
