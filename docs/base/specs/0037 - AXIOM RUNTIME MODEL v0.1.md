Tiếp tục với **AXIOM RUNTIME MODEL v0.1**. Đây là chỗ cần đặc biệt cẩn thận, vì nếu thiết kế sai thì toàn bộ mục tiêu “native, nhỏ, không runtime bắt buộc” sẽ bị phá.

# AXIOM RUNTIME MODEL v0.1

## 1. Quyết định nền tảng

Tôi đề xuất Axiom **không có một “runtime” duy nhất**.

Thay vào đó:

```text id="j4h3c8"
Axiom Program
     │
     ├── Core machine code
     │
     ├── Optional Runtime Components
     │      ├── allocator
     │      ├── threads
     │      ├── async
     │      ├── panic
     │      ├── reflection
     │      ├── unicode
     │      └── ...
     │
     └── OS / Platform ABI
```

Hay nói ngắn:

> **Runtime là tập hợp các capability được link khi cần, không phải một cục bắt buộc.**

---

# 2. Chương trình tối thiểu

Axiom phải có khả năng compile một chương trình kiểu:

```axiom
fn main() {
}
```

thành binary mà không cần:

```text
GC
allocator
thread runtime
async runtime
reflection
exception runtime
```

Thậm chí:

```text
main
  ↓
OS entry
  ↓
return
```

là đủ.

---

# 3. Startup

Trên native target:

```text id="9t7m4e"
OS
 ↓
_process_start
 ↓
Axiom startup
 ↓
main()
 ↓
exit
```

Nhưng startup phải cực mỏng.

Ví dụ Linux có thể cần:

```text id="q3n8d5"
_ELF entry
    ↓
parse argc/argv
    ↓
initialize minimal process state
    ↓
main
    ↓
exit syscall
```

Không cần:

```text id="4c6m9r"
runtime initialization framework
```

nếu program không yêu cầu.

---

# 4. `main` không nên bị đóng cứng quá sớm

Có thể hỗ trợ:

```axiom
fn main() {
}
```

và:

```axiom
fn main(args: Args) -> i32 {
    ...
}
```

hoặc:

```axiom
fn main() -> Result<(), Error> {
    ...
}
```

Compiler tạo startup adapter.

Semantic:

```text id="p3q5s1"
OS entry
    ↓
Axiom main signature
```

Startup layer chuyển đổi ABI.

---

# 5. Exit semantics

Tôi đề xuất:

```text id="3x8k2m"
main returns i32
    ↓
process exit(code)
```

Nếu:

```axiom
fn main() {
}
```

thì:

```text id="m1p4c7"
exit(0)
```

Nếu:

```axiom
fn main() -> Result<(), Error>
```

thì runtime/application policy quyết định mapping error → exit code.

Core không cần một exception runtime.

---

# 6. Không có hidden runtime initialization

Đây là một invariant rất quan trọng.

Không được tự động:

```text id="1c7g5n"
program start
  ↓
initialize GC
  ↓
initialize thread pool
  ↓
initialize reflection
  ↓
initialize logging
  ↓
initialize allocator
  ↓
main
```

Thay vào đó:

```text id="9b0f2k"
program start
  ↓
minimum required initialization
  ↓
main
```

---

# 7. Runtime Components

Tôi đề xuất chia runtime thành modules:

```text id="w7g3n2"
runtime/
├── startup
├── process
├── allocator
├── panic
├── threads
├── sync
├── async
├── atomics
├── tls
├── io
├── unicode
├── reflection
└── diagnostics
```

Nhưng nhiều cái thực chất có thể là library + intrinsic, không phải runtime.

---

# 8. Core Runtime ≈ gần bằng 0

Một chương trình:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

không cần runtime.

Nếu executable cần entry point:

```text id="f2r6j8"
startup + OS ABI glue
```

là đủ.

---

# 9. Allocator chỉ link khi cần

Ví dụ:

```axiom
fn main() {
    let x = 1
}
```

không cần allocator.

Nếu:

```axiom
fn main() {
    let x = Box.new(123)
}
```

thì cần allocation capability.

Nhưng:

```text id="w1q4d6"
Box.new(123)
```

vẫn có thể được compiler optimize thành:

```text id="a8s2f0"
local/register
```

nếu address không observable.

Nếu allocation thực sự cần:

```text id="q5v8c1"
link allocator component
```

---

# 10. Runtime dependency graph

Thay vì:

```text id="l6m2x7"
program → runtime
```

nên là:

```text id="4k8y2p"
Program
  │
  ├── uses Box
  │      ↓
  │   allocator
  │
  ├── uses Mutex
  │      ↓
  │   sync
  │
  ├── uses async
  │      ↓
  │   executor
  │
  └── uses Text
         ↓
      unicode
```

Compiler/linker có thể resolve dependency graph.

---

# 11. Không nên ép mọi runtime component static-link

Nếu program dùng:

```text id="x1f5z8"
libc
```

có thể link dynamic tùy target/profile.

Nhưng Axiom compiler phải có khả năng tạo:

```text id="6j3c9v"
fully static/native binary
```

nếu platform cho phép và programmer yêu cầu.

---

# 12. “Không phụ thuộc compiler bên thứ ba”

Cần phân biệt hai giai đoạn.

### Bootstrap

Có thể dùng:

```text id="q7b2n8"
LLVM
system assembler
system linker
```

hoặc các tool khác để xây compiler đầu tiên.

### Final Axiom toolchain

Phải có:

```text id="w8k4p2"
Axiom compiler
├── parser
├── semantic analyzer
├── optimizer
├── Axiom LIR
├── machine encoder
├── object writer
└── executable writer
```

Không cần LLVM để define/compile semantics.

---

# 13. Object writer

Đây là một thành phần tôi nghĩ Axiom nên tự sở hữu.

Compiler có thể sinh:

```text id="7m0v5r"
ELF
PE/COFF
Mach-O
WASM
```

thay vì bắt buộc:

```text id="3h8q1n"
source → LLVM → clang → linker
```

Tuy nhiên:

> **Không nhất thiết phải tự viết linker ngay từ ngày đầu.**

Đây là implementation roadmap, không phải language semantics.

---

# 14. Linker independence

Final toolchain lý tưởng:

```text id="2n4v6s"
Axiom Compiler
      ↓
Object Writer
      ↓
Axiom Linker
      ↓
Executable
```

Nhưng bootstrap có thể:

```text id="c8j1p0"
Axiom Compiler
      ↓
ELF/COFF/Mach-O object
      ↓
system linker
```

Sau khi compiler ổn định mới tự-host linker.

---

# 15. Runtime ABI

Axiom cần một ABI nội bộ:

```text id="v7f2c4"
@abi(axiom)
```

và external:

```text id="m2k6q9"
@abi(C)
@abi(system)
```

Runtime components giao tiếp qua ABI rõ ràng.

Không được phụ thuộc vào:

```text id="a0x4s6"
C++ ABI
```

trong core runtime.

---

# 16. Panic runtime

Panic là optional component.

Có thể compile:

```text id="n5p3j8"
--panic=abort
```

thành:

```text id="2k9v1c"
panic
 ↓
minimal diagnostic
 ↓
exit/trap
```

Hoặc:

```text id="7g4w0n"
--panic=unwind
```

thì cần:

```text id="q1x8d3"
unwind machinery
cleanup
stack metadata
```

---

# 17. Không nên có exception runtime

Core vẫn:

```text id="a5r2z8"
Result
Option
panic
trap
```

Không có:

```text id="y9m4v2"
try/catch/throw
```

Nếu sau này library muốn có exception-like abstraction, nó phải nằm ngoài semantic core.

---

# 18. Panic payload

Panic có thể:

```text id="k8v3p5"
panic(message)
panic(value)
```

nhưng không nên bắt buộc runtime phải có string formatting.

Ví dụ embedded:

```text id="w6c2n1"
--panic=trap
```

có thể bỏ message.

Đây là profile/target policy.

---

# 19. Assertions

```axiom
assert(x > 0)
```

là semantic.

Compiler có thể:

```text id="x0p7m4"
if proven true
    eliminate
else
    keep check
```

`debug_assert`:

```text id="s2d6y8"
profile-controlled
```

Nếu release profile disable:

```text id="v5n1r7"
debug_assert
→ eliminated
```

---

# 20. Thread runtime

Một chương trình không dùng thread:

```text id="j7c3m2"
không link thread runtime
```

Nếu:

```axiom
spawn(worker)
```

thì cần:

```text id="p4k8q1"
thread abstraction
scheduler/OS adapter
```

Tùy API.

---

# 21. OS threads vs Axiom tasks

Axiom không nên bắt runtime phải có thread pool.

Library có thể cung cấp:

```text id="z8m2k5"
Thread.spawn
```

và:

```text id="f6r1n9"
Executor.spawn
```

Hai abstraction khác nhau.

---

# 22. Async runtime

`async fn` bản thân **không cần executor** để compile.

Compiler chỉ tạo:

```text id="t4j8q6"
state machine
```

Executor là library/runtime.

Ví dụ:

```text id="k0n3v7"
async function
    ↓
Future/Task state machine
```

sau đó:

```text id="r2m5x8"
executor.run(task)
```

Nếu program tự viết executor:

```text id="u9c4a1"
không cần Axiom async runtime mặc định
```

Đây là một điểm rất mạnh.

---

# 23. Embedded target

Ví dụ:

```axiom
fn main() {
    unsafe {
        write_register(...)
    }
}
```

Có thể compile mà không cần:

```text id="b8q1s4"
OS
allocator
threads
filesystem
network
```

Binary có thể rất nhỏ.

---

# 24. Freestanding profile

Tôi đề xuất compiler có profile:

```text id="7c4m2p"
--target-profile=freestanding
```

hoặc attribute tương đương.

Nó có:

```text id="z1r6x8"
no OS assumptions
no default runtime
no default allocator
no default threading
```

Phù hợp:

- embedded
- kernel
- bootloader
- firmware
- game console low-level
- WASM environments đặc biệt

---

# 25. Hosted profile

Normal desktop:

```text id="n5v2q8"
--target-profile=hosted
```

có thể dùng:

```text id="4x7m1p"
OS
filesystem
threads
network
allocator
locale/unicode
```

nhưng vẫn **on demand**.

---

# 26. Runtime capability linking

Đây là mô hình tôi thích nhất:

```text id="g6p2x9"
Program capabilities
        ↓
Dependency analysis
        ↓
Runtime components
        ↓
Link
```

Ví dụ:

```text id="8k3r5v"
main()
 ├── Vec
 ├── String
 └── print
```

Dependency:

```text id="1m7q4s"
Vec → allocator
String → unicode(optional)
print → stdout
```

Binary không có:

```text id="z4n8c2"
async
thread
reflection
GC
```

---

# 27. Nhưng compiler phải tránh “dependency explosion”

Ví dụ:

```axiom
Vec<i32>
```

không nên kéo theo:

```text id="n0w3k7"
network
filesystem
unicode
reflection
async
```

Do đó standard library phải chia module nhỏ.

Không nên có:

```text id="p6r2m9"
libaxiom_runtime.so
```

chứa mọi thứ.

---

# 28. Standard library ≠ runtime

Đây là distinction cần khóa:

```text id="3x8c6v"
Language Core
    ≠
Runtime
    ≠
Standard Library
```

### Core

```text
types
semantics
ownership
traits
generics
control flow
```

### Runtime

```text
startup
panic
threading glue
async executor
allocator glue
```

### Standard library

