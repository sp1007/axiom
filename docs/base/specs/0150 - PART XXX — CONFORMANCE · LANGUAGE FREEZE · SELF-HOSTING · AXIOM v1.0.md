# PART XXX — CONFORMANCE · LANGUAGE FREEZE · SELF-HOSTING · AXIOM v1.0

Đây là **phần SPEC cuối cùng** của bộ 30 phần.

Mục tiêu của Part XXX không phải thêm tính năng. Ngược lại:

> **Khóa những gì Axiom có nghĩa là gì, compiler phải tuân thủ điều gì, và từ đây về sau thay đổi nào được phép.**

Một ngôn ngữ không thực sự có specification chỉ vì có grammar. Nó cần một **conformance definition** đủ mạnh để hai compiler độc lập có thể cùng implement một Axiom program và vẫn được xem là implement cùng ngôn ngữ.

---

# 1. Axiom Language Definition

Specification chính thức phải được chia thành:

```text id="2kr5c8"
AXIOM LANGUAGE DEFINITION
│
├── Part I–XXX
│
├── Core Semantics
├── Standard Library Contracts
├── ABI Specification
├── Target Specifications
├── Tooling Contracts
└── Conformance Requirements
```

Trong đó cần phân biệt rõ:

```text id="s8p1w7"
Language
Library
Compiler
Toolchain
Platform
```

Không được trộn chúng.

---

# 2. Ba tầng normative

Mỗi phần specification có ba mức:

### MUST

Bắt buộc.

```text id="j9qf2u"
Compiler MUST reject ...
Compiler MUST preserve ...
Program MUST ...
```

### SHOULD

Khuyến nghị nhưng implementation có thể khác nếu không phá contract.

```text id="4o6j1e"
Compiler SHOULD optimize ...
Tool SHOULD provide ...
```

### MAY

Implementation freedom.

```text id="d9zv5s"
Compiler MAY inline ...
Compiler MAY choose stack ...
Compiler MAY use ...
```

---

# 3. Semantic authority

Khi có tranh chấp:

```text id="n9sv3a"
Specification
    ↓
Normative invariant
    ↓
Conformance test
    ↓
Compiler implementation
```

Compiler source code **không phải specification**.

Oracle cũng không phải specification.

Oracle là implementation độc lập để kiểm chứng specification.

---

# 4. Rule → Invariant → Test

Mọi semantic rule quan trọng phải có chuỗi:

```text id="k6d2g5"
SPEC rule
   ↓
Invariant
   ↓
Positive test
   ↓
Negative test
   ↓
Oracle test
   ↓
Optimization equivalence test
```

Ví dụ:

```text id="nq1m9w"
Rule:
mut_view<T> cannot overlap another active mutable capability
```

↓

```text id="v5f5n4"
ACAP-...
```

↓

```text id="8z9s0v"
valid_mut_view.axiom
```

↓

```text id="q3x3f7"
overlapping_mut_view.axiom
```

↓

Oracle kiểm tra.

↓

`-O0` và `-O3` phải giữ cùng semantic result.

---

# 5. Conformance suite

Repository:

```text id="v4a1qj"
tests/
├── lexical/
├── parser/
├── name/
├── type/
├── trait/
├── generic/
├── ownership/
├── copy/
├── move/
├── view/
├── drop/
├── match/
├── error/
├── async/
├── concurrency/
├── atomic/
├── memory/
├── unsafe/
├── ffi/
├── abi/
├── gpu/
├── comptime/
├── module/
├── package/
├── build/
├── runtime/
├── optimizer/
├── oracle/
├── target/
├── object/
├── linker/
├── diagnostics/
└── tooling/
```

---

# 6. Positive tests

Positive test chứng minh chương trình hợp lệ.

Ví dụ:

```text id="8f49wi"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

expected:

```text
compile: success
run: 30
```

---

# 7. Negative tests

Negative test quan trọng không kém.

Ví dụ:

```axiom id="m6k4eg"
let x = Buffer(...)
let y = x
print(x)
```

expected:

```text
compile: failure
code: AX_MOVE_...
```

Không được chỉ kiểm tra:

```text id="z3k74x"
"compiler failed"
```

mà phải kiểm tra semantic diagnostic class.

---

# 8. Diagnostic conformance

Mỗi diagnostic test nên kiểm tra:

```text id="vqq6v6"
error code
primary span
secondary span
semantic category
```

Không khóa cứng toàn bộ human message.

Ví dụ:

```text id="m9q5oc"
AX_MOVE_0003
```

là stable.

Nhưng:

```text id="1g6q8e"
"value has already been moved"
```

có thể thay đổi cách diễn đạt.

---

# 9. Golden MIR

Các semantic lowering quan trọng có golden MIR:

```text id="m1u1l8"
source
   ↓
expected MIR
```

Ví dụ:

```text id="1q3h2x"
? propagation
match
drop
move
async lowering
closure capture
```

Golden MIR không nhất thiết khóa mọi optimization.

Nó chủ yếu kiểm tra semantic lowering.

---

# 10. Verified MIR tests

Ví dụ:

```text id="a3my1u"
source
 ↓
MIR
 ↓
Verifier
 ↓
Verified MIR
```

Test phải chứng minh:

```text id="5t7w4g"
valid ownership
valid capabilities
valid drops
valid aliasing
valid concurrency
```

---

# 11. Optimization equivalence

Một chương trình hợp lệ phải được chạy ở nhiều mức:

```text id="l7o6b0"
-O0
-O1
-O2
-O3
-Os
-Oz
```

và kết quả observable phải tương đương.

Ví dụ:

```text id="n2l1m5"
Oracle result
=
-O0 result
=
-O3 result
```

trong phạm vi semantics được định nghĩa.

---

# 12. Undefined unsafe behavior

Không thể yêu cầu Oracle mô phỏng mọi thứ trong `unsafe`.

Ví dụ:

```axiom id="x3i1pd"
unsafe {
    *(ptr + 999999)
}
```

nếu vi phạm contract, specification không bắt Oracle phải tạo một kết quả giả.

Nguyên tắc:

> **Undefined/invalid unsafe behavior is outside conformance semantics.**

Oracle phải có thể báo:

```text
UNDEFINED_UNSAFE
```

thay vì tự bịa kết quả.

---

# 13. Safe code conformance

Ngược lại, safe code phải có semantics mạnh.

Không được có:

```text id="p3v8zq"
safe program
→ random machine-dependent behavior
```

chỉ vì compiler/backend khác nhau.

Safe program phải có observable behavior được specification xác định.

---

# 14. Implementation freedom

Compiler được tự do:

```text id="x3kn8y"
stack vs register
heap vs stack
inline vs call
scalar vs vector
allocation elimination
layout optimization
enum niche
code ordering
instruction selection
```

miễn:

```text id="k8d1u3"
observable semantics preserved
```

Đây là cơ sở cho zero-cost abstraction.

---

# 15. Conformance levels

Axiom có thể định nghĩa:

### Core Conforming

```text id="x7n8m1"
Core language
Oracle
basic target
```

### Hosted Conforming

Thêm:

```text id="s8b2pz"
OS startup
standard runtime components
```

### Native Conforming

Thêm:

```text id="5k9f2w"
native ABI
object
linker
```

### Full Toolchain Conforming

Thêm:

```text id="7n1x8q"
debug
diagnostics
LSP
trace
profiler
sanitizer
```

Compiler không nhất thiết phải hỗ trợ mọi target để được Core Conforming.

---

# 16. Target conformance

Một target declaration:

```text id="2s4m6z"
Target: x86_64-linux
```

chỉ được gọi là conforming khi pass:

```text id="6v5g2k"
language tests
ABI tests
object tests
runtime tests
FFI tests
```

Các test target-specific được phân loại riêng.

---

# 17. ABI conformance

ABI test phải kiểm tra:

```text id="r8y7s2"
type size
alignment
field offsets
calling convention
argument passing
return passing
enum representation
aggregate return
symbol naming
TLS
unwind
```

Ví dụ:

```text id="x0r5sa"
extern "C" fn foo(Vec3) -> Vec3
```

phải có expected ABI theo target.

---

# 18. Object conformance

Object writer test:

```text id="e3q4k1"
source
 ↓
