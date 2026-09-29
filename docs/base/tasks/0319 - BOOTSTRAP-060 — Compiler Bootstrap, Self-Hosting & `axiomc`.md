Tiếp tục với **BOOTSTRAP-060**. Đây là bước rất quan trọng vì từ đây ta chuyển từ “Axiom có kiến trúc compiler” sang **“làm thế nào xây compiler thật và cuối cùng compiler tự build chính nó.”**

# BOOTSTRAP-060 — Compiler Bootstrap, Self-Hosting & `axiomc`

## 1. Mục tiêu

Axiom cuối cùng phải đạt:

```text
Axiom source
     ↓
     axiomc
     ↓
 native executable
```

và quan trọng hơn:

```text
axiomc.ax
     ↓
 axiomc₀
     ↓
 axiomc₁
     ↓
 axiomc₁ build axiomc.ax
     ↓
 axiomc₂
```

Trong đó:

> **axiomc₂ được tạo bởi chính Axiom compiler chạy trên chính source compiler của nó.**

Đây mới là self-hosting thực sự.

---

# 2. Không nên cố self-host ngay từ đầu

Bootstrap nên chia thành các stage.

```text
Stage 0
External implementation
        ↓
Stage 1
Axiom compiler prototype
        ↓
Stage 2
Compiler viết bằng Axiom
        ↓
Stage 3
Axiom tự build
```

---

# 3. Stage-0

Stage-0 có thể viết bằng một ngôn ngữ đã tồn tại.

Mục tiêu:

```text
parse Axiom
→ type check
→ MIR
→ verify
→ codegen
```

Không cần đẹp.

Nó là **bootstrap vehicle**.

---

# 4. Stage-0 backend

Ban đầu có thể:

```text
Axiom
 ↓
Stage-0 compiler
 ↓
LLVM IR
 ↓
LLVM
 ↓
native
```

hoặc:

```text
Axiom
 ↓
Stage-0
 ↓
C
 ↓
C compiler
```

Nhưng đây chỉ là bootstrap.

---

# 5. Không đưa LLVM vào specification

Điểm này rất quan trọng.

Axiom specification chỉ định:

```text
Axiom semantics
MIR
ABI
machine behavior
object format
```

Không chỉ định:

```text
LLVM
Clang
GCC
MSVC
```

---

# 6. Stage-1

Stage-1 có thể vẫn được build bằng Stage-0:

```text
axiomc.ax
    ↓
stage0
    ↓
axiomc1
```

`axiomc1` đã là compiler native.

---

# 7. Stage-2

Sau đó dùng:

```text
axiomc1
```

để build lại:

```text
axiomc.ax
```

tạo:

```text
axiomc2
```

Nếu:

```text
axiomc2
```

có thể build lại source compiler thành:

```text
axiomc3
```

và output ổn định → bootstrap convergence.

---

# 8. Three-stage verification

Có thể kiểm tra:

```text
S
 ↓
C0(S) = C1
 ↓
C1(S) = C2
 ↓
C2(S) = C3
```

Nếu:

```text
C2 ≈ C3
```

thì compiler đã đạt bootstrap stability ở mức phù hợp.

Không nhất thiết byte-for-byte giống nhau nếu build metadata/timestamp khác.

---

# 9. Reproducible bootstrap

Tốt hơn nữa:

```text
C2(S) == C3(S)
```

byte-for-byte trong reproducible mode.

Đây là mục tiêu rất đáng giá.

---

# 10. Compiler source tree

Tôi đề xuất compiler không chia theo “feature ngôn ngữ” một cách tùy tiện mà theo pipeline:

```text
compiler/
├── source/
├── lexer/
├── parser/
├── syntax/
├── resolver/
├── types/
├── traits/
├── comptime/
├── hir/
├── mir/
├── verify/
├── opt/
├── abi/
├── lir/
├── machine/
├── object/
├── linker/
├── diagnostics/
├── incremental/
├── query/
├── driver/
└── targets/
```

---

# 11. `source`

Quản lý:

```text
SourceFileId
SourceSpanId
line maps
UTF-8
source revisions
```

---

# 12. Lexer

Lexer chỉ chịu trách nhiệm:

```text
source bytes
 ↓
tokens
```

Không type check.

---

# 13. Parser

```text
tokens
 ↓
AST
```

AST nên giữ source spans đầy đủ.

---

