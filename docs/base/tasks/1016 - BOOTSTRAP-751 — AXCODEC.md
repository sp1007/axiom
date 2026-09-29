# BOOTSTRAP-751 — AXCODEC

**Namespace:** `AXCODEC`  
**Phase:** Axiom Civilization Runtime / Native Encoding, Serialization, Compression, Checksum & Framing Codec Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXCODEC` là tầng chịu trách nhiệm biến đổi giữa:

```text
structured Axiom values
        ↕
encoded representation
        ↕
bytes / text / frames
```

Nó cung cấp nền tảng native cho:

- text encoding/decoding;
- binary encoding/decoding;
- serialization/deserialization;
- schema;
- schema evolution;
- deterministic encoding;
- canonical encoding;
- framing codecs;
- compression/decompression;
- checksum;
- incremental streaming codec;
- zero-copy decoding;
- bounded decoding;
- compiler-generated codecs;
- codec pipelines;
- codec registry;
- codec diagnostics;
- deterministic simulation.

Mục tiêu kiến trúc quan trọng:

> **Không cần reflection runtime để serialize Axiom types.**

Compiler có thể sinh codec trực tiếp từ type information.

---

# 2. Vị trí trong Axiom

```text
                  AXAPPLICATION
                        │
                        ▼
                    AXTASK
                        │
                        ▼
                    AXSTREAM
                        │
                        ▼
                    AXCODEC
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      AXSTORAGE     AXNETWORK       AXIPC
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                    AXMEMORY
```

`AXCODEC` nằm **trên representation layer nhưng dưới application protocol**.

---

# 3. Boundary cực kỳ quan trọng

## AXCODEC sở hữu

- representation;
- encoding;
- decoding;
- serialization;
- deserialization;
- schema;
- schema version;
- binary layout;
- text encoding;
- framing codec;
- compression;
- checksum;
- codec state;
- codec limits;
- generated codec;
- codec pipeline.

## AXCODEC không sở hữu

### AXSTREAM

Sở hữu:

- stream;
- buffering;
- cursor;
- backpressure;
- stream lifecycle.

### AXIPC

Sở hữu:

- IPC message ABI;
- endpoint;
- channel;
- capability transfer.

AXCODEC có thể được IPC sử dụng để encode payload, nhưng không định nghĩa IPC message semantics.

### AXNETWORK

Sở hữu:

- protocol;
- TCP/UDP/QUIC;
- packet semantics;
- network state.

### AXSTORAGE

Sở hữu:

- filesystem;
- database/storage semantics;
- persistence consistency.

### AXSECURITY

Sở hữu:

- cryptographic authority;
- keys;
- authentication;
- authorization.

AXCODEC chỉ cung cấp representation primitives.

---

# 4. Serialization ≠ IPC ABI ≠ persistence format

Ba khái niệm phải tách biệt.

```text
Serialization
    ↓
biến value thành representation

IPC ABI
    ↓
quy định message giữa processes

Persistence format
    ↓
quy định dữ liệu được lưu lâu dài
```

Ví dụ:

```text
User
  ↓
AXCODEC
  ↓
binary representation
  ↓
AXIPC
```

AXCODEC không trở thành AXIPC.

---

# 5. Core object model

Các type nền:

```text
codec
encoder
decoder

codec_state
codec_options
codec_error

text_encoding
binary_format

schema
schema_id
schema_version

frame_codec
compression_codec
checksum_codec

codec_pipeline
codec_buffer

codec_registry
codec_profile
codec_trace
```

---

# 6. Codec abstraction

```text
codec<T>
```

conceptually:

```text
encode(T) -> bytes
decode(bytes) -> T
```

Nhưng implementation thực tế phải hỗ trợ incremental processing:

```text
encode_step()
decode_step()
finish()
reset()
```

---

# 7. Encoder

```text
encoder<T>
```

có state:

```text
READY
ENCODING
NEED_OUTPUT
DONE
ERROR
```

Encoder không bắt buộc tạo temporary byte array.

Có thể encode trực tiếp:

```text
T
 ↓
