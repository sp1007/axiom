# BOOTSTRAP-598 — NATIVE APPLICATION IPC & INTER-PROCESS DATA MODEL 6.0

## LOCAL IPC, NAMED CHANNELS, SOCKETS, SHARED MEMORY, HANDLE TRANSFER, RPC, MESSAGE SERIALIZATION, SERVICE DISCOVERY, SECURITY CAPABILITIES, PROCESS SUPERVISOR INTEGRATION & ZERO-COPY INTER-PROCESS COMMUNICATION

**Trạng thái: COMPLETED / LOCKED**

`598` định nghĩa lớp IPC ở cấp application, nằm trên các primitive thấp hơn của `454`, `472`, `490`, `594`, nhưng **không thay thế** socket, pipe, shared memory hoặc OS handle API.

Mục tiêu:

```text
                    Axiom Application IPC
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Message           Stream           Shared
        IPC               IPC             Memory
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Endpoint / Channel
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
             RPC         Events       Bulk Data
              │            │            │
              └────────────┼────────────┘
                           ▼
                   Capability Security
                           │
                           ▼
                 Native OS / Virtual IPC
```

---

# 598.1. IPC design principles

Axiom IPC phải:

1. native;
2. zero-copy khi có thể;
3. explicit về ownership;
4. capability-based;
5. cross-platform;
6. không yêu cầu serialization nếu hai process có shared ABI;
7. hỗ trợ serialization khi process không chia sẻ ABI;
8. hỗ trợ synchronous và asynchronous usage;
9. không bắt buộc RPC framework;
10. không phụ thuộc một IPC daemon trung tâm.

---

# 598.2. IPC layers

```text
Application Protocol
        ↓
RPC / Event / Stream
        ↓
Message Channel
        ↓
Transport
        ↓
Native IPC Adapter
        ↓
Operating System
```

---

# 598.3. Transport abstraction

Transport là lớp vận chuyển byte/message.

Các transport chuẩn:

```text
Pipe
UnixDomainSocket
NamedPipe
LocalSocket
TCP
UDP
SharedMemory
PlatformChannel
```

---

# 598.4. Message abstraction

```text
Message {
    type_id
    flags
    payload
    metadata
}
```

Message không bắt buộc phải serialize thành một buffer mới.

---

# 598.5. Message identity

Mỗi message có thể có:

```text
MessageID
CorrelationID
RequestID
SequenceNumber
```

---

# 598.6. Correlation ID

RPC request/response sử dụng `CorrelationID` để liên kết response với request.

---

# 598.7. Sequence number

Ordered channels có sequence number.

---

# 598.8. Ordering

Transport phải công bố:

```text
Ordered
Unordered
PartiallyOrdered
```

Không được giả định mọi IPC đều ordered.

---

# 598.9. Reliability

Channel có thể có:

```text Reliable
BestEffort
LossDetectable
```

---

# 598.10. Message size

Transport phải expose maximum message size nếu có giới hạn.

---

# 598.11. Fragmentation

Message lớn có thể được transport fragmentation.

Application không cần tự fragment nếu transport contract hỗ trợ.

---

# 598.12. Stream vs message

Axiom phân biệt:

```text
ByteStream
MessageStream
Datagram
SharedRegion
```

---

# 598.13. Byte stream

Byte stream không giữ message boundaries.

---

# 598.14. Message stream

Message stream giữ boundaries.

---

# 598.15. Datagram

Datagram giữ packet/message boundary nhưng có thể mất.

---

# 598.16. Shared region

Shared region cung cấp memory trực tiếp giữa process.

---

# 598.17. Endpoint

```text
Endpoint
```

là logical IPC address.

---

# 598.18. Endpoint identity

Endpoint identity có thể gồm:

```text
scheme
namespace
name
instance
security descriptor
```

---

# 598.19. Logical endpoint URI

Axiom có thể sử dụng:

```text
axipc://local/service
axipc://local/app/{id}
```

URI chỉ là logical address.

---

# 598.20. Endpoint discovery

Endpoint có thể được:

```text
well-known
dynamically registered
passed explicitly
inherited
```

---

# 598.21. No global registry requirement

IPC không phụ thuộc registry daemon.

---

# 598.22. Local endpoint

Local IPC endpoint chỉ tồn tại trong host.

---

# 598.23. Remote endpoint

Remote endpoint có thể map sang network transport `454`.

---

# 598.24. Endpoint type

```text
EndpointKind {
    Local
    Remote
    InProcess
}
```

---

# 598.25. In-process endpoint

In-process channel có thể bypass kernel IPC và dùng direct queue khi an toàn.

---

# 598.26. In-process optimization

API semantics phải tương thích với out-of-process channel ở mức abstraction.

---

# 598.27. Pipe

Pipe thích hợp cho:

```text
parent → child
child → parent
pipeline
```

---

# 598.28. Named pipe

Named pipe hỗ trợ service discovery trên Windows và tương đương platform adapter.

---

# 598.29. Unix domain socket

Unix domain socket được dùng cho local socket semantics trên Unix-like systems.

---

# 598.30. Local socket

Portable API:

```text
LocalSocket
```

không expose Unix-specific assumptions.

---

# 598.31. Socket address

Socket endpoint có:

```text
LocalPath
AbstractName?
NetworkAddress
```

tùy backend.

---

# 598.32. Parent-child IPC

Supervisor `594` có thể tạo channel trước khi spawn child.

```text
Supervisor
   │
   ├── spawn
   │
   └── channel handle
             ↓
          Child
```

---

# 598.33. Handle inheritance

Handle inheritance phải explicit.

---

# 598.34. No accidental inheritance

Process spawn không tự động inherit mọi IPC handle.

---

# 598.35. Handle transfer

Process A có thể transfer IPC capability cho process B nếu platform hỗ trợ.

---

# 598.36. Capability transfer

```text
Capability A
     │
     ▼
Transfer
     │
     ▼
Capability B
```

Capability không phải raw integer handle.

---

# 598.37. Handle type

Các handle có thể transfer:

```text
File
Socket
Pipe
SharedMemory
Event
Semaphore
Process
```

theo platform capability.

---

# 598.38. Transfer metadata

Handle transfer có metadata:

```text type
rights
owner
transfer_id
```

---

# 598.39. Rights attenuation

Capability khi transfer có thể giảm quyền:

```text ReadWrite
    ↓
Read
```

---

# 598.40. No privilege amplification

Process B không thể nhận capability có quyền cao hơn capability A đã sở hữu.

---

# 598.41. Channel

```text
Channel<T>
```

là abstraction message-oriented.

---

# 598.42. Typed channel

`Channel<T>` đảm bảo message payload thuộc type `T` ở compile time nếu cả hai endpoints cùng ABI/type schema.

---

# 598.43. Untyped channel

```text
RawChannel
```

cho byte/message protocol động.

---

# 598.44. Channel direction

```text
Sender<T>
Receiver<T>
Duplex<T>
```

---

# 598.45. Ownership

Sender và receiver có ownership riêng.

---

# 598.46. Close semantics

Khi sender cuối cùng đóng:

```text
Receiver → EndOfStream
```

---

# 598.47. Receiver close

Receiver đóng khiến sender nhận:

```text
BrokenChannel
```

nếu transport hỗ trợ detection.

---

# 598.48. Backpressure