# 14. Syntax database

AST không nên là cấu trúc duy nhất.

Có thể có:

```text
SyntaxTree
SyntaxNodeId
```

giúp:

- IDE
- incremental parsing
- diagnostics
- refactoring.

---

# 15. Resolver

Resolver:

```text
names
imports
modules
visibility
overloads
```

→ semantic declarations.

---

# 16. Type engine

`TypeDB` đã được thiết kế ở 054.

Nhiệm vụ:

```text
type inference
unification
trait resolution
generic substitution
coercion
operator resolution
```

---

# 17. Trait solver

Tách thành query:

```text
solve(T: Trait)
```

Kết quả:

```text
Proven
NotProven
Ambiguous
Error
```

Có memoization.

---

# 18. HIR

AST gần source.

HIR gần semantic language.

Ví dụ:

```axiom
a.foo(x)
```

AST:

```text
MethodCall(foo)
```

HIR có thể đã resolve thành:

```text
Call(
    FunctionId::foo,
    receiver=a,
    args=[x]
)
```

---

# 19. Typed HIR

Tại đây mỗi expression có type:

```text
expr → TypeId
```

và semantic properties.

---

# 20. MIR

HIR:

```text
high-level semantics
```

MIR:

```text
explicit control flow
ownership
capabilities
drops
calls
memory effects
```

MIR là compiler semantic backbone.

---

# 21. Verified MIR

Chỉ khi:

```text
ownership
capability
drop
Send/Share
async
GPU
FFI
```

được kiểm tra xong:

```text
VerifiedMIR
```

mới được truyền xuống optimization/backend.

---

# 22. Compiler trust boundary

Đây là một invariant kiến trúc rất mạnh:

```text
Source
 ↓
compiler analysis
 ↓
Verified MIR
 ║
 ║ TRUST BOUNDARY
 ║
 ↓
optimization/backend
```

Backend không được “sửa” semantics.

---

# 23. Query architecture

Compiler nên là **query-driven compiler**, không phải một pipeline khổng lồ mutable state.

Ví dụ:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solution(trait_ref)
lower_hir(fn)
lower_mir(fn)
verify_mir(fn)
optimize(fn)
layout(type)
abi(fn)
machine(fn)
object(module)
```

---

# 24. Dependency graph

Ví dụ:

```text
machine(foo)
 ↓
abi(foo)
 ↓
layout(TypeA)
 ↓
type(TypeA)
 ↓
