# BOOTSTRAP-303 — AXIOM LINKER CORE & SYMBOL/RELOCATION RESOLUTION ENGINE

## 303.1. Mục tiêu

Xây dựng **linker core** nhận nhiều relocatable object từ BOOTSTRAP-302 cùng static libraries và tạo ra một **Linked Image** trước khi serialize thành executable/shared library.

Pipeline mới:

```text
Axiom Source
    ↓
Frontend / MIR
    ↓
Machine Backend
    ↓
Object Writer ──────────────┐
    ↓                       │
  .o / .obj                 │
                            │
Libraries / Runtime / FFI ─┤
                            ↓
                  ┌───────────────────┐
                  │ BOOTSTRAP-303     │
                  │ LINKER CORE       │
                  │                   │
                  │ Symbol Resolution │
                  │ Archive Selection │
                  │ Section Merging   │
                  │ Relocations       │
                  │ Layout            │
                  │ GC / Dead Strip   │
                  │ Thunks / Stubs    │
                  │ TLS               │
                  │ PLT/GOT / IAT     │
                  └─────────┬─────────┘
                            ↓
                     Linked Image IR
                            ↓
                 executable/shared image
```

**303 chưa phải executable writer hoàn chỉnh.**

Nó phải xây dựng một **Linked Image** có địa chỉ, section, symbol và relocation đã được resolve. Việc serialize thành ELF executable, PE/COFF image, Mach-O executable… nên được tách thành bước tiếp theo.

---

# 303.2. Nguyên tắc quan trọng nhất

Axiom linker phải là:

> **Một linker semantic-first, target-independent ở core và target-specific ở policy/layout.**

Không được viết:

```text
ELF linker
COFF linker
Mach-O linker
```

thành ba linker độc lập.

Phải có:

```text
                    Linker Core
                        │
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
        ELF           COFF          Mach-O
      Backend         Backend         Backend
```

WASM có linker model riêng nhưng vẫn sử dụng cùng abstraction ở những phần có thể chia sẻ.

---

# 303.3. Linked Image IR

Định nghĩa representation trung gian:

```text
LinkedImage {
    target
    sections[]
    segments[]
    symbols[]
    resolved_relocations[]
    imports[]
    exports[]
    entry_point
    tls_layout
    unwind_layout
    debug_layout
    security_metadata
}
```

Đây là **semantic output của linker**.

Format writer sau này chỉ cần:

```text
LinkedImage
      ↓
ELF Image Writer
PE Image Writer
Mach-O Image Writer
WASM Module Writer
```

---

# 303.4. Input model

Linker nhận:

```text
ObjectUnit[]
StaticArchive[]
SharedImport[]
LinkOptions
Target
```

Một `ObjectUnit` chứa:

```text
Object IR
+
origin
+
dependency metadata
```

`origin` cần giữ để diagnostics có thể nói:

```text
foo defined in a.o
foo also defined in b.o
```

thay vì chỉ báo:

```text
duplicate symbol foo
```

---

# 303.5. Link graph

Linker phải xây dựng dependency graph:

```text
Entry
  ↓
main
  ↓
foo
  ↓
bar
  ↓
libX
```

Graph gồm:

```text
Symbol dependency
Section dependency
Object dependency
Archive member dependency
Runtime dependency
```

Đây là cơ sở cho:

- archive extraction
- dead-code elimination
- dead-section stripping
- incremental linking
- diagnostics.

---

# 303.6. Symbol resolution

Đây là core của 303.

Input có thể chứa:

```text
A.o:
    foo = defined global

B.o:
    foo = undefined
```

Linker phải tạo:

```text
foo → A.o::foo
```

Relocation trong B.o được redirect tới definition này.

---

# 303.7. Symbol resolution precedence

Phải định nghĩa deterministic rule.

Ví dụ semantic model:

```text
Strong definition
    >
Weak definition
    >
Undefined
```

Nếu có:

```text
strong + strong
```

thì:

```text
duplicate-definition error
```

trừ khi symbol/section policy explicit cho phép.

