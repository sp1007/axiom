Tiếp tục với **BOOTSTRAP-645 — Native AI Knowledge Graph, Semantic Graph, Ontology, Entity Resolution, Graph Query, Graph Analytics & Knowledge Runtime 5.0**.

:::writing{variant="document" id="58314" title="BOOTSTRAP-645 — Native AI Knowledge Graph, Semantic Graph, Ontology, Entity Resolution, Graph Query, Graph Analytics & Knowledge Runtime 5.0"}
# BOOTSTRAP-645
## Native AI Knowledge Graph, Semantic Graph, Ontology, Entity Resolution, Graph Query, Graph Analytics & Knowledge Runtime 5.0

**Status:** COMPLETE  
**Layer:** Native Knowledge & Semantic Data Plane  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-644

---

# 1. Mục tiêu

BOOTSTRAP-645 bổ sung cho Axiom một runtime native để biểu diễn và xử lý tri thức dưới dạng:

- entity;
- relation;
- property graph;
- semantic graph;
- ontology;
- taxonomy;
- knowledge base;
- provenance graph;
- lineage graph;
- entity resolution;
- graph query;
- graph traversal;
- graph analytics;
- graph embeddings;
- semantic retrieval;
- knowledge-aware AI.

Mục tiêu không phải xây một database graph đơn thuần.

645 phải tạo ra nền tảng để:

```text
structured data
      ↓
knowledge graph
      ↓
semantic representation
      ↓
retrieval
      ↓
AI agent
```

đồng thời cho phép:

```text
Axiom application
       ↓
KnowledgeGraph
       ↓
Query / Traverse / Reason
       ↓
Agent / Analytics / Search
```

---

# 2. Boundary

| Layer | Responsibility |
|---|---|
| 612 | schema/serialization |
| 628 | distributed data/replication |
| 640 | data governance/lineage |
| 641 | search/vector retrieval |
| 642 | analytical processing |
| 643 | tensor/model execution |
| 644 | AI agent orchestration |
| **645** | semantic graph/knowledge |

645 không thay thế:

- relational storage;
- document storage;
- search engine;
- vector database;
- policy engine.

Nó kết hợp chúng thành một semantic data layer.

---

# 3. Core architecture

```text
                  Application / AI Agent
                           │
                           ▼
                   Knowledge Runtime
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Entity             Relation           Ontology
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                      Graph Store
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Query         Traversal      Analytics
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                   Semantic Retrieval
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
            641           642           643
         Search          OLAP          Models
                           │
                           ▼
                          644
                         Agent
```

---

# 4. Design principles

1. Entity identity is explicit.
2. Relation identity is explicit.
3. Graph schema is optional but strongly encouraged.
4. Unknown entities can exist.
5. Unknown relations can exist only under explicit schema policy.
6. Provenance is first-class.
7. Temporal validity is first-class.
8. Graph versions are immutable.
9. Updates are revisioned.
10. Distributed replication uses 628.
11. Governance uses 640.
12. Authorization uses 603/639.
13. Search uses 641.
14. Analytics uses 642.
15. ML embeddings use 643.
16. Agents consume graph through 644.
17. Graph queries are typed.
18. Query execution is bounded.
19. Traversal cannot escape authorization boundaries.
20. No implicit reasoning engine is required.
21. Inference is explicit.
22. AI-generated facts are not automatically trusted.
23. Provenance is preserved through derived facts.
24. No mandatory RDF/SPARQL dependency.
25. No mandatory Neo4j dependency.
26. No mandatory external graph database.
27. Native implementation is possible.

---

# 5. Core objects

```text
KnowledgeGraph
GraphId
GraphGeneration
GraphRevision

Entity
EntityId
EntityType
EntityVersion

Relation
RelationId
RelationType
RelationVersion

Property
PropertyId
PropertyValue

GraphNode
GraphEdge

Ontology
OntologyId
OntologyVersion
Concept
ConceptId
ConceptRelation

Taxonomy
Schema
GraphSchema

Provenance
ProvenanceRecord

Evidence
EvidenceId

TemporalValidity
Confidence
Assertion

GraphQuery
GraphPlan
GraphResult

GraphPath
GraphPattern

EntityResolver
EntityCandidate
EntityMatch

GraphIndex
GraphPartition

GraphSnapshot
GraphTransaction

GraphEmbedding
SemanticRelation

GraphAnalytics
```

---

# 6. KnowledgeGraph

```text
struct KnowledgeGraph {
    id: GraphId
    schema: GraphSchemaRef
    revision: GraphRevision
}
```

---

# 7. Graph identity

A graph is identified by:

```text
GraphId
Generation
SchemaFingerprint
```

---

# 8. Entity

Entity represents a real or logical object.

Examples:

```text
Person
Company
Product
Place
Document
Event
Concept
Device
Model
Dataset
Service
```

---

# 9. EntityId

Entity IDs are stable within a graph namespace.

---

# 10. Entity identity

Identity is independent from display name.

```text
EntityId != EntityName
```

---

# 11. Entity generation

Entity updates increment generation.

Stale writers cannot modify newer generations.

---

# 12. Entity type

Entity may have one or more typed classifications.

---

# 13. Multiple types

Example:

```text
Entity: "Axiom"

Types:
    ProgrammingLanguage
    SoftwareProject
    KnowledgeArtifact
```

---

# 14. Entity properties

Properties are typed.

```text
name: String
created_at: Timestamp
population: Int64
active: Bool
```

---

# 15. Property schema

Properties may specify:

```text
type
required
nullable
indexed
searchable
sensitive
```

---

# 16. Relation

Relation connects two entities.

```text
Entity A
   │
   └── relation ──→ Entity B
```

---

# 17. Directed relation

Relations are directed by default.

---

# 18. Undirected semantic relation

Can be represented by symmetric relation metadata.

---

# 19. Relation identity

Every stored relation has an identity.

This allows:

- provenance;
- revision;
- deletion;
- conflict resolution.

---

# 20. Relation properties

Relations can have properties.

Example:

```text
Person ── works_at ──→ Company

properties:
    role
    start_date
    end_date
```

---

# 21. Hyperedge boundary

N-ary relationships are represented using an explicit event/entity node.

This keeps the core graph model simple.

---

# 22. Graph schema

Graph schema defines:

```text
entity types
relation types
property types
constraints
indexes
```

---

# 23. Open-world mode

Graph can permit unknown properties/types.

---

# 24. Closed-world mode

Schema can require all entities/relations to conform.

---

# 25. Mixed mode

Individual namespaces may use different strictness.

---

# 26. Ontology

Ontology describes semantic concepts and their relationships.

---

# 27. Ontology concepts

```text
Concept
SubConcept
EquivalentConcept
DisjointConcept
RelatedConcept
```

---

# 28. Taxonomy

Taxonomy is a directed hierarchical classification.

Example:

```text
Animal
 ├── Mammal
 │    ├── Dog
 │    └── Cat
 └── Bird
```

---

# 29. Subtype relation

Ontology can declare:

```text
Dog IS_A Animal
```

---

# 30. Part-of relation

Explicit relation:

```text
Engine PART_OF Car
```

---

# 31. Ontology version

Ontology is versioned and immutable.

---

# 32. Ontology compatibility

Changing semantics requires a new ontology revision.

---

# 33. Namespace

Graphs use namespaces to prevent identifier collisions.

---

# 34. Entity alias

An entity can have aliases:

```text
canonical_name
aliases[]
external_ids[]
```

---

# 35. External identifiers

Example:

```text
doi
isbn
uuid
url
database_id
```

---

# 36. External identity mapping

Mappings are explicit assertions, not automatic truth.

---

# 37. Entity resolution

EntityResolver matches records that may refer to the same entity.

---

# 38. Entity resolution pipeline

```text
Candidate Generation
        ↓
Feature Extraction
        ↓
Similarity
        ↓
Decision
        ↓
Identity Mapping
```

---

# 39. Candidate generation

Possible strategies:

- exact identifiers;
- normalized names;
- prefix indexes;
- full-text search;
- vector similarity;
- geographic constraints;
- temporal constraints.

---

# 40. Similarity

Similarity may use:

- exact;
- edit distance;
- token similarity;
- phonetic provider;
- vector similarity;
- application-defined score.

---

# 41. Entity match

```text
EntityMatch {
    source
    target
    evidence
    score
    method
    revision
}
```

---

# 42. Match score

Score is evidence metadata, not identity authority.

---

# 43. Automatic merge

Not enabled by default.

---

# 44. Merge policy

Application may define:

```text
RequireApproval
AutoMerge
SuggestOnly
Reject
```

---

# 45. Merge provenance

Merged entities retain source identities and evidence.

---

# 46. Split entity

A mistaken merge can be reversed through a new graph revision.

---

# 47. Entity aliases after split

Historical aliases remain provenance metadata.

---

# 48. Graph assertions

A fact is represented as an assertion.

```text
Assertion {
    subject
    predicate
    object
    provenance
    validity
}
```

---

# 49. Assertion confidence

Confidence is metadata.

It does not automatically become truth.

---

# 50. Evidence

An assertion may reference:

- document;
- database record;
- event;
- observation;
- human approval;
- model output.

---

# 51. Evidence provenance

Evidence records source revision.

---

# 52. Model-generated fact

Marked:

```text
source = Model
```

and can remain unverified.

---

# 53. Verified fact

Application may explicitly promote evidence.

---

# 54. Fact status

```text
Proposed
Verified
Rejected
Superseded
Expired
```

---

# 55. Temporal graph

Assertions may have:

```text
valid_from
valid_until
observed_at
recorded_at
```

---

# 56. Bitemporal support

Optional:

```text
valid_time
transaction_time
```

---

# 57. Historical queries

Queries can request graph state at a revision/time.

---

# 58. Graph revision

Every mutation creates a revision or transactionally advances revision.

---

# 59. Snapshot

Snapshot references an immutable graph revision.

---

# 60. Transaction

Graph transactions support:

- create;
- update;
- delete;
- relation changes.

---

# 61. Atomic transaction

Within one graph partition, transaction is atomic.

---

# 62. Distributed transaction

Not mandatory.

Cross-partition operations use explicit coordination semantics.

---

# 63. Optimistic concurrency

Transactions may specify expected graph/entity generation.

---

# 64. Conflict

Conflict includes:

```text
EntityGenerationMismatch
RelationGenerationMismatch
SchemaConflict
ConcurrentUpdate
```

---

# 65. Conflict resolution

Uses explicit application policy.

---

# 66. Distributed graph

628 provides replication.

---

# 67. Graph partitioning

Possible partition keys:

```text
EntityId
TenantId
DomainId
GeographicRegion
ApplicationDefined
```

---

# 68. Graph locality

Graph planner tries to keep traversal local.

---

# 69. Cross-partition traversal

Explicitly bounded.

---

# 70. Traversal budget

```text
max_depth
max_nodes
max_edges
max_bytes
max_time
max_partitions
```

---

# 71. Graph query

Typed AST.

```text
GraphQuery {
    source
    pattern
    filters
    projection
    order
    limit
}
```

---

# 72. Pattern matching

Supports:

```text
EntityPattern
RelationPattern
PathPattern
PropertyPattern
```

---

# 73. Example

```text
Person
  -[WORKS_AT]->
Company
```

---

# 74. Multi-hop query

```text
Person
 → WorksAt
 → Company
 → LocatedIn
 → City
```

---

# 75. Path query

Find paths between two entities.

---

# 76. Path constraints

Can specify:

```text
max_length
allowed_relations
forbidden_relations
```

---

# 77. Shortest path

Provider supports weighted/unweighted shortest path.

---

# 78. Reachability

Determine whether target is reachable under constraints.

---

# 79. Neighborhood query

Retrieve N-hop neighborhood.

---

# 80. Subgraph query

Return induced or explicitly matched subgraph.

---

# 81. Graph filters

Property predicates:

```text
=
!=
<
<=
>
>=
IN
CONTAINS
PREFIX
```

---

# 82. Boolean expressions

```text
AND
OR
NOT
```

---

# 83. Graph aggregation

Supports:

```text
COUNT
SUM
MIN
MAX
AVG
```

via 642 execution where appropriate.

---

# 84. Group by

Group by:

- entity type;
- property;
- relation type;
- temporal bucket.

---

# 85. Graph analytics

Supported primitives:

```text
Degree
InDegree
OutDegree
ConnectedComponents
ShortestPath
PageRankLike
Centrality
CommunityDetection
TriangleCount
NeighborhoodCount
```

---

# 86. Analytics boundary

Large graph analytics can delegate to 630/642.

---

# 87. Deterministic analytics

Algorithms specify deterministic tie-breaking.

---

# 88. Approximate algorithms

Must explicitly declare approximation and error metadata.

---

# 89. Graph statistics

Maintain:

- node count;
- edge count;
- type distribution;
- degree distribution;
- property cardinality.

---

# 90. Query planner

Logical graph query → physical graph plan.

---

# 91. Physical operators

```text
NodeScan
EdgeScan
IndexLookup
Expand
Filter
Join
Intersect
Union
Aggregate
Sort
Limit
PathExpand
Exchange
```

---

# 92. Index types

```text
EntityIdIndex
PropertyIndex
TypeIndex
RelationIndex
AdjacencyIndex
FullTextIndex
VectorIndex
TemporalIndex
```

---

# 93. Adjacency storage

Core optimized structure:

```text
node → outgoing edges
node → incoming edges
```

---

# 94. Compressed adjacency

Large graphs may use compressed adjacency lists.

---

# 95. Property storage

Hot properties may be columnar through 642.

---

# 96. Search integration

641 indexes entity/relation textual properties.

---

# 97. Vector integration

643 generates embeddings.

641 indexes them.

645 stores embedding provenance.

---

# 98. Semantic search

Query:

```text
text
→ embedding
→ vector search
→ entities
→ graph expansion
```

---

# 99. Graph RAG

644 can perform:

```text
question
→ graph retrieval
→ entity expansion
→ evidence collection
→ context
→ model
```

---

# 100. Graph-aware agent

644 may expose:

```text
graph.search
graph.query
graph.expand
graph.path
graph.entity
```

as tools.

---

# 101. Tool security

Each graph operation requires appropriate capability.

---

# 102. Tenant graph isolation

Graphs can be tenant-scoped.

---

# 103. Cross-tenant traversal

Denied by default.

---

# 104. Data governance

640 metadata attaches to:

- entities;
- relations;
- properties;
- graph partitions;
- derived embeddings.

---

# 105. Classification propagation

Derived graph facts inherit applicable classification unless explicitly downgraded by policy.

---

# 106. Residency

Graph partition placement must satisfy residency.

---

# 107. Retention

Entity/relation retention can differ.

---

# 108. Deletion

Deleting source data must propagate to derived graph facts when required by governance.

---

# 109. Lineage

Every derived assertion may contain lineage:

```text
source entities
source documents
transformation
agent
model
tool
execution
```

---

# 110. Provenance graph

645 can represent lineage itself as graph data.

---

# 111. Provenance recursion

Lineage depth is bounded.

---

# 112. Evidence graph

Evidence can itself be represented as linked entities.

---

# 113. Knowledge confidence

Confidence values use typed numeric representation.

---

# 114. Confidence semantics

Runtime does not interpret a confidence score as probability unless explicitly declared.

---

# 115. Semantic relation

Relations can specify semantic properties:

```text
symmetric
transitive
reflexive
functional
inverse
```

---

# 116. Inverse relation

Example:

```text
parent_of
child_of
```

---

# 117. Symmetric relation

Example:

```text
married_to
```

---

# 118. Transitive relation

Example:

```text
ancestor_of
```

---

# 119. Functional relation

A subject has at most one object under a declared constraint.

---

# 120. Constraint validation

Graph writes validate declared semantic constraints.

---

# 121. Constraint violation

Returns explicit error.

---

# 122. Inference

645 may support explicit rule-based inference.

---

# 123. Rule

```text
Rule {
    premises
    conclusion
}
```

---

# 124. Rule execution

Rules are deterministic and bounded.

---

# 125. No arbitrary code in rules

Rules cannot invoke native functions implicitly.

---

# 126. Rule recursion

Recursion depth and derived-fact count bounded.

---

# 127. Materialized inference

Derived facts can be stored with provenance.

---

# 128. Virtual inference

Derived facts can be computed at query time.

---

# 129. Inference mode

```text
None
Materialized
OnQuery
Hybrid
```

---

# 130. Rule provenance

Derived assertion records rule ID/version.

---

# 131. Rule invalidation

Changing rule version may require recomputation.

---

# 132. Ontology reasoning

Basic operations:

```text
subclass
subproperty
equivalence
disjointness
domain
range
inverse
```

---

# 133. Reasoning limits

No unrestricted theorem prover in the core.

---

# 134. External reasoning

Advanced reasoners may be providers.

---

# 135. Knowledge graph embedding

645 can reference embeddings generated by 643.

---

# 136. Embedding model identity

Recorded with embedding.

---

# 137. Embedding version

Changing embedding model creates a new embedding generation.

---

# 138. Graph embedding

Possible representations:

```text
EntityEmbedding
RelationEmbedding
SubgraphEmbedding
```

---

# 139. Embedding index

641.

---

# 140. Semantic entity search

Find entities by vector similarity.

---

# 141. Hybrid entity search

Combine:

- exact ID;
- lexical;
- graph constraints;
- vector similarity.

---

# 142. Entity resolution + vector

Vector similarity can generate candidates but does not automatically merge entities.

---

# 143. Graph query language

Native typed API is canonical.

---

# 144. Textual query boundary

Optional graph query language may resemble:

```text
MATCH
WHERE
RETURN
```

but is not required for compiler/runtime correctness.

---

# 145. SPARQL boundary

Optional external compatibility provider.

---

# 146. Cypher boundary

Optional external compatibility provider.

---

# 147. Query compilation

Text query → typed graph AST.

---

# 148. Injection safety

Parameters are bound separately from query syntax.

---

# 149. Query fingerprints

Normalized query produces deterministic fingerprint.

---

# 150. Plan cache

Plans keyed by:

```text
query_fingerprint
schema_fingerprint
statistics_revision
policy_revision
```

---

# 151. Policy-aware planning

Planner cannot choose a plan that exposes forbidden data.

---

# 152. Result filtering

Authorization is applied before final result exposure.

---

# 153. Side-channel protection

Counts/facets/path existence may require policy filtering.

---

# 154. Query explanation

```text
graph.explain(query)
```

returns:

- logical plan;
- physical plan;
- indexes;
- partitions;
- estimated cost;
- policy constraints.

---

# 155. Cost model

Uses:

- node count;
- edge count;
- degree;
- selectivity;
- partition locality;
- statistics.

---

# 156. Cost model determinism

Given same statistics and configuration, planner produces same plan.

---

# 157. Distributed query

```text
Coordinator
    ↓
Partition workers
    ↓
Local graph operations
    ↓
Exchange
    ↓
Merge
```

---

# 158. Distributed traversal

Frontier-based execution.

---

# 159. Frontier

Current entity IDs to expand.

---

# 160. Frontier deduplication

Generation-aware visited set prevents repeated expansion.

---

# 161. Traversal cycle

Cycles do not cause infinite traversal.

---

# 162. Traversal ordering

Deterministic ordering optional.

---

# 163. Distributed graph consistency

Queries specify:

```text
Local
Session
Causal
Quorum
Linearizable
Eventual
```

where supported by 628.

---

# 164. Staleness

Query can specify maximum acceptable graph revision lag.

---

# 165. Partial result

Distributed query may return partial result only when explicitly requested.

---

# 166. Partial result marker

```text
partial = true
failed_partitions[]
```

---

# 167. No false completeness

Partial results cannot be presented as complete.

---

# 168. Graph replication

628 handles:

- primary/replica;
- multi-primary;
- async replication;
- conflict metadata.

---

# 169. Graph conflict

Possible conflicts:

- entity property;
- relation;
- schema;
- ontology;
- inference result.

---

# 170. Conflict resolver

Application-defined.

---

# 171. CRDT boundary

Simple graph metadata may use CRDT providers.

---

# 172. Graph transaction log

634 may transport graph mutations.

---

# 173. Event sourcing

Graph mutations can be emitted as typed events.

---

# 174. Event type

```text
EntityCreated
EntityUpdated
EntityDeleted
RelationCreated
RelationUpdated
RelationDeleted
OntologyChanged
AssertionVerified
AssertionRejected
```

