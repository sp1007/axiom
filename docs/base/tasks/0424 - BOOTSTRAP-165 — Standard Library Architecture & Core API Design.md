# BOOTSTRAP-165 — Standard Library Architecture & Core API Design
**STATUS: FROZEN / COMPLETED**

> **Standard Library phải cung cấp abstraction mạnh nhưng không áp đặt runtime, allocator, threading, async executor hay object model lên chương trình.**

Đây là bước rất quan trọng vì Axiom đã có semantic/compiler foundation khá đầy đủ. Từ đây, `std` phải trở thành **lớp xây dựng trên Core**, không được âm thầm trở thành “Core thứ hai”.

---

# 1. Kiến trúc tổng thể

Chốt:

```text
                    Axiom Language Core
                           │
                           ▼
                    Compiler Builtins
                           │
                           ▼
                      std::core
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      std::alloc      std::collections   std::string
          │                │                │
          ├────────────────┼────────────────┤
          ▼                ▼                ▼
       std::io         std::sync        std::thread
          │                │                │
          ▼                ▼                ▼
       std::fs         std::async       std::process
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                        std::os
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
       std::net         std::gpu         std::ffi
```

Không phải module nào cũng được link vào executable.

---

# 2. Bốn tầng API

Giữ nguyên distinction:

### Layer 0 — Language Core

Ví dụ:

```text
bool
i32
struct
enum
fn
trait
match
ownership
view
mut_view
async
comptime
unsafe
```

Không phụ thuộc `std`.

### Layer 1 — Compiler Builtins

Những thứ compiler phải hiểu:

```text
Copy
Drop
Send
Share
size_of
align_of
offset_of
atomic primitives
panic primitive
```

### Layer 2 — Runtime Components

Chỉ được link nếu cần:

```text
allocator
thread runtime
async executor
TLS
unwind
GPU runtime
```

### Layer 3 — Standard Library

API thông thường:

```text
Vec
String
HashMap
File
TcpStream
Mutex
Arc
Future
```

---

# 3. `std::core`

Đây là module quan trọng nhất.

Nó phải **rất nhỏ**.

Đề xuất:

```text
std::core
├── option
├── result
├── ordering
├── cmp
├── range
├── iterator
├── numeric
├── convert
├── mem
├── slice
├── array
├── tuple
├── panic
└── marker
```

---

# 4. Option

Không có `null`.

```ax
let x: Option<i32> = Some(42);

match x {
    Some(v) => println(v),
    None => ...
}
```

`Option<T>` là enum semantic.

Compiler được phép tối ưu representation.

---

# 5. Result

Recoverable failure:

```ax
fn read() -> Result<Data, Error>
```

và:

```ax
let data = read()?;
```

Không cần exception runtime.

---

# 6. Error trait

Không ép mọi error thành một base class.

Ví dụ:

```ax
trait Error {
    fn message(self) -> Str;
}
```

nhưng static dispatch mặc định.

Dynamic error chỉ khi API thực sự cần:

```ax
dyn Error
```

---

# 7. Ordering

```ax
enum Ordering {
    Less,
    Equal,
    Greater,
}
```

Dùng chung cho:

```text
sort
compare
Ord
PartialOrd
```

---

# 8. Numeric traits

Không hard-code toàn bộ toán học vào compiler.

`std::core` cung cấp:

```text
Integer
Signed
Unsigned
Float
Add
Sub
Mul
Div
Rem
BitAnd
BitOr
BitXor
Shl
Shr
```

Compiler nhận diện các primitive operation khi cần tối ưu.

---

# 9. Convert

Phân biệt rõ:

```text
as
```

với:

```text
From
Into
TryFrom
TryInto
```

`as` là cast semantic primitive.

Conversion trait là abstraction.

Không để:

```text
as
```

gọi arbitrary user code.

---

# 10. Memory utilities

`std::core::mem`:

```text
size_of<T>()
align_of<T>()
offset_of<T, field>()
swap()
replace()
take()
drop()
forget()
```

Nhưng phải định nghĩa cực kỳ rõ semantics.

---

# 11. `forget`

`forget(x)` không phải “memory leak bug” theo nghĩa compiler violation.

Nó là explicit suppression của Drop semantics.

Phải là API có tính chất unsafe hoặc system-level tùy final contract.

Không được vô tình dùng để bypass ownership verifier.

---

# 12. Slice/view API

Semantic primitive:

```text
view<T>
mut_view<T>
```

Nhưng std cung cấp:

```text
slice
split
chunks
windows
first
last
subview
```

Ví dụ:

```ax
fn sum(xs: view<i32>) -> i32 {
    ...
}
```

---

# 13. `Vec<T>`

`Vec<T>` là owning growable contiguous collection.

Semantic model:

```text
Vec<T> {
    pointer/storage
    length
    capacity
}
```

Nhưng representation thực tế không phải API contract trừ khi explicitly documented.

---

# 14. Vec relocation

Điểm quan trọng:

```ax
let v = Vec<i32>();
let x = view(v);

v.push(10);
```

Nếu `push` cần relocate và `x` còn sống:

**compiler phải reject hoặc API phải buộc kết thúc capability trước relocation.**

Không dùng runtime check mặc định để che lỗi semantic.

---

# 15. Vec không đảm bảo stable address

Muốn stable storage:

```text
Box<T>
StableBox<T>
Arena
Pool
```

tùy abstraction.

`Vec` chỉ đảm bảo semantics của collection, không phải permanent address.

---

# 16. String architecture

Không gọi mọi thứ là `String`.

Chốt:

```text
String   = owned UTF-8 text
Str      = borrowed UTF-8 text/view
Bytes    = owned bytes
ByteStr  = borrowed bytes
```

Không implicit:

```text
String → C char*
```

---

# 17. Unicode

Unicode processing không nên nằm trong compiler Core.

```text
std::unicode
```

cung cấp:

```text
code point
grapheme
normalization
case mapping
segmentation
```

Chương trình không dùng Unicode không phải link Unicode runtime.

---

# 18. String indexing

Không cho:

```ax
s[3]
```

mang semantics mơ hồ kiểu “character thứ 3”.

Vì UTF-8 có variable width.

Có thể:

```text
byte_at
codepoint_at
grapheme_at
```

với cost rõ ràng.

---

# 19. Iterator

Iterator là abstraction compile-time friendly:

```ax
for x in xs {
    ...
}
```

có thể lower thành vòng lặp trực tiếp.

Không tạo object iterator runtime bắt buộc.

---

# 20. Iterator pipeline

Ví dụ:

```ax
xs
    .map(...)
    .filter(...)
    .take(...)
```

mục tiêu:

```text
zero allocation
zero virtual dispatch
inline
fusion
```

nếu semantics cho phép.

Đây là một test thực tế cho triết lý:

> **Abstraction Erasure.**

---

# 21. Collections

Không đưa mọi collection vào `std::core`.

```text
std::collections
├── Vec
├── VecDeque
├── LinkedList
├── HashMap
├── HashSet
├── BTreeMap
├── BTreeSet
├── SmallVec
├── RingBuffer
├── BitSet
└── ...
```

Một chương trình chỉ dùng `Vec` không link `HashMap`.

---

# 22. HashMap

Hashing strategy phải là library concern.

Có thể có:

```text
HashMap
FastHashMap
DeterministicHashMap
```

Không hard-code một hash algorithm vào language.

---

# 23. Deterministic collections

Compiler/build tooling có thể cần:

```text
BTreeMap
OrderedMap
```

để deterministic output.

Application có thể chọn hash-based structure.

---

# 24. Small-vector optimization

`SmallVec<T, N>` là std abstraction hợp lý.

Ví dụ:

```text
inline capacity N
→ spill to dynamic storage
```

