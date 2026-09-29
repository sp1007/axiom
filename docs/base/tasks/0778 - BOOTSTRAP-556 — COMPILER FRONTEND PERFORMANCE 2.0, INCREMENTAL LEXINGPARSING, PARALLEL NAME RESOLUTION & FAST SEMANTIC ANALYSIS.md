# BOOTSTRAP-556 — COMPILER FRONTEND PERFORMANCE 2.0, INCREMENTAL LEXING/PARSING, PARALLEL NAME RESOLUTION & FAST SEMANTIC ANALYSIS

**Trạng thái: COMPLETED / LOCKED**

`556` khóa kiến trúc frontend hiệu năng cao cho Axiom. Nó nối trực tiếp:

- `436` — Compiler Architecture
- `429` — Lexical/Syntax
- `430` — Type System
- `446` — Semantic Metadata
- `487` — Incremental Build Graph
- `554` — Compiler cache/query identity
- `555` — Compiler Daemon

Mục tiêu chính:

> **Một thay đổi nhỏ trong source chỉ làm compiler xử lý lại vùng syntax và semantic thực sự bị ảnh hưởng, thay vì mặc định lex/parse/typecheck lại toàn bộ file hoặc project.**

---

## 556.1. Frontend architecture

```text
                    SourceSnapshot
                          │
                          ▼
                  Incremental Lexer
                          │
                    Token Chunks
                          │
                          ▼
                 Incremental Parser
                          │
                    Green Syntax Tree
                          │
                          ▼
                 Semantic/Red Layer
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         Name Index     Scope DB    Syntax DB
              │           │           │
              └───────────┼───────────┘
                          ▼
                  Incremental HIR
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
         Type Query    Trait Query   Effect Query
             │            │            │
             └────────────┼────────────┘
                          ▼
                    Semantic DB
                          │
                          ▼
                       MIR
```

---

# 556.2. Core principle

Frontend phải phân biệt:

```text
text change
syntax change
semantic change
interface change
ABI change
```

Không được coi tất cả đều tương đương.

---

# 556.3. Incremental compilation unit

Đơn vị nhỏ nhất có thể cache:

```text
TokenChunk
SyntaxNode
Scope
Declaration
Expression
TypeQuery
TraitQuery
HIRNode
```

tùy dependency.

---

# 556.4. Token chunk

Lexer chia source thành các vùng:

```text
TokenChunk {
    chunk_id
    byte_start
    byte_end
    token_hash
    lexer_state_in
    lexer_state_out
}
```

---

# 556.5. Lexer state

Lexer state phải đủ biểu diễn trạng thái ảnh hưởng tokenization:

- string mode;
- raw string mode;
- comment mode;
- escape state;
- delimiter nesting nếu cần;
- lexical feature mode.

---

# 556.6. Chunk boundary

Boundary không được cắt giữa một lexical construct đang ảnh hưởng tokenization.

---

# 556.7. Stable unchanged chunks

Nếu source edit không ảnh hưởng chunk:

```text
old chunk
    ↓
reuse
```

---

# 556.8. Change propagation

```text
EditedChunk
   ↓
relex
   ↓
compare output state
   ↓
unchanged?
 ┌─┴─┐
yes no
 │   │
stop continue
```

---

# 556.9. Lexer convergence

Nếu lexer state và token sequence trở lại giống phiên bản cũ tại boundary:

```text
converged
```

các chunk phía sau có thể reuse.

---

# 556.10. Example

Nếu sửa:

```text
let x = 10
```

thành:

```text
let x = 11
```

lexer không cần relex toàn file.

---

# 556.11. UTF-8

Lexer hoạt động trên byte source nhưng phải validate UTF-8 theo `429/464`.

---

# 556.12. Invalid UTF-8

IDE mode có thể tạo diagnostic/recovery token.

Build mode phải reject source không hợp lệ.

---

# 556.13. Unicode identifier

Identifier token phải preserve:

```text
raw bytes
normalized form
source span
```

nếu normalization được áp dụng.

---

# 556.14. Unicode normalization

Compiler phải xác định rõ normalization policy trước khi token identity được tính.

Không được để host OS quyết định normalization.

---

# 556.15. Token identity

```text
TokenIdentity =
    kind
    normalized_value
    lexical_flags
```

Source location không thuộc semantic identity.

---

# 556.16. Trivia

Whitespace/comment có thể được giữ trong syntax tree để formatter/IDE nhưng không được làm thay đổi semantic identity.

---

# 556.17. Comment-only edit

Thay đổi comment không được trigger semantic re-analysis nếu không ảnh hưởng:

- documentation metadata;
- attributes;
- doc tests;
- source mapping policy.

---

# 556.18. Documentation dependency

Nếu comment là doc comment:

```text
doc change
```

chỉ invalidate documentation-related queries.

---

# 556.19. Incremental parser

Parser phải hỗ trợ reparse subtree thay vì toàn compilation unit.

---

# 556.20. Green tree

