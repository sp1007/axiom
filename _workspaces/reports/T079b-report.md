# T079b report - Port recursive-descent parser to Axiom

## Summary
- `compiler/syntax/parse.ax` is the Axiom port of `bootstrap/axiom0/src/syntax/parse.c`: recursive-descent item,
  statement, type and pattern parsers, the Pratt expression parser, speculative generic-argument parsing with `>>`
  token splitting and rollback, newline-sensitive mode, `@derive` expansion and all of the C parser's error
  recovery. Public entry point: `ax_parse(arena, tokens, token_count, sink, interner) -> ParseResult`.
- Scope change received mid-task (the 1,500-line cap was removed; priority is a complete and readable parser). The
  squeezed first draft (1,498 lines, 66 lines over 120 columns) was therefore regenerated and restructured:
  - one statement per line, no line over 120 columns (checked: 0), blocks expanded, full names (`parser`, `span`,
    `next_kind`, `type_node`, `saved_mode_on`, ...), every function has a doc comment;
  - no magic numbers: token kinds by `TOK_*` name, diagnostic messages by `MSG_*`, identifiers the parser compares
    against by `LIT_*`, derive text fragments by `DERIVE_*`, operator binding power by `PREC_*`;
  - `infix_prec`, `binary_op_for_token`, `unary_op_for_token`, `jump_kind_for_token` are explicit, named mappings;
  - the long functions were split into focused helpers (`parse_primary` into 14 helpers, `parse_item` into 12,
    `parse_expr_prec` into 7 suffix/binary helpers, `parse_pat_no_or` into 6, `parse_type` into 7, `format_derive`
    into one helper per derivable trait); the longest function is 69 lines (`parse_stmt`);
  - Axiom is newline sensitive, so wrapped conditions keep `&&` / `||` at the END of a line (found the hard way:
    the new parser rejects leading operators, exactly like the C parser).
- Layout decision (asked by the coordinator): ONE file. `parse.ax` is 2,922 lines, of which about 500 are the text
  table (messages, identifier literals, derive text, 16 bytes per line) and the named-constant declarations, and
  286 are `use` lines. Splitting into `compiler/syntax/parse/` submodules would force `pub` on every helper
  and a 100+ name cross-module import list per file for no readability gain, and the module/bundling layout used
  by the other `compiler/` ports (single file per C module) fits one file. Record for the architect if a split is
  still wanted.
- `@derive` expansion no longer depends on `ast_format_derive` of `ast.ax`: that function (T079a) emits one `}`
  too few for `Clone` (the generated `impl Clone` was never closed, error `Expected '}'` without a span) and
  mis-handles `Clone` on enums. `parse.ax` has its own `format_derive` family that reproduces the C text exactly
  (including the C behaviour of treating enums like tuple structs for `Clone`). `ast_format_derive` is now dead
  code; see Follow-ups.
- Self-hosting subset: only features axiom0 already supports; no workaround code except two documented axiom0 bugs
  (below) that needed one-line rewrites.

## Files changed
- compiler/syntax/parse.ax
- tests/selfhost/parse/qa_parse_corpus_a.ax
- tests/selfhost/parse/qa_parse_corpus_b.ax
- tests/selfhost/parse/qa_parse_corpus_c.ax
- tests/selfhost/parse/qa_parse_corpus_d.ax
- tests/selfhost/parse/qa_parse_corpus_e.ax
- tests/selfhost/parse/qa_parse_corpus_f.ax
- tests/selfhost/parse/qa_parse_corpus_g.ax
- tests/selfhost/parse/qa_parse_corpus_h.ax
- tests/selfhost/parse/qa_parse_corpus_i.ax
- tests/selfhost/parse/qa_parse_corpus_j.ax
- tests/selfhost/parse/qa_parse_heavy_a.ax
- tests/selfhost/parse/qa_parse_heavy_b.ax
- tests/selfhost/parse/qa_parse_recovery_a.ax
- tests/selfhost/parse/qa_parse_recovery_b.ax
- tests/selfhost/parse/qa_parse_qa_edge.ax
- tests/selfhost/parse/qa_parse_qa_tuple_struct.ax

