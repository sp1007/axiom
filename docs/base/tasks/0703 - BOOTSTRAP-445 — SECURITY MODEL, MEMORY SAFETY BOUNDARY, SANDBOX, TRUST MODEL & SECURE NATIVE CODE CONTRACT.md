# BOOTSTRAP-445 — SECURITY MODEL, MEMORY SAFETY BOUNDARY, SANDBOX, TRUST MODEL & SECURE NATIVE CODE CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Axiom không theo hướng Rust với borrow checker toàn diện, cũng không theo hướng GC. Vì vậy security model phải được thiết kế rõ ràng để đạt:

- safe code có các guarantee mạnh;
- không biến compiler thành một hệ thống lifetime quá phức tạp;
- unsafe là ranh giới rõ ràng;
- FFI/OS/hardware được coi là trust boundary;
- optimizer vẫn được phép hoạt động mạnh;
- không có hidden runtime safety machinery.

Mô hình tổng quát:

```text
                    AXIOM PROGRAM
                         │
             ┌───────────┴───────────┐
             │                       │
          SAFE CODE              UNSAFE CODE
             │                       │
       compiler guarantees      programmer contract
             │                       │
             └───────────┬───────────┘
                         │
                   TRUST BOUNDARY
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         FFI             OS          Hardware
```

---

## 445.1 — Ba mức trust

Axiom phân biệt:

```text
Trusted Compiler
Trusted Runtime
Program Code
```

và bên ngoài:

```text
Foreign Code
Operating System
Hardware
```

---

## 445.2 — Safe code

Safe code phải tuân thủ language safety rules.

Compiler chịu trách nhiệm reject các chương trình vi phạm các invariant mà language định nghĩa là statically enforceable.

---

## 445.3 — Unsafe code

Unsafe không có nghĩa:

> compiler tắt kiểm tra.

Nó có nghĩa:

> programmer được phép thực hiện operations mà compiler không thể bảo đảm safety hoàn toàn.

---

## 445.4 — Unsafe boundary

Các operation điển hình cần unsafe:

```text
raw pointer dereference
arbitrary address access
inline assembly
raw syscall
MMIO
executable memory
unchecked indexing
foreign ABI assumptions
```

---

## 445.5 — Unsafe block

Conceptual:

```text
unsafe {
    ...
}
```

---

## 445.6 — Unsafe function

```text
unsafe fn read_raw(...)
```

Caller phải explicitly acknowledge unsafe contract.

---

## 445.7 — Unsafe propagation

Gọi `unsafe fn` từ safe code phải bị compiler reject nếu không nằm trong unsafe context.

---

## 445.8 — Unsafe attribute

Các declarations như:

```text
@unsafe
```

chỉ được phép ở những semantic contexts được định nghĩa rõ.

---

## 445.9 — Safety documentation

Unsafe API phải có machine-readable safety contract khi có thể:

```text
@safety(
    requires = "...",
    guarantees = "..."
)
```

Syntax chính xác có thể thay đổi.

---

## 445.10 — AI safety metadata

Compiler semantic database expose:

```text
function.is_unsafe
function.safety_requirements
function.effects
```

---

## 445.11 — Safe pointer abstraction

Safe code có thể sử dụng:

```text
Slice<T>
StringSlice
Option<&T>
```

hoặc các view/handle abstractions mà không expose arbitrary addresses.

---

## 445.12 — Raw pointer

Raw pointers:

```text
*const T
*mut T
```

là explicit low-level types.

---

## 445.13 — Pointer dereference

Raw pointer dereference yêu cầu unsafe.

---

## 445.14 — Pointer creation

Tạo pointer từ reference/view có thể safe nếu compiler biết conversion không tạo invalid state.

---

## 445.15 — Integer-to-pointer

Conversion:

```text
usize as *mut T
```

là unsafe.

---

## 445.16 — Pointer-to-integer

Pointer → integer có thể được phép trong unsafe/platform context.

---

## 445.17 — Pointer provenance

Axiom không cho phép optimizer coi mọi integer có cùng numeric address là interchangeable pointer provenance.

Pointer provenance phải được giữ trong IR khi cần để tránh optimization sai.

---

## 445.18 — Pointer equality

Pointer equality và integer equality là hai operations khác nhau.

---

## 445.19 — Pointer ordering

Ordering raw pointers chỉ được định nghĩa khi language/platform contract cho phép.

Không giả định mọi pointer có thể so sánh thứ tự như integer.

---

## 445.20 — Null raw pointer

Raw pointer có thể biểu diễn null.

Nhưng:

```text
null raw pointer
```

không phải safe reference.

---

## 445.21 — No implicit null

Axiom không có `null` cho ordinary references.

`Option<T>` biểu diễn optional value.

---

## 445.22 — Null dereference

Dereference null raw pointer là unsafe UB.

---

## 445.23 — Dangling pointer

Dereference pointer tới object đã hết lifetime là UB.

---

## 445.24 — Use-after-free

Safe ownership model phải ngăn trường hợp này trong safe code khi object ownership/view lifetime nằm trong compiler's enforceable domain.

---

## 445.25 — Unsafe lifetime escape

Raw pointer có thể escape scope.

Compiler không cố xây full Rust-style lifetime theorem cho raw pointer.

---

## 445.26 — View lifetime

Safe view/reference có lifetime dependency được compiler theo dõi ở mức local flow.

---

## 445.27 — Local borrow

Ví dụ conceptual:

```text
fn first(s: []i32) -> &i32 {
    &s[0]
}
```

Compiler đảm bảo returned reference không outlive source khi semantics yêu cầu.

---

## 445.28 — No explicit lifetime syntax

Axiom không yêu cầu:

```text
'a
'b
```

trong API thông thường.

---

## 445.29 — Lifetime inference

Compiler suy ra dependency từ:

```text
source
view
return
```

khi có thể.

---

## 445.30 — Ambiguous lifetime

Nếu compiler không chứng minh được safe relationship:

```text
compile error
```

hoặc API phải chuyển sang owned value/explicit unsafe.

---

## 445.31 — No lifetime escape hatch hidden

Unsafe phải được viết rõ.

Compiler không tự âm thầm biến ambiguous lifetime thành unsafe.

---

## 445.32 — Move safety

Sau move:

```text
x
```

không còn được dùng như owner.

---

## 445.33 — Double drop

Compiler phải bảo đảm safe code không drop cùng ownership hai lần.

---

## 445.34 — Partial initialization

Chỉ các fields đã initialized mới được cleanup.

---

## 445.35 — Uninitialized memory

Reading uninitialized ordinary value là forbidden trong safe code.

---

