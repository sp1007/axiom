Tiếp tục với **BOOTSTRAP-641 — Native Distributed Search, Indexing, Query Planning, Full-Text Search, Vector Search, Hybrid Retrieval & Query Execution Runtime 5.0**.

:::writing{variant="document" id="58314" title="BOOTSTRAP-641 — Native Distributed Search, Indexing, Query Planning, Full-Text Search, Vector Search, Hybrid Retrieval & Query Execution Runtime 5.0"}
# BOOTSTRAP-641
## Native Distributed Search, Indexing, Query Planning, Full-Text Search, Vector Search, Hybrid Retrieval & Query Execution Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Search & Query Execution Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-640

---

# 1. Mục tiêu

BOOTSTRAP-641 cung cấp search/query runtime native cho Axiom.

Nó bao phủ:

- indexing;
- structured query;
- full-text search;
- lexical search;
- vector search;
- approximate nearest neighbor;
- hybrid retrieval;
- filtering;
- faceting;
- aggregation;
- sorting;
- pagination;
- distributed query planning;
- shard routing;
- parallel execution;
- query cancellation;
- streaming results;
- ranking;
- scoring;
- highlighting;
- result merging;
- index lifecycle;
- incremental indexing;
- snapshot/recovery;
- query cache;
- index cache;
- data locality;
- schema-aware search;
- data governance-aware retrieval.

Mục tiêu kiến trúc:

> Axiom có thể xây dựng database search, document search, log search, code search, semantic/vector search và AI retrieval mà không bắt buộc Elasticsearch, Solr, OpenSearch, Milvus, FAISS hoặc hệ thống search bên ngoài.

External search engines vẫn được hỗ trợ như provider.

---

# 2. Ranh giới

| Layer | Trách nhiệm |
|---|---|
| 611 | storage primitives |
| 612 | schema/serialization |
| 628 | distributed data |
| 634 | event/stream |
| 640 | data governance |
| **641** | indexing/query/search |
| 639 | policy decision |
| 603 | capability enforcement |
| 630 | distributed compute |
| 633 | telemetry |

641 không trở thành database storage layer.

```text
611/612
   ↓
628 Data
   ↓
641 Index
   ↓
Query Planner
   ↓
Distributed Execution
```

---

# 3. Core principles

1. Query phải typed.
2. Query plan phải deterministic.
3. Index không phải source of truth.
4. Search result không được coi là authoritative data.
5. Index có thể rebuild từ source.
6. Query cancellation phải propagate.
7. Distributed query phải bounded.
8. Không yêu cầu global transaction.
9. Ranking phải explicit.
10. Vector similarity phải explicit metric.
11. ANN là approximation, không giả định exact.
12. Hybrid ranking phải deterministic khi inputs giống nhau.
13. Governance policy phải được áp dụng trước khi trả kết quả.
14. Index không được bypass 640.
15. Search authorization vẫn thuộc 639 + 603.
16. Query engine không cần GC.
17. Hot path hạn chế allocation.
18. External engine chỉ là provider.
19. Core query execution không phụ thuộc scripting.
20. Query resource budgets là bắt buộc.

---

# 4. Search architecture

```text
                    Query
                      │
             ┌────────▼────────┐
             │ Query Parser    │
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │ Type Checker    │
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │ Query Optimizer │
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │ Query Planner   │
             └────────┬────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
     Lexical        Vector       Structured
      Index          Index          Index
        │             │             │
        └─────────────┼─────────────┘
                      ▼
             Distributed Merge
                      │
                      ▼
                  Ranking
                      │
                      ▼
                 Governance
                      │
                      ▼
                   Result
```

---

# 5. Core types

```text
SearchEngine
Index
IndexId
IndexGeneration
IndexSchema
IndexField
IndexSegment
IndexSnapshot
Query
QueryPlan
QueryNode
QueryContext
QueryResult
SearchHit
SearchScore
Ranker
Analyzer
Tokenizer
Vector
VectorIndex
VectorMetric
Filter
Facet
Aggregation
Shard
ShardId
SearchCursor
SearchRequest
SearchResponse
```

---

# 6. SearchEngine

```text
SearchEngine {
    registry
    planner
    executor
    cache
    resource_policy
}
```

API:

```text
SearchEngine.search(self, request)
SearchEngine.explain(self, query)
SearchEngine.create_index(self, schema)
SearchEngine.drop_index(self, index)
SearchEngine.refresh(self, index)
SearchEngine.optimize(self, index)
```

---

# 7. Index

Index identity:

```text
IndexId
IndexGeneration
IndexRevision
```

Index generation prevents stale handles.

---

# 8. Index source

Index can be built from:

```text
Dataset
Table
Collection
Stream
File
Document
EventLog
MaterializedView
ExternalProvider
```

---

# 9. Source of truth

Index metadata:

```text
source_asset
source_revision
```

Index never becomes authoritative unless explicitly designed as primary store.

---

# 10. Index schema

```text
IndexSchema {
    fields
    analyzers
    vectors
    sortable_fields
    facetable_fields
    stored_fields
}
```

---

# 11. Field definition

```text
IndexField {
    name
    source_type
    index_type
    analyzer
    stored
    sortable
    facetable
}
```

---

# 12. Field index types

```text
Keyword
Text
Integer
Float
Boolean
DateTime
GeoPoint
GeoShape
Vector
Binary
Nested
Object
```

---

# 13. Keyword index

Exact matching:

```text
status == "active"
```

---

# 14. Numeric index

Supports:

```text
=
!=
<
<=
>
>=
range
```

---

# 15. Date index

Canonical representation:

```text
integer timestamp
```

No floating-point time comparison.

---

# 16. Boolean index

Bitmap/posting optimization allowed.

---

# 17. Text index

Text index requires analyzer:

```text
Tokenizer
Normalizer
StopwordPolicy
Stemmer?
```

All components versioned.

---

# 18. Analyzer identity

```text
AnalyzerId
AnalyzerVersion
```

Changing analyzer requires new index generation unless migration is explicitly supported.

---

# 19. Tokenizer

Tokenizer produces:

```text
Token {
    term
    position
    start_offset
    end_offset
}
```

---

# 20. Unicode

Text processing builds on BOOTSTRAP-617.

No ASCII-only assumption.

---

# 21. Language analyzer

Analyzer may specify:

```text
language
normalization
segmentation
stemming
```

Vietnamese and English can use different analyzer configurations.

---

# 22. Multilingual index

A field can have multiple logical analyzers:

```text
title.vi
title.en
title.raw
```

or analyzer selection metadata.

---

# 23. Search normalization

Search normalization must use same compatible analyzer version as indexing.

---

# 24. Inverted index

