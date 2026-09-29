# BOOTSTRAP-780 — AXRUNTIME

**Title:** Native Axiom Runtime Core, Process Runtime State, Global Initialization, Allocator Integration, Panic/Trap Boundary, Thread Runtime, Task/Async Runtime Bridge, TLS Runtime, I/O/OS Abstraction, Runtime Services Registration, Minimal/Full Runtime Profiles & Application Handoff 5.0  
**Namespace:** `AXRUNTIME`  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXRUNTIME` là lớp runtime native tối thiểu của Axiom, nằm sau `AXSTARTUP` và trước application code.

```text
                    OS / Loader
                         │
                         ▼
                    AXSTARTUP
                         │
                  StartupState
                         │
                         ▼
                     AXRUNTIME
          ┌──────────────┼──────────────┐
          │              │              │
       process         TLS          allocator
          │              │              │
       panic          threads        services
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    APPLICATION
```

Mục tiêu quan trọng:

> **AXRUNTIME không phải một “big runtime” bắt buộc đi cùng mọi chương trình.**

Axiom executable tối thiểu phải có thể link chỉ những runtime components thực sự cần.

---

# 2. Các nguyên tắc bất biến

AXRUNTIME phải:

- native;
- không phụ thuộc GC;
- không bắt buộc reference counting;
- không bắt buộc borrow checker runtime;
- không tạo OS thread cho mỗi task;
- không hidden allocation trong function call thông thường;
- không bắt buộc heap cho application;
- không bắt buộc filesystem/network;
- không bắt buộc scheduler nếu chương trình không dùng task;
- không bắt buộc exception runtime;
- không yêu cầu libc;
- hỗ trợ freestanding/minimal executable;
- hỗ trợ full application runtime;
- có thể self-host.

---

# 3. Boundary

### AXRUNTIME sở hữu

- runtime state;
- process runtime initialization;
- global runtime state;
- runtime service registration;
- allocator interface;
- TLS runtime integration;
- thread runtime bridge;
- panic/trap boundary;
- runtime shutdown;
- minimal runtime services;
- task/async bridge;
- runtime feature activation;
- runtime ABI entry points.

### Không sở hữu

```text
AXSTARTUP
→ raw process startup

AXLOADER
→ image loading

AXPROCESS
→ OS process abstraction

AXTASK
→ task scheduler

AXASYNC
→ async semantics

AXMEMORY
→ memory model

AXIPC
→ IPC

AXNETWORK
→ network

AXSTORAGE
→ storage

AXSECURITY
→ security policy

AXTIME
→ time

AXLOGGING
→ logging

AXDIAGNOSTICS
→ diagnostics
```

AXRUNTIME **kết nối** các subsystem này, không thay thế chúng.

---

# 4. Runtime layering

```text
┌──────────────────────────────────────┐
│          Axiom Application           │
├──────────────────────────────────────┤
│       Standard / Domain APIs         │
├──────────────────────────────────────┤
│              AXRUNTIME               │
│                                      │
│ process state                        │
│ TLS                                  │
│ allocator bridge                     │
│ panic/trap                           │
│ initialization                       │
│ shutdown                             │
│ service registry                     │
│ task/async bridge                    │
├──────────────────────────────────────┤
│ AXPROCESS / AXMEMORY / AXTASK / ...  │
├──────────────────────────────────────┤
│ Platform / OS                        │
└──────────────────────────────────────┘
```

---

# 5. Runtime profiles

Axiom 5.0 định nghĩa bốn profile.

```text
MINIMAL
CORE
STANDARD
FULL
```

### MINIMAL

```text
startup
TLS
panic/trap
basic process state
```

### CORE

MINIMAL +

```text
allocator
thread bridge
runtime services
```

### STANDARD

CORE +

```text
I/O
filesystem
time
logging
diagnostics
task/async
```

### FULL

STANDARD +

```text
network
GUI
graphics
media
plugins
application lifecycle
```

Runtime linker chỉ kéo component cần thiết.

---

# 6. Freestanding profile

```text
FREESTANDING
```

có thể chỉ sử dụng:

```text
AXSTARTUP
AXABI
AXRUNTIME_CORE
```

và application tự quản lý memory/device.

---

# 7. WASM profile

WASM runtime không giả định OS process.

```text
Host
 ↓
WASM instance
 ↓
AXSTARTUP
 ↓
AXRUNTIME_WASM
 ↓
application
```

---

# 8. Runtime entry

Canonical entry:

```text
axiom_runtime_entry(
    StartupState* state
)
```

Đây là entry point duy nhất giữa AXSTARTUP và AXRUNTIME.

---

# 9. Runtime startup pipeline

```text
AXSTARTUP
    │
    ▼
validate StartupState
    │
    ▼
runtime bootstrap
    │
    ├── initialize TLS
    ├── establish process state
    ├── initialize allocator
    ├── register runtime services
    ├── initialize required subsystems
    │
    ▼
application entry
    │
    ▼
application shutdown
    │
    ▼
runtime shutdown
```

---

# 10. StartupState ownership

AXRUNTIME không được tự do modify raw startup memory.

AXSTARTUP tạo normalized state.

AXRUNTIME tạo:

```text
RuntimeState
```

---

# 11. RuntimeState

```text
RuntimeState {
    version
    flags

    target
    process
    main_thread

    tls
    allocator

    services
    panic
    diagnostics

    lifecycle
    shutdown
}
```

---

# 12. RuntimeState lifetime

RuntimeState sống từ:

```text
axiom_runtime_entry()
```

đến runtime shutdown.

Không được expose mutable global RuntimeState cho arbitrary application code.

---

# 13. Runtime global state

AXRUNTIME chỉ có một logical runtime instance mỗi process/profile.

---

# 14. Runtime instance

Một process có thể có:

```text
PRIMARY_RUNTIME
```

và các embedded/runtime contexts nếu explicitly supported.

---

# 15. Embedded runtime

Library nhúng Axiom runtime không được tự động tạo process-global runtime lần thứ hai.

API:

```text
runtime_attach()
runtime_detach()
```

---

# 16. Runtime initialization phases

```text
PHASE_0
  raw bootstrap

PHASE_1
  platform state

PHASE_2
  TLS

PHASE_3
  allocator

PHASE_4
  core services

PHASE_5
  application services

PHASE_6
  application
