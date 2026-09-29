Tiếp tục chuỗi đặc tả Axiom từ **BOOTSTRAP-604**, giữ cùng mức chi tiết và khả năng triển khai compiler/runtime như các task trước.

:::writing{variant="document" id="58321" title="BOOTSTRAP-604 — Native Application IPC, Shared Memory & Message Transport Runtime 5.0"}

# BOOTSTRAP-604
## Native Application IPC, Inter-Process Communication, Shared Memory & Message Transport Runtime 5.0

**Status:** Architecture Specification  
**Phase:** Native Runtime / Application Infrastructure  
**Depends on:** BOOTSTRAP-600, BOOTSTRAP-601, BOOTSTRAP-602, BOOTSTRAP-603  
**Scope:** IPC giữa các process/module/service native của Axiom  
**Primary goals:** hiệu năng cao, an toàn, zero-copy khi có thể, API thống nhất đa nền tảng, không phụ thuộc third-party runtime

---

# 604.0 — Mục tiêu

Axiom cần một IPC runtime thống nhất để các process có thể:

- gửi message;
- gọi request/response;
- truyền stream;
- truyền buffer lớn;
- chia sẻ memory;
- truyền OS handle;
- truyền capability;
- phát event;
- phát hiện peer chết;
- timeout/cancel;
- reconnect;
- kiểm soát backpressure;
- xác thực peer;
- kiểm soát quyền truy cập.

IPC phải hoạt động trên:

- Windows;
- Linux;
- macOS;
- Android;
- iOS;
- WASM/WASI ở mức capability phù hợp;
- embedded target nếu platform adapter cung cấp primitive tương ứng.

IPC core **không được phụ thuộc vào TCP/IP**.

IPC mạng và distributed networking là lớp khác.

---

# 604.1 — Nguyên tắc kiến trúc

Axiom IPC được chia thành các lớp:

```text
Application
    ↓
Service / RPC API
    ↓
Message API
    ↓
Transport
    ↓
OS IPC Primitive
```

Shared memory đi theo nhánh:

```text
Application
    ↓
SharedBuffer / SharedRegion
    ↓
SharedMemory Transport
    ↓
OS Shared Memory Primitive
```

Security:

```text
BOOTSTRAP-603
        ↓
Capability
        ↓
Endpoint authorization
        ↓
Message / shared-memory operation
```

Diagnostics:

```text
BOOTSTRAP-602
        ↓
IPC trace / metrics / faults
```

State:

```text
BOOTSTRAP-600
        ↓
checkpoint / recovery integration
```

Configuration:

```text
BOOTSTRAP-601
        ↓
endpoint / limits / policy configuration
```

---

# 604.2 — IPC không phải distributed system

Core IPC chỉ đảm bảo semantics trong phạm vi mà transport hỗ trợ.

Axiom không tuyên bố:

- exactly-once delivery;
- distributed transactions;
- consensus;
- distributed locks;
- global ordering;
- network reliability.

Những chức năng đó thuộc distributed/runtime service layer.

Đặc biệt:

```text
IPC ≠ networking
IPC ≠ distributed computing
IPC ≠ message broker
```

IPC có thể sử dụng socket transport nhưng socket chỉ là implementation detail.

---

# 604.3 — Các primitive chính

Core IPC cung cấp:

```text
Endpoint
Channel
Message
Request
Response
Stream
Event
SharedRegion
SharedBuffer
Handle
Peer
Service
Subscription
```

Các primitive này phải có ABI ổn định.

---

# 604.4 — Endpoint

Endpoint xác định một điểm giao tiếp.

Khái niệm:

```text
Endpoint
    scheme
    name
    namespace
    security
    transport
```

Ví dụ:

```text
ipc://app/service
ipc://user/cache
ipc://system/logger
```

Không expose trực tiếp OS-specific naming vào application API.

---

# 604.5 — Endpoint namespace

Có ba namespace:

```text
ProcessLocal
User
System
```

Ví dụ:

```text
ipc://process/foo
ipc://user/myapp/cache
ipc://system/service
```

Application không được tự ý tạo endpoint thuộc namespace cao hơn capability được cấp.

---

# 604.6 — Endpoint identity

Endpoint identity gồm:

```text
EndpointId
ServiceName
InstanceId
Namespace
Generation
```

`Generation` giúp tránh nhầm endpoint cũ sau khi service restart.

---

# 604.7 — Service

Service là logical owner của một hoặc nhiều endpoint.

Ví dụ:

```axiom
service ImageProcessor {
    fn resize(image: Image, width: u32, height: u32) -> Image
}
```

Compiler có thể sinh:

```text
ImageProcessorClient
ImageProcessorServer
ImageProcessorMessage
ImageProcessorCodec
```

---

# 604.8 — Struct-only service model

Axiom không cần class để xây service.

Ví dụ:

```axiom
struct ImageProcessor {
    workers: u32
}

fn process(self: ImageProcessor, image: Image) -> Result<Image>
```

IPC binding chỉ coi function có metadata service là RPC method.

```axiom
@ipc
fn process(self: ImageProcessor, image: Image) -> Result<Image>
```

`self` không phải object reference đặc biệt.

Nó vẫn là tham số struct bình thường.

---

# 604.9 — Method identity

Mỗi IPC method có:

```text
ServiceId
MethodId
SchemaVersion
```

Không sử dụng tên string làm identifier runtime chính.

Compiler tạo ID ổn định từ declaration metadata.

Có thể cho phép explicit ID:

```axiom
@ipc(id=0x1020)
fn process(...)
```

---

# 604.10 — Channel

Channel là đường truyền hai chiều logic:

```text
Peer A ←→ Channel ←→ Peer B
```

Channel có:

```text
send()
recv()
close()
cancel()
```

Channel không nhất thiết tương ứng 1:1 với OS socket/pipe.

---

# 604.11 — One-way channel

Cho event/fire-and-forget:

```axiom
channel.send(event)
```

Không tạo response queue nếu không cần.

Điều này giảm:

- memory;
- context switching;
- bookkeeping.

---

# 604.12 — Request/response

RPC semantics:

```text
request → response
```

Mỗi request có:

```text
RequestId
MethodId
Payload
Deadline
Flags
```

Response:

```text
RequestId
Status
Payload
Flags
```

---

# 604.13 — Request ID

`RequestId` là 128-bit logical identifier hoặc dạng compact 64-bit trong fast path.

Runtime phải chống collision trong phạm vi channel.

---

# 604.14 — Streaming

Một request có thể trả nhiều chunk:

```text
request
  ↓
chunk
  ↓
chunk
  ↓
chunk
  ↓
complete
```

Không cần gom toàn bộ stream vào RAM.

API:

```axiom
stream.next()
stream.cancel()
```

---

# 604.15 — Event subscription

Service có thể phát event:

```axiom
@event
struct FrameReady {
    frame: Frame
}
```

Client:

```axiom
subscribe(FrameReady)
```

Subscription phải có lifecycle rõ ràng.

---

# 604.16 — Message envelope

Mọi message transport-level có envelope:

```text
magic
version
flags
message_type
schema_id
request_id
payload_size
header_size
payload
```

Envelope phải được thiết kế để:

- parse nhanh;
- validate nhanh;
- forward-compatible;
- chống malformed input.

---

# 604.17 — Message size

Không có message size vô hạn.

Mỗi endpoint có:

```text
max_message_size
max_queue_bytes
max_inflight_requests
```

Giá trị mặc định phải bounded.

Application có thể tăng thông qua capability/configuration phù hợp.

---

# 604.18 — Serialization

Axiom IPC serialization sử dụng binary encoding mặc định.

Không dùng:

- JSON;
- XML;
- reflection runtime nặng;

cho fast-path native IPC.

Text encoding chỉ là adapter.

---

# 604.19 — ABI-safe serialization

Không serialize raw memory layout của struct mặc định.

Sai:

```axiom
send(raw_bytes_of_struct)
```

Đúng:

```text
logical field encoding
```

Điều này tránh phụ thuộc:

- padding;
- alignment;
- pointer size;
- compiler version;
- endian;
- target ABI.

