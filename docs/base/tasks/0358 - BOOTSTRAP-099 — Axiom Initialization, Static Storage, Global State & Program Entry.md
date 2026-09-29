# BOOTSTRAP-099 — Axiom Initialization, Static Storage, Global State & Program Entry

**Trạng thái: FROZEN**

Đây là phần rất quan trọng vì nếu thiết kế sai, Axiom rất dễ rơi vào vấn đề của C/C++: global constructor order, hidden runtime, shutdown order, static initialization race, DLL initialization hell.

Mục tiêu:

> **Global state phải mạnh nhưng không được tạo ra hidden execution model.**

---

## 1. Phân biệt 5 khái niệm

Axiom không gom tất cả vào `global`.

| Khái niệm | Ý nghĩa |
|---|---|
| `const` | Giá trị compile-time |
| `static` | Storage tồn tại cố định |
| `global` | Namespace-level declaration |
| `tls` | Storage riêng cho từng thread |
| `lazy` | Khởi tạo khi được yêu cầu |

Ví dụ:

```axiom
const MAX_USERS: usize = 1000;

static VERSION: Str = "1.0";

static mut counter: Atomic<u64> = Atomic.new(0);

@tls
static thread_buffer: Buffer = Buffer.new(4096);
```

`global` không phải một storage class. Nó chỉ nói rằng declaration nằm ở namespace/module scope.

---

# 2. `const` không phải `static`

Đây là distinction bắt buộc.

```axiom
const PAGE_SIZE: usize = 4096;
```

Compiler có thể thay trực tiếp:

```text
4096
```

vào nơi sử dụng.

Không có requirement rằng phải tồn tại một địa chỉ:

```axiom
address_of(PAGE_SIZE)
```

thậm chí operation này không hợp lệ nếu `PAGE_SIZE` không được materialize.

Trong khi:

```axiom
static PAGE_SIZE: usize = 4096;
```

có **storage identity**.

---

# 3. `static` có storage identity

`static` biểu diễn một object có lifetime thuộc execution domain phù hợp.

Thông thường:

```text
program lifetime
```

Nhưng compiler vẫn được phép tối ưu representation nếu địa chỉ không observable.

Ví dụ:

```axiom
static Answer: i32 = 42;

fn get() -> i32 {
    Answer
}
```

không bắt buộc binary phải thực sự load từ memory.

Nhưng:

```axiom
address_of(Answer)
```

làm địa chỉ trở thành observable và storage contract được giữ.

---

# 4. Static initialization phải chia thành 3 loại

### A. Constant initialization

```axiom
static X: i32 = 42;
```

Được materialize trực tiếp trong binary.

Không chạy code lúc startup.

---

### B. Compile-time initialization

```axiom
static X: Table = comptime {
    build_table()
};
```

`build_table()` chạy trong Comptime.

Runtime không cần thực hiện initialization.

---

### C. Runtime initialization

Chỉ được dùng khi initializer thực sự cần runtime.

```axiom
lazy static CONFIG: Config = load_config();
```

Điểm quan trọng:

> **Axiom không cho phép runtime initializer ngầm chạy chỉ vì module được import.**

---

# 5. Không có global constructor mặc định

Đây là một quyết định lớn.

Axiom **không có cơ chế tương đương C++ global object constructor** kiểu:

```cpp
Foo globalFoo;
```

rồi compiler tự tạo startup code để gọi constructor.

Nếu cần runtime initialization:

```axiom
lazy static foo: Foo = Foo.create();
```

hoặc explicit initialization:

```axiom
fn main() {
    let foo = Foo.create();
    ...
}
```

Như vậy import module không kéo theo execution.

---

# 6. `lazy static`

`lazy` là abstraction library/compiler-supported cho initialization on demand.

```axiom
lazy static registry: Registry = Registry.new();
```

Semantics:

```text
first access
    ↓
check initialized
    ↓
initialize
    ↓
publish value
    ↓
future accesses
```

Initialization phải **thread-safe** nếu object có thể được truy cập concurrently.

Không được phép tạo:

```text
double initialization
data race
partially initialized observation
```

---

# 7. Lazy initialization không đồng nghĩa mutex

Compiler có thể implement bằng:

- atomic state
- once primitive
- lock
- platform-specific initialization
- optimized fast path

Nhưng đây là implementation detail.

Ví dụ:

```axiom
lazy static table: Table = build_table();
```

