# BOOTSTRAP-410 — TRAIT SYSTEM, METHOD RESOLUTION, OVERLOADING, ASSOCIATED ITEMS & COHERENCE

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc trực tiếp:** 408 Name Resolution, 409 Type System  
**Mục tiêu:** biến Trait/Impl/Method thành một hệ thống semantic hoàn chỉnh, đủ để compiler triển khai ngay mà không cần dựa vào class/inheritance.

---

## 410.1. Vai trò của Trait System

Axiom không có:

- class inheritance;
- virtual method mặc định;
- implicit interface implementation;
- implicit user-defined conversion;
- global overload namespace.

Axiom dùng:

```text
Struct
   ↓
Inherent Functions
   +
Traits
   +
Trait Implementations
   +
Extension Functions
```

Trait là **behavior contract**, không phải class.

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Có thể gọi:

```axiom
v.length()
```

nhưng semantic representation vẫn là:

```axiom
length(v)
```

Compiler không tạo một method table cho `Vec2`.

---

# 410.2. Ba loại function gắn với một type

Method resolution phải phân biệt rõ:

### A. Inherent function

Function thuộc trực tiếp về type:

```axiom
fn length(self: Vec2) -> f32
```

### B. Trait function

Function đến từ trait:

```axiom
trait Printable {
    fn print(self)
}
```

và:

```axiom
impl Printable for Vec2 {
    fn print(self) {
        ...
    }
}
```

### C. Extension function

Function ở module khác nhưng có receiver phù hợp:

```axiom
fn normalize(self: Vec2) -> Vec2
```

Extension function không làm thay đổi type.

Nó chỉ được đưa vào method lookup khi module/trait/function đã được import phù hợp.

---

# 410.3. Thứ tự Method Resolution

Khi compiler gặp:

```axiom
value.foo(a, b)
```

compiler không chọn candidate theo thứ tự import.

Thứ tự semantic:

```text
1. Inherent exact candidate
2. Inherent generic candidate
3. Explicitly available trait candidate
4. Explicit extension candidate
5. Generic extension candidate
6. Reject / ambiguity
```

Nhưng có một nguyên tắc quan trọng:

> **Priority chỉ được áp dụng giữa các candidate semantic hợp lệ.**

Không được dùng priority để che giấu hai impl trait mâu thuẫn.

Ví dụ:

```axiom
struct Vec2 {}

fn foo(self: Vec2) {}
fn foo<T>(self: T) {}
```

`foo(v)` chọn overload cụ thể hơn nếu cả hai hợp lệ.

---

# 410.4. Method Resolution không thuộc Name Resolver

`ARES-408` chỉ giải quyết:

```text
foo → SymbolId
```

Nhưng:

```axiom
v.foo()
```

không thể giải quyết chỉ bằng tên `foo`.

Compiler phải thực hiện:

```text
Expression
 ↓
Receiver Type
 ↓
Candidate Discovery
 ↓
Trait/Impl Candidate Filtering
 ↓
Generic Constraint Solving
 ↓
Overload Ranking
 ↓
Method Selection
 ↓
Resolved FunctionId + Substitution
```

Do đó Method Resolution là một semantic phase riêng.

---

# 410.5. Candidate

Mỗi candidate có semantic record:

```text
MethodCandidate {
    FunctionId
    OwnerType
    TraitId?
    ImplId?
    SourceKind
    ReceiverType
    GenericParameters
    Constraints
    Substitution
    ConversionCost
    Visibility
    DispatchKind
}
```

`SourceKind`:

```text
INHERENT
TRAIT
EXTENSION
GENERIC_EXTENSION
```

Compiler không dùng text matching để chọn candidate.

---

# 410.6. Overloading

Axiom cho phép overload function.

Ví dụ:

```axiom
fn print(x: i32)
fn print(x: f32)
fn print(x: Text)
```

Nhưng overload resolution phải deterministic.

Candidate được đánh giá theo:

```text
1. Exact type match
2. Safe widening
3. Explicitly permitted implicit conversion
4. Generic specialization
5. Trait constraint satisfaction
```

Không có:

```text
"compiler thấy cái nào có vẻ phù hợp"
```

Nếu hai candidate có cùng semantic rank:

```text
compile error: ambiguous overload
```

---

# 410.7. Không có implicit user conversion

Ví dụ:

```axiom
struct Meter {
    value: f32
}

struct Kilometer {
    value: f32
}
```

Compiler không được tự động biến:

```axiom
Meter → Kilometer
```

