# PE-LINK-003 — Import Directory + IAT

Ta tiếp tục từ `hello.exe`. Đây là bước biến:

```text
Axiom-generated PE
        +
Kernel32.dll!ExitProcess
        ↓
Windows-loadable executable
```

Tôi đã kiểm tra lại PE format và Windows x64 ABI trước khi chốt phần này. PE32+ dùng **64-bit entries** cho Import Lookup Table/IAT; import directory có một entry cho mỗi DLL và kết thúc bằng entry null. IAT ban đầu có cùng nội dung với Import Lookup Table, sau đó Windows loader điền địa chỉ thực của các imported symbols. citeturn0search0

---

## 1. Kiến trúc import của Axiom

Không để frontend biết PE import.

```text
extern "system" fn ExitProcess(...)
            ↓
Typed HIR
            ↓
MIR
            ↓
LIR
            ↓
Machine IR
            ↓
ExternalCall("Kernel32.dll", "ExitProcess")
            ↓
COFF relocation / external symbol
            ↓
PE Linker
            ↓
Import Directory + INT + IAT
```

Tức là **import DLL là linker concern**, không phải language semantic.

---

# 2. FFI declaration

API phía Axiom:

```axiom
extern "system" fn ExitProcess(code: u32) -> never
```

`"system"` trên Windows x64 map tới Windows x64 ABI.

Theo ABI Windows x64, argument integer/pointer đầu tiên đi qua `RCX`, các argument tiếp theo qua `RDX`, `R8`, `R9`; return integer/pointer ở `RAX`. Caller cũng phải dành shadow space cho 4 register arguments. citeturn0search1turn0search9

Vì vậy:

```text
ExitProcess(code)
```

sẽ trở thành:

```text
MOV ECX, code
CALL imported_ExitProcess
```

---

# 3. Không gọi trực tiếp địa chỉ DLL

Machine code **không** được chứa:

```text
CALL 0x00007FF...
```

Địa chỉ DLL phụ thuộc process/load address.

Thay vào đó:

```text
CALL [IAT + offset]
```

IAT sau khi Windows loader xử lý sẽ chứa địa chỉ thật của `ExitProcess`.

---

# 4. Import symbol abstraction

Thêm vào linker IR:

```text
ImportSymbol {
    dll: DllId
    name: String
    ordinal: Option<u16>
}
```

Ví dụ:

```text
ImportSymbol {
    dll = "KERNEL32.dll"
    name = "ExitProcess"
}
```

---

# 5. Import identity

Không dùng string đơn:

```text
"ExitProcess"
```

làm identity.

Identity:

```text
ImportKey {
    dll
    symbol_kind
    name_or_ordinal
}
```

Ví dụ:

```text
("KERNEL32.dll", Name("ExitProcess"))
```

Điều này tránh collision khi nhiều DLL export cùng tên.

---

# 6. Import graph

```text
ImportGraph
 ├── Kernel32.dll
 │    ├── ExitProcess
 │    └── ...
 ├── User32.dll
 │    └── ...
 └── ...
```

MVP chỉ cần:

```text
Kernel32.dll
    ExitProcess
```

---

# 7. DLL canonicalization

Windows filesystem không phải nơi để Axiom suy đoán tùy tiện.

Axiom linker chuẩn hóa:

```text
kernel32.dll
Kernel32.dll
KERNEL32.DLL
```

thành một logical DLL identity.

Nhưng **tên lưu trong PE** nên được chọn deterministic, ví dụ:

```text
KERNEL32.dll
```

Không cần phụ thuộc casing mà filesystem hiện tại sử dụng.

---

# 8. Import Directory

PE Import Directory:

```text
IMAGE_IMPORT_DESCRIPTOR[]
```

mỗi DLL một descriptor.

Ví dụ:

```text
KERNEL32.dll
```

descriptor conceptually:

```text
ImportDescriptor {
    ImportLookupTableRVA
    TimeDateStamp
    ForwarderChain
    NameRVA
    ImportAddressTableRVA
}
```

Theo PE specification, descriptor cuối cùng phải là một entry toàn null. citeturn0search0

---

# 9. INT / Import Lookup Table

Với PE32+:

```text
INT:
    64-bit entry
    64-bit entry
    0
```

Ví dụ:

```text
INT
 ├── RVA → IMAGE_IMPORT_BY_NAME("ExitProcess")
 └── 0
```

PE specification xác nhận PE32+ dùng entry 64-bit cho Import Lookup Table. citeturn0search0

---

# 10. IAT

```text
IAT
 ├── thunk
 └── 0
```

Ban đầu:

```text
IAT[0] = same import descriptor reference
```

Windows loader sau đó thay bằng địa chỉ function thực tế. PE specification mô tả chính xác cơ chế này. citeturn0search0

---

# 11. IMAGE_IMPORT_BY_NAME

Import theo tên cần:

```text
Hint
Name[]
```

Conceptually:

```text
ImportByName {
    hint: u16
    name: null_terminated_ascii
}
```

Ví dụ:

```text
02 00
45 78 69 74 50 72 6F 63 65 73 73 00
```

`hint` không được Axiom tự đoán bừa. Với MVP có thể đặt:

```text
hint = 0
```

nếu loader vẫn xử lý import theo tên.

---

# 12. Ordinal import

Kiến trúc cũng phải hỗ trợ:

```text
ImportByOrdinal(u16)
```

PE32+ dùng bit cao nhất của thunk để phân biệt ordinal với RVA tới `IMAGE_IMPORT_BY_NAME`. citeturn0search0

Nhưng Axiom v0.1:

```text
name import = default
ordinal import = low-level linker feature
```

---

# 13. Import section

Có thể tạo:

```text
.idata
```

cho MVP.

Nhưng semantic model **không phụ thuộc tên `.idata`**.

```text
ImportSection {
    descriptors
    lookup_tables
    address_tables
    names
}
```

PE data directory sẽ trỏ tới vùng này.

Điều này quan trọng vì PE data directories xác định dữ liệu bằng RVA/size, không nên xây linker dựa trên assumption rằng directory nào cũng phải nằm trong section có một tên cố định. citeturn0search0

---

# 14. Layout `.idata`

Conceptual:

```text
.idata
│
├── Import Directory
│      ├── Kernel32 descriptor
│      └── NULL descriptor
│
├── Import Lookup Table
│      ├── ExitProcess
│      └── NULL
│
├── Import Address Table
│      ├── thunk
│      └── NULL
│
├── DLL name
│      "KERNEL32.dll"
│
└── Hint/Name
       hint
       "ExitProcess"
```

---

# 15. IAT alignment

IAT entries trên PE32+ là 8 byte.

Do đó:

```text
IAT alignment >= 8
```

Linker phải tự align.

---

# 16. `.idata` protection

Import metadata chứa read-only structures, nhưng **IAT là vùng loader có thể ghi** khi resolve imports.

Vì vậy đừng đơn giản hóa thành:

```text
.idata = READ
```

cho toàn bộ mọi dữ liệu.

Kiến trúc tốt hơn:

```text
ImportMetadata → READ
IAT            → READ | WRITE
```

và linker có thể đặt chúng ở vùng thích hợp.

Sau khi loader hoàn tất, hệ điều hành có thể áp dụng protection tương ứng theo image/load policy.

---

# 17. Tách Import Metadata và IAT

Thay vì:

```text
.idata = một blob
```

Axiom model:

```text
ImportImage {
    descriptors
    lookup_tables
    iat
    names
}
```

sau đó PE builder mới quyết định section layout.

---

# 18. Call sequence

Giả sử:

```axiom
ExitProcess(code)
```

Machine IR:

```text
MOV ECX, code
CALL imported_symbol
```

Instruction selector không cần biết:

```text
Kernel32.dll
```

Nó chỉ thấy:

```text
ExternalSymbol("__imp_ExitProcess")
```

---

# 19. IAT symbol

Linker tạo symbol nội bộ:

```text
__imp_ExitProcess
```

đại diện cho:

```text
IAT slot
```

Do đó:

```text
CALL [__imp_ExitProcess]
```

hoặc instruction form tương đương sẽ reference IAT.

---

# 20. Vì sao dùng `__imp_...`

Đây là một abstraction linker convention, **không phải Axiom language symbol**.

```text
ExitProcess
```

là foreign function.

```text
__imp_ExitProcess
```

là địa chỉ slot trong IAT.

Tách hai thứ này giúp linker rõ ràng.

---

# 21. Windows x64 call

Machine code conceptual:

```text
MOV ECX,EAX
CALL [RIP + disp32]
```

RIP-relative IAT access rất phù hợp x86-64.

Linker sẽ resolve:

```text
disp32
```

tới IAT slot.

---

# 22. Relocation

Trong `.obj`:

```text
CALL [RIP + __imp_ExitProcess]
```

có relocation:

```text
REL32(__imp_ExitProcess)
```

PE linker sau khi layout:

```text
.text
...
.idata
...
```

sẽ biết:

```text
source RVA
IAT RVA
```

và patch displacement.

---

# 23. Không cần absolute relocation cho IAT call

Ưu tiên:

```text
RIP-relative → IAT
```

thay vì:

```text
absolute 64-bit address
```

Điều này giảm nhu cầu base relocation cho code import-call path.

---

# 24. Import deduplication

Nếu source:

```axiom
fn a() {
    ExitProcess(1)
}

fn b() {
    ExitProcess(2)
}
```

không tạo:

```text
IAT[0] ExitProcess
IAT[1] ExitProcess
```

Mà:

```text
IAT[0] ExitProcess
```

cả hai call cùng dùng slot.

---

# 25. Deterministic ordering

Import DLL:

```text
sort by canonical DLL identity
```

Function:

```text
sort by import symbol identity
```

Ví dụ:

```text
Kernel32.dll
    ExitProcess
    GetStdHandle
    WriteFile
```

Như vậy cùng source luôn tạo cùng IAT layout.

---

# 26. Import library không nằm trong compiler core

Axiom có thể hỗ trợ:

```text
std.windows
```

với declarations:

```axiom
extern "system" fn ExitProcess(...)
```

Compiler chỉ phát ra external symbol.

Linker mới biết:

```text
ExitProcess → KERNEL32.dll
```

Thông tin mapping có thể nằm trong platform library metadata.

---

# 27. Platform library metadata

Ví dụ conceptually:

```text
windows.api.axmeta
```

```text
extern {
    ExitProcess {
        dll: "KERNEL32.dll"
        symbol: "ExitProcess"
    }
}
```

Nhưng đây không phải source syntax bắt buộc.

Có thể compiler intrinsic metadata sinh ra từ standard library interface.

---

# 28. FFI declaration không nên tự động đoán DLL

Sai:

```axiom
extern "system" fn ExitProcess(...)
```

→ compiler tự tìm Internet/Windows SDK.

Đúng:

```text
Axiom platform library
        ↓
foreign declaration
        ↓
link metadata
        ↓
PE linker
```

Compiler phải deterministic/offline.

---

# 29. Import error

Nếu:

```text
extern ExitProcess
```

nhưng không có DLL mapping:

```text
AX_LINK_0101
foreign symbol has no platform import mapping
```

Không tự đoán.

---

# 30. DLL missing

Axiom linker không cần DLL thật tồn tại trên máy build để tạo import table.

Ví dụ build cross-target Windows từ Linux:

```text
KERNEL32.dll
```

chỉ là import identity.

Không cần load DLL.

---

# 31. Đây là điều quan trọng cho cross-compilation

```text
Linux host
   ↓
Axiom compiler
   ↓
Windows PE
   ↓
imports KERNEL32.dll
```

không cần chạy Windows DLL trong quá trình link.

---

# 32. Import policy

Target configuration:

```text
WindowsTarget {
    import_resolution = Explicit
}
```

Không:

```text
search random DLLs
```

---

# 33. `ExitProcess` prototype

Axiom declaration:

```axiom
extern "system"
fn ExitProcess(code: u32) -> never
```

Mặc dù Windows API dùng `UINT`, Axiom mapping:

```text
UINT → u32
```

là explicit FFI type mapping.

---

# 34. Startup stack contract

Startup:

```text
__axiom_start:
    sub rsp, 40
    call __axiom_main
    mov ecx, eax
    call [rip + __imp_ExitProcess]
    ud2
```

Windows ABI yêu cầu caller reserve 32-byte shadow store; stack alignment cũng phải được duy trì ở các vùng code không phải prolog/epilog. citeturn0search1

Do đó `40` ở startup phải được sinh từ **ABI frame calculation**, không hard-code rải rác.

---

# 35. ABI lowering phải sinh startup frame

```text
Startup IR
    ↓
Windows ABI Lowering
    ↓
FrameLayout
    ↓
Machine IR
```

Không viết tay:

```text
sub rsp, 40
```

trong linker.

---

# 36. Startup trở thành một compilation unit bình thường

Đây là một kiến trúc rất quan trọng:

```text
startup.ax
    ↓
Lexer
    ↓
Parser
    ↓
HIR
    ↓
MIR
    ↓
LIR
    ↓
x86 backend
    ↓
startup.obj
```

Không có "special compiler backend magic" ngoài việc attribute xác định platform entry.

---

# 37. Điều này giúp self-host

Khi compiler được viết bằng Axiom:

```text
Axiom compiler
     ↓
startup.ax
     ↓
Axiom compiler
```

không cần duy trì một bản startup assembly riêng.

---

# 38. Import metadata cũng compile-time

Platform library:

```text
std/windows
```

có:

```text
ExitProcess
```

→ compiler tạo FFI symbol.

Linker đọc metadata:

```text
ExitProcess
→ KERNEL32.dll
```

→ ImportGraph.

---

# 39. Import verifier

Thêm:

```text
PEImportVerifier
```

kiểm:

```text
Import descriptor valid
INT RVA valid
IAT RVA valid
DLL name valid
Hint/name RVA valid
all tables null-terminated
IAT entry width = 8
PE32+ high-bit ordinal encoding valid
```

---

# 40. Import invariants

