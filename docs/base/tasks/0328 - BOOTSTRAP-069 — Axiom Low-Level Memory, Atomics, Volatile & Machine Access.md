Tiếp tục.

# BOOTSTRAP-069 — Axiom Low-Level Memory, Atomics, Volatile & Machine Access

**Trạng thái: FROZEN**

Đây là lớp cuối nối **safe Axiom → unsafe/system → CPU/GPU/hardware/OS**. Mục tiêu là Axiom đủ mạnh để viết:

- allocator;
- kernel/driver;
- OS runtime;
- lock-free data structure;
- networking stack;
- embedded firmware;
- SIMD/memory primitives;
- FFI;
- MMIO/DMA;

nhưng programmer bình thường **không phải sống với pointer và memory barrier**.

Nguyên tắc:

> **Safe code mô tả ý định. Unsafe code được phép mô tả máy.**

---

# 1. Ba loại memory access

Axiom phân biệt hoàn toàn:

```text
1. Ordinary memory access
2. Atomic memory access
3. Volatile memory access
```

Không được coi:

```text
volatile == atomic
atomic == volatile
```

Đây là lỗi thiết kế rất nguy hiểm trong systems language.

---

# 2. Ordinary access

Thông thường:

```axiom id="8huj4p"
x = value
y = x
```

được compiler tối ưu tự do nếu không có observable effect.

Compiler có thể:

- reorder;
- eliminate;
- combine;
- cache register;
- vectorize;
- load/store forwarding.

Miễn là memory model được bảo toàn.

---

# 3. Atomic

Atomic là semantic type/operation riêng.

Ví dụ library:

```axiom id="3b6ec0"
var counter: Atomic<u64>

counter.fetch_add(1, Relaxed)
```

Atomic operation có:

```text
atomicity
ordering
scope
```

không chỉ đơn giản là "đọc/ghi không bị xé".

---

# 4. Atomic không biến dữ liệu thành `mut_view`

Ví dụ:

```axiom id="2ddq7q"
Atomic<u64>
```

không được tự động chuyển thành:

```text
mut_view<u64>
```

Lý do:

Atomic access và ordinary mutable access là **hai access protocols khác nhau**.

Nếu cho phép chuyển đổi, programmer có thể phá vỡ memory model.

---

# 5. Memory ordering

Axiom giữ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không cần `Consume` trong Core v1.

Ví dụ:

```axiom id="f4fy5j"
flag.store(true, Release)
```

và:

```axiom id="0i0ppg"
if flag.load(Acquire) {
    ...
}
```

có thể tạo synchronizes-with relationship theo memory model đã freeze.

---

# 6. Relaxed

`Relaxed` đảm bảo atomicity của atomic operation nhưng không tạo publication ordering như Acquire/Release.

Ví dụ counter:

```axiom id="2u7ybi"
counter.fetch_add(1, Relaxed)
```

phù hợp khi chỉ cần atomic modification.

Không được compiler biến atomic thành ordinary load/store.

---

# 7. Acquire / Release

Acquire/Release là primitive cho publication.

```text id="4gt8m7"
Thread A:

data = ...
ready.store(true, Release)

             ↓
          synchronize

Thread B:

ready.load(Acquire)
data
```

Nếu synchronizes-with xảy ra, các ordinary writes trước Release được nhìn thấy theo memory model.

---

# 8. SeqCst

`SeqCst` tạo ordering mạnh hơn theo global sequential-consistency rules.

Không nên dùng nó mặc định.

Nhưng phải tồn tại vì một số algorithm cần semantics này.

Compiler vẫn được phép tối ưu nếu kết quả tuân thủ memory model.

---

# 9. Atomic width

Atomic type:

```text id="6kwk0u"
Atomic<T>
```

chỉ hợp lệ nếu target có atomic support phù hợp hoặc compiler có runtime/library fallback theo explicit contract.

Không được giả định:

```text
Atomic<u128>
```

luôn lock-free.

---

# 10. Lock-free không phải semantic guarantee

Các thuộc tính:

```text id="w9cvpy"
lock-free
wait-free
obstruction-free
blocking
```

là implementation properties/API contracts riêng.

