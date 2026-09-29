# BOOTSTRAP-790 — AXDEBUGGER

**Native Axiom Debugger Engine, Process/Thread Inspection, Breakpoints, Watchpoints, Stack Unwinding, Register State, Memory Inspection, Source Mapping, Variable Inspection, Expression Evaluation, Exception/Panic/Trap Handling, Debug Sessions, Remote Debugging & Debug ABI 5.0**

**Status:** FROZEN — 5.0  
**Namespace:** `AXDEBUGGER`  
**ABI:** `AXDEBUGGER_ABI_1`  
**Depends on:** `AXPROCESS`, `AXLOADER`, `AXSTARTUP`, `AXRUNTIME`, `AXTASK`, `AXASYNC`, `AXCOMPILER`, `AXABI`, `AXBINARY`, `AXDOC`, `AXIDE`, `AXCODEEDITOR`, `AXTEST`  
**Optional integrations:** `AXCRASH`, `AXDIAGNOSTICS`, `AXOBSERVABILITY`, `AXPROFILER`  

---

## 1. Purpose

AXDEBUGGER is the native debugging subsystem of Axiom.

It provides:

```text
Source
  ↓
AXCOMPILER debug metadata
  ↓
AXDEBUGGER
  ├── process control
  ├── thread/task inspection
  ├── breakpoint control
  ├── register inspection
  ├── memory inspection
  ├── stack unwinding
  ├── source mapping
  ├── variable decoding
  ├── expression evaluation
  ├── panic/trap handling
  └── crash/postmortem debugging
```

The debugger must expose **exact compiler/runtime information whenever available**, rather than reconstructing semantic information heuristically.

---

# 2. Architectural Boundary

```text
                         ┌───────────────┐
                         │    AXIDE      │
                         └───────┬───────┘
                                 │
                         Debug Protocol
                                 │
                         ┌───────▼───────┐
                         │  AXDEBUGGER   │
                         └───────┬───────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   Debug Metadata          Target Control          Runtime State
        │                        │                        │
   AXCOMPILER                 AXPROCESS               AXRUNTIME
   AXABI                      AXLOADER                AXTASK
   AXDOC                      OS backend              AXASYNC
        │
        ▼
  Source / Type / ABI
      semantics
```

AXDEBUGGER owns:

- debugging sessions;
- target control;
- stop/run state;
- breakpoints;
- watchpoints;
- registers;
- memory;
- stack;
- frames;
- source mapping;
- variables;
- expression evaluation;
- panic/trap handling;
- debug events;
- debug transport;
- debug artifact loading.

It does **not** own:

- compilation;
- optimization;
- source editing;
- GUI rendering;
- process creation primitives;
- executable loading;
- general profiling;
- general crash reporting;
- system-wide observability.

---

# 3. Non-Goals

AXDEBUGGER is not:

```text
AXCOMPILER     → compiler
AXIDE          → development orchestration
AXCODEEDITOR   → editor presentation
AXPROCESS      → process abstraction
AXLOADER       → executable loading
AXRUNTIME      → application runtime
AXPROFILER     → profiling
AXCRASH        → crash reporting
AXOBSERVABILITY→ production telemetry
```

Debugger-specific functionality must not leak into release runtime unless explicitly requested.

---

# 4. Fundamental Design Principle

The debugger operates on four layers:

```text
L0 Hardware / OS
       ↓
L1 Debug Backend
       ↓
L2 Axiom Debug Model
       ↓
L3 IDE / UI
```

Only L2 is platform-independent.

Therefore:

```text
Windows backend
Linux backend
macOS backend
Android backend
iOS backend
WASM backend
Remote backend
```

all translate into one canonical AXDEBUGGER model.

---

# 5. Debug Session

Canonical object:

```text
DebugSession {
    id
    generation
    target
    state
    process
    modules[]
    threads[]
    breakpoints[]
    watchpoints[]
    capabilities
    symbols
    source_maps
    transport
    diagnostics
}
```

Session states:

```text
CREATED
STARTING
RUNNING
STOPPED
STEPPING
DETACHED
TERMINATED
CRASHED
POSTMORTEM
ERROR
```

A session has a monotonically increasing:

```text
generation: u64
```

Any asynchronous operation carrying an obsolete generation is rejected.

---

# 6. Target Model

```text
DebugTarget {
    target_triple
    architecture
    platform
    abi
    executable
    arguments[]
    environment[]
    working_directory
    launch_mode
    symbol_policy
    source_mapping
    capabilities
}
```

Target identity includes:

```text
architecture
platform
ABI
binary build ID
debug-info identity
```

---

# 7. Process Model

```text
DebugProcess {
    id
    pid
    executable
    state
    architecture
    modules[]
    threads[]
    memory_regions[]
    capabilities
}
```

AXDEBUGGER must never assume:

```text
one debugger session = one OS process
```

A session may contain:

```text
parent
 ├── child process
 ├── worker process
 └── helper process
```

---

# 8. Thread Model

Axiom distinguishes:

```text
OS Thread
Logical Axiom Task
Async continuation
Coroutine
```

These are not interchangeable.

```text
DebugThread {
    id
    os_thread_id?
    task_id?
    state
    name?
    registers
    current_frame
}
```

A task may migrate between OS threads.

Therefore the debugger must represent:

```text
Task → currently executing on → OS Thread
```

rather than permanently identifying a task with one OS thread.

---

# 9. Attach / Launch / Detach

Canonical operations:

```text
debug_launch()
debug_attach()
debug_detach()
debug_terminate()
debug_kill()
```

Launch flow:

```text
configuration
    ↓
validate
    ↓
create process
    ↓
attach debugger
    ↓
load modules
    ↓
load symbols
    ↓
install pending breakpoints
    ↓
stop at entry / requested breakpoint
```

Attach must preserve the existing process state as far as the OS permits.

Detach must remove debugger-owned modifications.

---

# 10. Platform Backend

Canonical interface:

```text
DebugBackend {
    attach()
    launch()
    detach()

    continue()
    pause()
    terminate()

    read_registers()
    write_registers()

    read_memory()
    write_memory()

    set_breakpoint()
    remove_breakpoint()

    set_watchpoint()
    remove_watchpoint()

    enumerate_threads()
    enumerate_modules()

    wait_event()
}
```

Backends advertise capabilities rather than pretending all operations are universally available.

---

# 11. Capability Model

```text
DebugCapabilities {
    software_breakpoint
    hardware_breakpoint
    watchpoint
    conditional_breakpoint
    register_write
    memory_write
    thread_control
    reverse_execution
    async_debug
    exception_breakpoint
    core_dump
    remote_debug
}
```

Unavailable features return:

```text
DEBUG_UNSUPPORTED
```

rather than silently degrading to incorrect behavior.

---

# 12. Windows PE64

Windows backend supports:

```text
PE64
x86_64
AArch64 where supported by platform backend
```

The backend integrates with native Windows debugging facilities.

Responsibilities include:

- process attach;
- thread events;
- module load/unload;
- exception events;
- software breakpoints;
- hardware breakpoints;
- register state;
- memory access;
- stack unwinding;
- PE/CodeView symbols;
- PDB integration;
- TLS/module information.

AXDEBUGGER must not make the Windows debugging API part of the portable debugger ABI.

---

# 13. Linux ELF64

Linux backend supports:

```text
x86_64
AArch64
```

Capabilities include:

- process control;
- thread control;
- memory access;
- registers;
- hardware debug registers;
- signals;
- ELF module discovery;
- DWARF;
- unwind metadata;
- core dumps.

Platform-specific mechanisms remain behind:

```text
LinuxDebugBackend
```

---

# 14. macOS Mach-O

Supports:

```text
x86_64
AArch64
```

The backend understands:

- Mach-O modules;
- symbol UUID/build identity;
- DWARF/dSYM relationships;
- thread state;
- memory regions;
- exceptions;
- shared libraries;
- native debugging restrictions.

---

# 15. iOS

iOS debugging is capability-restricted.

AXDEBUGGER must support:

```text
local development debugging
attached development process
device/simulator distinctions
symbol loading
source mapping
thread/frame inspection
```

It must not assume arbitrary process attachment is possible on production devices.

---

# 16. Android

Android backend supports:

```text
AArch64 ELF64
```

and development debugging through the platform-supported transport.

It handles:

- native process;
- native threads;
- shared libraries;
- ELF/DWARF;
- signals;
- memory;
- registers;
- source mapping.

Java/Kotlin debugging is outside AXDEBUGGER's native semantic ownership, but a bridge may expose foreign frames.

---

# 17. WASM

WASM is not treated as a normal OS process.

```text
WasmInstance
 ├── memories
 ├── tables
 ├── globals
 ├── functions
 └── execution state
```

AXDEBUGGER provides:

- source mapping;
- function breakpoints;
- memory inspection;
- locals;
- stack;
- traps;
- module inspection.

Host-specific debugging is outside the WASM backend.

---

# 18. Remote Debugging

Architecture:

```text
AXIDE
  ↓
AXDEBUGGER client
  ↓
authenticated transport
  ↓
AXDEBUGGER server
  ↓
platform backend
  ↓
target
```

Remote protocol must be:

- versioned;
- authenticated;
- capability-negotiated;
- request-correlated;
- cancellable;
- resource-bounded.

No remote debugger server is enabled by default.

---

# 19. Process Lifecycle Events

Canonical events:

```text
ProcessCreated
ProcessStarted
ProcessExited
ProcessCrashed
ProcessDetached
ProcessTerminated
```

Module events:

```text
ModuleLoaded
ModuleUnloaded
```

Thread events:

```text
ThreadCreated
ThreadExited
ThreadNamed
ThreadStateChanged
```

---

# 20. Execution Control

Canonical states:

```text
RUNNING
STOPPED
STEPPING
PAUSED
TERMINATED
```

Canonical commands:

```text
continue
pause
step_into
step_over
step_out
step_instruction
run_to_cursor
restart
terminate
```

---

# 21. Stop Semantics

Every stop must have a reason.

