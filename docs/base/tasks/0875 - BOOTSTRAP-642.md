Tiếp tục với **BOOTSTRAP-642 — Native Distributed Analytics, OLAP, Columnar Execution, Vectorized Processing, DataFrame, SQL Analytics, Window Functions & Large-Scale Analytical Query Runtime 5.0**.

:::writing{variant="document" id="74126" title="BOOTSTRAP-642 — Native Distributed Analytics, OLAP, Columnar Execution, Vectorized Processing, DataFrame, SQL Analytics, Window Functions & Large-Scale Analytical Query Runtime 5.0"}
# BOOTSTRAP-642
## Native Distributed Analytics, OLAP, Columnar Execution, Vectorized Processing, DataFrame, SQL Analytics, Window Functions & Large-Scale Analytical Query Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Analytical Query & Vectorized Data Processing Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-641

---

# 1. Mục tiêu

BOOTSTRAP-642 bổ sung analytical execution engine native cho Axiom.

Mục tiêu là hỗ trợ:

- OLAP;
- columnar storage/execution;
- vectorized execution;
- DataFrame;
- relational analytical queries;
- SQL-compatible query boundary;
- group-by;
- aggregation;
- joins;
- window functions;
- sorting;
- partitioning;
- analytical scans;
- time-series analysis;
- approximate analytics;
- distributed aggregation;
- distributed joins;
- large dataset processing;
- batch analytics;
- streaming-to-analytics bridge;
- materialized analytical views;
- column statistics;
- predicate/projection pushdown;
- parallel CPU execution;
- SIMD;
- GPU acceleration boundary.

641 tập trung vào **retrieval/search**.

642 tập trung vào **tính toán trên lượng dữ liệu lớn**.

---

# 2. Architectural boundary

| Layer | Responsibility |
|---|---|
| 611 | durable storage |
| 612 | schema/serialization |
| 628 | distributed data |
| 634 | event/stream |
| 640 | governance |
| 641 | search/retrieval |
| **642** | analytical execution |
| 630 | distributed compute |
| 635 | placement |
| 606 | resource governance |

642 không thay thế:

- 611 storage;
- 628 distributed storage;
- 641 search;
- 630 general distributed compute.

642 là **query/execution engine chuyên cho analytical workloads**.

---

# 3. Core principles

1. Columnar execution là first-class.
2. Vectorized execution là mặc định cho analytical workloads.
3. Row-oriented data vẫn được hỗ trợ.
4. Query plan phải typed.
5. Logical plan tách khỏi physical plan.
6. Execution phải streaming/chunked.
7. Không yêu cầu toàn bộ dataset nằm trong RAM.
8. Aggregation phải có bounded-memory mode.
9. Distributed execution phải deterministic khi semantics yêu cầu.
10. Partial aggregation được ưu tiên.
11. Predicate pushdown được ưu tiên.
12. Projection pushdown được ưu tiên.
13. Statistics không được làm thay đổi semantics.
14. Approximate analytics phải khai báo approximation.
15. GPU là acceleration provider, không phải dependency.
16. SQL là compatibility boundary, không phải semantic foundation.
17. DataFrame là typed API, không phải dynamic scripting system.
18. Không bắt buộc GC.
19. Không yêu cầu Python.
20. Không yêu cầu pandas/Polars/Arrow/Spark/DuckDB.
21. External engines chỉ là provider/adaptor.

---

# 4. Architecture

```text id="n7y9k2"
                 Analytical Query
                       │
              ┌────────▼────────┐
              │ Parser / DSL    │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Logical Planner │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Optimizer       │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Physical Plan   │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Column Scan   Join       Aggregate
          │            │            │
          └────────────┼────────────┘
                       ▼
                Vectorized Runtime
                       │
              ┌────────▼────────┐
              │ Local Executor  │
              └────────┬────────┘
                       │
                 Distributed
                  Exchange
                       │
              ┌────────▼────────┐
              │ Global Merge    │
              └────────┬────────┘
                       │
                  Result/DataFrame
```

---

# 5. Core objects

```text id="9kbr3p"
AnalyticsEngine
AnalyticalQuery
LogicalPlan
PhysicalPlan
PlanNode
ExecutionContext
DataFrame
Column
ColumnBatch
RowBatch
Schema
Expression
Predicate
Aggregate
Window
Join
Sort
Partition
Exchange
Statistics
DataSource
DataSink
MaterializedView
```

---

# 6. DataFrame

Axiom DataFrame là typed collection of columns.

```text id="w6v2at"
DataFrame<TSchema> {
    schema
    columns
    row_count
}
```

Không yêu cầu runtime reflection.

---

# 7. Column

```text id="8rj1gy"
Column<T> {
    values
    validity
}
```

---

# 8. Nullable values

Không sử dụng sentinel value.

Column có:

```text id="tr4k3f"
values
validity_bitmap
```

---

# 9. Null semantics

Analytics engine dùng three-valued logic:

```text id="y5r7od"
TRUE
FALSE
UNKNOWN
```

---

# 10. Column types

Native:

```text id="qg0v3x"
Bool
I8/I16/I32/I64/I128
U8/U16/U32/U64/U128
F16/F32/F64
Decimal
Date
Time
Timestamp
Duration
String
Bytes
UUID
Struct
List
Map
```

---

# 11. Decimal

Decimal cần:

```text id="l5p7ez"
precision
scale
```

và phải detect overflow.

---

# 12. Timestamp

Timestamp dùng integer tick + timezone metadata.

---

# 13. Dictionary encoding

String columns có thể dictionary-encode:

```text id="6i3x2h"
dictionary
indices
```

---

# 14. Run-length encoding

Các column có repetition cao có thể dùng RLE.

---

# 15. Bit-packed encoding

Boolean/low-cardinality integers có thể bit-pack.

---

# 16. Delta encoding

Monotonic/numeric columns hỗ trợ delta encoding.

---

# 17. Column chunks

Column không nhất thiết lưu liên tục toàn bộ dataset.

```text id="v6x7dr"
Column
 → Chunk
 → Chunk
 → Chunk
```

---

# 18. Chunk size

Execution chunk có configurable target:

```text id="u7p4v3"
1K–64K rows
```

implementation có thể tự điều chỉnh.

---

# 19. Vectorized execution

