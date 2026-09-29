# BOOTSTRAP-137 — Effect System, Side Effects & Function Purity Model

**Trạng thái: FROZEN / COMPLETED**

Đây là lớp còn thiếu để compiler trả lời chính xác:

> **Một function có thể làm gì với thế giới bên ngoài?**

Và quan trọng hơn: **programmer không phải viết `pure`, `readonly`, `noexcept`, `const`, `noalias`... chỉ để giúp optimizer.** Compiler tự suy luận phần lớn.

---

## 1. Nguyên tắc thiết kế

Axiom phân biệt:

```text
Type        → function nhận/trả cái gì
Capability  → function được access vùng nào
Effect      → function có thể gây tác động gì
Ownership   → function sở hữu/chuyển cái gì
```

Ví dụ:

```ax
fn sum(a: view<i32>, b: view<i32>) -> i32
```

có thể được compiler suy ra:

```text
READ
NO_ALLOC
NO_DROP_OBSERVABLE
NO_IO
NO_SYNC
NO_PANIC        // nếu proof được
```

Trong khi:

```ax
fn save(path: Str, data: view<u8>) -> Result<unit, Error>
```

có:

```text
READ
IO
WRITE_EXTERNAL
ALLOC?           // tùy implementation
```

---

# 2. Effect không phải một keyword

Không bắt programmer viết:

```ax
pure fn sum(...)
```

hay:

```ax
readonly fn foo(...)
```

Compiler tự derive:

```text
EffectSummary(sum)
```

Annotation chỉ tồn tại khi muốn **đặt một semantic contract mà compiler không thể tự suy ra**.

---

# 3. EffectSet

Mỗi function có:

```text
EffectSet {
    Read
    Write
    Allocate
    Deallocate
    Drop
    Atomic
    Volatile
    IO
    Synchronize
    Panic
    Foreign
    GPU
    Suspend
    ExternalState
}
```

Có thể mở rộng sau này mà không thay đổi mô hình cơ bản.

---

# 4. `Read`

Function đọc dữ liệu:

```ax
fn length(x: view<u8>) -> usize
```

có:

```text
READ
```

Read có thể kèm region:

```text
READ(R1)
READ(R2)
```

---

# 5. `Write`

Ví dụ:

```ax
fn clear(x: mut_view<u8>)
```

có:

```text
WRITE(R)
```

Compiler kết hợp EffectInfo với AliasInfo để biết write ảnh hưởng những read nào.

---

# 6. `Allocate`

Function có thể tạo storage:

```ax
fn make_buffer(n: usize) -> Buffer
```

có:

```text
ALLOCATE
```

Nhưng:

> `ALLOCATE` là semantic possibility, không có nghĩa runtime chắc chắn gọi heap allocator.

Optimizer có thể biến:

```text
allocate → stack
```

hoặc:

```text
allocate → registers
```

nếu semantics cho phép.

---

# 7. `Deallocate`

Resource release:

```text
DEALLOCATE
```

thường xuất hiện trong Drop glue hoặc explicit resource operations.

Không đồng nghĩa với `free()` vật lý.

---

# 8. `Drop`

Một function có thể trigger destructor:

```text
DROP(T)
```

Effect này quan trọng vì destructor có thể:

- release resource;
- synchronize;
- IO;
- panic;
- gọi foreign code.

Vì vậy compiler không được coi Drop là “nothing”.

---

# 9. `Atomic`

Atomic operation:

```ax
counter.fetch_add(1, Relaxed)
```

có:

```text
ATOMIC
WRITE
```

và ordering metadata:

```text
Relaxed
```

hoặc:

```text
Acquire
Release
AcqRel
SeqCst
```

---

# 10. `Volatile`

```ax
volatile_read(addr)
```

có:

```text
VOLATILE
```

Volatile không phải Atomic.

Axiom tuyệt đối không được coi:

```text
VOLATILE == ATOMIC
```

---

# 11. `IO`

Ví dụ:

```ax
file.read(...)
socket.send(...)
console.write(...)
```

có:

```text
IO
```

IO là observable effect.

Compiler không được:

- loại bỏ;
- duplicate;
- reorder bất hợp lệ;
- CSE như ordinary pure computation.

---

# 12. `Synchronize`

Ví dụ:

```ax
mutex.lock()
channel.send(x)
thread.join()
```

có synchronization effect.

Synchronization không đơn giản là memory write.

---

# 13. `Panic`

Function có thể panic:

```ax
fn index(...)
```

nếu bounds không được đảm bảo.

Effect:

```text
PANIC
```

Nếu compiler chứng minh mọi path không panic:

```text
PANIC
```

có thể được loại khỏi specialized path.

---

# 14. `Foreign`

```ax
extern "C" fn foo(...)
```

có:

```text
FOREIGN
```

nếu compiler không biết contract.

Foreign call mặc định conservative:

```text
READ *
WRITE *
UNKNOWN
FOREIGN
```

theo khả năng mà ABI/contract cho phép.

---

# 15. `Suspend`

Async:

```ax
async fn download(...)
```

có:

```text
SUSPEND
```

vì function có thể chuyển execution state qua await.

---

# 16. `GPU`

Kernel:

```ax
@kernel
fn add(...)
```

có execution/storage-domain effects riêng:

```text
GPU
READ(DeviceRegion)
WRITE(DeviceRegion)
```

Không được nhầm với CPU memory effects.

---

# 17. Effect graph

Effect của function được derive từ body.

Ví dụ:

```ax
fn outer(x: T) {
    inner(x);
}
```

Nếu:

```text
inner = READ + ALLOCATE
```

thì:

```text
outer = READ + ALLOCATE
```

trừ khi optimizer/compiler chứng minh một effect không observable ở context đó.

---

# 18. Interprocedural effect inference

Compiler xây graph:

```text
outer
 ├── foo
 │    └── bar
 └── baz
```

Sau đó propagate:

```text
bar → foo → outer
```

Effect inference cần hỗ trợ:

- recursion;
- mutual recursion;
- generic instances;
- dynamic dispatch;
- FFI.

---

# 19. Recursive functions

Ví dụ:

```ax
fn a() {
    b();
}

fn b() {
    a();
}
```

Compiler dùng fixed-point:

```text
Effect(a) = Effect(b)
Effect(b) = Effect(a)
```

Khởi đầu bằng conservative approximation, sau đó refine.

---

# 20. Generic functions

```ax
fn apply<T>(x: T, f: fn(T) -> T) -> T
```

Effect của generic function có thể phụ thuộc vào:

```text
T
callee
trait implementation
```

Ví dụ một trait method:

```text
Trait::process
```

có thể có effect khác nhau giữa concrete implementations.

---

# 21. Static dispatch

Với:

```ax
fn foo<T: Process>(x: T)
```

khi compiler biết:

```text
T = MyType
```

có thể resolve:

```text
Process::process<MyType>
```

và lấy effect summary chính xác.

Đây là một lý do static dispatch có lợi cho optimization.

---

# 22. Dynamic dispatch

Với:

```ax
dyn Process
```

compiler chưa biết implementation cụ thể.

Effect phải là conservative union của các target có thể gọi:

```text
Effect(dyn call)
    = union(candidate effects)
```

Nếu runtime type set được narrow:

```text
EffectSet
```

cũng được narrow.

---

# 23. Closure

Closure effect là effect của body cộng effect của captured accesses.

Ví dụ:

```ax
let f = || x + 1;
```

nếu `x` chỉ READ:

```text
READ(x)
```

Nếu closure gọi IO:

```text
IO
```

Nếu closure mutate captured state:

```text
WRITE(R)
```

---

# 24. Closure capture + alias

EffectInfo phải phối hợp với AliasInfo:

```text
closure
  ↓
captured region
  ↓
READ/WRITE
```

Điều này đặc biệt quan trọng khi closure được:

- inlined;
- moved;
- spawned;
- passed to another function.

---

# 25. Effect và capability

Ví dụ:

```ax
fn increment(x: mut_view<i32>)
```

compiler derive:

```text
WRITE(provenance(x))
```

Không cần annotation:

```text
@writes(x)
```

---

# 26. Effect và ownership

Function:

```ax
fn consume(x: T)
```

có semantic ownership transfer:

```text
MOVE(x)
```

Nhưng `MOVE` không nhất thiết là effect memory write.

Do đó:

```text
Ownership effect
```

và:

```text
Memory effect
```

phải tách.

---

# 27. Read-only function

