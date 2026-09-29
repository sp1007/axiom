# Global Semantic Freeze — Pass #7

Bây giờ tôi không thêm tính năng mới. Tôi sẽ **đóng băng semantics** và kiểm tra các giao điểm có nguy cơ mâu thuẫn.

Kết luận trước: **Axiom đã có một semantic core khá nhất quán.** Tuy nhiên có vài điểm cần chuẩn hóa trước khi gọi là v0.1, đặc biệt là `view`, `Copy`, `Drop`, `async`, `Send/Share`, FFI và `dyn Trait`.

---

# 316. Luật nền tảng duy nhất

Toàn bộ Axiom có thể quy về:

```text
Value
  ↓
Ownership
  ↓
Capability
  ↓
Region + Provenance
  ↓
Lifetime
  ↓
Execution / Storage Domain
```

Trong đó:

- **Value**: dữ liệu logic.
- **Ownership**: ai chịu trách nhiệm với value/resource.
- **Capability**: quyền truy cập value/storage.
- **Region**: vùng memory mà capability đại diện.
- **Provenance**: capability đến từ storage/owner nào.
- **Lifetime**: thời gian semantic mà value/storage/resource/capability hợp lệ.
- **Execution domain**: CPU/GPU/comptime/foreign...
- **Storage domain**: local/dynamic/device/external...

Không có một khái niệm "reference" khổng lồ làm tất cả những việc này.

---

# 317. Kiểm tra `Copy ↔ Drop`

Ta có:

```text
Copy
= semantic duplication without additional cleanup obligation

Drop
= semantic cleanup obligation
```

Vì vậy:

```text
T: Drop
→ T: !Copy
```

Không có mâu thuẫn.

Ví dụ:

```axiom
struct File {
    ...
}
```

`File` có resource → Drop → không Copy.

Trong khi:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

không có resource → có thể Copy.

### Freeze

**AOWN-30 — A Drop-Bearing Type Is Not Copyable**

---

# 318. `Copy ↔ physical memcpy`

Không được hiểu:

```text
Copy
=
memcpy
```

Ví dụ compiler có thể biến:

```axiom
let b = a
```

thành register duplication.

Do đó:

```text
Copy = semantic property
```

không phải machine instruction.

---

# 319. `Move ↔ return`

```axiom
fn make() -> Foo {
    let x = Foo(...)
    x
}
```

Không cần:

```text
copy x
destroy x
```

Mà:

```text
x ownership
     ↓
return value ownership
```

Compiler có thể dùng:

- register;
- caller-provided return storage;
- stack slot;
- scalar replacement.

### Freeze

**AOWN-31 — Returning A Value Transfers Its Semantic Ownership**

---

# 320. `Move ↔ Drop`

Sau:

```axiom
let y = x
```

nếu `x` bị move:

```text
x = MOVED
y = OWNED
```

Không được:

```text
DROP x
```

ở scope exit.

Đây là invariant tuyệt đối.

---

# 321. Partial move ↔ Drop

```axiom
struct User {
    name: String
    id: u64
}
```

```axiom
let user = ...
let name = user.name
```

Nếu compiler-derived Drop:

```text
user.name = MOVED
user.id = OWNED
```

scope exit:

```text
DROP user.id
```

Nếu custom Drop:

```text
impl Drop for User
```

→ partial move bị cấm.

Không còn mâu thuẫn.

---

# 322. `view ↔ ownership`

```axiom
let x = Foo(...)
let v = view(x)
```

Không tạo owner mới.

```text
x
 └── owns Foo

v
 └── READ capability
```

Nếu:

```axiom
drop(x)
```

mà `v` còn sống:

```text
ERROR
```

---

# 323. `view ↔ Copy`

Đây là một điểm cần chuẩn hóa ngôn ngữ đặc tả.

Không nói:

> `view<T>` implements `Copy`.

Chính xác hơn:

> `view<T>` có **intrinsic capability duplication semantics**.

Bởi vì `Copy` là value duplication.