không có nghĩa programmer phải nhìn thấy:

```text
Mutex<Table>
```

---

# 8. Recursive lazy initialization

Phải được phát hiện.

```axiom
lazy static A: X = {
    B
};

lazy static B: X = {
    A
};
```

Runtime không được deadlock vô hạn mà không có diagnostic/runtime failure semantics rõ ràng.

Axiom quy định:

```text
INITIALIZING → access same initialization dependency
             → initialization cycle
             → deterministic runtime failure
```

Compiler có thể phát hiện cycle nếu dependency statically known.

---

# 9. Mutable global state

Axiom không cấm.

Nhưng phải tuân thủ memory/concurrency model.

Ví dụ:

```axiom
static counter: Atomic<u64> = Atomic.new(0);
```

hợp lệ.

Trong khi:

```axiom
static var counter: u64 = 0;
```

không tự động trở thành thread-safe.

Nếu nhiều threads truy cập mutable global:

```text
Atomic
Mutex
RwLock
Channel
...
```

phải cung cấp synchronization thích hợp.

---

# 10. Global `view` không được phép tùy tiện

Ví dụ:

```axiom
static data: Buffer = ...;

static view_data: view<u8> = view(data);
```

Không nên cho phép như một quy tắc tổng quát vì capability provenance của `view_data` phải gắn với lifetime của `data`.

Với static owner thì lifetime có thể là program lifetime, nhưng compiler phải xử lý đây như một **static capability**, không phải loophole.

Khuyến nghị:

```axiom
static data: Buffer = ...;

fn data_view() -> view<u8> {
    view(data)
}
```

Compiler biết provenance.

---

# 11. TLS

TLS là storage riêng từng execution thread.

```axiom
@tls
static thread_id: usize = 0;
```

Mỗi thread có:

```text
thread A → thread_id[A]
thread B → thread_id[B]
thread C → thread_id[C]
```

Không được coi TLS là shared global.

TLS initialization cũng phải tuân thủ initialization rules.

---

# 12. TLS và async

Đây là điểm cần khóa.

`TLS` thuộc **thread execution domain**, không phải task/future identity.

Vì vậy:

```axiom
async fn foo() {
    ...
}
```

không được hiểu rằng TLS state thuộc về Future.

Nếu Future migrate:

```text
Thread A
   ↓
Future
   ↓ migration
Thread B
```

thì TLS access sau `.await` có thể quan sát TLS của thread B.

Đây là behavior hợp lệ và phải được documented rõ.

Nếu muốn task-local state:

```axiom
TaskLocal<T>
```

phải là abstraction khác.

---

# 13. Program entry

Hosted application:

```axiom
fn main() -> i32 {
    ...
}
```

`main` là entry semantic.

Compiler/linker có thể tạo:

```text
OS startup
    ↓
Axiom startup adapter
    ↓
main()
    ↓
process exit
```

Nhưng adapter chỉ được link nếu target profile cần nó.

---

# 14. `main` không nhất thiết phải trả `i32`

Có thể hỗ trợ:

```axiom
fn main() {
}
```

tương đương exit code thành công.

Và:

```axiom
fn main() -> Result<(), AppError> {
    ...
}
```

runtime/startup layer chuyển `Err` thành process failure theo profile.

Điều này không cần exception runtime.

---

# 15. Freestanding entry

System programming cần bỏ qua hosted startup.

Ví dụ:

```axiom
@entry
fn kernel_entry(info: BootInfo) -> never {
    ...
}
```

Hoặc:

```axiom
@entry
fn _start() -> never {
    ...
}
```

`@entry` thuộc system layer.

Compiler không tự thêm:

- libc startup
- allocator
- thread runtime
- async runtime
- panic runtime

trừ khi profile yêu cầu.

---

# 16. Startup sequence

Axiom định nghĩa startup theo profile.

### Hosted

```text
OS loader
    ↓
platform startup
    ↓
TLS setup
    ↓
runtime components cần thiết
    ↓
main()
```

### Freestanding

```text
OS/firmware/bootloader
    ↓
@entry
```

Không có universal startup runtime.

---

# 17. Shutdown

Đây là nơi Axiom nên khác C++ mạnh nhất.

Không có:

> "Mọi global object phải tự động chạy destructor khi process exit."

Thay vào đó:

### Local owner

Drop deterministic:

```axiom
fn foo() {
    let x = Resource.open();
}
```

