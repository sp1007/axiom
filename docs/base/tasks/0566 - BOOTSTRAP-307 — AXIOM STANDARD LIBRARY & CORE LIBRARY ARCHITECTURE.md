# BOOTSTRAP-307 — AXIOM STANDARD LIBRARY & CORE LIBRARY ARCHITECTURE

## 1. Mục tiêu

Thiết kế **Standard Library của Axiom** sao cho:

- Core Language nhỏ nhưng đủ mạnh;
- Standard Library không trở thành “runtime trá hình”;
- API nhất quán với ownership/capability/concurrency/async đã frozen;
- không ép chương trình link những thứ không sử dụng;
- hỗ trợ từ embedded/freestanding đến desktop/server/GPU;
- tận dụng compiler để tối ưu abstraction xuống zero-cost;
- Standard Library cuối cùng có thể được viết bằng Axiom.

Nguyên tắc:

> **Language defines semantics. Library provides reusable capabilities. Runtime provides execution services.**

Ba lớp phải tách biệt rõ ràng:

```text
Axiom Language Core
        │
        ├── Compiler intrinsic
        │
Standard Library
        │
        ├── Runtime Components
        │
        └── Platform / OS / FFI
```

---

# 2. Ba tầng API

## 2.1 Core Language

Chứa những thứ compiler bắt buộc phải hiểu:

```text
struct
enum
trait
fn
match
ownership
view
mut_view
async
comptime
atomic semantics
```

Không đưa:

```text
Vec
String
HashMap
File
Socket
Thread
Mutex
```

vào language syntax.

---

## 2.2 Core Library

Là thư viện gần language nhất, có thể được compiler đặc biệt tối ưu.

Ví dụ:

```text
Option<T>
Result<T, E>
Vec<T>
Array<T, N>
Slice<T>
String
Box<T>
Rc<T>
Arc<T>
Range
Iterator
```

Core Library phải có dependency cực thấp.

---

## 2.3 Standard Library

Các capability cấp cao:

```text
std.fs
std.net
std.thread
std.async
std.process
std.time
std.crypto
std.compress
std.serialization
std.unicode
std.logging
std.testing
std.gpu
```

Không module nào được mặc định kéo toàn bộ `std`.

---

# 3. Không có “God Namespace”

Không thiết kế:

```text
std = mọi thứ
```

mà chia capability:

```text
std.core
std.collections
std.text
std.io
std.fs
std.net
std.thread
std.async
std.sync
std.process
std.time
std.crypto
std.compress
std.serialization
std.gpu
std.test
```

Compiler/build graph chỉ link module thực sự dùng.

---

# 4. Core Library không được phụ thuộc OS

Ví dụ:

```text
Vec<T>
Option<T>
Result<T,E>
String
HashMap
Iterator
```

không được phụ thuộc:

```text
Windows
Linux
POSIX
pthread
libc
```

Điều này cho phép chúng chạy trên:

```text
Windows
Linux
macOS
WASM
Embedded
Kernel
GPU
```

nếu semantic phù hợp.

---

# 5. Primitive Collections

Core Library phải có các cấu trúc dữ liệu nền tảng:

```text
Array<T,N>
Slice<T>
Vec<T>
Deque<T>
List<T>
Map<K,V>
Set<T>
HashMap<K,V>
HashSet<T>
BTreeMap<K,V>
BTreeSet<T>
```

Nhưng không nhất thiết tất cả nằm trong `core`.

Phân tầng:

```text
core:
    Array
    Slice
    Vec
    Option
    Result

collections:
    HashMap
    HashSet
    BTreeMap
    BTreeSet
    Deque
```

---

# 6. Vec<T>

`Vec<T>` là dynamic contiguous collection.

Semantic:

```text
Vec<T> {
    storage
    length
    capacity
}
```

Invariant:

```text
0 <= length <= capacity
```

Ownership:

```text
Vec<T> owns elements
```

Copy:

```text
Vec<T> !Copy
```

Move:

```text
let b = a
```

chuyển ownership.

---

# 7. View Integration

Ví dụ:

```text
fn sum(xs: view<i32>) -> i32
```

Có thể gọi:

```text
sum(numbers)
```

Compiler tạo ephemeral read capability.

Không cần:

```text
&numbers
```

hoặc:

```text
numbers.as_slice()
```

trong trường hợp đơn giản.

---

# 8. Mut View Integration

```text
fn normalize(xs: mut_view<f32>) {
    ...
}
```

Compiler đảm bảo:

```text
Vec storage
    ↓
exclusive mutable capability
```

không tồn tại conflicting access.

Nếu:

```text
normalize(a)
normalize(a)
```

tuần tự thì hợp lệ.

Nếu hai execution domain cùng truy cập:

```text
spawn(normalize(a))
spawn(normalize(a))
```

phải bị chặn nếu không có synchronization/transfer hợp lệ.

---

# 9. String Architecture

Axiom không được coi mọi string là một loại duy nhất.

Tách:

```text
ByteString
Utf8
Text
Char
CodePoint
Grapheme
```

Mục tiêu:

```text
byte processing
```

không kéo Unicode database.

Ví dụ:

```text
ByteString
```

có thể chạy freestanding.

Trong khi:

```text
Unicode.normalize()
```

có thể kéo Unicode data.

---

# 10. String Ownership

String sở hữu buffer:

```text
String
```

View:

```text
view<u8>
view<char>
```

hoặc API semantic tương đương.

Không cho phép implicit conversion gây allocation.

Ví dụ:

```text
fn print(s: view<str>)
```

truyền String không được tạo bản copy mới.

---

# 11. Option / Result

Đây là Core Library primitive-level.

```text
Option<T> =
    Some(T)
    None
```

```text
Result<T,E> =
    Ok(T)
    Err(E)
```

Compiler phải hiểu đủ sâu để:

- exhaustive match;
- niche optimization;
- branch optimization;
- move/drop chính xác;
- ABI optimization.

Nhưng `Option`/`Result` vẫn là **library-defined algebraic types**, không phải primitive syntax riêng.

---

# 12. Iterator Architecture

Iterator là trait:

```text
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Compiler có thể inline:

```text
map
filter
fold
zip
enumerate
take
skip
```

thành loop machine code.

Mục tiêu:

```text
high-level iterator
        ↓
zero abstraction overhead
        ↓
ordinary optimized loop
```

Không cần eager intermediate allocation.

---

# 13. Iterator Fusion

Compiler/optimizer được phép nhận diện:

```text
map
    → filter
    → map
    → fold
```

và tạo một loop duy nhất.

Nhưng đây là optimization, không phải semantic requirement.

Nếu compiler không fusion được thì chương trình vẫn đúng.

---

# 14. Error Architecture

Standard Library không được dùng exception làm mặc định.

API:

```text
fn read_file(...) -> Result<File, IOError>
```

là semantic contract.

Panic chỉ dành cho:

```text
programmer invariant violation
unrecoverable failure
explicit panic
```

Không dùng panic để biểu diễn normal recoverable errors.

---

# 15. I/O

Thiết kế layered:

```text
std.io
    ├── Reader
    ├── Writer
    ├── Read
    ├── Write
    └── Buffered
```

OS-specific:

```text
std.fs
std.net
std.process
```

Ví dụ:

```text
trait Reader {
    fn read(...)
}
```

Có thể có implementation:

```text
File
Socket
MemoryBuffer
Pipe
Console
Device
```

---

# 16. Sync Library

Các primitive:

```text
Mutex<T>
RwLock<T>
Semaphore
Condvar
Once
Barrier
Atomic<T>
```

Không object header bắt buộc.

Ví dụ:

```text
Mutex<T>
```

là một struct chứa:

```text
lock state
owned value
platform data
```

nếu cần.

---

# 17. Guard Model

```text
let guard = mutex.lock()
```

trả về capability/guard.

Guard:

```text
!Copy
Drop
```

Drop:

```text
unlock
```

Compiler hiểu ownership của guard.

Không cần:

```text
mutex.unlock(guard)
```

trong API thông thường.

---

# 18. Thread API

Thread library:

```text
thread.spawn(...)
thread.join(...)
thread.current()
thread.sleep(...)
```

Nhưng:

```text
Send
Share
```

vẫn là compiler-verified semantic traits.

API không được tự tin rằng programmer sẽ “tự chịu trách nhiệm”.

---

# 19. Async API

Tách:

```text
std.async
std.async.io
std.async.sync
```

Core chỉ biết:

```text
Future
Poll
Waker
async
await
```

Library cung cấp:

```text
spawn
join
timeout
select
channel
cancel
executor
```

---

# 20. Structured Concurrency

API mặc định nên hướng tới:

```text
scope {
    spawn(task1)
    spawn(task2)
}
```

scope kết thúc chỉ khi child tasks được xử lý theo contract.

Detached task phải explicit:

```text
detach(task)
```

Không để accidental background task trở thành nguồn lifetime bug.

---

# 21. Channel

Channel là ownership-transfer abstraction:

```text
Sender<T>
Receiver<T>
```

Send:

```text
sender.send(value)
```

chuyển ownership.

Receive:

```text
receiver.recv() -> Result<T, ChannelError>
```

Không cần copy dữ liệu nếu `T` movable.

---

# 22. Serialization

Không nhập serialization vào Core.

Các layer:

```text
std.serialization
    ├── Binary
    ├── JSON
    ├── CBOR
    ├── MessagePack
    └── Custom
