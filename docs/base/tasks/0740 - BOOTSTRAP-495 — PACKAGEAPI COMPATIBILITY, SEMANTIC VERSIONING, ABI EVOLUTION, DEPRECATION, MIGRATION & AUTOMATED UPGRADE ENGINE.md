# BOOTSTRAP-495 — PACKAGE/API COMPATIBILITY, SEMANTIC VERSIONING, ABI EVOLUTION, DEPRECATION, MIGRATION & AUTOMATED UPGRADE ENGINE

**Trạng thái: COMPLETED / LOCKED**

495 xây dựng tầng **evolution/compatibility** hoàn chỉnh cho Axiom, nối trực tiếp:

```text id="3x7m1q"
484 Language Evolution
      │
447 Package / ABI Versioning
      │
485 Documentation
      │
486 Semantic Refactoring
      │
493 Binary Interface
      │
495 Compatibility / Migration
      │
492 Dependency Resolution
```

Mục tiêu không chỉ là biết package "có version mới", mà phải xác định **thay đổi nào thực sự ảnh hưởng source/API/ABI/semantic behavior**, sau đó cung cấp migration có kiểm chứng.

---

## 495.1 — Compatibility không phải một khái niệm duy nhất

Axiom phân biệt:

```text
Source Compatibility
API Compatibility
ABI Compatibility
Semantic Compatibility
Behavioral Compatibility
Build Compatibility
Toolchain Compatibility
```

Không được gộp thành một compatibility score.

---

## 495.2 — Source compatibility

Source cũ vẫn compile được với interface mới.

---

## 495.3 — API compatibility

Public symbols/types/functions/contracts vẫn tương thích theo policy.

---

## 495.4 — ABI compatibility

Binary consumer vẫn link/call được binary provider.

---

## 495.5 — Semantic compatibility

Meaning được định nghĩa bởi language specification/interface contract vẫn tương thích.

---

## 495.6 — Behavioral compatibility

Runtime behavior observable bởi consumer vẫn tương thích theo documented contract.

Không được suy luận behavioral equivalence chỉ từ API/ABI equality.

---

## 495.7 — Build compatibility

Package vẫn resolve/build với toolchain/configuration cụ thể.

---

## 495.8 — Compatibility matrix

Tool phải có thể report:

```text id="q2w8m5"
Source     compatible
API        compatible
ABI        incompatible
Semantic   compatible
Build      compatible
```

---

## 495.9 — SemVer

Package có thể dùng:

```text
MAJOR.MINOR.PATCH
```

theo policy của 447.

---

## 495.10 — Major change

Breaking public API/ABI/semantic change có thể yêu cầu major version.

---

## 495.11 — Minor change

Backward-compatible functionality có thể tăng minor.

---

## 495.12 — Patch change

Bug fix không chủ ý thay public contract có thể tăng patch.

---

## 495.13 — SemVer ≠ proof

Version number không chứng minh compatibility.

---

## 495.14 — Compiler compatibility analysis

Compiler/tooling phải kiểm tra actual interface changes.

---

## 495.15 — API diff

So sánh:

```text
old interface
      ↓
new interface
      ↓
API diff
```

---

## 495.16 — ABI diff

So sánh:

- layout;
- alignment;
- calling convention;
- symbol;
- parameter ABI;
- return ABI;
- representation.

---

## 495.17 — Semantic diff

So sánh semantic metadata khi available.

---

## 495.18 — Contract diff

Thay đổi:

```text
requires
ensures
invariant
```

phải được classify riêng.

---

## 495.19 — Effect diff

Thay đổi:

```text
@no_alloc
@no_block
@no_panic
unsafe
```

là compatibility-relevant.

---

## 495.20 — Ownership diff

Thay đổi ownership contract phải được detect.

---

## 495.21 — Concurrency diff

Thay đổi `Send`/`Share` hoặc synchronization contract phải được detect.

---

## 495.22 — Realtime diff

Thay đổi realtime guarantees/effects phải được detect.

---

## 495.23 — Security diff

Thay đổi capability/security requirements phải được detect.

---

## 495.24 — Layout diff

`@repr(C)` layout changes có ABI implications.

---

## 495.25 — Enum evolution

Adding enum variants có thể phá exhaustive `match`.

Tool phải detect dependent matches.

