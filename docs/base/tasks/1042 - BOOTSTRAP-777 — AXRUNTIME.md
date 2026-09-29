# BOOTSTRAP-777 — AXRUNTIME

**Title:** Native Axiom Runtime Core, Process Startup, Runtime ABI, Panic/Trap, Global Initialization, TLS Runtime, Allocation Hooks, Stack/Unwind Boundary, Shutdown, Minimal Runtime & Zero-Cost Runtime Architecture 5.0  
**Namespace:** `AXRUNTIME`  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXRUNTIME` là lớp runtime native tối thiểu của Axiom, nằm giữa **OS/process activation** và **application code**.

```text
AXBINARY
   ↓
AXLOADER
   ↓
AXPROCESS
   ↓
┌─────────────────────────────┐
│          AXRUNTIME          │
│                             │
│ startup                     │
│ runtime ABI                 │
│ panic / trap                │
│ TLS                         │
│ global initialization       │
│ allocator hooks             │
│ unwind boundary             │
│ shutdown                    │
└──────────────┬──────────────┘
               ↓
        Axiom Application
```

Mục tiêu quan trọng:

> **AXRUNTIME không phải một “fat runtime” bắt buộc mọi chương trình phải mang theo.**

Compiler phải có khả năng loại bỏ hoàn toàn những phần runtime không được sử dụng.

---

# 2. Triết lý thiết kế

Axiom runtime tuân theo 5 nguyên tắc:

```text
1. Explicit
2. Deterministic
3. Zero-cost when unused
4. Native ABI
5. Minimal hidden behavior
```

Không có:

- mandatory garbage collector;
- mandatory VM;
- mandatory object runtime;
- mandatory reflection runtime;
- mandatory scheduler;
- mandatory exception runtime.

---

# 3. Runtime dependency model

```text
                    AXRUNTIME
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    CORE STARTUP     MEMORY         DIAGNOSTICS
        │              │              │
        ▼              ▼              ▼
      TLS            ALLOCATOR       UNWIND
        │
        ▼
     PANIC/TRAP
```

Các module khác chỉ được link nếu thực sự cần.

---

# 4. Runtime tiers

AXRUNTIME được chia thành 4 tier.

```text
TIER 0
Freestanding
```

Không runtime services.

```text
TIER 1
Minimal Native
```

Startup + basic panic/trap + TLS.

```text
TIER 2
System Runtime
```

Memory, threading, async, IO integration.

```text
TIER 3
Full Axiom Runtime
```

Diagnostics, observability, advanced services.
    
---

# 5. TIER 0 — Freestanding

Axiom phải hỗ trợ:

```text
@freestanding
```

ứng dụng không cần AXRUNTIME implementation.

Compiler cung cấp entry symbol trực tiếp.

---

# 6. TIER 1

Ứng dụng thông thường:

```text
OS
 ↓
startup
 ↓
AXRUNTIME
 ↓
main()
```

Runtime footprint mục tiêu rất nhỏ.

---

# 7. TIER 2

Khi dùng:

- dynamic memory;
- threads;
- tasks;
- async;
- filesystem;
- network;

runtime kéo theo các component cần thiết.

---

# 8. TIER 3

Ứng dụng production có thể enable:

```text
diagnostics
profiling
tracing
structured logging
crash reporting
```

---

# 9. Runtime ABI

Đóng băng:

```text
AXRUNTIME_ABI_1
```

ABI này là contract giữa:

```text
AXCOMPILER
AXLOADER
AXPROCESS
AXRUNTIME
```

---

# 10. Runtime ABI không phải language ABI

Phân biệt:

```text
Axiom Language ABI
→ function/type calling semantics

AXRUNTIME_ABI
→ runtime service interface
```

---

# 11. Runtime context

```text
RuntimeContext {
    process
    main_thread
    memory
    tls
    allocator?
    diagnostics?
    scheduler?
    config?
}
```

---

# 12. Runtime initialization state

```text
UNINITIALIZED
      ↓
BOOTSTRAPPING
      ↓
INITIALIZED
      ↓
RUNNING
      ↓
SHUTTING_DOWN
      ↓
TERMINATED
```

---

# 13. Runtime startup

Canonical sequence:

```text
OS
 ↓
AXPROCESS
 ↓
AXLOADER
 ↓
runtime_entry
 ↓
runtime_bootstrap
 ↓
TLS setup
 ↓
global initialization
 ↓
application_main
```

---

# 14. Runtime entry

Compiler generates:

```text
axiom_runtime_entry
```

hoặc target-equivalent entry wrapper.

---

# 15. OS entry versus Axiom entry

```text
OS entry
   ↓
platform startup
   ↓
Axiom runtime entry
   ↓
