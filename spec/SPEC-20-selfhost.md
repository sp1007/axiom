# SPEC-20 — Self-hosting plan: architecture, compiler layout, and differential verification

## Tóm tắt
Tài liệu này xác định **kế hoạch chuyển đổi (port) compiler từ Stage-0 C11 (`axiom0`) sang Axiom chuẩn (`axiomc`)**, thiết lập nền móng cho giai đoạn Phase 10:
- **Kiểm toán tập tính năng (Feature Audit)**: Tái thẩm định toàn bộ `spec/selfhost-subset.tsv` (72 tính năng từ `F-INT` tới `F-STD-OS.CLOCK`). Toàn bộ tính năng ngôn ngữ và thư viện chuẩn cần thiết đã được hoàn thiện trong P0–P9 và kiểm chứng qua suite conformance/real-programs (T075). Không có khoảng trống tính năng (0 gap tasks).
- **Bố cục mã nguồn `compiler/`**: Thiết lập cây thư mục chuẩn của `axiomc` bằng ngôn ngữ Axiom, phản chiếu trực tiếp 1:1 các module C trong `bootstrap/axiom0/src/` (kernel, source, diag, lex, syntax, resolve, hir, types, traits, own, mir, verify, interp, opt, lir, abi, target/x64, obj, link, driver).
- **Phân tách nhiệm vụ (Port Split)**: Phân rã 9 task lớn T077–T085 thành 23 sub-task nhỏ hơn hoặc bằng 1.500 dòng code Axiom (`T077a..c`, `T078a`, `T079a..b`, `T080a..b`, `T081a..c`, `T082a..e`, `T083a..b`, `T084a..d`, `T085a..c`). Các task cha T077–T085 giữ vai trò tích hợp và xác thực vi sai liên module.
- **Phân bổ mô hình trí tuệ nhân tạo (Model Policy)**: Sử dụng `opus` cho các module đòi hỏi phán đoán ngữ nghĩa chặt chẽ (types, traits/mono, ownership/init, capability, drop, MIR build, verifier, interpreter, optimizer); sử dụng `sonnet` cho các module kỹ thuật/cú pháp/hạ tầng khác.
- **Chiến lược kiểm chứng vi sai (Differential Strategy)**: Xác định rõ artifact kiểm chứng vi sai cho từng giai đoạn biên dịch (`inspect --emit=tokens`, `ast`, `hir`, `thir`, `mir`, `lir`, `obj`, và ảnh nhị phân PE `exe`), đảm bảo đồng nhất tuyệt đối với `axiom0` trên toàn bộ tập test `tests/`.
- **Ngân sách tự biên dịch (Self-Compile Budget)**: Cố định giới hạn tài nguyên tại T086:
  - `axiom0` -> `axiomc1`: thời gian chạy < 2 phút, đỉnh RAM < 2 GB.
  - `axiomc1` self-compile (`axiomc1` -> `axiomc2`): thời gian chạy < 10 phút, đỉnh RAM < 4 GB.
  - Cờ biên dịch chuẩn cho mọi stage: `-O1 --stack-reserve 67108864`.
- **Điểm cố định và đóng băng bootstrap (Fixed Point & Freeze)**: T087 chứng minh điểm cố định (`axiomc2` và `axiomc3` đồng nhất từng byte). Gắn tag `axiom0-frozen`, đóng băng `bootstrap/axiom0` ngoại trừ các bản vá `AX0-FIX`.
- **Tái định tuyến hậu self-host**: Cập nhật lại đường dẫn cho các task P11+ (T058, T063, T064, T066, T067, T068, T750, T751) vào cấu trúc `compiler/<module>`.

Status: canonical (T076, 2026-10-14). Rule ids `AXS-SELF-NNN` are stable.
Decisions: ADR-0005 §7-§8 (port split, compile-time budget, regalloc contingency), ADR-0002 (host interface), ADR-0003 (ABI lowering on LIR), ADR-0004 (subset additions), ADR-0006 (bootstrap forms), ADR-0012 (manifest format), ADR-0013 (self-host subset closure).
Subset: `spec/SPEC-00-bootstrap.md` §9 and `spec/selfhost-subset.tsv`.
Plan frame: `spec/ROADMAP.md` (R1-R9).
Consumers: T077–T087 (Phase 10 port and bootstrap), axiom-qa (differential validation), all P11+ epic planning tasks.

