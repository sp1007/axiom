# BOOTSTRAP-750 — AXSTREAM

**Namespace:** `AXSTREAM`  
**Phase:** Axiom Civilization Runtime / Native Unified Stream Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXSTREAM` là tầng abstraction cao hơn `AXASYNC`, cung cấp một mô hình thống nhất cho các luồng dữ liệu:

- byte stream;
- text stream;
- message stream;
- synchronous stream;
- asynchronous stream;
- buffered/unbuffered I/O;
- read/write cursor;
- seeking;
- EOF;
- framing;
- line processing;
- encoding/decoding;
- backpressure;
- zero-copy;
- ownership transfer;
- duplex stream;
- half-close;
- stream composition;
- stream filters;
- stream pipelines;
- timeout/deadline;
- cancellation;
- tracing;
- deterministic simulation.

Mục tiêu quan trọng:

> Application code không cần biết dữ liệu phía dưới đến từ file, socket, pipe, IPC hay device nếu chỉ quan tâm đến **stream semantics**.

---

# 2. Vị trí kiến trúc

```text
                    APPLICATION
                         │
                         ▼
                     AXSTREAM
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      AXSTORAGE      AXNETWORK         AXIPC
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                      AXASYNC
                         │
                         ▼
                      AXMEMORY
                         │
                         ▼
                    OS / DEVICE
```

`AXSTREAM` không thay thế các subsystem phía dưới.

---

# 3. Boundary

## AXSTREAM sở hữu

- stream abstraction;
- read/write semantics;
- buffering;
- cursor;
- EOF;
- partial read/write;
- stream state;
- framing;
- text stream;
- stream encoding;
- stream composition;
- backpressure;
- duplex/half-close;
- stream cancellation;
- stream deadline;
- zero-copy views;
- stream adapters;
- stream pipeline;
- stream tracing;
- stream simulation.

## Không sở hữu

### AXASYNC

- OS completion;
- poller;
- I/O operation;
- completion queue;
- registered I/O buffer.

### AXSTORAGE

- file system;
- file metadata;
- persistence semantics.

### AXNETWORK

- socket;
- TCP/UDP/QUIC;
- protocol.

### AXIPC

- message ABI;
- endpoint;
- channel;
- capability transfer.

### AXMEMORY

- allocation;
- virtual memory;
- buffer lifetime primitives.

### AXCODEC

- serialization;
- compression;
- general encoding/decoding algorithms.

---

# 4. Core stream model

Stream là:

> một ordered sequence của dữ liệu có trạng thái đọc/ghi và lifetime xác định.

Không giả định stream luôn là byte.

Có ba loại chính:

```text
byte_stream
text_stream
message_stream
```

---

# 5. Byte stream

```text
byte_stream
```

là sequence:

```text
u8 → u8 → u8 → ...
```

API cơ bản:

```text
read()
read_exact()
read_some()
write()
write_all()
flush()
close()
```

---

# 6. Text stream

```text
text_stream
```

là sequence của Unicode scalar/text units.

Mặc định:

```text
UTF-8
```

Encoding khác phải explicit.

Ví dụ:

```text
text_stream.from(byte_stream, UTF8)
```

---

# 7. Message stream

```text
message_stream<T>
```

là:

```text
T
T
T
T
...
```

Mỗi message là một logical unit.

`AXSTREAM` không định nghĩa message ABI của IPC.

Nó chỉ cung cấp stream abstraction cho message transport.

---

# 8. Stream interfaces

Canonical interface:

```text
stream {
    read(...)
    write(...)
    flush(...)
    close(...)
}
```

Capability interfaces:

```text
readable
writable
seekable
duplex
async_readable
async_writable
message_based
text_based
```

Không ép mọi stream implement tất cả operations.

---

# 9. Capability-based stream API

Ví dụ một network stream:

```text
readable
writable
duplex
async
```

nhưng có thể:

```text
not seekable
```

File stream:

```text
readable
writable
seekable
async
```

Compiler có thể reject:

```text
socket.seek(...)
```

ngay ở compile time nếu type không có `seekable`.

---

# 10. Stream lifecycle

```text
CREATED
   │
   ▼
