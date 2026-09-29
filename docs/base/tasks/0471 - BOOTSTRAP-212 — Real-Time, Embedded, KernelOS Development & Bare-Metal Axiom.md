# BOOTSTRAP-212 — Real-Time, Embedded, Kernel/OS Development & Bare-Metal Axiom

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 212 là kiểm chứng một yêu cầu nền tảng của Axiom:

> **Axiom không chỉ là ngôn ngữ ứng dụng hiệu năng cao; nó phải có khả năng đi xuống tận bootloader, firmware, driver, kernel và bare-metal mà không cần GC, OS runtime hay allocator bắt buộc.**

Kiến trúc:

```text
Application
     │
     ▼
 Hosted Axiom
     │
 ┌───┴──────────────────────────────┐
 │                                  │
Embedded                         OS/Kernel
 │                                  │
 ├── RTOS                           ├── Scheduler
 ├── Firmware                       ├── VM
 ├── Driver                         ├── Driver
 └── Bare Metal                     └── Filesystem
            │
            ▼
       Hardware / CPU
```

---

# 212.1. Freestanding là profile chính thức

Axiom phải có profile:

```text
hosted
freestanding
kernel
embedded
boot
```

Không profile nào thay đổi Core semantics.

Profile chỉ xác định **những capability/runtime/platform nào tồn tại**.

---

# 212.2. Không có hidden OS assumption

Core code không được mặc định giả sử tồn tại:

```text
filesystem
process
thread
heap
TLS
network
console
dynamic loader
```

Ví dụ một chương trình freestanding có thể chỉ cần:

```text
startup
stack
CPU
memory
```

---

# 212.3. Runtime-free

Một binary tối thiểu có thể:

```text
_start
    ↓
main
    ↓
exit/halt
```

hoặc thậm chí:

```text
_start
    ↓
infinite loop
```

không cần runtime.

---

# 212.4. Custom entry point

System profile cho phép:

```axiom
@entry
fn boot() -> never {
    ...
}
```

Compiler không tự động thêm `main` semantics nếu target không yêu cầu.

---

# 212.5. Startup contract

Startup chịu trách nhiệm target-specific:

```text
reset vector
stack initialization
BSS zeroing
data relocation
CPU initialization
runtime initialization
entry
```

Compiler chỉ tạo artifact theo startup ABI.

---

# 212.6. No implicit global initialization

Freestanding binary không được tự động kéo vào:

```text
global constructors
reflection registry
allocator
panic runtime
```

nếu không dùng.

---

# 212.7. Static data

Có thể khai báo static storage:

```text
static COUNTER: Atomic<u32> = Atomic::new(0)
```

với initialization contract rõ ràng.

---

# 212.8. Initialization phases

Target có thể định nghĩa:

```text
ZeroInit
ConstInit
EarlyInit
RuntimeInit
ApplicationInit
```

Không được tùy tiện tạo initialization order phụ thuộc source order nếu observable.

---

# 212.9. Interrupt

Interrupt không phải function call bình thường.

Concept:

```axiom
@interrupt
fn timer_irq(frame: InterruptFrame) {
    ...
}
```

Compiler phải kiểm tra ABI/target contract.

---

# 212.10. Interrupt execution domain

Thêm execution context:

```text
Application
Interrupt
Exception
NMI
```

Interrupt context có restrictions riêng.

---

# 212.11. Interrupt không được await

Một interrupt handler không được:

```text
await
```

hoặc block.

Compiler reject.

---

# 212.12. Interrupt allocation

Mặc định không allocation:

```text
@interrupt
```

không được gọi allocator trừ khi target contract cho phép.

---

# 212.13. Interrupt-safe operations

Tooling có thể phân tích:

```text
blocking
allocation
locking
IO
```

và reject operation không hợp lệ.

---

# 212.14. Exception handlers

CPU exception:

```text
page_fault
invalid_opcode
general_protection
```

có ABI riêng.

Không nhầm với Axiom `panic`.

---

# 212.15. Panic trong kernel

Kernel có thể chọn:

```text
abort
halt
panic_handler
debug_break
```

không cần unwind.

---

# 212.16. `never`

`never` đặc biệt quan trọng cho:

```text
halt
panic
interrupt loop
scheduler
```

---

# 212.17. MMIO

