# T001 report

## Tóm tắt
Đã viết hai spec chuẩn cho cú pháp Axiom v0.1: `spec/SPEC-01-lexical.md` (lexer, 56 quy tắc
`AXS-LEX-NNN`, 19 mã lỗi `AX_LEX_*`) và `spec/SPEC-02-grammar.md` (ngữ pháp ISO-EBNF đầy đủ, 113
production, 87 quy tắc `AXS-GRM-NNN`, bảng ưu tiên toán tử, 26 chương trình mẫu + 1 mẫu S1). Quyết định
của chủ dự án được áp dụng xuyên suốt: chỉ `=` cho gán/khai báo, chỉ `.` cho đường dẫn, `use` là từ
khoá import duy nhất. Bốn ADR ghi lại mọi mâu thuẫn đã giải quyết: ADR-0007 (chính tả `=`, `.`, `use`,
`module`), ADR-0008 (kết thúc câu lệnh bằng xuống dòng hoặc `;`), ADR-0009 (các quyết định lexer),
ADR-0010 (các dạng ngữ pháp). Hai điểm được đánh dấu **Revisit** để chủ dự án xem lại: định danh tạm
thời chỉ dùng ASCII (tên biến tiếng Việt dời sau self-host; chuỗi/ký tự/chú thích vẫn UTF-8 đầy đủ) và
không có nội suy chuỗi. Skill `axiom-syntax` đã được cập nhật cho khớp.

## Summary
- **SPEC-01** (lexical): UTF-8 source, BOM, byte spans; whitespace = space/tab/CR/LF, LF is the line
  terminator; **no newline token** — every token carries `NL_BEFORE` (AXS-LEX-013); nested block
  comments, `///` doc comments as trivia; ASCII identifiers (ADR-0009 §1, Revisit); 37 keywords + 3
  reserved words; integer bases, `_` separators, type suffixes, floats (`1.0`, `1e10`, `2.5f32`),
  the `1..2` / `1.max(2)` / `p.0.1` rules (AXS-LEX-056, AXS-LEX-057); strings, raw strings, byte
  strings, chars, byte literals (`b'a'` = `u8` integer token), labels (`'outer`); 47 punctuation /
  operator tokens with maximal munch; `::` and `:=` recognised only to report `AX_LEX_COLON_COLON` /
  `AX_LEX_COLON_EQ` with fix-its and recover as `.` / `=`; token kind names; scanning order;
  diagnostics table; 14 + 16 normative token examples for T010.
- **SPEC-02** (grammar): notation and staging (S0 = parsed by axiom0, S1 = `async`/`.await`/`comptime`
  reserved and rejected by axiom0 with `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP`); the statement-termination
  rule with a 22-row continuation matrix (AXS-GRM-010..019); items (fn, struct, enum, trait, impl,
  type alias, const, static, extern blocks, attributes, visibility, `use` groups/aliases, `module`);
  statements (let, `let … else`, assignment as a statement, block tail value); expressions with the
  precedence table (AXS-GRM-050), non-associative comparisons, `DottedChain` (AXS-GRM-055), the
  generic-argument commit rule (AXS-GRM-056), `>>` splitting, struct literals and the header
  restriction, closures, labelled loops, jump expressions, `view(x)`/`mut_view(x)`, sub-range index
  forms; types (`[N]T`, `[T]`, `view<T>`, `mut_view<T>`, `*const T`/`*mut T`, fn types, tuples,
  `dyn`); patterns (wildcard, binding, literal, char/integer ranges, or-patterns, variants, structs,
  tuples, guards); recovery rule and 25 `AX_PARSE_*` codes; `var` / `import` / `mod` diagnostics with
  fix-its; 15 rejected-spelling cases; example corpus EX-01..EX-26 and EX-S1 with a coverage table.
- Self-host forms required by the task are all specified, not left open: labelled `break`/`continue`
  (AXS-GRM-065/066), literal / char-range / or-patterns (AXS-GRM-093/094/098), `enum as uN`
  (AXS-GRM-030/054), checked `u32 as char` (syntax: AXS-GRM-054; EX-20), `extern "C"` /
  `extern "system"` with `@link` (AXS-GRM-036; EX-18), `unsafe fn` / `unsafe { }` (AXS-GRM-025/068),
  `s[a..b]`, `s[a..]`, `s[..b]` (AXS-GRM-070), `impl Drop for T` (AXS-GRM-032; EX-14), aggregate
  `const` (AXS-GRM-034; EX-20). `@at(<const expr>)` is admitted on `static`, `static mut`, `fn`,
  `extern fn` (AXS-GRM-037; EX-19).
