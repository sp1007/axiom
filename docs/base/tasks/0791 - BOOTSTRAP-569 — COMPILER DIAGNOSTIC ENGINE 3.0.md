# BOOTSTRAP-569 — COMPILER DIAGNOSTIC ENGINE 3.0
## ERROR RECOVERY, MULTI-DIAGNOSTIC ANALYSIS, ERROR CASCADE SUPPRESSION, SOURCE SPANS, FIX-IT, EXPLANATION GRAPH & AI-READABLE DIAGNOSTICS

**Trạng thái: COMPLETED / LOCKED**

`569` định nghĩa diagnostic engine production của Axiom. Diagnostic không còn là chuỗi text do từng compiler phase tự in ra, mà là **structured semantic artifact** có identity, provenance, source span, related evidence, fix-it và machine-readable representation.

Nguyên tắc nền tảng:

> **Compiler phải báo đúng lỗi gốc, giữ được càng nhiều thông tin hữu ích càng tốt, và tuyệt đối không biến một lỗi thành một chuỗi lỗi giả do error propagation.**

---

# 569.1. Kiến trúc

```text
                         SOURCE SNAPSHOT
                               │
                               ▼
                    ┌────────────────────┐
                    │ Diagnostic Context │
                    └─────────┬──────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
       Lexer              Parser              Semantic
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌────────────────────┐
                    │ Diagnostic Engine  │
                    ├────────────────────┤
                    │ Collector          │
                    │ Normalizer         │
                    │ Classifier         │
                    │ Causality Graph    │
                    │ Cascade Filter     │
                    │ Recovery Manager   │
                    │ Fix-it Engine      │
                    │ Explanation Engine │
                    └─────────┬──────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           CLI               LSP          AI / JSON
```

---

# 569.2. Diagnostic không phải text

Internal representation bắt buộc là structured object.

```text
Diagnostic {
    id
    severity
    category
    code
    primary_span
    secondary_spans[]
    message
    notes[]
    help[]
    causes[]
    related[]
    fixes[]
    provenance
    confidence
    snapshot_id
}
```

Text rendering chỉ là một backend.

---

# 569.3. Diagnostic identity

Mỗi diagnostic có stable logical identity:

```text
DiagnosticKey =
    diagnostic_code
  + normalized_source_location
  + semantic_subject
  + relevant_context
```

---

# 569.4. Diagnostic identity không phụ thuộc wording

Thay đổi message wording không được làm thay đổi diagnostic semantics.

---

# 569.5. Diagnostic code

Mỗi compiler diagnostic phải có machine-readable code.

Ví dụ:

```text
AX1001
AX2004
AX3017
```

Code namespace được compiler quản lý.

---

# 569.6. Severity

Core severity:

```text
Error
Warning
Info
Hint
```

---

# 569.7. Fatal

`Fatal` là execution state của compiler, không phải severity semantic thông thường.

---

# 569.8. Error

`Error` ngăn artifact tương ứng được coi là valid.

---

# 569.9. Warning

Warning không làm source invalid.

---

# 569.10. Info/Hint

Không ảnh hưởng compilation semantics.

---

# 569.11. Source snapshot

Diagnostic luôn gắn với immutable source snapshot.

---

# 569.12. Snapshot identity

```text
SourceSnapshotId = hash(source_content + relevant_virtual_files)
```

---

# 569.13. UTF-8 source

Axiom source mặc định UTF-8.

---

# 569.14. Span representation

Span dùng byte offsets làm canonical representation.

```text
Span {
    file_id
    start_byte
    end_byte
}
```

---

# 569.15. Byte offsets

Byte offset là authority.

---

# 569.16. Character positions

Line/column chỉ là derived presentation data.

---

# 569.17. Unicode correctness

Một UTF-8 code point nhiều byte không được làm hỏng span.

---

# 569.18. Grapheme handling

Grapheme cluster chỉ dùng presentation/editing khi cần; không thay thế byte-span identity.

---

# 569.19. Line index

Source snapshot có line index lazy/incremental.

---

# 569.20. Column calculation

Column được tính từ UTF-8 source và rendering policy.

---

# 569.21. Primary span

Mỗi error phải có primary span nếu có thể xác định.

---

# 569.22. Secondary span

Secondary spans biểu diễn evidence hoặc related source.

---

# 569.23. Related location

Diagnostic có thể trỏ tới:

- declaration;
- previous use;
- conflicting implementation;
- inferred type;
- dependency;
- ABI declaration.

---

# 569.24. Label

Mỗi span có optional label.

Ví dụ conceptually:

```text
foo(x)
  ^ argument has type A

bar(x)
  ^ expected B
```

---

# 569.25. Multi-file diagnostics

Một diagnostic có thể tham chiếu nhiều file.

---

# 569.26. External source

External dependency locations chỉ được hiển thị nếu source/debug metadata khả dụng.

---

# 569.27. Missing source

Nếu source không tồn tại, diagnostic dùng artifact/module identity thay thế.

---

# 569.28. Diagnostic provenance

```text
Provenance {
    phase
    query
    action
    parent_diagnostics[]
}
```

---

# 569.29. Provenance

Ví dụ:

```text
Parser
TypeChecker
TraitSolver
OwnershipChecker
ConstEvaluator
LayoutEngine
ABI
Linker
```

---

# 569.30. Causality graph

Diagnostics được tổ chức thành directed graph:

```text
Root Error
   │
   ├── derived error
   ├── derived error
   └── dependent error
```

---

# 569.31. Root diagnostic

Diagnostic có thể được đánh dấu:

```text
RootCause
Derived
Independent
```

---

# 569.32. Cascade suppression

Derived diagnostic không được hiển thị nếu nó chỉ là consequence không hữu ích của root error.

---

# 569.33. Suppression criterion

Suppression phải dựa trên provenance/causality, không chỉ text matching.

---

# 569.34. Example

Một typo:

```text
pritn("hello")
```

không được kéo theo hàng chục lỗi semantic không liên quan.

---

# 569.35. Error type

Compiler có internal:

```text
ErrorType
ErrorExpr
ErrorPattern
ErrorSymbol
ErrorModule
```

---

# 569.36. Error types

Error type cho phép semantic analysis tiếp tục.

---

# 569.37. Error expression

AST/HIR node có thể mang `ErrorExpr`.

---

# 569.38. Error symbol

Missing name có thể tạo temporary error symbol.

---

# 569.39. Error module

Import failure có thể tạo error module placeholder.

---

# 569.40. Error trait resolution

Failed trait lookup có thể tạo unresolved trait result.

---

# 569.41. Error ownership

Ownership failure không được khiến toàn bộ function trở thành invalid AST.

---

# 569.42. Error recovery principle

> **Recover locally, preserve globally.**

---

# 569.43. Lexer recovery

Lexer phải cố gắng tiếp tục sau:

- malformed UTF-8;
- unterminated literal;
- invalid escape;
- unknown character.

---

# 569.44. UTF-8 corruption

Malformed source bytes phải tạo diagnostic rõ ràng và không được giả định character boundaries sai.

---

# 569.45. Parser recovery

Parser sử dụng synchronization points.

---

# 569.46. Synchronization tokens

Ví dụ:

```text
}
)
]
;
,
fn
struct
enum
trait
impl
```

---

# 569.47. Recovery cost

Parser không được recovery bằng cách tạo lượng AST giả quá lớn.

---

# 569.48. Missing token

Compiler có thể tạo synthetic token.

---

# 569.49. Synthetic token

Synthetic token có source provenance rõ ràng.

---

# 569.50. Synthetic token

Không được xuất hiện như source text thật trong fix-it nếu chưa xác định edit an toàn.

---

# 569.51. Unexpected token

Diagnostic phải report token thực tế và expected token set khi hữu ích.

---

# 569.52. Expected-token compression

Expected token set phải được nhóm thành category khi danh sách quá lớn.

---

# 569.53. Parser ambiguity

Diagnostic phải ưu tiên interpretation có confidence cao nhất.

---

# 569.54. Semantic recovery

Semantic engine tiếp tục khi có error placeholder.

---

# 569.55. Name resolution recovery

Missing symbol không được khiến mọi reference downstream trở thành duplicate errors.

---

# 569.56. Type recovery

Type checker dùng `ErrorType`.

---

# 569.57. Inference recovery

Type inference có thể unify với `ErrorType` mà không tạo thêm mismatch errors.

---

# 569.58. Generic recovery

Generic substitution failure phải được containment trong diagnostic root.

---

# 569.59. Trait recovery

Trait solver có thể trả:

```text
Satisfied
Unsatisfied
Ambiguous
Error
```

---