OPEN
   │
   ├────► HALF_CLOSED_READ
   │
   ├────► HALF_CLOSED_WRITE
   │
   ▼
CLOSING
   │
   ▼
CLOSED
```

Ngoài ra:

```text
FAILED
CANCELLED
```

---

# 11. EOF

EOF là trạng thái riêng.

Không được nhầm:

```text
read() == 0
```

với:

```text
temporary no data
```

Đối với finite stream:

```text
EOF
```

có nghĩa:

> sẽ không còn dữ liệu nữa.

---

# 12. Async stream

```text
async_stream
```

API:

```text
read_async()
write_async()
flush_async()
close_async()
```

Implementation dựa trên:

```text
AXASYNC
+
AXTASK
```

---

# 13. Async lowering

Axiom:

```text
let data = await stream.read_async(buf)
```

Compiler hạ:

```text
AXTASK state machine
        │
        ▼
AXSTREAM operation
        │
        ▼
AXASYNC submission
        │
        ▼
suspend
        │
        ▼
completion
        │
        ▼
resume
```

---

# 14. Không block async worker

Invariant:

```text
await stream.read_async()
```

không được biến thành:

```text
blocking read()
```

trên worker thread.

Nếu backend chỉ hỗ trợ blocking:

```text
blocking executor
```

phải được sử dụng explicit.

---

# 15. Read semantics

`read()` có thể trả:

```text
0..requested
```

bytes.

Không giả định full read.

Ví dụ:

```text
requested = 8192
actual = 2731
```

vẫn là thành công hợp lệ.

---

# 16. `read_exact`

```text
read_exact(buffer)
```

có semantic:

> tiếp tục đọc cho đến khi buffer đầy hoặc stream kết thúc/lỗi.

Nếu EOF trước khi đủ:

```text
UNEXPECTED_EOF
```

---

# 17. Write semantics

`write()` có thể ghi:

```text
0..requested
```

bytes.

`write_all()` đảm bảo:

```text
all requested bytes
```

hoặc trả lỗi.

Không silently discard phần còn lại.

---

# 18. Flush

`flush()` có nghĩa:

> đẩy dữ liệu đang được buffer ở tầng stream xuống tầng kế tiếp theo contract của stream.

Không mặc định có nghĩa:

> dữ liệu đã được physically persisted to storage.

Đối với persistence:

```text
AXSTORAGE
```

mới quyết định semantic tương ứng.

---

# 19. Close

`close()` phải idempotent.

```text
close()
close()
close()
```

không tạo double-free hoặc undefined behavior.

Sau `CLOSED`:

```text
read
write
flush
```

phải trả:

```text
STREAM_CLOSED
```

trừ các operation explicitly được phép sau close.

---

# 20. Duplex stream

Một stream có:

```text
read side
write side
```

độc lập.

Có thể:

```text
shutdown_write()
```

nhưng vẫn:

```text
read()
```

được.

---

# 21. Half-close

States:

```text
OPEN
 ├── READ_OPEN
 └── WRITE_OPEN
```

Sau:

```text
shutdown_write()
```

thì:

```text
WRITE_CLOSED
READ_OPEN
```

Điều này quan trọng cho TCP-like protocols.

---

# 22. Cursor

Stream seekable có:

```text
stream_cursor
```

gồm:

```text
position
origin
limits
```

API:

```text
tell()
seek()
skip()
rewind()
```

---

# 23. Seek origin

```text
BEGIN
CURRENT
END
```

Không cho phép `END` trên stream không có known finite length.

---

# 24. Random access

Seekable stream hỗ trợ:

```text
read_at(offset)
write_at(offset)
```

Các operation này không nhất thiết thay đổi shared cursor.

Đây là distinction quan trọng cho concurrent file access.

---

# 25. Concurrent cursor semantics

Hai task:

```text
task A → read()
task B → read()
```

trên cùng cursor phải có semantic được xác định.

Không để:

```text
A/B race → undefined cursor position
```

Options:

```text
serialized cursor
independent cursor
read_at/write_at
```

---

# 26. Buffering

Các mode:

```text
UNBUFFERED
BUFFERED
READ_AHEAD
WRITE_BEHIND
RING_BUFFER
```

Application có thể chọn profile.

---

# 27. Buffered read

```text
application
     │
     ▼
