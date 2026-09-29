# BOOTSTRAP-150 — Whole-Program Optimization, LTO & Link-Time Semantic Optimization
**STATUS: FROZEN / COMPLETED**

> **Khi compiler nhìn thấy toàn bộ chương trình, Axiom không còn phải tối ưu từng module một cách độc lập. Nó có thể tối ưu xuyên module/package, nhưng chỉ trong phạm vi mà semantic và ABI cho phép.**

Đây là tầng kết nối **compiler optimizer** với **linker**.

---

## 1. Vị trí

```text id="a15001"
Source
  ↓
Module / Package Compilation
  ↓
Verified MIR
  ↓
Local Optimization
  ↓
OptIR
  ↓
Interprocedural Analysis
  ↓
Generic Specialization
  ↓
LTO Graph
  ↓
Whole-Program Optimization
  ├── Global Call Graph
  ├── Cross-Module Inlining
  ├── Cross-Module Devirtualization
  ├── Global Specialization
  ├── Global DCE
  ├── Global Constant Propagation
  ├── Global Alias / Effect / Escape
  ├── Global Code Layout
  └── Global Data Layout
  ↓
Final Optimized OptIR
  ↓
ABI MIR
  ↓
LIR
  ↓
Machine
  ↓
Object
  ↓
Link
```

---

# 2. LTO không phải chỉ là “link nhiều object”

Linker truyền thống nhìn:

```text id="a15002"
symbol
relocation
section
```

LTO của Axiom nhìn thêm:

```text id="a15003"
Function
Type
GenericInstance
Trait
Effect
Alias
Escape
CallGraph
Profile
ABI
Visibility
Representation
```

Do đó:

```text
Traditional Linker
        ↓
binary composition

Axiom LTO
        ↓
semantic-aware binary optimization
```

---

# 3. `.axmeta` trở thành rất quan trọng

Mỗi package có thể phát hành:

```text id="a15004"
foo.axlib
foo.axmeta
```

`.axmeta` chứa thông tin cần thiết cho downstream compilation:

```text id="a15005"
Public declarations
Types
Traits
Generic definitions
ABI contracts
Effects
Escape summaries
Capability contracts
GPU metadata
FFI contracts
Export information
Optimization summaries
Semantic fingerprints
```

Nhờ vậy package đã compile vẫn có thể được tối ưu ở mức cao.

---

# 4. Public API không đồng nghĩa optimization boundary

Ví dụ:

```ax id="a15006"
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`pub` nghĩa là:

```text id="a15007"
source-visible
```

không nhất thiết:

```text id="a15008"
must remain a separate machine function
```

Nếu compiler biết call sites và không có observable function identity:

```text id="a15009"
add()
 ↓
inline
 ↓
a + b
```

hoàn toàn hợp lệ.

---

# 5. `@export` mới là ABI boundary

Nếu:

```ax id="a15010"
@export("axiom_add")
pub fn add(...)
```

thì symbol:

```text id="a15011"
axiom_add
```

là observable binary interface.

Compiler phải giữ:

```text id="a15012"
symbol
calling convention
parameter ABI
return ABI
required representation
```

Nhưng **phần implementation bên trong vẫn có thể tối ưu**.

---

# 6. Cross-module inlining

Ví dụ:

```text id="a15013"
package math
    fn square(x) → x*x

package app
    fn process(x) {
        return square(x) + 1
    }
```

Không LTO:

```text id="a15014"
process
 ↓
call square
```

Có LTO:

```text id="a15015"
process
 ↓
