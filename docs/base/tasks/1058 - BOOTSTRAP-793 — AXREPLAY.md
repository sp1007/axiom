# BOOTSTRAP-793 — AXREPLAY

**Native Axiom Deterministic Execution Replay, Record/Replay Engine, Event Capture, Scheduler Replay, Time/Randomness Virtualization, Input/IO Determinism, Memory/Thread/Task State Correlation, Crash Replay, Reverse Debugging Foundation, Replay Artifact `.axreplay`, Replay ABI & Deterministic Debugging Runtime 5.0**

**Status:** FROZEN — 5.0  
**Namespace:** `AXREPLAY`  
**ABI:** `AXREPLAY_ABI_1`  
**Artifact:** `.axreplay`  
**Schema:** `AXREPLAY_SCHEMA_1`

**Depends on:** `AXDEBUGGER`, `AXCRASH`, `AXPROFILER`, `AXCOMPILER`, `AXABI`, `AXBINARY`, `AXLOADER`, `AXPROCESS`, `AXRUNTIME`, `AXMEMORY`, `AXTASK`, `AXASYNC`, `AXTIME`, `AXRANDOM`, `AXINPUT`, `AXSTREAM`, `AXCODEC`, `AXTEST`

**Optional integrations:** `AXOBSERVABILITY`, `AXDIAGNOSTICS`, `AXIDE`, `AXCODEEDITOR`, `AXGUI`, `AXCRYPTO`, `AXTRUST`

---

# 1. Purpose

AXREPLAY provides deterministic recording and replay of Axiom program execution.

Its central goal is:

```text
execution
    ↓
record nondeterministic decisions
    ↓
replay same decisions
    ↓
reproduce equivalent execution
```

The primary use cases are:

- deterministic debugging;
- reproducing intermittent crashes;
- reverse debugging foundation;
- concurrency debugging;
- async/task debugging;
- regression reproduction;
- deterministic test failure reproduction;
- crash-to-replay workflows;
- diagnosing race-sensitive behavior;
- performance investigation with reproducible execution context.

---

# 2. Fundamental Principle

AXREPLAY does **not** record every CPU instruction by default.

Instead it records the minimum externally observable nondeterministic information necessary to reproduce execution under a defined replay contract.

```text
                    Program
                       │
             ┌─────────┴─────────┐
             │                   │
       Deterministic        Nondeterministic
          state                   events
             │                   │
             │              AXREPLAY Recorder
             │                   │
             └─────────┬─────────┘
                       ▼
                  .axreplay
                       │
                       ▼
                 Replay Engine
                       │
                       ▼
              Equivalent execution
```

This keeps recording substantially cheaper than instruction-by-instruction tracing.

---

# 3. Scope Boundary

```text
AXREPLAY = execution determinism
AXCRASH  = crash evidence
AXDEBUGGER = interactive inspection
AXPROFILER = performance measurement
AXTEST = verification
```

AXREPLAY may integrate all of them but does not replace them.

---

# 4. Non-Goals

AXREPLAY does not guarantee:

- identical wall-clock timing;
- identical physical CPU execution;
- identical cache behavior;
- identical hardware-counter values;
- identical OS scheduling outside the replay contract;
- reproduction of arbitrary external systems not captured by the recorder.

---

# 5. Determinism Contract

A replay session defines:

```text
ReplayContract {
    target
    architecture
    ABI
    executable_build_id
    runtime_build_id
    compiler_build_id?
    deterministic_features
    external_inputs
    platform_requirements
}
```

Replay validity is always relative to this contract.

---

# 6. Record/Replay Modes

```text
REPLAY_DISABLED
RECORD_MINIMAL
RECORD_STANDARD
RECORD_DEBUG
RECORD_FULL
REPLAY_ONLY
```

---

# 7. Minimal Recording

Captures only events required by explicitly deterministic subsystems.

Useful for:

```text regression tests
controlled services
deterministic workloads
```

---

# 8. Standard Recording

Adds:

```text task scheduling
thread scheduling
time
randomness
external input
selected IO
```

---

# 9. Debug Recording

Adds additional checkpoints and state metadata to support reverse debugging.

---

# 10. Full Recording

May capture substantially more state for difficult failures.

It remains opt-in because of storage and runtime overhead.

---

# 11. Replay Session

```text
ReplaySession {
    id
    generation
    mode
    state
    contract
    recorder?
    replay_source?
    checkpoints[]
    artifact?
}
```

States:

```text CREATED
RECORDING
FINALIZING
RECORDED
REPLAYING
PAUSED
FAILED
COMPLETED
```

---

# 12. Event Model

Canonical:

```text
ReplayEvent {
    sequence
    logical_time
    thread_id?
    task_id?
    kind
    payload
}
```

---

# 13. Event Sequence

Every nondeterministic event receives a monotonically increasing sequence number.

```text
1
2
3
...
N
```

---

# 14. Event Ordering

The event sequence is the canonical replay order.

Wall-clock timestamps are informational and cannot replace sequence ordering.

---

# 15. Event Classes

```text
SCHEDULER
TIME
RANDOM
INPUT
FILE_IO
NETWORK_IO
PROCESS
THREAD
TASK
ASYNC
SIGNAL
EXCEPTION
MEMORY
MODULE
SYNC
ATOMIC
SYSTEM_CALL
USER_EVENT
CHECKPOINT
```

---

# 16. Scheduler Determinism

The scheduler is one of the most important replay sources.

Record:

```text
which runnable execution context was selected
```

rather than attempting to reproduce the original physical CPU scheduler.

---

# 17. Logical Execution Context

Axiom distinguishes:

```text
OS thread
logical task
executor
```

AXREPLAY preserves these identities independently.

---

# 18. Thread Event

```text
ThreadEvent {
    thread_id
    action
    sequence
}
```

Actions:

```text CREATE
START
BLOCK
UNBLOCK
EXIT
```

---

# 19. Task Event

```text
TaskEvent {
    task_id
    executor_id?
    action
}
```

Actions:

```text CREATE
QUEUE
RUN
SUSPEND
RESUME
COMPLETE
CANCEL
```

---

# 20. Task Migration

A task may move between OS threads.

Replay records:

```text
task_id
executor
thread
sequence
```

