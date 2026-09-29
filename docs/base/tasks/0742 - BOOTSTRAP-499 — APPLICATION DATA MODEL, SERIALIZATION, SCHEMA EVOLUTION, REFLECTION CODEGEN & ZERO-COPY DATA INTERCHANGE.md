# BOOTSTRAP-499 — APPLICATION DATA MODEL, SERIALIZATION, SCHEMA EVOLUTION, REFLECTION CODEGEN & ZERO-COPY DATA INTERCHANGE

**Trạng thái: COMPLETED / LOCKED**

499 chuẩn hóa tầng **data interchange** của Axiom: dữ liệu trong memory, dữ liệu serialized, schema, versioning và zero-copy phải được phân biệt rõ.

Nó nối:

```text id="a7m2x9"
430 Type System
      ↓
422 Memory Representation
      ↓
431 Comptime / Reflection
      ↓
446 Semantic Metadata
      ↓
454 Networking
455 Storage
467 Clipboard/Data Transfer
498 Resources
      ↓
499 Data Model / Serialization
      ↓
500 IPC / RPC / Interchange
```

Nguyên tắc trung tâm:

> **Serialization là chuyển đổi dữ liệu có schema; không được biến serialization thành một object runtime magic hoặc một hệ thống reflection bắt buộc.**

---

## 499.1 — Data domain

Axiom phân biệt:

```text id="m8q3v1"
Source Data
Semantic Value
In-Memory Representation
Serialized Representation
Transport Representation
Persistent Representation
```

Không mặc định chúng có cùng layout.

---

## 499.2 — Serialization

Serialization:

```text
Value → Bytes
```

---

## 499.3 — Deserialization

Deserialization:

```text
Bytes → Value
```

và có thể thất bại:

```text
Result<T, DecodeError>
```

---

## 499.4 — Encoding ≠ serialization

Encoding có thể chỉ là representation conversion:

```text
UTF-8
UTF-16
Base64
Hex
```

Serialization có schema/data semantics.

---

## 499.5 — Schema

Schema mô tả:

- fields;
- types;
- optionality;
- defaults;
- version;
- constraints;
- encoding.

---

## 499.6 — Schema identity

Schema có stable identity:

```text id="q5m9x2"
SchemaId
SchemaVersion
```

---

## 499.7 — Schema hash

Canonical schema có semantic hash.

---

## 499.8 — Schema evolution

Schema có thể tiến hóa mà không nhất thiết invalidate mọi historical data.

---

## 499.9 — Field identity

Field identity nên dựa vào stable field ID khi format hỗ trợ.

---

## 499.10 — Field rename

Rename có thể preserve field identity.

---

## 499.11 — Field removal

Removed field phải có compatibility policy.

---

## 499.12 — Field addition

New optional/defaulted field có thể backward-compatible tùy format.

---

## 499.13 — Required field addition

Required field addition là potentially breaking schema change.

---

## 499.14 — Field type change

Type changes phải được classify.

---

## 499.15 — Numeric widening

Ví dụ:

```text
i32 → i64
```

có thể có migration riêng; không tự coi universally compatible.

---

## 499.16 — Numeric narrowing

Narrowing cần explicit conversion/migration.

---

## 499.17 — Enum evolution

Adding enum variants phải có unknown-variant policy.

---

## 499.18 — Unknown enum variant

Decoder có thể:

```text id="x3m7p1"
reject
preserve
map-to-unknown
```

tùy schema.

---

## 499.19 — Optional fields

Optional field semantics không đồng nghĩa với zero/default value.

---

## 499.20 — Nullability

Axiom dùng `Option<T>` cho optional semantic values.

---

## 499.21 — Default values

Schema defaults phải deterministic.

---

## 499.22 — Default computation

Default không được chạy arbitrary runtime code khi decoding.

---

## 499.23 — Validation

Decode có thể gồm:

```text
syntax validation
schema validation
semantic validation
```

---

## 499.24 — Decode safety

Malformed input không được gây memory unsafety.

---

## 499.25 — Untrusted data

Network/storage/clipboard/resource data đều được coi là untrusted input theo 445/454/455/467/498.

