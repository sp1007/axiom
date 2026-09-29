# BOOTSTRAP-101 — Axiom Diagnostics, Error Model & Compiler UX

**Trạng thái: FROZEN**

Đây là phần rất quan trọng đối với mục tiêu **AI-friendly language** của Axiom.

Nguyên tắc:

> **Diagnostic không phải text mà compiler in ra. Diagnostic là một semantic object có cấu trúc; text/JSON/LSP chỉ là các cách trình bày nó.**

Vì vậy AI, IDE và con người đều đọc **cùng một nguồn dữ liệu**.

---

# 1. Diagnostic architecture

Compiler không tạo trực tiếp:

```text
error: something went wrong
```

mà tạo:

```text
Diagnostic {
    severity
    code
    primary_span
    secondary_spans
    message
    notes
    help
    causes
    related_declarations
    semantic_context
    machine_data
    fixits
}
```

Sau đó renderer biến nó thành:

```text
Human CLI
JSON
LSP
IDE
AI
```

---

# 2. Severity

Core có 4 mức:

```text
Error
Warning
Info
Hint
```

### Error

Không thể tạo artifact hợp lệ.

### Warning

Artifact vẫn hợp lệ nhưng có vấn đề đáng chú ý.

### Info

Thông tin bổ sung.

### Hint

Gợi ý tooling/IDE.

Không có `fatal` như một severity semantic.

ICE là một **compiler failure category**, không phải source diagnostic severity mới.

---

# 3. Stable diagnostic code

Mỗi compiler diagnostic có code ổn định.

Ví dụ:

```text
ETYPE_UNRESOLVED
ETYPE_MISMATCH
EOWN_MOVE
EOWN_USE_AFTER_MOVE
ECAP_CONFLICT
ECAP_DANGLING
ETRAIT_NOT_IMPLEMENTED
ETRAIT_AMBIGUOUS
EASYNC_AWAIT_VIEW
EGPU_ILLEGAL_OPERATION
EFFE_TYPE
ECOMPTIME_CAPABILITY
EABI_INVALID
```

Code không được thay đổi tùy wording.

Điều này cực kỳ quan trọng cho AI.

---

# 4. Message không phải API

Ví dụ hôm nay:

```text
cannot use moved value
```

ngày mai có thể đổi thành:

```text
value was moved before this access
```

nhưng:

```text
EOWN_USE_AFTER_MOVE
```

vẫn giữ nguyên.

AI/IDE không được parse English message để xác định loại lỗi.

---

# 5. Primary span

Mỗi error phải có một **primary span**.

Ví dụ:

```axiom
let b = a;
print(a);
```

Diagnostic:

```text
EOWN_USE_AFTER_MOVE

primary:
    `a` in print(a)

cause:
    `a` was moved into `b`
```

---

# 6. Multi-span diagnostic

Một lỗi thường liên quan nhiều vị trí.

Ví dụ:

```axiom
let b = a;
print(a);
```

Có:

```text
Primary:
    print(a)

Secondary:
    let b = a

Note:
    ownership was transferred here
```

CLI:

```text
error[EOWN_USE_AFTER_MOVE]: use of moved value `a`
  --> main.ax:2:7
   |
 1 | let b = a;
   |         - value moved here
 2 | print(a);
   |       ^ value used after move
```

---

# 7. Diagnostic cause graph

Đây là một điểm tôi đề xuất thêm cho Axiom.

Diagnostic có thể có:

```text
cause graph
```

Ví dụ:

```text
EASYNC_AWAIT_VIEW
        │
        ├── view originates from local buffer
        │
        └── await may suspend execution
                │
                └── buffer lifetime cannot cross suspension
```

AI có thể truy vấn causal chain thay vì đoán.

---

# 8. Machine-readable semantic payload

Ví dụ JSON concept:

```json
{
  "code": "EOWN_USE_AFTER_MOVE",
  "severity": "error",
  "primary": {
    "file": "main.ax",
    "start": 42,
    "end": 43
  },
  "causes": [
    {
      "kind": "move",
      "span": {
        "file": "main.ax",
        "start": 20,
        "end": 21
      }
    }
  ],
  "entity": "LocalId:17",
  "state": "Moved"
}
```

Đây mới là interface mà AI agent nên sử dụng.

---

# 9. Fix-it

Compiler có thể cung cấp machine-readable fix:

