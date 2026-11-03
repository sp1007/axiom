# SPEC-56 — Canonical Module-Relative Bindings (`@at(image("mod") + off)`, `image_self()`), Load-Time Slot Resolution & PE DLL/EXE Initializer Specification

Status: draft (T530, 2026-11-03)
Owner: axiom-architect
Consolidates: `spec/decisions/ADR-0001-fixed-address-declarations.md (§5–6, §7)`; `spec/requirements/OWNER.md (REQ-OWNER-005, REQ-OWNER-006, REQ-OWNER-008)`; `specs/0104 (§53–54)`; `specs/0138 (§53)`; `specs/0187 (§3–40, AIMPORT-20..30)`; `tasks/0336 (BOOTSTRAP-077)`; `tasks/0434 (§53, §92, AFFI-70..71)`; `tasks/0444 (§185.152, AABIAPI-22..26)`; `tasks/0451 (§192.39, AFFI-33..34)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-04-core-extensibility.md (AXS-EXT-032, AXS-EXT-070, AXS-EXT-073..074)`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-55-fixed-address-declarations.md`.
Covers: `REQ-OWNER-005`, `REQ-ABI-032`, `REQ-ABI-033`, `REQ-ABI-095` (and specifies the E13.7 contract for `T531`–`T533`: `REQ-CAP-132`, `REQ-FFI-119`, `REQ-FFI-042`).
Consumers: `compiler/hir/`, `compiler/sema/`, `compiler/mir/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/link/`, `T531`–`T533`, `E18.7` (`T751`).

## Tóm tắt

Tài liệu `SPEC-56` chuẩn hóa cơ chế ánh xạ chồng theo độ lệch tương đối mô-đun (`@at(image("mod") + offset)` và `@at(image_self() + offset)`), phân giải khe địa chỉ lúc nạp (`LoadTimeSlot`), ranh giới thế giới mở cho liên kết động, và quy tắc khởi tạo PE DLL/EXE cho phân hệ `E13.7` (Phase `P13`, `ADR-0001 §5–6`, `REQ-OWNER-005`, `REQ-ABI-032`, `REQ-ABI-033`, `REQ-ABI-095`):
- **Biểu thức cơ sở ảnh mô-đun `image("name") -> usize` và `image_self() -> usize` trong hồ sơ `hosted` (`ADR-0001 §5`, `REQ-OWNER-005`)**: Khi ASLR (Address Space Layout Randomization) bật trên hệ điều hành lưu trữ (`--profile hosted`), mã lệnh và dữ liệu của một tệp thực thi hoặc thư viện liên kết động (`.exe` / `.dll`) đã nạp vào tiến trình nằm tại địa chỉ `module_base + rva_offset`, chỉ biết tại thời điểm nạp. Axiom cung cấp `image("name") -> usize` (tra cứu địa chỉ cơ sở của mô-đun `"name"` đang nạp trong cùng tiến trình) và `image_self() -> usize` (địa chỉ cơ sở `__ImageBase` của chính mô-đun đang biên dịch) để dùng trực tiếp trong thuộc tính `@at(...)` / `@addr(...)` và trong phép tính độ lệch RVA lúc chạy (`addr_of(target) - image_self()`, `ADR-0001 §7`).
- **Chỉ cho phép Overlay, cấm Placement sang mô-đun ngoại (`ADR-0001 §5`, `T531`)**: Các khai báo `@at(image("mod") + offset)` và `@at(image_self() + offset)` chỉ được phép là **Overlay** (`static`, `static mut` không có biểu thức khởi tạo `= init`, hoặc `extern "C" fn` / `extern "system" fn` không có thân hàm). Mọi nỗ lực đặt dữ liệu khởi tạo hoặc thân hàm (`Placement`) vào `image(...) + offset` bị từ chối ở thời điểm biên dịch với mã chẩn đoán `AX_UNSAFE_AT_FOREIGN_PLACEMENT`. Sau khai báo `unsafe` hợp lệ (kiểu có bố cục xác định `@repr(C)` hoặc nguyên thủy, độ lệch thỏa căn chỉnh), lập trình viên gọi hàm và truy cập biến/trường bằng cú pháp Axiom thông thường (`GAME_STATE.player_count`, `game_add_item(...)`).
- **Ranh giới thế giới mở (`REQ-ABI-095`, `REQ-FFI-119`), bề mặt xuất tường minh (`REQ-FFI-042`), bảo toàn thời gian sống năng lực (`REQ-CAP-132`) và tách biệt liên kết động khỏi Hot Reload (`REQ-ABI-032`, `REQ-ABI-033`)**: Nạp thư viện động và liên kết qua khe mô-đun tạo thành ranh giới tối ưu hóa thế giới mở (`OpenWorld`): trình tối ưu hóa cấm áp dụng giả định thế giới đóng, cấm nội tuyến/devirtualize hoặc xóa mã chết qua biên mô-đun, và yêu cầu `unsafe` tại điểm khai báo đối với các ký hiệu nhập thô không có hợp đồng phiên bản. Liên kết động không bao hàm hot reload; hot reload đòi hỏi hợp đồng ABI trạng thái tường minh riêng biệt.
- **Phân giải khe địa chỉ lúc nạp (`LoadTimeSlot`), điều phối gián tiếp qua `.data` và thất bại khởi tạo tất định (`ADR-0001 §5–6`, `T532`)**: Mỗi khai báo overlay tương đối mô-đun hạ xuống một khe con trỏ 64-bit trong `.data` kèm bản ghi trong bảng khởi tạo mô-đun. Trước khi bất kỳ mã người dùng nào trong mô-đun chạy, hàm khởi tạo mô-đun (`DllMain` ở nhánh `DLL_PROCESS_ATTACH` đối với PE DLL hoặc stub khởi động đối với EXE) phân giải `image_self()` qua `__ImageBase` và `image("name")` qua `GetModuleHandleW(L"name")`. Nếu bất kỳ mô-đun đích nào chưa được nạp vào tiến trình (`NULL`), trình khởi tạo báo lỗi tất định ngay lập tức (DLL: `DllMain` trả về `FALSE` khiến `LoadLibraryW` trả về `NULL`; EXE: panic khởi động với mã thoát khác `0`) — tuyệt đối không bao giờ để mã người dùng gọi hay đọc/ghi qua khe địa chỉ `0` chưa phân giải.
- **Bản đồ mô-đun tiến trình mô phỏng trong Oracle (`--interp`, `T531`)**: Trình thông dịch MIR duy trì bảng mô-đun tiến trình ảo hóa (`ProcessModuleMap`), cho phép đăng ký mô-đun giả lập kèm địa chỉ cơ sở và kiểm thử đầy đủ cả đường thành công lẫn đường lỗi thiếu mô-đun hoàn toàn khớp với bản dịch native x86-64.

---

## 1. Module-Relative Overlay Declarations (`image("mod")` & `image_self()`), Overlay-Only Rule & ABI/Safety Boundaries (`AXS-MOD-001`..`005`)

### AXS-MOD-001 — Module-Base Address Intrinsics (`image("name") -> usize` and `image_self() -> usize`) (`ADR-0001 §5`, `REQ-OWNER-005`)

1. **Signature & Typing Contract**:
   - `image(name: Str) -> usize`: Returns the runtime virtual base address (load address / `HMODULE` on Windows PE32+) of the loaded module identified by the non-empty compile-time string literal `name` (e.g. `"game.exe"`, `"engine.dll"`) in the current process.
   - `image_self() -> usize`: Returns the runtime virtual base address of the current compilation unit's own executable or dynamic library image (`__ImageBase` in PE32+ images).
   - If `image(...)` is called with a non-literal expression or an empty string literal `""`, `compiler/sema/` rejects the call with `AX_TYPE_INVALID_IMAGE_ARG`.
   - Both `image("name")` and `image_self()` are valid in two contexts in `--profile hosted` (and `--profile system`):
     a. Inside the address expression `<expr>` of an `@at(<expr>)` or `@addr(<expr>)` overlay item declaration (`image("name") + offset` or `image_self() + offset`).
     b. As a runtime `usize` value expression inside function bodies (for example, computing a symbol's relative virtual address `let rva = addr_of(target) - image_self()`, `ADR-0001 §7`).
2. **Profile Rule**:
   - Unlike raw constant `@at(0x4000_1000)` hardware overlays (which require `--profile freestanding|kernel|system` or `--allow-fixed-addr` per `SPEC-55 AXS-ADR-014`), module-relative overlays `@at(image("name") + offset)` and `@at(image_self() + offset)` are **natively permitted in `--profile hosted`** (`ADR-0001 §5`, `REQ-OWNER-005`) without requiring `--allow-fixed-addr`.
   - Using `image("name")` in `--profile freestanding` or `--profile kernel` (where no hosted OS dynamic loader or process module table exists) is rejected at compile time with `AX_DRIVER_PROFILE_FORBIDDEN_CAP` (`data.capability = "dynamic_module"`), whereas `image_self()` remains valid when the linker defines `__ImageBase`.

[ADR-0001 §5, §7; OWNER.md REQ-OWNER-005, REQ-OWNER-008; SPEC-04 AXS-EXT-032; SPEC-55 AXS-ADR-014]

### AXS-MOD-002 — Hosted-Profile Module-Relative Overlays (`@at(image("mod") + offset)` & `@at(image_self() + offset)`) and "Use Normally" Contract (`ADR-0001 §5`, `REQ-OWNER-005`)

1. **Canonical Declaration Forms**:
   Inside a hosted EXE or DLL running in the same process as a target module, module-relative overlays bind functions and static data at `image("mod") + offset` or `image_self() + offset`:
   ```axiom
   // Binding an internal function of "game.exe" at RVA 0x1A_2B30:
   @at(image("game.exe") + 0x1A_2B30usize)
   unsafe extern "C" fn game_add_item(player: *mut Player, item_id: u32, count: i32) -> bool

   // Binding a @repr(C) global state struct of "game.exe" at RVA 0x3F_0010:
   @at(image("game.exe") + 0x3F_0010usize)
   unsafe static mut GAME_STATE: GameState

   // Binding a read-only lookup table inside the current module at RVA 0x2000:
   @at(image_self() + 0x2000usize)
   unsafe static TABLE: [256]u8
   ```
2. **"Use Normally" After an `unsafe` Declaration (`ADR-0001 §2, §5`, `REQ-OWNER-005`)**:
   - As in `SPEC-55 AXS-ADR-004`, the `unsafe` keyword on the `@at(image(...) + offset)` declaration is the **single trust boundary** where the author asserts that the module name, RVA offset, `@repr(C)` layout, alignment, calling convention, and access rules match the target image.
   - Once declared with `unsafe`, callers and readers/writers use **ordinary Axiom syntax** without pointer casts or call-site ceremony:
     ```axiom
     fn give_potions() {
         if GAME_STATE.player_count > 0 {
             let ok = game_add_item(GAME_STATE.players[0], 42u32, 10)
             let _ = ok
         }
     }
     ```
   - If a module-relative overlay is declared **without** the `unsafe` keyword on the item, every call or read/write access requires an enclosing `unsafe` block (`AX_UNSAFE_REQUIRED`, `SPEC-55 AXS-ADR-004`).
   - Fields of type `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, or `MmioWO<T>` inside a module-relative overlay struct automatically lower to exact-width `VolatileLoad` and `VolatileStore` operations (`SPEC-55 AXS-ADR-005`).

