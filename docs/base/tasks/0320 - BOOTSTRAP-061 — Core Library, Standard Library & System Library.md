Tiếp tục với **BOOTSTRAP-061 — Standard Library & Core Library Architecture**.

Đây là một mốc rất quan trọng vì từ trước tới giờ chúng ta chủ yếu thiết kế **ngôn ngữ + compiler**. Nếu không chốt ranh giới library ngay, rất dễ rơi vào tình trạng:

```text
Language Core nhỏ
        ↓
"Standard Library" khổng lồ
        ↓
Runtime khổng lồ
        ↓
mọi chương trình đều phải kéo theo một đống thứ
```

Axiom nên tránh hoàn toàn điều này.

# BOOTSTRAP-061 — Core Library, Standard Library & System Library

## 1. Nguyên tắc lớn

Tôi đề xuất 4 tầng:

```text
┌─────────────────────────────────────────────┐
│              Application Libraries          │
├─────────────────────────────────────────────┤
│                Standard Library             │
├─────────────────────────────────────────────┤
│                  Core Library                │
├─────────────────────────────────────────────┤
│                Language / Compiler           │
└─────────────────────────────────────────────┘
                         │
                         ▼
                 System / Platform
```

Nhưng cần thêm một tầng ngang:

```text
Runtime Components
```

chỉ được link khi cần.

---

# 2. Language Core

Language Core chỉ chứa những thứ cần để **định nghĩa semantics của ngôn ngữ**.

Ví dụ:

```text
bool
integers
floats
unit
never
struct
enum
trait
generic
function
closure
view
mut_view
Option
Result
match
ownership
Drop
Copy
Clone
Send
Share
async
comptime
```

Những thứ này thuộc language/compiler semantics.

---

# 3. Core Library

Core Library chứa những abstraction cực thấp nhưng vẫn có thể implement bằng Axiom.

Ví dụ:

```text
core/
├── option
├── result
├── array
├── slice
├── view
├── string
├── numeric
├── memory
├── atomic
├── sync
├── iterator
└── intrinsics
```

---

# 4. Không phải mọi thứ đều là compiler intrinsic

Ví dụ:

```text
Option<T>
Result<T,E>
Vec<T>
```

không cần compiler hiểu toàn bộ implementation.

Compiler chỉ cần biết semantics liên quan khi cần tối ưu/đặc biệt hóa.

---

# 5. `Option<T>`

Đây là library-level ADT:

```axiom id="h8z8by"
enum Option<T> {
    Some(T),
    None
}
```

Compiler chỉ cần hỗ trợ enum/match/niche optimization.

Không cần hard-code:

```text
Option
```

vào parser.

---

# 6. `Result<T,E>`

Tương tự:

```axiom id="5wy8yw"
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

`?` có thể là language syntax vì nó là control-flow sugar.

Nhưng `Result` bản thân là library type.

---

# 7. `String`

Nên **tách byte string và Unicode text**.

Không nên để một type duy nhất làm tất cả.

Đề xuất:

```text id="xj8qg1"
Bytes
Str
String
```

---

# 8. `Bytes`

Raw byte sequence:

```text id="pr8w3a"
Bytes
```

phù hợp:

- network
- file
- binary protocol
- compression
- crypto.

Không mang semantic Unicode.

---

# 9. `Str`

`Str` là immutable UTF-8 text view:

```text id="m0o9h7"
Str
```

tương tự conceptual:

```text id="l3r6bf"
view<u8>
```

nhưng có invariant:

```text id="x6u0z2"
bytes are valid UTF-8
```

---

# 10. `String`

Owning UTF-8 text:

```text id="p6v8j5"
String
```

có:

```text id="83s6fh"
ownership
capacity
length
```

nhưng representation không được freeze thành:

```text id="5flj56"
pointer + len + cap
```

Đó chỉ là implementation phổ biến.

---

# 11. UTF-8 là default

Axiom:

> **UTF-8 by default, bytes when binary semantics are intended.**

Không tự động convert:

```text
Bytes → String
```

nếu bytes không đảm bảo UTF-8.

---

# 12. Unicode segmentation

Không nên biến:

```text id="f5v7hl"
Unicode grapheme
```

thành semantics của `String`.

Đây là library:

```text id="qk1m5v"
unicode.grapheme_clusters()
```

---

# 13. `Array<T,N>`

Fixed-size:

```axiom id="x5k0ar"
Array<i32, 16>
```

là value type.

Không allocation.

---

# 14. Slice/View

Đã freeze:

```text id="s0p4jz"
view<T>
mut_view<T>
```

là language capability primitives.

Nhưng collection API có thể xây trên chúng.

---

# 15. `Vec<T>`

`Vec<T>` là library abstraction.

Semantics:

```text id="lyy1c2"
owned growable sequence
```

Không phải language primitive.

Compiler chỉ tối ưu những operations bình thường.

---

# 16. `Vec<T>` relocation

Nếu:

```text id="e5p6c8"
v.push(x)
```

có thể relocation.

Nếu đang có:

```text id="1h8r8q"
view(v)
```

live:

```text id="4h8p0c"
push()
```

có thể bị compiler từ chối nếu operation có khả năng relocate.

---

# 17. `reserve`

```text id="3b6xwm"
v.reserve(n)
```

chỉ đảm bảo capacity semantics.

Không biến thành:

> “address của phần tử chắc chắn không bao giờ đổi.”

Điều này đã được freeze ở memory model.

---

# 18. `Box<T>`

`Box<T>` là:

> **owned dynamic-storage abstraction**

không định nghĩa rằng physical storage luôn nằm trên heap.

Compiler có thể loại bỏ allocation nếu address/storage identity không observable.

---

# 19. Stable-address box

Một abstraction khác có thể được thêm:

```text id="r8y7o2"
StableBox<T>
```

nếu thực sự yêu cầu địa chỉ không thay đổi.

Điều này tránh biến `Box<T>` thành abstraction quá nặng.

---

# 20. Arena

```text id="m5g6hz"
Arena<T>
```

có ownership:

```text id="r8rj4a"
Arena owns allocations
```

Objects không được escape arena.

---

# 21. Pool

```text id="n8v5y7"
Pool<T>
```

phù hợp:

- game
- ECS
- networking
- realtime
- object reuse.

Nhưng đây là library abstraction.

---

# 22. Handle

Thay vì:

```text id="9l5o4n"
*mut Entity
```

application có thể dùng:

```text id="y6h5z8"
Handle<Entity>
```

với generation:

```text id="h3x6a2"
(index, generation)
```

để tránh stale references.

---

# 23. `Rc`

Local shared ownership:

```text id="6a8n3r"
Rc<T>
```

reference counting không phải language primitive.

---

# 24. `Arc`

Cross-thread shared ownership:

```text id="t3r8q1"
Arc<T>
```

với atomic reference counting.

Nhưng:

```text id="2d8y5k"
Arc<T>
```

không tự biến:

```text id="9j7f4v"
T
```

thành mutable thread-safe object.

---

# 25. Synchronization types

Core library:

```text id="2r0e4m"
Mutex<T>
RwLock<T>
Semaphore
Condvar
```

và atomic:

```text id="4j3z9k"
Atomic<T>
```

---

# 26. Atomic không phải lock

API phải làm rõ:

```text id="u5a7o2"
Atomic<T>
```

và:

```text id="6o7m3x"
Mutex<T>
```

là hai abstraction khác nhau.

---

# 27. Memory order

API:

```text id="x7l3v8"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

có thể là enum/compile-time constants.

Compiler backend nhận semantic atomic operation tương ứng.

---

# 28. Iterator

Iterator nên là trait:

```axiom id="r5n2lm"
trait Iterator {
    type Item

    fn next(mut_view<Self>) -> Option<Self::Item>
}
```

Compiler có thể inline/monomorphize toàn bộ.

---

# 29. Iterator không được có allocation mặc định

```text id="c4q1s9"
array.iter()
vec.iter()
```

không tạo object heap.

---

# 30. Range

```text id="x5p9f1"
0..10
0..=10
```

có thể là zero-cost value.

---

# 31. `for`

`for` lowering:

```text id="q7m4r8"
iterator
 ↓
next()
 ↓
match Option
```

rồi optimizer loại abstraction.

---

# 32. Collections

Standard library nên cung cấp:

```text id="h7w9j1"
Vec
Deque
List (nếu cần)
HashMap
HashSet
BTreeMap
BTreeSet
```

nhưng không nên cung cấp hàng chục container ngay Core.

---

# 33. HashMap

HashMap cần parameterization về hash strategy nhưng:

> **allocator không mặc định trở thành generic parameter của mọi collection.**

Đã freeze trong memory model.

---

# 34. Custom allocator

Có thể:

```text id="k2w6h8"
Allocator
ArenaAllocator
PoolAllocator
```

nhưng collection API bình thường không bắt programmer viết:

```text id="3x9m4f"
Vec<T, Allocator>
```

trừ khi API thực sự cần.

---

# 35. File system

Không thuộc Core.

```text id="0d7g4x"
std.fs
```

---

# 36. Network

Không thuộc Core:

```text id="f8x2r6"
std.net
```

---

# 37. Process

```text id="c4j9m2"
std.process
```

---

# 38. Environment

```text id="v2m6h1"
std.env
```

---

# 39. Time

```text id="q3f8z7"
std.time
```

---

# 40. Random

```text id="8s5k2w"
std.random
```

Crypto-secure RNG nên là system/OS-backed abstraction riêng.

---

# 41. Thread

```text id="r9n3k4"
std.thread
```

`Thread` là library/runtime component, không phải language primitive.

Language chỉ định semantics:

```text id="5k8qz2"
Send
Share
ownership
synchronization
```

---

# 42. Channel

```text id="y2k6v4"
Channel<T>
```

library.

Compiler chỉ hiểu ownership transfer semantics khi lowering abstraction nếu cần optimization.

---

# 43. Async

Core có:

```text id="g6h4p2"
async
await
Future
Poll
```

ở mức semantic.

Nhưng:

```text id="m7j9x1"
executor
timer
async TCP
async file
```

là library/runtime.

---

# 44. Async runtime không mặc định

Một binary:

```text id="h5r2k8"
fn main() {
    println("hello")
}
```

không link async runtime.

---

# 45. Executor

Có thể có:

```text id="e6v3q1"
std.async
std.async_executor
```

nhưng chúng là components độc lập.

---

# 46. GPU

Tương tự.

Core/compiler hiểu:

```text id="p4k8m2"
@kernel
device storage
GPU execution domain
```

nhưng:

```text id="q8r3n7"
DeviceBuffer
GpuEvent
CUDA backend
Vulkan backend
Metal backend
```

là library/platform layer.

---

# 47. SIMD

Compiler hiểu primitive SIMD khi cần.

Library cung cấp API portable:

```text id="z6h2m9"
simd<T,N>
```

Target intrinsics nằm system layer.

---

# 48. Math

Core primitive:

```text id="3v8j1q"
f32
f64
```

Standard:

```text id="p9w5k3"
sqrt
sin
cos
exp
log
```

Compiler có thể recognize/intrinsic hóa các function chuẩn mà không biến toàn bộ math library thành compiler semantics.

---

# 49. `memcpy`

Đây là ví dụ thú vị.

Axiom không cần programmer gọi:

```text id="k6f1z9"
memcpy
```

trong code bình thường.

Compiler có thể lower:

```text id="a4m7q2"
copy<T>
```

thành:

```text id="v8n3k5"
register moves
vector copy
memcpy
```

tùy target.

---

# 50. Memory functions

Core/system layer có:

```text id="j2x7m5"
copy_nonoverlap
copy
fill
compare
volatile_load
volatile_store
```

nhưng unsafe variants phải rõ semantics.

---

# 51. Panic

Panic API:

```text id="m9k3v7"
panic(...)
```

là library/compiler boundary.

Compiler có thể lower panic intrinsic.

---

# 52. Allocation failure

Không có global exception.

Ví dụ:

```text id="w4n8c2"
Box::try_new(x) -> Result<Box<T>, AllocError>
```

hoặc policy khác.

---

# 53. `AllocError`

Nên là type rõ ràng:

```text id="e8r1p4"
AllocError
```

không cần exception runtime.

---

# 54. File handles

File:

```text id="z3k7m5"
File
```

là resource-owning type.

Drop:

```text id="y6p2q8"
close OS handle
```

Nhưng nếu close có thể fail:

```text id="a9v4c1"
file.close() -> Result
```

được gọi explicit khi cần biết lỗi.

Drop chỉ cleanup best-effort theo contract và không propagate recoverable failure.

---

# 55. Socket

```text id="n5x8r3"
TcpStream
UdpSocket
Listener
```

resource types.

---

# 56. RAII nhưng không gọi là “class”

