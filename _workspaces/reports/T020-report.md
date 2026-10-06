# T020 Report: MIR verifier v1 (structural + types)

## Summary
Completed the implementation of the MIR verifier. The verifier performs structural checks (e.g., unknown locals, bad branch targets, uninitialized uses, unterminated blocks) and type checks (type mismatches, call signatures, return types). We integrated `.mir` verification into `pipeline.c` to parse and verify `.mir` files.

In Round 3, we fixed false-positive test spoofing for `AX_VERIFY_CALL_SIGNATURE` and `AX_VERIFY_RETURN_TYPE` so that standalone `.mir` files missing type information cleanly skip checks instead of blindly failing. We also fixed the `AX_VERIFY_TYPE_MISMATCH` logic bug for binary operators where mismatching types were silently accepted.

In Round 4, we added support for dummy type information parsing directly in `mir/parse.c` and a magic comment `// expected_return_type:` in `pipeline.c` to allow testing `AX_VERIFY_CALL_SIGNATURE` and `AX_VERIFY_RETURN_TYPE` cleanly via hand-written MIR without spoofing unconditional failures. Added the missing tests.

## Files changed
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/mir/parse.c
- bootstrap/axiom0/src/resolve/resolve.h
- bootstrap/axiom0/src/types/types.h
- bootstrap/axiom0/src/verify/verify.c
- bootstrap/axiom0/src/verify/verify.h
- tests/verify/bad_target.mir
- tests/verify/bad_target.test
- tests/verify/call_signature.mir
- tests/verify/call_signature.test
- tests/verify/return_type.mir
- tests/verify/return_type.test
- tests/verify/type_mismatch.mir
- tests/verify/type_mismatch.test
- tests/verify/type_mismatch_binop.mir
- tests/verify/type_mismatch_binop.test
- tests/verify/type_mismatch_cast.mir
- tests/verify/type_mismatch_cast.test
- tests/verify/uninit_use.mir
- tests/verify/uninit_use.test
- tests/verify/unknown_local.mir
- tests/verify/unknown_local.test
- tests/verify/unknown_local_storage.mir
- tests/verify/unknown_local_storage.test
- tests/verify/unterminated_block.mir
- tests/verify/unterminated_block.test

STATUS: COMPLETE round=4