destination buffer
```

---

# 8. Decoder

```text
decoder<T>
```

state:

```text
READY
DECODING
NEED_INPUT
NEED_OUTPUT
DONE
ERROR
```

`NEED_INPUT` là trạng thái bình thường.

Không được coi:

```text
NEED_INPUT
```

là malformed data.

---

# 9. Incremental codec

Ví dụ input:

```text
chunk A
chunk B
chunk C
```

Decoder:

```text
A → NEED_INPUT
B → NEED_INPUT
C → VALUE_READY
```

Không yêu cầu toàn bộ payload nằm trong memory một lần.

---

# 10. Codec result

Core:

```text
codec_result<T> {
    state
    value
    consumed
    produced
    error
}
```

Ví dụ:

```text
state = NEED_INPUT
consumed = 1024
produced = 0
```

---

# 11. UTF-8

Axiom mặc định:

```text
UTF-8
```

`AXCODEC` phải có native implementation.

Không yêu cầu OS encoding API cho common UTF-8 path.

---

# 12. Text encoding baseline

Core encoding set:

```text
UTF8
UTF16
UTF32
ASCII
LATIN1
```

Platform-specific encoding có thể tồn tại dưới adapter.

Không biến legacy encoding thành default.

---

# 13. UTF-8 validation

Decoder phải reject:

- invalid byte sequence;
- overlong sequence;
- surrogate code point;
- invalid scalar value;
- truncated sequence khi `finish()`.

---

# 14. Malformed text policy

```text
STRICT
REPLACE
PRESERVE
```

### STRICT

Trả lỗi.

### REPLACE

Thay malformed sequence bằng replacement character.

### PRESERVE

Giữ raw byte information thông qua representation phù hợp.

Không silently discard bytes.

---

# 15. Unicode normalization

Normalization không được tự động gắn vào UTF-8 decoding.

Tách thành transform:

```text
UTF8 decode
    ↓
Unicode normalization
```

Các policy:

```text
NONE
NFC
NFD
NFKC
NFKD
```

---

# 16. Binary representation

AXCODEC hỗ trợ:

```text
FIXED
VARIABLE
TAGGED
TLV
VARINT
BIT_PACKED
LENGTH_PREFIXED
```

---

# 17. Fixed layout

Ví dụ conceptually:

```text
struct Header {
    u32 version
    u64 timestamp
    u16 flags
}
```

có thể encode thành:

```text
[u32][u64][u16]
```

Layout phải deterministic.

---

# 18. Endianness

Binary codec phải explicit:

```text
LITTLE
BIG
NATIVE
```

`NATIVE` không phù hợp với portable persistent format nếu muốn cross-platform stability.

---

# 19. Alignment

Codec phải phân biệt:

```text
logical alignment
physical alignment
```

Packed format có thể không có padding.

Native ABI layout không được mặc định đồng nhất với serialization layout.

---

# 20. Tagged fields

Ví dụ:

```text
field_id
field_type
field_length
field_value
```

Cho phép schema evolution tốt hơn fixed positional encoding.

---

# 21. Optional fields

Codec phải biểu diễn:

```text
optional<T>
```

mà không nhầm:

```text
absent
```

với:

```text
present(default(T))
```

---

# 22. Nullable vs optional

Nếu language có:

```text
optional<T>
```

và nullable/reference semantics khác nhau, codec phải giữ distinction.

Không tự động biến mọi null thành missing field.

---

# 23. Arrays

Hỗ trợ:

```text
fixed_array<T, N>
dynamic_array<T>
```

Representation có thể:

```text
[length][elements]
```

hoặc fixed count.

---

# 24. Maps

Map serialization phải định nghĩa ordering.

Hai mode:

```text
UNORDERED
CANONICAL_ORDERED
```

Canonical encoding phải sort key theo codec-defined ordering.

Không phụ thuộc iteration order của hash table.

---

# 25. Struct serialization

Compiler biết layout:

```text
struct User {
    id: u64
    name: string
    age: u32
}
```

và có thể sinh:

```text
encode_User()
decode_User()
```

Không cần runtime reflection.

---

# 26. Enum serialization

Enum phải có explicit representation:

```text
enum Color {
    Red
    Green
    Blue
}
```

Có thể encode:

```text
u8 discriminant
```

hoặc tagged representation.

Không để compiler version tự ý thay đổi persistent discriminant.

---

# 27. Numeric encoding

Integer:

```text
u8/u16/u32/u64/u128
i8/i16/i32/i64/i128
```

có thể:

```text
fixed-width
varint
zigzag
```

Float:

```text
f32
f64
```

phải định nghĩa binary representation rõ.

---

# 28. Floating-point policy

Canonical codec phải quyết định:

- NaN representation;
- signed zero;
- infinity;
- endian;
- bit-level canonicalization.

Ví dụ canonical mode có thể normalize NaN representation.

Không được để hai compiler/backend tạo canonical data khác nhau.

---

# 29. String representation

String codec có thể:

```text
[length][UTF8 bytes]
```

hoặc:

```text
[length][UTF16 units]
```

depending on codec.

Axiom language default vẫn là UTF-8.

---

# 30. Binary string

Nếu application cần raw bytes:

```text
bytes
```

không dùng:

```text
string
```

Codec phải phân biệt hai type.

---

# 31. Cyclic structures

Mặc định:

```text
cycles = forbidden
```

Nếu application cần graph:

```text
@codec(graph)
```

thì phải dùng explicit identity table.

Không tự động phát hiện cycle bằng expensive global runtime machinery.

---

# 32. Graph codec

Graph representation:

```text
object_id
reference_id
```

có thể encode:

```text
object table
+
edge table
```

Feature này không thuộc fast-path serialization mặc định.

---

# 33. Deterministic encoding

```text
encode_deterministic(value)
```

cùng:

```text
value
schema
codec version
options
```

phải cho cùng byte sequence.

Mục đích:

- build cache;
- hashing;
- reproducible artifacts;
- deterministic tests;
- replay;
- content addressing.

---

# 34. Canonical encoding

Canonical encoding mạnh hơn deterministic.

Mọi representation hợp lệ của cùng logical value được đưa về một representation duy nhất.

```text
logical value
      ↓