Nếu:

```text
strong + weak
```

strong thắng.

Nếu:

```text
weak + weak
```

linker có thể chọn theo deterministic rule.

Không được phụ thuộc vào input object order nếu semantic không yêu cầu.

---

# 303.8. Symbol table nội bộ

Tạo:

```text
LinkSymbol {
    name
    kind
    binding
    visibility
    state
    definition
    references[]
}
```

State:

```text
Undefined
Defined
WeakDefined
Common
Imported
Absolute
Synthetic
Discarded
```

`Synthetic` dùng cho linker-generated symbols:

```text
__start_*
__stop_*
GOT base
TLS symbols
PLT entries
runtime boundaries
```

---

# 303.9. Archive extraction

Static library:

```text
libfoo.a
```

không được load toàn bộ mặc định.

Linker phải thực hiện:

```text
undefined symbols
       ↓
find matching archive member
       ↓
extract member
       ↓
new definitions
       ↓
new undefined symbols
       ↓
repeat
```

Cho đến fixed point.

Ví dụ:

```text
main.o → foo
libX.a:
    foo.o → bar
    bar.o
```

Linker:

```text
main.o
 ↓
foo.o
 ↓
bar.o
```

Không extract các member không cần thiết.

---

# 303.10. Archive index

Archive cần index:

```text
symbol → archive member
```

Linker phải hỗ trợ:

```text
GNU-style archive index
```

và tương đương của target/toolchain khác.

Nếu archive không có index:

```text
fallback scan
```

có thể được hỗ trợ nhưng phải rõ ràng về performance.

---

# 303.11. Circular archive dependencies

Phải xử lý:

```text
libA → libB
libB → libA
```

không được loop vô hạn.

Dependency extraction phải có:

```text
visited member set
resolution work queue
fixed-point detection
```

Linker phải phát hiện unresolved cycle nếu sau fixed point vẫn còn symbol thiếu.

---

# 303.12. Section merging

Input:

```text
A.o:
    .text.foo

B.o:
    .text.bar

C.o:
    .text.main
```

Output:

```text
.text
    foo
    bar
    main
```

Nhưng section merging phải dựa trên:

```text
semantic section attributes
```

chứ không đơn giản:

```text
same name → merge
```

Các thuộc tính cần tương thích:

```text
EXEC
WRITE
ALLOC
TLS
MERGE
alignment
COMDAT
target constraints
```

---

# 303.13. Input section

Định nghĩa:

```text
InputSection {
    object
    section
    size
    alignment
    flags
    symbols[]
    relocations[]
}
```

Sau đó:

```text
InputSection[]
      ↓
SectionGrouping
      ↓
OutputSection[]
```

---

# 303.14. Output section

```text
OutputSection {
    name
    flags
    alignment
    inputs[]
    address
    file_offset
    size
}
```

Ví dụ:

```text
.text
.rodata
.data
.bss
.tdata
.tbss
.eh_frame
.debug_*
```

---

# 303.15. Section ordering

Linker phải có explicit ordering policy.

Ví dụ:

```text
.text
.init
.fini
.rodata
.data.rel.ro
.data
.tdata
.tbss
.bss
```

Nhưng không hard-code cho mọi target.

Target backend cung cấp:

```text
SectionOrderingPolicy
```

---

# 303.16. Dead Section Elimination

Axiom phải hỗ trợ:

```text
--gc-sections
```

semantic equivalent ngay từ linker core.

Graph:

```text
root sections
      ↓
relocations
      ↓
reachable sections
      ↓
keep
```

Không reachable:

```text
discard
```

Roots gồm:

```text
entry point
exported symbols
forced symbols
runtime-required sections
init/fini
exception/unwind roots
target-specific roots
```

---

# 303.17. COMDAT resolution

Các generic instantiation có thể xuất hiện nhiều lần:

```text
foo<int>
foo<int>
foo<int>
```

Nếu được đánh dấu COMDAT:

```text
select one
discard others
redirect references
```

Selection phải tuân contract của input object.