Channel phải hỗ trợ:

```text
Bounded
Unbounded
Backpressured
Dropping
```

---

# 598.49. Bounded channel

Bounded channel giới hạn số message/bytes đang pending.

---

# 598.50. Send behavior

Khi đầy:

```text
Block
Await
Reject
Drop
```

phải explicit.

---

# 598.51. No hidden unbounded queue

IPC runtime không được tự động tạo unbounded queue cho high-volume channel.

---

# 598.52. Priority

Message channel có thể hỗ trợ priority.

Priority không được phá protocol ordering nếu channel contract yêu cầu strict order.

---

# 598.53. Cancellation

Send/receive có cancellation token tích hợp `424`.

---

# 598.54. Deadline

IPC operation có deadline:

```text
send(msg, deadline)
receive(deadline)
```

---

# 598.55. Timeout

Timeout không đồng nghĩa channel failure.

---

# 598.56. Retry

RPC layer có thể retry request nếu protocol đánh dấu operation idempotent.

---

# 598.57. No unsafe automatic retry

Non-idempotent RPC không được retry tự động.

---

# 598.58. Message schema

Cross-process typed message cần schema identity:

```text
SchemaID
TypeID
Version
```

---

# 598.59. Schema versioning

Schema evolution phải hỗ trợ:

```text
BackwardCompatible
ForwardCompatible
Breaking
```

---

# 598.60. ABI compatibility

Native zero-copy messages yêu cầu ABI compatibility.

---

# 598.61. Zero-copy prerequisite

Zero-copy chỉ được sử dụng khi:

```text
same ABI
compatible layout
compatible endianness
compatible pointer model
shared lifetime contract
```

---

# 598.62. Pointer prohibition in wire message

Raw process-local pointer không được serialize qua IPC.

---

# 598.63. Relative references

Shared-memory data có thể dùng offsets thay vì absolute pointers.

```text
offset = address - region_base
```

---

# 598.64. Shared-memory pointer model

Axiom cung cấp abstraction:

```text
SharedOffset<T>
```

thay vì raw pointer.

---

# 598.65. Shared memory

```text
SharedMemoryRegion
```

là vùng memory được map vào nhiều processes.

---

# 598.66. Region identity

```text
SharedRegionID
```

xác định logical region.

---

# 598.67. Region size

Size phải cố định hoặc explicit resize protocol.

---

# 598.68. Mapping

Process A:

```text
region.map()
```

Process B:

```text
region.attach()
```

---

# 598.69. Address independence

Không process nào được giả định shared region có cùng virtual address.

---

# 598.70. Offset-based data

Shared data phải sử dụng:

```text
offset
length
```

thay vì process-local address.

---

# 598.71. Shared struct ABI

Struct shared memory phải có stable layout.

---

# 598.72. Version header

Shared memory region nên bắt đầu bằng:

```text
SharedHeader {
    magic
    version
    schema_id
    total_size
}
```

---

# 598.73. Alignment

Shared structures phải respect ABI alignment.

---

# 598.74. Endianness

Cross-machine shared memory không phải mục tiêu; nếu shared storage được dùng cross-endian thì schema phải specify byte order.

---

# 598.75. Atomic shared memory

Atomic types có thể được đặt trong shared region nếu platform memory model hỗ trợ process-shared atomicity.

---

# 598.76. Memory ordering

Shared-memory synchronization sử dụng Axiom atomic memory ordering `424`.

---

# 598.77. Lock-free shared memory

Lock-free algorithms được phép nhưng phải dùng explicit atomics.

---

# 598.78. Shared mutex

Platform/runtime có thể cung cấp process-shared mutex.

---

# 598.79. Ring buffer

Standard library cung cấp optional:

```text
SharedRingBuffer<T>
```

---

# 598.80. Ring buffer layout

```text
SharedMemory
 ├── Header
 ├── ProducerIndex
 ├── ConsumerIndex
 └── Elements[]
```

---

# 598.81. Single producer

SP/SC ring buffer có optimized implementation.

---

# 598.82. Multi producer

MPMC ring buffer có synchronization mạnh hơn và không được giả định lock-free trên mọi target.

---

# 598.83. Bulk transfer

Large data nên dùng:

```text
control message
      +
shared memory descriptor
```

thay vì copy payload.

---

# 598.84. Descriptor

```text
SharedBufferDescriptor {
    region_id
    offset
    length
    permissions
    generation
}
```

---

# 598.85. Buffer ownership

Descriptor không tự động trao ownership của memory.

---

# 598.86. Buffer lease

Bulk transfer có thể dùng:

```text
BufferLease
```

để xác định thời gian receiver được phép đọc/ghi.

---

# 598.87. Lease lifecycle

```text
Created
  ↓
Transferred
  ↓
InUse
  ↓
Returned
  ↓
Released
```

---

# 598.88. Generation

Shared memory descriptor có generation để phát hiện stale handles.

---

# 598.89. Stale descriptor

Descriptor generation mismatch → `StaleHandle`.

---

# 598.90. Memory reclamation

Producer không được reclaim region trước khi receiver release lease.

---

# 598.91. Reference counting

Shared buffers có thể dùng explicit reference count.

---

# 598.92. No hidden GC

IPC buffers không được phụ thuộc garbage collector.

---

# 598.93. Shared allocator

Optional allocator:

```text
SharedAllocator
```

cho object allocation trong shared memory.

---

# 598.94. Shared allocator safety

Allocator metadata phải là process-safe.

---

# 598.95. Shared object restriction

Objects chứa process-local pointers không được đặt vào portable shared memory.

---

# 598.96. Shared strings

Shared strings dùng:

```text
offset
length
encoding
```

---

# 598.97. Shared arrays

Shared arrays:

```text
offset
length
stride
element_schema
```

---

# 598.98. Shared maps

Shared hash map chỉ được cung cấp nếu layout/locking contract rõ ràng.

---

# 598.99. Shared memory security

Một process chỉ được attach region khi sở hữu capability tương ứng.

---

# 598.100. Region permissions

```text
Read
Write
Execute
```

`Execute` phải bị cấm mặc định.

---

# 598.101. W^X

Shared memory không được đồng thời writable và executable trong portable security mode.

---

# 598.102. Executable shared memory

JIT/shared executable memory là separate capability và thuộc compiler/runtime security model.

---

# 598.103. Message serialization

Axiom hỗ trợ canonical serialization cho IPC.

---

# 598.104. Serialization formats

Standard library có thể cung cấp:

```text
AXON Binary
AXON JSON-like Text
CBOR-like compact format
```

nhưng core IPC không phụ thuộc một serialization format cụ thể.

---

# 598.105. Canonical binary

Canonical binary serialization phải deterministic.

---

# 598.106. Schema-driven encoding

Typed serializer sử dụng compiler-generated schema metadata.

---

# 598.107. Reflection integration

`446` semantic metadata có thể generate serialization descriptors.

---

# 598.108. Serialization zero-copy

Decoder có thể expose borrowed views nếu underlying buffer lifetime đủ dài.

---

# 598.109. Borrowed message view

```text
MessageView<'buffer, T>
```

là conceptual lifetime contract, nhưng implementation không bắt buộc Rust-style lifetime syntax.

---

# 598.110. Runtime validation

Untrusted serialized data phải validate bounds trước khi materialization.

---

# 598.111. Length validation