```

---

# 17. Initialization dependency graph

Không được sử dụng service trước khi dependency phase hoàn tất.

---

# 18. Static initialization

Axiom không cho phép arbitrary global constructors chạy ngẫu nhiên.

Global initialization phải có dependency ordering deterministic.

---

# 19. Global initializer model

Compiler tạo:

```text
RuntimeInitRecord[]
```

và runtime chạy theo deterministic order.

---

# 20. Init record

```text
RuntimeInitRecord {
    priority
    module_id
    function
    dependencies[]
    flags
}
```

---

# 21. Initialization cycle

Cycle phải được phát hiện build-time hoặc startup-time deterministic.

---

# 22. No hidden constructor explosion

Một executable không dùng module sẽ không kéo initialization code của module đó.

---

# 23. Lazy initialization

Service có thể lazy-init nếu:

- thread-safe;
- deterministic;
- no unexpected blocking;
- no recursion deadlock.

---

# 24. Runtime service registry

```text
RuntimeServices {
    allocator
    panic
    diagnostics
    threads
    tasks
    io
    time
    random
}
```

Các entry có thể null/disabled trong minimal profiles.

---

# 25. Service capability

Service availability không đồng nghĩa application permission.

Security permission vẫn thuộc AXSECURITY/AXCAPABILITY.

---

# 26. Runtime feature flags

```text
RuntimeFeature {
    ALLOCATOR
    THREADS
    TASKS
    ASYNC
    IO
    TIME
    RANDOM
    LOGGING
    DIAGNOSTICS
}
```

---

# 27. Feature activation

Compiler/linker có thể tạo runtime manifest:

```text
RuntimeRequirements {
    required[]
    optional[]
}
```

---

# 28. Dead runtime elimination

Nếu application không dùng:

```text
AXTASK
```

runtime task subsystem không được link.

---

# 29. Runtime component granularity

Không nên chỉ có:

```text
libaxiom_runtime.a
```

khổng lồ.

Nên có logical units:

```text
runtime.core
runtime.memory
runtime.thread
runtime.task
runtime.async
runtime.io
runtime.panic
runtime.diagnostics
```

---

# 30. Static linking

Static executable chỉ link component cần thiết.

---

# 31. Dynamic runtime

Dynamic runtime có thể được cung cấp cho desktop/server deployments.

Nhưng native executable không được bắt buộc phụ thuộc runtime DLL/SO để chạy nếu statically linked profile được chọn.

---

# 32. Runtime ABI

```text
AXRUNTIME_ABI_1
```

là stable ABI của runtime service boundary.

---

# 33. Runtime ABI vs AXABI

```text
AXABI
→ function-level machine contract

AXRUNTIME_ABI
→ semantic contract giữa application/compiler và runtime services
```

---

# 34. Runtime ABI fingerprint

Runtime artifact phải expose:

```text
runtime_abi_major
runtime_abi_minor
abi_fingerprint
target
features
```

---

# 35. Runtime versioning

Runtime breaking API/ABI:

```text
major++
```

Backward-compatible extension:

```text
minor++
```

---

# 36. Runtime compatibility

Executable phải reject runtime ABI incompatible thay vì chạy undefined behavior.

---

# 37. Allocator boundary

AXRUNTIME không định nghĩa memory model mới.

Nó bridge:

```text
Axiom application
        ↓
AXRUNTIME allocator ABI
        ↓
AXMEMORY
```

---

# 38. Allocator interface

```text
runtime_alloc(size, align)
runtime_free(ptr, size, align)
runtime_realloc(ptr, old_size, new_size, align)
```

---

# 39. Allocator semantics

Mỗi allocation phải có:

```text
size
alignment
lifetime owner
allocator identity
```

khi cần thiết.

---

# 40. No mandatory heap

Program:

```text
@freestanding
fn main() { ... }
```

có thể chạy mà không initialize heap.

---

# 41. Stack allocation

Compiler ưu tiên stack allocation khi lifetime chứng minh được.

AXRUNTIME không can thiệp.

---

# 42. Arena integration

Arena thuộc AXMEMORY.

AXRUNTIME chỉ expose service registration nếu application yêu cầu.

---

# 43. Allocator replacement

Có thể:

```text
runtime_set_allocator()
```

nhưng chỉ trước khi allocator-dependent services được initialized.

---

# 44. Global allocator

Nếu application chọn custom allocator:

```text
#[global_allocator]
```

runtime phải dùng allocator đó cho runtime-owned allocations.

---

# 45. Runtime allocation discipline

Core runtime cố gắng:

```text
no allocation during normal startup
```

ngoại trừ explicitly required initialization.

---

# 46. Panic model

AXRUNTIME cung cấp terminal boundary cho:

```text
panic
trap
abort
unwind
```

---

# 47. Panic handler

```text
runtime_panic(PanicInfo*)
```

---

# 48. PanicInfo

```text
PanicInfo {
    message?
    file?
    line?
    column?
    function?
    error_code
    thread
}
```

Thông tin có thể bị strip trong release.

---

# 49. Panic profiles

```text
ABORT
TRAP
UNWIND
CUSTOM
```

---

# 50. Default panic

Embedded/minimal:

```text
ABORT/TRAP
```

Full application có thể chọn:

```text
UNWIND
```

---

# 51. Panic must not require logging

Panic path phải hoạt động ngay cả khi logging chưa initialized.

---

# 52. Panic allocation

Panic handler không được phụ thuộc heap allocation.

---

# 53. Recursive panic

Nếu panic xảy ra trong panic handler:

```text
terminate immediately
```

Không recurse vô hạn.

---

# 54. Trap

Hardware/software trap được chuyển thành runtime diagnostic nếu profile cho phép.

---

# 55. Fatal runtime error

```text
runtime_fatal(code)
```

phải có emergency path.

---

# 56. Error vs panic

```text
Result<T,E>
→ recoverable application error

panic
→ violated invariant / unrecoverable local state

trap
→ machine/runtime fault