```text
StopReason {
    kind
    thread
    address?
    breakpoint_id?
    signal?
    exception?
    trap?
    watchpoint?
    step?
}
```

Kinds:

```text
BREAKPOINT
WATCHPOINT
STEP
PAUSE
SIGNAL
EXCEPTION
PANIC
TRAP
FAULT
ENTRY
MODULE_EVENT
TASK_EVENT
USER_INTERRUPT
```

The debugger must never infer:

```text
"probably breakpoint"
```

when the backend supplied a precise reason.

---

# 22. Continue Semantics

`continue` resumes the target from the current stop point.

If stopped because of a software breakpoint, the debugger performs the required platform-specific breakpoint-step-over procedure before continuing.

This must be invisible to the user but explicit in the backend state machine.

---

# 23. Software Breakpoints

Software breakpoint:

```text
SoftwareBreakpoint {
    id
    address
    original_bytes
    trap_encoding
    module
    verified
}
```

The original instruction bytes must be retained.

Never restore bytes belonging to a newer image or changed module.

---

# 24. Breakpoint Identity

Stable identity:

```text
BreakpointIdentity {
    symbol_id?
    source_file_id?
    source_range?
    module_identity?
    logical_key
}
```

Address alone is not a stable identity.

Recompilation can change addresses while preserving:

```text
SymbolId
source location
module identity
```

---

# 25. Hardware Breakpoints

Hardware breakpoints are architecture-specific.

They must expose:

```text
slot_count
instruction_slots
data_slots
supported_sizes
supported_access_modes
```

If slots are exhausted:

```text
DEBUG_HARDWARE_SLOTS_EXHAUSTED
```

must be returned.

No automatic silent conversion to software breakpoints when semantics differ.

---

# 26. Conditional Breakpoints

```text
ConditionalBreakpoint {
    breakpoint
    condition
    evaluation_policy
}
```

Default evaluation:

```text
READ_ONLY
NO_SIDE_EFFECT
```

Condition failures must not modify application state.

---

# 27. Hit-Count Breakpoints

```text
HitPolicy {
    break_on_count
    break_every
    break_after
}
```

Counters belong to debugger session state unless explicitly persisted.

---

# 28. Logpoints

A logpoint executes debugger-side formatting based on captured state.

It must not silently inject application code.

```text
Logpoint {
    breakpoint
    template
    expressions[]
}
```

Expressions follow the same side-effect policy as watch expressions.

---

# 29. Watchpoints

```text
Watchpoint {
    id
    address
    size
    access
    hardware
    condition?
}
```

Access:

```text
READ
WRITE
READ_WRITE
```

Watchpoints are inherently limited by hardware.

The debugger must report:

```text
EXACT
PARTIAL
UNSUPPORTED
```

semantics.

---

# 30. Exception / Panic / Trap Breakpoints

Debugger configuration:

```text
break_on_exception
break_on_panic
break_on_trap
break_on_signal
break_on_fault
```

Axiom panic/trap metadata should identify:

```text
panic code
source location
message reference
originating function
stack
```

without requiring the production runtime to contain a large debugger.

---

# 31. Function Breakpoints

Function breakpoint:

```text
FunctionBreakpoint {
    symbol
    module?
    overload_identity?
}
```

When the module is not loaded:

```text
PENDING
```

The debugger resolves it after `ModuleLoaded`.

---

# 32. Pending Breakpoints

States:

```text
PENDING
RESOLVED
VERIFIED
INVALID
DISABLED
```

A pending breakpoint is not an error.

---

# 33. Breakpoint Verification

Every resolved breakpoint records:

```text
requested_location
resolved_address
module_identity
verification_state
```

Verification may compare:

- instruction bytes;
- symbol identity;
- source mapping;
- module build ID.

---

# 34. Register Model

Canonical:

```text
RegisterSet {
    general[]
    flags?
    control?
    vector[]
    special[]
}
```

Each register:

```text
Register {
    id
    name
    width
    category
    value
    writable
}
```

---

# 35. x86-64 Registers

Baseline:

```text
RAX RBX RCX RDX
RSI RDI RBP RSP
R8-R15
RIP
RFLAGS
```

Debug information may additionally expose:

```text
XMM
YMM
ZMM
MXCSR
segment registers
debug registers
```

depending on backend capability.

---

# 36. AArch64 Registers

Baseline:

```text
X0-X30
SP
PC
PSTATE
```

Vector:

```text
V0-V31
```

with appropriate SIMD/FP interpretation.

---

# 37. Vector Register Model

Vector values must not be forced into scalar representations.

```text
VectorRegister {
    width
    bytes
    lanes?
    lane_type?
}
```

The UI can provide multiple interpretations without changing stored register state.

---

# 38. Register Read/Write

```text
debug_read_register()
debug_write_register()
debug_read_register_set()
debug_write_register_set()
```

Writes require:

```text
target stopped
register writable
architecture-compatible value
```

A failed write must not partially corrupt a register set.

---

# 39. Memory Model

```text
DebugMemory {
    address
    size
    permissions
    region
    bytes
}
```

Permissions:

```text
READ
WRITE
EXECUTE
GUARD
SHARED
PRIVATE
```

---

# 40. Memory Regions

```text
MemoryRegion {
    base
    size
    permissions
    mapped
    module?
    name?
}
```

Examples:

```text
CODE
RODATA
DATA
HEAP
STACK
TLS
SHARED_LIBRARY
MMIO
GUARD
UNKNOWN
```

---

# 41. Memory Read

Reads must return partial results safely.

```text
MemoryReadResult {
    bytes
    valid_prefix
    fault_address?
}
```

A page boundary must not cause the debugger to fabricate bytes.

---

# 42. Memory Write

Memory writes require:

```text
explicit debugger operation
target stopped
writable region or explicit override
```

Debugger UI inspection must never accidentally turn into a write.

---

# 43. Stack Model

```text
StackInfo {
    thread
    current_sp
    stack_base
    stack_limit
    growth_direction
}
```

Stack memory may contain:

- return addresses;
- locals;
- saved registers;
- arguments;
- task frames;
- runtime frames.

---

# 44. Stack Unwinding

Preferred order:

```text
1. precise debug/unwind metadata
2. platform unwind metadata
3. frame-pointer chain
4. architecture fallback
5. stop with UNKNOWN
```

The debugger must never fabricate a frame.

---

# 45. Frame Model

```text
DebugFrame {
    index
    instruction_address
    function
    module
    source
    inline_chain[]
    registers?
    locals
    arguments
}
```

---

# 46. Inline Frames

An optimized function may contain multiple logical source frames at one machine-code address.

Therefore:

```text
physical frame
    ↓
inline chain
    ↓
logical source frames
```

must be represented explicitly.

---

# 47. Source Mapping

Canonical mapping:

```text
InstructionAddress
      ↕
SourceLocation
```

```text
SourceLocation {
    file_id
    line
    column
    end_line?
    end_column?
}
```

Mapping must include:

```text
statement boundaries
expression locations
inline locations
function ranges
```

---

# 48. Source Identity

Paths are not sufficient.

Use:

```text
SourceFileIdentity {
    content_hash?
    canonical_path?
    source_id
}
```

This allows source mapping after source trees move.

---

# 49. Source Remapping

Debug session may specify:

```text
SourceMap {
    compiled_root
    local_root
    remote_root?
}
```

Mappings are deterministic and ordered.

---

# 50. Variable Model

```text
DebugVariable {
    name
    type
    location
    value_state
    children[]
    scope
    flags
}
```

Value states:

```text
AVAILABLE
OPTIMIZED_OUT
UNAVAILABLE
UNREADABLE
NOT_IN_SCOPE
UNKNOWN
```

---

# 51. No Fabricated Values

If the compiler reports a variable as optimized out:

```text
OPTIMIZED_OUT
```

must be displayed.

The debugger must never invent a plausible value from nearby registers or memory.

---

# 52. Local Variables

Scopes:

```text
GLOBAL
MODULE
FUNCTION
BLOCK
LOOP
TASK
CLOSURE
```

Scope validity follows compiler metadata.

---

# 53. Global Variables

Globals require:

```text
module identity
symbol identity
storage address
type metadata
```

ASLR must not invalidate symbolic identity.

---

# 54. Static Variables

Static storage must distinguish:

```text
module static
function static
thread-local static
process global
```

---

# 55. Aggregate Values

Axiom structs:

```text
StructValue {
    type_id
    fields[]
}
```

Enums:

```text
EnumValue {
    type_id
    discriminant
    variant
    payload?
}
```

Unions:

```text
UnionValue {
    type_id
    active_variant?
    raw_storage
}
```

---

# 56. Pointer Values

```text
PointerValue {
    address
    pointee_type?
    nullable
}
```

The debugger must distinguish:

```text
null
valid mapped address
unmapped address
non-readable address
unknown provenance
```

---

# 57. Slice Values

Axiom slices are decoded according to AXABI.

Conceptually:

```text
Slice<T> {
    ptr
    len
}
```

The debugger must know the exact compiler-emitted representation rather than assume it.

---

# 58. String Values

Axiom `String` and `Str` are decoded using compiler ABI metadata.

The debugger should provide:

```text
raw bytes
UTF-8 interpretation
length
capacity where applicable
```

without reading beyond validated bounds.

---

# 59. C ABI Values

Foreign values use:

```text
extern "C"
```

ABI metadata.

AXDEBUGGER supports:

- C integer types;
- floating-point types;
- pointers;
- structs;
- arrays;
- enums;
- ABI-defined aggregates.

---

# 60. Native Axiom Types

Every debug-capable compiled type may have:

```text
TypeDebugDescriptor {
    type_id
    name
    kind
    size
    alignment
    fields[]
    variants[]
    generic_args[]
    layout
}
```

---

# 61. Generic Types

Generics are normally monomorphized.

Therefore the debugger sees:

```text
Vector<i32>
Vector<f64>
Vector<MyStruct>
```

as concrete instantiated types where available.

---

# 62. Generic Symbol Identity

A generic instantiation identity includes:

```text
generic_definition_id
type_arguments[]
module_identity
```

This avoids ambiguity between different monomorphizations.

---

