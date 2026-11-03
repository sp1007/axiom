# SPEC-82 — Canonical Linux ELF64 Dynamic Linking, PIE, GOT/PLT, Shared Objects (`.so`) & `libc`/`dlopen` Interoperability Specification

- **Status:** draft (T657, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-091`), `spec/SPEC-26-windows-artifact-kinds.md`, `spec/SPEC-27-separate-compilation-linker-v2.md`, `spec/SPEC-50-unsafe-ub-ffi.md`, `spec/SPEC-52-freestanding-runtime-composition.md`, `spec/SPEC-54-panic-unwinding.md`, `spec/SPEC-56-module-relative-bindings.md`, `spec/SPEC-80-linux-x86-64-elf-static.md`, `spec/SPEC-81-target-desc-isa-conformance.md`, `0164`, `0192`, `0197` (`AELF-20..45`, `ATLS-20..25`), `0217`, `0220`, `tasks/0369`, `tasks/0518` (`AMACHINE-72..79`), `tasks/0521` (`AARM-51..52`), `tasks/0522` (`ABACKEND-36..38`), `tasks/0524` (`ABACKEND-82..83`), `tasks/0563` (§304.1–304.13)
- **Covers:** `REQ-TGT-061`, `REQ-TGT-062`, `REQ-TGT-063`, `REQ-TGT-064`, `REQ-TGT-065` (and specifies the E16.2 contract for `T658`, `T659`: `REQ-TGT-066`, `REQ-TGT-067`, `REQ-TGT-068`, `REQ-TGT-145`, `REQ-TGT-146`, `REQ-TGT-182`, `REQ-TGT-183`, `REQ-TGT-184`, `REQ-TGT-307`, `REQ-TGT-308`)
- **Consumers:** `compiler/target/x64/pic`, `compiler/obj/elf_dyn`, `compiler/link/elf_dyn`, `std/sys/linux_dl`, `T658`, `T659`

## Tóm tắt

Tài liệu `SPEC-82` chốt đặc tả chuẩn cho liên kết động ELF64 trên Linux x86-64 (Epic `E16.2`), mở rộng đường ống ELF tĩnh của `SPEC-80` sang mã độc lập vị trí (`PIC`/`PIE`), bảng `GOT`/`PLT`, thư viện chia sẻ (`.so`) và tương tác `libc`/`dlopen` mà không đưa chi tiết định dạng ELF vào tầng ngữ nghĩa ngôn ngữ (`0197 §1–42`):
1. **Tách biệt ELF tĩnh (`ET_EXEC`, `SPEC-80`) và ELF động (`ET_DYN`, `AXS-ELFD-001`..`010`):** Phân tách rõ chế độ liên kết (`Static`, `Pie`, `DynamicExe`, `SharedObject`) như chính sách của trình liên kết chứ không phải tính năng cú pháp ngôn ngữ (`AELF-20..26`); tệp thực thi `PIE` phát sinh `e_type = ET_DYN` tại cơ sở tương đối `0x0` kèm `PT_PHDR`, `PT_INTERP` (`/lib64/ld-linux-x86-64.so.2`) và `DF_1_PIE`; thư viện chia sẻ `--kind dll` phát sinh `lib<name>.so` (`ET_DYN`, `e_entry = 0`) kèm `DT_SONAME`; cố định kích thước lệnh, giãn nhánh (`branch relaxation`), căn chỉnh mã máy và nguồn gốc gỡ lỗi trước khi ghi đối tượng (`REQ-TGT-061..065`).
2. **Sinh mã độc lập vị trí (`PIC`), hạ tầng `GOT`/`PLT`, định vị lại động và TLS (`AXS-ELFD-011`..`021`):** Địa chỉ cục bộ dùng độ lệch `RIP`-relative (`R_X86_64_PC32`); địa chỉ ký hiệu ngoại hoặc có thể bị chiếm quyền dùng nạp gián tiếp qua `.got` (`R_X86_64_GOTPCREL` / `R_X86_64_REX_GOTPCRELX`, cho phép giãn `mov` $\rightarrow$ `lea` khi phân giải cục bộ, `REQ-TGT-066`); lời gọi hàm ngoại đi qua cầu nhảy `.plt`/`.got.plt` 16 byte (`R_X86_64_PLT32`); phát sinh `.rela.dyn` (`R_X86_64_RELATIVE`, `R_X86_64_GLOB_DAT`, `R_X86_64_64`) và `.rela.plt` (`R_X86_64_JUMP_SLOT`), cấm tuyệt đối định vị lại trên phân đoạn mã `DT_TEXTREL`, bảo toàn đồng nhất địa chỉ hàm qua `.got` (`AMACHINE-79`, `REQ-TGT-067..068`), và hạ tầng TLS theo mô hình `Local-Exec` / `Initial-Exec` (`R_X86_64_GOTTPOFF`) / `General-Dynamic` (`R_X86_64_TLSGD`, `REQ-TGT-145..146`, `REQ-TGT-182`).
3. **Các phân đoạn động ELF64, `PT_GNU_RELRO` và kiểm soát hiển thị/phiên bản ký hiệu (`AXS-ELFD-022`..`035`):** Quy định bố cục segment `PT_LOAD` (`R`, `RX`, `RW` tuân thủ W^X), `PT_DYNAMIC`, mặc định Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`) so với gắn kết lười (`--lazy-plt`), `PT_GNU_STACK` (`PF_R | PF_W`), `.dynsym` tách rời `.symtab`, bảng băm Bloom `.gnu.hash`, `.dynamic`, `.init_array`/`.fini_array`, mặc định ẩn ký hiệu nội bộ (`STV_HIDDEN`) và chỉ xuất `STV_DEFAULT` cho `@export`, cùng bảng phiên bản ký hiệu GNU (`SHT_GNU_versym`, `SHT_GNU_verneed`, `SHT_GNU_verdef`).
4. **Tương tác `libc`, `libm`, `libpthread` và `std.sys.linux_dl` (`dlopen`/`dlsym`/`dlclose`/`dlerror`, `AXS-ELFD-036`..`045`):** Giữ `libc` là thư viện FFI nền tảng tùy chọn thay vì phụ thuộc bắt buộc của Core (`0197 §30`, `0220 §2`), đồng thời hỗ trợ liên kết động đầy đủ với `libc.so.6`/`libm.so.6`/`libpthread`/`libdl`, đọc kịch bản liên kết GNU stub (`GROUP ( /lib/.../libc.so.6 )`), và nạp mô-đun thời gian chạy qua `std.sys.linux_dl`.

---

## 1. Static vs Dynamic ELF Separation, `PIE` Executables & Shared Objects (`AXS-ELFD-001`..`010`)

**AXS-ELFD-001 — Link Mode Orthogonality & Source-Semantic Independence.** Dynamic linking, Position-Independent Executables (`PIE`), and shared objects (`.so`) are target/linker execution policies (`LinkMode`), never source-language constructs (`0197 §1, §8–10, AELF-20..21, AELF-26, AELF-34, AELF-44..45`). Axiom exposes no `@pie` or shared-object type modifier in Core syntax, and dynamic linking never alters source-level function call semantics, ownership rules, `view<T>`/`mut_view<T>` capability checks, or deterministic `Drop` order (`0197 §8, AELF-44..45`). `compiler/link/elf_dyn` supports four orthogonal link modes on `x86_64-linux`:
- `LinkMode.Static` (`--static`, or default `--kind exe` when zero dynamic libraries are referenced and `--pie` is not requested): emits `ET_EXEC` at fixed base `0x400000` (`SPEC-80 AXS-ELFS-030..034`).
- `LinkMode.Pie` (`--pie`, or default `--kind exe` when `-l<so>` / `@link("<so>")` resolves to a shared object): emits a position-independent `ET_DYN` executable (`AXS-ELFD-003`).
- `LinkMode.StaticPie` (`--static-pie`): emits an `ET_DYN` executable without `PT_INTERP` that self-applies `R_X86_64_RELATIVE` fixups in `_start`.
- `LinkMode.SharedObject` (`--kind dll`): emits an `ET_DYN` shared library `lib<name>.so` (`AXS-ELFD-004`). [0197 §1, §8–10, AELF-20..21, AELF-26, AELF-34, AELF-44..45; tasks/0563 §304.3]

**AXS-ELFD-002 — `ET_EXEC` vs `ET_DYN` ELF64 Header & Relative Base `0x0` Contract.** Whereas a static executable (`SPEC-80 AXS-ELFS-030`) uses `e_type = ET_EXEC (2)` with fixed virtual addresses starting at `0x400000`, every `PIE` executable and `.so` shared library uses `e_type = ET_DYN (3)`, `e_machine = EM_X86_64 (62)`, `e_version = 1`, `e_phoff = 64`, `e_phentsize = 56`, and `e_shentsize = 64`, linked at relative virtual base address `0x0` (`0197 §10`, `tasks/0563 §304.7–304.8`). At runtime, the Linux kernel or dynamic loader (`ld-linux-x86-64.so.2`) chooses a 4 KiB page-aligned ASLR load bias $B$ and maps every `PT_LOAD` segment at runtime virtual address $\text{VA} = B + \text{p\_vaddr}$. [0197 §10, AELF-26, AELF-33; tasks/0563 §304.7–304.8]

