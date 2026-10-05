# SPEC-00 — Stage-0 bootstrap: milestone ladder, manifests, first programs

## Tóm tắt
Tài liệu này chốt **từng mốc (milestone) của compiler Stage-0 `axiom0` được phép làm gì**, để agent
không làm vượt mốc và QA có tiêu chí máy kiểm được:
- **Bản đồ tên các ladder**: V0–V4 (tasks/0262 §55), VS#1/VS#2 và BOOT-00..38 (0263 §51) ↔ task
  trên board (V1 = VS0 = T022, V2 = VS1 = T029, gate P5 = T044, V3 = T086, V4 = VS2 = T087).
- **Ladder P2..P10**: mỗi mốc liệt kê tính năng được thêm (mã `F-…`, có task oracle và task native),
  tính năng của mốc sau bị cấm, và các "đường tắt nguy hiểm" luôn bị cấm (AST→asm, xuất assembly
  text, assembler/linker ngoài trong đường sản xuất, LLVM, CRT, GC, std viết bằng C).
- **Manifest máy đọc được**: mỗi mốc có một khối ```` ```milestone ```` chứa JSON (0264 §19) liệt kê
  thư mục test bắt buộc pass; `tools/gatecheck.py` (T022) đọc các khối này. Gate chỉ có ĐẠT hoặc
  BỊ CHẶN (R9).
- **Các chương trình đầu tiên** của 0263 §32-39 viết lại bằng cú pháp chuẩn (exit 42, test âm
  `return true`, test MIR `40 + 2`, test tối ưu, test ABI `add(20, 22)`, test struct, ownership,
  capability) và mẫu "Xin chào thế giới", mỗi cái gắn với task và thư mục test.
- **Bảng BOOT-00..38 → task**, hoặc "hoãn tới epic … theo R6/R7" (comptime, regalloc, linker đầy
  đủ, AArch64; Linux-first của 0263 §4 bị đảo thành Windows-first).
Tập con self-host chính xác (tính năng nào axiom0 phải có để biên dịch axiomc) do T003a bổ sung vào
§9 của tài liệu này. Quyết định: ADR-0012.

Status: canonical (T003, 2026-10-04); §9 is completed by T003a. Rule ids `AXS-BOOT-NNN` are stable.
Decisions: ADR-0005 (native-after, gates, vertical slices), ADR-0012 (manifest format, ladder
choices). Semantics referenced here: `spec/SPEC-03-core-semantics.md`. Plan frame:
`spec/ROADMAP.md`. Consumers: every P2–P10 task ("Out of scope: features scheduled for later
tasks"), axiom-qa (scope check), T022 (`tools/gatecheck.py`), T003a, T076.

---

## 1. Rules of the ladder

**AXS-BOOT-001 — One milestone at a time.** A task implements only the features its milestone
introduces (§4) and the ones of earlier milestones. A feature introduced by a later milestone is
*forbidden* for it: the compiler reports the owning phase's "unsupported" diagnostic or the stage
diagnostic of the later task, and QA fails a change that implements it early. Reserving data-model
variants for later features is required, not forbidden ("implement later ≠ design later", 0263 §42;
SPEC-04 by T003a). [0263 §44-45; tasks/0262 §50; ROADMAP R1, R7]

**AXS-BOOT-002 — Out-of-subset constructs.** Constructs parsed by axiom0 (SPEC-02 S0) but outside
the self-host subset — float types and literals, `static` items, `@at`, `dyn Trait`, `i128`/`u128` —
are rejected by the owning phase with a code ending in `_UNSUPPORTED_IN_BOOTSTRAP` (for example
`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` with data `construct="@at"`), never a crash, never a silent
reinterpretation. S1 syntax (`async`, `.await`, `comptime`) is rejected by the parser with
`AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP` (AXS-GRM-003). [tasks/0494 §62; ADR-0011; SPEC-02 AXS-GRM-003]

**AXS-BOOT-003 — Interp first, native catch-up.** A feature runs in the oracle (MIR interpreter)
before native code exists for it. Its run tests carry `// native-after: <catch-up task>` (column
"native" in §4) until that task removes the marker (ADR-0005 §1). From MS-P4 on, every run test
without such a marker passes in both modes and the results agree (differential, T029).