---

## 1. Principles & Self-Hosting Strategy

**AXS-SELF-001 — Direct 1:1 Module Correspondence.** The Axiom compiler written in Axiom (`axiomc`) is structured under `compiler/` such that every module directly corresponds to a C module from `bootstrap/axiom0/src/`. This preserves conceptual continuity, keeps architectural invariants (`tools/archcheck.py`) clear, and allows fine-grained differential verification against the C implementation at every stage. [0263 §51; tasks/0260 ABOOT-41; tasks/0261]

**AXS-SELF-002 — Canonical Syntax and Idioms.** All Axiom source code in `compiler/` and `std/` strictly adheres to canonical Axiom syntax:
- Variable binding and assignment use `=` only (no `:=`, no `var`, per project owner decision).
- Module paths, record fields, and method calls use `.` only (no `::`, per project owner decision).
- Visibility is explicitly controlled via `pub` and `pub(crate)`.
- Error propagation uses `?` over `Result<T, E>`.
- Ownership, `view`, and `mut_view` capabilities are used idiomatically without runtime reference counting or garbage collection. [ADR-0007; .claude/skills/axiom-syntax/SKILL.md]

**AXS-SELF-003 — Standard Library Boundary.** The self-hosting compiler depends strictly on the audited self-host subset of the standard library (`std.core`, `std.alloc`, `std.text`, `std.collections`, `std.arena`, `std.io`, `std.fs`, `std.process`, `std.time`). It does not invoke host OS APIs directly except through `std`; all host memory allocations flow through `std.alloc` and host I/O through `std.io`/`std.fs`. [ROADMAP R8; ADR-0002; SPEC-00 §9.2]

**AXS-SELF-004 — Sub-Task Sizing Limit.** To avoid oversized tasks and ensure high-fidelity verification within a single sitting, port tasks T077–T085 are subdivided into sub-tasks containing ≤ 1,500 lines of Axiom code each. Each sub-task is assigned an explicit differential test artefact and a dedicated harness entry point. [ADR-0005 §8; 0264 §20]

**AXS-SELF-005 — Autonomous AI Model Assignment Policy.**
- **Opus (`model: opus`)**: Assigned to sub-tasks requiring deep semantic reasoning, complex invariant preservation, and architectural judgement: types data model, trait solver and monomorphization, type checking and inference, ownership and definite initialization, capability tracking, drop elaboration, MIR builder, MIR verifier, MIR interpreter, and MIR optimizer.
- **Sonnet (`model: sonnet`)**: Assigned to syntactic, procedural, backend, formatting, and structural tasks: kernel data structures, source manager, diagnostic emitter, lexer scanner, AST structures, recursive-descent parser, name resolver, HIR lowering, LIR lowering, ABI lowering, instruction selection, frame layout, machine code encoder, COFF writer, PE linker, and CLI driver. [ADR-0005 §8]

---

## 2. Language & Standard Library Feature Audit

### 2.1 Audit Summary
The complete self-host subset defined in `spec/SPEC-00-bootstrap.md` §9 and tabulated in `spec/selfhost-subset.tsv` comprises 72 normative feature items.
Phase 9 Gate (`T075`) successfully certified that:
1. **Core Language Features**: Primitives, arithmetic with overflow detection, control flow (`if`, `while`, `loop`, `for`), functions, structs, tuples, arrays, slices, enums, match expressions, pattern matching (literal ranges, or-patterns, destructuring), `Option`, `Result`, ownership move/copy, definite initialization, `view`/`mut_view` capabilities, deterministic drops, methods, generics with monomorphization, traits with static dispatch, closures, const items and `.rdata` tables, minimal raw pointers with `unsafe` blocks, and FFI DLL imports are 100% operational in both interpreter and native modes.
2. **Standard Library Subset**: `Box<T>`, `Vec<T>`, stable `sort`, `Str`, `String`, `StringBuilder`, UTF-8/UTF-16 conversions, integer parsing/formatting, `ByteBuf` little-endian binary writers, `HashMap`/`HashSet` (preserving insertion order with deterministic 64-bit hashing), `Arena`, `TypedId`, `IdTable`, `Interner`, console/file I/O, process environment and args, file system operations, and monotonic clock (`Instant`) pass all unit tests, standard conformance suites, and real-world programs (word counter, lexer tokenizer, JSON parser, expression evaluator, sorting benchmark).
3. **Audit Outcome**: Zero language or standard library gaps exist for Phase 10. No gap tasks are required before initiating the compiler port.

