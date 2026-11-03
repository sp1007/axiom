# SPEC-85 — Canonical Android AArch64 Bionic ELF Target & Capability-Safe JNI Binding Specification

Status: draft (T669, 2026-11-04). Owner: axiom-architect.
Consolidates: `SPEC-04` (extensibility & host intrinsics), `SPEC-24` (`.axmi`/`ObjectArtifact`), `SPEC-27` (`LinkIR`), `SPEC-30` (`Send`/`Share`), `SPEC-50` (`unsafe` & `extern "C"` FFI), `SPEC-51` (`@addr_space`), `SPEC-52` (profiles & runtime composition), `SPEC-54` (panic & FFI no-unwind barrier), `SPEC-56` (`image(...)` overlays), `SPEC-81` (`TargetDesc` & `verify_mc`), `SPEC-82` (ELF64 `ET_DYN` dynamic linking), `SPEC-83` (`Arch.AArch64` & `CallConv.Aapcs64`), `0193`, `0197`, `0198` (§1–41, `AANDROID-20..44`), `0200` (§1–61, `AJNI-20..52`), `0220` (§1–4, §9, §16, §18, §28–39 `AOS-20..40`), `tasks/0453` (§194.1–44 `ATARGET-20..50`), `tasks/0518` (§151 `AMACHINE-80..89`, memory codegen provenance), `tasks/0523` (§155 `AWASM-41, 81, 83, 84, 93`).
Covers: `REQ-TGT-069`, `REQ-TGT-070`, `REQ-TGT-071`, `REQ-TGT-072` (and specifies the E16.5 contract for `T670`, `T671`, `T672`: `REQ-TGT-073`..`REQ-TGT-078`, `REQ-TGT-110`, `REQ-TGT-230`, `REQ-TGT-270`, `REQ-TGT-272`, `REQ-TGT-273`, `REQ-TGT-282`).
Consumers: `compiler/target/aarch64/android`, `compiler/link/elf_android`, `std/sys/android`, `std/ffi/jni`, `compiler/hir/jni_attr`, `tests/obj/android`, `tests/selfhost/link`, `tests/run/jni`, `tests/selfhost/hir`, `tests/conformance/p16/e16_5_android_aarch64_jni`, `T670`, `T671`, `T672`.

## Tóm tắt
Đặc tả chuẩn cho đích biên dịch Android ARM64 (`aarch64-android`) dựa trên Bionic ELF64 và kiến trúc kết nối JNI an toàn theo năng lực (capability-safe JNI) của Axiom trong Epic `E16.5`:
1. **Đích `aarch64-android`, định danh mức API & quy ước gọi AAPCS64 bảo toàn `X18`**: Tái sử dụng tầng tập lệnh `Arch.AArch64` và `CallConv.Aapcs64` từ `SPEC-83`, gắn `api_level` (mặc định `29`, tối thiểu `21`) vào `TargetDesc` và `TargetFingerprint` (`0198 §2–3`), dành riêng tuyệt đối thanh ghi `X18` cho Android ShadowCallStack (`SCS`), tách biệt hạ tầng sinh mã vật lý khỏi cú pháp con trỏ/tham chiếu và ngữ nghĩa `Copy`/`Move`/`Drop`/năng lực/không gian địa chỉ CPU–GPU của Axiom Core (`REQ-TGT-069..078`, `REQ-TGT-110`).
2. **Liên kết động Bionic ELF64 căn lề trang 16 KiB không cần Android NDK & `std.sys.android`**: Mọi ảnh chạy được (`--kind exe` PIE với `PT_INTERP = "/system/bin/linker64\0"` và `--kind dll` `lib<stem>.so` với `DT_SONAME`) đều xuất `ET_DYN` với `p_align = 0x4000` (16 KiB, chuẩn Android 15+), ghi chú `.note.android.ident`, Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`), kiểm tra mức API & namespace thư viện công khai qua danh mục stub Bionic tích hợp sẵn (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`, `0198 §4, §10–29`), và hiện thực `std.sys.android` tích hợp `__android_log_write`.
3. **Kiến trúc JNI 3 tầng an toàn năng lực (`std.ffi.jni.raw`, `std.ffi.jni`, `@jni_export`)**: Mô hình hóa tham chiếu JVM như foreign handle mờ thuộc miền thực thi `JVM` tách biệt khỏi con trỏ bộ nhớ tuyến tính (`REQ-TGT-230`, `REQ-TGT-272..273`, `REQ-TGT-282`); khoá `JniEnv` theo luồng (`!Send`, `!Share`, chỉ truyền qua `view<JniEnv>` / `mut_view<JniEnv>`); giải phóng tất định `JLocal<T>`, `JGlobal<T>`, `JWeak<T>`, khung `with_local_frame` và luồng đính kèm `JavaVM.with_attached_env`; bắt buộc kiểm tra `ExceptionCheck`/`ExceptionClear` sang `JException` / `Result<T, JniError>`.
4. **Hạ tầng `@jni_export` & kiểm thử tất định**: Sinh hàm cầu nối `extern "C"` (`Java_<pkg>_<cls>_<method>` và bảng `JNI_OnLoad` `RegisterNatives`), chặn thoát `JLocal<T>`, chuyển lỗi/panic Axiom thành ngoại lệ Java (`Throw`/`ThrowNew`) mà không bao giờ unwind xuyên qua khung JVM (`REQ-TGT-270`, `SPEC-54 AXS-PAN-020..022`), kèm bộ giả lập `MockJvm` chạy trên cả `--interp` lẫn mã máy mọi hệ chủ.

---

## 1. `aarch64-android` Target Descriptor, `X18` ShadowCallStack & Backend Representation Independence

**AXS-ANDR-001 — Canonical Target Identity & API-Level Fingerprint (`0198 §1–3, AANDROID-20, 23..24, 43`, `tasks/0453 §194.3, 194.41`).** `TargetId.AArch64Android` identifies 64-bit ARMv8-A Android over the Linux kernel and Bionic C runtime (`Arch.AArch64`, `Os.Android`, `Env.Bionic`, `Endian.Little`, `ptr_bits = 64`). CLI `--target aarch64-android` is canonical; NDK/LLVM spellings `aarch64-linux-android` and `aarch64-linux-android<N>` normalize to `TargetId.AArch64Android` (where suffix `<N>` sets `api_level = N`). The Android API level (`--android-api <N>` or `axiom.toml` `[target.aarch64-android] api_level = N`) defaults to **`29`** (Android 10) and MUST satisfy `21 <= api_level <= 99`; values `< 21` (64-bit `arm64-v8a` did not exist prior to API 21), non-integers, or conflicting `--target aarch64-linux-android<M>` vs `--android-api <N>` (`M != N`) fail with `AX_DRIVER_INVALID_ANDROID_API` (exit code `2`). `api_level` is hashed directly into the 128-bit `TargetFingerprint` (`SPEC-22`, `SPEC-81 AXS-TGTD-003`) so `.axmi`, `.o`, and incremental cache entries never alias across distinct Android API levels.

**AXS-ANDR-002 — Artifact Taxonomy & APK/AAB Separation (`0198 §5–6, 19, 21–22, 32, AANDROID-31..32, 42`).** `aarch64-android` strictly separates native ELF compilation/linking from Android application packaging (`.apk`, `.aab`, `classes.dex`, `AndroidManifest.xml`, signing):
1. `--kind exe`: `<stem>` — `ET_DYN` Position-Independent Executable (`PIE`) with `/system/bin/linker64` interpreter for CLI tools, native test runners (`adb shell`), and daemons.
2. `--kind obj`: `<stem>.o` — ELF64 relocatable object (`ET_REL`, `EM_AARCH64 = 183`).
3. `--kind lib`: `lib<stem>.a` — deterministic GNU System V `ar` static archive (`SPEC-80 AXS-ELFS-029`).
4. `--kind dll`: `lib<stem>.so` — `ET_DYN` shared object with `DT_SONAME = "lib<stem>.so"` and no `PT_INTERP`, ready for direct placement into an APK/AAB `lib/arm64-v8a/lib<stem>.so` directory or loading via `System.loadLibrary("<stem>")` / `dlopen`.

**AXS-ANDR-003 — `DataLayout` & AArch64 ISA Reuse (`0198 §1, §7, AANDROID-20..21`, `SPEC-83 AXS-A64-001..003`).** `TargetId.AArch64Android` reuses the OS-independent `Arch.AArch64` 32-bit A64 encoder, `RegisterFile`, instruction selector, and `verify_mc` rules of `SPEC-83` without duplicating ISA tables (`AANDROID-20..21`). Baseline hosted features are `+fp` and `+neon` (`ARMv8.0-A`); optional features (`+lse`, `+crc`, `+crypto`, `+dotprod`, `+fp16`, `+sve`, `+bti`, `+pauth`) are enabled only via explicit `--target-feature` or `@target_feature` (`AX_TARGET_FEATURE_MISMATCH`). Pointer, `usize`, and `isize` are 64-bit (`size = 8`, `align = 8`); `i128`/`u128` have `size = 16`, `align = 16`; `max_page_size = 16384` (`0x4000`), while A64 `ADRP` hardware page granularity remains `4096` (`0x1000`).