x*x + 1
```

Sau đó:

```text id="a15016"
constant propagation
algebraic optimization
vectorization
```

có thể tiếp tục.

---

# 7. Cross-module specialization

Ví dụ:

```ax id="a15017"
fn sum<T: Numeric>(data: view<T>) -> T
```

Module A gọi:

```text id="a15018"
sum<f32>
```

Module B gọi:

```text id="a15019"
sum<i32>
```

LTO có thể tạo:

```text id="a15020"
sum_f32
sum_i32
```

và mỗi specialization tiếp tục được:

```text id="a15021"
vectorized
unrolled
target optimized
```

---

# 8. Không specialization mù

Generic instantiation có chi phí:

```text id="a15022"
compile time
binary size
instruction cache
```

Axiom dùng budget từ BOOTSTRAP-142:

```text id="a15023"
SpecializationBudget {
    instance_count
    code_size
    compile_time
    expected_speedup
    hotness
}
```

PGO có thể tăng priority cho specialization thực sự nóng.

---

# 9. Global dead-code elimination

Sau khi nhìn toàn bộ chương trình:

```text id="a15024"
Entry
Exports
FFI roots
Reflection roots
Init/Fini
Interrupt handlers
Explicit keep
```

được xem là roots.

Các function không reachable:

```text id="a15025"
remove
```

Điều này đặc biệt quan trọng cho mục tiêu:

> binary nhỏ như code native tối ưu.

---

# 10. Generic dead-instance elimination

Có thể có:

```text id="a15026"
Vec<i32>
Vec<f32>
Vec<MyHugeType>
Vec<UnusedType>
```

Nếu chỉ:

```text id="a15027"
Vec<i32>
Vec<f32>
```

được instantiate:

```text id="a15028"
unused generic instances
→ eliminate
```

---

# 11. Trait devirtualization xuyên package

Ví dụ:

```ax id="a15029"
fn process<T: Shape>(x: T) {
    x.area()
}
```

Static dispatch:

```text id="a15030"
Shape::area<T>
```

LTO biết:

```text id="a15031"
T = Circle
```

→ direct call:

```text id="a15032"
Circle::area
```

Sau đó inline.

---

# 12. `dyn Trait` vẫn là dynamic boundary

Ví dụ:

```ax id="a15033"
fn process(x: dyn Shape) {
    x.area()
}
```

Compiler không được giả định một concrete type nếu:

```text id="a15034"
multiple types
dynamic loading
FFI
reflection
```

Nhưng nếu whole-program analysis chứng minh:

```text id="a15035"
only Circle can reach this call
```

thì có thể devirtualize.

Nếu không:

```text id="a15036"
retain dynamic dispatch
```

---

# 13. Shared library boundary

Đây là giới hạn quan trọng.

Nếu:

```text id="a15037"
app
 ↓
libfoo.so
```

và `libfoo.so` có thể được thay thế/runtime-loaded:

compiler không được giả định:

```text id="a15038"
closed world
```

Do đó:

```text id="a15039"
static executable
→ stronger whole-program assumptions

dynamic library
→ conservative assumptions
```

---

# 14. Visibility lattice

Axiom có thể phân loại symbol:

```text id="a15040"
PRIVATE
MODULE_VISIBLE
PACKAGE_VISIBLE
PUBLIC
EXPORT
FFI_VISIBLE
REFLECTION_VISIBLE
DYNAMIC
```

Mức càng observable:

```text id="a15041"
optimization freedom ↓
```

Nhưng `pub` vẫn không đồng nghĩa native symbol export.

---

# 15. Whole-program alias analysis

Khi toàn bộ call graph biết được:

```text id="a15042"
foo(a, b)
```

compiler có thể hiểu:

```text id="a15043"
a → Region A
b → Region B
```

và truyền alias facts xuyên function.

Ví dụ:

```text id="a15044"
caller proves A ∩ B = ∅
        ↓
callee receives disjoint capabilities
        ↓
optimizer uses NoAlias
```

Không cần `restrict`.

---

# 16. Whole-program effect analysis

Tương tự:

```text id="a15045"
foo()
```

có thể ban đầu:

```text
Effect = Read + Write
```

nhưng LTO phát hiện:

```text
Write only Region X
```

thì load từ Region Y trước/sau call có thể vẫn được giữ trong register.

Đây là:

```text id="a15046"
Effect
+
Alias
+
MemorySSA
```

ở cấp toàn chương trình.

---

# 17. Whole-program escape analysis

Ví dụ:

```ax id="a15047"
fn create() -> Box<Point> {
    return Box(Point(...));
}
```

Caller:

```ax id="a15048"
let p = create();
use(p);
```

Nếu allocation không escape thật sự:

```text id="a15049"
Box allocation
 ↓
caller allocation
 ↓