### AXS-MOD-003 — Overlay-Only Restriction (No Foreign Placement `AX_UNSAFE_AT_FOREIGN_PLACEMENT`), `@repr(C)` Layout & Alignment Verification (`ADR-0001 §3, §5`, `T531`)

1. **Overlay-Only Rule (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`)**:
   - Module-relative bindings (`@at(image("name") + offset)` and `@at(image_self() + offset)`) MUST be **overlays** (`static` or `static mut` without `= init`, or `extern "<abi>" fn` without a `{ ... }` body).
   - Code or initialized data is **never placed** into a foreign module or at a load-time relocated `image(...) + offset` slot (`ADR-0001 §5`). Any `@at(image(...) + offset)` or `@at(image_self() + offset)` declaration carrying a static initializer `= init` or a function body `{ ... }` is rejected at compile time with `AX_UNSAFE_AT_FOREIGN_PLACEMENT`.
2. **Defined Layout (`AX_UNSAFE_INVALID_AT_LAYOUT`) & Offset Alignment (`AX_UNSAFE_AT_MISALIGNED`)**:
   - Every module-relative `static` / `static mut` overlay type `T` MUST satisfy the defined physical layout requirement of `SPEC-55 AXS-ADR-014` (`@repr(C)`, `@repr(packed)`, `@repr(transparent)`, primitive scalar, raw/fn pointer, SIMD vector, `Volatile`/`Mmio*`/`Atomic`, or fixed-size array/tuple thereof); layout-unspecified default `Repr.Axiom` structs are rejected with `AX_UNSAFE_INVALID_AT_LAYOUT`.
   - Since OS loaders align PE/ELF module base addresses (`__ImageBase` / `HMODULE`) to at least page granularity ($4096 = 2^{12}$ bytes), for any type `T` with $\text{align\_of}\langle T \rangle() \le 4096$ and compile-time constant `offset`, `compiler/sema/` verifies $(\text{offset} \bmod \text{align\_of}\langle T \rangle()) == 0$. If `offset % align_of<T>() != 0`, compilation fails with `AX_UNSAFE_AT_MISALIGNED` (alias `AX_UNSAFE_MISALIGNED_AT`).
   - Within the **same** target module key (`image("game.exe")` with identical normalized module name, or `image_self()`), two distinct non-union overlays whose constant offset intervals $[\text{off}_1, \text{off}_1 + S_1)$ and $[\text{off}_2, \text{off}_2 + S_2)$ overlap are rejected with `AX_UNSAFE_AT_OVERLAP`. No overlap check is performed across distinct module names (`ADR-0001 §5`).

[ADR-0001 §3, §5; SPEC-55 AXS-ADR-014]

### AXS-MOD-004 — Open-World Optimization Barrier (`REQ-ABI-095`, `REQ-FFI-119`), Explicit Export Surface (`REQ-FFI-042`) & Capability Lifetime Retention (`REQ-CAP-132`)

1. **Dynamic Module Loading as an Open-World Boundary (`REQ-ABI-095`, `REQ-FFI-119`, `tasks/0434 §53, §92 AFFI-70..71`, `tasks/0444 §185.152 AABIAPI-22..26`)**:
   - Dynamically loaded libraries and module-relative `@at(image("mod") + offset)` bindings constitute an **open-world boundary** (`OpenWorld`):
     a. Raw imported symbols and module-relative overlays have no compiler-verified cross-binary version contract; therefore calling or mutating them is an `unsafe` operation unless wrapped by an explicit version-checked host/plugin contract (`REQ-ABI-095`) or trusted at the `unsafe` item declaration (`ADR-0001 §2, §5`).
     b. In `compiler/opt/` (`SPEC-71`, `SPEC-73`, `SPEC-75`), every call or memory access through a module-relative slot (`LoadTimeSlot`) is treated as an opaque external side-effect and alias barrier (`MayAlias` / `GlobalEscape`). The optimizer is **forbidden** from applying closed-world reachability (`WPO`), constant propagation of foreign static contents, cross-module devirtualization, or dead-store/dead-code elimination across a dynamic library boundary (`REQ-FFI-119`).
2. **Explicit DLL Export Surface (`REQ-FFI-042`, `0138 §53`)**:
   - Building a dynamic library (`--kind dll`, `E18.7`) never exports internal module functions or statics by default. Only items explicitly annotated with `@export` or `@export("symbol_name")` (plus the compiler-generated `DllMain` entry point) are emitted into the PE `.edata` export directory (`REQ-FFI-042`).
3. **Capability Lifetime Retention Across Dynamic Libraries (`REQ-CAP-132`, `tasks/0451 §192.39 AFFI-33..34`)**:
   - Unloading a dynamically loaded library while safe capabilities (`view<T>`, `mut_view<T>`, or safe symbol handles) rooted in that library remain live would create dangling memory/code references. Therefore:
     - Safe dynamic symbol handles retain a lifetime/ownership dependency on their originating `Library` handle, preventing safe `Library.close()` / `FreeLibrary` while any derived capability is live (`REQ-CAP-132`).
     - Overlays declared via `@at(image("mod") + offset)` are bound for the lifetime of the enclosing module (`Provenance.Fixed` with static module lifetime) and require `"mod"` to remain loaded for the entire lifetime of the binding module (`ADR-0001 §5`).

[0138 §53; tasks/0434 §53, §92 AFFI-70..71; tasks/0444 §185.152 AABIAPI-22..26; tasks/0451 §192.39 AFFI-33..34; REQ-ABI-095; REQ-FFI-042; REQ-FFI-119; REQ-CAP-132]

### AXS-MOD-005 — Separation of Dynamic Linking and Module-Relative Overlays from Hot Reload (`REQ-ABI-032`, `REQ-ABI-033`, `0104 §54`)

1. **Dynamic Linking Does Not Imply Hot Reload (`REQ-ABI-033`)**:
   - Linking against a PE DLL, loading a plugin via `LoadLibraryW`, or binding addresses via `@at(image("mod") + offset)` resolves symbol and slot addresses **once** at module load/initialization time (`ADR-0001 §5`). Neither the compiler nor the runtime silently re-binds slots, migrates live heap/static state, or patches running stack frames after initialization (`REQ-ABI-033`).
2. **Hot Reload Requires an Explicit ABI & State-Transfer Contract (`REQ-ABI-032`)**:
   - Any system supporting live code/state reload must define an explicit versioned ABI state-handoff table (serialize/transfer state handle, drain in-flight fibers/threads, quiesce capabilities, unload old module, load new module, and re-initialize state) at the application/plugin boundary (`REQ-ABI-032`, `0104 §54`).

---

## 2. Load-Time Slot Resolution, Indirect Codegen, PE DLL/EXE Initializer Failure Hooks & Oracle Module Map (`AXS-MOD-010`..`014`)

### AXS-MOD-010 — HIR/THIR `PlacementAddr.ImageRel` Representation & MIR Load-Time Slot Lowering (`SPEC-04 AXS-EXT-032`, `SPEC-55 AXS-ADR-020`, `T531`)

1. **HIR/THIR Side Table (`compiler/hir/`)**:
   - A declaration with `@at(image("name") + offset)` or `@at(image_self() + offset)` records a `Placement` entry in the item attribute side table (`SPEC-04 AXS-EXT-032`, `SPEC-55 AXS-ADR-020`):
     - `kind = PlacementKind.Overlay` (placements are rejected per `AXS-MOD-003`).
     - `addr = PlacementAddr.ImageRel { module_name: Some(name_str_id), offset: offset_expr_id }` for `image("name") + offset`, or `PlacementAddr.ImageRel { module_name: None, offset: offset_expr_id }` for `image_self() + offset` (where `offset` defaults to `0usize` when omitted, e.g. `@at(image_self())`).
2. **MIR Load-Time Slot Lowering (`compiler/mir/`, `T531`)**:
   - For every module-relative overlay symbol `S` (whether `static`, `static mut`, or `extern "<abi>" fn`), `compiler/mir/` allocates a hidden 64-bit pointer slot symbol `__ax_modslot_<S>: usize` in the module's `.data` section and registers a descriptor `{ slot_sym: __ax_modslot_<S>, module_name: Option<StrId>, offset: u64 }` in the compilation unit's `ModuleRelocTable`.
   - **Data Overlays (`static` / `static mut`)**: Every access to `S` (field load/store, array index, `view(S)`, `mut_view(S)`, `static_addr(S)`, `addr_of(S)`, `address_of(S)`) loads the resolved base address `base_ptr: *mut T` from `__ax_modslot_<S>` and projects from `*base_ptr` with `Provenance.Fixed`.
   - **Function Overlays (`extern "<abi>" fn`)**: Calling `S(args...)` loads the resolved code pointer `fn_ptr` from `__ax_modslot_<S>` and executes an indirect `MirTerminator.Call { callee: Callee.FnPtr(fn_ptr), ... }` using `S`'s declared ABI (`Win64` / `C` / `System`). Querying `fn_addr(S)`, `addr_of(S)`, or `S as usize` reads the `usize` value stored in `__ax_modslot_<S>`.

### AXS-MOD-011 — LIR, x86-64 Indirect Slot Dispatch (`RIP`-Relative `.data` Slots) & `LoadTimeSlot` Object Descriptors (`SPEC-04 AXS-EXT-073`, `0187 §3, §23`, `T532`)

1. **No Hardcoded Foreign Addresses (`0187 §3, §23, §40 AIMPORT-29`)**:
   - Machine code emitted for module-relative overlays MUST NEVER embed hardcoded 64-bit virtual addresses. Instead, all accesses use 64-bit `RIP`-relative addressing through the `.data` slot `__ax_modslot_<S>` (`RelocKind.LoadTimeSlot`, `SPEC-04 AXS-EXT-073`):
     - **Function Call**: Emits `CALL qword ptr [rip + __ax_modslot_<S>]` (`FF 15 <disp32>`) or loads `MOV rax, qword ptr [rip + __ax_modslot_<S>]` followed by `CALL rax`.
     - **Static Field/Place Access**: Emits `MOV r64, qword ptr [rip + __ax_modslot_<S>]` and accesses `[r64 + field_offset]` (using exact-width volatile `MOV` instructions when the field is `Volatile<T>` / `Mmio*<T>`).
2. **Object Descriptor Table (`.axmodrel` / `.rdata` Init Table, `T532`)**:
   - `compiler/obj/` emits each `__ax_modslot_<S>` as an 8-byte aligned zero-initialized slot in `.data` (`READ | WRITE`) and emits a deterministic, sorted descriptor array `__ax_modrel_table` in `.rdata` where each entry records:
     ```axiom
     @repr(C)
     pub struct ModRelEntry {
         pub slot_rva: u32,       // RVA of the 8-byte slot in .data
         pub module_name_rva: u32,// RVA of UTF-16LE NUL-terminated module name in .rdata (0 for image_self())
         pub offset: u64,         // byte offset added to the resolved module base
     }
     ```

### AXS-MOD-012 — Load-Time Module Resolver (`GetModuleHandleW` / `__ImageBase`) & Deterministic PE DLL (`DllMain` Returns `FALSE`) / EXE Startup Failure Semantics (`ADR-0001 §5–6`, `REQ-OWNER-005`, `T532`)

1. **Resolution Before User Code Execution (`ADR-0001 §5`)**:
   - When `compiler/link/` links a PE32+ DLL (`--kind dll`, `T751`) or PE32+ executable (`--kind exe`) containing one or more `ModRelEntry` descriptors, the linker synthesizes the internal initialization routine `__ax_resolve_module_bindings() -> bool` and invokes it **before** any user `@entry`, `main`, or exported DLL function can execute:
     - For `module_name_rva == 0` (`image_self()`): the base address is `base = addr_of(__ImageBase)` (the runtime load address of the current PE image).
     - For `module_name_rva != 0` (`image("name")`): the resolver calls `KERNEL32.dll!GetModuleHandleW(wide_name_ptr)` to look up `"name"` among modules already loaded in the current process (`ADR-0001 §5`). (It intentionally uses `GetModuleHandleW` rather than `LoadLibraryW` because module-relative overlays bind to an in-process host or peer module that must already be present.)
     - If `base != 0usize`, the resolver writes `*(image_base + entry.slot_rva) = base + (entry.offset as usize)`.
2. **Deterministic Failure When a Target Module Is Not Loaded (`ADR-0001 §5–6`)**:
   - If `GetModuleHandleW` returns `0` (`NULL`) for any entry in `__ax_modrel_table`:
     - **In a PE DLL (`--kind dll`)**: `__ax_resolve_module_bindings()` immediately returns `false`, and the synthesized `DllMain(hinstDLL, fdwReason, lpvReserved)` on `DLL_PROCESS_ATTACH` (`fdwReason == 1`) immediately returns `0` (`FALSE`) without invoking any user `@entry` hook. Consequently, the Windows loader aborts attaching the DLL and `LoadLibraryW` returns `NULL` cleanly to the host process.
     - **In a PE Executable (`--kind exe`)**: the startup stub immediately triggers a deterministic startup panic (`panic: module-relative binding failed: target module '<name>' is not loaded`, exit code `101`) via `WriteFile(GetStdHandle(STD_ERROR_HANDLE), ...)` + `ExitProcess(101)`.
   - **Zero-Unresolved-Call Guarantee**: Under no circumstances can user code in a DLL or EXE ever call or dereference an unresolved `0` / `NULL` module-relative slot (`ADR-0001 §5`).

[ADR-0001 §5–6; OWNER.md REQ-OWNER-005, REQ-OWNER-006; 0187 §3–40; SPEC-04 AXS-EXT-073..074]

### AXS-MOD-013 — `REQ-OWNER-008` Self-Relative Offset Computation (`addr_of(target) - image_self()`) & Round-Trip Slot Identity (`ADR-0001 §5, §7`)

1. **Computing RVAs In-Process (`ADR-0001 §7`, `REQ-OWNER-008`)**:
   - Inside any module (such as a test host executable `game_host.exe`), code can compute the exact Relative Virtual Address (RVA) of any function or static variable at runtime via:
     ```axiom
     let fn_rva: usize = addr_of(host_add_item) - image_self()
     let state_rva: usize = addr_of(HOST_STATE) - image_self()
     ```
2. **Round-Trip Address Identity Across Module-Relative Overlays (`REQ-OWNER-005`, `REQ-OWNER-008`)**:
   - Once `__ax_resolve_module_bindings()` has succeeded for `@at(image("game_host.exe") + RVA) unsafe extern "C" fn game_add_item(...)` and `@at(image("game_host.exe") + STATE_RVA) unsafe static mut GAME_STATE: GameState`:
     $$\text{fn\_addr}(\text{game\_add\_item}) == \text{image}(\text{"game\_host.exe"}) + \text{RVA}$$
     $$\text{static\_addr}(\text{GAME\_STATE}) == \text{image}(\text{"game\_host.exe"}) + \text{STATE\_RVA}$$
   - And for any self-relative overlay `@at(image_self() + OFF) unsafe static TABLE: [256]u8`:
     $$\text{static\_addr}(\text{TABLE}) == \text{image\_self}() + \text{OFF}$$

### AXS-MOD-014 — Oracle (`--interp`) Simulated Process Module Map & Deterministic Missing-Module Failure (`ADR-0001 §4–5`, `T531`)

To make `@at(image("mod") + offset)` and `@at(image_self() + offset)` 100% testable in the MIR interpreter (`axiomc run --interp`) and differential test suites (`INV-ORACLE-002`):
1. **Simulated Process Module Map (`ProcessModuleMap` in `compiler/interp/`, `T531`)**:
   - The interpreter maintains a deterministic map `module_name -> ModuleImage { base_addr: usize, size: usize }` alongside `FixedAddrMap` (`SPEC-55 AXS-ADR-024`):
     - `image_self()` always resolves to the current module's simulated base address (default `0x0000_0001_4000_0000usize`, matching standard PE32+ `ImageBase`), and every function/static in the current module has a deterministic simulated RVA so `addr_of(item) - image_self()` works identically in `--interp` and native execution.
     - Simulated foreign modules can be registered in `--interp` via test harness directives / CLI `--interp-module <name>=<base_hex>` or via the intrinsic/test-harness hook mapping a foreign module name (e.g. `"game.exe"`) to a simulated base address (e.g. `0x0000_0001_8000_0000usize`) or aliasing the current module's simulated image.
2. **Pre-Entry Slot Resolution & Missing-Module Failure in `--interp`**:
   - Before executing `main` or `@entry` in `--interp`, the interpreter runs the simulated `__ax_resolve_module_bindings()` pass over all `PlacementAddr.ImageRel` items:
     - If every referenced `image("name")` exists in `ProcessModuleMap`, its slot `__ax_modslot_<S>` is populated with `base_addr + offset`.
     - If any referenced `image("name")` is absent from `ProcessModuleMap`, the interpreter aborts module initialization deterministically before running user code with diagnostic/panic `AX_UNSAFE_MODULE_NOT_LOADED` (exit code `101` in EXE mode, or returning `false` to a simulated DLL load request), matching native Windows behavior (`AXS-MOD-012`).

---

## 3. Diagnostics, Positive/Negative Canonical Examples & Conformance Matrix (`AXS-MOD-050`..`053`)

### AXS-MOD-050 — Module-Relative Binding Diagnostic Taxonomy

| Diagnostic Code | Severity | Emitting Stage | Condition |
|---|---|---|---|
| `AX_UNSAFE_AT_FOREIGN_PLACEMENT` | `error` | `sema` / `hir` | `@at(image("...") + off)` or `@at(image_self() + off)` declaration has an initializer `= init` or a function body `{ ... }` (`ADR-0001 §5`: module-relative bindings are overlay-only; never place code/data into a module-relative slot). |
| `AX_TYPE_INVALID_IMAGE_ARG` | `error` | `sema` / `typeck` | `image(...)` called with a non-string-literal argument, an empty string `""`, or wrong argument count, or `image_self(...)` called with arguments (`AXS-MOD-001`). |
| `AX_UNSAFE_INVALID_AT_LAYOUT` | `error` | `sema` / `types` | Module-relative overlay type `T` does not have a defined physical layout (`@repr(C)`, `@repr(packed)`, `@repr(transparent)`, or primitive/array, `AXS-MOD-003`, `SPEC-55 AXS-ADR-014`). |
| `AX_UNSAFE_AT_MISALIGNED` (alias `AX_UNSAFE_MISALIGNED_AT`) | `error` | `sema` / `types` | Constant RVA `offset` in `@at(image(...) + offset)` is not a multiple of `align_of<T>()` (`offset % align_of<T>() != 0`, `AXS-MOD-003`). |
| `AX_UNSAFE_AT_OVERLAP` | `error` | `sema` | Two module-relative overlays targeting the same module (`image("mod")` or `image_self()`) have overlapping constant RVA ranges (`AXS-MOD-003`). |
| `AX_UNSAFE_REQUIRED` | `error` | `sema` | Accessing or calling a module-relative binding that was not declared `unsafe` on the item without an enclosing `unsafe` block (`AXS-MOD-002`, `REQ-ABI-095`). |
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `error` | `sema` / `driver` | `image("name")` used in `--profile freestanding` or `--profile kernel` where no hosted dynamic module table exists (`AXS-MOD-001`). |

### AXS-MOD-051 — Canonical Positive Examples (In-Process Game Plugin DLL Binding Host Functions/State & `addr_of(target) - image_self()`)

```axiom
use std.core.mem.{addr_of, address_of_mut, fn_addr, static_addr, image, image_self}

@repr(C)
pub struct Player {
    pub id: u32,
    pub gold: i32,
}

@repr(C)
pub struct GameState {
    pub player_count: i32,
    pub active_id: u32,
    pub main_player: Player,
}

// 1. Foreign module overlays in a hosted plugin DLL targeting "game_host.exe":
@at(image("game_host.exe") + 0x1000usize)
unsafe extern "C" fn game_add_gold(player: *mut Player, amount: i32) -> i32

@at(image("game_host.exe") + 0x4000usize)
unsafe static mut GAME_STATE: GameState

// 2. Self-relative overlay targeting an RVA inside the current module:
@at(image_self() + 0x2000usize)
unsafe static BONUS_TABLE: [4]i32

@export
pub extern "C" fn plugin_grant_bonus() -> i32 {
    // Ordinary Axiom syntax after unsafe @at(image(...)) declarations (ADR-0001 §5):
    if GAME_STATE.player_count > 0 {
        let bonus = BONUS_TABLE[0] + 50
        let player_ptr = unsafe { address_of_mut(GAME_STATE.main_player) }
        let new_total = game_add_gold(player_ptr, bonus)
        assert(fn_addr(game_add_gold) == image("game_host.exe") + 0x1000usize)
        assert(static_addr(GAME_STATE) == image("game_host.exe") + 0x4000usize)
        return new_total
    }
    return 0
}
```

### AXS-MOD-052 — Canonical Negative Examples

1. **Foreign Placement Forbidden (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`)**:
   `@at(image("game.exe") + 0x2000usize) unsafe static mut PATCH: u32 = 0x9090_9090u32` or `@at(image("game.exe") + 0x1000usize) unsafe fn hook() {}` — rejected because code and initialized data cannot be placed into `image(...) + offset`.