Không được trust length fields từ remote process.

---

# 598.112. Integer overflow

Decoder phải kiểm tra arithmetic overflow trước allocation/copy.

---

# 598.113. Recursion limits

Nested serialization phải có configurable depth limit.

---

# 598.114. Allocation limits

Decoder phải hỗ trợ maximum allocation budget.

---

# 598.115. Message size limit

Endpoint có thể đặt max inbound message size.

---

# 598.116. Compression

IPC có thể compress large serialized messages.

Không compress shared-memory payload.

---

# 598.117. Compression bomb protection

Decoder phải kiểm tra decompressed-size budget.

---

# 598.118. RPC

RPC abstraction:

```text
Service<TRequest, TResponse>
```

---

# 598.119. RPC call

```text
response = service.call(request)
```

có thể compile thành direct channel operation.

---

# 598.120. RPC metadata

Request:

```text
method_id
request_id
deadline
auth_context
payload
```

---

# 598.121. RPC response

Response:

```text
request_id
status
payload?
error?
```

---

# 598.122. RPC errors

```text
TransportError
Timeout
Cancelled
Rejected
Unauthorized
ProtocolError
RemoteError
```

---

# 598.123. Remote error identity

Remote error có:

```text
error_type_id
message
metadata
```

---

# 598.124. Error boundary

Remote error không tự động trở thành local exception/panic.

---

# 598.125. Result integration

RPC API mặc định trả:

```text
Result<T, RpcError>
```

---

# 598.126. Panic boundary

Remote process panic không làm local process panic.

---

# 598.127. Service definition

Service có schema:

```text
service Calculator {
    fn add(AddRequest) -> AddResponse
}
```

---

# 598.128. Code generation

Compiler/tooling có thể generate client/server stubs.

---

# 598.129. Stub architecture

```text
Application
    ↓
Generated Client
    ↓
RPC Runtime
    ↓
Transport
    ↓
RPC Runtime
    ↓
Generated Server
    ↓
Implementation
```

---

# 598.130. Stub zero-copy

Nếu target hỗ trợ compatible ABI, generated stubs có thể bypass serialization.

---

# 598.131. Local optimization

Compiler có thể lower local RPC:

```text serialize
→ copy
```

thành:

```text typed call
→ shared buffer
```

khi semantics cho phép.

---

# 598.132. No semantic cheating

Optimization không được thay đổi observable IPC semantics.

---

# 598.133. Service version

Service identity:

```text ServiceID
InterfaceID
Version
```

---

# 598.134. Interface compatibility

New service versions có thể coexist.

---

# 598.135. Method identity

Method ID không phụ thuộc source declaration order.

---

# 598.136. Stable method IDs

Compiler nên derive method identity từ explicit schema identity.

---

# 598.137. Explicit IDs

Protocol designer có thể khai báo:

```text
@id(0x1001)
```

---

# 598.138. Event bus

Axiom cung cấp optional:

```text
EventBus<T>
```

cho pub/sub.

---

# 598.139. Event semantics

Event có thể:

```text
Broadcast
Multicast
PointToPoint
```

---

# 598.140. Event ordering

Ordering guarantee phải explicit.

---

# 598.141. Durable events

Durable event queues thuộc storage/distributed systems layer, không phải default IPC.

---

# 598.142. Local event bus

Local event bus có thể optimize bằng shared queue/in-process dispatch.

---

# 598.143. Service discovery

Service discovery API:

```text
register()
resolve()
watch()
unregister()
```

---

# 598.144. Service registration

Registration record:

```text
ServiceRecord {
    service_id
    instance_id
    endpoint
    version
    capabilities
    metadata
}
```

---

# 598.145. Local discovery

Local services có thể dùng OS namespace hoặc application supervisor `594`.

---

# 598.146. Supervisor discovery

Supervisor có thể publish child service endpoints.

---

# 598.147. Remote discovery

Remote service discovery thuộc `501` distributed system foundation.

---

# 598.148. No mandatory central registry

Axiom application IPC không yêu cầu một global service registry.

---

# 598.149. Endpoint lifetime

Endpoint tồn tại theo owner process/service lifecycle.

---

# 598.150. Service crash

Nếu service chết:

```text
Endpoint → Unavailable
```

---

# 598.151. Restart

Supervisor có thể restart service.

Client phải xử lý endpoint generation change.

---

# 598.152. Endpoint generation

```text
EndpointIdentity {
    service_id
    instance_id
    generation
}
```

---

# 598.153. Stale endpoint

Request đến instance cũ phải fail rõ ràng.

---

# 598.154. Authentication

Local IPC có thể authenticate peer identity từ OS.

---

# 598.155. Peer identity

```text
PeerIdentity {
    process_id?
    user_id?
    application_id?
    sandbox_id?
    signing_identity?
}
```

Các field có thể unavailable.

---

# 598.156. Authorization

Authentication và authorization phải tách biệt.

---

# 598.157. Capability authorization

Service policy có thể:

```text allow capability
deny capability
allow read-only
allow specific method
```

---

# 598.158. Per-method authorization

RPC service có thể authorize từng method.

---

# 598.159. Endpoint ACL

Endpoint có thể có ACL native/platform mapping.

---

# 598.160. Security policy

Security policy:

```text Deny
Allow
AllowRead
AllowWrite
AllowInvoke
```

---

# 598.161. Default deny

New privileged IPC endpoints phải default deny trong secure application profiles.

---

# 598.162. Capability delegation

Service có thể delegate restricted capability.

---

# 598.163. No ambient authority

Process không được tự động có quyền gọi mọi local service.

---

# 598.164. Sandboxed IPC

Sandbox policy có thể giới hạn:

```text outbound endpoints
inbound endpoints
shared memory
handle transfer
```

---

# 598.165. IPC manifest

`593` application manifest có thể khai báo:

```text
ipc.services
ipc.clients
ipc.capabilities
```

---

# 598.166. IPC capability declaration

Application có thể request:

```text
connect service X
listen endpoint Y
create shared memory
transfer handles
```

---

# 598.167. User consent

Platform có thể yêu cầu user consent cho cross-application IPC.

---

# 598.168. Same-application IPC

Các process cùng application identity có thể có policy nhẹ hơn nhưng vẫn explicit capability.

---

# 598.169. Cross-application IPC

Cross-application IPC cần peer identity validation.

---

# 598.170. Cross-user IPC

Cross-user IPC bị deny mặc định trừ khi platform/security policy cho phép.

---

# 598.171. Remote IPC

Remote IPC phải chịu network security `454` và không được coi local IPC như trusted network.

---

# 598.172. Encryption

Remote transport có thể dùng TLS.

---

# 598.173. Local encryption

Local IPC thường không cần encryption nếu OS channel bảo vệ; application có thể yêu cầu encryption nếu threat model cần.

---

# 598.174. Secret leakage

IPC diagnostics không được log payload nhạy cảm mặc định.

---

# 598.175. Audit

Security-sensitive IPC operations có thể tạo audit events.

---

# 598.176. Rate limiting

Service có thể giới hạn:

```text requests/sec
bytes/sec
concurrent calls
```

---

# 598.177. Resource exhaustion

Server phải có inbound limits.

---

# 598.178. Queue quotas

Mỗi endpoint có thể có:

```text max messages
max bytes
max shared regions
max handles
```

