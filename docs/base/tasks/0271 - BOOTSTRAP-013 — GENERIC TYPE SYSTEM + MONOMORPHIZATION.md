Tiếp theo là **BOOTSTRAP-013 — Generics + Monomorphization**.

Đây là bước hợp lý sau Ownership/Capability, vì từ đây Axiom bắt đầu có khả năng xây dựng `Option<T>`, `Result<T,E>`, `Vec<T>`, `Box<T>`… như **thư viện thật**, thay vì compiler phải đặc biệt hóa từng type.

# BOOTSTRAP-013 — GENERIC TYPE SYSTEM + MONOMORPHIZATION

## 1. Quyết định kiến trúc

> **Generic là compile-time abstraction. Static dispatch là mặc định. Không có generic runtime metadata.**

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    return x;
}
```

không tạo runtime function kiểu:

```text
identity(void* x, TypeInfo* T)
```

Thay vào đó:

```text
identity<i32>
identity<f64>
identity<Point>
```

được specialize khi cần.

---

# 2. Generic không phải dynamic typing

Axiom:

```axiom
fn max<T>(a: T, b: T) -> T
```

không có nghĩa:

```text
T = Any
```

và cũng không có:

```text
runtime type check
```

`T` là một **compile-time type parameter**.

---

# 3. Generic struct

Ví dụ:

```axiom
struct Pair<T, U> {
    first: T,
    second: U,
}
```

Các type khác nhau:

```text
Pair<i32, i32>
Pair<i32, String>
Pair<Point, f64>
```

có các type identity khác nhau.

---

# 4. Generic identity

Compiler dùng:

```text
GenericDefId
+
TypeArgs
+
ConstArgs
```

để tạo canonical type.

Ví dụ:

```text
Pair<i32, String>
```

internal:

```text
GenericInstance {
    def = Pair
    args = [
        i32,
        String
    ]
}
```

Không dùng string:

```text
"Pair<i32,String>"
```

làm type identity.

---

# 5. Type interning

Compiler nên có:

```text
TypeInterner
```

Ví dụ:

```text
intern(Pair<i32, String>)
```

trả:

```text
TypeId(123)
```

Nếu gặp lại cùng type:

```text
Pair<i32, String>
```

→ cùng canonical `TypeId`.

Điều này rất quan trọng cho:

- trait solving
- layout cache
- MIR
- incremental compilation
- monomorphization
- diagnostics

---

# 6. Generic function

Ví dụ:

```axiom
fn swap<T>(a: mut_view<T>, b: mut_view<T>) {
    ...
}
```

Compiler không cần generate code ngay khi parse declaration.

Đầu tiên tạo:

```text
GenericFunction {
    id
    params = [T]
    body
}
```

Khi có:

```axiom
swap(x, y);
```

compiler resolve:

```text
T = i32
```

và tạo instantiation:

```text
swap<i32>
```

---

# 7. Generic type checking

Generic body phải được type-check với symbolic parameter.

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    return x;
}
```

hợp lệ.

Nhưng:

```axiom
fn foo<T>(x: T) -> T {
    return x + x;
}
```

không thể mặc định hợp lệ.

Compiler chưa biết `T` có hỗ trợ `+`.

Sau này trait sẽ giải quyết:

```axiom
fn foo<T: Add>(x: T) -> T
```

Ở BOOT-013 có thể tạm hạn chế generic operations.

---

# 8. Generic constraints chuẩn bị cho Trait

Mặc dù Trait là BOOT-014, syntax nên chuẩn bị:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

hoặc:

```axiom
fn max<T>(a: T, b: T) -> T
where
    T: Ord,
{
    ...
}
```

Parser có thể hỗ trợ ngay.

Trait solver chưa cần hoàn thiện ở BOOT-013.

---

# 9. Không có implicit type parameters

Không cho kiểu:

```text
foo(x) 
```

mà compiler tự tạo generic parameter mới không rõ nguồn gốc.

Generic parameters phải xuất hiện rõ trong declaration:

```axiom
fn foo<T>(x: T)
```

Điều này giữ inference deterministic.

---

# 10. Type inference tại call site

Cho phép:

```axiom
let x = identity(42);
```

Compiler suy ra:

```text
T = i32
```

và:

```text
identity<i32>(42)
```

Nhưng public API vẫn nên có declaration rõ ràng.

---

# 11. Không inference toàn chương trình

Compiler không nên tìm kiếm:

```text
"có lẽ T là X vì sau 37 function calls..."
```

Inference nên chủ yếu local.

Ví dụ:

```axiom
let x = identity(42);
```

dễ.

Nhưng API:

```axiom
pub fn process(x) -> ...
```

không hợp lệ vì parameter type phải rõ.

---

# 12. Generic specialization

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    return x;
}
```

calls:

```axiom
identity(10);
identity(20);
identity(point);
```

Compiler có thể tạo:

```text
identity<i32>
identity<Point>
```

Chỉ cần một `identity<i32>` cho cả `10` và `20`.

Không specialize theo value.

---

# 13. Monomorphization

Pipeline:

```text
Typed HIR
    ↓
Generic Resolution
    ↓
Instantiation
    ↓
Concrete Typed HIR
    ↓
MIR
```

Ví dụ:

```text
identity<T>
```

→

```text
identity<i32>
identity<f64>
identity<Point>
```

Mỗi instantiation trở thành một function bình thường trước MIR.

---

# 14. MIR không chứa generic solver

Đây là invariant quan trọng.

Không để MIR chứa:

```text
call some_function<T>
```

và rồi machine backend phải hỏi trait solver.

MIR phải có:

```text
call FunctionId(identity<i32>)
```

hoặc canonical instantiated function ID.

---

# 15. Generic constraints biến mất

Ví dụ:

```axiom
fn f<T: SomeTrait>(x: T)
```

sau trait resolution + monomorphization:

```text
f<Point>
```

MIR không cần biết:

```text
Point implements SomeTrait
```

nữa.

Thông tin đó đã được compiler chứng minh trước đó.

---

# 16. Generic code không mặc định có runtime cost

Ví dụ:

```axiom
fn square<T>(x: T) -> T
```

với `i32`:

```text
square<i32>
```

có thể inline thành:

```text
x * x
```

Không có:

```text
TypeInfo
virtual call
boxing
heap allocation
```

---

# 17. Generic code bloat

Monomorphization có vấn đề:

```text
N types
×
M generic functions
=
N×M code
```

Không nên bỏ qua.

Axiom cần **deduplication**.

---

# 18. Generic deduplication

Sau codegen:

```text
identity<i32>
identity<MyI32Alias>
```

nếu machine semantics và ABI hoàn toàn giống nhau, linker/compiler có thể deduplicate.

Ban đầu có thể dùng:

```text
COMDAT
+
ICF
```

như đã định hướng ở Object/Linker.

---

# 19. Nhưng không merge mù quáng

Hai generic instantiation có thể có:

```text
same size
same machine code
```

nhưng khác:

```text
ABI
debug identity
visibility
symbol semantics
```

Do đó dedup chỉ là optimization.

Semantic identity vẫn khác:

```text
identity<UserId>
identity<u64>
```

nếu `UserId` là `distinct`.

---

# 20. `distinct` và generics

Ví dụ:

```axiom
type UserId = distinct u64;
```

thì:

```text
UserId != u64
```

dù representation giống nhau.

Vì vậy:

```axiom
fn f<T>(x: T)
```

có thể instantiate riêng:

```text
f<UserId>
f<u64>
```

và compiler sau đó mới quyết định dedup machine code nếu an toàn.

---

# 21. Generic recursion

Ví dụ:

```axiom
fn f<T>(x: T) {
    f<T>(x);
}
```

chỉ có một instantiation.

Nhưng:

```text
f<A>
→ f<B>
→ f<C>
→ ...
```

có thể gây infinite instantiation.

Compiler phải phát hiện.

---

# 22. Generic instantiation graph

Dùng:

```text
InstantiationGraph
```

Ví dụ:

```text
f<i32>
  └── g<i32>
       └── h<i32>
```

Compiler cache từng node.

Nếu gặp node đang active:

```text
f<A>
 → g<B>
 → f<A>
```

phải phân biệt:

- recursion runtime hợp lệ
- infinite compile-time instantiation

Hai thứ này không giống nhau.

---

# 23. Runtime recursion vẫn bình thường

```axiom
fn factorial(n: i32) -> i32 {
    if n == 0 {
        return 1;
    }

    return n * factorial(n - 1);
}
```

không phải generic instantiation recursion.

Chỉ là:

```text
factorial
 → factorial