user main
```

User `main()` không cần biết OS-specific startup ABI.

---

# 16. Main signature

Axiom chuẩn hóa application entry:

```text
fn main() -> i32
```

hoặc:

```text
fn main(args: Args, env: Env) -> i32
```

Compiler/runtime chịu trách nhiệm adapter.

---

# 17. Return value

`main()` return:

```text
i32
```

được chuyển thành process exit status.

---

# 18. Main không return

Nếu `main` là:

```text
fn main() -> Never
```

runtime không thực hiện implicit return.

---

# 19. Startup arguments

Runtime tạo:

```text
Args
```

từ OS process arguments.

---

# 20. Environment

Runtime tạo:

```text
Env
```

theo explicit API.

Không tự động copy toàn bộ environment nếu application không sử dụng.

---

# 21. Startup memory

Runtime startup tránh allocation nếu có thể.

---

# 22. Bootstrap allocator

Trong giai đoạn rất sớm:

```text
static bootstrap storage
```

có thể được sử dụng.

Sau allocator chính:

```text
bootstrap
   ↓
retire
```

---

# 23. Global initialization

Axiom cho phép:

```text
static initialization
```

nhưng phải có semantics deterministic.

---

# 24. Constant initialization

Ưu tiên:

```text
compile-time initialization
```

để tránh runtime work.

Ví dụ:

```text
const table = [...]
```

được đặt trực tiếp trong binary.

---

# 25. Dynamic initialization

Chỉ khi initializer không thể evaluate tại compile time.

---

# 26. Init table

Binary có thể chứa:

```text
runtime_init_table
```

với function pointers và dependency metadata.

---

# 27. Init order

Order:

```text
runtime core
 ↓
module dependencies
 ↓
global initialization
 ↓
main
```

---

# 28. Destruction

Global cleanup không được đảm bảo cho mọi process termination mode.

Có hai loại:

```text
NORMAL_EXIT
ABORT / CRASH
```

---

# 29. Normal shutdown

```text
main
 ↓
global cleanup
 ↓
TLS cleanup
 ↓
runtime shutdown
 ↓
process exit
```

---

# 30. Crash shutdown

Không chạy arbitrary destructors.

Thay vào đó:

```text
panic/trap
 ↓
diagnostics
 ↓
minimal cleanup
 ↓
process termination
```

---

# 31. Panic model

Axiom không yêu cầu C++-style exceptions.

Core panic:

```text
panic(message)
```

---

# 32. Panic semantics

Panic có thể:

```text
ABORT
UNWIND
RECOVER
```

nhưng `RECOVER` chỉ tồn tại nếu explicit runtime feature được link.

---

# 33. Default panic

Mặc định:

```text
panic
 ↓
diagnostic
 ↓
terminate
```

---

# 34. Why no mandatory exceptions

Axiom tránh hidden cost:

- exception tables;
- hidden stack unwinding;
- implicit allocation;
- implicit catch scopes.

---

# 35. Result/Error preferred

Recoverable failures dùng:

```text
Result<T, E>
```

hoặc equivalent error values.

---

# 36. Panic versus Result

```text
Result
→ expected/recoverable failure

panic
→ violated invariant / unrecoverable execution state
```

---

# 37. Trap

Low-level runtime trap:

```text
trap(code)
```

---

# 38. Trap classes

```text
DIVIDE_BY_ZERO
INVALID_CAST
OUT_OF_BOUNDS
NULL_ACCESS
UNREACHABLE
STACK_OVERFLOW
ILLEGAL_INSTRUCTION
ASSERTION_FAILURE
USER_PANIC
```

---

# 39. Trap behavior

Compiler may lower safety checks:

```text
bounds check
 ↓
trap
```

when optimization cannot prove safety.

---

# 40. Bounds-check elimination

Compiler should eliminate checks when statically provable.

Thus runtime trap path is cold.

---

# 41. Panic payload

```text
PanicInfo {
    code
    message?
    source_location?
    function?
    module?
    stack?
}
```

---

# 42. Panic allocation

Panic path must not require heap allocation.

---

# 43. Emergency panic buffer

Runtime maintains optional fixed-size emergency buffer.

---

# 44. Recursive panic

Nếu panic xảy ra trong panic handler:

```text
second panic
 ↓
minimal terminate
```

Không recurse vô hạn.

---

# 45. Panic hook

Application có thể đăng ký:

```text
set_panic_handler()
```

nếu runtime feature được link.

---

# 46. Handler safety

Panic handler không được mặc định giả định:

- heap hoạt động;
- locks available;
- scheduler hoạt động;
- filesystem hoạt động.

---

# 47. Stack boundary

AXRUNTIME không sở hữu native stack allocator chính.

AXPROCESS/OS owns thread stack.

---

# 48. Stack overflow

Nếu platform có guard page:

```text
guard page
 ↓
fault
 ↓
