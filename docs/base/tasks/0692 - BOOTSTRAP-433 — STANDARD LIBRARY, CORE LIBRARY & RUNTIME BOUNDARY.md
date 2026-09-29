# BOOTSTRAP-433 — STANDARD LIBRARY, CORE LIBRARY & RUNTIME BOUNDARY

Task này khóa ranh giới giữa **ngôn ngữ**, **core library**, **standard library**, **runtime** và **OS/platform layer**.

Mục tiêu là tránh hai cực đoan:

- nhồi quá nhiều thứ vào compiler;
- hoặc có một runtime khổng lồ mà mọi chương trình đều phải kéo theo.

Axiom phải cho phép:

```text
fn main() {
    ...
}
```

tạo native executable tối thiểu, đồng thời vẫn có thể xây application lớn với GUI, networking, async, GPU, ML...

---

## 433.1 — Bốn tầng chính

Axiom sử dụng:

```text
Language Core
    ↓
Core Library
    ↓
Standard Library
    ↓
Platform / Runtime
```

### Language Core

Compiler bắt buộc hiểu:

- primitive types;
- ownership/move/drop;
- traits;
- generics;
- `Option`/`Result` semantics;
- pattern matching;
- comptime;
- atomics/intrinsics;
- ABI;
- memory model.

### Core Library

Các abstraction nền tảng:

- `Option<T>`;
- `Result<T,E>`;
- basic iterators;
- basic collections;
- string abstractions;
- formatting primitives.

### Standard Library

Các chức năng application:

- filesystem;
- networking;
- process;
- threads;
- async;
- time;
- collections nâng cao;
- synchronization.

### Platform layer

OS-specific:

- Windows;
- Linux;
- macOS;
- iOS;
- Android;
- WASM;
- embedded.

---

# 433.2 — Không có "fat runtime" mặc định

Axiom không yêu cầu executable luôn link:

```text
axiom-runtime-full
```

Thay vào đó linker chỉ lấy những phần thực sự được sử dụng.

---

# 433.3 — Runtime là capability set

Runtime conceptual:

```text
Runtime
 ├── startup
 ├── allocator
 ├── panic
 ├── thread
 ├── async
 ├── IO
 └── platform
```

Mỗi component độc lập nhất có thể.

---

# 433.4 — Runtime component linking

Ví dụ chương trình chỉ dùng:

```text
String
Array
```

không được kéo theo:

```text
network
filesystem
async executor
```

---

# 433.5 — Dead-code elimination

433 phụ thuộc trực tiếp vào 420:

```text
source
 ↓
modules
 ↓
objects
 ↓
linker GC
 ↓
only reachable runtime components
```

---

# 433.6 — `core`

Axiom có một package/library cực nhỏ:

```text
core
```

chứa abstraction thiết yếu.

---

# 433.7 — `core` không phụ thuộc OS

`core` phải có thể dùng trong:

```text
Windows
Linux
macOS
iOS
Android
WASM
embedded
kernel/freestanding
```

---

# 433.8 — Core không allocation mặc định

Các primitive trong core không được implicit heap allocate.

---

# 433.9 — `Option<T>`

Định nghĩa logic:

```text
enum Option<T> {
    Some(T)
    None
}
```

Compiler/type layout có thể áp dụng niche optimization từ 422.

---

# 433.10 — `Result<T,E>`

```text
enum Result<T,E> {
    Ok(T)
    Err(E)
}
```

Không có implicit exception object.

---

# 433.11 — `never`

Core cung cấp:

```text
never
```

cho function không return:

```text
fn abort() -> never
```

---

# 433.12 — `unit`

```text
unit
```

là canonical empty value.

---

# 433.13 — Basic ordering/equality traits

Core định nghĩa các capability:

```text
Eq
Ord
Hash
```

hoặc tên tương đương được khóa ở trait library specification.

---

# 433.14 — Arithmetic traits

Operator semantics từ 429 map tới core traits:

```text
Add
Sub
Mul
Div
Rem
Neg
BitAnd
BitOr
BitXor
Shl
Shr
```

---

# 433.15 — Conversion traits

Core:

```text
From<T>
Into<T>
TryFrom<T>
TryInto<T>
```

với semantics tương ứng.

---

# 433.16 — Iterator abstraction