Không được đơn giản dùng:

```text
first wins
```

nếu target yêu cầu semantics khác.

---

# 303.18. Identical Code Folding

**Không đưa ICF vào semantic core v0.1.**

Có thể thiết kế extension:

```text
IdenticalCodeFolding
```

nhưng phải phân biệt:

```text
semantic duplicate
```

với:

```text
same machine bytes
```

Hai function có cùng machine bytes vẫn có thể có khác biệt observable:

- address identity
- symbol identity
- debug identity
- section semantics
- linker metadata.

Do đó ICF phải là optimization có contract riêng.

---

# 303.19. Address assignment

Sau section selection:

```text
OutputSection
      ↓
Segment
      ↓
Virtual Address
      ↓
File Offset
```

Phải duy trì:

```text
alignment
permissions
segment constraints
page boundaries
ABI rules
```

Ví dụ conceptual:

```text
.text      VA 0x1000
.rodata    VA 0x9000
.data      VA 0xA000
.bss       VA 0xB000
```

Đây vẫn là **linker virtual layout**, chưa serialize thành executable.

---

# 303.20. Segment model

Linked Image phải có abstraction:

```text
Segment {
    permissions
    alignment
    virtual_address
    file_offset
    file_size
    memory_size
    sections[]
}
```

Permissions:

```text
R
W
X
```

Axiom không được tạo executable writable segment mặc định nếu không có lý do target-specific.

---

# 303.21. W^X

Linker phải có policy:

```text
WRITE + EXECUTE
```

là bất thường và phải explicit.

Mục tiêu:

```text
R-X
RW-
R--
```

thay vì:

```text
RWX
```

Nếu target hoặc runtime yêu cầu executable writable memory thì phải có explicit contract.

---

# 303.22. Relocation resolution

Sau khi symbol + address được biết:

```text
Relocation
    ↓
symbol address
    ↓
addend
    ↓
place address
    ↓
target relocation formula
    ↓
patched bytes
```

Ví dụ PC-relative:

```text
S + A - P
```

trong đó:

```text
S = symbol address
A = addend
P = relocation place
```

Absolute:

```text
S + A
```

Linker phải sử dụng relocation semantics từ target backend, không tự suy đoán theo tên relocation.

---

# 303.23. Relocation overflow

Ví dụ:

```text
PCRelative32
```

nhưng target vượt ±2 GB.

Không được silently truncate.

Phải:

```text
overflow error
```

hoặc nếu target architecture hỗ trợ:

```text
relaxation / thunk generation
```

---

# 303.24. Linker relaxation

Một số relocation có thể được tối ưu sau layout.

Ví dụ conceptual:

```text
long branch
    ↓
target gần
    ↓
short branch
```

Pipeline:

```text
initial layout
    ↓
relocation analysis
    ↓
relaxation
    ↓
size changes
    ↓
re-layout
    ↓
repeat
```

Phải có fixed-point detection.

Không được dùng vòng lặp vô hạn.

---

# 303.25. Thunks / veneers

ARM64 và một số architecture cần branch veneer/thunk khi target quá xa.

Linker cần abstraction:

```text
Thunk {
    source
    target
    kind
    section
    generated_symbol
}
```

Ví dụ:

```text
call foo
   ↓
foo quá xa
   ↓
call __AxiomThunk_foo
   ↓
jump/call foo
```

Thunk phải trở thành một phần của link graph để relocation lại được xử lý chính xác.

---

# 303.26. GOT / PLT abstraction

Không đưa ELF-specific `GOT`/`PLT` trực tiếp vào core.

Core abstraction:

```text
IndirectAddressTable
ProcedureLinkageEntry
```

ELF backend map thành:

```text
GOT
PLT
```

PE backend có:

```text
IAT
```

Mach-O có cơ chế tương ứng.

---

# 303.27. Dynamic linking preparation

303 chỉ cần xây abstraction:

```text
ImportSymbol
ExportSymbol
DynamicRelocation
```

Chưa cần hoàn thiện dynamic loader.

Ví dụ:

```text
printf
```

có thể trở thành:

```text
Import {
    name = "printf"
    library = "libc"
}
```

Executable/shared-library builder sau này mới tạo:

```text
ELF .dynsym/.dynstr/.rela.*
PE import directory
Mach-O bind/rebase information
```

---

# 303.28. TLS

TLS cần được xử lý từ linker level.

Abstraction:

```text
TlsSymbol
TlsSection
TlsOffset
TlsModel
```

Models có thể gồm:

```text
LocalExec
InitialExec
LocalDynamic
GeneralDynamic
TargetSpecific
```

Linker phải đảm bảo relocation model phù hợp target.

---

# 303.29. Entry point

Linked Image có:

```text
entry_point: SymbolRef
```

Ví dụ:

```text
main
```

không nhất thiết là physical address ngay từ đầu.

Pipeline:

```text
entry symbol
    ↓
resolved symbol
    ↓
final address
```

Target executable writer sau này mới đưa nó vào header:

```text
ELF e_entry
PE AddressOfEntryPoint
Mach-O entry command
```

---

# 303.30. Init / fini

Không được coi constructor/destructor toàn cục như C++ magic.

Nếu Axiom module yêu cầu initialization:

```text
InitFunction
FiniFunction
```

phải trở thành explicit linker metadata.

Linker có thể tạo:

```text
.init_array
.fini_array
```

hoặc target equivalent.

Thứ tự phải deterministic.

---

# 303.31. Runtime dependency model

Axiom runtime là capability-driven.

Vì vậy linker không được tự động thêm:

```text
libaxiom-runtime
```

cho mọi chương trình.

Ví dụ:

```text
fn main() {
    1 + 2
}
```

có thể link runtime-free.

Trong khi:

```text
async
thread
allocator
panic
unicode
```

có thể kéo theo component tương ứng.

Link graph phải thể hiện dependency thật sự.

---

# 303.32. Library resolution

Linker cần abstraction:

```text
Library {
    StaticArchive
    SharedLibrary
    Framework
    SystemLibrary
    NativeObject
}
```

Nhưng core không được hard-code:

```text
libc.so
kernel32.dll
Foundation.framework
```

Target/platform layer cung cấp policy.

---

# 303.33. FFI symbol handling

FFI declaration:

```text
extern "C" fn printf(...)
```

phải tạo symbol contract:

```text
ABI = C
name = printf
external = true
```

Linker không được giả định Axiom ABI cho foreign symbol.

---

# 303.34. Symbol interposition

Đây là điểm phải thiết kế sớm.

Axiom static linking có thể mặc định:

```text
NoInterposition
```

để optimizer mạnh.

Dynamic/shared-library mode có thể bật:

```text
Interposable
```

Khi symbol có thể bị interpose, linker/compiler không được giả định rằng:

```text
foo → local foo
```

luôn luôn đúng.

Điều này ảnh hưởng trực tiếp tới:

- devirtualization
- constant propagation
- function address
- relocation
- PLT/GOT.

---

# 303.35. Incremental linking foundation

Ngay từ 303, giữ:

```text
ObjectId
SectionFingerprint
SymbolFingerprint
RelocationFingerprint
```

để sau này có thể:

```text
unchanged object
    ↓
reuse previous linked state
```

Nhưng **incremental linking không phải requirement hoàn chỉnh của 303**.

Chỉ cần không thiết kế kiến trúc ngăn cản nó.

---

# 303.36. Link diagnostics

Diagnostics phải ở mức semantic:

```text
error[A-LINK-001]:
multiple strong definitions of `foo`

  --> a.axobj: .text+0x20
  --> b.axobj: .text+0x40
```

Undefined:

```text
error[A-LINK-002]:
undefined symbol `foo`

referenced by:
  main.o: .text+0x18
  bar.o:  .text+0x42

searched:
  libA.a
  libB.a
```

Relocation overflow:

```text
error[A-LINK-003]:
PC-relative relocation overflow

symbol: foo
relocation: PCRelative32
distance: ...
range: ...
```

