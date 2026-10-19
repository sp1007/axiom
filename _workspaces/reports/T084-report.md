# T084 Report — Port LIR + x64 Backend + Encoder to Axiom (Integration + Differential)

## Summary

Integrated the Axiom self-hosted backend pipeline (`compiler/lir`, `compiler/abi`, `compiler/target/x64`, and `compiler/obj`) in `compiler/backend/session.ax` (`module compiler.backend.session`) and `compiler/backend/mod.ax` (`module compiler.backend`), and built the differential and unit test suites in `tests/selfhost/backend/` comparing `.mir` and `.ax` LIR dumps (`inspect --emit=lir`), Machine IR dumps (`inspect --emit=mi`), Machine Code hex dumps (`inspect --emit=mc`), Machine IR verification (`x64_verify_checked`), and `ObjModel` section/symbol/relocation emission against `axiom0`.

## Implementation Details

1. **Backend Integration Session (`compiler/backend/session.ax`, `compiler/backend/mod.ax`)**:
   - **Standalone `.mir` Text Inspection Emitters**:
     - `session_emit_lir_mir_text`: parses `.mir` text via `mir_parse`, lowers to LIR via `lir_lower`, and formats canonical LIR dump via `lir_print` (matching `axiom0 inspect --emit=lir <file.mir>`).
     - `session_emit_mi_mir_text`: parses `.mir` text, lowers to LIR, synthesizes the return-type function signature, runs Windows x64 ABI lowering (`lir_lower_abi_in_arena`), lowers to Machine IR (`x64_isel_in_arena`), and prints canonical MI text (`x64_mi_print`, matching `axiom0 inspect --emit=mi <file.mir>`).
     - `session_emit_mc_mir_text`: runs the full `.mir` -> LIR -> Win64 ABI -> x64 Isel -> x64 Frame Lowering -> x64 Verifier (`x64_verify_checked`) -> `.text` section encoding (`x64_emit_mi_body_mc`) -> hex dump (`x64_dump_mc_hex`, matching `axiom0 inspect --emit=mc <file.mir>`).
   - **HIR + THIR -> MIR -> Backend Lowering & Promotion**:
     - `backend_populate_hir_const_aggregates` and `backend_promote_const_aggregates`: serializes top-level `HIR_ITEM_CONST` array, tuple, and struct aggregates into `thir.symbol_consts` and promotes `CONST_AGGREGATE` MIR locals to `MIR_LOCAL_CONST` with `.Lconst_<sym>_<name>` `.rdata` symbols and string fat-pointer `RELOC_X86_64_64` relocations (`backend_emit_const_tables`).
     - `session_emit_lir_hir` / `session_emit_lir_file`: lowers all `HIR_ITEM_FN` items in the target `FileId` to LIR and prints `inspect --emit=lir` output.
     - `session_emit_mi_hir` / `session_emit_mi_file`: lowers all `HIR_ITEM_FN` items through LIR, Win64 ABI, and x64 Isel and prints `inspect --emit=mi` output.
     - `session_emit_mc_hir` / `session_emit_mc_file`: lowers all `HIR_ITEM_FN` items through LIR, Win64 ABI, x64 Isel, x64 Frame Lowering, x64 Verifier, and `.text` machine code hex dump (`inspect --emit=mc`).
   - **Full `ObjModel` Emission (`session_emit_objmodel_hir`, `session_compile_and_emit_objmodel`)**:
     - Supports both `full_native_mode = false` (matching `emit_obj.c` / `axiom0 inspect --emit=obj`) and `full_native_mode = true` (matching `build_native/build.c` with incoming parameter `ABI_ARG`s, `.rdata` constant aggregate tables and string literals `.Lstr.<sym>`, basic-block `JMP`/`JCC` `rel32` fixup patching, and `X64_MI_ASSERT` deferred `axiom_panic` block synthesis).
     - `backend_parse_virtual_file`: clones lexer-unescaped string literal buffers into `parse_arena` before freeing `lex_res` so AST/HIR/MIR/LIR/MI string pointers remain valid across both `--interp` and native execution.