AXRUNTIME diagnostic
```

---

# 49. Stack probing

Compiler chịu trách nhiệm stack probing khi target ABI yêu cầu.

AXRUNTIME cung cấp failure handling.

---

# 50. Unwind model

Axiom hỗ trợ hai mode:

```text
NO_UNWIND
UNWIND
```

---

# 51. NO_UNWIND

Minimal executable:

```text
panic → trap → terminate
```

Không cần unwind metadata nếu target không yêu cầu.

---

# 52. UNWIND

Nếu diagnostics/exceptions cần stack walking:

```text
code
+
unwind metadata
```

được generated by compiler/linker.

---

# 53. Runtime unwind API

```text
runtime_unwind_begin()
runtime_unwind_next()
runtime_unwind_end()
```

---

# 54. Unwind ownership

```text
AXCOMPILER
→ generate unwind metadata

AXBINARY
→ carry metadata

AXLOADER
→ register loaded ranges

AXRUNTIME
→ consume unwind information
```

---

# 55. TLS runtime

AXLOADER tạo module TLS.

AXRUNTIME quản lý:

```text
current thread TLS
```

---

# 56. TLS access

Compiler có thể lower:

```text
thread_local x
```

thành target TLS access sequence.

---

# 57. TLS runtime fallback

Nếu target cannot directly encode desired TLS model, runtime helper may be emitted.

---

# 58. TLS API

```text
tls_current()
tls_get(module_id)
tls_set(module_id, value)
tls_thread_attach()
tls_thread_detach()
```

---

# 59. TLS performance

Static TLS phải ưu tiên direct target instructions.

Generic lookup chỉ dùng dynamic TLS.

---

# 60. Thread startup

AXTASK/AXPROCESS tạo thread.

Sequence:

```text
OS thread
 ↓
runtime_thread_entry
 ↓
TLS attach
 ↓
thread-local initialization
 ↓
user thread function
 ↓
TLS detach
```

---

# 61. Thread-local destructor

Chỉ chạy nếu normal thread termination.

Crash path không guarantee destructor execution.

---

# 62. Allocator boundary

AXRUNTIME không bắt buộc một allocator cụ thể.

---

# 63. Allocation API

```text
runtime_alloc(size, align)
runtime_realloc(ptr, old_size, new_size, align)
runtime_free(ptr, size, align)
```

---

# 64. Size-aware free

Axiom ưu tiên:

```text
free(ptr, size, align)
```

khi compiler có size information.

Điều này giảm metadata overhead.

---

# 65. Allocator selection

```text
system
arena
pool
custom
```

có thể được chọn explicit.

---

# 66. No mandatory global heap

Freestanding application không cần global heap.

---

# 67. Zero allocation

Code chỉ sử dụng:

- stack;
- static storage;
- fixed buffers;

không kéo AXRUNTIME allocator.

---

# 68. Allocation failure

Không mặc định panic.

API có thể trả:

```text
Option
Result
```

depending on allocator contract.

---

# 69. OOM policy

Application có thể chọn:

```text
RETURN_ERROR
PANIC
TERMINATE
```

---

# 70. Runtime allocator hooks

Compiler/runtime cần internal hooks:

```text
runtime_alloc_hook
runtime_free_hook
```

nhưng không nên tạo dynamic dispatch trên normal allocation path.

---

# 71. Memory ownership

AXRUNTIME không thay thế AXMEMORY ownership model.

---

# 72. Scheduler

AXRUNTIME không mặc định tạo scheduler.

Scheduler thuộc:

```text
AXTASK / AXASYNC
```

---

# 73. Async runtime

Khi async được sử dụng:

```text
AXASYNC
 ↓
AXTASK
 ↓
AXRUNTIME services
```

---

# 74. Runtime scheduler initialization

Chỉ initialize scheduler khi executable thực sự chứa task/async.

---

# 75. IO runtime

IO primitive thuộc subsystem tương ứng.

AXRUNTIME chỉ cung cấp startup/runtime ABI hooks.

---

# 76. Logging

AXRUNTIME không embed full logging subsystem.

Nếu cần:

```text
AXLOGGING
```

được link.

---

# 77. Diagnostics

Tương tự:

```text
AXDIAGNOSTICS
```

là optional runtime component.

---

# 78. Observability

Không được tự động kéo tracing/metrics vào tiny binaries.

---

# 79. Runtime feature manifest

Compiler/linker xác định:

```text
RuntimeFeatures {
    tls
    allocator
    panic
    unwind
    diagnostics
    threading
    async
    logging
    observability
}
```

---

# 80. Runtime linking

```text
application
   ↓
runtime feature discovery
   ↓
dead-strip unused features
   ↓