Memory-mapped I/O phải có abstraction riêng.

Ví dụ conceptual:

```axiom
let status = mmio.read<u32>(STATUS_ADDR)
```

Đây không phải ordinary memory access.

---

# 212.18. Volatile

MMIO sử dụng:

```text
volatile read
volatile write
```

với semantics riêng.

Volatile:

```text
≠ atomic
≠ synchronization
≠ ordinary memory
```

---

# 212.19. Compiler không được xóa MMIO

Ví dụ:

```axiom
mmio.write(REG, 1)
mmio.write(REG, 1)
```

không được CSE/eliminate chỉ vì cùng value.

---

# 212.20. Device register types

Có thể tạo abstraction:

```text
Register<T>
ReadOnlyRegister<T>
WriteOnlyRegister<T>
ReadWriteRegister<T>
```

ở system library.

---

# 212.21. Bitfield registers

Comptime có thể generate:

```text
register.enable()
register.mode(3)
register.clear_status()
```

từ register specification.

Generated code vẫn được verifier kiểm tra.

---

# 212.22. Hardware addresses

Hardware address là:

```text
machine address
```

không phải safe Axiom pointer.

Chuyển đổi cần system/unsafe contract.

---

# 212.23. Physical address ≠ virtual address

Axiom phải phân biệt:

```text
PhysicalAddress
VirtualAddress
```

ở OS/system layer.

---

# 212.24. Raw pointer provenance

Nguyên tắc pointer model hiện tại vẫn giữ:

```text
integer address
    ≠
valid pointer
```

Bare-metal không được phá vỡ nguyên tắc này.

---

# 212.25. Unsafe hardware access

Ví dụ:

```axiom
unsafe {
    let p = physical_to_ptr(addr)
    ...
}
```

unsafe chỉ thiết lập trusted precondition.

Sau boundary, safe capability phải được xác minh lại.

---

# 212.26. DMA

DMA resource cần:

```text
DMABuffer<T>
```

với contract:

```text
CPU ownership
device ownership
transfer
completion
```

---

# 212.27. DMA ownership

Một buffer đang được device sử dụng không được CPU tùy tiện mutate.

Mô hình:

```text
CPU Owned
   ↓ submit
Device Owned
   ↓ completion
CPU Owned
```

---

# 212.28. DMA completion

Completion phải thiết lập synchronization trước khi CPU đọc dữ liệu.

---

# 212.29. DMA zero-copy

Có thể đạt:

```text
NIC
 ↓
DMA Buffer
 ↓
Parser
```

không copy nếu capability/lifetime/layout hợp lệ.

---

# 212.30. Device memory

Storage domain bổ sung:

```text
Device
MMIO
DMA
Physical
Mapped
```

nhưng không đưa tất cả thành Core storage primitives.

---

# 212.31. Cache coherency

DMA contract phải biết target:

```text
coherent
non-coherent
```

Nếu non-coherent cần:

```text
flush
invalidate
barrier
```

---

# 212.32. Cache maintenance

Compiler không được tự xóa các operation có observable hardware effect.

---

# 212.33. Memory barriers

Phân biệt:

```text
CompilerBarrier
CPUFence
DeviceFence
DMAFence
```

---

# 212.34. Atomic vs fence

Atomic operation:

```text
read-modify-write
```

khác:

```text
fence
```

và khác:

```text
volatile
```

---

# 212.35. Bare-metal atomics

Target phải khai báo:

```text
supported atomic widths
lock-free widths
memory ordering
```

CompilerDB sử dụng TargetSpec.

---

# 212.36. Unsupported atomics

Nếu target không hỗ trợ atomic width:

```text
Atomic<u128>
```

compiler không được giả vờ nó lock-free.

Có thể:

```text
library fallback
```

hoặc reject.

---

# 212.37. Physical memory allocator

Kernel layer có thể implement:

```text
PageAllocator
FrameAllocator
SlabAllocator
BuddyAllocator
```

đều là library/system abstractions.

---

# 212.38. Page

Kernel có:

```text
Page
Frame
PageTableEntry
```

đây là logical system types.

---

# 212.39. Virtual memory

VM subsystem quản lý:

```text
VirtualAddress
PhysicalFrame
PageTable
Mapping
Permission
```

---

# 212.40. Page permissions

Representation:

```text
Read
Write
Execute
User
Kernel
Global
CachePolicy
```

---

# 212.41. W^X

Security profile mặc định ưu tiên:

```text
Writable XOR Executable
```

trừ khi target/loader contract yêu cầu khác.

---

# 212.42. Executable memory

JIT/kernel code generation cần explicit capability:

```text
allocate executable memory
```

không phải ordinary allocator behavior.

---

# 212.43. Kernel/user boundary

OS API phải phân biệt:

```text
KernelAddress
UserAddress
```

và không cho safe kernel code tùy tiện dereference user pointer.

---

# 212.44. User pointer validation

Kernel API:

```text
copy_from_user
copy_to_user
```

có thể tạo safe capability sau validation.

---

# 212.45. User memory race

Validation không tự động đảm bảo memory không thay đổi.

Kernel abstraction phải xác định:

```text
copy semantics
pinning/locking
fault handling
```

---

# 212.46. Page fault

Page fault là asynchronous hardware event.

Không coi nó là ordinary `Result`.

---

# 212.47. Scheduler

Kernel scheduler là library/system component:

```text
Runnable
Running
Blocked
Sleeping
Exited
```

---

# 212.48. Context switch

Context switch có machine-specific ABI.

Compiler/backend phải hỗ trợ:

```text
save registers
restore registers
stack switch
TLS switch
```

khi system layer yêu cầu.

---

# 212.49. Stackful execution

Kernel threads/fibers có thể dùng explicit stack storage.

Không cần `Pin<T>` Core.

---

# 212.50. Stable stack address

Stack address có thể là explicit storage contract nếu cần:

```text
StableStorage
```

---

# 212.51. Thread-local storage

TLS là optional storage domain.

Bare-metal có thể:

```text
no TLS
```

hoặc implement custom TLS.

---

# 212.52. Per-CPU storage

Kernel có thể có:

```text
PerCpu<T>
```

semantic identity:

```text
CPU-local instance
```

---

# 212.53. Per-CPU không phải global mutable

Mỗi CPU có instance riêng.

Compiler không cần coi đó là một shared mutable object.

---

# 212.54. Interrupt-safe synchronization

Không phải Mutex nào cũng được dùng trong interrupt context.

API/type contract phải phân biệt:

```text
IRQ-safe
Thread-only
Blocking
NonBlocking
```

---

# 212.55. Spinlock

Kernel library:

```text
SpinLock<T>
```

với guard ownership semantics.

---

# 212.56. Spinlock guard

Guard:

```text
!Copy
Drop → unlock
```

giống Mutex guard hiện tại.

---

# 212.57. Interrupt disable guard

Có thể có:

```text
InterruptGuard
```

Drop khôi phục interrupt state.

---

# 212.58. Nested interrupt state

Guard phải lưu trạng thái trước đó:

```text
enabled
disabled
mask
priority
```

không chỉ gọi `enable()` khi Drop.

---

# 212.59. Real-time locking

RT profile có thể cấm:

```text
unbounded allocation
unbounded lock wait
unbounded recursion
```

---

# 212.60. Priority inversion

Tooling/runtime có thể hỗ trợ:

```text
priority inheritance
priority ceiling
```

nhưng đây là scheduler/synchronization policy.

---

# 212.61. Deadline

Real-time task có:

```text
deadline
period
budget
priority
```

---

# 212.62. Hard real-time contract

Axiom không tự tuyên bố:

> function này luôn chạy dưới 10 µs.

Thay vào đó, platform/profile phải cung cấp guarantee.

---

# 212.63. WCET

Tooling có thể hỗ trợ:

```text
WorstCaseExecutionTime
```

nhưng đây không phải property compiler có thể luôn tự chứng minh.

---

# 212.64. No hidden allocation

Trong profile:

```text
@realtime
```

compiler có thể reject các path chứa allocation không bounded.

---

# 212.65. No hidden blocking

Tương tự:

```text
blocking call
```

phải bị phát hiện trong realtime context.

---

# 212.66. Embedded panic

Embedded profile có thể chọn:

```text
panic → halt
panic → reset
panic → recovery handler
```

---

# 212.67. Stack overflow

Embedded/kernel profile có thể dùng:

```text
guard page
stack canary
stack limit
static analysis
```

---

# 212.68. Recursion