Ví dụ:

```text id="kg7g9d"
Atomic<u64>
```

không đồng nghĩa:

> luôn lock-free.

Nếu programmer cần guarantee:

```text id="e3v4xk"
is_lock_free<T>()
```

hoặc compile-time capability có thể được cung cấp.

---

# 11. Atomic compare-exchange

Core/library phải hỗ trợ:

```text id="3u3xmr"
compare_exchange
compare_exchange_weak
```

với success/failure ordering rõ ràng.

Ví dụ:

```axiom id="5k2m7n"
atomic.compare_exchange(
    expected,
    desired,
    AcqRel,
    Acquire
)
```

Compiler không được tự ý thay đổi ordering.

---

# 12. Atomic wait / notify

Hỗ trợ abstraction:

```text id="e0v7la"
wait(value)
notify_one()
notify_all()
```

nhưng:

> notification không phải publication.

Tức:

```text id="h71m5k"
notify()
```

không tự tạo synchronizes-with relationship ngoài contract của primitive.

---

# 13. Fence

Axiom cần memory fence ở system/library/compiler layer.

Ví dụ conceptually:

```text id="g1u1pd"
fence(Acquire)
fence(Release)
fence(SeqCst)
```

Fence không phải magic "đồng bộ mọi thứ".

Semantics phải được định nghĩa theo memory model và target lowering.

---

# 14. Compiler barrier vs CPU fence

Hai khái niệm khác nhau:

```text id="4if5b3"
Compiler barrier
CPU memory fence
```

Compiler barrier ảnh hưởng reordering của compiler.

CPU fence ảnh hưởng ordering quan sát bởi hardware.

Không nên nhập chúng thành một primitive mơ hồ.

System layer có thể cung cấp cả hai.

---

# 15. Volatile

`volatile` dành cho:

- MMIO;
- device registers;
- memory mapped hardware;
- một số firmware/hardware interface.

Ví dụ conceptually:

```axiom id="h3s6y9"
volatile_read<T>(address)
volatile_write<T>(address, value)
```

Volatile nghĩa:

> compiler không được loại bỏ/gộp/reorder operation theo cách vi phạm volatile contract.

Nó **không có nghĩa**:

- atomic;
- thread-safe;
- synchronization;
- acquire/release.

---

# 16. MMIO

Ví dụ driver:

```text id="c4z3i4"
DEVICE_REGISTER
      ↓
raw pointer
      ↓
volatile_read / volatile_write
```

Đây thuộc unsafe/system.

Không cho phép ordinary:

```axiom id="bq1d4e"
*p = value
```

tự nhiên trở thành volatile chỉ vì `p` trỏ vào hardware.

Volatile intent phải explicit.

---

# 17. DMA

DMA tạo một vấn đề khác:

> thiết bị có thể truy cập storage ngoài CPU execution model.

Do đó Axiom cần storage/external ownership contract đã chuẩn bị từ trước.

Ví dụ conceptually:

```text id="p8c5yh"
DmaBuffer<T>
```

library/system abstraction.

Không nên biến DMA thành Core pointer primitive.

---

# 18. Cache coherence

Axiom không giả định:

> mọi device memory đều coherent với CPU.

Storage domain đã được freeze:

```text id="8ey8f4"
Host
Device
Shared
External
```

API phải xác định:

```text id="6d6i3v"
ownership
visibility
synchronization
cache/domain semantics
```

riêng biệt.

---

# 19. Raw pointer

Raw pointer:

```axiom id="plp2u0"
*const T
*mut T
```

là machine-level value.

Nó:

- không sở hữu;
- không tự có lifetime;
- không tự có capability;
- không tự đảm bảo validity;
- có thể được copy;
- có thể được truyền qua FFI.

Dereference:

```axiom id="6shxgj"
*p
```

là unsafe.

---

# 20. Pointer provenance

Một integer:

```axiom id="n7v3j0"
let address: usize
```

không tự động trở thành valid pointer.

Không được coi:

```text id="e4h8fz"
usize
↓
*mut T
```

là conversion an toàn.

System layer có explicit operation:

```text id="8b1lq3"
pointer_from_address(...)
```