## Tests
Tests are self-contained bundles (the repo convention: tests cannot import `compiler.*`), each embedding the
lexer/session/AST code, the current `parse.ax` body and `ax_ast_render`, and checking `ax_parse` output
byte-for-byte against `axiom0 inspect --emit=ast` (AST text and human-readable diagnostics) for 38 source files:
28 positive/negative syntax files of `tests/parse/*` and the 10 `tests/ui/parse/*` recovery files, plus the QA
edge-case and tuple-struct regression suites (`qa_parse_qa_edge.ax`, `qa_parse_qa_tuple_struct.ax`).
- `qa_parse_corpus_a..j` (2 cases each, `[interp]`, `[native]`, `[native-O1]`) and `qa_parse_recovery_a/b`
  (5 cases each, all three modes).
- `qa_parse_heavy_a/b` (8 larger cases), `qa_parse_qa_edge` and `qa_parse_qa_tuple_struct` are `// modes: native`
  (heavy multi-case bundles with small interp twins in `corpus_a..j` and `recovery_a/b`).
- Round 1 fix for F1 (flaky `AX_UNSAFE_INTERP_UB: out-of-bounds pointer access` in `[interp]` under parallel load):
  in `bootstrap/axiom0/src/interp/interp.c`, `@intrinsic` calls (`wrapping_mul_u64`, `wrapping_add_u64`,
  `rotate_left_u64`) increment `ctx->call_depth` on entry without decrementing it on return, which prevents
  `exec_mir_body` from retiring stack-local `ctx->allocs` entries when frames return. When the C heap reuses a freed
  `frame.storage` address for a later frame, `find_synth_addr` (linear scan from index 0) could match a stale 8-byte
  local before reaching the live 56-byte `StrInterner` local. In Round 1, `CompilerSession`, `parse_arena`, `out_ast`
  and `out_err` are owned directly by `main` and passed by `mut_view` into `verify_case`/`run_and_verify_parse`.
  Because `main`'s locals are registered first (`alloc_id` 24..30 at `call_depth` 1) and stay live for the entire
  program, `find_synth_addr` deterministically matches `main`'s live allocation first regardless of heap reuse.
- Round 1 fix for F2 (tuple-struct divergence vs `parse.c`): `bootstrap/axiom0/src/syntax/parse.c:1630-1636` has a bug
  where `*curr = parse_type(p);` is called twice in the tuple-struct field loop, rejecting valid tuple structs like
  `struct T(u8);`. `compiler/syntax/parse.ax` (`parse_struct_item`) parses the type list once as required by
  `spec/SPEC-02-grammar.md` AXS-GRM-029; this intentional bug-fix difference against `parse.c` is documented below and
  locked in by `tests/selfhost/parse/qa_parse_qa_tuple_struct.ax`.
- Snapshot run (`axtest selfhost/parse`): `TOTAL 44 PASS 44 FAIL 0` across repeated parallel runs;
  `python tools/archcheck.py` -> 0 violations.
- Interp wall time of every parse test: 1-9 s alone (timeouts 60-90 s).
- Extra differential evidence (not committed; throwaway harnesses in the session scratchpad): the Axiom parser
  compiled natively against `axiom0 inspect --emit=ast` on every `.ax` under `tests/` (707 files below 20 KB,
  stdout AND stderr): 689 identical. The 18 non-identical files: 11 in `tests/modules/*/src/*.ax` (the C driver
  prepends a synthetic `ItemModule` for project discovery; not parser output) and 7 where the Axiom *lexer*
  panics (see Follow-ups). Plus 4,800 mutated files (truncate / delete / insert tokens / swap lines, seeds 1-8,
  tokens from the whole grammar): all identical except cases where the C compiler itself is wrong (see below).
  `compiler/syntax/ast.ax`, `compiler/lex/token.ax`, `compiler/diag/format.ax`, `compiler/kernel/arena.ax`,
  `compiler/source/manager.ax`, `std/core/host.ax`, `std/io/io.ax` parse identically too.
