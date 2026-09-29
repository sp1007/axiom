# BOOTSTRAP-197 — Standard Library Architecture, `std` Layering & Zero-Cost Platform Abstractions

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của phần này:

> **Axiom có standard library rất mạnh, nhưng việc import một API không được đồng nghĩa với việc kéo cả runtime, OS abstraction hoặc hàng MB code vào binary.**

Kiến trúc được chốt theo nguyên tắc:

```text
Language Core
    ↓
Core Library
    ↓
Allocation Library
    ↓
System/OS Library
    ↓
Runtime Library
    ↓
Platform Adapters
```

Các tầng **không được phụ thuộc ngược** một cách tùy tiện.

---

# 197.1. Phân biệt Language Core và Standard Library

Language Core chứa semantics cần compiler hiểu trực tiếp:

```text
bool
integers
floats
struct
enum
trait
generic
Option/Result semantics
ownership
view/mut_view
match
async
comptime
atomic semantics
```

Standard Library cung cấp implementation/reusable abstractions:

```text
Vec
HashMap
String
File
Socket
Mutex
Channel
Arc
Future executor
```

Không biến mọi thư viện thành keyword của ngôn ngữ.

---

# 197.2. Không có một `std` khổng lồ về mặt dependency

Người dùng có thể nhìn thấy:

```axiom
import std;
```

nhưng compiler không hiểu nó như:

```text
link everything in std
```

Thay vào đó:

```text
std
 ↓
module graph
 ↓
declaration reachability
 ↓
actual dependencies
```

---

# 197.3. Các tầng thư viện

Chốt kiến trúc:

```text
axiom.core
axiom.alloc
axiom.std
axiom.sys
axiom.os
axiom.runtime
axiom.gpu
```

Có thể có facade:

```text
std
```

nhưng facade **không phải một runtime blob**.

---

# 197.4. `core`

`core` là tầng thấp nhất.

Nó không được yêu cầu:

- heap
- OS
- thread
- filesystem
- network
- dynamic loader
- executor

Ví dụ:

```text
Option
Result
Iterator
Range
numeric traits
comparison
ordering
basic formatting contracts
```

---

# 197.5. `alloc`

`alloc` cung cấp abstraction cần dynamic storage:

```text
Box
Vec
String
Arc
Rc
HashMap
Deque
```

`alloc` phụ thuộc allocator contract nhưng không nhất thiết phụ thuộc một allocator implementation cụ thể.

```text
alloc
   ↓
Allocator interface
   ↓
chosen allocator
```

---

# 197.6. `std`

`std` là convenience layer cho hosted application:

```text
std::io
std::fs
std::net
std::process
std::thread
std::sync
std::time
std::env
```

Nhưng mỗi module vẫn được link độc lập.

---

# 197.7. `sys`

`sys` là tầng low-level platform/system API.

Ví dụ:

```text
sys::linux
sys::windows
sys::macos
sys::android
sys::ios
```

Nó có thể expose:

```text
syscall
native handle
OS structure
platform ABI
memory mapping
thread primitive
socket primitive
```

Đây là tầng dành cho system programming.

---

# 197.8. `os`

`os` cung cấp abstraction ổn định hơn:

```text
os::File
os::Process
os::Thread
os::Socket
os::Path
```

Trong đó:

```text
os abstraction
      ↓
sys implementation
      ↓
platform
```

---

# 197.9. Không ép mọi OS vào abstraction chung

Một API POSIX-only hoặc Windows-only không nhất thiết phải bị bóp thành abstraction chung.

Ví dụ:

```axiom
std::os::windows::registry
std::os::linux::epoll
std::os::linux::io_uring
std::os::windows::iocp
```

được phép tồn tại.

Abstraction chung chỉ tồn tại khi semantics thực sự tương thích.

---

# 197.10. `runtime`

Runtime implementation được tách khỏi API.

Ví dụ:

```text
std::thread::spawn
```

là API.

Implementation có thể dùng:

```text
runtime::thread
```

hoặc trực tiếp system API nếu compiler có thể inline/lower.

---

# 197.11. GPU library

GPU không nên trở thành dependency của CPU Core.

```text
std::gpu
```

có:

```text
Device
DeviceBuffer
Kernel
GpuEvent
CommandQueue
```

Compiler hiểu các annotation/semantic contracts cần thiết.

