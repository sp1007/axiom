# BOOTSTRAP-792 — AXCRASH

**Native Axiom Crash Capture, Fault Classification, Panic/Trap Reporting, Minidump/Core-Dump Generation, Crash Artifact Format, Symbolized Stack Capture, Exception Context, Native/Managed State Correlation, Crash Recovery, Postmortem Analysis, Crash Database, Deduplication, Privacy Controls, Remote Crash Collection & Crash ABI 5.0**

**Status:** FROZEN — 5.0  
**Namespace:** `AXCRASH`  
**ABI:** `AXCRASH_ABI_1`  
**Artifact:** `.axcrash`  
**Schema:** `AXCRASH_SCHEMA_1`

**Depends on:** `AXDEBUGGER`, `AXPROFILER`, `AXSTARTUP`, `AXABI`, `AXBINARY`, `AXLOADER`, `AXPROCESS`, `AXRUNTIME`, `AXMEMORY`, `AXTASK`, `AXASYNC`, `AXTIME`, `AXTEST`, `AXDOC`

**Optional integrations:** `AXOBSERVABILITY`, `AXDIAGNOSTICS`, `AXSECURITY`, `AXTRUST`, `AXCRYPTO`, `AXIDE`, `AXCODEEDITOR`

---

# 1. Purpose

AXCRASH is the native Axiom subsystem responsible for capturing and preserving abnormal process termination and execution-fault state.

Its fundamental question is:

> **What happened when the program failed, and what evidence can be preserved for later analysis?**

Architecture:

```text
                         Axiom Application
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
           Panic/Trap       OS Exception       Fatal Fault
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                           AXCRASH
                                │
               ┌────────────────┼────────────────┐
               │                │                │
          Fault Capture    State Capture    Artifact Writer
               │                │                │
               └────────────────┼────────────────┘
                                ▼
                         .axcrash artifact
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         Local Analysis    AXIDE/Debugger    Remote Collection
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                         Postmortem Analysis
```

---

# 2. Fundamental Boundary

The architectural distinction is:

```text
AXDEBUGGER  = interactive live execution inspection
AXPROFILER  = performance measurement
AXDIAGNOSTICS = general diagnostic information
AXOBSERVABILITY = telemetry
AXCRASH     = abnormal termination evidence
```

AXCRASH must remain independent of the debugger.

A production application can therefore generate a crash artifact without containing the full debugger.

---

# 3. Non-Goals

AXCRASH does not own:

- compiler optimization;
- debugger breakpoints;
- profiling;
- ordinary logging;
- application telemetry;
- OS process creation;
- executable loading;
- exception policy;
- security authorization;
- source editing;
- automatic source modification.

---

# 4. Crash Definition

A crash is an abnormal execution termination that requires diagnostic preservation.

Examples:

```text
invalid memory access
illegal instruction
divide/trap fault
stack exhaustion
explicit fatal panic
uncaught fatal runtime error
OS exception
fatal signal
abort
runtime invariant violation
```

Exact classification is platform-dependent.

---

# 5. Crash State Machine

```text
RUNNING
   │
   ▼
FAULT_DETECTED
   │
   ▼
CAPTURE
   │
   ├── capture failed ──► MINIMAL_CAPTURE
   │
   ▼
FINALIZE
   │
   ▼
ARTIFACT_READY
   │
   ├── local persistence
   └── optional remote submission
```

---

# 6. Crash Session

```text
CrashSession {
    id
    generation
    process
    fault
    state
    capture_policy
    start_timestamp
    completion_timestamp?
    artifact?
}
```

---

# 7. Crash Identity

Each crash receives:

```text
CrashId {
    session_id
    process_id
    timestamp
}
```

The artifact additionally contains a stable fingerprint.

---

# 8. Fault Model

```text
CrashFault {
    category
    code
    platform_code?
    address?
    instruction_pointer?
    access_type?
    access_address?
    thread_id
    task_id?
}
```

---

# 9. Fault Categories

Canonical categories:

```text
MEMORY_ACCESS
ILLEGAL_INSTRUCTION
ARITHMETIC_FAULT
STACK_FAILURE
PANIC
TRAP
ABORT
SIGNAL
OS_EXCEPTION
RUNTIME_FATAL
UNKNOWN
```

---

# 10. Memory Fault

Where the platform exposes sufficient information:

```text
access_type:
    READ
    WRITE
    EXECUTE
    UNKNOWN
```

and:

```text
fault_address
```

are captured.

---

# 11. Fault Address

The fault address is distinct from:

```text
instruction_pointer
```

Example:

```text
IP = instruction that faulted
FA = address involved in fault
```

Both must remain separately represented.

---

# 12. Register Capture

Crash capture records architecture-specific register state where available.

```text
RegisterState {
    architecture
    general[]
    instruction_pointer
    stack_pointer
    frame_pointer?
    flags?
    special[]
}
```

---

# 13. x86_64 Register Set

Where supported:

```text
RAX RBX RCX RDX
RSI RDI
RBP RSP
R8-R15
RIP
RFLAGS
```

plus relevant platform registers.

---

# 14. AArch64 Register Set

Where supported:

```text
X0-X30
SP
PC
PSTATE
```

plus relevant system/platform state exposed to user-space crash handling.

---

# 15. SIMD State

SIMD/vector register capture is optional according to policy.

Examples:

```text XMM/YMM/ZMM
NEON/V registers
```

---

# 16. Register Capture Failure

Unavailable registers must be represented as:

```text UNKNOWN
```

not zero-filled as though zero were the actual value.

---

# 17. Raw Register Preservation

The artifact should preserve a compact raw architecture-specific register block in addition to normalized fields when platform facilities permit.

This supports future analysis without changing the normalized schema.

---

# 18. Stack Capture

Crash capture attempts:

```text current stack
```

with a bounded byte limit.

Default crash capture must never attempt to dump unlimited memory.

---

# 19. Stack Unwinding

Preferred order:

```text unwind metadata
        ↓
frame pointers
        ↓
platform fallback
        ↓
current frame only
```

---

# 20. Unwind Quality

Every stack includes:

```text COMPLETE
PARTIAL
FAILED
CURRENT_FRAME_ONLY
UNKNOWN
```

---

# 21. No Fabricated Frames

If unwinding cannot continue, AXCRASH stops.

It must not infer additional frames from arbitrary memory patterns.

---

# 22. Crash Stack

```text CrashStack {
    thread_id
    frames[]
    quality
}
```

---

# 23. Frame Model

```text CrashFrame {
    frame_index
    instruction_address
    module_id?
    function_id?
    source_location?
    inline_chain[]
}
```

---

# 24. Source Mapping

AXCRASH uses compiler-generated debug metadata.

