# BOOTSTRAP-396 — Axiom Operating System Interface, System Calls, Processes & Native System Programming Engine

Sau **395 — Database, Transaction, Query & Persistent Data**, bước tiếp theo nên quay trở lại một tầng thấp hơn nhưng cực kỳ quan trọng đối với mục tiêu ban đầu của Axiom:

> **Axiom phải có khả năng viết trực tiếp hệ thống, OS service, daemon, driver-adjacent code và native application mà không cần một runtime khổng lồ.**

395 đã xây abstraction cho persistent storage. 396 xây **boundary giữa Axiom và operating system / machine environment**.

Mục tiêu là tránh hai cực:

```text
C style:
    mọi thứ là raw syscall / pointer / ABI
```

và:

```text
managed language:
    OS bị che bởi runtime/object model/GC
```

Axiom sẽ có:

```text
Safe high-level system API
        ↓
Axiom System ABI
        ↓
OS ABI / syscall ABI
        ↓
Machine
```

---

# 1. OS không phải Core

Core không chứa:

```text
File
Socket
Process
Thread
Window
Registry
Signal
Environment
```

Core chỉ cung cấp semantic primitives cần thiết.

System library cung cấp:

```text
std.os
std.fs
std.process
std.env
std.signal
std.time
std.console
```

và target-specific modules.

---

# 2. Hosted và Freestanding

Axiom phải hỗ trợ hai profile chính.

### Hosted

```text
OS
 ↓
Axiom program
```

Có:

- filesystem;
- process;
- thread;
- networking;
- dynamic loader;
- console.

### Freestanding

```text
Firmware / bootloader / kernel / bare metal
 ↓
Axiom
```

Không cần:

- OS;
- libc;
- heap;
- thread runtime;
- filesystem;
- exception runtime.

---

# 3. Không có libc bắt buộc

Đây là yêu cầu quan trọng.

Axiom executable có thể:

```text
Axiom
 ↓
own syscall / ABI layer
 ↓
kernel
```

không cần:

```text
Axiom
 ↓
libc
 ↓
kernel
```

Libc vẫn có thể được dùng qua FFI.

---

# 4. System ABI

Compiler phải có một abstraction:

```text
AxiomSystemABI
```

mô tả:

```text
calling convention
syscall convention
register convention
return convention
stack convention
TLS
error convention
process entry
thread entry
```

---

# 5. Target ABI

Mỗi target có:

```text
TargetOS
TargetArch
TargetABI
TargetObjectFormat
TargetCallingConvention
```

Ví dụ:

```text
Windows + x86_64
Linux + x86_64
Linux + AArch64
macOS + AArch64
Android + AArch64
WASM
```

---

# 6. Program Entry

Programmer viết:

```text
fn main() -> i32
```

nhưng compiler có thể generate:

```text
_start
```

hoặc OS-specific entry point.

Không cần runtime `main()` wrapper bắt buộc.

---

# 7. Startup

Startup sequence:

```text
OS
 ↓
Axiom entry
 ↓
initialize minimal process state
 ↓
initialize required TLS
 ↓
main()
 ↓
exit
```

Nếu chương trình không cần initialization runtime:

```text
entry → main
```

có thể cực kỳ nhỏ.

---

# 8. Exit

Process exit semantics:

```text
return code
```

phải được định nghĩa rõ.

Các resources cần cleanup theo profile.

Không được giả định OS sẽ luôn cleanup mọi semantic Drop trước khi process kết thúc nếu profile explicitly cho phép immediate exit.

---

# 9. Process

Process là:

```text
execution + address space + OS resources
```

không phải object hierarchy.

Logical type:

```text
Process
ProcessHandle
```

---

# 10. Process Identity

Không dùng raw PID làm identity abstraction.

```text
ProcessId
```

là logical OS identity.

PID có thể được reuse.

---

# 11. Process Handle

Handle:

```text
ProcessHandle
```

có ownership/capability semantics.

Đóng handle không đồng nghĩa kill process.

---

# 12. Spawn

Process creation:

```text
spawn_process(...)
```

phải có explicit contract.

Ví dụ:

```text
executable
arguments
environment
stdin
stdout
stderr
working_directory
capabilities
```

---

# 13. Process Environment

Environment:

```text
Environment
```

là process resource.

Không nên có global mutable map kiểu:

```text
global_env["X"] = ...
```

mà không có effect semantics.

---