parse(moduleA)
```

Compiler biết chính xác dependency.

---

# 25. Incremental compilation

Nếu sửa:

```text
fn foo()
```

thì không nên rebuild toàn bộ project.

Query engine invalidates:

```text
foo HIR
foo MIR
foo optimization
foo machine code
```

và những thứ phụ thuộc thực sự.

---

# 26. Semantic fingerprint

Không dùng:

```text
file timestamp
```

làm nguồn sự thật.

Fingerprint dựa trên:

```text
source
public API
types
traits
ABI
repr
comptime dependencies
target
compiler semantic version
```

---

# 27. Public/private invalidation

Nếu sửa private implementation:

```text
fn internal()
```

không làm invalid toàn bộ downstream modules nếu public semantic interface không thay đổi.

---

# 28. Interface metadata

Mỗi module/package có thể sinh:

```text
module.axmeta
```

chứa:

```text
public declarations
types
traits
generic metadata
ABI
repr contracts
comptime dependencies
semantic fingerprints
```

---

# 29. AI-friendly compiler

Đây là một điểm Axiom có thể làm khác.

Compiler diagnostic không chỉ:

```text
error: something went wrong
```

mà:

```text
{
    code: "EOWN-014",
    category: "ownership",
    source_span: ...,
    subject: ...,
    expected: ...,
    actual: ...,
    related_spans: [...],
    facts: [...]
}
```

---

# 30. AI không được tham gia semantic compilation

AI có thể:

```text
explain diagnostic
suggest fix
query compiler DB
navigate code
```

nhưng:

> **Compiler không được gọi AI để quyết định semantics.**

Nếu AI trả lời khác nhau → compilation không được khác nhau.

---

# 31. Determinism

Cùng:

```text
source
compiler
target
configuration
dependencies
```

phải có cùng semantic result.

Parallel compilation không được tạo semantic race.

---

# 32. Parallel queries

Các query độc lập:

```text
type(A)
type(B)
type(C)
```

có thể chạy song song.

Database phải đảm bảo:

```text
parallel result == serial result
```

---

# 33. Compiler memory architecture

Compiler itself có thể dùng:

```text
arena
intern pool
immutable IDs
generation IDs
query cache
```

Điều này không liên quan đến runtime memory model của chương trình Axiom.

Đây là distinction rất quan trọng:

> **Compiler implementation memory ≠ Axiom program memory semantics.**

---

# 34. Interning

Type:

```text
i32
Vec<i32>
Option<Vec<i32>>
```

nên được intern.

Hai query tạo cùng semantic type:

```text
TypeId(42)
```

---

# 35. Immutable semantic objects

Các semantic objects nên immutable sau khi canonicalized:

```text
Type
TraitRef
GenericSubstitution
Layout
AbiSignature
```

Giảm bug do mutation.

---

# 36. Arenas

Compiler internal objects có thể nằm trong arena:

```text
HIR arena
MIR arena
syntax arena
diagnostic arena
```

Không có ý nghĩa runtime đối với chương trình được compile.

---

# 37. ID thay vì pointer nội bộ

Compiler nên ưu tiên:

```text
TypeId
FunctionId
ModuleId
InstructionId
```

thay vì chia sẻ raw pointers khắp compiler.

Điều này giúp:

- serialization
- caching
- incremental
- debugging
- parallelism.

---

# 38. Compiler database

Kiến trúc:

```text
CompilerDB
│
├── SourceDB
├── PackageDB
├── ModuleDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── GenericDB
├── ConstDB
├── HIRDB
├── MIRDB
├── VerifyDB
├── OptDB
├── LayoutDB
├── AbiDB
├── MachineDB
├── ObjectDB
├── LinkDB
├── DiagnosticDB
└── SourceMapDB
```

---

# 39. Query cycle

Trait solving có thể gặp:

```text
A requires B
B requires A
```

Query engine phải phát hiện cycle.

Không được recursion vô hạn.

---

# 40. Query cancellation

IDE có thể yêu cầu:

```text
type_check(file)
```

rồi user tiếp tục gõ.

Compiler nên cancel revision cũ và bắt đầu revision mới.

---

# 41. Revision model

```text
Revision 100
   ↓
edit source
   ↓
Revision 101
```

Query cache của revision 100 vẫn có thể tái sử dụng nếu dependency fingerprint phù hợp.

---

# 42. Compiler driver

CLI:

```text
axiom build
axiom run
axiom test
axiom check
axiom fmt
axiom doc
axiom clean
```

Compiler executable:

```text
axiomc
```

Package/build driver có thể là:

```text
axiom
```

---

# 43. `axiom check`

Chỉ:

```text
parse
resolve
type
verify
```

không codegen.

Rất hữu ích cho IDE/AI.

---

# 44. `axiom build`

```text
parse
→ verify
→ optimize
→ codegen
→ object
→ link
```

---

# 45. `axiom build --emit`

Có thể:

```text
--emit=ast
--emit=hir
--emit=mir
--emit=verified-mir
--emit=lir
--emit=machine
--emit=obj
```

Điều này cực kỳ hữu ích để debug compiler.

---

# 46. Compiler explain mode

Ví dụ:

```text
axiom explain ownership EOWN-014
```

hoặc:

```text
axiom explain-opt foo
```

Output:

```text
view was proven non-escaping
→ stack allocation selected
→ heap allocation eliminated
```

---

# 47. Machine-readable mode

```text
axiom check --format=json
```

phục vụ:

- IDE
- AI agents
- CI
- compiler automation.

---

# 48. Compiler testing architecture

Không chỉ unit test.

Cần:

```text
unit tests
parser tests
type tests
trait tests
MIR tests
verification tests
optimization tests
ABI tests
machine encoding tests
linker tests
integration tests
runtime tests
```

---

# 49. Semantic test

Ví dụ:

```text
let x = Foo()
let y = x
use(x)
```

phải luôn fail vì move.

Không phụ thuộc optimization level.

---

# 50. Optimization differential tests

Compile:

```text
-O0
-O1
-O2
-O3
```

và chạy cùng input.

Observable result phải tương đương.

---

# 51. Fuzzing

Axiom compiler rất phù hợp với fuzzing:

```text
random source
 ↓
parser
 ↓
type checker
 ↓
