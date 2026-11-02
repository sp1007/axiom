# T211 Report — Plan phase P11: Concurrency & async

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P11 (`P11-concurrency-async`) từ 6 epic (`E11.1`–`E11.6`) trong `spec/ROADMAP.md` thành 32 task cụ thể (`T088`–`T090` được tinh chỉnh tại chỗ và 29 task mới `T400`–`T428`, từ 4 đến 6 task mỗi epic), chuyển toàn bộ 417 dòng `EPIC(E11.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T400`–`T428`), cập nhật `T311` phụ thuộc vào tất cả task P11, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P11 (`P11-concurrency-async`) across all six roadmap epics (`E11.1`–`E11.6`) into 32 concrete, single-sitting tasks (29 new tasks `T400`–`T428` in the `T400`–`T449` P11 block plus refined existing tasks `T088`, `T089`, `T090`), converted all 417 `EPIC(E11.*)` rows in `spec/requirements/CATALOG.md` to concrete `T4xx` task IDs with matching `covers:` lists, wired `T311` (`depends: [T211, T088, T089, T090, T400..T428]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E11.1 Concurrency semantics** (6 tasks: `T400`, `T089`, `T401`, `T402`, `T403`, `T404`):
   - `T400` (`axiom-architect`): Canonical `spec/SPEC-30-concurrency-semantics.md` (Send/Share auto-traits, spawn capture rules, data-race compile-error contract, happens-before memory model; 34 reqs).
   - `T089` (`axiom-semantics`): `Send` and `Share` auto-trait structural derivation, negative impls, and raw-pointer opt-in rules in `compiler/` (2 reqs).
   - `T401` (`axiom-semantics`): Closure capture classification (`Fn`/`FnMut`/`FnOnce`) and `thread.spawn` / `scope.spawn` `Send`/`Share` boundary enforcement (15 reqs).
   - `T402` (`axiom-semantics`): Compile-time data-race verifier (`AX_CONC_SHARED_MUT`, `AX_CONC_UNSYNC_STATIC`, `AX_CONC_LOCK_ORDER`, `AX_CONC_GUARD_ESCAPE`) (18 reqs).
   - `T403` (`axiom-semantics`): MIR optimizer synchronization barrier and lock/atomic reordering preservation (18 reqs).
   - `T404` (`axiom-qa`): Concurrency semantics & compile-time data-race conformance suite (27 reqs).
2. **E11.2 Atomics & memory ordering** (5 tasks: `T405`–`T409`):
   - `T405` (`axiom-architect`): Canonical `spec/SPEC-31-atomics-memory-ordering.md` (`Atomic<T>`, `Ordering`, fences, x86-64 mapping, oracle exploration; 13 reqs).
   - `T406` (`axiom-semantics`): `Atomic<T>` lang item, `Ordering` validation (`AX_ATOMIC_INVALID_ORDERING`), and MIR atomic statement/rvalue lowering (40 reqs).
   - `T407` (`axiom-backend`): LIR atomic operations (`LirInst.ATOMIC_*`, `FENCE`) and x86-64 `LOCK` / `XCHG` / `MFENCE` native emission (4 reqs).
   - `T408` (`axiom-semantics`): MIR interpreter (`--interp`) atomic memory model, release sequences, and deterministic schedule exploration (12 reqs).
   - `T409` (`axiom-qa`): Atomic litmus & memory ordering conformance suite (oracle + native stress; 7 reqs).
3. **E11.3 Threads & synchronisation library** (6 tasks: `T410`, `T090`, `T411`–`T414`):
   - `T410` (`axiom-architect`): Canonical `spec/SPEC-32-threads-sync-library.md` (threads, scoped threads, `Arc`, `Mutex`, `RwLock`, `Condvar`, `Once`, channels, `@thread_local`; 5 reqs).
   - `T090` (`axiom-stdlib`): `std.thread` (`spawn`, `JoinHandle`, `Builder`, `scope`, `park`/`unpark`, `sleep`, `yield_now`, `current`) on Windows x64 + oracle host intrinsics (1 req).
   - `T411` (`axiom-stdlib`): `std.sync` (`Arc<T>`, `Weak<T>`, `Mutex<T>`, `RwLock<T>`, `Condvar`, `Once`, `OnceLock<T>`, `Barrier`) on Windows SRWLock/CondVar/InitOnce + oracle (11 reqs).
   - `T412` (`axiom-stdlib`): `std.sync.channel` (`mpsc` unbounded, bounded array ring buffer, rendezvous `sync_channel(0)`, close/disconnect wakeups) (13 reqs).
   - `T413` (`axiom-backend`): `@thread_local` attribute, `.tls$` COFF section emission, and PE DataDirectory[9] (`IMAGE_TLS_DIRECTORY64`) linker support + oracle per-thread storage (2 reqs).
   - `T414` (`axiom-qa`): Threads, TLS & synchronization native stress and differential conformance suite (6 reqs).
4. **E11.4 Async/await** (6 tasks: `T415`–`T417`, `T088`, `T418`–`T419`):
   - `T415` (`axiom-architect`): Canonical `spec/SPEC-33-async-await-futures.md` (`Future`, `Poll`, `Context`, `Waker`, `Pin`, state-machine layout, cancellation drop, trace schema; 33 reqs).
   - `T416` (`axiom-frontend`): Lexer/parser/AST/HIR/typeck support for `async fn`, `async` blocks, `.await`, and `Future`/`Poll` lang items (14 reqs).
   - `T417` (`axiom-semantics`): Live-across-`.await` analysis (`AX_ASYNC_VIEW_ACROSS_AWAIT`, `AX_ASYNC_GUARD_ACROSS_AWAIT`, conditional `Send`/`Share` state-machine derivation) (30 reqs).
   - `T088` (`axiom-semantics`): `async fn` and `.await` MIR state-machine lowering (`MirTerminator.YIELD_AWAIT` dispatch switch, self-referential `Pin`, cancellation/resume drop flags) (2 reqs).
   - `T418` (`axiom-semantics`): MIR interpreter deterministic async trace engine (`--trace-async`) and poll/waker/cancellation lifecycle verifier (43 reqs).
   - `T419` (`axiom-qa`): Async/await state-machine, cancellation & Pin conformance suite (16 reqs).
5. **E11.5 Executors, fibers & structured concurrency** (5 tasks: `T420`–`T424`):
   - `T420` (`axiom-architect`): Canonical `spec/SPEC-34-executors-structured-concurrency.md` (single/multi-thread executors, async sync primitives, `TaskGroup`, cancellation, fibers; 17 reqs).
   - `T421` (`axiom-stdlib`): `std.async.executor` (`block_on`, `LocalExecutor`, work-stealing `ThreadPoolExecutor`) and `std.async.sync` (`Mutex`, `RwLock`, `Semaphore`, `Notify`, `channel`) (17 reqs).
   - `T422` (`axiom-stdlib`): Structured concurrency (`TaskGroup`, `scope`, `CancelToken`, `CancelScope`, `select`, `join`, `timeout`) (8 reqs).
   - `T423` (`axiom-stdlib`): Stackful fiber runtime (`std.fiber`, Windows x64 context switch + guard pages + oracle cooperative fiber scheduler, async-fiber bridge) (2 reqs).
   - `T424` (`axiom-qa`): Executor benchmarks, fiber & structured cancellation conformance suite (1 req).
6. **E11.6 Async IO integration** (4 tasks: `T425`–`T428`):
   - `T425` (`axiom-architect`): Canonical `spec/SPEC-35-async-io-reactor.md` (completion/readiness reactor abstraction, Windows IOCP, Linux epoll/io_uring contract, timers, async file/net traits; 2 reqs).
   - `T426` (`axiom-stdlib`): `std.io.reactor` Windows IOCP reactor, hierarchical timer wheel (`sleep`, `Instant`, `Interval`), and deterministic oracle virtual reactor/clock (4 reqs).
   - `T427` (`axiom-stdlib`): `AsyncRead`/`AsyncWrite`, `std.fs.async_file` (`OVERLAPPED` IOCP), and `std.net.async_net` (`TcpListener`, `TcpStream`, `UdpSocket`) (3 reqs).
   - `T428` (`axiom-qa`): Async file, timer & socket integration conformance suite (2 reqs).

## Files changed
- ./_workspaces/tasks/todo/T088-async-fn-await-state-machine-lowering-single-threa.md
- ./_workspaces/tasks/todo/T089-concurrency-semantics-send-share-data-race-rules-a.md
- ./_workspaces/tasks/todo/T090-std-thread-mutex-channel-atomic-t-on-windows.md
- ./_workspaces/tasks/todo/T211-plan-phase-p11-concurrency-async.md
- ./_workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- ./_workspaces/tasks/todo/T400-e11-1-concurrency-semantics-spec.md
- ./_workspaces/tasks/todo/T401-e11-1-closure-spawn-capture-verification.md
- ./_workspaces/tasks/todo/T402-e11-1-compile-time-data-race-verifier.md
- ./_workspaces/tasks/todo/T403-e11-1-mir-opt-synchronization-preservation.md
- ./_workspaces/tasks/todo/T404-e11-1-concurrency-race-conformance-suite.md
- ./_workspaces/tasks/todo/T405-e11-2-atomics-memory-ordering-spec.md
- ./_workspaces/tasks/todo/T406-e11-2-atomic-lang-item-ordering-mir-lowering.md
- ./_workspaces/tasks/todo/T407-e11-2-lir-atomic-ops-x64-codegen.md
- ./_workspaces/tasks/todo/T408-e11-2-oracle-atomic-memory-model-scheduler.md
- ./_workspaces/tasks/todo/T409-e11-2-atomic-litmus-conformance-suite.md
- ./_workspaces/tasks/todo/T410-e11-3-threads-tls-sync-library-spec.md
- ./_workspaces/tasks/todo/T411-e11-3-std-sync-arc-mutex-rwlock-condvar-once.md
- ./_workspaces/tasks/todo/T412-e11-3-std-sync-channel-bounded-unbounded.md
- ./_workspaces/tasks/todo/T413-e11-3-thread-local-storage-coff-pe-tls.md
- ./_workspaces/tasks/todo/T414-e11-3-threads-sync-native-stress-conformance.md
- ./_workspaces/tasks/todo/T415-e11-4-async-await-future-state-machine-spec.md
- ./_workspaces/tasks/todo/T416-e11-4-frontend-typeck-async-fn-await-future.md
- ./_workspaces/tasks/todo/T417-e11-4-live-across-await-view-guard-send-check.md
- ./_workspaces/tasks/todo/T418-e11-4-oracle-async-trace-lifecycle-verifier.md
- ./_workspaces/tasks/todo/T419-e11-4-async-await-conformance-suite.md
- ./_workspaces/tasks/todo/T420-e11-5-executors-structured-concurrency-fibers-spec.md
- ./_workspaces/tasks/todo/T421-e11-5-local-and-work-stealing-executors-async-sync.md
- ./_workspaces/tasks/todo/T422-e11-5-structured-concurrency-taskgroup-cancellation.md
- ./_workspaces/tasks/todo/T423-e11-5-stackful-fiber-runtime-context-switch.md
- ./_workspaces/tasks/todo/T424-e11-5-executor-benchmarks-structured-cancellation-conformance.md
- ./_workspaces/tasks/todo/T425-e11-6-unified-async-io-reactor-spec.md
- ./_workspaces/tasks/todo/T426-e11-6-windows-iocp-reactor-timer-wheel-oracle.md
- ./_workspaces/tasks/todo/T427-e11-6-async-read-write-file-tcp-udp-sockets.md
- ./_workspaces/tasks/todo/T428-e11-6-async-file-socket-conformance-suite.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on all `T400`–`T428`, `T088`–`T090`, and `T311` task files: `OK` (33 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (271 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 417 `EPIC(E11.*)` rows converted to concrete `T400`–`T428` tasks; `v1-full planned=458`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T211`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
