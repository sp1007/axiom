# BOOTSTRAP-570 — COMPILER IDE/LSP ENGINE 4.0
## SEMANTIC INDEX, INCREMENTAL LSP, CODE COMPLETION, NAVIGATION, REFERENCES, REFACTORING & REAL-TIME SEMANTIC SERVICES

**Trạng thái: COMPLETED / LOCKED**

`570` khóa tầng IDE/LSP native của Axiom. Đây không phải một compiler frontend thứ hai. IDE phải sử dụng trực tiếp **Query Engine + Semantic Database + Diagnostic Engine + Build Graph** của compiler.

Mục tiêu:

> **Một semantic engine duy nhất phục vụ compiler, IDE, CLI và AI agent; không tạo ra hai nguồn sự thật khác nhau.**

---

# 570.1. Kiến trúc tổng thể

```text
                         Source Snapshot
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Incremental Loader  │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Query / Semantic DB │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
   Symbol Index          Type / Trait Index       Diagnostics
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               ▼
                     ┌─────────────────────┐
                     │ IDE Service Engine  │
                     └──────────┬──────────┘
                               │
       ┌────────────┬──────────┼───────────┬────────────┐
       ▼            ▼          ▼           ▼            ▼
 Completion     Navigation   Hover      Semantic      Refactor
                                           Search
       │            │          │           │            │
       └────────────┴──────────┴───────────┴────────────┘
                               │
                               ▼
                             LSP
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
                IDE           CLI          AI Agent
```

---

# 570.2. Single semantic authority

IDE không được tự xây type checker riêng.

---

# 570.3. Shared Query Engine

Mọi IDE request sử dụng Query Engine của compiler.

---

# 570.4. Shared snapshot

Mỗi request gắn với:

```text
DocumentSnapshot
WorkspaceSnapshot
SemanticSnapshot
```

---

# 570.5. Snapshot consistency

Một LSP response phải biểu diễn một snapshot nhất quán.

---

# 570.6. Stale response

Response từ snapshot cũ không được overwrite state mới hơn.

---

# 570.7. Cancellation

Mọi request dài phải cancellable.

---

# 570.8. Request priority

```text
Interactive
Background
Maintenance
```

---

# 570.9. Interactive requests

Completion, hover, definition ưu tiên cao.

---

# 570.10. Background requests

Indexing, references, semantic precomputation ưu tiên thấp hơn.

---

# 570.11. Semantic index

Index lưu:

```text
Symbol
Definition
Reference
Type
Scope
Module
Trait
Call
Field
Method
```

---

# 570.12. Symbol ID

Mỗi symbol dùng stable semantic ID.

```text
SymbolId = semantic identity
```

---

# 570.13. Symbol identity

Symbol ID không phụ thuộc byte offset.

---

# 570.14. Offset

Offset chỉ là source location.

---

# 570.15. Rename stability

Một symbol dịch chuyển dòng không làm thay đổi identity nếu declaration semantics không đổi.

---

# 570.16. Symbol kinds

Core:

```text
module
package
struct
enum
trait
function
method
field
constant
variable
parameter
type_alias
generic_parameter
```

---

# 570.17. Visibility index

Index phải lưu visibility.

---

# 570.18. Scope graph

Semantic DB duy trì lexical/semantic scope graph.

---

# 570.19. Parent scope

Mỗi scope có parent rõ ràng.

---

# 570.20. Shadowing

Index phải biểu diễn shadowing thay vì flatten symbols.

---

# 570.21. Import graph

Index duy trì module import graph.

---

# 570.22. Re-export

Re-export phải giữ provenance tới symbol gốc.

---

# 570.23. Qualified lookup

Hỗ trợ:

```text
module::Type
module::function
Type::method
```

theo Axiom syntax.

---

# 570.24. Unqualified lookup

Lookup tuân thủ đúng compiler name-resolution rules.

---

# 570.25. Completion authority