---

# 604.20 — Primitive encoding

Các primitive có canonical representation:

```text
u8/u16/u32/u64
i8/i16/i32/i64
f32/f64
bool
char
bytes
string
array
map
optional
enum
struct
```

UTF-8 là encoding mặc định cho string.

---

# 604.21 — Integer encoding

Mặc định:

```text
fixed-width
```

cho predictable decoding.

Varint chỉ dùng khi schema đánh dấu:

```axiom
@compact
```

Compiler không được tự ý thay đổi wire representation mà phá compatibility.

---

# 604.22 — Endianness

Wire format sử dụng một endian canonical.

Native endian chỉ được dùng trong shared-memory structures khi region có ABI descriptor tương ứng.

---

# 604.23 — Schema identity

Mỗi schema có:

```text
SchemaId
Version
Fingerprint
```

Fingerprint được compiler tạo deterministic.

Ví dụ:

```text
SchemaId = hash(canonical_schema_definition)
```

---

# 604.24 — Schema evolution

Cho phép:

- thêm field;
- bỏ field;
- field optional;
- enum extension;
- version negotiation.

Không cho phép silently thay đổi meaning của field cũ.

---

# 604.25 — Unknown fields

Decoder phải có khả năng:

```text
ignore unknown field
```

khi schema cho phép.

Điều này giúp rolling upgrade.

---

# 604.26 — Required field

Core schema nên hạn chế required fields để giảm compatibility problem.

Field quan trọng có thể:

```axiom
field: T
```

Field backward-compatible:

```axiom
field?: T
```

---

# 604.27 — Bounds validation

Decoder phải validate trước khi cấp phát.

Không được:

```text
read count
allocate count * element_size
```

mà không kiểm tra overflow/bounds.

Phải:

```text
validate count
validate byte_size
validate remaining payload
then allocate
```

---

# 604.28 — Zero-copy

IPC runtime phải hỗ trợ ba path:

```text
Copy
Move
ZeroCopy
```

Runtime tự chọn path dựa trên transport và message type.

---

# 604.29 — Small message fast path

Message nhỏ nên được truyền trực tiếp qua inline buffer.

Ví dụ:

```text
≤ 256 bytes
```

có thể sử dụng inline storage tùy backend.

Mục tiêu:

- không heap allocation;
- ít syscall;
- ít copy.

---

# 604.30 — Large message path

Message lớn chuyển sang:

```text
SharedRegion
```

thay vì copy nhiều lần.

Pattern:

```text
control message
    ↓
shared memory handle
    ↓
large payload
```

---

# 604.31 — SharedRegion

`SharedRegion` biểu diễn vùng memory có thể map vào nhiều process.

Properties:

```text
RegionId
size
protection
owner
generation
capability
```

---

# 604.32 — SharedBuffer

`SharedBuffer` là slice có bounds:

```text
region
offset
length
```

Không chứa raw pointer cross-process.

---

# 604.33 — Cross-process pointer prohibition

Axiom IPC không cho phép truyền raw pointer giữa process.

Sai:

```text
ptr = 0x12345678
```

Đúng:

```text
SharedBuffer {
    region_id
    offset
    length
}
```

Mỗi process map region ở địa chỉ khác nhau vẫn hoạt động.

---

# 604.34 — Shared memory ownership

Shared memory phải có ownership state:

```text
Created
Published
InUse
Released
Closed
```

Không được tự động free khi một peer vẫn sở hữu reference hợp lệ.

---

# 604.35 — Reference counting

IPC runtime không yêu cầu GC.

Shared resource sử dụng explicit lifetime + atomic reference accounting hoặc lease.

---

# 604.36 — Handle

`Handle<T>` là opaque runtime token.

Handle có:

```text
type
index
generation
rights
```

Không phải pointer.

---

# 604.37 — Handle generation

Sau khi handle bị đóng:

```text
generation++
```

Handle cũ trở thành invalid.

Điều này ngăn stale-handle reuse.

---

# 604.38 — Capability transfer

Theo BOOTSTRAP-603, IPC có thể truyền capability.

Ví dụ:

```text
Process A
   |
   | Capability<SharedRegion>
   ↓
Process B
```

Transfer phải:

- explicit;
- authorized;
- auditable;
- có quyền attenuation.

---

# 604.39 — Capability attenuation

Process gửi handle với quyền thấp hơn quyền gốc.

Ví dụ:

```text
READ | WRITE
```

có thể gửi:

```text
READ
```

nhưng không thể tự nâng lên:

```text
READ | WRITE | EXECUTE
```

---

# 604.40 — OS handle transfer

Platform backend có thể truyền:

- file descriptor;
- Windows HANDLE;
- Mach port;
- platform-native IPC token.

Application chỉ thấy:

```axiom
Handle<T>
```

---

# 604.41 — Handle type safety

Handle phải mang type information compile-time:

```axiom
Handle<File>
Handle<SharedRegion>
Handle<Socket>
Handle<Device>
```

Không implicit cast giữa các handle type.

---

# 604.42 — Transport abstraction

Transport interface:

```axiom
trait Transport {
    fn send(self, message: Message) -> Result
    fn receive(self) -> Result<Message>
    fn close(self)
}
```

Backend:

```text
Loopback
Pipe
UnixDomainSocket
WindowsNamedPipe
SharedMemory
PlatformNative
```

---

# 604.43 — Loopback transport

Dùng cho:

- unit tests;
- same-process modules;
- benchmarks.

Không syscall.

---

# 604.44 — Windows backend

Có thể sử dụng:

```text
Named Pipes
```

và các native primitive khác khi cần.

Axiom API không expose Windows-specific types ở core layer.

---

# 604.45 — Linux backend

Ưu tiên:

```text
Unix Domain Socket
shared memory
eventfd/futex tương ứng
```

tùy transport.

---

# 604.46 — macOS backend

Có thể map xuống:

```text
Unix Domain Socket
Mach-based native transport
shared memory
```

Core API không phụ thuộc Mach.

---

# 604.47 — Android backend

Android adapter có thể tích hợp:

```text
Binder
Unix Domain Socket
shared memory primitives
```

Binder-specific semantics nằm trong platform layer.

---

# 604.48 — iOS backend

Có thể hỗ trợ:

```text
XPC
Mach
shared memory primitives
```

nhưng API application vẫn là Axiom IPC abstraction.

---

# 604.49 — WASM

WASM sandbox không có native process IPC mặc định.

Core phải cung cấp capability-dependent adapter:

```text
HostMessage
HostSharedBuffer
```

Nếu host không cung cấp IPC:

```text
IPC capability unavailable
```

Không giả lập bằng hidden global state.

---

# 604.50 — Service discovery

Service discovery gồm:

```text
register
lookup
resolve
watch
unregister
```

Không bắt buộc broker trung tâm.

---

# 604.51 — Brokerless default

Core IPC mặc định:

```text
Client ───────── Server
```

Không:

```text
Client → Broker → Server
```

trừ khi platform yêu cầu.

Điều này giảm:

- latency;
- memory;
- failure points;
- attack surface.

---

# 604.52 — Optional broker

Một broker có thể được xây ở higher-level runtime cho:

- dynamic discovery;
- multi-tenant routing;
- policy management;
- service lifecycle.

Broker không thuộc IPC primitive core.

---

# 604.53 — Service registration

Service đăng ký:

```text
ServiceId
Endpoint
Version
Capabilities
Health
```

Registration có lease hoặc explicit lifetime.

---

# 604.54 — Peer identity

IPC phải expose:

```text
PeerId
ProcessId
UserId
PlatformIdentity
SecurityContext
```

nếu platform hỗ trợ.

Không được suy đoán identity khi OS không cung cấp.

---

# 604.55 — Peer authentication

Local IPC có thể dựa trên OS credentials.

Application-level authentication là optional.

Core không tự invent cryptography.

Nếu encryption/integrity cần thiết, sử dụng crypto primitive được Axiom platform/runtime cung cấp.

---

# 604.56 — Authorization

Kết nối thành công không đồng nghĩa được phép gọi mọi method.

Authorization chain:

```text
OS identity
 ↓
Capability
 ↓
Endpoint policy
 ↓
Method permission
 ↓
Operation
```

phù hợp BOOTSTRAP-603.

---

# 604.57 — Method capability

Có thể yêu cầu:

```axiom
@requires(ipc.call("ImageProcessor.resize"))
fn use_processor(...)
```

Compiler/runtime kiểm tra capability metadata.

---

# 604.58 — Connection handshake

Handshake tối thiểu:

```text
protocol_version
endpoint_id
peer_id
feature_flags
schema_versions
transport_features
security_context
```

Handshake phải bounded.

---

# 604.59 — Feature negotiation

Ví dụ:

```text
ZERO_COPY
SHARED_MEMORY
HANDLE_TRANSFER
STREAMING
COMPRESSION
CANCELLATION
```

Hai peer chỉ sử dụng feature chung.

---

# 604.60 — Version negotiation

Nếu protocol version không tương thích:

```text
ProtocolMismatch
```

Không cố decode message bằng format không tương thích.

---

# 604.61 — Ordering

Trong cùng một ordered channel:

```text
M1 → M2 → M3
```

receiver thấy:

```text
M1 → M2 → M3
```

Cross-channel ordering không được đảm bảo.

---

# 604.62 — Delivery semantics

Core cung cấp:

```text
SendAccepted
DeliveredToTransport
Received
Completed
```

Các trạng thái khác nhau phải được phân biệt.

`send()` không mặc định có nghĩa remote application đã xử lý message.

---

# 604.63 — At-most-once RPC

RPC mặc định có semantics:

```text
at-most-once per request identity
```

Runtime có thể detect duplicate request ID trong retry window.

Không tuyên bố exactly-once execution.

---

# 604.64 — Retry

Retry chỉ được tự động nếu operation được đánh dấu idempotent:

```axiom
@idempotent
fn get(...)
```

Operation mutation không được retry tự động mặc định.

---

# 604.65 — Timeout

API hỗ trợ:

```axiom
request.with_timeout(500ms)
```

Timeout phải được truyền thành deadline.

---

# 604.66 — Deadline

Deadline format:

```text
MonotonicTimestamp
```

Không dùng wall-clock để timeout.

---

# 604.67 — Cancellation

Request có cancellation token:

```axiom
cancel(request)
```

Cancellation là cooperative.

Server có thể nhận:

```text
CancellationRequested
```

Không guarantee process/thread bị terminate ngay lập tức.

---

# 604.68 — Disconnect

Peer disconnect tạo event:

```text
PeerDisconnected
```

Pending requests chuyển thành:

```text
PeerUnavailable
```

hoặc status cụ thể.

---

# 604.69 — Crash detection

Nếu process chết, OS transport phải phát hiện disconnect.

Runtime không được chờ vô hạn.

---

# 604.70 — Reconnect

Client có thể:

```text
reconnect()
```

nhưng pending request không tự động được replay trừ khi semantics cho phép.

---

# 604.71 — Service restart

Service restart tạo:

```text
new InstanceId
new Generation
```

Client không được coi endpoint cũ là cùng process.

---

# 604.72 — Backpressure

IPC phải có backpressure.

Không cho phép producer tạo queue vô hạn.

Các chiến lược:

```text
Block
Fail
Drop
Coalesce
AwaitCapacity
```

---

# 604.73 — Event backpressure

Event subscriber chậm có thể:

```text
DropOldest
DropNewest
BlockProducer
DisconnectSlowPeer
```

Policy phải explicit.

---

# 604.74 — Queue

Queue có:

```text
max_messages
max_bytes
current_messages
current_bytes
```

Counters phải atomic/lock-free hoặc low-contention tùy backend.

---

# 604.75 — Flow control

Streaming sử dụng credit/window:

```text
sender → N bytes
receiver → credit
sender → next bytes
```

Tránh memory explosion.

---

# 604.76 — Shared-memory ring buffer

IPC cung cấp optional ring buffer:

```text
producer
    ↓
[slot][slot][slot][slot]
                  ↓
                consumer
```

Mỗi slot có:

```text
state
sequence
length
payload
```

---

# 604.77 — Ring-buffer states

Ví dụ:

```text
FREE
RESERVED
READY
READING
FREE
```

State transitions phải atomic.

---

# 604.78 — Memory ordering

Shared-memory synchronization phải chỉ rõ memory ordering.

Không phụ thuộc compiler accidental behavior.

Axiom atomic model phải map xuống:

```text
Acquire
Release
AcqRel
SeqCst
Relaxed
```

theo core concurrency specification.

---

# 604.79 — Cache-line considerations

Shared-memory structures nên hỗ trợ alignment metadata để tránh false sharing.

Compiler có thể cung cấp:

```axiom
@cache_aligned
```

cho IPC hot structures.

---

# 604.80 — Shared-memory ABI descriptor

Region có header:

```text
magic
version
schema_id
architecture
pointer_size
alignment
endianness
capacity
flags
```

Không chứa process-local pointer.

---

# 604.81 — Shared-memory corruption

Nếu header/schema invalid:

```text
RegionCorrupt
```

Consumer không được dereference dữ liệu.

---

# 604.82 — Memory protection

Shared memory hỗ trợ:

```text
READ
WRITE
```

`EXECUTE` mặc định bị cấm.

Phù hợp W^X từ BOOTSTRAP-603.

---

# 604.83 — Executable shared memory

IPC runtime không được mặc định hỗ trợ executable shared memory.

Chỉ được bật với capability:

```text
memory.exec
```

và policy phù hợp.

---

# 604.84 — Large buffer lifecycle

API:

```axiom
region = SharedRegion.create(size)
buffer = region.slice(offset, length)
send(buffer)
```

Receiver:

```axiom
buffer = message.shared_buffer()
```

Release:

```axiom
buffer.release()
```

---

# 604.85 — Buffer slicing

Slice không được copy.

```text
SharedRegion
 └── SharedBuffer[offset,length]
```

Bounds được kiểm tra khi tạo slice.

---

# 604.86 — Buffer ownership transfer

Có hai semantics:

```text
Borrow
Move
```

Borrow chỉ tồn tại trong lifetime được đảm bảo.

Move chuyển ownership.

---

# 604.87 — Borrow semantics IPC

Không sử dụng borrow checker global.

IPC borrow chỉ là runtime contract:

```text
borrow valid until message completion
```

Compiler có thể enforce một số lifetime đơn giản.

---

# 604.88 — Message builder

Compiler/runtime cung cấp:

```axiom
MessageBuilder
```

cho dynamic message construction.

Static generated messages vẫn là fast path.

---

# 604.89 — Generated codec

Từ:

```axiom
struct User {
    id: u64
    name: string
}
```

compiler tạo:

```text
encode_User()
decode_User()
```

Không cần reflection runtime.

---

# 604.90 — Compile-time serialization

Compiler biết:

```text
field offsets
field types
schema IDs
bounds
```

và có thể inline codec.

---

# 604.91 — Decode safety

Generated decoder phải:

1. kiểm tra header;
2. kiểm tra payload length;
3. kiểm tra field count;
4. kiểm tra integer overflow;
5. kiểm tra allocation limit;
6. decode;
7. validate semantic constraints.

---

# 604.92 — Semantic validation

Schema có thể khai báo:

```axiom
age: u8 @range(0..150)
```

Decoder có thể reject:

```text
InvalidValue
```

---

# 604.93 — String validation

String wire data phải là UTF-8 nếu schema yêu cầu string.

Invalid UTF-8:

```text
InvalidEncoding
```

Không silently sửa dữ liệu.

---

# 604.94 — Compression

Compression không thuộc fast-path mặc định.

Có thể bật:

```text
COMPRESSED
```

khi payload đủ lớn.

Compression phải chịu giới hạn resource.

---

# 604.95 — Compression bomb protection

Receiver không được allocate theo compressed size mà bỏ qua decompressed limit.

Phải có:

```text
max_decompressed_bytes
```

---

# 604.96 — Encryption

Encryption là optional transport feature.

Không ép mọi local IPC phải encryption nếu OS đã cung cấp security boundary phù hợp.

