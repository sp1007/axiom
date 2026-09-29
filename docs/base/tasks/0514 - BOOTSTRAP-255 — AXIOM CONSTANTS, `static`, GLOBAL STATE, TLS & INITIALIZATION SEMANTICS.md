# BOOTSTRAP-255 — AXIOM CONSTANTS, `static`, GLOBAL STATE, TLS & INITIALIZATION SEMANTICS

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần quan trọng vì nó hoàn thiện mô hình **storage lifetime** của Axiom:

```text
compile-time
    ↓
const
    ↓
local
    ↓
static
    ↓
TLS
    ↓
process / program lifetime
```

Mục tiêu là có global state mạnh như C/C++, nhưng **không tạo ra hidden initialization order, hidden runtime, hidden locks hoặc GC-like machinery**.

---

# 1. Quyết định kiến trúc trung tâm

Axiom phân biệt rõ:

```text
const
static
TLS
local
```

Chúng **không phải các biến thể syntax của cùng một khái niệm**.

### `const`

Giá trị compile-time.

```axiom
const MAX_SIZE: usize = 1024
```

Không phải mutable storage.

### `static`

Một storage location có identity ổn định trong suốt lifetime của chương trình/module theo contract.

```axiom
static VERSION: Str = "1.0"
```

### TLS

Một storage instance riêng cho mỗi thread.

```axiom
static thread_local COUNTER: Atomic<u64>
```

### local

Storage lifetime được quản lý theo scope/ownership.

---

# 2. `const` không phải `static`

```axiom
const X: i32 = 42
```

không đảm bảo có địa chỉ runtime.

Compiler có thể:

```text
X
↓
immediate 42
```

hoặc materialize thành storage nếu ABI/API yêu cầu.

---

# 3. `static` có identity

```axiom
static X: i32 = 42
```

khác:

```text
const X: i32 = 42
```

vì `static` có semantic storage identity.

---

# 4. `static` có thể có địa chỉ

Nếu system API cần:

```text
address_of(X)
```

thì `X` phải có stable storage contract.

---

# 5. `const` có thể được duplicate

Ví dụ:

```axiom
const BUFFER_SIZE: usize = 4096
```

compiler có thể inline ở mọi nơi.

Không tạo storage bắt buộc.

---

# 6. `static` không được mặc định Copy semantics

Một static storage location không phải một ordinary local value.

Access vào static tạo value/capability theo loại access.

---

# 7. Read-only static

Ví dụ:

```axiom
static PI: f64 = 3.141592653589793
```

có thể được đọc nhiều nơi.

---

# 8. Mutable static

Axiom cho phép mutable global state nhưng **không cho phép safe unsynchronized mutation**.

Ví dụ conceptual:

```axiom
static mut COUNTER: i32 = 0
```

access mutable phải thuộc system/unsafe boundary.

---

# 9. Vì sao?

Nếu:

```text
Thread A → write COUNTER
Thread B → write COUNTER
```

mà không synchronization:

→ data race.

Axiom safe core không cho phép.

---

# 10. Khuyến nghị cho safe global mutation

Dùng:

```axiom
static COUNTER: Atomic<i32>
```

hoặc:

```axiom
static STATE: Mutex<State>
```

---

# 11. Global state không bị cấm

Axiom không theo triết lý:

> global state luôn xấu.

Thay vào đó:

> global state phải có semantics rõ ràng.

---

# 12. `static Atomic`

```axiom
static COUNTER: Atomic<u64> = Atomic(0)
```

là một storage location dùng atomic semantics.

---

# 13. Atomic global

Nhiều thread có thể:

```text
fetch_add
load
store
compare_exchange
```

theo memory model.

---

# 14. `static Mutex`

```axiom
static CONFIG: Mutex<Config> = Mutex(...)
```

safe mutation thông qua guard:

```text
lock
 ↓
mut_view
 ↓
modify
 ↓
Drop guard
 ↓
unlock
```

---

# 15. Global Mutex không cần runtime registry

Một static mutex là object bình thường trong static storage.

Không cần:

```text
global_mutex_registry
```

---

# 16. `static` initialization

Axiom chia initialization thành:

```text
Constant Initialization
Dynamic Initialization
Lazy Initialization
```

---

# 17. Constant initialization

Nếu initializer có thể evaluate hoàn toàn tại compile time:

```axiom
static TABLE_SIZE: usize = 1024 * 4
```

→ static image có thể chứa trực tiếp giá trị.

Không cần startup code.

---

# 18. Comptime static initialization

```axiom
static TABLE: [256]u8 = comptime make_table()
```

Compiler chạy `make_table` trong comptime environment.

Kết quả được materialize vào binary.

---

# 19. Đây là preferred global initialization

Mục tiêu:

```text
static initialization
→ data section
```

thay vì:

```text
program startup
→ execute constructor
```

---

# 20. Dynamic static initialization

Nếu:

```axiom
static CONFIG: Config = load_config()
```

thì initializer cần runtime execution.

Axiom **không cho phép hidden arbitrary global constructors**.

---

# 21. Quyết định

Dynamic global initialization phải sử dụng **explicit lazy initialization** hoặc explicit startup registration.

Không có C++-style:

```text
global constructors magically run
```

mà không có dependency semantics rõ ràng.

---

# 22. Lazy initialization

Library có thể cung cấp:

```text
Lazy<T>
Once<T>
OnceLock<T>
```

Conceptually:

```axiom
static CONFIG: Lazy<Config> = Lazy(...)
```

và:

```text
CONFIG.get_or_init(...)
```

---

# 23. Lazy là library abstraction