---

# 598.179. DoS resistance

Untrusted client không được phép tạo unlimited IPC state.

---

# 598.180. Shared memory quotas

Shared memory allocation phải chịu capability/quota policy.

---

# 598.181. Handle quotas

Handle transfer phải có limits.

---

# 598.182. Server lifecycle

Service state machine:

```text
Created
   ↓
Starting
   ↓
Ready
   ↓
Serving
   ├──────→ Draining
   │          ↓
   │        Stopped
   ↓
Failed
   ↓
Restarting
```

---

# 598.183. Graceful shutdown

Service shutdown:

```text
Stop accepting
     ↓
Drain requests
     ↓
Release resources
     ↓
Close endpoints
```

---

# 598.184. Shutdown deadline

Supervisor có thể enforce deadline.

---

# 598.185. Forced termination

Deadline exceeded → supervisor có thể terminate process.

---

# 598.186. In-flight RPC

Forced termination làm in-flight calls fail.

---

# 598.187. Request cancellation propagation

RPC cancellation có thể propagate client → server.

---

# 598.188. Server cancellation

Server phải kiểm tra cancellation tại cancellation points.

---

# 598.189. Idempotent restart

Service initialization nên tránh duplicate side effects khi supervisor retry.

---

# 598.190. Health endpoint

Service có thể expose:

```text health()
ready()
live()
```

---

# 598.191. Health semantics

```text
Starting
Ready
Degraded
Draining
Failed
```

---

# 598.192. IPC observability

`475/481` có thể record:

```text latency
throughput
queue depth
message size
RPC errors
disconnects
```

---

# 598.193. Tracing

RPC spans có:

```text trace_id
span_id
correlation_id
service_id
method_id
```

---

# 598.194. Performance counters

IPC runtime có thể expose:

```text copied_bytes
zero_copy_bytes
serialized_bytes
shared_memory_bytes
```

---

# 598.195. Zero-copy ratio

Profiler có thể report percentage traffic bypassing copies.

---

# 598.196. Debugger integration

`589` có thể inspect:

```text endpoints
channels
pending RPC
shared regions
peer identity
```

---

# 598.197. Debugger safety

Debugger không được mutate shared IPC state mặc định.

---

# 598.198. Crash dump

Crash dump có thể include:

```text endpoint IDs
peer IDs
in-flight request IDs
channel states
```

nhưng không include arbitrary payloads mặc định.

---

# 598.199. IDE integration

`590` có thể hiển thị:

```text Process
   ↓
IPC
   ├── endpoint
   ├── channel
   ├── service
   └── shared memory
```

---

# 598.200. AI semantic integration

AI tooling có thể query IPC topology:

```text
Process A
   │
   ├── calls Service B
   └── shares Region R
```

---

# 598.201. AI protocol reasoning

AI tooling có thể inspect:

```text schema
version
method
authorization
transport
```

---

# 598.202. AI safety

AI agent không được tự ý:

```text expose service publicly
grant IPC capability
disable authorization
transfer privileged handle
```

---

# 598.203. Compiler metadata

Compiler có thể emit IPC schema metadata:

```text
IPCInterface {
    interface_id
    version
    methods
    types
    compatibility
}
```

---

# 598.204. Binary metadata

IPC metadata có thể được lưu trong `565` AXIOM artifacts.

---

# 598.205. ABI fingerprint

Native zero-copy interfaces phải có ABI fingerprint.

---

# 598.206. ABI mismatch

Mismatch:

```text
Expected ABI X
Received ABI Y
```

→ reject zero-copy path.

---

# 598.207. Serialization fallback

Nếu protocol cho phép:

```text zero-copy
   ↓ incompatible
serialized transport
```

---

# 598.208. Explicit fallback

Fallback phải là protocol policy, không tự ý thay đổi semantics.

---

# 598.209. Cross-version compatibility

Client mới có thể giao tiếp server cũ nếu schema compatibility checker xác nhận.

---

# 598.210. Compatibility checker

Compiler/tooling có thể kiểm tra:

```text removed method
changed type
changed field
changed enum
changed semantics
```

---

# 598.211. Optional fields

Schema có thể hỗ trợ optional fields để evolve protocol.

---

# 598.212. Unknown fields

Forward-compatible decoder có thể preserve/ignore unknown fields theo schema policy.

---

# 598.213. Enum evolution

Enum decoder phải có explicit unknown-case policy.

---

# 598.214. Version negotiation

Handshake có thể negotiate:

```text protocol version
features
serialization
compression
zero-copy capability
```

---

# 598.215. Handshake

```textClient → Hello
Server → HelloAck
Client → CapabilitySet
Server → NegotiatedProtocol
```

---

# 598.216. No mandatory handshake

Known same-version local channels có thể skip handshake.

---

# 598.217. Connection state

```text
Created
Connecting
Negotiating
Connected
Draining
Closed
Failed
```

---

# 598.218. Reconnection

Long-lived client có thể reconnect.

---

# 598.219. Reconnection identity

Reconnect phải phân biệt:

```text same service
new instance
```

---

# 598.220. Session identity

```text SessionID
```

được dùng để tránh replaying stale session state.

---

# 598.221. Replay protection

Security-sensitive RPC có thể yêu cầu request nonce/sequence.

---

# 598.222. Duplicate requests

Server có thể deduplicate bằng `RequestID` cho idempotent operations.

---

# 598.223. Exactly-once semantics

Axiom IPC không claim universal exactly-once delivery.

---

# 598.224. At-most-once

Transport có thể cung cấp at-most-once semantics.

---

# 598.225. At-least-once

Retryable protocols có thể implement at-least-once.

---

# 598.226. Exactly-once application semantics

Nếu cần, application phải implement idempotency/deduplication.

---

# 598.227. Shared-memory RPC

RPC có thể use:

```text control channel
+
shared request buffer
+
shared response buffer
```

---

# 598.228. Large-message optimization

Compiler/runtime nên tự động chọn shared buffer cho messages vượt threshold nếu protocol cho phép.

---

# 598.229. Small-message optimization

Small messages nên tránh shared-memory setup overhead.

---

# 598.230. Adaptive transport

Transport selector có thể dùng:

```text message size
latency
copy cost
queue depth
```

---

# 598.231. Deterministic selection

Build/replay mode có thể disable adaptive heuristics để reproducibility.

---

# 598.232. IPC allocator

Message allocation nên hỗ trợ per-channel pools.

---

# 598.233. Allocation elimination

Compiler có thể scalarize/stack-allocate small messages khi lifetime cho phép.

---

# 598.234. Copy elimination

Compiler có thể eliminate intermediate copies khi ownership semantics chứng minh an toàn.

---

# 598.235. Ownership transfer

Message có thể transfer ownership:

```text Sender
   │ move
   ▼
Receiver
```

---

# 598.236. Borrowed message

Receiver có thể chỉ borrow payload trong thời gian callback/receive scope.

---

# 598.237. Retain

Receiver muốn giữ payload phải explicitly retain/copy/lease.

---

# 598.238. No implicit deep copy

Typed IPC không mặc định deep-copy mọi object nếu zero-copy representation có thể dùng.

---

# 598.239. Pointer-containing types

Types chứa process-local pointers không được trực tiếp cross-process.

---

# 598.240. Compiler rejection

Compiler phải reject:

```text
IPC.send(raw_pointer_struct)
```

nếu protocol yêu cầu portable representation.

---

# 598.241. Unsafe escape hatch

Unsafe native ABI IPC có thể bypass restriction, nhưng phải explicit `unsafe`.

---

# 598.242. Unsafe IPC contract

Unsafe IPC programmer chịu trách nhiệm:

```text layout
alignment
lifetime
pointer validity
synchronization
```

---

# 598.243. Native ABI IPC

Two Axiom processes built against compatible compiler/ABI có thể share native structs.

---

# 598.244. Compiler version

ABI fingerprint phải include compiler ABI version nếu layout semantics có thể thay đổi.

---

# 598.245. Stable ABI

Public IPC interfaces nên dùng explicitly versioned stable ABI.

---

# 598.246. Unstable internal ABI

Same-application internal IPC có thể dùng unstable compiler ABI khi build graph đảm bảo compatibility.

---

# 598.247. Build graph integration

`487/568` có thể detect ABI dependencies giữa IPC participants.

---

# 598.248. Rebuild propagation

Nếu shared IPC schema thay đổi:

```text schema
 ↓
generated code
 ↓
clients
 ↓
servers
```

phải được invalidated.

---

# 598.249. Package integration

`591` package metadata có thể publish IPC interfaces and schema versions.

---

# 598.250. Application packaging

`593` manifest có thể declare IPC endpoints exposed by application.

---

# 598.251. Runtime supervisor

`594` supervisor chịu trách nhiệm:

```text spawn
endpoint setup
capability delegation
health
restart
shutdown
```

---

# 598.252. Storage integration

`597` có thể lưu:

```text service registration state
IPC logs
persistent queues
```

nhưng IPC runtime không phụ thuộc persistent storage.

---

# 598.253. Network integration

`454` cung cấp:

```text socket
TLS
serialization
network transport
```

`598` chỉ compose các primitive đó thành application IPC.

---

# 598.254. Actor integration

`472` actor mailbox có thể được backed bởi local IPC channel.

---

# 598.255. Actor isolation

Actor process có thể communicate bằng typed IPC mà không expose shared mutable state.

---

# 598.256. Dataflow integration

`473` stream/dataflow graph có thể cross process bằng IPC channels.

---

# 598.257. Task integration

`471` task scheduler quản lý asynchronous send/receive.

---

# 598.258. Time integration

`474` cung cấp:

```text timeout
deadline
lease expiration
heartbeat
```

---

# 598.259. Security integration

`490` cung cấp:

```text capability
sandbox
identity
policy
```

---

# 598.260. Error integration

`425`:

```text Result
Option
panic
```

được dùng ở IPC API.

---

# 598.261. Resource lifetime

`423` quản lý:

```text channel
endpoint
shared region
buffer lease
handle
```

lifetime.

---

# 598.262. IPC object model

Core interfaces:

```text
Endpoint
Connection
Channel<T>
Sender<T>
Receiver<T>
Message
SharedMemoryRegion
SharedBuffer
BufferLease
Service
RpcClient
RpcServer
ServiceRegistry
```

---

# 598.263. Example — simple channel

```axiom
let channel = ipc.channel<i32>(capacity: 128)

spawn {
    channel.send(42)
}

let value = channel.receive()?
```

---

# 598.264. Example — service

```axiom
service Calculator {
    fn add(a: i64, b: i64) -> Result<i64, RpcError>
}
```

Compiler/tooling generates:

```text
CalculatorClient
CalculatorServer
CalculatorSchema
```

---

# 598.265. Example — shared buffer

```axiom
let region = ipc.shared_memory.create(64 * MB)

let buffer = region.allocate<u8>(size)

channel.send(buffer.descriptor())
```

Receiver:

```axiom
let descriptor = channel.receive()?
let buffer = ipc.attach(descriptor)?
```

---

# 598.266. Example — zero-copy image pipeline

```text
Camera Process
      │
      │ SharedBufferDescriptor
      ▼
Image Processor
      │
      │ SharedBufferDescriptor
      ▼
Encoder
```

Không copy toàn bộ frame qua từng process.

---

# 598.267. Example — process supervisor

```text
Supervisor
   │
   ├── spawn Worker A
   │       └── IPC endpoint
   │
   └── spawn Worker B
           └── IPC endpoint
```

Supervisor giữ capability của các endpoints.

---

# 598.268. Example — restricted worker

```text
Worker
 ├── read input channel
 ├── write output channel
 └── no filesystem capability
```

Đây là pattern quan trọng cho sandbox/plugin architecture.

---

# 598.269. Plugin integration

Plugin process có thể chỉ nhận:

```text IPC capability
SharedMemory capability
Resource capability
```

thay vì full application access.

---

# 598.270. Plugin crash isolation

Plugin crash không được crash host process nếu chạy out-of-process.

---

# 598.271. Plugin restart

Supervisor có thể restart plugin và establish new endpoint generation.

---

# 598.272. Plugin protocol compatibility

Plugin ABI/schema phải được verify trước activation.

---

# 598.273. IPC fuzzing

IPC decoder, handshake và schema compatibility phải được fuzz.

---

# 598.274. Malformed message

Malformed input phải:

```text reject
close optional
record diagnostic
```

không được memory corruption.

---

# 598.275. Parser isolation

Network/IPC decoder không được chạy với compiler parser.

---

# 598.276. Resource limits

IPC parser phải có:

```text max_depth
max_message
max_alloc
max_handles
max_regions
```

---

# 598.277. Differential protocol tests

Generated serializer/deserializer phải được test round-trip.

---

# 598.278. ABI tests

Shared-memory structures phải có compile-time layout assertions.

---

# 598.279. Cross-version tests

CI phải test:

```text client N ↔ server N
client N+1 ↔ server N
client N ↔ server N+1
```

nếu compatibility policy cho phép.

---

# 598.280. Cross-target tests

IPC conformance phải test:

```text Windows
Linux
macOS
Android
iOS
WASM
```

theo capabilities từng target.

---

# 598.281. Performance benchmark

Benchmark tối thiểu:

```text latency
throughput
small message
large message
serialized message
zero-copy
shared memory
RPC
```

---

# 598.282. Copy budget

Profiler phải có khả năng xác định số byte copy trong IPC pipeline.

---

# 598.283. Latency budget

Application có thể đặt IPC latency budget.

---

# 598.284. Backpressure benchmark

Benchmarks phải test sender faster than receiver.

---

# 598.285. Failure benchmark

Test:

```text peer crash
network disconnect
channel close
service restart
timeout
cancel
```

---

# 598.286. Crash consistency

Shared-memory ownership/reclamation phải được test khi owner process chết.

---

# 598.287. Owner death

Nếu owner chết, region/handle cleanup phụ thuộc OS semantics.

Runtime phải expose trạng thái thay vì giả định.

---

# 598.288. Orphan detection

IPC endpoints có thể phát:

```text PeerExited
```

---

# 598.289. Shared region orphan

Region có thể giữ tới khi last mapping closes.

---

# 598.290. Automatic cleanup

OS-backed IPC objects nên được cleanup khi last owner exits nếu platform hỗ trợ.

---

# 598.291. Named endpoint collision

Endpoint creation phải hỗ trợ:

```text FailIfExists
OpenExisting
ReplaceIfOwner
```

---

