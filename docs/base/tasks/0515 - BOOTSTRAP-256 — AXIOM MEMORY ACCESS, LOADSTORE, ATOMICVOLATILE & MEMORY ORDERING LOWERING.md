# BOOTSTRAP-256 — AXIOM MEMORY ACCESS, LOAD/STORE, ATOMIC/VOLATILE & MEMORY ORDERING LOWERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng nối trực tiếp:

```text
Axiom semantic values
        ↓
Place
        ↓
Capability / provenance
        ↓
Memory operation
        ↓
Load / Store / Atomic / Volatile
        ↓
Axiom LIR
        ↓
Machine instructions
```

Mục tiêu của tầng này là: **Axiom cho compiler toàn quyền tối ưu memory access, nhưng không được làm thay đổi semantics đã được verifier chứng minh.**

---

# 1. Nguyên tắc trung tâm

Axiom phân biệt 4 thứ:

```text
Value
Place
Address
Memory Operation
```

Chúng không phải một khái niệm.

Ví dụ:

```axiom
x.field
```

có thể là:

```text
Place
```

nhưng chưa nhất thiết tạo machine address.

---

# 2. Place

`Place` biểu diễn **vị trí lưu trữ semantic** của một giá trị.

Mô hình:

```text
Place =
    Base
    + Projection*
```

Ví dụ:

```axiom
person.address.city
```

có thể trở thành:

```text
Place(
    Base = person,
    Projection = [
        Field(address),
        Field(city)
    ]
)
```

---

# 3. Các Base

MIR có thể có:

```text
Local
Static
TLS
Parameter
Temporary
Deref
External
Device
```

---

# 4. Projection

Các projection Core:

```text
Field
Index
ConstantIndex
Deref
Slice
Downcast
```

và system/GPU có thể mở rộng.

---

# 5. Field projection

```axiom
p.x
```

không có nghĩa:

```text
load p
load x
```

Compiler có thể tính offset và load trực tiếp:

```text
load [p + offset(x)]
```

---

# 6. Đây là lý do `Place` rất quan trọng

Ownership verifier có thể biết:

```text
p.x
p.y
```

là hai region khác nhau.

---

# 7. Array indexing

```axiom
a[i]
```

semantic:

```text
base = a
index = i
```

Compiler phải kiểm tra bounds trong safe code.

---

# 8. Bounds check

Nếu:

```text
0 <= i < len(a)
```

đã được chứng minh:

→ check có thể bị loại bỏ.

---

# 9. Nếu không chứng minh được

Compiler giữ:

```text
bounds_check(i)
```

Không được giả định safety chỉ vì optimizer “có vẻ biết”.

---

# 10. Slice

```axiom
a[start..end]
```

tạo view/capability theo semantics.

Không nhất thiết copy dữ liệu.

---

# 11. Slice address

Compiler có thể lower:

```text
base + start * sizeof(T)
```

nhưng semantic validity vẫn phải được kiểm tra trước.

---

# 12. `view<T>`

`view<T>` là capability, không phải raw address.

Conceptual representation có thể là:

```text
View {
    provenance
    region
    length
}
```

nhưng physical representation không cố định.

---

# 13. Compiler có thể erase capability metadata

Sau verification:

```text
view<T>
```

có thể trở thành:

```text
pointer + length
```

hoặc chỉ:

```text
pointer
```

nếu length không còn cần.

---

# 14. Nhưng semantic provenance không được mất

Optimizer có thể bỏ metadata vật lý.

Không được biến:

```text
UNKNOWN
```

thành:

```text
NO_ALIAS
```

chỉ vì metadata bị erase.

---

# 15. `mut_view<T>`

Đại diện exclusive write capability.

Semantic:

```text
provenance
region
WRITE
```

---

# 16. Load

MIR:

```text
Load(place)
```

có nghĩa:

> đọc giá trị hiện tại của place theo memory semantics.

---

# 17. Store

```text
Store(place, value)
```

có nghĩa:

> thay thế semantic value tại place.

---

# 18. Load không nhất thiết là machine load

Ví dụ:

```axiom
let x = a
```

compiler có thể giữ `x` trong register.

Không cần:

```text
memory load
```

---

# 19. Store không nhất thiết là machine store

```axiom
x = 5
```

có thể chỉ thay đổi SSA value.

---

# 20. Memory operation chỉ xuất hiện khi storage semantics yêu cầu

Ví dụ:

```text
address observable
volatile
atomic
FFI
shared memory
escaping pointer
```

---

# 21. Semantic memory vs register

Axiom không coi register là một memory location.

Compiler được phép scalarize.

---

# 22. Scalar replacement

```axiom
struct Point {
    x: f32
    y: f32
}
```

có thể trở thành:

```text
px = ...
py = ...
```

không cần materialize `Point`.

---

# 23. Khi nào phải materialize?

Nếu:

```text
address_of(point)
```

hoặc:

```text
FFI
volatile
atomic
stable storage
```

yêu cầu.

---

# 24. Address formation

Raw address chỉ xuất hiện tại system/unsafe boundary hoặc explicit storage API.

Ví dụ conceptual:

```axiom
let p = unsafe { address_of(x) }
```

---

# 25. Address ≠ provenance