- Intentional differences vs C `parse.c`:
  1. When an expected name is missing the C parser reads the stale `ident_val` of the non-identifier token
     (uninitialised union member, e.g. `(Param false "main")`); the Axiom parser stores id 0 (`""`). In some mutated
     inputs the C compiler also dies with `internal compiler error: ax_interner_get: invalid StrId 0` where the Axiom
     parser recovers normally.
  2. Tuple structs (`struct T(u8, i32);`): `parse.c:1630-1636` calls `parse_type` twice per element by mistake;
     `parse.ax` parses each tuple-struct field type once per `SPEC-02` AXS-GRM-029 (`qa_parse_qa_tuple_struct.ax`).

## Spec deviations
none. (`parse.ax` follows `SPEC-02` AXS-GRM-029 on tuple structs where `parse.c` had a duplicate `parse_type` call;
`SPEC-20` AXS-SELF-004 hard 1,500-line cap was removed in commit `a852563`.)

## Follow-ups
1. axiom0 MIR interpreter, performance and `call_depth` leak: `ax_interp_register_alloc` appends to `ctx->allocs` for
   every heap block AND every stack local of every call, and `eval_call` forgets `ctx->call_depth--` when returning
   from arithmetic `@intrinsic` functions (`wrapping_add`, `wrapping_mul`, `rotate_left`, etc.), so frames that call
   intrinsics never retire their stack allocations on return.
2. axiom0 MIR interpreter, bug (minimised, `AX_UNSAFE_INTERP_UB: pointer arithmetic on pointer outside live
   allocation`): updating a nested field through a raw pointer with a computed value,
   `(*p).span.start = (*p).span.start + 1u32;` (`p: *mut Tok` from `address_of_mut`). `= 7u32`, or
   `let s1 = (*p).span.start + 1u32; (*p).span.start = s1;` work in the interpreter. `split_gt` in `parse.ax`
   therefore uses the split form (`let s0 = ...; let s1 = s0 + 1u32; ... = s1`).
3. Lexer (T078, `compiler/lex`): `panic: arithmetic overflow` while lexing larger files (first 512 lines of
   `tests/std/bytes/qa_byte_buf.ax` pass, 513 lines = 15,296 bytes panic; also `tests/run/host/fs/dir.ax`,
   `tests/std/text/qa_string_builder.ax`, `qa_text_roundtrip.ax`, `tests/std/utf16/*` x3). Reproduces without the
   parser (lex only). `compiler/lex/scanner.ax`/`token.ax` is the suspect (token or comment buffer growth).
4. `compiler/syntax/ast.ax` (T079a): `ast_format_derive` is wrong for `Clone` (missing `}`, enums not treated like
   tuple structs) and now unused; delete it (and its `AST_TAG_*` derive entries) or fix it. Also
   `compiler/diag/code.ax` packs several `pub const` items per line (formatting only, not touched).
5. axiom0 C parser: reads an uninitialised/stale `ident_val` for missing names, can ICE
   (`ax_interner_get: invalid StrId 0`) on malformed input, and calls `parse_type` twice per element in tuple structs
   (`bootstrap/axiom0/src/syntax/parse.c:1630-1636`); frozen compiler, so only an `AX0-FIX` task if wanted.
6. Language/tooling notes found while writing the tests: `view(CONST)` is rejected (`AX_CAP_OUTLIVES_OWNER`), so
   tests copy the const to a local first, and copying a 400 KB const array onto the stack overflows the native
   stack (corpus differential harnesses must keep test data under ~100 KB per file).

STATUS: COMPLETE round=1
