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
address introspection & fixed-address placement, and FFI/ABI (`SPEC-50`), `MEM` raw memory access, volatile/MMIO register wrappers, untagged `union` types, `@repr(packed)`/`@align(N)` layout, `MaybeUninit<T>`, `bitcast`, and pointer address spaces (`SPEC-51`), `FRE` freestanding execution, modular runtime composition, compilation profiles, `@entry`/`@naked`/`@section`/`@used`, interrupt handlers, and runtime capability graph (`SPEC-52`), `SEC` safety profiles, capability-based OS authority, `Secret<T>` zeroization, and `@constant_time` execution (`SPEC-53`), `PAN` panic strategies (`--panic abort|unwind`), `catch_unwind`, deterministic `Drop` unwinding, `@no_panic` verification, Windows x64 SEH `.pdata`/`.xdata` unwind tables, and `extern "C"` FFI no-unwind barrier (`SPEC-54`), `ADR` fixed-address `@at` / `@addr` overlay and placement declarations (`REQ-OWNER-003`), ordinary-syntax MMIO register access, `REQ-OWNER-008` address introspection, COFF `IMAGE_SYM_ABSOLUTE` symbols, pinned VMA sections, `--format bin` raw binary output, and oracle simulated address space & device model (`SPEC-55`), `MOD` module-relative `@at(image("mod") + offset)` and `@at(image_self() + offset)` hosted overlays (`REQ-OWNER-005`), overlay-only enforcement, open-world dynamic library optimization barrier (`REQ-ABI-095`, `REQ-FFI-119`), `LoadTimeSlot` indirect dispatch, `GetModuleHandleW`/`__ImageBase` PE DLL `DllMain` / EXE startup resolution, and oracle `ProcessModuleMap` (`SPEC-56`), `CTM` Comptime 2.0 unified execution model, sandboxed authority, value lifting & resource no-escape barrier, partial evaluation, specialization, dependency-tracked caching, and `const`/`static`/`TLS` initialization (`SPEC-60`), `RFL` compile-time reflection data model (`TypeInfo`, `FieldInfo`, `VariantInfo`, `TraitInfo`), visibility & layout query contracts, typed `@derive` synthesis with provenance tracking & full semantic/MIR re-verification, and zero-overhead `std.reflect` / `std.derive` (`SPEC-61`), `GEN` synchronous generators (`gen fn`, `yield`), lazy pull-based iterator state machines, `LiveAcrossYield` ownership & capability rules (`AX_GEN_*`), HIR → MIR boundary & structural invariants, per-state `Drop` cleanup, and `for-in` / `std.iter` lazy combinators (`SPEC-62`), `DYN` dynamic trait objects (`dyn Trait`), object-safety verification (`AX_DYN_NOT_OBJECT_SAFE`), two-word fat-pointer representation, unsizing coercions, `.rdata` vtable ABI, and `Box<dyn Trait>` dynamic `Drop` (`SPEC-63`). A new group is added by editing this list.

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

## Sources
0153 §37 (ACKERNEL, ASOURCE, AINTERN, AQUERY, APAR, ADIAG-20..24, APASS, ACACHE, ADET); 0171 §40
(AKERNEL-24..37); 0172 §1-§24; tasks/0260 §45 (ABOOT-41..80); tasks/0262 §42-§49; tasks/0360 §51
(ADIAG-20..90); 0146 §50-§58; 0151 §1-§25, §56-§57; 0188; 0212; 0229; 0263 §28, §46-§47; tasks/0351; tasks/0389; tasks/0476; tasks/0512; tasks/0517; tasks/0539; tasks/0700; ROADMAP R3, R6–R8; ADR-0001; ADR-0002;
ADR-0003; ADR-0004 §2, §4, §8; ADR-0005 §2, §15; ADR-0011; ADR-0034 §8; ADR-0036; SPEC-01 §11; SPEC-02 §10; SPEC-03; SPEC-12; SPEC-30; SPEC-31; SPEC-32; SPEC-33; SPEC-40; SPEC-41; SPEC-42; SPEC-43; SPEC-44; SPEC-50; SPEC-51; SPEC-52; SPEC-53; SPEC-54; SPEC-55; SPEC-56; SPEC-60; SPEC-61; SPEC-62; SPEC-63; SPEC-70; SPEC-71; SPEC-72; SPEC-73; SPEC-75; SPEC-76; SPEC-77; axiom-c-stage0.
Not catalogued here because they belong to later architecture (E18.1 query engine, E18.2 caches):
0153 AQUERY-21..25, ACACHE-20..24, ACKERNEL-22, 0171 AKERNEL-31..33. They are added when E18 is
planned (T218).