### 2.2 Feature Consumption Map for `axiomc`
| Language / Std Feature | Primary Compiler Modules Consuming It |
|---|---|
| `F-INT`, `F-ARITH`, `F-DIVREM`, `F-BITS`, `F-CMP` | All modules (offsets, alignments, bit flags, hashing, counters) |
| `F-LET`, `F-MUT`, `F-CF`, `F-CFV`, `F-CFV.LABEL` | Scanner, parser, worklists, CFG traversals, register allocation |
| `F-STRUCT`, `F-STRUCT.TUPLE`, `F-ARRAY`, `F-SLICE` | AST/HIR/MIR/LIR node records, token tables, encoder buffers |
| `F-ENUM`, `F-PATTERN`, `F-PATTERN.LIT` | Token kinds, node variants, type kinds, match expressions, instruction opcodes |
| `F-OPTRES` (`?` operator) | Fallible parsing, type lookup, name resolution, file I/O |
| `F-STR`, `F-STD-TEXT` (`String`, `Str`) | Identifier storage, symbol text, diagnostic message generation |
| `F-MOVE`, `F-INIT`, `F-VIEW`, `F-DROP` | Zero-copy AST/HIR node passing, memory management without GC |
| `F-STD-ALLOC` (`Vec<T>`, `Box<T>`) | Dynamic arrays for AST children, basic blocks, instructions, relocations |
| `F-STD-COLL` (`HashMap<K, V>`) | Symbol resolution tables, interners, interned type caches |
| `F-STD-ARENA` (`Arena`, `IdTable`, `Interner`) | Fast per-compilation-phase allocation, DefId/NodeId/TypeId indices |
| `F-CONST` (constant tables in `.rdata`) | Keyword tables, x64 opcode tables, diagnostic code descriptions |
| `F-STD-TEXT.BYTEBUF` | COFF section binary emission, PE header and section writing |
| `F-STD-OS.IO`, `F-STD-OS.FS` | Reading source files, writing output object and executable files |
| `F-STD-OS.PROCESS`, `F-STD-OS.CLOCK` | CLI argument parsing, compilation timing (`--time-passes`) |

---

## 3. Canonical `compiler/` Source Layout

**AXS-SELF-013 — Canonical Directory Tree.** The Axiom self-hosting compiler source tree is organized into the following canonical layout:

```
compiler/
├── main.ax                     # Entry point for axiomc executable
├── kernel/                     # Core compiler data structures & utilities
│   ├── mod.ax
│   ├── arena.ax                # Arena allocator for compiler passes
│   ├── interner.ax             # Symbol and identifier string interning
│   ├── hash.ax                 # Deterministic 64-bit compiler hashing
│   ├── dynarray.ax             # Growable dense array structures
│   └── id.ax                   # Type-safe ID wrappers and ID maps
├── source/                     # Source text management and span tracking
│   ├── mod.ax
│   ├── span.ax                 # Source span representation and byte offsets
│   └── manager.ax              # File loader, line index, and source database
├── diag/                       # Compiler diagnostic reporting
│   ├── mod.ax
│   ├── code.ax                 # Diagnostic code definitions (AX_*)
│   ├── emitter.ax              # Diagnostic reporting pipeline and error sink
│   ├── format.ax               # Terminal span highlighter and text formatter
│   └── json.ax                 # Machine-readable JSON diagnostic output
├── lex/                        # Lexical scanner
│   ├── mod.ax
│   ├── token.ax                # Token kinds, keyword tables, literal kinds
│   └── scanner.ax              # UTF-8 lexical scanner and literal decoders
├── syntax/                     # Syntax analysis and AST
│   ├── mod.ax
│   ├── ast.ax                  # AST node definitions, visitor traits
│   └── parse.ax                # Recursive-descent & Pratt expression parser
├── resolve/                    # Name and module resolution
│   ├── mod.ax
│   ├── rib.ax                  # Lexical scoping ribs and name environments
│   ├── symtab.ax               # Symbol tables and def ID allocations
│   └── resolver.ax             # Name resolution, multi-file imports, visibility
├── hir/                        # High-level Intermediate Representation
│   ├── mod.ax
│   ├── hir.ax                  # HIR node definitions and types
│   └── lower.ax                # AST -> HIR lowering, pattern expansion
├── types/                      # Type system and checking
│   ├── mod.ax
│   ├── types.ax                # TypeKind, TypeId, and type interner
│   ├── layout.ax               # Target-independent struct/enum/tuple layout
│   └── typeck.ax               # Bidirectional type inference & checking
├── traits/                     # Trait system & monomorphization
│   ├── mod.ax
│   ├── solver.ax               # Trait obligation resolution
│   └── mono.ax                 # Monomorphization engine and instance cache
├── own/                        # Ownership, initialization & capability analysis
│   ├── mod.ax
│   ├── move.ax                 # Move/copy classification & use-after-move
│   ├── init.ax                 # Definite initialization analysis
│   └── cap.ax                  # View and mut_view capability conflict tracking
├── mir/                        # Mid-level Intermediate Representation
│   ├── mod.ax
│   ├── mir.ax                  # Control-flow graph, basic blocks, operands
│   ├── builder.ax              # HIR -> MIR lowering
│   └── drop.ax                 # Deterministic drop elaboration and cleanup
├── verify/                     # MIR structural and semantic verifier
│   ├── mod.ax
│   └── verifier.ax             # CFG, type, and capability validation
├── interp/                     # MIR interpreter and const evaluator
│   ├── mod.ax
│   ├── value.ax                # Runtime value representations
│   ├── frame.ax                # Stack frame and local allocation
│   ├── oracle.ax               # Host interface emulation
│   └── interp.ax               # Step execution engine
├── opt/                        # MIR optimizations
│   ├── mod.ax
│   ├── const_fold.ax           # Constant folding
│   ├── dce.ax                  # Dead code elimination
│   └── cfg_simp.ax             # CFG branch and block simplification
├── lir/                        # Low-level Intermediate Representation
│   ├── mod.ax
│   ├── lir.ax                  # Virtual register instruction model
│   └── builder.ax              # MIR -> LIR instruction selector
├── abi/                        # ABI lowering
│   ├── mod.ax
│   └── win64.ax                # Windows x64 calling conventions and shadow space
├── target/                     # Target-specific code generation
│   ├── mod.ax
│   └── x64/
│       ├── mod.ax
│       ├── isel.ax             # LIR -> x86-64 machine instruction selection
│       ├── frame.ax            # Prologue/epilogue and stack frame lowering
│       ├── reg.ax              # Register allocation and clobber sets
│       └── encode.ax           # Machine code binary encoding (REX, ModRM, SIB)
├── obj/                        # Object file formatting
│   ├── mod.ax
│   ├── coff.ax                 # COFF header and relocation model
│   └── writer.ax               # COFF relocatable object emitter (.obj)
├── link/                       # Linker and executable generation
│   ├── mod.ax
│   ├── pe.ax                   # PE32+ header and section headers
│   ├── import.ax               # Import address table and kernel32 bindings
│   └── linker.ax               # In-memory PE linker and image builder (.exe)
└── driver/                     # Driver and pipeline orchestration
    ├── mod.ax
    ├── opts.ax                 # CLI flag parsing
    └── pipeline.ax             # Driver pipeline, inspect emitters, file I/O
```

---

## 4. Module-by-Module Port Specifications (T077–T085)

### 4.1 Group T077 — Kernel, Source DB, Diagnostics
- **Integration Task**: `T077` (Port kernel, source DB, diagnostics to Axiom). Depends on `[T077a, T077b, T077c]`.
  - Artefact: Diagnostic text output, `--json` formatted errors, interner token identity.
  - Harness: `tests/selfhost/kernel_source_diag`.
- **Sub-tasks**:
  1. `T077a`: **Port kernel to Axiom** (arena, interner, hashtable, dynarray, idtable).
     - Paths: `[compiler/kernel, tests/selfhost/kernel]`.
     - Model: `sonnet`. Size budget: ~1,200 LOC.
     - Differential: Verify arena allocation invariants, hash collisions, and interner string pooling.
  2. `T077b`: **Port source DB to Axiom** (source manager, span decoding, line/col lookup).
     - Paths: `[compiler/source, tests/selfhost/source]`.
     - Model: `sonnet`. Size budget: ~400 LOC.
     - Differential: Byte offset to line/column calculation identical to `axiom0`.
  3. `T077c`: **Port diagnostics emitter to Axiom** (codes, formatters, json).
     - Paths: `[compiler/diag, tests/selfhost/diag]`.
     - Model: `sonnet`. Size budget: ~900 LOC.
     - Differential: Output byte-identical text and JSON diagnostics across test suite.

