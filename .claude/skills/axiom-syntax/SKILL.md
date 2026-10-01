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

The full, authoritative text is `spec/SPEC-01-lexical.md` (tokens, rule ids `AXS-LEX-NNN`) and
`spec/SPEC-02-grammar.md` (EBNF, precedence, 26 example programs, rule ids `AXS-GRM-NNN`), with the
decisions in ADR-0007 (spelling), ADR-0008 (newlines), ADR-0009 (lexical), ADR-0010 (grammar forms).
This skill is the short summary of them.

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
binding or `x = …` for assignment") and continues as if `=` had been written. `var` is not a
keyword; if it starts a statement and is followed on the same line by an identifier, the parser
emits `AX_PARSE_VAR` suggesting `let mut`.

Assignment is a **statement**, not an expression: `if x = 5 { }`, `f(x = 1)` and `a = b = c` are
syntax errors (`AX_PARSE_ASSIGN_IN_EXPR`). A match arm or closure that assigns uses a block:
`Some(v) => { total += v }`.

Note: in the specs, `:=` inside EBNF blocks (`Item := Attribute* ...`) is grammar meta-notation,
not Axiom code. In our own grammar files avoid both `:=` and `::=` — write EBNF ISO-style
(`rule = a , b ;`) so the notation never looks like Axiom.

## Rule 2 — Every path separator is `.`

| Construct | Canonical | Never |
|---|---|---|
| Module declaration | `module graphics.render` | `module graphics::render`, `mod render` |
| Import | `use std.io.print` | `use std::io::print`, `import std::io` |
| Grouped import | `use std.collections.{Vec, Map}` | |
| Import alias | `use std.collections.HashMap as Map` | |
| Enum variant | `Result.Ok(v)`, `Option.None` | `Result::Ok(v)` |
| Associated item | `Self.Item`, `T.Item`, `Vec.new()` | `Self::Item`, `Vec::new()` |
| Qualified trait call | `Display.display(p)` | `Display::display(&p)` |
| Package-qualified | `mylib.parse.Token` | |

`::` is not an Axiom token; the lexer emits `AX_LEX_COLON_COLON` with a fix-it replacing it by `.`
and continues with a `.` token. `use` is the only import keyword (`import a.b` at item position is
rejected with `AX_PARSE_IMPORT` and a fix-it; `mod x` with `AX_PARSE_MOD`). No glob imports, no
inline modules.

Prelude items (`Option`, `Result`, `Some`, `None`, `Ok`, `Err`, `print`, `drop`, `len`, …) are
usable unqualified: `Some(3)`, `Ok(v)`.

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
Axiom are **non-associative** (`a < b > c`, `a == b == c` are syntax errors), so in expression
position the parser tentatively parses `<TypeArgs>` after an identifier / dotted segment (the `<`
on the same line) and **commits** iff the closing `>` is immediately followed by `(`, `.`, or `{`
(struct literal; not inside an `if`/`while`/`match`/`for` header). Otherwise it backtracks and parses
a comparison. Examples: `Vec<i32>.new()`, `size_of<T>()`, `parse<u32>(s)?`,
`Point<f32> { x: 1.0, y: 2.0 }`. Known corner: `f(a < b, c > (d))` is read as the generic call
`a<b, c>(d)` — parenthesise the comparisons.

## Rule 3 — Other canonical forms (SPEC-01 / SPEC-02 in brief)

- **Statements** end at a line break or `;` (also before `}`). A line that ends with a binary
  operator, `,`, `(`, `[`, `{`, `.` or `=` continues on the next line; a line that *starts* with `.`
  continues the previous expression (method chains). An operator that can only be binary or postfix
  (`+ / % ^ & && == != < <= > >= << >> = += … ? as`) at the start of a line is an error
  (`AX_PARSE_LEADING_OPERATOR`). **`-`, `*`, `!`, `~`, `|`, `||`, `(`, `[`, `{` at the start of a
  line start a new statement, silently** — `let d = a` ↵ `- b` is two statements. So always put the
  operator at the end of the previous line (or parenthesise). Inside `( )` and `[ ]` line breaks
  never matter. `return`/`break`/`continue` take a label or value only from the same line.
  `else`, `where` and an opening `{` may start a line. Two statements on one line need `;`.
- **Blocks** are expressions: the last expression without `;` is the value; a final `;` discards it.
- Functions: `fn add(a: i32, b: i32) -> i32 { a + b }`; `return x` is the explicit early return.
  Qualifier order `[unsafe] [extern "C"] fn`. No items inside function bodies.
- Struct fields, enum variants, match arms and struct-literal fields are separated by a line break
  or `,`: `Point { x: 1.0, y: 2.0 }`; shorthand `Point { x, y }`. In an `if`/`while`/`match`/`for`
  header `Name {` is not a struct literal (parenthesise).
- Fixed array type `[4]i32` (never `[i32; 4]`); array literal `[1, 2, 3, 4]`; repeat `[0u8; 16]`;
  dynamic-length sequence behind a view `view<[u8]>`; sub-ranges `a[1..3]`, `a[1..]`, `a[..3]`.