Canonical structure:

```text
term
→
posting list
```

Posting:

```text
doc_id
frequency
positions?
```

---

# 25. Posting compression

Use:

```text
delta encoding
block encoding
bit packing
```

Provider-selectable.

---

# 26. Skip structures

Posting lists may include skip blocks for fast intersection.

---

# 27. Term dictionary

Dictionary maps:

```text
term → term_id
```

Implementation can use:

```text
FST
B-tree
hash table
sorted blocks
```

---

# 28. Exact lookup

Keyword queries should avoid full-text analysis when exact semantics are intended.

---

# 29. Phrase query

```text
Phrase("native programming language")
```

requires positional postings.

---

# 30. Boolean query

Operators:

```text
AND
OR
NOT
```

---

# 31. Query precedence

Canonical:

```text
NOT
AND
OR
```

Parentheses override.

---

# 32. Query AST

```text
QueryNode =
    Term
    Phrase
    Prefix
    Wildcard
    Range
    Exists
    And
    Or
    Not
    MatchAll
    MatchNone
    Vector
    Hybrid
    Filter
```

---

# 33. Query parser

Text search syntax is optional.

Typed API remains canonical.

---

# 34. Typed query API

```text
Query.term(field, value)
Query.range(field, min, max)
Query.and(queries)
Query.or(queries)
Query.not(query)
Query.vector(field, vector)
```

---

# 35. Query builder

Struct-only:

```text
SearchQuery.term(self, field, term)
SearchQuery.filter(self, predicate)
SearchQuery.sort(self, field, direction)
SearchQuery.limit(self, count)
```

---

# 36. Filter

Filters produce boolean document sets.

They should avoid scoring when possible.

---

# 37. Filter types

```text
TermFilter
RangeFilter
ExistsFilter
PrefixFilter
GeoFilter
BooleanFilter
GovernanceFilter
TenantFilter
```

---

# 38. Filter pushdown

Filters should be pushed toward index scans whenever possible.

---

# 39. Query optimizer

Optimizer transformations:

```text
constant folding
predicate simplification
filter pushdown
AND ordering
OR simplification
range merging
duplicate elimination
```

---

# 40. Query cost

Planner estimates:

```text
posting cardinality
selectivity
segment count
shard count
vector candidate count
sort cost
aggregation cost
```

---

# 41. No mandatory cost statistics

Small indexes can use deterministic heuristics.

Large indexes can maintain statistics.

---

# 42. Query plan

```text
QueryPlan {
    root
    estimated_cost
    resource_budget
    index_generation
}
```

---

# 43. Query plan node types

```text
IndexScan
TermScan
RangeScan
VectorScan
Filter
Join
Aggregate
Sort
TopK
Project
Deduplicate
ShardScatter
ShardGather
Rank
Highlight
```

---

# 44. Execution model

Execution is streaming where possible.

```text
source
→ operator
→ operator
→ sink
```

---

# 45. Query pipeline

```text
Parse
→ Validate
→ Authorize
→ Plan
→ Execute
→ Rank
→ Govern
→ Project
→ Return
```

---

# 46. Authorization ordering

Security-sensitive filtering should happen before exposing unauthorized fields.

---

# 47. Governance ordering

640 constraints must be considered before result exposure.

---

# 48. Document visibility

A search hit may be:

```text
Visible
Filtered
Restricted
Redacted
```

---

# 49. Redaction

Result projection may remove restricted fields.

---

# 50. No leakage through score

Unauthorized document existence must not be inferable through result counts when policy forbids existence disclosure.

---

# 51. SearchHit

```text
SearchHit {
    document_id
    score
    fields
    highlights
    sort_values
}
```

---

# 52. SearchScore

Score is typed numeric:

```text
f32
f64
```

depending on profile.

---

# 53. Deterministic tie-break

If scores equal:

```text
document_id
```

is default deterministic tie-break.

---

# 54. Pagination

Support:

```text
Offset
Cursor
SearchAfter
```

---

# 55. Cursor

Cursor must bind:

```text
index_generation
query_fingerprint
sort_spec
policy_revision
```

---

# 56. Cursor expiration

Optional TTL.

---

# 57. Deep pagination

Offset pagination should be bounded.

Cursor/search-after preferred.

---

# 58. Top-K

Planner should push Top-K into shard scans.

---

# 59. Distributed search

For N shards:

```text
Scatter
→
local top-K
→
Gather
→
global merge
```

---

# 60. Oversampling

For distributed ranked search:

```text
local_k >= global_k
```

may require oversampling to reduce missed results.

---

# 61. Vector search

Core supports:

```text
ExactNearestNeighbor
ApproximateNearestNeighbor
```

---

# 62. Vector type

```text
Vector {
    dimension
    values
    element_type
}
```

Element types:

```text
f32
f16
bf16?
int8
```

depending on provider.

---

# 63. Vector dimensions

Dimension must be fixed per index field.

---

# 64. Vector metrics

```text
Cosine
DotProduct
L2
L1
Hamming
Jaccard
```

Provider may add others.

---

# 65. Vector normalization

Cosine may use normalized vectors.

Normalization semantics must be explicit.

---

# 66. Exact vector search

Compute:

```text
distance(query, vector)
```

over candidate set.

---

# 67. ANN boundary

Supported algorithm families:

```text
HNSW
IVF
PQ
IVF-PQ
Flat
Graph-based provider
```

Exact algorithm is index-provider metadata.

---

# 68. ANN parameters

Example:

```text
ef_search
ef_construction
M
nprobe
```

must be typed configuration.

---

# 69. ANN approximation

Search result must expose:

```text
exact = false
```

when approximate execution is used.

---

# 70. Vector index rebuild

Changing vector dimension requires new generation.

Changing ANN parameters may permit in-place optimization depending on provider.

---

# 71. Vector filtering

Preferred execution:

```text
filter
→
vector search
```

or:

```text
vector candidate
→
filter
```

depending on selectivity and index capabilities.

Planner chooses.

---

# 72. Hybrid retrieval

Combine:

```text
Lexical
+
Vector
```

---

# 73. Hybrid strategies

```text
WeightedScore
RRF
Cascade
FilterThenVector
VectorThenLexical
UnionThenRank
```

---

# 74. Reciprocal Rank Fusion

RRF:

```text
score(d) =
Σ 1 / (k + rank_i(d))
```

Parameters explicit.

---

# 75. Weighted hybrid

```text
final =
w_lexical * lexical_score
+
w_vector * vector_score
```

Weights typed.

---

# 76. Score normalization

Different score spaces must not be blindly added.

Supported normalization:

```text
MinMax
ZScore
Softmax
Rank
None
```

---

# 77. Determinism

Given identical:

```text query
index generation
provider version
parameters
```

result ordering should be deterministic.

---

# 78. Ranking API

```text
Ranker.rank(self, candidates, context)
```

---

# 79. Built-in rankers

```text
BM25
TFIDF
VectorDistance
Weighted
RRF
FieldBoost
Recency
```

---

# 80. BM25

Parameters:

```text
k1
b
```

must be index/query configuration.

---

# 81. Field boosting

```text
title ^ 3
body ^ 1
tags ^ 2
```

---

# 82. Recency ranking

Requires explicit timestamp field.

Example:

```text
score × decay(age)
```

---

# 83. Ranking plugins

External ranker providers allowed.

Must declare:

```text
ABI
version
determinism
resource limits
```

---

# 84. No arbitrary ranking scripts

Core ranker cannot execute arbitrary remote code.

---

# 85. Aggregation

Supported:

```text
Count
Min
Max
Sum
Average
Stats
Percentiles
Cardinality
Terms
DateHistogram
Range
```

---

# 86. Aggregation execution

Shard-local partial aggregation:

```text
local aggregate
→
merge
```

---

# 87. Approximate aggregation

Optional:

```text
HyperLogLog
TDigest
```

must report approximation.

---

# 88. Faceting

Facets use indexed fields.

---

# 89. Facet counts

Counts must obey security/governance visibility rules.

---

# 90. Hidden-document leakage

Facet counts cannot expose restricted documents.

---

# 91. Sorting

Supported:

```text
ascending
descending
score
distance
```

---

# 92. Missing values

Explicit:

```text
MissingFirst
MissingLast
```

---

# 93. Geo search

Types:

```text
GeoPoint
GeoShape
```

Queries:

```text
Radius
BoundingBox
Polygon
Nearest
```

---

# 94. Geo distance

Canonical units:

```text
meters
```

---

# 95. Geo index

Provider may use:

```text
RTree
Geohash
S2
H3
BKD
```

---

# 96. Geo governance

640 can restrict:

```text
data region
```

but search coordinates themselves may be sensitive.

---

# 97. Search authorization

Query context:

```text
subject
identity
tenant
capabilities
purpose
```

---

# 98. Tenant isolation

Index can partition by:

```text
tenant_id
```

---

# 99. Tenant-aware index

Planner should push tenant filter into shard selection.

---

# 100. Row-level security

639 policy can return:

```text
filter predicate
```

that becomes mandatory query constraint.

---

# 101. Field-level security

Policy can specify:

```text
allowed_fields
redacted_fields
```

---

# 102. Governance-aware index

Index metadata:

```text
governance_fingerprint
```

---

# 103. Classification-aware query

Query context can require:

```text
classification <= allowed_level
```

---

# 104. Residency-aware query

Planner may only query shards in permitted regions.

---

# 105. Cross-region query

Explicit policy required.

---

# 106. Query routing

Routing keys:

```text
tenant
document_id
partition_key
region
```

---

# 107. Shard

```text
Shard {
    shard_id
    generation
    region
    node
    index_segment_set
}
```

---

# 108. Shard states

```text
Creating
Ready
Recovering
ReadOnly
Draining
Offline
Failed
```

---

# 109. Shard allocation

635 provides placement.

---

# 110. Shard replication

628 manages replicated index/source state.

---

# 111. Index replica

Search replica may be independently optimized.

---

# 112. Replica consistency

Modes:

```text
Strong
Session
Eventual
```

Search default may be eventual.

---

# 113. Search freshness

Response metadata:

```text
index_revision
source_revision
lag
```

---

# 114. Read-after-write

Optional session token binds query to minimum index revision.

---

# 115. Index refresh

Modes:

```text
Manual
Periodic
NearRealTime
TransactionalProvider
```

---

# 116. Near-real-time

Documents become searchable after refresh interval.

---

# 117. Indexing pipeline

```text
Source Change
→
Decode
→
Governance Validate
→
Analyze
→
Index
→
Commit
```

---

# 118. Change ingestion

Sources:

```text
628 change feed
634 events
611 file watcher
612 snapshot
```

---

# 119. Incremental indexing

Only changed documents should be reindexed.

---

# 120. Delete indexing

Delete marker:

```text
document_id
source_revision
```

---

# 121. Update

Update may be:

```text
delete old
+
index new
```

or provider-specific in-place update.

---

# 122. Index transaction

Batch indexing supports:

```text
begin
add/update/delete
commit
abort
```

---

# 123. Atomic visibility

Commit makes batch visible as one index generation/revision where provider supports it.

---

# 124. Partial failure

Failed batch must not falsely report complete commit.

---

# 125. Backpressure

Indexing pipeline bounded by:

```text
CPU
memory
disk
queue
IOPS
```

---

# 126. Resource governance

606 limits:

```text
query_cpu
query_memory
index_cpu
index_memory
disk
IO
vector_build
```

---

# 127. Query budget

```text
QueryBudget {
    max_time
    max_memory
    max_docs
    max_shards
    max_vector_candidates
    max_result_count
}
```

---

# 128. Query cancellation

Cancellation propagates:

```text
client
→ coordinator
→ shard
→ operator
```

---

# 129. Deadline

Every distributed query may carry deadline.

---

# 130. Timeout behavior

Result:

```text
Complete
Partial
Timeout
Cancelled
Failed
```

---

# 131. Partial results

Partial result is only returned if request explicitly permits it.

---

# 132. Search consistency

Request:

```text
ConsistencyMode
```

values:

```text
BestEffort
Session
Quorum
LinearizableProvider
```

---

# 133. Linearizable search

Only if underlying index/provider supports it.

Search engine must not falsely claim linearizability.

---

# 134. Query cache

Cache key:

```text
query_fingerprint
index_generation
policy_revision
governance_revision
tenant
```

---

# 135. Query cache safety

No secret/private query material should appear in global cache keys.

---

# 136. Result cache

Result cache must obey authorization and governance context.

---

# 137. Negative cache

Misses may be cached with bounded TTL.

---

# 138. Segment cache

Caches:

```text
term dictionary
postings
vector graph
stored fields
```

---

# 139. Memory budgeting

Cache eviction integrated with 606.

---

# 140. Index snapshots

Index snapshot:

```text
IndexSnapshot {
    index_generation
    segments
    manifest
    source_revision
}
```

---

# 141. Snapshot storage

613/611 can store snapshots.

---

# 142. Snapshot restore

Restore:

```text
validate
→
stage
→
verify
→
activate
```

---

# 143. Snapshot integrity

Checksums/hashes from 610.

---

# 144. Index corruption

State:

```text
Healthy
Suspect
Corrupt
Recovering
```

---

# 145. Recovery