Diagnostics phải giữ được:

```text
source → object → section → relocation → symbol
```

---

# 303.37. Link verification

Trước khi trả về `LinkedImage`, chạy:

```text
LinkVerifier
```

Kiểm tra:

```text
- tất cả required symbols đã resolve
- không duplicate illegal definitions
- section layout hợp lệ
- segment permissions hợp lệ
- relocation đã resolve hoặc được đánh dấu dynamic
- relocation overflow không tồn tại
- symbol address hợp lệ
- entry point hợp lệ
- TLS layout hợp lệ
- thunk references hợp lệ
- GOT/IAT/PLT metadata nhất quán
- alignment hợp lệ
- no impossible overlapping regions
```

---

# 303.38. Linker phases

Pipeline chính:

```text
1. Load Objects
        ↓
2. Load Archives
        ↓
3. Build Symbol Universe
        ↓
4. Resolve Archive Members
        ↓
5. Resolve Symbols
        ↓
6. Build Link Graph
        ↓
7. COMDAT Resolution
        ↓
8. Dead Section Elimination
        ↓
9. Create Synthetic Sections
        ↓
10. Merge Input Sections
        ↓
11. Assign Output Sections
        ↓
12. Assign Segments
        ↓
13. Assign Addresses
        ↓
14. Create Thunks / Indirection
        ↓
15. Relaxation
        ↓
16. Re-layout if necessary
        ↓
17. Resolve Relocations
        ↓
18. Build Dynamic Metadata
        ↓
19. Resolve Entry Point
        ↓
20. Verify LinkedImage
```

---

# 303.39. Fixed-point architecture

Một số phase có thể làm thay đổi graph:

```text
archive extraction
COMDAT
GC
thunks
relaxation
synthetic sections
```

Do đó linker phải có worklist/fixed-point engine thay vì một chuỗi hard-code đơn giản.

Concept:

```text
LinkState
    ↓
Change
    ↓
Invalidate affected facts
    ↓
Re-run dependent phase
    ↓
No change → stable
```

Điều này rất quan trọng cho linker lớn sau này.

---

# 303.40. Implementation tree

```text
compiler/linker/
│
├── link_ir.ax
├── link_context.ax
├── link_options.ax
├── link_graph.ax
│
├── input/
│   ├── object_loader.ax
│   ├── archive_loader.ax
│   └── library_loader.ax
│
├── symbols/
│   ├── symbol_table.ax
│   ├── resolver.ax
│   ├── visibility.ax
│   └── imports.ax
│
├── sections/
│   ├── input_section.ax
│   ├── output_section.ax
│   ├── merge.ax
│   ├── gc.ax
│   └── comdat.ax
│
├── layout/
│   ├── section_layout.ax
│   ├── segment_layout.ax
│   ├── address_layout.ax
│   └── tls_layout.ax
│
├── relocation/
│   ├── resolver.ax
│   ├── overflow.ax
│   ├── relaxation.ax
│   └── thunk.ax
│
├── dynamic/
│   ├── got.ax
│   ├── plt.ax
│   ├── imports.ax
│   └── exports.ax
│
├── verify/
│   └── link_verifier.ax
│
└── tests/
    ├── symbols/
    ├── archives/
    ├── comdat/
    ├── gc/
    ├── relocation/
    ├── overflow/
    ├── tls/
    ├── thunk/
    └── integration/
```

---

# 303.41. Public API

```text
fn link(
    inputs: LinkInputs,
    target: Target,
    options: LinkOptions
) -> Result<LinkedImage, LinkError>
```

Trong đó:

```text
LinkInputs {
    objects[]
    archives[]
    shared_imports[]
}
```

và:

```text
LinkOptions {
    entry
    output_kind
    dead_strip
    icf
    lto
    pie
    static
    dynamic
    debug
    deterministic
}
```

`icf` có thể tồn tại trong API nhưng **không được implement trong semantic core 303**.

---

# 303.42. Invariants