và operation này unsafe.

---

# 21. Pointer arithmetic

Các phép:

```text id="ihv9an"
p + n
p - n
p.offset(n)
```

unsafe.

Compiler không cần cố chứng minh mọi pointer arithmetic trong system code.

Nhưng sau unsafe boundary, nếu programmer chuyển pointer thành:

```text id="qk3f7f"
view<T>
```

thì phải establish contract về:

- validity;
- alignment;
- initialized memory;
- length;
- provenance;
- aliasing;
- lifetime.

Sau đó verifier tiếp tục làm việc bình thường.

---

# 22. Raw memory copy

Axiom cần primitive tương đương:

```text id="k7e6ol"
copy
copy_nonoverlapping
fill
compare
```

ở low-level library/intrinsic.

Nhưng phải phân biệt:

```text id="9dxq4k"
typed move
typed copy
raw byte copy
```

Raw byte copy không tự động thực hiện Drop/ownership semantics.

---

# 23. `memcpy` không phải semantic Move

Ví dụ:

```text id="4f2h4s"
copy bytes(A, B)
```

không có nghĩa:

```text id="0w8j75"
B = Move(A)
```

Move là ownership-state transition.

Byte copy là machine operation.

Đây là một invariant rất quan trọng để optimizer không phá Drop semantics.

---

# 24. Initialization state

MIR tiếp tục theo dõi:

```text id="whk52d"
UNINIT
INIT
MOVED
DROPPED
```

Raw memory allocation:

```text id="q7n4v6"
allocate<T>()
```

không tự tạo một initialized `T`.

System code phải initialize trước khi safe typed access.

---

# 25. Uninitialized memory

Có thể có abstraction:

```text id="6w6s5c"
MaybeUninit<T>
```

ở low-level library.

Ví dụ conceptually:

```axiom id="u4g6ls"
var storage: MaybeUninit<T>
```

Sau khi initialization:

```text id="5duv8d"
assume_init()
```

là unsafe hoặc operation yêu cầu compiler proof.

Không cho phép safe code đọc uninitialized value.

---

# 26. Alignment

Mỗi type có:

```text id="e8j5mz"
size
alignment
```

được LayoutDB xác định.

Ordinary typed access yêu cầu alignment hợp lệ.

Unaligned access phải explicit:

```text id="4u0q3q"
read_unaligned<T>()
write_unaligned<T>()
```

ở low-level layer.

---

# 27. Packed structures

`@repr(packed)` đã được xác định là unsafe/system-level.

Lý do:

```text id="5t9f5x"
packed field
    ↓
may be unaligned
    ↓
ordinary typed access unsafe
```

Compiler không tự thêm penalty cho toàn bộ chương trình.

---

# 28. Endianness

Endianness **không nên là property mặc định của Axiom integer type**.

`u32` là semantic integer.

Khi cần byte representation:

```text id="8y5x7c"
to_le
to_be
from_le
from_be
```

hoặc equivalent APIs.

Compiler có thể map:

```text id="f2i6q0"
byte_swap
```

thành native instruction.

---

# 29. Serialization ≠ memory representation

Không được dùng:

```text id="vl2av4"
@repr(C)
```

để ngụ ý:

> đây là wire format.

Memory representation và serialization representation là hai contract khác nhau.

Ví dụ network packet:

```text id="7h6nzo"
Axiom value
   ↓
serializer
   ↓
explicit byte format
```

---

# 30. Bit-level access

Cần compiler/library primitives:

```text id="sjjq8b"
bitcast
extract_bits
insert_bits
mask
rotate
byte_swap
```

để system programmer không phải dùng pointer tricks.

Ví dụ:

```axiom id="hly6zv"
let bits = bitcast<u32>(f)
```

giữ nguyên bit pattern nếu representation contract hợp lệ.

---

# 31. `unsafe` không phải optimization mode

Không chấp nhận tư duy:

```text id="0r3h54"
safe = slow
unsafe = fast
```

Axiom compiler có thể tạo native code rất mạnh từ safe code.

`unsafe` chỉ cần khi:

```text id="7dfyab"
compiler cannot prove a machine-level precondition
```