canonical codec
      ↓
one canonical byte sequence
```

---

# 35. Schema model

```text
schema {
    schema_id
    version
    type_name
    fields[]
    encoding
    options
}
```

`schema_id` phải stable.

Không dùng memory address hoặc compiler session ID.

---

# 36. Schema identity

Có thể tạo:

```text
schema_id = hash(
    canonical_schema_definition
)
```

Nhưng algorithm hash cụ thể phải thuộc hashing subsystem contract.

---

# 37. Schema version

Ví dụ:

```text
User v1
User v2
User v3
```

Decoder phải có policy:

```text
EXACT
BACKWARD_COMPATIBLE
FORWARD_COMPATIBLE
COMPATIBLE
CUSTOM_MIGRATOR
```

---

# 38. Schema evolution

Ví dụ v1:

```text
id
name
```

v2:

```text
id
name
email
```

Decoder v2 đọc v1:

```text
email = absent
```

nếu schema cho phép.

---

# 39. Removed fields

Field bị xóa không được tái sử dụng ID ngay lập tức.

Ví dụ:

```text
field 5 = old_email
```

không nên ngay lập tức gán:

```text
field 5 = salary
```

trong persistent schema.

---

# 40. Renaming fields

Rename:

```text
name → display_name
```

nên giữ:

```text
field_id
```

Không dựa vào string name làm identity chính.

---

# 41. Schema migration

Migration function:

```text
migrate_v1_to_v2()
```

là explicit code.

Không yêu cầu codec tự động suy luận mọi migration.

---

# 42. Compiler-generated codec

Axiom:

```text
@derive(codec)
struct User {
    id: u64
    name: string
    email: string
}
```

Compiler sinh:

```text
User.encode()
User.decode()
User.schema()
```

hoặc equivalent intrinsic.

---

# 43. Không reflection runtime

Generated code có thể conceptually:

```text
encode_User(value, output)
```

thay vì:

```text
runtime_reflect(value)
find_fields()
find_types()
```

Điều này giảm:

- metadata runtime;
- allocations;
- branch;
- lookup;
- startup cost.

---

# 44. Codec attributes

Baseline attributes:

```text
@derive(codec)
@codec(binary)
@codec(text)
@codec(tagged)
@codec(version = 2)
@codec(field_id = 7)
@codec(skip)
@codec(rename = "...")
```

Compiler phải validate attribute conflicts.

---

# 45. Compile-time schema

Compiler có thể emit:

```text
.schema
```

metadata cùng object/module artifact.

Schema metadata phục vụ:

- tooling;
- compatibility validation;
- AI tooling;
- migration;
- debugging.

Không cần load toàn bộ schema runtime nếu application không sử dụng.

---

# 46. Framing codec

Framing biến:

```text
byte stream
```

thành:

```text
frame stream
```

Core:

```text
frame_codec
```

Strategies:

```text
FIXED
DELIMITER
LENGTH_PREFIX
VARINT
CHUNKED
CUSTOM
```

---

# 47. Frame limits

Decoder luôn có:

```text
max_frame_size
```

và:

```text
max_total_decoded_bytes
```

để chống allocation abuse.

---

# 48. Incremental frame decoder

Ví dụ:

```text
input A
  ↓