# 598.292. Service ownership

Named service phải có owner identity để tránh process khác hijack endpoint.

---

# 598.293. Endpoint hijacking prevention

Service registration phải bind endpoint identity với capability/owner.

---

# 598.294. TOCTOU service discovery

Resolve + connect phải xác minh peer identity sau connection.

---

# 598.295. Peer verification

Không trust service chỉ vì endpoint name đúng.

---

# 598.296. Local impersonation

OS-specific peer credentials phải được validate khi security policy yêu cầu.

---

# 598.297. IPC ACL

ACL có thể map:

```text ApplicationID
UserID
GroupID
SandboxID
SigningIdentity
```

---

# 598.298. Signing identity

Platform package signing identity `489/593` có thể tham gia IPC authorization.

---

# 598.299. No universal identity

Không phải target nào cũng có signing identity; missing capability phải biểu diễn rõ.

---

# 598.300. Security decision record

Authorization decision có thể emit diagnostic/audit:

```text
peer
service
method
decision
policy
```

---

# 598.301. Protocol logging

Logging phải tránh payload-sensitive data.

---

# 598.302. Deterministic simulation

IPC subsystem phải có virtual transport cho unit tests:

```text VirtualChannel
VirtualEndpoint
VirtualClock
VirtualPeer
```

---

# 598.303. Virtual transport

Cho phép test deadlock, timeout và cancellation deterministic.

---

# 598.304. Deadlock detection

Debug/test mode có thể detect dependency cycles:

```text
A waits B
B waits C
C waits A
```

---

# 598.305. Blocking policy

IPC APIs phải document blocking behavior.

---

# 598.306. Async-first internal implementation

Runtime có thể implement async primitives dưới synchronous API nhưng không được block arbitrary application threads indefinitely.

---

# 598.307. Thread affinity

IPC callbacks không được mặc định chạy trên UI thread.

---

# 598.308. UI integration

GUI `452` có thể marshal IPC events về UI event loop.

---

# 598.309. Callback lifetime

IPC callback phải obey ownership/lifetime `423`.

---

# 598.310. Reentrancy

RPC callbacks phải document reentrancy.

---

# 598.311. Nested calls

Nested RPC được phép nhưng phải chịu deadlock/backpressure rules.

---

# 598.312. Recursive service call

Service A → B → A phải không làm runtime deadlock mặc định; application protocol chịu trách nhiệm tránh cycle.

---

# 598.313. Priority inversion

Real-time IPC có thể hỗ trợ priority propagation nếu OS backend cho phép.

---

# 598.314. Real-time mode

Real-time applications có thể disable allocations/serialization trên hot path.

---

# 598.315. Audio IPC

`461` có thể sử dụng shared ring buffers cho real-time audio.

---

# 598.316. Video IPC

`460/462` có thể sử dụng shared buffers cho frames.

---

# 598.317. GPU IPC

GPU resource handles có thể được transferred qua platform-specific capability.

---

# 598.318. GPU security

GPU handle transfer phải chịu platform security policy.

---

# 598.319. AI IPC

AI workers có thể chia sẻ tensor buffers:

```text
Inference Server
       │
       │ TensorDescriptor
       ▼
Client
```

---

# 598.320. Tensor descriptor

Có thể chứa:

```text
device
memory_type
shape
stride
dtype
region
offset
length
```

---

# 598.321. Device ownership

GPU/device buffer ownership phải explicit.

---

# 598.322. Synchronization fence

Cross-process GPU buffer cần synchronization primitive/fence khi backend yêu cầu.

---

# 598.323. No CPU copy requirement

AI/media pipeline không được ép copy về CPU nếu direct shared accelerator memory có thể dùng.

---

# 598.324. IPC schema generation

Compiler có thể generate:

```text
schema
serializer
deserializer
client
server
compatibility checker
```

từ service definition.

---

# 598.325. Generated code trust

Generated IPC code phải là ordinary Axiom code và có thể inspect/debug.

---

# 598.326. No hidden compiler service

RPC không cần compiler daemon khi application runtime chạy.

---

# 598.327. Artifact embedding

Service schema có thể embed vào executable/package để runtime discovery.

---

# 598.328. Package manifest

Application package có thể publish:

```text
services:
  - interface_id
  - version
  - endpoint_policy
```

---

# 598.329. Deployment integration

Installer/deployer không được tự động expose privileged IPC endpoints ngoài manifest policy.

---

# 598.330. Update compatibility

Application update phải kiểm tra IPC compatibility với running companion processes/services.

---

# 598.331. Rolling update

Services có thể hỗ trợ:

```text old instance
new instance
```

song song trong transition.

---

# 598.332. Endpoint migration

Discovery có thể point clients tới new instance sau readiness.

---

# 598.333. Draining

Old instance chuyển:

```text Ready → Draining
```

và không nhận request mới.

---

# 598.334. In-flight completion

Old instance hoàn tất requests đang chạy trước shutdown nếu deadline cho phép.

---

# 598.335. Version routing

Service registry có thể route client tới compatible version.

---

# 598.336. No automatic semantic downgrade

Runtime không tự động route sang incompatible service chỉ để request succeed.

---

# 598.337. IPC cache

Schema metadata, endpoint discovery metadata và generated codecs có thể cache.

---

# 598.338. Cache invalidation

Cache identity phải bao gồm:

```text schema_id
version
ABI fingerprint
compiler/runtime compatibility
```

---

# 598.339. Build cache

Generated IPC code có thể reuse từ build cache `487`.

---

# 598.340. Reproducibility

Generated serializers/stubs phải deterministic.

---

# 598.341. Debug metadata

IPC schema mapping source:

```text source service method
      ↓
generated stub
      ↓
RPC method ID
      ↓
wire/shared representation
```

phải được debug metadata.

---

# 598.342. Source stepping

Debugger có thể step từ application call vào generated IPC stub.

---

# 598.343. Remote debugging

`589` remote debugger có thể inspect IPC topology khi permissions cho phép.

---

# 598.344. IPC profiler

`476` có thể attribute IPC cost:

```text serialization
copy
kernel transition
queue wait
server execution
```

---

# 598.345. Optimization explanation

Compiler/IDE có thể giải thích:

```text "This IPC path performs 2 copies."
```

---

# 598.346. Zero-copy explanation

Hoặc:

```text "Payload uses shared-memory descriptor; no payload copy."
```

---

# 598.347. AI optimization

AI tooling có thể suggest moving large payloads to shared memory nhưng phải preserve correctness.

---

# 598.348. AI-generated IPC

AI-generated IPC protocol phải compile + schema validate + security validate trước deployment.

---

# 598.349. No hidden endpoint

AI không được tạo globally reachable endpoint mà không có manifest/security declaration.

---

# 598.350. IPC topology graph

Semantic metadata có thể represent:

```text
Process
  ├── Endpoint
  ├── Service
  ├── Channel
  ├── SharedRegion
  └── Capability
```

---

# 598.351. IPC graph consistency

Graph phải distinguish:

```text Declared
Active
Disconnected
Stale
Unknown
```

---

# 598.352. No hallucinated topology

Debugger/AI tooling không được hiển thị endpoint như active nếu runtime chưa xác nhận.

---

# 598.353. IPC state query

Runtime API:

```text endpoint.state()
connection.state()
service.state()
```

---