so migration can be reproduced logically.

---

# 21. Executor Determinism

A replay-aware executor exposes:

```text
next_runnable_task()
```

and consumes the recorded selection.

---

# 22. Scheduler Divergence

If the replay runtime cannot reproduce the recorded scheduling decision:

```text
REPLAY_SCHEDULER_DIVERGENCE
```

is emitted.

Replay must not silently choose a different task and claim deterministic success.

---

# 23. Synchronization

Synchronization events include:

```text
mutex
rwlock
semaphore
condition
event
barrier
channel
atomic coordination
```

where needed by the determinism contract.

---

# 24. Lock Ordering

The recorder may record the successful synchronization decision:

```text lock_id
owner
waiter
sequence
```

rather than continuously tracing every lock operation.

---

# 25. Atomic Operations

Atomic memory operations are special.

AXREPLAY may record ordering decisions when the compiler/runtime determines that they affect externally observable nondeterminism.

---

# 26. Memory Ordering

The replay model must preserve the language-defined atomic memory semantics.

It must not weaken Axiom's memory model merely to simplify replay.

---

# 27. Race Detection Boundary

AXREPLAY does not become a race detector.

It records enough synchronization information to replay supported execution.

AXTEST/diagnostic tooling can analyze races separately.

---

# 28. Time Virtualization

Nondeterministic time is redirected through:

```text AXTIME
   ↓
AXREPLAY time provider
```

during recording/replay.

---

# 29. Time Event

```text
ReplayTimeEvent {
    clock
    value
}
```

---

# 30. Clock Classes

At minimum:

```text MONOTONIC
WALL
PROCESS
THREAD
```

---

# 31. Monotonic Clock

Replay returns the recorded value where deterministic replay requires exact temporal observation.

---

# 32. Wall Clock

Wall-clock time can be:

```text recorded
virtualized
excluded
```

according to policy.

---

# 33. Timer Events

Timer expiration order is recorded when multiple timers could fire nondeterministically.

---

# 34. Timer Replay

```text timer_id
scheduled_deadline
actual_delivery_sequence
```

can reproduce delivery ordering.

---

# 35. Randomness

AXRANDOM exposes a replay-aware provider.

```text random_request
    ↓
recorded bytes
    ↓
replay exact bytes
```

---

# 36. Random Event

```text RandomEvent {
    source
    stream_id
    request_size
    data_hash
    data?
}
```

---

# 37. Random Data Policy

Recording may store:

```text exact random bytes
```

or:

```text deterministic seed/state
```

depending on the generator.

For cryptographically secure randomness, recording exact output is generally required if exact replay is intended.

---

# 38. Security Boundary

AXREPLAY must clearly mark recorded randomness as potentially sensitive.

Replay artifacts must not be treated as cryptographic secrets merely because they contain random bytes.

---

# 39. Input Determinism

External application input may include:

```text keyboard
mouse
touch
pen
game/controller input
IPC messages
sensor input
host callbacks
```

---

# 40. Input Event

```text
InputEvent {
    source
    timestamp
    sequence
    payload
}
```

---

# 41. Input Capture

AXINPUT can provide replay hooks.

The recorder captures logical input events rather than raw device electrical state.

---

# 42. Input Replay

During replay:

```text external input
        X
        │
   replay provider
        │
        ▼
recorded logical input
```

---

# 43. GUI Determinism

AXGUI can integrate with AXREPLAY to reproduce:

```text input ordering
timer events
command events
application UI state transitions
```

but GPU rendering itself is not required to be pixel-identical.

---

# 44. File I/O

File reads are potentially nondeterministic because filesystem contents may change.

Replay can record:

```text path identity
operation
offset
length
returned bytes
error
```

subject to privacy policy.

---

# 45. File Write

Writes can be handled in two modes:

```text REAL_WRITE
REPLAYED_WRITE
```

---

# 46. Safe Replay

Default replay should avoid mutating the real external filesystem where practical.

A replay sandbox can redirect writes.

---

# 47. File Identity

Recorded file identity includes:

```text normalized path
file identity where available
size
mtime
content hash
```

---

# 48. File Read Verification

Replay may verify that the external file still matches the recorded identity.

---

# 49. File Divergence

If external input differs:

```text REPLAY_INPUT_DIVERGENCE
```

is raised.

---

# 50. Network I/O

Network input is fundamentally external nondeterminism.

Replay supports:

```text recorded-response mode
```

where response data is captured during recording.

---

# 51. Network Output

Outgoing network traffic is not automatically replayed onto the real network.

Default:

```text replay sandbox
```

or:

```text suppressed
```

---

# 52. Network Safety

Replay must not accidentally resend:

```text transactions
commands
messages
credentials
```

to production systems.

---

# 53. Process Creation

Child process creation is recorded:

```text executable identity
arguments policy
environment policy
creation result
exit state
```

---

# 54. Child Process Replay

Supported modes:

```text REAL_CHILD
RECORDED_CHILD
FORBIDDEN
```

Default deterministic replay should prefer recorded/sandboxed behavior.

---

# 55. Environment

Environment variables can affect execution.

The replay contract records only explicitly permitted variables.

---

# 56. Environment Snapshot

```text EnvironmentSnapshot {
    variable_hashes
    selected_values
}
```

---

# 57. Secret Filtering

Variables matching configured sensitive patterns must be excluded or redacted.

---

# 58. System Calls

AXREPLAY may use syscall interception only through platform-specific adapters.

It must not require intercepting every syscall.

---

# 59. System Call Policy

Each external operation is classified:

```text DETERMINISTIC
CAPTURE_REQUIRED
REPLAY_SAFE
REPLAY_FORBIDDEN
UNKNOWN
```

---

# 60. Unknown External Dependency

If an operation cannot be classified safely, replay must report:

```text REPLAY_UNSUPPORTED_EXTERNAL_DEPENDENCY
```

rather than silently pretending determinism.

---

# 61. Module Determinism

Loaded modules affect execution.

The replay contract records:

```text module_id
build_id
base identity
load sequence
```

---

# 62. Dynamic Loading

Replay validates dynamic module identity before continuing.

---

# 63. Module Mismatch

A different module build produces:

```text REPLAY_MODULE_MISMATCH
```

