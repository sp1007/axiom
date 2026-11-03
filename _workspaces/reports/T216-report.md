# T216 — Plan phase P16: Targets & platforms

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P16 (`P16-targets-platforms`)** theo `spec/ROADMAP.md` §3–§4 và `.claude/agents/axiom-architect.md`. Đã mở rộng đầy đủ 12 epic của P16 (`E16.9` và `E16.1`–`E16.8`, `E16.10`–`E16.12`) thành **48 task cụ thể** (`T066` đã tinh chỉnh + 47 task mới `T650`–`T696`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-80`..`SPEC-91`, 2 task cài đặt của `axiom-backend`/`axiom-stdlib`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`), nối toàn bộ phụ thuộc với cổng P13 (`T313`) và cổng P16 (`T316`), đồng thời chuyển đổi toàn bộ **327 dòng `EPIC(E16.*)`** (`REQ-TOOL-001` và `REQ-TGT-001`..`REQ-TGT-326`) trong `spec/requirements/CATALOG.md` sang mã task cụ thể.

## Summary

Expanded Phase **P16 (`P16-targets-platforms`)** from the 12 epics in `spec/ROADMAP.md` §3 (`E16.9` first per R6/R7, followed by `E16.1`–`E16.8` and `E16.10`–`E16.12`) into **48 concrete tasks** (`T066` refined in place + 47 new tasks `T650`–`T696`, 4 tasks per epic):

1. **E16.9 — Linux x86-64 static (`T650`, `T066`, `T651`, `T652`; first P16 tasks)**:
   - `T650` (`axiom-architect`): `spec/SPEC-80-linux-x86-64-elf-static.md` — SysV AMD64 ABI (`rdi, rsi, rdx, rcx, r8, r9`, `xmm0`–`xmm7`, 128-byte red zone, 8-byte stack slots), ELF64 relocatable (`.o`) and static executable (`ET_EXEC`, `PT_LOAD`, `PT_GNU_STACK`, `PT_TLS`), and raw Linux x86-64 `syscall` numbers.
   - `T066` (`axiom-backend`): SysV AMD64 ABI pass, ELF64 `.o` writer (`R_X86_64_64`, `PC32`, `PLT32`, `32S`, `TPOFF32`), and static ELF64 linker (`compiler/link/elf64_static.ax`).
   - `T651` (`axiom-stdlib`): `std.sys.linux` raw x86-64 syscalls (`read`, `write`, `openat`, `close`, `mmap`, `futex`, `clock_gettime`, `getrandom`, `exit_group`), `_start` entry (`compiler/runtime/linux_x64_start.ax`), and WSL/Linux runner integration in `tools/axtest_linux.py`.
   - `T652` (`axiom-qa`): Linux x86-64 static ELF64 conformance suite (`tests/conformance/p16/e16_9_linux_x64_static`).

2. **E16.1 — Target description as data (`T653`–`T656`)**:
   - `T653` (`axiom-architect`): `spec/SPEC-81-target-desc-isa-conformance.md` — declarative `TargetDesc`, `RegFileDesc`, `CallingConvDesc`, `IsaEncodingTable`, `RelocKindDesc`, and backend conformance contract.
   - `T654` (`axiom-backend`): `TargetDesc` registry, register file & declarative ABI classification engine (`compiler/target/desc`, `compiler/abi/table_eval`), refactoring x86-64 Windows PE & Linux ELF onto table-driven descriptors.
   - `T655` (`axiom-backend`): Declarative ISA legalizer, pattern matcher & machine-IR verifier (`compiler/lir/legalize`, `compiler/lir/verify_target`).
   - `T656` (`axiom-qa`): TargetDesc & backend conformance suite (`tests/conformance/p16/e16_1_target_desc`).

