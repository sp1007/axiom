# T147 report - AX0-FIX-05 object-local string/panic data symbols and index-based local-symbol linking

## Summary
- Both compilers now name compiler-generated data symbols by ADR-0035 section 1 and both linkers bind same-object
  references by symbol index (section 2).
- **axiom0**: new `driver/build_native/data_syms.{c,h}` is the single code path for string literal data, used by
  `build`, `build --emit=obj` and `inspect --emit=obj` (`build.c`, `emit_obj.c`). Each literal is emitted NUL-terminated
  and padded to 8 bytes as one STATIC symbol `.Lstr.<f>.<k>` (`f` = emission-order ordinal of the function body,
  `k` = isel `sym_id`), defined once, no undefined twin; the `lea` operand is rewritten to the symbol's own id, so the
  COFF relocation targets that symbol's index. Panic data is `.Lpanic.<n>` (STATIC, per-object counter; the
  process-wide `static int` is gone). The `.Lcstr_<n>` counter of the const tables is per object too (was `static`).
  `emit_obj.c` also passed a stack buffer as a symbol name (dangling); fixed by sharing the code path.
- **axiom0 linker** (`link/pe/linker.c`): a relocation whose target has SectionNumber > 0 is bound to that symbol's
  merged section + offset at load time (`add_reloc_direct`); only EXTERNAL definitions enter the global table
  (duplicates still `AX_LINK_DUPLICATE_SYMBOL`); undefined EXTERNAL resolves by name. Aux-record slots of the
  per-symbol arrays are now initialised.
- **Port**: `compiler/backend/session.ax` (`backend_emit_fn_strings_rdata` takes `fn_ordinal`, new
  `alloc_str_data_sym`, `.Lpanic.` table entry, both call sites pass the ordinal, `session_emit_objmodel_hir` uses a
  panic counter separate from the const-table counter like `build.c`), `compiler/driver/pipeline.ax` (`.Lpanic.<n>`,
  STATIC, ordinal = emission index), `compiler/link/pe.ax` (`PeReloc.dsec/doffset`, `linker_add_reloc_direct`),
  `compiler/link/linker.ax` (per-symbol section/offset arrays; STATIC symbols no longer enter the global table;
  direct relocations; the old "first definition wins" STATIC registration is removed), `compiler/link/mod.ax` export.

## Tests added / changed
- `tests/run/parity/strings/multi_fn_literals.ax` (interp native): five literal functions (ASCII, empty, UTF-8,
  embedded `\0`, 135-byte) + a destructor that prints; `stdout:` derived by hand.
