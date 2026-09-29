# BOOTSTRAP-485 — DOCUMENTATION, API DOCS, LANGUAGE REFERENCE, EXAMPLES, DOC TESTS & KNOWLEDGE GRAPH

**Trạng thái: COMPLETED / LOCKED**

485 định nghĩa documentation như một **artifact có cấu trúc**, không chỉ là văn bản cho con người đọc.

Mục tiêu:

```text id="5p4x1m"
Source
  ↓
Semantic Metadata
  ↓
Documentation Model
  ├── Language Reference
  ├── API Reference
  ├── Examples
  ├── Tutorials
  ├── Doc Tests
  └── Knowledge Graph
```

---

## 485.1 — Documentation ≠ Source Comments

Documentation có thể lấy dữ liệu từ source nhưng semantic documentation phải được compiler/tooling hiểu độc lập.

---

## 485.2 — Documentation layers

```text id="n0k4xs"
Language Reference
API Reference
Package Documentation
Module Documentation
Type Documentation
Function Documentation
Example Documentation
Tutorial Documentation
Architecture Documentation
```

---

## 485.3 — Language Reference

Language reference mô tả normative semantics:

- syntax;
- types;
- ownership;
- traits;
- generics;
- comptime;
- concurrency;
- memory;
- ABI;
- contracts;
- error model.

---

## 485.4 — API Documentation

API docs được tạo từ semantic declarations:

```text id="9g8s2m"
package
 └── module
      └── type
           ├── field
           ├── method
           └── trait implementation
```

---

## 485.5 — Documentation comments

Conceptual syntax:

```text id="5l1x8k"
/// Calculate the length of this vector.
fn length(self: Vec2) -> f32 { ... }
```

---

## 485.6 — Structured documentation

Documentation node:

```text id="j3q7v9"
DocItem {
    symbol_id
    kind
    summary
    description
    parameters
    returns
    errors
    examples
    contracts
    safety
    effects
    see_also
}
```

---

## 485.7 — Parameter documentation

Có thể liên kết trực tiếp tới semantic parameter ID thay vì chỉ dùng text.

---

## 485.8 — Return documentation

Return docs phải phân biệt:

```text id="g6n2p0"
normal value
Result<T,E>
Option<T>
never
panic
```

---

## 485.9 — Error documentation

Function documentation có thể mô tả các `E` có thể trả về.

Không được tự động coi mọi panic là Result error.

---

## 485.10 — Safety documentation

Unsafe API phải có section:

```text id="z8r1q5"
Safety
```

mô tả caller obligations.

---

## 485.11 — Contract documentation

479 contracts có thể tự động xuất hiện trong API docs.

---

## 485.12 — Effect documentation

Compiler metadata có thể expose:

```text id="e2k7w4"
allocates
blocks
panics
unsafe
IO
async
realtime
```

---

## 485.13 — Ownership documentation

API docs có thể biểu diễn:

```text id="q5d0m8"
borrowed
owned
consumes
returns_owned
```

---

## 485.14 — ABI documentation

FFI APIs phải có:

- ABI;
- calling convention;
- layout;
- ownership;
- safety boundary.

---

## 485.15 — Examples

Example phải là first-class documentation artifact.

```text id="w7p2c4"
Example {
    source
    expected_output?
    dependencies
    target
    edition
}
```

---

## 485.16 — Runnable examples

Tooling có thể compile/run examples.

---

## 485.17 — Doc tests

Documentation code blocks có thể trở thành test:

```text id="2j6m9a"
documentation
    ↓
extract
    ↓
compile
    ↓
run
    ↓
verify
```

---

## 485.18 — Expected output

Có thể khai báo expected output.

Output comparison phải có mode rõ:

```text id="0m7v3x"
exact
normalized
pattern
custom verifier
```

---

## 485.19 — No arbitrary output normalization

Tool không được silently bỏ qua khác biệt output.

---

## 485.20 — Compile-only example

Ví dụ có thể chỉ yêu cầu:

```text id="p8n1c6"
compiles successfully
```

---

## 485.21 — Target-specific examples

Example có thể chỉ applicable trên target:

```text id="x4f6s2"
@target(os = "windows")
```

---