It must prefer exact metadata over heuristic source inference.

---

# 25. Build Identity

Every crash artifact records:

```text executable_build_id
compiler_build_id?
target
architecture
ABI
```

---

# 26. Debug Symbol Identity

Debug information is matched using:

```text BuildId
DebugArtifactId
ModuleId
```

rather than merely filename.

---

# 27. Symbol Mismatch

If symbols do not match:

```text SYMBOL_MISMATCH
```

is recorded.

AXCRASH must not silently symbolize against a different build.

---

# 28. Sidecar Debug Information

Axiom supports external debug artifacts:

```text executable
   +
.axdbg / platform-specific debug artifact
```

rather than requiring full debug data inside every executable.

---

# 29. Minimal Binary Debug Reference

A release binary may retain only enough metadata to identify its debug artifact.

This minimizes production binary size.

---

# 30. Debug Levels

Compiler/debug output may define:

```text DEBUG_NONE
DEBUG_MINIMAL
DEBUG_LINE
DEBUG_FULL
```

---

# 31. DEBUG_NONE

Crash artifact may still contain:

```text raw addresses
registers
module identities
```

but source-level symbolization may be unavailable.

---

# 32. DEBUG_LINE

Provides:

```text address → source file/line
```

where available.

---

# 33. DEBUG_FULL

Provides:

```text symbols
types
variables
inline frames
source mapping
ABI metadata
```

for postmortem analysis.

---

# 34. Panic Model

Axiom panic is represented explicitly:

```text PanicInfo {
    code
    message?
    source_location?
    function?
    task_id?
}
```

---

# 35. Panic Message

Messages are optional.

A panic capture must remain useful when no message exists.

---

# 36. Panic Payload

AXCRASH does not automatically serialize arbitrary user objects.

A caller may explicitly provide a bounded diagnostic payload.

---

# 37. Trap Model

```text TrapInfo {
    trap_code
    source_location?
    instruction_pointer
}
```

---

# 38. Runtime Fatal Error

AXRUNTIME may invoke:

```text crash_runtime_fatal()
```

with structured error information.

---

# 39. Explicit Application Crash

Applications may request:

```text crash_report_fatal()
```

for unrecoverable conditions.

This is distinct from ordinary error handling.

---

# 40. Error vs Crash

```text Result<T,E>
    ↓
recoverable error

panic/trap/fatal
    ↓
AXCRASH
```

This preserves Axiom's explicit error philosophy.

---

# 41. Crash Handler

Canonical:

```text CrashHandler {
    install()
    uninstall()
    on_fault()
    on_panic()
    on_trap()
    on_abort()
}
```

---

# 42. Handler Constraints

Crash-time code must assume:

```text heap may be corrupted
locks may be held
allocator may be broken
other threads may be inconsistent
runtime state may be partially destroyed
```

Therefore crash handling requires a restricted emergency path.

---

# 43. Emergency Allocator

AXCRASH may reserve a small emergency memory region at startup:

```text crash_reserve
```

used only when normal allocation is unsafe.

---

# 44. Crash Reserve

Reserve size is configurable but bounded.

Example profiles:

```text MINIMAL
STANDARD
EXTENDED
```

---

# 45. No Normal Allocator Dependency

The emergency crash path must not depend on the normal allocator being functional.

---

# 46. Crash-Time Lock Avoidance

Crash capture must avoid global locks where possible.

A deadlocked process cannot depend on the deadlocked lock to produce its crash artifact.

---

# 47. Crash Serialization

The emergency path writes:

```text bounded binary records
```

rather than constructing large object graphs.

---

# 48. Crash-Safe Writer

```text CrashWriter {
    begin()
    write_header()
    write_fault()
    write_registers()
    write_threads()
    write_stacks()
    write_modules()
    write_memory_regions()
    finalize()
}
```

---

# 49. Crash Artifact

Canonical:

```text .axcrash
```

is a structured crash evidence bundle.

---

# 50. Artifact Layout

```text
Header
CrashIdentity
Target
BuildIdentity
Fault
Registers
Threads
Tasks
Stacks
Modules
MemoryRegions
RuntimeState
PanicState
DebugReferences
EnvironmentMetadata
Diagnostics
Checksums
Footer
```

---

# 51. Crash Schema

```text
AXCRASH_SCHEMA_1
```

is independently versioned from:

```text
AXCRASH_ABI_1
```

---

# 52. Artifact Header

```text
CrashHeader {
    magic
    schema_version
    architecture
    format
    flags
    crash_id
}
```

---

# 53. Artifact Integrity

Every completed artifact contains:

```text checksum
```

and may optionally contain a cryptographic digest.

---

# 54. Partial Artifact

Crash handling can fail partway through.

The artifact then records:

```text PARTIAL_CAPTURE
```

and the sections successfully captured remain usable.

---

# 55. Crash Completeness

```text CrashQuality {
    registers
    current_stack
    other_threads
    modules
    memory_map
    runtime_state
    task_state
}
```

Each field reports:

```text COMPLETE
PARTIAL
UNAVAILABLE
FAILED
```

---

# 56. Thread Enumeration

Crash capture attempts to enumerate process threads.

Each:

```text CrashThread
```

contains:

```text thread_id
name?
state?
registers?
stack?
task_ids?
```

---

# 57. Faulting Thread

The faulting thread receives:

```text is_faulting_thread = true
```

exactly once.

---

# 58. Other Threads

Other threads may be:

```text RUNNING
BLOCKED
WAITING
UNKNOWN
```

at capture time.

Their state is inherently a snapshot and not assumed to be perfectly synchronized.

---

# 59. Thread Suspension

Platform crash handlers may suspend or otherwise snapshot threads where supported.

The strategy is backend-specific.

---

# 60. Suspension Failure

If another thread cannot be captured:

```text THREAD_CAPTURE_UNAVAILABLE
```

is recorded.

---

# 61. Deadlock Awareness

AXCRASH must not require all threads to cooperate before generating a minimal artifact.

---

# 62. Task Capture

AXTASK may expose crash-safe metadata:

```text TaskCrashState {
    task_id
    executor_id?
    state
    logical_stack?
}
```

---

# 63. Logical vs Physical Stack

For async tasks:

```text OS stack
```

and:

```text logical async/task continuation
```

are different.

AXCRASH may store both.

---

# 64. Async State

```text AsyncCrashState {
    task_id
    state
    continuation_id?
    await_site?
}
```

only where compiler/runtime metadata permits.

---

# 65. Compiler Async Metadata

AXCOMPILER may emit:

```text async state map
```

mapping state-machine locations to source-level async functions.

---

# 66. Closure State

If debug metadata exists, closure environments can be described.

