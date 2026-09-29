# BOOTSTRAP-183 — Filesystem, Paths, File I/O, Memory Mapping & Storage Abstractions
**FROZEN / COMPLETED**

Đây là phần nối trực tiếp từ networking. Mục tiêu là filesystem API đủ cao để dễ dùng, nhưng không che mất những khả năng systems-level như `mmap`, direct I/O, sparse file, file locking hay `fsync`.

Nguyên tắc:

> **File là resource; Path là dữ liệu; FileView là capability; MappedRegion là storage contract.**

Không gom tất cả thành một kiểu `File` khổng lồ.

---

## 183.1. Phân biệt Path và File

Hai khái niệm hoàn toàn khác nhau:

```text
Path
    = tên/địa chỉ của filesystem object

File
    = resource/handle đang mở tới object
```

Ví dụ:

```ax
let path = Path::from("data/test.bin");
let file = File::open(path)?;
```

`Path` không sở hữu file descriptor.

`File` sở hữu OS resource.

---

# 183.2. Path là value

`Path` nên là value semantic.

Có thể:

```ax
let a = path;
let b = a;
```

nếu loại Path tương ứng là `Copy`/immutable value hoặc có semantics value phù hợp.

Không có ownership của OS resource.

---

# 183.3. File là resource

```ax
let file = File::open(path)?;
```

`File`:

```text
!Copy
Move
Drop
```

Drop release handle.

---

# 183.4. Không dùng integer làm File API

Không:

```ax
let fd: i32 = open(...);
```

làm API thông thường.

Raw descriptor chỉ nằm ở:

```text
std::os
std::system
unsafe
FFI
```

---

# 183.5. File handle ≠ filesystem identity

Một file có thể có:

```text
FileId
```

và nhiều handles:

```text
Handle A
Handle B
```

Hai handle có thể trỏ cùng object.

Do đó:

```text
memory identity
file-handle identity
filesystem object identity
path identity
```

là các khái niệm khác nhau.

---

# 183.6. Path ≠ File identity

Hai path:

```text
/a/data
/b/link-to-data
```

có thể tham chiếu cùng object tùy filesystem.

Không dùng string/path equality để suy ra object identity.

---

# 183.7. Path representation

Axiom cần hai lớp:

```text
Path
OsPath
```

### `Path`

Portable logical filesystem path.

### `OsPath`

Native platform representation.

Ví dụ:

```text
Unix → byte-oriented
Windows → UTF-16-oriented OS API
```

---

# 183.8. Không ép filesystem thành UTF-8

Đây là điểm rất quan trọng.

Axiom mặc định UTF-8 cho **text**, nhưng filesystem path là OS resource identifier.

Không được giả định mọi filename đều là UTF-8.

---

# 183.9. String → Path

Có thể có conversion:

```ax
let path = Path::from_str(text)?;
```

nếu platform/path semantics cho phép.

Không phải mọi `String` đều tự động là valid Path.

---

# 183.10. Path → String

Không nên:

```ax
let s: String = path;
```

một cách implicit.

Có thể:

```ax
path.to_string()?
```

và operation có thể fail nếu path không biểu diễn được dưới encoding yêu cầu.

---

# 183.11. Path components

Path API nên hỗ trợ:

```text
root
parent
file_name
extension
stem
components
join
normalize
```

nhưng phải phân biệt:

```text
lexical normalization
filesystem resolution
```

---

# 183.12. Lexical normalization ≠ canonicalization

Ví dụ:

```text
a/../b
```

có thể lexical-normalize thành:

```text
b
```

nhưng filesystem resolution có thể khác nếu symlink/component semantics liên quan.

Không được gọi `normalize()` rồi giả định đã xác định object thật.

---

# 183.13. Absolute vs relative

Path có semantic:

```text
Absolute
Relative
```

Nhưng relative path resolution phụ thuộc base directory.

---

# 183.14. Current directory

`current_dir()` là external process state.

Do đó:

```text
Effect:
ExternalState
```

Không phải pure function.

---

# 183.15. Path join

```ax
let path2 = base.join("data").join("file.bin");
```

là operation trên value.

Không truy cập filesystem.

---

# 183.16. Metadata

Filesystem metadata:

```text
Metadata
├── type
├── size
├── permissions
├── timestamps
├── identity
├── links
└── platform fields
```

---

# 183.17. File type

Semantic enum:

```text
Regular
Directory
Symlink
Device
Pipe
Socket
Other
```

Platform có thể có thêm type.

---

# 183.18. Symlink

Symlink phải được biểu diễn rõ.

Các API:

```text
metadata(path)
symlink_metadata(path)
read_link(path)
```

nên phân biệt follow-link và no-follow.

---

# 183.19. TOCTOU

Không nên khuyến khích pattern:

```text
check(path)
↓
open(path)
```

như một guarantee security.

Filesystem có thể thay đổi giữa hai operation.

---

# 183.20. Open là authority boundary

Operation:

```text
File::open(path)
```

mới tạo resource capability.