Completion candidates phải đến từ semantic resolver.

---

# 570.26. Completion context

Engine xác định context:

```text
expression
type
pattern
member
import
attribute
generic
```

---

# 570.27. Member completion

Sau:

```text
value.
```

engine lấy type của `value`.

---

# 570.28. Method completion

Method candidates được resolve bằng trait/extension rules thực tế.

---

# 570.29. Field completion

Chỉ expose fields mà visibility/context cho phép.

---

# 570.30. Type completion

Completion type sử dụng type namespace.

---

# 570.31. Import completion

Module/package index được sử dụng.

---

# 570.32. Generic completion

Generic parameters hiện tại phải nằm trong candidate context.

---

# 570.33. Completion ranking

Ranking chỉ là presentation heuristic.

---

# 570.34. Completion semantics

Ranking không thay đổi compiler resolution.

---

# 570.35. Deterministic completion

Cùng snapshot/context phải tạo cùng candidate set.

---

# 570.36. Candidate deduplication

Cùng semantic symbol không xuất hiện nhiều lần nếu không có lý do presentation.

---

# 570.37. Completion item

Internal representation:

```text
CompletionItem {
    symbol_id
    label
    kind
    detail
    insert_text
    edits
    documentation
    score
}
```

---

# 570.38. Insert text

Insertion phải phù hợp grammar hiện tại.

---

# 570.39. Import insertion

Completion có thể kèm import edit nếu symbol uniquely resolved.

---

# 570.40. Import safety

Không tự động thêm import nếu candidate ambiguous.

---

# 570.41. Signature help

Function/method calls cung cấp:

```text
parameters
active_parameter
return_type
documentation
```

---

# 570.42. Overload resolution

Signature help có thể hiển thị candidates phù hợp context.

---

# 570.43. No semantic mutation

IDE request không được mutate source.

---

# 570.44. Hover

Hover được xây từ semantic facts.

---

# 570.45. Hover contents

Có thể gồm:

```text
symbol
type
signature
documentation
visibility
module
trait
```

---

# 570.46. Type display

Type renderer phải dùng canonical Axiom type representation.

---

# 570.47. Alias expansion

Hover có thể hiển thị alias và expanded form tùy verbosity.

---

# 570.48. Definition navigation

Definition query:

```text
reference → SymbolId → declaration span
```

---

# 570.49. Declaration navigation

Declaration location phải canonical.

---

# 570.50. Go-to-definition

Nếu symbol có nhiều implementation, resolver phải phân biệt declaration và concrete implementation.

---

# 570.51. Go-to-implementation

Trait method có thể navigate tới implementations.

---

# 570.52. Trait navigation

Trait declaration ↔ implementation relationship được indexed.

---

# 570.53. Override navigation

Axiom không có class inheritance; navigation dùng trait/default-method/implementation relationships.

---

# 570.54. Method provenance

Struct-first method phải giữ relation:

```text
method → receiver type
```

---

# 570.55. Extension function

Extension method phải được distinguish khỏi inherent struct method nếu semantic model phân biệt.

---

# 570.56. Find references

Reference index lưu:

```text
SymbolId → Reference[]
```

---

# 570.57. Reference span

Mỗi reference có source span.

---

# 570.58. Reference kind

Ví dụ:

```text
read
write
call
type-use
construction
import
pattern
```

---

# 570.59. Reference completeness

Find references phải tôn trọng snapshot và visibility.

---

# 570.60. Closed-world limitation

Nếu external dependency source không có index, engine phải biểu diễn incomplete result rõ ràng.

---

# 570.61. Reference indexing

Indexing có thể incremental.

---

# 570.62. Reverse index

Symbol → references là first-class index.

---

# 570.63. Forward index

Source node → referenced symbols cũng được lưu.

---

# 570.64. Rename dependency

Rename dùng cả forward và reverse index.

---

# 570.65. Rename planning

Rename trước tiên tạo `RenamePlan`.