Syntax tree dùng immutable green nodes:

```text
GreenNode {
    kind
    children[]
    width
    hash
}
```

---

# 556.21. Green node immutability

Green node đã publish không được mutate.

---

# 556.22. Structural sharing

```text
Old Tree
 ├── A
 ├── B
 └── C

New Tree
 ├── A   ← reused
 ├── B'  ← changed
 └── C   ← reused
```

---

# 556.23. Node hash

Hash dùng để nhận diện structural equality.

Hash collision không được trở thành bằng chứng semantic equality.

---

# 556.24. Hash verification

Khi correctness quan trọng, equality phải được xác nhận bằng structure/content nếu cần.

---

# 556.25. Red tree

Red layer cung cấp:

```text
parent
position
semantic context
source span
```

trên green tree.

---

# 556.26. Red nodes không cần persistent identity

Red nodes có thể được tạo lại nhẹ nhàng.

---

# 556.27. Syntax identity

Green node identity phục vụ structural reuse.

Semantic identity vẫn dùng:

```text
SymbolId
TypeId
```

---

# 556.28. Parse boundary

Parser phải xác định các recovery/reparse boundaries:

- declaration;
- statement;
- expression;
- block;
- item;
- module.

---

# 556.29. Reparse strategy

Khi edit:

```text
smallest enclosing reparsable node
```

được chọn trước.

---

# 556.30. Reparse escalation

Nếu subtree không parse được:

```text
expression
 ↓
statement
 ↓
block
 ↓
declaration
 ↓
module
```

có thể escalate.

---

# 556.31. Whole-file reparse

Chỉ dùng khi incremental boundary không thể đảm bảo correctness.

---

# 556.32. Correctness over speed

Nếu compiler không chắc subtree reuse an toàn:

```text
invalidate
→ reparse larger region
```

Không được reuse speculative syntax một cách không an toàn.

---

# 556.33. Error recovery tree

IDE parser tạo recovery nodes:

```text
MissingToken
UnexpectedToken
SkippedTokens
SyntheticNode
```

---

# 556.34. Recovery node

Recovery node phải được đánh dấu synthetic.

---

# 556.35. Synthetic source

Synthetic nodes không được coi là source declaration thật.

---

# 556.36. IDE incomplete code

Ví dụ:

```text
fn foo(
```

phải có thể tạo syntax tree tạm thời để hỗ trợ completion.

---

# 556.37. Build parser

Build artifact chỉ được tạo từ fully valid syntax/semantic state.

---

# 556.38. Parser determinism

Cùng:

```text
source
edition
language features
```

phải tạo cùng syntax semantics.

---

# 556.39. Grammar ambiguity

Axiom grammar phải có deterministic parse policy.

---

# 556.40. Pratt parser integration

Expression parser từ `429` dùng Pratt/precedence table nhưng phải hỗ trợ incremental subtree boundaries.

---

# 556.41. Parser cache key

```text
ParseKey {
    syntax_hash
    grammar_version
    edition
    feature_set
}
```

---

# 556.42. Grammar change invalidation

Grammar/compiler edition thay đổi:

```text
invalidate affected parse cache
```

---

# 556.43. Syntax feature gate

Feature flag thay đổi phải được đưa vào parser identity khi ảnh hưởng grammar.

---

# 556.44. Name resolution index

Frontend xây:

```text
NameIndex
```

theo:

```text
module
scope
symbol
```

---

# 556.45. Declaration-first pass

Một module có thể xử lý:

```text
declarations
```

trước:

```text
bodies
```

---

# 556.46. Interface extraction

Module interface:

```text
public symbols
public types
public traits
public constants
ABI-relevant metadata
```

được tách khỏi implementation.

---

# 556.47. Fast dependency checking

Consumer module chỉ cần interface fingerprint của dependency nếu implementation không leak semantic dependency.

---

# 556.48. Interface fingerprint

```text
InterfaceFingerprint =
    exported_symbol_signatures
    + visibility
    + public trait contracts
    + ABI metadata
    + relevant attributes
```

---

# 556.49. Private change

Private implementation thay đổi nhưng interface không đổi:

```text
consumer semantic cache → reusable
```

---

# 556.50. Public signature change

Public signature thay đổi:

```text
dependent semantic queries → invalidate
```

---

# 556.51. Public type layout change

Nếu type layout public/ABI-visible thay đổi:

```text
ABI/layout dependents → invalidate
```

---

# 556.52. Private type layout

Nếu hoàn toàn private và không escape boundary:

```text
external consumers
```

không cần invalidate.

---

# 556.53. Name lookup cache

```text
ResolveKey {
    scope
    name
    namespace
    visibility_context
}
```

---

# 556.54. Scope fingerprint

Scope fingerprint bao gồm những declarations ảnh hưởng lookup.

---

# 556.55. Shadowing

Thêm:

```text
let x
```

phải invalidate lookup chỉ ở scope bị shadow và descendants phù hợp.

---

# 556.56. Import changes