header incomplete
  ↓
NEED_INPUT

input B
  ↓
header complete
  ↓
payload incomplete
  ↓
NEED_INPUT

input C
  ↓
FRAME_READY
```

Không cần concatenate toàn bộ input.

---

# 49. Compression codec

Core abstraction:

```text
compression_codec
```

API:

```text
compress()
decompress()

compress_step()
decompress_step()
finish()
reset()
```

Hỗ trợ streaming.

---

# 50. Compression independence

Compression algorithm không được hard-code vào AXSTREAM.

Pipeline:

```text
AXSTREAM
   ↓
AXCODEC
   ↓
compression codec
```

---

# 51. Native dependency rule

Do Axiom yêu cầu runtime độc lập third-party:

> Các codec chuẩn được chọn làm core runtime phải có implementation do Axiom sở hữu.

External codec có thể được sử dụng qua explicit plugin/FFI ABI nhưng không được trở thành dependency bắt buộc của compiler/runtime.

---

# 52. Compression profiles

Không cố định một algorithm duy nhất cho mọi workload.

Profiles:

```text
FAST
BALANCED
MAX_COMPRESSION
LOW_MEMORY
STREAMING
DETERMINISTIC
```

Algorithm capability phải được khai báo.

---

# 53. Compression bomb protection

Decoder phải giới hạn:

```text
compressed_size
expanded_size
expansion_ratio
memory_budget
nested_layers
```

Ví dụ:

```text
compressed = 1 MB
```

không có nghĩa:

```text
decoder được phép tự động tạo 100 GB
```

---

# 54. Nested compression

Pipeline:

```text
gzip
 ↓
gzip
 ↓
gzip
```

phải có:

```text
max_pipeline_depth
```

Không decode đệ quy vô hạn.

---

# 55. Checksum codec

Checksum non-cryptographic có thể cung cấp:

```text
CRC32C
CRC64
```

và các fast integrity hashes được chọn trong standard library.

Mục tiêu:

- corruption detection;
- frame integrity;
- storage verification;
- transport validation.

---

# 56. Cryptographic boundary

Cryptographic hash/signature/key management không thuộc codec core.

Pipeline có thể:

```text
data
 ↓
AXCODEC
 ↓
AXCRYPTO
```

hoặc:

```text
AXCRYPTO
 ↓
AXCODEC
```

tùy protocol.

---

# 57. Codec pipeline

Core:

```text
codec_pipeline
```

Ví dụ:

```text
struct
 ↓
binary encode
 ↓
compress
 ↓
checksum
 ↓
frame
 ↓
stream
```

Decode đảo ngược:

```text
stream
 ↓
frame
 ↓
checksum
 ↓
decompress
 ↓
binary decode
 ↓
struct
```

---

# 58. Pipeline ownership

Mỗi stage phải khai báo:

```text
input ownership
output ownership
buffering
state
limits
flush behavior
close behavior
```

Không để ownership trở thành implicit.

---

# 59. Pipeline fusion

Compiler/runtime có thể fuse:

```text
encode
 ↓
temporary buffer
 ↓
compress
```

thành:

```text
encode directly into compressor
```

nếu codec hỗ trợ streaming interface.

Mục tiêu:

> giảm intermediate buffer và memory copy.

---

# 60. Zero-copy decode

Nếu format cho phép, decoder có thể trả:

```text
string_view
bytes_view
array_view
```

trỏ trực tiếp vào encoded buffer.

Ví dụ:

```text
decode_view(buffer)
```

Không copy string/bytes.

---

# 61. Borrowed decoded values

Một decoded value có thể chứa:

```text
borrowed fields
```

gắn với lifetime của input buffer.

Axiom không cần borrow checker toàn ngôn ngữ để hỗ trợ feature này.

Codec API phải explicit:

```text
decode_owned()
decode_view()
```

---

# 62. Owned decode

```text
decode_owned()
```

luôn tạo representation độc lập với input.

Do đó:

```text
release(input_buffer)
```

sau decode vẫn hợp lệ.

---

# 63. View decode

```text
decode_view()
```

yêu cầu:

```text
input_buffer lifetime >= decoded_value lifetime
```

Contract này phải rõ ở type/API level.

---

# 64. Validation

Codec phải hỗ trợ:

```text
validate()
```

trước khi decode full object.

Có thể kiểm tra:

- length;
- field IDs;
- nesting;
- integer range;
- enum discriminant;
- UTF validity;
- frame bounds.

---

# 65. Resource limits

```text
codec_limits {
    max_input_bytes
    max_output_bytes
    max_string_length
    max_array_length
    max_map_entries
    max_nesting_depth
    max_object_count
    max_frame_size
    max_expansion
    max_alloc_bytes
}
```

Decoder phải propagate budget xuống nested codecs.

---

# 66. Integer overflow

Length arithmetic phải dùng checked arithmetic.

Không:

```text
length + header
```

nếu overflow có thể wrap.

Mọi size computation phải:

```text
checked_add
checked_mul
checked_align
```

trước allocation hoặc pointer arithmetic.

---

# 67. Recursion depth

Nested schema:

```text
A
 └─ B
     └─ C
         └─ ...