read()
     │
     ▼
stream buffer
     │
     ▼
underlying source
```

Nếu buffer còn dữ liệu:

```text
no underlying I/O
```

được phép.

---

# 28. Read-ahead

Runtime có thể đọc trước:

```text
requested = 4 KB
prefetch = 64 KB
```

nếu profile cho phép.

Không được vượt:

```text
memory budget
security limit
stream bounds
```

---

# 29. Write-behind

Application:

```text
write(A)
write(B)
write(C)
```

có thể tạo:

```text
buffer = A+B+C
```

rồi submit một operation lớn.

`flush()` quyết định khi nào buffer phải được đẩy.

---

# 30. Ring buffer

High-throughput streams có thể dùng:

```text
ring_buffer
```

Ví dụ:

```text
producer
   ↓
┌─────────────────┐
│ ring buffer     │
└─────────────────┘
   ↓
consumer
```

Phù hợp:

- audio;
- video;
- network;
- telemetry;
- IPC;
- device streams.

---

# 31. Backpressure

Stream phải có flow control.

Nếu consumer chậm:

```text
producer
   ↓
buffer full
   ↓
BACKPRESSURE
```

Policy:

```text
BLOCK
ASYNC_WAIT
FAIL
THROTTLE
DROP
```

`DROP` chỉ hợp lệ nếu stream khai báo lossy semantics.

---

# 32. Không silently drop

Không được:

```text
write()
buffer full
→ silently discard
```

với:

- file;
- database;
- IPC command;
- ordinary network request.

---

# 33. Bounded stream

```text
bounded_stream(capacity)
```

phải có giới hạn rõ:

```text
max_bytes
max_messages
max_frames
```

Điều này đặc biệt quan trọng khi nhận dữ liệu không tin cậy.

---

# 34. Unbounded stream

Có thể hỗ trợ:

```text
unbounded_stream
```

nhưng runtime phải áp dụng:

```text
resource quota
```

Không có stream nào được phép tăng memory vô hạn ngoài policy.

---

# 35. Zero-copy

Stream có API:

```text
read_view()
peek()
consume()
```

Ví dụ:

```text
view = stream.peek()
```

trả:

```text
immutable byte span
```

không copy.

Sau:

```text
consume(n)
```

stream mới được phép tái sử dụng vùng buffer đó.

---

# 36. Ownership transfer

API có thể:

```text
read_owned_buffer()
```

và transfer ownership:

```text
stream → application
```

hoặc:

```text
application → stream
```

Không copy nếu backend hỗ trợ.

---

# 37. Buffer lifetime

View:

```text
stream_view
```

không được tồn tại sau khi underlying buffer bị recycle.

Compiler/debug runtime có thể kiểm tra lifetime trong mode phù hợp.

Production fast path không bắt buộc runtime tracking.

---

# 38. Framing

Byte stream vốn không có message boundary.

AXSTREAM cung cấp:

```text
frame
```

để biến:

```text
bytes...
```

thành:

```text
frame
frame
frame
```

Các framing strategy:

```text
FIXED_SIZE
DELIMITER
LENGTH_PREFIX
VARINT_LENGTH
CHUNKED
CUSTOM
```

---

# 39. Maximum frame size

Mọi frame decoder phải có:

```text
max_frame_size
```

Không được đọc:

```text
length = 0xFFFFFFFFFFFFFFFF
```

rồi allocate tương ứng.

---

# 40. Incremental framing

Decoder phải hỗ trợ partial input:

```text
input 1 → NEED_INPUT
input 2 → NEED_INPUT
input 3 → FRAME_READY
```

Không yêu cầu toàn bộ frame phải nằm trong một buffer.

---

# 41. Decoder state

Canonical state:

```text
NEED_INPUT
NEED_OUTPUT
PRODUCED
DONE
ERROR
```

Ví dụ:

```text
decode(input)
→ NEED_INPUT
```

là trạng thái bình thường, không phải error.

---

# 42. Delimiter framing

Ví dụ newline:

```text
frame1\n
frame2\n
frame3\n
```

Decoder phải hỗ trợ delimiter xuyên qua buffer boundary:

```text
buffer A: "hello"
buffer B: "\nworld"
```

vẫn tạo được:

```text
"hello"
```

---

# 43. Length-prefix framing

```text
[length][payload]
```

Length phải được validate trước khi allocation.

```text
if length > max_frame_size:
    FRAME_TOO_LARGE
