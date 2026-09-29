# BOOTSTRAP-408 — Name Resolution, Scope, Symbol Graph & Module Semantics

Đây là bước tiếp theo sau **CompilerDB (407)**.

408 định nghĩa cách Axiom biến:

```text
source code
    ↓
module graph
    ↓
scope graph
    ↓
symbol graph
    ↓
resolved references
```

Đây là nền móng trực tiếp cho **type checking, trait resolution, generic resolution, IDE navigation và AI semantic queries**.

Nguyên tắc quan trọng:

> **Tên trong source chỉ là syntax; SymbolId mới là identity semantic.**

---

# 1. Mục tiêu

Axiom cần giải quyết chính xác:

```text
import foo
foo.bar()
```

`foo` là gì?

```text
local variable?
function?
type?
module?
trait?
constant?
package?
```

Compiler phải xác định duy nhất trước khi type checker làm việc.

---

# 2. Ba Graph khác nhau

Không được gộp thành một graph.

### Module Graph

```text
Module A
 ├── Module B
 └── Module C
```

### Scope Graph

```text
function
 └── block
      ├── local x
      └── local y
```

### Symbol Graph

```text
SymbolId
 ├── declaration
 ├── type
 ├── owner
 ├── visibility
 └── references
```

Chúng liên kết nhưng có semantics khác nhau.

---

# 3. Module Identity

Mỗi module:

```text
ModuleId
```

có:

```text
PackageId
ModulePath
SourceFileId
Visibility
Imports
Exports
```

Ví dụ:

```text
myapp
├── main
├── math
└── graphics.render
```

sẽ tạo:

```text
Module(myapp::main)
Module(myapp::math)
Module(myapp::graphics::render)
```

---

# 4. Không có Global Namespace

Axiom không có:

```text
global foo
```

theo nghĩa tất cả package chia sẻ một namespace.

Tên đầy đủ:

```text
package::module::symbol
```

Ví dụ:

```text
std::math::sin
```

Package identity vẫn nằm ngoài module identity.

---

# 5. Package Namespace

Hai package có thể cùng có:

```text
math
```

mà không xung đột:

```text
company_a::math
company_b::math
```

Dependency resolution quyết định package identity.

---

# 6. Symbol Identity

Một declaration tạo:

```text
SymbolId
```

Ví dụ:

```text
fn add(a: i32, b: i32) -> i32
```

tạo:

```text
SymbolId(...)
FunctionId(...)
```

SymbolId là identity ổn định hơn source position.

---

# 7. Symbol Categories

Axiom cần phân biệt:

```text
Module
Package
Function
Struct
Enum
Trait
TypeAlias
Const
Static
Field
Variant
Parameter
Local
GenericParameter
Label
```

Không dùng một namespace mơ hồ cho tất cả.

---

# 8. Namespace Model

Đề xuất ba namespace chính:

```text
Value namespace
Type namespace
Module namespace
```

Ví dụ:

```text
struct User {}
fn User() {}
```

có thể được phép vì:

```text
User → type namespace
User → value namespace
```

nhưng:

```text
struct User {}
struct User {}
```

không hợp lệ.

---

# 9. Field Namespace

Field được resolve theo owner:

```text
user.name
```

không tìm `name` trong global scope.

Compiler resolve:

```text
user
 ↓
Type = User
 ↓
field lookup(User, "name")
```

Method:

```text
user.save()
```

thực hiện method-resolution ở phase phù hợp, không đơn thuần field lookup.

---

# 10. Lexical Scope

Scope tạo theo cấu trúc source:

```text
fn foo() {
    let x = 1;

    {
        let y = 2;
    }
}
```

Graph:

```text
FunctionScope
   │
   ├── x
   │
   └── BlockScope
          └── y
```

`y` không tồn tại ngoài block.

---

# 11. Scope Shadowing

Axiom cho phép shadowing có kiểm soát:

```text
let x = 10;

{
    let x = 20;
}
```

Inner `x` che outer `x`.

Nhưng compiler phải giữ:

```text
SymbolId(x_outer)
SymbolId(x_inner)
```

khác nhau.

---

# 12. Shadowing không thay đổi Identity

Ví dụ:

```text
let x = 10;

{
    let x = 20;
    use(x);
}
```

reference phải resolve:

```text
Reference → SymbolId(x_inner)
```

không phải chỉ lưu string `"x"`.

---

# 13. Declaration Before Use

Axiom cần quy tắc rõ ràng.

Đề xuất:

### Trong cùng lexical scope

Tên phải được khai báo trước khi sử dụng.

```text
use(x) // error
let x = 1;
```

### Function/type/module declarations

Cho phép two-phase declaration collection.

