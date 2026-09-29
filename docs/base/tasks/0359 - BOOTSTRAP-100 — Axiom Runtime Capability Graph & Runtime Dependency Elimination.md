# BOOTSTRAP-100 — Axiom Runtime Capability Graph & Runtime Dependency Elimination

**Trạng thái: FROZEN**

Đây là phần nối trực tiếp giữa:

- Language Core
- Standard Library
- `static` / `lazy`
- panic/unwind
- thread/async
- allocator
- GPU
- linker
- mục tiêu binary nhỏ và không có runtime thừa.

Nguyên tắc trung tâm:

> **Axiom không link “runtime” theo tên thư viện; Axiom link đúng những semantic capabilities mà chương trình thực sự sử dụng.**

---

# 1. Không có một "Axiom Runtime" duy nhất

Không tạo:

```text
axiom-runtime.dll
axiom-runtime.so
libaxiom_runtime.a
```

rồi mặc định link toàn bộ.

Thay vào đó runtime được chia thành các component độc lập:

```text
Runtime Components
├── startup
├── allocator
├── panic
├── unwind
├── thread
├── TLS
├── async
├── IO
├── process
├── filesystem
├── network
├── GPU
├── reflection
├── synchronization
└── platform
```

Một chương trình đơn giản:

```axiom
fn main() {
    println("Hello");
}
```

không nên tự động kéo theo:

```text
thread
async
GPU
reflection
unwind
network
filesystem
...
```

---

# 2. Runtime Capability Graph

Compiler xây dựng một graph:

```text
Application
    │
    ├── main
    │
    ├── println
    │      │
    │      └── stdout
    │
    └── panic
           │
           └── panic_abort
```

Ví dụ:

```text
Program
 │
 ├─ Startup
 ├─ IO.Stdout
 │    └─ OS.Write
 └─ Panic.Abort
```

Chỉ những node reachable từ semantic roots mới cần thiết.

---

# 3. Runtime capability ≠ library import

Đây là distinction rất quan trọng.

```axiom
import std::collections::Vec;
```

không có nghĩa:

```text
link Vec runtime
```

vì `Vec` có thể không cần runtime component riêng.

Ngược lại:

```axiom
let t = spawn(worker);
```

có thể tạo dependency:

```text
Thread
 ├── Thread creation
 ├── Scheduler/platform support
 └── Synchronization
```

Compiler phát hiện từ **semantic usage**, không từ tên module.

---

# 4. Runtime capability được khai báo ở API boundary

Một API có thể khai báo:

```text
requires:
    runtime.thread
```

hoặc compiler biết trực tiếp qua intrinsic/semantic operation.

Ví dụ:

```axiom
thread::spawn(...)
```

lower thành semantic operation:

```text
SPAWN_THREAD
```

Compiler biết:

```text
SPAWN_THREAD → ThreadRuntime
```

Không cần parser source để đoán dependency.

---

# 5. Runtime graph nằm sau Verified MIR

Pipeline:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Capability / Concurrency verification
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
Runtime Capability Discovery
  ↓
Runtime Graph
  ↓
Runtime Closure
  ↓
ABI MIR
  ↓
Machine Code
  ↓
Link
```

Không nên xác định runtime dependency quá sớm.

Vì optimizer có thể loại bỏ operation.

---

# 6. Ví dụ allocation elimination

```axiom
fn foo() -> i32 {
    let x = Box.new(42);
    *x
}
```

Semantic ban đầu:

```text
ALLOC dynamic
STORE 42
LOAD
DEALLOC
```

Optimizer có thể biến thành:

```text
return 42
```

Khi đó:

```text
RuntimeAllocator
```

không còn là dependency.

Đây chính là lý do runtime discovery phải diễn ra **sau semantic optimization**, hoặc ít nhất phải được recompute sau optimization.

---

# 7. Runtime Closure

Graph ban đầu:

```text
main
 ├── allocator
 ├── panic
 └── thread
