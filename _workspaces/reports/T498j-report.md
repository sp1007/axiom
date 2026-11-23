# T498j Report — Fix `ui/backend_ice/sat_u128_emit_mc.test` RBP displacement after T498h

## Summary
Updated `tests/ui/backend_ice/sat_u128_emit_mc.test` to match the post-`T498h` stack frame layout (`sub rsp, 0x90`, 8-byte `sret` pointer slot `_0` at `[rbp-0x10]`, `copy _1` at `[rbp-0x60]`/`[rbp-0x58]`, and `copy _2` at `[rbp-0x70]`/`[rbp-0x68]`).

Pinned both:
- Prologue `48 81 ec 90 00 00 00` (`sub rsp, 0x90`)
- Complete 128-bit `SatAdd` machine-code sequence `48 03 45 90 48 13 55 98 49 b8 ff ff ff ff ff ff ff ff 49 0f 42 c0 49 0f 42 d0` (`add rax,[rbp-0x70]; adc rdx,[rbp-0x68]; mov r8,-1; cmovb rax,r8; cmovb rdx,r8`)

Zero compiler files were modified.

## Files changed
- `tests/ui/backend_ice/sat_u128_emit_mc.test`

## Verification (inside `build-snap-T498j/`)
- `python tools/build_axiomc.py --out build --root . --stage 2`: `BUILD-AXIOMC OK` (`FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`, sha256=`43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6`).
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v ui/backend_ice`: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (exit 0).
- `python tools/taskgate.py --task T498j --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: `TASKGATE T498j exit=0`, `TOTAL 55 PASS 55 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `archcheck: clean (exit 0) 232 files scanned, 0 violations`.

STATUS: COMPLETE round=0