Operators xử lý nhiều rows mỗi lần.

Không:

```text id="5t8wqm"
for row:
    virtual_call()
```

trong hot path.

---

# 20. Vector batch

```text id="9x3d0w"
VectorBatch {
    columns
    row_count
    selection
}
```

---

# 21. Selection vector

Filter có thể tạo:

```text id="z5o9v2"
selected row IDs
```

thay vì copy toàn bộ columns.

---

# 22. Predicate evaluation

Predicate trả:

```text id="v4s0pz"
BooleanMask
```

---

# 23. Predicate composition

```text id="2m9v4a"
AND
OR
NOT
```

vectorized.

---

# 24. Predicate pushdown

```text id="j2r0fw"
Filter
→
Scan
```

được đẩy xuống source khi có thể.

---

# 25. Projection pushdown

Chỉ đọc các column cần thiết.

---

# 26. Column pruning

Optimizer loại bỏ column không sử dụng.

---

# 27. Constant folding

```text id="7s0y2p"
2 * 3
```

được compile thành:

```text
6
```

---

# 28. Expression engine

Expressions:

```text id="g0k2tm"
Literal
ColumnRef
Unary
Binary
Cast
Function
Case
Coalesce
AggregateRef
WindowRef
```

---

# 29. Typed expressions

Expression có static type.

---

# 30. Function registry

Built-in functions:

```text id="3t6n8v"
math
string
date/time
conditional
aggregate
window
array
map
```

---

# 31. Deterministic function metadata

Function khai báo:

```text id="m1o5sk"
deterministic
pure
null_behavior
overflow_behavior
```

---

# 32. Volatile functions

Ví dụ:

```text id="qj8y6f"
random()
now()
```

phải được đánh dấu volatile.

---

# 33. Distributed semantics

`now()` phải có explicit execution-time semantics.

---

# 34. Query plan

```text id="a6w5y8"
LogicalPlan
→
OptimizedLogicalPlan
→
PhysicalPlan
```

---

# 35. Logical operators

```text id="f4c8jw"
Scan
Filter
Project
Join
Aggregate
Window
Sort
Distinct
Union
Intersect
Except
Limit
Offset
Exchange
```

---

# 36. Physical operators

```text id="6u1yqb"
ColumnScan
FilterExec
ProjectExec
HashJoinExec
MergeJoinExec
HashAggregateExec
SortAggregateExec
WindowExec
SortExec
TopKExec
ExchangeExec
ShuffleExec
BroadcastExec
```

---

# 37. Scan

Scan metadata:

```text id="v8r1m5"
source
schema
partition
projection
predicate
```

---

# 38. File scan

Supports:

```text id="0h8n9e"
AX columnar format
Parquet provider
ORC provider
CSV
JSON
```

CSV/JSON are ingestion formats, not preferred analytical representation.

---

# 39. Native columnar format

Axiom native format:

```text id="3s6q1e"
AXCOL
```

---

# 40. AXCOL

Logical structure:

```text id="p2d7az"
Header
Schema
RowGroups
ColumnChunks
Statistics
Footer
Checksum
```

---

# 41. Row group

Each row group stores:

```text id="5m2k0x"
row_count
column_chunks
min/max
null_count
encoding
compression
```

---

# 42. Statistics

Statistics enable pruning.

---

# 43. Min/max pruning

If predicate:

```text id="7x1p9c"
age > 100
```

and row group max age = 80:

skip row group.

---

# 44. Null count

Used for:

```text id="2r4y6j"
IS NULL
IS NOT NULL
```

---

# 45. Distinct count

Optional.

---

# 46. Bloom filter

Optional per column chunk.

---

# 47. Partition pruning

Partitions can be eliminated before scan.

---

# 48. Partition expressions

Example:

```text id="w8k3t2"
year
month
tenant
region
```

---

# 49. Partition pruning safety

Pruning may only occur if predicate implication is proven.

---

# 50. Storage integration

AXCOL stored through 611.

---

# 51. Serialization

612 defines schema and canonical encoding metadata.

---

# 52. Compression

613 supplies compression providers.

---

# 53. Encryption

610/638 supply encryption/key management.

---

# 54. Distributed data

628 provides:

```text id="b3y7nq"
partition
replica
revision
```

---

# 55. Analytics over replicated data

Query may specify:

```text id="c9j2v1"
local
session
causal
quorum
```

depending source.

---

# 56. Freshness

Analytics query can require:

```text id="r4y8c0"
max_data_lag
```

---

# 57. Scan consistency

Result metadata records data revisions used.

---

# 58. Aggregation

Basic:

```text id="x8m2c5"
COUNT
SUM
MIN
MAX
AVG
```

---

# 59. Statistical aggregates

```text id="t4z6p1"
STDDEV
VARIANCE
MEDIAN
QUANTILE
```

---

# 60. Approximate aggregates

Optional:

```text id="n7q2b8"
ApproxDistinct
ApproxQuantile
```

Must declare approximation.

---

# 61. Group by

```text id="u3k5d9"
GROUP BY column
```

---

# 62. Multi-key group

```text id="j5p1w6"
GROUP BY region, year, month
```

---

# 63. Hash aggregation

Default for unsorted data.

---

# 64. Sort aggregation

Useful when input is ordered.

---

# 65. Partial aggregation

Distributed execution:

```text id="e7c3m9"
local aggregate
→
shuffle/group
→
global aggregate
```

---

# 66. Aggregate state

Each aggregate has:

```text id="v5f8q2"
init
update
merge
finalize
```

---

# 67. Custom aggregate

Axiom functions can define typed aggregate states.

---

# 68. Aggregate safety

Custom aggregate must declare resource requirements.

---

# 69. Window functions

Support:

```text id="x3n7k1"
ROW_NUMBER
RANK
DENSE_RANK
LAG
LEAD
FIRST_VALUE
LAST_VALUE
SUM
AVG
MIN
MAX
```

---

# 70. Window specification

```text id="m8q2v4"
PARTITION BY
ORDER BY
FRAME
```

---

# 71. Window frames

```text id="f3p7s9"
ROWS
RANGE
GROUPS
```

---

# 72. Frame boundaries

```text id="r6w1k4"
UNBOUNDED PRECEDING
N PRECEDING
CURRENT ROW
N FOLLOWING
UNBOUNDED FOLLOWING
```

