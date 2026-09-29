# BOOTSTRAP-330 — AXIOM STANDARD LIBRARY SEMANTIC FOUNDATION & PLATFORM PORTABILITY LAYER

Sau Package Manager-329, bước tiếp theo hợp lý là **đóng khung Standard Library thực sự của Axiom**.

Trước đây task 307 đã xác định kiến trúc Standard Library ở mức tổng thể. Nhưng sau khi ABI, FFI, Platform, Target và Package đã được hoàn thiện, cần đặc tả sâu hơn **semantic boundary của từng lớp thư viện**, để tránh Standard Library biến thành một “runtime khổng lồ” hoặc một bản sao của C++/Rust/Java.

Mục tiêu của task này là:

> **Axiom Core đủ nhỏ để làm nền tảng; Standard Library đủ mạnh để viết ứng dụng thực tế; nhưng mọi capability nặng đều optional và không làm phình binary.**

---

# 1. Kiến trúc 4 tầng

Standard Library được chia thành:

```text
                    Axiom Core
                        │
                        ▼
                 axiom.core
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
        axiom.foundation      axiom.alloc
              │                   │
              └─────────┬─────────┘
                        ▼
                  axiom.std
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Platform       Network       Graphics
```

### Core

Ngôn ngữ + semantic primitives.

### Foundation

Các abstraction gần như mọi chương trình cần.

### Alloc

Allocation/data structures.

### Std

API ứng dụng và platform.

---

# 2. `axiom.core`

Core library phải cực nhỏ.

Chỉ chứa những thứ gắn trực tiếp với semantic language:

```text
Option
Result
Ordering
Range
Iterator primitive contracts
Copy
Clone
Drop
Send
Share
Sized
Fn
FnMut
FnOnce
```

và các primitive utilities thực sự cần cho compiler.

Không chứa:

```text
File
Socket
ThreadPool
HTTP
JSON
Regex
GUI
```

---

# 3. `Option<T>`

`Option<T>` là type nền tảng.

```axiom
enum Option<T> {
    None,
    Some(T),
}
```

Không có:

```text
null
```

trong safe Core.

Compiler có thể tối ưu:

```text
Option<Box<T>>
Option<*const T>
Option<NonZero<T>>
```

bằng niche representation khi hợp lệ.

Nhưng optimization này không trở thành ABI contract mặc định.

---

# 4. `Result<T,E>`

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Không có exception mặc định.

Compiler/tooling cần hỗ trợ ergonomics:

```axiom
let value = operation()?;
```

`?` chỉ là control-flow sugar:

```text
Ok(x)  → continue
Err(e) → return Err(e)
```

Không phải exception mechanism.

---

# 5. Error hierarchy

Không tạo:

```text
Exception
  ├── IOException
  ├── NetworkException
  └── ...
```

Thay vào đó:

```text
Error type
ErrorKind
Context
Source
```

Một error có thể là:

```axiom
struct IoError {
    kind: IoErrorKind,
    native_code: i64,
}
```

Application-specific error dùng enum/struct riêng.

---

# 6. `Drop`

`Drop` là compiler-known trait.

Ví dụ:

```axiom
trait Drop {
    fn drop(self);
}
```

nhưng implementation semantics được compiler xử lý đặc biệt.

Không cho programmer gọi `drop` như một ordinary method để phá ownership model.

API:

```text
drop(value)
```

là compiler intrinsic/semantic operation.

---

# 7. `Clone`

`Clone` phải khác `Copy`.

```text
Copy:
    cheap semantic duplication

Clone:
    explicit potentially-expensive duplication
```

Ví dụ:

```axiom
let b = a.clone();
```

không được compiler tự biến thành Copy.

---

# 8. Collection architecture

Standard Library cần:

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

Nhưng không phải tất cả đều thuộc Foundation.

---

# 9. `Vec<T>`

Semantic contract:

```text
Vec<T> {
    pointer/storage
    length
    capacity
}
```

nhưng physical representation không phải ABI stable.

Invariant:

```text
0 <= len <= capacity
```

Operations:

```text
push
pop
insert
remove
reserve
resize
clear
truncate
```

Nếu có live `view<T>` hoặc `mut_view<T>`:

```text
reallocation
```

phải bị ngăn chặn cho tới khi capability hết hiệu lực.

---

# 10. `String`

Axiom phải phân biệt:

```text
String
Utf8String
ByteBuffer
```