**AXS-ELFD-003 — Position-Independent Executables (`PIE`, `PT_PHDR`, `PT_INTERP`, `DF_1_PIE`).** A `PIE` executable (`LinkMode.Pie`) is an `ET_DYN` image distinguished from a shared library by four mandatory properties (`0197 §10, §29, §36`, `tasks/0563 §304.8, §304.11–304.12`):
1. `Elf64_Ehdr.e_entry` is non-zero and set to the relative virtual address (`RVA`) of the synthesized PIC `_start` stub (`AXS-ELFD-033`).
2. Program header 0 is `PT_PHDR (6)` (`p_flags = PF_R = 0x4`, `p_offset = 64`, `p_vaddr = 64`, `p_filesz = p_memsz = e_phnum * 56`, `p_align = 8`).
3. Program header 1 (in dynamically linked `PIE` images) is `PT_INTERP (3)` (`p_flags = PF_R = 0x4`, `p_align = 1`) pointing to the `.interp` section containing the NUL-terminated system dynamic loader path, defaulting on `x86_64-linux` to `"/lib64/ld-linux-x86-64.so.2\0"` (28 bytes, overridable via `--dynamic-linker <path>`).
4. `.dynamic` includes `DT_FLAGS_1 (0x6ffffffb)` with the `DF_1_PIE (0x0800_0000)` bit set. [0197 §10, §29, §36; tasks/0563 §304.8, §304.11–304.12]

**AXS-ELFD-004 — Shared Objects (`--kind dll`, `lib<name>.so`, `DT_SONAME`).** On `x86_64-linux`, `--kind dll` (or `kind = "dll"` in `axiom.toml`, `SPEC-26 AXS-WLIB-001..002`) produces an ELF64 shared object named `lib<stem>.so` by default when `-o <path>` is omitted (`0197 §17, §23, §37`, `tasks/0563 §304.3`):
- `e_type = ET_DYN (3)` and `e_entry = 0` (initialization runs exclusively through `.init_array`, never `e_entry`);
- No `PT_INTERP` program header is emitted;
- `.dynamic` records `DT_SONAME (14)` pointing to the `.dynstr` offset of `"lib<stem>.so"` (or the explicit string passed via `--soname <name>`);
- Unlike Windows PE (`SPEC-26 AXS-WLIB-030`), no companion `.lib` import archive is needed on Linux because `compiler/link/elf_dyn` links downstream executables and shared libraries directly against the `.so`'s `.dynsym` and `DT_SONAME` (`AXS-ELFD-031`). [0197 §17, §23, §37; SPEC-26 AXS-WLIB-001..002; tasks/0563 §304.3]

**AXS-ELFD-005 — Distinct `FileOffset`, `VirtualAddress`, `RelativeVirtualAddress`, and `SectionOffset` Domains.** `compiler/obj/elf_dyn` and `compiler/link/elf_dyn` maintain type-distinct coordinate domains (`FileOffset`, `VirtualAddress`, `RelativeVirtualAddress`, `SectionOffset`, `0197 AELF-42`, `tasks/0563 §304.5–304.6`). Every `PT_LOAD` segment satisfies `p_filesz <= p_memsz` (`.bss` and `.tbss` occupy `0` file bytes, `tasks/0563 §304.5`) and `(p_vaddr % 0x1000) == (p_offset % 0x1000)`. [0197 AELF-42; tasks/0563 §304.5–304.6]

**AXS-ELFD-006 — `CodeModel.PositionIndependent` (`PIC`) Selection.** `TargetDesc` and the driver model position independence as `CodeModel.PositionIndependent` (`0197 §11–12, §27–28, AELF-27`). `CodeModel.PositionIndependent` is enabled unconditionally when compiling `--kind dll`, `--pie`, or `--static-pie`, and is the default for `--kind obj` and `--kind lib` on `x86_64-linux` (unless `--no-pic` / `--static` fixed-address codegen is explicitly requested) so every `.o` and `.a` archive member can be linked into both `ET_EXEC` and `ET_DYN` images without recompilation. [0197 §11–12, §27–28, AELF-27]

**AXS-ELFD-007 — Separation of ISA Encoding, `ObjectWriter`, `LinkerCore` (`LinkedImage`), and `ElfImageWriter` Verification.** In compliance with `tasks/0522` (`ABACKEND-37..38`), `tasks/0524` (`ABACKEND-82..83`), and `tasks/0563` (§304.1–304.4):
1. **ISA encoding vs object serialization (`REQ-TGT-184`):** The x86-64 encoder emits raw instruction bytes and symbolic relocation descriptors without constructing ELF headers or dynamic tables.
2. **Explicit relocation semantics (`REQ-TGT-183`, `REQ-TGT-308`):** Relocations remain explicit and symbolic across `.o` files and `LinkerCore` until resolved at static link time or emitted into `.rela.dyn`/`.rela.plt` for runtime resolution (`0197 AELF-28..29`).
3. **No re-linking in `ElfImageWriter` (`tasks/0563 §304.1`):** `LinkerCore` finalizes symbol resolution, section GC, GOT/PLT slot allocation, and `ImageLayout` virtual addresses before `ElfImageWriter` serializes bytes.
4. **Post-encoding object/image verification (`REQ-TGT-307`):** Immediately after encoding/serializing an ELF `.o`, `PIE`, or `.so`, the structural verifier (`verify_elf_image`) validates header bounds, section/segment alignment, W^X flags, `.dynsym`/`.gnu.hash` consistency, and relocation indices (`ABACKEND-82`). [0197 §2, AELF-28..30; tasks/0522 ABACKEND-37..38; tasks/0524 ABACKEND-82..83; tasks/0563 §304.1–304.4; REQ-TGT-183, REQ-TGT-184, REQ-TGT-307, REQ-TGT-308]

**AXS-ELFD-008 — Pre-Emission Instruction Sizing, Branch Relaxation & Alignment Preservation.** In `compiler/target/x64/`, all instruction size changes — including short (`2`-byte `EB rel8` / `7cc rel8`) vs near (`5`-byte `E9 rel32` / `6`-byte `0F 8cc rel32`) branch relaxation and 6-byte `REX_GOTPCRELX` forms — are resolved to fixed byte lengths before final object/image emission (`tasks/0518 AMACHINE-72`, `REQ-TGT-061`). Branch relaxation preserves exact condition predicates, `RFLAGS` liveness, and control-flow targets (`AMACHINE-73`, `REQ-TGT-062`), and machine code layout preserves all required function (`16`-byte), basic-block, constant-pool, and section alignment contracts (`AMACHINE-74`, `REQ-TGT-063`). [tasks/0518 §151 AMACHINE-72..74; REQ-TGT-061, REQ-TGT-062, REQ-TGT-063]

**AXS-ELFD-009 — Source-to-Machine Debug & Unwind Provenance Preservation.** Every Machine IR instruction lowered by `compiler/target/x64/pic` and transformed during branch or GOT relaxation retains its `SourceSpan` / `DebugLoc` provenance mapping back to MIR and source lines (`tasks/0518 AMACHINE-75..76`, `REQ-TGT-064`, `REQ-TGT-065`), feeding DWARF `.debug_line`/`.debug_info` and `.eh_frame` CFI generation (`0197 §33–34, AELF-40..41`). [0197 §33–34, AELF-40..41; tasks/0518 §151 AMACHINE-75..76; REQ-TGT-064, REQ-TGT-065]

**AXS-ELFD-010 — Byte-Exact Reproducible Dynamic ELF Generation.** Every `.o`, `PIE`, and `.so` binary emitted by `compiler/obj/elf_dyn` and `compiler/link/elf_dyn` is a pure deterministic function of source inputs and compiler flags (`0197 AELF-43`, `INV-DET-001..002`), sorting `.dynsym`, `.rela.dyn`, `.rela.plt`, and `.got`/`.plt` slots canonically and containing zero timestamps or host paths. [0197 AELF-43; INV-DET-001..002]

---

## 2. PIC Codegen, GOT/PLT Lowering, Dynamic Relocations, TLS & Function Identity (`AXS-ELFD-011`..`021`)

**AXS-ELFD-011 — Target-Neutral `DynamicAddressSlot` & `DynamicCall` Lowering.** `Axiom LIR` represents global symbol addresses and function calls without target-specific `GOT` or `PLT` opcodes (`0197 §6–8, §11–12, AELF-23..24`, `tasks/0521 AARM-52`, `REQ-TGT-146`). PIC/GOT/PLT lowering is performed in the target backend (`compiler/target/x64/pic`) and linker (`compiler/link/elf_dyn`), mapping `DynamicAddressSlot` to `.got` on ELF (just as PE maps it to `.idata` IAT) and `DynamicCall` to `.plt`/`.got.plt`. [0197 §6–8, §11–12, AELF-23..24; tasks/0521 §156 AARM-52; REQ-TGT-146]