Nếu policy yêu cầu confidentiality, transport phải fail closed khi encryption unavailable.

---

# 604.97 — Integrity

Message có thể có integrity metadata:

```text
auth tag / signature
```

nếu security policy yêu cầu.

---

# 604.98 — Replay protection

Nếu transport có security token/message authentication, phải hỗ trợ sequence/nonce để ngăn replay.

---

# 604.99 — IPC quotas

Mỗi peer có thể bị giới hạn:

```text
max_connections
max_inflight
max_queue_bytes
max_shared_memory
max_message_size
max_handles
```

---

# 604.100 — DoS resistance

Malformed peer không được làm:

- process crash;
- unbounded allocation;
- queue exhaustion;
- handle exhaustion;
- thread explosion.

---

# 604.101 — Threading model

IPC runtime không được tạo một OS thread cho mỗi connection theo mặc định.

Ưu tiên:

```text
event loop
IO completion
polling
shared worker pool
```

tùy platform.

---

# 604.102 — Callback execution

Không chạy user callback trực tiếp trong privileged transport thread nếu có thể tránh.

Transport thread chỉ:

```text
receive
validate
enqueue
```

Application executor xử lý callback.

---

# 604.103 — Async API

API:

```axiom
async fn call(...)
```

phải tích hợp với Axiom async runtime.

Không tạo event-loop riêng cho mỗi IPC connection.

---

# 604.104 — Sync API

Cho application đơn giản:

```axiom
response = client.call(request)
```

Sync API chỉ là facade trên transport primitive.

---

# 604.105 — Reentrancy

IPC callback không được mặc định re-enter cùng state machine theo cách gây deadlock.

Runtime phải document rõ:

```text
callback context
lock context
executor context
```

---

# 604.106 — Deadlock avoidance

IPC runtime không giữ global IPC lock khi:

```text
calling user code
waiting remote response
performing arbitrary allocation
```

---

# 604.107 — Local call optimization

Nếu compiler chứng minh client/server cùng process:

```text
RPC → direct function call
```

có thể được tối ưu.

Semantics observable phải tương thích.

---

# 604.108 — In-process transport

`LoopbackTransport` dùng cùng message abstraction.

Cho phép test:

```text
Client
  ↓
Loopback
  ↓
Server
```

mà không cần process creation.

---

# 604.109 — IPC transaction context

Mỗi request có context:

```text
request_id
peer_id
deadline
trace_id
security_context
```

Context tích hợp BOOTSTRAP-602.

---

# 604.110 — Distributed tracing

IPC request có thể propagate:

```text
TraceId
SpanId
TraceFlags
```

Không bắt buộc tracing để IPC hoạt động.

---

# 604.111 — Logging

IPC events có structured event IDs:

```text
IPC_CONNECT
IPC_DISCONNECT
IPC_SEND
IPC_RECEIVE
IPC_TIMEOUT
IPC_PROTOCOL_ERROR
IPC_AUTH_FAILURE
IPC_BACKPRESSURE
```

Không log payload mặc định.

---

# 604.112 — Secret protection

Payload có field `Secret<T>` phải được:

- redact trong logs;
- không dump vào diagnostics;
- không copy sang debug buffer.

---

# 604.113 — Crash diagnostics

Khi IPC crash/fault xảy ra, diagnostics có thể lưu:

```text
peer identity
endpoint
request id
method id
transport
queue statistics
last protocol state
```

Không lưu plaintext secret.

---

# 604.114 — IPC metrics

Metrics:

```text
messages_sent
messages_received
bytes_sent
bytes_received
active_connections
pending_requests
timeouts
disconnects
protocol_errors
auth_failures
queue_drops
shared_memory_bytes
```

Counters có thể disabled compile-time.

---

# 604.115 — Diagnostics sampling

High-frequency IPC trace phải hỗ trợ sampling để tránh overhead.

---

# 604.116 — State integration

BOOTSTRAP-600 state system có thể checkpoint logical IPC state:

```text
service identity
subscription metadata
pending recoverable operations
```

Không checkpoint raw OS handles.

Sau recovery phải recreate handles.

---

# 604.117 — Recovery

IPC recovery sequence:

```text
process restart
 ↓
reinitialize runtime
 ↓
recreate endpoint
 ↓
register service
 ↓
reconnect peers
 ↓
restore subscriptions
 ↓
resume recoverable operations
```

---

# 604.118 — Non-recoverable operations

Pending operation sử dụng OS resource không recoverable phải chuyển thành:

```text
RecoveryLost
```

Không giả vờ request vẫn tồn tại.

---

# 604.119 — Configuration integration

BOOTSTRAP-601 có thể cấu hình:

```text
IPC limits
default transport
endpoint namespace
timeouts
security policy
shared memory limits
logging policy
```

Configuration snapshot được gắn với runtime diagnostics.

---

# 604.120 — Configuration reload

Thay đổi IPC configuration không được phá connection đang hoạt động nếu không cần thiết.

Policy mới áp dụng cho:

```text
new connections
new requests
```

trừ khi field yêu cầu immediate enforcement.

---

# 604.121 — Security policy integration

BOOTSTRAP-603 policy quyết định:

```text
who may connect
who may call
what capability may transfer
what shared memory may be mapped
what handle types may cross boundary
```

IPC không bypass capability system.

---

# 604.122 — Capability revocation

Khi capability bị revoke:

```text
future operations → denied
```

Các operation đang chạy xử lý theo revocation policy.

---

# 604.123 — IPC endpoint capability

Một process không có:

```text
ipc.connect(endpoint)
```

capability không được connect endpoint đó.

---

# 604.124 — Listener capability

Server cần:

```text
ipc.listen(endpoint)
```

capability riêng.

Connect và listen không đồng nghĩa.

---

# 604.125 — Method authorization

Một peer có thể connect nhưng chỉ được phép:

```text
method A
method B
```

không được:

```text
method C
```

---

# 604.126 — Capability transfer audit

Mọi transfer capability có thể tạo audit event:

```text
CAPABILITY_TRANSFER
```

gồm:

```text
source
destination
type
attenuated_rights
timestamp
```

Không ghi secret content.

---

# 604.127 — Service isolation

Service có thể chạy trong process riêng.

IPC boundary trở thành security boundary.

```text
App
 │
 IPC
 ├── GraphicsService
 ├── StorageService
 └── PluginService
```

---

# 604.128 — Plugin communication

Plugin sandbox không được trực tiếp truy cập application internals.

Plugin dùng IPC/capability interface.

Điều này cho phép thay plugin implementation mà không đổi API.

---

# 604.129 — ABI boundary

IPC là ABI boundary rõ ràng.

Không expose:

```text
compiler-specific vtable
raw pointer
private struct layout
```

---

# 604.130 — Stable interface

Public IPC schema phải có:

```text
stable IDs
versioning
compatibility rules
```

Compiler có thể cảnh báo breaking changes.

---

# 604.131 — Interface compiler diagnostics

Ví dụ:

```text
AXIOM IPC E6041:
field removal breaks required compatibility
```

Compiler nên phát hiện ở build time.

---

# 604.132 — Schema compatibility checker

Build system cung cấp:

```text
axiom ipc check-compat
```

Input:

```text
old.schema
new.schema
```

Output:

```text
compatible
conditionally-compatible
breaking
```

---

# 604.133 — IPC interface artifact

Compiler có thể tạo:

```text
service.axipc
```

artifact chứa:

```text
service ID
method IDs
schema
version
codec metadata
security requirements
transport requirements
```

Artifact phục vụ:

- compiler;
- tooling;
- AI agents;
- documentation;
- compatibility checking.

---

# 604.134 — AI-readable IPC metadata

Artifact phải có machine-readable representation:

```text
service
method
input
output
errors
permissions
side_effects
idempotency
streaming
```

AI tooling có thể hiểu interface mà không đọc compiler internals.

---

# 604.135 — Side-effect declaration

IPC method có thể khai báo:

```axiom
@readonly
@idempotent
@streaming
```

để compiler/runtime biết semantics.

---

# 604.136 — Error model