## 485.22 — Feature-specific examples

Example có thể yêu cầu package features.

---

## 485.23 — Dependency isolation

Doc test phải chạy trong isolated build environment.

---

## 485.24 — Network isolation

Documentation examples không được tự động truy cập network trong test.

Nếu cần phải explicit.

---

## 485.25 — Filesystem isolation

Doc tests phải có controlled workspace.

---

## 485.26 — Nondeterministic examples

Examples sử dụng random/time/concurrency phải có deterministic test mode nếu muốn output comparison.

---

## 485.27 — Documentation warnings

Broken links, missing references, invalid code examples là diagnostics.

---

## 485.28 — Documentation compiler

Có thể có:

```text id="5s9w1k"
axiom doc
```

---

## 485.29 — Documentation output

Có thể tạo:

```text id="2f6m8r"
HTML
Markdown
JSON
plain text
IDE metadata
```

---

## 485.30 — Static site generation

HTML documentation có thể có:

- search;
- source links;
- cross references;
- trait implementations;
- dependency graph.

---

## 485.31 — Symbol navigation

Mỗi API item phải có stable SymbolId từ 446.

---

## 485.32 — Cross-reference

Docs có thể link:

```text id="j4k8w0"
type → method
method → trait
trait → implementation
function → error type
function → contract
```

---

## 485.33 — Generic documentation

Generic API phải hiển thị:

```text id="n8p4x7"
type parameters
trait bounds
associated types
const parameters
```

---

## 485.34 — Dynamic interface documentation

`dyn Trait` phải chỉ rõ:

- object safety;
- supported methods;
- dynamic dispatch semantics.

---

## 485.35 — Inheritance-free model

Documentation không được trình bày trait implementation như class inheritance.

---

## 485.36 — Method documentation

Struct-first methods phải được hiển thị tự nhiên:

```text id="5w7m2d"
Vec2.length()
```

đồng thời giữ canonical function identity.

---

## 485.37 — Overload documentation

Nếu overload tồn tại, mỗi candidate phải có signature/constraints rõ.

---

## 485.38 — Operator documentation

Operator implementations có thể được liên kết tới underlying trait.

---

## 485.39 — Source links

API docs có thể link source nếu package cho phép.

Binary-only packages không bắt buộc cung cấp source.

---

## 485.40 — Privacy

Private implementation details không được xuất trong public docs trừ khi explicitly requested.

---

## 485.41 — Documentation visibility

Docs obey:

```text id="g1r6c8"
private
package
pub
```

visibility rules.

---

## 485.42 — Generated documentation

Compiler-generated APIs phải có provenance.

---

## 485.43 — Comptime generated API

Generated symbols có thể xuất hiện trong docs nếu public.

---

## 485.44 — Documentation provenance

Mỗi generated documentation node có thể truy ngược:

```text id="u2k7m4"
source
generator
semantic symbol
generated artifact
```

---

## 485.45 — Documentation versioning

Docs phải gắn:

```text id="w8s0q2"
package version
language edition
compiler version
```

---

## 485.46 — API version comparison

Tooling có thể diff:

```text id="v1p5r8"
old docs
vs
new docs
```

---

## 485.47 — Breaking documentation changes

API/ABI changes từ 447 có thể xuất hiện trong documentation diff.

---

## 485.48 — Search index

Documentation search index nên sử dụng semantic identifiers, không chỉ full-text.

---

## 485.49 — AI knowledge graph

Documentation có thể sinh graph:

```text id="4x8c1m"
Package
  ↓
Module
  ↓
Symbol
  ├── Type
  ├── Trait
  ├── Function
  ├── Contract
  ├── Effects
  ├── Dependencies
  └── Examples
```

---

## 485.50 — AI query

AI có thể query:

```text id="8n3w6v"
docs(symbol)
examples(symbol)
contract(symbol)
effects(symbol)
dependencies(symbol)
related_symbols(symbol)
```

---

## 485.51 — Semantic neighborhood

AI có thể lấy documentation của symbol cùng:

- callers;
- callees;
- related types;
- trait implementations;
- contracts.

---

## 485.52 — Documentation generation

AI-generated prose có thể tồn tại nhưng phải phân biệt:

```text id="s4j8q2"
normative compiler fact
generated explanation
human-authored documentation
```

---

## 485.53 — No hallucinated API

Documentation generator không được tạo API facts không tồn tại trong semantic metadata.

---

## 485.54 — Compiler facts

Compiler-generated sections như signature/type/layout/effects phải lấy từ semantic DB.

---

## 485.55 — Human prose

Human-authored descriptions có thể giải thích intent nhưng không override compiler semantics.

---

## 485.56 — Documentation lint

Có thể kiểm tra:

- broken links;
- missing docs;
- invalid references;
- stale examples;
- outdated signatures;
- undocumented unsafe API.

---

## 485.57 — Public API coverage

Project có thể yêu cầu public API documentation.

Đây là project policy, không phải language requirement.

---

## 485.58 — Example coverage

Tooling có thể xác định API nào có examples.

Không biến thành universal quality score.

---

## 485.59 — Documentation tests in CI

CI có thể chạy:

```text id="v4m8x1"
axiom test --docs
```

---

## 485.60 — Incremental docs

Chỉ regenerate documentation affected by semantic changes.

---

## 485.61 — Documentation cache

Cache key:

```text id="g2r9m5"
SymbolId
semantic_hash
doc_hash
compiler
edition
```

---

## 485.62 — Reproducible docs

Cùng semantic input phải tạo documentation deterministic, ngoại trừ explicitly dynamic metadata.

---

## 485.63 — Localization

Documentation có thể có translated prose.

Compiler-generated signatures remain canonical.

---

## 485.64 — Search localization

Search index có thể map localized terms về SymbolId.

---

## 485.65 — Documentation security

Documentation renderer phải escape untrusted content.

---

## 485.66 — Example security

Examples phải được sandboxed khi chạy trong documentation tooling.

---

## 485.67 — Dependency security

Doc tests phải sử dụng dependency lock/provenance 447.

---

## 485.68 — Offline docs

Documentation generation phải hoạt động offline nếu dependencies/docs metadata đã local.

---

## 485.69 — Package documentation

`.axpkg` có thể chứa pre-generated documentation artifacts.

---

## 485.70 — Binary documentation

Binary-only package vẫn có thể cung cấp API metadata/docs.

---

## 485.71 — Documentation API

Tooling API:

```text id="s1c8k5"
get_doc(SymbolId)
get_signature(SymbolId)
get_examples(SymbolId)
get_contracts(SymbolId)
get_related(SymbolId)
```

---

## 485.72 — IDE integration

LSP hover có thể lấy documentation model.

---

## 485.73 — AI/LSP shared source

LSP và AI tooling dùng cùng semantic documentation database.

---

## 485.74 — Hard invariants