Không cần Core keyword:

```text
lazy
```

---

# 24. Lazy initialization và concurrency

`Lazy<T>` phải có synchronization semantics.

Hai thread đồng thời gọi:

```text
get_or_init()
```

không được tạo hai giá trị nếu contract yêu cầu exactly-once initialization.

---

# 25. Failed initialization

Nếu initializer trả:

```text
Result<T,E>
```

thì library quyết định semantics:

```text
retry
poison
cache error
```

Không phải Core rule.

---

# 26. Panic during initialization

Lazy abstraction phải định nghĩa:

```text
initialized
initializing
failed
poisoned
```

nếu cần.

---

# 27. Core không định nghĩa global constructor order

Không có:

```text
A constructor before B constructor
```

dựa trên file order.

---

# 28. Cross-module static dependencies

Ví dụ:

```text
module A
static A

module B
static B = use(A)
```

Nếu `A` là constant-initialized:

→ OK.

Nếu A dynamic-initialized:

→ không được tự động chạy trước B.

---

# 29. Cách đúng

Dùng explicit:

```text
init()
```

hoặc:

```text
Lazy
Once
```

---

# 30. Vì sao?

Tránh dependency graph ẩn.

---

# 31. Global initialization graph

Compiler có thể phân tích:

```text
A → B → C
```

nhưng không tự tạo semantics “magic constructor ordering”.

---

# 32. Explicit startup

Application có thể:

```axiom
fn main() -> Result<(), Error> {
    init_database()?
    init_network()?
    run()
}
```

Rõ ràng và deterministic.

---

# 33. Startup registration

Frameworks có thể cần registration.

Thay vì hidden constructor:

```text
@startup
fn register_plugin()
```

có thể tồn tại ở system/application layer.

Nhưng:

> registration order phải được định nghĩa và không được phụ thuộc source/link order.

---

# 34. Nếu registration cần dependency

Metadata phải biểu diễn dependency:

```text
startup A
requires B
```

Compiler/linker tạo deterministic order.

---

# 35. Nhưng không phải Core global initializer

Đây là distinction quan trọng.

---

# 36. Static Drop

Static có process lifetime.

Do đó static Drop semantics phải được định nghĩa rõ.

Axiom **không yêu cầu tất cả static Drop chạy khi process kết thúc**.

---

# 37. Vì sao?

Operating system sẽ reclaim process memory/resources.

Ngoài ra static destructors có thể tạo:

```text
shutdown-order dependency
```

rất khó kiểm soát.

---

# 38. Quyết định

Static values có Drop:

- không mặc định yêu cầu process-exit destructor;
- system/library có thể explicit shutdown;
- runtime profile có thể opt-in shutdown cleanup.

---

# 39. Ví dụ

```axiom
static LOGGER: Logger = ...
```

Application có thể:

```axiom
logger.shutdown()
```

trước khi exit nếu flush/close cần thiết.

---

# 40. Không có "static destructor magic"

Axiom tránh:

```text
program exits
→ random reverse global destructor order
```

---

# 41. Freestanding

Trong freestanding/kernel:

```text
static
```

phải hoạt động mà không cần runtime.

---

# 42. Static data

Có thể nằm trong:

```text
.rodata
.data
.bss
```

theo object writer.

---

# 43. Zero-initialized static

```axiom
static BUFFER: [4096]u8 = zeroed()
```

có thể map vào BSS nếu representation phù hợp.

Không nhất thiết lưu 4096 bytes trong binary.

---

# 44. `const` vs `static` example

```axiom
const SIZE: usize = 4096
static BUFFER: [SIZE]u8 = zeroed()
```

`SIZE` có thể disappear hoàn toàn.

`BUFFER` vẫn là storage.

---

# 45. Static address identity

Hai static:

```axiom
static A: i32 = 1
static B: i32 = 1
```

không được compiler merge nếu observable identity khác nhau.

---

# 46. Constant merging

Hai `const`:

```text
A = 42
B = 42
```

có thể trở thành cùng immediate value.

---

# 47. Static deduplication

Compiler chỉ merge static storage nếu:

```text
semantic identity
address observability
mutability
ABI
FFI
```

cho phép.

---

# 48. Static exported symbol

Nếu:

```axiom
@export
pub static VERSION: ...
```

thì binary symbol/address có thể observable.

Compiler phải giữ storage.

---

# 49. FFI global

C global:

```c
extern int errno;
```

không tự biến thành Axiom static.

FFI declaration phải mô tả:

```text
ABI
type
mutability
TLS
ownership
representation
```

---

# 50. External static

Conceptual:

```axiom
extern "C" {
    static mut errno: i32
}
```

access mutable phải obey FFI/system/unsafe rules.

---

# 51. TLS

TLS là storage:

```text
one instance / execution thread
```

---

# 52. TLS ≠ static

```text
static X
```

→ một process/module storage location.

```text
thread_local X
```

→ mỗi thread một instance.

---

# 53. TLS identity

Hai threads:

```text
Thread A → X
Thread B → X
```

có cùng semantic declaration nhưng khác physical storage instances.

---

# 54. TLS address

Address của TLS variable khác theo thread.

Do đó:

```text
storage identity
```

phụ thuộc execution context.

---

# 55. TLS initialization

Constant-initialized TLS:

```text
TLS image/template
```

có thể được OS/runtime tạo khi thread starts.

---

# 56. Dynamic TLS initialization

Nếu cần runtime initialization:

→ explicit TLS lazy abstraction preferred.

Không hidden arbitrary constructor.

---

# 57. TLS Drop

Giống static:

Axiom không bắt buộc arbitrary TLS destructors.

Platform/runtime profile có thể hỗ trợ explicit TLS cleanup.

---

# 58. Vì sao?

TLS destructor order trên các platform khác nhau phức tạp.

Axiom không đưa platform quirks vào Core semantics.

---

# 59. Thread-local synchronization

TLS không cần lock nếu thread thực sự sở hữu riêng storage.

Nhưng TLS value có thể chứa `Arc`, shared resources etc.

Normal Send/Share rules vẫn áp dụng khi values escape.

---

# 60. TLS escape

Nếu lấy address/handle tới TLS và gửi sang thread khác:

→ capability/storage contract phải reject nếu không valid.

---

# 61. TLS view

Một `view<T>` vào TLS không tự nhiên Send.

Provenance bao gồm:

```text
TLS instance
+
Thread identity
```

---

# 62. Thread termination

TLS values thuộc thread.

Nếu runtime/platform cung cấp cleanup:

→ cleanup theo TLS contract.

Nếu không:

→ OS/thread teardown semantics.

---

# 63. Global mutable capability

Không được:

```text
static mut
→ safe mut_view
```

mà không synchronization.

---

# 64. Global immutable view

Read-only static:

```text
static DATA: [u8; ...]
```

có thể tạo:

```text
view<u8>
```

với program-lifetime provenance.

---

# 65. Static view lifetime

Vì static sống program lifetime:

```text
static
→ view
```

có thể có lifetime tương ứng program lifetime.

Không cần lifetime annotation.

---

# 66. Returning static view

```axiom
fn data() -> view<u8> {
    view(DATA)
}
```

hợp lệ nếu static read capability.

---

# 67. Local view vs static view

Local:

```text
view(local)
```

không thể escape local lifetime.

Static:

```text
view(static)
```

có thể escape tới program lifetime.

---

# 68. Global mutable access

Nếu static được protected bởi Mutex:

```text
static STATE: Mutex<State>
```

then:

```text
let guard = STATE.lock()
```

tạo exclusive capability.

---

# 69. Guard Drop

```text
scope exit
→ drop guard
→ unlock
```

không cần defer.

---

# 70. Static and effects

Access mutable global state tạo effect:

```text
GlobalRead
GlobalWrite
Atomic
Synchronization
```

trong compiler EffectInfo.

---

# 71. Pure functions

Một function đọc mutable global:

```text
static CONFIG
```

không thể được coi pure nếu global state có thể thay đổi.

---

# 72. Optimizer

Compiler không được CSE/hoist global reads nếu global state có thể be invalidated.

---

# 73. Atomic globals

Atomic load/store effects obey memory ordering.

---

# 74. FFI global

Compiler phải coi unknown foreign global mutation conservatively.

---

# 75. Volatile global

System layer có thể:

```text
volatile_load
volatile_store
```

Không được optimize away.

---

# 76. MMIO

Memory-mapped device register có thể được biểu diễn bằng system-layer storage abstraction.

Không cần global variable special case.

---

# 77. `const` and effects

Compile-time constants không tạo runtime effect.

---

# 78. Comptime

```axiom
const TABLE = comptime generate()
```

generation xảy ra compiler-side.

Runtime access chỉ đọc materialized value.

---

# 79. Comptime external dependency

Nếu `comptime` đọc filesystem:

→ build fingerprint phải bao gồm dependency.

---

# 80. Static generated by comptime

Ví dụ:

```axiom
static LUT: [1024]f32 = comptime make_lut()
```

Compiler tạo static data.

Không cần runtime initialization.

---

# 81. Generated declaration

`comptime` có thể generate static declarations thông qua typed generation/derive mechanism.

Generated declaration quay lại:

```text
resolve
→ typecheck
→ ownership
→ layout
→ ABI
```

---

# 82. Static generic

Generic declarations không nhất thiết tạo storage cho mọi instantiation.

Chỉ những instance được dùng/reachable cần materialize.

---

# 83. Monomorphization

Ví dụ:

```text
static<T> ...
```

nếu generic static được cho phép, mỗi concrete instance có semantic identity riêng.

Tuy nhiên để tránh complexity, Core v1 **không cần generic mutable global storage** như một primitive.

Library wrappers có thể model bằng generic types.

---

# 84. `static` inside generic function

Không tạo một static mới cho mỗi function invocation.

Nếu generic instance được instantiate:

```text
one static per concrete instantiation
```

chỉ khi language feature explicitly cho phép.

---

# 85. Better v1 rule

`static` declarations chỉ ở module/package scope.

Không có function-local static Core v1.

---

# 86. Vì sao?

Function-local static tạo:

```text
identity
initialization
thread safety
visibility
lifetime
```

complexity không cần thiết.

Library `Lazy<T>` giải quyết nhu cầu này.

---

# 87. Static visibility

Có thể:

```axiom
pub static VERSION: ...
```

hoặc private.

Visibility semantics giống declarations khác.

---

# 88. Module static

Private static chỉ module sử dụng.

---

# 89. Package static

`pub(package)`.

---

# 90. Stable ABI static

Nếu public ABI:

```text
@abi(stable)
@export
pub static ...
```

representation/address contract phải rõ.

---

# 91. Stable ABI and mutable static

Stable ABI mutable globals rất khó versioning.

Axiom khuyến nghị opaque accessor functions:

```text
get_state()
set_state()
```

thay vì exposing raw global layout.

Đây là ABI guidance, không phải semantic prohibition.

---

# 92. Static layout

Default compiler-controlled.

Nếu FFI:

```text
@repr(C)
```