# 63. Closure Values

Closures are represented according to compiler-generated debug metadata.

Conceptually:

```text
ClosureValue {
    function
    environment
}
```

Captured variables are exposed when their storage is available.

---

# 64. Function Values

```text
FunctionValue {
    code_address
    function_type
    environment?
}
```

The debugger distinguishes:

```text
plain function pointer
closure
method value
foreign function pointer
```

---

# 65. Expression Evaluation

Architecture:

```text
AXIDE expression
       ↓
AXDEBUGGER
       ↓
compiler semantic/type service
       ↓
debug evaluator
       ↓
target state
```

Expressions must reuse Axiom's semantic rules.

The debugger must not implement a second incompatible Axiom language parser.

---

# 66. Expression Modes

```text
READ_ONLY
DEBUG_MUTATING
RAW_MACHINE
```

Default:

```text READ_ONLY
```

---

# 67. Read-Only Evaluation

Read-only evaluation may:

- inspect locals;
- inspect fields;
- perform arithmetic;
- perform comparisons;
- dereference readable memory;
- call pure debugger-provided formatting operations.

It must not mutate target state.

---

# 68. Mutating Evaluation

Mutation requires explicit user action.

Examples:

```text
set variable
set memory
set register
```

are distinct debugger operations.

They must not be hidden inside an ordinary watch expression.

---

# 69. Function Calls From Debugger

Calling target functions is dangerous because it can:

- mutate state;
- allocate;
- block;
- acquire locks;
- trigger I/O;
- deadlock.

Therefore target function calls are disabled by default.

If supported:

```text
EXPLICIT_DEBUG_CALL
```

must be a distinct operation with clear side-effect semantics and cancellation limitations.

---

# 70. Compiler/Debugger Expression Bridge

Canonical interface:

```text
debug_parse_expression()
debug_typecheck_expression()
debug_lower_expression()
debug_evaluate_expression()
```

The compiler supplies:

```text
types
operators
casts
names
generic rules
member lookup
```

The debugger supplies:

```text
runtime values
memory
registers
frame context
```

---

# 71. Async/Task Debugging

Axiom task:

```text
Task {
    id
    state
    continuation
    stack_state
    executor
    current_thread?
}
```

A task may be:

```text
READY
RUNNING
WAITING
SUSPENDED
COMPLETED
FAILED
CANCELLED
```

---

# 72. Task Stack

An async task may not have a conventional contiguous OS-thread stack.

Debugger therefore needs:

```text
logical task frame
↓
suspended state
↓
compiler-generated continuation state
```

---

# 73. Coroutine State

Compiler emits task debug metadata describing:

```text
state machine
state identifier
suspended variables
resume function
await location
```

This permits source-level debugging across `await`.

---

# 74. Task-to-Thread Mapping

When running:

```text
Task A → Thread 3
```

After rescheduling:

```text
Task A → Thread 7
```

the debugger preserves Task A's logical identity.

---

# 75. Concurrency Inspection

Debugger exposes:

```text
threads
tasks
executors
locks
waits
channels
condition variables
```

where metadata is available.

---

# 76. Synchronization State

Canonical:

```text
SyncWait {
    waiter
    resource
    owner?
    state
}
```

The debugger may construct a wait graph:

```text
Thread A
   ↓ waits
Lock X
   ↓ owned by
Thread B
```

---

# 77. Deadlock Inspection

AXDEBUGGER may report suspected cycles:

```text
A → B → C → A
```

but this is an inspection result, not a guarantee of a deadlock unless the runtime/platform provides sufficient evidence.

---

# 78. Race Diagnostics Boundary

Race detection belongs to a dedicated subsystem/tooling layer.

AXDEBUGGER may consume:

```text
race event
race report
instrumentation metadata
```

but does not become the race detector.

---

# 79. Source-Level Stepping

`step_into` follows the next source-level executable location.

Compiler metadata must identify:

```text
statement
expression
call boundary
inline boundary
```

---

# 80. Step Over

`step_over` executes the current source operation without entering called functions where possible.

For optimized/inlined code, exact semantics depend on available debug metadata.

---

# 81. Step Out

`step_out` resumes until the current logical frame exits.

Inline frames require special treatment because an inline frame may not correspond to an independent machine stack frame.

---

# 82. Instruction Stepping

```text
step_instruction()
```

operates on machine instructions.

It is always available only where the platform backend supports it.

---

# 83. Run to Cursor

The IDE may request:

```text
run_to_source_location()
```

AXDEBUGGER resolves the source location and uses a temporary breakpoint.

The temporary breakpoint is removed after the stop.

---

# 84. Reverse Debugging Boundary

Reverse execution is **optional**.

AXDEBUGGER defines the interface:

```text
reverse_continue()
reverse_step()
checkpoint()
restore_checkpoint()
```

but does not require a general reverse-execution engine in v5.0.

If unavailable:

```text
DEBUG_REVERSE_UNSUPPORTED
```

---

# 85. Deterministic Replay

AXDEBUGGER can integrate with deterministic replay infrastructure.

Required metadata:

```text
replay_session_id
event_sequence
checkpoint_id
execution_generation
```

Replay itself belongs to a dedicated runtime/debug infrastructure layer.

---

# 86. Watch / Inspect Contract

AXCODEEDITOR and AXGUI must never directly access target memory.

They call:

```text
AXDEBUGGER
```

through an immutable inspection result.

```text
InspectionSnapshot {
    session_generation
    stop_generation
    variables[]
    frames[]
    memory_views[]
}
```

---

# 87. AXCODEEDITOR Integration

AXCODEEDITOR displays:

```text
breakpoint markers
current instruction
execution line
inline variable hints
diagnostic state
```

AXDEBUGGER owns all semantic state.

---

# 88. Breakpoint UI Contract

```text
BreakpointPresentation {
    breakpoint_id
    source_location
    enabled
    verified
    pending
    condition
    hit_count
}
```

AXCODEEDITOR never directly installs machine breakpoints.

---

# 89. AXIDE Integration

AXIDE owns orchestration:

```text
launch configuration
workspace
source selection
debug panel
terminal
project state
```

AXDEBUGGER owns target execution.

---

# 90. AXDOC Integration

AXDEBUGGER can request type documentation:

```text
type_id
symbol_id
```

AXDOC may provide:

- type description;
- field documentation;
- function documentation;
- semantic links.

Debugger does not own documentation.

---

# 91. Crash / Panic / Trap Capture

Live crash flow:

```text
target
 ↓
fault/panic/trap
 ↓
backend event
 ↓
AXDEBUGGER
 ↓
capture stable state
 ↓
classify stop reason
 ↓
AXCRASH / AXDIAGNOSTICS
```

Debugger must survive target termination.

---

# 92. Crash Artifact

Canonical:

```text
DebugCrashArtifact {
    build_id
    target
    abi
    process_info
    thread_states[]
    registers[]
    stack_frames[]
    loaded_modules[]
    exception
    source_mapping
    memory_regions?
    debug_info_identity
}
```

---

# 93. Minidump / Core Dump

AXDEBUGGER can open:

```text
Windows minidump
Linux core
platform-specific crash artifact
Axiom debug artifact
```

through adapters.

---

# 94. Postmortem Session

A postmortem session:

```text
POSTMORTEM
```

is immutable.

No:

```text
continue
step
write register
write memory
```

operations are permitted.

---

# 95. Debug Symbols

Symbol sources:

```text
embedded symbols
sidecar debug artifact
local symbol cache
configured symbol server
source package
```

Preferred production architecture:

```text
Binary
  └── minimal build/debug identity

Sidecar
  ├── symbols
  ├── types
  ├── source maps
  ├── line tables
  └── unwind metadata
```

---

# 96. Debug Artifact Identity

```text
DebugArtifactIdentity {
    build_id
    debug_id
    target
    abi
    compiler_version
    metadata_schema
}
```

The debugger must reject mismatched artifacts unless the user explicitly overrides validation.

---

# 97. Symbol Cache

Cache key:

```text
debug_id
```

not merely:

```text filename
```

This prevents stale symbols from being silently applied.

---

# 98. Symbol Server

Optional symbol lookup:

```text
local
LAN
remote
enterprise
```

Network access must be explicit.

No arbitrary symbol server is contacted automatically.

---

# 99. Symbol Identity

Axiom symbols use compiler-generated stable identifiers.

```text
SymbolId
```

is distinct from:

```text
machine address
mangled name
source spelling
```

---

# 100. Name Mangling

AXDEBUGGER consumes the canonical AXABI mangling rules.

It must be able to display:

```text
human-readable symbol
canonical symbol
linker symbol
foreign symbol
```

---

# 101. Module Tracking

```text
DebugModule {
    id
    path
    load_address
    size
    build_id
    debug_id
    symbols
    source_map
}
```

Modules include:

- executable;
- static-linked logical modules;
- shared libraries;
- dynamic libraries;
- plugins.

---

# 102. Dynamic Loader Events

AXDEBUGGER listens for:

```text
MODULE_LOAD
MODULE_UNLOAD
```

and updates:

```text
symbols
breakpoints
source maps
type database
```

Pending breakpoints may become resolved.

---

# 103. TLS Debugging

TLS variables are resolved through:

```text
module
thread
TLS key/index
offset
type
```

A debugger must never interpret TLS addresses as ordinary global addresses.

---

# 104. Arguments / Environment

Launch configuration stores:

```text
argv[]
env[]
working_directory
```

Debugger exposes them as session metadata.

Sensitive environment variables should not be automatically displayed in logs.

---

# 105. Child Processes

Process tree:

```text
DebugSession
 └── Process
      ├── Child
      └── Child
           └── Grandchild
```

Each process has its own:

```text
modules
threads
memory
register state
```

while sharing session identity.

---

# 106. Launch Configuration

```text
LaunchConfig {
    executable
    args[]
    env[]
    cwd
    target
    debugger
    break_on_entry
    break_on_panic
    symbol_paths[]
    source_maps[]
    capabilities
}
```

Configuration must be schema-versioned.

---

# 107. Capability / Sandbox Boundary