### 4.2 Group T078 — Lexer
- **Integration Task**: `T078` (Port lexer to Axiom — differential tokens). Depends on `[T078a]`.
  - Artefact: Token stream dump via `inspect --emit=tokens`.
  - Harness: `tests/selfhost/lexer`.
- **Sub-tasks**:
  1. `T078a`: **Port lexer scanner to Axiom** (UTF-8, tokens, literals).
     - Paths: `[compiler/lex, tests/selfhost/lex]`.
     - Model: `sonnet`. Size budget: ~1,200 LOC.
     - Differential: Compare token kind, span, and literal values against `axiom0 inspect --emit=tokens`.

### 4.3 Group T079 — Parser & AST
- **Integration Task**: `T079` (Port parser + AST to Axiom — differential AST). Depends on `[T079a, T079b]`.
  - Artefact: AST S-expression dump via `inspect --emit=ast`.
  - Harness: `tests/selfhost/parser`.
- **Sub-tasks**:
  1. `T079a`: **Port AST data structures & visitor to Axiom**.
     - Paths: `[compiler/syntax/ast.ax, tests/selfhost/ast]`.
     - Model: `sonnet`. Size budget: ~900 LOC.
     - Differential: Verify AST node serialization and traversal order.
  2. `T079b`: **Port recursive-descent parser to Axiom**.
     - Paths: `[compiler/syntax/parse.ax, tests/selfhost/parse]`.
     - Model: `sonnet`. Size budget: ~1,500 LOC.
     - Differential: AST tree matches `axiom0 inspect --emit=ast` for all syntax test cases.

### 4.4 Group T080 — Resolver & HIR
- **Integration Task**: `T080` (Port resolver + HIR to Axiom). Depends on `[T080a, T080b]`.
  - Artefact: HIR dump via `inspect --emit=hir`.
  - Harness: `tests/selfhost/resolve_hir`.
- **Sub-tasks**:
  1. `T080a`: **Port resolver and module graph to Axiom** (scoping, rib stack, imports).
     - Paths: `[compiler/resolve, tests/selfhost/resolve]`.
     - Model: `sonnet`. Size budget: ~1,400 LOC.
     - Differential: Identical symbol resolution and visibility rejection diagnostics.
  2. `T080b`: **Port HIR data model and lowering to Axiom**.
     - Paths: `[compiler/hir, tests/selfhost/hir]`.
     - Model: `sonnet`. Size budget: ~1,400 LOC.
     - Differential: HIR node structure matches `axiom0 inspect --emit=hir`.

### 4.5 Group T081 — Types, Traits & Typeck
- **Integration Task**: `T081` (Port typeck + trait solver to Axiom). Depends on `[T081a, T081b, T081c]`.
  - Artefact: Typed HIR dump via `inspect --emit=thir` and typeck diagnostics.
  - Harness: `tests/selfhost/typeck_traits`.
- **Sub-tasks**:
  1. `T081a`: **Port types data model, interner & layout to Axiom**.
     - Paths: `[compiler/types/types.ax, compiler/types/layout.ax, tests/selfhost/types]`.
     - Model: `opus`. Size budget: ~1,200 LOC.
     - Differential: Type layout, field offsets, and alignments match target specification.
  2. `T081b`: **Port trait solver & monomorphization engine to Axiom**.
     - Paths: `[compiler/traits, tests/selfhost/traits]`.
     - Model: `opus`. Size budget: ~800 LOC.
     - Differential: Static dispatch resolution and monomorphized instance sets agree.
  3. `T081c`: **Port type checker and inference engine to Axiom**.
     - Paths: `[compiler/types/typeck.ax, tests/selfhost/typeck]`.
     - Model: `opus`. Size budget: ~1,500 LOC.
     - Differential: Type inference, unification, and diagnostic error codes match `axiom0`.

### 4.6 Group T082 — Ownership, MIR Builder, Drop, Verifier
- **Integration Task**: `T082` (Port ownership, MIR builder, drop, verifier to Axiom). Depends on `[T082a, T082b, T082c, T082d, T082e]`.
  - Artefact: Elaborated MIR dump via `inspect --emit=mir`.
  - Harness: `tests/selfhost/own_mir_verify`.