AXCRASH must not dump arbitrary closure memory by default.

---

# 67. Generic Types

Monomorphized Axiom functions carry type metadata when full debug information is enabled.

This permits postmortem display of:

```text Foo<i32>
Foo<MyStruct>
```

without requiring runtime reflection.

---

# 68. Optimized-Out State

Variables may be:

```text AVAILABLE
PARTIALLY_AVAILABLE
OPTIMIZED_OUT
UNAVAILABLE
```

---

# 69. No Fabricated Variables

An unavailable variable must never be shown with a guessed value.

---

# 70. Memory Map

Crash artifact can contain:

```text MemoryRegion {
    base
    size
    permissions
    type
    module?
}
```

---

# 71. Memory Permissions

Canonical:

```text R
RW
RX
RWX
NONE
```

Actual platform permissions are preserved.

---

# 72. RWX Detection

If a crash artifact observes an RWX region, it records it.

AXCRASH does not automatically modify process memory during capture.

---

# 73. Memory Contents

Default:

```text no arbitrary memory dump
```

Only bounded diagnostic regions are captured.

---

# 74. Fault Memory Window

Optional policy may capture a small bounded window around:

```text fault_address
instruction_pointer
stack_pointer
```

when safe.

---

# 75. Security Reason

Memory contents may contain:

```text passwords
tokens
personal data
application secrets
```

therefore memory capture is opt-in.

---

# 76. Register Privacy

Registers can also contain sensitive values.

Crash policy may redact selected registers or disable full register capture.

---

# 77. Environment Metadata

Default crash metadata may include:

```text OS
architecture
application version
build ID
locale
target
```

but not arbitrary environment variables.

---

# 78. Environment Capture

Full environment capture requires explicit policy.

---

# 79. Command-Line Capture

Arguments may contain secrets.

Default policy should provide:

```text argument count
```

and optionally sanitized arguments rather than blindly storing every value.

---

# 80. Redaction

```text CrashRedactionPolicy {
    environment
    arguments
    memory
    registers
    paths
    custom_fields
}
```

---

# 81. File Paths

Source paths can expose local usernames/directories.

Path mapping/redaction may replace:

```text C:\Users\...\project
```

with:

```text <SOURCE_ROOT>
```

---

# 82. Source Remapping

Compiler/AXDOC/AXIDE metadata can provide:

```text source root mapping
```

for stable postmortem paths.

---

# 83. Module Model

```text CrashModule {
    module_id
    name
    path?
    build_id
    base_address
    size
    debug_id?
}
```

---

# 84. Dynamic Libraries

Loaded shared libraries are captured when possible.

This is essential for correct stack symbolization.

---

# 85. Module Load Order

Each module may include:

```text load_sequence
```

to distinguish repeated load/unload cycles.

---

# 86. Shared Library Unload

If supported, AXCRASH preserves module identity for addresses belonging to previously unloaded regions when capture metadata allows.

---

# 87. Loader Integration

AXLOADER provides module metadata to AXCRASH.

AXCRASH does not perform module loading.

---

# 88. Windows Backend

Windows crash capture maps platform exceptions into normalized:

```text CrashFault
RegisterState
MemoryRegion
CrashModule
```

while preserving the original platform exception code.

---

# 89. Windows Exception Context

Where available, preserve:

```text exception code
exception address
context/register state
exception parameters
```

with bounded size.

---

# 90. Linux Backend

Linux backend supports applicable:

```text signals
fault addresses
register state
ELF module information
thread state
core/minidump-like capture
```

through platform adapters.

---

# 91. Linux Signal Classification

Signals are normalized into categories while preserving:

```text signal number
signal code
fault address
```

when available.

---

# 92. macOS Backend

macOS crash capture preserves applicable:

```text Mach exception information
thread state
Mach-O module identity
```

through the platform backend.

---

# 93. iOS Boundary

iOS imposes platform restrictions.

AXCRASH provides the native crash-data abstraction while respecting platform crash-reporting and application lifecycle constraints.

---

# 94. Android Boundary

Android native crashes use:

```text AArch64/ELF64
```

where available, while platform-specific crash mechanisms remain behind the backend.

---

# 95. WASM Crash Model

WASM does not expose the same native process fault model.

AXCRASH therefore captures:

```text trap
module
function
instruction/source mapping
linear memory metadata
host-provided context
```

where available.

---

# 96. WASM Host Boundary

Host-level process crashes remain the host's responsibility.

Axiom captures only faults within the available WASM execution boundary.

---

# 97. Core Dump Compatibility

AXCRASH can import or reference platform core/minidump artifacts.

It does not require those formats as its canonical representation.

---

# 98. Native Core Import

Concept:

```text platform core
      ↓
AXCRASH decoder
      ↓
CrashModel
      ↓
.axcrash
```

---

# 99. Minidump Import

Windows minidump-like artifacts can be translated into the normalized model where information exists.

---

# 100. Lossless Principle

Platform-specific fields not represented in the normalized model may be preserved as:

```text platform_extension
```

rather than discarded.

---

# 101. Postmortem Mode

AXCRASH analysis does not require the original process to remain alive.

```text .axcrash
   ↓
AXCRASH reader
   ↓
CrashModel
   ↓
symbolization
   ↓
analysis
```

---

# 102. Postmortem Symbolization

The analyzer searches:

```text local symbol cache
debug artifact paths
build artifact store
configured symbol servers
```

according to explicit configuration.

---

# 103. Symbol Server

Optional remote symbol source:

```text SymbolServer
```

is read-only from AXCRASH's perspective.

---

# 104. Symbol Server Security

Remote symbol retrieval must use:

```text authenticated/secure transport
verified build identity
bounded downloads
```

and must not execute downloaded content.

---

# 105. Symbol Cache

Cache key:

```text DebugArtifactId
BuildId
Architecture
```

---

# 106. No Symbol Guessing

A filename match alone is insufficient for trusted symbolization.

---

# 107. Crash Fingerprint

A crash fingerprint is generated from stable structural information:

```text fault category
module
function
instruction offset
normalized stack
```

---

# 108. Fingerprint Stability

Absolute ASLR addresses must not form the primary fingerprint.

Use:

```text module-relative address
symbol identity
source identity
```

where available.

---

# 109. Fingerprint Versions

```text CrashFingerprintV1
```

is versioned.

Fingerprint algorithm changes do not silently change historical identities.

---

# 110. Deduplication

Crash database can group artifacts by fingerprint.

AXCRASH provides:

```text crash_fingerprint()
```

but the crash database policy decides grouping.

---

# 111. Similar but Distinct Crashes

Two crashes may share a coarse stack but differ in:

```text fault address
faulting instruction
build
```