```text
FixIt {
    span
    replacement
    applicability
}
```

Ví dụ:

```text
suggestion:
    clone `a` before passing it
```

nhưng compiler phải phân biệt:

```text
MachineApplicable
MaybeApplicable
ManualReview
```

Không được biến suggestion thành automatic source mutation mặc định.

---

# 10. Compiler không tự sửa code

Diagnostics có thể đưa ra:

```text
help:
    consider `clone()`
```

nhưng compiler:

```text
check
```

không tự sửa source.

IDE/AI mới quyết định có áp dụng fix-it hay không.

Điều này giữ compiler deterministic.

---

# 11. Fix-it phải semantic

Không nên chỉ:

```text
replace "x" with "y"
```

mà metadata nên có:

```text
intent:
    resolve_move_conflict

candidate:
    clone

reason:
    required ownership remains after call

cost:
    explicit_allocation_or_copy_possible
```

AI có thể hiểu trade-off.

---

# 12. Type mismatch

Ví dụ:

```axiom
let x: i32 = 3.14;
```

Diagnostic:

```text
ETYPE_MISMATCH
expected: i32
found: f64
conversion: implicit numeric narrowing not permitted
```

Compiler có thể gợi ý:

```text
as i32
```

nhưng chỉ là suggestion.

---

# 13. Ownership diagnostics

Ví dụ:

```axiom
let a = File.open(...);
let b = a;
a.read(...);
```

Compiler nên nói chính xác:

```text
EOWN_USE_AFTER_MOVE
```

và semantic data:

```text
moved_from: LocalId(a)
moved_to: LocalId(b)
move_kind: ownership_transfer
```

Không nói chung chung:

```text
borrow error
```

vì Axiom không có programmer-facing borrow model kiểu Rust.

---

# 14. Capability diagnostics

Ví dụ:

```axiom
let a = mut_view(buffer);
let b = mut_view(buffer);
```

Diagnostic:

```text
ECAP_CONFLICT
```

với:

```text
capability_a:
    access = WRITE
    region = buffer

capability_b:
    access = WRITE
    region = buffer

overlap:
    SAME

rule:
    WRITE + WRITE is forbidden
```

AI có thể tự hiểu chính xác conflict.

---

# 15. UNKNOWN alias diagnostics

Đặc biệt:

```text
ECAP_UNKNOWN_OVERLAP
```

Compiler phải nói:

```text
regions cannot be proven disjoint
```

thay vì:

```text
borrow checker failed
```

Điều này phản ánh đúng Axiom capability model.

---

# 16. Trait diagnostics

Trait solver có thể rất phức tạp.

Không được đưa ra:

```text
trait bound not satisfied
```

một cách mơ hồ.

Payload:

```text
ETRAIT_NOT_IMPLEMENTED

goal:
    T: Iterator

type:
    MyCollection

candidates:
    impl Iterator for ...
    
unsatisfied:
    Item = ...
```

Nếu ambiguous:

```text
ETRAIT_AMBIGUOUS
```

và liệt kê candidate set.

---

# 17. Generic diagnostics

Ví dụ:

```axiom
fn foo<T: Add>(x: T) -> T {
    x + x
}
```

Diagnostic có thể chỉ rõ:

```text
operator `+`
requires:
    Add<T, Output = T>

available constraint:
    Add<T>

unsolved associated type:
    Output
```

AI không cần đọc cả compiler internals.

---

# 18. Async diagnostics

Ví dụ:

```axiom
async fn foo(mut_view<u8> buffer) {
    await something();
    buffer[0] = 1;
}
```

Diagnostic:

```text
EASYNC_VIEW_ACROSS_AWAIT
```

Payload:

```text
capability:
    WRITE

suspension_point:
    SuspensionPointId:4

reason:
    capability is live across suspension

allowed alternatives:
    end capability before await
    move owned storage into future
    use explicit stable-storage contract
```

---

# 19. GPU diagnostics

Ví dụ kernel:

```axiom
@kernel
fn foo() {
    File.open(...);
}
```

Diagnostic:

```text
EGPU_ILLEGAL_OPERATION
```

Payload:

```text
execution_domain: GPU
operation: filesystem.open
required_domain: HOST
```

Không cần AI đoán GPU restrictions.

---

# 20. FFI diagnostics

Ví dụ:

```axiom
extern "C" fn foo(x: String);
```

Diagnostic:

```text
EABI_FFI_UNSAFE_TYPE
```

Payload:

```text
abi: C
type: String
reason:
    String does not have a stable C representation
suggestion:
    use C-compatible representation
```

---

# 21. Comptime diagnostics

Ví dụ comptime:

```axiom
comptime {
    network.fetch(...);
}
```

nếu capability không được cấp:

```text
ECOMPTIME_CAPABILITY
```

Payload:

```text
phase: comptime
operation: Network
required_capability: Network
available_capabilities:
    ReadSource
    ReadMetadata
```

---

# 22. Build diagnostics

Build system cũng dùng cùng diagnostic model.

Ví dụ dependency conflict:

```text
EBUILD_DEP_CONFLICT
```

Không tạo một hệ thống error hoàn toàn khác.

---

# 23. Compiler error vs ICE

Phải phân biệt cực rõ.

### User/compiler semantic error

```text
ETYPE_MISMATCH
```

### Internal compiler failure

```text
ICE
```

ICE record:

```text
CompilerFailure {
    stage
    query
    compiler_version
    target
    reproducibility_token
}
```

Không expose stack trace nội bộ mặc định cho user.

Có thể bật:

```bash
axiom --debug-compiler
```

---

# 24. ICE không được biến thành "undefined behavior"

Nếu compiler gặp bug:

```text
ICE
```

không được:

```text
generate random binary
```

hoặc im lặng tiếp tục.

---

# 25. Error recovery

Parser cần recovery để IDE vẫn hoạt động.

Ví dụ:

```axiom
fn foo( {
```

compiler có thể tạo synthetic token trong parser state để tiếp tục phân tích.

Nhưng:

> **synthetic recovery node không được coi là source semantic fact.**

Do đó downstream diagnostics không được sinh ra hàng loạt lỗi giả nếu có thể tránh.

---

# 26. Diagnostic suppression

Có thể:

```text
@allow(WARNING_CODE)
```

nhưng chỉ áp dụng warning.

Không được suppress semantic errors.

---

# 27. Warning policy

Compiler profiles:

```text
default
strict
pedantic
```

Ví dụ:

```text
warning[WUNUSED]
```

có thể thành error trong strict profile.

Nhưng:

```text
ETYPE_MISMATCH
```

luôn là error.

---

# 28. Warning stability

Warning code cũng stable:

```text
WUNUSED_VARIABLE
WUNUSED_IMPORT
WDEPRECATED
WUNREACHABLE
WIMPLICIT_COST
```

Tooling không parse message.

---

# 29. Diagnostic identity

Mỗi diagnostic nên có:

```text
DiagnosticId
```

ổn định trong một compiler revision/build session.

Mục đích:

- IDE update
- incremental diagnostics
- suppressions
- AI agent tracking

Không nên dùng DiagnosticId như persistent source identifier giữa các compiler runs.

---

# 30. Incremental diagnostics

CompilerDB có:

```text
DiagnosticDB
```

query:

```text
diagnostics(ModuleId)
```

Nếu module không đổi semantic fingerprint:

```text
diagnostics
```

có thể reuse.

Nếu upstream public API đổi:

```text
dependent diagnostics
```

được invalidated.

---

# 31. Diagnostic provenance

Generated code:

```text
comptime generate()
```

nếu gây lỗi phải chỉ ra cả:

```text
generated location
+
source generation origin
```

Ví dụ:

```text
generated:
    <comptime-generated>:12

origin:
    schema.ax:44

generated_by:
    derive(Entity)
```

AI có thể quay về declaration nguồn.

---

# 32. Macro-free architecture có lợi ở đây

Vì Axiom không có unrestricted procedural macro trong Core v1, diagnostic provenance dễ giữ hơn.

Typed generation:

```text
source
 ↓
comptime / derive
 ↓
HIR
```

vẫn giữ origin metadata.

---

# 33. IDE/LSP

Axiom compiler nên cung cấp native query interface:

```text
axiom language-server
```

LSP layer chỉ là adapter.

Compiler semantic engine không phụ thuộc LSP.

IDE có thể query:

```text
type_at(position)
definition_at(position)
references(declaration)
diagnostics(file)
hover(position)
completion(scope)
```

---

# 34. AI interface

