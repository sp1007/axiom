# BOOTSTRAP-156 — Native Runtime Primitives, Allocator Architecture & `std::core`
**STATUS: FROZEN / COMPLETED**

> **`std::core` phải là nền tảng có thể xây dựng gần như toàn bộ thư viện còn lại bằng chính Axiom, trong khi compiler chỉ cung cấp một tập rất nhỏ các primitive thực sự không thể biểu diễn bằng Axiom.**

Mục tiêu ở đây là tránh hai cực đoan:

```text
Cực đoan 1:
Compiler biết quá nhiều → language runtime khổng lồ

Cực đoan 2:
std::core quá yếu → mọi thứ phải là compiler intrinsic
```

Axiom chọn:

```text
        Axiom language semantics
                  ↓
        tiny compiler primitives
                  ↓
             std::core
                  ↓
       alloc / collections / io / ...
```

---

# 1. Phân chia 4 tầng

Chốt mô hình:

```text
┌────────────────────────────────────┐
│ Axiom Language Core                │
│ type / ownership / capability ...  │
├────────────────────────────────────┤
│ Compiler Builtins                  │
│ machine/compiler-only operations   │
├────────────────────────────────────┤
│ std::core                           │
│ foundational Axiom library         │
├────────────────────────────────────┤
│ Runtime / System Components        │
│ OS / allocator / thread / async... │
└────────────────────────────────────┘
```

Compiler Builtin **không phải** standard library.

---

# 2. Compiler primitive tối thiểu

Chỉ những thứ như:

```text
size_of
align_of
offset_of

atomic primitive
volatile primitive

CPU intrinsic
memory barrier
compiler barrier

bit operations
unchecked low-level operations

type/layout introspection
```

mới có thể cần compiler support.

Không nên biến:

```text
Vec
String
HashMap
Option
Result
Box
Arc
Mutex
```

thành compiler magic.

---

# 3. `std::core` không có OS dependency

`std::core` phải chạy được trong:

```text
hosted
freestanding
kernel
embedded
GPU-subset
```

nếu API cụ thể phù hợp.

Ví dụ:

```text
Option
Result
Slice/View
Iterator
Ordering
numeric traits
memory utilities
```

không cần OS.

---

# 4. `Option`

`Option<T>` là enum:

```ax
enum Option<T> {
    None,
    Some(T)
}
```

Không cần runtime đặc biệt.

Compiler có thể tối ưu niche:

```text
Option<NonNull<T>>
```

thành representation tương đương pointer khi hợp lệ.

Nhưng:

> Niche optimization là implementation optimization, không phải semantic definition của `Option`.

---

# 5. `Result`

