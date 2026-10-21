# Owner requirements (highest priority)

Requirements stated directly by the project owner. They override every document in `docs/base`.
T110 must copy each row into `CATALOG.md` unchanged (same id) and keep this file as the source.
New owner requirements are appended here with the next id.

| REQ-OWNER-001 | grammar | v1-core | Binding and assignment use only `=` (`let x = …`, `let mut x = …`, `x = …`); `:=` and `var` are not Axiom syntax and get fix-it diagnostics | owner 2026-09-29; axiom-syntax Rule 1 | T001, T010, T011 |
| REQ-OWNER-002 | grammar | v1-core | `.` is the only namespace/library/path separator (`use std.io.print`, `Result.Ok(v)`, `Self.Item`); `::` is not Axiom syntax and gets a fix-it diagnostic; the resolver disambiguates dotted chains | owner 2026-09-29; axiom-syntax Rule 2 | T001, T010, T014 |
| REQ-OWNER-003 | layout | v1-full | In low-level code, variables, arrays, structs, functions (all static items with defined layout/ABI) can be declared at a fixed memory address (`@at(addr)`), as overlay or placement, and then used with ordinary syntax when the declaration is correct | owner 2026-09-29; ADR-0001 | EPIC(E13.6) |
| REQ-OWNER-004 | bootstrap | v1-core | The C Stage-0 compiler implements only the self-host subset; later features are written once, in Axiom, while core data models reserve extension points for them | owner 2026-09-29; ROADMAP R7 | T003a |
| REQ-OWNER-005 | layout | v1-full | Code in a DLL/EXE can bind functions and data of another module loaded in the same process at `module base + offset` (`@at(image("game.exe") + 0x1A2B30)`), resolved at load time, and call/use them with ordinary syntax; Axiom can produce PE DLLs (exports, DllMain initialiser, relocations) | owner 2026-09-29; ADR-0001 §5-6 | EPIC(E13.7) |
| REQ-OWNER-006 | linker | v1-full | On x86_64-windows Axiom emits and consumes every artifact kind: .obj and .exe (core), static .lib archives and .dll with import libraries (right after self-hosting, in axiomc); the core's data models reserve these kinds from day one | owner 2026-09-29 | T026, T028, T750, T751 |
| REQ-OWNER-007 | types | v1-full | In complex mathematical expressions mixing unsuffixed numeric literals (`1`, `-3`, `0x3F`, `0.5`, `6.0`) and variables of different numeric types (`i8..usize`, `f32`, `f64`) across nested arithmetic, bitwise/shift, unary, array-index, call, and comparison sub-expressions (e.g. `((a + i * k - 1) / (2 * n + u - 3)) * (w + 0.5) + (base - u * 4 + i) / (a * a / 6.0 - k + 2)` and `(((mask >> sh) & 0x3F) + delta * step - 5) * scale / ((1 << sh) + 3)`), the compiler automatically infers literal types and promotes narrower integer/float variables along a deterministic numeric lattice lowered to explicit MIR casts so no suffixes or manual `as` casts are required | owner 2026-10-21 | EPIC(E12.2) |

Note: rows referencing tasks will be completed with `covers:` entries by T111.

Status note 2026-10-01 (audit 2026-09-30, ADR-0002..0006): no owner requirement was dropped,
re-tiered or re-sequenced. The task ids in the rows above are unchanged; T003a additionally produces
`spec/selfhost-subset.tsv` for REQ-OWNER-004. The owner's rule that samples print
`Xin chào thế giới` (UTF-8, correct on pipe, file and console) is kept, and its console part is now
checked by a script instead of by eye (T042, T074; ADR-0005 §16, ADR-0006 §9).
