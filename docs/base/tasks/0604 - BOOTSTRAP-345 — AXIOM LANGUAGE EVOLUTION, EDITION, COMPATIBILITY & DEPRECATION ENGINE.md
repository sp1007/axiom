# BOOTSTRAP-345 — AXIOM LANGUAGE EVOLUTION, EDITION, COMPATIBILITY & DEPRECATION ENGINE

Sau 344, Axiom đã có quy trình để **build → verify → qualify → release** compiler. Nhưng một ngôn ngữ sống lâu sẽ gặp vấn đề khó hơn:

> **Làm thế nào để Axiom tiếp tục phát triển trong 10–20 năm mà không phá vỡ code cũ, ABI cũ, package cũ và compiler cũ?**

Đây là nhiệm vụ của 345.

Mục tiêu không phải làm Axiom “nhiều version” một cách phức tạp, mà tạo ra **một cơ chế tiến hóa có kiểm soát**, trong đó compiler luôn biết:

- code này thuộc language edition nào;
- semantics nào được áp dụng;
- API nào đã deprecated;
- thay đổi nào breaking;
- code cũ có thể migrate tự động đến đâu;
- ABI có còn tương thích không;
- package nào cần rebuild;
- compiler mới có thể compile code cũ hay không.

---

# 1. Nguyên tắc nền tảng

Axiom phân biệt hoàn toàn:

```text
Language Version
Compiler Version
Language Edition
Standard Library Version
ABI Version
Package Version
Target Version
```

Không được gộp tất cả thành một `version`.

---

# 2. Language Edition

Axiom dùng **edition** để đóng băng semantics của source code.

Ví dụ:

```text
edition 2026
edition 2028
edition 2030
```

Một package khai báo:

```text
edition = "2028"
```

Compiler mới vẫn có thể compile:

```text
edition = "2026"
```

nếu compiler còn hỗ trợ edition đó.

---

# 3. Edition không phải fork ngôn ngữ

Mục tiêu:

```text
Old source
    ↓
New compiler
    ↓
Old semantics
```

không phải:

```text
Old source
    ↓
New compiler
    ↓
randomly changed behavior
```

---

# 4. Compiler compatibility matrix

Compiler phải có:

```text
Compiler × Edition
```

Ví dụ:

```text
             2026   2028   2030
Compiler 1    ✓
Compiler 2    ✓      ✓
Compiler 3    ✓      ✓      ✓
```

---

# 5. Edition support policy

Compiler manifest ghi:

```text
supported_editions:
    2026
    2028
    2030
```

Không được âm thầm bỏ edition.

Việc bỏ support là một compatibility event.

---

# 6. Semantic fingerprint của edition

Mỗi edition có:

```text
EditionFingerprint
```

bao gồm:

```text
syntax rules
type rules
ownership rules
trait rules
evaluation rules
comptime rules
async rules
FFI rules
ABI assumptions
```

---

# 7. Core semantics phải ổn định

Một edition mới chỉ thay đổi semantics khi:

```text
old behavior
    ↓
known problem
    ↓
explicit language proposal
    ↓
compatibility analysis
    ↓
edition boundary
```

Không thay đổi semantic chỉ vì compiler implementation mới.

---

# 8. Breaking change classification

Mỗi thay đổi được phân loại:

```text
NonBreaking
WarningOnly
SourceBreaking
SemanticBreaking
ABI-Breaking
BinaryBreaking
TargetBreaking
ToolingBreaking
```

---

# 9. Ví dụ

Thay đổi:

```text
deprecated function
```

có thể là:

```text
WarningOnly
```

Thay đổi:

```text
type inference result
```

có thể là:

```text
SourceBreaking
```

Thay đổi:

```text
struct ABI layout
```

có thể là:

```text
ABI-Breaking
```

---

# 10. Không được đánh đồng source breaking và semantic breaking

Ví dụ:

```text
old syntax:
fn foo(x: i32)

new syntax:
fn foo(x i32)
```

có thể là:

```text
SourceBreaking
```

nhưng semantics giống nhau.

