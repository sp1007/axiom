# BOOTSTRAP-750 — AXABI

**Namespace:** `AXABI`  
**Phase:** Axiom Civilization Runtime / Native Application Binary Interface & Cross-Module ABI Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXMEMORY`, `AXPROCESS`, `AXTASK`, `AXASYNC`, `AXSYNC`, `AXCOMPUTE`, `AXSTORAGE`, `AXSECURITY`, compiler IR/object/emission layers, platform object-format backends.

---

# 750.1 — Purpose

`AXABI` định nghĩa **binary contract** giữa:

```text
Axiom source
      ↓
Axiom compiler
      ↓
Axiom IR
      ↓
machine code
      ↓
object file
      ↓
static library / dynamic library
      ↓
executable / application
      ↓
other module / OS / foreign language
```

ABI phải trả lời chính xác:

- argument truyền ở đâu;
- return value nằm ở đâu;
- struct truyền thế nào;
- struct trả về thế nào;
- register nào caller/callee save;
- stack frame ra sao;
- alignment thế nào;
- symbol được đặt tên thế nào;
- function pointer có representation gì;
- closure ABI ra sao;
- generic ABI ra sao;
- error ABI;
- async ABI;
- allocator ABI;
- module compatibility;
- dynamic linking;
- FFI;
- binary versioning.

**ABI là contract machine-level, không phải language-level syntax.**

---

# 750.2 — Core Principle

Axiom phải có một **canonical internal ABI**.

Không để từng compiler backend tự phát minh ABI riêng.

```text
Axiom ABI
   │
   ├── x86_64
   ├── ARM64
   ├── WASM
   └── future architectures
```

Architecture-specific ABI chỉ thay đổi:

```text
register set
calling convention
stack alignment
object relocation
platform linkage
```

Semantic ABI vẫn thống nhất.

---

# 750.3 — ABI Layers

AXABI chia thành:

```text
AXABI
 ├── Language ABI
 ├── Type Layout ABI
 ├── Calling ABI
 ├── Runtime ABI
 ├── Module ABI
 ├── Object ABI
 ├── FFI ABI
 ├── Async ABI
 ├── Allocation ABI
 ├── Exception/Error ABI
 └── Platform ABI
```

---

# 750.4 — ABI vs API

API:

```text
function read_file(...)
```

ABI:

```text
argument registers
stack slots
return registers
symbol
alignment
calling convention
```

API có thể thay đổi implementation.

ABI thay đổi có thể làm binary không tương thích.

---

# 750.5 — ABI Stability Classes

Mỗi public binary contract có:

```text
ABI_STABLE
ABI_VERSIONED
ABI_PRIVATE
ABI_EXPERIMENTAL
```

---

# 750.6 — ABI-Stable

Stable ABI chỉ sử dụng những layout/semantic guarantees đã frozen.

---

# 750.7 — ABI-Private

Compiler-generated internal symbols được phép thay đổi giữa compiler versions.

---

# 750.8 — ABI Version

Canonical:

```axiom
abi_version {
    major
    minor
    revision
}
```

---

# 750.9 — Compatibility Rule

```text
major mismatch
→ incompatible

minor increase
→ compatible only according to declared compatibility contract

revision
→ bugfix-compatible
```

---

# 750.10 — ABI Fingerprint

Mỗi module có:

```axiom
abi_fingerprint
```

được tính từ:

```text
target architecture
calling convention
type layout
public symbols
public ABI types
runtime ABI version
compiler ABI features
```

---

# 750.11 — ABI Fingerprint Purpose

Linker có thể reject:

```text
module A ABI ≠ module B ABI
```

trước khi tạo binary lỗi.

---

# 750.12 — Calling Convention

Axiom canonical calling convention:

```text
AXCALL
```

được compiler map sang architecture-specific convention.

---

# 750.13 — AXCALL Contract

AXCALL định nghĩa:

```text
argument classification
return classification
register volatility
stack ownership
stack alignment
aggregate passing
aggregate return
variadic behavior
```

---

# 750.14 — Register Classes

ABI phân loại:

```text
INTEGER
FLOAT
VECTOR
SPECIAL
RETURN
TEMPORARY
CALLEE_SAVED
```

---

# 750.15 — x86-64

PE64 và các Unix-like targets có backend-specific register mapping.

Axiom không hard-code source-level semantics vào Windows/Linux calling convention.

---

# 750.16 — ARM64

ARM64 sử dụng register classes tương ứng với architecture.

ABI abstraction phải giữ nguyên semantic argument classification.

---

# 750.17 — Stack Alignment

Mỗi architecture/backend khai báo:

```axiom
stack_alignment
```

Compiler phải đảm bảo trước mọi ABI-visible call.

---

# 750.18 — Stack Ownership

Caller và callee có trách nhiệm rõ ràng:

```text
caller
→ creates call arguments

callee
→ owns its local frame

caller
→ reclaims caller-owned argument area
```

theo platform ABI.

---

# 750.19 — Shadow Space

Nếu platform ABI yêu cầu shadow/home space, backend tự tạo.

Core AXABI không bắt buộc shadow space.

---

# 750.20 — Red Zone

Red-zone support là architecture/platform capability.

Compiler không được assume red zone universally.

---

# 750.21 — Register Volatility

ABI metadata khai báo:

```text
caller_saved
callee_saved
reserved
argument
return
```

---

# 750.22 — Function Prologue

Compiler có thể omit frame pointer nếu:

```text
debugging
unwinding
ABI
```

không yêu cầu.

---

# 750.23 — Frame Pointer

Frame pointer là optimization/debug choice, không phải language semantic.

---

# 750.24 — Tail Call

AXABI phải hỗ trợ tail-call-compatible calls khi:

```text
argument ABI
return ABI
stack contract
```

cho phép.

---

# 750.25 — Tail Call Optimization

Compiler có thể transform:

```axiom
return f(x)
```

thành direct tail jump.

---

# 750.26 — Function Return

Scalar return classification:

```text
INTEGER
FLOAT
VECTOR
AGGREGATE
VOID
```

---

# 750.27 — Multi-Register Return

Small aggregates có thể return bằng nhiều registers nếu architecture ABI cho phép.

---

# 750.28 — Large Aggregate Return

Large struct có thể dùng hidden return pointer:

```text
caller allocates result
        ↓
