# T084d QA Report — Port x64 Machine Code Encoder to Axiom

## Round 0

### 1. Changeset & Task Scope Check
- Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T084d`
- Result: 0 `REFUSED` lines. Staged files are strictly within `paths: [compiler/target/x64/encode.ax, tests/selfhost/encode]` plus reports.

### 2. Snapshot Build & Warnings Check
- Command (inside `build-snap-T084d/`):
  `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build`
- Result: Clean build, 0 warnings, 0 errors.

### 3. Acceptance Criteria Verification
- **[x] x64 encoder implemented in `compiler/target/x64/encode.ax` — complete and readable**:
  - `compiler/target/x64/encode.ax` (1,809 lines, canonical `=` / `.` syntax) ports `bootstrap/axiom0/src/target/x64/encode/{encode.h,encode.c}`, `bootstrap/axiom0/src/target/x64/frame/frame.c` prologue/epilogue and 4KB page probe emitters, and relocation/branch-fixup/rodata/panic helpers from `bootstrap/axiom0/src/driver/{emit_obj.c,emit_mc.c,build_native/build.c}`.
  - All 16 general-purpose registers (`REG_RAX`..`REG_R15`, `REG_NONE`), condition codes (`CC_O`..`CC_G` plus mnemonic aliases), Machine IR opcodes (`X64_MI_*`), addressing modes (`X64Mem`), REX/ModR/M/SIB/displacement encoders, full ALU/shift/multiply/divide/branch/call/stack instruction set, PC32 symbol relocations, branch fixups, and frame prologues/epilogues are implemented cleanly without shortcuts.
- **[x] Unit tests pass in both interpreter and native modes**:
  - Ran `python tools/axtest.py --compiler build/axiom0.exe --filter selfhost/encode --verbose` inside `build-snap-T084d/`:
    - `PASS selfhost/encode/qa_encode_edge_cases.ax [interp]`
    - `PASS selfhost/encode/qa_encode_edge_cases.ax [native]`
    - `PASS selfhost/encode/qa_encode_edge_cases.ax [native-O1]`
    - `PASS selfhost/encode/qa_encode_instructions.ax [interp]`
    - `PASS selfhost/encode/qa_encode_instructions.ax [native]`
    - `PASS selfhost/encode/qa_encode_instructions.ax [native-O1]`
    - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [interp]`
    - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [native]`
    - `PASS selfhost/encode/qa_encode_relocs_and_frames.ax [native-O1]`
    - `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0`
- **[x] Emitted machine code bytes match `axiom0` byte-for-byte across instruction fixtures**:
  - Verified all 135 GNU `as` / `axiom0` reference fixtures from `tests/encode/encode_tests.inc`, `tests/mc/frame/main_42.mc` (78 bytes), stack probe boundary fixtures (`4088`, `4096`, `4097`, `4104` bytes), and end-to-end COFF `.obj` differential byte comparisons (`relocs.obj` 359 bytes, `ret42.obj` 326 bytes).
- **[x] Full test suite passes; build warning-free; archcheck clean**:
  - `python tools/archcheck.py` (inside `build-snap-T084d/`): `archcheck: 189 files scanned, 0 violations`.
  - Relevant suites (`selfhost/encode`, `selfhost/obj`, `encode`, `mc`, `obj`, `link`, `run/vs1`): `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`.
- **[x] Report `_workspaces/reports/T084d-report.md` with exact `## Files changed`**:
  - Verified `_workspaces/reports/T084d-report.md` ends with `STATUS: COMPLETE round=0` and lists all modified files.

### 4. Boundary Cross-Check & Added QA Tests
- Checked the seam between `compiler.target.x64.encode` and `compiler.obj.coff` (`Section`, `ObjModel`, `Reloc`, `SymbolId`, `SectionId`, `coff_write_u32_le`) as well as Stage-0 C `encode.c` / `frame.c`.
- Added `tests/selfhost/encode/qa_encode_edge_cases.ax` covering:
  1. Exact `disp8`/`disp32` transition boundaries (`-129`, `-128`, `0`, `127`, `128`), `RBP`/`R13` (`base_low3 == 5`) with SIB index and `disp == 0` forcing `mod = 01` + `disp8 = 0x00`, and negative RIP-relative displacements.
  2. `REG_RAX` accumulator short-form vs `REG_R8` (`low3 == 0`) non-accumulator encoding across `add_ri`, `sub_ri`, `cmp_ri`, `or_ri`, and `test_ri` at 8/16/64-bit widths and `imm8`/`imm32` boundaries (`-129`, `-128`, `127`, `128`).
  3. 8-bit and 16-bit unary/multiply/divide/shift/movzx/movsx encodings with `SPL`/`RSI`/`RDI` byte-REX and `R8`..`R15` extended registers, `push_m`/`pop_m` with `REX.XB` (`0x43`), and C `AX_REG_NONE = -1` vs Axiom `REG_NONE = 255` predicate compatibility.
  4. Frame prologue/epilogue exact thresholds (`frame_size = 0`, `127`, `128`, `4096` without probe loop, `4097` triggering the 52-byte page probe loop).
  5. Negative symbol displacement addends (`disp - 4`), out-of-bounds `target_bb` and `fixup_offset` safety in `x64_patch_branch_fixups`/`x64_patch_rel32`, and 8-byte alignment padding in `x64_emit_rodata_slice`.

## Files changed
- `tests/selfhost/encode/qa_encode_edge_cases.ax`

VERDICT: PASS round=0