Đây là rule cực kỳ quan trọng:

```text
numeric address
```

không tự động trở thành:

```text
valid Axiom pointer
```

---

# 26. Integer → pointer

Không có safe implicit conversion.

System layer phải establish:

```text
provenance
validity
alignment
bounds
access
lifetime
```

---

# 27. Pointer dereference

```axiom
unsafe {
    *p
}
```

requires established contract.

---

# 28. Raw pointer does not own

```text
*const T
*mut T
```

không tạo ownership.

---

# 29. Raw pointer can be copied

Machine pointer value có thể Copy.

Nhưng:

```text
Copy(pointer)
```

không tạo thêm ownership.

---

# 30. Pointer → `view`

Có thể:

```text
unsafe raw pointer
        ↓
validated capability
        ↓
view<T>
```

nếu contract chứng minh được.

---

# 31. Pointer → `mut_view`

Cần thêm:

```text
exclusive access
non-overlap
valid lifetime
```

---

# 32. Unsafe boundary

Ví dụ:

```axiom
unsafe {
    make_mut_view(p, len)
}
```

không có nghĩa:

> compiler tắt memory safety.

Nó có nghĩa:

> programmer/system contract cung cấp facts mà compiler không tự chứng minh được.

---

# 33. Sau unsafe

Verifier tiếp tục kiểm tra:

```text
view lifetime
alias conflicts
Send
Share
Drop
escape
```

---

# 34. Unaligned memory

Axiom phân biệt:

```text
aligned access
unaligned access
packed representation
```

---

# 35. Default

Typed load/store yêu cầu alignment phù hợp với type.

---

# 36. Unaligned

System library có thể cung cấp:

```text
read_unaligned<T>
write_unaligned<T>
```

với semantics rõ ràng.

---

# 37. Không tự động dùng unaligned

Compiler không được silently biến ordinary access thành unaligned access nếu ABI/semantic contract không cho phép.

---

# 38. `@repr(packed)`

Packed layout là system/unsafe concern.

Field access có thể cần unaligned load.

---

# 39. Bitcast

```text
BITCAST<T,U>
```

khác load/store.

Nó giữ bit pattern nhưng phải satisfy:

```text
size
alignment
valid representation
```

---

# 40. Cast

```text
CAST<T,U>
```

thay đổi semantic value theo conversion rules.

---

# 41. `memcpy`

Semantic copy of bytes chỉ hợp lệ khi representation contract cho phép.

Không dùng memcpy để giả định mọi T đều bitwise-copyable.

---

# 42. Copy trait

`Copy` là semantic property.

Không đồng nghĩa:

```text
memcpy(sizeof(T))
```

luôn là đúng abstraction.

---

# 43. Initialization states

MIR phải track:

```text
UNINIT
INIT
MOVED
PARTIALLY_MOVED
DROPPED
```

---

# 44. Read from UNINIT

Compile error.

---

# 45. Drop UNINIT

Không được thực hiện semantic Drop.

---

# 46. Partial initialization

Ví dụ:

```text
p.x = 1
p.y = 2
```

Verifier có thể track:

```text
p.x = INIT
p.y = INIT
```

---

# 47. Partial move

```text
let x = p.x
```

có thể làm:

```text
p.x = MOVED
p.y = OWNED
```

nếu type/Drop contract cho phép.

---

# 48. Custom Drop

Type có custom Drop không được phép partial move theo frozen ownership rules.

---

# 49. MaybeUninit

Library/system abstraction có thể model:

```text
MaybeUninit<T>
```

nhưng compiler vẫn phải hiểu initialization state khi lowering unsafe primitives.

---

# 50. `assume_init`

Unsafe operation:

```text
MaybeUninit<T>.assume_init()
```

establishes:

```text
INIT(T)
```

chỉ dưới programmer contract.

---

# 51. Verifier không tự tin tưởng mọi unsafe

Unsafe không phải:

```text
skip verifier
```

mà là:

```text
trusted precondition
→ resume verification
```

---

# 52. Volatile

Volatile là memory operation có observable semantics.

Nó không phải:

```text
atomic
```

và không phải:

```text
synchronization
```

---

# 53. Volatile load

```text
volatile_load(place)
```

phải được thực hiện theo target/system semantics.

Compiler không được remove vì “không thấy dùng”.

---

# 54. Volatile store

Tương tự.

---

# 55. Volatile ordering

Axiom không mặc định biến volatile thành full memory fence.

Platform semantics xác định ordering.

---

# 56. Atomic

Atomic là semantic operation trên shared memory.

Ví dụ:

```text
atomic_load
atomic_store
atomic_exchange
compare_exchange
fetch_add
```

---

# 57. Atomic type

```axiom
Atomic<T>
```

là abstraction khác:

```text
T
```

---

# 58. Không implicit atomic conversion

Không thể:

```text
Atomic<i32>
→
mut_view<i32>
```

---

# 59. Vì sao?

Điều đó phá vỡ atomicity.

---

# 60. Atomicity ≠ ordering

Một atomic operation có:

```text
atomicity
+
memory ordering
```

Hai thuộc tính riêng.

---

# 61. Memory order

Axiom hỗ trợ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không cần `Consume` trong Core v1.

---

# 62. Relaxed

