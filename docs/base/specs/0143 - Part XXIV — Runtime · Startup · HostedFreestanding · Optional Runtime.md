# Part XXIV — Runtime · Startup · Hosted/Freestanding · Optional Runtime

Đây là một phần rất quan trọng đối với mục tiêu ban đầu của Axiom.

Ta muốn đồng thời đạt được:

```text
tiny firmware
        ↓
freestanding kernel
        ↓
CLI native
        ↓
GUI application
        ↓
server
        ↓
async/network application
        ↓
GPU application
```

mà **không biến tất cả thành một runtime khổng lồ**.

Quyết định nền tảng:

> **Axiom không có “Axiom Runtime” duy nhất. Runtime là tập hợp các capability/runtime component mà chương trình thực sự sử dụng.**

---

# XXIV.1. Không Có Monolithic Runtime

Không tạo:

```text
libaxiom_runtime.so
```

rồi mọi chương trình đều link nó.

Thay vào đó:

```text
Program
 │
 ├── startup
 ├── allocator
 ├── panic
 ├── thread
 ├── async
 ├── TLS
 ├── reflection
 └── ...
```

Mỗi component độc lập.

Một chương trình chỉ arithmetic:

```text
startup
```

Một chương trình dùng heap:

```text
startup
allocator
```

Một chương trình dùng threads:

```text
startup
allocator?
thread
```

---

# XXIV.2. Hai Execution Profiles

Axiom v0.1 chốt:

```text
hosted
freestanding
```

## Hosted

Có OS/platform environment.

Ví dụ:

```text
Windows
Linux
macOS
Android
```

## Freestanding

Không giả định:

- OS;
- filesystem;
- process;
- heap;
- thread;
- libc;
- runtime.

---

# XXIV.3. Hosted Không Có Nghĩa Phải Có std

Điểm này rất quan trọng.

```text
hosted ≠ std mandatory
```

Ví dụ một chương trình Linux cực nhỏ có thể:

```text
hosted
+
direct syscall
+
no std
+
no heap
```

nếu API/platform layer cho phép.

---

# XXIV.4. Freestanding Không Có Nghĩa Không Có Runtime Code

Freestanding vẫn có thể cần:

```text
startup
panic handler
compiler-generated support
```

Nhưng mọi thành phần đều explicit/minimal.

---

# XXIV.5. Entry Point

Hosted application mặc định:

```axiom
fn main() {
    ...
}
```

Compiler tạo startup adapter:

```text
OS
 ↓
_process_start
 ↓
Axiom startup
 ↓
main
 ↓
exit
```

`main` không phải ABI trực tiếp của OS.

---

# XXIV.6. Freestanding Entry

Freestanding:

```axiom
@entry
fn kernel_main() -> never {
    ...
}
```

hoặc entry signature target-specific.

Compiler không tự giả định:

```text
argc
argv
environment
```

---

# XXIV.7. Entry ABI

Entry point có ABI riêng:

```text
@entry
```

không phải:

```text
pub
```

và không nhất thiết là:

```text
@export
```

Compiler target backend biết cách biến nó thành actual entry symbol.

---

# XXIV.8. Startup Layer

Startup chịu trách nhiệm tối thiểu:

```text
stack/environment setup
→ runtime initialization required by profile
→ main
→ exit
```

Không được tự động:

```text
initialize every library
initialize every static
spawn worker thread
initialize GC
```

---

# XXIV.9. Startup Không Có Global Constructor Model

Không có:

```text
C++ global constructors
```

kiểu:

```text
import module
→ constructor tự chạy
```

Đã bị loại từ Part XXII.

---

# XXIV.10. Static Data

Static:

```axiom
static MAX: usize = 100
```

có thể trở thành:

```text
.rodata
.data
.bss
```

theo representation.

Không cần runtime initialization nếu initializer là compile-time constant.

---

# XXIV.11. Mutable Static

Ví dụ:

```axiom
static var counter: Atomic<u64>
```

có storage identity toàn chương trình.

Concurrency semantics vẫn áp dụng bình thường.

Không có:

```text
static = automatically synchronized
```

---

# XXIV.12. Static Lifetime

Static value có semantic lifetime:

```text
program lifetime
```

Nhưng compiler không nhất thiết phải thực hiện destructor lúc process exit.

Đặc biệt:

> **Không có global Drop shutdown mặc định.**

---

# XXIV.13. Tại Sao Không Global Drop?

Nếu mọi static resource đều tự động cleanup lúc process exit:

```text
network
thread
file
GPU
logger
...
```

startup/shutdown trở nên phức tạp và không cần thiết.

OS vốn sẽ reclaim process memory/resources.

Axiom ưu tiên:

```text
explicit shutdown
```

nếu cần semantic cleanup.

---

# XXIV.14. TLS

`static` có thể có TLS storage:

```text
@thread_local
static var state: State
```

Mỗi thread có:

```text
distinct storage identity
```

TLS không phải global shared state.

---

# XXIV.15. TLS Initialization

Không cho hidden arbitrary initialization.

Có thể:

```text
zero/constant initialized
```

hoặc explicit runtime initialization API.

Nếu target ABI có TLS constructor mechanism, đó là platform backend detail và phải tuân contract của Axiom semantics.

---

# XXIV.16. Allocator Runtime

Allocator không bắt buộc.

Ví dụ:

```axiom
fn main() {
    let x: u64 = 10
}
```

không cần allocator.

Nhưng:

```axiom
let v = Vec<i32>()
```

có thể cần allocator.

Build graph/runtime dependency:

```text
Vec
 ↓
allocator
```

---

# XXIV.17. Allocator Không Nhất Thiết Là malloc

Axiom abstraction:

```text
Allocator
```

có thể map tới:

```text
OS allocator
custom allocator
arena
pool
static region
GPU allocator
```

`malloc/free` chỉ là một implementation.

---

# XXIV.18. Global Allocator

Không nên bắt mọi program có:

```text
global malloc
```

MVP có thể cung cấp standard allocator trong std.

Core chỉ biết semantic allocation operation.

---

# XXIV.19. Allocation Failure

Allocation API có thể:

```text
Result<T, AllocError>
```

hoặc panic theo API contract.

Ví dụ:

```axiom
let buffer = Buffer.try_new(1024)?
```

là fallible.

Trong khi:

```axiom
let buffer = Buffer.new(1024)
```

có thể panic on OOM nếu đó là library contract.

---

# XXIV.20. OOM Không Phải Drop Failure

Đã chốt:

```text
allocation failure
≠
resource cleanup failure
```

Drop vẫn non-fallible.

---

# XXIV.21. Panic Component

Axiom panic có hai profile:

```text
abort
unwind
```

### Abort

```text
panic
 ↓
terminate
```

Không cần unwind runtime.

### Unwind

```text
panic
 ↓
stack/state cleanup
 ↓
catch boundary nếu explicit
```

Cần unwind machinery.

---

# XXIV.22. Abort Là Default Cho Tiny/Freestanding

Profile:

```toml
[profile.release]
panic = "abort"
```

được khuyến nghị làm default release.

Lý do:

- binary nhỏ;
- implementation đơn giản;
- predictable;
- không cần unwind tables/runtime nếu target cho phép bỏ.

---

# XXIV.23. Unwind Không Phải Exception Language

Axiom vẫn không có:

```text
throw
try
catch
finally
```

Unwind chỉ là **panic propagation mechanism**.

---

# XXIV.24. Panic Boundary

Có thể có explicit API:

```axiom
catch_panic(fn() -> T) -> Result<T, Panic>
```

nhưng đây là library/runtime boundary.

Không biến thành general exception mechanism.

---

# XXIV.25. Panic Across FFI

Mặc định:

```text
Axiom panic
      X
      ↓
extern "C"
```

Không được phép crossing C ABI.

Compiler phải:

```text
panic → abort
```

hoặc boundary adapter explicit.

---

# XXIV.26. Thread Runtime

Thread creation không thuộc Core runtime bắt buộc.

Program dùng:

```axiom
Thread.spawn(...)
```

thì build system thêm:

```text
thread runtime/platform support
```

nếu target cần.

---

# XXIV.27. Không Có Hidden Thread Pool

Một program sync:

```axiom
fn main() {
    ...
}
```

không được compiler tự spawn worker threads chỉ vì optimizer.

Optimization có thể vectorize/parallelize trong semantic constraints tương lai, nhưng:

> observable thread creation không được tự phát sinh.

---

# XXIV.28. Async Runtime

`async fn` không tự động kéo executor vào binary.

```axiom
async fn fetch() -> Result<Data, Error>
```

chỉ tạo Future.

Nếu program:

```axiom
let f = fetch()
```

thì không có executor bắt buộc.

---

# XXIV.29. Executor

Executor là library/runtime:

```text
std.async.Executor
```

Có thể có:

```text
single-thread
multi-thread
io-driven
custom
embedded
```

---

# XXIV.30. Async Program

Hosted:

```axiom
fn main() {
    let executor = Executor.new()
    executor.block_on(run())
}
```

hoặc std có helper:

```axiom
fn main() {
    async_main(run())
}
```

Nhưng helper này là library convenience.

---

# XXIV.31. No Global Async Runtime

Không có:

```text
import async
→ global executor automatically initialized
```

Điều này giúp:

- tiny binaries;
- embedded;
- deterministic startup;
- custom schedulers.

---

# XXIV.32. Future State Storage

Future state machine có thể nằm:

```text
register
stack
inline
heap
arena
```

Compiler tự chọn.

Không có rule:

```text
async = heap allocation
```

---

# XXIV.33. Runtime Reflection

Reflection runtime không mặc định.

Comptime reflection:

```text
type metadata
field metadata
trait metadata
```

có thể tồn tại compiler-side.

Nếu program cần runtime reflection:

```text
@runtime_reflect
```

hoặc library/type metadata generation explicit.

---

# XXIV.34. Reflection Binary Cost

Không:

```text
all types → runtime metadata
```

mặc định.

Chỉ types/fields được yêu cầu mới emit metadata.

---

# XXIV.35. Unicode Runtime

Core string semantics không bắt buộc kéo toàn bộ Unicode database.

Ví dụ:

```text
Bytes
Text
```

có representation.

Operations như:

```text
Unicode normalization
grapheme segmentation
locale
```

là library/runtime capabilities.

---

# XXIV.36. IO Runtime

File/Socket không phải Core primitive.

```text
std.io.File
std.net.Socket
```

kéo platform abstraction tương ứng.

Freestanding program không link chúng.

---

# XXIV.37. OS Layer

Axiom nên có:

```text
core
platform
std
```

### Core

Language semantics.

### Platform

OS/ABI bindings.

### Std

High-level library.

Ví dụ:

```text
std.fs
 ↓
platform.fs
 ↓
OS ABI
```

---

# XXIV.38. Không Đưa OS API Vào Core

Core không biết:

```text
Win32
POSIX
Linux syscall
Mach
Android NDK
```

Compiler backend có thể biết ABI target, nhưng language semantics không phụ thuộc OS.

---

# XXIV.39. Direct Syscall

System-level Axiom có thể gọi syscall thông qua platform library hoặc unsafe intrinsic.

Ví dụ conceptual:

```axiom
extern "system"
fn write(fd: i32, data: view<u8>) -> isize
```

Đây không phải Core API.

---

# XXIV.40. Exit

Hosted:

```text
main() -> ()
```

mặc định exit code:

```text
0
```

Có thể:

```axiom
fn main() -> i32 {
    42
}
```

để return process exit code.

Tôi đề xuất hỗ trợ cả hai:

```text
main() -> ()
main() -> i32
```

Compiler startup adapter xử lý.

---

# XXIV.41. `Result` Main

Nên hỗ trợ:

```axiom
fn main() -> Result<(), AppError> {
    run()?
}
```

Startup layer sẽ chuyển:

```text
Ok → exit 0
Err → report + nonzero exit
```

nhưng error reporting cụ thể thuộc std/platform.