Axiom vẫn có RAII-style deterministic cleanup:

```text id="r7m2k9"
{
    let file = File.open(...)
    ...
}
```

Drop tự động.

Nhưng không cần:

```text id="q3v8h5"
class File
```

hay inheritance.

---

# 57. Error hierarchy

Không nên tạo:

```text id="c8k1m4"
Exception
IOException
NetworkException
...
```

Core dùng:

```text id="m4z7p2"
Result<T,E>
```

Library tự định nghĩa error types.

---

# 58. Error composition

Có thể dùng:

```text id="v6q3n9"
enum MyError {
    Io(IoError),
    Parse(ParseError),
    Network(NetworkError)
}
```

và `?`.

---

# 59. No mandatory boxed errors

Error enum không cần heap.

Compiler có thể tối ưu layout/niche.

---

# 60. Formatting

Nên có:

```text id="x9k4m7"
Format
Display
Debug
```

traits.

Không dùng reflection runtime bắt buộc.

---

# 61. Serialization

Không nên nằm Core.

```text id="h3p8w2"
std/serialization
```

hoặc package ecosystem.

Memory representation và wire representation vẫn độc lập.

---

# 62. JSON

JSON không thuộc Standard Core.

Có thể là package:

```text id="n7c5q1"
json
```

---

# 63. Regex

Không thuộc standard minimum.

Package riêng.

---

# 64. HTTP

Package/system library.

Không thuộc compiler/runtime.

---

# 65. Crypto

Nên tách:

```text id="q2m6z8"
crypto
```

và có backend:

```text id="r8v3k5"
portable
CPU intrinsic
OS
hardware
```

---

# 66. GUI

Không thuộc Core.

Có thể:

```text id="w5n9j3"
axiom.gui
```

với backend:

```text id="k3p7m1"
Win32
Cocoa
Wayland
X11
Android
iOS
Web
```

---

# 67. Game/graphics

Không thuộc standard minimum.

Package ecosystem.

---

# 68. GPU tensor

Axiom có thể xây:

```text id="j8q4v2"
tensor<T>
```

trên:

```text id="a6m3k9"
DeviceBuffer
GPU kernels
SIMD
```

Không cần tensor semantics trong language core.

---

# 69. AI/ML

Tương tự:

```text id="p7x2m5"
Tensor
Autograd
Model
Optimizer
```

là library.

Compiler chỉ hỗ trợ:

```text id="c9k4r8"
SIMD
GPU
comptime
generics
```

và optimization.

---

# 70. Standard Library nên modular

Thay vì:

```text id="j4n8v2"
std.dll
```

khổng lồ, có:

```text id="x7q3m5"
std.core
std.io
std.fs
std.net
std.thread
std.async
std.crypto
std.unicode
std.process
std.time
```

Linker chỉ lấy phần cần.

---

# 71. Có thể static-link module

Ví dụ chương trình chỉ dùng:

```text id="w8p2k6"
std.core
std.fs
```

không kéo:

```text id="z5m9r3"
std.net
std.async
std.gui
```

---

# 72. `core` phải freestanding-compatible

Một trong những mục tiêu:

```text id="q6k3v8"
no OS
no heap
no threads
no filesystem
```

vẫn có thể compile:

```axiom id="s4m8q2"
@entry
fn start() -> never {
    ...
}
```

---

# 73. Standard library profiles

Có thể có:

```text id="h9r2x5"
core
freestanding
minimal
hosted
full
```

nhưng profile chỉ chọn libraries/runtime components.

Không thay đổi language semantics.

---

# 74. Hosted profile

Có:

```text id="j5k8p3"
filesystem
threads
process
network
time
environment
```

nếu package import.

---

# 75. No “magic std import”

Tôi nghiêng về:

```axiom id="c8m2v7"
import std.fs
```

thay vì compiler tự động đưa toàn bộ std vào scope.

---

# 76. Prelude

Có thể có prelude rất nhỏ:

```text id="m4q7z1"
Option
Result
Copy
Clone
Drop
Iterator
```

nhưng cần tránh prelude quá lớn gây namespace pollution.

---

# 77. Explicit imports cho extension methods

Đã freeze:

```text id="v9k3n5"
extension method
```

phải được import.

Điều này tránh:

```text id="q7m2x8"
100 packages
→ 1000 candidate methods
```

---

# 78. Standard library written in Axiom