Thêm/xóa import phải invalidate name resolution trong module liên quan.

---

# 556.57. Re-export changes

Re-export thay đổi có thể invalidate downstream modules.

---

# 556.58. Glob import

Nếu Axiom hỗ trợ glob import, dependency impact phải conservatively track.

---

# 556.59. Namespace separation

Lookup phải phân biệt namespace:

```text
type
value
trait
module
macro/generator
```

nếu từng namespace tồn tại.

---

# 556.60. Overload index

Nếu function overloading tồn tại trong namespace phù hợp, compiler phải duy trì candidate index.

---

# 556.61. Method lookup

Struct-first method model:

```text
fn length(self: Vec2)
```

được index theo receiver type.

---

# 556.62. Extension method lookup

Trait/impl method candidates được index theo:

```text
receiver type
trait constraints
visibility
```

---

# 556.63. Method invalidation

Thêm một impl có thể invalidate method-resolution queries liên quan.

---

# 556.64. Coherence integration

`426` coherence/orphan rules phải là dependency của trait lookup cache.

---

# 556.65. Generic declaration cache

Generic signature được cache độc lập với từng instantiation.

---

# 556.66. Generic body cache

Body semantic result có thể reuse giữa các instantiation nếu generic analysis cho phép.

---

# 556.67. Monomorphization separation

Type checking generic definition không đồng nghĩa với native monomorphization.

---

# 556.68. Type query cache

```text
TypeOf(ExpressionId, ExpectedTypeContext)
```

có thể memoize.

---

# 556.69. Expected type dependency

Nếu expected type thay đổi:

```text
type query
```

phải invalidate.

---

# 556.70. No global type invalidation

Một expression thay đổi không được mặc định invalidate toàn module type checking.

---

# 556.71. Bidirectional typing

Incremental engine phải preserve:

```text
synthesized type
vs
expected type
```

context.

---

# 556.72. Coercion query

Implicit coercion candidate phải có cache identity chứa relevant source/target types.

---

# 556.73. Trait solver query

Trait solving sử dụng canonical query:

```text
Goal
+ environment
+ impl universe
```

---

# 556.74. Trait cache invalidation

Thay đổi impl set phải invalidate những goals có thể affected.

---

# 556.75. Negative reasoning

Compiler không được cache:

```text
TraitNotImplemented
```

vĩnh viễn nếu impl universe còn thay đổi.

---

# 556.76. Closed-world boundary

Sau khi module/package boundary được đóng, negative result có thể cache theo interface fingerprint.

---

# 556.77. Type layout query

```text
LayoutOf(TypeId, TargetSpec)
```

là target-dependent.

---

# 556.78. Layout cache

Cache key phải bao gồm:

```text
type
target
ABI
repr
feature set
```

---

# 556.79. Const evaluation

Comptime result cache từ `431/554`.

---

# 556.80. Const dependency

Nếu comptime input không đổi:

```text
reuse
```

---

# 556.81. Effect analysis

Effects:

```text
alloc
block
panic
unsafe
io
```

có thể được incremental hóa theo function body.

---

# 556.82. Effect propagation

Thay đổi effect của function có thể invalidate callers nếu caller analysis phụ thuộc effect.

---

# 556.83. Ownership analysis

Ownership flow chỉ cần rerun vùng MIR affected.

---

# 556.84. HIR generation

HIR node phải giữ provenance về syntax node.

---

# 556.85. HIR identity

Semantic HIR identity không được phụ thuộc byte offset.

---

# 556.86. Source edit before node

Chèn text trước một function không được khiến semantic identity của mọi function sau đó bắt buộc đổi.

---

# 556.87. Symbol identity preservation

Compiler có thể preserve `SymbolId` dựa trên declaration identity/evidence.

---

# 556.88. Symbol identity ambiguity

Nếu không xác định chắc:

```text
new SymbolId
```

thay vì đoán.

---

# 556.89. Semantic diff

Frontend phải cung cấp:

```text
AddedSymbol
RemovedSymbol
ChangedSignature
ChangedVisibility
ChangedType
ChangedTraitImpl
ChangedBody
ChangedAttribute
```

---

# 556.90. Semantic impact

Impact engine từ `486/487` dùng semantic diff để xác định invalidation.

---

# 556.91. Parallel lexing

Independent files có thể lex song song.

---

# 556.92. Parallel parsing

Independent modules/files có thể parse song song.

---

# 556.93. Intra-file parallelism

Có thể parse independent top-level regions song song sau khi lexical boundaries đã xác định.

---

# 556.94. Dependency-aware parallel name resolution

Name resolution có thể song song theo module SCC.

---

# 556.95. Import SCC

Module graph:

```text
A → B
B → C
C → A
```

phải được xử lý theo SCC semantics đã khóa ở `432`.

---

# 556.96. Parallel SCC processing

Các SCC độc lập có thể resolve song song.

---

# 556.97. Deterministic merge

Parallel result merge phải deterministic.

---

