# BOOTSTRAP-080 — Axiom Security, Safety, Undefined Behavior & Trusted Unsafe Model

**Trạng thái: FROZEN**

Đây là một trong những phần quan trọng nhất của Axiom, vì nó quyết định ranh giới giữa:

- **safe code** — compiler có thể bảo đảm các invariant quan trọng;
- **unsafe code** — programmer được phép thao tác gần máy hơn;
- **undefined behavior** — những gì compiler không được phép suy diễn thành semantics tùy ý;
- **implementation-defined / target-defined behavior**;
- và **optimizer assumptions**.

Mục tiêu của Axiom:

> **Safe code phải mạnh hơn C/C++ về safety, nhưng unsafe code phải đủ thấp-level để viết OS, driver, runtime, compiler, allocator, GPU backend và FFI.**

Đồng thời:

> **`unsafe` không phải là “tắt compiler”. Nó chỉ chuyển một số proof obligation từ compiler sang programmer/API contract.**

---

# 1. Ba tầng semantic

Axiom chia chương trình thành:

```text
SAFE
  │
  │ compiler proves invariants
  ▼
TRUSTED UNSAFE BOUNDARY
  │
  │ programmer establishes explicit machine-level preconditions
  ▼
MACHINE / SYSTEM BEHAVIOR
```

Không có khái niệm:

```text
unsafe = compiler bỏ qua tất cả
```

---

# 2. Safe Axiom phải bảo đảm gì?

Trong safe code, compiler phải đảm bảo ít nhất:

```text
No use-after-free
No double-drop
No dangling view
No invalid ownership transfer
No conflicting mutable capabilities
No safe data race
No out-of-bounds access
No use of moved value
No invalid initialization state
No invalid safe UTF-8
No invalid safe enum state
No invalid safe type representation
```

Ngoài ra còn phải duy trì:

```text
Drop correctness
Send/Share correctness
async lifetime correctness
GPU storage/lifetime correctness
FFI wrapper contracts
```

---

# 3. Safe không có nghĩa là “không thể crash”

Ví dụ:

```ax id="q6v7qz"
panic("fatal invariant")
```

vẫn có thể kết thúc chương trình.

Hoặc:

```text id="7x9myf"
allocation failure
OS failure
GPU failure
external process failure
```

có thể xảy ra.

Safety nghĩa là:

> chương trình không được crash bằng cách phá vỡ memory/ownership/type invariants trong safe semantics.

---

# 4. Safe code không có UB memory corruption

Các hành vi như:

```text id="g4m0qj"
use-after-free
double-free
out-of-bounds write
invalid pointer dereference
data race
```

không phải một cách bình thường để safe code có thể đạt tới.

Nếu compiler gặp:

```ax id="x7k3dz"
buffer[i]
```

thì hoặc:

```text
prove i < len
```

hoặc:

```text
emit bounds check
```

hoặc:

```text
reject / require unsafe unchecked API
```

---

# 5. Unsafe là một semantic boundary

Ví dụ:

```ax id="x1e9r6"
unsafe {
    *ptr
}
```

không có nghĩa:

```text
mọi thứ bên trong đều hợp lệ.
```

Nó chỉ nói:

> programmer chấp nhận trách nhiệm đối với precondition của phép raw-memory operation.

Compiler vẫn kiểm tra:

```text
type correctness
control flow
initialized state
basic IR validity
ABI consistency
```

và những invariant khác không được phép bị phá chỉ vì `unsafe`.

---

# 6. `unsafe fn`

Có thể định nghĩa:

```ax id="0n0j8k"
unsafe fn from_raw(ptr: *const u8, len: usize) -> view<u8>
```

Ý nghĩa:

> caller phải đảm bảo preconditions mà API yêu cầu.

Nhưng bên trong compiler vẫn xử lý type semantics bình thường.

---

# 7. SAFETY contract

Axiom không đưa full design-by-contract system vào Core v1.

Nhưng unsafe API nên có documentation convention:

```ax id="4e5y7f"
/// SAFETY:
/// ptr must reference at least len initialized bytes.
/// The region must remain valid for the returned view lifetime.
unsafe fn from_raw(...)
```

Compiler/tooling có thể đọc contract.

Không biến documentation thành proof tự động.

---

# 8. Unsafe không tự tạo safety facts vô hạn

Ví dụ:

```ax id="3g0v4w"
unsafe {
    let p = ...
}
```

không khiến compiler kết luận:

```text
mọi pointer đều valid
mọi alias đều disjoint
mọi lifetime đều infinite
```

Chỉ các precondition cụ thể được established mới trở thành trusted facts.

---

# 9. Trusted fact

Mô hình:

```text id="8w9jhm"
unsafe operation
       │
       ▼
establish contract C
       │
       ▼
trusted semantic fact
       │
       ▼
normal verifier resumes
```

Ví dụ:

```text id="5yl0h4"
raw pointer
  ↓
unsafe validation
  ↓
valid region [p, p+n)
  ↓
mut_view<u8>
  ↓
ordinary safe analysis
```