---

# 175. Search index updates

641 can consume graph mutation events.

---

# 176. Analytics updates

642 can consume graph change streams.

---

# 177. Agent memory updates

644 can consume graph events.

---

# 178. Feature generation

Graph-derived features can feed 643 training.

---

# 179. Feature lineage

640 records graph → feature → model lineage.

---

# 180. ML model knowledge

Models can be graph entities.

---

# 181. Model relations

Example:

```text
Model
 ├── trained_on → Dataset
 ├── version_of → Model
 ├── deployed_as → Service
 └── generated_by → TrainingRun
```

---

# 182. Service graph

631 service metadata can be represented in 645.

---

# 183. Deployment graph

636 deployments can be represented as entities/relations.

---

# 184. Infrastructure knowledge

635 nodes/clusters can be represented.

---

# 185. Package knowledge

625/613 packages can be represented.

---

# 186. Governance graph

640 lineage can map directly to graph representation.

---

# 187. Policy graph

639 policy relationships can be represented as metadata but policy enforcement remains 639.

---

# 188. Security graph

603 identities/capabilities can be represented for analysis.

---

# 189. Security boundary

Graph representation never grants security authority.

---

# 190. Knowledge graph API

```text
graph.create_entity()
graph.get_entity()
graph.update_entity()
graph.delete_entity()

graph.create_relation()
graph.get_relation()
graph.update_relation()
graph.delete_relation()

graph.query()
graph.traverse()
graph.path()
graph.neighborhood()
graph.explain()
```

---

# 191. Entity API

```text
entity.get<T>()
entity.set<T>()
entity.remove()
entity.relations()
```

---

# 192. Relation API

```text
relation.source()
relation.target()
relation.type()
relation.properties()
relation.provenance()
```

---

# 193. Snapshot API

```text
graph.snapshot()
snapshot.query()
snapshot.traverse()
```

---

# 194. Transaction API

```text
graph.transaction(fn)
```

---

# 195. Struct-only model

Không có class hierarchy bắt buộc.

---

# 196. Trait model

Optional traits:

```text
GraphEntity
GraphRelation
GraphQueryable
GraphPersistable
GraphProvenance
GraphTemporal
```

---

# 197. Compiler metadata

```text
@graph
@entity
@relation
@property
@ontology
@taxonomy
@concept
@assertion
@evidence
@provenance
@temporal
@index
@vector
@inference
@rule
@graph_query
@partition
```

---

# 198. Generated artifacts

```text
.axgraph
.axentity
.axrelation
.axontology
.axtaxonomy
.axassertion
.axprovenance
.axgraphquery
.axgraphindex
```

---

# 199. Graph schema example

```text
@entity
struct Person {
    id: EntityId
    name: String
    birth_year: i32
}

@entity
struct Company {
    id: EntityId
    name: String
}

@relation
struct Employment {
    person: Person
    company: Company
    role: String
}
```

---

# 200. Query example

```text
graph.query {
    Person
      -> Employment
      -> Company

    where Company.name == "Example"
    return Person.name
}
```

---

# 201. Graph traversal example

```text
graph.traverse(
    start = person,
    relation = "works_at",
    depth = 2
)
```

---

# 202. Inference example

```text
rule {
    Person(x) AND
    Parent(x, y)
    =>
    Ancestor(x, y)
}
```

---

# 203. Entity resolution example

```text
resolver.match(
    source_record,
    candidates
)
```

returns candidate matches with evidence.

---

# 204. Agent integration

644 can expose:

```text
KnowledgeTool
EntityLookupTool
GraphQueryTool
GraphTraversalTool
EvidenceTool
```

---

# 205. RAG integration

Graph retrieval can produce:

```text
entities
relations
evidence
paths
```

for context assembly.

---

# 206. Structured context

Graph context should preferably be passed as structured data instead of arbitrary serialized prose.

---

# 207. Context compression

Large subgraphs can be summarized while retaining source references.

---

# 208. Citation preservation

Compressed graph context must preserve evidence references.

---

# 209. Graph-to-text

Optional provider converts subgraph to natural language.

---

# 210. Text-to-graph

Optional model-assisted extraction produces proposed assertions.

---

# 211. Extraction pipeline

```text
Document
 → NLP/model
 → CandidateEntities
 → CandidateRelations
 → Validation
 → Policy
 → Commit
```

---

# 212. Extraction trust

Model extraction remains `Proposed` until validation policy permits promotion.

---

# 213. Schema extraction

Model can suggest ontology changes, but cannot directly mutate ontology.

---

# 214. Ontology approval

Ontology changes may require explicit 639 approval.

---

# 215. Graph evolution

Schema evolution uses 612-compatible migration mechanisms.

---

# 216. Migration

Migration can:

- rename property;
- split entity type;
- merge types;
- create derived relation;
- transform property.

---

# 217. Migration provenance

Every migrated record references migration version.

---

# 218. Online migration

New schema generation can coexist with old generation.

---

# 219. Atomic activation

New graph schema activates atomically.

---

# 220. Rollback

Rollback means selecting previous immutable generation, not reversing arbitrary historical side effects.

---

# 221. Graph compaction

Storage compaction is distinct from semantic deletion.

---