IPC errors là typed:

```axiom
enum IpcError {
    Timeout
    Cancelled
    Disconnected
    PermissionDenied
    ProtocolMismatch
    InvalidMessage
    ResourceLimit
    ServiceUnavailable
}
```

Platform-specific error có thể nằm trong `PlatformError`.

---

# 604.137 — Remote exception prohibition

Server không gửi raw exception object.

Chỉ gửi structured error.

Điều này tránh:

- ABI leakage;
- stack leakage;
- implementation details.

---

# 604.138 — Panic isolation

Server panic không được mặc định crash client.

Server runtime xử lý panic theo BOOTSTRAP-602.

Client nhận:

```text
RemoteFailure
```

nếu process vẫn có thể phản hồi.

---

# 604.139 — Malformed message behavior

Malformed input:

```text
reject
record diagnostic
optionally disconnect peer
```

Không gọi application handler trước khi decode/validate xong.

---

# 604.140 — Fuzzing

Codec và envelope parser bắt buộc fuzz.

Targets:

```text
header parser
schema decoder
shared-memory descriptor
handle transfer
handshake
compression
capability metadata
```

---

# 604.141 — Fault injection

Test:

```text
peer kill
connection reset
partial message
corrupted payload
timeout
queue full
shared region revoked
handle invalidated
service restart
```

---

# 604.142 — Race testing

Shared-memory implementation phải test:

```text
producer/consumer races
close/send races
disconnect/reconnect races
cancel/complete races
capability revoke/use races
```

---

# 604.143 — Deterministic tests

Loopback transport phải cho phép deterministic scheduling để test race-sensitive semantics.

---

# 604.144 — Benchmark suite

Benchmark:

```text
small message latency
large message throughput
RPC round trip
one-way throughput
shared-memory throughput
zero-copy throughput
serialization cost
connection setup
concurrent clients
backpressure
```

---

# 604.145 — Performance targets

Mục tiêu architecture:

```text
small local message:
    minimal allocation
    minimal syscall

large payload:
    avoid repeated copies

concurrency:
    no global IPC lock

idle:
    near-zero CPU
```

Exact numeric targets được benchmark theo từng platform.

---

# 604.146 — Allocation policy

Fast path không được yêu cầu heap allocation cho mọi message.

Có thể sử dụng:

```text
stack inline buffer
per-channel slab
ring buffer
preallocated pool
```

---

# 604.147 — Memory pools

IPC pools phải:

- bounded;
- localizable per worker/channel;
- không tạo fragmentation không kiểm soát.

---

# 604.148 — Binary size

IPC feature modules phải tách được:

```text
core
serialization
shared_memory
rpc
discovery
security
platform adapters
```

Unused components phải dead-strip.

---

# 604.149 — No mandatory runtime broker

Một binary chỉ sử dụng local RPC không được kéo toàn bộ service-discovery stack vào executable.

---

# 604.150 — Static linking

IPC runtime phải link statically vào native executable nếu developer chọn static deployment.

---

# 604.151 — Dynamic library

IPC APIs có thể nằm trong Axiom runtime library nhưng không bắt buộc external third-party runtime.

---

# 604.152 — OS dependency boundary

Allowed:

```text
Windows API
Linux syscalls/libc boundary khi target ABI yêu cầu
macOS system API
Android NDK/system API
iOS system API
WASI host API
```

Không allowed trong core:

```text
third-party IPC framework
third-party serialization runtime
mandatory external broker
```

---

# 604.153 — Public API

Core API tối thiểu:

```axiom
Endpoint
Channel
Message
Request
Response
Stream
Service
SharedRegion
SharedBuffer
Handle
Peer
Subscription
```

---

# 604.154 — Example service

```axiom
struct Calculator {
}

@ipc
@idempotent
fn add(self: Calculator, a: i64, b: i64) -> i64 {
    return a + b
}
```

---

# 604.155 — Example client

```axiom
client = ipc.connect("ipc://user/calculator")?

result = client.add(10, 20)?
```

Generated client có thể làm:

```text
encode
send
await response
decode
```

---

# 604.156 — Streaming example

```axiom
@ipc
@streaming
fn generate(self: Generator, input: Input) -> Stream<Chunk>
```

Client:

```axiom
stream = client.generate(input)?

while let chunk = stream.next()? {
    consume(chunk)
}
```

---

# 604.157 — Shared buffer example

```axiom
region = SharedRegion.create(16 * MB)?
buffer = region.slice(0, image_size)?

processor.process(buffer)?
```

Large payload không cần copy qua message envelope.

---

# 604.158 — Explicit transfer example

```axiom
client.send(
    message.with_handle(
        region.move()
    )
)?
```

Ownership transfer phải rõ ràng.

---

# 604.159 — Event example

```axiom
@event
struct FrameReady {
    frame_id: u64
}
```

Client:

```axiom
subscription = client.subscribe<FrameReady>()?
```

---

# 604.160 — Backpressure example

```axiom
channel.send(message, .await_capacity)?
```

hoặc:

```axiom
channel.send(message, .fail_if_full)?
```

---

# 604.161 — Timeout example

```axiom
client.call(request)
    .deadline(500ms)
```

---

# 604.162 — Cancellation example

```axiom
request = client.begin(request)?
request.cancel()
```

---

# 604.163 — Endpoint policy example

Deployment/configuration:

```text
endpoint: ipc://user/image
allow:
    image-client
methods:
    resize
    convert
deny:
    raw-memory
```

Policy parser phải declarative.

---

# 604.164 — No dynamic scripting in IPC policy

IPC/security configuration không được chạy arbitrary code.

---

# 604.165 — Service lifecycle

Service registration lifecycle:

```text
Created
Starting
Ready
Stopping
Stopped
Failed
```

Lifecycle orchestration thuộc task process supervision kế tiếp.

IPC chỉ expose state.

---

# 604.166 — Health

Endpoint có thể report:

```text
Healthy
Degraded
Unavailable
```

Không IPC tự quyết định health business logic.

---

# 604.167 — Graceful shutdown

Shutdown:

```text
stop accepting new requests
↓
finish allowed requests
↓
close streams
↓
release shared resources
↓
close transport
```

Deadline giới hạn graceful shutdown.

---

# 604.168 — Abort shutdown

Nếu deadline hết:

```text
Abort
```

Pending requests nhận lỗi.

---

# 604.169 — Resource cleanup

IPC resource cleanup phải idempotent.

Gọi:

```axiom
close()
close()
```

không crash.

---

# 604.170 — Handle close race

Nếu close xảy ra đồng thời send:

```text
send → success
```

hoặc:

```text
send → Closed
```

Không undefined behavior.

---

# 604.171 — Message immutability

Sau khi message được enqueue, payload mặc định immutable.

Nếu cần mutation:

```text
mutable buffer
```

phải explicit.

---

# 604.172 — Avoid hidden copies

Compiler/runtime không được âm thầm copy large `SharedBuffer`.

Move semantics phải được giữ qua generated client/server boundary.

---

# 604.173 — Borrowed message

Receiver có thể đọc payload trực tiếp từ receive buffer trong lifetime:

```axiom
fn handle(msg: Borrowed<Message>)
```

Sau callback lifetime, borrowed data invalid.

---

# 604.174 — Message ownership

API phải phân biệt:

```text
Owned<Message>
Borrowed<Message>
Shared<Message>
```

Không dựa vào implicit pointer semantics.

---

# 604.175 — Security and zero-copy

Zero-copy không được bypass security validation.

Flow:

```text
validate descriptor
↓
authorize region
↓
map region
↓
expose buffer
```

---

# 604.176 — Memory mapping limits

Một peer không được map region vượt quá capability/quota.

---

# 604.177 — Region revocation

Nếu region bị revoke:

```text
new access → denied
```

Existing mapping behavior phụ thuộc platform nhưng runtime phải chuyển resource vào trạng thái invalid/revoked an toàn.

---

# 604.178 — Shared-memory cleanup after crash

OS-backed shared memory phải có ownership mechanism để cleanup hoặc reclaim khi owner process chết.

---

# 604.179 — Orphan handling