Đây là phần tôi muốn Axiom làm tốt hơn nhiều compiler hiện tại.

Có thể có:

```bash
axiom explain EOWN_USE_AFTER_MOVE
axiom diagnostics --format=json
axiom diagnostics --format=ai
```

`ai` có thể trả:

```text
problem
entities
facts
causes
constraints
candidate_fixes
verification_status
```

AI không cần parse human prose.

---

# 35. AI sửa lỗi phải build lại

Workflow:

```text
AI
 ↓
axiom check --diagnostics=json
 ↓
parse structured diagnostics
 ↓
modify source
 ↓
axiom check
 ↓
new diagnostics
 ↓
repeat
```

Compiler không cần "AI mode" để hiểu code.

Nó chỉ cần cung cấp semantic data sạch.

---

# 36. Compiler Explain API

Ngoài diagnostics, Axiom nên có:

```bash
axiom explain type ...
axiom explain ownership ...
axiom explain capability ...
axiom explain trait ...
axiom explain async ...
axiom explain runtime ...
axiom explain optimization ...
axiom explain layout ...
```

Ví dụ:

```text
axiom explain ownership x
```

trả:

```text
Local x
state:
    Owned

created:
    main.ax:12

moved:
    no

capabilities:
    none

drop:
    yes

live range:
    block 3 → block 7
```

---

# 37. Không expose compiler internals tùy tiện

AI interface nên expose:

```text
semantic facts
```

chứ không phụ thuộc vào:

```text
Rust-like MIR dump
LLVM IR
machine register allocation internals
```

vì backend có thể thay đổi.

Có thể có debug modes riêng.

---

# 38. Diagnostic categories

Axiom registry:

```text
ELEX
EPARSE
ERESOLVE
ETYPE
ETRAIT
EOWN
ECAP
ECONCUR
EASYNC
EGPU
ECOMPTIME
EABI
EFFI
EATTR
EBUILD
ELINK
ERUNTIME
EINTERNAL
```

Code naming phải deterministic.

---

# 39. One error, one root cause

Compiler nên tránh:

```text
100 cascading errors
```

khi một declaration bị thiếu.

Ví dụ:

```axiom
let x = UnknownType;
```

có thể gây downstream unknown types.

Compiler nên mark:

```text
error recovery / poisoned type
```

để không spam.

---

# 40. Poison semantic nodes

Một semantic node có thể:

```text
TypeId::Error
DeclarationId::Error
TraitResult::Error
```

Downstream analysis tiếp tục nhưng không sinh duplicate root errors.

Đây rất hữu ích cho IDE.

---

# 41. Deterministic diagnostic ordering

Nếu compiler chạy parallel:

```text
module A
module B
module C
```

diagnostic order vẫn deterministic.

Sort theo:

```text
file identity
source position
severity
diagnostic code
stable diagnostic identity
```

hoặc một ordering contract tương đương.

Không để thread scheduling quyết định output.

---

# 42. Localization

Diagnostic semantic code/message key tách riêng:

```text
code = EOWN_USE_AFTER_MOVE
message_key = ownership.use_after_move
```

Human renderer có thể dịch.

Semantic machine data không phụ thuộc ngôn ngữ.

---

# 43. Source spans

`SourceSpan` nên là:

```text
SourceFileId
start_offset
end_offset
```

Unicode position chỉ là rendering layer.

Compiler semantic offsets nên dựa trên UTF-8 byte offset hoặc một representation chuẩn.

Không dùng visual column làm identity.

---

# 44. Rich source context

Diagnostic renderer có thể hiển thị:

```text
source snippet
caret
underline
labels
notes
help
```

nhưng đây là UI.

Semantic diagnostic vẫn giữ span IDs.

---

# 45. Diagnostic suppression không làm mất semantic facts

Nếu warning bị suppress:

```text
@allow(WUNUSED)
```

compiler vẫn có thể giữ internal fact.

IDE/AI có thể query.

---

# 46. Compiler contracts

Compiler API nên expose machine-readable schema:

```text
diagnostic.schema.json
```

có version:

```text
diagnostic_schema_version
```

Tương tự `.axmeta`.

AI tooling không nên phụ thuộc vào compiler minor wording.

---

# 47. Error codes không tái sử dụng

Một khi:

```text
EOWN_USE_AFTER_MOVE
```

đã public:

> Không tái sử dụng code đó cho semantic meaning khác.

Nếu obsolete:

```text
deprecated code
```

có thể giữ mapping.

---

# 48. Diagnostics và compiler evolution

Compiler version:

```text
0.1
0.2
...
```

có thể thêm diagnostic codes.

Nhưng không nên thay đổi meaning của existing code trong cùng compatibility contract.

---

# 49. Diagnostic test suite

Mỗi error cần test:

```text
source
expected_code
primary_span
secondary_spans
semantic_payload
```

Không test bằng toàn bộ output text.

Ví dụ:

```text
test EOWN_USE_AFTER_MOVE:
    assert diagnostic.code == EOWN_USE_AFTER_MOVE
    assert primary.span == ...
```

Text snapshot chỉ là supplementary.

---

# 50. AI-agent loop

Axiom compiler cuối cùng có thể hỗ trợ workflow:

```text
┌──────────────┐
│     AI       │
└──────┬───────┘
       │ source
       ▼
┌──────────────┐
│    Axiom     │
│    check     │
└──────┬───────┘
       │ structured diagnostics
       ▼
┌──────────────┐
│ AI reasoning │
└──────┬───────┘
       │ patch
       ▼
┌──────────────┐
│    Axiom     │
│    verify    │
└──────┬───────┘
       │
       ├── error → next patch
       │
       └── success
              ↓
            build
```

Điều này phù hợp trực tiếp với mục tiêu Axiom được xây dựng và sử dụng bởi AI agents.

---

# 51. Frozen invariants

