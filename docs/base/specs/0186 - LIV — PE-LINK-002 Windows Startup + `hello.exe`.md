# LIV — PE-LINK-002: Windows Startup + `hello.exe`

Ta tiếp tục. Tôi vừa kiểm tra lại các điểm Windows-specific vì đây là chỗ nếu sai ABI thì `.exe` có thể được tạo ra nhưng crash ngay khi chạy.

Microsoft xác nhận PE32+ dùng `AddressOfEntryPoint` là **RVA của entry point**, còn Windows x64 ABI dùng `RCX/RDX/R8/R9` cho 4 tham số integer/pointer đầu tiên và caller phải dành **32-byte shadow space**. citeturn0search0turn0search2

## 1. Chốt lại startup architecture

Không cho PE entry trỏ thẳng vào `main`.

Ta dùng:

```text id="q6v2r8"
PE Entry
   ↓
axiom_start
   ↓
axiom_main
   ↓
ExitProcess
```

Trong đó:

```text
main() -> i32
```

là API cấp ngôn ngữ.

Còn:

```text
axiom_start()
```

là platform startup ABI.

Windows xác định entry point thông qua `AddressOfEntryPoint`; đây là RVA tương đối với image base. citeturn1search8

---

# 2. Không cần CRT

Mục tiêu của Axiom:

```text id="f2c7s1"
Axiom
  ├── Compiler
  ├── Axiom linker
  └── minimal Windows startup
```

Không:

```text
Axiom
  ↓
MSVC CRT
  ↓
mainCRTStartup
  ↓
main
```

Microsoft cũng mô tả `mainCRTStartup` là entry point mặc định do CRT cung cấp cho ứng dụng console. Axiom sẽ tự cung cấp startup tương đương, nhưng không phụ thuộc CRT. citeturn1search2

---

# 3. Startup ABI

Ta định nghĩa nội bộ:

```text id="m1k9x4"
extern "axiom.windows.startup"
fn axiom_start() -> never
```

và:

```text
extern "axiom"
fn axiom_main() -> i32
```

`axiom_start` **không phải API công khai của ngôn ngữ**.

Nó là compiler-generated symbol.

---

# 4. Tên symbol

Không dùng trực tiếp:

```text
main
```

để tránh collision.

Dùng:

```text id="n8h4s6"
__axiom_start
__axiom_main
```

hoặc tốt hơn:

```text id="2c8r7v"
__axiom$start
__axiom$main$<module-id>
```

Nhưng vì COFF symbol có quy tắc tên riêng, compiler nên có:

```text
SymbolMangler
```

riêng.

---

# 5. Main không nhất thiết phải exported

```axiom id="t0m7k1"
fn main() -> i32 {
    42
}
```

không có nghĩa:

```text
PE export: main
```

Nó chỉ là:

```text
semantic entry declaration
```

Linker tìm:

```text
axiom_main
```

sau name mangling.

---

# 6. Startup code

Conceptual x86-64:

```text id="4q9s7x"
__axiom_start:
    ; establish startup call frame
    ...
    call __axiom_main
    ; return value in EAX
    ...
    call ExitProcess
```

`ExitProcess(UINT)` nhận exit code và kết thúc process. Windows documentation xác nhận exit code được truyền qua tham số của `ExitProcess`. citeturn1search0

---

# 7. Không gọi `ExitProcess` bằng magic compiler opcode

Đây là điểm quan trọng.

Compiler không được có:

```text
EXIT_PROCESS
```

trong x86 backend.

Thay vào đó:

```text id="a7n3c5"
std.windows.process.ExitProcess
```

là FFI declaration:

```text
extern "system" fn ExitProcess(code: u32) -> never
```

Compiler chỉ xử lý:

```text
CALL ExitProcess
```

PE linker xử lý import.

Như vậy Windows API không trở thành một phần của Core language.

---

# 8. Vì vậy `.exe` đầu tiên có import

Đây là một điều chỉnh nhỏ nhưng quan trọng so với mục tiêu "static PE tối giản".

Nếu muốn `main() -> i32` kết thúc đúng chuẩn Windows, startup có thể gọi `ExitProcess`; khi đó executable cần import `Kernel32.dll`. Microsoft xác nhận `ExitProcess` nằm trong `Kernel32.dll`. citeturn1search0