callee writes result
```

---

# 750.29 — Hidden Arguments

ABI có thể thêm hidden arguments:

```text
return pointer
closure context
generic metadata
async frame
runtime context
```

nhưng phải có deterministic ordering.

---

# 750.30 — Hidden Argument Ordering

Canonical ordering phải được frozen.

Ví dụ:

```text
explicit arguments
→ hidden ABI context
```

hoặc backend-specific equivalent.

Compiler IR phải biểu diễn hidden ABI parameters explicitly trước code generation.

---

# 750.31 — Struct Layout

Axiom struct ABI gồm:

```text
field order
offset
size
alignment
padding
packing
```

---

# 750.32 — Default Struct Layout

Default:

```text
source field order preserved
natural alignment
minimal required padding
```

---

# 750.33 — Explicit Layout

Axiom hỗ trợ:

```axiom
@layout(...)
struct Packet {
    ...
}
```

cho binary protocol/FFI/device ABI.

---

# 750.34 — Packed Layout

Packed layout được phép nhưng compiler phải cảnh báo/correctly lower unaligned accesses.

---

# 750.35 — Explicit Alignment

```axiom
@align(64)
struct CacheLine {
    ...
}
```

---

# 750.36 — Struct ABI Stability

Public ABI struct không được tự động thay đổi layout chỉ vì compiler optimization.

---

# 750.37 — Private Struct

Private/internal structs có thể được freely optimized.

---

# 750.38 — Opaque Struct

ABI có thể expose:

```axiom
opaque FileHandle
```

mà không expose layout.

Đây là cơ chế quan trọng để giữ ABI stability.

---

# 750.39 — ABI Handle

Opaque handle representation:

```text
integer/generation-safe token
```

hoặc pointer theo backend contract.

Source không được phụ thuộc representation.

---

# 750.40 — Enum ABI

Enum có:

```text
discriminant type
value mapping
layout
size
alignment
```

---

# 750.41 — Enum Representation

Compiler phải freeze representation nếu enum là ABI-visible.

---

# 750.42 — Option ABI

`option<T>` có canonical ABI representation tùy `T`.

Ví dụ nullable pointer optimization chỉ được sử dụng nếu representation contract cho phép.

---

# 750.43 — Result ABI

```axiom
result<T, E>
```

được ABI-lower thành explicit tagged representation.

---

# 750.44 — Boolean ABI

`bool` có canonical representation.

Không phụ thuộc C `bool` hoặc platform ABI trừ FFI boundary.

---

# 750.45 — Integer ABI

Các loại:

```text
i8  i16  i32  i64
u8  u16  u32  u64
i128 u128
```

có size/sign semantics cố định.

---

# 750.46 — Pointer ABI

Pointer representation là architecture-defined.

Axiom:

```text
raw pointer
```

chỉ có ý nghĩa trong memory/address-space contract của target.

---

# 750.47 — Pointer Width

Compiler query:

```axiom
target.pointer_bits
```

---

# 750.48 — Slice ABI

Slice không phải raw pointer đơn.

Canonical conceptual layout:

```text
slice<T> {
    pointer
    length
}
```

Nhưng exact register/stack classification phụ thuộc target ABI.

---

# 750.49 — Span ABI

`span<T>` có thể dùng cùng physical representation với slice nhưng semantic contract có thể khác.

---

# 750.50 — String ABI

Axiom UTF-8 string ABI:

```text
pointer
byte_length
```

không mặc định NUL-terminated.

---

# 750.51 — C String ABI

FFI adapter riêng:

```text
cstring
```

với NUL termination.

---

# 750.52 — UTF-8 Guarantee

Axiom `string` luôn biểu diễn UTF-8 unless explicitly declared binary/raw bytes.

---

# 750.53 — Byte Buffer ABI

```axiom
buffer<u8>
```

không có implicit text semantics.

---

# 750.54 — SIMD ABI

Vector types được phân loại:

```text
VECTOR
```

và truyền/return theo target register ABI.

---

# 750.55 — Vector Width

Compiler hỗ trợ:

```text
128
256
512
```

hoặc architecture-supported widths.

---

# 750.56 — Generic ABI

Generic function có hai khả năng:

```text
MONOMORPHIC
ERASED
```

---

# 750.57 — Monomorphization

Compiler tạo specialization:

```text
foo<i32>
foo<f64>
foo<MyStruct>
```

mỗi specialization có machine-level ABI cụ thể.

---

# 750.58 — Generic Metadata

Nếu erased/generic runtime representation cần metadata:

```text
type_info
layout_info
operation_table
```

được truyền qua hidden ABI parameter.

---

# 750.59 — Generic ABI Stability

Compiler-generated generic symbols mặc định `ABI_PRIVATE`.

Public stable generic ABI phải explicit annotation.

---

# 750.60 — Trait ABI

Axiom trait/interface không yêu cầu C++-style class vtable.

---

# 750.61 — Static Trait Dispatch

Compiler ưu tiên:

```text
compile-time specialization
```

khi concrete type biết trước.

---

# 750.62 — Dynamic Trait Dispatch

Nếu dynamic dispatch cần thiết:

```axiom
trait_object {
    data
    dispatch_table
}
```

---

# 750.63 — Dispatch Table

Dispatch table có:

```text
method pointers
type metadata
ABI version
```

---

# 750.64 — Struct Method ABI

Theo kiến trúc Axiom:

```axiom
player.update(dt)
```

lower thành conceptually:

```text
Player_update(&player, dt)
```

---

# 750.65 — No Class ABI

AXABI không cần class-layout ABI.

Đây là một điểm làm binary model đơn giản hơn.

---

# 750.66 — Override ABI

Override chỉ là dispatch contract.

Static dispatch:

```text
direct call
```

Dynamic dispatch:

```text
dispatch table lookup
```

---

# 750.67 — Function Pointer ABI

Function pointer chứa:

```text
code address
```

trong simple function case.

---

# 750.68 — Closure ABI

Closure:

```axiom
closure {
    code
    context
}
```

không được giả định là một function pointer đơn.

---

# 750.69 — Closure Call

Conceptually:

```text
closure.code(context, arguments...)
```

---

# 750.70 — Non-Capturing Closure

Có thể ABI-compatible với function pointer nếu compiler chứng minh không capture state và contract cho phép.

---

# 750.71 — Capturing Closure

Capturing closure phải có explicit environment.

---

# 750.72 — Closure Lifetime

Environment lifetime do language/runtime ownership model quản lý, không phải ABI tự động GC.

---

# 750.73 — Variadic ABI

Axiom native variadic:

```axiom
fn printf(format: cstring, ...)
```

chỉ được dùng tại FFI/system boundary.

---

# 750.74 — Typed Variadic

Axiom nên ưu tiên:

```axiom
format(args...)
```

hoặc tuple/array-based APIs thay vì raw variadic ABI.

---

# 750.75 — Variadic Register Save

Architecture backend chịu trách nhiệm register-save area nếu ABI yêu cầu.

---

# 750.76 — Error ABI

Axiom không bắt buộc exceptions cho native error transport.

Primary ABI:

```text
Result<T,E>
```

hoặc status + out parameters.

---

# 750.77 — Error Return

Small error/status có thể return register.

Large result dùng hidden result structure.

---

# 750.78 — Panic/Trap ABI

Fatal runtime conditions có dedicated runtime entry:

```axiom
__ax_panic
__ax_abort
__ax_trap
```

---

# 750.79 — Unwinding

Unwinding không phải bắt buộc language mechanism.

Backend có thể support:

```text
NO_UNWIND
TABLE_UNWIND
PLATFORM_UNWIND
```

---

# 750.80 — Exception Boundary

Foreign exceptions không được tự động xuyên qua Axiom ABI boundary.

Phải adapter rõ ràng.

---

# 750.81 — Unwind Metadata

Native object có thể chứa:

```text
unwind info
debug unwind info
exception tables
```

theo target.

---

# 750.82 — Async ABI

AXASYNC + AXTASK cần ABI riêng.

Async function không đơn giản là synchronous function có callback.

---

# 750.83 — Async Function Lowering

```axiom
async fn read_data() -> Result<Data, Error>
```

lower thành conceptual state machine:

```text
create frame
 ↓
