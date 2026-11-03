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
  (`AX_PANIC_FORBIDDEN_IN_NO_PANIC`).
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
| `AX_UNSAFE_AT_HOSTED` | E | T504/T525 | `@addr` / `@at` placement on `static` or `fn` in the `hosted` profile without `--freestanding` or `--allow-fixed-addr` (ADR-0001, `SPEC-50` AXS-UNS-023, AXS-UNS-050; formerly `AX_ADDR_HOSTED`) |
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
| `AX_UNSAFE_MISALIGNED_AT` | E | T504/T525 | `@addr(A)` / `@at(A)` has `A == 0` or `A % align_of::<T>() != 0` (`SPEC-50` AXS-UNS-022..024, AXS-UNS-050) |
| `AX_UNSAFE_INVALID_AT_LAYOUT` | E | T504/T525 | `@addr(A)` / `@at(A)` applied to a type with dynamically sized or non-fixed layout (`SPEC-50` AXS-UNS-023..024, AXS-UNS-050) |
| `AX_FFI_UNKNOWN_ABI` | E | T503 | unknown ABI string in `extern "<abi>"` or `@abi(<mode>)` (`SPEC-50` AXS-UNS-031..032, AXS-UNS-050) |
| `AX_FFI_BAD_TYPE` | E | T503 | non-FFI-safe parameter or return type in an `extern "C"` / `"system"` signature (`SPEC-50` AXS-UNS-032..033, AXS-UNS-050) |
| `AX_FFI_INVALID_TRANSPARENT` | E | T503 | `@repr(transparent)` applied to a type that does not have exactly one non-zero-sized field (`SPEC-50` AXS-UNS-031, AXS-UNS-050) |
| `AX_FFI_OPAQUE_BY_VALUE` | E | T503 | opaque foreign type (`extern "C" { type T; }`) instantiated, passed by value, or queried with `size_of` (`SPEC-50` AXS-UNS-033, AXS-UNS-050) |
| `AX_FFI_GENERIC_EXPORT` | E | T503 | `@no_mangle` or `extern "C"` export declared with unmonomorphized type parameters (`SPEC-50` AXS-UNS-032, AXS-UNS-050) |
| `AX_FFI_CAPTURING_CLOSURE_CALLBACK` | E | T503 | closure with non-empty capture environment converted to `extern "C" fn(...)` (`SPEC-50` AXS-UNS-033, AXS-UNS-050) |
| `AX_FFI_VARIADIC_NOT_EXTERN_C` | E | T503 | variadic parameter list `...` used outside an `extern "C"` import declaration (`SPEC-50` AXS-UNS-032, AXS-UNS-050) |
| `AX_TYPE_NOT_A_PLACE` | E | T504 | `address_of(e)` / `address_of_mut(e)` / `addr_of(e)` applied to a temporary rvalue rather than a place expression (`SPEC-50` AXS-UNS-021, AXS-UNS-050) |
| `AX_CAP_CONFLICT_MUT` | E | T125/T501 | `mut_view<T>` overlaps another live `view<T>` or `mut_view<T>` (`SPEC-11`, `SPEC-50` AXS-UNS-005..006, AXS-UNS-050) |
| `AX_CAP_OUTLIVES_OWNER` | E | T125/T501 | `view<T>` or `mut_view<T>` escapes or outlives its backing owner (`SPEC-11`, `SPEC-50` AXS-UNS-005..006, AXS-UNS-050) |
| `AX_CAP_CONTAINER_RELOC` | E | T125/T501 | mutating or reallocating a container (`Vec<T>`, `String`, `HashMap<K, V>`) while an element `view` / `mut_view` is live (`SPEC-11`, `SPEC-50` AXS-UNS-006, AXS-UNS-050) |
| `AX_SIMD_INVALID_ELEMENT` | E | T464 | `Vector<T, N>` instantiated with an element type `T` outside the supported `SimdElement` scalar integer/float set (`SPEC-42` AXS-SIMD-002, AXS-SIMD-060) |
| `AX_SIMD_INVALID_LANES` | E | T464 | `Vector<T, N>` or `Mask<N>` instantiated with a lane count `N` outside `{2, 4, 8, 16, 32, 64}` (`SPEC-42` AXS-SIMD-002, AXS-SIMD-060) |
| `AX_SIMD_LANE_OUT_OF_RANGE` | E | T464 | compile-time constant lane index `idx >= N` in `extract` / `insert` (`SPEC-42` AXS-SIMD-011, AXS-SIMD-060) |
| `AX_SIMD_SHUFFLE_OUT_OF_RANGE` | E | T464 | non-constant shuffle selector array or selector index `>= 2 * N` (`>= N` in single-vector `swizzle`) (`SPEC-42` AXS-SIMD-012, AXS-SIMD-060) |
| `AX_SIMD_BITCAST_SIZE_MISMATCH` | E | T464 | `bitcast` / `simd_bitcast` between vector types of different total byte sizes or involving `Mask<N>` (`SPEC-42` AXS-SIMD-025, AXS-SIMD-060) |
| `AX_TARGET_UNKNOWN_FEATURE` | E | T476 | unknown CPU feature name (or disallowed `-sse`/`-sse2` baseline removal) in `--target-feature`, `@target_feature("...")`, or `@multiversion("...")` (`SPEC-44` AXS-CPU-003, AXS-CPU-010, AXS-CPU-030, AXS-CPU-040) |
| `AX_TARGET_INVALID_ATTRIBUTE` | E | T476/T478 | `@target_feature` or `@multiversion` attached to a non-function item (`struct`, `enum`, `const`, `static`, `extern`), empty `@multiversion()`, duplicate clone feature sets, or `@multiversion` combined with `@target_feature` (`SPEC-44` AXS-CPU-010, AXS-CPU-030, AXS-CPU-040) |
| `AX_TARGET_FEATURE_MISMATCH` | E | T476 | calling a `@target_feature` function or target-gated `std.arch.x86_64` intrinsic (or coercing a `@target_feature` function to `fn(...)`) from a caller lacking the required features without an enclosing `unsafe` block or dominating `is_x86_feature_detected` guard (`SPEC-44` AXS-CPU-011..012, AXS-CPU-040; synonym `AX_SIMD_TARGET_FEATURE_MISMATCH` / `AX_SIMD_TARGET_FEATURE_REQUIRED`) |
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
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | E | T512 | reachable function in `--profile freestanding` or `--profile kernel` transitively requires a forbidden runtime capability (`os_io`, `os_env_process`, `thread`, `blocking`, `async_reactor`, `tls`, `unwind`, or `heap_alloc` without `@global_allocator`) (`SPEC-52` AXS-FRE-022, AXS-FRE-050) |
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

## Sources
tasks/0360 (BOOTSTRAP-101, frozen: §1-§51, ADIAG-20..90); 0146 Part XXVII §3-§12, §19-§21, §50-§58;
0153 §37 (ADIAG-20..24, APAR-23); 0171 §40 (AKERNEL-27/28/34); 0172 §10-§12; tasks/0260 ABOOT-60..62;
tasks/0262 §46; SPEC-01 §9; SPEC-02 §10; ADR-0001; ADR-0002 §4; ADR-0004 §2; ADR-0005 §2-3, §14;
ADR-0006 §8; ADR-0007; ADR-0011; ADR-0036 §4; SPEC-03; SPEC-30; SPEC-31; SPEC-32; SPEC-33; SPEC-40; SPEC-41; SPEC-42; SPEC-43; SPEC-44; SPEC-50; SPEC-51; SPEC-52; SPEC-53; SPEC-54; SPEC-70; SPEC-71; SPEC-72; SPEC-73; SPEC-75; SPEC-76; SPEC-77; axiom-c-stage0; axiom-testing.