Sau khi open, thao tác trên handle không nên phụ thuộc path string nữa.

---

# 183.21. File capabilities

File có thể có capabilities:

```text
READ
WRITE
APPEND
SEEK
SYNC
RESIZE
METADATA
```

---

# 183.22. Read capability

```ax
file.read(mut_view(buffer))?;
```

yêu cầu read capability.

---

# 183.23. Write capability

```ax
file.write(view(data))?;
```

yêu cầu write capability.

---

# 183.24. Read/write không cần hai pointer type

Không cần:

```text
File*
File&
```

hay lifetime annotations.

Capability verifier quản lý access.

---

# 183.25. Open options

API:

```ax
OpenOptions {
    read: true,
    write: true,
    create: true,
    truncate: false,
    append: false
}
```

Nhưng đây nên là builder/value API.

---

# 183.26. Open flags không nên là magic integer

Không:

```text
O_RDONLY | O_CREAT | ...
```

trong portable API.

Native flags nằm ở `std::os`.

---

# 183.27. Create

```ax
File::create(path)
```

có thể là convenience API tương đương một cấu hình `OpenOptions`.

---

# 183.28. Append semantics

Append phải là OS/filesystem semantic.

Nhiều writer đồng thời có thể có behavior phụ thuộc platform.

API phải không hứa atomic record append nếu backend không đảm bảo.

---

# 183.29. Truncate

```ax
file.set_length(0)?;
```

là explicit mutation.

Không implicit từ việc mở file trừ khi `truncate=true`.

---

# 183.30. Seek

File có cursor state:

```text
Position
```

API:

```ax
file.seek(SeekFrom::Start(0))?;
```

---

# 183.31. Seek là mutable state

Hai task dùng chung một file handle và cùng thay đổi cursor sẽ conflict nếu không có synchronization.

---

# 183.32. Positional I/O

Để tránh shared cursor:

```ax
file.read_at(offset, mut_view(buffer))?;
file.write_at(offset, view(data))?;
```

Đây là abstraction rất quan trọng cho concurrent/random-access workloads.

---

# 183.33. `read_at` không thay đổi cursor

Đây nên là semantic guarantee.

---

# 183.34. Async positional I/O

```ax
file.read_at_async(offset, mut_view(buffer)).await?;
```

cho phép nhiều operation độc lập hơn.

---

# 183.35. File offset và capability

`read_at()` có thể dùng immutable/shared file resource nếu OS semantics cho phép.

Đây là lý do capability model tốt hơn một mutex bắt buộc cho mọi File.

---

# 183.36. Buffered I/O

```text
BufferedReader<File>
BufferedWriter<File>
```

là library abstraction.

Không phải Core.

---

# 183.37. Compiler optimization

Nếu generic static:

```ax
BufferedReader<File>
```

compiler có thể inline:

```text
buffer management
+
file read
```

và loại bỏ abstraction overhead.

---

# 183.38. Direct I/O

Một số platform hỗ trợ direct/unbuffered I/O.

Axiom có thể:

```text
DirectFile
```

hoặc option:

```text
OpenOptions.direct = true
```

nhưng alignment/buffer constraints phải được API kiểm tra.

---

# 183.39. Direct I/O buffer

Nếu OS yêu cầu alignment:

```text
alignment = N
```

safe API phải đảm bảo buffer hợp lệ.

Không bắt application dùng unsafe pointer.

---

# 183.40. Alignment contract

Compiler/storage layer có thể cung cấp:

```text
AlignedBuffer<T>
```

với semantic alignment guarantee.

---

# 183.41. Memory mapping

`mmap` không nên được biểu diễn chỉ bằng:

```text
view<u8>
```

vì mapping có storage contract đặc biệt.

Nên có:

```text
MappedRegion<T>
```

hoặc tương đương.

---

# 183.42. MappedRegion là resource

```text
MappedRegion
    owns mapping
    Drop → unmap
```

---

# 183.43. Mapping capability

Từ:

```text
MappedRegion
```

có thể tạo:

```text
view<T>
mut_view<T>
```

nếu mapping được mở với capability tương ứng.

---

# 183.44. Mapping lifetime

```text
MappedRegion
    ↓
view
```

view không được sống lâu hơn mapping.

Verifier biết dependency:

```text
owner → capability
```

---

# 183.45. Unmap

Không cho:

```text
unmap(region)
```

trong khi safe view còn sống.

Compiler báo:

```text
E_CAPABILITY_LIFETIME
```

---

# 183.46. Memory mapping và relocation

MappedRegion có stable address contract nếu API expose address-sensitive semantics.

Compiler không được:

```text
move
relocate
scalarize
```

mapping theo cách thay đổi observable address.

---

# 183.47. Mapping ≠ heap

Đây là điểm quan trọng:

```text
MappedRegion
```

không phải heap allocation.

Storage domain:

```text
MAPPED_FILE
```

có thể được thêm vào internal storage classification.

---

# 183.48. File-backed storage

Mapping:

```text
file
 ↓
virtual memory mapping
 ↓
MappedRegion
```

OS quản lý physical pages.

Axiom không giả định mọi byte đã nằm trong RAM.

---

# 183.49. Lazy paging

Page faults là OS behavior.

Không làm thay đổi language memory semantics.

---

# 183.50. Mapping persistence

`flush()` có thể:

```text
memory → OS page cache
```

Trong khi `sync` có semantics mạnh hơn tùy platform.

API phải phân biệt.

---

# 183.51. `flush` vs `sync`

Không nên hứa:

```text
flush == physically persistent
```

Một API mạnh hơn có thể:

```text
sync_data()
sync_all()
```

---

# 183.52. Persistence semantics

Filesystem persistence không thể được định nghĩa hoàn toàn portable.

Axiom nên ghi rõ:

```text
semantic request
+
platform guarantee
```

---

# 183.53. Atomic rename

Filesystem API nên có:

```ax
rename_atomic(old, new)?;
```

nếu platform hỗ trợ semantics cần thiết.

---

# 183.54. Atomic replacement

Pattern:

```text
write temp
sync
rename
```

có thể được library hỗ trợ:

```text
atomic_replace(path, data)
```

nhưng durability guarantees phải explicit.

---

# 183.55. Temporary files

API:

```text
TempFile
TempDir
```

resource ownership deterministic.

---

# 183.56. Temp cleanup

Drop có thể cleanup temporary resource.

Nếu cleanup failure observable, explicit `close()`/`persist()` có thể được cung cấp.

---

# 183.57. Persistent temporary file

Ví dụ:

```ax
let temp = TempFile::new()?;
temp.persist(final_path)?;
```

ownership resource chuyển đổi rõ ràng.

---

# 183.58. Directory

```text
Directory
```

có thể là owned handle resource.

---

# 183.59. Directory iteration

```ax
for entry in dir.entries()? {
    ...
}
```

Iterator giữ capability tới directory resource.

---

# 183.60. Directory iterator Drop

Nếu iterator bị bỏ giữa chừng:

```text
Drop
→ close directory enumeration resource
```

---

# 183.61. Directory entry

`DirEntry` nên chứa path/name data và metadata capability tùy API.

Không tự động giữ directory open nếu không cần.

---

# 183.62. Recursive traversal

Filesystem traversal nên là library iterator:

```text
walk(path)
```

không phải compiler primitive.

---

# 183.63. Symlink traversal

Traversal options:

```text
follow_symlinks
max_depth
stay_on_filesystem
```

explicit.

---

# 183.64. File locking

Tách:

```text
AdvisoryLock
MandatoryLock
```

---

# 183.65. Advisory lock

Advisory locking chỉ có ý nghĩa giữa cooperating processes.

Không phải memory-safety mechanism.

---

# 183.66. Mandatory lock

Nếu platform hỗ trợ mandatory locking, phải expose platform-specific semantics.

Không giả định portable.

---

# 183.67. Lock ownership

Lock guard:

```text
FileLockGuard
```

có thể là:

```text
!Copy
Drop → release
```

giống MutexGuard.

---

# 183.68. File lock và async

Không nên giữ synchronous blocking file lock guard qua `.await`.

Verifier có thể áp dụng rule tương tự sync mutex guard.

---

# 183.69. Async file I/O

Không assume mọi OS có native async filesystem I/O.

Backend có thể:

```text
native async
thread pool
blocking worker
io_uring
```

---

# 183.70. Semantic distinction

Application thấy:

```text
Future
```

Backend quyết định implementation.

---

# 183.71. Blocking worker

Nếu filesystem backend dùng thread pool:

```text
async read
    ↓
worker thread
    ↓
completion
```

vẫn hợp lệ.

Nhưng runtime phải không tạo một thread vô hạn cho mỗi operation.

---

# 183.72. Runtime policy

Async filesystem runtime có thể chọn:

```text
native
thread pool
hybrid
```

theo target.

---

# 183.73. File read into owned buffer

API:

```ax
let (buffer, n) =
    file.read_async(buffer).await?;
```

cho phép ownership transfer giống networking.

---

# 183.74. Zero-copy file processing

Pipeline:

```text
MappedRegion
 ↓
view<u8>
 ↓
parser
 ↓
Message
```

có thể zero-copy.

Verifier bảo vệ mapping lifetime.

---

# 183.75. Read-only mmap

```ax
let map = file.map_read_only()?;
```

sinh:

```text
MappedRegion
```

với READ capability.

---

# 183.76. Read-write mmap

```ax
let map = file.map_read_write()?;
```

sinh WRITE capability.

---

# 183.77. Copy-on-write mapping

Có thể:

```text
map_copy_on_write()
```

nhưng semantics phải rõ rằng writes không nhất thiết modify underlying file.

---

# 183.78. Executable mapping

Executable memory/file mapping thuộc system/unsafe domain.

Không nên có:

```text
map_executable()
```

trong ordinary safe filesystem API.

---

# 183.79. File-backed code