Axiom không cần keyword `readonly`.

Compiler có thể xác định:

```text
READ only
```

nhưng điều đó không có nghĩa function là mathematical pure.

Ví dụ:

```ax
fn get_time() -> Time
```

có thể không WRITE memory nhưng vẫn:

```text
TIME
EXTERNAL_STATE
```

và không pure.

---

# 28. Pure không phải chỉ “không write”

Đây là điểm quan trọng.

Một function:

```ax
fn random() -> u64
```

không write visible program memory nhưng có:

```text
RANDOM
EXTERNAL_STATE
```

nên không phải pure.

---

# 29. Observable effect model

Axiom định nghĩa effect dựa trên **observable semantics**, không chỉ memory mutation.

Các nguồn observable state gồm:

```text
Memory
IO
Time
Random
Environment
Process
Synchronization
Foreign state
Device state
```

---

# 30. Compiler-known pure

Compiler có thể xác định một function là:

```text
PURE
```

khi:

```text
no IO
no external state
no synchronization
no volatile
no foreign unknown effect
no observable allocation identity
no observable panic
```

và kết quả chỉ phụ thuộc input/compile-time state hợp lệ.

---

# 31. Pure không cần keyword

Ví dụ:

```ax
fn square(x: f64) -> f64 {
    x * x
}
```

Compiler tự suy ra:

```text
PURE
```

---

# 32. Pure không đồng nghĩa constant

```ax
fn square(x: f64)
```

có thể pure nhưng vẫn runtime.

Trong khi:

```ax
comptime square(4)
```

là compile-time execution.

Hai khái niệm độc lập:

```text
PURE ≠ COMPTIME
```

---

# 33. Const function

`comptime fn` có guarantee mạnh hơn:

```text
COMPTIME_EXECUTABLE
```

Nhưng một function runtime vẫn có thể được optimizer constant-fold nếu input constant.

---

# 34. Effect polymorphism

Axiom v0.1 **không nên bắt programmer viết effect generic syntax** kiểu:

```text
fn foo<E: Effect>(...)
```

Compiler tự propagate effect.

Điều này giữ surface language đơn giản.

---

# 35. Effect specialization

Ví dụ generic:

```ax
fn map<T, F>(...)
```

với một closure pure:

```text
Effect(F) = PURE
```

compiler có thể tạo specialization:

```text
map<T, PureClosure>
```

và tối ưu mạnh hơn.

---

# 36. Effect-driven optimization

Nếu function:

```text
PURE + NO_PANIC
```

compiler có thể:

- CSE;
- GVN;
- constant fold;
- common subexpression reuse;
- hoist;
- eliminate duplicate calls;
- inline aggressively.

---

# 37. READ-only optimization

Nếu:

```text
foo = READ(R)
```

và không có:

```text
WRITE(R)
```

giữa hai calls:

```ax
let a = foo(x);
let b = foo(x);
```

compiler có thể reuse kết quả nếu các effect khác cũng không observable.

---

# 38. WRITE invalidation

Alias + Effect phối hợp:

```text
foo:
    READ(R)

bar:
    WRITE(R)
```

thì:

```text
foo()
bar()
foo()
```

không được CSE hai `foo()` nếu `bar` có thể thay đổi `R`.

---

# 39. Call invalidation chính xác

Không dùng kiểu:

```text
CALL → clobber all memory
```

trừ khi call thực sự unknown.

Nếu compiler biết:

```text
bar:
    WRITE(R2)
```

thì `READ(R1)` vẫn có thể được giữ nếu:

```text
R1 DISJOINT R2
```

Đây chính là:

```text
AliasInfo + EffectInfo
```

---

# 40. Allocation effect và optimization

Ví dụ:

```ax
fn make() -> Box<Point>
```

semantic effect:

```text
ALLOCATE
```

nhưng nếu Box không escape:

```text
NoEscape
```

optimizer có thể:

```text
heap allocation
      ↓
stack
      ↓
SSA
```

và effect vật lý biến mất.

---

# 41. Allocation identity

Ngược lại nếu programmer có thể quan sát identity:

```ax
let a = Box::new(x);
let b = Box::new(x);
compare_identity(a, b);
```

compiler không được merge hai allocations chỉ vì giá trị giống nhau.

Effect system và identity analysis phối hợp.