Ví dụ:

```text
raw pointer
MMIO
custom allocator
intrinsic
inline asm
FFI
unaligned memory
```

---

# 32. Unsafe boundary

Mô hình:

```text id="22vr7v"
SAFE
  │
  ▼
unsafe operation
  │
  ▼
trusted precondition established
  │
  ▼
SAFE CAPABILITY
  │
  ▼
normal verifier resumes
```

Không phải:

```text id="v7gn7t"
unsafe
  ↓
compiler turns brain off
```

Đây là điểm rất quan trọng.

---

# 33. Inline assembly

Inline asm:

```text id="v0e9v4"
asm(...)
```

chỉ ở unsafe/system.

Phải khai báo:

- inputs;
- outputs;
- clobbers;
- memory effects;
- flags/state effects;
- volatile-ness nếu có;
- target constraints.

Ví dụ conceptually:

```text id="q8b8i4"
asm {
    ...
    inputs(...)
    outputs(...)
    clobbers(...)
}
```

Compiler không được đoán clobber.

---

# 34. Naked functions

`@naked` thuộc system layer.

Compiler không được tự tạo:

```text id="f2h1g0"
prologue
epilogue
stack frame
```

trong naked function nếu contract cấm.

Programmer chịu trách nhiệm machine ABI.

---

# 35. Interrupt functions

`@interrupt` là system ABI contract.

Có thể khác function bình thường về:

- register preservation;
- return instruction;
- stack;
- interrupt state;
- ABI.

Không phải một function annotation bình thường.

---

# 36. CPU instruction intrinsics

Compiler intrinsic nên có API có cấu trúc:

```text id="k0x2ar"
intrinsic::x86::...
intrinsic::arm::...
intrinsic::riscv::...
```

hoặc tương đương.

Target-specific code không làm bẩn portable Core.

---

# 37. Memory operations và optimizer

Optimizer phải hiểu:

```text id="7j0p9b"
Load
Store
Atomic
Volatile
Fence
IO
Foreign
```

khác nhau.

Ví dụ:

```text id="p9a1mc"
ordinary load
```

có thể CSE.

Nhưng:

```text id="x6ef8m0"
volatile load
```

không được CSE tùy tiện.

Atomic cũng không được biến thành ordinary load.

---

# 38. Atomic + capability

Một `Atomic<T>` có thể được chia sẻ theo `Share` semantics.

Nhưng:

```text id="4w6ztt"
Share(Atomic<T>)
```

không tạo:

```text id="0f9w1k"
mut_view<T>
```

Thay vào đó access protocol là:

```text id="aqv0b7"
AtomicLoad
AtomicStore
AtomicRMW
AtomicCAS
```

Điều này giúp verifier phân biệt concurrent access đúng bản chất.

---

# 39. Volatile + capability

Tương tự:

```text id="db5nkk"
volatile_read
volatile_write
```

là explicit memory effects.

Không được coi volatile write là synchronization.

Nếu hardware/device cần ordering:

```text id="9c0cgy"
volatile
+
appropriate fence
```

theo platform contract.

---

# 40. Memory model cuối cùng

Có thể nhìn toàn bộ low-level model:

```text
                  MEMORY
                    │
       ┌────────────┼────────────┐
       │            │            │
   Ordinary      Atomic       Volatile
       │            │            │
    compiler      ordering     observable
   optimized       model       access
       │            │            │
       └────────────┼────────────┘
                    │
                 Unsafe
                    │
       ┌────────────┼─────────────┐
       │            │             │
 Raw Pointer   Inline ASM       MMIO/DMA
       │            │             │
       └────────────┼─────────────┘
                    │
              Trusted Contract
                    │
                    ▼
              Safe Capability
```

---

# Frozen Invariants — `AMEMLOW-20..100`

### Ordinary memory

- **AMEMLOW-20** Ordinary memory access is distinct from atomic access.
- **AMEMLOW-21** Ordinary memory access is distinct from volatile access.
- **AMEMLOW-22** Ordinary loads/stores may be optimized when semantics permit.
- **AMEMLOW-23** Optimizer must preserve the Axiom memory model.
- **AMEMLOW-24** Ordinary access cannot violate safe capability rules.
- **AMEMLOW-25** Typed access requires valid initialization.
- **AMEMLOW-26** Typed access requires valid alignment.
- **AMEMLOW-27** Raw byte operations do not automatically establish typed ownership.