Orphaned region:

```text
OwnerDead
```

có thể:

- reclaim;
- transfer ownership;
- retain until explicit cleanup.

Policy phải deterministic.

---

# 604.180 — Cross-platform semantic contract

Platform adapters có thể khác nhau về primitive nhưng application semantics phải nhất quán ở các phần core:

```text
message ordering
bounds safety
capability checking
timeouts
cancellation
resource limits
lifetime
```

---

# 604.181 — Platform feature degradation

Nếu platform không hỗ trợ zero-copy:

```text
ZeroCopy unavailable
```

runtime có thể fallback:

```text
Copy
```

nhưng phải expose capability/feature state.

---

# 604.182 — Explicit capability query

Application có thể hỏi:

```axiom
transport.features()
```

Ví dụ:

```text
ZERO_COPY
HANDLE_TRANSFER
SHARED_MEMORY
```

---

# 604.183 — No silent semantic downgrade

Nếu application yêu cầu bắt buộc:

```axiom
require(ZERO_COPY)
```

và transport không hỗ trợ:

```text
UnsupportedFeature
```

Không âm thầm copy.

---

# 604.184 — Transport selection

Runtime selection order:

```text
explicit transport
↓
endpoint policy
↓
platform preferred transport
↓
fallback transport
```

---

# 604.185 — Transport fingerprint

Diagnostics có thể ghi:

```text
transport_id
transport_version
feature_flags
```

để reproduce performance/failure.

---

# 604.186 — Protocol version

Protocol có version độc lập với Axiom compiler version.

Ví dụ:

```text
AXIPC/5
```

Compiler update không bắt buộc thay IPC protocol.

---

# 604.187 — Schema version

Schema version độc lập:

```text
Service version
Protocol version
Schema version
```

Không gộp thành một số version duy nhất.

---

# 604.188 — Compatibility matrix

Tooling phải có thể sinh:

```text
client schema
server schema
compatible?
```

---

# 604.189 — Rolling deployment

Cho phép:

```text
Client v2
    ↓
Server v1
```

nếu schema compatibility cho phép.

---

# 604.190 — Incompatible upgrade

Nếu không compatible:

```text
handshake reject
ProtocolMismatch
```

---

# 604.191 — Security versioning

Security policy version phải độc lập với wire schema.

---

# 604.192 — Auditability

IPC security events tích hợp BOOTSTRAP-603 audit stream.

---

# 604.193 — Privacy

Diagnostics mặc định không thu thập:

```text
message payload
file contents
secret values
personal data
```

trừ khi application explicit opt-in.

---

# 604.194 — Debug mode

Development build có thể bật verbose IPC diagnostics.

Production vẫn phải enforce secret/redaction policy.

---

# 604.195 — IPC inspector

Tooling có thể cung cấp:

```text
axiom ipc inspect
```

để xem:

```text
endpoints
services
connections
queue depth
schema
peer identity
capabilities
```

Sensitive data phải được redact.

---

# 604.196 — Trace capture

Có thể capture:

```text
connect
send
receive
response
disconnect
```

không capture payload mặc định.

---

# 604.197 — Replay testing

IPC event metadata có thể được replay trong loopback test.

Không replay arbitrary security credentials.

---

# 604.198 — Protocol fuzz corpus

Compiler project phải duy trì corpus:

```text
valid envelopes
invalid envelopes
boundary sizes
version combinations
schema mutations
```

---

# 604.199 — ABI test matrix

Test tối thiểu:

```text
x86_64
arm64
32-bit where supported
little-endian targets
different compiler builds
different schema versions
```

---

# 604.200 — Determinism

Generated schema IDs, method IDs, codec output và artifact metadata phải deterministic.

---

# 604.201 — Compiler integration

Compiler pipeline:

```text
parse
 ↓
semantic analysis
 ↓
IPC annotation analysis
 ↓
schema generation
 ↓
method ID generation
 ↓
codec generation
 ↓
security requirement generation
 ↓
IR
 ↓
native code
```

---

# 604.202 — IPC IR

Compiler IR có thể chứa:

```text
ipc.service
ipc.method
ipc.encode
ipc.decode
ipc.send
ipc.receive
ipc.shared_region
ipc.transfer_handle
ipc.authorize
```

---

# 604.203 — Security-aware IR

IR phải giữ metadata:

```text
required_capability
method_id
schema_id
max_payload
```

Linker không được làm mất security metadata trước khi final validation.

---

# 604.204 — Link-time validation

Linker kiểm tra:

```text
service IDs
method IDs
schema collisions
capability requirements
platform transport availability
```

---

# 604.205 — Dead stripping

Nếu executable không sử dụng:

```text
shared memory
streaming
service discovery
compression
```

thì module tương ứng phải có thể bị loại bỏ.

---

# 604.206 — Runtime initialization

IPC runtime không được khởi tạo toàn bộ stack khi application không sử dụng IPC.

Lazy initialization được ưu tiên.

---

# 604.207 — Static initialization

Không phụ thuộc vào thứ tự global constructor giữa modules.

IPC initialization phải explicit hoặc deterministic runtime bootstrap.

---

# 604.208 — Error propagation

Error chain:

```text
OS error
 ↓
TransportError
 ↓
IpcError
 ↓
Application error
```

Không expose OS error number làm API portable duy nhất.

---

# 604.209 — Native error retention

Diagnostic object có thể giữ:

```text
platform_error_code
```

nhưng application portable chỉ dựa trên `IpcError`.

---

# 604.210 — No hidden process spawning

`ipc.connect()` không được tự động spawn arbitrary process.

Service spawning thuộc process/service supervisor.

---

# 604.211 — Explicit activation

Có thể có higher-level:

```text
service.ensure_running()
```

nhưng phải đi qua process supervision/capability policy.

---

# 604.212 — Security boundary ordering

IPC operation phải tuân theo:

```text
parse endpoint
↓
resolve endpoint
↓
authenticate peer
↓
authorize capability
↓
negotiate protocol
↓
validate message
↓
dispatch
```

Không dispatch trước authorization.

---

# 604.213 — Malformed endpoint

Endpoint parsing không được truy cập OS resource trước khi validation hoàn tất.

---

# 604.214 — Endpoint canonicalization

Endpoint names phải canonicalized để tránh:

```text
alias collision
path traversal
namespace confusion
```

---

# 604.215 — Name squatting

Service registration phải chống service giả mạo bằng:

```text
identity
capability
namespace ownership
```

---

# 604.216 — Service ownership

User namespace service phải chứng minh quyền sở hữu namespace.

---

# 604.217 — System namespace

System endpoints chỉ dành cho privileged/system capability.

Application không được tự claim:

```text
ipc://system/*
```

---

# 604.218 — User namespace isolation

User A không mặc định thấy service riêng của User B.

---

# 604.219 — Process-local namespace

Process-local IPC không expose ra ngoài process.

---

# 604.220 — Namespace lifetime

Dynamic namespace tồn tại theo:

```text
process
user session
system
```

tùy declaration.

---

# 604.221 — Message priority

Có thể hỗ trợ priority:

```text
Critical
High
Normal
Low
```

nhưng priority không được bypass security/quota.

---

# 604.222 — Priority abuse protection

Peer không được tự đánh dấu mọi message là Critical để chiếm queue.

---

# 604.223 — Fairness

Scheduler/queue phải có fairness policy giữa peer.

Không để một peer độc chiếm worker pool.

---

# 604.224 — Connection limits

Default limits phải bounded.

Ví dụ conceptual:

```text
connections/process
inflight/process
queue bytes/process
```

Actual values là platform/config dependent.

---

# 604.225 — Worker limits

IPC không tạo unbounded worker threads.

---

# 604.226 — Queue memory accounting

Memory queue phải được charge cho owner/peer để quota enforcement.

---

# 604.227 — Shared memory accounting

Shared region phải tính vào process quota.

---

# 604.228 — Handle quota

Handle transfer phải có quota.

Ngăn handle exhaustion attack.

---

# 604.229 — Descriptor exhaustion

Transport phải xử lý OS descriptor exhaustion thành error có kiểm soát.