Không để một type vừa có semantics text vừa raw bytes.

Đề xuất:

```text
String
```

là valid UTF-8 owned text.

```text
ByteBuffer
```

là arbitrary bytes.

```text
view<u8>
```

là raw byte view.

---

# 11. Unicode

Unicode support không nên là Core language requirement.

```text
axiom.text
```

có:

```text
UnicodeScalar
Grapheme
Utf8
Utf16
Normalization
CaseMapping
```

Một freestanding numeric program không cần link Unicode database.

---

# 12. Iterator

Iterator không nên yêu cầu object/vtable.

Thiết kế:

```axiom
trait Iterator {
    type Item;

    fn next(mut self) -> Option<Self::Item>;
}
```

Generic static dispatch mặc định.

Ví dụ:

```axiom
for x in values {
    ...
}
```

lower thành iterator protocol.

Compiler có thể inline toàn bộ abstraction.

---

# 13. Iterator adapters

Các adapter:

```text
map
filter
take
skip
zip
enumerate
chain
flat_map
fold
reduce
```

nên là zero-cost generic abstractions.

Ví dụ:

```axiom
values
    .filter(...)
    .map(...)
    .sum()
```

không tạo chain of heap objects.

Compiler có thể biến toàn bộ thành loop.

---

# 14. Slice/View

Standard Library không tạo abstraction mới thay cho Core:

```text
view<T>
mut_view<T>
```

Collection APIs sử dụng trực tiếp capability model.

Ví dụ:

```axiom
fn sort(data: mut_view<i32>)
```

không cần:

```text
&mut [i32]
```

hay lifetime syntax.

---

# 15. Sorting

Generic:

```axiom
sort(data: mut_view<T>, less: fn(T,T)->bool)
```

có thể được specialize thành:

```text
int sort
float sort
struct sort
SIMD sort
```

Compiler có thể inline comparator khi static.

---

# 16. Map/HashMap

HashMap phải tách:

```text
semantic map
```

khỏi:

```text
hash algorithm
```

Không hard-code một hash algorithm vào language.

Cho phép:

```axiom
HashMap<K,V,H>
```

và default hasher ở library.

Security-sensitive applications có thể chọn randomized hashing.

Performance-sensitive code có thể chọn specialized hash.

---

# 17. Allocator abstraction

Allocator thuộc `axiom.alloc`.

Trait:

```axiom
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
}
```

nhưng allocator contract phải tương thích với memory model.

Không được tạo abstraction khiến compiler phải dynamic dispatch allocator ở mọi allocation.

Static generic allocator là default.

---

# 18. Allocation strategies

Standard Library cần:

```text
GlobalAllocator
SystemAllocator
Arena
Pool
Slab
StackAllocator
LinearAllocator
BumpAllocator
```

Mỗi loại có semantic contract riêng.

Ví dụ:

```axiom
Arena<T>
```

có lifetime của toàn arena.

Compiler có thể optimize allocation khi object không escape.

---

# 19. Collections và allocator

Collections có thể parameterize:

```axiom
Vec<T, A>
```

nhưng default:

```axiom
Vec<T>
```

dùng allocator mặc định.

Programmer không bị bắt buộc viết allocator parameter.

Compiler/library inference điền default.

---

# 20. Smart pointer architecture

Axiom không có:

```text
unique_ptr
shared_ptr
weak_ptr
```

ở Core.

Standard Library cung cấp:

```text
Box<T>
Rc<T>
Arc<T>
Weak<T>
```

với semantics đã frozen.

### Box

single ownership.

### Rc

single-thread shared ownership.

### Arc

cross-thread shared ownership.

### Weak

non-owning logical link.

---

# 21. `Box<T>`

```axiom
let x = Box.new(value)
```

là semantic owned dynamic storage.

Nhưng compiler được phép:

```text
stack promote
register scalarize
allocation eliminate
```

nếu physical address không observable.

Nếu API yêu cầu stable address:

```text
Box
```

phải trở thành storage contract phù hợp.

---

# 22. `Arc<T>`

`Arc<T>` chỉ cung cấp shared ownership.

Không có:

```text
Arc<T> ⇒ T thread-safe
```

Muốn mutate:

```axiom
Arc<Mutex<T>>
```

hoặc:

```axiom
Arc<Atomic<T>>
```

---

# 23. Synchronization library

`axiom.sync`:

```text
Mutex
RwLock
Semaphore
Condvar
Barrier
Once
OnceCell
Atomic
Channel
```

được xây trên concurrency semantics của Core.

Không tự định nghĩa memory model mới.

---

# 24. Channel

Channel:

```text
Sender<T>
Receiver<T>
```

ownership transfer là Move.

Ví dụ:

```axiom
sender.send(buffer)
```

sau đó sender không còn ownership của `buffer`.

Đây là zero-copy concurrency primitive quan trọng.

---

# 25. Sync vs async channel

Không nên cố hợp nhất thành một type.

```text
Channel<T>
AsyncChannel<T>
```

là hai abstraction khác nhau.

Sync channel có:

```text
blocking
```

Async channel:

```text
Future
Waker
executor
```

---

# 26. Async standard library

`axiom.async` cung cấp:

```text
Future
Stream
Task
CancellationToken
JoinHandle
AsyncChannel
AsyncMutex
AsyncRwLock
```

nhưng **executor không thuộc Core**.

Các executor có thể:

```text
single-thread
multi-thread
work-stealing
embedded
deterministic
io_uring
IOCP
```

---

# 27. Structured concurrency

API mặc định nên hướng tới:

```axiom
scope {
    spawn(...)
    spawn(...)
}
```

scope kết thúc chỉ khi child tasks được xử lý theo contract.

Detached task phải explicit.

Điều này giúp tránh task "mồ côi".

---

# 28. Time library

```text
Instant
SystemTime
Duration
Deadline
Clock
Timer
```

`Instant` dùng monotonic source.

`SystemTime` dùng wall clock.

Không cho phép arithmetic giữa hai domain nếu chưa convert đúng.

---

# 29. IO library

```text
Reader
Writer
Read
Write
Seek
Flush
BufReader
BufWriter
```

Trait-based.

Ví dụ:

```axiom
fn copy<R: Reader, W: Writer>(
    src: mut R,
    dst: mut W
)
```

Compiler có thể specialize static dispatch.

---

# 30. Filesystem

```text
Path
File
Directory
DirectoryEntry
Metadata
Permissions
```

File là owning resource.

API:

```text
open
create
read
write
seek
flush
close
```

`close()` có thể trả error.

Drop vẫn deterministic.

---

# 31. Network

Tách:

```text
TcpStream
TcpListener
UdpSocket
UnixStream
UnixListener
TlsStream
```

không tạo một `Socket` object hierarchy khổng lồ.

Trait:

```text
Read
Write
AsyncRead
AsyncWrite
```

cho phép generic code.

---

# 32. HTTP

HTTP không thuộc `axiom.core`.

Có thể là:

```text
axiom.net.http
```

với:

```text
Request
Response
Headers
Body
Client
Server
```

TLS là dependency riêng.

Một CLI không dùng network không link HTTP/TLS.

---

# 33. Serialization

Không đưa JSON vào Core.

```text
axiom.codec
axiom.json
axiom.cbor
axiom.toml
axiom.binary
```

Serialization có thể dùng comptime/derive:

```axiom
@derive(Serialize, Deserialize)
struct User {
    ...
}
```

Compiler-generated implementation đi qua semantic verification bình thường.

---

# 34. Reflection

Runtime reflection không mặc định.

Comptime:

```axiom
type_info<T>()
fields<T>()
methods<T>()
```

có thể generate serializer.

Nếu muốn runtime metadata:

```text
@emit_metadata
```

phải explicit.

---

# 35. Logging

Không để logging thành runtime bắt buộc.

```text
axiom.log
```

có:

```text
trace
debug
info
warn
error
```

Compiler có thể loại bỏ:

```text
debug logs
```

theo build profile.

---

# 36. Testing

Standard Library cần:

```text
axiom.test
```

test function:

```axiom
@test
fn test_add() {
    assert(add(1,2) == 3)
}
```

Test binary không phải runtime dependency của production binary.

---

# 37. Benchmark

```axiom
@bench
fn benchmark_sort() {
    ...
}
```

Benchmark infrastructure hỗ trợ:

```text
iterations
warmup
statistics
CPU counters
allocation counters
```

PGO subsystem có thể lấy profile từ benchmark.

---

# 38. SIMD

Không tạo một SIMD API gắn cứng với x86.

Foundation cung cấp semantic vector:

```text
Simd<T,N>
```

Compiler lower:

```text
x86 → SSE/AVX
ARM → NEON/SVE
WASM → SIMD
```