Compiler vẫn có thể optimize allocation nếu escape analysis cho phép.

---

# 25. `Box<T>`

`Box<T>`:

```text
owned dynamic storage
```

Semantics:

- owning;
- !Copy;
- Drop;
- stable address **chỉ khi contract yêu cầu storage stability**.

Không mặc định đồng nghĩa:

```text
malloc()
```

---

# 26. `Rc<T>` / `Arc<T>`

Shared ownership phải explicit.

```text
Rc<T>   local
Arc<T>  concurrent
```

Không bao giờ compiler tự biến:

```text
T
```

thành:

```text
Arc<T>
```

vì điều đó thay đổi ownership semantics.

---

# 27. `Arc<Mutex<T>>`

Đây vẫn là abstraction hợp lệ:

```ax
let x: Arc<Mutex<Data>>;
```

Nhưng `Arc` không tự làm `Data` mutable-safe.

`Mutex` mới cung cấp synchronization capability.

---

# 28. Allocator architecture

Không có:

```text
global malloc
```

bắt buộc.

API:

```text
std::alloc
```

có thể cung cấp:

```text
Allocator
SystemAllocator
Arena
Pool
Slab
BumpAllocator
```

---

# 29. Allocator generic

Có thể:

```ax
Vec<T, A>
```

hoặc compiler/library chọn cách khác.

Nhưng không nên làm allocator generic xuất hiện ở mọi API nếu không cần.

Một abstraction tốt phải không ép programmer mang allocator parameter xuyên application.

---

# 30. Arena

Arena:

```ax
Arena<T>
```

phù hợp:

- compiler;
- parser;
- ECS;
- temporary graph;
- batch processing.

Cleanup toàn arena:

```text
O(1) / proportional storage policy
```

tùy implementation.

---

# 31. `std::io`

Không để `File` trở thành Core primitive.

```text
std::io
├── Read
├── Write
├── Seek
├── BufRead
├── Reader
├── Writer
└── Error
```

---

# 32. IO abstraction

Trait:

```ax
trait Read {
    fn read(self: mut_view<Self>, buffer: mut_view<u8>)
        -> Result<usize, Error>;
}
```

Method syntax vẫn chỉ là function call.

Không cần interface object.

---

# 33. Buffer ownership

API ưu tiên:

```ax
fn read(
    self: mut_view<Self>,
    buffer: mut_view<u8>
) -> Result<usize, Error>
```

thay vì:

```text
allocate internal buffer
return new object
```

để tránh allocation.

---

# 34. Async IO

Có thể:

```ax
async fn read(...) -> Result<usize, Error>
```

nhưng `async` không tạo executor.

Executor thuộc:

```text
std::async
```

hoặc runtime component.

---

# 35. File

```text
std::fs::File
```

là wrapper trên platform resource.

Nó có:

- ownership;
- Drop;
- explicit close nếu muốn kiểm tra lỗi.

Ví dụ:

```ax
file.close()?;
```

Drop vẫn phải đảm bảo resource không bị bỏ quên.

---

# 36. Fallible cleanup

Như đã frozen:

```text
Drop ≠ recoverable error
```

Vì vậy:

```ax
file.close() -> Result<(), Error>
```

có thể báo lỗi.

Drop là fallback cleanup.

---

# 37. Networking

```text
std::net
├── TcpStream
├── TcpListener
├── UdpSocket
├── IpAddr
├── SocketAddr
└── ...
```

Không link network runtime nếu application không sử dụng.

---

# 38. OS abstraction

`std::os` chia platform:

```text
std::os::windows
std::os::linux
std::os::macos
std::os::android
```

Nhưng API portable nằm ở:

```text
std::fs
std::process
std::net
std::thread
```

khi semantics có thể thống nhất.

---

# 39. Platform handles

Raw OS handles không tự động trở thành:

```text
Box
```

hay:

```text
Arc
```

Wrapper phải xác định:

```text
ownership
close semantics
thread safety
FFI representation
```

---

# 40. `std::process`

Cung cấp:

```text
Command
Child
ExitStatus
Environment
```

Không nhét process management vào language Core.

---

# 41. `std::sync`

```text
Mutex
RwLock
Semaphore
Condvar
Barrier
Atomic
Channel
Once
```

Các primitive này dùng memory model đã frozen.

---

# 42. Atomic API

`Atomic<T>` phải phân biệt:

```text
load
store
swap
compare_exchange
fetch_add
```

với memory ordering:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không cho atomic tự động chuyển thành ordinary `mut_view<T>`.

---

# 43. Mutex guard

```ax
let guard = mutex.lock()?;
guard.value += 1;
```

Guard:

- ownership-bearing capability;
- !Copy;
- Drop unlocks.

---

# 44. Channel

Channel nên là abstraction ownership-centric:

```ax
tx.send(value)?;
```

`value` chuyển ownership.

Không cần clone nếu không cần.

---

# 45. Channel implementations

Có thể chuyên biệt:

```text
SPSC
MPSC
SPMC
MPMC
bounded
unbounded
async
```

Nhưng API có thể thống nhất ở tầng cao hơn.

---

# 46. Thread

```ax
std::thread::spawn(...)
```

nhận closure.

Compiler kiểm tra:

```text
closure captures
Send
ownership
```

không cần runtime borrow checker.

---

# 47. Spawn semantics

`spawn` nghĩa là:

```text
execution crosses thread boundary
```

→ captured state phải thỏa `Send`.

Không đồng nghĩa `Share`.

---

# 48. Thread-local

```text
std::os / std::thread
```

có TLS API.

TLS runtime chỉ được link khi dùng.

---

# 49. Async architecture

```text
std::async
├── Future
├── Poll
├── Waker
├── Executor
├── Task
├── JoinHandle
├── Cancellation
└── channels
```

Core chỉ cung cấp lowering semantics.

---

# 50. Executor không phải Core

Có thể có:

```text
single-thread executor
thread-pool executor
io executor
GUI executor
GPU-aware executor
```

Một chương trình sync không cần link executor.

---

# 51. Structured concurrency

Ưu tiên:

```ax
scope {
    spawn(task1);
    spawn(task2);
}
```

và:

```text
scope waits/joins according to contract
```

Detached execution phải explicit.

---

# 52. Cancellation

Không kill task cưỡng bức.

```text
CancellationToken
CancellationHandle
```

Task tự kiểm tra/safely suspend.

---

# 53. Time

```text
std::time
```

chia:

```text
Instant
Duration
SystemTime
DateTime
```

Không để wall clock trở thành compiler-visible semantic primitive ngoại trừ comptime capability.

---

# 54. Random

```text
std::random
```

phân biệt:

```text
PRNG
OS entropy
secure RNG
```

Không có global hidden RNG.

---

# 55. Math

```text
std::math
```

cung cấp:

```text
sin
cos
sqrt
exp
log
pow
...
```

Compiler có thể map sang target intrinsic khi semantics phù hợp.

---

# 56. Strict vs fast math

Đây là boundary quan trọng.

Default:

```text
strict FP semantics
```

Fast math:

```text
explicit optimization mode/contract
```

Không tự ý biến:

```text
a + b + c
```

thành reassociated expression nếu semantics không cho phép.

---

# 57. SIMD API

Compiler tự vectorize là mặc định.

Nhưng programmer vẫn cần explicit SIMD:

```text
std::simd
```

cho:

- algorithm đặc biệt;
- architecture-specific work;
- deterministic vector width;
- low-level optimization.

---

# 58. GPU

```text
std::gpu
├── Device
├── DeviceBuffer
├── DeviceView
├── Kernel
├── GpuEvent
├── Stream
└── ...
```

GPU model đã frozen trước đó.

---

# 59. Tensor library

