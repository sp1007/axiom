Tiếp tục. Tôi sẽ chốt **EFFECT/CONTROL-001** trước, nhưng theo hướng rất hạn chế: **Axiom không có một effect system tổng quát ở v1**. Sau đó đi thẳng sang **GENERIC-001 / TRAIT-SOLVER-001**, vì đây là phần quyết định abstraction có thực sự zero-cost hay không.

# EFFECT/CONTROL-001

## 1. Nguyên tắc

Không biến function signature thành:

```text
fn foo() throws allocates blocks io unsafe async ...
```

Thay vào đó compiler duy trì một **Semantic Facts Graph** nội bộ.

```text
Function
 ├── Ownership facts
 ├── Capability facts
 ├── Async/Suspension facts
 ├── Unsafe facts
 ├── Concurrency facts
 ├── Execution-domain facts
 ├── Panic facts
 ├── Allocation facts
 └── ABI facts
```

Phần lớn **không xuất hiện trong source syntax**.

---

# 2. Chỉ 6 nhóm effect/fact là semantic-critical

Tôi đề xuất compiler theo dõi:

```text
1. Memory / Ownership
2. Capability / Alias
3. Suspension
4. Unsafe
5. Concurrency / Atomic
6. Execution Domain
```

Các thứ như:

```text
filesystem
network
logging
allocation
blocking
```

không mặc định trở thành type-system effects.

---

# 3. `async` là effect đặc biệt

`async` phải nằm trên declaration:

```text
async fn fetch() -> Result<Data, Error>
```

vì nó thay đổi calling convention/return type:

```text
fetch()
```

không trả trực tiếp `Data`.

Nó trả Future.

Do đó `async` là **language semantic modifier**, không phải annotation thông thường.

---

# 4. `await` là control-flow operation

```text
let data = await fetch()
```

MIR:

```text
CALL fetch
SUSPEND_IF_PENDING
SAVE_STATE
RETURN_PENDING

RESUME
RESTORE_STATE
CONTINUE
```

Compiler phải biết chính xác:

> điểm này có thể suspend.

---

# 5. View không được sống qua await

Đã chốt:

```text
let v = view(data)
await something(v)
```

nếu `v` có khả năng tồn tại qua suspension:

```text
ERROR
```

Compiler có thể cho phép nếu chứng minh `v` kết thúc trước await.

Ví dụ:

```text
process(view(data))
await task
```

hoàn toàn hợp lệ.

---

# 6. Ownership không phải effect annotation

Không viết:

```text
fn foo(x: T) // moves x
```

compiler tự biết.

Tương tự:

```text
fn foo(view x)
```

thể hiện capability vì nó **thay đổi API contract**, nhưng không cần một effect declaration riêng.

---

# 7. Unsafe là boundary

```text
unsafe fn read(...)
```

và:

```text
unsafe {
    ...
}
```

được compiler ghi nhận.

Unsafe có tính chất khác effects thông thường:

> nó thay đổi **proof responsibility**.

Không phải:

> function này có thêm một runtime side effect.

---

# 8. Allocation không phải effect của Core

Ví dụ:

```text
Box.new(x)
```

có semantic dynamic-storage intent.

Nhưng:

```text
Box.new(x)
```

có thể được compiler tối ưu thành stack/register.

Vì vậy không nên bắt:

```text
fn foo() allocates
```

xuất hiện trong type signature.

---

# 9. Blocking cũng không phải Core effect

```text
socket.read(...)
```

có thể blocking tùy implementation.

Compiler không cần biến:

```text
fn read() blocking
```

thành type-level effect.

Library/tooling có thể đánh dấu:

```text
@blocking
```

nếu muốn static analysis.

Nhưng đó là **tooling metadata**, không phải language semantics.

---

# 10. IO cũng vậy

```text
File.read()
```

có IO side effect.

Nhưng không cần:

```text
fn read() -> Result<Data, Error> with IO
```

Điều này giữ API sạch.

---

# 11. Panic

Panic được compiler biết vì:

```text
panic() -> never
```

và optimizer cần biết nó không return.

Nhưng không cần:

```text
fn foo() panic
```

trong signature.

---

# 12. Pure function

Không đưa `pure` vào Core v1.

Compiler có thể tự phân tích:

```text
fn square(x: f64) -> f64 {
    x * x
}
```

và phát hiện:

```text
no observable side effects
```

để optimization.

Không cần programmer viết:

```text
pure fn
```

---

# 13. Nhưng compiler không được tự biến pure thành semantic guarantee

Ví dụ:

```text
fn read_counter() -> u64
```

compiler không được tự suy ra function pure chỉ vì body hiện tại trông như vậy nếu external/volatile/atomic semantics tồn tại.

Pure analysis là optimization fact.

Không phải public contract.

---

# 14. `volatile`

Volatile:

```text
unsafe volatile_read(...)
unsafe volatile_write(...)
```

được compiler coi là observable machine operation.

Không được loại bỏ/reorder tùy ý như normal load/store.

---

# 15. Atomic

Atomic đã có memory ordering riêng:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Không cần:

```text
effect Atomic
```

vì chính operation type/API đã biểu đạt semantics.

---

# 16. GPU

GPU execution domain là semantic fact.

```text
@kernel
fn add(...)
```

Compiler cần biết:

```text
ExecutionDomain = GPU
```

để kiểm tra:

- pointer;
- IO;
- synchronization;
- address space;
- allowed calls.

Đây không phải generic effect system.

---

# 17. Foreign calls

```text
extern "C" fn foo(...)
```

là ABI fact.

Compiler không cần:

```text
effect FFI
```

Nhưng call có thể được đánh dấu:

```text
opaque side effect
```

để optimizer không giả định quá mức.

---

# 18. Control-flow facts

Compiler cần internal facts:

```text
MayReturn
NeverReturns
MaySuspend
MayPanic
MayTrap
```

Nhưng chúng không nhất thiết xuất hiện trong source.

Ví dụ:

```text
panic() -> never
```

đủ để suy ra `NeverReturns`.

---

# 19. Interprocedural propagation

Nếu:

```text
fn a() {
    b()
}
```

và `b()` có:

```text
MaySuspend
```

thì `a()` chỉ được phép gọi `b()` nếu `a` là async context hoặc API phù hợp.

Compiler kiểm tra call graph.

Không bắt programmer viết:

```text
fn a() async
```

nếu `a` thực sự không thay đổi calling convention.

Nhưng nếu `a` trực tiếp chứa `await`, thì phải khai báo:

```text
async fn a()
```

---

# 20. Đây là distinction rất quan trọng

Có hai loại facts:

### Signature-changing

Phải thể hiện trong source:

```text
async
unsafe
@kernel
extern
```

### Internal semantic facts

Không cần viết:

```text
MayPanic
MayAllocate
MayIO
MayBlock
HasAtomic
Pure
```

---

# 21. Bảng chốt

| Property | Source-visible? | Compiler fact? |
|---|---:|---:|
| async | Có | Có |
| unsafe | Có | Có |
| GPU/kernel | Có | Có |
| extern ABI | Có | Có |
| ownership | Không | Có |
| alias/capability | Không | Có |
| allocation | Không | Có |
| blocking | Không | Có |
| IO | Không | Có |
| panic | Không | Có |
| purity | Không | Có |
| atomic | API/type | Có |
| suspension | `async/await` | Có |
| target domain | attribute | Có |

Đây là kiến trúc tôi khuyên **freeze**.

---

# 22. Invariants

```text
AEFFECT-20 — Semantic Effects Are Compiler Facts

AEFFECT-21 — Axiom Has No General Effect Annotation System In v1

AEFFECT-22 — Signature-Changing Effects Are Explicit

AEFFECT-23 — Non-Signature Effects Remain Internal Facts

AEFFECT-24 — Async Is Explicit

AEFFECT-25 — Suspension Is Compiler-Tracked

AEFFECT-26 — Unsafe Is An Explicit Proof Boundary

AEFFECT-27 — Allocation Is Not A Type-Level Effect

AEFFECT-28 — Blocking Is Not A Core Type-Level Effect

AEFFECT-29 — IO Is Not A Core Type-Level Effect

AEFFECT-30 — Panic Does Not Require Effect Annotation

AEFFECT-31 — Compiler May Infer Optimization Facts

AEFFECT-32 — Optimization Facts Do Not Become Semantic Guarantees

AEFFECT-33 — Atomic Semantics Are Defined By Atomic Operations

AEFFECT-34 — GPU Execution Domain Is Explicit

AEFFECT-35 — FFI ABI Is Explicit

AEFFECT-36 — Effect Analysis Must Not Change Program Semantics
```

---

# GENERIC-001 — Generics

Đây mới là phần rất quan trọng đối với mục tiêu:

> **Abstraction mạnh nhưng không runtime overhead.**

Axiom nên dùng:

```text
Generic source
      ↓
Constraint solving
      ↓
Instantiation
      ↓
Monomorphization
      ↓
Optimization
      ↓
Machine code
```

---

# 23. Generic mặc định là static

```text
fn max<T: Ord>(a: T, b: T) -> T
```

không tạo:

```text
runtime generic object
```

và không cần:

```text
type descriptor
```

trừ khi API yêu cầu runtime reflection.

---

# 24. Monomorphization

Ví dụ:

```text
max<i32>
max<f64>
max<u64>
```

Compiler tạo các specialization:

```text
max_i32
max_f64
max_u64
```

sau đó optimizer có thể inline.

---

# 25. Nhưng không được để binary phình vô hạn

Ví dụ:

```text
foo<T>
```

được instantiate 1000 type.

Compiler cần dedup.

Nếu:

```text
foo<A>
foo<B>
```

sau lowering tạo machine code giống hệt:

```text
COMDAT / ICF / semantic dedup
```

có thể merge.

---

# 26. Generic không nhất thiết phải monomorphize mọi thứ

Axiom có thể có chiến lược:

```text
specialize
```

hoặc:

```text
share
```

tùy compiler.

Ví dụ generic function chỉ thao tác trên opaque layout:

```text
fn identity<T>(x: T) -> T {
    x
}
```

nhiều instantiation có thể share machine implementation nếu ABI cho phép.

Nhưng initial compiler:

> **monomorphization trước, dedup sau.**

Đơn giản và dễ debug.

---

# 27. Generic constraints

```text
fn sort<T: Ord>(items: mut_view<T>)
```

Compiler phải solve:

```text
Does T implement Ord?
```

trước MIR.

MIR không nên chứa:

```text
trait solver query
```

---

# 28. Trait solver

Tôi đề xuất solver theo mô hình:

```text
Goal
 ↓
Candidate lookup
 ↓
Impl matching
 ↓
Unification
 ↓
Constraint solving
 ↓
Proof
```

Ví dụ:

```text
T: Add<U>
```

solver tìm:

```text
impl Add<U> for T
```

---

# 29. Không có unrestricted specialization v1

Không cho:

```text
impl<T> Foo for T
impl Foo for i32
```

rồi compiler phải quyết định implementation nào “thắng”.

Thay vào đó coherence rules phải rõ.

---

# 30. Coherence

Một cặp:

```text
(Trait, Type)
```

chỉ có một implementation hợp lệ trong toàn chương trình/module coherence model.

Ví dụ:

```text
impl Display for User
```

không thể có một implementation thứ hai conflict.

---

# 31. Orphan rule

Tôi đề xuất quy tắc đơn giản:

Bạn chỉ được implement trait nếu:

```text
trait thuộc module của bạn
```

hoặc:

```text
type thuộc module của bạn
```

Ví dụ:

```text
impl MyTrait for std::String
```

được nếu `MyTrait` của bạn.

Nhưng:

```text
impl std::Display for std::String
```

không được từ application module.

Điều này tránh dependency order conflict.

---

# 32. Associated type

Ví dụ:

```text
trait Iterator {
    type Item

    fn next(mut self) -> Option<Self.Item>
}
```

Solver phải resolve:

```text
I::Item
```

khi `I` đã biết.

---

# 33. Associated type equality

Có thể viết:

```text
T: Iterator<Item = u32>
```

Solver hiểu:

```text
associated_type(T, Iterator, Item) == u32
```

Đây là một constraint rất hữu ích.

---

# 34. Generic associated constraints

Ví dụ:

```text
fn sum<I: Iterator<Item = i32>>(it: I) -> i32
```

đủ mạnh cho phần lớn generic programming.

Không cần dependent type system.

---

# 35. Generic const parameters

Cho phép giới hạn:

```text
struct Array<T, const N: usize> {
    data: [T; N]
}
```

Nhưng chỉ hỗ trợ các const types đơn giản:

```text
bool
integer
char?
```

Tôi khuyên v1:

```text
integer/bool
```

trước.

Không full dependent types.

---

# 36. Type aliases

```text
type UserId = u64
```

là alias, không tạo type mới.

```text
type UserId = u64
```

thì:

```text
UserId == u64
```

---

# 37. Newtype

Khi cần type identity:

```text
distinct UserId = u64
```

Ví dụ:

```text
distinct UserId = u64
distinct ProductId = u64
```

Compiler không cho:

```text
let p: ProductId = user_id
```

dù representation giống.

---

# 38. Transparent newtype

```text
@repr(transparent)
distinct UserId = u64
```

cho phép ABI-compatible representation với `u64` theo quy tắc `repr`.

Nhưng semantic type vẫn khác.

---

# 39. Trait auto implementation

Compiler có thể tự derive:

```text
Copy
Send
Share
```

nhưng phải theo semantic rules.

Ví dụ:

```text
struct A {
    x: i32
}
```

có thể tự:

```text
Copy
Send
Share
```

Trong khi:

```text
struct B {
    file: File
}
```

không Copy.

---

# 40. `Copy` không phải trait bình thường

Đây là điểm cần giữ.

Compiler có thể cho:

```text
impl Copy for User
```

nhưng `Copy` ảnh hưởng ownership semantics.

Do đó:

> `Copy` là **compiler-known semantic trait**.

Tương tự:

```text
Drop
Send
Share
```

không nên được coi như trait library hoàn toàn bình thường.

---

# 41. Trait object

Generic:

```text
fn draw<T: Drawable>(x: T)
```

→ static dispatch.

Dynamic:

```text
fn draw(x: dyn Drawable)
```

→ dynamic dispatch.

Không implicit conversion.

---

# 42. `dyn Trait` phải explicit

Không:

```text
Drawable x = Circle(...)
```

nếu `Drawable` là dynamic trait object.

Phải:

```text
Box<dyn Drawable>
```

hoặc:

```text
Arc<dyn Drawable>
```

nếu ownership semantics cần.

---

# 43. Vtable

Chỉ tồn tại khi:

```text
dyn Trait
```

được sử dụng.

Concrete:

```text
Circle
```

không có hidden vtable pointer.

Đây là một trong các điểm quan trọng để đạt binary/performance tốt.

---

# 44. Generic dispatch

Ví dụ:

```text
fn draw<T: Drawable>(x: T) {
    x.draw()
}
```

MIR sau trait solving:

```text
call Circle.draw
```

nếu:

```text
T = Circle
```

Không còn trait lookup runtime.

---

# 45. Dynamic dispatch

```text
fn draw(x: dyn Drawable) {
    x.draw()
}
```

MIR:

```text
load vtable
indirect_call slot(draw)
```

Đây là runtime cost **explicitly requested by programmer**.

---

# 46. Không allocation khi chuyển sang dyn

Điểm này phải freeze:

```text
Circle → dyn Drawable
```

không tự động:

```text
heap allocate
```

Nếu API yêu cầu owned trait object:

```text
Box<dyn Drawable>
```

thì allocation là do `Box` semantics.

---

# 47. Trait solver và method resolution

Thứ tự đã chốt:

```text
1. inherent method
2. trait implementation
3. explicitly imported extension
4. generic extension
```

Nếu nhiều candidate cùng độ ưu tiên:

```text
compile error
```

Không chọn “gần nhất” theo heuristic khó đoán.

---

# 48. Generic extension

Ví dụ:

```text
fn clamp<T: Ord>(self: T, min: T, max: T) -> T
```

có thể gọi:

```text
x.clamp(0, 100)
```

nếu extension được import.

Compiler resolve:

```text
clamp(x, 0, 100)
```

---

# 49. Trait default implementation

```text
trait Printable {
    fn print(self) {
        ...
    }
}
```

Nếu type không override:

```text
impl Printable for User {}
```

dùng default.

Nếu override:

```text
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

implementation cụ thể thắng.

Không cần `override`.

---

# 50. Specialization

V1:

```text
NO unrestricted specialization
```

Sau này có thể thêm:

```text
@specialize
```

nhưng phải có coherence model rõ.

Tôi không muốn compiler v1 phụ thuộc vào specialization để solve generic code.

---

# 51. Generic recursion

Ví dụ:

```text
fn foo<T>() {
    foo<Box<T>>()
}
```

có thể tạo vô hạn monomorphization.

Compiler phải phát hiện:

```text
infinite instantiation
```

và diagnostic rõ ràng.

---

# 52. Generic compile-time evaluation

Ví dụ:

```text
const N = 1024

fn zero<T>() -> T {
    ...
}
```

Comptime và generic solver có thể phối hợp:

```text
T
N
```

nhưng phải có giới hạn recursion/instantiation để compiler không bị DoS.

---

# 53. Generic specialization pipeline

Tôi đề xuất compiler:

```text
Generic HIR
    ↓
Trait Solve
    ↓
Substitution
    ↓
Monomorphized HIR
    ↓
Typed MIR
    ↓
Optimization
```

Không monomorphize trước khi trait resolution xong.

---

# 54. Generic metadata

Compiler lưu:

```text
GenericDef {
    params
    constraints
    body
}
```

và:

```text
Instantiation {
    generic_id
    type_args
    const_args
}
```

Cache theo:

```text
generic_id
+
type arguments
+
const arguments
+
target ABI context
```

---

# 55. Incremental compilation

Nếu:

```text
fn sort<T: Ord>(...)
```

không thay đổi và:

```text
sort<User>
```

đã compile:

compiler có thể reuse semantic/codegen artifact.

Điều này rất phù hợp với `.axm` semantic artifacts mà ta đã định hướng.

---

# 56. Generic code bloat control

Ba tầng:

```text
1. Monomorphization
2. Machine/code equivalence dedup
3. Link-time dead stripping
```

Ví dụ chương trình chỉ dùng:

```text
sort<User>
```

thì:

```text
sort<i32>
sort<f64>
```

không tồn tại trong binary.

---

# 57. Trait solver không được chạy trong optimizer

Trait resolution phải hoàn tất trước:

```text
MIR verification
```

Optimizer chỉ thấy:

```text
direct call
indirect call
```

Điều này làm backend đơn giản.

---

# 58. Đây là một invariant rất quan trọng

```text
ATRAIT-61 — Trait Resolution Completes Before MIR Verification

ATRAIT-62 — MIR Contains Resolved Dispatch

ATRAIT-63 — Generic Constraints Do Not Reach Machine IR

ATRAIT-64 — Static Generic Dispatch Has No Required Runtime Metadata

ATRAIT-65 — Dynamic Dispatch Requires Explicit dyn Trait

ATRAIT-66 — Dynamic Dispatch Does Not Imply Allocation

ATRAIT-67 — Generic Instantiation Is Cacheable

ATRAIT-68 — Generic Code May Be Deduplicated

ATRAIT-69 — Unrestricted Specialization Is Not Required By v1

ATRAIT-70 — Coherence Must Be Deterministic

ATRAIT-71 — Trait Resolution Must Be Deterministic

ATRAIT-72 — Auto Traits Are Compiler-Known Semantic Properties

ATRAIT-73 — Copy Is Semantic, Not Merely Bitwise

ATRAIT-74 — Trait Solver Failure Is A Compile-Time Diagnostic
```

---

# 59. Kiến trúc solver

Tôi đề xuất tách:

```text
Trait Solver
├── Type Unifier
├── Impl Index
├── Goal Engine
├── Associated Type Resolver
├── Auto Trait Solver
├── Coherence Checker
└── Cycle Detector
```

Ví dụ query:

```text
T: Add<U>
```

→ `Goal`.

Solver tìm candidates.

```text
impl Add<U> for Vec<U>
```

Unify.

Nếu thành công:

```text
Output = ...
```

Sau đó fact được ghi vào semantic facts engine.

---

# 60. Cycle detection

Ví dụ:

```text
trait A: B {}
trait B: A {}
```

hoặc recursive generic constraint.

Solver phải có:

```text
Goal stack
Cycle detection
Coinductive policy
```

Nhưng v1 nên tránh các quy tắc coinductive quá phức tạp.

Nếu cycle không được phép:

```text
diagnostic: recursive trait obligation
```

---

# 61. Một điểm tôi muốn đơn giản hóa mạnh

Không đưa Haskell-style:

```text
type classes
higher-kinded types
associated type families
dependent types
implicit parameters
```

vào v1.

Axiom đã có:

```text
generics
traits
associated types
const generics
comptime
```

đã đủ mạnh cho systems programming.

---

# 62. Kết quả cuối cùng

Axiom generic code:

```text
fn process<T: Processable>(x: T) -> Result<T, Error> {
    x.process()
}
```

trải qua:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Trait Solver
 ↓
T = User
 ↓
Monomorphization
 ↓
MIR
 ↓
direct call User.process
 ↓
Inlining
 ↓
Optimization
 ↓
Machine code
```

Không còn:

```text
generic runtime
reflection
vtable
type descriptor
GC
```

nếu programmer không yêu cầu.

---

# 63. Đây chính là “zero-cost abstraction” thực tế của Axiom

Không phải tuyên bố:

> abstraction luôn miễn phí.

Mà là:

> **Abstraction không tạo runtime cost nếu compiler có thể chứng minh rằng semantics không yêu cầu cost đó.**

Ví dụ:

```text
struct Vec2
trait Add
generic function
extension method
closure
comptime
```

đều có thể biến thành machine code trực tiếp.

Ngược lại:

```text
dyn Trait
Arc
Mutex
atomic
stable address
FFI
```

có cost nếu semantics thực sự yêu cầu.

---

# 64. Bước tiếp theo

Đến đây tầng semantic chính gần như đã đủ. Phần tiếp theo nên là một trong những phần **cực kỳ quan trọng đối với mục tiêu “C/C++ performance nhưng dễ lập trình”**:

# **OPT-001 — Optimization Contract**

Cần chốt chính xác compiler được phép làm gì:

```text
Inlining
Constant folding
Dead code elimination
SROA
Scalar replacement
Escape analysis
Allocation elimination
NRVO / return optimization
Alias analysis
Loop optimization
Vectorization
Bounds-check elimination
Devirtualization
Generic code merging
PGO
LTO
IPO
Tail calls
Stack/register promotion
Function multiversioning
```

và quan trọng nhất:

> **Compiler được phép tối ưu đến đâu mà không biến semantics Axiom thành thứ “lúc chạy debug một kiểu, release một kiểu”?**

Đây cũng là nơi ta sẽ chốt **memory model + alias guarantees + optimizer legality**, đặc biệt liên quan đến quyết định trước đây của bạn về **flat memory, pointer/reference và việc không muốn borrow checker làm phiền programmer**.