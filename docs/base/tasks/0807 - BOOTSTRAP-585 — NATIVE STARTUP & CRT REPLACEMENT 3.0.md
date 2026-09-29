# BOOTSTRAP-585 — NATIVE STARTUP & CRT REPLACEMENT 3.0
## ZERO-DEPENDENCY PROCESS ENTRY, PLATFORM STARTUP, ARGUMENT/ENVIRONMENT INITIALIZATION, GLOBAL CONSTRUCTORS, TLS BOOTSTRAP, EXIT/ABORT, PANIC BOOTSTRAP, SIGNAL/EXCEPTION BRIDGE & MINIMAL AXIOM RUNTIME

**Trạng thái: COMPLETED / LOCKED**

`585` hoàn thiện tầng startup thực tế của Axiom. Sau task này, executable được tạo ở `584` có thể đi từ **OS loader → Axiom entry → runtime → `main`** mà không cần C runtime hoặc startup code của compiler khác.

```text id="585arch"
                    OS Loader
                        │
                        ▼
                 Axiom Entry Stub
                        │
                        ▼
              Platform Bootstrap
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
      ABI/CPU        Process State      TLS
        │               │                │
        └───────────────┼────────────────┘
                        ▼
                 Axiom Runtime Init
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
      Args/Env       Allocator       Panic/Unwind
                        │
                        ▼
               Global Initialization
                        │
                        ▼
                     main()
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
          return                 panic
             │                     │
             └──────────┬──────────┘
                        ▼
                 Runtime Shutdown
                        │
                        ▼
                   OS Exit
```

---

# 585.1. Startup design goals

Axiom startup phải:

- không phụ thuộc CRT;
- không phụ thuộc compiler khác;
- không yêu cầu heap để bootstrap;
- initialize đủ ABI state;
- initialize TLS trước TLS access;
- canonicalize arguments thành UTF-8;
- setup runtime theo profile;
- support panic/abort;
- support static và dynamic executable;
- support freestanding;
- deterministic.

---

# 585.2. Runtime profiles

```text id="profiles585"
Freestanding
Minimal
Hosted
Full
```

### Freestanding

Không mặc định:

- heap;
- filesystem;
- threads;
- environment;
- locale;
- dynamic loader API.

### Minimal

Có:

- process entry;
- arguments;
- basic memory;
- panic;
- exit.

### Hosted

Có:

- allocator;
- filesystem;
- environment;
- threads;
- networking;
- standard I/O.

### Full

Có toàn bộ runtime services được target hỗ trợ.

---

# 585.3. Entry point contract

OS chỉ gọi một symbol:

```text
__axiom_entry
```

Tên thực tế có thể target-specific nhưng semantic identity phải cố định.

---

# 585.4. Entry point không phải `main`

```text
OS entry
   ≠
Axiom main
```

Entry chịu trách nhiệm bootstrap.

`main` chỉ chạy sau khi startup contract hoàn thành.

---

# 585.5. Entry function ABI

Entry function sử dụng platform ABI từ `421`.

Không sử dụng Axiom high-level calling convention nếu OS không biết convention đó.

---

# 585.6. Entry state capture

Entry stub phải capture:

```text
stack pointer
register state
platform arguments
TLS state
loader-provided state
```

trước khi state bị thay đổi.

---

# 585.7. Stack preservation

Startup không được phá alignment yêu cầu của ABI trước khi gọi runtime.

---

# 585.8. Stack alignment

Trước lời gọi đầu tiên vào Axiom ABI:

```text
SP % ABI_ALIGNMENT == 0
```

theo target ABI cụ thể.

---

# 585.9. Initial stack ownership

Startup sở hữu initial stack frame cho đến khi transfer sang runtime.

---

# 585.10. Stack frame transition

Sau bootstrap, runtime được phép thiết lập stack frame chuẩn.

---

# 585.11. CPU feature state

Startup không được tự ý bật CPU features không được OS/platform cho phép.

---

# 585.12. Floating-point state

FP/SIMD state phải phù hợp ABI trước khi gọi code sử dụng FP/SIMD.

---

# 585.13. CPU dispatch

Nếu executable có multiversioning:

```text
startup
   ↓
CPU feature detection
   ↓
dispatch table
```

Detection phải xảy ra trước lần gọi implementation phụ thuộc feature.

---

# 585.14. No mandatory CPU probing

Freestanding target có thể disable runtime CPU detection.

---

# 585.15. Process state

Runtime state tối thiểu:

```text
ProcessContext {
    args
    environment
    allocator
    runtime_policy
    panic_policy
    exit_state
}
```

---

# 585.16. ProcessContext ownership

ProcessContext tồn tại ít nhất cho đến khi `main` kết thúc.

---

# 585.17. Arguments abstraction

Axiom canonical argument representation:

```text
Args
 └── UTF-8 strings
```

---

# 585.18. Windows arguments

Windows native command-line representation phải được chuyển sang UTF-8 theo một thuật toán canonical của Axiom.

---

# 585.19. Unix arguments

Unix `argv` được xem là byte sequences và được canonicalize theo Axiom process-argument policy.

---

# 585.20. Invalid UTF-8

Policy phải explicit:

```text
Strict
LosslessBytes
Replacement
```

Không được silently assume valid UTF-8.

---

# 585.21. Environment

Environment được expose như:

```text
Environment
 ├── get(name)
 ├── contains(name)
 └── enumerate()
```

---

# 585.22. Environment encoding

Environment sử dụng cùng encoding policy với process arguments.

---

# 585.23. Environment mutability

Hosted runtime có thể cho phép mutation.

Freestanding không bắt buộc support.

---

# 585.24. Standard streams

Hosted profile có:

```text
stdin
stdout
stderr
```

---

# 585.25. Stream initialization

Streams phải được initialized trước khi application code sử dụng standard I/O.

---

# 585.26. No hidden buffering dependency

Axiom runtime không được yêu cầu external C stdio.

---

# 585.27. Direct OS I/O

Core runtime có thể gọi trực tiếp:

```text
OS syscall / native platform API
```

qua platform layer.

---

# 585.28. Syscall boundary

Syscall wrappers không được expose raw platform ABI trực tiếp ở high-level API.

---

# 585.29. Platform adapter

```text id="platform585"
Axiom Runtime
      │
      ▼
Platform Adapter
 ┌────┼────┬─────┐
Linux Windows macOS WASM
```

---

# 585.30. Linux bootstrap

Linux hosted startup phải hỗ trợ initial process stack:

```text
argc
argv
envp
auxv
```

và loader-provided state khi applicable.

---

# 585.31. Linux auxiliary vector

Runtime có thể query:

- page size;
- hardware capabilities;
- executable base;
- randomization data;
- platform metadata.

---

# 585.32. Linux dynamic executable

Dynamic executable phải initialize loader-dependent facilities trước runtime code sử dụng chúng.

---

# 585.33. Linux static executable

Static executable phải chạy mà không cần dynamic loader.

---

# 585.34. Windows bootstrap

Windows startup phải canonicalize:

```text
command line
environment
process handles
startup information
```

---

# 585.35. Windows Unicode

Wide-character process APIs được chuyển sang Axiom UTF-8 representation.

---

# 585.36. Windows subsystem

Image builder `584` quyết định:

```text
Console
GUI
Native/other target mode
```

Startup semantics phải match subsystem.

---

# 585.37. macOS bootstrap

Mach-O entry phải chuyển sang Axiom startup trong đúng ABI/register state.

---

# 585.38. iOS bootstrap

iOS application startup không được giả định giống command-line process.

Axiom runtime phải phân biệt:

```text
Application
Extension
Framework
```

---

# 585.39. Android bootstrap

Android native process startup phải match Android ABI/API contract.

---

# 585.40. WASM startup

WASM không có OS process entry.

```text
WASM instantiate
       ↓
imports initialized
       ↓
start function
       ↓
Axiom runtime
```

---

# 585.41. WASI

WASI-hosted Axiom có thể map:

```text
args
env
stdin
stdout
filesystem
clock
random
```

thành capability-backed runtime services.

---

# TLS BOOTSTRAP

# 585.42. TLS-before-use invariant

Không Axiom code nào được đọc TLS trước khi TLS bootstrap hoàn thành.

---

# 585.43. Static TLS