Đảm bảo atomicity nhưng không tạo đầy đủ synchronization ordering.

---

# 63. Release

Publication boundary.

---

# 64. Acquire

Consumption/synchronization boundary.

---

# 65. Release → Acquire

Nếu cùng atomic synchronization relation:

```text
Thread A
write data
release(flag)

        ↓

Thread B
acquire(flag)
read data
```

có happens-before relation theo memory model.

---

# 66. SeqCst

Atomic operation tham gia global sequentially consistent order theo semantics.

---

# 67. Fence

Fence là operation riêng.

Không nên giả định:

```text
atomic
```

và:

```text
fence
```

là cùng một thứ.

---

# 68. Compiler barrier

Compiler barrier:

```text
prevent compiler motion
```

khác CPU hardware fence.

---

# 69. Hardware fence

CPU/GPU instruction barrier.

Axiom phải giữ hai abstraction riêng.

---

# 70. No generic `barrier()` ambiguity

System API nên expose explicit semantics:

```text
compiler_fence
memory_fence
thread_fence
gpu_fence
```

nếu cần.

---

# 71. Happens-before

Axiom concurrency model:

```text
sequenced-before
+
synchronizes-with
→
happens-before
```

theo transitive closure.

---

# 72. Load/store reordering

Compiler được phép reorder ordinary operations nếu observable semantics unchanged.

---

# 73. Atomic reorder

Không được reorder vượt qua memory-order constraints.

---

# 74. Volatile reorder

Không được phá vỡ volatile semantics của target/system contract.

---

# 75. FFI

Unknown foreign call có thể:

```text
read memory
write memory
synchronize
modify globals
```

trừ khi contract chứng minh hẹp hơn.

---

# 76. FFI memory effects

Ví dụ:

```text
extern fn c_fn(p: *mut T)
```

compiler không được giả định `p` unchanged nếu contract không nói.

---

# 77. FFI aliasing

Default conservative:

```text
MAY_ALIAS
```

nếu không có contract.

---

# 78. `@noalias`

System/FFI annotation có thể establish stronger alias contract.

Không phải Core source-level feature v0.1.

---

# 79. Memory-mapped files

Mapped file:

```text
File
 ↓
MemoryMap
 ↓
view<T>
```

lifetime của view phụ thuộc mapping.

Unmap khi view còn live → invalid.

Verifier phải chặn.

---

# 80. DMA

DMA buffer có thêm external/device actor.

Compiler cần contract:

```text
CPU ownership
DMA ownership
completion event
```

---

# 81. CPU → DMA

Có thể transfer ownership/capability:

```text
CPU
 ↓
submit
 ↓
DMA owns buffer
 ↓
completion
 ↓
CPU regains ownership
```

---

# 82. Không được truy cập buffer khi DMA owns it

Nếu mutable CPU capability conflict:

→ compile/API-level rejection.

---

# 83. GPU

GPU buffer tương tự:

```text
Host capability
Device capability
GpuEvent
```

---

# 84. Memory domain

Axiom semantic memory operation có:

```text
StorageDomain
AddressSpace
AccessMode
```

---

# 85. CPU address spaces

Normal:

```text
Process
```

System layer có thể thêm:

```text
MMIO
kernel
physical
```

---

# 86. GPU address spaces

Đã frozen:

```text
Host
Device
Shared
Local
Private
Constant
External
```

---

# 87. Address-space mismatch

Không implicit convert:

```text
Device pointer
→ Host pointer
```

---

# 88. Transfer

Phải explicit:

```text
copy_to_device
copy_to_host
map
unmap
```

hoặc zero-copy abstraction.

---

# 89. Zero-copy

Zero-copy không có nghĩa:

> mọi pointer đều dùng chung.

Nó nghĩa:

> hai execution domains được cấp capability tới cùng storage hoặc ownership được chuyển mà không copy.

---

# 90. Cache coherence

Không giả định GPU/CPU coherence trừ khi target contract chứng minh.

---

# 91. Memory ordering + GPU

GPU atomics/barriers có thêm:

```text
scope
address space
execution domain
```

---

# 92. MIR memory operation model

Conceptual:

```text
Load {
    place
    type
    access
    alignment
    ordering?
    volatile?
}

Store {
    place
    value
    access
    alignment
    ordering?
    volatile?
}
```

Atomic riêng:

```text
AtomicOp {
    location
    operation
    ordering
    scope
}
```

---

# 93. Why separate AtomicOp?

Để optimizer không vô tình biến:

```text
atomic load
```

thành ordinary load.

---

# 94. Memory operation effects

EffectInfo có:

```text
Read
Write
Atomic
Volatile
Synchronize
Foreign
```

---

# 95. Memory operation + capability

Verifier phải prove:

```text
Load → READ capability
Store → WRITE capability
Move → OWNERSHIP transfer
Drop → DROP capability
```

---

# 96. Ordinary owner access

Owner có thể tạo ephemeral view.

Ví dụ:

```axiom
fn sum(a: view<i32>) -> i32
```

caller:

```axiom
sum(array)
```

Compiler tạo capability tạm thời.

---

# 97. Mutable call

```axiom
fn sort(a: mut_view<i32>)
```

caller phải provide exclusive capability.

---

# 98. Compiler-generated address

Source:

```axiom
sort(a)
```

có thể lower:

```text
address(a)
length(a)
call sort
```

nhưng programmer không cần viết pointer.

---

# 99. Nested field access

```axiom
foo(s.a.b)
```

Compiler tracks exact Place:

```text
s → Field(a) → Field(b)
```

---

# 100. Disjoint fields

```axiom
fn f(a: mut_view<A>, b: mut_view<B>)
```

có thể cùng tồn tại nếu verifier chứng minh regions disjoint.

---

# 101. Unknown overlap

Không chứng minh được:

→ reject safe program.

---

# 102. Runtime bounds do not automatically prove alias disjointness

Ví dụ hai dynamic slices:

```text
a[0..n]
b[0..m]
```

không mặc định disjoint chỉ vì programmer nghĩ chúng khác nhau.

---

# 103. Explicit disjoint API

Library có thể cung cấp:

```text
split_at_mut
chunks_mut
windows_mut
```

với proven contracts.

---

# 104. Compiler then knows

```text
left ≠ right
```

và có thể generate internal:

```text
NO_ALIAS
```

---

# 105. This feeds optimizer

```text
Capability verifier
        ↓
Region facts
        ↓
AliasInfo
        ↓
NoAlias
        ↓
load/store optimization
```

---

# 106. NoAlias is derived, never guessed

```text
UNKNOWN ≠ NO_ALIAS
```

là invariant cực kỳ quan trọng.

---

# 107. Memory SSA

After semantic verification:

```text
MIR
 ↓
MemorySSA
```

tracks memory definitions/uses.

---

# 108. MemorySSA doesn't redefine semantics

It is optimization representation.

---

# 109. MemorySSA and volatile

Volatile operations are explicit memory effects.

---

# 110. MemorySSA and atomic

Atomic operations are synchronization-aware memory effects.

---

# 111. MemorySSA and FFI

Unknown foreign writes create conservative clobbers unless contract narrows them.

---

# 112. Load forwarding

Legal only if:

```text
same memory
+
no intervening write
+
no volatile/atomic constraint
+
no foreign clobber
+
alias proof
```

---

# 113. Store forwarding

Same principle.

---

# 114. Dead store elimination

Can remove store only if no observable read/effect can observe it.

---

# 115. Volatile prevents DSE

Nếu volatile store observable:

→ cannot remove.

---

# 116. Atomic store

Cannot simply remove because value “looks unused”; synchronization semantics may be observable.

---

# 117. Mutex

Lock/unlock create synchronization effects.

---

# 118. Channel

Send/receive create synchronization and ownership-transfer effects.

---

# 119. Process/shared memory

OS shared memory is external synchronization domain.

Compiler must use explicit contract.

---

# 120. Signal/MMIO

External asynchronous modification requires volatile/atomic/system semantics.

---

# 121. Pointer escape

If raw pointer escapes:

```text
EscapeInfo = ExternalEscape
```

optimizer becomes conservative around affected memory.

---

# 122. But not entire program

Escape is region-sensitive.

Only affected storage becomes conservative.

---

# 123. Stack promotion

If no address escape:

```text
heap allocation
→ stack
```

or:

```text
stack
→ register
```

---

# 124. Address escape blocks scalarization

If API can observe address:

```text
Point
→ memory object
```

must preserve required identity.

---

# 125. Stable address contract

Only explicit contract makes address stable.

Ordinary local variable can move.

---

# 126. Relocation

Vector growth:

```text
old storage
→ new storage
```

is legal if no active capability requires old address.

---

# 127. Active view blocks relocation

```text
view(vec)
vec.push(...)
```

may be rejected if push could relocate and invalidate the view.

---

# 128. Reallocation

Compiler/library can know whether operation definitely relocates or may relocate.

---

# 129. Reserve

`reserve` does not permanently guarantee address stability.

Only explicit storage contract does.

---

# 130. `Box`

`Box<T>` may have stable address only when address is explicitly observed/contracted.

---

# 131. Machine representation

Axiom must not mandate:

```text
Box<T> = heap pointer
```

at semantic level.

---

# 132. But when address escapes

Compiler materializes appropriate storage.

---

# 133. Atomic alignment

Atomic type requires target-supported alignment and size.

If unsupported:

```text
compiler error
```

or library fallback using lock-based implementation where type semantics allow.

---

# 134. Atomic fallback

`Atomic<T>` semantic atomicity does not necessarily imply hardware lock-free implementation.

---

# 135. `is_lock_free`

Can be target-dependent runtime/compile-time property.

---

# 136. Volatile type validity

Volatile access requires representation suitable for target memory operation.

---

# 137. Volatile is not for synchronization

Programmer should use Atomic/Mutex/Channel for synchronization.

---

# 138. MMIO

MMIO APIs may use volatile.

Example conceptual:

```text
reg.read_volatile()
reg.write_volatile(value)
```

---

# 139. MMIO ordering

Device-specific barriers are explicit system APIs.

---

# 140. Compiler cannot infer device protocol

Axiom only preserves specified memory effects.

---

# 141. Persistent storage

File-backed memory is not ordinary RAM semantically.

Persistence requires explicit flush/sync protocol.

---

# 142. Serialization

Memory layout ≠ wire layout.

