# Audit A1 — Self-host feasibility

## Summary
Checked: T076–T087 against every P0–P9 task (scope, `depends`, `paths`), by writing out axiomc module by module (kernel → driver) and matching each needed language feature / std API to the task that delivers it and its native catch-up.
Also checked: scale risks when axiom0 compiles a 50–100k line program, and the differential / fixed-point plan.
Counts: BLOCKER 2 (1 CONFIRMED, 1 PLAUSIBLE), MAJOR 9, MINOR 4.
Main risks: (1) the MIR interpreter cannot run any program that uses the heap or OS I/O, yet every P9/P10 acceptance line says "interp + native"; (2) no stack probing, and naive stack-slot frames on the 1 MB default stack; (3) several std tasks can start before the language features they use exist (closures, raw pointers, generics, hashing).

## Findings

### A1-01 [BLOCKER] [CONFIRMED] The MIR interpreter has no way to run heap allocation or OS calls, so no std-based program can run in interp mode
- Where: T065 §Scope + `paths` (abi, link, types/ffi — no `interp`); T070 §Scope ("Windows heap backend via FFI"); T074 §Scope (CreateFileW, WriteFile, … via FFI); T021 §Scope (value model, no host calls); T061a §Scope (interp memory = abstract (alloc id, offset)). The acceptance lines that require interp: T069 ("interp + native"), T073a ("in interp and native mode"), T075 ("All programs pass both modes"), T077–T085 ("module tests pass in interp and native"); axiom-testing SKILL.md:35 (run tests default to both modes); T029 (differential for every run test).
- Problem: Box/Vec/String/HashMap/Arena get memory from HeapAlloc through FFI. std.io/fs/env go through kernel32/shell32 through FFI. No task gives the interpreter a way to run an `extern` call: there is no host-call bridge and no allocation or I/O intrinsics. The interp pointer model (abstract alloc ids) also cannot hand a buffer to WriteFile. `ptr as usize` alignment arithmetic in arenas (T073a) is also unspecified for abstract pointers.
- Consequence if not fixed: T070 cannot pass its tests in interp mode, and the same goes for T071–T075, T073a and every port task T077–T085. Either these tasks block, or they fall back to `// modes: native`. That fallback silently drops the semantic oracle (the three-compiler test, tasks/0260 §42) for all real programs, including axiomc itself, just when the oracle matters most.
- Proposed fix: extend T061a (or add a T061b before T065, with paths `interp/`, `mir/`, `lir/`, `target/x64`) with a small **host-interface intrinsic set**. std's Windows backends call it, and both interp and native implement it: `heap_alloc/heap_realloc/heap_free`, `write_fd`, `read_file`/`write_file` (or open/read/write/close handles), `args`, `env_get`, `exit`, `monotonic_ns`, `dir_list`. Native lowers these to the kernel32 imports; interp implements them in C over its memory model. Direct FFI remains for user code and runs native-only. The alternative is an interp FFI bridge, which is feasible because Win64 with no floats passes everything as u64 registers or stack slots. It needs marshalling of interp allocations to real memory, and axiomc would have to port it in T083. ROADMAP R8 ("C provides only compiler intrinsics and FFI to the OS") allows either option. This is an architect decision (SPEC-04), not an owner decision. T070/T074 then depend on it.