**AXS-ANDR-004 — `CallConv.Aapcs64` & Absence of Platform-Specific Core ABIs (`0198 §7–8, §14, AANDROID-21, 29`).** Function calls on `aarch64-android` use standard `CallConv.Aapcs64` (`SPEC-83 AXS-A64-013..023`): `X0..X7` for integer/pointer scalars and `<= 16`-byte general composites, `X8` (`XR`) for indirect `sret` (`> 16`-byte non-`HFA`/`HVA` returns) without consuming `X0`, `V0..V7` for floating-point/NEON scalars and `<= 4`-element `HFA`/`HVA` aggregates, `X19..X28` and low 64-bit `D8..D15` callee-saved, `X29` (`FP`) + `X30` (`LR`) frame record, 16-byte `SP` alignment at every call and memory access, and `red_zone_bytes = 0`. Platform and JNI boundaries use `extern "C"`; Axiom defines **no** `extern "android"` or `extern "JNI"` ABI string (rejected with `AX_FFI_UNKNOWN_ABI`).

**AXS-ANDR-005 — Strict `X18` Reservation for Android ShadowCallStack (`0198 §7`, `SPEC-83 AXS-A64-009`).** On `aarch64-android`, Bionic and ART reserve `X18` (`W18`) as the per-thread **ShadowCallStack (`SCS`)** pointer. `compiler/target/aarch64/android` marks `X18` as `RegRole.Reserved`: register allocation (`LinearScan`/`Graph`), spill/reload, `PLT` stubs (`X16`/`X17` only), `±128 MiB` branch veneers (`X16` only), inline assembly/intrinsics, and `std.sys.android` stackful fiber switches MUST NOT read, write, save, restore, or clobber `X18`. Pre-encoding `verify_mc` rejects any Machine IR instruction referencing `X18`/`W18` on `aarch64-android` with `AX_VERIFY_MC_ILLEGAL` (`data.rule = "android_x18_scs_reserved"`).

**AXS-ANDR-006 — Source-Syntax Independence & Internal Pointer Lowering (`tasks/0518 §151 AMACHINE-80..81`, `REQ-TGT-069`, `REQ-TGT-070`).** Machine code generation on `aarch64-android` is completely independent of source-level pointer or reference syntax (`REQ-TGT-069`): Axiom Core exposes values, `view<T>`, `mut_view<T>`, and typed foreign handles (`JLocal<T>`, `JGlobal<T>`), never `&T`/`&mut T`. Below `Verified MIR` and `Axiom LIR`, the machine backend MAY represent indirect `> 16`B aggregate arguments, `X8` `sret` buffers, `GOT`/`PLT` entries, and `JNIEnv*` vtable slots as physical 64-bit addresses without exposing raw pointers to safe Core (`REQ-TGT-070`).

**AXS-ANDR-007 — Physical Temporaries, Physical Copies & Semantic `Move` Independence (`tasks/0518 §151 AMACHINE-82..84`, `REQ-TGT-071`, `REQ-TGT-072`, `REQ-TGT-073`).** During A64 instruction selection, ABI marshalling, and register allocation on `aarch64-android`:
1. The backend MAY materialize physical temporaries (scratch registers `X9..X15`, `X16`/`X17` address intermediates, stack spill slots) without introducing semantic temporaries or extra `Drop` obligations (`REQ-TGT-071`).
2. Physical register-to-register (`MOV`) or stack-to-register (`LDR`/`STP`) bit-copies used to pass or spill a `!Copy` value (such as `JLocal<T>`, `JGlobal<T>`, `String`, or `MutexGuard<T>`) DO NOT imply semantic `Copy` (`REQ-TGT-072`).
3. Conversely, a semantic `Move` in Core/MIR DOES NOT require any physical memory or register movement when coalesced in place (`NRVO`, `X8` `sret` construction, or register aliasing) (`REQ-TGT-073`).

**AXS-ANDR-008 — Preservation of `Drop`, Capability Validity & Pointer Provenance (`tasks/0518 §151 AMACHINE-85..86`, `REQ-TGT-074`, `REQ-TGT-075`, `REQ-TGT-110`).** Target lowering, peephole optimization, and ABI adaptation on `aarch64-android` MUST preserve exact MIR ownership and deterministic reverse-order `Drop` execution (`DeleteLocalRef`, `DeleteGlobalRef`, `PopLocalFrame`, `DetachCurrentThread`; `REQ-TGT-074`), preserve `view<T>` / `mut_view<T>` / `view<JniEnv>` capability validity and non-escaping lifetime bounds (`REQ-TGT-075`), and preserve pointer provenance and alias disjointness so the optimizer NEVER rewrites a valid capability or foreign-buffer access into an access with wrong provenance or illegal aliasing (`REQ-TGT-110`).

**AXS-ANDR-009 — Execution-Domain Constraints & CPU vs GPU Address-Space Isolation (`tasks/0518 §151 AMACHINE-87..89`, `SPEC-51 AXS-MEM-024`, `REQ-TGT-076`, `REQ-TGT-077`, `REQ-TGT-078`).** `compiler/target/aarch64/android` MUST preserve all execution-domain constraints (`@no_panic`, `--profile freestanding`, `CurrentJNIThread` affinity, critical-array GC-pin windows; `REQ-TGT-076`). Android CPU A64 machine lowering is strictly distinct from Android GPU/compute lowering (Vulkan SPIR-V in `P22`; `REQ-TGT-077`), and `@addr_space(N)` GPU device/shared/constant pointers MUST NEVER be implicitly cast to, aliased with, or lowered as 64-bit Bionic CPU virtual addresses (`AX_TYPE_ADDR_SPACE_MISMATCH`, `REQ-TGT-078`).

---

## 2. 16 KiB Page-Aligned Bionic ELF64 (`ET_DYN` PIE & `.so`), `.note.android.ident`, Linker Namespaces & `std.sys.android`

**AXS-ANDR-010 — Mandatory `ET_DYN` Image Format for Both PIE Executables & Shared Libraries (`0198 §5, §10, §19–20, AANDROID-22, 26..27, 31, 41`).** Android's `/system/bin/linker64` unconditionally rejects non-PIE `ET_EXEC (2)` binaries. `compiler/link/elf_android` therefore emits `ELFCLASS64`, `ELFDATA2LSB`, `EI_OSABI = ELFOSABI_NONE (0)`, `e_type = ET_DYN (3)`, `e_machine = EM_AARCH64 (183)` for every linked image (`CodeModel.PositionIndependent`):
1. **Hosted Executable (`--kind exe`, PIE)**: emits `PT_PHDR`, `PT_INTERP = "/system/bin/linker64\0"` (`21` bytes including NUL), `DT_FLAGS_1 = DF_1_PIE (0x08000000) | DF_1_NOW (0x00000001)`, and PIC `_start` at `e_entry` that captures `raw_args = SP` (`MOV X0, SP`, pointing to `[argc, argv..., NULL, envp..., NULL, auxv...]`) as its first instruction before any `SP` adjustment, clears `X29 = 0` and `X30 = 0`, aligns `SP` to 16 bytes (`AND SP, X0, #-16`), sets `X1 = null` (`onexit`), `X2 = __axiom_slingshot_main`, and `X3 = &structors` pointing to Bionic's 24-byte `@repr(C)` `structors_array_t { preinit_array: *const *const extern "C" fn(), init_array: *const *const extern "C" fn(), fini_array: *const *const extern "C" fn() }`, and invokes Bionic `__libc_init(raw_args, null, __axiom_slingshot_main, &structors)` so Bionic initializes `pthread`, TLS, and `[TPIDR_EL0 + 40]` stack-guard state before entering Axiom `main` (in `--profile freestanding`, `@entry` `_start` invokes `SVC #0` `SYS_exit_group = 94` with zero `libc.so` dependency).
2. **Shared Library (`--kind dll`, `lib<stem>.so`)**: omits `PT_INTERP`, sets `e_entry = 0`, emits `DT_SONAME = "lib<stem>.so"` and `DT_FLAGS_1 = DF_1_NOW (0x00000001)`, and performs **no** hidden C++-style global constructor side effects (`0198 §20, AANDROID-31, 41`). `.init_array` is emitted solely when `SPEC-56` `@at(image(...) + off)` load-time slots require deterministic pointer binding; application/JNI initialization is explicit (`JNI_OnLoad` or `@export` init function).

**AXS-ANDR-011 — Mandatory 16 KiB (`0x4000`) `PT_LOAD` Page Alignment, W^X & Full RELRO (`0198 §5, §10`, `0220 §18`, `SPEC-82 AXS-ELFD-018, AXS-ELFD-022..023`).** To satisfy Android 15+ (API 35+) 16 KiB kernel page-size devices while remaining 100% compatible with 4 KiB devices (API 21–34), `compiler/link/elf_android` enforces:
1. Every `PT_LOAD` segment sets `p_align = 0x4000` (`16384`), satisfies `(p_vaddr - p_offset) % 0x4000 == 0`, and occupies disjoint `0x4000`-aligned virtual address pages across three strict W^X segments:
   - **Segment 0 (`PF_R`)**: `Elf64_Ehdr`, `Elf64_Phdr` table, `.note.android.ident`, `.dynsym`, `.dynstr`, `.gnu.hash` (plus SysV `.hash` when `api_level < 23`), `.gnu.version`, `.gnu.version_r`, `.rela.dyn`, `.rela.plt`, `.rodata`, `.eh_frame_hdr`, `.eh_frame`.
   - **Segment 1 (`PF_R | PF_X`)**: `.plt` (16-byte A64 entries using `X16`/`X17` only), `.text`, `±128 MiB` `X16` range-extension veneers (`SPEC-83 AXS-A64-042`).
   - **Segment 2 (`PF_R | PF_W`)**: `.tdata` (when `PT_TLS` active), `.data.rel.ro` (relocated constant pointer tables such as `dyn Trait` vtables, `structors_array_t`, and static `JNINativeMethod` arrays; `SPEC-82 AXS-ELFD-018, 022`), `.init_array`, `.fini_array`, `.dynamic`, `.got`, and `.got.plt` (when present, eagerly bound at load time under Full RELRO) — padded to a `0x4000` boundary covered by `PT_GNU_RELRO` (`DT_BIND_NOW`, `DF_BIND_NOW`, `DF_1_NOW`), followed by writable `.data` and zero-file-byte `.bss`.
