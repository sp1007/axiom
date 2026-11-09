# T412: E11.3 — std.sync.channel: bounded & unbounded ownership-transferring channels

## Summary
Implemented `std.sync.channel` providing bounded and unbounded typed channels with move-only ownership transfer, backpressure, disconnection detection, and deterministic cleanup of unread messages per `spec/SPEC-32-threads-sync.md`. Channels operate across both native Windows x64 (using atomic state and futex WaitOnAddress/WakeByAddress) and the MIR interpreter concurrency oracle (`[interp]`).

All test suites pass cleanly across all execution modes (`[interp]`, `[native]`, `[native-O1]`) with 0 WEAK-NATIVE discrepancies.

## Implementation Details

1. **`std/sync/channel/mod.ax`**:
   - **Bounded Channel (`Sender<T>`, `Receiver<T>`)**:
     - `channel_bounded<T: Send>(capacity: usize) -> ChannelPair<T>` creates an MPMC/MPSC/SPSC bounded channel backed by a heap-allocated ring buffer `BoundedInner<T>`.
     - Ring buffer uses `ChannelSlot<T>` with heap storage, head/tail indices, and capacity tracking.
     - Thread synchronization via `Mutex<()>` and `Condvar`s (`not_empty`, `not_full`) for blocking and waking on enqueue/dequeue and state transitions.
     - Blocking `send(msg: T)` and non-blocking `try_send(msg: T) -> Result<(), TrySendError<T>>`.
     - Blocking `recv() -> Result<T, RecvError>` and non-blocking `try_recv() -> Result<T, TryRecvError>`.
     - Pointer helpers `send_from_ptr(p_src)` and `recv_into_ptr(p_dst)` for layout-safe zero-truncation transfer of large payloads (e.g., multi-field structs > 8 bytes).
     - Explicit `close()` method to close channel endpoints.
     - Arc-like ref-counting on `Sender` and `Receiver` endpoints (`sender_count`, `receiver_count`) tracking disconnection:
       - Dropping all `Sender`s wakes blocked `Receiver`s with `Disconnected` / `RecvError.Disconnected`.
       - Dropping all `Receiver`s causes `send` to fail with `SendError(T)` / `TrySendError.Disconnected(T)`.
       - Dropping the last endpoint triggers deterministic destruction (`drop_fn`) of all remaining queued items in the ring buffer.
   - **Unbounded Channel (`UnboundedSender<T>`, `UnboundedReceiver<T>`)**:
     - `channel_unbounded<T: Send>() -> UnboundedChannelPair<T>` creates an MPMC/MPSC/SPSC unbounded channel backed by a dynamically growing linked list in `UnboundedInner<T>`.
     - Linked list nodes `UnboundedNode<T>` allocate on enqueue and deallocate on dequeue.
     - Non-blocking `send(msg: T)` (unbounded growth, never blocks on full), `recv()`, `try_recv()`, and `close()`.
     - Pointer helpers `send_from_ptr` and `recv_into_ptr` matching the bounded channel interface.
     - Deterministic cleanup of all unread linked list nodes and messages on final endpoint drop.
   - **Custom Drop Glue Support**:
     - `channel_bounded_with_drop<T: Send>(capacity: usize, drop_fn: fn(*mut u8) -> ()) -> ChannelPair<T>`
     - `channel_unbounded_with_drop<T: Send>(drop_fn: fn(*mut u8) -> ()) -> UnboundedChannelPair<T>`
     - Enables types with custom destructors (`Tracked`, move-only wrappers) to have their destructors cleanly executed on channel teardown without requiring runtime monomorphization of generic drop glue.
   - **Send & Share Trait Implementations**:
     - `Sender<T>`: `Send + Clone` iff `T: Send`.
     - `Receiver<T>`: `Send + Clone` iff `T: Send` (supporting MPMC).
     - `UnboundedSender<T>`: `Send + Clone` iff `T: Send`.
     - `UnboundedReceiver<T>`: `Send + Clone` iff `T: Send`.