---

## 495.26 — Struct evolution

Adding/removing/reordering public fields được classify theo representation/visibility/ABI.

---

## 495.27 — Trait evolution

Adding required trait method có thể break existing implementations.

---

## 495.28 — Default trait method

Adding default method có compatibility semantics khác adding required method.

---

## 495.29 — Trait contract change

Changing trait contract phải be explicitly reported.

---

## 495.30 — Function parameter change

Parameter type/count/order changes là API change.

---

## 495.31 — Return type change

Return type changes là API change.

---

## 495.32 — Generic constraint change

Strengthening generic constraints có thể break consumers.

---

## 495.33 — Generic constraint weakening

Weakening constraints thường mở rộng accepted programs nhưng vẫn phải classify.

---

## 495.34 — Associated type change

Associated type changes phải được tracked.

---

## 495.35 — Associated constant change

Public associated constants are API surface.

---

## 495.36 — Visibility change

`pub → private` là breaking API change.

---

## 495.37 — Name removal

Removed symbol phải appear in compatibility report.

---

## 495.38 — Rename

Rename nên được represented as semantic rename when provenance available.

---

## 495.39 — Deprecation

API có thể được mark:

```text
deprecated
since
replacement
reason
migration
```

---

## 495.40 — Deprecation ≠ removal

Deprecated API vẫn có thể compile.

---

## 495.41 — Removal schedule

Package có thể document planned removal version.

---

## 495.42 — Deprecation diagnostics

Compiler có thể emit warning/error theo project policy.

---

## 495.43 — Replacement metadata

Deprecated symbol có thể chỉ rõ replacement SymbolId.

---

## 495.44 — Automated migration

Migration engine có thể transform:

```text
old API
→
new API
```

---

## 495.45 — Semantic transformation

Migration dùng AST/semantic model 486, không dùng regex.

---

## 495.46 — Migration transaction

Flow:

```text id="s4n9x2"
Analyze
→ Preview
→ Transform
→ Format
→ Check
→ Test
→ Commit
```

---

## 495.47 — Migration safety

Nếu compiler không thể chứng minh transformation safe, phải giữ nguyên source và report issue.

---

## 495.48 — Mechanical migration

Ví dụ rename SymbolId có thể automated hoàn toàn.

---

## 495.49 — Semantic migration

Nếu thay đổi behavior cần human review.

Tool có thể prepare patch nhưng không tự coi là equivalent.

---

## 495.50 — Migration provenance

Mỗi changed source có thể record:

```text id="u7p2m5"
old SymbolId
new SymbolId
migration rule
compiler version
```

---

## 495.51 — Migration rules

Package author có thể cung cấp migration metadata.

---

## 495.52 — Compiler migrations

Language edition migrations từ 484 sử dụng cùng engine.

---

## 495.53 — Package migrations

Package API migrations sử dụng semantic transformation engine.

---

## 495.54 — Workspace migration

Một migration có thể update nhiều package trong workspace.

---

## 495.55 — Dependency migration order

Dependencies phải được migrated theo dependency graph khi cần.

---

## 495.56 — Bottom-up migration

Internal library có thể migrate trước consumer.

---

## 495.57 — Compatibility adapters

Package có thể cung cấp adapter layer cho old API.

---

## 495.58 — ABI shims

ABI migration có thể cung cấp explicit shim:

```text id="k5x1q8"
old ABI
  ↓
adapter
  ↓
new ABI
```

---

## 495.59 — ABI shim cost

Shim overhead phải explicit.

---

## 495.60 — No hidden ABI adapter

Compiler không silently insert expensive ABI wrappers.

---

## 495.61 — Symbol aliases

Native symbol alias có thể support backward ABI compatibility.

---

## 495.62 — ABI versioning

ABI version độc lập package semantic version.

---

## 495.63 — ABI break

ABI break phải invalidate incompatible binary artifacts.

---

## 495.64 — Binary package rebuild

Nếu ABI fingerprint mismatch:

```text id="b4m8r2"
reject binary
→ source fallback / rebuild
```

---

## 495.65 — Interface compatibility

493 interface fingerprint được dùng làm fast-path.

---

## 495.66 — Fast compatibility

Nếu relevant fingerprints match, full source analysis không cần thiết.

---

