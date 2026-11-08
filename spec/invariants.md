# Axiom architecture and semantic invariants (catalogue)

## Tóm tắt
Danh mục các **bất biến** mà code compiler (axiom0 bằng C, sau này axiomc bằng Axiom) phải giữ: định
danh có kiểu, arena, không có biến toàn cục, span tính theo byte, thứ tự tầng kiến trúc, chẩn đoán là
dữ liệu, tính tất định (chạy hai lần cho kết quả từng byte giống nhau), MIR đã kiểm định là ranh giới
duy nhất, oracle (trình thông dịch MIR) và bản native phải cho cùng kết quả, mô hình ngữ nghĩa đóng
băng (ownership không phải borrow checker, view/mut_view, drop tất định, không GC, không runtime ẩn),
và phạm vi tối thiểu của axiom0.
Mỗi bất biến có mã `INV-<NHÓM>-NNN`, câu phát biểu, nguồn, và trường `verify:` máy đọc được, chỉ ra thư
mục test hoặc công cụ kiểm tra nó. Trường `since:` ghi task tạo ra phép kiểm tra đó. `tools/gatecheck.py`
(T022) đọc các trường này: một bất biến không được chỉ là lời bình (0264 §23-24). Tài liệu gốc đánh số
ADIAG trùng nhau giữa 0146, 0153 và tasks/0360, nên ở đây dùng không gian mã riêng (ADR-0011 §8).

Status: canonical (T002, 2026-10-04). Map of the spec set: `spec/INDEX.md`. Diagnostic rules:
`spec/diagnostics.md` (AXD-*). Decision record: ADR-0011.

## 1. Format (machine-readable; parsed by `tools/gatecheck.py`)

Every invariant is one block:

```text
### INV-<GROUP>-<NNN> — <short title>
- statement: <one paragraph; normative>
- source: <docs/base refs, ADRs, spec rule ids>
- verify: <target>[, <target>…]
- since: <task id>
- check: <what the verifying test or tool asserts>
```

Rules for `gatecheck.py` (refining T022 scope item (a)):
- **IG-1.** The id matches `^### (INV-[A-Z]+-[0-9]{3}) — ` and is unique. Ids are never renumbered
  or reused. A retired invariant keeps its block, with `statement: RETIRED (<ADR>)` and
  `verify: none`.
- **IG-2.** `verify:` lists one or more repository-relative paths separated by `, `: a test directory
  (`tests/…`) or a check program (`tools/…`, or a harness script under `.claude/skills/…/scripts/`).
- **IG-3.** `since:` names a board task that delivers the check. If that task is in
  `_workspaces/tasks/done/`, every `verify:` path must exist (a directory must contain at least one
  test file). If it is not done, the task must exist on the board and must not be superseded. This
  is how invariants of later phases are catalogued before their tests exist.
  A `verify:` path need not be in the `paths:` of the `since` task. It may be delivered by a
  task in the `depends` closure of the `since` task, or be an existing harness script; the
  `check:` line then names the task that delivers it.
- **IG-4.** The fields appear in the order shown, each on one line starting with `- <field>: `. Text
  outside blocks is ignored.

Groups: `KERN` kernel, `LAYER` architecture layers, `DIAG` diagnostics, `DET` determinism, `PIPE`
pipeline and verifier boundary, `ORACLE` oracle and differential agreement, `SEM` frozen semantic model,
`BOOT` bootstrap scope, `LEX` / `GRM` invariants already stated in SPEC-01 / SPEC-02, `CONC` concurrency,
memory model, atomics, threads, sync, and async state machines (`SPEC-30`..`SPEC-33`), `INT` scalar integer
model, 128-bit arithmetic, conversions, and multi-width integer promotion (`SPEC-40`), `FLT` IEEE-754
floating-point semantics, mixed-type promotion lattice, SSE2/`Xmm` ABI lowering, formatting, and pure-Axiom
`std.math` (`SPEC-41`), `SIMD` portable SIMD vectors, masks, masked memory/gather/scatter safety,
data-oriented `TensorView`/`MatrixView`, LIR vector lowering/legalization, Windows x64 vector ABI, x86-64 SSE2/AVX2/VEX encoding, `TargetDesc` CPU feature hierarchy, `@target_feature` legality, `std.arch` `CPUID`/`XGETBV` detection, and `@multiversion` dispatch (`SPEC-42`, `SPEC-43`, `SPEC-44`), `UNS` unsafe boundary, raw pointer strict provenance, UB detector, `REQ-OWNER-008`
address introspection & fixed-address placement, and FFI/ABI (`SPEC-50`), `MEM` raw memory access, volatile/MMIO register wrappers, untagged `union` types, `@repr(packed)`/`@align(N)` layout, `MaybeUninit<T>`, `bitcast`, and pointer address spaces (`SPEC-51`), `FRE` freestanding execution, modular runtime composition, compilation profiles, `@entry`/`@naked`/`@section`/`@used`, interrupt handlers, and runtime capability graph (`SPEC-52`), `SEC` safety profiles, capability-based OS authority, `Secret<T>` zeroization, and `@constant_time` execution (`SPEC-53`), `PAN` panic strategies (`--panic abort|unwind`), `catch_unwind`, deterministic `Drop` unwinding, `@no_panic` verification, Windows x64 SEH `.pdata`/`.xdata` unwind tables, and `extern "C"` FFI no-unwind barrier (`SPEC-54`), `ADR` fixed-address `@at` / `@addr` overlay and placement declarations (`REQ-OWNER-003`), ordinary-syntax MMIO register access, `REQ-OWNER-008` address introspection, COFF `IMAGE_SYM_ABSOLUTE` symbols, pinned VMA sections, `--format bin` raw binary output, and oracle simulated address space & device model (`SPEC-55`), `MOD` module-relative `@at(image("mod") + offset)` and `@at(image_self() + offset)` hosted overlays (`REQ-OWNER-005`), overlay-only enforcement, open-world dynamic library optimization barrier (`REQ-ABI-095`, `REQ-FFI-119`), `LoadTimeSlot` indirect dispatch, `GetModuleHandleW`/`__ImageBase` PE DLL `DllMain` / EXE startup resolution, and oracle `ProcessModuleMap` (`SPEC-56`), `CTM` Comptime 2.0 unified execution model, sandboxed authority, value lifting & resource no-escape barrier, partial evaluation, specialization, dependency-tracked caching, and `const`/`static`/`TLS` initialization (`SPEC-60`), `RFL` compile-time reflection data model (`TypeInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`), visibility & layout query contracts, typed `@derive` synthesis with provenance tracking & full semantic/MIR re-verification, and zero-overhead `std.reflect` / `std.derive` (`SPEC-61`), `GEN` synchronous generators (`gen fn`, `yield`), lazy pull-based iterator state machines, `LiveAcrossYield` ownership & capability rules (`AX_GEN_*`), HIR → MIR boundary & structural invariants, per-state `Drop` cleanup, and `for-in` / `std.iter` lazy combinators (`SPEC-62`), `DYN` dynamic trait objects (`dyn Trait`), object-safety verification (`AX_DYN_NOT_OBJECT_SAFE`), two-word fat-pointer representation, unsizing coercions, `.rdata` vtable ABI, and `Box<dyn Trait>` dynamic `Drop` (`SPEC-63`), `WLIB` Windows x64 artifact kinds (`--kind exe|obj|lib|dll`), deterministic COFF `.lib` archives & fixed-point extraction, PE32+ `.dll` emission (`.edata`, synthesized `DllMain`, `.reloc`), companion COFF short-import `.lib`, and `ADR-0034` §4 OI-07b `__imp_<name>` cross-linking (`SPEC-26`), `QRY` demand-driven `CompilerDB` input/derived tables, `QueryStack` dependency DAG recording, `inspect --emit=query-graph`, active-stack cycle detection & canonical `SemanticKey` rotation, fallback recovery values, snapshot-bound diagnostic replay, and revision invalidation (`SPEC-21`), `INC` incremental compilation, four-tier 128-bit fingerprints (`Source`/`Ast`/`Interface`/`Abi`/`Body`/`Codegen`), red-green `try_mark_green` change propagation, persistent `.axiom-cache` schema, hermetic `EnvironmentDigest`, `< 100 ms` no-op rebuild fast path, and clean-vs-incremental equivalence (`SPEC-22`), `PAR` parallel compilation determinism (`--jobs 1` == `--jobs N`), thread-safe immutable `DatabaseSnapshot` sharing, module-scoped `(ModuleId, LocalIndex)` semantic IDs, sharded interner, `SingleFlightLatch` & cross-worker `WaitForGraph` cycle detection, work-stealing DAG scheduler, parallel per-`CGU` codegen, and deterministic post-join diagnostic/artifact merging (`SPEC-23`), `ART` canonical artifact format, `.axmi` module interfaces, and embedded `.axmeta`/`.axmir`/`.axlto` object sections (`SPEC-24`), `PCT` formal pass contracts (`PassContract`), proof-carrying transformation certificates (`ProofCertificate` / `ProofProvenance`), three-valued `Certainty` (`Proven`/`Possible`/`Unknown`) fail-closed gate, shared source dataflow (`Source Analysis 2.0`), multi-category `EffectSummary` (`Effect System 2.0`), bounded `Symbolic Execution 2.0`, and per-function `TranslationWitness` validation (`SPEC-25`), `LNK` separate compilation (`.obj` + `.axmi`), format-neutral `LinkIR`, multi-object & `.lib` archive linking, `Strong` vs `Weak` vs `IMAGE_SCN_LNK_COMDAT` symbol resolution, demangled linker diagnostics (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_ABI_MISMATCH`), per-item section subdivision, and root-set reachability section GC (`SPEC-27`), `VEC` loop & `SLP` auto-vectorization, capability-disjoint dependence proving, and target SIMD cost modeling (`SPEC-74`), `ELFS` Linux x86-64 System V AMD64 ABI (`CallConv.SysV64`), ELF64 relocatable object (`.o`) & GNU `ar` (`.a`) emission, static ELF64 executable linking (`ET_EXEC` at `0x400000` with `_start`), and `std.sys.linux` raw syscall host interface (`SPEC-80`), `TGTD` declarative `TargetDesc`, `RegisterFile`, `IsaTable`, `Legalizer`, pre-encoding `verify_mc`, and target-independent LIR backend conformance (`SPEC-81`), `ELFD` Linux ELF64 dynamic linking (`ET_DYN`), `PIE`, `GOT`/`PLT`, `lib<name>.so`, `.dynsym`/`.gnu.hash`/`.dynamic`, `PT_GNU_RELRO`, GNU symbol versioning, and `libc`/`std.sys.linux_dl` `dlopen` interoperability (`SPEC-82`), `AARCH` AArch64 `RegisterFile`, `CallConv.Aapcs64` calling convention, `STP`/`LDP` frame lowering, A64 instruction selection & NEON/LL-SC/`+lse` atomics, 32-bit fixed-width encoding, `EM_AARCH64` ELF64 relocations/veneers, `.eh_frame` DWARF unwind, and `std.sys.linux_aarch64` `SVC #0` syscalls (`SPEC-83`), `MACHO` macOS AArch64 `CallConv.Aapcs64Darwin` Darwin ABI, Mach-O 64 `MH_OBJECT`/`ARM64_RELOC_*`/BSD `ar`, 16 KiB W^X `MH_EXECUTE` & `MH_DYLIB` linking, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, self-contained SHA-256 ad-hoc `LC_CODE_SIGNATURE`, hermetic `.tbd`/`libSystem.B.dylib` resolution, and `std.sys.macos` (`SPEC-84`), `ANDR` Android AArch64 (`aarch64-android`) `api_level` target identity, `X18` ShadowCallStack reservation, 16 KiB page-aligned Bionic ELF64 `ET_DYN` PIE (`/system/bin/linker64`) & `lib<stem>.so` (`DT_SONAME`) linking, 152-byte `.note.android.ident`, NDK-free built-in Bionic stub symbol catalog, API-level & private-library linker namespace verification, and `std.sys.android` (`SPEC-85`), `JNI` 3-layer capability-safe JNI binding stack (`std.ffi.jni.raw`, `std.ffi.jni` `JniEnv`/`JavaVM`/`JLocal`/`JGlobal`/`JWeak`, `with_local_frame`, `with_attached_env`, `JString`, array views, mandatory `ExceptionCheck` -> `Result<T, JException>`, `@jni_export` `Java_*` + `JNI_OnLoad`, no-unwind panic/exception barrier, and `MockJvm`; `SPEC-85`), `WASM` WASM32 virtual stack-machine target (`wasm32-freestanding`, `wasm32-wasi`), dual-storage non-addressable WASM locals vs 16B-aligned `LinearMemory` shadow stack (`$__stack_pointer`), arbitrary `LIR` CFG structuring (`block`/`loop`/`if-else`/`br_table` & `$irr_state` irreducible cycle dispatch) & SSA expression-tree stackification, `CallConv.Wasm` Basic C ABI, pre-emission `verify_wasm` bytecode validation, relocatable `.wasm` (`linking` v2) & static `.wasm` linking, and capability-scoped `std.sys.wasi` (`wasi_snapshot_preview1`; `SPEC-86`), `RISCV` RISC-V 64 (`RV64GC`) flagless ISA `RegisterFile` (`x0` `ZeroReg`, reserved `sp`/`gp`/`tp`, `f32` NaN-boxing, scalable `RVV`), `CallConv.RiscV` `LP64D` psABI, flagless ISel & RVWMO atomics, pre-encoding `verify_mc` & pseudo expansion, 32-bit + 16-bit `RVC` encoding, relaxation-independent `EM_RISCV = 243` ELF64 paired `PCREL_HI20`/`LO12` linking & Variant I `tp` TLS, and `std.sys.linux_riscv64` `ecall` host interface (`SPEC-87`), `XCMP` single-binary multi-target cross-compilation (`Build`/`Host`/`Target` isolation, frontend ISA independence & `Axiom LIR` `TargetBackend` contract, 3-tier query/cache sharing, target-parameterized `const`/`comptime` layout, cross-host byte-for-byte determinism), `@cfg(...)` parse-all-then-prune-before-resolve conditional compilation, hermetic `--sysroot` / built-in OS import stub catalogs, and the 3-level OS & platform layer (`Level 1` portable `std.*`, `Level 2` `@cfg`-gated `std.os.*`, `Level 3` internal `std.sys.*`; `SPEC-88`), `ARTM` cross-target artifact kinds (`--kind <exe|bin|obj|lib|staticlib|dll|cdylib|axlib|wasm-module>`), deterministic `!<arch>\n` static archives (`CoffAr`, `GnuAr` + `/SYM64/`, `BsdAr` + `__.SYMDEF SORTED`), `.axlib` `lib.axrmeta` package containers & diamond coherence, hidden-by-default `cdylib` symbol isolation, Windows `.def` & import `.lib` tooling, ELF64 GNU symbol versioning (`VERSYM`/`VERDEF`/`VERNEED`), Mach-O `MH_DYLIB` `@rpath`/version triples/`MH_TWOLEVEL`, WASM `_initialize` reactor vs `_start` command modules, `--whole-archive` vs fixed-point archive extraction, cross-format `Strong`/`Weak`/`Comdat` symbol resolution, and final-image `.axmeta`/`.axmir`/`.axlto` stripping (`SPEC-89`), `UNIV` explicit multi-target artifact composition (`ArtifactKind.Universal` vs `.axpkg`), `TargetId.X86_64Macos` (`x86_64-macos` / `x86_64-apple-darwin`) `CallConv.SysV64` Darwin Mach-O slice delta (`_` symbol prefix, 4 KiB page alignment, `X86_64_RELOC_*` `0..9`, `$INODE64` ABI), Mach-O Universal 2 big-endian `fat_header` (`FAT_MAGIC = 0xCAFEBABE`, `FAT_MAGIC_64 = 0xCAFEBABF`) & `fat_arch`/`fat_arch_64` composer/reader, `2^12` x86_64 / `2^14` arm64 slice alignment, ascending `cputype` sorting, per-slice `LC_CODE_SIGNATURE` preservation, universal `BsdAr` `.a`/`.axlib` archives, `--universal-targets` cache-isolated build pipeline, and native `lipo`-free `--inspect-slices`/`--extract-slice`/`--verify-arch` CLI tooling (`SPEC-90`), `WARM` Windows ARM64 (`aarch64-windows` / `aarch64-pc-windows-msvc`) `CallConv.WinArm64` ABI, strict `X18` TEB reservation, `BL __chkstk` (`X15 = alloc_bytes >> 4`) stack probing, COFF `IMAGE_FILE_MACHINE_ARM64 = 0xAA64` & `IMAGE_REL_ARM64_*` (`0x0000..0x0011`) relocations, `.pdata`/`.xdata` SEH unwind tables, PE32+ ARM64 `.exe`/`.dll` linking (`12`-byte `__imp_` thunks, `±128 MiB` veneers, `.reloc`), `[X18, #0x58]` `_tls_index` TLS, and `std.sys.windows.arm64` (`SPEC-91`), `LSP` canonical Language Server Protocol (`axiomc lsp`), single semantic authority over `CompilerDB` (`SPEC-21`/`SPEC-22`), generational entity IDs (`SymbolId`, `TypeId`, `FunctionId`, `LocalId`, `PlaceId`), JSON-RPC 2.0 wire protocol, in-memory `VfsOverlay` & UTF-8/UTF-16/UTF-32 `LineIndex`, `std.editor` `AXEDITOR` B-tree piece-table text buffer, partial-program syntax/semantic recovery, constraint-aware semantic IDE queries (`completion`, `hover`, `goto_definition`, `find_references`, `rename`, `semantic_tokens`, `inlay_hint`, `code_action`), `AXCODEEDITOR` semantic highlighting & ownership/move/async inlays, and thin VS Code client (`tools/vscode-axiom`; `SPEC-100`), `FMT` canonical language form, unified `CompilerDB` frontend authority, lossless Concrete Syntax Tree (`CST`) & 5-slot trivia attachment (`//`, `///`, `//!`, nested `/* */`, `#region`/`#endregion`), deterministic Wadler-Lindig `Doc` layout algebra, zero-configuration canonical formatting (`4` spaces, `100` columns, `LF`, `=`, `.`), `parse(fmt(src)) == parse(src)` AST-equivalence verification gate, single-step idempotence `fmt(fmt(src)) == fmt(src)`, and `axiomc fmt` (`--check`, `--stdin`) / LSP formatting parity (`SPEC-101`). A new group is added by editing this list.

## 2. Kernel

### INV-KERN-001 — Typed IDs
- statement: Every compiler entity (file, string, symbol, type, HIR node, MIR body/local/block, section, symbol in an object, …) is referred to by a typed ID: one C struct per ID kind, index 0 means "none", and tables are accessed only through `xxx_get(ctx, id)`. IDs of different kinds are never interchangeable.
- source: 0171 §40 AKERNEL-24; 0153 §37 ACKERNEL-20/23; tasks/0260 ABOOT-54/55; 0172 §2
- verify: tests/unit/kernel
- since: T007
- check: unit tests use the ID tables (create, get, 0 = none) and the ID types are distinct C structs (a test translation unit that mixes kinds is part of the kernel unit suite as a compile check documented by T007)

### INV-KERN-002 — Identity is not a memory address
- statement: No semantic decision, ordering or output depends on pointer values. Hash keys, ordering keys and printed identities use IDs or content, never addresses.
- source: 0153 ACKERNEL-21, ADET-22
- verify: tests/unit/kernel
- since: T007
- check: hash-map iteration and interner tests give identical results across runs with different allocation patterns (insertion order, not address order)

### INV-KERN-003 — Arenas own phase data
- statement: Phase data lives in arenas freed as a whole at phase boundaries. There is no per-node free, no garbage collector and no reference counting.
- source: tasks/0260 ABOOT-49..53, ABOOT-56/57; axiom-c-stage0
- verify: tests/unit/kernel
- since: T007
- check: arena unit tests (growth, alignment, reset, free-all)

### INV-KERN-004 — Interning
- statement: Equal strings interned in one session have the same `StrId`. `StrId` is not a `SymbolId`. Canonical types are hash-consed, so two types are equal if and only if their `TypeId`s are equal. Interning defines identity only, never language semantics.
- source: 0153 AINTERN-20..23; 0172 §7-9
- verify: tests/unit/kernel, tests/typeck
- since: T017
- check: interner unit tests (T007); type-interner tests for structural equality (T017) (tests/unit/kernel is delivered by T007, a dependency of T017)

### INV-KERN-005 — Byte spans, derived line/column
- statement: Spans are `FileId` plus the byte range `[start, end)`. Line and column numbers are computed only by renderers through the line map; a CRLF pair counts as one line break.
- source: 0153 ASOURCE-20/21; 0171 AKERNEL-26; tasks/0360 ADIAG-53/54; SPEC-01 §1; AXD-051
- verify: tests/unit/source
- since: T008
- check: line-map tests for CRLF, BOM, multi-byte characters, empty file and last line without newline

### INV-KERN-006 — Source identity and immutability
- statement: A `FileId` is not a path string. Source text never changes during a compilation. Generated sources get their own `FileId` with an explicit origin.
- source: 0153 ASOURCE-22..24
- verify: tests/unit/source
- since: T008
- check: source-database tests (virtual files, two paths to one file, content hash)

### INV-KERN-007 — Defined hash and map order
- statement: The 64-bit hash function and the insertion-ordered iteration of HashMap/HashSet in axiom0 `kernel/` are specified, and std (T073) uses the same ones, so ported code produces byte-identical output.
- source: ADR-0004 §4; 0153 ADET-21
- verify: tests/unit/kernel
- since: T007
- check: known-answer hash vectors and an insertion-order iteration test (std side: tests/std/collections, T073)

## 3. Architecture layers (checked by `tools/archcheck.py`)

### INV-LAYER-001 — Layer order
- statement: A module includes headers only from its own layer or lower layers: kernel < source < diag < lex < syntax < resolve < hir < types < traits < own < mir < verify < {interp, opt} < lir < abi < target/x64 < obj < link < driver. `objmodel` is a low layer that depends only on `kernel`. The kernel depends on no back end, runtime or language-semantic layer. ABI lowering lives in `abi` as a LIR-to-LIR pass, so no MIR-level layer sees ABI details.
- source: axiom-c-stage0 (layer rules); 0171 AKERNEL-35..37; 0172 §23-24; ADR-0003
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: archcheck passes on the tree; a bad fixture per rule fails

### INV-LAYER-002 — Object and linker layers stay below the IR
- statement: `obj` and `link` depend only on `objmodel`, `kernel` and `diag`, never on MIR, HIR or front-end layers ("linker → parser" is a violation).
- source: 0263 §46; axiom-c-stage0
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: rule fixture `link` including `mir/` fails

### INV-LAYER-003 — Oracle and optimizer independence
- statement: `interp` never includes `target`, `lir`, `abi`, `obj` or `link`, and `opt` never includes `syntax`. The oracle is independent of the native back end.
- source: tasks/0260 ABOOT-76; axiom-c-stage0
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: rule fixtures for both exceptions

### INV-LAYER-004 — Const evaluation through an interface
- statement: `types` never includes `interp`. Constant evaluation goes through an evaluator interface that `types` declares and the driver connects to the interpreter.
- source: ADR-0004 §8
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: rule fixture `types` including `interp/` fails

### INV-LAYER-005 — Back end never sees the front end
- statement: `lir`, `abi`, `target/x64`, `objmodel`, `obj` and `link` never include `lex`, `syntax`, `resolve` or `hir`. Code generation starts from verified MIR only, never from AST or HIR.
- source: 0263 §28 (no dangerous shortcuts); 0152 pipeline; INV-PIPE-001
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: rule fixture `lir` including `syntax/` fails (this rule must be in T006's rules file; see ADR-0011 consequences)

### INV-LAYER-006 — No mutable globals, no printing in libraries
- statement: Outside `driver/` there are no mutable file-scope variables, and library layers never call `printf`, `puts`, `exit` or `abort` directly. Output comes only from the driver and the diagnostic renderers, and aborts only through `AX_ICE(...)`.
- source: tasks/0260 ABOOT-58; 0153 APAR-22; 0171 AKERNEL-29; AXD-001
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: heuristic rules for non-const file-scope variables and for `printf`/`exit(` outside `driver/` and `diag/` renderers

### INV-LAYER-007 — Diagnostic codes registered in their area file
- statement: A code `AX_<AREA>_*` is defined only in `diag/codes/<AREA>.def`, `<AREA>` is one of the 18 areas of `spec/diagnostics.md` §3, and no code is defined outside `diag/codes/`.
- source: ADR-0005 §2; AXD-020, AXD-030
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: fixture registering `AX_TYPE_X` in `NAME.def` fails

### INV-LAYER-008 — Standard library is Axiom source
- statement: `std/` contains Axiom sources only (`*.ax`, manifests, data). C provides only compiler intrinsics and OS FFI, never a std implementation.
- source: ROADMAP R8
- verify: tools/archcheck.py, tools/tests/archcheck
- since: T006
- check: a fixture `std/x.c` fails (this rule must be in T006's rules file; see ADR-0011 consequences)

## 4. Diagnostics

### INV-DIAG-001 — Diagnostics are data with stable codes
- statement: Every user-facing problem is a diagnostic value with a registered code (AXD-001..003, AXD-010). Tests identify diagnostics by code and position, never by message text.
- source: tasks/0360 ADIAG-20..23, ADIAG-73; 0146 §4; 0153 ADIAG-20..22; 0171 AKERNEL-27/28; tasks/0260 ABOOT-60
- verify: tests/unit/diag
- since: T009
- check: sink and registry unit tests; using an unregistered code fails to compile

### INV-DIAG-002 — Codes are never reused or removed
- statement: The registry only grows. Codes are never renamed, removed or given a new meaning (AXD-011).
- source: tasks/0360 ADIAG-24, ADIAG-75; 0146 §4
- verify: tests/unit/diag
- since: T009
- check: a golden list of all registered codes (T009); a removed or renamed code shows up as a golden diff that QA rejects

### INV-DIAG-003 — Primary span on every located error
- statement: Every error has a primary span, except the location-free codes of AXD-051.
- source: tasks/0360 ADIAG-25; 0146 §7; AXD-051
- verify: tests/unit/diag
- since: T009
- check: the sink rejects (as ICE in debug builds) a located-area error without a primary span

### INV-DIAG-004 — Deterministic diagnostic order
- statement: Diagnostics are sorted by the key of AXD-060, and their order never depends on hashing, addresses, threads, file-system listing order or import order.
- source: tasks/0360 ADIAG-51/52/78/79; 0153 APAR-23; SPEC-01 AXS-LEX-101
- verify: tests/unit/diag
- since: T009
- check: diagnostics emitted out of order are rendered in key order; registry-ordinal tie-break

### INV-DIAG-005 — Versioned JSON schema
- statement: `--json` produces exactly one schema-1 document on stderr as defined in AXD-063. The human and JSON renderings carry the same diagnostics in the same order.
- source: tasks/0360 ADIAG-34; 0146 §57; 0172 §12
- verify: tests/unit/diag, tests/driver
- since: T016
- check: JSON golden tests (renderer, T009) and driver tests of `--json` with 0, 1 and several diagnostics (T016) (tests/unit/diag is delivered by T009, a dependency of T016)

### INV-DIAG-006 — ICE is distinct and produces no artifact
- statement: An internal failure is reported as `AX_ICE_*`, exits with code 3 and never leaves an output artifact. Expected user errors never cause an ICE or a crash.
- source: tasks/0360 ADIAG-37/38; 0146 §50-51; tasks/0260 ABOOT-61/62; 0171 AKERNEL-34; AXD-042
- verify: tests/driver
- since: T016
- check: a test-only ICE trigger gives exit code 3 and no output file; exit codes 0/1/2 for the other cases

### INV-DIAG-007 — Never crash or hang on user input
- statement: Any byte sequence given as source produces diagnostics or a result, never a crash, hang or memory error.
- source: tasks/0262 §49; tasks/0260 ABOOT-61; 0263 §47
- verify: tests/fuzz, tools/fuzz.py
- since: T013
- check: the gate campaign `python tools/fuzz.py --seed 1 --iterations 200000` finds nothing

### INV-DIAG-008 — Recovery does not invent semantics
- statement: Error nodes and `Error` tokens produce no diagnostics in later stages, and poisoned operands suppress derived errors. The stage barrier of AXD-044 holds.
- source: tasks/0360 ADIAG-39..41, ADIAG-82/83; SPEC-02 AXS-GRM-100; AXD-044
- verify: tests/ui/parse, tests/ui/typeck
- since: T017
- check: ui tests with one root error assert exactly one diagnostic (parse side T011, type side T017) (tests/ui/parse is delivered by T011, a dependency of T017)

## 5. Determinism

### INV-DET-001 — Byte-identical outputs
- statement: Two runs of the compiler on the same inputs and flags produce byte-identical diagnostics, dumps, object files and executables. Results never depend on hash iteration order, addresses, time, environment variables not named as inputs, thread scheduling or directory listing order.
- source: 0153 ADET-20..24, AQUERY-20; 0171 AKERNEL-30; axiom-c-stage0
- verify: tests/diff
- since: T029
- check: the T029 determinism check builds every native-enabled run test twice and compares bytes; fuzz (T013) also flags non-deterministic `--json` output

### INV-DET-002 — No timestamps in artifacts
- statement: Object and image headers carry no time or host data (COFF/PE `TimeDateStamp` = 0, no absolute paths).
- source: tasks/0262 §43; 0263; axiom-x64-backend
- verify: tests/link
- since: T027
- check: header fields of linked fixtures are compared with expected values

### INV-DET-003 — Deterministic interpretation
- statement: The MIR interpreter gives the same output, exit code and step count for the same program, arguments and input.
- source: tasks/0260 ABOOT-48; 0025
- verify: tests/run/basic
- since: T021
- check: run tests in interp mode are compared byte-exactly against expected stdout and exit code

### INV-DET-004 — Reproducible self-compilation
- statement: axiomc2 and axiomc3 are byte-identical when built in different directories with identical flags, at -O0 and -O1.
- source: tasks/0260 ABOOT-73/79; tasks/0262 §42-43
- verify: tests/selfhost/fixedpoint, tools/bootstrap.py
- since: T087
- check: the fixed-point gate compares hashes

## 6. Pipeline and verifier boundary

### INV-PIPE-001 — Fixed pipeline, no shortcuts
- statement: Every program goes Source → Lexer → Parser → AST → Resolver → HIR → Typeck → THIR → ownership/capability → MIR (+ drop elaboration) → Verifier → {Interpreter | Optimizer → LIR → machine IR → Encoder → Object → Linker}. No stage is skipped, no machine code is generated from AST or HIR, and there is no textual assembly in the production path. MIR is target-independent and independent of physical storage strategy, stack-vs-heap placement, general register allocation, and vector register usage, and MIR lowering consumes Typed HIR (`THIR`) semantic facts without rediscovering source-level meaning (`SPEC-03` AXS-SEM-001, AXS-SEM-047).
- source: 0152 (pipeline); 0263 §28; ABOOT-46; tasks/0539 §89 AMIR-81..87; REQ-CORE-3051..3057; skill axiom-spec-index
- verify: tools/archcheck.py
- since: T006
- check: enforced structurally through INV-LAYER-005; driver stage list in `driver/pipeline.c` (T016)

### INV-PIPE-002 — Verified MIR is the checkpoint
- statement: The interpreter, the optimizer and MIR-to-LIR lowering consume only MIR that passed the verifier in the same compilation. The driver refuses to go on with unverified MIR.
- source: 0153 APASS-23; tasks/0260 ABOOT-47; tasks/0539 §89 AMIR-90; REQ-CORE-3060; T020; T050
- verify: tests/verify
- since: T020
- check: hand-written invalid MIR is rejected with `AX_VERIFY_*` and never executed

### INV-PIPE-003 — The verifier does not trust the analyses
- statement: The verifier re-checks move, drop and view invariants on the MIR itself and does not rely on the results of the analyses that produced it.
- source: T050; 0027; 0029; tasks/0539 §89 AMIR-88..89; REQ-CORE-3058..3059
- verify: tests/verify/own
- since: T050
- check: hand-written MIR with a double drop, a use after move and a missing drop is rejected

### INV-PIPE-004 — Optimization preserves verified semantics
- statement: Every optimization pass maps verified MIR to verified MIR with the same observable behaviour. With `--verify-each` the verifier runs after every pass.
- source: 0153 APASS-24; tasks/0262 §48
- verify: tests/diff/opt
- since: T043
- check: -O0 and -O1 agree with the interpreter; `--verify-each` is clean over the suite

### INV-PIPE-005 — Machine IR verified before encoding
- statement: Machine IR passes the machine-IR verifier (frame, stack probes, register classes) before encoding.
- source: ADR-0003
- verify: tests/mc/frame
- since: T025b
- check: malformed machine IR fixtures are rejected; frames over 4 KiB carry probes

### INV-PIPE-006 — Linear-scan register allocation and frame preservation
- statement: Post-RA Machine IR contains no virtual registers, satisfies all register-class, fixed-register (`rcx` shifts, `rax`/`rdx` div/mul), and call-clobber constraints, and saves/restores every modified callee-saved register in `FrameLayout` without altering observable program semantics (SPEC-77 AXS-RA-010..027).
- source: SPEC-77 AXS-RA-010..027; 0182 AREG-20..36, AFRAME-20..30; 0235 ARA-20..44; 0252 ARALLOC-20..60; tasks/0557 AREG-20..51
- verify: tests/mc/regalloc
- since: T063
- check: machine IR and differential run tests in tests/mc/regalloc verify high register pressure, call clobbers, fixed-register constraints, and callee-saved register restoration across -O0, -O1, and -O2

### INV-PIPE-007 — Instruction selection, branchless if-conversion, and post-RA peephole safety
- statement: Complex instruction selection (`lea` scaled addressing, constant division/modulo), branchless `cmovcc`/`setcc` if-conversion, and post-RA machine peephole rewrites preserve `EFLAGS` liveness, checked-arithmetic traps, and volatile/atomic/alias memory barriers, and pass the Machine IR verifier before encoding (SPEC-77 AXS-MCOPT-001..026).
- source: SPEC-77 AXS-MCOPT-001..026; 0162 §39-40; 0237 AMOPT-20..42; tasks/0406 AMICRO-20..45; tasks/0553 ACTRL-20..100; tasks/0559 AFINAL-20..50
- verify: tests/mc/isel_peephole, tests/conformance/p15/e15_8_regalloc_isel
- since: T629
- check: machine IR dump and differential conformance tests in tests/mc/isel_peephole (T628) and tests/conformance/p15/e15_8_regalloc_isel (T629) verify lea addressing, branchless cmov diamonds, flag-safe xor/test peepholes, and observable agreement across --interp, -O0, -O1, and -O2

### INV-PIPE-008 — OptIR SSA/MemorySSA construction, fail-closed pass contracts, and scalar optimization safety
- statement: `OptIR` is constructed exclusively from Verified MIR without re-inferring ownership or capability safety, maintains valid dominance, SSA, and `MemorySSA` def-use invariants, enforces fail-closed `Certainty.Proven` transformation contracts in `PassManager`, and preserves checked-arithmetic traps, deterministic `Drop` ordering, I/O, atomics, `volatile`, `black_box`, and secure zeroization across SCCP, GVN, CSE, SROA, and DCE (SPEC-70 AXS-OPT-001..047).
- source: SPEC-70 AXS-OPT-001..047; 0161 §17, §37; 0165 §1-16; tasks/0366 AOPT-20..65; tasks/0398 AOPTIR-20..75; tasks/0399 AOPT-70..110; tasks/0545-0547; tasks/0794-0797
- verify: tests/run/optir_ssa, tests/run/opt_passmgr, tests/run/opt_scalar, tests/conformance/p15/e15_1_optir_ssa
- since: T604
- check: OptIR/MemorySSA dump and differential conformance tests in tests/run/optir_ssa (T601), tests/run/opt_passmgr (T602), tests/run/opt_scalar (T603), and tests/conformance/p15/e15_1_optir_ssa (T604) verify SSA/MemorySSA construction, PassManager invalidation and `--verify-each` contracts, and observable equivalence across --interp, -O0, -O1, and -O2

### INV-PIPE-009 — Capability-driven alias analysis, escape analysis, and allocation promotion safety
- statement: `AliasInfo` derives `NoAlias` and `MustAlias` exclusively from verified ownership, capability (`view`/`mut_view`), allocation-root, field-layout, and range proofs while keeping raw-pointer and FFI aliasing conservative (`MayAlias`/`UnknownAlias`), and `EscapeInfo` promotes or eliminates allocations, closure environments, bounded collections, and return slots only when escape and address-observability (`address_of`, `@at`, `volatile`) barriers and deterministic `Drop` ordering are preserved (SPEC-71 AXS-ALIAS-001..006, AXS-ESC-001..017).
- source: SPEC-71 AXS-ALIAS-001..006, AXS-ESC-001..017; 0131 §86; 0162 §29; 0165 §17-20; 0226 §5-16; tasks/0366 AOPT-23..38, AOPT-59..60; tasks/0395 AALIAS-20..70; tasks/0397 AESCAPE-20..80; tasks/0548 AMEMOPT-20..85; tasks/0615 ACLOS-01..30
- verify: tests/run/opt_alias, tests/run/opt_escape, tests/conformance/p15/e15_2_alias_escape
- since: T608
- check: alias/escape dump and differential conformance tests in tests/run/opt_alias (T606), tests/run/opt_escape (T607), and tests/conformance/p15/e15_2_alias_escape (T608) verify capability NoAlias forwarding, DSE, Box/closure/buffer stack and register promotion, address-observability barriers, and observable agreement across --interp, -O0, -O1, and -O2

### INV-PIPE-010 — Canonical loop analysis, overflow-faithful SCEV, bounds-check elimination, and loop transformation safety
- statement: Natural loop discovery, `LoopSimplify`/`LCSSA` canonicalization, Scalar Evolution (`SCEV`), `RangeInfo`, Bounds-Check Elimination (`BCE`), `LICM`, strength reduction, loop peeling/unswitching/unrolling/versioning/fusion, and iterator pipeline fusion preserve checked vs wrapping overflow semantics, retain bounds checks whenever `InBounds` is not `Certainty.Proven`, block hoisting of trapping instructions out of potentially zero-trip loops, and preserve `Drop`, capability, `atomic`, `volatile`, async `await`, and FFI barriers (SPEC-72 AXS-LOOP-001..017, AXS-BCE-001..006).
- source: SPEC-72 AXS-LOOP-001..017, AXS-BCE-001..006; 0113 §122 AOPT-20; 0165 §21-30; tasks/0366 AOPT-35; tasks/0402 ALOOP-20..70, ABCE-20..27, ALICM-20..24; tasks/0416 ACOLLECT-44..47; tasks/0426 AITER-20..75; tasks/0549 ALOOP-20..90
- verify: tests/run/opt_bce, tests/run/opt_loops, tests/conformance/p15/e15_3_loops_bce
- since: T612
- check: loop/BCE dump and differential conformance tests in tests/run/opt_bce (T610), tests/run/opt_loops (T611), and tests/conformance/p15/e15_3_loops_bce (T612) verify SCEV overflow fidelity, proven BCE vs retained out-of-bounds panics, LICM hoisting and zero-trip trap safety, iterator pipeline fusion, and observable agreement across --interp, -O0, -O1, and -O2

### INV-PIPE-011 — Interprocedural inlining, SROA, specialization, devirtualization, and tail-call safety
- statement: Call-graph `SCC` summary propagation, ownership-aware copy/move propagation, Scalar Replacement of Aggregates (`SROA`), caller return-slot construction (`RVO`/`NRVO`), function and closure inlining (`@inline`, `@inline(always)`, `@inline(never)`), call-site/generic specialization, `dyn Trait` and function-pointer devirtualization, and tail-call optimization (`@tailcall`) strictly separate legality from `CostModel` profitability, bound recursive `SCC` expansion, retain dynamic dispatch when target identity is not `Certainty.Proven`, and preserve `Drop`, ownership, capability, `atomic`, `volatile`, address-observability, and external FFI/export ABI contracts (SPEC-73 AXS-INL-001..035).
- source: SPEC-73 AXS-INL-001..035; 0131 §28-29, §73-76, §86, §88 AFN-58; 0152 §73-75; 0165 §13-16; tasks/0366 AOPT-27..38, AOPT-60..62; tasks/0400 AIP-20..70; tasks/0401 AINLINE-20..36, ASPEC-20..35, ADEvirt-20..30, AABST-20..30; tasks/0551 AINLINE-20..95
- verify: tests/opt2, tests/run/opt_ipa_devirt, tests/conformance/p15/e15_4_inline_specialize_devirt
- since: T615
- check: dump and differential conformance tests in tests/opt2 (T064), tests/run/opt_ipa_devirt (T614), and tests/conformance/p15/e15_4_inline_specialize_devirt (T615) verify copy/move propagation, deep SROA, RVO/NRVO, bounded SCC inlining, constant/closure specialization, proven vs open-world devirtualization, O(1)-stack tail-recursion lowering, and observable agreement across --interp, -O0, -O1, and -O2

### INV-PIPE-012 — Whole-program LTO, section GC/ICF, and PGO profitability-only safety
- statement: Link-Time Optimization (`--lto`) and whole-program reachability (`WPO`) operate only within proven closed-world boundaries while preserving `@export`, dynamic-lookup, reflection, FFI, `@at`, `volatile`, and `atomic` roots and deduplicating generics without erasing observable function-pointer identity; the linker's mark-sweep section GC (`COMDAT`) and safe Identical Code Folding (`ICF`) consume explicit object section-graph contracts without inferring source ownership; and Profile-Guided Optimization (`--pgo-gen` / `--pgo-use`) treats profile data strictly as `Observed` profitability weights that never fabricate semantic/safety/alias/devirtualization proofs, never bypass `Verified MIR`, degrade gracefully on stale profiles, and produce deterministic byte-identical builds (SPEC-75 AXS-LTO-001..030, AXS-PGO-001..015).
- source: SPEC-75 AXS-LTO-001..030, AXS-PGO-001..015; tasks/0355 ALTO-20..58; tasks/0366 AOPT-20..65; tasks/0408 APGO-20..53; tasks/0409 ALTO-20..55; tasks/0410 ABINOPT-20..50; tasks/0580 AWPA-01..25; tasks/0581 APGO-20..44; tasks/0594 AWP-01..25; tasks/0595 ALAYOUT-01..25; tasks/0597 APROF-01..25
- verify: tests/run/opt_lto, tests/run/opt_pgo_gc, tests/conformance/p15/e15_6_lto_pgo_gc
- since: T623
- check: dump and differential conformance tests in tests/run/opt_lto (T621), tests/run/opt_pgo_gc (T622), and tests/conformance/p15/e15_6_lto_pgo_gc (T623) verify cross-module inlining/specialization/devirt, generic deduplication, COMDAT dead stripping, address-safe ICF, deterministic `--pgo-gen`/`--pgo-use` round-trips, stale-profile fallback, and observable agreement across --interp, -O0, -O2, --lto, and --pgo-use

### INV-PIPE-013 — Cross-profile semantic equivalence, 3D binary footprint, noise-free telemetry, and CI performance budget enforcement
- statement: All optimization profiles (`--interp`, `-O0`, `-O1`, `-O2`, `-Os`, `-Oz`, `--lto`, `--pgo-use`) preserve identical core language semantics without safe UB or monolithic runtime dependencies; `--time-passes` and `--size-report` emit machine-readable pass-timing and 3D binary footprint (`FileSize`, `MappedSize`, `WorkingSet`) telemetry without altering artifact bytes; and `tools/perf.py --check-budgets` validates correctness before accepting timings and enforces compile-time, runtime speedup, startup latency, and code-size budgets over `tools/bench` (SPEC-76 AXS-PERF-001..044).
- source: SPEC-76 AXS-PERF-001..044; 0074 ASEM-01..15; tasks/0355 ALTO-55..58; tasks/0366 AOPT-58; tasks/0408 APGO-39..42, APGO-48..53; tasks/0595 ALAYOUT-01..25; tasks/0706 §450.1-450.150
- verify: tests/run/perf_contract, tests/conformance/p15/e15_7_perf_contract, tools/perf.py
- since: T626
- check: telemetry, benchmark harness, and differential conformance tests in tests/run/perf_contract (T625) and tests/conformance/p15/e15_7_perf_contract (T626) verify `--time-passes`, `--size-report`, byte-identical reproducibility, differential equivalence across --interp, -O0, -O1, -O2, and -Oz, and `python tools/perf.py --check-budgets` exit 0

## 7. Oracle and agreement

### INV-ORACLE-001 — Semantics are explicit, not inherited from C
- statement: Integer overflow, division by zero, shifts, casts and (later) floating point behave as the spec defines (SPEC-03), implemented with explicit checked or unsigned arithmetic, never through C undefined or implementation-defined behaviour.
- source: axiom-c-stage0; tasks/0260 ABOOT-43; SPEC-03
- verify: tests/run/basic, tests/run/numeric
- since: T034
- check: run tests of the edge cases (min/max, overflow trap, division by zero) in both modes (tests/run/basic is delivered by T021, a dependency of T034)

### INV-ORACLE-002 — Native agrees with the oracle
- statement: Every run test enabled in both modes gives the same exit code and byte-identical stdout under the interpreter and natively.
- source: tasks/0260 ABOOT-77; 0263 §47; tasks/0262 §47
- verify: tests/diff
- since: T029
- check: the differential suite compares both modes for every test without `native-after`

### INV-ORACLE-003 — std runs under the oracle
- statement: Heap and OS operations reach the interpreter through the host intrinsics, so std and compiler-port tests run in both modes. Only direct FFI is native-only.
- source: ADR-0002; ROADMAP R8
- verify: tests/run/host
- since: T061c
- check: host-intrinsic run tests in interp and native mode

## 8. Frozen semantic model (full rules: SPEC-03, SPEC-10, SPEC-11, SPEC-12)

### INV-SEM-001 — Ownership, not a borrow checker
- statement: Values are moved or copied by their type's Copy classification. A use after move is a compile error. Surface code has no lifetimes and no references (`&`): access to a value without owning it goes through the `view` / `mut_view` capabilities.
- source: 0151 §1-3, §57; 0160; tasks/0360 §13; SPEC-02 AXS-GRM-053
- verify: tests/ui/own
- since: T121
- check: ui tests for use after move, partial move and Copy types

### INV-SEM-002 — Capability conflicts are compile errors
- statement: A `mut_view` that overlaps any other live view of the same region is rejected, and so is an overlap the compiler cannot prove absent. Validity of capabilities does not depend on the optimization level.
- source: 0151 §5-6 (ACAP-31); tasks/0360 §14-15; 0177
- verify: tests/ui/cap
- since: T125
- check: ui tests WRITE+WRITE, WRITE+READ and unknown overlap; run tests stay identical at -O0/-O1

### INV-SEM-003 — Deterministic drop
- statement: Owned values are dropped exactly once, at the end of their scope in reverse declaration order, never after being moved out. Conditional moves use drop flags. Drop never depends on a garbage collector or on reference counting.
- source: 0151 §1, §8; 0178; tasks/0262 §26-27; tasks/0260 ABOOT-50/51
- verify: tests/run/drop
- since: T127
- check: run tests observe drop order through output in both modes

### INV-SEM-004 — Definite initialisation
- statement: No local is read before it is definitely assigned on every path.
- source: 0160; tasks/0394
- verify: tests/ui/init
- since: T047
- check: ui tests for deferred initialisation on branches and loops

### INV-SEM-005 — No hidden runtime
- statement: A native executable contains only the startup stub, the program's code and the imports it uses. There is no garbage collector, no implicit allocator and no runtime library unless the program uses std features that need one.
- source: 0263; ROADMAP R6/R7; tasks/0360 ADIAG-89/90; tasks/0260 ABOOT-63/64
- verify: tests/link
- since: T027
- check: the first image imports exactly `KERNEL32.dll!ExitProcess` and contains no other code than startup and the program

### INV-SEM-006 — `unsafe` adds obligations, it does not switch checking off
- statement: Raw-pointer dereference, pointer arithmetic and calls to unsafe functions are errors outside `unsafe`. Inside `unsafe`, types, ownership of safe values, ABI and control flow are still checked.
- source: 0151 §24-25 (AUNSAFE-56/57); ROADMAP E13.1; T061a
- verify: tests/ui/ptr
- since: T061a
- check: ui tests produce `AX_UNSAFE_REQUIRED`; ownership errors still reported inside `unsafe`

### INV-SEM-007 — Index auto-deref through views vs raw-pointer indexing and store-drop rules
- statement: Indexing `base[i]` where `base` has type `view<X>` or `mut_view<X>` and `X` resolves (after one or more view levels) to `[N]T` or `[T]` implicitly dereferences `base` one level at a time (`a[i]` lowers in MIR to explicit `Deref` projections before `Index` consumed from Typed HIR / THIR facts, without rediscovering source semantics or determining physical storage or register allocation); reading requires `view` or `mut_view`, mutating (`a[i] = v`, `a[i] op= v`, `mut_view(a[i])`) requires every traversed view level to be `mut_view` (`AX_TYPE_ASSIGN_IMMUTABLE`), assigning through `mut_view` drops the old element value (`AXS-SEM-043`, `AXS-DROP-007`), and raw-pointer bases (`*const [N]T`, `*mut [N]T`, `*const T`, `*mut T`) are never auto-dereferenced for indexing (`AX_TYPE_CANNOT_INDEX`) while explicit `(*p)[i] = v` inside `unsafe` is a raw store that never drops the old value (SPEC-03 AXS-SEM-042/043/047, SPEC-12 AXS-DROP-007).
- source: ADR-0036 §1, §4; SPEC-03 AXS-SEM-042, AXS-SEM-043, AXS-SEM-047; SPEC-12 AXS-DROP-007; tasks/0539 §89 AMIR-83..90; REQ-CORE-3053..3060
- verify: tests/run/index_autoderef, tests/ui/index_autoderef, tests/conformance/p14/e14_5_index_autoderef
- since: T572
- check: execution, UI diagnostic, and conformance tests in tests/run/index_autoderef (T571), tests/ui/index_autoderef (T571), and tests/conformance/p14/e14_5_index_autoderef (T572) verify view/mut_view index auto-deref, evaluation order, bounds checks, old-element Drop on assignment, rejection of writes through immutable views (`AX_TYPE_ASSIGN_IMMUTABLE`), and rejection of raw-pointer indexing (`AX_TYPE_CANNOT_INDEX`)

## 9. Bootstrap scope

### INV-BOOT-001 — axiom0 implements exactly the self-host subset
- statement: axiom0 accepts the self-host subset of `spec/SPEC-00-bootstrap.md` and nothing more. Every other valid construct gets an `*_UNSUPPORTED_IN_BOOTSTRAP` diagnostic (AXD-013), never a crash and never a silent miscompile.
- source: ROADMAP R7; tasks/0260 ABOOT-42/43; ADR-0004 §2; ADR-0011 §3
- verify: tests/ui/parse, tests/ui/numeric
- since: T034
- check: ui tests for S1 forms (`async fn`, parser level) and floats (semantic level), plus the SPEC-00 list (tests/ui/parse is delivered by T011, a dependency of T034)

### INV-BOOT-002 — The bootstrap subset is Axiom
- statement: Every program accepted by axiom0 has the same meaning under axiomc. The self-host subset is not a separate language.
- source: tasks/0260 ABOOT-41/42/80
- verify: tests/selfhost/stage1
- since: T086
- check: axiomc1 passes the axiom0 suite with identical `--json` diagnostics and run results

### INV-BOOT-003 — No external assembler or linker in the production path
- statement: Building an Axiom program, and building axiomc from axiom0, never invokes an external assembler, linker or C compiler. gcc, ld and objdump are used only to build axiom0 and as test oracles.
- source: tasks/0260 ABOOT-74/75; 0263; 0172
- verify: tools/bootstrap.py
- since: T087
- check: the bootstrap chain completes with gcc/ld/as removed from PATH

### INV-BOOT-004 — axiom0 frozen after the fixed point
- statement: After T087 is accepted (local tag `axiom0-frozen`), commits touching `bootstrap/axiom0` are allowed only for tasks titled `AX0-FIX-<nn> …`.
- source: ROADMAP R3; ADR-0005 §15
- verify: .claude/skills/axiom-tasks/scripts/harness_check.py
- since: T087
- check: harness_check rejects other commits that touch `bootstrap/axiom0` once the tag exists (harness_check.py already exists and already implements the freeze check; T087 creates the tag that activates it)

## 10. Invariants stated in SPEC-01 / SPEC-02

### INV-LEX-001 — Lossless lexing
- statement: The BOM, whitespace, comments and token spans concatenated in order reproduce the input exactly (SPEC-01 AXS-LEX-110).
- source: SPEC-01 AXS-LEX-110
- verify: tests/lex
- since: T010
- check: golden token dumps plus a round-trip check over the lexer corpus

### INV-LEX-002 — Error tokens and diagnostics correspond
- statement: An `Error` token or `ERROR` flag appears if and only if a diagnostic is reported for it, and the diagnostic count is exactly as AXS-LEX-101 defines (SPEC-01 AXS-LEX-112).
- source: SPEC-01 AXS-LEX-101, AXS-LEX-112
- verify: tests/ui/lex
- since: T010
- check: SPEC-01 error cases E01–E23 report exactly the listed codes

### INV-GRM-001 — Parser recovery
- statement: The parser never stops at the first error and never crashes. It reports at most one diagnostic per erroneous construct and recovers deterministically (SPEC-02 AXS-GRM-100).
- source: SPEC-02 AXS-GRM-100
- verify: tests/ui/parse
- since: T011
- check: rejected-spelling cases R01–R15 and multi-error files

## 11. Concurrency, memory model, and async state machines (SPEC-30, SPEC-31, SPEC-32, SPEC-33)

### INV-CONC-001 — `Send` and `Share` are independent, zero-cost marker auto-traits
- statement: `Send` (cross-context ownership transfer) and `Share` (concurrent shared read access via `view<T>`) are tracked as independent semantic properties (`Send != Share`). They are structurally synthesized for composite types, require `unsafe impl` for positive manual overrides, allow safe `impl !Send`/`impl !Share` opt-outs, and are completely erased after semantic checking with zero runtime representation or overhead (SPEC-30 AXS-CONC-010..019).
- source: 0033; 0126 §5-§7; 0136 §101+; 0160 §27; tasks/0298; tasks/0482; SPEC-30 AXS-CONC-010..019
- verify: tests/ui/concurrency/send_share, tests/run/concurrency/send_share
- since: T089
- check: UI and execution tests in tests/ui/concurrency/send_share and tests/run/concurrency/send_share verify structural auto-derivation, `Send != Share` independence, `unsafe impl` requirement (`AX_CONC_SAFE_IMPL_MARKER`), negative impls, and zero runtime descriptor emission

### INV-CONC-002 — Spawn and escaping closures enforce move ownership and forbid non-static views
- statement: Closure `Send`/`Share` traits derive from execution-relevant captured fields. Unscoped `spawn` requires explicit `move` ownership transfer without implicit cloning of `!Copy` values and rejects any non-`'static` `view<T>` or `mut_view<T>` escape (`AX_CONC_ESCAPING_VIEW`, `AX_CONC_CAPTURE_NOT_SEND`), while `spawn_local` relaxes `Send` on the current OS thread without relaxing lifetime containment (SPEC-30 AXS-CONC-020..026).
- source: 0079; 0091; 0126 §18-§25; SPEC-30 AXS-CONC-020..026
- verify: tests/unit/sema/conc_capture, tests/ui/conc_capture
- since: T401
- check: unit and ui tests verify closure capture `Send`/`Share` inference, `move` capture invalidation, rejection of non-static views across `spawn`, and `spawn` vs `spawn_local` obligations

### INV-CONC-003 — Compile-time data-race freedom and conservative region disjointness
- statement: Safe Axiom code is statically free of data races on ordinary memory. Concurrent `READ`/`READ` requires `T: Share`, while unsynchronized `READ`/`WRITE` and `WRITE`/`WRITE` on overlapping regions are rejected (`AX_CONC_SHARED_MUT`). Place overlap analysis (`DISJOINT`, `CONTAINS`, `SAME`, `UNKNOWN`) never treats `UNKNOWN` as `DISJOINT`; only provably `DISJOINT` struct fields or slice partitions (`split_at_mut`) permit concurrent `mut_view` access inside a structured `scope`, and `unsafe` blocks do not disable concurrency checking once safe capabilities are re-established (SPEC-30 AXS-CONC-030..038).
- source: 0126 §49-§59; 0136 §28-§51; tasks/0488; tasks/0685; SPEC-30 AXS-CONC-030..038
- verify: tests/unit/sema/conc_race, tests/ui/conc_race
- since: T402
- check: unit and ui tests verify `READ`/`WRITE` and `WRITE`/`WRITE` rejection, `UNKNOWN != DISJOINT` conservatism, disjoint field/slice `mut_view` acceptance, `static mut` restriction (`AX_CONC_UNSYNC_STATIC`), and guard escape rejection (`AX_CONC_GUARD_ESCAPE`)

### INV-CONC-004 — Happens-Before synchronization barriers are preserved by MIR optimization
- statement: Every MIR/OptIR optimization pass preserves the `Happens-Before` partial order established by `spawn`, `join`, lock `acquire`/`release`, channel `send`/`recv`, `fence`, and `Release`/`Acquire`/`AcqRel`/`SeqCst` atomic operations. No memory read or write to potentially shared state may be hoisted above an `Acquire` boundary, sunk below a `Release` boundary, folded to a stale value across a synchronization edge, or introduced speculatively (SPEC-30 AXS-CONC-040..047).
- source: 0105; 0126 §39; 0136 §79; tasks/0685; SPEC-30 AXS-CONC-040..047; SPEC-70 AXS-OPT-021
- verify: tests/unit/opt/conc_hb, tests/conformance/concurrency
- since: T403
- check: optimizer unit tests (T403) and concurrency conformance tests (delivered by T404) verify that CSE/GVN/LICM/DSE do not reorder, fold, or eliminate shared memory operations across synchronization barriers and that concurrency verification is deterministic

### INV-CONC-005 — `Atomic<T>` width/alignment/ordering legality and MIR optimizer preservation
- statement: `Atomic<T>` is restricted to naturally aligned 1-, 2-, 4-, and 8-byte integers, `bool`, and raw pointers (`AX_CONC_INVALID_ATOMIC_TYPE`, `AX_CONC_INVALID_ATOMIC_ALIGNMENT`), forbids `mut_view<T>` into its inner storage (`AX_CONC_ATOMIC_MUT_VIEW`), requires explicit `Ordering` validated against the operation/fence/CAS legality matrix (`AX_CONC_INVALID_ATOMIC_ORDERING`), and lowers to dedicated `MIR_STMT_ATOMIC` statements that `const_fold`, `dce`, and all MIR optimization passes never fold, coalesce, reorder across acquire/release barriers, weaken, or eliminate (SPEC-31 AXS-ATM-001..034, AXS-ATM-060).
- source: 0092 §1-14; 0128 §1-35, §58; 0161 §30; 0208 §1-39; SPEC-04 AXS-EXT-043; SPEC-31 AXS-ATM-001..034, AXS-ATM-060
- verify: tests/mir/atomics, tests/ui/concurrency/atomics
- since: T406
- check: MIR dump and UI diagnostic tests in tests/mir/atomics and tests/ui/concurrency/atomics verify `Atomic<T>` type/alignment/ordering validation, rejection of `mut_view` inner borrows, and preservation of `MIR_STMT_ATOMIC` across `const_fold` and `dce`

### INV-CONC-006 — LIR atomic preservation and x86-64 TSO instruction selection / byte-exact encoding
- statement: `MIR_STMT_ATOMIC` lowers to dedicated `LIR_INST_ATOMIC_*`, `LIR_INST_FENCE`, and `LIR_INST_PAUSE` nodes preserved up to x86-64 instruction selection, where `SeqCst` stores emit `XCHG`, RMW `fetch_add`/`fetch_sub` emit `LOCK XADD`, bitwise RMW and CAS emit `LOCK CMPXCHG`, `fence(SeqCst)` emits `MFENCE`, `fence(Acquire|Release|AcqRel)` and `compiler_fence` emit compiler scheduling barriers (`0` machine bytes), and `spin_loop_hint` emits `PAUSE` (`F3 90`) across 8-, 16-, 32-, and 64-bit widths (SPEC-31 AXS-ATM-040..047).
- source: 0092 §15-17; 0162 §30 ALIR-23; tasks/0328 §7; tasks/0515 §12; SPEC-04 AXS-EXT-051; SPEC-31 AXS-ATM-040..047
- verify: tests/lir/atomics, tests/encode/atomics, tests/run/concurrency/atomics_native
- since: T407
- check: LIR dump, machine-code byte encoding (`F0` `LOCK`, `0F C0`/`0F C1` `XADD`, `0F B0`/`0F B1` `CMPXCHG`, `86`/`87` `XCHG`, `0F AE F0` `MFENCE`, `F3 90` `PAUSE`), and native execution tests verify x86-64 atomic codegen across all widths and orderings

### INV-CONC-007 — Oracle atomic modification-order & vector-clock model agrees with native litmus conformance
- statement: The MIR interpreter oracle models per-location modification orders, release/acquire vector clocks, release sequences across RMW chains, `SeqCst` total ordering, deterministic spurious failures on `compare_exchange_weak`, and `AX_UNSAFE_INTERP_UB` detection on unsynchronized ordinary/atomic races, agreeing with native x86-64 execution across the `E11.2` litmus conformance suite (`LITMUS-MP`, `LITMUS-MP-FENCE`, `LITMUS-SB`, `LITMUS-LB`, `LITMUS-RMW`, `LITMUS-CAS-ABA`) (SPEC-31 AXS-ATM-050..066).
- source: 0092 §18-28; 0128 §19-33, §59; tasks/0515 §6, §11-12; SPEC-31 AXS-ATM-050..066
- verify: tests/run/concurrency/atomics_oracle, tests/conformance/p11/e11_2_atomics
- since: T408
- check: oracle memory-model tests (T408) and end-to-end litmus conformance tests (delivered by T409) verify message passing, store/load buffering, lossless RMW counters, weak/strong CAS retry loops, ABA tag protection, and differential agreement between `--interp` and native x86-64 binaries

### INV-CONC-008 — `async`/`await` and `Future<T>` are zero-overhead cold state machines without `Pin<T>`
- statement: `async fn` and `async { ... }` lower to cold, inline compiler-generated `Coroutine` state machines implementing `std.future.Future` (`fn poll(self: mut_view<Self>, cx: mut_view<Context>) -> Poll<Self.Output>`) with zero mandatory heap allocation, no `Pin<T>` wrapper in Core v1.0, and deterministic `std.future.block_on` single-thread execution; `.await` is rejected outside async contexts (`AX_ASYNC_AWAIT_OUTSIDE_ASYNC`), inside `Drop.drop` (`AX_ASYNC_AWAIT_IN_DROP`), and on non-`Future` operands (`AX_ASYNC_NOT_A_FUTURE`), while unboxed recursive `async fn` cycles (`AX_ASYNC_RECURSIVE_FUTURE`) and `async extern` ABIs (`AX_ASYNC_EXTERN_ABI`) are rejected at compile time (SPEC-33 AXS-ASY-001..027).
- source: 0093; 0127; 0135; 0159 §8; 0201; 0202; 0248; tasks/0275; tasks/0297; tasks/0619; SPEC-33 AXS-ASY-001..027
- verify: tests/run/async/block_on, tests/ui/async/syntax_type
- since: T416
- check: execution and UI diagnostic tests verify `Poll`/`Waker`/`Context`/`Future` lang items, cold-future semantics, `std.future.block_on`, and rejection of `.await` outside async or in `Drop`, non-`Future` `.await`, recursive `async fn`, and `async extern` ABI

### INV-CONC-009 — Live-across-await analysis forbids views and sync guards across `.await` and derives `Future: Send` strictly from live state
- statement: Pre-lowering MIR dataflow computes `LiveAcross(s) = Gen(s) ∪ (LiveIn(bb_resume(s)) \ Def(bb_resume(s)))` after pre-suspension drop elaboration; any `view<T>`, `mut_view<T>`, or view-containing composite in `LiveAcross(s)` is unconditionally rejected (`AX_ASYNC_VIEW_ACROSS_AWAIT`), synchronous lock guards (`MutexGuard`, `RwLockReadGuard`, `RwLockWriteGuard`) in `LiveAcross(s)` are rejected (`AX_ASYNC_GUARD_ACROSS_AWAIT`), and `Future: Send` is derived strictly from parameters plus `LiveAcross(s)` locals and awaited sub-futures (`AX_ASYNC_FUTURE_NOT_SEND`) while every state-machine `Future` is `!Share` (SPEC-33 AXS-ASY-030..037).
- source: 0093 §3; 0127 §11-§14, §26; 0135 §3-§11, §24, §29, §33; 0202 §5-§12; 0248 §6-§15; tasks/0275 §8-§9; tasks/0297 §6-§9; SPEC-33 AXS-ASY-030..037
- verify: tests/ui/async/live_across_await
- since: T417
- check: UI and unit tests verify that `view`/`mut_view` and `!Send` temporaries confined within a single poll step or dropped before `.await` are accepted, while views, sync guards, or `!Send` values live across `.await` are rejected with exact spans

### INV-CONC-010 — MIR async state-machine lowering, per-state cancellation `Drop` glue, and oracle lifecycle agreement
- statement: `compiler/mir/async_lower.ax` transforms each `async` body into a `__AsyncState_f` struct (`state_tag: u32` with `0 = Unstarted`, `1..K = Suspended(s)`, `0xFFFF_FFFE = Complete`, `0xFFFF_FFFF = Poisoned`), reconstructs self-views from the `self: mut_view<__AsyncState_f>` argument on every resume, generates state-driven `Drop` glue that drops the active sub-future before live locals in reverse declaration order when cancelled at `Suspended(s)`, and preserves byte-exact equivalence between `--interp` (including `POLL`/`SUSPEND`/`WAKE`/`RESUME`/`COMPLETE`/`CANCEL_DROP` lifecycle traces) and native x86-64 execution (SPEC-33 AXS-ASY-040..052).
- source: 0093 §7; 0127 §16-§22, §36; 0135 §7, §14-§21, §34-§38; 0202 §6-§11; 0248 §16-§18; tasks/0275 §6-§13; tasks/0297 §10-§11; tasks/0619 §5-§11; SPEC-33 AXS-ASY-040..052
- verify: tests/mir/async/state_machine, tests/run/async/cancellation_drop
- since: T418
- check: MIR state-machine dump tests (`T088`/`T418`), cancellation drop-order tests (`T418`), and E11.4 conformance tests (`T419`) verify state transitions, reverse-order cancellation drop glue, panic/completed re-poll rejection (`AX_ASYNC_POLL_AFTER_COMPLETE`), and oracle vs native x86-64 agreement

## 12. Scalar integer model, 128-bit arithmetic, and multi-width promotion (SPEC-40)

### INV-INT-001 — 128-bit scalar integers (`i128`, `u128`) are 16-byte values lowered to LIR register pairs `(lo, hi)` with oracle-native agreement
- statement: `i128` and `u128` are first-class 16-byte, 16-byte-aligned scalar integer types (`TypeKind.Int128`, `ConstValue.Int128`) with exact two's-complement limb representation `(lo: u64, hi: u64)` in MIR and the MIR interpreter, lowered in LIR to a pair of 64-bit GPRs `(lo: Gpr, hi: Gpr)` with a deterministic Win64 16-byte calling convention contract and x86-64 multi-word instruction selection (`ADD`/`ADC`, `SUB`/`SBB`, `MUL`/`IMUL`, `udiv128`/`sdiv128`, `SHLD`/`SHRD`, `BSWAP`, `LZCNT`/`TZCNT`/`POPCNT`) that matches the MIR interpreter bit-for-bit (SPEC-40 AXS-INT-001..012).
- source: 0157; 0175; 0245; tasks/0327 §84.1, §84.10-16; SPEC-04 AXS-EXT-020, AXS-EXT-024, AXS-EXT-050; SPEC-40 AXS-INT-001..012
- verify: tests/run/numeric
- since: T453
- check: 128-bit integer tests in tests/run/numeric (T451, T453) verify `i128`/`u128` size/align 16, literal bounds (`AX_LEX_INT_OVERFLOW`, `AX_TYPE_LITERAL_OUT_OF_RANGE`), MIR interpreter evaluation, LIR register-pair lowering, Win64 ABI calls, and x86-64 native parity

### INV-INT-002 — Five explicit integer overflow families and distinct conversion classes (`COERCION`, `CAST`, `TRY_CAST`, `BITCAST`)
- statement: All twelve integer types (`i8..i128`, `u8..u128`, `isize`, `usize`) maintain five explicit overflow families — default checked operators (`+`, `-`, `*`, `/`, `%`, `-`, `<<`, `>>`), `wrapping_*`, `saturating_*` (lowered to `MirBinOp.SatAdd`/`SatSub`/`SatMul`), `checked_*` (`Option<Self>`), and `overflowing_*` (`(Self, bool)`) — without SIMD or optimizer weakening (`ANUM-36`), and partition conversions into lossless `COERCION`, explicit primitive `CAST` (`as`), trait-based `TRY_CAST` (`From`/`Into`/`TryFrom`/`TryInto` with `TryFromIntError`), and bit-preserving `BITCAST` (`to_*_bytes`/`from_*_bytes`) (SPEC-40 AXS-INT-013, AXS-INT-020..044).
- source: tasks/0327 §84.10-11; tasks/0431 §172.1-14; SPEC-04 AXS-EXT-042; SPEC-40 AXS-INT-013, AXS-INT-020..044
- verify: tests/run/numeric
- since: T454
- check: execution and UI tests in tests/run/numeric (T452, T454) verify default checked traps, `wrapping_*`, `saturating_*`, `checked_*`, `overflowing_*`, bit/endian helpers, and `From`/`TryFrom` vs `as`/bitcast across all 12 integer widths

### INV-INT-003 — Multi-width integer expression promotion lowers to explicit `MIR_RVALUE_CAST` (`IntToInt`) before MIR verification
- statement: Multi-width integer arithmetic, bitwise, comparison, and array-index expressions promote narrower integer operands deterministically along the integer promotion sub-lattice (`SPEC-40` AXS-INT-050..053, `REQ-OWNER-007` Pattern D) in `typeck` and `compiler/mir/builder.ax` by inserting explicit `MIR_RVALUE_CAST` (`MIR_CAST_INT_TO_INT`) temporaries prior to every binary operation and index projection; `compiler/verify/verifier.ax` enforces homogeneous operand types on all MIR binary rvalues, while standalone variable bindings, assignments, return statements, call arguments, and standalone same-width signed/unsigned operations continue to reject mismatched types with `AX_TYPE_MISMATCH` (SPEC-40 AXS-INT-050..054).
- source: OWNER.md REQ-OWNER-007; tasks/0431 §172.1-14; SPEC-40 AXS-INT-050..054
- verify: tests/run/numeric, tests/ui/typeck
- since: T455
- check: execution tests in tests/run/numeric (T455, Pattern D) and UI tests in tests/ui/typeck verify deterministic multi-width integer promotion in expressions, explicit `MIR_RVALUE_CAST` emission, homogeneous MIR verifier enforcement, and `AX_TYPE_MISMATCH` preservation on standalone bindings and same-width signed/unsigned mixing

## 13. Floating-point semantics, mixed-type promotion lattice, and deterministic math (SPEC-41)

### INV-FLT-001 — Complete 12-primitive promotion lattice (`join_num`) and contextual literal adaptation lower to explicit `MIR_RVALUE_CAST`
- statement: The typechecker (`compiler/types/typeck.ax`) and MIR builder (`compiler/mir/builder.ax`) evaluate mixed numeric expressions over all scalar numeric types (`i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`) plus `IntVar` and `FloatVar` using the partial join operator `join_num` (`SPEC-41` AXS-FLT-030..037, `REQ-OWNER-007` Patterns A, B, C, D): in binary arithmetic and comparison expressions, `f32` widens to `f64` (`FloatConvert`), concrete integer operands (`i8..i128`, `u8..u128`, `isize`, `usize`) and unsuffixed `IntVar` literals promote to a floating-point peer `F` (`join_num(F, Int) = F` via `MIR_CAST_INT_TO_FLOAT`), narrower integers widen along `join_int` (`MIR_CAST_INT_TO_INT`), array indices convert to `usize` (`MIR_CAST_INT_TO_INT`), and unconstrained `FloatVar` defaults to `f64`, while standalone variable/return/argument type mismatches (`let x: f64 = n_i32`, `let n: i32 = x_f64`, `let x: f64 = w_f32`) and standalone same-width signed/unsigned integer operations (`u32_v + i32_v`) are rejected with `AX_TYPE_MISMATCH` (`AXS-FLT-035`), and every implicit promotion is materialized as an explicit `MIR_RVALUE_CAST` (`IntToInt`, `IntToFloat`, `FloatConvert`) so `compiler/verify/verifier.ax` observes strictly homogeneous binary MIR operands.
- source: OWNER.md REQ-OWNER-007; tasks/0331; tasks/0338; tasks/0345; SPEC-40 AXS-INT-050..054; SPEC-41 AXS-FLT-030..037
- verify: tests/typeck/float, tests/mir/float_mixed
- since: T457
- check: typeck and MIR dump tests in tests/typeck/float (T457), tests/mir/float_mixed (T457), and execution tests in tests/run/numeric/mixed_expr_matrix (T462 Patterns A/B/C/D) verify `f32 -> f64` widening, concrete integer and `IntVar -> Float` promotion (`MIR_CAST_INT_TO_FLOAT`), explicit `MIR_RVALUE_CAST` generation, and `AX_TYPE_MISMATCH` on standalone bindings/narrowing or same-width signed/unsigned mixing

### INV-FLT-002 — Strict IEEE-754 binary32/binary64 arithmetic, canonical quiet `NaN`, signed zero (`-0.0`), and saturating `FloatToInt` casts
- statement: Scalar `f32` and `f64` operations obey IEEE-754-2019 binary32 and binary64 with `roundTiesToEven`, canonical quiet `NaN` (`0x7FC0_0000u32` / `0x7FF8_0000_0000_0000u64`), signed zero (`+0.0` vs `-0.0`) preservation, non-trapping division by zero (`±inf` / `NaN`), partial `UCOMISS`/`UCOMISD` comparisons (`NaN != NaN` is `true`, all other relational predicates on `NaN` are `false`, `-0.0 == +0.0` is `true`), no implicit `-ffast-math` reassociation or silent FMA contraction, and saturating `FloatToInt` `as` casts (`NaN -> 0`, clamped to `[T.MIN, T.MAX]`, never undefined behaviour or raw `0x8000...` hardware sentinel) with bit-for-bit agreement between `--interp` and native x86-64 (SPEC-41 AXS-FLT-001..025).
- source: tasks/0331; tasks/0345; tasks/0469; CATALOG.md REQ-SIMD-108..110, REQ-SIMD-163, REQ-SIMD-186..188; SPEC-41 AXS-FLT-001..025
- verify: tests/mir/float_interp, tests/opt/float_strict
- since: T458
- check: float oracle and strict-FP optimizer tests in tests/mir/float_interp (T458), tests/opt/float_strict (T458), and E12.2 conformance tests in tests/conformance/p12/e12_2_floating_point (T462) verify IEEE-754 arithmetic, signed zero, `NaN` propagation, partial and total comparisons, saturating `FloatToInt` casts, and differential oracle vs native parity

### INV-FLT-003 — LIR `Xmm` register class, Windows x64 ABI `XMM0`–`XMM3` parameter slots, `XMM6`–`XMM15` callee-saved preservation, and SSE2 unordered comparison lowering
- statement: `compiler/lir/` and `compiler/target/x64/` lower `f32` and `f64` through `RegClass.Xmm` (`XMM0`–`XMM15`), pass floating-point arguments in positional slots `0..3` via `XMM0`–`XMM3` (mirroring to `RCX`/`RDX`/`R8`/`R9` on variadic `extern "C"` calls) and return scalars in `XMM0`, save and restore full 128-bit non-volatile `XMM6`–`XMM15` registers in `FrameLayout` whenever clobbered, deduplicate `.rdata` float constants by exact bit pattern (`+0.0` distinct from `-0.0`), and lower `UCOMISS`/`UCOMISD` `==`/`!=` with explicit parity (`PF`) checks (`SETE+SETNP+AND` for `==`, `SETNE+SETP+OR` for `!=`) (SPEC-41 AXS-FLT-040..044).
- source: 0162; 0179; 0181; 0182; SPEC-04 AXS-EXT-050, AXS-EXT-052; SPEC-41 AXS-FLT-040..044
- verify: tests/lir/float, tests/encode/sse2_scalar, tests/abi/win64_float
- since: T459
- check: LIR, SSE2 encoding, and Win64 ABI float tests in tests/lir/float (T459), tests/encode/sse2_scalar (T459), tests/abi/win64_float (T459), and E12.2 conformance tests in tests/conformance/p12/e12_2_floating_point (T462) verify mixed integer/float Win64 ABI calls (>4 parameters, variadic FFI), `XMM6`–`XMM15` preservation across calls, `.rdata` `-0.0` vs `+0.0` constant pooling, and `UCOMISS`/`UCOMISD` `NaN` comparison flags

### INV-FLT-004 — Pure-Axiom deterministic `std.text.fmt.float` round-trip formatting/parsing and `std.math` transcendental accuracy without OS `libm`
- statement: `std.text.fmt.float` (`T460`) and `std.math` (`T461`) are implemented in 100% pure Axiom without calling host C `snprintf`/`strtod` or OS `libm`, guaranteeing exact round-trip formatting (`parse(format(x)).unwrap().to_bits() == x.to_bits()`), canonical `"NaN"`/`"inf"`/`"-inf"`/`"-0.0"` formatting, exact `roundTiesToEven` decimal parsing, exact ($\le 0.5\text{ ULP}$) elementary operations (`sqrt`, `fma`, `floor`, `ceil`, `trunc`, `round`, `round_ties_even`, `frexp`, `ldexp`), and bounded ($\le 1.0\text{ ULP}$ / $\le 1.5\text{ ULP}$) minimax + Cody-Waite/Payne-Hanek transcendentals with bit-identical results across all platforms and compiler stages (SPEC-41 AXS-FLT-050..064).
- source: tasks/0427; tasks/0469; CATALOG.md REQ-SIMD-110, REQ-SIMD-163, REQ-SIMD-186..189; SPEC-41 AXS-FLT-050..064
- verify: tests/std/float_fmt, tests/std/math, tests/conformance/p12/e12_2_floating_point
- since: T462
- check: float formatting/parsing tests in tests/std/float_fmt (T460), `std.math` accuracy/special-value tests in tests/std/math (T461), and E12.2 conformance tests in tests/conformance/p12/e12_2_floating_point (T462) verify round-trip identity, special string formatting, ULP bounds, and IEEE-754 special-value identities

## 14. Unsafe boundary, pointer provenance, FFI/ABI, and address introspection (SPEC-50)

### INV-UNS-001 — Narrow unsafe boundary and immediate resumption of safe capability verification
- statement: `unsafe { ... }` blocks, `unsafe fn` bodies, and `unsafe trait` / `unsafe impl` declarations authorize only the seven primitive unsafe operation categories (`SPEC-50` AXS-UNS-002..004) without disabling typechecking, definite initialization, move/drop tracking, or safe capability conflict checking (`AX_UNSAFE_REQUIRED`, `AX_UNSAFE_TRAIT_IMPL`, `AX_UNSAFE_UNNECESSARY_IMPL`), and any `view<T>` / `mut_view<T>` or slice view synthesized from a raw pointer via `MakeView` / `MakeMutView` (`view.from_raw`, `mut_view.from_raw`, `slice.from_raw_parts`, `slice.from_raw_parts_mut`) immediately re-enters full compile-time capability and lifetime verification (`AX_CAP_CONFLICT_MUT`, `AX_CAP_OUTLIVES_OWNER`, `AX_CAP_CONTAINER_RELOC`) (SPEC-50 AXS-UNS-001..007).
- source: 0071 §1-13, §24; tasks/0282; tasks/0339; tasks/0395; SPEC-11; SPEC-50 AXS-UNS-001..007
- verify: tests/ui/unsafe, tests/run/unsafe
- since: T501
- check: UI and execution tests in tests/ui/unsafe and tests/run/unsafe verify `AX_UNSAFE_REQUIRED`, `AX_UNSAFE_TRAIT_IMPL`, `AX_UNSAFE_UNNECESSARY_IMPL`, `MakeView`/`MakeMutView` lowering, and preservation of move/init/capability checks inside and after `unsafe` blocks

### INV-UNS-002 — Strict pointer provenance and deterministic `--interp` UB detection (`UB-01..UB-12`)
- statement: Raw pointers (`*const T`, `*mut T`) carry strict allocation provenance `(AllocId, Bounds, Perm, AddrSpace)` preserved across pointer arithmetic (`offset`, `add`, `sub`, `wrapping_offset`, `byte_add`, `byte_sub`) and `with_addr` (`SPEC-50` AXS-UNS-010..014); integer-to-pointer casts (`addr as *const T` / `ptr.from_exposed_addr`) never guess or synthesize arbitrary stack/heap provenance, and the MIR interpreter (`--interp`) deterministically traps every violation in the closed `UB-01..UB-12` taxonomy (null/dangling/out-of-bounds/misaligned/uninitialized/invalid-scalar/read-only-store/provenance-forgery/capability-conflict/overlapping-copy/invalid-fn-ptr/ffi-abi mismatch) with `AX_UNSAFE_INTERP_UB` and exit code `125` (SPEC-50 AXS-UNS-010..016).
- source: 0044 §10-16; 0071 §8-21, §25; tasks/0282; tasks/0339; SPEC-03 AXS-SEM-092; SPEC-50 AXS-UNS-010..016
- verify: tests/run/unsafe/ub_interp, tests/unit/mir/provenance
- since: T502
- check: oracle UB tests in tests/run/unsafe/ub_interp and provenance unit tests in tests/unit/mir/provenance verify deterministic `AX_UNSAFE_INTERP_UB` (exit 125) across `UB-01..UB-12` and strict provenance preservation across pointer arithmetic and `with_addr`

### INV-UNS-003 — Explicit `@repr(C)` / `@repr(transparent)` / `@abi(stable)` layout, Win64 `1..24`-byte struct ABI, and external C DLL FFI parity
- statement: Internal Axiom types have no implicit C layout guarantee unless annotated with `@repr(C)`, `@repr(transparent)` (`AX_FFI_INVALID_TRANSPARENT`), or `@abi(stable)` (`SPEC-50` AXS-UNS-030..031); `extern "C"` / `"system"` declarations validate FFI-safe types (`AX_FFI_BAD_TYPE`, `AX_FFI_UNKNOWN_ABI`, `AX_FFI_OPAQUE_BY_VALUE`, `AX_FFI_GENERIC_EXPORT`, `AX_FFI_CAPTURING_CLOSURE_CALLBACK`, `AX_FFI_VARIADIC_NOT_EXTERN_C`), classify Win64 struct values of sizes `1, 2, 4, 8` into `RCX`/`RDX`/`R8`/`R9`/`RAX` and sizes `3, 5..7, 9..24` (including `3, 12, 16, 24`) by hidden pointer in caller-allocated 16-byte-aligned stack memory (`AXS-UNS-035`), and pass the external `gcc -shared` C DLL interop oracle (`ADR-0034 §8 / OI-12`) (SPEC-50 AXS-UNS-030..036).
- source: 0104; 0138; 0181; tasks/0367; tasks/0413; ADR-0002 §4; ADR-0034 §8; SPEC-50 AXS-UNS-030..036
- verify: tests/abi/win64_struct, tests/ffi/c_dll, tests/ui/ffi
- since: T503
- check: Win64 struct ABI tests in tests/abi/win64_struct (sizes 1, 2, 3, 4, 8, 12, 16, 24), external C DLL tests in tests/ffi/c_dll (compiled with `gcc -shared`), and UI tests in tests/ui/ffi verify C layout, calling convention, callbacks, and FFI diagnostics

### INV-UNS-004 — `REQ-OWNER-008` address introspection (`fn_addr`, `static_addr`, `address_of`, `f as usize`) and `@addr` / `@at` placement round-trip
- statement: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) -> *const T`, `address_of_mut(v) -> *mut T`, `addr_of(v) -> usize`, and `f as usize` query symbol and place addresses without moving or copying the operand (`AX_TYPE_NOT_A_PLACE` on temporaries), while `@addr(<expr>)` and `@at(<expr>)` place `static`, local `let`, and `fn` items at constant or runtime-computed addresses (validating alignment via `AX_UNSAFE_MISALIGNED_AT`, fixed layout via `AX_UNSAFE_INVALID_AT_LAYOUT`, and hosted-profile gating via `AX_UNSAFE_AT_HOSTED`) and satisfy the round-trip identities (`fn_addr(isr) == 0x2000_0000usize`, `let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`, `address_of(local_reg) as usize == addr`) across `--interp` and native x86-64 (SPEC-50 AXS-UNS-020..025).
- source: OWNER.md REQ-OWNER-008; ADR-0001; 0044 §3-9; 0071 §15; tasks/0339; SPEC-50 AXS-UNS-020..025
- verify: tests/run/unsafe/addr_introspect, tests/ui/unsafe/addr
- since: T504
- check: execution and UI tests in tests/run/unsafe/addr_introspect and tests/ui/unsafe/addr verify `fn_addr`, `static_addr`, `address_of(v) as usize`, `f as usize`, `@addr`/`@at` on `static`/`let`/`fn`, dynamic `base + 0x100` offset placement, and alignment/place diagnostics

### INV-UNS-005 — End-to-end E13.1 unsafe, UB, provenance, FFI/ABI, and address-introspection conformance
- statement: The E13.1 conformance suite verifies the complete `SPEC-50` contract across the unsafe boundary, raw pointer strict provenance, `--interp` UB detection (`UB-01..UB-12`), `@repr(C)` / `@repr(transparent)` / `@abi(stable)` FFI interop with an external C DLL (`ADR-0034 §8`), and `REQ-OWNER-008` address introspection and fixed-address placement (`fn_addr`, `static_addr`, `address_of`, `@addr`/`@at`) in both `--interp` and native x86-64 execution (SPEC-50 AXS-UNS-001..053).
- source: SPEC-50 AXS-UNS-001..053; OWNER.md REQ-OWNER-008; ADR-0001; ADR-0034 §8
- verify: tests/conformance/p13/e13_1_unsafe_ffi
- since: T505
- check: end-to-end conformance suite in tests/conformance/p13/e13_1_unsafe_ffi (delivered by T505) exercises `UNS-T01..T15`, `--interp` UB exit 125 verdicts, external C DLL calls and callbacks, and `REQ-OWNER-008` round-trip address identities

## 15. Portable SIMD vectors, masks, masked memory safety, data-oriented tensor/matrix views, SIMD backend lowering, and CPU feature multiversioning (SPEC-42, SPEC-43, SPEC-44)

### INV-SIMD-001 — First-class `Vector<T, N>` and `Mask<N>` type system, alignment layout, diagnostic validation, and MIR SIMD rvalue verification
- statement: `compiler/types/` and `compiler/mir/` represent portable SIMD vectors (`TypeKind.Vector { elem, lanes }`) and lane masks (`TypeKind.Mask { lanes }`) as `Copy + Send + Share` value types for `elem in {i8, i16, i32, i64, u8, u16, u32, u64, isize, usize, f32, f64}` and `lanes in {2, 4, 8, 16, 32, 64}`, enforce natural power-of-two alignment capped at 32 bytes (`align_of<Vector<T, N>>() == min(N * size_of<T>(), 32)` and `align_of<Mask<N>>() == min(N, 16)`), reject invalid element types, lane counts, constant lane indices, shuffle selectors, and mismatched bitcasts (`AX_SIMD_INVALID_ELEMENT`, `AX_SIMD_INVALID_LANES`, `AX_SIMD_LANE_OUT_OF_RANGE`, `AX_SIMD_SHUFFLE_OUT_OF_RANGE`, `AX_SIMD_BITCAST_SIZE_MISMATCH`), and verify `MIR_RVALUE_VECTOR_OP`, `MIR_RVALUE_SPLAT`, `MIR_RVALUE_EXTRACT`, `MIR_RVALUE_INSERT`, `MIR_RVALUE_SHUFFLE`, and `MIR_RVALUE_REDUCE` in `compiler/verify/verifier.ax` (SPEC-42 AXS-SIMD-001..025, AXS-SIMD-033, AXS-SIMD-060).
- source: 0095; tasks/0341; tasks/0344; tasks/0347; CATALOG.md REQ-SIMD-001..008, REQ-SIMD-086..090, REQ-SIMD-166..168; SPEC-42 AXS-SIMD-001..025, AXS-SIMD-033, AXS-SIMD-060
- verify: tests/typeck/simd, tests/mir/simd
- since: T464
- check: typechecker and MIR SIMD tests in tests/typeck/simd and tests/mir/simd (delivered by T464) verify `Vector<T, N>` / `Mask<N>` layout, `AX_SIMD_*` diagnostics, and MIR verifier rules for all SIMD rvalue variants

### INV-SIMD-002 — Bit-exact MIR interpreter (`--interp`) and compile-time `const` evaluator for `Vector<T, N>` and `Mask<N>`
- statement: `compiler/interp/` and `compiler/opt/const_fold.ax` evaluate `Vector<T, N>` and `Mask<N>` across all lane operations, shuffles, reductions, casts/bitcasts, and masked memory intrinsics in both `--interp` and `const` items, enforce inactive-lane fault suppression on `load_masked`, `store_masked`, `gather`, and `scatter` (`mask.test(i) == false` performs zero memory/bounds touches), trap out-of-bounds active lanes deterministically, and execute floating-point `reduce_add_ordered` strictly left-to-right and `reduce_add` / `reduce_mul` in canonical pairwise binary-tree halving order without host-dependent associative reordering (SPEC-42 AXS-SIMD-007, AXS-SIMD-030..033, AXS-SIMD-040..042).
- source: 0095; tasks/0341; tasks/0344; tasks/0347; tasks/0403; CATALOG.md REQ-SIMD-088..092, REQ-SIMD-171; SPEC-42 AXS-SIMD-007, AXS-SIMD-030..033, AXS-SIMD-040..042
- verify: tests/mir/simd_interp, tests/opt/simd_const
- since: T465
- check: SIMD oracle and const-folding tests in tests/mir/simd_interp and tests/opt/simd_const (delivered by T465) verify bit-exact lane execution, ordered and pairwise binary-tree float reductions, inactive-lane fault suppression on masked/gather/scatter accesses, and compile-time SIMD constant folding

### INV-SIMD-003 — `std.simd` portable `Vector<T, N>`, `Mask<N>`, fixed-width aliases, lane operations, reductions, and capability-checked masked memory API
- statement: `std/simd/mod.ax` provides portable `Vector<T, N>`, `Mask<N>`, and canonical fixed-width aliases (`i8x16`..`f64x4`, `mask8x16`..`mask64x4`) with `splat`/`from_array`/`to_array` constructors, `extract`/`insert`, compile-time `shuffle`/`swizzle`/`interleave_lo`/`interleave_hi`/`deinterleave`/`reverse`/`rotate_lanes_*`, `Mask<N>` bitmask (`bitmask`/`from_bitmask`) and predicate queries (`all`/`any`/`none`/`count_ones`/`select`), explicit integer overflow families (`wrapping_*`, `saturating_*`, `checked_*`, `overflowing_*`), strict IEEE-754 float lane operations (`fma`, `sqrt`, `abs`, `copysign`, `min`, `max`, `floor`, `ceil`, `round`, `trunc`), deterministic reductions (`reduce_add_ordered`, `reduce_add`), and safe `view<[T]>` / `mut_view<[T]>` memory operations (`from_slice`, `copy_to_slice`, `load_unaligned`, `store_unaligned`, `load_masked`, `store_masked`, `gather`, `scatter`) without exposing target ISA intrinsics (SPEC-42 AXS-SIMD-001..043).
- source: 0095; tasks/0337; tasks/0341; tasks/0344; tasks/0347; tasks/0427; CATALOG.md REQ-SIMD-001..008, REQ-SIMD-086..092, REQ-SIMD-096..097, REQ-SIMD-166..168, REQ-SIMD-171; SPEC-42 AXS-SIMD-001..043
- verify: tests/std/simd
- since: T466
- check: `std.simd` unit and execution tests in tests/std/simd (delivered by T466) verify all vector/mask constructors, lane shuffles, arithmetic/bitwise/mask operations, reductions, and masked/gather/scatter memory safety

### INV-SIMD-004 — Data-oriented `SoA`, `Vec2..4`/`Mat2..4`, and rank-parameterized `TensorView<T, R>` / `TensorMutView<T, R>` / `MatrixView<T>` capability discipline and E12.3 conformance
- statement: `std/simd/tensor.ax` and `std/simd/matrix.ax` provide `TensorView<T, const R: usize>`, `TensorMutView<T, const R: usize>`, `MatrixView<T>`, `MatrixMutView<T>`, and value-semantic `Vec2..4<T>` / `Mat2..4<T>` backed by a single flat `view<[T]>` / `mut_view<[T]>` capability and `[R]usize` / `[R]isize` shape/stride metadata without nested views, ensuring zero-copy `subview`/`transpose`/`reshape_contiguous` transformations, read-only `broadcast_to` (forbidding zero or overlapping mutable strides on `TensorMutView`), disjoint `split_axis_mut` borrows, deterministic SIMD `dot`/`axpy`/`gemv`/tiled `matmul`, and full compile-time capability lifetime enforcement (`AX_CAP_CONFLICT_MUT`, `AX_CAP_OUTLIVES_OWNER`, `AX_CAP_CONTAINER_RELOC`) across `--interp` and native x86-64 (SPEC-42 AXS-SIMD-050..063).
- source: 0095; tasks/0337; tasks/0341; tasks/0344; tasks/0472; CATALOG.md REQ-SIMD-096, REQ-SIMD-097, REQ-SIMD-333; SPEC-42 AXS-SIMD-050..063
- verify: tests/std/tensor_matrix, tests/conformance/p12/e12_3_simd_vectors, tests/ui/simd/capability_bounds
- since: T468
- check: tensor/matrix tests in tests/std/tensor_matrix (T467), UI capability tests in tests/ui/simd/capability_bounds (T468), and E12.3 conformance tests in tests/conformance/p12/e12_3_simd_vectors (T468) verify zero-copy views, tiled `matmul`, `SoA` vectorization, and capability conflict/escape rejection

### INV-SIMD-005 — LIR vector type model (`v128`/`v256`/`v512`), `RegClass`, MIR-to-LIR vector legalizer, and Windows x64 vector ABI
- statement: `compiler/lir/` represents vector values via `v128`, `v256`, and `v512` `LirType` tags with lane element/count metadata and `Vec128`/`Vec256`/`Vec512`/`Mask` `RegClass` entries, lowers MIR SIMD operations (`MIR_RVALUE_VECTOR_OP`, `Splat`, `Extract`, `Insert`, `Shuffle`, `Reduce`, `nontemporal`, `prefetch`) into canonical `LirOp.V*` instructions, deterministically splits `v256`/`v512` operations into lo/hi `v128` pairs when target ISA width is 128 bits (`x86_64_v1`) while preserving ordered and pairwise float reduction trees, and classifies `Vector<T, N>` / `Mask<N>` arguments and returns under Windows x64 ABI (`ByRef` in `RCX..R9`, `sret` in `RCX`, `XMM6..XMM15` 128-bit callee-saved preservation, and `VZEROUPPER` hygiene) (SPEC-43 AXS-SBE-001..023).
- source: 0162 §36-41, ALIR-36..41; 0179 §26-34, AWINABI-11, AWINABI-16..18, AWINABI-30..33; tasks/0403; tasks/0407; CATALOG.md REQ-SIMD-019..021, REQ-SIMD-023..025, REQ-SIMD-029..039; SPEC-43 AXS-SBE-001..023
- verify: tests/lir/simd, tests/abi/win64_simd
- since: T470
- check: LIR golden tests in tests/lir/simd and Windows x64 ABI tests in tests/abi/win64_simd (delivered by T470) verify `v128`/`v256`/`v512` LIR construction, legalizer `v256 -> 2x v128` splitting, ordered vs pairwise float reduction lowering, `ByRef`/`sret` classification, `XMM6..XMM15` save/restore, and `VZEROUPPER` emission

### INV-SIMD-006 — Pure-Axiom x86-64 SSE2/SSE4.1 (`0F`/`0F 38`/`0F 3A`) and 2-byte/3-byte `VEX` (`C5`/`C4`) machine-code encoder
- statement: `compiler/target/x64/encode.ax` encodes SSE2/SSE4.1 (`0F`, `0F 38`, `0F 3A`) and AVX/AVX2/FMA 2-byte (`C5`) and 3-byte (`C4`) `VEX` instructions with exact inverted `~R`/`~X`/`~B`/`~vvvv` bits, shortest-form `C5` selection whenever `X == 1 && B == 1 && W == 0 && mmmmm == 0b00001`, mandatory `SIB` (`0x24`) on `RSP`/`R12` base addressing and `disp8 = 0x00` on `RBP`/`R13` base addressing, `VSIB` (`mod != 0b11`, `index = ymm/xmm`) encoding for `VGATHER*`, and bit-exact 128-bit/256-bit `.rdata` vector constant emission (SPEC-43 AXS-SBE-030..035).
- source: 0181 §32, AX64-28; tasks/0403; tasks/0407; CATALOG.md REQ-SIMD-042..043; SPEC-43 AXS-SBE-030..035
- verify: tests/encode/simd_vex
- since: T471
- check: encoder unit tests in tests/encode/simd_vex (delivered by T471) assert byte-for-byte machine code for SSE2, SSE4.1 (`0F 38`/`0F 3A`), 2-byte `C5` and 3-byte `C4` VEX instructions across low/extended `XMM0..15`/`YMM0..15` registers, `RSP`/`RBP` memory edge cases, and `VSIB` gather addressing

### INV-SIMD-007 — Native x86-64 baseline SSE2 SIMD instruction selection, stack frame alignment, and fault-suppressing masked memory
- statement: `compiler/target/x64/isel.ax` and `compiler/target/x64/frame.ax` lower all `v128` LIR vector operations to baseline SSE2 (`x86_64_v1`) instructions without requiring SSE4.1/AVX2 on the host CPU, align 16-byte and 32-byte vector spill slots (`MOVDQA`/`MOVUPS` or `VMOVDQA`/`VMOVUPS`), enforce inactive-lane fault suppression on `VLoadMasked`, `VStoreMasked`, `VGather`, and `VScatter` by guarding per-lane memory accesses when `VMOVMASKPS`/`VMOVMASKPD` (with `VTESTPS`/`VTESTPD` fast-paths) indicates partial masks, and promote `tests/std/simd` and `tests/std/tensor_matrix` to native execution with `0 WEAK-NATIVE` (SPEC-43 AXS-SBE-016, AXS-SBE-021, AXS-SBE-040..045).
- source: 0179; 0181; tasks/0403; tasks/0407; CATALOG.md REQ-SIMD-019..022, REQ-SIMD-031..039, REQ-SIMD-046..050; SPEC-43 AXS-SBE-016, AXS-SBE-021, AXS-SBE-040..045
- verify: tests/run/simd/sse2_native, tests/std/simd, tests/std/tensor_matrix
- since: T472
- check: differential execution tests in tests/run/simd/sse2_native, tests/std/simd, and tests/std/tensor_matrix (delivered by T472) pass in both `--interp` and native x86-64 modes with `0 WEAK-NATIVE`

### INV-SIMD-008 — Target-gated AVX2/FMA 256-bit `YMM` codegen, `std.arch.x86_64` intrinsic surface, and E12.4 conformance
- statement: Under `-C target-feature=+avx2,+fma` (`x86_64_v3`) or `@target_feature("avx2,fma")`, `compiler/target/x64/isel.ax` keeps `v256` values in `YMM0..YMM15`, emits 3-operand VEX instructions (`VPADDD`, `VFMADD213PS`, `VPERM2I128`/`VPERMD`, `VMASKMOVPS`/`VMASKMOVPD` loads, `VZEROUPPER`), exposes `std.arch.x86_64` (`__m128*`, `__m256*`, SSE2/SSE4.1/AVX2/FMA intrinsics, `cpuid`, `xgetbv`, `has_avx2`, `has_fma`) with compile-time `AX_SIMD_TARGET_FEATURE_REQUIRED` (`AXD-042`) and `AX_UNSAFE_REQUIRED` checks, and satisfies the E12.4 conformance suite with `0 WEAK-NATIVE` (SPEC-43 AXS-SBE-023, AXS-SBE-040..052).
- source: SPEC-04 AXS-EXT-010..013, AXS-EXT-044; SPEC-43 AXS-SBE-001..052; tasks/0403; tasks/0407; CATALOG.md REQ-SIMD-019..025, REQ-SIMD-029..039, REQ-SIMD-042..043, REQ-SIMD-046..050
- verify: tests/lir/simd_avx2, tests/run/simd/avx2_native, tests/conformance/p12/e12_4_simd_backend
- since: T474
- check: AVX2 LIR golden tests in tests/lir/simd_avx2 (T473), runtime-dispatched AVX2/FMA execution tests in tests/run/simd/avx2_native (T473), and E12.4 conformance tests in tests/conformance/p12/e12_4_simd_backend (T474) verify `x86_64_v1` vs `x86_64_v3` parity, `AX_SIMD_TARGET_FEATURE_REQUIRED` diagnostics, `VZEROUPPER` hygiene, and `0 WEAK-NATIVE`

### INV-SIMD-009 — `TargetDesc` feature implication DAG, `@target_feature` call-site/inliner legality, and `std.arch` `CPUID`/`XGETBV` runtime feature detection
- statement: `TargetDesc` models the x86-64 feature implication DAG (`avx512f -> avx2 -> avx -> sse4.2 -> sse4.1 -> ssse3 -> sse3 -> sse2 -> sse`, `fma -> avx`, `sse4.2 -> popcnt`, `bmi2 -> bmi1`) controlled via `--target-feature=+feat,-feat` without altering Core language semantics (`AXS-CPU-001..005`); `compiler/hir/`, `compiler/types/`, and `compiler/verify/` enforce `@target_feature("...")` (`AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_INVALID_ATTRIBUTE`) and reject unguarded calls or function-pointer coercions from narrower-feature callers with `AX_TARGET_FEATURE_MISMATCH` unless inside `unsafe`, a dominating `is_x86_feature_detected` branch, or a `@multiversion` dispatcher while forbidding inlining of wider-feature callees into narrower callers (`AXS-CPU-010..014`); and `std/arch/detect.ax` (`is_x86_feature_detected`, `detected_feature_mask`, `has_*`) verifies both `CPUID` leaves `1`/`7`/`0x80000001` and OS `XGETBV(0)` (`XCR0` XMM/YMM/ZMM state), caches the result atomically, and is simulated deterministically in `--interp` via `--interp-cpu-features` (SPEC-44 AXS-CPU-001..023).
- source: 0095 §7-8, ASIMD-14; 0163 §1-7; tasks/0341 §100 ANUM-29..30; tasks/0344 §100 ASIMD-71..73, 97; tasks/0403 §82; tasks/0407 §35; tasks/0453 §194.14-15; CATALOG.md REQ-SIMD-011..013, REQ-SIMD-051, REQ-SIMD-079, REQ-SIMD-094..095, REQ-SIMD-217..219, REQ-SIMD-243, REQ-SIMD-256..257; SPEC-04 AXS-EXT-022/032/054/060/091; SPEC-44 AXS-CPU-001..023
- verify: tests/ui/simd/target_feature, tests/std/arch_detect
- since: T477
- check: UI diagnostic tests in tests/ui/simd/target_feature (T476) and runtime detection / oracle simulation tests in tests/std/arch_detect (T477) verify feature DAG closure, `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_INVALID_ATTRIBUTE`, `AX_TARGET_FEATURE_MISMATCH` on unguarded calls, dominating `is_x86_feature_detected` acceptance, and `CPUID`/`XGETBV` parity across `--interp-cpu-features` profiles and native x86-64

### INV-SIMD-010 — `@multiversion` clone synthesis, deterministic runtime/compile-time dispatcher, external ABI preservation, and E12.5 conformance
- statement: `@multiversion("...")` synthesizes per-feature specialized clones (`<fn>$mv$<slug>`) plus a mandatory baseline fallback (`<fn>$mv$default`), lowers each clone with its own `effective_features` while preserving a single common semantic contract and identical external `Win64` ABI (`VZEROUPPER` hygiene at public boundaries), emits a deterministic descending feature-priority runtime dispatcher via `std.arch.detect.detected_feature_mask()`, eliminates runtime dispatch statically when compile-time `--target-feature` satisfies the highest clone, and passes the E12.5 conformance suite across `--interp-cpu-features=sse2`, `sse4.1`, `avx2,fma`, and native x86-64 with `0 WEAK-NATIVE` (SPEC-44 AXS-CPU-030..042).
- source: 0095 §8; tasks/0344 §100 ASIMD-73..78; tasks/0347 §100 ASIMD-73..78; tasks/0453 §194.14-15; CATALOG.md REQ-SIMD-218..224; SPEC-44 AXS-CPU-030..042
- verify: tests/mir/multiversion, tests/run/simd/multiversion, tests/conformance/p12/e12_5_multiversioning
- since: T479
- check: MIR/LIR clone and static-dispatch dump tests in tests/mir/multiversion (T478), differential execution tests in tests/run/simd/multiversion (T478), and E12.5 conformance tests in tests/conformance/p12/e12_5_multiversioning (T479) verify clone synthesis, runtime dispatch across simulated CPU profiles, static dispatch elimination under `--target-feature=+avx2,+fma`, and bit-identical oracle vs native x86-64 results (`0 WEAK-NATIVE`)

## 16. Raw memory, volatile/MMIO register wrappers, untagged unions, packed/aligned layout, and address spaces (SPEC-51)

### INV-MEM-001 — Untagged `union` ownership safety, `@repr(packed)` / `@align(N)` layout, unaligned packed-field view prohibition, and `@addr_space(N)` checking
- statement: Untagged `union` types place all fields at offset `0` (`size = align_up(max_field_size, align)`, `align = max_field_align`), restrict fields to `Copy` or `ManuallyDrop<T>` (`AX_TYPE_UNION_NON_COPY_FIELD`), require single-field initialization (`AX_TYPE_UNION_INIT_FIELD_COUNT`), permit safe field writes, and require `unsafe` for field reads or pattern matching (`AX_UNSAFE_REQUIRED`); `@align(N)` and `@repr(packed(N))` enforce power-of-two alignments (`AX_TYPE_INVALID_ALIGN`) and reject conflicting `@repr(packed)` + `@align(N)` combinations (`AX_TYPE_CONFLICTING_REPR`); creating a `view<T>`, `mut_view<T>`, or aligned `*const T`/`*mut T` to a potentially unaligned field of a `@repr(packed)` struct is rejected (`AX_TYPE_UNALIGNED_PACKED_REF`) while by-value copy loads/stores remain legal; and pointers with distinct `@addr_space(N)` qualifiers cannot implicitly coerce (`AX_TYPE_ADDR_SPACE_MISMATCH`) (SPEC-51 AXS-MEM-010..012, AXS-MEM-020..024, AXS-MEM-050).
- source: 0067 §7-10, AREP-06..07; 0072 §1-13, AREP-13..16; 0113 §122; 0119 §226; 0132 §13-16, ADATA-29..31; tasks/0328 §26-27; tasks/0367 §82; tasks/0413 §70; tasks/0515 §84-88; SPEC-04 AXS-EXT-020..021, AXS-EXT-030; SPEC-51 AXS-MEM-010..012, AXS-MEM-020..024, AXS-MEM-050
- verify: tests/ui/layout
- since: T507
- check: UI and layout tests in tests/ui/layout (delivered by T507) verify `union` size/alignment and `Copy`/`ManuallyDrop` field enforcement, `unsafe` union reads, `@repr(packed)`/`@align(N)` layout calculations, `AX_TYPE_UNALIGNED_PACKED_REF`, and `AX_TYPE_ADDR_SPACE_MISMATCH`

### INV-MEM-002 — Non-elidable, non-reordering, exact-width non-tearing volatile and `Mmio*<T>` lowering plus unaligned packed codegen
- statement: `volatile_load`, `volatile_store`, `volatile_copy`, `compiler_fence`, `memory_barrier`/`write_barrier`/`read_barrier`, and direct field reads/writes on `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, and `MmioWO<T>` (`ADR-0001 §2`) lower through `MirStmtKind.VolatileLoad`/`VolatileStore` and `LIR_MEM_FLAG_VOLATILE` without CSE, dead-store elimination, coalescing, loop hoisting, or cross-volatile reordering at `-O1`/`-O2`, emit exact-width non-tearing x86-64 instructions (`MOV r8/m8`, `MOV r16/m16`, `MOV r32/m32`, `MOV r64/m64`, `MFENCE`/`SFENCE`/`LFENCE`) for 1-, 2-, 4-, and 8-byte accesses, and lower `read_unaligned`, `write_unaligned`, and `@repr(packed)` by-value field loads/stores with alignment `1` (SPEC-51 AXS-MEM-001..005, AXS-MEM-023).
- source: ADR-0001 §2; 0071 §31-32; 0097 AOS-26..30; 0128 §62; 0161 §30-31; 0162 §9-12, §32; tasks/0328 §13-16, §37-39, AMEMLOW-41..48, AMEMLOW-90..97; tasks/0515 §109, §112-115, §136-140, §149, AMEM-74..78, AMEM-93, AMEM-122; SPEC-04 AXS-EXT-043, AXS-EXT-051; SPEC-51 AXS-MEM-001..005, AXS-MEM-023
- verify: tests/lir/volatile, tests/run/volatile
- since: T508
- check: LIR golden tests in tests/lir/volatile and differential execution tests in tests/run/volatile (delivered by T508) verify non-elision and non-merging of consecutive volatile loads/stores at `-O1`, exact-width `MOV` emission, and unaligned `@repr(packed)` field access in `--interp` and native x86-64

### INV-MEM-003 — `std.mem` `Volatile<T>` / `Mmio<T>` / `MmioRO<T>` / `MmioWO<T>`, `MaybeUninit<T>`, `ManuallyDrop<T>`, `bitcast`, and `offset_of` contracts
- statement: `std/mem/` provides `Volatile<T>`, `Mmio<T>`, `MmioRO<T>` (rejecting writes with `AX_TYPE_MMIO_WRITE_READONLY`), and `MmioWO<T>` (rejecting reads with `AX_TYPE_MMIO_READ_WRITEONLY`) with `read`, `write`, `modify`, and bitmask helpers (`set_bits`, `clear_bits`, `test_bits`, `extract_bits`, `insert_bits`), `MaybeUninit<T>` (`uninit`, `zeroed`, `new`, `write`, `assume_init`, `as_ptr`, `as_mut_ptr`), `ManuallyDrop<T>`, size-checked `bitcast<From, To>(v: From) -> To` (`AX_TYPE_BITCAST_SIZE_MISMATCH`), and `offset_of(Type, field)` with bit-exact parity between `--interp` and native execution (SPEC-51 AXS-MEM-005..006, AXS-MEM-013..015, AXS-MEM-020).
- source: ADR-0001 §2; ADR-0013 §2; 0067 §11-13, §35-36, AREP-10; 0072 §7-9, §14-17, §26-31, §51-54, AREP-15, AREP-18..19, AREP-22; tasks/0328 §24-25, §30, AMEMLOW-60..64; tasks/0367 §82; tasks/0515 AMEM-39..46, AMEM-61..62; SPEC-51 AXS-MEM-005..006, AXS-MEM-013..015, AXS-MEM-020
- verify: tests/std/mem_volatile_mmio
- since: T509
- check: unit and differential tests in tests/std/mem_volatile_mmio (delivered by T509) verify `Volatile<T>`, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>`, `MaybeUninit<T>`, `ManuallyDrop<T>`, `bitcast`, and `offset_of` across `--interp` and native x86-64

### INV-MEM-004 — End-to-end E13.2 raw memory, volatile, MMIO, untagged union, `@repr(packed)` / `@align(N)`, `MaybeUninit<T>`, and `bitcast` conformance
- statement: The E13.2 conformance suite certifies the complete `SPEC-51` contract across volatile ordering and non-tearing width guarantees, `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` register wrappers, untagged `union` initialization and `unsafe` field reads, `@repr(packed)` unaligned-view rejection, `MaybeUninit<T>`/`ManuallyDrop<T>`, `bitcast`, and `@addr_space(N)` isolation with differential agreement between `--interp` and native x86-64 (SPEC-51 AXS-MEM-001..053).
- source: SPEC-51 AXS-MEM-001..053; ADR-0001 §2; 0067; 0072; tasks/0328; tasks/0515
- verify: tests/conformance/p13/e13_2_volatile_mmio_layout
- since: T510
- check: conformance tests in tests/conformance/p13/e13_2_volatile_mmio_layout (delivered by T510) pass in both `--interp` and native modes with `0 WEAK-NATIVE`

## 17. Freestanding execution, modular runtime composition, and capability graph (SPEC-52)

### INV-FRE-001 — Compilation profiles (`--profile hosted|freestanding|kernel|system`), `@entry`/`@panic_handler`/`@naked`/`@section`/`@used` checking, `extern "interrupt"` restrictions (`REQ-ABI-102`), and `RuntimeCapabilityGraph`
- statement: `compiler/driver/` and `compiler/sema/` validate `--profile hosted|freestanding|kernel|system` (`AX_DRIVER_INVALID_PROFILE`), enforce `@entry` (`AX_TYPE_ENTRY_MISSING`, `AX_TYPE_DUPLICATE_ENTRY`, `AX_TYPE_ENTRY_SIGNATURE`), `@panic_handler` (`AX_TYPE_INVALID_PANIC_HANDLER`, `AX_TYPE_DUPLICATE_PANIC_HANDLER`), `@global_allocator` (`AX_TYPE_INVALID_GLOBAL_ALLOCATOR`, `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR`), `@naked` (`AX_TYPE_INVALID_NAKED_FN`), `@section("...")`, and `@used` (`AX_TYPE_INVALID_SECTION`), reject hosted Layer-3 OS imports in `freestanding`/`kernel` (`AX_NAME_FREESTANDING_FORBIDDEN_IMPORT`), reject implicit heap allocation, blocking, thread creation, OS I/O, or `.await` directly or transitively inside `extern "interrupt"` handlers (`AX_UNSAFE_INTERRUPT_FORBIDDEN_OP`, `REQ-ABI-102`), and compute the transitive `RuntimeCapabilityGraph` rejecting forbidden capabilities per profile (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`) while versioning Runtime ABI separately (`REQ-ABI-031`) (SPEC-52 AXS-FRE-001..022, AXS-FRE-050).
- source: 0097 AOS-01..35; 0104 §54; 0143 §1-65, ARUNTIME-20..63; tasks/0358 AINIT-20..80; tasks/0359 ARUNTIME-20..90; tasks/0370 ARUNTIME-20..57; tasks/0455 ART-20..50; tasks/0471 AKERNEL-20..70; REQ-ABI-031, REQ-ABI-102; SPEC-52 AXS-FRE-001..022, AXS-FRE-050
- verify: tests/ui/freestanding
- since: T512
- check: positive and negative UI tests in tests/ui/freestanding (delivered by T512) verify `--profile freestanding` rejection of hosted OS modules and forbidden capabilities, `extern "interrupt"` allocation/blocking/`await` rejection (`REQ-ABI-102`), and `@entry`/`@panic_handler`/`@naked`/`@section` validation

### INV-FRE-002 — CRT-free and `kernel32.dll`-free freestanding native image emission, `@entry` direct entrypoint, `@naked` frame suppression, `extern "interrupt"` `IRETQ`, and custom `@section` / `@used` retention
- statement: Under `--profile freestanding` and `--profile kernel`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, and `compiler/link/` emit native PE32+/COFF executables with zero default DLL imports (`objdump -p` shows no `.idata` import directory), bind `AddressOfEntryPoint` directly to `@entry`, omit prologue/epilogue frames on `@naked` functions, preserve all modified GPRs and return via `IRETQ` (`48 CF`) on `extern "interrupt"` handlers (`REQ-ABI-078`), place `@section("...")` items into named COFF sections, and retain `@used` symbols as live roots against dead-section GC (SPEC-52 AXS-FRE-004..005, AXS-FRE-010, AXS-FRE-013..015, AXS-FRE-023).
- source: 0097 AOS-09..12, AOS-26..27; 0129 §76-77 ATYPE-46..47; 0143 §5-15; 0163 §6; 0230 §6; tasks/0358 AINIT-20..80; tasks/0370; tasks/0455; tasks/0471 AKERNEL-25..30, AKERNEL-63; REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-RES-145; SPEC-52 AXS-FRE-004..005, AXS-FRE-010, AXS-FRE-013..015, AXS-FRE-023
- verify: tests/link/freestanding
- since: T513
- check: link and objdump tests in tests/link/freestanding (delivered by T513) verify zero DLL imports (`objdump -p`), `@entry` entry point, `@naked` prologue-free codegen, `extern "interrupt"` `IRETQ` emission, custom `@section` placement, `@used` retention, and native execution

### INV-FRE-003 — Zero-OS `std.core` freestanding foundation, pluggable `@panic_handler` / `@global_allocator`, `ForeignBox<T, A>`, and `DmaBuffer<T>` capability ownership
- statement: `std/core/` compiles and executes in `--profile freestanding` with zero references to `std.os`, `std.io`, or `kernel32.dll`; `std/core/panic.ax` and `std/alloc/` expose pluggable `@panic_handler` (`PanicInfo`) and `@global_allocator` (`Allocator` / `GlobalAlloc`) hooks; `ForeignBox<T, A: ForeignDeleter>` enforces explicit foreign allocation domain cleanup without guessing allocator compatibility (`REQ-FFI-005..009`, `REQ-FFI-020`, `REQ-FFI-024`, `REQ-FFI-058`, `REQ-FFI-080`, `REQ-FFI-121`, `REQ-RES-170`); and `DmaBuffer<T>` / `DmaTransfer<T>` statically prevent CPU `mut_view<T>` access while a device DMA transfer is active (`REQ-CAP-140`, `REQ-CAP-143`, `AX_CAP_DMA_ACTIVE_CONFLICT`) (SPEC-52 AXS-FRE-003, AXS-FRE-005, AXS-FRE-011..012).
- source: 0097; 0111 §47; 0119 §233, §259 AFFI-20..21; 0131 §67, §88 AFN-54; 0138 §100 AFFI-27; 0143 §28-41; 0163 §6; tasks/0358; tasks/0359; tasks/0367 §82; tasks/0413 §70; tasks/0445 §186.161 AFFI-30..33; tasks/0465 §206.24 ANET2-44..45; tasks/0471 AKERNEL-34..37; REQ-ABI-078, REQ-CAP-140, REQ-CAP-143, REQ-FFI-005..009, REQ-FFI-020, REQ-FFI-024, REQ-FFI-058, REQ-FFI-080, REQ-FFI-121, REQ-RES-170; SPEC-52 AXS-FRE-003, AXS-FRE-005, AXS-FRE-011..012
- verify: tests/std/freestanding_core
- since: T514
- check: freestanding stdlib tests in tests/std/freestanding_core (delivered by T514) compile and run `std.core` and static-arena `std.alloc` (`ForeignBox`, `DmaBuffer`) under `--profile freestanding` in both `--interp` and native modes with zero OS imports

### INV-FRE-004 — End-to-end E13.3 freestanding boot-without-std and modular runtime composition conformance
- statement: The E13.3 conformance suite certifies that a freestanding Axiom program (`--profile freestanding`) with `@entry`, `@panic_handler`, custom `@section` / `@used` placement, `extern "interrupt"` handlers, and `std.core` boots and runs without `std` or any OS/CRT import across `--interp` and native x86-64 (`0 WEAK-NATIVE`, verified zero DLL imports via `objdump -p`), while rejecting forbidden ambient OS/heap/blocking operations in freestanding and interrupt contexts (SPEC-52 AXS-FRE-001..053).
- source: SPEC-52 AXS-FRE-001..053; 0097; 0143; tasks/0358; tasks/0359; tasks/0370; tasks/0455; tasks/0471; REQ-ABI-031, REQ-ABI-102, REQ-FFI-005, REQ-FFI-008, REQ-FFI-066
- verify: tests/conformance/p13/e13_3_freestanding_runtime
- since: T515
- check: positive and negative conformance tests in tests/conformance/p13/e13_3_freestanding_runtime (delivered by T515) pass in `--interp` and native execution with `0 WEAK-NATIVE` and zero DLL imports

## 18. Safety profiles, capability-based OS authority, secure memory, and constant-time execution (SPEC-53)

### INV-SEC-001 — Safety profiles (`--safety-profile safe|sandbox|system`), monotonic `@forbid_unsafe` enforcement, ambient-authority ban (`REQ-CAP-131`), and capability non-forgery (`REQ-CAP-010`, `REQ-CAP-123`)
- statement: `compiler/driver/` and `compiler/sema/` validate `--safety-profile safe|sandbox|system` (`AX_DRIVER_INVALID_SAFETY_PROFILE`), reject all `unsafe` blocks, `unsafe fn`, `unsafe trait`/`unsafe impl`, raw-pointer dereferences/arithmetic, `extern` blocks, `static mut`, and `@addr`/`@at` declarations under `@forbid_unsafe` or `--safety-profile safe|sandbox` (`AX_SEC_UNSAFE_FORBIDDEN`) while preventing inner `@allow_unsafe` escalation (`AX_SEC_CONFLICTING_SAFETY_POLICY`), reject ambient OS calls in `sandbox` and `comptime` without explicit authority capability tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`) and prevent `comptime` $\leftrightarrow$ `runtime` authority leakage (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `REQ-CAP-131`), enforce that every non-owning capability (`view<T>` / `mut_view<T>`) derives from a live owning authority (`REQ-CAP-010`), and forbid implicit conversions from raw pointers or integer addresses into safe capabilities or authority tokens (`AX_SEC_CAPABILITY_FORGERY`, `REQ-CAP-123`) while treating FFI boundaries conservatively as untrusted (`REQ-FFI-117`) (SPEC-53 AXS-SEC-001..011, AXS-SEC-050).
- source: 0124 §1; tasks/0342 ASEC-20..100; tasks/0420 §70 ASEC-31..33, ASEC-54..56; tasks/0449 ASEC-20..44; tasks/0703 §445.1-200; REQ-CAP-010, REQ-CAP-123, REQ-CAP-131, REQ-FFI-117; SPEC-53 AXS-SEC-001..011, AXS-SEC-050
- verify: tests/ui/security_profiles
- since: T517
- check: positive and negative UI diagnostic tests in tests/ui/security_profiles (delivered by T517) verify `@forbid_unsafe`, `--safety-profile sandbox` ambient-authority rejection, capability-token acceptance, and raw-pointer/integer capability forgery rejection

### INV-SEC-002 — `@constant_time` and `Secret<T>` taint verification, branchless `ct_select` (`CMOVcc`) lowering, and non-elidable `zeroize_memory` / `black_box` barriers
- statement: `compiler/mir/`, `compiler/lir/`, and `compiler/target/x64/` propagate `SecClass.Secret` taint across `@secret` / `Secret<T>` values and reject secret-dependent control-flow branches, secret-dependent array/memory indexing, and variable-latency instructions (`DIV`/`IDIV`/`REM` or non-`@constant_time` calls) inside `@constant_time` functions with `AX_SEC_TIMING_LEAK` (`AXS-SEC-022..023`), lower `ct_select` to branchless x86-64 `CMOVcc` / bitwise masks without `-O1` branch re-introduction (`AXS-SEC-024`), preserve `zeroize_memory` and `black_box` as volatile optimization barriers immune to Dead-Store Elimination (`REQ-OPT-353`, `AXS-SEC-021`), enforce WASM linear-memory provenance isolation (`REQ-FFI-124`) and compiler-proven zero-copy deserialization (`REQ-CAP-141`, `AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN`), and support target-specific calling conventions in `TargetDesc` (`REQ-ABI-046`) (SPEC-53 AXS-SEC-004..005, AXS-SEC-014, AXS-SEC-020..024).
- source: 0129 §63; tasks/0451 §192.39 AFFI-46..47; tasks/0466 §207.12 ADATA-34..35; tasks/0467 §208.1-100 ASEC2-20..75; tasks/0703 §445.111-114; REQ-ABI-046, REQ-CAP-141, REQ-FFI-124, REQ-OPT-353; SPEC-53 AXS-SEC-004..005, AXS-SEC-014, AXS-SEC-020..024
- verify: tests/ui/constant_time, tests/lir/constant_time
- since: T518
- check: UI tests in tests/ui/constant_time and LIR golden tests in tests/lir/constant_time (delivered by T518) verify rejection of secret branches/indexing/division (`AX_SEC_TIMING_LEAK`), branchless `CMOVcc` emission for `ct_select`, and retention of `zeroize_memory` stores under `-O1`

### INV-SEC-003 — `std.security` `Secret<T>` zeroize-on-drop, constant-time primitives (`ct_eq`, `ct_select`, `ct_swap_if`), attenuated capability tokens (`FsCap`, `NetCap`, `EnvCap`), and zero-copy I/O/mmap/timer lifetime guards
- statement: `std/security/` provides non-`Copy` `Secret<T>` with redacted `"<secret>"` formatting (`AX_SEC_SECRET_IMPLICIT_COPY`, `AX_SEC_SECRET_EXPOSURE`) and deterministic `Zeroize` scrubbing on `Drop` via `zeroize_memory`, constant-time primitives (`ct_eq_bytes`, `ct_select_u8..u64`, `ct_swap_if_u64`, `ct_copy_if_bytes`) verified under `@constant_time`, monotonically attenuated `FsCap` / `NetCap` / `EnvCap` / `ProcessCap` / `ClockCap` tokens rejecting `..` path traversal, and lifetime-checked zero-copy scatter/gather I/O slices (`REQ-CAP-135`, `REQ-CAP-139`, `AX_CAP_IO_BUFFER_OVERLAP`), `MappedRegion` exclusive/shared views (`REQ-CAP-136`), and scoped timer callbacks (`REQ-CAP-138`) (SPEC-53 AXS-SEC-010..013, AXS-SEC-020..024).
- source: tasks/0342; tasks/0449; tasks/0461 ANET-27..29; tasks/0462 ASTORE-23..25; tasks/0464 ATIME-32..33; tasks/0465 ANET2-35..36; tasks/0467 ASEC2-20..40; REQ-CAP-135, REQ-CAP-136, REQ-CAP-138, REQ-CAP-139; SPEC-53 AXS-SEC-010..013, AXS-SEC-020..024
- verify: tests/std/security
- since: T519
- check: execution tests in tests/std/security (delivered by T519) verify `Secret<T>` zeroization on drop, redacted formatting, constant-time comparisons/selections, attenuated `FsCap`/`NetCap` path/endpoint confinement, and scatter/gather/mmap/timer capability lifetime enforcement in `--interp` and native modes

### INV-SEC-004 — End-to-end E13.4 safety profiles, capability security, buffer-pool pin lifetimes (`REQ-CAP-137`), `Secret<T>` zeroization, and `@constant_time` conformance
- statement: The E13.4 conformance suite certifies `@forbid_unsafe`, `--safety-profile safe|sandbox|system`, explicit capability-token OS access (`REQ-CAP-131`), raw-pointer/integer capability non-forgery (`REQ-CAP-010`, `REQ-CAP-123`), buffer-pool `PagePin<T>` eviction prevention while page views are live (`REQ-CAP-137`), `Secret<T>` non-elidable zeroization on drop, and `@constant_time` timing-leak rejection across `--interp` and native x86-64 with `0 WEAK-NATIVE` (SPEC-53 AXS-SEC-001..053).
- source: SPEC-53 AXS-SEC-001..053; tasks/0342; tasks/0449; tasks/0462 ASTORE-29..31; tasks/0467; tasks/0703; REQ-CAP-010, REQ-CAP-123, REQ-CAP-131, REQ-CAP-137
- verify: tests/conformance/p13/e13_4_security_profiles
- since: T520
- check: positive and negative conformance tests in tests/conformance/p13/e13_4_security_profiles (delivered by T520) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 19. Panic strategy, deterministic drop unwinding, @no_panic verification, and FFI no-unwind barrier (SPEC-54)

### INV-PAN-001 — `--panic abort|unwind` driver flag, `@no_panic` transitive call-graph verification, MIR unwind cleanup edges, FFI boundary abort guard, and oracle `std.panic.catch_unwind`
- statement: The compiler driver accepts `--panic abort|unwind` and `axiom.toml` `panic = "abort" | "unwind"` (`REQ-FFI-125`), emitting `AX_DRIVER_INVALID_PANIC_STRATEGY` (exit code 2) on invalid values or unsupported `--no-std` unwind requests. Semantic analysis enforces `@no_panic` (`REQ-ABI-105`), rejecting any direct or transitive panic source (`panic`, `assert`, `unwrap`, unchecked indexing, unverified division/remainder, or non-`@no_panic` calls) with `AX_PANIC_FORBIDDEN_IN_NO_PANIC` and non-function `@no_panic` attributes with `AX_TYPE_INVALID_NO_PANIC_ATTR`. Under `--panic unwind`, MIR lowering emits explicit unwind cleanup edges executing reverse-order `Drop` glue (`REQ-FFI-094`), synthesized `AbortOnUnwind` guards on `extern "C"` boundaries (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-ABI-096`), double-panic abort guards, and `std.panic.catch_unwind` recovery (`REQ-FFI-127`) (SPEC-54 AXS-PAN-001..023, AXS-PAN-050..053).
- source: 0107 §7; 0119; 0131; 0138; 0188 AFINAL-26..27; 0229; tasks/0351 AFFI-27; tasks/0413 AUNSAFE-32; tasks/0445; tasks/0478 AGOV2-26; tasks/0517 APANIC-20..40; tasks/0585; tasks/0700; REQ-FFI-004, REQ-FFI-010, REQ-FFI-019, REQ-FFI-023, REQ-FFI-041, REQ-FFI-061, REQ-FFI-093, REQ-FFI-094, REQ-ABI-096, REQ-FFI-125, REQ-FFI-127, REQ-ABI-105; SPEC-54 AXS-PAN-001..023, AXS-PAN-050..053
- verify: tests/ui/panic, tests/run/panic_oracle
- since: T522
- check: UI tests in tests/ui/panic and oracle execution tests in tests/run/panic_oracle (delivered by T522) verify `--panic abort|unwind` CLI validation, `@no_panic` call-graph diagnostics, reverse-order `Drop` execution during unwinding, `std.panic.catch_unwind` recovery, double-panic abort, and `extern "C"` boundary abort barriers

### INV-PAN-002 — Native x86-64 MIR cleanup landing pads, Windows x64 SEH `.pdata`/`.xdata` unwind metadata, and native `catch_unwind` / `extern "C"` no-unwind barrier parity
- statement: The native x86-64 backend lowers MIR unwind cleanup edges into native cleanup landing pads (`REQ-FFI-094`), emits Windows x64 SEH `.pdata` (`RUNTIME_FUNCTION`) and `.xdata` (`UNWIND_INFO`) unwind metadata tables in COFF/PE outputs, and executes `std.panic.catch_unwind` (`REQ-FFI-127`), double-panic abort, and `extern "C"` callback panic abort barriers (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-ABI-096`) identically to `--interp` (`0 WEAK-NATIVE`) (SPEC-54 AXS-PAN-010..023, AXS-PAN-051..053).
- source: 0188 AFINAL-26..27; tasks/0351 AFFI-27; tasks/0517 APANIC-20..40; tasks/0585; tasks/0700; REQ-FFI-004, REQ-FFI-010, REQ-FFI-019, REQ-FFI-023, REQ-FFI-041, REQ-FFI-061, REQ-FFI-093, REQ-FFI-094, REQ-ABI-096, REQ-FFI-127; SPEC-54 AXS-PAN-010..023, AXS-PAN-051..053
- verify: tests/run/panic_native
- since: T523
- check: native execution tests in tests/run/panic_native (delivered by T523) verify native reverse-order `Drop` unwinding, `std.panic.catch_unwind` recovery, double-panic abort, `extern "C"` callback no-unwind abort barrier, and PE `.pdata`/`.xdata` unwind table generation on Windows x64

### INV-PAN-003 — End-to-end E13.5 `--panic abort|unwind`, `@no_panic`, `std.panic.catch_unwind`, and FFI no-unwind barrier conformance
- statement: The E13.5 conformance suite certifies `--panic abort|unwind` (`REQ-FFI-125`), `@no_panic` transitive panic-freedom verification (`REQ-ABI-105`), reverse-order `Drop` cleanup during stack unwinding (`REQ-FFI-094`), `std.panic.catch_unwind` isolation (`REQ-FFI-127`), double-panic abort, and `extern "C"` / WASM / plugin / GPU FFI no-unwind abort barriers (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-ABI-096`) across `--interp` and native x86-64 with `0 WEAK-NATIVE` (SPEC-54 AXS-PAN-001..053).
- source: SPEC-54 AXS-PAN-001..053; 0107; 0119; 0131; 0138; 0188; 0229; tasks/0351; tasks/0413; tasks/0445; tasks/0478; tasks/0517; tasks/0585; tasks/0700; REQ-FFI-004, REQ-FFI-010, REQ-FFI-019, REQ-FFI-023, REQ-FFI-041, REQ-FFI-061, REQ-FFI-093, REQ-FFI-094, REQ-ABI-096, REQ-FFI-125, REQ-FFI-127, REQ-ABI-105
- verify: tests/conformance/p13/e13_5_panic_unwinding
- since: T524
- check: positive and negative conformance tests in tests/conformance/p13/e13_5_panic_unwinding (delivered by T524) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 20. Comptime 2.0, value lifting, partial evaluation, specialization, and const/static/TLS initialization (SPEC-60)

### INV-CTM-001 — Unified Comptime 2.0 type/ownership/capability verification and default capability sandbox (`AX_CTM_CAPABILITY_DENIED`)
- statement: `const`, `comptime fn`, `comptime { ... }` blocks, and `[T, comptime N: usize]` const generics execute as evaluation modes of the single Axiom language using the identical type system, move/`Copy` ownership rules, `view`/`mut_view` capability verifier, and package visibility boundaries as runtime code (`AXS-CTM-001..004`), reject runtime calls to `comptime fn` (`AX_CTM_RUNTIME_CALL_FORBIDDEN`) and runtime captures inside `comptime { ... }` (`AX_CTM_NON_CONST_CAPTURE`), and run in a default sandboxed environment that rejects undeclared ambient OS filesystem, network, process environment (`env`), wall-clock/monotonic time (`time`), or foreign FFI operations with `AX_CTM_CAPABILITY_DENIED` even inside `unsafe` blocks (SPEC-60 AXS-CTM-001..004, AXS-CTM-050).
- source: 0102; 0131 §68-69, §88 AFN-55..56; 0140 Part XXI; tasks/0340; tasks/0346 ACOMP2-20..49; tasks/0443 APROC-30..34; tasks/0453 ATARGET-22..23, 35..36; tasks/0464 ATIME-47..49; tasks/0509 COMPTIME-20..42; REQ-CTM-001, REQ-CTM-007..014, REQ-CTM-017..018, REQ-CTM-025..034, REQ-CTM-037..038, REQ-CTM-044, REQ-CTM-046..047, REQ-CORE-683..712, REQ-CORE-2130..2154; SPEC-60 AXS-CTM-001..004, AXS-CTM-050
- verify: tests/ui/comptime
- since: T551
- check: positive and negative UI tests in tests/ui/comptime (delivered by T551) verify `comptime fn`, `comptime { ... }` blocks, `comptime` parameters, `AX_CTM_RUNTIME_CALL_FORBIDDEN`, `AX_CTM_NON_CONST_CAPTURE`, `AX_CTM_CAPABILITY_DENIED`, and `unsafe`-in-comptime sandbox enforcement

### INV-CTM-002 — Comptime MIR evaluation, transient compiler-heap `Drop`, resource no-escape barrier (`AX_CTM_RESOURCE_ESCAPE`), and deterministic `const`/`static` initialization
- statement: `compiler/interp` executes `comptime fn` and `comptime { ... }` bodies on Verified MIR in isolated compiler arena memory, runs deterministic reverse-order `Drop` cleanup on all transient comptime heap allocations (`Vec`, `String`, `Box`) before comptime completion, enforces the Comptime-to-Runtime Value Lifting Barrier by rejecting any escaping unpromoted heap handle, `mut_view`, dead-owner `view`, raw comptime pointer, or authority token with `AX_CTM_RESOURCE_ESCAPE`, uses target `TargetDesc` layout for all compile-time layout queries, and enforces dependency-ordered constant initialization for `const`, `static`, and `@thread_local static` items while detecting cycles (`AX_CTM_CYCLE`), panics (`AX_CTM_PANIC`), and step/memory budget exhaustion (`AX_CTM_STEP_LIMIT`, `AX_CTM_MEM_LIMIT`) without compiler crashes or ICEs (SPEC-60 AXS-CTM-010..013, AXS-CTM-030..032, AXS-CTM-050).
- source: 0111 §47; 0115 §59 ACOMP-20..21; 0120 §276-278 ACOMP-22..23; 0140 Part XXI; tasks/0346 ACOMP2-50..66; tasks/0509 COMPTIME-48..82; tasks/0514 AGLOBAL-20..88; REQ-CTM-002..006, REQ-CTM-015..016, REQ-CTM-023..024, REQ-CTM-036, REQ-CORE-713..729, REQ-CORE-2160..2199, REQ-CORE-2214..2283; SPEC-60 AXS-CTM-010..013, AXS-CTM-030..032, AXS-CTM-050
- verify: tests/run/comptime, tests/mir/comptime
- since: T552
- check: execution and MIR tests in tests/run/comptime and tests/mir/comptime (delivered by T552) verify transient comptime heap allocation and deterministic `Drop`, complex value lifting, `AX_CTM_RESOURCE_ESCAPE` rejection, `AX_CTM_CYCLE`/`AX_CTM_STEP_LIMIT`/`AX_CTM_MEM_LIMIT`, and deterministic `const`/`static` initialization

### INV-CTM-003 — Partial evaluation, `if comptime` specialization, and dependency-tracked comptime cache identity (`ComptimeCacheKey`)
- statement: `compiler/sema/specialize.ax` and `compiler/opt/` specialize functions and closures over `comptime` parameters and constant arguments, fold `if comptime` branches while preserving runtime overflow/bounds/division traps on remaining runtime paths, respect global effect/alias/synchronization barriers (`AGLOBAL-89..108`), and cache comptime evaluations in `compiler/driver` under a content-addressed `ComptimeCacheKey` covering compiler version, target configuration, transitive callees, capability policy, and declared external inputs so cache hits are 100% observationally equivalent to fresh evaluations (SPEC-60 AXS-CTM-020..022, AXS-CTM-033).
- source: 0140 §XXI.48 ACOMP-44; tasks/0346 ACOMP2-67..91; tasks/0509 COMPTIME-41..47, COMPTIME-83..87; tasks/0514 AGLOBAL-89..108; REQ-CTM-035, REQ-CTM-041..042, REQ-CORE-730..754, REQ-CORE-2153..2159, REQ-CORE-2195..2199, REQ-CORE-2284..2303; SPEC-60 AXS-CTM-020..022, AXS-CTM-033
- verify: tests/mir/specialize, tests/run/specialize
- since: T553
- check: MIR golden tests in tests/mir/specialize and differential run tests in tests/run/specialize (delivered by T553) verify `comptime` parameter specialization, `if comptime` dead-branch elimination, preservation of runtime traps on untaken paths, and `ComptimeCacheKey` invalidation

### INV-CTM-004 — Native materialization of lifted comptime aggregates into `.rdata`, `.data`, `.bss`, and `.tls` without runtime ComptimeVM overhead
- statement: `compiler/lir`, `compiler/target/x64`, and `compiler/obj` lower comptime-lifted structs, enums, arrays, and promoted static slices (`view<[T]>`, `Str`) into deterministic global data objects with `Addr64` internal relocations, emit read-only constants and immutable statics into `.rdata`, non-zero mutable statics into `.data`, zero-initialized mutable statics into `.bss`, and `@thread_local` templates into `.tls`, preserve unique address identity for address-observable `static` items while permitting `const` deduplication, and link zero ComptimeVM or interpreter symbols into native binaries (SPEC-60 AXS-CTM-030, AXS-CTM-034).
- source: tasks/0509 COMPTIME-24..25, COMPTIME-81; tasks/0514 AGLOBAL-109..150; REQ-CORE-2136..2137, REQ-CORE-2304..2345; SPEC-60 AXS-CTM-030, AXS-CTM-034
- verify: tests/run/comptime_native
- since: T554
- check: differential (`--interp` and native) tests in tests/run/comptime_native (delivered by T554) verify comptime lookup tables, nested structs/enums/slices, `.rdata`/`.data`/`.bss` placement, `static` address identity vs `const` value semantics, and `0 WEAK-NATIVE`

### INV-CTM-005 — End-to-end E14.1 Comptime 2.0, partial evaluation, specialization, and `const`/`static` initialization conformance
- statement: The E14.1 conformance suite certifies `comptime fn`, `comptime { ... }` blocks, `comptime` generic parameters, sandboxed capability enforcement (`AX_CTM_CAPABILITY_DENIED`), transient compiler-heap `Drop` cleanup, the comptime-to-runtime resource no-escape barrier (`AX_CTM_RESOURCE_ESCAPE`), `if comptime` partial evaluation and specialization, dependency-tracked `ComptimeCacheKey` equivalence, and deterministic `const` vs `static` vs `TLS` initialization and `.rdata`/`.data`/`.bss` materialization across `--interp` and native x86-64 with `0 WEAK-NATIVE` (SPEC-60 AXS-CTM-001..053).
- source: SPEC-60 AXS-CTM-001..053; 0102; 0140; tasks/0346 ACOMP2-92..100; tasks/0509 COMPTIME-88..100; tasks/0514 AGLOBAL-151..165; REQ-CORE-755..763, REQ-CORE-2200..2213, REQ-CORE-2346..2360
- verify: tests/conformance/p14/e14_1_comptime
- since: T555
- check: positive and negative conformance tests in tests/conformance/p14/e14_1_comptime (delivered by T555) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 21. Fixed-address declarations (`@at` / `@addr`), MMIO overlay/placement, and address introspection (SPEC-55)

### INV-ADR-001 — `@at` / `@addr` overlay vs placement HIR/THIR/MIR lowering, `fixed` provenance, alignment/overlap/layout verification, and automatic `Volatile`/`Mmio*` field lowering
- statement: `compiler/hir/`, `compiler/sema/`, and `compiler/mir/` lower `@at(<expr>)` and `@addr(<expr>)` on `static`, `static mut`, `let`, `fn`, and `extern fn` into `Placement { kind: Overlay | Place, addr, region }`, enforce `unsafe` declaration trust (`ADR-0001 §2`), defined `@repr(C)`/primitive layout (`AX_UNSAFE_INVALID_AT_LAYOUT`), natural address alignment (`AX_UNSAFE_AT_MISALIGNED` / `AX_UNSAFE_MISALIGNED_AT`), intra-module address range non-overlap (`AX_UNSAFE_AT_OVERLAP`), and profile/region rules (`AX_UNSAFE_AT_HOSTED`), lower fixed-address statics to `PlaceBase.FixedStatic(SymbolId)` with `Provenance.Fixed` (never moved, never dropped) and `Volatile<T>`/`Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` field projections directly to `VolatileLoad`/`VolatileStore` (`AX_TYPE_MMIO_WRITE_READONLY`, `AX_TYPE_MMIO_READ_WRITEONLY`), and support `REQ-OWNER-008` dynamic `base + offset` expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32`) (SPEC-55 AXS-ADR-001..020, AXS-ADR-050).
- source: ADR-0001 §1-4, §7; OWNER.md REQ-OWNER-003, REQ-OWNER-008; 0044; 0071; 0097; tasks/0328; REQ-ABI-055, REQ-ABI-056, REQ-ABI-083, REQ-RES-145, REQ-CAP-140, REQ-CAP-143; SPEC-55 AXS-ADR-001..020, AXS-ADR-050
- verify: tests/ui/fixed_addr
- since: T526
- check: positive and negative UI diagnostic tests in tests/ui/fixed_addr (delivered by T526) verify `@at`/`@addr` overlay and placement declarations, alignment errors, overlap errors, layout-unspecified struct rejection, `MmioRO`/`MmioWO` direction checks, and `REQ-OWNER-008` address expressions

### INV-ADR-002 — Oracle (`--interp`) sparse simulated address space, scriptable MMIO/UART/vector-table device model, and `REQ-OWNER-008` round-trip equality
- statement: `compiler/interp/` maintains a sparse simulated address-space map (`FixedAddrMap`) backing `@at` and `@addr` overlays and placements at their exact `usize` addresses, executes a deterministic scriptable MMIO device model (UART status/tx/rx registers and interrupt vector table dispatch) without hardware, and guarantees `fn_addr(f) == A`, `static_addr(s) == A`, `addr_of(v) == A`, and `(address_of(v) as usize) == A` for both constant and dynamic `base + offset` placements (SPEC-55 AXS-ADR-010..012, AXS-ADR-024).
- source: ADR-0001 §4, §7; OWNER.md REQ-OWNER-003, REQ-OWNER-008; 0071; 0097; tasks/0328; SPEC-55 AXS-ADR-010..012, AXS-ADR-024
- verify: tests/run/fixed_addr_oracle
- since: T527
- check: oracle execution tests in tests/run/fixed_addr_oracle (delivered by T527) verify simulated `@at` vector table dispatch, ROM function overlay calls, UART status polling and data transmission (`UART0.status`, `UART0.data`), dynamic `@addr(base + 0x100)` placement, and `REQ-OWNER-008` round-trip address equality

### INV-ADR-003 — COFF `IMAGE_SYM_ABSOLUTE` overlay symbols, pinned VMA sections, cross-object overlap detection, and freestanding `--format bin` raw-binary output
- statement: `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, and `compiler/link/` emit COFF `IMAGE_SYM_ABSOLUTE` (`SectionNumber = -1`) symbols for constant `@at`/`@addr` overlays, emit per-item pinned sections (`.at.text.*`, `.at.data.*`, `.at.rdata.*` with `pinned_vma = Some(A)`) for placements, reject cross-object VMA overlaps (`AX_LINK_AT_OVERLAP`), emit headerless `--format bin` (`ImageFormat.RawBinary`) freestanding images alongside PE32+ images, and preserve `fn_addr`/`static_addr`/`address_of` round-trip equality in native x86-64 execution (SPEC-55 AXS-ADR-021..023).
- source: ADR-0001 §4, §7; OWNER.md REQ-OWNER-003, REQ-OWNER-008; 0071; 0097; tasks/0328; SPEC-04 AXS-EXT-070..072; SPEC-55 AXS-ADR-021..023
- verify: tests/link/fixed_addr
- since: T528
- check: link, `objdump`, and native execution tests in tests/link/fixed_addr (delivered by T528) verify `IMAGE_SYM_ABSOLUTE` symbols, pinned VMA sections, cross-object overlap rejection, `--format bin` raw binary output, and native `fn_addr(isr) == 0x2000_0000usize` / `static_addr` / `address_of` round-trip equality

### INV-ADR-004 — End-to-end E13.6 fixed-address (`@at` / `@addr`) vector table, UART MMIO, and `REQ-OWNER-003`/`REQ-OWNER-008` round-trip conformance
- statement: The E13.6 conformance suite certifies `@at` and `@addr` overlays and placements across `static`, `static mut`, `let`, arrays, `@repr(C)` structs with `Mmio<T>`/`MmioRO<T>`/`MmioWO<T>` fields, `fn`, and `extern "C" fn`, verifying `REQ-OWNER-003` ordinary-syntax MMIO/vector-table usage and `REQ-OWNER-008` address introspection (`fn_addr`, `static_addr`, `addr_of`, `address_of(v) as usize`, dynamic `base + 0x100` placement) across `--interp` and native x86-64 with `0 WEAK-NATIVE` (SPEC-55 AXS-ADR-001..053).
- source: SPEC-55 AXS-ADR-001..053; ADR-0001 §1-4, §7; OWNER.md REQ-OWNER-003, REQ-OWNER-008
- verify: tests/conformance/p13/e13_6_fixed_addr
- since: T529
- check: positive and negative conformance tests in tests/conformance/p13/e13_6_fixed_addr (delivered by T529) pass in `--interp` and native modes with `0 WEAK-NATIVE` and `objdump` verification

## 22. Compile-time reflection, typed `@derive` synthesis, and code generation boundary (SPEC-61)

### INV-RFL-001 — Zero-overhead compile-time `TypeInfo` reflection intrinsics, declaration-order enumeration, visibility enforcement (`AX_REFLECT_PRIVATE_FIELD`), and representation-obeying layout queries
- statement: `compiler/sema/reflect.ax` and `compiler/interp/reflect.ax` evaluate `type_info<T>()`, `type_name<T>()`, `fields_of<T>()`, `variants_of<T>()`, `attributes_of<T>()`, `offset_of<T, F>()`, and `implements<T, Trait>()` at compile time over authoritative `CompilerDB` semantic data, enumerate struct fields and enum variants in exact source declaration order (`AREFLECT-26..27`), enforce module/package privacy boundaries (`AX_REFLECT_PRIVATE_FIELD` on cross-module private field reflection without `@derive` authority), validate `offset_of` against active representation contracts (`AX_REFLECT_UNSPECIFIED_LAYOUT`) while locking physical field order once observed (`REQ-CTM-020..021`), and erase compile-time reflection descriptors after codegen with zero runtime RTTI or object headers unless explicitly requested (`AX_REFLECT_RUNTIME_NOT_ENABLED`, `REQ-CTM-039`, `REQ-CTM-043`, `REQ-CTM-045`) (SPEC-61 AXS-RFL-001..012, AXS-RFL-050).
- source: 0102; 0140 Part XXI AREFLECT-20..26; tasks/0296; tasks/0343 AMETA-20..57; tasks/0433 AREFLECT-20..30, AMETA-20..27, AZREFLECT-20..24; tasks/0444 §185.152; REQ-CTM-019..022, REQ-CTM-039..040, REQ-CTM-043, REQ-CTM-045, REQ-CORE-602..639; SPEC-61 AXS-RFL-001..012, AXS-RFL-050
- verify: tests/run/reflect, tests/ui/reflect
- since: T557
- check: execution and UI diagnostic tests in tests/run/reflect and tests/ui/reflect (delivered by T557) verify `type_info<T>()`, declaration-order `fields_of`/`variants_of`, `implements<T, Trait>()`, `offset_of`, `AX_REFLECT_PRIVATE_FIELD`, `AX_REFLECT_UNSPECIFIED_LAYOUT`, and zero runtime metadata overhead

### INV-RFL-002 — Typed `@derive` expansion engine, `GenProvenanceId` field-span attribution (`AX_DERIVE_FIELD_BOUND`), conflict/cycle rejection (`AX_DERIVE_CONFLICT`), and mandatory semantic/MIR re-verification
- statement: `compiler/hir/derive.ax` and `compiler/sema/derive_check.ax` synthesize typed HIR `impl` declarations for `@derive(...)` without textual macro substitution or arbitrary AST/HIR/MIR mutation (`REQ-CTM-019`, `AMETA-50..54`, `COMPTIME-32..34`), attach `GenProvenanceId` tracing generated items back to both the `@derive` attribute and offending field/variant spans (`AX_DERIVE_FIELD_BOUND`), deterministically reject duplicate or conflicting impls (`AX_DERIVE_CONFLICT`) and generation cycles (`AX_DERIVE_CYCLE`), and pass every generated `impl` through full name resolution, generic/trait solving, typechecking, ownership, capability, concurrency, FFI/ABI, and MIR verification (`REQ-CTM-040`, `AMETA-41..49`, `COMPTIME-31`, `COMPTIME-58..67`) (SPEC-61 AXS-RFL-020..023, AXS-RFL-050).
- source: 0140 AGEN-20..25; tasks/0343 AMETA-40..77; tasks/0509 COMPTIME-31..37, COMPTIME-58..67; REQ-CTM-019, REQ-CTM-040, REQ-CORE-640..659, REQ-CORE-2143..2149, REQ-CORE-2170..2179; SPEC-61 AXS-RFL-020..023, AXS-RFL-050
- verify: tests/ui/derive, tests/mir/derive
- since: T558
- check: UI and MIR golden tests in tests/ui/derive and tests/mir/derive (delivered by T558) verify typed `@derive` HIR/MIR synthesis, `AX_DERIVE_FIELD_BOUND` provenance labels, `AX_DERIVE_CONFLICT` rejection, and full MIR verification of generated `impl` bodies

### INV-RFL-003 — `std.reflect` API and zero-overhead reflection-driven `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)`
- statement: `std/reflect/` and `std/derive/` expose `TypeInfo`, `TypeKind`, `FieldInfo`, `VariantInfo`, `AttributeInfo`, and `StructLayout` over the compile-time reflection intrinsics and implement `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` across structs, generic structs, fieldless enums, and payload enums (honoring compile-time `@rename`, `@skip`, and `@default` field/variant attributes) while specializing to direct field-by-field operations with zero runtime reflection table overhead (SPEC-61 AXS-RFL-003, AXS-RFL-023..024).
- source: tasks/0296; tasks/0343 AMETA-78..90; tasks/0433 AZREFLECT-20..24; REQ-CORE-660..672; SPEC-61 AXS-RFL-003, AXS-RFL-023..024
- verify: tests/run/derive_std
- since: T559
- check: differential (`--interp` and native) tests in tests/run/derive_std (delivered by T559) verify `@derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` and `@rename`/`@skip`/`@default` attributes with `0 WEAK-NATIVE`

### INV-RFL-004 — End-to-end E14.2 compile-time reflection, visibility/layout boundaries, typed `@derive` re-verification, and `std` derive conformance
- statement: The E14.2 conformance suite certifies compile-time `TypeInfo` introspection, declaration-order field/variant enumeration, cross-module privacy enforcement (`AX_REFLECT_PRIVATE_FIELD`), layout query contracts (`AX_REFLECT_UNSPECIFIED_LAYOUT`), typed `@derive` provenance and conflict diagnostics (`AX_DERIVE_FIELD_BOUND`, `AX_DERIVE_CONFLICT`), and reflection-driven `derive(Debug, Eq, Ord, Hash, Clone, Default, Serialize, Deserialize)` across `--interp` and native x86-64 with `0 WEAK-NATIVE` (SPEC-61 AXS-RFL-001..052).
- source: SPEC-61 AXS-RFL-001..052; tasks/0343 AMETA-91..100; tasks/0433; REQ-CORE-673..682
- verify: tests/conformance/p14/e14_2_reflection_derive
- since: T560
- check: positive and negative conformance tests in tests/conformance/p14/e14_2_reflection_derive (delivered by T560) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 23. Module-relative bindings (`@at(image("mod") + off)`, `image_self()`), load-time slot resolution, and PE DLL/EXE initializer semantics (SPEC-56)

### INV-MOD-001 — `image("name")` / `image_self()` hosted overlay typing, foreign-placement rejection (`AX_UNSAFE_AT_FOREIGN_PLACEMENT`), MIR slot lowering, and oracle `ProcessModuleMap`
- statement: `compiler/hir/`, `compiler/sema/`, `compiler/mir/`, and `compiler/interp/` typecheck `image("name") -> usize` and `image_self() -> usize` in the `hosted` profile (`AX_TYPE_INVALID_IMAGE_ARG`), permit `@at(image("mod") + offset)` and `@at(image_self() + offset)` overlays on `static`, `static mut`, and `extern fn` while rejecting initializers or function bodies at module-relative addresses with `AX_UNSAFE_AT_FOREIGN_PLACEMENT`, verify `@repr(C)`/primitive layout (`AX_UNSAFE_INVALID_AT_LAYOUT`) and constant RVA alignment (`AX_UNSAFE_AT_MISALIGNED`), retain dynamic library capability lifetimes (`REQ-CAP-132`), lower module-relative overlays to load-time resolved pointer slots (`PlacementAddr.ImageRel`), and simulate process modules via `ProcessModuleMap` in `--interp` with deterministic pre-entry failure (`AX_UNSAFE_MODULE_NOT_LOADED`) when a required module is absent (SPEC-56 AXS-MOD-001..010, AXS-MOD-013..014, AXS-MOD-050).
- source: ADR-0001 §5, §7; OWNER.md REQ-OWNER-005, REQ-OWNER-008; 0104 §53-54; 0187; tasks/0336; tasks/0444 AABIAPI-22..26; tasks/0451 AFFI-33..34; REQ-ABI-032, REQ-ABI-033, REQ-ABI-095, REQ-CAP-132; SPEC-56 AXS-MOD-001..010, AXS-MOD-013..014, AXS-MOD-050
- verify: tests/ui/module_rel, tests/run/module_rel_oracle
- since: T531
- check: positive and negative UI diagnostic tests in tests/ui/module_rel and oracle execution tests in tests/run/module_rel_oracle (delivered by T531) verify `image("mod") + off` and `image_self() + off` overlay rules, `AX_UNSAFE_AT_FOREIGN_PLACEMENT` rejection, `addr_of(sym) - image_self()`, and deterministic missing-module init failure

### INV-MOD-002 — Native `.data` slot emission, `RIP`-relative indirect dispatch, open-world optimization barrier (`REQ-FFI-119`), and `GetModuleHandleW` / `__ImageBase` PE DLL `DllMain` (`FALSE`) / EXE startup resolution
- statement: `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, and `compiler/link/` emit `.data` pointer slots (`__ax_modslot_*`) and `.rdata` `ModRelEntry` descriptors for all module-relative bindings, generate 64-bit `RIP`-relative indirect loads and calls through the resolved slots without hardcoded foreign virtual addresses (`0187 §3, §23`), enforce an open-world optimization barrier across foreign module symbols (`REQ-ABI-095`, `REQ-FFI-119`), and wire `__ax_resolve_module_bindings()` (`__ImageBase` for `image_self()`, `GetModuleHandleW` for `image("mod")`) into the synthesized PE DLL `DllMain` (`DLL_PROCESS_ATTACH`) and EXE startup stub so missing modules deterministically return `FALSE` from `DllMain` (`LoadLibraryW == NULL`) or abort EXE startup before any user code runs (SPEC-56 AXS-MOD-004, AXS-MOD-011..012).
- source: ADR-0001 §5-6; OWNER.md REQ-OWNER-005, REQ-OWNER-006; 0104 §53-54; 0187 §3-40 AIMPORT-20..30; tasks/0336; tasks/0434 §53, §92 AFFI-70..71; tasks/0444 AABIAPI-22..26; REQ-ABI-095, REQ-FFI-119; SPEC-04 AXS-EXT-073..074; SPEC-56 AXS-MOD-004, AXS-MOD-011..012
- verify: tests/link/module_rel_dll
- since: T532
- check: native link and execution tests in tests/link/module_rel_dll (delivered by T532) verify host EXE and plugin PE DLL (`--kind dll`) load-time slot resolution via `GetModuleHandleW`/`__ImageBase` and verify that `LoadLibraryW` returns `NULL` (`DllMain` returns `FALSE`) when a target module is missing

### INV-MOD-003 — End-to-end E13.7 module-relative bindings (`@at(image("mod") + off)`, `image_self()`) host EXE + plugin PE DLL conformance
- statement: The E13.7 conformance suite certifies host EXE (`game_host.exe`) and plugin PE DLL (`mod_plugin.dll`) execution using `@at(image("game_host.exe") + RVA)` function and `@repr(C)` static overlays, `@at(image_self() + RVA)` self-relative overlays, `addr_of(item) - image_self()` RVA computation (`REQ-OWNER-008`), explicit `@export` DLL surfaces (`REQ-FFI-042`), and deterministic `DllMain` `FALSE` failure on missing modules (`bad_plugin.dll`) across `--interp` and native Windows x64 execution with `0 WEAK-NATIVE` (SPEC-56 AXS-MOD-001..053).
- source: SPEC-56 AXS-MOD-001..053; ADR-0001 §5-7; OWNER.md REQ-OWNER-005, REQ-OWNER-006, REQ-OWNER-008; 0104 §53-54; 0138 §53; 0187; tasks/0336; REQ-ABI-032, REQ-ABI-033, REQ-ABI-095, REQ-CAP-132, REQ-FFI-042, REQ-FFI-119
- verify: tests/conformance/p13/e13_7_module_relative
- since: T533
- check: positive and negative conformance tests in tests/conformance/p13/e13_7_module_relative (delivered by T533) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 24. Synchronous generators (`gen fn`, `yield`), iterator state machines, and per-state `Drop` cleanup (SPEC-62)

### INV-GEN-001 — `gen fn` / `yield` syntax, HIR → MIR semantic boundary, and live-across-`yield` ownership & capability verification (`AX_GEN_*`)
- statement: `compiler/ast`, `compiler/parser`, `compiler/hir`, and `compiler/own` parse and lower `gen fn` declarations and `yield <expr>` suspensions without re-inferring HIR-determined types, names, overloads, or coercions in MIR (`REQ-CORE-2989..3007`, `AMIR-20..37`), reject `yield` outside a generator (`AX_GEN_YIELD_OUTSIDE_GEN`), value-bearing `return <expr>` inside `gen fn` (`AX_GEN_RETURN_VALUE`), unboxed recursive generators (`AX_GEN_RECURSIVE`), and `@gpu` generators (`AX_GEN_GPU_FORBIDDEN`), compute per-`YieldPointId` `LiveAcrossYield` sets, keep generators non-`Copy` by default, and reject self-referential borrows of generator locals (`AX_GEN_SELF_BORROW_ACROSS_YIELD`) and ephemeral or escaping capabilities (`AX_GEN_VIEW_ACROSS_YIELD`) across `yield` points (`UNKNOWN != SAFE`) (SPEC-62 AXS-GEN-001..020, AXS-GEN-050).
- source: tasks/0512 AGEN-20..65, AGEN-84..89, AGEN-129; tasks/0539 §1, §89 AMIR-20..37; REQ-EXP-325..377, REQ-EXP-391..396, REQ-EXP-436, REQ-CORE-2989..3007; SPEC-62 AXS-GEN-001..020, AXS-GEN-050
- verify: tests/ui/generators
- since: T562
- check: positive and negative UI tests in tests/ui/generators (delivered by T562) verify `gen fn` and `yield` parsing/typing, `AX_GEN_YIELD_OUTSIDE_GEN`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`, `AX_GEN_VIEW_ACROSS_YIELD`, and ownership tracking across multiple `yield` points

### INV-GEN-002 — Zero-heap MIR generator state-machine synthesis, `SwitchInt` resume dispatch, terminal `STATE_COMPLETE`, and per-state `Drop` cleanup
- statement: `compiler/mir/gen_lower.ax`, `compiler/verify`, and `compiler/interp` lower each `gen fn` body into a stackless state-machine struct (`state_tag: u32`, parameters, and only `LiveAcrossYield` locals) implementing `Iterator<Item = T>`, dispatch `next(mut_view(self)) -> Option<T>` via `SwitchInt(self.state_tag)` (`0` = unstarted lazy initial state, `1..K` = suspended at `YieldPointId(k)`, `u32.MAX` = terminal `STATE_COMPLETE` returning `Option.None` on all subsequent calls after completion or panic), and synthesize deterministic per-state `Drop` glue that drops only the live initialized locals of state `k` in reverse declaration order without double-drop (`AMIR-38..48`, `AGEN-21..49`) (SPEC-62 AXS-GEN-003..004, AXS-GEN-021..022).
- source: tasks/0512 AGEN-21..49, AGEN-65..68, AGEN-90..91, AGEN-111..113; tasks/0539 §89 AMIR-38..48; REQ-EXP-328..356, REQ-EXP-372..375, REQ-EXP-397..398, REQ-EXP-418..420, REQ-CORE-3008..3018; SPEC-62 AXS-GEN-003..004, AXS-GEN-021..022
- verify: tests/mir/generators, tests/run/generators
- since: T563
- check: MIR golden tests in tests/mir/generators and differential (`--interp` and native) tests in tests/run/generators (delivered by T563) verify lazy start, `SwitchInt` state transitions, minimal captured locals, per-state `Drop` cleanup on early drop while suspended, and terminal `None` after completion (`0 WEAK-NATIVE`)

### INV-GEN-003 — `for-in` generator loop integration, lazy `std.iter` combinator composition, nested `yield` delegation, and comptime generator evaluation
- statement: `compiler/lowering` and `std/iter` integrate generator state machines directly with `for x in gen(...)` loops and lazy iterator adapters (`map`, `filter`, `take`, `skip`, `zip`, `chain`, `enumerate`, `flatten`, `fold`, `collect`) without intermediate heap allocation, preserve `unsafe`/provenance/atomic/volatile/sync/suspension MIR boundaries (`AMIR-49..60`), run deterministic `Drop` cleanup on early `break`/`return`, and support comptime generator evaluation under `SPEC-60` step budgets (`AGEN-92..110`, `AGEN-127..128`, `AGEN-140`) (SPEC-62 AXS-GEN-023..024).
- source: tasks/0512 AGEN-71, AGEN-92..110, AGEN-127..128, AGEN-140; tasks/0539 §89 AMIR-49..55; REQ-EXP-378, REQ-EXP-399..417, REQ-EXP-434..435, REQ-EXP-447, REQ-CORE-3019..3025; SPEC-62 AXS-GEN-023..024
- verify: tests/run/iter_gen
- since: T564
- check: differential (`--interp` and native) tests in tests/run/iter_gen (delivered by T564) verify `for x in gen_fn(...)` loops, early `break` cleanup, nested generator delegation, comptime generator folding, and `std.iter` adapter chains with `0 WEAK-NATIVE`

### INV-GEN-004 — End-to-end E14.3 generators, `yield` state machines, per-state `Drop`, and lazy control-flow conformance
- statement: The E14.3 conformance suite certifies lazy generator construction, multi-`yield` control flow, terminal `Option.None` completion, per-state `Drop` cleanup when dropped at any suspension point, negative UI diagnostics (`AX_GEN_YIELD_OUTSIDE_GEN`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`, `AX_GEN_VIEW_ACROSS_YIELD`), and differential equivalence across `--interp` and native x86-64 (`-O0` and `-O1`) with zero mandatory heap allocation (`AMIR-56..60`, `0 WEAK-NATIVE`) (SPEC-62 AXS-GEN-001..052).
- source: SPEC-62 AXS-GEN-001..052; tasks/0512 AGEN-20..140; tasks/0539 §89 AMIR-20..60; REQ-CORE-2989..3030, REQ-EXP-325..447
- verify: tests/conformance/p14/e14_3_generators
- since: T565
- check: positive and negative conformance tests in tests/conformance/p14/e14_3_generators (delivered by T565) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 25. Dynamic trait objects (`dyn Trait`), object safety, vtable ABI, and dynamic `Drop` (SPEC-63)

### INV-DYN-001 — `dyn Trait` object-safety verification (`AX_DYN_NOT_OBJECT_SAFE`), capability-preserving unsizing coercion, and oracle dynamic dispatch
- statement: `compiler/traits`, `compiler/mir`, and `compiler/interp` enforce `dyn Trait` object safety (`AX_DYN_NOT_OBJECT_SAFE` when a trait requires `Self: Sized`, declares an associated `const`, leaves an associated `type` unbound, or has a method lacking a `view<Self>`/`mut_view<Self>`/`Box<Self>` receiver, declaring generic parameters, or mentioning `Self` outside the receiver), lower `view<T> -> view<dyn Trait>` and `mut_view<T> -> mut_view<dyn Trait>` unsizing coercions explicitly in MIR (`MirRvalue.UnsizeDyn`) while preserving capability lifetimes and provenance without GC, object headers, or a monolithic runtime (`AMIR-61..70`, `REQ-CORE-3031..3040`), and execute `MirTerminator.CallDyn` and supertrait upcasting deterministically in `--interp` (SPEC-63 AXS-DYN-001..022, AXS-DYN-050).
- source: 0212 §19-48 ATRAIT-20..60; 0158 §18-19; 0161 §31; tasks/0389 §52-70; tasks/0476 §217.49-50; tasks/0539 §42, §89 AMIR-61..70; REQ-CORE-3031..3040, REQ-PAT-015..020; SPEC-63 AXS-DYN-001..022, AXS-DYN-050
- verify: tests/ui/dyn, tests/run/dyn
- since: T058
- check: positive and negative UI tests in tests/ui/dyn and execution tests in tests/run/dyn (delivered by T058) verify `AX_DYN_NOT_OBJECT_SAFE`, capability lifetime tracking on `view<dyn Trait>` / `mut_view<dyn Trait>`, polymorphic dispatch across multiple concrete types, default trait methods, and supertrait upcasting

### INV-DYN-002 — Native read-only `.rdata` vtable emission, 16-byte Windows x64 fat-pointer ABI, and indirect call codegen
- statement: `compiler/lir`, `compiler/target/x64`, and `compiler/obj` construct deterministic MIR/LIR CFGs independent of worker order with structural validation preceding semantic verification (`AMIR-71..74`, `REQ-CORE-3041..3044`), emit deduplicated 8-byte-aligned read-only `.rdata` vtable symbols (`[drop_in_place, size, align, super_vtables..., method_0, ...]`) with 64-bit COFF `IMAGE_REL_AMD64_ADDR64` function relocations, pass and return 16-byte `(data_ptr, vtable_ptr)` fat pointers consistently under the Windows x64 ABI, and emit indirect vtable calls (`call [r_vtable + slot_offset]`) matching `--interp` (`0 WEAK-NATIVE`) (SPEC-63 AXS-DYN-010, AXS-DYN-020..023).
- source: 0212 §23, §47-48; tasks/0539 §89 AMIR-71..74; REQ-CORE-3041..3044, REQ-ABI-068; SPEC-04 AXS-EXT-044, AXS-EXT-071..073; SPEC-63 AXS-DYN-010, AXS-DYN-020..023
- verify: tests/mc/dyn, tests/run/dyn_native
- since: T567
- check: machine-code and differential (`--interp` and native) tests in tests/mc/dyn and tests/run/dyn_native (delivered by T567) verify `.rdata` vtable emission, 16-byte fat-pointer Win64 ABI passing/returning, and indirect method dispatch (`0 WEAK-NATIVE`)

### INV-DYN-003 — Owned `Box<dyn Trait>`, `view`/`mut_view` reborrowing, and vtable-driven `drop_in_place` + sized heap deallocation
- statement: `std/alloc/box.ax` and `compiler/mir/drop.ax` enter optimization only from `Verified MIR` while preserving semantic types, ownership, and capability invariants (`AMIR-75..78`, `REQ-CORE-3045..3048`), support unsizing `Box<T> -> Box<dyn Trait>` without reallocating or copying the pointee, support reborrowing `view(box_dyn) -> view<dyn Trait>` and `mut_view(box_dyn) -> mut_view<dyn Trait>`, and elaborate dynamic `Drop` on `Box<dyn Trait>` by invoking the vtable's `drop_in_place(data_ptr)` slot followed by `host.heap_free(data_ptr, vtable.size, vtable.align)` when `size > 0` (SPEC-63 AXS-DYN-011..012, AXS-DYN-024).
- source: 0212 §22-23, §48; tasks/0389 §68; tasks/0539 §89 AMIR-75..78; REQ-CORE-3045..3048; SPEC-12 AXS-DROP-001..007; SPEC-63 AXS-DYN-011..012, AXS-DYN-024
- verify: tests/run/dyn_box
- since: T568
- check: differential (`--interp` and native) tests in tests/run/dyn_box (delivered by T568) verify `Box<dyn Trait>` unsizing, heterogeneous `Vec<Box<dyn Trait>>` dispatch, `mut_view<dyn Trait>` reborrowing, and exact concrete destructor execution + heap deallocation on drop or overwrite (`0 WEAK-NATIVE`)

### INV-DYN-004 — End-to-end E14.4 `dyn Trait` object safety, fat-pointer coercion, `.rdata` vtable ABI, and dynamic `Drop` conformance
- statement: The E14.4 conformance suite certifies `dyn Trait` object-safety diagnostics (`AX_DYN_NOT_OBJECT_SAFE`), capability lifetime enforcement on `view<dyn Trait>` and `mut_view<dyn Trait>`, preservation of evaluation order and observable effects across storage-independent MIR (`AMIR-79..82`, `REQ-CORE-3049..3052`), heterogeneous `Vec<Box<dyn Trait>>` and slice-of-`view<dyn Trait>` dispatch, supertrait upcasting, and deterministic vtable-driven destructor order across `--interp` and native x86-64 (`-O0` and `-O1`) with `0 WEAK-NATIVE` (SPEC-63 AXS-DYN-001..052).
- source: SPEC-63 AXS-DYN-001..052; 0212; tasks/0476 §217.49-50; tasks/0539 §89 AMIR-60..82; REQ-CORE-3031..3052, REQ-PAT-015..020, REQ-ABI-068
- verify: tests/conformance/p14/e14_4_dyn_trait
- since: T569
- check: positive and negative conformance tests in tests/conformance/p14/e14_4_dyn_trait (delivered by T569) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 26. Windows x64 static `.lib` archives, PE32+ DLLs, and import libraries (SPEC-26)

### INV-WLIB-001 — Deterministic COFF static `.lib` archive writer (`--kind lib`), `-l`/`-L` search order, and demand-driven fixed-point archive extraction
- statement: `compiler/obj/` (`ArchiveWriter`) and `compiler/driver/` support `--kind exe|obj|lib|dll` (with `--emit=obj` as an alias for `--kind obj`), emit byte-for-byte deterministic COFF `.lib` archives (`!<arch>\n` magic, 60-byte headers with `Date = 0`, `UID = 0`, `GID = 0`, `Mode = 0`, big-endian First Linker Member, little-endian Second Linker Member with sorted symbols, and `//` longnames table), and `compiler/link/` resolves `-l<name>`, `-L<dir>`, and `@link("<name>")` in deterministic CLI order using demand-driven fixed-point archive extraction that excludes unreferenced members while diagnosing `AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_LIBRARY_NOT_FOUND`, and `AX_LINK_DUPLICATE_SYMBOL` (`SPEC-26` AXS-WLIB-001..012, AXS-WLIB-050).
- source: SPEC-26 AXS-WLIB-001..012, AXS-WLIB-050; SPEC-04 AXS-EXT-070..074, AXS-EXT-091; OWNER.md REQ-OWNER-006; 0185 §63 LINK-020..035; tasks/0356 §100; tasks/0369 §37; tasks/0562 §303.1; REQ-LNK-057..072, REQ-LNK-161..164, REQ-LNK-196..226, REQ-LNK-232..233
- verify: tests/link/lib
- since: T750
- check: linker tests in tests/link/lib (delivered by T750) verify `--kind lib` byte-for-byte determinism, linking against `.lib` archives, dead-member exclusion, and archive diagnostics

### INV-WLIB-002 — PE32+ `.dll` emission (`.edata`, synthesized `DllMain`, `.reloc`), companion COFF short-import `.lib`, and `__imp_<name>` resolution
- statement: `compiler/link/` (`PeImageWriter`) supports `--kind dll` (`IMAGE_FILE_DLL = 0x2000`, preferred `ImageBase = 0x180000000`, `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE = 0x0040`), emits a lexicographically sorted `.edata` Export Directory for `@export` items (while never exporting non-`@export` `pub` items and diagnosing `AX_LINK_DUPLICATE_EXPORT`), synthesizes `_DllMainCRTStartup` calling `__ax_resolve_module_bindings()` (`SPEC-56`) and module initializers on `DLL_PROCESS_ATTACH`, emits `.reloc` (`IMAGE_REL_BASED_DIR64`) blocks for all `ADDR64` relocations, simultaneously emits a companion COFF short-import `.lib` (`IMPORT_OBJECT_HEADER`, `Sig1 = 0x0000`, `Sig2 = 0xFFFF`), and consumes both short-import and traditional `.lib` import archives with standard `__imp_<name>` IAT symbol bindings (`SPEC-26` AXS-WLIB-020..032, AXS-WLIB-050).
- source: SPEC-26 AXS-WLIB-020..032, AXS-WLIB-050; SPEC-56 AXS-MOD-012..013; ADR-0001 §5-6; ADR-0034 §4 OI-07b; OWNER.md REQ-OWNER-006; 0186 APE-20..37; 0187 AIMPORT-20..27; tasks/0563 §304.2-3, §304.18-19; REQ-LNK-073..112, REQ-CORE-3087..3088
- verify: tests/link/dll
- since: T751
- check: linker and execution tests in tests/link/dll (delivered by T751) verify `--kind dll` + companion `.lib` generation, linking an `.exe` against the import `.lib`, `LoadLibraryA`/`GetProcAddress` execution, `DllMain` initialization, and `.reloc` base relocation

### INV-WLIB-003 — End-to-end E18.7 Windows `.lib` / `.dll` / import-library conformance and `ADR-0034` §4 OI-07b GNU `ld` cross-linking
- statement: The E18.7 conformance suite certifies static `.lib` creation and dead-member exclusion, PE32+ `.dll` + short-import `.lib` creation and consumption, dynamic runtime loading via `LoadLibraryA`/`GetProcAddress`, forced base relocation at a non-preferred `ImageBase` via `.reloc`, and `ADR-0034` §4 OI-07b independent cross-linking of `--kind obj` (`--emit=obj`) output with GNU `ld` / `gcc` using standard `__imp_<name>` and linkable runtime symbols (`SPEC-26` AXS-WLIB-001..053).
- source: SPEC-26 AXS-WLIB-001..053; ADR-0034 §4 OI-07b; OWNER.md REQ-OWNER-006; 0187 AIMPORT-28..34; 0188 AUNW-34; 0189 §28; REQ-LNK-113..121
- verify: tests/conformance/p18/e18_7_windows_artifacts
- since: T773
- check: conformance tests in tests/conformance/p18/e18_7_windows_artifacts (delivered by T773) pass end-to-end across static `.lib`, PE `.dll` + import `.lib`, forced `.reloc` rebasing, and GNU `ld` `--emit=obj` cross-linking

## 27. Demand-driven query engine, semantic database, cycle recovery, and snapshot-bound diagnostics (SPEC-21)

### INV-QRY-001 — `CompilerDB` input vs derived table separation, demand-driven `QueryStack` dependency DAG recording, and `inspect --emit=query-graph`
- statement: `compiler/query/db` partitions `CompilerDB` into revision-stamped immutable input tables (`SourceFileId`, `ModuleId`, `TargetConfig`, `PackageGraph`) and pure derived query tables (`parse_module`, `resolve_module`, `item_signature`, `typeck_body`, `mir_body`, `layout_of`) with zero process-global mutable state, evaluates derived queries strictly on demand (so unreferenced function bodies are not evaluated during signature-only checks), records caller->callee `DependencyEdge`s automatically from the active `QueryStack`, memoizes results stamped with `RevisionId`, and exposes deterministic `inspect --emit=query-graph` output sorted by canonical `SemanticKey` (`SPEC-21` AXS-QRY-001..013).
- source: SPEC-21 AXS-QRY-001..013; 0153 §3, §37 ACKERNEL-22, AQUERY-20..22; 0171 §3.4, §8, §40 AKERNEL-31..33; tasks/0384 §3; tasks/0530 §4-§6; tasks/0532; tasks/0533 §4
- verify: tests/run/query_db
- since: T753
- check: tests in tests/run/query_db (delivered by T753) verify input/derived table separation, demand-driven skipping of unreferenced function bodies, memoization hit/miss counters, and deterministic `inspect --emit=query-graph` output

### INV-QRY-002 — Deterministic active-stack query cycle detection, canonical `SemanticKey` rotation, fallback recovery values, snapshot-bound diagnostic replay, and revision invalidation
- statement: `compiler/query/engine` detects cyclic query dependencies on the active `QueryStack`, rotates every detected cycle to start at its lexicographically minimum `(QueryKind, SemanticKey)` node so cycle diagnostics (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`, `AX_QUERY_DEPTH_LIMIT`) are independent of entry query order, returns deterministic poisoned fallback values (`ErrorType`, `ConstValue.Poisoned`, `TraitResult.Error`) that suppress secondary cascading errors while allowing unrelated subgraphs to continue checking, binds emitted diagnostics to the producing `(SnapshotId, RevisionId)` memo entry for exact warm-hit replay, and invalidates transitive dependent queries across the recorded dependency DAG when input revisions advance (`SPEC-21` AXS-QRY-020..033, AXS-QRY-050).
- source: SPEC-21 AXS-QRY-020..033, AXS-QRY-050; 0153 §37 AQUERY-23..25, ADIAG-20..24; tasks/0530 §8; tasks/0781 §10-§11; tasks/0791 §10-§11
- verify: tests/run/query_cycles
- since: T754
- check: tests in tests/run/query_cycles (delivered by T754) verify canonical cycle rotation across entry orders, recovery fallback cascade suppression, warm-hit diagnostic replay, and input-revision transitive dirty invalidation

### INV-QRY-003 — End-to-end E18.1 demand-driven query engine & semantic database conformance
- statement: The E18.1 conformance suite certifies demand-driven query isolation across multi-module programs, identical canonical cycle diagnostics regardless of query invocation order, exact equivalence of semantic results and diagnostic sets between cold evaluation and warm memoized evaluation, and differential equivalence between `--interp` and native execution with `0 WEAK-NATIVE` (`SPEC-21` AXS-QRY-001..053).
- source: SPEC-21 AXS-QRY-001..053; 0153 §37 AQUERY-21..25; tasks/0530; tasks/0781; tasks/0791
- verify: tests/conformance/p18/e18_1_query_engine
- since: T755
- check: positive and negative conformance tests in tests/conformance/p18/e18_1_query_engine (delivered by T755) pass across cold and warm memoized runs and in `--interp` and native modes with `0 WEAK-NATIVE`

## 28. Incremental compilation, four-tier fingerprinting, red-green propagation, and persistent cache (SPEC-22)

### INV-INC-001 — Domain-separated 128-bit `Source`/`Ast`/`Interface`/`Abi`/`Body`/`Codegen` fingerprints, red-green `try_mark_green` propagation, and private-body firewall
- statement: `compiler/incremental/fingerprint` computes deterministic 128-bit domain-separated fingerprints (`SourceFingerprint`, comment/whitespace/span-insensitive `AstFingerprint`, exported `InterfaceFingerprint` and `AbiFingerprint`, `Verified MIR` `BodyFingerprint`, and monomorphized `CodegenFingerprint`), tracks cross-module `const`, generic, and inlined body edges, implements `try_mark_green` dependency verification and backdating over `CompilerDB` so editing a non-inlined private or public function body leaves `InterfaceFingerprint` green (`0` downstream `typeck` queries re-run) while signature or `@repr(C)` ABI edits propagate strictly to affected dependents (`REQ-CORE-3089`, `REQ-CORE-3090`), and exposes deterministic `inspect --emit=fingerprints` and `--emit=incremental-stats` telemetry (`SPEC-22` AXS-INC-001..013).
- source: SPEC-22 AXS-INC-001..013; 0142 §XXIII.16-24; 0152 §78-79; 0153 §18, §37 ACACHE-20..21; tasks/0564 §305.6-10; tasks/0778 §556.48-54, §556.141-151; tasks/0788 §566.15-32, §566.168-178; tasks/0792; REQ-CORE-3089, REQ-CORE-3090, REQ-LNK-634..713, REQ-LNK-1434..1603
- verify: tests/run/incremental_fingerprint
- since: T757
- check: tests in tests/run/incremental_fingerprint (delivered by T757) verify whitespace/comment fingerprint invariance, `0` downstream `typeck` queries re-run on private/body-only edits, targeted invalidation on signature/const/generic/ABI edits, and deterministic `--emit=fingerprints` / `--emit=incremental-stats` output

### INV-INC-002 — Persistent checksummed `.axiom-cache`, hermetic `EnvironmentDigest` key binding, corruption recovery, `< 100 ms` no-op fast path, and clean-build byte identity
- statement: `compiler/incremental/cache` persists the query dependency graph, item fingerprints, cached diagnostics, and content-addressed per-module `.obj` artifacts in versioned, BLAKE3-checksummed `.axcache` files published via atomic rename and keyed by `EnvironmentDigest` (compiler binary digest, target triple, CPU features, optimization/safety/panic profile, and manifest digest), transparently discards and rebuilds on schema mismatch or file corruption (`ACACHE-23..24`), executes a root manifest/content-digest fast path completing no-op workspace/compiler rebuilds in `< 100 ms`, and guarantees byte-identical `.obj`/`.exe` outputs and identical sorted diagnostics between incremental and clean `--no-incremental` builds (`ACACHE-20..24`, `SPEC-22` AXS-INC-020..024).
- source: SPEC-22 AXS-INC-020..024; 0142 §XXIII.25-28, §XXIII.53; 0153 §30, §37 ACACHE-20..24; tasks/0564 §305.11-13; tasks/0778 §556.190-200; tasks/0788 §566.1-14, §566.81-125, §566.180-200; tasks/0789; REQ-LNK-714..803, REQ-LNK-834..933
- verify: tests/run/incremental_cache
- since: T758
- check: tests in tests/run/incremental_cache (delivered by T758) verify cold-to-warm cache population, clean-vs-incremental `.obj`/`.exe` and diagnostic byte equivalence, corrupt/truncated cache recovery, and `< 100 ms` no-op rebuild

### INV-INC-003 — End-to-end E18.2 incremental compilation, edit-one-private-fn isolation, and `< 100 ms` no-op rebuild conformance
- statement: The E18.2 conformance suite certifies `< 100 ms` no-op rebuild of `axiomc` with zero re-executed semantic or codegen queries, single-module re-typechecking on private function body edits (`0` downstream modules re-typechecked), minimal dependent invalidation on public signature, `const`, or generic body edits with byte-identical binaries to clean rebuilds, and differential equivalence across `--interp`, clean native, and incremental native builds with `0 WEAK-NATIVE` (`SPEC-22` AXS-INC-001..053).
- source: SPEC-22 AXS-INC-001..053; 0142; 0152 §78-79; 0153 §37 ACACHE-20..24; tasks/0564; tasks/0778; tasks/0788; tasks/0789; tasks/0792; REQ-LNK-804..833, REQ-LNK-1604..1633
- verify: tests/conformance/p18/e18_2_incremental
- since: T759
- check: conformance tests in tests/conformance/p18/e18_2_incremental (delivered by T759) pass across `--interp`, clean native, and incremental native modes with `0 WEAK-NATIVE`

## 29. Parallel compilation, thread-safe snapshots, work-stealing DAG scheduling, and deterministic post-join merging (SPEC-23)

### INV-PAR-001 — Thread-safe immutable `DatabaseSnapshot` sharing, `(ModuleId, LocalIndex)` semantic IDs, sharded interner, `SingleFlightLatch` + cross-worker `WaitForGraph` cycle detection, and `--jobs N` work-stealing scheduler
- statement: `compiler/parallel/scheduler` executes frontend and middle-end queries across `--jobs <N>` worker threads over immutable `DatabaseSnapshot`s (`ACOMPARCH-20..60`, `AQUERY-51..80`), assigns thread-count-independent `(ModuleId, LocalIndex)` semantic IDs and content-addressed sharded string/type intern IDs without racing on sequential global counters, deduplicates concurrent in-flight queries via `SingleFlightLatch` with deadlock-free cross-worker `WaitForGraph` cycle detection and canonical `SemanticKey` rotation (`AQUERY-51`), and schedules DAG actions by critical-path priority and resource tokens (`cpu_cost`, `memory_cost`) without uncontrolled nested thread pools (`SPEC-23` AXS-PAR-001..015).
- source: SPEC-23 AXS-PAR-001..015; 0153 §19, §37 APAR-20..22, ACKERNEL-21, AINTERN-20..23; tasks/0528 §115, §131, §134 ACOMPARCH-20..60; tasks/0530 §127-148, §163 AQUERY-50..80; tasks/0593 §1-24, §41-56, §334; tasks/0790 §568.1-100; REQ-CORE-2669..2711, REQ-CORE-3125, REQ-CORE-3126, REQ-TOOL-224..254, REQ-LNK-1034..1133
- verify: tests/run/parallel_scheduler
- since: T761
- check: tests in tests/run/parallel_scheduler (delivered by T761) verify parallel lex/parse/resolve/typeck across multi-module workspaces, cross-worker cycle detection, and identical HIR/MIR dumps under `--jobs 1`, `--jobs 2`, and `--jobs 8`

### INV-PAR-002 — Parallel per-module / per-`CGU` LIR lowering and object emission, hybrid incremental cache integration, and deterministic post-join diagnostic/artifact merging
- statement: `compiler/parallel/codegen` partitions `Verified MIR` / `OptIR` into canonical Codegen Units (`CGU`s), reuses clean cached `.obj` artifacts via `CodegenFingerprint` while executing dirty `CGU` LIR lowering, register allocation, machine encoding, and COFF `.obj` emission in parallel across worker threads, merges per-worker diagnostic buffers in canonical `AXD-060` order (`(FileId, primary.start, code_ordinal)`), and feeds per-`CGU` `.obj` buffers to `compiler/link/` in strict canonical `CGU` index order (`SPEC-23` AXS-PAR-020..024).
- source: SPEC-23 AXS-PAR-020..024; 0153 §37 APAR-23..24; tasks/0473 §214.24-33 ACOMPILER-30..33; tasks/0528 ACOMPARCH-37..44; tasks/0593 §16-19, §23-40; tasks/0789 §567.101-170; tasks/0790 §568.101-170; REQ-DRV-018, REQ-LNK-934..1003, REQ-LNK-1134..1203
- verify: tests/run/parallel_codegen
- since: T762
- check: tests in tests/run/parallel_codegen (delivered by T762) verify that `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` produce byte-identical `.obj` and `.exe` binaries and identical diagnostic streams

### INV-PAR-003 — End-to-end E18.3 parallel compilation thread-count invariance and byte-identical determinism conformance
- statement: The E18.3 conformance suite certifies byte-identical `.obj`/`.exe` outputs and identical HIR/MIR/LIR dumps across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8`, identical multi-file error and warning diagnostic ordering under randomized worker scheduling delays, combined parallel + incremental rebuild determinism, and differential equivalence between `--interp` and parallel native builds with `0 WEAK-NATIVE` (`SPEC-23` AXS-PAR-001..053).
- source: SPEC-23 AXS-PAR-001..053; 0153 §37 APAR-20..24; tasks/0473 ACOMPILER-30..33; tasks/0528; tasks/0530; tasks/0593; tasks/0789 §567.171-200; tasks/0790 §568.171-200; REQ-LNK-1004..1033, REQ-LNK-1204..1233
- verify: tests/conformance/p18/e18_3_parallel
- since: T763
- check: conformance tests in tests/conformance/p18/e18_3_parallel (delivered by T763) pass across `--jobs 1`, `--jobs 2`, `--jobs 4`, and `--jobs 8` and in `--interp` and native modes with `0 WEAK-NATIVE`

## 30. Canonical artifact format, module interfaces (`.axmi`), and embedded object/LTO sections (SPEC-24)

### INV-ART-001 — Deterministic `.axmi` module interface serialization, source-free `CompilerDB` ingestion, and exported generic/capability/const summaries
- statement: `compiler/artifact/axmi` emits and loads byte-deterministic `.axmi` module interface artifacts (`ArtifactHeader`, `SectionDescriptor[]`, BLAKE3-128 `content_hash`, zero pointers/timestamps) containing exported item signatures, canonical nominal `TypeId` tables, trait/impl coherence records, interprocedural ownership/capability/effect/panic/concurrency summaries (`tasks/0582`), evaluated `const` payloads, and pre-verified generic/`@inline`/`comptime` MIR templates (`tasks/0739`), populates `CompilerDB` directly from `.axmi` so downstream modules compile and instantiate generics without reading upstream `.ax` source files, and exposes `--emit=axmi` and `inspect --axmi <file>` (`SPEC-24` AXS-ART-001..014, AXS-ART-050).
- source: SPEC-24 AXS-ART-001..014, AXS-ART-050; SPEC-04 AXS-EXT-070..074; tasks/0582 §323.1-20; tasks/0591 §1-12; tasks/0739 §493.1-30; tasks/0787 §565.1-140; REQ-CORE-3109, REQ-CORE-3110, REQ-CORE-3123, REQ-CORE-3124, REQ-LNK-434..573
- verify: tests/run/artifact_axmi
- since: T765
- check: tests in tests/run/artifact_axmi (delivered by T765) compile an upstream module to `.axmi` + `.obj`, remove/hide the upstream `.ax` source, and compile a downstream consumer using only `.axmi` + `.obj` across generics, traits, capabilities, and `const` items

### INV-ART-002 — Embedded non-alloc `.axmeta` / `.axlto` COFF object sections, schema/target/checksum validation, and final `.exe`/`.dll` stripping
- statement: `compiler/artifact/container` and `compiler/obj/` embed non-alloc discardable `.axmeta` and `.axlto` (`IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE`) sections into COFF `.obj` and `.lib` artifacts carrying the module's `InterfaceFingerprint`, `AbiFingerprint`, `TargetFingerprint`, and LTO `Verified MIR` summary, validate magic, `schema_version`, target/ABI compatibility, bounds, and BLAKE3 checksums on load (diagnosing `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, and `AX_LINK_ARTIFACT_TARGET_MISMATCH`), and strip all `.axmeta`/`.axmir`/`.axlto` sections when linking final `.exe` and `.dll` images (`SPEC-24` AXS-ART-020..024, AXS-ART-050).
- source: SPEC-24 AXS-ART-020..024, AXS-ART-050; SPEC-04 AXS-EXT-071; 0164; tasks/0591; tasks/0739; tasks/0787 §565.141-180; tasks/0803 §581.1-110; REQ-LNK-574..613, REQ-LNK-3634..3743
- verify: tests/run/artifact_container
- since: T766
- check: tests in tests/run/artifact_container (delivered by T766) verify `.axmeta`/`.axlto` embedding in `.obj`, round-trip extraction, rejection of corrupted or mismatched-schema/target sections with `AX_LINK_*` diagnostics, and stripping from final `.exe`

### INV-ART-003 — End-to-end E18.4 `.axmi` module interface, `.axmeta`/`.axlto` container section, and source-free separate-compilation conformance
- statement: The E18.4 conformance suite certifies multi-module separate compilation using `.axmi` and embedded `.axmeta`/`.axlto` sections without upstream `.ax` source files across generics, traits, capabilities, and `const` items, byte-identical `.axmi` and `.obj` emission across repeated runs, deterministic `AX_LINK_BAD_ARTIFACT` / `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` / `AX_LINK_ARTIFACT_TARGET_MISMATCH` rejection on corrupt, wrong-schema, or wrong-target artifacts, and differential equivalence between `--interp` and native execution with `0 WEAK-NATIVE` (`SPEC-24` AXS-ART-001..053).
- source: SPEC-24 AXS-ART-001..053; tasks/0739; tasks/0787 §565.181-200; tasks/0803 §581.111-200; REQ-LNK-614..633, REQ-LNK-3744..3784
- verify: tests/conformance/p18/e18_4_artifacts
- since: T767
- check: positive and negative conformance tests in tests/conformance/p18/e18_4_artifacts (delivered by T767) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 31. Pass contracts, proof-carrying transformations, and bounded translation validation (SPEC-25)

### INV-PCT-001 — Formal `PassContract` registry, `ProofCertificate` / `ProofProvenance` invalidation on IR mutation, three-valued `Certainty` (`Proven` / `Possible` / `Unknown`), and fail-closed rollback gate
- statement: `compiler/verify/pass_contracts` registers machine-readable `PassContract` descriptors (IR level, required analyses, required propositions, preserved analyses, invalidated analyses, preserved semantic properties, and postcondition predicates) for compiler passes (`tasks/0545`, `tasks/0578`, `tasks/0797`), attaches `ProofCertificate` records carrying `ProofProvenance` and `ir_revision` across shared dataflow (`tasks/0793`), three-valued static certainty (`Proven` / `Possible` / `Unknown`, `tasks/0794`), canonical multi-category `EffectSummary` (`tasks/0795`), and in-process bounded symbolic execution (`tasks/0796`), automatically invalidates dependent proof certificates when underlying IR definitions mutate, rolls back any candidate transformation whose proof obligation evaluates to `Possible` or `Unknown` without emitting a user error, and enforces pre/postcondition verification under `--verify-pass-contracts` (`SPEC-25` AXS-PCT-001..015, AXS-PCT-050).
- source: SPEC-25 AXS-PCT-001..015, AXS-PCT-050; SPEC-70 AXS-OPT-001..006, AXS-OPT-030..034; tasks/0545 §1-42 APROOF-20..65, AOPTGATE-20..40; tasks/0578 §319.1-34 APASS-01..40; tasks/0793 §571.1-200; tasks/0794 §572.1-200; tasks/0795 §573.1-200; tasks/0796 §574.1-200; tasks/0797 §575.1-200; REQ-CORE-3107..3108, REQ-CORE-3192..3285, REQ-LNK-1634..2633
- verify: tests/run/pass_contracts
- since: T769
- check: tests in tests/run/pass_contracts (delivered by T769) verify `PassContract` pre/postcondition checking, automatic invalidation of dependent `ProofCertificate`s on IR mutation, and fail-closed rollback when a required proof is `Unknown`

### INV-PCT-002 — Per-function bounded `TranslationWitness` validation across MIR, `OptIR`, LIR, register allocation, and instruction scheduling (`--validate-translations`, `inspect --emit=pass-witness`)
- statement: `compiler/verify/translation_val` validates per-function `TranslationWitness` equivalence across scalar/algebraic rewrites, CFG canonicalization (`tasks/0798`), target legalization (`tasks/0799`), register allocation live-range interference and spill/reload dominance (`tasks/0799`), instruction scheduling `RAW`/`WAR`/`WAW` dependency and `volatile`/`atomic`/`trap` barrier preservation (`tasks/0800`), and final Machine IR resolution (`tasks/0801`), exposes `--validate-translations` and `inspect --emit=pass-witness` (`tasks/0577`, `tasks/0578`), and deterministically rejects synthetic pass bugs (dropped overflow check, clobbered live register, or reordered `volatile` load) (`SPEC-25` AXS-PCT-020..024, AXS-PCT-050).
- source: SPEC-25 AXS-PCT-020..024, AXS-PCT-050; SPEC-77 AXS-RA-010..027, AXS-MCOPT-001..026; tasks/0545; tasks/0577 §318.1-33 ACORR-01..40; tasks/0578; tasks/0798 §576.1-200; tasks/0799 §577.1-200; tasks/0800 §578.1-200; tasks/0801 §579.1-150; REQ-CORE-3105..3106, REQ-LNK-2634..3383
- verify: tests/run/translation_val
- since: T770
- check: tests in tests/run/translation_val (delivered by T770) verify witness validation across MIR, `OptIR`, LIR, regalloc, and scheduling passes and confirm injected synthetic pass bugs (dropped overflow check, clobbered live register, reordered `volatile` load) are caught deterministically

### INV-PCT-003 — End-to-end E18.5 pass contracts, proof-carrying transformations, fail-closed rollback, and translation validation conformance
- statement: The E18.5 conformance suite certifies that `--verify-pass-contracts` and `--validate-translations` succeed cleanly across `-O0`, `-O1`, and `-O2`, preserve overflow, signed/unsigned comparison, deterministic `Drop`, `atomic`, `volatile`, and capability invariants across all passes (`tasks/0796`, `tasks/0797`), and maintain differential equivalence between `--interp` and native execution with `0 WEAK-NATIVE` (`SPEC-25` AXS-PCT-001..053).
- source: SPEC-25 AXS-PCT-001..053; tasks/0545; tasks/0577; tasks/0578; tasks/0796; tasks/0797; tasks/0801 §579.151-200; REQ-LNK-3384..3433
- verify: tests/conformance/p18/e18_5_pass_contracts
- since: T771
- check: positive and negative conformance tests in tests/conformance/p18/e18_5_pass_contracts (delivered by T771) pass across `-O0`, `-O1`, and `-O2` in `--interp` and native modes with `0 WEAK-NATIVE`

## 32. Separate compilation, multi-object `LinkIR` linking, `COMDAT` deduplication, and section GC (SPEC-27)

### INV-LNK-001 — Per-module separate compilation (`.obj` + `.axmi`), `LinkIR` multi-object & `.lib` archive linking, cross-object relocation patching, and demangled linker diagnostics
- statement: `compiler/driver` and `compiler/link` compile each module in a multi-module project to its own `.obj` + `.axmi` (enforcing trait orphan coherence `REQ-LNK-122`, canonical `TypeId` interning `REQ-LNK-140`, separated `FrameLayout` vs prologue/epilogue emission `REQ-LNK-123..131`, and pure deterministic `Machine Code Encoding 4.0` `REQ-LNK-3434..3633`), ingest multiple `.obj` files and `.lib` archives in deterministic canonical order into format-neutral `LinkIR`, resolve `Strong`, `Weak`, `Local`, and `Import` symbols without language-level AST/HIR/MIR coupling (`INV-LAYER-002`, `REQ-LNK-001..003`), patch `ADDR64`, `REL32`, and section-relative `.pdata`/`.xdata` relocations with strict range checks (`AX_LINK_RELOC_OUT_OF_RANGE`), and emit structured `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`, and `AX_LINK_ABI_MISMATCH` diagnostics carrying demangled Axiom paths (`data.demangled`) and `.axmeta` source spans (`SPEC-27` AXS-LNK-001..014, AXS-LNK-024..025, AXS-LNK-050).
- source: SPEC-27 AXS-LNK-001..014, AXS-LNK-024..025, AXS-LNK-050; 0099; 0164 §1-41; 0217; 0225 §31; 0236 §1-28; 0239 §1-32; 0245 §3-27; 0256 §1-42; tasks/0369; tasks/0786 §564.1-32, §564.65-90, §564.165-171; tasks/0802 §580.1-200; tasks/0803; tasks/0804 §582.1-31, §582.63-94, §582.158-171; REQ-LNK-001..056, REQ-LNK-122..160, REQ-LNK-228..433, REQ-LNK-3434..3633, REQ-LNK-3785..3884, REQ-LNK-3984..3993
- verify: tests/link2
- since: T067
- check: multi-object and archive link tests in tests/link2 (delivered by T067) verify separate per-module `.obj` compilation and linking, byte-identical rebuilds, and structured duplicate/undefined/ABI-mismatch diagnostics with demangled symbol names

### INV-LNK-002 — Per-item section subdivision, `IMAGE_SCN_LNK_COMDAT` generic/vtable deduplication, root-set mark-sweep section GC (`--gc-sections`), and `inspect --emit=link-map` / `--emit=gc-sections`
- statement: `compiler/obj/` and `compiler/link/gc` emit each function and datum into its own section / `COMDAT` group (`.text$<sym>`, `.rdata$<sym>`, `.data$<sym>`, `.bss$<sym>`, and `IMAGE_COMDAT_SELECT_ASSOCIATIVE` `.pdata$<sym>` / `.xdata$<sym>`), deterministically fold duplicate monomorphized generic instantiations and vtables across separate `.obj` files (`IMAGE_SCN_LNK_COMDAT`), perform mark-sweep reachability garbage collection (`--gc-sections`) from `@entry`/`main`/`DllMain`, `@export`, `@used`, `@at` fixed-address roots, module initializers, and runtime reflection roots to strip unreferenced code/data and their associated `.pdata`/`.xdata` unwind entries, and expose deterministic `inspect --emit=link-map` and `inspect --emit=gc-sections` reports (`SPEC-27` AXS-LNK-013, AXS-LNK-020..023, AXS-LNK-050).
- source: SPEC-27 AXS-LNK-013, AXS-LNK-020..023, AXS-LNK-050; SPEC-75 AXS-LTO-014, AXS-LTO-020..022; 0164; tasks/0409; tasks/0410; tasks/0526; tasks/0786 §564.33-64; tasks/0804 §582.19-21, §582.32-48, §582.114, §582.146-155; REQ-CORE-592..601, REQ-CORE-2541..2643, REQ-LNK-227, REQ-LNK-3885..3944
- verify: tests/run/link_section_gc
- since: T775
- check: tests in tests/run/link_section_gc (delivered by T775) verify that importing a single function from `std` or a multi-module library strips unreferenced functions/statics and their unwind records from the final `.exe`/`.dll`, folds duplicate generic instantiations across separate `.obj` files, and preserves `@export`/`@used` roots

### INV-LNK-003 — End-to-end E18.6 separate compilation, multi-object archives, `COMDAT` deduplication, section GC & P18 exit conformance
- statement: The E18.6 conformance suite certifies that multi-module workspaces compiled separately to `.obj` + `.axmi` and linked with `.lib` and `.dll` artifacts produce byte-identical executables to whole-workspace builds, `COMDAT` deduplication and section GC strip unused library code while preserving all live/exported/unwind sections, editing one private function in a multi-module separate-compilation project re-typechecks and re-emits only that module's `.obj` (with `< 100 ms` no-op rebuild on the compiler itself), and `--interp` and native execution agree with `0 WEAK-NATIVE` (`SPEC-27` AXS-LNK-001..053).
- source: SPEC-27 AXS-LNK-001..053; 0099; 0164; 0217; tasks/0369; tasks/0526; tasks/0786; tasks/0804 §582.172-200; REQ-LNK-3945..3983
- verify: tests/conformance/p18/e18_6_separate_compilation
- since: T776
- check: positive and negative conformance tests in tests/conformance/p18/e18_6_separate_compilation (delivered by T776) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 33. Loop & SLP auto-vectorization, capability-disjoint dependence proving, and target SIMD cost modeling (SPEC-74)

### INV-VEC-001 — Annotation-free loop auto-vectorization (`opt_loop_vec`), capability-disjoint dependence proving (`mut_view` vs `view`), reduction legality, and scalar epilogue fallback
- statement: `compiler/opt/vectorize` (`opt_loop_vec`) automatically vectorizes eligible counted canonical loops on `OptIR` before LIR lowering without requiring source annotations (`REQ-OPT-013`), consumes `AliasInfo` capability disjointness (`mut_view<[T]>` vs `view<[T]>`) and `SCEV` distance proofs to establish zero loop-carried memory dependency (`REQ-OPT-148..149`) while never assuming `UnknownAlias`/`MayAlias` is `NoAlias` (`REQ-OPT-150`), enforces hard barriers on `Atomic<T>` (`REQ-OPT-151`) and `Volatile<T>` (`REQ-OPT-152`), preserves strict IEEE-754 floating-point ordering by default while vectorizing associative (`wrapping_*`, bitwise, `min`/`max`, proven `NoOverflow`, or explicit associative) reductions (`REQ-OPT-153..154`, `REQ-OPT-206`), selects target-legal vector widths (`128`-bit `SSE2` baseline or `256`-bit `AVX2` when enabled, `REQ-OPT-209..211`), and emits a scalar remainder epilogue loop preserving exact scalar semantics for all trip counts (`REQ-OPT-191`, `SPEC-74` AXS-VEC-001..035, AXS-VEC-044).
- source: SPEC-74 AXS-VEC-001..035, AXS-VEC-044; 0095; 0162 §31; tasks/0402 §32-39, §80 AVEC-20..26, ALOOP-65; tasks/0403 §30-47, §82 ASIMD-38..56; tasks/0406 §30 AMICRO-29, 32..34; tasks/0407 §1-35 AVEC-20..47; REQ-OPT-013, REQ-OPT-148..154, REQ-OPT-191, REQ-OPT-206, REQ-OPT-209..211
- verify: tests/run/opt_loop_vec
- since: T617
- check: differential execution and dump tests in tests/run/opt_loop_vec (delivered by T617) verify automatic loop vectorization across arbitrary trip counts (including scalar epilogue execution) and conservative scalar retention on loop-carried dependencies, unknown aliasing, atomics, volatiles, and strict FP reductions

### INV-VEC-002 — Straight-line `SLP` pack-tree vectorization (`opt_slp_vec`), target-aware `VectorCostModel` profitability, and `OptIR` → LIR `Vec128`/`Vec256` lowering
- statement: `compiler/opt/slp` (`opt_slp_vec`) discovers isomorphic straight-line basic-block pack trees seeded from contiguous struct-field or array-element stores and reductions while verifying DAG acyclicity and `MemorySSA` independence without fabricating safety or `NoAlias` proofs (`REQ-OPT-215..217`), `VectorCostModel` evaluates vector throughput, pack/extract overhead, setup/epilogue cost, and register pressure on the declared target profile without leaking CPU profiles into Core language semantics (`REQ-OPT-213..214`), and `compiler/lir/vec_lower` lowers vectorized `OptIR` operations to canonical `LirType.V128`/`V256` (`Vec128`/`Vec256`) instructions with `VZEROUPPER` hygiene (`SPEC-74` AXS-VEC-036..050).
- source: SPEC-74 AXS-VEC-036..050; 0095; 0162 §30-31; tasks/0403 §32-33, §57-60, §82 ASIMD-55, 57..58; tasks/0406 §30 AMICRO-21..25, 36..40; tasks/0407 §7-10, §58-61, §35 AVEC-26..29; SPEC-43 AXS-SBE-001..022; REQ-OPT-213..217
- verify: tests/run/opt_slp_vec
- since: T618
- check: differential execution and LIR/machine dump tests in tests/run/opt_slp_vec (delivered by T618) verify `SLP` packing of 2-, 4-, and 8-lane adjacent field/array operations into `XMM`/`YMM` instructions and verify cost-model rejection of unprofitable scatter/gather packs

### INV-VEC-003 — End-to-end E15.5 loop & `SLP` auto-vectorization equivalence and `Source → MIR → OptIR → LIR → Machine` provenance conformance
- statement: The E15.5 conformance suite certifies exact numerical, memory, and panic equivalence between `--interp` and native `-O0`/`-O1`/`-O2` builds across `i8..i64`, `u8..u64`, `f32`, and `f64` loop and `SLP` kernels for zero, unit, prime, aligned, and unaligned lengths, isolates target-specific vectorization from Core language semantics (`REQ-OPT-219`), fails closed under cost/alias uncertainty (`REQ-OPT-220`), and preserves inspectable `Source → MIR → OptIR → LIR → Machine` provenance and structured vectorization explanations (`inspect --emit=vectorize` / `--emit=vector-cost`, `REQ-OPT-221..222`, `SPEC-74` AXS-VEC-001..053).
- source: SPEC-74 AXS-VEC-001..053; tasks/0402; tasks/0403 §80-82 ASIMD-69, 71..72; tasks/0406 §28-30 AMICRO-42..45; tasks/0407 §34-35 AVEC-45..47; REQ-OPT-219..222
- verify: tests/conformance/p15/e15_5_autovec
- since: T619
- check: positive and negative conformance tests in tests/conformance/p15/e15_5_autovec (delivered by T619) pass in `--interp` and native modes with `0 WEAK-NATIVE`

## 34. Linux x86-64 System V AMD64 ABI, ELF64 object/archive emission, static ELF64 linking, and `std.sys.linux` syscall host interface (SPEC-80)

### INV-ELFS-001 — `CallConv.SysV64` ABI lowering, deterministic ELF64 relocatable object (`ET_REL`) & GNU `ar` (`.a`) emission, and static ELF64 executable (`ET_EXEC`) linking
- statement: `compiler/abi/sysv64`, `compiler/obj/elf`, and `compiler/link/elf` reuse the shared x86-64 instruction selector, register allocator, and encoder while lowering `CallConv.SysV64` (`RDI, RSI, RDX, RCX, R8, R9`, `XMM0..XMM7`, eightbyte `INTEGER`/`SSE`/`MEMORY` aggregate classification, hidden `sret` in `RDI` returned in `RAX`, dual-register 16-byte returns in `RAX:RDX` / `XMM0:XMM1`, callee-saved `RBX, RBP, R12..R15`, 16-byte stack alignment before `call`, and 128-byte leaf red zone disabled under `-mno-red-zone` or `freestanding`/`kernel` profiles; `REQ-TGT-037..043`), emit byte-deterministic ELF64 `ET_REL` `.o` objects (`.text`, `.rodata`, `.data`, `.bss`, `.symtab`, `.strtab`, `.shstrtab`, `.rela.*` with `R_X86_64_64`, `R_X86_64_PC32`, `R_X86_64_PLT32`, `R_X86_64_32`, `R_X86_64_32S`, and `SHN_ABS` for `@at`) and GNU `ar` `.a` archives without an external assembler (`REQ-TGT-059..060`, `REQ-TGT-101`, `REQ-TGT-103..104`), and link static `ET_EXEC` binaries at base `0x400000` with 4 KiB page-aligned W^X `PT_LOAD` (`RX`, `R`, `RW`) segments and `_start` → `main` → `SYS_exit_group = 231` without `libc` or external `ld` (`SPEC-80` AXS-ELFS-001..039).
- source: SPEC-80 AXS-ELFS-001..039; 0053; 0163 §1-7; 0164; 0192 §1-29 AELF-20..40; 0217; 0255; 0256; tasks/0369; tasks/0471 AKERNEL-20..27; tasks/0518 AMACHINE-48..54, AMACHINE-70..71, AMACHINE-112, AMACHINE-114..115; tasks/0563; REQ-TGT-002..003, REQ-TGT-037..043, REQ-TGT-059..060, REQ-TGT-101, REQ-TGT-103..104
- verify: tests/run/linux, tests/selfhost/abi, tests/selfhost/obj, tests/selfhost/link
- since: T066
- check: unit and execution tests in tests/run/linux, tests/selfhost/abi, tests/selfhost/obj, and tests/selfhost/link (delivered by T066) verify SysV64 ABI classification, ELF64 `ET_REL` and `ET_EXEC` binary layout, relocation patching, round-trip object reading/writing, and byte-identical output

### INV-ELFS-002 — `std.sys.linux` raw Linux x86-64 syscall host interface (`AXS-EXT-110`), deterministic `-errno` mapping, and WSL test runner integration
- statement: `std/sys/linux` and `compiler/driver/target_linux` implement the complete `SPEC-04 AXS-EXT-110` host-interface surface using direct Linux x86-64 `syscall` (`0F 05`, args in `RDI, RSI, RDX, R10, R8, R9`) instructions (`SYS_mmap`/`SYS_mremap`/`SYS_munmap`, `SYS_openat`/`SYS_read`/`SYS_write`/`SYS_close`/`SYS_fstat`, `SYS_unlinkat`/`SYS_mkdirat`/`SYS_newfstatat`/`SYS_getdents64`, `SYS_readlinkat` on `/proc/self/exe` and `_start` stack `argc`/`argv`/`envp`, `SYS_clock_gettime`, `SYS_clone`/`SYS_futex`/`SYS_nanosleep`/`SYS_sched_yield`, `io_uring`/`epoll`, and `SYS_exit_group`), map kernel `-errno` values deterministically to negated host error kinds (`-1`..`-5`, `-9`) without requiring hosted runtime machinery in `freestanding`, GC, reference counting, object headers, or surface pointer syntax (`REQ-TGT-096..100`), and `tools/axtest.py` executes `--target x86_64-linux` binaries natively on Linux or via `wsl` on Windows (`SPEC-80` AXS-ELFS-040..049).
- source: SPEC-80 AXS-ELFS-040..049; SPEC-04 AXS-EXT-110; 0192 §21-23 AELF-33, AELF-35..36; 0220; tasks/0518 AMACHINE-107..111; REQ-TGT-096..100
- verify: tests/run/linux_std, tests/selfhost/driver
- since: T651
- check: tests in tests/run/linux_std and tests/selfhost/driver (delivered by T651) verify `Vec`, `String`, `HashMap`, `fs`, `io`, `process`, `time`, threads, and UTF-8 `Xin chào thế giới` execution under `--target x86_64-linux`

### INV-ELFS-003 — End-to-end E16.9 Linux x86-64 static ELF64, System V AMD64 ABI, and `--interp` vs native WSL/Linux differential conformance
- statement: The E16.9 conformance suite certifies `CallConv.SysV64` register/stack argument passing, eightbyte aggregate classification (`INTEGER`, `SSE`, `MEMORY` / `sret`), dual-register 16-byte returns, callee-saved register preservation (`RBX, RBP, R12..R15`), 16-byte stack alignment, leaf red-zone policy, ELF64 `ET_REL` and `ET_EXEC` structural validity and byte-for-byte determinism, optional diagnostic assembly dumps (`REQ-TGT-102`), `TargetDesc`-driven target selection (`REQ-TGT-105..106`), target-independent LIR lowering (`REQ-TGT-111..112`), and exact differential agreement between `--interp` and `--target x86_64-linux` native execution (`0 WEAK-NATIVE`, `SPEC-80` AXS-ELFS-001..053).
- source: SPEC-80 AXS-ELFS-001..053; 0053; 0192 §25-31 AELF-20..40, ELF-BOOT-001..012; 0255; 0256; tasks/0518 AMACHINE-113, AMACHINE-116..117; tasks/0520 §13; REQ-TGT-102, REQ-TGT-105..106, REQ-TGT-111..112
- verify: tests/conformance/p16/e16_9_linux_x64_static
- since: T652
- check: positive and negative conformance tests in tests/conformance/p16/e16_9_linux_x64_static (delivered by T652) pass across `--interp` and `--target x86_64-linux` with `0 WEAK-NATIVE`

## 35. Declarative `TargetDesc`, `RegisterFile`, `IsaTable`, `Legalizer`, pre-encoding `verify_mc`, and target-independent LIR backend conformance (SPEC-81)

### INV-TGTD-001 — Declarative `TargetDesc` registry, 128-bit `TargetFingerprint`, hierarchical `RegisterFile` `RegUnit`/alias tables, `TargetFeatureSet` implication DAG, and table-driven `CallConvDesc` ABI engine
- statement: `compiler/target/desc` and `compiler/abi/table` define every target (`x86_64-windows`, `x86_64-linux`, `aarch64-linux`, `aarch64-macos`, `aarch64-android`, `aarch64-windows`, `wasm32`, `riscv64-linux`) as static declarative `TargetDesc` data computing a deterministic 128-bit `TargetFingerprint`, separate virtual registers and physical stack slots from semantic variables (`AMACHINE-23..24, 28..30`, `REQ-TGT-012..013, 017..019`), model target register classes, `RegUnit` overlap bitmasks, subregister/superregister aliases (`RAX`/`EAX`/`AX`/`AL`/`AH`, `ZMM`/`YMM`/`XMM`, `X0`/`W0`, `Q0`/`D0`/`S0`), reserved architectural registers (`RSP`, `SP`, `XZR`, `X18`, `x0`, `gp`, `tp`), and target addressing modes without leaking them into Core semantics (`AMACHINE-25..27, 31..32`, `REQ-TGT-014..016, 020..021`), enforce compile-time `TargetFeatureSet` implication DAG legality without hidden runtime CPU dispatch (`AMACHINE-65..67`, `REQ-TGT-004, 054..056`), and drive ABI classification via declarative `CallConvDesc` tables (`SPEC-81` AXS-TGTD-001..023).
- source: SPEC-81 AXS-TGTD-001..023; SPEC-04 AXS-EXT-050..052, AXS-EXT-060..062, AXS-EXT-070; 0163 §1-7; tasks/0472 §213.1-5, §213.95 AHW-20..24; tasks/0518 §5-23, §38-43, §96-97, §151 AMACHINE-23..32, AMACHINE-65..67; tasks/0524 §5-6, §28-40; tasks/0784 §562.2-16, §562.29-39, §562.60-64; REQ-TGT-004..005, REQ-TGT-007..008, REQ-TGT-012..021, REQ-TGT-054..056
- verify: tests/run/target_desc, tests/selfhost/abi
- since: T654
- check: unit and execution tests in tests/run/target_desc and tests/selfhost/abi (delivered by T654) verify `TargetDesc` lookup, `TargetFingerprint` determinism, `RegUnit` overlap and subregister alias symmetry, reserved vs allocatable register disjointness, `TargetFeatureSet` implication/conflict rules, and `CallConvDesc` ABI classification

### INV-TGTD-002 — Declarative `IsaTable` instruction descriptors, semantic-preserving `Legalizer` expansions, and mandatory pre-encoding `verify_mc` Machine IR verification
- statement: `compiler/target/isa` and `compiler/backend/verify_mc` define pattern-based instruction descriptors (`IsaTable` operand constraints, immediate predicates, addressing modes, explicit implicit register uses/defs `RAX:RDX`/`RCX`/call clobbers, flags vs flagless condition-code dependencies, and latency/throughput optimization hints that never alter language semantics; `AMACHINE-33..34, 46..47, 55..64`, `REQ-TGT-006, 022..023, 035..036, 044..053`), legalize unsupported `LIR` operations while strictly preserving integer overflow traps, strict IEEE-754 floating-point semantics (unless `@fast_math` is explicitly authorized), atomic/volatile/memory-ordering semantics (never silently lowering atomics to ordinary loads/stores), and explicit `Panic` vs hardware `TrapBehavior` separation (`AMACHINE-35..45`, `ABACKEND-64..70`, `REQ-TGT-024..034, 289..295`), and verify every `MachineFunction` in `verify_mc` before encoding so invalid Machine IR never reaches the binary encoder (`AMACHINE-68..69, 119..120`, `ABACKEND-81`, `REQ-TGT-057..058, 108..109`, `SPEC-81` AXS-TGTD-024..038).
- source: SPEC-81 AXS-TGTD-024..038; 0162; 0163 §8-14; ADR-0003; tasks/0518 §24-55, §130-132, §151 AMACHINE-33..47, AMACHINE-55..64, AMACHINE-68..69, AMACHINE-119..120; tasks/0520; tasks/0524 §7-27, §100-103, §112 ABACKEND-63..70, ABACKEND-80..81; tasks/0784 §562.17-28, §562.182-184; REQ-TGT-006, REQ-TGT-022..036, REQ-TGT-044..053, REQ-TGT-057..058, REQ-TGT-108..109
- verify: tests/mc/isa_table, tests/selfhost/backend, tests/selfhost/isel
- since: T655
- check: positive and negative tests in tests/mc/isa_table, tests/selfhost/backend, and tests/selfhost/isel (delivered by T655) verify `IsaTable` constraint validation, `encode`/`decode` round-trips, overflow/atomic/volatile/strict-FP legalization, and deterministic `verify_mc` rejection of wrong register classes, unallocated vregs, illegal reserved-register writes, missing target features, and misaligned call frames

### INV-TGTD-003 — Target-independent `Axiom LIR` semantic portability boundary, stage-isolated Machine IR serialization, and E16.1 cross-profile backend conformance
- statement: `Axiom LIR` is the canonical semantic portability boundary of the native compiler (`AMACHINE-20..22`, `ABACKEND-61..62, 99..100`, `REQ-TGT-009..011, 285..287`), assembly golden files serve strictly as code-quality tests rather than semantic authority (`ABACKEND-90`), and the E16.1 conformance suite certifies independent testability of serialized `LIR`/`Machine IR`, instruction selection, register allocation, legalizer expansion, `verify_mc` negative rejection, non-overridable machine verification, and exact observable equivalence across `--interp`, `-O0`, `-O1`, `-O2`, and `-Oz` (`AMACHINE-96..106, 118`, `ABACKEND-61..100`, `REQ-TGT-085..095, 107, 287..295`, `SPEC-81` AXS-TGTD-039..053).
- source: SPEC-81 AXS-TGTD-039..053; tasks/0518 §124-146, §151 AMACHINE-20..22, AMACHINE-96..106, AMACHINE-118; tasks/0524 §1-4, §81-113 ABACKEND-61..100; tasks/0784 §562.160-171, §562.183-200; REQ-TGT-009..011, REQ-TGT-085..095, REQ-TGT-107, REQ-TGT-285..295
- verify: tests/conformance/p16/e16_1_target_desc
- since: T656
- check: positive and negative conformance tests in tests/conformance/p16/e16_1_target_desc (delivered by T656) pass across `--interp` and native profiles (`-O0`, `-O1`, `-O2`, `-Oz`) with `0 WEAK-NATIVE`

## 36. Linux ELF64 dynamic linking, PIE, GOT/PLT, shared objects (`.so`), and `libc`/`dlopen` interoperability (SPEC-82)

### INV-ELFD-001 — Position-independent (`PIC`/`PIE`) x86-64 codegen, `GOT`/`PLT` lowering, function-address identity (`AMACHINE-79`), ELF TLS models (`IE`/`GD`), and pre-emission sizing/relaxation/provenance preservation
- statement: `compiler/target/x64/pic` lowers `CodeModel.PositionIndependent` without leaking ELF/GOT/PLT mechanics into Core semantics or `Axiom LIR` (`0197 AELF-20..27`, `REQ-TGT-146`), resolves instruction size changes, branch relaxation, and code alignment before final object emission while preserving `SourceSpan` debug provenance (`AMACHINE-72..76`, `REQ-TGT-061..065`), emits direct `RIP`-relative `R_X86_64_PC32` references for proven local/hidden symbols, indirect `.got` loads (`R_X86_64_GOTPCREL` / `R_X86_64_REX_GOTPCRELX`, relaxable to `lea` when resolved locally, `AMACHINE-77`, `REQ-TGT-066`) for external/preemptible symbols and taken function addresses so `fn_addr` equality holds across dynamic boundaries (`AMACHINE-78..79`, `REQ-TGT-067..068`), `R_X86_64_PLT32` calls through 16-byte `.plt` trampolines, and target/ABI-specific ELF TLS (`Initial-Exec` `R_X86_64_GOTTPOFF` and `General-Dynamic` `R_X86_64_TLSGD`, `ATLS-20..25`, `REQ-TGT-145, 182`) (`SPEC-82` AXS-ELFD-001..021).
- source: SPEC-82 AXS-ELFD-001..021; 0192; 0197 §1-22, §27-28, §41 AELF-20..31, ATLS-20..25; tasks/0518 §100-120, §151 AMACHINE-72..79; tasks/0521 §156 AARM-51..52; tasks/0522 §159 ABACKEND-36; REQ-TGT-061..068, REQ-TGT-145..146, REQ-TGT-182
- verify: tests/obj/elf_dyn, tests/selfhost/encode
- since: T658
- check: unit and encoding tests in tests/obj/elf_dyn and tests/selfhost/encode (delivered by T658) verify PIC RIP-relative vs GOT/PLT instruction lowering, GOT `mov -> lea` relaxation, function-pointer equality preservation, `IE`/`GD` TLS sequences, branch relaxation, and pre-emission layout alignment

### INV-ELFD-002 — ELF64 dynamic sections (`.dynsym`, `.dynstr`, `.gnu.hash`, `.dynamic`, `.rela.dyn`, `.rela.plt`), `PT_GNU_RELRO` + `DT_BIND_NOW`, `STV_DEFAULT` vs `STV_HIDDEN` visibility, and GNU symbol versioning
- statement: `compiler/obj/elf_dyn` and `compiler/link/elf_dyn` keep ISA encoding separate from object/image serialization (`ABACKEND-37..38`, `REQ-TGT-183..184`), maintain `.dynsym` distinct from `.symtab` (`0197 §4, AELF-22`), emit deterministic `.dynstr`, DJB2 Bloom-filter `.gnu.hash`, `.got`/`.got.plt`/`.plt`, `.rela.dyn` (`R_X86_64_RELATIVE`, `R_X86_64_GLOB_DAT`, `R_X86_64_64`, `R_X86_64_TPOFF64`, `R_X86_64_DTPMOD64`, `R_X86_64_DTPOFF64`), `.rela.plt` (`R_X86_64_JUMP_SLOT`), `.dynamic`, `.init_array`/`.fini_array`, and GNU version tables (`SHT_GNU_versym`, `SHT_GNU_verneed`, `SHT_GNU_verdef`), default internal and non-`@export` `pub` symbols to `STV_HIDDEN` while exporting only `@export` items as `STV_DEFAULT` in `.dynsym`, forbid text relocations (`AX_LINK_TEXTREL_FORBIDDEN`), enforce W^X `PT_LOAD` segments with `PT_GNU_STACK` (`PF_R | PF_W`) and Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`) by default, and run post-encoding structural verification (`verify_elf_image`, `ABACKEND-82..83`, `REQ-TGT-307..308`, `SPEC-82` AXS-ELFD-022..035).
- source: SPEC-82 AXS-ELFD-022..035; 0164; 0197 §3-20, §41 AELF-22..32, AELF-42..43; 0217; tasks/0369; tasks/0522 §159 ABACKEND-37..38; tasks/0524 §112 ABACKEND-82..83; tasks/0563 §304.1-304.13; REQ-TGT-183..184, REQ-TGT-307..308
- verify: tests/obj/elf_dyn, tests/selfhost/obj, tests/selfhost/link
- since: T658
- check: structural and `readelf`-equivalent tests in tests/obj/elf_dyn, tests/selfhost/obj (delivered by T658), and tests/selfhost/link (delivered by T659) verify `.dynsym`, `.gnu.hash`, `.dynamic`, `.got`/`.plt`, `.rela.dyn`/`.rela.plt`, `PT_GNU_RELRO`, `STV_HIDDEN` vs `STV_DEFAULT`, and `AX_LINK_TEXTREL_FORBIDDEN`

### INV-ELFD-003 — ELF64 `ET_DYN` `PIE` executable and `lib<name>.so` shared object linking, external `.so` `DT_NEEDED` resolution, `libc` FFI coexistence, and `std.sys.linux_dl` (`dlopen`/`dlsym`/`dlclose`/`dlerror`) interoperability
- statement: `compiler/link/elf_dyn` and `std/sys/linux_dl` link `ET_DYN` `PIE` executables (`PT_PHDR`, `PT_INTERP` `/lib64/ld-linux-x86-64.so.2`, `DF_1_PIE`, PIC `_start`) and `--kind dll` shared libraries (`lib<name>.so`, `DT_SONAME`, `.init_array` module-relative binding resolution), ingest external `.so` files and GNU linker script stubs (`GROUP`/`INPUT`) to populate explicit `DT_NEEDED` and `.gnu.version_r` entries without making `libc` or `libgcc_s` a mandatory compiler dependency (`0197 §30-32, AELF-36..39`, `0220 §2`), interoperate with `libc.so.6`/`libm.so.6`/`libpthread`/`libdl`, and provide `std.sys.linux_dl` (`dlopen`, `dlsym`, `dlclose`, `dlerror`, `dl_iterate_phdr`, `DynLib`) with an explicit `unsafe` symbol lookup boundary and `extern "C"` no-unwind abort barrier (`SPEC-82` AXS-ELFD-036..053).
- source: SPEC-82 AXS-ELFD-036..053; 0164; 0197 §23-41 AELF-25..45; 0217; 0220 §1-5; tasks/0369; tasks/0563 §304.1-304.13; SPEC-50; SPEC-54; SPEC-56; REQ-TGT-182..184, REQ-TGT-307..308
- verify: tests/run/linux_dyn, tests/selfhost/link
- since: T659
- check: execution and link tests in tests/run/linux_dyn and tests/selfhost/link (delivered by T659) verify `PIE` and `lib<name>.so` generation, `libc.so.6` PLT calls, custom `.so` `DT_NEEDED` linking, `dlopen`/`dlsym`/`dlclose` round-trips, and WSL/Linux native execution

## 37. AArch64 ISA backend, AAPCS64 ABI, 32-bit A64 encoder, `EM_AARCH64` ELF64 linking, and `std.sys.linux_aarch64` (SPEC-83)

### INV-AARCH-001 — AArch64 `RegisterFile`, `CallConv.Aapcs64` ABI lowering, `STP`/`LDP` 16-byte aligned frames, and A64 instruction selection (`verify_mc`)
- statement: `compiler/abi/aapcs64` and `compiler/target/aarch64/isel` model AArch64 `X0..X30`/`W0..W30` `RegUnit` aliasing, dedicated `SP` vs `XZR`/`WZR`, `X29` (`FP`), `X30` (`LR`), `X16`/`X17` (`IP0`/`IP1`), reserved `X18`, `V0..V31` (`Q/D/S/H/B`), and `NZCV` flags without leaking x86 or ARM64 details into `Axiom LIR` (`AARM-20..28`, `REQ-TGT-113..122`), lower `CallConv.Aapcs64` (`X0..X7` ints/ptrs, `V0..V7` floats/vectors/`HFA`/`HVA`, `<= 16`B GPR composites, `> 16`B indirect args, `X8` `XR` `sret` without consuming `X0`, callee-saved `X19..X28` and low 64-bit `D8..D15`, 16-byte `SP` alignment, `red_zone = 0`, paired `STP`/`LDP` frames; `AARM-29..37`, `REQ-TGT-123, 125..131`), select A64 immediates, addressing modes, checked overflow (`ADDS`/`SUBS`/`B.VS`/`B.CS`/`B.CC`, `SMULL`/`UMULL`, guarded `SDIV`/`UDIV`), strict IEEE-754 FP, 128-bit NEON SIMD, `LDAR`/`STLR` + `LDXR`/`STLXR` LL/SC + optional `+lse` atomics, `DMB ISH`, and volatile/MMIO ops (`AARM-38..50`, `REQ-TGT-132..133, 135..144`), and pass `ABIVerifier` + `verify_mc` before encoding (`SPEC-83` AXS-A64-001..037).
- source: SPEC-83 AXS-A64-001..037; 0193 §1-20, §29-33 AARCH64-20..35; tasks/0521 §17-95, §151-156 AARM-20..50, AARM-68..69; tasks/0784 §562.60-76; REQ-TGT-113..123, REQ-TGT-125..133, REQ-TGT-135..144
- verify: tests/mc/aarch64_isel, tests/selfhost/abi, tests/selfhost/isel
- since: T662
- check: positive and negative tests in tests/mc/aarch64_isel, tests/selfhost/abi, and tests/selfhost/isel (delivered by T662) verify `CallConv.Aapcs64` (`HFA`/`HVA`, `<= 16`B, `X8` `sret`, `X19..X28`/`D8..D15`), `STP`/`LDP` frame layout, A64 scalar/FP/NEON/LL-SC/`+lse` ISel, and `verify_mc` enforcement

### INV-AARCH-002 — Fixed-width 32-bit A64 encoder, branch relaxation, ELF64 `EM_AARCH64 = 183` relocations & `±128 MiB` veneers, `.eh_frame` DWARF unwind, and `std.sys.linux_aarch64` (`SVC #0`)
- statement: `compiler/target/aarch64/encode`, `compiler/obj/elf_aarch64`, `compiler/link/elf_aarch64`, and `std/sys/linux_aarch64` encode verified Machine IR deterministically into 4-byte-aligned 32-bit little-endian A64 words (`decode(encode(I)) == I`) without an external assembler or LLVM (`AARM-54, 57, 59`, `REQ-TGT-148, 151, 153`), relax out-of-range intra-function `B.cond`/`CBZ`/`TBZ` branches and synthesize 12-byte `ADRP X16 + ADD X16 + BR X16` linker veneers for `±128 MiB` `R_AARCH64_CALL26`/`R_AARCH64_JUMP26` crossings (`AARM-56`, `REQ-TGT-150`), emit explicit `EM_AARCH64` `Elf64_Rela` relocations (`ADRP` + `:lo12:`, `GOT`/`PLT` via `X16`/`X17`, `TPIDR_EL0` TLS, `.eh_frame` `R_AARCH64_PREL32`; `AARM-40, 51..52, 55, 58`, `REQ-TGT-134, 149, 152`), key backend caches by `TargetFingerprint` (`AARM-60`, `REQ-TGT-154`), and implement `_start` and the `SPEC-04 AXS-EXT-110` host interface via `SVC #0` (`X8`, `X0..X5`, `asm-generic/unistd.h` without legacy x86 syscalls; `SPEC-83` AXS-A64-038..048).
- source: SPEC-83 AXS-A64-038..048; 0193 §21-27, §33 AARCH64-30..39; tasks/0521 §78-80, §97-104, §136, §156 AARM-40, AARM-51..52, AARM-54..60; tasks/0784 §562.68-69; REQ-TGT-134, REQ-TGT-148..154
- verify: tests/encode/aarch64, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link
- since: T663
- check: encoding, object, and link tests in tests/encode/aarch64, tests/selfhost/encode, tests/selfhost/obj, and tests/selfhost/link (delivered by T663) verify 32-bit A64 encoding round-trips, `ADRP`+`:lo12:` page relocations, `±128 MiB` veneers, `.eh_frame` CFI, `_start` + `SVC #0` `aarch64-linux` images, and byte-identical determinism

### INV-AARCH-003 — End-to-end E16.3 AArch64 Linux encoding, AAPCS64 ABI, optimization/feature/verifier isolation, and `x86_64` vs `aarch64` differential conformance
- statement: The E16.3 conformance suite certifies that semantic tests remain independent of machine instruction sequences while assembly goldens test only implementation quality (`AARM-61..62`, `REQ-TGT-155..156`), target-independent optimization never depends on AArch64 opcodes and target-dependent optimization begins strictly after `LIR` target lowering (`AARM-64..65`, `REQ-TGT-158..159`), unsupported operations expand legally or fail explicitly and target features are never silently assumed (`AARM-66..67`, `REQ-TGT-160..161`), `ABIVerifier` and `verify_mc` precede encoding with zero Core syntax leakage under a single `TargetBackend` contract (`AARM-68..70`, `0521 §158`, `REQ-TGT-162..165`), and `aarch64-linux` binaries produce byte-identical observable behavior to `--interp` and `x86_64` across scalar, aggregate/`HFA`/`sret`, atomic, FP, NEON, `Drop`, and UTF-8 workloads (`AARM-63`, `REQ-TGT-157`, `SPEC-83` AXS-A64-001..053).
- source: SPEC-83 AXS-A64-001..053; 0193 §28-40 AARCH64-20..40; tasks/0521 §124-158 AARM-61..70; REQ-TGT-155..165
- verify: tests/conformance/p16/e16_3_aarch64_linux
- since: T664
- check: positive, negative, encoding golden, and differential execution tests in tests/conformance/p16/e16_3_aarch64_linux (delivered by T664) pass across `--interp`, `x86_64`, and `--target aarch64-linux` with `0 WEAK-NATIVE`

## 38. macOS AArch64 Darwin ABI, Mach-O 64 object/archive/image linking, ad-hoc codesign, and `std.sys.macos` (SPEC-84)

### INV-MACHO-001 — `CallConv.Aapcs64Darwin` Apple ARM64 ABI (`X18` reservation, `< 32`-bit extension, packed stack, stack variadics, `128`B red zone, `X29` FP chain), Mach-O 64 `MH_OBJECT` (`ARM64_RELOC_*`), and deterministic BSD `ar`
- statement: `compiler/abi/apple_arm64` and `compiler/obj/macho` reuse the OS-independent `Arch.AArch64` ISA layer (`SPEC-83`) while specializing `TargetId.AArch64Macos` (`CallConv.Aapcs64Darwin`): strictly reserving `X18` (`verify_mc` rejects any read/write, `AX_VERIFY_MC_ILLEGAL`), keeping `pauth` outside Core pointer/capability semantics (`AARM-53`, `REQ-TGT-147`), caller/callee sign- and zero-extending `< 32`-bit scalars in `W0..W7`, packing spilled non-variadic stack arguments at natural size/alignment (`1/2/4/8/16`B) without even-register GPR pair rounding, placing all variadic `...` arguments in 8-byte stack slots (`va_list = *mut u8`), enabling a 128-byte hosted leaf red zone, maintaining an unbroken `X29` (`FP`) frame-record chain (`ABACKEND-71..75`, `REQ-TGT-296..300`), decorating linkage symbols with a single leading `_`, serializing field-by-field `MH_OBJECT` files (`MH_MAGIC_64 = 0xFEEDFACF`, `CPU_TYPE_ARM64 = 0x0100000C`, `MH_SUBSECTIONS_VIA_SYMBOLS`, 80-byte `section_64` with `sectname` at `+0..16` before `segname` at `+16..32`, 4 KiB-page `ARM64_RELOC_*` records, Darwin `tlv_descriptor` with `ARM64_RELOC_UNSIGNED` at `+0` `_tlv_bootstrap` and `+16` TLS backing symbol; `ABACKEND-76..77`, `REQ-TGT-301..302`), and packaging deterministic BSD 4.4 `ar` archives (`__.SYMDEF SORTED`, `#1/<len>` names; `SPEC-84` AXS-MACHO-001..019).
- source: SPEC-84 AXS-MACHO-001..019; 0196 §1-12, §25, §27-28, §31, §40 AMACHO-20..24, AMACHO-27, AMACHO-32..34, AMACHO-38; 0217 §4-19, §37, §44, §51, §72 ALINK-20..38, ALINK-50; 0220 §16; tasks/0369 §2-12, §17, §31; tasks/0453 §194.18; tasks/0521 §60-63, §80, §91-92, §156 AARM-20, AARM-22, AARM-30, AARM-53; tasks/0524 §112 ABACKEND-71..77; tasks/0563 §304.22, §304.30-32, §304.45 AIMG-29, AIMG-32..34, AIMG-59; REQ-TGT-147, REQ-TGT-296..302
- verify: tests/obj/macho, tests/selfhost/abi, tests/selfhost/obj
- since: T666
- check: unit and object golden tests in tests/obj/macho, tests/selfhost/abi, and tests/selfhost/obj (delivered by T666) verify `X18` non-clobbering, `< 32`b extensions, packed Darwin stack offsets, stack-only variadics, `X29` FP chains, `_` symbol prefixing, `section_64` `(sectname, segname)` layout, `ARM64_RELOC_*` & `tlv_descriptor` encodings, and deterministic BSD `ar` archives

### INV-MACHO-002 — Native Mach-O 64 linker (`MH_EXECUTE` & `MH_DYLIB`), 16 KiB W^X segments, `__stubs`+`__got`, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, hermetic `.tbd`/`libSystem`, 88-byte `CS_CodeDirectory` ad-hoc `LC_CODE_SIGNATURE`, and `std.sys.macos`
- statement: `compiler/link/macho` and `std/sys/macos` link `MH_OBJECT` and BSD `ar` inputs into 16 KiB-aligned (`0x4000`) W^X `MH_EXECUTE` (`__PAGEZERO`, `__TEXT` at `0x1_0000_0000`, `__DATA_CONST` `SG_READ_ONLY`, `__DATA` with zero-file-byte `S_ZEROFILL`, `__LINKEDIT`, `LC_MAIN`) and `MH_DYLIB` (`lib<name>.dylib`, `LC_ID_DYLIB`) images without Xcode, `clang`, `ld64`, or `codesign`, synthesizing 12-byte `__TEXT,__stubs` + 8-byte `__DATA_CONST,__got`, relaxing linkage-local GOT loads to `ADD`, inserting `±128 MiB` `X16` branch islands (`ABACKEND-78, 86..88`, `REQ-TGT-303, 311..313`), encoding `LC_DYLD_CHAINED_FIXUPS` (`DYLD_CHAINED_PTR_64_OFFSET`, while resolving `S_THREAD_LOCAL_VARIABLES` `tlv_descriptor.offset` at `+16` statically to `S + A - tls_template_base_vma` without emitting a `bind == 0` rebase) and ULEB128 `LC_DYLD_EXPORTS_TRIE`, resolving `/usr/lib/libSystem.B.dylib` via a built-in hermetic export catalog and `.tbd`/`.dylib` stub reader, appending a big-endian 20-byte `CS_SuperBlob` + 88-byte `CS_CodeDirectory` (`v0x00020400`, `length = total_sig_bytes - 20` at `+4`, `CS_ADHOC | CS_LINKER_SIGNED`, `identOffset = 88` and `hashOffset = 88 + ident_len_with_nul` relative to `sig_off + 20`, SHA-256 over 4 KiB pages) at EOF, folding Compact Unwind (`__TEXT,__unwind_info`), enforcing `verify_macho_image`, and implementing the `SPEC-04 AXS-EXT-110` `std/sys/macos` host contract strictly over `libSystem.B.dylib` with zero raw `SVC #0x80` syscalls, Darwin ARM64 `O_*` flags, 144-byte `struct stat` and 64-bit-inode `struct dirent` (`_stat`, `_fstat`, `_readdir`), `_NSGetExecutablePath`, `clock_gettime_nsec_np`, `pthread_*`/`__ulock_*`, `kqueue`/`kevent64`, and `X18`-preserving 160-byte stackful fibers (`SPEC-84` AXS-MACHO-020..031).
- source: SPEC-84 AXS-MACHO-020..031; 0196 §6-7, §10, §13-34, §40 AMACHO-25..40; 0217 §25-34, §44-55, §72 ALINK-39..56; 0220 §1-4, §7, §13-31, §39 AOS-20..40; tasks/0453 §194.20-23; tasks/0518 AMACHINE-73, AMACHINE-79; tasks/0524 §112 ABACKEND-78, ABACKEND-86..88; tasks/0563 §304.5-6, §304.21-25, §304.28-40, §304.45 AIMG-24..34, AIMG-37, AIMG-41..52; REQ-TGT-303, REQ-TGT-311..313
- verify: tests/link/macho, tests/selfhost/link
- since: T667
- check: link, `std/sys/macos` binding, and structural verification tests in tests/link/macho and tests/selfhost/link (delivered by T667) verify 16 KiB segment layout, W^X, `__stubs`+`__got`, `LC_DYLD_CHAINED_FIXUPS` (including non-rebased `tlv_descriptor.offset`), `LC_DYLD_EXPORTS_TRIE`, `.tbd` & built-in `libSystem` linking, `std/sys/macos` host imports, and valid 88-byte-header SHA-256 `LC_CODE_SIGNATURE` blobs

### INV-MACHO-003 — End-to-end E16.4 macOS AArch64 semantic portability, differential execution, `TargetFingerprint` cache isolation, and Mach-O / SHA-256 codesign determinism conformance
- statement: The E16.4 conformance suite certifies on `aarch64-macos` (covering `compiler/abi/apple_arm64` + `compiler/obj/macho` from `T666` and `compiler/link/macho` + `std/sys/macos` from `T667`, feeding `E16.10` `T685`–`T688` `SPEC-89` and `E16.11` `T689`–`T692` `SPEC-90`) that distinct instruction sequences may represent identical `LIR` semantics (`ABACKEND-89`, `REQ-TGT-314`), assembly and encoding golden tests are never the semantic authority (`ABACKEND-90`, `REQ-TGT-315`), reference `--interp` evaluation and differential execution across `x86_64`, `aarch64-linux`, and `aarch64-macos` are the semantic validation mechanisms (`ABACKEND-91`, `REQ-TGT-316`), and backend conformance tests remain target-independent at the semantic level (`ABACKEND-92`, `REQ-TGT-317`), while isolating incremental/artifact caches by `TargetFingerprint` (`TargetId.AArch64Macos`, `CallConv.Aapcs64Darwin`; `ABACKEND-94`) and guaranteeing byte-for-byte deterministic Mach-O, `LC_UUID`, and 88-byte `CS_CodeDirectory` SHA-256 ad-hoc `LC_CODE_SIGNATURE` artifacts (`AMACHO-35..36, 40`, `ABACKEND-95`, `AIMG-45..47`, `SPEC-84` AXS-MACHO-001..036).
- source: SPEC-84 AXS-MACHO-001..036; 0196 §23-24, §35-40 AMACHO-35..36, AMACHO-40; 0220 §7, §39 AOS-20..40; tasks/0453 §194.31; tasks/0524 §68-91, §112 ABACKEND-89..92, ABACKEND-94..95; tasks/0563 §304.25, §304.33-38, §304.45 AIMG-37, AIMG-45..51; REQ-TGT-314..317
- verify: tests/conformance/p16/e16_4_macos_aarch64
- since: T668
- check: cross-build structural, SHA-256 codesign, target-independent semantic, and Apple Silicon native differential execution conformance tests in tests/conformance/p16/e16_4_macos_aarch64 (delivered by T668) pass across `--interp`, `x86_64`, `aarch64-linux`, and `aarch64-macos` with `0 WEAK-NATIVE` and byte-identical determinism

## 39. Android AArch64 Bionic ELF64 target (`ET_DYN` PIE & `.so`), NDK-free stub linking, `std.sys.android`, and capability-safe 3-layer JNI bindings (SPEC-85)

### INV-ANDR-001 — `aarch64-android` `TargetDesc` (`api_level` fingerprint, reserved `X18` ShadowCallStack), 16 KiB Bionic ELF64 `ET_DYN` PIE/`.so` linker, `.note.android.ident`, NDK-free Bionic stubs, and `std.sys.android`
- statement: `compiler/target/aarch64/android`, `compiler/link/elf_android`, and `std/sys/android` reuse the OS-independent `Arch.AArch64` ISA and `CallConv.Aapcs64` layers (`SPEC-83`) while specializing `TargetId.AArch64Android`: encoding `api_level` (default `29`, min `21`) into `TargetFingerprint` (`0198 §2-3, AANDROID-23..24, 43`), strictly reserving `X18`/`W18` for the Android ShadowCallStack (`verify_mc` rejects any read/write, `AX_VERIFY_MC_ILLEGAL`), keeping physical pointer/temporary/copy/move lowering independent of Core syntax and `Copy`/`Move` semantics while preserving execution-domain and CPU-vs-GPU `@addr_space` isolation (`AMACHINE-80..84, 87..89`, `REQ-TGT-069..073, 076..078`), emitting mandatory `ET_DYN` 16 KiB-aligned (`p_align = 0x4000`) W^X Full-RELRO PIE executables (`PT_INTERP = "/system/bin/linker64\0"`, `DF_1_PIE`, `__libc_init` `_start`) and `lib<stem>.so` shared libraries (`DT_SONAME`, `e_entry = 0`, no hidden global constructors), writing the 152-byte `.note.android.ident` section (`NT_ANDROID_TYPE_IDENT = 1`), linking without an installed Android NDK via a built-in Bionic stub symbol catalog (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`) with API-level (`AX_TARGET_API_LEVEL_TOO_LOW`) and private-library namespace (`AX_LINK_ANDROID_PRIVATE_LIB`) verification, and implementing `std/sys/android` (`__ax_host_*`, `__errno`, `arc4random_buf`/`getrandom`, `SYS_futex = 98`, `epoll`, `X18`-preserving 160-byte fibers, and `liblog.so` `__android_log_write`; `SPEC-85` AXS-ANDR-001..016).
- source: SPEC-85 AXS-ANDR-001..016; SPEC-82; SPEC-83; 0193; 0197; 0198 §1-41 AANDROID-20..44; 0220 §1-4, §9, §16, §18, §28-39 AOS-20..40; tasks/0453 §194.1-44 ATARGET-20..50; tasks/0518 §151 AMACHINE-80..84, AMACHINE-87..89; REQ-TGT-069..073, REQ-TGT-076..078
- verify: tests/obj/android, tests/selfhost/link
- since: T670
- check: unit, binary-inspection, and negative link tests in tests/obj/android and tests/selfhost/link (delivered by T670) verify `TargetFingerprint` API-level isolation, `X18` reservation, 16 KiB `PT_LOAD` `ET_DYN` PIE (`/system/bin/linker64`) and `lib<stem>.so` (`DT_SONAME`) layout, `.note.android.ident`, NDK-free Bionic `DT_NEEDED` linking, `AX_TARGET_API_LEVEL_TOO_LOW`, and `AX_LINK_ANDROID_PRIVATE_LIB`

### INV-JNI-001 — Capability-safe 3-layer JNI bindings (`std.ffi.jni.raw`, `JniEnv`/`JavaVM`/`JLocal`/`JGlobal`/`JWeak`, `JString`, array views, `ExceptionCheck` -> `JException` / `Result<T, JniError>`) and `@jni_export` adapter lowering
- statement: `std/ffi/jni` and `compiler/hir/jni_attr` implement the 3-layer capability-safe JNI stack over `extern "C"` (`no extern "JNI"`, `0198 §14-18`, `0200 §1-48, AJNI-20..52`): exposing raw `<jni.h>` 8-slot `JNIInvokeInterface_` and 233-slot `JNINativeInterface_` vtables in `std.ffi.jni.raw` (`unsafe`), enforcing thread-bound `JniEnv` (`!Copy`, `!Send`, `!Share`, passed solely as `view<JniEnv>`/`mut_view<JniEnv>`), structured `JavaVM.with_attached_env` (`AttachCurrentThread`/`DetachCurrentThread` RAII without detaching pre-attached host threads), frame-scoped `JLocal<T>` (`!Send`, `!Share`, deterministic `DeleteLocalRef` in `Drop`, `clone_local`) and `with_local_frame` (`PushLocalFrame`/`PopLocalFrame`), cross-thread `JGlobal<T>`/`JWeak<T>` (`Send + Share`, `new_local_ref`, deterministic `DeleteGlobalRef`/`DeleteWeakGlobalRef` in `Drop`, race-free `upgrade_local`), explicit `JString` UTF-8/Modified-UTF-8/UTF-16 conversion and array region/element/critical views, mandatory `ExceptionCheck` + immediate `ExceptionClear` conversion to `JException` / `Result<T, JniError>` (`JniError.Exception(JException)`), and `@jni_export` lowering (`Java_*` mangling + synthesized `JNI_OnLoad` `RegisterNatives`, explicit `JniReturn<T>` handoff rejecting bare `JLocal<T>` escape with `AX_FFI_JNI_LOCAL_ESCAPE`, and panic/`Err` -> `Throw`/`ThrowNew` barrier), while preserving `Drop`, capability validity, pointer provenance, and explicit imported-resource lifetime contracts (`AMACHINE-85..86`, `AWASM-41`, `REQ-TGT-074..075, 110, 230`, `SPEC-85` AXS-JNI-001..017).
- source: SPEC-85 AXS-JNI-001..017; SPEC-30; SPEC-50; SPEC-54 AXS-PAN-020..022; 0198 §14-18 AANDROID-29..30; 0200 §1-61 AJNI-20..52; tasks/0518 §151 AMACHINE-85..86, memory codegen provenance; tasks/0523 §155 AWASM-41; REQ-TGT-074..075, REQ-TGT-110, REQ-TGT-230
- verify: tests/run/jni, tests/selfhost/hir
- since: T671
- check: execution tests over `MockJvm` and negative HIR/type tests in tests/run/jni and tests/selfhost/hir (delivered by T671) verify `JLocal`/`JGlobal`/`JWeak` deterministic `Drop`, `with_local_frame`, `with_attached_env`, `JString` UTF-8/Modified-UTF-8 round-trips, `ExceptionCheck` -> `JException` / `Result.Err(JniError.Exception(JException))`, `@jni_export` `Java_*`/`JNI_OnLoad` generation, panic-to-`ThrowNew` containment, and compile-time rejection of `JniEnv`/`JLocal` thread transfer or frame escape

### INV-JNI-002 — End-to-end E16.5 Android AArch64 Bionic ELF64 (`.so`/PIE), foreign handle identity, JNI reference/frame/thread lifetimes, and Java<->Axiom exception/panic bridge conformance
- statement: The E16.5 conformance suite certifies end-to-end across `aarch64-android` ELF64 artifacts and the deterministic `MockJvm` harness that `axiomc` produces 16 KiB-aligned NDK-free Bionic PIE and `lib<stem>.so` images preserving `X18` ShadowCallStack and `.note.android.ident`, that host callbacks (`@jni_export`, `JNI_OnLoad`, `JavaVM.with_attached_env`) preserve resource, attachment, and exception/no-unwind contracts across normal returns, `?` early returns, and panics (`AWASM-81`, `REQ-TGT-270`), that foreign handle logical identity (`IsSameObject`) remains strictly distinct from numeric slot/memory addresses and never grants memory capabilities (`AWASM-83..84`, `REQ-TGT-272..273`), and that target/host binding layers do not alter Core FFI safety semantics (`AWASM-93`, `REQ-TGT-282`, `SPEC-85` AXS-ANDR-001..016, AXS-JNI-001..020).
- source: SPEC-85 AXS-ANDR-001..016, AXS-JNI-001..020; 0198 §32-41 AANDROID-20..44; 0200 §50-61 AJNI-20..52; tasks/0523 §155 AWASM-81, AWASM-83..84, AWASM-93; REQ-TGT-270, REQ-TGT-272..273, REQ-TGT-282
- verify: tests/conformance/p16/e16_5_android_aarch64_jni
- since: T672
- check: structural ELF64 inspection, `MockJvm` reference/frame/attach counter verification, exception/panic bridge tests, and negative UI escape tests in tests/conformance/p16/e16_5_android_aarch64_jni (delivered by T672) pass across `--interp` and native targets

## 40. WASM32 virtual stack-machine backend, CFG structuring & stackification, binary `.wasm` validator/linker, and `std.sys.wasi` (SPEC-86)

### INV-WASM-001 — Arbitrary `LIR` CFG structuring (`block`/`loop`/`if-else`/`br_table` & `$irr_state` irreducible loop legalization), side-effect-preserving SSA stackification, typed local coalescing, and `CallConv.Wasm` Basic C ABI
- statement: `compiler/target/wasm32/isel` and `compiler/abi/wasm32` classify WASM under `TargetFamily.VirtualMachine` (`TargetId.Wasm32Freestanding` and `TargetId.Wasm32Wasi`, `pointer_width_bits = 32`, `Endian.Little`, 64 KiB pages) while keeping `Verified MIR`, `OptIR`, and `Axiom LIR` 100% independent of operand-stack and structured-CFG constraints (`AMACHINE-90`, `AWASM-20..36, 65..66`, `ABACKEND-79`, `REQ-TGT-079, 207..225, 254..255, 304`), reconstruct every reducible `LIR` CFG into `block`/`loop`/`if-else`/`br`/`br_if`/`br_table` and legalize every irreducible multi-entry cycle deterministically via `$irr_state: i32` + single-header `loop` dispatch (`AWASM-67..68`, `REQ-TGT-256..257`), schedule single-use SSA subtrees onto the virtual operand stack strictly within side-effect/panic/memory-aliasing barriers while coalescing remaining values into typed WASM locals (`AWASM-69..70`, `REQ-TGT-258..259`), emit explicit division/shift/bounds pre-checks (`AWASM-32..33`), and implement `CallConv.Wasm` (`(i64, i64)` `i128` parameters, hidden `sret: i32` aggregate/`i128` returns, shadow-stack `$__stack_pointer` frames, `va_list: i32` variadics, `slot 0 = null` `__indirect_function_table` `call_indirect`, zero-header closures/8-byte `dyn Trait`, stackless `Future` state machines without WASM GC, and profile-governed `unreachable` vs WASI `fd_write(2)+proc_exit(101)` panic lowering; `AWASM-42..55`, `REQ-TGT-231..244`, `SPEC-86` AXS-WASM-001..024).
- source: SPEC-86 AXS-WASM-001..024; SPEC-81; tasks/0518 §151 AMACHINE-90; tasks/0522 header; tasks/0523 §1-42, §51-99, §109-147, §155 AWASM-20..36, AWASM-42..55, AWASM-65..70; tasks/0524 §112 ABACKEND-79; tasks/0784 §562.77-92, §562.98, §562.200 #71..86, #98, #163, #174; REQ-TGT-079, REQ-TGT-207..225, REQ-TGT-231..244, REQ-TGT-254..259, REQ-TGT-304
- verify: tests/mc/wasm32_stackify, tests/selfhost/abi, tests/selfhost/isel
- since: T674
- check: unit and WAT lowering tests in tests/mc/wasm32_stackify, tests/selfhost/abi, and tests/selfhost/isel (delivered by T674) verify reducible and `$irr_state` irreducible CFG structuring, SSA stackification and `local.tee`/local coalescing, `CallConv.Wasm` scalar/`i128`/aggregate/`sret`/variadic/indirect-call lowering, and profile-governed panic lowering

### INV-WASM-002 — Self-contained pre-emission `verify_wasm` bytecode validator, relocatable `.wasm` (`linking` v2 + `reloc.CODE`/`reloc.DATA`) & GNU `ar` writer, export-rooted deterministic static `.wasm` linker, and capability-scoped `std.sys.wasi`
- statement: `compiler/target/wasm32/encode`, `compiler/obj/wasm`, `compiler/link/wasm`, and `std/sys/wasi` run the internal polymorphic operand-stack and index-space validator `verify_wasm` (`AX_VERIFY_WASM_ILLEGAL` on negative test IR, `AX_ICE_INTERNAL` on compiler IR) prior to emitting any `.wasm` object or linked binary without relying on external tools (`AWASM-63..64`, `REQ-TGT-252..253`), enforce explicit `TargetFeatureSet` gating and `TargetFingerprint` cache isolation (`AWASM-61..62, 77`, `REQ-TGT-250..251, 266`), serialize `\0asm` v1 modules in canonical W3C section order (`1..9, 12 DataCount, 10 Code, 11 Data`) alongside relocatable `linking` v2 followed by `reloc.CODE`/`reloc.DATA` custom sections (`(target_section_index, reloc_count)` headers and `addend: sleb32` on `R_WASM_*` `{3, 4, 5, 8, 9}`) and deterministic GNU `ar` `.a` archives, statically link `.wasm` modules with export-rooted dead-code/data/import/runtime GC and byte-for-byte determinism (`AWASM-56..60, 74, 78, 82`, `REQ-TGT-245..249, 263, 267, 271`), preserve explicit `@wasm_import`/`@wasm_export`, imported-memory, host-sync, and Component Model/WIT layering boundaries (`AWASM-38..40, 71, 73, 79..80`, `REQ-TGT-227..229, 260, 262, 268..269`), and implement `std/sys/wasi` (`wasi_snapshot_preview1`, `filestat.size` at `+32` and `filetype` `4->1, 3->2, _->3`) strictly over preopened directory capabilities (`fd_prestat_get`, zero ambient root `/` paths) and a pure-Axiom 64 KiB `memory.grow` heap allocator (`0220 §10`, `AWASM-37, 72`, `REQ-TGT-226, 261`, `SPEC-86` AXS-WASM-001..010, AXS-WASM-022..029).
- source: SPEC-86 AXS-WASM-001..010, AXS-WASM-022..029; 0220 §10, §39 AOS-20..40; tasks/0453 §194.36, §194.44 ATARGET-20..50; tasks/0523 §43-50, §100-117, §140-150, §155 AWASM-37..40, AWASM-56..64, AWASM-71..74, AWASM-77..80, AWASM-82; tasks/0784 §562.5, §562.29-34, §562.87-99, §562.141-145, §562.153, §562.179-182; REQ-TGT-208, REQ-TGT-226..229, REQ-TGT-245..253, REQ-TGT-260..263, REQ-TGT-266..269, REQ-TGT-271
- verify: tests/obj/wasm, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link
- since: T675
- check: binary encoding, negative `verify_wasm`, relocatable `linking` v2 / `reloc.CODE` / `reloc.DATA` / `.a` archive, export-rooted static linker GC, determinism, and `std/sys/wasi` preopen/metadata/allocator tests in tests/obj/wasm, tests/selfhost/encode, tests/selfhost/obj, and tests/selfhost/link (delivered by T675) pass cleanly

### INV-WASM-003 — End-to-end E16.6 WASM32 `--interp` & native-vs-stack semantic equivalence, Core semantic non-contamination, `Axiom LIR` portability, and WASI differential conformance
- statement: The E16.6 conformance suite certifies across `wasm32-freestanding` and `wasm32-wasi` that WASM code generation is semantically equivalent to reference execution (`--interp`) while WASM target-specific optimizations never alter Core semantics and WAT/binary inspections verify lowering quality without acting as the semantic authority (`AWASM-75..76`, `REQ-TGT-264..265`, `SPEC-81` AXS-TGTD-043, `ABACKEND-89..92`), that both WASM targets pass common `TargetBackend` conformance tests, agree with native (`x86_64`, `aarch64`) backends on observable semantics while treating physical layout differences as non-semantic, require zero WASM-specific Core v1 syntax, and require zero changes to Core ownership, trait, `async`, or numeric semantics (`AWASM-85..92`, `REQ-TGT-274..281`), and that the WASM backend remains frontend-independently replaceable behind `Axiom LIR` while validating `Axiom LIR` portability, `verify_wasm` validity, byte-for-byte determinism, and `0 WEAK-NATIVE` WASI differential parity against `--interp` and `x86_64` (`AWASM-60..64, 94..95`, `REQ-TGT-283..284`, `SPEC-86` AXS-WASM-001..034).
- source: SPEC-86 AXS-WASM-001..034; SPEC-81 AXS-TGTD-040..044; 0220 §10, §39 AOS-20..40; tasks/0523 §151-156 AWASM-75..76, AWASM-85..92, AWASM-94..95; tasks/0524 §112 ABACKEND-89..92; tasks/0784 §562.165, §562.182-186, §562.200 #71..86, #177; REQ-TGT-264..265, REQ-TGT-274..281, REQ-TGT-283..284
- verify: tests/conformance/p16/e16_6_wasm32
- since: T676
- check: positive cross-build `verify_wasm` structural tests, negative feature/capability/bytecode-validator tests, determinism checks, and WASI runtime differential execution tests (`wasmtime`/`wasmer` vs `--interp` and `x86_64`) in tests/conformance/p16/e16_6_wasm32 (delivered by T676) pass with `0 WEAK-NATIVE`

## 41. RISC-V 64 (`RV64GC`) flagless ISA backend, `LP64D` psABI, RV64 + `RVC` encoder, `EM_RISCV` ELF64 linking, and `std.sys.linux_riscv64` (SPEC-87)

### INV-RISCV-001 — Modular `RV64GC` `TargetDesc`/`RegisterFile` (`x0` `ZeroReg`, reserved `sp`/`gp`/`tp`, `f32` NaN-boxing, scalable `RVV`), `CallConv.RiscV` (`LP64D`) lowering, flagless ISel, RVWMO atomics, and pre-encoding `verify_mc`
- statement: `compiler/abi/riscv64` and `compiler/target/riscv64/isel` implement `TargetId.Riscv64Linux` (`Arch.RiscV64, Os.Linux, CallConv.RiscV, ObjectFormat.Elf64`) over modular `RV64GC` (`{i, m, a, f, d, zicsr, zifencei, c}` plus explicit `+v`/`+zba`/`+zbb`/`+zbc`/`+zbs`/`+zbkb`/`+zicond`/`+zacas`/custom feature DAG, never emitting unavailable instructions; `ABACKEND-28..29, 48`, `REQ-TGT-174..175, 194`), keep `Axiom LIR` free of physical registers and condition-code flags (`ABACKEND-21..25`, `REQ-TGT-167..171`), enforce `x0` `ZeroReg` non-allocation, reserved `sp`/`gp`/`tp` (and `s0` when frame-pointer active), `f32` NaN-boxing (`[63:32] = 0xFFFF_FFFF`), and scalable `v0..v31` `RVV` separation (`ABACKEND-44..45`, `REQ-TGT-190..191`), lower `CallConv.RiscV` `LP64D` (`i32` and `u32` sign-extension, `{FP}`/`{FP,FP}`/`{INT,FP}`/`{FP,INT}` hardware flattening, `a7`+stack split, `> 16`B caller-copy reference, hidden `sret` in `a0`, even-pair variadic `2*XLEN` alignment, 16B `sp` with `red_zone = 0`, and 4 KiB stack probing; `ABACKEND-26..27, 33`, `REQ-TGT-172..173, 179`), select flagless compare-branch fusion, two-register checked overflow, guarded `DIV`/`REM`, `NaN -> 0` saturating float-to-int casts, `+0x800` `HI20`/`LO12` addressing, RVWMO `AMO*`/`LR`-`SC`/`FENCE` atomics, and `Volatile`/`FENCE io, io` MMIO (`ABACKEND-30, 32, 34..35, 41..42`, `REQ-TGT-176, 178, 180..181, 187..188`), and pass `verify_mc` strictly before encoding (`ABACKEND-31, 50`, `REQ-TGT-177, 196`, `SPEC-87` AXS-RV64-001..032).
- source: SPEC-87 AXS-RV64-001..032; SPEC-81; ADR-0003; 0152 §59; tasks/0522 §1-62, §66-86, §95, §100-121, §124, §148-150, §159 ABACKEND-20..35, ABACKEND-41..42, ABACKEND-44..45, ABACKEND-48, ABACKEND-50; tasks/0784 §562.135-140, §562.200; REQ-TGT-166..181, REQ-TGT-187..188, REQ-TGT-190..191, REQ-TGT-194, REQ-TGT-196
- verify: tests/mc/riscv64_isel, tests/selfhost/abi, tests/selfhost/isel
- since: T678
- check: unit, `LP64D` ABI classification, flagless ISel/overflow/atomic lowering, and negative `verify_mc` tests in tests/mc/riscv64_isel, tests/selfhost/abi, and tests/selfhost/isel (delivered by T678) verify `x0`/`sp`/`gp`/`tp` invariants, `u32` sign-extension, `{FP}`/`{FP,FP}`/`{INT,FP}` flattening, `a7`+stack split, `a0` `sret`, flagless overflow/div-zero traps, `NaN -> 0`, and `AX_VERIFY_MC_ILLEGAL` rejection

### INV-RISCV-002 — Pre-encoding pseudo expansion, RV64GC 32-bit + 16-bit `RVC` encoder, relaxation-independent `EM_RISCV` ELF64 object/linker (`PCREL_HI20`/`LO12`, `PIE`/`GOT`/`PLT`, Variant I `tp` TLS, `.eh_frame`), and `std.sys.linux_riscv64`
- statement: `compiler/target/riscv64/encode`, `compiler/obj/elf_riscv64`, `compiler/link/elf_riscv64`, and `std/sys/linux_riscv64` expand all pseudo-instructions into concrete verified machine instructions before encoding (`ABACKEND-46`, `REQ-TGT-192`), encode little-endian 32-bit `R/R4/I/S/B/U/J` and 16-bit `RVC` (`C` extension) instructions with `decode(encode(I)) == I` round-trip fidelity while treating `RVC` strictly as a semantics-preserving encoding optimization (`ABACKEND-43`, `REQ-TGT-189`), serialize `EM_RISCV = 243` ELF64 objects (`e_flags = 0x0005`, `.riscv.attributes` `SHT_RISCV_ATTRIBUTES = 0x70000003`) separately from instruction encoding (`ABACKEND-38`, `REQ-TGT-184`), resolve paired `R_RISCV_PCREL_HI20` + `R_RISCV_PCREL_LO12_I`/`S` relocations via the `AUIPC` symbol with `+0x800` carry compensation so sequences execute validly without optional `R_RISCV_RELAX` (`ABACKEND-37, 47`, `REQ-TGT-183, 193`), link static, `PIE` (`/lib/ld-linux-riscv64-lp64d.so.1`), and `.so` images with `PT_GNU_RELRO`, `GOT`/`PLT`, Variant I `tp` TLS (`LE`/`IE`/`GD`; `ABACKEND-36`, `REQ-TGT-182`), DWARF v5 provenance and `.eh_frame` CFI (`ABACKEND-39..40`, `REQ-TGT-185..186`), inline-asm machine-effect contracts (`ABACKEND-49`, `REQ-TGT-195`), and `std.sys.linux_riscv64` (`_start`, `ecall` `asm-generic/unistd.h` + `SYS_riscv_hwprobe = 258` + `SYS_riscv_flush_icache = 259`, and 208-byte stackful fibers; `SPEC-87` AXS-RV64-020, AXS-RV64-033..044).
- source: SPEC-87 AXS-RV64-020, AXS-RV64-033..044; SPEC-04 AXS-EXT-110; SPEC-80; SPEC-82; 0152 §59; tasks/0522 §12, §29-30, §39-41, §63-65, §87-94, §98-99, §111-113, §122-124, §141, §148-150, §159 ABACKEND-36..40, ABACKEND-43, ABACKEND-46..50; tasks/0784 §562.138-140; REQ-TGT-182..186, REQ-TGT-189, REQ-TGT-192..196
- verify: tests/encode/riscv64, tests/selfhost/encode, tests/selfhost/obj, tests/selfhost/link
- since: T679
- check: 32-bit + `RVC` encoding round-trip tests, `.riscv.attributes` and paired `PCREL_HI20`/`LO12` relocation tests (including `+0x800` sign-extension boundary without `R_RISCV_RELAX`), static/`PIE`/`.so`/`tp`-TLS/`.eh_frame` link tests, and `std.sys.linux_riscv64` startup/syscall tests in tests/encode/riscv64, tests/selfhost/encode, tests/selfhost/obj, and tests/selfhost/link (delivered by T679) pass cleanly

### INV-RISCV-003 — End-to-end E16.7 `riscv64-linux` cross-target conformance, `TargetFingerprint` cache isolation, deterministic parallel codegen, and `TargetBackend` portability boundary
- statement: The E16.7 conformance suite certifies across `riscv64-linux` that the RV64GC backend passes the common cross-target conformance suites (`ABACKEND-51`, `REQ-TGT-197`), determines semantic correctness by observable execution equivalence rather than assembly golden files (`ABACKEND-52`, `REQ-TGT-198`), produces identical observable exit codes, stdout (including UTF-8 `"Xin chào thế giới"`), panics, `Drop` order, and atomic/memory effects to `--interp`, `x86_64-linux`, `aarch64-linux`, and `wasm32` (`ABACKEND-53`, `REQ-TGT-199`), isolates backend caches by `(TargetId.Riscv64Linux, TargetFeatureSet, CallConv.RiscV, OptProfile, CodegenFingerprint)` and preserves byte-identical determinism under parallel compilation (`ABACKEND-54..55`, `REQ-TGT-200..201`), and adds the flagless RV64 ISA, `LP64D` psABI, and `EM_RISCV` ELF64 object format solely behind the `TargetBackend` portability boundary with zero leakage into Core syntax, type rules, or frontend semantics (`ABACKEND-56..60`, `REQ-TGT-202..206`, `SPEC-87` AXS-RV64-001..051).
- source: SPEC-87 AXS-RV64-001..051; SPEC-81 AXS-TGTD-044..049; 0152 §59; tasks/0522 §125-160 ABACKEND-20..60; tasks/0784 §562.135-140, §562.198-200; REQ-TGT-166..206
- verify: tests/conformance/p16/e16_7_riscv64
- since: T680
- check: encoding/structural ELF64 checks, `LP64D` ABI & relaxation-free relocation tests, `TargetFingerprint` cache and parallel determinism checks, and native RV64 / `qemu-riscv64` differential execution conformance tests against `--interp`, `x86_64-linux`, and `aarch64-linux` in tests/conformance/p16/e16_7_riscv64 (delivered by T680) pass with `0 WEAK-NATIVE`

## 42. Cross-compilation, `@cfg` target matrix, hermetic sysroot/stub catalogs, and 3-level OS platform layer (SPEC-88)

### INV-XCMP-001 — Unified cross-compilation driver (`Build`/`Host`/`Target` isolation), target-parameterized `const`/`comptime` layout, and `@cfg(...)` parse-all-then-prune-before-resolve semantics
- statement: `compiler/hir/cfg` and `compiler/driver/cross` compile from one unified `axiomc` binary (`--target <triple>`) without third-party compilers (`REQ-TOOL-001`), maintain strict `Build` vs `Host` vs `Target` separation while keeping Core syntax and frontend stages ISA-independent behind the common self-hostable `TargetBackend` contract (`AMACHINE-91..95`, `ABACKEND-97..98`, `REQ-TGT-080..084, 322..323`), isolate `TargetParameterized` and `TargetSpecific` caches and `target/<canonical-triple>/<profile>/` outputs by `TargetFingerprint` + `CfgEnvFingerprint` (`ABACKEND-94`, `REQ-TGT-319`), evaluate `const` and `comptime` layout/width/endian queries (`size_of<T>()`, `align_of<T>()`, `usize`/`isize` bounds, `to_ne_bytes`) strictly against `target_spec` rather than host `sizeof(size_t)` (`ATARGET-17..18, 22..24, 44`), diagnose unsupported target requirements explicitly (`ABACKEND-96`, `REQ-TGT-321`), and lex/parse all `@cfg(...)` branches in full, validate closed-set predicates (`AX_NAME_INVALID_CFG_PREDICATE`), and prune inactive constructs before name resolution and typechecking (`SPEC-88` AXS-XCMP-001..020).
- source: SPEC-88 AXS-XCMP-001..020; SPEC-02 AXS-GRM-024, §12; SPEC-04 AXS-EXT-052, AXS-EXT-091; SPEC-60 AXS-CTM-003, AXS-CTM-013; 0097 §1-10, §54, §57 AOS-01..07, AOS-35; 0220 §30, §32-35 AOS-37..38; tasks/0453 §194.1-12, §194.26-32, §194.38-40 ATARGET-20..28, ATARGET-40, ATARGET-44..45; tasks/0518 §151 AMACHINE-91..95; tasks/0524 §112 ABACKEND-94, ABACKEND-96..98; tasks/0587 §1-11, §23-25, §32-36 ATARGET-01..10, ATARGET-17..18, ATARGET-26..27; REQ-TOOL-001, REQ-TGT-080..084, REQ-TGT-319, REQ-TGT-321..323
- verify: tests/run/cfg_target, tests/ui/cfg, tests/selfhost/hir, tests/selfhost/driver
- since: T682
- check: positive and negative tests in tests/run/cfg_target, tests/ui/cfg, tests/selfhost/hir, and tests/selfhost/driver (delivered by T682) verify `@cfg` boolean combinators across all placement sites, syntax-error and `AX_NAME_INVALID_CFG_PREDICATE` detection inside inactive `@cfg` branches, target-parameterized `size_of<usize>()` (`4` on `wasm32-*`, `8` on 64-bit targets), and multi-target cache isolation

### INV-XCMP-002 — Hermetic zero-third-party-compiler cross-linking (`--sysroot` & built-in OS import stub catalogs) and 3-level OS platform layer (`std.*` / `std.os.*` / `std.sys.*`)
- statement: `compiler/link/sysroot` and `std/os` link cross-compiled PE/COFF, ELF64, Mach-O 64, and `.wasm` images hermetically without probing host `/usr/lib` or `C:\Windows\System32` paths and without external compilers or SDKs (`REQ-TOOL-001`), using deterministic `--sysroot` / `--target-sdk` / `-L` resolution (`AX_DRIVER_SYSROOT_NOT_FOUND`), `SysrootFingerprint` cache keys, forward-slash path normalization for cross-host byte-for-byte reproducibility (`ABACKEND-95`, `REQ-TGT-320`), built-in OS import stub catalogs (`kernel32`/`ntdll`/`ws2_32`/`bcrypt`, Linux static syscall & `libc.so.6` stubs, macOS `libSystem.B.dylib`/`.tbd`, Android Bionic stubs, `wasi_snapshot_preview1`), `Axiom LIR` as the sole native backend portability boundary (`ABACKEND-99..100`, `REQ-TGT-324..325`), and the acyclic 3-level OS layer separating portable UTF-8 Level-1 `std.*` (`!Copy` + `Drop` + fallible `close()`), `@cfg`-gated Level-2 `std.os.{windows,linux,macos,android,wasi,unix,error}` typed opaque handles (`OwnedHandle`/`OwnedFd`/`OwnedWasiFd`), and static `@cfg`-dispatched Level-3 `std.sys.*` providers (`SPEC-88` AXS-XCMP-008, AXS-XCMP-021..028, AXS-PLAT-001..022).
- source: SPEC-88 AXS-XCMP-008, AXS-XCMP-021..028, AXS-PLAT-001..022; SPEC-04 AXS-EXT-110; SPEC-52 AXS-FRE-002..003; 0097 §1, §7-8, §11-27, §51-55 AOS-01..35; 0220 §1-39 AOS-20..40; tasks/0336 §15-24, §49-52, §73-80 AFFI2-58..75, AFFI2-91..93; tasks/0453 §194.20-23, §194.41-43 ATARGET-29..32, ATARGET-46..50; tasks/0524 §112 ABACKEND-95, ABACKEND-99..100; tasks/0587 §13-22 ATARGET-11..16; REQ-TOOL-001, REQ-TGT-320, REQ-TGT-324..325
- verify: tests/std/os_platform, tests/selfhost/link
- since: T683
- check: platform and cross-linker tests in tests/std/os_platform and tests/selfhost/link (delivered by T683) verify built-in Windows/Linux/macOS/Android/WASI stub cross-linking without host library leakage, `--sysroot` error handling, Level-1 portable UTF-8 & `close()`/`Drop` parity, Level-2 `std.os.*` `@cfg` gating (`AX_NAME_UNRESOLVED_IMPORT` on foreign targets) and `unsafe` `FromRaw*` boundaries, and static `std.core.host` -> `std.sys.*` dispatch

### INV-XCMP-003 — End-to-end E16.8 cross-compilation target matrix, `Axiom LIR` semantic portability boundary, cross-host determinism, and 3-level OS platform conformance
- statement: The E16.8 conformance suite certifies across `x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-macos`, `aarch64-android`, `wasm32-wasi`, and `wasm32-freestanding` that a single `axiomc` host binary compiles single-source programs cleanly for every target without third-party toolchains (`REQ-TOOL-001`), that all supported targets pass the common semantic conformance suite with frontend meaning strictly separated from backend hardware/VM realization (`ABACKEND-93`, `0524 §113`, `REQ-TGT-318, 326`), that `@cfg` positive/negative pruning, target-parameterized `const`/`comptime` layout, cross-host byte-for-byte reproducibility, and 3-level OS handle/error/UTF-8 contracts hold uniformly, and that runnable target binaries agree differentially with `--interp` (`0 WEAK-NATIVE`, `SPEC-88` AXS-XCMP-001..028, AXS-PLAT-001..024).
- source: SPEC-88 AXS-XCMP-001..028, AXS-PLAT-001..024; 0097; 0220; tasks/0336; tasks/0453; tasks/0518 §151 AMACHINE-91..95; tasks/0524 §112-113 ABACKEND-93..100; tasks/0587; REQ-TOOL-001, REQ-TGT-080..084, REQ-TGT-318..326
- verify: tests/conformance/p16/e16_8_cross_compile
- since: T684
- check: cross-build binary inspection, `@cfg` positive/negative UI checks, cross-host determinism checks, and native/WSL/QEMU/WASI differential execution tests against `--interp` in tests/conformance/p16/e16_8_cross_compile (delivered by T684) pass with `0 WEAK-NATIVE`

## 43. Cross-target artifact kinds, static archive formats, dynamic library matrix, and library symbol resolution (SPEC-89)

### INV-ARTM-001 — Unified cross-target static archive producer (`CoffAr`, `GnuAr` + `/SYM64/`, `BsdAr` + `__.SYMDEF SORTED`) and native `.axlib` (`lib.axrmeta`) serialization
- statement: `compiler/obj/archive_matrix` serializes byte-deterministic `"!<arch>\n"` archives directly without external archivers or intermediate assembly (`REQ-TOOL-001`, `REQ-TGT-101, 103, 151, 184`), zeroing `ar_date`, `ar_uid`, and `ar_gid` with harmonized `ar_mode` (`"0       "` in `CoffAr` and `GnuAr` pseudo-members, `"100644  "` in regular `GnuAr`/`BsdAr` members; `REQ-TGT-106, 320`), emitting Microsoft 1st/2nd `/` + `//` tables for `CoffAr`, GNU big-endian `/` (`u32be`) or `/SYM64/` (`u64be` at `>= 4 GiB`) + `//` tables for `GnuAr`, BSD `#1/<byte_len>` extended names (8-byte `MH_OBJECT` payload-aligned) + little-endian `__.SYMDEF SORTED` / `__.SYMDEF_64` `ranlib` tables for `BsdAr`, and embedding `lib.axrmeta` (`SPEC-24` `.axmi` + generic `Verified MIR`) ahead of canonical `CGU` object members for `--kind axlib` (`SPEC-89` AXS-ARTM-001..014).
- source: SPEC-89 AXS-ARTM-001..014; SPEC-04 AXS-EXT-070; SPEC-24 AXS-ART-001..005, AXS-ART-010..014, AXS-ART-020, AXS-ART-023; SPEC-26 AXS-WLIB-010..012; SPEC-27 AXS-LNK-004; SPEC-80 AXS-ELFS-029; SPEC-81 AXS-TGTD-039; SPEC-84 AXS-MACHO-019; SPEC-86 AXS-WASM-027; SPEC-88 AXS-XCMP-009; 0097 §27; 0164 §24, §33; 0185; 0197 §24-25; 0217 §19, §44-45 ALINK-28, ALINK-50..51; tasks/0369 §10; tasks/0453 §194.28, §194.42; tasks/0518 §151 AMACHINE-112, AMACHINE-114; tasks/0521 §156 AARM-57; tasks/0522 §159 ABACKEND-38; REQ-TOOL-001, REQ-TGT-101, REQ-TGT-103, REQ-TGT-151, REQ-TGT-184
- verify: tests/link/static_matrix, tests/selfhost/obj
- since: T686
- check: archive container round-trip, host `ar`/`llvm-ar` interoperability, `CoffAr`/`GnuAr`/`BsdAr` symbol-directory, `lib.axrmeta` packaging, and repeat-build byte-identity tests in tests/link/static_matrix and tests/selfhost/obj (delivered by T686) pass cleanly

### INV-ARTM-002 — Demand-driven fixed-point archive extraction, scoped `--whole-archive` / `-force_load`, diamond `axlib` coherence, and final-image `.axmeta`/`.axmir`/`.axlto` stripping
- statement: `compiler/link/archive_resolve` resolves static `.lib`/`.a`/`.axlib` archives via a deterministic FIFO fixed-point loop that extracts only members needed to satisfy unresolved symbols (including mutually recursive archives while leaving unused members unlinked; `REQ-TGT-247`), enforces positional `--whole-archive` / `--no-whole-archive` and `-force_load` scoping (`AX_LINK_UNMATCHED_WHOLE_ARCHIVE`), rejects non-hermetic `"!<thin>\n"` archives (`AX_LINK_THIN_ARCHIVE_UNSUPPORTED`), enforces cross-format `Strong` vs `Weak` vs `Comdat` resolution and diamond `axlib` `InterfaceFingerprint` coherence (`AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_AXLIB_PACKAGE_CONFLICT`, `AX_LINK_ABI_MISMATCH`; `REQ-TGT-308`), and strips 100% of embedded `.axmeta`, `.axmir`, and `.axlto` sections from every final executable and dynamic library image (`SPEC-89` AXS-ARTM-014, AXS-ARTM-025..030).
- source: SPEC-89 AXS-ARTM-014, AXS-ARTM-025..030, AXS-ARTM-032; SPEC-24 AXS-ART-020..022; SPEC-27 AXS-LNK-010..014; SPEC-75 AXS-LTO-002..003; 0164 §6-8, §24-28; 0217 §11-13, §22-23, §36-38, §42; tasks/0369 §5-7, §10-12; tasks/0523 §155 AWASM-58; tasks/0524 §112 ABACKEND-82..83; REQ-TGT-247, REQ-TGT-307, REQ-TGT-308
- verify: tests/link/static_matrix, tests/selfhost/link
- since: T686
- check: fixed-point selective extraction, circular archive resolution, `--whole-archive`/`-force_load` retention and unmatched-flag errors, thin-archive rejection, duplicate-symbol/diamond diagnostics, and final-image `.axmeta`/`.axmir`/`.axlto` zero-residue tests in tests/link/static_matrix and tests/selfhost/link (delivered by T686) pass cleanly

### INV-ARTM-003 — Windows `.def` module-definition parser/generator (`--def` / `--emit-def`), COFF short/long import `.lib` tooling, and hidden-by-default `cdylib` symbol isolation
- statement: `compiler/obj/def_import` and `compiler/link/dynlib_matrix` parse and emit Windows `.def` files supporting pinned ordinals `@1..65535`, `NONAME`, `DATA`, `PRIVATE`, and `.edata` forwarded exports `Ext = OTHER.Bar` (`AX_LINK_INVALID_DEF_FILE`, `AX_LINK_DUPLICATE_EXPORT`), produce and consume COFF short-import (`Sig1 = 0, Sig2 = 0xFFFF`) and standard 3-object import `.lib` archives with `__imp_<name>` cross-linking (`ADR-0034 §4`), and enforce across PE `.dll`, ELF64 `.so`, Mach-O `.dylib`, and WASM reactor `.wasm` that non-`@export` `pub` items remain binary-hidden (`STV_HIDDEN`, `N_PEXT`, non-`dllexport`) and never leak into dynamic export tables (`SPEC-89` AXS-ARTM-006, AXS-ARTM-015..017).
- source: SPEC-89 AXS-ARTM-006, AXS-ARTM-015..017, AXS-ARTM-032; ADR-0034 §4; SPEC-26 AXS-WLIB-004, AXS-WLIB-020..023, AXS-WLIB-030..032; SPEC-56 AXS-MOD-012; 0186; 0187; 0197 §3, §17-18; 0217 §24, §40-41; tasks/0369 §15; tasks/0563 §304.14-20; REQ-OWNER-006, REQ-TGT-060, REQ-TGT-104
- verify: tests/link/dynlib_matrix, tests/selfhost/obj
- since: T687
- check: `.def` round-trip, ordinal/`NONAME`/`DATA`/forwarder export, short/long import `.lib`, negative `AX_LINK_INVALID_DEF_FILE`, and `cdylib` non-`@export` zero-leakage tests in tests/link/dynlib_matrix and tests/selfhost/obj (delivered by T687) pass cleanly

### INV-ARTM-004 — ELF64 `.so` GNU symbol versioning (`VERSYM`/`VERDEF`/`VERNEED`), Mach-O `MH_DYLIB` `@rpath`/version triples/`MH_TWOLEVEL`, and WASM `_initialize` reactor vs `_start` command matrix
- statement: `compiler/link/dynlib_matrix` emits PIC-verified (`AX_LINK_TEXTREL_FORBIDDEN`; `REQ-TGT-060, 146`) ELF64 `ET_DYN` shared objects (`DT_SONAME`, `DT_NEEDED`, `DT_RUNPATH` + `DF_ORIGIN`, Full RELRO) with `.gnu.version` (`SHT_GNU_versym`), `.gnu.version_d` (`VERDEF`), and `.gnu.version_r` (`VERNEED`) sections from `@export(version = ...)` or `--version-script` (`AX_LINK_INVALID_VERSION_SCRIPT`), emits Mach-O `MH_DYLIB` images with `LC_ID_DYLIB` (`@rpath`/`@loader_path`/`@executable_path`), packed `X.Y.Z` `current_version`/`compatibility_version` (`AX_LINK_INVALID_DYLIB_VERSION`), two-level namespace ordinals, `LC_LOAD_WEAK_DYLIB`, `LC_REEXPORT_DYLIB`, `.tbd` consumption, and ad-hoc `LC_CODE_SIGNATURE`, and emits W3C WASM reactor modules (`_initialize` single-shot guard + `@export`/`@wasm_export` roots + explicit `Import` entries, `AX_LINK_WASM_ENTRY_CONFLICT`; `REQ-TGT-245..246`, `SPEC-89` AXS-ARTM-005, AXS-ARTM-018..024).
- source: SPEC-89 AXS-ARTM-005, AXS-ARTM-018..024, AXS-ARTM-031..032; SPEC-54 AXS-PAN-010, AXS-PAN-020; SPEC-82 AXS-ELFD-027..031; SPEC-84 AXS-MACHO-001, AXS-MACHO-013, AXS-MACHO-020..028; SPEC-85 AXS-ANDR-010..012; SPEC-86 AXS-WASM-023, AXS-WASM-028..029; SPEC-88 AXS-PLAT-012; 0196; 0197 §5, §15, §19, §23, §26; 0217 §30-35, §52-54; tasks/0369 §13-16, §22; tasks/0518 §151 AMACHINE-71, AMACHINE-115; tasks/0521 §156 AARM-52; tasks/0523 §155 AWASM-56..57; tasks/0524 §112 ABACKEND-83; tasks/0563 §304.7-13, §304.21-27; REQ-TGT-060, REQ-TGT-104, REQ-TGT-146, REQ-TGT-245, REQ-TGT-246, REQ-TGT-308
- verify: tests/link/dynlib_matrix, tests/selfhost/link
- since: T687
- check: ELF64 `VERDEF`/`VERNEED`/`VERSYM` & `$ORIGIN` `DT_RUNPATH` inspection, Mach-O `LC_ID_DYLIB`/`LC_RPATH`/`LC_REEXPORT_DYLIB`/two-level ordinal/codesign checks, WASM `_initialize` reactor vs `_start` command validation, and negative version/entry diagnostic tests in tests/link/dynlib_matrix and tests/selfhost/link (delivered by T687) pass cleanly

### INV-ARTM-005 — End-to-end E16.10 cross-target artifact & library matrix conformance, diamond dependency resolution, post-encoding verification, and byte-for-byte library determinism
- statement: The E16.10 conformance suite certifies across Windows x64, Linux x64/AArch64/RISC-V64, macOS AArch64, Android AArch64, and WASM32 that `axiomc` directly emits post-encoding-verified (`REQ-TGT-307`) `exe`, `staticlib`/`lib`, `cdylib`/`dll`, `axlib`, `obj`, and WASM command/reactor artifacts (`REQ-TGT-104, 308, 318`), resolves diamond `axlib` + `staticlib` + `cdylib` dependency graphs with deterministic `--whole-archive` overrides and `AX_LINK_DUPLICATE_SYMBOL`/`AX_LINK_AXLIB_PACKAGE_CONFLICT` diagnostics, prevents any non-`@export` symbol leakage into `.dynsym`/`.edata`/Mach-O export tries/WASM `Export` tables, strips `.axmeta`/`.axmir`/`.axlto` from final images, and produces byte-for-byte identical `.a`, `.lib`, `.axlib`, `.so`, `.dll`, `.dylib`, and `.wasm` outputs across repeated builds (`REQ-TGT-106, 320`, `SPEC-89` AXS-ARTM-001..040).
- source: SPEC-89 AXS-ARTM-001..040; 0164; 0197; 0217; tasks/0369; tasks/0453; tasks/0518 §151 AMACHINE-115, AMACHINE-117; tasks/0524 §112 ABACKEND-82..83, ABACKEND-93, ABACKEND-95; tasks/0563 §304.1-46 AIMG-20..60; REQ-TGT-106, REQ-TGT-307, REQ-TGT-308, REQ-TGT-318, REQ-TGT-320
- verify: tests/conformance/p16/e16_10_artifact_matrix
- since: T688
- check: cross-target artifact emission, diamond dependency positive/negative resolution, export-table non-leakage inspection, post-encoding verifier gates, and repeat-build byte-identity checks in tests/conformance/p16/e16_10_artifact_matrix (delivered by T688) pass 100%

## 44. Universal / multi-architecture Mach-O Fat artifacts, `x86_64-macos` slice delta, and slice inspection tooling (SPEC-90)

### INV-UNIV-001 — `x86_64-macos` (`x86_64-apple-darwin`) `TargetDesc`, `CallConv.SysV64` Darwin slice ABI, 4 KiB segment layout, and `X86_64_RELOC_*` Mach-O 64 emission
- statement: `compiler/target/x64/macos` selects machine backend lowering purely from `TargetSpec` / `TargetDesc` (`REQ-TGT-105`), registering `TargetId.X86_64Macos` (`x86_64-macos`, aliases `x86_64-apple-darwin` and `x86_64-apple-macosx*`) reusing shared x86-64 ISel/RegAlloc/encoder with `CallConv.SysV64` on Darwin (leading `_` symbol decoration, `RBP` frame-pointer chain, 128-byte hosted leaf red zone, 16-byte `RSP` call alignment, SysV variadic `va_list`, Rosetta-2-safe `x86-64-v2` baseline), deterministically emits `CPU_TYPE_X86_64 (0x01000007)` / `CPU_SUBTYPE_X86_64_ALL (3)` `MH_OBJECT`, `MH_EXECUTE`, and `MH_DYLIB` slices (`REQ-TGT-104, 106, 153`) with complete `X86_64_RELOC_*` (`0..9`) relocations, 4 KiB (`0x1000`) segment/chained-fixup page alignment (`__PAGEZERO.vmsize = 4 GiB`), 6-byte `__TEXT,__stubs`, Darwin 24-byte `tlv_descriptor` TLS, `UNWIND_X86_64_*` compact unwind, `UD2` FFI panic traps, `_stat$INODE64`/`_fstat$INODE64`/`_lstat$INODE64`/`_readdir$INODE64` 64-bit inode bindings, `64`-byte (`x86_64`) / `160`-byte (`aarch64`) `std.sys.macos` stackful fiber switching, and pre-composition SHA-256 ad-hoc `LC_CODE_SIGNATURE` (`CS_ADHOC | CS_LINKER_SIGNED = 0x00020002`, `pageSize = 12`; `REQ-TOOL-001`) + `verify_macho_image` gates (`REQ-TGT-307`, `SPEC-90` AXS-UNIV-002..009).
- source: SPEC-90 AXS-UNIV-002..009, AXS-UNIV-032; SPEC-02 AXS-GRM-086; SPEC-04 AXS-EXT-060..062, AXS-EXT-070..074; SPEC-34 AXS-EXEC-054; SPEC-54 AXS-PAN-020; SPEC-80 AXS-ELFS-002, AXS-ELFS-005..020, AXS-ELFS-026..027, AXS-ELFS-048; SPEC-81 AXS-TGTD-001..012; SPEC-84 AXS-MACHO-001..036; SPEC-88 AXS-XCMP-002, AXS-XCMP-007, AXS-XCMP-014, AXS-XCMP-025; SPEC-89 AXS-ARTM-021..022, AXS-ARTM-030; 0097 §27; 0163 §1-7; 0196 §1-40; 0217 §15-17, §33-34; 0220 §4, §7; tasks/0518 §151 AMACHINE-115..117; tasks/0521 §156 AARM-59; tasks/0524 §112 ABACKEND-82; tasks/0563 §304.21-25, §304.33; REQ-TOOL-001, REQ-TGT-104, REQ-TGT-105, REQ-TGT-106, REQ-TGT-153, REQ-TGT-307
- verify: tests/obj/macho_universal, tests/selfhost/obj
- since: T690
- check: `x86_64-macos` `TargetDesc`, `_` symbol mangling, `X86_64_RELOC_*` object/image encoding, 4 KiB segment & chained-fixup alignment, compact unwind, and ad-hoc `LC_CODE_SIGNATURE` tests in tests/obj/macho_universal and tests/selfhost/obj (delivered by T690) pass cleanly

### INV-UNIV-002 — Mach-O Universal 2 (`FAT_MAGIC` / `FAT_MAGIC_64`) big-endian container layout, `2^12` / `2^14` slice alignment, universal `BsdAr` archives, and `verify_universal_artifact`
- statement: `compiler/obj/macho_universal` composes and parses explicit multi-architecture Darwin executables (`MH_EXECUTE`), dynamic libraries (`MH_DYLIB`), static archives (`BsdAr` `.a`), and Axiom package archives (`BsdAr` `.axlib` with slice-local `lib.axrmeta` carrying `TargetFingerprint`, `REQ-TGT-200`) using big-endian 8-byte `fat_header` + 20-byte `fat_arch` (`FAT_MAGIC = 0xCAFEBABE`) or automatically promoted 32-byte `fat_arch_64` (`FAT_MAGIC_64 = 0xCAFEBABF` when any slice `offset` or `size >= 2^32`, `reserved = 0`), enforces `align = 12` (4 KiB) for `CPU_TYPE_X86_64` and `align = 14` (16 KiB) for `CPU_TYPE_ARM64`, sorts slices deterministically by ascending `(cputype, cpusubtype & 0x00FF_FFFF)` with `0x00` gap padding, preserves per-slice `LC_UUID` (`BLAKE3("axiom-macho-uuid-v1" || ...)`) and `LC_CODE_SIGNATURE` verbatim, wraps slice-relative `__.SYMDEF SORTED` `BsdAr` archives inside Fat containers for linker consumption, and enforces `verify_universal_artifact` (`AX_LINK_DUPLICATE_FAT_ARCH`, `AX_LINK_FAT_SLICE_KIND_MISMATCH`, `AX_LINK_UNALIGNED_FAT_SLICE`, `AX_LINK_BAD_UNIVERSAL`, `AX_LINK_BAD_CODESIGN`; `REQ-TGT-001, 104, 106, 153, 200, 307`, `SPEC-90` AXS-UNIV-010..025).
- source: SPEC-90 AXS-UNIV-001, AXS-UNIV-010..025, AXS-UNIV-032; SPEC-04 AXS-EXT-070, AXS-EXT-074; SPEC-24 AXS-ART-022..024; SPEC-84 AXS-MACHO-019..026; SPEC-89 AXS-ARTM-008..013, AXS-ARTM-021..022, AXS-ARTM-025..026, AXS-ARTM-030; 0196 §23-24, §34; 0217 §19, §44; tasks/0453 §194.29, §194.42, §194.44 ATARGET-43; tasks/0518 §151 AMACHINE-115, 117; tasks/0521 §156 AARM-59..60; tasks/0522 §159 ABACKEND-54; tasks/0524 §112 ABACKEND-82, ABACKEND-94..95; tasks/0563 §304.5, §304.30-38, §304.45 AIMG-32..34, AIMG-50; tasks/0587 §30-32, §36, §39 ATARGET-22; REQ-TGT-001, REQ-TGT-104, REQ-TGT-106, REQ-TGT-153, REQ-TGT-154, REQ-TGT-200, REQ-TGT-307, REQ-TGT-319, REQ-TGT-320
- verify: tests/obj/macho_universal, tests/selfhost/obj
- since: T690
- check: `FAT_MAGIC` and `FAT_MAGIC_64` big-endian serialization/round-trip, `align = 12`/`14` offset verification, ascending `cputype` sorting, universal `MH_EXECUTE`/`MH_DYLIB`/`BsdAr` `.a` composition, per-slice SHA-256 `LC_CODE_SIGNATURE` preservation, and negative Fat container diagnostic tests in tests/obj/macho_universal and tests/selfhost/obj (delivered by T690) pass cleanly

### INV-UNIV-003 — Driver `--universal-targets` multi-slice orchestration, three-tier `CompilerDB` cache isolation, and native `lipo`-free slice inspection/extraction CLI
- statement: `compiler/driver/universal` and `compiler/driver/emit_universal` orchestrate explicit `--universal-targets <t1>,<t2>` (`TargetSpec`-driven slice selection, `REQ-TGT-001, 105`) and `--compose-universal` builds (`AX_DRIVER_INVALID_UNIVERSAL_TARGETS`, `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE`), sharing Tier-A (`TargetIndependent` AST/source) queries once while isolating per-slice `@cfg` evaluation, target-parameterized `const`/`comptime` layout, MIR/OptIR/LIR codegen, Mach-O linking, and ad-hoc signing under distinct 128-bit `TargetFingerprint` `(TargetId, TargetFeatureSet, CallConv / AbiFingerprint, OptProfile, CodegenFingerprint)` cache keys in `target/<canonical-triple>/<profile>/` (`REQ-TGT-154, 200, 319`), and provide native Xcode-free `--inspect-slices` (`--emit=slices` / `obj inspect --slices`), `--extract-slice <arch>`, and `--verify-arch <arch>` CLI commands with deterministic text and `--json` output (`AX_LINK_FAT_ARCH_NOT_FOUND`; `REQ-TOOL-001`, `SPEC-90` AXS-UNIV-026..032).
- source: SPEC-90 AXS-UNIV-001, AXS-UNIV-026..032; SPEC-21; SPEC-22; SPEC-23; SPEC-88 AXS-XCMP-002, AXS-XCMP-005, AXS-XCMP-009; SPEC-89 AXS-ARTM-002, AXS-ARTM-031; 0097 §27; tasks/0453 §194.29-32, §194.43, ATARGET-39..40, ATARGET-43; tasks/0518 §151 AMACHINE-116; tasks/0521 §156 AARM-60; tasks/0522 §159 ABACKEND-54; tasks/0524 §112 ABACKEND-94; tasks/0563 §304.34; tasks/0587 §5-8, §30, §33-38, ATARGET-06..09, ATARGET-13, ATARGET-26; REQ-TOOL-001, REQ-TGT-001, REQ-TGT-105, REQ-TGT-154, REQ-TGT-200, REQ-TGT-319
- verify: tests/driver/universal, tests/selfhost/driver
- since: T691
- check: `--universal-targets` multi-slice build, Tier-B/C per-slice `@cfg` and `TargetFingerprint` cache isolation, `--compose-universal`, `--inspect-slices` (`--json`), `--extract-slice` round-trip byte identity, `--verify-arch`, and CLI diagnostic tests in tests/driver/universal and tests/selfhost/driver (delivered by T691) pass cleanly

### INV-UNIV-004 — End-to-end E16.11 Universal 2 executable, `.dylib`, and static archive conformance, cross-slice behavioral equivalence, and cross-host bit-for-bit determinism
- statement: The E16.11 conformance suite certifies across `x86_64-macos` (`x86_64-apple-darwin`) and `aarch64-macos` (`aarch64-apple-darwin`) slices that `axiomc` preserves invariant Core language semantics (`REQ-TGT-318`) and equivalent observable program behavior across `x86_64-macos`, `aarch64-macos`, and `--interp` (`REQ-TGT-199`), emits valid Universal 2 `MH_EXECUTE`, `MH_DYLIB`, and `BsdAr` `.a`/`.axlib` containers (`REQ-TGT-001`) with `@cfg(target_arch = ...)` specialization, big-endian `fat_header`/`fat_arch`/`fat_arch_64` descriptors, 4 KiB x86_64 (`align = 12`) and 16 KiB ARM64 (`align = 14`) slice alignment, valid per-slice SHA-256 `LC_CODE_SIGNATURE` digests preserved across `--extract-slice`, deterministic `E9000–E9014` (`AX_DRIVER_*` / `AX_LINK_*`) diagnostics on duplicate architectures, heterogeneous slice kinds, unaligned offsets, and missing slices, and 100% bit-for-bit reproducible Universal binaries across repeated and cross-host builds (`REQ-TGT-106, 153, 320`, `SPEC-90` AXS-UNIV-001..036).
- source: SPEC-90 AXS-UNIV-001..036; 0196; 0217; tasks/0453 §194.29, §194.42, §194.44 ATARGET-43; tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-59, AARM-63; tasks/0522 §159 ABACKEND-53, ABACKEND-55; tasks/0524 §112 ABACKEND-82, ABACKEND-93, ABACKEND-95; tasks/0563 §304.21-38; tasks/0587 §30-39 ATARGET-22, ATARGET-30; REQ-TGT-001, REQ-TGT-106, REQ-TGT-153, REQ-TGT-199, REQ-TGT-307, REQ-TGT-318, REQ-TGT-320
- verify: tests/conformance/p16/e16_11_universal_artifacts
- since: T692
- check: Universal 2 `MH_EXECUTE`/`.dylib`/`.a`/`.axlib` emission, `@cfg` slice divergence, `--inspect-slices`/`--extract-slice`/`--verify-arch` validation, SHA-256 `LC_CODE_SIGNATURE` page-hash checks, `E9000–E9014` negative diagnostic cases, and repeat-build byte-identity checks in tests/conformance/p16/e16_11_universal_artifacts (delivered by T692) pass 100%

## 45. Windows ARM64 (`aarch64-pc-windows-msvc`) ABI, `X18` TEB, `__chkstk`, COFF `0xAA64`, `.pdata`/`.xdata` SEH unwind, and PE32+ linking (SPEC-91)

### INV-WARM-001 — `CallConv.WinArm64` register reservation (`X18` TEB), non-variadic `HFA`/`HVA` vs GPR-only variadic layout, and C/POD `X8` vs C++ `X0`/`X1` `sret` ABI
- statement: On `TargetId.AArch64Windows` (`aarch64-windows` / `aarch64-pc-windows-msvc`; task-card shorthand `INV-WIN-ARM64-01`), `compiler/abi/win_arm64` reserves `X18` strictly across all code as the Windows Thread Environment Block (`TEB`) pointer (forbidding GPR allocation or writes to `X18`/`W18` and restricting reads to synthesized TEB loads `[X18, #0x10]` / `[X18, #0x58]` or `std.sys.windows.arm64` TEB intrinsics, enforced by `verify_mc` `AX_VERIFY_MC_ILLEGAL`), preserves `X19..X28`, `X29` (`FP`), `X30` (`LR`), `SP` (`16`-byte aligned at all call sites and `SP`-base instructions, `red_zone = 0`, `shadow_space = 0`), and low 64-bit `D8..D15` (upper bits `V8..V15[127:64]` and `V0..V7, V16..V31` volatile), classifies non-variadic `HFA`/`HVA` (`1..=4` `f32`/`f64`/vector elements) into `V0..V7`, even-aligned `i128`/`u128` pairs into `X0:X1..X6:X7` (never split across `X7`+stack), `<= 16`B composites into `1..2` GPRs, and `> 16`B composites as caller-copied `8`B pointers, disables `V0..V7` and `HFA`/`HVA` completely across the entire call for variadic functions (`extern "C" fn(..., ...)` uses `X0..X7` + `8`B stack slots for both fixed and `...` arguments, `VaList = *mut u8`), and distinguishes C / `@repr(C)` POD `> 16`B `X8` indirect returns from C++ non-POD free-function `X0` `sret` and C++ instance-method `X0 = this, X1 = sret` returns (`REQ-TGT-105, 114, 124, 125, 127`, `SPEC-91` AXS-WA64-001..007, AXS-WA64-010).
- source: SPEC-91 AXS-WA64-001..007, AXS-WA64-010, AXS-WA64-033, AXS-WA64-035; SPEC-50 AXS-UNS-031..035; SPEC-81 AXS-TGTD-001..018, AXS-TGTD-036..038; SPEC-83 AXS-A64-001..018; 0186 §2; 0193 §1-10, §15-20; tasks/0453 §194.2-10, §194.18; tasks/0521 §156 AARM-20..37; REQ-TGT-105, REQ-TGT-114, REQ-TGT-124, REQ-TGT-125, REQ-TGT-127
- verify: tests/obj/coff_arm64, tests/selfhost/abi
- since: T694
- check: `CallConv.WinArm64` scalar/`i128`/`HFA`/`HVA`/composite/variadic/C-POD-`X8`/C++-`X0`-`X1` lowering, `VaList` layout, and `verify_mc` `X18` TEB reservation tests in tests/obj/coff_arm64 and tests/selfhost/abi (delivered by T694) pass cleanly

### INV-WARM-002 — Canonical `X29`/`X30` frame layout, `BL __chkstk` (`X15 = alloc_bytes >> 4`) guard-page probing, and `.pdata` packed / `.xdata` unpacked SEH unwind derivation
- statement: On `aarch64-windows` (task-card shorthand `INV-WIN-ARM64-02`), `compiler/target/aarch64/win_frame` maintains an unbroken `16`-byte-aligned `(X29, X30)` frame-pointer chain in every non-leaf, dynamic-allocation, or unwindable function (`ADR-0003`), loads `X15 = alloc_bytes >> 4`, invokes `BL __chkstk` (`IMAGE_REL_ARM64_BRANCH26`, clobbering only `X16, X17, X30, NZCV` while preserving `X0..X8, X15, SP` and probing `4 KiB` pages down to `[X18, #0x10]` `NT_TIB64.StackLimit`) after saving `X30`, and executes extended-register `SUB SP, SP, X15, LSL #4` (`0xCB2F73FF`) whenever `alloc_bytes >= 4096` bytes (`REQ-TGT-129, 130, 131`), and derives 8-byte `.pdata` `IMAGE_ARM64_RUNTIME_FUNCTION_ENTRY` records directly from `FramePlan` (`REQ-TGT-152`) — emitting packed `.pdata` (`Flag = 1`/`2`) only when canonical frame constraints hold (strictly excluding `1` saved FP register `D8` alone because `RegF = 1..=7` encodes `2..=8` FP registers `D8..D[8+RegF]`) and otherwise emitting `4`-byte-aligned `.xdata` (`Vers = 0`, exact reverse-prologue / forward-epilogue `alloc_*` and `save_*` opcodes including `save_r19r20_x` `z = off/8` vs `save_fplr_x` `z = off/8 - 1` and `5`-bit `z` on `save_reg_x`/`save_freg_x`, terminated by `0xE4` `end` or `0xE5` `end_c`, with `X = 1` `__axiom_seh_personality` cleanup/FFI no-unwind barrier scopes under `--panic unwind`, `REQ-FFI-004`; `AX_LINK_BAD_UNWIND_INFO` on malformed records; `SPEC-91` AXS-WA64-008..009, AXS-WA64-018..024).
- source: SPEC-91 AXS-WA64-008..009, AXS-WA64-018..024, AXS-WA64-031, AXS-WA64-033, AXS-WA64-035; ADR-0003; SPEC-52 AXS-FRE-013, AXS-FRE-022; SPEC-54 AXS-PAN-002..004, AXS-PAN-013, AXS-PAN-020; SPEC-83 AXS-A64-019..021; 0107 §64; 0186 §2; 0188 §2-35, §38-55; 0193 §8, §18; tasks/0521 §156 AARM-33..37, AARM-58; REQ-FFI-004, REQ-TGT-124, REQ-TGT-129, REQ-TGT-130, REQ-TGT-131, REQ-TGT-152
- verify: tests/obj/coff_arm64, tests/selfhost/obj
- since: T694
- check: canonical `STP`/`LDP` prologue/epilogue emission, `>= 4096`B `X15 = alloc_bytes >> 4` + `BL __chkstk` + `0xCB2F73FF` `SUB SP, SP, X15, LSL #4` encoding, packed `.pdata` (`RegF` `0` and `2..=8` vs `1`-FP `.xdata` fallback), unpacked `.xdata` opcode byte verification, and negative `AX_VERIFY_MC_ILLEGAL` / `AX_LINK_BAD_UNWIND_INFO` tests in tests/obj/coff_arm64 and tests/selfhost/obj (delivered by T694) pass cleanly

### INV-WARM-003 — Deterministic COFF `0xAA64` object emission, `IMAGE_REL_ARM64_*` (`0x0000..0x0011`) relocations, associative COMDATs, and `0xAA64` `CoffAr` / short-import `.lib` archives
- statement: `compiler/obj/coff_arm64` (task-card shorthand `INV-WIN-ARM64-03`) enforces pre-encoding `verify_mc` invariants (`REQ-TGT-162`), emits deterministic COFF relocatable objects (`Machine = IMAGE_FILE_MACHINE_ARM64 = 0xAA64`, `TimeDateStamp = 0`, `@feat.00 = 0`, undecorated COFF symbol names, `IMAGE_SCN_LNK_COMDAT` sections with `IMAGE_COMDAT_SELECT_ASSOCIATIVE` `.pdata`/`.xdata` children, and non-allocatable `.axmeta`/`.axmir`/`.axlto` sections with `Characteristics = 0x42000200` `IMAGE_SCN_LNK_INFO | IMAGE_SCN_MEM_DISCARDABLE | IMAGE_SCN_MEM_READ`) without external assemblers (`REQ-TOOL-001`, `REQ-TGT-106, 151`), encodes and validates all 18 `IMAGE_REL_ARM64_*` (`0x0000..0x0011`) relocation kinds (`ADDR32`, `ADDR32NB`, `BRANCH26`, `PAGEBASE_REL21`, `REL21`, `PAGEOFFSET_12A`/`12L`, `SECREL`, `SECREL_LOW12A`/`HIGH12A`/`LOW12L`, `SECTION`, `ADDR64`, `BRANCH19`, `BRANCH14`, `REL32`, rejecting `0x000C` `TOKEN` and codes `> 0x0011` with `AX_LINK_BAD_OBJECT`; `REQ-TGT-149`), packages deterministic `CoffAr` `"!<arch>\n"` static `.lib` and `IMPORT_OBJECT_HEADER` (`Machine = 0xAA64`, `IMPORT_OBJECT_NAME = 1`) short-import `.lib` archives (rejecting foreign-machine `0x8664` / `0xA641` inputs with `AX_LINK_ARTIFACT_TARGET_MISMATCH`), and runs post-encoding COFF object/archive structural verification (`verify_coff_obj` / `verify_archive`) with crash-safe `<out>.tmp.<pid>` atomic publication (`REQ-TGT-307`, `SPEC-91` AXS-WA64-011..017).
- source: SPEC-91 AXS-WA64-011..017, AXS-WA64-033, AXS-WA64-035; SPEC-24 AXS-ART-020..023; SPEC-26 AXS-WLIB-010..012, AXS-WLIB-030..031; SPEC-27 AXS-LNK-011..013, AXS-LNK-020..022; SPEC-83 AXS-A64-037; SPEC-89 AXS-ARTM-008, AXS-ARTM-017, AXS-ARTM-028..030; 0097 §27; 0181; 0185 §1-24; 0186 §4; 0187 §18-23; 0193 §23-24; tasks/0521 §156 AARM-55, AARM-57, AARM-68; tasks/0524 §112 ABACKEND-81..82; tasks/0563 §304.45 AIMG-50; REQ-TOOL-001, REQ-TGT-106, REQ-TGT-124, REQ-TGT-149, REQ-TGT-151, REQ-TGT-162, REQ-TGT-307
- verify: tests/obj/coff_arm64, tests/selfhost/obj
- since: T694
- check: COFF `0xAA64` header/section/symbol/string-table serialization, `.axmeta`/`.axmir`/`.axlto` `0x42000200` headers, all `IMAGE_REL_ARM64_*` (`0x0000..0x0011`) bit-field round-trips, associative `.pdata`/`.xdata` COMDAT folding, `CoffAr` + `0xAA64` short-import `.lib` generation, post-encoding `verify_coff_obj` / `verify_archive` checks, and negative `AX_LINK_BAD_OBJECT` / `AX_LINK_ARTIFACT_TARGET_MISMATCH` tests in tests/obj/coff_arm64 and tests/selfhost/obj (delivered by T694) pass cleanly

### INV-WARM-004 — Native MSVC-free PE32+ ARM64 `.exe`/`.dll`/import-`.lib` linker, `12`-byte `__imp_` thunks, `±128 MiB` veneers, `[X18, #0x58]` TLS, and `std.sys.windows.arm64`
- statement: `compiler/link/pe_arm64` and `std/sys/windows/arm64` (task-card shorthand `INV-WIN-ARM64-04`) link COFF `0xAA64` objects and `.lib` / short-import `.lib` (`Machine = 0xAA64`) archives directly into W^X PE32+ ARM64 executables (`--kind exe` and synonym `--kind bin`, default `ImageBase = 0x0000_0001_4000_0000`) and dynamic libraries (`--kind dll`/`cdylib`, default `ImageBase = 0x0000_0001_8000_0000`) without `link.exe`, `lld-link`, or MSVC CRT/SDK dependencies (`REQ-TOOL-001`, `REQ-TGT-104, 151, 152, 308`), setting `Magic = 0x020B`, `DllCharacteristics = 0x0160` (`HIGH_ENTROPY_VA | DYNAMIC_BASE | NX_COMPAT`), stripping `100%` of `.axmeta`/`.axmir`/`.axlto` sections (`SPEC-24` AXS-ART-022, `SPEC-89` AXS-ARTM-029), synthesizing `12`-byte `ADRP X16 + LDR X16 + BR X16` DLL import thunks (`0187` AIMPORT-20..34) and `12`-byte `ADRP X16 + ADD X16 + BR X16` out-of-range `±128 MiB` `BRANCH26` veneers, emitting RVA-sorted non-overlapping `IMAGE_DIRECTORY_ENTRY_EXCEPTION` `.pdata`, `4 KiB`-blocked `IMAGE_REL_BASED_DIR64` (`type = 10`) `.reloc` fixups (forbidding `.text` relocations via `AX_LINK_TEXTREL_FORBIDDEN`), `IMAGE_TLS_DIRECTORY64` `.tls` accessed via `[X18, #0x58]` + `_tls_index`, built-in CRT-free `__chkstk` and `mainCRTStartup` / `DllMainCRTStartup`, Win32 fiber switching preserving `X18`, hermetic `0xAA64` OS import stubs (`kernel32.dll`, `ntdll.dll`, `ws2_32.dll`, `bcrypt.dll`, …), and post-encoding `verify_coff_pe` verification with atomic output (`REQ-TGT-106, 307`, `SPEC-91` AXS-WA64-024..032).
- source: SPEC-91 AXS-WA64-016, AXS-WA64-024..033, AXS-WA64-035; SPEC-24 AXS-ART-022; SPEC-26 AXS-WLIB-001..005, AXS-WLIB-020..023, AXS-WLIB-030..032; SPEC-27 AXS-LNK-005, AXS-LNK-011..014, AXS-LNK-020..024; SPEC-32 AXS-SYNC-020..023; SPEC-34 AXS-EXEC-055; SPEC-54 AXS-PAN-013, AXS-PAN-020; SPEC-88 AXS-XCMP-021..023, AXS-PLAT-020; SPEC-89 AXS-ARTM-002..003, AXS-ARTM-006, AXS-ARTM-015..017, AXS-ARTM-027, AXS-ARTM-029..030; 0097 §27; 0107 §64; 0181; 0185; 0186; 0187 §8-25, §40 AIMPORT-20..34; 0188; 0193; tasks/0453 §194.20-28; tasks/0521 §156 AARM-50..62; tasks/0524 §112 ABACKEND-82..83; tasks/0563 §304.14-20, §304.33-45 AIMG-20..60; REQ-FFI-004, REQ-TOOL-001, REQ-TGT-104, REQ-TGT-106, REQ-TGT-124, REQ-TGT-151, REQ-TGT-152, REQ-TGT-307, REQ-TGT-308
- verify: tests/link/pe_arm64, tests/selfhost/link
- since: T695
- check: PE32+ ARM64 `.exe`/`.dll`/short-import-`.lib` emission, `12`-byte import thunk & `±128 MiB` veneer synthesis, RVA-sorted `.pdata`/`.reloc`/`.tls` layout, `.axmeta`/`.axmir`/`.axlto` stripping, `verify_coff_pe` checks, CRT-free `__chkstk` & `std.sys.windows.arm64` TEB/fiber helpers, and negative linker diagnostic tests in tests/link/pe_arm64 and tests/selfhost/link (delivered by T695) pass cleanly

### INV-WARM-005 — End-to-end E16.12 Windows ARM64 conformance, cross-OS/cross-ISA behavioral equivalence, and cross-host bit-for-bit PE32+ determinism
- statement: The E16.12 conformance suite (task-card shorthand `INV-WIN-ARM64-05`) passes common target conformance suites (`REQ-TGT-197`) and certifies that `axiomc --target aarch64-windows` (`aarch64-pc-windows-msvc`) preserves invariant Core language semantics (`REQ-TGT-318`) and equivalent observable program behavior across `aarch64-windows`, `x86_64-windows`, `aarch64-linux`, and `--interp` (`REQ-TGT-157`), validates `CallConv.WinArm64` `HFA`/`HVA`, GPR-only variadics, `X8` vs `X0`/`X1` `sret` C/C++ FFI, `X18` TEB preservation, `>= 4 KiB` `__chkstk` stack probing, `.pdata`/`.xdata` SEH panic unwinding (`catch_unwind`) and `extern "C"` FFI no-unwind abort barriers (`REQ-FFI-004`), `[X18, #0x58]` `@thread_local` TLS, MSVC-free PE32+ `.exe`/`.dll`/`.lib` round-trip linking and post-encoding verification (`REQ-TOOL-001`, `REQ-TGT-307`), `"Xin chào thế giới"` UTF-8 -> UTF-16LE Win32 console/filesystem I/O, deterministic `E9100–E9119` diagnostics, and 100% bit-for-bit identical `.obj`, `.lib`, `.dll`, and `.exe` outputs across Windows x64, Linux x64, macOS ARM64, and Windows ARM64 build hosts (`REQ-TGT-106, 124, 157, 197, 307, 318, 320`, `SPEC-91` AXS-WA64-001..036).
- source: SPEC-91 AXS-WA64-001..036; 0097 §27; 0107 §64; 0181; 0185; 0186; 0187 §8-25, §40 AIMPORT-20..34; 0188; 0193; tasks/0453 §194.2-28, §194.42-44; tasks/0518 §151 AMACHINE-117; tasks/0521 §156 AARM-20..68; tasks/0522 §159 ABACKEND-51, ABACKEND-53, ABACKEND-55; tasks/0524 §112 ABACKEND-81..83, ABACKEND-93, ABACKEND-95; tasks/0563 §304.14-20, §304.33-45 AIMG-20..60; REQ-FFI-004, REQ-TOOL-001, REQ-TGT-106, REQ-TGT-124, REQ-TGT-157, REQ-TGT-162, REQ-TGT-197, REQ-TGT-307, REQ-TGT-318, REQ-TGT-320
- verify: tests/conformance/p16/e16_12_windows_arm64
- since: T696
- check: `CallConv.WinArm64` ABI/variadic/FFI matrix, `X18` TEB & `__chkstk` frame probes, `.pdata`/`.xdata` SEH unwind & FFI abort barrier, `[X18, #0x58]` TLS, PE32+ `.exe`/`.dll`/`.lib` structural inspection (and native/emulated execution when an ARM64 Windows runner is available), `E9100–E9119` negative diagnostic cases, and repeat/cross-host byte-identity checks in tests/conformance/p16/e16_12_windows_arm64 (delivered by T696) pass 100%

## 46. Language Server (`axiomc lsp`), IDE semantic engine, `AXEDITOR`/`AXCODEEDITOR`, and thin VS Code client (SPEC-100)

### INV-LSP-001 — Deterministic JSON-RPC 2.0 transport, `VfsOverlay` & UTF-8/UTF-16/UTF-32 `LineIndex`, `std.editor` (`AXEDITOR`) B-tree piece table, and partial-program recovery
- statement: `compiler/lsp/protocol`, `compiler/lsp/vfs`, `std/editor`, and the partial-program parser/resolver/type-checker recovery paths enforce exact byte-counted `Content-Length: <N>\r\n\r\n` JSON-RPC 2.0 framing, `initialize`/`initialized`/`shutdown`/`exit` lifecycle state transitions, `$/cancelRequest` (`-32800` `RequestCancelled`), in-memory `VfsOverlay` precedence (`didOpen`/`didChange`/`didClose`/`didSave`) mapped into `CompilerDB.SourceText(FileId)` (`SPEC-21` AXS-QRY-002, `SPEC-22` AXS-INC-010..012), lossless bidirectional UTF-8 byte / UTF-16 code-unit / Unicode scalar `LineIndex` conversions across multi-byte Vietnamese (`"Xin chào"`) and astral-plane (`> U+FFFF` surrogate pair) codepoints, `std.editor` (`AXEDITOR`, `tasks/1053`, `REQ-TOOL-299`) $O(\log N)$ B-tree piece-table (`PieceTree`, `EditTransaction`, `SelectionSet`, `SearchIndex`) mutations with Unicode grapheme-boundary safety and `< 2` ms p99 incremental edit latency on `>= 10` MiB files, and panic-free partial-program syntax/semantic recovery (`REQ-TOOL-188`) that lowers trailing-`.` member access (`buf.`), unclosed call lists (`process(buf, `), unclosed blocks, and incomplete patterns into poison-isolated `ExprKind.Error` / `TypeId.ERROR` nodes (`AXD-044`) while preserving 100% of sibling item identities (`SymbolId`, `TypeId`, `FunctionId`) and valid local environment entries (`SPEC-100` AXS-LSP-010..012, AXS-LSP-020..022, AXS-LSP-030..032).
- source: SPEC-100 AXS-LSP-010..012, AXS-LSP-020..022, AXS-LSP-030..032, AXS-LSP-060..063; SPEC-01 §1; SPEC-02 §9; SPEC-21 AXS-QRY-002, AXS-QRY-030..032, AXS-QRY-040..042; SPEC-22 AXS-INC-010..013; spec/diagnostics.md AXD-044, AXD-051; 0101 §1-5, §14-20; 0146 §31-37; tasks/0374; tasks/0448; tasks/0664; tasks/1053; REQ-TOOL-184, REQ-TOOL-188, REQ-TOOL-298, REQ-TOOL-299
- verify: tests/run/lsp_vfs
- since: T801
- check: JSON-RPC 2.0 `Content-Length` framing/lifecycle/cancellation, `VfsOverlay` full and incremental range edits, `LineIndex` UTF-8/UTF-16/UTF-32 round-trips on ASCII, Vietnamese, and astral surrogate-pair text, `std.editor` `PieceTree` `10` MiB edit/undo/redo/multi-cursor/search invariants, and partial-program syntax/semantic recovery tests in tests/run/lsp_vfs (delivered by T801) pass 100%

### INV-LSP-002 — Single semantic authority (`CompilerDB`), zero mandatory codegen, constraint-aware IDE queries, `AXCODEEDITOR` inlays/tokens, and thin VS Code client
- statement: `compiler/lsp/handlers`, `compiler/driver/lsp_cmd` (`axiomc lsp`), `std/editor` (`AXCODEEDITOR`), and `tools/vscode-axiom` share a single semantic engine (`CompilerDB`, `SPEC-21`/`SPEC-22`) with `axiomc check`/`build` (`REQ-TOOL-183`, `REQ-TOOL-297`, `REQ-TOOL-298`), use typed generational IDs (`SymbolId`, `TypeId`, `FunctionId`, `LocalId`, `PlaceId`; `REQ-TOOL-191`) with stable identities across incremental body edits (`REQ-TOOL-184`), execute all interactive IDE queries (`textDocument/publishDiagnostics`, `completion`, `hover`, `definition`, `references`, `prepareRename`/`rename`, `semanticTokens/full` & `range`, `inlayHint`, `codeAction`, `signatureHelp`, `documentSymbol`, `workspace/symbol`, `formatting`) through `DatabaseSnapshot` without invoking `OptIR`, `LIR`, `ObjectEmit`, or `Linker` (`REQ-TOOL-185`), enforce exact module visibility, move-liveness (`!Copy` consumed locals excluded), receiver capability (`view<T>` excludes `mut self` and consuming `self` methods; `mut_view<T>` excludes consuming `self` methods), and trait/associated-item constraints in completion (`0101 §6-13`, `0146 §31-37`, `tasks/0450`, `REQ-TOOL-189`), compute `AXCODEEDITOR` (`tasks/1054`, `REQ-TOOL-300`) delta-encoded semantic tokens and ownership/move/capability/async/comptime inlay hints directly from `CompilerDB`, and keep `tools/vscode-axiom` a zero-semantic-duplication thin client (`0101 §38-41`, `SPEC-100` AXS-LSP-001..004, AXS-LSP-040..043, AXS-LSP-050..052, AXS-LSP-060..063).
- source: SPEC-100 AXS-LSP-001..004, AXS-LSP-040..043, AXS-LSP-050..052, AXS-LSP-060..063; SPEC-21 AXS-QRY-001..006, AXS-QRY-030..034; SPEC-22 AXS-INC-001..013; SPEC-23 AXS-PAR-002..004; spec/diagnostics.md AXD-040, AXD-055..056, AXD-060; 0101 §1-41; 0146 §11-12, §31-37; tasks/0374; tasks/0448; tasks/0450; tasks/0479; tasks/0664; tasks/0693; tasks/0695; tasks/0696; tasks/1054; REQ-TOOL-183, REQ-TOOL-184, REQ-TOOL-185, REQ-TOOL-189, REQ-TOOL-191, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-300
- verify: tests/run/lsp_queries
- since: T802
- check: CLI-vs-LSP diagnostic parity, zero-codegen query-graph counter assertions, generational ID stability across body edits, visibility/move/`view`/`mut_view`/trait-filtered completion, hover, go-to-definition, find-references, hygiene-checked rename, `AXCODEEDITOR` semantic tokens & ownership/move/async inlays, `codeAction` fix-its, and `tools/vscode-axiom` thin-client manifest/grammar checks in tests/run/lsp_queries (delivered by T802) pass 100%

### INV-LSP-003 — End-to-end E19.1 LSP server, IDE semantic engine, `AXEDITOR`/`AXCODEEDITOR`, and thin VS Code client conformance
- statement: The E19.1 conformance suite (`tests/conformance/p19/e19_1_lsp_server`) certifies end-to-end compliance with `SPEC-100` across `REQ-TOOL-183`, `REQ-TOOL-184`, `REQ-TOOL-185`, `REQ-TOOL-188`, `REQ-TOOL-189`, `REQ-TOOL-191`, `REQ-TOOL-297`, `REQ-TOOL-298`, `REQ-TOOL-299`, and `REQ-TOOL-300`: 100% diagnostic parity (`code`, `severity`, `primary`, `labels`, `notes`, `helps`, `fixes`) between `axiomc check --json` and `axiomc lsp` `textDocument/publishDiagnostics`, zero backend codegen invocations across all LSP sessions, generational ID stability and green-node reuse (`SPEC-22` `try_mark_green`) across multi-revision editing sessions, partial-program recovery under syntax/type errors, constraint-aware completion/hover/definition/references/rename under ownership and `view<T>`/`mut_view<T>` capability rules, `AXEDITOR` large-buffer Unicode/grapheme invariants, `AXCODEEDITOR` semantic token & ownership/move/async inlay accuracy, thin VS Code client conformance, and repeat-run byte-for-byte JSON-RPC response determinism (`SPEC-100` AXS-LSP-001..063).
- source: SPEC-100 AXS-LSP-001..063; SPEC-21; SPEC-22; 0101 §1-41; 0146 §31-37; tasks/0374; tasks/0448; tasks/0450; tasks/0479; tasks/0664; tasks/0693; tasks/0695; tasks/0696; tasks/1053; tasks/1054; REQ-TOOL-183, REQ-TOOL-184, REQ-TOOL-185, REQ-TOOL-188, REQ-TOOL-189, REQ-TOOL-191, REQ-TOOL-297, REQ-TOOL-298, REQ-TOOL-299, REQ-TOOL-300
- verify: tests/conformance/p19/e19_1_lsp_server
- since: T803
- check: full E19.1 conformance suite in tests/conformance/p19/e19_1_lsp_server (delivered by T803) passes 100% across multi-module workspaces, partial-program recovery, constraint-filtered completion, `AXEDITOR`/`AXCODEEDITOR` editor models, and thin VS Code client verification

## 47. Canonical language form, lossless CST trivia model, and deterministic formatter (SPEC-101)

### INV-FMT-001 — Lossless 5-slot CST trivia attachment, Wadler-Lindig `Doc` layout algebra, and zero-config canonical formatting
- statement: `compiler/fmt/cst` and `compiler/fmt/printer` consume the shared `compiler/lex` and `compiler/syntax` streams inside `CompilerDB` (`REQ-TOOL-183`, `REQ-TOOL-298`), partition every valid `.ax` source buffer into tokens and trivia without gaps or losses, attach all comments (`//`, `///`, `//!`, nested `/* ... */`, `#region`/`#endregion` directives) and blank-line runs deterministically across the 5 CST slots (header, trailing same-line, inline interior, leading, dangling) preserving 100% of comment count, kind, and source order (`AXS-FMT-001..004`), evaluate the bounded-lookahead $O(N)$ Wadler-Lindig `Doc` combinator algebra (`Group`, `Indent`, `Line`, `SoftLine`, `SoftLineEmpty`, `IfBreak`, `LineSuffix`; `AXS-FMT-010..013`) under Axiom's fixed canonical policy (4-space indent, 100 Unicode scalar columns, `LF` line endings, single blank-line cap), format all surface constructs in canonical `=` and `.` syntax with sorted `use` groups, trailing binary operators on wrapped lines (`SPEC-02` continuation safety), leading-`.` method chains, preserved tail-suppression `;` on final `STMT_EXPR` when `has_semi == true` (`AXS-FMT-020..029`), and satisfy single-step idempotence $\text{fmt}(\text{fmt}(S)) = \text{fmt}(S)$ (`AXS-FMT-032`).
- source: SPEC-101 AXS-FMT-001..004, AXS-FMT-010..013, AXS-FMT-020..029, AXS-FMT-032, AXS-FMT-051..053; SPEC-01 §1-2; SPEC-02 AXS-GRM-013, AXS-GRM-019..022, AXS-GRM-030, AXS-GRM-040;ADR-0007; ADR-0008; tasks/0374; tasks/0448; tasks/0476; tasks/0693; tasks/0695; tasks/0696; REQ-TOOL-183, REQ-TOOL-298
- verify: tests/run/fmt_engine
- since: T805
- check: 5-slot CST trivia conservation (`//`, `///`, `//!`, nested `/* */`, `#region`), Wadler-Lindig `Group`/`Indent`/`IfBreak`/`LineSuffix` layout at 100 Unicode scalar columns, canonical `=`/`.`, import sorting, trailing-operator wraps vs leading-`.` chains, semantic tail-suppression `;` preservation, and `fmt(fmt(src)) == fmt(src)` unit tests in tests/run/fmt_engine (delivered by T805) pass 100%

### INV-FMT-002 — Post-format AST-equivalence verification gate, syntax-error refusal, `axiomc fmt` CLI (`--check`, `--stdin`), and LSP formatting parity
- statement: `compiler/fmt/verify`, `compiler/driver/fmt_cmd` (`axiomc fmt`), and `compiler/lsp/handlers` (`textDocument/formatting`, `textDocument/rangeFormatting`) refuse to format or mutate any input with `AX_LEX_*` or `AX_PARSE_*` diagnostics (returning exit code `1` in CLI and `null`/empty edits in LSP; `AXS-FMT-030`), execute the mandatory post-format verification gate (`AXS-FMT-031`) that re-lexes and re-parses formatted output $S' = \text{fmt}(S)$ to certify structural AST equivalence ($\text{parse}(\text{fmt}(S)) \equiv \text{parse}(S)$ including final-statement `has_semi` parity) and 100% comment conservation before any disk write or LSP `TextEdit` emission (aborting with `AX_ICE_INTERNAL` `data.stage = "fmt_verify"` and exit code `3` on any discrepancy), support deterministic lexicographical workspace/directory/file traversal, read-only CI `--check` mode (exit code `0` when canonical, exit code `1` with unified diff on `stdout` when non-canonical), `--stdin` -> `stdout` pipeline formatting, timestamp-preserving atomic writes, and 100% identical formatting output between `axiomc fmt` and LSP `textDocument/formatting` / `textDocument/rangeFormatting` (`SPEC-100` AXS-LSP-053, `SPEC-101` AXS-FMT-030..032, AXS-FMT-040..042, AXS-FMT-050).
- source: SPEC-101 AXS-FMT-030..032, AXS-FMT-040..042, AXS-FMT-050, AXS-FMT-053; SPEC-100 AXS-LSP-053; spec/diagnostics.md AXD-021, AXD-042..043; tasks/0374; tasks/0448; tasks/0476; tasks/0693; tasks/0695; tasks/0696; REQ-TOOL-183, REQ-TOOL-298
- verify: tests/run/fmt_cli
- since: T806
- check: post-format AST-equivalence & comment-conservation verifier gate, syntax-error refusal (`exit 1` with untouched files), `axiomc fmt` file/directory/workspace traversal, `--check` unified diff & exit codes `0`/`1`, `--stdin` formatting, and LSP `textDocument/formatting` & `textDocument/rangeFormatting` parity tests in tests/run/fmt_cli (delivered by T806) pass 100%

### INV-FMT-003 — End-to-end E19.2 canonical formatter conformance, idempotence, comment & UTF-8 preservation, and `--interp` vs native parity
- statement: The E19.2 conformance suite (`tests/conformance/p19/e19_2_formatter`) certifies end-to-end compliance with `SPEC-101` across `REQ-TOOL-183` and `REQ-TOOL-298`: single-step idempotence $\text{fmt}(\text{fmt}(S)) = \text{fmt}(S)$ across all Axiom surface declarations/expressions/statements/attributes, 100% comment conservation (`//`, `///`, `//!`, nested `/* */`, `#region`/`#endregion`) and multi-byte UTF-8 string/comment fidelity (`"Xin chào thế giới"`), structural AST equivalence $\text{parse}(\text{fmt}(S)) \equiv \text{parse}(S)$ and behavioral preservation under `axiomc check`/`run`, syntax-error refusal (`exit 1`, zero file corruption), `--check` and `--stdin` CLI contracts, LSP formatting parity, and 100% agreement between `--interp` and native x86-64 execution (`0 WEAK-NATIVE`; `SPEC-101` AXS-FMT-001..053).
- source: SPEC-101 AXS-FMT-001..053; SPEC-01; SPEC-02; SPEC-100 AXS-LSP-053; tasks/0374; tasks/0448; tasks/0476; tasks/0693; tasks/0695; tasks/0696; REQ-TOOL-183, REQ-TOOL-298
- verify: tests/conformance/p19/e19_2_formatter
- since: T807
- check: full E19.2 conformance suite in tests/conformance/p19/e19_2_formatter (delivered by T807) passes 100% across idempotence, trivia/UTF-8 preservation, AST equivalence, `--check`/`--stdin` CLI, LSP formatting, and `--interp` vs native execution parity (`0 WEAK-NATIVE`)

## Sources
0153 §37 (ACKERNEL, ASOURCE, AINTERN, AQUERY, APAR, ADIAG-20..24, APASS, ACACHE, ADET); 0171 §40
(AKERNEL-24..37); 0172 §1-§24; tasks/0260 §45 (ABOOT-41..80); tasks/0262 §42-§49; tasks/0360 §51
(ADIAG-20..90); 0053; 0095; 0097; 0099; 0101; 0107; 0142; 0146 §31-§37, §50-§58; 0151 §1-§25, §56-§57; 0152 §59, §78-§79; 0162; 0163; 0164; 0181; 0185; 0186; 0187; 0188; 0192; 0193; 0196; 0197; 0198; 0200; 0212; 0217; 0220; 0225; 0229; 0236; 0239; 0245; 0255; 0256; 0263 §28, §46-§47; tasks/0336; tasks/0351; tasks/0356; tasks/0369; tasks/0374; tasks/0384; tasks/0389; tasks/0402; tasks/0403; tasks/0406; tasks/0407; tasks/0448; tasks/0450; tasks/0453; tasks/0471; tasks/0472; tasks/0473; tasks/0476; tasks/0479; tasks/0512; tasks/0517; tasks/0518; tasks/0520; tasks/0521; tasks/0522; tasks/0523; tasks/0524; tasks/0526; tasks/0528; tasks/0530; tasks/0532; tasks/0533; tasks/0539; tasks/0545; tasks/0562; tasks/0563; tasks/0564; tasks/0577; tasks/0578; tasks/0582; tasks/0587; tasks/0591; tasks/0593; tasks/0664; tasks/0693; tasks/0695; tasks/0696; tasks/0700; tasks/0739; tasks/0778; tasks/0781; tasks/0784; tasks/0786; tasks/0787; tasks/0788; tasks/0789; tasks/0790; tasks/0791; tasks/0792; tasks/0793; tasks/0794; tasks/0795; tasks/0796; tasks/0797; tasks/0798; tasks/0799; tasks/0800; tasks/0801; tasks/0802; tasks/0803; tasks/0804; tasks/1053; tasks/1054; ROADMAP R3, R6–R8; ADR-0001; ADR-0002;
ADR-0003; ADR-0004 §2, §4, §8; ADR-0005 §2, §15; ADR-0011; ADR-0034 §4, §8; ADR-0036; SPEC-01 §11; SPEC-02 §10; SPEC-03; SPEC-12; SPEC-21; SPEC-22; SPEC-23; SPEC-24; SPEC-25; SPEC-26; SPEC-27; SPEC-30; SPEC-31; SPEC-32; SPEC-33; SPEC-40; SPEC-41; SPEC-42; SPEC-43; SPEC-44; SPEC-50; SPEC-51; SPEC-52; SPEC-53; SPEC-54; SPEC-55; SPEC-56; SPEC-60; SPEC-61; SPEC-62; SPEC-63; SPEC-70; SPEC-71; SPEC-72; SPEC-73; SPEC-74; SPEC-75; SPEC-76; SPEC-77; SPEC-80; SPEC-81; SPEC-82; SPEC-83; SPEC-84; SPEC-85; SPEC-86; SPEC-87; SPEC-88; SPEC-89; SPEC-90; SPEC-91; SPEC-100; SPEC-101; axiom-c-stage0.