Recursion không bị cấm Core.

Nhưng realtime/embedded profile có thể yêu cầu:

```text
bounded recursion
```

hoặc reject không chứng minh được.

---

# 212.69. Static allocation

Embedded code có thể chỉ dùng:

```text
static
stack
arena
pool
```

không cần heap.

---

# 212.70. No-allocator program

Compiler phải hỗ trợ:

```text
Allocator = None
```

trong build configuration.

---

# 212.71. No-std

Có thể:

```text
import core
```

mà không link:

```text
std
```

---

# 212.72. Minimal standard library

Axiom library nên phân tầng:

```text
core
system
alloc
std
network
gui
gpu
```

Ví dụ:

```text
core
  ↓
alloc
  ↓
system
  ↓
std
```

không phải dependency bắt buộc ngược lại.

---

# 212.73. Bootloader

Axiom có thể compile boot code:

```text
16-bit
32-bit
64-bit
UEFI
BIOS
ARM
RISC-V
```

thông qua TargetSpec/profile.

---

# 212.74. Boot stages

Có thể:

```text
Stage 0
 ↓
Stage 1
 ↓
Stage 2
 ↓
Kernel
```

mỗi stage có target/profile riêng.

---

# 212.75. Linker script

Axiom linker cần hỗ trợ logical memory layout:

```text
.text
.rodata
.data
.bss
.init
.stack
```

và platform-specific placement.

---

# 212.76. Custom sections

System layer có thể:

```axiom
@section(".boot")
static BOOT_DATA = ...
```

---

# 212.77. Linker symbols

Kernel/boot code có thể cần:

```text
__stack_top
__kernel_start
__kernel_end
```

Axiom linker/object model phải hỗ trợ symbol contracts.

---

# 212.78. Binary layout

Các contract:

```text
section
symbol
alignment
address
region
```

được đưa vào linker layer, không làm Core type system phức tạp.

---

# 212.79. Device driver

Driver architecture:

```text
Hardware
   ↓
MMIO/DMA
   ↓
Driver
   ↓
Device abstraction
   ↓
Kernel
```

Driver không cần class inheritance.

---

# 212.80. Driver interface

Traits + structs đủ:

```axiom
trait DeviceDriver {
    fn probe(...)
    fn start(...)
    fn stop(...)
}
```

Dynamic dispatch chỉ khi cần.

---

# 212.81. Interrupt-driven driver

Driver có thể đăng ký:

```text
IRQ
```

và chuyển event sang normal execution context.

---

# 212.82. Deferred interrupt work

Mô hình:

```text
IRQ
 ↓
minimal handler
 ↓
atomic/event
 ↓
worker/task
 ↓
heavy processing
```

giảm latency.

---

# 212.83. Embedded DMA pipeline

Ví dụ:

```text
ADC
 ↓ DMA
Buffer
 ↓ completion
DSP
 ↓
SIMD
 ↓
Output
```

Axiom ownership có thể biểu diễn toàn bộ pipeline mà không cần lifetime annotations.

---

# 212.84. MMIO + capability

Một register mapping có thể trả:

```text
view<RegisterBlock>
```

nhưng lifetime phải phụ thuộc device mapping.

---

# 212.85. Device lifetime

Nếu:

```text
DeviceMapping
```

bị Drop trong khi register view còn sống:

```text
reject
```

Đây chính xác là capability provenance model đã thiết kế.

---

# 212.86. Kernel memory safety

Safe kernel code vẫn được bảo vệ bởi:

```text
ownership
initialization
capability
alias
```

Unsafe chỉ xuất hiện ở boundary:

```text
page tables
MMIO
context switch
CPU registers
hardware ABI
```

---

# 212.87. Không tạo "kernel mode" thành ngôn ngữ khác

Kernel code vẫn là Axiom.

Khác biệt chủ yếu nằm ở:

```text
TargetSpec
Profile
Capabilities
ABI
Available libraries
```

---

# 212.88. Embedded generics

Generic code phải chạy được trong:

```text
freestanding
```

nếu không phụ thuộc runtime.

---

# 212.89. Compile-time hardware configuration

Comptime rất phù hợp cho:

```text
CPU registers
pin mappings
clock frequencies
memory regions
device capabilities
```

---

# 212.90. Generated hardware code