**AXS-ELFD-012 — `RIP`-Relative Addressing for Local & Non-Preemptible Symbols.** Under `CodeModel.PositionIndependent`, accessing data or taking the address of a symbol proven defined within the current linkage unit and non-preemptible (`STB_LOCAL` or `STV_HIDDEN`, `AXS-ELFD-029`) lowers directly to `lea r64, [rip + disp32]` (`48 8D /r`) or `[rip + disp32]` memory operands carrying relocation `R_X86_64_PC32 (2)` ($S + A - P$, $A = \text{offset} - 4$) (`0197 §11–13`), resolved at link time without allocating a `.got` slot. [0197 §11–13]

**AXS-ELFD-013 — Indirect `.got` Address Loads via `R_X86_64_GOTPCREL` / `R_X86_64_REX_GOTPCRELX`.** Accessing or taking the address of an external (`extern`), imported (`DT_NEEDED`), or preemptible (`STV_DEFAULT` in a `.so`) symbol in PIC mode lowers to a 6-byte indirect load from the Global Offset Table (`0197 §6, §13`):
- Instruction: `mov r64, qword ptr [rip + disp32]` (`REX.W + 8B /r`, 6 bytes);
- Relocation in `.rela.text`: `R_X86_64_REX_GOTPCRELX (42)` (or `R_X86_64_GOTPCREL (9)` / `R_X86_64_GOTPCRELX (41)`) with `r_addend = -4` and `r_offset` pointing to the 4-byte `disp32` field;
- Link-time patch: `disp32` is patched to $G + \text{GOT} + A - P$, where $G + \text{GOT}$ is the virtual address of the 8-byte `.got` slot allocated for the symbol. [0197 §6, §13]

**AXS-ELFD-014 — GOT Load Relaxation (`mov` $\rightarrow$ `lea`) When Resolved Locally.** When `compiler/link/elf_dyn` determines that the target symbol $S$ of an `R_X86_64_REX_GOTPCRELX (42)` `mov r64, qword ptr [rip + disp32]` (`48 8B /r` or `4C 8B /r`) is defined locally in the final image, non-preemptible (`LinkMode.Pie`, `LinkMode.Static`, or `STV_HIDDEN` in `LinkMode.SharedObject`), and within 32-bit signed PC-relative range, the linker relaxes the instruction in-place from `8B` (`MOV`) to `8D` (`LEA`: `lea r64, [rip + disp32]`) and patches `disp32` to $S + A - P$, eliminating the `.got` memory indirection while preserving the exact 6-byte instruction length (`REQ-TGT-061`) and semantic equivalence (`tasks/0518 AMACHINE-77`, `REQ-TGT-066`). [0197 §6, §13; tasks/0518 §151 AMACHINE-77; REQ-TGT-061, REQ-TGT-066]

**AXS-ELFD-015 — Procedure Linkage Table (`.plt`) Calls via `R_X86_64_PLT32`.** Direct function calls (`call rel32`, `E8 disp32`) and tail jumps (`jmp rel32`, `E9 disp32`) in PIC mode emit relocation `R_X86_64_PLT32 (4)` with `r_addend = -4` (`0197 §7–8, §13`). If the callee is defined locally and non-preemptible, `compiler/link/elf_dyn` patches `disp32` directly to $S + A - P$ without creating a PLT entry; if the callee is imported from a `DT_NEEDED` shared object (or preemptible), `compiler/link/elf_dyn` synthesizes a `.plt` stub at virtual address $L$ and patches `disp32` to $L + A - P$. [0197 §7–8, §13]

**AXS-ELFD-016 — Canonical x86-64 `.plt`, `.plt.got`, `.got`, and `.got.plt` Binary Layout.** `compiler/obj/elf_dyn` and `compiler/link/elf_dyn` construct the GOT and PLT sections with exact x86-64 psABI layout (`0197 §6–9`, `tasks/0563 §304.10`):
1. **`.got` (`SHT_PROGBITS`, `SHF_ALLOC | SHF_WRITE`, align `8`)**: 8-byte slots for `R_X86_64_GLOB_DAT`, `R_X86_64_RELATIVE`, and TLS `R_X86_64_TPOFF64` / `R_X86_64_DTPMOD64` / `R_X86_64_DTPOFF64` descriptors.
2. **`.got.plt` (`SHT_PROGBITS`, `SHF_ALLOC | SHF_WRITE`, align `8`)**:
   - `GOT.PLT[0]` (offset `0`): relative virtual address of `_DYNAMIC` (`.dynamic` section);
   - `GOT.PLT[1]` (offset `8`): `0` (reserved for runtime `link_map*`);
   - `GOT.PLT[2]` (offset `16`): `0` (reserved for runtime `_dl_runtime_resolve`);
   - `GOT.PLT[3 + k]` (offset `24 + 8*k` for $k \in [0, N_{\text{plt}})$): initialized to `VMA(PLT[k + 1]) + 6` (the `push k` instruction following `jmp [rip + disp32]`), accompanied by a `.rela.plt` entry of type `R_X86_64_JUMP_SLOT (7)` targeting `GOT.PLT[3 + k]`.
3. **`.plt` (`SHT_PROGBITS`, `SHF_ALLOC | SHF_EXECINSTR`, align `16`)**:
   - `PLT[0]` (16 bytes at offset `0`): `FF 35 <disp32 to GOT.PLT[1]>` (`push qword ptr [rip + GOT.PLT[1]]`), `FF 25 <disp32 to GOT.PLT[2]>` (`jmp qword ptr [rip + GOT.PLT[2]]`), `0F 1F 40 00` (`nop dword ptr [rax + 0]`).
   - `PLT[k + 1]` (16 bytes at offset `16 * (k + 1)`): `FF 25 <disp32 to GOT.PLT[3 + k]>` (`jmp qword ptr [rip + GOT.PLT[3 + k]]`), `68 <u32 k>` (`push k`), `E9 <disp32 to PLT[0]>` (`jmp PLT[0]`). [0197 §6–9; tasks/0563 §304.10]

**AXS-ELFD-017 — Static Link-Time vs Dynamic Runtime Relocations (`.rela.dyn` & `.rela.plt`).** ELF64 on x86-64 uses 24-byte `Elf64_Rela` records exclusively (`0197 §13–16, AELF-28..30`, `REQ-TGT-183`, `REQ-TGT-308`). `compiler/link/elf_dyn` resolves static PC-relative displacements at link time and emits dynamic relocations into `.rela.dyn` (`SHT_RELA`, sorted with all `R_X86_64_RELATIVE` entries first so `DT_RELACOUNT` is exact) and `.rela.plt` (`SHT_RELA`, `sh_info = .got.plt`):

| Dynamic `r_type` | Code | Section | Relocated Slot | Loader Formula ($B$ = load bias, $S$ = runtime sym VA) |
|---|---|---|---|---|
| `R_X86_64_64` | `1` | `.rela.dyn` | 8-byte data pointer (`sym_idx != 0`) | $S + A$ |
| `R_X86_64_GLOB_DAT` | `6` | `.rela.dyn` | 8-byte `.got` entry (`sym_idx != 0`, $A = 0$) | $S$ |
| `R_X86_64_JUMP_SLOT` | `7` | `.rela.plt` | 8-byte `.got.plt` entry (`sym_idx != 0`, $A = 0$) | $S$ |
| `R_X86_64_RELATIVE` | `8` | `.rela.dyn` | 8-byte internal pointer in `.data.rel.ro`/`.data`/`.got`/`.init_array` (`sym_idx == 0`) | $B + A$ |
| `R_X86_64_DTPMOD64` | `16` | `.rela.dyn` | 8-byte `.got` TLS module ID slot | $\text{tls\_modid}(S)$ |
| `R_X86_64_DTPOFF64` | `17` | `.rela.dyn` | 8-byte `.got` TLS intra-module offset slot | $\text{tls\_offset}(S) + A$ |
| `R_X86_64_TPOFF64` | `18` | `.rela.dyn` | 8-byte `.got` Initial-Exec TLS offset from `%fs:0` | $\text{tpoff}(S) + A$ |

[0197 §13–16, AELF-28..30; tasks/0563 §304.10; REQ-TGT-183, REQ-TGT-308]

**AXS-ELFD-018 — Strict Prohibition of Text Relocations (`DT_TEXTREL` Ban, `AX_LINK_TEXTREL_FORBIDDEN`).** Dynamic `ET_DYN` images (`PIE` and `.so`) never set `DT_TEXTREL` and never emit dynamic relocations into read-only or executable `PT_LOAD` segments (`tasks/0563 §304.8–304.13`). Any constant data structure containing relocated pointers (such as `dyn Trait` vtables `SPEC-63` or static pointer tables) is emitted into `.data.rel.ro` (`SHF_ALLOC | SHF_WRITE`), relocated by `R_X86_64_RELATIVE` / `R_X86_64_64` at load time, and subsequently locked read-only by `PT_GNU_RELRO` (`AXS-ELFD-023`). If a non-PIC `.o` input contains an absolute relocation (`R_X86_64_64`, `R_X86_64_32`, `R_X86_64_32S`) or non-local `R_X86_64_PC32` against a read-only/executable section during an `ET_DYN` link, `compiler/link/elf_dyn` rejects the link with `AX_LINK_TEXTREL_FORBIDDEN`. [0197 §11–16; tasks/0563 §304.8–304.13]

