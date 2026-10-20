# T085 Report - Port COFF writer, PE linker, driver -> axiomc (integration + differential)

## Summary

T085 joins the three accepted sub-ports (T085a `compiler/obj`, T085b `compiler/link`, T085c
`compiler/driver`) into a runnable `axiomc` and builds the differential harness that compares it with
`axiom0` byte for byte. The integration works: the complete compiler written in Axiom is compiled by
`axiom0` into a 13 MB `axiomc.exe` (with the 64 MB stack reserve of ADR-0003), and that binary produces
COFF objects and PE32+ images, runs `version`/`--features`/`help`/`inspect`/`check`/`build`/`run`, and
its images execute. The harness shows, honestly, that the pipeline is **not yet byte-identical to
`axiom0` on the whole language**: 124 of the 268 programs of the corpus are identical, 144 expose
documented gaps in *earlier* ports (lexer, resolver, typeck, MIR builder, backend string naming). Those
gaps are outside the `paths:` of T085 (no file of `compiler/{lex,resolve,types,mir,backend,driver,...}`
may be edited here), so they are recorded in a registry (`known_divergent.txt`) and handed over as
follow-ups instead of being hidden or "fixed" in the harness.

### 1. Integration (`compiler/obj_link_driver/`)
- `mod.ax` (`module compiler.obj_link_driver`): facade re-exporting the artefact producers of the group
  (`CoffBuf`, `ObjModel`, `coff_write_to_buf`, `coff_encode_bytes`, `coff_write_str`,
  `pe_link_coff_buffers_to_buf`, `pe_link_single_coff_to_buf`, `pe_link_objmodel_to_buf`,
  `pe_link_files_to_buf`, `pe_link`, `pe_link_one_file_str`, `driver_run_args`,
  `driver_execute_build_into`, `driver_main`, exit codes) and the `axiomc_main()` entry point.
- `main.ax` (`module compiler.obj_link_driver.main`): `pub fn main() -> i32 { axiomc_main() }`, the root
  of the `axiomc` program.

### 2. Differential harness (`tests/selfhost/obj_link_driver/`)
- `gen_obj_link_driver_tests.py`: reuses the module assembly of `tests/selfhost/driver/gen_driver_tests.py`
  (stage-0 compiles one file at a time, so all `compiler.*` modules are concatenated with the host
  prelude) and generates the two in-process bundles; `axiomc_bundle_text()` returns the whole `axiomc`
  program (never committed, built on the fly by the oracle).
- `qa_obj_link_driver_diff.ax` (native, native-O1): 6 programs (`main_42`, 3 x `vs1_*`, `modules/hello`,
  `modules/nested`) built *inside the Axiom driver* through `driver_execute_build_into` as `--emit=obj`
  and PE image at `-O0` and `-O1`, plus `--stack-reserve=2097152`: every byte equals the output of `axiom0`
  captured when the bundle is generated (30 artefacts). Also: object -> linker hand-off (axiom0's `.obj`
  bytes through the Axiom linker == axiom0's image, default and 2 MB stack reserve), the same hand-off inside
  the Axiom pipeline (driver `.obj` -> `pe_link_single_coff_to_buf` == image), a real on-disk
  `build -o` read back from the file system, and the exit code + stderr bytes of two diagnostic paths
  (missing input, `build` without input).
- `qa_obj_link_driver_smoke.ax` (interp, native, native-O1): the interp twin, `LITE` subset (one program,
  `main_42`): ONE `-O0` compile in the Axiom driver (`--emit=obj`), whose object bytes are compared with axiom0's
  object, then that same object linked by the Axiom linker (`pipeline_obj_and_image_status`) whose image bytes are
  compared with axiom0's image; plus the hand-off of axiom0's own object and both diagnostic paths (exit code +
  stderr bytes). QA round 0 found this leg timing out (1800 s): the earlier LITE did two full compiles
  (`--emit=obj` and the one-step image build) in the interpreter, which interprets the whole compiler. Round 1
  keeps every compared byte string (object bytes AND image bytes against axiom0) and drops only the redundant
  second compile: the one-step `build` to an image, `-O1`, `--stack-reserve` and the on-disk output are still
  compared in `qa_obj_link_driver_diff.ax` (native, native-O1) and in the end-to-end oracle. Measured interp leg:
  789 s before, 242 s after (same loaded machine, `axiom0 run --interp` alone); in `axtest` the leg passes.
  No `modes:` line was changed (still `interp native`).
- `axiomc_e2e.test` + `axiomc_e2e_oracle.py` (exec): the end-to-end oracle. It assembles `axiomc`,
  builds it with `axiom0 build --stack-reserve=67108864`, then for each of the **268 programs** of the corpus
  (`tests/run/**`, `tests/programs`, `tests/mc/**`, `tests/modules/*/src/main.ax`, `tests/opt`,
  `tests/driver`) runs `build` and `build --emit=obj` at `-O0` and `-O1` with both compilers and compares exit
  code, diagnostics and output bytes, then **runs both executables** and compares exit code and stdout.
  `known_divergent.txt` lists, for every non-identical program, the first `inspect --emit=` stage whose output
  differs and whether the images still behave the same. The oracle fails on: a regression of an identical
  program, a listed program that became identical (XPASS), a listed program whose images stopped behaving
  identically, or a stale entry. `--update-registry` regenerates the list.

## Differential counts (corpus of 268 programs, `AXIOMC-E2E` line of the oracle)

```
programs=268 equal=124 known_divergent=144 built=500 rejected=6 obj_equal=249 exe_equal=251
run_equal=180 images=202 same_behaviour=180
```
- Byte-identical objects and images at -O0 and -O1, identical diagnostics and identical run results:
  **124 programs** (248 object + 248 image comparisons plus the rejected-program diagnostics).
- Divergent: **144 programs**, by first divergent pipeline stage: tokens 8, resolved 14, thir 43, mir 25,
  obj 53 (output of `inspect --emit=obj` / `build`), backend-build 1 (sum 144).
- By observable behaviour of the produced images: 180 of the 202 programs for which both compilers produced an
  image run identically (exit code + stdout), 22 run differently, 64 divergent programs have no comparable
  image (axiomc rejects the program or crashes).

## Findings (follow-ups for the architect, root cause by stage)

1. **Wrong string data at run time (22 programs, e.g. `tests/run/drop/*`)**: `build` names the `.rdata`
   string symbols `.Lstr.<id>` with `IMAGE_SYM_CLASS_STATIC`, where `<id>` is the per-function string index; two
   functions that both have string #100000 collide in the linker's symbol table, so a call prints the other
   function's literal (`tests/run/drop/qa_param_drop.ax` prints `S drop` three times instead of
   `inside`/`S drop`/`after function call`). Port bug in the T085c/T084 build path
   (`driver_emit_build_mi_body_obj` / `backend_emit_fn_strings_rdata`): the name must be unique per function
   (for example `.Lstr.<function index>.<id>`).