# 598.354. Handle inspection

Handle metadata không expose secret/native kernel data không cần thiết.

---

# 598.355. Native escape hatch

Platform modules có thể expose native IPC handles.

---

# 598.356. Unsafe native handle

Native handle conversion phải explicit unsafe hoặc capability constructor.

---

# 598.357. Handle ownership

Native handle ownership chuyển giao phải explicit:

```text borrow
duplicate
transfer
adopt
```

---

# 598.358. Double-close prevention

Axiom handle abstraction phải bảo đảm ownership không bị double-close.

---

# 598.359. Handle duplication

OS duplicate handle phải tạo independent owner semantics.

---

# 598.360. Handle lifetime

Process exit tự động cleanup OS-owned handles.

---

# 598.361. Final API skeleton

```axiom
module axiom.ipc

struct Endpoint
struct Connection
struct Message
struct Channel<T>
struct Sender<T>
struct Receiver<T>

struct SharedMemoryRegion
struct SharedBuffer<T>
struct BufferLease<T>

struct ServiceID
struct InterfaceID
struct MethodID
struct RequestID
struct CorrelationID

struct ServiceRecord
struct PeerIdentity
struct IpcCapabilities

trait Transport
trait Service
trait RpcClient
trait RpcServer
trait ServiceRegistry
```

---

# 598.362. Core error API

```axiom
enum IpcError {
    InvalidEndpoint
    NotFound
    PermissionDenied
    AlreadyExists
    ConnectionFailed
    Disconnected
    Timeout
    Cancelled
    Closed
    BrokenPipe
    MessageTooLarge
    QueueFull
    ProtocolMismatch
    AbiMismatch
    SchemaMismatch
    StaleHandle
    ResourceLimit
    Unsupported
    PeerExited
    RemoteFailure
}
```

---

# 598.363. Message contract

```axiom
struct Message {
    type_id: TypeID
    schema_id: SchemaID
    correlation_id: CorrelationID?
    sequence: u64?
    flags: MessageFlags
    payload: ByteView
}
```

---

# 598.364. Shared descriptor contract

```axiom
struct SharedBufferDescriptor {
    region: SharedRegionID
    generation: u64
    offset: u64
    length: u64
    permissions: SharedPermissions
    schema_id: SchemaID?
}
```

---

# 598.365. Service record contract

```axiom
struct ServiceRecord {
    service_id: ServiceID
    instance_id: InstanceID
    interface_id: InterfaceID
    version: Version
    endpoint: Endpoint
    capabilities: CapabilitySet
}
```

---

# 598.366. IPC lifecycle

```text
Declare
   ↓
Create Endpoint
   ↓
Authorize
   ↓
Connect
   ↓
Negotiate
   ↓
Ready
   ↓
Communicate
   ├── Messages
   ├── RPC
   ├── Streams
   └── Shared Memory
   ↓
Drain
   ↓
Close
```

---

# 598.367. Security lifecycle

```text
Endpoint requested
        ↓
Capability check
        ↓
Peer identity
        ↓
Policy evaluation
        ↓
Allow / Deny
        ↓
Optional negotiation
        ↓
Active connection
```

---

# 598.368. Zero-copy lifecycle

```text
Allocate SharedRegion
        ↓
Create Buffer
        ↓
Fill
        ↓
Create Descriptor
        ↓
Transfer Descriptor
        ↓
Receiver Attach
        ↓
Lease
        ↓
Consume
        ↓
Release
        ↓
Reclaim
```

---

# 598.369. RPC lifecycle

```text
Client
  │
  │ Request
  ▼
Transport
  │
  ▼
Server
  │
  ├── Validate
  ├── Authorize
  ├── Execute
  └── Response
  │
  ▼
Client
```

---

# 598.370. Failure model

IPC failure phải được phân biệt:

```text
Transport failure
Protocol failure
Peer failure
Application failure
Authorization failure
Resource exhaustion
Timeout
Cancellation
```

---

# 598.371. No exception leakage

Một exception/panic nội bộ service không được tự động truyền stack/runtime state sang client.

Chỉ `RemoteError` contract được truyền.

---

# 598.372. No implicit retry

IPC runtime không retry arbitrary operations.

---

# 598.373. Explicit reliability

Protocol designer phải khai báo retry/idempotency policy.

---

# 598.374. Explicit ownership

Mọi resource cross-process phải có owner hoặc lease.

---

# 598.375. Explicit synchronization

Shared mutable memory phải có synchronization protocol.

---

# 598.376. No implicit shared mutable state

IPC channel không tự động tạo shared mutable state.

---

# 598.377. Native performance invariant

Đối với native local IPC:

```text small message
→ direct message transport

large payload
→ shared memory

same-process
→ direct queue optimization
```

khi semantics cho phép.

---

# 598.378. No mandatory serialization

Axiom không bắt mọi IPC payload phải serialize.

---

# 598.379. No mandatory shared memory

Axiom không bắt mọi IPC phải dùng shared memory.

---

# 598.380. No mandatory RPC

RPC là abstraction tùy chọn.

---

# 598.381. No mandatory registry

Service discovery là tùy chọn.

---

# 598.382. No mandatory daemon

Không có Axiom IPC daemon bắt buộc cho native application.

---

# 598.383. Portable semantics

Portable API chỉ guarantee semantics được tất cả target support.

---

# 598.384. Native optimization

Target backend có thể optimize IPC xuống:

```text syscall
shared mapping
kernel queue
direct memory
native async primitive
```

mà không thay đổi API semantics.

---

# 598.385. Compiler ownership analysis

Compiler có thể sử dụng ownership information để loại bỏ unnecessary copies.

---

# 598.386. Compiler escape analysis

Nếu compiler chứng minh buffer không escape process boundary, có thể dùng stack/register/local memory.

---

# 598.387. IPC boundary prevents unsafe escape

Compiler không được coi object đã gửi qua IPC là local-only sau khi ownership transfer.

---

# 598.388. Type system integration

IPC-safe types có thể được đánh dấu:

```text
@ipc
```

---

# 598.389. IPC type validation

`@ipc` type phải đáp ứng:

```text
layout known
serialization or shared representation defined
pointer restrictions satisfied
schema identity available
```

---

# 598.390. Compiler diagnostics

Ví dụ:

```text
AXIOM-IPC-001:
type Foo cannot cross a process boundary because it
contains a process-local pointer.
```

---

# 598.391. AI-readable diagnostic

Diagnostic metadata phải chỉ rõ:

```text cause
boundary
offending field
required fix
possible alternatives
```

---

# 598.392. Suggested fix

Compiler có thể đề xuất:

```text Replace pointer with SharedOffset<T>
or
serialize Foo
or
copy referenced data
```

---

# 598.393. IPC-safe standard types

Standard library nên cung cấp IPC-safe:

```text
bool
integers
floats
fixed arrays
structs
enums
strings
byte buffers
optional
result
```

với schema/representation rõ ràng.

---

# 598.394. Dynamic containers

Dynamic vectors/maps phải serialize hoặc shared-memory representation rõ ràng.

---

# 598.395. String encoding

Portable IPC string mặc định UTF-8.

---

# 598.396. Binary blobs

Binary payload dùng immutable byte sequence hoặc shared buffer.

---

# 598.397. Large tensor

AI tensor payload nên dùng descriptor thay vì serialization.