# 14. Environment Variables

Đọc:

```text
env.get("HOME")
```

là external/environment effect.

Compiler biết đây không phải pure computation.

---

# 15. Arguments

Process arguments là immutable startup data.

Có thể materialize thành:

```text
view<Text>
```

nếu lifetime phù hợp.

---

# 16. Current Directory

Current working directory là **process-global mutable state**.

Vì vậy:

```text
set_current_directory(...)
```

là effect có khả năng ảnh hưởng code khác.

Không được coi như ordinary local variable.

---

# 17. File Descriptor / Handle

Axiom không nên expose trực tiếp:

```text
int fd
```

ở safe API.

Dùng:

```text
FileHandle
SocketHandle
PipeHandle
DeviceHandle
```

nhưng underlying representation có thể là integer.

---

# 18. Zero-Cost Handle

Ví dụ:

```text
struct FileHandle {
    raw: usize
}
```

có thể compile thành:

```text
register
```

không object header.

---

# 19. Capability Integration

Đây là nơi 394 kết nối trực tiếp với 396.

Ví dụ:

```text
ReadCapability<File>
WriteCapability<File>
ExecuteCapability<Process>
```

không nhất thiết phải có runtime security object.

Capability có thể compile thành:

```text
OS handle
```

hoặc credential/context tương ứng.

---

# 20. System Call

System call là effect:

```text
SYSCALL
```

Compiler không được coi syscall như pure function.

---

# 21. Syscall ABI

Internal representation:

```text
SYSCALL {
    number
    arguments
    calling_convention
    clobbers
    return
    error
}
```

Target lowering sẽ biến thành instruction sequence phù hợp.

---

# 22. Syscall không nhất thiết là function call

Optimizer có thể inline hoặc emit trực tiếp:

```text
register setup
syscall instruction
```

khi ABI cho phép.

---

# 23. Error Model

OS error không nên phụ thuộc vào:

```text
errno global
```

semantic model:

```text
Result<T, OsError>
```

Nếu target ABI dùng errno, compiler/library có thể lower tương ứng.

---

# 24. OsError

Phân biệt:

```text
PermissionDenied
NotFound
AlreadyExists
InvalidArgument
WouldBlock
Interrupted
TimedOut
ResourceExhausted
BrokenPipe
ConnectionError
Unknown
```

nhưng mapping target-specific.

---

# 25. Interrupted Operations

Một syscall có thể trả:

```text
Interrupted
```

Library quyết định retry nếu operation retry-safe.

Không tự động retry mọi syscall.

---

# 26. Blocking

System API phải khai báo:

```text
blocking
nonblocking
may_block
```

để tích hợp với async engine 360–361.

---

# 27. Async OS Interface

Không để:

```text
async fn read()
```

ngầm biến mọi OS I/O thành thread.

Backend có thể là:

```text
io_uring
IOCP
kqueue
epoll
event port
blocking worker
DMA
```

---

# 28. Memory Mapping

OS memory mapping:

```text
map_memory(...)
```

trả về storage capability.

Phải xác định:

```text
address
length
protection
ownership
shared/private
lifetime
```

---

# 29. Virtual Memory

Axiom không cần expose virtual addresses trong safe code.

System layer có:

```text
VirtualMemory
```

cho:

- reserve;
- commit;
- decommit;
- protect;
- map;
- unmap.

---

# 30. Guard Pages

Compiler/runtime/system library có thể dùng guard pages cho:

- stack;
- arena;
- debug allocation;
- memory protection.

Đây là target optimization/security feature.

---

# 31. Memory Protection

Các quyền:

```text
READ
WRITE
EXECUTE
```

không được xem là ordinary ownership.

Một memory capability cần cả:

```text
ownership
access
protection
lifetime
```

---

# 32. Executable Memory

Executable memory phải explicit unsafe/system operation.

Không cho safe code tùy tiện:

```text
write machine code
execute buffer
```

---

# 33. Dynamic Loading

System library:

```text
load_library(...)
load_symbol(...)
```

với explicit FFI ABI.

Ví dụ:

```text
LibraryHandle
Symbol<T>
```

---

# 34. Symbol Type Safety

Không được coi:

```text
raw address
```

tự động là:

```text
fn(...)
```

Conversion phải qua unsafe/FFI contract.

---

# 35. Static Linking

Axiom compiler/linker phải hỗ trợ:

```text
Axiom object
    ↓
static link
    ↓
native executable
```