Do not serialize raw struct bytes unless explicit `WireSafe`/representation contract.

---

# 143. Endianness

Memory access uses native target endianness.

Wire format explicitly specifies endian.

---

# 144. Network buffers

Zero-copy parser can create:

```text
view<u8>
```

into network buffer.

Lifetime follows buffer ownership.

---

# 145. Buffer reuse

Cannot reuse/mutate buffer while parser view is live if regions overlap.

---

# 146. Compiler-generated loads

Optimizer may combine loads:

```text
a.x
a.y
```

into vector load if semantics permit.

---

# 147. Vector load

Physical representation may differ from source operations.

Semantics remain equivalent.

---

# 148. Atomic vectorization

Atomic operations cannot be arbitrarily vectorized if atomic granularity changes.

---

# 149. Volatile vectorization

Cannot combine separate volatile accesses unless target contract explicitly permits.

---

# 150. Floating-point loads

Normal numeric semantics apply.

Fast-math may change permitted optimization set only under explicit profile/annotation.

---

# 151. Trap representations

Types must define valid representations.

Reading invalid representation is not automatically permitted.

---

# 152. Uninitialized bytes

Padding bytes are not necessarily semantic values.

---

# 153. Bytewise equality

Not equivalent to semantic equality.

Especially:

```text
NaN
padding
niches
```

---

# 154. Object representation

Semantic value:

```text
T
```

can have:

```text
representation R(T)
```

chosen by compiler.

---

# 155. Memory access pipeline

Final model:

```text
Source
 ↓
Place construction
 ↓
Type/ownership/capability verification
 ↓
Memory semantics
 ↓
Verified MIR
 ↓
Alias + Effect + MemorySSA
 ↓
Optimization
 ↓
ABI representation
 ↓
Machine memory instruction
```

---

# 156. No semantic pointer language

Programmer normally writes:

```axiom
x.field
a[i]
foo(x)
```

rather than:

```text
&p
*p
p + offset
```

---

# 157. Yet compiler remains low-level

Internally it can reason about:

```text
address
offset
alignment
alias
lifetime
region
memory effect
```

---

# 158. This matches the Axiom philosophy

> **Programmer sees values and capabilities; compiler sees memory topology.**

---

# 159. Unsafe remains powerful

System programmer can eventually write:

```text
raw pointer
pointer arithmetic
MMIO
DMA
custom allocator
ABI bridge
kernel code
```

without forcing ordinary application code to use those mechanisms.

---

# 160. No hidden cost

A safe abstraction can compile down to:

```text
one pointer
one length
one load
```

when all checks are statically proven/eliminated.

---

# 161. No hidden checks when unnecessary

For:

```axiom
fn sum(a: view<i32>) -> i32
```

if caller length is known and loop analysis proves bounds:

→ no runtime bounds check may remain.

---

# 162. But safety first

If proof fails:

```text
keep check
```

rather than generate potentially unsafe code.

---

# 163. Diagnostics

Compiler should explain:

```text
AMEM-E001
cannot prove index is within bounds
```

```text
AMEM-E002
cannot prove two mutable views are disjoint
```

```text
AMEM-E003
raw pointer lacks established validity contract
```

```text
AMEM-E004
unaligned access requires explicit operation
```

```text
AMEM-E005
atomic operation requires supported target representation
```

```text
AMEM-E006
volatile operation cannot be used as ordinary synchronization
```

```text
AMEM-E007
storage may relocate while capability is live
```

---

# 164. CompilerDB additions

```text
MemoryDB
PlaceDB
MemoryOpDB
AddressDB
ProvenanceDB
AtomicDB
VolatileDB
MemoryOrderDB
AlignmentDB
```

---

# 165. IDs

```text
PlaceId
ProjectionId
MemoryOpId
AddressExprId
ProvenanceId
AtomicOpId
MemoryOrderId
AddressSpaceId
StorageRegionId
```

---

# 166. MIR additions

```text
Load
Store
CopyFrom
MoveFrom
AddressOf
MakeView
MakeMutView
AtomicLoad
AtomicStore
AtomicRmw
AtomicCmpXchg
Fence
CompilerFence
VolatileLoad
VolatileStore
```

---

# 167. Important distinction

`AddressOf` is not automatically an observable address.

Compiler may represent it symbolically until ABI/system semantics require materialization.

---

# 168. Address observability

Address becomes semantically observable if it:

```text
escapes
is compared
is converted to integer
is passed to FFI
is stored externally
is used as identity
```

according to safe/system rules.

---

# 169. Pointer comparison

Raw pointer comparison remains unsafe/system-level.

Compiler cannot assume arbitrary pointer integers preserve provenance.

---

# 170. Pointer equality

Even equal numeric addresses do not automatically imply same semantic object under all provenance contracts.

---

# 171. Integer pointer round-trip

System-specific.

Must preserve/re-establish required provenance contract.

---

# 172. Memory safety invariant

Every safe load must have:

```text
valid provenance
+
valid lifetime
+
READ capability
+
valid representation
+
valid alignment
```

---

# 173. Safe store

Every safe store must have:

```text
valid provenance
+
valid lifetime
+
WRITE capability
+
valid representation
+
valid alignment
```

---

# 174. Safe atomic

Additionally:

```text
atomic-compatible location
+
valid ordering
+
valid scope
```

---

# 175. Safe volatile

Additionally:

```text
volatile-compatible storage
+
system contract
```

---

# 176. DMA access

Additionally:

```text
device ownership
+
completion synchronization
```

---

# 177. GPU access

Additionally:

```text
execution domain
+
address space
+
GPU legality
```

---

# 178. FFI access

Additionally:

```text
FfiContract
```

---

# 179. MMIO

Additionally:

```text
device register contract
```

---

# 180. Optimizer contract

Optimization can only transform:

```text
Verified MIR
```

and must preserve:

```text
memory semantics
ownership
capability
effects
atomic ordering
volatile observability
external behavior
```

---

# 181. Translation validation

For aggressive memory optimizations:

```text
Before MIR
     ↓
transform
     ↓
After MIR
     ↓
prove semantic equivalence
```

---

# 182. Example

Source:

```axiom
fn add(a: view<i32>, b: view<i32>) -> i32 {
    a[0] + b[0]
}
```

Verifier establishes:

```text
a[0] valid
b[0] valid
a READ
b READ
```

If regions are disjoint:

```text
NO_ALIAS(a,b)
```

---

# 183. Optimizer may produce

```text
load a
load b
add
```

without runtime alias checks.

---

# 184. If alias unknown

Still legal:

```text
load a
load b
```

but optimizer cannot assume independence for transformations that require it.

---

# 185. Mutable example

```axiom
fn add_into(
    out: mut_view<i32>,
    a: view<i32>,
    b: view<i32>
)
```

Verifier checks overlap relations.

---

# 186. If `out` overlaps `a`

Operation may be legal or illegal depending on API contract.

Language does not guess.

---

# 187. If algorithm requires disjoint

Library can establish:

```text
requires disjoint(out,a,b)
```

through safe API construction.

---

# 188. If overlap is intentionally allowed

Function semantics explicitly define ordering.

Then compiler must preserve that semantic behavior.

---

# 189. Memory ordering does not solve aliasing

Atomic does not mean:

```text
no alias
```

Atomicity and aliasing are independent dimensions.

---

# 190. Ownership does not solve ordering

Send only transfers ownership.

It does not establish:

```text
happens-before
```

unless channel/synchronization semantics provide it.

---

# 191. Capability does not automatically synchronize

`mut_view` gives exclusive access but does not establish cross-thread publication unless execution model says so.

---

# 192. Three independent questions

Axiom therefore keeps:

```text
Who owns it?
Can I access it?
When is access ordered?
```

as separate semantic dimensions.

---

# 193. Fourth question

And:

```text
Where does it execute?
```

for CPU/GPU/thread/task domains.

---

# 194. Unified memory model

```text
Ownership
    │
    ├── Move
    ├── Send
    └── Share

Capability
    │
    ├── READ
    └── WRITE

Synchronization
    │
    ├── Atomic
    ├── Mutex
    ├── Channel
    └── Fence

Storage
    │
    ├── Local
    ├── Static
    ├── TLS
    ├── Heap
    ├── Device
    └── External

Execution
    │
    ├── CPU
    ├── Thread
    ├── Task
    └── GPU
```

---

# 195. Đây là mô hình rất mạnh

Nó cho phép Axiom tránh hai cực:

```text
C/C++
→ programmer chịu quá nhiều memory details
```

và:

```text
GC language
→ runtime chịu quá nhiều memory management
```

Axiom chọn:

```text
Programmer:
    ownership intent
    access intent
    explicit unsafe boundaries

Compiler:
    lifetime
    alias
    address
    storage
    register allocation
    memory optimization
```

---

# 196. Frozen invariants

