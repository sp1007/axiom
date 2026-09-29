# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XVIII — Unsafe · Raw Pointer · Provenance · Volatile · Intrinsics

Phần này khóa một nguyên tắc rất quan trọng:

> **`unsafe` mở quyền biểu diễn những thứ compiler không thể tự chứng minh; nó không tắt semantic checking của Axiom.**

Mục tiêu là để Axiom có thể viết kernel, allocator, driver, runtime, JIT, FFI, SIMD, MMIO… nhưng safe code vẫn giữ được mô hình đơn giản.

---

# 1. Safe và unsafe

Axiom có hai mức:

```text
safe
unsafe
```

Safe code phải thỏa các invariant của language.

Unsafe code được phép thực hiện các thao tác mà compiler không thể chứng minh hoàn toàn.

Ví dụ:

```axiom
unsafe {
    let p = addr_cast::<*mut u32>(address)
    p.write(42)
}
```

Nhưng sau đó compiler vẫn kiểm tra:

```text
type correctness
control flow
initialization
move state
Drop
ABI
atomic semantics
```

---

# 2. `unsafe` không phải "tắt compiler"

Không được hiểu:

```text
unsafe
```

là:

```text
disable all checks
```

Mà là:

```text
unsafe
    ↓
relax selected semantic proof obligations
    ↓
continue normal compiler verification
```

Đây là distinction nền tảng.

---

# 3. Các thao tác yêu cầu unsafe

Core v0.1 yêu cầu `unsafe` cho:

```text
raw pointer dereference
raw pointer arithmetic
arbitrary address conversion
reinterpretation không an toàn
unaligned typed access
volatile memory access
MMIO
inline assembly
certain FFI operations
manual lifetime/resource assumptions
```

---

# 4. Raw pointer

Hai loại:

```axiom
*const T
*mut T
```

`*const T`:

```text
raw read pointer
```

`*mut T`:

```text
raw mutable pointer
```

Raw pointer không phải ownership.

---

# 5. Raw pointer không phải `view`

So sánh:

```text
view<T>
```

và:

```text
*const T
```

| | `view<T>` | `*const T` |
|---|---|---|
| safe | yes | no dereference |
| provenance | compiler-tracked | programmer contract |
| lifetime | compiler-checked | not guaranteed |
| ownership | none | none |
| arithmetic | restricted | unsafe |
| null | no | possible |
| aliasing | compiler-checked | programmer responsibility |

---

# 6. Raw pointer không có ownership

Ví dụ:

```axiom
let p: *mut T = ...
```

không có nghĩa:

```text
p owns T
```

Do đó:

```text
Drop(p)
```

không giải phóng `T`.

Muốn ownership phải dùng abstraction:

```text
Box<T>
```

hoặc custom owner.

---

# 7. Pointer dereference

Conceptually:

```axiom
unsafe {
    let x = p.read()
    p.write(value)
}
```

Compiler không chứng minh:

```text
p != null
p aligned
p points to T
p is live
p is writable
no conflicting access
```

Đây là programmer's responsibility.

---

# 8. Nhưng type checking vẫn tồn tại

Ví dụ:

```axiom
unsafe {
    p.write("hello")
}
```

nếu `p: *mut i32`

vẫn là type error.

`unsafe` không phá type system.

---

# 9. Null pointer

Raw pointer có thể mang null:

```text
*const T = null
```

nhưng chỉ ở unsafe/system boundary.

Safe code không có:

```text
null
```

thay vào đó:

```text
Option<T>
Option<*const T>
```

nếu semantics cần.

---

# 10. Null không phải invalid address duy nhất

Compiler không được giả định:

```text
non-null == valid
```

Một pointer non-null vẫn có thể:

```text
dangling
misaligned
wrong type
wrong address space
freed
unmapped
```

---

# 11. Pointer provenance

Axiom phân biệt:

```text
numeric address
```

với:

```text
pointer provenance
```

Ví dụ:

```text
address = 0x12340000
```

chỉ là số.

Nó không tự chứng minh:

```text
"đây là pointer tới T"
```

---

# 12. `addr_cast`

Axiom có phép chuyển:

```axiom
let p = addr_cast::<*mut T>(addr)
```

nhưng đây là:

```text
unsafe
```

vì compiler không biết address đó thuộc object nào.

---

# 13. Pointer → integer

Tương tự:

```axiom
let addr = ptr_to_addr(p)
```

là system-level operation.