# 556.98. No scheduler-dependent semantics

Thread scheduling không được ảnh hưởng symbol/type result.

---

# 556.99. Query parallelism

Query engine từ `436/555` có thể evaluate independent queries concurrently.

---

# 556.100. Query deduplication

Nếu nhiều consumers cần cùng query:

```text
one computation
```

---

# 556.101. Frontend worker pool

Daemon có thể sử dụng worker pool:

```text
Lexer workers
Parser workers
Semantic workers
```

nhưng đây là implementation detail.

---

# 556.102. CPU affinity

Frontend không được tự ý pin CPU trừ policy/performance mode.

---

# 556.103. Memory locality

Syntax nodes nên được tổ chức để giảm pointer chasing.

---

# 556.104. Arena allocation

Compiler internal syntax/semantic nodes có thể dùng arenas.

---

# 556.105. Arena lifetime

Arena phải gắn snapshot/query generation.

---

# 556.106. Arena reclamation

Khi snapshot/query không còn referenced:

```text
arena → reclaim
```

---

# 556.107. No semantic dangling

Reclaim memory không được invalidate persistent semantic identity.

---

# 556.108. Green tree persistence

Green nodes có thể shared giữa snapshots.

---

# 556.109. Reference counting vs arena

Implementation được phép dùng:

```text
RC
arena
generational arena
persistent tree
```

miễn semantics không phụ thuộc strategy.

---

# 556.110. Hash-consing

Có thể hash-cons immutable green nodes để tăng reuse.

---

# 556.111. Hash-consing correctness

Hash collision không được merge structurally different nodes.

---

# 556.112. Interning

Strings/identifiers có thể intern trong compiler session.

---

# 556.113. Interning lifetime

Interned data phải có lifecycle bounded hoặc GC-independent reclamation strategy.

---

# 556.114. No language GC implication

Compiler có thể dùng memory-management techniques riêng; điều này không thay đổi Axiom runtime memory model.

---

# 556.115. Parser performance budget

Interactive parse latency phải được đo riêng khỏi full build.

---

# 556.116. Semantic performance budget

Đo riêng:

```text
lex
parse
resolve
typecheck
trait
HIR
```

---

# 556.117. Cold frontend benchmark

Compiler từ filesystem/cache sạch.

---

# 556.118. Warm frontend benchmark

Compiler daemon với query cache nóng.

---

# 556.119. Single-edit benchmark

Đo:

```text
1 character edit
```

trên project lớn.

---

# 556.120. Signature-edit benchmark

Đo public API change và downstream invalidation.

---

# 556.121. Comment-edit benchmark

Comment-only edit phải gần như không có semantic recomputation.

---

# 556.122. Large-file benchmark

File hàng trăm nghìn dòng phải không biến một local edit thành toàn-project parse mặc định.

---

# 556.123. Unicode benchmark

Vietnamese, CJK, emoji, combining marks, bidi-sensitive source phải được test.

---

# 556.124. Deep nesting benchmark

Parser phải chịu được nesting sâu mà không stack overflow ngoài giới hạn policy.

---

# 556.125. Malformed source benchmark

Recovery parser phải xử lý source lỗi mà không quadratic blow-up không kiểm soát.

---

# 556.126. Incremental parser complexity

Mục tiêu thực tế:

```text
O(changed_region + affected_context)
```

thay vì:

```text
O(entire_file)
```

khi change local.

---

# 556.127. Worst-case fallback

Compiler vẫn được phép:

```text
O(file)
```

hoặc lớn hơn khi change phá lexical/grammar boundary rộng.

Không được hy sinh correctness để giữ asymptotic đẹp.

---

# 556.128. Quadratic prevention

Lexer/parser phải tránh repeated rescanning cùng source region.

---

# 556.129. Parser stack

Có thể dùng explicit stack cho grammar recursion sâu.

---

# 556.130. Token stream random access

Parser phải có efficient indexed access tới token chunks.

---

# 556.131. Token rope

Implementation có thể dùng:

```text
token rope
piece table
persistent vector
```

---

# 556.132. Source text rope

Editor snapshot có thể dùng piece table/rope để tránh copy toàn file mỗi edit.

---

# 556.133. Source storage abstraction

Compiler không phụ thuộc editor data structure.

---

# 556.134. Text version

Mỗi source document phải có monotonic document version trong interactive session.

---

# 556.135. Content identity

Document version khác content hash.

---

# 556.136. Version ≠ semantic identity

Version tăng dù comment-only edit.

---

# 556.137. Content hash

Content hash dùng cache identity.

---

# 556.138. Semantic hash

Semantic hash bỏ qua những textual changes không ảnh hưởng semantics.

---

# 556.139. Interface hash

Interface hash chỉ phản ánh public contract relevant tới consumers.

---

# 556.140. ABI hash

ABI hash phản ánh layout/calling-convention/linkage relevant.

---

# 556.141. Four fingerprints

```text
TextHash
SyntaxHash
SemanticHash
InterfaceHash
ABIHash
```