**ADIAG-20** — Diagnostics Are Semantic Objects  
**ADIAG-21** — Diagnostic Rendering Is Separate From Diagnostic Identity  
**ADIAG-22** — Every Diagnostic Has A Stable Code  
**ADIAG-23** — Diagnostic Codes Are Not Message Text  
**ADIAG-24** — Diagnostic Codes Must Not Be Reused For Different Semantics  
**ADIAG-25** — Errors Have A Primary Source Span  
**ADIAG-26** — Diagnostics May Have Multiple Secondary Spans  
**ADIAG-27** — Diagnostics May Contain Causal Relationships  
**ADIAG-28** — Diagnostic Causes Are Machine-Readable  
**ADIAG-29** — Diagnostics May Contain Structured Semantic Facts  
**ADIAG-30** — Diagnostics May Contain Machine-Applicable Fixes  
**ADIAG-31** — Fix-It Suggestions Do Not Mutate Source Automatically  
**ADIAG-32** — Fix-It Applicability Is Explicit  
**ADIAG-33** — Compiler Messages Are Not A Stable Machine Interface  
**ADIAG-34** — Diagnostic Schema Is Versioned  
**ADIAG-35** — Diagnostic Semantic Data Is Language-Independent  
**ADIAG-36** — Diagnostic Rendering May Be Localized  
**ADIAG-37** — Compiler Errors Are Distinct From Internal Compiler Failures  
**ADIAG-38** — ICE Must Not Produce Unverified Artifacts  
**ADIAG-39** — Parser Recovery Must Not Invent Source Semantics  
**ADIAG-40** — Error Recovery Should Minimize Cascading Diagnostics  
**ADIAG-41** — Poisoned Semantic Nodes May Suppress Cascading Errors  
**ADIAG-42** — Warning Severity Is Distinct From Error Semantics  
**ADIAG-43** — Warning Policy May Vary By Build Profile  
**ADIAG-44** — Semantic Errors Cannot Be Suppressed Into Validity  
**ADIAG-45** — Diagnostic Identity Is Stable Within A Compiler Session  
**ADIAG-46** — Diagnostic Identity Is Not A Persistent Source Identity  
**ADIAG-47** — Generated Code Diagnostics Preserve Provenance  
**ADIAG-48** — Comptime Diagnostics Preserve Generation Origin  
**ADIAG-49** — Incremental Compilation May Reuse Diagnostics  
**ADIAG-50** — Diagnostic Invalidation Follows Semantic Dependency  
**ADIAG-51** — Parallel Compilation Must Produce Deterministic Diagnostic Ordering  
**ADIAG-52** — Diagnostic Ordering Must Not Depend On Thread Scheduling  
**ADIAG-53** — Source Span Identity Is Independent Of Display Column  
**ADIAG-54** — UTF-8 Source Offsets Are Semantic Source Coordinates  
**ADIAG-55** — IDE Integration Uses Compiler Semantic Queries  
**ADIAG-56** — LSP Is An Adapter, Not The Compiler Semantic Core  
**ADIAG-57** — AI Tooling Uses Structured Diagnostics  
**ADIAG-58** — AI Tooling Must Not Depend On Human Diagnostic Wording  
**ADIAG-59** — Ownership Diagnostics Expose Ownership Facts  
**ADIAG-60** — Capability Diagnostics Expose Capability Facts  
**ADIAG-61** — Trait Diagnostics Expose Constraint Facts  
**ADIAG-62** — Async Diagnostics Expose Suspension Facts  
**ADIAG-63** — GPU Diagnostics Expose Execution-Domain Facts  
**ADIAG-64** — FFI Diagnostics Expose ABI Facts  
**ADIAG-65** — Comptime Diagnostics Expose Capability Facts  
**ADIAG-66** — Build Diagnostics Use The Same Structured Diagnostic Model  
**ADIAG-67** — Link Diagnostics Use The Same Structured Diagnostic Model  
**ADIAG-68** — Runtime Diagnostics May Reuse Diagnostic Codes Where Appropriate  
**ADIAG-69** — Diagnostic Suppression Does Not Remove Internal Semantic Facts  
**ADIAG-70** — Compiler Explain Interfaces Are Separate From Error Rendering  
**ADIAG-71** — Explain Interfaces May Expose Semantic State  
**ADIAG-72** — Explain Interfaces Must Remain Backend-Independent By Default  
**ADIAG-73** — Diagnostic Tests Must Assert Semantic Identity  
**ADIAG-74** — Text Snapshots Are Supplementary Diagnostic Tests  
**ADIAG-75** — Diagnostic Schema Evolution Must Preserve Compatibility Contracts  
**ADIAG-76** — Diagnostic Data Must Be Deterministic  
**ADIAG-77** — Diagnostics Must Preserve Source Provenance  
**ADIAG-78** — Diagnostics Must Not Depend On Filesystem Ordering  
**ADIAG-79** — Diagnostics Must Not Depend On Import Ordering  
**ADIAG-80** — Diagnostics Must Be Queryable By Compiler Tooling  
**ADIAG-81** — Diagnostics Must Be Queryable By AI Tooling  
**ADIAG-82** — Compiler Must Distinguish Root Causes From Derived Failures  
**ADIAG-83** — Compiler Should Prefer Root-Cause Diagnostics  
**ADIAG-84** — Diagnostic Suggestions Must Respect Language Semantics  
**ADIAG-85** — Compiler Must Not Suggest Semantically Invalid Fixes  
**ADIAG-86** — Diagnostic Semantic Data Must Not Require A Specific Backend  
**ADIAG-87** — Diagnostic Output Must Support Human And Machine Consumers  
**ADIAG-88** — Diagnostic Architecture Must Remain Usable In Freestanding Toolchains  
**ADIAG-89** — Diagnostic Infrastructure Must Not Require A Runtime Library  
**ADIAG-90** — Diagnostic Generation Is A Compiler Concern, Not A Program Runtime Concern  

**BOOTSTRAP-101: FROZEN.**

---

# BOOTSTRAP-102 — Axiom Testing Architecture & Language Conformance Suite

Bước tiếp theo sẽ khóa một thứ còn quan trọng hơn compiler implementation:

> **Làm thế nào chứng minh Axiom compiler thực sự tuân thủ toàn bộ semantic specification?**

Ta sẽ thiết kế:

```text
Lexer tests
Parser tests
Resolver tests
Type-system tests
Trait-solver tests
Ownership tests
Capability tests
Drop tests
Concurrency tests
Async tests
GPU tests
Comptime tests
FFI/ABI tests
Layout tests
MIR tests
Optimization equivalence tests
Codegen tests
Object/linker tests
Runtime tests
Cross-target tests
Compile-fail tests
Diagnostic tests
Fuzzing
Property testing
Differential testing
Golden tests
Bootstrap/self-host tests
Reproducible-build tests
AI-agent compiler tests
```

và đặc biệt sẽ định nghĩa **Axiom Conformance Model** để sau này compiler do AI xây dựng vẫn có thể tự kiểm chứng từng semantic contract thay vì chỉ dựa vào "build thành công".