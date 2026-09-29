---
name: axiom-syntax
description: Canonical Axiom surface syntax ruleset (binding/assignment with "=", namespace/path separator ".", no "::", no ":="). MUST be used whenever writing, reading, parsing, testing, or specifying Axiom source code — lexer/parser work, grammar/EBNF, .ax test files, std library code, spec examples, diagnostics with fix-its, or translating examples from docs/base (which mix "::", ":=", "var", "use"). Also use when a spec example conflicts with another and you need the canonical form.
---

# Axiom Canonical Syntax (project-binding decisions)

The design corpus in `docs/base/` was written over a long period and is **inconsistent** in
surface syntax (`::` vs `.`, `:=` vs `=`, `var` vs `let mut`, `use` vs `import`). The project owner
fixed the ambiguity. These rules override every example in `docs/base/`. Why: one obvious way to
write each construct makes code easier for humans and AI to read/generate and removes a whole class
of "which form is right?" confusion.

Semantics are NOT changed by these rules — only spelling. When you port an example from the
specs, translate it with the table below and keep its meaning.

## Rule 1 — Binding and assignment always use `=`

| Construct | Canonical | Never |
|---|---|---|
| Immutable binding | `let x = 10` | `x := 10`, `var x = 10` |
| Typed binding | `let x: i32 = 10` | `x: i32 := 10` |
| Mutable binding | `let mut count = 0` | `var count = 0`, `count := 0` |
| Deferred init | `let x: i32` then `x = 5` (definite-assignment checked) | |
| Assignment | `count = count + 1` | `count := ...` |
| Compound | `+= -= *= /= %= &= \|= ^= <<= >>=` | |
| Shadowing | `let x = x + 1` (new binding, not mutation) | |