Static TLS được OS loader chuẩn bị nếu platform hỗ trợ.

---

# 585.44. Dynamic TLS

Runtime phải initialize dynamic TLS module state khi required.

---

# 585.45. TLS template

```text
TLS Template
 ├── initialized bytes
 ├── zero-fill size
 └── alignment
```

---

# 585.46. TLS access

Compiler-generated TLS access phải sử dụng target ABI model từ `421`.

---

# 585.47. Thread-local runtime state

TLS có thể chứa:

```text
current task
panic state
allocator cache
error context
runtime flags
```

nhưng không được biến thành hidden global synchronization mechanism.

---

# 585.48. TLS destructor

TLS destructor chạy khi platform/thread lifecycle cho phép.

---

# 585.49. Thread bootstrap

Mọi Axiom-created thread phải initialize Axiom TLS trước khi chạy user function.

---

# 585.50. Thread exit

Thread exit phải execute required TLS cleanup.

---

# ALLOCATOR BOOTSTRAP

# 585.51. Bootstrap allocator

Runtime có một bootstrap allocator tối thiểu hoặc static allocation path.

---

# 585.52. No heap dependency

Entry/startup không được yêu cầu heap allocation để đạt tới allocator initialization.

---

# 585.53. Allocator initialization

```text
OS memory
    ↓
Axiom allocator
    ↓
application allocator
```

---

# 585.54. Allocator profiles

```text
System
Arena
Pool
General
Custom
```

---

# 585.55. Freestanding allocator

Application có thể cung cấp allocator trước khi runtime đầy đủ khởi tạo.

---

# 585.56. Allocator failure

Allocation failure policy:

```text
Result
Panic
Abort
Custom handler
```

---

# GLOBAL INITIALIZATION

# 585.57. Initialization registry

Compiler/linker tạo deterministic initialization registry.

---

# 585.58. Initialization entry

Mỗi initializer có:

```text
function
priority/dependency metadata
module identity
```

---

# 585.59. Dependency ordering

Nếu `B` phụ thuộc `A`:

```text
A → B
```

phải được enforce.

---

# 585.60. Cycle detection

Initialization cycle phải được phát hiện compile/link time khi statically knowable.

Runtime cycle detection là fallback.

---

# 585.61. Deterministic ordering

Không được phụ thuộc vào object-file discovery order.

---

# 585.62. Lazy initialization

Axiom hỗ trợ lazy initialization cho state phù hợp.

---

# 585.63. Thread-safe lazy initialization

Có primitive compiler/runtime cho:

```text
Once
Lazy
```

---

# 585.64. Initialization failure

Initializer có thể:

```text
return Result
panic
abort
```

theo declared policy.

---

# 585.65. Shutdown registry

Finalizers có deterministic reverse dependency ordering khi semantics yêu cầu.

---

# 585.66. Process termination

Không phải mọi termination path đều chạy finalizers.

Các mode:

```text
NormalExit
ImmediateExit
Abort
PanicAbort
OSKill
```

---

# 585.67. Normal exit

`main` return:

```text
main result
 ↓
shutdown
 ↓
exit
```

---

# 585.68. Immediate exit

Không chạy arbitrary application cleanup.

---

# 585.69. Abort

Abort phải chuyển sang OS/process termination primitive.

---

# 585.70. Exit code

Canonical:

```text
ExitCode : i32
```

Platform mapping được định nghĩa riêng.

---

# PANIC BOOTSTRAP

# 585.71. Panic before runtime

Nếu panic xảy ra trước runtime đầy đủ:

```text
minimal panic handler
```

được dùng.

---

# 585.72. Early panic handler

Early panic handler không được phụ thuộc:

- allocator;
- filesystem;
- logger;
- threads.

---

# 585.73. Hosted panic

Hosted runtime có thể:

```text
panic
 ↓
capture context
 ↓
unwind/abort
```

---

# 585.74. Freestanding panic

Freestanding có thể:

```text
panic → user handler
panic → abort
panic → platform trap
```

---

# 585.75. Panic payload

Panic payload phải có deterministic representation.

---

# 585.76. Panic recursion

Nếu panic handler panic lần hai:

```text
double panic → abort
```