```ax
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

`?` được compiler lower thành control flow.

Không cần exception runtime.

---

# 6. `Box<T>`

`Box<T>` là standard-library abstraction:

```text
owned dynamic storage
```

với semantics:

```text
!Copy
Drop
ownership
```

Compiler chỉ hỗ trợ allocation/storage optimization.

Ví dụ:

```ax
let x = Box.new(value);
```

có thể sau optimization trở thành:

```text
register
stack
SSA
```

nếu address/identity không observable.

---

# 7. Allocator không phải một allocator duy nhất

Chốt interface:

```text
Allocator {
    allocate(...)
    deallocate(...)
    grow(...)
    shrink(...)
}
```

nhưng implementation có thể là:

```text
SystemAllocator
AxiomAllocator
Arena
Pool
Slab
StackAllocator
StaticAllocator
CustomAllocator
```

---

# 8. Allocation contract

Allocator phải trả về storage thỏa:

```text
size
alignment
validity
ownership
storage domain
```

Compiler verifier dùng contract này.

---

# 9. Allocation failure

Không dùng:

```text
NULL
```

làm semantic API chính.

Có thể:

```text
Result<Allocation, AllocError>
```

với các chiến lược:

```text
fallible
abort
panic
```

tùy allocator/profile.

---

# 10. Allocator không được hidden

Không có:

```text
global hidden allocator
```

bắt buộc cho mọi chương trình.

Program có thể:

```text
NO_ALLOCATOR
SYSTEM_ALLOCATOR
CUSTOM_ALLOCATOR
ARENA
STATIC_ONLY
```

---

# 11. `Box` và allocator

`Box<T>` cần một allocation provider nhưng compiler không được giả định:

```text
Box = malloc
```

Semantics chỉ là:

```text
owned dynamic storage
```

---

# 12. `Vec<T>`

`Vec<T>` là:

```text
pointer/storage
length
capacity
```

về logical semantics.

Nhưng representation có thể được tối ưu nếu address/layout không observable.

---

# 13. Vec relocation

```text
push()
```

có thể relocate storage.

Do đó:

```text
active mut_view<T>
```

hoặc capability phụ thuộc vào vùng storage sẽ ngăn relocation.

Đây là nơi memory model và `Vec` kết nối trực tiếp.

---

# 14. Vec không đảm bảo stable address

Không được mặc định:

```text
Vec<T> → stable pointer
```

Nếu cần stable address:

```text
Box
stable storage container
arena
pinned/system abstraction
```

phải được sử dụng.

---

# 15. `String`

Axiom phân biệt:

```text
String
Str
Bytes
```

### `String`

Owning UTF-8 text.

### `Str`

Non-owning UTF-8 text view.

### `Bytes`

Raw bytes.

Không implicit conversion giữa chúng nếu semantics không rõ.

---

# 16. UTF-8 invariant

`String` phải luôn chứa UTF-8 hợp lệ.

`Bytes` không có invariant UTF-8.

Do đó:

```text
Bytes → String
```

phải validate hoặc dùng explicit unsafe constructor.

---

# 17. Byte operations

`std::core` cần primitive:

```text
copy
move
fill
compare
```

nhưng semantics phải phân biệt:

```text
ordinary memory
volatile memory
atomic memory
```

Không được dùng một `memcpy` universal để phá semantic boundaries.

---

# 18. `memcpy`

Ở library level:

```text
copy_nonoverlapping
```

chỉ hợp lệ khi vùng nguồn/đích thỏa contract.

Compiler có thể lower thành:

```text
inline instructions
SIMD
rep movsb
library call
```

tùy target.

---

# 19. `memmove`

Cho phép overlap:

```text
move_bytes(src, dst, n)
```

Compiler/backend có thể chọn implementation tối ưu.

---

# 20. Memory initialization

Axiom cần phân biệt:

```text
UNINIT
INIT
MOVED
DROPPED
```

đã có trong verifier.

`Uninit<T>` chỉ là low-level abstraction.

Không được cho phép ordinary safe code đọc nó.

---

# 21. `MaybeUninit` tương đương

Có thể đặt tên:

```text
Uninit<T>
```

với operations:

```text
uninit
write
assume_init
```

Trong đó:

```text
assume_init
```

là unsafe nếu compiler không chứng minh initialization.

---

# 22. `assume_init` không phải “bỏ safety”

Nó tạo trusted precondition:

```text
T is fully initialized
```

sau đó verifier tiếp tục theo dõi.

Phù hợp với:

```text
AUNSAFE
```

đã frozen.

---

# 23. Bit operations

`std::core` nên cung cấp:

```text
count_ones
count_zeros
leading_zeros
trailing_zeros
rotate_left
rotate_right
reverse_bits
byte_swap
```

Compiler có thể map trực tiếp xuống ISA.

---

# 24. Endianness

API:

```text
to_le
to_be
from_le
from_be
```

không được phụ thuộc target bằng semantic magic.

Compiler tối ưu:

```text
little-endian target
```

thành no-op khi phù hợp.

---

# 25. Overflow operations

Numeric primitives:

```text
checked_add
checked_sub
checked_mul

wrapping_add
wrapping_sub
wrapping_mul