chỉ vì programmer định nghĩa một function conversion.

Phải viết explicit:

```axiom
fn to_kilometer(m: Meter) -> Kilometer
```

hoặc protocol chuyển đổi rõ ràng được compiler công nhận.

Điều này tránh:

- overload ambiguity;
- hidden computation;
- unexpected allocation;
- hidden precision loss.

---

# 410.8. Conversion Protocol

Axiom có thể định nghĩa các conversion protocol chuẩn trong library/compiler.

Ví dụ semantic:

```text
Convert<T, U>
TryConvert<T, U>
```

Nhưng chúng **không tự động được áp dụng** trong mọi context.

Explicit conversion:

```axiom
let km: Kilometer = convert(meter)
```

Nếu language muốn hỗ trợ một số coercion đặc biệt, chúng phải nằm trong danh sách compiler-defined coercions.

Core không cho phép mỗi library tự tạo implicit conversion rule.

---

# 410.9. Generic Method Resolution

Ví dụ:

```axiom
trait Add<Rhs> {
    type Output
    fn add(self, rhs: Rhs) -> Output
}
```

và:

```axiom
impl Add<Vec2> for Vec2 {
    type Output = Vec2

    fn add(self, rhs: Vec2) -> Vec2 {
        ...
    }
}
```

Khi gặp:

```axiom
a.add(b)
```

compiler phải giải:

```text
Type(a) = Vec2
Type(b) = Vec2

Goal:
    Add<Vec2> for Vec2

Normalize:
    Output = Vec2

Result:
    FunctionId(...)
```

---

# 410.10. Associated Types

Trait có thể khai báo associated type:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Impl:

```axiom
impl Iterator for MyIterator {
    type Item = i32
}
```

Compiler phải normalize:

```text
<MyIterator as Iterator>::Item
```

→

```text
i32
```

Associated type là semantic type identity, không phải text alias.

---

# 410.11. Associated Constants

Trait:

```axiom
trait Numeric {
    const ZERO: Self
    const ONE: Self
}
```

Impl:

```axiom
impl Numeric for i32 {
    const ZERO: i32 = 0
    const ONE: i32 = 1
}
```

Associated constant có:

```text
TraitId
ImplId
ItemId
Type
Value
```

Nếu value cần compile-time, compiler phải kiểm tra nó bằng Comptime system.

---

# 410.12. Associated Functions

Trait có thể chứa function không có receiver:

```axiom
trait Construct {
    fn create() -> Self
}
```

Gọi:

```axiom
T::create()
```

Compiler giải quyết theo:

```text
TypeId
TraitId
ImplId
FunctionId
```

Không cần object/class static-method concept.

---

# 410.13. Default Trait Method

Trait:

```axiom
trait Printable {
    fn print(self) {
        ...
    }
}
```

Impl có thể không override:

```axiom
impl Printable for Vec2 {}
```

→ dùng default implementation.

Có thể override:

```axiom
impl Printable for Vec2 {
    fn print(self) {
        ...
    }
}
```

Không cần:

```axiom
override
```

Compiler biết function đang implement trait item.

---

# 410.14. Override phải đúng signature

Nếu trait yêu cầu:

```axiom
trait Foo {
    fn process(self, x: i32) -> bool
}
```

mà impl viết:

```axiom
fn process(self, x: f32) -> bool
```

đây **không phải override**.

Nó là function khác và impl bị lỗi vì trait item chưa được implement.

Không có cơ chế "gần giống signature".

---

# 410.15. Trait Coherence

Axiom phải đảm bảo:

```text
mỗi (TraitId, TypeId)
```

chỉ có **một implementation hợp lệ trong cùng semantic universe**.

Không cho:

```axiom
impl Display for Vec2 {}
```

ở hai package khác nhau rồi để linker quyết định.

Đây là lỗi compile-time.

---

# 410.16. Orphan Rule

Một package chỉ được implement trait nếu:

```text
Trait là local
OR
Type là local
```

Ví dụ package A sở hữu:

```text
Vec2
```

package B sở hữu:

```text
Printable
```

package C không được tùy tiện:

```axiom
impl Printable for Vec2 {}
```

nếu cả `Printable` và `Vec2` đều external.

Điều này ngăn dependency graph làm thay đổi semantic behavior.

---

# 410.17. Coherence Universe

Coherence không đơn giản là nhìn source hiện tại.

Compiler phải xác định:

```text
Package Graph
+
Feature Configuration
+
Target Semantic Configuration
+
Dependency Versions
```