phải được phân biệt.

---

# 556.142. Fingerprint hierarchy

```text
Text
 ↓
Syntax
 ↓
Semantic
 ↓
Interface
 ↓
ABI
```

Không phải mọi thay đổi ở tầng trên đều imply thay đổi tầng dưới.

---

# 556.143. Documentation fingerprint

Có thể có:

```text
DocHash
```

độc lập.

---

# 556.144. Test fingerprint

Doc tests/test generation có thể có fingerprint riêng.

---

# 556.145. Build invalidation matrix

Compiler phải có bảng:

```text
Change
→ invalidates
```

thay vì logic rải rác trong code.

---

# 556.146. Invalidation rule

Ví dụ:

```text
private body
    → local HIR/MIR/codegen

public body without contract/interface change
    → implementation dependents only

public signature
    → semantic dependents

ABI layout
    → ABI dependents

toolchain
    → compiler-dependent artifacts
```

---

# 556.147. Conservative invalidation

Nếu không biết impact:

```text
invalidate larger region
```

---

# 556.148. Unsound reuse forbidden

Không được giữ cache chỉ để nhanh nếu dependency analysis chưa chứng minh reusable.

---

# 556.149. Invalidation provenance

Mỗi invalidation nên có reason:

```text
DependencyChanged
SignatureChanged
TraitSetChanged
TargetChanged
ConfigurationChanged
ToolchainChanged
```

---

# 556.150. Why invalidated

AI/IDE có thể query:

```text
why_invalidated(QueryId)
```

---

# 556.151. Incremental semantic database

Database từ `436/554` lưu:

```text
query key
inputs
dependencies
result
fingerprints
provenance
```

---

# 556.152. Snapshot-aware query key

Query identity phải include snapshot-independent semantic fingerprints hoặc snapshot identity khi cần.

---

# 556.153. Cross-snapshot reuse

Result từ S1 có thể reuse trong S2 nếu:

```text
all semantic dependencies equivalent
```

---

# 556.154. Snapshot ID alone

Snapshot ID không nhất thiết phải khiến toàn bộ cache invalid nếu underlying content unchanged.

---

# 556.155. Semantic equivalence

Compiler có thể reuse cross-snapshot result nếu dependency fingerprints chứng minh equivalence.

---

# 556.156. Query invalidation transaction

Invalidation và snapshot publish phải atomic ở semantic DB boundary.

---

# 556.157. Failed update

Nếu semantic update fail:

```text
old valid snapshot state
```

vẫn phải tồn tại.

---

# 556.158. IDE resilience

Compiler error không được làm mất semantic state của previous valid snapshot.

---

# 556.159. Best-effort IDE semantics

IDE có thể sử dụng:

```text
previous valid semantics
+
current recovery syntax
```

nhưng phải đánh dấu stale/approximate.

---

# 556.160. Approximate result

AI/IDE result phải distinguish:

```text
CurrentExact
CurrentRecovered
PreviousSnapshot
Speculative
Unknown
```

---

# 556.161. No silent stale semantics

Không được trả previous result như current result mà không metadata.

---

# 556.162. Semantic completion

Completion có thể kết hợp:

```text
current syntax
previous semantic index
```

---

# 556.163. Error tolerance

Một syntax error ở function A không được làm mất completion của function B nếu B semantic state vẫn recoverable.

---

# 556.164. Error isolation

Compiler phải isolate semantic errors càng local càng tốt.

---

# 556.165. Error cascades

Diagnostic engine phải deduplicate cascading errors.

---

# 556.166. Root diagnostic

Có thể đánh dấu:

```text
Primary
Derived
Suppressed
```

---

# 556.167. Diagnostic dependency graph

Cho phép IDE chỉ hiển thị root errors mặc định nếu cascade quá lớn.

---

# 556.168. Parallel diagnostics

Independent diagnostic queries có thể chạy song song.

---

# 556.169. Deterministic diagnostic order

Output order phải stable:

```text
source position
severity
diagnostic code
stable identity
```

---

# 556.170. Formatter integration

Formatter dùng syntax tree nhưng không được mutate compiler semantic tree.

---

# 556.171. Formatting-only edit

Formatter output phải tạo source snapshot mới và đi qua incremental pipeline bình thường.

---

# 556.172. Formatter idempotence

Đã khóa ở `429`:

```text
fmt(fmt(source)) == fmt(source)
```

---

# 556.173. Source maps

Incremental source map phải preserve mapping khi subtree unchanged.

---

# 556.174. Debug mapping

Semantic node provenance phải đủ để `440` tạo debug info chính xác.

---

# 556.175. Documentation

Doc extractor từ `485` có thể reuse semantic declarations.

---

# 556.176. LSP

`555` daemon cung cấp:

```text
hover
completion
definition
references
rename
diagnostics
semantic tokens
```

từ cùng semantic DB.

---

# 556.177. Semantic tokens

Token classification có thể incremental theo syntax subtree.