2. **`std/sync/mod.ax`**:
   - Re-exports channel primitives and types:
     `channel_bounded`, `channel_bounded_with_drop`, `channel_unbounded`, `channel_unbounded_with_drop`,
     `Sender`, `Receiver`, `UnboundedSender`, `UnboundedReceiver`,
     `ChannelPair`, `UnboundedChannelPair`,
     `SendError`, `RecvError`, `TrySendError`, `TryRecvError`.

3. **`tests/std/channel/`**:
   - `channel_bounded_basic.ax`: Tests single-thread FIFO ordering, bounded capacity limits, `try_send` when full, `try_recv` when empty, and disconnection after sender/receiver drop.
   - `channel_unbounded_basic.ax`: Tests unbounded growth (100 items), FIFO ordering, `try_recv` empty state, and disconnection.
   - `channel_spsc_threads.ax`: SPSC multi-threaded transfer of 20 items with bounded capacity 4, validating backpressure and thread synchronization.
   - `channel_mpsc_threads.ax`: MPSC multi-threaded transfer with 3 concurrent producer threads sending into a single receiver channel.
   - `channel_mpmc_threads.ax`: MPMC multi-threaded transfer with 2 producers and 2 consumers using cloned senders and receivers.
   - `channel_move_only_drop.ax`: Validates move-only ownership transfer and deterministic drop of unread queued items upon receiver drop across both bounded and unbounded channels.
   - `channel_big_struct.ax`: Multi-thread transfer of 32-byte struct `BigItem { a: i64, b: i64, c: i64, d: i64 }` (> 24 bytes) via `send_from_ptr` and `recv_into_ptr`, verifying no field truncation.
   - `ui_channel_send_bounds.ax`: Compile-fail UI test verifying that attempting to use `Sender<T>` or `Receiver<T>` with non-Send type (`Rc<i32>`) fails trait bound check.
   - `check_channel_bundles.test`: Validates byte-for-byte freshness of test bundles against live std source files.
   - `compile_live_channel.test`: Invokes `axiomc2 check` directly on `std/sync/channel/mod.ax`.
   - `gen_tests.py`: Python generator reproducing test bundles directly from live `std/` modules.

## Verification
- **All `std/channel/` Tests**:
  - `tests/std/channel/channel_bounded_basic.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_unbounded_basic.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_spsc_threads.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_mpsc_threads.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_mpmc_threads.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_move_only_drop.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/channel_big_struct.ax`: PASS 3/3 (`[interp]`, `[native]`, `[native-O1]`), 0 WEAK-NATIVE
  - `tests/std/channel/check_channel_bundles.test`: PASS 1/1
  - `tests/std/channel/compile_live_channel.test`: PASS 1/1
  - `tests/std/channel/ui_channel_send_bounds.ax`: PASS 1/1
  - Total `std/channel/`: 24 PASS, 0 FAIL, 0 WEAK-NATIVE.
- **Regression Suites**:
  - `tests/std/thread/`: 18 PASS, 0 FAIL, 0 WEAK-NATIVE.
  - `tests/run/atomics/`: 9 PASS, 0 FAIL, 0 WEAK-NATIVE.
  - `tests/run/concurrency/`: 37 PASS, 0 FAIL, 0 WEAK-NATIVE.
- **Sanity & Harness Checks**:
  - `tools/archcheck.py`: 218 files scanned, 0 violations.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: COVERAGE OK (0 gaps).
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: HARNESS OK.
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T412`: 0 REFUSED lines.

## Files changed
- std/sync/channel/mod.ax
- std/sync/mod.ax
- tests/std/channel/channel_big_struct.ax
- tests/std/channel/channel_bounded_basic.ax
- tests/std/channel/channel_move_only_drop.ax
- tests/std/channel/channel_mpmc_threads.ax
- tests/std/channel/channel_mpsc_threads.ax
- tests/std/channel/channel_spsc_threads.ax
- tests/std/channel/channel_unbounded_basic.ax
- tests/std/channel/check_channel_bundles.test
- tests/std/channel/compile_live_channel.test
- tests/std/channel/gen_tests.py
- tests/std/channel/ui_channel_send_bounds.ax

STATUS: COMPLETE round=0