abort
→ immediate termination
```

---

# 57. Thread integration

AXRUNTIME không implement scheduler OS thread.

AXTHREAD service được AXPROCESS/AXTASK/platform layer cung cấp.

---

# 58. Main thread

Startup tạo main thread descriptor.

AXRUNTIME registers it.

---

# 59. Thread runtime state

```text
ThreadRuntimeState {
    id
    tls
    runtime_flags
    panic_state
    task_context?
}
```

---

# 60. TLS

AXRUNTIME dùng TLS được bootstrap bởi:

```text
AXLOADER
AXSTARTUP
platform ABI
```

---

# 61. Runtime TLS

Per-thread:

```text
RuntimeTLS {
    thread_state
    panic_state
    current_task
    errno_like_state?
}
```

---

# 62. TLS fast path

Runtime TLS access phải compile xuống platform-native TLS mechanism.

Không dùng global lock.

---

# 63. Thread registration

```text
runtime_thread_attach()
runtime_thread_detach()
```

---

# 64. External thread attach

Foreign OS thread gọi Axiom library phải attach trước khi sử dụng thread-local runtime state.

---

# 65. Attach semantics

```text
OS thread
   ↓
runtime_thread_attach
   ↓
TLS state
   ↓
Axiom API
```

---

# 66. Thread detach

Detach phải:

- flush thread-local runtime state;
- unregister current task if applicable;
- release thread-local resources.

---

# 67. Thread destruction

Runtime không được assume mọi thread đều được tạo bởi Axiom.

---

# 68. Task integration

AXRUNTIME không chứa scheduler implementation.

Nó cung cấp bridge:

```text
application
 ↓
AXRUNTIME
 ↓
AXTASK
```

---

# 69. Task runtime handle

```text
RuntimeTaskHandle
```

chỉ là opaque/native handle.

---

# 70. Async runtime

AXASYNC sở hữu future/promise semantics.

AXRUNTIME cung cấp initialization/context.

---

# 71. Executor

Executor belongs AXTASK/AXASYNC.

Runtime chỉ activate executor khi application yêu cầu.

---

# 72. No thread-per-task

AXRUNTIME không được tạo OS thread cho mỗi async task.

---

# 73. Runtime task context

TLS có thể chứa:

```text
current_task
```

để diagnostics và cancellation.

---

# 74. Cancellation

Cancellation semantics thuộc AXTASK/AXASYNC.

Runtime chỉ đảm bảo task context có thể truy cập.

---

# 75. Runtime I/O bridge

AXRUNTIME không implement filesystem/network protocol.

Nó cung cấp service lookup:

```text
runtime_service("io")
```

---

# 76. Service lookup

Service lookup phải nhanh và immutable sau initialization.

---

# 77. Runtime service descriptor

```text
RuntimeService {
    id
    version
    abi
    capabilities
    vtable
}
```

---

# 78. Service vtable

Nếu runtime service được dynamic dispatch:

```text
service header
+
function table
```

---

# 79. Service ABI stability

Vtable phải versioned.

---

# 80. Service registration

```text
runtime_register_service()
```

chỉ được phép trong initialization phase hoặc explicit plugin lifecycle.

---

# 81. Plugin services

Plugin services phải qua AXCAPABILITY/AXSECURITY.

Không được register service để bypass security.

---

# 82. Runtime logging

AXRUNTIME không implement logging engine.

Panic/fatal path có thể gọi emergency diagnostic sink.

---

# 83. Runtime diagnostics

```text
runtime_report_fault()
```

được forward tới AXDIAGNOSTICS nếu available.

---

# 84. Minimal diagnostics

Nếu AXDIAGNOSTICS không linked:

```text
stderr/debug output/OS emergency channel
```

hoặc platform-specific minimal termination.

---

# 85. Runtime time

Không own clock.

Dùng AXTIME.

---

# 86. Runtime random

Không own RNG.

Dùng AXRANDOM.

---

# 87. Runtime security

Không own policy engine.

Runtime phải query AXSECURITY khi service cần authorization.

---

# 88. Runtime capability

Không tự grant capabilities.

---

# 89. Runtime environment

Startup environment:

```text
argv
env
platform data
```

được lưu trong runtime process state nếu profile cần.

---

# 90. Environment ownership

Runtime có thể expose immutable views.

Không copy toàn bộ environment nếu không cần.

---

# 91. Arguments

`args` có thể giữ references tới normalized startup storage.

---

# 92. UTF-8

Axiom API sử dụng UTF-8 mặc định.

Raw bytes vẫn có thể được truy cập để preserve invalid external data.

---

# 93. Process exit

API:

```text
runtime_exit(code)
```

---

# 94. Normal exit

Normal application exit:

```text
main
 ↓
return code
 ↓
runtime_shutdown
 ↓
OS exit
```

---

# 95. Immediate exit

```text
runtime_abort(code)
```

bỏ qua normal cleanup.

---

# 96. Shutdown ordering

```text
application shutdown
 ↓
task shutdown
 ↓
service shutdown
 ↓
thread runtime cleanup
 ↓
allocator finalization
 ↓
process exit
```

---

# 97. Shutdown handlers

Application có thể đăng ký:

```text
runtime_on_exit(fn)
```

nhưng phải deterministic.

---

# 98. Exit handler restrictions

Không được assume:

- arbitrary scheduler;
- filesystem;
- network;
- allocator availability.

---

# 99. Exit recursion

Shutdown callback gọi `runtime_exit()` lần nữa phải không tạo recursive shutdown.

---

# 100. Runtime finalization state machine

```text
UNINITIALIZED
     ↓
BOOTSTRAPPING
     ↓
RUNNING
     ↓
SHUTTING_DOWN
     ↓
TERMINATED
```

---

# 101. Invalid transitions

Ví dụ:

```text
TERMINATED → RUNNING
```

phải fail.

---

# 102. Runtime state atomicity

State transitions phải thread-safe.

---

# 103. Runtime lock strategy

Core runtime không được có global mutex trong normal function-call path.

---

# 104. Initialization synchronization

Nếu multiple threads attach trong startup race, initialization phải dùng one-time initialization primitive.

---

# 105. One-time initialization

```text
runtime_once()
```

có semantics tương tự platform atomic once.

---

# 106. Reentrancy

Core runtime functions phải document:

```text
REENTRANT
NON_REENTRANT
INIT_ONLY
SHUTDOWN_ONLY
```

---

# 107. Signal/exception context

Platform signal handler không được gọi arbitrary runtime API.

Chỉ async-signal-safe emergency functions.

---

# 108. Crash path

```text
fault
 ↓
minimal runtime handler
 ↓