stack/register/scalarized
```

có thể được tối ưu xuyên function boundary.

---

# 18. Global constant propagation

Ví dụ:

```ax id="a15050"
const MODE = 3;
```

nhiều module sử dụng:

```text id="a15051"
if MODE == 3 {
    A
} else {
    B
}
```

LTO có thể:

```text id="a15052"
remove B
```

và kéo theo:

```text id="a15053"
remove functions only used by B
remove data only used by B
```

---

# 19. Whole-program data layout

Nếu không có ABI/FFI/reflection constraint:

```text id="a15054"
struct layout
```

có thể được tối ưu dựa trên toàn bộ workload.

Ví dụ compiler phát hiện:

```text id="a15055"
field A → extremely hot
field B → hot
field C → cold
field D → never read
```

có thể:

```text id="a15056"
cluster A/B
separate C
eliminate D if provably unused
```

Nhưng nếu:

```text id="a15057"
@repr(C)
```

thì contract thắng optimization.

---

# 20. Global code layout

LTO có thể xây dựng:

```text id="a15058"
Call Frequency Graph
```

Ví dụ:

```text id="a15059"
A → B 90%
A → C 5%
A → D 5%
```

Có thể đặt:

```text id="a15060"
A
B
```

gần nhau trong binary.

C/D đưa vào cold region.

---

# 21. Hot/cold splitting

Whole program có thể phát hiện:

```text id="a15061"
error handler
panic path
debug path
rare feature
```

và đưa vào:

```text id="a15062"
.text.cold
```

Lợi ích:

```text
I-cache ↓ pressure
binary locality ↑
hot code density ↑
```

---

# 22. Identical Code Folding

Ví dụ sau specialization:

```text id="a15063"
foo<i32>
foo<u32>
foo<MyNewType>
```

có thể cuối cùng tạo machine implementation giống nhau.

Compiler/linker có thể merge:

```text id="a15064"
identical implementation
```

nếu:

- observable semantics giống;
- ABI tương thích;
- function identity không observable;
- Drop/metadata/FFI constraints không khác.

---

# 23. Semantic identity vẫn giữ

Quan trọng:

```text id="a15065"
GenericInstanceId A
≠
GenericInstanceId B
```

dù machine code được share.

Ví dụ:

```text id="a15066"
semantic entities
     ↓
different

machine implementation
     ↓
shared
```

Đây chính là **abstraction erasure** ở mức cao nhất.

---

# 24. Whole-program constant folding

LTO có thể biết:

```text id="a15067"
function input always constant
```

nhưng phải phân biệt:

```text
observed constant
vs
proven constant
```

PGO:

```text
always 42 in profile
```

không đủ để biến thành compile-time constant.

Interprocedural proof:

```text
all legal callers pass 42
```

mới có thể tạo specialization.

---

# 25. Partial evaluation

Axiom có thể hỗ trợ:

```text id="a15068"
foo(const_arg, runtime_arg)
```

→

```text id="a15069"
foo_specialized(runtime_arg)
```

Nếu `const_arg` known:

```text
constant propagation
branch elimination
loop simplification
```

Đây là dạng partial evaluation rất mạnh.

---

# 26. Global bounds-check elimination

Ví dụ:

```ax id="a15070"
fn process(a: view<f32>, n: usize) {
    helper(a, n);
}
```

Nếu caller đã chứng minh:

```text id="a15071"
n <= a.len
```

và contract được truyền xuyên call:

```text id="a15072"
helper
 ↓
bounds checks eliminated
```

Không cần programmer truyền assertion/runtime annotation nếu compiler tự chứng minh được.

---

# 27. Nhưng LTO không được “lách” verifier

Luồng bắt buộc:

```text id="a15073"
Source
 ↓
Typed MIR
 ↓
Verification
 ↓
Verified MIR
 ↓
LTO
```

Không:

```text id="a15074"
Source
 ↓
LTO assumption
 ↓
skip verification
```

LTO chỉ được dùng:

```text id="a15075"
verified facts
```

---

# 28. Incremental LTO

Không thể mỗi lần sửa một dòng:

```text id="a15076"
re-optimize entire universe
```

Axiom sử dụng:

```text id="a15077"
SemanticFingerprint
InterfaceFingerprint
SummaryFingerprint
ProfileFingerprint
```

Nếu chỉ implementation nội bộ thay đổi:

```text id="a15078"
downstream public interface unchanged
```

thì có thể giữ nhiều cached analysis.

Nếu ABI thay đổi:

```text id="a15079"
invalidate ABI-dependent nodes
```

---

# 29. ThinLTO-style architecture

Axiom nên hỗ trợ hai chế độ:

### Full LTO

```text id="a15080"
all semantic optimization data
→ centralized/global optimization
```

### Distributed / Thin LTO

```text id="a15081"
module summaries
       ↓