nếu cần.

---

# 93. Static alignment

Theo type layout.

System layer có:

```text
@align(N)
```

---

# 94. Static section

Compiler/linker quyết định:

```text
.rodata
.data
.bss
.tls
custom sections
```

dựa semantic properties.

---

# 95. Linker roots

Static được giữ nếu:

```text
referenced
exported
FFI-visible
reflection-retained
startup registration
linker keep
```

---

# 96. Unused static

Nếu:

```text
static UNUSED = ...
```

không observable:

→ linker/compiler có thể eliminate.

---

# 97. Static with address identity

Nếu address observable through API:

→ storage retained.

---

# 98. Static and section GC

Dead-section elimination không được loại bỏ static có semantic external identity.

---

# 99. Static initialization graph

Compiler/build system có thể represent:

```text
StaticInitNode
```

nhưng Core chỉ cho phép:

```text
constant initialization
```

hoặc explicit lazy/startup mechanisms.

---

# 100. Initialization purity

Constant initialization phải là:

```text
comptime-evaluable
```

và không có runtime external effects.

---

# 101. Forbidden constant initializer

Ví dụ:

```axiom
const X = read_file("x")
```

nếu filesystem capability không được phép.

---

# 102. Const capability

`const` evaluation tuân thủ Comptime capability model.

---

# 103. Runtime static initializer and filesystem

Nếu muốn:

```text
CONFIG = read_file(...)
```

phải explicit runtime function.

Không hidden global constructor.

---

# 104. Startup runtime

Runtime profile có thể expose:

```text
startup hooks
```

nhưng executable dependency graph phải thể hiện chúng.

---

# 105. Freestanding startup

Kernel/embedded có thể define:

```text
@entry
fn kernel_main(...)
```

và initialize static memory explicitly/platform-defined.

---

# 106. No mandatory `main`

Freestanding profile không cần hosted `main`.

---

# 107. Process startup

Hosted executable:

```text
OS
 ↓
Axiom startup
 ↓
runtime initialization
 ↓
main
```

Runtime components only linked when needed.

---

# 108. Static before main

Constant static data đã sẵn sàng.

Explicit runtime initialization components có defined order.

Không có arbitrary module constructor race.

---

# 109. Exit

Program termination không phụ thuộc static destructor chain.

---

# 110. Explicit shutdown

Applications needing deterministic global cleanup should expose:

```axiom
fn shutdown() -> Result<(), Error>
```

và gọi explicit.

---

# 111. Library unload

Dynamic library static state lifetime follows library lifetime contract.

Không được giả định process lifetime nếu library unload được.

---

# 112. Plugin static state

Plugin may own:

```text
static registry
```

nhưng unload contract phải ensure no live capabilities/symbols/resources refer to plugin state.

---

# 113. Dynamic loading

Static storage inside shared library belongs to loaded module instance.

Unload invalidates addresses.

Compiler/FFI capability model phải bảo vệ references.

---

# 114. TLS in dynamic library

TLS instance is per thread per loaded module.

Platform details remain target-specific.

---

# 115. TLS and dynamic unload

Cannot unload library while TLS/resource references remain live according to ABI contract.

---

# 116. Static and `Arc`

Static can contain:

```text
Arc<T>
```

but Arc semantics remain ordinary.

---

# 117. Static Drop of Arc

If static storage remains until process/module lifetime, reference count release happens according to explicit static lifecycle policy.

No GC.

---

# 118. Static cycles

Static initialization cycles are not automatically solved.

Prefer:

```text
Lazy
explicit initialization
```

---

# 119. `Lazy` cycle

If:

```text
A.get() → B.get()
B.get() → A.get()
```

library must detect/reject/define behavior.

Core does not magically solve it.

---

# 120. Thread-local lazy cycle

Same.

---

# 121. Static dependency diagnostics

Compiler can explain:

```text
static initialization cannot depend on runtime value
```

or:

```text
dynamic initialization requires explicit Lazy/Startup mechanism
```

---

# 122. Example

Invalid conceptual code:

```axiom
static A: AType = make_a()
```

if `make_a()` requires runtime IO.

Diagnostic:

```text
ASTATIC-E001
static initializer is not compile-time evaluable
```

Suggested semantic alternatives:

```text
Lazy<AType>
```

or explicit startup initialization.

---

# 123. Global state and purity

Compiler should expose:

```text
reads_global
writes_global
reads_tls
writes_tls
```

in Explain API.

---

# 124. AI tooling

AI can query:

```text
ax explain global STATE
```

and receive:

```text
storage: Static
mutability: Mutable
synchronization: Mutex
initialization: Constant
drop: ProgramLifetime
ABI: Internal
```

---

# 125. CompilerDB additions

```text
StaticDB
TlsDB
GlobalInitDB
GlobalAccessDB
StartupDB
ShutdownDB
```

---

# 126. IDs

```text
StaticId
TlsId
GlobalStorageId
InitNodeId
StartupHookId
ShutdownHookId
```

---

# 127. Global storage metadata

Conceptual:

```text
GlobalStorage {
    declaration
    storage_kind
    mutability
    initialization_kind
    lifetime
    representation
    alignment
    visibility
    abi
    address_observable
    thread_local
    effects
}
```

---

# 128. Storage kinds

```text
CONST
STATIC
TLS
EXTERNAL_STATIC
DEVICE_STATIC
```

`DEVICE_STATIC` can remain system/GPU-specific.

---

# 129. Compiler analysis

Global accesses feed:

```text
EffectInfo
AliasInfo
EscapeInfo
ConcurrencyInfo
ABI
LinkerRoots
```