- **ADRs** (numbers reserved with `taskctl.py adr-next`): ADR-0007 `::`→`.`, `:=`→`=`, `var`→`let mut`,
  `import`→`use`, `mod`→`module`, no turbofish; ADR-0008 optional semicolons / newline rule; ADR-0009
  lexical decisions (9 items); ADR-0010 grammar forms (11 items, incl. array type `[N]T`).
- **Skill** `.claude/skills/axiom-syntax/SKILL.md` refined to match the specs (see Spec deviations).

Key decisions beyond the owner's two rules (each with options and rationale in the ADRs):
1. Newline termination is a parser rule on a lexer flag; only a leading `.` (and `else`) continues a
   line; other leading operators are errors, never reinterpreted (ADR-0008).
2. Bitwise operators bind tighter than comparisons, one non-associative comparison level, `as` just
   below prefix operators (ADR-0010 §2) — needed for `status & MASK == 0` (ADR-0001 example) and for
   the generic-argument rule.
3. Assignment is a statement (ADR-0010 §3); `return`/`break`/`continue` are `never`-typed expressions.
4. `view` and `mut_view` are keywords; `view(x)` is a dedicated place form (ADR-0009 §2).
5. Receivers always carry a type (`self: view<Self>`); no `move` closures; no items in blocks.
6. Fixed array `[N]T`, unsized sequence `[T]` behind a view (`view<[u8]>`, the corpus and T048b form).
7. Identifiers ASCII-only in v0.1 (Revisit); no string interpolation (Revisit).

## Files changed
- spec/SPEC-01-lexical.md
- spec/SPEC-02-grammar.md
- spec/decisions/ADR-0007-canonical-spelling-binding-paths-imports.md
- spec/decisions/ADR-0008-statement-termination-newline.md
- spec/decisions/ADR-0009-lexical-decisions-v0-1.md
- spec/decisions/ADR-0010-grammar-forms-v0-1.md
- .claude/skills/axiom-syntax/SKILL.md

## Tests
Spec-only task: the repository has no build or test suite yet (T004/T005 not done), so "full test
suite / warning-free build / archcheck" have nothing to run. Checks performed:

1. **Forbidden spellings in Axiom examples** (acceptance 2). Command, run from the repository root:
   `awk '/^```axiom/{f=1;next}/^```/{f=0}f' spec/SPEC-01-lexical.md spec/SPEC-02-grammar.md spec/decisions/ADR-*.md .claude/skills/axiom-syntax/SKILL.md | grep -cE '::|:='`
   → `0` (810 lines of Axiom: 32 `axiom` blocks in the two specs and the skill, the rest in ADR-0001). The
   same extraction over the `ebnf` blocks gives 0 uses of `:=` / `::=`. The only occurrences of the
   two spellings in the specs are inline code in diagnostics text and tables (rejected forms).
2. **Every production referenced is defined** (acceptance 1): a script extracted all `ebnf` blocks —
   SPEC-01: 28 productions, 0 undefined; SPEC-02: 113 productions, 0 undefined, only `SourceFile`
   unreferenced (the start symbol); no production defined twice. Token classes used as terminals
   (`IDENT INT FLOAT STR BYTE_STR CHAR LABEL EOF`) are all defined in SPEC-01 §7.
