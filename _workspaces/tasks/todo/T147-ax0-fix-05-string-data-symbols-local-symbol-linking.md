---
id: T147
title: AX0-FIX-05 deterministic object-local string/panic data symbols and index-based local-symbol linking (axiom0 + port)
phase: P10-selfhost
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: opus
depends: [T146]
priority: 0
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/driver/build_native, bootstrap/axiom0/src/driver/emit_obj.c, bootstrap/axiom0/src/link, compiler/backend, compiler/driver/pipeline.ax, compiler/link, compiler/obj, tests/link, tests/obj, tests/run/parity/strings, tests/run/numeric/qa_t140_edge_matrix.ax, tests/selfhost]
spec: [spec/decisions/ADR-0035-axiomc-parity-symbols.md, spec/decisions/ADR-0034-oracle-independence.md, 0185]
covers: [REQ-CORE-3181, REQ-BLD-030]
timeout_min: 240
---
# T147 — AX0-FIX-05: string/panic data symbols and local-symbol linking

## Goal
A program with string literals in several functions prints the right literal in every function when
built by `axiomc`, and `axiom0 build` produces byte-identical output on every run. Both compilers
name compiler-generated data symbols by ADR-0035 §1 and both linkers resolve same-object references
by symbol index (ADR-0035 §2). This removes the `different-behaviour` class of the T085 registry
(15 `tests/run/drop/*` programs) and the axiom0 non-determinism that made every string program
divergent.

Confirmed defects (architect probe 2026-10-20, `_workspaces/reports/plan-axiomc-divergence.md`):
1. Port: `compiler/link/linker.ax` (~line 380) registers `IMAGE_SYM_CLASS_STATIC` symbols in the
   global name table (first definition wins). `axiomc build` emits `.Lstr.100000` as STATIC in every
   function, so `tests/run/drop/qa_param_drop.ax` prints `S drop` three times instead of
   `inside` / `S drop` / `after function call` (the object itself is correct: relocations reference
   distinct symbol indexes 0, 4, 9).
2. axiom0: `driver/build_native/build.c:498,559` names strings `.Lstr.<heap address>.<id>` (two
   consecutive `axiom0 build --emit=obj` runs of `tests/run/str/qa_hello_tabs.ax` differ), defines
   them GLOBAL and adds an undefined EXTERNAL twin per reference, pads with one NUL only;
   `link/pe/linker.c` resolves every relocation by name and ignores STATIC symbols;
   `driver/emit_obj.c:496` (`inspect --emit=obj`) uses a third convention. `.Lpanic_<n>` uses a
   process-wide `static int`.

## Scope
- **Naming (ADR-0035 §1)** in axiom0 `build.c`, `emit_obj.c` and the port
  (`compiler/backend/session.ax` `backend_emit_fn_strings_rdata`, `compiler/driver/pipeline.ax`
  build path): `.Lstr.<f>.<k>`, STATIC, defined once, NUL + pad to 8, relocation against the
  symbol's own index; `.Lpanic.<n>` with a per-object counter. `build`, `build --emit=obj` and
  `inspect --emit=obj` use the same code path or provably the same convention.
- **Linking (ADR-0035 §2)** in `link/pe/linker.c` and `compiler/link/linker.ax` (file path and the
  in-memory object-model path): same-object references by index, STATIC never global, duplicate
  EXTERNAL definitions still `AX_LINK_DUPLICATE_SYMBOL`, undefined EXTERNAL by name.
- Regenerate selfhost bundles/goldens that embed or compare the changed code or output with their
  generators; explain each regenerated file in the report (ADR-0034 §2).
- Lift T085's "string-free programs only" restriction: add one program with literals in at least
  three functions to the in-process byte-blob bundle of `tests/selfhost/obj_link_driver`
  (via `gen_obj_link_driver_tests.py`).

## Acceptance
- [ ] `tests/run/parity/strings/multi_fn_literals.ax` (`modes: interp native`): five functions each
      printing its own literal (ASCII, empty, `"Xin chào thế giới"`, a literal containing `\0`, a
      >100-byte literal) plus a destructor that prints; `// stdout:` written by hand from the source.
      Passes with axiom0 in both modes; being under `tests/run/**` it is in the e2e corpus and is not
      listed in the registry (so axiomc's image prints the same).
- [ ] `tests/link/local_symbols/` (new): a hand-built COFF object (bytes written by a Python generator
      from the PE/COFF spec, not by either compiler) with two STATIC symbols of the same name at
      different `.rdata` offsets referenced from two functions, plus an EXTERNAL definition; linked by
      axiom0 and by the port linker (selfhost test built from the real `compiler/link`), the image
      exits with the code that proves each reference resolved to its own symbol. A duplicate
      EXTERNAL definition still fails with `AX_LINK_DUPLICATE_SYMBOL`.
- [ ] Determinism: `axiom0 build --emit=obj` and `axiom0 build` run twice on every `tests/run/str/**`
      program produce identical bytes (a test that builds twice into `{tmp}` and byte-compares).
- [ ] `known_divergent.txt` shrinks by every entry this fix makes identical (oracle XPASS lines), at
      least the sole-cause entries of the plan table: `tests/run/drop/{005_explicit,qa_array_drop,
      qa_explicit_field,qa_explicit_multiple,qa_explicit_temp}.ax`, `tests/run/method/{builtins,
      qa_run}.ax`, `tests/run/native_own/str_moves.ax`, `tests/run/own/reinit.ax`, all eight
      `tests/run/native_str/*` and seven `tests/run/str/*` entries. Every remaining `tests/run/drop/*`
      entry is `same-behaviour` (no `different-behaviour` entry with a string-symbol cause remains);
      its line is updated in place. No entry is added (ADR-0035 §4).
- [ ] `tests/run/numeric/qa_t140_edge_matrix.ax` is switched back to string literals (T141 round 0
      rewrote it to print through one byte-buffer `put()` only to dodge the `.Lstr` divergence; T141
      QA R0-4): every `stdout:` directive and every numeric `return n` check unchanged; passes in all
      modes with axiom0 and is identical under axiomc_e2e (ADR-0036 §6).
- [ ] `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/obj_link_driver` passes in
      `build-snap-T147`; full suite passes with native legs; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T147-report.md` with exact `## Files changed`, the removed registry
      paths and the regenerated bundles with reasons.

## Out of scope
- The destructor-call ABI difference in the same drop programs (T148), other codegen differences.
- Import-library/`__imp_` work (E18.7).

## Notes
- AX0-FIX chain (ADR-0034 §2, §5): runs alone after T146 (priority 0); both compilers in one task.
- How to get axiomc for single-program probes: `python tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py
  <axiom0> <tmp> <root>` builds `<tmp>/axiomc.exe` (64 MB stack) before checking the corpus.
- Build fresh in the snapshot; `build/axiom0.exe` in the main tree is stale and is not evidence.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
