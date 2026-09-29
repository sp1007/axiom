Tiếp tục đúng chuỗi Axiom. Task kế tiếp là **BOOTSTRAP-602**.

:::writing{variant="document" id="58321" title="BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0"}

# BOOTSTRAP-602 — NATIVE APPLICATION LOGGING, DIAGNOSTICS, CRASH REPORTING & OBSERVABILITY RUNTIME 5.0

**Status:** Architecture Specification  
**Layer:** Bootstrap / Native Runtime  
**Depends on:** BOOTSTRAP-600, BOOTSTRAP-601  
**Target:** Native Axiom applications on Windows, Linux, macOS, iOS, Android, WASM  
**Primary goals:** deterministic diagnostics, near-zero disabled logging overhead, crash-resilient evidence capture, structured observability, zero mandatory external runtime dependency.

---

## 602.0 — Purpose

BOOTSTRAP-602 defines the native diagnostics subsystem used by an Axiom application to:

1. emit structured logs;
2. report warnings and errors;
3. capture diagnostic context;
4. trace important execution paths;
5. capture application crashes and fatal faults;
6. produce deterministic crash artifacts;
7. symbolize stack traces;
8. correlate crashes with application builds;
9. integrate with BOOTSTRAP-600 application state/checkpoints;
10. integrate with BOOTSTRAP-601 configuration/deployment identity;
11. provide local and externally exportable diagnostic data;
12. operate safely when the application is already partially corrupted.

The subsystem must remain useful without requiring:

- a third-party logging library;
- a third-party telemetry service;
- a managed runtime;
- a garbage collector;
- a background service;
- a network connection.

---

# 602.1 — Design Principles

The subsystem follows these principles:

### 602.1.1 Native first

Diagnostics are implemented directly by the Axiom runtime/toolchain.

### 602.1.2 Structured first

The canonical representation is structured data, not formatted strings.

### 602.1.3 Human readable second

Human-readable formatting is generated from structured events.

### 602.1.4 Disabled means almost free

A disabled log statement should ideally compile to no executable instructions.

### 602.1.5 Crash handling must not depend on normal application state

The crash handler cannot assume:

- heap integrity;
- allocator availability;
- locks are usable;
- scheduler is healthy;
- worker threads are alive;
- configuration is valid;
- normal logging infrastructure is operational.

### 602.1.6 Bounded resources

Every diagnostics component has explicit limits.

### 602.1.7 Deterministic identity

Every executable build has a diagnostic identity derived from:

- application identity;
- target;
- compiler;
- source/build metadata;
- executable identity.

### 602.1.8 Secret safety

Secrets from BOOTSTRAP-601 must never accidentally enter logs or crash artifacts.

### 602.1.9 Local operation

Logging and crash capture must work fully offline.

### 602.1.10 Export is optional

Uploading telemetry is outside the mandatory runtime core.

---

# 602.2 — Diagnostic Architecture

The runtime is divided into:

```text
Application
    │
    ├── Logger
    ├── Diagnostic API
    ├── Trace API
    └── Health API
          │
          ▼
    Diagnostic Event Core
          │
    ┌─────┼─────────┐
    ▼     ▼         ▼
 Ring   Logger     Trace
Buffer  Pipeline   Buffer
    │     │         │
    └─────┼─────────┘
          ▼
    Diagnostic Store
          │
    ┌─────┼───────────────┐
    ▼     ▼               ▼
 Console File       Crash Artifact
    │     │               │
    └─────┴───────┬───────┘
                    ▼
              Optional Export
```

Crash capture has a separate low-level path.

---

# 602.3 — Diagnostic Event

The fundamental unit is:

```axiom
struct DiagnosticEvent {
    timestamp: Instant
    monotonic: Duration
    severity: LogLevel
    category: Symbol
    event_id: u32

    process_id: u64
    thread_id: u64

    message: Optional<StringView>

    fields: DiagnosticFields

    trace_id: TraceId
    span_id: SpanId

    source: SourceLocation
}
```

Not every field must be physically present in every event.

The compiler/runtime may use compact representations.

---

# 602.4 — Severity

Axiom defines:

```axiom
enum LogLevel {
    trace
    debug
    info
    notice
    warning
    error
    critical
    fatal
}
```

Ordering:

```text
trace < debug < info < notice
      < warning < error < critical < fatal
```

Applications may configure a minimum active level.

---

# 602.5 — Compile-Time Log Elimination

Example:

```axiom
log.debug("cache lookup")
```

If debug logging is disabled at compilation:

```text
source
  ↓
compiler
  ↓
constant diagnostic policy
  ↓
statement eliminated
```

The resulting binary must not contain unnecessary formatting operations.

This is especially important for:

- embedded systems;
- mobile applications;
- high-frequency loops;
- graphics pipelines;
- networking;
- numerical kernels.

---

# 602.6 — Runtime Log Filtering

Runtime filtering remains available:

```axiom
logger.set_level(.info)
```

The runtime check occurs before expensive formatting.

Preferred execution:

```text
check level
    ↓
disabled → return
    ↓
construct event
    ↓
emit
```

Not:

```text
format message
    ↓
check level
```

---

# 602.7 — Lazy Diagnostic Arguments

Axiom supports lazy construction:

```axiom
log.debug("mesh", {
    vertices: || mesh.vertex_count(),
    triangles: || mesh.triangle_count()
})
```

The expressions are evaluated only when the event is accepted.

---

# 602.8 — Structured Fields

Fields are key/value pairs.

Example:

```axiom
log.info("connection.open", {
    host: host,
    port: port,
    protocol: "tcp"
})
```

Fields may contain:

- integers;
- floats;
- booleans;
- strings;
- byte sequences;
- enums;
- timestamps;
- durations;
- identifiers;
- arrays;
- bounded maps;
- nested diagnostic objects.

---

# 602.9 — Field Type Restrictions

Diagnostic fields must be serializable without arbitrary user code execution.

Custom objects are not automatically logged.

Instead:

```axiom
log.debug("user", {
    id: user.id,
    state: user.state
})
```

This prevents accidental:

```text
to_string()
```

execution from arbitrary application code.

---

# 602.10 — Message vs Event

A message is optional.

This is valid:

```axiom
log.error_event(
    id = ERR_DB_TIMEOUT,
    fields = {
        retry: retry_count
    }
)
```

The event can therefore be machine-readable without requiring English text.

---

# 602.11 — Event IDs

Production diagnostics should prefer stable event IDs.

Example:

```axiom
const ERR_DB_TIMEOUT: u32 = 0x120001
```

The compiler may generate IDs from symbolic declarations.

An event ID should remain stable across builds unless intentionally changed.

---

# 602.12 — Diagnostic Categories

Categories are hierarchical.

Example:

```text
app
app.network
app.network.http
app.database
runtime
runtime.memory
runtime.scheduler
runtime.graphics
compiler
```

Filtering can occur by prefix.

---

# 602.13 — Category Filtering

Example:

```axiom
logger.disable("runtime.graphics")
logger.enable("app.network")
```

Filtering precedence:

```text
global
    ↓
category
    ↓
event
```

The most specific matching rule wins.

---

# 602.14 — Logger

Core API:

```axiom
struct Logger {
    level: LogLevel

    log(
        level: LogLevel,
        category: Symbol,
        event: DiagnosticEventData
    )

    trace(...)
    debug(...)
    info(...)
    notice(...)
    warning(...)
    error(...)
    critical(...)
    fatal(...)
}
```

---

# 602.15 — Global Logger

Axiom may expose:

```axiom
runtime.logger()
```

However, the language must not require global mutable logger state for ordinary programs.

Dependency injection remains possible:

```axiom
fn run(logger: Logger)
```

---

# 602.16 — Logger Context

A logger can inherit contextual fields:

```axiom
let logger2 = logger.with_context({
    service: "payment",
    request_id: request.id
})
```

Then:

```axiom
logger2.info("payment.started")
```

automatically includes the inherited fields.

---

# 602.17 — Context Lifetime

Contexts must be explicit.

The runtime must not require hidden thread-local mutable state for correctness.

Thread-local context may be an optimization.

---

# 602.18 — Diagnostic Context

The runtime defines:

```axiom
struct DiagnosticContext {
    application_id: AppId
    build_id: BuildId
    process_id: u64
    thread_id: u64

    trace_id: TraceId
    span_id: SpanId

    config_fingerprint: Hash
    state_checkpoint_id: Optional<CheckpointId>
}
```

---

# 602.19 — Build Identity

Every release-capable executable should contain:

```text
AppId
BuildId
Target
CompilerVersion
RuntimeVersion
ABI
DebugSymbolId
```

This information is available to diagnostics.

---

# 602.20 — Configuration Fingerprint

BOOTSTRAP-601 configuration snapshots may expose:

```axiom
config.fingerprint()
```

Diagnostics may include the fingerprint.

Secret values must not be included.

---

# 602.21 — State Checkpoint Association

BOOTSTRAP-600 may expose:

```axiom
state.last_checkpoint_id()
```

A crash artifact can therefore contain:

```text
last known checkpoint
configuration fingerprint
build identity
crash context
```

without storing the entire application state.

---

# 602.22 — Trace IDs

The runtime defines:

```axiom
struct TraceId {
    high: u64
    low: u64
}
```

An invalid/zero value means no trace.

---

# 602.23 — Span IDs

```axiom
struct SpanId {
    value: u64
}
```

Span IDs identify individual operations.

---

# 602.24 — Trace Span

API:

```axiom
let span = trace.begin("database.query")

// work

span.end()
```

Scope-based form:

```axiom
with trace.span("database.query") {
    query()
}
```

---

# 602.25 — Automatic Span Closure

If a scope exits because of:

- normal return;
- error;
- panic;

the runtime must close the span.

This must not require garbage collection.

---

# 602.26 — Span Metadata

A span may contain:

```text
start
duration
name
category
thread
parent
trace
status
attributes
```

---

# 602.27 — Trace Sampling

Tracing supports:

```axiom
enum TraceSampling {
    off
    errors
    probability
    always
}
```

Production defaults should avoid unbounded tracing.

---

# 602.28 — Trace Buffer

Trace events may use a bounded ring buffer.

When full:

```text
drop oldest
```

or:

```text
drop newest
```

depending on policy.

The policy must be explicit.

---

# 602.29 — Logging Ring Buffer

A native crash-safe ring buffer is mandatory for fatal diagnostics.

Properties:

- preallocated;
- bounded;
- lock-minimized;
- allocation-free in crash mode;
- overwrite policy defined;
- checksum optional.

---

# 602.30 — Crash-Safe Logging

During a fatal fault, the runtime must not rely on ordinary logging.

Instead:

```text
normal logger
     X
     │
     ▼
crash recorder
     │
     ▼
preallocated emergency buffer
```

---

# 602.31 — Emergency Buffer

The runtime reserves a configurable region:

```axiom
CrashBuffer {
    address
    capacity
    write_position
}
```

The buffer must be initialized before application code begins.

---

# 602.32 — Crash Handler

The runtime installs platform-specific handlers.

Abstract interface:

```axiom
struct CrashHandler {
    install()
    uninstall()
}
```

Platform implementation maps to:

- Windows SEH/unhandled exception mechanisms;
- POSIX signal mechanisms;
- platform-specific mobile crash facilities;
- WASM host traps where available.

---

# 602.33 — Crash Handler Restrictions

Crash handlers must avoid:

- normal heap allocation;
- arbitrary locks;
- complex formatting;
- network access;
- arbitrary application callbacks;
- dynamic module loading;
- recursive logging.

---

# 602.34 — Crash Reentrancy

A crash handler must detect recursive invocation.

Example:

```text
crash
 ↓
handler
 ↓
handler crashes again
 ↓
emergency terminate
```

The second failure must not cause infinite recursion.

---

# 602.35 — Crash State Machine

```text
RUNNING
   │
   ▼
FAULT_DETECTED
   │
   ▼
CAPTURING
   │
   ├── success ──► WRITING
   │
   └── failure ──► EMERGENCY_TERMINATE
                         │
                         ▼
                       EXITED
```

---

# 602.36 — Crash Capture Stages

The crash handler attempts:

1. mark crash state;
2. identify fault;
3. identify thread;
4. capture registers;
5. capture stack;
6. capture module identities;
7. capture emergency logs;
8. capture diagnostic context;
9. capture state checkpoint identity;
10. capture configuration fingerprint;
11. write artifact;
12. flush if safely possible;
13. terminate or delegate according to platform policy.