---

# 64. ASLR

Absolute addresses are not replay identity.

Replay may use different virtual addresses if all address-dependent behavior remains valid.

---

# 65. Pointer Values

Raw pointer values are not generally recorded as deterministic semantic values.

They are process-instance addresses.

---

# 66. Address-Sensitive Programs

Programs depending on exact pointer addresses are outside portable deterministic replay unless the replay contract explicitly fixes the address layout.

---

# 67. Memory Allocation

Allocator behavior can influence pointer identity and memory layout.

AXREPLAY does not automatically record every allocation.

---

# 68. Allocation Determinism

Axiom's allocator may expose deterministic replay hooks for:

```text allocation sequence
arena identity
object identity
```

where required.

---

# 69. Allocation IDs

Debug/replay mode may assign:

```text AllocationId
```

without embedding it into ordinary pointers.

---

# 70. Heap Checkpoints

Full replay mode may create bounded heap checkpoints.

This is optional because of potentially large storage cost.

---

# 71. Memory Checkpoint

```text MemoryCheckpoint {
    checkpoint_id
    regions[]
    hashes[]
}
```

---

# 72. Incremental Checkpoint

Only changed pages/regions should be stored after the initial checkpoint when supported.

---

# 73. Copy-on-Write Checkpoints

The replay engine may use OS copy-on-write facilities to reduce checkpoint overhead.

---

# 74. Checkpoint Frequency

Configurable:

```text NONE
LOW
MEDIUM
HIGH
ADAPTIVE
```

---

# 75. Adaptive Checkpointing

The debugger may request denser checkpoints near:

```text fault
breakpoint
interesting event
```

without recording the entire execution at maximum density.

---

# 76. Reverse Debugging

AXREPLAY provides the foundation for:

```text reverse_continue
reverse_step
reverse_next
reverse_task
```

---

# 77. Reverse Execution

Reverse execution is implemented as:

```text checkpoint
    ↓
restore state
    ↓
replay forward
    ↓
stop at requested event
```

not by magically executing machine instructions backward.

---

# 78. Reverse Step Granularity

Supported granularity:

```text event
source statement
function
task transition
checkpoint
```

depending on compiler/debug metadata.

---

# 79. Instruction Reverse Step

Optional and target-dependent.

It is not mandatory for AXREPLAY 5.0.

---

# 80. Replay Cursor

```text ReplayCursor {
    sequence
    timestamp
    checkpoint_id?
    thread_id?
    task_id?
}
```

---

# 81. Replay Seek

```text replay_seek(sequence)
```

restores the nearest valid checkpoint and replays forward.

---

# 82. Replay Speed

Replay supports:

```text normal
fast-forward
single-step
reverse-step
reverse-continue
```

---

# 83. Deterministic Breakpoints

AXDEBUGGER breakpoints can bind to replay sequence/source identities.

---

# 84. Replay Breakpoint

```text ReplayBreakpoint {
    location
    condition?
    sequence_range?
}
```

---

# 85. Conditional Breakpoints

Conditions are evaluated against replay state.

By default they must not modify program state.

---

# 86. Replay Expression Evaluation

AXDEBUGGER remains the owner of expression semantics.

AXREPLAY supplies historical execution state.

---

# 87. Replay Variable State

Variables may be reconstructed from:

```text checkpoint
debug metadata
replayed execution
```

---

# 88. Optimized Variables

As with AXCRASH:

```text AVAILABLE
OPTIMIZED_OUT
PARTIAL
UNAVAILABLE
```

remain explicit.

---

# 89. Replay Crash

A crash can produce:

```text .axcrash
+
.axreplay reference
```

if recording was enabled.

---

# 90. Crash-to-Replay Flow

```text Application
    ↓
AXREPLAY recording
    ↓
crash
    ↓
AXCRASH
    ↓
.axcrash
    +
.axreplay
    ↓
AXIDE
    ↓
replay crash
```

---

# 91. Crash Correlation

The crash artifact may contain:

```text replay_session_id
replay_sequence
```

---

# 92. Replay Artifact

Canonical:

```text .axreplay
```

contains:

```text Header
ReplayContract
BuildIdentity
EventStream
Checkpoints
ExternalInputs
ModuleRecords
TaskRecords
ThreadRecords
RandomRecords
TimeRecords
IORecords
Indexes
Integrity
```

---

# 93. Artifact Header

```text
ReplayHeader {
    magic
    schema_version
    target
    architecture
    flags
    session_id
}
```

---

# 94. Event Stream Storage

The event stream is chunked.

```text
Chunk 0
Chunk 1
Chunk 2
...
```

---

# 95. Chunk Index

Each chunk contains:

```text first_sequence
last_sequence
offset
compressed_size
uncompressed_size
checksum
```

---

# 96. Random Access

This allows replay to seek without scanning the entire artifact.

---

# 97. Streaming Recorder

Recording can write chunks incrementally.

---

# 98. Crash-Safe Recording

If the application crashes during recording, completed chunks remain recoverable.

---

# 99. Partial Replay Artifact

A partial recording is marked:

```text PARTIAL_RECORDING
```

and exposes its valid sequence range.

---

# 100. Recording Finalization

```text active chunks
    ↓
flush
    ↓
index
    ↓
checksum
    ↓
final marker
```

---

# 101. Compression

Event chunks may be compressed.

The recorder's hot path should use bounded buffering.

---

# 102. Recording Hot Path

The hot path must avoid:

```text global locks
unbounded allocation
string formatting
symbolization
network operations
```

---

# 103. Per-Thread Buffers

Recommended architecture:

```text Thread
  ↓
local event buffer
  ↓
collector
  ↓
ordered chunk writer
```

---

# 104. Event Backpressure

If recording buffers fill, policy determines:

```text BLOCK
DROP
ABORT_RECORDING
```

---

# 105. Determinism Rule

For events required to guarantee replay, dropping the event is not permitted.

The recorder must instead:

```text block
or terminate recording
```

---

# 106. Optional Events

Non-essential diagnostic events may be dropped and marked accordingly.

---

# 107. Dropped Event Metadata

```text DroppedEvents {
    first_sequence?
    count
    reason
}
```

---

# 108. Replay Quality