```

phải có:

```text
max_depth
```

Nếu vượt:

```text
CODEC_DEPTH_LIMIT
```

---

# 68. Unknown fields

Tagged decoder có policy:

```text
IGNORE
PRESERVE
REJECT
```

`PRESERVE` cho phép round-trip dữ liệu chưa biết.

---

# 69. Unknown enum values

Policy:

```text
REJECT
MAP_UNKNOWN
PRESERVE_RAW
```

Không mặc định map về enum đầu tiên.

---

# 70. Forward compatibility

Một v1 decoder có thể gặp field v2.

Nếu schema policy cho phép:

```text
unknown field → skip
```

nhưng phải skip chính xác theo encoded length/type.

---

# 71. Backward compatibility

v2 decoder đọc v1:

```text
missing field
```

chỉ được default nếu schema khai báo default semantics.

Không tự ý gọi `default(T)` nếu semantics không cho phép.

---

# 72. Version-independent wire format

Schema version không nhất thiết phải được encode trong mọi message.

Có thể:

```text
external schema negotiation
```

hoặc:

```text
embedded version field
```

tùy protocol.

AXCODEC hỗ trợ cả hai.

---

# 73. Schema negotiation

Codec API có thể expose:

```text
schema_hash()
schema_id()
schema_version()
is_compatible()
```

Protocol layer quyết định cách negotiation.

---

# 74. Text codec

Text representations có thể gồm:

```text
UTF8
JSON-like
CSV-like
custom textual
```

Nhưng generic codec core không được biến một application format thành mandatory language runtime dependency.

---

# 75. Binary codec performance

Generated encoder phải hướng tới:

```text
no reflection
no per-field allocation
no dynamic dispatch
minimal branches
contiguous output
```

Với fixed format, compiler có thể generate trực tiếp:

```text
store
store
store
```

gần machine-code level.

---

# 76. Small-object fast path

Struct nhỏ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

có thể encode trực tiếp vào caller-provided stack/inline buffer.

Không allocation heap.

---

# 77. Large object path

Object lớn:

```text
large array
large string
large blob
```

sử dụng:

```text
AXMEMORY
```

và streaming encoder.

Không bắt buộc tạo một contiguous temporary byte array.

---

# 78. Direct-to-stream encoding

Cho phép:

```text
encode_to(stream, value)
```

flow:

```text
value
 ↓
generated encoder
 ↓
AXSTREAM
```

không cần:

```text
value
 ↓
huge temporary bytes
 ↓
stream
```

---

# 79. Direct-from-stream decoding

```text
decode_from(stream)
```

flow:

```text
AXSTREAM
 ↓
incremental decoder
 ↓
value
```

Decoder chỉ request số byte cần thiết.

---

# 80. Async codec

Codec itself không tạo scheduler.

Ví dụ:

```text
await decode_from_async(stream)
```

composition:

```text
AXTASK
  ↓
AXSTREAM
  ↓
AXASYNC
  ↓
AXCODEC
```

Codec chỉ cung cấp state machine.

---

# 81. Async pipeline

```text
network
 ↓
AXSTREAM
 ↓
frame decoder
 ↓
decompressor
 ↓
generated decoder
 ↓