ra khỏi scope:

```text
drop(x)
```

---

### Global static

Program-lifetime static không mặc định chạy user-defined destructor tại process exit.

Điều này tránh:

```text
global A destructor
    ↓
global B already destroyed
    ↓
use-after-destruction
```

---

# 18. Nếu cần cleanup khi shutdown

Phải explicit.

Ví dụ:

```axiom
fn main() -> i32 {
    let app = App.start();

    let result = app.run();

    app.shutdown();

    result
}
```

Hoặc system lifecycle API:

```axiom
process.on_exit(cleanup);
```

Nhưng đây là explicit registration và có thứ tự xác định.

Không có "magic destructor registry".

---

# 19. Shared library / DLL initialization

Axiom không cho phép module import tự động tạo constructor execution.

Nếu shared library cần lifecycle:

```axiom
@library_init
fn initialize() -> Result<(), InitError> {
    ...
}
```

và:

```axiom
@library_fini
fn finalize() {
    ...
}
```

là **System ABI contract**, không phải language-level global destructor.

Host platform có thể yêu cầu lifecycle callback.

---

# 20. Initialization ordering

Không có:

```text
file order
import order
link order
```

làm thay đổi initialization semantics.

Nếu:

```text
A depends on B
```

dependency phải được biểu diễn rõ.

Compiler/build system có thể construct dependency graph.

Không được dựa vào:

```text
"module B happens to initialize first"
```

---

# 21. Global state và modules

Import:

```axiom
import foo::registry;
```

**không thực hiện initialization**.

Đây là consequence trực tiếp của AMOD-36/56.

Nếu module có:

```axiom
lazy static registry
```

thì initialization chỉ xảy ra khi semantic access yêu cầu.

---

# 22. Static initialization and comptime

Ưu tiên:

```text
const
 ↓
comptime materialization
 ↓
static constant initialization
 ↓
lazy initialization
 ↓
explicit runtime initialization
```

Tức là compiler nên đẩy initialization lên compile-time khi có thể, nhưng **không được thay đổi observable semantics**.

---

# 23. Global mutable state và ABI

`static` không tự động có symbol public.

Ví dụ:

```axiom
static internal_counter: Atomic<u64>;
```

mặc định private.

Muốn binary symbol:

```axiom
@export("axiom_counter")
pub static counter: Atomic<u64>;
```

Nhưng cần ABI/representation contract phù hợp.

`pub` vẫn khác `@export`.

---

# 24. Static storage và relocation

Compiler/linker được phép đặt static vào:

```text
.rodata
.data
.bss
TLS
platform-specific section
```

tùy semantics.

Ví dụ zero-initialized:

```axiom
static buffer: [u8; 4096] = [0; 4096];
```

không nhất thiết binary phải chứa 4096 zero bytes.

Có thể dùng `.bss`.

---

# 25. Static address

Nếu programmer yêu cầu:

```axiom
address_of(static_value)
```

thì static storage identity trở thành observable.

Compiler/linker phải duy trì contract phù hợp.

Điều này đặc biệt quan trọng cho:

- MMIO
- linker symbols
- shared memory
- FFI
- OS structures
- DMA
- interrupt tables

---

# 26. Initialization failure

`static` constant/comptime initialization không có runtime failure.

`lazy` có thể fail.

Ví dụ:

```axiom
lazy static config: Result<Config, ConfigError> = load_config();
```

hoặc initializer semantics có thể cho phép failure propagation qua API.

Không dùng exception.

---

# 27. Global allocation

Đặc biệt quan trọng:

```axiom
static registry: HashMap<Key, Value>
```

không được phép ngầm kéo toàn bộ allocator/runtime vào chương trình mà programmer không biết.

Nếu initialization/storage cần allocator:

```text
registry
   ↓
allocator dependency
```

phải xuất hiện trong build/runtime dependency graph.

---

# 28. Global state và deterministic builds

Comptime static initialization:

```axiom
static X = comptime generate();
```

phụ thuộc vào:

- source
- comptime dependencies
- compiler semantic version
- target
- configuration
- external inputs

đã thuộc build identity theo BOOTSTRAP-087/097.

Không được để:

```text
current wall-clock time
random environment state
machine-specific state
```

âm thầm thay đổi artifact trong reproducible mode.

---

# 29. Process exit

Process exit là **execution-domain termination**, không phải Drop thông thường.