2. `PT_GNU_STACK` is emitted with `PF_R | PF_W` (non-executable stack). Text relocations (`R_AARCH64_ABS64`/`ABS32`/`PREL32` targeting `PF_R` or `PF_R | PF_X` in `ET_DYN` when non-local/dynamic) are rejected with `AX_LINK_TEXTREL_FORBIDDEN` (never emitting `DT_TEXTREL`). Post-encoding `verify_android_elf_image` validates headers, `0x4000` segment alignment, W^X, `.note.android.ident`, and dynamic relocation targets before disk write (`AX_ICE_INTERNAL` with `data.stage = "link_verify"` on internal invariant failure).

**AXS-ANDR-012 — `.note.android.ident` Binary Layout (`0198 §3, §5`).** Every linked `aarch64-android` PIE and `.so` image contains an allocatable `SHT_NOTE (7)` section `.note.android.ident` (`SHF_ALLOC = 0x2`, `sh_addralign = 4`, `152` bytes total) in Segment 0 covered by a `PT_NOTE (4)` program header (`p_align = 4`), matching Android Bionic `crtbrand` / NDK `note_android_ident`:

| Byte Offset | Field | Type | Value |
|---|---|---|---|
| `+0..4` | `namesz` | `u32le` | `8` (`"Android\0"`) |
| `+4..8` | `descsz` | `u32le` | `132` (`4 + 64 + 64`) |
| `+8..12` | `type` | `u32le` | `1` (`NT_ANDROID_TYPE_IDENT`) |
| `+12..20` | `name` | `[8]u8` | `"Android\0"` (`41 6E 64 72 6F 69 64 00`) |
| `+20..24` | `android_api` | `u32le` | `target.api_level` (default `29` = `1D 00 00 00`) |
| `+24..88` | `ndk_version` | `[64]u8` | NUL-padded ASCII `"r27c\0..."` (deterministic ABI tag) |
| `+88..152` | `ndk_build_number` | `[64]u8` | NUL-padded ASCII `"axiomc-hermetic\0..."` |

When reading external Android `.o`/`.so` inputs, `compiler/link/elf_android` accepts both 24-byte (`descsz == 4`) and 152-byte (`descsz == 132`) `.note.android.ident` sections; if an input records `android_api > target.api_level`, linking fails with `AX_TARGET_API_LEVEL_TOO_LOW`.

**AXS-ANDR-013 — NDK-Free Built-In Bionic Stub Catalog & API-Level Verifier (`0198 §4, §23–26, §31, AANDROID-22, 24, 33..35`).** `compiler/link/elf_android` embeds a deterministic symbol stub catalog for the core public Android NDK system libraries — `libc.so` (`LIBC`), `libm.so` (`LIBC`), `libdl.so` (`LIBC`), and `liblog.so` (`LIBLOG`/unversioned) — recording `(soname, symbol, kind, version_tag, api_min)` per export. Consequently, `axiomc build --target aarch64-android` compiles and links valid PIE and `.so` binaries on Windows, Linux, and macOS **without an installed Android NDK, `clang`, `lld`, or external sysroot** (`0198 §4`). An optional `--sysroot <dir>` adds external NDK `.so` stubs (`libandroid.so`, `libvulkan.so`, `libaaudio.so`, `libnativewindow.so`, `libmediandk.so`, `libcamera2ndk.so`). Resolving any symbol whose `api_min > target.api_level` fails deterministically at link time with `AX_TARGET_API_LEVEL_TOO_LOW` (`data.symbol`, `data.required_api`, `data.target_api`; canonical mapping of corpus `0198 §24 AX_ANDROID_0001`).

**AXS-ANDR-014 — Android Linker Namespaces, Public Library Policy & Symbol Visibility (`0198 §10–13, §27–29, AANDROID-26..28, 36..38`).**
1. **Private System Library Rejection**: Android 7.0+ (`linker64` linker namespaces) and Android 12+ (API 31+) block app shared libraries from loading non-NDK private platform libraries (`libart.so`, `libbinder.so`, `libcutils.so`, `libutils.so`, `libgui.so`, `libui.so`, `libhidlbase.so`, system `libcrypto.so`/`libssl.so`). Requesting `-l<name>` or `@link("<name>")` for a non-NDK private platform library fails at link time with `AX_LINK_ANDROID_PRIVATE_LIB` (`data.library`) unless `--allow-private-android-libs` is passed for AOSP/OEM system-partition builds.
2. **Minimal `DT_NEEDED` & `STV_HIDDEN` Default**: `DT_NEEDED` entries are emitted only for shared libraries that satisfy at least one unresolved dynamic reference or explicit `@link` directive (`0198 §13`, never guessed). All internal and non-`@export` `pub` Axiom symbols default to `STV_HIDDEN`; only `@export` items, `@jni_export` adapters, and synthesized `JNI_OnLoad` appear in `.dynsym` with `STV_DEFAULT`. Android ELF linker namespaces never affect Axiom `module` resolution (`0198 §12, AANDROID-28`).

**AXS-ANDR-015 — Bionic TLS (`TPIDR_EL0`) & `.eh_frame` Unwind (`0220 §16`, `SPEC-83 AXS-A64-041, AXS-A64-043, AXS-A64-047`).** Bionic reserves fixed `TPIDR_EL0` pointer slots (`TLS_SLOT_SELF = 0`, `TLS_SLOT_THREAD_ID = 1`, `TLS_SLOT_ERRNO = 2`, `TLS_SLOT_STACK_GUARD = 5` at `[TPIDR_EL0 + 40]`, `TLS_SLOT_BIONIC_TLS = 6`, `TLS_SLOT_DTV = 7`); generated code MUST NOT index fixed `TPIDR_EL0` offsets directly. Furthermore, 64-bit ARM Bionic `libc.so` **does not export `__tls_get_addr`** (emitting an undefined reference to `__tls_get_addr` causes `/system/bin/linker64` to reject the image at load time). Consequently:
1. For `target.api_level >= 29` (default), `@thread_local static` uses native Bionic ELF TLS (`PT_TLS`): `--kind exe` (PIE) uses Initial-Exec (`R_AARCH64_TLSIE_ADR_GOTTPREL_PAGE21 = 541` + `R_AARCH64_TLSIE_LD64_GOTTPREL_LO12_NC = 542`, resolved via an 8-byte `.got` slot relocated by `R_AARCH64_TLS_TPREL = 1030`, or linker-relaxed from `TLSDESC`), whereas `--kind dll` (`.so`) uses **ARM64 `TLSDESC` exclusively** — relocatable `.o` (`ET_REL`) emits `adrp x0, :tlsdesc:sym` (`R_AARCH64_TLSDESC_ADR_PAGE21 = 562`), `ldr x1, [x0, :tlsdesc_lo12:sym]` (`R_AARCH64_TLSDESC_LD64_LO12 = 563`), `add x0, x0, :tlsdesc_lo12:sym` (`R_AARCH64_TLSDESC_ADD_LO12 = 564`), and `blr x1` (`R_AARCH64_TLSDESC_CALL = 569`) yielding the TP-relative byte offset in `X0` added to `MRS Xbase, TPIDR_EL0`, and linked `.so` allocates a 16-byte (`2 * u64`) `.got` descriptor pair `(resolver_fn_ptr, tls_offset)` relocated in `.rela.dyn` by `R_AARCH64_TLSDESC = 1031`.
2. For `target.api_level < 29`, `@thread_local static` in `--kind dll` lowers via `pthread_key_create` / `pthread_getspecific` so pre-Android-10 `dlopen` never rejects `PT_TLS`. DWARF `.eh_frame` + `.eh_frame_hdr` (`PT_GNU_EH_FRAME`) follow `SPEC-83 AXS-A64-047`.

