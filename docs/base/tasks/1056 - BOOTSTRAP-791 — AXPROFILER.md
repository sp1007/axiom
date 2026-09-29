# BOOTSTRAP-791 — AXPROFILER

**Native Axiom Profiler, CPU Sampling, Instrumentation, Hardware Counters, Allocation Profiling, Task/Async Profiling, Lock/Wait Analysis, Call-Tree Aggregation, Flame Graph Data Model, Timeline Profiling, Cross-Platform Performance Counters, Low-Overhead Production Profiling, Trace Capture, Profile Artifacts & Profiling ABI 5.0**

**Status:** FROZEN — 5.0  
**Namespace:** `AXPROFILER`  
**ABI:** `AXPROFILER_ABI_1`  
**Depends on:** `AXDEBUGGER`, `AXCOMPILER`, `AXABI`, `AXBINARY`, `AXLOADER`, `AXPROCESS`, `AXRUNTIME`, `AXTASK`, `AXASYNC`, `AXMEMORY`, `AXTIME`, `AXTEST`, `AXIDE`, `AXDOC`  
**Optional integrations:** `AXOBSERVABILITY`, `AXDIAGNOSTICS`, `AXCRASH`, `AXCODEEDITOR`, `AXGUI`

---

# 1. Purpose

AXPROFILER is the native Axiom performance-analysis subsystem.

Its purpose is to answer:

```text
Where is execution time spent?
Why is it spent there?
Which functions consume CPU?
Which tasks wait?
Where are allocations occurring?
Which locks cause contention?
How does execution evolve over time?
Which code paths scale poorly?
```

Architecture:

```text
                         APPLICATION
                              │
              ┌───────────────┼───────────────┐
              │               │               │
          CPU execution    Memory          Tasks/Async
              │               │               │
              ▼               ▼               ▼
         AXPROFILER     AXMEMORY/Runtime    AXTASK
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                       PROFILE ENGINE
                              │
                ┌─────────────┼─────────────┐
                │             │             │
             Samples      Events        Counters
                │             │             │
                └─────────────┼─────────────┘
                              ▼
                       Aggregation Engine
                              │
                 ┌────────────┼────────────┐
                 │            │            │
             Call Tree     Timeline    Statistics
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                        Profile Artifact
                              │
                    AXIDE / AXGUI / AI
```

---

# 2. Fundamental Boundary

AXDEBUGGER answers:

> **What is the target doing at this exact stopped moment?**

AXPROFILER answers:

> **What did the target spend time/resources doing over an interval?**

Therefore:

```text
AXDEBUGGER = state inspection
AXPROFILER = statistical/performance analysis
```

Neither subsystem replaces the other.

---

# 3. Non-Goals

AXPROFILER does not own:

- debugger breakpoints;
- source editing;
- general logging;
- production telemetry;
- crash reporting;
- executable loading;
- compiler optimization;
- memory allocation itself;
- scheduler implementation;
- hardware performance-counter configuration outside profiling.

---

# 4. Profiling Modes

Axiom defines:

```text
PROFILE_NONE
PROFILE_SAMPLE
PROFILE_INSTRUMENT
PROFILE_COUNTER
PROFILE_MEMORY
PROFILE_CONCURRENCY
PROFILE_TASK
PROFILE_TIMELINE
PROFILE_TRACE
PROFILE_COMBINED
```

The application chooses explicitly.

---

# 5. Default Philosophy

The default profiler must be:

```text
low overhead
sampling-first
opt-in
bounded
deterministic in artifact structure
platform-aware
```

Instrumentation is available when sampling cannot answer the required question.

---

# 6. Profiling Architecture

```text
Target
 │
 ├── CPU sampler
 ├── hardware counters
 ├── allocation hooks
 ├── task hooks
 ├── synchronization hooks
 └── explicit instrumentation
          │
          ▼
     Event Buffer
          │
          ▼
     Aggregation
          │
          ▼
      Profile IR
          │
          ├── call tree
          ├── timeline
          ├── counters
          ├── allocations
          ├── waits
          └── task analysis
          │
          ▼
      .axprof
```

---

# 7. Profile Session

Canonical model:

```text
ProfileSession {
    id
    generation
    target
    mode
    state
    start_time
    end_time?
    configuration
    capabilities
    collectors[]
    buffers[]
    artifact?
}
```

States:

```text
CREATED
ARMED
RUNNING
STOPPING
FINALIZING
COMPLETED
CANCELLED
FAILED
```

---

# 8. Session Generation

Every profile session owns:

```text
generation: u64
```

Any asynchronous collector or UI result carrying an obsolete generation is rejected.

---

# 9. Target Identity

Profile data must identify:

```text
build_id
target
architecture
ABI
compiler version
optimization level
profile configuration
```

This is required for meaningful comparison.

---

# 10. Profile Configuration

```text
ProfileConfig {
    mode
    duration?
    sampling_frequency?
    counters[]
    include_modules[]
    exclude_modules[]
    include_threads[]
    include_tasks[]
    memory_policy?
    synchronization_policy?
    stack_depth
    buffer_size
    compression
    output
}
```

---

# 11. Sampling Profiler

Sampling is the primary low-overhead profiler.

Concept:

```text
timer/hardware interrupt
        ↓
capture execution state
        ↓
instruction pointer
        ↓
stack
        ↓
symbol/source mapping
        ↓
sample
```

No application instrumentation is required.

---

# 12. Sample Model

```text
ProfileSample {
    timestamp
    process_id
    thread_id
    task_id?
    cpu_id?
    instruction_pointer
    stack[]
    state
}
```

---

# 13. Sampling Frequency

Configuration may specify:

```text
samples_per_second
```

Typical modes:

```text LOW
MEDIUM
HIGH
CUSTOM
```

The profiler must prevent unsafe frequencies that exceed backend/platform capabilities.

---

# 14. Sampling Overhead

Sampling must be designed around:

```text short interrupt path
minimal allocation
per-thread buffers
deferred symbolization
```

The hot path should not:

```text allocate
lock globally
perform symbol lookup
format strings
write files synchronously
```

---

# 15. Per-Thread Buffers

Each profiling thread receives:

```text
lock-free or low-contention ring buffer
```

Concept:

```text Thread
  ↓
Local SampleBuffer
  ↓
background drain
  ↓
aggregator
```

---

# 16. Buffer Overflow

If the buffer fills:

```text samples_dropped++
```

must be recorded.

The profiler must never pretend that dropped samples exist.

---

# 17. Sample Quality

Every sample has:

```text validity
capture_quality
stack_quality
symbolization_quality
```

Possible states:

```text COMPLETE
PARTIAL_STACK
UNKNOWN_SYMBOL
STACK_UNAVAILABLE
DROPPED
```

---

# 18. Stack Sampling

Preferred:

```text unwind metadata
```

Fallback:

```text frame pointers
```

Then:

```text architecture fallback
```

The profiler must never fabricate stack frames.

---

# 19. Stack Depth

Configurable:

```text max_stack_depth
```

A bounded default prevents pathological recursive stacks from exhausting buffers.

---

# 20. Call Tree

Samples are aggregated into:

```text CallTree
```

Example:

```text main
 ├── render
 │    ├── layout
 │    └── raster
 └── update
      ├── physics
      └── input
```

---

# 21. Call Tree Node