3. **E16.2 — Linux ELF dynamic (`T657`–`T660`)**:
   - `T657` (`axiom-architect`): `spec/SPEC-82-linux-elf-dynamic.md` — ELF64 PIE (`ET_DYN`), `.so` shared libraries, GOT/PLT, `.dynamic`, `.dynsym`, `.gnu.hash`, `R_X86_64_GOTPCRELX`/`REX_GOTPCRELX`, TLS GD/LD/IE/LE models, and `libc`/`dlopen` interop.
   - `T658` (`axiom-backend`): x86-64 PIC/PIE codegen, GOT/PLT relocations & ELF64 dynamic sections (`compiler/obj/elf64_dyn`, `compiler/target/x64/pic`).
   - `T659` (`axiom-backend`): ELF64 dynamic linker (`ET_DYN` PIE + `.so`), `PT_INTERP`, `DT_NEEDED`/`DT_RPATH`/`DT_RUNPATH` & `std.ffi.dl` (`dlopen`/`dlsym`/`dlclose`).
   - `T660` (`axiom-qa`): Linux ELF dynamic PIE, `.so` & `libc` interop conformance suite (`tests/conformance/p16/e16_2_linux_elf_dynamic`).

4. **E16.3 — AArch64 Linux (`T661`–`T664`)**:
   - `T661` (`axiom-architect`): `spec/SPEC-83-aarch64-linux.md` — AArch64 A64 ISA, AAPCS64 (`x0`–`x7`, `x8` indirect result, `v0`–`v7` HFA/HVA, `x18` platform register, `x29`/`x30` FP/LR, 16-byte `sp` alignment), ELF64 `EM_AARCH64` relocations (`R_AARCH64_CALL26`, `ADR_PREL_PG_HI21`, `ADD_ABS_LO12_NC`, `ADR_GOT_PAGE`, `LD64_GOT_LO12_NC`), and `svc #0` syscalls.
   - `T662` (`axiom-backend`): AArch64 TargetDesc, AAPCS64 ABI pass, 16-byte SP frame lowering & A64/NEON instruction selection (`compiler/target/aarch64/desc`, `compiler/target/aarch64/isel`, `compiler/abi/aapcs64`).
   - `T663` (`axiom-backend`): AArch64 32-bit binary encoder, `EM_AARCH64` ELF64 object/linker & `std.sys.linux.aarch64` (`svc #0` + `TPIDR_EL0` TLS).
   - `T664` (`axiom-qa`): AArch64 Linux static/dynamic & NEON conformance suite (`tests/conformance/p16/e16_3_aarch64_linux`).

5. **E16.4 — macOS AArch64 + Mach-O (`T665`–`T668`)**:
   - `T665` (`axiom-architect`): `spec/SPEC-84-macos-aarch64-macho.md` — Apple ARM64 ABI deltas (packed stack arguments, variadic stack marshaling, `x18` reserved), 16 KiB page alignment, Mach-O 64-bit (`MH_OBJECT`, `MH_EXECUTE`, `MH_DYLIB`), `ARM64_RELOC_*`, chained fixups (`LC_DYLD_CHAINED_FIXUPS`), export trie (`LC_DYLD_EXPORTS_TRIE`), and ad-hoc `LC_CODE_SIGNATURE` (SHA-256 CodeDirectory).
   - `T666` (`axiom-backend`): Apple ARM64 ABI pass & Mach-O 64-bit relocatable object writer (`compiler/abi/apple_arm64`, `compiler/obj/macho64`).
   - `T667` (`axiom-backend`): Mach-O 64-bit linker (`MH_EXECUTE` & `.dylib`), chained fixups, ad-hoc SHA-256 code signing (`compiler/link/macho64`, `compiler/link/codesign_adhoc`) & `std.sys.macos` (`libSystem.B.dylib` FFI).
   - `T668` (`axiom-qa`): macOS AArch64 & Mach-O 64-bit conformance suite (`tests/conformance/p16/e16_4_macos_aarch64`).