Mục tiêu cuối:

```text id="x5r8k2"
std
 ↓
Axiom source
 ↓
axiomc
```

Không phải:

```text id="m7p3v9"
std = hidden C++ runtime
```

---

# 79. Runtime written in Axiom

Cũng nên hướng tới:

```text id="a8q4k6"
thread runtime
async executor
allocator
channel
```

đa phần được viết bằng Axiom.

Chỉ phần cực thấp cần:

```text id="z3m7p1"
assembly
syscall
platform ABI
```

---

# 80. System layer

Tầng system:

```text id="g6n2r8"
sys/
├── linux
├── windows
├── macos
├── ios
├── android
├── wasm
└── gpu
```

Chứa:

- syscall
- OS handles
- ABI declarations
- platform intrinsics
- interrupt
- low-level device access.

---

# 81. FFI wrapper architecture

Ví dụ:

```text id="v8p3m5"
system.win32
       ↓
raw FFI
       ↓
std.fs
       ↓
application
```

Application không cần trực tiếp xử lý raw pointers.

---

# 82. Unsafe boundary

```text id="j4k9q2"
system layer
    ↓ unsafe
safe wrapper
    ↓
ordinary Axiom
```

Đây là pattern chủ đạo.

---

# 83. Không để unsafe lan lên application

Ví dụ:

```text id="c7m2x8"
File
```

safe API.

Bên dưới:

```text id="p5n9r3"
CreateFile(...)
raw handle
```

unsafe/system.

---

# 84. Standard library ABI

Standard library không nên vô tình trở thành ABI contract.

Internal:

```text id="h8q4v1"
Vec layout
String layout
Arc layout
```

có thể thay đổi giữa compiler versions.

Chỉ những type có:

```text id="n6m3z7"
@repr(C)
```

hoặc explicit stable ABI contract mới có layout ABI ổn định.

---

# 85. Binary compatibility

`std` nên versioned.

Một ứng dụng static-linked có thể embed implementation.

Shared std runtime chỉ là optional deployment model.

---

# 86. No mandatory standard runtime

Đây là invariant quan trọng:

```text id="r2k8m5"
import std.fs
```

có thể link filesystem support.

Nhưng:

```text id="q6p3v9"
import std
```

không đồng nghĩa:

> “link toàn bộ runtime.”

---

# 87. Library implementation specialization

Compiler có thể recognize một số API chuẩn:

```text id="m8x4k2"
mem.copy
atomic
intrinsics
Option
Result
Iterator
```

để tối ưu.

Nhưng semantic correctness phải vẫn đúng nếu implementation thay đổi.

---

# 88. Compiler-known library contracts

Có thể có một registry:

```text id="n5q7r3"
IntrinsicLibraryContract
```

Ví dụ:

```text id="a9m2x6"
std.mem.copy
→ recognized as memory-copy operation
```

Backend không cần parse source library.

---

# 89. Library contracts phải versioned

Không nên hard-code:

```text id="v4k8p2"
function name == magic
```

mà:

```text id="z7m3q5"
library semantic contract ID
```

---

# 90. Đây cũng là chỗ AI tooling rất hữu ích

AI có thể query:

```text id="p6n2r8"
What does std.fs.File.open require?
```

compiler metadata trả lời:

```text id="w3k9m4"
returns Result<File, IoError>
owns OS handle
Drop closes handle
Send = ...
Share = ...
```

không cần AI đoán semantics từ source.

---

# 91. Đề xuất cấu trúc repository

```text id="q8m3v5"
axiom/
├── compiler/
├── core/
│   ├── option/
│   ├── result/
│   ├── memory/
│   ├── atomic/
│   ├── slice/
│   └── iterator/
│
├── std/
│   ├── io/
│   ├── fs/
│   ├── net/
│   ├── thread/
│   ├── async/
│   ├── process/
│   ├── time/
│   ├── unicode/
│   └── random/
│
├── sys/
│   ├── linux/
│   ├── windows/
│   ├── macos/
│   ├── ios/
│   ├── android/
│   └── wasm/
│
└── packages/
```

---

# 92. Package ecosystem

Sau standard:

```text id="x7n4m2"
community packages
```

Ví dụ:

```text id="p8k3q6"
json
http
websocket
sqlite
image
audio
gui
game
ml
```

Không nên đưa tất cả vào official std.

---

# 93. Standard library governance