AXDIAGNOSTICS
 ↓
AXAUDIT/AXOBSERVABILITY if safe
 ↓
terminate
```

---

# 109. Crash path no allocation

Crash path phải tránh heap allocation.

---

# 110. Crash path no locks

Crash handler không được phụ thuộc potentially-held locks.

---

# 111. Runtime diagnostics handoff

AXRUNTIME chuyển:

```text
RuntimeFault {
    code
    address
    thread
    registers?
    stack?
}
```

sang AXDIAGNOSTICS.

---

# 112. Register capture

Platform backend chịu trách nhiệm capture machine registers.

---

# 113. Stack capture

Stack unwinding thuộc AXDIAGNOSTICS/AXABI unwind metadata.

---

# 114. Runtime and debugger

Runtime phải expose runtime state metadata khi debugger integration enabled.

---

# 115. Runtime symbol

Canonical runtime symbols nên có prefix:

```text
__ax_
```

để tránh collision với application symbols.

---

# 116. Internal runtime symbol

Internal symbol có thể hidden/local.

---

# 117. Runtime public symbol

Chỉ ABI-required symbols được export.

---

# 118. Runtime API classes

```text
BOOTSTRAP
CORE
THREAD
MEMORY
TASK
ASYNC
DIAGNOSTIC
SHUTDOWN
```

---

# 119. Core API

```text
runtime_init()
runtime_start()
runtime_state()
runtime_features()
runtime_profile()
runtime_shutdown()
runtime_exit()
runtime_abort()
```

---

# 120. Allocator API

```text
runtime_alloc()
runtime_free()
runtime_realloc()
runtime_allocator()
runtime_set_allocator()
```

---

# 121. TLS API

```text
runtime_tls()
runtime_thread_attach()
runtime_thread_detach()
runtime_thread_state()
runtime_current_thread()
```

---

# 122. Panic API

```text
runtime_panic()
runtime_trap()
runtime_abort()
runtime_set_panic_handler()
runtime_panic_mode()
```

---

# 123. Task bridge

```text
runtime_task_current()
runtime_task_attach()
runtime_task_detach()
runtime_task_yield()
```

Scheduler remains AXTASK.

---

# 124. Service API

```text
runtime_register_service()
runtime_find_service()
runtime_require_service()
runtime_service_available()
```

---

# 125. Initialization API

```text
runtime_register_initializer()
runtime_run_initializers()
runtime_register_shutdown()
runtime_run_shutdown()
```

---

# 126. Diagnostic API

```text
runtime_fault()
runtime_emergency_write()
runtime_capture_state()
```

---

# 127. Runtime profile API

```text
runtime_profile()
runtime_has_feature(feature)
runtime_require_feature(feature)
```

---

# 128. Runtime manifest

Executable có thể chứa:

```text
RuntimeManifest {
    abi
    profile
    required_features[]
    optional_features[]
    allocator
    panic_mode
}
```

---

# 129. Runtime manifest purpose

Dùng để:

- linker;
- diagnostics;
- compatibility;
- inspection;
- AI tooling.

---

# 130. Runtime manifest không phải policy

Security policy vẫn thuộc AXSECURITY.

---

# 131. Runtime and static linking

AXLINKER có thể perform component-level dead stripping.

---

# 132. Runtime section

Linked binary có thể có:

```text
.axruntime
```

metadata section nếu target cho phép.

---

# 133. Runtime metadata stripping

Production build có thể strip nonessential metadata.

---

# 134. Runtime code size

Core runtime mục tiêu:

```text
minimal profile:
as small as target permits
```

Không đặt một con số tuyệt đối vì target/optimization khác nhau.

---

# 135. Runtime hot path

Hot-path APIs phải:

- inlineable;
- branch-light;
- allocation-free khi có thể;
- lock-free hoặc local-state.

---

# 136. Runtime cold path

Initialization, diagnostics, panic có thể tối ưu size thay vì latency.

---

# 137. Runtime inline policy

Compiler được phép inline:

```text
runtime_tls()
runtime_feature_check()
small service lookup
```

nếu ABI không bị phá.

---

# 138. Runtime call ABI

Internal calls dùng:

```text
"axiom"
```

trừ platform/FFI boundary.

---

# 139. Runtime C ABI

Nếu runtime expose C compatibility:

```text
extern "c"
```

adapter phải được generate.

---

# 140. Runtime allocator C API

Có thể expose:

```text
ax_alloc
ax_free
ax_realloc
```

nhưng không đồng nhất chúng với libc malloc/free.

---

# 141. Runtime and libc

**libc không phải dependency bắt buộc.**

Axiom runtime có thể gọi native OS interfaces trực tiếp qua platform adapters.

---

# 142. Windows runtime

Có thể sử dụng Windows native APIs.

Không bắt buộc MSVC runtime.

---

# 143. Linux runtime

Có thể dùng direct syscall/platform abstraction hoặc system libraries khi toolchain profile yêu cầu.

Không bắt buộc glibc.

---

# 144. Android

Runtime sử dụng Android native platform boundary theo target SDK/NDK integration khi cần, nhưng Axiom runtime ABI không phụ thuộc compiler của bên thứ ba.

---

# 145. macOS/iOS

Runtime sử dụng native platform interfaces theo deployment target.

---

# 146. WASM

Runtime host imports được explicit:

```text
axiom.runtime.*
```

hoặc target-specific import namespace.

---

# 147. Host import validation

WASM runtime phải reject incompatible host ABI.

---

# 148. Runtime host capability

WASM host service chỉ available nếu host grants capability.

---

# 149. Runtime and sandbox

AXRUNTIME phải hoạt động trong sandbox mà không giả định unrestricted OS access.

---

# 150. Runtime service denial

Nếu service không được phép:

```text
SERVICE_UNAVAILABLE
```

không bypass security.

---

# 151. Runtime thread-local state

TLS layout:

```text
AXRUNTIME_TLS {
    magic
    version
    thread_id
    runtime_state
    panic_state
    current_task
}
```

---

# 152. TLS ABI stability

TLS struct không được expose raw layout cho application.

---

# 153. Opaque handles

Public runtime state nên sử dụng opaque handles.

---

# 154. Runtime handles

Handle phải encode:

```text
type
generation
identity
```

nếu stale-handle detection cần thiết.

---

# 155. Runtime object ownership

Runtime objects có explicit ownership semantics.

Không dùng implicit reference counting toàn hệ thống.

---

# 156. Runtime reference counting

Có thể tồn tại trong specific subsystem nhưng không phải AXRUNTIME core requirement.

---

# 157. Runtime string allocation

Core runtime không tạo String object cho mọi diagnostic.

---

# 158. Panic message

Panic message có thể là:

```text
static string
```

để tránh allocation.

---

# 159. Runtime error codes

Core errors dùng compact integer/error enum.

---

# 160. Runtime result

Runtime API ưu tiên:

```text
Result<T, RuntimeError>
```

thay vì exceptions.

---

# 161. RuntimeError

```text
RuntimeError {
    code
    subsystem
    detail?
}
```

---

# 162. Error ABI

Error values phải nhỏ và register-returnable khi có thể.

---

# 163. Runtime error ownership

Detail strings không được assume heap lifetime.

---

# 164. Runtime configuration

AXCONFIG cung cấp configuration.

AXRUNTIME chỉ consume immutable configuration snapshot.

---

# 165. Runtime logging configuration

AXLOGGING owns configuration.

---

# 166. Runtime observability

AXOBSERVABILITY integration chỉ activate khi enabled.

---

# 167. Runtime audit

Security-relevant runtime events được chuyển AXAUDIT.

---

# 168. Runtime identity

AXIDENTITY cung cấp process/thread identity semantics nếu cần.

AXRUNTIME chỉ giữ handle.

---

# 169. Runtime environment snapshot

Nếu cần reproducibility, runtime có thể capture immutable startup snapshot.

---

# 170. Runtime determinism

Core initialization order phải deterministic.

---

# 171. Randomness

Runtime không dùng random implicit cho:

- object IDs;
- initialization ordering;
- ABI layout.

---

# 172. ASLR

ASLR thuộc AXLOADER/OS.

AXRUNTIME không tự randomize code addresses.

---

# 173. Runtime security initialization

Security enforcement phải được active trước các service có capability-sensitive behavior.

---

# 174. Startup ordering

```text
AXSTARTUP
 ↓