### A1-02 [BLOCKER] [PLAUSIBLE] No stack probes and a 1 MB stack: axiomc built by axiom0 is likely to crash on large frames or deep recursion
- Where: T023 §Scope ("every MIR local → stack slot"); T025 §Scope (fixed-register baseline, prologue/epilogue, no probe); T027 (no stack-size option); .claude/skills/axiom-x64-backend/references/pe-coff.md:71 (`SizeOfStackReserve 0x100000, SizeOfStackCommit 0x1000`); docs 0188 §12 lines 300–334 (frames larger than one page must be probed with `__chkstk`); T068 (unwind) deferred to E17.3; T063 (regalloc) deferred to E15.8.
- Problem: naive lowering gives every MIR temp its own slot with no reuse. In axiomc functions such as the parser's `parse_expr`, the isel/encoder `match` over hundreds of opcodes, and the diagnostic code tables, frames will exceed 4 KB. On Windows, an access below the guard page without sequential probing is an access violation. No task implements a probe or chkstk loop. Separately, recursive-descent parse, typeck and MIR build over long left-associated operator chains or else-if ladders, with fat naive frames, can exhaust the default 1 MB reserve. The recursion-depth test in T033 does not cover this.
- Consequence if not fixed: axiomc1 crashes with 0xC0000005 or 0xC00000FD in T084–T086, with no backtrace (no .pdata). Diagnosing this at the self-host gate is costly.
- Proposed fix: add to T025 §Scope: "frames > 4096 bytes emit an inline stack-probe loop (touch each page before `sub rsp`; no CRT `__chkstk`); run test with an 64 KB local array". Add to T027: "`--stack-reserve` linker/driver option; default stays 1 MB; tools/bootstrap.py (T086) builds axiomc with ≥ 64 MB". Optionally, T023 reuses slots of dead temps per block. That is simple and stays within R7.

### A1-03 [MAJOR] [CONFIRMED] std tasks depend on too little: they can start before closures, raw pointers and hashing exist
- Where: T069 `depends: [T056, T060]` but §Scope has Option/Result combinators (need closures: T057, native T059) and `mem.swap/replace/take`, `size_of/align_of` (need T061a intrinsics). T070 `depends: [T069, T065, T061a]` but §Scope has `sort_by`/`sort_by_key` (closures: T057/T059). T073a `depends: [T070]` but §Scope has "`Interner<T>` … with deterministic hashing from T073". ROADMAP changelog line 331 ("T069 → T056+T060") shows the R8 relaxation went too far.
- Problem: none of T057, T059, T061a is in T069's transitive closure, T059 is not in T070's, and T073 is not in T073a's. The autopilot's `start` checks dependencies, so it can start these tasks as soon as their listed deps are done.
- Consequence if not fixed: T069, T070 and T073a start early and then block, or ship partial APIs (combinators missing, sort without key closures, an interner with an ad-hoc hash). That is rework before T075.
- Proposed fix: T069 depends += T059, T061a; T070 depends += T059; T073a depends += T073. This does not delay the critical path: T075 already waits for all of them.

### A1-04 [MAJOR] [CONFIRMED] T061a's generic intrinsics come before generics
- Where: T061a `depends: [T051]`; §Scope `size_of<T>()`, `align_of<T>()`, `ptr_copy`, `ptr_copy_nonoverlapping` (generic over T); generics are T054 (`depends: [T053]` → T052 → T051).
- Problem: T061a can run in parallel with T052–T054. Its intrinsics are generic functions whose type-argument checking and instantiation belong to T054.
- Consequence if not fixed: T061a has to special-case generic intrinsic calls in C, which is throw-away work under R7, or block until T054.
- Proposed fix: T061a depends += T054. T062/T065/T070 already come after it, so nothing downstream moves.

### A1-05 [MAJOR] [CONFIRMED] No task parses or resolves `extern` declarations; T065's paths cannot reach syntax/resolve/hir/mir
- Where: T011 §Scope item list (fn, struct, enum, type alias, const, static, use, module — no `extern`); T012 §Scope (no extern blocks and no `unsafe fn` modifier); T065 `paths: [abi, link, types/ffi, tests…]`; T001 line 25 mentions `extern fn` only for `@at`.
- Problem: `extern "system" fn …` items, the `@link("kernel32")` attribute binding, HIR/THIR for foreign functions and MIR calls to imported symbols are not in any task's scope or paths. The same applies to `unsafe fn` on the parser/HIR side (T061a's paths also lack syntax, mir and lir, although its acceptance requires native tests).
- Consequence if not fixed: T065 cannot be done inside its declared paths, so it runs over its paths or blocks. That also blocks T070/T074, so the whole self-host std depends on it.
- Proposed fix: add `extern` item and `unsafe fn` parsing to T012 §Scope (the AST is already meant to cover the whole grammar, per T011). Extend T065 `paths` with `resolve`, `hir`, `mir`, `lir`, `target/x64`. Extend T061a `paths` with `mir`, `lir`, `target/x64/isel`.