Khi chuyển pointer thành integer, compiler phải coi việc mất provenance là một semantic boundary.

---

# 14. Không được âm thầm khôi phục provenance

Ví dụ:

```axiom
let n = ptr_to_addr(p)
let q = addr_cast::<*mut T>(n)
```

Axiom không giả định:

```text
q == p
```

theo semantic identity.

Nếu programmer cần điều đó, phải chịu trách nhiệm unsafe.

---

# 15. Pointer arithmetic

Có thể:

```axiom
unsafe {
    let q = p.add(i)
}
```

nhưng chỉ programmer chịu trách nhiệm rằng:

```text
q
```

nằm trong allocation/provenance hợp lệ.

---

# 16. Không có unrestricted pointer arithmetic trong safe code

Safe:

```axiom
a[i]
```

Compiler kiểm tra bounds hoặc chứng minh bounds.

Unsafe:

```axiom
p.add(i)
```

cho phép low-level programming.

---

# 17. One-past pointer

Axiom có thể cho phép pointer biểu diễn:

```text
end = one-past-last
```

cho:

```text
iteration
range construction
C ABI
```

nhưng không được dereference.

---

# 18. Pointer subtraction

```axiom
unsafe {
    let distance = p2.offset_from(p1)
}
```

chỉ hợp lệ khi pointer provenance/region relationship thỏa contract.

Không được coi hai arbitrary addresses là cùng một array.

---

# 19. Typed access

Nếu:

```text
*mut T
```

thì:

```text
read::<T>
write::<T>
```

phải tôn trọng:

```text
alignment
initialization
validity
```

---

# 20. Uninitialized memory

Axiom cần phân biệt:

```text
allocated memory
```

và:

```text
initialized value
```

Allocation không đồng nghĩa initialized.

Ví dụ allocator:

```text
allocate(size, align)
```

chỉ tạo storage.

Chưa có giá trị `T` hợp lệ.

---

# 21. Initialization

Low-level code có thể:

```axiom
unsafe {
    let p = alloc<T>()
    p.write(value)
}
```

Sau `write`, storage mới có initialized `T`.

Điều này cực kỳ quan trọng cho:

```text
Vec
Box
Arena
allocator
FFI
```

---

# 22. Double initialization

Nếu storage đã chứa live `T`:

```axiom
p.write(new_value)
```

không phải mặc định safe.

Có thể cần:

```text
drop old value
```

trước khi overwrite.

---

# 23. `MaybeUninit`

Nên có library/core primitive dạng:

```text
MaybeUninit<T>
```

nhưng semantic primitive tối thiểu:

```text
UNINITIALIZED
INITIALIZED
```

phải được compiler hiểu.

---

# 24. Không đọc uninitialized memory

```axiom
unsafe {
    let x = p.read()
}
```

nếu storage chưa initialized → invalid operation.

Axiom không biến uninitialized bytes thành arbitrary valid `T`.

---

# 25. Byte representation

Axiom phân biệt:

```text
value of T
```

và:

```text
bytes representing T
```

Dùng:

```text
Bytes
```

hoặc raw byte view.

---

# 26. `bit_cast`

Đã định nghĩa:

```axiom
let y = bit_cast::<U>(x)
```

`bit_cast` là reinterpretation của representation, không phải semantic conversion.

Điều kiện:

```text
size(U) == size(T)
```

và representation phải hợp lệ cho `U`.

Nếu không chứng minh được → unsafe hoặc compile error tùy trường hợp.

---

# 27. `as` khác `bit_cast`

```text
as
    semantic conversion

bit_cast
    representation reinterpretation
```

Ví dụ:

```axiom
let x: u32 = 10
let y: f32 = bit_cast(x)
```

không giống:

```axiom
let y = x as f32
```

---

# 28. Không có `transmute`

Axiom không có primitive kiểu:

```text
transmute<T,U>(x)
```

vì quá dễ biến mọi representation/lifetime invariant thành opaque operation.

Thay vào đó:

```text
as
bit_cast
ptr_cast
addr_cast
reinterpret_bytes
```

mỗi primitive có semantic contract riêng.

---

# 29. Pointer cast

```axiom
ptr_cast::<U>(p)
```

cho:

```text
*const T → *const U
*mut T → *mut U
```

nhưng phải tôn trọng:

```text
alignment
layout
validity
provenance
```

và thường là unsafe.

---

# 30. Alignment

Mọi typed access có alignment requirement.