```text ReplayQuality {
    deterministic
    partial
    dropped_optional_events
    unsupported_features
    divergence?
}
```

---

# 109. Determinism Validation

Replay compares expected event:

```text expected kind
expected identity
expected payload/hash
```

against actual execution.

---

# 110. Divergence Event

```text ReplayDivergence {
    sequence
    expected
    actual
    thread_id?
    task_id?
}
```

---

# 111. Divergence Types

```text INPUT_DIVERGENCE
SCHEDULER_DIVERGENCE
TIME_DIVERGENCE
RANDOM_DIVERGENCE
MODULE_DIVERGENCE
IO_DIVERGENCE
SYNC_DIVERGENCE
STATE_DIVERGENCE
ABI_DIVERGENCE
UNKNOWN_DIVERGENCE
```

---

# 112. Divergence Policy

```text STOP
WARN
CONTINUE_NONDETERMINISTIC
```

Default for deterministic replay:

```text STOP
```

---

# 113. Silent Divergence Prohibited

AXREPLAY must never silently switch to uncontrolled execution and still label the session deterministic.

---

# 114. Replay State Hash

At checkpoints:

```text state_hash
```

may be recorded.

---

# 115. State Hash

Hash can cover selected deterministic state:

```text task state
runtime state
selected memory
logical clocks
```

rather than every physical byte.

---

# 116. State Mismatch

```text REPLAY_STATE_DIVERGENCE
```

is reported if expected and actual state hashes differ.

---

# 117. Hash Limitations

A state hash is evidence of divergence, not proof of semantic equivalence.

---

# 118. External Input Hash

Large external inputs may be stored separately with:

```text content_hash
```

and referenced from the replay artifact.

---

# 119. Input Blob Store

Optional:

```text .axreplay.data/
```

or equivalent container sections may store large input payloads.

---

# 120. Artifact Deduplication

Identical external blobs may be content-addressed.

---

# 121. Privacy

Replay artifacts can contain much more sensitive information than ordinary crash reports.

Default policy must therefore be conservative.

---

# 122. Memory Privacy

No arbitrary heap recording by default.

---

# 123. Input Privacy

Input recording must be explicitly enabled for sensitive input classes.

---

# 124. Network Privacy

Network payload recording is opt-in.

---

# 125. Encryption

Replay artifacts may be encrypted with:

```text AXCRYPTO
```

---

# 126. Artifact Authentication

Signed replay artifacts can use:

```text AXTRUST
```

---

# 127. Remote Replay Artifact

Remote collection must use the same authentication principles as AXCRASH.

---

# 128. Replay Storage Limits

```text max_artifact_size
max_event_count
max_checkpoint_bytes
max_input_bytes
max_queue_size
```

are mandatory policy controls.

---

# 129. Garbage Collection of Checkpoints

Old checkpoints can be removed only if no retained replay cursor depends on them.

---

# 130. Replay Snapshot Lifetime

A checkpoint is immutable once published.

---

# 131. Checkpoint Identity

```text CheckpointId
```

is stable within the replay artifact.

---

# 132. Replay Context

```text ReplayContext {
    process
    threads[]
    tasks[]
    cursor
    contract
    state
}
```

---

# 133. Replay Process

Replay may run:

```text same executable build
same target
sandboxed environment
```

rather than modifying the original crashed process.

---

# 134. Replay Sandbox

Sandbox can isolate:

```text filesystem
network
environment
process creation
IPC
```

---

# 135. Replay Security

A replay artifact must never automatically execute arbitrary payloads embedded within it.

---

# 136. Executable Identity

Replay launches only an explicitly trusted executable matching the contract.

---

# 137. Artifact Cannot Select Arbitrary Executable

The replay file cannot override executable identity silently.

---

# 138. Build Validation

Before replay:

```text executable build ID
runtime build ID
ABI
target
```

must be validated.

---

# 139. Build Mismatch

Default:

```text REPLAY_BUILD_MISMATCH
```

and replay stops.

---

# 140. Compatible Replay

A future compatibility policy may allow:

```text ABI-compatible patch build
```

but this must be explicitly declared.

---

# 141. Compiler Optimization

Replay can work with optimized builds, but available source-level state may be reduced.

---

# 142. Debug Metadata

Debug metadata improves:

```text checkpoints
source mapping
reverse stepping
variables
```

but is not required for basic event replay.

---

# 143. Compiler Replay Metadata

AXCOMPILER may emit:

```text ReplayPoint
ReplayStateMap
TaskStateMap
DeterminismBoundary
```

---

# 144. Replay Point

A replay point maps:

```text instruction/source location
        ↔
logical execution event
```

---

# 145. Replay State Map

Maps compiler-generated state to:

```text source variable
task state
continuation
scope
```

when debug replay is enabled.

---

# 146. Async Reverse Debugging

Compiler-generated async state machines can expose:

```text await point
continuation
logical frame
```

for reverse navigation.

---

# 147. Closure Replay

Closure identity is preserved through compiler debug metadata rather than runtime object addresses.

---

# 148. Generic Replay

Monomorphized generic functions retain their concrete semantic identity in debug/replay metadata.

---

# 149. Function Identity

Uses Axiom semantic:

```text FunctionId
SymbolId
```

rather than raw addresses.

---

# 150. Module Identity

Uses:

```text ModuleId
BuildId
```

---

# 151. Source Identity

Uses:

```text file identity
source revision
range
```

not only line number.

---

# 152. Replay Event Query

```text replay_event_at(sequence)
replay_events(range)
replay_find(kind)
```

---

# 153. Replay Cursor API

```text replay_cursor()
replay_seek()
replay_step_forward()
replay_step_backward()
replay_continue()
replay_reverse_continue()
```

---

# 154. Replay State API

```text replay_threads()
replay_tasks()
replay_stack()
replay_registers()
replay_variables()
replay_memory()
```

---

# 155. Replay Comparison API

```text replay_compare()
replay_expected_event()
replay_actual_event()
replay_divergence()
```

---

# 156. Recorder API

```text replay_record_start()
replay_record_stop()
replay_record_flush()
replay_record_checkpoint()
replay_record_event()
```

---

# 157. Provider API