---

## 499.26 — Bounds checking

Length/count/offset phải được validate trước memory access.

---

## 499.27 — Integer overflow

Length arithmetic phải overflow-safe.

---

## 499.28 — Resource limits

Decoder có thể enforce:

```text id="p8m2x4"
max_bytes
max_depth
max_items
max_string
max_allocation
```

---

## 499.29 — Recursion limit

Recursive schemas phải có bounded decoding.

---

## 499.30 — Streaming decoder

Decoder không cần load toàn bộ input.

---

## 499.31 — Streaming encoder

Encoder có thể emit từng phần.

---

## 499.32 — Incremental decoding

Large message có thể decode incrementally.

---

## 499.33 — Backpressure

Streaming serialization integrate 454/471.

---

## 499.34 — Cancellation

Async decoding có thể cancel.

---

## 499.35 — Zero-copy principle

Zero-copy chỉ được phép khi:

```text id="v4m8x1"
representation compatible
alignment valid
lifetime valid
endianness compatible
ownership valid
schema valid
```

---

## 499.36 — Borrowed view

Decoder có thể tạo view vào input buffer.

---

## 499.37 — View lifetime

View không được outlive backing buffer.

---

## 499.38 — Ownership

Owned decoded value và borrowed view phải phân biệt.

---

## 499.39 — Copy-on-demand

Có thể delay copy đến khi ownership cần thiết.

---

## 499.40 — Mutable zero-copy

Mutable zero-copy phải có exclusive ownership/alias guarantees.

---

## 499.41 — Serialized pointers

Serialized format không được chứa process-local raw pointers.

---

## 499.42 — Offsets

Offset references phải bounds-check.

---

## 499.43 — IDs

Cross-process references dùng IDs, không dùng addresses.

---

## 499.44 — Endianness

Binary formats phải define byte order.

---

## 499.45 — Alignment

Binary layout phải define alignment requirements.

---

## 499.46 — Padding

Padding bytes không được mặc định mang semantic data.

---

## 499.47 — Uninitialized bytes

Uninitialized memory không được serialize.

---

## 499.48 — Deterministic serialization

Canonical serialization phải deterministic.

---

## 499.49 — Map ordering

Map serialization phải có ordering policy nếu canonical bytes cần stable.

---

## 499.50 — Hashing

Canonical serialized representation có thể được dùng để hash/sign nếu format quy định canonicalization.

---

## 499.51 — Equality

Byte equality không mặc định đồng nghĩa semantic equality.

---

## 499.52 — Compression

Compression là transport/storage layer, không phải schema semantics.

---

## 499.53 — Encryption

Encryption là security layer, không phải serialization semantics.

---

## 499.54 — Authentication

MAC/signature được tách khỏi serialization.

---

## 499.55 — Format layers

Canonical:

```text id="h2x7m4"
Schema
  ↓
Serialization
  ↓
Compression
  ↓
Encryption
  ↓
Transport / Storage
```

---

## 499.56 — Codec abstraction

Conceptual:

```text id="c5m8x2"
trait Encoder<T> {
    fn encode(self, value: T, out: Writer) -> Result<unit, EncodeError>
}

trait Decoder<T> {
    fn decode(self, input: Reader) -> Result<T, DecodeError>
}
```

---

## 499.57 — Generic serialization

Generic implementations có thể dùng trait-based static dispatch.

---

## 499.58 — Dynamic serialization

Dynamic codec selection có thể dùng `dyn Trait` explicit.

---

## 499.59 — Comptime derive

Serialization implementation có thể được generate tại comptime.

---

## 499.60 — Reflection codegen

Compiler metadata 446 có thể cấp information cho generator.

---

## 499.61 — Generated codec

Generated codec phải là ordinary Axiom code/IR.

---

## 499.62 — No magic reflection

Compiler không tự inject reflection/runtime metadata.

---

## 499.63 — Runtime reflection

Runtime schema inspection là optional.

---

## 499.64 — Schema compiler

Schema compiler có thể generate:

- Axiom types;
- encoders;
- decoders;
- validators;
- docs;
- compatibility metadata.