**AXS-ELFD-019 — Uniform `.got` Access for External Data (No `R_X86_64_COPY` Fragility).** Because `compiler/target/x64/pic` lowers all accesses to `extern` static data through `R_X86_64_GOTPCREL` (`AXS-ELFD-013`), `PIE` executables reference external shared-library globals directly in place via `.got` (`R_X86_64_GLOB_DAT`) without emitting `R_X86_64_COPY (5)` relocations that would couple the executable's `.bss` layout to a shared library's internal object size. [0197 §6, §13–15]

**AXS-ELFD-020 — Function-Address Equality & Machine Code Merging Constraints (`AMACHINE-77..79`).** When a function's address is observed as a value (`fn_addr(f)`, `f as usize`, or coercion to a first-class `fn(...)` pointer), PIC codegen loads the function's address from `.got` via `R_X86_64_GOTPCREL` (`AXS-ELFD-013`) rather than taking the address of a local `.plt` stub, and exported `.dynsym` entries for undefined imports carry `st_value = 0` (`SHN_UNDEF`) so `ld-linux-x86-64.so.2` resolves all `R_X86_64_GLOB_DAT` slots across the process to the single canonical function definition (`tasks/0518 AMACHINE-79`, `REQ-TGT-068`). Machine-level optimizations may remove physical instructions only when semantic equivalence is proven (`AMACHINE-77`, `REQ-TGT-066`) and may merge identical code sequences or functions (`ICF`, `SPEC-75 AXS-LTO-022`) only when observable function-pointer identity (`f as usize == g as usize`) is unaffected (`AMACHINE-78..79`, `REQ-TGT-067`, `REQ-TGT-068`). [tasks/0518 §151 AMACHINE-77..79; SPEC-75 AXS-LTO-022; REQ-TGT-066, REQ-TGT-067, REQ-TGT-068]

**AXS-ELFD-021 — ELF64 Thread-Local Storage (`@thread_local static`) Lowering & Invariants (`ATLS-20..25`).** `@thread_local static` items (`SPEC-32 AXS-SYNC-040`, `SPEC-60 AXS-CTM-031`) have per-thread identity and thread lifetime (`0197 §21–22, ATLS-20..21`), while TLS codegen and relocation lowering are strictly target-, ABI-, and link-mode-specific without exposing ELF TLS models in source syntax (`ATLS-22..25, AELF-31`, `tasks/0521 AARM-51`, `tasks/0522 ABACKEND-36`, `REQ-TGT-145`, `REQ-TGT-182`):
- **Local-Exec (`LE`, `LinkMode.Static` `ET_EXEC`)**: `mov rax, qword ptr fs:[0]; lea rax, [rax + disp32]` with `R_X86_64_TPOFF32 (23)` resolved at link time against `PT_TLS`.
- **Initial-Exec (`IE`, `LinkMode.Pie` / `LinkMode.StaticPie`)**: `mov rax, qword ptr fs:[0]; add rax, qword ptr [rip + disp32]` with `R_X86_64_GOTTPOFF (22)` referencing an 8-byte `.got` slot relocated at load time by `R_X86_64_TPOFF64 (18)`.
- **General-Dynamic (`GD`, `LinkMode.SharedObject` `.so`)**: canonical 16-byte sequence `.byte 0x66; lea rdi, [rip + disp32]; .word 0x6666; rex64; call __tls_get_addr@PLT` with `R_X86_64_TLSGD (19)` referencing a 16-byte pair of `.got` slots relocated by `R_X86_64_DTPMOD64 (16)` and `R_X86_64_DTPOFF64 (17)` (relaxable by the linker to `IE` or `LE` when linking into an executable).
- Initialized TLS templates are emitted in `.tdata` (`SHT_PROGBITS`, `SHF_ALLOC | SHF_WRITE | SHF_TLS = 0x403`) and zero-initialized TLS in `.tbss` (`SHT_NOBITS`, `SHF_ALLOC | SHF_WRITE | SHF_TLS = 0x403`), covered by a `PT_TLS (7)` (`PF_R = 0x4`) program header. [0197 §21–22, ATLS-20..25, AELF-31; tasks/0521 §156 AARM-51; tasks/0522 §159 ABACKEND-36; REQ-TGT-145, REQ-TGT-182]

---

## 3. ELF64 Dynamic Sections, Program Headers, RELRO, Visibility & GNU Versioning (`AXS-ELFD-022`..`035`)

**AXS-ELFD-022 — `ET_DYN` Program Header Table (`Elf64_Phdr`) & W^X Segment Layout.** `compiler/link/elf_dyn` maps dynamic and allocatable sections into 4 KiB page-aligned (`p_align = 0x1000`) `PT_LOAD` segments and metadata headers (`0197 §2, §10`, `tasks/0563 §304.8–304.13`):
1. **`PT_PHDR (6)` (`PF_R = 0x4`, `PIE` executables)**: Maps the `Elf64_Phdr` array in memory.
2. **`PT_INTERP (3)` (`PF_R = 0x4`, dynamic `PIE` executables only)**: Maps `.interp` (`/lib64/ld-linux-x86-64.so.2\0`).
3. **`PT_LOAD` 0 (`R`, `PF_R = 0x4`)**: Maps `Elf64_Ehdr`, `Elf64_Phdr[]`, `.interp`, `.dynsym`, `.gnu.hash`, `.hash` (when emitted), `.dynstr`, `.gnu.version`, `.gnu.version_d`, `.gnu.version_r`, `.rela.dyn`, `.rela.plt`, `.rodata`, and `.eh_frame`.
4. **`PT_LOAD` 1 (`RX`, `PF_R | PF_X = 0x5`)**: Maps `.plt`, `.plt.got`, and `.text` at the next 4 KiB page boundary.
5. **`PT_LOAD` 2 (`RW`, `PF_R | PF_W = 0x6`)**: Maps the RELRO prefix (`.init_array`, `.fini_array`, `.data.rel.ro`, `.dynamic`, `.got`, and `.got.plt` under Full RELRO), padded to a 4 KiB page boundary, followed by writable `.got.plt` (under `--lazy-plt`), `.data`, and `.bss` (`p_memsz = p_filesz + sizeof(.bss)`).
6. **`PT_DYNAMIC (2)` (`PF_R | PF_W = 0x6`, `p_align = 8`)**: Covers `.dynamic`.
7. **`PT_TLS (7)` (`PF_R = 0x4`)**: Covers `.tdata` + `.tbss` when thread-local storage is present.
8. **`PT_GNU_RELRO (0x6474e552)` (`PF_R = 0x4`, `p_align = 1`)**: Covers the RELRO prefix of `PT_LOAD` 2 such that `(p_vaddr + p_memsz) % 0x1000 == 0`.
9. **`PT_GNU_STACK (0x6474e551)` (`PF_R | PF_W = 0x6`, `p_filesz = p_memsz = 0`)**: Marks the process stack non-executable. No segment ever carries both `PF_W` and `PF_X`. [0197 §2, §10; tasks/0563 §304.8–304.13]

