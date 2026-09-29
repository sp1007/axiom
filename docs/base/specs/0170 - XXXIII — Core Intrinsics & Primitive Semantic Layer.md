Tiếp tục với **XXXIII — Axiom Core Intrinsics & Primitive Semantic Layer v0.1**. Đây là lớp cần khóa trước khi bắt đầu viết `core`, vì nếu không tách rõ thì compiler sẽ vô tình biến stdlib thành một phần của language runtime.

# XXXIII — Core Intrinsics & Primitive Semantic Layer

## 1. Bốn tầng phải tách tuyệt đối

Axiom sẽ có:

```text
┌──────────────────────────────┐
│        Axiom Language        │
│ syntax + semantic primitives │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│     Compiler Intrinsics      │
│ compiler-known operations    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│          core                │
│ safe library abstractions    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│           std                 │
│ OS / IO / Net / Thread / ... │
└──────────────────────────────┘
```

Nguyên tắc:

> **Chỉ đưa vào language những semantics mà compiler bắt buộc phải hiểu.**

Không biến mọi tiện ích nhanh thành keyword/intrinsic.

---

# 2. Những thứ thực sự thuộc Language

Core language chỉ cần hiểu trực tiếp:

```text
bool
integer
float
unit
never

struct
enum
tuple
array

function
closure

ownership
move
Copy
Drop

view
mut_view

pointer
unsafe

async
await

atomic semantics

comptime

extern / ABI
```

Ngoài ra là control flow và type system.

Không cần:

```text
Vec
String
HashMap
File
Socket
Mutex
Arc
```

là language primitive.

---

# 3. Intrinsic là gì?

Intrinsic là operation mà programmer có thể gọi như function, nhưng compiler có quyền nhận diện đặc biệt.

Ví dụ:

```axiom id="m2i4f7"
size_of<T>()
```

Compiler có thể lower trực tiếp thành constant.

Nhưng:

```text id="j6l7te"
size_of<T>
```

không phải keyword.

Điều này giữ syntax nhỏ.

---

# 4. Phân loại intrinsic

Tôi đề xuất 6 nhóm:

```text
Intrinsic
├── Type/Layout
├── Memory
├── Control
├── Arithmetic
├── Atomic
└── Compiler/Optimization
```

---

# 5. Type/Layout intrinsics

### `size_of<T>()`

```axiom id="8r0h7w"
let n = size_of<MyStruct>()
```

Compile-time constant.

### `align_of<T>()`

```axiom id="h11p7x"
let a = align_of<MyStruct>()
```

### `type_id<T>()`

Không nên đưa runtime `TypeId` vào Core v0.1.

Nếu cần reflection compile-time:

```text id="g6m5s1"
comptime type information
```

là đủ.

Do đó:

> `size_of` và `align_of` có; runtime type identity chưa có.

---

# 6. `offset_of`

Có giá trị cho FFI/system programming:

```axiom id="qv9y13"
offset_of<MyStruct>(field)
```

Nhưng field phải được compiler resolve.

Ví dụ concept:

```axiom id="k9qzv5"
offset_of<Vec2>(Vec2.x)
```

Trả về compile-time constant.

Nên có vì:

- FFI
- packed data
- kernel
- serialization
- hardware structures

---

# 7. Representation introspection

Có:

```text id="1v7z2k"
size_of
align_of
offset_of
```

Không có mặc định:

```text id="7gq0h4"
field_count
field_name
runtime_type_name
```

những thứ đó thuộc compile-time reflection.

---

# 8. Memory intrinsics

Nhóm này phải cực kỳ cẩn thận.

### `copy`

Semantic:

```text id="1g7x8m"
copy<T>(dst: mut_view<T>, src: view<T>)
```

Safe nếu capability analysis chứng minh hợp lệ.

Không nhất thiết intrinsic.

Có thể implementation trong Core.

---

# 9. `move`

`move` **không cần là function runtime**.

Nó là ownership semantic operation.

Ví dụ:

```axiom id="8m38k4"
let b = a
```

Compiler quyết định:

```text id="7m0y7h"
Copy
```

hay:

```text id="4f0s7f"
Move
```

tùy type.

Do đó không nên có:

```axiom id="d4l9e2"
move(a)
```

trong v0.1 như một runtime intrinsic.

---

# 10. Explicit `drop`

Ngược lại:

```axiom id="q6k9v2"
drop(x)
```

nên tồn tại.

Nó có semantics:

```text id="5l8qgs"
terminate ownership of x now
```

nhưng không đảm bảo physical deallocation.

Compiler lower:

```text id="p0v3ne"
DROP x
```