### A1-06 [MAJOR] [CONFIRMED] Wrapping and bit intrinsics have no compiler-side owner, yet hashing and hash-parity depend on them
- Where: T069 §Scope "wrapping_*" (paths `std/core` only); T034 §Scope (checked arithmetic only); T061a intrinsic list (no wrapping ops); T007 §Scope "stable 64-bit hash (documented algorithm)"; T073 "deterministic hashing"; T054 "mangling deterministic".
- Problem: FNV/xxhash-style hashing in HashMap, the interner and mangling needs `wrapping_mul/add`, `rotate_left` and shifts that do not trap. With panic-on-overflow defaults (T034), a std method `wrapping_mul` must be a compiler intrinsic: a MIR op, interp semantics and native lowering without `jo`. No task with compiler paths implements one. axiomc must also reproduce axiom0's T007 hash bit-for-bit wherever hash values are observable (mangled names, ordering).
- Consequence if not fixed: T069 blocks, or someone writes wrapping arithmetic by 32-bit limb masking in Axiom. That is slow and easy to get wrong, and it risks differential divergence in T081/T084 (mangling).
- Proposed fix: add to T034 §Scope (paths already include types/mir/interp): "`@intrinsic` wrapping_add/sub/mul/neg, rotate_left/right, leading/trailing_zeros, count_ones for all integer widths (MIR ops without overflow assert)"; T037 covers the native side. Record in T003 SPEC-03 that the wrapping family is in the self-host subset (E12.1 completes saturating/i128 later).

### A1-07 [MAJOR] [CONFIRMED] Axiom's HashMap is not required to iterate in insertion order like axiom0's, which undermines byte-identical differential tests
- Where: T007 §Scope "HashMap (open addressing, deterministic iteration = insertion order)"; T073 §Scope "HashMap/HashSet with deterministic hashing" (no order contract); T073a "iteration in insertion order" (IdTable only); T077–T085 "keeping behaviour identical to the C implementation"; T084/T085 differential on bytes.
- Problem: a faithful port copies loops over maps. If axiom0's map iterates in insertion order and std's map iterates in hash-bucket order, symbol order, diagnostic order (where not sorted), import tables and so on differ.
- Consequence if not fixed: unexplained differential mismatches in T080–T085, or the port has to add sorts that axiom0 does not have.
- Proposed fix: T073 §Scope: "HashMap/HashSet iteration order = insertion order (index-map layout), identical to axiom0 kernel/hashmap; hash function = the T007 documented algorithm". Add a test that iterates after deletions.

### A1-08 [MAJOR] [PLAUSIBLE] Stored views (a view held in a struct field) are not scoped, yet iterators and compiler contexts need them
- Where: T048 §Scope ("view escape via return/store" appears only as a conflict check); docs tasks/0541 §96 "Explicit stored view" (struct field `data: view(x)`, lifetime = containing object); tasks/0270 ACAP-43; users: T072 (iteration over arrays/views), T073 (`Str.chars()`, `char_indices`, adapters that wrap iterators), T077–T080 (lexer over a source view; contexts referencing interners/SourceDb).
- Problem: if T048 only implements ephemeral views and rejects any view stored in a struct, `Chars { s: view<[u8]>, i: usize }` and the compiler's context structs cannot be written in safe code.
- Consequence if not fixed: iterators are rewritten on raw pointers in `unsafe`, or the compiler is forced into a pass-everything-as-parameter style. Either way, T072/T073 are reworked, or the port diverges from axiom0's context-struct design.
- Proposed fix: T048 §Scope + acceptance: "explicit stored views in struct fields per 0541 §96 / ACAP-43 (owner-outlives check, no self-reference); test: a slice iterator struct used in a loop, and rejection when the owner is moved/dropped while the struct is live". T045 must state the rule.