saturating_add
saturating_sub
```

Semantics rõ ràng.

---

# 26. Ordinary arithmetic

Axiom core vẫn có:

```text
a + b
```

với semantics overflow đã định nghĩa.

Compiler không được biến signed overflow thành C-style UB.

---

# 27. Atomics

Compiler primitive:

```text
atomic_load
atomic_store
atomic_rmw
atomic_compare_exchange
```

Standard library xây:

```text
Atomic<T>
```

trên đó.

---

# 28. Atomic ordering

Các order:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

đã frozen.

Compiler backend map xuống target.

---

# 29. `Atomic<T>` không phải ordinary `T`

Không cho:

```text
Atomic<T> → mut_view<T>
```

vì điều đó phá memory model.

---

# 30. Volatile

Primitive riêng:

```text
volatile_load
volatile_store
```

Không dùng atomic primitive thay thế.

---

# 31. Compiler barrier

Primitive:

```text
compiler_barrier()
```

ngăn compiler reorder/eliminate theo contract.

Không nhất thiết tạo CPU fence.

---

# 32. CPU fence

Primitive:

```text
cpu_fence(order)
```

là machine-level ordering.

Khác:

```text
compiler_barrier
```

---

# 33. Device fence

GPU/system layer có:

```text
device_fence
```

không nhập nhằng với CPU fence.

---

# 34. Intrinsics

Axiom cần cơ chế compiler intrinsic nội bộ:

```text
@intrinsic(...)
```

nhưng:

> Programmer không được tự định nghĩa intrinsic semantic tùy ý.

Compiler biết tập intrinsic canonical.

---

# 35. CPU intrinsics

Ví dụ:

```text
x86_sse...
x86_avx...
arm_neon...
riscv_vector...
```

nằm trong target-specific library.

Compiler backend mới quyết định machine instruction.

---

# 36. Target feature

Intrinsic chỉ hợp lệ nếu:

```text
TargetFeatures
```

cho phép.

Compiler không được phát instruction không tồn tại trên target.

---

# 37. SIMD API

Không cần bắt programmer dùng intrinsic.

Có thể có:

```text
std::simd
```

và auto-vectorizer vẫn là đường mặc định.

Explicit SIMD dành cho trường hợp cần kiểm soát.

---

# 38. `std::core::mem`

Đề xuất:

```text
mem/
 ├── size_of
 ├── align_of
 ├── offset_of
 ├── swap
 ├── replace
 ├── take
 ├── drop
 ├── copy
 ├── copy_nonoverlapping
 ├── zeroed
 └── uninit
```

Một số API compiler-known nhưng interface nằm ở std.

---

# 39. `zeroed<T>`

Không phải mọi type đều hợp lệ khi toàn bộ byte = 0.

Do đó:

```text
zeroed<T>()
```

chỉ safe nếu:

```text
ZeroValid<T>
```

được compiler chứng minh.

Nếu không:

```text
unsafe
```

---

# 40. `Copy` và byte-copy

Rất quan trọng:

```text
Copy<T>
```

không đồng nghĩa:

```text
arbitrary byte copy is valid
```

Bitwise validity và semantic Copy là hai khái niệm khác nhau.

---

# 41. Equality

Không dùng:

```text
memcmp(&a, &b)
```

làm định nghĩa equality.

Vì:

```text
padding
NaN
niche
logical representation
```

có thể khác.

---

# 42. Hash

Hash semantic value, không hash toàn bộ physical object bytes mặc định.

Compiler có thể tối ưu representation sau khi semantic hash được xác định.

---

# 43. `Drop`

`std::core` cung cấp trait:

```text
Drop
```

nhưng compiler chịu trách nhiệm:

```text
drop glue
cleanup paths
exactly-once semantics
```

---

# 44. Explicit `drop`

```ax
drop(x);
```

là semantic early destruction/release.

Sau đó:

```text
x = new_value;
```

có thể hợp lệ.

---

# 45. Panic

`std::core` cung cấp panic interface:

```text
panic(message)
```

Compiler/runtime profile quyết định:

```text
abort
unwind
custom handler
```

---

# 46. Panic payload

Không cần bắt buộc heap allocation.

Ví dụ minimal freestanding:

```text
panic
 ↓
platform handler
 ↓