Trong khi thay đổi:

```text
evaluation order
```

là:

```text
SemanticBreaking
```

---

# 11. Compatibility graph

Compiler duy trì:

```text
CompatibilityGraph
```

với:

```text
Source
Semantic
ABI
Binary
Package
Target
```

Ví dụ:

```text
Axiom 2026
   │
   ├── source compatible → 2028
   ├── semantic compatible → 2028
   └── ABI compatible → conditional
```

---

# 12. Deprecation lifecycle

Một API có lifecycle:

```text
Active
    ↓
Deprecated
    ↓
MigrationRecommended
    ↓
RemovalScheduled
    ↓
Removed
```

Không được nhảy thẳng:

```text
Active → Removed
```

trong stable edition nếu policy không cho phép.

---

# 13. Deprecation metadata

Ví dụ:

```text
@deprecated(
    since = "2028",
    replacement = "new_api",
    removal = "2030"
)
```

Compiler lưu metadata machine-readable.

---

# 14. Deprecation warning

Diagnostic:

```text
WDEPR001
```

phải chứa:

```text
deprecated_since
replacement
removal_edition
migration_hint
```

---

# 15. Deprecated API không tự động biến mất

Trong edition cũ:

```text
edition = 2026
```

API có thể tiếp tục tồn tại.

Edition mới:

```text
edition = 2030
```

có thể không còn API đó.

---

# 16. Compatibility shim

Compiler/library có thể cung cấp:

```text
compat::old_api
```

để package cũ tiếp tục hoạt động.

Shim phải được đánh dấu rõ:

```text
CompatibilityLayer
```

---

# 17. Shim không được thay đổi semantics

Nếu shim chỉ phục vụ source compatibility:

```text
old API
   ↓
adapter
   ↓
new API
```

thì behavior phải tương đương theo contract.

---

# 18. Automatic migration

Axiom có thể cung cấp:

```text
axiom migrate
```

Pipeline:

```text
Source
 ↓
Parse
 ↓
Semantic analysis
 ↓
Migration rules
 ↓
AST/HIR transformation
 ↓
Re-verify
 ↓
Formatted source
```

---

# 19. Không dùng text replacement

Không làm:

```text
replace("old_fn", "new_fn")
```

một cách mù quáng.

Migration phải hoạt động trên:

```text
AST/HIR
```

và hiểu:

- scope;
- type;
- overload;
- trait;
- generic;
- ownership;
- module.

---

# 20. Migration rule

```text
MigrationRule {
    id
    from_edition
    to_edition
    match
    transform
    preconditions
    postconditions
}
```

---

# 21. Migration phải re-enter compiler verification

Sau migration:

```text
Generated Source
      ↓
Parser
      ↓
Resolver
      ↓
TypeCheck
      ↓
Ownership
      ↓
Capability
      ↓
Conformance
```

Không coi migration engine là trusted shortcut.

---

# 22. Migration report

Ví dụ:

```text
3 changes applied
1 manual migration required

Changed:
    old API → new API

Manual:
    behavior of X changed in edition 2030
```

---

# 23. Semantic migration warning

Nếu compiler không thể chứng minh equivalent:

```text
MIGRATE001
```

và không tự động sửa.

---

# 24. Edition migration graph

Không nhất thiết phải migrate:

```text
2026 → 2030
```

trực tiếp.

Compiler có thể:

```text
2026 → 2028 → 2030
```

mỗi bước có transformation riêng.

---

# 25. Preserve source intent

Migration không được tự ý:

- đổi algorithm;
- đổi ownership model;
- đổi concurrency;
- đổi error handling;
- đổi performance characteristics;

nếu migration contract không bao gồm điều đó.

---

# 26. Language feature lifecycle

Mỗi feature có:

```text
Experimental
    ↓
Provisional
    ↓
Stable
    ↓
Deprecated
    ↓
Removed
```

---

# 27. Experimental features

Ví dụ:

```text
@feature("new_async")
```

Compiler phải biết:

```text
feature_id
edition
status
```

---