---

# 556.178. Rename impact

Rename dùng SymbolId/reference index, không scan text toàn project mặc định.

---

# 556.179. Reference index

Compiler có thể maintain:

```text
SymbolId → references[]
```

incrementally.

---

# 556.180. Reverse call graph

Có thể maintain:

```text
FunctionId → callers[]
```

để AI/refactoring.

---

# 556.181. Forward call graph

```text
FunctionId → callees[]
```

có thể được cập nhật sau type/trait resolution.

---

# 556.182. Trait implementation index

```text
TraitId → ImplIds[]
TypeId → ApplicableImpls[]
```

phải hỗ trợ efficient invalidation.

---

# 556.183. Type dependency graph

```text
TypeId → dependent layouts/queries
```

---

# 556.184. Effect dependency graph

```text
FunctionId → callers
```

cho effect propagation.

---

# 556.185. Ownership dependency graph

MIR region dependencies phải được lưu nếu incremental ownership analysis cần.

---

# 556.186. Comptime dependency graph

`431` inputs/outputs phải được tích hợp.

---

# 556.187. Build graph dependency

`487` BuildNode dependency không được suy ra đơn giản từ file modification time.

---

# 556.188. Timestamp

Timestamp chỉ là optimization signal.

---

# 556.189. Content verification

Cache reuse phải dựa trên content/semantic fingerprints.

---

# 556.190. Frontend cache poisoning

Cache entry phải verify:

```text
compiler version
grammar
edition
target/config where relevant
dependency fingerprints
```

---

# 556.191. Persistent parser cache

Có thể persist green syntax trees/token chunks nhưng phải versioned.

---

# 556.192. Memory mapped cache

Large syntax caches có thể mmap.

---

# 556.193. Cache format

Cache phải:

```text
versioned
checksummed
self-describing
```

---

# 556.194. Cache corruption

Corrupt cache:

```text
discard
recompute
```

---

# 556.195. No cache correctness dependency

Compiler correctness không được phụ thuộc cache availability.

---

# 556.196. Frontend differential test

So sánh:

```text
incremental frontend
vs
clean frontend
```

trên cùng final source.

---

# 556.197. Random edit testing

Fuzzer tạo:

```text
S0
→ random edit
→ S1
→ random edit
→ S2
```

và so incremental với clean compilation.

---

# 556.198. Edit minimization

Khi divergence:

```text
semantic reducer
```

từ `552` phải minimize sequence.

---

# 556.199. Final frontend contract

Axiom frontend phải:

```text
Incremental
Persistent
Parallel
Deterministic
Unicode-correct
Recovery-capable
Snapshot-aware
Semantic-aware
AI-queryable
```

và luôn có fallback:

```text
incremental failure
      ↓
larger reparse
      ↓
full reanalysis
```

thay vì đánh đổi correctness.

---

# 556.200. HARD INVARIANTS