## 495.67 — Conservative fallback

Nếu metadata thiếu/không đủ, compiler phải analyze source hoặc reject binary theo policy.

---

## 495.68 — Unknown ≠ incompatible

Thiếu evidence không đồng nghĩa với incompatibility.

---

## 495.69 — Compatibility evidence

Report phải phân biệt:

```text id="f7n3m1"
Proven Compatible
Proven Incompatible
Unknown
Policy Rejected
```

---

## 495.70 — Consumer impact

Tool xác định package nào bị ảnh hưởng bởi API change.

---

## 495.71 — Symbol impact

Impact graph:

```text id="r8q2x6"
Changed Symbol
 ↓
References
 ↓
Functions
 ↓
Packages
 ↓
Artifacts
```

---

## 495.72 — ABI impact graph

ABI change → dependent binary artifacts.

---

## 495.73 — Documentation impact

485 docs/examples referencing changed symbols được detect.

---

## 495.74 — Test impact

477 test mappings được dùng để identify affected tests.

---

## 495.75 — Build impact

487 build graph xác định nodes cần rebuild.

---

## 495.76 — Cache impact

493/494 cache entries affected phải invalidate chính xác.

---

## 495.77 — Minimal invalidation

Không rebuild unrelated packages chỉ vì package version thay đổi nếu semantic interface không ảnh hưởng chúng.

---

## 495.78 — Version update planning

Tool có thể generate update plan:

```text id="v2x7m4"
package A: 1.2 → 1.3
package B: unchanged
package C: rebuild
```

Đây là plan, không phải ranking.

---

## 495.79 — Upgrade groups

Các package có compatibility dependency có thể update as group.

---

## 495.80 — Locked dependencies

Lockfile 492 remains authoritative until explicit update.

---

## 495.81 — Compatibility policy

Project có thể chọn:

```text id="e3m8q1"
strict
compatible-only
allow-breaking
source-only
binary-only
```

---

## 495.82 — CI compatibility

CI có thể kiểm tra:

```text id="j7p4n9"
API break
ABI break
deprecated API
compiler compatibility
```

---

## 495.83 — Baseline interface

Project có thể lưu public interface baseline.

---

## 495.84 — API compatibility check

New release compare với baseline.

---

## 495.85 — ABI baseline

ABI baseline có thể được lưu cho stable library.

---

## 495.86 — Compatibility gates

Release pipeline có thể reject unauthorized breaking changes.

---

## 495.87 — Exception approval

Breaking change có thể được explicitly approved by project policy.

---

## 495.88 — No universal policy

Axiom compiler không tự quyết định mọi project phải follow same compatibility policy.

---

## 495.89 — Migration testing

Automated migration phải compile-check result.

---

## 495.90 — Test execution

Migration có thể chạy affected tests.

---

## 495.91 — Rollback

Migration transaction phải có rollback nếu validation fails.

---

## 495.92 — Partial migration

Failed package không được commit partial workspace transformation.

---

## 495.93 — Generated code

Generated/comptime code phải có provenance.

---

## 495.94 — Generated API migration

Nếu generated code có migration support, engine phải update generator/input thay vì chỉ patch output.

---

## 495.95 — FFI compatibility

451 FFI declarations được đưa vào ABI diff.

---

## 495.96 — Platform compatibility

Platform-specific API changes được classify target-by-target.

---

## 495.97 — Documentation migration

Examples/docs có thể được migrated cùng source.

---

## 495.98 — AI migration interface

AI có thể query:

```text id="z1m6x4"
compatibility()
breaking_changes()
affected_symbols()
migration()
affected_tests()
abi_changes()
```

---

## 495.99 — No automatic semantic claim

Passing compiler/tests does not prove complete behavioral equivalence.

---

## 495.100 — Hard invariants