Ví dụ từ chip description:

```text
comptime
    generate_registers(device_spec)
```

→ declarations

→ normal verification

→ machine code.

---

# 212.91. Device tree

Linux/embedded-style metadata có thể được parse:

```text
comptime
```

hoặc build-time.

Không biến device tree thành Core syntax.

---

# 212.92. Interrupt vector generation

Comptime có thể generate:

```text
InterruptVectorTable
```

từ declarations.

---

# 212.93. ABI exactness

System-level functions có thể yêu cầu:

```text
calling convention
register arguments
stack layout
alignment
preserved registers
```

được mô tả trong ABI contract.

---

# 212.94. Inline assembly

Axiom cần system escape hatch:

```axiom
unsafe asm {
    ...
}
```

nhưng phải khai báo:

```text
inputs
outputs
clobbers
memory effects
```

---

# 212.95. Inline asm effect model

Compiler không được giả định asm là pure.

Có thể:

```text
ReadMemory
WriteMemory
RegisterClobber
ControlFlow
Volatile
```

---

# 212.96. ASM và optimizer

ASM không được phá vỡ verifier semantic boundary.

Compiler biết những gì contract khai báo; phần còn lại thuộc unsafe responsibility.

---

# 212.97. CPU instructions

Target-specific intrinsic có thể tốt hơn inline asm:

```text
rdtsc
cpuid
wfi
fence
crc
aes
```

và được compiler kiểm soát tốt hơn.

---

# 212.98. Kernel build

Một kernel build có thể:

```text
ax build \
  --target=x86_64-unknown-none \
  --profile=kernel
```

và không kéo `std`, allocator hoặc OS runtime.

---

# 212.99. Bare-metal correctness boundary

Production compiler pipeline vẫn:

```text
Source
 ↓
Typed HIR
 ↓
MIR
 ↓
Ownership
 ↓
Capability
 ↓
Unsafe contracts
 ↓
Verified MIR
 ↓
Target lowering
 ↓
Machine code
```

Bare-metal **không có đường tắt bỏ verifier**.

---

# 212.100. Embedded/kernel invariants — `AKERNEL`

### `AKERNEL-20`
Freestanding compilation shall not require an operating system.

### `AKERNEL-21`
Freestanding compilation shall not require a garbage collector.

### `AKERNEL-22`
Freestanding compilation shall not require an allocator.

### `AKERNEL-23`
Freestanding compilation shall not require a monolithic runtime.

### `AKERNEL-24`
Core semantics shall remain identical across hosted and freestanding profiles.

### `AKERNEL-25`
Startup behavior shall be defined by target/profile contracts.

### `AKERNEL-26`
Custom entry points shall be supported.

### `AKERNEL-27`
Global initialization shall not be implicitly required.

### `AKERNEL-28`
Interrupt handlers shall have explicit ABI and execution-domain semantics.

### `AKERNEL-29`
Interrupt handlers shall not implicitly allocate, block, or await.

### `AKERNEL-30`
Hardware exceptions shall remain distinct from language panic.

### `AKERNEL-31`
MMIO shall remain distinct from ordinary memory.

### `AKERNEL-32`
Volatile access shall not be confused with atomic synchronization.

### `AKERNEL-33`
Compiler optimization shall preserve observable MMIO effects.

### `AKERNEL-34`
Physical addresses shall remain distinct from safe Axiom pointers.

### `AKERNEL-35`
DMA ownership shall explicitly track CPU/device ownership.

### `AKERNEL-36`
DMA buffers shall remain valid until operation completion.

### `AKERNEL-37`
DMA synchronization shall respect target cache-coherency rules.

### `AKERNEL-38`
Memory barriers shall distinguish compiler, CPU, device, and DMA semantics.

### `AKERNEL-39`
Unsupported atomic operations shall never silently claim stronger guarantees.

### `AKERNEL-40`
Kernel/user address domains shall remain distinct.

### `AKERNEL-41`
User memory shall not become safe kernel capability without validation.

### `AKERNEL-42`
Validation shall not imply absence of concurrent external mutation.

### `AKERNEL-43`
Virtual-memory mappings shall have explicit permissions.

### `AKERNEL-44`
Executable writable memory shall require an explicit security/system contract.

### `AKERNEL-45`
Kernel synchronization shall obey ownership and capability semantics.

