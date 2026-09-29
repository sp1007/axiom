# BOOTSTRAP-094 — Axiom Standard Library Architecture & Prelude

**Trạng thái: FROZEN**

Mục tiêu của bước này là chốt kiến trúc thư viện để Axiom có thể vừa:

- mạnh như hệ sinh thái C++/Rust;
- không biến mọi chương trình thành một executable có runtime khổng lồ;
- giữ zero-cost abstraction;
- hỗ trợ native/freestanding;
- dễ self-host;
- dễ cho AI sử dụng;
- không biến Core Language thành một đống API.

Nguyên tắc trung tâm:

> **Language Core định nghĩa semantics. Library cung cấp capability và abstraction. Runtime chỉ xuất hiện khi chương trình thực sự cần.**

---

# 1. Bốn tầng của Axiom

Axiom chuẩn hóa thành:

```text
┌─────────────────────────────────────┐
│ Application / Community Libraries   │
├─────────────────────────────────────┤
│ Standard Library                    │
├─────────────────────────────────────┤
│ Core Library                        │
├─────────────────────────────────────┤
│ Language Core                       │
└─────────────────────────────────────┘
```

Và **System/Platform Library** nằm bên cạnh Standard Library:

```text
                 Application
                      │
              Standard Library
                /           \
        Core Library     System Library
                \           /
                 Language Core
```

Runtime components là một trục khác:

```text
Program
  ├── allocator? 
  ├── thread runtime?
  ├── async executor?
  ├── panic/unwind?
  ├── TLS?
  ├── GPU runtime?
  └── reflection metadata?
```

Không có chuyện:

```text
import std
    ↓
link everything
```

---

# 2. Language Core

Language Core chỉ chứa những thứ **không thể hoặc không hợp lý để đưa thành library**.

Ví dụ:

```text
struct
enum
trait
impl
fn
let
var
match
loop
async
await
comptime
unsafe

ownership
Drop
Copy
Move
view
mut_view
Send
Share
```

Core **không chứa**:

```text
Vec
String
HashMap
File
Socket
Thread
Mutex
GPU
JSON
HTTP
```

---

# 3. Core Library

Core Library là tầng thấp nhất có thể sử dụng trong gần như mọi chương trình.

Dự kiến:

```text
core/
├── option
├── result
├── array
├── slice
├── view
├── numeric
├── memory
├── ptr
├── atomic
├── sync primitives
├── iterator
├── range
├── string primitives
└── intrinsics wrappers
```

Core Library phải:

- không phụ thuộc OS;
- không yêu cầu heap nếu API không cần;
- không yêu cầu thread runtime;
- không yêu cầu async runtime;
- có thể chạy freestanding.

---

# 4. Standard Library

Standard Library cung cấp abstraction thường dùng:

```text
std/
├── collections
├── string
├── io
├── fs
├── net
├── process
├── thread
├── async
├── time
├── unicode
├── random
├── sync
├── gpu
├── math
├── encoding
└── compression
```

Nhưng mỗi module là **độc lập về dependency**.

Ví dụ:

```text
import std.collections.Vec;
```

không kéo theo:

```text
network
filesystem
thread
async executor
```

---

# 5. System Library

System Library là interface trực tiếp tới platform:

```text
system/
├── windows
├── linux
├── macos
├── ios
├── android
├── wasm
├── posix
├── syscall
├── cpu
├── gpu
├── interrupt
├── device
└── abi
```

Ví dụ:

```text
system.linux.epoll
system.windows.io
system.macos.mach
```

Không nên để những thứ này trở thành portable API.

---

# 6. Application Library

Các API như:

```text
JSON
HTTP
GUI
Game
Audio
Video
Database
ML
Tensor
Image
Crypto
Compression
```

không thuộc Standard Library Core.

Chúng là package/library ecosystem.

Điều này giữ compiler distribution nhỏ.

---

# 7. Prelude

Axiom **không nên có một prelude khổng lồ**.

Prelude mặc định chỉ chứa những abstraction gần như luôn cần.

Đề xuất:

```text
prelude:
    Option
    Result
    Some
    None
    Ok
    Err
    Copy
    Clone
    Drop
    Send
    Share
    view
    mut_view
    Iterator
    IntoIterator
```

Các collection:

```text
Vec
HashMap
String
```

**không nhất thiết phải nằm trong implicit prelude**.

---

# 8. Vì sao không import toàn bộ std?

Ví dụ chương trình:

```text
@freestanding

fn main() {
    let x: i32 = 42;
}
```

Không nên link:

```text
allocator
filesystem
network
thread
unicode database
async executor
```

Binary có thể chỉ chứa phần thực sự sử dụng.

---

# 9. Module dependency graph

Ví dụ:

```text
std.collections.Vec
        │
        ├── core.array
        ├── core.view
        ├── core.memory
        └── core.iterator
```

Trong khi:

```text
std.net.Socket
        │
        ├── core.result
        ├── core.view
        ├── system.socket
        └── runtime/io
```

Dependency graph phải được compiler biết chính xác.

---

# 10. Không có "god runtime"

Axiom không tạo:

```text
libaxiom_runtime.so
```

mà mặc định có các component:

```text
axiom.alloc
axiom.panic
axiom.thread
axiom.async
axiom.tls
axiom.gpu
axiom.unwind
```

Có thể link độc lập.

---

# 11. Program không heap

Ví dụ:

```text
@freestanding
fn main() {
    var x: [u8; 1024];
    ...
}
```

Không dùng:

```text
Box
Vec
String
HashMap
```

→ không cần allocator.

Đây là yêu cầu quan trọng cho embedded/kernel/bootloader.

---

# 12. Program không thread

Nếu chỉ:

```text
fn main() {
    println("hello");
}
```

không nên link:

```text
thread scheduler
atomic runtime
async executor
```

Compiler/linker loại bỏ hoàn toàn.

---

# 13. Program không async

Không:

```text
async executor
waker registry
task scheduler
```

nếu không có async.

---

# 14. Program không panic unwind

Nếu profile:

```text
panic = abort
```

thì không link unwind machinery.

Nếu:

```text
panic = unwind
```

thì mới link unwinder tương ứng.

---

# 15. Program không Unicode database

UTF-8 validity là language/library primitive.

Nhưng:

```text
grapheme segmentation
case folding
normalization
BiDi
Unicode properties
```

không cần nằm trong mọi executable.

---

# 16. `Option<T>`

Canonical:

```text
enum Option<T> {
    Some(T),
    None,
}
```

Compiler có thể tối ưu niche.

Ví dụ:

```text
Option<*const T>
```

có thể dùng null representation ở ABI thích hợp.

Nhưng **semantic null không xuất hiện trong safe language**.

---

# 17. `Result<T,E>`

```text
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Không allocation bắt buộc.

Compiler có thể return bằng register.

---

# 18. `Vec<T>`

`Vec<T>` semantic:

```text
owned growable sequence
length
capacity
storage identity
```

Không expose:

```text
ptr
len
cap
```

là representation mặc định.

API:

```text
Vec.new()
Vec.with_capacity(n)

v.push(x)
v.pop()
v.reserve(n)

v.len()
v.is_empty()

v[i]
view(v)
mut_view(v)
```

---

# 19. Relocation

API phải phản ánh semantics:

```text
v.push(x)
```

**có thể relocate storage**.

Do đó capability đang trỏ vào vùng của `Vec` có thể ngăn operation hoặc yêu cầu compiler chứng minh capability không còn live.

Không có lời hứa:

```text
reserve() == stable address
```

---

# 20. `Box<T>`

`Box<T>` có semantic:

> owned dynamic storage.

Không định nghĩa:

> luôn luôn heap allocation.

Compiler có thể eliminate allocation nếu địa chỉ/storage identity không observable.

Nếu programmer thực sự cần stable dynamic address:

```text
StableBox<T>
```

có thể là abstraction riêng sau này.

---

# 21. `String`

Axiom giữ:

```text
String
Str
Bytes
```

ba abstraction khác nhau.

```text
String = owned UTF-8
Str    = borrowed UTF-8
Bytes  = arbitrary bytes
```

Không dùng một `String` type cho cả ba.

---

# 22. Không implicit Bytes ↔ Str

Phải validate:

```text
Bytes → Str
```

nếu UTF-8 hợp lệ.

Có thể:

```text
let text = bytes.as_str()?;
```

Trusted unsafe:

```text
unsafe {
    Str.from_utf8_unchecked(bytes)
}
```

---

# 23. Iterator

Iterator là một trong những abstraction quan trọng nhất của Axiom.

Canonical:

```text
trait Iterator {
    type Item;

