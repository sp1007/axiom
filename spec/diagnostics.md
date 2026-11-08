# Axiom diagnostics: code taxonomy, severity, JSON schema, fix-its

## Tóm tắt
Tài liệu chuẩn cho **chẩn đoán (diagnostic)** của compiler Axiom (axiom0 viết bằng C và axiomc viết
bằng Axiom phải dùng chung). Các điểm đã quyết định (ADR-0011):
- Chẩn đoán là **dữ liệu**: mã ổn định, mức độ, vị trí chính (file + khoảng byte), nhãn phụ, ghi chú,
  gợi ý, fix-it, và payload có cấu trúc. Câu chữ tiếng Anh không phải API, nên test chỉ kiểm mã và vị trí.
- Mã có dạng `AX_<VÙNG>_<TÊN>` (tên mô tả, không đánh số). Danh sách **18 vùng cố định**: LEX, PARSE,
  NAME, TYPE, TRAIT, PAT, MOVE, INIT, CAP, DROP, UNSAFE, CONST, VERIFY, FFI, LINK, IO, DRIVER, ICE.
  Mỗi vùng ứng với một file `bootstrap/axiom0/src/diag/codes/<VÙNG>.def`, và tiền tố của mã chỉ ra file
  chứa nó. Muốn thêm vùng phải sửa spec này trước.
- axiom0 chỉ phát hai mức `error` và `warning`; `note`/`help` là phần đính kèm, không phải mức độ. ICE
  (lỗi nội bộ compiler) là một vùng riêng, trả mã thoát 3 và không bao giờ ghi ra artifact.
- Thứ tự in ra cố định: theo file, byte bắt đầu, rồi thứ tự đăng ký của mã.
- Có định dạng hiển thị cho người và lược đồ JSON phiên bản 1; cả hai đều ghi ra stderr.
- Fix-it gồm danh sách sửa (khoảng byte + chuỗi thay thế) và mức áp dụng. Compiler không bao giờ tự sửa mã nguồn.
- §10 là danh sách mã gieo sẵn cho P1–P4, T009 đăng ký toàn bộ. Các mã LEX và PARSE lấy nguyên từ
  SPEC-01 và SPEC-02.

Status: canonical (T002, 2026-10-04). Decision record: ADR-0011. Map of the spec set: `spec/INDEX.md`.
Invariants about diagnostics: `spec/invariants.md` (INV-DIAG-*).
Consumers: T009 (engine, registry, renderers), T016 (driver, exit codes, `--json`), T005 (runner reads
`--json`), T006 (archcheck registry rule), every task that adds a code, QA (ui tests).

Conventions: rule ids `AXD-NNN` are stable and never renumbered. Source tags as in SPEC-01
(`[0146 §54]` = `docs/base/specs`, `tasks/` = `docs/base/tasks`). Invalid source text appears only in
inline code, never in `axiom` blocks.

---

## 1. Principles

**AXD-001 — Diagnostics are data.** A diagnostic is a value with the fields of §6, created by library
code and handed to a sink. Only the driver renders diagnostics (§8). Library code never prints and never exits.
[tasks/0360 §1, ADIAG-20/21; 0146 §1; 0172 §10; tasks/0260 ABOOT-60]

**AXD-002 — The code is the identity, the message is not.** Tools, tests and AI agents identify
a diagnostic by its code, primary span and `data` payload, never by its message text. Messages may change
at any time without notice. [tasks/0360 §3-4, ADIAG-22/23/33/58; 0146 §4, §19; 0172 §11]

**AXD-003 — Tests assert identity.** ui tests assert code, line and severity (inline `//~ ERROR CODE`
/ `//~ WARN CODE`, axiom-testing). Unit tests may also assert spans and `data` keys. Text snapshots
of rendered output are supplementary and exist only in T009's renderer goldens.
[tasks/0360 §49, ADIAG-73/74]

## 2. Code format

**AXD-010 — Shape.** A code is `AX_<AREA>_<NAME>`: `<AREA>` is one of the areas in §3, `<NAME>` matches
`[A-Z][A-Z0-9]*(_[A-Z0-9]+)*`, and the whole code has at most 48 characters. Names describe the
condition (`AX_TYPE_MISMATCH`). They never use serial numbers (`AX_TYPE_0001`) or anything tied to a
source location. [0146 §4-5, §54; ADR-0011 §1]

**AXD-011 — Stability.** A code that has been registered is never renamed, never reused for another
meaning and never removed. If it becomes obsolete it stays registered and is marked deprecated in its
`.def` file, and the compiler stops emitting it. [tasks/0360 §47-48, ADIAG-24/75]

**AXD-012 — Fixed severity.** Each code has one severity, fixed at registration (§5). An error code
is always an error and a warning code is always a warning (in v0.1 no option changes this).
[tasks/0360 §27, ADIAG-42/44]

**AXD-013 — Unsupported constructs.** A construct that is valid Axiom but outside the self-host
subset of axiom0 (ROADMAP R7, `spec/SPEC-00-bootstrap.md`) gets one of two codes:
- `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` when the parser rejects it (S1 forms, SPEC-02 AXS-GRM-003);
- `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` when it parses but semantic analysis rejects it (floating
  point, `static` / `static mut`, `@at`, and the rest of the SPEC-00 list).
In both cases `data.construct` names the construct and `data.epic` names the epic that delivers it. The
suffix is always `_UNSUPPORTED_IN_BOOTSTRAP`. The spellings `AX_*_UNSUPPORTED_STAGE0` and
`AX_ADDR_UNSUPPORTED_STAGE0` used in older texts mean these codes (ADR-0011 §3).

**AXD-014 — Not-yet-implemented stages.** Until the task that delivers a construct is done, a stage
that meets a construct it cannot handle yet reports `AX_<AREA>_NOT_YET_SUPPORTED` of its own area
(seeded: `AX_NAME_NOT_YET_SUPPORTED`, `AX_DRIVER_STAGE_NOT_AVAILABLE`). It never crashes. These codes are
transient: once the delivering task is done, no test of the self-host subset may expect them.

## 3. Areas (fixed list)

**AXD-020 — The area list.** The areas are exactly the rows below, in this order. The order is the
registry order (AXD-031). Each area has one registry file `bootstrap/axiom0/src/diag/codes/<AREA>.def`,
created by T009. A code's prefix names the file it lives in. Board tasks list the area files they add codes to
in `locks:` (ADR-0005 §2, §14).

| # | Area | Registry file | Covers | Typical emitter (axiom0 layer) | Corpus namespaces mapped here |
|---|---|---|---|---|---|
| 1 | `LEX` | `codes/LEX.def` | tokens, literals, rejected spellings `::` `:=` (SPEC-01 §9) | `lex/` | ELEX, AX_LEX_ |
| 2 | `PARSE` | `codes/PARSE.def` | syntax, terminators, recovery (SPEC-02 §10) | `syntax/` | EPARSE, AX_PARSE_, EATTR (syntax part) |
| 3 | `NAME` | `codes/NAME.def` | names, scopes, imports, modules, visibility, labels, HIR lowering structure | `resolve/`, `hir/` | ERESOLVE, AX_NAME_, AX_MODULE_, AX_IMPORT_ |
| 4 | `TYPE` | `codes/TYPE.def` | type checking and inference, literals, casts, entry point, items and attributes checked semantically, unsupported-in-bootstrap | `types/` | ETYPE, AX_TYPE_, EATTR (semantic part) |
| 5 | `TRAIT` | `codes/TRAIT.def` | traits, impls, bounds, generics, coherence, monomorphization | `traits/` | ETRAIT, AX_TRAIT_, AX_GENERIC_ |
| 6 | `PAT` | `codes/PAT.def` | patterns, exhaustiveness, refutability, unreachable arms | `types/`, `own/` | AX_MATCH_ |
| 7 | `MOVE` | `codes/MOVE.def` | ownership transfer, use after move, Copy | `own/` | EOWN, AX_MOVE_, AX_COPY_ |
| 8 | `INIT` | `codes/INIT.def` | definite initialisation and assignment | `own/` | — |
| 9 | `CAP` | `codes/CAP.def` | `view` / `mut_view` capabilities, regions, stored views, slices | `own/` | ECAP, AX_VIEW_ |
| 10 | `DROP` | `codes/DROP.def` | drop rules, `impl Drop`, partial moves out of Drop types | `own/`, `mir/` | AX_DROP_ |
| 11 | `UNSAFE` | `codes/UNSAFE.def` | `unsafe` blocks/functions, raw pointers, fixed-address (`@at`) rules after T087, UB detected by the oracle | `types/`, `own/`, `interp/` | AX_UNSAFE_, AX_ADDR_ (ADR-0011 §3) |
| 12 | `CONST` | `codes/CONST.def` | constant evaluation and `const` items | `types/` via the const-eval interface, `interp/` | ECOMPTIME, AX_CONST_, AX_COMPTIME_ |
| 13 | `VERIFY` | `codes/VERIFY.def` | MIR (and later machine-IR) verifier findings, MIR text syntax | `verify/`, `mir/` | — |
| 14 | `FFI` | `codes/FFI.def` | `extern` blocks, ABI strings, FFI-safe types, `@link`, calls the oracle cannot run | `types/`, `interp/`, `abi/` | EFFI, EABI, AX_FFI_, AX_ABI_ |
| 15 | `LINK` | `codes/LINK.def` | object reading, symbol resolution, relocation, image layout | `link/`, `obj/` | ELINK, AX_LINK_ |
| 16 | `IO` | `codes/IO.def` | reading sources and writing outputs, host file system errors | `source/`, `driver/` | — |
| 17 | `DRIVER` | `codes/DRIVER.def` | command line, options, targets, stages, manifest, std root, interpreter limits | `driver/` | EBUILD, AX_BUILD_, AX_PACKAGE_, AX_TARGET_ |
| 18 | `ICE` | `codes/ICE.def` | internal compiler errors (AXD-042) | any layer through `AX_ICE(...)` | EINTERNAL, AXC_INTERNAL_ |

**AXD-021 — Namespaces of the corpus.** The corpus proposes other namespaces (0146 §54, tasks/0360 §38).
They map to the areas above as the last column shows. Three groups have no area in v0.1:
- `AX_RUNTIME_` / `AX_PANIC_` / `ERUNTIME`: program panics and traps are program outcomes (exit code,
  stderr text) defined by `spec/SPEC-03-core-semantics.md`, not compiler diagnostics (0146 §53).