# 28. Feature interactions

Một feature có thể phụ thuộc feature khác:

```text
GPU
 └── async_gpu
       └── device_events
```

Feature graph phải tránh cycle bất hợp lệ.

---

# 29. Feature stability

Một feature chỉ thành stable khi:

```text
Specification
Reference semantics
Conformance
Compiler
Targets
ABI
Tooling
Performance
```

đã đạt policy.

---

# 30. Feature cannot silently alter Core

Experimental feature không được làm:

```text
Core semantics
```

thay đổi mà không có explicit feature boundary.

---

# 31. Language proposal artifact

Mỗi thay đổi lớn có:

```text
Proposal {
    id
    motivation
    alternatives
    semantic_changes
    syntax_changes
    compatibility
    migration
    ABI_impact
    performance_impact
    implementation_impact
    specification_impact
    test_plan
}
```

---

# 32. Proposal lifecycle

```text
Draft
 ↓
Research
 ↓
Design
 ↓
Prototype
 ↓
Experimental
 ↓
Review
 ↓
Accepted
 ↓
Stable
```

---

# 33. Proposal không được sửa compiler trước specification

Thứ tự ưu tiên:

```text
Design
 ↓
Semantic rule
 ↓
Reference model
 ↓
Conformance tests
 ↓
Compiler
```

Không:

```text
Compiler implementation
 ↓
“compiler hiện làm thế này”
 ↓
specification
```

---

# 34. Semantic diff

Axiom cần:

```text
axiom spec diff
```

để trả lời:

```text
What changed between edition 2028 and 2030?
```

Ví dụ:

```text
OWN-17:
    unchanged

ASYNC-08:
    changed

ABI-12:
    new

TRAIT-31:
    deprecated
```

---

# 35. Machine-readable semantic diff

```text
SemanticChange {
    rule_id
    old_semantics
    new_semantics
    classification
    affected_editions
    migration_rule
}
```

---

# 36. Impact analysis

Khi một semantic rule thay đổi:

```text
Rule
 ↓
Spec dependencies
 ↓
Compiler passes
 ↓
Standard library
 ↓
ABI
 ↓
Tests
 ↓
Packages
```

Compiler phải tìm toàn bộ affected nodes.

---

# 37. Specification dependency graph

343 đã có SpecRuleDB.

345 mở rộng:

```text
SpecRule
 ↓
depends_on
 ↓
affected_by
 ↓
implemented_by
 ↓
tested_by
```

---

# 38. Compiler implementation mapping

Mỗi semantic rule có thể trỏ tới:

```text
Parser
Resolver
TypeChecker
TraitSolver
MIR
Verifier
Optimizer
Codegen
Runtime
```

---

# 39. Change impact report

Ví dụ:

```text
Rule ASYNC-017 changed.

Affected:
    async lowering
    Future Send analysis
    executor contract
    async FFI
    conformance tests: 17
    standard library: 4 APIs
```

Đây là chức năng cực kỳ quan trọng cho AI-agent.

---

# 40. ABI evolution

Language edition và ABI version **không tự động tăng cùng nhau**.

Ví dụ:

```text
Language 2030
ABI 2
```

hoặc:

```text
Language 2030
ABI 1
```

nếu ABI vẫn compatible.

---

# 41. Stable ABI preservation

Nếu một edition thay đổi source semantics nhưng không ảnh hưởng ABI:

```text
ABI remains compatible
```

Điều này rất quan trọng cho dynamic libraries/components.

---

# 42. ABI migration adapter

Nếu cần:

```text
ABI v1
 ↓
adapter
 ↓
ABI v2
```

compiler/toolchain có thể generate adapter nếu contract cho phép.

---

# 43. Binary compatibility matrix

```text
              ABI1   ABI2   ABI3
Library1       ✓
Library2       ✓      ✓
Library3              ✓      ✓
```

---

# 44. Package compatibility

Package metadata:

```text
package {
    language_edition
    compiler_min
    compiler_max
    abi
    std_version
}
```

Compiler dùng để resolve compatibility.