Therefore deduplication must preserve multiple fingerprints/variants where needed.

---

# 112. Crash Variant

```text CrashVariant {
    fingerprint
    build_id
    first_seen
    last_seen
    count
}
```

---

# 113. Crash Database Boundary

A future AXCRASH database service may store:

```text artifacts
fingerprints
metadata
symbol references
```

but the core library remains usable without a server.

---

# 114. Local Crash Store

Applications can configure:

```text local crash directory
```

with:

```text retention
size limit
file count
```

---

# 115. Retention

Old artifacts are removed according to explicit policy.

No unlimited crash accumulation.

---

# 116. Disk Budget

```text max_artifact_size
max_total_storage
```

must be enforced.

---

# 117. Crash Queue

For remote reporting:

```text .axcrash
 ↓
local queue
 ↓
upload worker
```

---

# 118. Crash Upload

Upload must be:

```text asynchronous
authenticated
retryable
bounded
```

when possible.

---

# 119. Crash Capture Must Not Depend on Network

The crash handler must never wait for a network connection to produce the local artifact.

---

# 120. Remote Submission

Remote submission is optional.

The application continues with:

```text local artifact only
```

if remote reporting is disabled.

---

# 121. Consent/Policy

Applications must explicitly configure whether crash artifacts may leave the machine.

---

# 122. Artifact Encryption

Sensitive crash artifacts may be encrypted through:

```text AXCRYPTO
```

AXCRASH does not implement cryptography itself.

---

# 123. Artifact Signing

Integrity/authenticity may be provided through:

```text AXTRUST
AXCRYPTO
```

---

# 124. Remote Authorization

Server permissions distinguish:

```text SUBMIT_CRASH
READ_CRASH
DELETE_CRASH
READ_SYMBOLS
```

---

# 125. No Open Crash Endpoint

An unauthenticated crash-upload/debug endpoint is prohibited by default.

---

# 126. Crash Reporter Process

Architecture may use an external helper:

```text Application
    ↓
small crash handoff
    ↓
AXCrashReporter
    ↓
.axcrash
```

This is useful because the crashed process itself may be corrupted.

---

# 127. Reporter Boundary

The crash reporter may own:

```text final serialization
compression
upload
retention
```

while AXCRASH core owns:

```text crash evidence model
capture contract
```

---

# 128. Out-of-Process Capture

Where platform support allows, an external reporter can capture more reliable process state.

---

# 129. In-Process Minimal Capture

Every platform must define a minimal capture path that does not depend on the external reporter.

---

# 130. Crash Handoff Record

```text CrashHandoff {
    process_id
    crash_id
    fault_summary
    emergency_buffer
    executable_identity
}
```

---

# 131. Shared Memory Handoff

A preallocated shared memory region may be used between target and crash reporter.

---

# 132. Crash Handoff Integrity

The handoff contains:

```text magic
version
length
checksum
```

to prevent corrupted interpretation.

---

# 133. Crash During Crash Handling

If a second fatal fault occurs while capturing:

```text DOUBLE_FAULT
```

is recorded where possible.

The system then terminates capture immediately.

---

# 134. Recursion Guard

Crash handling maintains a minimal atomic guard:

```text crash_handler_active
```

to prevent recursive invocation.

---

# 135. Signal/Exception Safety

Platform handlers only invoke operations explicitly certified as safe for that backend.

---

# 136. No Logging Dependency

Crash capture cannot depend on ordinary:

```text logging
filesystem abstraction
network stack
```

being functional.

---

# 137. Emergency File Writer

Where necessary, the crash backend uses a minimal platform file-writing mechanism.

AXSTORAGE is not required for the emergency path.

---

# 138. Atomic Artifact Publication

The writer uses:

```text temporary artifact
        ↓
flush
        ↓
integrity finalize
        ↓
atomic publish
```

where the filesystem supports it.

---

# 139. Corrupt Artifact Prevention

An artifact is considered complete only after its final marker/checksum is successfully written.

---

# 140. Crash Artifact Reader

Canonical APIs:

```text crash_open()
crash_close()
crash_validate()
crash_metadata()
crash_fault()
crash_threads()
crash_registers()
crash_stacks()
crash_modules()
crash_memory_regions()
crash_runtime_state()
```

---

# 141. Crash Analysis

```text crash_symbolize()
crash_unwind()
crash_source_location()
crash_function()
crash_fingerprint()
crash_summary()
```

---

# 142. Crash Comparison

```text crash_compare()
crash_same_fingerprint()
crash_diff_stacks()
crash_diff_modules()
```

---

# 143. Crash Export

```text crash_export_json()
crash_export_text()
crash_export_report()
```

The binary `.axcrash` remains canonical.

---

# 144. Crash Capture API

```text crash_install()
crash_uninstall()
crash_set_policy()
crash_set_output()
crash_capture()
crash_capture_panic()
crash_capture_trap()
```

---

# 145. Crash Policy API

```text crash_policy_create()
crash_policy_set_stack_limit()
crash_policy_set_memory_limit()
crash_policy_set_register_capture()
crash_policy_set_environment_capture()
crash_policy_set_argument_capture()
crash_policy_set_redaction()
crash_policy_set_remote_upload()
```

---

# 146. Crash Module API

```text crash_register_module()
crash_unregister_module()
crash_module_lookup()
crash_module_list()
```

Runtime/module loaders may notify AXCRASH.

---

# 147. Crash Symbol API

```text crash_register_debug_artifact()
crash_unregister_debug_artifact()
crash_symbol_server_configure()
crash_symbol_cache_open()
crash_symbol_cache_clear()
```

---

# 148. Crash Reporter API

```text crash_reporter_start()
crash_reporter_stop()
crash_reporter_queue()
crash_reporter_retry()
crash_reporter_upload()
crash_reporter_status()
```

---

# 149. Crash Database API

```text crash_store_open()
crash_store_add()
crash_store_find()
crash_store_group()
crash_store_delete()
crash_store_prune()
```

---

# 150. Crash Session API

```text crash_session_create()
crash_session_state()
crash_session_finalize()
crash_session_artifact()
```

---

# 151. Crash Event Model

AXCRASH can expose:

```text CrashEvent {
    timestamp
    process_id
    thread_id
    category
    code
}
```

---

# 152. AXDEBUGGER Integration

Postmortem navigation:

```text AXCRASH
    ↓
faulting frame
    ↓
AXDEBUGGER source model
    ↓
AXCODEEDITOR
```

AXDEBUGGER remains responsible for live inspection.

---

# 153. AXPROFILER Integration

A crash may include a bounded reference to the active profiling session:

```text profile_session_id
```

if profiling was active.

AXCRASH does not embed an entire `.axprof` artifact automatically.