## 445.36 — Maybe-uninitialized state

MIR phải theo dõi:

```text
Uninitialized
Initialized
Moved
Destroyed
```

---

## 445.37 — `MaybeUninit`

Low-level library có thể cung cấp explicit abstraction tương đương:

```text
MaybeUninit<T>
```

với unsafe initialization contract.

---

## 445.38 — Zero initialization

Compiler không được giả định mọi type có zero bit pattern hợp lệ.

Ví dụ:

```text
enum
reference
trait object
```

có thể có invalid bit patterns.

---

## 445.39 — `memset(0)` safety

Zeroing arbitrary `T` không phải safe operation.

---

## 445.40 — Byte representation

Raw byte access phải phân biệt:

```text
bytes
typed value
```

---

## 445.41 — Byte-to-T conversion

Converting arbitrary bytes thành `T` yêu cầu validity proof hoặc unsafe.

---

## 445.42 — Bitcast

`bitcast<T>` chỉ safe nếu source/destination representation hợp lệ theo compiler rules.

---

## 445.43 — Alignment

Typed pointer dereference phải đáp ứng alignment requirements.

---

## 445.44 — Misaligned access

Misaligned typed access là unsafe hoặc phải dùng explicit unaligned API.

---

## 445.45 — Unaligned load

```text
load_unaligned<T>()
```

là low-level operation với semantics riêng.

---

## 445.46 — Out-of-bounds access

Safe indexing phải kiểm tra bounds hoặc được compiler chứng minh bounds.

---

## 445.47 — Unchecked indexing

```text
unsafe a.get_unchecked(i)
```

cho phép bỏ check.

---

## 445.48 — Bounds-check elimination

Compiler có thể loại bounds check khi proof tồn tại.

---

## 445.49 — No hidden bounds-check guarantee

Không cam kết mọi indexing đều zero-cost.

Compiler chỉ loại check khi có đủ information.

---

## 445.50 — Slice validity

Slice/view phải luôn có:

```text
ptr
length
```

và invariant:

```text
length >= 0
```

cùng pointer validity/alignment contract.

---

## 445.51 — Slice provenance

Slice không tự động kéo dài lifetime của backing storage.

---

## 445.52 — String validity

`String` invariant:

```text
valid UTF-8
```

---

## 445.53 — Raw bytes to String

Phải validate UTF-8 hoặc sử dụng explicit unchecked constructor trong unsafe API.

---

## 445.54 — CString

CString phải bảo đảm null termination.

---

## 445.55 — Interior null

UTF-8 `String` có thể chứa U+0000.

CString semantics phải phân biệt byte `0` và Unicode string semantics.

---

## 445.56 — Integer safety

Integer operations có semantics explicit:

```text
checked
wrapping
saturating
```

---

## 445.57 — Division by zero

Division by zero:

```text
panic
```

hoặc defined failure behavior theo operation variant.

---

## 445.58 — Shift bounds

Invalid shift count phải có defined semantics hoặc panic tùy operation.

---

## 445.59 — Enum validity

Safe code không được tạo enum discriminator invalid.

---

## 445.60 — Raw enum construction

Arbitrary discriminator construction là unsafe.

---

## 445.61 — Tagged union validity

Tag và payload phải nhất quán.

---

## 445.62 — Type punning

Arbitrary reinterpretation giữa unrelated types không safe.

---

## 445.63 — `repr(C)`

`@repr(C)` cung cấp layout contract, không tự biến mọi operation thành safe.

---

## 445.64 — Packed structures

Packed fields có thể không aligned.

Access phải được compiler xử lý đúng hoặc yêu cầu unaligned operation.

---

## 445.65 — FFI trust boundary

Tất cả foreign code được coi là:

```text
externally trusted contract
```

---

## 445.66 — Safe FFI wrapper

Một wrapper có thể safe nếu nó kiểm tra đầy đủ preconditions.

---

## 445.67 — Raw FFI

Raw foreign function declarations thường nằm trong unsafe/platform layer.

---

## 445.68 — FFI pointer contract

FFI declaration phải mô tả ownership:

```text
@borrowed
@owned
@consumes
@returns_owned
```

---

## 445.69 — FFI string contract

Không được giả định native `char*` là UTF-8 `String`.

Phải explicit encoding contract.

---

## 445.70 — FFI integer contract

`int`/`long` native types phải map theo target ABI, không được map tùy tiện thành `i32/i64`.

---

## 445.71 — FFI struct contract

Native structs dùng explicit representation.

---

## 445.72 — FFI union contract

Union access cần explicit semantics.

---

## 445.73 — FFI callback

Native callback phải giữ code/environment lifetime phù hợp.

---

## 445.74 — Callback ownership

Compiler không tự giả định foreign caller sẽ giữ callback bao lâu.

---

## 445.75 — FFI unwind

Unwind qua FFI boundary chỉ được phép nếu ABI hỗ trợ.

---

## 445.76 — FFI panic

Default:

```text
panic
→ catch/convert/abort
```

tại FFI boundary.

---

## 445.77 — Foreign exception

Foreign exception không được tự động biến thành Axiom `Result`.

Adapter phải explicit.

---

## 445.78 — Data race

Safe shared mutable data phải dùng:

```text
Atomic
Mutex
RwLock
```

hoặc abstraction có synchronization contract.

---

## 445.79 — Send

Type chỉ được transfer giữa threads nếu đáp ứng `Send`.

---

## 445.80 — Share

Type chỉ được shared concurrently nếu đáp ứng `Share`.

---

## 445.81 — Auto Send/Share

Compiler có thể derive nếu fields đều đáp ứng requirements.

---

## 445.82 — Unsafe Send/Share

Unsafe implementation có thể override compiler inference nhưng phải explicit.

---

## 445.83 — Data-race-free safe subset

Safe Axiom concurrency APIs phải không tạo data race nếu được dùng theo contract.

---

## 445.84 — Atomic memory ordering

Compiler phải preserve ordering semantics.

---

## 445.85 — Lock poisoning

Poisoning không phải language semantic bắt buộc.

Library chọn policy.

---

## 445.86 — Deadlock

Deadlock không được coi là memory safety violation.

Compiler không hứa loại bỏ deadlock.

---

## 445.87 — Race detector

Optional tooling có thể phát hiện runtime races.

---

## 445.88 — Thread lifetime

Thread handles là resources.

Drop policy đã khóa ở 424.

---

## 445.89 — Detached thread

Detach phải explicit.

---

## 445.90 — Async cancellation

Cancellation phải chạy cleanup.

---

## 445.91 — Resource leak

Leak không nhất thiết là memory corruption.

Axiom phân biệt:

```text
memory safety
resource safety
liveness
```

---

## 445.92 — Intentional leak

Low-level code có thể explicit leak:

```text
leak(value)
```

nếu library cung cấp.

---

## 445.93 — Leak is not use-after-free

Compiler không coi leak là dangling pointer.

---

## 445.94 — Resource capability

File/socket/process handle nên là opaque resource type.

---

## 445.95 — Capability possession

Có handle nghĩa là code sở hữu quyền tương ứng theo OS semantics.

---

## 445.96 — Capability transfer

Move handle transfer quyền sở hữu.

---

## 445.97 — Capability duplication

OS-supported duplication tạo capability mới.

---

## 445.98 — Capability revocation

Closing/destroying owner revokes resource capability khi platform semantics quy định.

---

## 445.99 — Sandbox

Sandbox không phải language safety.

Ví dụ:

```text
WASM sandbox
OS sandbox
container
mobile sandbox
```

là platform/security layers.

---

## 445.100 — Language safety ≠ sandbox

Một chương trình memory-safe vẫn có thể:

```text
delete files
open sockets
```

nếu OS cấp quyền.

---

## 445.101 — Capability-restricted runtime

Runtime có thể được build chỉ với:

```text
allocator
console
```

mà không link:

```text
filesystem
network
process
```

---

## 445.102 — Capability manifest

Artifact metadata có thể mô tả:

```text
requires:
    filesystem
    network
    threads
```

---

## 445.103 — Minimal privilege

Application nên link/request capability tối thiểu cần thiết khi platform cho phép.

---

## 445.104 — WASM capability

WASM imports là explicit capabilities.

---

## 445.105 — Plugin sandbox

Plugin API có thể expose capability-limited interface.

---

## 445.106 — Untrusted plugin

Không được coi Axiom type safety là sandbox boundary.

Plugin isolation phải do OS/process/WASM sandbox cung cấp.

---

## 445.107 — JIT trust

JIT-generated executable memory thuộc unsafe runtime capability.

---

## 445.108 — Self-modifying code

Không safe mặc định.

---

## 445.109 — Executable memory

```text
RWX
```

không phải default allocation mode.

---

## 445.110 — Memory protection

Platform API phải expose:

```text
read
write
execute
```

permissions explicit.

---

## 445.111 — Secret data

Compiler không đảm bảo register/memory contents được xóa khỏi machine state khi variable drop.

Nếu cần:

```text
secure_zero()
```

là explicit primitive với target-aware semantics.

---

## 445.112 — Constant-time code

Cryptographic library có thể yêu cầu:

```text
@constant_time
```

nhưng compiler chỉ được thực hiện các transformations không phá contract.

---

## 445.113 — Timing side channels

Language core không thể bảo đảm loại bỏ toàn bộ side channels.

Đây là security engineering concern.

---

## 445.114 — Spectre-style issues

Compiler có thể cung cấp target-specific mitigations.

Không coi memory safety là protection hoàn chỉnh trước microarchitectural side channels.

---

## 445.115 — Stack protection

Compiler có thể hỗ trợ:

```text
stack canary
shadow stack
CFI
```

như optional security profiles.

---

## 445.116 — Control-flow integrity

Optional instrumentation/metadata.

---

## 445.117 — Shadow stack

Target/platform feature có thể được sử dụng nếu supported.

---

## 445.118 — ASLR

Được xử lý bởi OS/linker/runtime policy.

---

## 445.119 — DEP/NX

Executable image phải hỗ trợ non-executable memory khi target yêu cầu.

---

## 445.120 — RELRO-like protections

ELF security profile có thể bật read-only relocation structures sau relocation.

---

## 445.121 — Import hardening

Dynamic imports có thể được restricted theo deployment policy.

---

## 445.122 — Binary hardening profile

Conceptual:

```text
security=baseline
security=hardened
security=max
```

Compiler/linker quyết định feature set.

---

## 445.123 — Security profile ≠ semantics

Security profile thay đổi emitted protections, không thay đổi language meaning.

---

## 445.124 — Safe API design

Standard library ưu tiên:

```text
Result
Option
owned handles
views
typed APIs
```

thay vì:

```text
raw pointers
magic integers
global mutable state
```

---

## 445.125 — Raw integer handles

Được phép ở platform layer nhưng không nên là standard safe abstraction nếu typed handle có thể dùng.

---

## 445.126 — Handle newtypes

Mỗi resource có nominal type riêng:

```text
FileHandle
SocketHandle
ProcessHandle
```

---

## 445.127 — Type-state APIs

Library có thể dùng types để biểu diễn:

```text
Connected
Closed
Listening
```

nhưng không bắt buộc compiler language feature riêng.

---

## 445.128 — Input validation

Foreign/user input không được coi là valid typed value chỉ vì parse thành bytes.

---

## 445.129 — Parser boundary

Parser/decoder phải validate:

```text
length
encoding
ranges
structure
```

---

## 445.130 — Integer conversion

Input conversion dùng checked conversion mặc định.

---

## 445.131 — Serialization

Deserialization phải coi input là untrusted.

---

## 445.132 — Unsafe deserialization

Zero-copy deserialization có thể dùng unsafe fast path nhưng phải có explicit validity contract.

---

## 445.133 — Network input

Network bytes là untrusted data.

Standard networking APIs không tự động tạo typed objects từ arbitrary bytes.

---

## 445.134 — File input

File contents không được assume trusted.

---

## 445.135 — Memory mapped input

Mapped bytes vẫn là untrusted unless application validates them.

---

## 445.136 — Compiler security

Compiler phải reject malformed source safely.

---

## 445.137 — Compiler crash

Malformed source không được phép dẫn đến arbitrary code execution trong compiler process nếu có thể tránh.

---

## 445.138 — Comptime sandbox

`comptime` không có filesystem/network/process access mặc định.

Điều này đã khóa ở 431.

---

## 445.139 — Build scripts

Build scripts là external trusted code và phải được phân biệt với comptime.

---

## 445.140 — Package scripts

Package installation không được tự động execute arbitrary scripts trong secure/default mode nếu package manager có thể tránh.

---

## 445.141 — Dependency provenance

Package metadata có:

```text
source
version
hash
publisher/signature
```

khi ecosystem hỗ trợ.

---

## 445.142 — Dependency lock

Lockfile đảm bảo dependency graph deterministic.

---

## 445.143 — Artifact hash

Build artifact có content hash.

---

## 445.144 — Compiler version trust

Compiler binary là một trust root.

---

## 445.145 — Bootstrap trust

Self-hosting compiler phải có bootstrap verification.

---

## 445.146 — Stage comparison