- **Sub-tasks**:
  1. `T082a`: **Port MIR data model and MIR builder to Axiom**.
     - Paths: `[compiler/mir/mir.ax, compiler/mir/builder.ax, tests/selfhost/mir]`.
     - Model: `opus`. Size budget: ~1,500 LOC.
     - Differential: Control flow graphs, basic blocks, and statements match `axiom0`.
  2. `T082b`: **Port ownership move analysis and definite initialization to Axiom**.
     - Paths: `[compiler/own/move.ax, compiler/own/init.ax, tests/selfhost/own]`.
     - Model: `opus`. Size budget: ~1,100 LOC.
     - Differential: Move/copy tracking, borrow errors, and use-after-move diagnostics match.
  3. `T082c`: **Port capability analysis to Axiom** (`view` / `mut_view`).
     - Paths: `[compiler/own/cap.ax, tests/selfhost/cap]`.
     - Model: `opus`. Size budget: ~700 LOC.
     - Differential: Capability conflicts and aliasing violations match `axiom0`.
  4. `T082d`: **Port drop elaboration and cleanup edges to Axiom**.
     - Paths: `[compiler/mir/drop.ax, tests/selfhost/drop]`.
     - Model: `opus`. Size budget: ~1,100 LOC.
     - Differential: Generated drop flags, drop calls, and cleanup blocks match `axiom0`.
  5. `T082e`: **Port MIR verifier to Axiom**.
     - Paths: `[compiler/verify, tests/selfhost/verify]`.
     - Model: `opus`. Size budget: ~700 LOC.
     - Differential: Verifier accepts valid MIR and rejects malformed IR identically.

### 4.7 Group T083 — Interpreter & Optimizer
- **Integration Task**: `T083` (Port interpreter + optimizer to Axiom). Depends on `[T083a, T083b]`.
  - Artefact: Interpreter execution results and optimized MIR via `inspect --emit=mir-opt`.
  - Harness: `tests/selfhost/interp_opt`.
- **Sub-tasks**:
  1. `T083a`: **Port MIR interpreter and host oracle to Axiom**.
     - Paths: `[compiler/interp, tests/selfhost/interp]`.
     - Model: `opus`. Size budget: ~1,500 LOC.
     - Differential: Program exit codes, terminal output, and panic messages match `axiom0` in interp mode.
  2. `T083b`: **Port MIR optimizer (-O1 const folding, DCE, CFG simplify) to Axiom**.
     - Paths: `[compiler/opt, tests/selfhost/opt]`.
     - Model: `opus`. Size budget: ~500 LOC.
     - Differential: Constant propagation, dead code elimination, and block merging match `axiom0`.

### 4.8 Group T084 — LIR, ABI, x64 Backend & Encoder
- **Integration Task**: `T084` (Port LIR + x64 backend + encoder to Axiom). Depends on `[T084a, T084b, T084c, T084d]`.
  - Artefact: LIR instruction dump via `inspect --emit=lir` and encoded machine code bytes.
  - Harness: `tests/selfhost/backend`.
- **Sub-tasks**:
  1. `T084a`: **Port LIR data model and builder to Axiom**.
     - Paths: `[compiler/lir, tests/selfhost/lir]`.
     - Model: `sonnet`. Size budget: ~1,500 LOC.
     - Differential: LIR virtual register instructions match `axiom0 inspect --emit=lir`.
  2. `T084b`: **Port Windows x64 ABI lowering to Axiom**.
     - Paths: `[compiler/abi, tests/selfhost/abi]`.
     - Model: `sonnet`. Size budget: ~300 LOC.
     - Differential: Register assignment (RCX/RDX/R8/R9) and shadow space layout match.
  3. `T084c`: **Port x64 instruction selection and frame lowering to Axiom**.
     - Paths: `[compiler/target/x64/isel.ax, compiler/target/x64/frame.ax, tests/selfhost/isel]`.
     - Model: `sonnet`. Size budget: ~1,100 LOC.
     - Differential: Generated machine instructions, stack allocations, and epilogues match.
  4. `T084d`: **Port x64 machine code encoder to Axiom**.
     - Paths: `[compiler/target/x64/encode.ax, tests/selfhost/encode]`.
     - Model: `sonnet`. Size budget: ~1,400 LOC.
     - Differential: Encoded opcode bytes, REX prefixes, and ModRM bytes match byte-for-byte.

