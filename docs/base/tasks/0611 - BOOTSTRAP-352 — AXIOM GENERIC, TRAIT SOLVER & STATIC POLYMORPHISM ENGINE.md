# BOOTSTRAP-352 — AXIOM GENERIC, TRAIT SOLVER & STATIC POLYMORPHISM ENGINE

Sau `BOOTSTRAP-351`, Axiom đã khóa function/call/ABI/control-flow. Bước tiếp theo nên hoàn thiện **generic + trait system**, vì đây là phần quyết định Axiom có đạt được mục tiêu:

> **Abstraction mạnh ở source, nhưng sau compilation không còn abstraction overhead nếu không cần thiết.**

Đây cũng là nền móng trực tiếp cho `Vec<T>`, `Map<K,V>`, SIMD generic, allocator, collection, GPU API, numerical library, FFI wrapper và standard library.

---

# 1. Triết lý

Axiom không dùng inheritance làm cơ chế polymorphism chính.

Có 3 tầng:

```text
Concrete type
     │
     ├── Generic static polymorphism
     │
     ├── Trait constraint
     │
     └── dyn Trait → explicit dynamic polymorphism
```

Mặc định:

> **Static dispatch.**

Dynamic dispatch chỉ xuất hiện khi source code yêu cầu.

---

# 2. Generic cơ bản

Ví dụ:

```text
fn identity<T>(x: T) -> T {
    x
}
```

`T` là compile-time type parameter.

Không có runtime type information mặc định.

```text
identity<i32>(10)
identity<f64>(3.14)
```

có thể trở thành hai code instance độc lập.

---

# 3. Generic type

```text
struct Box<T> {
    value: T
}
```

Mỗi specialization:

```text
Box<i32>
Box<f64>
Box<MyStruct>
```

là một semantic type riêng trong `TypeDB`.

---

# 4. Generic không mặc định tạo code riêng

Đây là điểm quan trọng.

Compiler có thể chọn:

```text
Monomorphization
```

hoặc:

```text
Shared generic code
```

nếu ABI/representation cho phép.

Ví dụ:

```text
fn identity<T>(x: T) -> T
```

với một số `T` có cùng ABI có thể được chia sẻ code.

Nhưng:

```text
fn add<T: Numeric>(a: T, b: T) -> T
```

có thể được specialize hoàn toàn.

Source semantics không phụ thuộc chiến lược này.

---

# 5. Generic specialization

Pipeline:

```text
Generic Function
      ↓
Constraint Collection
      ↓
Trait Resolution
      ↓
Generic Instance
      ↓
Specialization
      ↓
Typed MIR
```

Ví dụ:

```text
fn sum<T: Add + Zero>(a: T, b: T) -> T
```

với:

```text
sum<i32>
```

compiler biết:

```text
Add for i32
Zero for i32
```

và có thể trực tiếp generate machine arithmetic.

Không có:

```text
vtable
reflection
runtime type lookup
```

---

# 6. Trait

Trait mô tả capability/behavior:

```text
trait Add<Rhs, Output> {
    fn add(self, rhs: Rhs) -> Output
}
```

Type thực thi:

```text
impl Add<i32, i32> for i32 {
    fn add(self, rhs: i32) -> i32 {
        ...
    }
}
```

Trait không phải class.

Không chứa:

```text
object identity
object header
inheritance state
```

---

# 7. Trait là compile-time contract

Khi viết:

```text
fn sum<T: Add>(a: T, b: T) -> T
```

compiler phải chứng minh:

```text
T implements Add
```

trước khi tạo executable.

Không có runtime fallback.

---

# 8. Multiple constraints

Có thể viết:

```text
fn process<T: Read + Write + Send>(x: T)
```

Semantic:

```text
T implements Read
T implements Write
T is Send
```

Compiler biến thành constraint set:

```text
C = {
    Implements(T, Read),
    Implements(T, Write),
    Implements(T, Send)
}
```

---

# 9. `where`

Để tránh signature quá dài:

```text
fn process<T, U>(x: T, y: U)
where
    T: Read + Send,
    U: Write,
    T: Convert<U>
```

`where` chỉ là syntax khác cho cùng constraint model.