security context
 ↓
runtime core
 ↓
allocator
 ↓
services
 ↓
application
```

Không được để application code chạy trước required security initialization.

---

# 175. Runtime plugin loading

Plugin loading thuộc AXREGISTRY/AXPACKAGE/AXLOADER.

Runtime chỉ cung cấp lifecycle hooks.

---

# 176. Runtime lifecycle hooks

```text
runtime_before_main()
runtime_after_main()
runtime_before_exit()
runtime_after_exit()
```

không expose arbitrary order ngoài contract.

---

# 177. Main invocation

AXRUNTIME không hard-code một signature duy nhất.

Compiler generate adapter từ:

```text
fn main()
fn main(args)
fn main(args, env)
```

hoặc canonical application entry.

---

# 178. Canonical application entry

Runtime nên nhận:

```text
fn __ax_main(ApplicationContext*) -> ExitCode
```

là compiler-generated internal entry.

---

# 179. ApplicationContext

```text
ApplicationContext {
    process
    args
    env
    runtime
}
```

---

# 180. ApplicationContext ownership

Runtime owns context lifetime.

Application receives a borrowed immutable/mutable view according to API.

---

# 181. Main return

Canonical:

```text
ExitCode
```

---

# 182. ExitCode

```text
ExitCode {
    value: i32
}
```

---

# 183. Main panic

If `main` panics:

```text
panic handler
→ shutdown policy
→ process termination
```

---

# 184. Main error

If `main` returns `Result`:

compiler-generated adapter converts:

```text
Ok → exit 0
Err → diagnostic + nonzero exit
```

the exact mapping must be explicit.

---

# 185. GUI applications

GUI application lifecycle thuộc AXAPPLICATION.

AXRUNTIME chỉ bootstrap process/runtime trước AXAPPLICATION.

---

# 186. Server applications

Server runtime có thể keep process alive through AXTASK/AXNETWORK.

---

# 187. Console applications

Không cần GUI runtime.

---

# 188. Static constructors

Avoid implicit C++-style arbitrary static constructors.

---

# 189. Module initialization

Module init records explicit.

---

# 190. Init failure

Initialization failure:

```text
Result/Error
```

hoặc fatal according to phase.

---

# 191. Runtime startup error

Trước application:

```text
runtime_fail_startup(error)
```

---

# 192. Startup diagnostics

Startup failure phải có minimal diagnostics không phụ thuộc full logger.

---

# 193. Runtime ABI table

Canonical runtime ABI:

```text
RuntimeABI {
    version
    fingerprint

    runtime_entry
    runtime_init
    runtime_shutdown

    allocator_api
    panic_api

    thread_api
    task_bridge

    service_api
}
```

---

# 194. ABI compatibility

Runtime caller phải verify:

```text
major
target
AXABI fingerprint
feature requirements
```

---

# 195. Runtime interface table

Có thể sử dụng immutable function table:

```text
RuntimeInterface {
    header
    core
    memory
    thread
    task
    diagnostics
}
```

---

# 196. Interface version

Mỗi interface table:

```text
size
version
flags
```

cho forward compatibility.

---

# 197. Reserved fields

Reserved fields phải zero trong canonical ABI.

---

# 198. Extending interface

Append-only fields được phép trong minor ABI revision.

---

# 199. Runtime ABI compatibility

Consumer chỉ access fields <= advertised `size`.

---

# 200. Runtime service lookup

Service lookup:

```text
runtime_find_service(id, version)
```

trả về interface compatible.

---

# 201. Runtime startup pseudoflow

```text
axiom_runtime_entry(startup)
{
    validate_startup(startup);

    state = runtime_create_state(startup);

    runtime_bootstrap_platform(state);
    runtime_bootstrap_tls(state);
    runtime_bootstrap_allocator(state);

    runtime_load_required_services(state);
    runtime_run_initializers(state);

    result = ax_main(state);

    runtime_run_shutdown(state);

    return runtime_exit(result);
}
```

---

# 202. Runtime must not do

Không được mặc định:

```text
spawn threads
open filesystem
open network
initialize GUI
start scheduler
allocate large heap
start logger
load plugins
```

nếu application không yêu cầu.

---

# 203. Runtime dependency graph

```text
                 AXRUNTIME_CORE
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     MEMORY          THREAD          PANIC
        │              │              │
        └──────┬───────┴──────┬───────┘
               ▼              ▼
             TASK           DIAG
               │
               ▼
             ASYNC
               │
               ▼
               IO