2. **Invalid `image(...)` Argument (`AX_TYPE_INVALID_IMAGE_ARG`)**:
   `@at(image("") + 0x100usize) unsafe static X: u32` — rejected because the module name literal cannot be empty.
3. **Misaligned RVA Offset (`AX_UNSAFE_AT_MISALIGNED`)**:
   `@at(image("game.exe") + 0x1002usize) unsafe static BAD_U32: u32` — rejected because `0x1002 % align_of<u32>() != 0`.
4. **Unspecified Struct Layout (`AX_UNSAFE_INVALID_AT_LAYOUT`)**:
   `struct HostData { a: u32, b: u8 }` (missing `@repr(C)`) used in `@at(image("game.exe") + 0x3000usize) unsafe static DATA: HostData` — rejected with `AX_UNSAFE_INVALID_AT_LAYOUT`.

### AXS-MOD-053 — E13.7 Verification & Conformance Matrix (`T531`–`T533`)

| Task | Verification Target | Certified Invariants & Requirements |
|---|---|---|
| `T531` | `tests/ui/module_rel`, `tests/run/module_rel_oracle` | `image("name")` and `image_self()` typing (`AX_TYPE_INVALID_IMAGE_ARG`), overlay-only enforcement (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`), `@repr(C)` layout and offset alignment checks, `PlacementAddr.ImageRel` HIR/MIR slot lowering, `REQ-CAP-132` capability retention, and `--interp` `ProcessModuleMap` simulation (including clean init failure on missing module). |
| `T532` | `tests/link/module_rel_dll` | Native `.data` slot emission (`__ax_modslot_*`), `.rdata` `ModRelEntry` descriptor table, x86-64 `RIP`-relative indirect call/load codegen (`REQ-FFI-119`, `REQ-ABI-095` open-world barrier), `GetModuleHandleW` / `__ImageBase` load-time resolver in PE DLL `DllMain` (`DLL_PROCESS_ATTACH`) and EXE startup, and `DllMain` returning `FALSE` (`LoadLibraryW == NULL`) when a target module is missing. |
| `T533` | `tests/conformance/p13/e13_7_module_relative` | End-to-end E13.7 conformance suite certifying host EXE (`game_host.exe`) + plugin PE DLL (`mod_plugin.dll`, `REQ-FFI-042` explicit exports) + negative missing-module DLL (`bad_plugin.dll`) across `--interp` and native Windows x64 execution (`0 WEAK-NATIVE`, `REQ-OWNER-005`). |

## Sources
`spec/decisions/ADR-0001-fixed-address-declarations.md (§5–6, §7)`; `spec/requirements/OWNER.md (REQ-OWNER-005, REQ-OWNER-006, REQ-OWNER-008)`; `specs/0104 (§53–54)`; `specs/0138 (§53)`; `specs/0187 (§3–40, AIMPORT-20..30)`; `tasks/0336 (BOOTSTRAP-077)`; `tasks/0434 (§53, §92, AFFI-70..71)`; `tasks/0444 (§185.152, AABIAPI-22..26)`; `tasks/0451 (§192.39, AFFI-33..34)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-04-core-extensibility.md (AXS-EXT-032, AXS-EXT-070, AXS-EXT-073..074)`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-55-fixed-address-declarations.md`.