submit operation
 ↓
suspend
 ↓
resume
 ↓
continue
 ↓
complete
```

---

# 750.84 — Task Frame ABI

AXTASK đã định nghĩa:

```text
AXTASK_FRAME_ABI_1
```

AXABI phải expose binary contract cho frame khi frame crosses module boundaries.

---

# 750.85 — Async Frame Ownership

Frame ownership phải explicit:

```text
creator
→ executor/runtime
→ completion
→ destroy
```

---

# 750.86 — Async Frame Layout

Frame metadata:

```text
state
resume function
destroy function
result storage
live locals
cancellation state
```

---

# 750.87 — Resume Function

Canonical conceptual ABI:

```text
resume(frame)
```

---

# 750.88 — Destroy Function

```text
destroy(frame)
```

được gọi đúng một lần sau frame lifetime kết thúc.

---

# 750.89 — Async Cancellation ABI

Cancellation được biểu diễn bằng token/state, không phải arbitrary stack unwinding.

---

# 750.90 — Future ABI

`future<T>` public ABI phải define:

```text
state
result
wait/await mechanism
ownership
```

hoặc expose opaque representation.

---

# 750.91 — Preferred Future ABI

Public binary interface nên dùng opaque future handle thay vì expose compiler-private frame layout.

---

# 750.92 — Allocator ABI

Một module không được:

```text
allocate with allocator A
free with incompatible allocator B
```

---

# 750.93 — Canonical Allocator Boundary

AXABI định nghĩa:

```axiom
ax_alloc
ax_realloc
ax_free
```

ABI contract.

---

# 750.94 — Allocator Ownership

Memory returned by module phải document:

```text
caller-owned
callee-owned
shared
transfer
```

---

# 750.95 — Transfer ABI

Function có thể explicitly transfer ownership:

```axiom
@transfer
fn create_buffer() -> buffer
```

---

# 750.96 — Borrow ABI

Temporary borrowed view có thể cross call:

```text
slice
span
```

nhưng lifetime contract phải được compiler/runtime validate.

---

# 750.97 — ABI Does Not Impose Borrow Checker

AXABI chỉ biểu diễn lifetime contract.

Không biến Axiom thành borrow-checker language.

---

# 750.98 — Shared Memory ABI

Cross-module shared memory dùng:

```text
region handle
offset
length
```

thay vì process-specific raw pointer.

---

# 750.99 — IPC ABI

IPC message ABI phải dùng AXIPC schema/type contract.

AXABI không duplicate message transport.

---

# 750.100 — Binary Serialization

ABI layout không mặc định đồng nghĩa wire serialization.

```text
ABI layout ≠ network format
```

---

# 750.101 — Packed Wire Types

Protocol structs phải explicit:

```axiom
@wire
struct Header { ... }
```

để compiler không nhầm với native ABI layout.

---

# 750.102 — Endianness

Native ABI sử dụng target native endianness.

Wire ABI phải explicit endian.

---

# 750.103 — Bitfields

Bitfield layout chỉ ABI-stable khi explicit declaration.

---

# 750.104 — Atomic ABI

Atomic types có:

```text
size
alignment
memory order semantics
```

được target backend map xuống hardware.

---

# 750.105 — Atomic Lock-Free Property

Không được assume mọi atomic width đều lock-free.

Compiler query:

```axiom
atomic.is_lock_free<T>()
```

---

# 750.106 — SIMD Alignment

Vector ABI phải specify alignment requirements.

---

# 750.107 — Device ABI

MMIO/device structs có explicit layout và volatile semantics.

---

# 750.108 — FFI

Axiom FFI phải hỗ trợ tối thiểu:

```text
C
C-compatible structs
function pointers
opaque handles
native libraries
```

---

# 750.109 — C ABI

Canonical:

```axiom
extern "c" fn ...
```

---

# 750.110 — C Struct

```axiom
extern "c" struct sockaddr {
    ...
}
```

Compiler dùng target C ABI layout.

---

# 750.111 — C Name Mangling

`extern "c"` không Axiom-mangle symbol.

---

# 750.112 — Axiom Name Mangling

Internal symbol:

```text
_AX_<module>_<namespace>_<function>_<signature_hash>
```

conceptually.

Exact encoding phải deterministic.

---

# 750.113 — Mangling Requirements

Mangling phải:

```text
collision-free
deterministic
architecture-aware where required
linker-safe
```

---

# 750.114 — Symbol Visibility

```text
PUBLIC
HIDDEN
PRIVATE
WEAK
IMPORT
EXPORT
```

---

# 750.115 — Public Symbol

Chỉ explicit exported declaration trở thành ABI public.

---

# 750.116 — Dead Symbol Elimination

Internal symbols có thể bị loại khỏi binary.

---

# 750.117 — Symbol Versioning

Dynamic libraries có thể support:

```text
symbol@ABI_1
symbol@ABI_2
```

nếu platform linker hỗ trợ.

---

# 750.118 — Symbol Alias

ABI compatibility layer có thể map:

```text
old_symbol
→ new implementation
```

---

# 750.119 — Deprecated ABI

Symbol có metadata:

```text
deprecated_since
remove_after
replacement
```

---

# 750.120 — Static Library ABI

Static library chứa:

```text
object modules
symbols
relocations
ABI metadata
dependency metadata
```

---

# 750.121 — Dynamic Library ABI

Dynamic module chứa:

```text
exports
imports
relocations
ABI manifest
runtime requirements
```

---

# 750.122 — Module Manifest

Canonical:

```axiom
abi_manifest {
    abi_version
    target
    architecture
    exports
    imports
    dependencies
    fingerprint
}
```

---

# 750.123 — Module Dependency

Dependency phải ghi:

```text
module name
ABI range
feature requirements
```

---

# 750.124 — Link Compatibility

Linker kiểm tra:

```text
target
architecture
ABI version
calling convention
type layout
symbol
feature requirements
```

---

# 750.125 — ABI Mismatch Diagnostic

Ví dụ:

```text
AXABI-ERR-001
expected: AXABI 5.x
found:    AXABI 4.x
reason:   incompatible struct layout
symbol:   Foo::bar
```

---

# 750.126 — PE64

Windows native artifact:

```text
Axiom
 ↓