**AXS-ELFD-023 — Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`) Default vs Lazy PLT Binding (`--lazy-plt`).** `compiler/link/elf_dyn` models binding policy explicitly (`BindingPolicy.Eager` vs `BindingPolicy.Lazy`, `0197 §9`, `tasks/0563 §304.13`):
- **Default (`BindingPolicy.Eager`, Full RELRO / `-z relro -z now`)**: `.dynamic` emits `DT_BIND_NOW (24)`, sets `DF_BIND_NOW (0x8)` in `DT_FLAGS (30)`, and sets `DF_1_NOW (0x1)` in `DT_FLAGS_1 (0x6ffffffb)`. Both `.got` and `.got.plt` reside inside `PT_GNU_RELRO`, so `ld-linux-x86-64.so.2` resolves all `R_X86_64_GLOB_DAT` and `R_X86_64_JUMP_SLOT` entries before startup and marks the entire GOT read-only via `mprotect(PROT_READ)`.
- **Opt-in Lazy Binding (`BindingPolicy.Lazy`, `--lazy-plt` / `-z lazy`)**: `DT_BIND_NOW` is omitted, `.init_array`/`.fini_array`/`.data.rel.ro`/`.dynamic`/`.got` remain protected by `PT_GNU_RELRO` (Partial RELRO), and `.got.plt` is placed immediately after the 4 KiB RELRO page boundary so `PLT[0]` can lazily patch `GOT.PLT[3 + k]` on first call. [0197 §9; tasks/0563 §304.13]

**AXS-ELFD-024 — Separation of `.symtab` (Static) vs `.dynsym` (Dynamic Symbol Table).** `compiler/obj/elf_dyn` and `compiler/link/elf_dyn` maintain `StaticSymbolTable` (`.symtab`, `SHT_SYMTAB = 2`, non-`SHF_ALLOC`) and `DynamicSymbolTable` (`.dynsym`, `SHT_DYNSYM = 11`, `SHF_ALLOC = 0x2`, `sh_entsize = 24`, `sh_link = .dynstr`, `sh_info = 1`) as separate data structures (`0197 §4, AELF-22`). `.dynsym` begins with `STN_UNDEF` at index `0`, followed by imported undefined dynamic symbols (`st_shndx = SHN_UNDEF`, `st_value = 0`) sorted deterministically by name, followed by exported dynamic definitions (`st_shndx != SHN_UNDEF`) ordered by `.gnu.hash` bucket index (`AXS-ELFD-026`). [0197 §4, AELF-22; tasks/0563 §304.10]

**AXS-ELFD-025 — Dynamic String Table (`.dynstr`, `SHT_STRTAB`).** `.dynstr` (`sh_type = SHT_STRTAB = 3`, `sh_flags = SHF_ALLOC = 0x2`, `sh_addralign = 1`) stores NUL-terminated strings referenced by `.dynsym`, `.dynamic` (`DT_NEEDED`, `DT_SONAME`, `DT_RUNPATH`), and `.gnu.version_d`/`.gnu.version_r`, beginning with `'\0'` at offset `0`. [0197 §4–5; tasks/0563 §304.10]

**AXS-ELFD-026 — `.gnu.hash` (`SHT_GNU_HASH`) & Optional SysV `.hash` (`SHT_HASH`) Symbol Lookup.** Every `ET_DYN` image emits a deterministic `.gnu.hash` section (`sh_type = SHT_GNU_HASH = 0x6ffffff6`, `sh_flags = SHF_ALLOC`, `sh_addralign = 8`, `sh_link = .dynsym`, `0197 §20`, `tasks/0563 §304.10`):
- **Header (16 bytes)**: `nbuckets: u32` ($\ge 1$), `symoffset: u32` (first exported defined symbol index in `.dynsym`; all `SHN_UNDEF` imports have index $< \text{symoffset}$), `bloom_size: u32` (power of two $\ge 1$), `bloom_shift: u32` ($6$).
- **Hash function**: `gnu_hash(name)` initializes `h: u32 = 5381` and iterates $h = (h \times 33 + \text{byte}) \bmod 2^{32}$.
- **Bloom filter (`u64[bloom_size]`)**: For each exported symbol hash $h$, sets bit $h \bmod 64$ and bit $((h \gg \text{bloom\_shift}) \bmod 64)$ in word $((h / 64) \bmod \text{bloom\_size})$.
- **Buckets (`u32[nbuckets]`) & Chains (`u32[N_exports]`)**: Exported `.dynsym[symoffset..]` entries are stably sorted by ascending $h \bmod \text{nbuckets}$; `buckets[b]` holds the first `.dynsym` index in bucket $b$ (or `0` if empty), and `chains[i - symoffset]` holds $(h \ \& \ \text{\textasciitilde}1) \mid \text{is\_last\_in\_bucket}$.
- When `--sysv-hash` is requested, a standard SysV `.hash` (`SHT_HASH = 5`, `sh_entsize = 4`) section is also emitted. [0197 §20; tasks/0563 §304.10]

**AXS-ELFD-027 — `.dynamic` Section (`SHT_DYNAMIC`, `Elf64_Dyn`, 16 Bytes Each).** `.dynamic` (`sh_type = SHT_DYNAMIC = 6`, `sh_flags = SHF_ALLOC | SHF_WRITE = 0x3`, `sh_addralign = 8`, `sh_entsize = 16`, `sh_link = .dynstr`) contains 16-byte `Elf64_Dyn { d_tag: i64, d_un: u64 }` records terminated by `DT_NULL (0)` (`0197 §5, §15`, `tasks/0563 §304.10`):
- `DT_NEEDED (1)` (one per required `.so` in deterministic order), `DT_SONAME (14)` (in `.so`), `DT_RUNPATH (29)` (when `--rpath <dir>` is specified; preferred over deprecated `DT_RPATH = 15`);
- `DT_GNU_HASH (0x6ffffef5)` (and `DT_HASH = 4` if `.hash` is emitted), `DT_STRTAB (5)`, `DT_SYMTAB (6)`, `DT_STRSZ (10)`, `DT_SYMENT (11 = 24)`;
- `DT_RELA (7)`, `DT_RELASZ (8)`, `DT_RELAENT (9 = 24)`, `DT_RELACOUNT (0x6ffffff9)` (when `.rela.dyn` is non-empty);
- `DT_PLTGOT (3)`, `DT_PLTREL (20 = 7)`, `DT_JMPREL (23)`, `DT_PLTRELSZ (2)` (when `.rela.plt` is non-empty);
- `DT_INIT_ARRAY (25)`, `DT_INIT_ARRAYSZ (27)`, `DT_FINI_ARRAY (26)`, `DT_FINI_ARRAYSZ (28)` (when `.init_array`/`.fini_array` are non-empty);
- `DT_VERSYM (0x6ffffff0)`, `DT_VERDEF (0x6ffffffc)` / `DT_VERDEFNUM (0x6ffffffd)`, `DT_VERNEED (0x6ffffffe)` / `DT_VERNEEDNUM (0x6fffffff)` (when GNU symbol versions are present);
- `DT_BIND_NOW (24)`, `DT_FLAGS (30)`, `DT_FLAGS_1 (0x6ffffffb)`, and trailing `DT_NULL (0)`. [0197 §5, §15; tasks/0563 §304.10]

**AXS-ELFD-028 — `.init_array` (`SHT_INIT_ARRAY`) & `.fini_array` (`SHT_FINI_ARRAY`) Lifecycle Hooks.** Module-level `static` items are initialized from compile-time constants (`SPEC-52 AXS-FRE-004`, zero implicit user constructors from module imports). When an `ET_DYN` binary requires load-time initialization — specifically for E13.7 module-relative bindings (`@at(image("mod") + offset)`, `AXS-ELFD-034`) or explicit runtime/FFI registration — `compiler/link/elf_dyn` places 8-byte function pointers in `.init_array` (`SHT_INIT_ARRAY = 14`, `SHF_ALLOC | SHF_WRITE`, relocated by `R_X86_64_RELATIVE`) and teardown pointers in `.fini_array` (`SHT_FINI_ARRAY = 15`). [SPEC-52 AXS-FRE-004; SPEC-56 AXS-MOD-012; tasks/0563 §304.8–304.10]

**AXS-ELFD-029 — Symbol Visibility (`STV_DEFAULT` for `@export`, `STV_HIDDEN` Default for Internal Symbols).** Axiom never conflates module-level `pub` with ELF dynamic symbol export (`0197 §3, §17–18`, `SPEC-26 AXS-WLIB-004`, `SPEC-56 AXS-MOD-004`, `REQ-FFI-042`):
- Private items generate `STB_LOCAL (0)` symbols in `.symtab` and are omitted from `.dynsym`.
- Cross-module `pub` functions and `pub static` items without `@export` generate `STB_GLOBAL (1)` symbols with `st_other = STV_HIDDEN (2)` in `.symtab`: they are resolved across `.o`/`.a` objects during linking, use direct RIP-relative addressing without GOT/PLT overhead, and are omitted from `.dynsym` in the linked `PIE` or `.so`.
- Only items explicitly annotated with `@export` or `@export("custom_name")` receive `STB_GLOBAL (1)` + `STV_DEFAULT (0)` (or `STV_PROTECTED (3)` when non-preemptible export is specified) and are emitted into `.dynsym`. Duplicate `@export` names in the same linked image emit `AX_LINK_DUPLICATE_EXPORT`. [0197 §3, §17–18; SPEC-26 AXS-WLIB-004; SPEC-56 AXS-MOD-004; REQ-FFI-042]

**AXS-ELFD-030 — GNU Symbol Versioning (`SHT_GNU_versym`, `SHT_GNU_verneed`, `SHT_GNU_verdef`).** GNU symbol versioning is handled as platform linker metadata without polluting Core language syntax (`0197 §19, AELF-32`):
- `.gnu.version` (`SHT_GNU_versym = 0x6fffffff`, `sh_entsize = 2`, `sh_link = .dynsym`) stores a `u16` version index for every `.dynsym` entry (`0 = VER_NDX_LOCAL` for `STN_UNDEF`/local entries, `1 = VER_NDX_GLOBAL` for unversioned globals, and $\ge 2$ for versioned imports/exports).
- `.gnu.version_r` (`SHT_GNU_verneed = 0x6ffffffe`, `sh_link = .dynstr`) emits `Elf64_Verneed` + `Elf64_Vernaux` records (`vna_hash = sysv_elf_hash(ver_name)`) when linking against versioned symbols in external shared objects (e.g. `libc.so.6` symbols tagged `GLIBC_2.2.5`, `GLIBC_2.17`, or `GLIBC_2.34`).
- `.gnu.version_d` (`SHT_GNU_verdef = 0x6ffffffd`, `sh_link = .dynstr`) emits `Elf64_Verdef` + `Elf64_Verdaux` records when building a `.so` with versioned exports. [0197 §19, AELF-32]

**AXS-ELFD-031 — External `.so` Ingestion & Explicit `DT_NEEDED` Dependency Graph.** When resolving `-l<name>` or `@link("<name>")` in dynamic mode (`LinkMode.Pie`, `LinkMode.SharedObject`), `compiler/link/elf_dyn` probes each `-L<dir>` in CLI order for `<dir>/lib<name>.so` before `<dir>/lib<name>.a` (`0197 §5, §26, AELF-25`):
- Reads the external `.so`'s `Elf64_Ehdr`, `.dynamic` (`DT_SONAME`), `.dynsym`, `.dynstr`, and `.gnu.version` / `.gnu.version_d` (reporting `AX_LINK_BAD_OBJECT` on corrupt ELF headers or `AX_LINK_ARTIFACT_TARGET_MISMATCH` if `e_machine != EM_X86_64`).
- Binds unresolved symbol references to matching defined `STB_GLOBAL`/`STB_WEAK` `STV_DEFAULT`/`STV_PROTECTED` entries in the `.so`'s `.dynsym`, recording their default version string from `.gnu.version_d` (`VER_NDX` without hidden bit `0x8000`).
- Emits a `DT_NEEDED` entry using the `.so`'s `DT_SONAME` (or `lib<name>.so` if `DT_SONAME` is absent). The compiler never guesses `DT_NEEDED` entries from function names (`0197 §5`). [0197 §5, §26, AELF-25; T659]

**AXS-ELFD-032 — Transparent GNU Linker Script Stub Parsing (`GROUP` / `INPUT`) for System Libraries.** On standard Linux distributions (`glibc`), `/usr/lib/x86_64-linux-gnu/libc.so` and `libm.so` are often small ASCII linker scripts (`GROUP ( /lib/x86_64-linux-gnu/libc.so.6 /usr/lib/x86_64-linux-gnu/libc_nonshared.a AS_NEEDED ( /lib64/ld-linux-x86-64.so.2 ) )`). When `compiler/link/elf_dyn` opens a candidate `.so` file lacking `\x7FELF` magic that parses as an ASCII `INPUT(...)` or `GROUP(...)` stub, it resolves the referenced `.so.6` and `.a` paths deterministically in-process without invoking `ld`. [T659]

**AXS-ELFD-033 — Position-Independent `_start` Entry Stub for `PIE` Executables.** In `--profile hosted`, `compiler/link/elf_dyn` synthesizes a PIC `_start` stub for `PIE` executables (`0197 §29–30, §36`):
1. `xor ebp, ebp`; reads `argc = [rsp]`, `argv = rsp + 8`, and `envp = rsp + 8 * (argc + 2)` from the initial kernel/loader stack and stores them via RIP-relative `mov [rip + __ax_linux_argc], rdi` into `std.sys.linux` globals (`SPEC-80 AXS-ELFS-033`).
2. When `DT_INTERP` (`ld-linux-x86-64.so.2`) is present, the dynamic loader executes `.init_array` entries before jumping to `e_entry` (`_start`), and passes its finalizer pointer in `RDX` (registered or invoked on exit); in `--static-pie`, `_start` first iterates `[__rela_iplt_start, __rela_iplt_end)` to apply `R_X86_64_RELATIVE` (`*slot = load_bias + r_addend`) and calls `.init_array` entries directly.
3. Aligns `rsp` to 16 bytes (`and rsp, -16`), calls `main` (`call main`), runs `.fini_array` hooks in reverse order, and terminates via `SYS_exit_group = 231` (`mov edi, eax; mov eax, 231; syscall`). [0197 §29–30, §36; SPEC-80 AXS-ELFS-033; T659]

**AXS-ELFD-034 — Shared Object (`.so`) Initialization & E13.7 Module-Relative Binding Resolution.** When a Linux `PIE` executable or `.so` shared library uses E13.7 module-relative overlays (`@at(image("mod") + offset)` or `@at(image_self() + offset)`, `SPEC-56 AXS-MOD-001..013`), `compiler/link/elf_dyn` emits an 8-byte `LoadTimeSlot` in `.data` per overlay and registers `__ax_resolve_module_bindings` in `.init_array` (`T659`):
- `image_self()` resolves to the current ELF image's runtime load base via linker-defined hidden symbol `__ehdr_start` (`lea rax, [rip + __ehdr_start]`).
- `image("name")` resolves the runtime base address (`dlpi_addr` of the first `PT_LOAD` segment) of module `"name"` via `dl_iterate_phdr` (or `/proc/self/maps` scan when `libc`/`libdl` is not linked). If any required target module is missing at load time, `__ax_resolve_module_bindings` aborts deterministically before any user code executes (`SPEC-56 AXS-MOD-013`). [SPEC-56 AXS-MOD-001..013; T659]

**AXS-ELFD-035 — Zero Mandatory `libgcc_s.so` or Monolithic Runtime `.so` Dependency.** `axiomc` never emits an implicit `DT_NEEDED` on `libgcc_s.so.1` or a monolithic `libaxiom-runtime.so` (`0197 §31–32, AELF-37`). All compiler intrinsics (such as 128-bit integer division `__ax_udiv128`/`__ax_sdiv128`, `SPEC-40 AXS-INT-012`) are lowered directly by the Axiom backend and garbage-collected when unused. [0197 §31–32, AELF-37]

---

## 4. `libc`, `libm`, `libpthread` & `libdl` (`dlopen`/`dlsym`) Interoperability (`AXS-ELFD-036`..`045`)

**AXS-ELFD-036 — `libc` as an Optional Platform FFI Library, Not a Core Dependency.** Axiom decouples its language and standard library semantics from `libc` (`0197 §30, §40, AELF-38..39`, `0220 §1–5`):
1. `freestanding` and static `hosted` builds (`SPEC-80`) require zero `libc` headers, startup objects (`crt1.o`), or shared libraries.
2. Dynamic `PIE` executables and `.so` libraries in `--profile hosted` interoperate cleanly with system `libc.so.6` (`glibc` or `musl`), `libm.so.6`, `libpthread.so.0`, and `libdl.so.2` whenever `@link("c")` / `-lc` (or foreign C libraries) are linked. [0197 §30, §40, AELF-38..39; 0220 §1–5]

**AXS-ELFD-037 — `libc.so.6` C ABI Interoperability (`@link("c")`).** `extern "C"` declarations carrying `@link("c")` (or compiled with `-lc`) resolve against `libc.so.6` via `.plt`/`.got` under `CallConv.SysV64` (`0197 §38`, `SPEC-50 AXS-UNS-030..034`, `SPEC-80 §2`):
- Fixed and variadic `extern "C"` functions (`puts`, `printf`, `snprintf`, `malloc`, `calloc`, `realloc`, `free`, `fopen`, `fread`, `fwrite`, `fclose`, `getenv`, `qsort`) follow exact SysV AMD64 register assignment (`RDI, RSI, RDX, RCX, R8, R9`, `XMM0..XMM7`, and `AL` vector count for variadic calls `SPEC-80 AXS-ELFS-019`).
- Non-capturing Axiom `extern "C" fn` pointers pass directly to C higher-order routines (`qsort`, `bsearch`, `atexit`, `pthread_create`). [0197 §38; SPEC-50 AXS-UNS-030..034; SPEC-80 §2]

**AXS-ELFD-038 — Thread-Safe `errno` Interoperability (`__errno_location`).** On Linux `glibc`/`musl`, `errno` is a per-thread lvalue accessed via `extern "C" fn __errno_location() -> *mut i32`. When user FFI code or `std.os.linux` inspects or resets C `errno` across a `libc.so.6` call, it calls `__errno_location()` through `.plt`; `std.sys.linux` raw syscalls (`SPEC-80 AXS-ELFS-040..041`) decode `-errno` directly from `RAX` without clobbering C `errno`. [0220 §4–5; SPEC-80 AXS-ELFS-040..041]

**AXS-ELFD-039 — `libm.so.6` Interoperability vs Pure-Axiom `std.math`.** `std.math` is implemented in 100% pure deterministic Axiom (`SPEC-41 AXS-FLT-050`, `INV-FLT-004`) without linking `libm.so.6`. Foreign declarations explicitly annotated with `@link("m")` (or linked with `-lm`) bind to `libm.so.6` (`sin`, `cos`, `tan`, `exp`, `log`, `pow`, `atan2`, `hypot`) using `XMM0..XMM1` under `CallConv.SysV64`. [0197 §5; SPEC-41 AXS-FLT-050; INV-FLT-004]

**AXS-ELFD-040 — `libpthread` & Dynamic Loader TLS/Thread Coexistence.** When an Axiom `PIE` links against `libc.so.6` / `libpthread.so.0` or when an Axiom `.so` is loaded into a foreign host process, `ld-linux-x86-64.so.2` manages the `%fs:0` Thread Control Block (`TCB`) and Dynamic Thread Vector (`DTV`) (`0220 §4–5`). Because Axiom `.so` libraries lower `@thread_local static` via `General-Dynamic` TLS (`__tls_get_addr@PLT`, `AXS-ELFD-021`) and `PIE` executables use `Initial-Exec` TLS against `PT_TLS`, both OS threads spawned via `pthread_create` and Axiom threads access `@thread_local` storage safely without corrupting `%fs:0`. [0197 §21–22; 0220 §4–5]

**AXS-ELFD-041 — `std.sys.linux_dl` Dynamic Loader Interface (`dlopen`, `dlsym`, `dlclose`, `dlerror`, `dl_iterate_phdr`).** `std/sys/linux_dl` provides the canonical low-level Linux dynamic loading bindings (`T659`), linking against `libdl.so.2` / `libc.so.6` (`glibc >= 2.34` merges `libdl` into `libc.so.6`; `compiler/link/elf_dyn` resolves `dlopen` from whichever provides it under `-ldl` / `-lc`):
- Constants: `RTLD_LAZY: i32 = 0x0001`, `RTLD_NOW: i32 = 0x0002`, `RTLD_NOLOAD: i32 = 0x0004`, `RTLD_DEEPBIND: i32 = 0x0008`, `RTLD_LOCAL: i32 = 0x0000`, `RTLD_GLOBAL: i32 = 0x0100`, `RTLD_NODELETE: i32 = 0x1000`, `RTLD_DEFAULT: *mut u8 = 0 as *mut u8`, `RTLD_NEXT: *mut u8 = (-1isize) as *mut u8`.
- Functions (`extern "C"`):
  - `unsafe fn dlopen(filename: *const u8, flags: i32) -> *mut u8`
  - `unsafe fn dlsym(handle: *mut u8, symbol: *const u8) -> *mut u8`
  - `unsafe fn dlclose(handle: *mut u8) -> i32`
  - `unsafe fn dlerror() -> *const u8`
  - `unsafe fn dl_iterate_phdr(cb: extern "C" fn(*const DlPhdrInfo, usize, *mut u8) -> i32, data: *mut u8) -> i32` [0220 §2–5; T659]

**AXS-ELFD-042 — `std.sys.linux_dl.DynLib` RAII Handle & Open-World `unsafe` Trust Boundary.** `std.sys.linux_dl` exposes an owned RAII handle `DynLib` (`!Copy`, implements `Drop` calling `dlclose`) that enforces Axiom's open-world FFI safety rules (`SPEC-50 AXS-UNS-030`, `SPEC-53 AXS-SEC-004`, `SPEC-56 AXS-MOD-004`, `REQ-ABI-095`, `REQ-FFI-119`, `REQ-CAP-132`):
1. `DynLib.open(path: Str) -> Result<DynLib, i32>` validates that `path` contains no interior `\0` (`-4`), NUL-terminates it on a scratch buffer, and invokes `dlopen(c_path, RTLD_NOW | RTLD_LOCAL)`.
2. `unsafe fn sym_addr(self: view<DynLib>, name: Str) -> Result<usize, i32>` clears any prior `dlerror()`, calls `dlsym(self.handle, c_name)`, checks `dlerror() != null` to distinguish a legitimate `0` symbol value from lookup failure (`-1`), and returns the resolved runtime address as `usize`.
3. Converting the resolved address to a callable `extern "C" fn(...)` or dereferenceable pointer requires `unsafe` because dynamic symbol lookup cannot statically verify the target `.so`'s type signature, and `dlsym` never fabricates a safe `view<T>` / `mut_view<T>` capability (`AX_SEC_CAPABILITY_FORGERY`). Views borrowed across a dynamic call remain governed by `SPEC-11` lifetime containment (`REQ-CAP-132`). [SPEC-50 AXS-UNS-030; SPEC-53 AXS-SEC-004; SPEC-56 AXS-MOD-004; T659]

**AXS-ELFD-043 — Mandatory `extern "C"` No-Unwind Abort Barrier Across `.so` & `dlopen` Boundaries.** Every `@export extern "C" fn` in an Axiom `.so` and every call to an imported `extern "C"` or `dlsym` function enforces the `SPEC-54 AXS-PAN-010` FFI no-unwind barrier (`REQ-FFI-004`): an uncaught panic inside an exported `.so` entry point aborts deterministically rather than unwinding into a foreign C caller or dynamic loader frame. [SPEC-54 AXS-PAN-010; REQ-FFI-004]

**AXS-ELFD-044 — End-to-End Axiom `PIE` $\leftrightarrow$ Axiom `.so` & `libc.so.6` Interoperability.** An Axiom shared library built with `axiomc build --target x86_64-linux --kind dll` (`lib<name>.so`) is simultaneously consumable:
1. at link time by `axiomc build --target x86_64-linux --pie app.ax -L. -l<name>` (via `DT_NEEDED` + `.plt`/`.got`),
2. at runtime by `std.sys.linux_dl` (`dlopen` + `dlsym` + `dlclose`), and
3. by external C/C++/Python hosts (`gcc app.c -L. -l<name>` or `dlopen`). [0197 §36–39; T659]

**AXS-ELFD-045 — Structural Inspection (`inspect --emit=elf-dyn`) & System Tooling Compatibility.** `axiomc inspect --emit=elf-dyn <file>` prints a deterministic report of the image's `e_type` (`ET_DYN`), `PT_INTERP`, `PT_DYNAMIC`, `PT_GNU_RELRO`, `PT_GNU_STACK`, `.dynamic` tags (`DT_NEEDED`, `DT_SONAME`, `DT_RUNPATH`, `DT_FLAGS`, `DT_FLAGS_1`), `.dynsym` imports/exports with visibility and version tags, `.gnu.hash` parameters, and `.rela.dyn`/`.rela.plt` records. Emitted `PIE` and `.so` binaries pass `readelf -d -r -s -l`, `objdump -d -R`, `ldd`, and native Linux / WSL execution without warnings or structural errors. [0197 §36–41; tasks/0563 §304.8–304.13; T658, T659]

---

## 5. Diagnostics, Canonical Examples & Traceability (`AXS-ELFD-046`..`053`)

**AXS-ELFD-046 — Diagnostics Referenced by `SPEC-82`.** Linux ELF64 dynamic linking, `PIE`, and `.so` generation use the canonical `DRIVER`, `FFI`, `UNSAFE`, and `LINK` diagnostic codes (`spec/diagnostics.md` §10–11):

| Code | Area | Sev | Condition on `x86_64-linux` (`ET_DYN` / `PIE` / `.so`) |
|---|---|---|---|
| `AX_DRIVER_INVALID_ARTIFACT_KIND` | `DRIVER` | `error` | `--kind <k>` outside `{exe, obj, lib, dll}` (`AXS-ELFD-004`) |
| `AX_LINK_BAD_OBJECT` | `LINK` | `error` | Input `.o` or external `.so` lacks `\x7FELF` magic, is not 64-bit little-endian ELF64, or has corrupt `.dynsym`/`.dynstr`/`.dynamic`/`.rela.*` tables (`AXS-ELFD-007`, `AXS-ELFD-031`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | Input `.o`, `.a`, or external `.so` has `e_machine != EM_X86_64` or mismatched `TargetFingerprint` (`AXS-ELFD-031`) |
| `AX_LINK_LIBRARY_NOT_FOUND` | `LINK` | `error` | `-l<name>` or `@link("<name>")` cannot be resolved to `lib<name>.so` or `lib<name>.a` in any `-L<dir>` search path (`AXS-ELFD-031`) |
| `AX_LINK_UNDEFINED_SYMBOL` | `LINK` | `error` | Strong symbol reference remains unresolved after scanning all input `.o`, `.a`, and `DT_NEEDED` `.so` symbol tables (`AXS-ELFD-031`) |
| `AX_LINK_DUPLICATE_SYMBOL` | `LINK` | `error` | Two input `.o` / `.a` objects define the same strong `STB_GLOBAL` symbol (`SPEC-80 AXS-ELFS-036`) |
| `AX_LINK_DUPLICATE_EXPORT` | `LINK` | `error` | Two `@export` items in the same `.so` or `PIE` image resolve to the identical exported `.dynsym` name (`AXS-ELFD-029`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `error` | `R_X86_64_PC32`, `R_X86_64_PLT32`, or `R_X86_64_GOTPCREL` displacement overflows signed 32-bit range (`AXS-ELFD-012`..`015`) |
| `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | `error` | Non-PIC relocation (`R_X86_64_64`, `R_X86_64_32`, `R_X86_64_32S`) targets a read-only or executable segment in a `PIE` or `.so` link (`AXS-ELFD-018`) |
| `AX_FFI_GENERIC_EXPORT` | `FFI` | `error` | `@export` applied to an unmonomorphized generic function (`AXS-ELFD-029`) |
| `AX_UNSAFE_AT_FOREIGN_PLACEMENT` | `UNSAFE` | `error` | `@at(image("...") + off)` or `@at(image_self() + off)` carries an initializer `= init` or function body `{ ... }` (`AXS-ELFD-034`) |