```

Nhưng:

```text
allocator
```

sau optimization không còn reachable.

Final closure:

```text
main
 └── panic_abort
```

Chỉ runtime closure cuối cùng được link.

---

# 8. Runtime component có dependency riêng

Ví dụ:

```text
AsyncRuntime
 ├── Scheduler
 ├── Waker
 ├── Timer
 └── ThreadRuntime   [optional]
```

Nhưng async không nhất thiết cần thread.

Có thể có:

```text
AsyncRuntime
 └── SingleThreadExecutor
```

Do đó dependency graph phải cho phép nhiều implementation.

---

# 9. Capability và implementation policy tách biệt

Semantic code yêu cầu:

```text
ASYNC_EXECUTION
```

nhưng không nhất thiết yêu cầu:

```text
Tokio-like runtime
```

hoặc:

```text
ThreadPool
```

Compiler/runtime profile chọn implementation.

Ví dụ:

```text
Async Capability
    ├── SingleThreadExecutor
    ├── MultiThreadExecutor
    └── EmbeddedExecutor
```

Language semantics chỉ yêu cầu capability contract.

---

# 10. Hosted / Minimal / Freestanding

Ba profile hữu ích:

### Hosted

```text
OS startup
filesystem
network
threads
process
...
```

được phép sử dụng đầy đủ.

### Minimal

```text
startup
panic
allocator nếu cần
```

chỉ link component cần thiết.

### Freestanding

```text
@entry
```

không mặc định có:

```text
allocator
thread
async
filesystem
network
libc
```

---

# 11. Panic runtime

Panic có hai implementation policy chính:

```text
panic=abort
panic=unwind
```

Nếu:

```text
panic=abort
```

không link unwind runtime.

Nếu:

```text
panic=unwind
```

cần:

```text
unwind metadata
unwind runtime
drop cleanup support
```

Nhưng chỉ khi target/profile thực sự cần.

---

# 12. `panic=abort` cho binary nhỏ

Freestanding:

```text
@entry
    ↓
panic
    ↓