```axiom
process.exit(0);
```

không được hiểu là:

```text
drop every object in arbitrary order
```

Nếu chương trình cần cleanup quan trọng, phải thực hiện explicit trước exit.

Điều này giúp:

- kernel
- embedded
- CLI
- server
- game
- native app

có semantics rõ ràng.

---

# 30. Panic và process exit

Phân biệt:

```text
return
panic
abort
process.exit
OS termination
```

`panic` theo panic profile có thể unwind hoặc abort.

`process.exit` chủ động terminate process.

Không được biến tất cả thành một mechanism.

---

# 31. Global initialization model hoàn chỉnh

Kiến trúc cuối:

```text
                    ┌──────────────┐
                    │    const     │
                    └──────┬───────┘
                           │
                    compile-time
                           │
                    ┌──────▼───────┐
                    │   comptime   │
                    └──────┬───────┘
                           │
                    materialize
                           │
                    ┌──────▼───────┐
                    │    static    │
                    └──────────────┘


runtime demand
      │
      ▼
 lazy static
      │
      ▼
 deterministic initialization


thread creation
      │
      ▼
     TLS


program entry
      │
      ├── hosted → main
      │
      └── freestanding → @entry
```

Không có hidden global constructor graph.

---

# 32. Compiler implementation

CompilerDB bổ sung:

```text
StaticDB
TlsDB
InitGraphDB
EntryPointDB
ShutdownDB
```

Mỗi static declaration có semantic record:

```text
StaticId
TypeId
Mutability
InitializationKind
StorageDomain
ExecutionDomain
Visibility
ExportContract
AddressObservability
Dependencies
ThreadSafety
DropPolicy
```

---

# 33. Initialization lowering

Semantic:

```axiom
lazy static registry: Registry = Registry.new();
```

↓

HIR:

```text
LazyStatic<Registry>
```

↓

MIR:

```text
LOAD_INIT_STATE
BRANCH initialized / initializing / uninitialized

uninitialized:
    CAS INITIALIZING
    initialize Registry
    PUBLISH
    return

initialized:
    return

initializing:
    wait/failure according to contract
```

↓

ABI MIR / Machine IR

Compiler có thể thay implementation bằng target primitive tương ứng.

---

# 34. Một quyết định quan trọng: không có `global` magic

Tôi đề xuất **không tạo keyword `global` trong Core**.

Ví dụ:

```axiom
global foo: i32
```

không cần thiết.

Chỉ cần:

```axiom
static foo: i32 = 0;
```

Namespace-level declaration tự nhiên đã là global declaration.

Điều này tránh thêm một khái niệm chỉ để phân biệt:

```text
global static
local static
```

trong khi `static` đã đủ semantic information.

---

# 35. Frozen invariants

### Initialization