AXDEBUGGER may have extremely powerful access.

Therefore capabilities must distinguish:

```text
PROCESS_CONTROL
MEMORY_READ
MEMORY_WRITE
REGISTER_READ
REGISTER_WRITE
CODE_EXECUTION
REMOTE_DEBUG
SYMBOL_NETWORK
```

A debugger session should receive only the capabilities required.

---

# 108. Remote Security

Remote debugging requires:

```text
authentication
authorization
session binding
protocol version
capability negotiation
```

Encryption is required for untrusted networks.

An unauthenticated public debug endpoint is prohibited by architecture.

---

# 109. Debug Protocol

Internal canonical protocol:

```text
AXDBG
```

Message:

```text
DebugMessage {
    protocol_version
    session_id
    generation
    request_id
    kind
    payload
}
```

---

# 110. Request/Response

```text
request
  ↓
request_id
  ↓
backend
  ↓
response(request_id)
```

Out-of-order responses are allowed for independent asynchronous requests.

---

# 111. Event Stream

Events are unsolicited messages:

```text
DebugEvent {
    session_id
    generation
    sequence
    kind
    payload
}
```

`sequence` is monotonically increasing.

---

# 112. Event Ordering

Within a session:

```text
sequence N
<
sequence N+1
```

Events must not be reordered when delivered to consumers.

---

# 113. Asynchronous Events

Examples:

```text
ThreadCreated
ModuleLoaded
BreakpointHit
ExceptionRaised
ProcessExited
```

Consumers must tolerate events arriving while UI requests are pending.

---

# 114. Command Queue

All target-mutating operations pass through a serialized control queue:

```text
DebugCommandQueue
```

Examples:

```text
continue
pause
step
write_memory
write_register
set_breakpoint
```

This prevents concurrent commands from corrupting process-control state.

---

# 115. Cancellation

Long operations support cancellation:

```text
symbol_load
memory_scan
large_variable_decode
expression_evaluation
remote_request
```

Cancellation must not leave target control in an indeterminate state.

---

# 116. State Consistency

AXDEBUGGER maintains:

```text
session_generation
target_generation
stop_generation
module_generation
```

Results must include the generation under which they were generated.

---

# 117. Stale Result Rejection

Example:

```text
stop generation = 42

memory request → generation 42

target resumes
stop generation = 43

memory response arrives
```

Response from generation 42 must be rejected for current stopped-state UI unless explicitly requested as historical data.

---

# 118. Thread Safety

AXDEBUGGER internal state is concurrent-safe.

Target execution itself remains controlled by the backend.

Rule:

```text
read-only inspection
    → parallel where safe

target mutation
    → serialized
```

---

# 119. Release Build Overhead

Normal release build:

```text
No debugger runtime
No debugger threads
No breakpoint tables
No variable metadata
No expression evaluator
No debug allocations
```

unless explicitly enabled.

---

# 120. Debug Build Metadata

Debug metadata should preferably be emitted into:

```text
external .axdbg artifact
```

while binary retains only minimal identity information.

---

# 121. Debug Levels

Axiom defines:

```text
NONE
LINE
STANDARD
FULL
TRACE
```

Conceptual meaning:

### NONE

No source debugging.

### LINE

Address ↔ source mapping.

### STANDARD

Variables, types, frames, functions.

### FULL

Detailed scopes, aggregates, async state, inline information.

### TRACE

Additional execution/runtime instrumentation explicitly requested.

---

# 122. Debug Metadata Separation

Debug metadata may include:

```text
line tables
type descriptors
variable locations
inline tables
scope ranges
async state maps
source identity
unwind data
```

These are independently compressible and cacheable.

---

# 123. Compiler Emission

AXCOMPILER emits a canonical debug IR:

```text
DebugIR {
    files[]
    symbols[]
    types[]
    functions[]
    scopes[]
    locations[]
    inline_sites[]
    variables[]
    async_states[]
    unwind[]
}
```

AXDEBUGGER consumes the resulting artifact.

---

# 124. Debug Location Expressions

A variable location may be:

```text
register
stack offset
constant
memory address
piecewise
computed
unavailable
```

Location expressions must be bounded and non-executable in the arbitrary-code sense.

---

# 125. Optimized Code

Optimized builds can produce:

```text
merged variables
eliminated variables
reordered instructions
inlined functions
split ranges
register allocation changes
```

Debugger must expose limitations honestly.

---

# 126. Optimized-Out State

Example:

```text
x = OPTIMIZED_OUT
```

not:

```text
x = 0
```

---

# 127. Variable Location Ranges

A variable may have different locations:

```text
line 10 → RAX
line 11 → stack[32]
line 12 → optimized out
```

The debugger resolves by:

```text instruction address + scope
```

---

# 128. Debug Type Layout

Type metadata must expose:

```text
size
alignment
field offset
field size
variant discriminant
padding
ABI representation
```

This is critical for correct memory inspection.

---

# 129. ABI-Aware Decoding

AXDEBUGGER uses AXABI:

```text
AXABI
 ↓
type layout
 ↓
debug decoder
 ↓
value
```

It must not duplicate ABI assumptions.

---

# 130. Foreign Debug Types

C/C++ foreign modules may expose:

```text
DWARF
CodeView
platform symbols
```

AXDEBUGGER uses format adapters to convert them into its canonical model.

---

# 131. Debug Info Format Adapters

Required:

```text
DWARF adapter
CodeView/PDB adapter
Mach-O/dSYM adapter
WASM debug adapter
AXDBG adapter
```

---

# 132. No Format Leakage

AXDEBUGGER core must never contain logic such as:

```text
if ELF then ...
if PDB then ...
```

throughout the semantic engine.

Instead:

```text
DebugInfoProvider
```

abstracts the source.

---

# 133. Source Location Resolution

```text
debug_resolve_address(address)
debug_resolve_source(file,line,column)
debug_resolve_symbol(symbol_id)
```

Resolution returns all matching ranges when ambiguity exists.

---

# 134. Address Resolution

```text
AddressInfo {
    module
    symbol
    function
    inline_chain
    source
    instruction_offset
}
```

---

# 135. Symbol Search

Supports:

```text
exact
prefix
qualified
module-qualified
source-name
symbol-id
```

Search results are immutable.

---

# 136. Memory Inspection UI Contract

AXDEBUGGER returns:

```text
MemoryView {
    address
    bytes
    ascii?
    typed_values[]
}
```

AXCODEEDITOR/AXIDE decide presentation.

---

# 137. Stack Inspection UI Contract

```text
StackSnapshot {
    thread_id
    stop_generation
    frames[]
}
```

Frames are immutable.

---

# 138. Register Inspection UI Contract

```text
RegisterSnapshot {
    thread_id
    generation
    registers[]
}
```

No UI component writes registers directly.

---

# 139. Expression Watch List

```text
WatchExpression {
    id
    expression
    mode
    enabled
}
```

Results:

```text
WatchResult {
    expression_id
    generation
    value
    state
    error?
}
```

---

# 140. Hover Evaluation

Hover evaluation must be:

```text
read-only
bounded
cancelable
timeout-limited
```

It must never execute arbitrary target functions automatically.

---

# 141. Debugger Timeout

Potentially expensive operations receive budgets:

```text
expression timeout
memory read limit
symbol decode limit
collection expansion limit
remote request timeout
```

---

# 142. Collection Expansion

A debugger must never recursively expand an unbounded data structure.

Use:

```text
max_depth
max_children
max_bytes
max_time
```

---

# 143. Cyclic Structures

Pointer graphs may contain cycles.

Debugger tracks:

```text
visited address + type
```

to prevent infinite recursion.

---

# 144. Large Buffers

Debugger must not automatically read:

```text
1 GB buffer
```

because a user expanded a variable.

Use bounded previews and explicit expansion.

---

# 145. Security of Debug Artifacts

Debug information is untrusted input.

All parsers require:

```text
bounds checking
integer overflow checking
recursion limits
allocation limits
```

---

# 146. Symbol Server Security

Remote symbols must be validated against:

```text
debug_id
build_id
target
ABI
```

before use.

---

# 147. Target Memory Safety

Debugger memory access is privileged but still must validate:

```text address overflow
size overflow
region validity
permission
backend response length
```

---

# 148. Debugger Self-Protection

AXDEBUGGER must not crash because the target is corrupt.

Target faults must be represented as:

```text
TargetMemoryFault
TargetRegisterFault
TargetProcessExited
```

rather than debugger process corruption.

---

# 149. Resource Limits

Configurable limits:

```text
max_threads
max_modules
max_breakpoints
max_watchpoints
max_memory_read
max_expression_depth
max_variable_children
max_symbol_size
max_remote_message
```

---

# 150. Plugin Boundary

Debugger extensions use:

```text
DebugExtension
```

but plugins cannot obtain arbitrary process-control privileges automatically.

Capabilities are explicit.

---

# 151. Native Extension

Axiom-native debugger backend:

```text
DebugBackendV1
```

must be sufficient for third-party platform backends without changing the core ABI.

---

# 152. Protocol Compatibility

```text
AXDEBUGGER_ABI_1
```

defines:

- session protocol;
- object schemas;
- event types;
- capability model;
- error codes;
- generation semantics.

Unknown optional fields must be safely ignored.

---

# 153. Error Model

Canonical errors:

```text
DEBUG_INVALID_SESSION
DEBUG_TARGET_NOT_STOPPED
DEBUG_TARGET_RUNNING
DEBUG_TARGET_EXITED
DEBUG_UNSUPPORTED
DEBUG_PERMISSION_DENIED
DEBUG_BREAKPOINT_INVALID
DEBUG_BREAKPOINT_UNRESOLVED
DEBUG_HARDWARE_SLOTS_EXHAUSTED
DEBUG_MEMORY_UNREADABLE
DEBUG_MEMORY_UNWRITABLE
DEBUG_REGISTER_UNAVAILABLE
DEBUG_SYMBOL_NOT_FOUND
DEBUG_SYMBOL_MISMATCH
DEBUG_SOURCE_NOT_FOUND
DEBUG_EXPRESSION_ERROR
DEBUG_EXPRESSION_SIDE_EFFECT
DEBUG_EXPRESSION_TIMEOUT
DEBUG_STALE_GENERATION
DEBUG_REMOTE_AUTH_FAILED
DEBUG_REMOTE_PROTOCOL_MISMATCH
DEBUG_RESOURCE_LIMIT
```