Core có iterator protocol:

```text
trait Iterator {
    type Item
    fn next(self: mut Self) -> Option<Self::Item>
}
```

Exact receiver syntax có thể được tinh chỉnh, nhưng struct-first method model vẫn giữ.

---

# 433.17 — Iterator không tạo allocation

Iterator mặc định là value/state machine.

```text
for x in items {
    ...
}
```

có thể được zero-cost lowered.

---

# 433.18 — Iterator combinators

Ví dụ:

```text
map
filter
fold
take
skip
zip
enumerate
```

là library abstractions, không phải compiler magic ngoại trừ optimization.

---

# 433.19 — Range

Range syntax từ 429:

```text
0..10
```

là core/library value.

---

# 433.20 — Array

Array:

```text
[T; N]
```

là language type.

---

# 433.21 — Slice

Slice/view là language-supported representation nhưng abstraction API thuộc core.

Conceptual:

```text
[]T
```

hoặc read/write view tương ứng theo ownership/view rules.

---

# 433.22 — Vector

Dynamic contiguous array:

```text
Vec<T>
```

thuộc core/standard collection layer, không phải primitive type.

---

# 433.23 — `Vec<T>` ownership

`Vec<T>` sở hữu:

```text
pointer
length
capacity
allocator information nếu cần
```

và deterministic drop.

---

# 433.24 — Small vector

`SmallVec<T,N>` không phải language primitive.

Có thể là standard-library optimization.

---

# 433.25 — Slice allocation

Slice không sở hữu memory.

Nó chỉ view memory owned elsewhere.

---

# 433.26 — String

`String` là owned UTF-8 string.

Memory:

```text
ptr
len
capacity
```

theo 422.

---

# 433.27 — StringSlice

Một string view:

```text
Str
```

hoặc tên tương đương.

Không ownership.

---

# 433.28 — UTF-8 invariant

`String` luôn chứa valid UTF-8.

Raw bytes dùng:

```text
[]u8
```

hoặc byte buffer.

---

# 433.29 — Invalid UTF-8

Conversion từ bytes:

```text
String::from_utf8(bytes)
```

trả:

```text
Result<String, Utf8Error>
```

---

# 433.30 — String literal

Literal:

```text
"hello"
```

được compiler encode UTF-8.

---

# 433.31 — Byte literal

```text
b"hello"
```

tạo byte sequence, không yêu cầu UTF-8.

---

# 433.32 — Character

`char` biểu diễn Unicode scalar value, không phải UTF-8 byte.

---

# 433.33 — Formatting

Core/standard library cung cấp:

```text
format(...)
print(...)
println(...)
```

nhưng formatting implementation không phải compiler runtime bắt buộc.

---

# 433.34 — Formatting allocation

`print` không nhất thiết phải tạo `String` trung gian.

Có thể stream trực tiếp tới writer.

---

# 433.35 — Formatting trait

Có thể có:

```text
trait Display
trait Debug
trait Format
```

để compiler/library xử lý generic formatting.

---

# 433.36 — Collections

Standard library cung cấp tối thiểu:

```text
Vec
Map
Set
Deque
Heap
```

---

# 433.37 — HashMap

HashMap phải cho phép lựa chọn hasher.

Không hard-code một thuật toán hash duy nhất cho mọi use case.

---

# 433.38 — Hash collision behavior

Collision không được tạo memory unsafety.

Performance guarantee phụ thuộc hasher/input.

---

# 433.39 — Ordered collections

Có thể cung cấp:

```text
BTreeMap
BTreeSet
```

hoặc equivalent.

---

# 433.40 — Arena collections

Các collection có allocator parameter:

```text
Vec<T, A>
```

hoặc equivalent.

---

# 433.41 — Allocator model

Allocator là trait/interface:

```text
trait Allocator {
    fn allocate(...)
    fn deallocate(...)
    fn resize(...)
}
```

Exact API sẽ được khóa trong memory-library specification.

---

# 433.42 — Global allocator

Application có thể chọn global allocator.

Nhưng standard library không được giả định một allocator duy nhất về semantics.

---

# 433.43 — Local allocator

Data structure có thể nhận allocator:

```text
Vec<T, Arena>
```

để tránh fragmentation.

---

# 433.44 — Arena