1. Compatibility có nhiều dimensions.
2. Source/API/ABI/Semantic/Behavioral/Build/Toolchain được phân biệt.
3. Không có aggregate compatibility score.
4. Source compatibility được định nghĩa riêng.
5. API compatibility được định nghĩa riêng.
6. ABI compatibility được định nghĩa riêng.
7. Semantic compatibility được định nghĩa riêng.
8. Behavioral compatibility được định nghĩa riêng.
9. Build compatibility được định nghĩa riêng.
10. SemVer không phải proof.
11. Actual interface changes phải được phân tích.
12. API diff được hỗ trợ.
13. ABI diff được hỗ trợ.
14. Semantic diff được hỗ trợ.
15. Contract diff được hỗ trợ.
16. Effect diff được hỗ trợ.
17. Ownership diff được hỗ trợ.
18. Concurrency diff được hỗ trợ.
19. Realtime diff được hỗ trợ.
20. Security diff được hỗ trợ.
21. Layout diff được hỗ trợ.
22. Enum evolution được phân tích.
23. Struct evolution được phân tích.
24. Trait evolution được phân tích.
25. Default trait method evolution được phân biệt.
26. Trait contract changes được detect.
27. Function signature changes được detect.
28. Generic constraint changes được detect.
29. Associated types được track.
30. Associated constants được track.
31. Visibility changes được detect.
32. Symbol removal được detect.
33. Rename được biểu diễn semantic khi có thể.
34. Deprecation metadata được hỗ trợ.
35. Deprecation không đồng nghĩa removal.
36. Replacement SymbolId được hỗ trợ.
37. Automated migration được hỗ trợ.
38. Migration dùng semantic transformation.
39. Migration có transaction.
40. Unsafe transformation phải được review.
41. Mechanical migration có thể tự động.
42. Semantic migration không tự nhận equivalent.
43. Migration provenance được record.
44. Package-author migration rules được hỗ trợ.
45. Language migration dùng cùng engine.
46. Workspace migration được hỗ trợ.
47. Dependency migration order được xác định.
48. Compatibility adapters được hỗ trợ.
49. ABI shims được hỗ trợ.
50. ABI shim cost phải explicit.
51. Không hidden ABI adapter.
52. Symbol aliases được hỗ trợ.
53. ABI version độc lập package version.
54. ABI break invalidates incompatible binary.
55. Binary rebuild/fallback được hỗ trợ.
56. Interface fingerprint được dùng fast-path.
57. Missing metadata không tự suy ra incompatibility.
58. Unknown được phân biệt với incompatible.
59. Compatibility evidence có provenance.
60. Consumer impact analysis được hỗ trợ.
61. Symbol impact graph được hỗ trợ.
62. ABI impact graph được hỗ trợ.
63. Documentation impact được hỗ trợ.
64. Test impact được hỗ trợ.
65. Build impact được hỗ trợ.
66. Cache impact được hỗ trợ.
67. Minimal invalidation được hỗ trợ.
68. Upgrade plan được hỗ trợ.
69. Lockfile remains authoritative.
70. Compatibility policy configurable.
71. CI compatibility checks được hỗ trợ.
72. Baseline interface được hỗ trợ.
73. Baseline ABI được hỗ trợ.
74. Release compatibility gates được hỗ trợ.
75. Project có thể explicitly approve breaking changes.
76. Compiler không áp đặt một compatibility policy duy nhất.
77. Migration phải compile-check.
78. Affected tests có thể được chạy.
79. Migration có rollback.
80. Failed migration không partial commit.
81. Generated code provenance được giữ.
82. Generator migration ưu tiên update source/generator.
83. FFI ABI được kiểm tra.
84. Platform compatibility được phân tích theo target.
85. Documentation/examples có thể migrate.
86. AI compatibility queries được hỗ trợ.
87. Compiler/tests không phải behavioral proof.
88. Compatibility analysis phải deterministic.
89. Migration phải reproducible.
90. Compatibility reports machine-readable.
91. API/ABI/semantic changes không bị che bởi version number.
92. Breaking changes phải trace về changed symbols/contracts/layout.
93. Binary consumers phải được xác định từ dependency graph.
94. Source consumers phải được xác định từ semantic graph.
95. Cache invalidation phải dựa semantic/ABI identity.
96. Compatibility tooling không được sửa source ngoài transaction.
97. Compatibility tooling không được tự fetch dependencies ngoài package policy.
98. Migration không được thay đổi semantics âm thầm.
99. Human review points phải machine-readable.
100. **Axiom phải biến package evolution thành một quy trình có thể kiểm chứng: phát hiện chính xác thay đổi → xác định impact → phân loại source/API/ABI/semantic risk → tạo migration nếu có thể → validate → commit; version number chỉ là metadata, không phải bằng chứng compatibility.**