```text
ALINK-20  Linker core độc lập executable format.

ALINK-21  Linker không phụ thuộc assembler.

ALINK-22  Linker không phụ thuộc compiler frontend.

ALINK-23  Symbol resolution deterministic.

ALINK-24  Strong + strong duplicate phải được xử lý explicit.

ALINK-25  Strong thắng weak.

ALINK-26  Undefined symbol chỉ được chấp nhận nếu dynamic/import policy cho phép.

ALINK-27  Archive extraction đạt fixed point.

ALINK-28  Archive member không cần thiết không được tự động extract.

ALINK-29  Section merge phải kiểm tra compatibility.

ALINK-30  COMDAT semantics phải được bảo toàn.

ALINK-31  Dead-section elimination không được loại root.

ALINK-32  Entry point phải resolve được.

ALINK-33  Output section alignment phải được bảo toàn.

ALINK-34  Segment permissions phải hợp lệ.

ALINK-35  W+X phải explicit.

ALINK-36  Relocation phải được resolve hoặc chuyển thành dynamic relocation hợp lệ.

ALINK-37  Relocation overflow không được truncate.

ALINK-38  Thunk generation phải nằm trong link graph.

ALINK-39  Relaxation phải đạt fixed point.

ALINK-40  Symbol address chỉ được finalize sau layout thích hợp.

ALINK-41  TLS layout phải target-valid.

ALINK-42  GOT/PLT/IAT không được hard-code vào Linker Core.

ALINK-43  Dynamic linking là capability/policy, không mặc định.

ALINK-44  Runtime component chỉ được link khi dependency yêu cầu.

ALINK-45  FFI symbol phải giữ đúng ABI contract.

ALINK-46  Interposable symbol không được giả định local.

ALINK-47  LinkedImage phải được verify trước serialization.

ALINK-48  Link failure phải có provenance tới object/section/symbol/relocation.

ALINK-49  Deterministic mode phải tạo layout deterministic.

ALINK-50  Linker không được thay đổi semantic machine code ngoài relocation/thunk/relaxation được phép.

ALINK-51  LinkedImage là source of truth cho executable writers.

ALINK-52  Executable format writer không được thực hiện lại symbol resolution.

ALINK-53  Executable format writer không được thực hiện lại section GC.

ALINK-54  Executable format writer không được thực hiện lại relocation resolution.

ALINK-55  LinkedImage phải có thể serialize sang target format mà không cần quay lại compiler IR.

ALINK-56  Link graph phải biểu diễn đầy đủ dependency của synthetic sections.

ALINK-57  Fixed-point phases phải có termination detection.

ALINK-58  Incremental-link metadata không được làm thay đổi semantic output.

ALINK-59  Linker phải hỗ trợ runtime-free image.

ALINK-60  Linker architecture phải cho phép self-hosting, không cần external linker trong final Axiom toolchain.
```

---

# 303.43. Definition of Done

303 hoàn thành khi có thể thực hiện đầy đủ:

```text
a.o ─────┐
b.o ─────┤
c.o ─────┤
libA.a ──┤
libB.a ──┘
    ↓
 Axiom Linker
    ↓
 LinkedImage
```

với:

- symbol resolution
- archive extraction
- COMDAT
- section merging
- dead-section elimination
- address assignment
- relocation resolution
- relocation overflow detection
- thunk infrastructure
- basic relaxation infrastructure
- TLS layout
- basic dynamic-import/export abstraction
- deterministic linking
- link verification.

Và quan trọng nhất:

```text
.o/.obj
   ↓
Linker Core
   ↓
LinkedImage
```

phải trở thành **ranh giới kiến trúc rõ ràng**.

Sau 303, Axiom đã có chuỗi backend hoàn chỉnh ở mức:

```text
Source
  ↓
MIR
  ↓
Machine IR
  ↓
Machine Bytes
  ↓
Relocatable Object
  ↓
Linked Image
```

Bước tiếp theo sẽ xử lý **Executable/Image Writer**: biến `LinkedImage` thành PE/ELF/Mach-O executable/shared library và các image native tương ứng.