`:=` is not an Axiom token. The lexer recognises the character pair only to emit a precise
diagnostic with a fix-it (`AX_LEX_COLON_EQ`: "`:=` is not Axiom syntax; use `let x = …` for a new
binding or `x = …` for assignment"). `var` is not a keyword; if it starts a statement followed by an
identifier and `=`, the parser emits `AX_PARSE_VAR` suggesting `let mut`.

Note: in the specs, `:=` inside EBNF blocks (`Item := Attribute* ...`) is grammar meta-notation,
not Axiom code. In our own grammar files avoid both `:=` and `::=` — write EBNF ISO-style
(`rule = a , b ;`) so the notation never looks like Axiom.

## Rule 2 — Every path separator is `.`

| Construct | Canonical | Never |
|---|---|---|
| Module declaration | `module graphics.render` | `module graphics::render` |
| Import | `use std.io.print` | `use std::io::print`, `import std::io` |
| Grouped import | `use std.collections.{Vec, Map}` | |
| Import alias | `use std.collections.HashMap as Map` | |
| Enum variant | `Result.Ok(v)`, `Option.None` | `Result::Ok(v)` |
| Associated item | `Self.Item`, `T.Item`, `Vec.new()` | `Self::Item`, `Vec::new()` |
| Qualified trait call | `Display.display(p)` | `Display::display(&p)` |
| Package-qualified | `mylib.parse.Token` | |

`::` is not an Axiom token; lexer emits `AX_LEX_COLON_COLON` with a fix-it replacing it by `.`.
`use` is the only import keyword (`import` is rejected with a fix-it).

Prelude items (`Option`, `Result`, `Some`, `None`, `Ok`, `Err`, `print`, `drop`, …) are usable
unqualified: `Some(3)`, `Ok(v)`.

### How `.` is disambiguated (resolver, not parser)

Because values, modules, types and enums share one separator, the **parser does not decide** what
`a.b.c` means. It builds a `DottedChain` (primary + segments). The **resolver** resolves the leftmost
segment with the frozen lookup order — local → parameter → current module → explicit import →
re-export → prelude — and then walks right:

- leftmost is a **value** (local/param/const/static) → every following segment is a field, tuple
  index, or method call;
- leftmost is a **module/package** → next segment is looked up inside that module;
- leftmost is a **type/enum/trait** → next segment is an associated item / variant / method;
- once a segment resolves to a value, the rest are value accesses.

A local that shadows a module name wins (lookup order); emit warning `AX_NAME_SHADOW_MODULE`.
This mirrors how Go, Java, Zig and C# work, and costs nothing at run time.

### Generic arguments in expression position

Without Rust's turbofish, `f<T>(x)` could be read as comparisons. Rule: comparison operators in
Axiom are **non-associative** (`a < b > c` is already a syntax error), so in expression position the
parser tentatively parses `<TypeArgs>` after an identifier / dotted segment and **commits** iff the
closing `>` is immediately followed by `(`, `.`, or `{` (struct literal context). Otherwise it
backtracks and parses a comparison. Examples: `Vec<i32>.new()`, `size_of<T>()`,
`parse<u32>(s)?`, `Point<f32> { x: 1.0, y: 2.0 }`.

## Rule 3 — Other canonical forms (from frozen BOOTSTRAP-217, restated)

- Statements end at newline when unambiguous; `;` is an optional explicit terminator. A line that
  ends with a binary operator, `,`, `(`, `[`, `{`, `.` or `=` continues on the next line; a line that
  *starts* with `.` continues the previous expression (method chains).
- Functions: `fn add(a: i32, b: i32) -> i32 { a + b }` — last expression is the value; `return x`
  is explicit early return.
- Struct literal fields separated by newline or `,`: `Point { x: 1.0, y: 2.0 }`.
- Fixed array type `[4]i32`; array literal `[1, 2, 3, 4]`; slice `a[1..3]`.
- Ranges `0..10`, `0..=10` (lexer must not confuse `1..2` with float `1.` — ranges win; `1.0` needs
  a digit after the dot). Tuple index `p.0`, nested `p.0.1` lexes as `p` `.` `0` `.` `1`.
- Views: `view<T>`, `mut_view<T>`; no `&`, `&mut`, or safe `*x`. Raw pointers `*const T`, `*mut T`
  only in `unsafe`; `p->field` sugar in unsafe.
- Methods: `fn length(self: view<Vec2>) -> f32`; `v.length()` is sugar for `length(v)`.
- Traits `trait Display { fn display(self: view<Self>) -> Str }`, `impl Display for Point { … }`.
- Attributes `@repr(C)`, `@entry`, `@derive(Copy, Clone)`; unknown attributes are errors.
- Closures `|a, b| a + b`, typed `|a: i32| -> i32 { a * 2 }`.
- Errors: `let v = op()?`; `panic("msg")`; `assert(cond)`.
- Visibility `pub`, `pub(package)`, `pub(module)`; default private.
- Comments `//`, nested `/* */`, doc `///`.
- Integer literals `42`, `42u32`, `0xff`, `0b1010`, `0o17`, `1_000`; floats `1.0`, `1e10`, `2.5f32`.
- Strings `"…"` (UTF-8, escapes `\n \t \\ \" \u{…}`), byte strings `b"…"`, chars `'a'` if enabled by
  the lexical spec.

## Rule 4 — Fixed-address declarations (owner requirement, ADR-0001)

Low-level code may bind statics and functions to absolute addresses and then use them normally:

```axiom
@at(0x4000_1000)
unsafe static UART0: UartRegs          // overlay: object already exists there (no initializer)

@at(0x0000_0000)
unsafe static VECTORS: [48]fn() = [reset, nmi, hard_fault]   // placement: we emit it there

@at(0xFFFF_0400)
unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32   // routine already in ROM

UART0.ctrl = UartCtrl.ENABLE           // ordinary field access; Mmio<T> fields are volatile
```

Module-relative overlays for ASLR'd images (hosted profile, resolved at load time, ADR-0001 §5):
`@at(image("game.exe") + 0x1A_2B30) unsafe extern "C" fn f(x: i32) -> i32`, `@at(image_self() + 0x2000)`.

No initializer / `extern fn` = overlay; initializer or body = placement. The address is a
compile-time constant; the type needs a defined layout (`@repr(C)`/primitive). Freestanding/system
profiles only. Semantics land in epic E13.6; Stage-0 parses `@at` and reports
`AX_ADDR_UNSUPPORTED_STAGE0`.

## Canonical example

```axiom
module demo.geometry

use std.io.print
use std.math.sqrt

struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}

enum Shape {
    Circle(f32)
    Rect(Vec2)
}

fn area(s: view<Shape>) -> f32 {
    match s {
        Shape.Circle(r) => 3.14159 * r * r
        Shape.Rect(v) => v.x * v.y
    }
}

fn main() -> i32 {
    let mut total = 0.0
    let v = Vec2 { x: 3.0, y: 4.0 }
    total = total + v.length()
    let parsed = parse<u32>("42")?
    if total > 4.0 { 0 } else { 1 }
}
```

## Translating spec examples

When a spec shows `Result::Ok(x)`, `x := f()`, `var n = 0`, `use a::b`, write
`Result.Ok(x)`, `let x = f()`, `let mut n = 0`, `use a.b`. If a translation seems to change meaning
(e.g. a spec relies on `::` to separate a value from a module with the same name), do not guess —
record it in `spec/decisions/` via the axiom-architect agent.

The authoritative long-form grammar lives in `spec/SPEC-02-grammar.md` once task T001 lands;
this skill is the short, binding summary and wins if the two disagree until the architect
reconciles them.
