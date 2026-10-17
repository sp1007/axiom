# T084a QA Gate Report — Port LIR data model and builder to Axiom

## Round 0

### 1. Task & Change Set Audit
- Checked `_workspaces/reports/T084a-report.md`: ends with `STATUS: COMPLETE round=0`.
- Ran `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T084a`:
  ```
  stage _workspaces/reports/T084a-report.md
  stage compiler/lir/builder.ax
  stage compiler/lir/lir.ax
  stage compiler/lir/mod.ax
  stage tests/selfhost/lir/qa_lir_from_ax_a.ax
  stage tests/selfhost/lir/qa_lir_from_ax_b.ax
  stage tests/selfhost/lir/qa_lir_from_ax_c.ax
  stage tests/selfhost/lir/qa_lir_from_ax_d.ax
  stage tests/selfhost/lir/qa_lir_from_ax_e.ax
  stage tests/selfhost/lir/qa_lir_from_mir.ax
  ```
  0 `REFUSED` lines; all modified files are within `paths: [compiler/lir, tests/selfhost/lir]`.

### 2. Snapshot Build & Architecture Layer Check
- Refreshed snapshot `build-snap-T084a` (`HEAD 305864f + 11 changed, 0 deleted file(s) of T084a`).
- Built `axiom0.exe` inside `build-snap-T084a/build` with `gcc` + Ninja:
  - `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build` -> exit 0, 0 warnings.
- Ran `python tools/archcheck.py --root .` inside `build-snap-T084a`:
  - `archcheck: 188 files scanned, 0 violations`.

### 3. Acceptance Criteria Verification
- **LIR data model and text printer (`compiler/lir/lir.ax`)**:
  - Verified canonical Axiom syntax (`=` only, `.` paths only, no `BOOTSTRAP-SHORTCUT`, clean formatting with no line-packing).
  - Cross-checked all 44 LIR instruction kinds (`LIR_INST_ADD` = 0 through `LIR_INST_ABI_RESULT` = 43), all 6 terminator kinds (`LIR_TERM_JMP` = 0 through `LIR_TERM_ASSERT` = 5), `LirBody`, `LirBb`, `LirInst`, `LirTerminator`, `LirSwitchTarget`, `LirStackSlot`, `LirVReg`, `LirFrameReq`, `LirConstEntry`, `LirConstTable`, and `lir_print` against `bootstrap/axiom0/src/lir/lir.h` and `bootstrap/axiom0/src/lir/print.c`.
- **MIR-to-LIR lowering and builder (`compiler/lir/builder.ax`) & module root (`compiler/lir/mod.ax`)**:
  - Cross-checked `lir_lower` and `lir_lower_ext` against `bootstrap/axiom0/src/lir/lower.c`, covering stack slot allocation, ABI entry argument extraction (`fn_ty`), `lower_place_addr` (`MIR_PROJ_DEREF`, `MIR_PROJ_FIELD`, `MIR_PROJ_INDEX`, `MIR_PROJ_SUB_SLICE`, `MIR_PROJ_DOWNCAST`), `lower_operand` (including `MIR_LOCAL_CONST` via `LirConstTable` and `TY_FN`/`TY_CLOSURE` `fn_addr`), `lower_rvalue` (all binary ops, overflow binary ops with bit-width, unary ops, casts, discriminant, `MIR_RVALUE_LEN`), `lower_assign_stmt` (`MIR_RVALUE_AGGREGATE`, `MIR_RVALUE_REPEAT`, fat-pointer `MIR_RVALUE_REF` slice/subslice construction), and `lower_call_terminator` (all 13 intrinsic/builtin call lowerings, closure environment capture passing, direct/indirect calls, `abi_arg`/`abi_result`).
- **Golden LIR dump parity & self-host test suite (`tests/selfhost/lir/`)**:
  - Ran `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/lir --jobs 2 --verbose` inside `build-snap-T084a`:
    - `PASS selfhost/lir/qa_lir_from_ax_a.ax [interp]`, `[native]`, `[native-O1]` (3 `.ax` end-to-end golden cases)
    - `PASS selfhost/lir/qa_lir_from_ax_b.ax [interp]`, `[native]`, `[native-O1]` (3 `.ax` end-to-end golden cases)
    - `PASS selfhost/lir/qa_lir_from_ax_c.ax [interp]`, `[native]`, `[native-O1]` (3 `.ax` end-to-end golden cases)
    - `PASS selfhost/lir/qa_lir_from_ax_d.ax [interp]`, `[native]`, `[native-O1]` (2 `.ax` end-to-end golden cases)
    - `PASS selfhost/lir/qa_lir_from_ax_e.ax [interp]`, `[native]`, `[native-O1]` (1 `.ax` end-to-end golden case)
    - `PASS selfhost/lir/qa_lir_from_mir.ax [interp]`, `[native]`, `[native-O1]` (37 `.mir` golden cases + `fn_ty` ABI prologue & `LirConstTable` test)
    - `PASS selfhost/lir/qa_lir_seam_edge.ax [interp]`, `[native]`, `[native-O1]` (QA boundary/seam test)
    - `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0`
  - Note: `_workspaces/reports/T084a-report.md` prose slightly misnames a couple of internal helpers (e.g., referring to `lir_print_body` instead of `lir_print`), while `## Files changed` and the actual exported symbols in `compiler/lir/` are exact.

### 4. Boundary Cross-Check & Added QA Tests
- Added `tests/selfhost/lir/qa_lir_seam_edge.ax` testing seam and edge cases not covered by the golden fixtures:
  - Null pointer guards on `lir_lower_ext` and `lir_lower` (`mir == null` and `interner == null` returning null `LirBody` without crashing).
  - Manual `LirBody` construction exercising `lir_inst_reset`, `lir_copy_inst`, `lir_term_reset`, `lir_copy_term`, `lir_buf_push_u64` boundaries (`0` and `9223372036854775807` / `i64::MAX`), `LIR_INST_CONST_STR`, both `lhs/rhs` and `ptr/offset` forms of `LIR_INST_OFFSET`, indirect `LIR_INST_CALL` (`call_indirect`), `LIR_TERM_JCC`, and `LIR_TERM_ASSERT` text printing.
  - `MIR_TERM_ASSERT` with `expected == false` lowering to `const 1` + `xor` condition inversion before `assert`, and 0-case `MIR_TERM_SWITCH_INT` (`otherwise` only) lowering and printing.
  - Builtin call terminator lowering seam (`TY_BUILTIN_SIZE_OF`, `TY_BUILTIN_ALIGN_OF`, `TY_BUILTIN_NULL`, `TY_BUILTIN_IS_NULL`, `TY_BUILTIN_PTR_ADD`, `TY_BUILTIN_PTR_SUB`, `TY_BUILTIN_FORGET`) directly from `MirBody` + `TypeInterner`.
- Refreshed snapshot and verified `tests/selfhost/lir/qa_lir_seam_edge.ax` passes across `[interp]`, `[native]`, and `[native-O1]`.

## Files changed
- tests/selfhost/lir/qa_lir_seam_edge.ax

## Findings
None.

VERDICT: PASS round=0