```

Quan trọng:

> Memory representation ≠ wire representation.

Không được serialize struct bằng cách mặc định dump raw memory.

---

# 23. Reflection

Runtime reflection không phải mặc định.

Comptime reflection:

```text
Type
Field
Method
Variant
Trait
```

có thể được dùng để generate:

```text
serialization
debug formatting
GUI binding
RPC
schema
```

Runtime metadata chỉ emit khi user yêu cầu.

---

# 24. Formatting

Core formatting abstraction:

```text
Display
Debug
Format
```

Ví dụ:

```text
print("value = {}", x)
```

Compiler có thể compile format string tại compile time.

Nếu format string constant:

```text
format parser
```

có thể chạy ở comptime.

---

# 25. Time

Tách rõ:

```text
Duration
Instant
Timestamp
CalendarDate
TimeZone
```

`Instant` dùng monotonic clock.

`Timestamp` có thể phụ thuộc wall clock.

Không được dùng timestamp để đo duration nếu monotonic clock có sẵn.

---

# 26. Random

Tách:

```text
PRNG
SecureRandom
SystemRandom
```

Không coi random là một primitive duy nhất.

Comptime random phải explicit vì ảnh hưởng reproducibility/build cache.

---

# 27. Crypto

Crypto library phải có abstraction:

```text
Hash
HMAC
AEAD
Signature
KeyExchange
KDF
```

Không đưa thuật toán crypto vào compiler Core.

Compiler chỉ tối ưu ordinary arithmetic/vector/constant-time contracts khi được khai báo.

---

# 28. GPU Library

API high-level:

```text
Device
DeviceBuffer<T>
Kernel
GpuEvent
Stream
```

nhưng chúng sử dụng GPU semantic đã frozen:

```text
ownership
view
mut_view
Send
storage domain
execution domain
```

Không tạo một memory model thứ hai cho GPU.

---

# 29. Testing Library

Testing phải hỗ trợ:

```text
unit test
integration test
property test
benchmark
compile test
diagnostic test
```

Compiler-native:

```text
@test
@benchmark
@compile_fail
```

là metadata/attribute, không cần language primitive lớn.

---

# 30. Package Dependency

Standard Library phải được chia thành package/module độc lập.

Ví dụ:

```text
axiom.core
axiom.collections
axiom.text
axiom.io
axiom.fs
axiom.net
axiom.async
axiom.sync
axiom.crypto
axiom.serialization
axiom.gpu
```

Một package không được phụ thuộc ngược vào package cấp cao hơn.

Dependency graph phải DAG.

---

# 31. Platform Abstraction

Không để:

```text
std.fs.File
```

phụ thuộc trực tiếp vào Linux implementation trong source-level API.

Kiến trúc:

```text
Public API
    ↓
Semantic platform interface
    ↓
Platform provider
    ├── Windows
    ├── Linux
    ├── macOS
    ├── WASM
    └── Embedded