---

# 154. Profile Correlation

If available:

```text crash timestamp
profile session
build ID
process ID
thread ID
```

allow the profiler to be opened separately.

---

# 155. AXDIAGNOSTICS Integration

Diagnostic records can be attached as bounded structured metadata.

AXDIAGNOSTICS remains the authority for general diagnostic events.

---

# 156. AXOBSERVABILITY Integration

A crash event may be exported as telemetry:

```text crash fingerprint
build ID
timestamp
```

without uploading the entire crash artifact.

---

# 157. AXIDE Integration

AXIDE can open:

```text .axcrash
```

and present:

```text crash summary
faulting frame
stack
registers
modules
source
variables
threads
tasks
```

---

# 158. AXCODEEDITOR Integration

The editor can highlight:

```text faulting source line
inline frame
related stack frames
```

as presentation only.

---

# 159. AXDOC Integration

AXDOC can resolve:

```text function documentation
type documentation
API documentation
```

from the crash's semantic IDs.

---

# 160. Crash Summary

Canonical summary:

```text CrashSummary {
    category
    code
    fault_address?
    instruction_pointer
    faulting_module?
    faulting_function?
    source_location?
    thread_id
    task_id?
    fingerprint
}
```

---

# 161. Crash Severity

AXCRASH does not assign business severity.

It reports technical fault category.

Application systems may map that to their own severity.

---

# 162. Crash Reason vs Cause

The artifact records:

```text observed fault
```

not an automatically inferred root cause.

For example:

```text MEMORY_ACCESS
```

does not prove why the invalid access occurred.

---

# 163. Root-Cause Analysis

AXCRASH provides evidence.

AXDEBUGGER/AXIDE/AI analysis can reason over that evidence.

No subsystem may claim certainty where the captured evidence is insufficient.

---

# 164. AI Crash Context

```text AICrashContext {
    summary
    fault
    stack
    modules
    source
    registers_available
    variables_available
    quality
    build_identity
}
```

---

# 165. AI Provenance

Every AI-visible field identifies:

```text source = CRASH_ARTIFACT
source = DEBUG_METADATA
source = COMPILER_METADATA
source = PLATFORM_METADATA
```

---

# 166. AI Restrictions

AI must not fabricate:

```text variable values
stack frames
source locations
fault causes
```

when unavailable.

---

# 167. Automatic Fix Boundary

AXCRASH does not modify source code.

AXIDE may propose a patch based on crash evidence, but applying it requires an explicit action.

---

# 168. Crash Reproduction

A crash artifact may contain enough information to reproduce:

```text build
target
arguments policy
workload ID
```

but AXCRASH does not guarantee reproduction.

---

# 169. Deterministic Replay

If AXTEST or a future replay subsystem provides deterministic execution metadata, AXCRASH can reference:

```text replay_id
trace_id
```

but replay itself remains outside AXCRASH.

---

# 170. Crash Context ID

A runtime may propagate:

```text CrashContextId
```

through task execution.

This must remain a compact identifier.

---

# 171. Thread-Local Crash Context

When used, crash context should preferably be:

```text compact TLS state
```

with no heap allocation.

---

# 172. No-Debug Overhead

Release builds without crash support should contain no mandatory AXCRASH runtime.

---

# 173. Minimal Crash Runtime

When crash reporting is enabled, the runtime component must remain:

```text small
bounded
platform-specific
```

---

# 174. Link-Time Stripping

Unused crash functionality must be removed through:

```text dead-code elimination
section GC
LTO
```

where supported.

---

# 175. Static Linking

A static application should only include:

```text selected crash collectors
```

rather than a universal crash framework.

---

# 176. Dynamic Runtime

If AXRUNTIME is shared, AXCRASH may be loaded through it.

The ABI remains explicit.

---

# 177. Embedded/Freestanding

Freestanding targets may provide:

```text minimal crash record
```

without filesystem or OS crash reporting.

---

# 178. Embedded Artifact

A constrained target can write crash evidence into:

```text reserved storage
```

or expose it through a host debugging interface.

---

# 179. Kernel Boundary

AXCRASH is a user-space subsystem.

Kernel crash handling is outside its scope.

---

# 180. Security Boundary

AXCRASH must treat:

```text crash files
symbol files
remote crash data
```

as untrusted inputs.

---

# 181. Parser Security

The reader must defend against:

```text integer overflow
recursive structures
oversized sections
malformed indexes
compression bombs
path traversal
```

---

# 182. Path Safety

Debug/source paths must never be interpreted as filesystem commands.

---

# 183. Symbol Server Safety

Downloaded symbols are data.

AXCRASH must not execute:

```text binaries
scripts
plugins
```

as part of symbolization.

---

# 184. Crash Upload Safety

Uploads use explicit:

```text endpoint
identity
authorization
certificate/trust policy
```

---

# 185. Network Failure

Network failure must not corrupt the local artifact.

---

# 186. Retry Policy

Retries use:

```text bounded exponential backoff
max attempts
max queue size
```

---

# 187. Offline Mode

AXCRASH fully supports:

```text CAPTURE_ONLY
```

without network functionality.

---

# 188. Crash Store Encryption

Optional encryption can protect:

```text local crash queue
```

using AXCRYPTO.

---

# 189. Access Control

Local crash artifacts should follow platform file permissions.

---

# 190. Multi-User Systems

A crash store must not accidentally expose one user's crash memory or source paths to another user.

---

# 191. Crash Artifact Size

Default artifact should be small enough for practical local/remote use.

Large memory dumps are an explicitly separate profile.

---

# 192. Capture Profiles

```text CRASH_MINIMAL
CRASH_STANDARD
CRASH_FULL
CRASH_FORENSIC
```

---

# 193. Minimal Profile

Captures:

```text fault
faulting thread
registers
short stack
module identity
build identity
```

---

# 194. Standard Profile

Adds:

```text all thread stacks
module map
task metadata
runtime state
```

where available.

---

# 195. Full Profile

May include:

```text extended registers
larger stacks
selected memory windows
extended task state
```

---

# 196. Forensic Profile

May include larger diagnostic memory regions, but remains explicitly opt-in due privacy and storage cost.

---

# 197. Capture Configuration

```text CrashCapturePolicy {
    profile
    max_stack_bytes
    max_memory_bytes
    max_artifact_bytes
    capture_all_threads
    capture_tasks
    capture_registers
    capture_memory_windows
    capture_environment
    capture_arguments
    redact
}
```

---

# 198. Crash Artifact Index

The artifact should have indexes for:

```text thread_id
module_id
function_id
source location
```

to allow fast postmortem navigation.

---

# 199. Lazy Analysis

Opening a crash should not require loading:

```text all memory
all modules
all symbols
```

immediately.

---

# 200. Symbolization Cache

Postmortem symbolization results can be cached by:

```text crash_hash
debug_artifact_id
```

---

# 201. Crash Report Rendering

AXCRASH can render:

```text text
JSON
structured report
```

while AXIDE provides the graphical presentation.

---

# 202. Human Report

A concise report should contain:

```text application
build
target
fault
faulting location
thread
stack
modules
capture quality
```

---

# 203. JSON Report

JSON is intended for:

```text CI
issue trackers
automation
AI
```

not as canonical artifact storage.

---

# 204. CI Crash Handling

AXTEST can consume `.axcrash` artifacts from failing tests.

---

# 205. Test Crash Flow

```text AXTEST
   ↓
run test
   ↓
crash
   ↓
AXCRASH
   ↓
.axcrash
   ↓
AXTEST failure artifact
```

---

# 206. Crash Fuzzing

AXTEST fuzzing campaigns should preserve crash artifacts.

---

# 207. Crash Minimization

AXTEST may minimize the input that caused a crash.

AXCRASH only stores the resulting crash evidence and input identity.

---

# 208. Crash Regression Test

A known crash fingerprint can become a regression fixture.

---

# 209. Symbol Regression Tests

AXTEST must verify:

```text source location
inline frames
generic types
optimized-out values
```

against expected compiler metadata.

---

# 210. Platform Tests

Required test matrix:

```text Windows x86_64
Windows AArch64 where supported
Linux x86_64
Linux AArch64
macOS x86_64
macOS AArch64
Android AArch64
iOS AArch64/simulator where permitted
WASM32
```

---

# 211. Fault Injection

Test-only builds may intentionally generate:

```text controlled panic
controlled trap
controlled invalid operation
```

for capture validation.

These tests must remain isolated from production binaries.

---

# 212. Stack Test

Verify:

```text deep recursion
inlining
tail calls
frame-pointer omission
mixed Axiom/C stack
```

---

# 213. Async Crash Test

Verify crashes occurring:

```text inside task
after await
during task migration
inside nested async calls
```

---

# 214. Thread Crash Test

Verify:

```text faulting thread
many concurrent threads
thread creation/exit
```

---

# 215. Module Test

Verify:

```text main executable
static code
shared libraries
load/unload
```

---

# 216. Symbol Mismatch Test

Use intentionally wrong debug symbols and verify:

```text SYMBOL_MISMATCH
```

rather than false symbolization.

---

# 217. Corrupt Artifact Test

Fuzz:

```text header
chunks
indexes
register blocks
stack frames
module records
checksums
```

---

# 218. Resource Exhaustion

Test:

```text enormous thread count
deep stack
huge module list
oversized metadata
```

and verify bounded capture.

---

# 219. Crash Handler Recursion Test

Trigger a failure during crash handling and verify:

```text DOUBLE_FAULT
```

or safe minimal termination.

---

# 220. Disk Failure Test

Simulate:

```text full disk
permission denied
I/O error
```

and verify the process does not hang indefinitely.

---

# 221. Network Failure Test

Remote upload failure must leave:

```text valid local artifact
```

where storage permits.

---

# 222. Privacy Test

Verify disabled fields are absent:

```text environment
arguments
memory
```

rather than merely hidden from the UI.

---

# 223. Redaction Test

Configured sensitive fields must be redacted before remote submission.

---

# 224. Deterministic Serialization

Given identical crash model input:

```text serialized artifact
```

must have deterministic canonical ordering.

---

# 225. Crash Timestamp

Timestamps use:

```text monotonic
```

for ordering and optionally:

```text wall-clock
```

for human reporting.

---

# 226. Clock Failure

If wall-clock time is unavailable, crash identity remains valid using monotonic/process-local information.

---

# 227. Crash Sequence

A process may have multiple crash-reporting events over its lifetime only if it survives them; fatal crashes normally terminate the process.

Crash sequence IDs distinguish separate sessions/process runs.

---

# 228. Process Identity

Artifact records:

```text process_id
process_start_identity
```

where platform facilities permit.

---

# 229. PID Reuse

A bare OS PID must never be the sole identity across crash records.

---

# 230. Application Identity

```text ApplicationIdentity {
    name
    version?
    build_id
    package_id?
}
```

---

# 231. Target Identity

```text TargetIdentity {
    OS
    architecture
    ABI
    binary_format
}
```

---

# 232. Crash Metadata

```text CrashMetadata {
    application
    target
    build
    timestamp
    session
    capture_profile
    quality
}
```

---

# 233. Extension Metadata

Applications may attach bounded:

```text key/value diagnostic metadata
```

subject to redaction policy.

---

# 234. Metadata Limits

Each custom field must have:

```text max key length
max value length
max total metadata
```

---

# 235. Extension Namespace

Application metadata uses:

```text app.*
```

AXCRASH-reserved fields use:

```text ax.*
```

to prevent collisions.

---

# 236. Plugin Boundary

Crash decoders can have extension interfaces.

They must not be loaded automatically from an untrusted crash artifact.

---

# 237. Trusted Extensions

Optional debugger/profiler extensions are loaded only through explicit AXIDE configuration.

---

# 238. ABI Stability

`AXCRASH_ABI_1` covers:

```text capture API
reader API
policy API
analysis API
```

---

# 239. Schema Stability

`AXCRASH_SCHEMA_1` covers:

```text .axcrash
```

serialization.

---

# 240. Forward Compatibility

Readers must skip unknown optional sections.

Unknown mandatory sections produce:

```text UNSUPPORTED_SCHEMA_FEATURE
```

---

# 241. ABI Handles

Opaque handles:

```text CrashSessionHandle
CrashArtifactHandle
CrashThreadHandle
CrashFrameHandle
CrashModuleHandle
CrashSymbolHandle
CrashStoreHandle
```

---

# 242. Handle Safety

Every handle contains an internal generation.

Use-after-close returns:

```text CRASH_INVALID_HANDLE
```

---

# 243. Error Model

Canonical errors:

```text CRASH_INVALID_SESSION
CRASH_ALREADY_INSTALLED
CRASH_NOT_INSTALLED
CRASH_CAPTURE_FAILED
CRASH_PARTIAL
CRASH_DOUBLE_FAULT
CRASH_ARTIFACT_CORRUPT
CRASH_SCHEMA_UNSUPPORTED
CRASH_SYMBOL_MISMATCH
CRASH_SYMBOL_UNAVAILABLE
CRASH_PERMISSION_DENIED
CRASH_STORAGE_FULL
CRASH_IO_ERROR
CRASH_REMOTE_AUTH_FAILED
CRASH_REMOTE_UNAVAILABLE
CRASH_RESOURCE_LIMIT
CRASH_REDACTION_FAILED
```

