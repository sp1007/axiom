# BOOTSTRAP-260 — AXIOM MEMORY CODEGEN, POINTER PROVENANCE, ADDRESS CALCULATION & LOAD/STORE LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng khóa lại mối quan hệ giữa mô hình bộ nhớ cấp ngôn ngữ và machine memory:

```text
Value
  ↓
Place
  ↓
Projection
  ↓
Region / Capability
  ↓
Address
  ↓
Memory Access
  ↓
Load / Store / Atomic / Volatile
  ↓
Machine Memory Operand
```

Mục tiêu đặc biệt quan trọng của Axiom:

> **Programmer không cần quản lý pointer/reference để viết code an toàn, nhưng compiler vẫn phải có một mô hình địa chỉ, provenance, alias và memory access đủ chính xác để tạo machine code tối ưu.**

---

# 1. Hai thế giới phải tách biệt

Axiom có:

```text
Semantic Memory Model
```

và:

```text
Machine Memory Model
```

Không được đồng nhất chúng.

Ví dụ programmer viết:

```axiom
fn sum(a: view<i32>) -> i32 {
    a[0] + a[1]
}
```

Programmer không viết:

```text
pointer + offset
load address
```

Nhưng compiler cuối cùng phải tạo:

```text
address = base + index * 4
value = load<i32>(address)
```

---

# 2. Place

**Place** biểu diễn một vị trí có thể chứa value.

Conceptual:

```text
Place =
    Base
    + Projection*
```

Ví dụ:

```axiom
p.x
```

có thể trở thành:

```text
Place(
    base = p,
    projection = Field(x)
)
```

---

# 3. Array place

```axiom
a[i]
```

trở thành:

```text
Place(
    base = a,
    projection = Index(i)
)
```

nhưng `Index(i)` vẫn mang semantic bounds information.

---

# 4. Nested place

```axiom
person.address.city
```

là:

```text
person
 └─ address
     └─ city
```

Compiler có thể phân tích ownership/capability ở từng projection.

---

# 5. Place không phải address

Đây là distinction rất quan trọng.

```text
Place ≠ Pointer ≠ Integer Address
```

`Place` là semantic abstraction.

---

# 6. Address

Address là machine-level representation của vị trí.

```text
Place
 ↓
Address
```

chỉ xảy ra khi physical access/addressability cần thiết.

---

# 7. Không phải mọi Place đều cần address

Ví dụ:

```axiom
let x = 10
let y = x + 20
```

compiler có thể giữ toàn bộ trong registers/SSA.

Không cần:

```text
&x
```

và không cần memory address.

---

# 8. Scalar replacement

Struct:

```axiom
struct Point {
    x: f32
    y: f32
}
```

có thể trở thành:

```text
%x
%y
```

thay vì:

```text
stack[0]
stack[4]
```

---

# 9. Address observability

Nếu programmer/system code thực sự lấy địa chỉ:

```text
address_of(x)
```

thì storage identity trở thành observable.

Compiler không còn được tự do scalarize theo cách làm mất semantics đó.

---

# 10. `address_of`

Axiom không dùng:

```text
&x
```

trong Core.

Dùng system-level:

```axiom
address_of(x)
```

và operation này là **unsafe/system**.

---

# 11. Vì sao?

Để giữ cho:

```text
&
```

không trở thành cửa ngõ khiến programmer phải học pointer/reference semantics.

---

# 12. Provenance

Mỗi safe memory capability có provenance.

Conceptual:

```text
Provenance {
    owner
    allocation
    region
    access
    lifetime
    storage_domain
}
```

---

# 13. Provenance không phải numeric address

Ví dụ:

```text
0x1000
```

chỉ là một machine address.

Nó không tự chứng minh:

```text
"địa chỉ này thuộc object X"
```

---

# 14. Integer → pointer

Trong safe Core:

```text
integer
→ pointer
```

không tự động trở thành valid pointer.

---

# 15. Raw pointer

```axiom
*const T
*mut T
```

là machine-level value.

Raw pointer không tự mang safe ownership.

---

# 16. Dereference

```axiom
*p
```

chỉ được thực hiện trong `unsafe`.

Compiler phải kiểm tra phần còn lại của pipeline theo contract đã thiết lập.

---

# 17. Pointer arithmetic

Ví dụ conceptual:

```text
p + n
```

là unsafe.

Không phải mọi numeric addition trên pointer đều hợp lệ.

---

# 18. Pointer arithmetic contract

Để dereference được safe sau unsafe boundary, compiler cần một contract kiểu:

```text
pointer belongs to allocation A
offset is within permitted region
alignment is valid
object is initialized
access mode is permitted
```

---

# 19. Unsafe không có nghĩa là "mọi thứ đều hợp lệ"

Đây là nguyên tắc đã frozen:

```text
unsafe
 ↓
trusted precondition
 ↓
safe verification resumes
```

---

# 20. Capability → Address

Một:

```text
view<T>
```

có thể được lower thành:

```text
{base_address, length}
```

nếu ABI/target cần.

---

# 21. `mut_view<T>`

Conceptually:

```text
{base_address, length}
```

nhưng semantic state bao gồm:

```text
WRITE
exclusive
provenance
```

---

# 22. View representation không phải language ABI cố định