---

# 45. Compiler compatibility

Package có thể yêu cầu:

```text
compiler >= 2.4
compiler < 3.0
```

Nhưng semantic requirement quan trọng hơn compiler version.

---

# 46. Semantic compiler requirement

Có thể khai báo:

```text
requires:
    feature = "stable_trait_defaults"
    edition >= "2028"
```

để tránh phụ thuộc vào compiler version cụ thể khi không cần.

---

# 47. Standard library evolution

Std API có lifecycle riêng:

```text
Core semantics
Standard library API
Platform API
```

Không nên buộc language edition phải thay đổi chỉ vì thêm một `std` function.

---

# 48. Core vs Std evolution

Ví dụ:

```text
new HashMap API
```

không cần edition.

Trong khi:

```text
new ownership rule
```

có thể cần edition.

---

# 49. Compiler bug vs language change

Đây là điểm cực kỳ quan trọng.

Nếu compiler 2.0 sửa:

```text
compiler bug
```

để đúng specification, đây **không phải language breaking change** dù một số chương trình sai trước đây có thể ngừng compile.

Phải phân loại:

```text
BugFixSemanticCorrection
```

riêng với:

```text
LanguageSemanticChange
```

---

# 50. Miscompilation correction

Ví dụ:

```text
Specification:
    program must reject X

Compiler 1:
    accepts X
```

Compiler 2:

```text
rejects X
```

không được ghi là:

```text
“language changed”
```

mà:

```text
“compiler corrected to conform to specification”
```

---

# 51. Compatibility exception

Một compiler bug fix có thể gây source break.

Release system phải ghi:

```text
CorrectnessFix
SourceImpact = possible
SemanticChange = none
```

---

# 52. Deprecated syntax lint levels

Cho phép:

```text
allow
warn
deny
```

nhưng semantic validity vẫn do compiler quyết định.

---

# 53. Compatibility policy

Package/project có thể chọn:

```text
strict
balanced
legacy
```

Ví dụ:

```text
strict:
    deprecated = error

balanced:
    deprecated = warning

legacy:
    migration hints only
```

Đây là tooling policy, không thay đổi language semantics.

---

# 54. Migration confidence

Migration engine có thể trả:

```text
Exact
ProvenEquivalent
LikelyEquivalent
ManualReview
Impossible
```

Chỉ:

```text
Exact
ProvenEquivalent
```

mới nên tự động áp dụng trong mode an toàn.

---

# 55. Semantic migration proof

Nếu migration:

```text
P_old
→
P_new
```

compiler có thể chứng minh:

```text
Semantics(P_old) == Semantics(P_new)
```

thì ghi:

```text
MigrationProof
```

---

# 56. Migration tests

Mỗi migration rule phải có:

```text
before.ax
after.ax
expected equivalence
```

và chạy qua 343.

---

# 57. Edition interoperability

Một package edition 2026 có thể dependency package edition 2030 nếu API boundary cho phép.

Graph:

```text
Package A [2026]
       ↓
Package B [2030]
```

Compiler phải xác định semantic boundary.

---

# 58. Không trộn semantics giữa editions

Một module edition 2026 không tự động nhận semantics 2030 chỉ vì import package 2030.

Edition thuộc về source/module/package theo contract.

---

# 59. Generic boundaries

Generic API giữa editions cần được kiểm tra:

```text
types
traits
associated types
ABI
ownership
capabilities
```

đặc biệt khi compiler nội bộ monomorphize.

---

# 60. Trait evolution

Trait thay đổi là một trong những breaking change khó nhất.

Ví dụ:

```text
trait Iterator {
    fn next(...)
}
```

thêm:

```text
fn size_hint(...)
```

có thể ảnh hưởng:

- implementations;
- object ABI;
- generic constraints;
- coherence;
- dynamic dispatch.

Do đó trait evolution phải có analyzer riêng.

---

# 61. Trait compatibility analyzer

```text
TraitChange {
    added_methods
    removed_methods
    changed_methods
    changed_defaults
    changed_associated_types
    changed_bounds
    object_compatibility
    ABI_impact
}
```