- Ranges `0..10`, `0..=10` (the lexer never confuses `1..2` with a float — a float needs digits on
  both sides of the point: `1.0`). Tuple index `p.0`, nested `p.0.1` lexes as `p` `.` `0` `.` `1`.
- Operator precedence, tightest first: postfix; prefix `- ! ~ *`; `as`; `* / %`; `+ -`; `<< >>`;
  `&`; `^`; `|`; comparisons (non-associative); `&&`; `||`; `..`/`..=`. So `flags & MASK == 0` is
  `(flags & MASK) == 0`. `!` is logical not, `~` is bitwise not; there is no unary `+`.
- Views: `view<T>`, `mut_view<T>`, expressions `view(x)`, `mut_view(x)` (`view`/`mut_view` are
  keywords); no `&`, `&mut`, or safe `*x`. Raw pointers `*const T`, `*mut T` only in `unsafe`;
  `p->field` sugar in unsafe.
- Methods: the receiver is the first parameter, named `self`, always with a type —
  `fn length(self: view<Vec2>) -> f32`, `self: mut_view<Self>`, `self: Self` (no bare `self`).
  Methods may be free functions or inside `impl Type { … }`; `v.length()` is sugar for `length(v)`.
- Traits `trait Display { fn display(self: view<Self>) -> Str }`, `impl Display for Point { … }`,
  destructor `impl Drop for T { fn drop(self: mut_view<T>) { … } }`.
- Generics `fn max<T: Ord>(a: T, b: T) -> T`, `where T: A + B,` clauses (comma-separated).
- Attributes `@repr(C)`, `@entry`, `@derive(Copy, Clone)`, `@link("kernel32")`; unknown attributes
  are errors. FFI: `extern "C" { fn puts(s: *const u8) -> i32 }`, `extern "system" { … }`.
- Closures `|a, b| a + b`, typed `|a: i32| -> i32 { a * 2 }`; capture is inferred (no `move`).
- Loops `loop { }`, `while c { }`, `for x in xs { }`; labels `'outer: loop { … break 'outer … }`;
  `break value` from `loop`. `return`/`break`/`continue` may be a match-arm body.
- Patterns: `_`, bindings (`mut x`), literals (integers, chars, bools), ranges `'a'..='z'`, `0..10`,
  or-patterns `a | b`, variants `Shape.Circle(r)`, structs `Point { x, .. }`, tuples, guards
  `x if x > 0 =>`; `if let`, `while let`, `let Some(v) = e else { return }`.
- Casts `x as u32`, `enum_value as u8` (fieldless enums), `n as char` (checked for `u32`).
- Errors: `let v = op()?`; `panic("msg")`; `assert(cond)`.
- Visibility `pub`, `pub(package)`, `pub(module)`; default private.
- Comments `//`, nested `/* */`, doc `///`.
- Identifiers are ASCII (`[A-Za-z_][A-Za-z0-9_]*`) in v0.1; strings, chars and comments are full
  UTF-8. `_` alone is the wildcard.
- Integer literals `42`, `42u32`, `0xff`, `0b1010`, `0o17`, `1_000` (`_` only between digits);
  floats `1.0`, `1e10`, `2.5f32`; byte literal `b'a'` (a `u8`).
- Strings `"…"` (UTF-8, one line, escapes `\n \r \t \\ \" \' \0 \xNN \u{…}`), raw strings `r"…"`,
  byte strings `b"…"`, chars `'a'`, `'ế'`, `'\n'`. No string interpolation: `{` is an ordinary
  character.
- Keywords (37): `as async await break comptime const continue dyn else enum extern false fn for if
  impl in let loop match module mut mut_view pub return self Self static struct trait true type
  unsafe use view where while`. Reserved for later: `move union yield`. Not keywords: `var`,
  `import`, `mod`, primitive type names. `async`/`.await`/`comptime` have fixed grammar but are
  implemented after self-hosting.

## Rule 4 — Fixed-address declarations (owner requirement, ADR-0001)

Low-level code may bind statics and functions to absolute addresses and then use them normally:

```axiom
@at(0x4000_1000)
unsafe static UART0: UartRegs          // overlay: object already exists there (no initializer)

@at(0x0000_0000)
unsafe static VECTORS: [3]fn() = [reset, nmi, hard_fault]   // placement: we emit it there

@at(0xFFFF_0400)
unsafe extern "C" fn rom_crc32(data: *const u8, len: usize) -> u32   // routine already in ROM

fn enable_uart() {
    UART0.ctrl = UartCtrl.ENABLE       // ordinary field access; Mmio<T> fields are volatile
}
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

When a spec shows `Result::Ok(x)`, `x := f()`, `var n = 0`, `use a::b`, `[i32; 4]`, `fn f(self)`,
write `Result.Ok(x)`, `let x = f()`, `let mut n = 0`, `use a.b`, `[4]i32`, `fn f(self: view<Self>)`.
If a translation seems to change meaning (e.g. a spec relies on `::` to separate a value from a
module with the same name), do not guess — record it in `spec/decisions/` via the axiom-architect
agent.

Authority: `spec/decisions/` → `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md` → this skill →
`docs/base`. If this summary and the specs disagree, the specs win and the architect corrects the
summary.