---

# 570.66. RenamePlan

```text
RenamePlan {
    symbol_id
    declaration_edit
    reference_edits[]
    import_edits[]
    conflict_set[]
}
```

---

# 570.67. Rename validation

Plan phải được semantic-check trước khi apply.

---

# 570.68. Rename conflict

Nếu rename tạo shadowing/conflict không hợp lệ → reject.

---

# 570.69. Rename generated code

Generated references phải được xử lý theo provenance.

---

# 570.70. Rename comments

Comment/text occurrences không mặc định là semantic references.

---

# 570.71. String literals

String literals không được rename như identifiers trừ khi explicit tooling rule.

---

# 570.72. File rename

Module/file rename phải update import graph.

---

# 570.73. Package rename

Package rename phải update manifest/dependency references.

---

# 570.74. Safe refactoring

Refactoring phải semantic-first, text-second.

---

# 570.75. Refactoring engine

```text
Parse
 → Resolve
 → Analyze
 → Build Transformation
 → Validate
 → Emit Edits
```

---

# 570.76. Atomic refactoring

Một refactor nhiều file được apply atomically.

---

# 570.77. Refactor snapshot

Refactoring bắt đầu từ immutable snapshot.

---

# 570.78. Refactor stale check

Nếu source thay đổi trước khi apply, plan phải revalidate.

---

# 570.79. Extract function

Có thể hỗ trợ extract function sau khi core semantic transformation framework hoàn thiện.

---

# 570.80. Extract variable

Tương tự, phải kiểm tra type/control-flow/resource semantics.

---

# 570.81. Inline function

Không được inline nếu làm thay đổi resource lifetime hoặc observable semantics.

---

# 570.82. Move symbol

Move giữa modules phải cập nhật imports/visibility.

---

# 570.83. Change signature

Signature refactor phải cập nhật call sites.

---

# 570.84. Trait implementation refactor

Moving implementation phải preserve trait coherence.

---

# 570.85. Struct field refactor

Field rename phải cập nhật named construction/access/pattern.

---

# 570.86. Enum variant refactor

Variant rename phải cập nhật pattern matching.

---

# 570.87. Pattern-aware transformation

Refactoring không được chỉ dựa trên text search.

---

# 570.88. Macro/generated transformation

Transformation phải biết source provenance.

---

# 570.89. Semantic search

IDE hỗ trợ query:

```text
symbols
types
methods
traits
calls
references
```

---

# 570.90. Symbol search

Search index phải hỗ trợ prefix/fuzzy search.

---

# 570.91. Fuzzy ranking

Fuzzy score chỉ presentation metadata.

---

# 570.92. Workspace symbol

Workspace-wide symbol search phải không cần compile toàn bộ workspace nếu index đủ.

---

# 570.93. Index persistence

Semantic index có thể persist dưới `.axsem` hoặc compiler index artifact.

---

# 570.94. Index validation

Index phải bind với semantic/source identity.

---

# 570.95. Stale index

Index stale không được dùng như semantic authority.

---

# 570.96. Index rebuild

Stale entries được rebuild incremental.

---

# 570.97. Partial index

Partial workspace index được hỗ trợ.

---

# 570.98. External package index

Precompiled packages có thể cung cấp semantic metadata.

---

# 570.99. `.axsem` integration

`570` sử dụng metadata layer đã khóa trong `565`.

---

# 570.100. Zero-source navigation

Public symbols của precompiled libraries vẫn phải navigation được nếu semantic metadata có sẵn.

---

# 570.101. Private metadata

Private implementation details có thể bị strip khỏi distributed package.

---

# 570.102. Public API metadata

Public API phải đủ metadata cho completion/navigation/type checking.

---

# 570.103. AI semantic interface

AI agent được truy vấn semantic database.

---

# 570.104. AI symbol query

Ví dụ:

```text
resolve_symbol(name, scope)
```

---

# 570.105. AI definition query