---

# 11. `view()`

`view(x)` là semantic operation.

```axiom id="prk6uz"
let v = view(x)
```

Compiler tạo:

```text id="1n2f4j"
Capability {
    provenance = x
    region = whole(x)
    access = READ
}
```

Không nhất thiết gọi runtime function.

Do đó `view` nên là **compiler-known intrinsic**.

---

# 12. `mut_view()`

Tương tự:

```axiom id="l7r4h9"
let v = mut_view(x)
```

Compiler tạo:

```text id="q0d6ph"
Capability {
    provenance = x
    region = whole(x)
    access = WRITE
}
```

và verifier kiểm tra exclusive access.

---

# 13. Slice operation

Expression:

```axiom id="j0x2xk"
a[1..4]
```

không nên runtime-call `slice()` một cách bắt buộc.

Semantic lowering:

```text id="v1xq8w"
VIEW
region = [1,4)
```

Optimizer có thể biến thành:

```text id="xw4z3p"
pointer + length
```

hoặc representation khác.

---

# 14. Indexing

```axiom id="o0v6s7"
a[i]
```

semantic operation:

```text id="d6v5x1"
INDEX
```

có bounds-check.

Optimizer có thể loại:

```text id="5m8q6f"
BOUNDS_CHECK
```

nếu chứng minh:

```text id="y7t1ac"
0 <= i < len(a)
```

---

# 15. Pointer intrinsics

Raw pointer:

```text id="9kjy4e"
*const T
*mut T
```

Các operation:

```text id="6k3gxn"
ptr.read()
ptr.write()
ptr.add()
ptr.offset()
ptr.cast()
```

đều unsafe.

Không cần compiler keyword cho từng operation.

Core có thể định nghĩa wrapper/compiler intrinsic.

---

# 16. `address_of`

Có thể có:

```axiom id="2y8x6v"
unsafe {
    address_of(x)
}
```

Nhưng cần phân biệt:

```text id="j09h1x"
address_of
```

với:

```text id="h6z5x9"
raw pointer conversion
```

Address exposure làm storage identity observable.

Đây chính là trigger cho:

```text
AMEM-55
AMEM-70
```

---

# 17. `addr_cast`

Numeric address và pointer provenance khác nhau.

Do đó:

```text id="8f1w5r"
addr_cast
```

phải là unsafe.

Ví dụ concept:

```axiom id="j3u0af"
unsafe {
    let p = addr_cast::<*mut Device>(address)
}
```

Không được biến integer thành safe pointer một cách ngầm định.

---

# 18. `ptr_cast`

Khác `addr_cast`.

```text id="4n1v8x"
ptr_cast::<T>(p)
```

giữ provenance nhưng thay đổi typed interpretation.

Vẫn unsafe nếu alignment/type validity không được chứng minh.

---

# 19. `bit_cast`

Đây nên là intrinsic rõ ràng:

```axiom id="m8t3d7"
bit_cast<f32>(bits)
```

Điều kiện:

```text id="5q7u8e"
same size
valid destination representation
```

Không có:

```text id="2o0z1n"
transmute<T,U>()
```

tùy tiện.

---

# 20. `reinterpret_bytes`

Nếu cần raw byte reinterpretation:

```text id="5h3e0n"
reinterpret_bytes<T>(bytes)
```

phải phân biệt với `bit_cast`.

`bit_cast`:

```text id="f0r7ne"
same-size value representation
```

`reinterpret_bytes`:

```text id="5l1d9g"
byte-level interpretation
```

có thể yêu cầu alignment/initialization guarantees.

---

# 21. `MaybeUninit`

Đây **không phải intrinsic**.

Nó nên là Core type:

```text id="y1b4d6"
MaybeUninit<T>
```

cho system code.

Ví dụ:

```text id="9y6n0p"
allocate storage
→ initialize fields
→ assume_init()
```

`assume_init()` unsafe.

Điều này cho phép:

- custom allocator
- FFI
- array initialization
- OS structures
- high-performance buffers

mà không làm language type system phình lên.

---

# 22. `black_box`

Compiler intrinsic:

```axiom id="6x8p2q"
black_box(x)
```

Semantics:

> Compiler phải coi giá trị có thể được observed externally tại điểm này theo optimization model, nhưng giá trị ngôn ngữ vẫn là `x`.

Không phải:

```text id="p2s5k8"
volatile
```

Không phải:

```text id="h6k4j1"
atomic
```

Mục đích:

- benchmark
- optimizer testing
- preventing dead-code elimination

---

# 23. Branch prediction hints

Không nên đưa:

```text id="8y2r3f"
likely()
unlikely()
```

vào Core semantic v0.1.

Nếu cần:

```axiom id="y5z8m4"
@cold
fn error_path() {}
```

hoặc compiler attributes.

Vì branch hint không được phép thay đổi semantics.

---

# 24. Arithmetic intrinsics

Compiler phải hiểu:

```text id="m8h5q0"
+%
-| 
*|
```

nhưng không cần:

```text id="b9w4v2"
intrinsic_add_wrapping()
```

Language operator đã đủ.

Tuy nhiên có intrinsic cho CPU-specific arithmetic sau này:

```text id="q1m6z8"
mul_high
leading_zeros
trailing_zeros
population_count
rotate_left
rotate_right
```

Những cái này nên nằm Core numeric API.

Compiler pattern-match và lower thành instruction nếu target hỗ trợ.

---

# 25. Division semantics

Core không nên tự implement:

```text id="7a2f3n"
i32.div()
```

bằng Axiom nếu compiler đã có arithmetic instruction.

Compiler xử lý:

```text id="v5x0p2"
DIV
REM
```

với semantics:

```text id="q4m8r1"
division by zero → panic/trap
```

---

# 26. Atomic intrinsics

Atomic là semantic primitive.

Nhưng programmer-facing API:

```axiom id="k7q2m9"
Atomic<i32>
```

nên là Core/Std type.

Compiler nhận diện operations:

```text id="8r3x1c"
load
store
swap
fetch_add
compare_exchange
```

và lower xuống MIR:

```text id="5v0s8n"
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

---

# 27. Memory ordering

Ordering phải là type/enum compile-time:

```axiom id="s6m1q9"
Ordering.Relaxed
Ordering.Acquire
Ordering.Release
Ordering.AcqRel
Ordering.SeqCst
```

Compiler kiểm tra.

Không phải string:

```text id="0w4k8v"
"acquire"
```

---

# 28. Volatile

Volatile phải là operation riêng:

```text id="n5k7p2"
volatile_read
volatile_write
```

và **không đồng nghĩa atomic**.

Đây là system programming primitive.

---

# 29. Fence

```text id="m2x8c4"
fence(Ordering.SeqCst)
```

lower:

```text id="z5v1r8"
FENCE
```

Target backend chịu trách nhiệm chọn instruction.

---

# 30. Compiler optimization intrinsics

Nhóm:

```text id="q8m3y6"
black_box
assume
unreachable
```

Cẩn thận với `assume`.

Tôi đề xuất:

```text id="d1x7k5"
assume(condition)
```

**không thuộc safe Core API**.

Nó chỉ tồn tại:

```text id="z8c2m4"
unsafe
```

vì một assumption sai có thể làm toàn bộ optimization trở nên invalid.

---

# 31. `unreachable`

Có:

```text id="r6y2v9"
unreachable()
```

nhưng semantics tương đương:

```text id="k2w5f1"
never
```

và nếu execution đến đó:

```text id="n3j8x0"
trap / undefined unsafe behavior
```

Cần phân biệt với:

```text id="q5v1m7"
panic()
```

Panic có observable error semantics.

`unreachable` nói:

> Programmer/compiler invariant đảm bảo control flow không tới đây.

---

# 32. `assert`

`assert(condition)` là library-level operation:

```axiom id="v4k9m1"
assert(x >= 0)
```

Nếu false:

```text id="e2x7s5"
panic
```

Không phải safety proof.

Do đó:

```text id="j3p8q6"
debug_assert
```

không được verifier coi là proof của memory safety.

---

# 33. Compile-time assertions

```axiom id="b7w2r9"
comptime assert(size_of<T>() <= 64)
```

được xử lý hoàn toàn compile-time.

Đây là một trong những nơi `comptime` rất hữu ích.

---

# 34. Compiler intrinsic không nhất thiết public

Compiler có thể có internal operations:

```text id="a3k8q1"
__axiom_drop
__axiom_view
__axiom_move
```

nhưng **không expose cho programmer**.

AST/HIR có semantic nodes tương ứng.

Điều này tránh việc source language bị ô nhiễm bởi compiler implementation.

---

# 35. Intrinsic resolution

Khi compiler gặp:

```axiom id="w4c7y2"
size_of<T>()
```

resolver xử lý như một predefined symbol.

Ví dụ:

```text id="5s1n8m"
SymbolKind::Intrinsic
```

Nhưng intrinsic vẫn phải có:

```text id="q7z3v0"
FunctionId
TypeSignature
Effects
Safety
ConstEvalRule
LoweringRule
```

---

# 36. Intrinsic metadata

Ví dụ:

```text id="t9f2x6"
Intrinsic {
    id
    name
    signature
    const_eval
    safety
    effects
    lowering
}
```

Ví dụ `size_of`:

```text id="p3m8v1"
const_eval = REQUIRED
safety = SAFE
effects = NONE
lowering = CONSTANT
```

`volatile_read`:

```text id="x6k1r4"
const_eval = FORBIDDEN
safety = UNSAFE
effects = READ_VOLATILE
lowering = TARGET_MEMORY_OP
```

---

# 37. Đây là điểm rất quan trọng cho optimizer

Optimizer không được đoán semantics của intrinsic từ tên.

Nó đọc metadata:

```text id="z2n7c5"
MemoryEffect
Purity
PanicBehavior
ConstEval
NoReturn
Volatile
Atomic
```

Ví dụ:

```text id="q8y4m0"
black_box
```

có:

```text
Pure?       No
Memory?     Unknown/CompilerBarrier
Volatile?   No
Atomic?     No
```

tùy semantic model đã định.

---

# 38. Intrinsic và ABI

Intrinsic không có C ABI.

Ví dụ:

```text id="n3x7r8"
size_of<T>()
```

không thể:

```text
extern "C"
```

vì nó không phải runtime function.

Compiler sẽ eliminate nó thành constant.

---

# 39. Core implementation

Mục tiêu:

```text id="f2k6s9"
~80–90%
```

Core có thể viết bằng Axiom.

Compiler intrinsic chỉ dùng ở những nơi thực sự cần.

Ví dụ:

```axiom id="h9m2v4"
fn min<T: Ord>(a: T, b: T) -> T {
    if a < b { a } else { b }
}
```

Không cần intrinsic.

Optimizer sẽ inline.

---

# 40. Điều gì KHÔNG cần intrinsic?

Không nên intrinsic hóa:

```text id="0k5m8z"
Vec
String
HashMap
Option
Result
Iterator
Range
Path
Duration
```

Ngay cả:

```text id="3r7v1p"
Mutex
```

cũng có thể là library abstraction bao quanh atomic/OS primitives.

---

# 41. Core runtime boundary

Ta có thể định nghĩa:

```text id="n8q4c6"
Core Intrinsic ABI
```

nhưng nó không phải runtime ABI.

Ví dụ:

```text id="5m2x9r"
Intrinsic → MIR
```

chứ không:

```text id="j7v3q1"
Intrinsic → libaxiom_runtime.so
```

trừ khi implementation cụ thể yêu cầu.

---

# 42. Freestanding

Một chương trình:

```axiom id="f0q6w8"
@entry
fn start() {
    let x = 42
}
```

có thể compile mà không cần:

```text id="1y5r7k"
core runtime
allocator
libc
```

Nếu compiler có intrinsic cần thiết, chúng được lower trực tiếp.

---

# 43. Hosted

Nếu dùng:

```axiom id="k3p9w5"
File.open()
```

thì dependency graph kéo:

```text id="r7x1m4"
std.fs
→ platform.linux
→ OS syscall layer
```

Chứ không phải compiler tự động nhúng toàn bộ runtime.

---

# 44. Intrinsic → MIR mapping

Bảng v0.1:

| Source | Semantic IR |
|---|---|
| `size_of<T>()` | `CONST` |
| `align_of<T>()` | `CONST` |
| `offset_of<T>()` | `CONST` |
| `drop(x)` | `DROP` |
| `view(x)` | `VIEW` |
| `mut_view(x)` | `VIEW_MUT` |
| `bit_cast<T>(x)` | `CAST/BITCAST` |
| pointer read | `LOAD` |
| pointer write | `STORE` |
| atomic load | `ATOMIC_LOAD` |
| atomic store | `ATOMIC_STORE` |
| CAS | `ATOMIC_CAS` |
| fence | `FENCE` |
| volatile read | `LOAD[volatile]` |
| volatile write | `STORE[volatile]` |
| `black_box` | optimizer barrier |
| `unreachable()` | `UNREACHABLE` |

---

# 45. Source → Core → MIR

Ví dụ:

```axiom id="3v9k2p"
fn sum(a: view<i32>) -> i32 {
    var result = 0

    for x in a {
        result = result + x
    }

    result
}
```

Core `Iterator` semantics có thể được lower.

Sau đó optimizer có thể nhận ra:

```text id="6z4m8q"
contiguous view
known length
simple iterator
```

và biến thành loop index.

Cuối cùng:

```text id="p1x7c9"
load
add
store
branch
```

rồi backend có thể vectorize.

Programmer không cần biết bất kỳ bước nào.

---

# 46. Intrinsic invariants

Ta freeze nhóm:

```text id="0a8c3f"
AINTR-20  Intrinsics have explicit semantic signatures
AINTR-21  Intrinsic semantics are deterministic
AINTR-22  Intrinsics do not bypass type checking
AINTR-23  Intrinsics do not bypass ownership verification
AINTR-24  Unsafe intrinsics declare safety requirements
AINTR-25  Intrinsics have explicit lowering rules
AINTR-26  Intrinsic effects are machine-readable
AINTR-27  Optimizer uses intrinsic metadata
AINTR-28  Intrinsics may be compile-time only
AINTR-29  Compile-time-only intrinsics emit no runtime code
AINTR-30  Intrinsics do not imply a mandatory runtime
AINTR-31  Intrinsics do not define platform APIs
AINTR-32  Intrinsics preserve ABI semantics
AINTR-33  Intrinsics cannot silently alter language semantics
AINTR-34  Intrinsic behavior is independent of optimization level
AINTR-35  Unsafe intrinsics do not disable unrelated verifier checks
AINTR-36  Intrinsic names are not semantic contracts by themselves
AINTR-37  Intrinsic metadata is part of compiler semantic configuration
AINTR-38  Intrinsic lowering is target-independent until backend stage where possible
```

---

# 47. Final Core boundary

Sau bước này, kiến trúc Axiom trở nên rất sạch:

```text
                         AXIOM LANGUAGE
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          syntax           semantics        type system
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                     Compiler Intrinsics
                              │
                              ↓
                           MIR
                              │
                 ┌────────────┴────────────┐
                 │                         │
              core                     optimizer
                 │                         │
                 └────────────┬────────────┘
                              ↓
                             std
                              │
                ┌─────────────┼─────────────┐
                ↓             ↓             ↓
               OS            Net           Async
