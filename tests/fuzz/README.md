# Fuzzing

The `tools/fuzz.py` script is used to fuzz the compiler's frontend (lexer and parser) to catch crashes, ICEs, hangs, and non-determinism.

## Seed Corpus
This directory contains the seed corpus `.ax` files copied from `tests/lex` and `tests/parse`.

## Campaigns

The gate campaign command is:
`python tools/fuzz.py --seed 1 --iterations 200000`

## CI / Smoke
For the CI hook, use the smoke mode:
`python tools/fuzz.py --smoke`
which uses a fixed seed and runs for at most 60 seconds.