- `EASYNC`, `AX_ASYNC_`, `ECONCUR`, `AX_CONC_`, `AX_ATOM_`, `EGPU`, `AX_GPU_`: the epics that need them (E11.*,
  E22.*) add an area by editing this section and §11 first (AXD-022). For E11.1 (`T400` / `SPEC-30 §6`), E11.2
  (`T405` / `SPEC-31 §7`), E11.3 (`T410` / `SPEC-32 §6`), and E11.4 (`T415` / `SPEC-33 §6`), the `CONC` area
  (`AX_CONC_*`) and `ASYNC` area (`AX_ASYNC_*`) are established for self-hosted `axiomc` (`compiler/diag/code.ax`,
  where `axiom0` is frozen post-`T087`), covering `Send`/`Share` auto-traits (`T089`), closure/spawn captures (`T401`),
  the compile-time data-race verifier (`T402`), happens-before/lock-order diagnostics (`T403`), atomic
  type/ordering/alignment/capability diagnostics (`T406`), thread/guard/channel/`@thread_local` TLS escape
  diagnostics (`T090`, `T411`–`T413`), and `async`/`await` syntax/type/recursion/FFI checks (`T416`),
  live-across-await capability/guard/`Future: Send` checks (`T417`), and `Future` state-machine polling
  diagnostics (`T088`, `T418`). For E12.3 (`T463` / `SPEC-42 §7`), the `SIMD` area (`AX_SIMD_*`) is established
  for self-hosted `axiomc` (`compiler/diag/code.ax`, `T464`), covering `Vector<T, N>` / `Mask<N>` element/lane-count
  validation, constant lane extract/insert bounds, shuffle selector validation, and bitcast size checks. For E12.5
  (`T475` / `SPEC-44 §5`), the `TARGET` area (`AX_TARGET_*`, alongside `AX_SIMD_*` in `compiler/diag/code.ax`,
  `T476`–`T478`) is established for self-hosted `axiomc`, covering unknown CPU target features
  (`AX_TARGET_UNKNOWN_FEATURE`), invalid `@target_feature` / `@multiversion` attribute placement or arguments
  (`AX_TARGET_INVALID_ATTRIBUTE`), and unguarded call-site target feature mismatches (`AX_TARGET_FEATURE_MISMATCH` /
  `AX_SIMD_TARGET_FEATURE_MISMATCH` / `AX_SIMD_TARGET_FEATURE_REQUIRED`). For E13.4 (`T516` / `SPEC-53 §4`), the `SEC`
  area (`AX_SEC_*`, alongside `AX_DRIVER_*` and `AX_CAP_*` in `compiler/diag/code.ax`, `T517`–`T519`) is established
  for self-hosted `axiomc`, covering `@forbid_unsafe` and `--safety-profile safe|sandbox` unsafe rejection
  (`AX_SEC_UNSAFE_FORBIDDEN`, `AX_SEC_CONFLICTING_SAFETY_POLICY`), `sandbox`/`comptime` ambient OS authority ban
  (`AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`), capability provenance forgery rejection (`AX_SEC_CAPABILITY_FORGERY`), and
  `@constant_time` / `Secret<T>` verification (`AX_SEC_TIMING_LEAK`, `AX_SEC_SECRET_IMPLICIT_COPY`,
  `AX_SEC_SECRET_EXPOSURE`, `AX_SEC_INVALID_CONSTANT_TIME_ATTR`). For E13.5 (`T521` / `SPEC-54 §4`), the `PANIC`
  prefix (`AX_PANIC_*`, alongside `AX_DRIVER_*`, `AX_TYPE_*`, and `AX_FFI_*` in `compiler/diag/code.ax`, `T522`) is
  established for self-hosted `axiomc`, covering `@no_panic` call-graph and checked-operation verification
  (`AX_PANIC_FORBIDDEN_IN_NO_PANIC`). For E14.1 (`T550` / `SPEC-60 §5`), the `CTM` prefix (`AX_CTM_*`, alongside
  `AX_CONST_*` in `compiler/diag/code.ax`, `T551`–`T552`) is established for self-hosted `axiomc`, covering
  `comptime fn` runtime call rejection (`AX_CTM_RUNTIME_CALL_FORBIDDEN`, `AX_CTM_NON_CONST_CAPTURE`), sandboxed
  comptime capability verification (`AX_CTM_CAPABILITY_DENIED`), comptime-to-runtime resource no-escape
  (`AX_CTM_ESCAPE` / `AX_CTM_RESOURCE_ESCAPE`), cycle/budget/panic diagnostics (`AX_CTM_CYCLE`, `AX_CTM_STEP_LIMIT`,
  `AX_CTM_MEM_LIMIT`, `AX_CTM_PANIC`), and constant static initialization / static move enforcement
  (`AX_CTM_NON_CONST_STATIC_INIT`, `AX_CTM_STATIC_MOVE_FORBIDDEN`). For E14.2 (`T556` / `SPEC-61 §4`), the `REFLECT`
  (`AX_REFLECT_*`) and `DERIVE` (`AX_DERIVE_*`) prefixes (alongside `AX_TRAIT_UNKNOWN_DERIVE` in `compiler/diag/code.ax`,
  `T557`–`T558`) are established for self-hosted `axiomc`, covering private cross-module reflection rejection
  (`AX_REFLECT_PRIVATE_FIELD`), unspecified layout offset queries (`AX_REFLECT_UNSPECIFIED_LAYOUT`), opt-in runtime
  reflection enforcement (`AX_REFLECT_RUNTIME_NOT_ENABLED`), unsatisfied derived field/variant bounds with provenance
  (`AX_DERIVE_FIELD_BOUND`), duplicate or conflicting derived impls (`AX_DERIVE_CONFLICT`), derive/generation cycles
  (`AX_DERIVE_CYCLE`), and unsupported derive targets (`AX_DERIVE_UNSUPPORTED_ITEM`). For E14.3 (`T561` / `SPEC-62 §4`),
  the `GEN` prefix (`AX_GEN_*`, alongside `AX_PARSE_RESERVED_KEYWORD` and `AX_CAP_*` in `compiler/diag/code.ax`, `T562`–`T563`)
  is established for self-hosted `axiomc`, covering `yield` outside a generator context (`AX_GEN_YIELD_OUTSIDE_GEN`),
  self-referential borrows of generator locals across `yield` (`AX_GEN_SELF_BORROW_ACROSS_YIELD`), ephemeral or escaping
  capabilities across `yield` (`AX_GEN_VIEW_ACROSS_YIELD`), value-bearing `return <expr>` inside `gen fn`
  (`AX_GEN_RETURN_VALUE`), unboxed recursive generator state machines (`AX_GEN_RECURSIVE`), and generator suspension
  inside `@gpu` kernels (`AX_GEN_GPU_FORBIDDEN`). For E14.4 (`T566` / `SPEC-63 §4`), the `DYN` prefix (`AX_DYN_*`,
  alongside `AX_TRAIT_*` and `AX_CAP_*` in `compiler/diag/code.ax`, `T058`) is established for self-hosted `axiomc`,
  covering `dyn Trait` object-safety verification (`AX_DYN_NOT_OBJECT_SAFE`). For E18.1 (`T752` / `SPEC-21 §5`), the
  `QUERY` prefix (`AX_QUERY_CYCLE`, `AX_QUERY_DEPTH_LIMIT`, alongside `AX_TYPE_CYCLE`, `AX_TRAIT_CYCLE`, and `AX_CTM_CYCLE`
  in `compiler/diag/code.ax`, `T754`) is established for self-hosted `axiomc`, covering active-stack query cycle
  detection with canonical `SemanticKey` rotation (`AXS-QRY-021..022`) and depth-limited query evaluation. For E18.2
  (`T756` / `SPEC-22 §4`), incremental cache misses, version/schema changes, and corrupt `.axcache` files recover
  transparently via clean recomputation without user diagnostics (`AXS-INC-022`, `AXS-INC-050`), while warm incremental
  builds replay cached diagnostics in exact `AXD-060` order (`AXS-INC-024`). For E18.3 (`T760` / `SPEC-23 §4`),
  parallel compilation across `--jobs <N>` worker threads (`T761`–`T762`) detects cross-worker cycles on `WaitForGraph`
  using the canonical `SPEC-21` cycle codes (`AX_QUERY_CYCLE`, `AX_TYPE_CYCLE`, `AX_CTM_CYCLE`, `AX_TRAIT_CYCLE`,
  `AX_QUERY_DEPTH_LIMIT`; `AXS-PAR-011`, `AXS-PAR-050`) and merges per-worker diagnostic buffers in exact `AXD-060`
  order (`AXS-PAR-023`). For E18.4 (`T764` / `SPEC-24 §4`), `.axmi` module interface and `.axmeta`/`.axlto` container
  validation (`T765`–`T766`) uses the `LINK` area codes `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, and
  `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`AXS-ART-050`). For E18.5 (`T768` / `SPEC-25 §4`), unproven optimization
  obligations (`Certainty.Possible` or `Certainty.Unknown`) roll back cleanly with zero user diagnostics (`AXS-PCT-010`,
  `AXS-PCT-050`), while a committed pass contract or translation validation failure under `--verify-pass-contracts` or
  `--validate-translations` (`T769`–`T770`) reports `AX_ICE_MIR_VERIFY` or `AX_ICE_INTERNAL` (`data.stage = "pass_contract"`
  or `"translation_val"`, `AXD-042`). For E18.6 (`T774` / `SPEC-27 §4`), separate compilation and `LinkIR` multi-object/archive linking (`T067`, `T775`) enrich `AX_LINK_UNDEFINED_SYMBOL` and `AX_LINK_DUPLICATE_SYMBOL` with demangled Axiom paths (`data.demangled`) and `.axmeta` source spans (`AXS-LNK-014`), and add `AX_LINK_ABI_MISMATCH` in the `LINK` area for cross-object calling-convention or `.axmeta` `AbiFingerprint` mismatches (`AXS-LNK-005`, `AXS-LNK-050`). For E16.9 (`T650` / `SPEC-80 §6`), `--target x86_64-linux` ELF64 object/archive/static-executable linking (`T066`, `T651`) reuses the `DRIVER` and `LINK` area codes (`AX_DRIVER_UNKNOWN_TARGET`, `AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_RELOC_OUT_OF_RANGE`, `AX_LINK_AT_OVERLAP`; `AXS-ELFS-050`). For E16.5 (`T669` / `SPEC-85 §5`), serial-numbered corpus namespaces `AX_ANDROID_0001` (`0198 §24`) and `AX_JNI_0001..0010` (`0200 §49`) map per `AXD-010` to `DRIVER`, `TARGET`, `LINK`, `FFI`, `TYPE`, `CONC`, and `CAP` diagnostics (`AX_DRIVER_INVALID_ANDROID_API`, `AX_TARGET_API_LEVEL_TOO_LOW`, `AX_LINK_ANDROID_PRIVATE_LIB`, `AX_FFI_INVALID_JNI_EXPORT`, `AX_FFI_JNI_LOCAL_ESCAPE`, alongside `AX_TYPE_STORED_VIEW_ESCAPE`, `AX_CONC_NOT_SEND`, `AX_CONC_NOT_SHARE`, `AX_CAP_OUTLIVES_OWNER`, `AX_CAP_CONFLICT_MUT`, `AX_CAP_CONFLICT_READ`, and `AX_FFI_CAPTURING_CLOSURE_CALLBACK`; `T670`–`T671`) while dynamic JVM failure states (`AX_JNI_0001, 0004, 0007..0008`) are typed runtime `std.ffi.jni.JniError` / `JException` outcomes (`AXS-JNI-011`, `AXS-JNI-017`). For E16.6 (`T673` / `SPEC-86 §5`), `wasm32-freestanding` and `wasm32-wasi` target feature, FFI import/export attribute, pre-emission `verify_wasm` bytecode validator, and `.wasm` object/static-linker diagnostics map per `AXD-010` to `FFI`, `VERIFY`, `TARGET`, `DRIVER`, `NAME`, `SEC`, `CAP`, `CONC`, `UNSAFE`, `LINK`, and `ICE` (`AX_FFI_INVALID_WASM_ATTR`, `AX_VERIFY_WASM_ILLEGAL`, alongside `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_FEATURE_MISMATCH`, `AX_TARGET_UNSUPPORTED_OP`, `AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_DUPLICATE_EXPORT`, and `AX_ICE_INTERNAL`; `T674`–`T675`). For E16.7 (`T677` / `SPEC-87 §5`), `riscv64-linux` modular `RV64GC` target feature validation, flagless Machine IR `verify_mc` checks, and `EM_RISCV = 243` ELF64 object/archive/`PIE`/shared-library linking reuse the canonical `DRIVER`, `TARGET`, `VERIFY`, `LINK`, and `ICE` diagnostics (`AX_DRIVER_UNKNOWN_TARGET`, `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_FEATURE_MISMATCH`, `AX_TARGET_UNSUPPORTED_OP`, `AX_VERIFY_MC_ILLEGAL`, `AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_RELOC_OUT_OF_RANGE`, `AX_LINK_TEXTREL_FORBIDDEN`, and `AX_ICE_INTERNAL`; `AXS-RV64-048`, `T678`–`T679`). For E16.8 (`T681` / `SPEC-88 §7`), `@cfg(...)` conditional compilation predicate validation, hermetic `--sysroot` / `--target-sdk` cross-linking, and 3-level OS platform boundary checks add `AX_NAME_INVALID_CFG_PREDICATE` (`NAME` area) and `AX_DRIVER_SYSROOT_NOT_FOUND` (`DRIVER` area) while reusing `AX_DRIVER_UNKNOWN_TARGET`, `AX_NAME_UNRESOLVED_IMPORT`, `AX_NAME_UNRESOLVED`, `AX_NAME_DUPLICATE`, `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT`, `AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `AX_TARGET_UNSUPPORTED_OP`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_UNSAFE_REQUIRED`, `AX_CAP_OUTLIVES_OWNER`, `AX_SEC_CAPABILITY_FORGERY`, and `AX_CTM_CAPABILITY_DENIED` (`AXS-XCMP-020`, `AXS-PLAT-022`, `T682`–`T683`). For E16.10 (`T685` / `SPEC-89 §5`), task-card shorthand codes `E8900–E8919` for the cross-target artifact & library matrix (`T686`–`T688`) map per `AXD-010` to the `DRIVER`, `FFI`, and `LINK` areas, adding `AX_LINK_THIN_ARCHIVE_UNSUPPORTED`, `AX_LINK_UNMATCHED_WHOLE_ARCHIVE`, `AX_LINK_AXLIB_PACKAGE_CONFLICT`, `AX_LINK_INVALID_DEF_FILE`, `AX_LINK_INVALID_VERSION_SCRIPT`, `AX_LINK_INVALID_DYLIB_VERSION`, and `AX_LINK_WASM_ENTRY_CONFLICT` in `LINK` while reusing `AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_DRIVER_USAGE`, `AX_DRIVER_UNKNOWN_OPTION`, `AX_FFI_GENERIC_EXPORT`, `AX_FFI_BAD_TYPE`, `AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_DUPLICATE_EXPORT`, `AX_LINK_ABI_MISMATCH`, and `AX_LINK_TEXTREL_FORBIDDEN` (`AXS-ARTM-002`, `AXS-ARTM-032`). For E16.11 (`T689` / `SPEC-90 §5`), task-card shorthand codes `E9000–E9014` for `x86_64-macos` Mach-O slices, Mach-O Universal 2 (`FAT_MAGIC` / `FAT_MAGIC_64`) artifact composition, and native `lipo`-free slice inspection/extraction (`T690`–`T692`) map per `AXD-010` to the `DRIVER` and `LINK` areas, adding `AX_DRIVER_INVALID_UNIVERSAL_TARGETS` and `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE` in `DRIVER` and `AX_LINK_DUPLICATE_FAT_ARCH`, `AX_LINK_FAT_SLICE_KIND_MISMATCH`, `AX_LINK_UNALIGNED_FAT_SLICE`, `AX_LINK_BAD_UNIVERSAL`, `AX_LINK_BAD_CODESIGN`, and `AX_LINK_FAT_ARCH_NOT_FOUND` in `LINK` while reusing `AX_DRIVER_UNKNOWN_TARGET`, `AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_DRIVER_USAGE`, `AX_LINK_INVALID_DYLIB_VERSION`, `AX_LINK_IMAGE_TOO_LARGE`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_RELOC_OUT_OF_RANGE`, `AX_LINK_TEXTREL_FORBIDDEN`, `AX_LINK_BAD_OBJECT`, and `AX_LINK_BAD_ARCHIVE` (`AXS-UNIV-032`). For E16.12 (`T693` / `SPEC-91 §5`), task-card shorthand codes `E9100–E9119` for `aarch64-windows` (`aarch64-pc-windows-msvc`) `CallConv.WinArm64` ABI, `X18` TEB reservation, `__chkstk` (`X15`) stack probing, COFF `0xAA64` relocations, `.pdata`/`.xdata` SEH unwind metadata, and PE32+ ARM64 `.exe`/`.dll` linking (`T694`–`T696`) map per `AXD-010` to the `DRIVER`, `TARGET`, `FFI`, `VERIFY`, `LINK`, and `ICE` areas, adding `AX_LINK_BAD_UNWIND_INFO` in `LINK` while reusing `AX_DRIVER_UNKNOWN_TARGET`, `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_FEATURE_MISMATCH`, `AX_FFI_UNKNOWN_ABI`, `AX_FFI_BAD_TYPE`, `AX_FFI_VARIADIC_NOT_EXTERN_C`, `AX_VERIFY_MC_ILLEGAL`, `AX_TARGET_UNSUPPORTED_OP`, `AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_BAD_OBJECT`, `AX_LINK_BAD_ARCHIVE`, `AX_LINK_RELOC_OUT_OF_RANGE`, `AX_LINK_TEXTREL_FORBIDDEN`, `AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_LIBRARY_NOT_FOUND`, `AX_LINK_DUPLICATE_EXPORT`, `AX_LINK_INVALID_DEF_FILE`, `AX_LINK_IMAGE_TOO_LARGE`, and `AX_ICE_INTERNAL` (`AXS-WA64-033`). For E19.1 (`T800` / `SPEC-100 §7`), `axiomc lsp` (`T801`–`T802`) introduces no separate IDE diagnostic area: `textDocument/publishDiagnostics` streams the exact `CompilerDB` `AX_<AREA>_<NAME>` diagnostics in `AXD-060` order (`AXS-LSP-004`, `AXS-LSP-060`), while serial-numbered corpus examples `AX_METHOD_0001`, `AX_VIEW_0001..0007`, `AX_MOVE_0003`, `AX_TRAIT_0012` (`tasks/0450 §153`), and `ATYPE-204` / `ACAP-204` (`0146 §4`) map per `AXD-010` to the existing canonical `AX_TRAIT_AMBIGUOUS_METHOD`, `AX_CAP_OUTLIVES_OWNER`, `AX_CAP_CONFLICT_MUT`, `AX_MOVE_USED_AFTER_MOVE`, `AX_DYN_NOT_OBJECT_SAFE`, and `AX_TYPE_MISMATCH` codes (`AXS-LSP-060`). For E19.2 (`T804` / `SPEC-101 §6`), `axiomc fmt` (`T805`–`T806`) introduces no separate formatter diagnostic area: syntax errors in input files emit the shared `LEX` (`AX_LEX_*`) and `PARSE` (`AX_PARSE_*`) diagnostics and refuse to format with exit code `1` (`AXS-FMT-030`, `AXS-FMT-050`), file I/O failures emit `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` (exit code `1`), invalid CLI combinations (`--stdin` with file paths) or unknown `[format]` keys in `axiom.toml` emit `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`), and any failure of the post-format AST-equivalence or comment-conservation verification gate (`AXS-FMT-031`) aborts before touching the file and emits `AX_ICE_INTERNAL` (`data.stage = "fmt_verify"`, exit code `3`). For E19.3 (`T808` / `SPEC-102 §7`), `compiler/refactor/*` and `std/vcs` (`T809`–`T810`) introduce no separate refactoring or VCS diagnostic area: post-refactoring, post-merge, and post-patch verification gates (`AXS-REF-002`, `AXS-REF-042`, `AXS-REF-051`, `AXS-REF-063`; `REQ-TOOL-186`) reuse the canonical `CompilerDB` `PARSE`, `NAME`, `TYPE`, `TRAIT`, `PAT`, `MOVE`, `INIT`, `CAP`, `DROP`, and `UNSAFE` diagnostics, CLI usage errors in `axiomc refactor|diff|merge|patch` emit `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`), file/repo I/O failures emit `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` (exit code `1`), and internal refactoring/VCS invariant failures emit `AX_ICE_INTERNAL` (`data.stage = "refactor_verify"` or `"vcs_verify"`, exit code `3`). For E19.4 (`T812` / `SPEC-103 §7`), Diagnostics UX 2.0 (`compiler/diag/ux2`), `axiomc explain <AX_CODE>` (`compiler/diag/explain`), `axiomc fix`, `axiomc inspect layout`, and `axiomc query` (`compiler/ai_query`, `T813`–`T814`) introduce no separate diagnostic area: they enrich existing `AX_<AREA>_<NAME>` diagnostics with `CausalProvenanceChain` steps (`Origin`, `Transfer`, `BorrowShared`, `BorrowMut`, `AliasOverlap`, `ContainerMutation`, `SuspensionPoint`, `ScopeExit`, `ObligationOrigin`, `Violation`), 128-bit `DiagnosticFingerprint`s (`0146 §40`), and `PoisonTaint` cascade suppression (`AXS-DIAG-001..005`; `REQ-TOOL-298`), map corpus shorthand codes `E_USE_AFTER_MOVE`/`EOWN_MOVED`/`AX_MOVE_0003`, `E_CAPABILITY_CONFLICT`/`ECAP_CONFLICT`/`AX_VIEW_0002`, `E_CAPABILITY_LIFETIME`/`AX_VIEW_0001`, `E_TRAIT_AMBIGUOUS`/`AX_METHOD_0001`, `E_NONEXHAUSTIVE_MATCH`, and `E_CONSTANT_TIME_VIOLATION` (`tasks/0374`, `tasks/0421`) to the existing canonical `AX_MOVE_USE_AFTER_MOVE`, `AX_CAP_CONFLICT_MUT`/`AX_CAP_CONFLICT_READ`, `AX_CAP_OUTLIVES_OWNER`/`AX_TYPE_STORED_VIEW_ESCAPE`, `AX_TRAIT_AMBIGUOUS_METHOD`, `AX_PAT_NONEXHAUSTIVE`, and `AX_SEC_TIMING_LEAK` codes (`AXS-DIAG-050`), emit `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`) on invalid `explain`/`fix`/`query`/`inspect layout` invocations, and emit `AX_ICE_INTERNAL` (`data.stage = "fix_verify"`, exit code `3`) if an internal `axiomc fix` verification invariant fails. For E19.5 (`T816` / `SPEC-104 §7`), `axiomc doc` (`compiler/docgen`, `compiler/driver/doc_cmd`; `T817`) and `axiomc test` (`compiler/test_runner`, `compiler/opt/bisect`, `compiler/driver/test_cmd`; `T818`) introduce no separate docgen or test-framework diagnostic area: broken intra-doc `[module.Item]` links emit `AX_NAME_UNRESOLVED` (`data.context = "doc_link"`, warning by default or error under `--deny-broken-links`; `AXS-DOC-004`, `AXS-DOC-050`), compile-time diagnostics in `test "..."`, `@test fn`, and `axiomc doc --test` blocks emit the exact `CompilerDB` `AX_<AREA>_<NAME>` codes with root-cause `PoisonTaint` cascade suppression (`REQ-TOOL-298`), invalid CLI flag combinations (`--opt-bisect` without a failing test filter, negative `--opt-bisect-limit`, invalid `--seed`, or corrupt `--opt-replay` bundle headers) emit `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (exit code `2`), file I/O errors emit `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED` (exit code `1`), and any internal MIR/OptIR/LIR/MachineIR verifier failure during `--opt-bisect` or `--opt-replay` emits `AX_ICE_MIR_VERIFY` or `AX_ICE_INTERNAL` (`data.stage = "opt_bisect"` or `"opt_replay"`, exit code `3`; `AXS-TST-021..022`, `AXS-TST-050`). For E20.1 (`T850` / `SPEC-110 §5`), declarative `axiom.toml` package/workspace manifest loading (`compiler/build/manifest`, `compiler/build/workspace`; `T851`) and `CompilerDB` `BuildGraph`, 4-tier build cache, and workspace driver CLI orchestration (`compiler/build/graph`, `compiler/build/cache`, `compiler/driver/workspace_cmd`; `T852`) introduce no separate build diagnostic area: serial-numbered corpus codes `AXPKG_0001..0005` and `AXBUILD_0001..0004` (`0168 §38`, `tasks/0356`, `tasks/0372`, `tasks/0411`, `tasks/0661`) map per `AXD-010` to `AX_DRIVER_BAD_MANIFEST` (`data.kind = "syntax" | "schema" | "semver" | "forbidden_script" | "workspace_member" | "package_cycle" | "unknown_feature" | "feature_conflict" | "missing_required_feature"`), `AX_NAME_INVALID_CFG_PREDICATE` (for invalid `[target.'cfg(...)'.dependencies]` predicates), `AX_DRIVER_INVALID_PROFILE`, `AX_DRIVER_UNKNOWN_TARGET`, `AX_DRIVER_INVALID_ARTIFACT_KIND`, `AX_LINK_ARTIFACT_TARGET_MISMATCH` (for `Host` vs `Target` artifact mixing), and `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (`AXS-BLD-050`). For E20.2 (`T854` / `SPEC-111 §5`), `AXPACKAGE` SemVer 2.0 constraint resolution, monotonic feature unification, and side-by-side major-version isolation (`compiler/pkg/semver`, `compiler/pkg/resolver`; `T855`) and `axiom.lock` v1 serialization/verification, `SHA-256` content-addressed package store, offline `vendor/`, and `axiomc pkg` CLI (`std/pkg/lockfile`, `std/pkg/store`, `compiler/driver/pkg_cmd`; `T856`) introduce no separate package diagnostic area: corpus/task shorthand codes (`AXPKG_SEMVER`, `AXPKG_CONFLICT`, `AXPKG_FEATURE`, `AXPKG_CYCLE`, `AXPKG_NATIVE_LINKS`, `AXPKG_TYPE_VERSION_MISMATCH`, `AXPKG_LOCK_DRIFT`, `AXPKG_LOCK_CORRUPT`, `AXPKG_HASH_MISMATCH`, `AXPKG_UNPINNED_VCS`, `PACKAGE_NOT_CACHED` / `AXPKG_OFFLINE_MISSING`, `AXPKG_PATH_TRAVERSAL`; `0098`, `tasks/0412`, `tasks/0446`, `tasks/0661`, `tasks/1065`) map per `AXD-010` to `AX_DRIVER_BAD_MANIFEST` (`data.kind = "semver" | "version_conflict" | "unknown_feature" | "feature_conflict" | "missing_required_feature" | "package_cycle" | "duplicate_native_links" | "lockfile_drift" | "lockfile_corrupt" | "hash_mismatch" | "unpinned_vcs" | "offline_missing_package" | "path_traversal" | "archive_quota_exceeded"`), `AX_TYPE_MISMATCH` (`data.reason = "distinct_package_versions"` when values/traits from side-by-side `pkg@v1` and `pkg@v2` are mixed without a shared `pub use` re-export bridge), `AX_LINK_AXLIB_PACKAGE_CONFLICT`, `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED`, and `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (`AXS-PKG-050`). For E20.3 (`T858` / `SPEC-112 §5`), deterministic `.axpkg` archive packing/unpacking, binary SHA-256 Merkle verification, sparse registry index (`AXPACKAGE_PROTOCOL_1`), local mirrors, and transactional `.axupdate-journal` generation rollback (`std/pkg/archive`, `std/pkg/registry`; `T859`) and multi-repository priority vs trust routing with `pinned_namespaces` dependency-confusion defense, precompiled `.axmeta`/`.axmi` + binary package consumption, and `axiomc pkg pack|publish|fetch|verify|search|mirror|install|rollback` CLI (`compiler/pkg/distribution`, `compiler/driver/registry_cmd`; `T860`) introduce no separate registry diagnostic area: corpus/task shorthand codes (`AXPKG_MERKLE_MISMATCH`, `AXPKG_IMMUTABLE_VERSION`, `AXPKG_UNPUBLISHABLE_DEP`, `AXPKG_COORD_MISMATCH`, `AXPKG_NAMESPACE_SHADOW` / `E_DEP_CONFUSION`, `AXPKG_QUARANTINED`, `AXPKG_POLICY_BLOCKED`, `AXPKG_ROLLBACK_FAILED`, `AXPKG_BAD_CONTAINER`, `AXPKG_SCHEMA_INCOMPATIBLE`, `AXPKG_TARGET_INCOMPATIBLE`, `AXPKG_ABI_INCOMPATIBLE`, `AXPKG_DIAMOND_CONFLICT`; `tasks/0412`, `tasks/0665`, `tasks/0739`, `tasks/0858`, `tasks/1065`) map per `AXD-010` to `AX_DRIVER_BAD_MANIFEST` (`data.kind = "merkle_mismatch" | "hash_mismatch" | "immutable_version_exists" | "unpublishable_dependency" | "manifest_coordinate_mismatch" | "namespace_shadow_blocked" | "conflicting_namespace_pin" | "quarantined_package" | "policy_blocked_version" | "rollback_unavailable" | "path_traversal" | "duplicate_archive_entry" | "archive_quota_exceeded"`), `AX_LINK_BAD_ARTIFACT`, `AX_LINK_ARTIFACT_SCHEMA_MISMATCH`, `AX_LINK_ARTIFACT_TARGET_MISMATCH`, `AX_LINK_ABI_MISMATCH`, `AX_LINK_AXLIB_PACKAGE_CONFLICT`, `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED`, and `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (`AXS-REG-050`). For E20.4 (`T862` / `SPEC-113 §5`), hermetic `BuildSandbox` isolation, canonical `--remap-path-prefix` path normalization, and 2-run differential `--verify-repro` reproducibility verification (`compiler/build/sandbox`, `compiler/build/repro`; `T863`) and `[capabilities]`/`[trust.policy]` transitive capability auditing (`REQ-PKG-024`), Ed25519 package/toolchain signing, `.axprov.json` provenance attestation, `ArtifactLog` transparency verification, Diverse Double-Compilation (`DDC`) bootstrap verification, and `axiomc verify-repro|trust|audit|provenance` CLI (`std/pkg/trust`, `compiler/driver/trust_cmd`; `T864`) introduce no separate sandbox or trust diagnostic area: corpus/task shorthand rules (`ABUILD-01..26` in `tasks/0590`, `tasks/0449 §190.1..6`, `tasks/0772 §550.1..90`) map per `AXD-010` to `AX_DRIVER_BAD_MANIFEST` (`data.kind = "undeclared_package_capability" | "capability_escalation_denied" | "undeclared_build_output" | "sandbox_fs_violation" | "sandbox_net_violation" | "sandbox_env_violation" | "sandbox_clock_or_rng_violation" | "sandbox_process_violation" | "repro_host_path_leak" | "repro_mismatch" | "signature_invalid" | "unsigned_package_rejected" | "untrusted_signer" | "revoked_signing_key" | "sdk_integrity_mismatch" | "provenance_mismatch" | "ddc_mismatch"`), alongside `AX_SEC_UNSAFE_FORBIDDEN`, `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`, `AX_CTM_CAPABILITY_DENIED`, `AX_LINK_BAD_ARTIFACT`, `AX_IO_FILE_NOT_FOUND` / `AX_IO_READ_FAILED` / `AX_IO_WRITE_FAILED`, and `AX_DRIVER_USAGE` / `AX_DRIVER_UNKNOWN_OPTION` (`AXS-HERM-050`).
- `W…` warning codes of tasks/0360 §28 (`WUNUSED_VARIABLE` …): warnings use the same `AX_<AREA>_`
  shape and the area of the rule they report.

**AXD-022 — New areas.** An area is added only by an edit of this table (by an architect task), and
then by a task that creates the new `.def` file and its include line in `diag/codes.def`, with `codes.def`
in its `locks:`. No other task edits `codes.def` (ADR-0005 §2).

## 4. Registry

**AXD-030 — Registry entry.** Each `.def` file is an X-macro list. An entry holds at least the code,
its severity and a one-line summary, which is the default message key:
`AX_DIAG(AX_LEX_INVALID_UTF8, ERROR, "invalid UTF-8 byte sequence")`. T009 fixes the exact macro and may
add columns (deprecated flag, exit class). Using an unregistered code is a C compile error (T009). A
code `AX_<AREA>_*` is defined only in `codes/<AREA>.def` (archcheck rule, T006; INV-LAYER-007).

**AXD-031 — Registry order.** `codes.def` includes the area files in the order of §3. Inside an area
file, entries appear in the order of the seed tables in §10, and new codes are **appended** at the end.
The registry ordinal of a code (area index, then position) is used only to break ordering ties
(AXD-060). Because of this rule, the LEX order equals the table of SPEC-01 AXS-LEX-100, as AXS-LEX-101 requires.

**AXD-032 — Seeding and later codes.** T009 registers **every** code of §10 (so T010–T029 use seeded
codes without editing a registry file). A later task that needs a new code:
1. picks a name by AXD-010 in the right area (or a name already fixed in §11);
2. appends it to `codes/<AREA>.def`, which must be in its `locks:`;
3. documents the condition, the rule it enforces and an example in the canonical spec that owns the
   rule (SPEC-03 for TYPE rules, SPEC-10/11/12 for MOVE/INIT/CAP/DROP, …), and adds a ui test.
This file is not a shared hot file: the architect copies new codes into §10/§11 at each phase-gate
review (core gates T022, T029, T044, T052, T062, T075, T087).

## 5. Severity policy

**AXD-040 — Severities.** The schema has four severities: `error`, `warning`, `info`, `hint`
(tasks/0360 §2, 0146 §3). axiom0 emits only `error` and `warning`. `info` and `hint` are reserved
for tooling (LSP, E19.1; `SPEC-100` `AXS-LSP-051`, `AXS-LSP-060`). `note` and `help` are not severities: they are text attached to a
diagnostic (§6). There is no `fatal` severity.

**AXD-041 — Effect of severity.**
- `error`: the compilation produces no artifact. The written output file is removed, or never written.
  The exit code is 1 (or 2 for usage errors, AXD-043).
- `warning`: no effect on artifacts or on the exit code. axiom0 has no `@allow`, no `-Werror`
  and no warning profiles: those belong to E19.4. Semantic errors can never be suppressed
  (tasks/0360 §26, ADIAG-44).
- ui tests must annotate every diagnostic they produce, warnings included ("expected codes, nothing else").

**AXD-042 — Internal compiler errors.** An ICE is a compiler bug, not a user error (tasks/0360 §23,
ADIAG-37; 0146 §50-53; tasks/0260 ABOOT-62). It is reported with an `AX_ICE_*` code and severity
`error`, through `AX_ICE(...)` (axiom-c-stage0). The driver renders the diagnostics already collected
plus the ICE, writes no artifact (ADIAG-38) and exits with code 3. `data.stage` names the pipeline stage.
`data.detail` gives the C source location (`file.c:line`) of the failed check. No stack trace is
printed by default (tasks/0360 §23). When compiler-built MIR fails the verifier, that is an ICE
(`AX_ICE_MIR_VERIFY`) with the `AX_VERIFY_*` findings attached as notes. Hand-written MIR that fails
(T018 parser, `tests/verify`) gets plain `AX_VERIFY_*` errors and exit code 1. When compiler-transformed
`OptIR` fails its post-pass structural, SSA/`MemorySSA`, effect-preservation, or MIR-reverification contract
(`spec/SPEC-70-optir-ssa-memoryssa.md`, rule `AXS-OPT-034`; `spec/SPEC-71-alias-escape-promotion.md`,
rule `AXS-ESC-016`; `spec/SPEC-72-loops-scev-bce.md`, rule `AXS-LOOP-017`; `spec/SPEC-73-inlining-specialization-devirt.md`,
rule `AXS-INL-034`; `spec/SPEC-75-lto-wpo-section-gc-pgo.md`, rule `AXS-LTO-030`; `spec/SPEC-76-performance-contract.md`, rule `AXS-PERF-003`), the compiler reports `AX_ICE_MIR_VERIFY` /
`AX_ICE_INTERNAL` (`data.stage = "optir_verify"`) and emits no artifact, whereas unproven optimization
preconditions (`Certainty.Possible` / `Certainty.Unknown`, `MayAlias` / `UnknownAlias`, `GlobalEscape` /
`UnknownEscape`, `address_observable == true`, unproven `InBounds` / `TripCount` / `NoOverflow`, `INLINE_ILLEGAL` / `UnknownTarget` / exhausted `InlineBudget` or `SpecializationBudget`, open-world `LTO` boundaries, `address_taken == true` preventing `ICF` merge, stale `PGO` `cfg_fingerprint` fallback, or `-Os`/`-Oz` size-budget profitability rejections) fail closed and leave the IR unchanged without
emitting a user error (`AXS-OPT-032`, `AXS-ESC-016`, `AXS-LOOP-001`, `AXS-BCE-002`, `AXS-INL-021`, `AXS-INL-032`, `AXS-INL-034`, `AXS-LTO-022`, `AXS-LTO-030`, `AXS-PGO-002`, `AXS-PGO-005`, `AXS-PERF-002`, `AXS-PERF-010`, `tasks/0355 ALTO-44/55..58`, `tasks/0395 AALIAS-55`, `tasks/0397 AESCAPE-65/80`, `tasks/0399 AOPT-96/97`, `tasks/0401 AINLINE-32/ADEvirt-24`, `tasks/0402 ABCE-21/ALOOP-55`, `tasks/0408 APGO-26/45`, `tasks/0551 §45`, `tasks/0581 APGO-26/44`). Likewise, when
post-RA or post-peephole Machine IR fails `x64_verify_checked` (`spec/SPEC-43-simd-backend.md`,
rule `AXS-SBE-050`; `spec/SPEC-77-regalloc-machine-opt.md`,
rules `AXS-RA-027` and `AXS-MCOPT-026`), the compiler reports `AX_ICE_INTERNAL` (`data.stage = "x64_verify"`)
and emits no artifact; profitability or legality rejections during vectorization, instruction selection, branchless
if-conversion, or peephole optimization fall back to the unoptimized sequence and never emit a user
diagnostic (`AXS-SBE-004`, `AXS-SBE-050`, `tasks/0403 ASIMD-72`, `tasks/0407 AVEC-47`, `tasks/0553 ACTRL-99`).

**AXD-043 — Exit codes** (driver, T016): 0 means no error (warnings allowed). 1 means at least one
error diagnostic. 2 means a usage error: the code is one of `AX_DRIVER_USAGE`,
`AX_DRIVER_UNKNOWN_OPTION`, `AX_DRIVER_NO_INPUT`, `AX_DRIVER_UNKNOWN_TARGET`. 3 means an ICE. For
`run`, the exit code of the program itself is defined by SPEC-03 and is used only when compilation
succeeded.

**AXD-044 — One root cause, one diagnostic.** (tasks/0360 §39-40, ADIAG-40/41/82/83)
- Recovery nodes (parser error nodes, `Error` tokens) never produce diagnostics of their own in later
  stages (ADIAG-39).
- An expression whose type is the error type, or a name that failed to resolve, is *poisoned*. Checks
  that involve a poisoned operand report nothing.
- **Stage barrier.** The pipeline runs in stage groups: {lex, parse}, {resolve, HIR lowering},
  {type check}, {ownership, initialisation, capability, drop}, {MIR build, verify}, {back end}. Once a
  group reports at least one error, later groups do not run for that compilation. Lexing and parsing
  always run together, so lexer and parser errors appear in one run (SPEC-02 R14/R15).
- The same (code, primary span) pair is never reported twice. The sink keeps the first report.

## 6. Data model

**AXD-050 — Fields.** (tasks/0360 §1; 0146 §20; 0172 §10)

| Field | Type | Rule |
|---|---|---|
| `code` | registered code | required |
| `severity` | `error` \| `warning` (\| `info` \| `hint` reserved) | the registered severity |
| `message` | one line of English | starts lower-case, no final period, entities in backticks (`` `x` ``); not API |
| `primary` | span or none | required for every code except those listed in AXD-051 |
| `labels` | list of {span, message} | secondary locations ("value moved here"); message may be empty |
| `notes` | list of text | facts ("`a` has type `i32`") |
| `helps` | list of text | advice without a machine edit (advisory suggestions, 0146 §12) |
| `fixes` | list of fix (§7) | machine-readable edits |
| `data` | map from snake_case key to string, integer, boolean or list of strings | structured facts (§10 lists the normative keys per code); may be empty |

**AXD-051 — Spans.** A span is `FileId` plus the byte range `[start, end)`, with `end ≥ start`. A
zero-width span marks an insertion point, for example a missing terminator or end of file. Line and
column numbers are derived only by renderers through the source database (ASOURCE-21, SPEC-01 §1). A diagnostic may lack a primary
span only if it has no source location: `AX_IO_*` about paths named on the command line,
`AX_DRIVER_*`, `AX_LINK_*` about object symbols, and `AX_ICE_*` raised outside any source position.

**AXD-052 — Instance identity.** The `id` of a diagnostic is its 0-based position in the sorted output
of one run. It is valid only within that run (ADIAG-45/46). axiom0 does not emit cross-diagnostic
`related` links (reserved for E19.4; `SPEC-103` `AXS-DIAG-002..003` adds `DiagnosticFingerprint` and `CausalProvenanceChain` in self-hosted `axiomc`).

## 7. Fix-it model

**AXD-055 — Fix.** A fix is `{message, applicability, edits}`. Each edit is `{span, replacement}`,
where `replacement` is UTF-8 text and may be empty for a deletion. In v0.1 all edits of one fix are in
the file of the primary span, do not overlap, and are sorted by `start`.

**AXD-056 — Applicability.** (tasks/0360 §9, ADIAG-30/32; 0146 §11-12; `SPEC-103` `AXS-DIAG-010`)
- `machine-applicable` (`Applicability.MachineApplicable`): applying the edits keeps the program's evident intent and removes the
  diagnostic. Tools may apply it without asking. Required property, tested by T009, T010, and T813: re-checking
  the source after all machine-applicable fixes are applied does not report the original diagnostics again.
- `has-placeholders` (`Applicability.HasPlaceholders`, E19.4 `SPEC-103` `AXS-DIAG-010`): the structural skeleton is valid but contains placeholders requiring completion before compiling.
- `maybe-applicable` (`Applicability.MaybeIncorrect`): the edit is probably right but changes meaning in some cases. A human or agent
  must confirm it.
- `manual-review` (`Applicability.Unspecified`): an edit is shown as an example only.
A suggestion that is only a heuristic carries no fix: it goes in `helps` (0146 §12). A fix never
suggests something the language forbids, such as `&x` or `::` (ADIAG-84/85), and never grades an `unsafe`-introducing edit as `machine-applicable` (`0146 §65 ADIAG-26`, `SPEC-103` `AXS-DIAG-011`).

**AXD-057 — The compiler never applies fixes.** `check`, `build` and `run` never modify source files
(tasks/0360 §10, ADIAG-31). Applying fixes is an explicit tooling command (`axiomc fix`, E19.4 `SPEC-103` `AXS-DIAG-013..014`, `T813`).

The fix-its required in v0.1 are those in the "Fix-it" columns of SPEC-01 AXS-LEX-100 and SPEC-02
AXS-GRM-101, all `machine-applicable` except `AX_PARSE_EXPECTED_TOKEN`, which is `maybe-applicable`.

## 8. Rendering

**AXD-060 — Order.** Before rendering, diagnostics are stably sorted by:
1. diagnostics without a primary span first, in emission order;
2. the file ordinal: the `FileId` order of the source database, which is deterministic (files named on
   the command line in argument order, then modules in module-graph order; T008, T060);
3. `primary.start`;
4. the registry ordinal of the code (AXD-031);
5. emission order.
Thread scheduling, hash order, pointer values and directory listing order never affect the result
(tasks/0360 §41, ADIAG-51/52/78/79; 0153 APAR-23). This order refines the "(file, offset, code)" order
in T009's scope: "code" means the registry ordinal, not alphabetical order.

**AXD-061 — Streams.** Diagnostics go to **stderr** in both formats. stdout is reserved for
`inspect` dumps, emitted artifacts written to `-`, and the output of a program under `run`.
Output is UTF-8 with LF line ends and is byte-exact (binary mode, axiom-c-stage0).

**AXD-062 — Human format.**

```text
error[AX_TYPE_MISMATCH]: mismatched types: expected `i32`, found `bool`
 --> src/main.ax:2:12
  |
2 |     return true
  |            ^^^^ expected `i32`
  |
  = note: the function returns `i32`
  = help: remove the value or change the return type
```

- The header is `<severity>[<code>]: <message>`.
- The location line is ` --> <path>:<line>:<col>` for the primary span. `line` is 1-based. `col` is
  1-based and counts Unicode scalar values; a tab counts as one. For a span at end of file, the
  location is the position after the last character.
- `<path>` is the path as the file was named (command line, module discovery or manifest), with `\`
  replaced by `/`. It is never made absolute by the compiler. A virtual file shows its name in angle
  brackets (`<stdin>`).
- In the snippet, a tab is displayed as 4 spaces and CR characters are not shown. The gutter width is
  the number of digits of the largest line number shown. Primary spans are underlined with `^` and
  labels with `-`. A zero-width span shows one `^` at its position.
- A span over several lines shows its first line, underlined from the start column to the end of the
  line, and its last line, underlined from the first non-blank character to the end column. A line
  `...` stands for the lines in between when there are more than two.
- Labels on other lines are shown in line order, inside the same snippet if they are in the same file.
- After the snippet come `= note: …` lines, `= help: …` lines, then one `= fix: <message>` line per fix.
- Diagnostics are separated by one blank line. The run ends with a summary line, only if at least one
  diagnostic was printed: `<E> error(s), <W> warning(s)` spelled exactly as `1 error, 0 warnings`,
  `2 errors, 1 warning`.
- No colour unless `--color=always`. Pipes, files and tests are always uncoloured.

**AXD-063 — JSON format, schema 1.** With `--json`, the driver writes **one** JSON document on a single
line to stderr, followed by `\n` (also when there are no diagnostics). Keys appear in the order shown.
Strings are escaped per RFC 8259: `"` `\` and control characters are escaped (as `\n`, `\t` or
`\u00XX`), and all other characters, including non-ASCII, are written as raw UTF-8. Integers are
decimal. The document never contains absolute paths unless the input path was absolute, and never
contains timestamps or the compiler version (determinism). Formatted for reading:

```json
{"schema":1,"tool":"axiom0","diagnostics":[
  {"id":0,"code":"AX_LEX_COLON_COLON","severity":"error",
   "message":"`::` is not an Axiom token; paths use `.`",
   "primary":{"file":"src/main.ax","start":5,"end":7,"line":1,"col":6,"end_line":1,"end_col":8},
   "labels":[],"notes":[],"helps":[],
   "fixes":[{"message":"replace `::` with `.`","applicability":"machine-applicable",
             "edits":[{"span":{"file":"src/main.ax","start":5,"end":7,"line":1,"col":6,"end_line":1,"end_col":8},
                       "replacement":"."}]}],
   "data":{}}
 ],"errors":1,"warnings":0}
```

- `tool` is `axiom0` or `axiomc`. `schema` is incremented only for an incompatible change. Adding
  optional keys is compatible (ADIAG-34/75; 0146 §57).
- `primary` is `null` when there is none (AXD-051). `end_line`/`end_col` give the position of `end`.
- A label is `{"span":…,"message":…}`. `data` values are JSON strings, integers, booleans or arrays of strings.
- `--json` changes only the rendering. The set and order of diagnostics are identical to the human format.
- The JSON is never an AST or state dump (0146 §58). Debug dumps are `inspect --emit=…`.

## 9. ui tests and the runner

The runner (T005) runs `check --json` (or `build`/`run` as the test kind needs), reads `code`,
`severity` and `primary.line` from the document, and compares them with the inline annotations. The
human format is covered only by T009 goldens (multi-line spans, tabs, CRLF, Vietnamese text). A test
that needs a `data` key or a fix asserts it in a unit test or a `*.test` exec manifest.

## 10. Seed list (P1–P4)

T009 registers every code in this section, in this order, with the stated severity (E = error,
W = warning). "Task" is the first task that emits it. Examples are minimal programs or situations;
for LEX and PARSE, SPEC-01 §9/§10 and SPEC-02 §10 are normative and are reproduced here only as an
index. The meaning column is the registry summary.

### 10.1 LEX (SPEC-01 AXS-LEX-100; all E; task T010)

| Code | Meaning | Example |
|---|---|---|
| `AX_LEX_INVALID_UTF8` | invalid UTF-8 byte sequence | a lone byte 0xFF inside a string |
| `AX_LEX_INVALID_CHAR` | character that cannot start a token | `#[x]` (SPEC-01 E12) |
| `AX_LEX_NON_ASCII_IDENT` | non-ASCII character outside literals and comments | `let tên = 1` (E14) |
| `AX_LEX_UNTERMINATED_COMMENT` | block comment open at end of file | `/* /* */` then end of file (E11) |
| `AX_LEX_UNTERMINATED_STRING` | line break or end of file inside a string | `"abc` then LF (E10) |
| `AX_LEX_UNTERMINATED_CHAR` | character literal without closing quote on the line | `'\` then end of file (E23) |
| `AX_LEX_BAD_CHAR_LITERAL` | empty or multi-character char/byte literal | `'ab'` (E06) |
| `AX_LEX_INVALID_ESCAPE` | unknown escape or bad `\x` | `"a\qb"` (E22) |
| `AX_LEX_INVALID_UNICODE_ESCAPE` | malformed or non-scalar `\u{…}` | `"\u{D800}"` (E08) |
| `AX_LEX_NON_ASCII_IN_BYTE_LITERAL` | non-ASCII character in a byte literal | `b"chào"` |
| `AX_LEX_MISSING_DIGITS` | base prefix without digits | `0x` (E03) |
| `AX_LEX_BAD_BASE_PREFIX` | upper-case base prefix | `0XFF` (fix: `0xFF`) |
| `AX_LEX_INVALID_DIGIT` | digit not valid for the base | `0b102` (E15) |
| `AX_LEX_BAD_DIGIT_SEPARATOR` | misplaced `_` in a number | `1__000` (E04) |
| `AX_LEX_INVALID_SUFFIX` | unknown or mismatched literal suffix | `2foo` (E05) |
| `AX_LEX_INT_OVERFLOW` | integer literal above 2^64 − 1 in axiom0, or above 2^128 − 1 in axiomc (`SPEC-40` AXS-INT-004, T451) | `18446744073709551616` in axiom0 (E16); `340282366920938463463374607431768211456u128` in axiomc |
| `AX_LEX_INVALID_OPERATOR` | three or more dots | `a...b` (E13) |
| `AX_LEX_COLON_COLON` | `::` is not a token; paths use `.` | `a::b` (E01, fix `.`) |
| `AX_LEX_COLON_EQ` | `:=` is not a token; bind with `=` | `x := 1` (E02, fix `=`) |

### 10.2 PARSE (SPEC-02 AXS-GRM-101; all E; tasks T011, T012)

| Code | Meaning | Example |
|---|---|---|
| `AX_PARSE_EXPECTED_TOKEN` | a specific token is required | `fn f( {}` |
| `AX_PARSE_EXPECTED_EXPR` | an expression is required | `let x = ` then LF |
| `AX_PARSE_EXPECTED_TYPE` | a type is required | `let x: = 1` |
| `AX_PARSE_EXPECTED_PATTERN` | a pattern is required | `match v { => 1 }` |
| `AX_PARSE_EXPECTED_ITEM` | an item is required | `42` at file level |
| `AX_PARSE_EXPECTED_TERMINATOR` | two statements on one line without `;` | `let a = 1 let b = 2` (R10) |
| `AX_PARSE_EXPECTED_LOOP` | label not followed by a loop | `'a: if c { }` |
| `AX_PARSE_UNCLOSED_DELIMITER` | `(`, `[` or `{` without its closer | `let x = (1 + ` then end of file (R12) |
| `AX_PARSE_LEADING_OPERATOR` | line starts with a binary/postfix operator | a line starting with `+ b` |
| `AX_PARSE_CHAINED_COMPARISON` | comparisons do not chain | `if a < b < c { }` (R06) |
| `AX_PARSE_ASSIGN_IN_EXPR` | assignment is a statement, not an expression | `if x = 5 { }` (R07) |
| `AX_PARSE_REFERENCE_OPERATOR` | prefix `&` / `&&` does not exist | `let r = &x` (R08, fix remove `&`) |
| `AX_PARSE_VAR` | `var` is not Axiom; use `let mut` | `var count = 0` (R01) |
| `AX_PARSE_IMPORT` | `import` is not Axiom; use `use` | `import std.io` (R02) |
| `AX_PARSE_MOD` | no inline modules; write `module a.b` at file top | `mod util` (R03) |
| `AX_PARSE_MODULE_NOT_FIRST` | `module` after another construct, or twice | `fn f() {}` then `module a` |
| `AX_PARSE_ITEM_IN_BLOCK` | items are not allowed inside blocks | `fn f() { fn g() {} }` (R11) |
| `AX_PARSE_LET_NEEDS_TYPE_OR_INIT` | `let` needs a type or an initialiser | `let x` |
| `AX_PARSE_SELF_NEEDS_TYPE` | `self` parameter needs a type | `fn len(self) -> usize { 0 }` (R05) |
| `AX_PARSE_FN_BODY_REQUIRED` | function body required here | `fn f() -> i32` at file level |
| `AX_PARSE_FN_BODY_NOT_ALLOWED` | body not allowed in an `extern` block | `extern "C" { fn f() { } }` |
| `AX_PARSE_VIS_NOT_ALLOWED` | visibility not allowed here | `pub let x = 1` |
| `AX_PARSE_ARRAY_TYPE_ORDER` | array types are written `[N]T` | `let xs: [i32; 4] = make()` (R04) |
| `AX_PARSE_RESERVED_KEYWORD` | reserved word `move`, `union` or `yield` | `let f = move \|x\| x` (R09) |
| `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` | construct outside the axiom0 subset (parser level) | `async fn f() {}` in axiom0 (R13); `data.construct`, `data.epic` |

### 10.3 NAME (tasks T014, T015, T015b)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_NAME_UNRESOLVED` | E | name not found in scope | `fn main() -> i32 { return y }` (no `y`) |
| `AX_NAME_DUPLICATE` | E | name defined twice in one scope | two `fn f()` items in one module; two parameters `a` |
| `AX_NAME_NOT_A_VALUE` | E | a module or type used where a value is expected | `let x = std.io` |
| `AX_NAME_NOT_A_TYPE` | E | a value or module used where a type is expected | `let x: main = 1` |
| `AX_NAME_UNRESOLVED_IMPORT` | E | `use` path does not name an existing item or module | `use std.nothing` |
| `AX_NAME_SHADOW_MODULE` | W | a local binding shadows a module name (lookup order still picks the local) | `let io = 1` while `std.io` is imported as `io` (ADR-0007) |
| `AX_NAME_UNDEFINED_LABEL` | E | `break` / `continue` names an unknown label | `loop { break 'outer }` |
| `AX_NAME_BREAK_OUTSIDE_LOOP` | E | `break` or `continue` outside a loop | `fn f() { break }` |
| `AX_NAME_NOT_YET_SUPPORTED` | E | construct parsed but not lowered by this build yet (AXD-014) | a `trait` item before T015b; `data.construct` |

### 10.4 TYPE (tasks T017, T021/T028 for the entry point, T034/T457/T458 for floats and mixed-type promotion)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_TYPE_MISMATCH` | E | expression type differs from the expected type in a binding/assignment/return/argument, or same-width signed/unsigned integer operands are mixed without a common supertype (`SPEC-03` AXS-SEM-022, `SPEC-40` AXS-INT-050..051, `SPEC-41` AXS-FLT-035) | `return true` in a function returning `i32`; `let x: f64 = n_i32`; `u32_v + i32_v`; `data.expected`, `data.found` |
| `AX_TYPE_UNKNOWN` | E | the type cannot be inferred; add an annotation | `let xs = []` |
| `AX_TYPE_NOT_CALLABLE` | E | callee is not a function | `let x = 1` then `x(2)` |
| `AX_TYPE_ARG_COUNT` | E | wrong number of arguments | `f(1, 2)` where `fn f(a: i32)`; `data.expected`, `data.found` |
| `AX_TYPE_RETURN` | E | body can reach its end without producing the declared non-unit value | `fn f(c: bool) -> i32 { if c { return 1 } }` |
| `AX_TYPE_OPERATOR` | E | operator not defined for these operand types (`SPEC-41` AXS-FLT-033) | `true + 1`; `x_f64 & 1.0`; `data.operator` |
| `AX_TYPE_LITERAL_OUT_OF_RANGE` | E | numeric literal does not fit its type (`SPEC-03` AXS-SEM-021, `SPEC-40` AXS-INT-004, `SPEC-41` AXS-FLT-003) | `let b: u8 = 300`; `let h: i128 = 170141183460469231731687303715884105728i128`; `let f: f32 = 1e40f32` |
| `AX_TYPE_NEG_UNSIGNED` | E | unary minus applied to an unsigned type | `let n: u32 = -1` |
| `AX_TYPE_INVALID_CAST` | E | `as` cast between types SPEC-03 / SPEC-40 / SPEC-41 does not allow | `true as u8 as bool` (cast to `bool`); `1.5f64 as bool` |
| `AX_TYPE_NEVER_RETURNS` | E | a function declared to return `never` can return normally | `fn fail() -> never { }` |
| `AX_TYPE_MAIN_MISSING` | E | the root file has no `fn main` (build/run) | a file containing only `fn f() {}` |
| `AX_TYPE_MAIN_SIGNATURE` | E | `main` signature not allowed by SPEC-03 | `fn main(x: i32) -> i32 { x }` |
| `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E | valid Axiom outside the axiom0 subset (AXD-013) | `let x = 1.5` (supported in `axiomc` via `SPEC-41`); `static N: i32 = 1`; `@at(0x1000) static R: u32`; `data.construct`, `data.epic` |

### 10.5 VERIFY (tasks T018, T020)

The MIR text syntax is defined by T018. These examples describe the faulty MIR in words.

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_VERIFY_MIR_SYNTAX` | E | MIR text cannot be parsed (C-only test input, T018) | a MIR file with a block header missing its `:` |
| `AX_VERIFY_UNKNOWN_LOCAL` | E | a local or block id is not declared in the body | an operand uses `_9` in a body that declares `_0`…`_3` |
| `AX_VERIFY_UNTERMINATED_BLOCK` | E | a basic block has no terminator | `bb1` ends after an assignment |
| `AX_VERIFY_BAD_TARGET` | E | a terminator targets a block that does not exist | `goto bb7` in a body with `bb0`…`bb2` |
| `AX_VERIFY_TYPE_MISMATCH` | E | operand or rvalue type differs from the place type | an `i64` constant assigned to an `i32` local |
| `AX_VERIFY_UNINIT_USE` | E | local read before it is definitely assigned | `_2` read in `bb0` before any assignment |
| `AX_VERIFY_CALL_SIGNATURE` | E | call arguments or destination do not match the callee signature | a call passing 1 argument to a 2-parameter function |
| `AX_VERIFY_RETURN_TYPE` | E | the return place type differs from the function's return type | `_0: bool` in a function returning `i32` |

### 10.6 IO (tasks T008, T016)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_IO_FILE_NOT_FOUND` | E | input file does not exist | `axiom0 check nothere.ax` |
| `AX_IO_READ_FAILED` | E | input file exists but cannot be read | a directory given as source; a locked file |
| `AX_IO_WRITE_FAILED` | E | output cannot be written | `build -o` into a missing or read-only directory |
| `AX_IO_FILE_TOO_LARGE` | E | source file exceeds the source-database limit (T008) | a source file of 5 GiB |

### 10.7 DRIVER (tasks T016, T021)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_DRIVER_USAGE` | E | malformed command line (exit 2) | `axiom0 frobnicate x.ax` |
| `AX_DRIVER_UNKNOWN_OPTION` | E | unknown option (exit 2) | `axiom0 check --fast x.ax` |
| `AX_DRIVER_NO_INPUT` | E | command needs an input file (exit 2) | `axiom0 build` |
| `AX_DRIVER_UNKNOWN_TARGET` | E | target triple not supported (exit 2) | `--target mips-linux` |
| `AX_DRIVER_STAGE_NOT_AVAILABLE` | E | the requested stage or emitter is not implemented in this build (AXD-014) | `inspect --emit=lir` before T023 |
| `AX_DRIVER_INTERP_STEP_LIMIT` | E | the MIR interpreter exceeded its step limit (SPEC-03 default, `--step-limit N`) | `loop { }` under `run --interp` |
| `AX_DRIVER_INTERP_STACK_LIMIT` | E | the MIR interpreter exceeded its call-depth limit (SPEC-03) | unbounded recursion `fn f() -> i32 { f() }` under `run --interp` |

### 10.8 LINK (task T027)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_LINK_UNDEFINED_SYMBOL` | E | a referenced symbol is defined in no input object or import | a call to `helper` whose object is not linked; `data.symbol` |
| `AX_LINK_DUPLICATE_SYMBOL` | E | a global symbol is defined twice | two objects both define `main`; `data.symbol` |
| `AX_LINK_RELOC_OUT_OF_RANGE` | E | a relocation value does not fit its field | a `REL32` target more than 2 GiB away |
| `AX_LINK_BAD_OBJECT` | E | input object file is malformed or of an unsupported kind | a truncated `.obj` fixture |
| `AX_LINK_IMAGE_TOO_LARGE` | E | image exceeds the PE32+ size limit | sections totalling more than 2 GiB |

### 10.9 ICE (all tasks through `AX_ICE(...)`; exit 3)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_ICE_INTERNAL` | E | an internal invariant failed; `data.stage`, `data.detail` | an assertion in `types/` on a HIR node kind it does not know |
| `AX_ICE_MIR_VERIFY` | E | compiler-built MIR was rejected by the verifier (AXD-042) | the MIR builder emits a block without terminator |
| `AX_ICE_OUT_OF_MEMORY` | E | the compiler could not allocate memory | arena growth fails |

### 10.10 Areas with no seed codes

`TRAIT`, `PAT`, `MOVE`, `INIT`, `CAP`, `DROP`, `UNSAFE`, `CONST`, `FFI`: T009 creates their files
empty. Their first codes are added by the tasks in §11.

## 11. Names already fixed for later tasks (not seeded)

These names are referenced by ADRs or task texts. They are fixed here so that tasks do not invent
variants. Each is appended to its area file by the task named (AXD-032).

| Code | Sev | Task | Meaning |
|---|---|---|---|
| `AX_TYPE_ASSIGN_IMMUTABLE` | E | T030/T571 | assignment to a binding not declared `mut`, or through an immutable `view` (`w.f = v`, `*v = x`, or `a[i] = v` where any traversed view level is `view`; `SPEC-03` AXS-SEM-043, AXS-SEM-047) |
| `AX_TYPE_CANNOT_INDEX` | E | T036/T571 | indexing `base[i]` where `base` is not an array `[N]T`, slice view, `Str`, `view`/`mut_view` chain resolving to `[N]T`/`[T]` in `axiomc`, or `Index` impl — including raw pointers `*const [N]T`, `*mut [N]T`, `*const T`, `*mut T` which are never auto-dereferenced for indexing (`SPEC-03` AXS-SEM-042, AXS-SEM-047; help `write (*p)[i]` inside `unsafe`) |
| `AX_PAT_NONEXHAUSTIVE` | E | T038 | `match` misses patterns (`data.missing` lists them) |
| `AX_PAT_UNREACHABLE` | W | T038 | an arm can never match |
| `AX_PAT_REFUTABLE` | E | T038b | refutable pattern where an irrefutable one is required |
| `AX_MOVE_USE_AFTER_MOVE` | E | T046 | use of a value after it was moved (label at the move) |
| `AX_UNSAFE_REQUIRED` | E | T061a/T501/T473 | raw-pointer dereference, pointer arithmetic, `MakeView`/`MakeMutView` capability creation from raw pointers, mutable `static` access, `@addr`/`@at` fixed-address access, or `unsafe fn` / `extern` / `std.arch.x86_64` non-temporal/raw-pointer intrinsic call outside `unsafe` (`SPEC-43` AXS-SBE-043, AXS-SBE-050; `SPEC-50` AXS-UNS-001..005, AXS-UNS-050) |
| `AX_UNSAFE_INTERP_UB` | E | T061a/T061c/T502 | undefined behaviour detected by the MIR interpreter oracle (`UB-01..UB-12`: null/dangling/out-of-bounds/misaligned/uninit/invalid-value/read-only-write/provenance-forgery/capability-conflict/overlapping-copy/invalid-fn-ptr/ffi-abi violation; exit code 125; `SPEC-50` AXS-UNS-015..016, AXS-UNS-050) |
| `AX_CONST_OVERFLOW` | E | T061/T451 | arithmetic overflow during constant evaluation (`SPEC-03` AXS-SEM-030, `SPEC-40` AXS-INT-005) |
| `AX_CONST_DIV_ZERO` | E | T061/T451 | division by zero during constant evaluation (`SPEC-03` AXS-SEM-032, `SPEC-40` AXS-INT-005) |
| `AX_CONST_SHIFT_RANGE` | E | T061/T451 | shift count out of range during constant evaluation (`SPEC-03` AXS-SEM-034, `SPEC-40` AXS-INT-005) |
| `AX_DRIVER_NO_STD` | E | T060 | no std root found (ADR-0006 §8) |
| `AX_FFI_NOT_IN_ORACLE` | E | T065/T503 | the interpreter reached a direct `extern` call without a host intrinsic or mock binding (ADR-0002 §4, `SPEC-50` AXS-UNS-036) |
| `AX_UNSAFE_AT_HOSTED` | E | T504/T525/T526 | `@addr` / `@at` placement on `static` or `fn` in the `hosted` profile without `--freestanding` or `--allow-fixed-addr` (ADR-0001, `SPEC-50` AXS-UNS-023, AXS-UNS-050; `SPEC-55` AXS-ADR-014, AXS-ADR-050; formerly `AX_ADDR_HOSTED`) |
| `AX_CONC_NOT_SEND` | E | T089/T401 | value of type `T: !Send` transferred across an execution context boundary (`SPEC-30` AXS-CONC-050) |
| `AX_CONC_NOT_SHARE` | E | T089/T401 | shared capability `view<T>` where `T: !Share` shared across execution contexts (`SPEC-30` AXS-CONC-050) |
| `AX_CONC_SAFE_IMPL_MARKER` | E | T089 | positive `impl Send` or `impl Share` written without `unsafe` (`SPEC-30` AXS-CONC-018) |
| `AX_CONC_CONFLICTING_MARKER_IMPL` | E | T089 | conflicting positive and negative `Send`/`Share` impls for overlapping types (`SPEC-30` AXS-CONC-017) |
| `AX_CONC_CAPTURE_NOT_SEND` | E | T401 | closure or async `Future` passed to `spawn` captures a `!Send` field (`SPEC-30` AXS-CONC-020) |
| `AX_CONC_ESCAPING_VIEW` | E | T401 | escaping closure or unscoped `spawn` captures a non-`'static` `view<T>` or `mut_view<T>` (`SPEC-30` AXS-CONC-023) |
| `AX_CONC_SPAWN_REQUIRES_MOVE` | E | T401 | unscoped `spawn` closure captures outer bindings without `move` ownership transfer (`SPEC-30` AXS-CONC-022) |
| `AX_CONC_SHARED_MUT` | E | T402/T403 | unsynchronized concurrent `READ`/`WRITE` or `WRITE`/`WRITE` on overlapping (`SAME`, `CONTAINS`, `UNKNOWN`) places (`SPEC-30` AXS-CONC-031) |
| `AX_CONC_VIEW_NOT_SHARE` | E | T402 | concurrent `READ`/`READ` via `view<T>` across execution contexts when `T: !Share` (`SPEC-30` AXS-CONC-031) |
| `AX_CONC_UNSYNC_STATIC` | E | T402 | safe code accesses unsynchronized mutable `static` or exports `@thread_local` view across threads (`SPEC-30` AXS-CONC-034) |
| `AX_CONC_GUARD_ESCAPE` | E | T402 | capability derived from `MutexGuard`/`RwLock*Guard` escapes the guard or guard is held across `.await` (`SPEC-30` AXS-CONC-035) |
| `AX_CONC_ATOMIC_MUT_VIEW` | E | T402/T406 | concurrent non-atomic `mut_view<T>` access mixed with shared `Atomic<T>` access or attempt to borrow `Atomic<T>` inner storage as `mut_view<T>` (`SPEC-30` AXS-CONC-036, `SPEC-31` AXS-ATM-005) |
| `AX_CONC_LOCK_ORDER` | W/E | T403 | inverted lock acquisition order on the same lock pair across concurrent paths (`SPEC-30` AXS-CONC-007) |
| `AX_CONC_INVALID_ATOMIC_TYPE` | E | T406 | `Atomic<T>` instantiated with a type outside the allowed 1-, 2-, 4-, or 8-byte integer, `bool`, or raw-pointer set (`SPEC-31` AXS-ATM-010, AXS-ATM-060) |
| `AX_CONC_INVALID_ATOMIC_ORDERING` | E | T406 | disallowed `Ordering` for an atomic operation or fence (`load` with `Release`/`AcqRel`, `store` with `Acquire`/`AcqRel`, `fence`/`compiler_fence` with `Relaxed`, CAS `failure` with `Release`/`AcqRel`, or CAS `failure` stronger than `success`; `SPEC-31` AXS-ATM-026, AXS-ATM-060) |
| `AX_CONC_INVALID_ATOMIC_ALIGNMENT` | E | T406 | `Atomic<T>` placed inside a `@packed` struct or given a sub-natural `@align(N)` where `N < size_of::<T>()` (`SPEC-31` AXS-ATM-011, AXS-ATM-060) |
| `AX_CONC_TLS_ESCAPE` | E | T413 | `view<T>` or `mut_view<T>` rooted at a `@thread_local static` item or `LocalKey<T>.with` callback escapes its lexical scope, is stored in a global/heap place, is captured into `spawn`, or is held across `.await` (`SPEC-32` AXS-SYNC-020..022, AXS-SYNC-050) |
| `AX_TYPE_INVALID_TLS_DECL` | E | T413 | `@thread_local` attached to a non-`static` item (`fn`, `struct`, `enum`, `const`, `type`, or local `let`), or `@thread_local static` initialized with a non-constant expression (`SPEC-32` AXS-SYNC-022, AXS-SYNC-050) |
| `AX_ASYNC_AWAIT_OUTSIDE_ASYNC` | E | T416 | `.await` expression used outside an `async fn` body or `async { ... }` block (`SPEC-33` AXS-ASY-021, AXS-ASY-051) |
| `AX_ASYNC_NOT_A_FUTURE` | E | T416 | operand `e` of `e.await` has a type `F` that does not implement `std.future.Future` (`SPEC-33` AXS-ASY-021, AXS-ASY-051) |
| `AX_ASYNC_EXTERN_ABI` | E | T416 | `async` modifier combined with `extern "<abi>" fn` (`SPEC-33` AXS-ASY-026, AXS-ASY-051) |
| `AX_ASYNC_RECURSIVE_FUTURE` | E | T416 | direct or mutual recursion among `async fn` bodies creates an unboxed infinite-size `Future` state machine (`SPEC-33` AXS-ASY-025, AXS-ASY-051) |
| `AX_ASYNC_AWAIT_IN_DROP` | E | T416 | `impl Drop` method is declared `async` or contains `.await` (`SPEC-33` AXS-ASY-021, AXS-ASY-045, AXS-ASY-051) |
| `AX_ASYNC_BLOCKING_IN_ASYNC` | W/E | T416 | operation carrying the `Blocking` effect (`Thread.sleep`, `JoinHandle.join`, synchronous socket/file I/O) invoked inside an `async` body (`SPEC-33` AXS-ASY-027, AXS-ASY-051) |
| `AX_ASYNC_VIEW_ACROSS_AWAIT` | E | T417 | `view<T>`, `mut_view<T>`, or view-containing composite is live across an `.await` suspension point (`SPEC-33` AXS-ASY-034, AXS-ASY-051) |
| `AX_ASYNC_GUARD_ACROSS_AWAIT` | E | T417 | synchronous lock guard (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`) is live across an `.await` suspension point (`SPEC-33` AXS-ASY-035, AXS-ASY-051) |
| `AX_ASYNC_FUTURE_NOT_SEND` | E | T417 | `Future` required to satisfy `Send` has a parameter or live-across-await local/sub-future whose type is `!Send` (`SPEC-33` AXS-ASY-036, AXS-ASY-051) |
| `AX_ASYNC_POLL_AFTER_COMPLETE` | E | T088/T418 | oracle or debug check detects `Future.poll` called on a state machine already in `STATE_COMPLETE` or `STATE_POISONED` (`SPEC-33` AXS-ASY-042, AXS-ASY-050, AXS-ASY-051) |
| `AX_UNSAFE_TRAIT_IMPL` | E | T501 | `impl Trait for T` written without `unsafe` when `Trait` is declared `unsafe trait` (`SPEC-50` AXS-UNS-004, AXS-UNS-050) |
| `AX_UNSAFE_UNNECESSARY_IMPL` | E | T501 | `unsafe impl Trait for T` written when `Trait` is not declared `unsafe trait` (`SPEC-50` AXS-UNS-004, AXS-UNS-050) |
| `AX_UNSAFE_MISALIGNED_AT` | E | T504/T525/T526 | `@addr(A)` / `@at(A)` has `A == 0` or `A % align_of<T>() != 0` (`SPEC-50` AXS-UNS-022..024, AXS-UNS-050; `SPEC-55` AXS-ADR-014, AXS-ADR-050; canonical alias `AX_UNSAFE_AT_MISALIGNED`) |
| `AX_UNSAFE_AT_MISALIGNED` | E | T526 | constant `@at(A)` / `@addr(A)` address `A` is not aligned to `align_of<T>()` (`SPEC-55` AXS-ADR-014, AXS-ADR-050; canonical alias of `AX_UNSAFE_MISALIGNED_AT`) |
| `AX_UNSAFE_AT_OVERLAP` | E | T526 | two constant `@at` / `@addr` items in the same module have overlapping address ranges (`ADR-0001 §3`, `SPEC-55` AXS-ADR-014, AXS-ADR-050) |
| `AX_LINK_AT_OVERLAP` | E | T528 | two pinned `@at` / `@addr` sections or symbols across linked objects overlap in VMA space (`ADR-0001 §3–4`, `SPEC-55` AXS-ADR-014, AXS-ADR-023, AXS-ADR-050) |
| `AX_UNSAFE_INVALID_AT_LAYOUT` | E | T504/T525/T526 | `@addr(A)` / `@at(A)` applied to a type with dynamically sized or non-fixed layout (`SPEC-50` AXS-UNS-023..024, AXS-UNS-050; `SPEC-55` AXS-ADR-014, AXS-ADR-050) |
| `AX_FFI_UNKNOWN_ABI` | E | T503/T694 | unknown or target-unsupported ABI string in `extern "<abi>"` or `@abi(<mode>)`, including x86-only `"win64"`, `"sysv64"`, `"stdcall"`, `"fastcall"`, or `"vectorcall"` on `aarch64-windows` (`SPEC-50` AXS-UNS-031..032, AXS-UNS-050; `SPEC-91` AXS-WA64-001, AXS-WA64-033) |
| `AX_FFI_BAD_TYPE` | E | T503/T694 | non-FFI-safe parameter or return type in an `extern "C"` / `"system"` signature (`SPEC-50` AXS-UNS-032..033, AXS-UNS-050; `SPEC-91` AXS-WA64-004..006, AXS-WA64-033) |
| `AX_FFI_INVALID_TRANSPARENT` | E | T503 | `@repr(transparent)` applied to a type that does not have exactly one non-zero-sized field (`SPEC-50` AXS-UNS-031, AXS-UNS-050) |
| `AX_FFI_OPAQUE_BY_VALUE` | E | T503 | opaque foreign type (`extern "C" { type T; }`) instantiated, passed by value, or queried with `size_of` (`SPEC-50` AXS-UNS-033, AXS-UNS-050) |
| `AX_FFI_GENERIC_EXPORT` | E | T503 | `@no_mangle` or `extern "C"` export declared with unmonomorphized type parameters (`SPEC-50` AXS-UNS-032, AXS-UNS-050) |
| `AX_FFI_CAPTURING_CLOSURE_CALLBACK` | E | T503 | closure with non-empty capture environment converted to `extern "C" fn(...)` (`SPEC-50` AXS-UNS-033, AXS-UNS-050) |
| `AX_FFI_VARIADIC_NOT_EXTERN_C` | E | T503/T694 | variadic parameter list `...` used outside an `extern "C"` import declaration (`SPEC-50` AXS-UNS-032, AXS-UNS-050; `SPEC-91` AXS-WA64-006, AXS-WA64-033) |
| `AX_TYPE_NOT_A_PLACE` | E | T504 | `address_of(e)` / `address_of_mut(e)` / `addr_of(e)` applied to a temporary rvalue rather than a place expression (`SPEC-50` AXS-UNS-021, AXS-UNS-050) |
| `AX_CAP_CONFLICT_MUT` | E | T125/T501 | `mut_view<T>` overlaps another live `view<T>` or `mut_view<T>` (`SPEC-11`, `SPEC-50` AXS-UNS-005..006, AXS-UNS-050) |
| `AX_CAP_OUTLIVES_OWNER` | E | T125/T501 | `view<T>` or `mut_view<T>` escapes or outlives its backing owner (`SPEC-11`, `SPEC-50` AXS-UNS-005..006, AXS-UNS-050) |
| `AX_CAP_CONTAINER_RELOC` | E | T125/T501 | mutating or reallocating a container (`Vec<T>`, `String`, `HashMap<K, V>`) while an element `view` / `mut_view` is live (`SPEC-11`, `SPEC-50` AXS-UNS-006, AXS-UNS-050) |
| `AX_SIMD_INVALID_ELEMENT` | E | T464 | `Vector<T, N>` instantiated with an element type `T` outside the supported `SimdElement` scalar integer/float set (`SPEC-42` AXS-SIMD-002, AXS-SIMD-060) |
| `AX_SIMD_INVALID_LANES` | E | T464 | `Vector<T, N>` or `Mask<N>` instantiated with a lane count `N` outside `{2, 4, 8, 16, 32, 64}` (`SPEC-42` AXS-SIMD-002, AXS-SIMD-060) |
| `AX_SIMD_LANE_OUT_OF_RANGE` | E | T464 | compile-time constant lane index `idx >= N` in `extract` / `insert` (`SPEC-42` AXS-SIMD-011, AXS-SIMD-060) |
| `AX_SIMD_SHUFFLE_OUT_OF_RANGE` | E | T464 | non-constant shuffle selector array or selector index `>= 2 * N` (`>= N` in single-vector `swizzle`) (`SPEC-42` AXS-SIMD-012, AXS-SIMD-060) |
| `AX_SIMD_BITCAST_SIZE_MISMATCH` | E | T464 | `bitcast` / `simd_bitcast` between vector types of different total byte sizes or involving `Mask<N>` (`SPEC-42` AXS-SIMD-025, AXS-SIMD-060) |
| `AX_TARGET_UNKNOWN_FEATURE` | E | T476/T654/T662/T666/T674/T678/T694 | unknown CPU/WASM/RISC-V feature name (or disallowed `-neon`/`-fp` on hosted AArch64 targets including `aarch64-windows`, `-sse`/`-sse2`, WASM `-mutable_globals`/`-sign_ext`/`-nontrapping_fptoint`, or hosted `riscv64-linux` `-f`/`-d`/`-a`/`-m` baseline removal) in `--target-feature`, `@target_feature("...")`, or `@multiversion("...")` (`SPEC-44` AXS-CPU-003, AXS-CPU-010, AXS-CPU-030, AXS-CPU-040; `SPEC-81` AXS-TGTD-007..008; `SPEC-83` AXS-A64-003, AXS-A64-050; `SPEC-84` AXS-MACHO-002, AXS-MACHO-033; `SPEC-86` AXS-WASM-003, AXS-WASM-031; `SPEC-87` AXS-RV64-003, AXS-RV64-048; `SPEC-91` AXS-WA64-002, AXS-WA64-033) |
| `AX_TARGET_INVALID_ATTRIBUTE` | E | T476/T478 | `@target_feature` or `@multiversion` attached to a non-function item (`struct`, `enum`, `const`, `static`, `extern`), empty `@multiversion()`, duplicate clone feature sets, or `@multiversion` combined with `@target_feature` (`SPEC-44` AXS-CPU-010, AXS-CPU-030, AXS-CPU-040) |
| `AX_TARGET_FEATURE_MISMATCH` | E | T476/T662/T666/T674/T678/T694 | calling a `@target_feature` function or target-gated intrinsic (or coercing a `@target_feature` function to `fn(...)`) from a caller lacking the required features without an enclosing `unsafe` block or dominating runtime feature-detection guard (`SPEC-44` AXS-CPU-011..012, AXS-CPU-040; `SPEC-83` AXS-A64-003, AXS-A64-050; `SPEC-84` AXS-MACHO-002, AXS-MACHO-033; `SPEC-86` AXS-WASM-003, AXS-WASM-031; `SPEC-87` AXS-RV64-003, AXS-RV64-048; `SPEC-91` AXS-WA64-002, AXS-WA64-033; synonym `AX_SIMD_TARGET_FEATURE_MISMATCH` / `AX_SIMD_TARGET_FEATURE_REQUIRED`) |
| `AX_TYPE_UNION_NON_COPY_FIELD` | E | T507 | untagged `union` field is neither `Copy` nor wrapped in `ManuallyDrop<T>` (`SPEC-51` AXS-MEM-011, AXS-MEM-050) |
| `AX_TYPE_UNION_INIT_FIELD_COUNT` | E | T507 | `union` literal initializes zero fields or more than one field (`SPEC-51` AXS-MEM-012, AXS-MEM-050) |
| `AX_TYPE_INVALID_ALIGN` | E | T507 | `@align(N)` or `@repr(packed(N))` specifies `N` that is `0`, not a power of two, or `> 2^29` (`SPEC-51` AXS-MEM-021..022, AXS-MEM-050) |
| `AX_TYPE_CONFLICTING_REPR` | E | T507 | conflicting representation attributes on the same type (`@repr(packed)` combined with `@align(N)` or `@repr(transparent)`) (`SPEC-51` AXS-MEM-022, AXS-MEM-050) |
| `AX_TYPE_UNALIGNED_PACKED_REF` | E | T507 | taking `view<T>`, `mut_view<T>`, or an aligned `*const T` / `*mut T` reference to an unaligned field of a `@repr(packed)` / `@repr(packed(N))` struct (`SPEC-51` AXS-MEM-023, AXS-MEM-050) |
| `AX_TYPE_ADDR_SPACE_MISMATCH` | E | T507 | implicit conversion or cast between pointers of different `@addr_space(N)` qualifiers, or creating a host view from a non-host address space (`SPEC-51` AXS-MEM-024, AXS-MEM-050) |
| `AX_TYPE_BITCAST_SIZE_MISMATCH` | E | T509 | `std.mem.bitcast<From, To>(v)` called when `size_of<From>() != size_of<To>()` or when either type is not bitcast-eligible (`SPEC-51` AXS-MEM-015, AXS-MEM-050) |
| `AX_TYPE_MMIO_WRITE_READONLY` | E | T508/T509 | writing to or calling `.write`/`.modify` on a read-only `MmioRO<T>` register field (`SPEC-51` AXS-MEM-005..006, AXS-MEM-050) |
| `AX_TYPE_MMIO_READ_WRITEONLY` | E | T508/T509 | reading from or calling `.read`/`.modify` on a write-only `MmioWO<T>` register field (`SPEC-51` AXS-MEM-005..006, AXS-MEM-050) |
| `AX_UNSAFE_INVALID_VOLATILE_WIDTH` | E | T508/T509 | `volatile_load`/`volatile_store`/`Volatile<T>` instantiated with `!Copy`, or `Mmio*<T>` instantiated with `size_of<T>() not in {1, 2, 4, 8}` (`SPEC-51` AXS-MEM-002, AXS-MEM-005, AXS-MEM-050) |
| `AX_DRIVER_INVALID_PROFILE` | E | T512 | unknown `--profile <name>` or `axiom.toml` `profile` value outside `{hosted, freestanding, kernel, system}` (exit code 2; `SPEC-52` AXS-FRE-002, AXS-FRE-050) |
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | E | T512/T694/T695 | reachable function in `--profile freestanding` or `--profile kernel` transitively requires a forbidden runtime capability (`os_io`, `os_env_process`, `thread`, `blocking`, `async_reactor`, `tls`, `unwind`, or `heap_alloc` without `@global_allocator`) (`SPEC-52` AXS-FRE-022, AXS-FRE-050; `SPEC-91` AXS-WA64-023, AXS-WA64-032..033) |
| `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT` | E | T512 | importing a hosted Layer-3 OS module (`std.os`, `std.io`, `std.fs`, `std.net`, `std.process`, `std.thread`, `std.env`, `std.time`) in `--profile freestanding` or `--profile kernel` (`SPEC-52` AXS-FRE-003, AXS-FRE-050) |
| `AX_TYPE_ENTRY_MISSING` | E | T512 | executable compiled in `--profile freestanding` or `--profile kernel` defines no `@entry` function (`SPEC-52` AXS-FRE-010, AXS-FRE-050) |
| `AX_TYPE_DUPLICATE_ENTRY` | E | T512 | more than one `@entry` function defined in the compilation unit (`SPEC-52` AXS-FRE-010, AXS-FRE-050) |
| `AX_TYPE_ENTRY_SIGNATURE` | E | T512 | `@entry` function is generic, `async`, or has an invalid parameter/return signature (`SPEC-52` AXS-FRE-010, AXS-FRE-050) |
| `AX_TYPE_INVALID_PANIC_HANDLER` | E | T512 | `@panic_handler` function is generic, `async`, or does not have signature `fn(view<PanicInfo>) -> never` / `fn() -> never` (`SPEC-52` AXS-FRE-011, AXS-FRE-050) |
| `AX_TYPE_DUPLICATE_PANIC_HANDLER` | E | T512 | more than one `@panic_handler` function defined in the binary (`SPEC-52` AXS-FRE-011, AXS-FRE-050) |
| `AX_TYPE_INVALID_GLOBAL_ALLOCATOR` | E | T512/T514 | `@global_allocator` attached to a non-`static` item or a type not implementing `GlobalAlloc` / `Allocator` (`SPEC-52` AXS-FRE-012, AXS-FRE-050) |
| `AX_TYPE_DUPLICATE_GLOBAL_ALLOCATOR` | E | T512/T514 | more than one `@global_allocator` item defined in the binary (`SPEC-52` AXS-FRE-012, AXS-FRE-050) |
| `AX_TYPE_INVALID_NAKED_FN` | E | T512/T513 | `@naked` function is not declared `unsafe`, is `async`, or allocates local stack frame slots (`SPEC-52` AXS-FRE-013, AXS-FRE-050) |
| `AX_TYPE_INVALID_SECTION` | E | T512/T513 | `@section("...")` or `@used` applied to a non-`fn`/non-`static` item, or `@section` given an invalid section name (`SPEC-52` AXS-FRE-014, AXS-FRE-050) |
| `AX_UNSAFE_INTERRUPT_FORBIDDEN_OP` | E | T512 | `extern "interrupt"` handler directly or transitively performs heap allocation (`heap_alloc`), blocking (`blocking`), thread creation (`thread`), `.await` (`async`), or OS I/O (`os_io`) (`REQ-ABI-102`, `SPEC-52` AXS-FRE-016, AXS-FRE-050) |
| `AX_CAP_DMA_ACTIVE_CONFLICT` | E | T513/T514 | CPU `view<T>` or `mut_view<T>` access attempted on a `DmaBuffer<T>` while an active `DmaTransfer<T>` owns the buffer (`REQ-CAP-140`, `REQ-CAP-143`, `SPEC-52` AXS-FRE-005, AXS-FRE-050) |
| `AX_DRIVER_INVALID_SAFETY_PROFILE` | E | T517 | unknown `--safety-profile <mode>` or `axiom.toml` `safety_profile` value outside `{safe, sandbox, system}` (exit code 2; `SPEC-53` AXS-SEC-002, AXS-SEC-050) |
| `AX_SEC_UNSAFE_FORBIDDEN` | E | T517 | `unsafe` block, `unsafe fn`, `unsafe trait`/`unsafe impl`, raw-pointer dereference/arithmetic, `extern` block, `static mut`, or `@addr`/`@at` used under `@forbid_unsafe` or `--safety-profile safe\|sandbox` (`SPEC-53` AXS-SEC-003, AXS-SEC-050) |
| `AX_SEC_CONFLICTING_SAFETY_POLICY` | E | T517 | `@allow_unsafe` applied inside a scope already locked by `@forbid_unsafe` or `--safety-profile safe\|sandbox`, or invalid safety policy attribute syntax (`SPEC-53` AXS-SEC-003, AXS-SEC-050) |
| `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN` | E | T517 | calling an ambient OS API (`std.fs`, `std.net`, `std.env`, `std.process`, `std.time`, `host.*`) in `--safety-profile sandbox` or `comptime` without an explicit authority capability token (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`), or bridging `comptime` and `runtime` authority (`REQ-CAP-131`, `SPEC-53` AXS-SEC-011, AXS-SEC-050) |
| `AX_SEC_CAPABILITY_FORGERY` | E | T517 | implicitly converting or casting a raw pointer (`*const T`, `*mut T`), integer address (`usize`), or WASM linear-memory offset into a safe capability (`view<T>`, `mut_view<T>`) or authority token (`FsCap`, `NetCap`, etc.) without an explicit `unsafe` precondition boundary (`REQ-CAP-010`, `REQ-CAP-123`, `REQ-FFI-124`, `SPEC-53` AXS-SEC-004, AXS-SEC-050) |
| `AX_SEC_TIMING_LEAK` | E | T518 | secret-dependent branch (`if`/`match`/`while`/`&&`/`||`), secret-dependent memory/array indexing (`arr[secret]`), variable-latency instruction (`/` `DIV`/`IDIV`, `%` `REM`), or non-`@constant_time` call on `@secret` / `Secret<T>` data inside a `@constant_time` function (`SPEC-53` AXS-SEC-023, AXS-SEC-050) |
| `AX_SEC_SECRET_IMPLICIT_COPY` | E | T518/T519 | attempting to implicitly `Copy` a `Secret<T>` value instead of moving or calling `clone_secret()` (`SPEC-53` AXS-SEC-020, AXS-SEC-050) |
| `AX_SEC_SECRET_EXPOSURE` | E | T518/T519 | passing `Secret<T>` across an untrusted FFI boundary or public sink without explicit `expose_secret()` / `declassify` (`REQ-FFI-117`, `SPEC-53` AXS-SEC-005, AXS-SEC-020, AXS-SEC-050) |
| `AX_SEC_INVALID_CONSTANT_TIME_ATTR` | E | T518 | `@constant_time` or `@secret` applied to an invalid item (`async fn`, `extern fn` without body, or non-zeroizable type) (`SPEC-53` AXS-SEC-020, AXS-SEC-023, AXS-SEC-050) |
| `AX_CAP_ZERO_COPY_DESERIALIZE_UNPROVEN` | E | T518 | zero-copy deserialization requested for a type `T` lacking proven bit-validity, alignment, or `@repr(C)` layout (`REQ-CAP-141`, `SPEC-53` AXS-SEC-014, AXS-SEC-050) |
| `AX_CAP_IO_BUFFER_OVERLAP` | E | T519 | scatter/gather I/O vector constructed with overlapping mutable buffer slices (`REQ-CAP-135`, `REQ-CAP-139`, `SPEC-53` AXS-SEC-013, AXS-SEC-050) |
| `AX_DRIVER_INVALID_PANIC_STRATEGY` | E | T522 | unknown `--panic <mode>` or `axiom.toml` `panic` value outside `{abort, unwind}`, or `--panic unwind` requested on a freestanding `--no-std` target lacking an unwinder (`REQ-FFI-125`, `SPEC-54` AXS-PAN-001, AXS-PAN-004, AXS-PAN-050) |
| `AX_PANIC_FORBIDDEN_IN_NO_PANIC` | E | T522 | `@no_panic` function directly or transitively calls `panic`, `unreachable`, `assert`, `Option.unwrap`, `Result.unwrap`, unchecked indexing, checked division/remainder without a non-zero proof, or a non-`@no_panic` function (`REQ-ABI-105`, `SPEC-54` AXS-PAN-005, AXS-PAN-050) |
| `AX_TYPE_INVALID_NO_PANIC_ATTR` | E | T522 | `@no_panic` attribute applied to a non-function item (`struct`, `enum`, `trait`, `type`, `let`, `const`, `static`) (`SPEC-54` AXS-PAN-005, AXS-PAN-050) |
| `AX_FFI_INVALID_UNWIND_CONTRACT` | E | T522 | invalid unwind-crossing attribute or calling-convention modifier applied to an `extern "C"` declaration or exported function (`REQ-FFI-004`, `REQ-FFI-041`, `REQ-FFI-093`, `SPEC-54` AXS-PAN-010, AXS-PAN-050) |
| `AX_CTM_RUNTIME_CALL_FORBIDDEN` | E | T551 | `comptime fn` called from a runtime expression context (`SPEC-60` AXS-CTM-002, AXS-CTM-050) |
| `AX_CTM_NON_CONST_CAPTURE` | E | T551 | `comptime { ... }` block or `const`/`static` initializer references a runtime local or non-`comptime` parameter (`SPEC-60` AXS-CTM-002, AXS-CTM-050) |
| `AX_CTM_CAPABILITY_DENIED` | E | T551 | `comptime` evaluation invokes ambient OS filesystem, network, environment (`env`), clock (`time`), process, or foreign `extern` FFI without an explicit granted comptime capability (`REQ-CTM-044`, `REQ-CTM-047`, `SPEC-60` AXS-CTM-003, AXS-CTM-050) |
| `AX_CTM_RESOURCE_ESCAPE` | E | T551/T552 | unpromoted comptime heap handle (`Vec`, `String`, `Box`), `mut_view`, `view` to a dead comptime local, raw comptime pointer, or authority token escapes across the comptime-to-runtime value lifting barrier (`REQ-CTM-002`, `REQ-CTM-004..006`, `REQ-CTM-009`, `REQ-CTM-011`, `SPEC-60` AXS-CTM-011, AXS-CTM-050) |
| `AX_CTM_CYCLE` | E | T552 | cyclic evaluation dependency among `const`, `static`, or `comptime` items (`SPEC-60` AXS-CTM-012, AXS-CTM-032, AXS-CTM-050; aliases `AX_CONST_CYCLE`) |
| `AX_CTM_STEP_LIMIT` | E | T552 | comptime evaluation exceeded the step limit or call-depth budget (`SPEC-60` AXS-CTM-012, AXS-CTM-050; aliases `AX_CONST_EVAL_LIMIT`) |
| `AX_CTM_MEM_LIMIT` | E | T552 | comptime evaluation exceeded the compiler arena memory budget (`SPEC-60` AXS-CTM-012, AXS-CTM-050) |
| `AX_CTM_PANIC` | E | T552 | explicit `panic(...)` or failed `assert(...)` executed during comptime evaluation (`SPEC-60` AXS-CTM-012, AXS-CTM-050) |
| `AX_CTM_NON_CONST_STATIC_INIT` | E | T551/T552 | `const`, `static`, or `@thread_local static` initialized with a runtime-only expression (`SPEC-60` AXS-CTM-032, AXS-CTM-050) |
| `AX_CTM_STATIC_MOVE_FORBIDDEN` | E | T551/T552 | moving a `!Copy` value out of a `static` or `@thread_local static` storage place (`SPEC-60` AXS-CTM-031, AXS-CTM-050) |
| `AX_REFLECT_PRIVATE_FIELD` | E | T557 | cross-module compile-time reflection (`fields_of<T>()`, `type_info<T>()`, `offset_of<T, F>()`) accesses private fields of `T` without defining-module or `@derive` authority (`SPEC-61` AXS-RFL-010, AXS-RFL-050) |
| `AX_REFLECT_UNSPECIFIED_LAYOUT` | E | T557 | `offset_of` queried on a non-existent field or a type whose representation does not define a valid addressable field offset (`SPEC-61` AXS-RFL-012, AXS-RFL-050) |
| `AX_REFLECT_RUNTIME_NOT_ENABLED` | E | T557 | `runtime_type_info<T>()` requested for a type `T` not explicitly opted into runtime reflection via `@reflect(runtime)` (`REQ-CTM-039`, `SPEC-61` AXS-RFL-002, AXS-RFL-050) |
| `AX_DERIVE_FIELD_BOUND` | E | T558 | `@derive(Trait)` applied to a struct or enum whose field or variant payload type does not implement `Trait`, with provenance spans for `@derive` and the offending field/variant (`SPEC-61` AXS-RFL-021..022, AXS-RFL-050) |
| `AX_DERIVE_CONFLICT` | E | T558 | duplicate `@derive(Trait)` on the same type, or conflict between `@derive(Trait)` and an explicit `impl Trait for T` (`SPEC-61` AXS-RFL-022, AXS-RFL-050) |
| `AX_DERIVE_CYCLE` | E | T558 | cyclic derive or compile-time declaration generation dependency (`SPEC-61` AXS-RFL-022, AXS-RFL-050) |
| `AX_DERIVE_UNSUPPORTED_ITEM` | E | T558 | `@derive(...)` attached to an unsupported declaration kind or illegal combination such as `@derive(Copy)` on a `Drop` type (`SPEC-61` AXS-RFL-021, AXS-RFL-050) |
| `AX_UNSAFE_AT_FOREIGN_PLACEMENT` | E | T531 | `@at(image("...") + off)` or `@at(image_self() + off)` declaration has an initializer `= init` or a function body `{ ... }` (`ADR-0001 §5`, `SPEC-56` AXS-MOD-003, AXS-MOD-050) |
| `AX_TYPE_INVALID_IMAGE_ARG` | E | T531 | `image(...)` called with a non-string-literal argument, an empty string `""`, or wrong argument count, or `image_self(...)` called with arguments (`SPEC-56` AXS-MOD-001, AXS-MOD-050) |
| `AX_UNSAFE_MODULE_NOT_LOADED` | E | T531 | oracle (`--interp`) pre-entry module-relative binding resolution failed because a target module named in `image("...")` is not loaded in `ProcessModuleMap` (`ADR-0001 §5`, `SPEC-56` AXS-MOD-014, AXS-MOD-050) |
| `AX_GEN_YIELD_OUTSIDE_GEN` | E | T562 | `yield` expression used outside a `gen fn` body (`SPEC-62` AXS-GEN-002, AXS-GEN-050) |
| `AX_GEN_SELF_BORROW_ACROSS_YIELD` | E | T562 | capability (`view<T>`, `mut_view<T>`, `Str`, slice view) borrowing a generator local or captured parameter is held live across a `yield` suspension point (`SPEC-62` AXS-GEN-012, AXS-GEN-050) |
| `AX_GEN_VIEW_ACROSS_YIELD` | E | T562 | ephemeral capability (`view<T>`, `mut_view<T>`), `@thread_local` view, or view into a generator-owned local escapes through `yield` or is held across `yield` without proven outer provenance (`SPEC-62` AXS-GEN-012..013, AXS-GEN-050) |
| `AX_GEN_RETURN_VALUE` | E | T562 | `return <expr>` with a value used inside a `gen fn` body instead of bare `return` (`SPEC-62` AXS-GEN-002, AXS-GEN-050) |
| `AX_GEN_RECURSIVE` | E | T562 | direct or mutual recursion among `gen fn` bodies creates an unboxed infinite-size generator state machine (`SPEC-62` AXS-GEN-002, AXS-GEN-050) |
| `AX_GEN_GPU_FORBIDDEN` | E | T562 | `gen fn` or `yield` used inside a `@gpu` kernel execution domain (`SPEC-62` AXS-GEN-023, AXS-GEN-050) |
| `AX_DYN_NOT_OBJECT_SAFE` | E | T058 | `dyn Trait` formed with a trait that violates object safety: requires `Self: Sized`, declares an associated `const`, has an unbound associated `type`, declares a method without a `view<Self>`/`mut_view<Self>`/`Box<Self>` receiver, declares a generic method `fn m<U>(...)`, mentions `Self` in non-receiver parameter/return position, or combines multiple non-auto principal traits (`SPEC-63` AXS-DYN-002..003, AXS-DYN-050) |
| `AX_DRIVER_INVALID_ARTIFACT_KIND` | E | T750/T686/T691 | unknown `--kind <k>` or `axiom.toml` `kind` value outside `{exe, bin, obj, lib, staticlib, dll, cdylib, axlib, rlib, wasm-module, wasm-reactor}`, `wasm-module`/`wasm-reactor` on non-WASM, `dll`/`cdylib` on bare-metal `<arch>-none`, or `--universal-targets` combined with unsupported `--kind obj` (`--emit=obj`) or `wasm-module`/`wasm-reactor` (exit code 2; passing a recognized non-`exe` `--kind` or `--universal-targets` to `axiomc run` emits `AX_DRIVER_USAGE`; `SPEC-26` AXS-WLIB-002, AXS-WLIB-050; `SPEC-89` AXS-ARTM-002, AXS-ARTM-032; `SPEC-90` AXS-UNIV-026, AXS-UNIV-031..032) |
| `AX_LINK_BAD_ARCHIVE` | E | T750/T066/T666/T667/T675/T679/T690/T695 | input `.lib`/`.a`/`.axlib` archive (including COFF `.lib` / short-import `.lib` on `aarch64-windows` or a `BsdAr` slice inside a Mach-O Fat container) lacks `!<arch>\n` magic, has truncated/corrupt 60-byte member headers or `#1/<len>` extended names, or invalid linker symbol directory (`__.SYMDEF` / `/`) offsets (`SPEC-26` AXS-WLIB-012, AXS-WLIB-050; `SPEC-80` AXS-ELFS-029, AXS-ELFS-050; `SPEC-84` AXS-MACHO-019, AXS-MACHO-033; `SPEC-86` AXS-WASM-027..028, AXS-WASM-031; `SPEC-87` AXS-RV64-040, AXS-RV64-048; `SPEC-90` AXS-UNIV-021, AXS-UNIV-032; `SPEC-91` AXS-WA64-016, AXS-WA64-033) |
| `AX_LINK_LIBRARY_NOT_FOUND` | E | T750/T066/T659/T667/T670/T683/T695 | library requested via `-l<name>` or `@link("<name>")` cannot be found in any `-L<dir>` search path, `--target-sdk`/`--sysroot` directory, `.tbd`/`.dylib` stub search, Android Bionic stub catalog, or built-in OS import stub table (`data.library`; `SPEC-26` AXS-WLIB-003, AXS-WLIB-050; `SPEC-80` AXS-ELFS-035; `SPEC-82` AXS-ELFD-031, AXS-ELFD-046; `SPEC-84` AXS-MACHO-028, AXS-MACHO-033; `SPEC-85` AXS-ANDR-013, AXS-JNI-017; `SPEC-88` AXS-XCMP-022, AXS-PLAT-022; `SPEC-91` AXS-WA64-032..033) |
| `AX_LINK_DUPLICATE_EXPORT` | E | T751/T659/T667/T670/T671/T675/T695 | two `@export`, `@jni_export`, or `@wasm_export` items in the same linked image resolve to the identical external export symbol name (`data.symbol`; `SPEC-26` AXS-WLIB-004, AXS-WLIB-050; `SPEC-82` AXS-ELFD-029, AXS-ELFD-046; `SPEC-84` AXS-MACHO-024, AXS-MACHO-033; `SPEC-85` AXS-ANDR-014, AXS-JNI-014, AXS-JNI-017; `SPEC-86` AXS-WASM-023, AXS-WASM-028, AXS-WASM-031; `SPEC-91` AXS-WA64-028, AXS-WA64-033) |
| `AX_QUERY_CYCLE` | E | T754 | generic illegal cyclic query dependency detected on the active `QueryStack` after canonical `SemanticKey` rotation (`SPEC-21` AXS-QRY-021..022, AXS-QRY-050) |
| `AX_TYPE_CYCLE` | E | T754 | cyclic type alias definition (`type A = B; type B = A`) or infinite value-sized struct/enum layout recursion without indirection (`SPEC-21` AXS-QRY-020..022, AXS-QRY-050) |
| `AX_TRAIT_CYCLE` | E | T754 | cyclic trait or obligation resolution goal under `CyclePolicy.Reject` or `DepthLimited` (`SPEC-21` AXS-QRY-020..022, AXS-QRY-050) |
| `AX_QUERY_DEPTH_LIMIT` | E | T754 | demand-driven query evaluation stack depth exceeded configured recursion limit (`SPEC-21` AXS-QRY-021, AXS-QRY-050) |
| `AX_LINK_BAD_ARTIFACT` | E | T765/T766 | invalid magic, truncated header or section table, out-of-bounds offset/size, overlapping sections, or failed BLAKE3 `content_hash`/`checksum` in `.axmi`, `.axmeta`, `.axlto`, or `.axpkg` (`SPEC-24` AXS-ART-002..004, AXS-ART-022, AXS-ART-050) |
| `AX_LINK_ARTIFACT_SCHEMA_MISMATCH` | E | T765/T766 | unsupported `schema_version`, unknown non-optional section (`RequiredUnknown`), or incompatible MIR/LTO/interface schema version in `.axmi` or `.axmeta`/`.axlto` (`data.expected_version`, `data.found_version`; `SPEC-24` AXS-ART-005, AXS-ART-013, AXS-ART-050) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | E | T765/T766/T066/T654/T659/T663/T666/T667/T670/T675/T679/T682/T683/T690/T691/T694/T695 | `TargetFingerprint`, endianness, pointer width, COFF `Machine` (`0x8664` vs `0xAA64`) / ELF `e_machine` (`EM_X86_64`, `EM_AARCH64`, `EM_RISCV`) / Mach-O `cputype` (`CPU_TYPE_X86_64`, `CPU_TYPE_ARM64`) / `.wasm` target & memory sharing mode, required CPU/WASM/RISC-V features, `e_flags` float ABI, `AbiFingerprint`, or profile/panic strategy in `.axmi`/`.axmeta`/`.obj`/`.lib`/`.o`/`.wasm`/`.so`/`.dylib`/`.tbd` conflicts with the active compilation target, or a linked Mach-O Fat `.a`/`.axlib`/`.dylib` or `.tbd` stub lacks a slice matching the active Darwin target leg (`data.expected_target`, `data.found_target`, `data.available_slices`; `SPEC-24` AXS-ART-022..023, AXS-ART-050; `SPEC-80` AXS-ELFS-023, AXS-ELFS-028, AXS-ELFS-050; `SPEC-81` AXS-TGTD-003, AXS-TGTD-050; `SPEC-82` AXS-ELFD-031, AXS-ELFD-046; `SPEC-83` AXS-A64-040, AXS-A64-048, AXS-A64-050; `SPEC-84` AXS-MACHO-019, AXS-MACHO-028, AXS-MACHO-032..033; `SPEC-85` AXS-ANDR-001, AXS-JNI-017; `SPEC-86` AXS-WASM-001, AXS-WASM-028, AXS-WASM-031; `SPEC-87` AXS-RV64-037, AXS-RV64-040, AXS-RV64-048; `SPEC-88` AXS-XCMP-009, AXS-XCMP-021, AXS-PLAT-022; `SPEC-90` AXS-UNIV-018, AXS-UNIV-022, AXS-UNIV-032; `SPEC-91` AXS-WA64-011, AXS-WA64-016, AXS-WA64-025, AXS-WA64-033) |
| `AX_LINK_ABI_MISMATCH` | E | T067/T675/T695 | cross-object calling convention (including variadic vs non-variadic `CallConv.WinArm64`), WASM `FuncType` / import `(module, name)` signature, symbol kind, or `.axmeta` `AbiFingerprint` mismatch for the same external symbol (`data.symbol`, `data.demangled`, `data.expected_abi`, `data.found_abi`; `SPEC-27` AXS-LNK-005, AXS-LNK-014, AXS-LNK-050; `SPEC-86` AXS-WASM-028, AXS-WASM-031; `SPEC-91` AXS-WA64-025, AXS-WA64-033) |
| `AX_TARGET_FEATURE_CONFLICT` | E | T654/T662/T666/T674/T675/T678/T694 | mutually exclusive or contradictory target features or WASM shared-memory configurations requested in `--target-feature` or `@target_feature` (`SPEC-81` AXS-TGTD-008, AXS-TGTD-050; `SPEC-83` AXS-A64-003, AXS-A64-050; `SPEC-84` AXS-MACHO-002, AXS-MACHO-033; `SPEC-86` AXS-WASM-003, AXS-WASM-031; `SPEC-87` AXS-RV64-003, AXS-RV64-048; `SPEC-91` AXS-WA64-002, AXS-WA64-033) |
| `AX_TARGET_UNSUPPORTED_OP` | E | T655/T662/T666/T674/T678/T682/T694 | `LIR` operation, atomic width, linkage kind, or ABI convention (such as x86-only `IRETQ` `extern "interrupt"` on `aarch64-windows`) cannot be legally expanded on the active target/profile without violating semantics (`SPEC-81` AXS-TGTD-029, AXS-TGTD-032, AXS-TGTD-050; `SPEC-83` AXS-A64-048, AXS-A64-050; `SPEC-84` AXS-MACHO-011, AXS-MACHO-033; `SPEC-86` AXS-WASM-003, AXS-WASM-008, AXS-WASM-031; `SPEC-87` AXS-RV64-004, AXS-RV64-014, AXS-RV64-048; `SPEC-88` AXS-XCMP-010, AXS-PLAT-022; `SPEC-91` AXS-WA64-001, AXS-WA64-010, AXS-WA64-033) |
| `AX_VERIFY_MC_ILLEGAL` | E | T655/T662/T666/T670/T678/T694 | hand-written or deserialized Machine IR in a verifier test violates `verify_mc` pre-encoding invariants, including unauthorized `X18` writes or general allocations in `aarch64-windows` functions, unaligned `SP`, missing `BL __chkstk` (`X15 = alloc_bytes >> 4`) on frames `>= 4096` bytes, or non-unwindable prologue/epilogue instructions (`data.rule`, `data.opcode`, `data.detail`; `SPEC-81` AXS-TGTD-036..038, AXS-TGTD-050; `SPEC-83` AXS-A64-037, AXS-A64-050; `SPEC-84` AXS-MACHO-004, AXS-MACHO-009, AXS-MACHO-033; `SPEC-85` AXS-ANDR-005, AXS-JNI-017; `SPEC-87` AXS-RV64-032..033, AXS-RV64-048; `SPEC-91` AXS-WA64-003, AXS-WA64-008..009, AXS-WA64-017, AXS-WA64-033) |
| `AX_LINK_TEXTREL_FORBIDDEN` | E | T658/T659/T663/T667/T670/T679/T690/T695 | non-PIC or text-mutating relocation (`R_X86_64_64`, `R_X86_64_32`, `R_X86_64_32S`, non-local `R_X86_64_PC32`, `R_AARCH64_ABS64`, `R_AARCH64_ABS32`, `R_RISCV_64`, `R_RISCV_32`, `ARM64_RELOC_UNSIGNED` / `X86_64_RELOC_UNSIGNED` in `__TEXT`, or writable `.reloc` base relocation targeting read-only/executable `.text` in PE32+ ARM64) targets a read-only or executable segment in a `PIE`, `.so`, `MH_EXECUTE`, `MH_DYLIB`, or PE32+ image (`data.section`, `data.symbol`; `SPEC-82` AXS-ELFD-018, AXS-ELFD-046; `SPEC-83` AXS-A64-040..041, AXS-A64-050; `SPEC-84` AXS-MACHO-022, AXS-MACHO-033; `SPEC-85` AXS-ANDR-011, AXS-JNI-017; `SPEC-87` AXS-RV64-040, AXS-RV64-048; `SPEC-90` AXS-UNIV-005, AXS-UNIV-032; `SPEC-91` AXS-WA64-029, AXS-WA64-033) |
| `AX_DRIVER_INVALID_ANDROID_API` | E | T670 | `--android-api <N>`, `aarch64-linux-android<N>`, or `[target.aarch64-android] api_level` specifies an Android API level `< 21`, `> 99`, non-integer, or conflicting values (exit code 2; `SPEC-85` AXS-ANDR-001, AXS-JNI-017) |
| `AX_TARGET_API_LEVEL_TOO_LOW` | E | T670 | referenced Android Bionic/NDK symbol or input `.note.android.ident` requires Android API level `M > target.api_level` (`data.symbol`, `data.required_api`, `data.target_api`; `0198 §24`, `SPEC-85` AXS-ANDR-012..013, AXS-JNI-017) |
| `AX_LINK_ANDROID_PRIVATE_LIB` | E | T670 | linking `-l<name>` or `@link("<name>")` against a non-NDK private Android platform shared library (`libart.so`, `libbinder.so`, `libcutils.so`, `libutils.so`, `libgui.so`, …) without `--allow-private-android-libs` (`data.library`; `0198 §11, §28`, `SPEC-85` AXS-ANDR-014, AXS-JNI-017) |
| `AX_FFI_INVALID_JNI_EXPORT` | E | T671 | `@jni_export` applied to a non-`fn`, generic `fn`, `async fn`, or `gen fn`, given invalid Java `package`/`class`/`name` identifiers, or declared with non-JNI parameter/receiver/return types (`0200 §32–34, §49`, `SPEC-85` AXS-JNI-012, AXS-JNI-017) |
| `AX_FFI_JNI_LOCAL_ESCAPE` | E | T671 | returning a bare `JLocal<T>` without `into_jni_return()`, escaping `JLocal<T>` or `view<JniEnv>`/`mut_view<JniEnv>` out of `with_local_frame` or `JavaVM.with_attached_env`, or storing `JLocal<T>`/`view<JniEnv>` in a `static` or escaping aggregate (`0200 §5, §32–34, §49`, `SPEC-85` AXS-JNI-004, AXS-JNI-006, AXS-JNI-013, AXS-JNI-017) |
| `AX_TYPE_STORED_VIEW_ESCAPE` | E | T048/T125/T671 | stored `view<T>` / `mut_view<T>` or view-containing aggregate escapes into a `static`/long-lived place, outlives its backing owner, or appears in a function return type without a valid input-rooted lifetime (`SPEC-11` AXS-CAP-006; `SPEC-85` AXS-JNI-004, AXS-JNI-013, AXS-JNI-017) |
| `AX_CAP_CONFLICT_READ` | E | T048/T125/T501/T671 | creating or using a shared `view<T>` read capability overlaps an active exclusive `mut_view<T>` capability (`SPEC-11` AXS-CAP-003; `SPEC-50` AXS-UNS-005..006, AXS-UNS-050; `SPEC-85` AXS-JNI-010, AXS-JNI-017) |
| `AX_FFI_INVALID_WASM_ATTR` | E | T674/T675 | `@wasm_import` attached outside an `extern` declaration or to a function with a body, `@wasm_export` attached to a non-`fn`/non-`static`, `async fn`, or `gen fn`, or empty/ill-formed `module` or `name` string (`tasks/0523 §155 AWASM-56..57`, `SPEC-86` AXS-WASM-023, AXS-WASM-031) |
| `AX_VERIFY_WASM_ILLEGAL` | E | T675 | hand-constructed or deserialized WASM module/function IR in a `verify_wasm` negative test violates polymorphic operand-stack typing, structured control-flow label/arity rules, index bounds, `memarg` alignment (`2^align > width`, or `!= width` for atomics), or active `TargetFeatureSet` gating (`data.rule`, `data.opcode`, `data.func`; `tasks/0523 §155 AWASM-63..64`, `SPEC-86` AXS-WASM-026, AXS-WASM-031) |
| `AX_NAME_INVALID_CFG_PREDICATE` | E | T682 | malformed `@cfg(...)` syntax/arity (`@cfg()`, `@cfg(a, b)`, `not(a, b)`), non-string value literal, bare OS/arch identifier (`@cfg(windows)`), unknown `@cfg` key, value outside the key's closed canonical set (`@cfg(target_os = "win32")`), or undeclared `--cfg` / package `feature` name (`data.key`, `data.value`; `tasks/0587 §9–11, §36`, `SPEC-88` AXS-XCMP-012..017, AXS-XCMP-020, AXS-PLAT-022) |
| `AX_DRIVER_SYSROOT_NOT_FOUND` | E | T682/T683 | explicit `--sysroot <dir>` or `--target-sdk <dir>` directory does not exist or is unreadable during cross-compilation or `--hermetic` linking (exit code 2; `tasks/0453 §194.20–21`, `tasks/0587 §14`, `SPEC-88` AXS-XCMP-021..022, AXS-PLAT-022) |
| `AX_LINK_THIN_ARCHIVE_UNSUPPORTED` | E | T686 | non-hermetic GNU thin archive (`!<thin>\n`) passed as a static library or linker input (`data.archive`; `SPEC-89` AXS-ARTM-008, AXS-ARTM-032) |
| `AX_LINK_UNMATCHED_WHOLE_ARCHIVE` | E | T686 | unclosed `--whole-archive` without matching `--no-whole-archive`, stray `--no-whole-archive`, empty whole-archive group, or non-archive file passed to `-force_load` (`data.flag`; `SPEC-89` AXS-ARTM-026, AXS-ARTM-032) |
| `AX_LINK_AXLIB_PACKAGE_CONFLICT` | E | T686/T688 | diamond dependency graph links two `.axlib` (or `.axlib` + bundled `staticlib`) artifacts for the same `package` with differing `InterfaceFingerprint` or `AbiFingerprint` (`data.package`, `data.first_artifact`, `data.second_artifact`; `SPEC-89` AXS-ARTM-014, AXS-ARTM-032) |
| `AX_LINK_INVALID_DEF_FILE` | E | T687/T695 | syntax or semantic error in a Windows `.def` module-definition file (`--def <path>`), including ordinal outside `1..65535`, `NONAME` without `@<ordinal>`, malformed forwarder `Sym = OTHER.Target`, or `LIBRARY` mismatch (`data.file`, `data.line`, `data.detail`; `SPEC-89` AXS-ARTM-016, AXS-ARTM-032; `SPEC-91` AXS-WA64-028, AXS-WA64-033) |
| `AX_LINK_INVALID_VERSION_SCRIPT` | E | T687 | syntax or semantic error in an ELF `--version-script` or `@export(version = ...)` declaration, including duplicate version nodes, undefined/cyclic parent version node, or multiple default `@@` versions for one symbol (`data.version`, `data.symbol`; `SPEC-89` AXS-ARTM-020, AXS-ARTM-032) |
| `AX_LINK_INVALID_DYLIB_VERSION` | E | T687/T690/T691 | malformed Mach-O `--current-version` or `--compatibility-version` (`X.Y.Z` with `X > 65535` or `Y, Z > 255`), `compatibility_version > current_version`, empty/NUL-containing `--install-name`, `--soname`, or `--rpath`, or composed Universal `MH_DYLIB` slices disagreeing on `LC_ID_DYLIB` `install_name`, `current_version`, or `compatibility_version` (`data.flag`, `data.value`; `SPEC-89` AXS-ARTM-018, AXS-ARTM-021, AXS-ARTM-032; `SPEC-90` AXS-UNIV-019, AXS-UNIV-032) |
| `AX_LINK_WASM_ENTRY_CONFLICT` | E | T687 | WASM reactor (`--kind dll`/`cdylib`) defines reserved `_start`, or WASM command (`--kind exe`) defines explicit `_initialize` conflicting with command startup (`data.symbol`, `data.kind`; `SPEC-89` AXS-ARTM-023, AXS-ARTM-032) |
| `AX_DRIVER_INVALID_UNIVERSAL_TARGETS` | E | T691 | empty `--universal-targets` value, empty comma-separated element, fewer than 2 target slices, or mutually exclusive `--target` combined with `--universal-targets` (exit code 2; `data.flag`, `data.value`; `SPEC-90` AXS-UNIV-026, AXS-UNIV-032) |
| `AX_DRIVER_UNIVERSAL_TARGET_INCOMPATIBLE` | E | T691 | non-Mach-O target (`x86_64-windows`, `x86_64-linux`, `wasm32-wasi`, `<arch>-none`, …) or cross-OS mix passed to Mach-O `--universal-targets` instead of a `.axpkg` multi-target package bundle (exit code 2; `data.target`; `SPEC-90` AXS-UNIV-023, AXS-UNIV-026, AXS-UNIV-032) |
| `AX_LINK_DUPLICATE_FAT_ARCH` | E | T690/T691 | two slices in `--universal-targets`, `--compose-universal`, or a Mach-O Fat container resolve to the identical `(cputype, cpusubtype & 0x00FF_FFFF)` (`data.arch`, `data.cputype`, `data.cpusubtype`; `SPEC-90` AXS-UNIV-014, AXS-UNIV-026, AXS-UNIV-032) |
| `AX_LINK_FAT_SLICE_KIND_MISMATCH` | E | T690/T692 | heterogeneous payload kinds across slices in a Mach-O Fat container (`MH_EXECUTE` mixed with `MH_DYLIB` or `BsdAr`), legacy 32-bit `MH_MAGIC` (`0xFEED_FACE`) or non-Mach-O/non-`BsdAr` slice bytes, or inner `mach_header_64.cputype` disagreeing with outer `fat_arch.cputype` (`data.slice_index`, `data.expected_kind`, `data.found_kind`; `SPEC-90` AXS-UNIV-010, AXS-UNIV-018..019, AXS-UNIV-032) |
| `AX_LINK_UNALIGNED_FAT_SLICE` | E | T690/T692 | Mach-O Fat slice descriptor violates alignment invariants: `align > 30`, `(offset & ((1u64 << align) - 1)) != 0`, or `MH_EXECUTE`/`MH_DYLIB` slice `align` below target VM page shift (`< 12` for `CPU_TYPE_X86_64`, `< 14` for `CPU_TYPE_ARM64`; `data.arch`, `data.offset`, `data.align`; `SPEC-90` AXS-UNIV-013, AXS-UNIV-032) |
| `AX_LINK_BAD_UNIVERSAL` | E | T690/T691/T692 | corrupt or malformed Mach-O Fat / Universal 2 container: invalid magic (including JVM `.class` `0xCAFEBABE`), `nfat_arch == 0` or `> 16`, truncated header/descriptor table, `size == 0`, `offset < hdr_end`, `offset + size` overflow or exceeding file length, overlapping slices, or non-zero `fat_arch_64.reserved` (`data.file`, `data.detail`; `SPEC-90` AXS-UNIV-010..018, AXS-UNIV-032) |
| `AX_LINK_BAD_CODESIGN` | E | T690/T691/T692 | corrupt or mismatched per-slice `LC_CODE_SIGNATURE` (`CS_SuperBlob` / `CS_CodeDirectory` magic, bounds, `pageSize`, or SHA-256 page hash mismatch over `[0 .. slice_sig_off)`) during Universal composition or `--verify-arch` (`data.file`, `data.arch`, `data.detail`; `SPEC-90` AXS-UNIV-020, AXS-UNIV-028, AXS-UNIV-032) |
| `AX_LINK_FAT_ARCH_NOT_FOUND` | E | T691/T692 | architecture requested by `--extract-slice <arch>` or `--verify-arch <arch>` does not exist in the inspected Universal or thin file, or `--extract-slice` is invoked on a non-Fat thin file (`data.file`, `data.requested_arch`, `data.available_archs`; `SPEC-90` AXS-UNIV-028, AXS-UNIV-032) |
| `AX_LINK_BAD_UNWIND_INFO` | E | T694/T695 | malformed, truncated, or overlapping Windows `.pdata` or `.xdata` SEH unwind metadata (`BeginAddress % 4 != 0`, reserved `Flag == 3`, `RegI > 10`, `.xdata` `Vers != 0`, missing `0xE4`/`0xE5` end opcode, out-of-bounds `.xdata` RVA, or overlapping `[BeginAddress, EndAddress)` function intervals; `data.symbol`, `data.rva`, `data.detail`; `SPEC-91` AXS-WA64-019..020, AXS-WA64-024, AXS-WA64-033) |
| `AX_DRIVER_BAD_MANIFEST` | E | T060/T851/T852/T855/T856/T859/T860/T863/T864 | malformed `axiom.toml` TOML syntax or schema, invalid SemVer literal or version constraint (`REQ-PKG-022`; `data.kind = "semver"`), forbidden imperative build script key (`script`/`command`/`shell`/`eval`; `data.kind = "forbidden_script"`), missing/escaping `[workspace].members` entry (`data.kind = "workspace_member"`), inter-package dependency cycle (`REQ-PKG-008`, `REQ-PKG-011`; `data.kind = "package_cycle"`, `data.cycle`), unsatisfiable SemVer constraints with PubGrub conflict derivation chain (`data.kind = "version_conflict"`, `data.derivation_chain`), undeclared/conflicting/disabled required package feature (`REQ-PKG-025`; `data.kind = "unknown_feature" \| "feature_conflict" \| "missing_required_feature"`), duplicate native `links` package (`data.kind = "duplicate_native_links"`), `axiom.lock` drift or corruption under `--locked` / `verify-lock` (`data.kind = "lockfile_drift" \| "lockfile_corrupt"`), `SHA-256` content store / `vendor/` / `.axpkg` Merkle digest mismatch (`data.kind = "hash_mismatch" \| "merkle_mismatch"`), unpinned VCS branch/tag in reproducible mode (`data.kind = "unpinned_vcs"`), missing offline package (`data.kind = "offline_missing_package"`), immutable registry version overwrite (`data.kind = "immutable_version_exists"`), unpublishable path/VCS dependency (`data.kind = "unpublishable_dependency"`), `.axpkg` embedded manifest coordinate mismatch (`data.kind = "manifest_coordinate_mismatch"`), multi-repository `pinned_namespaces` shadowing/dependency-confusion attempt (`data.kind = "namespace_shadow_blocked" \| "conflicting_namespace_pin"`), quarantined or policy-blocked package version/rollback (`data.kind = "quarantined_package" \| "policy_blocked_version" \| "rollback_unavailable"`), archive path traversal / duplicate entry / decompression quota violation (`data.kind = "path_traversal" \| "duplicate_archive_entry" \| "archive_quota_exceeded"`), undeclared package capability or transitive `[trust.policy]` capability escalation (`REQ-PKG-024`; `data.kind = "undeclared_package_capability" \| "capability_escalation_denied"`), hermetic `BuildSandbox` filesystem/network/env/clock/RNG/process violation or undeclared `[[build_tool]]` output (`REQ-PKG-022`; `data.kind = "undeclared_build_output" \| "sandbox_fs_violation" \| "sandbox_net_violation" \| "sandbox_env_violation" \| "sandbox_clock_or_rng_violation" \| "sandbox_process_violation"`), unremapped host path leak or double-build `--verify-repro` binary mismatch (`REQ-PKG-022`; `data.kind = "repro_host_path_leak" \| "repro_mismatch"`), or Ed25519 signature / signer trust / key revocation / SDK digest / `.axprov.json` provenance / DDC bootstrap mismatch (`data.kind = "signature_invalid" \| "unsigned_package_rejected" \| "untrusted_signer" \| "revoked_signing_key" \| "sdk_integrity_mismatch" \| "provenance_mismatch" \| "ddc_mismatch"`; `ADR-0006 §6`, `SPEC-110` AXS-BLD-003, AXS-BLD-011..015, AXS-BLD-050; `SPEC-111` AXS-PKG-002..033, AXS-PKG-050; `SPEC-112` AXS-REG-003..034, AXS-REG-050; `SPEC-113` AXS-HERM-002..035, AXS-HERM-050) |
| `AX_ABI_UNSTABLE_TYPE` | E | T867 | attempt to pass or return an unstable type (capturing closure, unadorned/unrepr'd struct/enum, raw generic parameter, bare internal fat pointer/slice/string, internal trait object) across an `@abi(stable)` boundary (`SPEC-114` AXS-ABI-004, AXS-ABI-017) |
| `AX_ABI_EXTENSIBLE_MISSING_HEADER` | E | T867 | an `@abi(stable)` struct marked extensible or evolved with new fields is missing the mandatory `abi_version: u32, struct_size: u32` header fields (`SPEC-114` AXS-ABI-011) |
| `AX_ABI_OPAQUE_BY_VALUE` | E | T867 | an `@opaque` handle type is instantiated, queried for `size_of`/`align_of`, or passed/returned by value outside its defining module (`SPEC-114` AXS-ABI-013) |
| `AX_ABI_SYMBOL_VERSION_DUPLICATE` | E | T868 | multiple exported functions within the same package define the same identifier, module path, and `@symbol_version` string, or multiple functions in a group are marked `default = true` (`SPEC-114` AXS-ABI-030) |
| `AX_ABI_BREAKING_CHANGE` | E | T868 | the `axiomc abi-check` tool detected a breaking ABI/API change (removed symbol, modified field layout/offsets, changed parameter types, altered calling convention) without an accompanying major SemVer bump (`SPEC-114` AXS-ABI-040, AXS-ABI-041) |
| `AX_ABI_SEMVER_MISMATCH` | E | T868 | the `axiomc abi-check` tool detected an additive ABI/API change across a version increment specified as a patch release (`SPEC-114` AXS-ABI-040, AXS-ABI-041) |
| `AX_COMP_MISSING_ENTRY_POINT` | E | T871 | dynamic component binary is missing the mandatory `@plugin_export fn axiom_component_entry` entry point (`SPEC-115` AXS-COMP-004) |
| `AX_COMP_MISSING_MANIFEST` | E | T871/T872 | the `.axcomp` binary section was not found within the inspected dynamic library image (`SPEC-115` AXS-COMP-005, AXS-COMP-010) |
| `AX_COMP_CORRUPT_MANIFEST` | E | T871/T872 | the `.axcomp` section header contains invalid magic, an unknown version, or out-of-bounds offsets (`SPEC-115` AXS-COMP-005) |
| `AX_COMP_DUPLICATE_REGISTRATION` | E | T872 | duplicate registration of the identical `(ComponentId, SemanticVersion)` pair within the same process context (`SPEC-115` AXS-COMP-002) |
| `AX_COMP_TARGET_MISMATCH` | E | T872 | the component target triple hash does not match the host executable target triple (`SPEC-115` AXS-COMP-012) |
| `AX_COMP_VERSION_INCOMPATIBLE` | E | T872 | discovered component version does not satisfy the host SemVer requirement query (`SPEC-115` AXS-COMP-011) |
| `AX_COMP_ABI_MISMATCH` | E | T872 | component `AbiFingerprint` differs from the host expected interface layout hash (`SPEC-115` AXS-COMP-012) |
| `AX_COMP_CAPABILITY_DENIED` | E | T872 | component manifest requests capabilities not granted by the host `CapabilityGrant` policy (`SPEC-115` AXS-COMP-013) |
| `AX_COMP_RAW_POINTER_ESCAPE` | E | T871 | safe `@component_interface` declaration accepts or returns a raw pointer (`*T`, `*mut T`) (`SPEC-115` AXS-COMP-020) |
| `AX_COMP_CROSS_ALLOCATOR_VIOLATION` | E | T871/T872 | owned heap allocation crossed a dynamic boundary without an originating allocator binding (`ComponentBox<T>`) (`SPEC-115` AXS-COMP-021) |
| `AX_COMP_STALE_HANDLE` | E | T872 | access attempted using a `ComponentHandle` whose generation or epoch token has been invalidated (`SPEC-115` AXS-COMP-022) |
| `AX_COMP_UNLOAD_ACTIVE_LEASES` | E | T872 | physical library unload attempted while active epoch leases, borrows, tasks, or callbacks remain live (`SPEC-115` AXS-COMP-023) |
| `AX_COMP_QUIESCE_TIMEOUT` | E | T872 | hot-reload quiescence failed because active operations did not drain within the timeout limit (`SPEC-115` AXS-COMP-031) |
| `AX_COMP_HOT_RELOAD_SCHEMA_MISMATCH` | E | T871/T872 | hot-reload state snapshot schema version cannot be parsed by candidate component (`SPEC-115` AXS-COMP-034) |
| `AX_COMP_HOT_RELOAD_MIGRATION_FAILED` | E | T872 | hot-reload migration hook returned an error; transactional rollback executed to previous epoch (`SPEC-115` AXS-COMP-034, AXS-COMP-036) |
| `AX_SDK_MANIFEST_NOT_FOUND` | E | T875 | `.axsdk` manifest `sdk.toml` or `sdk.json` missing or unreadable in sysroot directory (`SPEC-116` AXS-SDK-010) |
| `AX_SDK_CORRUPT_MANIFEST` | E | T875 | `.axsdk` manifest contains syntax errors, unknown schema version, or inconsistent metadata (`SPEC-116` AXS-SDK-010) |
| `AX_SDK_FINGERPRINT_MISMATCH` | E | T875/T876 | calculated `SdkFingerprint` does not match manifest or `axiom.lock` pinned digest (`SPEC-116` AXS-SDK-035, AXS-SDK-039) |
| `AX_SDK_TOOLCHAIN_FINGERPRINT_MISMATCH` | E | T875/T876 | calculated `ToolchainFingerprint` does not match active toolchain binary hash or `axiom.lock` pinned digest (`SPEC-116` AXS-SDK-036, AXS-SDK-039) |
| `AX_SDK_HOST_FALLBACK_DENIED` | E | T875 | hermetic build attempted fallback to ambient host OS paths without an installed `.axsdk` (`SPEC-116` AXS-SDK-004) |
| `AX_SDK_API_UNAVAILABLE` | E | T875 | referenced platform API requires an OS version newer than target deployment version without `@available(...)` guard (`SPEC-116` AXS-SDK-015) |
| `AX_SDK_IMPORT_STUB_NOT_FOUND` | E | T875 | required platform syscall or dynamic import stub (`.def`, `.tbd`, `.so` stub) not provided by `.axsdk` (`SPEC-116` AXS-SDK-012) |
| `AX_SDK_STARTUP_CONTRACT_MISMATCH` | E | T875 | CRT/startup contract incompatible with selected binary subsystem, runtime profile, or target ABI (`SPEC-116` AXS-SDK-013) |
| `AX_SDK_TOOLCHAIN_NOT_FOUND` | E | T875/T876 | requested `AXTOOLCHAIN` target descriptor or pipeline component not installed in toolchain store (`SPEC-116` AXS-SDK-025) |
| `AX_SDK_TOOLCHAIN_INCOMPATIBLE` | E | T875 | selected toolchain pipeline components disagree on pointer width, endianness, data model, or calling convention (`SPEC-116` AXS-SDK-026, AXS-SDK-027) |
| `AX_SDK_LOCK_MISMATCH` | E | T876 | active SDK or toolchain fingerprint differs from `axiom.lock` under `--locked` or `--frozen` (`SPEC-116` AXS-SDK-039) |
| `AX_SDK_BUNDLE_CORRUPT` | E | T876 | `.axsdk` or `.axtoolchain` distribution archive contains corrupt headers, checksum mismatch, or path traversal (`SPEC-116` AXS-SDK-043) |
| `AX_SDK_SIGNATURE_INVALID` | E | T876 | Ed25519 signature verification failed for `.axsdk` or `.axtoolchain` archive manifest against trusted public keys (`SPEC-116` AXS-SDK-044) |

## Sources
tasks/0360 (BOOTSTRAP-101, frozen: §1-§51, ADIAG-20..90); tasks/0791 (BOOTSTRAP-569: §10-§11); 0098; 0104; 0146 Part XXVII §3-§12, §19-§21, §50-§58;
0153 §37 (ADIAG-20..24, APAR-23); 0168 §38; 0171 §40 (AKERNEL-27/28/34); 0172 §10-§12; 0181; 0185..0188; 0193; 0198 §24; 0200 §49; tasks/0260 ABOOT-60..62; tasks/0356; tasks/0372; tasks/0411; tasks/0412; tasks/0446; tasks/0449; tasks/0452; tasks/0453 §194.20–21, §194.29; tasks/0521 §156 (AARM-20..65); tasks/0522 §100–102, §148–150, §159 (ABACKEND-20..60); tasks/0523 §155 (AWASM-20..95); tasks/0583; tasks/0584; tasks/0587 §9–14, §30–36; tasks/0590; tasks/0661; tasks/0665; tasks/0739; tasks/0772; tasks/0856; tasks/0858; tasks/1065;
tasks/0262 §46; SPEC-01 §9; SPEC-02 §10; ADR-0001; ADR-0002 §4; ADR-0004 §2; ADR-0005 §2-3, §14;
ADR-0006 §8; ADR-0007; ADR-0011; ADR-0036 §4; SPEC-03; SPEC-21; SPEC-22; SPEC-23; SPEC-24; SPEC-25; SPEC-26; SPEC-27; SPEC-30; SPEC-31; SPEC-32; SPEC-33; SPEC-40; SPEC-41; SPEC-42; SPEC-43; SPEC-44; SPEC-50; SPEC-51; SPEC-52; SPEC-53; SPEC-54; SPEC-55; SPEC-56; SPEC-60; SPEC-61; SPEC-62; SPEC-63; SPEC-70; SPEC-71; SPEC-72; SPEC-73; SPEC-74; SPEC-75; SPEC-76; SPEC-77; SPEC-80; SPEC-81; SPEC-82; SPEC-83; SPEC-84; SPEC-85; SPEC-86; SPEC-87; SPEC-88; SPEC-89; SPEC-90; SPEC-91; SPEC-100; SPEC-101; SPEC-102; SPEC-103; SPEC-104; SPEC-110; SPEC-111; SPEC-112; SPEC-113; SPEC-114; SPEC-115; axiom-c-stage0; axiom-testing.