```

runtime call.

---

# 24. Generic const parameters

Axiom nên hỗ trợ giới hạn:

```axiom
struct Array<T, const N: usize> {
    ...
}
```

nhưng Stage-0 chỉ cần:

```text
integer
bool
```

làm const generic.

Không đưa dependent types đầy đủ.

---

# 25. Ví dụ

```axiom
fn first<T, const N: usize>(
    a: view<[N]T>
) -> view<T> {
    ...
}
```

`N` là compile-time value.

Compiler có thể instantiate:

```text
first<i32, 16>
first<i32, 32>
```

---

# 26. Không cho arbitrary runtime value làm const parameter

Không:

```axiom
let n = read_input();
foo<i32, n>();
```

vì `n` không phải compile-time constant.

---

# 27. Generic arrays

Đây là một use case rất quan trọng:

```axiom
fn sum<const N: usize>(
    a: view<[N]i32>
) -> i32
```

Compiler biết:

```text
N = 4
```

có thể unroll hoặc vectorize nếu profitable.

---

# 28. Generic return

Ví dụ:

```axiom
fn make<T>(x: T) -> T {
    return x;
}
```

return semantics vẫn theo Ownership:

```text
non-Copy T
→ Move

Copy T
→ Copy
```

Generic không được bypass ownership verifier.

---

# 29. Generic `view`

Ví dụ:

```axiom
fn print<T>(x: view<T>)
```

`view<T>` vẫn là capability.

Không được generic hóa thành:

```text
raw pointer
```

trước khi capability checking hoàn thành.

Pipeline:

```text
Generic Resolution
    ↓
Concrete T
    ↓
Ownership/Capability Verification
```

---

# 30. Generic `mut_view`

Ví dụ:

```axiom
fn swap<T>(
    a: mut_view<T>,
    b: mut_view<T>
)
```

vẫn phải kiểm tra:

```text
region(a)
vs
region(b)
```

có overlap hay không.

Generic không làm mất alias information.

---

# 31. Generic Drop

Ví dụ:

```axiom
struct Boxed<T> {
    value: T,
}
```

Nếu `T` có Drop:

```text
Boxed<T>
```

có Drop semantics.

Nếu `T` là trivially droppable:

```text
Boxed<T>
```

có thể không cần runtime cleanup.

Compiler specialize Drop behavior.

---

# 32. Generic Copy

Tương tự:

```text
struct Pair<T, U> {
    a: T,
    b: U,
}
```

`Pair<T,U>` là Copy khi:

```text
T: Copy
U: Copy
```

Đây là semantic property.

Compiler có thể derive tự động.

---

# 33. Generic Send/Share

Tương tự:

```text
Pair<T,U>: Send
```

khi các thành phần đáp ứng Send semantics.

Không cần programmer viết:

```text
unsafe impl Send
```

trong trường hợp compiler có thể chứng minh.

---

# 34. Generic layout

`Pair<i32,i64>` và:

```text
Pair<u8,u64>
```

có thể có layout khác.

Layout cache key:

```text
GenericInstance
+
Target
+
Repr
+
ABI
```

không được cache generic definition layout chung.

---

# 35. Generic ABI

Ví dụ:

```axiom
fn f<T>(x: T) -> T
```

không có một ABI representation duy nhất.

`T=i32`:

```text
register
```

`T=LargeStruct`:

```text
multiple registers / indirect / sret
```

Do đó ABI lowering xảy ra sau specialization/layout.

---

# 36. Generic function pointers

Ví dụ:

```axiom
let f = identity::<i32>;
```

sau resolution:

```text
fn(i32) -> i32
```

function pointer là concrete.

Không có:

```text
generic function pointer
```

runtime.

---

# 37. Generic closures

Có thể:

```axiom
fn apply<T, U>(
    x: T,
    f: fn(T) -> U
) -> U
```

hoặc closure type.

Generic closure environment vẫn là ordinary aggregate.

Không cần runtime generic object.

---

# 38. Generic compilation cache

Compiler nên có:

```text
GenericInstanceCache
```

key:

```text
GenericDefId
TypeArgs
ConstArgs
TargetABIContext
```

Nhưng cần phân biệt:

```text
semantic instantiation
```

và:

```text
machine code generation
```

Một semantic instantiation có thể dùng chung nhiều codegen target.

---

# 39. Incremental compilation

Ví dụ:

```text
foo<i32>
foo<f64>
foo<Point>
```

Nếu chỉ thay đổi code sử dụng:

```text
foo<Point>
```

không nhất thiết rebuild:

```text
foo<i32>
foo<f64>
```

Semantic hash của generic definition + arguments giúp incremental cache.

---

# 40. Diagnostics

Đề xuất:

```text
AX1301 generic argument count mismatch
AX1302 generic type constraint not satisfied
AX1303 generic const argument is not constant
AX1304 generic type cannot be inferred
AX1305 generic parameter unused
AX1306 infinite generic instantiation
AX1307 generic instantiation recursion limit exceeded
AX1308 invalid const generic type
AX1309 generic ABI cannot be determined
AX1310 ambiguous generic instantiation
```

---

# 41. Generic inference

Ví dụ:

```axiom
fn pair<T>(x: T, y: T) -> Pair<T,T> {
    ...
}

