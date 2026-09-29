# BOOTSTRAP-207 — Serialization, Compression, Binary Formats, IPC & Data Interchange

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 207:

> **Axiom phải phân biệt rõ giá trị trong bộ nhớ, dữ liệu trên wire, dữ liệu persistent và dữ liệu IPC, nhưng vẫn cho phép compiler tối ưu xuống zero-copy khi representation thực sự tương thích.**

Đây là tầng rất quan trọng vì Axiom hiện đã có:

```text
Memory
Storage
Network
Distributed Systems
IPC
GPU
FFI
```

Nếu không tách representation đúng, ngôn ngữ rất dễ rơi vào một trong hai cực:

- an toàn nhưng copy quá nhiều;
- zero-copy nhưng phá vỡ memory safety.

---

# 207.1. Bốn loại representation

Axiom khóa:

```text
Semantic Value
      │
      ├── Memory Representation
      │
      ├── Wire Representation
      │
      ├── Persistent Representation
      │
      └── IPC Representation
```

Không mặc định chúng giống nhau.

---

# 207.2. Semantic value ≠ bytes

Ví dụ:

```axiom
struct User {
    id: u64
    name: String
}
```

Không được mặc định:

```text
User == raw bytes
```

vì:

- `String` có ownership;
- representation có thể chứa pointer/metadata;
- field layout có thể được compiler reorder;
- padding không có semantic meaning.

---

# 207.3. Memory representation

Đây là representation phục vụ execution:

```text
size
alignment
field offsets
niches
padding
ABI
```

được quyết định bởi compiler trừ khi có `repr` contract.

---

# 207.4. Wire representation

Wire format phải có contract độc lập:

```text
endianness
field encoding
length encoding
alignment
version
optional fields
unknown fields
```

---

# 207.5. Persistent representation

Storage format có thêm:

```text
version
schema
checksums
page boundaries
migration
durability
compatibility
```

Không mặc định giống network wire format.

---

# 207.6. IPC representation

IPC có thể dùng:

```text
serialization
shared memory
mapped file
OS message
handle transfer
```

Tùy platform.

---

# 207.7. Serialization trait

Library có thể cung cấp:

```axiom
trait Serialize<Format> {
    fn encode(self: view<Self>, out: mut_view<Encoder<Format>>) -> Result<(), Error>
}
```

Conceptual semantics quan trọng hơn syntax cuối cùng.

---

# 207.8. Deserialize

```axiom
trait Deserialize<Format> {
    fn decode(input: mut_view<Decoder<Format>>) -> Result<Self, Error>
}
```

`Deserialize` tạo **giá trị mới có ownership hợp lệ**.

---

# 207.9. Serialization không implicit

Không cho compiler tự động:

```text
struct → JSON
```

trong mọi context.

Phải có:

- compiler-known derive;
- trait implementation;
- comptime generation;
- explicit schema.

---

# 207.10. `@derive(Serialize)`

Đây là trường hợp phù hợp với hệ thống `@derive` đã khóa:

```axiom
@derive(Serialize, Deserialize)
struct User {
    id: u64
    name: String
}
```

Compiler/comptime sinh code typed.

Generated code quay lại pipeline bình thường:

```text
Generated HIR
 → typecheck
 → ownership
 → capability
 → verification
```

---

# 207.11. Không dùng textual macro

Serialization generation không cần:

```text
generate string source
```

mà nên tạo typed declarations/HIR.

---

# 207.12. Schema

Schema là metadata mô tả data contract:

```text
Schema
 ├── fields
 ├── types
 ├── optionality
 ├── encoding
 └── version
```

---

# 207.13. SchemaFingerprint

Schema có fingerprint riêng:

```text
SchemaFingerprint
```

không dùng:

```text
SemanticFingerprint
```

hay:

```text
AbiFingerprint
```

thay thế.

---

# 207.14. Các fingerprint độc lập

Axiom hiện có:

```text
SemanticFingerprint
CodegenFingerprint
AbiFingerprint
SchemaFingerprint
StorageFormatFingerprint
```