Compiler có thể truyền:

```text
pointer + length
```

hoặc:

```text
pointer
```

nếu length không cần ở runtime.

---

# 23. Fat vs thin view

Ví dụ:

```axiom
fn sum(a: view<i32>)
```

có thể ABI thành:

```text
(ptr, len)
```

---

# 24. Nhưng compiler có thể specialize

Nếu caller chứng minh length cố định:

```text
[4]i32
```

có thể truyền trực tiếp hoặc inline hoàn toàn.

---

# 25. Semantic view vẫn giữ length/provenance

Cho dù physical representation bị tối ưu.

---

# 26. Load

Semantic:

```text
load<T>(place)
```

có các điều kiện:

```text
initialized
read capability
valid provenance
valid alignment
```

---

# 27. Store

Semantic:

```text
store<T>(place, value)
```

yêu cầu:

```text
write capability
valid provenance
valid alignment
```

và object state phải cho phép ghi.

---

# 28. Store không đơn giản là "ghi byte"

Nó có thể thay đổi ownership/drop state.

Ví dụ:

```axiom
x.field = new_value
```

nếu field chứa Drop-bearing value:

```text
old field
 ↓
drop old value
 ↓
store new value
```

theo semantic rules.

---

# 29. Assignment lowering

Conceptual:

```text
x = y
```

↓

```text
evaluate y
verify destination
drop old destination if required
move/copy y
initialize destination
```

Physical store đến sau semantic verification.

---

# 30. Partial initialization

Compiler phải hỗ trợ:

```text
struct S {
    a: String
    b: String
}
```

trong trạng thái:

```text
a = initialized
b = uninitialized
```

---

# 31. MIR state

Ownership verifier đã có:

```text
INIT
UNINIT
MOVED
PARTIALLY_MOVED
DROPPED
```

Memory codegen không được làm mất state này.

---

# 32. `MaybeUninit`

System/library abstraction cho:

```text
uninitialized storage
```

không phải một cách để bypass verifier.

---

# 33. `MaybeUninit<T>`

Semantic distinction:

```text
storage exists
value T does not necessarily exist
```

---

# 34. Reading uninitialized memory

Không hợp lệ trong safe semantics.

Unsafe code phải establish initialization contract trước khi biến nó thành `T`.

---

# 35. Alignment

Mỗi type có:

```text
size_of(T)
align_of(T)
```

Compiler biết tại compile time nếu type static.

---

# 36. Aligned access

Machine code mặc định sử dụng alignment mà ABI/type contract cho phép.

---

# 37. Unaligned access

Nếu cần đọc dữ liệu không aligned:

```text
read_unaligned<T>
write_unaligned<T>
```

là explicit system/library operations.

---

# 38. Không tự động coi mọi pointer là aligned

Raw pointer contract phải chứng minh hoặc sử dụng API unaligned.

---

# 39. Endianness

Memory representation và byte order là hai vấn đề khác nhau.

```text
T
```

không tự có wire endian semantics.

---

# 40. `read_le` / `read_be`

Serialization/network/storage layer xử lý explicit.

---

# 41. Machine load/store flags

Machine IR:

```text
Load {
    address
    type
    alignment
    volatile
    atomic_order
    address_space
}
```

---

# 42. Ordinary load

```text
atomic = false
volatile = false
```

compiler được phép tối ưu theo AliasInfo/EffectInfo.

---

# 43. Atomic load

```text
atomic = true
order = Acquire
```

không thể được xử lý như ordinary load.

---

# 44. Volatile load

```text
volatile = true
```

là observable memory operation.

---

# 45. Atomic ≠ volatile

Atomic:

```text
concurrency semantics
```

Volatile:

```text
observable memory access
```

Hai concept độc lập.

---

# 46. Có thể có:

```text
atomic + volatile
```

nếu system/target API yêu cầu.

---

# 47. Memory ordering

Axiom semantic layer đã định nghĩa:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Machine backend mapping xuống ISA.

---

# 48. Relaxed

Chỉ yêu cầu atomicity và các semantics tương ứng, không tạo ordering mạnh hơn cần thiết.

---

# 49. Acquire

Các operation sau acquire không được semantic reorder trước acquire theo cách phá happens-before.

---

# 50. Release

Các operation trước release không được semantic reorder sau release theo cách phá happens-before.

---

# 51. SeqCst

Có thêm global sequential consistency ordering theo memory model Axiom.

---

# 52. Compiler barrier ≠ CPU fence

Phải phân biệt:

```text
CompilerBarrier
CPUFence
AtomicOperation
```

---

# 53. Compiler barrier

Ngăn compiler reorder một số operations.

Không nhất thiết sinh machine instruction.

---

# 54. CPU fence

Có thể sinh instruction:

```text
mfence
dmb
fence
...
```

tùy target.

---

# 55. Atomic RMW

Semantic:

```text
fetch_add
compare_exchange
swap
```

---

# 56. Compare-exchange

Phải biểu diễn rõ:

```text
success_order
failure_order
```

và semantics của expected/current value.

---

# 57. Không được hạ atomic RMW thành:

```text
load
add
store
```

ordinary.

---

# 58. Trừ khi target/backend có primitive tương đương đảm bảo đúng atomic semantics.