```text id="AIMPORT-20"
Every imported function has exactly one logical ImportKey.

AIMPORT-21
Import identity includes DLL identity.

AIMPORT-22
Duplicate imports are deduplicated.

AIMPORT-23
Import Lookup Table is null terminated.

AIMPORT-24
Import Address Table is null terminated.

AIMPORT-25
PE32+ thunk entries are 64-bit.

AIMPORT-26
Import Directory has a null terminator descriptor.

AIMPORT-27
IAT slots are distinct from foreign function semantic symbols.

AIMPORT-28
IAT addresses are resolved by the Windows loader.

AIMPORT-29
Compiler does not hard-code foreign function addresses.

AIMPORT-30
DLL mapping is explicit and deterministic.

AIMPORT-31
Import layout is deterministic.

AIMPORT-32
RIP-relative IAT references are preferred on x86-64.

AIMPORT-33
Import metadata is independent of source language semantics.

AIMPORT-34
Delay-load imports are not required for MVP.
```

PE specification xác nhận cấu trúc descriptor/INT/IAT và cơ chế loader điền địa chỉ thực vào IAT. citeturn0search0

---

# 41. `hello.exe` bây giờ có cấu trúc

```text
hello.exe
│
├── DOS Header
├── DOS Stub
├── PE Signature
├── COFF Header
├── PE32+ Optional Header
├── Section Table
│
├── .text
│    ├── __axiom_start
│    └── __axiom_main
│
├── .rdata
│    └── import names / metadata
│
├── .idata
│    ├── Import Directory
│    ├── INT
│    ├── IAT
│    ├── "KERNEL32.dll"
│    └── "ExitProcess"
│
└── ...
```

---

# 42. Test end-to-end

Source:

```axiom
fn main() -> i32 {
    42
}
```

Compiler tạo:

```text
hello.obj
startup.obj
```

Linker:

```text
hello.obj
+
startup.obj
+
ImportGraph:
    KERNEL32.dll!ExitProcess
```

→

```text
hello.exe
```

---

# 43. Expected execution

```text
Windows Loader
      ↓
maps hello.exe
      ↓
loads KERNEL32.dll
      ↓
resolves ExitProcess
      ↓
writes actual address into IAT
      ↓
PE entry
      ↓
__axiom_start
      ↓
__axiom_main
      ↓
EAX = 42
      ↓
ECX = 42
      ↓
CALL [IAT.ExitProcess]
      ↓
process exits with 42
```

Cơ chế loader resolve import thông qua Import Directory/IAT là một phần chuẩn của PE image. citeturn0search0

---

# 44. Đây là milestone `hello.exe`

Từ đây ta có acceptance criterion thực sự:

```text
AXIOM-BOOT-001

Given:

fn main() -> i32 {
    42
}

Build:

axiom build hello.ax --target x86_64-windows

Must produce:

hello.exe

Must execute on Windows.

Must exit with:

42

Must not depend on:

MSVC
MSVC CRT
Clang
LLVM
MinGW
GNU ld
NASM
MASM
external assembler
external linker
```

Đây là **mốc bootstrap native đầu tiên của Axiom**.

---

# 45. Nhưng chưa gọi là production Windows backend

Còn thiếu một thứ rất quan trọng:

```text
.pdata
.xdata
```

Windows x64 yêu cầu unwind metadata cho non-leaf functions; Microsoft mô tả `.pdata` chứa function table và `.xdata` chứa unwind information, đồng thời prologue/epilogue có những hạn chế để hệ thống unwind có thể phục hồi trạng thái. Leaf functions có thể không cần pdata/xdata. citeturn0search1

Vì vậy roadmap ngay sau `hello.exe` là:

```text
PE-UNWIND-001
        ↓
Windows x64 prologue model
        ↓
UNWIND_INFO
        ↓
.pdata/.xdata
        ↓
stack walking
        ↓
debugger
        ↓
panic/unwind infrastructure
```

---

# 46. Và có một chỉnh sửa kiến trúc quan trọng

**Không nên chờ đến sau Linux mới làm unwind.**

Thứ tự mới:

```text
LI    Encoder                         ✅
LII   COFF Writer                     → 
LIII  PE Linker                       →
LIV   Windows Startup                 →
LV    Import/IAT                      →
LVI   hello.exe                       →
LVII  Windows Unwind (.pdata/.xdata)
LVIII Windows Debug/CodeView
LIX   ELF64 Writer
LX    Linux Linker
```

Sau `LVII`, backend Windows đã có nền tảng đủ nghiêm túc để dùng làm **bootstrap target đầu tiên**.

Và song song với đó, ta cần khóa một nguyên tắc lớn cho Axiom:

> **Mọi thứ cần thiết để tạo native executable phải nằm trong Axiom toolchain; platform API chỉ là external ABI dependency của chương trình, không phải compiler dependency.**

Đây chính là ranh giới giúp mục tiêu **“không phụ thuộc compiler/linker/toolchain bên thứ ba”** khả thi mà vẫn sử dụng được Windows API bình thường.