---

# 73. Window determinism

ORDER BY must be deterministic when result ordering matters.

---

# 74. Ranking functions

Tie semantics explicit.

---

# 75. Time windows

Support:

```text id="k4v7n2"
Tumbling
Sliding
Session
```

---

# 76. Event-time analytics

634 event timestamps can be used.

---

# 77. Watermarks

642 can consume 634 watermarks for bounded-lateness analytics.

---

# 78. Late data

Policies:

```text id="y8p2d4"
Drop
Update
Recompute
SideOutput
```

---

# 79. Stream-to-table bridge

634 streams can materialize analytical tables.

---

# 80. Materialized view

```text id="h2m6q8"
MaterializedView {
    definition
    source_revision
    refresh_policy
}
```

---

# 81. View refresh

Modes:

```text id="s4n7x1"
Manual
Scheduled
Incremental
EventDriven
```

---

# 82. Incremental materialized view

Uses:

```text id="b8c3r5"
634 events
628 change feeds
```

---

# 83. View consistency

Explicit:

```text id="w6j2m9"
Strong
NearRealTime
Eventual
```

---

# 84. Query rewrite

Optimizer may replace:

```text id="a5x8v3"
base tables
```

with:

```text id="p9m4k7"
materialized view
```

only when equivalence is proven.

---

# 85. Join

Supported:

```text id="n3v7b2"
INNER
LEFT
RIGHT
FULL
CROSS
SEMI
ANTI
```

---

# 86. Join algorithms

```text id="c5x8m1"
HashJoin
MergeJoin
NestedLoopJoin
IndexJoin
```

---

# 87. Join selection

Optimizer uses:

```text id="z2q6f4"
cardinality
statistics
ordering
memory
partitioning
```

---

# 88. Hash join

Build smaller side when safe.

---

# 89. Spill-to-disk

Large hash tables may spill through 611.

---

# 90. External sort

Sort can spill to disk.

---

# 91. Sort runs

```text id="r5j8k2"
memory batch
→
sorted run
→
disk
```

---

# 92. Merge sort

Sorted runs merge incrementally.

---

# 93. Memory budget

Every operator receives budget from 606.

---

# 94. Out-of-memory behavior

Engine should:

```text id="v3m6p9"
spill
reduce parallelism
or fail boundedly
```

rather than uncontrolled allocation.

---

# 95. Exchange

Distributed operators:

```text id="k7d2x5"
Broadcast
HashPartition
RangePartition
RoundRobin
Gather
```

---

# 96. Shuffle

Shuffle uses 604/630 transport.

---

# 97. Shuffle spill

Large shuffle data may be stored via 611.

---

# 98. Shuffle compression

613 provider.

---

# 99. Shuffle encryption

610 provider where required.

---

# 100. Partitioning

Hash partition:

```text id="b4r7m2"
hash(key) % N
```

---

# 101. Range partition

Uses ordered boundaries.

---

# 102. Adaptive partitioning

Optional planner feature.

---

# 103. Data skew

Statistics identify potential skew.

---

# 104. Skew mitigation

Strategies:

```text id="t5q8v1"
salting
broadcast
split-heavy-key
adaptive repartition
```

---

# 105. Broadcast join

Small relation replicated to workers.

---

# 106. Broadcast budget

Must be bounded by resource policy.

---

# 107. Distributed aggregate

Coordinator merges partial states.

---

# 108. Associativity

Parallel aggregate requires explicit merge semantics.

---

# 109. Floating-point aggregation

Order can affect result.

Axiom must expose:

```text id="x6n2p4"
deterministic
reproducible
provider-defined
```

semantics.

---

# 110. Deterministic decimal aggregation

Decimal arithmetic should be deterministic across workers.

---

# 111. Numeric overflow

Operations detect overflow according to type policy.

---

# 112. Arithmetic policy

```text id="g4m7z2"
Checked
Saturating
Wrapping
```

must be explicit.

---

# 113. Vectorized math

Built-in SIMD kernels:

```text id="q8v1m5"
add
subtract
multiply
divide
sqrt
exp
log
sin
cos
```

where platform supports.

---

# 114. SIMD backend

Compiler selects:

```text id="n5j2k7"
SSE
AVX2
AVX-512
NEON
SVE
```

as target permits.

---

# 115. Scalar fallback

Required.

---

# 116. CPU dispatch

Runtime can select ISA-specific kernel.

---

# 117. GPU execution

Optional GPU backend through 614.

---

# 118. GPU operators

Potential:

```text id="f7p3x9"
filter
projection
aggregation
sort
join
vector math
```

---

# 119. GPU transfer cost

Planner must account for CPU↔GPU transfer.

---

# 120. GPU fallback

Explicit provider policy.

---

# 121. DataFrame API

```text id="e5q2n8"
df.select(...)
df.filter(...)
df.group_by(...)
df.aggregate(...)
df.join(...)
df.sort(...)
df.window(...)
```

---

# 122. Lazy DataFrame

Operations build logical plan.

Execution occurs at terminal operation.

---

# 123. Eager DataFrame

Optional convenience mode.

---

# 124. Terminal operations

```text id="x7m3c1"
collect
execute
write
stream
explain
```

---

# 125. Typed DataFrame

Schema known statically when possible.

---

# 126. Dynamic DataFrame

Runtime schema supported for imported datasets.

---

# 127. DataFrame schema evolution

Compatible additions may be handled explicitly.

---

# 128. Schema mismatch

Must produce typed error.

---

# 129. SQL compatibility

Optional SQL parser:

```text id="p2v8n5"
SQL
→
LogicalPlan
```

---

# 130. SQL semantics

Axiom canonical semantics remain defined by typed logical plan.

---

# 131. SQL dialect

Axiom should define a documented compatibility subset.

---

# 132. No SQL injection

Parameterized expressions required for dynamic SQL.

---

# 133. Query parameters

```text id="h4k7q1"
$1
$2
```

or typed named parameters.

---

# 134. Prepared analytical query

Plan may be reused with parameter values.

---

# 135. Plan cache

Key includes:

```text id="m3x6v9"
query_shape
schema_fingerprint
optimizer_version
statistics_revision
```

---

# 136. Statistics revision

Changing statistics can invalidate plan cache.

---

# 137. Cost-based optimizer