**BOOTSTRAP-495 hoàn tất / LOCKED.**

---

# BOOTSTRAP-496 — LANGUAGE/COMPILER EXTENSIBILITY, PLUGIN COMPILER, CUSTOM DERIVE, CODE GENERATOR, MACRO SYSTEM & AST/SEMANTIC TRANSFORMATION

496 giải quyết khả năng mở rộng compiler/language tooling mà **không phá compiler core**.

Đây là bước quan trọng vì Axiom đã có:

- comptime 431;
- package/build 432/487;
- semantic metadata 446;
- docs 485;
- semantic transformation 486;
- registry 491;
- binary interface 493;
- compatibility/migration 495.

Kiến trúc:

```text id="p5m8x3"
                    Axiom Compiler
                          │
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
      Language Core    Semantic DB      Build Graph
                          │
                ┌─────────┼─────────┐
                ↓         ↓         ↓
             Derive    Generator   Analyzer
                │         │         │
                └─────────┼─────────┘
                          ↓
                  Semantic Transform
                          ↓
                       Axiom IR
```

Nguyên tắc trung tâm:

> **Mở rộng khả năng của ecosystem mà không biến compiler thành một runtime/plugin soup khó kiểm soát.**

---

## 496.1 — Language core immutable boundary

Extension không được âm thầm thay đổi core language semantics.

---

## 496.2 — Extension ≠ language feature

Một generator tạo code không phải compiler feature mới.

---

## 496.3 — Compiler plugin

Compiler plugin là optional tooling capability.

---

## 496.4 — Plugin trust

Compiler plugin chạy trong compiler process phải được coi là trusted code.

---

## 496.5 — Untrusted extension

Untrusted extension phải chạy out-of-process/WASM/sandbox.

---

## 496.6 — Compiler crash isolation

Out-of-process plugin crash không được corrupt compiler state.

---

## 496.7 — Plugin API

Plugin API phải versioned.

---

## 496.8 — Plugin ABI

Native compiler plugins cần ABI riêng.

---

## 496.9 — Plugin semantic API

Plugin có thể query:

```text id="y4m2p8"
symbols
types
traits
layouts
attributes
source spans
contracts
effects
```

---

## 496.10 — Read-only semantic access

Default plugin access là read-only.

---

## 496.11 — Transform permission

Source/semantic mutation phải yêu cầu explicit transformation capability.

---

## 496.12 — Transactional transformation

Transformation:

```text id="v8q3m1"
prepare
→ preview
→ validate
→ commit
```

---

## 496.13 — AST transformation

Plugin có thể transform AST nếu API cho phép.

---

## 496.14 — Semantic transformation

Preferred API là semantic transformation.

---

## 496.15 — Text macro

Raw token/text macro không phải default mechanism.

---

## 496.16 — Hygienic transformation

Generated identifiers phải có hygiene/provenance.

---

## 496.17 — Name collision

Generated symbols không được vô tình capture local identifiers.

---

## 496.18 — Source provenance

Generated source mapping:

```text id="x6m1q9"
generated symbol
→ generator
→ input symbol
→ source span
```

---

## 496.19 — Derive

Built-in-style `derive` mechanism có thể generate implementations.

Ví dụ:

```text
@derive(Eq, Hash, Debug)
struct User {
    id: u64
}
```

---

## 496.20 — Derive contract

Derive chỉ được generate APIs được specification cho phép.

---

## 496.21 — Custom derive

Package có thể provide custom derive generator.

---

## 496.22 — Custom derive input

Generator nhận semantic description thay vì raw source text khi có thể.

---

## 496.23 — Custom derive output

Output là AST/semantic items, không phải arbitrary compiler memory mutation.

---

## 496.24 — Generator determinism

Generator phải deterministic với cùng inputs.

---

## 496.25 — Generator environment

Generator không được implicit access filesystem/network/clock/random.

---

## 496.26 — Explicit generator capabilities

Nếu cần external resource, đó là build tool capability được khai báo trong 487.

---

## 496.27 — Generator dependency

Generator là dependency class riêng trong 492.

---

## 496.28 — Build-time code generation

Build generator chạy trước compilation khi graph yêu cầu.

---

## 496.29 — Comptime vs generator