# 569.60. Error propagation

`Error` result phải propagate mà không tạo duplicate diagnostic.

---

# 569.61. Duplicate suppression

Hai diagnostics cùng logical root không nên được report nhiều lần.

---

# 569.62. Diagnostic deduplication key

Dựa trên:

```text
code
snapshot
span
semantic_subject
causal_root
```

---

# 569.63. Independent errors

Compiler vẫn phải report các lỗi độc lập nếu recovery đủ an toàn.

---

# 569.64. Maximum diagnostics

Có configurable limit:

```text
max_errors
max_warnings
```

---

# 569.65. Error limit

Khi đạt limit, compiler report summary thay vì tạo avalanche.

---

# 569.66. Error truncation

Không được silently discard errors.

---

# 569.67. Truncation metadata

Output phải ghi rõ:

```text
additional diagnostics suppressed
```

---

# 569.68. Diagnostic grouping

Có thể group theo:

- file;
- phase;
- root cause;
- module;
- category.

---

# 569.69. CLI ordering

Default ordering phải deterministic.

---

# 569.70. Canonical diagnostic order

Canonical ordering:

```text
snapshot
file
byte offset
severity
diagnostic code
diagnostic identity
```

---

# 569.71. Scheduler independence

Parallel compiler execution không được thay đổi canonical diagnostic set/order.

---

# 569.72. Concurrent diagnostics

Multiple threads có thể emit diagnostics vào concurrent collector.

---

# 569.73. Collector

Collector thread-safe hoặc shard-based.

---

# 569.74. Merge

Diagnostics được canonicalize sau collection.

---

# 569.75. Deterministic merge

Merge result phải deterministic.

---

# 569.76. Incremental diagnostics

Diagnostic engine phải reuse diagnostics từ unchanged semantic regions khi identity còn hợp lệ.

---

# 569.77. Diagnostic cache

Cache key phải include snapshot and relevant semantic dependencies.

---

# 569.78. Invalidated diagnostic

Khi source span hoặc semantic dependency thay đổi, diagnostic cũ phải invalidate.

---

# 569.79. Stable diagnostic identity

Unchanged source/semantics phải giữ diagnostic identity ổn định.

---

# 569.80. LSP mapping

Diagnostic phải map trực tiếp sang LSP diagnostics.

---

# 569.81. LSP range

LSP line/character range được derive từ canonical byte span.

---

# 569.82. UTF-16 compatibility

Nếu LSP client yêu cầu UTF-16 positions, mapping layer phải convert chính xác.

---

# 569.83. LSP versioning

Diagnostic publication gắn document version.

---

# 569.84. Stale diagnostic

Diagnostic của document version cũ không được overwrite version mới.

---

# 569.85. Diagnostic cancellation

Stale semantic request có thể cancel.

---

# 569.86. CLI renderer

Renderer phải hỗ trợ:

```text
human
compact
json
jsonl
machine
```

---

# 569.87. JSON schema

Machine output phải có stable schema version.

---

# 569.88. JSON example

```text
{
  "code": "AX2031",
  "severity": "error",
  "message": "...",
  "primary": {
    "file": "...",
    "start": 120,
    "end": 124
  },
  "related": [],
  "fixes": []
}
```

---

# 569.89. JSON stability

Field semantics phải versioned.

---

# 569.90. AI diagnostic format

Diagnostic graph phải machine-readable.

---

# 569.91. AI node

Mỗi diagnostic có thể expose:

```text
problem
evidence
cause
impact
suggested_action
confidence
```

---

# 569.92. AI explanation

AI explanation layer được phép diễn giải diagnostic nhưng không được thay đổi canonical diagnostic.

---

# 569.93. AI authority

AI không phải compiler semantic authority.

---

# 569.94. AI hallucination boundary

Generated explanation phải đánh dấu là generated explanation.

---

# 569.95. Compiler fact

Compiler facts phải phân biệt với AI-generated explanation.

---

# 569.96. Explanation graph

```text
Diagnostic
   │
   ├── Definition
   ├── Expected rule
   ├── Actual fact
   ├── Related symbols
   └── Suggested fixes
```

---

# 569.97. Type error explanation

Ví dụ semantic structure:

```text
expected: Vec3
found: Vec2
source: argument #2
```

---

# 569.98. Inference explanation

Có thể show constraint chain:

```text
T = ?
T : Numeric
argument => String
constraint conflict
```