tạo thành một **Semantic Universe**.

Một impl hợp lệ trong universe A không mặc nhiên hợp lệ trong universe B.

Điều này quan trọng với:

- feature;
- conditional compilation;
- platform;
- specialization;
- plugin;
- generated code.

---

# 410.18. Specialization

Axiom **không cho phép unrestricted specialization trong Core v1**.

Ví dụ không cho:

```axiom
impl<T> Foo for T {}
impl Foo for i32 {}
```

nếu cả hai cùng áp dụng và không có quy tắc specialization rõ ràng.

Lý do:

```text
coherence
+
predictable dispatch
+
compiler termination
+
incremental compilation
```

quan trọng hơn sự tiện lợi.

Nếu cần specialization sau này, nó phải là một semantic feature riêng với ordering/proof rõ ràng.

---

# 410.19. Trait Bounds

Generic:

```axiom
fn print_all<T: Printable>(x: T)
```

semantic constraint:

```text
T implements Printable
```

Compiler tạo goal:

```text
Printable(T)
```

Trait solver phải chứng minh goal trước khi function được monomorphize/codegen.

---

# 410.20. Trait Solver

Trait solver sử dụng:

```text
Goal
 ↓
Canonicalization
 ↓
Candidate Lookup
 ↓
Unification
 ↓
Nested Goals
 ↓
Normalization
 ↓
Cycle Detection
 ↓
Proof / Failure
```

Ví dụ:

```text
Goal:
    Add<Vec2> for T
```

solver tìm impl:

```text
impl Add<Vec2> for Vec2
```

→ unify:

```text
T = Vec2
```

→ proof.

---

# 410.21. Canonicalization

Compiler không giải lại những goal semantic giống nhau.

Ví dụ:

```text
Add<Vec2> for Vec2
```

xuất hiện ở hàng nghìn nơi.

Compiler canonicalizes thành key:

```text
TraitGoalKey
```

và cache:

```text
Goal
→ Success / Failure / Ambiguous
```

Điều này rất quan trọng đối với generic-heavy code.

---

# 410.22. Solver Cycle

Ví dụ:

```axiom
trait A<T> {}
trait B<T> {}

impl<T: B<T>> A<T> {}
impl<T: A<T>> B<T> {}
```

Solver không được đệ quy vô hạn.

Phải phát hiện:

```text
A<T>
 ↓
B<T>
 ↓
A<T>
```

và áp dụng cycle policy.

Core v1:

> **Không tự động coi cyclic proof là thành công.**

Cycle không chứng minh được → reject hoặc `ambiguous` tùy dạng goal.

---

# 410.23. Dyn Trait

Dynamic dispatch phải explicit:

```axiom
dyn Printable
```

Không được compiler âm thầm biến:

```axiom
T: Printable
```

thành dynamic dispatch.

Static generic:

```axiom
fn render<T: Renderable>(x: T)
```

mặc định:

```text
monomorphized/static dispatch
```

Dynamic:

```axiom
fn render(x: dyn Renderable)
```

→ dynamic dispatch.

---

# 410.24. Trait Object Representation

`dyn Trait` không phải object/class.

Compiler có thể biểu diễn bằng:

```text
(data pointer, dispatch metadata)
```

hoặc representation khác tùy ABI.

Core semantic guarantee chỉ là:

```text
value implements Trait
+
dispatch operations are valid
```

Không expose object header.

---

# 410.25. Dyn Compatibility

Không phải trait nào cũng có thể biến thành `dyn Trait`.

Trait chứa các yêu cầu không thể dispatch động phải bị reject.

Ví dụ điển hình:

```axiom
trait Factory {
    fn create<T>() -> T
}
```

không có đủ thông tin runtime để dynamic dispatch generic method kiểu này.

Compiler kiểm tra `DynCompatibility`.

Một trait object-safe/dyn-compatible cần thỏa các restriction semantic được định nghĩa rõ.

---

# 410.26. Operator Overloading

Operator không phải magic compiler special case cho từng type.

Ví dụ:

```axiom
a + b
```

được resolve thông qua protocol tương ứng:

```text
Add
```

tương tự:

```text
-       Neg
*       Mul
/       Div
==      Eq
<       Ord/Lt
[]      Index
```

Compiler parser tạo operator expression, sau đó semantic resolver chuyển thành trait operation.

Điều này giữ:

```text
language syntax
≠
type implementation
```

---

# 410.27. Không cho overload tùy tiện mọi syntax

Chỉ các operator/protocol được Core công nhận mới có thể overload.