task
```

Mỗi stage xử lý incrementally.

---

# 82. Checksum placement

Checksum có thể đặt:

```text
payload
checksum
```

hoặc:

```text
frame {
    header
    payload
    checksum
}
```

AXCODEC không tự quyết định protocol layout nếu application protocol đã quy định.

---

# 83. Error taxonomy

Stable codec errors:

```text
INVALID_INPUT
INVALID_UTF8
INVALID_ENCODING
INVALID_FIELD
UNKNOWN_FIELD
INVALID_ENUM
INVALID_LENGTH
OVERFLOW
UNEXPECTED_EOF
FRAME_TOO_LARGE
DEPTH_LIMIT
ALLOCATION_LIMIT
OUTPUT_LIMIT
SCHEMA_MISMATCH
VERSION_MISMATCH
CHECKSUM_MISMATCH
COMPRESSION_ERROR
UNSUPPORTED_CODEC
NEED_INPUT
NEED_OUTPUT
```

Kèm optional native/algorithm-specific detail.

---

# 84. Error position

Decoder error nên chứa:

```text
offset
field_path
schema_id
schema_version
codec_id
```

Ví dụ:

```text
offset = 1842
field = "user.address.zip"
error = INVALID_LENGTH
```

Điều này rất hữu ích cho AI/compiler tooling.

---

# 85. Field path

Nested error:

```text
users[17].profile.address.zip
```

phải có representation machine-readable.

Không chỉ tạo error string.

---

# 86. Diagnostics metadata

Codec trace có thể ghi:

```text
codec_enter
codec_exit
field_begin
field_end
frame_begin
frame_end
compression_begin
compression_end
error
```

Payload không capture mặc định.

---

# 87. Deterministic simulation

Simulation phải có:

```text
virtual input
virtual output
controlled chunking
controlled partial writes
controlled allocation limits
controlled malformed input
```

Cho phép fuzz/test generated codecs.

---

# 88. Fuzzing boundary

Compiler/runtime test framework có thể generate:

```text
valid values
boundary values
invalid byte sequences
truncated messages
oversized lengths
unknown fields
unknown enum values
deep nesting
```

Codec phải không crash process vì malformed input.

---

# 89. No hidden process termination

Malformed input:

```text
decode(untrusted_bytes)
```

chỉ được tạo:

```text
codec_error
```

Không được:

```text
panic process
abort process
undefined behavior
```

trừ explicit `unsafe` low-level codec implementation violation.

---

# 90. Codec registry

```text
codec_registry
```

có thể map:

```text
codec_id
→ codec implementation
```

Nhưng static/generated codec nên được ưu tiên khi type compile-time known.

Registry dynamic dành cho:

- plugins;
- tooling;
- configuration;
- generic applications.

---

# 91. Codec IDs

Codec ID phải stable:

```text
codec_id {
    namespace
    name
    version
}
```

Không dùng vtable pointer làm codec identity.

---

# 92. ABI

Core ABI:

```text
encoder_vtable
decoder_vtable
codec_descriptor
```

nhưng generated static codec không nhất thiết sử dụng vtable.

Static dispatch:

```text
compile time
```

Dynamic dispatch:

```text
runtime
```

cùng semantic contract.

---

# 93. Compiler IR integration

Compiler có thể tạo metadata:

```text
CodecIR {
    Type
    Encoding
    Fields
    FieldIDs
    Defaults
    Limits
    Version
}
```

Sau đó lower:

```text
CodecIR
 ↓
Axiom IR
 ↓
machine code
```

Không cần runtime reflection.

---

# 94. Compile-time validation

Compiler phải bắt lỗi:

```text
duplicate field ID
invalid field ID
unsupported type
recursive codec without graph annotation
conflicting attributes
invalid default
incompatible schema change
```

trước runtime.

---

# 95. Codec specialization

Compiler có thể specialize:

```text
encode_u32_le()
encode_fixed_array()
encode_struct()
```

và inline chúng.

Ví dụ:

```text
encode_User()
```

không cần generic dispatch nếu `User` known statically.

---

# 96. Build artifact metadata

Axiom object có thể chứa:

```text
codec schema metadata
```

để tooling biết:

```text
type
schema
version
codec
```

mà không cần source code.

Điều này phù hợp với mục tiêu **AI-friendly compiled artifacts** của Axiom.

---

# 97. AI integration

AI tooling có thể đọc:

```text
schema
codec metadata
trace
compatibility report
```

và hỗ trợ:

- generate adapters;
- detect schema incompatibility;
- explain decode failures;
- suggest migration code;
- analyze serialization size;
- identify unnecessary copies.

AI không được tự động bypass:

```text
security
authorization
input limits
```

---

# 98. Performance architecture

Fast path:

```text
typed value
 ↓
generated codec
 ↓
caller buffer
```

Không:

```text
reflection
 ↓
metadata lookup
 ↓
temporary object
 ↓
heap allocation
 ↓