---

# 602.37 — Fault Information

Crash information may contain:

```axiom
struct FaultInfo {
    kind: FaultKind
    code: u64
    address: u64
    thread_id: u64
}
```

---

# 602.38 — Fault Kind

Examples:

```axiom
enum FaultKind {
    access_violation
    illegal_instruction
    arithmetic_fault
    stack_overflow
    assertion
    explicit_panic
    abort
    unhandled_exception
    platform_fault
    unknown
}
```

---

# 602.39 — Register Capture

The crash artifact should capture architecture-relevant registers.

Examples:

```text
x86-64:
RAX RBX RCX RDX
RSI RDI RSP RBP
R8..R15
RIP
RFLAGS
```

ARM64 captures its corresponding architectural state.

The runtime must use architecture-specific implementations.

---

# 602.40 — Stack Capture

The runtime attempts to capture the current stack without requiring ordinary heap allocation.

The capture size is bounded.

Example default:

```text
maximum_frames = 256
```

---

# 602.41 — Other Thread State

Full thread suspension during a crash is optional.

The minimum mandatory artifact contains the crashing thread.

Best-effort capture of other threads may be enabled.

---

# 602.42 — Stack Safety

Stack walking must detect:

- invalid stack pointers;
- unmapped memory;
- frame loops;
- malformed unwind metadata;
- maximum depth.

---

# 602.43 — Symbolization

Runtime crash artifacts should store addresses plus module identity.

Symbolization may happen later.

This reduces crash-handler complexity.

---

# 602.44 — Debug Symbol Identity

Each executable/module should expose:

```text
DebugSymbolId
```

The ID allows external symbol files to be matched to crash artifacts.

---

# 602.45 — Source Location

Debug builds may associate:

```axiom
struct SourceLocation {
    file_id
    line
    column
    function_id
}
```

Release builds may omit source strings while retaining compact IDs.

---

# 602.46 — Symbol Server Independence

Axiom does not mandate a central symbol server.

Symbols may be stored:

```text
locally
CI artifacts
build archive
developer machine
private server
```

---

# 602.47 — Crash Artifact

Canonical artifact:

```text
.axcrash
```

The format is binary and versioned.

A human-readable projection:

```text
.axcrash.txt
```

may be generated later.

---

# 602.48 — Crash Artifact Header

Minimum:

```text
magic
format_version
architecture
platform
app_id
build_id
timestamp
crash_kind
```

---

# 602.49 — Crash Artifact Sections

Recommended sections:

```text
HEADER
PROCESS
FAULT
THREAD
REGISTERS
STACK
MODULES
LOG_RING
TRACE_RING
CONFIG_ID
STATE_ID
ENVIRONMENT
USER_CONTEXT
CHECKSUM
```

Each section is independently length-delimited.

---

# 602.50 — Forward Compatibility

Unknown sections must be safely skippable.

The parser must not assume a fixed section ordering.

---

# 602.51 — Crash Artifact Integrity

The artifact may contain:

```text
CRC
SHA-256
or equivalent integrity hash
```

Integrity is primarily for corruption detection.

It is not automatically an authenticity guarantee.

---

# 602.52 — Privacy

Crash artifacts must support a privacy policy.

Possible levels:

```axiom
enum DiagnosticPrivacy {
    minimal
    standard
    detailed
}
```

---

# 602.53 — Minimal Privacy Mode

May contain:

- build ID;
- platform;
- fault;
- registers;
- stack addresses;
- module IDs.

It should exclude application payload data.

---

# 602.54 — Standard Privacy Mode

Adds:

- selected logs;
- trace metadata;
- configuration fingerprint;
- state checkpoint identity.

Secrets remain excluded.

---

# 602.55 — Detailed Privacy Mode

May include explicitly whitelisted application diagnostic fields.

It must still enforce secret redaction.

---

# 602.56 — Secret Type Integration

BOOTSTRAP-601 defines:

```axiom
Secret<T>
```

The diagnostic system must recognize it as non-loggable.

This is a compile-time/runtime safety boundary.

---

# 602.57 — Secret Logging Rejection

This should be rejected:

```axiom
log.info("token", {
    token: secret_token
})
```

unless an explicit unsafe conversion exists.

The preferred behavior is compile-time rejection.

---

# 602.58 — Redaction

Explicit redaction:

```axiom
log.info("request", {
    authorization: redact(token)
})
```

produces:

```text
authorization = [REDACTED]
```

---

# 602.59 — Sensitive Field Annotation

Application structures may mark fields:

```axiom
struct Account {
    id: u64
    email: String
    password: secret String
}
```

Diagnostic serialization automatically excludes secret fields.

---

# 602.60 — Environment Capture

Crash artifacts may capture selected environment information.

Examples:

```text
OS
architecture
CPU count
memory size
application version
runtime version
locale
timezone
```

Arbitrary environment variables must not be captured by default.

---

# 602.61 — Environment Allowlist

Applications may explicitly declare:

```axiom
diagnostics.environment_allow(
    "APP_MODE"
)
```

Secrets and sensitive environment variables remain blocked.

---

# 602.62 — Command-Line Capture

Command-line arguments may contain secrets.

Therefore the default crash artifact stores:

```text
argument count
```

rather than raw arguments.

Explicit safe arguments may be registered.

---

# 602.63 — Configuration Capture

The diagnostic runtime records:

```text
config schema version
config fingerprint
active profile
```

It does not dump the complete resolved configuration by default.

---

# 602.64 — State Capture

BOOTSTRAP-600 state integration records:

```text
state store ID
last checkpoint ID
checkpoint timestamp
checkpoint status
```

It does not automatically serialize arbitrary application state during a crash.

---

# 602.65 — Panic

Axiom defines:

```axiom
panic("reason")
```

A panic is a controlled fatal diagnostic event.

---

# 602.66 — Panic Policy

Application policy may define:

```axiom
enum PanicPolicy {
    terminate
    crash_report
    recover
}
```

`recover` is allowed only where the language's control-flow semantics explicitly support it.

---

# 602.67 — Panic Payload

Panic payloads should be bounded.