Optional but supported.

---

# 138. Rule-based optimizer

Mandatory baseline.

---

# 139. Optimization rules

```text id="y6p1r4"
predicate_pushdown
projection_pushdown
constant_fold
filter_merge
join_reorder
aggregate_pushdown
limit_pushdown
partition_pruning
```

---

# 140. Join reorder

For N joins, optimizer may use dynamic programming or bounded greedy search.

---

# 141. Optimizer budget

Planning itself has resource limits.

---

# 142. Query complexity

Limit:

```text id="v8n3k6"
max_nodes
max_joins
max_expression_depth
```

---

# 143. Query admission

639 can reject expensive analytical plans.

---

# 144. Workload classes

```text id="q4m7x2"
Interactive
BI
Batch
ETL
Materialization
Maintenance
```

---

# 145. Scheduling

607 + 606 coordinate CPU execution.

---

# 146. Priority

Interactive analytics may receive separate resource pool.

---

# 147. Concurrency

Per-query and global concurrency limits.

---

# 148. Fairness

Tenant/workload fairness.

---

# 149. Query cancellation

Cancellation propagates to all workers.

---

# 150. Query deadline

Distributed operators inherit deadline.

---

# 151. Partial analytics

Request may permit partial output.

Response must indicate:

```text id="g8v2n5"
partial=true
```

---

# 152. Exact analytics

Default for ordinary aggregations unless approximate operator selected.

---

# 153. Approximation

Every approximate result includes:

```text id="m1x7q4"
approximation_type
error_bound?
```

when known.

---

# 154. Approximate distinct

Can use HyperLogLog.

---

# 155. Approximate quantile

Can use t-digest/KLL boundary.

---

# 156. Approximate sampling

Optional:

```text id="z5r2p8"
Bernoulli
Reservoir
Stratified
```

---

# 157. Sampling metadata

Result records sampling fraction/method.

---

# 158. Time-series functions

```text id="q7m3v1"
date_bucket
lag
lead
moving_average
rate
delta
```

---

# 159. Time-series partitioning

Time-based partition pruning.

---

# 160. Time-series compression

Delta/RLE/dictionary compression.

---

# 161. Gap filling

Optional:

```text id="x4n8p2"
generate missing time buckets
```

---

# 162. Interpolation

Must be explicit.

---

# 163. Pivot

```text id="m8q5v3"
pivot(column)
```

---

# 164. Unpivot

```text id="r2k7x9"
unpivot(...)
```

---

# 165. Set operations

```text id="v5p1m8"
UNION
UNION ALL
INTERSECT
EXCEPT
```

---

# 166. Duplicate semantics

Explicit.

---

# 167. Distinct

Hash-based or sort-based.

---

# 168. Top-K

Use bounded heap where possible.

---

# 169. Limit pushdown

Safe when ordering semantics permit.

---

# 170. Sampling pushdown

Only when semantics permit.

---

# 171. Predicate equivalence

Optimizer must preserve null and three-valued semantics.

---

# 172. Null-aware joins

Correct NULL behavior required.

---

# 173. Null-aware aggregation

COUNT(*) differs from COUNT(column).

---

# 174. Empty input

Every aggregate defines empty-set result.

---

# 175. Schema metadata

Analytics schema contains:

```text id="g3x8m5"
name
type
nullable
encoding
statistics
governance
```

---

# 176. Governance integration

640 metadata propagates into analytical plans.

---

# 177. Residency

Analytics cannot silently move restricted data across regions.

---

# 178. Classification

Output classification may inherit highest relevant input classification.

---

# 179. Aggregation privacy

Aggregation can still leak sensitive information.

Policy can impose minimum group size.

---

# 180. Minimum group size

Example:

```text id="x6p2m8"
GROUP BY region
HAVING population >= policy.minimum_group_size
```

must be policy-enforced where configured.

---

# 181. Differential privacy boundary

Optional provider:

```text id="d8m4q1"
Noise
PrivacyBudget
Epsilon
Delta
```

---

# 182. Privacy accounting

If enabled, privacy budget is tracked outside ordinary resource budget.

---

# 183. No implicit privacy noise

Results must not silently become approximate/private.

---

# 184. Security

603 capabilities required for:

```text id="q5v9m2"
read dataset
write result
export
cross-region
GPU
```

---

# 185. Data export

642 can write:

```text id="p7x3n6"
AXCOL
CSV
JSON
Parquet
```

subject to governance.

---

# 186. Export policy

639 + 640 evaluate:

```text id="m2r8v5"
purpose
destination
fields
classification
region
```

---

# 187. Result sink

```text id="f4n7q2"
FileSink
TableSink
StreamSink
NetworkSink
MaterializedViewSink
```

---

# 188. Atomic analytical output

Write to temporary generation, then activate.

---

# 189. Checkpoint

Long analytical jobs can checkpoint:

```text id="v8m3p6"
operator state
source positions
shuffle state
```

---

# 190. Workflow integration

629 can run durable analytics jobs.

---

# 191. Compute integration

630 can provision workers.

---

# 192. Cluster placement

635 handles placement.

---

# 193. Event integration

634 can trigger analytics refresh.

---

# 194. Distributed state

628 stores checkpoints/materialized state.

---

# 195. Failure recovery

Worker failure:

```text id="q3x7n5"
retry
restore checkpoint
recompute partition
```

---

# 196. Exactly-once

Analytics computation may be deterministic, but external sink exactly-once is not assumed.

---

# 197. Idempotent sink

Recommended using:

```text id="h6m2v9"
job_id
partition_id
attempt
output_generation
```

---

# 198. Output commit

Only successful job generation becomes visible.

---

# 199. Job identity

```text id="x2r7m4"
AnalyticsJobId
ExecutionId
Attempt
```

---

# 200. Job state

```text id="k8p3v1"
Pending
Running
Checkpointing
Recovering
Completed
Failed
Cancelled
```

---

# 201. Analytics service

642 can expose:

```text id="m5q2x8"
AnalyticsEngine
```

as service through 631.

---

# 202. Remote DataFrame

DataFrame plan can be serialized and executed remotely.

---

# 203. Plan serialization

Uses 612.

---

# 204. Plan fingerprint

```text id="r7v3m1"
hash(normalized_logical_plan)
```

---

# 205. Execution fingerprint