```

Điều này giải quyết một vấn đề lớn của các ngôn ngữ hệ thống:

> **Không phải cứ muốn performance thấp-level là phải biến mọi low-level operation thành syntax của language.**

Axiom có thể giữ language nhỏ, trong khi compiler vẫn rất mạnh.

---

# 48. Một quyết định nữa nên freeze

Tôi đề xuất **không có hidden magic trong Core**.

Ví dụ `Vec.push()` không được compiler tự hiểu chỉ vì tên là `push`.

Nếu compiler muốn tối ưu:

```text
Vec.push
```

thì optimizer phân tích IR và metadata của function.

Điều này đảm bảo:

```text
library implementation
```

và:

```text
compiler magic
```

không bị trộn lẫn.

Ngoại lệ chỉ là những primitive đã được specification công nhận như:

```text
view
mut_view
drop
atomic
volatile
bit_cast
```

---

# 49. Bây giờ Axiom đã đủ nền để bước sang implementation thật

Sau ba lớp:

```text
Build System
        ↓
Standard Library Architecture
        ↓
Core Intrinsics
```

thiết kế language đã gần như hoàn chỉnh về mặt architecture.

Bước tiếp theo **không nên tiếp tục thiết kế thêm tính năng**.

Ta chuyển sang:

# XXXIV — Axiom Compiler Implementation Plan

Cụ thể là dựng **Compiler Kernel v0.1** thật sự:

```text
compiler/
├── kernel/
│   ├── ids
│   ├── source
│   ├── span
│   ├── diagnostics
│   ├── interner
│   ├── arena
│   ├── types
│   ├── symbols
│   ├── query
│   ├── cache
│   └── session
```

và quan trọng nhất: xác định **ngôn ngữ dùng để viết compiler bootstrap**.

Tôi đề xuất ngay từ đầu compiler implementation phải được chia thành:

```text
Stage 0
C/C++ bootstrap

Stage 1
Axiom compiler subset

Stage 2
Axiom compiler full

Stage 3
Self-hosted Axiom compiler

Stage 4
Self-hosted compiler + own linker + own stdlib
```

Sau đó chúng ta có thể bắt đầu bằng vertical slice nhỏ nhất:

```text
fn main() {
}
```

và đi xuyên suốt:

```text
Source
→ Lexer
→ Parser
→ AST
→ Resolver
→ HIR
→ Type
→ Ownership
→ MIR
→ Verified MIR
→ LIR
→ x86-64
→ Machine Code
→ ELF
→ axiom-link
→ executable
```

Đây sẽ là **vertical slice đầu tiên của Axiom**, và từ đó mọi subsystem còn lại được xây lên trên một compiler thực sự chạy được, thay vì tiếp tục mở rộng specification trên giấy.