abort/trap
```

có thể không cần exception/unwind machinery.

Đây là một lợi thế trực tiếp cho:

- embedded
- bootloader
- kernel
- tiny CLI
- WASM nhỏ.

---

# 13. Allocator runtime

Không có:

```text
"Program uses Axiom → automatically gets heap"
```

Một chương trình:

```axiom
fn main() {
    let x = 42;
}
```

không cần allocator.

Nếu dùng:

```axiom
let x = Vec.new();
```

allocator dependency chỉ xuất hiện nếu actual implementation/storage không được optimizer loại bỏ.

---

# 14. Allocator component có nhiều backend

```text
Allocator Capability
├── OS allocator
├── System allocator
├── Axiom allocator
├── Arena
├── Pool
├── Slab
└── Custom allocator
```

Nhưng:

> `Vec<T>` không hard-code một allocator runtime cụ thể.

Điều này đã phù hợp với ALIB2-40/41 và AMEM-40.

---

# 15. Không link allocator chỉ vì `Box<T>`

Ví dụ:

```axiom
fn foo() -> i32 {
    let x = Box.new(42);
    *x
}
```

Nếu compiler chứng minh:

```text
x does not escape
address not observable
```

thì có thể:

```text
Box
↓
stack/register
↓
no allocation
```

và allocator biến mất khỏi runtime graph.

---

# 16. Thread runtime

Chỉ xuất hiện khi semantic operation yêu cầu:

```text
spawn
thread-local execution
thread synchronization
thread join
...
```

Nhưng một `Atomic<T>` đơn độc không nhất thiết phải link **thread runtime**.

Atomic là machine/platform capability.

Ví dụ:

```axiom
static counter: Atomic<u64>;
```

có thể chỉ cần:

```text
CPU atomic instructions
```

không cần scheduler/thread library.

---

# 17. Synchronization runtime

Tách:

```text
Atomic
Mutex
RwLock
Semaphore
Condvar
Channel
```

Không gom thành một `sync-runtime` khổng lồ.

Ví dụ chỉ dùng:

```axiom
Atomic.fetch_add(...)
```

không kéo:

```text
Mutex
RwLock
Condvar
Channel
```

---

# 18. Async runtime

Quan trọng:

```axiom
async fn foo() -> i32 {
    42
}
```

**không tự động link async executor**.

Future chỉ là value/control-flow state machine.

Executor chỉ cần khi:

```axiom
spawn(foo());
```

hoặc:

```axiom
block_on(foo());
```

---

# 19. Future có thể hoàn toàn runtime-free

Ví dụ library:

```axiom
fn make_future() -> Future<i32> {
    ...
}
```

chỉ tạo Future.

Consumer có thể tự poll.

Không cần:

```text
async runtime
scheduler
thread pool
```

---

# 20. GPU runtime

Tương tự:

```axiom
@kernel
fn add(...) { ... }
```

compile GPU code không có nghĩa executable CPU phải link toàn bộ GPU runtime.

Nếu program chỉ tạo GPU binary:

```text
GPU code artifact
```

có thể không có host GPU runtime.

Nếu thực hiện:

```axiom
gpu.launch(...)
```

thì dependency:

```text
GPU launch capability
```

được thêm.

---

# 21. Reflection runtime

Compile-time reflection:

```axiom
comptime {
    size_of<T>()
}
```

không cần runtime reflection.

Runtime reflection chỉ khi programmer yêu cầu:

```text
emit runtime type metadata
```

Do đó:

```text
compile-time reflection ≠ reflection runtime
```

---

# 22. TLS runtime

Một chương trình dùng:

```axiom
@tls static buffer: Buffer;
```

cần target TLS machinery.

Nhưng không cần:

```text
thread runtime
```

nếu thread creation được thực hiện bên ngoài.

Đây là distinction:

```text
TLS capability
≠
thread creation capability
```

---

# 23. FFI runtime

FFI call:

```axiom
extern "C" fn puts(...);
```

không mặc định kéo:

```text
C runtime
```

Axiom chỉ phát sinh external dependency:

```text
symbol: puts
library: user/platform specified
```

Nếu user chọn libc thì đó là build dependency.

Axiom compiler không tự biến libc thành runtime bắt buộc.

---

# 24. OS APIs

Ví dụ:

```axiom
File.open(...)
```

semantic dependency:

```text
File API
    ↓
OS file capability
```

Nhưng:

```text
File
```

không nhất thiết kéo:

```text
Network
Thread
Async
Process
```

---

# 25. Runtime root set

Runtime graph bắt đầu từ các roots:

```text
Program Entry
Exported Symbols
Externally Required Symbols
Explicit Runtime Features
Static Initialization
TLS Initialization
GPU Entry
FFI Callbacks
```

Sau đó compiler tính:

```text
Reachable Runtime Closure
```

---

# 26. Exported functions là runtime roots

Nếu:

```axiom
@export("foo")
pub fn foo() { ... }
```

thì `foo` là externally reachable.

Compiler không được dead-strip code chỉ vì không thấy internal call.

Từ đó runtime dependencies của `foo` cũng trở thành roots.

---

# 27. Shared library

Shared library có graph riêng:

```text
Exports
   ↓
Reachable functions
   ↓