JIT/compiler có thể cần executable memory.

Đây là:

```text
std::os::memory
```

hoặc JIT library/system layer.

---

# 183.80. Sparse files

API có thể expose:

```text
set_length()
punch_hole()
allocate_range()
```

nếu backend hỗ trợ.

---

# 183.81. Sparse file semantics

Logical file size:

```text
size
```

khác physical blocks allocated.

Không được suy ra disk usage từ `size`.

---

# 183.82. Allocation metadata

Metadata có thể cung cấp:

```text
logical_size
allocated_size
```

nếu platform hỗ trợ.

---

# 183.83. File resize

`set_length()` là explicit mutation.

Có thể truncate hoặc extend.

---

# 183.84. Extend semantics

Extended region không mặc định chứa arbitrary uninitialized garbage trong safe API.

Filesystem semantics quyết định đọc extended bytes.

---

# 183.85. Security-sensitive zeroization

Deleting/truncating file không đồng nghĩa physical media erasure.

Không gọi:

```text
delete()
```

là secure erase.

Secure erase là platform/storage-specific.

---

# 183.86. File deletion

`remove(path)` xóa directory entry/reference.

Open file handle có thể vẫn tồn tại tùy OS.

Do đó:

```text
path removed
```

không đồng nghĩa:

```text
resource immediately destroyed
```

---

# 183.87. File lifetime

Một open File có thể tiếp tục sử dụng resource sau khi path bị unlink trên Unix-like systems.

Axiom phải không giả định path lifetime == file resource lifetime.

---

# 183.88. Windows differences

Windows có sharing/access semantics khác Unix.

Portable API không được giả định:

```text
unlink while open
```

luôn hợp lệ.

---

# 183.89. Cross-platform error

`PermissionDenied`, `NotFound`, `AlreadyExists` nên là portable error kinds.

Raw OS code vẫn được giữ.

---

# 183.90. Permissions

Portable abstraction:

```text
Permissions
```

nhưng Unix mode bits và Windows ACL không thể đồng nhất hoàn toàn.

---

# 183.91. ACL

Windows ACL / POSIX ACL / extended attributes nằm ở platform/system APIs.

---

# 183.92. File timestamps

Có thể có:

```text
created
modified
accessed
changed
```

nhưng semantics platform-specific.

Không ép mọi platform có cùng set timestamp.

---

# 183.93. Filesystem capabilities

Sandboxed application có thể chỉ được:

```text
read path X
write path Y
```

Runtime/security layer có thể enforce.

Compiler metadata có thể ghi required capability:

```text
FilesystemRead
FilesystemWrite
```

---

# 183.94. Package capability metadata

Một package dùng:

```text
std::fs
```

không nhất thiết có quyền filesystem ở compile time.

Quyền runtime/deployment là layer khác.

---

# 183.95. Compile-time filesystem

`comptime` có thể đọc source/resource nếu capability cho phép.

Nhưng:

```text
ReadFilesystem
```

phải là explicit external capability.

---

# 183.96. Build dependency

Nếu comptime đọc:

```text
assets/schema.json
```

file đó phải trở thành build dependency.

---

# 183.97. Generated source

Nếu comptime tạo:

```text
generated.ax
```

source generated phải quay lại:

```text
parse
resolve
type
verify
```

như đã frozen.

---

# 183.98. Reproducibility

Build identity phải chứa:

```text
path/content hash
```

của external compile-time input.

Không phụ thuộc mù vào filesystem timestamp.

---

# 183.99. File caching

Compiler có thể cache:

```text
file metadata
file contents
comptime result
```

nhưng invalidation phải dựa trên dependency identity.

---

# 183.100. File content hash

Content-addressed cache phù hợp với Axiom build model:

```text
FileContentHash
```

thay vì chỉ modification time.

---

# 183.101. Memory-mapped compiler input

Compiler có thể mmap source files lớn.

Đây là implementation optimization.

Semantic SourceDB vẫn dùng:

```text
SourceFileId
SourceRevision
```

---

# 183.102. File-backed compiler cache

`.axmeta`, `.axo`, cache artifacts có thể dùng mmap để giảm copy.

Không làm thay đổi CompilerDB semantics.

---

# 183.103. Large-file support

File offsets nên dùng:

```text
u64
```

hoặc target-appropriate semantic type.

Không dùng `i32`.

---

# 183.104. File size vs memory size

`usize` phù hợp memory indexing.

File offset là storage/external-domain quantity.

Không nên mặc định đồng nhất hai loại.

---

# 183.105. Offset type

Có thể có:

```text
FileOffset
FileSize
```

newtypes để tránh nhầm:

```text
offset
length
index
```

---

# 183.106. Random access

File API nên hỗ trợ:

```text
read_at
write_at
```

để compiler/runtime có thể song song hóa operations khi semantics cho phép.

---

# 183.107. Sequential access

`Read` trait cung cấp stream semantics.

---

# 183.108. Memory-mapped access

`MappedRegion` cung cấp memory semantics.