---

# 197.12. Networking

Network không thuộc `core`.

```text
std::net
```

có:

```text
Tcp
Udp
IpAddress
Socket
Listener
```

Runtime/OS dependency chỉ xuất hiện khi API được sử dụng.

---

# 197.13. Filesystem

Tương tự:

```text
std::fs
```

không làm `std` phụ thuộc filesystem.

Chỉ reachable filesystem code mới được link.

---

# 197.14. Generic code và code bloat

Axiom sử dụng:

```text
monomorphization
specialization
code sharing
```

nhưng không mặc định tạo một bản machine code cho mọi generic instantiation nếu không cần.

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Compiler có thể:

```text
T = i32
T = i64
T = MyType
```

specialize khi lợi ích đủ lớn.

---

# 197.15. Generic code sharing

Nếu hai instantiation có representation/behavior tương thích:

```text
Vec<A>
Vec<B>
```

compiler có thể chia sẻ machine implementation ở những phần không phụ thuộc type-specific behavior.

Đặc biệt với:

```text
pointer-sized
opaque
same ABI
```

---

# 197.16. Nhưng không được hy sinh performance

Code sharing không phải mục tiêu tuyệt đối.

Compiler có thể chọn:

```text
specialize
```

khi:

- hot path
- vectorization
- constant propagation
- inlining
- type-specific optimization

và chọn:

```text
share
```

khi:

- cold path
- binary-size profile
- implementation representation giống nhau.

---

# 197.17. Profile ảnh hưởng code generation, không semantics

Ví dụ:

```text
--profile release
--profile size
--profile debug
```

có thể tạo machine code khác nhau.

Nhưng:

```text
program semantics
```

không thay đổi.

---

# 197.18. `no_std` tương đương không cần keyword riêng

Thay vì thiết kế một chế độ ngôn ngữ riêng như:

```text
#![no_std]
```

Axiom có dependency/profile model.

Ví dụ:

```text
core only
core + alloc
core + sys
hosted std
```

Một package chỉ import `core` tự nhiên không kéo `std`.

---

# 197.19. Freestanding package

Package có thể khai báo:

```text
target profile = freestanding
```

Compiler kiểm tra dependency graph:

```text
core
 ├── allowed
alloc
 ├── optional
std
 └── forbidden
```

Nếu vô tình gọi filesystem:

```text
compile error:
requires hosted capability
```

---

# 197.20. Library capability requirements

Mỗi library declaration có metadata:

```text
Requires:
    Allocator
    IO
    Thread
    Network
    Runtime
```

CompilerDB có thể truy vấn:

```text
ax requirements std::net::TcpStream
```

---

# 197.21. Capability propagation

Nếu:

```text
foo()
  ↓
bar()
  ↓
File.open()
```

thì compiler/build graph có thể biết:

```text
foo → Filesystem
```

Điều này phù hợp trực tiếp với security architecture 190.

---

# 197.22. Effect và library dependency

Không phải mọi dependency đều là runtime effect.

Ví dụ:

```text
Option<T>
```

không có external effect.

Trong khi:

```text
File.read()
```

có:

```text
IO
```

CompilerDB có thể phân biệt:

```text
Type dependency
Code dependency
Runtime dependency
Authority dependency
```

---

# 197.23. Compiler intrinsics vs library

Một API có thể có ba implementation:

```text
library implementation
compiler intrinsic
target instruction
```

Ví dụ:

```text
sqrt
memcpy
atomic
bit operations
SIMD
```

Source vẫn có API thống nhất.

Compiler chọn implementation.

---

# 197.24. Intrinsic không phải escape hatch semantic

Intrinsic phải có semantic specification.

Không được:

```text
intrinsic = compiler magic không kiểm chứng
```

Compiler phải biết:

```text
type
effects
ABI
memory semantics
target constraints
```

---

# 197.25. `memcpy` không nhất thiết gọi function

```axiom
copy_bytes(...)
```

có thể lower thành:

```text
inline instructions
SIMD
rep movsb
library call
```

tùy size/target.

Source không phải quyết định implementation.

---

# 197.26. Collection implementation

`Vec<T>` interface ổn định:

```text
len
capacity
push
pop
reserve
view
mut_view
```

Implementation có thể thay đổi.

Compiler có thể inline:

```text
push
index
len
```

vào machine code.