---

# 42. Drop effect

Ví dụ:

```ax
{
    let f = File::open(...);
}
```

compiler phải biết Drop của `File` có:

```text
IO
```

hoặc resource release effect.

Không được coi:

```text
DROP(File)
```

là trivial.

---

# 43. Trivial Drop

Nếu:

```ax
struct Point {
    x: i32,
    y: i32
}
```

không có Drop:

```text
DROP(Point) = no observable effect
```

compiler có thể erase cleanup hoàn toàn.

---

# 44. Panic effect

Một function có:

```text
PANIC
```

không nhất thiết phải generate runtime panic machinery nếu build profile là:

```text
panic = abort
```

Effect semantics vẫn tồn tại; backend quyết định representation.

---

# 45. `Result` và effect

```ax
fn parse(x: Str) -> Result<T, Error>
```

không tự động có `PANIC`.

Recoverable failure là **giá trị**:

```text
Result
```

không phải implicit effect.

---

# 46. `?`

```ax
let x = parse(input)?;
```

`?` tạo control flow:

```text
Err → return
Ok  → continue
```

Không biến function thành exception-based effect.

---

# 47. Error effect

Axiom không cần:

```text
THROWS
```

trong function signature để biểu diễn `Result`.

Do đó:

```text
Result<T,E>
```

là type semantics.

```text
PANIC
```

mới là effect.

---

# 48. Time / Random / Environment

Các effect này nên được phân biệt:

```text
TIME
RANDOM
ENVIRONMENT
PROCESS
```

Ví dụ:

```ax
fn now() -> Time
```

không pure dù không mutate ordinary memory.

---

# 49. Deterministic mode

Build/test có thể yêu cầu:

```text
deterministic
```

Compiler/runtime có thể reject hoặc virtualize:

```text
TIME
RANDOM
ENVIRONMENT
```

tùy capability.

Điều này nối trực tiếp với Comptime sandbox đã frozen.

---

# 50. Effect contracts

Compiler tự derive là mặc định.

Annotation chỉ dùng cho trường hợp:

```text
semantic external contract
```

Ví dụ FFI:

```ax
@ffi_contract(...)
extern "C" fn foo(...)
```

Contract trở thành input của verifier/effect/alias analysis.

---

# 51. Programmer không được giả mạo pure

Không cho:

```ax
@pure
fn evil() {
    write_global();
}
```

và compiler tin annotation.

Nếu annotation là **semantic assertion**, compiler phải verify hoặc reject.

Unsafe cũng không được biến một function thành pure bằng lời tuyên bố.

---

# 52. Trusted effect boundary

Một số primitive compiler/platform có thể là trusted:

```text
syscall
atomic intrinsic
volatile intrinsic
GPU intrinsic
FFI boundary
```

Chúng phải khai báo effect metadata trong compiler/system layer.

---

# 53. Effect inference algorithm

Pipeline:

```text
MIR
 ↓
Local Effect Collection
 ↓
Call Graph
 ↓
Interprocedural Fixed Point
 ↓
Capability/Region Refinement
 ↓
Alias Refinement
 ↓
EffectSummary
```

---

# 54. Local effect collection

Compiler scan MIR:

```text
Load       → READ
Store      → WRITE
Alloc      → ALLOCATE
Drop       → DROP
Atomic     → ATOMIC
Volatile   → VOLATILE
Call       → callee effects
Await      → SUSPEND
Foreign    → FOREIGN
```

---

# 55. Effect summary structure

Đề xuất:

```text
EffectSummary {
    effects: EffectSet

    reads: RegionSet
    writes: RegionSet

    allocations: AllocationEffect
    synchronization: SyncEffect
    panic: PanicEffect
    suspension: SuspensionEffect

    external_state: ExternalStateSet

    provenance: EffectOrigin
}
```

---

# 56. Effect lattice

Mỗi effect analysis dùng monotonic refinement:

```text
UNKNOWN
   ↓
CONSERVATIVE_EFFECTS
   ↓
PRECISE_EFFECTS
```

Compiler chỉ loại effect khi có proof.

Không được tự ý suy:

```text
UNKNOWN → PURE
```

---

# 57. Effect summary và dynamic dispatch

Nếu:

```text
dyn Trait
```

có nhiều implementations:

```text
E1
E2
E3
```

thì:

```text
E_dynamic = E1 ∪ E2 ∪ E3
```

Sau devirtualization:

```text
E_dynamic
   ↓
E_concrete
```

và optimizer có thêm thông tin.

---

# 58. Effect + inlining

Inlining không thay đổi semantic effects.

Nó chỉ làm effect information cụ thể hơn tại call site.

Ví dụ:

```text
foo()
```

ban đầu:

```text
READ R
WRITE S
```

Sau inline:

```text
READ R
WRITE S
```

nhưng AliasInfo có thể xác định chính xác hơn region.

---

# 59. Effect + LTO

LTO có thể mở rộng call graph qua package/object boundary nếu metadata cho phép.

Nhưng:

> Effect semantics không được phụ thuộc vào việc bật/tắt LTO.

LTO chỉ giúp compiler **biết nhiều hơn để tối ưu**.

---

# 60. Effect + binary size

Nếu function có:

```text
PURE
```

và không được sử dụng:

```text
DCE
```

có thể loại bỏ.

Nếu function có:

```text
IO
```

nhưng không reachable:

```text
```

vẫn có thể loại bỏ nếu không có registration/export side effect.

---

# 61. Global initialization

Axiom không mặc định có hidden global constructors.

Nếu có explicit initialization:

```text
@init
```

thì compiler đưa vào:

```text
INIT
```

effect graph/link graph.

Nếu init chỉ là compile-time constant:

```text
comptime
```

thì runtime effect có thể biến mất.

---

# 62. Effect và runtime components

Effect summary giúp linker biết cần runtime nào.

Ví dụ:

```text
PURE program
```

không cần:

```text
IO
THREAD
ASYNC
UNICODE
NETWORK
```

runtime components có thể bị loại hoàn toàn.

---

# 63. Effect và freestanding

Freestanding program có thể có:

```text
READ
WRITE
ATOMIC
VOLATILE
```

nhưng không:

```text
IO
PROCESS
THREAD
```

tùy platform.

Compiler không ép kéo hosted runtime.

---

# 64. Effect và GPU

GPU kernel:

```text
@kernel fn foo(...)
```

không được có effect:

```text
File
Socket
Process
Host OS
```

Kernel legality checker sử dụng EffectSummary để reject.

---

# 65. Effect và async

Async function:

```text
async fn foo()
```

có:

```text
SUSPEND
```

nhưng:

```text
SUSPEND
```

không tự có:

```text
THREAD
```

Async vẫn có thể chạy hoàn toàn trên một thread.

---

# 66. Effect và concurrency

`spawn` thêm execution effect:

```text
SPAWN
```

nhưng `async fn` không tự spawn.

Channel:

```text
SEND
RECEIVE
```

có synchronization effects.

Thread creation:

```text
THREAD
```

runtime component tương ứng.

---

# 67. Effect và memory ordering

Ví dụ:

```ax
atomic.store(x, Release)
```

Effect:

```text
ATOMIC
WRITE
SYNCHRONIZE
```

với ordering:

```text
RELEASE
```

Alias analysis không được xóa `SYNCHRONIZE` chỉ vì memory value dường như không thay đổi.

---

# 68. Compiler barriers

```ax
compiler_fence(...)
```

có effect:

```text
COMPILER_BARRIER
```

CPU fence:

```ax
cpu_fence(...)
```

có:

```text
CPU_FENCE
```

Hai loại không được nhập làm một.

---

# 69. Effect và volatile

```text
volatile read
```

phải giữ observable access.

Ví dụ hardware register:

```ax
let status = volatile_read(REG);
```

compiler không được:

```text
CSE
DCE
```

nó chỉ vì giá trị trước đó có vẻ giống nhau.

---

# 70. Effect và FFI

Không có contract:

```text
extern foo(...)
```

→ conservative.

Có contract:

```text
reads = R1
writes = R2
```

→ effect/alias được refine.

Đây là cơ chế để Axiom vẫn tối ưu tốt khi interoperating với C/system APIs.

---

# 71. Effect explanation

CLI:

```text
axc inspect effects foo
```

ví dụ:

```text
foo

Effects:
    READ    user.name
    WRITE   output
    ALLOCATE
    PANIC

Sources:
    line 12 → load user.name
    line 18 → output.write
    line 21 → Vec::push
    line 27 → index operation
```