Compiler biết:

```text
alignof(T)
```

Nếu pointer không aligned:

```text
p: *mut T
```

thì:

```text
p.read()
```

không hợp lệ.

---

# 31. Unaligned access

Axiom nên cung cấp explicit:

```axiom
unsafe {
    p.read_unaligned()
    p.write_unaligned(value)
}
```

thay vì ép programmer cast qua byte array.

Compiler backend có thể generate:

```text
unaligned load/store
```

hoặc sequence tương ứng.

---

# 32. `@repr(packed)`

Struct:

```axiom
@repr(packed)
struct Header {
    a: u8
    b: u32
}
```

không được tự động tạo aligned reference tới `b`.

Compiler phải:

```text
generate unaligned access
```

hoặc yêu cầu explicit unsafe operation.

---

# 33. Volatile

Axiom cung cấp:

```axiom
unsafe {
    volatile_read(p)
    volatile_write(p, value)
}
```

Volatile dùng cho:

```text
MMIO
device registers
memory-mapped hardware
special hardware-visible memory
```

---

# 34. Volatile không phải atomic

Rất quan trọng:

```text
volatile
    compiler-observable memory access

atomic
    concurrency synchronization
```

Không thay thế nhau.

---

# 35. Volatile không tạo happens-before

Ví dụ:

```text
volatile_write(...)
```

không tự đảm bảo thread khác nhìn thấy data theo memory model.

Nếu cần synchronization:

```text
Atomic
Fence
Lock
```

phải dùng mechanism phù hợp.

---

# 36. MMIO

System code:

```axiom
let status: *const u32 = addr_cast(0xFFFF0000)

let x = volatile_read(status)
```

là use case hợp lệ của unsafe.

Axiom không cần biết địa chỉ đó thuộc hardware nào.

---

# 37. Device memory

GPU/device memory có address-space semantics riêng.

Không được coi:

```text
*mut T
```

ở host:

```text
```

và device pointer:

```text
```

là cùng một semantic type nếu target phân biệt address spaces.

Đây sẽ kết nối trực tiếp với Part XX GPU.

---

# 38. Address spaces

Target có thể có:

```text
Host
Device
Shared
Local
Constant
External
```

Raw pointer nên mang address-space metadata ở compiler/LIR nếu target cần.

Source syntax không nhất thiết phải expose mọi address space.

---

# 39. Inline assembly

Axiom cần escape hatch:

```axiom
unsafe asm {
    ...
}
```

Nhưng inline asm phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

Không được xem asm là opaque function không có side effects.

---

# 40. Assembly constraints

Conceptually:

```axiom
unsafe asm(
    "..."
    inputs(...)
    outputs(...)
    clobbers(...)
)
```

Exact syntax có thể khóa ở target/backend spec.

---

# 41. Compiler phải biết asm effects

Ví dụ asm có:

```text
memory clobber
```

compiler không được reorder memory access qua nó như một pure operation.

---

# 42. Register constraints

Inline asm có thể yêu cầu:

```text
register
specific register class
immediate
memory
```

Target backend chịu trách nhiệm validate.

---

# 43. Target-specific asm

Không nên cố universalize assembly syntax.

Ví dụ:

```text
x86 asm
ARM asm
RISC-V asm
```

khác nhau.

Axiom Core chỉ định semantics.

Target module định nghĩa syntax/constraints.

---

# 44. Intrinsics

Compiler intrinsics dùng cho operations mà library không thể biểu diễn hiệu quả:

```text
simd
bit operations
cpu instructions
fence
prefetch
saturating instructions
carry operations
```

Ví dụ:

```text
intrinsic.clz(x)
intrinsic.popcount(x)
```

---

# 45. Intrinsic không phải runtime call

Compiler có thể lower:

```text
clz(x)
```

thành:

```text
LZCNT
CLZ
software sequence
```

tùy target.

---

# 46. Intrinsic semantics phải target-independent nếu có thể

Ví dụ:

```text
count_ones(u64)
```

nên có semantic definition độc lập target.

Backend chọn implementation.

---

# 47. Target-specific intrinsic

Nếu thật sự target-specific:

```text
x86.sse42(...)
arm.neon(...)
riscv.v(...)
```

phải explicit.

Không để source portable vô tình phụ thuộc CPU.

---

# 48. CPU feature detection

Compiler có thể hỗ trợ:

```text
@target_feature("avx2")
```