```text
definition(symbol_id)
```

---

# 570.106. AI reference query

```text
references(symbol_id)
```

---

# 570.107. AI type query

```text
type_at(file, span)
```

---

# 570.108. AI call graph

```text
callers(function)
callees(function)
```

---

# 570.109. AI implementation query

```text
implementations(trait)
```

---

# 570.110. AI refactor preview

Agent có thể request transformation plan trước khi sửa source.

---

# 570.111. AI authority boundary

AI không được tự tuyên bố semantic fact trái với Query Engine.

---

# 570.112. AI source editing

AI-generated edits phải đi qua same validation/refactoring pipeline.

---

# 570.113. AI patch validation

Patch được parse/type-check/reindex trước commit.

---

# 570.114. Semantic diff

IDE có thể expose semantic changes:

```text
API added
API removed
type changed
visibility changed
trait implementation changed
```

---

# 570.115. API impact

Change analysis dùng reverse dependency graph.

---

# 570.116. Impact analysis

Symbol change → affected queries/actions.

---

# 570.117. Build integration

IDE semantic change có thể trigger Build Graph incremental scheduling `568`.

---

# 570.118. Diagnostic integration

IDE lấy diagnostics trực tiếp từ `569`.

---

# 570.119. Live diagnostics

Sau edit:

```text
edit
 ↓
incremental queries
 ↓
diagnostics
 ↓
LSP publish
```

---

# 570.120. Debounce

Rapid typing có thể debounce background compilation.

---

# 570.121. Immediate syntax feedback

Parser errors có thể được trả nhanh hơn full semantic analysis.

---

# 570.122. Progressive diagnostics

Diagnostics có thể xuất hiện theo phase nhưng snapshot ordering vẫn phải deterministic.

---

# 570.123. Partial semantic state

IDE được phép phục vụ partial results nếu explicit `incomplete=true`.

---

# 570.124. Incomplete result

Không được trình bày partial result như definitive nếu semantic analysis chưa hoàn tất.

---

# 570.125. Completion latency

Completion phải ưu tiên cached semantic facts.

---

# 570.126. Query timeout

Interactive query có deadline.

---

# 570.127. Timeout result

Timeout trả partial/incomplete result thay vì block vô hạn.

---

# 570.128. No semantic degradation

Timeout không được thay đổi compiler correctness.

---

# 570.129. Memory budget

IDE service có memory budget riêng.

---

# 570.130. Index eviction

Cold index pages có thể evict.

---

# 570.131. Lazy index loading

Không cần load toàn bộ workspace index vào RAM.

---

# 570.132. mmap

Semantic artifacts có thể mmap theo `565`.

---

# 570.133. Zero-copy query

Simple symbol metadata nên query mà không copy large strings/records.

---

# 570.134. String interning

Semantic names dùng shared/interned strings khi có lợi.

---

# 570.135. Snapshot sharing

Unchanged snapshots có thể share immutable structures.

---

# 570.136. Copy-on-write

Source edits tạo delta thay vì copy toàn bộ workspace.

---

# 570.137. Document overlay

Unsaved IDE buffers tồn tại như overlay trên filesystem snapshot.

---

# 570.138. Overlay priority

Unsaved source có priority cao hơn disk source cho IDE snapshot.

---

# 570.139. Build boundary

Unsaved document không tự động trở thành build artifact nếu chưa requested.

---

# 570.140. Virtual documents

Generated/in-memory documents có URI/source identity riêng.

---

# 570.141. URI mapping

LSP URI ↔ Axiom FileId phải deterministic.

---

# 570.142. File identity

File identity không chỉ dựa trên display path.

---

# 570.143. Path canonicalization

Canonical path rules phải đồng nhất với Build Graph.

---

# 570.144. Case sensitivity

Target filesystem semantics phải được phản ánh chính xác.

---

# 570.145. Symlink policy

Symlink resolution phải tuân theo workspace security policy.