---

## 499.65 — External schema

Axiom có thể consume external schemas.

---

## 499.66 — Schema provenance

Generated type phải retain schema source/version/hash.

---

## 499.67 — Schema-to-code

Canonical pipeline:

```text id="m4x8q2"
Schema
 ↓
Schema IR
 ↓
Axiom Type
 ↓
Generated Codec
 ↓
Semantic Validation
```

---

## 499.68 — Code-to-schema

Axiom types có thể generate schema khi representation/contracts đủ xác định.

---

## 499.69 — Explicit schema export

Không phải mọi type đều tự động export thành schema.

---

## 499.70 — Private fields

Private implementation details không được tự động trở thành public wire format.

---

## 499.71 — Wire representation

Wire schema phải độc lập với default in-memory layout nếu cần cross-version/platform compatibility.

---

## 499.72 — Stable ABI data

`@repr(C)` không tự biến struct thành stable serialization format.

---

## 499.73 — Version negotiation

Protocol peers có thể negotiate supported schema versions.

---

## 499.74 — Capability negotiation

Peer capabilities được phân biệt schema version.

---

## 499.75 — Compatibility matrix

Schema compatibility có thể report:

```text id="n3m7x1"
read-old/write-new
read-new/write-old
bidirectional
migration-required
incompatible
```

---

## 499.76 — Migration

Schema migration:

```text id="q8m2v5"
V1
 ↓
Migration
 ↓
V2
```

---

## 499.77 — Migration determinism

Migration phải deterministic trong standard mode.

---

## 499.78 — Migration errors

Migration dùng `Result`.

---

## 499.79 — Migration transaction

Persistent data migration phải transactional khi storage backend hỗ trợ.

---

## 499.80 — Lazy migration

Database/storage có thể lazy-migrate records.

---

## 499.81 — Eager migration

Tool có thể migrate toàn bộ dataset offline.

---

## 499.82 — Forward compatibility

Reader mới có thể preserve unknown fields khi format hỗ trợ.

---

## 499.83 — Backward compatibility

Reader cũ chỉ đọc được fields/version mà nó hiểu.

---

## 499.84 — Unknown fields

Policy:

```text id="r5x8m2"
ignore
preserve
reject
```

---

## 499.85 — Preservation

Preserving unknown fields phải giữ raw representation nếu schema cho phép.

---

## 499.86 — Canonicalization

Canonical encoding phải định nghĩa:

- field ordering;
- integer representation;
- string normalization policy;
- map ordering;
- optional encoding.

---

## 499.87 — Floating point

Binary format phải specify float representation/NaN policy nếu interoperability cần.

---

## 499.88 — String encoding

UTF-8 là default Axiom text representation nhưng external format có thể specify khác.

---

## 499.89 — Invalid UTF-8

Decoder phải reject hoặc explicit lossy conversion.

---

## 499.90 — Binary blobs

Opaque bytes dùng `ByteString`/`ByteView`, không giả dạng String.

---

## 499.91 — Date/time

Serialized timestamps phải specify:

- unit;
- epoch;
- timezone/offset semantics;
- valid range.

---

## 499.92 — Resource references

498 resources có thể serialize `ResourceId`.

---

## 499.93 — Storage integration

455 có thể serialize directly vào pages/WAL/records.

---

## 499.94 — Network integration

454 có thể use streaming codecs.

---

## 499.95 — IPC integration

500 sử dụng cùng data model nhưng transport-independent.

---

## 499.96 — Clipboard integration

467 representations có thể use serialization codecs.

---

## 499.97 — AI metadata

AI có thể query:

```text id="x4m7q2"
schema()
encoding()
compatibility()
fields()
generated_codec()
zero_copy_conditions()
```

---

## 499.98 — Testing

Phải có:

- round-trip;
- malformed input;
- fuzzing;
- schema evolution;
- compatibility;
- canonicalization;
- zero-copy lifetime;
- endian;
- overflow;
- resource limits.

---

## 499.99 — Performance

Benchmark:

- encode;
- decode;
- streaming;
- allocation;
- copy count;
- zero-copy;
- schema validation;
- generated vs generic codec.

---

## 499.100 — Hard invariants

1. Semantic value khác in-memory representation.
2. In-memory representation khác serialized representation.
3. Serialization khác encoding.
4. Schema là first-class metadata.
5. Schema có stable identity.
6. Schema có version.
7. Schema hash canonical.
8. Schema evolution được hỗ trợ.
9. Field identity có thể stable.
10. Rename có thể preserve identity.
11. Field removal có compatibility policy.
12. Field addition có compatibility policy.
13. Required field addition được classify.
14. Field type changes được classify.
15. Numeric widening không mặc định universally compatible.
16. Numeric narrowing cần explicit migration/conversion.
17. Enum evolution có policy.
18. Unknown enum variants có policy.
19. Optional khác default.
20. Option semantics được preserve.
21. Defaults deterministic.
22. Default decode không arbitrary runtime code.
23. Decode validation được phân tầng.
24. Malformed input không được gây memory unsafety.
25. External data là untrusted.
26. Length/count/offset phải bounds-check.
27. Arithmetic overflow phải được xử lý.
28. Resource limits được hỗ trợ.
29. Recursion depth được giới hạn.
30. Streaming decoder được hỗ trợ.
31. Streaming encoder được hỗ trợ.
32. Incremental decode được hỗ trợ.
33. Backpressure được hỗ trợ.
34. Async cancellation được hỗ trợ.
35. Zero-copy có preconditions rõ.
36. Borrowed view có lifetime constraint.
37. Owned và borrowed data được phân biệt.
38. Copy-on-demand được hỗ trợ.
39. Mutable zero-copy yêu cầu exclusive access.
40. Serialized data không chứa process-local pointers.
41. Offset references được validate.
42. Cross-process references dùng stable IDs.
43. Endianness explicit.
44. Alignment explicit.
45. Padding không mang implicit semantic.
46. Uninitialized bytes không được serialize.
47. Canonical serialization deterministic.
48. Map ordering có policy.
49. Canonical bytes có thể dùng hashing khi specified.
50. Byte equality không mặc định semantic equality.
51. Compression tách khỏi schema.
52. Encryption tách khỏi schema.
53. Authentication tách khỏi serialization.
54. Codec abstraction được hỗ trợ.
55. Generic codecs dùng traits.
56. Dynamic codecs explicit.
57. Comptime codec generation được hỗ trợ.
58. Reflection codegen dùng semantic metadata.
59. Generated codec là ordinary Axiom code/IR.
60. Runtime reflection không bắt buộc.
61. Schema compiler được hỗ trợ.
62. External schemas được hỗ trợ.
63. Schema provenance được preserve.
64. Schema-to-code được hỗ trợ.
65. Code-to-schema là explicit.
66. Private implementation không tự thành wire schema.
67. Wire representation độc lập in-memory layout khi cần.
68. `@repr(C)` không tự là serialization contract.
69. Version negotiation được hỗ trợ.
70. Capability negotiation tách khỏi version.
71. Compatibility matrix được hỗ trợ.
72. Schema migration được hỗ trợ.
73. Migration deterministic.
74. Migration errors dùng Result.
75. Persistent migration có thể transactional.
76. Lazy migration được hỗ trợ.
77. Eager migration được hỗ trợ.
78. Forward compatibility được hỗ trợ khi format cho phép.
79. Backward compatibility được classify.
80. Unknown fields có explicit policy.
81. Unknown-field preservation được hỗ trợ khi format cho phép.
82. Canonicalization rules explicit.
83. Float representation/NaN policy explicit khi interoperability cần.
84. UTF-8 default được giữ.
85. Invalid UTF-8 có explicit policy.
86. Binary bytes không giả dạng String.
87. Timestamp representation explicit.
88. Resource references dùng ResourceId.
89. Storage integration hỗ trợ.
90. Network integration hỗ trợ.
91. IPC integration hỗ trợ.
92. Clipboard/data-transfer integration hỗ trợ.
93. AI schema queries được hỗ trợ.
94. Round-trip testing bắt buộc.
95. Malformed/fuzz testing bắt buộc.
96. Evolution compatibility testing bắt buộc.
97. Zero-copy lifetime testing bắt buộc.
98. Performance đo copy/allocation.
99. Generic và generated codec được benchmark riêng.
100. **Axiom data interchange phải cho phép cùng một semantic value được biểu diễn hiệu quả trong memory, storage và network mà không nhầm lẫn các representation; schema, version, ownership, lifetime, validation và compatibility phải explicit, còn zero-copy chỉ được phép khi mọi điều kiện an toàn và representation đều được chứng minh.**