Không đưa tensor vào Core.

```text
std::tensor
```

hoặc package ecosystem.

Có thể dùng:

```text
Tensor<T, Shape, Device>
```

và compiler specialization/vectorization/GPU backend hỗ trợ.

---

# 60. AI/ML

Axiom không cần có:

```text
Tensor
Autograd
Model
Optimizer
```

trong Core.

Chúng là ecosystem libraries.

Điều này giúp language không bị khóa vào AI framework cụ thể.

---

# 61. `std::ffi`

FFI nên cung cấp:

```text
CStr
CString
C ABI helpers
raw pointer utilities
dynamic library
calling convention
```

nhưng raw operations vẫn nằm ở unsafe boundary.

---

# 62. C string

Phân biệt:

```text
String
CStr
CString
```

`String` không tự động null-terminate.

---

# 63. Dynamic libraries

`std::ffi`/`std::os` có:

```text
load_library
get_symbol
```

Nhưng dynamic symbol loading tạo Open World assumptions cho optimizer.

Compiler phải biết boundary này.

---

# 64. Crypto

Crypto nên nằm ngoài `std::core`.

Có thể:

```text
std::crypto
```

nhưng implementation có thể nằm package riêng.

Các primitive security-sensitive cần:

```text
constant-time contracts
secure memory
zeroization
```

khi phù hợp.

---

# 65. Collections không ép allocation

API nên cho phép:

```text
stack
arena
custom allocator
```

nhưng abstraction phổ biến không nên bắt programmer viết allocator mọi nơi.

Đây là balance quan trọng:

> **Power without ceremony.**

---

# 66. Error philosophy của std

Không dùng exception mặc định.

Ba lớp:

```text
Result<T,E>  recoverable
Option<T>    absence
panic        unrecoverable/program invariant failure
```

Ngoài ra:

```text
abort
```

ở system/runtime level.

---

# 67. Panic không phải exception

Panic:

```text
never
```

và policy:

```text
abort
unwind
custom
```

được chọn bởi build profile/runtime.

---

# 68. Logging

Không đưa global logger vào Core.

Có thể:

```text
std::log
```

nhưng logger là dependency explicit.

Một tiny executable không tự động kéo:

```text
logging
formatting
thread
IO
```

vào binary.

---

# 69. Formatting

```text
std::fmt
```

cung cấp:

```text
format
print
write
Display
Debug
```

Generic formatting phải được specialize/inline khi có thể.

---

# 70. Serialization

Serialization **không phải memory representation**.

```text
std::serialize
```

có thể hỗ trợ:

```text
JSON
CBOR
binary
custom
```

Nhưng:

```text
serialize(T)
```

không được giả định rằng:

```text
memory bytes of T
```

là wire format.

---

# 71. Reflection

Runtime reflection không mặc định.

Comptime reflection:

```ax
comptime {
    fields_of<T>()
}
```

có thể dùng để derive:

```text
Serialize
Debug
Hash
```

Generated code vẫn đi qua normal verification.

---

# 72. Derive system

Compiler-known:

```ax
@derive(Copy, Clone, Debug, Hash)
struct Point {
    x: f32,
    y: f32,
}
```

không phải procedural macro language.

Compiler generates typed declarations.

---

# 73. GUI

GUI không thuộc Core.

Có thể ecosystem:

```text
std::gui
```

hoặc package:

```text
axiom.gui
```

với native backend:

```text
Windows
macOS
Linux
Android
iOS
Web
```

---

# 74. Graphics

Graphics API tương tự:

```text
std::graphics
```

hoặc package.

Không cần compiler biết:

```text
Mesh
Texture
Material
Scene
```

trừ GPU ABI/kernel primitives.

---

# 75. Game development

Axiom không nên hard-code game engine.

Nhưng std phải đủ tốt để engine xây được:

```text
allocator
thread
async
SIMD
GPU
filesystem
network
time
math
```