nếu target hỗ trợ.

Fallback scalar phải có semantic tương đương.

---

# 39. Math

`axiom.math`:

```text
abs
min
max
sqrt
sin
cos
exp
log
pow
fma
```

phải phân biệt:

```text
strict semantics
fast math
approximate math
```

Ví dụ build profile:

```text
math = strict
```

không được compiler tự ý dùng approximation.

---

# 40. `no_std` tương đương

Không nên copy Rust syntax/terminology.

Axiom nên có profile:

```text
@profile("freestanding")
```

hoặc build configuration:

```text
runtime = none
```

Điều này loại bỏ:

```text
filesystem
network
threads
OS
```

nếu program không sử dụng.

---

# 41. Standard Library capability graph

Ví dụ:

```text
axiom.std
 │
 ├── core
 ├── alloc
 │
 ├── io
 │    └── platform
 │
 ├── fs
 │    └── platform
 │
 ├── net
 │    └── platform
 │
 ├── async
 │    └── executor [optional]
 │
 └── gpu
      └── platform
```

Dependency chỉ xuất hiện khi thực sự được sử dụng.

---

# 42. Runtime components

Standard Library không được ngầm kéo một runtime duy nhất.

Ví dụ program:

```axiom
fn main() {
    println("hello")
}
```

có thể cần:

```text
stdout
allocator
startup
```

nhưng không cần:

```text
network
async executor
thread pool
GPU runtime
reflection
HTTP
```

---

# 43. `std` không phải magic

Mọi API Standard Library cuối cùng phải là Axiom code hoặc một thin compiler/platform intrinsic.

Ví dụ:

```text
File
```

→ Axiom implementation

→ FFI/system call

→ platform contract.

Không được có hàng trăm primitive compiler-only mà programmer không thể inspect.

---

# 44. Intrinsics

Một số operation có thể cần compiler intrinsic:

```text
atomic
SIMD
bit operations
CPU features
memory barriers
stack allocation
unreachable
compiler fence
```

Nhưng intrinsic phải có:

```text
semantic specification
type contract
target contract
verification rules
```

Không biến intrinsic thành "escape hatch".

---

# 45. Standard Library source distribution

Axiom nên hướng tới:

```text
std/
├── core/
├── alloc/
├── collections/
├── text/
├── io/
├── fs/
├── net/
├── sync/
├── async/
├── process/
├── time/
├── crypto/
├── codec/
├── math/
├── gpu/
└── platform/
```

Phần lớn viết bằng Axiom.

Các phần target-specific có thể chứa:

```text
Axiom
FFI
intrinsic
assembly
```

---

# 46. ABI boundary của Standard Library

Public Standard Library API không mặc định là Stable ABI.

Ví dụ:

```text
Vec<T>
String
HashMap<K,V>
```

có thể thay đổi internal representation.

Nếu cần binary-stable API:

```text
@stable_abi
```

và dùng explicit ABI representation.

Điều này giữ freedom cho compiler/library evolution.

---

# 47. Performance contract

Standard Library không hứa:

> abstraction nào cũng zero-cost tuyệt đối.

Thay vào đó từng API có:

```text
Complexity
Allocation behavior
Blocking behavior
Synchronization behavior
Ownership behavior
ABI behavior
```

Ví dụ:

```text
Vec.push
```

có thể:

```text
O(1) amortized
```

và có khả năng allocation.

`sort`:

```text
O(n log n)
```

với implementation-specific optimization.

---

# 48. No hidden expensive behavior

Các operation sau không được âm thầm xảy ra nếu API không nói rõ:

```text
heap allocation
blocking
thread spawn
network access
filesystem access
large clone
global lock
```

Đây là nguyên tắc rất quan trọng cho systems language:

> **High-level syntax không được che giấu một cost model bất ngờ.**

---

# 49. Standard Library documentation metadata

Mỗi API nên machine-readable:

```text
FunctionContract {
    complexity
    allocation
    blocking
    synchronization
    effects
    panic
    ownership
    thread_safety
    target_requirements
}
```

Ví dụ AI tooling có thể hỏi:

```text
"API này có allocate không?"
```

và compiler trả lời chính xác từ contract.

---

# 50. Compiler integration

Standard Library cần compiler-known traits/intrinsics nhưng không compiler-specialize toàn bộ std.

Compiler chỉ có special knowledge cho:

```text
Option
Result
Drop
Iterator lowering
async Future
atomic
SIMD
range
panic/unreachable
allocation primitives
```

Phần còn lại là ordinary Axiom code.

---

# 51. Implementation tree

```text
std/
├── core/
│   ├── option.ax
│   ├── result.ax
│   ├── ordering.ax
│   ├── range.ax
│   └── traits.ax
│
├── alloc/
│   ├── allocator.ax
│   ├── box.ax
│   ├── arena.ax
│   └── pool.ax
│
├── collections/
│   ├── vec.ax
│   ├── deque.ax
│   ├── hashmap.ax
│   ├── hashset.ax
│   └── btree.ax
│
├── text/
│   ├── string.ax
│   ├── utf8.ax
│   └── unicode.ax
│
├── io/
├── fs/
├── net/
├── process/
├── sync/
├── async/
├── time/
├── math/
├── crypto/
├── codec/
├── gpu/
│
└── platform/
    ├── windows/
    ├── linux/
    ├── macos/
    ├── ios/
    ├── android/
    └── wasm/
```

---

# 52. Các invariant

```text
ASTD-01
Standard Library must not redefine Core ownership semantics.

ASTD-02
Standard Library must not require a tracing garbage collector.

ASTD-03
Standard Library must not require a monolithic runtime.

ASTD-04
Unused library capabilities must not enter the final binary.

ASTD-05
Core types must remain available in freestanding environments.

ASTD-06
Platform APIs must remain outside Core.

ASTD-07
OS resources must obey deterministic ownership semantics.

ASTD-08
Fallible cleanup must be explicit.

ASTD-09
Copy and Clone must remain semantically distinct.

ASTD-10
String and raw byte storage must remain semantically distinct.

ASTD-11
Collections must expose their allocation behavior.

ASTD-12
Collection relocation must respect active capabilities.

ASTD-13
Shared ownership must not imply mutable thread-safe access.

ASTD-14
Arc must not imply synchronization of contained data.

ASTD-15
Async APIs must not imply a particular executor.

ASTD-16
Blocking APIs must be distinguishable from async APIs.

ASTD-17
Iterator abstractions should compile away when statically optimizable.

ASTD-18
Standard Library generic abstractions must not require dynamic dispatch by default.

ASTD-19
Runtime reflection must not be mandatory.

ASTD-20
Unicode data must not be mandatory for non-text programs.

ASTD-21
HTTP/TLS/GPU/GUI must not become implicit dependencies.

ASTD-22
SIMD abstractions must remain target-independent at the semantic level.

ASTD-23
Strict and approximate numerical semantics must be distinguishable.

ASTD-24
Standard Library APIs must expose important complexity/cost contracts.

ASTD-25
Hidden allocation is forbidden where the API contract promises allocation-free operation.

ASTD-26
Hidden blocking is forbidden where the API contract promises non-blocking operation.

ASTD-27
Compiler intrinsics must have specified semantic contracts.

ASTD-28
Standard Library source should itself be ordinary Axiom wherever practical.

ASTD-29
Standard Library public API does not imply stable binary ABI.

ASTD-30
Every Standard Library abstraction must compose with ownership, capability, effect, concurrency and target semantics.
```

---

# 53. Kết quả

Sau BOOTSTRAP-330, kiến trúc Axiom có một lớp Standard Library thực sự phù hợp với mục tiêu ban đầu:

```text
                 AXIOM CORE
                     │
        ┌────────────┴────────────┐
        │                         │
   FOUNDATION                  ALLOC
        │                         │
        └────────────┬────────────┘
                     │
                 STANDARD
                  LIBRARY
                     │
       ┌─────────────┼──────────────┐
       │             │              │
      IO            NET            GPU
       │             │              │
   PLATFORM       PLATFORM       PLATFORM
       │             │              │
       └─────────────┼──────────────┘
                     │
                   FFI
                     │
                Native OS
```

Và một nguyên tắc quan trọng được chốt:

> **Axiom Standard Library phải là một tập hợp các abstraction có semantic contract rõ ràng, không phải một runtime khổng lồ bị ép vào mọi chương trình.**

Điều này đặc biệt phù hợp với mục tiêu của bạn: **ứng dụng Axiom có thể dùng abstraction rất cao cấp, nhưng khi không cần thì compiler có thể loại bỏ toàn bộ tầng đó và cuối cùng chỉ còn native machine code cần thiết.**