---

# 59. Address calculation

Ví dụ:

```axiom
a[i]
```

conceptual:

```text
base + i * sizeof(T)
```

---

# 60. Bounds checking

Semantic:

```text
0 <= i < len
```

---

# 61. Bounds-check elimination

Nếu compiler chứng minh:

```text
i < len
```

thì machine bounds check có thể biến mất.

---

# 62. Không được bỏ bounds check chỉ vì optimizer "tin rằng" index hợp lệ.

Proof phải tồn tại trong RangeInfo/verified analysis.

---

# 63. Loop example

```axiom
for i in 0..n {
    sum += a[i]
}
```

Compiler có thể chứng minh:

```text
i < n
n <= a.len
```

và eliminate repeated checks.

---

# 64. Vectorization

Sau proof:

```text
a[i]
a[i+1]
a[i+2]
a[i+3]
```

có thể thành vector load.

---

# 65. Nhưng alias proof vẫn cần thiết.

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu compiler không chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

không được tùy tiện vectorize theo giả định no-alias.

---

# 66. Capability → AliasInfo

Đây là một trong các điểm mạnh của Axiom.

```text
mut_view(out)
```

đã mang exclusive semantic capability.

Nếu verifier chứng minh disjointness:

```text
NO_ALIAS
```

được đưa xuống optimizer.

---

# 67. Nhưng UNKNOWN ≠ NO_ALIAS

Đây là invariant quan trọng.

---

# 68. Field-level access

```axiom
struct Pair {
    a: i32
    b: i32
}
```

Compiler có thể cho:

```text
mut_view(pair.a)
mut_view(pair.b)
```

nếu regions chứng minh disjoint.

---

# 69. Address calculation cho field

Conceptual:

```text
base + field_offset
```

---

# 70. Field offset

Với layout mặc định:

```text
offset_of(Pair, a)
```

là compiler fact, nhưng không nhất thiết stable ABI.

---

# 71. Với `@repr(C)`

Field order/representation obey C ABI contract.

---

# 72. Nested field

```text
p.a.b.c
```

được lower thành tổng các offset/projections.

---

# 73. Compiler có thể collapse toàn bộ chain

Ví dụ:

```text
base + 24
```

nếu layout biết rõ.

---

# 74. Dynamic index

```text
a[i]
```

có thể tạo:

```text
base + i * element_size
```

và bounds proof.

---

# 75. Constant index

```text
a[3]
```

có thể compile thành fixed offset.

---

# 76. Slice

```axiom
a[start:end]
```

semantic:

```text
new view
provenance = a
region = [start,end)
```

---

# 77. Slice không copy dữ liệu

Trừ khi API explicitly yêu cầu materialization.

---

# 78. Nested slice

```text
view(view(a))
```

không tạo ownership mới.

Compiler có thể collapse provenance chain.

---

# 79. View lifetime

Nếu:

```axiom
let v = view(x)
```

thì:

```text
lifetime(v) <= lifetime(x)
```

---

# 80. Relocation

Nếu:

```text
Vec<T>
```

đang có live view:

```text
view(vec)
```

thì operation có thể relocate storage phải bị chặn hoặc view phải kết thúc trước đó.

---

# 81. Compiler không cần programmer viết lifetime

Đây chính là mục tiêu:

```text
compiler proves
```

thay vì:

```text
programmer annotates
```

---

# 82. Example

```axiom
fn test() {
    let mut v = Vec<i32>()
    v.push(1)

    let x = view(v)

    v.push(2)   // compiler checks relocation possibility
}
```

Nếu `push` có thể relocate và `x` vẫn live:

```text
error
```

hoặc compiler có thể chọn một implementation/API path không relocate nếu contract cho phép.

---

# 83. `reserve`

```axiom
v.reserve(100)
```

không tạo perpetual stable address.

Nó chỉ thay đổi capacity/storage contract.

---

# 84. Stable address

Nếu cần:

```text
StableBox
PinnedStorage
ArenaStorage
```

library/system abstraction cung cấp contract.

Không cần Core `Pin<T>`.

---

# 85. Memory mapped file

```text
MappedFile
```

có storage identity riêng.

`view<T>` vào mapping phụ thuộc mapping lifetime.

---

# 86. Compiler không được coi mmap giống heap object thông thường.

---

# 87. DMA

DMA buffer có:

```text
CPU visibility
device visibility
ownership
synchronization
alignment
lifetime
```

---

# 88. DMA completion

Không được drop/reuse buffer trước khi device hoàn thành.

`GpuEvent`/`DmaEvent`/I/O completion tạo synchronization capability.

---

# 89. Đây là một trường hợp ownership vượt ra ngoài CPU memory.

---

# 90. Address spaces

Axiom memory access có:

```text
AddressSpace
```

conceptual:

```text
Host
Device
Shared
Local
Constant
MMIO
TLS
External
```

---

# 91. AddressSpace không phải Type

Một `i32` có thể tồn tại ở nhiều storage domains.

---

# 92. Nhưng access legality phụ thuộc domain.

---

# 93. CPU → GPU

Không tự biến:

```text
view<T>
```

thành:

```text
DeviceView<T>
```

---

# 94. Transfer explicit

Ví dụ:

```axiom
device.copy_from(host)
```

hoặc API tương đương.

---

# 95. Zero-copy

Compiler/runtime có thể phát hiện shared/unified memory và bỏ transfer.

Nhưng chỉ khi storage contract cho phép.

---

# 96. Không được tối ưu bỏ transfer nếu transfer có observable synchronization semantics.

---

# 97. TLS

TLS address calculation khác ordinary global.

```text
TLS variable
```

được lower theo target TLS ABI.

---

# 98. Static

Static có stable storage identity nếu address-observable.

Machine placement:

```text
.rodata
.data
.bss
```

tùy semantics.

---

# 99. Global immutable

Compiler có thể embed constant trực tiếp:

```text
mov immediate
```

nếu address không observable.

---

# 100. Address-observable static

Nếu:

```text
address_of(GLOBAL)
```

được expose:

storage phải tồn tại.

---

# 101. Atomic static

Ví dụ:

```axiom
static COUNTER: Atomic<u64>
```

machine access phải atomic.

---

# 102. MMIO

Ví dụ conceptual:

```axiom
unsafe {
    mmio.write32(addr, value)
}
```

backend phải preserve:

```text
volatile
ordering
address space
```

theo system contract.

---

# 103. Memory barriers around MMIO

Không được compiler tự xóa/reorder các operations cần thiết.

---

# 104. Raw pointer load

Conceptual:

```text
load_raw<T>(*const T)
```

yêu cầu unsafe preconditions.

---

# 105. Safe view load

```text
load(view)
```

được verifier chứng minh.

---

# 106. Same machine instruction, different semantic origin

Hai operation đều có thể trở thành:

```text
MOV
```

nhưng semantic facts trước đó khác nhau.

Đây là lý do Machine IR cần metadata.

---

# 107. Semantic metadata không nhất thiết đi vào binary

Compiler internal only.

---

# 108. Memory access effect

EffectInfo có:

```text
Read(region)
Write(region)
Atomic(region)
Volatile(region)
```

---

# 109. Alias optimizer

Có thể suy ra:

```text
load A
load B
```

độc lập nếu regions NO_ALIAS.

---

# 110. Load forwarding

```text
store x, 10
load x
```

có thể thành:

```text
10
```

nếu không có intervening observable access.

---

# 111. Store-to-load forwarding

Đây là optimization hợp lệ nếu AliasInfo/EffectInfo chứng minh.

---

# 112. Load CSE

```text
x = a.field
y = a.field
```

có thể dùng cùng value nếu không có mutation/observable invalidation.

---

# 113. Nhưng volatile load không được CSE như vậy.

---

# 114. Atomic load

Atomic load không được biến thành cached ordinary value qua một operation có thể modify atomic.

---

# 115. Memory dependency

Optimizer cần MemorySSA.

Ví dụ:

```text
Store A
Load B
Store C
Load A
```

MemorySSA + alias facts quyết định dependency.

---

# 116. `view` không tự đồng nghĩa với immutable machine memory

`view<T>` chỉ:

```text
READ capability
```

Không có nghĩa physical memory không bị thay đổi bởi một actor khác nếu unsafe/foreign/shared synchronization contract cho phép.

---

# 117. Share + synchronization

Compiler phải biết synchronization boundary:

```text
Mutex
Atomic
Channel
ThreadJoin
```

để reason về visibility.

---

# 118. Foreign call

Nếu:

```text
extern "C" fn foo(...)
```

không có memory contract:

compiler phải conservative.

---

# 119. Có thể khai báo contract

System/FFI metadata có thể nói:

```text
@reads(arg0)
@writes(arg1)
@noalias(arg1,arg2)
```

nhưng đây là boundary contract, không phải Core programmer syntax mặc định.

---

# 120. Nếu contract sai

Đó là FFI/unsafe violation.

Compiler không thể prove foreign implementation đúng nếu không có trusted verification.

---

# 121. Machine lowering model

Cuối cùng:

```text
Load<T>(Place)
```

↓

```text
AddressCalc
```

↓

```text
MachineMemoryOperand
```

↓

```text
MachineLoad
```

---

# 122. Address calculation có thể bị eliminate

Nếu base nằm trong register:

```text
RAX
```

và offset constant:

```text
[RAX + 16]
```

không cần instruction riêng.

---

# 123. Complex addressing

x86 có thể:

```text
[base + index*scale + displacement]
```

---

# 124. ARM64 có addressing mode khác.

---

# 125. RISC-V khác nữa.

Vì vậy:

> **Address calculation là semantic LIR operation, còn addressing mode là Machine IR/target concern.**

---

# 126. Example

LIR:

```text
load(
    address = base + index * 4 + 16
)
```

x86 có thể:

```text
MOV EAX, [RDI + RSI*4 + 16]
```

ARM64 có thể cần sequence khác.

---

# 127. Không được để x86 addressing mode rò vào LIR.

---

# 128. Load width

Machine access cần explicit:

```text
8-bit
16-bit
32-bit
64-bit
128-bit
256-bit
512-bit
```

hoặc target vector width.

---

# 129. Extension

Semantic integer load có thể cần:

```text
zero_extend
sign_extend
```

Ví dụ:

```text
load u8 → i32
```

không phải đơn giản là 32-bit load.