COFF objects
 ↓
PE/PE32+
```

AXABI supplies calling/linkage contract.

---

# 750.127 — ELF

Linux/Unix:

```text
Axiom
 ↓
ELF object
 ↓
static/dynamic executable
```

---

# 750.128 — Mach-O

macOS/iOS:

```text
Axiom
 ↓
Mach-O
```

với platform-specific ABI adapter.

---

# 750.129 — Android

Android target sử dụng ARM64 hoặc supported architecture ABI cùng Android platform constraints.

---

# 750.130 — WASM

WASM ABI khác native register ABI.

AXABI map:

```text
function arguments
→ WASM value types
```

---

# 750.131 — WASM Complex Types

Struct/string/slice có thể được lower thành:

```text
pointer + length
```

theo Axiom WASM ABI profile.

---

# 750.132 — Dynamic Linking

Dynamic linker cần:

```text
symbol resolution
relocation
dependency loading
initialization
finalization
```

---

# 750.133 — Initialization

Module initialization phải explicit và deterministic.

Không cho phép hidden arbitrary global initialization làm thay đổi ABI contract.

---

# 750.134 — Finalization

Module unload chỉ được phép khi runtime xác nhận không còn active references/calls.

---

# 750.135 — Plugin ABI

Plugin API phải expose:

```axiom
plugin_descriptor {
    abi_version
    plugin_version
    capabilities
    init
    shutdown
}
```

---

# 750.136 — Plugin Compatibility

Plugin load sequence:

```text
read manifest
 ↓
check target
 ↓
check ABI
 ↓
check dependencies
 ↓
resolve symbols
 ↓
initialize
```

---

# 750.137 — Hot Reload

Hot reload chỉ áp dụng module có explicit reload contract.

---

# 750.138 — Hot Reload Safety

Không unload module nếu:

```text
active function pointers
active callbacks
active async frames
active threads
live objects
```

còn trỏ tới module code/data.

---

# 750.139 — Function Pointer Stability

Hot reload cần indirection table nếu muốn function addresses stable.

---

# 750.140 — ABI Thunk

Compatibility thunk:

```text
old ABI
 ↓
adapter
 ↓