---

# 197.27. `Vec` không kéo collection ecosystem

Nếu dùng:

```axiom
Vec<i32>
```

binary không tự động chứa:

```text
HashMap
BTree
Deque
Graph
ParallelCollection
```

Declaration-level reachability loại bỏ chúng.

---

# 197.28. String

`String` nằm trên:

```text
alloc
```

vì owned mutable UTF-8 storage.

`Str` có thể sử dụng trong:

```text
core
```

vì nó chỉ là semantic view.

Điều này tạo boundary đẹp:

```text
Str
 ↓
core

String
 ↓
alloc
```

---

# 197.29. Formatting

Formatting có thể chia:

```text
core formatting contracts
std formatting implementation
```

Một chương trình không dùng formatting không cần kéo formatter.

---

# 197.30. Error types

`Option` và `Result` thuộc core-level library.

Concrete errors:

```text
IoError
ParseError
NetworkError
ProcessError
```

nằm ở các package/module tương ứng.

Không có một giant:

```text
std::Error
```

bắt buộc.

---

# 197.31. Trait organization

Core traits:

```text
Copy
Clone
Drop
Send
Share
Eq
Ord
Hash
Iterator
```

Standard traits mở rộng:

```text
Read
Write
Seek
Serialize
Deserialize
AsyncRead
AsyncWrite
```

Không đưa IO trait vào language Core.

---

# 197.32. Platform-neutral APIs

Ví dụ:

```axiom
fn read_file(path: Str) -> Result<String, IoError>
```

có thể map tới:

```text
Windows
Linux
macOS
Android
iOS
```

nhưng implementation platform-specific.

---

# 197.33. Platform-specific escape hatch

Khi abstraction không đủ:

```axiom
import std::os::linux;
```

hoặc:

```axiom
import std::sys::windows;
```

cho phép truy cập native API.

Không cần unsafe cho mọi platform API; wrapper có thể cung cấp safe contract.

---

# 197.34. Unsafe chỉ ở boundary

Ví dụ:

```text
std::sys::linux::epoll_create
```

có thể là unsafe/system API.

Nhưng:

```text
std::net::TcpListener
```

có safe abstraction phía trên.

Mục tiêu:

```text
Application
   ↓
safe std
   ↓
safe OS abstraction
   ↓
small unsafe boundary
   ↓
native OS
```

---

# 197.35. Standard library không che giấu cost

API phải có cost model rõ ràng.

Ví dụ:

```text
Vec.push
```

có thể:

```text
O(1) amortized
```

nhưng relocation có thể xảy ra.

`String` có thể relocate khi grow.

`HashMap` có thể rehash.

AI/IDE có thể query metadata:

```text
complexity
allocation
blocking
IO
synchronization
invalidates views?
```

---

# 197.36. Library metadata

Mỗi public API có thể cung cấp:

```text
Complexity
Allocation behavior
Effects
Capability behavior
Invalidation
Send/Share
Blocking
Async
ABI
```

CompilerDB đã có đủ semantic machinery để cung cấp thông tin này.

---

# 197.37. AI-native standard library

AI không nên phải đọc toàn bộ source `std` để biết API.

Ví dụ query:

```text
ax query std::Vec.push
```

có thể trả:

```text
receiver: mut Vec<T>
effect: mutate
allocation: may_allocate
invalidates: existing views if relocation occurs
complexity: amortized O(1)
panic: possible if allocation failure policy
```

Đây là một lợi thế rất lớn của Axiom.

---

# 197.38. Library contracts

Một API có thể khai báo contract metadata:

```text
@complexity("amortized O(1)")
@allocates("conditional")
@blocking(false)
@invalidates("views:on_reallocation")
```

Compiler có thể kiểm chứng một phần; phần còn lại là documentation/tooling contract.

Không biến mọi documentation thành semantic law nếu compiler không thể verify.

---

# 197.39. Standard library versioning

Language version và standard library version tách biệt:

```text
Axiom language 1.x
std 1.x
```

Nhưng Core ABI/semantic compatibility phải được quản lý rõ.

---

# 197.40. Core library có thể được compiler đặc biệt hóa

Compiler được phép recognize một số API chuẩn:

```text
Option
Result
Vec
String
Atomic
Future
```

nhưng semantics vẫn phải được định nghĩa.

Không được để compiler “đoán” dựa trên tên function.