---

# 130. Narrow store

```text
store u8
```

chỉ ghi byte tương ứng, không được biến thành full-word store nếu có thể overwrite observable neighboring bytes.

---

# 131. Partial memory writes

Đặc biệt quan trọng với:

- packed structs
- MMIO
- volatile
- shared memory
- FFI.

---

# 132. Vector load/store

Compiler phải biết:

```text
alignment
mask
tail
addressing
```

---

# 133. Masked load

Không phải target nào cũng có native masked load.

Legalization phải preserve:

```text
inactive lanes semantics
faulting semantics
```

theo operation contract.

---

# 134. Gather/scatter

Có thể lower thành native instruction hoặc scalar expansion.

---

# 135. Scalar expansion

Ví dụ target không có gather:

```text
gather
 ↓
load
load
load
...
```

nhưng phải preserve semantics.

---

# 136. Atomic width

Target có thể không hỗ trợ mọi width.

Ví dụ:

```text
Atomic<u128>
```

có thể cần library/runtime fallback hoặc target-specific sequence.

---

# 137. Compiler không được silently weaken atomicity.

---

# 138. Lock-free

`Atomic<T>` không đảm bảo lock-free.

Có thể query:

```text
is_lock_free<T>()
```

ở compile/runtime tùy target.

---

# 139. Volatile width

System API phải xác định access width chính xác.

---

# 140. Compiler không được merge:

```text
volatile8
volatile8
```

thành:

```text
volatile16
```

nếu semantics không cho phép.

---

# 141. Memory fence lowering

LIR:

```text
Fence(Release)
```

↓

target-specific barrier hoặc no-op nếu target memory model đã đủ mạnh.

---

# 142. No-op fence vẫn phải giữ semantic model

Nếu target naturally stronger:

```text
Acquire → no instruction
```

có thể hợp lệ.

---

# 143. Stronger hardware ordering

CPU có thể mạnh hơn Axiom requirement.

Compiler được phép tận dụng.

---

# 144. Weaker hardware ordering

Compiler phải thêm instruction/sequence cần thiết.

---

# 145. Pointer equality

Raw pointer equality là machine/system concept.

Không được dùng để suy ra semantic identity của arbitrary values.

---

# 146. Object identity

Axiom phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

Memory address chỉ là một physical representation của Storage Identity khi address observable.

---

# 147. Pointer provenance and equality

Hai pointer có cùng numeric address ở các thời điểm khác nhau không mặc nhiên có cùng semantic provenance.

---

# 148. Allocator reuse

Memory allocator có thể:

```text
free A
allocate B
```

và B nhận cùng numeric address.

Điều đó không biến pointer cũ thành pointer tới B.

---

# 149. Đây là điểm cần thiết để tránh use-after-free optimizer bugs.

---

# 150. Integer round-trip

Axiom không đảm bảo:

```text
pointer → integer → pointer
```

khôi phục safe provenance.

System/FFI có explicit APIs/contracts nếu platform yêu cầu.

---

# 151. Provenance stripping

Optimizer không được tùy tiện coi mọi pointer như integer arithmetic nếu làm mất validity semantics.

---

# 152. Pointer comparison

Ordering raw pointers chỉ có semantics khi target/system contract cho phép.

Không được mặc định áp dụng mathematical ordering giữa hai allocation độc lập.

---

# 153. `memcpy`

Axiom cần phân biệt:

```text
semantic Copy
```

với:

```text
byte copy
```

---

# 154. `memcpy` không phải `Copy<T>`

Byte copying một Drop-bearing/invalid-representation type có thể phá semantic invariants.

---

# 155. Typed copy

Compiler có thể generate memcpy cho một `Copy` type nếu representation/ABI cho phép.

---

# 156. Nhưng:

```text
Copy semantic
```

không yêu cầu physical memcpy.

---

# 157. Move

Move cũng không yêu cầu physical copy.

Ví dụ:

```text
RAX
```

có thể tiếp tục được coi là destination value sau ownership state transition.

---

# 158. Drop

Drop semantic operation có thể lower thành:

```text
call destructor
```

hoặc inline hoàn toàn.

---

# 159. Zero-sized type

ZST có:

```text
size = 0
```

nhưng semantic value vẫn tồn tại.

---

# 160. Address of ZST

Nếu system yêu cầu stable address identity, backend phải tuân thủ storage contract; không được giả định mọi ZST có địa chỉ vật lý unique theo mặc định.

---

# 161. Memory allocation

Semantic:

```text
ALLOC<T>
```

không nhất thiết:

```text
malloc(sizeof(T))
```

---

# 162. Backend có thể eliminate allocation

Nếu:

```text
NoEscape
```

→ stack/register/scalarization.

---

# 163. Heap allocation

Chỉ trở thành machine/runtime operation nếu storage semantics yêu cầu.

---

# 164. Arena allocation

Một `Arena<T>` có thể compile thành:

```text
bump pointer
```

và một số metadata.

---

# 165. Pool

Có thể compile thành free-list operations.

---

# 166. GPU memory

Không dùng CPU allocator.

---

# 167. Memory-mapped storage

Không dùng allocator semantics thông thường.

---

# 168. External memory

Compiler phải biết ownership boundary.

---