let p = pair(1, 2);
```

Compiler:

```text
T = i32
```

OK.

Nhưng:

```axiom
pair(1, 2.0);
```

không tự động:

```text
T = ??? 
```

vì Axiom không muốn hidden numeric coercion phức tạp.

---

# 42. Generic inference phải deterministic

Không được phụ thuộc:

```text
file order
hash map iteration
optimization level
CPU
parallel compilation order
```

Cùng source:

```text
→ cùng generic instantiation set
```

trừ những phần compiler cố ý tối ưu nhưng không ảnh hưởng semantics.

---

# 43. Không full dependent types

Không:

```text
fn f<T, N: expression>(...)
```

với arbitrary type-level computation.

Không:

```text
Vector<T, T::AssociatedType::Foo(...)>
```

phức tạp.

V1 chỉ:

```text
Type parameters
Const integer/bool parameters
Trait constraints
Associated types
```

là đủ mạnh.

---

# 44. Không higher-kinded types v1

Không cần:

```text
F<_>
```

kiểu Haskell:

```text
Functor<F>
```

ngay trong core.

Nếu sau này có nhu cầu abstraction cao hơn, có thể mở rộng trait system mà không phá generic foundation.

---

# 45. Generic + comptime

Sau này:

```axiom
comptime fn make_array<T, const N: usize>() -> Type {
    ...
}
```

có thể dùng generic information.

Nhưng BOOT-013 không cần implement comptime.

Chỉ cần đảm bảo architecture không chặn nó.

---

# 46. Generic + specialization

Không đưa unrestricted specialization vào v1.

Ví dụ:

```axiom
impl<T> Foo for T { ... }

impl Foo for i32 { ... }
```

nếu có overlap sẽ tạo ambiguity.

Axiom v1 nên yêu cầu coherence rõ ràng.

Sau này nếu cần specialization:

```text
explicit opt-in
compiler-controlled
deterministic
```

không biến thành feature mặc định.

---

# 47. Generic codegen pipeline

Đề xuất chính thức:

```text
Generic HIR
    ↓
Type / Const Resolution
    ↓
Instantiation
    ↓
Concrete HIR
    ↓
Ownership / Capability
    ↓
MIR
    ↓
Optimization
    ↓
ABI
    ↓
Machine
```

Không:

```text
Generic HIR
    ↓
Machine
    ↓
magic runtime dispatch
```

---

# 48. MIR function identity

Thay vì:

```text
FunctionId = 17
```

cho mọi specialization, dùng:

```text
FunctionInstanceId
```

Ví dụ:

```text
FunctionInstanceId {
    generic_def: FunctionId(17),
    type_args: [i32],
    const_args: []
}
```

Sau canonicalization có ID ổn định:

```text
InstanceId(42)
```

---

# 49. Generic instance graph

Compiler cần:

```text
InstanceGraph
```

Ví dụ:

```text
main
 ├── Vec<i32>::push
 │     └── grow<i32>
 └── Option<Point>::map
       └── closure<Point>
```

Graph này sau này cực kỳ hữu ích cho:

- dead code elimination
- monomorphization
- linker GC
- code-size analysis
- incremental compilation
- LTO-like optimization

---

# 50. Dead generic instantiations

Không phải mọi generic declaration đều generate machine code.

Ví dụ:

```axiom
fn unused<T>(x: T) { ... }
```

không được gọi.

→ Không cần machine code.

Do đó:

```text
Generic declaration
```

khác:

```text
Instantiated function
```

và khác:

```text
Emitted machine function
```

---

# 51. Generic code size policy

Compiler có thể có:

```text
-Oz
```

và:

```text
-O3
```

khác nhau về dedup/inlining/codegen nhưng không thay đổi semantics.

Ví dụ:

```text
-Oz
→ mạnh tay deduplicate