```

Mỗi node có thể được loại bỏ khi unused.

---

# 204. Runtime component ABI

Mỗi component phải declare:

```text
provides[]
requires[]
abi_version
target
```

---

# 205. Link-time dependency validation

AXLINKER phải reject circular runtime dependency không được hỗ trợ.

---

# 206. Runtime component initialization

Mỗi component có:

```text
init()
shutdown()
```

nếu cần.

---

# 207. Component idempotency

Initialization phải không chạy hai lần trên cùng runtime instance.

---

# 208. Thread-safe initialization

Component initialization có thể chạy parallel chỉ nếu dependency graph cho phép.

---

# 209. Deterministic serialization

Runtime manifest phải deterministic.

---

# 210. Runtime reproducibility

Cùng binary + cùng startup environment/config phải tạo cùng runtime initialization ordering.

---

# 211. Runtime performance target

Normal application function calls không được bị runtime dispatcher chặn.

---

# 212. Direct binding

Runtime APIs hot path nên được link trực tiếp:

```text
call runtime_function
```

thay vì generic service lookup mỗi lần.

---

# 213. Service lookup cold path

Dynamic lookup chỉ xảy ra:

- startup;
- plugin load;
- explicit service query.

---

# 214. TLS performance

Current-thread access phải compile xuống native TLS load.

---

# 215. Panic performance

Panic path không tối ưu cho normal execution.

---

# 216. Shutdown performance

Shutdown chỉ chạy khi process kết thúc, không ảnh hưởng steady-state.

---

# 217. Runtime memory footprint

Core state phải nhỏ.

Không giữ global caches lớn nếu không required.

---

# 218. Cache policy

Runtime caches phải explicit component-owned.

---

# 219. Runtime fragmentation

AXRUNTIME không được tạo allocator fragmentation ngoài contract của AXMEMORY.

---

# 220. Runtime scheduler separation

Scheduler state không nằm trong RuntimeState nếu task subsystem disabled.

---

# 221. Runtime task ABI

Task subsystem chỉ cần:

```text
current task handle
scheduler context
cancellation context
```

khi active.

---

# 222. Async bridge

AXRUNTIME cung cấp context transition:

```text
thread
 ↓
task
 ↓
await
 ↓
scheduler
```

---

# 223. Await ABI

Compiler lowers await according to AXASYNC.

AXRUNTIME không hiểu source-level await syntax.

---

# 224. Coroutine state

Coroutine frame ownership thuộc compiler + AXASYNC/AXTASK.

---

# 225. No universal boxed future

Axiom không bắt mọi async result vào heap boxed future.

---

# 226. Runtime and stack growth

Stack management thuộc AXPROCESS/AXTASK/platform.

AXRUNTIME chỉ consume service.

---

# 227. Fiber support

Nếu platform hỗ trợ fibers, AXTASK owns implementation.

---

# 228. Runtime stack switching

AXRUNTIME chỉ expose bridge cần thiết cho task subsystem.

---

# 229. Foreign thread callbacks

Callback vào Axiom:

```text
foreign thread
 ↓
runtime_thread_attach
 ↓
Axiom callback
```

---

# 230. Callback cleanup

Callback trampoline phải không để thread-local runtime state dangling.

---

# 231. Runtime re-entry

Một foreign callback có thể re-enter application nếu ABI cho phép.

Runtime phải maintain thread state correctly.

---

# 232. Deadlock prevention

Core runtime không giữ global runtime lock trong user callback.

---

# 233. User callback isolation

Runtime callback không được gọi user code khi đang giữ internal mutex nếu tránh được.

---

# 234. Error propagation

Runtime service errors không được implicit panic trừ API contract.

---

# 235. Runtime API annotations

API metadata nên có:

```text
@blocking
@allocates
@panic
@thread_safe
@reentrant
@async
```

---

# 236. AI metadata

Runtime API metadata giúp compiler/AI biết:

```text
allocation behavior
blocking behavior
thread safety
ownership
ABI
```

---

# 237. Runtime documentation

`ax runtime inspect` phải hiển thị:

```text
profile
features
ABI
components
allocator
panic mode
TLS mode
```

---

# 238. Runtime introspection

Không yêu cầu reflection runtime.

Inspection có thể sử dụng manifest.

---

# 239. Release build

Production default:

```text
strip debug
strip unused services
strip unused diagnostics
```

---

# 240. Debug build

Debug runtime có thể enable:

- allocation tracking;
- runtime assertions;
- panic stack traces;
- thread diagnostics.

Các tính năng này phải compile-time selectable.

---

# 241. Sanitizer runtime

Sanitizer support là optional runtime component.

---

# 242. Leak detection

Không phải core runtime requirement.

---

# 243. Memory poisoning

Optional debug/diagnostic feature.

---

# 244. Runtime assertions

Core assertions phải có low-cost release-off mode.

---

# 245. Runtime build modes

```text
TINY
RELEASE
DEBUG
SANITIZED
PROFILED
```

---

# 246. Runtime mode compatibility

Debug-only runtime ABI extensions không được accidentally leak vào release ABI.

---

# 247. Runtime package structure

Conceptual:

```text
runtime/
    core/
    memory/
    panic/
    thread/
    task/
    async/
    io/
    diagnostics/
    platform/
```

---

# 248. Platform backend

```text
RuntimePlatformBackend {
    init()
    shutdown()
    thread()
    tls()
    exit()
    emergency_write()
}
```

---

# 249. Windows backend

Hỗ trợ:

- PE64 startup integration;
- TLS;
- thread;
- process exit;
- emergency diagnostics.

---

# 250. Linux backend

Hỗ trợ:

- ELF64;
- TLS;
- pthread/native thread adapter;
- process exit;
- emergency diagnostics.

---

# 251. macOS backend

Hỗ trợ:

- Mach-O;
- TLS;
- thread;
- process lifecycle.

---

# 252. iOS backend

Không assume desktop process lifecycle.

AXAPPLICATION owns app lifecycle.

---

# 253. Android backend

Native runtime startup được AXSTARTUP cung cấp.

Application lifecycle thuộc AXAPPLICATION/Android adapter.

---

# 254. WASM backend

Không có native thread/TLS assumptions trừ khi target profile hỗ trợ.

---

# 255. Freestanding backend

Có thể cung cấp:

```text
startup
exit
memory
panic
```

mà không cần OS.

---

# 256. Embedded

Runtime platform backend có thể được thay thế hoàn toàn.

---

# 257. Runtime portability

Core runtime code không được chứa OS-specific code trực tiếp nếu platform backend có thể isolate.

---

# 258. Platform conditional compilation

```text
@target("windows")
@target("linux")
```

được compiler xử lý.

---

# 259. Runtime linker

Runtime components nên là ordinary AXOBJECT artifacts.

Không cần special linker.

---

# 260. Runtime binary

Có thể build:

```text
libaxiom_runtime.a
axiom_runtime.dll
libaxiom_runtime.so
libaxiom_runtime.dylib
```

nhưng static component linking là baseline.

---

# 261. Dynamic runtime constraints

Dynamic runtime phải có stable ABI.

---

# 262. Static runtime constraints

Static runtime có thể dùng internal ABI optimization.

---

# 263. Runtime symbol visibility

Internal symbols hidden để giảm:

- collision;
- relocation;
- export table;
- attack surface.

---

# 264. Runtime attack surface

Minimal profile phải có attack surface nhỏ nhất.

---

# 265. Runtime untrusted input

Runtime phải coi:

- argv;
- env;
- host imports;
- plugin descriptors;
- external metadata

là untrusted.

---

# 266. Runtime parsing

Không parse external strings với unbounded recursion.

---

# 267. Resource limits

Runtime initialization phải có giới hạn đối với:

- service count;
- init records;
- metadata;
- environment;
- command line.

---

# 268. Runtime service isolation

Service failure không được corrupt RuntimeState.

---

# 269. Runtime failure containment

Nếu optional service init fails:

```text
optional feature disabled
```

nếu contract cho phép.

Required service failure:

```text
startup failure
```

---

# 270. Runtime corruption detection

RuntimeState có thể có debug magic/version.

Release có thể strip expensive checks.

---

# 271. Runtime ABI checksum

Optional lightweight checksum cho debug/diagnostics.

---

# 272. Runtime object lifetime

RuntimeState:

```text
process lifetime
```

Service state:

```text
service lifetime
```

Thread state:

```text
thread lifetime
```

Task state:

```text
task lifetime
```

---

# 273. No hidden ownership

Runtime không tự giữ arbitrary user objects.

---

# 274. Runtime callback registry

Nếu tồn tại, callback entries phải có explicit lifetime.

---

# 275. Callback removal

Removal phải tránh callback đang chạy bị use-after-free.

---

# 276. Runtime atomic operations

Dùng AXMEMORY/atomic primitives.

---

# 277. Lock-free policy

Không tuyên bố lock-free nếu target ABI/hardware không guarantee.

---

# 278. Runtime portability tests

Mọi platform backend phải pass core runtime conformance suite.

---

# 279. Runtime synthetic startup tests

Có thể tạo `StartupState` giả để test mà không boot process thật.

---

# 280. Runtime fault injection

Test:

```text
allocator failure
service init failure
TLS failure
thread attach failure
panic during init
shutdown failure
```

---

# 281. Runtime fuzzing

Fuzz:

- manifests;
- service descriptors;
- initialization graphs;
- startup state adapters;
- runtime ABI metadata.

---

# 282. Runtime stress testing

Test:

```text
many threads
many task attach/detach
repeated service access
panic under load
shutdown under concurrency
```

---

# 283. Runtime race testing

Thread/TLS/service state phải được race-tested.

---

# 284. Runtime deterministic test

Repeated startup với cùng synthetic state phải produce same initialization sequence.

---

# 285. Bootstrap test

```text
Stage0
 ↓
AXRUNTIME
 ↓
Stage1 compiler
 ↓
Stage2 compiler
```

phải pass.

---

# 286. Minimal executable test

Phải tạo được executable chỉ với:

```text
AXSTARTUP
AXABI
AXRUNTIME_CORE
main
```

---

# 287. No-libc test

Phải có test profile build native executable không phụ thuộc libc/CRT khi platform cho phép.

---

# 288. No-heap test

Program chỉ stack/static memory phải link/run không có allocator initialization.

---

# 289. No-thread test

Console hello-world không được kéo task/thread subsystem.

---

# 290. No-I/O-runtime test

Program computation-only không được kéo filesystem/network.

---

# 291. Size regression

Build system phải track runtime component size.

---

# 292. Startup latency regression

Benchmark:

```text
process start
→ main
```

cho minimal/core/full profiles.

---

# 293. Runtime overhead

Steady-state application code không được chịu runtime dispatch overhead ngoài explicit API calls.

---

# 294. Runtime profile benchmark

So sánh:

```text
MINIMAL
CORE
STANDARD
FULL
```

về:

- binary size;
- startup latency;
- memory footprint.

---

# 295. Runtime ABI golden symbols

Canonical symbols phải được kiểm tra bằng AXOBJECT/AXLINKER.

---

# 296. Runtime binary compatibility

Old runtime + compatible application phải pass ABI compatibility tests.

---

# 297. Runtime incompatibility

Mismatched ABI phải fail deterministic.

---

# 298. Runtime self-hosting

AXRUNTIME core phải eventually được compile bởi Axiom compiler itself.

---

# 299. Formal invariants

```text id="d4x5r1"
RUNTIME-INV-01
AXRUNTIME phải có runtime entry rõ ràng sau AXSTARTUP.

RUNTIME-INV-02
AXRUNTIME không được thay thế AXSTARTUP.

RUNTIME-INV-03
AXRUNTIME không được yêu cầu GC.

RUNTIME-INV-04
AXRUNTIME không được yêu cầu borrow checker runtime.

RUNTIME-INV-05
AXRUNTIME không được tạo OS thread cho mỗi task.

RUNTIME-INV-06
AXRUNTIME core không được bắt buộc heap.

RUNTIME-INV-07
Runtime profile phải xác định feature set.

RUNTIME-INV-08
Unused runtime features phải có khả năng loại bỏ khỏi binary.

RUNTIME-INV-09
Runtime initialization phải deterministic.