không cần dynamic runtime.

---

# 36. Dynamic Linking

Cũng hỗ trợ:

```text
Axiom executable
    ↓
dynamic library
```

ABI contract phải explicit.

---

# 37. Shared Library

Axiom có thể build:

```text
.dll
.so
.dylib
```

hoặc target equivalent.

---

# 38. ABI Stability

Default Axiom ABI không nhất thiết stable giữa compiler versions.

Nếu cần public ABI:

```text
@abi(stable)
```

hoặc explicit C/system ABI.

---

# 39. Struct ABI

Struct truyền qua FFI cần explicit layout.

Ví dụ:

```text
@repr(C)
struct Foo {
    ...
}
```

Compiler không được tự ý AoS→SoA đối với layout observable ở boundary.

---

# 40. Function ABI

Function ABI cần xác định:

```text
parameters
returns
registers
stack
variadic
unwind
ownership
```

---

# 41. Variadic Functions

C variadic:

```text
printf(...)
```

không được trở thành Core variadic mechanism.

FFI boundary có:

```text
extern(C) fn ...
```

với explicit contract.

---

# 42. Signals

Signal/interrupt là asynchronous execution boundary.

Safe API phải tránh giả định signal handler có thể làm mọi việc.

Signal handler có execution restrictions:

```text
nonblocking
async-signal-safe
no allocation
no await
```

tùy platform.

---

# 43. Signal State

Không dùng shared mutable global state không synchronization.

Signal → event/message abstraction tốt hơn khi có thể.

---

# 44. Timer

OS timer có thể lower thành:

```text
Future
Event
Signal
TimerFD
IOCP completion
```

tùy backend.

---

# 45. Time

Phải phân biệt:

```text
MonotonicTime
WallClockTime
ProcessTime
ThreadTime
CPUTime
```

Không được dùng wall clock cho duration measurement.

---

# 46. Sleep

```text
sleep(duration)
```

là blocking effect.

Async:

```text
await sleep(duration)
```

không nên block worker.

---

# 47. CPU Information

System API có thể expose:

```text
cpu_count
cache_info
page_size
features
frequency
```

nhưng compiler target information nên được biết ở compile-time khi có thể.

---

# 48. CPU Feature

Compiler có thể compile:

```text
@target_feature(avx2)
fn ...
```

kết hợp với SIMD engine 366.

---

# 49. NUMA

System API có thể expose:

```text
NumaNode
CpuSet
MemoryNode
Affinity
```

nhưng NUMA không thay đổi Axiom memory semantics.

---

# 50. Thread Affinity

396 dùng lại semantics 364:

```text
ThreadAffinity
TaskAffinity
CpuAffinity
```

phải phân biệt.

---

# 51. Process Affinity

Process có thể có CPU/memory placement policy.

Đây là system optimization, không phải ownership.

---

# 52. Priority

Process/thread priority là scheduling hint.

Compiler không được biến nó thành correctness assumption trừ khi explicit realtime contract.

---

# 53. Realtime

Realtime profile có thể yêu cầu:

```text
no allocation
no blocking
bounded execution
bounded memory
```

Compiler có thể verify một phần.

---

# 54. Kernel Interaction

Axiom không giới hạn ở application.

Có thể xây:

```text
kernel
driver
hypervisor component
bootloader
firmware
```

với freestanding profile.

---

# 55. Interrupt Context

Interrupt function:

```text
@interrupt
fn handler(...)
```

có execution contract.

Không được:

```text
await
blocking
ordinary heap allocation
```

nếu target contract cấm.

---

# 56. MMIO

Memory-mapped I/O:

```text
volatile load/store
```

kết hợp với 363.

MMIO không phải ordinary memory.

---

# 57. Device Register

Có thể khai báo:

```text
@mmio
struct DeviceRegisters {
    status: volatile u32
    control: volatile u32
}
```

representation target-specific.

---

# 58. DMA

DMA buffer đã được định nghĩa ở 390.

396 thêm OS/device mapping:

```text
CPU ownership
DMA ownership
```

phải có explicit transition.

---

# 59. DMA Ownership

Ví dụ:

```text
CPU
 ↓ submit
DEVICE owns buffer
 ↓ completion
CPU owns buffer
```

Compiler/library không cho CPU mutate buffer trong thời gian device ownership nếu safe contract.

---

# 60. Shared Memory

