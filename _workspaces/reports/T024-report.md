# T024 - Object model + x86-64 encoder core

## Summary
Implemented the object model containing Section, Relocation, and Symbol structures.
Implemented the target-neutral x86-64 encoder core, translating LIR concepts into x86-64 machine instructions.
Built a Python-based generator script that hooks into `GNU as` to retrieve ground truth bytes, emitting a C testing header.
Created an exhaustive suite testing forms against `GNU as`, verifying all byte outputs.

## Files changed
- bootstrap/axiom0/src/objmodel/objmodel.h
- bootstrap/axiom0/src/objmodel/objmodel.c
- bootstrap/axiom0/src/target/x64/encode/encode.h
- bootstrap/axiom0/src/target/x64/encode/encode.c
- tools/gen_encode_tests.py
- tests/encode/cdriver_encode.c
- tests/encode/encode.test
- tests/encode/encode_tests.inc

STATUS: COMPLETE round=0