1. Documentation là structured artifact.
2. Documentation khác source comments.
3. Language Reference là normative documentation.
4. API Reference được semantic-driven.
5. Documentation comments được hỗ trợ.
6. Structured DocItem được hỗ trợ.
7. Parameter docs gắn semantic parameter.
8. Return docs phân biệt Result/Option/panic.
9. Error docs được hỗ trợ.
10. Unsafe APIs có safety documentation.
11. Contracts có thể tự động xuất hiện.
12. Effects có thể xuất hiện.
13. Ownership semantics có thể xuất hiện.
14. ABI information có thể xuất hiện.
15. Examples là first-class artifacts.
16. Runnable examples được hỗ trợ.
17. Doc tests được hỗ trợ.
18. Compile-only examples được hỗ trợ.
19. Expected output mode explicit.
20. Output normalization không hidden.
21. Target-specific examples được hỗ trợ.
22. Feature-specific examples được hỗ trợ.
23. Doc tests isolated.
24. Network access không implicit.
25. Filesystem access controlled.
26. Nondeterministic examples cần deterministic testing khi output được verify.
27. Documentation errors là diagnostics.
28. `axiom doc` được hỗ trợ.
29. HTML/Markdown/JSON output được hỗ trợ.
30. Static documentation navigation được hỗ trợ.
31. SymbolId được dùng cho cross-reference.
32. Generic information được hiển thị.
33. Dynamic interface semantics được hiển thị.
34. Trait không được trình bày như class inheritance.
35. Struct-first methods được documentation tự nhiên.
36. Operator implementation có trait mapping.
37. Source links obey visibility.
38. Private details không leak vào public docs.
39. Generated API có provenance.
40. Documentation có version context.
41. API diff tích hợp 447.
42. Semantic search được hỗ trợ.
43. AI knowledge graph được hỗ trợ.
44. AI queries dựa trên semantic facts.
45. Human prose không override compiler facts.
46. AI-generated explanation phải phân biệt với normative fact.
47. Documentation không được hallucinate API.
48. Compiler facts lấy từ semantic DB.
49. Documentation lint được hỗ trợ.
50. Public API doc coverage là project policy.
51. Không aggregate documentation score.
52. Doc tests chạy được trong CI.
53. Incremental documentation được hỗ trợ.
54. Documentation cache semantic-based.
55. Documentation generation deterministic.
56. Localization được hỗ trợ.
57. Localized docs không thay canonical signatures.
58. Documentation renderer phải chống injection.
59. Examples được sandbox khi chạy.
60. Doc-test dependencies tuân supply-chain rules.
61. Offline docs được hỗ trợ.
62. Package có thể chứa docs.
63. Binary package có thể chứa API docs.
64. Documentation API được expose.
65. LSP và AI có thể dùng cùng documentation DB.
66. **Axiom documentation phải vừa là tài liệu dễ đọc cho con người vừa là semantic knowledge base có thể truy vấn chính xác bởi compiler, IDE và AI, trong đó compiler facts không thể bị prose hoặc AI-generated text ghi đè.**

**BOOTSTRAP-485 hoàn tất / LOCKED.**

---

# BOOTSTRAP-486 — SOURCE CONTROL INTEGRATION, PROJECT HISTORY, CHANGE IMPACT, REFACTORING & SEMANTIC CODE TRANSFORMATION

486 định nghĩa lớp tooling để Axiom hiểu **thay đổi code theo semantic**, thay vì chỉ coi source là text.

Kiến trúc:

```text id="9m5r2x"
                    Source Repository
                           │
                    File / Revision
                           │
                    Semantic Snapshot
                           │
             ┌─────────────┼─────────────┐
             ↓             ↓             ↓
        Change Graph    API Diff      Impact Analysis
             │             │             │
             └─────────────┼─────────────┘
                           ↓
                 Semantic Refactoring
                           │
                    ┌──────┴──────┐
                    ↓             ↓
                  Patch        Validation
                                  │
                         Check → Test → Build
```

## 486.1 — Text diff ≠ semantic diff

Git/text diff trả lời:

> dòng nào thay đổi?

Semantic diff trả lời:

> program meaning nào thay đổi?

Axiom cần cả hai.

---

## 486.2 — Revision identity

Mỗi source snapshot có:

```text id="x6p3n8"
Repository
Revision
FileId
ContentHash
```

---

## 486.3 — Semantic snapshot

Snapshot gồm:

```text id="4k9s2m"
symbols
types
traits
dependencies
contracts
effects
ABI
layouts
call graph
```

---

## 486.4 — Change classification

Changes được phân loại:

```text id="z7f1w4"
text-only
documentation
internal implementation
API
ABI
semantic
behavioral-risk
build/dependency
```

---

## 486.5 — Symbol rename

Semantic rename phải dựa trên SymbolId.

Không dùng text replacement mù.

---

## 486.6 — Rename safety

Rename phải cập nhật:

- declarations;
- references;
- imports;
- docs;
- examples;
- generated references.

---

## 486.7 — Shadowing

Tool phải tránh đổi identifier thành tên gây shadowing/ambiguity.

---

## 486.8 — Type rename

Type rename phải update type references và relevant metadata.

---

## 486.9 — Signature change

Nếu:

```text id="f8m2q6"
fn foo(x: i32) -> i32
```

thành:

```text id="w4r9s1"
fn foo(x: i64) -> i32
```

tool phải xác định affected callers.

---

## 486.10 — Call-site migration

Có thể tạo patch cho callers nhưng phải compile-check trước khi apply final patch.

---

## 486.11 — Trait migration

Changing trait bounds phải tìm:

```text id="2q7v8m"
implementations
call sites
generic instantiations
dyn Trait consumers
```

---

## 486.12 — Struct field migration

Adding/removing/renaming field phải phân tích:

- constructors;
- literals;
- field access;
- serialization;
- FFI;
- `repr(C)` ABI.

---

## 486.13 — ABI-sensitive change

Nếu `@repr(C)` struct thay đổi layout, tooling phải flag ABI impact.

---

## 486.14 — Contract change

479 contract changes phải được semantic diff.

---

## 486.15 — Effect change

Ví dụ:

```text id="u7s3k5"
@no_alloc
```

bị mất có thể affect callers/tooling.

---

## 486.16 — Ownership change

Thay:

```text id="j1r8w2"
borrowed
```

thành:

```text id="p4c9x7"
owned
```

là API semantic change.

---

## 486.17 — Concurrency change

Changing `Send`/`Share` or synchronization requirements phải được impact-analyzed.

---

## 48618 — Realtime change

Adding/removing `@realtime`, `@no_block`, `@no_alloc` phải được tracked.

---

## 486.19 — Unsafe boundary change

Moving API into/out of `unsafe` context phải là high-visibility semantic change.

---

## 486.20 — Refactoring engine

Canonical refactoring operations:

```text id="5g8n2p"
rename
move symbol
extract function
inline function
extract type
change signature
introduce trait
implement trait
convert API
```

---

## 486.21 — Extract function

Compiler phải đảm bảo:

- captured values;
- ownership;
- return paths;
- contracts;
- effects.

---

## 486.22 — Inline refactoring

Inline source transformation khác compiler optimization.

Refactoring thay source.

Optimizer thay generated program.

---

## 486.23 — Move symbol

Moving function/type/module phải update imports and references semantically.

---

## 486.24 — Import cleanup

Unused imports có thể được removed automatically nếu semantics không đổi.

---

## 486.25 — AST-aware transformation

Transformation phải operate trên syntax/semantic trees, không regex.

---

## 486.26 — Formatting

Sau semantic transformation:

```text id="c7m1x9"
transform
→ format
→ parse
→ semantic check
```

---

## 486.27 — Transactional edits

Mọi semantic refactoring nên có transaction:

```text id="h4q8s2"
prepare
→ preview
→ validate
→ commit
```

---

## 486.28 — Preview

Tool phải có khả năng hiển thị patch trước khi commit.

---

## 486.29 — Rollback

Nếu validation thất bại, source không được commit một phần.

---

## 486.30 — Validation pipeline

```text id="t8m4y1"
Patch
 ↓
Parse
 ↓
Resolve
 ↓
Typecheck
 ↓
Ownership
 ↓
Contracts
 ↓
Static Analysis
 ↓
Tests
```

---

## 486.31 — Build validation

Project có thể yêu cầu full build trước commit.

---

## 486.32 — Test impact analysis

Semantic graph có thể xác định tests có khả năng bị ảnh hưởng.

---

## 486.33 — Dependency impact

Change graph:

```text id="b3n6r8"
Changed Symbol
      ↓
References
      ↓
Callers
      ↓
Dependent Modules
      ↓
Affected Packages
```

---

## 486.34 — Reverse dependency

Có thể query:

```text id="z1x7c5"
who depends on this symbol?
```

---

## 486.35 — Forward dependency

```text id="s6p2k4"
what does this symbol depend on?
```

---

## 486.36 — API impact

Tool có thể báo:

```text id="r9m3w8"
public API affected
```

---

## 486.37 — ABI impact

447/421 ABI analyzer xác định binary compatibility consequences.

---

## 486.38 — Runtime impact

Semantic change có thể map tới:

- allocator;
- synchronization;
- IO;
- GPU;
- audio;
- media.

---

## 486.39 — Documentation impact

485 links phải được cập nhật khi symbol changes.

---

## 486.40 — Generated code impact

Comptime/generated artifacts phải được invalidated/rebuilt theo dependency graph.

---

## 486.41 — Cache invalidation

Semantic hash determines affected compiler queries.

---

## 486.42 — Minimal rebuild

Only affected units should rebuild when possible.

---

## 486.43 — Source-control integration