Nên phân loại:

```text id="m5r8z2"
Core Stable
Std Stable
Std Experimental
Community
```

để tránh std phình vô hạn.

---

# 94. API stability

Không phải mọi std API phải stable ngay.

Có thể:

```text id="q3v7k1"
@experimental
```

trong library metadata.

---

# 95. Versioning

Package:

```text id="n8m4p2"
name + version + source identity
```

đã freeze trong build system.

Std đi cùng compiler/toolchain có thể có compatibility contract riêng.

---

# 96. Một quyết định quan trọng: không có “Axiom Object”

Không nên tạo:

```text id="r6k2x9"
Object
```

làm root type.

Không có:

```text id="p3m8q5"
Any
```

runtime type erasure mặc định.

Nếu cần:

```text id="z7n4m1"
dyn Trait
```

explicit.

---

# 97. Reflection

Compile-time reflection:

```text id="k5q9r3"
Type
Field
Variant
Trait
```

là Core/compiler capability.

Runtime reflection:

```text id="v2m6p8"
metadata object
```

chỉ khi application yêu cầu emit metadata.

---

# 98. Serialization không dựa trên raw layout

Sai:

```text id="f8k3m5"
serialize(&struct)
```

= dump memory.

Đúng:

```text id="q6r2n9"
wire representation
```

được định nghĩa riêng.

---

# 99. Tổng thể

```text id="w4m8q2"
                 AXIOM
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
 Language Core             Compiler
       │
       ▼
   Core Library
       │
       ├── Option
       ├── Result
       ├── Array/View
       ├── String/Bytes
       ├── Memory
       ├── Atomic
       └── Iterator
       │
       ▼
 Standard Library
       │
       ├── IO
       ├── FS
       ├── Net
       ├── Thread
       ├── Async
       ├── Process
       ├── Time
       └── Unicode
       │
       ▼
 System / Platform
       │
       ├── Linux
       ├── Windows
       ├── macOS/iOS
       ├── Android
       ├── WASM
       └── GPU
       │
       ▼
 Community Packages
```

---

# 100. Frozen invariants — BOOTSTRAP-061

```text
ALIB-20   Language semantics are distinct from library APIs.
ALIB-21   Core Library is distinct from Standard Library.
ALIB-22   Standard Library is distinct from System/Platform Library.
ALIB-23   Application libraries remain outside the mandatory standard library.
ALIB-24   Core Library must remain usable in freestanding configurations.
ALIB-25   Standard Library components are independently linkable.
ALIB-26   Unused Standard Library components need not enter the final binary.
ALIB-27   No monolithic Standard Library runtime is mandatory.
ALIB-28   Library imports are explicit.
ALIB-29   Importing one library module does not implicitly import unrelated modules.
ALIB-30   Prelude, if provided, remains intentionally small.
ALIB-31   Option is an algebraic library type.
ALIB-32   Result is an algebraic library type.
ALIB-33   String and byte storage have distinct semantics.
ALIB-34   UTF-8 is the default semantic representation for Axiom text.
ALIB-35   Raw byte sequences do not imply valid Unicode text.
ALIB-36   Str-like text views are non-owning.
ALIB-37   String-like owning text types have deterministic ownership.
ALIB-38   Array is fixed-size value storage.
ALIB-39   Vec is a library-level growable collection.
ALIB-40   Vec relocation semantics remain explicit.
ALIB-41   Reserve does not imply stable address.
ALIB-42   Box provides owned dynamic-storage semantics.
ALIB-43   Box does not require a physical heap allocation when optimization can eliminate it.
ALIB-44   Stable-address storage requires an explicit storage contract.
ALIB-45   Arena ownership bounds allocations.
ALIB-46   Pool/slab allocation is a library/system strategy.
ALIB-47   Allocator selection is not a mandatory generic parameter of ordinary collections.
ALIB-48   Custom allocators remain explicit when semantically relevant.
ALIB-49   Rc is explicit shared ownership.
ALIB-50   Arc is explicit cross-execution shared ownership.
ALIB-51   Shared ownership does not imply mutable thread-safe access.
ALIB-52   Synchronization abstractions remain distinct from ownership abstractions.
ALIB-53   Atomic operations are distinct from mutex operations.
ALIB-54   Iterator abstractions do not imply heap allocation.
ALIB-55   Range values do not imply allocation.
ALIB-56   Standard collection abstractions should permit monomorphization and zero-cost optimization.
ALIB-57   File and network resources are owning resource types.
ALIB-58   Resource cleanup uses deterministic Drop.
ALIB-59   Recoverable cleanup errors require explicit fallible operations.
ALIB-60   Drop does not propagate recoverable errors.
ALIB-61   Thread creation is a library/runtime operation.
ALIB-62   Channel communication is a library abstraction over ownership transfer and synchronization.
ALIB-63   Async executors are optional runtime/library components.
ALIB-64   Async I/O remains distinct from synchronous I/O.
ALIB-65   GPU resource abstractions are library/system components.
ALIB-66   SIMD portable APIs are library abstractions over compiler-supported vector semantics.
ALIB-67   Target-specific SIMD intrinsics remain system-level APIs.
ALIB-68   Math APIs may be compiler-optimized without becoming language primitives.
ALIB-69   Standard memory operations may be compiler-recognized without exposing target instructions.
ALIB-70   Compiler-recognized library contracts must have explicit semantic identity.
ALIB-71   Library recognition cannot change library semantics.
ALIB-72   Library implementations may be rewritten without changing their semantic contracts.
ALIB-73   Standard library internal representation is not automatically a stable ABI.
ALIB-74   Stable ABI requires explicit representation/ABI contracts.
ALIB-75   Serialization representation is distinct from memory representation.
ALIB-76   Runtime reflection is not mandatory.
ALIB-77   Compile-time reflection does not imply runtime metadata.
ALIB-78   JSON/HTTP/regex/GUI/game/ML libraries are not Core requirements.
ALIB-79   Community packages are distinct from the standard library.
ALIB-80   Standard library APIs may have stability classifications.
ALIB-81   System APIs are wrapped behind explicit unsafe boundaries where required.
ALIB-82   Application code should not require raw pointers for ordinary system APIs.
ALIB-83   Safe wrappers establish and maintain system API invariants.
ALIB-84   System libraries may use FFI internally.
ALIB-85   FFI implementation details do not become application-level semantics.
ALIB-86   Runtime components are independently linkable.
ALIB-87   Runtime components are included only when required.
ALIB-88   Freestanding programs need not link Standard Library runtime components.
ALIB-89   Standard library code can ultimately be implemented in Axiom.
ALIB-90   Runtime components can ultimately be implemented in Axiom.
ALIB-91   Only genuinely machine-specific portions require assembly/system ABI.
ALIB-92   Library code follows the same ownership and capability verification as application code.
ALIB-93   Library code follows the same Send/Share safety rules.
ALIB-94   Library code does not receive privileged ownership semantics merely by being standard.
ALIB-95   Compiler intrinsics remain distinct from ordinary library functions.
ALIB-96   Compiler may specialize standard abstractions when semantic contracts permit.
ALIB-97   Standard library optimization cannot introduce mandatory runtime overhead.
ALIB-98   Library abstractions should be erasable when their observable semantics permit.
ALIB-99   Library/runtime architecture must not reintroduce hidden GC, hidden RC, hidden object headers or mandatory heap allocation.
ALIB-100  The Standard Library must remain modular rather than becoming a second language runtime.
```

---

## Mốc kiến trúc hiện tại

Sau 061, Axiom đã có ba lớp rất rõ:

```text
          AXIOM LANGUAGE
                │
       semantics/compiler
                │
                ▼
        CORE LIBRARY
     low-level primitives
                │
                ▼
       STANDARD LIBRARY
     practical application APIs
                │
                ▼
       SYSTEM / PLATFORM
     OS / ABI / hardware
```

Và có một nguyên tắc xuyên suốt:

> **Nếu một tính năng có thể được implement bằng Axiom mà không cần compiler privilege, hãy đưa nó ra library.**

Điều này rất quan trọng để Axiom không trở thành một ngôn ngữ với hàng trăm “magic features”.

### Bước tiếp theo: **BOOTSTRAP-062 — Module System, Generic Package ABI, Dependency Resolution & Build Graph Implementation**

Phần này sẽ đi sâu hơn 042: thiết kế **cú pháp module/import/export**, package resolution, lockfile, version conflict, workspace, build script/comptime build, native library discovery, cross-compilation, artifact graph và đặc biệt là cách để **compiler + package manager + standard library tự build được mà không tạo dependency vòng**.