---

# 244. Crash Summary API

```text crash_summary()
```

must be safe even when detailed sections cannot be parsed.

---

# 245. Minimal Reader

A diagnostic environment with no AXRUNTIME can still inspect:

```text .axcrash
```

using a standalone native reader.

---

# 246. Standalone Analyzer

Final Axiom toolchain should provide:

```text ax crash analyze file.axcrash
```

conceptually.

The CLI frontend remains an AXTOOLCHAIN/AXIDE integration concern.

---

# 247. Crash Symbolization CLI

Conceptually:

```text ax crash symbolize
```

uses configured symbol stores.

---

# 248. Crash Fingerprint CLI

Conceptually:

```text ax crash fingerprint
```

returns the stable fingerprint and variants.

---

# 249. Crash Export CLI

Conceptually:

```text ax crash export --json
```

exports structured evidence.

---

# 250. Crash Database CLI

Conceptually:

```text ax crash store
```

provides local artifact management.

---

# 251. Performance Architecture

Normal application execution must incur:

```text zero mandatory AXCRASH cost
```

when disabled.

---

# 252. Enabled Runtime Cost

When enabled, the runtime should primarily pay for:

```text handler registration
small crash context
module registration
optional task metadata
```

rather than continuously capturing expensive information.

---

# 253. Preallocated State

Crash-safe state should be allocated:

```text before application execution
```

where possible.

---

# 254. No Continuous Stack Capture

Stacks are captured only when a crash occurs.

---

# 255. No Continuous Memory Dump

Memory is not copied continuously.

---

# 256. No Continuous Network Traffic

Crash reporting generates network traffic only after an explicit capture/submission policy permits it.

---

# 257. Crash Capture Latency

The emergency capture path should be bounded.

It must not attempt unlimited analysis before process termination.

---

# 258. Deferred Analysis

Expensive work such as:

```text full symbolization
stack visualization
fingerprint database lookup
compression
upload
```

should occur after minimal evidence is safely persisted.

---

# 259. Crash Compression

`.axcrash` sections may be compressed.

Compression must be bounded and must not prevent creation of a minimal artifact.

---

# 260. Crash Artifact Streaming

Large artifacts may be written incrementally.

---

# 261. Memory-Mapped Analysis

Postmortem reader may mmap large artifacts for efficient random access.

---

# 262. Zero-Copy Reader

Fixed-layout tables can be accessed without copying where alignment and endian requirements permit.

---

# 263. Endianness

Artifact serialization defines a canonical byte order.

Platform-specific raw structures are tagged with architecture/endianness.

---

# 264. Cross-Platform Analysis

A crash captured on:

```text Linux AArch64
```

may be analyzed on:

```text Windows x86_64
```

provided matching debug artifacts exist.

---

# 265. Cross-Architecture Reader

The reader must not interpret target register blocks using host architecture assumptions.

---

# 266. Target Architecture Decoder

```text CrashArchitectureDecoder
```

selects:

```text x86_64
AArch64
WASM32
```

or future targets.

---

# 267. Source Encoding

All textual artifact metadata uses UTF-8.

---

# 268. Binary Safety

Raw registers, memory windows and platform extension records remain byte arrays.

---

# 269. Crash API — Core

```text
crash_install()
crash_uninstall()
crash_is_installed()
crash_set_policy()
crash_capture()
crash_state()
```

---

# 270. Crash API — Analysis

```text
crash_open()
crash_close()
crash_validate()
crash_summary()
crash_fault()
crash_threads()
crash_stacks()
crash_modules()
crash_memory_regions()
crash_symbolize()
crash_fingerprint()
```

---

# 271. Crash API — Symbol

```text
crash_symbols_open()
crash_symbols_add()
crash_symbols_lookup()
crash_symbols_match()
crash_symbols_clear_cache()
```

---

# 272. Crash API — Store

```text
crash_store_open()
crash_store_add()
crash_store_find()
crash_store_group()
crash_store_prune()
crash_store_remove()
```

---

# 273. Crash API — Remote

```text
crash_remote_configure()
crash_remote_authenticate()
crash_remote_submit()
crash_remote_status()
crash_remote_cancel()
```

---

# 274. Crash API — Integration

```text
crash_register_module()
crash_register_task()
crash_unregister_task()
crash_set_context()
crash_set_metadata()
```

---

# 275. Crash API — Reporter

```text
crash_reporter_start()
crash_reporter_stop()
crash_reporter_process()
crash_reporter_upload()
```

---

# 276. Crash API — Redaction

```text
crash_redaction_create()
crash_redaction_add_field()
crash_redaction_add_region()
crash_redaction_apply()
crash_redaction_validate()
```

---

# 277. AXCRASH Internal Layering

```text
                 AXCRASH
                    │
       ┌────────────┼────────────┐
       │            │            │
   Capture       Evidence     Analysis
       │            │            │
       ▼            ▼            ▼
  Platform      CrashModel   Symbolizer
  Backend                    Fingerprint
       │                         │
       └──────────┬──────────────┘
                  ▼
             Artifact Layer
                  │
           ┌──────┴──────┐
           ▼             ▼
        Local          Remote
        Store          Reporter
```

---

# 278. Platform Backend Interface

```text
CrashBackend {
    install()
    uninstall()
    capabilities()
    capture_fault()
    capture_registers()
    capture_threads()
    capture_modules()
    capture_memory_map()
    emergency_write()
}
```

---

# 279. Backend Independence

Platform-specific APIs must remain behind the backend.

Portable AXCRASH code must operate on normalized models.

---

# 280. Crash Capability Model

```text
CrashCapabilities {
    panic
    traps
    signals
    exceptions
    registers
    thread_capture
    module_capture
    memory_map
    core_import
    external_reporter
}
```

---

# 281. Capability Failure

Unsupported functionality returns:

```text unavailable
```

rather than silently substituting incorrect data.

---

# 282. AXCRASH Invariants

### CRASH-INV-01
Every completed crash artifact has a unique crash identity.

### CRASH-INV-02
Every crash artifact identifies the target build.

### CRASH-INV-03
Fault address and instruction address remain distinct.

### CRASH-INV-04
Unavailable register state is never represented as valid zero values.

### CRASH-INV-05
AXCRASH never fabricates stack frames.

### CRASH-INV-06
Stack quality is explicitly recorded.

### CRASH-INV-07
Symbol mismatch is explicitly reported.

### CRASH-INV-08
Debug symbols are matched by build/debug identity.

### CRASH-INV-09
Crash capture is bounded by resource limits.

### CRASH-INV-10
Crash capture does not require network availability.