```text
ProfileCallNode {
    id
    parent_id
    function
    module
    source
    inclusive_samples
    exclusive_samples
    inclusive_time?
    exclusive_time?
    children[]
}
```

---

# 22. Inclusive Cost

A function's inclusive cost includes:

```text function itself
+
all descendant execution
```

---

# 23. Exclusive Cost

Exclusive cost measures execution attributed directly to the function.

For sampling:

```text exclusive sample
```

means the sampled stack's leaf frame is the function.

---

# 24. Statistical Nature

Sampling results are estimates.

AXPROFILER must display:

```text sample count
sampling interval
estimated duration
confidence/statistical metadata where available
```

rather than implying exact instruction-level accounting.

---

# 25. Time Attribution

Wall-clock time and CPU time are different.

Profiler distinguishes:

```text CPU_TIME
WALL_TIME
WAIT_TIME
```

---

# 26. CPU Time

CPU time measures time actually executing on a processor.

---

# 27. Wall Time

Wall time measures elapsed time.

A thread can have:

```text high wall time
low CPU time
```

because it spends time waiting.

---

# 28. Wait Time

Wait time may include:

```text lock wait
I/O wait
sleep
condition wait
channel wait
task suspension
```

where supported.

---

# 29. Timeline Model

```text ProfileTimeline {
    events[]
}
```

Events:

```text CPU_SAMPLE
TASK_START
TASK_END
TASK_WAIT
LOCK_ACQUIRE
LOCK_RELEASE
THREAD_START
THREAD_END
ALLOC
FREE
MODULE_LOAD
CUSTOM
```

---

# 30. Timeline Event

```text ProfileEvent {
    timestamp
    duration?
    process
    thread
    task?
    category
    name
    payload
}
```

---

# 31. Timestamp Source

AXPROFILER uses a monotonic clock.

Wall-clock time is optional metadata.

Ordering uses:

```text monotonic timestamp
sequence
```

not local wall-clock changes.

---

# 32. Hardware Performance Counters

Optional collector:

```text HardwareCounterCollector
```

may expose:

```text cycles
instructions
branches
branch_misses
cache_references
cache_misses
frontend_stalls
backend_stalls
```

depending on CPU.

---

# 33. Counter Capability Discovery

```text profile_counter_list()
profile_counter_describe()
profile_counter_supported()
```

The profiler must never assume every CPU supports every event.

---

# 34. Counter Multiplexing

When hardware provides fewer counters than requested:

```text counter multiplexing
```

may divide measurement periods.

Results must identify multiplexing.

---

# 35. Counter Quality

```text CounterResult {
    value
    enabled_time
    running_time
    scaled?
    precision
}
```

If scaling was required, it is explicitly recorded.

---

# 36. CPU Architecture

Baseline support:

```text x86_64
AArch64
```

Future architectures use backend adapters.

---

# 37. CPU Frequency

Profiler must not infer CPU frequency from wall-clock samples unless the backend explicitly supplies reliable counter information.

---

# 38. Branch Profiling

Where available:

```text branches
branch misses
```

can identify branch-heavy functions.

---

# 39. Cache Profiling

Optional counters:

```text L1
L2
LLC
load/store
cache misses
```

must be represented as backend-provided metrics.

---

# 40. Memory Profiling

AXPROFILER memory mode measures:

```text allocations
frees
allocation sizes
allocation sites
lifetimes
live bytes
peak bytes
```

---

# 41. Allocation Event

```text AllocationEvent {
    timestamp
    thread_id
    task_id?
    address
    size
    allocation_site
    allocator_id
}
```

---

# 42. Free Event

```text FreeEvent {
    timestamp
    thread_id
    address
    allocator_id
}
```

---

# 43. Allocation Site

Canonical identity:

```text AllocationSite {
    function
    source_location
    call_stack
}
```

---

# 44. Allocation Statistics

```text AllocationStats {
    allocation_count
    free_count
    total_allocated
    total_freed
    live_count
    live_bytes
    peak_live_bytes
}
```

---

# 45. Allocation Overhead

Memory profiling must not always impose hooks on every allocation.

Profiles may choose:

```text SAMPLE_ALLOCATIONS
FULL_ALLOCATIONS
AGGREGATED_ALLOCATIONS
```

---

# 46. Allocation Sampling

For very high allocation rates:

```text sample 1/N allocations
```

is allowed.

Sampling ratio must be stored in the artifact.

---

# 47. Memory Lifetime

If allocation/free events are complete:

```text lifetime = free_timestamp - allocation_timestamp
```

If not, lifetime is:

```text UNKNOWN
```

for allocations surviving the capture.

---

# 48. Leak Analysis Boundary

AXPROFILER can report:

```text allocations not freed at capture end
```

but this is not automatically proof of a memory leak.

Application lifetime may legitimately retain allocations.

---

# 49. Fragmentation Analysis

AXPROFILER may consume allocator metadata to estimate:

```text free space
live blocks
size classes
fragmentation
```

but AXMEMORY remains allocator authority.

---

# 50. Task Profiling

AXTASK exposes optional profiling events:

```text task_created
task_started
task_suspended
task_resumed
task_completed
task_cancelled
task_failed
```

---

# 51. Task Event

```text TaskProfileEvent {
    timestamp
    task_id
    executor
    thread_id?
    state
}
```

---

# 52. Async Profiling

Axiom async execution must be analyzed as:

```text logical task lifetime
```

separate from:

```text OS thread lifetime
```

---

# 53. Task CPU Attribution

Profiler may aggregate:

```text CPU time by task
```

even when a task migrates:

```text Thread 2 → Thread 7
```

---

# 54. Task Wait Attribution

The profiler distinguishes:

```text RUNNING
READY
WAITING
SUSPENDED
```

so idle/waiting tasks do not appear as CPU consumers.

---

# 55. Executor Profiling

```text ExecutorProfile {
    executor_id
    worker_threads
    runnable_tasks
    queue_depth
    utilization
}
```

where AXTASK exposes the information.

---

# 56. Scheduler Profiling Boundary

AXPROFILER observes scheduling.

It does not implement:

```text scheduling
work stealing
task queues
```

Those belong to AXTASK.

---

# 57. Lock Profiling

Optional synchronization collector:

```text lock_acquire
lock_release
lock_wait
```

---

# 58. Lock Event

```text LockProfileEvent {
    timestamp
    duration?
    thread_id
    task_id?
    lock_id
    operation
    owner?
}
```

---

# 59. Lock Contention

Aggregate:

```text acquisition_count
wait_count
total_wait
max_wait
average_wait
contention_rate
```

---

# 60. Wait Graph

Profiler can construct:

```text Thread A → Lock X
Thread B → Lock X
Thread C → Lock Y
```

to identify contention.

---

# 61. Deadlock Boundary

AXPROFILER may expose wait cycles, but deadlock diagnosis remains observational.

AXDEBUGGER can use the same data for interactive inspection.

---

# 62. I/O Profiling

Optional integration may capture:

```text file I/O
network I/O
device I/O
```

but actual subsystem ownership remains:

```text AXSTORAGE
AXNETWORK
```

---

# 63. System Call Profiling

Platform backends may expose:

```text syscall count
duration
failure
```

as optional events.

---

# 64. Function Instrumentation

Compiler can optionally emit:

```text function_enter
function_exit
```

hooks.