```text
AMEM-20
Place represents a semantic storage location.

AMEM-21
A Place consists of a base and zero or more projections.

AMEM-22
Field access forms a field projection.

AMEM-23
Index access forms an index projection.

AMEM-24
Dereference forms a dereference projection.

AMEM-25
Place identity is distinct from physical address.

AMEM-26
A semantic Place need not have materialized storage.

AMEM-27
A compiler may scalarize a Place when address observability permits.

AMEM-28
Address materialization is required only when semantic or ABI obligations require it.

AMEM-29
Raw addresses do not inherently carry Axiom ownership.

AMEM-30
Raw addresses do not inherently carry safe capabilities.

AMEM-31
Numeric integers are not automatically valid Axiom pointers.

AMEM-32
Pointer provenance is distinct from numeric address value.

AMEM-33
Safe dereference requires valid provenance.

AMEM-34
Safe dereference requires valid lifetime.

AMEM-35
Safe loads require valid read capability.

AMEM-36
Safe stores require valid write capability.

AMEM-37
Safe memory access requires valid representation.

AMEM-38
Safe memory access requires valid alignment.

AMEM-39
Uninitialized memory cannot be safely read.

AMEM-40
Dropped memory cannot be safely accessed.

AMEM-41
Moved memory cannot be safely accessed without reinitialization.

AMEM-42
Partial initialization is tracked at place granularity.

AMEM-43
Partial moves are tracked at place granularity when permitted.

AMEM-44
Custom Drop forbids unsafe partial-move states.

AMEM-45
MaybeUninit-style abstractions must preserve initialization invariants.

AMEM-46
Unsafe initialization assumptions do not bypass subsequent verification.

AMEM-47
Owner-to-view conversion does not transfer ownership.

AMEM-48
A view does not own its referent.

AMEM-49
A mutable view represents exclusive write capability.

AMEM-50
Read capabilities may coexist when regions permit.

AMEM-51
Conflicting write capabilities are rejected in safe code.

AMEM-52
Unknown overlap is never treated as disjoint.

AMEM-53
Proven disjoint regions may be represented internally as NO_ALIAS.

AMEM-54
NO_ALIAS is a derived compiler fact, not a programmer assertion in Core v1.

AMEM-55
Pointer copying does not create ownership.

AMEM-56
Pointer copying does not create additional safe capability.

AMEM-57
Pointer-to-view conversion requires an established safety contract.

AMEM-58
Pointer-to-mut_view conversion requires exclusive-access proof or trusted system contract.

AMEM-59
Unaligned access requires explicit supported semantics.

AMEM-60
Packed representations may require unaligned system operations.

AMEM-61
Bitcast is distinct from semantic cast.

AMEM-62
Bitcast requires valid representation conditions.

AMEM-63
Bytewise copying does not imply semantic Copy.

AMEM-64
Memory load is distinct from semantic value acquisition.

AMEM-65
Memory store is distinct from semantic assignment.

AMEM-66
Registers and SSA values are not semantic memory locations.

AMEM-67
Ordinary values may remain entirely outside memory.

AMEM-68
Observable addresses constrain storage optimization.

AMEM-69
Stable-address contracts constrain relocation.

AMEM-70
A live capability may prevent storage relocation.

AMEM-71
A storage relocation cannot invalidate a live safe capability.

AMEM-72
Vector growth may relocate storage when no stability contract is active.

AMEM-73
Reserve does not imply permanent address stability.

AMEM-74
Volatile is distinct from atomic.

AMEM-75
Volatile is distinct from synchronization.

AMEM-76
Volatile operations are observable memory operations.

AMEM-77
Volatile operations cannot be removed as ordinary dead operations.

AMEM-78
Volatile does not automatically imply a full hardware fence.

AMEM-79
Atomicity is distinct from memory ordering.

AMEM-80
Atomic operations have explicit ordering semantics.

AMEM-81
Supported Core atomic orders are Relaxed, Acquire, Release, AcqRel, and SeqCst.

AMEM-82
Consume ordering is not required by Core v1.

AMEM-83
Atomic operations cannot be silently replaced by ordinary operations when semantics would change.

AMEM-84
Atomic<T> does not implicitly become ordinary T access.

AMEM-85
Atomic<T> does not implicitly produce mut_view<T>.

AMEM-86
Atomic operations participate in the Axiom happens-before model.

AMEM-87
Release/Acquire synchronization establishes ordering according to the memory model.

AMEM-88
SeqCst operations participate in the global sequentially consistent order.

AMEM-89
Compiler fences are distinct from hardware memory fences.

AMEM-90
Hardware fences are target-specific implementations of explicit memory semantics.

AMEM-91
Ordinary memory operations may be reordered when observable semantics remain unchanged.

AMEM-92
Atomic ordering constraints restrict legal reordering.

AMEM-93
Volatile constraints restrict legal reordering.

AMEM-94
Synchronization effects restrict legal reordering.

AMEM-95
Unknown foreign calls are conservative memory-effect boundaries.

AMEM-96
FFI contracts may narrow foreign memory effects.

AMEM-97
Unknown foreign aliasing is never treated as NO_ALIAS.

AMEM-98
FFI pointer ownership is determined by explicit FFI contracts.

AMEM-99
Memory-mapped storage requires explicit lifetime and mapping contracts.

AMEM-100
A mapped view cannot outlive its mapping.

AMEM-101
DMA access requires explicit ownership/completion semantics.

AMEM-102
CPU access cannot conflict with active DMA ownership.

AMEM-103
GPU memory is a distinct storage domain.

AMEM-104
GPU address spaces are distinct from ordinary CPU address spaces.

AMEM-105
Host/device capability conversion is never implicit.

AMEM-106
GPU synchronization is part of memory semantics.

AMEM-107
GPU memory operations include execution and address-space constraints.

AMEM-108
Persistent storage is distinct from volatile memory.

AMEM-109
Serialization representation is distinct from memory representation.

AMEM-110
Wire endianness is distinct from native memory endianness.

AMEM-111
Network-buffer views obey ordinary capability lifetime rules.

AMEM-112
Buffer reuse cannot invalidate live safe views.

AMEM-113
Memory operations contribute to EffectInfo.

AMEM-114
Memory operations contribute to AliasInfo.

AMEM-115
Memory operations contribute to MemorySSA.

AMEM-116
Verified capability facts may feed optimizer alias analysis.

AMEM-117
Optimizer alias facts cannot weaken semantic safety.

AMEM-118
Optimizer cannot manufacture a safe capability from UNKNOWN facts.

AMEM-119
Dead-store elimination cannot remove observable memory effects.

AMEM-120
Load forwarding requires proof of memory equivalence and absence of invalidating effects.

AMEM-121
Store forwarding requires proof of memory equivalence and absence of invalidating effects.

AMEM-122
Volatile accesses inhibit ordinary dead-store elimination.

AMEM-123
Atomic operations inhibit transformations that would change atomic semantics.

AMEM-124
Foreign calls inhibit memory transformations according to their declared effects.

AMEM-125
Address escape may require materialized storage.

AMEM-126
Address escape is tracked by EscapeInfo.

AMEM-127
Escape analysis may remain region-sensitive.

AMEM-128
Nonescaping storage may be promoted to registers or stack.

AMEM-129
Heap allocation may be eliminated when storage identity is unobservable.

AMEM-130
Stable address is an explicit semantic contract.

AMEM-131
Stable-address contracts may prevent allocation elimination.

AMEM-132
MMIO access requires explicit system semantics.

AMEM-133
Device registers may require volatile operations.

AMEM-134
Device-specific ordering requires explicit system contracts.

AMEM-135
Unsafe does not disable the memory verifier.

AMEM-136
Unsafe may establish trusted machine-level preconditions.

AMEM-137
Safe verification resumes after an unsafe boundary.

AMEM-138
Unsafe cannot convert UNKNOWN semantic facts into verified facts without an explicit trusted contract.

AMEM-139
Every safe load has valid provenance, lifetime, access, representation, and alignment.

AMEM-140
Every safe store has valid provenance, lifetime, access, representation, and alignment.

AMEM-141
Every safe atomic access additionally satisfies atomic-location and ordering requirements.

AMEM-142
Every safe volatile access additionally satisfies its system memory contract.

AMEM-143
Every safe GPU access additionally satisfies execution-domain and address-space requirements.

AMEM-144
Every safe DMA access additionally satisfies ownership and completion requirements.

AMEM-145
Every FFI memory access additionally satisfies its FFI contract.

AMEM-146
Verified MIR is the correctness boundary for memory optimization.

AMEM-147
Memory optimization cannot change observable memory semantics.

AMEM-148
Memory semantics are independent of physical register allocation.

AMEM-149
Memory semantics are independent of stack versus heap placement when storage identity is unobservable.

AMEM-150
Memory semantics are independent of target instruction selection.

AMEM-151
Memory semantics are independent of optimization level.

AMEM-152
Memory semantics are independent of object-file section placement.

AMEM-153
Memory semantics are preserved across ABI lowering.

AMEM-154
Memory semantics are preserved across GPU lowering.

AMEM-155
Memory semantics are preserved across FFI lowering.

AMEM-156
Memory semantics are covered by reference-interpreter and MIR conformance tests.

AMEM-157
Atomic semantics are covered by concurrency litmus tests.

AMEM-158
Volatile semantics are covered by system conformance tests.

AMEM-159
Pointer provenance is covered by unsafe adversarial tests.

AMEM-160
Initialization states are covered by ownership verifier tests.

AMEM-161
Alias-derived optimization facts are covered by miscompilation regression tests.

AMEM-162
Memory ordering is covered by target-specific concurrency tests.

AMEM-163
DMA/GPU memory contracts are covered by execution-domain tests.

AMEM-164
No safe program may perform an invalid memory access.

AMEM-165
No optimizer transformation may rely on an unproven memory fact.

AMEM-166
No physical memory optimization may change the semantic meaning of a Place.

AMEM-167
No implicit pointer/reference syntax is required for ordinary safe memory access.

AMEM-168
Low-level memory control remains available through explicit system and unsafe mechanisms.

AMEM-169
Compiler complexity may exceed programmer-visible memory complexity.

AMEM-170
The memory model remains deterministic and explicitly specified.
```