---

# 130. Global aliasing

A read-only static may have many views.

Mutable static requires exclusive/synchronized access.

---

# 131. Global `view`

Program-lifetime read capability:

```text
static DATA
    ↓
view(DATA)
```

can safely be shared if immutable.

---

# 132. Global `mut_view`

Not implicitly available for mutable static.

Requires valid synchronization/exclusive access.

---

# 133. Atomic ≠ mutable view

```text
Atomic<T>
```

cannot be converted to:

```text
mut_view<T>
```

because that would bypass atomic semantics.

---

# 134. Mutex guard ≠ ordinary reference

Guard provides exclusive capability while lock is held.

Drop releases synchronization.

---

# 135. TLS and Send

TLS value cannot simply be “sent” by address.

To transfer data, move the actual value or use explicit shared storage.

---

# 136. TLS and Share

A TLS storage location itself is not inherently Share because instances are execution-context-specific.

---

# 137. Static immutable data and Share

Immutable program-lifetime data can satisfy Share if its type semantics permit.

---

# 138. Global mutable data and Share

`static mut` does not imply Share.

---

# 139. Global synchronization

Safe global mutable state patterns:

```text
Atomic<T>
Mutex<T>
RwLock<T>
Channel
Once<T>
Lazy<T>
```

all library/system abstractions.

---

# 140. No global runtime lock

Axiom must not automatically lock every mutable global.

That would destroy performance and predictability.

---

# 141. Global state performance

Compiler knows exact synchronization.

It can optimize:

```text
TLS access
atomic load
mutex path
```

according to target.

---

# 142. TLS optimization

Compiler may optimize TLS access using platform TLS ABI.

---

# 143. Static access optimization

Immutable static may become immediate/constant if address identity is not observable.

---

# 144. Mutable static

Cannot be constant-folded across possible writes unless compiler proves no invalidation.

---

# 145. Whole-program analysis

LTO may prove:

```text
static X
never modified
```

and optimize reads.

But only if all relevant external/FFI/reflection access is accounted for.

---

# 146. Dynamic linking

External module can mutate exported symbol.

Therefore compiler must retain conservative assumptions across ABI boundaries.

---

# 147. FFI visibility

`@export static` makes mutation potentially observable externally.

---

# 148. Reflection

Runtime reflection can make declarations reachable.

Metadata roots must preserve retained statics where requested.

---

# 149. Comptime reflection

Does not itself imply runtime storage.

---

# 150. Static serialization

Static values can be serialized by ordinary library code.

No special Core serializer.

---

# 151. Static address serialization

Raw addresses must not be serialized as persistent identity.

Use logical identifiers.

---

# 152. Static and ASLR

Runtime virtual address may change between processes.

Semantic static identity is not numeric address identity across executions.

---

# 153. Security

Secrets should not be exposed as ordinary immutable static data if binary inspection is a concern.

Crypto/security library can use secure storage abstractions.

---

# 154. Read-only secret static

Even `.rodata` may be observable from binary.

This is an application/security concern, not Core semantics.

---

# 155. Constant-time

Global secret access must preserve constant-time contracts when annotated.

---

# 156. GPU globals

GPU constant memory/static device data is separate storage domain.

Explicit GPU annotations/representations.

---

# 157. Device static

Axiom should not imply CPU static automatically exists on GPU.

Host/device storage domains remain distinct.

---

# 158. WASM

WASM linear-memory globals and Axiom static storage require target lowering.

Axiom semantic static identity remains separate from machine address.

---

# 159. Embedded

Static is particularly important:

```text
.rodata
.data
.bss
```

with no OS/runtime requirement.

---

# 160. Kernel

Kernel static storage may map to kernel image sections or explicitly allocated memory.

No mandatory user-space assumptions.

---

# 161. Initialization in kernel

Only constant/static image initialization by default.

Runtime subsystem can define explicit initialization phases.

---

# 162. Multiple executables

Each executable has its own static storage instance.

---

# 163. Shared library

Each loaded module instance has its own static storage unless platform semantics explicitly provide process-shared external storage.

---

# 164. Fork

Process semantics are platform-specific.

Axiom static semantics are inherited according to OS process model, not a Core-level clone abstraction.

---

# 165. `exec`

New process image → new static/TLS storage.

---

# 166. Thread spawn

New thread → new TLS instances.

Ordinary static storage remains shared.

---

# 167. TLS initialization inheritance

Platform-specific; Axiom library/system layer defines supported semantics.

---

# 168. Global ownership

Static owner is not owned by a lexical scope.

Its ownership domain is program/module lifetime.

---

# 169. Static Drop capability

A static resource can have a lifetime contract longer than all ordinary locals.

---

# 170. No `static` ownership transfer

Cannot:

```text
return static_resource
```

as if transferring ownership of the static itself.

Can return a view/handle/copy/explicit ownership wrapper according to type.

---

# 171. Static resource access

Example:

```text
static GLOBAL_SOCKET: Mutex<Option<Socket>>
```

Socket ownership remains inside global state.

---

# 172. Take from static

Can explicitly move value out of an initialized mutable container:

```text
Mutex<Option<T>>
```

with synchronization.

Then static container remains.

---

# 173. This is preferred to static ownership mutation

Global slot abstraction handles optional ownership.

---

# 174. Global `Option`

```text
static STATE: Mutex<Option<State>>
```

supports:

```text
Some
None
take
replace
```

without null.

---

# 175. No null global

Core still has no null.

---

# 176. Function-local state alternative

If user wants one lazily initialized value:

```text
static VALUE: Lazy<T>
```