---

# 10. Safe verification resumes

Đây là invariant rất quan trọng:

> Unsafe boundary không phải vùng “miễn kiểm tra” kéo dài đến hết function.

Ví dụ:

```ax id="8efq22"
unsafe {
    let buffer = make_view(ptr, len)
}

process(buffer)
```

Sau khi `buffer` trở thành capability hợp lệ, verifier lại kiểm tra:

```text
lifetime
alias
mutation
escape
Send
Share
Drop
```

như bình thường.

---

# 11. Pointer provenance

Axiom phân biệt:

```text id="y2p3b8"
numeric address
```

và:

```text id="6m5b7f"
pointer provenance
```

Ví dụ:

```ax id="1j9xj0"
let n: usize = 0x1000
```

không tự động trở thành:

```text
*mut T
```

hợp lệ.

---

# 12. Integer → pointer

Operation kiểu:

```ax id="z4p7q1"
address_to_ptr<T>(address)
```

là unsafe/system.

Compiler không được giả định rằng mọi integer address là pointer hợp lệ.

---

# 13. Pointer → integer

Ngược lại:

```ax id="p2h9x1"
ptr_to_address(p)
```

có thể cung cấp machine address.

Nhưng sau đó:

```text
integer → pointer
```

không tự động khôi phục provenance.

---

# 14. Pointer arithmetic

Raw pointer arithmetic:

```ax id="m5c8z2"
p + offset
p - offset
```

là unsafe.

Compiler không cần theo dõi arbitrary pointer arithmetic như safe capability arithmetic.

Safe code dùng:

```text id="5z0y2c"
view
mut_view
slice/range APIs
```

---

# 15. Dereference

```ax id="h4x8n1"
*p
```

với raw pointer là unsafe.

Điều kiện tối thiểu:

```text id="1s8g7v"
valid provenance
correct alignment
initialized value
valid lifetime
correct type
accessible memory
```

---

# 16. Alignment

Ví dụ:

```text id="7j0h5p"
u64
```

không được mặc định đọc từ arbitrary byte address.

Nếu address không aligned:

```text id="x9c2g6"
unaligned_read
unaligned_write
```

phải là explicit operation.

---

# 17. Packed structures

```ax id="q3r7p8"
@repr(packed)
```

làm alignment contract thay đổi.

Do đó field access có thể trở thành:

```text id="7a0d2q"
unaligned access
```

và phải được xử lý theo unsafe/system semantics.

---

# 18. Uninitialized memory

Axiom phân biệt:

```text id="j2p8s1"
allocated storage
```

với:

```text id="g6x1r9"
initialized value
```

Không được đọc:

```text id="a7d4m3"
UNINIT → normal T
```

---

# 19. `MaybeUninit<T>`

Low-level code có thể cần:

```ax id="p8r1z3"
MaybeUninit<T>
```

hoặc abstraction tương đương.

Semantics:

```text id="4c8x0y"
UNINIT
INIT
```

được compiler MIR theo dõi.

---

# 20. Partial initialization

Có thể:

```text id="v9k2q1"
storage for struct
field A initialized
field B uninitialized
```

nhưng chỉ khi compiler biết chính xác state.

Drop chỉ chạy trên những phần đã initialized.

---

# 21. Byte manipulation

Không được giả định:

```text id="r7y3n6"
copy bytes → valid T
```

Ví dụ:

```text
bytes = arbitrary 4 bytes
bitcast<u32>
```

có thể hợp lệ.

Nhưng:

```text
arbitrary bytes → enum
```

không tự động hợp lệ.

---

# 22. Invalid enum

Nếu:

```ax id="j5x7p2"
enum Color {
    Red
    Green
    Blue
}
```

thì machine representation có thể chứa bit pattern không tương ứng variant.

Safe Axiom không cho tạo một `Color` invalid.

Raw byte reinterpretation có thể cần unsafe.

---

# 23. Invalid boolean

Tương tự:

```text id="h7q3m9"
bool
```

chỉ có:

```text
true
false
```

Arbitrary byte `2` không trở thành một safe bool hợp lệ.

---

# 24. Invalid UTF-8

`String` và `Str` đã có invariant:

```text id="p8m4r1"
valid UTF-8
```

Unsafe byte mutation có thể tạm thời phá invariant.

Nhưng trước khi đưa trở lại safe abstraction:

```text id="r2v7k5"
UTF-8 validity
```

phải được re-established.

---

# 25. Type punning

Không cho phép tùy tiện:

```text id="h3n9w2"
reinterpret T as U
```

chỉ vì:

```text same size
```

Phải phân biệt:

```text id="k7x2p8"
CAST
BITCAST
RAW MEMORY ACCESS
```

---

# 26. `bitcast`

`bitcast<T>` hợp lệ nếu:

```text id="c4m9v1"
size compatible
alignment compatible
representation valid
```

Nếu target representation có invalid bit patterns:

```text id="d8q2s5"
bitcast
```

phải bị reject hoặc đưa vào unsafe API.

---

# 27. Object lifetime

Memory tồn tại không đồng nghĩa object tồn tại.

Ví dụ:

```text id="f6x1z3"
allocated bytes
```

có thể chưa có:

```text
T object
```

Điều này rất quan trọng cho placement construction / allocators / FFI.

---

# 28. Storage lifetime

Axiom tiếp tục giữ ba khái niệm:

```text id="w4j9q2"
Value lifetime
Resource lifetime
Storage lifetime
```

và thêm:

```text id="n5x3r8"
Object validity lifetime
```

Một vùng memory có thể còn tồn tại nhưng object bên trong đã bị destroyed.

---

# 29. Use-after-destroy

Ngay cả khi:

```text id="a8y2m5"
storage vẫn allocated
```

thì access vào object đã Drop vẫn invalid.

Compiler verifier phải phân biệt:

```text id="q4v7z1"
storage exists
```

và:

```text
T is live
```

---

# 30. Data race

Safe Axiom không cho:

```text id="h1x8k4"
concurrent conflicting ordinary accesses
```

nếu không có synchronization.

Ví dụ:

```text
Thread A → WRITE x
Thread B → READ x
```

mà không có ordering/synchronization:

```text
reject
```

hoặc không thể tạo ra trong safe model.

---

# 31. Atomic không phải magic safety

```ax id="e7p3m9"
Atomic<u32>
```

cho phép concurrent atomic access.

Nhưng:

```text
atomic x
ordinary mutable alias x
```

không tự động trở thành hợp lệ.

Atomicity không biến:

```text
shared mutable object
```

thành thread-safe abstraction.

---

# 32. Volatile

Volatile:

```text id="x6j2r5"
volatile_read
volatile_write
```

là machine/hardware semantics.

Nó không có nghĩa:

```text
synchronization
atomicity
thread safety
```

---

# 33. FFI boundary

FFI là một trong những nơi unsafe phổ biến nhất.

Ví dụ:

```ax id="v1n8s4"
extern "C" fn c_function(...)
```

Foreign function có thể vi phạm những assumption mà Axiom không kiểm chứng được.

Do đó wrapper an toàn phải thiết lập:

```text id="q5m3x7"
ownership
lifetime
layout
aliasing
error
thread-safety
ABI
```

---

# 34. Foreign aliasing

Nếu C function nhận:

```text id="d3y7k2"
*mut T
```

compiler không được tự động giả định:

```text
noalias
```

trừ khi contract rõ ràng.

Mặc định:

```text id="s9x4q1"
foreign aliasing = UNKNOWN
```

---

# 35. Foreign callback

Callback phải đảm bảo:

```text id="j7c2v5"
function ABI
context validity
lifetime
thread-safety
reentrancy
```

Một callback pointer sống lâu hơn environment của closure là invalid.

Compiler/wrapper phải biểu diễn lifetime contract.

---

# 36. FFI ownership violation

Ví dụ foreign API trả:

```text id="m5z8q2"
char*
```

không có nghĩa:

```text
Axiom owns memory
```

Ownership phải explicit:

```text id="c1x7r4"
Borrowed
OwnedByAxiom
OwnedByForeign
```

---

# 37. Double-free qua FFI

Nếu foreign API yêu cầu:

```text
foreign_free(ptr)
```

thì Axiom không được đồng thời:

```text id="k8p2s5"
Drop(ptr)
```

nếu ownership contract không cho phép.

Resource ownership graph phải biểu diễn điều này.

---

# 38. ABI mismatch

Một trong những lỗi nghiêm trọng nhất:

```text id="q4x8n2"
Axiom declaration
        ≠
foreign ABI
```

Ví dụ:

```text
wrong calling convention
wrong struct layout
wrong integer width
wrong alignment
wrong variadic convention
```

đây là unsafe/FFI contract violation.

---

# 39. Calling convention

Compiler phải kiểm tra explicit:

```text id="v8j3q6"
extern "C"
extern "system"
extern "Axiom"
```

hoặc target-specific ABI.

Không đoán calling convention từ function type.

---

# 40. Variadic FFI

Variadic:

```text id="f3m7x1"
printf(...)
```

không thuộc safe general function semantics.

C variadics chỉ ở:

```text id="q9z2v5"
FFI/system layer
```

và phải tuân ABI.

---

# 41. Undefined behavior

Axiom cần định nghĩa UB rất hẹp.

Safe program:

> **không có memory/lifetime/type/data-race UB theo Core semantics.**

Unsafe program có thể violate machine-level preconditions.

Nhưng compiler không nên dùng “UB” như một cái cớ để tùy tiện tối ưu những thứ mà Axiom đã định nghĩa.

---

# 42. Defined behavior

Ưu tiên:

```text id="n8q3v6"
DEFINED
```

cho:

- integer arithmetic
- overflow modes
- casts
- enum semantics
- ownership
- capabilities
- control flow
- memory access
- concurrency
- async
- Drop.