1. Incremental compilation không được thay đổi semantics.
2. Clean compilation và incremental compilation phải equivalent.
3. Lexer phải deterministic.
4. Parser phải deterministic.
5. Name resolution phải deterministic.
6. Type checking phải deterministic.
7. Trait solving phải deterministic.
8. Parallel execution không được thay đổi semantics.
9. Source snapshot phải immutable.
10. Token chunks phải có identity.
11. Token chunk identity không phụ thuộc source offset đơn thuần.
12. Lexer state phải được fingerprint.
13. Lexical convergence phải được detect.
14. Unchanged token chunks phải có thể reuse.
15. Lexer không được bỏ qua UTF-8 validation.
16. Unicode identifier semantics phải deterministic.
17. Normalization policy phải explicit.
18. Comment-only edit không được mặc định invalidate semantics.
19. Documentation changes phải có dependency riêng.
20. Green tree phải immutable.
21. Green tree phải hỗ trợ structural sharing.
22. Hash collision không được chứng minh equality.
23. Red tree không được là semantic source of truth.
24. Semantic identity phải dùng SymbolId/TypeId.
25. Source offset không phải semantic identity.
26. Parser phải hỗ trợ subtree reparse.
27. Reparse phải bắt đầu từ boundary nhỏ nhất an toàn.
28. Reparse phải được phép escalate.
29. Compiler phải ưu tiên correctness khi incremental boundary không chắc chắn.
30. Whole-file reparse là fallback hợp lệ.
31. Recovery nodes phải được đánh dấu synthetic.
32. Synthetic nodes không được tạo release artifact.
33. IDE incomplete source phải được hỗ trợ.
34. Build mode phải strict.
35. Parser grammar version phải thuộc cache key.
36. Edition phải thuộc cache key khi grammar affected.
37. Feature gates phải thuộc cache key khi grammar affected.
38. Name index phải track module/scope/namespace.
39. Declaration indexing phải tách khỏi body analysis khi có thể.
40. Public interface phải có fingerprint.
41. Private implementation change không được invalidate consumers không liên quan.
42. Public signature change phải invalidate semantic dependents.
43. Public layout change phải invalidate layout/ABI dependents.
44. Import changes phải invalidate affected lookup.
45. Re-export changes phải propagate correctly.
46. Method lookup phải track receiver type.
47. Trait method lookup phải track impl universe.
48. Added impl có thể invalidate negative trait results.
49. Negative trait results không được cache vô hạn trong open world.
50. Closed-world negative results phải fingerprint impl universe.
51. Type query phải include expected-type context khi relevant.
52. Coercion query phải include source/target types.
53. Trait query phải include environment.
54. Layout query phải include target/ABI/repr.
55. Comptime query phải include all relevant inputs.
56. Effect changes phải propagate tới affected callers.
57. Ownership changes phải invalidate affected MIR analysis.
58. HIR phải giữ source provenance.
59. HIR identity không phụ thuộc byte offset.
60. SymbolId có thể được preserve khi identity evidence đủ mạnh.
61. Compiler không được đoán identity khi evidence không đủ.
62. Semantic diff phải distinguish body/signature/interface/ABI changes.
63. Impact analysis phải dùng semantic diff.
64. Conservative invalidation phải được phép.
65. Unsound cache reuse bị cấm.
66. Invalidated query không được publish như Ready.
67. Query dependency phải được recorded.
68. Dynamic dependencies phải được recorded.
69. Cross-snapshot reuse phải chứng minh dependency equivalence.
70. Snapshot ID không được là lý do duy nhất để bỏ cache nếu semantics equivalent.
71. Semantic DB update phải atomic.
72. Failed incremental update không được destroy previous valid state.
73. IDE có thể giữ previous valid semantics nhưng phải đánh dấu stale.
74. Stale semantics không được trả như current exact result.
75. Approximate results phải có provenance/state.
76. Diagnostic cascade phải có root/dependency information.
77. Diagnostic order phải deterministic.
78. Completion phải bind document version.
79. Definition lookup phải semantic.
80. Rename phải semantic.
81. Reference index phải support incremental update.
82. Call graph phải support incremental update.
83. Trait index phải support incremental update.
84. Type dependency graph phải support incremental invalidation.
85. Comptime dependency graph phải integrate.
86. Build graph phải integrate `487`.
87. Query engine phải integrate `555`.
88. Cache identity phải integrate `554`.
89. Correctness validation phải integrate `552`.
90. Parser cache phải versioned.
91. Persistent cache phải integrity-check.
92. Corrupt cache phải bị discard/rebuild.
93. Cache availability không được là correctness dependency.
94. Cache timestamp không được là correctness authority.
95. Content hash phải được kiểm tra khi cần.
96. Semantic hash phải phân biệt textual noise.
97. Interface hash phải phân biệt private implementation.
98. ABI hash phải phân biệt ABI-visible changes.
99. Documentation hash phải có dependency riêng nếu cần.
100. Build artifact phải dùng correct fingerprint set.
101. Independent files phải có thể lex song song.
102. Independent files phải có thể parse song song.
103. Independent modules phải có thể resolve song song.
104. SCC scheduling phải respect module graph.
105. Parallel merge phải deterministic.
106. Worker scheduling không được ảnh hưởng result.
107. Compiler internal arenas không được leak semantic state.
108. Snapshot-bound memory phải reclaimable.
109. Green nodes có thể persistent/share.
110. Memory reclamation không được tạo dangling semantic references.
111. Interning phải có lifecycle policy.
112. Compiler internal memory management không imply language GC.
113. Interactive parsing phải có latency benchmark.
114. Interactive semantic analysis phải có latency benchmark.
115. Cold frontend phải benchmark.
116. Warm frontend phải benchmark.
117. Single-edit benchmark phải tồn tại.
118. Signature-edit benchmark phải tồn tại.
119. Comment-edit benchmark phải tồn tại.
120. Large-file benchmark phải tồn tại.
121. Unicode benchmark phải tồn tại.
122. Malformed-source benchmark phải tồn tại.
123. Incremental frontend phải được differential-tested.
124. Random edit sequences phải được tested.
125. Edit sequences phải được minimizable.
126. Incremental result phải compare với clean result.
127. Parser recovery phải được fuzz.
128. Lexer phải được fuzz.
129. Unicode input phải được fuzz.
130. Query invalidation phải được fuzz.
131. Snapshot transitions phải được fuzz.
132. Parallel frontend phải được race-tested.
133. Parallel frontend phải được deterministic-tested.
134. Cache purge phải preserve semantics.
135. Daemon restart phải preserve semantics.
136. Editor/FS races phải preserve correctness.
137. Stale snapshot phải detectable.
138. Stale diagnostic phải detectable.
139. Stale completion phải detectable.
140. Previous semantic state phải distinguish current state.
141. Error recovery không được leak synthetic declarations.
142. Synthetic nodes không được có ABI identity.
143. Formatter không được mutate semantic truth.
144. Source-map provenance phải preserve.
145. Documentation extraction phải use semantic truth.
146. LSP phải dùng shared semantic engine.
147. AI phải dùng shared semantic engine.
148. AI semantic results phải snapshot-bound.
149. AI semantic results phải provenance-bound.
150. AI không được fabricate incremental state.
151. `why_invalidated` phải dựa trên dependency evidence.
152. `why_rebuilt` phải dựa trên build graph evidence.
153. Frontend optimization không được bypass correctness checks.
154. Hash-based reuse không được thay thế semantic validation khi cần.
155. Recovery mode không được masquerade as release mode.
156. Parser version changes phải invalidate incompatible syntax caches.
157. Semantic rule changes phải invalidate affected semantic caches.
158. Compiler build identity phải fingerprint persistent caches.
159. Toolchain identity phải fingerprint target-dependent results.
160. Target identity phải fingerprint layout/codegen results.
161. Configuration identity phải fingerprint affected semantic/codegen results.
162. Security policy changes phải invalidate security-dependent analysis.
163. Numeric policy changes phải invalidate affected numeric analysis.
164. ABI changes phải invalidate ABI-dependent results.
165. Trait implementation changes phải invalidate relevant trait queries.
166. Public type changes phải invalidate affected layout queries.
167. Public generic constraint changes phải invalidate affected instantiations.
168. Macro/generator changes phải invalidate generated semantic artifacts.
169. Comptime input changes phải invalidate generated results.
170. Resource/compiler-generated source changes phải enter dependency graph.
171. Generated source identity phải preserve provenance.
172. Generated source changes phải propagate correctly.
173. File rename phải reconcile semantic identity.
174. File deletion phải invalidate dependent queries.
175. Module removal phải invalidate imports/dependents.
176. Package dependency changes phải invalidate correct graph regions.
177. Lockfile changes phải affect dependency fingerprint.
178. Workspace changes phải affect workspace graph.
179. Multi-target daemon state phải remain isolated.
180. Multi-toolchain daemon state phải remain isolated.
181. Multi-workspace state phải remain isolated.
182. Persistent state phải schema-versioned.
183. Schema migration phải preserve semantics hoặc invalidate safely.
184. Unsupported cache schema không được silently reinterpret.
185. IPC snapshot identity phải be explicit.
186. Cancellation không được commit partial semantic state.
187. Deadline không được return incomplete semantic result as valid.
188. Interactive priority không được alter correctness.
189. Background warming không được alter correctness.
190. Speculative analysis không được contaminate current exact state.
191. Query deduplication không được alter semantics.
192. Query batching không được alter semantics.
193. Parallel parsing không được alter diagnostics semantics.
194. Parallel resolution không được alter symbol binding.
195. Parallel typechecking không được alter inferred types.
196. Incremental frontend phải support full fallback.
197. Full fallback phải remain tested.
198. Incremental optimization must remain optional.
199. Frontend speed must never outrank semantic correctness.
200. **Final invariant:** Axiom frontend phải biến source editing thành một chuỗi **snapshot → incremental lex → incremental parse → incremental semantic queries → precise invalidation → parallel recomputation**, trong đó mọi reuse đều phải có dependency evidence và bất kỳ trường hợp nào không chứng minh được an toàn đều phải fallback sang phân tích rộng hơn; vì vậy incremental compilation chỉ là một phương thức tối ưu hóa, không bao giờ trở thành một nguồn semantics thứ hai.

**BOOTSTRAP-556: LOCKED.**

---

# NEXT — BOOTSTRAP-557

## BOOTSTRAP-557 — COMPILER MEMORY ARCHITECTURE 2.0, ARENA, INTERNING, PERSISTENT DATA STRUCTURE, CACHE STORAGE & LONG-RUNNING COMPILER MEMORY SAFETY

Task kế tiếp sẽ khóa **bộ nhớ bên trong chính compiler**, một vấn đề đặc biệt quan trọng sau `555–556`.

Nó sẽ giải quyết:

```text
Source
  ↓
Tokens
  ↓
Green Tree
  ↓
AST/HIR
  ↓
Symbols/Types/Traits
  ↓
MIR
  ↓
Query DB
  ↓
Persistent Cache
```

và cách tất cả các lớp này quản lý memory mà **không cần GC của Axiom runtime**.

Trọng tâm `557`:

- arena/bump allocation;
- generational arena;
- interned strings/types/symbols;
- immutable/persistent structures;
- memory ownership giữa query;
- snapshot lifetime;
- cross-snapshot sharing;
- cache mmap;
- eviction;
- fragmentation;
- memory compaction;
- compiler memory budgets;
- OOM recovery;
- daemon memory pressure;
- leak detection;
- long-running daemon stability;
- zero-copy source/token representation;
- pointer/reference nội bộ compiler;
- thread-safe memory ownership;
- deterministic destruction;
- interaction với Axiom memory model `423`;
- và cơ chế để compiler có thể chạy hàng ngày trong IDE/AI mà **memory usage không tăng vô hạn theo số lần edit**.