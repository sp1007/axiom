# ADR-0022 — allow-own-depend-on-mir

## Summary
Update the architectural layer invariants to move `own` (ownership dataflow) to depend on and sit above `mir`.

## Context
During the implementation of T121 (Move dataflow analysis), the ownership checking (`own` layer) required operations on MIR places to effectively trace dataflow for use-after-move and partial moves. However, `archcheck_rules.txt` previously positioned `own` before `mir` in the layer stack (`order ... traits own mir verify ...`), meaning `own` was disallowed from including or interacting with `mir`.
This caused an architectural violation `INV-LAYER-001` when `own.h` attempted to include `mir.h`. Since ownership checking fundamentally revolves around control-flow graphs and places emitted by the MIR builder, it is logically necessary for `own` to sit above `mir`.

## Decision
We adjust the layer order in `archcheck_rules.txt` from `traits own mir verify` to `traits mir own verify`. This correctly models that the MIR is built first, and then the ownership dataflow analysis pass (`own`) consumes/inspects the MIR.

## Consequences
- `own` is now permitted to `#include "mir/mir.h"` and use MIR data structures (`AxLocation`, `AxMirBlock`, `AxMirPlace`, etc.).
- `mir` may no longer depend on `own` (which is natural, as the MIR builder should not perform ownership checks itself).
- `archcheck` will pass for T121 and future ownership dataflow checks.