2. **axiom0 `build` is not deterministic when a program has string literals** (`build.c:498,559` formats the
   `mi_body` heap address into `.Lstr.%zx.%u`): two consecutive `axiom0 build --emit=obj` runs of
   `tests/run/str/qa_hello_tabs.ax` differ (offset 458/459, the COFF string table). It also emits the string
   symbol twice (defined + undefined). Byte-identity with the reference is impossible for these programs
   until axiom0 gets a deterministic name (an `AX0-FIX` task); this is why the in-process bundles only use
   string-free programs and why 36 `obj`-stage entries are `same-behaviour`.
3. **tokens stage, 8 programs** (`tests/run/numeric/boundary.ax`, `host/fs/*`, ...): the Axiom lexer built by
   axiom0 exits with `panic: arithmetic overflow` (rc 101) on files with large integer literals; probably
   the unsigned checked arithmetic of the native back-end (see queued T140 "unsigned div/mul overflow shift width").
4. **resolved stage, 14 programs**: the `resolved` dump prints `(PathSegment @Sym(2) "i32")` for builtin
   types where axiom0 prints `(PathSegment "i32")`; plus `Self.Item` associated-type paths
   (`trait2/test_assoc_items.ax`) are unresolved.
5. **thir stage, 43 programs**: typeck gaps of the ported compiler: generic instantiation at call sites and
   struct/enum literals (`Option<i32>.Some(42)`, `Pair<i32> {..}`, `id(42)`), closures / fn pointers,
   `address_of`/`address_of_mut`/`null<T>()` pointer intrinsics (`AX_TYPE_MISMATCH`), operator typing
   (`AX_TYPE_OPERATOR`), duplicate closure symbols (`AX_LINK_DUPLICATE_SYMBOL`, `__ax_fn_1073741825`).
6. **mir stage, 25 programs**: type-id numbering of the dump differs (`type#26` vs `type#29`, interning order
   of slice/array types) - the six programs that also run differently are `for` ranges, `char` panics and
   `trait2/test_default_override.ax`.
7. **`axiomc` needs the 64 MB stack** (ADR-0003): built with the default 1 MB reserve it dies with
   `0xC00000FD` on the larger programs (`tests/programs/*`). The oracle builds it with
   `--stack-reserve=67108864`; `tools/bootstrap.py` (T086) must do the same.

Design decisions recorded here for the architect: (a) the differential corpus is the whole existing test
corpus, not a hand-picked passing subset, and the registry makes every gap visible and monotone (no silent
growth, no silent fixes); (b) strings make axiom0 output non-deterministic, so the committed byte-blob bundles
use string-free programs and the string programs are covered by the oracle through run-behaviour equality
only; (c) the `compiler/obj_link_driver` entry module is deliberately separate from the facade so the test
bundles (which define their own `main`) can import the facade without the entry point.