Runtime capabilities
```

Không được lấy `main` làm root vì shared library có thể không có `main`.

---

# 28. Dynamic symbol lookup

Nếu dùng:

```axiom
Symbol.load("foo")
```

compiler không biết symbol nào sẽ được gọi.

Khi đó programmer/build system phải khai báo:

```text
external root
```

hoặc runtime loader phải chịu trách nhiệm.

Không được giả định dead-stripping vẫn an toàn.

---

# 29. Runtime component ABI

Mỗi runtime component có metadata:

```text
RuntimeComponent {
    id
    version
    target
    abi
    capabilities
    dependencies
    exported_symbols
    initialization
    shutdown
}
```

Ví dụ:

```text
panic.abort {
    capability: panic.abort
    dependencies: platform.terminate
}
```

---

# 30. Runtime components không nhất thiết là libraries

Compiler có thể implement component bằng:

- inline machine code
- compiler intrinsic
- object module
- static library
- generated source/object
- platform ABI
- system call

Do đó:

> Runtime component là **semantic/build unit**, không phải bắt buộc là file `.a/.lib/.so`.

---

# 31. Runtime capability elimination

Ví dụ:

```text
Program
├── Vec
│   └── Allocator
├── async
│   └── Executor
├── panic
│   └── Abort
└── Atomic
```

Nếu optimizer phát hiện:

```text
Vec path eliminated
async path eliminated
```

final:

```text
Program
├── Atomic
└── Abort
```

Runtime closure được tính lại.

---

# 32. Linker integration

Linker nhận:

```text
User Objects
+
Runtime Objects
+
Foreign Objects
+
System Objects
```

Sau đó:

```text
symbol resolution
↓
section GC
↓
COMDAT elimination
↓
dead stripping
↓
relocation
```

Do đó có **hai tầng elimination**:

```text
Compiler semantic elimination
        ↓
Runtime capability elimination
        ↓
Linker reachability elimination
```

---

# 33. Không được phụ thuộc vào linker để sửa semantic runtime

Ví dụ compiler không được nói:

> "Cứ link toàn bộ runtime, linker tự loại."

Vì điều này:

- làm binary intermediate lớn
- làm incremental build tệ
- che dependency thật
- có thể gây initialization side effects
- phá freestanding
- làm dependency graph không chính xác.

Compiler phải biết runtime semantics trước.

---

# 34. Runtime initialization và dead stripping

Nếu runtime component có initialization:

```text
ThreadRuntime.init()
```

thì initialization phải chỉ tồn tại khi component reachable.

Không được có:

```text
unused component
    ↓
hidden startup constructor
```

Điều này trực tiếp bảo vệ quyết định của BOOTSTRAP-099.

---

# 35. Runtime component dependency cycle

Ví dụ:

```text
Async → Thread
Thread → Async
```

không nên tồn tại ở semantic component layer.

Nếu implementation cycle thực sự cần:

```text
shared lower-level primitive
```

phải tách:

```text
SchedulerCore
       ↑
   ThreadRuntime
       ↑
   AsyncRuntime
```

hoặc:

```text
ExecutionPrimitive
   ├── Thread
   └── Async
```

---

# 36. Runtime versioning

Runtime component identity phải bao gồm:

```text
component
semantic version
target
ABI
compiler/runtime contract
feature configuration
```

để incremental cache không lấy nhầm binary runtime incompatible.

---

# 37. Static linking mặc định cho runtime nhỏ

Với runtime component nhỏ:

```text
panic_abort
atomic helpers
startup
```

static embedding/linking thường phù hợp.

Không nên bắt executable nhỏ phụ thuộc vào một `axiom-runtime.so`.

---

# 38. Shared runtime là optimization, không phải requirement

Có thể tồn tại:

```text
libaxiom_thread.so
```

trong ecosystem.

Nhưng:

```text
language semantics
```

không phụ thuộc vào nó.

Shared runtime là deployment/build optimization.

---

# 39. Runtime-free Axiom

Mục tiêu quan trọng:

```axiom
@entry
fn _start() -> never {
    ...
}
```

có thể compile thành:

```text
native code
+
platform-required metadata
```

mà không cần:

```text
Axiom runtime
GC
allocator
libc
thread library
exception runtime
```

Đây là một test cực mạnh cho kiến trúc.

---

# 40. Binary-size model

Axiom binary size không được định nghĩa:

```text
language runtime size
+
application size
```

mà gần hơn:

```text
Binary
=
Reachable Application Code
+
Reachable Runtime Capabilities
+
Required Platform Glue
+
Required Metadata
```

Do đó mục tiêu "nhỏ như ASM" có ý nghĩa thực tế:

> **Không có chi phí runtime bắt buộc mà chương trình không sử dụng.**

---

# 41. CompilerDB additions

Thêm:

```text
RuntimeDB
RuntimeComponentDB
RuntimeCapabilityDB
RuntimeGraphDB
RuntimeSelectionDB
RuntimeArtifactDB
```

Các ID:

```text
RuntimeComponentId
RuntimeCapabilityId
RuntimeDependencyId
RuntimeInstanceId
```

---

# 42. MIR representation

Có thể có semantic ops:

```text
ALLOC
DEALLOC
SPAWN
AWAIT
PANIC
UNWIND
TLS_ACCESS
ATOMIC
IO
GPU_LAUNCH
PROCESS_EXIT
```

Runtime discovery mapping:

```text
ALLOC        → allocator capability
SPAWN        → thread capability
AWAIT        → async capability only if execution requires it
PANIC        → panic capability
UNWIND       → unwind capability
TLS_ACCESS   → TLS capability
IO           → platform IO capability
GPU_LAUNCH   → GPU runtime/driver capability
```

Sau optimization, mapping lại từ **remaining operations**.

---

# 43. AI explainability

Axiom nên hỗ trợ:

```bash
axiom build --explain-runtime
```

Ví dụ output:

```text
Runtime capabilities:

startup
  required by: main

panic.abort
  required by: bounds-check failure path

allocator
  eliminated:
    Vec<T> allocation did not escape

thread
  not required

async
  not required

unwind
  not required
```

Hoặc machine-readable:

```bash
axiom build --runtime-graph=json
```

Điều này cực kỳ hữu ích cho AI agent.

---

# 44. Runtime dependency diagnostics

Compiler có thể báo:

```text
RUNTIME001:
  `spawn()` requires runtime capability `thread.execution`.

RUNTIME002:
  `async::spawn()` requires `async.execution`.

RUNTIME003:
  `@tls` requires target TLS support.

RUNTIME004:
  runtime component eliminated after optimization.
```

Không chỉ compiler error mà còn optimization explanation.

---

# 45. Quy tắc quan trọng nhất

Axiom sẽ khóa:

> **Nếu một abstraction không observable và compiler loại bỏ được implementation của nó, runtime dependency tương ứng cũng phải được phép loại bỏ.**

Ví dụ:

```text
Box → no allocation
Future → fully inlined
Iterator → fused
Closure → eliminated
Generic → specialized
Bounds check → proven
Panic path → unreachable
```

thì các runtime component tương ứng có thể biến mất.

---

# 46. Nhưng không được over-optimize semantic behavior

Ví dụ:

```axiom
let x = Box.new(...);
let p = address_of(x);
```

địa chỉ observable.

Compiler không được loại allocation tùy tiện nếu semantics yêu cầu stable address.

Tương tự:

```axiom
lazy static x = ...
```

có initialization semantics observable.

Không được biến thành constant nếu điều đó thay đổi semantics.

---

# 47. Runtime graph và incremental compilation

Runtime graph fingerprint:

```text
RuntimeFingerprint =
    semantic runtime capabilities
    + target
    + profile
    + panic mode
    + ABI
    + feature configuration
```

Nếu source thay đổi nhưng runtime closure không đổi:

```text
runtime artifacts
```

có thể cache/reuse.

---

# 48. Runtime graph và cross compilation

Runtime component selection phụ thuộc target:

```text
Windows
    → PE startup
    → Windows TLS
    → Windows threading

Linux
    → ELF startup
    → ELF TLS
    → Linux threading

WASM
    → WASM entry
    → WASM memory
    → no native thread unless enabled
```

Semantic capability giữ nguyên; implementation target thay đổi.

---

# 49. Runtime graph và GPU

GPU runtime cũng target-specific:

```text
Axiom GPU semantic capability
          ↓
     target backend
     ├── CUDA-like target
     ├── Vulkan/SPIR-V
     ├── Metal
     ├── DirectX
     └── future backend