Có thể:

```text
Stage0 compiler
→ build Stage1
→ Stage1 build Stage2
```

và compare artifacts.

---

## 445.147 — Reproducible bootstrap

Stage1/Stage2 deterministic output là security signal quan trọng.

---

## 445.148 — Compiler compromise

Axiom không thể tự bảo vệ khỏi malicious compiler binary.

Supply-chain security phải nằm ngoài language semantics.

---

## 445.149 — Trusted standard library

Core library/runtime binaries là part of trusted computing base nếu linked.

---

## 445.150 — Minimal TCB

Freestanding programs có thể giảm TCB xuống:

```text
compiler
program
platform
```

---

## 445.151 — Runtime TCB

Program dùng standard runtime thêm:

```text
runtime
allocator
platform adapter
```

vào TCB tương ứng.

---

## 445.152 — Unsafe code auditability

Compiler có thể xuất:

```text
unsafe block locations
unsafe call graph
```

---

## 445.153 — Unsafe inventory

Tool:

```text
axiom audit unsafe
```

có thể thống kê:

```text
files
functions
blocks
raw pointer operations
FFI calls
assembly
```

---

## 445.154 — AI unsafe analysis

AI tooling có thể query:

```text
unsafe_sites()
unsafe_callers()
unsafe_requirements()
```

---

## 445.155 — Security diagnostics

Ví dụ:

```text
E445001 raw pointer dereference requires unsafe
E445002 invalid alignment assumption
E445003 FFI ownership contract missing
E445004 unsafe operation outside unsafe context
```

---

## 445.156 — Security annotations

Annotations không thay thế compiler verification.

Chúng chỉ bổ sung contract.

---

## 445.157 — Contract verification

Compiler kiểm tra được những phần machine-checkable.

Phần còn lại thuộc programmer/library contract.

---

## 445.158 — Contract hierarchy

```text
Language invariant
    >
Type invariant
    >
Ownership invariant
    >
API contract
    >
Unsafe contract
    >
External system contract
```

---

## 445.159 — Contract violation

Violation của language invariant trong safe code là compiler error.

Violation unsafe/FFI contract có thể dẫn tới UB.

---

## 445.160 — No hidden UB in safe abstraction

Safe standard API phải encapsulate unsafe internals mà không expose invalid states.

---

## 445.161 — Unsafe implementation behind safe API

Đây là pattern hợp lệ:

```text
safe API
    ↓
validated invariant
    ↓
unsafe optimized implementation
```

---

## 445.162 — Example

`Vec<T>` có thể internally dùng raw pointers/allocator nhưng public operations maintain:

```text
ptr
len
capacity
```

invariants.

---

## 445.163 — Allocator trust

Custom allocator implementations có thể be unsafe if they violate allocator contract.

---

## 445.164 — Global allocator

Global allocator is runtime capability, not language magic.

---

## 445.165 — OOM

OOM handling đã được khóa ở 423/441.

Security model chỉ đảm bảo failure không tự động trở thành memory corruption.

---

## 445.166 — Stack overflow

Stack overflow là runtime/OS failure, không phải ordinary language exception.

---

## 445.167 — Recursion

Compiler không đảm bảo arbitrary recursion luôn safe.

---

## 445.168 — Stack limits

Platform/runtime có thể configure stack sizes.

---

## 445.169 — Guard pages

Runtime/thread backend có thể dùng guard pages nếu target hỗ trợ.

---

## 445.170 — Memory exhaustion

Allocator failure → `Result`/panic/abort theo policy.

---

## 445.171 — Integer truncation

Implicit truncating conversion không được phép.

---

## 445.172 — Explicit truncation

```text
x as u8
```

có semantics rõ ràng.

---

## 445.173 — Checked cast

Library/compiler cung cấp checked conversions khi cần.

---

## 445.174 — Enum cast

Enum-to-integer representation phải tuân layout rules.

---

## 445.175 — Boolean representation

Safe `bool` chỉ có valid representation.

Arbitrary byte → bool là unsafe nếu representation validity không được chứng minh.

---

## 445.176 — Function pointers

Invalid function pointer call là unsafe/UB.

---

## 445.177 — Vtable pointers

`dyn Trait` vtable phải được compiler tạo và quản lý; user không được tự construct valid vtable trong safe code.

---

## 445.178 — Trait object metadata

Trait object metadata không phải arbitrary user data.

---

## 445.179 — Type erasure

Type-erased values phải preserve destruction/alignment/layout metadata cần thiết.

---

## 445.180 — Reflection

Compile-time reflection không tạo runtime attack surface mặc định.

---

## 445.181 — Runtime reflection

Nếu bổ sung, phải là explicit library/runtime capability.

---

## 445.182 — Dynamic loading

Loaded library code không được coi là trusted chỉ vì symbol signature đúng.

---

## 445.183 — Plugin ABI

Plugin interface phải versioned.

---

## 445.184 — Plugin compatibility

ABI hash có thể được dùng để reject incompatible plugins.

---

## 445.185 — Native module isolation

Nếu cần untrusted extension:

```text
process isolation
WASM
sandbox
```

thay vì dựa vào Axiom type system.

---

## 445.186 — Security-sensitive attributes

Compiler phải có registry của attributes ảnh hưởng security:

```text
@unsafe
@no_sanitize
@target_feature
@constant_time
```

---

## 445.187 — `no_sanitize`

Không nên mặc định cho phép user tắt security instrumentation trong safe production profile mà không diagnostic.

---

## 445.188 — Security warnings

Security-relevant unsafe patterns có thể sinh warning/lint.

---

## 445.189 — Lint levels

```text
allow
warn
deny
```

là tooling policy.

---

## 445.190 — CI security mode

Project có thể cấu hình:

```text
deny(unsafe_outside_platform)
deny(unchecked)
deny(missing_ffi_contract)
```

---

## 445.191 — Safe core profile

Một profile có thể cấm toàn bộ unsafe trong application layer.

---

## 445.192 — Kernel profile

Kernel/firmware có thể cho phép unsafe rộng hơn.

---

## 445.193 — Freestanding profile

Không yêu cầu OS sandbox/runtime.

---

## 445.194 — Web profile

WASM sandbox + restricted imports.

---

## 445.195 — Mobile profile

Platform sandbox + restricted capabilities.

---

## 445.196 — Server profile

Native execution + OS capabilities.

---

## 445.197 — Security metadata

Artifact metadata có thể ghi:

```text
unsafe_count
ffi_count
required_capabilities
security_profile
sanitizer_profile
```

---

## 445.198 — AI-readable trust graph

Compiler/toolchain có thể xuất:

```text
Program
 ├── safe
 ├── unsafe
 ├── FFI
 ├── runtime
 ├── OS capability
 └── external dependencies
```

---

## 445.199 — Security architecture

```text
                 Axiom Safe Semantics
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Static Guarantees      Explicit Contracts
              │                     │
              └──────────┬──────────┘
                         ▼
                    Unsafe Boundary
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         FFI             OS         Hardware
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  External Trust
```

---

# 445.200 — Hard invariants

1. Safe và unsafe là hai semantic contexts rõ ràng.
2. Unsafe không tắt toàn bộ compiler checking.
3. Raw pointer dereference cần unsafe.
4. Arbitrary address access cần unsafe.
5. Raw syscall cần unsafe.
6. Inline assembly cần unsafe.
7. MMIO cần unsafe.
8. Executable memory cần explicit unsafe capability.
9. Safe code không được đọc uninitialized typed values.
10. Safe code không được tạo invalid enum/tagged-union states.
11. Safe indexing phải có bounds guarantee.
12. Compiler được phép eliminate bounds checks bằng proof.
13. Raw pointers có thể null.
14. Safe references không có implicit null.
15. Dangling pointer dereference là UB.
16. Double ownership destruction không được xảy ra trong safe code.
17. Move semantics được compiler enforce.
18. Partial initialization được compiler track.
19. Zeroing arbitrary type không mặc định safe.
20. Arbitrary byte-to-type reinterpretation không mặc định safe.
21. Alignment phải được tôn trọng.
22. Misaligned typed access phải explicit.
23. Pointer provenance phải được bảo toàn ở IR khi cần.
24. Integer/pointer conversion là explicit.
25. Pointer ordering không được giả định portable.
26. String invariant UTF-8 phải được bảo vệ.
27. CString và String là hai contracts khác nhau.
28. FFI là trust boundary.
29. FFI ownership phải explicit.
30. FFI layout phải explicit.
31. FFI calling convention phải explicit.
32. FFI unwind boundary phải explicit.
33. Foreign exceptions không tự động trở thành Axiom errors.
34. Safe wrappers có thể encapsulate unsafe implementation.
35. Safe wrappers phải preserve invariants.
36. `Send`/`Share` kiểm soát cross-thread transfer/sharing.
37. Safe shared mutation phải synchronization-aware.
38. Atomic semantics phải được preserve.
39. Deadlock không phải memory-safety guarantee.
40. Resource leak khác memory corruption.
41. Sandbox khác language safety.
42. WASM imports là explicit capabilities.
43. Runtime capability set có thể bị giới hạn.
44. Native executable không mặc định có sandbox.
45. Dynamic libraries không tự động được coi là trusted.
46. Plugin isolation cần process/WASM/OS sandbox khi untrusted.
47. JIT/executable memory là explicit capability.
48. W^X được ưu tiên.
49. Security hardening là build/platform profile.
50. ASLR/NX/CFI/shadow stack là platform/toolchain mechanisms.
51. Compiler không được giả định side-channel đã được loại bỏ.
52. Constant-time là explicit contract.
53. Build scripts khác comptime.
54. Comptime sandbox không có filesystem/network/process mặc định.
55. Dependency provenance phải có thể biểu diễn.
56. Artifact hashes phải deterministic.
57. Bootstrap compiler là trust root.
58. Reproducible bootstrap là validation mechanism.
59. Unsafe inventory phải machine-readable.
60. Security diagnostics phải machine-readable.
61. AI tooling có thể query unsafe/trust/capability graph.
62. Safe code không được phụ thuộc vào undefined behavior.
63. Unsafe code có thể dùng low-level operations nhưng phải explicit.
64. Optimizer vẫn được phép optimize unsafe code dựa trên semantics.
65. Security profile không được âm thầm thay đổi language semantics.
66. Compiler phải phân biệt machine-checkable guarantees và programmer contracts.
67. Standard library phải ưu tiên typed capabilities thay raw integer handles.
68. Native handles phải có ownership semantics.
69. Security-sensitive attributes phải được compiler hiểu.
70. **Axiom security model phải tạo được một safe subset mạnh mà không cần GC hoặc Rust-style global borrow checker.**

**BOOTSTRAP-445 hoàn tất.**

---

# BOOTSTRAP-446 — SOURCE/SEMANTIC METADATA, REFLECTION, DEBUG QUERY, AI TOOLING & MACHINE-READABLE PROGRAM KNOWLEDGE

Đây là task đặc biệt quan trọng đối với mục tiêu Axiom của bạn: **AI phải có thể hiểu và thao tác project mà không cần đọc lại toàn bộ source mỗi lần**.

Axiom sẽ coi semantic metadata là **một artifact chính thức của compiler**, không phải log phụ.

Kiến trúc:

```text
                    Axiom Source
                         │
                         ▼
                 Semantic Database
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Compiler        LSP/IDE        AI Agent
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                 Semantic Metadata
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
   Symbols            Types              Effects
   Layouts            Traits             Ownership
   ABI                Calls              Dependencies
   Diagnostics        Optimization        Security
```

---

## 446.1 — Metadata là semantic artifact

Compiler phải có thể serialize semantic information.

---

## 446.2 — Không thay source

Metadata không thay source code.

Nó là indexed semantic representation của source.

---

## 446.3 — Source hash

Metadata gắn với:

```text
FileId
ContentHash
CompilerVersion
Edition
Target
```

---

## 446.4 — Semantic identity

Symbol identity không phụ thuộc chỉ vào textual name.

---

## 446.5 — Symbol ID

Mỗi declaration có stable semantic ID:

```text
SymbolId
```

---

## 446.6 — Symbol identity

Conceptual:

```text
Package
Module
Declaration
GenericInstance
```

tạo namespace identity.

---

## 446.7 — Type ID

Mỗi canonical type có:

```text
TypeId
```

---

## 446.8 — Type interning

Equivalent canonical types share semantic identity.

---

## 446.9 — Function signature metadata

Metadata chứa:

```text
name
parameters
return_type
generic_parameters
where_constraints
visibility
ABI
effects
```

---

## 446.10 — Struct metadata

```text
Struct {
    fields
    layout
    alignment
    visibility
    traits
}
```

---

## 446.11 — Field metadata

Field:

```text
name
type
offset
size
alignment
visibility
```

---

## 446.12 — Enum metadata

Enum:

```text
variants
discriminator
payload
layout
niche
```

---

## 446.13 — Trait metadata

Trait:

```text
methods
associated_types
associated_constants
supertraits
object_safety
```

---

## 446.14 — Impl metadata

```text
impl Trait for Type
```

được indexed.

---