6. **E16.5 — Android AArch64 (+JNI layer) (`T669`–`T672`)**:
   - `T669` (`axiom-architect`): `spec/SPEC-85-android-aarch64-jni.md` — `aarch64-linux-android` Bionic ELF64 rules (`PT_INTERP = "/system/bin/linker64"`, mandatory PIE, 16 KiB `p_align = 0x4000` for Android 15+ compatibility, `DT_RUNPATH`), `std.ffi.jni` (`JavaVM`, `JNIEnv`, local/global refs, exception translation), and `@jni_export`.
   - `T670` (`axiom-backend`): `aarch64-linux-android` TargetDesc, 16 KiB-aligned Bionic ELF64 PIE/`.so` linker & `std.sys.android` (`__android_log_write`, `getauxval`, Bionic TLS).
   - `T671` (`axiom-stdlib`): `std.ffi.jni` safe wrapper library (`LocalFrame`, `GlobalRef<T>`, `JString` modified UTF-8 conversion, exception guard) and `@jni_export` mangling/glue pass (`compiler/hir/jni_export`).
   - `T672` (`axiom-qa`): Android AArch64 Bionic ELF & JNI conformance suite (`tests/conformance/p16/e16_5_android_jni`).

7. **E16.6 — WASM32 (`T673`–`T676`)**:
   - `T673` (`axiom-architect`): `spec/SPEC-86-wasm32-backend.md` — `wasm32-unknown-unknown` and `wasm32-wasi`, CFG structuring (`block`/`loop`/`if`/`br`/`br_table`), expression tree stackification, shadow stack (`__stack_pointer`), Wasm C Basic ABI, `.wasm` binary module format (`\0asm\x01\0\0\0`, LEB128 sections `1`–`12`), and WASI Preview 1 imports.
   - `T674` (`axiom-backend`): WASM32 TargetDesc, basic-C ABI pass, CFG loop/block structurer & expression stackifier (`compiler/target/wasm32/desc`, `compiler/target/wasm32/stackify`, `compiler/abi/wasm32`).
   - `T675` (`axiom-backend`): `.wasm` binary module writer, operand-stack bytecode validator, static wasm object linker (`compiler/obj/wasm32`, `compiler/link/wasm32`) & `std.sys.wasi`.
   - `T676` (`axiom-qa`): WASM32 & WASI conformance suite (`tests/conformance/p16/e16_6_wasm32`).

8. **E16.7 — RISC-V64 (`T677`–`T680`)**:
   - `T677` (`axiom-architect`): `spec/SPEC-87-riscv64-linux.md` — `riscv64gc-unknown-linux-gnu` (`RV64IMAFDC`), LP64D ABI (`a0`–`a7`, `fa0`–`fa7`, `ra`, `sp`, `gp`, `tp`, `s0`/`fp`), flagless compare-and-branch instruction selection (`beq`/`bne`/`blt`/`bge`/`bltu`/`bgeu`), `LR.W`/`SC.W`/`AMO*` atomics, and ELF64 `EM_RISCV` relocations (`R_RISCV_CALL_PLT`, `PCREL_HI20`, `PCREL_LO12_I`/`S`).
   - `T678` (`axiom-backend`): RISC-V64 (`RV64GC`) TargetDesc, LP64D ABI pass, flagless branch/atomic instruction selection (`compiler/target/riscv64/desc`, `compiler/target/riscv64/isel`, `compiler/abi/lp64d`).
   - `T679` (`axiom-backend`): RV64GC 32-bit/16-bit RVC instruction encoder, `EM_RISCV` ELF64 `.o`/linker & `std.sys.linux.riscv64` (`ecall` + `tp` TLS).
   - `T680` (`axiom-qa`): RISC-V64 (`RV64GC` / LP64D) Linux conformance suite (`tests/conformance/p16/e16_7_riscv64_linux`).