nhưng function contract phải rõ.

Không gọi function yêu cầu AVX2 trên CPU không hỗ trợ nếu không có dispatch.

---

# 49. Runtime CPU dispatch

Library có thể làm:

```text
baseline implementation
optimized implementation
CPU feature selection
```

Axiom compiler không cần runtime dispatch bắt buộc.

---

# 50. Memory fences

Fences đã thuộc atomic memory model:

```text
fence(Acquire)
fence(Release)
fence(SeqCst)
```

Unsafe không được phép thay đổi semantics của fence.

---

# 51. Compiler fence

Có thể có:

```text
compiler_fence(...)
```

khác với hardware memory fence.

```text
compiler fence
    ↓
compiler reordering constraint

atomic fence
    ↓
machine memory-order semantics
```

---

# 52. Cache operations

Các primitive như:

```text
prefetch
cache_flush
cache_invalidate
```

là target/system intrinsic.

Không đưa thành universal memory semantic nếu hardware không hỗ trợ.

---

# 53. DMA

DMA là một ví dụ rất quan trọng.

CPU memory:

```text
buffer
```

có thể đồng thời được:

```text
CPU
DMA device
```

truy cập.

Compiler không thể chỉ dựa trên CPU alias model để hiểu toàn bộ.

System API phải tạo explicit ownership/synchronization contract:

```text
CPU owns buffer
       ↓
submit DMA
       ↓
device owns buffer
       ↓
completion event
       ↓
CPU ownership restored
```

---

# 54. Device ownership

Đây là mở rộng tự nhiên của ownership model:

```text
CPU ownership
Device ownership
```

Ownership semantic vẫn có thể giữ:

```text
one exclusive owner
```

dù owner là execution domain khác.

---

# 55. Unsafe API nên tạo safe abstraction

Ví dụ allocator:

```text
unsafe allocate_raw()
```

nhưng public API:

```text
Box<T>
Vec<T>
```

phải safe.

Pattern:

```text
unsafe implementation
        ↓
prove invariant once
        ↓
safe abstraction
```

Đây là cách Axiom có thể xây standard library mạnh mà không biến mọi application thành unsafe.

---

# 56. `unsafe fn`

Một function có thể yêu cầu caller chịu trách nhiệm:

```axiom
unsafe fn from_raw(p: *mut T) -> Box<T>
```

Caller phải:

```axiom
unsafe {
    Box.from_raw(p)
}
```

---

# 57. Unsafe function contract

Axiom nên hỗ trợ documentation/semantic contract:

```text
Requires:
    p points to valid T
    p is uniquely owned
    p satisfies alignment
```

Compiler có thể dùng contract cho tooling/static analysis.

Nhưng contract không tự biến thành proof.

---

# 58. Unsafe block nhỏ hơn tốt hơn

Khuyến nghị:

```axiom
let value = unsafe {
    p.read()
}
```

thay vì:

```axiom
unsafe {
    300 lines
}
```

Compiler/tooling có thể hiển thị:

```text
unsafe boundary
```

trên IDE.

---

# 59. Unsafe contamination

Một function gọi unsafe API không nhất thiết phải trở thành unsafe nếu nó tự chứng minh/encapsulate invariant.

Ví dụ:

```axiom
fn get(i: usize) -> T {
    if i < len {
        unsafe {
            raw_get(i)
        }
    }
}
```

Public `get` vẫn safe nếu implementation đảm bảo invariant.

---

# 60. Đây là cách xây Vec

Conceptually:

```text
Vec<T>
 ├── ptr: raw storage
 ├── len
 └── cap
```

Internally:

```text
unsafe
```

Public:

```text
safe
```

Compiler vẫn hiểu:

```text
ownership
Drop
views
relocation
```

ở semantic level.

---

# 61. Raw pointer không ngăn compiler optimization

Compiler được phép optimize unsafe code theo semantics mà programmer đã cam kết.

Nếu programmer vi phạm unsafe contract:

```text
program has invalid behavior
```

Compiler không phải bảo vệ khỏi mọi lỗi unsafe.

---

# 62. Nhưng compiler không được coi mọi unsafe là UB tùy tiện

Axiom cần phân biệt:

```text
defined semantics
implementation-defined
target-defined
invalid unsafe precondition
```

Không biến mọi thứ thành:

```text
"anything can happen"
```

vì như vậy sẽ phá debugging và compiler engineering.

---

# 63. Unsafe violation

