# Typed ID Tables and Interners for Compiler Data Model

## Overview

`std.collections.idtable` provides typed ID newtypes, dense contiguous ID tables, and deterministic interners for the self-hosted Axiom compiler. This mirrors the stage-0 kernel architecture in `bootstrap/axiom0/src/kernel/id.h` and `bootstrap/axiom0/src/kernel/interner.h` (tasks/0260 ABOOT-52..57, 0172 AKERNEL-24, 0153 ACKERNEL-20..23).

In Axiom's compiler architecture, raw pointers across phase boundaries are prohibited. Instead, all AST nodes, symbols, source files, and types are identified by typed integer IDs stored in dense tables.

## 1. Typed ID Newtypes Pattern

Each semantic domain has its own newtype struct wrapping `u32`:
- `StrId`: Interned string spelling identity
- `FileId`: Source file identity in the compilation session
- `NodeId`: AST or HIR node index
- `SymbolId`: Resolved symbol table identity
- `TypeId`: Interned semantic type identity

### Conventions (INV-KERN-001)
- **None / Invalid ID**: `v == 0`. Every ID type provides `.none()`, `.is_none()`, and `.is_some()`.
- **1-Based Dense Numbering**: Real IDs have `v = table_index + 1`. The first item inserted into any table receives ID `1`.
- **Determinism**: IDs are assigned sequentially in insertion order and never reused or renumbered. IDs never depend on memory addresses (INV-KERN-002).
- **Conversions**: `.from_index(idx)` produces `v = idx + 1`, and `.index()` extracts the 0-based array index `(v - 1)`.

```axiom
let file = FileId.from_index(0); // v = 1
if file.is_some() {
    let idx = file.index(); // 0
}
```

## 2. ID Tables (`RawIdTable` & `U32IdTable`)

ID tables provide dense, contiguous storage indexed by typed IDs.

- **`RawIdTable`**: Untyped contiguous backing store with configurable element size and alignment.
- **`U32IdTable`**: High-performance typed table storing 32-bit values (indices, node IDs, offsets).
- **Access Safety**: Out-of-bounds or `none` ID accesses return default values or null pointers. In production compiler phases, lookups validate `Table_contains(t, id)`.
- **Iteration Order**: `first(t)` and `after(t, id)` traverse entries strictly in insertion (ID) order:
```axiom
let mut id = u32_idtable_first(view(table));
while id != 0 {
    let val = u32_idtable_get(view(table), id);
    // process val...
    id = u32_idtable_after(view(table), id);
}
```

## 3. String Interner (`StrInterner`)

The string interner (`StrInterner`) maps byte strings to dense `StrId`s:
- **Deduplication**: Identical strings receive the identical `StrId`.
- **Arena-Backed Storage**: Interned string bytes are stored immutably in an arena (`Arena`), null-terminated, and remain valid for the interner's lifetime.
- **Deterministic Hashing**: Built with AXH64 v1 (matching `bootstrap/axiom0/src/kernel/hash.c` and T073). Hash tables maintain determinism across different runs, platforms, and address-space layouts.
- **First-Interning Order**: `StrId` values (1, 2, 3...) depend solely on the sequence of calls to `interner_intern`, never on memory addresses or hash values.

```axiom
let mut interner = interner_new();
let id1 = interner_intern(mut_view(interner), "foo");
let id2 = interner_intern(mut_view(interner), "foo");
// id1.v == id2.v (deduplicated)
let sv = interner_get(view(interner), id1); // StrView { ptr, len }
interner_free(mut_view(interner));
```

## 4. Value Interner (`U32Interner`)

The `U32Interner` provides deterministic hash-consing for 32-bit values (primitive type tags, tuple arities, flags):
- Values are deduplicated via AXH64-hashed hash table.
- IDs are dense 1-based integers in first-seen order.
- Enables efficient structural equality checks via single integer comparisons.