---

# 43. Implementation-defined

Một số thứ:

```text id="m2x7r9"
target ABI
struct default layout
instruction selection
register allocation
object format details
```

có thể implementation/target-defined.

Nhưng compiler phải document/encode contract.

---

# 44. Unspecified behavior

Có thể tồn tại ở nơi semantics cho phép nhiều kết quả hợp lệ.

Ví dụ:

```text id="b5r8k2"
HashMap iteration order
```

nếu API không đảm bảo ordering.

Nhưng:

> unspecified ≠ undefined.

Compiler vẫn phải tạo một behavior nằm trong tập behavior được specification cho phép.

---

# 45. Optimizer assumptions

Optimizer chỉ được sử dụng:

```text id="w6z3p1"
language facts
verified facts
explicit contracts
target contracts
```

Không được tự tạo:

```text
NoAlias
NoOverflow
ValidPointer
NoNaN
NoRace
```

chỉ vì điều đó giúp optimize.

---

# 46. Safety facts vs optimization facts

Ví dụ:

```text id="p3x7m2"
Verifier:
    regions DISJOINT
```

→ optimizer có thể tạo:

```text id="k8v1q5"
NoAlias
```

Nhưng:

```text id="s4y9n3"
Optimizer:
    "probably disjoint"
```

không thể trở thành safety fact.

---

# 47. Unsafe không phải optimization switch

Không được dùng:

```ax id="z6m2q8"
unsafe {
    ...
}
```

để yêu cầu compiler:

```text
disable bounds checks everywhere
disable alias analysis
disable ownership
disable initialization checking
```

Muốn unchecked operation:

```text id="r1x5v7"
unchecked_index
```

phải là operation cụ thể.

---

# 48. Unchecked operations

Ví dụ library/system:

```ax id="a7k3p9"
unsafe fn get_unchecked(v: view<T>, i: usize) -> T
```

Contract:

```text
i < v.length
```

Compiler không emit bounds check **cho operation đó**, nhưng chỉ trong phạm vi operation.

Không làm toàn function unsafe optimization mode.

---

# 49. Safe wrapper pattern

Library nên xây:

```ax id="f4x8q2"
safe API
   ↓
prove/check precondition
   ↓
unsafe primitive
   ↓
return safe abstraction
```

Đây sẽ là pattern cực kỳ quan trọng trong:

- Vec
- Slice
- Allocator
- OS
- GPU
- SIMD
- FFI.

---

# 50. Example: Vec indexing

Safe:

```ax id="e8m2s5"
items[i]
```

Compiler:

```text
prove i < len
    OR
bounds check
```

Unsafe primitive:

```ax id="j4x7n1"
items.get_unchecked(i)
```

requires caller contract.

---

# 51. Example: raw allocation

System allocator có thể:

```ax id="u5q2m8"
unsafe fn alloc_raw(size: usize, align: usize) -> *mut u8
```

Nhưng safe wrapper:

```ax id="c7z1p4"
Box<T>
Buffer<T>
Vec<T>
```

sẽ thiết lập:

```text
allocation validity
alignment
initialization
Drop
ownership
capacity
```

---

# 52. Sanitizer

Axiom nên có sanitizer tooling nhưng sanitizer **không phải semantic layer**.

Có thể:

```text id="v3x8m1"
axiom build --sanitize=address
axiom build --sanitize=thread
axiom build --sanitize=memory
axiom build --sanitize=undefined
```

tùy backend/platform.

---

# 53. Sanitizer không sửa semantics

Nếu chương trình có:

```text id="s8q2k5"
unsafe violation
```

sanitizer có thể:

```text
detect
report
abort
```

nhưng không biến behavior thành defined behavior.

---

# 54. Debug mode

Debug có thể thêm:

```text id="k2m7x4"
bounds instrumentation
overflow checks
assertions
sanitizer hooks
```

nhưng không được thay đổi semantics của chương trình hợp lệ.

---

# 55. Release mode

Release có thể loại bỏ:

```text id="q6z1p8"
bounds checks
overflow checks
assertions
```

**chỉ khi compiler chứng minh chúng không cần thiết** hoặc semantics của operation vốn không yêu cầu chúng.

Không được:

```text
debug = checked semantics
release = UB semantics
```

---

# 56. Hardware faults

Ví dụ:

```text id="n4x8p2"
page fault
illegal instruction
machine check
```

không tự động trở thành:

```text
Result<T,E>
```

Đó là machine/OS failure.

---

# 57. Panic vs trap

Axiom phân biệt:

```text id="m7q3v1"
panic
```

với:

```text id="c5x8n2"
trap/fault
```

Panic là language/runtime-defined failure.

Trap là machine-level termination/fault.

---

# 58. Bounds failure

Safe indexing nếu không chứng minh được:

```text id="z3r6k1"
index >= len
```

phải dẫn đến defined failure behavior:

```text
panic/trap
```

không memory corruption.

---

# 59. Arithmetic failure