---

## Kết quả kiến trúc

Sau BOOTSTRAP-256, đường đi của một access trong Axiom đã khá hoàn chỉnh:

```text
                    SOURCE
                      │
               x.field / a[i]
                      │
                      ▼
                    Place
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
      Ownership    Capability    Provenance
          │           │            │
          └───────────┼────────────┘
                      ▼
                Memory Semantics
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
        Load        Store       Atomic/Volatile
          │           │            │
          └───────────┼────────────┘
                      ▼
                 Verified MIR
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
       AliasInfo   MemorySSA   EffectInfo
          │           │            │
          └───────────┼────────────┘
                      ▼
                    OptIR
                      │
                      ▼
                   Axiom LIR
                      │
                      ▼
                Machine Memory
```

Điểm đáng chú ý là **Axiom đã có một abstraction rất mạnh mà không cần biến programmer thành người viết pointer arithmetic**.

---

# BOOTSTRAP-257 — tiếp theo

Bước logic kế tiếp là **AXIOM CONTROL-FLOW IR, SSA, PHI, DOMINANCE & STRUCTURED CONTROL LOWERING**.

Ta sẽ chốt sâu:

```text
if
match
loop
while
for
break
continue
return
?
panic
unwind
async suspension
generator suspension
```

→

```text
CFG
BasicBlock
Terminator
Dominance
SSA
Phi
MemorySSA
Critical Edge
Loop
Exception/Unwind Edge
Cleanup Edge
```

Đây là phần cần làm thật chắc trước khi đi sâu tiếp vào **machine backend/register allocation**, bởi ownership/drop/capability của Axiom phụ thuộc rất mạnh vào CFG và dominance.