minimal runtime image
```

---

# 81. Runtime component ABI

Các component giao tiếp qua:

```text
AXRUNTIME_ABI_1
```

không qua C++ ABI.

---

# 82. Runtime versioning

```text
major
minor
patch
```

Major mismatch → load failure.

---

# 83. Runtime compatibility

Application có thể declare:

```text
requires AXRUNTIME_ABI >= 1.0
```

---

# 84. Freestanding API

Freestanding application chỉ được gọi services explicit.

Ví dụ:

```text
syscall(...)
trap(...)
```

---

# 85. Syscall boundary

AXRUNTIME không giả lập kernel.

```text
Axiom API
 ↓
AX subsystem
 ↓
platform adapter
 ↓
OS syscall
```

---

# 86. Platform adapters

```text
runtime/windows
runtime/linux
runtime/macos
runtime/ios
runtime/android
runtime/wasm
```

---

# 87. Windows runtime

Có thể cung cấp:

- PE startup adapter;
- TLS adapter;
- SEH integration;
- process exit adapter.

---

# 88. Linux runtime

Có thể cung cấp:

- ELF startup adapter;
- TLS;
- signal/trap;
- pthread/native thread integration.

---

# 89. macOS/iOS runtime

Có thể cung cấp:

- Mach-O startup;
- dyld interaction;
- TLS;
- platform exception/unwind integration.

---

# 90. Android

Runtime target:

```text
AArch64
+
ELF64
+
Android ABI
```

---

# 91. WASM runtime

WASM runtime không expose native process startup semantics.

Thay vào đó:

```text
instantiate
→ start
→ exported calls
```

---

# 92. Runtime process identity

AXRUNTIME lấy process identity từ AXPROCESS.

Không tự duy trì process lifecycle.

---

# 93. Exit API

```text
runtime_exit(code)
runtime_abort(code)
```

---

# 94. Exit semantics

`runtime_exit()`:

- chạy normal runtime shutdown;
- flush các runtime facilities theo policy;
- trả status.

`runtime_abort()`:

- bỏ qua normal cleanup;
- terminate nhanh.

---

# 95. Quick termination

Cho crash/emergency:

```text
runtime_terminate_fast(code)
```

không phụ thuộc allocator/scheduler.

---

# 96. Atexit equivalent

Axiom không khuyến khích global arbitrary callback registry.

Nếu cần:

```text
runtime_on_exit()
```

phải có deterministic ordering.

---

# 97. Exit callback ordering

LIFO đối với callbacks cùng scope.

Module dependencies vẫn quyết định module-level finalization.

---

# 98. Resource ownership

Runtime resource cleanup phải explicit hoặc scope-bound.

Không dùng hidden GC để tìm resource.

---

# 99. File descriptors

AXRUNTIME không tự close arbitrary user handles khi process exit.

OS sẽ reclaim process resources.

---

# 100. Crash semantics

OS reclaim memory/resources sau process termination.

Do đó crash path ưu tiên:

```text
diagnostic integrity
```

thay vì cleanup completeness.

---

# 101. Runtime startup error

Nếu startup fail trước `main`:

```text
runtime_bootstrap()
 ↓
RuntimeError
 ↓
diagnostics
 ↓
exit
```

---

# 102. Startup diagnostics

Không phụ thuộc application logger.

---

# 103. Runtime panic output

Minimal fallback có thể ghi:

```text
panic code
module
address
source location if available
```

---

# 104. Debug build

Có thể bật:

```text
runtime assertions
heap checks
stack checks
diagnostic hooks
```

---

# 105. Release build

Compiler phải loại bỏ diagnostic code không được yêu cầu.

---

# 106. Runtime configuration

Runtime configuration lấy từ:

```text
AXCONFIG
```

nhưng startup phải có defaults compile-time.

---

# 107. Environment-sensitive runtime

Không được làm binary behavior nondeterministic ngoài các nguồn được khai báo.

---

# 108. Deterministic mode

Runtime hỗ trợ:

```text
deterministic startup
```

cho tests/reproducible execution.

---

# 109. Time dependency

Runtime không tự lấy wall clock trong core startup trừ khi feature yêu cầu.

---

# 110. Random dependency

Runtime không tự initialize RNG subsystem nếu không cần.

---

# 111. Global runtime singleton

Không bắt buộc một global heap object.

Runtime context có thể nằm trong static storage.

---

# 112. Static runtime state

Core runtime state nên dùng:

```text
static immutable
```

hoặc:

```text
static atomic
```

khi có thể.

---

# 113. Reentrancy

Core APIs phải được phân loại:

```text
REENTRANT
THREAD_SAFE
THREAD_LOCAL
SINGLE_THREAD_ONLY
STARTUP_ONLY
SHUTDOWN_ONLY
```

---

# 114. Runtime lock

Không có global runtime lock trong normal application execution.

---

# 115. Panic lock

Panic handler không phụ thuộc mutex nếu có thể.

---

# 116. Allocator concurrency

Allocator implementation tự quyết định synchronization.

AXRUNTIME ABI không ép một locking strategy.

---

# 117. Atomic runtime primitives

Compiler cung cấp atomic operations.

AXRUNTIME chỉ cung cấp fallback helper khi target yêu cầu.

---

# 118. CPU feature initialization

Không probe toàn bộ CPU trong startup.

Chỉ probe khi:

```text
runtime feature
```

yêu cầu.

---

# 119. SIMD

Compiler-generated CPU dispatch ưu tiên static target features.

Dynamic dispatch là optional.

---

# 120. Runtime dispatch

Không được biến mọi runtime function thành indirect call.

---

# 121. Inline runtime functions

Các primitive nhỏ nên có compiler intrinsic equivalent:

```text
likely()
unreachable()
trap()
atomic()
memory_barrier()
```

---

# 122. Compiler/runtime cooperation

Compiler có thể recognize:

```text
runtime_alloc
runtime_panic
runtime_trap
runtime_tls
```

và inline/lower trực tiếp.

---

# 123. Runtime intrinsic boundary

```text
language primitive
 ↓