9. **E16.8 — Cross-compilation & target matrix, OS platform layer (`T681`–`T684`)**:
   - `T681` (`axiom-architect`): `spec/SPEC-88-cross-compilation-platform-layer.md` — any-host-to-any-target compilation without third-party C toolchains (`REQ-TOOL-001`), `@cfg(...)` boolean predicate evaluation (`target_os`, `target_arch`, `target_abi`, `target_endian`, `target_pointer_width`, `profile`, `all`/`any`/`not`), host-vs-target comptime isolation, hermetic sysroot/stub resolution, and 3-level OS platform hierarchy (`std.*`, `std.os.<platform>`, `std.sys.<platform>`).
   - `T682` (`axiom-backend`): `@cfg(...)` predicate evaluator, HIR conditional pruning, target-aware comptime sizing & driver `--target`/`--sysroot` pipeline (`compiler/hir/cfg_eval`, `compiler/driver/cross_target`).
   - `T683` (`axiom-stdlib`): Hermetic target sysroot descriptor & minimal import-stub generator (`compiler/link/sysroot_stubs`) plus 3-level `std.os.<platform>` (`windows`, `linux`, `macos`, `android`, `wasi`) capability modules.
   - `T684` (`axiom-qa`): Cross-compilation, `@cfg` matrix & OS platform layer conformance suite (`tests/conformance/p16/e16_8_cross_compile`).

10. **E16.10 — Artifact kinds & library matrix (`T685`–`T688`)**:
    - `T685` (`axiom-architect`): `spec/SPEC-89-artifact-library-matrix.md` — cross-target artifact kinds (`exe`, `staticlib`, `cdylib`, `axlib`, `obj`, `wasm-module`) and library production/consumption matrix across PE/COFF, ELF64, Mach-O, and WASM32.
    - `T686` (`axiom-backend`): Cross-target static archive producer & iterative resolver (`compiler/obj/archive_matrix`, `compiler/link/archive_resolve`) supporting GNU/SysV `.a`, BSD/Darwin `__.SYMDEF SORTED` `.a`, COFF `.lib`, and `.axlib` (`.axrmeta`).
    - `T687` (`axiom-backend`): Cross-target dynamic library matrix (`.dll`/`.so`/`.dylib`), ELF GNU symbol versioning (`VERDEF`/`VERNEED`/`VERSYM`), Mach-O `@rpath`/`LC_ID_DYLIB`, and `.def`/COFF short-import libraries (`compiler/link/dynlib_matrix`, `compiler/obj/def_import`).
    - `T688` (`axiom-qa`): Artifact & library matrix conformance suite (`tests/conformance/p16/e16_10_artifact_matrix`).

11. **E16.11 — Universal / multi-architecture artifacts (`T689`–`T692`)**:
    - `T689` (`axiom-architect`): `spec/SPEC-90-universal-multiarch-artifacts.md` — Mach-O Fat / Universal 2 (`FAT_MAGIC`/`0xcafebabe`, `FAT_MAGIC_64`/`0xcafebabf`) multi-arch executables, `.dylib`s, and static archives (`x86_64-apple-darwin` + `aarch64-apple-darwin`), slice alignment (16 KiB ARM64, 4 KiB x86_64), and CLI slice inspection.
    - `T690` (`axiom-backend`): `x86_64-apple-darwin` Mach-O slice emitter & Fat/Universal 2 binary/archive composer (`compiler/obj/macho_universal`, `compiler/target/x64/macos`).
    - `T691` (`axiom-backend`): Driver `--universal-targets` build pipeline & `lipo`-equivalent slice inspection/extraction (`compiler/driver/universal`, `compiler/driver/emit_universal`).
    - `T692` (`axiom-qa`): Universal / multi-arch artifacts conformance suite (`tests/conformance/p16/e16_11_universal_artifacts`).