    fn next(self: mut_view<Self>) -> Option<Self.Item>;
}
```

Composition:

```text
items
    .filter(...)
    .map(...)
    .take(10)
```

Không allocation bắt buộc.

---

# 24. Iterator fusion

Compiler được phép biến:

```text
items
    .map(f)
    .filter(p)
    .map(g)
```

thành một loop duy nhất.

Đây là:

```text
abstraction
    ↓
HIR
    ↓
MIR
    ↓
inlining
    ↓
fusion
    ↓
machine loop
```

Không cần viết loop thủ công chỉ để đạt performance.

---

# 25. Collection categories

Axiom Standard Library chuẩn hóa:

```text
Vec
Deque
Queue
Stack
HashMap
HashSet
BTreeMap
BTreeSet
SmallVec
ArenaVec
```

nhưng không bắt mọi implementation dùng cùng storage.

---

# 26. HashMap

Semantic contract:

```text
key equality
hash consistency
lookup
insert
remove
```

Không đảm bảo:

```text
iteration order
physical bucket layout
pointer stability
```

Nếu cần deterministic ordered iteration:

```text
BTreeMap
```

hoặc explicit ordered map.

---

# 27. Stable identity

Đây là lý do Axiom trước đó đưa ra:

```text
EntityId
Handle<T>
GenerationHandle<T>
```

Application không cần giữ raw pointer.

Ví dụ:

```text
let player = world.spawn(Player {...});

world.get(player)
world.get_mut(player)
world.destroy(player)
```

Compiler/library quản lý storage identity.

---

# 28. `Handle<T>`

`Handle<T>` không phải:

```text
pointer
reference
borrow
owner
```

Nó là:

> logical identity token.

Có thể chứa:

```text
index
generation
type/domain information
```

Representation compiler/library controlled.

---

# 29. Resource APIs

Ví dụ:

```text
let file = File.open(path)?;
```

`File`:

- non-Copy;
- Move;
- Drop;
- explicit `close()`;
- resource ownership rõ ràng.

```text
file.read(buffer)?;
file.write(data)?;
file.flush()?;
```

---

# 30. Fallible cleanup

Không:

```text
Drop -> Result
```

Drop vẫn non-fallible.

Nếu cần xử lý lỗi:

```text
file.close()?;
```

sau đó Drop chỉ là safety fallback.

---

# 31. File read zero-copy

API nên ưu tiên:

```text
fn read(
    self: mut_view<File>,
    buffer: mut_view<u8>
) -> Result<usize, IoError>
```

Programmer có thể kiểm soát allocation:

```text
var buffer: [u8; 64 * 1024];

let n = file.read(buffer)?;
```

Không ép `read()` phải tạo String/Vec mới.

---

# 32. Convenience API

Có thể có:

```text
file.read_all()
```

trả:

```text
Result<Bytes, IoError>
```

Nhưng đây là convenience abstraction.

Zero-copy API vẫn tồn tại.

---

# 33. Networking

Socket abstraction:

```text
TcpListener
TcpStream
UdpSocket
```

Không gom tất cả vào:

```text
Socket
```

rồi runtime dispatch.

---

# 34. Async I/O

API:

```text
async fn read(
    self: mut_view<AsyncFile>,
    buffer: mut_view<u8>
) -> Result<usize, IoError>
```

Buffer lifetime được compiler kiểm tra.

In-flight operation giữ storage contract.

---

# 35. Thread API

```text
spawn(fn)
join()
```

hoặc:

```text
let handle = Thread.spawn(|| {
    work()
});