global index
       ↓
local optimization guided by global facts
```

Thin mode phù hợp build lớn.

---

# 30. Global Optimization Index

Đề xuất:

```text id="a15082"
LTOIndex {
    functions
    symbols
    generic_instances
    call_edges
    trait_edges
    effects
    aliases
    escapes
    exports
    reflection_roots
    profile
    fingerprints
}
```

Có thể cache:

```text id="a15083"
.axlto
```

hoặc tích hợp vào `.axmeta`.

---

# 31. Dynamic loading

Nếu chương trình dùng:

```text
load_library(...)
```

thì compiler phải coi unknown external code là potential root/boundary.

Không được dead-strip symbol mà dynamic loader có thể yêu cầu nếu contract nói symbol đó exported.

---

# 32. Reflection

Nếu runtime reflection được bật:

```text id="a15084"
Type metadata
Function metadata
Field metadata
```

có thể trở thành observable.

Compiler phải preserve những gì reflection contract yêu cầu.

Nếu không runtime reflection:

```text id="a15085"
metadata can be omitted
```

để giảm binary size.

---

# 33. FFI

Một hàm:

```ax id="a15086"
extern "C" fn foo(...)
```

là semantic boundary.

Compiler không được inline qua boundary nếu implementation không có.

Nhưng có thể tối ưu:

```text id="a15087"
arguments
temporary creation
layout
caller-side computation
```

miễn ABI vẫn đúng.

---

# 34. Linker và compiler phải phối hợp

Kiến trúc nên là:

```text id="a15088"
Compiler
   ↓
LTO semantic graph
   ↓
Optimized object
   ↓
Linker graph
   ↓
Section/symbol optimization
   ↓
Final binary
```

Không nên để linker phải hiểu toàn bộ Axiom type system.

Ngược lại compiler không nên tự giả lập toàn bộ platform linker.

Hai bên chia boundary rõ ràng.

---

# 35. LTO + linker dead stripping

Hai tầng:

```text id="a15089"
Semantic DCE
    ↓
Machine/Object DCE
    ↓
Linker section GC
```

Semantic DCE biết:

```text
function meaning
generic instances
traits
reflection
```

Linker biết:

```text
sections
relocations
symbols
platform roots
```

---

# 36. Whole-program optimization và binary size

Đây là một trong những nơi Axiom có thể đạt mục tiêu:

> binary nhỏ gọn.

Pipeline:

```text id="a15090"
unused module
   ↓ remove

unused generic
   ↓ remove

unused function
   ↓ remove

unused constant
   ↓ remove

unused section
   ↓ remove

identical code
   ↓ merge

cold code
   ↓ separate

unused runtime component
   ↓ remove
```

Không cần runtime monolithic.

---

# 37. LTO + runtime composition

Ví dụ chương trình chỉ dùng:

```text
math
filesystem
```

không dùng:

```text
async
GPU
reflection
network
Unicode
```

LTO/linker có thể loại bỏ toàn bộ component không reachable.

Kết quả:

```text id="a15091"
application
+
minimum required runtime
```

thay vì:

```text
application
+
giant runtime
```

---

# 38. Whole-program optimization không có nghĩa “everything visible”

Axiom phải phân biệt:

```text
Closed World
Partial World
Open World
```

### Closed World

Executable hoàn chỉnh, static linking.

→ mạnh nhất.

### Partial World

Một số dynamic libraries.

→ cần conservative assumptions.

### Open World

Plugin/reflection/dynamic loading.

→ rất bảo thủ ở boundary.

---

# 39. Optimization trust hierarchy

Toàn bộ compiler hiện tại có thể thống nhất thành:

```text id="a15092"
SEMANTIC PROOF
      ↓
VERIFIED FACT
      ↓
OPTIMIZATION FACT
      ↓
PROFILE OBSERVATION
      ↓