object
```

kiểm tra:

```text id="8z6r2j"
header
sections
symbols
relocations
alignment
debug sections
```

Không chỉ kiểm tra executable cuối cùng.

---

# 19. Linker conformance

Linker test:

```text id="p2m3t8"
foo.o
+
bar.o
+
lib.a
 ↓
program
```

kiểm tra:

```text id="8u7s2q"
symbol resolution
relocations
section layout
dead code elimination
exports
imports
TLS
```

---

# 20. Self-hosting test

Một milestone đặc biệt:

```text id="z3p1w6"
stage0 compiler
     ↓
build compiler source
     ↓
stage1 compiler
     ↓
stage1 builds itself
     ↓
stage2 compiler
```

Sau đó:

```text id="r4u2s9"
stage1 compiler
vs
stage2 compiler
```

phải cho kết quả tương đương về semantics.

---

# 21. Three-stage bootstrap

Axiom nên có test kinh điển:

```text id="6f8w2j"
A = bootstrap compiler
B = compiler built by A
C = compiler built by B
```

Sau đó:

```text id="f0m4y2"
B builds compiler → C
C builds compiler → D
```

Nếu:

```text id="z1q9r8"
C == D
```

về binary reproducibility trong cùng môi trường, đó là một tín hiệu rất mạnh.

---

# 22. Compiler self-reproducibility

Mục tiêu:

```text id="9v1q6k"
source compiler
 + compiler version
 + deterministic environment
       ↓
same compiler binary
```

Không nhất thiết bắt buộc byte-identical trên mọi target.

Nhưng trong cùng target/profile/environment, reproducibility là mục tiêu chuẩn.

---

# 23. Compiler bootstrap trust

Không được có vòng:

```text id="g6f2j8"
compiler says compiler is correct
```

Thay vào đó:

```text id="6h7v4a"
Specification
     +
Oracle
     +
Conformance Suite
     +
Independent Tests
     ↓
Compiler
```

Compiler tự build được **không chứng minh compiler đúng**.

---

# 24. Differential compiler testing

Axiom có thể có:

```text id="q8p5z0"
Compiler A
Compiler B
Oracle
```

cùng chạy một program.

Nếu:

```text id="1m9s4x"
A == B == Oracle
```

confidence tăng rất mạnh.

Trong bootstrap:

```text id="3y7k1p"
external compiler
vs
Axiom compiler
```

cũng có thể dùng differential testing.

---

# 25. Fuzzing compiler

Fuzzer sinh:

```text id="x7h4p2"
valid programs
invalid programs
boundary programs
generic programs
ownership programs
async programs
unsafe programs
```

Compiler phải:

```text id="0p6j8m"
never crash
```

trừ internal compiler failure được xác định rõ.

Compiler crash trở thành regression test.

---

# 26. Metamorphic testing

Không phải lúc nào cũng cần biết output đúng tuyệt đối.

Có thể kiểm tra:

```text id="m1f8z2"
P
```

và transformation:

```text id="e4q9n6"
P'
```

phải có quan hệ semantics đã biết.

Ví dụ:

```text id="2z6p7a"
x + 0
```

vs transformation tương đương.

Hoặc:

```text id="k8w2q3"
-O0
```

vs:

```text id="n7r4m1"
-O3
```

---

# 27. Compiler internal errors

Compiler không được biến mọi bug thành:

```text id="z6r4x1"
"invalid program"
```

Nếu internal invariant bị phá:

```text id="m7k1p4"
AXC_INTERNAL_...
```

Phải tạo crash artifact:

```text id="q2v8n0"
compiler version
target
source hash
pass
IR snapshot
diagnostic context
```

nhưng không tự động upload source.

---

# 28. Versioning

Axiom dùng semantic versioning ở language level:

```text id="7v1n3k"
MAJOR.MINOR.PATCH
```

Nhưng language version và compiler version khác nhau.

Ví dụ:

```text id="8s2q4p"
Axiom language 1.0
Compiler 1.3.7
```

Compiler mới có thể implement Axiom 1.0.

---

# 29. Language version

Source có thể chỉ định:

```axiom id="k1f7q9"
@language("1.0")
```

hoặc package manifest:

```text id="0s4d6n"
language = "1.0"
```

Compiler biết semantic target.

---

# 30. Compatibility

Compiler Axiom 2.x có thể hỗ trợ:

```text id="n3x8m5"
Axiom 1.x source
```

nhưng không được âm thầm thay semantics.

Nếu có incompatibility:

```text id="v7j2r6"
diagnostic
migration suggestion
```

---

# 31. Deprecation

Feature không nên bị xóa ngay.

Flow:

```text id="j5r8x1"
stable
 ↓