-O3
→ specialize/inlining nhiều hơn
```

Nhưng cả hai vẫn phải cùng behavior.

---

# 52. BOOT-013 test ladder

### Generic function

```axiom
fn identity<T>(x: T) -> T {
    return x;
}
```

### Generic struct

```axiom
struct Box<T> {
    value: T,
}
```

### Multiple types

```text
Box<i32>
Box<f64>
Box<Point>
```

### Generic ownership

```text
Box<String>
move
drop
```

### Generic Copy

```text
Box<i32> → Copy
Box<String> → !Copy
```

### Generic views

```text
fn f<T>(x: view<T>)
```

### Generic arrays

```text
fn sum<const N: usize>(...)
```

### Generic inference

```text
identity(42)
```

### Error

```text
identity() // cannot infer T
```

### Infinite instantiation

Phải có test riêng.

### Code dedup

```text
identity<i32>
identity<MyAlias>
```

kiểm tra machine-level dedup nếu representations tương thích.

---

# 53. Invariants

```text
AGENERIC-20  Generic Parameters Are Compile-Time Entities
AGENERIC-21  Generic Types Have Canonical Identity
AGENERIC-22  Generic Functions Have Canonical Identity
AGENERIC-23  Generic Instantiations Are Deterministic
AGENERIC-24  Generic Arguments Are Explicitly Typed
AGENERIC-25  Local Generic Inference Is Deterministic
AGENERIC-26  Public Generic APIs Require Explicit Parameter Types
AGENERIC-27  Generic Constraints Are Compile-Time
AGENERIC-28  Generic Constraints Do Not Require Runtime Metadata
AGENERIC-29  Generic Code Uses Static Dispatch By Default
AGENERIC-30  Generic Instantiation Produces Concrete Semantic Code
AGENERIC-31  MIR Contains Resolved Generic Instances
AGENERIC-32  Trait Solving Does Not Occur In MIR
AGENERIC-33  Generic Ownership Semantics Are Normal Ownership Semantics
AGENERIC-34  Generic Capability Semantics Are Normal Capability Semantics
AGENERIC-35  Generic Drop Is Type Dependent
AGENERIC-36  Generic Copy Is Semantic
AGENERIC-37  Generic Send/Share Are Compiler Properties
AGENERIC-38  Generic Layout Is Instance Dependent
AGENERIC-39  Generic ABI Is Instance Dependent
AGENERIC-40  Generic Instances Are Cacheable
AGENERIC-41  Infinite Generic Instantiation Is Diagnosed
AGENERIC-42  Runtime Recursion Is Distinct From Generic Instantiation
AGENERIC-43  Unused Generic Instances Need Not Be Emitted
AGENERIC-44  Generic Code May Be Deduplicated
AGENERIC-45  Deduplication Does Not Change Type Identity
AGENERIC-46  Generic Const Parameters Are Compile-Time Values
AGENERIC-47  Generic Const Parameters Are Initially Limited
AGENERIC-48  Arbitrary Dependent Types Are Not Required
AGENERIC-49  Higher-Kinded Types Are Not Required By v1
AGENERIC-50  Unrestricted Specialization Is Not Required
AGENERIC-51  Generic Resolution Is Independent Of Optimization Level
AGENERIC-52  Generic Compilation Is Reproducible
```

---

# 54. BOOT-013 gate

Phải đạt:

```text
Generic type                 ✓
Generic function             ✓
Generic struct               ✓
Type inference               ✓
Const generic integer        ✓
Canonical TypeId             ✓
Instantiation cache          ✓
Monomorphization             ✓
Generic ownership            ✓
Generic capability           ✓
Generic Drop                 ✓
Generic Copy                 ✓
Generic layout               ✓
Generic ABI                  ✓
Infinite instantiation check ✓
MIR concrete instances       ✓
x86-64 native                ✓
-O0/O1/O2/O3                 ✓
Interpreter/native equality  ✓
```

---

## Một điểm tôi muốn chốt ở BOOT-013

Axiom đang hình thành một pipeline rất rõ:

```text
                 SOURCE
                   │
        ┌──────────▼──────────┐
        │ Generic Abstraction │
        └──────────┬──────────┘
                   │
             compile time
                   │
        ┌──────────▼──────────┐
        │ Concrete Instance   │
        └──────────┬──────────┘
                   │
        Ownership + Capability
                   │
        ┌──────────▼──────────┐
        │    Verified MIR     │
        └──────────┬──────────┘
                   │
               optimize
                   │
        ┌──────────▼──────────┐
        │      Native         │
        └─────────────────────┘
```

**Không có bước “generic → runtime object”.**

Đây là nền tảng để sau này `Vec<T>`, `HashMap<K,V>`, `Box<T>`, `Arc<T>`, `Mutex<T>`, `Option<T>`, `Result<T,E>` đều có thể được xây dựng bằng Axiom thông thường, trong khi compiler vẫn có thể specialize và tối ưu chúng gần như code viết trực tiếp cho từng kiểu dữ liệu.