Đây mới là nền tảng đúng.

---

# 76. Compiler dependency rule

Std itself phải được xây bằng Axiom càng sớm càng tốt.

Bootstrap có thể tạm dùng:

```text
external C/LLVM/runtime
```

nhưng production architecture:

```text
Axiom compiler
    ↓
Axiom std
    ↓
Axiom application
```

không cần C++ runtime.

---

# 77. No hidden dependency

Ví dụ chương trình:

```ax
fn main() {
    return;
}
```

không được tự động link:

```text
allocator
thread runtime
async runtime
network
unicode
reflection
```

---

# 78. Runtime composition

Dependency graph:

```text
Program
 │
 ├── std::core
 │
 ├── std::fmt
 │
 └── std::fs
       │
       └── OS filesystem component
```

Linker chỉ lấy các component cần thiết.

---

# 79. Standard library ABI

Public std types có:

```text
semantic API
```

nhưng binary ABI stability phải là một contract riêng.

Không hứa ABI stable cho mọi std type mặc định.

---

# 80. API evolution

Axiom std nên hỗ trợ:

```text
source compatibility
semantic compatibility
ABI compatibility
```

nhưng không mặc định coi cả ba là cùng một thứ.

---

# 81. `std` không phải monolith

Một chương trình embedded có thể dùng:

```text
std::core
std::alloc::arena
```

mà không có:

```text
std::net
std::fs
std::thread
```

---

# 82. Freestanding

Freestanding profile tối thiểu:

```text
core
intrinsics
basic memory
panic/abort primitive
```

Không yêu cầu OS.

---

# 83. Kernel profile

Có:

```text
core
atomic
volatile
memory
interrupt
device
```

nhưng không:

```text
filesystem
socket
user process
```

trừ khi kernel tự cung cấp abstraction.

---

# 84. Embedded

Có thể:

```text
core
alloc optional
device
atomic
interrupt
```

và tránh toàn bộ OS runtime.

---

# 85. GPU/device profile

Chỉ compile phần GPU-legal:

```text
core numeric
vector
device memory
kernel
```

Không kéo:

```text
File
Socket
Thread
Process
```

vào device code.

---

# 86. Capability-driven std

Một cách nhìn thống nhất:

```text
Program capability requirements
          ↓
Runtime component selection
          ↓
Link
```

Ví dụ:

```text
File
```

yêu cầu:

```text
OS + IO
```

trong khi:

```text
Vec
```

chỉ cần allocation strategy nếu thực sự dynamic.

---

# 87. API design rule: capability explicit

Không có API kiểu:

```ax
global_random()
global_logger()
global_allocator()
global_executor()
```

nếu nó tạo hidden global state.

Ưu tiên dependency explicit.

---

# 88. API design rule: ownership explicit

Ví dụ:

```ax
fn read_file(path: Str) -> Result<String, Error>
```

trả ownership rõ ràng.

Không có hidden shared string.

---

# 89. API design rule: borrowing invisible where possible

Người dùng không phải viết:

```text
'a
&'a
&mut
```

Thay vào đó:

```ax
fn parse(input: Str) -> Result<Value, Error>
```

Compiler quản lý capability/lifetime.

---

# 90. API design rule: allocation visible only when meaningful

Không bắt programmer quan tâm:

```text
stack vs heap
```

trừ khi API semantics yêu cầu:

```text
stable address
arena lifetime
device storage
external resource
```

---

# 91. API design rule: no accidental dynamic dispatch

Generic:

```ax
fn sort<T: Ord>(...)
```

static dispatch.

Dynamic:

```ax
fn process(x: dyn Processor)
```

chỉ khi programmer chọn.

---

# 92. API design rule: no accidental clone

Ví dụ:

```ax
send(value)
```

phải Move nếu API nhận ownership.

Nếu cần duplicate:

```ax
send(value.clone())
```

rõ ràng.

---

# 93. API design rule: zero-cost by default