---

# 604.230 — Recovery from resource exhaustion

Khi queue/resource đầy:

```text
Backpressure
ResourceLimit
```

không crash process.

---

# 604.231 — Service overload

Server có thể trả:

```text
Busy
RetryAfter
```

nếu protocol hỗ trợ.

---

# 604.232 — Retry-after

Retry delay phải bounded và không được tạo retry storm.

---

# 604.233 — Connection storm protection

Service registration/discovery phải rate-limit hoặc quota khi cần.

---

# 604.234 — Cancellation propagation

Client cancel phải được propagate tới server khi transport hỗ trợ.

---

# 604.235 — Cancellation race

Nếu request hoàn thành trước cancel:

```text
Completed
```

Nếu cancel thắng:

```text
Cancelled
```

Semantics phải deterministic theo runtime event ordering.

---

# 604.236 — Stream cancellation

Stream cancel phải giải phóng:

- buffers;
- subscriptions;
- pending transport state;
- shared regions nếu owned.

---

# 604.237 — Stream half-close

Streaming transport có thể hỗ trợ:

```text
send_close
receive_close
```

cho half-duplex semantics.

---

# 604.238 — Duplex stream

Có thể có:

```text
Stream<TIn, TOut>
```

hai chiều.

---

# 604.239 — Message fragmentation

Transport có thể fragment large messages.

Application không thấy fragment.

---

# 604.240 — Reassembly limits

Reassembly phải bounded:

```text
max_message_size
max_fragments
max_reassembly_memory
```

---

# 604.241 — Partial read

Partial OS read không được expose như partial application message trừ streaming API.

---

# 604.242 — Atomic message boundary

Message transport phải preserve logical message boundaries.

---

# 604.243 — Batch send

API có thể hỗ trợ:

```axiom
channel.send_batch(messages)
```

để giảm syscall/context switch.

---

# 604.244 — Batch receive

Tương tự:

```axiom
channel.receive_batch()
```

---

# 604.245 — Scatter/gather

Large payload có thể sử dụng vectored I/O:

```text
header
payload1
payload2
```

tránh concatenate copy.

---

# 604.246 — Buffer chain

Message có thể chứa:

```text
BufferChain
```

thay vì contiguous allocation.

---

# 604.247 — Zero-copy condition

Zero-copy chỉ được claim nếu:

```text
source buffer
→ transport
→ receiver
```

không tạo payload copy.

Diagnostics nên expose actual path.

---

# 604.248 — Copy fallback visibility

Nếu zero-copy requested nhưng fallback copy xảy ra, runtime có thể report:

```text
TransportFallback
```

để benchmark chính xác.

---

# 604.249 — Performance counters

Có thể expose:

```text
copy_bytes
zero_copy_bytes
allocations
syscalls
```

development/diagnostics builds.

---

# 604.250 — IPC API stability

Public IPC API phải ổn định hơn implementation backend.

Platform-specific optimization có thể thay đổi mà không phá source API.

---

# 604.251 — Generic transport API

Application có thể viết:

```axiom
fn run<T: Transport>(transport: T)
```

nhưng service code nên phụ thuộc interface/service contract hơn backend.

---

# 604.252 — Dependency inversion

Service:

```text
Business logic
     ↓
IPC interface
     ↓
Transport
```

không:

```text
Business logic → WindowsNamedPipe
```

---

# 604.253 — Testing architecture

Mọi IPC service phải có thể test với:

```text
LoopbackTransport
FaultInjectingTransport
```

---

# 604.254 — FaultInjectingTransport

Test backend có thể inject:

```text
drop
delay
duplicate
reorder
corrupt
disconnect
timeout
```

nhưng semantics phải rõ ràng.

---

# 604.255 — Duplicate test

Duplicate request chỉ dùng để test idempotency/deduplication.

Không mặc định biến transport thành at-least-once system.

---

# 604.256 — Security fuzzing

Fuzz phải chạy dưới:

```text
minimal capability
```

để đảm bảo malformed IPC không escalate privilege.

---

# 604.257 — Privilege separation test

Test:

```text
low privilege client
high privilege service
```

và xác minh client không thể lấy capability ngoài policy.

---

# 604.258 — Capability non-escalation invariant

Nếu:

```text
C_child ⊆ C_parent
```

thì IPC transfer không được tạo:

```text
C_child ⊃ C_parent
```

---

# 604.259 — Handle confusion invariant

Handle generation/type phải ngăn:

```text
Handle<File> → Handle<Device>
```

và stale handle reuse.

---

# 604.260 — Memory safety invariant

Không có IPC API nào yêu cầu application truyền:

```text
raw pointer
unbounded pointer
foreign object address
```

qua process boundary.

---

# 604.261 — Resource safety invariant

Mọi externally controlled:

```text
length
count
offset
timeout
queue size
allocation size
```

đều phải bounded/validated.

---

# 604.262 — Security invariant

IPC không được trở thành đường bypass:

```text
BOOTSTRAP-603 capability policy
```

---

# 604.263 — Diagnostics invariant

IPC diagnostics không được phá:

```text
BOOTSTRAP-602 secret/privacy rules
```

---

# 604.264 — State invariant

IPC recovery không được restore raw OS handles từ checkpoint.

---

# 604.265 — Configuration invariant

IPC runtime chỉ đọc configuration snapshot hợp lệ từ BOOTSTRAP-601.

---

# 604.266 — Compatibility invariant

Wire schema phải độc lập với:

```text
compiler optimization
struct padding
native pointer size
```

---

# 604.267 — Performance invariant

IPC architecture không được bắt buộc:

```text
GC
global tracing
global lock
broker
heap allocation per message
thread per connection
```

---

# 604.268 — Minimal runtime path

Một simple RPC path lý tưởng:

```text
generated client
 ↓
encode inline
 ↓
transport send
 ↓
OS primitive
 ↓
transport receive
 ↓
decode inline
 ↓
generated server function
```

Không đi qua:

```text
reflection
dynamic dispatch registry
global broker
GC
```

trừ khi application chọn dynamic features.

---

# 604.269 — Dynamic service support

Dynamic services vẫn được hỗ trợ qua:

```text
ServiceRegistry
DynamicMessage
SchemaDescriptor
```

nhưng nằm trên static fast path.

---

# 604.270 — Static vs dynamic IPC

| Feature | Static IPC | Dynamic IPC |
|---|---|---|
| Schema | compile-time | runtime |
| Codec | generated | generic |
| Performance | highest | lower |
| Reflection | none | optional |
| ABI | stable | descriptor-driven |
| Use | production hot path | tooling/plugins |

---

# 604.271 — IPC plugin boundary

Plugin API nên ưu tiên:

```text
typed IPC
```

thay vì expose compiler/runtime internals.

---

# 604.272 — Plugin versioning

Plugin interface có:

```text
API version
schema version
capability requirements
```

---

# 604.273 — Service documentation generation

Compiler có thể generate:

```text
service API docs
schema docs
permission docs
compatibility metadata
```

từ cùng một source definition.

---

# 604.274 — Generated language bindings

Axiom-to-Axiom là primary.

Foreign bindings có thể được xây ở higher layer.

Core không phụ thuộc foreign language generator.

---

# 604.275 — C ABI adapter

Có thể tạo C-compatible IPC wrapper cho interoperability.

Nhưng C ABI không được trở thành native internal representation.

---

# 604.276 — Foreign process

External process không phải Axiom có thể giao tiếp thông qua:

```text
C ABI
defined wire protocol
standard socket/pipe adapter
```

---

# 604.277 — Protocol openness

Wire protocol documentation phải đủ để external implementation có thể implement mà không cần Axiom compiler.

---

# 604.278 — Versioned protocol documentation

Protocol specification phải version-controlled.

---

# 604.279 — Security disclosure

Protocol documentation phải mô tả:

```text
trust boundary
authentication
authorization
resource limits
malformed message behavior
```

---

# 604.280 — IPC threat model

Threats tối thiểu:

```text
unauthorized connection
message forgery
capability theft
handle confusion
resource exhaustion
malformed serialization
replay
service spoofing
shared memory corruption
information leakage
```

