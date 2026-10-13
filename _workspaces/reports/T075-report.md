# T075 — Library conformance + real-program suite

## Summary of Work
Completed Phase 9 milestone gate `T075`: standard library conformance test suite, real program benchmarks, scale test generator, and compilation profile measurements.

1. **Real Program Suite (`tests/programs/`)**:
   - `word_count.ax`: counts lines, words, bytes, and max word length across multi-line text input. Passes 3/3 execution modes (`interp`, `native`, `native-O1`).
   - `tokenizer.ax`: lexical analyzer tokenizing keywords, identifiers, integers, symbols, and operators. Passes 3/3 execution modes.
   - `json_parser.ax`: recursive descent JSON parser and query engine evaluating nested objects and arrays. Passes 3/3 execution modes.
   - `expr_interp.ax`: stack-based bytecode virtual machine evaluating arithmetic expressions and conditional branches. Passes 3/3 execution modes.
   - `sorting.ax`: in-place insertion sort, selection sort, bubble sort, and shell sort with sortedness and element checksum verification. Passes 3/3 execution modes.
   - All 5 programs pass without leaks; timings recorded in `tests/perf/programs.csv`.

2. **Standard Conformance Suite (`tests/conformance/std/`)**:
   - `0169_std_core_option_result.ax`: validates `Option<T>` and `Result<T, E>` semantics, discriminant extraction, pattern matching, unwrap helpers (`// test: diff`).
   - `0169_std_text_str.ax`: validates `Str`, UTF-8 byte lengths, multi-byte Vietnamese Unicode, binary string literals (`// test: diff`).
   - `0169_std_for_iter.ax`: validates for-loop iteration, step adapters, and range reductions (`// test: diff`).
   - `0169_std_collections_map.ax`: validates associative hash table insertion, key lookup, replacement, collision handling (`// test: diff`).
   - `0169_std_arena_interner.ax`: validates bump allocator alignment calculation and fixed capacity symbol interner (`// test: diff`).
   - `0169_std_format_bytes.ax`: validates byte buffer formatting of integers and byte slice concatenation (`// test: diff`).
   - All 6 conformance tests pass differentially across `interp`, `native`, and `native-O1`.

3. **Scale Test Generator & Benchmark (`tools/gen_large.py`, ADR-0005 §7)**:
   - Implemented `tools/gen_large.py` generating deterministic, valid Axiom programs of configurable scale (default 100,000 lines).
   - Generates all required scale patterns:
     - Large constant tables in `.rdata` (T061d)
     - 200-arm match statement
     - 500-deep nested expression
     - Deep generics (`GenPair<T>`, `gen_step_0`..`10`)
     - Long functions with bounded local variable frames
   - 5k-line variant compiles and runs correctly in interpreter mode (`OK scale`).
   - 100k-line program compiles natively in **12.055 s** (budget `< 30 s`) and uses **~830 MB RAM** (budget `< 2 GB`).
   - The compiled native 100k-line binary executes and outputs `OK scale`.
   - Pass breakdown recorded in `tests/perf/scale.csv`.

## Files changed
- tests/conformance/std/0169_std_arena_interner.ax
- tests/conformance/std/0169_std_collections_map.ax
- tests/conformance/std/0169_std_core_option_result.ax
- tests/conformance/std/0169_std_for_iter.ax
- tests/conformance/std/0169_std_format_bytes.ax
- tests/conformance/std/0169_std_text_str.ax
- tests/perf/programs.csv
- tests/perf/scale.csv
- tests/programs/expr_interp.ax
- tests/programs/json_parser.ax
- tests/programs/sorting.ax
- tests/programs/tokenizer.ax
- tests/programs/word_count.ax
- tools/gen_large.py

## Verification
- `tools/archcheck.py`: 188 files scanned, 0 violations.
- `reqcov.py --strict`: 0 gaps, COVERAGE OK.
- `harness_check.py`: HARNESS OK.
- `tools/gatecheck.py --gate T075 --no-run`: MS-P1 through MS-P9 all PASS.
- Full test suite: 1519/1519 tests PASS.
- Scale test budget: 12.055 s (< 30 s), ~830 MB (< 2 GB), native execution verified.

STATUS: COMPLETE round=0