---

# 154. Canonical APIs — Session

```text
debug_session_create()
debug_session_destroy()
debug_session_state()
debug_session_capabilities()
debug_session_generation()
```

---

# 155. Canonical APIs — Process

```text
debug_launch()
debug_attach()
debug_detach()
debug_terminate()
debug_kill()
debug_process()
debug_process_tree()
```

---

# 156. Canonical APIs — Execution

```text
debug_continue()
debug_pause()
debug_step_into()
debug_step_over()
debug_step_out()
debug_step_instruction()
debug_run_to_source()
debug_restart()
```

---

# 157. Canonical APIs — Breakpoints

```text
debug_breakpoint_create()
debug_breakpoint_delete()
debug_breakpoint_enable()
debug_breakpoint_disable()
debug_breakpoint_resolve()
debug_breakpoint_verify()
debug_breakpoint_list()
debug_breakpoint_set_condition()
debug_breakpoint_set_hit_policy()
debug_breakpoint_set_logpoint()
```

---

# 158. Canonical APIs — Watchpoints

```text
debug_watchpoint_create()
debug_watchpoint_delete()
debug_watchpoint_enable()
debug_watchpoint_disable()
debug_watchpoint_list()
debug_watchpoint_capabilities()
```

---

# 159. Canonical APIs — Registers

```text
debug_registers_read()
debug_registers_write()
debug_register_read()
debug_register_write()
debug_register_describe()
```

---

# 160. Canonical APIs — Memory

```text
debug_memory_regions()
debug_memory_read()
debug_memory_write()
debug_memory_validate()
debug_memory_search()
```

---

# 161. Canonical APIs — Stack

```text
debug_stack_trace()
debug_frame_get()
debug_frame_locals()
debug_frame_arguments()
debug_unwind()
```

---

# 162. Canonical APIs — Symbols

```text
debug_symbols_load()
debug_symbols_unload()
debug_symbol_lookup()
debug_symbol_search()
debug_symbol_resolve_address()
debug_symbol_identity()
```

---

# 163. Canonical APIs — Source

```text
debug_source_resolve_address()
debug_source_resolve_location()
debug_source_set_mapping()
debug_source_get_mapping()
```

---

# 164. Canonical APIs — Variables

```text
debug_variable_list()
debug_variable_read()
debug_variable_expand()
debug_variable_location()
debug_variable_type()
```

---

# 165. Canonical APIs — Expressions

```text
debug_expression_parse()
debug_expression_check()
debug_expression_evaluate()
debug_expression_cancel()
debug_expression_set_mode()
```

---

# 166. Canonical APIs — Modules

```text
debug_module_list()
debug_module_get()
debug_module_symbols()
debug_module_load_event()
debug_module_unload_event()
```

---

# 167. Canonical APIs — Tasks

```text
debug_task_list()
debug_task_get()
debug_task_stack()
debug_task_state()
debug_task_current_thread()
debug_task_resume()
```

Task resume is only supported where runtime/backend semantics permit it.

---

# 168. Canonical APIs — Crash

```text
debug_crash_open()
debug_crash_close()
debug_crash_threads()
debug_crash_stack()
debug_crash_registers()
debug_crash_modules()
debug_crash_memory()
```

---

# 169. Canonical APIs — Remote

```text
debug_remote_connect()
debug_remote_authenticate()
debug_remote_disconnect()
debug_remote_capabilities()
debug_remote_session()
```

---

# 170. Canonical APIs — Replay

```text
debug_replay_open()
debug_replay_checkpoint()
debug_replay_restore()
debug_replay_forward()
debug_replay_reverse()
```

Optional backend capability.

---

# 171. Canonical Debug Data Flow

```text
AXCOMPILER
    ↓
DebugIR
    ↓
AXOBJECT / AXBINARY
    ↓
debug artifact
    ↓
AXDEBUGGER
    ↓
DebugModel
    ↓
AXIDE / AXCODEEDITOR
```

---

# 172. Compiler → Debugger Contract

Compiler guarantees:

```text
symbol identity
type identity
source mapping
variable location metadata
inline information
unwind information
ABI layout
async/task state metadata
```

when requested by the selected debug level.

---

# 173. Debugger → Compiler Contract

Debugger requests:

```text
parse expression
resolve name
resolve type
resolve member
format type
decode generic instantiation
```

The compiler remains semantic authority.

---

# 174. AXDEBUGGER Memory Architecture

Hot structures use:

```text
arena
pool
small-vector
interned strings
immutable snapshots
```

Long-lived caches:

```text
symbol cache
type cache
source map cache
module cache
```

must be independently evictable.

---

# 175. Snapshot Architecture

Debugger UI receives immutable snapshots:

```text
TargetStateSnapshot
StackSnapshot
RegisterSnapshot
VariableSnapshot
ModuleSnapshot
```

This prevents UI race conditions with target execution.

---

# 176. Zero-Copy Debug Data

Large debug artifacts should support:

```text
memory mapping
lazy decoding
string interning
compressed block indexing
```

Only requested types/functions are decoded.

---

# 177. Symbol Loading Performance

Loading a large symbol file must not block the UI.

Pipeline:

```text
open
 ↓
validate
 ↓
index
 ↓
publish module identity
 ↓
lazy symbol/type decode
```

---

# 178. Breakpoint Performance

Breakpoint lookup uses indexed structures:

```text
source → ranges
symbol → addresses
address → breakpoint
module → breakpoints
```

No full breakpoint scan on every stop.

---

# 179. Stack Performance

Stack unwinding should be lazy:

```text
frame 0
 ↓
request frame 1
 ↓
request frame 2
```

rather than eagerly decoding hundreds of frames.

---

# 180. Variable Performance

Children are fetched lazily:

```text
variable
 ↓
summary
 ↓
expand
 ↓
children
```

---

# 181. Expression Performance

Expression evaluator has:

```text
parse cache
type cache
compiled evaluator cache
```

keyed by:

```text expression
module build ID
debug generation
type context
```

---

# 182. Concurrency Architecture

Independent read operations can execute concurrently:

```text
symbols
memory
stack
variables
```

but all target mutation is serialized.

---

# 183. Stop-the-World Semantics

When a backend reports a process stop:

```text
all controllable threads
```

are considered stopped unless the backend explicitly reports partial-stop semantics.

The debugger records:

```text
global stop state
per-thread stop state
```

---

# 184. Partial Stop

Some platforms can expose nonuniform thread state.

AXDEBUGGER must represent:

```text
STOPPED
RUNNING
UNKNOWN
```

per thread.

---

# 185. Thread Selection

Debugger UI selects:

```text
current thread
current frame
```

without changing target execution.

---

# 186. Frame Selection

Changing selected frame changes inspection context only:

```text
selected_frame
```

It does not move execution.

---

# 187. Register Context

Register inspection uses selected thread.

Frame-relative logical registers are reconstructed from unwind information where necessary.

---

# 188. Memory Context

Memory reads are independent of selected frame.

Stack-relative views are derived from:

```text selected frame + unwind context
```

---

# 189. Debug Session Persistence

Persist:

```text breakpoints
watch expressions
launch configuration
source mappings
debug preferences
```

Do not persist volatile:

```text process IDs
raw addresses
register values
```

as authoritative state.

---

# 190. Breakpoint Persistence

Persistent identity:

```text symbol_id
source_id
source_range
module_build_id?
```

Address is only cached optimization.

---

# 191. Recompilation

After recompilation:

```text old address
     ↓
discard
     ↓
resolve logical breakpoint
     ↓
new address
```

when symbol/source identity remains compatible.

---

# 192. Binary Build Identity

A binary gets:

```text BuildId
```

from AXBUILD/AXCOMPILER/AXLINKER.

AXDEBUGGER uses it to prevent accidental symbol mismatches.

---

# 193. Reproducibility

Debug artifacts must be reproducible given:

```text source
compiler
toolchain
target
ABI
debug level
build configuration
```

Paths can be normalized through source maps.

---

# 194. Deterministic Debugging

AXTEST should be able to reproduce:

```text breakpoint location
source mapping
symbol ordering
type ordering
debug artifact hashes
```

independent of parallel compilation order.

---

# 195. Debug Event Recording

Optional event recording:

```text DebugTrace {
    sequence
    timestamp?
    event
    thread
    process
}
```

Timestamp is diagnostic metadata, not semantic ordering.

Sequence number is authoritative.

---

# 196. Crash Resilience

If target crashes:

```text target → terminated/crashed
AXDEBUGGER → capture → classify → preserve session
```

Debugger must not lose:

- last known modules;
- thread list;
- registers;
- stop reason;
- stack;
- debug identity.

---

# 197. Debugger Crash Resilience

AXDEBUGGER itself should isolate risky parsers/backends where possible.

A corrupt target or debug artifact must not terminate the entire IDE.

---

# 198. Backend Isolation

Architecture:

```text
AXDEBUGGER CORE
      │
      ├── WindowsBackend
      ├── LinuxBackend
      ├── MacBackend
      ├── AndroidBackend
      ├── iOSBackend
      └── WASMBackend
```

Backend failure becomes:

```text DEBUG_BACKEND_ERROR
```

with diagnostic details.

---

# 199. AXTEST Integration

AXTEST validates:

```text session lifecycle
breakpoints
watchpoints
registers
memory
stack
symbols
source mapping
variables
expressions
async
tasks
crashes
remote protocol
```

---

# 200. Debugger Unit Tests

Each subsystem has isolated tests:

```text breakpoint resolver
source mapper
symbol index
type decoder
expression parser bridge
generation validator
snapshot manager
```

---

# 201. Backend Integration Tests

For each target:

```text launch
attach
break
step
inspect
continue
crash
detach
```

must be tested.

---

# 202. ABI Tests