Instrumentation is explicitly enabled.

---

# 65. Instrumentation Overhead

The compiler may optimize instrumentation through:

```text inline fast path
thread-local buffers
batching
sampling
```

---

# 66. Instrumentation ABI

Optional:

```text AXPROFILE_HOOKS_ABI_1
```

is separate from:

```text AXPROFILER_ABI_1
```

so normal runtime ABI remains small.

---

# 67. Function IDs

Compiler assigns:

```text FunctionId
```

to functions.

Profiler artifacts prefer:

```text FunctionId
```

over textual names.

---

# 68. Symbolization

Profiling should collect raw addresses first:

```text address
```

then symbolize asynchronously:

```text address
 ↓
module
 ↓
function
 ↓
source
```

---

# 69. Why Deferred Symbolization

This prevents the hot profiling path from performing:

```text hash lookup
string formatting
debug artifact parsing
filesystem access
```

---

# 70. Symbolization Cache

Cache:

```text module build_id
+
address range
```

to:

```text symbol/source
```

---

# 71. Unresolved Symbols

Valid result:

```text UNKNOWN_SYMBOL
```

rather than guessed names.

---

# 72. Mixed Native/Foreign Profiling

Call stacks may contain:

```text Axiom
C
system runtime
kernel boundary
```

Language identity is retained.

---

# 73. Profile Module

```text ProfileModule {
    module_id
    path
    build_id
    load_address
    size
    symbol_identity
}
```

---

# 74. Dynamic Modules

Module load/unload events update profiling identity.

Addresses are always interpreted relative to the correct module generation.

---

# 75. JIT Profiling Boundary

If Axiom supports JIT execution later:

```text register code region
register symbols
register source map
```

can be integrated.

---

# 76. CPU Affinity

Samples may include:

```text cpu_id
```

when available.

This enables analysis of:

```text migration
NUMA behavior
CPU imbalance
```

without requiring affinity changes.

---

# 77. NUMA Profiling

Future/optional backend may expose:

```text NUMA node
memory locality
remote access
```

AXPROFILER does not change process affinity merely to collect data.

---

# 78. Thread Profile

```text ThreadProfile {
    thread_id
    name
    cpu_time
    wall_time
    sample_count
    wait_time
}
```

---

# 79. Thread Utilization

Concept:

```text utilization =
CPU_TIME / WALL_TIME
```

for a thread over a defined interval.

---

# 80. Process Profile

```text ProcessProfile {
    process_id
    cpu_time
    wall_time
    threads[]
    tasks[]
    modules[]
}
```

---

# 81. Multi-Process Profiling

A profile session can include:

```text parent
 ├── worker
 └── helper
```

with explicit process identity.

---

# 82. Profile Filtering

Filters may include:

```text process
thread
task
module
function
source file
category
```

Filtering occurs after collection where possible.

---

# 83. Include/Exclude Rules

Example:

```text include AX application
exclude system libraries
```

must not alter underlying samples unless explicitly configured as a collection filter.

---

# 84. Aggregation

Raw events are transformed into:

```text ProfileIR
```

containing:

```text call tree
timeline
counters
allocation statistics
task statistics
lock statistics
```

---

# 85. ProfileIR

Canonical:

```text ProfileIR {
    metadata
    modules[]
    functions[]
    threads[]
    tasks[]
    samples[]
    events[]
    call_tree
    counters[]
    allocations?
    synchronization?
    timeline?
}
```

---

# 86. Aggregation Determinism

Given identical raw events and aggregation configuration:

```text ProfileIR
```

must have deterministic ordering.

---

# 87. Event Ordering

Every raw event receives:

```text sequence: u64
```

in addition to timestamp.

Sequence is authoritative when timestamps collide.

---

# 88. Sampling Jitter

Sampling intervals may intentionally vary to avoid synchronization artifacts.

The actual timestamp of each sample is stored.

---

# 89. Sampling Bias

Profiler metadata records:

```text sampling mode
frequency
jitter policy
dropped samples
```

so users understand limitations.

---

# 90. Flame Graph Data

AXPROFILER produces flame-graph-compatible hierarchical data.

Canonical structure:

```text FlameNode {
    function
    module
    value
    children[]
}
```

---

# 91. Flame Graph Value

Value may represent:

```text samples
CPU time
wall time
allocation bytes
allocation count
wait time
```

The metric is explicitly stored.

---

# 92. Timeline Visualization Data

AXPROFILER provides:

```text TimelineTrack {
    id
    name
    category
    events[]
}
```

AXGUI decides how it is rendered.

---

# 93. No UI Ownership

AXPROFILER does not own:

```text flame graph widget
timeline widget
charts
zoom UI
```

It provides semantic profile data.

---

# 94. AXIDE Integration

AXIDE may provide:

```text CPU profile
Memory profile
Concurrency profile
Timeline
Counters
Call tree
```

through AXPROFILER.

---

# 95. AXCODEEDITOR Integration

Profiler can annotate source:

```text hot function
hot line
allocation-heavy line
contention-heavy line
```

These are presentation overlays.

---

# 96. AXDOC Integration

Profiler can resolve:

```text FunctionId
TypeId
ModuleId
```

to documentation.

---

# 97. AXDEBUGGER Integration

Debugger can navigate:

```text profile hotspot
     ↓
source location
     ↓
AXDEBUGGER
     ↓
breakpoint / inspection
```

but profiler remains responsible for measurement.

---

# 98. AXOBSERVABILITY Integration

AXPROFILER may export aggregate performance metrics.

It must not become the production telemetry system.

---

# 99. Profile Comparison

Profiles can be compared:

```text Profile A
vs
Profile B
```

by:

```text build ID
function identity
metric
configuration
```

---

# 100. Comparison Metrics

Examples:

```text sample delta
CPU-time delta
allocation delta
wait-time delta
counter delta
```

---

# 101. Comparison Validity

Comparisons must identify incompatible conditions:

```text different target
different CPU
different compiler
different optimization
different sampling frequency
different workload
```

The tool should not silently present them as equivalent.

---

# 102. Benchmark Integration

AXPROFILER can consume AXTEST benchmark runs.

Canonical:

```text BenchmarkProfile {
    benchmark_id
    iteration
    profile_session
}
```

---

# 103. Benchmark Statistics

Support:

```text min
max
mean
median
percentiles
standard deviation
sample count
```

---

# 104. Benchmark vs Profile

AXTEST measures:

```text benchmark performance
```

AXPROFILER explains:

```text where performance was spent
```

---

# 105. Statistical Metadata

Every profile stores:

```text sample_count
duration
sampling_period
dropped_events
counter_scaling
```

where applicable.

---

# 106. Production Profiling

AXPROFILER may operate in production with:

```text low-rate sampling
remote capture
bounded buffers
explicit authorization
```

No debugger attachment is required.

---

# 107. Production Safety

Production profiling must avoid:

```text arbitrary code execution
unbounded memory
unbounded trace files
automatic remote exposure
```

---

# 108. Remote Profiling

Architecture:

```text Application
   ↓
AXPROFILER Agent
   ↓
authenticated transport
   ↓
AXPROFILER Client
```

Remote collection requires authentication and authorization.

---

# 109. Remote Profile Commands

Supported:

```text start
stop
pause
resume
configure
snapshot
download artifact
```

---

# 110. Remote Authentication

No anonymous profiler endpoint.