new ABI
```

cho phép migration.

---

# 750.141 — ABI Adapter

Compiler/linker có thể generate thunk cho:

```text
calling convention
struct transformation
symbol rename
error conversion
```

nhưng chỉ khi transformation an toàn và được khai báo.

---

# 750.142 — No Implicit Unsafe ABI Conversion

Nếu layout không tương thích:

```text
link failure
```

không tự đoán.

---

# 750.143 — Debug ABI

Debug build có metadata:

```text
function
type
source location
stack frame
variable location
ABI version
```

---

# 750.144 — Release ABI

Release binary có thể strip debug metadata nhưng ABI identity vẫn phải tồn tại.

---

# 750.145 — Stack Unwinding

AXABI cung cấp abstract unwind contract:

```text
unwind_table
frame_info
restore_state
```

backend map xuống platform format.

---

# 750.146 — Crash Compatibility

Crash runtime có thể reconstruct:

```text
module
symbol
offset
ABI frame
```

nếu unwind metadata tồn tại.

---

# 750.147 — Sanitizer ABI

Runtime instrumentation có thể add:

```text
stack checks
bounds metadata
memory poisoning
```

nhưng instrumentation ABI phải distinguish debug/instrumented binaries khỏi production ABI.

---

# 750.148 — Sanitizer Compatibility

Không link arbitrary instrumented runtime vào production ABI nếu ABI fingerprint không match.

---

# 750.149 — Profile ABI

Compiler profile:

```text
debug
release
size
speed
realtime
instrumented
```

có thể ảnh hưởng implementation nhưng không được phá stable ABI trừ khi manifest khai báo.

---

# 750.150 — LTO

Link-time optimization được phép inline xuyên module khi:

```text
LTO metadata
```

được cung cấp.

---

# 750.151 — Thin LTO

Compiler có thể giữ summary:

```text
function size
call graph
constant info
visibility
```

để tối ưu mà không cần load toàn bộ module.

---

# 750.152 — ABI Boundary and Optimization

Stable ABI boundary thường ngăn aggressive cross-module optimization.

Compiler có thể cung cấp:

```text
@inline_abi
@final
@internal
```

---

# 750.153 — ABI Internalization

Linker có thể biến public-looking symbol thành local nếu whole-program analysis chứng minh không external reference.

---

# 750.154 — PGO

Profile-guided optimization không được thay đổi stable ABI representation.

---

# 750.155 — Calling Convention Attributes

Có thể khai báo:

```axiom
@callconv("axcall")
@callconv("c")
@callconv("system")
```

---

# 750.156 — System ABI

`system` map tới platform-native external calling convention.

Ví dụ Windows API có thể yêu cầu platform-specific convention.

---

# 750.157 — Import ABI

```axiom
extern "system" fn CreateFileW(...)
```

được compiler bind tới platform ABI.

---

# 750.158 — Export ABI

```axiom
@export
fn ax_main(...)
```

chỉ export khi explicit.

---

# 750.159 — Entry Point ABI

Native executable có canonical internal entry:

```text
__ax_entry
```

Platform startup adapter gọi entry này.

---

# 750.160 — Startup

```text
OS
 ↓
platform entry
 ↓
AX runtime initialization
 ↓
AXAPPLICATION
 ↓
user main
```

---

# 750.161 — Runtime Initialization

Runtime initialize tối thiểu:

```text
memory
thread state
process state
async context if needed
security context
application state
```

Không bắt buộc initialize toàn bộ Civilization Runtime.

---

# 750.162 — Freestanding Mode

Axiom phải hỗ trợ:

```text
@freestanding
```

cho kernel/embedded/boot/runtime-level programs.

---

# 750.163 — Freestanding ABI

Không có:

```text
OS runtime
heap
thread runtime
filesystem
```

trừ những phần application cung cấp.

---

# 750.164 — Hosted Mode

Normal applications dùng full runtime.

---

# 750.165 — Kernel Boundary

AXABI phải cho phép kernel ABI profile riêng.

---

# 750.166 — Syscall ABI

Syscall wrapper:

```text
Axiom ABI
 ↓
