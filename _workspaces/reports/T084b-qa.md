# QA Gate Report — T084b: Port Windows x64 ABI Lowering to Axiom

## Round 0

### 1. Change-Set & Scope Verification (`taskctl.py changes T084b`)
- Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T084b`
- Result: Exit code `0`, `0` `REFUSED` lines. All modified/added files lie strictly within `paths: [compiler/abi, tests/selfhost/abi]` and `_workspaces/reports/`:
  - `compiler/abi/mod.ax` (72 lines)
  - `compiler/abi/win64.ax` (593 lines)
  - `tests/selfhost/abi/qa_abi_win64_classify.ax`
  - `tests/selfhost/abi/qa_abi_lir_lower.ax`
  - `tests/selfhost/abi/qa_abi_boundary_seam.ax` (added by QA)

### 2. Snapshot Build, Architecture Layer Check & CTest Suite
- Command (in `build-snap-T084b/`):
  - `python tools/archcheck.py --root .` -> `archcheck: 188 files scanned, 0 violations`
  - `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build` -> 0 warnings, 0 errors.
  - `ctest --test-dir build --output-on-failure` -> `18/18` passed (`100%`), including `ct_mc_isel_cdriver_abi`, `ct_mc_isel_cdriver_abi_edge`, `ct_mc_isel_cdriver_abi_qa`, and `ct_mc_isel_cdriver_abi_qa2`.

### 3. Acceptance Criteria & Spec / Boundary Cross-Check
- **Completeness & Readability (`AXS-SELF-001`, `AXS-SELF-002`, `AXS-SELF-004`)**:
  - `compiler/abi/win64.ax` (593 LOC) and `compiler/abi/mod.ax` (72 LOC) cleanly port `bootstrap/axiom0/src/abi/{abi.h,win64.c,lower.c}` using canonical Axiom syntax (`=` bindings, `.` paths, `view`/`mut_view`, no mutable globals or library I/O).
  - Imports strictly respect `INV-LAYER-001` and `INV-LAYER-005` (`compiler.kernel`, `compiler.types`, `compiler.lir` only).
- **Windows x64 Calling Convention & ABI Lowering Parity (`REQ-ABI-106`, `REQ-ABI-107`, `REQ-ABI-108`)**:
  - Verified GP argument registers `RCX (1), RDX (2), R8 (8), R9 (9)`, return register `RAX (0)`, caller-saved volatile set (`RAX, RCX, RDX, R8, R9, R10, R11`), callee-saved non-volatile set (`RBX, RSI, RDI, R12, R13, R14, R15` + `RBP`, 56 bytes), 32-byte mandatory shadow space (`WIN64_SHADOW_SPACE = 32`), and 16-byte stack alignment (`WIN64_STACK_ALIGN = 16`).
  - Verified direct-by-value vs. indirect-by-pointer classification (`win64_needs_indirect`: sizes `0, 1, 2, 4, 8` direct; sizes `3, 5, 6, 7, >8` indirect), hidden `sret` pointer in `RCX` shifting subsequent parameters to `RDX, R8, R9` and 8-byte stack slots at offset `>= 32`, `TY_CLOSURE` unwrapping, and `TY_BUILTIN_PRINT` / `TY_BUILTIN_PRINT_INT` classification.
  - Verified seam between `compiler/lir`, `compiler/abi`, and `target/x64/isel`: `AbiLoc` populates both `.reg` and `.offset` so indirect stack arguments at offset `>= 32` set `loc_reg_or_offset >= 32`, matching `AxAbiLoc`'s C union layout expected by `isel`.
- **QA Boundary & Seam Test Added (`tests/selfhost/abi/qa_abi_boundary_seam.ax`)**:
  - Added exhaustive aggregate size boundary test (`0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 16` bytes in a single 11-parameter function with a 6-byte `sret` return).
  - Added `TY_CLOSURE` with `sret` + captures + stack arguments seam test and degenerate `AxType` guard tests (`TY_CLOSURE` with `fn_type == 0`, `TY_FN` with null `param_types`).
  - Added multi-block LIR ABI lowering test covering incoming indirect stack arguments, out-of-bounds `ABI_ARG` indices, orphan outgoing `ABI_ARG` without following `CALL`, and non-monotonic `max_outgoing_args_bytes` peak tracking across multiple basic blocks.
- **Selfhost ABI & Backend Test Execution (in `build-snap-T084b/`)**:
  - `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/abi --verbose`:
    - `PASS selfhost/abi/qa_abi_boundary_seam.ax [interp]`
    - `PASS selfhost/abi/qa_abi_boundary_seam.ax [native]`
    - `PASS selfhost/abi/qa_abi_boundary_seam.ax [native-O1]`
    - `PASS selfhost/abi/qa_abi_lir_lower.ax [interp]`
    - `PASS selfhost/abi/qa_abi_lir_lower.ax [native]`
    - `PASS selfhost/abi/qa_abi_lir_lower.ax [native-O1]`
    - `PASS selfhost/abi/qa_abi_win64_classify.ax [interp]`
    - `PASS selfhost/abi/qa_abi_win64_classify.ax [native]`
    - `PASS selfhost/abi/qa_abi_win64_classify.ax [native-O1]`
    - `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0`
  - Full suite (`axtest.py`): 1,759+ tests pass with 0 functional failures (`mc/`, `driver/`, `perf/`, `run/native_ptr/`, `selfhost/abi/` all 100% PASS).

### Findings
None.

## Files changed
- `tests/selfhost/abi/qa_abi_boundary_seam.ax`

## Verdict
VERDICT: PASS round=0