Arena phù hợp:

- compiler;
- parser;
- frame data;
- temporary objects;
- game scenes.

Arena drop giải phóng toàn bộ region.

---

# 433.45 — Pool

Pool allocator phù hợp object có kích thước cố định.

---

# 433.46 — Stack allocator

Cho temporary lifetimes rõ ràng.

---

# 433.47 — Memory APIs

Standard library cung cấp:

```text
alloc
dealloc
realloc
copy
move
zero
fill
```

với safety contract rõ ràng.

---

# 433.48 — Unsafe memory operations

Low-level API nằm trong:

```text
unsafe
```

namespace/module.

---

# 433.49 — Volatile

Compiler intrinsic:

```text
volatile_load
volatile_store
```

được dành cho memory-mapped IO/device semantics.

---

# 433.50 — Atomics

Atomic primitives từ 424 được expose trong core:

```text
AtomicBool
AtomicI32
AtomicU32
AtomicI64
AtomicU64
AtomicUsize
AtomicIsize
```

---

# 433.51 — Atomic pointer

Có thể:

```text
AtomicPtr<T>
```

với unsafe rules phù hợp.

---

# 433.52 — Atomic ordering

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

---

# 433.53 — Synchronization

Standard library:

```text
Mutex
RwLock
Semaphore
Condvar
Once
Barrier
```

---

# 433.54 — Mutex ownership

Mutex guard là resource-owning value:

```text
lock()
 ↓
Guard
 ↓
drop
 ↓
unlock
```

RAII/deterministic cleanup.

---

# 433.55 — No hidden locking

Axiom không tự động thêm mutex khi truy cập shared mutable data.

---

# 433.56 — Channel

Library abstraction:

```text
Channel<T>
Sender<T>
Receiver<T>
```

---

# 433.57 — Channel ownership

Message passing ưu tiên move semantics.

```text
sender.send(value)
```

có thể transfer ownership.

---

# 433.58 — Thread

Thread API:

```text
thread::spawn(...)
thread::join(...)
```

được standard/platform library cung cấp.

Thread primitive lowering vẫn thuộc compiler/runtime integration.

---

# 433.59 — Thread handle

Handle là resource.

Drop behavior phải explicit theo 424.

---

# 433.60 — Thread-local storage

```text
thread_local
```

được compiler/ABI hỗ trợ.

API nằm ở standard library.

---

# 433.61 — Async

Async API không thuộc language core ngoài syntax/lowering đã khóa ở 424.

Executor thuộc library/runtime.

---

# 433.62 — Future

Conceptual:

```text
Future<T>
```

là state machine.

---

# 433.63 — Executor

Có thể có:

```text
single_thread_executor
thread_pool_executor
io_executor
custom_executor
```

Không có executor duy nhất bắt buộc.

---

# 433.64 — Async runtime optional

Program không dùng async:

```text
```

→ không link async runtime.

---

# 433.65 — Async allocation

Compiler phải ưu tiên stack/static state-machine storage khi escape analysis cho phép.

---

# 433.66 — Cancellation

Cancellation là library contract.

Cleanup vẫn theo ownership model 423.

---

# 433.67 — IO

Standard library cung cấp abstraction:

```text
Reader
Writer
Read
Write
Seek
```

---

# 433.68 — File

```text
File
```

là resource-owning type.

Drop đóng file theo deterministic cleanup.

---

# 433.69 — Explicit close

Có thể hỗ trợ:

```text
file.close()
```

nhưng drop vẫn là safety net.

---

# 433.70 — File buffering

Buffering là library layer.

Không ép mọi file handle phải buffered.

---

# 433.71 — Standard streams

```text
stdin
stdout
stderr
```

là platform runtime services.

---

# 433.72 — Networking

Standard library abstraction:

```text
TcpStream
TcpListener
UdpSocket
```

---

# 433.73 — Networking runtime

Network stack implementation phụ thuộc OS/platform.

Axiom API không cần expose OS-specific details trừ khi programmer yêu cầu.

---

# 433.74 — Async networking

Có thể có:

```text
AsyncTcpStream
AsyncUdpSocket
```

nhưng API nên reuse common traits.

---

# 433.75 — HTTP

HTTP client/server **không thuộc core**.

Có thể nằm ở higher-level package:

```text
std::net::http
```

hoặc ecosystem package.

---

# 433.76 — TLS

TLS không phải compiler/runtime core.

Là security/network package.

---

# 433.77 — Filesystem

Filesystem abstraction:

```text
Path
File
Directory
Metadata
```

---

# 433.78 — Path

Path không nhất thiết là UTF-8 string trên mọi platform.

Axiom phải cho phép platform-native path representation.

---

# 433.79 — Environment

API:

```text
env::args()
env::get(...)
```

thuộc platform library.

---

# 433.80 — Process

```text
Process
Command
ExitStatus
```

thuộc standard library/platform.

---

# 433.81 — Dynamic library

API có thể load shared library:

```text
load_library(...)
```

nhưng nằm ở platform/system layer.

---

# 433.82 — Time

Core không phụ thuộc wall clock.

Standard library:

```text
Duration
Instant
SystemTime
```

---

# 433.83 — `Instant`

Dùng monotonic clock.

Phù hợp:

```text
benchmark
timeout
scheduler
```

---

# 433.84 — `SystemTime`

Đại diện wall-clock time.

Có thể thay đổi/điều chỉnh theo OS.

---

# 433.85 — Duration

Value type:

```text
Duration
```

không allocation.

---

# 433.86 — Date/time calendar

Calendar/time-zone API là higher-level library.

Không đưa toàn bộ timezone database vào core runtime.

---

# 433.87 — Random

Core không có implicit global RNG.

Standard library cung cấp:

```text
Random
SecureRandom
```

---

# 433.88 — Cryptographic RNG

Secure randomness phải delegate tới OS/platform secure entropy source hoặc audited implementation.

Không tự tạo RNG yếu rồi gọi là secure.

---

# 433.89 — Math

Core numeric operations:

```text
+
-
*
/
```

Compiler intrinsic khi cần.

Standard math:

```text
sin
cos
tan
sqrt
exp
log
pow
```

---

# 433.90 — Math implementation

Compiler có thể:

```text
inline
constant-fold
vectorize
call platform math
```

tùy target/profile.

---

# 433.91 — SIMD

SIMD types/intrinsics có thể thuộc:

```text
core::simd
```

nhưng target implementation compiler-specific.

---

# 433.92 — Portable SIMD

Có abstraction portable:

```text
Simd<T, N>
```

với target-specific lowering.

---

# 433.93 — Matrix/vector

Không biến matrix thành primitive type.

Library:

```text
Vec2
Vec3
Vec4
Mat4
```

có thể dùng generic/const generics.

---

# 433.94 — GPU

GPU API không thuộc core.

Tầng:

```text
gpu
 ↓
graphics
compute
```

là platform/library ecosystem.

---

# 433.95 — Tensor

Tensor cũng không thuộc core.

Nhưng Axiom type system + const generics + SIMD + comptime phải đủ mạnh để xây tensor library hiệu năng cao.

---

# 433.96 — ML runtime

PyTorch-like functionality không thuộc compiler runtime.

Có thể xây thành package:

```text
axiom::tensor
axiom::nn
axiom::autograd
```

---

# 433.97 — Logging

Logging không phải language primitive.

Standard library cung cấp API tối thiểu:

```text
log
warn
error
```

implementation có thể replace.

---

# 433.98 — Panic

Panic mechanism từ 425 nằm tại runtime boundary.

Các mode:

```text
panic=abort
panic=unwind
```

---

# 433.99 — Panic payload

Panic không cần runtime heap object bắt buộc.

Có thể panic với:

```text
static string
error value
```

tùy mode.

---

# 433.100 — Backtrace

Backtrace là optional diagnostic service.

Binary tối giản không phải mang full symbolization runtime.

---

# 433.101 — Assertions

```text
assert(...)
debug_assert(...)
```

là library/compiler-integrated utilities.

`debug_assert` bị loại trong release nếu profile quy định.

---

# 433.102 — Contracts

Future Axiom có thể hỗ trợ:

```text
requires
ensures
invariant
```

nhưng không đưa runtime checking vào mọi build mặc định.

---

# 433.103 — Reflection

Reflection runtime không mặc định.

Compile-time reflection từ 431 là hướng chính.

---

# 433.104 — Serialization

Serialization ưu tiên:

```text
@derive(Serializable)
```

→ comptime generate static code.

Không cần runtime reflection.

---

# 433.105 — JSON

JSON parser/serializer là standard/high-level library.

Không thuộc compiler.

---

# 433.106 — XML/CSV/YAML

Tương tự.

Không đưa parser vào language core.

---

# 433.107 — FFI

Core compiler hiểu ABI boundary.

Standard library cung cấp wrappers.

Ví dụ:

```text
extern "c" {
    fn malloc(size: usize) -> *mut u8
}
```

---

# 433.108 — C library

Axiom không cần ship một C compiler.

Có thể link system C libraries khi target/platform cung cấp.

---

# 433.109 — C runtime

Axiom executable không bắt buộc phải startup qua C runtime.

Compiler có thể emit native entrypoint trực tiếp.

---

# 433.110 — Native startup

Conceptual:

```text
OS loader
 ↓
_axiom_start
 ↓
runtime initialization
 ↓
main()
 ↓
exit
```

Runtime components chỉ được đưa vào nếu cần.

---

# 433.111 — Minimal startup

Freestanding program:

```text
OS loader
 ↓
entry
 ↓
main
```

không cần full standard runtime.

---

# 433.112 — Exit

```text
exit(code)
```

platform intrinsic/runtime service.

---

# 433.113 — Static initialization

Ưu tiên compile-time generated static data.

Tránh global constructor registry kiểu C++ khi không cần.

---

# 433.114 — Runtime initialization

Nếu cần:

```text
@init
```

có thể đăng ký initialization function, nhưng compiler phải xây deterministic initialization graph.

---

# 433.115 — Shutdown

Global shutdown handlers không được mặc định tồn tại.

Resource lifetime nên thuộc explicit owner/scope.

---

# 433.116 — Global state

`static mut` hoặc equivalent phải chịu ownership/concurrency restrictions.

Không coi global mutable state là tiện ích an toàn mặc định.

---

# 433.117 — Thread-safe global state

Dùng:

```text
Atomic
Mutex
Once
```

hoặc explicit unsafe.

---

# 433.118 — Error model

Standard library error types dùng:

```text
Result<T,E>
```

thay vì exception mặc định.

---

# 433.119 — IO errors

Ví dụ:

```text
fn read(...) -> Result<usize, IOError>
```

---

# 433.120 — Error composition

Các error có thể convert bằng trait:

```text
From
```

và propagate bằng:

```text
try
```

---

# 433.121 — Standard error hierarchy

Không cần một class hierarchy:

```text
Exception
 ├── IOError
 ├── NetworkError
 ...
```

Thay vào đó:

```text
struct IOError
enum NetworkError
```

và traits chung.

---

# 433.122 — Collection errors

Ví dụ indexing:

```text
get(i) -> Option<&T>
```

thay vì exception.

---

# 433.123 — Checked indexing

```text
array[i]
```

có bounds checking theo 422.

---

# 433.124 — Unchecked indexing

Unsafe API:

```text
array.get_unchecked(i)
```

hoặc equivalent.

---

# 433.125 — Bounds-check optimization

Compiler có thể loại bounds check khi chứng minh được index hợp lệ.

---

# 433.126 — Allocator failure

Standard collection allocation failure:

```text
Result
panic
abort
```

tùy configured OOM policy từ 423.

---

# 433.127 — No implicit GC

Standard library không được âm thầm biến:

```text
Vec
String
Map
```

thành GC objects.

---

# 433.128 — Reference counting

```text
Rc<T>
Arc<T>
Weak<T>
```

là library abstractions.

Không phải compiler primitive.

---

# 433.129 — Smart pointers

Có thể có:

```text
Box<T>
Rc<T>
Arc<T>
Weak<T>
```

nhưng chúng có ownership semantics rõ ràng.

---

# 433.130 — `Box<T>`

`Box<T>` là owning heap allocation.

Drop deterministic.

---

# 433.131 — `Arc<T>`

Atomic reference counting cho shared ownership giữa threads.

Không phải mặc định cho mọi object.

---

# 433.132 — Pinning

Async/self-referential structures có thể cần pinning abstraction.

Không đưa pinning vào tất cả types.

---

# 433.133 — ABI wrappers