Điều này rất quan trọng.

Thay đổi implementation không nhất thiết phá schema.

---

# 207.15. Field identity

Field serialization identity không nhất thiết phụ thuộc field position.

Ví dụ:

```text
id = 1
name = 2
email = 3
```

cho phép reorder field trong source mà không phá wire compatibility.

---

# 207.16. Field tags

Binary protocol có thể dùng:

```text
@field_id(1)
```

để giữ stable identity.

---

# 207.17. Schema evolution

Cho phép:

```text
v1
 ↓
v2
 ↓
v3
```

với:

- add field;
- remove deprecated field;
- rename bằng stable field ID;
- change representation khi có migration.

---

# 207.18. Unknown fields

Deserializer có thể:

```text
ignore
preserve
reject
```

unknown fields tùy schema policy.

---

# 207.19. Forward compatibility

Old reader gặp field mới:

```text
unknown field
```

có thể bỏ qua nếu protocol cho phép.

---

# 207.20. Backward compatibility

New reader phải có policy cho:

```text
missing field
```

Ví dụ:

```text
default
Option::None
migration
reject
```

---

# 207.21. Breaking schema changes

Thay đổi:

```text
u32 → String
```

không được tự coi là compatible chỉ vì compiler có thể cast.

Schema compatibility là một vấn đề riêng.

---

# 207.22. JSON

JSON là library format.

Không đưa JSON parser vào Core.

```text
JsonValue
JsonParser
JsonWriter
```

là standard library/application layer.

---

# 207.23. JSON zero-copy

JSON parsing có thể trả:

```text
Str
view<u8>
```

để tránh copy substring.

Nhưng backing input phải sống đủ lâu.

---

# 207.24. Binary formats

Axiom nên hỗ trợ framework cho:

```text
CBOR
MessagePack
Protobuf
FlatBuffers
Cap'n Proto
custom binary formats
```

chứ không khóa một format duy nhất vào language.

---

# 207.25. Length-prefixed format

Một primitive phổ biến:

```text
[length][payload]
```

Decoder phải kiểm tra:

```text
length <= remaining
```

trước khi tạo view.

---

# 207.26. Bounds validation

Không được:

```text
bytes[offset .. offset+length]
```

nếu chưa chứng minh:

```text
offset <= size
offset + length <= size
```

Compiler có thể eliminate bounds checks sau khi proof thành công.

---

# 207.27. Varint

Binary encoding có thể hỗ trợ:

```text
VarUInt
VarInt
```

với overflow semantics rõ ràng.

---

# 207.28. Integer encoding

Wire integer encoding độc lập với native integer representation.

Ví dụ:

```text
u32
```

có thể encoded:

```text
little-endian fixed32
big-endian fixed32
varint
```

---

# 207.29. Floating-point encoding

Float serialization phải định nghĩa:

- bit representation;
- NaN policy;
- infinity;
- signed zero;
- endian.

Không mặc định mọi format có cùng semantics.

---

# 207.30. String encoding

Wire string phải xác định:

```text
UTF-8
UTF-16
UTF-32
length + bytes
null terminated
```

Axiom mặc định UTF-8 cho text nhưng không ép mọi external protocol.

---

# 207.31. Bytes vs Text

Không implicit:

```text
Bytes → String
```

nếu bytes chưa được validate UTF-8.

Đã phù hợp với 169.

---

# 207.32. Zero-copy deserialization

Đây là tính năng quan trọng.

Có thể có:

```text
BorrowedMessage<'...>
```

về mặt semantic nhưng **programmer không phải viết lifetime**.

Ví dụ conceptual:

```text
input Buffer
      │
      ▼
BorrowedMessage
 ├── Str
 ├── view<u8>
 └── fields
```

Compiler theo dõi provenance.

---

# 207.33. Borrowed deserializer

Conceptual API:

```text
decode_view(input) -> Result<MessageView, Error>
```

`MessageView` không sở hữu input.

---