Includes:

```text id="p2x8q5"
plan
data revisions
optimizer version
provider versions
```

---

# 206. Explain

```text id="f6m3v9"
explain(logical_plan)
explain(physical_plan)
```

---

# 207. Explain output

Includes:

```text id="v2q7m5"
operator tree
estimated rows
estimated cost
partition count
memory
parallelism
```

---

# 208. Runtime profile

Includes:

```text id="n8x3p1"
actual rows
operator time
CPU
memory
spill
shuffle
cache
```

---

# 209. Metrics

633 metrics:

```text id="g4m7v2"
query_count
query_latency
scan_bytes
rows_scanned
rows_output
shuffle_bytes
spill_bytes
CPU_time
GPU_time
```

---

# 210. Query cardinality metrics

Avoid exposing raw sensitive values as labels.

---

# 211. Logs

602 structured logs.

---

# 212. Tracing

Span hierarchy:

```text id="q6v2m8"
query
→ stage
→ task
→ operator
```

---

# 213. Resource accounting

606 tracks:

```text id="x5r8n3"
CPU
RAM
disk
IO
network
GPU
spill
```

---

# 214. Memory allocator

Analytics can use:

```text id="m2p7v4"
Arena
Pool
ScratchBuffer
```

per query/operator.

---

# 215. Arena lifetime

Arena belongs to query/stage.

---

# 216. No GC

Temporary objects are freed by arena scope.

---

# 217. Reference semantics

Column buffers use generation-safe handles/views rather than pervasive raw pointers.

---

# 218. Zero-copy

Where possible:

```text id="v8q3m1"
storage
→
mmap
→
column view
```

---

# 219. Memory mapping

611 provides mmap.

---

# 220. Cache-aware execution

Column chunks should fit cache-friendly processing batches.

---

# 221. SIMD alignment

Native column buffers can request alignment.

---

# 222. String processing

String columns may use:

```text id="p6m2x9"
offsets
values
validity
```

---

# 223. String vectorization

Common operations:

```text id="g3v7n5"
contains
starts_with
ends_with
lower
upper
length
substring
```

---

# 224. Unicode correctness

617 semantics remain authoritative.

---

# 225. Locale-aware operations

Explicit locale required.

---

# 226. Collation

Sorting strings can specify:

```text id="x5q8m2"
Binary
Unicode
Locale
```

---

# 227. Deterministic collation

Binary/Unicode-defined collation preferred for reproducible distributed results.

---

# 228. Join collation

Join key comparison semantics must match.

---

# 229. Data source abstraction

```text id="n7m3v8"
DataSource.scan(plan)
```

---

# 230. Native source providers

```text id="q2x6p4"
AXCOL
612 collections
628 datasets
641 indexes
634 materialized streams
```

---

# 231. External source providers

Optional:

```text id="v5r8m1"
PostgreSQL
MySQL
SQLite
Parquet
ObjectStorage
```

---

# 232. Pushdown contract

External source advertises:

```text id="m8p3x7"
predicate
projection
limit
aggregate
sort
```

support.

---

# 233. Pushdown correctness

Provider must not claim unsupported semantics.

---

# 234. Federation

Analytics can combine multiple sources.

---

# 235. Cross-source join

Explicitly enabled and budgeted.

---

# 236. Source credentials

638 manages credentials.

---

# 237. Secret isolation

Credentials never appear in query plans.

---

# 238. Query plan security

Serialized plan must not contain secret material.

---

# 239. Prepared statement

External credentials remain provider-side.

---

# 240. Cache security

Plans containing provider identifiers remain tenant/context isolated where required.

---

# 241. DataFrame serialization

Schema + logical plan can be serialized.

---

# 242. Lazy plan portability

A lazy DataFrame can be shipped to worker.

---

# 243. Plan versioning

Optimizer/version compatibility required.

---

# 244. Unsupported plan

Worker rejects incompatible physical plan and can re-plan from logical plan.

---

# 245. Adaptive execution

Optional:

```text id="p7m2x6"
runtime cardinality
→
reoptimize
```

---

# 246. Adaptive execution safety

Must preserve semantics.

---

# 247. Adaptive join

Can switch:

```text id="q3v8m1"
broadcast
↔
shuffle
```

if policy permits.

---

# 248. Adaptive partitioning

Can split skewed partitions.

---

# 249. Runtime statistics

Operators produce bounded statistics.

---

# 250. Statistics storage

612/628 can store table/column statistics.

---

# 251. Statistics freshness

Statistics have:

```text id="m5x8p2"
revision
timestamp
source_revision
```

---

# 252. Stale statistics

Optimizer may use them only within configured tolerance.

---

# 253. Statistics privacy

Statistics can leak data characteristics.

Governance applies.

---

# 254. Statistics security

Restricted datasets may prohibit global statistics.

---

# 255. Table statistics

```text id="v2q6m9"
row_count
null_count
distinct_count
min
max
histogram
```

---

# 256. Histogram

Supported:

```text id="r7p3x5"
EquiDepth
EquiWidth
TDigest boundary
```

---

# 257. Histogram boundedness

Maximum buckets configured.

---

# 258. Query optimizer feedback

Optional runtime feedback can update statistics.

---

# 259. No self-modifying arbitrary optimizer

Optimizer updates remain declarative metadata.

---

# 260. Index integration

641 indexes can accelerate:

```text id="n6m2v8"
filter
join
sort
group
```

---

# 261. Search-to-analytics bridge

641 result IDs can feed 642 aggregation.

---

# 262. Analytics-to-search bridge

642 can generate analytical features used by 641.

---

# 263. Feature table

```text id="p5x8m2"
FeatureSet
```

can be materialized.

---

# 264. ML integration boundary

Feature computation can feed 630/GPU ML runtime.

---

# 265. Vector feature

Vector columns supported.

---

# 266. Array analytics

Operations:

```text id="v3q7m1"
array_length
array_sum
array_map
array_filter
```

subject to bounded execution.

---

# 267. Nested data

Struct/list/map columns supported.

---

# 268. Explode

```text id="m8x2p6"
explode(list)
```

---

# 269. Unnest

Nested structures can become rows.

---

# 270. Nested data explosion limits

Maximum expansion controlled by 606.

---

# 271. JSON functions

Optional JSON provider.

---

