---
id: T665
title: E16.4 — Canonical macOS AArch64 Darwin ABI, Mach-O 64 object/image & ad-hoc codesign specification (SPEC-84)
phase: P16-targets-platforms
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T216, T511, T661]
priority: 108
status: done
attempts: 1
paths: [spec/SPEC-84-macos-aarch64-macho.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-83-aarch64-linux.md, 0193, 0196, 0217, 0220, tasks/0369, tasks/0453, tasks/0563]
covers: [REQ-TGT-147, REQ-TGT-296, REQ-TGT-297, REQ-TGT-298]
started: 2026-11-03 23:19:57
finished: 2026-11-04 00:31:04
---
# T665 — E16.4 — Canonical macOS AArch64 Darwin ABI, Mach-O 64 object/image & ad-hoc codesign specification (SPEC-84)

## Goal
Consolidate the canonical specification for Axiom's `aarch64-macos` target: Apple ARM64 ABI differences from standard AAPCS64, Mach-O 64-bit relocatable object (`MH_OBJECT`), executable (`MH_EXECUTE`), and dynamic library (`MH_DYLIB`) formats, BSD `ar` archives, `dyld` chained fixups / export trie, self-contained ad-hoc `LC_CODE_SIGNATURE` signing, and `libSystem.B.dylib` (`std.sys.macos`) OS bindings into `spec/SPEC-84-macos-aarch64-macho.md` (`AXS-MACHO-*` rule IDs).

## Scope
- Write `spec/SPEC-84-macos-aarch64-macho.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-MACHO-NNN` rules (`0196`, `0220 §7`).
- Specify Apple ARM64 ABI differences from standard AAPCS64 (`0196 §1–2`): `X18` strictly reserved as Apple platform register (never touched by user code), caller sign/zero extension of `< 32`-bit integer arguments, tightly packed natural-alignment stack slots for spilled non-variadic arguments (instead of 8-byte slots), variadic arguments always placed on the stack in 8-byte slots, 128-byte leaf red zone, `X29` frame-pointer chain requirement, and `_` leading underscore C symbol mangling.
- Specify the Mach-O 64-bit object and image model (`0196 §3–19`, `tasks/0563 §304`): `mach_header_64` (`MH_MAGIC_64 = 0xFEEDFACF`, `CPU_TYPE_ARM64 = 0x0100000C`, `MH_OBJECT`, `MH_EXECUTE`, `MH_DYLIB`, `MH_PIE`, `MH_TWOLEVEL`, `MH_SUBSECTIONS_VIA_SYMBOLS`), 16 KiB (`0x4000`) VM page alignment on Apple Silicon, segments (`__PAGEZERO`, `__TEXT`, `__DATA_CONST`, `__DATA`, `__LINKEDIT`), sections (`__text`, `__stubs`, `__cstring`, `__const`, `__got`, `__data`, `__bss`, `__thread_vars`, `__thread_data`), and ARM64 Mach-O relocations (`ARM64_RELOC_UNSIGNED`, `ARM64_RELOC_SUBTRACTOR`, `ARM64_RELOC_BRANCH26`, `ARM64_RELOC_PAGE21`, `ARM64_RELOC_PAGEOFF12`, `ARM64_RELOC_GOT_LOAD_PAGE21`, `ARM64_RELOC_GOT_LOAD_PAGEOFF12`, `ARM64_RELOC_ADDEND`).
- Specify Mach-O load commands (`LC_SEGMENT_64`, `LC_MAIN`, `LC_LOAD_DYLINKER` `/usr/lib/dyld`, `LC_LOAD_DYLIB` `/usr/lib/libSystem.B.dylib`, `LC_ID_DYLIB`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, `LC_SYMTAB`, `LC_DYSYMTAB`, `LC_BUILD_VERSION`, `LC_UUID`, `LC_CODE_SIGNATURE`), BSD `ar` archives (`__.SYMDEF SORTED`), and self-contained ad-hoc `LC_CODE_SIGNATURE` (`CS_MAGIC_EMBEDDED_SIGNATURE`, `CS_MAGIC_CODEDIRECTORY` with SHA-256 4 KiB page hashes required by Apple Silicon kernel policy without external Xcode tools).
- Specify the macOS platform boundary (`0196 §15–16`, `0220 §7`): macOS binaries link dynamically against `libSystem.B.dylib` (using built-in `.tbd` stub metadata when cross-compiling) rather than unstable raw Darwin/Mach syscalls.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-84-macos-aarch64-macho.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-MACHO-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T665-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of Apple ARM64 ABI and Mach-O writer/linker (`T666`, `T667`).
- Universal Mach-O binaries (`x86_64` + `aarch64`), specified in `T689` (`SPEC-90`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P16 (`P16-targets-platforms`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 08:39:00 created by T216 (P16 phase planning)
- 2026-11-03 23:19:57 started (attempt 1) T665-impl
- 2026-11-04 00:31:04 accepted by QA -> done