AXTEST verifies debugger decoding of:

```text scalar
struct
enum
union
slice
string
pointer
function value
generic type
closure
TLS
```

against AXABI.

---

# 203. Source Mapping Tests

Golden tests include:

```text simple function
nested blocks
inlining
generic instantiation
async/await
optimization
multiple source files
source remapping
```

---

# 204. Stack Tests

Verify:

```text frame pointer
DWARF unwind
Windows unwind
Mach-O unwind
inline frames
mixed native/foreign frames
corrupt stack
```

---

# 205. Breakpoint Tests

Required:

```text source breakpoint
function breakpoint
pending breakpoint
conditional breakpoint
hit count
logpoint
hardware breakpoint
software breakpoint
module unload/reload
recompilation
```

---

# 206. Memory Tests

Verify:

```text mapped read
unmapped read
guard page
cross-page read
write protection
overflow
large request
target exit during read
```

---

# 207. Expression Tests

Verify:

```text arithmetic
locals
fields
arrays
slices
generic values
casts
comparisons
short-circuit operators
invalid expressions
side effects
timeouts
```

---

# 208. Async Tests

Required:

```text await stop
resume
task migration
task suspension
task completion
task failure
task cancellation
multiple executors
```

---

# 209. Remote Tests

Verify:

```text authentication
capability negotiation
version mismatch
disconnect
reconnect
request cancellation
message ordering
resource limits
malformed packets
```

---

# 210. Fuzzing

Fuzz targets:

```text DWARF parser
CodeView parser
PDB adapter
Mach-O symbols
WASM debug metadata
AXDBG parser
expression bridge
source-map parser
remote protocol
crash artifacts
```

---

# 211. Differential Testing

Compare AXDEBUGGER results against:

```text platform-native debugger
reference DWARF/CodeView consumers
known-good ABI decoder
```

for supported cases.

Differential testing does not make external debuggers runtime dependencies.

---

# 212. Security Tests

Required:

```text malformed debug info
malformed remote packet
integer overflow
memory range overflow
symbol decompression bomb
recursive type explosion
expression resource exhaustion
remote authentication bypass
```

---

# 213. Performance Targets

Baseline target:

```text simple breakpoint resolution      < 1 ms
source-location lookup                < 1 ms
cached symbol lookup                  < 1 ms
register snapshot                     < 1 ms
small memory read                     < 1 ms
simple stack unwind                   < 2 ms
simple variable display               < 2 ms
completion of debug event processing  < 2 ms
```

These are target budgets, not universal guarantees across remote/slow targets.

---

# 214. Large Program Targets

For:

```text 10,000+ functions
1,000+ modules
100,000+ symbols
100+ threads
```

AXDEBUGGER must remain responsive through:

```text indexing
lazy decoding
virtualized enumeration
incremental updates
```

---

# 215. No Hidden Application Cost

Compiling:

```text axc app.ax -O2
```

without debug instrumentation must not introduce debugger runtime machinery.

Debug information lives primarily outside executable code.

---

# 216. Debug Instrumentation

Explicit instrumentation may be requested:

```text -g
-debug
-debug=full
-instrument=debug
```

Instrumentation must be opt-in.

---

# 217. Trace Mode

Trace mode may emit:

```text task events
scheduler events
function events
allocation events
```

but this is instrumentation, not baseline debugging.

---

# 218. Profiler Boundary

AXDEBUGGER may expose:

```text debug_profiler_attach()
debug_profiler_marker()
```

integration points.

Actual profiling is owned by AXPROFILER.

---

# 219. Observability Boundary

AXDEBUGGER may consume:

```text logs
traces
metrics
```

for correlation.

It does not become AXOBSERVABILITY.

---

# 220. Debug Metadata Compression

Debug artifacts should support:

```text compressed sections
block indexes
lazy decompression
string tables
deduplicated types
```

to reduce disk usage.

---

# 221. Type Deduplication

Equivalent compiler types may share:

```text TypeId
```

within a module/debug artifact.

Cross-module canonicalization is optional.

---

# 222. Symbol Index

Canonical index:

```text SymbolIndex {
    by_id
    by_name
    by_address
    by_source
    by_module
}
```

---

# 223. Source Index

```text SourceIndex {
    source_id → ranges[]
    location → address ranges
}
```

Must support logarithmic or near-logarithmic lookup.

---

# 224. Debug Artifact Format

Canonical Axiom debug artifact:

```text .axdbg
```

Conceptual layout:

```text Header
Identity
Target/ABI
StringTable
SourceTable
SymbolTable
TypeTable
LineTable
ScopeTable
VariableTable
InlineTable
AsyncTable
UnwindTable
Metadata
Index
```

---

# 225. `.axdbg` Properties

Requirements:

```text versioned
deterministic
streamable
memory-map friendly
checksummed
random-access indexed
```

---

# 226. Artifact Validation

Before consumption:

```text header
 ↓
version
 ↓
target
 ↓
ABI
 ↓
build ID
 ↓
section bounds
 ↓
indexes
 ↓
cross references
```

must be validated.

---

# 227. Cross-Reference Integrity

Every:

```text SymbolId
TypeId
SourceId
FunctionId
ModuleId
```

reference must either resolve or be explicitly marked external/optional.

---

# 228. Debug Metadata Provenance

Each semantic record may carry:

```text compiler_generated
foreign_debug
runtime_generated
user_override
```

This allows diagnostics to distinguish authoritative compiler information from imported information.

---

# 229. AI Integration

AXDEBUGGER may provide AI-readable inspection context:

```text DebugContext {
    process
    thread
    frame
    source
    variables
    exception
    task
    modules
}
```

AI tools must receive explicit read-only snapshots by default.

---

# 230. AI Mutation Boundary

AI may propose:

```text breakpoint
expression
variable change
memory change
```

but mutations require explicit debugger action approval.

No hidden AI execution.

---

# 231. AI Context Provenance

Every AI-generated debugger action records:

```text source
request
session_id
generation
timestamp?
action
approval
result
```

---

# 232. Accessibility

AXDEBUGGER exposes semantic structures for AXIDE:

```text process tree
thread tree
call stack
locals
watch values
registers
memory
breakpoints
```

AXGUI renders them.

---

# 233. Headless Debugger

Everything essential must work without GUI:

```text ax debug
ax debug attach
ax debug launch
ax debug break
ax debug stack
ax debug vars
ax debug memory
```

CLI is an AXIDE/AXCLI consumer of AXDEBUGGER, not the debugger itself.

---

# 234. Remote Headless Mode

A headless machine may run:

```text AXDEBUGGER server
```

without:

```text AXGUI
AXIDE
AXCODEEDITOR
```

---

# 235. Embedded Debugging

AXDEBUGGER may be embedded in:

```text test runner
IDE
CI
crash analyzer
AI agent
```

through the stable protocol.

---

# 236. CI Debugging

AXTEST can launch a failed test under AXDEBUGGER automatically when configured.

No debugger is required in normal test execution.

---

# 237. Test Failure Artifact

AXTEST may emit:

```text test.axcrash
test.axdbgstate
```

containing:

```text binary identity
stack
registers
source location
variables
logs
```

subject to configured privacy/security policy.

---

# 238. Privacy

Debugger must avoid automatically persisting:

```text passwords
environment secrets
tokens
private memory
```

unless explicitly requested.

---

# 239. Deterministic Error Reporting

Debug errors must have:

```text stable code
human message
machine metadata
session generation
backend origin
```

---

# 240. Diagnostics Example

```text
DEBUG_SYMBOL_MISMATCH

binary:
    build_id = A

debug artifact:
    build_id = B

target:
    x86_64-windows
```

The debugger must stop rather than silently mixing artifacts.

---

# 241. Backend State Machine

```text
DISCONNECTED
    ↓
ATTACHING
    ↓
CONNECTED
    ↓
STOPPED ↔ RUNNING
    ↓
CRASHED / TERMINATED
    ↓
DISCONNECTED
```

Stepping is represented as a controlled transition from STOPPED to RUNNING and back to STOPPED.

---

# 242. Backend Command Serialization

Only one control transition may own the target at a time.

Example:

```text
step_over
    ↓
RUNNING
    ↓
breakpoint/event
    ↓
STOPPED
```

A second `continue` arriving during the transition is queued or rejected according to command policy.

---

# 243. Debug Session Ownership

A target process may have:

```text one controlling session
multiple read-only observers
```

where platform support permits.

Only the controlling session may mutate execution.

---

# 244. Observer Sessions

Observer mode:

```text read registers
read memory
read stack
read symbols
```

but cannot:

```text continue
step
write memory
write registers
```

---

# 245. Multi-Process Sessions

The session manager correlates:

```text process IDs
parent-child relations
module identities
thread identities
```

without conflating them.

---

# 246. Loader Integration

AXLOADER owns actual loading.

AXDEBUGGER receives:

```text loaded image
module identity
base address
segments
symbols/debug identity
```

and observes loader events.

---

# 247. Startup Integration

AXSTARTUP exposes the initial source-level entry:

```text __ax_start
```

and optionally maps it to:

```text application main
```

so users need not manually step through platform bootstrap unless requested.

---

# 248. Runtime Integration

AXRUNTIME may expose debugger hooks:

```text panic
trap
task state
runtime frames
allocator diagnostics
```

but hooks must be optional and stripped in release builds.

---

# 249. Runtime Debug Hook ABI

Optional:

```text AXDEBUG_HOOKS
```

must be versioned separately from ordinary runtime ABI.

---

# 250. Panic Handling

A panic event should identify:

```text panic code
source
message
thread/task
stack
```

without requiring a heavyweight exception runtime.

---

# 251. Trap Handling

Hardware/software traps are classified:

```text illegal_instruction
divide_error
access_fault
breakpoint
debug_trap
explicit_axiom_trap
```

platform adapters normalize these.

---

# 252. Signal Handling

Linux/macOS signals map to canonical events while retaining:

```text native signal number
code
fault address
```

for platform-specific inspection.

---

# 253. Windows Exception Handling

Windows exception code is retained:

```text exception_code
exception_address
exception_information[]
```