```text id="h4r7x2"
comptime
    = language-level deterministic computation

generator
    = build-time transformation/tool
```

---

## 496.30 — Macro vs comptime

Không dùng macro để thay thế mọi compile-time computation.

---

## 496.31 — Declarative attributes

Attributes có thể attach metadata:

```text id="q7m3x8"
@inline
@repr(C)
@deprecated
@derive(...)
```

---

## 496.32 — Attribute namespaces

Third-party attributes phải có namespace để tránh collision.

---

## 496.33 — Unknown attributes

Compiler phải reject hoặc explicitly allow according to attribute policy; không silently ignore semantic attributes.

---

## 496.34 — Attribute validation

Attribute processor kiểm tra:

- target;
- arguments;
- type;
- semantic constraints.

---

## 496.35 — Compiler built-in attributes

Core attributes có stable semantics.

---

## 496.36 — External attributes

External attributes không được modify language semantics ngoài extension boundary.

---

## 496.37 — Generator output visibility

Generated public API phải appear trong semantic metadata.

---

## 496.38 — Generated API docs

485 documentation engine phải thấy generated symbols.

---

## 496.39 — Generated tests

Generators có thể emit test items.

---

## 496.40 — Generated contracts

Generator có thể emit contracts nhưng compiler vẫn type-check/validate chúng.

---

## 496.41 — Generated unsafe code

Unsafe generated code phải retain unsafe provenance.

---

## 496.42 — Generated FFI

Generated FFI bindings phải preserve 451 provenance.

---

## 496.43 — Binding generators

SDK/header binding generator nằm ở tooling layer, không compiler core.

---

## 496.44 — Schema generators

Database/network serialization schemas có thể generate Axiom types/code.

---

## 496.45 — Serialization derive

485/454/455 serialization implementations có thể dùng derive.

---

## 496.46 — Reflection generation

Compile-time reflection có thể generate metadata/code.

---

## 496.47 — Runtime reflection

Runtime reflection vẫn không mặc định.

---

## 496.48 — Semantic query API

Extension có thể query:

```text id="g6x2p9"
type_of
layout_of
implements
references
callers
callees
effects
contracts
```

---

## 496.49 — Incremental extension

Generator results được cache.

---

## 496.50 — Generator fingerprint

Fingerprint gồm:

```text id="m3q7x1"
generator version
generator package hash
input semantic hashes
target
features
configuration
```

---

## 496.51 — Generator invalidation

Thay đổi generator hoặc semantic input invalidate output.

---

## 496.52 — Generated artifact cache

Generated AST/interface/source có thể cache content-addressed.

---

## 496.53 — No stale generated code

Compiler phải detect generated artifact provenance mismatch.

---

## 496.54 — Extension dependency graph

Generator dependencies được đưa vào build graph.

---

## 496.55 — Cyclic generation

Generator cycles phải detect.

---

## 496.56 — Phase ordering

Canonical:

```text id="n8w4c2"
load
→ parse
→ semantic analysis
→ generator/derive
→ re-enter semantic analysis
→ lower
```

Không được tạo vòng vô hạn.

---

## 496.57 — Generated declaration phase

Generated declarations phải được collect trước khi dependent type checking nếu dependency yêu cầu.

---

## 496.58 — Multi-pass generation

Có thể support nhiều generation phases nhưng mỗi phase phải explicit.

---

## 496.59 — Fixed-point generation

Nếu hỗ trợ fixed-point, phải có convergence/resource limit.

---

## 496.60 — Recursion limit

Generator recursion phải có giới hạn.

---

## 496.61 — Output limit

Generator có output size limit.

---

## 496.62 — CPU/time limit

Build generators có resource policy.

---

## 496.63 — Memory limit

Generator memory usage có thể bị giới hạn.

---

## 496.64 — Diagnostic provenance

Generator diagnostics map về:

```text id="k7x2m4"
generator source
input source
generated source
```

---

## 496.65 — Generated code errors

Error trong generated code phải chỉ rõ generator provenance.

---

## 496.66 — User source error

Không đổ lỗi cho generator nếu original input invalid.

---

## 496.67 — IDE integration

LSP phải hiểu generated symbols.

---

## 496.68 — Go-to-definition

Generated declaration có thể link về generator/input.

---

## 496.69 — Find references