Options:

```text
RestoreSnapshot
ReplayChanges
Rebuild
UseReplica
```

---

# 146. Index rebuild

Source of truth:

```text
628/611
```

---

# 147. Rebuild scheduling

630 can execute distributed rebuild jobs.

---

# 148. Index migration

New index generation:

```text
old generation
→
build new
→
validate
→
atomic switch
```

---

# 149. Zero-downtime migration

Readers remain on old generation until new is ready.

---

# 150. Dual indexing

Optional:

```text
old + new
```

during migration.

---

# 151. Schema migration

612 schema fingerprint must be checked.

---

# 152. Analyzer migration

Analyzer version mismatch requires reindex unless compatibility declared.

---

# 153. Vector migration

Dimension change always creates new index field/generation.

---

# 154. Index alias

```text
IndexAlias {
    alias_id
    target_generation
}
```

---

# 155. Atomic alias switch

Useful for blue/green index deployments.

---

# 156. Search deployment

636 can deploy index generation.

---

# 157. Search rollback

Rollback switches alias to previous healthy generation.

---

# 158. Query plan cache

Plan cache key:

```text
query_shape
schema_fingerprint
index_generation
optimizer_version
```

---

# 159. Plan invalidation

Invalidate on:

```text
schema change
index generation change
optimizer version
provider change
```

---

# 160. Query compilation

Frequent queries may compile to native execution plans.

---

# 161. Native query plan

Possible:

```text
IR
→
optimizer
→
native execution
```

---

# 162. Query bytecode

Optional compact VM for dynamic plans.

VM must be removable.

---

# 163. No mandatory JIT

Static query workloads can use ahead-of-time compilation.

---

# 164. Search DSL

Axiom can provide:

```text
search users
where age >= 18
and name contains "hung"
sort score desc
limit 20
```

---

# 165. Canonical typed form

DSL lowers to typed Query AST.

---

# 166. Query schema

Compiler validates field existence where index schema is known.

---

# 167. Compile-time query error

Example:

```text
unknown field "agge"
```

must be compiler error when statically knowable.

---

# 168. Dynamic query

Runtime validation remains available.

---

# 169. SQL boundary

Optional SQL-like provider can lower:

```text
SELECT ...
WHERE ...
```

into Query AST.

---

# 170. No SQL dependency

Search core does not require SQL.

---

# 171. JSON query boundary

Optional JSON query format.

---

# 172. AI retrieval

641 provides:

```text
lexical retrieval
vector retrieval
hybrid retrieval
metadata filtering
ranking
```

suitable for RAG.

---

# 173. Embedding generation

Embedding model execution belongs to 630/GPU runtime.

641 consumes vectors.

---

# 174. Embedding provenance

Vector field may reference:

```text
EmbeddingModelId
EmbeddingModelVersion
Dimension
```

---

# 175. Vector compatibility

Query vector model must match index vector metadata.

---

# 176. Vector model mismatch

Error:

```text
EmbeddingModelMismatch
```

unless explicit projection is configured.

---

# 177. Quantization

Optional:

```text
FP16
INT8
PQ
Binary
```

with accuracy metadata.

---

# 178. Quantized search

Result may expose:

```text
approximation_mode
```

---

# 179. Reranking

Pipeline:

```text
retrieve top 100
→
rerank top 20
```

---

# 180. Reranker

Provider:

```text
RankerProvider
```

could be CPU/GPU/remote.

---

# 181. Reranker security

Remote reranker requires 603 + 639 + network capabilities.

---

# 182. Reranker budget

Must respect:

```text
max_candidates
max_latency
max_memory
```

---

# 183. Hybrid pipeline

Example:

```text
BM25 top 100
+
Vector top 100
→
RRF
→
rerank top 50
→
top 10
```

---

# 184. Search explanation

```text
SearchEngine.explain(query)
```

returns:

```text
parsed_ast
plan
index
filters
ranking
resource_estimates
```

---

# 185. Hit explanation

Optional:

```text
explain_hit(document_id)
```

showing score components.

---

# 186. Explain security

Explanation must obey same authorization/data governance rules.

---

# 187. Highlighting

Text highlight:

```text
<match>
```

but output format should be structured spans rather than raw HTML.

---

# 188. Highlight span

```text
HighlightSpan {
    start
    end
    field
}
```

---

# 189. Suggestion

Optional:

```text
TermSuggest
PhraseSuggest
PrefixSuggest
```

---

# 190. Autocomplete

Prefix index / completion index.

---

# 191. Completion index

Separate from full-text index if needed.

---

# 192. Fuzzy search

Optional edit distance.

Must have bounded:

```text
max_distance
max_expansions
```

---

# 193. Regex search

Only bounded/safe regex provider.

No catastrophic backtracking.

---

# 194. Wildcard expansion

Must enforce:

```text
max_expansions
max_terms
```

---

# 195. Expensive query guard

Potentially dangerous:

```text
leading wildcard
large regex
deep nested boolean
huge vector candidate set
```

must be rejected or budget-limited.

---

# 196. Query admission

639 can apply:

```text
QueryAdmissionPolicy
```

before execution.

---

# 197. Search rate limiting

606 + 639:

```text
requests/sec
concurrency
CPU
vector operations
```

---

# 198. Tenant query quotas

Per tenant:

```text
QPS
concurrency
memory
vector budget
```

---

# 199. Fair scheduling

607 executes query tasks with fairness.

---

# 200. Priority

Query priority cannot bypass security/resource hard limits.

---

# 201. Query isolation

Large aggregation must not starve latency-sensitive search.

---

# 202. Query classes

```text
Interactive
Batch
Analytics
BackgroundIndex
Rebuild
```

---

# 203. Background indexing

Lower priority by default.

---

# 204. Batch search

Streaming result API:

```text
next_batch()
```

---

# 205. Result streaming

```text
SearchStream<T>
```

supports cancellation/backpressure.

---

# 206. Async API

```text
SearchEngine.search_async(...)
```

integrates 607.

---

# 207. Blocking API

Synchronous convenience API can wrap async runtime.

---

# 208. Search worker

Worker identity integrated with 630.

---

# 209. Distributed execution

Coordinator:

```text
QueryCoordinator
```

workers:

```text
QueryWorker
```

---

# 210. Coordinator failure

Client can retry using query ID.

---

# 211. Query ID

```text
QueryId
QueryGeneration
```

---

# 212. Idempotent execution

Read-only query retries are naturally idempotent.

Index mutation requests require explicit idempotency keys.

---

# 213. Search request identity

```text
SearchRequestId
```

for audit/tracing.

---

# 214. Trace integration

633 spans:

```text
parse
plan
scatter
shard
merge
rank
serialize
```