---

# 72. AI-readable effect data

`.axmeta` có thể chứa:

```json
{
  "function": "foo",
  "effects": ["READ", "WRITE", "ALLOCATE"],
  "reads": ["R17"],
  "writes": ["R23"],
  "panic": true,
  "suspend": false
}
```

AI agent có thể dùng trực tiếp thay vì phải phân tích source toàn bộ.

---

# 73. Effect và diagnostics

Nếu optimizer không hoist:

```ax
foo()
```

vì `foo` có:

```text
IO
```

compiler có thể giải thích:

```text
EOPT_EFFECT_BARRIER
call has observable IO effect
```

Nếu không CSE:

```text
foo()
foo()
```

vì `TIME`:

```text
EOPT_NONDETERMINISTIC_EFFECT
```

---

# 74. Effect summary cache

Effect summary phụ thuộc:

```text
function body
called functions
generic instances
trait resolution
FFI contracts
compiler semantic version
```

nên được cache trong CompilerDB.

---

# 75. Incremental effect analysis

Nếu:

```text
bar()
```

thay đổi implementation nhưng public signature không đổi:

```text
Effect(bar)
```

có thể thay đổi.

Các callers phụ thuộc effect phải được invalidated.

Nhưng các package không reachable từ `bar` không cần rebuild.

---

# 76. Effect fingerprint

Đề xuất:

```text
EffectFingerprint {
    semantic_effects
    read_regions
    write_regions
    external_state
    panic
    suspension
    sync
}
```

được đưa vào dependency graph.

---

# 77. Không expose toàn bộ effect system trong syntax

Axiom **không nên biến effect system thành một ngôn ngữ thứ hai**.

Không cần:

```text
fn foo() !{Read,Write,Alloc,IO,...}
```

cho ordinary code.

Compiler làm việc đó.

---

# 78. Khi nào cần effect annotation?

Chỉ ở những boundary mà compiler không thể derive:

```text
FFI
assembly
hardware
external device
foreign runtime
trusted intrinsic
```

hoặc khi một API muốn công bố contract đặc biệt.

---

# 79. Effect contracts phải được verify

Nếu viết:

```text
@contract(reads = R1)
```

nhưng function thực tế write `R2`:

```text
compile error
```

Không có “tin programmer”.

---

# 80. Core principle

> **Effect annotation là contract, không phải lời nói dối được compiler tin tưởng.**

---

# 81. Các invariant frozen

### `AEFFECT-20`
Every function has a compiler-derived semantic effect summary.

### `AEFFECT-21`
Effects are distinct from types.

### `AEFFECT-22`
Effects are distinct from ownership.

### `AEFFECT-23`
Effects are distinct from capabilities.

### `AEFFECT-24`
Effects are distinct from alias relations.

### `AEFFECT-25`
Read and write effects may be associated with semantic regions.

### `AEFFECT-26`
Unknown calls are conservative.

### `AEFFECT-27`
Foreign calls are conservative unless an explicit verified contract exists.

### `AEFFECT-28`
Compiler does not infer purity from absence of ordinary memory writes alone.

### `AEFFECT-29`
External state such as time, randomness, environment and process state is observable.

### `AEFFECT-30`
Pure functions have no observable external effects.

### `AEFFECT-31`
Pure does not imply comptime execution.

### `AEFFECT-32`
Comptime execution does not imply runtime purity.

### `AEFFECT-33`
Allocation is a semantic effect distinct from physical heap allocation.

### `AEFFECT-34`
Optimizer may eliminate allocation when semantic identity and lifetime permit.

### `AEFFECT-35`
Observable allocation identity prevents invalid allocation merging.

### `AEFFECT-36`
Drop is an observable effect when destruction has observable behavior.

### `AEFFECT-37`
Trivial Drop may be eliminated.

### `AEFFECT-38`
Recoverable `Result` failure is not an implicit panic effect.

### `AEFFECT-39`
Panic is a distinct control/effect property.

### `AEFFECT-40`
Async suspension is distinct from thread creation.

### `AEFFECT-41`
Synchronization effects preserve ordering semantics.

### `AEFFECT-42`
Atomic effects preserve atomicity and memory ordering.