Standard library wrappers không được làm thay đổi ABI của `extern "c"`.

---

# 433.134 — Platform abstraction

API common:

```text
std::os
std::fs
std::net
std::thread
```

implementation:

```text
windows
linux
macos
android
ios
wasm
```

---

# 433.135 — Platform-specific escape hatch

Có thể:

```text
os::windows::...
```

nhưng phải explicit.

---

# 433.136 — Conditional platform modules

431/432 cho phép:

```text
comptime if target.os == ...
```

---

# 433.137 — WASM

WASM standard environment không có native OS filesystem/thread assumptions.

Standard library phải capability-based.

---

# 433.138 — Embedded

Embedded profile có thể:

```text
runtime = "none"
allocator = "none"
```

nếu chương trình không cần chúng.

---

# 433.139 — Kernel development

Axiom phải có khả năng:

```text
freestanding
no_std-equivalent
no_allocator
custom_entry
```

để xây kernel/firmware.

---

# 433.140 — No mandatory libc

Axiom native program không bắt buộc:

```text
libc
```

nếu không dùng API yêu cầu libc.

---

# 433.141 — No mandatory C++ runtime

Không phụ thuộc:

```text
libstdc++
libc++
MSVC C++ runtime
```

trừ khi FFI/external library thực sự cần.

---

# 433.142 — Runtime component registry

Compiler/runtime package có thể khai báo component:

```text
startup
allocator
panic
thread
async
io
```

linker chỉ kéo component cần thiết.

---

# 433.143 — Runtime dependency graph

Ví dụ:

```text
File
 ↓
IO
 ↓
OS
```

nhưng:

```text
Vec
```

chỉ:

```text
Allocator
```

nếu heap được dùng.

---

# 433.144 — Static runtime linking

Mặc định có thể static-link runtime component nhỏ để tạo executable self-contained hơn.

---

# 433.145 — Dynamic runtime

Application có thể chọn dynamic runtime nếu muốn giảm disk duplication.

Không bắt buộc.

---

# 433.146 — Runtime versioning

Runtime ABI version phải được encode nếu dynamic runtime được sử dụng.

---

# 433.147 — Standard library ABI

Public standard-library ABI không được mặc định coi là stable across compiler versions.

FFI-stable interface phải explicit.

---

# 433.148 — Core library version

Core library phải tương thích với language edition/compiler.

---

# 433.149 — Library implementation freedom

Compiler không được phụ thuộc vào implementation cụ thể của `Vec`, `Map`, `String`.

Chỉ phụ thuộc public contract.

---

# 433.150 — Intrinsic escape hatch

Nếu library cần backend primitive:

```text
core::intrinsic
```

có thể expose compiler-supported intrinsic.

Intrinsic phải có semantic specification.

---

# 433.151 — Intrinsic không được tùy tiện

Không cho library gọi arbitrary compiler internal function.

---

# 433.152 — `unsafe` boundary

Low-level platform implementation thường dùng:

```text
unsafe
```

nhưng public API có thể cung cấp safe wrapper.

---

# 433.153 — Safe wrapper example

Platform:

```text
unsafe syscall(...)
```

library:

```text
fn read(file: File, buffer: []mut u8) -> Result<usize, IOError>
```

---

# 433.154 — Standard library safety

Library safe API phải duy trì invariants dù implementation bên trong dùng unsafe.

---

# 433.155 — Allocator-aware collections

Các collection quan trọng nên hỗ trợ custom allocator để phù hợp mục tiêu hiệu năng của Axiom.

---

# 433.156 — Zero-allocation APIs

Standard library phải ưu tiên API:

```text
write_to(buffer)
format_into(buffer)
parse_from(slice)
```

để application real-time tránh heap allocation.

---

# 433.157 — Allocation visibility

AI/compiler tooling nên có khả năng xác định function có allocation.

Ví dụ metadata:

```text
@allocates
@no_alloc
```

---

# 433.158 — Blocking visibility

API blocking có thể có:

```text
@blocking
```

để compiler/AI tooling phát hiện misuse trong async context.

---

# 433.159 — Panic visibility

Có thể:

```text
@no_panic
```

theo 425.

---

# 433.160 — Standard API effects

Một function metadata có thể mô tả:

```text
allocates
blocks
panics
unsafe
io
```