## 446.15 — Generic metadata

Generic declarations lưu:

```text
type parameters
const parameters
constraints
instances
```

---

## 446.16 — Method resolution metadata

Compiler có thể trả:

```text
receiver
method
selected implementation
trait
dispatch mode
```

---

## 446.17 — Dynamic dispatch metadata

`dyn Trait` ghi:

```text
trait
vtable
methods
object safety
```

---

## 446.18 — Ownership metadata

Function có thể expose:

```text
consumes parameter
borrows parameter
returns owned
returns view
```

---

## 446.19 — Effect metadata

Ví dụ:

```text
allocates
blocks
panics
unsafe
io
thread
async
```

---

## 446.20 — Effect inference

Compiler có thể infer effects nội bộ.

Public metadata có thể expose inferred effects.

---

## 446.21 — Effect stability

Inferred effect changes có thể ảnh hưởng API contract nếu project cấu hình strict effect checking.

---

## 446.22 — ABI metadata

Exported function metadata:

```text
calling_convention
parameter ABI
return ABI
layout
symbol name
```

---

## 446.23 — Target metadata

Metadata ghi target:

```text
arch
os
abi
pointer_width
features
```

---

## 446.24 — Layout metadata

Có thể query:

```text
sizeof<T>
alignof<T>
offsetof<T, field>
```

---

## 446.25 — Dependency graph

Metadata lưu:

```text
module → module
package → package
function → function
type → type
```

---

## 446.26 — Call graph

Compiler có thể export:

```text
caller
callee
dispatch_kind
```

---

## 446.27 — Dynamic call graph

Dynamic dispatch được đánh dấu:

```text
Indirect
DynamicTrait
FunctionPointer
UnknownForeign
```

---

## 446.28 — Security graph

Metadata có thể biểu diễn:

```text
safe
unsafe
ffi
raw_pointer
syscall
assembly
```

---

## 446.29 — Capability graph

Runtime/platform requirements:

```text
filesystem
network
threads
process
dynamic_library
```

---

## 446.30 — Optimization metadata

Compiler có thể lưu:

```text
inlined
vectorized
devirtualized
bounds_check_eliminated
allocation_eliminated
```

---

## 446.31 — Optimization reason

Không chỉ ghi "optimized".

Có thể ghi:

```text
proof
cost_model
profile
target_feature
```

---

## 446.32 — Missed optimization

Metadata có thể lưu:

```text
not_inlined
not_vectorized
not_devirtualized
```

cùng reason.

---

## 446.33 — Source mapping

Semantic IDs map tới:

```text
FileId
line
column
span
```

---

## 446.34 — AST query

AI tooling có thể hỏi:

```text
symbol(id)
references(symbol)
definition(symbol)
```

---

## 446.35 — Semantic query

```text
type_of(expr)
layout_of(type)
trait_impl(trait,type)
```

---

## 446.36 — Dependency query

```text
dependencies(module)
dependents(module)
```

---

## 446.37 — Call query

```text
callers(function)
callees(function)
```

---

## 446.38 — Ownership query

```text
ownership_of(parameter)
return_ownership(function)
```

---

## 446.39 — Effect query

```text
effects(function)
```

---

## 446.40 — Unsafe query

```text
unsafe_sites(function)
```

---

## 446.41 — ABI query

```text
abi(function,target)
```

---

## 446.42 — Layout query

```text
layout(type,target)
```

---

## 446.43 — Optimization query

```text
optimization(function)
```

---

## 446.44 — Diagnostic query

Diagnostics phải có:

```text
code
severity
span
message
related_symbols
fixes
```

---

## 446.45 — Fix-it metadata

Compiler có thể trả machine-readable edit:

```text
file
range
replacement
```

---

## 446.46 — AI code action

AI agent có thể request:

```text
suggest_fix(diagnostic)
```

---

## 446.47 — No arbitrary source rewriting

Compiler code actions phải trả structured edits thay vì opaque natural-language instructions.

---

## 446.48 — Semantic patch

Tooling có thể apply semantic patch:

```text
rename_symbol
change_type
add_import
implement_trait
```

---

## 446.49 — Rename

Rename dùng SymbolId thay textual search.

---

## 446.50 — Reference search

Compiler semantic DB trả tất cả references có thể xác định.

---

## 446.51 — Generated code

Generated declarations phải được đánh dấu:

```text
generated
generator_id
generator_version
source
```

---

## 446.52 — Comptime-generated code

Metadata liên kết generated item với comptime invocation.

---

## 446.53 — Derive-generated code

`derive` output có provenance.

---

## 446.54 — Macro-like generation

Nếu sau này có hygienic generators, metadata phải giữ origin mapping.

---

## 446.55 — Reflection

Axiom ưu tiên compile-time reflection.

---

## 446.56 — Type reflection

Comptime có thể query:

```text
fields<T>()
methods<T>()
variants<T>()
traits<T>()
```

theo reflection API được chuẩn hóa.

---

## 446.57 — Runtime reflection

Không mặc định.

---

## 446.58 — Reflection metadata stripping

Release build có thể loại runtime reflection metadata nếu không sử dụng.

---

## 446.59 — Debug metadata

Debug info và semantic metadata là hai artifacts liên quan nhưng không đồng nhất.

---

## 446.60 — Debug stripping

Release binary có thể bỏ debug info.

Semantic package metadata vẫn có thể được giữ riêng.

---

## 446.61 — Public API metadata

Library distribution nên chứa metadata cần cho consumers mà không cần source.

---

## 446.62 — Private metadata

Private implementation metadata có thể được strip.

---

## 446.63 — API-only artifact

Conceptual:

```text
libfoo.ax
libfoo.axmeta
```

Consumer chỉ cần API metadata + native artifact.

---

## 446.64 — Generic metadata

Nếu generic cần monomorphization phía consumer, metadata phải đủ để instantiate.

---

## 446.65 — Generic implementation privacy

Nếu implementation không được phân phối, library phải cung cấp alternative precompiled generic instances hoặc type-erased interface.

---

## 446.66 — ABI metadata version

Semantic metadata có schema version.

---

## 446.67 — Metadata compatibility

Compiler phải reject metadata schema không tương thích hoặc có migration path.

---

## 446.68 — Semantic hash

Mỗi semantic item có hash dựa trên meaning-relevant inputs.

---

## 446.69 — Semantic hash ≠ source hash

Whitespace/comments có thể thay đổi source hash nhưng không nhất thiết thay semantic hash.

---

## 446.70 — Incremental compilation

Semantic hash giúp compiler xác định item nào thực sự thay đổi.

---

## 446.71 — ABI hash