# 222. Tombstones

Deleted entities/relations retain tombstones until replication/recovery guarantees permit reclamation.

---

# 223. Garbage collection

Graph storage reclamation is storage maintenance, not language GC.

---

# 224. Memory safety

Graph handles use generation-safe IDs.

---

# 225. No raw pointer API

Public graph API does not expose raw pointers.

---

# 226. Zero-copy

Read-only graph views may use memory-mapped/owned buffers.

---

# 227. Serialization

612 serializes graph schemas/results.

---

# 228. Storage

611 stores local graph data.

---

# 229. Distributed storage

628 replicates graph state.

---

# 230. Compression

613 compresses graph segments.

---

# 231. Encryption

610/638 secure graph data.

---

# 232. Package

613/625 distributes ontology/schema/graph snapshots.

---

# 233. Configuration

601/637 controls graph runtime parameters.

---

# 234. Policy

639 controls graph operations.

---

# 235. Governance

640 controls data lifecycle.

---

# 236. Scheduler

607 executes graph operations.

---

# 237. Compute

630 handles distributed graph analytics.

---

# 238. Observability

633 monitors graph workload.

---

# 239. Event stream

634 distributes graph changes.

---

# 240. Deployment

636 deploys graph services.

---

# 241. Service

631 exposes graph API.

---

# 242. Gateway

632 exposes external graph API.

---

# 243. Resource limits

606 controls:

```text
nodes_scanned
edges_scanned
memory
CPU
partitions
network
query_time
```

---

# 244. Query cancellation

Graph queries support cancellation/deadline.

---

# 245. Backpressure

Streaming traversal supports bounded buffers.

---

# 246. Streaming graph query

Results can be streamed.

---

# 247. Pagination

Cursor-based pagination preferred.

---

# 248. Cursor

Cursor contains:

```text
query_fingerprint
graph_revision
sort_state
expiry
```

---

# 249. Cursor security

Cursor is opaque and signed/bound where required.

---

# 250. Query cache

Cache key includes:

```text
query
graph_revision
policy_revision
governance_fingerprint
```

---

# 251. Cache invalidation

Graph mutations invalidate affected entries.

---

# 252. Semantic cache

Derived semantic answers must carry source revision.

---

# 253. Stale semantic cache

Stale answers are explicitly marked.

---

# 254. No silent stale truth

Application chooses whether stale knowledge is acceptable.

---

# 255. Graph snapshot export

Can export:

```text
entities
relations
schema
ontology
provenance
```

---

# 256. Import

Import validates:

- schema;
- IDs;
- provenance;
- governance;
- signatures.

---

# 257. Signed graph snapshot

Optional signed package.

---

# 258. Trust

Snapshot publisher identity comes from 638.

---

# 259. External graph provider

```text
NativeGraphProvider
ExternalGraphProvider
RemoteGraphProvider
TestGraphProvider
```

---

# 260. External providers

May map to:

- Neo4j;
- RDF stores;
- property graph databases;
- graph analytics engines.

Compatibility adapters are optional.

---

# 261. No vendor lock-in

Native semantic API remains canonical.

---

# 262. Graph schema fingerprint

Stable fingerprint derived from canonical schema.

---

# 263. Ontology fingerprint

Stable fingerprint derived from canonical ontology.

---

# 264. Query fingerprint

Stable canonical AST fingerprint.

---

# 265. Provenance fingerprint

Derived transformations can be uniquely identified.

---

# 266. AI-readable metadata

All graph artifacts contain machine-readable schemas and relationships.

---

# 267. Graph inspection CLI

```text
axiom graph inspect
axiom graph entity
axiom graph relation
axiom graph query
axiom graph path
axiom graph neighbors
axiom graph schema
axiom graph ontology
axiom graph provenance
axiom graph explain
```

---

# 268. Entity resolution CLI

```text
axiom graph resolve
axiom graph candidates
axiom graph merge
axiom graph split
```

---

# 269. Governance CLI

```text
axiom graph why-blocked
axiom graph residency
axiom graph retention
axiom graph lineage
```

---

# 270. Graph health

Metrics:

```text
node_count
edge_count
partition_count
query_latency
traversal_depth
cache_hit_rate
replication_lag
index_lag
```

---

# 271. Semantic health

Metrics:

```text
unresolved_entities
conflicting_assertions
stale_assertions
orphan_relations
schema_violations
```

---

# 272. No automatic truth scoring

Runtime reports metadata; it does not declare a global truth score.

---

# 273. Data quality

642 can analyze graph quality.

---

# 274. Entity quality

641 can detect duplicate candidates.

---

# 275. ML-assisted quality

643 may generate suggestions.

---

# 276. Human review

619/629 can support review workflows.

---

# 277. Review provenance

Human approval/rejection is recorded.

---

# 278. Knowledge lifecycle

```text
Candidate
→ Validating
→ Accepted
→ Active
→ Superseded
→ Retired
```

---

# 279. Rejected knowledge

Retained according to governance for audit/provenance where permitted.

---

# 280. Knowledge expiration

Temporal assertions can expire without deleting historical evidence.

---

# 281. Contradiction

Graph can contain contradictory assertions if evidence conflicts.

---

# 282. Contradiction representation