---

# 197.41. Intrinsic recognition bằng semantic identity

Compiler nhận:

```text
DeclarationId
```

thay vì:

```text
name == "memcpy"
```

Điều này tránh collision từ user-defined API.

---

# 197.42. Standard library source vẫn là Axiom

Mục tiêu self-host:

```text
Compiler
Stdlib
Runtime
Linker
```

đều có thể được viết bằng Axiom.

Không yêu cầu C++ implementation vĩnh viễn.

---

# 197.43. Bootstrap standard library

Ban đầu:

```text
Axiom compiler
   ↓
bootstrap runtime/std
```

có thể dùng:

```text
C ABI
OS APIs
LLVM
system libraries
```

Nhưng final architecture phải thay thế từng boundary bằng Axiom implementation.

---

# 197.44. ABI boundary của std

Public `std` API không mặc định có stable binary ABI.

Nếu cần:

```text
@stable_abi
```

hoặc package-level ABI contract.

Điều này cho phép std được tối ưu/reorganize mà không khóa implementation quá sớm.

---

# 197.45. No hidden allocation

Một API không được âm thầm allocate nếu semantic contract nói:

```text
nonallocating
```

Ví dụ:

```text
Str.len()
```

không allocation.

Compiler/IDE có thể kiểm tra effect metadata.

---

# 197.46. Blocking semantics

API có thể phân biệt:

```text
nonblocking
blocking
may_block
async
```

Ví dụ:

```text
File.read()
```

có thể blocking.

```text
AsyncFile.read()
```

có suspension.

Compiler không tự biến synchronous call thành async.

---

# 197.47. Synchronization semantics

Library API phải khai báo synchronization effects.

Ví dụ:

```text
Mutex.lock()
```

có:

```text
synchronization
may_block
capability acquisition
```

Trong khi:

```text
Atomic.load(Relaxed)
```

có atomic effect nhưng không nhất thiết blocking.

---

# 197.48. Standard library và zero-cost abstraction

Mục tiêu:

```text
high-level API
      ↓
compiler specialization
      ↓
same machine code as hand-written low-level version
```

khi abstraction không yêu cầu runtime behavior.

Không tuyên bố mọi abstraction luôn zero-cost.

---

# 197.49. `std` không phải language feature dump

Không đưa vào Core:

```text
File
HTTP
JSON
Regex
Database
GUI
Image
Audio
```

Chúng là libraries.

Core chỉ cung cấp nền tảng để xây chúng.

---

# 197.50. Standard Library Layer

Kiến trúc cuối:

```text
┌──────────────────────────────────────────┐
│                Application               │
├──────────────────────────────────────────┤
│ std / domain libraries                   │
│ net / fs / process / GUI / serialization │
├──────────────────────────────────────────┤
│ os / sys / runtime adapters              │
├──────────────────────────────────────────┤
│ alloc / collections / async / sync       │
├──────────────────────────────────────────┤
│ core library                             │
├──────────────────────────────────────────┤
│ Axiom Language Core                      │
├──────────────────────────────────────────┤
│ Target / ABI / Machine                   │
└──────────────────────────────────────────┘
```

Dependency direction:

```text
Application
    ↓
std
    ↓
alloc/core
    ↓
os/sys/runtime
    ↓
platform
```

nhưng các dependency cụ thể chỉ được kéo khi reachable.

---

# 197.51. Invariants — Standard Library

### `ASTDL-20`
Language Core shall remain independent of the hosted standard library.

### `ASTDL-21`
Core library shall not require a heap, OS, filesystem, network, thread runtime, or async executor.

### `ASTDL-22`
Dynamic allocation facilities shall reside above Core.

### `ASTDL-23`
Hosted APIs shall not be mandatory dependencies of freestanding programs.

### `ASTDL-24`
Importing a package/module shall not imply linking all declarations within it.

### `ASTDL-25`
Library linking shall operate on declaration/code reachability.

### `ASTDL-26`
Unused standard-library subsystems shall be removable.

### `ASTDL-27`
Platform-specific APIs shall remain isolated from platform-neutral APIs.

### `ASTDL-28`
Safe standard-library wrappers may encapsulate unsafe/system boundaries.

### `ASTDL-29`
Compiler intrinsics shall have explicit semantic identities and contracts.