MIR
```

và đặc biệt:

```text
MIR verifier fuzzing
```

---

# 52. Translation validation

Một optimization pass có thể được kiểm chứng bằng:

```text
before MIR
vs
after MIR
```

để kiểm tra semantic equivalence trong phạm vi có thể chứng minh.

---

# 53. Backend differential testing

Trong bootstrap:

```text
Axiom → LLVM
Axiom → Axiom backend
```

chạy cùng test corpus.

Nếu:

```text
result_A != result_B
```

điều tra compiler bug.

---

# 54. Compiler bootstrap tests

Đặc biệt:

```text
stage0 builds stage1
stage1 builds stage2
stage2 builds stage3
```

và so sánh:

```text
semantic behavior
compiler test suite
reproducible artifact
```

---

# 55. Trusting Trust

Self-hosting có một vấn đề nổi tiếng:

> Compiler có thể chứa backdoor tự tái sinh khi compiler build chính nó.

Axiom có thể giảm rủi ro bằng:

```text
bootstrap diversity
reproducible builds
stage comparison
source auditing
independent bootstrap
```

Không thể giải quyết tuyệt đối bằng language semantics.

---

# 56. Stage-0 diversity

Sau khi Axiom ổn định, có thể có:

```text
bootstrap compiler A
bootstrap compiler B
```

viết bằng hai implementation khác nhau.

Nếu cả hai build ra compiler có behavior tương đương, confidence tăng.

---

# 57. Compiler version identity

Binary compiler nên chứa:

```text
Axiom compiler version
language semantic version
target backend version
build identity
```

nhưng metadata này không nên ảnh hưởng codegen nếu reproducibility yêu cầu.

---

# 58. Compiler/plugin boundary

Không nên cho compiler plugin arbitrary native code can thiệp semantic compiler.

Plugin nếu có sau này phải capability-restricted.

Core compiler semantics phải deterministic.

---

# 59. Compiler configuration

Các semantic-affecting options phải explicit.

Ví dụ:

```text
target
architecture
float profile
panic mode
ABI
feature flags
```

được đưa vào compilation identity.

---

# 60. Optimization flags

```text
-O0
-O1
-O2
-O3
-Os
```

chỉ thay đổi optimization, không được thay đổi language semantics.

---

# 61. Compiler cache

Cache hierarchy:

```text
Source cache
↓
Syntax cache
↓
HIR cache
↓
MIR cache
↓
Verified MIR cache
↓
OptIR cache
↓
Machine/Object cache
```

---

# 62. Verified MIR cache

Có thể cache Verified MIR nếu fingerprint:

```text
source
dependencies
compiler semantic version
target-independent semantic configuration
```

không đổi.

---

# 63. Machine cache

Machine code cache phải bao gồm:

```text
target architecture
CPU features
ABI
optimization level
compiler backend version
```

---

# 64. Cross compilation

Compiler host:

```text
Windows x64
```

có thể build:

```text
Linux ARM64
```

mà không cần chạy target.

Architecture:

```text
Host
Target
```

luôn tách biệt.

---

# 65. Comptime host vs target

Đây là điểm cần rất rõ.

Comptime mặc định chạy trên:

```text
host
```

nhưng có thể query:

```text
target
```

thông qua explicit target metadata.

Không được nhầm:

```text
host CPU
```

với:

```text
target CPU
```

---

# 66. Cross compilation tới GPU

Tương tự:

```text
host compiler
 ↓
GPU target backend
```

comptime chạy trên host, kernel được compile cho device.

---

# 67. Compiler executable size

Không cần áp dụng “small binary” cực đoan cho compiler.

Compiler có thể lớn.

Mục tiêu:

```text
generated application
```

mới cần zero-runtime/size optimization.

---

# 68. Compiler architecture final

```text
                    axiom
                      │
             ┌────────┴────────┐
             │                 │
          Package             IDE
             │
           axiomc
             │
 ┌───────────┴───────────────────────────┐
 │                                       │
 ▼                                       │
Source → AST → HIR → Typed HIR → MIR     │
                                  │       │
                                  ▼       │
                              Verified    │
                                  │       │
                                  ▼       │
                                OptIR     │
                                  │       │
                                  ▼       │
                               ABI MIR    │
                                  │       │
                                  ▼       │
                                LIR       │
                                  │       │
                                  ▼       │
                             Machine IR   │
                                  │       │
                                  ▼       │
                            Object Writer │
                                  │       │
                                  ▼       │
                              Linker      │
                                  │       │
                                  ▼       │
                              Binary      │