**AXS-ELFD-047 — Canonical Positive Example 1: ELF64 Shared Object (`--kind dll`, `libmath_plugin.so`) with `@export` (`STV_DEFAULT`) & Hidden Internal Helpers (`STV_HIDDEN`).**

```axiom
// Compiled with: axiomc build --target x86_64-linux --kind dll math_plugin.ax -o libmath_plugin.so
// Emits ET_DYN with DT_SONAME = "libmath_plugin.so", PT_GNU_RELRO + DT_BIND_NOW, PT_GNU_STACK (RW),
// .gnu.hash, and .dynsym exporting only "plugin_fma_i64" (STV_DEFAULT) while clamp_i64 stays STV_HIDDEN.
module demo.linux_so_plugin

// Internal pub helper: STV_HIDDEN in .symtab, called via direct RIP-relative call, omitted from .dynsym
pub fn clamp_i64(x: i64, lo: i64, hi: i64) -> i64 {
    if x < lo {
        return lo
    }
    if x > hi {
        return hi
    }
    return x
}

@export("plugin_fma_i64")
pub extern "C" fn plugin_fma_i64(a: i64, b: i64, c: i64) -> i64 {
    let prod = a * b + c
    return clamp_i64(prod, -1_000_000, 1_000_000)
}
```

**AXS-ELFD-048 — Canonical Positive Example 2: Dynamically Linked `PIE` Executable Calling `libc.so.6` via `.plt` and `dlopen`/`dlsym` via `std.sys.linux_dl`.**