```text replay_time_provider()
replay_random_provider()
replay_input_provider()
replay_io_provider()
replay_scheduler_provider()
```

---

# 158. Module API

```text replay_register_module()
replay_validate_module()
replay_module_identity()
```

---

# 159. Task API

```text replay_register_task()
replay_task_event()
replay_task_selection()
replay_task_state()
```

---

# 160. Artifact API

```text replay_open()
replay_close()
replay_validate()
replay_metadata()
replay_chunks()
replay_checkpoints()
replay_export()
```

---

# 161. Replay Store API

```text replay_store_open()
replay_store_add()
replay_store_find()
replay_store_prune()
replay_store_delete()
```

---

# 162. AXDEBUGGER Integration

AXDEBUGGER consumes:

```text ReplayContext
ReplayCursor
ReplayState
```

and provides the interactive debugging surface.

---

# 163. AXCRASH Integration

AXCRASH can reference:

```text replay session
sequence
checkpoint
```

when a crash occurs during recording.

---

# 164. AXPROFILER Integration

AXPROFILER can record profile segments associated with:

```text replay sequence
```

for correlation.

---

# 165. AXTEST Integration

AXTEST can run:

```text record test
    ↓
crash/failure
    ↓
replay test
```

to reproduce intermittent failures.

---

# 166. Deterministic Test Mode

AXTEST may automatically enable:

```text virtual time
deterministic random
controlled scheduler
```

through AXREPLAY.

---

# 167. Regression Artifact

A failing test can retain:

```text test input
.axreplay
.axcrash
```

as a reproducible regression bundle.

---

# 168. Reproducibility Bundle

Optional bundle:

```text .axrepro
```

may reference:

```text executable
debug artifacts
.axreplay
.axcrash
test input
environment contract
```

The `.axrepro` container itself belongs to a later packaging/reproducibility layer; AXREPLAY only defines the replay components.

---

# 169. Remote Replay

A replay artifact can be analyzed on another machine if:

```text target executable
debug metadata
replay artifact
```

are available.

---

# 170. Remote Target

AXDEBUGGER may use AXREPLAY as the execution backend for a remote replay session.

---

# 171. Replay Transport

Transport is outside the core replay model and may use existing secure Axiom communication infrastructure.

---

# 172. Replay UI

AXIDE should expose:

```text timeline
event cursor
record/replay state
divergence
checkpoint markers
reverse controls
```

---

# 173. Timeline

Conceptually:

```text ──●────●────●────●────●────●──
   CP1       CP2        CP3
       ↑
     cursor
```

---

# 174. Reverse Timeline

Dragging the cursor backward performs:

```text restore nearest checkpoint
        ↓
replay forward
        ↓
stop at selected point
```

---

# 175. Source Navigation

AXCODEEDITOR can navigate to the source location represented by the replay cursor.

---

# 176. Task Timeline

AXIDE can visualize:

```text Thread 1
Task A ─────┐      ┌──────
Task B      └──────┘
Thread 2
Task C ───────────────
```

using AXREPLAY events.

---

# 177. Divergence UI

The IDE should show:

```text expected
actual
sequence
thread
task
source location
```

without hiding the exact evidence.

---

# 178. Replay Diagnostics

AXDIAGNOSTICS can consume divergence records.

---

# 179. AI Replay Context

```text AIReplayContext {
    cursor
    current_event
    previous_event
    next_event
    thread
    task
    source
    stack
    divergence?
    checkpoint
}
```

---

# 180. AI Evidence Rule

AI analysis must distinguish:

```text RECORDED
REPLAYED
DERIVED
INFERRED
UNKNOWN
```

---

# 181. AI Must Not Fabricate

No invented:

```text events
thread scheduling
variable values
external inputs
causes
```

---

# 182. Replay Root Cause

AXREPLAY can identify:

```text first divergence
```

but first divergence is not automatically the root cause.

---

# 183. First Divergence Analysis

When replay differs, analyzer should inspect the earliest known divergence because later differences may be consequences.

---

# 184. Divergence Chain

```text D1
 ↓
D2
 ↓
D3
```

can be displayed.

---

# 185. State Checkpoints

Periodic state hashes help locate the earliest divergence region.

---

# 186. Replay Recovery

If replay encounters an unsupported optional event:

```text partial replay
```

may continue only under explicitly non-deterministic mode.

---

# 187. Strict Replay

```text STRICT
```

is the default for debugging.

Any required divergence stops execution.

---

# 188. Best-Effort Replay

```text BEST_EFFORT
```

is available for exploratory analysis and must visibly mark the session as non-deterministic.

---

# 189. Replay Modes

```text STRICT_REPLAY
BEST_EFFORT_REPLAY
ANALYSIS_ONLY
```

---

# 190. Analysis-Only

Allows inspection of the event stream without executing the program.

---

# 191. Replay Resource Limits

```text max_runtime
max_memory
max_events
max_checkpoints
max_external_data
```

must be enforced.

---

# 192. Replay Cancellation

All replay operations are cancellable.

---

# 193. Replay Thread Safety

Replay control commands are serialized through the replay session.

---

# 194. Concurrent UI

AXIDE may query immutable replay snapshots concurrently.

---

# 195. Mutable Replay State

Only the replay engine's control thread mutates the active execution state.

---

# 196. Snapshot Model

```text ReplaySnapshot {
    cursor
    threads
    tasks
    stack
    registers
    state_hash
}
```

---

# 197. Snapshot Immutability

Published snapshots are immutable.

---

# 198. Performance Goal

Recording should add as little overhead as possible.

The architecture prioritizes:

```text local buffering
binary event IDs
compact payloads
deferred serialization
```

---

# 199. No String Formatting in Hot Path

Event names and symbols are represented by IDs.

---

# 200. No Symbolization in Hot Path

Symbolization occurs during analysis.

---

# 201. Compact Event Encoding

Common events use compact integer IDs and fixed-size fields.

---

# 202. Variable Payloads

Large payloads use references to separate data blocks.

---

# 203. Event Deduplication

Repeated immutable metadata can be interned once per artifact.

---

# 204. Event Compression

Chunk-level compression is preferred over per-event compression.

---

# 205. CPU Overhead Profiles

Suggested target:

