# T400 Report — E11.1 Canonical Concurrency Semantics & Memory Model Specification (`SPEC-30`)

## Tóm tắt

Hoàn thành đặc tả chính tắc `spec/SPEC-30-concurrency.md` cho mô hình đồng thời và bộ nhớ của ngôn ngữ Axiom (`E11.1`), đồng thời cập nhật các bảng chỉ mục và danh mục kiểm định tại `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md`. Đặc tả `SPEC-30` định nghĩa 41 quy tắc chuẩn (`AXS-CONC-001`..`AXS-CONC-052`) hợp nhất quyền sở hữu (`SPEC-10`), năng lực truy cập `view<T>` / `mut_view<T>` (`SPEC-11`), hai auto-trait đánh dấu độc lập `Send` và `Share`, quy tắc bắt giữ biến của closure tại ranh giới `spawn` / `spawn_local`, bộ kiểm chứng không tranh chấp dữ liệu ở thời điểm biên dịch (`compile-time data-race freedom`), mô hình thứ tự bộ nhớ `Happens-Before` cùng hợp đồng bảo toàn rào cản đồng bộ trong bộ tối ưu hóa MIR (`SPEC-70`), và hệ phân loại mã chẩn đoán `AX_CONC_*`. Toàn bộ 34 yêu cầu trong `covers:` của `T400` và toàn bộ giao diện cho các tác vụ anh em trong `E11.1` (`T089`, `T401`, `T402`, `T403`, `T404`) đã được truy vết đầy đủ.

## 1. Deliverables Summary