### Atomic

- **AMEMLOW-28** Atomic operations are semantically distinct from ordinary operations.
- **AMEMLOW-29** Atomicity does not imply synchronization ordering.
- **AMEMLOW-30** Relaxed, Acquire, Release, AcqRel and SeqCst are distinct orderings.
- **AMEMLOW-31** Atomic ordering cannot be silently weakened.
- **AMEMLOW-32** Atomic ordering cannot be silently strengthened when observable semantics change.
- **AMEMLOW-33** Atomic operations preserve atomicity.
- **AMEMLOW-34** Atomic does not imply lock-free.
- **AMEMLOW-35** Lock-free status is distinct from atomic semantics.
- **AMEMLOW-36** Atomic wait/notify does not automatically imply publication.
- **AMEMLOW-37** Atomic access does not create ordinary mutable capabilities.
- **AMEMLOW-38** Atomic compare-exchange preserves success/failure ordering semantics.
- **AMEMLOW-39** Atomic fences are distinct from ordinary operations.
- **AMEMLOW-40** Atomic semantics are preserved across optimization.

### Volatile

- **AMEMLOW-41** Volatile access is distinct from atomic access.
- **AMEMLOW-42** Volatile access is distinct from synchronization.
- **AMEMLOW-43** Volatile operations are observable memory operations.
- **AMEMLOW-44** Volatile operations cannot be eliminated when observable.
- **AMEMLOW-45** Volatile does not imply atomicity.
- **AMEMLOW-46** Volatile does not imply happens-before.
- **AMEMLOW-47** Device/MMIO access uses explicit volatile semantics.
- **AMEMLOW-48** Required device ordering requires an explicit ordering contract.

### Raw pointers

- **AMEMLOW-49** Raw pointers are unsafe/system-level values.
- **AMEMLOW-50** Raw pointers do not imply ownership.
- **AMEMLOW-51** Raw pointers do not imply capability.
- **AMEMLOW-52** Raw pointers do not imply lifetime validity.
- **AMEMLOW-53** Raw pointer copying does not copy ownership.
- **AMEMLOW-54** Raw pointer dereference is unsafe.
- **AMEMLOW-55** Pointer arithmetic is unsafe.
- **AMEMLOW-56** Integer addresses are not automatically valid pointers.
- **AMEMLOW-57** Pointer provenance is distinct from numeric address.
- **AMEMLOW-58** Raw pointer to safe capability conversion requires an unsafe contract.
- **AMEMLOW-59** Safe verification resumes after a valid unsafe boundary.

### Initialization / representation

- **AMEMLOW-60** Uninitialized storage is distinct from initialized values.
- **AMEMLOW-61** Safe code cannot read uninitialized typed storage.
- **AMEMLOW-62** Raw byte copying does not imply typed Move.
- **AMEMLOW-63** Raw byte copying does not imply typed Copy.
- **AMEMLOW-64** Typed Move remains an ownership-state operation.
- **AMEMLOW-65** Alignment is part of typed memory validity.
- **AMEMLOW-66** Unaligned typed access requires explicit low-level semantics.
- **AMEMLOW-67** Packed representation may create unaligned fields.
- **AMEMLOW-68** Packed access is unsafe/system-level.
- **AMEMLOW-69** Endianness is distinct from integer type identity.
- **AMEMLOW-70** Byte-order conversion is explicit.
- **AMEMLOW-71** Memory representation is distinct from serialization format.

### Low-level machine access

- **AMEMLOW-72** Compiler intrinsics may expose target-specific machine operations.
- **AMEMLOW-73** Target-specific intrinsics are isolated from portable Core semantics.
- **AMEMLOW-74** Inline assembly is unsafe/system-level.
- **AMEMLOW-75** Inline assembly declares operands and machine effects.
- **AMEMLOW-76** Inline assembly clobbers are explicit.
- **AMEMLOW-77** Inline assembly cannot silently invalidate compiler assumptions.
- **AMEMLOW-78** Naked functions are explicit system ABI contracts.
- **AMEMLOW-79** Interrupt functions are explicit system ABI contracts.
- **AMEMLOW-80** Machine-specific instructions do not redefine Axiom source semantics.