Capabilities must distinguish:

```text READ_PROFILE
START_PROFILE
STOP_PROFILE
CONFIGURE_PROFILE
DOWNLOAD_ARTIFACT
```

---

# 111. Profile Artifact

Canonical file:

```text .axprof
```

---

# 112. `.axprof` Structure

```text Header
ProfileIdentity
Target
Configuration
Modules
Functions
Threads
Tasks
RawSamples
Events
CallTree
Counters
Allocations
Synchronization
Timeline
Statistics
Indexes
Metadata
```

---

# 113. Artifact Requirements

`.axprof` must be:

```text versioned
checksummed
deterministic
streamable
compressible
random-access capable
```

---

# 114. Artifact Streaming

A profile can be written incrementally:

```text collector
 ↓
chunk
 ↓
compress
 ↓
artifact writer
```

without retaining the entire raw profile in RAM.

---

# 115. Chunk Model

```text ProfileChunk {
    sequence
    type
    compressed_size
    uncompressed_size
    checksum
    payload
}
```

---

# 116. Crash-Safe Profile Writing

If the process being profiled crashes:

```text partial profile
```

should remain recoverable when possible.

The profiler writes checkpoints/chunks independently.

---

# 117. Profile Finalization

Normal completion:

```text stop
 ↓
flush collectors
 ↓
flush buffers
 ↓
aggregate
 ↓
build indexes
 ↓
write footer
 ↓
checksum
 ↓
COMPLETE
```

---

# 118. Partial Artifact

If interrupted:

```text PARTIAL
```

must be explicitly marked.

---

# 119. Profile Reader

Canonical:

```text profile_open()
profile_close()
profile_metadata()
profile_modules()
profile_functions()
profile_call_tree()
profile_timeline()
profile_counters()
profile_allocations()
profile_tasks()
profile_locks()
```

---

# 120. Lazy Reader

Large profiles must support:

```text lazy chunk loading
memory mapping
index lookup
```

rather than loading everything.

---

# 121. Profile Compression

Compression may be applied independently to:

```text samples
events
strings
call tree
metadata
```

---

# 122. String Interning

Repeated:

```text module names
function names
source paths
event names
```

are interned.

---

# 123. Profile Security

Profile artifacts may contain:

```text memory addresses
source paths
function names
allocation information
timing
```

They are sensitive development artifacts.

---

# 124. Sensitive Data

Profiler must not automatically capture:

```text arbitrary heap contents
environment secrets
file contents
network payloads
```

unless explicitly requested by a separate diagnostic mode.

---

# 125. Memory Sampling Privacy

Allocation profiling records metadata such as:

```text size
address
site
```

not the allocated bytes by default.

---

# 126. Resource Limits

Configurable:

```text max profile duration
max buffer memory
max event count
max artifact size
max stack depth
max symbolization work
max timeline tracks
```

---

# 127. Event Rate Limiting

If instrumentation produces too many events:

```text sampling
aggregation
drop policy
```

may be applied.

Dropped events must be counted.

---

# 128. Backpressure

The target must not block indefinitely because the profiler consumer is slow.

Preferred:

```text target
 ↓
bounded buffer
 ↓
drop/degrade
```

rather than:

```text target → blocking profiler disk writer
```

---

# 129. Collector Isolation

Collectors:

```text CPU
counter
memory
task
sync
timeline
instrumentation
```

are independent modules.

---

# 130. Collector Interface

```text ProfileCollector {
    prepare()
    start()
    poll()
    flush()
    stop()
    destroy()
    capabilities()
}
```

---

# 131. Collector Failure

One collector failing should not necessarily destroy the entire profile.

Example:

```text hardware counter unavailable
```

can produce:

```text CPU samples + timeline
```

without counter data.

---

# 132. Profile Quality Report

Artifact includes:

```text ProfileQuality {
    dropped_samples
    dropped_events
    unavailable_counters
    partial_stacks
    unresolved_symbols
    collector_errors[]
}
```

---

# 133. Symbolization Quality

Statistics:

```text total_frames
resolved_frames
unresolved_frames
```

are recorded.

---

# 134. Stack Quality

```text complete
partial
failed
```

counts are recorded.

---

# 135. Profile Reproducibility

Raw event ordering is deterministic given identical captured event sequence.

Sampling itself is inherently statistical and must not be represented as exact deterministic execution.

---

# 136. Profile Seeds

Where sampling jitter is software-controlled, configuration may contain:

```text sampling_seed
```

for reproducibility of the scheduling pattern.

---

# 137. Hardware Non-Determinism

Hardware counters may vary across runs.

Artifact records:

```text CPU model
counter configuration
kernel/platform
```

---

# 138. CPU Identification

```text CpuProfileInfo {
    vendor
    family?
    model?
    architecture
    features[]
}
```

---

# 139. Compiler Identification

```text CompilerProfileInfo {
    compiler_version
    optimization
    debug_level
    LTO
    PGO
    build_id
}
```

---

# 140. Workload Identity

Profiles should optionally identify:

```text benchmark
scenario
input hash
test name
run id
```

---

# 141. Profile Metadata

```text ProfileMetadata {
    timestamp
    duration
    target
    build_id
    compiler
    cpu
    OS
    configuration
    workload
}
```

---

# 142. Profile API — Session

```text
profile_session_create()
profile_session_destroy()
profile_session_state()
profile_session_start()
profile_session_stop()
profile_session_pause()
profile_session_resume()
```

---

# 143. Profile API — Configuration

```text
profile_config_create()
profile_config_set_mode()
profile_config_set_duration()
profile_config_set_frequency()
profile_config_set_stack_depth()
profile_config_set_buffer_size()
profile_config_add_module()
profile_config_add_thread()
profile_config_add_counter()
profile_config_validate()
```

---

# 144. Profile API — Sampling

```text
profile_sample_start()
profile_sample_stop()
profile_sample_frequency()
profile_sample_statistics()
```

---

# 145. Profile API — Counters

```text
profile_counter_list()
profile_counter_describe()
profile_counter_enable()
profile_counter_disable()
profile_counter_read()
profile_counter_results()
```

---

# 146. Profile API — Memory

```text
profile_memory_start()
profile_memory_stop()
profile_memory_statistics()
profile_memory_allocations()
profile_memory_sites()
profile_memory_lifetimes()
```

---

# 147. Profile API — Tasks

```text
profile_task_start()
profile_task_stop()
profile_task_statistics()
profile_task_timeline()
profile_executor_statistics()
```

---

# 148. Profile API — Synchronization

```text
profile_sync_start()
profile_sync_stop()
profile_lock_statistics()
profile_wait_statistics()
profile_wait_graph()
```

---

# 149. Profile API — Timeline

```text
profile_timeline()
profile_timeline_tracks()
profile_timeline_events()
profile_timeline_range()
```

---

# 150. Profile API — Call Tree

```text
profile_call_tree()
profile_call_tree_root()
profile_call_tree_children()
profile_call_tree_hotspots()
```

---

# 151. Profile API — Symbolization

```text
profile_symbolize()
profile_symbol_lookup()
profile_source_lookup()
profile_symbol_statistics()
```

---

# 152. Profile API — Artifact

```text
profile_write()
profile_write_chunk()
profile_finalize()
profile_open()
profile_validate()
profile_metadata()
```

---

