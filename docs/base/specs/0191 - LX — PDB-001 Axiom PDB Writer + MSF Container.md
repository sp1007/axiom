# LX — PDB-001: Axiom PDB Writer + MSF Container

Ta chuyển sang bước tiếp theo: **tạo `.pdb` thật**, nhưng vẫn giữ CodeView và PDB linker tách biệt.

Mục tiêu của milestone này:

```text
Axiom Source
    ↓
Debug IR
    ↓
CodeView records
    ↓
COFF .debug$S / .debug$T
    ↓
Axiom Debug Linker
    ↓
MSF container
    ↓
PDB
    ↓
WinDbg / Visual Studio / debugger
```

Điểm quan trọng: **PDB không phải một file debug đơn giản**. Nó là một container MSF chứa nhiều stream; vì vậy phải xây một `MSF Writer` độc lập trước.

---

# 1. Kiến trúc

Không làm:

```text
DebugIR → PDB bytes
```

Mà:

```text
Debug IR
   ↓
CodeView IR
   ↓
CodeView Encoder
   ↓
Debug Contributions
   ↓
PDB Debug Linker
   ↓
MSF Database
   ↓
PDB Writer
```

Tách như vậy để sau này có thể:

```text
COFF
  ↓
CodeView
  ↓
PDB
```

mà không cần compiler frontend.

---

# 2. PDB gồm hai lớp chính

Ta nên coi:

```text
PDB
├── MSF container
└── PDB streams
     ├── PDB information
     ├── TPI
     ├── IPI
     ├── DBI
     ├── Module streams
     └── named streams
```

Trong đó:

- **MSF** quản lý pages/streams.
- **PDB layer** định nghĩa ý nghĩa các stream.
- **CodeView** định nghĩa nhiều record/debug symbol/type structures.

Đây là ba abstraction khác nhau.

---

# 3. MSF-001

Tạo module:

```text
compiler/debug/pdb/msf/
├── page.ax
├── stream.ax
├── directory.ax
├── superblock.ax
├── writer.ax
├── reader.ax
├── allocator.ax
├── verifier.ax
└── tests/
```

---

# 4. Page model

PDB/MSF dùng page-based storage.

Axiom abstraction:

```text
PageId
PageSize
PageRange
```

Không để code PDB trực tiếp thao tác:

```text
file_offset / 4096
```

Khắp nơi.

---

# 5. Page size

MSF database có page size được ghi trong superblock.

Do đó:

```text
MSFDatabase {
    page_size
    pages
    streams
    directory
}
```

Không hard-code một page size duy nhất trong architecture.

MVP có thể chọn page size phổ biến, nhưng reader phải đọc giá trị từ file.

---

# 6. Stream abstraction

```text
Stream {
    id
    size
    pages[]
}
```

Một stream có thể:

```text
size = 0
```

hoặc nhiều pages.

Ví dụ:

```text
PDB
 ├── Stream 0
 ├── Stream 1
 ├── Stream 2
 ├── TPI
 ├── IPI
 └── DBI
```

---

# 7. Stream writer

API nội bộ:

```text
create_stream()
write(stream, bytes)
finish_stream()
```

Không cho CodeView writer biết page allocation.

---

# 8. Page allocator

```text
PageAllocator {
    allocate()
    allocate_many(n)
    free()
}
```

MVP PDB writer không cần incremental modification.

Vì vậy:

```text
free()
```

có thể chưa cần exposed trong writer path.

Reader vẫn phải hiểu free-page map.

---

# 9. MSF superblock

Tạo:

```text
MSFSuperBlock {
    magic
    page_size
    free_page_map
    page_count
    directory_size
    directory_root_pages[]
}
```

Tên field nội bộ có thể khác, nhưng phải phân biệt:

```text
logical field
physical byte encoding
```

---

# 10. Directory

MSF directory mô tả:

```text
number_of_streams
stream_sizes[]
stream_page_lists[]
```

Do directory itself nằm trong stream/pages, writer phải thực hiện layout hai-phase.

---

# 11. Two-phase layout

Đây là cách sạch:

```text
Phase 1
    build logical streams

Phase 2
    calculate page requirements

Phase 3
    allocate pages

Phase 4
    construct directory

Phase 5
    allocate directory pages

Phase 6
    finalize superblock

Phase 7
    emit bytes
```