Large arbitrary objects must not be automatically serialized.

---

# 602.68 — Assertions

Axiom supports:

```axiom
assert(condition)
```

and:

```axiom
debug_assert(condition)
```

`debug_assert` may be removed from release builds.

---

# 602.69 — Assertion Diagnostics

A failed assertion records:

```text
assertion ID
source location
condition identity
message if available
```

---

# 602.70 — Error vs Crash

Recoverable errors must not automatically produce crash artifacts.

Example:

```axiom
let result = file.read()
```

An ordinary I/O error is not a crash.

A crash artifact is reserved for abnormal process termination or explicit diagnostic capture.

---

# 602.71 — Explicit Diagnostic Snapshot

Applications may request:

```axiom
diagnostics.snapshot("user_report")
```

This creates a diagnostic package without terminating the process.

---

# 602.72 — Snapshot Safety

Snapshot generation must use normal runtime facilities.

Unlike crash capture, it may:

- allocate;
- format;
- serialize;
- compress;
- invoke application-safe callbacks.

---

# 602.73 — Diagnostic Snapshot Contents

Default:

```text
application identity
build identity
platform
configuration fingerprint
state checkpoint identity
recent logs
recent trace
thread information
health information
```

---

# 602.74 — Log Sinks

The runtime defines:

```axiom
trait LogSink {
    fn emit(event: DiagnosticEvent)
    fn flush()
    fn close()
}
```

---

# 602.75 — Built-In Sinks

Mandatory or platform-appropriate sinks:

```text
console
file
memory
debugger
system log
```

Not every platform needs every sink.

---

# 602.76 — Console Sink

Console output is human-readable by default.

Example:

```text
10:42:31 INFO  app.network
connection.open host=api.example.com port=443
```

---

# 602.77 — Structured Console Mode

Machine-readable output:

```text
JSON Lines
```

may be enabled.

---

# 602.78 — File Sink

File logging supports:

- append;
- rotation;
- bounded size;
- retention;
- flush policy;
- encoding.

UTF-8 is the default text encoding.

---

# 602.79 — Log Rotation

Example:

```axiom
LogRotation {
    max_file_size: 32MB
    max_files: 8
}
```

Rotation must be atomic where the platform permits.

---

# 602.80 — Crash During Rotation

If rotation is interrupted:

- old logs remain readable;
- the current log may be partially written;
- startup recovery must detect incomplete rotation.

---

# 602.81 — Async Logging

Optional asynchronous logging:

```text
application thread
      │
      ▼
bounded queue
      │
      ▼
logging worker
      │
      ▼
sink
```

---

# 602.82 — Async Logging Backpressure

Policies:

```axiom
enum LogBackpressure {
    drop
    block
    synchronous_fallback
}
```

Default should favor application availability over unbounded memory growth.

---

# 602.83 — Critical Logs

Critical/fatal events must have stronger delivery guarantees.

They should bypass ordinary queue limits where safely possible.

---

# 602.84 — Flush

API:

```axiom
logger.flush()
```

Flush guarantees depend on sink.

File sink may provide:

```text
buffer flush
OS write
durability flush
```

as separate levels.

---

# 602.85 — Durability Levels

```axiom
enum FlushMode {
    buffered
    flushed
    durable
}
```

`durable` may incur significant cost and must not be implicit for ordinary logging.

---

# 602.86 — Locking

The logger should minimize global locks.

Preferred architecture:

```text
thread-local encoding
      ↓
bounded queue/ring
      ↓
single writer per sink
```

where appropriate.

---

# 602.87 — Thread Safety

Logger APIs are thread-safe.

A custom sink must explicitly declare its concurrency contract.

---

# 602.88 — Reentrant Logging

Logging from inside a logger implementation must not recurse indefinitely.

The runtime detects reentrancy.

---

# 602.89 — Logging Allocation

High-performance paths should support allocation-free logging for primitive fields.

Example:

```axiom
log.info("packet", {
    id: packet.id,
    size: packet.size
})
```

should be representable without temporary heap allocation.

---

# 602.90 — Formatting

Formatting should occur only when required by a sink.

Canonical event storage remains structured.

---

# 602.91 — Binary Log Format

For high-volume logging, the runtime may store compact binary events.

Advantages:

- smaller size;
- lower formatting cost;
- deferred rendering;
- easier crash-safe capture.

---

# 602.92 — Event Schema

Each event schema may declare:

```axiom
event ConnectionOpened {
    id: 0x1001

    host: String
    port: u16
}
```

The compiler can generate compact encoders.

---

# 602.93 — Schema Evolution

Event schemas are versioned.

Readers must tolerate missing optional fields.

Renaming an event field should preserve compatibility metadata when possible.

---

# 602.94 — Diagnostic Dictionary

A build may contain or reference:

```text
event ID → category
event ID → field schema
function ID → symbol
source ID → source file
```

This dictionary enables compact release diagnostics.

---

# 602.95 — String Stripping

Release builds may strip verbose diagnostic strings.

Instead:

```text
event_id = 0x1201
```

is emitted.

A separate diagnostic dictionary reconstructs:

```text
database.timeout
```

---

# 602.96 — Binary Size

Diagnostics must support linker-level dead stripping.

Unused features such as:

- tracing;
- file sink;
- symbol metadata;
- JSON formatter;

should not increase the final executable unnecessarily.

---

# 602.97 — Feature Flags

Possible build flags:

```text
AXIOM_DIAGNOSTICS
AXIOM_LOGGING
AXIOM_TRACING
AXIOM_CRASH_REPORTING
AXIOM_DEBUG_SYMBOLS
AXIOM_DIAGNOSTIC_JSON
```

The exact build-system spelling is implementation-defined.

---

# 602.98 — Minimal Runtime

A minimal Axiom executable may contain only:

```text
panic handling
fatal crash capture
minimal emergency buffer
```

Everything else can be removed if unused.

---

# 602.99 — Diagnostics Profile

BOOTSTRAP-601 deployment profiles may select:

```text
minimal
development
production
diagnostic
```

Example:

```text
production:
    info+
    crash capture
    minimal tracing
```

---

# 602.100 — Development Profile

Development may enable:

- debug logs;
- source locations;
- assertions;
- detailed traces;
- debugger integration.

---