```text MINIMAL  <2%
STANDARD    <5%
DEBUG       <10%
FULL        configurable
```

These are engineering targets, not semantic guarantees.

---

# 206. Storage Targets

Storage should scale approximately with:

```text nondeterministic events
+
selected checkpoints
+
external inputs
```

rather than CPU instruction count.

---

# 207. Memory Overhead

Recorder memory must be bounded by configuration.

---

# 208. Long-Running Applications

Recording can use:

```text rolling mode
```

with bounded storage.

---

# 209. Rolling Recording

Keep only the most recent:

```text N seconds
N events
N bytes
```

---

# 210. Crash Ring Buffer

This enables:

```text recent execution history
      ↓
crash
      ↓
preserve last N events
```

without recording unlimited history.

---

# 211. Always-On Crash Replay

Optional minimal replay mode may maintain a small rolling buffer in production.

---

# 212. Production Overhead

This feature remains opt-in and is never mandatory for ordinary release binaries.

---

# 213. Replay Artifact Integrity

Every chunk has:

```text checksum
```

and the artifact has a final integrity record.

---

# 214. Artifact Authentication

Optional signatures are handled by AXTRUST/AXCRYPTO.

---

# 215. Artifact Parser Security

The reader must defend against:

```text malformed chunks
integer overflow
oversized decompression
invalid sequence ranges
recursive references
```

---

# 216. No Artifact Code Execution

Opening `.axreplay` must never execute embedded code.

---

# 217. External Blob Safety

Referenced input blobs are treated as untrusted data.

---

# 218. Path Safety

Recorded filesystem paths cannot cause automatic filesystem access merely by being displayed.

---

# 219. Network Safety

Replay never contacts recorded network endpoints automatically.

---

# 220. Replay Environment

The environment is explicitly configured.

No hidden dependency on the machine's current environment is permitted in strict mode.

---

# 221. Replay Compatibility Matrix

```text same executable/build      = supported
ABI-compatible build          = explicit policy
different compiler build      = normally reject
different target              = reject
different architecture        = reject
different runtime semantics   = reject
```

---

# 222. Determinism Version

The artifact contains:

```text ReplayDeterminismVersion
```

because determinism semantics may evolve independently from binary ABI.

---

# 223. Replay Schema

```text AXREPLAY_SCHEMA_1
```

defines artifact serialization.

---

# 224. Replay ABI

```text AXREPLAY_ABI_1
```

defines runtime/provider APIs.

---

# 225. Version Separation

Changing serialization does not necessarily require changing runtime ABI, and vice versa.

---

# 226. Forward Compatibility

Readers skip unknown optional event fields.

Unknown required determinism mechanisms produce an explicit compatibility error.

---

# 227. Platform Backend

```text ReplayBackend {
    capabilities()
    start_record()
    stop_record()
    start_replay()
    scheduler()
    time()
    random()
    io()
    input()
    process()
}
```

---

# 228. Platform Independence

The normalized replay engine remains platform-independent.

---

# 229. Windows

Windows backend handles relevant:

```text thread scheduling hooks
time providers
input providers
filesystem
process
native synchronization
```

through Axiom/platform adapters.

---

# 230. Linux

Linux backend supports equivalent facilities using Linux-native mechanisms.

---

# 231. macOS

macOS backend follows the same normalized model while respecting Mach-O/macOS restrictions.

---

# 232. Android

Android replay is primarily intended for:

```text deterministic application/test execution
```

with platform capabilities explicitly reported.

---

# 233. iOS

iOS replay operates within application and platform lifecycle restrictions.

---

# 234. WASM

WASM replay can provide especially strong determinism for:

```text virtual time
randomness
host input
imports
```

because host boundaries are explicit.

---

# 235. Host Import Replay

For WASM:

```text import call
    ↓
recorded result
```

can be replayed without invoking the original host.

---

# 236. Native FFI

External native calls are determinism boundaries.

Axiom can classify them:

```text PURE
DETERMINISTIC
CAPTURED
UNSUPPORTED
```

---

# 237. C ABI

Foreign functions marked deterministic can execute normally.

Others must be captured or forbidden under strict replay.

---

# 238. FFI Annotation

Compiler attributes may declare:

```text @replay(pure)
@replay(captured)
@replay(external)
```

The exact attribute syntax belongs to AXCOMPILER's attribute system.

---

# 239. Unsafe Code

Unsafe Axiom code can participate in replay, but unsupported external effects remain explicit.

---

# 240. Undefined Behavior

Axiom must avoid defining replay semantics around undefined behavior.

If an execution violates Axiom's language/runtime invariants, replay may preserve the observed event history but cannot guarantee semantic reproduction.

---

# 241. Hardware Nondeterminism

Examples:

```text CPU counters
physical timing
thermal behavior
cache state
```

are not generally replayed.

---

# 242. Hardware Randomness

Hardware random instructions must be routed through AXRANDOM if deterministic replay is required.

---

# 243. SIMD Determinism

Replay does not require recording every SIMD instruction.

Floating-point behavior must instead follow the target/compiler floating-point contract.

---

# 244. Floating-Point Environment

If execution observes mutable floating-point environment state, replay may record:

```text rounding mode
exception state
```

where supported.

---

# 245. Locale

Locale-dependent behavior must use explicit AXSTANDARD/AXTIME configuration or be captured as external state.

---

# 246. Time Zone

Replay contract can include:

```text timezone database identity
timezone configuration
```

where relevant.

---

# 247. Filesystem Metadata

Metadata such as:

```text file size
timestamp
directory ordering
```

may be nondeterministic.

Captured values are replayed when observable.

---

# 248. Directory Enumeration

Directory entry ordering is captured when application behavior depends on it.

---

# 249. Environment Ordering

Environment enumeration ordering is normalized or recorded.

---

# 250. Hash Randomization

Any language/runtime hash seed must be captured for strict replay.

---

# 251. Collection Ordering

Axiom collections must not silently depend on nondeterministic iteration order unless explicitly documented.

---

# 252. Concurrency Collections

Concurrent structures expose replay hooks only when needed to reproduce observable ordering.

---

# 253. Channel Ordering

Message delivery sequence can be recorded:

```text channel_id
message_id
receiver_task
sequence
```

---

# 254. Async Cancellation