### DMA / external memory

- **AMEMLOW-81** DMA memory is an explicit storage/external-resource abstraction.
- **AMEMLOW-82** Device access may involve storage domains distinct from CPU memory.
- **AMEMLOW-83** Host/device visibility is explicit.
- **AMEMLOW-84** Device synchronization is distinct from CPU synchronization.
- **AMEMLOW-85** DMA cannot invalidate a live safe capability.
- **AMEMLOW-86** External devices require explicit ownership contracts.
- **AMEMLOW-87** External memory is not implicitly safe merely because it has an address.

### Compiler guarantees

- **AMEMLOW-88** Unsafe is not an optimization mode.
- **AMEMLOW-89** Safe code may receive the same low-level optimization opportunities when proofs exist.
- **AMEMLOW-90** Compiler barriers are distinct from CPU fences.
- **AMEMLOW-91** CPU fences are target-lowered according to memory-model semantics.
- **AMEMLOW-92** Memory effects are represented explicitly in optimization IR.
- **AMEMLOW-93** Atomic, volatile and IO effects constrain optimization.
- **AMEMLOW-94** Unknown foreign memory effects are treated conservatively.
- **AMEMLOW-95** Backend cannot reinterpret memory semantics.
- **AMEMLOW-96** Backend cannot manufacture atomic or synchronization guarantees.
- **AMEMLOW-97** Backend cannot remove required volatile effects.
- **AMEMLOW-98** Low-level operations preserve ownership and capability invariants.
- **AMEMLOW-99** Unsafe boundaries are explicit semantic boundaries.
- **AMEMLOW-100** Machine-level freedom does not weaken safe-language guarantees outside the unsafe boundary.

---

## Một điểm tôi muốn điều chỉnh so với cách nhiều language thiết kế

Axiom **không nên có một "unsafe mode" rộng** kiểu:

```text
unsafe {
    // từ đây compiler mặc kệ
}
```

Mà nên có:

```text
unsafe {
    raw pointer operation
}
```

sau đó compiler quay lại kiểm tra bình thường.

Ví dụ:

```text
safe
 ↓
unsafe pointer arithmetic
 ↓
validate/establish capability
 ↓
safe mut_view
 ↓
ordinary Axiom
```

Như vậy programmer systems-level vẫn có toàn bộ sức mạnh của máy, nhưng **unsafe không trở thành một lỗ thủng xuyên suốt compiler**.

---

## Kiến trúc Axiom hiện tại đã khá hoàn chỉnh

Từ `BOOTSTRAP-020` đến `069`, chúng ta đã gần như khóa toàn bộ **semantic foundation**:

```text
Language
├── Syntax
├── Type System
├── Value / Ownership
├── Capability / View
├── Memory
├── Collections
├── Numeric
├── Control Flow
├── Functions / Closures
├── Generics / Traits
├── Error / Panic
├── Async
├── Concurrency
├── GPU
├── Comptime / Reflection
├── FFI
├── ABI
├── Modules / Packages
└── Low-level Machine Access
        │
        ▼
Compiler
├── HIR
├── MIR
├── Verification
├── OptIR
├── ABI MIR
├── LIR
├── Machine IR
├── Object Writer
└── Linker
        │
        ▼
Native
├── PE/COFF
├── ELF
├── Mach-O
├── WASM
└── GPU
```

**Bước tiếp theo nên chuyển từ semantic foundation sang một phần rất lớn còn thiếu:**

### `BOOTSTRAP-070 — Axiom Standard Concurrency & Synchronization Library`

Phần này sẽ thiết kế cụ thể `Mutex`, `RwLock`, `Semaphore`, `Channel`, `Atomic`, `Arc`, thread, task, executor, structured concurrency và cách tất cả chúng sử dụng **Ownership + Capability + Send/Share + Memory Model** mà không tạo ra một runtime bắt buộc.