# 207.34. Owned deserializer

```text
decode(input) -> Result<Message, Error>
```

tạo data owned.

Programmer chọn semantics theo API.

---

# 207.35. No hidden copies

Nếu API trả borrowed view:

```text
decode_view()
```

compiler không được âm thầm clone toàn bộ message chỉ để làm lifetime dễ hơn.

Nếu cần owned result phải dùng API owned.

---

# 207.36. Zero-copy safety

Zero-copy chỉ được phép nếu compiler chứng minh:

```text
backing storage alive
region valid
alignment valid
representation valid
immutability valid
```

---

# 207.37. Zero-copy mutable deserialization

`mut_view` có thể được dùng để decode trực tiếp vào buffer:

```text
network buffer
 ↓
decode
 ↓
typed mutable view
```

nhưng chỉ khi representation contract cho phép.

---

# 207.38. In-place decoding

Có thể:

```text
decode_into(buffer, destination)
```

để tránh allocation.

---

# 207.39. In-place construction

Compiler có thể tối ưu:

```text
decode()
```

thành caller-provided destination nếu ABI/codegen cho phép.

Không cần programmer viết placement-new.

---

# 207.40. Flat representation

Một type có thể khai báo representation phù hợp wire format:

```axiom
@repr(wire("MyProtocol"))
struct Packet {
    ...
}
```

Đây phải là **representation contract**, không phải magic cast.

---

# 207.41. Wire-safe types

Compiler có thể xác minh:

```text
WireSafe<Format>
```

theo format contract.

Ví dụ:

```text
primitive
fixed array
repr-transparent type
wire-safe struct
```

---

# 207.42. Pointer-containing types

Type chứa:

```text
String
Vec
Box
raw pointer
```

không mặc định `WireSafe`.

---

# 207.43. Handle serialization

OS handle không được serialize như raw integer rồi coi như handle hợp lệ ở process khác.

Phải có explicit handle-transfer mechanism.

---

# 207.44. File descriptor passing

Unix có:

```text
SCM_RIGHTS
```

Windows có handle duplication.

Axiom API phải biểu diễn đây là:

```text
resource transfer
```

không phải:

```text
serialize(u64)
```

---

# 207.45. Shared memory

Shared memory:

```text
SharedMemory
```

là storage resource.

Typed access cần:

```text
layout contract
initialization contract
synchronization contract
process compatibility
```

---

# 207.46. Shared-memory type

Không được tự động đặt:

```text
struct Foo
```

vào shared memory rồi giả định process khác có thể dereference.

Pointers/provenance trong process A không hợp lệ ở process B.

---

# 207.47. Relative offsets

Shared memory có thể dùng:

```text
Offset
RelativePtr
```

sau khi validation.

Đây là một trường hợp system-level hợp lệ.

---

# 207.48. Shared-memory serialization

Một schema có thể dùng:

```text
offset-based representation
```

để đạt zero-copy IPC.

Nhưng phải có explicit ABI/schema contract.

---

# 207.49. IPC message

IPC message có thể dùng:

```text
copy
move
shared-memory reference
OS handle
```

tùy transport.

---

# 207.50. Compression

Compression là transformation:

```text
PlainData
 ↓
Compressor
 ↓
CompressedData
```

Không làm thay đổi semantic value.

---

# 207.51. Compression stream

Có:

```text
Encoder
Decoder
```

hỗ trợ streaming.

Không cần materialize toàn bộ input.

---

# 207.52. Compression algorithms

Standard library/framework có thể cung cấp:

```text
LZ4
Zstd
Deflate
Brotli
```

và platform/third-party implementations thông qua explicit package/FFI nếu cần.

Core không phụ thuộc bất kỳ compressor nào.

---

# 207.53. Compression level

Compression:

```text
Level
```

là performance policy.

Không thay đổi decoded semantics.

---

# 207.54. Compression dictionary

Có thể hỗ trợ:

```text
Dictionary
```

với explicit ownership/lifetime.

---

# 207.55. Compression + zero-copy