Do đó ba abstraction:

```text
Stream I/O
Random-access I/O
Memory-mapped storage
```

không bị trộn.

---

# 183.109. Storage abstraction

Có thể có generic:

```text
Storage
```

nhưng không nên trở thành trait khổng lồ.

Nên tách:

```text
ReadableStorage
WritableStorage
SeekableStorage
MappableStorage
ResizableStorage
```

khi thực sự cần.

---

# 183.110. Generic algorithm

Ví dụ parser chỉ cần:

```ax
fn load<R: Read>(reader: mut_view<R>) -> Result<Data, Error>
```

Không cần biết đó là:

```text
File
TcpStream
MemoryStream
Pipe
```

---

# 183.111. Compile-time specialization

Nếu `R` là `File`, compiler có thể specialize.

Nếu dynamic:

```text
dyn Read
```

dynamic dispatch explicit.

---

# 183.112. File abstraction zero-cost

Không có hidden:

```text
Box<dyn Read>
```

cho generic code.

---

# 183.113. Memory mapping and alias analysis

Nếu:

```text
let a = map.view();
let b = map.view();
```

cả hai READ:

```text
NO_ALIAS? → không nhất thiết
```

chúng có thể alias.

Nếu:

```text
a = map.mut_view(rangeA)
b = map.mut_view(rangeB)
```

compiler chỉ cho phép cùng tồn tại nếu:

```text
rangeA ∩ rangeB = ∅
```

được chứng minh.

---

# 183.114. MappedRegion mutation

Mutation phải obey capability rules giống ordinary memory.

`mmap` không phải escape hatch khỏi safety.

---

# 183.115. Unsafe mapping

Unsafe API có thể expose:

```text
arbitrary address
raw mapping flags
device mapping
physical memory
```

nhưng sau unsafe boundary, safe capability vẫn phải được established bằng contract.

---

# 183.116. Device files

Unix `/dev/...` có thể mở qua File nhưng semantics có thể là:

```text
Device
```

không phải regular file.

API không được assume `seek/read/write` semantics giống regular file.

---

# 183.117. Pipes

Pipe có stream semantics.

Có thể implement:

```text
Read
Write
AsyncRead
AsyncWrite
```

---

# 183.118. Named pipes

Platform-specific resource.

Có thể expose generic stream traits.

---

# 183.119. Terminal

Terminal I/O không phải regular file semantics.

Có thể có:

```text
Terminal
Console
```

system layer.

---

# 183.120. Standard streams

```text
stdin
stdout
stderr
```

là process-owned resources.

Không nhất thiết là ordinary `File`, dù có thể implement common I/O traits.

---

# 183.121. Flush stdout

Explicit:

```ax
stdout.flush()?;
```

không compiler magic.

---

# 183.122. Environment

Filesystem/process state đều thuộc external state.

Compiler effect system phải biết các API này không pure.

---

# 183.123. Atomic filesystem operations

Các operation như:

```text
rename
link
unlink
mkdir
```

phải được biểu diễn như external effects.

Optimizer không được reorder chúng tùy tiện.

---

# 183.124. Evaluation order

Nếu:

```ax
rename(a, b)?;
write(c)?;
```

observable filesystem ordering phải giữ nguyên.

---

# 183.125. Filesystem effect regions

Future effect system có thể phân biệt:

```text
filesystem path A
filesystem path B
```

nhưng mặc định unknown filesystem state nên conservative.

---

# 183.126. Directory mutation invalidation

Một filesystem mutation có thể invalidate directory iteration state.

API phải khai báo contract.

---

# 183.127. File metadata cache

Compiler/runtime không được cache metadata indefinitely nếu API semantics yêu cầu fresh observation.

Cache chỉ là implementation detail với invalidation phù hợp.

---

# 183.128. File watcher

Filesystem watcher là external event source:

```text
watch(path).await
```

có thể dùng Future/Channel.

---

# 183.129. Watch event

```text
Created
Modified
Removed
Renamed
AttributeChanged
```

nhưng OS watcher semantics không hoàn toàn giống nhau.

API phải cho phép:

```text
RescanRequired
Overflow
Unknown
```

---

# 183.130. Watcher không đảm bảo event hoàn hảo

Event stream là observation mechanism, không phải transactional filesystem journal.

---

# 183.131. File locking vs capability

File lock không thay thế ownership.

Một process có thể own `File` resource nhưng vẫn cần advisory lock để coordinate với processes khác.

---

# 183.132. Cross-process synchronization

Axiom memory/concurrency model áp dụng cho shared memory/thread.

Filesystem lock là external synchronization primitive.

---

# 183.133. Atomic file replacement

Một library helper có thể cung cấp:

```ax
atomic_write(path, data)?;
```

với documented guarantees.

Không biến thành language primitive.

---

# 183.134. Crash consistency

Filesystem API phải phân biệt:

```text
operation succeeded
```

với:

```text
data guaranteed durable after power loss
```

---

# 183.135. Durable write

API explicit:

```text
sync_data()
sync_all()
```

hoặc platform-specific durability primitives.

---

# 183.136. No false portability

Nếu platform không có guarantee tương ứng:

```text
Unsupported
```

hoặc documentation giới hạn guarantee.

Không giả vờ mọi OS giống nhau.

---

# 183.137. File compression

Compression layer:

```text
CompressedReader<File>
CompressedWriter<File>
```

library abstraction.

Compiler generic optimization có thể loại overhead abstraction.

---

# 183.138. Encryption

Encryption stream tương tự:

```text
EncryptWriter<File>
DecryptReader<File>
```

Không phải filesystem primitive.

---

# 183.139. Storage pipeline

Axiom có thể viết:

```text
File
 ↓
BufferedReader
 ↓
DecryptReader
 ↓
DecompressReader
 ↓
Parser
```

và compiler có thể inline/fuse các lớp.

---

# 183.140. Memory allocation

Không có requirement:

```text
File.read()
→ heap allocate
```

API có thể nhận caller-provided buffer.

---

# 183.141. Allocation-free I/O

Ví dụ:

```ax
var buffer: Array<u8, 8192>;

loop {
    let n = file.read(mut_view(buffer))?;
    ...
}
```

không yêu cầu heap allocation.

---

# 183.142. Owned read

Khi cần dynamic size:

```ax
let data = file.read_all()?;
```

library có thể dùng `Vec<u8>`.

Compiler có thể tối ưu capacity bằng size metadata.

---

# 183.143. File size preallocation

Library có thể:

```text
metadata.size
→ reserve_exact
→ read
```

nhưng race vẫn có thể xảy ra.

Size metadata chỉ là optimization hint.

---

# 183.144. Race-safe reading

Không được giả định file size không thay đổi giữa:

```text
stat
read
```

External state.

---

# 183.145. `read_all`

Nếu file thay đổi trong lúc đọc:

API phải định nghĩa behavior:

```text
read until EOF
```

không phải “đọc đúng size ban đầu”.

---

# 183.146. File snapshot

Nếu cần immutable snapshot semantics, phải dùng explicit mechanism:

```text
snapshot
copy
versioned storage
mmap contract
```

Không suy ra từ ordinary File.

---

# 183.147. File clone

`File::clone_handle()` có thể tạo handle mới cùng resource tùy OS.

Không phải `Clone` semantic mặc định.

---

# 183.148. Why File isn't Copy

Nếu `File` là Copy:

```ax
let b = a;
```

sẽ khó xác định:

```text
who closes?
who owns cursor?
who controls flags?
```

Do đó:

> **File luôn non-Copy resource trong Core standard library contract.**

---

# 183.149. File API and Drop

`Drop(File)` release resource.

Nếu application cần flush/close errors:

```ax
file.close()?;
```

explicit.

---

# 183.150. Closed state

Sau explicit successful close:

```text
File
→ Closed
```

không thể dùng tiếp.

Verifier tracking ownership state + library contract có thể phát hiện use-after-close.

---

# 183.151. Reinitialization

Nếu type cho phép:

```text
close(file)
reopen_into(file)
```

có thể khôi phục ownership state.

---

# 183.152. No nullable File

Không:

```text
File? = null
```

mà:

```text
Option<File>
```

---

# 183.153. File optional resource

```ax
let file: Option<File>
```

mang semantics rõ ràng.

---

# 183.154. Error handling

Filesystem operations dùng:

```text
Result<T, IoError>
```

không exceptions.

---

# 183.155. Panic

Panic chỉ cho programming/environment fatal conditions, không dùng cho:

```text
file not found
permission denied
```

---

# 183.156. Async cancellation

Filesystem Future cancellation:

```text
Pending I/O
 ↓
cancel
```

không được giả định underlying operation đã rollback.

---

# 183.157. File operation ownership

Nếu operation owns buffer:

```text
Future
→ owns buffer
```

Nếu borrowed:

```text
Future
→ capability dependency
```

Verifier xử lý hai trường hợp.

---

# 183.158. Direct I/O and async

Direct async file I/O có thể yêu cầu:

```text
aligned buffer
stable address
restricted sizes
```

API/backend establish contracts.

---

# 183.159. mmap and async

Mapped memory không phải asynchronous I/O.

Page faults có thể xảy ra khi CPU accesses mapping.

Không coi ordinary load/store là Future.

---

# 183.160. `MappedRegion` and Drop

Drop unmaps.

Nếu có live view:

```text
E_CAPABILITY_LIFETIME
```

---

# 183.161. Mapping resize

Resizing underlying file trong khi mapped region tồn tại có thể invalidation.

API phải enforce hoặc document explicit unsafe behavior.

Safe API có thể disallow conflicting resize while mapping capability exists.

---

# 183.162. Mapping region split

Có thể:

```ax
let (a, b) = region.split_at(offset);
```

nếu compiler/library chứng minh disjoint regions.

Điều này rất phù hợp với `mut_view` capability model.

---