Không cho library tạo:

```text
@@
%%>
<magic>
```

rồi compiler phải hiểu thêm syntax.

Syntax surface của Axiom vẫn cố định và deterministic.

---

# 410.28. Method Ambiguity

Ví dụ:

```axiom
trait A {
    fn foo(self)
}

trait B {
    fn foo(self)
}
```

và:

```axiom
impl A for X {}
impl B for X {}
```

Khi:

```axiom
x.foo()
```

→ compile error:

```text
ambiguous method `foo`
```

Programmer có thể disambiguate:

```axiom
A::foo(x)
```

hoặc syntax tương đương trait-qualified call mà grammar Core định nghĩa.

Không dựa vào:

- import order;
- declaration order;
- package load order.

---

# 410.29. Method Receiver

Axiom hỗ trợ các receiver semantic:

```text
self
view<Self>
mut_view<Self>
```

và compiler có thể infer cách truyền receiver phù hợp.

Ví dụ:

```axiom
fn read(self: Vec2)
fn inspect(self: view<Vec2>)
fn mutate(self: mut_view<Vec2>)
```

Compiler phải kiểm tra capability/ownership trước khi chọn candidate.

Do đó method resolution không thể hoàn toàn tách khỏi ownership verifier.

Pipeline:

```text
Type Resolution
 ↓
Candidate Discovery
 ↓
Type/Generic Resolution
 ↓
Capability Compatibility
 ↓
Ownership Compatibility
 ↓
Overload Ranking
```

---

# 410.30. Method Resolution và implicit view

Ví dụ:

```axiom
fn length(self: view<Vec2>) -> f32
```

cho phép:

```axiom
v.length()
```

compiler tạo ephemeral view hợp lệ.

Nhưng:

```axiom
let f = v.length
```

không được tự động biến thành escaping capability.

Nếu function value cần tồn tại lâu hơn:

```text
capture / lifetime / escape analysis
```

phải chứng minh được tính hợp lệ.

---

# 410.31. Trait Method + Capability

Ví dụ:

```axiom
trait Sortable {
    fn sort(self: mut_view<Self>)
}
```

`Sortable` implementation không được tùy tiện thay:

```axiom
fn sort(self: Self)
```

hoặc:

```axiom
fn sort(self: view<Self>)
```

vì receiver capability là một phần của semantic contract.

Trait item identity bao gồm cả signature/capability contract cần thiết.

---

# 410.32. ABI không thuộc Trait Identity

Hai function có cùng semantic type nhưng ABI khác nhau không tạo ra hai trait semantics.

ABI được lưu riêng:

```text
FunctionType
+
Effect
+
Capability Contract
+
ABI Metadata
```

Điều này cho phép:

```text
Axiom ABI
C ABI
System ABI
GPU ABI
```

mà không phá type identity.

---

# 410.33. Trait Implementation Record

CompilerDB:

```text
ImplRecord {
    ImplId
    TraitId?
    SelfType
    GenericParameters
    Constraints
    AssociatedTypes
    AssociatedConstants
    Methods
    Visibility
    PackageId
    SourceSpan
    CoherenceUniverse
}
```

Impl không chỉ là syntax node.

Nó là semantic entity có identity riêng.

---

# 410.34. Method Resolution Database

Thêm:

```text
TraitDB
ImplDB
TraitGoalDB
TraitSolverDB
MethodResolutionDB
OverloadDB
AssociatedItemDB
DynCompatibilityDB
OperatorDB
CoherenceDB
```

Cache key ví dụ:

```text
MethodQueryKey {
    ReceiverType
    MethodName
    ArgumentTypes
    GenericContext
    CapabilityContext
    VisibilityContext
    SemanticUniverse
}
```

---

# 410.35. Proof Artifacts

Compiler phải có thể tạo:

```text
TraitImplProof
TraitGoalProof
AssociatedTypeProof
MethodResolutionProof
OverloadResolutionProof
CoherenceProof
DynCompatibilityProof
OperatorResolutionProof
```

Ví dụ:

```text
MethodResolutionProof

receiver:
    Vec2

method:
    add

candidate:
    <Vec2 as Add<Vec2>>::add

constraints:
    satisfied

dispatch:
    static

result:
    Vec2
```

Điều này rất quan trọng cho `axiom explain` và AI agent.

---

# 410.36. AI Semantic Interface

AI có thể hỏi compiler:

```text
why_method("v.foo()")
```

Compiler trả:

```text
receiver type
candidate set
rejected candidates
rejection reasons
selected candidate
generic substitutions
trait proofs
capability proof
dispatch kind
```

AI không cần tự mô phỏng trait solver.

Đây là nguyên tắc Axiom:

> **Compiler phải là nguồn sự thật semantic duy nhất.**

---

# 410.37. Invariants — `ATRAIT`

Axiom Trait System phải bảo đảm ít nhất các invariant:

```text
ATRAIT-01  Trait identity is nominal.
ATRAIT-02  Impl identity is unique.
ATRAIT-03  One coherent impl per (Trait, Type, Universe).
ATRAIT-04  Orphan rule is enforced.
ATRAIT-05  Trait solving is deterministic.
ATRAIT-06  Trait solving terminates.
ATRAIT-07  Cyclic goals cannot silently prove themselves.
ATRAIT-08  Associated types normalize deterministically.
ATRAIT-09  Associated constants have verified types.
ATRAIT-10  Associated functions have stable identity.
ATRAIT-11  Default methods are semantically valid.
ATRAIT-12  Overrides exactly satisfy trait contracts.
ATRAIT-13  Method lookup is deterministic.
ATRAIT-14  Import order cannot change method resolution.
ATRAIT-15  Ambiguous methods are compile errors.
ATRAIT-16  Ambiguous overloads are compile errors.
ATRAIT-17  No implicit user-defined conversions.
ATRAIT-18  Generic constraints must be proven.
ATRAIT-19  Canonical goals have stable cache identity.
ATRAIT-20  Dyn dispatch is explicit.
ATRAIT-21  Dyn-incompatible traits cannot form dyn objects.
ATRAIT-22  Dynamic dispatch never appears implicitly.
ATRAIT-23  Operator overloads use compiler-defined protocols.
ATRAIT-24  Operator semantics remain type-safe.
ATRAIT-25  Receiver capability contracts are preserved.
ATRAIT-26  Trait ABI metadata is separate from semantic identity.
ATRAIT-27  Method resolution respects visibility.
ATRAIT-28  Generated impls re-enter coherence verification.
ATRAIT-29  Trait proofs are reproducible.
ATRAIT-30  No unresolved trait/method candidate reaches codegen.
```

---

# 410.38. Compiler Pipeline

Sau 409, pipeline được mở rộng thành:

```text
Parsed HIR
   ↓
Name Resolution
   ↓
Type Inference
   ↓
Generic Constraint Generation
   ↓
Trait Candidate Discovery
   ↓
Trait Solving
   ↓
Associated Type Normalization
   ↓
Method Resolution
   ↓
Overload Resolution
   ↓
Operator Resolution
   ↓
Coherence Verification
   ↓
Dyn Compatibility Verification
   ↓
Capability/Ownership Verification
   ↓
Typed HIR
```

Sau đó mới tiếp tục:

```text
Typed HIR
 ↓
Closure/Async Analysis
 ↓
MIR
 ↓
Ownership Verification
 ↓
Optimization
 ↓
Codegen
```

---

# 410.39. Quyết định kiến trúc quan trọng

Axiom **không xây OOP bằng cách giả lập class**.

Mô hình chính thức là:

```text
DATA
  ↓
struct

BEHAVIOR
  ↓
function

SHARED CONTRACT
  ↓
trait

IMPLEMENTATION
  ↓
impl

POLYMORPHISM
  ↓
generic/static dispatch
        hoặc
dyn Trait/dynamic dispatch
```

Và:

```text
method syntax
```

chỉ là **syntactic sugar của function call**.

Điều này giữ được:

- layout đơn giản;
- không bắt buộc object header;
- static dispatch mặc định;
- optimizer dễ inline/devirtualize;
- FFI dễ hơn;
- data-oriented programming;
- AI dễ hiểu semantic graph;
- không cần inheritance hierarchy.

---

## 410.40. Trạng thái sau BOOTSTRAP-410

Hiện Axiom đã có nền semantic:

```text
408  Name / Scope / Symbol
        ↓
409  Type / Generic / Type Identity
        ↓
410  Trait / Impl / Method / Overload
        ↓
411  Ownership / Capability / Effect integration
        ↓
412  Closure / Capture / Function Values
        ↓
413  MIR semantic model
```

Trong đó **410 đã khóa nguyên tắc quan trọng nhất**:

> **Axiom không cần class để có polymorphism. Struct + function + trait + impl + compiler-managed resolution là đủ để xây dựng hệ thống abstraction mạnh mà vẫn giữ mô hình machine-friendly.**