Tương tự:

```text id="f8m2q4"
checked arithmetic
```

failure không trở thành arbitrary machine behavior.

Compiler có thể tối ưu check nếu proof tồn tại.

---

# 60. Lifetime violation

Một safe program không được tạo:

```text id="j5x9p2"
dangling view
```

Compiler phải reject.

Không được transform thành:

```text
"developer tự chịu trách nhiệm"
```

trừ khi operation đi qua unsafe boundary.

---

# 61. Capability invalidation

Nếu:

```text id="a3v7k8"
let v = view(x)
drop(x)
```

thì compiler reject vì:

```text id="s6q2m4"
owner destruction conflicts with live capability
```

Đây là một safety invariant, không phải optimization.

---

# 62. Relocation safety

Nếu:

```text id="n8x4r1"
let v = view(vec)
vec.push(...)
```

và push có thể relocate:

```text
reject
```

hoặc API phải đảm bảo operation không relocate.

Compiler không được “hy vọng Vec không move”.

---

# 63. Stable storage

Nếu programmer cần:

```text id="q1m7z5"
stable address
```

phải dùng storage abstraction có contract:

```text
StableBox
Arena
Pool
MMap
Pinned/device storage
```

Không biến raw pointer thành cách mặc định để giữ stable address.

---

# 64. Handle không phải capability

```ax id="v4x8n2"
Handle<Entity>
```

có thể tồn tại sau khi entity bị destroy.

Handle resolution phải kiểm tra:

```text id="p6r1k9"
generation
validity
ownership
capability
```

trước khi truy cập.

Đây là lý do generation handle rất hữu ích.

---

# 65. Safe handles

Một API:

```ax id="h2m7x4"
world.get(handle)
```

có thể trả:

```text id="j8q3n1"
Option<view<Entity>>
```

thay vì expose pointer.

Điều này cho phép game/GUI/database/runtime code có identity mà không phụ thuộc physical address.

---

# 66. Reentrancy

Unsafe/FFI callback có thể gây reentrancy:

```text id="s5x9k2"
Axiom → foreign → callback → Axiom
```

Không được mặc định giả định:

```text callback never happens
```

Nếu API không reentrant:

```text id="c3v7m1"
contract phải explicit
```

---

# 67. Thread-affinity

Một resource có thể:

```text id="p8n2q5"
!Send
```

hoặc:

```text id="x4m7r1"
!Share
```

Không được unsafe cast một cách tùy tiện thành Send/Share.

Compiler-derived properties vẫn phải được bảo toàn.

---

# 68. FFI thread safety

Foreign API:

```text id="j6q3z8"
```

không tự động được coi là thread-safe.

Wrapper phải cung cấp contract.

Nếu không biết:

```text id="v2x8m4"
conservative
```

---

# 69. Async unsafe

Một unsafe operation tạo capability/resource trước:

```text id="q7m1s5"
await
```

phải tuân async lifetime rules.

Unsafe không cho phép:

```text
dangling capability across await
```

một cách tự động.

---

# 70. GPU unsafe

Tương tự:

```text id="n3x8r2"
unsafe device pointer
```

không vô hiệu:

```text storage-domain verification
in-flight lifetime
GPU legality
```

---

# 71. DMA unsafe

DMA buffer có thể bị hardware truy cập ngoài CPU control flow.

Do đó unsafe DMA API phải thiết lập:

```text id="f5k2m9"
device ownership
completion
lifetime
cache/coherency contract
```

Không được Drop buffer khi DMA vẫn in-flight.

---

# 72. Memory-mapped I/O

MMIO access có:

```text id="x1q7v4"
volatile
alignment
device semantics
```

không dùng ordinary memory semantics.

---

# 73. Compiler barrier

Compiler barrier chỉ kiểm soát:

```text id="m8z3p6"
compiler reordering
```

không tự động tạo CPU memory ordering.

CPU fence là một semantics khác.

---

# 74. Unsafe assembly

Inline assembly:

```ax id="r4x9k2"
unsafe {
    asm(...)
}
```

phải khai báo:

```text id="p7m1v5"
inputs
outputs
clobbers
memory effects
control-flow effects
```

Nếu khai báo sai:

```text
unsafe contract violation
```

Compiler không cần bảo vệ programmer khỏi mọi lỗi assembly.

---

# 75. Naked functions

```ax id="k3x8q1"
@naked
```

là system-level.

Compiler không tự thêm:

```text
prologue
epilogue
stack setup
```

nhưng ABI contract trở thành trách nhiệm của implementation/programmer.

---

# 76. Interrupt handlers

```ax id="v6m2r8"
@interrupt
```

có contract đặc biệt về:

```text
register state
calling convention
stack
reentrancy
concurrency
```

Không phải ordinary function.

---

# 77. Syscalls

Syscall wrapper có thể là:

```ax id="j1q7x4"
unsafe system primitive
```

nhưng standard library nên cung cấp safe wrappers:

```text id="m5z8p2"
File
Socket
Process
MMap
```

đã được chốt trong resource model.

---

# 78. Security boundary

Axiom không cố biến memory safety thành toàn bộ security.

Vẫn có:

```text id="s4x9k2"
logic bugs
authentication bugs
authorization bugs
cryptographic mistakes
TOCTOU
side channels
resource exhaustion
```

Safe memory model không giải quyết tất cả.

---

# 79. Side channels

Timing/cache/power side channels không thể được Core v1 bảo đảm tuyệt đối.

Nhưng:

```text id="n7q2m5"
constant-time crypto APIs
```

có thể nằm trong crypto/system libraries.

Compiler-specific guarantees có thể được thêm sau nếu thật sự cần.

---

# 80. TOCTOU

Safe ownership không tự ngăn:

```text id="c3x8v1"
check(path)
...
use(path)
```

file thay đổi giữa hai thao tác.

Đây là OS/resource semantics.

API nên cung cấp resource-handle based patterns thay vì path-based assumptions khi cần.

---

# 81. Resource exhaustion

Không có guarantee:

```text id="p6m2z8"
program cannot run out of memory
```

hoặc:

```text
cannot exhaust file descriptors
```

Các failure này phải được biểu diễn qua `Result`/explicit system behavior.

---

# 82. Panic safety

Panic phải giữ:

```text id="x4q7n1"
ownership invariants
Drop invariants
resource invariants
```

đã chốt ở Error Model.

---

# 83. Unsafe trong Drop

User-defined Drop không nên được phép tạo ra các invariant không thể kiểm chứng khiến destructor trở thành nguồn memory corruption trong safe code.

Nếu Drop chứa unsafe:

```text id="m8v3r5"
unsafe boundary
```

chỉ chịu trách nhiệm cho chính contract của Drop.

---

# 84. Destructor poisoning

Axiom không cần cơ chế kiểu:

```text id="k1x7q4"
object becomes poisoned after panic
```

ở Core.

Nếu library cần poisoning:

```text
Mutex
RwLock
resource wrapper
```

có thể định nghĩa riêng.

---

# 85. Type invariant pattern

Một type safe có thể duy trì invariant:

```ax id="z5m2p8"
struct NonZero(u32)
```

Constructor:

```ax id="j3x7q1"
fn new(x: u32) -> Option<NonZero>
```

Sau đó compiler tin:

```text
NonZero.0 != 0
```

theo type construction semantics.

Unsafe raw construction phải tái lập invariant.

---

# 86. Trusted constructors

Đây là pattern rất quan trọng:

```text id="v8q3m6"
unsafe raw construction
        ↓
validated invariant
        ↓
safe nominal type
```

Ví dụ:

```text
NonNull
NonZero
ValidUtf8
Aligned<T>
Initialized<T>
```

Không cần đưa tất cả thành primitive Core.

---

# 87. Invariant ownership

Một type invariant phải gắn với:

```text id="s2x9k4"
type construction
field visibility
methods
unsafe escape
```

Nếu field private:

```text
struct NonZero {
    value: u32
}
```

safe external code không thể tự tạo invalid state.

---

# 88. Representation contract và safety

`@repr(C)` không tự làm type FFI-safe.

Nó chỉ đảm bảo:

```text id="f7m2x8"
representation contract
```

Các invariant khác vẫn phải kiểm tra:

```text ownership
valid values
ABI
lifetime
```

---

# 89. Transparent types

```ax id="q3x8n1"
@repr(transparent)
struct UserId(u64)
```

cho phép ABI compatibility theo contract.

Nhưng:

```text UserId
```

vẫn là semantic distinct type.

---

# 90. Safe transmute

Axiom **không có general safe `transmute`**.

Nếu cần:

```text id="k5m1z7"
bitcast
raw pointer
union access
```

phải dùng primitive/API với điều kiện rõ ràng.

---

# 91. Union

C ABI unions cần support.

Nhưng:

```text id="x8q2r4"
union {
    a: u32
    b: f32
}
```

không mang semantic tag.

Đọc field sai active representation là unsafe.

Safe wrapper có thể cung cấp tagged abstraction.

---

# 92. Bitfields

Bitfields là ABI representation concern.

Không nên đưa bitfield semantics vào general struct syntax.

System/FFI representation:

```text id="m4v7p2"
@repr(C)
```

+ compiler/system declaration.

---

# 93. Safe union wrapper

Có thể xây:

```text id="j2x8q5"
enum
```

nếu cần safety.

Compiler có thể optimize enum thành union-like representation.

Đây là ví dụ:

> **semantic abstraction cao hơn physical representation.**

---

# 94. Unsafe doesn't leak automatically

Một function:

```ax id="c7m1z4"
unsafe fn low_level(...)
```

không khiến mọi caller unsafe nếu có:

```text id="n8x3q6"
safe wrapper
```

Do đó unsafe có thể được **cô lập ở library boundary**.

---

# 95. Unsafe surface minimization

Axiom library nên hướng tới:

```text id="p4q7m2"
large safe API
small unsafe implementation core
```

Ví dụ:

```text
Vec
 ├── 95% safe
 └── small raw allocation/indexing primitives

File
 ├── safe resource API
 └── small syscall/handle layer

GPU
 ├── safe buffer/view API
 └── unsafe driver boundary
```

---

# 96. Trusted core

Compiler và standard library có thể có một tập nhỏ:

```text id="x1m8r5"
trusted primitives
```

được audit đặc biệt.

Không nên có:

```text
unsafe everywhere
```

trong standard library.

---

# 97. Unsafe auditability

Tooling nên hỗ trợ:

```text id="k5z2q7"
axiom unsafe
```

để liệt kê:

```text
unsafe blocks
unsafe functions
FFI boundaries
raw pointer operations
inline asm
unchecked operations
repr(packed)
system intrinsics
```

và call graph liên quan.

---

# 98. AI-friendly safety diagnostics

Compiler diagnostic nên machine-readable:

```text id="v3x7n1"
{
    code: "ASAFE-042",
    kind: "CapabilityConflict",
    source: ...,
    facts: ...,
    required: ...,
    conflicting_region: ...
}
```

AI có thể hiểu:

```text
WRITE capability conflicts with READ capability
```

thay vì chỉ:

```text
borrow error
```

---

# 99. Safety philosophy

Axiom không theo hướng:

```text
C:
    programmer responsible for everything

Rust:
    programmer manually satisfies lifetime system
```

Mà theo:

```text
Axiom:

programmer
    ↓
express semantic intent
    ↓
compiler performs proof
    ↓
safe code
```

Chỉ khi programmer yêu cầu:

```text
machine-level operation
```

thì:

```text
unsafe boundary
```

xuất hiện.

Đây chính là:

> **Compiler Complexity Is Not Language Complexity.**

---

# 100. Frozen Safety Invariants

## `ASAFE-20..100`

**ASAFE-20** — Safe code must preserve Axiom memory-safety invariants.

**ASAFE-21** — Safe code cannot perform use-after-free.

**ASAFE-22** — Safe code cannot perform double destruction.

**ASAFE-23** — Safe code cannot create dangling capabilities.

**ASAFE-24** — Safe code cannot use moved values.

**ASAFE-25** — Safe code cannot create invalid ownership transfer.

**ASAFE-26** — Safe code cannot create conflicting mutable capabilities.

**ASAFE-27** — Safe code cannot create unsynchronized data races.

**ASAFE-28** — Safe indexed access cannot cause memory corruption.

**ASAFE-29** — Safe values cannot contain invalid initialization state.

**ASAFE-30** — Safe enum values must correspond to valid variants.

**ASAFE-31** — Safe bool values must be valid boolean states.

**ASAFE-32** — Safe UTF-8 abstractions preserve UTF-8 validity.

**ASAFE-33** — Safe type invariants must be established by valid construction.

**ASAFE-34** — Unsafe operations may establish trusted semantic preconditions.

**ASAFE-35** — Trusted facts are specific to their established contracts.

**ASAFE-36** — Unsafe does not disable ordinary type checking.

**ASAFE-37** — Unsafe does not disable ownership verification.

**ASAFE-38** — Unsafe does not disable capability verification.

**ASAFE-39** — Unsafe does not disable initialization verification.

**ASAFE-40** — Safe verification resumes after a valid unsafe boundary.

**ASAFE-41** — Raw pointers do not imply ownership.

**ASAFE-42** — Raw pointers do not imply safe capabilities.

**ASAFE-43** — Integer addresses do not automatically become valid pointers.

**ASAFE-44** — Pointer provenance is distinct from numeric address.

**ASAFE-45** — Raw pointer arithmetic is unsafe/system-level.

**ASAFE-46** — Raw pointer dereference is unsafe/system-level.

**ASAFE-47** — Raw pointer access requires valid provenance.

**ASAFE-48** — Raw pointer access requires valid lifetime.

**ASAFE-49** — Raw pointer access requires valid alignment.

**ASAFE-50** — Raw pointer access requires valid initialization.

**ASAFE-51** — Raw pointer access requires valid type representation.

**ASAFE-52** — Uninitialized storage is distinct from initialized values.

**ASAFE-53** — Reading uninitialized storage as a normal value is invalid.

**ASAFE-54** — Partial initialization state is explicitly tracked.

**ASAFE-55** — Drop applies only to initialized live values.

**ASAFE-56** — Raw byte copying does not imply semantic value validity.

**ASAFE-57** — Bitwise representation does not automatically establish type invariants.

**ASAFE-58** — General safe transmutation is not provided.

**ASAFE-59** — `bitcast` requires representation validity.

**ASAFE-60** — Union field access without an established active representation is unsafe.

**ASAFE-61** — Packed representation may require unaligned access handling.

**ASAFE-62** — Unaligned access is explicit.

**ASAFE-63** — `@repr(C)` establishes representation compatibility but not complete safety.