Không tạo một cơ chế type checking thứ hai.

---

# 10. Associated type

Trait có thể có associated type:

```text
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Ví dụ:

```text
impl Iterator for MyIterator {
    type Item = i32
}
```

Compiler phải resolve:

```text
Iterator::Item
```

thành concrete type.

---

# 11. Associated constant

Cho phép:

```text
trait Numeric {
    const ZERO: Self
    const ONE: Self
}
```

Compiler có thể constant-fold.

Không cần runtime lookup.

---

# 12. Associated function

Trait có thể khai báo:

```text
trait Factory {
    fn create() -> Self
}
```

Không cần object instance.

Static dispatch:

```text
T::create()
```

---

# 13. Default implementation

```text
trait Printable {
    fn print(self) {
        ...
    }
}
```

Concrete implementation có thể override:

```text
impl Printable for MyType {
    fn print(self) {
        ...
    }
}
```

Không cần:

```text
override
```

vì compiler biết đây là trait implementation.

---

# 14. Không có class inheritance

Không cho:

```text
class B : A
```

Core.

Thay vào đó:

```text
struct B { ... }

impl Trait for B { ... }
```

Nếu muốn reuse implementation:

```text
trait ABehavior { ... }

impl ABehavior for B { ... }
```

hoặc composition.

---

# 15. Extension methods

Một function:

```text
fn magnitude(self: Vec3) -> f32
```

có thể được gọi:

```text
v.magnitude()
```

nếu function nằm trong scope/import hợp lệ.

Method resolution không cần modify type gốc.

---

# 16. Method resolution

Thứ tự cố định:

```text
1. Inherent method
2. Trait method
3. Explicitly imported extension
4. Generic extension
```

Nếu có nhiều candidate ngang hàng:

```text
compile error: ambiguous method
```

Không chọn dựa vào import order.

---

# 17. Coherence

Axiom cần coherence rule để tránh hai package định nghĩa conflicting implementation.

Ví dụ không cho package X tự ý:

```text
impl SomeTrait for ForeignType
```

nếu cả trait và type đều thuộc package khác.

Áp dụng orphan/coherence rules.

Mục tiêu:

> Một `(Trait, Type)` pair phải có semantic implementation duy nhất trong compilation universe.

---

# 18. Negative implementations

Có thể cần biểu diễn:

```text
impl !Send for SomeType
```

nhưng không nên đưa full negative trait system vào Core v1 nếu chưa cần.

Thay vào đó compiler có thể có intrinsic negative facts:

```text
NonSend
NonShare
NonCopy
```

được suy luận từ type structure.

Negative impl mở rộng chỉ đưa vào khi trait ecosystem thực sự cần.

---

# 19. Auto traits

Một số trait được compiler tự suy luận:

```text
Copy
Send
Share
Sized
FfiSafe
GpuLegal
```

Ví dụ:

```text
struct Pair<T, U> {
    a: T
    b: U
}
```

`Send<Pair<T,U>>` nếu:

```text
Send<T>
Send<U>
```

và không có field/resource đặc biệt ngăn cản.

---

# 20. Trait categories

Không nên để mọi trait có cùng compiler semantics.

Phân loại:

```text
BehaviorTrait
MarkerTrait
AutoTrait
OperatorTrait
ConversionTrait
UnsafeTrait
FFITrait
GPUCapabilityTrait
```

Ví dụ:

```text
Send
```

không phải behavior dispatch trait.

---

# 21. Trait object

Dynamic polymorphism:

```text
dyn Drawable
```

là explicit.

Ví dụ:

```text
fn render(x: view<dyn Drawable>)
```

Compiler tạo dynamic dispatch representation.

Conceptually:

```text
data pointer
vtable pointer
```

Nhưng layout là ABI/compiler detail.

---

# 22. Trait object không tự động xuất hiện

Không được implicit:

```text
Drawable
```

→

```text
dyn Drawable
```

vì như vậy sẽ làm abstraction boundary khó đoán và có thể tạo allocation/indirection.

Programmer phải yêu cầu dynamic dispatch.

---

# 23. Object safety

Không phải trait nào cũng có thể trở thành:

```text
dyn Trait
```

Ví dụ trait yêu cầu:

```text
fn create() -> Self
```

thường không thể gọi qua trait object.

Compiler phải phân tích `DynSafe`/object-safety.

---

# 24. Dynamic dispatch ABI

Trait object cần metadata:

```text
TraitObjectMetadata {
    method_table
    type_metadata
    drop_fn
    size
    alignment
}
```

Nhưng **không nhất thiết tất cả field đều nằm trong runtime object**.

Compiler có thể tối ưu vtable theo target/use-site.

---

# 25. Devirtualization

Ngay cả khi source viết:

```text
dyn Trait
```

compiler vẫn có thể chứng minh target duy nhất:

```text
obj.draw()
```

→ direct call.

Điều này đặc biệt quan trọng cho performance.

Dynamic syntax không bắt buộc dynamic machine instruction nếu compiler chứng minh được static target.

---

# 26. Trait solver

Đây là subsystem quan trọng nhất.

Input:

```text
T: TraitA
TraitB<T>: TraitC
```

Output:

```text
Proven
NotProven
Ambiguous
Error
```

Solver phải xử lý:

- generic unification;
- associated types;
- trait bounds;
- supertraits;
- generic impls;
- auto traits;
- coherence;
- recursion;
- normalization.

---

# 27. Trait resolution example

```text
trait Add<R> {
    type Output
}

fn plus<T: Add<T>>(a: T, b: T) -> T
```

Khi instantiate:

```text
plus<i32>
```

solver cần chứng minh:

```text
ImplExists(
    Add<i32>
)
```

và:

```text
Output(Add<i32>) == i32
```

---

# 28. Associated type normalization

Ví dụ:

```text
<T as Iterator>::Item
```

solver phải normalize:

```text
<T as Iterator>::Item
```

→ concrete type nếu đủ facts.

Nếu chưa đủ:

```text
Ambiguous
```

Không được tự đoán.

---

# 29. Trait solver termination

Trait recursion phải có giới hạn.

Ví dụ pathological:

```text
trait A<T>
impl<T: A<T>> A<T>
```

Compiler không được chạy vô hạn.

Cần:

```text
cycle detection
depth limit
candidate memoization
canonicalization
coinductive rules where appropriate
```

---

# 30. Canonicalization

Solver nên canonicalize inference variables:

```text
<T>
<U>
```

để các query tương đương có thể cache chung.

Ví dụ:

```text
CanImplement(T, Add)
```

và:

```text
CanImplement(U, Add)
```

có cùng canonical query shape.

---

# 31. Incremental trait solving

Trait query là một trong những điểm dễ khiến compiler chậm.

Do đó:

```text
TraitQueryCache
```

phải là một phần của CompilerDB.

Cache key bao gồm:

```text
trait
self type
arguments
environment
edition
semantic fingerprint
```

Nếu dependency không đổi:

```text
reuse result
```

---

# 32. Ambiguity không phải failure ngay

Ví dụ:

```text
<T as Trait>::Assoc
```

chưa đủ constraint.

Solver trả:

```text
Ambiguous
```

Type inference có thể thêm constraint rồi solve lại.

Chỉ khi compilation boundary yêu cầu concrete answer mà vẫn ambiguous:

```text
compile error
```

---

# 33. Type inference

Axiom có thể hỗ trợ inference:

```text
let x = Vec3(1.0, 2.0, 3.0)
```

nhưng không nên trở thành dynamic inference kiểu scripting language.

Inference phải:

- deterministic;
- local khi có thể;
- predictable;
- không phụ thuộc optimizer;
- không phụ thuộc declaration order ngoài scope rules.

---

# 34. Numeric generic interaction

Task `350` đã định nghĩa numeric traits.

Ví dụ:

```text
fn dot<T: Numeric>(a: view<T>, b: view<T>) -> T
```

Có thể specialize:

```text
dot<f32>
dot<f64>
dot<i32>
vectorized_dot<f32, 8>
```

Trait solver và SIMD specialization phải phối hợp, không tạo hai type systems riêng.

---

# 35. Const generics

Const generic v0.1:

```text
struct Array<T, const N: usize>
```

Cho phép:

```text
Array<f32, 4>
Array<f32, 16>
```

Compiler có thể biết `N` tại compile time.

Ban đầu chỉ cần:

```text
usize
isize
u64
i64
bool
```

làm const parameter.

Không cần full dependent type system.

---

# 36. Const parameter equality

Compiler có thể prove:

```text
N == 4
```

và:

```text
N + 1 == 5
```

trong phạm vi hỗ trợ.

Nhưng không biến Axiom thành theorem prover.

Mục tiêu là **practical compile-time reasoning**, không phải dependent type language.

---

# 37. Specialization policy

Axiom v1 không nên cho programmer tự do viết:

```text
impl<T> Trait for T
impl<i32> Trait for i32
```

rồi yêu cầu compiler chọn specialization tùy ý.

Điều này dễ tạo ambiguity.

Ban đầu:

> **Coherent, deterministic, non-overlapping implementations.**

Compiler optimization có thể specialize machine code mà không thay đổi trait resolution.

---

# 38. Trait dispatch và ownership

Trait method vẫn phải obey capability model.

Ví dụ:

```text
trait Sort {
    fn sort(self: mut_view<Self>)
}
```

Trait object không được trở thành loophole để tạo alias mutable.

Verifier vẫn kiểm tra:

```text
view
mut_view
Move
Drop
Send
Share
```

sau khi dispatch target được resolve.

---

# 39. Trait + async

Trait có thể chứa:

```text
async fn fetch(...)
```

nhưng semantic là:

```text
Future<...>
```

Trait solver chỉ resolve function signature.

Async lowering xảy ra sau đó.

Dynamic async trait object là vấn đề ABI riêng:

```text
dyn AsyncTrait
```

có thể cần explicit boxed/pinned future representation trong library/ABI.

Không đưa implicit heap allocation vào trait core.

---

# 40. Trait + GPU

Có thể có:

```text
trait GpuKernel
```

nhưng compiler phải distinguish:

```text
trait resolution
```

với:

```text
GpuLegal
```

Một type có trait không có nghĩa implementation tự động hợp lệ trên GPU.

---

# 41. Trait + FFI

FFI-safe abstraction:

```text
trait FfiSafe
```

phải được compiler verify theo layout/ABI rules.

Không được coi:

```text
struct<T>
```

là FFI-safe chỉ vì từng field riêng lẻ safe nếu generic representation chưa được xác định.

---

# 42. Generic error diagnostics

Compiler phải giải thích được:

```text
cannot satisfy T: Add<U>
```

theo structured proof tree:

```text
Required:
    T: Add<U>

Candidate:
    Add<i32> for i32

Rejected:
    T is unconstrained
```

AI tooling có thể lấy trực tiếp proof tree thay vì parse text error.

---

# 43. CompilerDB additions

```text
GenericDB
GenericParameterDB
GenericInstanceDB
GenericConstraintDB
TraitDB
TraitImplDB
TraitSolverDB
TraitQueryDB
TraitCandidateDB
TraitNormalizationDB
AssociatedTypeDB
AssociatedConstDB
AutoTraitDB
CoherenceDB
DynTraitDB
ObjectSafetyDB
DispatchDB
SpecializationDB
ConstGenericDB
TypeInferenceDB
```

---

# 44. Generic compilation pipeline

```text
Source
  ↓
Generic AST
  ↓
HIR
  ↓
Constraint Generation
  ↓
Trait Solver
  ↓
Type/Associated-Type Normalization
  ↓
Generic Instance
  ↓
Coherence Verification
  ↓
Monomorphization / Code Sharing
  ↓
Typed MIR
```

---

# 45. Proof-oriented trait solving

Trait solver không chỉ trả:

```text
true / false
```

mà nên tạo:

```text
TraitProof
```

Ví dụ:

```text
TraitProof {
    goal: Add<i32>,
    source: ImplId(42),
    obligations: [],
    fingerprint: ...
}
```

Các compiler pass sau có thể dùng proof này.

Không cần resolve lại cùng một fact ở từng pass.

---

# 46. Generic ABI

Sau specialization, compiler phải biết:

```text
GenericInstance
    ↓
Concrete Types
    ↓
Layout
    ↓