```text
Vec
String
Map
File
Socket
Mutex
Channel
JSON
HTTP
...
```

Nhiều stdlib component có thể **không cần runtime riêng**.

---

# 29. `Vec` không nhất thiết cần runtime

Ví dụ compiler có thể inline allocator call:

```text id="9k2w5x"
Vec.push
    ↓
Allocator.allocate
```

Nếu allocator là static generic:

```text id="f7n1m3"
monomorphize
```

thì code cuối cùng có thể chỉ là:

```text id="c4v8q2"
few machine instructions
```

Không cần “Vec runtime”.

---

# 30. Generics và runtime size

Đây cũng là lý do ta chọn monomorphization.

```axiom
fn sum<T: Add>(a: T, b: T) -> T
```

sau specialize:

```text id="k8m4v1"
sum<i32>
sum<f64>
sum<Vec2>
```

Compiler biết concrete type.

Không cần:

```text id="p3x9q6"
runtime type metadata
```

trừ khi dynamic dispatch được yêu cầu.

---

# 31. Reflection phải optional

Compile-time reflection:

```text id="r5m2k8"
type_info<T>()
```

có thể được compiler evaluate.

Runtime reflection:

```text id="j3q7n1"
inspect_type_at_runtime()
```

không được mặc định.

Nếu program không dùng:

```text id="z8v4c0"
no metadata
```

Binary nhỏ.

---

# 32. Debug info không phải runtime

Debug build có:

```text id="a6k1p9"
DWARF
PDB
source maps
```

nhưng release binary không cần.

Debug metadata nằm ngoài executable hoặc section tùy target.

---

# 33. Stack unwinding

Nếu:

```text id="h7m3q5"
panic=abort
```

không cần full unwind infrastructure.

Nếu:

```text id="n4c8v2"
panic=unwind
```

compiler emit unwind metadata.

Do đó:

```text id="x1z6r9"
runtime complexity = profile dependent
```

---

# 34. TLS

Thread-local storage có thể map trực tiếp xuống platform:

```text id="p8m2k4"
ELF TLS
PE TLS
Mach-O TLS
```

không cần Axiom runtime abstraction nếu API không yêu cầu complex lifecycle.

---

# 35. FFI

FFI không nên kéo runtime tự động.

Ví dụ:

```axiom
extern @abi(C)
fn puts(x: *const u8) -> i32
```

program dùng `puts`:

```text id="b7c1m5"
link C library
```

Nếu static/dynamic tùy target.

Axiom không cần dựng một “C runtime” riêng nếu platform/toolchain cung cấp nó.

---

# 36. Nhưng mục tiêu “không phụ thuộc third-party compiler” vẫn giữ

Điều này không có nghĩa:

```text id="j9w2q4"
Axiom phải tự implement libc
```

Không cần.

Có thể:

```text id="s3m8v1"
Axiom compiler
    ↓
native code
    ↓
OS ABI / system libraries
```

System library là platform dependency, không phải compiler dependency.

---

# 37. Runtime component graph

Tôi đề xuất một metadata format nội bộ:

```text id="0v4k8n"
component {
    name: allocator
    requires: [os_memory]
    exports: [...]
}
```

Ví dụ:

```text id="c5m2r7"
async_executor
    requires:
        task
        synchronization
```

Linker chỉ kéo component cần thiết.

---

# 38. Link-time dead stripping

Ngay cả khi dependency được link:

```text id="z7q1p3"
unused runtime functions
```

phải có khả năng bị:

```text id="m4c8x2"
dead-strip
```

Do đó:

```text id="n2v5k7"
runtime modularity
+
LTO
+
section GC
```

giúp binary nhỏ.

---

# 39. Binary size model

Tôi đề xuất không đặt mục tiêu:

> “Axiom executable luôn nhỏ hơn C.”

Không thể đảm bảo.

Mục tiêu kỹ thuật thực tế:

```text id="j8m3p6"
For equivalent semantics and optimization level:

Axiom should not impose mandatory
runtime/object-model overhead.
```

Ví dụ một `struct Point` không tự nhiên kéo:

```text id="d7v2x4"
vtable
RTTI
object header
GC metadata
reference count
```

---

# 40. Runtime invariants

### ART-01 — No Mandatory Runtime

Core program có thể chạy không cần runtime component ngoài startup/target glue tối thiểu.

### ART-02 — Capability-Based Runtime

Runtime components được link theo capability/use.

### ART-03 — No Hidden Initialization

Không có global runtime initialization nếu semantics không yêu cầu.

### ART-04 — No Mandatory GC

Runtime không chứa tracing GC mặc định.

### ART-05 — No Mandatory RC

Không có implicit reference counting.

### ART-06 — Async Optional

Async syntax không kéo executor nếu program không cần executor.

### ART-07 — Thread Optional

Không dùng concurrency thì không link thread machinery.

### ART-08 — Reflection Optional

Không dùng runtime reflection thì không có runtime type metadata.

### ART-09 — Panic Profile

Panic implementation phụ thuộc compilation profile.

### ART-10 — Freestanding Support

Compiler có thể tạo freestanding binary.

### ART-11 — ABI Independence

Core semantics không phụ thuộc C/C++ ABI.

### ART-12 — Runtime Modularity

Runtime components có dependency graph rõ ràng.

### ART-13 — Dead Component Elimination

Unused runtime components/functions có thể bị loại bỏ.

### ART-14 — Startup Minimality

Program startup chỉ thực hiện initialization cần thiết.

---

# 41. Kiến trúc Axiom lúc này

Chúng ta đã có một chuỗi khá hoàn chỉnh:

```text
                    AXIOM SOURCE
                         │
                         ↓
                 AST → HIR → MIR
                         │
                         ↓
                  SEMANTIC VERIFIER
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
         Ownership     Regions     Effects
             │           │           │
             └───────────┼───────────┘
                         ↓
                   Concurrency
                         │
                         ↓
                   VERIFIED MIR
                         │
                         ↓
                    OPTIMIZATION
                         │
                         ↓
                      Axiom LIR
                         │
                         ↓
                   Machine Backend
                         │
              ┌──────────┼──────────┐
              ↓          ↓          ↓
             ELF        PE       Mach-O
              │          │          │
              └──────────┼──────────┘
                         ↓
                  Modular Runtime
                    (optional)
```

Điểm rất quan trọng là **runtime nằm bên dưới language semantics**, chứ không nằm giữa programmer và language semantics.

---

# 42. Một vấn đề lớn tiếp theo: ABI + FFI + Object Format

Sau Runtime Model, tôi không nghĩ nên đi ngay vào syntax.

Có một tầng cần khóa trước:

## `AXIOM NATIVE ABI & BINARY MODEL v0.1`

Nó phải trả lời chính xác:

- `struct` truyền qua register hay memory?
- `enum` layout thế nào?
- `Option<T>` niche optimization thế nào?
- generic specialization ABI ra sao?
- function pointer representation?
- closure representation?
- `view<T>` ABI?
- `dyn Trait` ABI?
- variadic functions?
- C ABI?
- system ABI?
- symbol mangling?
- name visibility?
- TLS?
- static?
- relocation?
- TLS relocation?
- ELF/PE/Mach-O sections?
- exception/unwind metadata?
- debug information?
- SIMD/vector ABI?
- alignment?
- packed layout?
- endianness?

Đây là phần sẽ quyết định Axiom có thực sự là **một native systems language độc lập**, hay chỉ là một high-level language rồi cuối cùng phải “nhờ C++/LLVM làm hộ”.

Và có một nguyên tắc tôi muốn giữ xuyên suốt:

> **Axiom ABI phải là consequence của semantic type system, không được để ABI quay ngược lại quyết định semantics của ngôn ngữ.**