# 153. Profile API — Comparison

```text
profile_compare()
profile_compare_call_tree()
profile_compare_counters()
profile_compare_allocations()
profile_compare_tasks()
```

---

# 154. Profile API — Remote

```text
profile_remote_connect()
profile_remote_authenticate()
profile_remote_start()
profile_remote_stop()
profile_remote_download()
profile_remote_disconnect()
```

---

# 155. Profile API — Export

```text
profile_export_json()
profile_export_call_tree()
profile_export_flamegraph()
profile_export_timeline()
profile_export_csv()
```

Export formats are representations of `.axprof`, not canonical storage.

---

# 156. Profile Query Model

Queries should support:

```text top functions by CPU
top allocations
top waits
top counters
hot source lines
task utilization
thread utilization
```

---

# 157. Query Engine

```text ProfileQuery {
    metric
    filters
    grouping
    ordering
    limit
}
```

---

# 158. Metric Model

```text ProfileMetric {
    samples
    cpu_time
    wall_time
    wait_time
    allocations
    allocated_bytes
    live_bytes
    counter_value
}
```

---

# 159. Grouping

Group by:

```text process
thread
task
module
function
source
type
lock
```

---

# 160. Aggregation Without Full Raw Data

The profiler may aggregate in streaming mode when raw event retention is not requested.

This permits:

```text long production profiles
```

with bounded memory.

---

# 161. Streaming Profile

```text target
 ↓
samples
 ↓
online aggregation
 ↓
rolling call tree
 ↓
final .axprof
```

---

# 162. Full Trace Profile

For detailed analysis:

```text raw events retained
```

subject to configured limits.

---

# 163. Profile Levels

```text PROFILE_MINIMAL
PROFILE_STANDARD
PROFILE_DETAILED
PROFILE_TRACE
```

### MINIMAL

Hot functions.

### STANDARD

Call tree + thread/task statistics.

### DETAILED

Memory, counters, synchronization where available.

### TRACE

Detailed event timeline.

---

# 164. Production Default

Production profiling should prefer:

```text PROFILE_SAMPLE
```

with low frequency and bounded capture.

---

# 165. Development Default

Development profiling may use:

```text PROFILE_COMBINED
```

with:

```text sampling
+
counters
+
task events
```

---

# 166. Instrumentation Placement

AXCOMPILER may instrument only selected:

```text functions
modules
source ranges
```

instead of the entire application.

---

# 167. Selective Instrumentation

```text profile_instrument_function()
profile_instrument_module()
profile_instrument_range()
```

---

# 168. Compiler Optimization Interaction

Profiling metadata must identify:

```text optimization
LTO
inlining
PGO
```

because optimization changes attribution.

---

# 169. PGO Boundary

AXPROFILER can produce profile data consumed by AXCOMPILER for PGO.

Flow:

```text AXPROFILER
      ↓
profile artifact
      ↓
AXCOMPILER PGO importer
      ↓
optimized build
```

---

# 170. PGO Data Separation

Performance profiles and PGO profiles are related but not identical.

AXPROFILER owns collection.

AXCOMPILER owns optimization decisions.

---

# 171. Hotness Data

Canonical:

```text FunctionHotness {
    function_id
    sample_count
    normalized_hotness
}
```

---

# 172. PGO Export

```text profile_export_pgo()
```

must produce a compiler-consumable representation without requiring the compiler to understand UI-specific profile formats.

---

# 173. Inlining Analysis

Profiler may show:

```text logical source function
physical machine function
inline chain
```

to explain optimized code.

---

# 174. Hot Line Mapping

Sample addresses map to source lines where compiler metadata permits.

Line attribution must identify:

```text source file
line
column?
inline context
```

---

# 175. Source Line Ambiguity

If multiple machine ranges map to the same line:

```text aggregate
```

but preserve individual ranges internally.

---

# 176. Assembly-Level Profile

Optional view:

```text instruction address
instruction
sample count
counter metrics
```

This is particularly useful for Axiom compiler developers.

---

# 177. Machine Instruction Identity

Instruction-level profile uses:

```text module build_id
relative address
instruction bytes/hash where available
```

so addresses remain meaningful within the build.

---

# 178. Binary Changes

After recompilation, profile data is never automatically applied to a different binary unless build identity compatibility is established.

---

# 179. Cross-Version Profile

A comparison tool may explicitly compare different builds using:

```text SymbolId
source identity
```

but must mark unmatched functions.

---

# 180. Profile Diff

States:

```text NEW
REMOVED
UNCHANGED
CHANGED
```

are descriptive, not performance judgments.

---

# 181. Performance Regression Detection

AXTEST can consume profile metrics to detect configured thresholds.

AXPROFILER provides measurements.

AXTEST owns pass/fail policy.

---

# 182. Alert Boundary

AXPROFILER does not decide:

```text "performance is unacceptable"
```

unless a caller supplies an explicit threshold.

---

# 183. Profile Export for AI

Canonical AI context:

```text AIProfileContext {
    build_id
    workload
    top_functions[]
    top_allocations[]
    top_waits[]
    counters[]
    timeline_summary
    quality
}
```

---

# 184. AI Analysis Safety

AI receives measured data with provenance.

It must not treat:

```text sample estimate
```

as:

```text exact execution time
```

---

# 185. AI Recommendation Boundary

AI may explain profile evidence and propose optimizations.

Any source mutation remains an explicit AXIDE action.

---

# 186. Profile Provenance

Each aggregate records:

```text source collector
raw event count
aggregation configuration
symbolization source
```

---

# 187. Profile Quality UI

AXIDE should expose:

```text samples
dropped
unresolved
partial
counter scaled
```

alongside results.

---

# 188. No False Precision

If sampling gives:

```text 1,000 samples
```

the UI must not claim:

```text exactly 1.000 seconds
```

unless duration is independently measured.

---

# 189. Time Estimation

Estimated CPU contribution:

```text sample_count × sampling_period
```

must be labeled as estimated.

---

# 190. Multi-Core Sampling

Per-CPU/per-thread samples can be aggregated into process-level views.

No assumption is made that:

```text one CPU = one thread
```

---

# 191. CPU Saturation

Profiler can expose:

```text runnable threads
CPU utilization
sample distribution
```

but scheduler policy remains outside the profiler.

---

# 192. Thread Imbalance

Profile data can reveal uneven CPU distribution.

It remains observational.

---

# 193. Task Imbalance

Task profile can expose:

```text task runtime distribution
queue latency
executor utilization
```

---

# 194. Queue Latency

For supported AXTASK executors:

```text enqueue timestamp
start timestamp
```

yield:

```text queue_latency
```

---

# 195. Task Latency

```text completion - creation
```

can be decomposed into:

```text CPU
wait
queue
suspend
```

where metadata exists.

---

# 196. Async Latency

A task may spend most of its lifetime suspended.

Profiler distinguishes:

```text elapsed lifetime
CPU execution
waiting
```

---

# 197. Lock Latency

Lock metrics distinguish:

```text acquisition time
wait time
critical-section duration
```

where instrumentation provides enough information.

---

# 198. Synchronization Overhead

Profiler can aggregate:

```text total wait
wait count
lock hold time
```

without becoming the synchronization runtime.

---

# 199. Event Correlation

Events can correlate through:

```text process_id
thread_id
task_id
lock_id
module_id
sequence
```

---