```

Compiler/build system chọn provider.

---

# 32. Allocator-aware APIs

Các collection không nên hard-code một allocator duy nhất.

Có thể hỗ trợ:

```text
Vec<T>
Vec<T, A>
```

hoặc compiler/library design tương đương.

Nhưng allocator parameter không được làm API trở nên quá verbose.

Compiler có thể infer allocator trong trường hợp thông thường.

Mục tiêu:

```text
simple code
```

và vẫn cho phép:

```text
custom allocator
arena
pool
embedded memory
```

---

# 33. No Hidden Allocation

API phải có contract rõ ràng về allocation.

Ví dụ:

```text
sort()
```

không được âm thầm heap allocate nếu API contract nói:

```text
NoAllocation
```

Có thể có effect/capability metadata:

```text
@allocates
@noalloc
@blocking
@async
```

Những annotation này nên được compiler kiểm tra thay vì chỉ là documentation.

---

# 34. Library Effect Contracts

Standard Library API có thể công bố effect:

```text
ReadMemory
WriteMemory
Allocate
IO
Blocking
Async
Atomic
Foreign
Panic
```

Compiler dùng chúng cho:

- optimization;
- diagnostics;
- async safety;
- realtime verification;
- kernel/GPU legality;
- freestanding validation.

Ví dụ:

```text
@noalloc
@nonblocking
fn process(...)
```

nếu implementation vi phạm contract → compile error.

---

# 35. ABI Boundary

Standard Library không được vô tình biến thành ABI contract.

Ví dụ:

```text
Vec<T>
String
HashMap<K,V>
```

không mặc định có stable binary layout.

Nếu cần FFI:

```text
@repr(C)
```

hoặc một ABI-specific wrapper.

---

# 36. Standard Library Self-Hosting

Mục tiêu cuối:

```text
axiom.core       → Axiom
axiom.collections → Axiom
axiom.text        → Axiom
axiom.io          → Axiom
axiom.thread      → Axiom
axiom.async       → Axiom
```

Platform layer có thể chứa một lượng nhỏ:

```text
extern
intrinsic
unsafe
assembly
```

nhưng phải cô lập.

Không để toàn bộ Standard Library trở thành wrapper quanh C.

---

# 37. Compiler Intrinsics

Một số API có thể cần intrinsic:

```text
size_of
align_of
offset_of
atomic
simd
bit operations
CPU feature detection
prefetch
fence
trap
unreachable
```

Nhưng API public vẫn nên là Axiom-level abstraction.

Ví dụ:

```text
atomic.load()
```

thay vì bắt programmer viết intrinsic opcode.

---

# 38. Library Optimization Contract

Compiler phải có cơ chế nhận diện các library abstraction quan trọng:

```text
#[compiler_intrinsic]
#[compiler_known]
#[lang_item]
```

nhưng phải cực kỳ hạn chế.

Mục tiêu:

> Compiler biết đủ về Standard Library để tối ưu, nhưng Standard Library không trở thành một phần không thể thay thế của language semantics.

---

# 39. Standard Library Dependency Graph

Kiến trúc đề xuất:

```text
                 ┌──────────────┐
                 │  Axiom Core  │
                 └──────┬───────┘
                        │
             ┌──────────▼──────────┐
             │     axiom.core      │
             └──────────┬──────────┘
                        │
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
 collections          text             math
       │                │                │
       └────────┬───────┴───────┬────────┘
                ▼               ▼
               io              sync
                │               │
          ┌─────┴─────┐         │
          ▼           ▼         ▼
         fs          net      thread
          │           │         │
          └─────┬─────┴─────────┘
                ▼
              async
```

Không cho:

```text
core → std
std.fs → compiler
compiler → std.fs
```

dependency phải một chiều.

---

# 40. Definition of Done

BOOTSTRAP-307 hoàn thành khi:

1. Axiom có architecture rõ ràng cho Core Library và Standard Library.
2. Core không phụ thuộc OS/runtime.
3. Collection APIs tương thích ownership/view/mut_view.
4. String/Unicode được phân tầng.
5. Result/Option được compiler tối ưu.
6. Iterator có khả năng zero-cost abstraction.
7. Sync/Thread/Async dùng đúng semantic đã frozen.
8. Channel là ownership-transfer abstraction.
9. Standard Library không ép runtime dependency.
10. Allocation contract có thể được compiler kiểm tra.
11. Effect contracts có thể tích hợp với compiler.
12. FFI không phụ thuộc layout nội bộ của Standard Library.
13. Platform implementations tách khỏi public API.
14. Standard Library có thể self-host bằng Axiom.
15. Các module không sử dụng không được link vào executable.

---

## Invariants

```text
ASTDL-20
Core Library does not depend on OS facilities.

ASTDL-21
Standard Library is modular.

ASTDL-22
Unused library modules are not linked.

ASTDL-23
Library abstractions obey Core ownership semantics.

ASTDL-24
Library views obey capability rules.

ASTDL-25
Library APIs cannot silently introduce semantic aliasing.

ASTDL-26
Library APIs must declare observable allocation/blocking/async effects where required.

ASTDL-27
Memory representation is distinct from serialization representation.

ASTDL-28
Standard Library types have no stable ABI unless explicitly declared.

ASTDL-29
FFI uses explicit representation and ABI contracts.

ASTDL-30
Standard Library does not require a monolithic runtime.

ASTDL-31
Core Library remains usable in freestanding environments.

ASTDL-32
Async library does not redefine Core async semantics.

ASTDL-33
Concurrency library does not bypass Send/Share verification.

ASTDL-34
GPU library uses the unified ownership/capability model.

ASTDL-35
Platform implementations are replaceable providers.

ASTDL-36
Standard Library dependency graph is acyclic.

ASTDL-37
Compiler intrinsics are implementation mechanisms, not general escape hatches.

ASTDL-38
Library optimization cannot change observable semantics.

ASTDL-39
Standard Library must be implementable primarily in Axiom itself.

ASTDL-40
No Standard Library abstraction may require hidden global runtime state unless explicitly specified.

ASTDL-41
No API may silently allocate when its contract promises no allocation.

ASTDL-42
No API may silently block when its contract promises non-blocking behavior.

ASTDL-43
No library type implicitly becomes a language primitive merely because the compiler optimizes it.

ASTDL-44
Library capability requirements participate in the build graph.

ASTDL-45
Standard Library components may be independently versioned and replaced subject to ABI/API contracts.
```