**AINIT-20** — `const` Has Compile-Time Value Semantics  
**AINIT-21** — `static` Has Storage Identity  
**AINIT-22** — Global Scope Does Not Define A Storage Class  
**AINIT-23** — Static Lifetime Is Explicitly Defined  
**AINIT-24** — Constant Initialization Does Not Require Runtime Execution  
**AINIT-25** — Comptime Initialization Executes Before Runtime  
**AINIT-26** — Runtime Static Initialization Must Be Explicit  
**AINIT-27** — Module Import Does Not Trigger Initialization  
**AINIT-28** — Import Order Does Not Define Initialization Order  
**AINIT-29** — Global Constructors Are Not Implicit  
**AINIT-30** — Global Destructors Are Not Implicit  
**AINIT-31** — Static Initialization Must Be Deterministic  
**AINIT-32** — Lazy Initialization Occurs On Semantic Demand  
**AINIT-33** — Lazy Initialization Is Thread-Safe When Shared  
**AINIT-34** — Recursive Lazy Initialization Is Defined  
**AINIT-35** — Mutable Global State Does Not Imply Synchronization  
**AINIT-36** — Global Mutable Access Must Obey Concurrency Rules  
**AINIT-37** — Static Capability Provenance Is Explicit  
**AINIT-38** — Static Storage May Become Address-Observable  
**AINIT-39** — Address-Observable Static Storage Cannot Be Arbitrarily Relocated  
**AINIT-40** — Static Representation Is Target-Dependent Unless Contracted  
**AINIT-41** — Static Symbols Are Not Automatically Externally Exported  
**AINIT-42** — `pub` Does Not Imply Binary Symbol Export  
**AINIT-43** — `@export` Defines External Symbol Contract  
**AINIT-44** — Static Allocation Does Not Imply Heap Allocation  
**AINIT-45** — Static Initialization Does Not Imply Monolithic Runtime  
**AINIT-46** — Static Initialization Dependencies Are Build-Visible  
**AINIT-47** — Runtime Initialization Failure Is Not An Exception Mechanism  
**AINIT-48** — TLS Has Per-Thread Storage Identity  
**AINIT-49** — TLS Is Distinct From Task-Local Storage  
**AINIT-50** — TLS Does Not Migrate With Async Tasks  
**AINIT-51** — Hosted Entry Is Distinct From Freestanding Entry  
**AINIT-52** — `main` Is A Hosted Entry Convention  
**AINIT-53** — `@entry` Defines Explicit System Entry  
**AINIT-54** — Freestanding Entry Does Not Require Hosted Runtime  
**AINIT-55** — Process Exit Is Distinct From Drop  
**AINIT-56** — Process Exit Does Not Imply Arbitrary Global Destruction  
**AINIT-57** — Explicit Shutdown May Be Used For Required Cleanup  
**AINIT-58** — Shared-Library Initialization Is An ABI/System Contract  
**AINIT-59** — Shared-Library Initialization Does Not Follow Import Semantics  
**AINIT-60** — Initialization Cycles Must Be Diagnosable  
**AINIT-61** — Static Initialization Must Respect Ownership Rules  
**AINIT-62** — Static Initialization Must Respect Capability Rules  
**AINIT-63** — Static Initialization Must Respect Send/Share Rules  
**AINIT-64** — Static Initialization Must Respect Comptime Dependency Rules  
**AINIT-65** — Unused Static Initialization Must Not Be Emitted Without Semantic Need  
**AINIT-66** — Linker Dead-Stripping May Remove Unobservable Static State  
**AINIT-67** — Address-Observable Static State Is A Linker Root  
**AINIT-68** — TLS Initialization Is Target-Specific At ABI Lowering  
**AINIT-69** — Static Storage May Use `.rodata`, `.data`, `.bss`, TLS Or Equivalent Sections  
**AINIT-70** — Zero Initialization Need Not Occupy Binary File Space  
**AINIT-71** — Global State Must Not Create Hidden Thread Execution  
**AINIT-72** — Global State Must Not Create Hidden Async Execution  
**AINIT-73** — Global State Must Not Create Hidden Allocator Dependency  
**AINIT-74** — Global State Must Not Create Hidden Synchronization  
**AINIT-75** — Global Initialization Must Remain Compatible With Freestanding Builds  
**AINIT-76** — Initialization Semantics Are Independent Of Link Order  
**AINIT-77** — Initialization Semantics Are Independent Of Filesystem Order  
**AINIT-78** — Shutdown Semantics Are Independent Of Destruction Order Of Unrelated Globals  
**AINIT-79** — Runtime Resources Require Explicit Lifecycle Contracts  
**AINIT-80** — Initialization Is A Semantic Property Before Code Generation  

**BOOTSTRAP-099: FROZEN.**

---

# BOOTSTRAP-100 — Axiom Package/Module Initialization Boundary & Runtime Dependency Elimination

Task kế tiếp nên xử lý một vấn đề liên quan trực tiếp 099:

> **Làm thế nào compiler xác định chính xác runtime nào thực sự cần được link vào executable?**

Đây là bước để biến các nguyên tắc "no hidden runtime / no hidden allocation / no hidden thread / no hidden async" thành **một cơ chế dependency elimination hoàn chỉnh**.

Ta sẽ khóa:

```text
Runtime Capability Graph
Runtime Component Discovery
Dead Runtime Elimination
Panic Runtime
Allocator Runtime
Thread Runtime
Async Runtime
TLS Runtime
Unwind Runtime
GPU Runtime
Reflection Runtime
Startup Runtime
FFI Runtime
Freestanding Runtime
```

và đặc biệt là:

```text
Axiom source
   ↓
semantic dependencies
   ↓
runtime capability graph
   ↓
minimal runtime closure
   ↓
link only required components
   ↓
dead component elimination
   ↓
small native binary
```

Điều này sẽ nối trực tiếp **BOOTSTRAP-099 → runtime architecture → linker → binary-size goal** mà Axiom đang hướng tới.