### CRASH-INV-11
Crash capture does not require the normal allocator.

### CRASH-INV-12
Crash capture does not depend on ordinary logging.

### CRASH-INV-13
Crash handling contains recursion protection.

### CRASH-INV-14
Partial artifacts are explicitly marked.

### CRASH-INV-15
Completed artifacts contain integrity information.

### CRASH-INV-16
Arbitrary memory contents are not captured by default.

### CRASH-INV-17
Environment capture is policy-controlled.

### CRASH-INV-18
Argument capture is policy-controlled.

### CRASH-INV-19
Sensitive data can be redacted before remote submission.

### CRASH-INV-20
Remote crash submission is authenticated.

### CRASH-INV-21
Remote submission failure does not invalidate a valid local artifact.

### CRASH-INV-22
AXCRASH does not own debugger execution control.

### CRASH-INV-23
AXCRASH does not own performance profiling.

### CRASH-INV-24
AXCRASH does not own general telemetry.

### CRASH-INV-25
AXCRASH does not infer root cause beyond captured evidence.

### CRASH-INV-26
Optimized-out variables remain explicitly unavailable.

### CRASH-INV-27
Logical task identity remains distinct from OS thread identity.

### CRASH-INV-28
Async state is captured only when valid compiler/runtime metadata exists.

### CRASH-INV-29
Platform-specific fields can be preserved without corrupting the normalized model.

### CRASH-INV-30
Cross-architecture artifacts are interpreted using target architecture metadata.

### CRASH-INV-31
Malformed crash artifacts must not cause arbitrary code execution.

### CRASH-INV-32
Symbol servers are treated as data sources, not executable sources.

### CRASH-INV-33
Crash artifact readers enforce section and resource limits.

### CRASH-INV-34
Crash stores enforce retention and storage limits.

### CRASH-INV-35
Release builds contain no mandatory crash runtime when crash support is disabled.

### CRASH-INV-36
Crash analysis can operate independently of the crashed process.

### CRASH-INV-37
Crash fingerprints are versioned.

### CRASH-INV-38
AI-readable crash evidence preserves provenance and availability state.

### CRASH-INV-39
AXTEST can validate controlled crash capture and postmortem analysis.

### CRASH-INV-40
Every conforming AXCRASH implementation satisfies all mandatory invariants above.

---

# 283. Complete Crash Flow

```text
Application
    │
    ▼
Fault / Panic / Trap
    │
    ▼
AXCRASH Handler
    │
    ├── emergency state
    ├── fault
    ├── registers
    ├── faulting stack
    └── bounded thread state
    │
    ▼
Crash Handoff
    │
    ▼
Crash Reporter
    │
    ├── modules
    ├── task state
    ├── runtime metadata
    ├── integrity
    └── artifact finalization
    │
    ▼
.axcrash
    │
    ├── AXIDE
    ├── AXDEBUGGER
    ├── Symbol Store
    ├── Crash Store
    └── optional Remote Reporter
```

---

# 284. Complete Postmortem Flow

```text
.axcrash
   ↓
validate
   ↓
build identity
   ↓
debug symbol matching
   ↓
stack unwind
   ↓
source mapping
   ↓
fingerprint
   ↓
CrashSummary
   ↓
AXIDE / AI / CI
```

---

# 285. Release-Build Principle

Axiom now has a clear three-level distinction:

```text RELEASE
    │
    ├── no debugger runtime
    ├── no profiler runtime
    └── optional minimal crash support

DEVELOPMENT
    │
    ├── debugger
    ├── profiler
    └── full crash metadata

TEST
    │
    ├── crash injection
    ├── deterministic capture
    └── automated artifact verification
```

This prevents development tooling from becoming an unavoidable tax on production binaries.

---

# 286. Architectural Relationship

```text
                     AXCOMPILER
                         │
                debug/type metadata
                         │
                         ▼
AXBINARY ───────► AXLOADER ───────► Process
                                      │
                 ┌────────────────────┼───────────────────┐
                 │                    │                   │
             AXDEBUGGER          AXPROFILER          AXCRASH
                 │                    │                   │
            live state          performance          failure state
                 │                    │                   │
                 └────────────────────┼───────────────────┘
                                      │
                                    AXIDE
```

---

# 287. Critical Architectural Decision

AXCRASH **does not become a giant always-running diagnostic runtime**.

The final design is:

```text normal execution
       ↓
almost zero crash-related overhead

fault occurs
       ↓
small emergency path

artifact persisted
       ↓
expensive analysis deferred
```

This is particularly important for Axiom's original objective of native performance comparable to C/C++.

---

# 288. Definition of Done

AXCRASH 5.0 is complete when:

- `AXCRASH_ABI_1` is frozen.
- `AXCRASH_SCHEMA_1` is frozen.
- native crash handler infrastructure exists.
- panic/trap/fatal paths integrate with AXRUNTIME.
- Windows backend works.
- Linux backend works.
- macOS backend works.
- Android backend works within platform constraints.
- iOS backend works within platform constraints.
- WASM trap model works.
- register capture works.
- stack capture works.
- unwind metadata is consumed.
- Axiom debug metadata is consumed.
- DWARF/CodeView/Mach-O-compatible symbol sources can be consumed through adapters.
- build identity validation works.
- module tracking works.
- async/task state integration works.
- optimized-out variables are represented correctly.
- bounded memory capture works.
- redaction works.
- emergency capture does not require the normal allocator.
- partial artifacts work.
- `.axcrash` validation works.
- postmortem analysis works without the crashed process.
- symbol cache works.
- symbol mismatch detection works.
- crash fingerprinting works.
- local crash store works.
- remote reporting is optional and authenticated.
- remote failure does not destroy local evidence.
- AXIDE integration works.
- AXDEBUGGER integration works.
- AXPROFILER correlation works.
- AXTEST integration works.
- fuzzing of artifact readers passes.
- controlled fault-injection tests pass.
- resource exhaustion tests pass.
- privacy/redaction tests pass.
- release build without crash support contains no mandatory AXCRASH runtime.
- all `CRASH-INV-01..40` pass.
- cross-platform conformance passes.
- self-hosted Axiom can generate and analyze its own `.axcrash` artifacts.

**BOOTSTRAP-792 — AXCRASH 5.0 is frozen.**

---

# Next task

## BOOTSTRAP-793 — AXREPLAY

**Native Axiom Deterministic Execution Replay, Record/Replay Engine, Event Capture, Scheduler Replay, Time/Randomness Virtualization, Input/IO Determinism, Memory/Thread/Task State Correlation, Crash Replay, Reverse Debugging Foundation, Replay Artifact `.axreplay`, Replay ABI & Deterministic Debugging Runtime 5.0**