Contradictory assertions coexist with provenance.

---

# 283. Contradiction query

Application can request conflicting facts.

---

# 284. Conflict resolution

Policy determines which assertion is used operationally.

---

# 285. No hidden truth resolution

Graph does not silently erase contradictory evidence.

---

# 286. Semantic constraints

Can express:

```text
requires
forbids
cardinality
domain
range
```

---

# 287. Constraint enforcement

Write-time or query-time.

---

# 288. Constraint cost

Constraints have declared computational bounds.

---

# 289. Rule execution resource

Rules consume 606 budget.

---

# 290. Rule timeout

Inference terminates on timeout.

---

# 291. Rule result limit

Maximum derived facts.

---

# 292. Recursive inference

Maximum depth.

---

# 293. Knowledge extraction resource

Model calls governed by 643/606.

---

# 294. Knowledge extraction provenance

Each extracted fact references model/version and source.

---

# 295. Extraction reproducibility

Store:

```text
source_revision
model_version
prompt_schema
ontology_version
```

---

# 296. Model-generated ontology

Must be proposal only by default.

---

# 297. Graph-backed RAG

Preferred architecture:

```text
641
Search
 │
 ├── entity candidates
 └── documents
        │
        ▼
645
Knowledge graph
        │
        ▼
graph expansion
        │
        ▼
644
Agent
```

---

# 298. Graph-backed training

Graph-derived datasets feed 643.

---

# 299. Training lineage

640 records:

```text
graph revision
→ dataset revision
→ training run
→ model
```

---

# 300. Model knowledge provenance

Model artifact can reference knowledge graph snapshot used during training.

---

# 301. Inference provenance

Inference can reference graph snapshot used for retrieval.

---

# 302. Knowledge freshness

Agent can request:

```text
max_graph_age
required_revision
```

---

# 303. Freshness failure

If freshness cannot be satisfied:

```text
KnowledgeStale
```

---

# 304. Offline graph

Edge devices can hold signed graph snapshots.

---

# 305. Edge synchronization

636/635/628 manage synchronization.

---

# 306. Conflict during edge sync

Explicit conflict resolution.

---

# 307. Federation

Graphs may federate across clusters.

---

# 308. Federation trust

638 establishes trust.

---

# 309. Federation query

Cross-graph query requires explicit permission.

---

# 310. Federation query limits

Each graph has independent resource/security boundaries.

---

# 311. Federation failure

Partial result semantics apply.

---

# 312. Graph gateway

632 can expose graph APIs.

---

# 313. Graph service

631 can expose graph operations internally.

---

# 314. Graph workflow

629 can orchestrate:

```text
extract
→ resolve
→ validate
→ enrich
→ publish
```

---

# 315. Graph events

634 provides incremental updates.

---

# 316. Graph indexing

641 receives updates.

---

# 317. Graph analytics

642 receives snapshots/materializations.

---

# 318. Graph ML

643 consumes graph features/embeddings.

---

# 319. Agent

644 consumes graph knowledge.

---

# 320. Complete integration matrix

```text
600  State/Checkpoint
601  Configuration
602  Diagnostics
603  Security/Capability
604  IPC
605  Supervision
606  Resource
607  Scheduler
608  Synchronization
609  Network
610  Crypto
611  Storage
612  Serialization
613  Package/CAS
614  Device
615  Graphics
616  Media
617  Text
618  Input
619  GUI
620  Reactive State
621  Documents
622  Navigation
623  Plugins
624  Scripting
625  Package Registry
626  HTTP/API
627  Identity
628  Distributed Data
629  Workflow
630  Distributed Compute
631  Services
632  Gateway
633  Observability
634  Events
635  Cluster
636  Deployment
637  Dynamic Config
638  Credentials
639  Policy
640  Data Governance
641  Search
642  Analytics
643  ML
644  AI Agent
645  Knowledge Graph
```

---

# 321. Core invariants

1. Entity IDs are generation-safe.
2. Relation endpoints must resolve or be explicitly deferred.
3. Relation direction is explicit.
4. Graph revisions are monotonic.
5. Snapshots are immutable.
6. Transactions are atomic within declared scope.
7. Stale writers cannot overwrite newer generations.
8. Query execution is resource bounded.
9. Traversal is depth bounded.
10. Traversal is node/edge bounded.
11. Cycles cannot cause infinite execution.
12. Cross-partition execution is explicit.
13. Partial distributed results are marked.
14. Search results retain provenance.
15. Vector embeddings retain model identity.
16. Derived assertions retain provenance.
17. Model-generated facts are not implicitly verified.
18. Contradictory facts may coexist.
19. Inference is explicitly enabled.
20. Inference is bounded.
21. Rule execution cannot execute arbitrary code.
22. Ontology versions are immutable.
23. Schema changes are versioned.
24. Migrations are versioned.
25. Graph deletion obeys governance.
26. Retention cannot be bypassed.
27. Residency cannot be bypassed.
28. Authorization cannot be bypassed.
29. Capability cannot be created by graph data.
30. Agent output cannot grant graph authority.
31. Query caches include policy revision.
32. Query caches include graph revision.
33. Stale caches are marked.
34. Cursor state is bound to query generation.
35. External providers cannot expand authority.
36. Graph snapshots can be cryptographically verified.
37. Large graph operations can spill or fail explicitly.
38. No mandatory garbage collector.
39. Public API does not expose raw pointers.
40. Native implementation is possible without external graph DB.
41. External graph databases are adapters.
42. SQL/graph textual languages are compatibility layers.
43. Typed graph AST is canonical.
44. Query parameters are separate from syntax.
45. Security metadata is separate from graph payload.
46. Governance metadata is separate from payload.
47. Secrets are never logged by default.
48. Model extraction is traceable.
49. Human review is traceable.
50. Federation authority remains local.
51. Cross-tenant traversal is denied by default.
52. Graph state can be checkpointed.
53. Replication uses explicit consistency semantics.
54. Exactly-once distributed graph mutation is not assumed.
55. Event replay is idempotent.
56. Search/index updates are versioned.
57. Analytics snapshots identify graph revision.
58. Training data identifies graph revision.
59. Agent retrieval identifies graph revision.
60. Knowledge provenance survives transformation.