---

# 569.99. Trait explanation

Có thể show:

```text
required trait: Display
candidate type: MyType
matching implementations: none
```

---

# 569.100. Ownership explanation

Có thể show:

```text
resource moved here
later use here
```

---

# 569.101. Lifetime terminology

Axiom diagnostic không được yêu cầu Rust-style lifetime notation nếu core language không sử dụng lifetime model đó.

---

# 569.102. Resource diagnostic

Resource errors dùng:

```text
acquired
moved
consumed
released
used
```

theo Axiom ownership model.

---

# 569.103. Defer diagnostics

Invalid `defer` usage phải chỉ rõ scope và cleanup ordering.

---

# 569.104. Async diagnostics

Async misuse phải liên kết:

```text
producer
await
task
executor
```

nếu có.

---

# 569.105. Concurrency diagnostics

Data race prevention diagnostics nếu static analysis phát hiện được phải phân biệt với runtime detection.

---

# 569.106. Atomic diagnostics

Invalid atomic operation/order combination phải chỉ rõ target limitation.

---

# 569.107. Const diagnostics

Const evaluation failure phải expose evaluation location.

---

# 569.108. Comptime diagnostics

Comptime panic/error phải preserve compile-time stack trace.

---

# 569.109. Generic instantiation

Diagnostic trong instantiated generic phải map:

```text
generic definition
instantiation site
failing expression
```

---

# 569.110. Generic backtrace

Có thể collapse generic instantiation stack để tránh output khổng lồ.

---

# 569.111. Macro/generated source

Generated code phải giữ provenance về source generator.

---

# 569.112. Hygiene

Diagnostic trong generated syntax phải map về hygienic origin khi có thể.

---

# 569.113. Generated source display

CLI có thể show generated source khi `--explain-generated`.

---

# 569.114. Fix-it

Fix-it là structured edit:

```text
TextEdit {
    file
    start
    end
    replacement
}
```

---

# 569.115. Multiple edits

Một fix có thể chứa nhiều edits.

---

# 569.116. Edit atomicity

Multi-edit fix phải apply atomically.

---

# 569.117. Non-overlap

Một fix không được chứa overlapping edits trừ khi explicitly supported.

---

# 569.118. Fix validation

Fix-it phải được reparse/recheck trước khi đánh dấu validated.

---

# 569.119. Safe fix

Safe fix có semantic confidence cao và không làm thay đổi intended behavior ngoài correction cần thiết.

---

# 569.120. Suggested fix

Suggested fix có thể cần developer review.

---

# 569.121. Unsafe fix

Compiler không tự động apply unsafe semantic transformation.

---

# 569.122. Fix confidence

```text
Exact
High
Medium
Low
```

---

# 569.123. Fix identity

Fix identity phải stable để IDE action caching.

---

# 569.124. Code action

LSP code action được derive từ Fix-it.

---

# 569.125. Import fix

Missing symbol có thể đề xuất import nếu candidate uniquely determined.

---

# 569.126. Rename-like correction

Typo suggestion chỉ tự động nếu confidence đủ cao.

---

# 569.127. Did-you-mean

Name lookup có thể tính edit distance + semantic visibility.

---

# 569.128. Candidate explosion

Không report hàng trăm candidate.

---

# 569.129. Candidate ranking

Candidates có thể sort theo deterministic relevance.

---

# 569.130. No political/subjective inference

Diagnostic engine chỉ phản ánh compiler facts/rules, không suy diễn intent của programmer ngoài các heuristic rõ ràng.

---

# 569.131. Warning configuration

Warnings có thể:

```text
allow
warn
deny
```

---

# 569.132. Error promotion

`deny` warning có thể trở thành compilation error.

---

# 569.133. Diagnostic policy

Policy không thay đổi underlying diagnostic identity.

---

# 569.134. Suppression attributes

Axiom có thể hỗ trợ local suppression.

---

# 569.135. Suppression scope

Suppression phải có lexical/semantic scope rõ ràng.

---

# 569.136. Suppression audit

Machine output phải có thể biết diagnostic bị suppressed bởi policy nào.

---

# 569.137. Unused suppression

Compiler có thể warning suppression không còn tác dụng.

---

# 569.138. Diagnostic categories

Core category examples:

```text
syntax
name
type
trait
generic
ownership
const
comptime
concurrency
async
module
visibility
ABI
FFI
layout
link
resource
security
```

