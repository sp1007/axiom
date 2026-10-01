---
id: T001
title: Canonical lexical + grammar spec (= and . rules applied)
phase: P0-foundation
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: opus
depends: []
priority: 10
status: done
attempts: 1
paths: [spec/SPEC-01-lexical.md, spec/SPEC-02-grammar.md, spec/decisions, .claude/skills/axiom-syntax/SKILL.md]
timeout_min: 300
spec: [0154, 0173, tasks/0324, tasks/0476, tasks/0323, 0243, 0084, 0109, 0151]
started: 2026-10-01 08:37:43
finished: 2026-10-01 12:10:00
---
# T001 — Canonical lexical + grammar spec (= and . rules applied)

## Goal
Produce the canonical, implementable lexical specification and complete EBNF grammar for Axiom v0.1 surface syntax, with the owner's decisions applied: `=` is the only binding/assignment spelling (no `:=`, no `var`), `.` is the only path separator (no `::`), `use` is the only import keyword.

## Scope
- SPEC-01-lexical.md: source encoding, whitespace/newline significance, comments (nested /* */, ///), identifiers (Unicode rules or ASCII-first decision), keywords (reserved vs contextual), literals (int bases, suffixes, underscores, floats, strings, escapes, byte strings, chars), operators/punctuation with maximal munch, `..`/`..=` vs float, `p.0.1` tuple index lexing, diagnostics for `::`, `:=`, `var`, `import` with fix-its. Each rule gets an ID AXS-LEX-NNN.
- SPEC-02-grammar.md: complete ISO-EBNF (no `:=`/`::=` notation) for items, statements, expressions (precedence/associativity table; comparisons non-associative), types (`[N]T`, `view<T>`, `mut_view<T>`, `*const T`, fn types, tuples), patterns, generics + where, traits/impls, attributes `@x(...)`, closures, visibility, modules/use with groups and aliases. Newline statement-termination rules precisely (continuation tokens). Generic-argument commit rule in expressions. DottedChain: parser builds it, resolver disambiguates. Rule IDs AXS-GRM-NNN.
- ADRs in spec/decisions/ for every contradiction resolved (at least: `::`→`.`, `:=`→`=`, `var`→`let mut`, `import`→`use`, array type `[N]T`, semicolons optional).
- Grammar admits `@at(<const expr>)` on `static`, `static mut`, `fn` and `extern fn` items (ADR-0001, owner requirement REQ-OWNER-003); semantics are E13.6.
- Example corpus: 20+ small canonical programs inside the spec exercising every construct (they become parser tests).
- Forms the self-host subset needs (ADR-0004 §7, ADR-0006) are specified, not left as "if in spec": labelled loops with `break`/`continue` to a label; literal, char-range (`'a'..='z'`) and or-patterns; `enum as uN` casts for fieldless enums; checked `u32 as char`; `extern "C"` / `extern "system"` items with `@link("name")`; `unsafe fn` and `unsafe { }`; sub-range index forms `s[a..b]`, `s[a..]`, `s[..b]`; `impl Drop for T`; `const` items of aggregate type.

## Acceptance
- [ ] Both files exist; every production referenced is defined; precedence table present.
- [ ] No `::` or `:=` appears in any Axiom example (grep check documented in report).
- [ ] Consistent with .claude/skills/axiom-syntax/SKILL.md (if you refine a rule, update the skill too and list it).
- [ ] Report lists open questions deliberately deferred (with the milestone that needs them).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T001-report.md` with exact `## Files changed`.

## Out of scope
- Semantics (typing, ownership) beyond what syntax needs.

## Notes
- ADRs: reserve the number with `python .claude/skills/axiom-tasks/scripts/taskctl.py adr-next <slug>` (never pick one by listing the directory) and list the ADR file in the report.
- Not a "critical, runs alone" task any more (ADR-0005 §11): it runs in parallel with T004.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-01 08:37:43 started (attempt 1) T001-impl
- 2026-10-01 12:10:00 accepted by QA -> done