generic serializer
```

Mục tiêu là serialization overhead tiến gần native memory copy/layout cost đối với fixed-layout formats.

---

# 99. Core native API

```text
create_encoder()
create_decoder()

encode()
decode()

encode_into()
decode_from()

step()
finish()
reset()

set_limits()
validate()

frame_encode()
frame_decode()

compress()
decompress()

compress_stream()
decompress_stream()

checksum()

create_pipeline()
destroy_pipeline()

register_codec()
lookup_codec()

schema_id()
schema_hash()
schema_version()
is_compatible()

canonical_encode()
deterministic_encode()

get_codec_stats()

start_codec_trace()
stop_codec_trace()

create_codec_simulation()
replay_codec_trace()
```

---

# 100. Canonical flow — binary struct

```text
Axiom struct
     │
     ▼
@derive(codec)
     │
     ▼
compiler generates encoder
     │
     ▼
encode_into(buffer)
     │
     ▼
bytes
```

Không reflection.

---

# 101. Canonical flow — schema evolution

```text
User v1
   │
   ▼
encoded bytes
   │
   ▼
User v2 decoder
   │
   ├── known fields
   ├── missing fields
   └── unknown fields
          │
          ▼
compatibility policy
          │
          ▼
User v2
```

---

# 102. Canonical flow — streaming frame

```text
AXSTREAM
   │
   ▼
frame decoder
   │
   ├── NEED_INPUT
   │
   ├── NEED_INPUT
   │
   └── FRAME_READY
          │
          ▼
      payload
```

---

# 103. Canonical flow — compression

```text
value
  ↓
generated encoder
  ↓
compression codec
  ↓
checksum
  ↓
frame
  ↓
AXSTREAM
```

---

# 104. Canonical flow — bounded untrusted decode

```text
untrusted stream
       │
       ▼
frame limit
       │
       ▼
length validation
       │
       ▼
allocation budget
       │
       ▼
nesting limit
       │
       ▼
schema validation
       │
       ▼
decode
```

Không allocate trước khi validate kích thước cần thiết.

---

# 105. Canonical flow — zero-copy

```text
encoded buffer
      │
      ▼
decode_view()
      │
      ├── string_view
      ├── bytes_view
      └── array_view
```

Input buffer phải sống đủ lâu.

---

# 106. Canonical flow — deterministic build metadata

```text
Axiom type
    ↓
canonical schema
    ↓
deterministic encoding
    ↓
hash/cache key
    ↓
build artifact
```

Cùng source/schema/options phải tạo representation ổn định.

---

# 107. Canonical flow — async

```text
await decode_from_async(stream)
            │
            ▼
        AXSTREAM
            │
            ▼
         AXASYNC
            │
            ▼
         input chunk
            │
            ▼
        AXCODEC step
            │
       ┌────┴────┐
       ▼         ▼
 NEED_INPUT    VALUE
       │         │
       ▼         ▼
  next I/O      task
```

---

# 108. Formal invariants

### CODEC-INV-01
Codec state luôn thuộc state machine hợp lệ.

### CODEC-INV-02
`NEED_INPUT` không phải lỗi.

### CODEC-INV-03
`NEED_OUTPUT` không phải lỗi.

### CODEC-INV-04
Encoder không được silently discard output.

### CODEC-INV-05
Decoder không được đọc quá input boundary.

### CODEC-INV-06
Mọi length arithmetic phải overflow-safe.

### CODEC-INV-07
Mọi untrusted decode phải có resource limits.

### CODEC-INV-08
Frame decoder phải có maximum frame size.

### CODEC-INV-09
Nested decoding phải có depth limit.

### CODEC-INV-10
Allocation phải nằm trong configured budget.

### CODEC-INV-11
EOF giữa object phải trả `UNEXPECTED_EOF`.

### CODEC-INV-12
Malformed input không được biến thành EOF.

### CODEC-INV-13
Malformed UTF-8 phải tuân theo explicit policy.

### CODEC-INV-14
UTF-8 là default text encoding.

### CODEC-INV-15
Binary endian phải deterministic khi format yêu cầu portability.

### CODEC-INV-16
Native ABI layout không mặc định là serialization layout.

### CODEC-INV-17
Optional field absent khác present-default.

### CODEC-INV-18
Unknown fields phải tuân schema policy.

### CODEC-INV-19
Unknown enum values phải tuân schema policy.

### CODEC-INV-20
Persistent field IDs không được tự ý tái sử dụng.

### CODEC-INV-21
Schema identity phải stable.

### CODEC-INV-22
Deterministic encoding cùng input/schema/options phải cho cùng representation.

### CODEC-INV-23
Canonical encoding không phụ thuộc hash-table iteration order.

### CODEC-INV-24
Generated codec không yêu cầu runtime reflection.

### CODEC-INV-25
Generated static codec không bắt buộc dynamic dispatch.

### CODEC-INV-26
View decode phải khai báo backing-buffer lifetime contract.

### CODEC-INV-27
Owned decode không phụ thuộc lifetime input buffer.

### CODEC-INV-28
Graph/cycle codec phải explicit.

### CODEC-INV-29
Compression decoder phải có expansion limits.

### CODEC-INV-30
Nested compression phải có depth limit.

### CODEC-INV-31
Checksum mismatch không được trả success.

### CODEC-INV-32
Codec không tự tạo security authority.

### CODEC-INV-33
Codec không được bypass AXSECURITY policy.

### CODEC-INV-34
AXCODEC không sở hữu IPC message semantics.

### CODEC-INV-35
AXCODEC không sở hữu network protocol semantics.

### CODEC-INV-36
AXCODEC không sở hữu filesystem/persistence semantics.

### CODEC-INV-37
Codec hot path không bắt buộc heap allocation.

### CODEC-INV-38
Incremental codec phải giữ state qua chunk boundaries.

### CODEC-INV-39
Simulation/fault injection không active trong production mặc định.

### CODEC-INV-40
`AXCODEC 5.0` phải duy trì semantic contract độc lập với stream, storage, network và IPC backend.

---

# 109. Definition of Done

`AXCODEC 5.0` hoàn tất khi có:

- text codec;
- UTF-8 native implementation;
- UTF-16/UTF-32;
- binary fixed format;
- variable format;
- tagged/TLV format;
- varint;
- bit-packed format;
- endian handling;
- deterministic encoding;
- canonical encoding;
- schema;
- schema ID;
- schema version;
- compatibility checking;
- migration hooks;
- optional fields;
- arrays;
- maps;
- structs;
- enums;
- numeric types;
- strings;
- bytes;
- explicit graph codec;
- incremental encoder;
- incremental decoder;
- zero-copy view decode;
- owned decode;
- frame codec;
- compression abstraction;
- streaming compression;
- checksum abstraction;
- resource limits;
- overflow protection;
- recursion limits;
- compiler-generated codecs;
- compile-time schema validation;
- codec IR;
- artifact metadata;
- direct-to-stream encoding;
- direct-from-stream decoding;
- async integration;
- codec pipelines;
- tracing;
- deterministic simulation;
- fuzzing contract;
- stable errors;
- dynamic codec registry;
- native ABI;
- cross-platform contract;
- 40 invariants.

**AXCODEC 5.0 → FROZEN.**

---

# 110. Kiến trúc sau BOOTSTRAP-751

Pipeline hiện tại trở nên rất rõ:

```text
Axiom Type
    │
    ▼
Compiler
    │
    ├──────────────► Native Machine Code
    │
    └──────────────► Generated Codec
                          │
                          ▼
                       AXCODEC
                          │
                          ▼
                       AXSTREAM
                          │
                ┌─────────┼─────────┐
                ▼         ▼         ▼
            AXSTORAGE AXNETWORK  AXIPC
```

Điểm quan trọng là **codec được compiler sinh ra**, thay vì xây một serializer reflection-heavy ở runtime. Điều này phù hợp trực tiếp với mục tiêu hiệu năng và binary nhỏ của Axiom.

---

# BOOTSTRAP-752 — AXCRYPTO

**Native Cryptography, Hashing, Key Material, Secure Randomness, Signatures, MAC, KDF, AEAD, Certificate/Trust Primitives & Cryptographic Runtime 5.0**

Task tiếp theo sẽ tách hoàn toàn **cryptographic primitives** khỏi `AXSECURITY`, để:

```text
AXCODEC
   │
   ├── checksum / representation
   │
   ▼
AXCRYPTO
   │
   ├── hash
   ├── MAC
   ├── KDF
   ├── AEAD
   ├── signature
   ├── key material
   └── secure randomness
   │
   ▼
AXSECURITY
   │
   ├── identity
   ├── authorization
   ├── capabilities
   └── policy
```

Qua đó Axiom sẽ có distinction rõ giữa **thuật toán mật mã**, **vật liệu khóa**, và **quyền/security policy** thay vì gom toàn bộ vào một runtime module.