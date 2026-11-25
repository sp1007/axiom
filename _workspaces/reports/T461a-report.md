# T461a report: large native programs must run (COFF relocation count overflow)

## Summary

Root cause: the COFF object writer (`compiler/obj/writer.ax`) wrote the per-section relocation count
as `rlen as u16`. The 330-chunk program has about 66,000 relocations in its single `.text` section
(two direct `call rel32` per statement plus `main`). That is more than the 16-bit `NumberOfRelocations`
field holds, so the count wrapped modulo 65,536. The in-memory build path writes the object and the
PE linker (`compiler/link/linker.ax`) parses it back. The linker therefore saw only `count mod 65536`
relocations and left every later `call` with displacement 0 (`e8 00 00 00 00`). The first chunk
(`chunk_0`, placed last in `.text`) then jumped into the middle of its own code and crashed with
0xC0000005 before anything was flushed. Evidence from HEAD (`objdump -d`, first callee of `main`):

```
140506e34: 48 8d 5d c8     lea  -0x38(%rbp),%rbx
140506e38: e8 00 00 00 00  call 0x140506e3d      <- call plain_f32, relocation dropped
...
140506e70: e8 00 00 00 00  call 0x140506e75      <- call pr, relocation dropped
```

The suspects listed in the task were also checked and ruled out. PE layout was fine: SizeOfImage
0x50c000, sections aligned, and `.text` is 5.3 MB, well inside rel32 range. The stack probe was also
correct: `main` has a 0x14d8-byte frame and the probe loop is right. The crash happens the same way
under gdb at the first call into `chunk_0`.

Bisect with the generator in this task (HEAD compiler): 66, 200, 300 and 320 chunks pass, while
330 and 500 crash. The boundary is the point where `.text` relocations go past 65,535 (about 327
chunks).

## Fix (owning modules)

- `compiler/obj/coff.ax` (object model / COFF format constants, layer obj):
  - Added `IMAGE_SCN_LNK_NRELOC_OVFL` (0x01000000) and `COFF_NRELOC_OVFL_MARK` (0xFFFF).
  - Added `coff_reloc_entries(rlen)`, the number of table entries written: one extra placeholder
    entry when `rlen >= 0xFFFF`. 0xFFFF itself is ambiguous, so it also uses the overflow form,
    as LLVM does.
  - Added `CoffRelocSpan` and `coff_section_reloc_span(buf, len, shdr)`, the single reader-side
    decoding of the relocation table. If the flag is set and the count is 0xFFFF, the real count is
    the first entry's VirtualAddress minus 1 and the entries start 10 bytes later. `ok = false` when
    the placeholder entry is missing or holds 0.
- `compiler/obj/writer.ax` (COFF writer):
  - Emits the PE/COFF overflow encoding: NumberOfRelocations = 0xFFFF, `IMAGE_SCN_LNK_NRELOC_OVFL`
    set, and a first entry of {VirtualAddress = entry count including itself, SymbolTableIndex = 0,
    Type = IMAGE_REL_AMD64_ABSOLUTE}.
  - Format limits are now checked instead of silently wrapped: file offsets are summed in u64, and
    an object of 4 GiB or more, or one with more than 65,279 sections, makes `coff_write_to_buf`
    return false. The driver already turns that into a failed build (`AX_EXIT_DIAG`), so no broken
    image is written.
- `compiler/link/linker.ax` (PE linker): both COFF relocation readers (`linker_load_coff_object_ex`
  and the provenance/GC reader) now use `coff_section_reloc_span`. A malformed overflow header is
  reported as `AX_LINK_BAD_OBJECT` on the same path as an out-of-file relocation table.

Design choices (no spec text dictates them; the PE/COFF format does):

- The overflow form is used for `rlen >= 0xFFFF`, as LLVM and MSVC do.
- The reader also accepts the overflow form for small counts, which the spec allows. This lets
  `nreloc_ovfl.test` exercise it cheaply.
- No new diagnostic code was added for the write-side limits. `coff_write_to_buf` has no
  diagnostic sink, and both limits (4 GiB objects, more than 65,279 sections) are far beyond the
  relocation case that actually happened. Adding a dedicated code means changing
  `compiler/driver/pipeline.ax`, which is outside this task's locks; see follow-up 3.

## Tests

New directory `tests/build_native/large_program/`, Python stdlib only:

- `run_large.py` is a deterministic generator and driver. It builds the program
  `pr(plain_f32(from_bits_f32(N)));` × 100 per chunk at -O0 and -O1, runs it and compares stdout
  byte-for-byte with two references:
  - a Python IEEE-754 binary32 reference (independent oracle, ADR-0034);
  - `run --interp`, which every size runs.

  With `--obj` it also emits the `.obj` and checks the overflow encoding by parsing the COFF
  headers, and checks that GNU `objdump -r` reads the same relocation count. That check also
  requires a section with ≥ 0xFFFF relocations whenever the program needs one.
