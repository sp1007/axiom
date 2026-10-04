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
  E22.*) add an area by editing this table first (AXD-022).
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
for tooling (LSP, E19.1). `note` and `help` are not severities: they are text attached to a
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
(T018 parser, `tests/verify`) gets plain `AX_VERIFY_*` errors and exit code 1.

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
`related` links (reserved for E19.4).

## 7. Fix-it model

**AXD-055 — Fix.** A fix is `{message, applicability, edits}`. Each edit is `{span, replacement}`,
where `replacement` is UTF-8 text and may be empty for a deletion. In v0.1 all edits of one fix are in
the file of the primary span, do not overlap, and are sorted by `start`.

**AXD-056 — Applicability.** (tasks/0360 §9, ADIAG-30/32; 0146 §11-12)
- `machine-applicable`: applying the edits keeps the program's evident intent and removes the
  diagnostic. Tools may apply it without asking. Required property, tested by T009 and T010: re-checking
  the source after all machine-applicable fixes are applied does not report the original diagnostics again.
- `maybe-applicable`: the edit is probably right but changes meaning in some cases. A human or agent
  must confirm it.
- `manual-review`: an edit is shown as an example only.
A suggestion that is only a heuristic carries no fix: it goes in `helps` (0146 §12). A fix never
suggests something the language forbids, such as `&x` or `::` (ADIAG-84/85).

**AXD-057 — The compiler never applies fixes.** `check`, `build` and `run` never modify source files
(tasks/0360 §10, ADIAG-31). Applying fixes is a tooling feature (E19.4).

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
| `AX_LEX_INT_OVERFLOW` | integer literal above 2^64 − 1 | `18446744073709551616` (E16) |
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

### 10.4 TYPE (tasks T017, T021/T028 for the entry point, T034 for floats)

| Code | Sev | Meaning | Example |
|---|---|---|---|
| `AX_TYPE_MISMATCH` | E | expression type differs from the expected type | `return true` in a function returning `i32`; `data.expected`, `data.found` |
| `AX_TYPE_UNKNOWN` | E | the type cannot be inferred; add an annotation | `let xs = []` |
| `AX_TYPE_NOT_CALLABLE` | E | callee is not a function | `let x = 1` then `x(2)` |
| `AX_TYPE_ARG_COUNT` | E | wrong number of arguments | `f(1, 2)` where `fn f(a: i32)`; `data.expected`, `data.found` |
| `AX_TYPE_RETURN` | E | body can reach its end without producing the declared non-unit value | `fn f(c: bool) -> i32 { if c { return 1 } }` |
| `AX_TYPE_OPERATOR` | E | operator not defined for these operand types | `true + 1`; `data.operator` |
| `AX_TYPE_LITERAL_OUT_OF_RANGE` | E | integer literal does not fit its type | `let b: u8 = 300` |
| `AX_TYPE_NEG_UNSIGNED` | E | unary minus applied to an unsigned type | `let n: u32 = -1` |
| `AX_TYPE_INVALID_CAST` | E | `as` cast between types SPEC-03 does not allow | `true as u8 as bool` (cast to `bool`) |
| `AX_TYPE_NEVER_RETURNS` | E | a function declared to return `never` can return normally | `fn fail() -> never { }` |
| `AX_TYPE_MAIN_MISSING` | E | the root file has no `fn main` (build/run) | a file containing only `fn f() {}` |
| `AX_TYPE_MAIN_SIGNATURE` | E | `main` signature not allowed by SPEC-03 | `fn main(x: i32) -> i32 { x }` |
| `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` | E | valid Axiom outside the axiom0 subset (AXD-013) | `let x = 1.5`; `static N: i32 = 1`; `@at(0x1000) static R: u32`; `data.construct`, `data.epic` |

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
| `AX_TYPE_ASSIGN_IMMUTABLE` | E | T030 | assignment to a binding not declared `mut` |
| `AX_PAT_NONEXHAUSTIVE` | E | T038 | `match` misses patterns (`data.missing` lists them) |
| `AX_PAT_UNREACHABLE` | W | T038 | an arm can never match |
| `AX_PAT_REFUTABLE` | E | T038b | refutable pattern where an irrefutable one is required |
| `AX_MOVE_USE_AFTER_MOVE` | E | T046 | use of a value after it was moved (label at the move) |
| `AX_UNSAFE_REQUIRED` | E | T061a | raw-pointer dereference, pointer arithmetic or unsafe call outside `unsafe` |
| `AX_UNSAFE_INTERP_UB` | E | T061a/T061c | undefined behaviour detected by the oracle (out-of-bounds, dangling or misaligned raw access) |
| `AX_CONST_OVERFLOW` | E | T061 | arithmetic overflow during constant evaluation |
| `AX_CONST_DIV_ZERO` | E | T061 | division by zero during constant evaluation |
| `AX_DRIVER_NO_STD` | E | T060 | no std root found (ADR-0006 §8) |
| `AX_FFI_NOT_IN_ORACLE` | E | T065 | the interpreter reached a direct `extern` call (ADR-0002 §4) |
| `AX_UNSAFE_AT_HOSTED` | E | E13.6 (axiomc) | `@at` placement in the hosted profile (ADR-0001; formerly `AX_ADDR_HOSTED`) |

## Sources
tasks/0360 (BOOTSTRAP-101, frozen: §1-§51, ADIAG-20..90); 0146 Part XXVII §3-§12, §19-§21, §50-§58;
0153 §37 (ADIAG-20..24, APAR-23); 0171 §40 (AKERNEL-27/28/34); 0172 §10-§12; tasks/0260 ABOOT-60..62;
tasks/0262 §46; SPEC-01 §9; SPEC-02 §10; ADR-0001; ADR-0002 §4; ADR-0004 §2; ADR-0005 §2-3, §14;
ADR-0006 §8; ADR-0007; ADR-0011; axiom-c-stage0; axiom-testing.