platform syscall ABI
```

không expose raw syscall calling convention tới ordinary application code.

---

# 750.167 — OS Callback ABI

OS callback adapter phải translate:

```text
OS calling convention
→ AX ABI
```

nếu cần.

---

# 750.168 — Callback Reentrancy

ABI metadata có thể khai báo callback:

```text
may_reenter
no_reenter
async_callback
```

---

# 750.169 — Thread ABI

Thread entry:

```axiom
fn thread_main(context: pointer)
```

conceptually.

Actual OS thread ABI nằm trong AXPROCESS backend.

---

# 750.170 — TLS ABI

Thread-local variables có backend-specific TLS model:

```text
LOCAL_EXEC
INITIAL_EXEC
LOCAL_DYNAMIC
GENERAL_DYNAMIC
```

hoặc Windows equivalent.

---

# 750.171 — TLS Model Selection

Compiler chọn model dựa trên:

```text
static/dynamic module
platform
visibility
performance profile
```

---

# 750.172 — Global Variable ABI

Public global data phải có:

```text
symbol
size
alignment
visibility
mutability
```

---

# 750.173 — Constant Data

Immutable public data có thể nằm trong read-only section.

---

# 750.174 — Read-Only ABI

Module không được mutate immutable ABI data thông qua unsafe alias.

---

# 750.175 — Section Contract

Object ABI hỗ trợ:

```text
.text
.rodata
.data
.bss
.tls
metadata
unwind
debug
```

platform backend có thể thêm sections.

---

# 750.176 — Relocation

AXABI không tự implement relocation encoding; object backend chịu trách nhiệm.

Nhưng ABI phải xác định relocation semantic requirements.

---

# 750.177 — PIC

Position-independent code là target/profile property.

---

# 750.178 — PIE

Executable có thể dùng PIE nếu platform profile yêu cầu/hỗ trợ.

---

# 750.179 — GOT/PLT

ELF backend có thể dùng GOT/PLT.

AXABI core không phụ thuộc chúng.

---

# 750.180 — Windows Import Table

PE backend map external symbols vào import table.

---

# 750.181 — Mach-O Binding

Mach-O backend map symbols vào binding/export structures.

---

# 750.182 — Symbol Hash

Linker có thể generate symbol hash:

```text
signature hash
ABI hash
```

để fast resolution.

---

# 750.183 — Signature Hash

Function signature hash bao gồm:

```text
parameter types
return type
calling convention
ABI attributes
```

---

# 750.184 — Type Identity

Type identity không chỉ dựa trên source name.

Canonical identity:

```text
module
namespace
type name
generic parameters
ABI-relevant attributes
```

---

# 750.185 — Anonymous Types

Anonymous/internal compiler types không được trở thành stable public ABI type trừ khi explicitly frozen.

---

# 750.186 — ABI Metadata

Every public ABI entity có metadata:

```axiom
abi_entity {
    name
    kind
    type
    layout
    calling_convention
    visibility
    version
}
```

---

# 750.187 — ABI Inspection

Native tool:

```text
ax abi inspect module.axm
```

hiển thị:

```text
symbols
types
layouts
calling conventions
ABI version
fingerprint
dependencies
```

---

# 750.188 — ABI Diff

Tool:

```text
ax abi diff old.axm new.axm
```

phát hiện:

```text
added symbol
removed symbol
signature change
layout change
alignment change
calling convention change
```

---

# 750.189 — ABI Compatibility Check

CI:

```text
ax abi check
```

fail nếu public ABI breaking change không được version bump.

---

# 750.190 — ABI Manifest File

Binary/module có thể embed:

```text
AXABI manifest
```

để linker/runtime không cần source.

---

# 750.191 — AI Metadata

ABI manifest có machine-readable metadata:

```text
purpose
ownership
thread safety
async behavior
error behavior
stability
```

AI tooling có thể consume metadata.

---

# 750.192 — AI ABI Safety

AI assistant có thể:

```text
explain ABI mismatch
generate FFI declaration
inspect struct layout
suggest migration thunk
```

nhưng không được tự động bypass ABI safety.

---

# 750.193 — Binary Introspection

Runtime có thể expose:

```axiom
abi.module_info()
abi.symbol_info()
abi.type_info()
```

chỉ cho metadata được public.

---

# 750.194 — Reflection vs ABI

ABI metadata không đồng nghĩa full runtime reflection.

Reflection có thể là higher-level feature.

---

# 750.195 — Size Optimization

ABI metadata nên có compact encoding:

```text
varint
interned strings
hashed type IDs
compressed tables
```

---

# 750.196 — Zero Runtime Cost

ABI metadata không cần được load vào runtime nếu application không sử dụng reflection/debugging.

---

# 750.197 — Native Binary Compactness

Compiler nên strip:

```text
unused symbols
unused metadata
unused runtime ABI tables
```

trong release binary.

---

# 750.198 — Cross-Module Inlining

Public ABI function có thể có optional IR body metadata:

```text
inline body
```

nhưng fallback vẫn phải ABI-compatible.

---

# 750.199 — Binary Cache

Compiler có thể cache:

```text
object
IR summary
ABI manifest
codegen result
```

nếu source + compiler ABI + target fingerprints không đổi.

---

# 750.200 — Incremental ABI

Nếu implementation thay đổi nhưng public ABI fingerprint không đổi:

```text
downstream modules
```

không nhất thiết phải rebuild.

---

# 750.201 — ABI Dependency Graph

Build system tracks:

```text
module
 ↓
ABI fingerprint
 ↓