---

# 62. Struct evolution

Stable ABI struct:

```text
@repr(C)
```

không được thêm field một cách vô tư.

Analyzer phải kiểm tra:

```text
size
alignment
offset
padding
field order
ABI passing
```

---

# 63. Enum evolution

Stable enum cần kiểm tra:

```text
discriminant
representation
valid values
size
alignment
niche
```

---

# 64. FFI evolution

Thay đổi:

```text
nullable
ownership
allocator
callback lifetime
threading
```

đều có thể là breaking FFI change.

345 phải liên kết với 326.

---

# 65. Component evolution

Component contract thay đổi:

```text
service
ABI
capability
lifecycle
state schema
```

phải được phân loại compatibility.

---

# 66. State migration

Hot reload/state schema:

```text
Schema v1
 ↓
Migration
 ↓
Schema v2
```

phải được versioned độc lập với language edition.

---

# 67. Documentation conformance

Documentation của language có thể được kiểm tra:

```text
Example
 ↓
Compile
 ↓
Run
```

Như vậy code example trong specification không bị stale.

---

# 68. Specification examples become tests

Ví dụ trong spec:

```text
Example:
    fn add(a: i32, b: i32) -> i32 {
        a + b
    }
```

có metadata:

```text
@spec_example("FUNC-001")
```

và tự động trở thành conformance test.

---

# 69. Dead specification detection

Nếu một semantic rule:

```text
không có test
không có compiler mapping
không có reference semantics
```

thì:

```text
SPEC-GAP
```

được báo.

---

# 70. Dead compiler semantics detection

Ngược lại nếu compiler có behavior:

```text
compiler rule
```

nhưng:

```text
không có spec rule
```

có thể báo:

```text
UNSPECIFIED-COMPILER-BEHAVIOR
```

Điều này rất hữu ích để ngăn implementation detail vô tình trở thành language semantics.

---

# 71. Language evolution dashboard

Có thể xem:

```text
Core Rules
    Stable: 812
    Changed: 4
    Deprecated: 7

Features
    Stable: 91
    Experimental: 12

ABI
    Stable Contracts: 128
```

---

# 72. Compiler DB

345 bổ sung:

```text
EditionDB
LanguageVersionDB
FeatureLifecycleDB
ProposalDB
SemanticChangeDB
CompatibilityGraphDB
DeprecationDB
MigrationDB
MigrationProofDB
SpecDependencyDB
ChangeImpactDB
TraitEvolutionDB
ApiEvolutionDB
EditionInteropDB
```

---

# 73. Implementation tree

```text
compiler/
└── evolution/
    ├── edition/
    ├── version/
    ├── feature/
    ├── proposal/
    ├── compatibility/
    ├── deprecation/
    ├── migration/
    ├── semantic_diff/
    ├── impact_analysis/
    ├── trait_evolution/
    ├── api_evolution/
    ├── abi_evolution/
    ├── ffi_evolution/
    ├── component_evolution/
    ├── edition_interop/
    ├── spec_mapping/
    └── diagnostics/

tools/
└── migration/
    ├── planner/
    ├── transformer/
    ├── verifier/
    └── reporting/
```

---

# 74. CLI

Edition:

```text
axiom edition list
axiom edition inspect
axiom edition diff
```

Evolution:

```text
axiom evolve inspect
axiom evolve diff
axiom evolve impact
```

Migration:

```text
axiom migrate
axiom migrate check
axiom migrate plan
axiom migrate verify
```

Compatibility:

```text
axiom compat source
axiom compat semantic
axiom compat abi
axiom compat binary
axiom compat package
```

API:

```text
axiom api diff
axiom api check
```

Trait:

```text
axiom trait diff
axiom trait compatibility
```

---

# 75. Invariants