```axiom
// Compiled with: axiomc build --target x86_64-linux --pie dyn_host.ax -L. -lmath_plugin -lc -ldl -o dyn_host
// Emits ET_DYN PIE with PT_INTERP = "/lib64/ld-linux-x86-64.so.2", DF_1_PIE, and DT_NEEDED for
// libmath_plugin.so and libc.so.6.
module demo.linux_pie_host

use std.sys.linux_dl.DynLib

@link("math_plugin")
extern "C" {
    fn plugin_fma_i64(a: i64, b: i64, c: i64) -> i64
}

@link("c")
extern "C" {
    fn puts(s: *const u8) -> i32
}

pub fn main() -> i32 {
    // 1. Direct PLT call to DT_NEEDED libmath_plugin.so and libc.so.6
    let direct = plugin_fma_i64(6, 7, 0)
    unsafe {
        let msg = "Xin chào thế giới\0"
        let _ = puts(msg.as_ptr())
    }

    // 2. Runtime dlopen + dlsym lookup via std.sys.linux_dl.DynLib
    let lib_res = DynLib.open("./libmath_plugin.so")
    match lib_res {
        Result.Ok(lib) => {
            let addr_res = unsafe { lib.sym_addr("plugin_fma_i64") }
            match addr_res {
                Result.Ok(addr) => {
                    let f: extern "C" fn(i64, i64, i64) -> i64 = unsafe {
                        std.mem.bitcast<usize, extern "C" fn(i64, i64, i64) -> i64>(addr)
                    }
                    let dyn_val = unsafe { f(10, 4, 2) }
                    if direct == 42 && dyn_val == 42 {
                        return 0
                    }
                    return 1
                }
                Result.Err(_) => return 2,
            }
        }
        Result.Err(_) => return 3,
    }
}
```