abort
```

---

# 47. Panic runtime

Nếu program:

```text
panic=abort
```

compiler có thể loại bỏ:

```text
unwind tables
cleanup runtime
exception machinery
```

nếu semantics cho phép.

---

# 48. Assertions

`assert(condition)` nên là library/compiler-known convenience.

Trong release build:

```text
assert
```

chỉ được loại bỏ nếu configuration semantics cho phép.

Không được tự ý biến assertion thành “hint”.

---

# 49. Debug assertions

```text
debug_assert
```

có configuration-dependent semantics.

Do đó nó phải được coi là explicit build-profile feature, không phải optimizer tự quyết.

---

# 50. `std::core` collections

Core không nên chứa toàn bộ collections.

Chỉ:

```text
Option
Result
Range
Ordering
Iterator foundations
```

Các cấu trúc lớn:

```text
Vec
HashMap
BTreeMap
Deque
```

nằm ở layer cao hơn.

---

# 51. Iterator

Iterator phải là zero-cost abstraction.

```ax
for x in values {
    ...
}
```

có thể lower thành:

```text
loop
index
load
branch
```

mà không tạo iterator object runtime nếu abstraction không observable.

---

# 52. Range

```text
0..n
```

là semantic range.

Compiler có thể biến thành:

```text
induction variable
```

và Scalar Evolution đã xây ở optimization layer sẽ xử lý.

---

# 53. Function utilities

`std::core` có thể cung cấp:

```text
Fn
FnMut
FnOnce
```

hoặc semantic equivalents.

Closure capture vẫn do compiler xác định.

---

# 54. `Fn` traits không tạo runtime object

Static dispatch:

```text
generic<T: Fn(...)>
```

được specialize/inline.

Không có hidden vtable.

---

# 55. `dyn Fn`

Nếu explicit:

```text
dyn Fn(...)
```

thì dynamic dispatch mới xuất hiện.

---

# 56. Runtime composition

`std::core` không kéo theo:

```text
allocator
thread
async
IO
Unicode
reflection
```

trừ khi API sử dụng chúng.

---

# 57. Dependency graph

Ví dụ:

```text
tiny_program
    ↓
std::core
```

có thể link gần như không runtime.

Trong khi:

```text
network_server
    ↓
std::core
    ↓
alloc
    ↓
thread
    ↓
sync
    ↓
os
```

chỉ link những thành phần cần thiết.

---

# 58. Compiler builtins manifest

Compiler nên có machine-readable:

```text
BuiltinManifest
```

chứa:

```text
name
signature
targets
effects
safety
lowering
availability
```

Ví dụ:

```text
atomic_compare_exchange
    ABI: compiler-internal
    Effects: Atomic
    Safety: safe through Atomic<T>
    Lowering: target-specific
```

---

# 59. Intrinsic implementation

Một intrinsic có thể có:

```text
generic fallback
target implementation
```

Ví dụ:

```text
count_ones
```

Nếu CPU có instruction:

```text
POPCNT
```

→ dùng instruction.

Nếu không:

```text
software implementation
```

Compiler chọn.

---

# 60. Intrinsic không làm mất portability

Source:

```ax
x.count_ones()
```

không cần:

```text
#if x86
```

trong application.

Backend quyết định implementation.

---

# 61. Compiler fallback

Một số compiler builtin có thể có canonical Axiom implementation.

Điều này rất hữu ích cho self-hosting:

```text
stage 1 compiler
 ↓
builtin
 ↓
stage 2
 ↓
builtin implementation rewritten in Axiom
```

---

# 62. Bootstrap strategy

Chốt:

```text
Stage 0
External compiler
        ↓
minimal builtins

Stage 1
Axiom std::core
        ↓
mostly Axiom source

Stage 2
compiler builtins reduced

Stage 3
self-hosted compiler
```

---

# 63. Không để intrinsic API trở thành “second language”

Đây là invariant quan trọng.

Intrinsic phải:

```text
small
typed
stable
documented
target-aware
verifiable
```

Không có:

```text
arbitrary compiler IR manipulation
```

trong std.

---

# 64. `unsafe` trong std

Standard library có thể chứa unsafe implementation:

```text
std::alloc
std::vec
std::sync
```

nhưng public API có thể safe.

Ví dụ:

```text
Vec.push()
```

bên trong có thể dùng raw pointer.

Application không cần thấy nó.

---

# 65. Zero-cost abstraction test

Một abstraction được coi là zero-cost khi:

```text
semantic overhead
```

không bắt buộc phải tồn tại ở runtime.

Ví dụ:

```ax
fn sum(xs: view<i32>) -> i32
```

có thể trở thành:

```text
pointer + length
```

hoặc chỉ:

```text
registers
```

tùy target.

---

# 66. “Zero cost” không có nghĩa “zero instructions”

Đây là cách hiểu chính xác:

> Abstraction không được áp đặt overhead mà một implementation thủ công tương đương không cần có.

Compiler vẫn có thể phải tạo:

```text
bounds check
drop
branch
copy
synchronization
```

nếu semantics yêu cầu.

---

# 67. Memory primitives và optimizer

Compiler được phép nhận diện:

```text
copy
fill
swap
```

và biến thành:

```text
SIMD
vector instructions
special instructions
```

nhưng phải giữ:

```text
ownership
initialization
alias
volatile
atomic
```

---

# 68. `memcpy` và Drop

Không được dùng byte copy để duplicate arbitrary:

```text
Drop-bearing T
```

vì có thể tạo double ownership.

Semantic Copy/Move vẫn là authority.

---

# 69. Compiler/runtime boundary

Chốt kiến trúc:

```text
Language semantics
       ↓