```text
AEVOL-01
Compiler version and language edition are distinct concepts.

AEVOL-02
A new compiler must preserve the semantics of supported older editions.

AEVOL-03
Language semantic changes must be explicitly versioned.

AEVOL-04
Compiler bug fixes must not be misclassified as language changes.

AEVOL-05
Source compatibility and semantic compatibility are distinct.

AEVOL-06
Semantic compatibility and ABI compatibility are distinct.

AEVOL-07
ABI version changes are independent from language edition changes.

AEVOL-08
Deprecation must have machine-readable metadata.

AEVOL-09
Stable APIs must not disappear without an explicit compatibility transition.

AEVOL-10
Automatic migration must operate on semantic syntax structures, not blind text replacement.

AEVOL-11
Migrated source must pass normal compiler verification.

AEVOL-12
Migration must never silently alter ownership or concurrency semantics.

AEVOL-13
Migration claiming semantic equivalence must provide evidence.

AEVOL-14
Experimental features must be explicitly gated.

AEVOL-15
Experimental features must not silently redefine unrelated Core semantics.

AEVOL-16
Every normative semantic change must have a specification rule.

AEVOL-17
Every normative semantic change must have conformance coverage.

AEVOL-18
Every semantic rule should have a compiler implementation mapping.

AEVOL-19
Compiler behavior without specification coverage must be detectable.

AEVOL-20
Edition interoperability must preserve each module's declared semantics.

AEVOL-21
Trait evolution must be checked for source, semantic and ABI impact.

AEVOL-22
Stable ABI structures must be checked for layout compatibility.

AEVOL-23
FFI contract evolution must be checked independently.

AEVOL-24
Component contract evolution must be checked independently.

AEVOL-25
Deprecation warnings must not alter program semantics.

AEVOL-26
Breaking changes must produce machine-readable compatibility reports.

AEVOL-27
Language migration must be deterministic under identical inputs.

AEVOL-28
Specification examples may be promoted into conformance tests.

AEVOL-29
Language evolution must integrate with release qualification.

AEVOL-30
No compiler implementation detail becomes a language guarantee merely because it exists in one compiler version.
```

---

# 76. Definition of Done

BOOTSTRAP-345 hoàn thành khi Axiom có:

- Language Edition system;
- edition compatibility matrix;
- semantic fingerprints per edition;
- feature lifecycle;
- proposal model;
- breaking-change classifier;
- deprecation system;
- semantic compatibility graph;
- source/semantic/ABI/binary compatibility analyzer;
- AST/HIR migration engine;
- migration proof mechanism;
- migration regression tests;
- edition interoperability;
- trait evolution analyzer;
- API evolution analyzer;
- ABI evolution analyzer;
- FFI evolution analyzer;
- component evolution analyzer;
- specification dependency graph;
- semantic impact analysis;
- compiler-to-spec mapping;
- specification gap detection;
- dead semantic implementation detection;
- machine-readable migration reports;
- integration với package manager;
- integration với `.axif`;
- integration với ABI engine;
- integration với conformance engine;
- integration với release qualification.

---

## Kiến trúc sau 345

Axiom lúc này không chỉ biết **compiler hiện tại đúng hay sai**, mà còn có cơ chế trả lời:

```text
                    AXIOM SPEC
                        │
                        ▼
                 Semantic Rules
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
        Reference Model       Compiler
              │                   │
              └─────────┬─────────┘
                        ▼
                  Conformance
                        │
                        ▼
                 Release Engine
                        │
                        ▼
                  Stable Edition
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
        Next Edition          Old Edition
             │                     │
             └──────────┬──────────┘
                        ▼
                Compatibility
                        │
                        ▼
                    Migration
                        │
                        ▼
                 Re-verification
```

Điểm cốt lõi của 345 là:

> **Axiom có thể tiến hóa mà không biến thành một ngôn ngữ luôn phá vỡ code cũ.**

Đặc biệt, **edition, compiler version, ABI version và package version được tách riêng**. Đây là quyết định kiến trúc rất quan trọng cho mục tiêu dài hạn của Axiom: compiler có thể phát triển nhanh, language semantics có thể tiến hóa có kiểm soát, trong khi binary/ABI và codebase cũ vẫn có đường tương thích rõ ràng.