Cancellation events are deterministic inputs:

```text task_id
cancel_source
sequence
```

---

# 255. Timeout Races

When a timeout races with another event, replay records the selected winner.

---

# 256. Scheduler Fairness

Fairness is not inferred from wall-clock timing.

Replay reproduces recorded logical scheduling choices.

---

# 257. Starvation

Replay can reproduce a recorded starvation pattern but does not itself diagnose whether starvation is a bug.

---

# 258. Deadlock

Replay can reproduce deadlock if relevant scheduling/synchronization events were recorded.

AXDEBUGGER/diagnostics can analyze the resulting state.

---

# 259. Crash + Deadlock

If a crash occurs while other threads are deadlocked, AXCRASH captures the available thread state and AXREPLAY preserves prior scheduling history where recording was enabled.

---

# 260. Replay + Profiler

Profiler events can be associated with replay sequence ranges, allowing:

```text performance before divergence
```

analysis.

---

# 261. Replay + Crash

AXIDE can provide:

```text "Replay from crash"
```

by loading the nearest valid checkpoint before the recorded crash.

---

# 262. Replay + Test

A failing randomized test can save its:

```text random stream
```

through AXREPLAY.

---

# 263. Reproducing Random Tests

The test can replay the exact random decisions without exposing the original generator seed as the only reproduction mechanism.

---

# 264. Replay Event Evidence

Each event records its provenance:

```text RECORDED
SYNTHESIZED
CHECKPOINT_DERIVED
```

---

# 265. Derived State

A reconstructed variable value is marked:

```text DERIVED
```

rather than `RECORDED`.

---

# 266. Exact Evidence

Recorded external bytes remain:

```text RECORDED
```

and can be verified by hash.

---

# 267. Replay Report

```text ReplayReport {
    session_id
    contract
    result
    cursor
    divergence?
    quality
    duration
    events_processed
}
```

---

# 268. Replay Result

```text SUCCESS
CRASH
DIVERGED
UNSUPPORTED
CANCELLED
RESOURCE_LIMIT
```

---

# 269. Replay Failure

A failed replay must preserve:

```text expected event
actual event
cursor
state
```

where possible.

---

# 270. Replay Failure Artifact

A failed replay may generate a smaller:

```text .axreplay-failure
```

reference or diagnostic report, while the original `.axreplay` remains canonical.

---

# 271. API — Session

```text
replay_session_create()
replay_session_destroy()
replay_session_state()
replay_session_contract()
```

---

# 272. API — Recording

```text
replay_record_start()
replay_record_stop()
replay_record_flush()
replay_record_checkpoint()
replay_record_event()
```

---

# 273. API — Replay

```text
replay_start()
replay_pause()
replay_resume()
replay_stop()
replay_seek()
replay_step_forward()
replay_step_backward()
replay_continue()
replay_reverse_continue()
```

---

# 274. API — Determinism

```text
replay_time()
replay_random()
replay_input()
replay_scheduler()
replay_io()
replay_sync()
```

---

# 275. API — Inspection

```text
replay_cursor()
replay_event_at()
replay_events()
replay_checkpoint()
replay_threads()
replay_tasks()
replay_stack()
replay_registers()
replay_variables()
replay_memory()
```

---

# 276. API — Divergence

```text
replay_diverged()
replay_divergence()
replay_expected()
replay_actual()
replay_state_hash()
```

---

# 277. API — Artifacts

```text
replay_open()
replay_close()
replay_validate()
replay_metadata()
replay_write()
replay_export()
```

---

# 278. API — Storage

```text
replay_store_open()
replay_store_add()
replay_store_find()
replay_store_prune()
replay_store_delete()
```

---

# 279. API — Integration

```text
replay_register_module()
replay_register_task()
replay_set_context()
replay_attach_crash()
replay_attach_profile()
```

---

# 280. Error Model

Canonical errors:

```text
REPLAY_INVALID_SESSION
REPLAY_ALREADY_ACTIVE
REPLAY_NOT_ACTIVE
REPLAY_ARTIFACT_CORRUPT
REPLAY_SCHEMA_UNSUPPORTED
REPLAY_ABI_MISMATCH
REPLAY_BUILD_MISMATCH
REPLAY_TARGET_MISMATCH
REPLAY_MODULE_MISMATCH
REPLAY_SCHEDULER_DIVERGENCE
REPLAY_INPUT_DIVERGENCE
REPLAY_TIME_DIVERGENCE
REPLAY_RANDOM_DIVERGENCE
REPLAY_IO_DIVERGENCE
REPLAY_SYNC_DIVERGENCE
REPLAY_STATE_DIVERGENCE
REPLAY_UNSUPPORTED_EXTERNAL_DEPENDENCY
REPLAY_RESOURCE_LIMIT
REPLAY_STORAGE_FULL
REPLAY_PERMISSION_DENIED
REPLAY_SANDBOX_FAILURE
REPLAY_CHECKPOINT_FAILURE
REPLAY_RECORDING_OVERFLOW
```

---

# 281. Replay Security Invariants

### REPLAY-INV-01
Every replay artifact has a unique session identity.

### REPLAY-INV-02
Every artifact identifies the exact target contract.

### REPLAY-INV-03
Every required nondeterministic event has an ordered sequence.

### REPLAY-INV-04
Required events cannot be silently dropped.

### REPLAY-INV-05
Optional dropped events are explicitly recorded.

### REPLAY-INV-06
Strict replay stops on required divergence.

### REPLAY-INV-07
Strict replay never silently falls back to nondeterministic execution.

### REPLAY-INV-08
Replay validates executable build identity.

### REPLAY-INV-09
Replay validates runtime compatibility.

### REPLAY-INV-10
Replay validates module identities.

### REPLAY-INV-11
Logical task identity remains distinct from OS thread identity.

### REPLAY-INV-12
Scheduler replay preserves recorded logical scheduling decisions.

### REPLAY-INV-13
Time virtualization preserves recorded values where required.

### REPLAY-INV-14
Randomness required for determinism is reproduced exactly.

### REPLAY-INV-15
External input required for determinism is reproduced exactly.

### REPLAY-INV-16
Network replay does not automatically contact recorded endpoints.