Không thể zero-copy xuyên qua một compression boundary theo nghĩa raw memory.

Nhưng có thể:

```text
stream
 ↓
decompress directly
 ↓
destination buffer
```

để tránh intermediate copy.

---

# 207.56. Chunked compression

Large data:

```text
chunk
 ↓
compress
 ↓
send
 ↓
decompress
 ↓
consume
```

không cần giữ toàn bộ dataset.

---

# 207.57. Checksum

Checksum:

```text
CRC32
CRC32C
xxHash
```

có mục tiêu phát hiện lỗi khác với cryptographic hash.

---

# 207.58. Hash

Hash:

```text
SHA-256
SHA-512
BLAKE3
```

có thể phục vụ:

- integrity;
- content addressing;
- identity;
- Merkle tree.

Không dùng hash làm encryption.

---

# 207.59. Authentication vs checksum

Phân biệt:

```text
Checksum
Hash
MAC
Digital Signature
```

---

# 207.60. Merkle tree

Merkle tree:

```text
             Root
           /      \
         H1        H2
        / \       / \
      H11 H12   H21 H22
```

là ordinary data structure.

Rất hữu ích cho:

- distributed storage;
- content addressing;
- deduplication;
- synchronization.

---

# 207.61. Content addressing

Có:

```text
ContentId
```

được tạo từ content hash.

Không phải memory address.

---

# 207.62. Content identity

Phân biệt:

```text
Memory Address
Storage Identity
Logical Identity
Content Identity
```

Axiom hiện có thể biểu diễn cả bốn mà không nhầm lẫn.

---

# 207.63. Canonical serialization

Một số protocol cần canonical encoding:

```text
same semantic value
       ↓
exact same bytes
```

Điều này cần explicit format contract.

---

# 207.64. Canonical map ordering

Nếu canonical format yêu cầu ordering, serializer phải deterministic.

Không phụ thuộc hash-map iteration order.

---

# 207.65. Serialization errors

Deserialize phải trả:

```text
Result<T, DecodeError>
```

Không panic khi input network/storage không hợp lệ.

---

# 207.66. Malformed input

Các lỗi:

```text
UnexpectedEOF
InvalidTag
InvalidLength
Overflow
InvalidUtf8
InvalidEnum
InvalidAlignment
UnsupportedVersion
ChecksumMismatch
```

là recoverable data errors.

---

# 207.67. Resource exhaustion

Decode phải bảo vệ:

```text
max depth
max length
max allocation
max fields
max nesting
```

để chống malicious input.

---

# 207.68. Allocation budget

Deserializer có thể nhận:

```text
DecodeLimits
```

Ví dụ:

```text
max_bytes
max_depth
max_items
```

---

# 207.69. Streaming limits

Streaming decoder không được giữ unbounded state chỉ vì input chưa kết thúc.

---

# 207.70. Recursive formats

Recursive structures cần giới hạn depth hoặc dùng explicit state machine.

---

# 207.71. Compression bombs

Compressed data có thể expand rất lớn.

API nên có:

```text
max_output
max_ratio
deadline
cancellation
```

policy.

---

# 207.72. Decompression cancellation

Async decompression phải hỗ trợ cancellation theo async semantics.

---

# 207.73. Serialization + async

Serializer có thể streaming trực tiếp:

```text
Serialize
 ↓
AsyncWriter
 ↓
Network
```

không cần intermediate giant `Vec<u8>`.

---

# 207.74. Serializer + storage

Tương tự:

```text
Object
 ↓
Serializer
 ↓
WAL/Page/File
```

có thể stream.

---

# 207.75. Serializer + GPU

GPU data transfer có thể dùng representation phù hợp:

```text
Host object
 ↓
GpuWire/Transfer format
 ↓
DeviceBuffer
```

nhưng GPU layout vẫn là contract riêng.

---

# 207.76. Binary schema generation

Comptime có thể sinh:

```text
encoder
decoder
schema descriptor
compatibility checker
```

từ Axiom types.

---

