# BOOTSTRAP-316 — AXIOM SPECIFICATION ENGINE & MACHINE-READABLE LANGUAGE DEFINITION SYSTEM

## 1. Mục tiêu

BOOTSTRAP-315 đã xác định **specification là nguồn sự thật chuẩn tắc**.

Bước tiếp theo là xây dựng hạ tầng để specification đó không chỉ là các file Markdown mà trở thành **một hệ thống có cấu trúc, có thể máy đọc, kiểm tra, truy vấn, sinh test và liên kết trực tiếp với compiler**.

Mục tiêu:

> Một semantic rule chỉ được định nghĩa một lần, sau đó có thể được sử dụng đồng thời bởi compiler, reference interpreter, conformance tests, documentation, IDE và AI agents.

---

# 2. Specification không còn là tài liệu thuần túy

Axiom cần phân biệt:

```text
Human Documentation
        │
        ▼
Machine Specification
        │
        ├── Compiler
        ├── Reference Semantics
        ├── Tests
        ├── IDE
        └── AI
```

Markdown/HTML/PDF chỉ là **projection** của machine-readable specification.

Không được lấy documentation làm semantic source of truth.

---

# 3. AXSpec

Định nghĩa một format nội bộ:

```text
AXSpec
```

Mục đích:

- biểu diễn semantic entities;
- semantic rules;
- invariants;
- constraints;
- examples;
- counterexamples;
- feature dependencies;
- target constraints;
- versioning;
- conformance requirements.

Một specification package:

```text
spec/
├── core.axspec
├── syntax.axspec
├── types.axspec
├── ownership.axspec
├── capability.axspec
├── memory.axspec
├── concurrency.axspec
├── async.axspec
├── comptime.axspec
├── gpu.axspec
├── abi.axspec
├── ffi.axspec
└── security.axspec
```

---

# 4. Semantic Entity

Mọi khái niệm quan trọng có ID ổn định.

Ví dụ:

```text
type.bool
type.i32
type.view
ownership.move
ownership.copy
capability.read
capability.write
memory.happens_before
async.await
gpu.kernel
ffi.c_abi
```

ID không phụ thuộc vào:

- file;
- dòng;
- compiler implementation;
- tên class trong compiler.

Điều này giúp compiler và AI tham chiếu semantic concept ổn định.

---

# 5. Rule Identity

Mỗi rule có ID:

```text
OWN-MOVE-001
CAP-VIEW-004
MEM-ACQUIRE-002
ASYNC-AWAIT-007
GPU-KERNEL-003
FFI-ABI-012
```

Rule ID phải ổn định qua patch releases.

Nếu semantic rule thay đổi:

```text
rule revision
```

được tăng.

---

# 6. Rule Structure

Mỗi rule có cấu trúc:

```text
Rule {
    id
    title
    domain
    applies_when
    preconditions
    facts_required
    transformation
    postconditions
    invalidates
    observable_effects
    diagnostics
    examples
    counterexamples
    references
}
```

Ví dụ:

```text
rule OWN-MOVE-001 {
    domain: ownership

    applies_when:
        source.state == Owned

    transition:
        source.state := Moved
        destination.state := Owned

    invalid_after:
        read(source)
        move(source)
        drop(source)
}
```

---

# 7. Rule Dependencies

Rule có dependency graph:

```text
OWN-MOVE-001
    ↓
OWN-STATE-003
    ↓
DROP-VALID-002
```

Compiler có thể hỏi:

```text
why does this diagnostic exist?
```

và nhận:

```text
OWN-MOVE-001
 → OWN-STATE-003
 → DROP-VALID-002
```

AI cũng có thể sử dụng graph này.

---

# 8. Semantic Fact System

Specification định nghĩa vocabulary chuẩn:

```text
Fact {
    subject
    predicate
    object
    provenance
    confidence
}
```

Ví dụ:

```text
Place(x)
State(x, Owned)
Region(x, R1)
Access(x, Read)
Send(T)
Share(T)
```

Compiler không cần dùng đúng representation này nội bộ, nhưng phải có mapping từ internal facts → normative facts.

---

# 9. Preconditions và Proof Obligations

Mỗi transformation/rule có thể yêu cầu:

```text
ProofObligation {
    id
    condition
    required_evidence
    verifier
}
```

Ví dụ bounds-check elimination:

```text
BOUNDS-ELIM-001

requires:
    index >= 0
    index < length

evidence:
    RangeAnalysis
    LoopInvariant
    GuardDominance
```

Điều này biến optimizer thành hệ thống:

```text
Transformation
+
Proof
```

thay vì:

```text
Transformation
+
heuristic
```

---

# 10. Specification → Test Generation

Một rule có thể chứa test schema:

```text
TestTemplate {
    valid_cases
    invalid_cases
    boundary_cases
    mutation_cases
}
```

Ví dụ ownership:

```text
OWN-MOVE-001
```

tự sinh các nhóm:

```text
move once
move twice
read after move
drop after move
reinitialize after move
partial move
move through branch
move through loop
move across await
```

---

# 11. Counterexample First-Class

Specification không chỉ mô tả chương trình đúng.

Mỗi rule có thể chứa:

```text
Counterexample
```

Ví dụ:

```text
CAP-MUT-002

invalid:
    let a = mut_view(x)
    let b = mut_view(x)
```

Counterexample trở thành regression test.

---

# 12. Semantic Example

Ví dụ chuẩn:

```text
Example {
    source
    expected_facts
    expected_result
    expected_state
}
```

Không chỉ lưu expected output.

Có thể kiểm tra:

```text
source
→ ownership state
→ capability state
→ effects
→ result
```

Điều này giúp test semantic sâu hơn snapshot text.

---

# 13. Specification Compiler

Axiom cần một tool:

```text
axspec
```

Pipeline:

```text
.axspec
   ↓
Parser
   ↓
Spec AST
   ↓
Resolver
   ↓
Rule Validator
   ↓
Dependency Graph
   ↓
Spec IR
   ↓
Generators
```

Outputs:

```text
compiler bindings
reference interpreter rules
test cases
documentation
AI semantic database
conformance metadata
```

---

# 14. Specification Validation

`axspec check` phải phát hiện:

- duplicate entity ID;
- duplicate rule ID;
- unresolved references;
- cyclic semantic dependency nếu không được phép;
- contradictory rules;
- missing preconditions;
- impossible postconditions;
- unreachable rule;
- conflicting version ranges;
- missing conformance tests.

Ví dụ:

```text
SPEC-CONFLICT-001
```

nếu:

```text
Rule A:
READ + WRITE = conflict

Rule B:
READ + WRITE = allowed
```

mà không có điều kiện phân biệt.

---

# 15. Rule Conflict Detection

Không chỉ detect textual conflict.

Phải phát hiện semantic overlap:

```text
Rule A:
if Region(A) == Region(B)

Rule B:
if Region(A) overlaps Region(B)
```

Compiler/spec engine phải biết rằng:

```text
SAME ⊂ OVERLAPS
```

và phân tích khả năng conflict.

---

# 16. Semantic Dependency Graph

Tạo:

```text
SpecGraph
```

Ví dụ:

```text
Type
 │
 ├── Ownership
 │     └── Drop
 │
 ├── Capability
 │     └── Alias
 │
 └── Layout
       └── ABI
```

Các tool:

```text
axspec graph
axspec explain OWN-MOVE-001
axspec dependencies memory.happens_before
```

---

# 17. Compiler Binding

Compiler không hard-code semantic rule ID rải rác.

Thay vào đó:

```text
Normative Rule
      ↓
Semantic Rule Registry
      ↓
Compiler Implementation
```

Compiler verifier có thể khai báo:

```text
implements:
    OWN-MOVE-001
    OWN-DROP-003
```

Nếu implementation không còn satisfy rule:

```text
CONFORMANCE-FAIL
```

---

# 18. Rule Coverage

Compiler cần semantic coverage:

```text
Rule Coverage
```

Ví dụ:

```text
OWN-MOVE-001        IMPLEMENTED
OWN-MOVE-002        TESTED
OWN-MOVE-003        IMPLEMENTED + PROVEN
```

Có thể chạy:

```text
axspec coverage
```

và thấy rule nào:

- chưa implement;
- chưa test;
- chỉ có negative test;
- chỉ có positive test;
- chưa có optimization equivalence test.

---

# 19. Specification Versioning

AXSpec version:

```text
major.minor.patch
```

Nhưng semantic rule có revision riêng.

Ví dụ:

```text
Axiom Spec 1.0.0

OWN-MOVE-001
revision 3
```

Patch:

- sửa typo;
- metadata;
- documentation.