---

# 215. Metrics

```text
query_count
query_latency
p50/p95/p99
cache_hit
shard_latency
index_lag
vector_candidates
rerank_count
partial_results
timeouts
```

---

# 216. Cardinality control

No raw query text as metric label.

---

# 217. Logs

602 logs query fingerprints, not raw sensitive queries by default.

---

# 218. Privacy

Query text can itself be sensitive.

---

# 219. Query redaction

Logs should redact:

```text
tokens
PII
secrets
```

using explicit policy.

---

# 220. Search audit

Audit event:

```text
SearchExecuted {
    subject
    tenant
    index
    query_fingerprint
    policy_revision
}
```

No raw query payload by default.

---

# 221. Index audit

```text
IndexCreated
IndexRebuilt
IndexMigrated
IndexActivated
IndexDeleted
```

---

# 222. Vector audit

```text
VectorIndexCreated
VectorIndexRebuilt
VectorModelChanged
```

---

# 223. External provider

Provider interface:

```text
SearchProvider
IndexProvider
VectorProvider
AnalyzerProvider
RankerProvider
```

---

# 224. Provider requirements

Provider declares:

```text
ABI
version
supported_query_features
consistency
security
governance
resource_model
```

---

# 225. External Elasticsearch/OpenSearch boundary

Can map:

```text
Query AST
→
provider query
```

but semantics differences must be declared.

---

# 226. External vector provider

Can map to:

```text
FAISS
Milvus
Qdrant
external service
```

without making them core dependencies.

---

# 227. Provider semantic contract

Provider must not silently claim unsupported:

```text
consistency
exactness
governance
security
```

---

# 228. Provider sandbox

Plugins use 623 + 603.

---

# 229. Package integration

Index schemas and analyzers can be packaged in 613.

---

# 230. Version pinning

Index manifest records:

```text
provider_version
analyzer_version
ranker_version
```

---

# 231. Reproducibility

Same:

```text
source revision
schema
analyzer
provider
```

should permit deterministic rebuild subject to provider guarantees.

---

# 232. Index manifest

```text
IndexManifest {
    index_id
    generation
    schema_fingerprint
    source_revision
    analyzer_versions
    vector_config
    provider
}
```

---

# 233. Search package

Optional:

```text
.axindex
.axquery
.axrank
.axvector
```

---

# 234. Compiler annotations

```text
@index
@index_field
@analyzer
@tokenizer
@vector
@metric
@ranker
@searchable
@sortable
@facetable
@stored
@filterable
@partition
@shard
@query
@retrieval
@rerank
```

---

# 235. Generated artifacts

```text
.axindex
.axquery
.axanalyzer
.axvector
.axrank
```

---

# 236. Static query generation

Compiler can generate:

```text
SearchQueryBuilder
SearchResultType
```

---

# 237. Typed result projection

Example:

```text
SearchResult<User> {
    id
    score
    name
}
```

---

# 238. No reflection

Schema metadata generated at compile time.

---

# 239. Query ABI

Stable serialized Query AST can cross process/network boundaries.

---

# 240. Query schema fingerprint

```text
QuerySchemaFingerprint
```

---

# 241. Remote query

631 RPC can transport:

```text
Query AST
QueryBudget
SecurityContext
GovernanceContext
```

---

# 242. Security context

Remote service must not trust caller-supplied capabilities without authentication/verification.

---

# 243. Capability propagation

603 handles authority.

---

# 244. Query context

```text
QueryContext {
    subject
    tenant
    purpose
    capabilities
    deadline
    cancellation
    consistency
}
```

---

# 245. Governance context

```text
GovernanceContext {
    allowed_classifications
    allowed_regions
    allowed_purposes
    data_subject_scope?
}
```

---

# 246. Policy context

639 evaluates query admission and result constraints.

---

# 247. Result policy

Policy may constrain:

```text
max_results
allowed_fields
max_score
regions
```

---

# 248. Policy-dependent ranking

Allowed only if deterministic and explicitly declared.

---

# 249. Policy revision binding

Search response includes:

```text
policy_revision
governance_revision
```

where required.

---

# 250. Search cache invalidation

Policy change invalidates affected cached results.

---

# 251. Governance cache invalidation

Classification/residency changes invalidate relevant result cache.

---

# 252. Tenant cache isolation

Tenant-specific cache entries cannot be served cross-tenant.

---

# 253. Index-level tenant partition

Preferred for high isolation.

---

# 254. Physical isolation

Optional:

```text
tenant → shard
```

---

# 255. Logical isolation

Default:

```text
tenant filter
```

---

# 256. Security recommendation

Highly sensitive tenants may require dedicated indexes/shards.

This is an architectural option, not a universal requirement.

---

# 257. Query planner locality

Planner should prefer local shard when semantics permit.

---

# 258. Cross-region search

Can execute parallel regional queries and merge.

---

# 259. Regional consistency

Each region returns:

```text
region
index_revision
```

---

# 260. Stale region

Planner may reject region if freshness requirement is unmet.

---

# 261. Search freshness requirement

```text
max_index_lag
```

---

# 262. Stale result policy

```text
AllowStale
RejectStale
PreferFresh
```

---

# 263. Federated search

```text
FederatedSearch {
    regions
    indexes
    merge_strategy
}
```

---

# 264. Federation security

Each remote region must authenticate.

---

# 265. Federation governance

Each region applies local governance before result export.

---

# 266. Result minimization

Remote region should return only fields required by caller.

---

# 267. Federated ranking

Scores may not be directly comparable across providers.

Normalize explicitly.

---

# 268. Provider score normalization

If no normalization contract exists:

```text
score ordering only
```

or use rank-based fusion.

---

# 269. Search result provenance

Each result can expose:

```text
source_region
index_generation
provider
```

---

# 270. Search snapshot

For reproducibility:

```text
SearchSnapshot {
    indexes
    revisions
    policy_revision
    governance_revision
}
```

---

# 271. Snapshot-bound query

Query can request:

```text
snapshot_id
```

---

# 272. Snapshot expiry

Snapshots have bounded retention.

---

# 273. Query replay

Replay can use snapshot + query AST.

---

# 274. Search debugging

CLI:

```text
axiom search explain
axiom search plan
axiom search stats
axiom search index inspect
```

---

# 275. Query plan inspection

Shows:

```text
operator tree
estimated cost
actual cost
shards
cache
```

---

# 276. Query profile

Optional profile output:

```text
operator latency
CPU
memory
documents scanned
```

---

# 277. Query simulator

Deterministic fake index/provider for tests.

---

# 278. Test index

Can use:

```text
MemoryIndexProvider
```

---

# 279. Fuzzing