```

Query engine nằm xuyên suốt toàn bộ pipeline.

---

# 69. Self-hosting architecture

Cuối cùng:

```text
                axiomc.ax
                    │
                    ▼
             ┌────────────┐
             │   axiomc   │
             └─────┬──────┘
                   │
                   ▼
             native axiomc
                   │
                   │ compile itself
                   ▼
             new axiomc
                   │
                   ▼
             stable compiler
```

Không cần:

```text
LLVM
Clang
GCC
Rust
C++
```

ở production semantic/codegen path.

---

# 70. BOOTSTRAP-060 invariants

```text id="q1v6c7"
ABOOT-20   Axiom compiler semantics are independent of the bootstrap implementation language.
ABOOT-21   External compilers may be used during bootstrap.
ABOOT-22   External compilers are not required by the final language architecture.
ABOOT-23   Stage-0 is a bootstrap vehicle, not a language dependency.
ABOOT-24   Stage-1 may compile Axiom compiler source into native code.
ABOOT-25   Stage-2 may be built by an Axiom compiler.
ABOOT-26   Self-hosting is achieved when the Axiom compiler can build its own compiler source.
ABOOT-27   Reproducible bootstrap should permit stable stage comparison.
ABOOT-28   Compiler semantic results are deterministic for fixed inputs and configuration.
ABOOT-29   Parallel compilation must be semantically equivalent to serial compilation.
ABOOT-30   Compiler query results are dependency-aware.
ABOOT-31   Incremental compilation uses semantic dependency identity.
ABOOT-32   Timestamps are not semantic compilation identity.
ABOOT-33   Public interface changes invalidate dependent semantic queries.
ABOOT-34   Private implementation changes need not invalidate unrelated downstream modules.
ABOOT-35   Compiler semantic objects have stable identities.
ABOOT-36   Semantic type identity is independent of physical compiler memory address.
ABOOT-37   Interned semantic types are canonical.
ABOOT-38   Semantic database objects are immutable after canonicalization where practical.
ABOOT-39   Query cycles are detected and diagnosed.
ABOOT-40   Query evaluation may be cancelled when a newer revision supersedes it.
ABOOT-41   Compiler revisions are explicit.
ABOOT-42   Cached results are validated against semantic fingerprints.
ABOOT-43   Host and target environments are distinct.
ABOOT-44   Cross compilation is a first-class compiler operation.
ABOOT-45   Comptime host execution is distinct from target execution.
ABOOT-46   Compiler metadata is distinct from runtime program metadata.
ABOOT-47   Verified MIR is the semantic trust boundary for optimization and backend.
ABOOT-48   Backend stages cannot redefine language semantics.
ABOOT-49   Optimization level cannot change language semantics.
ABOOT-50   Debug/release compilation must preserve semantic behavior.
ABOOT-51   Compiler diagnostics have stable machine-readable identities.
ABOOT-52   Diagnostic source spans are reproducible.
ABOOT-53   Compiler diagnostics may expose structured semantic facts.
ABOOT-54   AI tooling may query compiler facts but cannot determine compiler semantics.
ABOOT-55   AI assistance cannot make compilation nondeterministic.
ABOOT-56   Compiler semantic verification does not depend on AI output.
ABOOT-57   AST/HIR/MIR/OptIR/LIR/Machine IR are independently inspectable compiler representations.
ABOOT-58   Compiler representation dumps do not alter program semantics.
ABOOT-59   Compiler tests cover semantic, optimization, ABI, backend and linker layers.
ABOOT-60   Verification tests remain valid across optimization levels.
ABOOT-61   Backend differential testing may use external compilers during bootstrap.
ABOOT-62   External backend comparison validates behavior rather than requiring identical machine code.
ABOOT-63   Bootstrap stages may be compared for semantic and reproducibility stability.
ABOOT-64   Compiler cache invalidation is dependency-driven.
ABOOT-65   Machine-code cache identity includes target and backend configuration.
ABOOT-66   Comptime dependency identity participates in incremental compilation.
ABOOT-67   Generic specialization identity participates in incremental compilation.
ABOOT-68   ABI changes invalidate affected downstream binary artifacts.
ABOOT-69   Representation-contract changes invalidate affected layout/codegen artifacts.
ABOOT-70   Source-to-machine debug mappings remain queryable across optimization.
ABOOT-71   Compiler memory management is an implementation concern distinct from Axiom runtime memory semantics.
ABOOT-72   Compiler arenas/intern pools do not imply Axiom runtime allocation.
ABOOT-73   Compiler native binary size is independent of application binary-size semantics.
ABOOT-74   The final compiler may be fully self-hosted.
ABOOT-75   The final compiler does not require a third-party compiler backend.
ABOOT-76   The final compiler does not require a monolithic runtime.
ABOOT-77   Native object generation remains target-specific.
ABOOT-78   Native linking remains target-specific.
ABOOT-79   Package/build orchestration remains distinct from language semantics.
ABOOT-80   Compiler implementation can evolve without changing the language when frozen semantics remain unchanged.
ABOOT-81   Semantic version changes identify incompatible compiler-language meaning changes.
ABOOT-82   Internal compiler IR changes do not require source-language changes.
ABOOT-83   Bootstrap implementation details are not exposed as language semantics.
ABOOT-84   Rebuilding the compiler with itself must not silently change language meaning.
ABOOT-85   Compiler source is an ordinary Axiom program once self-hosting is established.
ABOOT-86   The compiler must be able to compile programs using the language features required by its own implementation.
ABOOT-87   Bootstrap dependencies must have a documented removal path.
ABOOT-88   External bootstrap tools may remain optional interoperability tools.
ABOOT-89   Self-hosting does not require abandoning foreign ABI interoperability.
ABOOT-90   Axiom can provide independent native compiler, object writer and linker implementations.
ABOOT-91   Stage convergence is a bootstrap correctness signal, not a substitute for testing.
ABOOT-92   Reproducible builds must exclude uncontrolled timestamps/randomness unless explicitly part of build identity.
ABOOT-93   Compiler build metadata is explicit.
ABOOT-94   Compiler implementation may parallelize independent queries.
ABOOT-95   Compiler behavior remains deterministic under permitted parallel execution.
ABOOT-96   Compiler failures distinguish user diagnostics from internal compiler errors.
ABOOT-97   Internal compiler errors expose enough structured context for debugging without pretending the source is invalid.
ABOOT-98   Compiler APIs may expose semantic facts to IDE and AI tooling.
ABOOT-99   Exposed compiler facts cannot be used to bypass semantic verification.
ABOOT-100  Self-hosted Axiom remains governed by the same language semantics as ordinary Axiom programs.
```

---

## Một kết luận quan trọng ở mốc 060

Đến đây, Axiom không còn chỉ là một **language design** nữa. Ta đã có kiến trúc cho:

```text
Language
   ↓