# 200. Profile Context Propagation

Axiom tasks may propagate:

```text ProfileContextId
```

across async boundaries.

This must not require heavyweight TLS or allocation per task.

---

# 201. Low-Overhead Context

Profile context should preferably use:

```text compact integer ID
```

rather than heap objects.

---

# 202. Release Runtime

Normal builds contain no profiling runtime unless:

```text profiling
instrumentation
runtime tracing
```

is explicitly enabled.

---

# 203. Sampling Without Runtime

Pure CPU sampling can profile a release binary without linking an Axiom profiling runtime.

This is a core design goal.

---

# 204. Instrumented Build

Only explicit modes add:

```text profiling hooks
task events
allocation events
synchronization events
```

---

# 205. No Hidden Allocations

Profiling hot paths must avoid hidden:

```text String
Vec growth
heap allocation
locking
formatting
```

---

# 206. Per-CPU/Per-Thread Aggregation

Where practical:

```text local aggregation
```

reduces global contention.

---

# 207. Merge Phase

At stop:

```text local collectors
 ↓
deterministic merge
 ↓
ProfileIR
```

---

# 208. Parallel Merge

Large profiles can merge in parallel.

Final ordering must remain deterministic.

---

# 209. Memory Budget

Example configuration:

```text 16 MB
64 MB
256 MB
1 GB
```

depending on profile level.

The profiler must enforce the configured budget.

---

# 210. Adaptive Degradation

When approaching resource limits:

```text full events
 ↓
aggregation
 ↓
sampling
 ↓
drop
```

The selected degradation is recorded.

---

# 211. Artifact Integrity

Every `.axprof` contains:

```text checksum
```

and optionally:

```text cryptographic hash
```

---

# 212. Profile Signature

Enterprise/build systems may optionally sign artifacts through:

```text AXTRUST / AXCRYPTO
```

AXPROFILER does not own signing.

---

# 213. Profile Artifact Identity

```text ProfileId {
    artifact_hash
    build_id
    session_id
}
```

---

# 214. Profile Cache

Cached symbolization and derived indexes use:

```text build_id
+
profile_hash
```

---

# 215. Incremental Analysis

Opening a large profile should support:

```text metadata first
call tree next
timeline on demand
memory analysis on demand
```

---

# 216. Profile Query Cache

Repeated queries can be cached by:

```text profile_hash
query_hash
```

---

# 217. Remote Artifact Transfer

Transfer supports:

```text chunked
resumable
checksummed
compressed
```

---

# 218. Remote Profile Privacy

A remote collector must explicitly state:

```text what is collected
where it is stored
duration
buffer size
```

before starting.

---

# 219. Remote Stop Safety

Disconnecting the client must not necessarily terminate the target.

The server may continue according to session policy.

---

# 220. Profile Session Ownership

Remote session ownership determines:

```text who may stop
who may reconfigure
who may download
```

---

# 221. Platform Backend

```text ProfileBackend {
    capabilities()
    attach()
    detach()
    start_sampling()
    stop_sampling()
    read_counters()
    collect_threads()
    collect_modules()
}
```

---

# 222. Windows Backend

Supports applicable:

```text PE64
Windows CPU sampling
hardware counters
thread/process profiling
ETW/native mechanisms where appropriate
```

without exposing Windows-specific APIs through the portable ABI.

---

# 223. Linux Backend

Supports applicable:

```text ELF64
CPU sampling
hardware counters
thread/process profiling
scheduler/task events
```

using platform facilities behind the backend boundary.

---

# 224. macOS Backend

Supports:

```text Mach-O
CPU sampling
thread profiling
hardware performance facilities where accessible
```

subject to OS permissions.

---

# 225. Android Backend

Supports native:

```text AArch64
ELF64
```

profiling under platform/device permissions.

---

# 226. iOS Backend

Profiling is capability-limited and primarily development-oriented.

Production/device restrictions must be respected.

---

# 227. WASM Backend

WASM profiling measures:

```text function execution
source ranges
linear memory
tasks if host runtime exposes them
```

rather than host CPU counters directly.

---

# 228. WASM Host Counter Boundary

Host hardware counters remain host-specific and are not represented as native WASM counters.

---

# 229. Sampling Permission Failure

If platform permission prevents sampling:

```text PROFILE_PERMISSION_DENIED
```

must be returned with actionable diagnostic information.

---

# 230. Backend Capability Report

```text ProfileCapabilities {
    cpu_sampling
    hardware_counters
    allocation
    task_events
    lock_events
    timeline
    remote
    wasm
}
```

---

# 231. API Error Model

Canonical errors:

```text PROFILE_INVALID_SESSION
PROFILE_ALREADY_RUNNING
PROFILE_NOT_RUNNING
PROFILE_UNSUPPORTED
PROFILE_PERMISSION_DENIED
PROFILE_BUFFER_LIMIT
PROFILE_EVENT_OVERFLOW
PROFILE_COUNTER_UNAVAILABLE
PROFILE_SYMBOL_MISMATCH
PROFILE_ARTIFACT_CORRUPT
PROFILE_TARGET_EXITED
PROFILE_BACKEND_ERROR
PROFILE_REMOTE_AUTH_FAILED
PROFILE_REMOTE_PROTOCOL_MISMATCH
PROFILE_RESOURCE_LIMIT
PROFILE_CANCELLED
```

---

# 232. ABI Handle Model

Opaque:

```text ProfileSessionHandle
ProfileCollectorHandle
ProfileArtifactHandle
ProfileQueryHandle
ProfileModuleHandle
ProfileFunctionHandle
```

---

# 233. Handle Generation

Handles include internal generation validation.

Stale handles return:

```text PROFILE_INVALID_HANDLE
```

---

# 234. ABI Allocation

All returned profile structures are owned by AXPROFILER unless explicitly documented otherwise.

Release functions are mandatory.

---

# 235. UTF-8

All human-readable profiler strings are UTF-8.

Binary profile data remains byte-oriented.

---

# 236. AI-Readable Schema

AXPROFILER exposes structured profile metadata:

```text ProfileSemanticNode {
    id
    kind
    name
    metric
    value
    source
    module
    evidence
}
```

---

# 237. AI Evidence Requirement

Every AI-visible metric must include:

```text metric definition
sample/event count
profile configuration
quality
```

---

# 238. No Automatic Optimization

AXPROFILER does not automatically modify source/compiler settings.

Optimization actions belong to explicit tooling workflows.

---

# 239. Compiler Feedback

AXCOMPILER may consume:

```text hot functions
branch data
call frequencies
```

through a PGO interface.

---

# 240. PGO Correctness

PGO data must never be applied to a binary whose:

```text target
ABI
function identity
```

is incompatible.

---

# 241. Benchmark Reproducibility

AXTEST should record:

```text CPU
OS
compiler
build ID
input
iterations
profile configuration
```

for benchmark profiles.

---

# 242. Statistical Test Integration

AXTEST can compare profile distributions across runs.

AXPROFILER supplies raw/profile metrics.

AXTEST decides regression thresholds.

---

# 243. Profile Fuzzing

Fuzz:

```text .axprof reader
profile chunk parser
compressed chunks
symbol records
timeline events
query engine
remote protocol
```

---

# 244. Artifact Corruption Tests

Test:

```text truncated file
invalid chunk
bad checksum
invalid index
integer overflow
recursive call tree
oversized string
```

---

# 245. Collector Stress Tests

Stress:

```text millions of samples
millions of events
thousands of threads
large task counts
rapid module load/unload
high allocation rates
high lock contention
```

---

# 246. Drop Accounting Tests

Force buffer overflow and verify:

```text dropped_count == actual dropped events
```

and no fabricated data appears.

---

# 247. Symbolization Tests

Verify:

```text Axiom symbols
C symbols
DWARF
CodeView
Mach-O
WASM
optimized/inlined frames
```

---

# 248. Counter Tests

Verify:

```text available counter
unavailable counter
multiplexing
scaling
permission failure
```

---

# 249. Async Tests

Verify:

```text task migration
suspend/resume
executor changes
nested await
task cancellation
```

---

# 250. Memory Tests

Verify:

```text allocation
free
partial capture
sampled allocation
high allocation rate
cross-thread free
```

---

# 251. Synchronization Tests

Verify:

```text lock acquisition
wait
release
task waiting
thread waiting
contention aggregation
```

---

# 252. Timeline Tests

Verify:

```text overlapping events
nested events
same timestamp
different threads
different processes
```

---

# 253. Deterministic Aggregation Test

Same raw event stream must produce identical:

```text call tree
indexes
statistics
artifact ordering
```

---

# 254. Remote Protocol Tests

Verify:

```text authentication
authorization
version negotiation
disconnect
resume
cancel
resource limits
malformed messages
```

---

# 255. Performance Tests

Profiler overhead itself must be measured.

Required:

```text no profiler
sampling profiler
counter profiler
instrumentation profiler
full trace profiler
```

comparisons.

---

# 256. Overhead Budget

Target:

```text sampling mode:
low single-digit percentage overhead or better

full instrumentation:
explicitly allowed higher overhead

full trace:
potentially substantial overhead
```

The exact measured overhead must be reported by AXTEST rather than guaranteed universally.

---

# 257. Overhead Attribution

Profiler should expose:

```text collector overhead
symbolization overhead
buffer overhead
aggregation overhead
```

separately where measurable.

---

# 258. Profiler Self-Profiling

AXPROFILER should be capable of profiling itself in development builds.

---

# 259. No Recursive Profiling

Profiler internals must not accidentally generate target profile events unless explicitly requested.

---

# 260. Sampling Isolation

Profiler sampling interrupts should minimize interference with:

```text target locks
scheduler
allocator
I/O
```

---

# 261. Signal/Interrupt Safety

Platform sampling handlers may only perform operations proven safe for that backend.

No arbitrary runtime allocation is permitted in asynchronous sampling paths.

---

# 262. Collector Hot Path

Canonical:

```text interrupt
 ↓
capture registers
 ↓
capture IP
 ↓
capture bounded stack
 ↓
write local record
 ↓
return
```

Everything expensive is deferred.

---

# 263. Stack Capture Optimization

Use:

```text compact addresses
delta encoding
thread-local scratch
```

where beneficial.

---

# 264. Event Compression

Timeline events can use:

```text timestamp deltas
ID compression
dictionary strings
```

to reduce artifact size.

---

# 265. Call Stack Compression

Repeated stacks should be deduplicated:

```text StackId
```

rather than storing every full stack repeatedly.

---

# 266. Stack Table

```text StackTable {
    stack_id
    frames[]
}
```

Sample:

```text
Sample {
    stack_id
}
```

---

# 267. Frame Table

```text FrameTable {
    frame_id
    function_id
    module_id
    address
}
```

---

# 268. Function Table

```text FunctionTable {
    function_id
    symbol_id
    name
    source
    module
}
```

---

# 269. Profile Storage Efficiency

The combination:

```text Sample → StackId → FrameId → FunctionId
```

avoids repeated strings and addresses.

---

# 270. Timeline Storage Efficiency

Repeated event types use:

```text EventTypeId
```

and dictionary-based payload encoding.

---

# 271. Large Profile Scaling

Architecture target:

```text 10^8 samples/events
```

must be analyzable through chunking and aggregation rather than requiring all data in RAM.

This is a scalability target, not a minimum artifact size guarantee.

---

# 272. Online Aggregation

For long captures:

```text raw samples
 ↓
local call tree
 ↓
periodic merge
 ↓
discard raw data
```

may be selected.

---

# 273. Exact Trace Mode

When exact event history is needed:

```text raw events retained
```

subject to limits.

---

# 274. Profile Sampling vs Instrumentation

Recommended architecture:

```text CPU hotspots
       → sampling

exact function durations
       → instrumentation

hardware behavior
       → counters

allocation behavior
       → memory collector

async latency
       → task collector

lock contention
       → synchronization collector
```

The system chooses the least intrusive mechanism capable of answering the requested question.

---

# 275. Profile Session Composition

A single session may combine:

```text sampling
+
counters
+
task events
```

but all collectors share:

```text session identity
timeline clock
build identity
generation
```

---

# 276. Cross-Collector Correlation

Example:

```text CPU sample
Thread 5
Task 91
Function render()

Lock wait
Thread 5
Task 91
Lock 17
```

can be correlated.

---

# 277. Event Context

Every event should include only the IDs required for correlation.

Avoid large repeated metadata.

---

# 278. Profile Artifact Schema Version

```text AXPROF_SCHEMA_1
```

is separate from:

```text AXPROFILER_ABI_1
```

The former describes artifact serialization; the latter describes runtime API compatibility.

---

# 279. ABI Versioning

Breaking public API changes require:

```text AXPROFILER_ABI_2
```

---

# 280. Artifact Versioning

Artifact readers should support:

```text current
compatible previous
```

where practical.

---

# 281. Unknown Fields

Unknown optional artifact fields must be skipped safely.

Unknown required schema features must produce explicit errors.

---

# 282. Profile Validation

Before analysis:

```text header
 ↓
schema
 ↓
target
 ↓
identity
 ↓
chunks
 ↓
indexes
 ↓
cross-references
```

---

# 283. Cross-Reference Validation

Every:

```text FunctionId
StackId
FrameId
ThreadId
TaskId
ModuleId
```

must resolve or be explicitly marked unavailable.

---

# 284. Profile API Documentation

AXDOC extracts:

```text profiler API
collector API
artifact schema
metrics
capabilities
```

---

# 285. AXTEST Conformance

Every mandatory profile invariant is tested.

---

# 286. Profile Invariants

### PROF-INV-01
Every profile session has a unique identity.

### PROF-INV-02
Every profile result identifies the target build.

### PROF-INV-03
Profile collection is explicitly enabled.

### PROF-INV-04
Sampling must not require application instrumentation.

### PROF-INV-05
Sampling hot paths must not perform arbitrary allocation.

### PROF-INV-06
Sampling hot paths must not synchronously perform symbolization.

### PROF-INV-07
Dropped samples must be counted.

### PROF-INV-08
Dropped events must be reported.

### PROF-INV-09
Unresolved symbols must remain unresolved.

### PROF-INV-10
Profiler must never fabricate stack frames.

### PROF-INV-11
Sampling results are identified as statistical measurements.

### PROF-INV-12
Actual sampling configuration is stored in the profile.

### PROF-INV-13
Hardware counter availability is capability-driven.

### PROF-INV-14
Counter multiplexing is explicitly recorded.