Fuzz:

```text
query parser
query AST
analyzers
vector dimensions
index metadata
cursor
distributed merge
```

---

# 280. Malformed query

Must fail safely without:

```text
crash
unbounded allocation
infinite recursion
```

---

# 281. Query depth

Limit:

```text
max_ast_depth
```

---

# 282. Boolean explosion

Limit:

```text
max_clauses
max_expansions
```

---

# 283. Vector explosion

Limit:

```text
max_candidates
max_dimensions
```

---

# 284. Aggregation explosion

Limit:

```text
max_buckets
max_groups
```

---

# 285. Result explosion

Limit:

```text
max_results
max_response_bytes
```

---

# 286. Index build explosion

Limit:

```text
max_terms
max_fields
max_vectors
```

---

# 287. Memory safety

No unchecked external length can directly allocate arbitrary memory.

---

# 288. Integer safety

Query arithmetic must detect overflow.

---

# 289. Floating-point safety

NaN/Inf vectors and scores must have defined behavior.

---

# 290. NaN policy

Default:

```text
reject NaN/Inf
```

unless provider explicitly supports them.

---

# 291. Vector dimension validation

Mismatch:

```text
VectorDimensionMismatch
```

before execution.

---

# 292. Vector zero norm

Cosine similarity with zero vector has explicit error semantics.

---

# 293. Index checksum

Segments have checksums.

---

# 294. Segment corruption

Corrupt segment is quarantined.

---

# 295. Segment replacement

Restore/rebuild can replace segment atomically.

---

# 296. Segment merge

Background merge:

```text
segments
→
merged segment
```

---

# 297. Merge scheduling

Resource governor limits CPU/IO.

---

# 298. Merge correctness

Old segments remain readable until new segment committed.

---

# 299. Crash during merge

Recovery discards incomplete output and preserves old segments.

---

# 300. Index compaction

Compaction distinct from source data compaction.

---

# 301. Tombstone cleanup

Only after source/index consistency permits.

---

# 302. Search engine startup

Startup:

```text
load manifest
→
verify segments
→
recover
→
publish ready
```

---

# 303. Service supervision

605 monitors search workers.

---

# 304. Health

Search health includes:

```text
IndexHealthy
QueryHealthy
ProviderHealthy
GovernanceHealthy
```

---

# 305. Degraded mode

Search may continue with:

```text
partial shards
```

only if policy/request permits.

---

# 306. Admission control

639 can reject expensive queries during overload.

---

# 307. Load shedding

606 + 639:

```text
reject
delay
downgrade
partial
```

according to explicit policy.

---

# 308. No silent downgrade

Exact vector search must not silently become ANN.

---

# 309. Approximation declaration

Any approximate operator must be visible in result metadata.

---

# 310. Search response metadata

```text
SearchResponse {
    hits
    total_hits
    approximate
    partial
    index_revision
    policy_revision
    governance_revision
    elapsed
}
```

---

# 311. Total hit semantics

Can be:

```text
Exact
LowerBound
Approximate
Unknown
```

---

# 312. Distributed count

Exact global count can be expensive.

Request may select:

```text
Exact
LowerBound
Skip
```

---

# 313. Streaming total

Streaming search may not know total until completion.

---

# 314. Search-after

Stable sort values required.

---

# 315. Cursor security

Cursor must not be user-modifiable to bypass filters.

Signed/opaque cursor recommended.

---

# 316. Cursor binding

Bind to:

```text
tenant
subject
policy
governance
query
index
```

---

# 317. Search cache security

Never share cached authorization decisions across subjects unless policy explicitly establishes equivalence.

---

# 318. Equivalence class

Optional cache key can use:

```text
authorization_context_fingerprint
```

instead of identity.

---

# 319. Fingerprint safety

Fingerprint must not expose raw sensitive identity.

---

# 320. Search observability

633 receives:

```text
query_fingerprint
plan_fingerprint
index_generation
provider_version
```

---

# 321. Query fingerprint

Stable canonical hash of Query AST.

---

# 322. Plan fingerprint

Hash of normalized execution plan.

---

# 323. Index fingerprint

Hash of schema + generation + provider configuration.

---

# 324. Governance fingerprint

From 640.

---

# 325. Policy fingerprint

From 639.

---

# 326. Full execution identity

```text
ExecutionFingerprint =
hash(
    query,
    plan,
    index,
    policy,
    governance
)
```

---

# 327. Reproducibility

Execution metadata allows postmortem reconstruction.

---

# 328. Distributed retry

Shard query retries allowed before deadline.

---

# 329. Retry budget

Prevent retry storm.

---

# 330. Query idempotency

Read-only execution is safe to retry.

---

# 331. Provider failure

Error categories:

```text
Unavailable
Timeout
Corrupt
Unsupported
Unauthorized
ResourceExceeded
InvalidQuery
```

---

# 332. Fallback provider

Can fallback only if semantics remain compatible.

---

# 333. No unsafe fallback

Exact → approximate fallback requires explicit policy.

---

# 334. Search provider capability negotiation

At startup:

```text
supported_features
limits
consistency
approximation
```

---

# 335. Feature negotiation

Query planner rejects unsupported features rather than silently changing semantics.

---

# 336. Query optimizer extensibility

Optimizer passes:

```text
logical plan
→
physical plan
```

---

# 337. Logical operators

```text
Scan
Filter
Project
Join
Aggregate
Sort
Limit
Rank
VectorSearch
```

---

# 338. Physical operators

```text
PostingScan
BKDRangeScan
HNSWSearch
HashAggregate
TopKHeap
ShardScatter
MergeTopK
```

---

# 339. Join support

Search engine may support:

```text
IndexJoin
HashJoin
LookupJoin
```

but large relational joins should use 628/630 query systems when appropriate.

---

# 340. Join budget

Strict memory limits.

---

# 341. Lookup join

Retrieve related document IDs from another index.

---

# 342. Cross-index join

Explicitly enabled.

---

# 343. Distributed join

Requires:

```text
partition strategy
broadcast threshold
shuffle budget
```

---

# 344. Shuffle

Uses 604/609/630 transport depending deployment.

---

# 345. Query execution placement

635 can place workers.

---

# 346. Data locality

Planner prefers:

```text
index shard locality
source data locality
GPU locality
```

---

# 347. GPU vector search

614/615/630 provide GPU execution.

641 submits vector operations.

---

# 348. GPU fallback

CPU fallback must be explicit or declared as provider behavior.

---

# 349. GPU memory

606 accounts VRAM/device memory.

---

# 350. Batch vector search

Support:

```text
N queries × vector dimension
```

with bounded batch size.

---

# 351. Vector batch streaming

Avoid loading unbounded query vectors.

