# Task Report — `T410`: Canonical Threads, TLS & Synchronization Library Specification (`SPEC-32`)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-32-threads-sync.md` (`AXS-SYNC-001`..`AXS-SYNC-051`) cho `E11.3` (OS threads, phạm vi có cấu trúc `scope`, cô lập `panic` & hủy hợp tác, lưu trữ cục bộ theo luồng `@thread_local` / `LocalKey<T>`, đếm tham chiếu `Rc<T>` / `Arc<T>` / `Weak<T>`, các nguyên thủy đồng bộ hóa `Mutex<T>`, `RwLock<T>`, `Condvar`, `Once`, `OnceCell<T>`, `Barrier`, và kênh truyền quyền sở hữu có giới hạn / không giới hạn `std.sync.channel`). Đồng thời cập nhật bảng hàm nội tại hệ thống trong `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-110`), mục lục đặc tả `spec/INDEX.md`, và bảng mã chẩn đoán `spec/diagnostics.md` (`AXD-021`, `§11`).

- **Task ID**: `T410` (`E11.3 — Canonical threads, TLS & synchronization library specification (SPEC-32)`)
- **Agent**: `axiom-architect`
- **Date**: `2026-11-03`

---

## 1. Architectural Summary & Rule Mapping

### 1.1 `spec/SPEC-32-threads-sync.md` (`AXS-SYNC-001`..`AXS-SYNC-051`)
1. **Section 1 — Architectural Foundations & Host Threading Intrinsics (`AXS-SYNC-001`..`AXS-SYNC-004`)**:
   - Defines the 4-layer separation (`REQ-CONC-003`, `REQ-CONC-198`):
     - Layer 1: Compiler language/type/lowering support (`Send`/`Share` auto-traits, `@thread_local`, `.tls$` section & `IMAGE_REL_AMD64_SECREL` relocation, PE TLS directory).
     - Layer 2: Host threading & futex intrinsic boundary (`std/core/host.ax` & `std/sys/windows/thread.ax`).
     - Layer 3: Safe standard library thread & synchronization modules (`std/thread/`, `std/sync/`).
     - Layer 4: Deterministic MIR interpreter oracle (`compiler/interp/interp.ax` & `oracle.ax`).
   - Specifies the 8 host threading/futex intrinsics (`thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, `futex_wake`), the `-5` `TimedOut` host error kind, the Windows x64 `kernel32.dll` + `api-ms-win-core-synch-l1-2-0.dll` (`WaitOnAddress` / `WakeByAddressSingle` / `WakeByAddressAll`) lowering, and the deterministic MIR interpreter thread/futex scheduler (`REQ-CONC-219`, `T090`).
2. **Section 2 — OS Threads, Structured Scopes, Panic Containment & Cancellation (`AXS-SYNC-010`..`AXS-SYNC-017`)**:
   - Specifies `std.thread` (`ThreadId`, `Thread`, `Builder`, `JoinHandle<T>`, `spawn`, `current`, `yield_now`, `sleep_ms`, `park`, `park_timeout_ms`, `Thread.unpark`, `available_parallelism`).
   - Enforces `F: FnOnce() -> T + Send + 'static` and `T: Send + 'static` for unscoped `spawn`, and structured `scope` (`Scope`, `ScopedJoinHandle<T>`) permitting non-`'static` `view<U>` (`U: Share`) and disjoint `mut_view<U>` (`U: Send`) borrows with mandatory join-before-return (`REQ-CONC-022`, `REQ-CONC-198`).
   - Specifies spawn/join `Happens-Before` edges, per-thread panic containment into `Result.Err(PanicPayload)` without poisoning locks or corrupting sibling threads (`REQ-CONC-080`), cooperative `CancelSource`/`CancelToken` cancellation, and explicit non-reentrancy contracts (`REQ-CONC-123`).
3. **Section 3 — Thread-Local Storage (`AXS-SYNC-020`..`AXS-SYNC-024`)**:
   - Specifies `@thread_local static` declarations (`'thread` lifetime, `!Share`, extracted value requires `T: Send`, `REQ-CONC-030`, `REQ-CONC-110`) and `std.thread.LocalKey<T>` (`with`, `with_mut`, `get`, `set`, LIFO per-thread destructor execution on thread exit, `T413`).
   - Specifies HIR/MIR/LIR lowering (`is_tls = true`, `AX_SEC_TLS = 4u32` `.tls$`, `AX_RELOC_X86_64_TLSREL = 6u32` mapped to `IMAGE_REL_AMD64_SECREL = 0x000Bu16`), Windows x64 `gs:[0x58]` (`TEB.ThreadLocalStoragePointer`) + `_tls_index` codegen, PE32+ 40-byte `IMAGE_TLS_DIRECTORY64` emission in `PE_DIR_TLS = 9`, and MIR interpreter per-thread `tls_slots` isolation.
4. **Section 4 — Reference Counting & Synchronization Primitives (`AXS-SYNC-030`..`AXS-SYNC-035`)**:
   - Specifies `Rc<T>` (`!Send`, `!Share`, `!Copy`, non-atomic reference count) and `Arc<T>` / `Weak<T>` (`Send + Share` iff `T: Send + Share`, `Relaxed` clone, `Release` decrement + `Acquire` fence before last-owner `Drop`, `REQ-CONC-070`, `REQ-CONC-071`, `T411`).
   - Specifies `Mutex<T>` (`Send + Share` iff `T: Send`, `REQ-CONC-105`, `REQ-CONC-106`) and `MutexGuard<T>` (`!Copy`, `!Send`, region-bound `get`/`get_mut` capabilities, `Release` unlock -> `Acquire` lock `Happens-Before` `REQ-CONC-180`, 3-state futex protocol, `REQ-CONC-010`, `REQ-CONC-015`, `REQ-CONC-044`, `REQ-CONC-045`, `REQ-CONC-047`).
   - Specifies `RwLock<T>` (`Send` iff `T: Send`, `Share` iff `T: Send + Share`), `RwLockReadGuard<T>`, `RwLockWriteGuard<T>` (`REQ-CONC-046`), `Condvar` (`wait`, `wait_timeout_ms`, `notify_one`, `notify_all`, predicate-loop rule), `Once` & `OnceCell<T>`, and `Barrier` (`BarrierWaitResult`, generation-safe reuse, all-to-all `Happens-Before`).
5. **Section 5 — Ownership-Transferring Channels (`AXS-SYNC-040`..`AXS-SYNC-044`)**:
   - Specifies `std.sync.channel` (`channel_bounded<T>(capacity)`, `channel_unbounded<T>()`, `Sender<T>`, `Receiver<T>`, `UnboundedSender<T>`, `UnboundedReceiver<T>`, `SendError<T>`, `TrySendError<T>`, `RecvError`, `TryRecvError`, `REQ-CONC-007`, `REQ-CONC-099`, `REQ-CONC-103`, `REQ-CONC-104`, `T412`).
   - Enforces move-by-value ownership transfer (`T: Send`, sender loses access on `send`, `REQ-CONC-011`, `REQ-CONC-041`, `REQ-CONC-042`, `REQ-CONC-143`, `REQ-CONC-186`), SPSC/MPSC/MPMC topologies with single-consumer delivery per message, drain-before-disconnect on `close()`, exact ownership accounting (`REQ-CONC-115`, `REQ-CONC-116`), and `Release`/`Acquire` `Happens-Before` (`REQ-CONC-043`, `REQ-CONC-185`).
6. **Section 6 & Section 7 — Diagnostics, Conformance Matrix & Traceability (`AXS-SYNC-050`..`AXS-SYNC-051`)**:
   - Defines the diagnostic table (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `AX_CONC_BORROW_ESCAPE_SPAWN`, `AX_CONC_GUARD_ESCAPE`, `AX_CONC_TLS_ESCAPE`, `AX_TYPE_INVALID_TLS_DECL`, `AX_CONC_UNSYNC_STATIC`), the 5-pillar conformance & multi-threaded stress verification matrix for `T414` (`REQ-CONC-036`..`039`, `REQ-CONC-081`, `REQ-CONC-187`), canonical Axiom positive/negative examples, and full traceability tables.

### 1.2 Lock-File Updates
- `spec/SPEC-04-core-extensibility.md`: Updated `AXS-EXT-110` (`§11`) with the `-5` `TimedOut` host error kind and the 8 `E11.3` thread/futex host intrinsics (`thread_spawn`, `thread_join`, `thread_detach`, `thread_current_id`, `thread_yield`, `thread_sleep_ns`, `futex_wait`, `futex_wake`, implemented in `thread.ax` / `T090`).
- `spec/INDEX.md`: Registered `spec/SPEC-32-threads-sync.md` in `§2`, `AXS-SYNC-NNN` in `§4`, and `SPEC-32 (T410)` + E11.3 corpus sources in `§5`.
- `spec/diagnostics.md`: Updated `AXD-021` (`§3`), appended `AX_CONC_TLS_ESCAPE` and `AX_TYPE_INVALID_TLS_DECL` (`T413`) in `§11`, and added `SPEC-32` to `## Sources`.

---

## 2. Verification Results

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `COVERAGE OK` (`gaps: 0`, `32308` requirements).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python tools/gatecheck.py --no-run`: `RESULT: PASS`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T410`: `0 REFUSED`, all modified files in `paths:` / `locks:`.

---

## Files changed

- `spec/SPEC-32-threads-sync.md`
- `spec/SPEC-04-core-extensibility.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`

## Status

STATUS: COMPLETE