---

# 604.281 — Threat mitigation

Architecture phải map:

```text
Threat
→ Boundary
→ Capability
→ Validation
→ Quota
→ Audit
```

---

# 604.282 — Service spoofing protection

Identity của service phải được verify thông qua platform/security policy.

Không tin service name đơn thuần.

---

# 604.283 — Capability authenticity

Capability token phải opaque và unforgeable theo BOOTSTRAP-603.

---

# 604.284 — Shared-memory authorization

Map shared region phải kiểm tra capability tại thời điểm authorization.

---

# 604.285 — Shared-memory schema trust

Receiver không tin schema descriptor do peer cung cấp nếu descriptor không được authenticated/validated theo policy.

---

# 604.286 — Resource cleanup invariant

Mọi IPC resource phải có ownership rõ:

```text
owner
borrower
shared
transferred
```

---

# 604.287 — No hidden ownership

IPC API không được âm thầm giữ reference indefinitely.

---

# 604.288 — Explicit subscription lifetime

Subscription phải implement:

```axiom
subscription.close()
```

và scope-based cleanup nếu language runtime hỗ trợ.

---

# 604.289 — Scope cleanup

Ví dụ:

```axiom
scope {
    sub = client.subscribe<Event>()?
    ...
}
```

khi scope kết thúc:

```text
subscription closed
```

không cần GC.

---

# 604.290 — Async cleanup

Async task cancellation phải release:

```text
channel
request
stream
subscription
buffer
```

---

# 604.291 — Runtime shutdown ordering

Shutdown order:

```text
stop new connections
↓
stop new requests
↓
cancel/finish tasks
↓
release subscriptions
↓
release buffers
↓
close channels
↓
close endpoints
↓
shutdown transport
```

---

# 604.292 — Global runtime shutdown

Không được assume destructor ordering giữa arbitrary modules.

Shutdown manager phải explicit.

---

# 604.293 — Process crash semantics

Nếu peer crash:

```text
transport disconnected
pending operations failed
owned resources reclaimed by OS
shared resources handled by owner policy
```

---

# 604.294 — Service restart semantics

Client có thể reconnect nhưng phải revalidate:

```text
identity
capability
schema
protocol
```

Không reuse blindly old security state.

---

# 604.295 — Security context refresh

Reconnect có thể tạo security context mới.

---

# 604.296 — Time source

Timeout sử dụng monotonic clock.

Timestamp trong logs sử dụng wall clock + monotonic correlation nếu cần.

---

# 604.297 — Clock skew

IPC local timeout không phụ thuộc clock synchronization.

---

# 604.298 — IPC event IDs

Event IDs phải deterministic và versioned.

---

# 604.299 — ABI compatibility test

Mỗi release phải kiểm tra:

```text
old client ↔ new server
new client ↔ old server
```

trong compatibility matrix được hỗ trợ.

---

# 604.300 — Minimum acceptance criteria

BOOTSTRAP-604 chỉ được coi là hoàn thành khi:

1. Có endpoint abstraction.
2. Có channel abstraction.
3. Có request/response.
4. Có one-way event.
5. Có streaming.
6. Có bounded queue.
7. Có backpressure.
8. Có timeout/deadline.
9. Có cancellation.
10. Có peer disconnect detection.
11. Có schema-based serialization.
12. Có schema versioning.
13. Có generated codec.
14. Có shared memory.
15. Có zero-copy large-buffer path.
16. Có typed handle.
17. Có capability transfer integration.
18. Có endpoint authorization.
19. Có peer identity abstraction.
20. Có platform transport abstraction.
21. Có Windows backend.
22. Có Linux backend.
23. Có macOS backend.
24. Có mobile adapter architecture.
25. Có WASM capability-limited adapter.
26. Không yêu cầu GC.
27. Không yêu cầu global borrow checker.
28. Không dùng raw pointer cross-process.
29. Có resource quotas.
30. Có malformed-input protection.
31. Có fuzz tests.
32. Có fault-injection tests.
33. Có race tests cho shared memory.
34. Có diagnostics integration.
35. Có state/recovery integration.
36. Có configuration integration.
37. Có security-policy integration.
38. Có deterministic schema artifacts.
39. Có compiler IR representation.
40. Có dead-stripping/module separation.
41. Có loopback transport.
42. Có compatibility checker.
43. Có performance benchmark.
44. Có explicit shutdown semantics.
45. Có protocol documentation.

---

# 604.301 — Core invariants

Axiom IPC phải giữ các invariant:

```text
No raw cross-process pointers
No implicit unbounded allocation
No implicit infinite queues
No implicit thread-per-connection
No mandatory broker
No mandatory GC
No capability escalation
No secret leakage through diagnostics
No unchecked deserialization
No fake exactly-once guarantee
No hidden ownership
No platform-specific ABI leakage
```

---

# 604.302 — Architectural boundary

BOOTSTRAP-604 chịu trách nhiệm:

```text
IPC
message transport
shared memory
handle transfer
service endpoint communication
```

Không chịu trách nhiệm trực tiếp về:

```text
process creation
process supervision
service restart policy
watchdogs
application lifecycle orchestration
distributed consensus
general networking
```

Các phần process/service lifecycle sẽ được xây ở task kế tiếp.

---

# 604.303 — Final architecture

Kiến trúc hoàn chỉnh:

```text
                 ┌──────────────────────────┐
                 │       Axiom App          │
                 └────────────┬─────────────┘
                              │
                     Typed Service API
                              │
                 ┌────────────▼─────────────┐
                 │      IPC Runtime         │
                 │                          │
                 │ RPC / Event / Stream     │
                 │ Message / Schema         │
                 │ Capability / Handle      │
                 └───────┬─────────┬────────┘
                         │         │
                ┌────────▼───┐ ┌───▼──────────┐
                │ Transport  │ │ SharedMemory │
                └──────┬─────┘ └──────┬──────┘
                       │               │
              ┌────────▼───────────────▼──────┐
              │       Platform Adapter        │
              └───────────────┬───────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │       Operating System   │
                 └──────────────────────────┘

Security → BOOTSTRAP-603
Diagnostics → BOOTSTRAP-602
Config → BOOTSTRAP-601
State/Recovery → BOOTSTRAP-600
```

---

# 604.304 — Design conclusion

BOOTSTRAP-604 biến IPC thành một **typed, capability-aware, schema-versioned, zero-copy-capable native subsystem** thay vì chỉ là wrapper quanh socket/pipe.

Đường đi tối ưu của Axiom là:

```text
typed API
   ↓
compile-time schema
   ↓
generated codec
   ↓
inline/small-message fast path
   ↓
native transport
```

và đối với dữ liệu lớn:

```text
typed buffer
   ↓
SharedRegion
   ↓
capability transfer
   ↓
zero-copy access
```

Điểm quan trọng là toàn bộ mô hình vẫn giữ nguyên triết lý của Axiom:

```text
explicit ownership
explicit capability
explicit lifetime
bounded resources
compile-time metadata
native performance
no mandatory GC
no raw cross-process pointers
```

---

# 604.305 — Task completion

**BOOTSTRAP-604 hoàn tất về mặt kiến trúc.**

IPC foundation hiện đã có đủ các primitive cần thiết để xây application/service architecture native trên Axiom.

## Next task

**BOOTSTRAP-605 — Native Application Process & Service Supervision, Lifecycle, Health, Watchdog & Recovery Runtime 5.0**

Phần tiếp theo sẽ xây lớp nằm **trên IPC** để quản lý:

```text
process creation
process groups
service lifecycle
startup ordering
shutdown ordering
health
watchdog
restart
crash recovery
dependency graph
resource supervision
service activation
graceful degradation
```

và đặc biệt sẽ nối trực tiếp:

```text
BOOTSTRAP-600  State/Recovery
       +
BOOTSTRAP-601  Configuration
       +
BOOTSTRAP-602  Diagnostics
       +
BOOTSTRAP-603  Security
       +
BOOTSTRAP-604  IPC
       ↓
BOOTSTRAP-605  Process/Service Supervision
```

:::