handle.join()?;
```

Closure capture quyết định `Send`.

Không cần programmer viết:

```text
Send + 'static
```

cho mọi task.

Compiler suy luận.

---

# 36. Shared state

Canonical:

```text
let state = Arc.new(Mutex.new(State {...}));

let task = spawn(move || {
    let guard = state.lock();
    ...
});
```

Đây vẫn có explicit shared ownership/synchronization.

Không biến:

```text
Arc<Mutex<T>>
```

thành implicit compiler magic.

---

# 37. Atomic

```text
let counter = Atomic<i64>.new(0);

counter.fetch_add(1, Relaxed);
```

Ordering explicit.

Không:

```text
counter++
```

với Atomic nếu semantics không rõ.

---

# 38. Time

Standard:

```text
Instant
Duration
SystemTime
DateTime
```

phải phân biệt:

```text
monotonic time
wall clock time
duration
deadline
```

Không dùng một `Time` type cho tất cả.

---

# 39. Random

Tách:

```text
Random
SecureRandom
SeededRandom
```

Không để:

```text
random()
```

ngầm dùng cryptographic RNG.

---

# 40. Math

Core:

```text
integer arithmetic
basic floating operations
```

Standard:

```text
sin
cos
exp
log
sqrt
pow
```

Extended:

```text
BigInt
Decimal
Complex
Rational
Interval
```

---

# 41. GPU

GPU API nằm ở Standard/System boundary:

```text
Device
DeviceBuffer
DeviceView
GpuEvent
Kernel
```

CPU-only executable không link GPU runtime.

---

# 42. SIMD

Portable:

```text
vector<T,N>
mask<N>
```

thuộc Core language/library.

Target intrinsics:

```text
system.x86.avx2
system.arm.neon
system.riscv.vector
```

không thuộc portable Standard API.

---

# 43. Serialization

Không đưa JSON vào Core.

Thay vào đó trait:

```text
trait Encode
trait Decode
```

và package:

```text
json
toml
yaml
protobuf
messagepack
```

---

# 44. Formatting

Standard nên có:

```text
Display
Debug
Format
Write
```

Nhưng formatting phải hỗ trợ:

```text
String
mut_view<u8>
Writer
```

để tránh allocation không cần thiết.

---

# 45. Logging

Không để `log()` là compiler primitive.

Standard/community:

```text
Logger
LogSink
LogLevel
```

Có thể compile out:

```text
@cfg(debug)
```

hoặc optimization.

---

# 46. Testing

Compiler/toolchain:

```text
axiom test
axiom bench
```

Library:

```text
@test
fn test_parser() {
    ...
}
```

Testing framework không nằm trong production runtime.

---

# 47. Prelude tối thiểu

Đề xuất frozen:

```text
prelude
├── Option
├── Result
├── Some
├── None
├── Ok
├── Err
├── Copy
├── Clone
├── Drop
├── Send
├── Share
├── Iterator
└── IntoIterator
```

Không đưa:

```text
Vec
String
HashMap
File
Arc
Mutex
```

vào implicit namespace.

---

# 48. Naming convention

Axiom thống nhất:

### Types

```text
PascalCase
```

Ví dụ:

```text
HashMap
DeviceBuffer
EntityId
```

### Functions

```text
snake_case
```

```text
read_file()
with_capacity()
```

### Fields

```text
snake_case
```

### Constants

```text
UPPER_SNAKE_CASE
```

Ví dụ:

```text
MAX_SIZE
```

### Generic parameters

```text
T
E
K
V
N
```

hoặc tên đầy đủ khi cần readability.

---

# 49. Method naming

Ưu tiên động từ rõ:

```text
read
write
open
close
reserve
insert
remove
clear
clone
duplicate
```

Không dùng quá nhiều shorthand:

```text
rd()
wr()
rm()
```

AI và người đều đọc khó hơn.

---

# 50. `get` vs `get_mut`

API convention:

```text
get(id) -> Option<view<T>>
get_mut(id) -> Option<mut_view<T>>
```

Rất hữu ích vì semantic intent nhìn thấy ngay.

---

# 51. `as_*`

`as_*` dành cho cheap view/conversion không ownership:

```text
as_str()
as_bytes()
as_view()
```

`to_*` dành cho conversion có thể tạo value mới:

```text
to_string()
to_vec()
```

`into_*` dành cho consuming conversion:

```text
into_string()
into_bytes()
```

Convention này đặc biệt hữu ích cho ownership readability.

---

# 52. `from_*`

Constructor-style conversion:

```text
String.from_utf8(...)
Bytes.from(...)
Duration.from_secs(...)
```

Không lạm dụng `new`.

---

# 53. `clone` vs `copy`

Không dùng:

```text
duplicate()
```

cho semantic Clone.

Chuẩn:

```text
x.clone()
```

`Copy` vẫn là compiler trait/property.

---

# 54. `duplicate`

Dùng khi resource/OS handle cần duplication thực sự:

```text
file.duplicate()
socket.duplicate()
```

Điều này tránh nhầm:

```text
clone value
```

với:

```text
duplicate external resource
```

---

# 55. `close` vs `drop`

```text
close()
```

là business/resource operation có thể fail.

```text
drop()
```

là ownership cleanup.

Không đồng nhất hai khái niệm.

---

# 56. API contract machine-readable

Mỗi public API semantic metadata có thể chứa:

```text
ownership
capability
Send
Share
panic behavior
allocation behavior
blocking behavior
async behavior
FFI safety
GPU legality
```

Ví dụ compiler metadata:

```text
{
    "function": "read",
    "receiver": "mut_view<File>",
    "allocation": "none",
    "blocking": true,
    "panic": false,
    "send": true
}
```

Điều này cực hữu ích cho AI agent và IDE.

---

# 57. API không được phụ thuộc implementation detail

Ví dụ không ghi trong public semantic API:

```text
Vec = ptr + len + cap
```

mà:

```text
Vec<T>
    owned
    growable
    contiguous logical sequence
    relocatable
