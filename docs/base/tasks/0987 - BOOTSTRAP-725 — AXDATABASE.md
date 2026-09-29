# BOOTSTRAP-725 — AXDATABASE

**Namespace:** `AXDATABASE`  
**Phase:** Axiom Civilization Runtime / Database & Data Query Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXSTORAGE`, `AXCOMPUTE`, `AXGEOSPATIAL`, `AXTELECOM`, `AXIDENTITY`, `AXLAW`, `AXGOV`, `AXFINANCE`

---

# 725.0 — Mục tiêu

`AXDATABASE` là database runtime native của Axiom, nằm **trên `AXSTORAGE` nhưng dưới các domain application**.

Mục tiêu không phải tạo một database engine duy nhất cho mọi trường hợp, mà cung cấp **một database semantic model thống nhất**, có thể compile xuống nhiều execution/storage strategy.

```text
Axiom Application
        ↓
AXDATABASE
        │
        ├── Relational
        ├── Key/Value
        ├── Document
        ├── Graph
        ├── Time-Series
        ├── Spatial
        ├── Vector
        └── Analytical
        │
        ↓
AXSTORAGE
        ↓
Native Storage
```

Nguyên tắc quan trọng:

> Database abstraction không được biến thành một lớp object-heavy chậm chạp nằm giữa application và storage.

---

# 725.1 — Database Boundary

`AXDATABASE` sở hữu:

```text
database schema
tables
columns
relations
constraints
queries
query compilation
query planning
query optimization
transactions
views
materialized views
indexes
aggregations
joins
change data capture
database migrations
database replication references
vector search
full-text search
spatial query
analytical execution
database statistics
database telemetry
database simulation
```

`AXSTORAGE` sở hữu:

```text
blocks
files
WAL primitives
filesystem
objects
physical persistence
replication primitives
snapshots
backup
```

`AXDATABASE` quyết định **dữ liệu có ý nghĩa gì và truy vấn thế nào**.

`AXSTORAGE` quyết định **dữ liệu được lưu vật lý ra sao**.

---

# 725.2 — Database Instance

```axiom
database {
    database_id
    name
    schema
    storage_reference
    engine_version
    configuration
    state
}
```

State:

```text
CREATING
ONLINE
READ_ONLY
DEGRADED
RECOVERING
OFFLINE
FAILED
RETIRING
```

---

# 725.3 — Database Namespace

```axiom
database_namespace {
    namespace_id
    database_reference
    name
}
```

Cho phép:

```text
database
 ├── public
 ├── users
 ├── commerce
 └── analytics
```

Namespace không đồng nghĩa với security tenant.

---

# 725.4 — Schema

```axiom
database_schema {
    schema_id
    version
    entities
    constraints
    indexes
}
```

Schema phải versioned.

```text
Schema v1
   ↓ migration
Schema v2
   ↓ migration
Schema v3
```

Không được silently thay đổi schema production.

---

# 725.5 — Table

```axiom
db_table {
    table_id
    name
    columns
    primary_key
    constraints
    indexes
    partitioning
}
```

---

# 725.6 — Column

```axiom
db_column {
    column_id
    name
    type
    nullable
    default
    constraints
}
```

Axiom type system phải map trực tiếp được sang database types khi có thể.

---

# 725.7 — Native Database Types

Tối thiểu:

```text
bool
i8 i16 i32 i64 i128
u8 u16 u32 u64 u128
f32 f64
decimal
string
bytes
uuid
timestamp
duration
date
time
datetime
json
enum
array
struct
geometry_reference
vector
```

---

# 725.8 — Exact Numeric

Các field:

```text
money
quantity
measurement
counter
identifier
```

không được mặc định map sang floating point.

Ví dụ:

```axiom
price: decimal(scale=2)
quantity: decimal(scale=6)
```

`AXFINANCE` vẫn sở hữu semantic tiền tệ.

---

# 725.9 — Primary Key

```axiom
primary_key {
    columns
    generation
}
```

Generation:

```text
explicit
sequence
UUID
content_hash
composite
```

Database không được tự ý thay đổi explicit primary key.

---

# 725.10 — Foreign Key

```axiom
foreign_key {
    source
    target
    columns
    action
}
```

Actions:

```text
restrict
cascade
set_null
set_default
custom_policy
```

---

# 725.11 — Constraint

```axiom
db_constraint {
    constraint_id
    type
    expression
    enforcement
}
```

Types:

```text
NOT_NULL
UNIQUE
CHECK
PRIMARY_KEY
FOREIGN_KEY
EXCLUSION
DOMAIN
```

---

# 725.12 — Constraint Timing

```text
immediate
deferred
```

Deferred constraint chỉ được xác nhận tại transaction boundary khi policy cho phép.

---

# 725.13 — Database Relation

Axiom database hỗ trợ:

```text
one-to-one
one-to-many
many-to-many
self-reference
temporal relation
polymorphic reference
```

Không biến mọi relation thành pointer/reference runtime.

---

# 725.14 — Query Language

Axiom cần một query DSL native:

```axiom
users
    .where(age >= 18)
    .select(name, age)
    .order_by(age.desc())
    .limit(100)
```

Nhưng compiler có thể biểu diễn cùng query dưới dạng relational algebra.

---

# 725.15 — Relational Algebra

Native logical operators:

```text
SCAN
FILTER
PROJECT
JOIN
AGGREGATE
SORT
LIMIT
UNION
INTERSECT
EXCEPT
DISTINCT
WINDOW
```

---

# 725.16 — Query AST

```axiom
query_ast {
    source
    operations
    expressions
    parameters
}
```

Query AST phải có stable representation để:

```text
compile
cache
audit
explain
replay
```

---

# 725.17 — Query Expression

```axiom
query_expression {
    type
    operands
    result_type
}
```

Operators:

```text
arithmetic
comparison
boolean
string
date/time
array
JSON
geometry
vector
aggregate
conditional
```

---

# 725.18 — Parameterized Query

```axiom
query_parameter {
    name
    type
    value
}
```

Query compiler phải tách:

```text
query structure
parameter value
```

để chống injection và tận dụng plan cache.

---

# 725.19 — Query Compilation

```text
Axiom Query
      ↓
Parse
      ↓
Type Check
      ↓
Logical Plan
      ↓
Rewrite
      ↓
Cost Optimization
      ↓
Physical Plan
      ↓
Execution
```

---

# 725.20 — Query Optimizer

Optimizer có thể lựa chọn:

```text
index scan
table scan
covering index
hash join
merge join
nested-loop join
parallel scan
partition pruning
predicate pushdown
projection pruning
aggregation pushdown
```

---

# 725.21 — Cost Model

```axiom
query_cost {
    cpu
    memory
    storage_io
    network_io
    latency
    estimated_rows
}
```

Cost estimate là **ước lượng**, không phải guarantee.

---

# 725.22 — Statistics

```axiom
database_statistics {
    table
    row_count
    column_statistics
    cardinality
    histogram
    null_fraction
    correlation
    freshness
}
```

Statistics phải versioned.

---

# 725.23 — Statistics Refresh

```axiom
analyze_table()
analyze_column()
refresh_statistics()
```

AI có thể đề xuất statistics strategy nhưng không được giả mạo statistics authoritative.

---

# 725.24 — Indexes

Các index native:

```text
B-tree
B+tree
hash
bitmap
inverted
full-text
spatial
vector
composite
partial
covering
```

---

# 725.25 — Index Selection

Optimizer phải có thể quyết định:

```text
index scan
vs
table scan
```

dựa trên statistics và cost.

Không ép dùng index chỉ vì index tồn tại.

---

# 725.26 — Composite Index

```axiom
index {
    columns: [tenant_id, created_at, status]
}
```

Thứ tự column có semantic đối với planner.

---

# 725.27 — Partial Index

```axiom
index users_active
where active == true
```

Chỉ index subset dữ liệu.

---

# 725.28 — Covering Index

Index có thể chứa:

```text
search keys
+
included fields
```

cho phép tránh table lookup.

---

# 725.29 — Transaction

`AXDATABASE` dùng transaction semantics của `AXSTORAGE` nhưng mở rộng thành database-level:

```axiom
db_transaction {
    transaction_id
    isolation
    snapshot
    read_set
    write_set
    state
}
```

---

# 725.30 — ACID

Khi database khai báo ACID:

```text
Atomicity
Consistency
Isolation
Durability
```

phải là contract thực tế.

Không được quảng cáo ACID nếu backend chỉ đạt eventual consistency.

---

# 725.31 — MVCC

```text
Transaction T1
   ↓
snapshot S1

Transaction T2
   ↓
new version
```

Reader không nhất thiết phải block writer.

---

# 725.32 — Optimistic Concurrency

```axiom
update user
where id == 10
  and version == 7
```

Nếu version đã thành 8:

```text
CONFLICT
```

không silent overwrite.

---

# 725.33 — Pessimistic Lock

Hỗ trợ:

```axiom
lock_row()
lock_range()
unlock()
```

Lock modes:

```text
shared
exclusive
update
intent
```

---

# 725.34 — Deadlock Detection

Database phải phát hiện:

```text
T1 → lock A → wait B
T2 → lock B → wait A
```

và chọn một transaction rollback theo policy.

---

# 725.35 — Savepoint

```axiom
savepoint()
rollback_to()
release_savepoint()
```

Hữu ích cho workflow phức tạp.

---

# 725.36 — Views

```axiom
db_view {
    view_id
    query
    schema
    version
}
```

View là derived query, không phải copy dữ liệu.

---

# 725.37 — Materialized View

```axiom
materialized_view {
    view_id
    query
    storage_reference
    refresh_policy
}
```

Refresh:

```text
manual
scheduled
incremental
on_commit
event_driven
```

---

# 725.38 — Change Data Capture

```axiom
cdc_stream {
    source
    sequence
    operation
    before
    after
    timestamp
}
```

Operations:

```text
INSERT
UPDATE
DELETE
SCHEMA_CHANGE
```

CDC phải preserve ordering trong phạm vi stream contract.

---

# 725.39 — Database Event Stream

```axiom
database_event {
    database
    transaction
    sequence
    table
    operation
    record_reference
}
```

Có thể dùng cho:

```text
AXGOV
AXRETAIL
AXMANUFACTURING
AXEDUCATION
AXTRANSPORT
```

mà không cho các domain trực tiếp truy cập physical storage.

---

# 725.40 — Temporal Database

Record có:

```text
valid_time
observed_time
transaction_time
```

Cho phép:

```axiom
query_at(timestamp)
```

và:

```axiom
history(record_id)
```

---

# 725.41 — Bitemporal Data

```text
        Valid Time
      ───────────────>
      A       B       C

Transaction Time
│
│ version 1
│ version 2
│ version 3
```

Cho phép phân biệt:

> điều gì đúng trong thế giới thực tại thời điểm X

với:

> database biết điều đó tại thời điểm Y.

---

# 725.42 — Partitioning

```axiom
partitioning {
    strategy
    key
    partitions
}
```

Strategies:

```text
range
hash
list
time
spatial
composite
```

---

# 725.43 — Partition Pruning

Planner phải loại bỏ partition không liên quan trước execution.

Ví dụ:

```text
WHERE timestamp >= 2026-01-01
```

không scan partition năm 2020.

---

# 725.44 — Distributed Database

```axiom
distributed_database {
    nodes
    shards
    replicas
    coordinator
    consistency
}
```

Architecture:

```text
Client
  ↓
Query Coordinator
  ↓
┌───────┬───────┬───────┐
Shard 0 Shard 1 Shard 2
```

---

# 725.45 — Distributed Query

Query planner có thể:

```text
push filter to shards
push aggregation to shards
parallel scan
partial join
shuffle
merge
```

---

# 725.46 — Distributed Join

Strategies:

```text
broadcast
partitioned hash
co-located
merge
```

Planner phải cân nhắc network cost.

---

# 725.47 — Co-location

Nếu hai table có cùng partition key:

```text
orders.customer_id
payments.customer_id
```

có thể đặt cùng shard để tránh network shuffle.

---

# 725.48 — Read Replica

```axiom
database_read_replica {
    source
    lag
    consistency
}
```

Application phải khai báo có chấp nhận stale read hay không.

---

# 725.49 — Failover

```text
PRIMARY
   ↓ failure
ELECTION / POLICY
   ↓
NEW PRIMARY
   ↓
VERIFY
   ↓
SERVE
```

Failover không được làm mất committed transaction theo declared durability contract.

---

# 725.50 — Embedded Database

Axiom phải hỗ trợ:

```text
application
   ↓
embedded database
   ↓
local AXSTORAGE
```

Không cần process/server riêng.

Đây là lựa chọn quan trọng cho:

```text
desktop
mobile
edge
embedded
offline
CLI
```

---

# 725.51 — Server Database

Cùng database semantic model có thể chạy:

```text
embedded
        OR
local server
        OR
cluster
```

Application API không cần thay đổi về semantic.

---

# 725.52 — Analytical Execution

Native operators:

```text
scan
aggregate
group
window
sort
join
vectorized execution
parallel execution
```

---

# 725.53 — Vectorized Execution

Thay vì:

```text
row
row
row
row
```

engine có thể:

```text
batch
batch
batch
```

để tận dụng:

```text
SIMD
cache locality
GPU
parallel execution
```

---

# 725.54 — Columnar Execution

Column data:

```text
age[] 
price[]
timestamp[]
```

phù hợp với:

```text
analytics
statistics
AI datasets
large scans
```

---

# 725.55 — Streaming Query

```axiom
stream query events
    |> filter(...)
    |> aggregate(window=1m)
```

Không cần materialize toàn bộ stream.

---

# 725.56 — Window

Hỗ trợ:

```text
tumbling
sliding
session
custom
```

---

# 725.57 — Full-Text Search

```axiom
fulltext_search(
    table,
    field,
    query
)
```

Primitive:

```text
tokenization
normalization
inverted index
ranking
phrase matching
prefix matching
```

Language-specific tokenization là plugin/backend capability.

---

# 725.58 — Vector Search

```axiom
vector_index {
    dimensions
    metric
    algorithm
}
```

Metrics:

```text
cosine
euclidean
dot_product
custom
```

Query:

```axiom
nearest_vectors(
    embedding,
    top_k
)
```

---

# 725.59 — Hybrid Search

Có thể kết hợp:

```text
text search
+
vector similarity
+
structured filters
+
spatial constraints
```

Ví dụ:

```text
WHERE category == "camera"
AND price < 20_000_000
AND distance(location, user_location) < 10km
ORDER BY semantic_similarity
```

---

# 725.60 — Spatial Query

`AXDATABASE` không định nghĩa geometry engine riêng.

Nó gọi primitive của `AXGEOSPATIAL`:

```text
intersects
contains
within
touches
overlaps
distance
nearest
buffer
```

Database chịu trách nhiệm:

```text
query planning
index selection
storage integration
```

---

# 725.61 — Spatial Index

Database có thể sử dụng:

```text
R-tree
grid
geohash
H3-like
S2-like
custom spatial index
```

nhưng abstraction không khóa implementation.

---

# 725.62 — Geospatial Join

Ví dụ semantic:

```text
restaurants
JOIN
administrative_regions

ON contains(region.geometry, restaurant.location)
```

Geometry semantics → `AXGEOSPATIAL`.

Query semantics → `AXDATABASE`.

---

# 725.63 — JSON

Native JSON operations:

```text
json_get()
json_set()
json_exists()
json_array()
json_object()
```

Index:

```text
path index
inverted index
```

---

# 725.64 — Document + Relational Hybrid

Một table có thể chứa:

```axiom
user {
    id: u64
    name: string
    profile: json
}
```

Không bắt buộc tạo thêm table cho mọi nested field.

---

# 725.65 — Graph Query

Database có thể expose:

```axiom
neighbors()
shortest_path()
reachable()
subgraph()
```

Graph engine có thể được backed bởi `AXSTORAGE.graph_store`.

---

# 725.66 — Database Migration

```axiom
migration {
    migration_id
    from_version
    to_version
    operations
}
```

Lifecycle:

```text
DRAFT
VALIDATED
APPLIED
VERIFIED
ROLLED_BACK
```

---

# 725.67 — Zero-Downtime Migration

Hỗ trợ pattern:

```text
expand
 ↓
dual compatibility
 ↓
backfill
 ↓
switch
 ↓
contract
```

Không yêu cầu downtime nếu backend hỗ trợ.

---

# 725.68 — Migration Safety

Migration phải khai báo:

```text
locking behavior
estimated duration
data rewrite
rollback capability
compatibility
```

---

# 725.69 — Backup/Restore Boundary

Database sử dụng:

```text
AXSTORAGE snapshot
AXSTORAGE WAL
AXSTORAGE backup
```

nhưng database phải bổ sung:

```text
schema version
catalog metadata
transaction state
index metadata
```

để restore hoàn chỉnh.

---

# 725.70 — Database Catalog

```axiom
database_catalog {
    databases
    schemas
    tables
    columns
    indexes
    constraints
    views
    functions
    migrations
    statistics
}
```

Catalog là metadata authoritative của database engine.

---

# 725.71 — Database Function

```axiom
db_function {
    function_id
    input_types
    output_type
    determinism
    execution_backend
}
```

Function có thể chạy:

```text
CPU
GPU
vectorized
distributed
```

nếu contract cho phép.

---

# 725.72 — Stored Procedure

Axiom không cần bắt buộc stored procedure theo mô hình SQL cổ điển.

Thay vào đó:

```axiom
db_procedure {
    procedure_id
    inputs
    outputs
    transaction_policy
    body
}
```

Compiler có thể native-compile procedure.

---

# 725.73 — Database Trigger

Hỗ trợ có kiểm soát:

```axiom
db_trigger {
    event
    condition
    action
}
```

Events:

```text
before_insert
after_insert
before_update
after_update
before_delete
after_delete
```

Trigger phải tránh recursive side effects không giới hạn.

---

# 725.74 — Constraint vs Trigger

Axiom phân biệt:

```text
constraint
    = invariant

trigger
    = event reaction
```

Không dùng trigger để che giấu invariant quan trọng.

---

# 725.75 — AI Query Optimization

AI có thể đề xuất:

```text
index
partition
join strategy
materialized view
cache
schema adjustment
```

Nhưng:

```text
AI recommendation
       ≠
database configuration
```

Production change cần policy/authorization.

---

# 725.76 — AI Data Analysis

AI có thể tạo:

```text
anomaly
forecast
classification
semantic search
summarization
pattern detection
```

Nhưng AI output phải:

```text
versioned
source-linked
auditable
probabilistic
```

Không biến prediction thành database fact.

---

# 725.77 — Security

Capabilities:

```text
database.read
database.write
database.admin

database.schema.read
database.schema.manage

database.table.read
database.table.write
database.table.manage

database.query.execute
database.query.explain

database.transaction.execute

database.index.manage
database.view.manage

database.migration.execute

database.cdc.read
database.cdc.manage

database.replication.manage

database.backup.manage
database.restore.manage

database.vector.search
database.fulltext.search
database.spatial.search

database.ai.execute
database.simulation.execute
database.digitaltwin.execute
```

---

# 725.78 — Row/Column Security

Có thể áp dụng:

```text
row-level policy
column-level policy
field masking
tenant isolation
purpose restriction
```

Security policy không được bypass bằng query planner optimization.

---

# 725.79 — Audit

Các operation nhạy cảm:

```text
schema change
migration
bulk export
delete
restore
permission change
query sensitive data
replication configuration
```

phải audit theo policy.

---

# 725.80 — Database Telemetry

```axiom
database_telemetry {
    database
    timestamp
    metric
    value
}
```

Metrics:

```text
query_latency
query_count
rows_scanned
rows_returned
cache_hit
lock_wait
deadlock
transaction_rate
commit_rate
rollback_rate
replication_lag
storage_io
cpu_usage
memory_usage
```

---

# 725.81 — Query Trace

```axiom
query_trace {
    query_id
    logical_plan
    physical_plan
    execution_time
    resources
    rows
    indexes_used
}
```

API:

```axiom
explain_query()
trace_query()
```

---

# 725.82 — Database Digital Twin

```axiom
database_digital_twin {
    schema
    tables
    indexes
    statistics
    workload
    topology
    replicas
    shards
}
```

Simulation:

```axiom
simulate_query()
simulate_index()
simulate_sharding()
simulate_failover()
simulate_migration()
simulate_capacity()
```

---

# 725.83 — Distributed Offline Database

```text
Local DB
   ↓
local transaction
   ↓
CDC/event journal
   ↓
offline
   ↓
reconnect
   ↓
sync
   ↓
conflict detection
   ↓
domain policy
```

Không tự động resolve authoritative conflicts bằng timestamp nếu domain yêu cầu explicit resolution.

---

# 725.84 — Native APIs

```axiom
create_database()
drop_database()

create_schema()
create_table()
alter_table()
drop_table()

add_column()
drop_column()
rename_column()

create_constraint()
drop_constraint()

create_index()
drop_index()
rebuild_index()

create_view()
create_materialized_view()
refresh_materialized_view()

prepare_query()
compile_query()
execute_query()

explain_query()
trace_query()

begin_transaction()
commit_transaction()
rollback_transaction()
create_savepoint()

lock_row()
unlock_row()

create_partition()
rebalance_partition()

create_replica()
failover_replica()

create_cdc_stream()
read_cdc()

create_migration()
validate_migration()
apply_migration()
rollback_migration()

create_fulltext_index()
search_fulltext()

create_vector_index()
search_vector()

create_spatial_index()
search_spatial()

create_graph_query()

analyze_table()
refresh_statistics()

create_backup()
restore_database()

create_database_simulation()
create_database_digital_twin()

reconcile_database_state()
replay_database_state()
```

---

# 725.85 — Canonical OLTP Flow

```text
Application
 ↓
Typed API
 ↓
Query Compiler
 ↓
Query Plan
 ↓
Transaction
 ↓
Index / Data Scan
 ↓
MVCC
 ↓
WAL
 ↓
AXSTORAGE
 ↓
Commit
```

---

# 725.86 — Canonical Analytics Flow

```text
Dataset
 ↓
Query
 ↓
Logical Plan
 ↓
Statistics
 ↓
Optimizer
 ↓
Partition Pruning
 ↓
Parallel / Vectorized Scan
 ↓
Aggregation
 ↓
Result
```

---

# 725.87 — Canonical Distributed Flow

```text
Client
 ↓
Coordinator
 ↓
Logical Query
 ↓
Distributed Planner
 ↓
Shard Pruning
 ↓
Parallel Execution
 ↓
Partial Results
 ↓
Merge
 ↓
Final Result
```

---

# 725.88 — Canonical Migration Flow

```text
Schema v1
 ↓
Migration Validation
 ↓
Compatibility Check
 ↓
Expand
 ↓
Backfill
 ↓
Verify
 ↓
Switch
 ↓
Contract
 ↓
Schema v2
```

---

# 725.89 — Canonical CDC Flow

```text
Transaction
 ↓
Commit
 ↓
CDC Event
 ↓
Ordered Stream
 ├── cache
 ├── projection
 ├── search index
 ├── analytics
 └── external domain consumer
```

---

# 725.90 — Formal Invariants

```text
DB-INV-01   Every database has stable identity.
DB-INV-02   Every schema has explicit version.
DB-INV-03   Every table has explicit schema.
DB-INV-04   Every column has explicit type.
DB-INV-05   Primary-key semantics are explicit.
DB-INV-06   Foreign-key semantics are explicit.
DB-INV-07   Constraints cannot be silently disabled.
DB-INV-08   Query parameters are type-checked.
DB-INV-09   Query plans reference schema versions.
DB-INV-10   Indexes are derived structures.

DB-INV-11   Transactions have explicit lifecycle.
DB-INV-12   Isolation level is explicit.
DB-INV-13   Unsupported isolation cannot silently downgrade.
DB-INV-14   Committed writes satisfy declared durability.
DB-INV-15   MVCC versions preserve transaction ordering.
DB-INV-16   Deadlocks are detectable.
DB-INV-17   Rollback cannot report committed state.
DB-INV-18   Savepoints belong to a transaction.
DB-INV-19   Distributed transactions preserve identity.
DB-INV-20   CDC cannot emit an uncommitted authoritative change.

DB-INV-21   Schema migrations are versioned.
DB-INV-22   Migration compatibility is checked.
DB-INV-23   Migration state is recoverable.
DB-INV-24   Materialized views identify their source version.
DB-INV-25   Statistics identify their freshness.
DB-INV-26   Query optimizer cannot violate constraints.
DB-INV-27   Query optimization cannot alter query semantics.
DB-INV-28   Security filters survive query rewriting.
DB-INV-29   Row/column authorization is enforced before result exposure.
DB-INV-30   Query execution is auditable when policy requires.

DB-INV-31   Replica consistency mode is explicit.
DB-INV-32   Replica lag is observable.
DB-INV-33   Shard ownership is explicit.
DB-INV-34   Distributed query results preserve query semantics.
DB-INV-35   Spatial queries use explicit CRS semantics.
DB-INV-36   Vector search identifies index/model configuration.
DB-INV-37   Full-text search identifies tokenizer/index version.
DB-INV-38   Temporal queries identify time semantics.
DB-INV-39   Simulation cannot mutate production database state.
DB-INV-40   AI output cannot become authoritative data without explicit domain operation.
```

---

# 725.91 — Performance Architecture

`AXDATABASE` phải được thiết kế để Axiom có thể đạt hiệu năng gần native storage/database engine chuyên dụng.

Không:

```text
Axiom object
 ↓
reflection
 ↓
generic ORM
 ↓
generic driver
 ↓
serialization
 ↓
database
```

Mà:

```text
Axiom Type
   ↓
Compile-Time Schema
   ↓
Typed Query IR
   ↓
Optimized Physical Plan
   ↓
Native Execution
   ↓
AXSTORAGE
```

---

# 725.92 — Compile-Time Query

Ví dụ:

```axiom
users
    .where(age >= 18)
    .select(id, name)
```

Compiler có thể biết:

```text
users.age → column #3
users.id  → column #0
users.name → column #1
```

Không cần reflection tại runtime.

---

# 725.93 — Static Query Specialization

Nếu query structure cố định:

```text
query template
     ↓
compile
     ↓
specialized execution function
```

Parameter vẫn dynamic.

Điều này giảm:

```text
parsing
reflection
allocation
dispatch
```

trên hot path.

---

# 725.94 — Native Memory Layout

Database engine phải có quyền chọn:

```text
row layout
column layout
hybrid layout
compressed layout
```

Compiler biết layout contract khi cần.

---

# 725.95 — Zero-Copy Query Result

Có thể trả:

```axiom
record_view
column_view
buffer_view
vector_view
```

thay vì copy toàn bộ result.

Ví dụ:

```text
storage page
      ↓
query
      ↓
typed view
```

---

# 725.96 — Embedded Fast Path

Cho database embedded:

```text
Axiom
 ↓
AXDATABASE
 ↓
AXSTORAGE
```

không cần:

```text
TCP
serialization
RPC
```

Điều này đặc biệt quan trọng cho:

```text
CLI
desktop
mobile
edge
local AI
embedded systems
```

---

# 725.97 — Completion Criteria

`BOOTSTRAP-725` phải freeze:

1. Database instance.
2. Namespace.
3. Schema.
4. Tables.
5. Columns.
6. Native types.
7. Primary keys.
8. Foreign keys.
9. Constraints.
10. Relations.
11. Query DSL.
12. Relational algebra.
13. Query AST.
14. Query compilation.
15. Query optimizer.
16. Cost model.
17. Statistics.
18. Indexes.
19. Composite indexes.
20. Partial indexes.
21. Covering indexes.
22. Transactions.
23. ACID.
24. MVCC.
25. Optimistic concurrency.
26. Pessimistic locking.
27. Deadlock detection.
28. Savepoints.
29. Views.
30. Materialized views.
31. CDC.
32. Event integration.
33. Temporal database.
34. Bitemporal database.
35. Partitioning.
36. Distributed database.
37. Distributed query.
38. Distributed join.
39. Replication.
40. Embedded database.
41. Server database.
42. Analytical execution.
43. Vectorized execution.
44. Columnar execution.
45. Streaming query.
46. Full-text search.
47. Vector search.
48. Hybrid search.
49. Spatial query.
50. JSON.
51. Graph query.
52. Schema migration.
53. Zero-downtime migration.
54. Backup/restore integration.
55. Database catalog.
56. Functions/procedures.
57. Triggers.
58. AI query optimization boundary.
59. Security.
60. Row/column security.
61. Audit.
62. Telemetry.
63. Query tracing.
64. Digital twin.
65. Offline synchronization.
66. Formal invariants.
67. Native compilation.
68. Zero-copy result.
69. Embedded fast path.

---

# 725.98 — Definition of Done

```text
BOOTSTRAP-725
STATUS: COMPLETE / FROZEN

AXDATABASE 5.0
    ├── Typed Schema
    ├── Relational Model
    ├── Query DSL
    ├── Query IR
    ├── Query Optimizer
    ├── Cost Model
    ├── Index Engine
    ├── Transactions
    ├── MVCC
    ├── Constraints
    ├── Views
    ├── Materialized Views
    ├── CDC
    ├── Temporal Data
    ├── Partitioning
    ├── Distributed Query
    ├── Replication
    ├── OLTP
    ├── OLAP
    ├── Streaming
    ├── Full-Text
    ├── Vector Search
    ├── Spatial Query
    ├── Graph Query
    ├── JSON
    ├── Migration
    ├── Backup/Restore
    ├── Security
    ├── Audit
    ├── Telemetry
    ├── Offline DB
    ├── AI Integration
    ├── Simulation
    ├── Digital Twin
    └── Native Performance
```

**BOOTSTRAP-725 / AXDATABASE — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-726 — AXNETWORK

**Native Networking & Network Runtime — sockets, TCP/UDP/QUIC-like transports, IPv4/IPv6, DNS, HTTP, WebSocket, RPC, streams, datagrams, multicast, service discovery, TLS/security references, connection pooling, load balancing, congestion/backpressure, zero-copy networking, RDMA-like abstraction, distributed messaging, pub/sub, offline networking, network telemetry, edge networking, network simulation & Network Runtime 5.0.**