rather than function-local static.

---

# 177. Why this is simpler

One visible declaration has:

```text
identity
visibility
initialization
storage
```

instead of hidden declaration generated by function semantics.

---

# 178. Global initialization and package graph

Package dependencies do not imply initialization order.

---

# 179. Module imports

`use` imports declarations, not runtime initialization actions.

---

# 180. This is crucial

```text
use package::foo
```

does not mean:

```text
execute foo's global constructors
```

---

# 181. Binary dependency graph

Linking a library does not automatically execute arbitrary package-level initialization.

---

# 182. Startup components

If library needs startup:

```text
StartupContract
```

must be explicit.

---

# 183. Runtime minimality

A program containing only:

```axiom
const
static readonly
```

may require zero runtime initialization code.

---

# 184. Example minimal binary

```axiom
const MAGIC: u32 = 123

static MESSAGE: Str = "hello"

fn main() {
    print(MESSAGE)
}
```

Only required IO/runtime components should link.

---

# 185. No hidden global constructor runtime

This directly supports Axiom's binary-size goal.

---

# 186. Global access and compiler barriers

Normal static access is not automatically a compiler barrier.

Atomic/volatile/synchronization semantics determine ordering.

---

# 187. Global ordinary mutable state

If safe access is mediated through a Mutex, compiler sees synchronization through guard operations.

---

# 188. FFI unknown global

Compiler assumes potentially mutable/external effects.

---

# 189. Interprocedural analysis

LTO can propagate global access facts.

---

# 190. Global constant propagation

If immutable static has no externally observable address and value is known:

```text
load static
```

may become:

```text
constant
```

---

# 191. Address-observable exception

If address escapes:

```text
address_of(static)
```

compiler retains storage identity.

---

# 192. Raw address is unsafe

`address_of` is system/unsafe.

But compiler must still respect its observable identity once used.

---

# 193. Stable static ABI

If static is exported through C ABI:

```text
@export
@repr(C)
```

representation/address contract becomes part of ABI fingerprint.

---

# 194. TLS ABI

Stable TLS exports require target-specific ABI support.

Not all foreign ABIs support arbitrary Axiom TLS semantics.

---

# 195. Static symbol mangling

Internal static names can use deterministic Axiom mangling.

Exported names use explicit `@export("name")`.

---

# 196. Linker

Static sections participate in:

```text
dead strip
ICF
section GC
relocation
TLS layout
```

according to observability.

---

# 197. Compiler tests

Need test classes:

```text
const evaluation
static initialization
static identity
static elimination
static address observation
mutable static safety
atomic static
mutex static
TLS isolation
TLS Send/Share
FFI globals
dynamic loading
startup hooks
shutdown
freestanding
WASM
GPU/device static
```

---

# 198. Formal semantics

Static variable semantic state:

```text
StaticCell {
    declaration
    initialized
    storage_identity
    value
}
```

TLS:

```text
TlsCell {
    declaration
    execution_instance
    initialized
    storage_identity
    value
}
```

---

# 199. `const` semantic state

```text
ConstValue {
    type
    compile_time_value
}
```

No storage identity.

---

# 200. Core rule

> **`const` denotes a compile-time value. `static` denotes program/module-lifetime storage. TLS denotes execution-context-lifetime storage.**

---

# 201. Frozen invariants