- `large_66.test`, `large_200.test`, `large_330.test` (with `--obj`) and `large_500.test`
  (with `--obj`) run these sizes. The 330 and 500 programs have about 66,000 and 100,000
  relocations.
- `check_nreloc_ovfl.py` + `nreloc_ovfl.test` test the linker reading overflow tables from `.obj`
  inputs. A small program's object is rewritten into the overflow form:
  - well-formed: links, runs and gives exact output;
  - count 0: rejected with `AX_LINK_BAD_OBJECT` and no image;
  - count past end of file: rejected with `AX_LINK_BAD_OBJECT` and no image.

Fails on HEAD (`axiomc2` built from unmodified HEAD bd33c32 in the snapshot; the fix build is on HEAD c6f7268, which touches none of the three files):

```
PASS    build_native/large_program/large_200.test
FAIL    build_native/large_program/large_330.test   (native -O0 rc=3221225477 (0xC0000005), 0 lines of 33000)
FAIL    build_native/large_program/large_500.test
PASS    build_native/large_program/large_66.test
nreloc_ovfl (HEAD): good: link failed rc=1: error[AX_LINK_BAD_OBJECT]: bad object
```

All commands were run in `build-snap-T461a` with the stage-2 compiler built from the snapshot plus
the fix:

1. `python tools/build_axiomc.py --out build --root . --stage 2`:
   - `FIXED-POINT (O1) OK`: sha256(axiomc2_O1) == sha256(axiomc3_O1) == 0dd392c2…3294, 9,260,032
     bytes.
   - `STAGE0-GUARD OK`.
   - `BUILD-AXIOMC OK`.
2. `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter build_native -j 2`
   gives `TOTAL 10 PASS 10 FAIL 0`, `WEAK-NATIVE 0`. That is 4 large_* tests plus 6 existing
   entries. `--filter nreloc_ovfl` gives `TOTAL 1 PASS 1`.
3. Same runner with `--filter link/ --filter link2/ --filter obj/ --filter run/native --filter obj_link_driver`
   (153 ids: tests/link/**, tests/link2/**, tests/obj/**, tests/run/native*/**, and the selfhost
   groups link, obj and obj_link_driver of the changed modules). After regenerating the bundles in
   the snapshot (`bundles.py regen --root build-snap-T461a`, see the note below), the selfhost
   groups rerun gave `TOTAL 20 PASS 19 FAIL 1`. The non-selfhost part gave 145 PASS, 4 SKIP and
   0 other failures.
   - The one failure, `selfhost/obj_link_driver/qa_t442_obj_link_driver_bounds.test`, is
     pre-existing and unrelated. It fails identically with the HEAD compiler because
     `_workspaces/baseline-failures.txt` at HEAD still has active lines (T540, T428a …), which the
     test forbids.
4. `python tools/archcheck.py` gives `252 files scanned, 0 violations`.

## Notes for QA / orchestrator

- **Snapshot caveat.** `taskctl snapshot T461a` copies only dirty files under `paths:`. This task's
  compiler edits are under `locks:` (`compiler/obj`, `compiler/link`), so the snapshot left them
  out ("1 changed"). The three compiler files were copied into the snapshot by hand (checked with
  `cmp`), and the selfhost bundles were then regenerated inside the snapshot only, with
  `bundles.py regen --root build-snap-T461a`. The gate must do the same, or the task's `paths:`
  should include `compiler/obj` and `compiler/link`.
- Pre-existing performance issue, not caused by this change: linking a standalone `.obj` with
  many relocations (`axiomc build x.obj`) is roughly quadratic. A 66-chunk object (13,269
  relocations) takes about 4 minutes with both HEAD and the fixed compiler. A 330-chunk object did
  not finish within 30 minutes and was stopped. The normal `.ax` build path is unaffected: about
  20 s for 330 chunks. This is why `nreloc_ovfl.test` uses a rewritten small object.

## Follow-ups (for the architect)

1. The frozen axiom0 has the same truncation: `bootstrap/axiom0/src/obj/coff/writer.c:166`
   `shdr.NumberOfRelocations = sec->relocs_len;`. It is not needed for bootstrapping (axiomc
   sources stay far below the limit per object), so it was not touched (outside paths, frozen).
2. Quadratic standalone `.obj` linking in `compiler/link/linker.ax`, described above.
3. Optional: a dedicated diagnostic code (for example `AX_OBJ_FORMAT_LIMIT`) for objects that
   exceed COFF limits. Today the writer refuses them with a generic failed-emission exit and no
   message (`compiler/driver/pipeline.ax`).

## Files changed

- compiler/obj/coff.ax
- compiler/obj/writer.ax
- compiler/link/linker.ax
- tests/build_native/large_program/run_large.py
- tests/build_native/large_program/large_66.test
- tests/build_native/large_program/large_200.test
- tests/build_native/large_program/large_330.test
- tests/build_native/large_program/large_500.test
- tests/build_native/large_program/check_nreloc_ovfl.py
- tests/build_native/large_program/nreloc_ovfl.test
- _workspaces/reports/T461a-report.md

STATUS: COMPLETE round=0