**BOOTSTRAP-499 hoàn tất / LOCKED.**

---

# BOOTSTRAP-500 — IPC, RPC, SERVICE MODEL, PROCESS COMMUNICATION, SHARED MEMORY & LOCAL/DISTRIBUTED API CONTRACT

**Trạng thái: COMPLETED / LOCKED**

500 hoàn thiện tầng giao tiếp giữa các component/process/service.

```text id="s8m3q1"
Axiom Application
       │
       ├── In-Process Call
       │
       ├── Thread / Channel
       │
       ├── IPC
       │    ├── Pipe
       │    ├── Unix Socket
       │    ├── Named Pipe
       │    ├── Shared Memory
       │    └── OS Message
       │
       └── Network RPC
            ├── TCP
            ├── QUIC
            └── HTTP/WebSocket
```

Nguyên tắc:

> **Local call, IPC và network RPC có thể chia sẻ contract/data model nhưng không được giả vờ có cùng failure, latency, ownership hoặc security semantics.**

---

## 500.1 — Communication domains

Phân biệt:

```text id="m2x7q5"
InProcess
ThreadLocal
InterThread
InterProcess
InterMachine
```

---

## 500.2 — Local function call

Function call không có communication serialization bắt buộc.

---

## 500.3 — IPC

IPC là communication giữa process/address spaces.

---

## 500.4 — RPC

RPC là invocation qua communication boundary.

---

## 500.5 — RPC illusion

Compiler không được giả định remote call có semantics giống local call.

---

## 500.6 — Endpoint

Conceptual:

```text id="q4m8x2"
Endpoint
```

có identity + transport + capability/security policy.

---

## 500.7 — Service

Service là logical provider của operations.

---

## 500.8 — Service interface

Interface gồm:

- methods/operations;
- request;
- response;
- errors;
- version;
- capabilities.

---

## 500.9 — Request

Request có stable operation ID.

---

## 500.10 — Response

Response có success/error representation.

---

## 500.11 — Error

Remote errors dùng typed `Result`.

---

## 500.12 — Transport error

Transport failure khác application error.

---

## 500.13 — Timeout

Timeout không tự chứng minh remote operation failed.

---

## 500.14 — Retry

Retry phải là explicit policy.

---

## 500.15 — Idempotency

Operation có thể declare idempotency semantics.

---

## 500.16 — Duplicate request

At-least-once delivery có thể produce duplicate operations.

---

## 500.17 — Exactly-once

Không được mặc định claim exactly-once.

---

## 500.18 — Cancellation

RPC cancellation explicit.

---

## 500.19 — Deadline

Deadline 474 truyền qua request context khi protocol hỗ trợ.

---

## 500.20 — Backpressure

Streaming RPC có backpressure.

---

## 500.21 — Streaming

Support:

```text id="n7x3m8"
Unary
ServerStream
ClientStream
BidirectionalStream
```

---

## 500.22 — Message framing

Transport protocol định nghĩa message boundaries.

---

## 500.23 — Serialization

499 codecs được dùng cho message payload.

---

## 500.24 — Compression

Compression explicit per transport/message policy.

---

## 500.25 — Encryption

TLS/security layer 454/490.

---

## 500.26 — Authentication

Authentication xác định peer identity.

---

## 500.27 — Authorization

Authorization quyết định peer được phép làm gì.

---

## 500.28 — Capability-based RPC

RPC endpoint có thể yêu cầu capability token/object.

---

## 500.29 — Capability attenuation

Delegated capability có thể giới hạn quyền.