```text
AGLOBAL-20
`const` denotes a compile-time value.

AGLOBAL-21
A `const` does not require runtime storage.

AGLOBAL-22
A compiler may materialize a const when required by ABI or observable semantics.

AGLOBAL-23
`static` denotes a storage location with explicit lifetime semantics.

AGLOBAL-24
Static storage identity is distinct from const value identity.

AGLOBAL-25
Static storage does not require heap allocation.

AGLOBAL-26
Static storage does not require garbage collection.

AGLOBAL-27
Static storage does not require a monolithic runtime.

AGLOBAL-28
Static layout is compiler-controlled unless an explicit representation/ABI contract exists.

AGLOBAL-29
Static address identity is preserved when address observability is part of the semantic contract.

AGLOBAL-30
Unobservable immutable static storage may be folded into constants.

AGLOBAL-31
Mutable static state is not implicitly safe for concurrent mutation.

AGLOBAL-32
Unsafe mutable static access cannot bypass the Axiom memory model.

AGLOBAL-33
Safe mutable global state requires an appropriate synchronization abstraction.

AGLOBAL-34
Atomic static state obeys ordinary Axiom atomic semantics.

AGLOBAL-35
Mutex-protected static state obeys ordinary mutex capability semantics.

AGLOBAL-36
Atomic<T> cannot implicitly become mut_view<T>.

AGLOBAL-37
A static read-only value may produce a long-lived read capability when provenance permits.

AGLOBAL-38
A static owner cannot be implicitly moved out of static storage.

AGLOBAL-39
Global ownership is distinct from lexical local ownership.

AGLOBAL-40
Static values are not ordinary lexical locals.

AGLOBAL-41
Static declarations are module/package-level in Core v1.

AGLOBAL-42
Core v1 does not require function-local static storage.

AGLOBAL-43
Lazy function-local state is expressible using explicit library abstractions.

AGLOBAL-44
Constant static initialization requires a compile-time-valid initializer.

AGLOBAL-45
Constant static initialization does not require runtime startup code.

AGLOBAL-46
Comptime-generated static data may be materialized directly into the binary.

AGLOBAL-47
Comptime static generation obeys comptime capability restrictions.

AGLOBAL-48
Comptime execution cannot silently acquire runtime capabilities.

AGLOBAL-49
Arbitrary runtime IO is not permitted in constant initialization.

AGLOBAL-50
Arbitrary dynamic global constructors are not implicit Core semantics.

AGLOBAL-51
Runtime-dependent global initialization requires an explicit mechanism.

AGLOBAL-52
Lazy initialization is a library abstraction.

AGLOBAL-53
Lazy initialization must define its concurrency semantics.

AGLOBAL-54
Lazy initialization must define failure semantics.

AGLOBAL-55
Lazy initialization cycles are not implicitly resolved by the language.

AGLOBAL-56
Package import does not imply runtime global initialization.

AGLOBAL-57
Module import does not imply arbitrary constructor execution.

AGLOBAL-58
Global initialization order cannot depend on source-file order.

AGLOBAL-59
Global initialization order cannot depend on linker input order.

AGLOBAL-60
Dynamic initialization dependencies must be explicit.

AGLOBAL-61
Explicit startup initialization may be provided by system/application layers.

AGLOBAL-62
Startup dependencies must be represented explicitly when ordering matters.

AGLOBAL-63
Startup execution order must be deterministic.

AGLOBAL-64
Static initialization does not require a universal constructor registry.

AGLOBAL-65
Static Drop does not imply mandatory process-exit destructor execution.

AGLOBAL-66
Core v1 does not require arbitrary static destructors at process exit.

AGLOBAL-67
Applications may perform explicit global shutdown.

AGLOBAL-68
Runtime profiles may provide optional shutdown facilities.

AGLOBAL-69
Static Drop semantics must not create an implicit global destruction-order dependency.

AGLOBAL-70
Static resources may have process or module lifetime.

AGLOBAL-71
Static resource cleanup remains subject to its explicit resource contract.

AGLOBAL-72
Static Drop is distinct from process termination.

AGLOBAL-73
Explicit abort-like termination may bypass ordinary static cleanup.

AGLOBAL-74
TLS denotes storage with an execution-context-specific instance.

AGLOBAL-75
TLS is distinct from ordinary static storage.

AGLOBAL-76
Each supported thread receives a distinct TLS storage instance.

AGLOBAL-77
TLS access does not imply shared mutable storage.

AGLOBAL-78
TLS access obeys ordinary ownership and capability rules.

AGLOBAL-79
A TLS capability cannot outlive its TLS execution context.

AGLOBAL-80
A TLS address cannot implicitly become a valid cross-thread capability.

AGLOBAL-81
TLS values do not automatically become Send merely because the declaration is TLS.

AGLOBAL-82
TLS values do not automatically become Share.

AGLOBAL-83
TLS initialization may use constant initialization.

AGLOBAL-84
Dynamic TLS initialization requires an explicit supported mechanism.

AGLOBAL-85
Core v1 does not require arbitrary TLS constructor execution.

AGLOBAL-86
Core v1 does not require arbitrary TLS destructor execution.

AGLOBAL-87
Platform TLS behavior may be exposed through system-layer contracts.

AGLOBAL-88
TLS ABI is target-specific.

AGLOBAL-89
Dynamic-library TLS follows the platform/module lifetime contract.

AGLOBAL-90
A dynamically unloaded module cannot leave valid Axiom capabilities pointing into unloaded static/TLS storage.

AGLOBAL-91
External static declarations require explicit FFI contracts.

AGLOBAL-92
Foreign static representation is not inferred solely from source type syntax.

AGLOBAL-93
Foreign mutable globals are conservative synchronization boundaries.

AGLOBAL-94
FFI global access contributes appropriate effects.

AGLOBAL-95
Volatile global access remains observable.

AGLOBAL-96
Atomic global access follows atomic ordering semantics.

AGLOBAL-97
Ordinary global reads are not automatically compiler barriers.

AGLOBAL-98
Global writes cannot be reordered across synchronization when forbidden by the memory model.

AGLOBAL-99
Global state contributes to effect analysis.

AGLOBAL-100
Global state contributes to alias analysis.

AGLOBAL-101
Global state contributes to concurrency analysis.

AGLOBAL-102
LTO may optimize global state only when all relevant observability conditions are proven.

AGLOBAL-103
Externally visible globals remain optimization roots.

AGLOBAL-104
Reflection-retained globals remain optimization roots when requested.

AGLOBAL-105
Exported globals have explicit symbol identity.

AGLOBAL-106
Exported global representation is part of ABI when stable ABI is declared.

AGLOBAL-107
Static ABI compatibility is independent of source visibility.

AGLOBAL-108
TLS ABI compatibility is target- and platform-dependent.

AGLOBAL-109
Static section placement is a linker concern.

AGLOBAL-110
Static section placement does not change semantic storage identity.

AGLOBAL-111
Read-only statics may reside in read-only sections.

AGLOBAL-112
Zero-initialized statics may use BSS-like representation.

AGLOBAL-113
TLS statics may use platform TLS sections.

AGLOBAL-114
Unused statics may be eliminated when no observable identity remains.

AGLOBAL-115
Address-observable statics cannot be eliminated.

AGLOBAL-116
Static merging is legal only when semantic identity remains preserved.

AGLOBAL-117
Const merging is generally permitted because const has no required storage identity.

AGLOBAL-118
Static storage is not automatically heap storage.

AGLOBAL-119
Static storage is not automatically process-global across dynamic-library instances.

AGLOBAL-120
Module lifetime and process lifetime are distinct concepts.

AGLOBAL-121
Dynamic library lifetime may be shorter than process lifetime.

AGLOBAL-122
Capabilities into dynamic-library static storage cannot outlive the module contract.

AGLOBAL-123
Freestanding programs may use static storage without a hosted runtime.

AGLOBAL-124
Kernel and embedded profiles may define explicit static initialization contracts.

AGLOBAL-125
Freestanding execution does not require a universal global constructor mechanism.

AGLOBAL-126
WASM global/storage lowering is target-specific.

AGLOBAL-127
Axiom semantic static identity is distinct from a numeric WASM linear-memory address.

AGLOBAL-128
GPU/device static storage is a separate storage-domain concern.

AGLOBAL-129
CPU static storage does not implicitly become GPU storage.

AGLOBAL-130
Device static resources require explicit GPU/system contracts.

AGLOBAL-131
Static values may be serialized through ordinary serialization abstractions.

AGLOBAL-132
Static addresses are not persistent logical identities.

AGLOBAL-133
Global cryptographic secrets do not gain security merely by being static.

AGLOBAL-134
Secure global storage requires explicit security-library contracts.

AGLOBAL-135
Global constant-time requirements remain subject to the constant-time subsystem.

AGLOBAL-136
Static initialization is part of the build dependency graph when external inputs are involved.

AGLOBAL-137
Comptime external dependencies contribute to build identity.

AGLOBAL-138
Static initialization must be deterministic under reproducible-build mode.

AGLOBAL-139
Global initialization diagnostics must identify the initialization mechanism.

AGLOBAL-140
The compiler must distinguish constant, lazy, explicit-startup, and unsupported dynamic initialization.

AGLOBAL-141
Unknown global initialization behavior is not treated as constant initialization.

AGLOBAL-142
AI tooling may inspect global storage and initialization facts.

AGLOBAL-143
AI tooling cannot override global safety verification.

AGLOBAL-144
Global state semantics are independent of optimization level.

AGLOBAL-145
Global state semantics are independent of section placement.

AGLOBAL-146
Global state semantics are independent of linker implementation.

AGLOBAL-147
Global state semantics are independent of allocator implementation.

AGLOBAL-148
Global state semantics are independent of runtime composition unless an explicit runtime contract is selected.

AGLOBAL-149
The semantic distinction between const, static, and TLS is preserved through MIR.

AGLOBAL-150
Global storage facts are available to ABI lowering and linker stages.

AGLOBAL-151
Global storage facts are available to debugger/source mapping.

AGLOBAL-152
Global initialization is covered by conformance testing.

AGLOBAL-153
Global concurrency behavior is covered by concurrency testing.

AGLOBAL-154
Global FFI behavior is covered by ABI testing.

AGLOBAL-155
Global behavior is covered by freestanding and cross-target testing.

AGLOBAL-156
Global storage behavior is covered by dynamic-linking tests.

AGLOBAL-157
Global storage behavior is covered by reproducible-build tests.

AGLOBAL-158
No safe global mutable access may introduce a data race.

AGLOBAL-159
No global initialization mechanism may silently introduce an unspecified dependency order.

AGLOBAL-160
No static storage operation may implicitly require garbage collection.

AGLOBAL-161
No static storage operation may implicitly require heap allocation.

AGLOBAL-162
No TLS operation may implicitly require a monolithic runtime.

AGLOBAL-163
No global mechanism may silently introduce a hidden synchronization cost.

AGLOBAL-164
No global mechanism may silently introduce process-exit destructor ordering.

AGLOBAL-165
The programmer-visible global model remains explicit while compiler implementation may optimize aggressively.
```