ABI hash là subset/derivative của semantic information relevant to ABI.

---

## 446.72 — API compatibility

Compiler/package manager có thể compare:

```text
old metadata
new metadata
```

---

## 446.73 — Breaking change detection

Tool có thể báo:

```text
removed symbol
changed signature
changed layout
changed ABI
changed trait requirement
```

---

## 446.74 — Semantic diff

Axiom hỗ trợ:

```text
axiom diff-api old new
```

---

## 446.75 — AI semantic diff

AI tooling có thể query structured API changes thay vì đọc hai source trees.

---

## 446.76 — Source summarization

Compiler metadata có thể cung cấp structural summary.

Không cần compiler tạo natural-language prose mặc định.

---

## 446.77 — Symbol documentation

Documentation comments liên kết với SymbolId.

---

## 446.78 — Documentation metadata

```text
summary
parameters
returns
errors
examples
safety
```

---

## 446.79 — Safety docs

Unsafe functions phải có safety information trong generated documentation.

---

## 446.80 — Effect docs

API docs có thể show:

```text
allocates
blocks
panics
unsafe
```

---

## 446.81 — AI context extraction

Tool:

```text
axiom query-context SymbolId
```

có thể trả context tối thiểu để AI sửa code.

---

## 446.82 — Context minimization

AI query không mặc định dump toàn bộ repository.

---

## 446.83 — Relevant dependency expansion

Agent có thể yêu cầu:

```text
symbol
→ direct dependencies
→ transitive dependencies
```

với depth giới hạn.

---

## 446.84 — Semantic neighborhood

Query có thể trả:

```text
definition
references
callers
callees
related types
traits
tests
```

---

## 446.85 — Test linkage

Test function/file có thể được liên kết với symbols/functions mà nó kiểm tra.

---

## 446.86 — Failure linkage

Test failure có thể trả:

```text
test
source
symbol
diagnostic
stack
artifact
```

---

## 446.87 — Crash linkage

Crash report có thể resolve:

```text
address
→ symbol
→ source span
→ inline stack
```

---

## 446.88 — Optimization linkage

Crash/debug metadata và optimization metadata dùng chung semantic identities.

---

## 446.89 — Binary-to-source query

Nếu debug metadata tồn tại:

```text
binary address
→ source
```

---

## 446.90 — Source-to-binary query

Ngược lại:

```text
source symbol
→ binary address
→ size
→ section
```

---

## 446.91 — Binary size attribution

AI có thể hỏi:

```text
why is binary large?
```

và nhận structured attribution.

---

## 446.92 — Dependency size attribution

Package/module/function-level size attribution nếu linker giữ provenance.

---

## 446.93 — Runtime capability attribution

AI có thể query:

```text
why is filesystem runtime linked?
```

---

## 446.94 — Allocation attribution

Compiler metadata có thể ghi static allocation sites.

---

## 446.95 — Blocking attribution

Blocking call graph có thể được query.

---

## 446.96 — Async attribution

Async state machine metadata liên kết source function với generated state machine.

---

## 446.97 — Closure attribution

Closure generated function/environment có source origin.

---

## 446.98 — Generic attribution

Monomorphized instance:

```text
InstanceKey
→ source generic
→ concrete types
```

---

## 446.99 — Code bloat analysis

AI tooling có thể query:

```text
largest_generic_instances()
largest_functions()
```

---

## 446.100 — Trait dispatch analysis

Có thể hỏi:

```text
why dynamic dispatch?
```

---

## 446.101 — Devirtualization report

Compiler trả:

```text
devirtualized
not_devirtualized
reason
```

---

## 446.102 — Bounds-check report

Compiler trả:

```text
eliminated
retained
reason
```

---

## 446.103 — Allocation report

```text
allocation
stack_promoted
eliminated
retained
reason
```

---

## 446.104 — Vectorization report

```text
vectorized
width
instruction_set
remainder
reason
```

---

## 446.105 — AI optimization workflow

AI agent có thể:

```text
1. query function
2. query hot path
3. query optimization report
4. query missed optimization
5. inspect relevant source only
6. generate patch
7. compile
8. benchmark
9. compare
```

---

## 446.106 — No full-source requirement

Compiler tooling không bắt AI phải parse entire repository nếu semantic DB đã có required information.

---

## 446.107 — Notebook/knowledge integration

Axiom metadata có thể được exported thành machine-readable corpus để external knowledge systems index.

---

## 446.108 — No mandatory external AI

Compiler phải hoạt động hoàn toàn không có AI.

AI integration là tooling consumer.

---

## 446.109 — AI protocol

Axiom có thể cung cấp JSON-RPC/CLI/LSP-compatible semantic queries.

---

## 446.110 — LSP overlap

LSP có thể reuse semantic database.

---

## 446.111 — CLI semantic query

Conceptual:

```text
axiom query symbol Foo
axiom query type Foo
axiom query callers Foo
axiom query layout Foo
```

---

## 446.112 — JSON output

Machine output:

```text
--format=json
```

---

## 446.113 — Stable schema

JSON schema versioned.

---

## 446.114 — Human-readable mode

Default CLI vẫn phải readable.

---

## 446.115 — AI mode

AI tooling dùng stable machine-readable mode.

---

## 446.116 — Query permissions

Tools phải respect package/private visibility.

---

## 446.117 — Private source privacy

Compiler không tự export private implementation metadata nếu package configuration cấm.

---

## 446.118 — Sensitive source metadata

Metadata có thể contain source paths/internal names; distribution policy phải cho phép strip/redact.

---

## 446.119 — Deterministic metadata

Cùng inputs phải produce identical semantic metadata.

---

## 446.120 — Metadata cache

Metadata cache keyed by:

```text
source hash
compiler version
edition
target
dependency semantic hashes
```

---

## 446.121 — Incremental metadata

Chỉ changed semantic items được recomputed.

---

## 446.122 — Query invalidation

Thay đổi declaration invalidates dependent queries.

---

## 446.123 — Query dependency graph

Semantic DB sử dụng cùng query architecture đã khóa ở 436.

---

## 446.124 — Persistent query cache

Compiler daemon có thể persist semantic query results.

---

## 446.125 — Snapshot isolation

LSP/AI queries nhìn thấy compiler snapshot nhất quán.

---

## 446.126 — Concurrent queries

Nhiều AI/IDE clients có thể query semantic database concurrently.

---

## 446.127 — Read-only default

External tooling mặc định chỉ đọc semantic state.

---

## 446.128 — Mutation through compiler actions

Code mutation phải đi qua explicit edit/code-action APIs.

---

## 446.129 — Transactional edits

Một nhóm edits được apply atomically.