Do đó milestone đầu tiên thực tế là:

```text id="q9m3s5"
hello.exe
 ├── Axiom-generated .text
 └── Kernel32.dll import
```

**Không có CRT.**

Đây vẫn hoàn toàn đạt mục tiêu "không phụ thuộc compiler/runtime bên thứ ba".

---

# 9. Windows x64 call ABI

Startup gọi:

```text
__axiom_main()
```

không có argument.

Sau khi `main` trả:

```text
EAX = exit code
```

Startup cần gọi:

```text
ExitProcess(exit_code)
```

Windows x64 ABI quy định tham số integer/pointer đầu tiên ở `RCX`. citeturn0search2

Vì vậy:

```text id="4c9v2x"
MOV ECX, EAX
CALL ExitProcess
```

---

# 10. Shadow space

Caller phải dành 32 bytes shadow/home space cho callee. citeturn0search2

Do đó startup không nên đơn giản:

```text
CALL main
```

mà phải có stack layout phù hợp.

Ta đặt:

```text id="m3w8k2"
32 bytes shadow space
+
alignment padding
```

trước call.

---

# 11. Startup frame

Thiết kế MVP:

```text id="x4k6p1"
__axiom_start:

    sub rsp, 40

    call __axiom_main

    mov ecx, eax
    call ExitProcess

    ud2
```

`40 = 32 shadow + 8 alignment adjustment`.

Con số chính xác phải được kiểm chứng bằng invariant stack-alignment của Windows ABI tại điểm `CALL`, không được hard-code ở nhiều nơi.

---

# 12. `never`

`ExitProcess`:

```text
-> never
```

vì nó không trở lại theo semantics của API.

Nếu compiler vẫn nhìn thấy fallthrough:

```text id="z7q2m5"
call ExitProcess
ud2
```

`UD2` chỉ là defensive unreachable instruction.

---

# 13. Startup không phải runtime

Điều này rất quan trọng đối với triết lý Axiom:

```text id="h6s9k3"
Startup ≠ Runtime
```

Startup chỉ làm:

```text
OS entry
 ↓
Axiom main
 ↓
process termination
```

Không tự động:

- GC
- allocator
- async executor
- thread pool
- reflection
- Unicode runtime
- exception runtime

---

# 14. Hosted profile

Ta định nghĩa:

```text id="c3n8w4"
@profile("windows-hosted")
```

conceptually:

```text
Windows Hosted
    ↓
__axiom_start
    ↓
main
    ↓
ExitProcess
```

---

# 15. Freestanding profile

Sau này:

```text id="j4p7s2"
@profile("windows-freestanding")
```

cho phép programmer tự kiểm soát entry:

```axiom
@entry
unsafe fn start() -> never {
    ...
}
```

Compiler không thêm:

```text
main
ExitProcess
```

---

# 16. Không nên dùng `@entry` cho `main`

Chốt:

```text id="e2h6k9"
fn main()
```

là application entry semantic.

```text
@entry
```

là low-level platform entry.

Hai khái niệm khác nhau.

---

# 17. PE Subsystem

CLI mặc định:

```text
IMAGE_SUBSYSTEM_WINDOWS_CUI = 3
```

GUI:

```text
IMAGE_SUBSYSTEM_WINDOWS_GUI = 2
```

Microsoft PE specification xác định các giá trị này trong PE Optional Header. citeturn0search0

Axiom build metadata:

```text id="b8m2r5"
[subsystem]
kind = "console"
```

hoặc:

```text
kind = "windows"
```

---

# 18. Không suy luận subsystem từ source

Không làm:

```text
if main has console calls
    => console subsystem
```

Đây là build configuration.

---

# 19. Linker config

```text id="d4x7m1"
PeImageConfig {
    subsystem
    image_base
    section_alignment
    file_alignment
    entry_symbol
    dll_characteristics
}
```

---

# 20. PE security defaults

MVP bật:

```text id="r8c5q2"
NX_COMPAT
DYNAMIC_BASE
```

nếu relocation table đầy đủ.

PE specification định nghĩa `IMAGE_DLLCHARACTERISTICS_NX_COMPAT` và `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` cho image. citeturn0search0

Điều này tốt hơn việc mặc định tạo executable với code/data tùy tiện executable/writable.

---

# 21. Entry symbol resolution