- `tests/run/parity/strings/fn_literals_plain.ax`: literals in three functions, no Drop; added to the
  in-process corpus of `qa_obj_link_driver_diff.ax` (lifts T085's "string-free programs only" restriction): the port
  builds it byte-identically to axiom0 (objects and images).
- `tests/link/local_symbols/` (`local_symbols.test`): hand-built COFF objects (Python, from the PE/COFF spec): two STATIC
  symbols named `.Lk` at different `.rdata` offsets referenced from two functions plus an EXTERNAL data symbol; linked by
  the axiom0 linker through `cdriver_link_objs.c`, image must exit 167 (3 + 4*5 + 16*9); a second object defining
  `ext_k` again must fail with `AX_LINK_DUPLICATE_SYMBOL`. Mutation: disabling the index binding makes it fail.
- `tests/selfhost/link/gen_local_symbols_test.py` -> `qa_pe_local_symbols.ax` (native): the same objects through the real
  `compiler/obj` + `compiler/link` sources; image written, run, exit code 167; duplicate EXTERNAL diagnostic code.
  Mutation: with HEAD's `compiler/link` the image exits with the wrong code (test rc 13).
- `tests/obj/determinism/` (`string_symbols.test`): for every `tests/run/str/*` and `tests/run/parity/strings/*` program,
  `build --emit=obj`, `build`, `inspect --emit=obj` each run twice are byte-identical; every `.Lstr.*` symbol matches
  `.Lstr.<f>.<k>`, is defined once, STATIC, with no undefined twin.
- `tests/run/numeric/qa_t140_edge_matrix.ax` restored to the T140 string-literal form (git `bda91be`); directives and
  numeric checks unchanged; passes interp/native/native-O1 and is byte-identical under axiomc_e2e.

## Regenerated bundles (ADR-0034 section 2)
- `tests/selfhost/backend/qa_backend_{unit,edge,diff_lir_a,diff_lir_b,diff_mi_mc_a,diff_mi_mc_b}.ax` via
  `gen_backend_tests.py`: embed the changed `compiler/backend/session.ax`; `harness_backend_edge.ax.in` / generator blobs
  updated (`.Lstr.0.100000`, `.Lpanic.10`, new `fn_ordinal` argument).
- `tests/selfhost/driver/qa_driver_{commands_a,commands_b,inspect_diff_a,inspect_diff_b}.ax` via `gen_driver_tests.py`: embed
  changed `session.ax`, `pipeline.ax`, `compiler/link`; expected axiom0 bytes re-captured (string symbol names).
  `qa_driver_cli_and_project.ax` and `qa_driver_boundary_edges.ax` are unchanged by the generator.
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}.ax` via `gen_obj_link_driver_tests.py`: same reasons
  plus the new corpus program.
- `tests/selfhost/link/qa_pe_linker_diff.ax` and `qa_pe_headers_and_imports.ax`: NOT refreshed in round 0 (corrected in Round 1
  below; the round 0 claim that they were already stale was wrong).

## known_divergent.txt
Removed 50 entries (the oracle's XPASS list): `tests/run/drop/{001,002,003,004_field_wise,005_explicit,005_partial_move,
006_conditional_reassignment,qa_array_drop,qa_block_scope_drop,qa_cf_cleanup,qa_cf_continue,qa_cf_nested_return,
qa_conditional_drop,qa_conditional_drop_false,qa_copy_drop,qa_drop_nested_blocks,qa_drop_nested_struct,qa_drop_order,
qa_explicit_field,qa_explicit_multiple,qa_explicit_temp,qa_loop_break,qa_param_drop,qa_temp_drop,qa_temp_drop2,
qa_temp_drop3,qa_temp_drop_chained,qa_temp_drop_early_return,qa_temp_drop_loop}.ax` (all drop entries, so none remains),
`tests/run/method/{builtins,inherent_methods,qa_run}.ax`, `tests/run/mono/{qa_drop_count_generic,qa_generic_enum_drop,
qa_test_result_drop}.ax`, `tests/run/native_own/str_moves.ax`, `tests/run/own/reinit.ax`,
`tests/run/native_str/{hello,qa_hello_edge,qa_hello_tabs,qa_hello_very_long,qa_multiple_prints,qa_null_byte,qa_unicode_mix}.ax`,
`tests/run/str/{hello,qa_hello_edge,qa_hello_tabs,qa_hello_very_long,qa_multiple_prints,qa_unicode_mix}.ax`.
Registry: 136 -> 86 entries. No entry added.
Kept (decision): `tests/run/str/qa_hello_empty.ax` and `tests/run/native_str/qa_hello_empty.ax`. Their remaining difference
is not a string symbol: the program declares `@intrinsic fn assert`, axiomc compiles it as a call to a placeholder body
(symbols `assert`, 1693 vs 1904 bytes) while axiom0 lowers it inline with `.Lpanic.*` data. That is T150's cause (intrinsic
placeholder bodies); the plan table's attribution of these two to T147 alone was incomplete. Lines unchanged.

## Verification (snapshot `build-snap-T147`)
- Build warning-free; `tools/archcheck.py`: 192 files, 0 violations.
- Full suite: `python tools/axtest.py --compiler build/axiom0.exe -j 6 --timeout-scale 3` -> `TOTAL 2658 PASS 2658 FAIL 0 SKIP 0`
  (includes `selfhost/obj_link_driver/axiomc_e2e.test`, native and native-O1 legs).
- `grep -rn "native-after: T147" tests` prints nothing.

## Notes / decisions
- Panic message layout (no padding to 8, `panic: <msg>\n\0`) was not changed; only name, linkage and counter (ADR scope).
- `f` counts emitted bodies in emission order (axiom0: mono instances with a LIR body; port build mode: loop index).
- Port `backend_emit_mi_body_full_obj` (non-build legacy path) panic symbol renamed `.Lpanic.<n>` for consistency.

## Round 1 (QA round 0 finding 1 and notes N2-N4)
- **Correction:** the round 0 statement that the two hand-written link bundles "already embed a stale snapshot
  (differs from HEAD before this task)" was wrong. Before this task their embedded `compiler/link/*` and
  `compiler/obj/{coff,mod}` were identical to HEAD (only `obj/writer.ax` differed by one equivalent refactor, and the
  `//` header comments are part of each embedded section); after T147 they embedded the pre-T147 linker.
- New committed generator `tests/selfhost/link/refresh_link_bundles.py`: replaces every embedded section of
  `compiler.obj.{coff,writer}`, `compiler.obj`, `compiler.link.{pe,import,linker}`, `compiler.link` in both bundles with the
  current file (header comments included); idempotent; leaves kernel/diag modules and the hand-written `module main` alone.
  Run it after any change to `compiler/obj` or `compiler/link`. Both bundles refreshed (diff = exactly the T147 link
  changes plus the `obj/writer.ax` refactor).
- `qa_pe_headers_and_imports.ax` check 104 now asserts the ADR-0035 section 2 representation of the relocation to the
  same-object EXTERNAL `eightchr`: `dsec` == the merged `.text_lo` section, `doffset == 4`, `sym_name` null, addend -4.
  Both bundles pass (interp, native, native-O1).
- N2: `check_string_symbols.py` now checks that every `.Lstr.*` symbol offset is a multiple of 8 and its docstring matches.
- N3: `gen_local_symbols_test.py` writes a comment into the bundle header giving the reason it is native only
  (direct kernel32 FFI `CreateProcessW`, ADR-0002); `qa_pe_local_symbols.ax` regenerated.
- N4: `data_syms.c` uses `ax_xmalloc` / `ax_xfree`.
- No compiler source touched in round 1, so no full-suite rerun. In `build-snap-T147`: `selfhost/link` (8 of 8),
  `link/` + `obj/` + `selfhost/obj/` + `selfhost/obj_link_driver/axiomc_e2e` (24 of 24, including QA's
  `qa_static_not_global` and `qa_panic_and_paths`), archcheck 0 violations, build warning-free.
- N1 (inspect vs build ordinals) is T148's scope, as QA noted; not changed.

## Files changed
- bootstrap/axiom0/src/driver/build_native/build.c
- bootstrap/axiom0/src/driver/build_native/data_syms.c
- bootstrap/axiom0/src/driver/build_native/data_syms.h
- bootstrap/axiom0/src/driver/emit_obj.c
- bootstrap/axiom0/src/link/README.md
- bootstrap/axiom0/src/link/pe/linker.c
- compiler/backend/session.ax
- compiler/driver/pipeline.ax
- compiler/link/linker.ax
- compiler/link/mod.ax
- compiler/link/pe.ax
- tests/link/local_symbols/cdriver_link_objs.c
- tests/link/local_symbols/check_local_symbols.py
- tests/link/local_symbols/gen_local_symbols_obj.py
- tests/link/local_symbols/local_symbols.test
- tests/obj/determinism/check_string_symbols.py
- tests/obj/determinism/string_symbols.test
- tests/run/numeric/qa_t140_edge_matrix.ax
- tests/run/parity/strings/fn_literals_plain.ax
- tests/run/parity/strings/multi_fn_literals.ax
- tests/selfhost/backend/gen_backend_tests.py
- tests/selfhost/backend/harness_backend_edge.ax.in
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/link/gen_local_symbols_test.py
- tests/selfhost/link/qa_pe_local_symbols.ax
- tests/selfhost/link/refresh_link_bundles.py
- tests/selfhost/link/qa_pe_linker_diff.ax
- tests/selfhost/link/qa_pe_headers_and_imports.ax
- tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- _workspaces/reports/T147-report.md

STATUS: COMPLETE round=1