```

Representation có thể thay đổi.

---

# 58. Standard Library cũng phải zero-cost

Một abstraction được gọi là zero-cost nếu compiler có thể erase overhead khi semantics cho phép.

Ví dụ:

```text
Iterator
Option
Result
closure
generic
newtype
view
```

không được tự động tạo runtime overhead chỉ vì tồn tại trong source.

---

# 59. Nhưng Standard Library không được lạm dụng zero-cost claim

Không nói:

> "mọi API đều zero-cost".

Ví dụ:

```text
Arc
Mutex
HashMap
File
Socket
```

có cost thực tế.

Axiom chỉ đảm bảo:

> **Không có cost ẩn chỉ vì abstraction tồn tại.**

---

# 60. Standard Library versioning

Library API phải có semantic versioning.

Compiler Core và Standard Library có thể version độc lập trong tương lai, nhưng compiler phải biết compatibility metadata.

Ví dụ:

```text
Axiom compiler 1.x
std 1.x
```

không nhất thiết phải lock cùng version tuyệt đối.

---

# 61. Freestanding profile

Axiom định nghĩa profile:

```text
freestanding
```

cho:

- kernel;
- embedded;
- bootloader;
- firmware;
- bare metal;
- OS runtime;
- GPU/system code.

Không có:

```text
File
Socket
Process
Thread
```

trừ khi target/system cung cấp.

---

# 62. Hosted profile

Default:

```text
hosted
```

có thể cung cấp:

```text
File
Process
Thread
Network
Time
```

nhưng vẫn module-based.

---

# 63. Minimal profile

Có thể có:

```text
profile = minimal
```

chỉ:

```text
Core
Core Library
panic=abort
```

để tạo binary cực nhỏ.

---

# 64. Full application profile

Một application có thể dùng:

```text
std
async
net
fs
unicode
gpu
```

nhưng linker vẫn dead-strip những gì không được sử dụng.

---

# 65. Runtime capability graph

Final link có thể nhìn như:

```text
Application
   │
   ├── Vec
   ├── String
   ├── File
   ├── Async
   └── GPU
        │
        ▼
Runtime Components
   ├── allocator
   ├── io
   ├── executor
   └── gpu
```

Không phải:

```text
Application
    ↓
