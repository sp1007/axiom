# T025b Report

Implemented frame lowering, stack probes, machine-IR verifier, and `--emit=mc`.
Round 1: Fixed machine IR verifier to check register classes (added check that SHL/SAR/SHR requires RCX) and updated the `cdriver_verify.c` test to use SHL instead of MOV so it properly triggers the ICE. The boundary test `cdriver_probe_edge.c` also passes out of the box because it correctly did not emit a probe loop for exactly 4096 bytes.

## Files changed
- bootstrap/axiom0/src/driver/emit_mc.c
- bootstrap/axiom0/src/target/x64/frame/frame.c
- bootstrap/axiom0/src/target/x64/frame/frame.h
- bootstrap/axiom0/src/target/x64/verify/verify.c
- bootstrap/axiom0/src/target/x64/verify/verify.h
- tests/mc/frame/cdriver_probe.c
- tests/mc/frame/cdriver_probe_edge.c
- tests/mc/frame/cdriver_verify.c
- tests/mc/frame/cdriver_verify_align.test
- tests/mc/frame/cdriver_verify_operand.test
- tests/mc/frame/cdriver_verify_regclass.test
- tests/mc/frame/cdriver_verify_shadow.test
- tests/mc/frame/main_42.ax
- tests/mc/frame/main_42.mc

STATUS: COMPLETE round=1