Generated references phải xuất hiện trong semantic graph.

---

## 496.70 — Rename

486 rename phải cập nhật generated source/input khi generator supports semantic references.

---

## 496.71 — Generator contract

Generator có thể declare:

```text id="s5m8q2"
inputs
outputs
effects
capabilities
targets
```

---

## 496.72 — Generator effect model

Generator có effect metadata tương tự build tools.

---

## 496.73 — Network generator

Network access chỉ được phép nếu explicitly declared build capability.

---

## 496.74 — Filesystem generator

Filesystem access explicit.

---

## 496.75 — Clock/random generator

Nondeterministic input phải explicit và làm build non-reproducible hoặc fingerprinted.

---

## 496.76 — Reproducibility

Deterministic generator là default.

---

## 496.77 — Plugin package distribution

496 plugins/generators được package như package ecosystem 491.

---

## 496.78 — Plugin target compatibility

Plugin host ABI/compiler compatibility phải được verify.

---

## 496.79 — Plugin compiler compatibility

Plugin phải declare supported compiler versions/API schema.

---

## 496.80 — Plugin isolation

Compiler plugin có thể:

```text id="p2x7m5"
in-process trusted
out-of-process
WASM sandbox
```

---

## 496.81 — Plugin capability manifest

Plugin manifest khai báo quyền.

---

## 496.82 — Plugin update

Plugin updates phải follow 495 compatibility/migration policy.

---

## 496.83 — Plugin crash

Failure phải produce structured diagnostic.

---

## 496.84 — Plugin timeout

Infinite/hung plugin phải có timeout/cancellation policy.

---

## 496.85 — Plugin output validation

Compiler validates generated AST/semantic items.

---

## 496.86 — Plugin cannot bypass type checker

Generated code always passes ordinary compiler semantic validation.

---

## 496.87 — Plugin cannot inject arbitrary machine code

Except explicitly trusted compiler backend/tooling interfaces.

---

## 496.88 — Backend extensions

ISA/backend extension API is separate from source-level generator API.

---

## 496.89 — Compiler backend plugin

Experimental targets may be external backend packages/tools.

Production native backend remains governed by 438/482.

---

## 496.90 — No mandatory plugin framework

Small/freestanding compiler profiles may omit extension runtime.

---

## 496.91 — Extension registry

Compiler may discover installed extensions from manifest.

---

## 496.92 — Extension selection

Selection must be deterministic.

---

## 496.93 — Version resolution

Extension dependencies use 492.

---

## 496.94 — Extension trust

490 package trust/security policies apply.

---

## 496.95 — AI extension API

AI can query extension:

```text id="b5m9x1"
what it generates
inputs
outputs
effects
capabilities
dependencies
```

---

## 496.96 — AI-generated transformation

AI-generated patches must use 486 transaction/validation.

---

## 496.97 — No opaque AI macro

AI-generated code must become ordinary Axiom source/semantic artifacts with provenance.

---

## 496.98 — Testing

496 must test:

- deterministic generation;
- collision/hygiene;
- incremental invalidation;
- plugin crash;
- plugin timeout;
- malicious output;
- generated unsafe code;
- LSP mapping;
- reproducibility.

---

## 496.99 — Performance

Extension overhead must disappear from programs that do not use it.

---

## 496.100 — Hard invariants