## Verification (round 1, all in `build-snap-T085`, HEAD 154b218 + task files; machine at ~100% CPU from other processes)

- `python tools/axtest.py --compiler build/axiom0.exe -j 4 --verbose --filter selfhost/obj_link_driver`:
  `TOTAL 7 PASS 7 FAIL 0 SKIP 0 XFAIL 0` (`axiomc_e2e.test`, `qa_axiomc_cli_edges.test`,
  `qa_obj_link_driver_diff.ax` native + native-O1, `qa_obj_link_driver_smoke.ax` interp + native + native-O1).
  Run twice after the last generator change (once with `-j 2`, once with `-j 4` plus the changed oracle limits): both 7/7.
- End-to-end oracle alone (`python axiomc_e2e_oracle.py build/axiom0.exe <tmp> .`, 274 s):
  `OK`, `AXIOMC-E2E programs=268 equal=124 known_divergent=144 built=500 rejected=6 obj_equal=249 exe_equal=251
  run_equal=180 images=202 same_behaviour=180`. `known_divergent.txt` matches this measured state exactly (the oracle
  fails on any REGRESSION / XPASS / IMPROVED / STALE entry); registry breakdown: 144 entries = no-image 64,
  different-behaviour 22, same-behaviour 58; by stage tokens 8, resolved 14, thir 43, mir 25, obj 53, backend-build 1.
  Counts: identical (objects, images, diagnostics, run results) 124; byte-different but same observable behaviour 58;
  different behaviour 22 (string-symbol collisions etc., findings 1-6 above); no comparable image 64.
- Smoke interp leg alone (`axiom0 run --interp`): 789 s before the change, 242 s after (rc 0).
- Liveness (axiom-testing "native PASS must check something"), scratch copies, snapshot untouched: in the
  regenerated smoke test one byte of the case-0 object blob changed -> native exit `101` (object bytes differ);
  one byte of the case-0 image blob changed -> exit `102` (image bytes differ); pristine -> 0. (Round 0: a byte of a
  `vs1_return` image blob in the diff test -> exit `132`; QA round 0 mutated the case-0 object blob -> `101`.)
- `python tools/archcheck.py`: `188 files scanned, 0 violations`.
- Full suite (`python tools/axtest.py --compiler build/axiom0.exe -j 4 --verbose`, 6126 s):
  `TOTAL 1942 PASS 1939 FAIL 3 SKIP 0 XFAIL 0`. The 3 failures, each re-examined:
  1. `selfhost/obj_link_driver/axiomc_e2e.test` (exit 1): a load flake of the oracle itself (8 parallel programs, 120 s
     per command / 20 s per run limits while 4 suite jobs and other agents saturated the CPU). It passes alone
     (`OK`, 274 s) and in the filtered rerun. Fix: `CMD_TIMEOUT` 120 -> 600 s and `RUN_TIMEOUT` 20 -> 60 s in
     `axiomc_e2e_oracle.py` (upper bounds only; a real hang is still bounded by the 1800 s test timeout). The full
     suite was not rerun after this edit; the filtered `obj_link_driver` run after it is 7/7.
  2. `selfhost/drop/qa_drop_d11.ax [interp]` (TIMEOUT 1200 s): not a T085 test; passes (interp + native + native-O1)
     when rerun alone.
  3. `selfhost/typeck/qa_typeck_b.ax [interp]` (TIMEOUT 600 s): not a T085 test; times out again when rerun alone
     on this loaded machine (native and native-O1 pass). Interp-leg cost of another task, reported for the architect.
  So 1939/1942 pass; none of the 3 is caused by T085 files, and (1) is fixed.
- Earlier concurrent runs of `qa_obj_link_driver_diff.ax` crashed (access violation / "out of memory (3569136
  bytes)") when 3 jobs plus the machine's other processes exhausted RAM (~4 GB free); alone and at `-j 2`/`-j 4`
  later they pass. Memory pressure, not a defect of the test.

## Round 1 changes (QA round 0 findings)
1. Placeholder `FULL_SUITE_RESULT` replaced by the measured result above.
2. Smoke interp leg: one compile instead of two (see section 2 above); every compared byte string kept.
3. `## Files changed` lists the QA-authored tests and every file touched in this round.
4. The 144/268 divergences were not touched (outside this task's paths); only the counts were re-measured.

## Files changed

- compiler/obj_link_driver/mod.ax
- compiler/obj_link_driver/main.ax
- tests/selfhost/obj_link_driver/axiomc_e2e.test
- tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py
- tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py
- tests/selfhost/obj_link_driver/known_divergent.txt
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/obj_link_driver/qa_axiomc_cli_edges.test
- tests/selfhost/obj_link_driver/qa_axiomc_cli_edges_oracle.py
- _workspaces/reports/T085-report.md

## Round 1

STATUS: COMPLETE round=1