Không viết file sequentially rồi quay lại patch ngẫu nhiên.

---

# 12. Deterministic PDB

Axiom yêu cầu reproducible build.

Vì vậy:

```text
same inputs
   +
same compiler version
   +
same debug configuration
   ↓
same PDB bytes
```

hoặc ít nhất cùng semantic/debug identity.

---

# 13. Không dùng timestamp ngẫu nhiên

PDB ecosystem có những metadata có thể chứa identity/version information.

Axiom không được lấy:

```text
current time
machine hostname
random UUID
```

trừ khi explicitly required bởi format.

Nếu cần GUID/identity:

```text
derive from build identity
```

để reproducibility.

---

# 14. PDB identity

Tạo:

```text
PdbIdentity {
    signature
    age
}
```

và:

```text
PdbBuildId
```

tách khỏi:

```text
PackageId
```

Không dùng package identity làm PDB identity.

---

# 15. PDB GUID

Nếu format/debugger yêu cầu GUID:

```text
PdbGuid = deterministic_hash(
    module_identity,
    object_identity,
    debug_configuration,
    compiler_identity
)
```

Không:

```text
random_uuid()
```

trong reproducible mode.

---

# 16. TPI

**TPI — Type Info stream** chứa type information.

Axiom CodeView type layer sẽ map:

```text
DebugType
```

→ CodeView type records.

Ví dụ:

```text
i32
f64
Vec2
Option<i32>
Result<T,E>
```

---

# 17. IPI

IPI chứa information liên quan đến identifiers/type references used by debug ecosystem.

Axiom không nên cố gắng nhồi mọi compiler semantic type vào IPI.

Rule:

> Chỉ emit những CodeView records mà debugger ecosystem thực sự cần.

---

# 18. Type index

CodeView type records thường được tham chiếu bằng type index.

Do đó:

```text
DebugTypeId
```

không được encode trực tiếp thành CodeView type index.

Mapping:

```text
DebugTypeId
      ↓
CodeViewTypeId
```

---

# 19. Type table

Tạo:

```text
CodeViewTypeTable {
    records[]
    index_map
}
```

API:

```text
intern_type(debug_type)
```

Nếu cùng semantic debug type:

```text
Vec<i32>
```

xuất hiện 100 lần:

```text
→ one CodeView type record
```

---

# 20. Type dependency

Ví dụ:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

requires:

```text
f32
Vec2
```

Dependency graph:

```text
Vec2
 ├── f32
 └── f32
```

Phải emit `f32` trước record cần reference tới nó.

---

# 21. Recursive type

Ví dụ:

```axiom id="3qv1x9"
struct Node {
    next: Box<Node>
}
```

Type graph:

```text
Node
 ↓
Box<Node>
 ↓
Node
```

Không được DFS naïvely rồi infinite loop.

Dùng:

```text
TypeState =
    Unseen
    Emitting
    Emitted
```

---

# 22. Forward type references

Nếu CodeView representation cho phép forward declaration:

```text
Forward
    ↓
Definition
```

thì sử dụng.

Không duplicate recursive definitions.

---

# 23. DBI

DBI — Debug Information stream — là nơi liên kết:

```text
PDB
 ↔
modules
 ↔
object files
 ↔
sections
 ↔
symbols
```

Axiom abstraction:

```text
DebugModule {
    module_id
    object_name
    source_files[]
    symbol_stream
    line_table
}
```

---

# 24. Một COFF object = một debug module contribution

Ví dụ:

```text
foo.ax
bar.ax
startup.ax
```

có thể tạo:

```text
foo.obj
bar.obj
startup.obj
```

và PDB:

```text
Module foo
Module bar
Module startup
```

---

# 25. Debug linker input

Không cần source:

```text
axiom debug-link \
    foo.obj \
    bar.obj \
    startup.obj
```

hoặc build system tự gọi.

Input:

```text
COFF objects
+
debug contributions
```

Output:

```text
program.pdb
```

---

# 26. Module identity

Mỗi object module:

```text
DebugModuleId
```

phải deterministic.

Không dùng path tuyệt đối làm identity.

Path:

```text
C:\Users\...\project\foo.ax
```

có thể khác machine.

---

# 27. Source path normalization

Debug path nên hỗ trợ:

```text
absolute
relative
remapped
```

Build config:

```text
--debug-prefix-map
```

sau này có thể:

```text
C:\Users\HUNG\project
→
/src
```

Đây cực kỳ hữu ích cho reproducible builds.

---

# 28. Public symbol

Function:

```axiom id="j2w7q9"
pub fn add(...)
```

cần debug symbol:

```text
DebugPublicSymbol {
    name
    address
    size
    type
}
```

Nhưng:

```text
pub
```

không đồng nghĩa:

```text
linker export
```

đúng như ABI đã freeze.

---

# 29. Linker symbol ≠ Debug symbol

Một function có thể:

```text
private
```

nhưng vẫn xuất hiện trong PDB để debugger.

Ngược lại:

```text
@export("foo")
```

là linker/export semantic.

Không trộn hai khái niệm.

---

# 30. Procedure symbol

Mỗi machine function:

```text
MachineFunction
```

sau final layout có:

```text
section
offset
size
```

Debug linker tạo:

```text
ProcedureSymbol {
    name
    linkage_name
    section
    offset
    length
}
```

---

# 31. Function address finalization

Không ghi absolute VA vào object debug model.

Dùng:

```text
SectionRef
SectionOffset
```

Sau linker:

```text
SectionRef + final section RVA
```

→ final address.

---

# 32. Line table

Debug linker merge:

```text
foo:
    line entries

bar:
    line entries
```

thành PDB module/global debug representation.

Input:

```text
DebugLineTable {
    ranges[]
}
```

Mỗi range:

```text
section
offset
length
file
line
column
```

---

# 33. No absolute addresses in Debug IR

Invariant:

```text
ADBG-37
Debug IR does not contain final image addresses.
```

Điều này cho phép:

```text
same object
→ different link layouts
```

mà không cần recompile.

---

# 34. Section contribution

Thêm:

```text
DebugSectionContribution {
    module
    section
    offset
    size
}
```

Ví dụ:

```text
foo.obj
.text offset 0x0000 size 0x80
```

Linker map:

```text
foo.obj .text
→ final .text RVA 0x1000
```

---

# 35. Source file table

PDB debug linker phải deduplicate:

```text
foo.ax
foo.ax
foo.ax
```

thành một logical source file.

Key:

```text
NormalizedSourceIdentity
```

không đơn giản filename string.

---

# 36. Source content hash

Axiom có thể lưu:

```text
SourceFile {
    path
    checksum_algorithm
    checksum
}
```

để debugger biết source local có khớp binary không.

Đây cũng hữu ích khi source được di chuyển.

---

# 37. Checksum

Không cần giữ source text trong PDB MVP.

Có:

```text
path
hash
```

là đủ để debugger xác định source.

Sau này có thể hỗ trợ embedded source.

---

# 38. Embedded source — để sau

Không đưa vào PDB-001:

```text
source code embedding
```

Milestone riêng:

```text
DEBUG-SOURCE-001
```

---

# 39. CodeView symbol stream

Tạo:

```text
CodeViewSymbolStream {
    records[]
}
```

Record classes:

```text
Procedure
Block
Local
Parameter
Public
InlineSite
FileChecksum
End
```

MVP tập trung:

```text
Procedure
Local
Parameter
Public
Block
End
```

---

# 40. Procedure scope

Ví dụ:

```text
foo
 ├── parameter a
 ├── parameter b
 ├── local c
 └── block
```

CodeView symbol stream phải giữ cấu trúc scope.

Debug IR đã có:

```text
DebugScope
```

nên CodeView writer chỉ map.

---

# 41. Local variable record

```text
DebugLocalSymbol {
    variable
    location
    flags
}
```

CodeView encoder chuyển thành record phù hợp.

Không cho frontend tạo CodeView symbol trực tiếp.

---

# 42. Parameter

Parameter là DebugVariable + flag:

```text
Parameter
```

Ví dụ:

```text
a → RCX
b → RDX
```

Debugger có thể hiển thị:

```text
a = 10
b = 20
```

---

# 43. Register mapping

Tạo:

```text
CodeViewRegisterMap {
    AxiomPhysReg
    → CodeViewRegisterNumber
}
```

Ví dụ conceptually:

```text
RAX
RCX
RDX
...
XMM0
...
```

Không hard-code CodeView register numbers trong Machine IR.

---

# 44. PDB stream architecture

MVP logical model:

```text
PdbDatabase {
    info
    tpi
    ipi
    dbi
    modules[]
    named_streams[]
}
```

Writer:

```text
PdbDatabase
 ↓
PdbStreamBuilder
 ↓
MsfDatabase
 ↓
bytes
```

---

# 45. MSF writer API

```text
MsfBuilder {
    new(page_size)

    add_stream(bytes) -> StreamId

    build() -> MsfImage
}
```

Không để PDB code biết physical page map.

---

# 46. MSF reader ngay từ đầu

Không chỉ viết writer.

Phải có:

```text
PdbReader
MsfReader
CodeViewReader
```

để test round-trip:

```text
Axiom PDB
 ↓
read
 ↓
logical PdbDatabase
```

---

# 47. Round-trip invariant

```text
PDB logical model
    ↓ encode
PDB bytes
    ↓ decode
PDB logical model'
```

phải thỏa:

```text
semantic_equivalent(model, model')
```

Không nhất thiết byte-for-byte trong decoder output, nhưng writer phải deterministic.

---

# 48. PDB verifier

```text
AX_PDB_0001
invalid MSF superblock

AX_PDB_0002
invalid page size

AX_PDB_0003
stream page outside file

AX_PDB_0004
invalid stream directory

AX_PDB_0005
invalid TPI record

AX_PDB_0006
invalid type index

AX_PDB_0007
invalid DBI module

AX_PDB_0008
invalid symbol record

AX_PDB_0009
invalid section contribution

AX_PDB_0010
invalid source checksum

AX_PDB_0011
invalid procedure range

AX_PDB_0012
non-deterministic PDB metadata
```

---

# 49. Acceptance test đầu tiên

Source:

```axiom id="6h9t2p"
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(20, 22)
}
```

Build:

```text
axiom build main.ax --debug
```

Output:

```text
main.exe
main.pdb
```

---

# 50. Debugger acceptance

Mục tiêu:

```text
break main
run
```

Debugger phải thấy:

```text
main
```

Sau đó:

```text
step
```

và source location phải chuyển đúng.

---

# 51. Local acceptance

Tại:

```axiom id="4a1k8m"
fn add(a: i32, b: i32) -> i32 {
    let c = a + b
    c
}
```

Debugger:

```text
a = 20
b = 22
c = 42
```

ở `-O0 -g`.

---

# 52. Optimized acceptance

```text
-O2 -g
```

không yêu cầu:

```text
c = 42
```

phải luôn available.

Cho phép:

```text
c = optimized out
```

nhưng:

```text
breakpoint/source/function/stack
```

vẫn phải chính xác.

---

# 53. PDB không được làm PE linker phình ra

Kiến trúc:

```text
PE linker
    ↓
hello.exe

Debug linker
    ↓
hello.pdb
```

Hai artifact độc lập.

Release build:

```text
hello.exe
```

có thể strip:

```text
debug sections
```

hoặc build không tạo chúng ngay từ đầu.

---

# 54. Split debug

Về sau hỗ trợ:

```text
axiom build --debug
```

→

```text
program.exe
program.pdb
```

và:

```text
axiom strip-debug
```

→

```text
program.exe
program.pdb
```

tùy profile.

---

# 55. Không cần third-party PDB library

Đây là mục tiêu quan trọng.

Final compiler phải có:

```text
Axiom compiler
 ├── COFF writer
 ├── PE linker
 ├── CodeView writer
 ├── MSF writer
 └── PDB writer
```

không:

```text
LLVM
LLD
MSVC
link.exe
dia2dump
```

là dependency bắt buộc.

---

# 56. Có thể dùng debugger bên ngoài để test

Điều này khác hoàn toàn.

Axiom không cần viết debugger ở milestone này.

Có thể test PDB bằng:

```text
WinDbg
Visual Studio
LLDB
```

nếu có.

Chúng là **consumer/reference tools**, không phải compiler dependency.

---