**AXS-ANDR-016 — `std.sys.android` Platform Implementation & `logcat` Integration (`0198 §9, AANDROID-25`, `0220 §1–4, §9, §39 AOS-20..40`, `T670`).** Bionic is an OS platform library below `std.sys.android`, never part of Axiom Core (`AANDROID-25`). `std/sys/android` implements the `SPEC-04 AXS-EXT-110` `__ax_host_*` contract over `libc.so`, `libdl.so`, and `liblog.so`:
1. **Allocator & `errno`**: `malloc`, `calloc`, `realloc`, `free`, `posix_memalign`; thread-local error code via Bionic `extern "C" fn __errno() -> *mut i32` (distinct from glibc `__errno_location`).
2. **Filesystem, Descriptors & Networking**: `openat` (`AT_FDCWD = -100`, Linux ARM64 `O_*` flags: `O_DIRECTORY = 0x4000`, `O_NOFOLLOW = 0x8000`, `O_DIRECT = 0x10000`, `O_LARGEFILE = 0x20000`), `read`, `write`, `pread64`, `pwrite64`, `lseek64`, `close`, `fstat`, `fstatat`, `opendir`/`readdir`/`closedir`, BSD sockets, and `epoll_create1`/`epoll_ctl`/`epoll_pwait`.
3. **Time, Entropy & Shared Memory**: `clock_gettime` (`CLOCK_REALTIME = 0`, `CLOCK_MONOTONIC = 1`, `CLOCK_BOOTTIME = 7`); `arc4random_buf` (API 21+) plus `getrandom` when `api_level >= 28`; anonymous shared memory via `memfd_create` (`api_level >= 30`) or `ASharedMemory_create` (`api_level >= 26`).
4. **Threads, `futex`, `X18`-Safe Fibers, Dynamic Loading & `logcat`**: `pthread_create`/`pthread_join`/`pthread_detach`, `SYS_futex = 98` (`Mutex`/`Condvar`/`Once`/`Parker`), 160-byte stackful fiber context switch saving `[X19..X28, X29, X30, SP, D8..D15]` without touching `X18`, `dlopen`/`dlsym`/`dlclose`/`dlerror`/`android_dlopen_ext`, and `__android_log_write(prio: i32, tag: *const u8, text: *const u8) -> i32` (`ANDROID_LOG_ERROR = 6`, `ANDROID_LOG_FATAL = 7`, tag `"axiom"`) so panics and runtime diagnostics appear in Android `logcat` as well as `stderr`.

---

## 3. Capability-Safe 3-Layer JNI Architecture: Foreign Handle Semantics, Raw ABI & Safe Wrappers

**AXS-JNI-001 — Three-Layer JNI Boundary & FFI Safety Orthogonality (`0198 §14–16`, `0200 §1–2, §44–48, AJNI-20, 49, 52`, `REQ-TGT-282`).** JNI is specified as a 3-layer interop stack over `extern "C"` rather than a Core language feature (`no extern "JNI"`):
1. **Layer 1 (`std.ffi.jni.raw`)**: exact `<jni.h>` C ABI types, constants, and `JNINativeInterface_` / `JNIInvokeInterface_` function-pointer vtables (`unsafe` only).
2. **Layer 2 (`std.ffi.jni`)**: capability-scoped safe wrappers (`JniEnv`, `JavaVM`, `JLocal<T>`, `JGlobal<T>`, `JWeak<T>`, `JClass`, `JMethodId`, `JFieldId`, `JString`, array views, `JException`, `JniError`).
3. **Layer 3 (`@jni_export` in `compiler/hir/jni_attr`)**: compile-time HIR adapter synthesis (`Java_*` exports and `JNI_OnLoad` `RegisterNatives` tables) with zero runtime reflection (`0200 §47–48`).
Adding or extending foreign host targets (JNI on Android/desktop JVM, WASM host imports in `E16.6`) MUST NOT require changing Core FFI safety or capability rules (`REQ-TGT-282`).

**AXS-JNI-002 — Foreign Handle Identity vs Memory Capability & Three Orthogonal Lifetimes (`0198 §17–18, AANDROID-30`, `0200 §3–4, §8–9, AJNI-21, 27..30`, `REQ-TGT-230`, `REQ-TGT-272`, `REQ-TGT-273`).**
1. Every JVM reference (`jobject`, `jclass`, `jstring`, `jthrowable`, `jarray`) is an **opaque foreign handle** in execution domain `JVM` (`ForeignHandle<T>`), never a raw pointer to Java object fields (`JObject != *mut u8`). Raw handle numeric bit-patterns (indirect table slots or tagged indices) are distinct from logical Java object identity — two distinct raw handles (e.g. a `JLocal` and a `JGlobal`) may denote the same Java object (`env.is_same_object(a, b)` via `IsSameObject` is the sole identity predicate; `REQ-TGT-272`) — and handle values NEVER grant an Axiom memory capability (`view<T>` / `mut_view<T>`; `REQ-TGT-273`).
2. Imported JVM resources enforce explicit lifetime/ownership contracts (`REQ-TGT-230`) across three distinct lifetimes: **(a)** the GC-managed Java heap object, **(b)** the JNI reference slot (`Local`, `Global`, `WeakGlobal`), and **(c)** the Axiom RAII wrapper (`JLocal<T>`, `JGlobal<T>`, `JWeak<T>`), whose `Drop` deterministically releases **(b)** (`DeleteLocalRef` / `DeleteGlobalRef` / `DeleteWeakGlobalRef`), never freeing **(a)** directly (`0200 §8–9, AJNI-27..28`).

**AXS-JNI-003 — Layer 1 `std.ffi.jni.raw` C ABI Types, Constants & Vtable Layout (`0200 §2, §20, AJNI-31`, `T671`).** `std.ffi.jni.raw` defines:
1. **Primitives & Constants**: `jboolean = u8` (`JNI_FALSE = 0u8`, `JNI_TRUE = 1u8`), `jbyte = i8`, `jchar = u16`, `jshort = i16`, `jint = i32`, `jlong = i64`, `jfloat = f32`, `jdouble = f64`, `jsize = i32`; status codes `JNI_OK = 0`, `JNI_ERR = -1`, `JNI_EDETACHED = -2`, `JNI_EVERSION = -3`, `JNI_ENOMEM = -4`, `JNI_EEXIST = -5`, `JNI_EINVAL = -6`; versions `JNI_VERSION_1_1 = 0x00010001`, `JNI_VERSION_1_2 = 0x00010002`, `JNI_VERSION_1_4 = 0x00010004`, `JNI_VERSION_1_6 = 0x00010006`; array release modes `JNI_COMMIT = 1`, `JNI_ABORT = 2`.
2. **Opaque Handles & Aggregates**: distinct opaque pointer aliases `jobject`, `jclass`, `jstring`, `jthrowable`, `jweak`, `jarray`, `jbooleanArray`, `jbyteArray`, `jcharArray`, `jshortArray`, `jintArray`, `jlongArray`, `jfloatArray`, `jdoubleArray`, `jobjectArray`, `jmethodID`, `jfieldID`; `@repr(C)` 8-byte `union jvalue { pub z: jboolean, pub b: jbyte, pub c: jchar, pub s: jshort, pub i: jint, pub j: jlong, pub f: jfloat, pub d: jdouble, pub l: jobject }`; and `@repr(C)` `struct JNINativeMethod { pub name: *const u8, pub signature: *const u8, pub fnPtr: *const u8 }`.
3. **Standard JNI 1.6 Vtables**: `JavaVM = *const JNIInvokeInterface_` (`8` `extern "C"` pointer slots: `reserved0..2` at `0..2`, `DestroyJavaVM` `3`, `AttachCurrentThread` `4`, `DetachCurrentThread` `5`, `GetEnv` `6`, `AttachCurrentThreadAsDaemon` `7`) and `JNIEnv = *const JNINativeInterface_` (`233` `extern "C"` pointer slots `0..232` matching `<jni.h>` byte-for-byte: `GetVersion` `4`, `FindClass` `6`, `Throw`/`ThrowNew`/`ExceptionOccurred`/`ExceptionDescribe`/`ExceptionClear`/`FatalError` `13..18`, `PushLocalFrame`/`PopLocalFrame` `19..20`, `NewGlobalRef`/`DeleteGlobalRef`/`DeleteLocalRef`/`IsSameObject`/`NewLocalRef`/`EnsureLocalCapacity` `21..26`, `GetObjectClass`/`IsInstanceOf` `31..32`, `GetMethodID` `33`, `Call*Method{,V,A}` `34..93`, `GetFieldID` `94`, `Get/Set*Field` `95..112`, `GetStaticMethodID` `113`, `CallStatic*Method{,V,A}` `114..143`, `GetStaticFieldID` `144`, `Get/SetStatic*Field` `145..162`, `NewString`/`GetStringLength`/`GetStringChars`/`ReleaseStringChars` `163..166`, `NewStringUTF`/`GetStringUTFLength`/`GetStringUTFChars`/`ReleaseStringUTFChars` `167..170`, `GetArrayLength` `171`, `New/Get/SetObjectArray*` `172..174`, `New<Prim>Array` `175..182`, `Get/Release<Prim>ArrayElements` `183..198`, `Get/Set<Prim>ArrayRegion` `199..214`, `RegisterNatives`/`UnregisterNatives` `215..216`, `MonitorEnter`/`MonitorExit` `217..218`, `GetJavaVM` `219`, `GetStringRegion`/`GetStringUTFRegion` `220..221`, `Get/ReleasePrimitiveArrayCritical` `222..223`, `Get/ReleaseStringCritical` `224..225`, `New/DeleteWeakGlobalRef` `226..227`, `ExceptionCheck` `228`, `NewDirectByteBuffer`/`GetDirectBufferAddress`/`GetDirectBufferCapacity` `229..231`, `GetObjectRefType` `232`). Invoking any `raw` vtable pointer requires `unsafe`.