---

## 500.30 — Capability lifetime

Capability có thể expire/revoke.

---

## 500.31 — IPC identity

OS process identity không đồng nghĩa application/service identity.

---

## 500.32 — Local authorization

OS security mechanisms có thể authorize IPC.

---

## 500.33 — Named endpoint

Endpoint names phải namespace-safe.

---

## 500.34 — Unix domain sockets

Được hỗ trợ trên platform phù hợp.

---

## 500.35 — Windows named pipes

Được hỗ trợ trên Windows.

---

## 500.36 — Anonymous pipes

Được hỗ trợ cho parent/child process communication.

---

## 500.37 — Shared memory

Shared memory là explicit resource.

---

## 500.38 — Shared memory ownership

Không được dùng ordinary Axiom ownership semantics để giả định exclusive process ownership khi memory shared.

---

## 500.39 — Shared memory synchronization

Synchronization explicit:

```text id="p5m8x1"
atomic
mutex
semaphore
futex/platform primitive
```

---

## 500.40 — Shared memory schema

Shared memory structures phải có stable representation/schema.

---

## 500.41 — Process address spaces

Raw pointer không được truyền trực tiếp giữa processes.

---

## 500.42 — Relative offsets

Shared-memory structures có thể dùng offsets.

---

## 500.43 — Offset validation

Offsets phải bounds-check.

---

## 500.44 — ABI version

Shared memory ABI phải versioned.

---

## 500.45 — Crash resilience

Consumer phải xử lý producer crash.

---

## 500.46 — Stale lock

Shared-memory synchronization phải có strategy cho crashed owner.

---

## 500.47 — Ring buffer

High-performance IPC có thể dùng shared-memory ring buffers.

---

## 500.48 — SPSC

SPSC ring buffer optimized case.

---

## 500.49 — MPMC

MPMC support nếu required; semantics explicit.

---

## 500.50 — Zero-copy IPC

Zero-copy có thể dùng shared memory.

---

## 500.51 — Lifetime

Zero-copy buffer lifetime phải explicit.

---

## 500.52 — Buffer ownership transfer

Ownership có thể chuyển qua IPC bằng protocol-level handles/capabilities, không phải raw address.

---

## 500.53 — OS handles

OS resources có thể transfer nếu platform hỗ trợ.

---

## 500.54 — Handle validity

Transferred handle có explicit ownership/lifetime.

---

## 500.55 — Process spawning

500 integrates 441 process API.

---

## 500.56 — Service startup

Service manager có thể launch service.

---

## 500.57 — Service lifecycle

States:

```text id="x8m2q4"
Starting
Ready
Stopping
Stopped
Failed
```

---

## 500.58 — Health

Health endpoint is optional application-level contract.

---

## 500.59 — Discovery

Service discovery có thể be:

- static;
- local registry;
- DNS;
- configuration;
- platform service manager.

---

## 500.60 — No mandatory service registry

Axiom core không yêu cầu central service discovery.

---

## 500.61 — Local RPC

IPC RPC can use 499 serialization.

---

## 500.62 — Network RPC

Network RPC uses 454 transport.

---

## 500.63 — Transport independence

Service contract không được gắn cứng vào TCP nếu không cần.

---

## 500.64 — Generated client

Schema/service definition có thể generate client.

---

## 500.65 — Generated server

Có thể generate server dispatch skeleton.

---

## 500.66 — Dispatch

Dispatch table maps operation ID → implementation.

---

## 500.67 — Static dispatch

Known service can use generated static dispatch.

---

## 500.68 — Dynamic dispatch

Runtime service registry có thể use dynamic dispatch explicit.

---

## 500.69 — ABI

In-process service interface có thể dùng native ABI.

---

## 500.70 — IPC ABI

IPC representation dùng serialized/shared-memory ABI.

---

## 500.71 — FFI service

Foreign services có thể expose C ABI wrappers.

---

## 500.72 — Version negotiation

Client/server negotiate supported interface versions.

---

## 500.73 — Compatibility

495 rules apply to service schema/API evolution.

---

## 500.74 — Method removal