# 207.77. Schema migration generation

Có thể sinh:

```text
v1 → v2
v2 → v3
```

migration functions.

Nhưng migration vẫn phải được typecheck/verify bình thường.

---

# 207.78. Schema compatibility checker

Tooling:

```text
ax schema check
```

có thể phát hiện:

```text
field removed
type changed
tag reused
required field added
encoding changed
```

trước deployment.

---

# 207.79. Wire ABI

Wire contract có thể được coi là:

```text
public protocol ABI
```

nhưng không phải Axiom binary ABI.

---

# 207.80. Persistent format ABI

Database/storage format cũng có compatibility identity riêng:

```text
StorageFormatFingerprint
```

đã được khóa ở 203.

---

# 207.81. Version negotiation

Network protocol:

```text
client
 ↓
supported schema versions
 ↓
server
 ↓
selected version
```

---

# 207.82. Optional fields

Optionality phải phân biệt:

```text
field absent
field present with null
field present with default
```

Không tất cả format đều có `null`.

---

# 207.83. Enum encoding

Enum có thể encoded bằng:

```text
tag
tag + payload
string
integer
custom representation
```

Không phụ thuộc enum memory layout.

---

# 207.84. Invalid enum discriminant

Raw bytes có discriminant không hợp lệ:

```text
0xFF
```

không được cast trực tiếp thành safe enum.

Phải validate trước.

---

# 207.85. Bitcast vs Deserialize

Phân biệt:

```text
BITCAST
```

với:

```text
DESERIALIZE
```

Bitcast chỉ bảo toàn bit representation trong memory.

Deserialize diễn giải external representation thành semantic value.

---

# 207.86. Endian conversion

Endian conversion là semantic encoding operation.

Không dùng arbitrary pointer cast.

---

# 207.87. Alignment

Zero-copy typed access phải kiểm tra alignment.

Nếu không đủ alignment:

```text
copy/decode
```

thay vì unsafe dereference.

---

# 207.88. Packed wire representation

Packed structs có thể tồn tại:

```text
@repr(packed)
```

nhưng field access có thể cần unaligned load.

Unsafe/system layer phải chịu trách nhiệm.

---

# 207.89. Unaligned zero-copy

Compiler/backend có thể generate:

```text
unaligned load
```

nếu target hỗ trợ và representation contract cho phép.

Không giả định mọi CPU xử lý unaligned giống nhau.

---

# 207.90. Data interchange pipeline

Kiến trúc hoàn chỉnh:

```text
                  AXIOM VALUE
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Memory        Wire        Persistent
       Layout        Format        Format
          │            │            │
          │       ┌────┴────┐       │
          │       ▼         ▼       │
          │     Encode    Decode    │
          │       │         │       │
          └───────┴────┬────┴───────┘
                       ▼
                  Typed Value
```

---

# 207.91. Zero-copy decision tree

Compiler/library có thể chọn:

```text
Is representation compatible?
        │
       YES
        │
Is alignment valid?
        │
       YES
        │
Is backing storage alive?
        │
       YES
        │
Is access capability valid?
        │
       YES
        │
      ZERO-COPY
```

Nếu bất kỳ điều kiện nào không chứng minh được:

```text
       ↓
safe decode/copy
```

Không dùng unsafe fallback âm thầm.

---

# 207.92. Copy elimination

Ngay cả khi format không zero-copy, compiler vẫn có thể eliminate intermediate copies:

```text
network
 ↓
decode
 ↓
final object
```

thay vì:

```text
network
 ↓
temporary bytes
 ↓
temporary struct
 ↓
final struct
```

---

# 207.93. Allocation elimination

Comptime/generated serializers nên cung cấp đủ metadata để compiler biết:

```text
required_size
alignment
field locations
```

cho phép caller allocation.

---

# 207.94. Serializer specialization

Generic:

```text
serialize<T>
```

có thể specialize thành code riêng cho:

```text
T = User
```

và inline toàn bộ traversal.

---

# 207.95. No runtime reflection requirement