---

# 569.139. Security diagnostics

Security analysis phải phân biệt:

```text
definite violation
potential issue
advisory
```

---

# 569.140. Undefined behavior

Potential UB phải không bị report như definite UB nếu analysis chưa chứng minh được.

---

# 569.141. Static-analysis confidence

Static analyzer có confidence/proof status riêng.

---

# 569.142. Analyzer provenance

Diagnostic từ lint/static analysis phải ghi analyzer identity.

---

# 569.143. Compiler phase boundary

Mọi compiler phase phải emit structured diagnostics qua shared interface.

---

# 569.144. No direct stderr

Core compiler phases không được trực tiếp print diagnostic.

---

# 569.145. Diagnostic API

Conceptually:

```text
emit(diagnostic)
note(diagnostic)
related(diagnostic)
fix(diagnostic)
```

---

# 569.146. Diagnostic builder

Builder API phải enforce required fields trước publication.

---

# 569.147. Missing primary span

Một diagnostic có thể không có span nếu lỗi là project/global.

---

# 569.148. Global diagnostic

Ví dụ:

```text
target SDK missing
```

có thể dùng logical resource location.

---

# 569.149. Project diagnostic

Package/build configuration errors có project-level span.

---

# 569.150. Linker diagnostics

Linker dùng cùng diagnostic model.

---

# 569.151. Undefined symbol

Link error phải liên kết:

```text
reference
symbol
object
candidate definition
```

---

# 569.152. ABI diagnostics

ABI mismatch phải chỉ rõ:

```text
calling convention
parameter type
return type
target
```

---

# 569.153. FFI diagnostics

Foreign declaration mismatch phải report cả Axiom và foreign side khi metadata available.

---

# 569.154. Artifact diagnostics

Corrupt `.axobj/.axmir/.axsem` phải report:

```text
artifact identity
schema
offset/chunk
validation failure
```

---

# 569.155. Cache diagnostics

Cache failure không được biến thành source error.

---

# 569.156. Remote diagnostics

Remote worker error phải preserve original provenance.

---

# 569.157. Worker failure

Worker crash phải report infrastructure failure, không phải compiler source error.

---

# 569.158. Retry

Retry không tạo duplicate user-facing diagnostic nếu failure đã được recovered.

---

# 569.159. Distributed diagnostic merge

Remote diagnostics phải merge deterministic với local diagnostics.

---

# 569.160. Diagnostic ownership

Diagnostic collector thuộc compilation snapshot.

---

# 569.161. Snapshot isolation

Diagnostics từ snapshot A không được leak vào snapshot B.

---

# 569.162. Daemon retention

Daemon có thể retain diagnostics để LSP queries.

---

# 569.163. Diagnostic invalidation

Source change invalidate affected diagnostics.

---

# 569.164. Partial invalidation

Không cần recompute diagnostics của unaffected modules.

---

# 569.165. Query integration

Diagnostic engine có thể request facts từ Query Engine `559+`.

---

# 569.166. Query provenance

Diagnostic records query dependencies để incremental invalidation.

---

# 569.167. Semantic error root

Nếu nhiều diagnostics cùng fail vì một query result, query failure có thể trở thành common causal node.

---

# 569.168. Explanation DAG

Không phải mọi diagnostic relationship đều là tree; internal model hỗ trợ DAG.

---

# 569.169. Cycle protection

Diagnostic explanation graph không được tạo cycle vô hạn.

---

# 569.170. Explanation depth

CLI có giới hạn explanation depth.

---

# 569.171. Compact mode

Default CLI phải readable, không dump toàn bộ graph.

---

# 569.172. Verbose mode

`--explain` có thể mở rộng causal chain.

---

# 569.173. Debug mode

`--diagnostic-debug` expose provenance/query IDs.

---

# 569.174. JSON full graph

Machine consumers có thể yêu cầu full diagnostic graph.

---

# 569.175. AI query

AI tooling có thể query:

```text
why diagnostic?
what rule failed?
what facts support it?
what fixes exist?
what dependencies caused it?
```

---

# 569.176. AI query safety

AI query không được mutate compiler semantic state.

---

# 569.177. IDE hover

IDE có thể lấy structured explanation cho diagnostic span.

---

# 569.178. Quick fix

IDE lấy Fix-it trực tiếp.

---

# 569.179. Related information