**AXS-JNI-004 — `JniEnv` Thread-Local Capability (`0200 §10–11, §40–43, AJNI-22, 45`).** `JniEnv` is an opaque `!Copy`, `!Send`, `!Share` capability token representing the calling OS thread's active JVM attachment (`CurrentJNIThread`). Safe user code CANNOT construct, copy, or move `JniEnv` by value; it is received exclusively as `view<JniEnv>` or `mut_view<JniEnv>` from a `@jni_export` entry point, `JavaVM.with_attached_env`, or `with_local_frame`. Attempting to store `view<JniEnv>` / `mut_view<JniEnv>` in a `static` or escaping struct or send/share it across threads is rejected at compile time (`AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `AX_TYPE_STORED_VIEW_ESCAPE`, `AX_FFI_JNI_LOCAL_ESCAPE`).

**AXS-JNI-005 — `JavaVM` & Structured Thread Attachment (`0200 §12–14, §40, AJNI-23, 44`, `REQ-TGT-270`).** `JavaVM` is a process-wide VM handle implementing `Copy`, `Send`, and `Share` (`env.java_vm()` obtains it safely; `unsafe fn from_raw(vm: *mut raw.JavaVM) -> JavaVM` wraps a raw pointer). `JavaVM.with_attached_env<R>(self: view<JavaVM>, f: fn(mut_view<JniEnv>) -> Result<R, JniError>) -> Result<R, JniError>` (and `with_attached_daemon_env`) enforces structured attachment:
1. Calls `GetEnv(&raw_env, JNI_VERSION_1_6)`. If `JNI_OK`, the thread is already attached: `f` runs inside a `with_local_frame` guard **without** calling `DetachCurrentThread` on exit (preserving host ART/JVM thread ownership).
2. If `JNI_EDETACHED`, calls `AttachCurrentThread` (or `AttachCurrentThreadAsDaemon`), runs `f` inside an RAII `AttachGuard`, and deterministically calls `DetachCurrentThread` on normal return, `Err`, or panic unwind (`REQ-TGT-270`). Any other status returns `Result.Err(JniError.EnvUnavailable(status))`.

**AXS-JNI-006 — `JLocal<T>` & `with_local_frame` (`0200 §5, AJNI-24, 27..28, 32`).** `JLocal<T>` is `!Copy`, `!Send`, `!Share`, wrapping `(raw_env: *mut raw.JNIEnv, raw_obj: raw.jobject, owned: bool)` in the current thread's active `JNILocalFrame`. `impl<T> Drop for JLocal<T>` invokes `DeleteLocalRef(raw_env, raw_obj)` iff `owned && raw_obj != null` (caller-owned `@jni_export` parameters have `owned = false`; `into_jni_return(self) -> JniReturn<T>` sets `owned = false` when handing a return reference to the JVM caller; `env.clone_local<T>(self: mut_view<JniEnv>, local: view<JLocal<T>>) -> Result<JLocal<T>, JniError>` duplicates a local slot via `NewLocalRef` with `owned = true`, `ExceptionCheck`, and `JniError.EnvUnavailable(raw.JNI_ENOMEM)` on out-of-memory `null`). `with_local_frame<R>(env: mut_view<JniEnv>, capacity: i32, f: fn(mut_view<JniEnv>) -> Result<R, JniError>) -> Result<R, JniError>` pairs `PushLocalFrame(capacity)` with an RAII guard calling `PopLocalFrame(null)` on every exit; `JLocal<T>` cannot escape `f` (`AX_FFI_JNI_LOCAL_ESCAPE` / `AX_CAP_OUTLIVES_OWNER`), while `JGlobal<T>`, `String`, `Vec<u8>`, and scalars return freely (`with_local_frame_local` promotes one `JLocal<T>` into the outer frame via `PopLocalFrame(raw_obj)`).

**AXS-JNI-007 — `JGlobal<T>` & `JWeak<T>` Cross-Thread References (`0200 §6–7, §41–42, AJNI-25..28, 46`).** `JGlobal<T>` and `JWeak<T>` are `!Copy` and implement `Send + Share`, holding `(vm: JavaVM, raw_ref: raw.jobject)`. Promotion and frame-local reacquisition are explicit and uniform over `Result<..., JniError>`: `env.new_global_ref<T>(self: mut_view<JniEnv>, local: view<JLocal<T>>) -> Result<JGlobal<T>, JniError>` (`NewGlobalRef`, slot `21`), `env.new_weak_ref<T>(self: mut_view<JniEnv>, local: view<JLocal<T>>) -> Result<JWeak<T>, JniError>` (`NewWeakGlobalRef`, slot `226`), and `env.new_local_ref<T>(self: mut_view<JniEnv>, global: view<JGlobal<T>>) -> Result<JLocal<T>, JniError>` (`NewLocalRef`, slot `25`, creating a frame-owned `JLocal<T>` with `owned = true` in the active `JNILocalFrame` after `ExceptionCheck`, or returning `Result.Err(JniError.EnvUnavailable(raw.JNI_ENOMEM))` if `NewLocalRef` returns `null` without a pending exception for a non-null `global`). Their `Drop` implementations obtain `JNIEnv*` from `vm` (attaching and detaching iff the dropping thread is currently detached) and deterministically call `DeleteGlobalRef` / `DeleteWeakGlobalRef`. `JGlobal<T>: Send + Share` permits cross-thread storage, whereas invoking any Java method on `JGlobal<T>` still requires an active `mut_view<JniEnv>` on the calling thread (`0200 §41–42, AJNI-46`). `JWeak<T>.upgrade_local(self: view<JWeak<T>>, env: mut_view<JniEnv>) -> Result<Option<JLocal<T>>, JniError>` atomically calls `NewLocalRef` + `ExceptionCheck` and checks `raw_local == null || IsSameObject(raw_local, null) == JNI_TRUE`, avoiding GC TOCTOU races.

**AXS-JNI-008 — Typed Reference Markers, `JClass`, `JMethodId` / `JFieldId` & Descriptor Validation (`0200 §15–19, AJNI-36..37, 50..51`).** `std.ffi.jni` provides zero-sized type markers `JObject`, `JClass`, `JString`, `JThrowable`, `JBooleanArray`, `JByteArray`, `JCharArray`, `JShortArray`, `JIntArray`, `JLongArray`, `JFloatArray`, `JDoubleArray`, and `JObjectArray<T>`. Upcasting `JLocal<Sub>` to `JLocal<JObject>` is safe; downcasting `env.cast_local<Sub>(obj)` checks `IsInstanceOf` and returns `Result.Err(JniError.TypeMismatch)` on mismatch. `FindClass` requires slash-separated `JniClassName` (`"java/lang/String"`; dot-separated `"java.lang.String"` fails validation with `JniError.InvalidSignature`). `JMethodId`, `JStaticMethodId`, `JFieldId`, and `JStaticFieldId` validate JNI type descriptors (`"(ILjava/lang/String;)[B"`) before calling `Get*ID`. Because `FindClass` on a `pthread`-attached native worker thread uses the system ClassLoader rather than the app ClassLoader, application classes needed off-thread MUST be looked up in `JNI_OnLoad` and cached as `JGlobal<JClass>` (`0200 §15, §40`).

**AXS-JNI-009 — `JString` UTF-8, Modified UTF-8 & UTF-16 Conversion (`0200 §21–23, AJNI-48`).** `JString` is never implicitly coerced to `Str` or `*const u8`. `env.get_string_utf8(self: mut_view<JniEnv>, s: view<JLocal<JString>>) -> Result<String, JniError>`, `env.new_string_utf8(self: mut_view<JniEnv>, s: Str) -> Result<JLocal<JString>, JniError>`, and `env.new_string_from_owned(self: mut_view<JniEnv>, s: view<String>) -> Result<JLocal<JString>, JniError>` perform explicit conversion between Axiom UTF-8 and JVM UTF-16 / Modified UTF-8 (`GetStringLength` + `GetStringRegion`/`NewString` or Modified-UTF-8 transcoding of `0xC0 0x80` embedded NULs and CESU-8 6-byte surrogate pairs `0xED 0xA0..0xAF` + `0xED 0xB0..0xBF` <-> 4-byte UTF-8 supplementary scalar values `U+10000..U+10FFFF`), preserving interior NUL bytes and returning `JniError.InvalidUtf16` on lone surrogates (`get_string_utf8_lossy` substitutes `U+FFFD`).

**AXS-JNI-010 — Primitive & Byte Array Access (`0200 §24–26, AJNI-47`).** `std.ffi.jni` exposes three tiered array APIs:
1. **Region Copy (default, zero GC pinning)**: `env.get_byte_array_region(arr, start, dst: mut_view<[u8]>) -> Result<(), JniError>` and `set_<prim>_array_region` (`Get/Set<Prim>ArrayRegion`), verifying `0 <= start` and `start + len(dst) <= array_len` before the JNI call.
2. **Scoped Element View**: `env.with_byte_array_elements(arr, mode, |elems: mut_view<[u8]>| ...)` (`Get<Prim>ArrayElements` paired with RAII `Release<Prim>ArrayElements`; `elems` cannot escape the closure: `AX_CAP_OUTLIVES_OWNER`).
3. **Restricted Critical Window**: `env.with_primitive_array_critical<P, R>(arr, mode, f: fn(mut_view<[P]>) -> R) -> Result<R, JniError>` (`GetPrimitiveArrayCritical` paired with RAII `ReleasePrimitiveArrayCritical`). Because `f` receives only `mut_view<[P]>` while `env` remains mutably borrowed for the call duration, the type/capability checker statically prevents any nested JNI call on `env` while the JVM GC pin is held (`AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ`).