# 272. JSON extraction

Typed result preferred over dynamic object.

---

# 273. Semi-structured analytics

Supported without requiring reflection.

---

# 274. Data quality checks

Analytics can run:

```text id="q6m3v8"
null_rate
duplicate_rate
range_check
schema_check
```

---

# 275. Data quality result

```text id="x5p7m2"
QualityReport
```

---

# 276. Governance integration

Quality metadata can feed 640 but does not automatically change classification.

---

# 277. ETL boundary

642 can perform:

```text id="r3v8m1"
Extract
Transform
Aggregate
Load
```

---

# 278. Transformation provenance

640 lineage records transformations.

---

# 279. Lineage event

```text id="m7q2x5"
source
operator
output
execution
```

---

# 280. Transformation fingerprint

Hash of logical/physical transformation.

---

# 281. Materialized result lineage

Result table carries lineage metadata.

---

# 282. Retention

642-generated temporary data obeys 640 lifecycle.

---

# 283. Temporary spill

Spill files are governed as temporary derived data.

---

# 284. Spill cleanup

On successful/failure completion:

```text id="p6x3m8"
cleanup
```

must occur.

---

# 285. Crash cleanup

Supervisor/recovery cleans orphan spill files.

---

# 286. Secure spill

Restricted data spill can require encryption.

---

# 287. Compression

Spill can use 613 compression.

---

# 288. Encryption

Spill can use 610 encryption.

---

# 289. Query snapshot

Long analytical query can pin source revisions.

---

# 290. Snapshot semantics

Query may request:

```text id="v4m8p2"
consistent snapshot
```

where source supports it.

---

# 291. Snapshot isolation

Distributed source may provide MVCC snapshot via 628.

---

# 292. No universal transaction

642 does not create global distributed transactions.

---

# 293. Analytical consistency

Explicit:

```text id="q7x3m5"
Snapshot
ReadCommitted
Eventual
```

where provider supports.

---

# 294. Streaming analytics

642 can consume bounded/unbounded stream.

---

# 295. Unbounded query

Requires windowing or explicit termination.

---

# 296. Streaming aggregation

State stored in 628 when durable.

---

# 297. Streaming checkpoint

629/628 provide durable state.

---

# 298. Exactly-once streaming

Not assumed globally.

---

# 299. Idempotent aggregate update

Supported through event IDs/source revisions.

---

# 300. Watermark progression

Watermarks must be monotonic.

---

# 301. Late-event correction

Policies explicit.

---

# 302. Window closure

Window closes when watermark passes end + allowed lateness.

---

# 303. Session windows

Session gap explicit.

---

# 304. Window state limits

Per-key state budget.

---

# 305. Hot-key protection

Per-key memory and processing budget.

---

# 306. Backpressure

Streaming source receives backpressure.

---

# 307. Drop policy

Only if explicitly configured.

---

# 308. Analytics result sinks

Streaming sink:

```text id="f5m2x8"
Event
Table
File
Dashboard feed
```

---

# 309. Dashboard integration

619/622 can consume materialized analytical results.

---

# 310. GUI visualization boundary

642 computes data; 619/615 render it.

---

# 311. Chart-friendly result

Typed table with metadata.

---

# 312. Pivoted output

Optional for visualization.

---

# 313. Sampling for visualization

Explicit approximate sampling.

---

# 314. Large result protection

GUI should not request millions of rows by default.

642 enforces resource budget.

---

# 315. CLI

```text id="m8q3v1"
axiom analytics explain
axiom analytics profile
axiom analytics stats
axiom analytics execute
axiom analytics materialize
axiom analytics inspect
```

---

# 316. Compiler annotations

```text id="x4p7m2"
@analytics
@table
@column
@partition
@aggregate
@window
@materialized
@statistics
@vectorized
@gpu
@spillable
@deterministic
@approximate
```

---

# 317. Generated artifacts

```text id="q6m2v8"
.axplan
.axschema
.axstats
.axmaterialized
.axanalytics
```

---

# 318. Typed aggregate declaration

Example:

```text id="r3x8m5"
aggregate RevenueByRegion {
    input Decimal
    state Decimal
    update(state, value)
    merge(a, b)
    finalize(state)
}
```

---

# 319. Aggregate compiler checks

Compiler validates:

- state type;
- input type;
- merge signature;
- finalize signature;
- determinism metadata.

---

# 320. Window declaration

```text id="p5m7x2"
window SalesWindow {
    partition_by region
    order_by timestamp
    frame rows 30 preceding
}
```

---

# 321. Query DSL

Example:

```text id="v8q3m1"
from sales
where year >= 2025
group_by region
select region, sum(amount)
order_by sum(amount) desc
limit 20
```

---

# 322. SQL lowering

Equivalent SQL-like syntax lowers to same logical plan.

---

# 323. DataFrame lowering

DataFrame operations lower to same logical plan.

---

# 324. One semantic core

```text id="m2x7p4"
Axiom DSL
     │
SQL
     │
DataFrame
     │
API
     ▼
LogicalPlan
```

---

# 325. This avoids duplicated engines

There is one optimizer/executor.

---

# 326. External engine adapters

Could translate logical plans to:

```text id="q5v8m2"
DuckDB
Spark
Trino
ClickHouse
PostgreSQL
```

where supported.

---

# 327. Adapter semantics

Unsupported operations remain local or fail explicitly.

---

# 328. External execution security

External engine credentials/capabilities are isolated.

---

# 329. Native analytical engine

Axiom must remain fully functional without external analytical engine.

---

# 330. Binary size profiles

```text id="x7m3p5"
AXANALYTICS_NONE
AXANALYTICS_LOCAL
AXANALYTICS_COLUMNAR
AXANALYTICS_OLAP
AXANALYTICS_DATAFRAME
AXANALYTICS_SQL
AXANALYTICS_STREAM
AXANALYTICS_DISTRIBUTED
AXANALYTICS_GPU
AXANALYTICS_FULL
```

---

# 331. Minimal profile

`AXANALYTICS_LOCAL`:

- DataFrame;
- columnar;
- vectorized;
- basic aggregation;
- no cluster;
- no SQL parser;
- no GPU.

---

# 332. OLAP profile

Adds:

- distributed aggregation;
- joins;
- window functions;
- partition pruning;
- materialized views.