**AXS-ELFD-049 — Canonical Positive Example 3: Function-Address Identity Preservation (`AMACHINE-79`) & Module-Relative Overlay in a Hosted Linux `PIE`.**

```axiom
// Taking fn_addr in PIC/PIE mode loads the canonical address from .got (R_X86_64_GOTPCREL),
// preserving pointer equality across modules (AXS-ELFD-020, REQ-TGT-068).
module demo.linux_fn_identity

use std.mem.fn_addr

@export("compute_step")
pub extern "C" fn compute_step(x: i32) -> i32 {
    return x + 1
}

pub fn same_fn_ptr(fp: extern "C" fn(i32) -> i32) -> bool {
    let a = fn_addr(compute_step)
    let b = fp as usize
    return a == b
}

pub fn main() -> i32 {
    let f: extern "C" fn(i32) -> i32 = compute_step
    if same_fn_ptr(f) {
        return 0
    }
    return 1
}
```

**AXS-ELFD-050 — Canonical Negative Example 1: Generic Function Marked `@export` in a Linux `.so` Rejected (`AX_FFI_GENERIC_EXPORT`).**

```axiom
// Compiled with: axiomc check --target x86_64-linux --kind dll bad_generic_export.ax
module demo.bad_generic_export

@export("generic_id") //~ ERROR AX_FFI_GENERIC_EXPORT
pub fn generic_id<T>(x: T) -> T {
    return x
}
```

**AXS-ELFD-051 — Canonical Negative Example 2: Duplicate `@export` Symbol Name in a Linux `.so` Rejected (`AX_LINK_DUPLICATE_EXPORT`).**

```axiom
// Compiled with: axiomc build --target x86_64-linux --kind dll dup_export.ax
module demo.dup_export

@export("shared_api")
pub extern "C" fn api_v1() -> i32 {
    return 1
}

@export("shared_api") //~ ERROR AX_LINK_DUPLICATE_EXPORT
pub extern "C" fn api_v2() -> i32 {
    return 2
}
```

**AXS-ELFD-052 — Canonical Negative Example 3: Foreign Placement in `@at(image("libc.so.6") + offset)` Rejected (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`).**

```axiom
// Compiled with: axiomc check --target x86_64-linux --pie bad_foreign_placement.ax
module demo.bad_foreign_placement

// Module-relative bindings in hosted PIE/.so builds must be overlays without initializers or bodies (AXS-ELFD-034)
@at(image("libc.so.6") + 0x1000usize) //~ ERROR AX_UNSAFE_AT_FOREIGN_PLACEMENT
pub unsafe static mut PATCHED_SLOT: u64 = 0xDEAD_BEEFu64

pub fn main() -> i32 {
    return 0
}
```

**AXS-ELFD-053 — Requirement, Invariant & Task Traceability Matrix (`E16.2`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T657` | `SPEC-82`: Canonical Linux ELF64 dynamic linking, `PIE`, `GOT`/`PLT`, `.so`, symbol visibility/versioning, pre-emission sizing/relaxation/provenance, and `libc`/`dlopen` interop specification | `INV-ELFD-001`..`003` | `REQ-TGT-061`, `REQ-TGT-062`, `REQ-TGT-063`, `REQ-TGT-064`, `REQ-TGT-065` | `spec/SPEC-82-linux-elf-dynamic.md` |
| `T658` | `compiler/target/x64/pic` & `compiler/obj/elf_dyn`: PIC/PIE codegen, `GOT`/`PLT` lowering, function-address identity (`AMACHINE-79`), ELF TLS (`IE`/`GD`), `.dynsym`/`.dynstr`/`.gnu.hash`/`.dynamic`/`.rela.*`, and `PT_GNU_RELRO` | `INV-ELFD-001`, `INV-ELFD-002` | `REQ-TGT-066`, `REQ-TGT-067`, `REQ-TGT-068`, `REQ-TGT-145`, `REQ-TGT-146` | `tests/obj/elf_dyn`, `tests/selfhost/encode`, `tests/selfhost/obj` |
| `T659` | `compiler/link/elf_dyn` & `std/sys/linux_dl`: ELF64 `ET_DYN` `PIE` & `.so` linker, external `.so` `DT_NEEDED` & GNU version resolution, `libc` FFI interop, and `dlopen`/`dlsym`/`dlclose`/`dlerror` | `INV-ELFD-002`, `INV-ELFD-003` | `REQ-TGT-182`, `REQ-TGT-183`, `REQ-TGT-184`, `REQ-TGT-307`, `REQ-TGT-308` | `tests/run/linux_dyn`, `tests/selfhost/link` |

## Sources

0164 §1–41; 0192 §1–32 (`AELF-20..40`); 0197 §1–43 (`AELF-20..45`, `ATLS-20..25`); 0217 §1–30; 0220 §1–12; 0255 §1–20; 0256 §1–42; `tasks/0369`; `tasks/0518` §100–120, §151 (`AMACHINE-72..79`); `tasks/0521` §156 (`AARM-51..52`); `tasks/0522` §159 (`ABACKEND-36..38`); `tasks/0524` §112 (`ABACKEND-82..83`); `tasks/0563` §304.1–304.13; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-091`); `spec/SPEC-26-windows-artifact-kinds.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-32-threads-sync.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-56-module-relative-bindings.md`; `spec/SPEC-60-comptime-2-0.md`; `spec/SPEC-63-dyn-trait-vtables.md`; `spec/SPEC-75-lto-wpo-section-gc-pgo.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `ADR-0001`; `ADR-0002`; `ADR-0003`; `ADR-0011`; `ADR-0034`.
