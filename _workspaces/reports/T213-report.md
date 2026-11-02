# T213 Report — Plan phase P13: Low-level systems, unsafe, freestanding, security

## Tóm tắt
Đã mở rộng toàn bộ giai đoạn P13 (`P13-low-level-systems-unsafe-frees`) từ 7 epic (`E13.1`–`E13.7`) trong `spec/ROADMAP.md` thành 34 task cụ thể (`T500`–`T533` trong dải `T500`–`T549` của P13, từ 4 đến 6 task mỗi epic), bao gồm đặc tả, cài đặt và kiểm thử chuẩn cho **`REQ-OWNER-008`** (`fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, và `@addr(<expr>)` cho `static`, `let`, `fn`, kể cả biểu thức động `let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;` và kiểm tra khứ hồi `fn_addr(isr) == 0x2000_0000usize`), **`REQ-OWNER-003`** (`@at`), **`REQ-OWNER-005`** (`@at(image("mod") + off)`), và oracle ABI Windows x64 độc lập bằng DLL `gcc -shared` (`ADR-0034 §8 / OI-12`, task `T503`) trước khi mở rộng FFI (`T504`); chuyển toàn bộ 434 dòng `EPIC(E13.*)` trong `spec/requirements/CATALOG.md` sang ID task cụ thể (`T500`–`T533`), cập nhật `T313` phụ thuộc vào tất cả task P13, và ghi nhận vào `spec/ROADMAP.md`.

## Summary
Expanded Phase P13 (`P13-low-level-systems-unsafe-frees`) across all seven roadmap epics (`E13.1`–`E13.7`) into 34 concrete, single-sitting tasks (`T500`–`T533` in the `T500`–`T549` P13 block), converted all 434 `EPIC(E13.*)` rows in `spec/requirements/CATALOG.md` (including `REQ-OWNER-003`, `REQ-OWNER-005`, and `REQ-OWNER-008`) to concrete `T500`–`T533` task IDs with matching `covers:` lists, wired `T313` (`depends: [T213, T500..T533]`), and updated `spec/ROADMAP.md`.

### Epic breakdown
1. **E13.1 Unsafe & UB model** (6 tasks: `T500`–`T505`):
   - `T500` (`axiom-architect`): Canonical `spec/SPEC-50-unsafe-ub-ffi.md` (`unsafe` blocks/fns/traits/impls, UB taxonomy, strict pointer provenance, FFI/ABI contracts, and `REQ-OWNER-008` `fn_addr`, `static_addr`, `address_of(v) as usize`, and `@addr(<expr>)` on `static`, `let`, and `fn` including dynamic `base + offset` and round-trip assertions; 135 reqs).
   - `T501` (`axiom-semantics`): `unsafe` context checking, raw-pointer-to-view provenance tracking, and `REQ-OWNER-008` address intrinsics (`fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) as usize`, and `@addr(<expr>)` on `static`, `let`, and `fn`; 45 reqs).
   - `T502` (`axiom-semantics`): Oracle (`--interp`) strict-provenance & UB detector (use-after-free, unaligned, uninitialized, aliasing) and `REQ-OWNER-008` round-trip evaluation (33 reqs).
   - `T503` (`axiom-qa`): External Windows x64 ABI oracle (`ADR-0034 §8 / OI-12` carry-over before FFI breadth: `gcc -shared` test DLL exporting 1..8 mixed-width args and size 1/2/3/4/8/12/16/24 structs by value/return called via `@link`, gcc `offsetof`/`sizeof` table for `@repr(C)` layouts, and `NDEBUG`-safe `tests/mc/isel/cdriver_abi*.c` audit; 33 reqs).
   - `T504` (`axiom-backend`, depends on `T501, T503`): FFI & C ABI breadth (`@repr(C)`/`@repr(transparent)`/`@abi(stable)`, C callbacks, opaque extern types) and native x86-64 codegen for `REQ-OWNER-008` (`fn_addr`, `static_addr`, `address_of(v) as usize`, `@addr(<expr>)`; 83 reqs).
   - `T505` (`axiom-qa`): Unsafe, UB, provenance, FFI & `REQ-OWNER-008` address-placement conformance suite (24 reqs).
2. **E13.2 Raw memory, volatile, MMIO, layout control** (5 tasks: `T506`–`T510`):
   - `T506` (`axiom-architect`): Canonical `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` (volatile, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>`, `union`, `@repr(packed)`/`@align(N)`, bitcasts, address spaces; 6 reqs).
   - `T507` (`axiom-semantics`): Untagged `union` types, `@repr(packed)`/`@align(N)`, unaligned field diagnostics, and address-space type checking (5 reqs).
   - `T508` (`axiom-backend`): MIR/LIR/x64 volatile load/store/fence lowering, non-tearing width guarantees, and unaligned codegen (2 reqs).
   - `T509` (`axiom-stdlib`): `std.mem.volatile`, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>`, `MaybeUninit<T>`, `ManuallyDrop<T>`, `bitcast`, and layout introspection API (4 reqs).
   - `T510` (`axiom-qa`): Raw memory, volatile, MMIO, union & layout-control conformance suite (16 reqs).
3. **E13.3 Runtime composition & freestanding profile** (5 tasks: `T511`–`T515`):
   - `T511` (`axiom-architect`): Canonical `spec/SPEC-52-freestanding-runtime-composition.md` (`hosted`/`freestanding`/`kernel`/`system` profiles, `@entry`, `extern "interrupt"`, runtime capability graph; 2 reqs).
   - `T512` (`axiom-semantics`): Profile checking (`--profile freestanding|kernel|system|hosted`), `@entry`/`@naked`/`@section`/`@used`, interrupt-domain verification, and runtime capability graph (2 reqs).
   - `T513` (`axiom-backend`): Freestanding startup, static init order, custom section layout, and CRT-free native image emission (6 reqs).
   - `T514` (`axiom-stdlib`): Freestanding `std.core` subset, explicit panic/alloc/DMA hooks, and zero-OS runtime layer (9 reqs).
   - `T515` (`axiom-qa`): Freestanding boot-without-std & runtime composition conformance suite (5 reqs).
4. **E13.4 Safety profiles & capability security** (5 tasks: `T516`–`T520`):
   - `T516` (`axiom-architect`): Canonical `spec/SPEC-53-safety-profiles-capability-security.md` (`@forbid_unsafe`, capability authority tokens, `Secret<T>`, `@constant_time`; 4 reqs).
   - `T517` (`axiom-semantics`): Safety profile enforcement (`@forbid_unsafe`, capability-only IO/net/fs, sandbox verification; 3 reqs).
   - `T518` (`axiom-backend`): Constant-time secret types (`@secret` / `Secret<T>`) branch/index/timing-leak verifier & barrier lowering (3 reqs).
   - `T519` (`axiom-stdlib`): `std.security` capability tokens, zeroize-on-drop `Secret<T>`, constant-time primitives, and sandbox hooks (4 reqs).
   - `T520` (`axiom-qa`): Safety profiles, capability security & constant-time conformance suite (4 reqs).
5. **E13.5 Panic & unwinding strategy** (4 tasks: `T521`–`T524`):
   - `T521` (`axiom-architect`): Canonical `spec/SPEC-54-panic-unwinding.md` (`--panic abort|unwind`, FFI no-unwind barrier, deterministic `Drop` cleanup; 10 reqs).
   - `T522` (`axiom-semantics`): `--panic abort|unwind` mode, `@no_panic` verification, `catch_unwind`, and FFI boundary abort guards (4 reqs).
   - `T523` (`axiom-backend`): Native MIR cleanup landing pads, Windows x64 SEH `.pdata`/`.xdata` unwind tables, and deterministic drop unwinding (4 reqs).
   - `T524` (`axiom-qa`): Panic strategy, drop cleanup across unwind & FFI boundary abort conformance suite (4 reqs).
6. **E13.6 Fixed-address declarations (`@at`)** (5 tasks: `T525`–`T529`):
   - `T525` (`axiom-architect`): Canonical `spec/SPEC-55-fixed-address-declarations.md` (`ADR-0001` §1–4 & §7, `REQ-OWNER-003`, `REQ-OWNER-008`: `@at`/`@addr` overlays and placements, `fn_addr`/`static_addr`/`address_of` round-trip, pinned sections, oracle device model; 2 reqs).
   - `T526` (`axiom-semantics`): `@at` / `@addr` placement & overlay HIR/THIR/MIR lowering, `fixed` provenance, overlap & layout checks (8 reqs).
   - `T527` (`axiom-semantics`): Oracle simulated address space & scriptable MMIO/UART/vector-table device model for `@at` / `@addr` (2 reqs).
   - `T528` (`axiom-backend`): COFF/PE `IMAGE_SYM_ABSOLUTE` symbols, pinned VMA sections, and freestanding raw-binary image writer for `@at` / `@addr` (2 reqs).
   - `T529` (`axiom-qa`): Fixed-address (`@at` / `@addr`) vector table, UART MMIO & `REQ-OWNER-003`/`008` round-trip conformance suite (2 reqs).
7. **E13.7 Module-relative bindings** (4 tasks: `T530`–`T533`):
   - `T530` (`axiom-architect`): Canonical `spec/SPEC-56-module-relative-bindings.md` (`ADR-0001 §5–6`, `REQ-OWNER-005`: `@at(image("mod") + off)`, `image_self()`, load-time slots, `DllMain` failure contract; 4 reqs).
   - `T531` (`axiom-semantics`): `image("mod")` / `image_self()` overlay expressions, load-time slot HIR/MIR lowering, and oracle module-map simulation (2 reqs).
   - `T532` (`axiom-backend`, depends on `T528, T531, T751`): Load-time module resolver, indirect slot codegen, and PE DLL/EXE initialiser failure hooks (`REQ-OWNER-005`; 2 reqs).
   - `T533` (`axiom-qa`): Module-relative bindings (`@at(image("mod") + off)`) host EXE + test DLL conformance suite (2 reqs).

## Files changed
- ./_workspaces/tasks/todo/T213-plan-phase-p13-low-level-systems-unsafe-freestanding-securit.md
- ./_workspaces/tasks/todo/T313-phase-p13-gate-low-level-systems-unsafe-freestanding-securit.md
- ./_workspaces/tasks/todo/T500-e13-1-unsafe-ub-provenance-ffi-addr-spec.md
- ./_workspaces/tasks/todo/T501-e13-1-typeck-mir-unsafe-provenance-req-owner-008.md
- ./_workspaces/tasks/todo/T502-e13-1-oracle-strict-provenance-ub-detector.md
- ./_workspaces/tasks/todo/T503-e13-1-external-win64-abi-gcc-dll-oracle.md
- ./_workspaces/tasks/todo/T504-e13-1-ffi-abi-breadth-and-native-req-owner-008.md
- ./_workspaces/tasks/todo/T505-e13-1-unsafe-ub-ffi-req-owner-008-conformance.md
- ./_workspaces/tasks/todo/T506-e13-2-raw-memory-volatile-mmio-layout-spec.md
- ./_workspaces/tasks/todo/T507-e13-2-unions-packed-align-address-space-sema.md
- ./_workspaces/tasks/todo/T508-e13-2-mir-lir-x64-volatile-unaligned-codegen.md
- ./_workspaces/tasks/todo/T509-e13-2-std-mem-volatile-mmio-maybeuninit-layout.md
- ./_workspaces/tasks/todo/T510-e13-2-volatile-mmio-union-layout-conformance.md
- ./_workspaces/tasks/todo/T511-e13-3-freestanding-runtime-composition-spec.md
- ./_workspaces/tasks/todo/T512-e13-3-profile-checking-entry-naked-capability-graph.md
- ./_workspaces/tasks/todo/T513-e13-3-freestanding-startup-sections-crt-free-link.md
- ./_workspaces/tasks/todo/T514-e13-3-std-core-freestanding-panic-alloc-hooks.md
- ./_workspaces/tasks/todo/T515-e13-3-freestanding-boot-without-std-conformance.md
- ./_workspaces/tasks/todo/T516-e13-4-safety-profiles-capability-security-spec.md
- ./_workspaces/tasks/todo/T517-e13-4-safety-profile-forbid-unsafe-sandbox-sema.md
- ./_workspaces/tasks/todo/T518-e13-4-constant-time-secret-verifier-barrier-codegen.md
- ./_workspaces/tasks/todo/T519-e13-4-std-security-secret-zeroize-ct-caps.md
- ./_workspaces/tasks/todo/T520-e13-4-safety-profiles-security-conformance.md
- ./_workspaces/tasks/todo/T521-e13-5-panic-unwinding-ffi-barrier-spec.md
- ./_workspaces/tasks/todo/T522-e13-5-panic-mode-no-panic-catch-unwind-mir-oracle.md
- ./_workspaces/tasks/todo/T523-e13-5-native-landing-pads-win64-seh-drop-unwinding.md
- ./_workspaces/tasks/todo/T524-e13-5-panic-strategy-unwind-drop-conformance.md
- ./_workspaces/tasks/todo/T525-e13-6-fixed-address-at-addr-declarations-spec.md
- ./_workspaces/tasks/todo/T526-e13-6-at-addr-hir-sema-mir-overlap-layout.md
- ./_workspaces/tasks/todo/T527-e13-6-oracle-simulated-address-space-mmio-device.md
- ./_workspaces/tasks/todo/T528-e13-6-coff-absolute-symbols-pinned-sections-raw-image.md
- ./_workspaces/tasks/todo/T529-e13-6-fixed-address-vector-uart-conformance.md
- ./_workspaces/tasks/todo/T530-e13-7-module-relative-bindings-image-spec.md
- ./_workspaces/tasks/todo/T531-e13-7-image-overlay-hir-mir-oracle-module-map.md
- ./_workspaces/tasks/todo/T532-e13-7-load-time-module-resolver-pe-dll-init-codegen.md
- ./_workspaces/tasks/todo/T533-e13-7-module-relative-host-exe-dll-conformance.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T313` and `T500`–`T533`: `OK` (35 files).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`: `OK (335 tasks)`.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: `gaps: 0`, `COVERAGE OK` (all 434 `EPIC(E13.*)` rows converted to concrete `T500`–`T533` tasks; `v1-full planned=1227`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T213`: `0 REFUSED`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE
