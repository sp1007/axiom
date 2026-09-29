Tiếp tục với **AXIOM CORE / STANDARD LIBRARY / PLATFORM BOUNDARY v0.1**. Tôi nghĩ đây là một trong những điểm quan trọng nhất để giữ Axiom không bị phình thành “C++ mới”.

# AXIOM LIBRARY BOUNDARY v0.1

## 1. Ba tầng phải tách tuyệt đối

```text
┌─────────────────────────────────────┐
│              AXIOM CORE             │
│ ngôn ngữ + semantic primitives      │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│          STANDARD LIBRARY            │
│ data structures / algorithms / sync  │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│          PLATFORM LIBRARIES          │
│ OS / GPU / GUI / network / audio     │
└─────────────────────────────────────┘
```

Nguyên tắc:

> **Core định nghĩa cách Axiom hoạt động. Library định nghĩa cách Axiom được sử dụng. Platform định nghĩa cách Axiom nói chuyện với thế giới bên ngoài.**

---

# 2. Core phải cực nhỏ

Core chỉ nên chứa những thứ mà compiler cần hiểu về mặt semantic.

Tôi đề xuất Core v0.1 gồm:

```text
bool
integers
floats

struct
enum
tuple
array

Option
Result

function
closure

trait
impl
generic

view
mut_view

ownership
Copy
Drop
Send
Share
Sized

if
match
loop
return

unsafe

const
static

module
import
export

async/await semantic support
```

Không có:

```text
Vec
String
HashMap
File
Socket
ThreadPool
HTTP
JSON
GUI
```

trong Core.

---

# 3. Nhưng `Option` và `Result` nên ở đâu?

Đây là một ngoại lệ thú vị.

Về implementation, có thể nằm trong compiler intrinsic/prelude.

Về semantic model:

```text
Option<T>
Result<T,E>
```

được compiler hiểu đủ sâu để:

- exhaustiveness
- `?`
- niche optimization
- control-flow analysis

Nhưng programmer vẫn nhìn thấy chúng như **ordinary algebraic types**.

Do đó:

> `Option`/`Result` là **core-defined types**, nhưng không nhất thiết là hard-coded magic syntax ở mọi nơi.

---

# 4. Không nên tạo “primitive class”

Một sai lầm cần tránh:

```text
String
Vec
File
Socket
```

trở thành những type compiler đặc biệt.

Ví dụ không nên:

```text
if type == Vec:
    special compiler logic
```

trừ những intrinsic tối thiểu.

Thay vào đó:

```text
Vec<T>
```

là library type bình thường, compiler chỉ cung cấp optimization hooks nếu cần.

---

# 5. Intrinsic là gì?

Axiom có thể có:

```text
compiler intrinsic
```

nhưng phải rất ít.

Ví dụ:

```text
atomic_load
atomic_store
sqrt
memcpy
memset
trap
size_of<T>
align_of<T>
```

Compiler hiểu chúng vì cần map trực tiếp xuống machine/platform.

Nhưng API bề mặt có thể nằm trong library.

Ví dụ programmer viết:

```axiom
atomic.load(Ordering.Acquire)
```

thay vì gọi intrinsic trực tiếp.

---

# 6. `Vec<T>` là library type

Semantic model:

```text
Vec<T>
├── logical elements
├── length
└── capacity/storage
```

Không bắt compiler phải hiểu implementation fields cụ thể.

Có thể implementation:

```text
struct Vec<T> {
    ptr
    len
    cap
}
```

nhưng sau này có thể thay đổi.

---

# 7. `Vec<T>` và ownership

```axiom
var xs = Vec.new()

xs.push(10)
xs.push(20)
```

`xs` sở hữu elements/storage.

Khi scope kết thúc:

```text
xs
 ↓
Drop
 ↓
release storage
```

Không có GC.

---

# 8. `view` từ Vec

```axiom
let v = view(xs)
```

hoặc implicit trong call:

```axiom
sum(view(xs))
```

Nếu:

```axiom
fn sum(xs: view<i32>) -> i32
```

thì `sum` chỉ đọc.

---

# 9. Relocation safety

Đây là nơi library API phải phối hợp với compiler verifier.

Ví dụ:

```axiom
let v = view(xs)
xs.push(10)
```

Nếu `push` có khả năng relocate backing storage:

```text
ERROR
active view may become dangling
```

Nhưng:

```axiom
xs[0] = 10
```

nếu vùng element phù hợp và không relocate:

```text
OK
```

---

# 10. `reserve`

Programmer có thể chủ động:

```axiom
xs.reserve(1000)
```

trước khi tạo view.

Nhưng tôi **không muốn semantic guarantee kiểu “reserve chắc chắn không bao giờ relocate nữa”** nếu API chưa được định nghĩa.

Tốt hơn:

```text
capacity >= required
```

là semantic guarantee.

Compiler/library có thể cung cấp abstraction mạnh hơn sau.

---

# 11. `Box<T>`

`Box<T>` là abstraction:

```text
owning dynamically-stored T
```

Properties:

```text
!Copy
Drop
Sized
```

Ví dụ:

```axiom
let p = Box.new(Point { x: 1, y: 2 })
```

Nhưng compiler vẫn có quyền scalarize/eliminate allocation nếu:

```text
address not observable
storage identity not required
```

---

# 12. Stable address phải explicit

Nếu programmer cần:

```text
address must remain stable
```

thì không nên dùng một `T` bình thường.

Cần abstraction riêng, ví dụ:

```text
Stable<T>
```

hoặc một container có stable-slot semantics.

Đây là điểm rất quan trọng để không biến **mọi value thành pointer-centric**.

---

# 13. Arena

Axiom nên có:

```axiom
let arena = Arena.new()
let x = arena.alloc(Data { ... })
```

Arena:

```text
owns many allocations
```

Khi:

```text
arena.drop()
```

thì tất cả allocation thuộc arena được release theo policy của arena.

Compiler phải biết provenance để không cho:

```text
return view(x)
```

nếu view sống lâu hơn arena.

---

# 14. Pool / Slab

Không nên đưa vào Core.

Standard library:

```text
Pool<T>
Slab<T>
```

phục vụ:

- game
- server
- ECS
- networking
- realtime
- OS-like code

Đây là cách xử lý fragmentation mà không cần biến memory allocator thành language semantic.

---

# 15. String

Đây là một quyết định lớn.

Tôi đề xuất **không có một `String` duy nhất đại diện cho mọi thứ**.

Ít nhất cần phân biệt:

```text
ByteString / Bytes
Text
```

Bởi vì:

```text
bytes != Unicode text
```

---

# 16. `Bytes`

Dùng cho:

- network packet
- file binary
- serialization
- image
- audio
- crypto
- raw protocol

Semantic:

```text
Bytes = sequence of u8
```

Có thể có:

```text
view<u8>
mut_view<u8>
```

để tránh allocation.

---

# 17. `Text`

`Text` biểu diễn Unicode-valid text.

Nhưng chưa nên khóa representation:

```text
UTF-8
UTF-16
UTF-32
```

ở language core.

Stdlib có thể chọn UTF-8 làm native representation ban đầu vì phù hợp ecosystem/network/storage.

Nhưng semantic:

```text
Text = valid Unicode text
```

không phải:

```text
Text = arbitrary bytes
```

---

# 18. Không nên làm indexing String là O(1) codepoint

Nếu representation UTF-8:

```axiom
text[i]
```

rất dễ dẫn tới kỳ vọng sai.

Tôi đề xuất API rõ:

```text
bytes()
codepoints()
graphemes()
```

và không nhất thiết có:

```text
text[5]
```

cho Unicode scalar value.

---

# 19. Unicode không nên nằm trong Core

Compiler không cần biết:

```text
grapheme
locale
normalization
collation
```

Đó là stdlib/platform functionality.

Điều này giúp compiler nhỏ.