Linker:

```text id="f7s3d9"
entry = "__axiom_start"
```

resolve:

```text
__axiom_start
    ↓
.text + offset
    ↓
RVA
```

Sau đó:

```text
OptionalHeader.AddressOfEntryPoint = RVA
```

đúng với PE semantics. citeturn0search0

---

# 22. Không hard-code entry RVA

Sai:

```text
AddressOfEntryPoint = 0x1000
```

Đúng:

```text
entry_symbol
 ↓
final section layout
 ↓
entry RVA
```

---

# 23. Import subsystem

Thêm:

```text id="v2m5x8"
ImportGraph
```

```text
ImportDLL {
    name
    symbols[]
}
```

Ví dụ:

```text
Kernel32.dll
    ExitProcess
```

---

# 24. IAT

PE image cần import structures.

Kiến trúc:

```text id="q8n4s2"
.rdata / .idata-like region
    ↓
Import Directory
    ↓
Import Descriptor
    ↓
ILT / INT
    ↓
IAT
    ↓
DLL + symbol
```

Không bắt buộc section phải tên `.idata`; PE specification lưu ý data directories trỏ tới dữ liệu theo RVA/size và không nên giả định mọi directory luôn bắt đầu ở một section tên cố định. citeturn0search0

---

# 25. Vì vậy Axiom không nên phụ thuộc section-name magic

Thay vì:

```text
if section.name == ".idata"
```

linker nên có:

```text id="n5r8c2"
Directory {
    kind: Import
    rva
    size
}
```

PE builder quyết định section placement.

---

# 26. Import library chưa cần

Ta có thể trực tiếp tạo import descriptor từ:

```text
Kernel32.dll
ExitProcess
```

Do đó milestone đầu:

```text
Axiom source
 ↓
COFF
 ↓
Axiom linker
 ↓
PE Import Directory
```

Không cần `.lib`.

`.lib` sẽ là milestone sau để tương thích toolchain bên ngoài.

---

# 27. Startup object

Không nên inject startup assembly sau encoder.

Tạo một object bình thường:

```text id="x9s3m7"
axiom_windows_startup.obj
```

chứa:

```text
__axiom_start
```

và reference:

```text
__axiom_main
ExitProcess
```

Sau đó linker link:

```text
user.obj
+
startup.obj
```

Đây là kiến trúc rất sạch.

---

# 28. Nhưng startup.obj phải được compiler sinh

Không dùng `.asm` external.

Có hai lựa chọn:

### A

Startup được xây bằng Axiom:

```text
startup.ax
```

### B

Compiler backend tạo Machine IR trực tiếp.

Tôi chọn **A**.

```text id="p3k7w2"
std/platform/windows/startup.ax
```

sau này self-host compiler có thể tự compile startup.

---

# 29. Startup code conceptual

```axiom
extern "system"
fn ExitProcess(code: u32) -> never

extern "axiom"
fn __axiom_main() -> i32

@platform_entry
unsafe fn __axiom_start() -> never {
    let code = __axiom_main()
    ExitProcess(code as u32)
}
```

`@platform_entry` là compiler-internal attribute, chưa public Core syntax.

---

# 30. Tại sao `unsafe`?

Không phải vì `main()` unsafe.

Mà vì:

```text
__axiom_start
```

là boundary giữa:

```text
Windows loader
```

và:

```text
Axiom semantic world
```

Platform startup chịu trách nhiệm về ABI preconditions.

---

# 31. `main` vẫn safe

```axiom
fn main() -> i32 {
    42
}
```

hoàn toàn safe.

Compiler đảm bảo startup contract.

---

# 32. First end-to-end artifact

Source:

```axiom
fn main() -> i32 {
    42
}
```

Link graph:

```text
hello.ax
    │
    ├── __axiom_main
    │
    └── startup.ax
          │
          ├── __axiom_start
          └── ExitProcess
```

---

# 33. Final PE graph

```text
hello.exe

PE Entry
   │
   ▼
__axiom_start
   │
   ▼
__axiom_main
   │
   ▼
EAX = 42
   │
   ▼
ECX = 42
   │
   ▼
ExitProcess(42)
```

Windows process exit code sẽ là `42`; Microsoft mô tả exit status có thể đến từ `ExitProcess` hoặc return value của `main`/`WinMain`. citeturn1search6turn1search10