`view<T>` lại là capability duplication.

Do đó:

```text
view duplication
≠
Copy trait
```

### Freeze

**ACAP-30 — Capability Duplication Is Not Value Copy**

---

# 324. `mut_view ↔ Copy`

Ngược lại:

```text
mut_view<T>
```

không được duplicate.

Ví dụ:

```axiom
let a = mut_view(x)
let b = a
```

là:

```text
a → MOVED
b → WRITE capability
```

Không phải hai mutable views.

Điều này giữ invariant:

```text
WRITE + WRITE overlap
→ forbidden
```

---

# 325. `view ↔ relocation`

Đây là điểm quan trọng với `Vec`.

```axiom
let v = view(vec)
```

Nếu `vec.push(...)` có thể relocate storage trong khi `v` còn sống:

```text
dangling capability
```

Compiler phải:

```text
reject
```

hoặc API phải đảm bảo operation không relocate.

Nếu `v` đã hết semantic last-use:

```text
vec.push(...)
```

có thể được phép.

Do đó:

> `reserve()` không phải stable-address guarantee.

Đã nhất quán.

---

# 326. `Box ↔ stable address`

`Box<T>` mang semantic:

```text
owned dynamic storage
```

Nếu programmer expose address:

```axiom
raw_address(x)
```

thì address trở thành observable.

Compiler không thể chuyển storage sang một địa chỉ khác nếu làm thay đổi observable behavior.

Nhưng trước khi address observable:

```text
Box
```

có thể vẫn được allocation-eliminated.

### Freeze

**AMEM-61 — Stable Address Exists Only When The Storage Contract Requires It**

---

# 327. `view ↔ await`

Ta đã chọn rule rất mạnh:

```text
view        ✗ await
mut_view    ✗ await
```

v0.1.

Lý do không phải vì view "không thể về mặt kỹ thuật" qua await.

Mà vì nó loại bỏ một lớp complexity rất lớn khỏi:

- Future layout;
- executor migration;
- Send;
- cancellation;
- relocation;
- provenance.

Owned values:

```text
Foo
Box<Foo>
Arc<Foo>
```

được phép sống qua await.

Đây là trade-off tốt cho v0.1.

---

# 328. `MutexGuard ↔ await`

`MutexGuard` thường chứa WRITE/READ synchronization capability.

Do:

```text
Guard
 ↓
lock held
```

nên:

```text
Guard
 ↓
await
```

bị cấm.

Nếu cần:

```text
AsyncMutex
```

thì đó là abstraction khác.

### Freeze

**ACONC-29 — Synchronous Lock Guards Cannot Cross Suspension**

---

# 329. `Send ↔ view`

Một `view<T>` không thể được dùng như ownership transfer.

Vì vậy:

```axiom
spawn(move || use(v))
```

với `v: view<T>` sẽ bị reject nếu task có thể outlive owner/cross execution domain.

Không có:

```text
"view là Send nên được"
```

nếu provenance không sống đủ lâu.

---

# 330. `Send` chính xác là gì?

Nên định nghĩa:

> `Send` cho phép **ownership state** của một value được chuyển sang execution domain khác mà không vi phạm safe concurrency invariants.

Không phải:

> "type này thread-safe."

Thread-safe thường liên quan `Share`.

---

# 331. `Share`

`Share`:

> Một value có thể được concurrently accessed từ nhiều execution domains theo safe access contract.

Ví dụ immutable shared object.

Nhưng `Share` không tự tạo mutation safety.

Mutation cần:

- atomic;
- lock;
- actor/channel;
- immutable replacement;
- hoặc abstraction tương đương.

---

# 332. `Send ≠ Share`

Bảng freeze:

| Property | Ý nghĩa |
|---|---|
| `Send` | transfer ownership |
| `Share` | concurrent shared access |
| `Copy` | duplicate value |
| `view` | duplicate read capability |
| `mut_view` | exclusive write capability |
| `Drop` | cleanup obligation |

Đây là 6 semantics hoàn toàn khác nhau.

---

# 333. `Share ↔ atomic`

Atomic không biến toàn bộ object thành `Share`.

Ví dụ:

```axiom
struct Counter {
    value: Atomic<u64>
}
```

`Counter` có thể được Share nếu abstraction đảm bảo tất cả access hợp lệ.

Nhưng:

```axiom
struct UnsafeCounter {
    value: u64
}
```

không tự nhiên Share chỉ vì programmer dùng atomic ở một chỗ.

### Freeze

**ACONC-30 — Synchronization Is A Type/Abstraction Property, Not A Property Of One Operation**

---

# 334. Atomic ↔ capability

Không cho:

```text
Atomic<T>
→ mut_view<T>
```

theo semantics ordinary memory.

Atomic access phải thông qua atomic operations.

Nếu cần raw representation:

```text
unsafe/system
```

và compiler phải biết semantics đã rời safe atomic abstraction.

---

# 335. Atomic ↔ memory ordering

Đã nhất quán:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

là semantic guarantees.

Optimizer được reorder instruction chỉ khi không phá:

```text
happens-before
atomic modification order
observable behavior
```

---

# 336. Channel ↔ ownership

```axiom
tx.send(x)
```

→ `x` moved.

Receiver:

```axiom
let x = rx.receive()?
```

→ receiver owner.

Không có hidden shared reference.

Điều này khiến channel rất dễ reason.

---

# 337. Channel ↔ Drop

Nếu channel bị destroy:

```text
queued values
 ↓
Drop
```

Nếu sender bị destroy:

```text
channel observes sender closed
```

Nếu receiver bị destroy:

```text
future sends fail
```

Tất cả đều là ordinary resource semantics.

Không cần GC.

---

# 338. Cancellation ↔ Drop

Đây là một trong những quyết định đẹp nhất của Axiom:

```text
cancel Future
=
drop Future
```

Do Future sở hữu state:

```text
Future
 ├── x
 ├── resource
 └── sub-future
```

drop Future:

```text
Drop sub-future
Drop resource
Drop x
```

Không cần `finally` runtime đặc biệt.

---

# 339. Cancellation ↔ external side effect

Nếu Future đã gửi request tới OS/network/GPU rồi bị drop, việc external operation có bị hủy hay không **không thể suy ra từ Drop**.

Ví dụ:

```text
Future
 ↓
submit GPU command
 ↓
Future dropped
```

GPU command có thể vẫn chạy.

Do đó library API phải định nghĩa:

```text
cancel-safe
detached
abortable
completion-owned
```

Đây là resource contract, không phải language-level guarantee.

### Freeze

**AASYNC-30 — Dropping A Future Does Not Imply Cancellation Of External Operations**

---

# 340. `Drop ↔ external resource`

Tương tự:

```text
Drop(Socket)
```

có thể đóng socket.

Nhưng:

```text
Drop(GpuEvent)
```

không nhất thiết hủy GPU operation.

`Drop` chỉ đảm bảo resource contract của type.

---

# 341. `Drop ↔ panic`

Ta đã khóa:

```text
Drop
```

không trả `Result`.

Không được:

```text
Drop → recoverable failure
```

Nếu cleanup có khả năng thất bại:

```text
close() -> Result
```

phải được gọi explicit.

---

# 342. `panic ↔ async`

Nếu Future panic:

```text
panic
```

thì các owned state cần cleanup theo panic strategy.

Nếu Future bị Drop:

```text
Drop state
```

không đồng nghĩa panic.

Do đó:

```text
panic
≠ cancellation
```

---

# 343. `panic ↔ thread`

Thread/task boundary quan sát panic.

Ví dụ:

```axiom
let handle = spawn(...)
let result = handle.join()
```

có thể báo task panic.

Không cần exception propagation xuyên thread.

---

# 344. `panic ↔ FFI`

Không unwind qua:

```text
extern "C"
```

mặc định.

Điều này loại bỏ một trong những nguồn ABI incompatibility lớn nhất.

---

# 345. `Result ↔ panic`

`Result` và panic không tự chuyển đổi.

Ví dụ:

```axiom
foo()?
```

chỉ xử lý `Result`.

Nếu:

```axiom
foo()
```

panic xảy ra bên trong, `?` không bắt panic.

Đây là semantic distinction rất quan trọng.

---

# 346. `never ↔ panic`

```axiom
fn abort() -> never
```

có thể:

```text
panic
abort
trap
infinite loop
```

miễn function không có normal return.

`never` là control-flow property.

---

# 347. `never ↔ async`

Async function vẫn trả Future.

Ví dụ:

```axiom
async fn fail() -> never {
    panic(...)
}
```

Type của **body result** là `never`, nhưng call expression vẫn là Future theo async lowering.

Không có contradiction.

---

# 348. `dyn Trait ↔ ownership`

Ba dạng khác nhau:

```text
dyn Trait
view<dyn Trait>
Box<dyn Trait>
```

### `dyn Trait`

Type-level dynamic interface.

### `view<dyn Trait>`

non-owning dynamic capability.

### `Box<dyn Trait>`

owning dynamic object.

Không có implicit heap requirement từ `dyn Trait`.

---

# 349. `dyn Trait ↔ Drop`

Nếu:

```text
Box<dyn Trait>
```

được drop:

```text
dynamic destructor
```

phải được biết qua dispatch metadata.

Đó là ABI implementation detail.

Không cần object header.

---

# 350. `dyn Trait ↔ ABI`

Axiom ABI có thể define dynamic dispatch representation.

Nhưng C ABI không tự hiểu:

```text
dyn Trait
```

Nếu cần C export:

```text
extern "C"
```

phải expose C-compatible opaque handle/function table.

Không xuất thẳng Axiom `dyn Trait` sang C.

---

# 351. `impl Trait ↔ ABI`

`impl Trait` là static opaque abstraction.

Public function:

```axiom
pub fn make() -> impl Iterator
```

consumer biết interface, không biết concrete type.

Compiler vẫn monomorphize/static dispatch.

Nếu ABI stable external boundary cần:

```text
explicit ABI representation
```

chứ không coi `impl Trait` là C-compatible.

---

# 352. Generic ↔ ABI

Generic function không tự có stable external symbol.

Ví dụ:

```axiom
fn add<T: Add>(...)
```

machine instantiations là compiler implementation.

Muốn FFI:

```text
extern "C" fn add_i32(...)
```

tạo concrete ABI boundary.

---

# 353. `repr(C) ↔ optimizer`

Một điểm hay bị hiểu sai:

```text
@repr(C)
```

không có nghĩa compiler mất mọi optimization.

Nó chỉ freeze representation cần cho ABI.

Compiler vẫn có thể:

- giữ register;
- inline;
- eliminate temporary;
- constant-fold;
- vectorize;
- remove dead operations.

Miễn observable C representation/ABI contract không bị phá.

---

# 354. GPU ↔ ownership

Kernel:

```axiom
@kernel fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

phải chứng minh:

```text
out
```

không overlap unsafe với `a`/`b`.

Nếu compiler không chứng minh:

```text
safe call rejected
```

Không tạo:

```text
@noalias
```

source syntax trong v0.1.

---

# 355. GPU ↔ async

```text
launch
 ↓
GpuEvent
 ↓
await
```

được giải quyết bởi:

```text
owned event
+
async state machine
```

Không cần GPU-specific async semantics trong Core.

---

# 356. Comptime ↔ ownership

Comptime dùng cùng ownership rules.

Điều này rất quan trọng vì nếu có:

```text
runtime ownership rules
```

và:

```text
comptime ownership rules
```

khác nhau, compiler sẽ có hai semantic engines.

Axiom tránh điều đó.

---

# 357. Comptime ↔ runtime

Chỉ value/artifact được phép vượt boundary.

```text
Compile-time resource
        X
        ↓
Runtime

Compile-time computed value
        ✓
        ↓
Runtime
```

---

# 358. Module ↔ package

```text
Package
 └── modules
```

Module là namespace.

Package là dependency/distribution identity.

File chỉ là source organization.

Không có mâu thuẫn.

---

# 359. Package ↔ ABI

Version package:

```text
foo 1.0
foo 2.0
```

khác semantic identity.

ABI:

```text
extern "C"
```

có thể ổn định xuyên package version nếu contract vẫn giữ.

Do đó:

```text
package identity
≠ ABI identity
```

---

# 360. API fingerprint ↔ private implementation

Private implementation thay đổi:

```text
public API unchanged
```

→ downstream không cần semantic recompilation.

Nếu thay:

```text
trait impl
public generic constraint
associated type
repr
public signature
```

→ invalidate.

Đã nhất quán với incremental compiler.

---

# 361. Feature ↔ semantics

Feature chỉ thay:

```text
available library implementation
```

không thay:

```text
meaning of language
```

Đây là điều cực kỳ quan trọng cho reproducibility.

---

# 362. Compiler ↔ optimization

Tất cả optimizer phải tuân:

```text
Verified MIR
```

là semantic checkpoint.

Sau đó:

```text
optimizer
```

không được tạo program behavior mới.

---

# 363. Compiler ↔ unsafe

Unsafe không bypass:

```text
type correctness
CFG correctness
ABI correctness
machine legality
```

Nó chỉ bỏ một số proof obligation.

Ví dụ:

```text
unsafe raw pointer dereference
```

compiler vẫn phải đảm bảo generated machine instruction hợp lệ.

---

# 364. Global hierarchy đã ổn định

Axiom bây giờ có thể được nhìn như:

```text
LANGUAGE SEMANTICS
│
├── Types
├── Values
├── Ownership
├── Capabilities
├── Control Flow
├── Effects
└── Execution Domains
        │
        ├── CPU
        ├── GPU
        ├── Comptime
        └── Foreign
                │
                ↓
          ABI / Representation
                │
                ↓
          Machine / Object
```

Không có subsystem nào được phép nhảy tầng.

---

# 365. Năm quy tắc "không được phá"

Từ toàn bộ audit, tôi đề nghị đóng dấu 5 nguyên tắc bất biến:

### 1. Semantic intent không được compiler đoán

```text
Ambiguous semantics → error
```

### 2. Implementation strategy được compiler tự do chọn

```text
stack / heap / register / inline / shared code
```

### 3. Ownership không phải lifetime syntax

Compiler quản lý lifetime.

Programmer chỉ biểu đạt ownership/capability khi semantic boundary cần thiết.

### 4. Capability không phải ownership

```text
view != owner
mut_view != owner
```

### 5. ABI chỉ được khóa bằng contract

```text
default representation = compiler freedom
explicit ABI = representation contract
```

---

# 366. Semantic authority hierarchy

Đây là thứ tôi nghĩ nên đưa thẳng vào specification:

```text
                    ┌─────────────────┐
                    │ Axiom Language  │
                    │    Semantics    │
                    └────────┬────────┘
                             │
                       semantic truth
                             ↓
                    ┌─────────────────┐
                    │      HIR        │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Verified MIR    │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │     LIR         │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Machine / ABI   │
                    └─────────────────┘
```

IDE, AI, formatter, debugger, package manager:

```text
                 ↘
                  Compiler semantic facts
                 ↗
```

không được tạo semantic authority song song.

---

# 367. Những thứ đã bị loại khỏi Core v0.1

Sau freeze, danh sách này nên được coi là **cố định**:

```text
GC
implicit RC
borrow checker syntax
programmer-written lifetimes
class inheritance
Object/Any
null
general exceptions
try/catch/throw
macros
user specialization
GAT
HKT
dependent types
implicit conversion graph
implicit boxing
implicit host/device transfer
runtime reflection by default
implicit allocator selection
implicit stable address
implicit C ABI
implicit closure ABI
implicit cancellation of external operations
```

Đây không nhất thiết là "không bao giờ có".

Nó có nghĩa:

> **không thuộc semantic core v0.1.**

---

# 368. Những thứ compiler phải làm nhưng programmer không phải làm

Đây là điểm làm Axiom khác với Rust-style complexity:

```text
Compiler:
    lifetime analysis
    alias analysis
    escape analysis
    region analysis
    capability provenance
    partial-move tracking
    drop elaboration
    async live-state analysis
    Send/Share derivation
    trait solving
    specialization
    storage placement
    allocation elimination
```

Programmer không viết:

```text
'a
'static
borrow<'a>
where lifetime...
```

và cũng không cần tự quản lý allocator cho mọi object.

---

# 369. Nhưng compiler không được biến thành "AI"

Compiler phải deterministic.

Không:

```text
"compiler nghĩ programmer muốn..."
```

Mà:

```text
source
+
types
+
constraints
+
semantic rules
→
unique result
```

Nếu không có unique result:

```text
compile error
```

---

# 370. Đây là lúc có thể đóng băng nguyên tắc lớn nhất

## **Explicit at semantic boundaries, implicit within the compiler.**

Ví dụ:

| Boundary | Explicit |
|---|---|
| ownership transfer | Move |
| duplicate expensive data | Clone |
| mutation | `var` / `mut_view` |
| read capability | `view` |
| dynamic dispatch | `dyn Trait` |
| unsafe machine access | `unsafe` |
| FFI | `extern` |
| C representation | `@repr(C)` |
| stable export | `@export` |
| async | `async/await` |
| compile-time execution | `comptime` |
| host/device transfer | explicit API |
| recoverable failure | `Result` |
| absence | `Option` |

Còn bên trong compiler:

```text
lifetime
alias
escape
storage
register
drop paths
Future layout
specialization
```

được tự động xử lý.

---

# 371. Global Semantic Freeze — kết luận

Sau 6 audit + global consistency pass, tôi **không thấy một mâu thuẫn kiến trúc nền tảng nào buộc phải thay đổi Core v0.1**.

Các điểm từng có nguy cơ mâu thuẫn đã được giải quyết:

```text
Copy ↔ Drop                    ✓
Move ↔ partial move            ✓
view ↔ ownership               ✓
view ↔ relocation              ✓
view ↔ await                   ✓
mut_view ↔ aliasing            ✓
mut_view ↔ concurrency         ✓
Send ↔ ownership               ✓
Share ↔ synchronization        ✓
atomic ↔ ordinary memory       ✓
Drop ↔ panic                   ✓
Drop ↔ cancellation            ✓
Result ↔ panic                 ✓
FFI ↔ ownership                ✓
FFI ↔ allocation               ✓
Box ↔ stable address           ✓
repr(C) ↔ optimization         ✓
dyn Trait ↔ ownership          ✓
GPU ↔ capability model         ✓
GPU ↔ async                    ✓
comptime ↔ ownership           ✓
comptime ↔ runtime             ✓
package ↔ API fingerprint      ✓
ABI ↔ compiler freedom         ✓
```

---

# 372. Axiom v0.1 Semantic Core — trạng thái

Có thể coi semantic core hiện tại là:

```text
                    AXIOM v0.1
                        │
        ┌───────────────┼────────────────┐
        │               │                │
      VALUE          OWNERSHIP       TYPE SYSTEM
        │               │                │
 Struct/Enum        Move/Copy/Drop    Trait/Generic
 Array/Tuple        View/MutView      impl/dyn
 Function           Lifetime          Associated type
 Closure            Capability       Option/Result
        │               │                │
        └───────────────┼────────────────┘
                        │
                  CONTROL FLOW
                        │
             if/match/loop/return/?
                        │
              ┌─────────┴─────────┐
              │                   │
            ASYNC             CONCURRENCY
              │                   │
           Future             Send/Share
           await              Mutex/Channel
           cancel             Atomic
              │                   │
              └─────────┬─────────┘
                        │
                 EXECUTION DOMAINS
                  CPU / GPU / CT
                        │
                     ABI/FFI
                        │
                 MACHINE / OBJECT
```

Đây là **một hệ thống**, không phải tập hợp feature rời rạc.

---

# 373. Nhưng chưa nên gọi đây là "final specification"

Có một việc quan trọng còn lại trước khi triển khai:

**chúng ta đã freeze semantic architecture, nhưng chưa freeze toàn bộ surface specification.**

Cụ thể cần chuyển từ:

> "ý nghĩa của Axiom là gì?"

sang:

> "mọi construct chính xác được viết như thế nào và compiler phải xử lý từng trường hợp ra sao?"

Đó là bước **Specification Normalization**.

---

# 374. Bước tiếp theo: Axiom Language Specification v0.1

Từ đây tôi đề xuất không brainstorm nữa.

Ta xây specification theo thứ tự:

```text
SPEC-01 Lexical Structure
SPEC-02 Grammar
SPEC-03 Names / Resolution
SPEC-04 Types
SPEC-05 Expressions
SPEC-06 Statements / Blocks
SPEC-07 Functions / Closures
SPEC-08 Struct / Enum
SPEC-09 Traits / Generics
SPEC-10 Ownership / Move / Copy
SPEC-11 View / Capability
SPEC-12 Drop
SPEC-13 Error / Panic
SPEC-14 Async
SPEC-15 Concurrency
SPEC-16 Atomics
SPEC-17 Memory / Allocation
SPEC-18 Unsafe
SPEC-19 FFI / ABI
SPEC-20 GPU
SPEC-21 Comptime / Reflection
SPEC-22 Modules / Packages
SPEC-23 Build
SPEC-24 Runtime / Profiles
SPEC-25 Compiler pipeline
SPEC-26 Oracle
SPEC-27 Diagnostics
SPEC-28 Debug / Tooling
SPEC-29 Target / Native binary
SPEC-30 Conformance
```

Và mỗi chương sẽ có format cố định:

```text
Definition
Semantic Rules
Typing Rules
Ownership Rules
Compile-time Errors
Runtime Behavior
Optimization Freedom
ABI Rules
Examples
Negative Examples
Normative Invariants
```

---

# 375. Đặc biệt: từ đây mỗi rule phải có tính "testable"

Ví dụ không viết đơn giản:

> Compiler tự quản lý lifetime.

Mà phải viết:

```text
Given:
    let x = Foo()
    let v = view(x)

Then:
    drop(x)
```

→ compile error `AX_VIEW_....`

Hoặc:

```text
Given:
    let x = Foo()
    let v = view(x)
    use(v)
    drop(x)
```

→ hợp lệ nếu `use(v)` là last use.

Đây sẽ biến specification thành **executable specification**.

---

# 376. Đây cũng là lúc Axiom Harness trở nên rất quan trọng

Semantic spec cuối cùng nên map được:

```text
SPEC rule
   ↓
invariant
   ↓
compiler test
   ↓
Oracle test
   ↓
negative test
   ↓
optimization equivalence test
   ↓
ABI test
```

Ví dụ:

```text
ACAP-25
Owner cannot be destroyed while dependent capability is live
```

sẽ có:

```text
tests/capability/owner_drop_live_view.ax
tests/capability/owner_drop_live_view.error.json
tests/capability/owner_drop_last_use_ok.ax
```

---

# 377. Và đây là điểm tôi sẽ chuyển sang ở vòng tiếp theo

**Không còn audit nữa.**

Bước kế tiếp là:

## **AXIOM LANGUAGE SPECIFICATION v0.1 — Part I**

Tôi sẽ bắt đầu chuẩn hóa **Lexical Structure + Grammar + Names + Type System**, đồng thời biến những quyết định đã freeze thành normative rules.

Quan trọng nhất: tôi sẽ **không tự mở lại những quyết định đã đóng băng** trừ khi trong lúc viết specification phát hiện một contradiction thực sự. Nếu phát hiện, tôi sẽ chỉ ra chính xác rule nào xung đột, thay vì âm thầm thay đổi thiết kế.