Nếu unsafe operation có precondition:

```text
p must be aligned
```

và programmer vi phạm:

```text
```

thì behavior thuộc:

```text
invalid unsafe operation
```

Compiler không có obligation giữ semantics.

Nhưng diagnostic/sanitizer có thể phát hiện.

---

# 64. Sanitizer

Toolchain có thể cung cấp:

```text
ASan-like
UBSan-like
ThreadSanitizer-like
alignment checks
pointer checks
```

nhưng không phải Core runtime.

---

# 65. FFI pointer ownership

Khi nhận:

```text
*mut CThing
```

Axiom không tự biết:

```text
who owns it
who frees it
whether borrowed
whether thread-safe
```

Wrapper phải encode contract.

---

# 66. `extern` boundary

Ví dụ:

```axiom
extern "C" fn malloc(size: usize) -> *mut u8
```

Raw pointer không tự trở thành:

```text
Box<u8>
```

Caller phải dùng đúng allocator contract.

---

# 67. Allocator domain

Không được:

```text
malloc()
 ↓
Box<T>
 ↓
Axiom allocator deallocate()
```

nếu allocator domains khác nhau.

Đây là invariant đã freeze:

```text
AMEM-50
AMEM-51
```

---

# 68. Freeing foreign memory

Wrapper phải encode:

```text
foreign_free(p)
```

thay vì để Drop mặc định gọi Axiom allocator.

---

# 69. C-compatible pointer wrappers

Có thể:

```axiom
struct CHandle {
    raw: *mut CThing
}
```

với:

```text
Drop → c_free
```

nếu ownership contract rõ.

---

# 70. Unsafe và Drop

Drop implementation có thể dùng unsafe internally.

Ví dụ:

```text
Vec.Drop
    ↓
unsafe deallocate(ptr)
```

Nhưng public semantics vẫn:

```text
deterministic cleanup
```

---

# 71. Unsafe và Send/Share

Một raw pointer không tự động:

```text
Send
Share
```

vì pointer không mang đủ lifetime/alias/synchronization proof.

Wrapper phải explicit contract.

---

# 72. Atomic pointer

```text
Atomic<*mut T>
```

có thể tồn tại ở system layer.

Nhưng:

```text
atomic pointer
```

không chứng minh:

```text
target object alive
```

Đã freeze:

```text
AATOM-31
```

---

# 73. ABA

Atomic pointer không giải quyết:

```text
A → B → A
```

ABA problem.

Memory reclamation phải dùng:

```text
generation
hazard pointer
epoch
tagged pointer
```

theo library/system layer.

---

# 74. Safe pointer abstraction

Axiom nên khuyến khích:

```text
Handle<T>
Box<T>
view<T>
mut_view<T>
Arc<T>
Weak<T>
```

thay vì raw pointer trong application code.

Raw pointer chủ yếu dành cho:

```text
OS
driver
allocator
FFI
runtime
compiler
embedded
JIT
GPU
```

---

# 75. Core Unsafe Surface

Tóm lại:

```text
unsafe
├── raw pointer
│   ├── read
│   ├── write
│   ├── arithmetic
│   └── cast
│
├── address
│   ├── pointer → integer
│   └── integer → pointer
│
├── representation
│   ├── bit_cast
│   └── reinterpret
│
├── memory
│   ├── uninitialized
│   ├── unaligned
│   └── volatile
│
├── hardware
│   ├── MMIO
│   ├── device memory
│   └── intrinsics
│
└── machine
    └── inline asm
```

---

# 76. Các thứ `unsafe` KHÔNG được làm

`unsafe` không được:

```text
disable type checking
disable ownership state tracking
disable Drop insertion
disable ABI checking
disable atomic semantics
disable control-flow validation
disable initialization analysis where provable
```

---

# 77. Nguyên tắc cực kỳ quan trọng

Axiom không có:

```text
unsafe = C mode
```

Mà:

```text
unsafe = controlled escape hatch
```

Đây là khác biệt lớn với việc đơn giản chỉ thiết kế một ngôn ngữ "C nhưng có syntax đẹp".

---

# 78. Invariants chính thức

### AUNSAFE-20 — Unsafe Relaxes Specific Proof Obligations

### AUNSAFE-21 — Unsafe Does Not Disable Type Checking

### AUNSAFE-22 — Unsafe Does Not Disable Ownership Semantics

### AUNSAFE-23 — Raw Pointers Do Not Imply Ownership

