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
`BOOT` bootstrap scope, `LEX` / `GRM` invariants already stated in SPEC-01 / SPEC-02. A new group is
added by editing this list.

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
- statement: Every program goes Source → Lexer → Parser → AST → Resolver → HIR → Typeck → THIR → ownership/capability → MIR (+ drop elaboration) → Verifier → {Interpreter | Optimizer → LIR → machine IR → Encoder → Object → Linker}. No stage is skipped, no machine code is generated from AST or HIR, and there is no textual assembly in the production path.
- source: 0152 (pipeline); 0263 §28; ABOOT-46; skill axiom-spec-index
- verify: tools/archcheck.py
- since: T006
- check: enforced structurally through INV-LAYER-005; driver stage list in `driver/pipeline.c` (T016)

### INV-PIPE-002 — Verified MIR is the checkpoint
- statement: The interpreter, the optimizer and MIR-to-LIR lowering consume only MIR that passed the verifier in the same compilation. The driver refuses to go on with unverified MIR.
- source: 0153 APASS-23; tasks/0260 ABOOT-47; T020; T050
- verify: tests/verify
- since: T020
- check: hand-written invalid MIR is rejected with `AX_VERIFY_*` and never executed

### INV-PIPE-003 — The verifier does not trust the analyses
- statement: The verifier re-checks move, drop and view invariants on the MIR itself and does not rely on the results of the analyses that produced it.
- source: T050; 0027; 0029
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
- since: T046
- check: ui tests for use after move, partial move and Copy types

### INV-SEM-002 — Capability conflicts are compile errors
- statement: A `mut_view` that overlaps any other live view of the same region is rejected, and so is an overlap the compiler cannot prove absent. Validity of capabilities does not depend on the optimization level.
- source: 0151 §5-6 (ACAP-31); tasks/0360 §14-15; 0177
- verify: tests/ui/cap
- since: T048
- check: ui tests WRITE+WRITE, WRITE+READ and unknown overlap; run tests stay identical at -O0/-O1

### INV-SEM-003 — Deterministic drop
- statement: Owned values are dropped exactly once, at the end of their scope in reverse declaration order, never after being moved out. Conditional moves use drop flags. Drop never depends on a garbage collector or on reference counting.
- source: 0151 §1, §8; 0178; tasks/0262 §26-27; tasks/0260 ABOOT-50/51
- verify: tests/run/drop
- since: T049
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

## Sources
0153 §37 (ACKERNEL, ASOURCE, AINTERN, AQUERY, APAR, ADIAG-20..24, APASS, ACACHE, ADET); 0171 §40
(AKERNEL-24..37); 0172 §1-§24; tasks/0260 §45 (ABOOT-41..80); tasks/0262 §42-§49; tasks/0360 §51
(ADIAG-20..90); 0146 §50-§58; 0151 §1-§25, §56-§57; 0263 §28, §46-§47; ROADMAP R3, R6–R8; ADR-0002;
ADR-0003; ADR-0004 §2, §4, §8; ADR-0005 §2, §15; ADR-0011; SPEC-01 §11; SPEC-02 §10; axiom-c-stage0.
Not catalogued here because they belong to later architecture (E18.1 query engine, E18.2 caches):
0153 AQUERY-21..25, ACACHE-20..24, ACKERNEL-22, 0171 AKERNEL-31..33. They are added when E18 is
planned (T218).