IDE có thể navigate giữa primary và related spans.

---

# 569.180. Diagnostic navigation

Compiler phải cung cấp stable IDs cho navigation.

---

# 569.181. Testing

Mỗi diagnostic code phải có test.

---

# 569.182. Golden tests

CLI rendering có golden tests.

---

# 569.183. JSON tests

Machine schema có compatibility tests.

---

# 569.184. Recovery tests

Parser recovery phải test:

```text
one error
two errors
many independent errors
cascading errors
```

---

# 569.185. Unicode tests

Phải test:

```text
ASCII
Vietnamese
CJK
emoji
combining marks
multibyte identifiers
```

---

# 569.186. Incremental tests

Source edit phải invalidate đúng diagnostic subset.

---

# 569.187. Parallel tests

Serial và parallel compilation phải produce equivalent diagnostic set.

---

# 569.188. Distributed tests

Local và remote diagnostics phải equivalent.

---

# 569.189. Fuzzing

Malformed source fuzzing phải đảm bảo:

```text
no crash
no infinite loop
no memory corruption
bounded diagnostic explosion
```

---

# 569.190. Recovery fuzzing

Parser/semantic recovery phải được fuzz riêng.

---

# 569.191. Fix-it tests

Mỗi automatic fix phải có:

```text
before
fix
after
recompile
```

---

# 569.192. Fix idempotence

Applying an already-correct fix không được tạo corruption.

---

# 569.193. Diagnostic determinism

Cùng source snapshot và compiler state semantics phải tạo cùng canonical diagnostics.

---

# 569.194. Performance

Diagnostic collection không được trở thành bottleneck của compiler.

---

# 569.195. Memory

Diagnostic storage phải hỗ trợ compact representation cho large builds.

---

# 569.196. Large-build limit

Một project có hàng triệu semantic nodes không được tạo diagnostic memory proportional với toàn bộ source nếu chỉ có ít errors.

---

# 569.197. Error avalanche invariant

Một root error không được tạo unbounded derived diagnostics.

---

# 569.198. Semantic authority

Canonical diagnostic facts phải đến từ compiler semantic engine; renderer/AI không được tự tạo compiler fact.

---

# 569.199. Reproducibility

CLI, LSP, JSON và AI representation của cùng diagnostic phải quy về cùng canonical diagnostic identity.

---

# 569.200. FINAL HARD INVARIANT

> **Axiom Diagnostic Engine phải biểu diễn mọi lỗi, cảnh báo và thông tin compiler dưới dạng structured, deterministic, snapshot-bound diagnostics với source span chính xác, provenance, causal relationships và optional fixes. Compiler phải recover đủ để tiếp tục phân tích các vùng độc lập, nhưng phải suppress các lỗi phái sinh không hữu ích. Parallelism, incremental compilation, cache, remote execution, renderer, LSP hoặc AI explanation không được thay đổi semantic diagnostic set. AI và UI chỉ diễn giải canonical compiler facts, không trở thành semantic authority.**

**BOOTSTRAP-569: LOCKED.**

---

# NEXT — BOOTSTRAP-570

## COMPILER IDE/LSP ENGINE 4.0 — SEMANTIC INDEX, INCREMENTAL LSP, CODE COMPLETION, GO-TO-DEFINITION, FIND REFERENCES, SYMBOL NAVIGATION, REFACTORING & REAL-TIME SEMANTIC SERVICES

`570` sẽ xây tầng IDE-native trực tiếp trên Query Engine + Semantic Database + Diagnostic Engine:

```text
                    AXIOM DAEMON
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Semantic Query DB      Build Graph
              │                     │
              └──────────┬──────────┘
                         ▼
                 IDE/LSP Engine
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 Completion        Navigation        Diagnostics
       │                 │                 │
       ├── Hover         ├── Definition    ├── Errors
       ├── Signature     ├── References     ├── Warnings
       ├── Members       ├── Implementations└── Fixes
       └── Imports       └── Call hierarchy
                         │
                         ▼
                  Refactoring Engine
```

Trọng tâm tiếp theo sẽ là **IDE responsiveness ở quy mô rất lớn** mà không biến LSP thành một compiler thứ hai: mọi completion/navigation/refactoring phải dùng chung semantic facts với compiler, có snapshot consistency, cancellation, incremental invalidation và khả năng phục vụ AI coding agent.

**BOOTSTRAP-570: NEXT.**