Minor:

- thêm compatible semantic rule.

Major:

- breaking semantic change.

---

# 20. Feature Gates

Mỗi entity/rule có thể yêu cầu:

```text
Feature {
    id
    status
    introduced
    stabilized
    deprecated
    removed
}
```

Ví dụ:

```text
feature.gpu
status: experimental
```

Compiler không được coi experimental feature là Core semantics.

---

# 21. Target Constraints

Rule có thể chỉ áp dụng cho target:

```text
when:
    target.arch == x86_64
```

hoặc:

```text
requires:
    atomic_width >= 64
```

Specification engine phải phân biệt:

```text
Core rule
Target rule
Implementation extension
```

---

# 22. ABI Specification Database

ABI trở thành một phần của machine specification:

```text
abi/
├── axiom/
├── c/
├── systemv_x86_64/
├── windows_x64/
├── aapcs64/
├── riscv64/
├── wasm/
└── apple/
```

Mỗi ABI có:

```text
calling convention
register classes
stack rules
alignment
aggregate passing
return rules
TLS
unwind
name mangling
```

Backend có thể query thay vì hard-code nhiều nơi.

---

# 23. Target Specification Database

Tương tự:

```text
targets/
├── x86_64-windows
├── x86_64-linux
├── arm64-linux
├── arm64-apple
├── riscv64-linux
├── wasm32
└── wasm64
```

TargetSpec chứa:

```text
architecture
endianness
pointer_width
ABI
object_format
executable_format
features
atomic_capabilities
alignment
register_model
security_features
```

---

# 24. Documentation Generation

Từ AXSpec sinh:

```text
docs/
├── language/
├── reference/
├── semantics/
├── diagnostics/
├── ABI/
└── conformance/
```

Mỗi trang có:

```text
Semantic IDs
Rule IDs
Version
Examples
Counterexamples
Related rules
```

Documentation không được viết lại semantic rules bằng tay.

---

# 25. AI Semantic Interface

AXSpec trở thành nguồn cho AI compiler assistant.

API:

```text
get_semantic_entity(id)
get_rule(id)
get_rule_dependencies(id)
get_rule_examples(id)
get_rule_counterexamples(id)
explain_semantic_fact()
explain_diagnostic()
find_rules_for_operation()
find_rules_for_type()
```

AI có thể hỏi:

> Tại sao compiler từ chối `mut_view` thứ hai?

Compiler trả:

```text
CAP-MUT-002
↓
CAP-REGION-003
↓
WRITE-WRITE conflict
```

thay vì AI phải tự suy luận từ hàng nghìn dòng source compiler.

---

# 26. AI Planning Integration

Agent xây compiler có thể query:

```text
what implements OWN-MOVE-001?
```

và nhận:

```text
compiler/analysis/ownership/
compiler/mir/ownership/
tests/ownership/
```

Hoặc:

```text
what tests validate MEM-ACQUIRE-002?
```

→ trả test IDs.

Điều này rất phù hợp với workflow Axiom hiện tại sử dụng nhiều AI agent.

---

# 27. Semantic Change Impact Analysis

Khi sửa một rule:

```text
axspec impact OWN-MOVE-001
```

phải trả:

```text
Rules affected
Compiler modules affected
Tests affected
Docs affected
ABI effects
Optimization effects
AI knowledge affected
```

Ví dụ:

```text
OWN-MOVE-001
 ├── ownership verifier
 ├── drop elaboration
 ├── async lowering
 ├── optimizer
 ├── debugger
 ├── diagnostics
 └── 143 tests
```

---

# 28. Specification Review

Một semantic change không được commit đơn giản như source code bình thường.

Change proposal:

```text
SpecChange {
    motivation
    old_semantics
    new_semantics
    affected_rules
    compatibility
    implementation_impact
    test_impact
    ABI_impact
    security_impact
}
```

Agent có thể tự tạo impact report trước khi sửa.

---

# 29. Semantic Migration

Nếu Axiom 1.x → 2.0 thay đổi semantics:

```text
axspec migrate
```

có thể sinh:

- diagnostics;
- migration hints;
- source transformations nếu an toàn;
- compatibility report.

Nhưng migration tool không được tự ý thay đổi semantics mà compiler không hiểu.

---

# 30. Specification Integrity

AXSpec package phải có:

```text
SpecManifest {
    version
    root_hash
    entity_count
    rule_count
    dependency_hash
}
```

Compiler build ghi lại:

```text
CoreSpecHash
```

Nếu specification thay đổi nhưng compiler không rebuild semantic components:

```text
SPEC-MISMATCH
```

---

# 31. Bootstrap Strategy

AXSpec tool ban đầu có thể được viết bằng:

```text
Stage 0:
Rust/C++/existing tooling
```

Sau khi Axiom compiler đủ mạnh:

```text
Stage 1:
AXSpec parser in Axiom

Stage 2:
AXSpec validator in Axiom

Stage 3:
self-hosted axspec
```

Cuối cùng:

```text
Axiom
 └── axspec
      └── validates Axiom specification
```

---

# 32. Specification Self-Validation

Axiom specification phải có khả năng tự kiểm tra:

```text
axspec self-test
```

Các kiểm tra:

- rule consistency;
- dependency consistency;
- example validity;
- counterexample rejection;
- reference semantics agreement;
- compiler conformance;
- documentation generation;
- version integrity.

---

# 33. Formal Proof Integration

AXSpec không bắt buộc theorem prover.

Nhưng thiết kế extension:

```text
Proof {
    proposition
    assumptions
    proof_artifact
    verifier
}
```

Ví dụ:

```text
CAP-MUT-002
```

có thể về sau liên kết với proof artifact chứng minh:

```text
two overlapping mutable capabilities
cannot coexist in safe execution
```

---

# 34. Implementation Tree

```text
spec/
├── axspec/
│   ├── grammar/
│   ├── parser/
│   ├── resolver/
│   ├── validator/
│   ├── graph/
│   ├── version/
│   ├── generators/
│   ├── documentation/
│   ├── conformance/
│   └── ai/
│
├── normative/
├── abi/
├── targets/
└── conformance/

compiler/
├── spec/
│   ├── registry/
│   ├── bindings/
│   ├── coverage/
│   └── validation/
```

---

# 35. CLI

Các command chuẩn:

```text
axspec check
axspec build
axspec graph
axspec explain <rule>
axspec impact <rule>
axspec coverage
axspec test
axspec conformance
axspec generate-docs
axspec generate-tests
axspec validate-compiler
axspec diff <version-a> <version-b>
```

---

# 36. Definition of Done

BOOTSTRAP-316 hoàn thành khi:

1. Có machine-readable AXSpec.
2. Semantic entity có ID ổn định.
3. Semantic rule có ID/revision.
4. Rule dependency graph hoạt động.
5. Semantic fact vocabulary được chuẩn hóa.
6. Proof obligations có thể biểu diễn.
7. Positive/negative examples được machine-check.
8. Counterexamples là first-class test artifacts.
9. `axspec` parser/validator hoạt động.
10. Semantic conflict detection hoạt động.
11. Compiler có semantic-rule bindings.
12. Compiler có rule coverage.
13. ABI/Target specification database hoạt động.
14. Documentation có thể sinh từ specification.
15. Conformance tests có thể sinh từ rule metadata.
16. AI semantic query API hoạt động.
17. Semantic impact analysis hoạt động.
18. Specification versioning hoạt động.
19. Specification integrity/hash được kiểm tra.
20. Compiler/spec mismatch bị phát hiện.
21. Specification có thể self-test.
22. Có đường chuyển sang self-hosted `axspec`.
23. Formal proof artifacts có extension point.
24. Không có semantic rule quan trọng chỉ tồn tại dưới dạng comment hoặc knowledge ngầm trong compiler source.

---

## Nguyên tắc đóng băng

> **Axiom Specification phải là dữ liệu có thể thực thi, không chỉ là tài liệu để con người đọc.**

Về lâu dài, kiến trúc mong muốn là:

```text
                 ┌───────────────┐
                 │    AXSpec     │
                 │ Source Truth  │
                 └───────┬───────┘
                         │
       ┌─────────────────┼──────────────────┐
       ▼                 ▼                  ▼
 Reference          Compiler            Conformance
 Semantics          Implementation         Tests
       │                 │                  │
       └─────────────────┼──────────────────┘
                         ▼
                  Same Semantics
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             IDE         AI       Docs
```

Đây là nền tảng để Axiom về sau có thể được **nhiều AI agent cùng thiết kế và triển khai mà không làm ngôn ngữ bị “trôi semantics” theo từng agent**.