CLI có thể đọc repository state nhưng không cần trở thành full VCS.

---

## 486.44 — VCS independence

Axiom tooling không được yêu cầu Git để compile.

---

## 486.45 — Git integration

Git có thể là optional integration:

```text id="j8w5v2"
axiom diff
axiom status
axiom blame
```

nếu provider tồn tại.

---

## 486.46 — Blame semantics

Blame vẫn thuộc VCS.

Axiom chỉ có thể map revision → SymbolId/source region.

---

## 486.47 — Change provenance

Semantic item có thể lưu:

```text id="q3n7x6"
introduced_revision
modified_revision
generator
```

nếu repository metadata được cung cấp.

---

## 486.48 — AI change analysis

AI có thể query:

```text id="m5r1z8"
impact(change)
affected_symbols(change)
affected_tests(change)
abi_risk(change)
contract_risk(change)
unsafe_impact(change)
```

---

## 486.49 — AI patch generation

AI có thể tạo semantic patch nhưng phải đi qua compiler transaction.

---

## 486.50 — No direct silent mutation

AI/tooling không được sửa source trực tiếp mà bỏ qua validation layer nếu sử dụng semantic refactoring API.

---

## 486.51 — Patch confidence

Tool có thể report evidence:

```text id="w2c8n5"
parse_pass
typecheck_pass
ownership_pass
test_pass
```

Không tạo aggregate quality score.

---

## 486.52 — Merge assistance

Semantic conflict detection có thể phát hiện:

```text id="y7p4m1"
same symbol changed differently
trait contract conflict
ABI conflict
struct layout conflict
```

---

## 486.53 — Text merge remains available

Semantic merge không thay thế text merge trong mọi trường hợp.

---

## 486.54 — Generated files

Generated files nên được phân biệt:

```text id="k9w2r6"
source
generated
derived
cache
```

---

## 486.55 — Generated source provenance

Generated source phải map về generator/input.

---

## 486.56 — Comptime provenance

431-generated declarations phải có origin metadata.

---

## 486.57 — Migration tooling

484 edition migrations sử dụng semantic transformation engine 486.

---

## 486.58 — API migration

447 package/API migration cũng sử dụng semantic refactoring.

---

## 486.59 — Documentation migration

485 documentation references được update cùng symbol changes.

---

## 486.60 — LSP integration

LSP refactor commands dùng cùng semantic engine.

---

## 486.61 — IDE integration

IDE có thể request:

```text id="v8k3s0"
prepare_refactor
preview_refactor
apply_refactor
```

---

## 486.62 — Snapshot isolation

Refactoring phải operate trên compiler snapshot để tránh race với concurrent edits.

---

## 486.63 — Conflict detection

Nếu source thay đổi giữa preview và commit:

```text id="n1r5q7"
commit rejected
```

và patch phải được recomputed.

---

## 486.64 — Formatting determinism

Final source phải pass formatter 429.

---

## 486.65 — Semantic equivalence

Refactoring claim:

```text id="p6x2m8"
semantics-preserving
```

chỉ được đưa ra khi compiler/tooling có evidence phù hợp.

---

## 486.66 — Optimization equivalence

Không được dùng runtime benchmark để tuyên bố semantic equivalence.

---

## 486.67 — Test evidence

Tests tăng confidence nhưng không phải formal proof.

---

## 486.68 — Formal proof

Nếu external verifier cung cấp proof, metadata có thể lưu proof provenance.

---

## 486.69 — Static analyzer evidence

478 findings có thể trở thành change-impact evidence.

---

## 486.70 — Coverage evidence

477 có thể cho biết changed code có test coverage nào.

---

## 486.71 — Performance evidence

450/481 có thể cho biết change ảnh hưởng benchmark nào.

---

## 486.72 — Security evidence

445/480 có thể cho biết change ảnh hưởng unsafe/sanitizer/security surfaces.

---

## 486.73 — AI knowledge graph

486 mở rộng graph:

```text id="j6m3q8"
Revision
 ↓
Change
 ↓
Symbol
 ↓
Dependency
 ↓
Contract
 ↓
Test
 ↓
Profile
 ↓
Artifact
```

---

## 486.74 — Hard invariants