---

# 322. Acceptance target

**≥500 acceptance criteria**

Các nhóm kiểm thử tối thiểu:

- graph CRUD;
- schema;
- ontology;
- taxonomy;
- entity identity;
- entity resolution;
- merge/split;
- relations;
- properties;
- temporal graph;
- provenance;
- evidence;
- confidence;
- inference;
- rule execution;
- query parsing;
- typed AST;
- graph planning;
- indexing;
- traversal;
- shortest path;
- neighborhood;
- aggregation;
- graph analytics;
- distributed query;
- replication;
- consistency;
- federation;
- security;
- capability;
- policy;
- governance;
- residency;
- retention;
- deletion;
- search integration;
- vector integration;
- ML integration;
- RAG;
- agent integration;
- event integration;
- workflow integration;
- checkpoint;
- recovery;
- migration;
- package;
- snapshot;
- import/export;
- performance;
- memory safety;
- fuzzing;
- fault injection;
- deterministic execution.

---

# 323. Profiles

```text
AXGRAPH_NONE
AXGRAPH_CORE
AXGRAPH_SCHEMA
AXGRAPH_QUERY
AXGRAPH_TRAVERSAL
AXGRAPH_ONTOLOGY
AXGRAPH_PROVENANCE
AXGRAPH_RESOLUTION
AXGRAPH_ANALYTICS
AXGRAPH_VECTOR
AXGRAPH_INFERENCE
AXGRAPH_DISTRIBUTED
AXGRAPH_FEDERATION
AXGRAPH_RAG
AXGRAPH_AI
AXGRAPH_FULL
```

---

# 324. Minimal profile

`AXGRAPH_CORE` chỉ cần:

```text
Entity
Relation
Property
Graph
CRUD
Snapshot
Transaction
```

Không kéo theo:

- ontology;
- inference;
- vector;
- distributed runtime.

---

# 325. AI profile

`AXGRAPH_AI` bổ sung:

```text
semantic retrieval
entity resolution
embeddings
provenance
RAG
agent integration
```

---

# 326. Distributed profile

`AXGRAPH_DISTRIBUTED` bổ sung:

```text
partition
replication
distributed query
federation
```

---

# 327. Final architecture

```text
                       AXIOM KNOWLEDGE PLANE

                           Application
                                │
                         ┌──────▼──────┐
                         │    644     │
                         │ AI Agent   │
                         └──────┬──────┘
                                │
                       ┌────────▼────────┐
                       │      645       │
                       │ KnowledgeGraph │
                       └────────┬───────┘
                                │
        ┌───────────────┬───────┼────────┬───────────────┐
        ▼               ▼       ▼        ▼               ▼
     Entity          Ontology Query   Inference       Provenance
        │               │       │        │               │
        └───────────────┴───────┼────────┴───────────────┘
                                ▼
                         Graph Execution
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
             641               642               643
           Search            Analytics            ML
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ▼
                              628
                       Distributed Data
                                │
                   ┌────────────┼────────────┐
                   ▼            ▼            ▼
                  634          635          640
                 Events       Cluster     Governance
```

---

# 328. Kết quả kiến trúc

Sau BOOTSTRAP-645, Axiom có đủ các lớp để xây một hệ thống:

```text
Raw Data
   ↓
Storage
   ↓
Analytics/Search
   ↓
Knowledge Graph
   ↓
Embedding / ML
   ↓
RAG
   ↓
AI Agent
   ↓
Tools / Services / Workflow
   ↓
Distributed Deployment
```

Điểm quan trọng nhất là các lớp này **không bị khóa vào một framework AI duy nhất**.

Axiom có thể xây:

- chatbot;
- RAG;
- knowledge assistant;
- coding agent;
- enterprise search;
- recommendation system;
- graph analytics;
- AI automation;
- local AI;
- edge AI;
- distributed AI.

mà không cần biến toàn bộ ngôn ngữ thành một DSL dành riêng cho AI.

---

# 329. Trạng thái

**BOOTSTRAP-645 — COMPLETE**

### Task kế tiếp

**BOOTSTRAP-646 — Native AI Evaluation, Benchmarking, Dataset Validation, Model Validation, Safety Testing, Red-Team Simulation & AI Quality Runtime 5.0**
:::