Abstraction:

```ax
Iterator
Option
Result
generic
trait
closure
```

không mặc định đồng nghĩa với:

```text
allocation
vtable
runtime object
```

---

# 94. API design rule: specialized fast paths

Standard library có thể cung cấp generic API:

```ax
sort<T: Ord>()
```

nhưng compiler/std có thể specialize:

```text
i32
u32
f32
small POD
```

thành implementation tối ưu.

---

# 95. API design rule: unsafe concentrated

Std có thể chứa unsafe implementation:

```text
unsafe internals
        ↓
verified safe API
```

Application developer không phải viết unsafe cho các thao tác thông thường.

---

# 96. API design rule: platform specialization

Portable:

```ax
std::fs::File
```

platform-specific:

```ax
std::os::windows::HANDLE
```

Không làm portable API yếu đi chỉ vì platform-specific API tồn tại.

---

# 97. API design rule: compiler hints remain optional

Std có thể dùng:

```text
@inline
@cold
@target_feature
```

nhưng semantics không phụ thuộc chúng.

---

# 98. Standard library source organization

Đề xuất:

```text
std/
├── core/
├── alloc/
├── collections/
├── string/
├── unicode/
├── fmt/
├── math/
├── io/
├── fs/
├── net/
├── process/
├── sync/
├── thread/
├── async/
├── time/
├── random/
├── crypto/
├── os/
├── gpu/
├── simd/
└── ffi/
```

---

# 99. Optional higher-level libraries

Không cần nhét vào std:

```text
HTTP
JSON
SQL
GUI
Tensor
ML
Game
Audio
Video
Image
ECS
```

Những thứ này nên là ecosystem packages.

---

# 100. Standard library philosophy

Chốt thành:

> **Core defines semantics. Compiler provides power. Runtime provides only required execution services. Standard Library provides reusable abstractions. Ecosystem provides domain-specific functionality.**

---

# Invariants

### `ASTD2-20`
`std::core` remains small and language-adjacent.

### `ASTD2-21`
Standard-library modules are independently linkable.

### `ASTD2-22`
Using one standard-library subsystem must not implicitly link unrelated subsystems.

### `ASTD2-23`
Standard-library APIs do not alter Axiom Core ownership semantics.

### `ASTD2-24`
Standard-library APIs do not require programmer-written lifetimes.

### `ASTD2-25`
Standard-library abstractions preserve deterministic resource cleanup.

### `ASTD2-26`
Standard-library APIs do not implicitly introduce tracing GC.

### `ASTD2-27`
Standard-library APIs do not require a monolithic runtime.

### `ASTD2-28`
`Option<T>` represents absence without null semantics.

### `ASTD2-29`
`Result<T,E>` represents recoverable failure.

### `ASTD2-30`
Panic remains distinct from recoverable error.

### `ASTD2-31`
`Vec<T>` does not promise stable addresses unless explicitly contracted.

### `ASTD2-32`
Active safe capabilities prevent storage relocation where required.

### `ASTD2-33`
`String` and byte-oriented storage remain semantically distinct.

### `ASTD2-34`
Axiom strings are not implicitly C strings.

### `ASTD2-35`
Iterator abstractions are designed for zero-cost specialization.

### `ASTD2-36`
Generic standard-library APIs use static dispatch by default.

### `ASTD2-37`
Dynamic dispatch requires explicit semantic representation.

### `ASTD2-38`
Clone is never silently inserted by standard-library APIs.

### `ASTD2-39`
Ownership transfer is explicit in API semantics.

### `ASTD2-40`
Shared ownership is explicit through dedicated abstractions.

### `ASTD2-41`
`Rc` and `Arc` remain distinct concurrency abstractions.

### `ASTD2-42`
`Arc` does not imply mutable thread-safe access.

### `ASTD2-43`
Synchronization abstractions preserve the Axiom memory model.

### `ASTD2-44`
Mutex guards are ownership-bearing capabilities.