```

---

# 44. Text line stream

API:

```text
read_line()
read_line_async()
write_line()
```

newline policy phải rõ:

```text
LF
CRLF
CR
ANY
```

Không silently thay đổi dữ liệu nếu mode raw.

---

# 45. UTF-8

UTF-8 là default.

Decoder phải xử lý:

- partial UTF-8 sequence;
- malformed sequence;
- overlong encoding;
- invalid scalar values.

Malformed policy:

```text
STRICT
REPLACE
PRESERVE_BYTES
```

---

# 46. Stateful decoding

Không giả định mỗi buffer là một text boundary.

Ví dụ một UTF-8 sequence có thể bị cắt:

```text
buffer A → first bytes
buffer B → remaining bytes
```

Decoder phải giữ state giữa các lần `decode()`.

---

# 47. Encoding separation

`AXSTREAM` cung cấp:

```text
text_stream
```

nhưng algorithm encoding/decoding phức tạp thuộc:

```text
AXCODEC
```

AXSTREAM chỉ compose chúng.

---

# 48. Stream filters

Một stream có thể tạo pipeline:

```text
source
  ↓
buffer
  ↓
decoder
  ↓
transform
  ↓
consumer
```

Ví dụ:

```text
file
 ↓
decompression
 ↓
UTF-8 decoder
 ↓
line reader
```

---

# 49. Pipeline

Core:

```text
stream_pipeline
```

Ví dụ:

```text
source
  → decompress
  → decode UTF8
  → frame
  → consumer
```

Mỗi stage có:

```text
input
output
state
limits
flush
close
```

---

# 50. Filter không được phá ownership

Nếu stage nhận ownership:

```text
take(buffer)
```

thì caller không được tiếp tục sử dụng buffer đó.

Nếu stage chỉ borrow:

```text
view(buffer)
```

thì lifetime phải được giữ đến khi operation hoàn tất.

---

# 51. Compression boundary

Compression là filter:

```text
source
  ↓
compressor
  ↓
stream
```

Không phải intrinsic semantic của byte stream.

Algorithm cụ thể được giao cho:

```text
AXCODEC
```

---

# 52. Checksum boundary

Có thể:

```text
stream
 ↓
checksum filter
 ↓
consumer
```

Nhưng hash/checksum implementation thuộc codec/crypto subsystem thích hợp.

---

# 53. Tee stream

```text
source
   ↓
  tee
 ┌─┴─┐
 ▼   ▼
A    B
```

Một input được đưa tới nhiều consumers.

Backpressure policy phải explicit:

```text
WAIT_ALL
DROP_SLOW_BRANCH
FAIL_ON_BRANCH
```

---

# 54. Merge stream

```text
A ─┐
B ─┼──► merge
C ─┘
```

Output ordering phải explicit:

```text
ARRIVAL_ORDER
SOURCE_ORDER
TIMESTAMP_ORDER
CUSTOM
```

Không giả định deterministic ordering nếu source concurrent.

---

# 55. Split stream

```text
stream
  │
  ▼
splitter
 ├── A
 ├── B
 └── C
```

Rule phân chia phải explicit:

```text
ROUND_ROBIN
HASH
KEY
CUSTOM
```

---

# 56. Duplex pipeline

Hỗ trợ:

```text
input pipeline
output pipeline
```

độc lập.

Ví dụ:

```text
network
 ↓
decrypt
 ↓
decode
 ↓
application
 ↓
encode
 ↓
compress
 ↓