# 183.163. Mapped slice

```text
MappedRegion
    ↓
view<u8>
```

là zero-copy.

---

# 183.164. Typed mapping

Có thể có:

```ax
let records = region.as_array<Record>();
```

nhưng chỉ safe nếu:

```text
alignment
size
valid representation
endianness
initialization
```

được đảm bảo.

Nếu file format không phải native memory representation:

> Không được dùng BITCAST để thay thế serialization.

---

# 183.165. Endianness

File format:

```text
little-endian
big-endian
```

phải decode explicit.

---

# 183.166. Serialization

Serialization layer riêng:

```text
Memory representation
≠
File representation
≠
Wire representation
```

đã thống nhất với ABI model.

---

# 183.167. File format

Một `.axmeta`, `.axlib`, executable, database file... có serialization schema riêng.

Không phụ thuộc default struct layout.

---

# 183.168. Compiler artifact mapping

Compiler có thể mmap:

```text
.axmeta
.axo
.axlib
```

nhưng parser đọc format theo schema.

Không cast file bytes trực tiếp thành internal structs nếu representation contract không explicit.

---

# 183.169. Security

Safe filesystem API phải ngăn:

```text
invalid pointer
dangling mapped view
use-after-close
buffer overflow
```

nhưng không thể tự ngăn:

```text
wrong path
wrong permissions
logic bug
TOCTOU design bug
```

---

# 183.170. Symlink security

Security-sensitive APIs nên có:

```text
no_follow
open_relative_to
resolve_beneath
```

hoặc platform-specific secure path APIs.

Không hứa path string normalization là security boundary.

---

# 183.171. Directory capability

Một security-oriented API có thể open:

```text
Directory
```

rồi resolve children relative to directory handle.

Điều này giảm TOCTOU/path traversal risk.

---

# 183.172. Handle-relative APIs

Ví dụ concept:

```ax
dir.open_file("data.bin")?;
```

thay vì:

```ax
File::open("/absolute/path/...")
```

khi sandbox/security cần containment.

---

# 183.173. Filesystem namespace

Package/security layer có thể cấp:

```text
Directory capability
```

cho application.

---

# 183.174. No ambient filesystem authority

Axiom language không bắt buộc filesystem phải là global ambient capability.

Runtime có thể sandbox.

---

# 183.175. Capability manifest

Application metadata có thể khai báo:

```text
requires:
    filesystem.read
    filesystem.write
```

---

# 183.176. Runtime enforcement

Sandbox có thể deny operation:

```text
PermissionDenied
```

không phải compiler error nếu quyền là deployment policy.

---

# 183.177. Compiler analysis

Compiler có thể báo:

```text
Program requires FilesystemWrite capability
```

nhưng không tự quyết định OS security policy.

---

# 183.178. Build system

Build scripts/comptime có capability riêng:

```text
ReadSource
ReadFilesystem
WriteGenerated
ExecuteTool
```

đã frozen.

---

# 183.179. Compiler cache

Filesystem content dependencies integrate với:

```text
SemanticFingerprint
ImplementationFingerprint
BuildIdentity
```

---

# 183.180. Final storage architecture

Axiom filesystem model:

```text
                 Filesystem
                     │
        ┌────────────┴────────────┐
        │                         │
      Path                     File
        │                         │
   value data                 resource
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                 Stream        Random I/O     Mapping
                    │             │             │
                Read/Write     read_at       MappedRegion
                    │             │             │
                    └─────────────┴─────────────┘
                                  │
                              view<T>
                            mut_view<T>
```

Đây là kiến trúc tôi đề xuất giữ lâu dài.

---

# 183.181. Các invariant đóng băng

### Path

- **AFS-20** — Path is value data, not an owned OS resource.
- **AFS-21** — Path identity is distinct from filesystem object identity.
- **AFS-22** — Portable Path does not imply UTF-8 filesystem representation.
- **AFS-23** — Lexical normalization is distinct from filesystem resolution.
- **AFS-24** — Path operations do not implicitly access the filesystem.

### File resource

- **AFS-30** — File is a deterministic owned resource.
- **AFS-31** — File is non-Copy.
- **AFS-32** — Raw descriptors do not establish safe ownership.
- **AFS-33** — File handle identity is distinct from filesystem object identity.
- **AFS-34** — Resource duplication is explicit.
- **AFS-35** — Drop releases owned resource according to platform contract.
- **AFS-36** — Fallible close is explicit; Drop does not return recoverable errors.
- **AFS-37** — File cursor state is explicit mutable state.

### I/O

- **AFS-40** — Stream I/O and positional I/O are semantically distinct.
- **AFS-41** — Positional I/O does not implicitly mutate shared file cursor state.
- **AFS-42** — Buffered/direct/unbuffered I/O are implementation/API contracts, not hidden semantic changes.
- **AFS-43** — Async file I/O is Future-based.
- **AFS-44** — Async filesystem backends may use native completion or worker threads.
- **AFS-45** — Backend selection cannot change portable observable semantics.
- **AFS-46** — Caller-provided buffers permit allocation-free I/O.
- **AFS-47** — Owned-buffer APIs may transfer buffer ownership through async operations.