dependent modules
```

---

# 750.202 — Rebuild Rule

Rebuild dependent module khi:

```text
ABI-breaking change
```

không chỉ khi source timestamp thay đổi.

---

# 750.203 — ABI Cache Key

Canonical:

```text
source_hash
compiler_hash
ABI_hash
target_hash
optimization_profile
dependency_ABI_hashes
```

---

# 750.204 — Reproducible ABI

Same source + same toolchain + same target/profile phải tạo cùng ABI manifest.

---

# 750.205 — Deterministic Symbol Naming

Symbol mangling không được phụ thuộc:

```text
memory address
build timestamp
random seed
```

---

# 750.206 — Build ID

Binary có thể có build ID nhưng build ID không được thay đổi ABI fingerprint.

---

# 750.207 — Reproducible Binary

ABI determinism là prerequisite cho reproducible native artifacts nhưng không tự đảm bảo toàn binary reproducibility.

---

# 750.208 — Security Metadata

ABI manifest có thể declare:

```text
required capabilities
sandbox requirements
FFI trust level
unsafe exports
```

---

# 750.209 — Unsafe ABI

Một ABI entity có thể đánh dấu:

```axiom
@unsafe_abi
```

khi caller phải đảm bảo invariant ngoài compiler.

---

# 750.210 — Safe ABI

Safe public ABI phải có compiler-checkable contracts ở mức có thể.

---

# 750.211 — ABI Contracts

Ví dụ:

```axiom
@requires(len > 0)
@requires(buffer.length >= len)
fn process(buffer: span<u8>, len: usize)
```

Compiler/runtime tooling có thể sử dụng contract.

---

# 750.212 — Contract Is Not Runtime Mandatory

Release build có thể erase checks nếu static analysis chứng minh safety hoặc policy cho phép.

---

# 750.213 — FFI Safety

FFI declaration phải specify:

```text
ownership
nullability
thread safety
blocking
calling convention
layout
error convention
```

---

# 750.214 — Blocking FFI

External function có metadata:

```axiom
@blocking
extern "c" fn legacy_io(...)
```

để AXTASK không gọi nó trên async worker.

---

# 750.215 — Async FFI

Native callback-based API có thể được wrapped bằng AXASYNC.

---

# 750.216 — Callback Context ABI

Callback context là opaque pointer/handle.

Lifetime contract phải explicit.

---

# 750.217 — ABI Boundary and Panic

Axiom panic không tự động cross foreign ABI.

Foreign boundary adapter chuyển thành:

```text
error
status
abort
```

theo declaration.

---

# 750.218 — ABI Boundary and Error Ownership

Returned error object phải có ownership contract.

---

# 750.219 — ABI Boundary and Strings

Không tự động convert:

```text
UTF-8
UTF-16
locale strings
```

trừ explicit FFI type.

---

# 750.220 — Windows String ABI

Windows API wrappers có thể dùng:

```text
UTF-16
```

tại platform boundary.

Axiom internal string vẫn UTF-8.

---

# 750.221 — C++ Interop

C++ ABI không phải primary stable ABI.

Axiom nên hỗ trợ C-compatible bridge trước.

---

# 750.222 — C++ Adapter

C++ libraries có thể được wrapped bằng thin C ABI shim.

Axiom compiler không phụ thuộc C++ compiler.

---

# 750.223 — Objective-C / Swift Boundary

Apple-specific adapters có thể expose C-compatible or platform-native bridge.

Core AXABI không phụ thuộc Swift/Objective-C runtime.

---

# 750.224 — JVM/.NET

Không thuộc native core ABI.

Có thể xây external bridge sau.

---

# 750.225 — GC Interop

Axiom ABI không yêu cầu GC.

Nếu foreign runtime dùng GC:

```text
interop adapter
```

chịu trách nhiệm rooting/lifetime.

---

# 750.226 — ABI and Memory Model

ABI phải phù hợp AXMEMORY:

```text
alignment
ownership
lifetime
atomicity
aliasing
```

---

# 750.227 — Aliasing ABI

Compiler có thể annotate:

```axiom
@noalias
```

nếu caller contract đảm bảo.

---

# 750.228 — Noalias Is Contract

Compiler không được tự assume noalias chỉ vì pointer type.

---

# 750.229 — Volatile ABI

MMIO/volatile accesses phải preserve observable access semantics.

---

# 750.230 — Atomic ABI

Cross-module atomic object phải có identical:

```text
size
alignment
ordering model
```

---

# 750.231 — Thread-Safe ABI Metadata

Function có thể declare:

```text
THREAD_SAFE
THREAD_CONFINED
REQUIRES_LOCK
```

để tooling/AI hiểu contract.

---

# 750.232 — Reentrancy Metadata

```text
REENTRANT
NON_REENTRANT
CALLBACK_REENTRANT
```

---

# 750.233 — Async Metadata

Public function có:

```text
SYNC
ASYNC
MAY_BLOCK
NEVER_BLOCK
```

---

# 750.234 — ABI Documentation Generation

Compiler có thể generate:

```text
ax abi doc
```

từ ABI metadata.

---

# 750.235 — ABI Test Artifact

Compiler test suite tạo:

```text
abi_probe
```

chạy cross-target để verify:

```text
sizeof
alignof
offsetof
calling
return
```

---

# 750.236 — Golden ABI Tests

Mỗi supported target có golden ABI records.

---

# 750.237 — Cross-Compiler Verification

Axiom có thể test:

```text
Axiom ↔ C
Axiom ↔ platform ABI
```

qua generated probe binaries.

---

# 750.238 — ABI Fuzzing

Fuzzer generate combinations:

```text
structs
arrays
vectors
nested types
returns
arguments
```

để phát hiện compiler ABI bugs.

---

# 750.239 — ABI Differential Testing

Compare:

```text
Axiom compiler
vs
platform reference ABI behavior
```

tại FFI boundaries.

---

# 750.240 — ABI Formal Invariants

```text
ABI-INV-01   Every ABI-visible symbol has a deterministic identity.
ABI-INV-02   Every ABI-visible function has an explicit calling convention.
ABI-INV-03   Argument classification is deterministic for a target.
ABI-INV-04   Return classification is deterministic for a target.
ABI-INV-05   Stack alignment requirements are always satisfied.
ABI-INV-06   Register volatility is defined by the selected ABI.
ABI-INV-07   ABI-visible struct layout is deterministic.
ABI-INV-08   ABI-visible field offsets are deterministic.
ABI-INV-09   ABI-visible alignment is deterministic.
ABI-INV-10   ABI-visible enum representation is deterministic.

ABI-INV-11   Public generic ABI entities cannot depend on unstable compiler-private layout.
ABI-INV-12   Closure ABI distinguishes code from captured environment.
ABI-INV-13   Function pointers have a defined representation.
ABI-INV-14   Large aggregate returns use an explicitly defined mechanism.
ABI-INV-15   Hidden ABI parameters have deterministic ordering.
ABI-INV-16   Async frames follow a versioned task-frame ABI.
ABI-INV-17   Async frame ownership is explicit.
ABI-INV-18   Future ABI does not expose unstable private compiler state without declaration.
ABI-INV-19   Allocated memory cannot be freed through an incompatible allocator contract.
ABI-INV-20   Ownership-transfer semantics are explicit at ABI boundaries.

ABI-INV-21   Native ABI layout is not silently reused as wire serialization.
ABI-INV-22   Endianness is explicit for wire-format ABI.
ABI-INV-23   Volatile accesses preserve their observable semantics.
ABI-INV-24   Atomic ABI size and alignment are compatible across module boundaries.
ABI-INV-25   FFI declarations explicitly identify foreign calling conventions.
ABI-INV-26   Foreign exceptions cannot silently cross an Axiom ABI boundary.
ABI-INV-27   Foreign string encodings are explicit.
ABI-INV-28   ABI mismatch is detected before unsafe module execution where possible.
ABI-INV-29   ABI fingerprints are deterministic.
ABI-INV-30   ABI version changes follow declared compatibility rules.

