---
id: T498j
title: Fix — fullrun-4 R3 ui/backend_ice/sat_u128_emit_mc.test RBP displacement after T498h 8B `sret` slot shrink
phase: P12-numeric-floating-point-simd
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 0
status: done
attempts: 1
paths: [tests/ui/backend_ice/sat_u128_emit_mc.test]
locks: []
spec: [spec/decisions/ADR-0003-backend-pipeline-robustness.md, spec/SPEC-40-integers.md]
covers: [REQ-TST-072]
started: 2026-11-23 15:48:43
finished: 2026-11-23 16:01:38
---
# T498j — Update `ui/backend_ice/sat_u128_emit_mc.test` for `T498h` 16B stack-frame reduction (`fullrun-4` R3)

## Goal
Resolve `fullrun-4` regression R3 (`ui/backend_ice/sat_u128_emit_mc.test`) caused by `T498h` (`2e50e70a`). In `tests/ui/backend_ice/sat_u128_lowered.mir`, `_0` is a 16-byte `u128` (`type#1073676585`) returned via the Win64 hidden `sret` pointer (`RCX`). `T498h` (`compiler/target/x64/frame.ax`, `x64_frame_lower_baseline_in_arena`) shrunk `i == 0` when `frame_size_is_ret_in_mem(size)` from 16 bytes to 8 bytes (storing only the 8-byte `sret` pointer at `[rbp-0x10]`), legitimately shrinking the stack frame by 16 bytes (`sub rsp, 0x90`: `48 81 ec 90 00 00 00`) and shifting all subsequent 16-byte-aligned slots closer to `rbp` by `+0x10`:
- `copy _1` low/high qwords sit at `[rbp-0x60]` / `[rbp-0x58]` (`mov rax, [rbp-0x60]; mov rdx, [rbp-0x58]` -> `48 8b 45 a0 48 8b 55 a8`);
- `copy _2` low/high qwords sit at `[rbp-0x70]` / `[rbp-0x68]` (`disp8` = `0x90` / `0x98`, shifted from `0x80` / `0x88`);
- 128-bit `SatAdd` emits `add rax, [rbp-0x70]; adc rdx, [rbp-0x68]; mov r8, -1; cmovb rax, r8; cmovb rdx, r8` (`48 03 45 90 48 13 55 98 49 b8 ff ff ff ff ff ff ff ff 49 0f 42 c0 49 0f 42 d0`).

Repro before fix (in an isolated snapshot):
```
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -v ui/backend_ice/sat_u128_emit_mc.test
```

## Scope
- Update `tests/ui/backend_ice/sat_u128_emit_mc.test`:
  - Update the comment to document the post-`T498h` frame layout (`sub rsp, 0x90` with 8-byte `sret` pointer slot `_0` at `[rbp-0x10]`, `copy _1` at `[rbp-0x60]`/`[rbp-0x58]`, and `copy _2` at `[rbp-0x70]`/`[rbp-0x68]`).
  - Update `stdout-contains:` to verify the complete 128-bit `SatAdd` sequence (`48 03 45 90 48 13 55 98 49 b8 ff ff ff ff ff ff ff ff 49 0f 42 c0 49 0f 42 d0`: `add rax,[rbp-0x70]; adc rdx,[rbp-0x68]; mov r8,-1; cmovb rax,r8; cmovb rdx,r8`) plus prologue `48 81 ec 90 00 00 00` (`sub rsp, 0x90`) so both the frame size and full saturating-add instruction encoding are pinned faithfully.

## Acceptance
- [ ] `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v ui/backend_ice` passes all tests in `tests/ui/backend_ice/`.
- [ ] `python tools/taskgate.py --task T498j --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` exits 0 (`BASELINE OK`, `archcheck` clean).
- [ ] Report `_workspaces/reports/T498j-report.md` written with exact `## Files changed` and `STATUS: COMPLETE round=0`.

## Out of scope
- Any changes to `compiler/`, `tests/ui/backend_ice/sat_u128_lowered.mir`, `spec/`, `bootstrap/axiom0/`, or `docs/`.

## Log
- 2026-11-23 created by axiom-architect (fullrun-4 triage R3; culprit T498h `2e50e70a`)
- 2026-11-23 15:48:43 started (attempt 1) axiom-backend
- 2026-11-23 16:01:38 accepted by QA -> done