1. Text diff khác semantic diff.
2. Revision identity được hỗ trợ.
3. Semantic snapshots được hỗ trợ.
4. Changes được classify.
5. Rename dùng SymbolId.
6. Rename cập nhật references.
7. Rename phải tránh shadowing.
8. Type rename semantic-safe.
9. Signature changes có impact analysis.
10. Call-site migration được hỗ trợ.
11. Trait migration được phân tích.
12. Struct field changes được phân tích.
13. ABI-sensitive layout changes được detect.
14. Contract changes được track.
15. Effect changes được track.
16. Ownership changes được track.
17. Concurrency changes được track.
18. Realtime constraints được track.
19. Unsafe boundary changes được track.
20. Semantic refactoring engine được hỗ trợ.
21. Extract-function phải giữ ownership semantics.
22. Inline refactoring khác compiler optimization.
23. Move-symbol cập nhật imports.
24. AST/semantic transformation thay regex.
25. Refactoring có transaction.
26. Refactoring có preview.
27. Refactoring có rollback.
28. Validation pipeline được thực hiện.
29. Build validation có thể được yêu cầu.
30. Test impact analysis được hỗ trợ.
31. Dependency impact được hỗ trợ.
32. Reverse dependency query được hỗ trợ.
33. Forward dependency query được hỗ trợ.
34. API impact được phân tích.
35. ABI impact được phân tích.
36. Runtime impact metadata có thể được truy vấn.
37. Documentation impact được phân tích.
38. Generated code impact được tính.
39. Cache invalidation dựa semantic dependencies.
40. Minimal rebuild được hỗ trợ.
41. Compilation không phụ thuộc VCS.
42. Git/VCS integration là optional.
43. Blame vẫn thuộc VCS.
44. Change provenance có thể được lưu.
45. AI có thể query impact.
46. AI-generated patches phải qua validation.
47. Semantic mutation không được silently bypass compiler transaction.
48. Validation evidence được machine-readable.
49. Không aggregate patch quality score.
50. Semantic conflict detection được hỗ trợ.
51. Text merge vẫn được hỗ trợ.
52. Generated source được phân loại.
53. Generated source có provenance.
54. Comptime provenance được giữ.
55. Edition migration dùng semantic transformation.
56. API migration dùng semantic transformation.
57. Documentation migration được hỗ trợ.
58. LSP dùng semantic refactoring engine.
59. IDE có transactional refactoring.
60. Snapshot isolation được hỗ trợ.
61. Concurrent source changes phải detect.
62. Formatter được chạy sau transformation.
63. Semantic-preserving claim cần evidence.
64. Benchmark không phải semantic proof.
65. Tests không phải formal proof.
66. External proof có thể được ghi provenance.
67. Static-analysis evidence được liên kết.
68. Coverage evidence được liên kết.
69. Performance evidence được liên kết.
70. Security/sanitizer evidence được liên kết.
71. AI knowledge graph nối revision → change → symbol → dependency → test → artifact.
72. Refactoring không yêu cầu GC.
73. Refactoring không yêu cầu borrow checker.
74. Refactoring không yêu cầu Git.
75. **Axiom semantic transformation system phải biến refactoring từ thao tác text thành thao tác trên program model, có preview, transaction, validation, provenance và impact analysis; mọi claim về tính tương đương phải được phân biệt rõ giữa compiler proof, static evidence, test evidence và empirical evidence.**

**BOOTSTRAP-486 hoàn tất / LOCKED.**

---

## Chuỗi đã tiến tới

```text
479  Contracts / Design-by-Contract          LOCKED
480  Sanitizers / Runtime Validation         LOCKED
481  Profiling / Tracing                     LOCKED
482  Self-hosting / Bootstrap Trust          LOCKED
483  Toolchain / Cross Compilation            LOCKED
484  Language Evolution / Editions            LOCKED
485  Documentation / Knowledge Graph         LOCKED
486  Semantic Refactoring / Change Impact    LOCKED
```

**Task tiếp theo: `BOOTSTRAP-487 — BUILD GRAPH 2.0, INCREMENTAL COMPILATION, DISTRIBUTED CACHE, REMOTE EXECUTION & HERMETIC BUILDS`.**