and normalized into AXDEBUGGER's event model.

---

# 254. Source-Level Panic

When compiler/runtime metadata identifies panic origin:

```text runtime panic frame
      ↓
source panic location
```

the debugger selects the logical source frame.

---

# 255. Faulting Instruction

Every hardware fault should expose:

```text instruction_pointer
fault_address?
access_type?
```

where platform provides it.

---

# 256. Memory Access Classification

If available:

```text READ
WRITE
EXECUTE
UNKNOWN
```

is recorded.

---

# 257. Mixed Axiom/Foreign Stack

Stack may be:

```text Axiom
 ↓
Axiom
 ↓
C
 ↓
OS
 ↓
Axiom callback
```

AXDEBUGGER keeps frame language metadata.

---

# 258. Foreign Frame Model

```text FrameLanguage {
    AXIOM
    C
    FOREIGN
    UNKNOWN
}
```

---

# 259. ABI Boundary Display

Debugger may show:

```text Axiom → C
C → Axiom
```

as explicit ABI transitions.

---

# 260. Calling Convention Display

Optional detailed inspection:

```text function
calling convention
arguments
return ABI
register assignments
stack arguments
```

Useful for low-level debugging and compiler development.

---

# 261. Compiler Developer Mode

AXDEBUGGER provides optional machine-level mode:

```text source
IR
machine instruction
register allocation
ABI
relocation
```

This is primarily for Axiom compiler/toolchain developers.

---

# 262. Source ↔ Instruction View

One source statement may map to:

```text multiple instructions
```

and one instruction may map to:

```text multiple inline source frames
```

The mapping must preserve both relationships.

---

# 263. Disassembly Boundary

AXDEBUGGER may request disassembly from:

```text AXASSEMBLER / AXCOMPILER instruction metadata
```

but does not own assembler semantics.

---

# 264. Instruction Decode

Platform instruction decoder may be supplied by AXASSEMBLER infrastructure.

Debugger consumes:

```text instruction
length
mnemonic
operands
source address
```

---

# 265. Breakpoint Safety

Before software breakpoint insertion:

```text verify executable mapping
verify instruction boundary
save original bytes
insert trap
flush instruction cache if required
```

---

# 266. Breakpoint Restoration

On removal:

```text verify process/module generation
verify expected trap bytes
restore original bytes
```

If bytes differ:

```text DEBUG_BREAKPOINT_CONTENT_CHANGED
```

rather than overwriting unknown code.

---

# 267. Self-Modifying Code

Self-modifying code is not assumed safe.

Debugger reports breakpoint state as:

```text INVALIDATED
```

when target code changes unexpectedly.

---

# 268. JIT Code

If Axiom eventually supports JIT:

```text JIT module identity
code range
source mapping
debug artifact
```

can be registered dynamically.

JIT support is an extension point, not a mandatory v5.0 runtime requirement.

---

# 269. Dynamic Code Registration

Optional API:

```text debug_register_code_region()
debug_unregister_code_region()
```

---

# 270. Security Boundary for JIT

Debugger must not execute arbitrary code merely because a debug artifact claims a region is executable.

Target/backend remains authoritative.

---

# 271. Debugger and ASLR

All symbolic addresses are:

```text module-relative
```

or derived from runtime module load addresses.

Persistent breakpoints never store raw addresses as canonical identity.

---

# 272. PIE

PIE executables use:

```text runtime load base + relative symbol address
```

for address resolution.

---

# 273. Shared Libraries

Shared-library breakpoints can remain pending until:

```text ModuleLoaded
```

---

# 274. Unloaded Modules

When a module unloads:

```text addresses invalid
```

but logical breakpoints remain persisted.

---

# 275. Reused Addresses

Address reuse must never resurrect an old module breakpoint without validating:

```text module build ID
module generation
symbol/source identity
```

---

# 276. Debugger Session Log

Optional structured log:

```text DebugLogEvent {
    sequence
    category
    severity
    message
    metadata
}
```

No target secrets should be logged automatically.

---

# 277. Debug Logging Levels

```text ERROR
WARN
INFO
DEBUG
TRACE
```

Debugger logging is independent of target logging.

---

# 278. Protocol Version Negotiation

Client/server exchange:

```text protocol
ABI
features
extensions
```

before session activation.

---

# 279. Capability Negotiation

Example:

```text client:
    hardware_watchpoint
    reverse_debug

server:
    hardware_watchpoint
```

Intersection becomes active capability set.

---

# 280. Protocol Compatibility

Required:

```text same major ABI
compatible minor ABI
```

Unknown optional fields may be ignored.

Unknown required capabilities cause explicit failure.

---

# 281. Remote Resource Limits

Server must enforce:

```text max clients
max sessions
max request size
max memory request
max expression time
max symbol cache
```

---

# 282. Remote Session Isolation

A remote client must never access another session's:

```text process
memory
symbols
breakpoints
events
```

---

# 283. Authentication Context

Every remote request carries an authenticated session identity.

Authorization is evaluated before privileged operations.

---

# 284. Debugger API Stability

Public ABI is:

```text AXDEBUGGER_ABI_1
```

Internal backend APIs may evolve without ABI stability.

---

# 285. ABI Struct Rules

Public structs use:

```text version
size
flags
reserved
```

where extensibility is required.

---

# 286. Handles

Opaque handles:

```text DebugSessionHandle
DebugProcessHandle
DebugThreadHandle
DebugFrameHandle
DebugBreakpointHandle
DebugWatchpointHandle
DebugModuleHandle
```

must not expose internal memory layout.

---

# 287. Lifetime Rules

Handle lifetime:

```text session
 ├── process
 │    ├── thread
 │    └── module
 ├── breakpoint
 └── watchpoint
```

Destroying a session invalidates all child handles.

---

# 288. Stale Handles

Every handle carries an internal generation.

Using an invalid handle returns:

```text DEBUG_INVALID_HANDLE
```

rather than dereferencing stale memory.

---

# 289. ABI Ownership

AXDEBUGGER allocates its own result objects.

Callers release through:

```text debug_free()
```

or typed destruction functions.

No cross-allocator ownership ambiguity.

---

# 290. String ABI

Debugger strings are UTF-8.

Binary/non-text data remains:

```text Bytes
```

rather than being forced through string encoding.

---

# 291. Paths

Paths may be platform-native internally but exposed through canonical UTF-8 path representation.

Source identity remains hash-based.

---

# 292. Time

Debugger timestamps are diagnostic.

Semantic event ordering uses:

```text sequence
```

not wall-clock time.

---

# 293. Memory Address Type

Use:

```text Address = u64
```

for current baseline architectures.

WASM uses its logical address model rather than pretending to have host virtual addresses.

---

# 294. Register Value Type

```text RegisterBits {
    width
    bytes[]
}
```

avoids forcing vector/control registers into integers.

---

# 295. Stop Generation

Every stopped state increments:

```text stop_generation
```

This is the primary mechanism preventing stale variable/register/memory inspection.

---

# 296. Event Generation

Events contain:

```text session_generation
stop_generation?
sequence
```

Consumers can determine whether a result is current.

---

# 297. Snapshot Validity

Snapshot:

```text valid_from_generation
valid_until_generation?
```

For live state, default validity ends when the target resumes.

---

# 298. Immutable UI Data

AXIDE receives immutable:

```text snapshot
```

and never directly holds mutable backend objects.

---

# 299. Debugger Architecture Summary

```text
                     AXIDE
                       │
                AXDEBUGGER API
                       │
             ┌─────────▼─────────┐
             │  Session Manager  │
             └─────────┬─────────┘
                       │
       ┌───────────────┼────────────────┐
       │               │                │
   Control          Inspection       Metadata
       │               │                │
   Process          Memory           Symbols
   Thread           Registers        Types
   Breakpoint       Stack            Source
   Watchpoint       Variables        ABI
       │               │                │
       └───────────────┼────────────────┘
                       │
                Backend Interface
                       │
       ┌───────┬───────┼───────┬────────┐
       │       │       │       │        │
    Windows Linux   macOS Android   WASM
```

---

# 300. Fundamental Invariants

The following invariants are normative.

### DEBUG-INV-01
A debugger session must have a unique session identity.

### DEBUG-INV-02
Every target control operation belongs to exactly one session.

### DEBUG-INV-03
AXDEBUGGER must distinguish process, OS thread, Axiom task and async continuation.

### DEBUG-INV-04
Target mutation is serialized.

### DEBUG-INV-05
Read-only inspection may execute concurrently where backend-safe.

### DEBUG-INV-06
Every asynchronous result carries generation information.

### DEBUG-INV-07
Stale results must not mutate current debugger state.

### DEBUG-INV-08
A breakpoint address is not its canonical identity.

### DEBUG-INV-09
Persistent breakpoints use symbolic/source identity where available.

### DEBUG-INV-10
Software breakpoint restoration must verify expected trap bytes.

### DEBUG-INV-11
Hardware breakpoint limitations must be reported explicitly.

### DEBUG-INV-12
Unsupported watchpoint semantics must not be simulated deceptively.

### DEBUG-INV-13
Register reads must respect backend architecture.

### DEBUG-INV-14
Register writes require an explicitly stopped target.

### DEBUG-INV-15
Memory reads must be bounds-checked.

### DEBUG-INV-16
Memory writes require explicit authorization.

### DEBUG-INV-17
Unmapped memory must never be represented as valid data.

### DEBUG-INV-18
Stack unwinding must never fabricate frames.

### DEBUG-INV-19
Inline frames must be distinguishable from physical frames.

### DEBUG-INV-20
Optimized-out variables must remain explicitly optimized-out.

### DEBUG-INV-21
Variable decoding must use ABI/type metadata when available.

### DEBUG-INV-22
Generic values must preserve concrete type arguments.

### DEBUG-INV-23
Async tasks must not be modeled as OS threads.

### DEBUG-INV-24
Task migration must preserve logical task identity.

### DEBUG-INV-25
Expression evaluation is read-only by default.

### DEBUG-INV-26
Target function calls are never implicit.

### DEBUG-INV-27
Expression evaluation must obey resource limits.