Semantic Core
   ↓
Memory / Ownership
   ↓
Concurrency / Async / GPU
   ↓
Type / Trait / Generic
   ↓
MIR
   ↓
Verification
   ↓
Optimization
   ↓
ABI
   ↓
Machine Backend
   ↓
Object Writer
   ↓
Linker
   ↓
Executable
   ↓
Self-hosting compiler
```

Và đặc biệt, triết lý ban đầu của bạn đã được giữ xuyên suốt:

> **Lập trình viên không phải gánh complexity của compiler.**

Compiler có thể thực hiện ownership analysis, lifetime analysis, alias analysis, escape analysis, register allocation, ABI lowering, v.v. cực kỳ phức tạp — nhưng programmer chỉ phải nhìn thấy những abstraction có ý nghĩa.

---

### Bước tiếp theo: **BOOTSTRAP-061 — Standard Library & Core Library Architecture**

Đây là phần rất đáng làm kỹ trước khi bắt đầu code compiler, bởi vì Axiom đã cố tình **không nhét quá nhiều thứ vào language core**.

061 sẽ thiết kế ranh giới:

```text
Language Core
    ↓
Core Library
    ↓
Std Library
    ↓
System Library
    ↓
Platform Library
```

và quyết định cụ thể các primitive/library type như:

`String`, `str`, `Vec`, `Array`, `Slice/View`, `Box`, `Arc`, `Rc`, `Option`, `Result`, `HashMap`, iterator, allocator, filesystem, socket, thread, channel, async runtime, GPU, SIMD, math, Unicode...

để tránh tình trạng **“core language nhỏ nhưng standard library lại vô tình biến thành một runtime khổng lồ.”**