### `AKERNEL-46`
Lock guards shall retain deterministic unlock behavior.

### `AKERNEL-47`
Interrupt synchronization shall restore prior hardware state correctly.

### `AKERNEL-48`
Real-time profiles may prohibit unbounded allocation and blocking.

### `AKERNEL-49`
Real-time claims shall depend on platform guarantees, not language annotations alone.

### `AKERNEL-50`
Embedded programs shall support static and bounded allocation strategies.

### `AKERNEL-51`
Kernel code shall be expressible without class inheritance or GC.

### `AKERNEL-52`
Device drivers shall be implementable using structs, functions, traits, and explicit system contracts.

### `AKERNEL-53`
Comptime may generate hardware descriptions and register abstractions.

### `AKERNEL-54`
Generated hardware code shall re-enter ordinary compiler verification.

### `AKERNEL-55`
Inline assembly shall declare observable machine effects.

### `AKERNEL-56`
Undeclared assembly effects shall not be assumed safe by the compiler.

### `AKERNEL-57`
Target-specific instructions shall remain target-gated.

### `AKERNEL-58`
Kernel compilation shall retain the same ownership verifier as application compilation.

### `AKERNEL-59`
Unsafe hardware code shall establish explicit trusted preconditions.

### `AKERNEL-60`
Safe verification shall resume after an unsafe boundary.

### `AKERNEL-61`
Bare-metal code shall support deterministic resource lifetime.

### `AKERNEL-62`
No hidden runtime dependency may be introduced by unused language features.

### `AKERNEL-63`
Kernel binaries shall support explicit linker section and symbol contracts.

### `AKERNEL-64`
Custom memory layouts shall be expressible without weakening semantic type safety.

### `AKERNEL-65`
Compiler optimizations shall remain legal under freestanding profiles.

### `AKERNEL-66`
Axiom shall support bootloader, firmware, driver, kernel, and application layers.

### `AKERNEL-67`
The language shall not require a separate kernel programming dialect.

### `AKERNEL-68`
Hardware-specific semantics shall remain isolated in system/platform layers.

### `AKERNEL-69`
Freestanding artifacts shall remain compatible with the Axiom object/link model.

### `AKERNEL-70`
Kernel and embedded programs shall remain testable through reference/simulation/hardware backends where available.

---

# 212.101. Kết luận kiến trúc

Sau 212, Axiom có một điểm rất quan trọng:

```text
                    AXIOM CORE
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Hosted       Freestanding    Kernel
          │             │             │
         std          embedded       driver
          │             │             │
        GUI          firmware        VM
        DB             RTOS        scheduler
       Network        device       filesystem
          │             │             │
          └─────────────┼─────────────┘
                        │
                    Hardware
```

**Không cần tạo một "Kernel Axiom" riêng.**

Chỉ có:

```text
Core semantics
+
TargetSpec
+
Execution/Storage domains
+
System contracts
+
Profile
```

Đây là kiến trúc phù hợp với mục tiêu ban đầu của Axiom: **một ngôn ngữ duy nhất từ firmware đến application, từ CPU đến GPU, nhưng không bắt application phải mang theo sự phức tạp của kernel programming.**

---

# BOOTSTRAP-213 — Compiler/Language Support cho Hardware, ISA Extensions, Vector ISA & Machine-Level Programming

**TRẠNG THÁI: NEXT**

Bước tiếp theo sẽ đi sâu hơn một tầng nữa: không chỉ viết kernel, mà phải đảm bảo Axiom **khai thác được phần cứng mới mà không cần thay đổi ngôn ngữ**.

Phạm vi:

```text
x86-64
ARM64
RISC-V
AVX2
AVX-512
SVE/SVE2
NEON
AMX
RISC-V Vector
Crypto ISA
Tensor/Matrix ISA
CPU feature detection
Target multiversioning
Function multiversioning
Instruction selection
Intrinsic
Inline ASM
Register constraints
Calling convention
ABI extensions
CPU dispatch
Fat binary
```

Câu hỏi trung tâm:

> **Axiom làm thế nào để compiler tự khai thác ISA mới và tạo machine code cực kỳ tối ưu, trong khi Core language vẫn ổn định và programmer không phải học lại ngôn ngữ cho từng thế hệ CPU/GPU?**