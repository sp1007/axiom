# ADR-0024: MIR Region Representation and Capability Tracker Prerequisite

## Context
Task T048 (Views & capabilities: view/mut_view, regions, conflicts, escapes) was blocked because the underlying MIR region representation and capability tracking data structures are missing. Implementing the full capability semantics requires a complete dataflow analysis over MIR to compute region relations (DISJOINT, OVERLAPS, etc.) and to detect view escapes/conflicts as defined in SPEC-11-capability.md. Doing this concurrently with the type-level capability implementation in a single task is too large and complex.

## Decision
We split the implementation by introducing a prerequisite task, T123. T123 will be responsible for defining the MIR region representations, the capability tracker data structures, and the foundational algorithms for computing region relations. T048 will depend on T123, allowing T048 to focus purely on the frontend and capability semantics using the infrastructure provided by T123.

## Consequences
- **Positive**: Reduces the scope of T048, making it more manageable. Clear separation of concerns between MIR infrastructure and frontend semantic checks.
- **Negative**: Adds a sequential dependency which slightly increases the overall number of tasks, but improves parallelization potential of other MIR tasks.