# 169. Machine IR memory model

Đề xuất:

```text
MachineMemoryOperand {
    base
    index
    scale
    displacement
    size
    alignment
    address_space
    access_kind
    atomic_order
    volatile
}
```

---

# 170. AccessKind

```text
READ
WRITE
READ_WRITE
ATOMIC
VOLATILE
```

---

# 171. Nhưng semantic metadata có thể nhiều hơn

```text
provenance_id
region_id
effect_id
```

chỉ compiler-internal.

---

# 172. Không nhất thiết encode provenance vào machine code

---

# 173. Sanitizer/debug mode

Compiler có thể instrument:

```text
bounds
use-after-free
race
uninitialized
```

nhưng instrumentation là tooling/profile.

---

# 174. Không được thay đổi language semantics

---

# 175. Address sanitizer-like mode

Có thể thêm red zones/quarantine.

---

# 176. Production build

Không có overhead nếu instrumentation không bật.

---

# 177. Memory safety guarantee

Safe Axiom không dựa vào sanitizer.

Sanitizer chỉ giúp tìm:

```text
unsafe/FFI/compiler bugs
```

---

# 178. Machine verifier

Trước encoding kiểm tra:

```text
address space
alignment
operand size
atomic legality
volatile legality
register/address constraints
```

---

# 179. Target legality

Ví dụ target không hỗ trợ:

```text
unaligned atomic 64
```

backend phải reject hoặc legalize.

---

# 180. Không được emit instruction không đáp ứng target contract.

---

# 181. Compiler pipeline hoàn chỉnh

```text
Typed HIR
   ↓
Ownership / Capability
   ↓
MIR Place
   ↓
Region Analysis
   ↓
AliasInfo
   ↓
MemorySSA
   ↓
Semantic Optimization
   ↓
ABI MIR
   ↓
Memory Lowering
   ↓
Axiom LIR
   ↓
Target Address Lowering
   ↓
Machine Memory Operand
   ↓
Machine Instruction
```

---

# 182. CompilerDB bổ sung

```text
PlaceDB
MemoryAccessDB
ProvenanceDB
AddressDB
AliasDB
MemorySSA
AtomicDB
VolatileDB
AddressSpaceDB
```

---

# 183. ID

```text
PlaceId
ProjectionId
ProvenanceId
AllocationId
RegionId
MemoryAccessId
AddressExprId
AddressSpaceId
AtomicOpId
FenceId
```

---

# 184. MemoryAccess record

Conceptual:

```text
MemoryAccess {
    id
    kind
    place
    region
    provenance
    size
    alignment
    address_space
    atomic
    volatile
    effect
}
```

---

# 185. Address expression

```text
AddressExpr =
    Base
  | Add(AddressExpr, Integer)
  | Scale(AddressExpr, Integer)
  | Index(AddressExpr, Value)
  | Field(AddressExpr, Offset)
```

---

# 186. Address expressions được canonicalize.

Ví dụ:

```text
(base + 4) + i*4
```

→

```text
base + i*4 + 4
```

---

# 187. Nhưng canonicalization không được mất overflow/address semantics.

---

# 188. Pointer arithmetic overflow

Machine integer arithmetic và valid pointer arithmetic không đồng nhất.

Unsafe pointer arithmetic phải obey target/object provenance contract.

---

# 189. Bounds proof

Compiler có thể reason:

```text
index range
object extent
element size
```

để chứng minh address hợp lệ.

---

# 190. Integer overflow trong address calculation

Backend phải dùng target-appropriate arithmetic semantics.

Nếu physical address computation được proven bounded, compiler có thể sử dụng native wrapping arithmetic internally.

---

# 191. Không được dùng machine overflow như một shortcut để bỏ semantic validity checks.

---

# 192. Huge arrays

Compiler phải tránh integer-width truncation trong address calculation.

---

# 193. `usize`

Dùng cho machine-size indexing/address-related quantities.

---

# 194. `isize`

Có semantics riêng cho signed machine-sized quantities.

---

# 195. Cross-target

32-bit target:

```text
usize = 32 bit
```

64-bit:

```text
usize = 64 bit
```

---

# 196. Nhưng Axiom semantic memory model không phụ thuộc pointer width cố định.

---

# 197. WASM

WASM32:

```text
linear memory address = i32
```

nhưng Axiom provenance vẫn là semantic layer.

---

# 198. WASM pointer

Không được mặc định coi:

```text
i32 address
```

là valid Axiom pointer.

---

# 199. GPU

GPU pointer/address space cũng không được coi là CPU pointer.

---

# 200. Final memory-codegen principle

Axiom đóng băng nguyên tắc:

> **Semantic memory access is typed, capability-checked and provenance-aware; physical memory access is target-specific and may be radically different.**

---

# 201. Các invariant chính