Verified MIR
       ↓
Compiler intrinsic
       ↓
std implementation
       ↓
runtime/system
```

Không có đường ngược:

```text
runtime
 ↓
changes language semantics
```

---

# 70. Invariants

Đóng băng:

### `ACORELIB-20`
`std::core` provides foundational language-adjacent abstractions without requiring an operating system.

### `ACORELIB-21`
Compiler builtins are distinct from standard-library APIs.

### `ACORELIB-22`
Only operations requiring compiler or target knowledge become compiler builtins.

### `ACORELIB-23`
Standard-library abstractions are implemented in Axiom wherever practical.

### `ACORELIB-24`
`Option` and `Result` are ordinary algebraic types.

### `ACORELIB-25`
Niche optimization does not redefine semantic type representation.

### `ACORELIB-26`
`Box<T>` is a library-owned dynamic-storage abstraction.

### `ACORELIB-27`
`Box<T>` has ownership and Drop semantics and is not Copy.

### `ACORELIB-28`
Physical allocation strategy remains independent of `Box<T>` semantics.

### `ACORELIB-29`
Axiom does not require one universal allocator.

### `ACORELIB-30`
Allocator choice is explicit through profile/runtime/library composition.

### `ACORELIB-31`
Allocation failure has explicit semantic policy.

### `ACORELIB-32`
`Vec<T>` does not guarantee stable physical address.

### `ACORELIB-33`
Live capabilities can prevent storage relocation.

### `ACORELIB-34`
`String`, `Str` and `Bytes` have distinct semantic contracts.

### `ACORELIB-35`
Axiom `String` maintains valid UTF-8.

### `ACORELIB-36`
Byte-oriented APIs do not implicitly establish Unicode validity.

### `ACORELIB-37`
Uninitialized memory cannot be read safely.

### `ACORELIB-38`
Initialization state remains tracked by the compiler verifier.

### `ACORELIB-39`
`assume_init` requires an established initialization contract.

### `ACORELIB-40`
Bitwise copyability is distinct from semantic `Copy`.

### `ACORELIB-41`
Bytewise equality does not define semantic equality.

### `ACORELIB-42`
Semantic hashing is distinct from physical object-byte hashing.

### `ACORELIB-43`
Atomic operations are distinct from ordinary memory operations.

### `ACORELIB-44`
Volatile operations are distinct from atomic operations.

### `ACORELIB-45`
Compiler barriers are distinct from CPU fences.

### `ACORELIB-46`
Device fences are distinct from CPU fences.

### `ACORELIB-47`
Atomic ordering semantics are preserved through all compiler stages.

### `ACORELIB-48`
Target-specific intrinsics are selected through target capabilities.

### `ACORELIB-49`
Unsupported target instructions cannot be emitted.

### `ACORELIB-50`
Compiler intrinsics cannot arbitrarily mutate compiler IR semantics.

### `ACORELIB-51`
`Drop` semantics are language/compiler verified even when implemented in std.

### `ACORELIB-52`
Panic behavior is selected through explicit runtime/build profile.

### `ACORELIB-53`
`panic=abort` may eliminate unwind machinery where semantically valid.

### `ACORELIB-54`
`std::core` does not implicitly require allocator, thread, async, IO or reflection runtime.

### `ACORELIB-55`
Iterator abstractions are designed for zero-cost lowering.

### `ACORELIB-56`
Generic iterator abstractions do not imply runtime polymorphism.

### `ACORELIB-57`
Dynamic callable dispatch occurs only when explicitly requested.

### `ACORELIB-58`
Safe std APIs may encapsulate unsafe implementation details.

### `ACORELIB-59`
Unsafe implementation inside std does not weaken public semantic guarantees.

### `ACORELIB-60`
Compiler builtins have machine-readable contracts.

### `ACORELIB-61`
Compiler builtins have explicit target availability.

### `ACORELIB-62`
Compiler builtins may have portable Axiom fallbacks where practical.

### `ACORELIB-63`
Intrinsic availability does not destroy source portability.

### `ACORELIB-64`
`std::core` must remain usable in freestanding environments where its dependencies permit.

### `ACORELIB-65`
`std::core` must not become a second language.

### `ACORELIB-66`
Standard-library abstractions cannot override language ownership/capability semantics.

### `ACORELIB-67`
Optimization may erase physical abstraction overhead but cannot erase required observable semantics.

### `ACORELIB-68`
Memory primitives preserve ownership, initialization, aliasing, atomic and volatile contracts.

### `ACORELIB-69`
The bootstrap compiler must be capable of compiling an increasing portion of `std::core` as Axiom source.

### `ACORELIB-70`
The final self-hosted compiler must not require an external C/C++ compiler to implement `std::core`.

---

# Kiến trúc Axiom hiện tại đã khá hoàn chỉnh

Từ các phần đã đóng băng, pipeline lớn hiện tại đã trở thành:

```text
                         AXIOM SOURCE
                              │
                              ▼
                    Lexer / CST / AST
                              │
                              ▼
                    Name Resolution
                              │
                              ▼
                  Type / Trait / Const
                              │
                              ▼
                         HIR
                              │
                              ▼
                         MIR
                              │
                              ▼
              ┌──────────────────────────┐
              │     VERIFICATION         │
              │ Ownership                │
              │ Initialization           │
              │ Capability               │
              │ Drop                     │
              │ Alias                    │
              │ Effect                   │
              │ Escape                   │
              │ Concurrency              │
              │ Async / GPU / FFI         │
              └────────────┬─────────────┘
                           │
                           ▼
                      VERIFIED MIR
                           │
                           ▼
                     SSA + MemorySSA
                           │
                           ▼
                         OptIR
                           │
            ┌──────────────┼───────────────┐
            ▼              ▼               ▼
       Interprocedural   Loop/Memory    Data Layout
            │           Vectorization       │
            ▼              ▼               ▼
       Specialization   Microarch        PGO/LTO
            └──────────────┼───────────────┘
                           ▼
                   Optimized OptIR
                           │
                           ▼
                       ABI MIR
                           │
                           ▼
                         LIR
                           │
                           ▼
                     Machine IR
                           │
                           ▼
                   Register Allocation
                           │
                           ▼
                     Machine Code
                           │
                           ▼
                      Object File
                           │
                           ▼
                         Linker
                           │
                           ▼
                 Native Executable