### `AEFFECT-43`
Volatile effects cannot be treated as ordinary memory effects.

### `AEFFECT-44`
Compiler barriers and CPU fences are distinct effects.

### `AEFFECT-45`
GPU effects are associated with execution and storage domains.

### `AEFFECT-46`
Effect summaries propagate through static calls.

### `AEFFECT-47`
Dynamic dispatch uses a conservative union of possible target effects.

### `AEFFECT-48`
Effect inference supports recursion through deterministic fixed-point analysis.

### `AEFFECT-49`
Generic effect inference occurs after relevant semantic resolution.

### `AEFFECT-50`
Closure effects include captured-region accesses and called-function effects.

### `AEFFECT-51`
Effect analysis cooperates with capability analysis.

### `AEFFECT-52`
Effect analysis cooperates with alias analysis.

### `AEFFECT-53`
Effect analysis cooperates with escape analysis.

### `AEFFECT-54`
Effect facts may enable optimization but cannot alter program semantics.

### `AEFFECT-55`
Optimization must preserve observable effects.

### `AEFFECT-56`
An unknown effect may not be treated as no effect.

### `AEFFECT-57`
Compiler-generated effect summaries are deterministic.

### `AEFFECT-58`
Effect summaries are incrementally cacheable.

### `AEFFECT-59`
Independent effect analyses may execute in parallel.

### `AEFFECT-60`
Effect summaries retain source and dependency provenance.

### `AEFFECT-61`
Effect explanations are available through compiler inspection.

### `AEFFECT-62`
Effect metadata may be emitted into `.axmeta`.

### `AEFFECT-63`
Effect contracts at FFI/system boundaries must be verified.

### `AEFFECT-64`
Programmer annotations cannot falsely suppress effects.

### `AEFFECT-65`
Effect inference does not require programmer-written `pure`, `readonly`, `noexcept`, or `restrict` annotations for ordinary code.

### `AEFFECT-66`
LTO may refine effect knowledge but cannot change semantic effects.

### `AEFFECT-67`
Optimization level cannot change effect semantics.

### `AEFFECT-68`
Effect analysis never weakens safety verification.

### `AEFFECT-69`
Effect analysis never creates ownership or capability proofs.

### `AEFFECT-70`
Verified MIR remains the correctness boundary.

---

# Kiến trúc Axiom lúc này đã rất đẹp

Ba subsystem hiện phối hợp theo đúng vai trò:

```text
             ┌─────────────────┐
             │ Ownership       │
             │ Capability      │
             │ Initialization  │
             │ Drop            │
             └────────┬────────┘
                      │
                      ▼
               VERIFIED MIR
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     Alias Analysis          Effect Analysis
          │                       │
          └───────────┬───────────┘
                      ▼
                   OptIR
                      │
                      ▼
               Aggressive Opt
```

Và đây chính là điểm Axiom bắt đầu có khả năng đạt mục tiêu **“ngôn ngữ đơn giản cho programmer nhưng compiler cực kỳ thông minh”**:

```text
Programmer:
    không viết lifetime
    không viết borrow
    không viết restrict
    không viết pure
    không viết readonly
    không viết noexcept
    không viết alias annotation

Compiler:
    Ownership
    Capability
    Region
    Alias
    Effect
    Escape
    Range
    Concurrency
    Async
    GPU
    ABI
```

---

# BOOTSTRAP-138 — Escape Analysis, Allocation Promotion & Storage Optimization

Task tiếp theo nên khóa **Escape Analysis** trước khi đi sâu hơn vào optimization.

Nó sẽ quyết định một vấn đề cực kỳ quan trọng đối với mục tiêu hiệu năng của Axiom:

```text
Box<T>
Vec<T>
Closure
Temporary
Return value
Future
Buffer
```

**khi nào thực sự cần heap, khi nào có thể stack/register/inline, và khi nào compiler có thể loại bỏ allocation hoàn toàn.**

Pipeline sẽ trở thành:

```text
Ownership
   ↓
Capability
   ↓
Alias
   ↓
Effect
   ↓
Escape
   ↓
Storage Optimization
   ↓
OptIR
```

Đây là phần rất quan trọng để biến nguyên tắc **“heap allocation là một implementation detail, không phải mặc định hiệu năng thấp”** thành semantics + compiler algorithm cụ thể.