---

# 20. Collections

Standard library nên có các abstraction cơ bản:

```text
Array<T,N>       // core/primitive semantic
Vec<T>           // dynamic contiguous
Deque<T>
List<T>          // nếu thực sự cần
Map<K,V>
Set<T>
HashMap<K,V>
HashSet<T>
```

Nhưng không nhất thiết tất cả đều có trong v0.1.

Tôi ưu tiên:

```text
Vec
Map
Set
```

sau đó mở rộng.

---

# 21. Không nên có “one true collection”

C++ có rất nhiều container vì từng trường hợp có trade-off.

Axiom nên chấp nhận điều đó.

Ví dụ:

```text
Vec          contiguous
Deque        segmented/ring
HashMap      hash table
TreeMap      ordered tree
ArenaMap     arena-oriented
```

Không ép một abstraction giải quyết tất cả.

---

# 22. Iterator

Trait:

```axiom
trait Iterator {
    ...
}
```

là phù hợp.

Nhưng cần tránh thiết kế iterator quá phức tạp.

Mục tiêu:

```text
iterator abstraction
→ generic
→ monomorphized
→ zero-cost
```

Ví dụ:

```axiom
for x in xs {
    ...
}
```

có thể lower thành:

```text
index/pointer loop
```

---

# 23. Range

Nên có range abstraction:

```text
0..10
0..=10
```

và compiler/stdlib có thể optimize thành loop.

Không cần object allocation.

---

# 24. Algorithms

Các thuật toán generic:

```text
sort
find
map
filter
reduce
copy
fill
```

nằm trong stdlib.

Compiler không cần biết `sort` là gì.

Nếu generic được specialize tốt:

```text
sort<i32>
```

có thể gần như hand-written implementation.

---

# 25. File API

File là platform/std library:

```axiom
let file = File.open("data.bin")?
```

`File`:

```text
!Copy
Drop
```

Drop đóng handle/release resource theo semantics.

Nhưng:

> Drop không được dùng để xử lý recoverable close failure.

Nếu close có thể lỗi:

```axiom
file.close()?
```

có thể explicit.

Drop chỉ là fallback cleanup.

---

# 26. RAII nhưng không phải C++ object model

Đây là một điểm Axiom nên giữ rõ.

Axiom có:

```text
deterministic resource cleanup
```

nhưng không có:

```text
constructor/destructor inheritance hierarchy
virtual destructor
```

Thay vào đó:

```text
struct + init function + Drop
```

Ví dụ:

```axiom
struct File {
    ...
}

impl File {
    fn open(...) -> Result<File, Error>
}

impl Drop for File {
    fn drop(self: mut_view<File>) {
        ...
    }
}
```

Exact syntax của `Drop` vẫn có thể tinh chỉnh.

---

# 27. Mutex

Mutex là stdlib/platform abstraction.

```axiom
let lock = Mutex.new(data)
```

Access:

```text
lock.lock()
```

trả guard.

Guard:

```text
!Copy
Drop
```

Drop guard:

```text
unlock
```

Đây là một ví dụ rất hay về:

> **Drop là semantic resource release, không phải destructor magic.**

---

# 28. Atomic

Atomic phải có API rõ:

```text
Atomic<T>
```

với:

```text
load
store
swap
compare_exchange
fetch_add
...
```

và:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Compiler lower xuống hardware atomics.

Không nên có implicit atomicity.

---

# 29. Thread

Standard library:

```axiom
Thread.spawn(...)
```

Compiler xử lý:

```text
Send
ownership transfer
closure capture
```

OS/platform layer thực hiện:

```text
CreateThread
pthread_create
...
```

---

# 30. Channel

Channel là library:

```axiom
let (tx, rx) = channel<T>()
```

Send:

```text
move ownership
```

không cần copy.

Điều này rất hợp Axiom:

```text
ownership transfer
→ communication
```

---

# 31. Async

Core hiểu:

```text
async
await
```

nhưng:

```text
Executor
Runtime
Timer
IO reactor
```

là library/platform.

Có thể:

```text
Axiom program
→ own executor
```

nếu cần tối ưu đặc thù.

---

# 32. Networking

Không đưa:

```text
TCP
UDP
HTTP
WebSocket
```

vào Core.

Std/platform:

```text
Socket
TcpStream
UdpSocket
```

HTTP nằm cao hơn nữa:

```text
net/http
```

---

# 33. GUI

Hoàn toàn platform/library.

Axiom Core không biết:

```text
window
button
mouse
GPU
```

Điều này cho phép:

```text
native Windows
native macOS
native Linux
Android
iOS
Web
```

mà không làm language core phụ thuộc UI framework.

---

# 34. GPU

Tương tự.

Không nên:

```text
gpu<T>
```

trở thành Core semantic.

Thay vào đó có:

```text
gpu/
├── vulkan
├── metal
├── d3d12
├── webgpu
└── cuda
```

hoặc abstraction cao hơn.

---

# 35. Standard Library không nên là monolith

Thay vì:

```text
std
```

một binary khổng lồ, conceptual module:

```text
std.core
std.mem
std.collections
std.text
std.io
std.fs
std.sync
std.thread
std.async
std.net
std.crypto
...
```

Compiler/linker chỉ lấy phần cần thiết.

---

# 36. Prelude

Một vấn đề cần xử lý là usability.

Nếu bắt programmer viết:

```axiom
import std.core.Option
import std.core.Result
import std.collections.Vec
...
```

mọi lúc thì rất phiền.

Tôi đề xuất:

```text
prelude
```

rất nhỏ.

Ví dụ tự động có:

```text
Option
Result
Some
None
Ok
Err
view
mut_view
basic traits
```

Không tự động import:

```text
File
Socket
Thread
HashMap
```

---

# 37. Core Prelude phải deterministic

Không có magic:

```text
compiler decides what is visible based on context
```

Prelude là một module/import set cố định theo language version.

---

# 38. `std` không được định nghĩa semantics mới

Ví dụ stdlib không được nói:

> `Vec` có một loại ownership đặc biệt mà compiler phải hiểu.

Thay vào đó compiler cung cấp primitives:

```text
ownership
Drop
view
regions
effects
allocation
```

`Vec` xây trên chúng.

---

# 39. Platform abstraction

Tôi đề xuất cấu trúc:

```text
std
 │
 ├── portable API
 │
 └── platform implementation
         ├── windows
         ├── linux
         ├── macos
         ├── android
         ├── ios
         └── wasm
```

API semantics thống nhất ở trên.

Platform implementation thay đổi bên dưới.

---

# 40. Syscall

Có thể có tầng:

```text
std.platform
```

và:

```text
platform.linux
platform.windows
```

cho programmer cần low-level.

Không cần ép tất cả đi qua abstraction cao.

Ví dụ systems programmer có thể gọi syscall abstraction trực tiếp trong unsafe/system module.

---

# 41. `unsafe` boundary

Một thiết kế tôi đánh giá rất phù hợp:

```text
safe std API
      ↓
unsafe platform implementation
      ↓
OS / hardware
```

Programmer bình thường chỉ thấy:

```text
File.read()
```

Systems programmer có thể xuống:

```text
unsafe platform::syscall(...)
```

---

# 42. Đây cũng giải quyết vấn đề “pointer quá phiền”

Code bình thường:

```axiom
let data = file.read_all()?
process(data)
```

Không cần:

```text
*T
&'a T
&mut T
lifetime annotations
manual free
```

Nhưng low-level vẫn có:

```axiom
unsafe {
    let p: *mut u8 = ...
}
```

Tức là:

> **Pointer không bị loại khỏi Axiom; pointer bị đẩy về đúng nơi nó thực sự cần thiết.**

---

# 43. Core API boundary

Tôi đề xuất một quy tắc rất mạnh:

> Một tính năng chỉ được đưa vào Core nếu compiler cần biết nó để bảo đảm semantic correctness hoặc generate efficient machine code.

Nếu không:

```text
→ library
```

Ví dụ:

| Tính năng | Core? |
|---|---:|
| ownership | ✅ |
| Drop | ✅ |
| trait | ✅ |
| generic | ✅ |
| view | ✅ |
| atomic semantics | ✅ |
| Vec | ❌ |
| String | ❌ |
| HashMap | ❌ |
| File | ❌ |
| HTTP | ❌ |
| GUI | ❌ |
| JSON | ❌ |
| GPU API | ❌ |
| regex | ❌ |

---

# 44. Nhưng đừng cực đoan “mọi thứ phải là library”

Compiler vẫn nên có intrinsic cho những thứ mà nếu không có compiler support sẽ:

- không thể đảm bảo semantics
- hoặc mất khả năng optimize tốt.

Ví dụ:

```text
size_of<T>()
align_of<T>()
atomic operations
trap
volatile
SIMD intrinsics
type metadata compile-time
```

Nhưng surface API vẫn có thể được cung cấp bởi stdlib.

---

# 45. Core/Std/Platform invariant

Tôi đề xuất khóa:

### ALIB-01
Core contains semantic necessities, not general-purpose APIs.

### ALIB-02
Standard library cannot redefine core semantics.

### ALIB-03
Platform APIs remain outside language core.

### ALIB-04
Unused library components must not impose mandatory runtime cost.

### ALIB-05
Core types must not require heap allocation.

### ALIB-06
Library abstractions should permit zero-cost specialization.

### ALIB-07
Unsafe platform functionality remains explicitly marked.

### ALIB-08
Portable APIs must not assume a particular OS.

### ALIB-09
Runtime dependencies are capability-driven.

### ALIB-10
Prelude remains small and deterministic.

### ALIB-11
Resource-owning library types use deterministic Drop.

### ALIB-12
Recoverable resource errors are explicit, not silently propagated by Drop.

---

# 46. Một thay đổi kiến trúc đáng giá

Đến đây tôi nghĩ Axiom không nên có khái niệm đơn giản là:

```text
Core
Std
```

mà nên có **4 tầng**:

```text
┌──────────────────────────┐
│ Language Core             │
│ semantic rules            │
├──────────────────────────┤
│ Core Library              │
│ Option Result Array       │
│ basic traits              │
├──────────────────────────┤
│ Standard Library          │
│ Vec Map Text IO Sync      │
├──────────────────────────┤
│ Platform / Ecosystem      │
│ OS GPU GUI HTTP DB ...    │
└──────────────────────────┘
```

Trong đó **Core Library** là lớp rất nhỏ, portable, có thể gần như luôn có nhưng không phải compiler semantic core.

Điều này giúp tránh hai thái cực:

```text
C:
Core quá thấp
→ programmer tự xây mọi thứ
```

và:

```text
C++/Java:
language/runtime quá lớn
→ mọi thứ dính vào nhau
```

Axiom nằm ở giữa:

```text
small semantic core
+
powerful generic library
+
thin platform boundary
```

---

## Bước tiếp theo tôi đề xuất

Bây giờ nền móng đã khá đầy đủ. Tôi sẽ không tiếp tục thêm API nữa.

Điểm có giá trị nhất tiếp theo là **AXIOM CONCURRENCY + ASYNC thực thi thực tế**, cụ thể hóa từ semantic model hiện tại thành:

```text
Thread
  ↓
Task
  ↓
Executor
  ↓
Future/State Machine
  ↓
Await
  ↓
Cancellation
  ↓
Channel
  ↓
Mutex/Atomic
  ↓
OS scheduling
```

và quan trọng nhất: **làm thế nào compiler có thể tự quản lý ownership/lifetime/concurrency mà programmer không phải viết borrow/lifetime syntax**, nhưng vẫn đạt data-race freedom và không biến compiler thành một “Rust borrow checker phiên bản khác tên”.