compiler lowering
 ↓
target instruction
```

ưu tiên hơn:

```text
language primitive
 ↓
generic runtime function
```

---

# 124. Example: trap

Nếu target hỗ trợ trực tiếp:

```text
unreachable
```

compiler emit instruction trực tiếp.

Không cần runtime function.

---

# 125. Example: memcpy

Small fixed-size copy:

```text
compiler → inline instructions
```

Large/dynamic copy:

```text
compiler → optimized runtime helper
```

---

# 126. Runtime helper ABI

Helpers có canonical signatures.

Ví dụ:

```text
__ax_memcpy
__ax_memmove
__ax_memset
__ax_memcmp
```

---

# 127. Helper replacement

AXRUNTIME helper có thể được target backend thay thế bằng optimized implementation.

---

# 128. No libc requirement

Axiom-native program không bắt buộc link libc để thực hiện core runtime operations.

---

# 129. C interoperability

Khi gọi C ABI:

```text
Axiom
 ↓
C ABI
 ↓
system library
```

là explicit FFI.

---

# 130. Runtime/libc separation

AXRUNTIME không giả định libc tồn tại.

Nếu target platform runtime dùng libc internally, đó là platform adapter detail.

---

# 131. Native startup object

AXLINKER có thể include:

```text
axiom_startup.o
```

nhưng Axiom cuối cùng có thể generate startup machine code trực tiếp.

---

# 132. Startup elimination

Freestanding:

```text
no startup object
```

nếu binary entry trực tiếp.

---

# 133. Runtime footprint

Mục tiêu:

> Runtime footprint tỷ lệ với feature sử dụng, không tỷ lệ với toàn bộ Axiom platform.

---

# 134. Link-time dead stripping

Mọi runtime component phải có symbol-level granularity đủ nhỏ để dead-strip.

---

# 135. Section layout

Runtime components nên đặt vào:

```text
.ax.runtime.*
```

hoặc canonical target sections.

---

# 136. Runtime metadata

Binary có thể chứa:

```text
RuntimeManifest {
    abi
    features
    version
}
```

---

# 137. Runtime manifest

Không bắt buộc runtime parser ở production nếu linker đã resolve mọi dependency.

---

# 138. Static runtime

Một executable có thể statically embed runtime components.

---

# 139. Shared runtime

Optional shared AX runtime:

```text
axiom-runtime.dll
libaxiom-runtime.so
libaxiom-runtime.dylib
```

nhưng không phải requirement của Axiom ABI.

---

# 140. ABI stability

Static runtime embedding tránh runtime-version conflicts.

---

# 141. Shared runtime compatibility

Nếu dùng shared runtime:

```text
application ABI
+
runtime ABI
```

phải được validate.

---

# 142. Runtime security

Runtime không tự bypass:

```text
AXCAPABILITY
AXPOLICY
AXSECURITY
```

---

# 143. Runtime trust

Runtime binary itself có thể chịu AXTRUST policy khi platform yêu cầu.

---

# 144. Runtime sandbox

Sandboxed process chỉ nhận capabilities được cấp.

---

# 145. Runtime handles

OS resources dùng opaque handles.

Không expose raw kernel object internals.

---

# 146. Error model

Runtime functions dùng:

```text
Result<T, RuntimeError>
```

ở public fallible API.

Internal hot-path helpers có thể dùng sentinel/status.

---

# 147. RuntimeError

```text
RuntimeError {
    domain
    code
    detail
}
```

---

# 148. Runtime domains

```text
STARTUP
MEMORY
TLS
PANIC
THREAD
ASYNC
IO
PROCESS
PLATFORM
```

---

# 149. Runtime testing

Test matrix:

```text
freestanding
minimal
full runtime
```

---

# 150. Startup tests

Kiểm tra:

- empty main;
- arguments;
- environment;
- return codes;
- static initialization;
- TLS;
- panic;
- exit.

---

# 151. Memory tests

Kiểm tra:

- allocation;
- free;
- alignment;
- realloc;
- OOM;
- zero-size;
- large allocation.

---

# 152. TLS tests

Kiểm tra:

- main thread;
- child threads;
- dynamic modules;
- initialization;
- cleanup;
- concurrent access.

---

# 153. Panic tests

Kiểm tra:

- panic;
- nested panic;
- trap;
- stack overflow;
- invalid bounds;
- emergency path.

---

# 154. Unwind tests

Kiểm tra:

```text
function
 ↓