---

# 570.146. Workspace boundaries

Semantic index không được tự ý đọc ngoài workspace/dependency roots.

---

# 570.147. Dependency source

Dependency source chỉ được load theo package/build policy.

---

# 570.148. Network isolation

IDE query không tự động fetch network dependency trừ explicit policy.

---

# 570.149. Package metadata

Package metadata có thể được sử dụng khi source unavailable.

---

# 570.150. Multi-target IDE

Một workspace có thể có nhiều target.

---

# 570.151. Target-specific semantics

Conditional compilation phải bind đúng target snapshot.

---

# 570.152. Target ambiguity

Nếu project có nhiều target, IDE phải biết active target/context.

---

# 570.153. Configuration context

Completion/type resolution phụ thuộc build configuration.

---

# 570.154. Feature flags

Semantic index key phải bao gồm relevant feature configuration.

---

# 570.155. Environment

Chỉ environment variables ảnh hưởng semantics mới được đưa vào semantic snapshot.

---

# 570.156. Configuration identity

Semantic configuration phải có stable identity.

---

# 570.157. Multi-workspace

Daemon hỗ trợ nhiều workspace isolation.

---

# 570.158. Workspace isolation

Một workspace không được leak semantic state sang workspace khác.

---

# 570.159. Multi-client

Nhiều LSP clients có thể dùng cùng daemon.

---

# 570.160. Client overlays

Mỗi client có thể có document overlay riêng.

---

# 570.161. Overlay isolation

Client A không nhìn thấy unsaved changes của client B trừ explicit shared-session mode.

---

# 570.162. LSP transport

Core semantic engine không phụ thuộc transport.

---

# 570.163. LSP adapter

LSP chỉ là adapter:

```text
LSP request
 → Axiom semantic request
 → result
 → LSP response
```

---

# 570.164. Protocol independence

Có thể dùng engine cho native IDE, CLI, AI tools ngoài LSP.

---

# 570.165. LSP versioning

Protocol adapter phải isolate version-specific behavior.

---

# 570.166. Capability negotiation

Client capabilities được lưu per session.

---

# 570.167. Diagnostics publication

Diagnostics có version và snapshot identity.

---

# 570.168. Semantic tokens

Axiom có thể cung cấp semantic token stream.

---

# 570.169. Token categories

Ví dụ:

```text
type
function
method
variable
parameter
field
constant
namespace
keyword
```

---

# 570.170. Semantic highlighting

Highlighting dùng semantic resolver thay vì regex.

---

# 570.171. Semantic token delta

Unchanged regions có thể reuse.

---

# 570.172. Folding

Folding ranges derive từ syntax/semantic structure.

---

# 570.173. Document symbols

Document symbol tree lấy từ semantic index.

---

# 570.174. Breadcrumbs

Parent symbol chain được index.

---

# 570.175. Call hierarchy

Index:

```text
caller → callee
```

---

# 570.176. Type hierarchy

Axiom không có class inheritance; type hierarchy biểu diễn:

```text
trait → implementation
trait → supertrait
struct → implemented trait
```

---

# 570.177. Field hierarchy

Struct composition relationships được expose khi hữu ích.

---

# 570.178. Workspace references

Cross-package references cần package identity.

---

# 570.179. API compatibility

Refactoring phải detect public API breakage.

---

# 570.180. Refactoring transaction

```text
Analyze
 → Plan
 → Validate
 → Apply
 → Reindex
 → Diagnostics
```

---

# 570.181. Rollback

Failed refactoring phải rollback toàn bộ edits.

---

# 570.182. Reindex atomicity

Index update sau refactor phải atomic theo snapshot.

---

# 570.183. Undo integration

IDE adapter có thể map transaction thành undo unit.

---

# 570.184. Refactor audit

Machine-readable refactor plan có:

```text
old symbol
new symbol
files changed
semantic effects
```

---

# 570.185. Testing

Mỗi semantic service phải có unit tests.