# 602.101 — Production Profile

Production defaults:

- bounded logs;
- warning/error diagnostics;
- crash capture;
- stable event IDs;
- low tracing overhead.

---

# 602.102 — Diagnostic Profile

A temporary diagnostic profile may enable:

- verbose logs;
- traces;
- extended snapshots.

It must still obey resource limits.

---

# 602.103 — Runtime Health

The subsystem exposes:

```axiom
struct DiagnosticHealth {
    events_written: u64
    events_dropped: u64
    bytes_written: u64
    sink_errors: u64
    crash_buffer_usage: u64
}
```

---

# 602.104 — Dropped Events

Dropped events must be observable.

Example:

```text
diagnostics.events_dropped = 152
```

The runtime should periodically emit a summary.

---

# 602.105 — Sink Failure

If a log sink fails:

```text
application must continue
```

unless the application explicitly configured logging as mandatory.

The logger must not become a single point of application failure.

---

# 602.106 — Disk Full

If disk logging reaches capacity:

```text
drop
rotate
disable sink
```

according to configured policy.

The application should not crash merely because diagnostics storage is full.

---

# 602.107 — Network Export

Network export is optional.

The core runtime must not require:

```text
internet
DNS
TLS service
remote logging vendor
```

---

# 602.108 — Export Interface

Optional API:

```axiom
trait DiagnosticExporter {
    fn export(package: DiagnosticPackage) -> Result
}
```

The exporter operates outside crash-handler critical paths.

---

# 602.109 — Retry Policy

Exports may use:

```text
bounded retry
exponential backoff
maximum queue size
expiration
```

---

# 602.110 — Offline Queue

If enabled:

```text
diagnostic package
      ↓
local queue
      ↓
future export
```

Queue size must be bounded.

---

# 602.111 — Compression

Diagnostic packages may use compression.

Compression must never be mandatory for crash capture.

---

# 602.112 — Encryption

Optional package encryption may be provided.

The core diagnostic system must not require an external key-management service.

---

# 602.113 — Crash Upload

Automatic crash upload is opt-in.

The runtime must never silently transmit arbitrary application data.

---

# 602.114 — User Consent

Applications may expose a user-controlled policy:

```axiom
CrashUploadPolicy {
    disabled
    ask
    enabled
}
```

---

# 602.115 — Crash Recovery Marker

After startup following a crash, the application may query:

```axiom
diagnostics.previous_exit()
```

Possible result:

```axiom
enum PreviousExit {
    normal
    crash
    forced
    unknown
}
```

---

# 602.116 — Previous Crash Artifact

The runtime may expose:

```axiom
diagnostics.previous_crash()
```

which returns metadata, not necessarily the complete artifact.

---

# 602.117 — Startup Recovery

On startup:

```text
detect incomplete crash artifact
      ↓
validate
      ↓
mark finalized
      ↓
make available
```

---

# 602.118 — Crash Loop Detection

The runtime may maintain a bounded crash-loop counter.

Example:

```text
application crashes repeatedly
       ↓
startup counter increases
       ↓
recovery policy activates
```

Recovery policy belongs primarily to BOOTSTRAP-600/601 and the application lifecycle layer.

---

# 602.119 — Crash Loop Diagnostic Event

Example:

```text
runtime.crash_loop.detected
```

contains:

```text
attempt count
last crash ID
build ID
```

---

# 602.120 — Assertion and Panic Integration

All fatal paths converge on a common diagnostic mechanism:

```text
assert failure ─┐
panic ──────────┤
fatal error ────┼──► fatal diagnostic path
native fault ───┤
abort ──────────┘
```

---

# 602.121 — Native Fault vs Axiom Panic

The diagnostic artifact distinguishes:

```text
AXIOM_PANIC
NATIVE_FAULT
ASSERTION
EXPLICIT_ABORT
```

---

# 602.122 — Fatal Exit Code

The runtime should generate a stable internal crash classification.

Operating-system exit codes may differ by platform.

---

# 602.123 — Platform Adapter

The core API remains platform-neutral.

Platform adapters implement:

```text
exception capture
signal capture
stack unwind
module enumeration
system logging
native dump integration
```

---

# 602.124 — Windows Adapter

Supports integration with native Windows exception facilities.

Crash artifacts should be able to coexist with native dump tooling.

---

# 602.125 — Linux Adapter

Supports:

- signals;
- native stack state;
- ELF module identity;
- core-dump-compatible diagnostics.

---

# 602.126 — macOS Adapter

Supports:

- native exception/signal mechanisms;
- Mach-O module identity;
- symbol/debug identity.

---

# 602.127 — iOS Adapter

The runtime must respect platform restrictions.

Crash collection must not depend on unrestricted process inspection.

Application-generated diagnostics may be stored locally and exported according to platform policy.

---

# 602.128 — Android Adapter

The runtime integrates with Android process/native crash facilities where available.

Native Axiom crash artifacts remain independently parseable.

---

# 602.129 — WASM Adapter

WASM has no universal native-process crash model.

The runtime maps traps and explicit panics into:

```text
DiagnosticFault
```

and delegates persistence to the host where required.

---

# 602.130 — Source Map / Debug Map

Axiom toolchains may generate:

```text
.axsym
```

or equivalent debug artifacts.

These map:

```text
machine address
    ↓
function
    ↓
source file
    ↓
line
```

---

# 602.131 — Reproducible Diagnostic Identity

Identical source/build inputs should produce identical diagnostic identities where reproducible-build mode is enabled.

---

# 602.132 — Non-Reproducible Builds

Build metadata such as timestamps may be excluded from identity computation when reproducibility is requested.

---

# 602.133 — Compiler Integration

The compiler emits metadata required for:

- event IDs;
- source locations;
- stack unwinding;
- function IDs;
- build identity.

---

# 602.134 — Linker Integration

The linker combines diagnostic metadata across:

```text
object files
static libraries
dynamic libraries
application
```

and preserves module identities.

---

# 602.135 — Library Diagnostics

A library must not assume that the host application uses the same logging policy.

Libraries should obtain a logger/context from the host.

---

# 602.136 — Library Event Namespace

Library events should use a namespace:

```text
vendor.library.component
```

or:

```text
org.project.component
```

without requiring a central logging service.

---

# 602.137 — Runtime Event Namespace

Axiom runtime events use:

```text
runtime.*
```

Compiler-generated events use:

```text
compiler.*
```

Application events use application-defined namespaces.

---

# 602.138 — Event Collision

Event IDs must be scoped by diagnostic namespace or generated through a linker-level allocation mechanism.

---

# 602.139 — User-Defined Diagnostic Types

Axiom permits:

```axiom
struct DiagnosticValue {
    ...
}
```

only when it implements a restricted diagnostic encoding trait.

The encoder must have explicit bounded behavior.

---

# 602.140 — No Arbitrary Display Execution

Logging an object must not invoke an arbitrary unbounded method.

The diagnostic encoder contract must define:

```text
maximum size
maximum recursion
maximum execution behavior
```

---

# 602.141 — Recursive Data

Diagnostic serialization detects cycles.

Example:

```text
A → B → A
```

must not recurse forever.

---

# 602.142 — Maximum Diagnostic Depth

Default:

```text
max_depth = 8
```

Configuration may change this within bounded limits.

---

# 602.143 — Maximum Event Size

Every event has a maximum encoded size.

Example:

```text
64 KiB
```

Events exceeding the limit are truncated or rejected according to policy.

---

# 602.144 — Truncation Metadata

Truncated events indicate:

```text
truncated = true
original_size = N
```

when known.

---

# 602.145 — Binary Data

Binary payloads must be bounded.

Large buffers should not be logged directly.

Instead:

```axiom
log.info("packet", {
    size: packet.len,
    hash: hash(packet)
})
```

---

# 602.146 — Diagnostic Hashing

A diagnostic helper may compute:

```axiom
diagnostic_hash(data)
```

to identify repeated payloads without storing the payload.

---

# 602.147 — Rate Limiting

High-frequency events may be rate-limited.

Example:

```axiom
logger.rate_limit(
    event = "network.retry",
    max_events = 100,
    interval = 1s
)
```

---

# 602.148 — Suppression Summary

Suppressed events should produce a summary:

```text
network.retry suppressed=2381
```

so filtering does not hide the fact that an abnormal volume occurred.

---

# 602.149 — Burst Protection

A logger must protect the application from event storms.

The diagnostic subsystem itself must not become an outage amplifier.

---

# 602.150 — Per-Category Budgets

Applications may define:

```text
network: 1 MB/min
database: 512 KB/min
graphics: 2 MB/min
```

---

# 602.151 — Global Diagnostic Budget

A global budget may cap:

```text
bytes
events
CPU time
memory
```

allocated to diagnostics.

---

# 602.152 — Diagnostic CPU Budget

The runtime should expose configuration for limiting expensive formatting/tracing.

---

# 602.153 — High-Frequency Path

For hot loops:

```axiom
if diagnostic.enabled(.trace) {
    ...
}
```

must allow the compiler to hoist or eliminate the check when possible.

---

# 602.154 — Compile-Time Category Elimination

If a category is disabled at compile time:

```axiom
log.trace("physics", ...)
```

can become zero instructions.

---

# 602.155 — Constant Propagation

Diagnostic configuration should be represented in compiler-visible constants where practical.

---

# 602.156 — Link-Time Elimination

Unused diagnostic sinks should be removed by linker dead-code elimination.

---

# 602.157 — No Hidden Global Initialization Requirement

Axiom diagnostics should use explicit runtime initialization.

The runtime may initialize mandatory crash facilities before application entry.

---

# 602.158 — Initialization Order

Startup:

```text
native process
    ↓
minimal runtime
    ↓
crash handler
    ↓
emergency buffer
    ↓
diagnostic core
    ↓
configuration
    ↓
application
```

---

# 602.159 — Shutdown Order

Shutdown:

```text
application
    ↓
flush logs
    ↓
flush traces
    ↓
close exporters
    ↓
close diagnostic store
```

The crash handler remains available until the process is actually terminating.

---

# 602.160 — Abrupt Exit

For:

```axiom
process.exit_now()
```

normal flushing is not guaranteed.

The API must document this explicitly.

---

# 602.161 — Graceful Exit

For normal shutdown:

```axiom
process.exit()
```

the runtime attempts configured flush operations.

---

# 602.162 — Diagnostic Clock

Events contain:

```text
wall-clock timestamp
monotonic timestamp
```

Wall-clock time is for humans.

Monotonic time is for duration ordering.

---

# 602.163 — Clock Failure

If wall-clock time is unavailable:

```text
timestamp = unknown
```

but monotonic diagnostic ordering remains available.

---

# 602.164 — Time Synchronization

The diagnostic subsystem does not assume the wall clock is synchronized.

Distributed systems must use trace IDs and monotonic local durations where appropriate.

---

# 602.165 — Thread Identity

Thread IDs are captured as native identifiers.

The runtime may additionally expose logical task IDs.

---

# 602.166 — Task Identity

For async execution:

```axiom
TaskId
```

may be associated with diagnostics.

This is especially useful when many tasks share one OS thread.

---

# 602.167 — Scheduler Integration

The scheduler may expose:

```text
task creation
task suspension
task resume
task completion
task failure
```

as trace events.

These events are optional.

---

# 602.168 — Deadlock Diagnostics

The runtime may provide a diagnostic snapshot of known synchronization state.

It must not attempt unsafe lock acquisition from a crash handler.

---

# 602.169 — Hang Detection

Optional watchdog:

```text
application heartbeat
       ↓
watchdog
       ↓
no progress
       ↓
diagnostic snapshot
```

This is not a mandatory crash mechanism.

---

# 602.170 — Watchdog Safety

The watchdog must be bounded and must not terminate healthy applications merely because they are intentionally idle.

---

# 602.171 — Health API

Applications may expose:

```axiom
trait HealthProvider {
    fn health() -> HealthStatus
}
```

---

# 602.172 — Health Status

```axiom
enum HealthStatus {
    healthy
    degraded
    unavailable
    unknown
}
```

---

# 602.173 — Diagnostic Health vs Application Health

These are distinct.

Diagnostic subsystem health answers:

```text
Can diagnostics function?
```

Application health answers:

```text
Is the application functioning?
```

---

# 602.174 — Diagnostic Self-Test

Optional:

```axiom
diagnostics.self_test()
```

checks:

- ring buffer;
- sinks;
- storage;
- symbol metadata;
- crash artifact directory.

---

# 602.175 — Self-Test Safety

Self-test must not intentionally trigger an actual process crash.

---

# 602.176 — Test Crash Capture

Development builds may expose a controlled test:

```axiom
diagnostics.test_crash()
```

It must be explicitly enabled and unavailable in normal production builds unless intentionally configured.

---

# 602.177 — Crash Artifact Naming

Recommended:

```text
<AppId>_<BuildId>_<Timestamp>_<CrashId>.axcrash
```

---

# 602.178 — Crash ID

Each crash receives a locally unique identifier.

It must not require network connectivity.

---

# 602.179 — UUID Dependency

The implementation may use UUID-like identifiers but the runtime must not require an external UUID library.

---

# 602.180 — Artifact Storage

Default location comes from BOOTSTRAP-601 deployment configuration.

The runtime must support platform-appropriate application data directories.

---

# 602.181 — Storage Security

Crash artifacts should use restrictive permissions where supported.

---

# 602.182 — Storage Quota

Diagnostic storage has a configurable quota.

Example:

```text
max_total = 128 MB
```

---

# 602.183 — Retention

Retention policy may be:

```text
count-based
size-based
age-based
```

---

# 602.184 — Artifact Corruption Recovery

At startup, incomplete artifacts are:

```text
detected
validated
marked incomplete
retained or deleted
```

according to retention policy.

---

# 602.185 — Partial Crash Artifact

A partial artifact is still useful.

The format therefore supports:

```text
complete = false
```

and independently parseable sections.

---

# 602.186 — Emergency Artifact Writer

The crash writer should use:

```text
preallocated buffers
direct/native file APIs
fixed-size metadata
bounded loops
```

where platform-safe.

---

# 602.187 — Crash Writer Failure

If file writing fails:

```text
attempt alternate location
```

then:

```text
attempt platform-native crash mechanism
```

then terminate.

---

# 602.188 — No Infinite Recovery

Crash reporting must never repeatedly attempt recovery after fatal corruption.

---

# 602.189 — Crash Handler Isolation

The application must not be able to accidentally disable mandatory crash capture through ordinary logger configuration.

---

# 602.190 — Diagnostic Permissions

Applications may disable optional diagnostics.

They must not be able to violate OS/platform security restrictions.

---

# 602.191 — User Data Policy

The runtime does not automatically inspect arbitrary application memory for crash reporting.

Only explicitly defined regions are captured.

---

# 602.192 — Memory Snapshot

Full process-memory dumps are optional and platform-controlled.

They are not part of the minimal `.axcrash` requirement.

---

# 602.193 — Large Memory Applications

Applications with huge memory footprints must not incur proportional diagnostic overhead during normal operation.

---

# 602.194 — Crash Capture Complexity

Target:

```text
O(number of captured frames
 + number of bounded metadata records)
```

No operation should scan the entire heap by default.

---

# 602.195 — Normal Logging Complexity

For accepted fixed-size primitive events:

```text
O(event_size)
```

For disabled events:

```text
O(1)
```

---

# 602.196 — Memory Requirements

Minimal runtime diagnostics should have bounded memory:

```text
emergency crash buffer
+
configured ring buffers
+
optional queues
```

No unbounded diagnostic memory structure is permitted.

---

# 602.197 — ABI Stability

Public diagnostic structures intended for native library interoperability must have explicit ABI versions.

---

# 602.198 — C ABI Interoperability

Axiom may expose a minimal C-compatible diagnostic ABI for interoperability.

This must not require a C runtime for Axiom applications.

---

# 602.199 — Native Callback ABI

Callbacks crossing diagnostic boundaries must declare:

```text
calling convention
threading contract
lifetime
error behavior
```

---

# 602.200 — Error Handling

Diagnostic APIs should return explicit errors where an operation can fail.

Example:

```axiom
let result = diagnostics.snapshot("support")
```

Possible errors:

```text
storage_unavailable
quota_exceeded
serialization_failed
permission_denied
busy
```

---

# 602.201 — Diagnostic API Must Not Panic

Ordinary diagnostic failures should not themselves trigger application panic.

Example:

```axiom
logger.flush()
```

must not recursively crash the application merely because disk I/O failed.

---

# 602.202 — Recursive Failure Protection

The diagnostic subsystem has a final emergency path:

```text
normal diagnostic
      ↓ failure
minimal diagnostic
      ↓ failure
raw termination
```

---

# 602.203 — Acceptance Criteria

BOOTSTRAP-602 is complete when the Axiom implementation can demonstrate:

### Logging

- structured logs;
- severity levels;
- category filtering;
- event IDs;
- lazy arguments;
- compile-time elimination;
- bounded events;
- thread-safe logging.

### Tracing

- trace IDs;
- spans;
- bounded trace buffers;
- sampling;
- async-task correlation.

### Crash handling

- native fault capture;
- panic capture;
- assertion capture;
- register capture;
- bounded stack capture;
- module identity;
- build identity;
- crash artifact generation.

### Security

- secret values cannot be logged accidentally;
- configuration secrets remain protected;
- environment capture is allowlisted;
- command-line secrets are not dumped by default.

### Resilience

- logger failure does not normally crash the application;
- disk-full behavior is bounded;
- crash handler does not depend on ordinary heap allocation;
- recursive crash handling terminates safely;
- partial artifacts remain parseable.

### Toolchain

- compiler emits diagnostic metadata;
- linker preserves diagnostic identities;
- symbols can be matched to crash artifacts;
- unused diagnostic components can be dead-stripped.

### Platform

At minimum, the architecture must support:

```text
Windows
Linux
macOS
iOS
Android
WASM
```

through platform adapters.

---

# 602.204 — Required Compiler/Runtime Components

Implementation should produce:

```text
axiom.diagnostics.core
axiom.diagnostics.logging
axiom.diagnostics.trace
axiom.diagnostics.crash
axiom.diagnostics.symbols
axiom.diagnostics.storage
axiom.diagnostics.export
```

These are logical components, not necessarily separate binaries.

---

# 602.205 — Required Tooling

The Axiom toolchain should provide:

```text
ax log
ax crash
ax symbolize
ax diagnose
ax dump
```

Possible operations:

```text
ax crash inspect file.axcrash
ax symbolize file.axcrash
ax diagnose build/
```

---

# 602.206 — `ax crash inspect`

Displays:

```text
application
build
platform
fault
thread
stack
modules
recent logs
trace
checkpoint
configuration fingerprint
```

---

# 602.207 — `ax symbolize`

Consumes:

```text
.axcrash
.axsym
```

and produces source-level stack information.

---

# 602.208 — `ax crash export`

Converts:

```text
.axcrash
```

to:

```text
JSON
text
diagnostic package
```

without changing the original artifact.

---

# 602.209 — `ax diagnose`

Can analyze:

- crash artifacts;
- logs;
- trace data;
- build metadata;
- symbol files.

It should remain a toolchain feature rather than part of the application runtime.

---

# 602.210 — AI-Friendly Diagnostics

Axiom diagnostic artifacts should be machine-readable.

The canonical structured representation must expose:

```text
stable IDs
schema versions
explicit types
source locations
build identity
causal relationships
```

This allows AI tooling to reason over failures without relying exclusively on human-formatted logs.

---

# 602.211 — Diagnostic Causality

Events may reference:

```text
parent event
trace
span
request
task
checkpoint
```

This enables reconstruction such as:

```text
request
  ↓
task
  ↓
database query
  ↓
timeout
  ↓
retry
  ↓
panic
  ↓
crash
```

---

# 602.212 — Failure Chain

The diagnostic runtime may assign:

```axiom
FailureId
```

to related failures.

Example:

```text
FailureId = F-1827
```

All related events can reference the same failure.

---

# 602.213 — Error Context

Axiom errors may optionally carry:

```axiom
struct ErrorContext {
    error_code
    source
    cause
    trace_id
    span_id
}
```

---

# 602.214 — Error Cause Chain

Errors may form:

```text
application error
    ↓
database error
    ↓
network error
    ↓
OS error
```

The chain must be bounded.

---

# 602.215 — Cause Depth

Default maximum:

```text
16
```

to prevent pathological recursive error chains.

---

# 602.216 — Diagnostic Serialization

Error chains can be serialized into crash artifacts and snapshots.

Secrets remain filtered.

---

# 602.217 — Runtime Version Compatibility

Diagnostic readers should support multiple artifact versions where practical.

The artifact format must explicitly identify its version.

---

# 602.218 — Schema Migration

Axiom tooling may migrate:

```text
.axcrash v1
```

to a newer logical representation without modifying the original artifact.

---

# 602.219 — Long-Term Preservation

Crash artifacts must be interpretable even if the original application is no longer installed.

Therefore the artifact must contain enough metadata to identify:

```text
format
platform
architecture
build
runtime
module identities
```

---

# 602.220 — No Mandatory Cloud

Axiom's diagnostics architecture is fully functional without:

```text
cloud
vendor account
telemetry server
internet
```

---

# 602.221 — No Mandatory Third-Party Runtime

The final native executable must not require an external logging or crash-reporting runtime merely to execute.

---

# 602.222 — Determinism

Diagnostic behavior must be deterministic with respect to:

- filtering;
- event schema;
- artifact encoding;
- retention policy.

Timestamps and runtime scheduling are naturally nondeterministic.

---

# 602.223 — Performance Target

The target for disabled logging:

```text
effectively zero runtime overhead
```

when compile-time elimination is possible.

For enabled primitive logging:

```text
bounded O(event_size)
```

with no mandatory heap allocation.

---

# 602.224 — Crash Performance

Crash capture must prioritize:

```text
safety > completeness > convenience
```

The runtime must prefer a partial valid crash artifact over risking recursive failure while attempting a perfect one.

---

# 602.225 — Relationship to BOOTSTRAP-600

BOOTSTRAP-600 owns:

```text
application state
session
checkpoint
recovery
crash-resilient state
```

BOOTSTRAP-602 only records diagnostic references to that state.

It must not become the state-management subsystem.

---

# 602.226 — Relationship to BOOTSTRAP-601

BOOTSTRAP-601 owns:

```text
configuration
profiles
environment
secrets
deployment identity
```

BOOTSTRAP-602 consumes safe identifiers from it.

It must not duplicate configuration resolution.

---

# 602.227 — Boundary Rule

The three subsystems therefore remain:

```text
600 = What state does the application have?
601 = How is the application configured/deployed?
602 = What happened while the application was running?
```

This separation is mandatory.

---

# 602.228 — Architectural Result

After BOOTSTRAP-602, a native Axiom application has a complete foundational observability path:

```text
             APPLICATION
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      STATE      CONFIG   DIAGNOSTICS
       600        601        602
        │          │          │
        └──────────┼──────────┘
                   ▼
             BUILD IDENTITY
                   │
                   ▼
             FAILURE EVIDENCE
                   │
        ┌──────────┼───────────┐
        ▼          ▼           ▼
      LOGS       TRACE       CRASH
        │          │           │
        └──────────┼───────────┘
                   ▼
             .AXCRASH / STORE
```

This creates the minimum native foundation required for an Axiom application to be diagnosable in production without depending on third-party infrastructure.

---

# 602.229 — Task Completion

**BOOTSTRAP-602 is complete.**

The specification now establishes:

- native structured logging;
- compile-time log elimination;
- runtime filtering;
- structured diagnostic events;
- trace/span infrastructure;
- crash-safe emergency buffers;
- native fault capture;
- panic/assertion diagnostics;
- stack/register/module capture;
- symbol identity;
- `.axcrash` artifact architecture;
- privacy and secret protection;
- configuration/state correlation;
- bounded logging and tracing;
- diagnostic snapshots;
- health/watchdog foundations;
- platform adapters;
- compiler/linker integration;
- AI-readable diagnostic metadata;
- offline-first operation;
- no mandatory third-party runtime dependency.

**Next task: `BOOTSTRAP-603 — NATIVE APPLICATION SECURITY, IDENTITY, CAPABILITY & TRUST RUNTIME 5.0`**
:::

BOOTSTRAP-602 đã nối đúng sau 601. Chuỗi tiếp theo là **BOOTSTRAP-603**, không cần thay đổi số thứ tự hay quay lại các task trước.