### REPLAY-INV-17
Filesystem replay does not automatically mutate the real filesystem.

### REPLAY-INV-18
Child-process replay is explicitly controlled.

### REPLAY-INV-19
Replay artifacts cannot execute embedded code.

### REPLAY-INV-20
Replay artifacts enforce resource limits.

### REPLAY-INV-21
Replay memory capture is not enabled implicitly without policy.

### REPLAY-INV-22
Replay checkpoints are immutable.

### REPLAY-INV-23
Replay cursor state is versioned.

### REPLAY-INV-24
Replay divergence identifies the earliest detected mismatch.

### REPLAY-INV-25
A divergence does not automatically imply root cause.

### REPLAY-INV-26
Unavailable variables remain explicitly unavailable.

### REPLAY-INV-27
Replay source mapping uses stable semantic identities.

### REPLAY-INV-28
Async/task state is correlated using compiler/runtime metadata.

### REPLAY-INV-29
Replay crash correlation references AXCRASH rather than duplicating crash semantics.

### REPLAY-INV-30
Replay profiling correlation references AXPROFILER rather than replacing it.

### REPLAY-INV-31
Replay does not become a general-purpose telemetry system.

### REPLAY-INV-32
Remote replay artifacts require explicit authorization.

### REPLAY-INV-33
Sensitive recorded data can be excluded or redacted.

### REPLAY-INV-34
Artifact integrity is validated before replay.

### REPLAY-INV-35
Cross-architecture replay is rejected unless an explicit compatible replay model exists.

### REPLAY-INV-36
Release binaries have no mandatory replay overhead when replay is disabled.

### REPLAY-INV-37
Recording resource usage is bounded.

### REPLAY-INV-38
AI-visible replay information preserves provenance.

### REPLAY-INV-39
AXTEST can deterministically verify record/replay behavior.

### REPLAY-INV-40
Every conforming implementation satisfies all mandatory replay invariants.

---

# 282. AXTEST Conformance

AXTEST must verify:

```text
time
random
scheduler
thread/task
async
input
filesystem
network sandbox
process creation
module identity
checkpoint
reverse execution
divergence
crash correlation
```

---

# 283. Deterministic Test

Canonical test:

```text
record execution
      ↓
save .axreplay
      ↓
fresh process
      ↓
replay
      ↓
compare event sequence
```

---

# 284. Scheduler Test

Run many tasks repeatedly and verify identical logical scheduling sequences.

---

# 285. Race-Sensitive Test

Use controlled synchronization races and verify the recorded winner is reproduced.

---

# 286. Timer Race Test

Create competing timers and verify delivery order.

---

# 287. Random Test

Record random output and verify exact replay.

---

# 288. IO Test

Modify an external file after recording and verify strict replay reports input divergence rather than using the modified content.

---

# 289. Network Test

Verify replay never sends captured requests to the real endpoint.

---

# 290. Checkpoint Test

Create multiple checkpoints and verify:

```text seek(CP1)
seek(CP2)
reverse step
forward step
```

produce expected states.

---

# 291. Crash Replay Test

Controlled test crash:

```text AXREPLAY
   ↓
AXCRASH
   ↓
.axcrash + .axreplay
   ↓
replay
   ↓
same crash location
```

where the platform and build permit deterministic reproduction.

---

# 292. Divergence Test

Intentionally modify one recorded input and verify the first divergence is identified.

---

# 293. Artifact Fuzz Test

Fuzz:

```text headers
chunks
event payloads
checkpoint indexes
external references
compression
```

---

# 294. Resource Test

Test:

```text enormous event count
huge checkpoint
tiny storage quota
large external input
```

and verify bounded failure.

---

# 295. Security Test

Verify:

```text malicious artifact
malicious path
malformed compression
invalid executable identity
unauthorized remote replay
```

cannot escape the replay boundary.

---

# 296. Performance Test

Measure:

```text disabled
minimal
standard
debug
full
```

recording overhead separately.

---

# 297. Deterministic Serialization Test

Identical logical replay streams must serialize canonically.

---

# 298. Cross-Platform Test

Replay artifacts must reject incompatible:

```text target
architecture
ABI
runtime
```

according to the contract.

---

# 299. Long-Run Test

Run recording for extended periods and verify:

```text bounded memory
bounded buffers
correct chunk rotation
correct rolling retention
```

---

# 300. Definition of Done

AXREPLAY 5.0 is complete when:

- `AXREPLAY_ABI_1` is frozen.
- `AXREPLAY_SCHEMA_1` is frozen.
- recording/replay session model is implemented.
- deterministic contract validation works.
- event sequencing works.
- scheduler replay works.
- task/thread distinction is preserved.
- async replay works.
- time virtualization works.
- randomness replay works.
- input replay works.
- filesystem capture/replay works.
- network replay sandbox works.
- process replay policy works.
- module identity validation works.
- synchronization replay works.
- bounded event buffers work.
- required-event backpressure works.
- chunked artifact writing works.
- crash-safe partial artifacts work.
- checkpoints work.
- incremental checkpoints work.
- replay seeking works.
- forward stepping works.
- reverse stepping works.
- reverse continue works.
- divergence detection works.
- state hashes work where enabled.
- optimized/debug metadata integration works.
- crash correlation with AXCRASH works.
- profiler correlation with AXPROFILER works.
- AXDEBUGGER integration works.
- AXIDE replay timeline works.
- AXCODEEDITOR source navigation works.
- AXTEST deterministic record/replay works.
- privacy controls work.
- artifact parser is fuzz-tested.
- replay sandbox is enforced.
- release binaries incur no mandatory replay cost when disabled.
- cross-platform capability detection works.
- all `REPLAY-INV-01..40` pass.
- self-hosted Axiom can record and replay a deterministic test.

**BOOTSTRAP-793 — AXREPLAY 5.0 is frozen.**

---

# Next task

## BOOTSTRAP-794 — AXDIFF

**Native Axiom Binary/Source/ABI/IR/Debug/Crash/Replay Difference Engine, Semantic Diff, API/ABI Compatibility Analysis, Executable/Object Comparison, Structural Binary Diff, Compiler Regression Diff, Crash/Replay Diff, Deterministic Comparison Artifacts & Difference Analysis ABI 5.0**