### Memory mapping

- **AFS-50** — MappedRegion is distinct from ordinary heap allocation.
- **AFS-51** — MappedRegion owns its mapping resource.
- **AFS-52** — Views into mappings cannot outlive the mapping.
- **AFS-53** — Writable mappings obey ordinary capability and alias rules.
- **AFS-54** — Unmapping cannot invalidate a live safe capability.
- **AFS-55** — Stable-address mapping contracts constrain storage optimization.
- **AFS-56** — Typed mapping requires valid alignment, size, initialization and representation guarantees.
- **AFS-57** — File representation is not assumed equal to native memory representation.

### Filesystem semantics

- **AFS-60** — Path operations and filesystem effects are distinct.
- **AFS-61** — Symlink following is explicit where relevant.
- **AFS-62** — TOCTOU cannot be eliminated by lexical path normalization.
- **AFS-63** — Atomic filesystem operations preserve their documented external ordering.
- **AFS-64** — File deletion does not imply immediate destruction of every open resource.
- **AFS-65** — Logical file size and physical storage allocation are distinct.
- **AFS-66** — Sparse files are supported without conflating logical and physical size.
- **AFS-67** — Durability is distinct from successful I/O completion.
- **AFS-68** — Cross-platform APIs do not invent unsupported filesystem guarantees.

### Security

- **AFS-70** — Filesystem authority may be represented as an explicit runtime capability.
- **AFS-71** — Directory-relative operations may establish stronger containment semantics than path strings.
- **AFS-72** — Sandbox permission is deployment/runtime policy, not ownership semantics.
- **AFS-73** — Raw filesystem/device-memory operations remain explicit system/unsafe APIs.

### Compiler integration

- **AFS-80** — Filesystem effects participate in EffectInfo.
- **AFS-81** — Filesystem operations are not assumed pure.
- **AFS-82** — Compiler caching of external file inputs requires dependency tracking.
- **AFS-83** — Comptime filesystem inputs participate in build identity.
- **AFS-84** — Compiler implementation may mmap source/artifact files without exposing mapping semantics to user code.
- **AFS-85** — Storage optimization cannot violate observable file/mapping identity or capability contracts.

---

## Một quyết định kiến trúc đáng giữ

Sau 183, tôi **không khuyến nghị** tạo một abstraction kiểu:

```text
Storage<T>
```

làm trung tâm của toàn bộ filesystem.

Nó sẽ quá rộng và cuối cùng trở thành một `Object/Any` trá hình.

Thay vào đó:

```text
Path
File
Directory
Read
Write
Seek
MappedRegion
view
mut_view
```

là những abstraction nhỏ, có composition rõ ràng.

Ví dụ:

```ax
fn parse<R: Read>(reader: mut_view<R>) -> Result<Data, Error>
```

có thể dùng với:

```text
File
TcpStream
MemoryStream
Pipe
TlsStream
CompressedReader
```

mà không cần một hierarchy kiểu Java/C++.

Đây rất phù hợp với triết lý **struct + trait + function** mà chúng ta đã chốt cho Axiom.

---

# Chuỗi kiến trúc hiện tại

Axiom bây giờ đã có:

```text
BOOTSTRAP-134   MIR
135             Ownership / Drop
136             Alias
137             Effect
138             Escape
139             SSA / MemorySSA
141             Interprocedural
142             Inlining / Specialization
143             Loop / Bounds
145             Memory Optimization
146             Data Layout
147             Microarchitecture
148             SIMD
149             PGO
150             LTO
151             Binary Optimization
160             Debug
161             Security
162             Diagnostics / AI
163             Compiler Performance
167             Iterators
168             Numeric
169             String / Unicode
170             Collections
171             Errors
172             Conversions
182             Networking
183             Filesystem / Storage
```

Nghĩa là language core đã dần chuyển từ **“thiết kế syntax”** sang **“thiết kế một hệ thống native hoàn chỉnh”**.

## Tiếp theo: BOOTSTRAP-184

**Process, Environment, Signals, IPC & OS Resource Model**

Sẽ giải quyết:

```text
Process
├── spawn
├── exec
├── wait
├── exit
├── environment
├── arguments
├── stdin/stdout/stderr
├── signals
├── process handles
└── child lifecycle

IPC
├── pipes
├── shared memory
├── channels
├── Unix sockets
├── Windows IPC
└── OS handles

System resources
├── process identity
├── thread identity
├── OS handle ownership
├── permissions
├── limits
└── resource inheritance
```

Đặc biệt sẽ chốt một vấn đề quan trọng: **Axiom có nên coi `Process`, `Thread`, `OS Handle`, `Device`, `Socket`, `File` đều là cùng một loại “external resource” ở tầng compiler hay chỉ dùng chung ownership/drop protocol mà vẫn giữ các semantic type hoàn toàn riêng biệt.**