3. **Reference implementation check.** A throw-away lexer + recursive-descent parser written from the
   two specs (Python, kept in the session scratchpad, not part of the repository) parses all 32
   `axiom` blocks of SPEC-01, SPEC-02 and the skill with zero diagnostics; EX-S1 in bootstrap mode
   gives only `AX_PARSE_UNSUPPORTED_IN_BOOTSTRAP`; the continuation matrix N01–N22 (all rows but N20),
   the rejected spellings R01–R15, nine generic-argument / assignment cases and the 30 lexer rows of
   SPEC-01 §10 (L12 by byte count) plus five extra literal cases produce exactly the tokens and
   diagnostics the specs state. This found and fixed one real
   inconsistency before delivery (the skill's `@at` example had a statement at item level).
4. Rule ids: 56 `AXS-LEX`, 87 `AXS-GRM`, no duplicate, no reference to an undefined id; keyword list
   in SPEC-01 = 37 words = 37 `Kw*` kinds (+3 reserved); 47 punctuation tokens = 47 kind names.
5. All seven files: UTF-8, LF only, final newline.
6. `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`;
   `taskctl.py validate` → `OK (155 tasks)`.

## Spec deviations
Refinements of the binding skill (the skill was updated in the same change, as the task requires):
- Rule 3 "statements end at newline when unambiguous" is now the exact rule of ADR-0008; added: other
  leading operators are errors, `return`/`break` operands must start on the same line.
- Assignment is a statement, not an expression (ADR-0010 §3) — new in the skill.
- "chars `'a'` if enabled by the lexical spec" → enabled; added byte literals, raw strings, the
  keyword list, `view`/`mut_view` as keywords, ASCII identifiers, no interpolation, precedence line,
  receiver rule, labels, pattern forms, slice type `view<[T]>`.
- The skill's Rule 4 example put the statement `UART0.ctrl = …` at item level; it is now inside a
  function, and `[48]fn() = [reset, nmi, hard_fault]` became `[3]fn()` to match its initialiser.
- The skill no longer says it "wins until the architect reconciles": `spec/` is authoritative
  (axiom-spec-index order), the skill is the summary.

Deviations from the corpus are all recorded in ADR-0007..0010 with sources. Two are flagged
**Revisit: yes** for the owner: ASCII-only identifiers (ADR-0009 §1) and no string interpolation
(ADR-0009 §9). No OWNER.md requirement is dropped or re-sequenced.

Process note: my first call `taskctl.py adr-next --help` (meant to read the usage) reserved ADR-0007
with the slug `help`; I renamed that stub file to the intended slug and used the number. No number was
picked by hand and no gap exists (0007–0010).

## Open questions deliberately deferred
(Full tables: SPEC-01 §12, SPEC-02 §12.)

| Question | Milestone that needs it |
|---|---|
| Unicode identifiers (XID, NFC-required, no silent normalisation) | E21.2 supplies the tables (planning T221); decide before spec freeze E23.2 / T091 |
| String interpolation (prefixed literal), multi-line and `#`-delimited raw strings | language-completion planning T214; before E23.2 |
| `i128`/`u128` suffixes and literals above 2^64 − 1 | E12.1 (T212) |
| Float literal value conversion; float typing | E12.2 (T212) |
| `async fn`, `.await` (grammar fixed, S1), `async { }` blocks | E11.4 (T211 / T088) |
| `comptime fn`, `comptime { }` (grammar fixed, S1), item-level comptime, const generics | E14.1 (T214) |
| `dyn Trait` semantics (parsed in S0) | E14.4 (T058) |
| `static` / `static mut` semantics (parsed in S0), `@at` semantics | E13.3, E13.6, E13.7 (T213) |
| `move` closures / capture lists; `union`; generators and `yield` (words reserved) | E11.1, E13.2, E14.3 |
| Fully qualified trait paths; wider follower set for generic arguments | T055/T056, T054 — new ADR only if needed |
| Local items in blocks; struct update `..base`; explicit enum discriminants; `impl Trait` types | T214 (discriminants: E13.2) |
| Patterns: binding-at, slice, string/float literals, `..` in tuples, parameter patterns | T214 |
| Glob imports, nested `use` groups | E20.1 (T220) |
| Variadic `extern` functions, more ABI strings | E13.1 / P16 (T213, T216) |
| Doc-comment forms `/** */`, `//!` and attachment rules | E19.5 (T219) |
| Named / default arguments, labelled blocks, inline modules | not scheduled (syntax kept free) |

## Follow-ups
No new task is needed. Wording alignments for tasks that consume these specs (I did not edit task
files — they are outside this task's `paths`; the architect/orchestrator can apply them as notes):
- **T010**: the goal says "newline tokens where significant" — the spec defines a per-token
  `NL_BEFORE` flag and no newline token (AXS-LEX-013). Token kinds also include byte literals
  (`b'a'` → `Int`, suffix `u8`), raw strings (`r"…"` → `Str`), `Label`, `Underscore`; kind names are
  fixed in AXS-LEX-092; the 19 `AX_LEX_*` codes are in AXS-LEX-100 (T010's examples
  `AX_LEX_INVALID_UNICODE_ESCAPE`, `AX_LEX_BAD_CHAR_LITERAL` are kept).
- **T011**: `let … else`, struct-literal field shorthand, the S1 diagnostic for `async`/`comptime`,
  `AX_PARSE_MOD`, `AX_PARSE_LEADING_OPERATOR`, `AX_PARSE_ITEM_IN_BLOCK` belong to the core parser;
  assignment is an AST statement node, not an expression node.
- **T012 / T015b**: `p->field` is parsed as a chain segment and lowered to `(*p).field`; the
  array/slice type disambiguation is AXS-GRM-083; the identifier-pattern rule is AXS-GRM-092 (resolver).
- **T002**: register the `AX_LEX_*` (AXS-LEX-100) and `AX_PARSE_*` (AXS-GRM-101) codes as the seed
  list of areas LEX and PARSE.
- **T003 / T003a**: SPEC-00/SPEC-03 decide subset membership and typing of: `~`, byte literals (plain
  `u8` integers after the lexer), raw strings, `->`, negated-literal range check (`-128i8`), which S0
  constructs are rejected after parsing (`static`, floats, `dyn`, `@at`).
- **T048b**: uses the spec form `view<[T]>` — consistent, no change.

## Round 1

Fixes for the gate verdict FAIL round=0 (`_workspaces/reports/T001-qa.md`). No decision changed; the
record, two under-specified rules and three summaries were corrected. Note on the round-0 text above:
its statement that the precedence order follows 0243 / 0155 / 0173 was wrong (F1); counts quoted
there (matrix rows, lexer rows) are superseded by the numbers below.

**F1 — precedence citations (accepted; QA was right, I had misread the three tables).**
- ADR-0010 §2 now says: the C order (bitwise looser than comparison, two comparison levels) is given
  by 0243 §35, 0155 §35, 0173 §30, tasks/0324 §28 and tasks/0476 §136; the adopted order (bitwise
  tighter, one comparison level, `as` near unary) is that of **0109 §92** only, chosen *against* the
  five others, with the unchanged rationale (no implicit truthiness, ADR-0001 example, tasks/0476
  §136 is "conceptual", §137 only requires a fixed table). Sources line gains 0109 §92.
- AXS-GRM-050 source tag: `[0109 §92 (the order adopted); ADR-0010 §2 — decided against the C order
  of 0243 §35, 0155 §35, 0173 §30, tasks/0324 §28 and tasks/0476 §136; tasks/0476 §137-138]`.

**F2 — label after `break` / `continue` across a line break.**
- AXS-GRM-015 is now "Labels and operands of jumps": in mode ON a `LABEL` is taken by `break` /
  `continue` only without `NL_BEFORE`; the operand rule is unchanged; mode OFF ignores the flag.
- AXS-GRM-017 lists "the label and operand of `return`, `break` and `continue`" among the places
  where the flag is consulted; AXS-GRM-066 points to the same-line rule; ADR-0008 §6 and ADR-0010 §4
  state it.
- Matrix rows added: N23 (`break` ↵ `'a: loop { }`), N24 (`continue` ↵ …), N25 (`break 'a` ↵ `x`).

**F3 — leading-operator wording.**
- Skill Rule 3, the SPEC-02 `## Tóm tắt` line and the ADR-0008 `## Tóm tắt` now say: an operator that
  can only be binary/postfix at line start is an error; `-`, `*`, `!`, `~`, `|`, `||`, `(`, `[`, `{`
  at line start begin a **new statement with no diagnostic** (`let d = a` ↵ `- b` is two statements).
- AXS-GRM-019 states "without any parser diagnostic" and how to continue (operator at the end of the
  previous line, or parentheses); matrix row N26 added; ADR-0008 Consequences records this as the one
  silent case and names the lint follow-up.

**F4 — exact lexer diagnostic counts.**
- AXS-LEX-101 is now "Recovery and diagnostic count": a numeric literal reports each code at most
  once, at its first place; different codes may combine (`0b12_` → `AX_LEX_INVALID_DIGIT`,
  `AX_LEX_BAD_DIGIT_SEPARATOR`); `AX_LEX_MISSING_DIGITS` suppresses `AX_LEX_BAD_DIGIT_SEPARATOR`; a
  literal with another error is not checked for overflow; quoted literals report one diagnostic per
  bad escape / non-ASCII byte plus at most one of unterminated / bad-char; emission order is source
  order.
- AXS-LEX-051: only the first bad underscore run of a literal is reported. AXS-LEX-053: a prefix with
  no digit at all (`0x`, `0x_`, `0b__`) reports only `AX_LEX_MISSING_DIGITS`; `0x_ff` reports only
  `AX_LEX_BAD_DIGIT_SEPARATOR` (value 255).
- AXS-LEX-061: a `\` directly before CR, LF or end of file is not an escape and reports nothing by
  itself; the literal is unterminated and the `\` is inside its span.
- SPEC-01 §10 rows added: E17 `0x_`, E18 `0x_ff`, E19 `0b12_`, E20 `1__0__0`, E21 `"abc\` + LF,
  E22 two bad escapes, E23 `'\` at end of file. ADR-0009 §4 mentions the count rule.

**Minor notes.**
- `ASYNTAX-nn` ids in ADR-0009 / ADR-0010 / SPEC-02 are prefixed with their document (tasks/0323 or
  tasks/0476).
- AXS-LEX-030 names the exact prefixes (`b"`, `b'`, `r"`); `r'x'` and `br"…"` are not prefixed literals.
- AXS-GRM-046 lists `async` / `comptime` followed by `fn`, `unsafe` or `extern` as an item start.
- ADR-0010 §9: tasks/0476 §78 lists `private` among its forms; the default-private rule is cited from
  tasks/0323 §87 and `private` / `internal` are stated as not Axiom.
- ADR-0009 §2: "six different lists".
- AXS-GRM-083: the corner `p as *const [u8] * n` (read as an array type) is stated, with the
  parenthesised form as the way out.

**Checks after the edits.**
- The reference lexer/parser was rewritten from the specs (the round-0 source had been overwritten;
  scratchpad only). Results: all 32 `axiom` blocks parse with zero diagnostics; N01–N19, N21–N26,
  R01–R15, the nine generic-argument / assignment cases, L01–L14 and E01–E23 give the stated tokens,
  statement counts and diagnostics, plus 12 extra rows (`0x`, `0b__`, `0X_`, `r'x'`, `"abc\` at end
  of file, `break 'a`, `continue 'a`, `async fn` / `comptime fn` in a block, N20).
- QA's independent checker (`qa-T001/run_qa.py`) on the main tree: `RESULT: OK (0 failures)` (it
  does not cover the new rows E17–E23 and N23–N26).
- EBNF closure unchanged (28 + 113 productions, 0 undefined); 56 `AXS-LEX` and 87 `AXS-GRM` rules,
  no duplicate, no dangling reference; grep check for `::` / `:=` in `axiom` blocks → 0; all files
  LF-only; `harness_check.py` → `HARNESS OK`.

**Follow-up added (architect, not this task's paths):** an "unused value / suspicious leading
operator" lint for the N03 / N26 case (`a` ↵ `- b`), to be placed in T031 or E19.4.

Round 1 edited SPEC-01, SPEC-02, ADR-0008, ADR-0009, ADR-0010 and the skill; ADR-0007 is unchanged
since round 0. The complete list for the task is repeated below.

## Files changed
- spec/SPEC-01-lexical.md
- spec/SPEC-02-grammar.md
- spec/decisions/ADR-0007-canonical-spelling-binding-paths-imports.md
- spec/decisions/ADR-0008-statement-termination-newline.md
- spec/decisions/ADR-0009-lexical-decisions-v0-1.md
- spec/decisions/ADR-0010-grammar-forms-v0-1.md
- .claude/skills/axiom-syntax/SKILL.md

STATUS: COMPLETE round=1