Processes có thể share memory.

Nhưng:

```text
shared memory
```

không tự động đồng nghĩa:

```text
shared mutable safe
```

phải dùng synchronization semantics 362–363.

---

# 61. IPC

System layer:

```text
Pipe
UnixSocket
NamedPipe
SharedMemory
MessageQueue
Signal
```

có thể xây trên I/O + distributed/message semantics.

---

# 62. Pipe

Pipe là typed/byte stream tùy API.

Ownership truyền qua process boundary.

---

# 63. Process Spawn + Capability

Process con có thể nhận:

```text
stdin capability
stdout capability
file capability
socket capability
```

thay vì ambient authority.

Điều này kết nối trực tiếp với 394.

---

# 64. Capability Inheritance

Mặc định:

```text
child != parent authority
```

Chỉ capability được explicit transfer/inherit mới xuất hiện ở child.

---

# 65. Sandbox Process

Có thể spawn:

```text
sandboxed process
```

với:

```text
filesystem capability
network capability
CPU budget
memory budget
device capability
```

---

# 66. Resource Limits

System layer có:

```text
MemoryLimit
CpuLimit
FileLimit
ThreadLimit
ProcessLimit
IoLimit
```

gắn với Security/ResourceBudget 394.

---

# 67. OOM

Không được giả định mọi allocation failure đều có thể recover.

Profile phải định nghĩa:

```text
Result
panic
abort
OS termination
```

---

# 68. Stack

Stack là storage strategy.

System API có thể yêu cầu:

```text
stack_size
guard_size
```

khi spawn thread.

Compiler vẫn có thể optimize local values.

---

# 69. TLS

TLS semantic model từ 364.

System layer map:

```text
Axiom ThreadLocal
 ↓
OS TLS
```

hoặc compiler-managed TLS.

---

# 70. Environment Initialization

Compiler có thể loại bỏ initialization không cần thiết.

Ví dụ program chỉ:

```text
write syscall
exit
```

thì không cần initialize:

```text
filesystem runtime
network runtime
async executor
database runtime
```

---

# 71. Runtime Feature Linking

Executable dependency graph:

```text
Program
 ├── allocator
 ├── threads
 ├── async
 ├── crypto
 └── database
```

chỉ link phần được sử dụng.

---

# 72. Dead Runtime Elimination

Nếu:

```text
async
```

không dùng → không link executor.

Nếu:

```text
heap
```

không dùng → không link allocator.

Nếu:

```text
panic
```

không dùng → có thể dùng minimal trap/abort.

---

# 73. System Calls + Effects

Compiler EffectDB bổ sung:

```text
OS_SYSCALL
PROCESS
THREAD
SIGNAL
TIME
ENVIRONMENT
VIRTUAL_MEMORY
DYNAMIC_LOAD
MMIO
DEVICE
```

---

# 74. Pure System Boundary

Một số system queries có thể được đánh dấu:

```text
READONLY_SYSTEM
```

nhưng không được coi pure nếu kết quả phụ thuộc môi trường observable.

---

# 75. Compile-Time OS Information

`comptime` có thể biết:

```text
target_os
target_arch
target_abi
target_endian
target_pointer_width
target_features
```

nhưng không được giả định runtime machine giống build machine trừ khi target contract đảm bảo.

---

# 76. Cross Compilation

Architecture:

```text
Source
 ↓
Target config
 ↓
Axiom compiler
 ↓
Target ABI
 ↓
Target object
```

không cần chạy compiler trên target.

---

# 77. Multi-Target Build

Một source có thể compile:

```text
Windows
Linux
macOS
Android
WASM
```

thông qua `@cfg`.

---

# 78. OS Abstraction không nên thành “giả OS”

API:

```text
read_file()
```

không nên che mọi khác biệt quan trọng.

Nếu semantics khác nhau:

```text
WindowsFile
UnixFile
```

hoặc capability/feature contract phải biểu diễn được.

---

# 79. Native Escape Hatch

System programmer phải có:

```text
extern
unsafe
raw pointer
asm
syscall
volatile
repr
link
```

nhưng tất cả đều là explicit boundary.

---

# 80. Inline Assembly

Axiom cần:

```text
asm(...)
```

ở system/unsafe layer.

Compiler phải biết:

```text
inputs
outputs
clobbers
memory effects
flags
control-flow effects
```

Không cho inline asm tùy tiện phá optimizer assumptions.

---