**AXS-JNI-011 — Mandatory `ExceptionCheck` Bridge & `JException` / `JniError` (`0200 §27–30, §49, AJNI-33, 35`).** Immediately after every JNI vtable operation that may raise a Java exception, `std.ffi.jni` runs `env.check_exception(self: mut_view<JniEnv>) -> Result<(), JException>` over `ExceptionCheck(raw_env)` (slot `228`). When `JNI_TRUE`:
1. Calls `exc = ExceptionOccurred(raw_env)` (slot `15`) and **immediately** calls `ExceptionClear(raw_env)` (slot `17`) before any `DeleteLocalRef`, RAII `Drop`, or subsequent JNI call (satisfying JNI's pending-exception protocol).
2. Promotes `exc` into `JException` (wrapping a `JGlobal<JThrowable>` and releasing the temporary local `exc` via `DeleteLocalRef`), returning `Result.Err(JException)` from `check_exception()` and wrapping it as `Result.Err(JniError.Exception(jexc))` across all fallible Layer-2 `JniEnv` / `JWeak` APIs so `?` (`HIR_EXPR_TRY`) composes uniformly with `with_local_frame`, `JavaVM.with_attached_env`, and `@jni_export` without implicit error conversion (`JException.into_jni_error(self) -> JniError` is explicit). Pending Java exceptions NEVER become native Axiom panics.

---

## 4. Layer 3 `@jni_export` Lowering, `Java_*` Mangling, `JNI_OnLoad` `RegisterNatives` & `MockJvm`

**AXS-JNI-012 — `@jni_export` Attribute Syntax & Signature Validation (`0200 §32–34, §39, AJNI-38..40`, `T671`).** `compiler/hir/jni_attr` lowers `@jni_export(package = "<pkg>", class = "<Cls>", ...)` on a function declaration:
1. **Arguments**: `package` (dot- or slash-separated Java package, `""` for default package) and `class` (Java class name, nested classes written `Outer$Inner`) are required string literals; optional string/bool arguments are `name = "<javaMethod>"` (default: Axiom function name), `overload = false | true` (default: `false`), and `mode = "both" | "onload" | "mangled"` (default: `"both"`).
2. **Signature Legality (`AX_FFI_INVALID_JNI_EXPORT`)**: The target item MUST be a monomorphic (non-generic), non-`async`, non-`gen` `fn` (`0200 §39`; capturing closures are rejected with `AX_FFI_CAPTURING_CLOSURE_CALLBACK`). Parameter `0` MUST be `env: mut_view<JniEnv>` (or `view<JniEnv>`); parameter `1` MUST be `this: JLocal<JObject>` (instance native method) or `cls: JLocal<JClass>` (`static` native method); parameters `2..N` MUST be JNI scalar primitives (`bool`, `i8`, `u16`, `i16`, `i32`, `i64`, `f32`, `f64`) or `JLocal<T>`. The return type MUST be `()`, a JNI scalar primitive, `JniReturn<T>`, or `Result<R, E>` where `R` is `()`, a JNI scalar primitive, or `JniReturn<T>` and `E` is `JException` or `JniError`. Any other item kind, malformed Java identifier, or non-JNI type fails with `AX_FFI_INVALID_JNI_EXPORT`.

**AXS-JNI-013 — `JLocal` No-Escape Rule & Explicit `JniReturn<T>` Handoff (`0200 §5, §32–34, §49`, `T671`).** Returning a bare `JLocal<T>` (or `Result<JLocal<T>, E>`) directly from a `@jni_export` function, `with_local_frame`, or `JavaVM.with_attached_env`, or storing `JLocal<T>` / `view<JniEnv>` into a `static` or escaping aggregate, is rejected at compile time with `AX_FFI_JNI_LOCAL_ESCAPE` (`AX_CAP_OUTLIVES_OWNER` / `AX_TYPE_STORED_VIEW_ESCAPE`). To return a JNI object reference to the calling JVM frame from `@jni_export`, user code MUST explicitly consume the local wrapper via `local.into_jni_return() -> JniReturn<T>` (which marks `owned = false` so `Drop` does not call `DeleteLocalRef` before the JVM caller receives `X0`) or promote it via `env.new_global_ref(view(local))`.

**AXS-JNI-014 — `Java_*` Mangling & Synthesized `JNI_OnLoad` `RegisterNatives` (`0200 §35–38, §51, §57, AJNI-41..43`).**
1. **Standard JNI Symbol Mangling (`mode = "mangled" | "both"`)**: emits an `STV_DEFAULT` symbol `Java_<mangle(pkg)>_<mangle(cls)>_<mangle(name)>` (omitting `<mangle(pkg)>_` when `package == ""`), appending `__<mangle(param_jni_descriptors)>` when `overload = true`. Escape rules per JNI specification: `.` or `/` -> `_`, `_` -> `_1`, `;` -> `_2`, `[` -> `_3`, and `$` or any code unit outside ASCII `[0-9A-Za-z]` -> `_0xxxx` (4 lowercase hex UTF-16 digits).
2. **`JNI_OnLoad` + `RegisterNatives` (`mode = "onload" | "both"`, preferred per `0200 §35–38`)**: When a `--kind dll` crate contains `@jni_export` items with `mode` `"onload"` or `"both"` and defines no manual `@export("JNI_OnLoad")`, `compiler/hir/jni_attr` synthesizes `pub extern "C" fn JNI_OnLoad(vm: *mut raw.JavaVM, reserved: *mut u8) -> raw.jint` (`STV_DEFAULT`). It calls `GetEnv(JNI_VERSION_1_6)`, groups `JNINativeMethod` descriptors `(name, signature, fnPtr)` by slash-separated class path, invokes `FindClass` + `RegisterNatives` + `DeleteLocalRef(cls)` per class, clears any pending exception and returns `JNI_ERR (-1)` cleanly without panicking if `FindClass` or `RegisterNatives` fails (`0200 §57`), and returns `JNI_VERSION_1_6 (0x00010006)` on success.

**AXS-JNI-015 — Generated Adapter Lowering, Exception Re-Throw & No-Unwind Panic Barrier (`0200 §31–34, AJNI-34, 38..40`, `SPEC-54 AXS-PAN-020..022`, `REQ-TGT-270`).** For each `@jni_export` function, `compiler/hir/jni_attr` generates an `extern "C"` wrapper `(raw_env: *mut raw.JNIEnv, raw_recv: raw.jobject, ...raw_args) -> RawRet`:
1. Constructs a stack-pinned `JniEnv` (`mut_view<JniEnv>`) and caller-owned (`owned = false`) `JLocal` wrappers for `raw_recv` and incoming object arguments.
2. Executes the user body inside a boundary panic guard (`std.panic.catch_unwind` under `--panic unwind`, or `logcat` + deterministic abort under `--panic abort`).
3. **Normal `Ok(v)` / value return**: unwraps `JniReturn<T>` to `raw.jobject`, converts `bool` to `0u8`/`1u8`, and returns scalar values directly in `X0`/`V0`.
4. **`Result.Err(e)` return**: clears any stale pending exception, raises `e` in the JVM via `Throw(raw_env, jexc.raw_throwable())` (for `JException` or `JniError.Exception(jexc)`) or `ThrowNew(raw_env, "java/lang/RuntimeException\0", msg_cstr)` (for other `JniError` variants), and returns the zeroed JNI sentinel (`0`, `0.0`, `JNI_FALSE`, `null`).
5. **Caught Axiom panic**: logs the panic to `logcat` on Android, clears any stale pending exception, calls `ThrowNew(raw_env, "java/lang/RuntimeException\0", panic_cstr)` (aborting the process only if `ThrowNew` itself fails to raise an exception), and returns the zeroed JNI sentinel — **never** unwinding an Axiom frame into foreign JVM/ART stack frames (`AJNI-34`, `SPEC-54 AXS-PAN-020..022`, `REQ-TGT-270`).

**AXS-JNI-016 — Deterministic In-Process `MockJvm` Harness (`std.ffi.jni.testing`, `T671`, `T672`).** To test JNI ownership, frame management, thread attachment, UTF-8/Modified-UTF-8 conversion, and `@jni_export` adapters deterministically under `--interp` and host native builds on Windows, Linux, and macOS without an Android emulator, `std.ffi.jni.testing` provides an arena-backed `MockJvm` implementing the complete `JNIInvokeInterface_` (`8`-slot) and `JNINativeInterface_` (`233`-slot) vtables:
1. Handle slots use non-dereferenceable tagged integers (`0x5A00_0000_0000_0000 | (kind << 32) | slot_id`) rather than host pointers, immediately trapping any illegal raw-pointer dereference and directly validating `IsSameObject` across distinct `Local`/`Global`/`Weak` slot IDs (`REQ-TGT-272`, `REQ-TGT-273`).
2. `MockJvm` records exact deterministic counters (`local_created`, `local_deleted`, `live_locals`, `global_created`, `global_deleted`, `live_globals`, `weak_created`, `weak_deleted`, `frames_pushed`, `frames_popped`, `threads_attached`, `threads_detached`, `exception_checks`, `exceptions_cleared`, `registered_natives`) and enforces JNI pending-exception discipline (trapping if a non-exempt vtable slot is called before `ExceptionClear`).

---

## 5. Diagnostics, Canonical Examples & E16.5 Traceability

**AXS-JNI-017 — Diagnostics & Corpus Error Taxonomy Mapping (`spec/diagnostics.md` §3, §11; `0198 §24`; `0200 §49`).** Per `ADR-0011` (`AXD-010`, `AXD-021`), serial-numbered corpus codes in `0198 §24` (`AX_ANDROID_0001`) and `0200 §49` (`AX_JNI_0001..0010`) map to descriptive `AX_<AREA>_<NAME>` diagnostics for compile/link-time errors and typed `JniError` enum variants for runtime JVM outcomes:

| Code | Area | Sev | Delivering Task | Condition on `aarch64-android` / `std.ffi.jni` |
|---|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | `T016`/`T654`/`T670` | Unrecognized `--target <triple>` (`AXS-ANDR-001`) |
| `AX_DRIVER_INVALID_ANDROID_API` | `DRIVER` | `error` | `T670` | `--android-api <N>` or `aarch64-linux-android<N>` specifies `N < 21`, non-integer, or conflicting API levels (`AXS-ANDR-001`; exit code `2`) |
| `AX_TARGET_API_LEVEL_TOO_LOW` | `TARGET` | `error` | `T670` | Symbol or input `.note.android.ident` requires Android API level `M > target.api_level` (`data.symbol`, `data.required_api`, `data.target_api`; `AXS-ANDR-012..013`, maps `0198 §24 AX_ANDROID_0001`) |
| `AX_LINK_ANDROID_PRIVATE_LIB` | `LINK` | `error` | `T670` | Linking against a non-NDK private Android platform `.so` (`libart.so`, `libbinder.so`, `libcutils.so`, `libgui.so`, …) without `--allow-private-android-libs` (`data.library`; `AXS-ANDR-014`) |
| `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | `error` | `T655`/`T662`/`T670` | Machine IR touches reserved `X18`/`W18` ShadowCallStack register or violates A64 `verify_mc` (`AXS-ANDR-005`) |
| `AX_TYPE_ADDR_SPACE_MISMATCH` | `TYPE` | `error` | `T507`/`T670` | Implicit conversion between `@addr_space(N)` GPU pointers and CPU Bionic virtual addresses (`AXS-ANDR-009`, `REQ-TGT-078`) |
| `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | `error` | `T658`/`T663`/`T670` | Non-PIC relocation targets a `PF_R` or `PF_R \| PF_X` segment in `ET_DYN` PIE or `.so` (`AXS-ANDR-011`) |
| `AX_LINK_LIBRARY_NOT_FOUND` | `LINK` | `error` | `T750`/`T659`/`T670` | Requested `-l<name>` / `@link("<name>")` not found in `-L` paths, `--sysroot`, or built-in Bionic stub catalog (`AXS-ANDR-013`) |
| `AX_LINK_DUPLICATE_EXPORT` | `LINK` | `error` | `T751`/`T670`/`T671` | Two `@export` or `@jni_export` items resolve to the identical exported `.dynsym` symbol (`AXS-ANDR-014`, `AXS-JNI-014`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `T766`/`T670` | Input `.o`/`.a`/`.so`/`.axmi` conflicts with `TargetId.AArch64Android` or `EM_AARCH64` (`AXS-ANDR-001`) |
| `AX_FFI_UNKNOWN_ABI` | `FFI` | `error` | `T503`/`T670`/`T671` | Forbidden `extern "android"` or `extern "JNI"` ABI string (`AXS-ANDR-004`, `AXS-JNI-001`) |
| `AX_FFI_CAPTURING_CLOSURE_CALLBACK` | `FFI` | `error` | `T503`/`T671` | Capturing closure passed as `JNINativeMethod` callback (`AXS-JNI-012`, maps `0200 §39, AX_JNI_0010`) |
| `AX_FFI_INVALID_JNI_EXPORT` | `FFI` | `error` | `T671` | `@jni_export` on generic/`async`/`gen`/non-`fn`, invalid Java `package`/`class`/`name`, or non-JNI parameter/return signature (`AXS-JNI-012`, maps `0200 §49 AX_JNI_0005..0006`) |
| `AX_FFI_JNI_LOCAL_ESCAPE` | `FFI` | `error` | `T671` | Returning bare `JLocal<T>` without `into_jni_return()`, escaping `JLocal<T>` / `view<JniEnv>` out of `with_local_frame` / `with_attached_env`, or storing `JLocal<T>` / `view<JniEnv>` in a `static` or long-lived struct (`AXS-JNI-004, 006, 013`, maps `0200 §49 AX_JNI_0002..0003`) |
| `AX_CONC_NOT_SEND` / `AX_CONC_NOT_SHARE` | `CONC` | `error` | `T089`/`T401`/`T671` | Sending or sharing `JniEnv` or `JLocal<T>` across threads (`AXS-JNI-004, 006`, maps `0200 §49 AX_JNI_0003, 0007, 0010`) |
| `AX_TYPE_STORED_VIEW_ESCAPE` | `TYPE` | `error` | `T048`/`T125`/`T671` | Storing or returning an escaping `view<JniEnv>` / `mut_view<JniEnv>` or view-containing aggregate beyond its owner (`AXS-JNI-004, 013`, maps `0200 §49 AX_JNI_0002..0003`) |
| `AX_CAP_OUTLIVES_OWNER` / `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ` | `CAP` | `error` | `T048`/`T125`/`T501`/`T671` | Escaping array element view or reading/mutating `JniEnv` inside `with_primitive_array_critical` while the GC pin borrow is live (`AXS-JNI-010`, maps `0200 §49 AX_JNI_0009`) |
| `AX_UNSAFE_REQUIRED` | `UNSAFE` | `error` | `T061a`/`T671` | Calling `std.ffi.jni.raw` vtable functions outside `unsafe` (`AXS-JNI-003`) |
| `AX_ICE_INTERNAL` (`stage = "link_verify"`) | `ICE` | `error` | `T670` | Synthesized Android ELF64 image failed `verify_android_elf_image` (`AXS-ANDR-011`) |

Runtime `JniError` variants cover dynamic JVM states from `0200 §49`: `EnvUnavailable(i32)` (`AX_JNI_0001`), `ThreadDetached` (`AX_JNI_0007`), `Exception(JException)` (`AX_JNI_0004`), `InvalidSignature` (`AX_JNI_0005`), `RegistrationFailed(i32)` (`AX_JNI_0006`), `TypeMismatch` (`AX_JNI_0008`), `InvalidUtf16`, and `OutOfBounds`.

**AXS-JNI-018 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Capability-safe @jni_export shared library (lib/arm64-v8a/libhello_jni.so)
// demonstrating JString UTF-8 ("Xin chào thế giới"), with_local_frame, JGlobal promotion,
// and explicit into_jni_return() handoff.
// Compiled with: axiomc build --target aarch64-android --android-api 29 --kind dll hello_jni.ax -o libhello_jni.so
module demo.android_hello_jni

use std.ffi.jni.{JniEnv, JLocal, JGlobal, JniReturn, JObject, JString, JniError, with_local_frame}

@jni_export(package = "com.example.axiom", class = "Bridge", name = "greet")
pub fn greet(
    env: mut_view<JniEnv>,
    _this: JLocal<JObject>,
    who: JLocal<JString>
) -> Result<JniReturn<JString>, JniError> {
    let caller_name = env.get_string_utf8(view(who))?
    let cached_greeting: JGlobal<JString> = with_local_frame(env, 16, |frame_env: mut_view<JniEnv>| {
        let local_str = if caller_name.is_empty() {
            frame_env.new_string_utf8("Xin chào thế giới")?
        } else {
            let base = frame_env.new_string_utf8("Xin chào thế giới, ")?
            let mut msg = frame_env.get_string_utf8(view(base))?
            msg.push_str(view(caller_name))
            frame_env.new_string_from_owned(view(msg))?
        }
        let promoted = frame_env.new_global_ref(view(local_str))?
        return Result.Ok(promoted)
    })?
    let out_local = env.new_local_ref(view(cached_greeting))?
    return Result.Ok(out_local.into_jni_return())
}
```

```axiom
// Example 2: Structured worker-thread JVM attachment (JavaVM.with_attached_env),
// zero-pin byte-array region copy, and Android logcat integration on aarch64-android.
module demo.android_worker_jni

use std.ffi.jni.{JavaVM, JniEnv, JGlobal, JByteArray, JniError}

extern "C" {
    fn __android_log_write(prio: i32, tag: *const u8, text: *const u8) -> i32
}

fn log_android_info(tag_cstr: view<[u8]>, msg_cstr: view<[u8]>) -> i32 {
    return unsafe { __android_log_write(4, tag_cstr.as_ptr(), msg_cstr.as_ptr()) }
}

pub fn sum_java_bytes_on_worker(vm: JavaVM, payload: JGlobal<JByteArray>) -> Result<i32, JniError> {
    return vm.with_attached_env(|env: mut_view<JniEnv>| {
        let local_arr = env.new_local_ref(view(payload))?
        let mut buf: [4]u8 = [0u8, 0u8, 0u8, 0u8]
        env.get_byte_array_region(view(local_arr), 0, mut_view(buf))?
        let total = (buf[0] as i32) + (buf[1] as i32) + (buf[2] as i32) + (buf[3] as i32)
        let tag: [6]u8 = [97u8, 120u8, 105u8, 111u8, 109u8, 0u8] // "axiom\0"
        let msg: [3]u8 = [111u8, 107u8, 0u8] // "ok\0"
        let _rc = log_android_info(view(tag), view(msg))
        return Result.Ok(total)
    })
}
```

**AXS-JNI-019 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Sending a thread-bound JLocal<JString> across std.thread.spawn is rejected (AX_CONC_NOT_SEND).
module demo.android_bad_send_jlocal

use std.ffi.jni.{JniEnv, JLocal, JString}
use std.thread

pub fn bad_spawn_local(_env: mut_view<JniEnv>, s: JLocal<JString>) {
    let _h = thread.spawn(|| { //~ ERROR AX_CONC_NOT_SEND
        let _moved = s
    })
}
```

```axiom
// Example 2: Returning a bare JLocal<JString> from @jni_export without into_jni_return()
// (or escaping with_local_frame) is rejected (AX_FFI_JNI_LOCAL_ESCAPE).
module demo.android_bad_local_escape

use std.ffi.jni.{JniEnv, JLocal, JObject, JString}

@jni_export(package = "com.example.axiom", class = "Bridge")
pub fn leak_local(env: mut_view<JniEnv>, _this: JLocal<JObject>) -> JLocal<JString> { //~ ERROR AX_FFI_JNI_LOCAL_ESCAPE
    let res = env.new_string_utf8("leak").unwrap()
    return res
}
```

```axiom
// Example 3: Calling an API-30 Bionic symbol (memfd_create) under --target aarch64-android --android-api 26
// or linking non-NDK private libbinder.so without --allow-private-android-libs is rejected.
module demo.android_bad_api_and_private_lib

@link("binder") //~ ERROR AX_LINK_ANDROID_PRIVATE_LIB
extern "C" {
    fn memfd_create(name: *const u8, flags: u32) -> i32 //~ ERROR AX_TARGET_API_LEVEL_TOO_LOW
}

pub fn probe(name: *const u8) -> i32 {
    return unsafe { memfd_create(name, 0u32) }
}
```

**AXS-JNI-020 — Requirement, Invariant & Task Traceability Matrix (`E16.5`: `REQ-TGT-069`..`078`, `REQ-TGT-110`, `REQ-TGT-230`, `REQ-TGT-270`, `REQ-TGT-272`..`273`, `REQ-TGT-282`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T669` | `SPEC-85`: Canonical `aarch64-android` `TargetDesc`, 16 KiB Bionic ELF64 PIE/`.so` linker, `std.sys.android` & 3-layer capability-safe JNI (`std.ffi.jni`, `@jni_export`) specification | `INV-ANDR-001`, `INV-JNI-001`, `INV-JNI-002` | `REQ-TGT-069`..`REQ-TGT-072` | `spec/SPEC-85-android-aarch64-jni.md` |
| `T670` | `compiler/target/aarch64/android`, `compiler/link/elf_android` & `std/sys/android`: `api_level` (`29` default), `X18` SCS reservation, 16 KiB `ET_DYN` PIE (`/system/bin/linker64`) & `.so` (`DT_SONAME`), `.note.android.ident`, NDK-free Bionic stubs, API/private-lib verifier, `__ax_host_*` & `__android_log_write` | `INV-ANDR-001` | `REQ-TGT-073`, `REQ-TGT-076`..`REQ-TGT-078` | `tests/obj/android`, `tests/selfhost/link` |
| `T671` | `std/ffi/jni` & `compiler/hir/jni_attr`: `std.ffi.jni.raw` vtables, `JniEnv`/`JavaVM`/`JLocal`/`JGlobal`/`JWeak`, `with_local_frame`, `with_attached_env`, `JString`, array views, `ExceptionCheck` -> `JException` / `Result<T, JniError>`, `@jni_export` (`Java_*` + `JNI_OnLoad`), panic barrier & `MockJvm` | `INV-JNI-001` | `REQ-TGT-074`, `REQ-TGT-075`, `REQ-TGT-110`, `REQ-TGT-230` | `tests/run/jni`, `tests/selfhost/hir` |
| `T672` | `tests/conformance/p16/e16_5_android_aarch64_jni`: E16.5 Android ELF64 PIE/`.so` binary layout, `X18` preservation, `MockJvm` reference/frame/attach lifetime counts, Java<->Axiom exception/panic bridge & compile-time escape rejection conformance suite | `INV-JNI-002` | `REQ-TGT-270`, `REQ-TGT-272`, `REQ-TGT-273`, `REQ-TGT-282` | `tests/conformance/p16/e16_5_android_aarch64_jni` |

Detailed requirement mapping across `REQ-TGT-*`, `0198 AANDROID-20..44`, `0200 AJNI-20..52`, `0220 AOS-20..40`, and `tasks/0453 ATARGET-20..50`:

| Requirement(s) | Corpus Anchor | Canonical `SPEC-85` Rule(s) | Board Task(s) |
|---|---|---|---|
| `REQ-TGT-069`, `REQ-TGT-070` | `tasks/0518 §151 AMACHINE-80..81` (source-pointer syntax independence; internal pointer lowering hidden from safe Core) | `AXS-ANDR-006`, `AXS-JNI-002`, `AXS-JNI-003` | `T669`, `T670`, `T671` |
| `REQ-TGT-071`, `REQ-TGT-072`, `REQ-TGT-073` | `tasks/0518 §151 AMACHINE-82..84` (physical temporaries, physical bit-copies != `Copy`, semantic `Move` without physical copy) | `AXS-ANDR-007`, `AXS-JNI-006`, `AXS-JNI-007` | `T669`, `T670` |
| `REQ-TGT-074`, `REQ-TGT-075`, `REQ-TGT-110` | `tasks/0518 §151 AMACHINE-85..86` & memory codegen provenance (`Drop`, capability validity, and pointer provenance/alias preservation) | `AXS-ANDR-008`, `AXS-JNI-004`..`007`, `AXS-JNI-010`, `AXS-JNI-013` | `T671` |
| `REQ-TGT-076`, `REQ-TGT-077`, `REQ-TGT-078` | `tasks/0518 §151 AMACHINE-87..89` (execution-domain preservation; CPU vs GPU lowering & `@addr_space` isolation) | `AXS-ANDR-005`, `AXS-ANDR-009`, `AXS-JNI-004`, `AXS-JNI-010` | `T670` |
| `REQ-TGT-230` | `tasks/0523 §155 AWASM-41`; `0198 §17–18`; `0200 §4–9 AJNI-24..30` (explicit lifetime/ownership contracts on imported foreign resources) | `AXS-JNI-002`, `AXS-JNI-006`, `AXS-JNI-007`, `AXS-JNI-013` | `T671` |
| `REQ-TGT-270` | `tasks/0523 §155 AWASM-81`; `0200 §12–13, §27–34, §40 AJNI-33..35, 44` (host callbacks preserve resource, attachment, and exception/panic contracts) | `AXS-JNI-005`, `AXS-JNI-011`, `AXS-JNI-015` | `T671`, `T672` |
| `REQ-TGT-272`, `REQ-TGT-273` | `tasks/0523 §155 AWASM-83..84`; `0200 §3–4 AJNI-21, 49` (handle logical identity != numeric address; handles != memory capabilities) | `AXS-JNI-002`, `AXS-JNI-008`, `AXS-JNI-016` | `T671`, `T672` |
| `REQ-TGT-282` | `tasks/0523 §155 AWASM-93`; `0198 §14`; `0200 §1–2 AJNI-20, 52` (target/host features do not alter Core FFI safety semantics) | `AXS-ANDR-004`, `AXS-JNI-001` | `T669`, `T672` |
| — (Corpus `0198`, `0200`, `0220`, `0453`) | `0198 §1–41 AANDROID-20..44`; `0200 §1–61 AJNI-20..52`; `0220 §9, §39 AOS-20..40`; `tasks/0453 §194.1–44 ATARGET-20..50` | `AXS-ANDR-001`..`016`, `AXS-JNI-001`..`020` | `T669`..`T672` |

## Sources

`0193` §1–40 (`AARCH64-20..40`); `0197` §1–42 (`AELF-20..45`); `0198` §1–41 (`AANDROID-20..44`); `0200` §1–61 (`AJNI-20..52`); `0217` §1–72 (`ALINK-20..56`); `0220` §1–4, §9, §16, §18, §28–39 (`AOS-20..40`); `tasks/0453` §194.1–44 (`ATARGET-20..50`); `tasks/0518` §1–151 (`AMACHINE-80..89`, memory codegen provenance); `tasks/0521` §1–158 (`AARM-20..70`); `tasks/0523` §155 (`AWASM-41, 81, 83..84, 93`); `tasks/0563` §304.1–45 (`AIMG-20..60`); `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-110`); `spec/SPEC-22-incremental-compilation.md`; `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-26-windows-artifact-kinds.md`; `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-34-executors-fibers.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-56-module-relative-bindings.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-82-linux-elf-dynamic.md`; `spec/SPEC-83-aarch64-linux.md`; `spec/invariants.md` (`INV-ANDR-001`, `INV-JNI-001..002`); `spec/diagnostics.md`; `ADR-0001`; `ADR-0002`; `ADR-0003`; `ADR-0007`; `ADR-0011`.