---

# 570.186. LSP conformance

LSP adapter phải có protocol conformance suite.

---

# 570.187. Completion tests

Test candidate correctness trên:

- scope;
- visibility;
- generic;
- traits;
- imports;
- members.

---

# 570.188. Navigation tests

Definition/reference tests phải kiểm tra exact spans.

---

# 570.189. Refactoring tests

Mọi transformation phải compile lại sau apply.

---

# 570.190. Incremental tests

So sánh:

```text
incremental result
vs
fresh full result
```

---

# 570.191. Snapshot tests

Edit sequence:

```text
S0 → S1 → S2 → ... → Sn
```

phải cho semantic result tương đương fresh compilation của `Sn`.

---

# 570.192. Concurrency tests

Concurrent LSP requests không được corrupt semantic DB.

---

# 570.193. Cancellation tests

Cancelled query không được publish stale result.

---

# 570.194. Crash recovery

Daemon restart phải rebuild/recover semantic index an toàn.

---

# 570.195. Large workspace test

Phải test workspace có hàng trăm nghìn/thậm chí hàng triệu symbols.

---

# 570.196. Performance

Hot interactive queries phải tránh full workspace recompilation.

---

# 570.197. Memory

Semantic index phải hỗ trợ paging/lazy loading/eviction.

---

# 570.198. Determinism

Cùng semantic snapshot phải cho cùng:

```text
symbol resolution
completion candidate set
definition
references
refactoring plan
diagnostics
```

---

# 570.199. Single-source-of-truth invariant

Compiler, IDE, CLI và AI agent phải dùng cùng semantic facts; không được tồn tại một “IDE type system” hoặc “AI type system” riêng có thể mâu thuẫn với compiler.

---

# 570.200. FINAL HARD INVARIANT

> **Axiom IDE/LSP Engine 4.0 phải là một lớp dịch vụ trực tiếp trên Semantic Query Engine và Compiler Semantic Database. Mọi completion, hover, navigation, reference search, semantic highlighting, call hierarchy, diagnostics và refactoring đều phải dựa trên cùng canonical semantic facts và snapshot model mà compiler sử dụng. Incremental updates, caching, parallelism, cancellation, multiple clients, AI agents hoặc LSP transport chỉ thay đổi cách truy cập; chúng không được tạo ra một semantic truth khác.**

**BOOTSTRAP-570: LOCKED.**

---

# NEXT — BOOTSTRAP-571

## COMPILER SOURCE ANALYSIS 2.0 — CONTROL-FLOW GRAPH, DATAFLOW ENGINE, DEF-USE CHAINS, CONSTANT PROPAGATION, REACHABILITY, DEAD CODE & FLOW-SENSITIVE SEMANTICS

`571` sẽ xây **dataflow foundation dùng chung** cho compiler optimization, static analysis, diagnostics, IDE và AI.

Kiến trúc dự kiến:

```text
                    HIR / MIR
                       │
                       ▼
                 ┌─────────────┐
                 │ CFG Builder  │
                 └──────┬──────┘
                        ▼
               ┌─────────────────┐
               │ Dataflow Engine │
               ├─────────────────┤
               │ Def-Use         │
               │ Reaching Defs   │
               │ Live Values     │
               │ Const Prop      │
               │ Reachability    │
               │ Dominators      │
               │ Postdominators  │
               │ Alias Facts     │
               └────────┬────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Optimizer      Analyzer        IDE/AI
```

Trọng tâm `571` sẽ là xây **một dataflow engine dùng chung**, thay vì để mỗi optimization/static analyzer tự viết một CFG/dataflow implementation riêng. Điều này đặc biệt quan trọng với mục tiêu Axiom: compiler phải mạnh về optimization nhưng kiến trúc vẫn tránh được việc hàng chục subsystem cùng duy trì những bản sao semantic/CFG khác nhau.

**BOOTSTRAP-571: NEXT.**