```text id="8xgk3h"
AMEMCODE-20
A Place is a semantic storage location, not necessarily a machine address.

AMEMCODE-21
A machine address is not inherently a valid Axiom capability.

AMEMCODE-22
Place, pointer, address and integer are distinct semantic concepts.

AMEMCODE-23
Address materialization occurs only when physical addressability is required.

AMEMCODE-24
Scalar values need not have addressable storage.

AMEMCODE-25
Address observability constrains storage optimization.

AMEMCODE-26
Safe capabilities carry provenance.

AMEMCODE-27
Numeric pointer equality does not establish semantic provenance.

AMEMCODE-28
Integer-to-pointer conversion does not automatically establish safe provenance.

AMEMCODE-29
Raw pointer dereference is unsafe/system-level.

AMEMCODE-30
Unsafe pointer operations require explicit semantic preconditions.

AMEMCODE-31
Safe verification resumes only from established unsafe contracts.

AMEMCODE-32
Load requires valid initialization, provenance, access and representation.

AMEMCODE-33
Store requires valid write capability and destination validity.

AMEMCODE-34
Partial initialization is tracked semantically.

AMEMCODE-35
Reading uninitialized storage as T is invalid.

AMEMCODE-36
MaybeUninit cannot bypass initialization verification.

AMEMCODE-37
Alignment is part of memory-access validity.

AMEMCODE-38
Unaligned access requires an explicit supported operation/contract.

AMEMCODE-39
Typed load/store semantics are distinct from byte copying.

AMEMCODE-40
Semantic Copy does not imply physical memcpy.

AMEMCODE-41
Semantic Move does not require physical movement.

AMEMCODE-42
Drop semantics must be preserved by memory lowering.

AMEMCODE-43
Field projections preserve place-sensitive ownership semantics.

AMEMCODE-44
Array indexing preserves bounds semantics.

AMEMCODE-45
Bounds checks may be eliminated only from proven range facts.

AMEMCODE-46
Unknown range facts cannot establish memory safety.

AMEMCODE-47
Slice views preserve source provenance.

AMEMCODE-48
View lifetime cannot exceed provenance lifetime.

AMEMCODE-49
Relocation is forbidden while a stable capability requires the old storage location.

AMEMCODE-50
A view does not imply physical immutability of memory outside its capability model.

AMEMCODE-51
READ and WRITE capability semantics feed AliasInfo.

AMEMCODE-52
Proven disjoint capabilities may establish internal NO_ALIAS.

AMEMCODE-53
UNKNOWN aliasing is never treated as NO_ALIAS.

AMEMCODE-54
Atomic access is distinct from ordinary memory access.

AMEMCODE-55
Atomic operations cannot be weakened to ordinary loads/stores.

AMEMCODE-56
Atomic memory ordering must be preserved.

AMEMCODE-57
Volatile access is distinct from atomic access.

AMEMCODE-58
Volatile accesses cannot be removed as ordinary dead memory operations.

AMEMCODE-59
Volatile ordering constraints must be preserved.

AMEMCODE-60
Compiler barriers and CPU fences are distinct concepts.

AMEMCODE-61
A stronger target memory model may implement an Axiom ordering with fewer instructions.

AMEMCODE-62
A weaker target memory model must be strengthened by legal machine operations.

AMEMCODE-63
Atomic RMW must preserve atomicity.

AMEMCODE-64
Compare-exchange success and failure orderings must be preserved.

AMEMCODE-65
Machine memory operands must encode required access width.

AMEMCODE-66
Narrow loads/stores cannot be widened when observable neighboring bytes would change.

AMEMCODE-67
Sign/zero extension semantics must be preserved.

AMEMCODE-68
Memory address calculations must preserve object bounds/provenance semantics.

AMEMCODE-69
Pointer arithmetic cannot be treated as unrestricted integer arithmetic in safe semantics.

AMEMCODE-70
Field offsets are representation facts, not semantic identity.

AMEMCODE-71
Default layout may be optimized unless a representation contract makes layout observable.

AMEMCODE-72
@repr(C) imposes explicit representation constraints.

AMEMCODE-73
Address spaces are explicit memory-domain concepts.

AMEMCODE-74
CPU, GPU, MMIO and device memory are not implicitly interchangeable.

AMEMCODE-75
Host-to-device conversion is never an implicit ownership conversion.

AMEMCODE-76
DMA buffers remain live until the required device operation completes.

AMEMCODE-77
Device synchronization is part of memory/resource semantics.

AMEMCODE-78
TLS memory uses target-specific TLS addressing while retaining Axiom storage semantics.

AMEMCODE-79
Static storage identity is preserved when address-observable.

AMEMCODE-80
Global atomic storage preserves atomic semantics.

AMEMCODE-81
Memory-mapped storage has explicit lifetime and provenance.

AMEMCODE-82
Foreign memory requires an explicit FFI contract.

AMEMCODE-83
Foreign calls without memory contracts are conservatively modeled.

AMEMCODE-84
memcpy is not a universal semantic value-copy operation.

AMEMCODE-85
Byte-level copying requires representation validity.

AMEMCODE-86
Zero-sized types retain semantic value identity despite zero physical size.

AMEMCODE-87
Allocation semantics are independent of a particular allocator implementation.

AMEMCODE-88
Allocation may be eliminated when storage is semantically unobservable.

AMEMCODE-89
Arena, pool and device allocations are distinct storage strategies.

AMEMCODE-90
Address expressions may be optimized only while preserving semantic address validity.

AMEMCODE-91
Address-expression canonicalization cannot change overflow/provenance semantics.

AMEMCODE-92
Machine addressing modes are target-specific.

AMEMCODE-93
LIR must not depend on x86-specific addressing modes.

AMEMCODE-94
Target lowering may combine address calculation with load/store instructions.

AMEMCODE-95
Target lowering may split one semantic memory operation into multiple machine operations only when semantics are preserved.

AMEMCODE-96
Masked/gather/scatter lowering must preserve inactive-lane and fault semantics.

AMEMCODE-97
Unsupported atomic widths require legal target-specific expansion or rejection.

AMEMCODE-98
Machine memory legality must be checked before encoding.

AMEMCODE-99
Sanitizer instrumentation does not define language semantics.

AMEMCODE-100
Safe memory correctness does not depend on runtime sanitizer instrumentation.

AMEMCODE-101
MemorySSA must preserve observable memory dependencies.

AMEMCODE-102
Load elimination requires proof that no relevant memory modification intervenes.

AMEMCODE-103
Store elimination requires proof that the store is unobservable.

AMEMCODE-104
Memory scheduling must preserve atomic, volatile and external effects.

AMEMCODE-105
Provenance information is compiler-semantic information and need not be emitted into ordinary machine code.

AMEMCODE-106
Pointer representation is a backend concern and must not leak into safe Core semantics.

AMEMCODE-107
The compiler may internally use pointers extensively without requiring programmer-visible pointer syntax.

AMEMCODE-108
Memory code generation must preserve ownership and Drop semantics.

AMEMCODE-109
Memory code generation must preserve capability validity.

AMEMCODE-110
Memory code generation must preserve execution/storage domain constraints.

AMEMCODE-111
WASM linear-memory addresses do not automatically become Axiom-safe pointers.

AMEMCODE-112
GPU addresses do not automatically become CPU pointers.

AMEMCODE-113
Device memory does not implicitly become host memory.

AMEMCODE-114
Compiler optimizations may eliminate physical memory operations only when semantic effects are absent.

AMEMCODE-115
A physical load/store may represent multiple semantic abstractions depending on metadata.

AMEMCODE-116
Machine IR must retain sufficient memory metadata for correct scheduling and legalization.

AMEMCODE-117
Memory lowering must be deterministic for a fixed target/configuration.

AMEMCODE-118
Memory semantics are independent of optimization level.

AMEMCODE-119
Safe memory verification occurs before target-specific memory optimization.

AMEMCODE-120
Memory code generation is the boundary where semantic Places become target-specific memory operations.
```