```

và phía dưới executable:

```text
Axiom Core
    ↓
Compiler Builtins
    ↓
std::core
    ↓
Allocator / Runtime Components
    ↓
System Layer
    ↓
FFI
    ↓
OS / Hardware
```

**Đây là một điểm rất tốt của thiết kế hiện tại:** compiler có thể cực kỳ phức tạp bên trong, nhưng complexity đó **không bị đẩy lên programmer** dưới dạng pointer arithmetic, lifetime annotation, borrow syntax, `restrict`, manual SIMD hay manual storage selection.

---

# BOOTSTRAP-157 — `std::collections`, Strings, Containers & Zero-Cost Data Structures

Bước tiếp theo hợp lý là xây tầng dữ liệu thực tế phía trên `std::core`:

```text
std::core
    ↓
std::alloc
    ↓
std::collections
    ├── Vec
    ├── Deque
    ├── List
    ├── HashMap
    ├── HashSet
    ├── BTreeMap
    ├── BTreeSet
    ├── SmallVec
    ├── ArrayVec
    └── SoA
```

Nhưng lần này cần giải quyết một vấn đề rất quan trọng đối với mục tiêu hiệu năng của Axiom:

> **Axiom có nên cung cấp một “container mặc định” kiểu `Vec`, hay compiler phải tự chọn giữa inline/stack/heap/arena/SoA tùy cách sử dụng?**

Đây sẽ là bước quyết định xem Axiom có thực sự đạt được triết lý **“programmer mô tả dữ liệu và ý định, compiler tối ưu representation”** hay không.