Huge Runtime
```

---

# 66. Compiler và Standard Library

Compiler không hardcode mọi Standard Library API.

Compiler chỉ hardcode semantic primitives:

```text
Option optimization
Result propagation
Iterator lowering opportunities
Drop
atomic
intrinsics
ABI
```

Standard Library cung cấp implementation.

Điều này cho phép:

```text
alternate standard library
custom embedded library
kernel library
```

---

# 67. Core Library có thể self-host

Mục tiêu self-host:

```text
Axiom compiler
    ↓
Axiom Core Library
    ↓
Axiom Standard Library
    ↓
Axiom System Library
```

không phụ thuộc C++ standard library.

---

# 68. Bootstrap dependency rule

Trong bootstrap:

```text
Stage 0
    C/C++/LLVM allowed

Stage 1
    Axiom compiler prototype

Stage 2
    Axiom compiler + Axiom core

Stage 3
    Axiom compiler + Axiom std + Axiom linker

Stage 4
    fully self-hosted
```

C/C++ không trở thành semantic dependency của Axiom.

---

# 69. Standard Library ABI

Mặc định:

```text
internal Axiom ABI
```

Không hứa:

```text
Vec<T>
String
HashMap
Arc
Future
```

có stable C ABI.

Nếu cần FFI:

```text
@repr(C)
extern "C"
```

và wrapper.

---

# 70. Standard Library không được tạo hidden global state

Không:

```text
global allocator singleton
global async runtime
global logger
global thread pool
```

làm default semantic requirement.

Nếu cần global resource:

```text
GlobalAllocator
Executor
Logger
```

phải là explicit runtime/application configuration.

---

# 71. Frozen invariants

### Library Architecture

**ALIB2-20 — Language Core Contains Semantics, Not General-Purpose APIs**

**ALIB2-21 — Core Library Must Be Usable Without An Operating System**

**ALIB2-22 — Standard Library Is Modular**

**ALIB2-23 — System Library Is Platform-Specific**

**ALIB2-24 — Application Libraries Are Not Core Dependencies**

**ALIB2-25 — Library Modules Must Declare Their Dependency Requirements**

**ALIB2-26 — Library Import Does Not Imply Whole-Standard-Library Linking**

---

### Runtime

**ALIB2-27 — Runtime Components Are Independently Linkable**

**ALIB2-28 — Programs Need Not Link An Unused Runtime Component**

**ALIB2-29 — Heap Allocation Is Not A Standard Library Global Requirement**

**ALIB2-30 — Thread Runtime Is Not A Language Requirement**

**ALIB2-31 — Async Runtime Is Not A Language Requirement**

**ALIB2-32 — Unwind Runtime Is Profile-Dependent**

**ALIB2-33 — GPU Runtime Is Optional**

**ALIB2-34 — Unicode Database Is Not Required By UTF-8 Core Semantics**

---

### Collections

**ALIB2-35 — Vec Has Relocatable Storage Semantics**

**ALIB2-36 — Reserve Does Not Guarantee Stable Address**

**ALIB2-37 — Collection APIs Must Expose Capability-Safe Access**

**ALIB2-38 — Iterators Must Not Require Allocation By Default**

**ALIB2-39 — Iterator Composition May Be Fully Eliminated By Optimization**

**ALIB2-40 — HashMap Does Not Promise Iteration Order By Default**

**ALIB2-41 — Ordered Collections Provide Explicit Ordering Semantics**

---

### Text

**ALIB2-42 — String Is Owned UTF-8 Text**

**ALIB2-43 — Str Is Non-Owning UTF-8 Text**

**ALIB2-44 — Bytes Is Arbitrary Byte Storage**

**ALIB2-45 — Bytes-to-Str Conversion Must Validate UTF-8 Unless Unsafe**

**ALIB2-46 — Unicode Normalization Is Not Implicit**

---

### Resources

**ALIB2-47 — Resource Ownership Is Explicit**

**ALIB2-48 — Resource Duplication Is Explicit**

**ALIB2-49 — Drop Is Non-Fallible**

**ALIB2-50 — Fallible Cleanup Uses Explicit close/release APIs**

**ALIB2-51 — Resource Lifetime Is Distinct From Memory Lifetime**

---

### Identity

**ALIB2-52 — Logical Handles Are Not Raw Pointers**

**ALIB2-53 — Stable Identity Is Explicit**

**ALIB2-54 — Generation Handles May Detect Stale Identity**

**ALIB2-55 — Application APIs Should Prefer Logical Identity Over Physical Addresses**

---

### API Design

**ALIB2-56 — `as_*` Convention Represents Non-Owning/Cheap Views**

**ALIB2-57 — `to_*` May Produce A New Value**

**ALIB2-58 — `into_*` Consumes The Source Value**

**ALIB2-59 — Resource Duplication Is Distinct From Value Cloning**

**ALIB2-60 — `close` Is Distinct From Ownership Drop**

---

### Performance

**ALIB2-61 — Library Abstractions Must Not Imply Hidden Allocation**

**ALIB2-62 — Library Abstractions Must Not Imply Hidden Dynamic Dispatch**

**ALIB2-63 — Library Abstractions Must Not Imply Hidden Thread Creation**

**ALIB2-64 — Library Abstractions Must Not Imply Hidden Async Execution**

**ALIB2-65 — Compiler May Erase Library Abstractions When Semantics Permit**

**ALIB2-66 — Observable Runtime Costs Must Remain Semantically Honest**

---

### Self-hosting

**ALIB2-67 — Standard Library Must Eventually Be Implementable In Axiom**

**ALIB2-68 — Core Library Must Not Require A C++ Runtime**

**ALIB2-69 — Axiom ABI Is Separate From C ABI**

**ALIB2-70 — Stable C ABI Requires Explicit Representation Contracts**

**ALIB2-71 — Bootstrap Dependencies Must Not Become Permanent Language Dependencies**

---

# 72. Kết quả kiến trúc

Axiom hiện có một mô hình rất rõ:

```text
                     ┌──────────────────────┐
                     │ Application Libraries│
                     │ JSON / HTTP / GUI... │
                     └──────────┬───────────┘
                                │
                     ┌──────────▼───────────┐
                     │ Standard Library     │
                     │ Vec String Net FS    │
                     │ Thread Async GPU     │
                     └───────┬───────┬──────┘
                             │       │
                ┌────────────▼─┐   ┌─▼────────────┐
                │ Core Library │   │ System Lib   │
                │ Result       │   │ OS / CPU     │
                │ Option       │   │ GPU / ABI    │
                │ Iterator     │   │ Syscall      │
                │ View         │   │ Device       │
                └───────┬──────┘   └──────┬───────┘
                        │                  │
                        └────────┬─────────┘
                                 ▼
                        ┌────────────────┐
                        │ Language Core  │
                        │ Type / Memory  │
                        │ Ownership      │
                        │ Capability     │
                        │ Concurrency    │
                        └────────────────┘
```

Điểm quan trọng nhất:

> **Axiom không có "standard runtime". Axiom có standard capabilities.**

Một executable chỉ mang theo những capability mà nó thực sự sử dụng.

---

# 73. Quyết định kiến trúc tiếp theo

Sau khi Core, Memory, Concurrency, GPU, Comptime, Syntax và Library đã tương đối hoàn chỉnh, nút thắt tiếp theo không còn là syntax nữa mà là **cách compiler biểu diễn và tối ưu các API/library này ở quy mô rất lớn**.

Do đó chuỗi tiếp theo sẽ đi vào:

# **BOOTSTRAP-095 — Axiom Generic/Monomorphization Engine, Code Sharing & Binary Size**

Tập trung giải quyết:

```text
Vec<i32>
Vec<f32>
Vec<u64>
Vec<MyStruct>
Vec<LargeType>
```

và:

```text
generic explosion
code bloat
monomorphization
specialization
generic sharing
LTO
COMDAT
incremental compilation
cross-module optimization
ABI-compatible generic instances
```

Mục tiêu là đạt được điều rất quan trọng với Axiom:

> **Generics có performance gần zero-cost nhưng không biến executable thành một đống code duplicate.**