---

# 352. Embedding pipeline

Optional:

```text
Text
→
Embedding Provider
→
Vector Search
```

Embedding provider is outside core search index.

---

# 353. Multimodal retrieval

Vector fields can represent:

```text
text
image
audio
video
code
```

but semantic model remains external.

---

# 354. Media integration

616 assets can expose searchable metadata and embeddings.

---

# 355. Code search

Text analyzer may use:

```text
identifier tokenizer
language tokenizer
symbol index
```

---

# 356. Symbol search

Compiler can emit:

```text
symbol
file
module
type
function
```

into search index.

---

# 357. AI code retrieval

Search can combine:

```text
symbol exact
+
text
+
vector
```

---

# 358. Documentation retrieval

617/619 docs can expose:

```text
text index
vector index
metadata
```

---

# 359. Search DSL for AI agents

Typed query can expose:

```text
retrieve()
filter()
rank()
limit()
explain()
```

without arbitrary code execution.

---

# 360. Agent security

AI-generated query is treated as untrusted input.

---

# 361. Query sandbox

Agent query has:

```text
budget
allowed_indexes
allowed_fields
allowed_regions
```

---

# 362. No query privilege escalation

Changing query text cannot increase capability.

---

# 363. Search policy

639 can define:

```text
AgentSearchPolicy
```

---

# 364. Search governance

640 defines:

```text
data eligibility
classification
purpose
residency
retention
```

---

# 365. Search result provenance

AI retrieval result can include:

```text
source_asset
source_revision
index_revision
```

---

# 366. Citation support

Result can expose source references without returning restricted payload.

---

# 367. Evidence object

```text
SearchEvidence {
    asset_id
    revision
    source_location
    index_revision
}
```

---

# 368. RAG boundary

641 does not generate answers.

It only retrieves ranked evidence.

---

# 369. Query result serialization

Uses 612.

---

# 370. Network transport

631/626 can expose search API.

---

# 371. HTTP API

Optional:

```text
POST /search
GET /indexes
POST /indexes/{id}/refresh
```

HTTP mapping is not core dependency.

---

# 372. RPC API

Generated from typed search interface.

---

# 373. IPC fast path

Same-node queries can use 604.

---

# 374. Embedded mode

Search can run in-process:

```text
SearchEngine
```

without distributed runtime.

---

# 375. Local mode

Single-node index.

---

# 376. Cluster mode

Distributed shards.

---

# 377. Federation mode

Multi-cluster search.

---

# 378. Edge mode

Local read-only/search index with signed snapshot.

---

# 379. Offline edge

Search remains available from last valid index.

---

# 380. Offline freshness

Response indicates index age.

---

# 381. Index update security

Signed index manifests required for untrusted update channels.

---

# 382. Package integration

Index snapshots can be shipped in AXPK packages.

---

# 383. Immutable search bundle

Useful for:

```text
offline docs
embedded help
firmware manuals
AI local knowledge
```

---

# 384. Read-only bundle

No write path.

---

# 385. Embedded search

Can dead-strip:

```text
distributed coordinator
vector engine
aggregations
```

when unused.

---

# 386. Binary size

Search components independently linkable.

---

# 387. Compiler dead stripping

Annotations identify required features.

---

# 388. Static library boundaries

```text
libaxiom_search_core
libaxiom_search_text
libaxiom_search_vector
libaxiom_search_distributed
```

logical components; exact artifact naming platform-dependent.

---

# 389. No third-party mandatory dependency

Native core implements minimal required primitives.

---

# 390. External provider linking

Optional.

---

# 391. ABI

Stable C-compatible boundary may be provided for providers.

---

# 392. Provider isolation

Provider failure must not corrupt query engine state.

---

# 393. Resource accounting

Every major operation has resource scope:

```text
query
index_build
merge
vector_build
rerank
```

---

# 394. Budget inheritance

```text
Application
→
Service
→
Query
→
Operator
```

---

# 395. Budget exhaustion

Operator returns:

```text
ResourceExceeded
```

rather than unbounded allocation.

---

# 396. Deterministic test clock

Timeout tests use 607 deterministic scheduler.

---

# 397. Deterministic test provider

All provider APIs have fake implementation.

---

# 398. Fault injection

Inject:

```text
shard failure
segment corruption
provider timeout
network partition
index lag
query cancellation
OOM budget
GPU loss
```

---

# 399. Recovery testing

Verify:

```text
snapshot restore
replay
rebuild
replica promotion
```

---

# 400. Security testing

Test:

```text
tenant escape
field leakage
facet leakage
cursor tampering
query injection
provider privilege escalation
```

---

# 401. Governance testing

Test:

```text
classification filter
residency filter
retention state
policy revision invalidation
governance drift
```

---

# 402. Distributed correctness

Test:

```text
duplicate shard
stale replica
split brain
partial response
late response
retry
```

---

# 403. Ranking correctness

Test:

```text
BM25
vector metric
RRF
weighted hybrid
tie-breaking
```

---

# 404. Approximation correctness

Verify:

```text
approximate=true
```

whenever ANN is used.

---

# 405. Query determinism

Same snapshot + same query:

```text
same ordering
```

subject to explicitly nondeterministic provider declaration.

---

# 406. Performance targets

Target:

- low-allocation query hot path;
- bounded planner overhead;
- parallel shard execution;
- vector SIMD where available;
- GPU batching;
- incremental indexing;
- asynchronous segment merge;
- cache-aware execution;
- no mandatory GC;
- no global query mutex.

---

# 407. Scalability targets

Support:

```text
single embedded index
→
single-node multi-index
→
multi-shard cluster
→
multi-region federation
```

without changing canonical Query AST.

---

# 408. API stability

Canonical query model versioned.

---

# 409. Query compatibility

Older query AST versions can be upgraded when semantics remain equivalent.

---

# 410. Index compatibility

Index manifest version controls compatibility.

---

# 411. Analyzer compatibility

Analyzer version is part of index identity.

---

# 412. Vector compatibility

Vector metric/dimension/model metadata mandatory.

---

# 413. Governance compatibility

Index cannot be activated if governance contract is incompatible with source.

---

# 414. Activation transaction

```text
Build
→ Validate
→ GovernanceCheck
→ SecurityCheck
→ Warm
→ Activate
```

---

# 415. Rollback

```text
Deactivate new
→
restore old alias
```

without rebuilding old index.

---

# 416. Disaster recovery

Index can be rebuilt from authoritative source.

---

# 417. Search DR priority

Search index itself may be disposable if rebuild cost is acceptable.

---

# 418. Durable index

For expensive indexes:

```text
snapshot
+
replica
```

---

# 419. Source/index separation