12. **E16.12 — Windows on ARM64 (`T693`–`T696`)**:
    - `T693` (`axiom-architect`): `spec/SPEC-91-windows-arm64.md` — `aarch64-pc-windows-msvc` ABI deltas (variadics in GPRs `x0`–`x7`, `x18` TEB reservation), `__chkstk` (`x15` in 16-byte units), COFF `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) relocations, `.pdata`/`.xdata` ARM64 unwind info, and PE32+ ARM64 linking.
    - `T694` (`axiom-backend`): Windows ARM64 ABI pass, `x15` `__chkstk` prologue/`.pdata`/`.xdata` unwind emitter & COFF `0xAA64` object writer (`compiler/abi/win_arm64`, `compiler/target/aarch64/win_frame`, `compiler/obj/coff_arm64`).
    - `T695` (`axiom-backend`): PE32+ ARM64 `.exe`/`.dll` linker, ARM64 IAT import thunks, range-extension branch veneers & `std.sys.windows.arm64` (`compiler/link/pe_arm64`, `std/sys/windows/arm64`).
    - `T696` (`axiom-qa`): Windows ARM64 conformance suite (`tests/conformance/p16/e16_12_windows_arm64`).

## Round 1 QA Fixes

- **Finding 1 (BLOCKER, `spec/requirements/CATALOG.md:14` and `6406`–`9050`)**: Restored the 6th column (`needs`) to `-` on all 327 P16 requirement rows (`REQ-TOOL-001` and `REQ-TGT-001`..`REQ-TGT-326`) and placed the concrete task IDs (`T066`, `T650`–`T696`) into the 7th column (`status`), replacing every `EPIC(E16.*)` entry (`0` `EPIC(E16.*)` strings remain in `spec/requirements/CATALOG.md`; `reqcov.py --phase P16-targets-platforms --strict` outputs 327 rows and `reqcov.py --strict` reports `v1-full epic=836`).
- **Finding 2 (MAJOR, `spec/requirements/CATALOG.md:14` & `_workspaces/tasks/todo/T682-e16-8-cfg-predicate-evaluator-hir-pruning-cross-driver.md:15`)**: Added `REQ-TOOL-001` to `T682`'s `covers:` list and updated `CATALOG.md:14` (`REQ-TOOL-001` `status` column) to `T024, T026, T681, T682, T683, T684, T686` so bidirectional coverage matches across all tasks covering `REQ-TOOL-001`.
- **Report & Title Cleanup**: Removed unrelated entries from `## Files changed`, aligned `SPEC-80`/`SPEC-81`/`SPEC-86` filenames with the task files, and normalized em-dashes in `T685`–`T696` titles.

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T066-linux-x86-64-sysv-abi-elf64-writer-static-elf-link.md
- ./_workspaces/tasks/todo/T316-phase-p16-gate-targets-platforms.md
- ./_workspaces/tasks/todo/T463-e12-3-portable-simd-masks-tensor-views-spec.md
- ./_workspaces/tasks/todo/T650-e16-9-linux-x86-64-sysv-abi-elf64-static-spec.md
- ./_workspaces/tasks/todo/T651-e16-9-std-sys-linux-syscalls-wsl-runner.md
- ./_workspaces/tasks/todo/T652-e16-9-linux-x86-64-static-elf-conformance.md
- ./_workspaces/tasks/todo/T653-e16-1-target-desc-isa-conformance-spec.md
- ./_workspaces/tasks/todo/T654-e16-1-target-desc-registry-regfile-abi-table.md
- ./_workspaces/tasks/todo/T655-e16-1-isa-table-legalizer-machine-verifier.md
- ./_workspaces/tasks/todo/T656-e16-1-target-desc-backend-conformance.md
- ./_workspaces/tasks/todo/T657-e16-2-linux-elf-dynamic-pie-got-plt-spec.md
- ./_workspaces/tasks/todo/T658-e16-2-x64-pic-got-plt-elf-dynamic-sections.md
- ./_workspaces/tasks/todo/T659-e16-2-elf64-pie-so-linker-libc-dlopen.md
- ./_workspaces/tasks/todo/T660-e16-2-linux-elf-dynamic-conformance.md
- ./_workspaces/tasks/todo/T661-e16-3-aarch64-isa-aapcs64-linux-spec.md
- ./_workspaces/tasks/todo/T662-e16-3-aarch64-aapcs64-frame-isel.md
- ./_workspaces/tasks/todo/T663-e16-3-aarch64-encoder-elf-linker-std-sys.md
- ./_workspaces/tasks/todo/T664-e16-3-aarch64-linux-conformance.md
- ./_workspaces/tasks/todo/T665-e16-4-macos-aarch64-macho-spec.md
- ./_workspaces/tasks/todo/T666-e16-4-apple-arm64-abi-macho-object-writer.md
- ./_workspaces/tasks/todo/T667-e16-4-macho-linker-chained-fixups-codesign-std.md
- ./_workspaces/tasks/todo/T668-e16-4-macos-aarch64-macho-conformance.md
- ./_workspaces/tasks/todo/T669-e16-5-android-aarch64-jni-spec.md
- ./_workspaces/tasks/todo/T670-e16-5-aarch64-android-bionic-elf-linker-std.md
- ./_workspaces/tasks/todo/T671-e16-5-std-ffi-jni-and-jni-export.md
- ./_workspaces/tasks/todo/T672-e16-5-android-aarch64-jni-conformance.md
- ./_workspaces/tasks/todo/T673-e16-6-wasm32-backend-stackify-wasi-spec.md
- ./_workspaces/tasks/todo/T674-e16-6-wasm32-cfg-structuring-stackification-abi.md
- ./_workspaces/tasks/todo/T675-e16-6-wasm32-binary-writer-validator-linker-wasi.md
- ./_workspaces/tasks/todo/T676-e16-6-wasm32-conformance.md
- ./_workspaces/tasks/todo/T677-e16-7-riscv64-rv64gc-lp64d-linux-spec.md
- ./_workspaces/tasks/todo/T678-e16-7-riscv64-lp64d-abi-flagless-isel.md
- ./_workspaces/tasks/todo/T679-e16-7-riscv64-encoder-elf-linker-std-sys.md
- ./_workspaces/tasks/todo/T680-e16-7-riscv64-conformance.md
- ./_workspaces/tasks/todo/T681-e16-8-cross-compilation-cfg-platform-layer-spec.md
- ./_workspaces/tasks/todo/T682-e16-8-cfg-predicate-evaluator-hir-pruning-cross-driver.md
- ./_workspaces/tasks/todo/T683-e16-8-hermetic-sysroot-stubs-std-os-platform.md
- ./_workspaces/tasks/todo/T684-e16-8-cross-compilation-platform-conformance.md
- ./_workspaces/tasks/todo/T685-e16-10-artifact-kinds-library-matrix-spec.md
- ./_workspaces/tasks/todo/T686-e16-10-cross-target-static-archive-producer-consumer.md
- ./_workspaces/tasks/todo/T687-e16-10-cross-target-dynlib-matrix-versioning-def-import.md
- ./_workspaces/tasks/todo/T688-e16-10-artifact-library-matrix-conformance.md
- ./_workspaces/tasks/todo/T689-e16-11-universal-multiarch-artifacts-spec.md
- ./_workspaces/tasks/todo/T690-e16-11-macho-x64-slice-fat-universal-composer.md
- ./_workspaces/tasks/todo/T691-e16-11-driver-universal-pipeline-inspect-slice.md
- ./_workspaces/tasks/todo/T692-e16-11-universal-multiarch-artifacts-conformance.md
- ./_workspaces/tasks/todo/T693-e16-12-windows-arm64-pe-abi-coff-spec.md
- ./_workspaces/tasks/todo/T694-e16-12-win-arm64-abi-chkstk-coff-arm64-writer.md
- ./_workspaces/tasks/todo/T695-e16-12-pe-arm64-exe-dll-linker-import-std-sys.md
- ./_workspaces/tasks/todo/T696-e16-12-windows-arm64-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P16-targets-platforms --strict` → `327 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `v1-full epic=836  implemented=414  planned=7581`, `gaps: 0`, `COVERAGE OK` (`0` `EPIC(E16.*)` rows remaining)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (460 tasks)`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T066`, `T316`, `T650`–`T696` → `0 warnings`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T216` → `51 stage, 0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=1
