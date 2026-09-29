Tiếp tục. Phần này rất quan trọng vì nó quyết định Axiom có thực sự đạt được mục tiêu **“high-level nhưng binary/native runtime tối thiểu”** hay cuối cùng lại biến thành một ngôn ngữ luôn phải kéo theo runtime lớn.

# RUNTIME-001 — Core / Runtime / Std / OS Boundary

## 1. Nguyên tắc nền tảng

Tôi đề xuất chốt một nguyên tắc:

> **Axiom không có “runtime mặc định”; Axiom có các runtime capability tùy chương trình sử dụng.**

Tức là không phải:

```text
Axiom program
    ↓
Axiom Runtime 20 MB
    ↓
application
```

mà:

```text
Axiom program
    ↓
compiler phân tích capability
    ↓
chỉ link những thành phần cần thiết
```

Ví dụ:

```text
return 42
```

có thể chỉ cần:

```text
startup
main
exit
```

Trong khi:

```text
Thread.spawn(...)
```

mới kéo:

```text
thread support
TLS
scheduler primitives
```

và:

```text
async fn
```

không tự động kéo executor.

---

# 2. Chia thành 4 tầng

Tôi đề xuất kiến trúc:

```text
┌─────────────────────────────┐
│       Application            │
├─────────────────────────────┤
│       Standard Library       │
├─────────────────────────────┤
│       Core / Runtime         │
├─────────────────────────────┤
│       OS / Platform ABI      │
└─────────────────────────────┘
```

Nhưng cần hiểu chính xác từng tầng.

---

# 3. Axiom Core

`Core` phải cực nhỏ.

Nó chứa những thứ **gắn với semantics của ngôn ngữ**, không phải tiện ích hệ điều hành.

Ví dụ:

```text
bool
integers
float
array
tuple
struct
enum
Option
Result
view
mut_view
Copy
Move
Drop
Send
Share
traits
generic
closures
comptime
match
```

Core **không chứa**:

```text
File
Socket
Thread
Mutex
TCP
HTTP
GUI
GPU driver
filesystem
```

---

# 4. Core không phải runtime

Ví dụ:

```text
Option<T>
```

không cần runtime.

Compiler biến:

```text
Option<i32>
```

thành representation thích hợp.

Có thể:

```text
enum Option<T> {
    None,
    Some(T)
}
```

sau optimization có thể trở thành:

```text
i32 + discriminant
```

hoặc niche representation.

Không cần:

```text
libaxiom_runtime.so
```

chỉ vì dùng `Option`.

---

# 5. Runtime capability

Runtime nên được chia thành các capability độc lập.

Ví dụ:

```text
runtime/
├── startup
├── alloc
├── panic
├── unwind
├── thread
├── tls
├── async
├── io
├── time
├── atomics
└── reflection
```

Không có chuyện:

```text
import Thread
```

→ linker phải kéo toàn bộ runtime.

Compiler/linker chỉ link phần thực sự được tham chiếu.

---

# 6. Startup runtime

Đây là phần đặc biệt.

Một native executable thường không thực sự bắt đầu trực tiếp ở:

```text
fn main()
```

OS gọi entry point:

```text
_start
```

hoặc PE equivalent.

Axiom cần có các startup profile.

### Freestanding

```text
_start
   ↓
Axiom main
```

Gần như không có runtime.

### Hosted Linux

```text
ELF entry
   ↓
Axiom startup
   ↓
initialize required runtime
   ↓
main
   ↓
exit
```

### Windows

```text
PE entry
   ↓
Axiom startup
   ↓
main
```

### WASM

```text
WASM module
   ↓
exported function
```

Không nên ép mọi target vào một startup model.

---

# 7. `main` không nên là một magic runtime object

Axiom có thể định nghĩa:

```text
fn main() -> i32
```

và compiler hiểu đây là program entry.

Nhưng semantics chỉ là:

```text
program entry
program return value
```

Compiler/target driver mới tạo startup phù hợp.

Như vậy:

```text
main()
```

không kéo theo một `Application` object khổng lồ.

---

# 8. Panic

Panic nên là capability.

Ví dụ:

```text
panic("bad state")
```

có thể compile thành:

```text
call axiom_panic
```

Nhưng nếu chương trình không có panic path:

```text
panic support
```

có thể bị loại khỏi binary.

Có các profile:

```text
panic = abort
panic = unwind
```

`abort` là profile tối giản.

---

# 9. Không có exception runtime mặc định

Axiom không nên có mô hình:

```text
try
catch
throw
```

làm nền tảng.

Recoverable failure:

```text
Result<T, E>
```

Fatal failure:

```text
panic
```

Do đó một chương trình chỉ dùng `Result` không cần exception/unwind machinery.

---

# 10. Allocation

Đây là nơi Axiom có thể khác rất mạnh so với nhiều ngôn ngữ hiện đại.

Không có:

```text
new
delete
```

trong Core.

Thay vào đó:

```text
Box<T>
Vec<T>
String
Buffer
Arena
Pool
```

là library abstractions.

Ví dụ chương trình:

```text
fn main() {
    let x = 123;
}
```

không có allocator.

Ngay cả:

```text
struct Foo { ... }
```

cũng không có allocator.

---

# 11. `Box<T>` và runtime

Như đã chốt:

> `Box<T>` biểu diễn **owned dynamic storage semantics**, không nhất thiết physical heap allocation sau optimization.

Ví dụ:

```text
fn make() -> Box<Foo> {
    Box::new(Foo(...))
}
```

Compiler có thể thấy:

```text
Box
 ↓
returned
 ↓
address escapes
```

→ dynamic storage thực sự cần thiết.

Nhưng:

```text
fn f() {
    let x = Box::new(Foo(...));
    use(x);
}
```

nếu không expose address/stable storage:

```text
Box
 ↓
escape analysis
 ↓
scalarize / stack / register
```

có thể loại allocation.

---

# 12. Standard Library

Std nên là:

> **library, không phải language runtime.**

Ví dụ:

```text
std::collections
std::string
std::io
std::fs
std::net
std::sync
std::thread
std::async
std::time
std::os
```

Mỗi module có thể kéo dependency riêng.

---

# 13. `std` phải được xây trên capability

Ví dụ:

```text
std::thread
```

phụ thuộc:

```text
OS thread API
TLS
atomic
synchronization
```

Trong khi:

```text
std::collections::Vec
```

chỉ phụ thuộc:

```text
allocator abstraction
```

Nếu chương trình chỉ dùng:

```text
Vec
```

không được link:

```text
thread runtime
async runtime
network runtime
```

---

# 14. OS layer

Tầng thấp nhất của standard ecosystem:

```text
axiom::os
```

hoặc:

```text
platform/
```

Nó ánh xạ:

```text
Axiom API
   ↓
OS ABI
```

Ví dụ Linux:

```text
std::fs::open()
    ↓
Linux syscall / libc ABI
```

Windows:

```text
std::fs::open()
    ↓
Win32 / NT API
```

macOS:

```text
    ↓
Darwin API
```

Axiom Core không biết các thứ này.

---

# 15. Có nên phụ thuộc libc?

**Không bắt buộc.**

Axiom cần hỗ trợ hai mode.

### libc/OS hosted

```text
Axiom
 ↓
libc
 ↓
OS
```

### Native direct

```text
Axiom
 ↓
OS ABI/syscall
```

Điều này rất quan trọng cho mục tiêu:

- freestanding
- tiny binaries
- kernel
- embedded
- custom runtime
- game engine
- bootloader

---

# 16. Nhưng không nên cố bỏ libc ở mọi nơi

Đây là điểm cần cân bằng.

Không nên biến:

> “Không phụ thuộc third-party compiler/runtime”