Removed operation phải compatibility policy.

---

## 500.75 — Field evolution

499 schema evolution applies to request/response.

---

## 500.76 — Capability evolution

New capability requirements can break clients and must be classified.

---

## 500.77 — Security boundary

Every IPC/RPC endpoint is a trust boundary unless explicitly in same trusted domain.

---

## 500.78 — Input validation

Requests are untrusted until authenticated/validated.

---

## 500.79 — Resource limits

Server can limit:

- message size;
- concurrent calls;
- stream count;
- CPU;
- memory;
- queue depth.

---

## 500.80 — Rate limiting

Service can apply explicit rate limits.

---

## 500.81 — Queue limits

Bounded queues preferred where resource exhaustion matters.

---

## 500.82 — Admission control

Service can reject requests before allocation.

---

## 500.83 — Priority

Priority must be explicit and must not violate security isolation.

---

## 500.84 — Fairness

Scheduler policy is transport/service implementation detail unless contract specifies it.

---

## 500.85 — Ordering

Message ordering is transport-specific and must be documented.

---

## 500.86 — Reordering

RPC protocol may include sequence numbers where required.

---

## 500.87 — Correlation ID

Requests may carry stable correlation IDs.

---

## 500.88 — Tracing

475/481 trace context may propagate explicitly.

---

## 500.89 — Logging

Sensitive request payloads must not be logged automatically.

---

## 500.90 — Privacy

Service policy can classify fields as sensitive.

---

## 500.91 — Audit

Security-sensitive operations may generate explicit audit records.

---

## 500.92 — Transactions

RPC transaction semantics are not automatically database transactions.

---

## 500.93 — Distributed transaction

Distributed transactions are library-level and explicit.

---

## 500.94 — Actor integration

472 actors can expose message-based service endpoints.

---

## 500.95 — Reactive integration

473 streams/signals can be transported through explicit stream contracts.

---

## 500.96 — Async integration

RPC can expose `Future`/streaming APIs.

---

## 500.97 — AI metadata

AI can query:

```text id="k3m8x1"
service()
operations()
transport()
schema()
security()
capabilities()
retry_policy()
idempotency()
```

---

## 500.98 — Testing

Must test:

- malformed requests;
- disconnect;
- timeout;
- cancellation;
- duplicate request;
- reorder;
- backpressure;
- peer crash;
- schema evolution;
- authorization;
- resource exhaustion.

---

## 500.99 — Performance

Measure separately:

- serialization;
- transport;
- kernel transition;
- IPC latency;
- context switching;
- copy count;
- allocation;
- throughput;
- tail latency.

---

## 500.100 — Hard invariants