network
```

---

# 57. Error propagation

Nếu stage:

```text
decompress
```

lỗi:

```text
INVALID_COMPRESSED_DATA
```

pipeline phải propagate error theo policy:

```text
FAIL_PIPELINE
CLOSE_DOWNSTREAM
CLOSE_UPSTREAM
RECOVER
```

Không được biến corruption thành EOF.

---

# 58. Cancellation

Stream operation có:

```text
stream_cancel_token
```

Có thể cancel:

```text
read
write
flush
frame decode
pipeline
```

Cancellation cuối cùng được thực hiện thông qua:

```text
AXASYNC
+
AXTASK
```

---

# 59. Deadline

Stream API hỗ trợ:

```text
read_until(deadline)
write_until(deadline)
flush_until(deadline)
```

Deadline sử dụng monotonic time.

---

# 60. Timeout vs cancellation

Hai khái niệm khác nhau:

```text
TIMEOUT
```

là deadline không đạt.

```text
CANCELLED
```

là caller/system yêu cầu dừng.

Không được map tất cả thành một error.

---

# 61. Async iterator

Stream có thể expose:

```text
async iterator<T>
```

Ví dụ:

```text
for await line in stream.lines():
    process(line)
```

Compiler hạ xuống:

```text
AXTASK
+
AXSTREAM
+
AXASYNC
```

Không tạo một task/thread cho mỗi item.

---

# 62. Message stream

```text
message_stream<T>
```

có:

```text
receive()
send()
receive_async()
send_async()
```

Nếu underlying source là IPC:

```text
AXIPC
```

giữ message ABI.

AXSTREAM chỉ cung cấp iteration/buffering/flow-control abstraction.

---

# 63. File adapter

```text
file.as_stream()
```

Semantics:

```text
AXSTORAGE
   ↓
AXSTREAM
   ↓
application
```

AXSTREAM không duplicate filesystem API.

---

# 64. Network adapter

```text
socket.as_stream()
```

cung cấp:

```text
byte_stream
```

nhưng không biến:

```text
TCP
```

thành application protocol.

---

# 65. IPC adapter

```text
channel.as_message_stream<T>()
```

Message type vẫn được kiểm soát bởi:

```text
AXIPC
```

---

# 66. Device adapter

Device có thể expose:

```text
byte_stream
message_stream
sample_stream<T>
```

depending on device semantics.

AXSTREAM không sở hữu device lifecycle.

---

# 67. Typed stream

Axiom có thể hỗ trợ:

```text
stream<T>
```

nhưng phải phân biệt:

```text
stream<T>
```

với:

```text
message_stream<T>
```

`stream<T>` có thể là logical typed sequence được codec chuyển thành byte representation.

---

# 68. Stream statistics

```text
stream_stats {
    bytes_read
    bytes_written
    reads
    writes

    partial_reads
    partial_writes

    buffer_hits
    buffer_misses

    flushes
    stalls
    backpressure_events

    peak_buffer_bytes
    latency
}
```

---

# 69. Tracing

Trace:

```text
open
read
write
flush
seek
frame
buffer
backpressure
cancel
deadline
close
error
```

Không ghi payload mặc định.

---

# 70. Deterministic simulation

`stream_simulation` có:

```text
virtual input
virtual output
virtual clock
latency
partial reads
partial writes
EOF
errors
backpressure
```

Cho phép test stream logic mà không cần real file/network.

---

# 71. Fault injection

Có thể mô phỏng:

```text
READ_ERROR
WRITE_ERROR
PARTIAL_READ
PARTIAL_WRITE
EOF
TIMEOUT
CANCEL
BUFFER_FULL
FRAME_TOO_LARGE
INVALID_ENCODING
```

Chỉ active trong test/simulation profile.

---

# 72. Security limits

Mọi untrusted stream phải có:

```text
max_bytes
max_frame_size
max_buffer
max_line_length
max_pipeline_depth
max_decode_depth
max_pending_operations
```

Không cho input kiểm soát memory usage vô hạn.

---

# 73. Resource budgets

Stream profile:

```text
stream_limits {
    max_buffer_bytes
    max_pending_bytes
    max_frame_size
    max_operations
    max_total_bytes
}
```

Có thể kế thừa quota từ `AXPROCESS`/`AXAPPLICATION`.

---

# 74. Stream ownership

Mỗi stream có owner rõ ràng.

Mô hình:

```text
OWNED
BORROWED
SHARED
TRANSFERRED
CLOSED
```

Không cần borrow checker toàn ngôn ngữ.

Chỉ stream API enforce các lifetime contract quan trọng.

---

# 75. Shared stream

Shared stream phải khai báo synchronization:

```text
SERIALIZED
MULTI_READER
MULTI_WRITER
FULL_DUPLEX_CONCURRENT
```

Không để concurrent writes tạo undefined byte ordering.

---

# 76. Performance fast path

Một byte stream đơn giản:

```text
read(buffer)
```

phải có khả năng hạ thành:

```text
inline wrapper
→ AXASYNC operation
→ native backend
```

không tạo hàng loạt abstraction objects.

---

# 77. Allocation policy

Không bắt buộc allocation cho:

```text
read
write
peek
consume
flush
```

Các object metadata nhỏ có thể nằm:

```text
stack
task frame
inline storage
operation slab
```

---

# 78. Compiler optimization

Compiler có thể:

- inline stream adapter;
- specialize static stream type;
- eliminate virtual dispatch;
- fuse filters;
- eliminate intermediate buffers;
- scalar-replace stream state;
- stack-allocate small stream objects;
- specialize fixed frame size;
- remove bounds checks sau khi chứng minh được giới hạn.

---

# 79. Static vs dynamic streams

Static:

```text
fn process<S: readable>(s: S)
```

cho phép monomorphization.

Dynamic:

```text
dyn readable
```

cho phép runtime polymorphism.

Không bắt buộc virtual dispatch trên hot path.

---

# 80. Stream ABI

Core ABI phải nhỏ:

```text
stream_vtable {
    read
    write
    flush
    close
    seek
}
```

Nhưng capability không có method thì pointer có thể `null` hoặc interface type khác.

Không ép một universal giant vtable.

---

# 81. Native API baseline

```text
create_stream()
open_stream()