Serialization không cần:

```text
runtime TypeInfo
```

nếu compiler generate static encoder.

Điều này giữ binary nhỏ.

---

# 207.96. Dynamic schemas

Nếu application cần runtime schema:

```text
Schema
DynamicValue
```

là explicit library feature.

Không đưa dynamic reflection vào mọi binary.

---

# 207.97. IPC shared memory fast path

Một RPC framework có thể chọn:

```text
small message
 → copy
```

và:

```text
large payload
 → shared memory
 → handle transfer
```

tùy size/policy.

---

# 207.98. AI/compiler introspection

CompilerDB nên expose:

```text
ax inspect schema
ax explain serialization
ax explain zero-copy
ax schema diff
ax schema fingerprint
ax inspect wire-layout
```

Ví dụ AI có thể hỏi:

```text
Why is this message being copied?
```

và compiler trả:

```text
Zero-copy rejected:
  field `name` uses owned String
  wire encoding differs from memory representation
  destination requires owned storage
```

Đây là loại diagnostics rất phù hợp với mục tiêu **AI-native language** của Axiom.

---

# 207.99. Data interchange correctness boundary

Mọi generated serializer/deserializer phải đi qua:

```text
Generated HIR
 ↓
Type checking
 ↓
Ownership
 ↓
Capability
 ↓
Bounds verification
 ↓
Unsafe verification
 ↓
Verified MIR
```

Không có:

```text
"compiler-generated nên được tin"
```

---

# 207.100. Data interchange invariants — `ADATA`

### `ADATA-20`
Semantic values shall remain distinct from memory representation.

### `ADATA-21`
Memory, wire, persistent and IPC representations shall remain distinct contracts.

### `ADATA-22`
Serialization shall be explicit.

### `ADATA-23`
Deserialization shall validate external data before creating safe typed values.

### `ADATA-24`
Generated serialization code shall pass ordinary Axiom verification.

### `ADATA-25`
Schema identity shall remain distinct from semantic and binary ABI identity.

### `ADATA-26`
Schema evolution shall use explicit compatibility rules.

### `ADATA-27`
Field identity shall not depend solely on source declaration order where stable wire compatibility is required.

### `ADATA-28`
Unknown-field handling shall be explicit.

### `ADATA-29`
Forward and backward compatibility shall be distinct concepts.

### `ADATA-30`
Wire integer representation shall remain independent of native integer representation.

### `ADATA-31`
Wire floating-point representation shall define relevant special-value semantics.

### `ADATA-32`
Text encoding shall be explicit at external boundaries.

### `ADATA-33`
Invalid UTF-8 shall not become safe `Str`/text without validation or trusted unsafe contract.

### `ADATA-34`
Zero-copy deserialization shall require valid provenance, lifetime, alignment, representation and capability.

### `ADATA-35`
Borrowed decoded values shall not outlive backing storage.

### `ADATA-36`
Owned deserialization shall produce independent valid ownership.

### `ADATA-37`
The compiler shall not introduce hidden whole-message copies merely to satisfy lifetime management.

### `ADATA-38`
In-place decoding shall be supported where representation permits.

### `ADATA-39`
Wire-safe representation shall require an explicit or compiler-proven contract.

### `ADATA-40`
Pointer-containing memory representations shall not automatically be wire-safe.

### `ADATA-41`
OS handles shall not be serialized as ordinary integers for cross-process transfer.

### `ADATA-42`
Shared-memory typed access shall require explicit layout and synchronization contracts.

### `ADATA-43`
Relative offsets shall not automatically become safe pointers.

### `ADATA-44`
Compression shall remain semantically separate from serialization.

### `ADATA-45`
Streaming compression shall not require materialization of the entire input.

### `ADATA-46`
Decompression shall support resource limits against expansion attacks.

### `ADATA-47`
Checksums, hashes, MACs and signatures shall remain distinct security primitives.

### `ADATA-48`
Canonical serialization shall be deterministic when required by the protocol.