### A1-09 [MAJOR] [PLAUSIBLE] Drop glue for generic instances (Vec<T>, Box<T>, Option<Box<T>>) has no owner
- Where: T049 (drop elaboration; `depends` before generics); T054 §Scope (instances, MIR instantiation — no drops); T070 "drops elements"; T061a intrinsics (no `drop_in_place`/`needs_drop`).
- Problem: drop elaboration is built before generics exist. Nobody is assigned the post-monomorphization drop glue for generic types or user `impl<T> Drop for Vec<T>`, or the ability to drop a `T` behind a raw pointer.
- Consequence if not fixed: T070 leaks or double-frees (its leak counters fail), or blocks on a compiler change outside its paths (std only).
- Proposed fix: T054 §Scope: "drop elaboration/drop glue per monomorphized instance; generic `Drop` impls"; T061a: add `drop_in_place<T>` (and `needs_drop<T>` if SPEC-04 keeps it). The acceptance for both: `Vec<Box<i32>>` drop count test in interp and native.

### A1-10 [MAJOR] [PLAUSIBLE] Constant tables: nothing places const aggregates in .rdata, and `static` is parsed but never implemented
- Where: T061 §Scope and `paths` (interp, types/const only — no mir/lir/obj); T011 parses `static`, but no later task types or lowers it; tasks/0260 §39–40 (keyword, opcode, register, ABI and diagnostic-metadata tables in the compiler).
- Problem: axiomc needs large read-only tables: x64 opcode/ModRM tables, keyword table, the diagnostic code registry (axiom0's `codes.def` X-macro), ABI register tables. Say T061 evaluates a const into an interp value and inlines it at each use, which is the natural reading. Then either Str/pointer fields cannot be materialized (they need relocations), or each runtime index copies the whole table onto the stack. That copy makes A1-02 worse.
- Consequence if not fixed: T084/T085 port the tables as giant `match` functions or init-at-startup code. That is slower and has huge frames, and no task plans for it.
- Proposed fix: T061 §Scope + paths (+ `mir`, `lir`, `obj`): "const items of aggregate type (arrays of structs incl. `Str` fields) are emitted once to .rdata with relocations and indexed in place; the interp uses the same single allocation". The other option is immutable `static` items in the self-host subset. That needs an architect decision in T003a.

### A1-11 [MAJOR] [PLAUSIBLE] No scale test and no compile-time budget before T086
- Where: T044 (perf baseline of small benchmarks); T062 (fuzz of generated programs); T075 (real programs: word count, tokenizer, …; "perf recorded"); T086/T087 (first time a 50–100k line program is compiled as a single unit, since separate compilation T067 is deferred).
- Problem: any quadratic pass (resolver scope lookup, trait-solver cache, monomorphization worklist, linker symbol lookup, diagnostics sort), recursion in axiom0's own C code on deep ASTs, or recursion in interp-in-C would first show up at the self-host gate. A rough estimate: axiom0 at gcc -O2 compiles 100k lines in seconds. axiomc1 (fixed-register code, every local on the stack, checked arithmetic, bounds checks, no inlining) is probably 10–50× slower, so a self-compile takes minutes. That is plausible, but nothing measures or bounds it.
- Consequence if not fixed: a performance cliff or crash is discovered at T086 and has to be fixed across many modules under the R3 freeze pressure.
- Proposed fix: add to T075 (or T062): "tools/gen_large.py generates a 100k-line valid program (many modules, deep generics, long functions, 200-arm matches, 500-deep expression nesting); axiom0 compiles it in < 30 s and < 2 GB, native and interp run correctly; time per pass recorded". Add to T086 an acceptance budget for axiomc1 self-compile time (for example < 10 min) with `--time-passes` output archived.

### A1-12 [MINOR] [PLAUSIBLE] Lexer and encoder rely on control forms marked "if in spec" or left implicit
- Where: T031 "labeled loops if in spec"; T038 "all pattern kinds" (integer/char literal patterns, range patterns `'a'..='z'`, or-patterns not listed; T012 parses them "if in spec"); T040 native "compare chains". There is no explicit cast from fieldless enum to integer in T034/T038.
- Problem: a lexer written in Axiom needs char-range and or-patterns, and the encoder needs integer-literal matches and enum→u8 casts. If SPEC-02 omits any of these, the port becomes clumsy. Workarounds exist.
- Proposed fix: T003a subset list states explicitly: labelled break/continue, literal/char/range/or-patterns, `enum as uN` for fieldless enums. T038/T040 acceptance includes a lexer-style char-range match.

### A1-13 [MINOR] [PLAUSIBLE] Hash/Ord for tuples and `@derive(Hash, Ord)` are missing, but map keys and sort keys use them
- Where: T056 derive list "Copy, Clone, Eq, Debug?"; T069 cmp traits; T073 HashMap; axiom0 diagnostic ordering (file, offset, code) per T009.
- Problem: interning TypeKind and mono-instance keys need Hash + Eq on enums and structs. Deterministic sorts use tuple keys. Without derive or builtin tuple impls these must be hand-written, which is verbose and error-prone but possible.
- Proposed fix: T056 derive += Hash, PartialEq/Ord; T069: impls of Eq/Ord/Hash for tuples up to arity 4 (compiler-provided or written out).

### A1-14 [MINOR] [PLAUSIBLE] How the compiler finds std is unspecified
- Where: T060 §Scope ("package root and minimal manifest", "prelude as a real std module"); R8 (ROADMAP.md:39–43, "axiomc compiles the same sources").
- Problem: axiom0 and axiomc must both find `std/` the same way (a `--std` flag or a path relative to the exe). T086 and T087 also need that path to be independent of the build directory for byte-identical stage 2/3.
- Proposed fix: T060 §Scope: "std root discovery (`--std-root`, default `<exe>/../std`), paths recorded in no artifact".

### A1-15 [MINOR] [CONFIRMED] Parts of the fixed-point plan are underspecified
- Where: T086 §Scope (suite green with axiomc; no byte comparison with axiom0); T087 §Scope (axiomc2 == axiomc3).
- Problem: nothing fixes the optimization level and flags used at each stage, and nothing requires artifacts to be free of absolute paths and timestamps (needed when stage 2 and stage 3 build in different directories). Nothing compares stage-1 outputs (axiomc1 vs axiom0) byte-for-byte over the corpus, although that is the cheapest whole-compiler differential check and matches T077–T085's "identical behaviour".
- Proposed fix: T086 acceptance: "`--emit=obj` of axiomc1 and axiom0 byte-identical over tests/run (or every difference explained)"; T087: "stages built with identical flags (-O0 and -O1 both checked), in two different directories".

## Checked and OK
Feature → delivering task (native catch-up), all within T076's transitive deps unless a finding above says otherwise:

- kernel: typed ID newtypes `struct FileId(u32)` → T035 structs + T073a IdTable; arenas → T073a (needs T061a ptrs, OK via T070); Vec<T> → T070; HashMap<Str,V> → T073 (A1-07); interner → T073a (A1-03); stable hash → T007/T073 (A1-06); UTF-8 helpers → T071.
- source: file read (binary) → T074; line maps → Vec<u32> + binary_search T070; spans → structs T035.
- diag: enums with payloads → T038/T040; sort diagnostics → T070 (+A1-13); JSON escaping and formatting → T071; stderr → T074; exit codes 0/1/2/3 → T074 exit.
- lex: `char` → T034/T037; decode_char_at → T071; match on chars → T038 (A1-12); u8 byte literals and byte strings → T041; integer literal parsing with overflow → T071; keyword table → HashMap T073 or const T061 (A1-10).
- syntax: recursive AST via arena ids (typed IDs, T073a) or Box<T> (T070) + enums T038; mutual recursion → T032; Option/`?` → T039, generic → T054; error recovery → loops and labelled break T031 (A1-12).
- resolve: scope graph with HashMap/IdTable → T073/T073a; multi-file modules and cross-module cycles → T060; dotted paths → T014.
- hir/types/traits: hash-consed TypeId → T073a Interner (+A1-13); generics → T054/T059; traits for internal abstractions (static dispatch; dyn not needed per tasks/0260 §37, T058 correctly deferred) → T055/T056; closures for sort_by and visitors → T057/T059.
- own/mir/verify: dataflow bitsets → u64 bit ops T017/T034/T037; worklists → Vec T070; views/mut_view params → T048/T051 (+A1-08); drops of compiler data → T049/T051 (+A1-09).
- interp: value model → enums + ByteBuf; recursion → T032/T033; checked vs wrapping semantics to reproduce → T034 (+A1-06); const eval use → T061.
- opt: CFG passes → Vec/IdTable; `-O1` itself → T043.
- lir/abi/target/x64: u8/u32/u64 math, shifts, masks → T034/T037; LE byte emission → ByteBuf T071; hex dumps for `--emit=mc` → T071 hex formatting; opcode tables → A1-10.
- objmodel/obj/link: ByteBuf + `patch_u32_at` → T071; sections sorted → T070; PE layout u64 alignment math → T034; import table for kernel32/shell32 in axiomc's own output → T027/T065.
- driver: args (GetCommandLineW) → T074; env → T074; binary writes → T074; paths and dir listing → T074; `--time-passes` with Instant (integer ns, no floats) → T074; process exit → T074; panic=abort as ICE backstop → T034.
- Native catch-up chain confirmed: T033 (CFG/calls/>4 args), T037 (numerics, aggregates, struct ABI, bounds), T040 (enums/match/Option), T042 (rodata/strings/stdout), T051 (views, slices as 16-byte fat pointers, drops), T059 (mono, closures, fn pointers), T061a (own native lowering; paths issue A1-05), T065 (FFI).
- if-let/while-let/destructuring → T038; slices and sub-ranges → T048/T051; minimal raw pointers/unsafe → T061a; no floats needed by the compiler (T003a) — consistent with tasks/0260 §3–4.
- Iterators/for loops → T072 (HIR desugaring, so no native catch-up needed); adapters → T073 (depends on T059, OK).
- dyn Trait, comptime fn, linear-scan regalloc, separate compilation and unwind info deferred (R7) — none of them is needed to write axiomc if it follows axiom0's structure (enums, generics, fn pointers for target hooks via T057/T059).
- Single-unit compile of compiler+std with our PE linker: rel32 range and image size are fine for a 5–20 MB naive image; no external tool in the production path.
- Fixed point: T087 has axiomc1 (by axiom0) → axiomc2 → axiomc3 with byte identity of 2 and 3, and a documented trust chain; this matches tasks/0260 §41–43. Per-module differential plan (tokens/AST/HIR/MIR/bytes) in T076–T085: OK in principle (A1-07, A1-15).
- T003a requires the self-host std subset to be mapped to P9 tasks early, and T076 re-audits it before porting. Both are good, but neither catches A1-01, A1-02 or A1-05 unless the architect looks for them.

## Cross-lens notes
- A3 (executability): T061 `paths` (types/const) call the interpreter, but the layer rule in axiom-c-stage0 SKILL.md:60–61 puts `interp` above `types`. Const eval during typeck (array lengths) is a layer inversion; needs an explicit exception or a callback interface in SPEC-04.
- A3: T077–T085 each port 5–20k lines of C with `model: sonnet` and a 180-minute limit. They are likely too large for one agent run; consider splitting each into 2–3 sub-tasks by submodule.
- A3: T061a acceptance requires native tests, but its paths lack `mir`, `lir` and `target` (see A1-05).
- A4 (process): once A1-01 is decided, the axiom-testing skill should say which std tests may be `// modes: native` and why, so QA does not accept a silent loss of interp coverage.