read()
read_some()
read_exact()

write()
write_all()

flush()
close()

seek()
tell()
skip()
rewind()

read_at()
write_at()

peek()
consume()

shutdown_read()
shutdown_write()

read_async()
write_async()
flush_async()
close_async()

read_line()
write_line()

create_frame_decoder()
create_frame_encoder()

create_pipeline()
add_filter()
connect_stage()

create_tee()
create_merge()
create_split()

get_stream_stats()

start_stream_trace()
stop_stream_trace()

create_stream_simulation()
inject_stream_fault()
```

---

# 82. Canonical file flow

```text
AXSTORAGE
    │
    ▼
file
    │
    ▼
file.as_stream()
    │
    ▼
buffer
    │
    ▼
read_exact()
    │
    ▼
application
```

---

# 83. Canonical network flow

```text
AXNETWORK socket
       │
       ▼
socket.as_stream()
       │
       ▼
frame decoder
       │
       ▼
message
       │
       ▼
application
```

---

# 84. Canonical text flow

```text
file/socket
    ↓
byte_stream
    ↓
UTF-8 decoder
    ↓
text_stream
    ↓
read_line()
    ↓
application
```

---

# 85. Canonical compression flow

```text
source
  ↓
compressed byte stream
  ↓
AXCODEC decompressor
  ↓
AXSTREAM
  ↓
application
```

---

# 86. Canonical zero-copy flow

```text
AXMEMORY buffer
       ↓
AXASYNC read
       ↓
AXSTREAM peek()
       ↓
immutable view
       ↓
application
       ↓
consume()
```

Không copy payload.

---

# 87. Canonical backpressure flow

```text
producer
   ↓
stream buffer
   ↓
FULL
   ↓
await capacity
   ↓
consumer drains
   ↓
producer resumes
```

---

# 88. Canonical cancellation flow

```text
task
 │
 ▼
read_async()
 │
 ▼
AXASYNC operation
 │
 ├──── cancel
 │
 ▼
completion
 │
 ▼