---

# 333. GPU profile

Adds:

- GPU column kernels;
- GPU aggregation;
- vectorized GPU execution.

---

# 334. SQL profile

Adds SQL parser/compatibility layer without changing core semantics.

---

# 335. Full profile

Includes all analytical components.

---

# 336. Error model

```text id="m5q8x2"
AnalyticsError
SchemaMismatch
TypeMismatch
NullabilityError
Overflow
DivisionByZero
UnsupportedOperation
ResourceExceeded
QueryTimeout
QueryCancelled
DataSourceUnavailable
SnapshotUnavailable
StatisticsUnavailable
JoinTooLarge
ShuffleFailure
SpillFailure
GovernanceViolation
ResidencyViolation
Unauthorized
ProviderMismatch
PlanVersionMismatch
```

---

# 337. Error propagation

Errors preserve:

```text id="x3p7m5"
query_id
stage_id
operator_id
worker_id
```

when available.

---

# 338. Fault domains

Failures can be:

```text id="q8m2v6"
operator
task
worker
node
source
sink
cluster
```

---

# 339. Recovery

Recoverable stages can retry.

---

# 340. Retry budget

Prevent infinite analytical retries.

---

# 341. Deterministic retries

Same partition should produce equivalent output when deterministic mode enabled.

---

# 342. Task attempt

```text id="v4x7m1"
TaskId
Attempt
```

---

# 343. Shuffle recovery

Shuffle data can be:

```text id="m6q3p8"
recomputed
or
persisted
```

according to profile.

---

# 344. Checkpoint strategy

```text id="x2m8v5"
None
Periodic
StageBoundary
Durable
```

---

# 345. Long-running analytics

629 durable workflow can supervise analytics job.

---

# 346. Cancellation

Cancellation is cooperative plus forced task termination when necessary.

---

# 347. Resource leak prevention

Query scope owns temporary resources.

---

# 348. File cleanup

Temporary analytical files registered with 611 cleanup manager.

---

# 349. Security boundary

No analytical operator may arbitrarily:

- execute process;
- open network connection;
- access filesystem outside capabilities;
- load native code.

---

# 350. Plugin boundary

Custom operators use 623 plugin system and 603 capabilities.

---

# 351. Custom operator

```text id="q7m3x8"
Operator {
    schema
    execute
    resource_profile
}
```

---

# 352. Operator purity

Operator declares:

```text id="m5p2v7"
Pure
Stateful
SideEffecting
```

---

# 353. Side effects

Only sink operators may normally have side effects.

---

# 354. Planner restrictions

Pure logical plans cannot contain arbitrary side-effecting operations.

---

# 355. Reproducibility

Pure analytical plan can be replayed.

---

# 356. AI-generated analytics

AI may generate logical plans.

They are treated as untrusted input.

---

# 357. AI plan limits

AI-generated query gets explicit:

```text id="x8q3m1"
dataset allowlist
column allowlist
budget
deadline
region
```

---

# 358. No privilege escalation

Query cannot alter its own budget or capabilities.

---

# 359. Query explanation for AI

Structured explain output enables an agent to inspect:

```text id="p6m2v8"
scan
filters
joins
aggregation
cost
resource estimate
```

---

# 360. AI data provenance

Results expose lineage references.

---

# 361. Search integration

641 can provide candidate IDs to 642.

---

# 362. Analytics integration

642 can produce:

- aggregates;
- statistics;
- feature tables;
- ranking features.

641 can consume them.

---

# 363. Unified analytical/search architecture

```text id="m3x7q5"
             Query
               │
        ┌──────┴──────┐
        ▼             ▼
    Retrieval      Analytics
       641            642
        │             │
        └──────┬──────┘
               ▼
        Shared Data Model
               │
      ┌────────┴────────┐
      ▼                 ▼
     628               611
```

---

# 364. Why separate 641 and 642

Search optimizes:

```text id="q8m3x5"
Top-K
latency
retrieval
ranking
```

Analytics optimizes:

```text id="v2p7m4"
scan
aggregation
joins
throughput
```

The engines share schemas and storage but optimize different workloads.

---

# 365. Shared optimizer infrastructure

Possible shared components:

```text id="x5m8q2"
Expression IR
Schema IR
Statistics
Resource model
Distributed exchange
```

---

# 366. Separate physical operators

Search:

```text id="q3v7m1"
PostingScan
VectorSearch
TopK
```

Analytics:

```text id="m6x2p8"
ColumnScan
HashJoin
Aggregate
Window
```

---

# 367. Common Axiom IR

Both can lower to common execution IR.

---

# 368. Compiler integration

Compiler may generate specialized kernels for known schemas.

---

# 369. Schema-specialized execution

Known column types permit:

```text id="p7m3x8"
static offsets
static types
specialized SIMD
```

---

# 370. No reflection dependency

Generated metadata replaces runtime reflection.

---

# 371. FFI

Stable C ABI boundary for analytical providers.

---

# 372. Platform support

Windows:

```text id="q4x8m2"
native threads
memory mapping
IOCP
```

Linux:

```text id="v7p3m5"
io_uring
mmap
NUMA
```

macOS:

```text id="m2q8x6"
mmap
native threading
```

Android/iOS:

platform sandbox constraints.

WASM:

host-provided filesystem/memory constraints.

---

# 373. NUMA

Optional NUMA-aware execution.

---

# 374. NUMA placement

Worker and data locality may be coordinated with 635.

---

# 375. Cache locality

Planner can favor partition-local execution.

---

# 376. Huge pages

Optional provider.

---

# 377. Memory alignment

Column buffers expose alignment metadata.

---

# 378. Compression-aware scan

Engine can scan compressed chunks without full decompression where codec supports it.

---

# 379. Predicate on compressed data

Optional provider optimization.

---

# 380. Storage prefetch

611 supports read-ahead hints.

---

# 381. Async scan

Storage scan integrates with 607.

---

# 382. Parallel scan

Partitions/chunks scanned concurrently.

---

# 383. Scan scheduling

606 controls IO/CPU concurrency.

---

# 384. Backpressure

Scan slows when downstream operator is full.

---

# 385. Pipeline execution

Operators can execute concurrently:

```text id="x7m2p5"
Scan
  ↓
Filter
  ↓
Project
  ↓
Aggregate
```