1. **`spec/SPEC-30-concurrency.md` (Canonical E11.1 Specification)**:
   - **§1. Unified Concurrency Architecture & Execution Contexts (`AXS-CONC-001`..`AXS-CONC-008`)**: Establishes the unified semantic formula ($\text{Ownership} \times \text{Capabilities} \times \text{Regions} \times \text{Synchronization} \times \text{Execution Domains}$) with no secondary concurrency pointer hierarchy (`REQ-CONC-019`, `REQ-CONC-095`); distinguishes `Thread`, lightweight `Task` (`REQ-RT-022`), `Fiber`, `Future<T>`, `GPUKernel`, and `InterruptContext` (`REQ-CONC-021`); enforces modular link-on-demand runtime independence (`REQ-CONC-145`); separates panic from cooperative cancellation (`REQ-CONC-082`); defines the static scope boundary for deadlocks and false sharing (`REQ-CONC-083`, `REQ-CONC-120`); and places synchronization contracts at the type/abstraction boundary (`REQ-CONC-050`).
   - **§2. `Send` and `Share` Marker Auto-Traits (`AXS-CONC-010`..`AXS-CONC-019`)**: Defines `Send` (cross-context ownership transfer) and `Share` (concurrent shared read access via `view<T>`) as strictly independent semantic properties (`Send != Share`, `REQ-CONC-025`..`027`, `REQ-CONC-073`, `REQ-CONC-131`, `REQ-CONC-136`..`138`, `REQ-CONC-156`); establishes capability bridge laws (`view<T>: Send <=> T: Share`, `mut_view<T>: Send <=> T: Send`, `mut_view<T>: !Share`); defines `@lang("send")` and `@lang("share")` auto-traits (`T089`, `REQ-CONC-218`..`219`); specifies the complete derivation matrix for primitives, `Str`, views, raw pointers (`!Send`, `!Share`), `Rc<T>`, `Arc<T>` (`REQ-CONC-028`), `Atomic<T>`, `Mutex<T>`, `RwLock<T>` (`REQ-CONC-101`, `REQ-CONC-102`), and standard collections (`REQ-CONC-141`); specifies negative `impl !Send`/`!Share`, `unsafe impl Send`/`Share` overrides with residual obligation checking (`REQ-CONC-126`..`128`), and zero-cost proof erasure (`REQ-CONC-144`).
   - **§3. Closure Capture & `spawn` / `spawn_local` Boundaries (`AXS-CONC-020`..`AXS-CONC-026`)**: Governs `T401` by specifying structural closure `Send`/`Share` derivation from execution-relevant captured fields (`REQ-CONC-005`, `REQ-CONC-006`, `REQ-CONC-125`), composition without class inheritance (`REQ-TYP-069`, `REQ-TYP-106`), mandatory `move` ownership transfer at `spawn` with no implicit copy/clone of `!Copy` values (`REQ-CONC-031`, `REQ-CONC-032`, `REQ-CONC-088`, `REQ-RES-044`), prohibition of escaping non-`'static` `view<T>`/`mut_view<T>` (`REQ-CONC-008`, `REQ-CONC-009`, `REQ-CONC-029`, `REQ-CONC-033`, `REQ-CONC-132`), `spawn` vs `spawn_local` obligations (`REQ-CONC-072`), structured `scope` vs `detach`, and `.await` suspension-point state-machine captures.
   - **§4. Compile-Time Data-Race Freedom & Capability Disjointness (`AXS-CONC-030`..`AXS-CONC-038`)**: Governs `T402` by defining formal data-race freedom on ordinary memory (`REQ-CONC-004`, `REQ-CONC-111`, `REQ-CONC-139`, `REQ-CONC-154`, `REQ-CONC-194`), the concurrent capability conflict matrix (`READ/READ` on `Share` allowed, unsynchronized `READ/WRITE` and `WRITE/WRITE` rejected; `REQ-CONC-067`, `REQ-CONC-068`, `REQ-CONC-140`, `REQ-CONC-195`, `REQ-CONC-196`), the 4-point place overlap lattice (`DISJOINT`, `CONTAINS`, `SAME`, `UNKNOWN`) where `UNKNOWN` is never treated as `DISJOINT` (`REQ-CONC-165`, `REQ-CONC-167`, `REQ-CONC-168`), disjoint struct-field and `split_at_mut` slice `mut_view` parallelism (`REQ-CONC-065`, `REQ-CONC-066`, `REQ-CONC-084`, `REQ-CONC-129`, `REQ-CONC-170`, `REQ-CONC-171`), mutable `static` and `@thread_local` isolation (`REQ-CONC-012`), lock guard lifetime and `!Send` invariants (`REQ-CONC-101`, `REQ-CONC-102`), `Atomic<T>` vs ordinary memory and `volatile != atomic` (`REQ-CONC-109`, `REQ-CONC-169`), custom `unsafe` synchronization contracts (`REQ-CONC-107`, `REQ-CONC-157`), and FFI thread-safety contracts (`REQ-CONC-117`).
   - **§5. Happens-Before Memory Model & Optimizer Preservation Contract (`AXS-CONC-040`..`AXS-CONC-047`)**: Governs `T403` by formalizing `Sequenced-Before`, `Synchronizes-With`, and transitive `Happens-Before` (`REQ-CONC-055`, `REQ-CONC-074`, `REQ-CONC-208`..`211`), atomic memory orderings (`Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`) and `fence`, notification vs publication (`REQ-CONC-090`), cross-domain/host-device/shared-memory boundaries (`REQ-CONC-112`..`114`), MIR/OptIR MemorySSA barrier preservation forbidding load/store hoisting/sinking/folding or speculative write introduction across synchronization edges (`REQ-CONC-122`, `REQ-CONC-124`, `REQ-CONC-215`), legal lock elision (`REQ-CONC-119`), and deterministic verification (`REQ-CONC-166`).
   - **§6–§9. Diagnostic Taxonomy (`AX_CONC_*`), Canonical Examples, Traceability Matrix & Sources (`AXS-CONC-050`..`AXS-CONC-052`)**: Defines 13 canonical `AX_CONC_*` diagnostic codes and structured payload keys (`place`, `region`, `domain`, `sync_state`, `reason`; `REQ-CONC-212`..`214`, `REQ-CONC-216`), canonical positive/negative Axiom examples (`=` and `.`), and full traceability tables.

2. **`spec/INDEX.md`**:
   - Registered `spec/SPEC-30-concurrency.md` in §2 (`The specification set`), `AXS-CONC-NNN` in §4 (`Identifier namespaces`), and the Concurrency & memory model row in §5 (`Topic → canonical source`).

3. **`spec/diagnostics.md`**:
   - Recorded the post-`T087` `CONC` area (`AX_CONC_*` in `compiler/diag/code.ax`) in §3 (`AXD-021`) while preserving the frozen 18-area `axiom0` `.def` table, and registered the 13 fixed `AX_CONC_*` diagnostic codes for `T089`, `T401`, `T402`, and `T403` in §11 (`Names already fixed for later tasks`).

4. **`spec/invariants.md`**:
   - Added the `CONC` group to §1 and defined `INV-CONC-001` (`since: T089`), `INV-CONC-002` (`since: T401`), `INV-CONC-003` (`since: T402`), and `INV-CONC-004` (`since: T403`, also referencing `T404` conformance).

## 2. Verification Results

- Line endings check: All modified `.md` files verified to use LF (`\n`) only with zero `\r` bytes.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `32308 requirements, 0 gaps, COVERAGE OK`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `MS-P1`..`MS-P10b PASS`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T400`: exits `0` with `0 REFUSED`.

## Files changed

- `spec/SPEC-30-concurrency.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## 3. Status

STATUS: COMPLETE