---

# 598.398. Media frame

Video/audio frame nên dùng shared buffer/descriptor.

---

# 598.399. File transfer

Large file transfer có thể use:

```text file handle transfer
```

hoặc shared/mapped file.

---

# 598.400. No forced file copy

Local file transfer giữa trusted processes không cần copy toàn bộ file nếu OS handle passing hỗ trợ.

---

# 598.401. Capability-based file transfer

Transferred file handle có rights attenuation.

---

# 598.402. Storage integration

`597` file handle có thể được đưa vào IPC capability transfer.

---

# 598.403. Resource integration

`596` resource handles có thể được passed giữa processes nếu resource provider cho phép.

---

# 598.404. Resource immutability

Transferred packaged resource vẫn immutable.

---

# 598.405. Process integration

`594` process supervisor owns process-level endpoint setup.

---

# 598.406. Package integration

`593` application manifest declares allowed IPC interfaces.

---

# 598.407. Security integration

`490` remains authoritative for sandbox/capability enforcement.

---

# 598.408. Network boundary

Khi endpoint remote, IPC security không được hạ thấp chỉ vì API giống local IPC.

---

# 598.409. Remote identity

Remote endpoint phải authenticate theo network security policy.

---

# 598.410. Local trust boundary

Local IPC vẫn là trust boundary giữa applications.

---

# 598.411. IPC testing matrix

```text
                    Transport
                 Pipe Socket SHM RPC
Process
Same process       ✓    ✓      ✓   ✓
Same application   ✓    ✓      ✓   ✓
Different app      ✓    ✓      ✓   ✓
Sandbox            ✓    ✓      ✓   ✓
Remote             -    ✓      -   ✓
WASM               ✓*   ✓*     ✓*  ✓*
```

`*` phụ thuộc host capability.

---

# 598.412. Performance target

Native local IPC phải hướng tới:

- low allocation;
- low copy count;
- predictable latency;
- batchable messages;
- shared-memory bulk transfer;
- native async I/O.

Không đặt một latency number universal vì hardware/OS khác nhau.

---

# 598.413. Benchmark classes

Compiler test suite phải có:

```text IPC-001 small message latency
IPC-002 throughput
IPC-003 large message
IPC-004 shared memory
IPC-005 zero-copy
IPC-006 RPC
IPC-007 contention
IPC-008 backpressure
IPC-009 peer crash
IPC-010 reconnect
IPC-011 schema mismatch
IPC-012 unauthorized peer
```

---

# 598.414. Conformance

Mỗi transport phải pass:

```text lifecycle
ordering
error
cancellation
deadline
ownership
security
resource-limit
```

tests.

---

# 598.415. Fuzz target

Fuzz:

```text endpoint parser
handshake
serializer
decoder
schema compatibility
shared descriptor
RPC dispatcher
```

---

# 598.416. Memory-safety invariant

Không malformed IPC payload nào được gây:

```text out-of-bounds
use-after-free
double-free
invalid pointer dereference
```

trong safe Axiom code.

---

# 598.417. Resource safety invariant

Process death phải không tạo permanent leaked kernel objects khi backend có automatic cleanup semantics.

---

# 598.418. Protocol safety invariant

Unknown protocol/version phải fail explicitly.

---

# 598.419. Compatibility invariant

ABI/schema mismatch không được silently interpret bytes theo layout khác.

---

# 598.420. Security invariant

IPC capability không thể được forged chỉ bằng endpoint name hoặc integer ID.

---

# 598.421. Isolation invariant

Một sandboxed process chỉ nhận IPC resources được policy cấp.

---

# 598.422. Ownership invariant

Cross-process resource ownership luôn có owner, lease hoặc explicit shared lifetime.

---

# 598.423. Zero-copy invariant

Zero-copy không được hy sinh memory safety hoặc lifetime correctness.

---

# 598.424. Performance invariant

Large payloads phải có đường đi tránh unnecessary serialization/copy khi shared memory hoặc native handle transfer khả dụng.

---

# 598.425. Determinism invariant

Schema generation, stub generation và artifact metadata phải deterministic.

---

# 598.426. Debug invariant

IPC debugger state phải phản ánh state runtime thực tế; không được suy diễn endpoint active chỉ từ source declaration.

---

# 598.427. AI invariant

AI tooling chỉ được đề xuất hoặc thực hiện IPC mutation trong phạm vi capability/permission được cấp.

---

# 598.428. Minimal-runtime invariant

Application không dùng RPC/shared-memory/service-discovery không phải mang toàn bộ IPC framework vào binary.

---

# 598.429. Final hard invariant

Axiom IPC phải đạt kiến trúc:

```text
                         IPC
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Message          Stream          Shared Memory
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                    Typed Boundary
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
             RPC        Events       Bulk
              │           │           │
              └───────────┼───────────┘
                          ▼
                  Capability Security
                          │
                          ▼
                    Native Backend
```

Các nguyên tắc không được phá:

1. **IPC không đồng nghĩa RPC.**
2. **IPC không đồng nghĩa serialization.**
3. **IPC không đồng nghĩa shared memory.**
4. **Không bắt buộc daemon trung gian.**
5. **Không có ambient IPC authority.**
6. **Handle/capability phải explicit.**
7. **Shared memory không dùng raw process-local pointer.**
8. **Large payload phải có zero-copy path khi khả thi.**
9. **ABI/schema mismatch phải fail rõ ràng.**
10. **Không tự động retry operation không idempotent.**
11. **Không claim exactly-once nếu transport không đảm bảo.**
12. **Process crash không được biến thành memory corruption của peer.**
13. **IPC failure phải biểu diễn bằng `Result`, không tự động panic.**
14. **AI không được tự ý mở endpoint hoặc cấp capability.**
15. **Native IPC phải có đường codegen trực tiếp, không phụ thuộc compiler bên thứ ba.**
16. **IPC subsystem không được trở thành mandatory runtime dependency.**

# 598 — LOCKED

Axiom hiện đã có đầy đủ chuỗi:

```text
593 Application Package
        ↓
594 Process Supervision
        ↓
596 Resource Runtime
        ↓
597 User/Application Storage
        ↓
598 Inter-Process Communication
        ↓
        └── Process ↔ Process
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
      Message  RPC     Shared Memory
```

---

# NEXT — BOOTSTRAP-599

## NATIVE APPLICATION SERVICE MODEL & LOCAL SERVICE HOSTING 6.0

### SERVICE REGISTRATION, SERVICE HOST, DAEMON, BACKGROUND SERVICE, SYSTEM SERVICE, STARTUP POLICY, HEALTH/READINESS, DEPENDENCY GRAPH, SUPERVISION, IPC BINDING, PRIVILEGE SEPARATION, SERVICE INSTALLATION, UPDATE, FAILURE RECOVERY & CROSS-PLATFORM SERVICE ABSTRACTION

```text
                         Application Package
                                │
                                ▼
                         Service Definition
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                User Service  App Service  System Service
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         Service Host
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 Process      IPC        Storage
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                          Supervisor 594
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                  Start       Health       Restart
```

`599` sẽ định nghĩa **service là một deployment/runtime abstraction nằm trên process + IPC + storage + supervision**, phân biệt rõ `application process`, `background worker`, `user service` và `system service`, đồng thời tránh biến Axiom thành một hệ điều hành riêng.