nested function
 ↓
panic
 ↓
stack walk
```

trên từng target ABI.

---

# 155. Determinism tests

Cùng binary/config:

```text
same startup state
same initialization order
```

ngoại trừ explicitly nondeterministic resources.

---

# 156. Concurrency tests

Kiểm tra:

- simultaneous startup helpers;
- TLS;
- allocator;
- panic races;
- shutdown races.

---

# 157. Reentrancy tests

Panic handler gọi runtime API.

Initializer gọi module loader.

Runtime phải không deadlock.

---

# 158. Fuzzing

Fuzz:

- panic payload;
- runtime manifest;
- startup metadata;
- TLS metadata;
- allocator API parameters;
- unwind metadata.

---

# 159. ABI tests

Mỗi release chạy:

```text
AXRUNTIME_ABI_1 compatibility suite
```

---

# 160. Bootstrap test

```text
Stage0 runtime
 ↓
Stage1 Axiom runtime
 ↓
Stage2 self-hosted runtime
```

Kết quả phải tương thích ABI.

---

# 161. Minimal executable test

Một chương trình:

```text
fn main() -> i32 {
    return 0;
}
```

phải có khả năng build với runtime footprint tối thiểu.

---

# 162. Freestanding test

```text
@freestanding
```

không kéo AXRUNTIME dynamic facilities.

---

# 163. Allocator-free test

Program không allocation → allocator component không xuất hiện trong final image.

---

# 164. Panic-free test

Program không panic → panic formatting machinery không xuất hiện nếu compiler chứng minh không cần.

---

# 165. TLS-free test

Program không TLS → TLS runtime component không được link.

---

# 166. Diagnostics-free test

Release program không diagnostics → không kéo full AXDIAGNOSTICS.

---

# 167. Async-free test

Program không async → không scheduler.

---

# 168. Runtime graph

Compiler/build system có thể generate:

```text
runtime dependency graph
```

để linker dead-strip chính xác.

---

# 169. Runtime symbol naming

Internal symbols dùng reserved namespace:

```text
__ax_
```

hoặc canonical mangling được AXCOMPILER định nghĩa.

---

# 170. User symbol collision

User code không được tạo symbol reserved namespace trong safe language mode.

---

# 171. Internal ABI

Private runtime helpers có thể thay đổi giữa builds nếu không exported.

---

# 172. Public ABI

Chỉ symbols thuộc:

```text
AXRUNTIME_ABI_1
```

được stability guarantee.

---

# 173. Runtime API

Canonical:

```text
runtime_init()
runtime_shutdown()

runtime_exit(code)
runtime_abort(code)
runtime_terminate_fast(code)

runtime_panic(info)
runtime_trap(code)

runtime_alloc(size, align)
runtime_realloc(...)
runtime_free(...)

runtime_tls_current()
runtime_tls_attach()
runtime_tls_detach()

runtime_unwind_begin()
runtime_unwind_next()
runtime_unwind_end()

runtime_register_init()
runtime_register_exit()

runtime_version()
runtime_features()
```

---

# 174. Startup API

```text
runtime_entry(platform_startup)
runtime_bootstrap(context)
runtime_start_main(main_fn, args, env)
```

---

# 175. Runtime feature query

```text
runtime_has_feature(feature)
```

chỉ nên dùng cho runtime tooling/diagnostics.

Compiler không nên dùng runtime query cho những thứ có thể resolve compile-time.

---

# 176. Main startup contract

```text
runtime_entry
    ↓
validate runtime ABI
    ↓
initialize runtime
    ↓
initialize TLS
    ↓
initialize modules
    ↓
construct Args/Env
    ↓
call main
    ↓
shutdown
    ↓