### `ASTDL-30`
Intrinsic recognition shall not depend on user-visible symbol names alone.

### `ASTDL-31`
Generic compilation may use monomorphization, specialization, or code sharing according to optimization policy.

### `ASTDL-32`
Generic code sharing shall not violate type-specific semantic or ABI requirements.

### `ASTDL-33`
Code-size optimization shall not change program semantics.

### `ASTDL-34`
Standard-library APIs shall expose relevant cost/effect information to compiler tooling.

### `ASTDL-35`
Allocation, blocking, synchronization, invalidation, and external effects shall be representable in API metadata.

### `ASTDL-36`
Standard-library metadata shall be queryable through CompilerDB.

### `ASTDL-37`
AI tooling shall be able to obtain structured API facts without parsing the entire library source.

### `ASTDL-38`
Standard-library abstractions shall not hide externally observable costs.

### `ASTDL-39`
Core traits shall remain independent of OS-specific facilities.

### `ASTDL-40`
Standard-library APIs shall not implicitly introduce unrelated runtime capabilities.

### `ASTDL-41`
Compiler special treatment of standard APIs shall be based on semantic identity.

### `ASTDL-42`
Standard-library implementations may be rewritten without changing Core semantics.

### `ASTDL-43`
Stable ABI shall be explicit rather than implicitly imposed on all standard-library APIs.

### `ASTDL-44`
Freestanding and embedded environments shall be able to use Core without hosted `std`.

### `ASTDL-45`
The standard library shall be implementable in Axiom itself in the self-hosted architecture.

### `ASTDL-46`
Standard-library runtime dependencies shall participate in RuntimeGraph.

### `ASTDL-47`
Platform adapters shall not leak foreign-language ownership models into safe Axiom APIs.

### `ASTDL-48`
A library abstraction shall be zero-cost where its semantic contract permits complete compile-time elimination.

### `ASTDL-49`
The standard library shall not become a mandatory monolithic runtime.

### `ASTDL-50`
Library layering shall preserve the separation between language semantics, reusable library abstractions, OS interfaces, runtime implementation, and platform ABI.

---

# Kết quả BOOTSTRAP-197

Đến đây Axiom có một boundary rất rõ:

```text
                 AXIOM
                   │
        ┌──────────┴──────────┐
        │                     │
   LANGUAGE CORE          CORE LIBRARY
        │                     │
        └──────────┬──────────┘
                   │
                ALLOC
                   │
          ┌────────┴────────┐
          │                 │
         SYS               OS
          │                 │
          └────────┬────────┘
                   │
                RUNTIME
                   │
               PLATFORM
```

Quan trọng nhất:

**`std` không phải runtime.**

**`std` không phải một DLL khổng lồ.**

**`std` không phải một phần của language syntax.**

Nó là một tập các thư viện có dependency graph có thể được compiler phân tích và linker cắt bỏ.

---

# BOOTSTRAP-198 — GUI, Application Framework, Event Loop & Native UI Architecture

**TRẠNG THÁI: NEXT**

Axiom đã có:

- native executable
- OS abstraction
- runtime composition
- GPU
- async
- concurrency
- package system
- standard library
- FFI

Bước tiếp theo cần giải quyết một mục tiêu ban đầu rất quan trọng của Axiom:

> **Có GUI hiện đại, đẹp, hiệu năng native, nhưng không biến GUI thành một phần bắt buộc của Core hoặc kéo một framework khổng lồ vào mọi binary.**

Cần khóa:

```text
Axiom Core
   ↓
Window/Event abstraction
   ↓
Native platform backend
   ↓
GPU renderer
   ↓
Widget/UI framework
```

và đặc biệt:

- GUI có phải standard library không?
- native widget hay custom-rendered?
- retained-mode hay immediate-mode?
- event loop có nằm trong runtime không?
- GUI thread affinity.
- async + GUI integration.
- GPU rendering.
- text shaping/Unicode.
- accessibility.
- DPI/scaling.
- Windows/Linux/macOS/iOS/Android.
- WASM/WebGPU.
- headless build.
- embedding native controls.
- FFI với Cocoa/Win32/Wayland/X11.
- GUI binary size.
- hot reload.
- declarative UI.
- AI-generated UI.
- data binding.
- reactive state.
- layout engine.
- animation/timeline.

Đây sẽ là **BOOTSTRAP-198**.