```text
fn a() {
    b();
}

fn b() {}
```

hợp lệ.

Điều này cần thiết cho function recursion và mutual recursion.

---

# 14. Two-Phase Module Resolution

Module được xử lý:

```text
Phase 1
collect declarations

Phase 2
resolve bodies/references
```

Nhờ vậy:

```text
fn foo()
fn bar()
```

có thể gọi lẫn nhau.

---

# 15. Import

Import là dependency semantic.

Ví dụ:

```text
import std::math
```

tạo module dependency:

```text
current module
      ↓
std::math
```

CompilerDB phải ghi dependency này.

---

# 16. Selective Import

Có thể:

```text
import std::math::sin
```

Reference:

```text
sin(x)
```

được bind trực tiếp đến:

```text
SymbolId(std::math::sin)
```

---

# 17. Aliased Import

Ví dụ:

```text
import std::math as m
```

sau đó:

```text
m::sin(x)
```

`m` là ModuleAlias semantic symbol.

Không phải runtime variable.

---

# 18. Re-export

Module:

```text
pub import foo::Bar
```

cho phép:

```text
consumer
   ↓
current module::Bar
   ↓
foo::Bar
```

Symbol identity thực tế vẫn là:

```text
foo::Bar
```

Re-export chỉ tạo exported binding.

---

# 19. Visibility

Giữ model 402:

```text
private
module
package
public
```

### private

Chỉ declaration/module scope owner được truy cập.

### module

Toàn module.

### package

Toàn package.

### public

Có thể export package.

Visibility phải là semantic property của declaration.

---

# 20. Visibility không phải Capability

Rất quan trọng:

```text
visibility ≠ capability
```

`public` chỉ có nghĩa:

> symbol được phép được tham chiếu từ nơi khác.

Nó không có nghĩa:

> code được phép thực hiện operation.

Ví dụ:

```text
public fn read_file(...)
```

vẫn có:

```text
Filesystem capability
```

---

# 21. Unqualified Lookup

Với:

```text
foo()
```

resolver tìm theo thứ tự:

```text
1. local scope
2. parameter
3. enclosing scope
4. module-local symbol
5. explicitly imported symbol
6. prelude, nếu có
```

Prelude phải cực kỳ hạn chế.

Không nên tạo một global namespace khổng lồ.

---

# 22. Prelude

Axiom có thể có prelude:

```text
bool
i32
Option
Result
view
```

nhưng prelude là compiler-known module.

Không nên để hàng trăm API tự động xuất hiện.

Có thể:

```text
import core::prelude
```

ngầm định.

Compiler vẫn biểu diễn nó như dependency thực.

---

# 23. Ambiguous Name

Nếu:

```text
import a::foo
import b::foo
```

và:

```text
foo()
```

thì:

```text
AMBIGUOUS_NAME
```

Không được chọn dựa trên:

```text
import order
file order
alphabetical order
```

Programmer phải resolve.

---

# 24. Explicit Qualification

Cho phép:

```text
a::foo()
b::foo()
```

để giải quyết ambiguity.

Đây cũng là cơ chế AI-friendly vì semantic intent rõ.

---

# 25. Method Lookup Không thuộc Resolver đơn thuần

Với:

```text
x.foo()
```

Resolver chỉ xác định:

```text
x
```

Sau đó:

```text
Type(x)
 ↓
MethodResolution
```

mới tìm:

```text
inherent methods
trait methods
extensions
generic candidates
```

Điều này tránh trộn name resolution với type inference.

---

# 26. Generic Names

Ví dụ:

```text
fn identity<T>(x: T) -> T
```

`T` tạo:

```text
GenericParameterSymbol
```

scope:

```text
FunctionScope
 └── GenericScope
       └── T
```

`T` không tồn tại bên ngoài function.

---

# 27. Type Parameters của Struct

```text
struct Vec<T> {
    data: Buffer<T>
}
```

`T` thuộc:

```text
StructGenericScope
```

và được resolve trong toàn declaration.

---

# 28. Trait Generic Scope

```text
trait Convert<T> {
    fn convert(x: T);
}
```

`T` thuộc trait scope.

Method có thể thêm generic riêng:

```text
trait Convert<T> {
    fn convert<U>(x: U);
}
```

Hai `T`/`U` là hai SymbolId khác nhau.

---

# 29. Associated Items

Trait:

```text
trait Iterator {
    type Item;
    fn next(self) -> Option<Self::Item>;
}
```

`Item` là:

```text
AssociatedTypeSymbol
```

Không phải global type.

Tương tự:

```text
Trait::method
Trait::Item
```

có namespace riêng của trait.

---

# 30. Enum Variants

Ví dụ:

```text
enum Color {
    Red,
    Green,
    Blue
}
```

Variant có identity:

```text
VariantId
```

và có thể resolve:

```text
Color::Red
```

Không nên biến `Red` thành global symbol.

---

# 31. Pattern Binding

```text
match value {
    Some(x) => x + 1
}
```

`x` là local symbol được tạo trong pattern scope.

Scope:

```text
MatchArm
 └── PatternBindings
       └── x
```

Chỉ tồn tại trong arm.

---

# 32. Closure Capture

Ví dụ:

```text
let x = 10;

let f = || x + 1;
```

Resolver trước hết xác định:

```text
x → outer SymbolId
```

Sau đó closure analysis ở phase khác quyết định:

```text
capture x
```

Không để resolver tự quyết định ownership/capture mode.

---

# 33. Labels

Nếu Axiom hỗ trợ loop labels:

```text
'outer: loop {
    loop {
        break 'outer;
    }
}
```

label có:

```text
LabelSymbol
```

và namespace riêng.

---

# 34. Built-in Symbols

Một số symbol không nằm trong source:

```text
bool
i32
u64
view
mut_view
```

Compiler có thể inject:

```text
BuiltinSymbol
```

nhưng chúng vẫn phải có SymbolId và metadata thống nhất.

Không được có hai cơ chế:

```text
source symbols
magic compiler symbols
```

không liên kết.

---

# 35. Error Recovery

Resolver phải tiếp tục sau lỗi.

Ví dụ:

```text
foo(bar(baz()))
```

nếu `bar` không tồn tại, compiler vẫn nên resolve:

```text
baz
```

nếu có thể.

Mục tiêu:

> một typo không tạo ra 500 lỗi cascading giả.

Diagnostic engine 403 xử lý grouping/suppression.

---

# 36. Unresolved Symbol

CompilerDB có thể tạo:

```text
UnresolvedSymbol
```

tạm thời trong IDE revision.

Nhưng unresolved state:

```text
không được đi vào codegen
```

Build có thể tiếp tục phân tích để tạo diagnostics, nhưng artifact hợp lệ không được phát hành.

---

# 37. Symbol References

CompilerDB lưu:

```text
SymbolId
   ↓
References[]
```

Ví dụ:

```text
foo
 ├── main.ax:10
 ├── test.ax:5
 └── util.ax:33
```

IDE:

```text
find references
rename
go to definition
```

đều dùng graph này.

---

# 38. Rename

Rename phải semantic:

```text
rename SymbolId(foo)
```

không phải:

```text
replace "foo"
```

Ví dụ:

```text
foo()
obj.foo
"foo"
```

chỉ reference đến `SymbolId(foo)` mới bị thay.

String literal không đổi.

---

# 39. Import Cycle

Module cycle:

```text
A → B
B → A
```

không nhất thiết phải cấm tuyệt đối.

Đề xuất:

### Declaration-level cycles

Cho phép nếu semantics xác định được.

### Initialization cycles

Phải kiểm tra riêng.

Ví dụ static initialization:

```text
A.x → B.y
B.y → A.x
```

có thể tạo cycle runtime.

Do đó:

```text
module dependency cycle
≠
initialization cycle
```

---

# 40. Module Initialization

Axiom nên tránh static initialization magic.

Nếu có:

```text
static x = expensive();
```

compiler phải xây dependency graph:

```text
x
 ↓
expensive()
```

và phát hiện cycle.

Freestanding code không nên bị ép có global runtime initializer.

---

# 41. Symbol Graph cho AI

AI query:

```text
find_symbol("User")
```

không nên trả string search.

Nó trả:

```text
Symbol {
    id
    kind
    module
    visibility
    declaration
    type
    documentation
    references
    implementations
}
```

AI có thể biết chính xác declaration nào.

---

# 42. Resolver Output

Resolver tạo:

```text
ResolvedHIRBindings
```

mỗi reference:

```text
ExpressionId
      ↓
SymbolId
```

Ví dụ:

```text
x + foo(y)
```

thành:

```text
x   → SymbolId(12)
foo → SymbolId(41)
y   → SymbolId(18)
```

Sau đó type checker không cần tìm tên lại.

---

# 43. Symbol Graph và Incremental Compilation

Nếu function body thay đổi:

```text
fn foo() { ... }
```

nhưng declaration/signature không đổi:

```text
SymbolId(foo)
```

vẫn giữ nguyên.

Downstream semantic dependency không bị invalidated chỉ vì source position/body thay đổi nếu không cần.

---

# 44. Resolution Phases

Resolver hoàn chỉnh:

```text
Source
 ↓
Parse
 ↓
Module Discovery
 ↓
Module Graph
 ↓
Declaration Collection
 ↓
Scope Construction
 ↓
Import Resolution
 ↓
Name Resolution
 ↓
Re-export Resolution
 ↓
Visibility Verification
 ↓
Resolved HIR Bindings
```

Sau đó mới:

```text
Type Resolution / Type Inference
```

---

# 45. Không để Resolver làm quá nhiều

Resolver **không** quyết định:

```text
type compatibility
ownership
borrow/view legality
trait implementation
overload selection dựa trên inferred types
effect legality
ABI
optimization
```

Nó chỉ trả lời:

> **"Tên này đang trỏ đến declaration semantic nào?"**

Method/trait resolution là bước semantic tiếp theo có type information.

---

# 46. Resolver Data Model

Có thể đóng băng:

```text
ModuleRecord {
    ModuleId
    PackageId
    Path
    Imports
    Exports
    ScopeId
}

ScopeRecord {
    ScopeId
    ParentScope
    Kind
    Bindings
}

SymbolRecord {
    SymbolId
    Kind
    Name
    Owner
    Visibility
    SourceSpan
}

ReferenceRecord {
    ExpressionId
    SymbolId
    SourceSpan
}
```

---

# 47. Resolver Proofs

Tạo:

```text
NameResolutionProof
ScopeResolutionProof
ImportResolutionProof
VisibilityProof
ReExportProof
SymbolIdentityProof
ModuleGraphProof
```

Ví dụ:

```text
foo()
```

có:

```text
Reference(Expression#21)
    →
Symbol(Function#42)
```

với proof rằng symbol được resolve duy nhất.

---

# 48. Bộ invariant ARES

Đóng băng 30 invariant:

### ARES-01
Mọi declaration semantic phải có SymbolId.

### ARES-02
SymbolId không phụ thuộc đơn thuần vào source position.

### ARES-03
Symbol identity phải deterministic.

### ARES-04
Module identity phải deterministic.

### ARES-05
Package identity và Module identity phải khác nhau.

### ARES-06
Module Graph và Scope Graph phải khác nhau.

### ARES-07
Scope Graph và Symbol Graph phải khác nhau.

### ARES-08
Reference phải resolve tới SymbolId, không chỉ tên text.

### ARES-09
Local shadowing phải tạo SymbolId khác.

### ARES-10
Unqualified lookup phải deterministic.

### ARES-11
Ambiguous lookup phải là compile error.

### ARES-12
Import order không được quyết định symbol resolution.

### ARES-13
Re-export không tạo identity mới cho declaration gốc.

### ARES-14
Visibility phải được kiểm tra semantic.

### ARES-15
Visibility không đồng nghĩa capability.

### ARES-16
Method lookup không được thực hiện bằng text substitution.

### ARES-17
Type information phải được dùng ở method/trait resolution phase phù hợp.

### ARES-18
Generic parameters phải có lexical scope riêng.

### ARES-19
Associated items phải có owner identity.

### ARES-20
Enum variants phải có identity riêng.

### ARES-21
Pattern bindings phải có scope chính xác.

### ARES-22
Closure capture không thuộc trách nhiệm chính của name resolver.

### ARES-23
Unresolved symbol không được codegen.

### ARES-24
Error recovery không được tạo hàng loạt cascading diagnostics giả.

### ARES-25
Rename phải dựa trên SymbolId.

### ARES-26
Reference graph phải incremental.

### ARES-27
Module cycles và initialization cycles phải được phân tích riêng.

### ARES-28
Built-in symbols phải có semantic identity thống nhất.

### ARES-29
Resolver output phải đủ deterministic để cache trong CompilerDB.

### ARES-30
Resolver chỉ xác định binding/name identity; không được tự ý thay thế type, ownership hoặc optimization semantics.

---

# 49. Kiến trúc sau BOOTSTRAP-408

Pipeline hiện tại trở thành:

```text
Source
  │
  ▼
Lexer / Parser
  │
  ▼
SyntaxDB
  │
  ▼
Module Discovery
  │
  ▼
Module Graph
  │
  ▼
Declaration Collection
  │
  ▼
Scope Graph
  │
  ▼
Name Resolver
  │
  ▼
Symbol Graph
  │
  ▼
Resolved HIR
  │
  ▼
Type System
```

và toàn bộ chạy trên:

```text
                    CompilerDB
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
         Query Engine          Revision
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
    Module  Symbol  Scope
      DB      DB      DB
```

Đây là một ranh giới rất tốt: **Resolver không biết ownership/type sâu, Type System không phải đi tìm tên text, IDE/AI không phải tự parse source để biết symbol.**

**BOOTSTRAP-408 — SPECIFIED / FROZEN**.