**ASAFE-64** — FFI boundaries require explicit ABI contracts.

**ASAFE-65** — Foreign aliasing is conservatively unknown unless explicitly contracted.

**ASAFE-66** — Foreign ownership is explicit.

**ASAFE-67** — Foreign allocation domains cannot be guessed.

**ASAFE-68** — Foreign callbacks require explicit lifetime and ABI contracts.

**ASAFE-69** — Foreign thread-safety is not assumed.

**ASAFE-70** — FFI does not implicitly establish synchronization.

**ASAFE-71** — Unsafe does not imply NoAlias.

**ASAFE-72** — Unsafe does not imply NoOverflow.

**ASAFE-73** — Unsafe does not imply valid lifetime.

**ASAFE-74** — Unsafe does not imply absence of data races.

**ASAFE-75** — Unchecked operations require operation-specific preconditions.

**ASAFE-76** — Unchecked operations do not globally disable safety verification.

**ASAFE-77** — Safe wrappers may encapsulate narrow unsafe implementations.

**ASAFE-78** — Trusted library primitives should minimize unsafe surface area.

**ASAFE-79** — Panic preserves ownership and Drop invariants.

**ASAFE-80** — Panic is distinct from machine fault/trap.

**ASAFE-81** — Hardware faults are not implicitly converted into `Result`.

**ASAFE-82** — Bounds failures have defined failure semantics.

**ASAFE-83** — Arithmetic failures have defined semantics.

**ASAFE-84** — Lifetime violations are rejected in safe code.

**ASAFE-85** — Capability invalidation is rejected in safe code.

**ASAFE-86** — Relocation cannot invalidate a live capability.

**ASAFE-87** — Stable address requires explicit storage contract.

**ASAFE-88** — Handle identity is distinct from capability validity.

**ASAFE-89** — Handle resolution must establish validity before safe access.

**ASAFE-90** — Atomic access does not imply arbitrary mutable sharing safety.

**ASAFE-91** — Volatile access does not imply synchronization.

**ASAFE-92** — Compiler barriers do not imply CPU memory ordering.

**ASAFE-93** — CPU fences do not transfer ownership.

**ASAFE-94** — Async boundaries preserve safety invariants.

**ASAFE-95** — GPU boundaries preserve ownership, capability and storage-domain invariants.

**ASAFE-96** — DMA operations preserve in-flight storage lifetime.

**ASAFE-97** — Inline assembly is unsafe/system-level and must declare relevant machine effects.

**ASAFE-98** — Sanitizers detect violations but do not redefine language semantics.

**ASAFE-99** — Optimization may consume proven safety facts but cannot manufacture them.

**ASAFE-100** — Undefined behavior is not a substitute for unspecified implementation details; safe Axiom minimizes UB and unsafe boundaries explicitly identify machine-level responsibility.

---

# Kiến trúc Axiom lúc này đã có một đặc điểm rất quan trọng

Ta đã tách được:

```text
                Axiom Program
                     │
          ┌──────────┴──────────┐
          │                     │
        SAFE                 UNSAFE
          │                     │
   compiler proves       programmer establishes
      invariants              contract
          │                     │
          └──────────┬──────────┘
                     ▼
                 Verified MIR
                     │
                     ▼
                 OptIR
                     │
                     ▼
               Native Machine
```

Điểm khác biệt cốt lõi của Axiom là **unsafe không phải một “mode” của compiler**.

Ví dụ muốn bỏ bounds check, programmer không viết:

```ax id="u4k8p2"
unsafe {
    toàn bộ function
}
```

mà dùng primitive cụ thể:

```ax id="x7m3q9"
unsafe_get(...)
```

Compiler chỉ bỏ **đúng proof/check tương ứng với primitive đó**.

Điều này giúp Axiom đạt được cả hai mục tiêu:

**High-level code:**

```ax id="b5n8r1"
for x in values {
    total += x
}
```

→ compiler tự prove, tự vectorize, tự loại bounds check.

**Low-level code:**

```ax id="q2v7m4"
unsafe {
    let p = ...
    let x = *p
}
```

→ vẫn có quyền thao tác trực tiếp với máy.

Không cần biến toàn bộ ngôn ngữ thành hệ thống pointer/lifetime annotation phức tạp.

---

## Chuỗi tiếp theo

Sau khi đã khóa:

```text
076 Resource/I/O
077 FFI/System ABI
078 SIMD/Vector/Tensor
079 Numeric
080 Safety/Unsafe/UB
```

thì kiến trúc compiler đã đủ nền tảng để bước sang một phần rất lớn:

# **BOOTSTRAP-081 — Axiom Compile-Time Metaprogramming, Reflection, Code Generation & Macro Boundary**

Phần này sẽ **khóa hẳn ranh giới giữa `comptime`, reflection, `@derive`, generated code và macro**, đặc biệt để Axiom có khả năng AI-generated code mạnh nhưng **không biến compiler thành một mớ procedural macro/AST mutation khó kiểm soát**.