---

## 202. Storage model của Axiom giờ đã hoàn chỉnh hơn

Có thể nhìn toàn bộ hệ thống như sau:

```text
                    STORAGE LIFETIME
                          │
          ┌───────────────┼────────────────┐
          │               │                │
       COMPTIME         RUNTIME          EXTERNAL
          │               │                │
        const       ┌─────┼─────┐       FFI/device
                    │     │     │
                  local static  TLS
                    │     │     │
                  scope  process thread
                    │
                  Drop
```

Trong đó:

```text
const
```

không có storage identity bắt buộc,

còn:

```text
local / static / TLS
```

có các **storage domains khác nhau**, nhưng tất cả vẫn dùng chung:

```text
Ownership
Capability
Drop
Effect
Send/Share
ABI
Escape
```

Đây là một điểm rất quan trọng của thiết kế Axiom: **không cần tạo một hệ thống quản lý memory riêng cho global, TLS, heap, stack và generator**. Chúng chỉ khác nhau ở storage/lifetime contract.

---

# BOOTSTRAP-256 tiếp theo

Bây giờ một mảnh cực kỳ quan trọng còn lại là:

## **AXIOM MEMORY ACCESS, LOAD/STORE, ATOMIC/VOLATILE & MEMORY ORDERING LOWERING**

Tức là đi xuống gần machine semantics hơn:

```text
value
 ↓
place
 ↓
address
 ↓
load/store
 ↓
atomic load/store/RMW
 ↓
volatile
 ↓
fence
 ↓
alias/provenance
 ↓
machine memory operation
```

Đặc biệt cần chốt **`Place` model và LValue/RValue** thành một semantic memory model hoàn chỉnh, bao gồm:

- field projection;
- array indexing;
- slice;
- dereference raw pointer;
- `view`/`mut_view`;
- load/store;
- unaligned access;
- volatile;
- atomic;
- memory barriers;
- address calculation;
- pointer provenance;
- aliasing;
- partial initialization;
- `MaybeUninit`;
- MMIO;
- DMA;
- memory-mapped files;
- GPU address spaces.

Đây gần như là **cầu nối cuối cùng từ Axiom type/ownership system xuống machine code**.