# 81. Assembly Contract

Ví dụ semantic metadata:

```text
AsmContract {
    inputs
    outputs
    clobbers
    memory
    preserves_flags
    may_unwind
    noreturn
}
```

---

# 82. Naked Functions

Có thể hỗ trợ:

```text
@naked
```

nhưng chỉ system/unsafe.

Compiler không tự chèn:

```text
prologue
epilogue
stack frame
```

nếu naked contract yêu cầu.

---

# 83. Linker Control

System programmer cần:

```text
@section
@link_name
@export
@import
@weak
@visibility
@align
```

ở ABI/system layer.

---

# 84. Linker Script

Freestanding targets có thể cần:

```text
linker script
memory layout
sections
symbols
```

Axiom build system phải truyền được các contract này tới linker.

Mục tiêu cuối cùng vẫn là Axiom có linker riêng, nhưng bootstrap có thể dùng target linker.

---

# 85. Object Format

396 kết nối trực tiếp với compiler backend:

```text
Machine Code
 ↓
Object Writer
 ↓
ELF / PE / Mach-O / WASM
```

---

# 86. Relocations

Object writer phải hiểu:

```text
symbol
relocation
section
visibility
TLS relocation
PLT/GOT
import/export
```

---

# 87. Symbol Model

Compiler cần phân biệt:

```text
Source Symbol
IR Symbol
Object Symbol
Linker Symbol
Runtime Address
```

Không được trộn chúng.

---

# 88. System Resource Lifecycle

Mọi OS resource phải dùng cùng ownership model:

```text
FileHandle
SocketHandle
ProcessHandle
LibraryHandle
MemoryMapping
DeviceHandle
```

đều có thể là:

```text
Move
Drop
Explicit close
```

---

# 89. Drop của OS Handle

`Drop` có thể gọi close/release.

Nhưng nếu cleanup có thể fail:

```text
close() -> Result
```

phải là explicit.

`Drop` không propagate recoverable error.

---

# 90. Handle Duplication

Duplicate handle không phải Copy.

Phải có:

```text
duplicate()
```

vì nó tạo thêm resource authority/reference.

---

# 91. Handle Transfer

Process/thread transfer có thể:

```text
move handle
duplicate handle
delegate capability
```

và compiler kiểm tra ownership.

---

# 92. System Resource + Async

Nếu handle đang được async operation sử dụng:

```text
close(handle)
```

không được xảy ra khi operation vẫn cần handle.

Compiler/resource state machine phải chứng minh lifetime.

---

# 93. Cancellation

OS operation cancellation phải phân biệt:

```text
request cancellation
operation completed
operation cancelled
result unknown
```

Đặc biệt với I/O.

Không được giả định cancellation rollback external side effect.

---

# 94. Restartability

System call wrapper có thể khai báo:

```text
idempotent
retry_safe
cancel_safe
```

để compiler/runtime hỗ trợ retry.

---

# 95. Security Boundary

OS API phải preserve:

```text
Capability
TrustDomain
Taint
Secret
Authorization
```

từ 394.

Ví dụ:

```text
open(path)
```

với untrusted `path` không được tự động coi là trusted filesystem capability.

---

# 96. File Path

Path là data.

Canonicalization/validation phải explicit khi crossing security boundary.

Không để:

```text
string == trusted path
```

một cách tự động.

---

# 97. Native Application Stack

Sau 396, một ứng dụng native điển hình có thể là:

```text
Axiom Core
   ↓
System API
   ↓
I/O
   ↓
Thread/Async
   ↓
GUI / Graphics / Audio / Network
```

và không cần:

```text
GC
VM
mandatory runtime
libc
```

---

# 98. CompilerDB

Bổ sung:

```text
SystemDB
SystemTargetDB
SystemProfileDB
SystemAbiDB
SystemCallDB
SystemCallAbiDB
SystemEffectDB
SystemCapabilityDB

OsDB
OsTargetDB
OsVersionDB
OsFeatureDB
OsResourceDB

ProcessDB
ProcessTypeDB
ProcessIdDB
ProcessHandleDB
ProcessSpawnDB
ProcessJoinDB
ProcessWaitDB
ProcessExitDB
ProcessKillDB
ProcessEnvironmentDB
ProcessArgumentDB
ProcessDirectoryDB
ProcessAffinityDB
ProcessPriorityDB
ProcessResourceLimitDB

SyscallDB
SyscallNumberDB
SyscallArgumentDB
SyscallConventionDB
SyscallReturnDB
SyscallErrorDB

SystemMemoryDB
VirtualMemoryDB
MemoryMappingDB
MemoryProtectionDB
MemoryReserveDB
MemoryCommitDB
MemoryDecommitDB
MemoryGuardDB

DynamicLoaderDB
LibraryHandleDB
SymbolLookupDB
DynamicLinkDB
StaticLinkDB
LinkSymbolDB
LinkVisibilityDB
RelocationDB

SignalDB
SignalHandlerDB
SignalSafetyDB
SignalMaskDB

TimerDB
ClockDB
MonotonicClockDB
WallClockDB
SleepDB

SystemAffinityDB
CpuSetDB
NumaSystemDB
SystemCpuDB
SystemFeatureDB

InterruptDB
InterruptHandlerDB
MmioDB
DmaSystemDB
DeviceMappingDB

IpcDB
PipeDB
SharedMemoryDB
MessageQueueDB
UnixSocketDB
NamedPipeDB

SandboxProcessDB
ProcessCapabilityDB
CapabilityInheritanceDB
ResourceLimitDB

AsmDB
AsmContractDB
AsmInputDB
AsmOutputDB
AsmClobberDB
NakedFunctionDB

EntryPointDB
StartupDB
ExitDB
TlsStartupDB

ObjectFormatDB
ElfDB
PeDB
MachODb
WasmObjectDB
SectionDB
RelocationDB
SymbolDB
LinkerDB
LinkerScriptDB

CrossCompileDB
TargetConfigDB
TargetAbiDB
TargetFeatureDB

SystemResourceDB
SystemHandleDB
SystemHandleOwnershipDB
SystemHandleDuplicationDB
SystemHandleTransferDB
SystemResourceLifetimeDB

SystemProofDB
SyscallProofDB
ProcessProofDB
MemoryMappingProofDB
CapabilityInheritanceProofDB
SignalSafetyProofDB
DmaOwnershipProofDB
AbiProofDB
AsmProofDB
LinkProofDB
SystemVerificationDB
```

---

# 99. MIR

Các system operations cần được biểu diễn rõ trong MIR:

```text
SYSCALL
SYSCALL_RESULT
SYSCALL_ERROR

PROCESS_SPAWN
PROCESS_WAIT
PROCESS_JOIN
PROCESS_EXIT
PROCESS_KILL

PROCESS_ENV_GET
PROCESS_ENV_SET
PROCESS_CWD_GET
PROCESS_CWD_SET

VIRTUAL_MEMORY_RESERVE
VIRTUAL_MEMORY_COMMIT
VIRTUAL_MEMORY_DECOMMIT
VIRTUAL_MEMORY_PROTECT
MEMORY_MAP
MEMORY_UNMAP

HANDLE_DUPLICATE
HANDLE_TRANSFER
HANDLE_CLOSE

DYNAMIC_LOAD
SYMBOL_LOOKUP

SIGNAL_REGISTER
SIGNAL_BLOCK
SIGNAL_UNBLOCK
SIGNAL_WAIT

TIMER_CREATE
TIMER_WAIT
CLOCK_READ
SLEEP

CPU_QUERY
CPU_AFFINITY_SET
THREAD_AFFINITY_SET

SHARED_MEMORY_CREATE
SHARED_MEMORY_MAP
SHARED_MEMORY_UNMAP

PIPE_CREATE
IPC_SEND
IPC_RECEIVE

DMA_MAP
DMA_UNMAP
DMA_ACQUIRE
DMA_RELEASE

MMIO_LOAD
MMIO_STORE

ASM_BEGIN
ASM_END

SECTION_DECLARE
SYMBOL_EXPORT
SYMBOL_IMPORT
LINK_DIRECTIVE
```

---

# 100. Proof System

