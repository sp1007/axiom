# BOOTSTRAP-375 — Axiom Graph Computing, Irregular Dataflow & Graph Algorithm Engine

Sau **374 — Sparse Computing**, bước tiếp theo tự nhiên là **Graph Computing**.

Sparse matrix đã cung cấp representation rất tốt cho adjacency structure, nhưng graph computation có những semantics riêng mà chỉ dùng `SparseMatrix` sẽ không đủ:

- graph topology;
- node/edge identity;
- traversal;
- BFS/DFS;
- shortest path;
- connected components;
- PageRank;
- graph reduction;
- dynamic graph;
- irregular parallelism;
- graph neural network primitives;
- graph partitioning.

Mục tiêu của 375 là xây **graph semantics trên nền Axiom hiện có**, nhưng **không biến Graph thành một kiểu Core đặc biệt**.

---

# 1. Graph không phải class hierarchy

Không tạo:

```text
class Graph
class DirectedGraph extends Graph
class WeightedGraph extends Graph
...
```

Thay vào đó:

```text
struct Graph<N, E, Topology>
```

hoặc các generic library abstractions.

Compiler chỉ hiểu những semantic properties cần thiết:

```text
Node
Edge
Adjacency
Traversal
Mutation
ParallelAccess
```

---

# 2. Graph gồm hai loại identity

Graph cần phân biệt:

```text
NodeId
EdgeId
```

với:

```text
NodeData
EdgeData
```

Ví dụ:

```text id="2b6t9m"
NodeId = 42
NodeData = Person { ... }
```

`NodeId` là logical identity.

Nó không phải:

```text
pointer
memory address
reference
```

Điều này phù hợp với Axiom memory model.

---

# 3. Stable graph identity

Graph có thể thay đổi storage:

```text
reallocate
compact
reorder
partition
move GPU
```

nhưng:

```text
NodeId
```

vẫn có thể giữ logical identity.

Do đó graph algorithm không phụ thuộc physical address.

---

# 4. Directed / undirected

Graph topology phải explicit:

```text id="f7c2qk"
Directed
Undirected
Bidirectional
```

Ví dụ:

```text
add_edge(a,b)
```

với directed graph:

```text
a → b
```

Trong undirected:

```text
a ↔ b
```

Compiler/library không được giả định.

---

# 5. Multigraph

Có thể tồn tại:

```text id="j4m8sp"
a → b
a → b
```

với hai edge khác nhau.

Do đó:

```text id="e6q2vx"
Node pair != Edge identity
```

Graph representation phải hỗ trợ:

```text
SimpleGraph
MultiGraph
```

như library-level types.

---

# 6. Self-loop

Phải xác định:

```text id="r8n5ck"
a → a
```

có hợp lệ hay không.

Đây là topology property, không nên compiler tự giả định.

---

# 7. Weighted graph

Weight có thể là:

```text id="c2m7wa"
f32
f64
integer
custom numeric type
```

Không cần:

```text id="h3x8qv"
Graph<f64>
```

bắt buộc.

Edge có thể chứa arbitrary user data:

```text id="z5p1fn"
struct Edge {
    weight: f32
    capacity: f32
}
```

---

# 8. Graph storage

Có thể dùng:

```text id="q7m3vd"
AdjacencyList
CSR
CSC
COO
EdgeList
CompressedGraph
Hybrid
```

Graph abstraction không được phụ thuộc representation.

Compiler có thể chọn representation nếu graph construction/use pattern đủ rõ.

---

# 9. Static graph

Nếu topology biết tại compile time:

```text id="n8k4wx"
graph {
    A -> B
    B -> C
    C -> D
}
```

thì compiler có thể specialize:

```text id="c6p9mz"
adjacency
degree
partition
traversal
```

nhưng đây là optimization, không bắt buộc phải có graph literal syntax trong Core.

---

# 10. Dynamic graph

Runtime graph:

```text id="w3x7qp"
add_node()
remove_node()
add_edge()
remove_edge()
```

phải có explicit mutation capability.

Đặc biệt:

```text id="v4n8yc"
NodeView
EdgeView
NeighborView
```

có thể bị invalidated bởi structural mutation.

---

# 11. Graph mutation capability

Tương tự sparse:

```text id="m7q2sx"
GraphValueMut
GraphStructureMut
```

`GraphValueMut`:

```text id="u1k6fb"
node.data = ...
edge.weight = ...
```

không thay đổi topology.

`GraphStructureMut`:

```text id="p5r9ka"
add_edge
remove_edge
add_node
remove_node
```

có thể invalidate adjacency views.

---

# 12. Traversal view

API:

```text id="x8m3qf"
for edge in graph.neighbors(node) {
    ...
}
```

không nên tạo heap iterator object bắt buộc.

Compiler có thể lower thành:

```text id="k2v7cd"
index loop
pointer/index arithmetic
bounds checks
```

và loại bỏ abstraction hoàn toàn.

---

# 13. BFS

Graph semantic primitive:

```text id="j9x4vw"
BFS(graph, source)
```

Compiler/library implementation có thể dùng:

```text id="b5m8qn"
frontier queue
visited bitmap
parallel frontier
```

nhưng semantics là traversal order/distance theo graph definition.

---

# 14. BFS order

Đây là điểm quan trọng.

Trong graph có:

```text id="z1q7yc"
A → B
A → C
```

thứ tự duyệt B/C có thể khác nhau nếu adjacency storage khác.

Axiom phải phân biệt:

```text id="f3m9ks"
OrderedTraversal
UnorderedTraversal
```

Nếu algorithm không yêu cầu thứ tự, compiler được phép reorder.

---

# 15. DFS

DFS có thể là:

```text id="n6w2rt"
DepthFirst
```

nhưng recursion không nên bắt buộc.

Compiler/library có thể lower thành explicit stack để tránh:

```text id="g8q4xm"
stack overflow
```

với graph sâu.

---

# 16. Recursive graph algorithms

Nếu programmer viết:

```text id="h2p7vc"
fn visit(node) {
    for child in node.children {
        visit(child);
    }
}
```

compiler có thể:

- giữ recursion;
- inline;
- convert thành loop;
- stack optimize.

Không thay đổi observable semantics.

---

# 17. Parallel BFS

BFS frontier:

```text id="r4m8yd"
current_frontier
        ↓
expand
        ↓
next_frontier
```

có thể parallelize.

Nhưng nhiều worker có thể cùng discover node.

Compiler phải đảm bảo:

```text id="s7c3pk"
visited
```

được cập nhật an toàn.

Strategies:

```text id="m1v6qx"
atomic CAS
partitioned visited
local frontier + merge
```

---

# 18. Graph parallelism khác array parallelism

Array:

```text id="w8k2zr"
for i in 0..N
```

thường có iteration space rõ ràng.

Graph:

```text id="y3m7qp"
for neighbor in adjacency(node)
```

có dynamic degree và irregular memory access.

Do đó cần:

```text id="c5n9fx"
GraphParallelRegion
```

hoặc compiler metadata để mô tả irregular work.

---

# 19. Work stealing

Graph algorithms có workload rất lệch.

Ví dụ:

```text id="p2x7ma"
node A: 2 neighbors
node B: 1000000 neighbors
```

Static partitioning rất dễ mất cân bằng.

Compiler/runtime có thể dùng:

```text id="k6r1vs"
dynamic scheduling
work stealing
frontier partitioning
```

dựa trên cost model.

---

# 20. Graph reductions

Ví dụ:

```text id="n7x3cm"
sum(neighbor.weight)
```

có thể được reduce.

Compiler cần biết:

```text id="q1v9kb"
identity
combine
numerical contract
```

giống parallel reduction từ task 365.

---

# 21. Shortest path

Graph engine có semantic algorithms:

```text id="r5m2wx"
BFS
Dijkstra
BellmanFord
AStar
FloydWarshall
```

nhưng không nhất thiết phải là compiler intrinsics từng algorithm.

Một số pattern có thể compiler recognize.

---

# 22. Dijkstra

Dijkstra yêu cầu:

```text id="c8q4yn"
non-negative edge weights
```

Nếu compiler có proof:

```text id="v7m1ps"
weight >= 0
```

thì algorithm legal.

Nếu không:

```text id="j3x8qb"
compile-time/runtime validation
```

tùy API.

---

# 23. A* heuristic

A*:

```text id="m9w4kc"
f(n) = g(n) + h(n)
```

heuristic có thể là user function.

Nếu user đánh dấu:

```text id="z2p7vt"
@admissible
```

compiler không nên tự tin tuyệt đối nếu không thể prove.

Có thể phân biệt:

```text id="d4n8sx"
VerifiedHeuristic
TrustedHeuristic
```

---

# 24. Graph algorithms + ownership

Một graph:

```text id="q6m1va"
Graph<NodeData, EdgeData>
```

sở hữu data.

Khi traversal:

```text id="b3x7pn"
view(node)
```

là non-owning capability.

Không được trả về view rồi cho phép graph mutation làm dangling view.

Ownership engine phải kiểm soát.

---

# 25. Graph handles

`NodeId` không nên tự động là capability.

Ví dụ:

```text id="h7c4ym"
node_id: NodeId
```

không có nghĩa node vẫn tồn tại.

Graph mutation có thể invalidate ID.

Do đó có thể có:

```text id="s2k8fq"
StableNodeId
GenerationNodeId
```

library-level abstractions.

---

# 26. Generation handles

Nếu graph hỗ trợ remove/reuse:

```text id="m5x9cd"
NodeHandle {
    index
    generation
}
```

thì stale handle có thể được phát hiện.

Đây là application của logical identity từ memory model.

---

# 27. Graph + sparse

Graph adjacency matrix:

```text id="u8q2mv"
Graph → SparseMatrix
```

có thể zero-copy trong một số layouts.

Ngược lại:

```text id="g6m4zr"
SparseMatrix → Graph
```

chỉ legal khi sparse representation thỏa graph topology requirements.

Ví dụ duplicate entries có thể cần canonicalization.

---

# 28. Graph + tensor

Node features:

```text id="c9x3wb"
X: Tensor<[N,D]>
```

Edge index:

```text id="p7m2kf"
E: Sparse/Graph structure
```

có thể tạo GNN library.

Axiom không cần GNN primitive trong Core.

Compiler chỉ cần optimize:

```text id="q1v6hz"
gather
scatter
reduce
SpMM
```

---

# 29. Graph neural network pattern

Typical message passing:

```text id="r3k7mx"
message = message_fn(node, neighbor)
aggregate = reduce(message)
update = update_fn(node, aggregate)
```

Compiler có thể nhận diện:

```text id="j5v2cq"
gather
compute
scatter/reduce
```

và lower thành:

```text id="x9m4ka"
CPU parallel kernel
SIMD
GPU kernel
```

Đây là một trong những lý do Graph engine đáng có.

---

# 30. Gather/scatter semantics

Graph algorithms thường cần:

```text id="k8x1vf"
gather
scatter
```

Axiom phải phân biệt:

```text id="s6q3yn"
SCATTER_UNIQUE
SCATTER_REDUCE
SCATTER_LAST
SCATTER_ATOMIC
```

Không được để duplicate destination behavior phụ thuộc CPU/GPU hardware.

---

# 31. Scatter-reduce

Ví dụ:

```text id="f4n8wm"
grad[neighbor] += message
```

có thể có nhiều writers.

Compiler có thể lower thành:

```text id="e2q7pz"
atomic
```

hoặc:

```text id="v9m3xc"
partition + local reduction
```

nếu semantic contract cho phép.

---

# 32. Graph + AD

Graph algorithm có thể chứa differentiable operations:

```text id="h5k8qa"
score = f(node_features, edge_weights)
```

AD engine phải differentiate phần numeric computation.

Topology:

```text id="z1c6wr"
NodeId
EdgeId
Adjacency
```

không tự động trở thành differentiable.

---

# 33. Differentiable graph structure

Nếu muốn differentiate graph topology, cần một abstraction khác:

```text id="p3v7mk"
SoftAdjacency
ContinuousEdgeWeight
```

Compiler không được tự động coi:

```text id="n4q8yx"
add_edge/remove_edge
```

là differentiable.

---

# 34. Graph partitioning

Large graph:

```text id="w7m2kc"
CPU NUMA
GPU
distributed
```

cần partition:

```text id="g9x4sv"
vertex partition
edge partition
community partition
```

Compiler/runtime có thể tối ưu locality.

Nhưng graph partitioning không được thay đổi logical result.

---

# 35. NUMA-aware graph

Graph irregular memory access rất nhạy với NUMA.

Cost model có thể sử dụng:

```text id="y5p8rn"
node locality
edge locality
partition
remote memory traffic
```

để chọn worker placement.

Đây là optimization, không phải thay đổi memory semantics.

---

# 36. GPU graph

GPU graph execution có:

```text id="j6q3xp"
warp divergence
atomic contention
irregular memory
frontier compaction
```

Compiler cần graph-specific cost model.

Nhưng vẫn dùng:

```text id="f4n9zc"
GpuKernelABI
GpuMemory
GpuAtomic
GpuParallel
```

đã có.

---

# 37. Graph execution graph

Một graph algorithm có thể được compiler biểu diễn:

```text id="m8x2qs"
GraphExecutionPlan {
    traversal
    frontier
    partition
    gather
    compute
    scatter
    reduction
}
```

Sau đó lower:

```text id="r5c7wa"
CPU
SIMD
parallel
GPU
```

---

# 38. CompilerDB

375 bổ sung:

```text id="u1q8vz"
GraphDB
GraphTypeDB
GraphTopologyDB
GraphNodeDB
GraphEdgeDB
GraphNodeIdDB
GraphEdgeIdDB
GraphHandleDB
GraphGenerationDB
GraphStorageDB
GraphAdjacencyDB
GraphMutationDB
GraphStructureMutationDB
GraphValueMutationDB
GraphViewDB
GraphNeighborDB
GraphTraversalDB
GraphBfsDB
GraphDfsDB
GraphShortestPathDB
GraphDijkstraDB
GraphAStarDB
GraphConnectedComponentDB
GraphPageRankDB
GraphPartitionDB
GraphParallelDB
GraphFrontierDB
GraphWorkDB
GraphWorkStealingDB
GraphGatherDB
GraphScatterDB
GraphScatterReduceDB
GraphReductionDB
GraphSparseDB
GraphTensorDB
GraphADDB
GraphCpuDB
GraphSimdDB
GraphGpuDB
GraphCostModelDB
GraphProofDB
GraphVerificationDB
```

---

# 39. MIR additions

Semantic MIR:

```text id="q4x8mk"
GRAPH_CREATE
GRAPH_VIEW
GRAPH_MUT_VIEW

GRAPH_NODE_CREATE
GRAPH_NODE_REMOVE
GRAPH_EDGE_CREATE
GRAPH_EDGE_REMOVE

GRAPH_NEIGHBORS
GRAPH_DEGREE

GRAPH_TRAVERSE_BEGIN
GRAPH_TRAVERSE_NEXT
GRAPH_TRAVERSE_END

GRAPH_FRONTIER_CREATE
GRAPH_FRONTIER_EXPAND
GRAPH_FRONTIER_COMPACT

GRAPH_GATHER
GRAPH_SCATTER
GRAPH_SCATTER_REDUCE

GRAPH_PARTITION
GRAPH_PARALLEL_REGION
GRAPH_REDUCE
```

Sau optimization, phần lớn có thể biến thành:

```text id="k7p3xy"
ordinary loops
array indexing
sparse kernels
SIMD
parallel regions
GPU kernels
```

---

# 40. Proof system

Cần:

```text id="s3m8qk"
GraphTopologyProof
GraphNodeProof
GraphEdgeProof
GraphHandleProof
GraphGenerationProof
GraphBoundsProof
GraphTraversalProof
GraphMutationProof
GraphAliasProof
GraphParallelProof
GraphRaceProof
GraphGatherProof
GraphScatterProof
GraphReductionProof
GraphSparseProof
GraphTensorProof
GraphADProof
GraphGpuProof
GraphPartitionProof
GraphNumericalProof
```

---

# 41. Invariants

### `AGRAPH-01`
Graph phải là library/generic abstraction, không phải mandatory Core object model.

### `AGRAPH-02`
Node identity phải khác physical address.

### `AGRAPH-03`
Edge identity phải khác node-pair identity trong multigraph.

### `AGRAPH-04`
Directed/undirected semantics phải explicit.

### `AGRAPH-05`
Self-loop semantics phải explicit.

### `AGRAPH-06`
Multigraph semantics phải explicit.

### `AGRAPH-07`
Graph topology mutation phải được phân biệt với data mutation.

### `AGRAPH-08`
Structural mutation phải invalidate các capability bị ảnh hưởng.

### `AGRAPH-09`
Node/edge views không được outlive backing graph/storage.

### `AGRAPH-10`
Logical handles không tự động trở thành safe memory capabilities.

### `AGRAPH-11`
Stale handles phải được phát hiện nếu storage model yêu cầu.

### `AGRAPH-12`
Traversal order phải explicit nếu observable.

### `AGRAPH-13`
Compiler không được assume adjacency order nếu API không đảm bảo order.

### `AGRAPH-14`
Graph parallelism phải chứng minh race safety.

### `AGRAPH-15`
Gather/scatter duplicate semantics phải explicit.

### `AGRAPH-16`
Scatter-reduce phải có explicit reduction operator.

### `AGRAPH-17`
Graph reduction phải tuân numerical contract.

### `AGRAPH-18`
Graph workload partitioning không được thay đổi logical semantics.

### `AGRAPH-19`
Graph storage representation có thể thay đổi nếu observable semantics được bảo toàn.

### `AGRAPH-20`
CSR/CSC/adjacency-list conversion phải preserve topology semantics.

### `AGRAPH-21`
Graph-to-sparse conversion phải xác định duplicate/weight semantics.

### `AGRAPH-22`
Sparse-to-graph conversion phải xác định implicit-zero semantics.

### `AGRAPH-23`
Graph algorithms phải kiểm tra các precondition toán học cần thiết.

### `AGRAPH-24`
Dijkstra không được áp dụng khi edge-weight contract không thỏa yêu cầu.

### `AGRAPH-25`
Graph AD chỉ differentiate explicit numeric values, không tự động differentiate topology mutation.

### `AGRAPH-26`
Graph GPU execution phải tuân GPU address-space/race semantics.

### `AGRAPH-27`
Graph optimization có thể dùng SIMD/parallel/GPU nhưng không được thay đổi observable semantics.

### `AGRAPH-28`
External graph libraries không được là mandatory language dependency.

### `AGRAPH-29`
Graph transformations phải có verification/validation path.

### `AGRAPH-30`
Nếu graph abstraction được compile away, generated native code không được giữ lại graph runtime metadata không cần thiết.

---

# 42. Kiến trúc sau 375

Axiom lúc này đã tiến đến một điểm khá thú vị:

```text
                         AXIOM NUMERICAL ENGINE
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
           Dense                Sparse              Graph
              │                   │                   │
          Tensor              SparseTensor       Graph/Topology
              │                   │                   │
      ┌───────┼───────┐           │           ┌───────┼───────┐
      ▼       ▼       ▼           ▼           ▼       ▼       ▼
    Linear   FFT      AD        SpMV/SpMM    BFS    Gather   Scatter
    Algebra  Conv               Solvers      │        │         │
      │       │                  │           └────────┼─────────┘
      └───────┴──────────────┬───┴────────────────────┘
                             ▼
                      Expression Graph
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
               SIMD       Parallel      GPU
                 │           │           │
                 └───────────┼───────────┘
                             ▼
                       Native Backend
```

Và đây là một bước quan trọng đối với mục tiêu ban đầu của Axiom: **AI/GPU không cần được hard-code thành “tính năng AI”**. Một GNN, sparse neural network, scientific solver hay graph simulator đều có thể cuối cùng quy về cùng những primitive compiler mà Axiom đã xây: **ownership + shape + expression + sparse + graph + parallel + SIMD + GPU → native code**.