### `ASTD2-45`
Channel send/receive semantics preserve ownership transfer.

### `ASTD2-46`
Thread spawning verifies `Send` requirements.

### `ASTD2-47`
Async executors are not part of Core semantics.

### `ASTD2-48`
Async runtime components are optional.

### `ASTD2-49`
GPU APIs preserve execution/storage-domain separation.

### `ASTD2-50`
FFI APIs preserve explicit ABI and ownership contracts.

### `ASTD2-51`
Platform APIs do not redefine portable Core semantics.

### `ASTD2-52`
Allocator choice remains independent from language-level ownership semantics.

### `ASTD2-53`
Arena/pool/slab allocation are library-level storage strategies.

### `ASTD2-54`
Standard-library allocation can be eliminated by compiler optimization where semantics permit.

### `ASTD2-55`
Stable-address requirements remain explicit.

### `ASTD2-56`
Serialization semantics are distinct from memory representation.

### `ASTD2-57`
Runtime reflection is not mandatory.

### `ASTD2-58`
Comptime reflection does not imply runtime metadata.

### `ASTD2-59`
Generated standard-library code re-enters normal compiler verification.

### `ASTD2-60`
Standard-library unsafe code cannot fabricate false compiler-derived semantic properties.

### `ASTD2-61`
Freestanding builds can use `std::core` without hosted OS facilities.

### `ASTD2-62`
Kernel/embedded builds can omit hosted runtime components.

### `ASTD2-63`
GPU/device code can omit host-only standard-library facilities.

### `ASTD2-64`
Unused runtime components are eliminated from final artifacts.

### `ASTD2-65`
Standard-library abstractions are designed for zero-cost specialization where practical.

### `ASTD2-66`
Standard-library APIs may expose explicit performance-oriented specialized variants.

### `ASTD2-67`
Platform-specific functionality is isolated from portable APIs.

### `ASTD2-68`
Standard-library ABI stability is an explicit contract, not an accidental property.

### `ASTD2-69`
Standard-library evolution distinguishes source, semantic and ABI compatibility.

### `ASTD2-70`
Domain-specific frameworks remain outside the mandatory Core/standard-library foundation.

### `ASTD2-71`
The standard library must remain buildable by the Axiom compiler itself in the self-hosting phase.

### `ASTD2-72`
Standard-library implementations may use unsafe internals behind verified safe abstractions.

### `ASTD2-73`
Standard-library APIs must not force hidden global allocator, executor, logger or RNG state.

### `ASTD2-74`
Standard-library abstractions preserve deterministic semantics across optimization levels.

### `ASTD2-75`
Standard-library behavior is covered by the compiler conformance and fuzzing architecture.

### `ASTD2-76`
Standard-library APIs are designed to expose semantic boundaries rather than implementation details.

### `ASTD2-77`
Standard-library abstractions must remain compatible with Axiom's capability and alias analysis.

### `ASTD2-78`
Standard-library APIs should maximize compiler visibility for optimization where semantics permit.

### `ASTD2-79`
Standard-library implementation complexity must not become programmer-facing language complexity.

### `ASTD2-80`
The standard library is an extensible foundation, not the definition of the Axiom language.

---

# BOOTSTRAP-166 — Standard Library Collections, Containers & Data Structures

Bước tiếp theo sẽ đi sâu vào **thiết kế container thực sự của Axiom**, thay vì chỉ liệt kê API.

Đặc biệt cần chốt:

```text
Vec
SmallVec
Array
Slice/View
String
Bytes
HashMap
BTreeMap
HashSet
RingBuffer
Deque
Queue
Stack
Arena
Pool
Slab
SparseSet
BitSet
Matrix
SoA
```

và quan trọng hơn:

**container nào là primitive semantic, container nào chỉ là library abstraction, container nào có stable address, container nào được phép relocate, và compiler phải hiểu đến mức nào để tối ưu chúng.**