1. Language core có boundary rõ.
2. Extension không silently thay core semantics.
3. Compiler plugin là optional.
4. Trusted in-process plugin được phân biệt.
5. Untrusted plugin có isolation.
6. Plugin API versioned.
7. Plugin ABI versioned.
8. Semantic query API được hỗ trợ.
9. Plugin access mặc định read-only.
10. Mutation phải explicit.
11. Mutation transactional.
12. AST transformation được hỗ trợ.
13. Semantic transformation được ưu tiên.
14. Raw text macro không phải default.
15. Generated identifiers có hygiene.
16. Name capture phải được ngăn chặn.
17. Generated source có provenance.
18. Derive mechanism được hỗ trợ.
19. Custom derive được hỗ trợ.
20. Custom derive nhận semantic input khi có thể.
21. Output của generator là semantic/AST items.
22. Generator deterministic mặc định.
23. Generator không implicit filesystem/network.
24. External capabilities phải explicit.
25. Generator là dependency class riêng.
26. Build-time generator được hỗ trợ.
27. Comptime khác generator.
28. Macro không thay thế toàn bộ comptime.
29. Attributes có namespace.
30. Unknown attributes có policy rõ.
31. Attributes được validate.
32. Built-in attributes có stable semantics.
33. External attributes không được silently thay language semantics.
34. Generated public API xuất hiện trong metadata.
35. Generated docs được hỗ trợ.
36. Generated tests được hỗ trợ.
37. Generated contracts vẫn được compiler validate.
38. Generated unsafe code giữ provenance.
39. Generated FFI giữ provenance.
40. Binding generators nằm ngoài compiler core.
41. Schema generators được hỗ trợ.
42. Serialization derive được hỗ trợ.
43. Compile-time reflection có thể generate code.
44. Runtime reflection không mặc định.
45. Semantic query API được chuẩn hóa.
46. Generator result được cache.
47. Generator fingerprint đầy đủ.
48. Generator invalidation deterministic.
49. Generated artifact có thể content-addressed.
50. Stale generated code phải bị detect.
51. Generator dependency nằm trong build graph.
52. Generator cycle được detect.
53. Generation phase ordering deterministic.
54. Generated declarations được collect đúng phase.
55. Multi-pass generation explicit.
56. Fixed-point generation nếu có phải bounded.
57. Generator recursion bounded.
58. Generator output bounded.
59. Generator CPU/time bounded theo policy.
60. Generator memory bounded theo policy.
61. Generator diagnostics có provenance.
62. Generated-code errors map được về source/generator.
63. Original source errors không bị che bởi generator.
64. LSP hiểu generated symbols.
65. Go-to-definition giữ provenance.
66. References include generated references.
67. Rename hiểu generated references khi generator hỗ trợ.
68. Generator contract mô tả inputs/outputs/effects/capabilities.
69. Generator effects được metadata.
70. Network access explicit.
71. Filesystem access explicit.
72. Clock/random access explicit.
73. Nondeterministic generation được fingerprint.
74. Deterministic generation là default.
75. Plugins được distribute qua package ecosystem.
76. Plugin target compatibility được verify.
77. Plugin compiler compatibility được verify.
78. Plugin isolation có nhiều mode.
79. Plugin capability manifest được hỗ trợ.
80. Plugin updates obey compatibility policy.
81. Plugin crash có structured diagnostics.
82. Plugin timeout/cancellation được hỗ trợ.
83. Generated output được compiler validate.
84. Plugin không bypass type checker.
85. Plugin không arbitrary inject machine code ngoài trusted backend interfaces.
86. Backend extensions khác source generators.
87. External backend không trở thành mandatory production compiler dependency.
88. Small/freestanding compiler có thể omit extension framework.
89. Extension discovery deterministic.
90. Extension version resolution dùng 492.
91. Extension trust dùng 490.
92. AI extension queries được hỗ trợ.
93. AI-generated transformations dùng transactional validation.
94. AI-generated code không phải opaque compiler behavior.
95. Generated code phải có provenance.
96. Extension tests cover determinism/security/failure.
97. Extension overhead không ảnh hưởng chương trình không sử dụng extension.
98. Extension artifacts được incremental-cache.
99. Extension semantics không được bypass compiler correctness boundaries.
100. **Axiom extension system phải mở rộng compiler/tooling bằng semantic, deterministic, transactional transformations với provenance và capability boundaries rõ ràng; generator/plugin không được trở thành đường vòng để bypass type checker, ownership, security, reproducibility hoặc compiler trust model.**

**BOOTSTRAP-496 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
491  Package Registry / CAS / Mirrors / Offline Vendor        LOCKED
492  Dependency Resolution / Workspace / Features             LOCKED
493  Binary Interface / Precompiled Generics                  LOCKED
494  Distributed Build / Remote Cache / Build Farm            LOCKED
495  Compatibility / Migration / ABI Evolution                LOCKED
496  Compiler Extension / Derive / Generator / Macro          LOCKED
```

**Task kế tiếp: `BOOTSTRAP-497 — PACKAGE SCRIPTING, BUILD SYSTEM EXTENSIONS, CODE GENERATION PIPELINE, RESOURCE COMPILERS & HERMETIC BUILD PLUGINS`.**