**AXS-BOOT-004 — Always-forbidden shortcuts.** In no milestone may the production pipeline contain
(ids used in the manifests' `forbidden` lists):

| Id | Forbidden | Source |
|---|---|---|
| X-AST-TO-ASM | machine code generated from AST/HIR, bypassing MIR → LIR | 0263 §24, §28, §50 |
| X-ASM-TEXT | assembly text output as an intermediate of code generation | 0263 §30; tasks/0260 ABOOT-74 |
| X-EXT-ASM | an external assembler in the production path (GNU `as` only as a test oracle, T024) | 0263 §30; tasks/0260 ABOOT-74 |
| X-EXT-LINK | an external linker in the production path (gcc/ld only as a test oracle, T026/T028) | 0263 §8-10, §31; tasks/0260 ABOOT-75 |
| X-LLVM | LLVM or any third-party backend | 0263 §3; ROADMAP R2 |
| X-CRT | the C runtime in produced programs (startup is linker-generated, T027) | 0263 §10-12; 0181 §15-16 |
| X-GC | a garbage collector or hidden runtime | frozen semantic model |
| X-HOST-SEM | interpreter or constant evaluator inheriting host C arithmetic behaviour | SPEC-03 AXS-SEM-001 |
| X-INTERP-TARGET | the interpreter depending on target/backend modules | 0263 §25; tasks/0262 §10 |
| X-STD-IN-C | standard-library functionality implemented in C (only intrinsics and host intrinsics) | ROADMAP R8; ADR-0002 |

**AXS-BOOT-005 — Gate rule.** A milestone passes only when every test of its manifest and of every
earlier manifest passes, the checks it lists pass, and no forbidden feature or shortcut is present.
The only tolerated non-passing tests are `xfail: <task>` entries for a spec gap with an ADR; XPASS is
a failure. There is no "almost done": PASS or BLOCKED. [0264 §20; 0263 §45; ROADMAP R9; ADR-0005 §3]

**AXS-BOOT-006 — Native never diverges silently.** From MS-P4 on, a native executable either
behaves exactly like the oracle (SPEC-03 AXS-SEM-001) or is not produced. Until the native task of a
feature (§4) is done, `axiom0 build` reports `AX_DRIVER_NOT_YET_SUPPORTED` (data
`construct="native:<feature id>"`, `task` = the native task that delivers it, e.g. `task="T033"`) at
the first MIR construct it cannot lower (a branch before T033, a division check before T037, ...) instead of emitting code. Dropping
a MIR check (overflow, division, shift, bounds, `char`) to make code generation easier is never a
permitted BOOTSTRAP-SHORTCUT. Interp-first tests of such features carry `native-after`, so the
runner never requests those builds. The code is transient in the sense of AXD-014: once the task
named in `task` is done, no test of the self-host subset may expect it for that feature (it is
distinct from the permanent AXD-013 `_UNSUPPORTED_IN_BOOTSTRAP` codes for constructs outside the
self-host subset). [ADR-0012 §9; spec/diagnostics.md AXD-014]

**AXS-BOOT-007 — The MS-P4 overflow contract.** VS1 includes checked arithmetic. MIR lowers
`+ - *` and unary `-` on integers to the operation plus an overflow assert whose failure edge is the
panic path. In MS-P4 the native pipeline supports exactly this form for `i32` and `i64`:
- T023 lowers a MIR assert whose failure target is a panic to the LIR op `check_ovf <kind>` placed
  directly after the arithmetic op (no general branch, no basic-block split);
- T025 selects `add`/`sub`/`imul`/`neg` followed by `jo rel32` to the symbol `__ax_panic_<kind>`
  (`kind` is one of `overflow`, `divzero`, `shift`, `bounds`, `char`, `assert`, `unreachable`); the
  encoder form `jcc rel32` with a REL32 relocation against a symbol belongs to T024;
- T027 synthesises every referenced `__ax_panic_<kind>` in the linker-generated startup code as
  exactly `and rsp, -16; sub rsp, 32; mov ecx, 101; call [ExitProcess]` (no message
  yet). The stub is entered by a jump, not a call, so no return address is pushed and `rsp` may be
  0 or 8 (mod 16) on arrival (a function body or a frameless leaf); `and rsp, -16` re-aligns it,
  `sub rsp, 32` reserves the Win64 shadow space, and the `call` therefore happens with `rsp` ≡ 0
  (mod 16). The stub never returns, so the original `rsp` is not restored. T027's fixture test
  jumps to the stub once with `rsp` ≡ 0 (mod 16) and once with `rsp` ≡ 8 (mod 16); both must exit
  with 101. T042 makes the stubs write `panic: <message>` and a line feed to stderr first, keeping
  the same alignment prologue;
- unsigned and 8/16-bit widths, division, shifts, bounds and `char` checks become native in T037;
  until then AXS-BOOT-006 applies to them.
The T029 differential runs FP-10 natively. [ADR-0012 §9; ADR-0005 §1]

## 2. Ladder name map

**AXS-BOOT-010 — Names.** The corpus uses three ladders; this table is the only translation.

| Name | Source | Meaning | Board |
|---|---|---|---|
| V0 | tasks/0262 §55 | lexer/parser | T011 (core parser), T013 (fuzz); checked by the T022 gate (milestone MS-P2) |
| V1 | tasks/0262 §55 | source → MIR (oracle) | **VS0** = T022 (MS-P3) |
| V2 | tasks/0262 §55 | source → native executable | **VS1** = T029 (MS-P4) = 0263 §51 VERTICAL SLICE #1 |
| — | board | language core | **P5 gate** = T044 (MS-P5); not a vertical slice of the corpus |
| V3 | tasks/0262 §55 | compiler written in Axiom | T086 stage-1 (MS-P10a), start of 0263 §51 VS#2 |
| V4 | tasks/0262 §55 | reproducible self-hosting | **VS2** = T087 (MS-P10b): the end of 0263 §51 VERTICAL SLICE #2 (BOOT-31..38; BOOT-36 is T086, BOOT-37..38 are T087) |
| BOOT-nn | 0263 §51 | ladder steps | §7 of this spec |
| ABOOT-nn | tasks/0260 | bootstrap invariants | traced in `spec/requirements/CATALOG.md` |

"VS2" on the board always means self-hosting (T087), never the P5 gate. [ADR-0005; audit A2-07]

## 3. Milestone ladder (P2..P10)

**AXS-BOOT-020 — Milestones.** Each milestone is closed by a board gate task. P0 (specs,
traceability, gate T111) and P1 (kernel) have no language features; their tool and unit tests are
the regression base MS-P1.

| Milestone | Gate | Aliases | Goal | Executors |
|---|---|---|---|---|
| MS-P1 | T022 | BOOT-00 | build, runner, archcheck, kernel, source DB, diagnostics | unit tests |
| MS-P2 | T022 | V0, BOOT-01..03 | whole v0.1 grammar lexed, parsed, resolved, lowered to HIR | front end only |
| MS-P3 | T022 | VS0, V1, BOOT-04..06 | the subset typed, lowered to verified MIR, run by the oracle | interp |
| MS-P4 | T029 | VS1, V2, BOOT-07..11 | first native executables: constants, checked `+ - *` and unary `-` on `i32`/`i64` (overflow → panic stub, AXS-BOOT-007), locals, `return` | interp + native (VS1 set) |
| MS-P5 | T044 | BOOT-12..18, 27 (-O1) | language core: mutation, control flow, functions, numerics, aggregates, enums, patterns, Option/Result, strings, -O1 | interp + native |
| MS-P6 | T052 | BOOT-19..22 | ownership, initialisation, views, slices, drop and cleanup | interp + native |
| MS-P7 | T062 | BOOT-23..26 (const items) | methods, generics, traits, closures, modules, const items, raw pointers, host interface | interp + native |
| MS-P8 | T075 | — | FFI (`extern`, `@repr(C)`, DLL imports) | native (FFI is native-only, ADR-0002 §4) |
| MS-P9 | T075 | — | self-host std subset written in Axiom | interp + native |
| MS-P10a | T086 | V3, BOOT-31..36 | axiomc ported module by module; axiom0 builds axiomc; axiomc passes the full suite | interp + native, both compilers |
| MS-P10b | T087 | VS2, V4, BOOT-37..38 | stage-2 = stage-3 byte-identical, reproducible, no external tools | both compilers |

What each milestone may implement is the union of the `introduces` lists of it and the earlier
milestones (§4, §6); everything else is forbidden for it (AXS-BOOT-001).

## 4. Feature table

**AXS-BOOT-030 — Feature ids.** Every language or library capability of the core has an id. The
oracle task delivers it in the interpreter (and front end), the native task removes the
`native-after` markers for it. `spec/selfhost-subset.tsv` (T003a) reuses these ids (and may refine
them with suffixes, `F-STR.LEN`) and adds the first consumer of each. Machine reading: the task ids
of a cell are its tokens matching `T\d{3}[a-z]?`; text in parentheses only explains them; `—` means
none (F-FFI is native-only, ADR-0002 §4).

| Id | Feature | Oracle task(s) | Native task | Milestone |
|---|---|---|---|---|
| F-INT | integer types (all widths), literals, suffixes, defaulting, range check (AXS-SEM-010..022) | T017 | T028 (constants), T037 (all widths) | MS-P3 |
| F-ARITH | `+ - *` and unary `-`, checked (AXS-SEM-030) | T017, T019, T021 | T028 (`i32`/`i64` with the overflow check, AXS-BOOT-007), T037 (all other widths) | MS-P3 |
| F-DIVREM | `/ %` with zero and `MIN / -1` checks (AXS-SEM-032) | T021 | T037 | MS-P3 |
| F-BITS | `& \| ^ ~ << >>`, shift-range check (AXS-SEM-033/034) | T021 | T037 | MS-P3 |
| F-CMP | comparisons, `bool`, `!`, short-circuit `&& \|\|` (AXS-SEM-035/036) | T017, T019, T021 | T033 | MS-P3 |
| F-LET | immutable `let` (annotated / inferred) | T017, T019 | T028 | MS-P3 |
| F-CF | `if`/`while`/`loop` as statements, `return` | T017, T019, T021 | T028 (`return`), T033 | MS-P3 |
| F-CALL | direct calls of functions | T017, T019, T021 | T033 | MS-P3 |
| F-MAIN | `main` forms, exit code (AXS-SEM-080/081) | T017, T021 | T027, T028 | MS-P3 |
| F-PANIC | panic = abort, exit 101 (AXS-SEM-071) for compiler-inserted checks | T021 | T028 (overflow stub), T037 (other checks), T042 (stderr line) | MS-P3 |
| F-MUT | `let mut`, assignment, compound assignment, deferred init (AXS-SEM-043/044) | T030 | T033 | MS-P5 |
| F-CFV | `if`/`loop` values, `break value`, `continue`, labels, block values, `never` | T031 | T033 | MS-P5 |
| F-FN | several functions, recursion, mutual recursion, parameters, returns | T032 | T033 | MS-P5 |
| F-CAST | `as` table (AXS-SEM-060), `char`, `bool` casts | T034 | T037 | MS-P5 |
| F-WRAP | wrapping and bit intrinsics (AXS-SEM-031) | T034 | T037 | MS-P5 |
| F-ASSERT | `assert`, `unreachable` (AXS-SEM-072) | T034 | T037 | MS-P5 |
| F-STRUCT | structs, tuples, layout engine | T035 | T037 | MS-P5 |
| F-ARRAY | fixed arrays, repeat literals, indexing, bounds checks, `len(a)` | T036 | T037 | MS-P5 |
| F-ENUM | enums, `match`, exhaustiveness, `enum as uN` | T038 | T040 | MS-P5 |
| F-PATTERN | literal/range/or-patterns, guards, `if let`, `while let`, `let … else`, destructuring | T038b | T040 | MS-P5 |
| F-OPTRES | built-in Option/Result, `?` (ADR-0006 §4) | T039 | T040 | MS-P5 |
| F-STR | `Str` literals, `print`, `panic(msg)`, `len(s)` | T041 | T042 | MS-P5 |
| F-OPT1 | MIR optimizer -O1 (const folding, DCE, CFG simplify) | T043 | T043 | MS-P5 |
| F-MOVE | move/copy analysis, partial moves, `@derive(Copy)` marker | T046 | T051 | MS-P6 |
| F-INIT | definite initialisation, re-init after move | T047 | T051 | MS-P6 |
| F-VIEW | `view`/`mut_view`, regions, conflicts, stored views | T048 | T051 | MS-P6 |
| F-SLICE | dynamic-length views, sub-ranges `s[a..b]` | T048b | T051 | MS-P6 |
| F-DROP | `impl Drop` (fixed shape), `drop(x)`, drop elaboration, cleanup on every edge | T049, T050 | T051 | MS-P6 |
| F-MODULE | multi-file modules, `use`, visibility, prelude module, `axiom.toml`, std root | T060 | T060 | MS-P7 |
| F-METHOD | methods, `impl` blocks, member calls | T053 | T059 | MS-P7 |
| F-GENERIC | generics, monomorphization, mangling, generic drop glue, generic Option/Result | T054, T054b | T059 | MS-P7 |
| F-TRAIT | traits, solver, static dispatch | T055 | T059 | MS-P7 |
| F-TRAIT2 | associated items, default methods, supertraits, operator traits, derive | T056 | T059 | MS-P7 |
| F-CLOSURE | closures, capture inference, function values | T057 | T059 | MS-P7 |
| F-CONST | const items, aggregate constant tables (ADR-0004 §2) | T061 | T061d | MS-P7 |
| F-PTR | raw pointers, `unsafe`, memory intrinsics | T061a | T061b | MS-P7 |
| F-HOST | host-interface intrinsics (ADR-0002) | T061c | T070, T074, T074b | MS-P7 |
| F-FFI | `extern "C"`/`"system"`, `@repr(C)`, `@link` DLL imports | — | T065 | MS-P8 |
| F-STD-CORE | core library | T069 | T069 | MS-P9 |
| F-STD-ALLOC | allocator, `Box`, `Vec`, sort | T070 | T070 | MS-P9 |
| F-STD-TEXT | `String`, UTF-8, char primitives, ByteBuf, format/parse, UTF-16 | T071, T071b, T071c | T071, T071b, T071c | MS-P9 |
| F-FOR | iterator protocol, `for`, ranges | T072 | T072 | MS-P9 |
| F-STD-COLL | `HashMap`/`HashSet` (insertion order), iterator adapters | T073 | T073 | MS-P9 |
| F-STD-ARENA | arenas, typed ID tables | T073a | T073a | MS-P9 |
| F-STD-OS | io, env, args, process, fs, path, directories, clock | T074, T074b | T074, T074b | MS-P9 |
| F-SELFHOST | axiomc in Axiom, stage-1 | T077–T086 | T086 | MS-P10a |
| F-FIXEDPOINT | stage-2/3 fixed point, reproducibility | T087 | T087 | MS-P10b |

Not in any core milestone (post-T087 epics, ROADMAP R7): floats (E12.2), `i128`/saturating (E12.1),
`static`/`@at` (E13.3, E13.6), `dyn` (E14.4), comptime functions (E14.1), async (E11.4), linear-scan
register allocation (E15.8), separate compilation (E18.6), ELF/Linux (E16.9), unwinding (E13.5,
E17.3).

## 5. First programs

**AXS-BOOT-040 — The first-test set.** The test programs of 0263 §32-39 (plus tasks/0494 §41 and the
owner's UTF-8 greeting) in canonical syntax. Each is a required test of the named task and of the
milestone that contains it. Diagnostic codes are registered in `spec/diagnostics.md`.

**FP-01 — First green test** (0263 §32; T021 interp, T028 native; `tests/run/basic/return_42.ax`):
```axiom
fn main() -> i32 {
    return 42
}
```
Expected: compiles; exit code 42 in interp and native.

**FP-02 — First negative test** (0263 §33; T017; `tests/ui/typeck/return_bool.ax`):
```axiom
fn main() -> i32 {
    return true
}
```
Expected: `AX_TYPE_MISMATCH` at `true` (0263's `AX1301 TypeMismatch` in the registry's naming).

**FP-03 — First MIR test** (0263 §34; T019; `tests/mir/build/return_40_plus_2.ax`):
```axiom
fn main() -> i32 {
    return 40 + 2
}
```
Expected MIR structure (golden, numbering not significant): two constant operands 40 and 2, one
*checked* `Add` (overflow assert to the panic path, AXS-SEM-030), the result moved to the return
place, `return`. 0263 lists `CONST CONST ADD RETURN`; the overflow assert is the only addition.

**FP-04 — First optimisation test** (0263 §35; T043; `tests/opt/fold_40_plus_2.ax`): the FP-03
program at `-O1` has MIR `return 42` (the assert is folded away because 40 + 2 cannot overflow);
interp and native both exit 42.

**FP-05 — First ABI test** (0263 §36; T032 interp, T033 native — not VS1, ADR-0005 §1;
`tests/run/fn/add_20_22.ax`):
```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b
}

fn main() -> i32 {
    return add(20, 22)
}
```
Expected: exit 42.

**FP-06 — First memory test** (0263 §37; T035 interp, T037 native; `tests/run/struct/point_sum.ax`):
```axiom
struct Point {
    x: i32
    y: i32
}

fn main() -> i32 {
    let p = Point { x: 20, y: 22 }
    return p.x + p.y
}
```
Expected: exit 42 (struct, layout, place, field projection, load, aggregate).

**FP-07 — First ownership test** (0263 §38; T046; `tests/ui/own/use_after_move.ax`). `use` is a
keyword in Axiom, so 0263's `use(a)` is spelled `consume(a)`:
```axiom
struct Buffer {
    len: i32
}

fn make_buffer() -> Buffer { Buffer { len: 0 } }

fn consume(b: Buffer) {}

fn main() {
    let a = make_buffer()
    let b = a
    consume(a)
}
```
Expected: the move-analysis use-after-move diagnostic at `a` in `consume(a)` (0263's `AX1401
UseAfterMove`), with a note at the move `let b = a`. Exact code: SPEC-10/11 (T045).

**FP-08 — First capability test** (0263 §39; T048; `tests/ui/cap/view_then_mutate.ax`):
```axiom
struct Buffer {
    len: i32
}

fn make_buffer() -> Buffer { Buffer { len: 0 } }

fn grow(b: mut_view<Buffer>) { b.len += 1 }

fn read(b: view<Buffer>) -> i32 { b.len }

fn main() -> i32 {
    let mut a = make_buffer()
    let x = view(a)
    grow(mut_view(a))
    read(x)
}
```
Expected: a capability-conflict diagnostic at `mut_view(a)` (a live `view` `x` is used later), proving
that `view` is a capability, not pointer + length. Exact code and rule: SPEC-11 (T045, T048).

**FP-09 — First output test** (tasks/0494 §41, the owner's `Xin chào thế giới` rule — `spec/requirements/OWNER.md` status note 2026-10-01 and the
CLAUDE.md decision of 2026-09-29; T041
interp, T042 native; `tests/run/str/greeting.ax`):
```axiom
fn main() {
    print("Xin chào thế giới\n")
}
```
Expected: stdout is exactly the UTF-8 bytes of `Xin chào thế giới` followed by LF; exit 0; the
console check of T042 shows the glyphs correctly (ADR-0005 §16, ADR-0006 §9).

**FP-10 — First panic test** (SPEC-03 SEM-T02; T021 interp, T028 native — part of the VS1 set by
AXS-BOOT-007, no `native-after`; `tests/run/basic/overflow_panics.ax`; the T029 differential runs it):
```axiom
fn main() -> i32 {
    let x: i32 = 2147483647
    return x + 1
}
```
Expected: exit 101 in both modes; stderr `panic: arithmetic overflow` (native: from T042 on). The
other trap tests of T021 (division by zero, shifts) carry `// native-after: T037`.

## 6. Milestone manifests

**AXS-BOOT-050 — Block format.** Each milestone has exactly one fenced code block whose info string
is `milestone` and whose content is one JSON object (RFC 8259, no comments, UTF-8) (0264 §19 chose
JSON for Stage-0). Fields, all required:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `MS-P<n>` or `MS-P<n><letter>`; unique |
| `title` | string | short name |
| `phase` | string | roadmap phase, `P1`..`P10` |
| `gate` | string | board task id that closes the milestone |
| `previous` | string or null | id of the preceding milestone (the chain is linear) |
| `aliases` | array of strings | names from §2 / 0263 §51 |
| `goal` | string | one sentence |
| `components` | array of strings | compiler components that must exist (0264 §19 `required`) |
| `introduces` | array of strings | feature ids of §4 first allowed at this milestone |
| `native` | array of strings | feature ids whose native support must be complete (no `native-after` left for their native tasks) at this gate |
| `modes` | array of strings | run modes every unmarked run test must pass: `interp`, `native` |
| `must_pass` | array of strings | test files or directories, repository-relative, `/` separators, no globs |
| `checks` | array of strings | names from the check table below |
| `forbidden` | array of strings | shortcut ids of AXS-BOOT-004 |

Checks (each passes when its command exits 0; commands run from the repository root):

| Check | Command | Owner |
|---|---|---|
| `axtest_selftest` | `python tools/tests/axtest/run_selftests.py` | T005 |
| `archcheck_selftest` | `python tools/tests/archcheck/run_selftests.py` | T006 |
| `archcheck` | `python tools/archcheck.py` | T006 |
| `reqcov` | `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` | harness |
| `harness_check` | `python .claude/skills/axiom-tasks/scripts/harness_check.py` | harness |
| `gatecheck` | the structural step 1, step 4 and the T022 rules (a)-(d) of AXS-BOOT-051 | T022 |
| `differential` | the differential CI leg of T029 | T029 |
| `determinism` | the build-twice byte comparison of T029 | T029 |

`must_pass` lists only tests discovered by `tools/axtest.py`; self-test scripts of tools appear only
as checks.

**AXS-BOOT-051 — What `tools/gatecheck.py` does with the blocks** (T022 implements, Python
standard library only):
1. Extract every block: a line that is exactly ```` ```milestone ```` opens it, the next line that is
   exactly ```` ``` ```` closes it; parse the content with `json.loads`. Any parse error, missing or
   extra field, wrong type, duplicate `id`, unknown feature id (not a `| F-…` row of §4), unknown
   shortcut id, a `previous` that is not the preceding block, or a `gate` that is not a board task
   is an error (exit 1).
2. `--gate <TID>` selects the *current* milestone(s): those whose `gate` is `<TID>`. A milestone is
   *due* if it is current or its gate task is done. Without `--gate`, only done gates are due.
3. For every due milestone, cumulatively in chain order: every `must_pass` path exists; `python
   tools/axtest.py <paths…>` reports no FAIL, XPASS, CRASH or TIMEOUT; every XFAIL names a task
   that exists and is not done; a SKIP is accepted only with a reason (a `native-after` naming a task
   that is not yet done, a missing optional tool, or a `modes` restriction).
4. For every feature in `native` of a due milestone, `grep "native-after: <task>"` over `tests/`
   is empty for each native task of that feature: the `T\d{3}[a-z]?` tokens of its §4 "Native
   task" cell (AXS-BOOT-030).
5. The listed `checks` run with the commands of the check table (AXS-BOOT-050).
   Steps 2–5 also cover rules (a)–(d) of T022 (invariants, xfail/native-after targets, the self-host
   subset TSV).
6. Output: one line per milestone `MS-Px PASS` or `MS-Px BLOCKED: <first reason>`; exit 0 only if
   every due milestone passes. There is no third state (AXS-BOOT-005).

**AXS-BOOT-052 — Changing a manifest.** Adding a test path or a feature to a milestone that is not
yet due is an ordinary edit by the task that creates the tests (the architect files it when the path
is outside the editor's `paths`). Removing anything from a due milestone, or moving a feature to a
later milestone, needs an ADR. T076 (self-hosting plan) re-splits the port tasks and updates the
MS-P10a `must_pass` list to the differential artefacts it defines.

### 6.1 Manifest blocks

```milestone
{
  "id": "MS-P1",
  "title": "Foundation and kernel",
  "phase": "P1",
  "gate": "T022",
  "previous": null,
  "aliases": ["BOOT-00"],
  "goal": "The build, the test runner, the layer checker and the compiler kernel work and are tested.",
  "components": ["build", "test_runner", "archcheck", "kernel", "source_db", "diagnostics"],
  "introduces": [],
  "native": [],
  "modes": [],
  "must_pass": ["tests/unit/driver", "tests/unit/kernel", "tests/unit/source", "tests/unit/diag"],
  "checks": ["axtest_selftest", "archcheck_selftest", "archcheck", "harness_check"],
  "forbidden": ["X-LLVM", "X-GC"]
}
```

```milestone
{
  "id": "MS-P2",
  "title": "Front end (V0)",
  "phase": "P2",
  "gate": "T022",
  "previous": "MS-P1",
  "aliases": ["V0", "BOOT-01", "BOOT-02", "BOOT-03"],
  "goal": "Every v0.1 source file is lexed, parsed with recovery, resolved and lowered to HIR, with diagnostics as data.",
  "components": ["lexer", "parser", "ast", "resolver", "hir", "driver"],
  "introduces": [],
  "native": [],
  "modes": [],
  "must_pass": ["tests/lex", "tests/ui/lex", "tests/parse", "tests/ui/parse", "tests/fuzz", "tests/resolve", "tests/ui/resolve", "tests/hir", "tests/driver"],
  "checks": ["archcheck", "harness_check"],
  "forbidden": ["X-AST-TO-ASM", "X-LLVM", "X-GC"]
}
```

```milestone
{
  "id": "MS-P3",
  "title": "Semantic core on the oracle (VS0)",
  "phase": "P3",
  "gate": "T022",
  "previous": "MS-P2",
  "aliases": ["VS0", "V1", "BOOT-04", "BOOT-05", "BOOT-06"],
  "goal": "The bootstrap subset is type-checked, lowered to verified MIR and executed by the MIR interpreter with exact SPEC-03 semantics.",
  "components": ["type_checker", "thir", "mir", "mir_verifier", "mir_interpreter"],
  "introduces": ["F-INT", "F-ARITH", "F-DIVREM", "F-BITS", "F-CMP", "F-LET", "F-CF", "F-CALL", "F-MAIN", "F-PANIC"],
  "native": [],
  "modes": ["interp"],
  "must_pass": ["tests/typeck", "tests/ui/typeck", "tests/mir", "tests/verify", "tests/run/basic", "tests/conformance/vs0"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck"],
  "forbidden": ["X-AST-TO-ASM", "X-LLVM", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET"]
}
```

```milestone
{
  "id": "MS-P4",
  "title": "First native executable (VS1)",
  "phase": "P4",
  "gate": "T029",
  "previous": "MS-P3",
  "aliases": ["VS1", "V2", "BOOT-07", "BOOT-08", "BOOT-09", "BOOT-10", "BOOT-11"],
  "goal": "fn main() -> i32 { return 42 } and the VS1 set (constants, checked + - * and unary - on i32/i64 with the overflow panic stub, locals, return) run natively as Windows PE executables built only by axiom0, and agree with the oracle.",
  "components": ["lir", "abi_lowering", "machine_ir", "isel", "frame_lowering", "machine_verifier", "encoder", "object_model", "coff_writer", "pe_linker", "startup"],
  "introduces": [],
  "native": ["F-LET", "F-MAIN"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/lir", "tests/encode", "tests/mc/isel", "tests/mc/frame", "tests/obj", "tests/link", "tests/run/native", "tests/diff", "tests/conformance/vs1"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET"]
}
```

```milestone
{
  "id": "MS-P5",
  "title": "Language core",
  "phase": "P5",
  "gate": "T044",
  "previous": "MS-P4",
  "aliases": ["BOOT-12", "BOOT-13", "BOOT-14", "BOOT-15", "BOOT-16", "BOOT-17", "BOOT-18", "BOOT-27"],
  "goal": "Mutation, control flow, functions, all integer operations and casts, structs, tuples, arrays, enums, patterns, Option/Result, strings and -O1 work in both executors and agree at -O0 and -O1.",
  "components": ["layout", "mir_optimizer_o1", "rodata"],
  "introduces": ["F-MUT", "F-CFV", "F-FN", "F-CAST", "F-WRAP", "F-ASSERT", "F-STRUCT", "F-ARRAY", "F-ENUM", "F-PATTERN", "F-OPTRES", "F-STR", "F-OPT1"],
  "native": ["F-INT", "F-ARITH", "F-DIVREM", "F-BITS", "F-CMP", "F-CF", "F-CALL", "F-PANIC", "F-MUT", "F-CFV", "F-FN", "F-CAST", "F-WRAP", "F-ASSERT", "F-STRUCT", "F-ARRAY", "F-ENUM", "F-PATTERN", "F-OPTRES", "F-STR", "F-OPT1"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/run/vars", "tests/ui/vars", "tests/run/cfg", "tests/ui/cfg", "tests/run/fn", "tests/ui/fn", "tests/run/native_abi", "tests/run/numeric", "tests/ui/numeric", "tests/run/struct", "tests/ui/struct", "tests/run/array", "tests/ui/array", "tests/run/native_aggr", "tests/run/enum", "tests/ui/enum", "tests/run/pattern", "tests/ui/pattern", "tests/run/result", "tests/ui/result", "tests/run/native_enum", "tests/run/str", "tests/run/native_str", "tests/opt", "tests/diff/opt", "tests/conformance/p5"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET"]
}
```

```milestone
{
  "id": "MS-P6",
  "title": "Ownership, capabilities, drop",
  "phase": "P6",
  "gate": "T052",
  "previous": "MS-P5",
  "aliases": ["BOOT-19", "BOOT-20", "BOOT-21", "BOOT-22"],
  "goal": "Move/copy, initialisation, view/mut_view capabilities, slices and drop elaboration are enforced, re-verified on MIR, executed natively, and survive the adversarial suite.",
  "components": ["place_model", "move_analysis", "init_analysis", "capability_analysis", "drop_elaboration", "mir_verifier_v2"],
  "introduces": ["F-MOVE", "F-INIT", "F-VIEW", "F-SLICE", "F-DROP"],
  "native": ["F-MOVE", "F-INIT", "F-VIEW", "F-SLICE", "F-DROP"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/ui/own", "tests/run/own", "tests/ui/init", "tests/run/init", "tests/ui/cap", "tests/run/cap", "tests/run/slice", "tests/ui/slice", "tests/run/drop", "tests/ui/drop", "tests/verify/own", "tests/run/native_own", "tests/conformance/adversarial", "tests/conformance/stress"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET"]
}
```

```milestone
{
  "id": "MS-P7",
  "title": "Abstraction",
  "phase": "P7",
  "gate": "T062",
  "previous": "MS-P6",
  "aliases": ["BOOT-23", "BOOT-24", "BOOT-25", "BOOT-26"],
  "goal": "Methods, generics with monomorphization, traits with static dispatch, closures, modules, const items and tables, raw pointers and the host interface work in both executors.",
  "components": ["methods", "monomorphization", "trait_solver", "closures", "module_graph", "const_evaluator", "host_interface"],
  "introduces": ["F-MODULE", "F-METHOD", "F-GENERIC", "F-TRAIT", "F-TRAIT2", "F-CLOSURE", "F-CONST", "F-PTR", "F-HOST"],
  "native": ["F-MODULE", "F-METHOD", "F-GENERIC", "F-TRAIT", "F-TRAIT2", "F-CLOSURE", "F-CONST", "F-PTR"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/run/method", "tests/ui/method", "tests/typeck/generic", "tests/ui/generic", "tests/run/generic", "tests/run/mono", "tests/ui/mono", "tests/run/trait", "tests/ui/trait", "tests/run/trait2", "tests/ui/trait2", "tests/run/closure", "tests/ui/closure", "tests/run/native_p7", "tests/modules", "tests/ui/modules", "tests/run/comptime", "tests/ui/comptime", "tests/run/ptr", "tests/ui/ptr", "tests/run/native_ptr", "tests/run/host", "tests/run/native_const", "tests/conformance/p7"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET", "X-STD-IN-C"]
}
```

```milestone
{
  "id": "MS-P8",
  "title": "FFI",
  "phase": "P8",
  "gate": "T075",
  "previous": "MS-P7",
  "aliases": [],
  "goal": "extern \"C\" / \"system\" functions, @repr(C) layout and DLL imports work natively.",
  "components": ["ffi", "import_tables"],
  "introduces": ["F-FFI"],
  "native": ["F-FFI"],
  "modes": ["native"],
  "must_pass": ["tests/run/ffi", "tests/ui/ffi"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-STD-IN-C"]
}
```

```milestone
{
  "id": "MS-P9",
  "title": "Self-host std subset",
  "phase": "P9",
  "gate": "T075",
  "previous": "MS-P8",
  "aliases": [],
  "goal": "The std subset axiomc needs is written in Axiom, compiled by axiom0, and passes its tests and the real-program suite in both executors.",
  "components": ["std_core", "std_alloc", "std_text", "std_collections", "std_arena", "std_os"],
  "introduces": ["F-STD-CORE", "F-STD-ALLOC", "F-STD-TEXT", "F-FOR", "F-STD-COLL", "F-STD-ARENA", "F-STD-OS"],
  "native": ["F-HOST", "F-STD-CORE", "F-STD-ALLOC", "F-STD-TEXT", "F-FOR", "F-STD-COLL", "F-STD-ARENA", "F-STD-OS"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/std/core", "tests/std/alloc", "tests/std/text", "tests/std/fmt", "tests/std/bytes", "tests/std/utf16", "tests/run/for", "tests/std/collections", "tests/std/arena", "tests/std/io", "tests/std/fs", "tests/programs", "tests/conformance/std"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET", "X-STD-IN-C"]
}
```

```milestone
{
  "id": "MS-P10a",
  "title": "Stage-1 self compile (V3)",
  "phase": "P10",
  "gate": "T086",
  "previous": "MS-P9",
  "aliases": ["V3", "BOOT-31", "BOOT-32", "BOOT-33", "BOOT-34", "BOOT-35", "BOOT-36"],
  "goal": "axiomc, written in Axiom, is built by axiom0, matches axiom0 on every differential artefact, and passes the full suite within the SPEC-20 compile-time budget.",
  "components": ["axiomc_frontend", "axiomc_semantics", "axiomc_backend", "axiomc_object_linker", "axiomc_driver", "bootstrap_script"],
  "introduces": ["F-SELFHOST"],
  "native": ["F-SELFHOST"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/selfhost/kernel_source_diag", "tests/selfhost/lexer", "tests/selfhost/parser", "tests/selfhost/resolve_hir", "tests/selfhost/typeck_traits", "tests/selfhost/own_mir_verify", "tests/selfhost/interp_opt", "tests/selfhost/backend", "tests/selfhost/obj_link_driver", "tests/selfhost/stage1"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET", "X-STD-IN-C"]
}
```

```milestone
{
  "id": "MS-P10b",
  "title": "Fixed point and reproducible bootstrap (VS2)",
  "phase": "P10",
  "gate": "T087",
  "previous": "MS-P10a",
  "aliases": ["VS2", "V4", "BOOT-37", "BOOT-38"],
  "goal": "axiomc2 passes the full suite with results identical to axiomc1, axiomc2 and axiomc3 are byte-identical when built in different directories, and the chain runs with gcc/ld/as absent from PATH.",
  "components": ["fixed_point_check", "reproducibility_check"],
  "introduces": ["F-FIXEDPOINT"],
  "native": ["F-FIXEDPOINT"],
  "modes": ["interp", "native"],
  "must_pass": ["tests/selfhost/fixedpoint"],
  "checks": ["archcheck", "reqcov", "harness_check", "gatecheck", "differential", "determinism"],
  "forbidden": ["X-AST-TO-ASM", "X-ASM-TEXT", "X-EXT-ASM", "X-EXT-LINK", "X-LLVM", "X-CRT", "X-GC", "X-HOST-SEM", "X-INTERP-TARGET", "X-STD-IN-C"]
}
```

## 7. BOOT-00..38 → board

**AXS-BOOT-060 — Step map.** Every step of 0263 §51 maps to board tasks or to a recorded deferral.
Deferred steps are not required for self-hosting; agents reading 0263 or tasks/0260 must not pull
them into axiom0 (ROADMAP R7).

| Step (0263 §51) | Board task(s) | Status |
|---|---|---|
| BOOT-00 Repository + Build | T004, T005, T006 (+ specs T001–T003a) | MS-P1 |
| BOOT-01 Lexer | T010 | MS-P2 |
| BOOT-02 Parser | T011 (core), T012 (rest of the grammar) | MS-P2 (vertical slice: T014 needs only T011, ADR-0005 §4) |
| BOOT-03 Basic HIR | T014, T015, T015b | MS-P2 |
| BOOT-04 Type Checking | T017 | MS-P3 |
| BOOT-05 Minimal MIR | T018 (after the ownership spec T045), T019, T020 | MS-P3 |
| BOOT-06 MIR Interpreter | T021; gate T022 | MS-P3 |
| BOOT-07 x86-64 Machine IR | T023 (LIR), T025 (ABI lowering on LIR, ADR-0003), T025b (frame, machine verifier) | MS-P4 |
| BOOT-08 Machine Encoder | T024 | MS-P4 |
| BOOT-09 ELF Object Writer | T026 — **COFF** instead of ELF (R6) | MS-P4 |
| BOOT-10 Tiny Axiom Linker | T027 — PE32+ with kernel32 imports | MS-P4 |
| BOOT-11 Native Execution / VERTICAL SLICE #1 | T028; gate T029 (VS1 set only, ADR-0005 §1) | MS-P4 |
| BOOT-12 Variables | T030 (immutable `let` already in T017/T019) | MS-P5 |
| BOOT-13 CFG | T031; native T033 | MS-P5 |
| BOOT-14 Functions + ABI | T032; native T033 (first ABI test FP-05) | MS-P5 |
| BOOT-15 Struct + Layout | T035; native T037 | MS-P5 |
| BOOT-16 Arrays | T036; native T037 | MS-P5 |
| BOOT-17 Enum + Match | T038, T038b; native T040 | MS-P5 |
| BOOT-18 Result + Option | T039; native T040 | MS-P5 |
| (strings, print — not a ladder step) | T041, T042 | MS-P5, needed for output tests |
| BOOT-19 Ownership | T045 (spec), T046, T047 | MS-P6 |
| BOOT-20 Capability/View | T048, T048b | MS-P6 |
| BOOT-21 Drop | T049, T050; native T051; gate T052 | MS-P6 |
| BOOT-22 Cleanup | T049 (cleanup on every edge including `?`) | MS-P6 |
| BOOT-23 Generic | T054, T054b; native T059 | MS-P7 |
| BOOT-24 Traits | T053, T055, T056; native T059 | MS-P7 |
| BOOT-25 Closures | T057; native T059 | MS-P7 |
| BOOT-26 Comptime | T061 **const items only** (+ T061d native tables); comptime functions and blocks deferred to E14.1 by R7 | partly MS-P7, rest deferred |
| BOOT-27 Optimization | T043 (-O1) — earlier than the ladder; ladder 2 deferred to E15.4 (T064) by R7 | MS-P5 |
| BOOT-28 Register Allocation | deferred to E15.8 (T063) by R7; conditional pull-in before T087 if T086 exceeds the SPEC-20 budget (ADR-0005 §7) | deferred |
| BOOT-29 Full ELF Linker | deferred: multi-object/archives to E18.6 (T067), ELF to E16.9 (T066) by R6/R7; the minimal PE linker of T027 suffices for bootstrap | deferred |
| BOOT-30 AArch64 | deferred to P16 (E16.3, planning T216) by R6; tasks/0260 §44 agrees | deferred |
| (modules, FFI, unsafe, host interface, std — needed by the subset) | T060, T065, T061a–T061c, T069–T075, T073a | MS-P7..MS-P9 |
| VERTICAL SLICE #2 begins | — | — |
| BOOT-31 Compiler Frontend in Axiom | T077–T081 (split per module by T076) | MS-P10a |
| BOOT-32 Axiom MIR in Axiom | T082, T083 | MS-P10a |
| BOOT-33 Axiom Backend in Axiom | T084 | MS-P10a |
| BOOT-34 Axiom Object Writer in Axiom | T085 | MS-P10a |
| BOOT-35 Axiom Linker in Axiom | T085 | MS-P10a |
| BOOT-36 Stage-1 Self Compile | T086 | MS-P10a |
| BOOT-37 Stage-2 Bootstrap | T087 | MS-P10b |
| BOOT-38 Reproducible Bootstrap | T087 | MS-P10b |

**AXS-BOOT-061 — Target order.** 0263 §4 picks Linux x86-64 ELF first. That choice is inverted by
the later 0181 (Windows x64 first, AX86TARGET-36) and ROADMAP R6: Windows x64 PE/COFF is the only
target of axiom0; Linux x86-64 ELF is E16.9 after self-hosting. Every "ELF" in 0263 §8-9, §29 and
BOOT-09/10/29 reads "COFF/PE" for axiom0.

**AXS-BOOT-062 — First-test set coverage.** 0263 §32-39 → FP-01..FP-08 (§5): exit 42 (T021/T028),
negative test (T017), MIR test (T019), optimisation test (T043), ABI test (T032/T033), memory test
(T035/T037), ownership test (T046), capability test (T048).

## 8. Core execution semantics by milestone

**AXS-BOOT-070 — Which SPEC-03 rules each milestone owns.** A rule belongs to the milestone of the
feature it applies to; a rule that spans several features is split accordingly.
- MS-P3: AXS-SEM-001..003; 010..012, 014, 015; 020..022; 030; 032..036; 040; 041; 045 for plain
  `let`; 046 for `if` and `while`; 070, 071 and 073 for the compiler-inserted overflow, division and
  shift checks; 080..082; 090; 091. (042 has no MS-P3 part: indexing is MS-P5.)
- MS-P4 (native, AXS-BOOT-007): 030, 071 and 073 for `i32`/`i64` `+ - *` and unary `-`; 080; 081.
- MS-P5: 013 (`char`); 031; 037 for array lengths; 042 (indexing, F-ARRAY); 043 and 044 (F-MUT);
  045 for `let ... else` (F-PATTERN); 046 for `match` and guards (F-ENUM, F-PATTERN); 060..062; 070,
  071 and 073 for bounds, `char`, `assert`, `unreachable` and `panic(msg)`; 072 (`assert` and
  `unreachable` in T034, `panic(msg)` in T041); native support of the rest of MS-P3 (T033, T037,
  T040, T042).
- MS-P6: step 3 of 043 (drop of the old value, T049).
- MS-P7: 037 for const items (T061); the pointer rows of 060; 092 (T061a).
Native support of each rule follows the feature's native task in §4.

## 9. Exact self-host subset

Reserved for T003a (ROADMAP R7): the feature-by-feature list of what axiom0 must support to compile
axiomc, the tasks/0260 §3 in/out table, the self-host std subset, and `spec/selfhost-subset.tsv`.
Until T003a lands, §4 is the list of core features and anything not in it is outside axiom0.

## Sources
0263 §4-12, §20-45, §49-51; 0264 §18-20; tasks/0262 §1, §13-19, §50, §55; tasks/0260 §3-4, §41,
§44, ABOOT-41..80; tasks/0494 §3, §41, §62-65; 0181 §15-16, §31, §38-42; 0152 §80-81; ROADMAP
R1-R9; ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006, ADR-0011, ADR-0012; audit
`_workspaces/audit/2026-09-30/A2-ladder.md` (step map, A2-01, A2-07, A2-10).