exit
```

---

# 177. Entry failure

Nếu bất kỳ bước mandatory nào fail:

```text
no main()
```

và runtime trả startup failure.

---

# 178. Runtime state visibility

Runtime context không được mặc định public global variable.

---

# 179. Runtime ABI data layout

Structures crossing runtime ABI phải có:

- fixed field order;
- explicit alignment;
- explicit integer width;
- version field;
- reserved fields.

---

# 180. Forward compatibility

Reserved fields phải zero-initialized.

Consumer phải ignore unknown optional fields.

---

# 181. Binary compatibility

Không dùng compiler-private layout cho public runtime ABI.

---

# 182. Cross-language runtime ABI

C/C++/Rust/etc. có thể gọi AX runtime only through explicit ABI bridge.

---

# 183. Native exception interoperability

Không bắt buộc.

Nếu FFI module sử dụng SEH/DWARF exceptions:

platform adapter chịu trách nhiệm interoperability.

---

# 184. Axiom exception policy

Axiom core không yêu cầu C++ exception semantics.

---

# 185. Signal integration

AXRUNTIME có thể register minimal signal/fault handlers khi diagnostics/panic feature yêu cầu.

---

# 186. Signal handler safety

Handler chỉ sử dụng async-signal-safe operations trên targets nơi signal model tồn tại.

---

# 187. Windows exception integration

Windows-specific faults được adapter chuyển thành runtime trap/diagnostic representation.

---

# 188. Linux signal integration

Signals như invalid memory access có thể được chuyển thành diagnostic event.

---

# 189. macOS exception integration

Platform-specific exception mechanisms được giữ trong adapter.

---

# 190. No universal fault abstraction leakage

Axiom API expose canonical fault categories nhưng giữ platform details trong diagnostics metadata.

---

# 191. Runtime logging

Core startup chỉ log khi:

```text
diagnostic feature enabled
```

---

# 192. Runtime observability

Metrics/tracing không được chạy trong minimal runtime.

---

# 193. Performance budget

Core startup phải:

- ít allocation;
- ít syscalls;
- không thread spawn ngoài yêu cầu;
- không global lock;
- không dynamic plugin scan;
- không filesystem scan ngoài dependency loading cần thiết.

---

# 194. Cold start

Axiom application startup phải tránh initialization work không liên quan tới application.

---

# 195. Static data locality

Runtime tables nên:

```text
read-only
compact
cache-friendly
```

---

# 196. Hot runtime helpers

Hot helpers:

```text
memcpy
memset
atomic
bounds trap
allocation fast path
TLS fast path
```

phải có target-specific lowering.

---

# 197. Cold runtime helpers

Cold helpers:

```text
panic formatting
diagnostics
unwind
startup errors
```

tách section để không ảnh hưởng instruction cache.

---

# 198. Code-size optimization

Runtime được compile theo:

```text
size
speed
balanced
```

nhưng semantic ABI không đổi.

---

# 199. Runtime self-hosting

AXRUNTIME cuối cùng phải:

```text
Axiom source
 ↓
AXCOMPILER
 ↓
native machine code
```

không yêu cầu C implementation.

---

# 200. Formal invariants

```text id="s1b6pt"
RUNTIME-INV-01
AXRUNTIME phải implement AXRUNTIME_ABI_1.

RUNTIME-INV-02
Runtime không được yêu cầu trong freestanding mode.

RUNTIME-INV-03
Runtime footprint phải tỷ lệ với feature được sử dụng.

RUNTIME-INV-04
Runtime không được yêu cầu garbage collector.

RUNTIME-INV-05
Runtime không được yêu cầu borrow checker runtime support.

RUNTIME-INV-06
Runtime không được tạo hidden OS thread cho application không yêu cầu.

RUNTIME-INV-07
Runtime startup phải deterministic với cùng startup inputs.

RUNTIME-INV-08
Runtime initialization phải hoàn thành trước application main.

RUNTIME-INV-09
TLS phải sẵn sàng trước code cần TLS execution.

RUNTIME-INV-10
Runtime không được dùng heap trong emergency panic path.

RUNTIME-INV-11
Recursive panic phải được bounded.

RUNTIME-INV-12
Default panic semantics không được yêu cầu exception unwinding.

RUNTIME-INV-13
Recoverable application errors phải có thể biểu diễn mà không panic.

RUNTIME-INV-14
Runtime trap phải có deterministic trap category.

RUNTIME-INV-15
Runtime không được thay thế AXMEMORY ownership semantics.

RUNTIME-INV-16
Runtime không được bắt buộc global heap.

RUNTIME-INV-17
Allocator phải có explicit failure semantics.

RUNTIME-INV-18
Allocator ABI phải preserve requested alignment.

RUNTIME-INV-19
Runtime không được tự động initialize unused subsystems.

RUNTIME-INV-20
Runtime không được tạo scheduler nếu async/task không được sử dụng.

RUNTIME-INV-21
Runtime không được tạo logging subsystem nếu logging không được sử dụng.

RUNTIME-INV-22
Runtime không được tạo observability subsystem nếu không được sử dụng.

RUNTIME-INV-23
Runtime không được tạo diagnostics subsystem đầy đủ nếu không được yêu cầu.