---

# Kiến trúc backend hiện tại

Sau 259 + 260, backend đã trở thành:

```text
                    AXIOM SOURCE
                         │
                         ▼
                   Typed / Verified MIR
                         │
             ┌───────────┴───────────┐
             │                       │
       Ownership/Capability       Effects
             │                       │
             └───────────┬───────────┘
                         ▼
                    Semantic OptIR
                         │
             ┌───────────┴───────────┐
             │                       │
         AliasInfo                MemorySSA
             │                       │
             └───────────┬───────────┘
                         ▼
                      ABI MIR
                         │
                         ▼
                    AXIOM LIR
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
           x86-64       ARM64       RISC-V
             │           │            │
             └───────────┼────────────┘
                         ▼
                    Machine IR
                         │
                ┌────────┴────────┐
                │                 │
          Address Lowering    Register Model
                │                 │
                └────────┬────────┘
                         ▼
                  Instruction Select
                         │
                         ▼
                  Register Allocation
                         │
                         ▼
                    Scheduling
                         │
                         ▼
                  Machine Verify
                         │
                         ▼
                    Encoder
                         │
                         ▼
                  AxiomObject
```

Điều này cũng xác nhận một quyết định kiến trúc quan trọng của Axiom:

**Axiom không cần tránh pointer ở compiler. Axiom chỉ cần tránh bắt programmer phải quản lý pointer.**

Compiler hoàn toàn có thể sử dụng:

- pointers
- addresses
- SSA pointers
- alias sets
- MemorySSA
- provenance
- register allocation
- stack slots
- raw machine addressing

ở bên trong.

Đó chính là cách đạt mục tiêu **“ngôn ngữ đơn giản cho programmer nhưng compiler đủ mạnh để đạt hiệu năng C/C++.”**

---

# Tiếp theo: BOOTSTRAP-261

Phần nền tảng memory/codegen đã khóa. Bước hợp lý tiếp theo là:

## **AXIOM x86-64 BACKEND V1**

Không chỉ mô tả vài instruction, mà thiết kế hoàn chỉnh:

```text
x86-64 TargetSpec
        ↓
register file
        ↓
ABI: Windows x64 / SysV
        ↓
calling convention
        ↓
integer ABI
        ↓
floating-point ABI
        ↓
vector ABI
        ↓
struct/aggregate return
        ↓
sret
        ↓
variadic functions
        ↓
stack frame
        ↓
red zone
        ↓
shadow space
        ↓
TLS
        ↓
atomics
        ↓
SIMD
        ↓
instruction selection
        ↓
register allocation
        ↓
encoding
        ↓
PE/ELF
```

Đây sẽ là **backend ISA đầu tiên được đặc tả ở mức có thể bắt đầu implement compiler**, và đồng thời tạo mẫu để sau đó xây ARM64 và RISC-V mà không làm bẩn kiến trúc frontend/Core.