thành:

> “Không được dùng OS-provided libraries”.

Hai thứ hoàn toàn khác nhau.

Ví dụ Windows API:

```text
kernel32
ntdll
```

là một phần của OS ecosystem.

Linux:

```text
libc
```

có thể là lựa chọn hợp lý trong hosted profile.

Axiom chỉ cần **không bắt buộc compiler của bên thứ ba**.

---

# 17. Runtime dependency graph

Compiler/linker nên xây dependency graph.

Ví dụ:

```text
main
 │
 ├── Vec
 │    └── allocator
 │
 └── print
      └── stdout
           └── OS
```

Không có:

```text
thread
async
TLS
network
```

→ không link.

Một chương trình khác:

```text
main
 └── spawn
      ├── thread
      ├── TLS
      └── synchronization
```

thì dependency graph tự mở rộng.

---

# 18. Đây là nơi linker và compiler phối hợp

Compiler nên phát sinh metadata capability:

```text
Object:
    requires:
        OS.stdout
        Runtime.alloc
```

Linker resolve:

```text
requires Runtime.alloc
```

→ tìm implementation.

Nếu không dùng:

```text
Runtime.async
```

thì không đưa vào executable.

---

# 19. Runtime ABI phải cực kỳ ổn định

Runtime functions như:

```text
axiom_alloc
axiom_dealloc
axiom_panic
axiom_thread_spawn
```

nên có ABI rõ ràng.

Nhưng không nhất thiết public.

Có thể:

```text
internal runtime ABI
```

được compiler biết.

Điều này cho phép compiler optimize trực tiếp.

---

# 20. Không nên biến runtime API thành magic intrinsic quá nhiều

Ví dụ không nên có hàng nghìn:

```text
@compiler_magic
```

vì sau này self-hosting sẽ rất khó.

Chỉ những thứ thực sự cần compiler integration mới là intrinsic.

Ví dụ:

```text
atomic
SIMD
CPU intrinsic
comptime
type reflection
```

Còn:

```text
Vec
String
HashMap
Mutex
Arc
```

nên viết bằng Axiom.

---

# 21. Đây là một mục tiêu rất quan trọng

Tôi đề xuất:

> **Stdlib phải là một trong những client lớn nhất của compiler, không phải phần mở rộng bí mật của compiler.**

Nếu compiler chỉ có thể implement `Vec` bằng magic compiler intrinsic, thì language design chưa đủ tốt.

Lý tưởng:

```text
compiler
   ↓
Core
   ↓
Std
```

và:

```text
Std
```

phần lớn được viết bằng Axiom.

---

# 22. Một chương trình tối giản

Ví dụ:

```text
fn main() {
}
```

Axiom không nên mặc định kéo:

```text
allocator
thread
async
unicode
network
filesystem
panic
reflection
```

Binary lý tưởng:

```text
entry
main
exit
```

Target-specific overhead vẫn tồn tại, nhưng đó là overhead của executable format/OS ABI chứ không phải Axiom runtime bắt buộc.

---

# 23. Một chương trình không heap

Ví dụ:

```text
fn main() -> i32 {
    var x: i64 = 10;
    var y: i64 = 20;
    return x + y;
}
```

Có thể compile gần như:

```asm
mov eax, 30
ret
```

tùy ABI/startup.

Không allocator.

Không GC.

Không RC.

Không runtime object.

---

# 24. Một chương trình dùng Vec

```text
fn main() {
    var values = Vec<i32>();
    values.push(10);
    values.push(20);
}
```

Lúc này mới cần:

```text
Vec
 ↓
allocator
```

Nếu optimizer chứng minh allocation không cần thiết, có thể loại bỏ.

---

# 25. Một chương trình dùng Arc

```text
let x = Arc.new(data);
```

dependency:

```text
Arc
 ↓
atomic
 ↓
allocator
```

Nếu:

```text
Arc
```

không escape và compiler có thể chứng minh single-owner equivalent thì **không được tự ý biến thành `Box` nếu điều đó thay đổi observable semantics**.

Nhưng có thể loại bỏ/refactor overhead nếu semantics vẫn tương đương.

---

# 26. Một chương trình dùng async

```text
async fn fetch() -> Result<Data, Error>
```

**Không tự động có executor.**

Chỉ tạo:

```text
Future
```

Muốn chạy:

```text
executor.spawn(fetch())
```

mới kéo executor.

Đây là điểm rất quan trọng.

Nếu:

```text
async fn
```

được gọi nhưng Future chỉ được poll thủ công:

```text
future.poll(...)
```

không cần một global runtime.

---

# 27. Thread cũng vậy

```text
Thread.spawn(...)
```

mới kéo thread support.

Không có:

```text
Axiom runtime starts 8 worker threads
```

khi chương trình không sử dụng concurrency.

---

# 28. Reflection

Runtime reflection **không phải mặc định**.

Compile-time reflection:

```text
comptime
```

không cần runtime metadata.

Nếu chương trình muốn:

```text
type_name(x)
enumerate_fields(x)
```

ở runtime thì phải explicit opt-in:

```text
@runtime_reflection
```

và khi đó compiler/linker mới giữ metadata.

---

# 29. Unicode

Không nên nhét Unicode runtime vào Core.

Có:

```text
String
```

là representation/data abstraction.

Nhưng:

```text
Unicode normalization
grapheme segmentation
locale
collation
```

là stdlib.

Như vậy chương trình embedded có thể chỉ dùng UTF-8 bytes mà không kéo cả Unicode database.

---

# 30. Memory allocator architecture

Allocator nên có interface:

```text
trait Allocator {
    fn alloc(...)
    fn dealloc(...)
    fn realloc(...)
}
```

Nhưng **không đưa allocator type vào mọi collection generic mặc định**.

Tức là tránh:

```text
Vec<T, A>
```

trở thành API phổ biến.

Mặc định:

```text
Vec<T>
```

và compiler/library chọn allocator policy.

Khi cần:

```text
Arena
Pool
CustomAllocator
```

thì explicit.

Điều này phù hợp với nguyên tắc trước:

> Allocation strategy không phải ordinary type semantics.

---

# 31. Resource lifetime và memory lifetime vẫn tách biệt

Ví dụ:

```text
File
```

Drop:

```text
close file handle
```

không có nghĩa:

```text
free memory
```

Tương tự:

```text
MutexGuard.drop()
```

có thể:

```text
unlock
```

nhưng không deallocate Mutex.

Đây là lý do rất đúng khi chúng ta đã tách:

```text
Value lifetime
Resource lifetime
Memory lifetime
```

---

# 32. Runtime ABI categories

Tôi đề xuất phân loại:

```text
RUNTIME ABI
├── Memory ABI
├── Panic ABI
├── Unwind ABI
├── Thread ABI
├── TLS ABI
├── Async ABI
├── Atomic ABI
├── IO ABI
└── Reflection ABI
```

Mỗi cái độc lập.

---

# 33. Runtime profile

Axiom build nên có profile.

### `freestanding`

```text
no OS
no allocator
no thread
no async
no std
```

### `minimal`

```text
OS
startup
basic panic
```

### `hosted`

```text
OS
std
filesystem
io
```

### `server`

```text
hosted
network
thread
async
```

### `embedded`

```text
freestanding
custom allocator
device memory
interrupt
```

### `gpu`

```text
device runtime
kernel support
```

Không phải compiler tạo các profile này bằng magic. Đây chủ yếu là **dependency policies**.

---

# 34. Một điểm tôi muốn bổ sung vào specification

## ARUNTIME-20 — No Mandatory Runtime

Một chương trình Axiom hợp lệ không yêu cầu runtime ngoài những thành phần mà semantics/target của chương trình thực sự cần.