Nhưng đây là semantic metadata, không nhất thiết là một effect system nặng.

---

# 433.161 — No mandatory effect annotations

Programmer không phải annotate mọi function.

Compiler infer được những property có thể infer.

---

# 433.162 — AI-oriented library metadata

Library metadata có thể expose:

```text
inputs
outputs
ownership
allocation
blocking
thread-safety
panic behavior
```

giúp AI agent sử dụng API chính xác hơn.

---

# 433.163 — Documentation as metadata

Documentation được compiler/LSP expose theo symbol.

---

# 433.164 — Package layering

Recommended:

```text
core
 ↓
alloc
 ↓
std
 ↓
platform
 ↓
ecosystem
```

---

# 433.165 — `alloc`

Một intermediate library layer chứa:

```text
heap collections
allocator-backed String
Vec
Box
```

nhưng không cần OS filesystem/network.

---

# 433.166 — `std`

`std` thêm:

```text
IO
filesystem
thread
network
process
time
sync
```

---

# 433.167 — Ecosystem

Higher-level:

```text
HTTP
TLS
GUI
database
image
audio
video
GPU
ML
```

không nằm trong core.

---

# 433.168 — GUI

Axiom không hard-code một GUI framework vào language.

Có thể xây:

```text
std::gui
```

ở layer ecosystem/platform nếu sau này chuẩn hóa.

---

# 433.169 — Graphics

Graphics backend:

```text
Vulkan
Metal
DirectX
OpenGL
WebGPU
```

là platform/ecosystem layers.

---

# 433.170 — Audio/video

Không thuộc runtime core.

---

# 433.171 — Database

Không thuộc standard core.

---

# 433.172 — Compression

Có thể ecosystem library:

```text
zlib
zstd
lz4
```

hoặc native Axiom implementations.

---

# 433.173 — Cryptography

Security-sensitive primitives cần implementation được audit.

Không tạo crypto API "toy" trong compiler core.

---

# 433.174 — Unicode

Core đảm bảo UTF-8.

Unicode normalization/grapheme segmentation/database có thể nằm trong standard Unicode library.

---

# 433.175 — Regex

Regex không phải language primitive.

Library.

---

# 433.176 — Parsing

Parser combinators/lexer framework là library.

Comptime có thể dùng parser library để generate code.

---

# 433.177 — Serialization code generation

Ưu tiên:

```text
@derive(Serialize)
```

→ compile-time generated static implementation.

---

# 433.178 — Reflection-free serialization

Runtime:

```text
serialize(user)
```

không cần inspect type metadata.

---

# 433.179 — Binary serialization

Library có thể cung cấp endian-aware primitives:

```text
read_u32_le
read_u32_be
write_u64_le
```

---

# 433.180 — Endianness

422 đã khóa representation.

Library phải expose explicit conversion.

---

# 433.181 — Networking byte order

Network protocols không được phụ thuộc host endianness.

---

# 433.182 — Benchmark

Standard tooling:

```text
axiom bench
```

không phải runtime primitive.

---

# 433.183 — Test framework

Testing framework có thể là standard tooling package.

Language chỉ cần assertion/panic semantics.

---

# 433.184 — Debugger integration

Compiler emits standard debug metadata.

Debugger không thuộc language runtime.

---

# 433.185 — Sanitizers

Address/race/UB instrumentation là compiler tooling/profile.

Không phải runtime requirement.

---

# 433.186 — Profiling

Compiler có thể emit:

```text
profiling hooks
```

chỉ khi profile yêu cầu.

---

# 433.187 — Tracing

Tracing runtime optional.

---

# 433.188 — Telemetry

Không được tự động tồn tại trong executable.

---

# 433.189 — Localization

Locale API thuộc standard library.

---

# 433.190 — Internationalization

Unicode core + ICU-like higher-level package nếu cần.

---

# 433.191 — Environment-independent core

Core algorithms phải hoạt động mà không cần:

```text
filesystem
network
environment
clock
```

---

# 433.192 — Deterministic core

Điều này giúp:

- embedded;
- kernel;
- WASM;
- comptime;
- testing.

---

# 433.193 — Runtime-free computation

Ví dụ:

```text
fn dot(a: Vec4, b: Vec4) -> f32 {
    ...
}
```