```text
SyscallEffectProof
SyscallAbiProof
SyscallErrorProof

ProcessOwnershipProof
ProcessCapabilityProof
ProcessInheritanceProof
ProcessLifetimeProof

MemoryMappingProof
MemoryProtectionProof
VirtualMemoryProof

HandleOwnershipProof
HandleDuplicationProof
HandleTransferProof
HandleLifetimeProof

DynamicSymbolProof
DynamicAbiProof
LinkageProof
RelocationProof

SignalSafetyProof
SignalExecutionProof

TimerProof
ClockSemanticsProof

DmaOwnershipProof
DmaLifetimeProof
MmioSafetyProof

IpcOwnershipProof
SharedMemoryProof
IpcSynchronizationProof

SandboxCapabilityProof
ResourceLimitProof

AsmContractProof
AsmClobberProof
AsmMemoryProof
AsmControlFlowProof

EntryPointProof
TlsStartupProof
ExitProof

CrossCompileProof
TargetAbiProof
ObjectFormatProof

SystemEffectProof
SystemCapabilityProof
SystemResourceProof
SystemVerificationProof
```

---

# 101. Invariants

### `ASYS-01`
Core language semantics không phụ thuộc vào một OS cụ thể.

### `ASYS-02`
Hosted và freestanding phải có semantic model thống nhất.

### `ASYS-03`
Không có OS/runtime dependency nào được link nếu không được yêu cầu.

### `ASYS-04`
System resource phải có ownership rõ ràng.

### `ASYS-05`
Handle không mặc định là `Copy`.

### `ASYS-06`
Duplicate handle phải là explicit operation.

### `ASYS-07`
Handle lifetime phải được kiểm soát trước khi resource được sử dụng.

### `ASYS-08`
Syscall phải được xem là effect, không phải pure computation.

### `ASYS-09`
OS error không được phụ thuộc semantic vào global mutable `errno`.

### `ASYS-10`
Blocking operation phải được compiler nhận diện.

### `ASYS-11`
Async API không được ngầm tạo thread nếu semantics không yêu cầu.

### `ASYS-12`
Process identity không được đồng nhất với raw PID.

### `ASYS-13`
Process capability inheritance phải explicit.

### `ASYS-14`
Child process không tự động nhận ambient authority ngoài contract.

### `ASYS-15`
Virtual memory mapping phải có explicit lifetime và protection contract.

### `ASYS-16`
Executable memory phải là explicit unsafe/system capability.

### `ASYS-17`
Dynamic symbol address không tự động trở thành typed function.

### `ASYS-18`
FFI ABI phải explicit.

### `ASYS-19`
Observable ABI layout không được bị Data Layout optimizer thay đổi.

### `ASYS-20`
Signal handler phải tuân thủ execution-safety contract.

### `ASYS-21`
MMIO phải sử dụng volatile/device-memory semantics, không phải ordinary memory semantics.

### `ASYS-22`
DMA ownership phải xác định rõ CPU/device ownership transition.

### `ASYS-23`
Shared memory không tự động đảm bảo data-race freedom.

### `ASYS-24`
Inline assembly phải khai báo inputs, outputs, clobbers và memory effects.

### `ASYS-25`
Compiler không được tối ưu qua những effects mà assembly contract chưa khai báo.

### `ASYS-26`
Freestanding code không được ngầm yêu cầu GC, allocator hoặc OS runtime.

### `ASYS-27`
Cross-compilation phải dựa trên target semantics, không dựa trên host environment.

### `ASYS-28`
System API optimization không được thay đổi observable OS semantics.

### `ASYS-29`
Resource cleanup phải tuân thủ ownership/Drop model của Axiom.

### `ASYS-30`
Axiom phải có khả năng biểu diễn trực tiếp machine/OS operations cần thiết để xây dựng hệ thống mà không bắt buộc phải thông qua C ABI.

---

## Ý nghĩa của 396 đối với mục tiêu ban đầu

Sau bước này, kiến trúc Axiom có một đặc điểm rất quan trọng:

```text
                 Axiom
                   │
       ┌───────────┴───────────┐
       │                       │
   High Level              System Level
       │                       │
 ML / DB / Graph          Syscall / MMIO
 Vision / Physics         Process / ABI
 Scientific               DMA / Assembly
       │                       │
       └───────────┬───────────┘
                   │
                MIR/LIR
                   │
             Native Machine
```

Tức là Axiom không bị mắc kẹt ở vị trí **“ngôn ngữ application high-level”**.

Nó vẫn có thể đi xuống tận:

```text
Axiom
→ syscall
→ MMIO
→ interrupt
→ DMA
→ assembly
→ object file
→ executable
```

trong khi phía trên cùng một ngôn ngữ có thể đi tới:

```text
Axiom
→ Tensor
→ ML
→ Database
→ Distributed System
→ GPU
```

Đây là một trong những điểm tạo nên khác biệt kiến trúc quan trọng nhất của Axiom.