---

# 34. Acceptance test

```text id="k3m7q1"
axiom build hello.ax
```

phải tạo:

```text
build/windows-x64/debug/hello.exe
```

Sau đó:

```text
hello.exe
```

và kiểm tra:

```text
$LASTEXITCODE
```

kỳ vọng:

```text
42
```

---

# 35. Không kiểm tra bằng việc "chạy được" duy nhất

Harness phải kiểm tra cả:

```text id="w9c2m5"
PE signature
Machine = AMD64
PE32+ magic
Subsystem = CUI
Entry RVA valid
.text executable/readable
.rdata readable
.data writable
IAT valid
Import Directory valid
Kernel32.dll present
ExitProcess imported
```

---

# 36. PE verifier

Thêm:

```text id="u5x8k2"
compiler/linker/pe64/
├── headers.ax
├── sections.ax
├── directories.ax
├── imports.ax
├── reloc.ax
├── layout.ax
├── builder.ax
├── verifier.ax
└── tests/
```

`PEVerifier` phải chạy trước khi file được xuất.

---

# 37. PE invariants mới

```text id="APE-20"
PE image uses PE32+ for x86-64.

APE-21
Machine is AMD64.

APE-22
Entry point is represented as RVA.

APE-23
RVA, VA and file offsets are distinct semantic types.

APE-24
SectionAlignment and FileAlignment are distinct.

APE-25
AddressOfEntryPoint resolves to a valid executable section.

APE-26
Subsystem is explicit.

APE-27
Import directories are explicit data-directory entries.

APE-28
IAT references are fully represented.

APE-29
Required imports are resolved by name.

APE-30
No CRT is required by the Axiom startup model.

APE-31
Startup is a linkable object component.

APE-32
Application main is distinct from OS entry.

APE-33
Hosted startup terminates through the platform process-exit mechanism.

APE-34
Freestanding profiles may provide their own entry.

APE-35
Default executable sections obey W^X policy.

APE-36
PE generation is deterministic.

APE-37
Generated PE is self-verified before emission.
```

---

# 38. Một điều chỉnh quan trọng đối với roadmap

Ban đầu ta đặt:

```text
PE-LINK-001
static PE
```

Nhưng thực tế Windows hosted executable cần startup/process termination.

Vì vậy chia đúng hơn:

```text
PE-LINK-001
    PE image builder

PE-LINK-002
    Axiom startup

PE-LINK-003
    Import/IAT

PE-LINK-004
    hello.exe end-to-end
```

Trong đó `PE-LINK-001` có thể tạo một PE image tối giản từ object, còn `PE-LINK-002..004` biến nó thành executable application hoàn chỉnh.

---

# 39. Và một điểm rất đáng chú ý

Windows x64 yêu cầu unwind metadata cho các function có prolog/epilog nhất định và exception/unwind support dùng function table; PE specification mô tả `.pdata` chứa function table với Begin RVA, End RVA và Unwind Information. citeturn0search0turn0search1

**Không nên giả vờ rằng Axiom đã hỗ trợ unwind chỉ vì `.exe` chạy được.**

MVP:

```text
panic = abort
```

và compiler có thể giới hạn startup/function frame complexity.

Sau khi `hello.exe` chạy:

```text
PE-UNWIND-001
```

sẽ xây:

```text
.pdata
.xdata
UNWIND_INFO
```

để debugger, stack walking và Windows exception/unwind hoạt động đúng.

---

# 40. Trạng thái hiện tại

Ta đã đi từ:

```text
Source
 ↓
MIR
 ↓
LIR
 ↓
x86 ISel
 ↓
Register Allocation
 ↓
Frame
 ↓
Machine IR
 ↓
Encoder
 ↓
COFF
```

và hiện đang hoàn thiện:

```text
COFF
 ↓
PE32+
 ↓
Windows startup
 ↓
Kernel32 import
 ↓
hello.exe
```

**Milestone kế tiếp là PE-LINK-003 — Import/IAT + Kernel32.dll**, rồi ghép thành `hello.exe` chạy thật trên Windows. Sau đó mới chuyển sang **Windows unwind `.pdata/.xdata`**, rồi **ELF64/Linux**, thay vì tiếp tục mở rộng language features khi native backend cơ bản chưa hoàn chỉnh.