mặc định.

---

# 585.77. Stack overflow

Stack overflow handling phải dùng platform mechanism hoặc compiler-generated guard/probe policy.

---

# 585.78. Stack overflow fallback

Không được giả định stack allocation vẫn an toàn sau stack exhaustion.

---

# EXCEPTION / SIGNAL BRIDGE

# 585.79. Platform exception boundary

Runtime có platform bridge cho:

```text
signals
exceptions
faults
```

---

# 585.80. Linux signals

Runtime có thể map selected signals tới:

```text
panic
termination
user handler
```

---

# 585.81. Windows exceptions

SEH-compatible bridge được hỗ trợ khi target policy yêu cầu.

---

# 585.82. Mach exceptions

macOS/iOS runtime không được giả định signal semantics giống Linux.

---

# 585.83. Hardware fault policy

Không tự động biến mọi hardware fault thành recoverable exception.

---

# 585.84. Illegal instruction

Mặc định:

```text
fatal
```

trừ khi explicit platform handler được cài.

---

# 585.85. Divide-by-zero

Behavior phụ thuộc target/runtime policy nhưng phải deterministic theo language contract.

---

# 585.86. Null access

Không được hứa rằng mọi OS page fault đều chuyển thành Axiom exception.

---

# UNWIND

# 585.87. Unwind runtime boundary

Runtime sử dụng unwind metadata đã tạo bởi `579`.

---

# 585.88. Zero-cost normal execution

Normal execution không cần exception bookkeeping trên mỗi instruction.

---

# 585.89. Cleanup

`drop/defer/finally` cleanup được compiler lower thành unwind/cleanup regions.

---

# 585.90. Panic unwind

Nếu profile bật unwind:

```text
panic
 ↓
unwind
 ↓
cleanup
 ↓
handler / terminate
```

---

# 585.91. Panic abort

Profile có thể compile:

```text
panic → abort
```

để giảm binary size/runtime complexity.

---

# 585.92. FFI unwind boundary

Không được unwind xuyên FFI boundary nếu foreign ABI không khai báo hỗ trợ.

---

# 585.93. Thread panic

Thread panic policy:

```text
catch
propagate
terminate thread
terminate process
```

phải explicit.

---

# 585.94. Main panic

Uncaught panic tại main → runtime termination policy.

---

# SIGNAL-SAFE RUNTIME

# 585.95. Async-signal-safe subset

Signal handler chỉ được gọi API thuộc signal-safe subset.

---

# 585.96. No allocator in signal handler

Allocator không được dùng trong signal-safe handler mặc định.

---

# 585.97. No lock recursion

Signal handler không được lock arbitrary runtime mutex.

---

# 585.98. Emergency output

Runtime có minimal emergency output path.

---

# 585.99. Startup/Shutdown synchronization

Startup và shutdown state machine:

```text
Uninitialized
    ↓
Bootstrapping
    ↓
Initialized
    ↓
Running
    ↓
ShuttingDown
    ↓
Exited
```

---

# 585.100. Invalid transition

Ví dụ:

```text
Exited → Running
```

phải reject/undefined theo runtime contract, không silent reset.

---

# RUNTIME STATE

# 585.101. Runtime singleton

Hosted runtime có một process-level runtime state.

---

# 585.102. Reentrancy

Runtime initialization phải detect reentrant initialization.

---

# 585.103. Initialization concurrency

Nếu multiple initialization paths có thể race, sử dụng `Once` semantics.

---

# 585.104. Runtime shutdown concurrency

Shutdown không được bắt đầu khi worker threads còn active nếu policy yêu cầu graceful shutdown.

---

# 585.105. Main-thread identity

Runtime phải biết main-thread identity nếu platform/runtime feature cần.

---

# 585.106. Current-thread identity

Thread identity phải là runtime abstraction, không hard-code platform integer semantics.

---

# 585.107. Current-task identity

Async runtime identity tách khỏi OS thread identity.

---

# 585.108. Process identity

Process ID chỉ được exposed bởi platform API, không được đưa vào core language semantics.

---

# CRT REPLACEMENT

# 585.109. Axiom replacement scope

Axiom startup thay thế phần tương đương:

```text
crt0
startup object
runtime init
basic process wrappers
```

không tuyên bố thay thế mọi OS library.

---

# 585.110. C runtime interoperability

Ứng dụng vẫn có thể link C runtime khi cần FFI.

---

# 585.111. Independent native mode

Pure Axiom executable:

```text
Axiom → OS
```

không:

```text
Axiom → C compiler runtime
```

---

# 585.112. Runtime symbol namespace

Internal symbols phải có namespace riêng:

```text
__axiom_*
```

hoặc equivalent mangling.

---

# 585.113. Symbol collision

Application không được vô tình override internal startup symbols.

---

# 585.114. User entry customization

Freestanding profile cho phép custom entry.

---

# 585.115. Custom entry contract

Custom entry phải explicitly declare:

```text
@entry
```

và compiler kiểm tra ABI.

---

# 585.116. Naked entry

Có thể hỗ trợ:

```text
@entry
@naked
```

cho low-level targets.

Naked function không được sử dụng language features yêu cầu compiler-generated frame trước khi setup hoàn tất.

---

# 585.117. Interrupt entry

Interrupt handlers là một ABI/profile riêng, không phải normal function.

---

# 585.118. Kernel mode

Axiom có thể compile freestanding kernel code mà không kéo hosted runtime.

---

# 585.119. Firmware

Firmware profile có thể bypass process/OS startup hoàn toàn.

---

# 585.120. Runtime component selection

Linker chỉ kéo runtime components thực sự được sử dụng.

```text
main
 ↓
runtime dependency graph
 ↓
minimal runtime closure
```

---

# 585.121. Dead runtime elimination

Unused runtime modules phải bị loại bỏ bởi linker GC.

---

# 585.122. Runtime size budget

Minimal executable không được vô tình kéo:

- networking;
- filesystem;
- threading;
- Unicode shaping;
- GUI;

nếu không sử dụng.

---

# 585.123. Startup latency

Runtime bootstrap phải có measurable startup budget.

---

# 585.124. Zero-allocation startup target

Minimal profile phải có thể đạt tới `main` mà không cần dynamic allocation.

---

# 585.125. Lazy subsystem initialization

Heavy subsystem:

```text
network
graphics
TLS crypto
filesystem
thread pool
```

chỉ initialize khi được sử dụng.

---

# SECURITY

# 585.126. Startup trust boundary

Startup code được xem là trusted low-level runtime.

---

# 585.127. Input validation

OS-provided startup structures phải validate trước khi sử dụng.

---

# 585.128. Stack validation

Startup không được assume malformed external process state là valid trong environment có thể bị hostile.

---

# 585.129. Environment sanitization

Security-sensitive applications có thể request environment filtering.

---

# 585.130. Privileged startup

Privileged executable không được tự động enable unsafe runtime behavior.

---

# 585.131. Random initialization

Security-sensitive runtime services có thể lấy OS-provided randomness sau bootstrap.

---

# 585.132. No deterministic security randomness

Reproducible binary identity không được đồng nghĩa runtime randomness deterministic.

---

# TESTING

# 585.133. Startup smoke tests

Mỗi target phải test:

```text
entry
 ↓
main
 ↓
exit
```

---

# 585.134. Arguments test

Test:

- empty args;
- Unicode;
- spaces;
- quotes;
- long arguments;
- malformed platform encoding.

---

# 585.135. Environment test

Test get/enumerate/mutation theo profile.

---

# 585.136. TLS test

Test:

```text
main thread
thread A
thread B
```

và verify TLS isolation.

---

# 585.137. Global init test

Verify dependency ordering.

---

# 585.138. Panic test

Test:

```text
main panic
nested panic
panic during initialization
panic during shutdown
```

---

# 585.139. Exit test

Test return codes.

---

# 585.140. No-runtime test

Build:

```text
@entry
```

program không kéo hosted runtime.

---

# 585.141. Freestanding test

Build executable/object cho environment không có OS runtime.

---

# 585.142. Dynamic test

Test executable sử dụng dynamic libraries.

---

# 585.143. Static test

Test fully static executable khi target hỗ trợ.

---

# 585.144. CRT independence test

Build pure-Axiom executable và inspect dependency graph:

```text
C runtime dependency = 0
```

trừ khi explicitly requested.

---

# 585.145. Loader integration test

Thực thi artifact bằng loader thật.

---

# 585.146. Unwind test

Panic/unwind phải produce valid stack traversal.

---

# 585.147. Stack overflow test

Test guard/probing trong controlled environment.

---

# 585.148. Signal/exception test

Test selected platform fault paths.

---

# 585.149. Startup fuzzing

Fuzz malformed:

```text
argv
environment
loader metadata
runtime configuration
```

---

# 585.150. Deterministic startup artifact

Startup code itself phải reproducibly encoded.

---

# 585.151. Runtime cache identity

Runtime component cache key:

```text
Target
ABI
RuntimeVersion
FeatureSet
SecurityPolicy
Profile
```

---

# 585.152. Cross-target isolation

Runtime artifact của target này không được reuse cho target khác chỉ vì source hash giống nhau.

---

# 585.153. Remote runtime artifact

Remote-built runtime object phải pass normal object/image verification.

---

# 585.154. Bootstrap self-hosting

Axiom compiler phải có thể:

```text
build compiler
 ↓
link runtime
 ↓
build executable
 ↓
execute compiler
```

không cần foreign compiler runtime.

---

# 585.155. Bootstrap trust

Startup binary là một phần của trusted compiler/runtime base.

---

# 585.156. Stage consistency

Stage0/1/2 phải produce semantically equivalent startup behavior.

---

# 585.157. FINAL STARTUP INVARIANT

> **Axiom native executable phải có khả năng đi từ OS/host entry point tới `main` thông qua startup/runtime do chính Axiom cung cấp, không bắt buộc C runtime hay startup code của compiler khác; mọi ABI, stack, argument, environment, TLS, allocator, global initialization, panic, unwind, signal/exception và process-exit transition phải được xác định rõ, kiểm tra được và phù hợp target.**

---

# 585 — LOCKED

Sau `585`, pipeline native của Axiom đã hoàn chỉnh thêm một tầng quan trọng:

```text
582  LINK
 ↓
583  LOADER CONTRACT
 ↓
584  FINAL IMAGE
 ↓
585  STARTUP / CRT REPLACEMENT
 ↓
OS PROCESS
 ↓
Axiom main()
```

Điều này cũng khóa một nguyên tắc quan trọng của Axiom:

> **Runtime là tập hợp các component có thể kéo theo nhu cầu, không phải một runtime khổng lồ luôn được nhúng vào mọi executable.**

Ví dụ một chương trình:

```text
@entry
fn main() -> i32 {
    return 0
}
```

có thể tạo binary gần như:

```text
OS loader
    +
Axiom entry
    +
minimal exit
```

trong khi ứng dụng lớn có thể kéo thêm:

```text
allocator
filesystem
network
TLS
threads
async
GUI
GPU
AI runtime
...
```

nhưng các phần không sử dụng không nên xuất hiện trong binary.

---

# NEXT — BOOTSTRAP-586

## COMPILER-BOOTSTRAP & RUNTIME SELF-HOSTING 4.0
### STAGE0/STAGE1/STAGE2, SELF-HOSTED COMPILER BUILD, TRUST ROOT, COMPILER/STD RUNTIME BOOTSTRAP, CROSS-COMPILATION, DETERMINISTIC SELF-REBUILD & TRUSTED COMPILER VERIFICATION

```text id="next586"
Stage0
  │
  ├── Axiom compiler seed
  ├── Minimal runtime
  └── Native backend
          │
          ▼
      Stage1 Compiler
          │
          ├── builds itself
          ├── builds runtime
          └── builds programs
                  │
                  ▼
            Stage2 Compiler
                  │
                  ▼
        Self-hosted Axiom toolchain
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  Reproducible Build   Bootstrap Verify
        │                   │
        └─────────┬─────────┘
                  ▼
          Trusted Compiler
```

`586` sẽ khóa **vòng lặp self-hosting thực sự của Axiom**: từ compiler seed tối thiểu đến compiler viết bằng Axiom tự build chính nó, tự build runtime/standard library, cross-compile target khác và kiểm tra bootstrap không phụ thuộc compiler bên ngoài.