có thể compile hoàn toàn runtime-independent.

---

# 433.194 — Runtime boundary in compiler

Compiler phải biết một function có dependency tới runtime component nào.

IR metadata:

```text
requires_runtime:
    allocator
    panic
    io
```

---

# 433.195 — Linker runtime pruning

420 linker dùng metadata + reachability để loại component không cần.

---

# 433.196 — Binary size target

Không đặt một con số cứng cho mọi program.

Nguyên tắc:

> Runtime footprint phải tỷ lệ với capability thực sự được sử dụng.

---

# 433.197 — Startup cost

Runtime startup phải tối thiểu.

Không load toàn bộ standard library registry trước `main`.

---

# 433.198 — No hidden background threads

Standard library không tự spawn thread trừ khi API explicit yêu cầu.

---

# 433.199 — No hidden allocator

Không có allocator background/global magic ngoài policy được chọn.

---

# 433.200 — Final library architecture

```text
                     AXIOM LANGUAGE
                           │
            ┌──────────────┴──────────────┐
            │                             │
       Compiler Core                 Core Library
            │                             │
     ABI / IR / Intrinsic          Option / Result
            │                      Iterator / String
            │                      basic collections
            │                             │
            └──────────────┬──────────────┘
                           │
                         alloc
                           │
                  Vec / Box / Map
                           │
                           ▼
                          std
                           │
        ┌──────────┬───────┼────────┬──────────┐
        │          │       │        │          │
       IO         FS     Thread    Async     Network
        │          │       │        │          │
        └──────────┴───────┴────────┴──────────┘
                           │
                      Platform Layer
                           │
       ┌──────────┬────────┼────────┬──────────┐
     Windows     Linux    macOS   Android     WASM
                           │
                           ▼
                       Ecosystem
                 GUI / GPU / ML / DB
```

---

## 433.201 — Invariants

Axiom standard library architecture được khóa với các invariant:

1. Không có GC.
2. Không có mandatory fat runtime.
3. Core không phụ thuộc OS.
4. Runtime component được link theo nhu cầu.
5. `Option`/`Result` là abstraction chuẩn cho absence/failure.
6. String mặc định UTF-8.
7. Collection ownership deterministic.
8. Allocator có thể thay thế.
9. Async runtime không bắt buộc.
10. Thread runtime không được tự động kéo vào chương trình không dùng thread.
11. Filesystem/network không thuộc core.
12. GUI/GPU/ML không thuộc language core.
13. Reflection runtime không mặc định.
14. Serialization ưu tiên compile-time generation.
15. FFI/ABI là compiler boundary.
16. Freestanding/embedded/WASM phải là first-class targets.
17. Standard library không được che giấu allocation/blocking/IO một cách tùy tiện.
18. Safe API có thể được xây trên unsafe platform primitives.
19. Binary size phụ thuộc capability sử dụng.
20. Không có global background service/thread ngầm.
21. Standard library implementation có thể thay đổi mà language semantics không đổi.
22. Core library phải đủ nhỏ để compiler self-hosting và embedded use không bị kéo theo application runtime.

**BOOTSTRAP-433 hoàn tất.**

---

# BOOTSTRAP-434 — TOOLCHAIN, CLI, DIAGNOSTICS, LSP, FORMATTER, PACKAGE TOOLS & DEVELOPER EXPERIENCE

Bây giờ phần semantic foundation đã khá đầy:

```text
420 Machine code / Object / Linker
421 ABI
422 Type layout
423 Memory / Ownership
424 Concurrency
425 Errors
426 Generics / Traits
429 Syntax
430 Type system
431 Comptime
432 Modules / Build
433 Library / Runtime
```

Task 434 chuyển sang **toolchain chính thức**.

Mục tiêu là compiler không chỉ compile được Axiom mà còn phải trở thành một hệ sinh thái developer/AI-friendly hoàn chỉnh:

```text
axiom build
axiom check
axiom run
axiom test
axiom fmt
axiom doc
axiom package
axiom publish
axiom clean
axiom cache
axiom lsp
```

và đặc biệt khóa **diagnostic format machine-readable**, incremental compilation, compiler driver, LSP, formatter và API để AI agent có thể hiểu/chỉnh sửa project mà không cần parse thủ công toàn bộ repository.