### 4.9 Group T085 — COFF Writer, PE Linker & Driver
- **Integration Task**: `T085` (Port COFF writer, PE linker, driver -> axiomc). Depends on `[T085a, T085b, T085c]`.
  - Artefact: Relocatable COFF object (`--emit=obj`) and PE32+ executable (`--emit=exe`).
  - Harness: `tests/selfhost/obj_link_driver`.
- **Sub-tasks**:
  1. `T085a`: **Port COFF object writer & object model to Axiom**.
     - Paths: `[compiler/obj, tests/selfhost/obj]`.
     - Model: `sonnet`. Size budget: ~500 LOC.
     - Differential: Emitted `.obj` file headers, sections, and relocations match `axiom0` byte-for-byte.
  2. `T085b`: **Port PE32+ linker to Axiom**.
     - Paths: `[compiler/link, tests/selfhost/link]`.
     - Model: `sonnet`. Size budget: ~1,000 LOC.
     - Differential: Linked executable headers, IAT, section alignments, and RVAs match `axiom0`.
  3. `T085c`: **Port compiler driver & pipeline CLI to Axiom**.
     - Paths: `[compiler/driver, tests/selfhost/driver]`.
     - Model: `sonnet`. Size budget: ~1,500 LOC.
     - Differential: CLI command handling (`build`, `check`, `inspect`), return codes, and output files match.

---

## 5. Differential Verification Strategy

**AXS-SELF-006 — Precise Artefact Alignment.** Each port module is verified by comparing its intermediate or final output against the corresponding output of `axiom0` on identical input files. Differential testing operates at multiple tiers:

| Compilation Stage | Verification Artefact | Inspection CLI Command | Target Match |
|---|---|---|---|
| Tokenizer / Scanner | Token kind, span, text, literals | `axiom0 inspect --emit=tokens <file>` | Structural equality |
| AST | AST S-expression dump | `axiom0 inspect --emit=ast <file>` | Structural equality |
| HIR | Desugared High-level IR dump | `axiom0 inspect --emit=hir <file>` | Structural equality |
| THIR / Typeck | Type-annotated HIR & types | `axiom0 inspect --emit=thir <file>` | Structural equality |
| MIR | Unoptimized & Elaborated MIR | `axiom0 inspect --emit=mir <file>` | Block & statement isomorphism |
| Optimizer | Optimized MIR | `axiom0 inspect --emit=mir-opt <file>` | Block & statement isomorphism |
| Interpreter | Exit code, stdout, stderr | `axiom0 run --backend=interp <file>` | Byte-exact output |
| LIR | Low-level IR instruction stream | `axiom0 inspect --emit=lir <file>` | Virtual register stream match |
| Object Writer | Relocatable COFF object | `axiom0 build --emit=obj <file>` | Byte-exact binary equality |
| Linker | PE32+ Executable binary | `axiom0 build <file>` | Functionally & structurally identical |

---

## 6. Multi-Stage Bootstrap Ladder & Resource Budgets

### 6.1 Bootstrap Stages
The complete self-hosting pipeline proceeds through four distinct stages:
1. **Stage 0 (`axiom0`)**: The C11 bootstrap compiler built by GCC/Clang.
2. **Stage 1 (`axiomc1`)**: The Axiom compiler built by `axiom0` from `compiler/main.ax`.
   - Command: `python tools/bootstrap.py --stage 1` (or `axiom0 build compiler/main.ax -o build/axiomc1.exe -O1 --stack-reserve 67108864`).
3. **Stage 2 (`axiomc2`)**: The Axiom compiler built by `axiomc1` compiling its own sources.
   - Command: `build/axiomc1.exe build compiler/main.ax -o build/axiomc2.exe -O1 --stack-reserve 67108864`.
4. **Stage 3 (`axiomc3`)**: The Axiom compiler built by `axiomc2`.
   - Command: `build/axiomc2.exe build compiler/main.ax -o build/axiomc3.exe -O1 --stack-reserve 67108864`.

### 6.2 Resource Budgets (T086 & T087)
**AXS-SELF-009 — Compile-Time and Memory Budget.** The self-compilation stages must adhere strictly to the following resource limits when executed on the reference development environment:

| Transition | Compiler Flags | Wall Clock Time Limit | Peak Memory Limit (RAM) | Acceptance Gate |
|---|---|---|---|---|
| `axiom0` -> `axiomc1` | `-O1 --stack-reserve 67108864` | **< 2 minutes** | **< 2.0 GB** | T086 |
| `axiomc1` -> `axiomc2` | `-O1 --stack-reserve 67108864` | **< 10 minutes** | **< 4.0 GB** | T086 |
| `axiomc2` -> `axiomc3` | `-O1 --stack-reserve 67108864` | **< 10 minutes** | **< 4.0 GB** | T087 |

**Contingency (ADR-0005 §7)**: If Stage-1 compilation (`axiomc1` self-compile) exceeds 10 minutes or 4 GB RAM due to excessive stack frame overhead or lack of register allocation, the architect will pull in a minimal linear-scan slice of E15.8 (scope of T063) into `axiom0` before T087 as an explicit, conditional exception to ROADMAP R7.

### 6.3 Fixed Point & Reproducibility Contract (T087)
**AXS-SELF-010 — Deterministic Fixed Point.**
- `axiomc2.exe` and `axiomc3.exe` must be **100% bitwise identical**.
- Building `axiomc` in two separate directory trees must produce bitwise identical binaries (independent of path strings or build timestamps).
- The entire Stage-2 and Stage-3 bootstrap process must execute with `gcc`, `as`, and `ld` removed from `PATH`.

---

## 7. Freeze Protocol & Maintenance Rules

**AXS-SELF-011 — axiom0 Freeze Rule.**
1. Upon acceptance of T087, the Git tag `axiom0-frozen` is created locally.
2. From that point forward, `tools/harness_check.py` rejects any commit that touches `bootstrap/axiom0/` unless the commit message specifically references an authorized `AX0-FIX-<nn>` task ID.
3. All new compiler features, optimizations, bug fixes, and targets from Phase 11 onward are implemented exclusively in `compiler/` and `std/`.
4. `tools/build_axiomc.py` becomes the standard build driver for developing the compiler in subsequent phases.

---

## 8. Post-Self-Host Tasks Re-Pathing

**AXS-SELF-012 — Re-pathing to `compiler/`.** The following tasks scheduled for Phase 11+ are re-pathed from `bootstrap/axiom0/src/` to the canonical `compiler/` directory layout:

| Task ID | Title | Previous / Provisional Paths | Canonical Re-Pathed Paths |
|---|---|---|---|
| `T058` | dyn Trait: vtables and dynamic dispatch | `[compiler/traits/dyn, compiler/mir, compiler/interp, ...]` | `[compiler/traits, compiler/mir, compiler/interp, tests/run/dyn, tests/ui/dyn]` |
| `T063` | Linear-scan register allocation | `[compiler/target/x64/regalloc, ...]` | `[compiler/target/x64, tests/mc/regalloc]` |
| `T064` | Optimizer ladder 2: copy prop, inlining | `[compiler/opt, tests/opt2]` | `[compiler/opt, tests/opt2]` |
| `T066` | Linux x86-64: SysV ABI, ELF64 | `[compiler/abi/sysv, compiler/obj/elf, ...]` | `[compiler/abi, compiler/obj, compiler/link, tests/run/linux]` |
| `T067` | Linker v2: separate compilation | `[compiler/link, compiler/driver, tests/link2]` | `[compiler/link, compiler/driver, tests/link2]` |
| `T068` | Windows unwind info (.pdata/.xdata) | `[compiler/target/x64/unwind, ...]` | `[compiler/target/x64, compiler/link, tests/run/unwind]` |
| `T750` | Static libraries: COFF archive (.lib) | `[compiler/obj/archive, compiler/link/archive, ...]` | `[compiler/obj, compiler/link, compiler/driver, tests/link/lib]` |
| `T751` | PE DLL output & import library | `[compiler/link/pe_dll, compiler/link/implib, ...]` | `[compiler/link, tests/link/dll]` |

---

## Sources
0263 §4-12, §20-45, §49-51; tasks/0260 §3-4, §41, §44, ABOOT-41..80; tasks/0261; tasks/0371; tasks/0473;
0167; 0150; 0152 §80-81; 0181 §15-16, §31, §38-42; ROADMAP R1-R9;
ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0007, ADR-0011, ADR-0012, ADR-0013.