# 57. Repository hoàn chỉnh

```text
compiler/debug/
├── id.ax
├── source.ax
├── location.ax
├── scope.ax
├── variable.ax
├── type.ax
├── function.ax
├── inline.ax
├── line.ax
├── module.ax
├── builder.ax
├── finalize.ax
├── verifier.ax
│
├── codeview/
│   ├── records.ax
│   ├── symbols.ax
│   ├── types.ax
│   ├── lines.ax
│   ├── registers.ax
│   ├── encoder.ax
│   ├── decoder.ax
│   └── tests/
│
└── pdb/
    ├── msf/
    │   ├── page.ax
    │   ├── stream.ax
    │   ├── directory.ax
    │   ├── superblock.ax
    │   ├── allocator.ax
    │   ├── writer.ax
    │   ├── reader.ax
    │   └── verifier.ax
    │
    ├── info.ax
    ├── tpi.ax
    ├── ipi.ax
    ├── dbi.ax
    ├── module.ax
    ├── symbols.ax
    ├── linker.ax
    ├── writer.ax
    ├── reader.ax
    └── tests/
```

---

# 58. Các invariant mới

```text
APDB-20
PDB generation is independent of semantic compilation.

APDB-21
MSF is represented as an independent container layer.

APDB-22
PDB streams are represented logically before physical page allocation.

APDB-23
MSF page allocation is deterministic.

APDB-24
PDB does not contain machine absolute addresses before final linking.

APDB-25
Section-relative debug addresses are resolved by the debug linker.

APDB-26
CodeView type indices are distinct from Axiom TypeId and DebugTypeId.

APDB-27
CodeView symbol records are generated from Debug IR.

APDB-28
PDB modules correspond to debug object/module contributions.

APDB-29
Source paths are normalized independently of host-specific absolute paths.

APDB-30
Source checksums are deterministic.

APDB-31
PDB identity is deterministic in reproducible builds.

APDB-32
PDB writer does not require a third-party compiler or linker.

APDB-33
PDB reader and writer support semantic round-trip testing.

APDB-34
PDB generation may be performed without recompiling source.

APDB-35
Release builds need not contain debug information.

APDB-36
Debug information cannot affect executable semantics.

APDB-37
PDB verification is independent from PE executable verification.

APDB-38
PDB format knowledge does not leak into frontend semantics.
```

---

# 59. Milestone đã đạt được

Nhánh Windows hiện có:

```text
                         Axiom Source
                              │
                         Frontend
                              │
                            MIR
                              │
                       Verified MIR
                              │
                             LIR
                              │
                       x86-64 ISel
                              │
                        Machine IR
                         /         \
                        /           \
                 ABI Lowering       Debug IR
                      │                 │
                Reg Allocation       CodeView
                      │                 │
                  FramePlan          PDB
                   /    \              │
             Machine    Unwind          │
                │          │             │
             Encoder      .xdata       .pdb
                │
              COFF
                │
             PE Linker
                │
             hello.exe
```

Đây là một architecture khá quan trọng: **executable path và debug path đã tách hoàn toàn nhưng cùng xuất phát từ Machine IR/Debug IR**.

---

# LXI — BƯỚC TIẾP THEO: ELF-001

Không nên tiếp tục đào sâu Windows nữa. Sau PDB, phần hợp lý nhất là chuyển sang **Linux x86-64 ELF**, vì đây là target thứ hai và nó sẽ kiểm chứng rằng backend architecture thực sự target-independent.

Ta sẽ xây:

```text
LIR
 ↓
same x86-64 ISel
 ↓
SysV AMD64 ABI
 ↓
same register allocator
 ↓
same FramePlan
 ↓
ELF Object Writer
 ↓
ELF64
 ↓
Axiom ELF Linker
 ↓
Linux executable
```

Điểm rất đáng chú ý là **không cần viết lại x86 backend**. Chỉ thay:

```text
WindowsX64ABI
        ↓
SysVAMD64ABI

COFF
        ↓
ELF

PE Linker
        ↓
ELF Linker

Windows Startup
        ↓
Linux Startup
```

Nếu abstraction hiện tại tốt, đây sẽ là bài kiểm tra thực tế đầu tiên cho quyết định kiến trúc của Axiom.