---

# 386. Operator fusion

Filter + projection may fuse.

---

# 387. Kernel fusion

Arithmetic expressions may fuse into one SIMD kernel.

---

# 388. Fusion correctness

Null semantics and overflow semantics preserved.

---

# 389. Branch reduction

Selection masks reduce branch-heavy loops.

---

# 390. Vectorized string operations

May use SIMD where safe.

---

# 391. Parallel aggregation

Per-worker local state then merge.

---

# 392. Lock avoidance

Per-worker aggregation avoids global hot locks.

---

# 393. Global state

Only final merge synchronizes.

---

# 394. Memory reclamation

Arena/pool lifetime.

---

# 395. Resource metrics

Each operator reports resource consumption.

---

# 396. Query profile tree

```text id="m8q2v6"
Query
 ├─ Scan
 ├─ Filter
 ├─ Join
 │   ├─ Build
 │   └─ Probe
 └─ Aggregate
```

---

# 397. Acceptance test categories

Minimum **500+ acceptance criteria** across:

1. schema;
2. nulls;
3. types;
4. columnar storage;
5. encoding;
6. compression;
7. scan;
8. predicate pushdown;
9. projection pushdown;
10. statistics;
11. partition pruning;
12. expression engine;
13. aggregation;
14. group-by;
15. joins;
16. windows;
17. sorting;
18. distinct;
19. set operations;
20. DataFrame;
21. SQL;
22. materialized views;
23. streaming analytics;
24. distributed exchange;
25. shuffle;
26. spill;
27. GPU;
28. SIMD;
29. NUMA;
30. resource governance;
31. security;
32. policy;
33. data governance;
34. lineage;
35. consistency;
36. checkpoint;
37. recovery;
38. observability;
39. AI-generated plans;
40. external providers;
41. ABI;
42. deterministic execution;
43. fault injection;
44. fuzzing;
45. performance;
46. binary-size minimization.

---

# 398. Core invariants

1. Query semantics are independent of physical plan.
2. Physical optimization cannot change logical result.
3. Null semantics are preserved.
4. Numeric overflow semantics are preserved.
5. Approximate operations declare approximation.
6. Partial results are explicitly marked.
7. Query budgets are enforced.
8. Memory allocations are bounded by operator policy.
9. Spill is governed.
10. Temporary data is cleaned.
11. Credentials never enter query plans.
12. Governance follows data movement.
13. Residency cannot be bypassed through shuffle.
14. Classification propagates according to policy.
15. Lineage is recorded for materialized transformations.
16. Source revisions are tracked.
17. Materialized views cannot claim fresher data than their source.
18. Statistics cannot alter query semantics.
19. Optimizer cannot execute arbitrary code.
20. Custom operators require explicit capability.
21. Side effects are isolated to explicit sinks.
22. Distributed retries cannot silently duplicate committed output.
23. Output activation is atomic.
24. Failed generation is never published.
25. GPU fallback is explicit.
26. SIMD fallback is mandatory.
27. External providers declare semantic capabilities.
28. Unsupported semantics fail explicitly.
29. SQL lowers to canonical logical plans.
30. DataFrame lowers to canonical logical plans.
31. There is one analytical semantic core.
32. Search and analytics can exchange typed data.
33. Search does not become analytical storage.
34. Analytics does not become search indexing.
35. No mandatory third-party engine.
36. No mandatory GC.
37. No mandatory Python runtime.
38. Long-running jobs can checkpoint.
39. Cancellation propagates.
40. Deadlines propagate.
41. Tenant boundaries are preserved.
42. Security capabilities are not expanded by query.
43. Policy cannot mint capabilities.
44. Analytics cannot bypass 603.
45. Analytics cannot bypass 639.
46. Analytics cannot bypass 640.
47. Storage remains owned by 611.
48. Distributed data remains owned by 628.
49. Compute placement remains owned by 635/630.
50. Result provenance remains available where configured.

---

# 399. Performance targets

The implementation should target:

- vectorized execution as default;
- SIMD for primitive operations;
- low allocation;
- column pruning;
- predicate pushdown;
- parallel scan;
- parallel aggregation;
- efficient hash joins;
- external sort;
- spill;
- compression-aware scans;
- cache-aware execution;
- GPU acceleration where beneficial;
- no global execution lock;
- bounded scheduler overhead;
- incremental materialized views;
- distributed partition locality.

---

# 400. Final architecture

```text id="k7m3x9"
                       Axiom Analytics
                              │
                  ┌───────────┴───────────┐
                  │                       │
             DataFrame                  SQL
                  │                       │
                  └───────────┬───────────┘
                              ▼
                       Logical Plan
                              │
                       Query Optimizer
                              │
                       Physical Plan
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          ColumnScan         Join          Aggregate
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                     Vectorized Runtime
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
                 CPU         SIMD        GPU
                  │           │           │
                  └───────────┼───────────┘
                              ▼
                       Distributed
                         Exchange
                              │
                        630 Compute
                              │
                         635 Placement
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
                 628         611         634
              Distributed   Storage      Events
                 Data
```

---

# 401. Final outcome

Sau BOOTSTRAP-642, Axiom có hai execution engines bổ trợ:

```text id="v5m2q8"
                Axiom Data Runtime
                       │
             ┌─────────┴─────────┐
             │                   │
         SEARCH 641          ANALYTICS 642
             │                   │
       Retrieval/Top-K      Scan/Aggregate
       Full Text            Join
       Vector               Window
       Hybrid               OLAP
       Ranking              DataFrame
             │                   │
             └─────────┬─────────┘
                       ▼
                Shared Data Core
             611 / 612 / 628 / 640
```

Điểm quan trọng là Axiom không cần xây hai hệ thống hoàn toàn tách biệt.

Chúng chia sẻ:

- schema;
- expression IR;
- resource governor;
- distributed execution;
- storage;
- governance;
- security;
- telemetry;
- compiler metadata;
- serialization;
- checkpoint/recovery.

Nhưng mỗi engine có physical operators tối ưu cho workload riêng.

**BOOTSTRAP-642 = COMPLETE**

**Task tiếp theo: BOOTSTRAP-643 — Native Distributed Machine Learning, Tensor, Dataset, Feature Store, Model Execution, Training/Inference & AI Compute Runtime 5.0.**
:::