AXTASK resume
```

---

# 89. Formal invariants

### STREAM-INV-01
Mỗi stream có lifecycle state hợp lệ.

### STREAM-INV-02
Closed stream không nhận ordinary I/O.

### STREAM-INV-03
`close()` idempotent.

### STREAM-INV-04
EOF khác temporary no-data.

### STREAM-INV-05
Partial read phải trả số byte thực tế.

### STREAM-INV-06
Partial write phải trả số byte thực tế.

### STREAM-INV-07
`read_exact()` không được coi partial success là complete.

### STREAM-INV-08
`write_all()` không được silently discard bytes.

### STREAM-INV-09
Flush không mặc định đồng nghĩa physical persistence.

### STREAM-INV-10
Seek chỉ tồn tại trên seekable stream.

### STREAM-INV-11
`read_at/write_at` không tự động thay đổi shared cursor.

### STREAM-INV-12
Concurrent cursor access phải có semantic xác định.

### STREAM-INV-13
Async stream operation không block async worker.

### STREAM-INV-14
Stream view không được tồn tại ngoài lifetime contract của backing buffer.

### STREAM-INV-15
Buffer ownership transfer phải explicit.

### STREAM-INV-16
Stream không được release buffer đang in-flight.

### STREAM-INV-17
Backpressure phải observable.

### STREAM-INV-18
Bounded stream không vượt configured capacity.

### STREAM-INV-19
Lossy stream phải explicit.

### STREAM-INV-20
Ordinary file/network/IPC data không được silently drop.

### STREAM-INV-21
Frame decoder phải có maximum frame size.

### STREAM-INV-22
Partial frame phải được hỗ trợ.

### STREAM-INV-23
Malformed frame không được biến thành EOF.

### STREAM-INV-24
Text decoder phải xử lý sequence xuyên buffer boundary.

### STREAM-INV-25
UTF-8 là default text encoding.

### STREAM-INV-26
Malformed text policy phải explicit.

### STREAM-INV-27
Filter pipeline phải giữ ownership semantics.

### STREAM-INV-28
Pipeline error phải propagate theo policy.

### STREAM-INV-29
Compression không thuộc byte-stream semantic core.

### STREAM-INV-30
IPC message ABI không thuộc AXSTREAM.

### STREAM-INV-31
Network protocol không thuộc AXSTREAM.

### STREAM-INV-32
Filesystem semantics không thuộc AXSTREAM.

### STREAM-INV-33
Security authority không được tạo bởi stream.

### STREAM-INV-34
Cancellation khác timeout.

### STREAM-INV-35
Deadline dùng monotonic clock.

### STREAM-INV-36
Trace mặc định không capture payload.

### STREAM-INV-37
Fault injection chỉ active dưới explicit diagnostic/test profile.

### STREAM-INV-38
Simulation không thay đổi production semantics.

### STREAM-INV-39
Stream abstraction không bắt buộc heap allocation trên hot path.

### STREAM-INV-40
AXSTREAM 5.0 phải duy trì semantic contract độc lập với backend.

---

# 90. Definition of Done

`AXSTREAM 5.0` hoàn tất khi có:

- byte stream;
- text stream;
- message stream;
- sync stream;
- async stream;
- capability interfaces;
- lifecycle;
- EOF;
- partial read/write;
- exact read/write;
- flush;
- close;
- cursor;
- seek;
- random access;
- buffering;
- read-ahead;
- write-behind;
- ring buffer;
- backpressure;
- bounded streams;
- zero-copy;
- ownership transfer;
- duplex;
- half-close;
- framing;
- incremental decoding;
- text encoding boundary;
- line streams;
- stream filters;
- pipelines;
- tee;
- merge;
- split;
- cancellation;
- deadlines;
- resource limits;
- file adapter;
- network adapter;
- IPC adapter;
- device adapter;
- async iterator;
- tracing;
- deterministic simulation;
- fault injection;
- compiler integration;
- native ABI;
- performance fast path;
- cross-platform semantics;
- 40 invariants.

**AXSTREAM 5.0 → FROZEN.**

---

# BOOTSTRAP-751 — AXCODEC

**Native Encoding, Serialization, Compression, Checksum & Framing Codec Runtime**

Mục tiêu tiếp theo là xây `AXCODEC` thành tầng codec độc lập với `AXSTREAM`: compiler-generated serialization, UTF/text codecs, binary layouts, schema/version evolution, deterministic/canonical encoding, compression, checksums, incremental encode/decode, bounded untrusted-input decoding, zero-copy decode và codec pipelines.

`AXCODEC` sẽ là lớp giúp Axiom có thể biến trực tiếp:

```text
Axiom Type
    ↓
Generated Codec
    ↓
bytes
    ↓
AXSTREAM / AXIPC / AXSTORAGE / AXNETWORK
```

mà **không cần reflection runtime và không cần third-party serialization runtime**.