This permits:

```text
data loss of index
```

without:

```text
data loss of source
```

---

# 420. Architecture invariant set

Core invariants:

1. Index is not authoritative by default.
2. Query is typed.
3. Query plan is bounded.
4. Query cancellation propagates.
5. Query deadline propagates.
6. Unauthorized documents cannot leak through fields.
7. Unauthorized documents cannot leak through counts when policy forbids existence disclosure.
8. Governance filters cannot be bypassed.
9. Tenant boundaries cannot be bypassed.
10. Cursor is context-bound.
11. Index generation is immutable.
12. Analyzer version is bound to index generation.
13. Vector dimension is fixed.
14. Vector metric is explicit.
15. ANN approximation is declared.
16. Exact search cannot silently degrade to approximate.
17. Hybrid score normalization is explicit.
18. Equal scores have deterministic tie-breaking.
19. Distributed merge preserves requested ordering.
20. Partial results require explicit permission.
21. Provider capabilities are declared.
22. Unsupported features fail rather than silently changing semantics.
23. Query budgets are enforced.
24. Aggregation buckets are bounded.
25. Regex/wildcard expansion is bounded.
26. Vector candidate count is bounded.
27. Result size is bounded.
28. Index build resources are bounded.
29. Segment corruption is detected.
30. Incomplete merges are not activated.
31. Index snapshots are verifiable.
32. Rebuild can recover from source.
33. Policy revision participates in cache validity.
34. Governance revision participates in cache validity.
35. Tenant context participates in cache isolation.
36. Query fingerprints do not expose raw sensitive query text.
37. Search logs avoid raw sensitive payload by default.
38. Index metadata does not contain secrets.
39. External providers cannot gain implicit capabilities.
40. Provider failures cannot corrupt core state.
41. Search does not require an external search engine.
42. Search does not require GC.
43. Query execution does not require arbitrary scripting.
44. Distributed search does not require global transaction.
45. Residency constraints are honored before cross-region result export.
46. Data classification is not inferred as authoritative without declaration.
47. RAG retrieval does not itself generate answers.
48. Search result provenance is available when requested.
49. Query replay can bind to a snapshot.
50. Security enforcement remains with 603.
51. Policy decision remains with 639.
52. Data governance remains with 640.
53. Storage remains with 611.
54. Distributed data remains with 628.
55. Placement remains with 635.
56. Compute execution remains with 630.

---

# 421. Acceptance criteria

Implementation target:

**≥500 acceptance criteria**

covering:

- index creation;
- index lifecycle;
- field types;
- analyzers;
- Unicode;
- inverted index;
- positional search;
- Boolean queries;
- phrase queries;
- wildcard;
- fuzzy search;
- range queries;
- numeric indexes;
- geo indexes;
- aggregations;
- facets;
- sorting;
- pagination;
- cursor;
- vector search;
- ANN;
- exact search;
- hybrid retrieval;
- RRF;
- ranking;
- reranking;
- filtering;
- query planning;
- optimization;
- distributed execution;
- shard routing;
- replication;
- consistency;
- freshness;
- caching;
- snapshots;
- recovery;
- rebuild;
- migration;
- governance;
- security;
- multi-tenancy;
- federation;
- edge;
- offline;
- GPU;
- AI retrieval;
- observability;
- resource governance;
- fault injection;
- fuzzing;
- deterministic replay;
- external providers;
- ABI;
- compiler integration;
- dead stripping.

---

# 422. Profiles

```text
AXSEARCH_NONE
AXSEARCH_LOCAL
AXSEARCH_TEXT
AXSEARCH_STRUCTURED
AXSEARCH_GEO
AXSEARCH_VECTOR
AXSEARCH_HYBRID
AXSEARCH_ANALYTICS
AXSEARCH_DISTRIBUTED
AXSEARCH_FEDERATED
AXSEARCH_EDGE
AXSEARCH_AI
AXSEARCH_FULL
```

---

# 423. Minimal embedded profile

`AXSEARCH_LOCAL`:

```text
structured
text
basic ranking
basic filtering
```

Không cần:

```text
distributed
GPU
vector
federation
```

---

# 424. AI retrieval profile

`AXSEARCH_AI`:

```text
vector
hybrid
metadata filtering
RRF
reranking boundary
provenance
evidence
```

---

# 425. Full profile

`AXSEARCH_FULL`:

```text
text
structured
geo
vector
hybrid
distributed
federated
GPU
analytics
governance
AI retrieval
external providers
```

---

# 426. Final architecture

```text
                    ┌─────────────────────┐
                    │      Application    │
                    └──────────┬──────────┘
                               │
                         Search Query
                               │
                    ┌──────────▼──────────┐
                    │      BOOTSTRAP-641 │
                    │   Search Runtime   │
                    ├─────────────────────┤
                    │ Query AST           │
                    │ Type Checker        │
                    │ Optimizer           │
                    │ Planner             │
                    │ Executor            │
                    │ Lexical Index       │
                    │ Vector Index        │
                    │ Hybrid Ranker       │
                    │ Aggregator          │
                    │ Cache               │
                    │ Distributed Merge    │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
        628                  640                  639
 Distributed Data      Data Governance       Policy Decision
          │                    │                    │
          └────────────┬───────┴────────────┬───────┘
                       ▼                    ▼
                     603                  635
                 Capability             Placement
                   Security             Scheduling
                       │                    │
                       └──────────┬─────────┘
                                  ▼
                              630 Compute
```

---

# 427. Architectural outcome

Sau BOOTSTRAP-641, Axiom có một search stack native hoàn chỉnh:

```text
Structured Data
      ↓
Indexing
      ↓
Lexical Search
      ↓
Vector Search
      ↓
Hybrid Retrieval
      ↓
Ranking
      ↓
Distributed Query
      ↓
Governance
      ↓
Policy
      ↓
Secure Result
```

và đặc biệt:

```text
                    Axiom
                      │
          ┌───────────┴────────────┐
          │                        │
      Traditional               AI/RAG
       Search                    Search
          │                        │
      BM25/Filter              Vector
      Facet/Geo                Hybrid
      Aggregate                Rerank
          │                        │
          └───────────┬────────────┘
                      ▼
                 Same Query AST
```

Điều này giúp Axiom không cần tạo một hệ thống search riêng cho AI. **Search truyền thống và semantic retrieval sử dụng chung execution infrastructure.**

**BOOTSTRAP-641 = COMPLETE**

**Task tiếp theo: BOOTSTRAP-642 — Native Distributed Analytics, OLAP, Columnar Execution, Vectorized Processing, DataFrame, SQL Analytics, Window Functions & Large-Scale Analytical Query Runtime 5.0.**
:::