COST HEURISTIC
```

Tầng dưới không được ghi đè tầng trên.

Ví dụ:

```text
Profile: no alias observed
```

không thắng:

```text
Verifier: alias UNKNOWN
```

---

# 40. Invariants

Đóng băng:

### `ALTO-20`
Whole-program optimization preserves program semantics.

### `ALTO-21`
LTO may optimize across modules when semantic boundaries permit.

### `ALTO-22`
`pub` does not inherently create a machine-code optimization boundary.

### `ALTO-23`
`@export` establishes an observable binary boundary.

### `ALTO-24`
FFI and dynamic-loading boundaries require conservative treatment.

### `ALTO-25`
Whole-program analysis may strengthen optimization facts only through valid proof.

### `ALTO-26`
Profile observations never become semantic proofs.

### `ALTO-27`
Cross-module inlining is permitted when observable semantics remain unchanged.

### `ALTO-28`
Cross-module specialization is permitted under specialization budget.

### `ALTO-29`
Cross-module devirtualization requires a proven target or valid guarded strategy.

### `ALTO-30`
Generic instances may be eliminated when unreachable.

### `ALTO-31`
Unused functions and data may be eliminated when not roots.

### `ALTO-32`
Reflection-visible entities are preserved according to reflection contract.

### `ALTO-33`
Dynamic-loading-visible entities are preserved according to export contract.

### `ALTO-34`
Whole-program alias analysis may propagate verified disjointness.

### `ALTO-35`
Whole-program effect analysis may refine call invalidation.

### `ALTO-36`
Whole-program escape analysis may enable allocation elimination/promotion.

### `ALTO-37`
Whole-program constant propagation must distinguish proof from profile observation.

### `ALTO-38`
Whole-program layout optimization respects explicit representation contracts.

### `ALTO-39`
Code layout may use call frequency and PGO.

### `ALTO-40`
Hot/cold splitting cannot alter observable control-flow semantics.

### `ALTO-41`
Identical implementations may be merged only when observable identity and ABI semantics permit.

### `ALTO-42`
LTO must not bypass Verified MIR.

### `ALTO-43`
LTO must preserve ownership, capability, Drop and concurrency semantics.

### `ALTO-44`
LTO must preserve atomic, volatile and synchronization semantics.

### `ALTO-45`
LTO must preserve async/GPU/FFI contracts.

### `ALTO-46`
Closed-world assumptions must not be applied to open-world program boundaries.

### `ALTO-47`
Incremental LTO uses semantic/interface fingerprints for invalidation.

### `ALTO-48`
Full LTO and distributed/Thin LTO must produce semantically equivalent programs.

### `ALTO-49`
LTO is optional.

### `ALTO-50`
No optimization level may change language semantics.

### `ALTO-51`
LTO decisions are inspectable and explainable.

### `ALTO-52`
Whole-program optimization is deterministic given identical inputs/configuration.

### `ALTO-53`
LTO may eliminate unused runtime components.

### `ALTO-54`
Semantic optimization and machine/linker optimization remain distinct layers.

### `ALTO-55`
Source-to-final-binary provenance must remain inspectable.

---

# Kiến trúc Axiom hiện đã rất mạnh

Từ đầu tới đây, chúng ta đã đi từ:

```text
Language semantics
```

đến:

```text
Ownership
Capability
Concurrency
Async
GPU
```

rồi:

```text
MIR
Verification
Alias
Effect
Escape
```

rồi:

```text
SSA
MemorySSA
Inlining
Specialization
Loop
Memory
Layout
Vectorization
Microarchitecture
PGO
LTO
```

và cuối cùng:

```text
LIR
Machine IR
Object
Linker
Native Binary
```

Nói cách khác, **Axiom hiện đã có một xương sống compiler hoàn chỉnh từ source semantics tới executable**.

---

# BOOTSTRAP-151 — Link-Time Code Generation, Section GC, Binary Size & Post-Link Optimization

Bước tiếp theo hợp lý là đi xuống **phần cuối cùng của pipeline**: sau LTO, compiler/linker cần tối ưu chính binary.

```text id="a15101"
LTO Optimized IR
      ↓
Code Generation
      ↓
Object Files
      ↓
Link Graph
      ↓
Section GC
      ↓
Identical Code Folding
      ↓
Constant/Data Merging
      ↓
Hot/Cold Layout
      ↓
Thunk / PLT / GOT Optimization
      ↓
Relocation Optimization
      ↓
Binary Layout
      ↓
Post-Link Optimization
      ↓
Final EXE / ELF / Mach-O / WASM
```

Đặc biệt 151 sẽ giải quyết mục tiêu **“binary nhỏ như ASM”** ở cấp thực tế: không chỉ compiler tạo machine code tốt, mà **object writer + linker cũng phải tránh mọi byte không cần thiết**, đồng thời không phá ABI, relocation, debugging, unwind hay platform loader requirements.