### DEBUG-INV-28
AXDEBUGGER must not become the profiling subsystem.

### DEBUG-INV-29
Release builds must not contain mandatory debugger runtime overhead.

### DEBUG-INV-30
Debug artifacts must be independently identifiable from binaries.

### DEBUG-INV-31
Mismatched debug artifacts must be rejected by default.

### DEBUG-INV-32
Remote debugging must authenticate before privileged operations.

### DEBUG-INV-33
Remote debugging must not be enabled publicly by default.

### DEBUG-INV-34
Postmortem sessions must not mutate target state.

### DEBUG-INV-35
Corrupt target state must not corrupt debugger state.

### DEBUG-INV-36
Debug metadata parsing must enforce resource limits.

### DEBUG-INV-37
AXIDE/AXCODEEDITOR must not directly control target memory or execution.

### DEBUG-INV-38
Compiler semantic metadata is authoritative over debugger heuristics.

### DEBUG-INV-39
AXDEBUGGER ABI changes require explicit ABI versioning.

### DEBUG-INV-40
Every conforming AXDEBUGGER implementation must satisfy all mandatory invariants above.

---

# 301. Canonical End-to-End Launch Flow

```text
AXIDE
  ↓
LaunchConfig
  ↓
AXDEBUGGER
  ↓
validate target
  ↓
AXPROCESS launch
  ↓
AXLOADER creates image
  ↓
AXSTARTUP
  ↓
module discovery
  ↓
debug artifact match
  ↓
symbol/source indexing
  ↓
pending breakpoint resolution
  ↓
entry breakpoint
  ↓
STOPPED
  ↓
AXCODEEDITOR displays source
```

---

# 302. Canonical Breakpoint Flow

```text
source location
    ↓
Symbol/Source resolver
    ↓
module/range
    ↓
runtime address
    ↓
backend breakpoint
    ↓
verification
    ↓
VERIFIED
```

On hit:

```text target
 ↓
backend event
 ↓
StopReason::BREAKPOINT
 ↓
stop_generation++
 ↓
stack/register/variable snapshot
 ↓
AXIDE
```

---

# 303. Canonical Crash Flow

```text target
 ↓
fault
 ↓
backend exception
 ↓
AXDEBUGGER
 ↓
capture registers
 ↓
capture stack
 ↓
capture modules
 ↓
resolve source
 ↓
classify panic/trap/fault
 ↓
CRASHED
 ↓
AXCRASH / AXDIAGNOSTICS
```

---

# 304. Canonical Async Flow

```text source await
    ↓
AXCOMPILER async metadata
    ↓
task suspension
    ↓
AXTASK
    ↓
task state metadata
    ↓
AXDEBUGGER
    ↓
logical task frame
    ↓
source await location
```

---

# 305. Canonical Remote Flow

```text AXIDE
   ↓
AXDEBUGGER client
   ↓
authenticate
   ↓
capability negotiation
   ↓
AXDBG protocol
   ↓
remote AXDEBUGGER
   ↓
platform backend
   ↓
target
```

---

# 306. Compiler Integration Requirement

AXCOMPILER 5.0 must expose enough metadata to make AXDEBUGGER deterministic for:

```text symbols
source
types
variables
inline frames
unwind
ABI
async
tasks
closures
generics
```

This becomes part of the compiler/debugger contract.

---

# 307. AXABI Integration Requirement

AXABI must define canonical debugger-visible representation for:

```text scalar
aggregate
enum
union
slice
string
function value
closure
TLS
method receiver
generic instantiation
```

---

# 308. AXOBJECT Integration Requirement

AXOBJECT must preserve:

```text debug artifact identity
symbol relationships
section metadata
relocation metadata
build identity
```

required for post-link debugging.

---

# 309. AXBINARY Integration Requirement

AXBINARY must expose:

```text build ID
debug artifact reference
module identity
loadable image identity
```

without embedding the full debug database.

---

# 310. AXLOADER Integration Requirement

AXLOADER provides:

```text module load/unload events
runtime load address
mapped segments
dynamic dependency identity
TLS module state
```

to AXDEBUGGER.

---

# 311. AXSTARTUP Integration Requirement

AXSTARTUP exposes source mapping from:

```text raw process entry
```

to:

```text Axiom runtime entry
application entry
```

when debug metadata exists.

---

# 312. AXRUNTIME Integration Requirement

AXRUNTIME provides optional:

```text panic hook
task state metadata
runtime frame metadata
debug registration
```

with zero-cost release elimination.

---

# 313. AXTASK Integration Requirement

AXTASK exposes:

```text task identity
state
continuation
executor
suspension point
current OS thread
```

only in debug-enabled configurations.

---

# 314. AXASYNC Integration Requirement

AXASYNC/compiler metadata must map:

```text await site
state machine state
suspended locals
resume point
```

to source locations.

---

# 315. AXCODEEDITOR Integration Requirement

AXCODEEDITOR consumes only:

```text DebugPresentation
```

and never owns:

```text breakpoint engine
process control
memory access
register state
```

---

# 316. AXIDE Integration Requirement

AXIDE owns:

```text debug workflow
launch configurations
workspace integration
session tabs
debug views
```

while AXDEBUGGER owns execution semantics.

---

# 317. AXTEST Integration Requirement

AXTEST must validate:

```text all 40 DEBUG-INV
```

plus target/backend conformance.

---

# 318. Native Bootstrap Strategy

Stage0 may use host-native debugging facilities.

Stage1/Stage2 progressively replace external components.

Final architecture:

```text Axiom source
   ↓
AXCOMPILER
   ↓
AXOBJECT
   ↓
AXLINKER
   ↓
AXBINARY
   ↓
AXLOADER
   ↓
AXSTARTUP
   ↓
AXRUNTIME
   ↑
AXDEBUGGER
```

No third-party debugger is required for final Axiom development.

---

# 319. Self-Hosting Requirement

The eventual self-hosted debugger must be capable of debugging:

```text AXCOMPILER
AXLINKER
AXLOADER
AXRUNTIME
AXIDE
AXDEBUGGER
```

including itself where platform restrictions permit.

---

# 320. Bootstrap Validation

AXTEST must execute:

```text Stage0 debugger
    ↓
debug Stage1 compiler
    ↓
debug Stage2 compiler
    ↓
debug self-hosted compiler
```

and compare:

```text source mappings
symbol identity
stack traces
breakpoint behavior
variable decoding
```

---

# 321. Definition of Done

AXDEBUGGER 5.0 is complete only when:

1. `AXDEBUGGER_ABI_1` is frozen.
2. Session lifecycle is implemented.
3. Launch/attach/detach work on supported targets.
4. Process/thread models are stable.
5. OS thread and Axiom task are distinct.
6. Software breakpoints work.
7. Hardware breakpoint capability reporting works.
8. Conditional breakpoints work where supported.
9. Watchpoints report exact capability.
10. Exception/panic/trap stops work.
11. Source breakpoints survive recompilation where identity permits.
12. Registers are readable on supported architectures.
13. Memory inspection is safe and bounded.
14. Stack unwinding works with available unwind metadata.
15. Inline frames are represented correctly.
16. DWARF/CodeView/Mach-O/WASM debug adapters exist as applicable.
17. `.axdbg` is validated and loadable.
18. Build/debug identities are enforced.
19. Axiom types decode through AXABI.
20. C ABI types can be inspected.
21. Optimized-out values are represented honestly.
22. Generic and closure values are inspectable where metadata exists.
23. Async/task state is inspectable.
24. Task migration does not destroy logical identity.
25. Expression evaluation is read-only by default.
26. Debugger function calls are never implicit.
27. Remote debugging is authenticated.
28. Postmortem sessions are supported.
29. AXCODEEDITOR integration is presentation-only.
30. AXIDE integration uses the stable debugger protocol.
31. Release builds have no mandatory debugger runtime overhead.
32. AXTEST covers all mandatory invariants.
33. Fuzzing covers debug artifact and protocol parsers.
34. Differential tests exist for supported platform debug formats.
35. Deterministic debug artifacts are reproducible.
36. Resource limits are enforced.
37. Security review passes.
38. Backend failures cannot corrupt core debugger state.
39. Self-hosting/debugging of Axiom toolchain is demonstrated.
40. `AXDEBUGGER 5.0` is frozen.

---

# 322. Final AXDEBUGGER Contract

The definitive architecture is:

```text
                         ┌───────────────────┐
                         │       AXIDE       │
                         └─────────┬─────────┘
                                   │
                          AXDEBUGGER_ABI_1
                                   │
                         ┌─────────▼─────────┐
                         │    AXDEBUGGER     │
                         │                   │
                         │ Session           │
                         │ Process/Thread    │
                         │ Task/Async        │
                         │ Breakpoints       │
                         │ Watchpoints       │
                         │ Registers         │
                         │ Memory            │
                         │ Stack/Frames      │
                         │ Variables         │
                         │ Expressions       │
                         │ Source Mapping    │
                         │ Crash/Trap        │
                         │ Remote            │
                         └─────────┬─────────┘
                                   │
                  ┌────────────────┼────────────────┐
                  │                │                │
             AXCOMPILER          AXABI          AXRUNTIME
                  │                │                │
             DebugIR/type       ABI layout      task/panic
                  │                │                │
                  └────────────────┼────────────────┘
                                   │
                           Debug Backend
                                   │
       ┌───────────┬───────────────┼──────────────┬──────────┐
       │           │               │              │          │
    Windows      Linux          macOS         Android     WASM
      PE64       ELF64         Mach-O          ELF64       VM
```

**AXDEBUGGER 5.0 is therefore frozen.**

## Next task

**BOOTSTRAP-791 — AXPROFILER**

**Native Axiom Profiler, CPU Sampling, Instrumentation, Hardware Counters, Allocation Profiling, Task/Async Profiling, Lock/Wait Analysis, Call-Tree Aggregation, Flame Graph Data Model, Timeline Profiling, Cross-Platform Performance Counters, Low-Overhead Production Profiling, Trace Capture, Profile Artifacts & Profiling ABI 5.0**