```

Không được để CPU executable tự động phụ thuộc tất cả GPU backends.

---

# 50. Architecture hoàn chỉnh

Đến đây runtime model của Axiom trở thành:

```text
                   Axiom Program
                         │
                         ▼
                  Verified MIR
                         │
                         ▼
                  Semantic Optimizer
                         │
              ┌──────────┴──────────┐
              │                     │
         Application Code      Runtime Ops
                                    │
                                    ▼
                         Runtime Capability Graph
                                    │
                                    ▼
                          Minimal Runtime Closure
                                    │
                  ┌─────────────────┼─────────────────┐
                  ▼                 ▼                 ▼
              startup            panic            allocator
                  │
                  ▼
             Target ABI
                  │
                  ▼
                Linker
                  │
                  ▼
           Dead-strip / GC / LTO
                  │
                  ▼
             Native Binary
```

---

# 51. Frozen invariants

### Runtime Architecture

**ARUNTIME-20** — Axiom Has No Mandatory Monolithic Runtime  
**ARUNTIME-21** — Runtime Is Composed Of Independent Capabilities  
**ARUNTIME-22** — Runtime Capability Is Distinct From Library Import  
**ARUNTIME-23** — Runtime Dependencies Are Determined Semantically  
**ARUNTIME-24** — Runtime Discovery Occurs After Semantic Verification  
**ARUNTIME-25** — Runtime Discovery Accounts For Semantic Optimization  
**ARUNTIME-26** — Runtime Graph Contains Only Reachable Capabilities  
**ARUNTIME-27** — Runtime Closure Is Minimal With Respect To Required Semantics  
**ARUNTIME-28** — Unused Runtime Components Must Not Be Linked  
**ARUNTIME-29** — Compiler Semantic Elimination May Remove Runtime Dependencies  
**ARUNTIME-30** — Linker Dead Stripping May Further Remove Unreachable Runtime Code  
**ARUNTIME-31** — Runtime Components Must Not Depend On Unrelated Components  
**ARUNTIME-32** — Runtime Dependency Cycles Must Be Explicitly Resolved  
**ARUNTIME-33** — Runtime Components Have Stable Semantic Identity  
**ARUNTIME-34** — Runtime Components Have Target-Specific Implementations  
**ARUNTIME-35** — Runtime Capability Is Distinct From Implementation Mechanism  
**ARUNTIME-36** — Runtime Capability May Be Implemented By Compiler Intrinsic  
**ARUNTIME-37** — Runtime Capability May Be Implemented By Generated Code  
**ARUNTIME-38** — Runtime Capability May Be Implemented By Static Object Code  
**ARUNTIME-39** — Runtime Capability May Be Implemented By Platform ABI  
**ARUNTIME-40** — Runtime Capability Does Not Imply A Specific Library File  
**ARUNTIME-41** — Allocator Runtime Is Optional  
**ARUNTIME-42** — Thread Runtime Is Optional  
**ARUNTIME-43** — Async Runtime Is Optional  
**ARUNTIME-44** — GPU Runtime Is Optional  
**ARUNTIME-45** — Reflection Runtime Is Optional  
**ARUNTIME-46** — Unwind Runtime Is Profile-Dependent  
**ARUNTIME-47** — Panic Runtime Is Profile-Dependent  
**ARUNTIME-48** — TLS Runtime Is Distinct From Thread Creation Runtime  
**ARUNTIME-49** — Atomic Operations Do Not Require Thread Runtime  
**ARUNTIME-50** — Future Construction Does Not Require Async Runtime  
**ARUNTIME-51** — Async Execution Requires An Explicit Execution Capability  
**ARUNTIME-52** — GPU Code Generation Does Not Require Host GPU Runtime  
**ARUNTIME-53** — Compile-Time Reflection Does Not Require Runtime Reflection  
**ARUNTIME-54** — FFI Does Not Imply A C Runtime  
**ARUNTIME-55** — FFI External Dependencies Must Be Explicit  
**ARUNTIME-56** — Freestanding Programs Need Not Link Hosted Runtime  
**ARUNTIME-57** — Hosted Startup Is A Runtime Capability  
**ARUNTIME-58** — Freestanding Entry Is Independent Of Hosted Startup  
**ARUNTIME-59** — Runtime Initialization Is Reachability-Driven  
**ARUNTIME-60** — Unused Runtime Initialization Must Not Be Emitted  
**ARUNTIME-61** — Runtime Initialization Must Not Depend On Link Order  
**ARUNTIME-62** — Runtime Components Must Declare Their Dependencies  
**ARUNTIME-63** — Runtime Component Dependencies Are Part Of Build Identity  
**ARUNTIME-64** — Runtime Selection Is Target-Aware  
**ARUNTIME-65** — Runtime Selection Is Profile-Aware  
**ARUNTIME-66** — Runtime Selection Is Feature-Aware  
**ARUNTIME-67** — Runtime Selection Is Deterministic  
**ARUNTIME-68** — Runtime Graph Is Incrementally Cacheable  
**ARUNTIME-69** — Runtime Artifacts May Be Content-Addressed  
**ARUNTIME-70** — Runtime Optimization Must Preserve Semantic Behavior  
**ARUNTIME-71** — Observable Initialization Prevents Invalid Runtime Elimination  
**ARUNTIME-72** — Observable Address Identity Prevents Invalid Storage Elimination  
**ARUNTIME-73** — Runtime Elimination Must Respect FFI Reachability  
**ARUNTIME-74** — Exported Symbols Are Runtime Graph Roots  
**ARUNTIME-75** — Dynamically Resolved Symbols Require Explicit Reachability Contracts  
**ARUNTIME-76** — Shared Libraries Have Independent Runtime Roots  
**ARUNTIME-77** — Runtime Capability Graph Is Independent Of Filesystem Layout  
**ARUNTIME-78** — Runtime Capability Graph Is Independent Of Import Order  
**ARUNTIME-79** — Runtime Components Must Not Create Hidden Threads  
**ARUNTIME-80** — Runtime Components Must Not Create Hidden Async Execution  
**ARUNTIME-81** — Runtime Components Must Not Create Hidden Allocator Dependencies  
**ARUNTIME-82** — Runtime Components Must Not Create Hidden Synchronization  
**ARUNTIME-83** — Runtime Components Must Not Create Hidden Global Initialization  
**ARUNTIME-84** — Runtime-Free Execution Is A Supported Axiom Profile  
**ARUNTIME-85** — Runtime Capability Requirements Are Machine-Readable  
**ARUNTIME-86** — Runtime Graph Is Queryable By Compiler Tooling And AI  
**ARUNTIME-87** — Runtime Explanation May Identify Why A Capability Is Required  
**ARUNTIME-88** — Runtime Explanation May Identify Why A Capability Was Eliminated  
**ARUNTIME-89** — Runtime Closure Must Be Semantically Equivalent To Required Capabilities  
**ARUNTIME-90** — Runtime Architecture Must Not Impose Costs For Unused Features  

**BOOTSTRAP-100: FROZEN.**

---

# Chuỗi kiến trúc tiếp theo

Sau 099–100, phần còn thiếu rất quan trọng là **ABI/API boundary của compiler và toolchain**. Task kế tiếp:

## **BOOTSTRAP-101 — Axiom Diagnostics, Error Model & Compiler UX**

Sẽ khóa:

```text
compiler errors
warnings
notes
help
stable diagnostic codes
source spans
multi-span diagnostics
fix-it
machine-readable JSON
AI-readable diagnostics
type errors
trait errors
ownership errors
capability errors
async errors
GPU errors
FFI errors
comptime errors
build errors
internal compiler errors
error recovery
incremental diagnostics
IDE/LSP integration
```

Đặc biệt sẽ thiết kế để **AI agent có thể tự đọc diagnostic → hiểu nguyên nhân → sửa code → build lại**, thay vì phải parse text compiler output.