2. **Target x64 Isel & Frame Alignment Fixes (`compiler/target/x64/isel.ax`, `compiler/target/x64/frame.ax`)**:
   - Fixed `isel_emit_trunc` in `compiler/target/x64/isel.ax` so `TY_CHAR` (`32`-bit scalar) emits `shl reg, 32; shr reg, 32`, matching `bootstrap/axiom0/src/target/x64/isel/isel.c`.
   - Fixed `x64_frame_lower_in_arena` in `compiler/target/x64/frame.ax` to reserve the `8`-byte `[rbp - 64]` stack slot whenever `lir.slot_count == 0 && lir.vreg_count == 0`, matching `bootstrap/axiom0/src/target/x64/frame/frame.c`.

3. **Self-Hosted Backend Unit & Differential Test Suite (`tests/selfhost/backend/`)**:
   - `qa_backend_unit.ax`: tests standalone `.mir` -> LIR / MI / MC (`add.mir`, `qa_edge_cond_br.mir`, `qa_multi_branch.mir`, `call.mir`) and full `.ax` `ObjModel` emission (`session_compile_and_emit_objmodel` in both `full_native_mode = false` and `full_native_mode = true`, verifying `.text` and `.rdata` sections, symbol table entries, `axiom_panic` external symbol, and `.text` PC32 relocations).
   - `qa_backend_diff_lir_a.ax` (4 cases, interp + native + native-O1) and `qa_backend_diff_lir_b.ax` (63 cases: 30 `.ax` + 33 `.mir`, native + native-O1): differential test comparing `session_compile_and_emit_lir` and `session_emit_lir_mir_text` byte-for-byte against `axiom0 inspect --emit=lir`.
   - `qa_backend_diff_mi_mc_a.ax` (3 cases, interp + native + native-O1) and `qa_backend_diff_mi_mc_b.ax` (60 cases: 30 `.ax` + 30 `.mir`, native + native-O1): differential test comparing `session_emit_mi_file`, `session_emit_mc_file` (including `x64_verify_checked`), `session_emit_objmodel_hir`, `session_emit_mi_mir_text`, and `session_emit_mc_mir_text` byte-for-byte against `axiom0 inspect --emit=mi` and `axiom0 inspect --emit=mc`.

## Verification

- Ran `python tools/axtest.py --compiler build-snap-T084/build/axiom0.exe --filter selfhost/backend --verbose`:
  - `PASS selfhost/backend/qa_backend_diff_lir_a.ax [interp]`
  - `PASS selfhost/backend/qa_backend_diff_lir_a.ax [native]`
  - `PASS selfhost/backend/qa_backend_diff_lir_a.ax [native-O1]`
  - `PASS selfhost/backend/qa_backend_diff_lir_b.ax [native]`
  - `PASS selfhost/backend/qa_backend_diff_lir_b.ax [native-O1]`
  - `PASS selfhost/backend/qa_backend_diff_mi_mc_a.ax [interp]`
  - `PASS selfhost/backend/qa_backend_diff_mi_mc_a.ax [native]`
  - `PASS selfhost/backend/qa_backend_diff_mi_mc_a.ax [native-O1]`
  - `PASS selfhost/backend/qa_backend_diff_mi_mc_b.ax [native]`
  - `PASS selfhost/backend/qa_backend_diff_mi_mc_b.ax [native-O1]`
  - `PASS selfhost/backend/qa_backend_unit.ax [interp]`
  - `PASS selfhost/backend/qa_backend_unit.ax [native]`
  - `PASS selfhost/backend/qa_backend_unit.ax [native-O1]`
  - `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`
- Ran `python tools/axtest.py --compiler build-snap-T084/build/axiom0.exe --filter selfhost/encode --verbose`: `TOTAL 9 PASS 9 FAIL 0`.
- Ran `python tools/archcheck.py`: `archcheck: 188 files scanned, 0 violations`.

## Files changed

- `compiler/backend/mod.ax`
- `compiler/backend/session.ax`
- `compiler/target/x64/frame.ax`
- `compiler/target/x64/isel.ax`
- `tests/selfhost/backend/gen_backend_tests.py`
- `tests/selfhost/backend/harness_backend_diff_lir.ax.in`
- `tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`
- `tests/selfhost/backend/harness_backend_unit.ax.in`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`

## Status

STATUS: COMPLETE round=0