Điều này cực tiện cho CLI.

---

# XXIV.42. Panic Main

Nếu:

```text
main()
```

panic:

```text
panic strategy
```

quyết định abort/unwind.

Không có hidden exception handler.

---

# XXIV.43. Startup Error

Nếu runtime initialization thất bại:

```text
allocator init
TLS init
platform init
```

phải có explicit startup failure policy.

Không thể gọi Axiom `Result` logic trước khi runtime state cần thiết tồn tại.

Freestanding target có thể tự định nghĩa.

---

# XXIV.44. Runtime Component Manifest

Compiler/build system có thể sinh:

```text
RuntimeRequirements {
    allocator: true
    threads: false
    async: false
    panic: abort
    reflection: false
    tls: true
}
```

Đây là compiler fact.

---

# XXIV.45. Runtime Linking

Build:

```text
source
 ↓
runtime requirement analysis
 ↓
runtime components
 ↓
link
```

Không phải:

```text
always link libaxiomruntime
```

---

# XXIV.46. Runtime Component Graph

Ví dụ:

```text
Program
 │
 ├── allocator
 │    └── platform memory
 │
 ├── thread
 │    └── platform thread
 │
 └── panic
      └── platform stderr
```

Compiler/linker chỉ lấy reachable components.

---

# XXIV.47. Runtime Component ABI

Runtime component có ABI nội bộ:

```text
axiom-runtime-v1
```

Nhưng không nhất thiết là stable public ABI.

Self-hosted compiler có thể regenerate/link runtime objects phù hợp compiler version.

---

# XXIV.48. No Mandatory CRT

Axiom không bắt buộc:

```text
C runtime
```

nhưng hosted target có thể chọn sử dụng OS/C runtime nếu platform integration muốn.

Ví dụ:

```text
Axiom
→ Win32
```

không cần MSVC CRT nếu startup/backend hỗ trợ trực tiếp.

---

# XXIV.49. Tiny Binary

Một chương trình:

```axiom
@entry
fn main() {
    let x: u64 = 10
}
```

có thể theoretically compile:

```text
entry
+
machine code
```

mà không cần:

```text
heap
GC
thread
async
reflection
std
```

Đây là một test quan trọng của kiến trúc Axiom.

---

# XXIV.50. Nhưng Không Hứa “Binary Bằng Assembly”

Không nên đóng spec bằng claim:

> Axiom binary luôn nhỏ bằng hand-written assembly.

Không thể bảo đảm cho mọi target/program.

Đúng hơn:

> **Axiom không áp đặt runtime overhead mà semantics không yêu cầu và compiler được tự do loại bỏ mọi abstraction không observable.**

Đây là mục tiêu có thể kiểm chứng.

---

# XXIV.51. Runtime và Optimization

Ví dụ:

```axiom
fn f() -> Box<i32> {
    Box.new(42)
}
```

Compiler có thể biến thành:

```text
caller-provided storage
```

nếu address không observable.

Runtime allocator không nhất thiết được gọi.

---

# XXIV.52. Runtime Capability ≠ Source Dependency

Một type:

```text
Vec<T>
```

có thể semantically cần dynamic storage.

Nhưng compiler có thể:

```text
scalarize
stack-promote
eliminate allocation
```

nếu không observable.

Do đó:

```text
library uses allocation
```

không đồng nghĩa:

```text
binary must perform heap allocation
```

---

# XXIV.53. Runtime-Free Program

Định nghĩa:

> Runtime-free là program không cần bất kỳ Axiom-managed runtime component nào ngoài startup/target entry contract cần thiết.

Không có nghĩa:

```text
không có OS
```

Ví dụ direct Windows syscall vẫn dùng OS.

---

# XXIV.54. Hosted Minimal Profile

Có thể định nghĩa:

```text
hosted-minimal
```

với:

```text
startup
OS ABI
panic=abort
no allocator
no threads
no async
no reflection
```

rất hữu ích cho tiny native applications.

---

# XXIV.55. Embedded Profile

```text
embedded
```

có thể:

```text
freestanding
panic=abort
custom allocator/no allocator
custom entry
custom interrupt handling
no OS
```

---

# XXIV.56. Kernel Profile

Conceptual:

```text
kernel
```

thêm:

```text
freestanding
no implicit allocator
no implicit threads
interrupt ABI
volatile
atomic
device memory
```

Kernel support chủ yếu là platform/system libraries và target extensions, không cần biến Core thành OS language.

---

# XXIV.57. GPU Profile

GPU:

```text
@kernel
```

không dùng hosted runtime.

GPU dispatch:

```text
host
 ↓
queue
 ↓
device
 ↓
kernel
```

đã được Part XX chốt.

---

# XXIV.58. Android

Android application có thể:

```text
Axiom
 ↓
Android target
 ↓
AArch64
 ↓
native library/executable
```

Runtime component nào cần thì link.

Axiom language không cần Android-specific primitives.

---

# XXIV.59. WASM

WASM có thể là:

```text
freestanding-like
```

hoặc:

```text
hosted by JS/WASI
```

tùy target profile.

WASI/platform layer nằm ngoài Core.

---

# XXIV.60. Runtime Diagnostics

Compiler phải có:

```text
axiom inspect --runtime
```

Ví dụ:

```text
Runtime requirements:
    startup: hosted-linux-x86_64
    allocator: yes
    threads: no
    async: no
    reflection: no
    panic: abort
    tls: no
```

Rất hữu ích để tối ưu binary.

---

# XXIV.61. Runtime Dependency Error

Nếu freestanding code:

```axiom
File.open(...)
```

compiler phải báo kiểu:

```text
AX_RUNTIME_0001:
operation requires hosted filesystem capability
```

Không link một runtime khổng lồ chỉ để làm cho compile pass.

---

# XXIV.62. Runtime Capability Mismatch

Ví dụ kernel:

```axiom
@kernel
fn compute() {
    File.open(...)
}
```

→ compile-time error:

```text
AX_DOMAIN_0001:
filesystem operation is not available in kernel execution domain
```

Đã phù hợp với execution-domain model của GPU.

---

# XXIV.63. Runtime Invariants

### Runtime architecture

**ARUNTIME-20 — Axiom Has No Mandatory Monolithic Runtime**

**ARUNTIME-21 — Runtime Components Are Capability-Driven**

**ARUNTIME-22 — Unused Runtime Components Need Not Be Linked**

**ARUNTIME-23 — Hosted And Freestanding Are Distinct Execution Profiles**

**ARUNTIME-24 — Hosted Does Not Imply Mandatory Standard Library**

**ARUNTIME-25 — Freestanding Does Not Imply A Specific Runtime Implementation**

### Startup

**ARUNTIME-26 — Program Entry Is An Explicit ABI Contract**

**ARUNTIME-27 — Hosted Startup Adapts Platform Entry To `main`**

**ARUNTIME-28 — Freestanding Entry Is Explicit**

**ARUNTIME-29 — Import Does Not Trigger Runtime Initialization**

**ARUNTIME-30 — Hidden Global Constructors Are Not Core Semantics**

**ARUNTIME-31 — Static Constant Initialization Does Not Require Runtime Code**

### Static/TLS

**ARUNTIME-32 — Static Storage Has Program Lifetime**

**ARUNTIME-33 — Static Lifetime Does Not Imply Process-Exit Destruction**

**ARUNTIME-34 — Global Drop At Process Exit Is Not Mandatory**

**ARUNTIME-35 — TLS Has Per-Thread Storage Identity**

**ARUNTIME-36 — TLS Initialization Must Follow An Explicit Target Contract**

### Allocation

**ARUNTIME-37 — Heap Allocation Is Not Mandatory**

**ARUNTIME-38 — Allocation Does Not Imply malloc/free**

**ARUNTIME-39 — Allocation Failure Is Distinct From Resource Cleanup**

**ARUNTIME-40 — Compiler May Eliminate Unobservable Allocation**

### Panic

**ARUNTIME-41 — Panic Strategy Is A Build Profile Property**