### PROF-INV-15
Counter scaling is explicitly recorded.

### PROF-INV-16
Allocation profiling must not capture allocation contents by default.

### PROF-INV-17
Allocation events must preserve allocation identity.

### PROF-INV-18
Task identity must remain independent from OS thread identity.

### PROF-INV-19
Task migration must preserve task identity.

### PROF-INV-20
Wait time must not be counted as CPU execution.

### PROF-INV-21
Wall time and CPU time must remain distinct.

### PROF-INV-22
Lock contention data must preserve lock identity where available.

### PROF-INV-23
Timeline ordering must use monotonic time and sequence.

### PROF-INV-24
Event sequence numbers must be monotonic within a capture.

### PROF-INV-25
Profile aggregation must be deterministic for identical raw input.

### PROF-INV-26
Profile artifacts must identify schema version.

### PROF-INV-27
Profile artifacts must identify target and build identity.

### PROF-INV-28
Mismatched debug symbols must not be silently accepted.

### PROF-INV-29
Release builds must not contain mandatory profiler runtime overhead.

### PROF-INV-30
Instrumentation must be opt-in.

### PROF-INV-31
Profiling must not block target execution indefinitely due to collector backpressure.

### PROF-INV-32
Profiler resource limits must be enforceable.

### PROF-INV-33
Remote profiling must authenticate before privileged operations.

### PROF-INV-34
Remote profiling must not be enabled anonymously by default.

### PROF-INV-35
Profile artifacts must be safely parseable as untrusted input.

### PROF-INV-36
Partial profiles must be explicitly identified.

### PROF-INV-37
AI-visible profile data must retain measurement provenance.

### PROF-INV-38
AXPROFILER must not own compiler optimization decisions.

### PROF-INV-39
AXPROFILER must not replace AXDEBUGGER, AXOBSERVABILITY or AXCRASH.

### PROF-INV-40
Every conforming AXPROFILER implementation must satisfy all mandatory invariants above.

---

# 287. End-to-End CPU Profile

```text
Application
    ↓
CPU sampler
    ↓
per-thread SampleBuffer
    ↓
background drain
    ↓
stack deduplication
    ↓
symbolization
    ↓
ProfileIR
    ↓
CallTree
    ↓
.axprof
    ↓
AXIDE
```

---

# 288. End-to-End Memory Profile

```text
AXMEMORY
   ↓
allocation/free events
   ↓
local buffers
   ↓
aggregation
   ↓
allocation sites
   ↓
lifetime/peak analysis
   ↓
.axprof
```

---

# 289. End-to-End Async Profile

```text
AXTASK / AXASYNC
       ↓
task events
       ↓
TaskId
       ↓
CPU + wait correlation
       ↓
TaskProfile
       ↓
timeline/call tree
```

---

# 290. End-to-End PGO Flow

```text workload
   ↓
AXPROFILER
   ↓
hotness/call-frequency data
   ↓
PGO artifact
   ↓
AXCOMPILER
   ↓
optimization
   ↓
new BuildId
   ↓
AXTEST benchmark
   ↓
AXPROFILER comparison
```

---

# 291. End-to-End IDE Flow

```text AXIDE
  ↓
Start Profiling
  ↓
AXPROFILER
  ↓
capture
  ↓
.axprof
  ↓
Call Tree
  ↓
hot function
  ↓
source location
  ↓
AXCODEEDITOR
  ↓
AXDEBUGGER
```

---

# 292. Final Architecture

```text
                           AXIDE
                             │
                      AXPROFILER_ABI_1
                             │
                  ┌──────────▼──────────┐
                  │     AXPROFILER      │
                  │                     │
                  │ Session             │
                  │ Sampling            │
                  │ Counters            │
                  │ Memory              │
                  │ Tasks/Async         │
                  │ Synchronization     │
                  │ Timeline            │
                  │ Instrumentation     │
                  │ Aggregation         │
                  │ Symbolization       │
                  │ PGO Export          │
                  │ Remote              │
                  └──────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      AXDEBUGGER         AXRUNTIME           AXTASK
          │                  │                  │
     stack/symbols       runtime hooks      task events
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
                       Platform Backend
                             │
          ┌──────────┬───────┼───────┬─────────┐
          │          │       │       │         │
       Windows     Linux   macOS  Android    WASM
```

---

# 293. Final Design Decisions

AXPROFILER 5.0 permanently establishes:

1. **Sampling is the primary low-overhead profiler.**
2. **Instrumentation is explicitly opt-in.**
3. **Release binaries have no mandatory profiling runtime.**
4. **CPU, wall and wait time are distinct metrics.**
5. **Axiom tasks are distinct from OS threads.**
6. **Hardware counters are capability-driven.**
7. **Allocation profiling does not capture memory contents by default.**
8. **Raw collection is separated from expensive symbolization.**
9. **Large profiles use streaming/chunked storage.**
10. **`.axprof` is the canonical profile artifact.**
11. **PGO export is a defined compiler boundary.**
12. **AXPROFILER does not make optimization decisions itself.**
13. **AXDEBUGGER remains responsible for interactive target inspection.**
14. **AXOBSERVABILITY remains responsible for general telemetry.**
15. **AXCRASH remains responsible for crash reporting.**
16. **Remote profiling is authenticated and capability-controlled.**
17. **Every statistical result retains measurement provenance.**
18. **Dropped/partial/unresolved data is explicitly represented.**
19. **Profile aggregation is deterministic for identical captured data.**
20. **The profiler is designed around bounded overhead and bounded memory.**

---

# 294. Definition of Done

AXPROFILER 5.0 is complete when:

- `AXPROFILER_ABI_1` is frozen.
- `.axprof` / `AXPROF_SCHEMA_1` is frozen.
- CPU sampling works on supported native targets.
- stack capture and symbolization work.
- call-tree aggregation works.
- timeline representation works.
- hardware counter discovery works.
- counter multiplexing/scaling is represented.
- allocation profiling works.
- task/async profiling works.
- task migration is represented correctly.
- synchronization profiling works where supported.
- instrumentation mode works.
- instrumentation remains opt-in.
- production sampling works without debugger attachment.
- remote profiling is authenticated.
- profile streaming works.
- partial artifact recovery works.
- profile quality statistics work.
- PGO export works.
- AXIDE integration works.
- AXCODEEDITOR source attribution works.
- AXDEBUGGER navigation integration works.
- AXTEST benchmark integration works.
- AI-readable profile context contains provenance.
- release builds incur no mandatory profiling runtime cost.
- resource limits are enforced.
- malformed `.axprof` input cannot corrupt the profiler.
- all `PROF-INV-01..40` pass.
- platform conformance tests pass.
- fuzzing passes.
- large-profile stress tests pass.
- profiler self-profiling is demonstrated.
- self-hosted Axiom toolchain can produce and consume its own profile artifacts.

**BOOTSTRAP-791 — AXPROFILER 5.0 is frozen.**

---

## Next task

# BOOTSTRAP-792 — AXCRASH

**Native Axiom Crash Capture, Fault Classification, Panic/Trap Reporting, Minidump/Core-Dump Generation, Crash Artifact Format, Symbolized Stack Capture, Exception Context, Native/Managed State Correlation, Crash Recovery, Postmortem Analysis, Crash Database, Deduplication, Privacy Controls, Remote Crash Collection & Crash ABI 5.0**