deprecated
 ↓
migration period
 ↓
removed in next major language version
```

Compiler phải cung cấp:

```text id="m2q7p9"
warning
replacement
machine-applicable fix
```

nếu có thể.

---

# 32. Không được “feature creep” Core

Sau v1.0, một proposal mới không được thêm vào Core chỉ vì:

```text id="6x1n8m"
"ngôn ngữ khác có"
```

Phải chứng minh:

```text id="y7r3p4"
semantic need
performance value
composability
implementation cost
tooling impact
ABI impact
conformance impact
```

---

# 33. Evolution principle

Axiom giữ nguyên triết lý:

> **One Semantic Question, One Mechanism.**

Nếu một proposal tạo ra hai cơ chế giải quyết cùng một semantic question:

```text id="3v8q2w"
ownership mechanism A
ownership mechanism B
```

thì mặc định phải phản biện proposal.

---

# 34. Core stability

Những thứ nên được coi là nền tảng cực khó thay đổi:

```text id="h9f3k1"
value semantics
ownership
Copy
Move
Drop
view
mut_view
Option
Result
trait model
struct model
unsafe boundary
deterministic evaluation
```

Thay đổi chúng sau v1.0 có thể tạo breaking semantic change cực lớn.

---

# 35. Compiler freedom stability

Ngược lại, những thứ compiler **được tự do thay đổi**:

```text id="w2n7s5"
register allocation
instruction selection
stack layout
optimization strategy
inline heuristics
generic code sharing
allocation elimination
internal IR structure
```

không phải language compatibility contract.

Đây là điều cực kỳ quan trọng để Axiom không tự khóa compiler vào implementation cũ.

---

# 36. IR không phải public language contract

Mặc dù chúng ta có:

```text id="c8m4x1"
AST
HIR
MIR
LIR
Machine IR
```

nhưng chỉ một số semantic properties là public.

Compiler có thể đổi:

```text id="j5w9r2"
MIR representation
```

miễn vẫn giữ semantics.

---

# 37. Oracle cũng có thể tiến hóa

Oracle không phải ABI.

Có thể thay đổi implementation Oracle để:

```text id="a7p2m9"
faster
more precise
better diagnostics
```

miễn output semantic tương đương.

---

# 38. Standard Library versioning

Core language và standard library phải tách:

```text id="q9s5t1"
Axiom Language 1.0
Axiom Std 1.0
```

Một compiler có thể hỗ trợ:

```text id="p4m7x2"
Language 1.0
Std 1.2
```

nếu contracts tương thích.

---

# 39. Core library boundary

Không được đẩy tất cả vào language.

Ví dụ:

```text id="g8n2r5"
Vec
Map
HashMap
String
File
Socket
Thread
Mutex
Channel
Arc
```

là library.

Trong khi:

```text id="k4v9s1"
ownership
move
trait
generic
view
async semantic lowering
```

là language/compiler semantics.

---

# 40. Toolchain boundary

Toolchain:

```text id="j2q6w8"
compiler
linker
formatter
LSP
debugger integration
profiler
package manager
```

không phải Core language.

Điều này cho phép:

```text id="m6t3r9"
minimal compiler
```

vẫn tồn tại cho embedded/freestanding.

---

# 41. Axiom v1.0 Core

Sau toàn bộ thiết kế, Core v1.0 có thể được tóm tắt:

```text id="b4k7n2"
Static typing
Value semantics
Struct
Enum
Pattern matching
Functions
Closures
Traits
Generics
Associated types
Ownership
Move
Copy
Drop
view
mut_view
Option
Result
?
panic
unsafe
raw pointers
modules
visibility
comptime
const/static
async/await semantics
Send/Share
atomics
deterministic evaluation
FFI
ABI
GPU execution-domain semantics
```

Không có:

```text id="r7m2c8"
class
inheritance
GC
implicit RC
mandatory runtime
mandatory heap
null
exceptions
macro language
implicit conversion graph
programmer lifetime syntax
```

---

# 42. Axiom v1.0 philosophy

Toàn bộ language có thể rút lại thành:

> **Axiom là một statically typed systems language với value semantics, deterministic ownership, compiler-managed lifetime verification, explicit capability-based access, zero-cost abstraction, optional runtime components và native compilation.**

Và nguyên tắc thiết kế:

> **Explicit at semantic boundaries, implicit within the compiler.**

---

# 43. Final semantic stack

Đây là kiến trúc semantic cuối cùng:

```text id="x8j3q6"
                  AXIOM
                    │
        ┌───────────┴───────────┐
        │                       │
     VALUES                  EFFECTS
        │                       │
 Ownership                  Mutation
 Move/Copy                  Async
 Drop                       Concurrency
 Capability                Atomic
        │                   GPU
        └───────────┬───────────┘
                    │
                 VERIFIED
                    │
                    ▼
                   MIR
                    │
              OPTIMIZATION
                    │
                    ▼
                   LIR
                    │
              TARGET LOWERING
                    │
                    ▼
              MACHINE CODE
                    │
                    ▼
              OBJECT / LINK
                    │
                    ▼
             NATIVE BINARY