RUNTIME-INV-24
Runtime helper hot paths không được dùng generic dynamic dispatch.

RUNTIME-INV-25
Compiler có quyền inline/lower runtime intrinsics trực tiếp.

RUNTIME-INV-26
Runtime không được yêu cầu libc cho freestanding core.

RUNTIME-INV-27
Platform-specific startup semantics phải nằm trong platform adapter.

RUNTIME-INV-28
Runtime không được sở hữu process lifecycle; AXPROCESS/OS giữ authority.

RUNTIME-INV-29
Runtime exit status phải được chuyển chính xác tới process exit status.

RUNTIME-INV-30
Crash path không được phụ thuộc normal cleanup completion.

RUNTIME-INV-31
Runtime shutdown không được chạy arbitrary cleanup sau fatal termination.

RUNTIME-INV-32
Public runtime ABI structures phải có explicit stable layout.

RUNTIME-INV-33
Runtime ABI major mismatch phải được reject.

RUNTIME-INV-34
Runtime không được bypass AXSECURITY hoặc AXCAPABILITY.

RUNTIME-INV-35
Runtime không được bypass AXLOADER cho dynamic module lifecycle.

RUNTIME-INV-36
Runtime unwind phải sử dụng compiler/linker-produced unwind metadata.

RUNTIME-INV-37
Runtime loaded-module diagnostics phải đồng bộ với AXLOADER lifecycle.

RUNTIME-INV-38
Runtime phải hỗ trợ deterministic bootstrap verification.

RUNTIME-INV-39
Unused runtime components phải có khả năng dead-strip khỏi final binary.

RUNTIME-INV-40
AXRUNTIME phải có implementation path self-hosted bằng Axiom, không phụ thuộc compiler thứ ba trong final toolchain.
```

---

# 201. Definition of Done

`AXRUNTIME 5.0` được freeze khi có:

### Core

- `AXRUNTIME_ABI_1`;
- startup;
- main invocation;
- process exit;
- panic;
- trap;
- emergency termination;
- TLS;
- runtime initialization;
- shutdown.

### Memory

- optional allocator;
- alignment;
- allocation failure;
- allocator hooks;
- compiler intrinsic integration.

### Diagnostics

- optional unwind;
- panic metadata;
- module/debug integration;
- crash-safe path.

### Platform

- Windows PE64;
- Linux ELF64;
- macOS Mach-O;
- iOS;
- Android;
- WASM.

### Architecture

- freestanding mode;
- minimal runtime;
- feature-driven linking;
- dead stripping;
- no mandatory GC;
- no mandatory exception runtime;
- no mandatory scheduler;
- no libc requirement for core.

### Engineering

- ABI compatibility suite;
- bootstrap verification;
- fuzzing;
- startup tests;
- TLS tests;
- allocator tests;
- panic/trap tests;
- unwind tests;
- deterministic-build tests;
- concurrency/reentrancy tests;
- self-hosting implementation.

**AXRUNTIME 5.0 → FROZEN.**

---

# Chuỗi execution hiện tại

Axiom hiện có một execution stack khá rõ:

```text
┌───────────────────────────────────────────────┐
│                  APPLICATION                  │
└───────────────────────┬───────────────────────┘
                        ↓
                 ┌─────────────┐
                 │  AXRUNTIME  │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │  AXPROCESS  │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │  AXLOADER   │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │  AXBINARY   │
                 └──────┬──────┘
                        ↑
                 ┌─────────────┐
                 │  AXLINKER   │
                 └──────┬──────┘
                        ↑
                 ┌─────────────┐
                 │  AXOBJECT   │
                 └──────┬──────┘
                        ↑
                 ┌─────────────┐
                 │ AXCOMPILER  │
                 └─────────────┘
```

Đặc biệt, thiết kế `AXRUNTIME` này giữ đúng mục tiêu ban đầu của Axiom: **một chương trình cực nhỏ có thể gần như không mang runtime**, trong khi chương trình lớn vẫn có thể sử dụng allocator, TLS, async, diagnostics, unwind… mà không phải thay đổi language core.

---

# BOOTSTRAP-778 — AXSTARTUP

**Native Platform Startup, CRT-Free Entry, PE64/ELF64/Mach-O/Android/iOS Process Bootstrap, Stack/Arguments/Environment Extraction, Auxiliary Vector, Platform TLS Bootstrap, Initial Thread Construction & Handoff to AXRUNTIME 5.0**

Task tiếp theo sẽ đi sâu hơn một tầng: **những instruction đầu tiên thực sự chạy sau khi OS chuyển control cho Axiom executable**. Đây là nơi xử lý sự khác biệt rất thấp tầng giữa PE64, ELF64, Mach-O, Android và iOS trước khi `AXRUNTIME` có thể nhận một `RuntimeContext` chuẩn hóa.