## ARUNTIME-21 — Capability-Driven Runtime

Runtime components được link theo dependency thực tế.

## ARUNTIME-22 — Core Is Runtime-Independent

Core language semantics không phụ thuộc vào monolithic runtime.

## ARUNTIME-23 — Standard Library Is Not Language Semantics

Stdlib APIs không phải compiler primitive trừ những phần được specification đánh dấu rõ.

## ARUNTIME-24 — Runtime Components Are Independently Linkable

Runtime components phải có boundary rõ ràng để linker loại bỏ phần không sử dụng.

## ARUNTIME-25 — Allocation Is Optional

Chương trình Axiom hợp lệ có thể không có dynamic allocation.

## ARUNTIME-26 — Threading Is Optional

Không dùng thread thì không cần thread runtime.

## ARUNTIME-27 — Async Execution Is Optional

`async` không tự tạo executor.

## ARUNTIME-28 — Reflection Is Optional

Runtime reflection không tồn tại nếu không explicit opt-in.

## ARUNTIME-29 — Panic/Unwind Are Profile Dependent

Chương trình có thể chọn abort hoặc unwind.

## ARUNTIME-30 — Hosted and Freestanding Are First-Class

Compiler không giả định mọi chương trình đều chạy dưới một OS hosted runtime.

## ARUNTIME-31 — OS Boundary Is Explicit

OS API không thuộc Core.

## ARUNTIME-32 — Runtime ABI Is Stable

Runtime/compiler boundary phải có ABI rõ ràng.

## ARUNTIME-33 — Stdlib Uses Axiom Semantics

Phần lớn stdlib phải có thể viết bằng Axiom mà không cần compiler magic.

## ARUNTIME-34 — Runtime Dependency Is Observable Only Through Required Semantics

Compiler không được thêm runtime component chỉ vì tiện implementation nếu component đó không cần thiết.

---

# 35. Kiến trúc hoàn chỉnh hiện tại

Axiom hiện đã có thể nhìn thành:

```text
                     AXIOM LANGUAGE
                           │
            ┌──────────────┴──────────────┐
            │                             │
         SEMANTICS                    COMPTIME
            │                             │
            └──────────────┬──────────────┘
                           ↓
                         MIR
                           ↓
                         LIR
                           ↓
                    MACHINE BACKEND
                           ↓
                         OBJECT
                           ↓
                        LINKER
                           ↓
                     EXECUTABLE
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
        CORE           RUNTIME             STD
                           │
                           ↓
                         OS ABI
```

Và điểm quan trọng nhất:

```text
                    ┌─────────────┐
                    │ Axiom Core  │
                    └──────┬──────┘
                           │
                     no runtime
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
       allocator         thread           async
          │                │                │
       optional         optional         optional
```

Đây là kiến trúc rất phù hợp với mục tiêu ban đầu của bạn: **ngôn ngữ mạnh nhưng không bắt người dùng trả “thuế runtime” cho những tính năng họ không dùng.**

---

## Bước tiếp theo: `OS-ABI-001`

Bây giờ phần còn thiếu để biến thiết kế này thành một hệ thống thực sự là **OS/Platform Layer**.

Tôi sẽ đi tiếp vào:

```text
OS-ABI-001
├── Linux syscall/ABI
├── Windows PE/Win32/NT
├── macOS/Darwin
├── iOS
├── Android/Bionic
├── WASM
├── UEFI
├── bare-metal
├── TLS
├── process
├── virtual memory
├── file/socket IO
├── clocks
├── signals/exceptions
├── dynamic libraries
└── platform abstraction
```

và đặc biệt sẽ chốt **Axiom có nên gọi trực tiếp syscall hay thông qua libc/Bionic/Win32 mặc định**, vì quyết định này ảnh hưởng trực tiếp tới **binary size, portability, ABI stability và hiệu năng**.