**ARUNTIME-42 — Abort Requires No Unwind Runtime**

**ARUNTIME-43 — Unwind Is Optional**

**ARUNTIME-44 — Unwind Does Not Introduce General Exception Semantics**

**ARUNTIME-45 — Panic Does Not Cross FFI Boundaries By Default**

### Async/Threads

**ARUNTIME-46 — Async Does Not Require An Executor**

**ARUNTIME-47 — Future Creation Does Not Imply Task Execution**

**ARUNTIME-48 — Thread Creation Is Explicit**

**ARUNTIME-49 — Hidden Worker Threads Are Not Required Runtime Semantics**

### Reflection/Library

**ARUNTIME-50 — Runtime Reflection Is Opt-In**

**ARUNTIME-51 — Compile-Time Reflection Does Not Require Runtime Metadata**

**ARUNTIME-52 — Unicode/IO/Network Facilities Are Library/Platform Capabilities**

### Binary

**ARUNTIME-53 — Runtime Requirements Are Discoverable**

**ARUNTIME-54 — Runtime Components Are Independently Linkable**

**ARUNTIME-55 — Runtime Linking Must Be Reachability/Requirement Driven**

**ARUNTIME-56 — Axiom Does Not Require A C Runtime For Core Semantics**

**ARUNTIME-57 — Hosted Platform Libraries Are Explicit Dependencies**

**ARUNTIME-58 — Runtime Optimization Cannot Change Observable Semantics**

### Cross-target

**ARUNTIME-59 — Host And Target Runtime Requirements Are Distinct**

**ARUNTIME-60 — Cross Compilation Does Not Require Target Execution**

**ARUNTIME-61 — WASM Runtime Assumptions Belong To The Target Profile**

**ARUNTIME-62 — GPU Runtime Requirements Are Distinct From CPU Runtime Requirements**

---

# XXIV.64. Runtime Architecture cuối

Ta có:

```text
                         AXIOM PROGRAM
                               │
                               ▼
                     Runtime Requirement
                         Analysis
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
          Startup           Optional          Platform
                            Components
              │                │                │
              │       ┌────────┼────────┐       │
              │       │        │        │       │
              │    Allocator  Thread  Async   OS ABI
              │       │        │        │       │
              └───────┴────────┴────────┴───────┘
                               │
                               ▼
                            Link
                               │
                               ▼
                          Native Binary
```

Không có:

```text
              ┌─────────────────────┐
              │ HUGE AXIOM RUNTIME  │
              │ GC + async + thread │
              │ reflection + ...    │
              └─────────────────────┘
```

---

# XXIV.65. Một nguyên tắc mới rất đáng đưa vào Axiom

Từ toàn bộ memory/ownership/build/runtime design, có thể rút ra một invariant cấp cao:

> **ARUNTIME-63 — Runtime Cost Must Correspond To Observable Or Required Semantics.**

Nếu chương trình không cần:

- GC → không có GC;
- heap → không có heap;
- thread → không có thread runtime;
- async → không có executor;
- reflection → không có metadata;
- unwind → không có unwind runtime.

Đây chính là cách Axiom có thể vừa có abstraction cấp cao vừa giữ performance gần machine-level.

---

## Tiếp theo — Part XXV: Compiler Architecture · Frontend → HIR → Typed IR → MIR → Verification → LIR → Backend

Đây sẽ là một trong những phần quan trọng nhất của toàn bộ spec. Ta sẽ **đóng băng compiler pipeline**, đặc biệt:

```text
Lexer
→ Parser
→ AST
→ Resolver
→ HIR
→ Typed HIR
→ Trait/Generic Solver
→ Closure/Async Lowering
→ MIR
→ Ownership/Capability Verification
→ Drop Elaboration
→ Verified MIR
→ Optimization
→ ABI Lowering
→ LIR
→ Target Lowering
→ Machine IR
→ Register Allocation
→ Encoder
→ Object
→ Link
```

và quan trọng hơn: xác định **compiler được phép tối ưu đến mức nào mà không bao giờ được phá semantics của Axiom**.