```

---

# 44. Final verification stack

```text id="f4k8n2"
SPECIFICATION
      ↓
INVARIANTS
      ↓
CONFORMANCE TESTS
      ↓
ORACLE
      ↓
COMPILER
      ↓
OPTIMIZATION DIFFERENTIAL TEST
      ↓
TARGET TEST
      ↓
ABI TEST
      ↓
SELF-HOSTING TEST
```

Đây là điểm tôi đánh giá rất quan trọng trong toàn bộ thiết kế:

**Axiom không chỉ được thiết kế như một language; nó được thiết kế như một hệ thống có khả năng tự kiểm chứng.**

---

# 45. Final self-hosting roadmap

## Stage 0 — Bootstrap

```text
External compiler
    ↓
Axiom compiler
```

Mục tiêu:

- parser
- resolver
- type checker
- MIR
- verifier
- Oracle integration

---

## Stage 1 — Native backend

```text
Axiom compiler
    ↓
x86-64
    ↓
ELF
```

Không còn phụ thuộc LLVM ở code generation.

---

## Stage 2 — Compiler written in Axiom

```text
compiler/
*.axiom
```

Compiler bắt đầu tự compile chính mình.

---

## Stage 3 — Self-hosting

```text
Axiom compiler
      ↓
Axiom compiler
```

---

## Stage 4 — Own object writer

```text
Axiom compiler
      ↓
ELF/COFF/Mach-O
```

không cần assembler.

---

## Stage 5 — Own linker

```text
Axiom compiler
      +
Axiom linker
```

---

## Stage 6 — Reproducible bootstrap

```text
stage0
  ↓
stage1
  ↓
stage2
  ↓