### AUNSAFE-24 — Raw Pointer Dereference Requires Unsafe

### AUNSAFE-25 — Raw Pointer Arithmetic Requires Unsafe

### AUNSAFE-26 — Raw Pointer Validity Is A Programmer Contract

### AUNSAFE-27 — Null Is Not A Safe Core Value

### AUNSAFE-28 — Address Is Distinct From Pointer Provenance

### AUNSAFE-29 — Integer-to-Pointer Conversion Requires Explicit Unsafe Semantics

### AUNSAFE-30 — Pointer-to-Integer Conversion Does Not Preserve Safe Capability

### AUNSAFE-31 — Pointer Cast Is Distinct From Numeric Conversion

### AUNSAFE-32 — Typed Access Requires Valid Alignment

### AUNSAFE-33 — Unaligned Access Is Explicit

### AUNSAFE-34 — Allocation Does Not Imply Initialization

### AUNSAFE-35 — Uninitialized Values Cannot Be Read As Valid Values

### AUNSAFE-36 — `bit_cast` Is Representation Reinterpretation

### AUNSAFE-37 — `bit_cast` Is Distinct From Semantic Conversion

### AUNSAFE-38 — Volatile Is Not Atomic Synchronization

### AUNSAFE-39 — Volatile Does Not Establish Happens-Before

### AUNSAFE-40 — Inline Assembly Has Explicit Machine Effects

### AUNSAFE-41 — Intrinsics Have Defined Semantic Contracts

### AUNSAFE-42 — Target-Specific Intrinsics Are Explicitly Target-Specific

### AUNSAFE-43 — Unsafe APIs Must State Required Invariants

### AUNSAFE-44 — Unsafe Abstractions May Encapsulate Safe Interfaces

### AUNSAFE-45 — Safe APIs May Internally Use Unsafe Implementations

### AUNSAFE-46 — Foreign Allocation Domains Must Not Be Mixed Implicitly

### AUNSAFE-47 — Raw Pointers Do Not Imply Send Or Share

### AUNSAFE-48 — Atomic Pointers Do Not Establish Object Lifetime

### AUNSAFE-49 — Unsafe Does Not Solve ABA Or Memory Reclamation

### AUNSAFE-50 — Device Memory Is Distinct From Ordinary Host Memory When Target Requires

### AUNSAFE-51 — Unsafe Violations Do Not Become Arbitrary Safe Semantics

### AUNSAFE-52 — Sanitizers Are Tooling, Not Core Safety Semantics

### AUNSAFE-53 — Unsafe Boundaries Are Explicit In Source

### AUNSAFE-54 — Compiler Optimizations Must Preserve Defined Unsafe Semantics

### AUNSAFE-55 — Undefined Unsafe Preconditions Must Not Be Used As Safe Program Assumptions

---

# Kết quả quan trọng của Part XVIII

Đến đây Axiom đã có hai tầng rất rõ:

```text
                    AXIOM
                      │
          ┌───────────┴───────────┐
          │                       │
        SAFE                   UNSAFE
          │                       │
 ownership/capability       raw machine access
 Send/Share                 pointers
 Drop                       addresses
 atomics                    volatile
 Result                     asm
 traits                     MMIO
 async                      FFI internals
          │                       │
          └───────────┬───────────┘
                      │
                  native code
```

Và quan trọng nhất:

> **Unsafe code có thể làm mọi thứ cần thiết ở tầng hệ thống, nhưng safe code không phải gánh complexity của tầng đó.**

---

# Part XIX — FFI · ABI · C Interop · Foreign Ownership

Phần tiếp theo cần khóa một vấn đề cực lớn đối với mục tiêu của Axiom:

```text
Axiom
   ↕
C
   ↕
OS API
   ↕
native libraries
```

Đặc biệt sẽ xử lý:

- `extern "C"`
- C structs
- C enums
- unions
- function pointers
- callbacks
- variadic functions
- ABI ownership
- allocator boundary
- string/bytes boundary
- error boundary
- panic boundary
- thread boundary
- `dyn Trait` không được leak nhầm qua C ABI
- generic không được leak nhầm qua stable ABI
- `@repr(C)`
- symbol export
- import/export
- static/dynamic linking
- calling convention
- platform ABI
- C header generation
- Axiom API gọi từ C
- C API gọi vào Axiom
- và đặc biệt: **làm thế nào để Axiom cuối cùng tự build native binary mà không cần C compiler**.