### `ADATA-49`
Malformed input shall produce recoverable decode errors rather than implicit panic.

### `ADATA-50`
Deserializers shall support explicit allocation/resource limits.

### `ADATA-51`
Recursive formats shall have explicit depth/resource limits where necessary.

### `ADATA-52`
Schema migrations shall be ordinary verified Axiom code.

### `ADATA-53`
Schema compatibility shall be independently checkable by tooling.

### `ADATA-54`
Wire compatibility shall remain distinct from Axiom source compatibility.

### `ADATA-55`
Persistent format compatibility shall remain distinct from wire compatibility.

### `ADATA-56`
Bitcast shall remain distinct from deserialize.

### `ADATA-57`
Unaligned wire data shall not be accessed as aligned typed memory without proof.

### `ADATA-58`
Invalid enum discriminants shall not become safe enum values without validation.

### `ADATA-59`
Serializer specialization shall preserve semantic equivalence.

### `ADATA-60`
Generated serializers should permit allocation and copy elimination.

### `ADATA-61`
Serialization need not require runtime reflection.

### `ADATA-62`
Static serialization shall not require a monolithic runtime.

### `ADATA-63`
Dynamic schema/reflection shall be opt-in.

### `ADATA-64`
IPC zero-copy shall preserve storage ownership and capability semantics.

### `ADATA-65`
Shared-memory fast paths shall remain explicit.

### `ADATA-66`
Compression/serialization libraries shall be replaceable without changing Core semantics.

### `ADATA-67`
Generated data-interchange code shall remain visible to CompilerDB.

### `ADATA-68`
AI tooling shall be able to explain serialization, schema and zero-copy decisions.

### `ADATA-69`
External data shall never gain safe memory capabilities merely because its byte representation resembles an Axiom type.

### `ADATA-70`
Data interchange abstractions shall compose with Network, Storage, IPC, FFI, GPU and Distributed Systems.

---

# Kết quả kiến trúc 207

Axiom giờ có một separation rất sạch:

```text
                  SEMANTIC VALUE
                        │
          ┌─────────────┼──────────────┐
          │             │              │
        MEMORY         WIRE         STORAGE
          │             │              │
       ABI/layout    protocol        persistence
          │             │              │
          └─────────────┼──────────────┘
                        │
                     IPC
```

Và compiler có thể tối ưu:

```text
normal case
    ↓
safe copy

compatible case
    ↓
zero-copy view

provably constructible case
    ↓
in-place construction

optimization case
    ↓
copy/temporary/allocation elimination
```

**Programmer không phải viết lifetime annotation để đạt zero-copy.**

Đây chính xác là triết lý Axiom:

> **Programmer mô tả semantic intent; compiler chứng minh và tối ưu implementation.**

---

# BOOTSTRAP-208 — Cryptography, Security Primitives, Secure Memory & Constant-Time Computing

**TRẠNG THÁI: NEXT**

Bước tiếp theo nên khóa tầng cryptography/security vì 207 vừa hoàn thiện:

```text
Hash
Checksum
MAC
Signature
Serialization
Network
IPC
Storage
```

208 sẽ hợp nhất chúng thành security architecture:

```text
Cryptographic Hash
MAC
HMAC
AEAD
AES-GCM
ChaCha20-Poly1305
Public Key
Ed25519
ECDSA
X25519
Key Exchange
KDF
HKDF
Randomness
CSPRNG
Secure Memory
Zeroization
Constant-Time
Side Channels
Key Storage
Certificate
Trust Store
Secure Channel
Hardware Security
TPM
Secure Enclave
HSM
Capability Tokens
Authentication
Authorization
```

Đặc biệt sẽ chốt một vấn đề rất quan trọng đối với Axiom:

> **Cryptography không được chỉ là một thư viện gọi C/ASM bên ngoài; Axiom phải có semantic contract để compiler biết vùng code nào yêu cầu constant-time, không được vectorize/branch/reorder theo cách tạo side-channel, đồng thời vẫn cho phép backend sinh machine code tối ưu.**