RUNTIME-INV-10
Runtime initialization phải tuân dependency ordering.

RUNTIME-INV-11
Initialization cycle phải được phát hiện.

RUNTIME-INV-12
RuntimeState phải có stable versioned representation.

RUNTIME-INV-13
Runtime ABI phải có major/minor identity.

RUNTIME-INV-14
Runtime ABI mismatch không được chạy silently.

RUNTIME-INV-15
Allocator interface phải explicit.

RUNTIME-INV-16
Allocator ownership crossing module boundary phải explicit.

RUNTIME-INV-17
Runtime không được đồng nhất Axiom allocator với libc allocator.

RUNTIME-INV-18
TLS runtime state phải thread-local.

RUNTIME-INV-19
External thread phải attach trước khi sử dụng required thread-local runtime state.

RUNTIME-INV-20
Thread attach/detach phải deterministic.

RUNTIME-INV-21
Panic path phải có allocation-independent fallback.

RUNTIME-INV-22
Recursive panic phải terminate an toàn.

RUNTIME-INV-23
Panic không được tự động xuyên incompatible FFI boundary.

RUNTIME-INV-24
Runtime error không được implicit panic nếu API không quy định.

RUNTIME-INV-25
Runtime core không được giữ global lock trong normal hot path.

RUNTIME-INV-26
Service lookup phải có version/ABI validation.

RUNTIME-INV-27
Runtime service registration không được bypass AXSECURITY.

RUNTIME-INV-28
Runtime không được tự grant capability.

RUNTIME-INV-29
Crash path phải có minimal fallback khi AXDIAGNOSTICS unavailable.

RUNTIME-INV-30
Crash path không được phụ thuộc lock có thể đang bị giữ.

RUNTIME-INV-31
Runtime shutdown phải có state machine deterministic.

RUNTIME-INV-32
Shutdown không được chạy hai lần trên cùng runtime instance.

RUNTIME-INV-33
WASM runtime không được giả định native OS process semantics.

RUNTIME-INV-34
Freestanding runtime không được yêu cầu OS services.

RUNTIME-INV-35
Runtime component dependencies phải được linker validate.

RUNTIME-INV-36
Runtime metadata phải deterministic.

RUNTIME-INV-37
Runtime external metadata phải được parse như untrusted input.

RUNTIME-INV-38
Runtime hot path phải tránh hidden allocation và unnecessary dispatch.

RUNTIME-INV-39
Runtime phải có minimal/no-libc/no-heap/no-thread conformance profiles khi target hỗ trợ.

RUNTIME-INV-40
AXRUNTIME chỉ là runtime integration layer; scheduler, memory model, security policy, OS process semantics và subsystem ownership vẫn thuộc các subsystem chuyên biệt.
```

---

# 300. Definition of Done

`AXRUNTIME 5.0` được freeze khi:

### Core

- runtime entry;
- RuntimeState;
- initialization state machine;
- shutdown state machine;
- runtime profiles;
- runtime feature graph;
- runtime ABI;
- service registry;
- platform backend.

### Memory

- allocator bridge;
- allocator replacement;
- ownership boundary;
- no-heap profile;
- allocator failure handling.

### Execution

- main-thread state;
- TLS;
- external-thread attach;
- panic;
- trap;
- abort;
- error propagation;
- exit.

### Concurrency

- thread runtime bridge;
- task bridge;
- async bridge;
- no-thread-per-task guarantee;
- thread-safe initialization.

### Platform

- Windows PE64;
- Linux ELF64;
- macOS Mach-O;
- iOS;
- Android;
- WASM32;
- freestanding.

### Toolchain

- AXABI integration;
- AXOBJECT metadata;
- AXLINKER component elimination;
- AXLOADER integration;
- AXSTARTUP handoff;
- AXBUILD runtime feature graph.

### Reliability

- startup failure;
- shutdown failure;
- recursive panic;
- crash path;
- fault injection;
- fuzzing;
- race testing;
- deterministic initialization.

### Performance

- minimal binary;
- no-libc profile;
- no-heap profile;
- no-thread profile;
- startup benchmark;
- runtime-size regression;
- hot-path benchmark.

### Bootstrap

```text
Stage0
  ↓
AXSTARTUP
  ↓
AXABI
  ↓
AXRUNTIME
  ↓
Stage1 Axiom compiler
  ↓
Stage2 Axiom compiler
  ↓
self-hosted
```

**AXRUNTIME 5.0 → FROZEN.**

---

# Kiến trúc đã hoàn thiện tới đây

```text
        SOURCE
          │
          ▼
     AXCOMPILER
          │
          ▼
       AXABI
          │
          ▼
      AXOBJECT
          │
          ▼
      AXLINKER
          │
          ▼
      AXBINARY
          │
          ▼
      AXLOADER
          │
          ▼
     AXSTARTUP
          │
          ▼
      AXRUNTIME
          │
     ┌────┼───────────────┐
     ▼    ▼               ▼
  AXMEMORY AXTASK      AXPROCESS
     │      │               │
     │    AXASYNC            │
     │      │               │
     └──────┼───────────────┘
            ▼
       APPLICATION
```

Điểm kiến trúc quan trọng của `AXRUNTIME` là **Axiom giờ đã có thể xây executable native mà runtime không còn là một khối bắt buộc**. Một chương trình rất nhỏ có thể chỉ kéo `AXSTARTUP + AXABI + AXRUNTIME_CORE`; trong khi ứng dụng GUI/server lớn mới kéo thêm task, async, I/O, diagnostics và các subsystem tương ứng.

---

# BOOTSTRAP-781 — AXSTANDARD

**Native Axiom Standard Runtime Library, Core Collections, String/UTF-8, Option/Result/Error, Iteration, Algorithms, Math, Formatting, Parsing, Conversion, Time/Random Facades, File/Path Facades & Zero-Cost Standard Library Architecture 5.0**

Đây là lớp tiếp theo hợp lý: `AXRUNTIME` đã cung cấp **runtime mechanism**, nhưng chưa cung cấp **thư viện chuẩn mà lập trình viên sử dụng hàng ngày**. `AXSTANDARD` sẽ định nghĩa standard library theo nguyên tắc quan trọng của Axiom: **API phong phú nhưng không biến mọi chương trình thành một executable khổng lồ và không tạo hidden runtime cost**.