ABI-INV-31   Symbol visibility is explicit.
ABI-INV-32   Dynamic-module dependencies declare required ABI compatibility.
ABI-INV-33   Hot reload cannot unload code referenced by live execution state.
ABI-INV-34   Compatibility thunks cannot silently reinterpret incompatible layouts.
ABI-INV-35   ABI metadata does not require runtime loading unless requested.
ABI-INV-36   ABI metadata cannot grant security authority.
ABI-INV-37   ABI caches are invalidated when ABI-relevant inputs change.
ABI-INV-38   Reproducible builds cannot depend on nondeterministic symbol naming.
ABI-INV-39   Freestanding ABI does not implicitly require hosted runtime services.
ABI-INV-40   Every supported target has a mechanically testable ABI profile.
```

---

# 750.241 — Canonical ABI Data Model

Implementation-level schema:

```axiom
abi_module {
    module_id
    abi_version
    target
    architecture
    endian
    pointer_bits

    calling_conventions[]
    types[]
    symbols[]
    imports[]
    exports[]

    allocator_abi
    error_abi
    async_abi
    unwind_abi

    layout_fingerprint
    abi_fingerprint
}
```

---

# 750.242 — ABI Type Record

```axiom
abi_type {
    type_id
    kind
    size
    alignment
    fields[]
    flags
}
```

---

# 750.243 — ABI Function Record

```axiom
abi_function {
    symbol
    calling_convention
    parameters[]
    return_type
    attributes
    visibility
    version
}
```

---

# 750.244 — ABI Field Record

```axiom
abi_field {
    name
    type
    offset
    size
    alignment
    flags
}
```

---

# 750.245 — ABI Compatibility Algorithm

Linker:

```text
1. Load module manifests
2. Verify target
3. Verify architecture
4. Verify ABI major
5. Resolve symbols
6. Compare signatures
7. Compare ABI-visible layouts
8. Compare calling conventions
9. Compare required runtime ABI
10. Validate dependencies
11. Apply safe relocations/thunks
12. Emit final binary
```

---

# 750.246 — ABI Failure Is Early

Không chờ runtime crash để phát hiện ABI mismatch nếu linker có thể phát hiện lúc build.

---

# 750.247 — Runtime ABI Check

Dynamic loader có thể repeat critical compatibility validation:

```text
module ABI fingerprint
runtime ABI fingerprint
```

---

# 750.248 — Versioned Runtime

Executable có thể yêu cầu:

```text
AXRUNTIME ABI >= X
```

runtime loader reject incompatible versions.

---

# 750.249 — Runtime ABI Minimality

AXABI runtime itself phải nhỏ.

Metadata-heavy ABI tooling không được kéo vào production executable nếu không cần.

---

# 750.250 — Final Architecture

```text
                    AXABI
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   Calling ABI     Type ABI      Runtime ABI
       │              │              │
       ├── x64        ├── struct     ├── async
       ├── ARM64      ├── enum       ├── allocator
       └── WASM       ├── slice      ├── error
                      ├── vector     └── unwind
                      └── opaque
       │
       ▼
   Module ABI
       │
       ├── static library
       ├── dynamic library
       ├── plugin
       └── executable
       │
       ▼
   Platform ABI
       ├── PE64
       ├── ELF
       ├── Mach-O
       └── WASM
```

---

# 750.251 — Definition of Done

```text
BOOTSTRAP-750
STATUS: COMPLETE / FROZEN

AXABI 5.0
 ├── Canonical Axiom Calling Convention
 ├── Register ABI
 ├── Stack ABI
 ├── Scalar ABI
 ├── Aggregate ABI
 ├── Struct Layout ABI
 ├── Enum ABI
 ├── Slice/Span ABI
 ├── String ABI
 ├── Pointer ABI
 ├── SIMD ABI
 ├── Generic ABI
 ├── Trait Dispatch ABI
 ├── Method ABI
 ├── Function Pointer ABI
 ├── Closure ABI
 ├── Variadic ABI
 ├── Error ABI
 ├── Panic/Trap ABI
 ├── Unwind ABI
 ├── Async ABI
 ├── Future ABI
 ├── Task Frame ABI
 ├── Allocator ABI
 ├── Ownership Transfer ABI
 ├── FFI
 ├── C ABI
 ├── Platform ABI
 ├── Symbol Mangling
 ├── Symbol Visibility
 ├── Static Library ABI
 ├── Dynamic Library ABI
 ├── Plugin ABI
 ├── Hot Reload Boundary
 ├── PE64
 ├── ELF
 ├── Mach-O
 ├── Android
 ├── iOS
 ├── WASM
 ├── ABI Fingerprint
 ├── ABI Manifest
 ├── ABI Diff
 ├── ABI Compatibility Checking
 ├── ABI Cache
 ├── AI Metadata
 ├── FFI Safety
 ├── ABI Testing
 ├── ABI Fuzzing
 ├── 40 Formal Invariants
 └── Native ABI Runtime 5.0
```

## AXABI 5.0 — FROZEN

Một quyết định kiến trúc quan trọng được khóa ở đây:

> **Axiom không lấy C ABI làm ABI nội bộ.**  
> Axiom có **AXCALL/AXABI riêng**, sau đó mới có adapter sang C/System/OS ABI.

Điều này cho phép compiler tối ưu native code theo kiến trúc Axiom mà vẫn giữ FFI sạch và có kiểm soát.

---

# BOOTSTRAP-751 — AXMODULE

**Native Module, Package, Library & Link Unit Runtime — module identity, source/package identity, compilation unit, interface unit, implementation unit, static library, dynamic library, object aggregation, dependency graph, import/export, symbol ownership, module initialization, module unloading, plugin boundary, ABI manifest integration, module capabilities, versioning, semantic version ranges, feature flags, optional dependencies, platform variants, target variants, build profiles, incremental compilation, module cache, precompiled module/interface, module graph invalidation, reproducible module builds, package-to-module mapping, native artifact composition, cross-module optimization boundary, module security metadata, deterministic module resolution, module inspection và Native Module Runtime 5.0.**