---

## 446.130 — Failed edit rollback

Nếu compilation fails unexpectedly, source edits không được partially corrupt.

---

## 446.131 — Symbol rename transaction

Rename across workspace là atomic operation.

---

## 446.132 — Import insertion

Compiler action có thể thêm import đúng namespace.

---

## 446.133 — Trait implementation generation

Tooling có thể generate skeleton:

```text
impl Trait for Type
```

nhưng compiler phải type-check generated result.

---

## 446.134 — Error-driven development

AI agent có thể dùng diagnostics như structured feedback loop.

---

## 446.135 — Build result schema

Build trả:

```text
success
artifacts
diagnostics
warnings
timings
cache_hits
```

---

## 446.136 — Test result schema

Test runner trả:

```text
passed
failed
ignored
duration
stdout
stderr
source
```

---

## 446.137 — Benchmark result schema

Benchmark trả structured measurements.

---

## 446.138 — Artifact result schema

Artifact metadata:

```text
path
kind
target
size
hash
debug_id
abi
capabilities
```

---

## 446.139 — AI build loop

Agent có thể hoạt động:

```text
edit
→ check
→ inspect diagnostics
→ patch
→ test
→ inspect
→ build
```

mà không cần parse terminal prose.

---

## 446.140 — Semantic completion

LSP/AI completion dùng actual type/trait information.

---

## 446.141 — Completion ranking

Ranking có thể dựa trên semantic relevance, không phải arbitrary textual popularity.

---

## 446.142 — Signature help

Compiler biết:

```text
parameter
type
generic constraints
effects
documentation
```

---

## 446.143 — Hover

Hover trả canonical semantic type.

---

## 446.144 — Go-to-definition

Symbol identity-based.

---

## 446.145 — Find references

Semantic identity-based.

---

## 446.146 — Rename

Semantic identity-based.

---

## 446.147 — Refactoring

Compiler-backed refactorings phải preserve semantics hoặc diagnostic nếu không chứng minh được.

---

## 446.148 — Semantic formatting

Formatter không thay đổi semantics.

---

## 446.149 — Generated metadata

Generated metadata phải có source origin để debugger/tooling không bị mất context.

---

## 446.150 — Metadata architecture

```text
                     Compiler Query DB
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     Semantic            Debug              Build
     Metadata             Info              Metadata
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    Tooling Query API
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
         LSP               CLI              AI
```

---

# 446.151 — Hard invariants

1. Semantic metadata là compiler artifact chính thức.
2. Metadata không thay source.
3. Metadata có schema version.
4. Metadata có source/content identity.
5. Symbol identity không phụ thuộc textual name đơn thuần.
6. Type identity được canonicalize.
7. Semantic hashes phải deterministic.
8. ABI metadata phải target-specific.
9. Layout metadata phải target-specific.
10. Ownership metadata có thể query được.
11. Effect metadata có thể query được.
12. Unsafe metadata có thể query được.
13. Dependency graph có thể query được.
14. Call graph có thể query được.
15. Generic instances có thể query được.
16. Trait resolution có thể query được.
17. Optimization decisions có thể query được.
18. Missed optimizations có thể query được.
19. Bounds-check status có thể query được.
20. Allocation elimination có thể query được.
21. Vectorization status có thể query được.
22. Debug mapping dùng semantic identity.
23. Generated code có provenance.
24. Comptime-generated code có provenance.
25. Derive-generated code có provenance.
26. Public API metadata có thể được phân phối mà không cần private source.
27. Generic consumers phải có đủ metadata để instantiate hoặc dùng precompiled instances.
28. API compatibility có thể được kiểm tra bằng metadata.
29. ABI compatibility có thể được kiểm tra bằng metadata.
30. Semantic diff là structured operation.
31. AI không bắt buộc phải đọc toàn bộ source.
32. AI có thể query semantic neighborhood.
33. AI có thể query chỉ phần relevant của dependency graph.
34. AI có thể query unsafe/trust boundaries.
35. AI có thể query runtime capabilities.
36. AI có thể query binary-size attribution.
37. AI có thể query optimization explanations.
38. LSP và AI tooling dùng chung semantic database.
39. CLI có machine-readable output.
40. JSON schema phải versioned.
41. Semantic queries phải respect visibility/privacy.
42. External tooling mặc định read-only.
43. Code mutation phải explicit.
44. Workspace edits có transactional semantics.
45. Failed semantic edits không được corrupt source.
46. Compiler diagnostics là structured data.
47. Build/test/benchmark results là structured data.
48. Artifact metadata có hash/target/kind.
49. Metadata cache dùng content/semantic hashes.
50. Query invalidation phải deterministic.
51. Compiler daemon và LSP phải dùng snapshot isolation.
52. Concurrent semantic queries phải an toàn.
53. Semantic metadata không được tạo runtime overhead nếu không được link.
54. Release binary có thể strip debug/runtime metadata.
55. Compile-time reflection không yêu cầu runtime RTTI.
56. Runtime reflection không mặc định.
57. AI integration không phải language semantic dependency.
58. Axiom compiler vẫn phải hoàn toàn hoạt động khi không có AI.
59. AI tooling không được có quyền tự ý thay đổi source chỉ vì metadata.
60. **Axiom phải trở thành một language/toolchain mà AI có thể hiểu bằng semantic queries thay vì phải liên tục đọc và suy luận lại toàn bộ source tree.**

**BOOTSTRAP-446 hoàn tất.**

---

# BOOTSTRAP-447 — PACKAGE ECOSYSTEM, NATIVE LIBRARY DISTRIBUTION, ABI STABILITY, VERSIONING & DEPENDENCY SUPPLY CHAIN

Bước tiếp theo sẽ khóa phần **Axiom ecosystem**:

```text
Package
   │
   ├── Source
   ├── Semantic Metadata
   ├── Native Artifacts
   ├── ABI Manifest
   ├── Dependencies
   ├── Tests
   └── Provenance
```

Trọng tâm tiếp theo:

- package identity;
- semantic versioning và ABI versioning;
- source package vs binary package;
- `.ax` metadata;
- static/dynamic native artifacts;
- cross-target package distribution;
- dependency resolution;
- lockfile;
- registry/path/git dependency;
- package signing/provenance;
- binary cache;
- precompiled generic instances;
- ABI compatibility;
- API compatibility;
- offline builds;
- vendoring;
- package reproducibility;
- AI-readable package metadata;
- tránh phụ thuộc ecosystem vào compiler bên ngoài.

**BOOTSTRAP-447 là task kế tiếp và chuỗi sẽ tiếp tục tự động theo nguyên tắc đã khóa.**