ABI
```

Không để generic source code trực tiếp quyết định machine ABI.

---

# 47. Zero-cost guarantee

Không tuyên bố:

> mọi generic đều zero-cost.

Thay vào đó contract chính xác hơn:

> **Generic abstraction không tự tạo runtime dispatch hoặc allocation. Nếu semantic contract không yêu cầu runtime mechanism, compiler được phép erase abstraction hoàn toàn.**

Đây phù hợp với triết lý Axiom.

---

# 48. Invariants

```text
ATRAIT-01
Generic abstraction is compile-time by default.

ATRAIT-02
Static dispatch is the default polymorphism mechanism.

ATRAIT-03
Dynamic dispatch requires explicit dyn Trait semantics.

ATRAIT-04
Traits do not imply object headers.

ATRAIT-05
Trait implementation is compile-time semantic evidence.

ATRAIT-06
Trait resolution is deterministic.

ATRAIT-07
Trait ambiguity is never resolved by arbitrary candidate ordering.

ATRAIT-08
Associated types are normalized through the trait solver.

ATRAIT-09
Associated-type ambiguity remains ambiguous until sufficient constraints exist.

ATRAIT-10
Trait solver must terminate.

ATRAIT-11
Trait queries are incrementally cacheable.

ATRAIT-12
Coherence prevents conflicting trait implementations.

ATRAIT-13
Generic specialization cannot alter semantic trait resolution.

ATRAIT-14
Monomorphization is an implementation strategy, not source semantics.

ATRAIT-15
Code sharing is permitted when ABI and semantics allow it.

ATRAIT-16
Auto traits are derived from verified type structure.

ATRAIT-17
Send and Share remain distinct capabilities.

ATRAIT-18
Copy and Clone remain distinct semantics.

ATRAIT-19
Trait dispatch cannot bypass ownership verification.

ATRAIT-20
Trait objects cannot bypass capability safety.

ATRAIT-21
Devirtualization may replace dynamic dispatch when proven safe.

ATRAIT-22
Generic inference is deterministic.

ATRAIT-23
Const generics do not imply a general dependent type system.

ATRAIT-24
Generic constraints are represented explicitly in compiler IR.

ATRAIT-25
Trait proofs can be reused by later compiler passes.

ATRAIT-26
FFI safety requires explicit ABI/layout verification.

ATRAIT-27
GPU legality is distinct from trait implementation.

ATRAIT-28
Async trait semantics are distinct from ordinary synchronous dispatch.

ATRAIT-29
Generic abstractions may be erased completely when unobservable.

ATRAIT-30
No generic mechanism may silently introduce runtime allocation or dynamic dispatch.
```

---

# 49. Definition of Done

`BOOTSTRAP-352` hoàn thành khi Axiom có đầy đủ:

- generic functions;
- generic structs/enums;
- trait definitions;
- trait implementations;
- trait bounds;
- `where`;
- associated types;
- associated constants;
- associated functions;
- default trait methods;
- extension methods;
- deterministic method resolution;
- coherence/orphan rules;
- auto traits;
- `Copy/Send/Share/Sized/FfiSafe/GpuLegal`;
- dynamic `dyn Trait`;
- object-safety checking;
- devirtualization;
- generic specialization;
- code sharing;
- const generics;
- type inference;
- associated-type normalization;
- canonical trait queries;
- incremental trait solver;
- trait proof artifacts;
- generic ABI lowering;
- structured generic diagnostics;
- conformance tests cho toàn bộ trait/generic semantics.

### Kiến trúc cốt lõi sau task này

Axiom sẽ có một đường đi rất rõ:

```text
              SOURCE
                 │
        ┌────────▼────────┐
        │ Generic + Trait │
        │   Abstraction   │
        └────────┬────────┘
                 │
          Trait Proofs
                 │
        Generic Specialization
                 │
        ┌────────▼────────┐
        │ Concrete Typed  │
        │      MIR        │
        └────────┬────────┘
                 │
           Optimization
                 │
           Machine Code
```

Tức là **programmer được phép viết abstraction rất cao cấp, nhưng abstraction đó không mặc định tồn tại ở runtime**. Đây chính là cơ chế quan trọng để Axiom đạt mục tiêu “ngôn ngữ hiện đại nhưng hiệu năng kiểu systems language”.