stage3
```

và kiểm tra convergence.

---

# 46. FINAL CONFORMANCE CRITERIA

Một Axiom compiler được gọi là **Axiom 1.0 Conforming** nếu:

```text id="g3m8q1"
✓ lexical conformance
✓ grammar conformance
✓ type conformance
✓ ownership conformance
✓ capability conformance
✓ drop conformance
✓ trait/generic conformance
✓ error/panic conformance
✓ async conformance
✓ concurrency conformance
✓ atomic conformance
✓ unsafe contract conformance
✓ FFI/ABI conformance
✓ module/package conformance
✓ comptime conformance
✓ GPU conformance where target-supported
✓ optimizer semantic equivalence
✓ diagnostic schema conformance
✓ Oracle differential conformance
```

Native target còn phải thêm:

```text
✓ ABI
✓ object
✓ relocation
✓ linker
✓ executable
```

---

# 47. FINAL AXIOM v1.0 FREEZE

Từ đây, specification có thể được coi là:

```text
AXIOM LANGUAGE v1.0
```

với ba loại thay đổi:

### Non-breaking

```text
compiler optimization
new target
new debugger support
new profiler
new standard-library API
```

### Controlled evolution

```text
new library abstraction
new comptime capability
new backend
new tooling protocol
```

### Breaking

```text
ownership semantics
type semantics
evaluation order
ABI contract
Drop semantics
capability rules
async/concurrency semantics
```

Breaking changes chỉ thuộc major language version mới.

---

# 48. Một nguyên tắc cuối cùng cần khóa

Sau 30 phần, tôi muốn thêm một invariant tổng hợp:

### **AAXIOM-001 — Semantic Stability**

> Một chương trình Axiom hợp lệ phải có cùng language-level semantics bất kể compiler sử dụng implementation strategy nào, optimization level nào, storage strategy nào, register allocation nào, hoặc target representation nào, trong phạm vi target được specification định nghĩa.

Và:

### **AAXIOM-002 — Implementation Freedom**

> Compiler được tự do thay đổi mọi implementation detail không observable đối với Axiom semantics.

Hai invariant này chính là nền móng để đạt đồng thời:

```text
HIGH LEVEL
      +
LOW LEVEL CONTROL
      +
ZERO-COST ABSTRACTION
      +
AGGRESSIVE OPTIMIZATION
```

---

# 49. Axiom đã hoàn tất 30 phần SPEC

```text
01  Lexical Structure
02  Grammar
03  Names / Resolution
04  Types
05  Expressions
06  Statements / Blocks
07  Functions / Closures
08  Struct / Enum
09  Traits / Generics
10  Ownership / Move / Copy
11  View / Capability
12  Drop
13  Error / Panic
14  Async
15  Concurrency
16  Atomics
17  Memory / Allocation
18  Unsafe
19  FFI / ABI
20  GPU
21  Comptime / Reflection
22  Modules / Packages
23  Build
24  Runtime / Profiles
25  Compiler Pipeline
26  Semantic Oracle
27  Diagnostics / IDE / AI
28  Debug / Tooling / Profiler
29  Native Target / Object / Linker
30  Conformance / Freeze / Self-hosting
```

**SPEC-01 → SPEC-30: hoàn tất.**

---

# Nhưng chưa nên bắt đầu code ngay

Bước tiếp theo không phải thêm `SPEC-31`.

Nó là **GLOBAL CONTRADICTION AUDIT**.

Tôi sẽ rà lại toàn bộ kiến trúc theo các trục có khả năng gây lỗi nhất:

```text
Ownership
      ↕
Copy / Move / Drop
      ↕
view / mut_view
      ↕
Allocation / relocation
      ↕
Async / await
      ↕
Threads / Send / Share
      ↕
Atomic
      ↕
Unsafe / provenance
      ↕
FFI / ABI
      ↕
GPU
      ↕
Comptime
      ↕
Traits / Generics
      ↕
Optimizer
      ↕
Oracle
      ↕
Native backend
```

Sau đó sẽ kiểm tra một vấn đề còn quan trọng hơn:

> **Liệu Axiom có thực sự đạt mục tiêu “đơn giản cho lập trình viên nhưng mạnh ngang systems language”, hay trong quá trình thiết kế chúng ta đã vô tình tạo ra một Rust thứ hai với quá nhiều quy tắc ẩn?**

Đây là audit cuối cùng trước khi chuyển sang **`AXIOM-SPECIFICATION.md` + architecture blueprint + compiler implementation plan**.