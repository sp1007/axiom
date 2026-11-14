# T443 report - bundle_common rejects duplicate module names

## Summary
`tests/selfhost/bundle_common.py::assemble_compiler_modules` now fails at generation time when a module is listed
twice, instead of emitting a bundle that later produces many `AX_NAME_DUPLICATE` errors (T430 root cause, ADR-0042 section 5).

- New helpers `_canonical_module_name` and `find_duplicate_modules`. Duplicates are detected after normalisation:
  a `.mod` suffix is folded away and `compiler.own.move` / `compiler.own.unsafe` are treated as `compiler.own.move_ck` /
  `compiler.own.unsafe_ck` (the names the assembler emits them under). Tuple-form entries are covered.
- `assemble_compiler_modules(mod_list, root=ROOT, caller=None)` raises `ValueError("duplicate module(s) [...] in module list of <caller>")`
  listing every duplicated module; `caller` defaults to the running script's basename (`sys.argv[0]`), so existing
  generator call sites need no change. No silent de-duplication; the caller's list is not mutated.
- Clean lists are unaffected: all 36 generators produce byte-identical output (see evidence).
- No generator module list contains a duplicate (nothing to report).
- `tests/selfhost/bundle_common_selftest.py` (plain Python, 11 checks) plus a `.test` manifest so `axtest` runs it
  (`selfhost/bundle_common_selftest`; axtest does not run bare `.py` self-tests).

## Evidence
- Self-test: `python tests/selfhost/bundle_common_selftest.py` -> `bundle_common selftest: 11 checks passed`.
- Mutation: replaced `if dups:` by `if False and dups:` in `bundle_common.py` -> self-test fails at the first check with
  `AssertionError: exact duplicate rejected: duplicate module list [...] was accepted`; restored, self-test passes again
  (`grep -c "False and dups"` = 0).
- All 36 `tests/selfhost/*/gen_*.py --check` run sequentially: 36 of 36 exit 0, every output line `... up to date`, 0 DIFFERS/MISSING.
  (`gen_local_symbols_test.py` has no `bundles_current.test` of its own; it is covered here by the direct run.)
- `python tools/axtest.py --no-cache -j 2 --compiler build/axiomc2.exe selfhost/bundle_common_selftest bundles_current`
  -> `TOTAL 35 PASS 35 FAIL 0 SKIP 0 XFAIL 0` (34 `bundles_current.test` + the new test);
  `selfhost/kernel/hash_native_current` -> `TOTAL 1 PASS 1`. No bundle was compiled.
- Native-evidence: the new test is a plain Python host test (`cmd:`), no native Axiom execution; its check is exit 0 plus
  `stdout-contains: bundle_common selftest: 11 checks passed`, and the mutation above proves the assertion is live.

## Files changed
- tests/selfhost/bundle_common.py
- tests/selfhost/bundle_common_selftest.py
- tests/selfhost/bundle_common_selftest.test

## Notes
- The `.test` manifest is not in the task's `paths:` literally but is explicitly allowed by the scope ("otherwise add a
  small `.test` manifest next to it") and lies under the locked `tests/selfhost`.

STATUS: COMPLETE round=0