1. In-process call khác IPC.
2. IPC khác network RPC.
3. Communication domain được phân biệt.
4. RPC không giả lập local-call semantics một cách sai lệch.
5. Endpoint có identity.
6. Endpoint có transport.
7. Endpoint có security policy.
8. Service là logical provider.
9. Service interface có version.
10. Operations có stable ID.
11. Request có schema.
12. Response có schema.
13. Remote errors dùng Result.
14. Transport error khác application error.
15. Timeout không chứng minh operation failure.
16. Retry explicit.
17. Idempotency explicit.
18. Duplicate requests được xử lý theo policy.
19. Exactly-once không mặc định.
20. Cancellation explicit.
21. Deadline tích hợp 474.
22. Streaming có backpressure.
23. Unary streaming modes được phân biệt.
24. Message framing explicit.
25. Serialization dùng 499.
26. Compression explicit.
27. Encryption dùng security/transport layer.
28. Authentication khác authorization.
29. Capability-based RPC được hỗ trợ.
30. Capability attenuation được hỗ trợ.
31. Capability lifetime được hỗ trợ.
32. Process identity khác service identity.
33. Local IPC authorization được hỗ trợ.
34. Endpoint namespace được bảo vệ.
35. Unix sockets được hỗ trợ khi platform có.
36. Windows named pipes được hỗ trợ.
37. Anonymous pipes được hỗ trợ.
38. Shared memory là explicit resource.
39. Shared memory ownership được phân biệt.
40. Shared synchronization explicit.
41. Shared memory schema stable.
42. Raw process pointers không được truyền.
43. Relative offsets được hỗ trợ.
44. Shared-memory offsets được validate.
45. Shared ABI versioned.
46. Producer crash được xử lý.
47. Crashed lock owner có recovery strategy.
48. Ring buffer được hỗ trợ.
49. SPSC optimized path được hỗ trợ.
50. MPMC có semantics explicit.
51. Zero-copy IPC được hỗ trợ.
52. Zero-copy lifetime explicit.
53. Ownership transfer dùng protocol/handles.
54. OS handles có thể transfer.
55. Transferred handles có lifetime semantics.
56. Process API 441 được tích hợp.
57. Service startup được hỗ trợ.
58. Service lifecycle explicit.
59. Health contract optional.
60. Service discovery không bắt buộc.
61. Local RPC được hỗ trợ.
62. Network RPC được hỗ trợ.
63. Service contract transport-independent khi có thể.
64. Generated clients được hỗ trợ.
65. Generated servers được hỗ trợ.
66. Dispatch IDs stable.
67. Static dispatch được ưu tiên khi known.
68. Dynamic dispatch explicit.
69. In-process ABI khác IPC ABI.
70. FFI service wrappers được hỗ trợ.
71. Version negotiation được hỗ trợ.
72. 495 compatibility rules được áp dụng.
73. Removed operations có compatibility policy.
74. 499 schema evolution được áp dụng.
75. Capability evolution được classify.
76. IPC/RPC là trust boundary mặc định.
77. Requests được validate.
78. Message/resource limits được hỗ trợ.
79. Concurrent-call limits được hỗ trợ.
80. Stream limits được hỗ trợ.
81. CPU/memory limits được hỗ trợ.
82. Queue limits được hỗ trợ.
83. Rate limiting được hỗ trợ.
84. Admission control được hỗ trợ.
85. Priority explicit.
86. Security isolation không bị priority bypass.
87. Ordering semantics explicit.
88. Reordering handling được hỗ trợ khi cần.
89. Correlation IDs được hỗ trợ.
90. Distributed trace propagation explicit.
91. Sensitive payload không được auto-log.
92. Privacy metadata được hỗ trợ.
93. Audit records explicit.
94. RPC transactions khác DB transactions.
95. Distributed transactions không phải core.
96. Actor integration được hỗ trợ.
97. Reactive streaming integration được hỗ trợ.
98. Async integration được hỗ trợ.
99. AI service/contract/security queries được hỗ trợ.
100. **Axiom IPC/RPC phải cung cấp một contract thống nhất ở tầng service/data nhưng giữ nguyên sự khác biệt thực tế giữa local, process và network communication: failure, ownership, latency, ordering, retry, security, resource limits và delivery semantics đều phải explicit, không có "distributed system magic" ẩn bên trong compiler/runtime.**

**BOOTSTRAP-500 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ MỚI

```text
BOOTSTRAP-491  Package Registry / CAS / Offline Vendor             LOCKED
BOOTSTRAP-492  Dependency Resolution / Workspace                   LOCKED
BOOTSTRAP-493  Binary Interface / Precompiled Generics             LOCKED
BOOTSTRAP-494  Distributed Build / Remote Cache                    LOCKED
BOOTSTRAP-495  Compatibility / Migration                           LOCKED
BOOTSTRAP-496  Compiler Extension / Generator                      LOCKED
BOOTSTRAP-497  Build Scripts / Resource Build Plugins              LOCKED
BOOTSTRAP-498  Resource / Asset Build Pipeline                     LOCKED
BOOTSTRAP-499  Application Data / Serialization / Schema           LOCKED
BOOTSTRAP-500  IPC / RPC / Service / Shared Memory                  LOCKED
```

**Task kế tiếp: `BOOTSTRAP-501 — DISTRIBUTED SYSTEM FOUNDATION, SERVICE DISCOVERY, CONSISTENCY, CLOCKS, MEMBERSHIP, FAILURE DETECTION & FAULT-TOLERANT PRIMITIVES`.**