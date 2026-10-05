# SPEC-03 — Axiom v0.1 core execution semantics

## Tóm tắt
Tài liệu này chốt ngữ nghĩa thực thi lõi mà bộ thông dịch MIR (oracle) và backend native của
axiom0/axiomc **phải cho cùng một kết quả**. Các quyết định chính (ADR-0012):
- **Số nguyên:** đủ các độ rộng `i8..i64`, `u8..u64`, `isize`/`usize` (64 bit trên mọi target của
  v0.1); literal không có kiểu thì mặc định `i32`; literal vượt phạm vi là lỗi biên dịch.
- **Tràn số luôn bị kiểm tra** ở mọi bản build (debug = release), tràn → panic. Muốn modulo thì
  gọi tường minh `wrapping_add/sub/mul/neg`; có thêm `rotate_left/right`, `leading_zeros`,
  `trailing_zeros`, `count_ones`.
- **Chia cho 0, `MIN / -1`, `MIN % -1`, dịch bit ngoài phạm vi, chỉ số ngoài mảng, `u32 as char`
  không hợp lệ** → panic, không bao giờ là hành vi không xác định.
- **Panic = abort** trong bootstrap: không chạy destructor, in `panic: <thông điệp>` ra stderr,
  mã thoát **101** ở cả hai chế độ.
- **`main`**: `fn main()` (thoát 0), `fn main() -> i32` hoặc `-> u32` (mã thoát = giá trị),
  `-> never`.
- **Thứ tự đánh giá** trái sang phải; phép gán đánh giá vế phải trước rồi mới tới vị trí đích;
  `&&`/`||` ngắn mạch.
- **Bảng ép kiểu `as`** đầy đủ (số nguyên cắt bớt theo modulo; `u8 as char` luôn hợp lệ; `u32 as
  char` có kiểm tra; `char as u32`; `enum as uN` cho enum không có trường).
- Oracle có **giới hạn số bước** mặc định 50 triệu (`--step-limit`), vượt thì báo
  `AX_DRIVER_INTERP_STEP_LIMIT`, mã thoát 124.
Mỗi quy tắc có mã `AXS-SEM-NNN` để test và code tham chiếu.

Status: canonical (T003, 2026-10-04). Decisions: ADR-0012 (this spec), ADR-0004 §1 (wrapping/bit
intrinsics), ADR-0006 §2-3 (char cast, built-in helpers), ADR-0002 §5 (pointer↔integer in the
oracle). Syntax: `spec/SPEC-01-lexical.md`, `spec/SPEC-02-grammar.md`. Milestones (which task
delivers which rule): `spec/SPEC-00-bootstrap.md`. Ownership, capabilities and drop: SPEC-10..12
(T045). Consumers: T017 (typing), T019 (MIR building), T020 (verifier), T021 (oracle), T023–T025b
(native lowering), T030–T043 (language core), T061 (const evaluation), the ports in P10.

Diagnostic code names below follow `AX_<AREA>_<NAME>`; the registry `spec/diagnostics.md` (T002)
is authoritative for areas, and each implementing task registers its codes in its area file.

---

## 1. Principles

**AXS-SEM-001 — One semantics, two executors.** Every rule here is target-independent. The MIR
interpreter (T021) is the reference: native code at every optimisation level must produce the same
observable behaviour (AXS-SEM-003) for every program accepted by the type checker. Neither executor
may inherit behaviour from the host C compiler (overflow, shifts, division, signed char, ...).
While a feature's native support is still missing, axiom0 refuses to build the program
(`AX_DRIVER_NOT_YET_SUPPORTED`, AXD-014) rather than produce code that differs; no check is ever
dropped (SPEC-00 AXS-BOOT-006/007).
[0263 §25; tasks/0262 §10; tasks/0260 ABOOT-48, ABOOT-76; 0032 §50 AES-27]

**AXS-SEM-002 — No undefined behaviour in safe code.** A program that uses no `unsafe` has no
undefined behaviour: every operation either produces its defined result, panics (§7), or is rejected
at compile time. [0032 AES-19, AES-21; 0010 §15-17; tasks/0327 ANUM-26..30, ANUM-42..46]

**AXS-SEM-003 — Observable behaviour.** The observable behaviour of a run is: the bytes written to
stdout and stderr (in order per stream), the process exit code, and the effects of host-interface
intrinsics (ADR-0002). Timing, stack depth, memory addresses (except where a program casts a
pointer to an integer, ADR-0002 §5) and the order of instructions are not observable. Optimisation
(T043, later P15) may change anything that is not observable, and must not remove, add or reorder a
panic relative to observable effects. [0032 §42-44, §50; tasks/0327 ANUM-34]

## 2. Types and representation

**AXS-SEM-010 — Scalar types of v0.1.** The integer types `i8 i16 i32 i64 isize u8 u16 u32 u64
usize`, `bool`, `char`, the unit type `()` and `never`. `Str` (string view, T041) is defined with
strings; float types `f32`/`f64` are reserved and rejected by axiom0 type checking with
`AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (they arrive in E12.2); `i128`/`u128` are not part of v0.1
(E12.1). [tasks/0327 ANUM-24; tasks/0494 §5; ROADMAP R7]

**AXS-SEM-011 — Integer representation.** `iN`/`uN` are N-bit two's-complement / unsigned
integers, size N/8 bytes, alignment N/8. `isize`/`usize` have the pointer width of the target; every
v0.1 target is 64-bit, so they are 64-bit (size 8, align 8). Byte order is the target's
(little-endian on x86-64); it is observable only through `unsafe` code. The oracle uses the same
widths as the selected target. [tasks/0327 ANUM-20..22; 0032 §13]

**AXS-SEM-012 — `bool`.** Size 1, alignment 1; `false` is the byte 0, `true` the byte 1. Other byte
values are invalid and can only arise through `unsafe` code (undefined there). `bool` is not an
integer: no implicit conversion either way, `if` and `while` require `bool`. [tasks/0327 §16,
ANUM-49..51; 0041 §48]

**AXS-SEM-013 — `char`.** One Unicode scalar value: 0..=0x10FFFF excluding 0xD800..=0xDFFF. Size 4,
alignment 4, stored as the scalar value in a `u32`. Comparison orders by scalar value; there is no
arithmetic on `char` (`'a' + 1` is a type error; convert with `as`). [ADR-0006 §2; T034]

**AXS-SEM-014 — Unit.** `()` has exactly one value, size 0, alignment 1. A function without `->`
returns `()`. A block without a tail expression has value `()` (AXS-GRM-040).

**AXS-SEM-015 — `never`.** The type of expressions that do not complete: `return`, `break`,
`continue`, a `loop` without a reachable `break`, calls of functions returning `never`
(`panic`, `unreachable`, `host.exit`), and `if`/`match` all of whose branches are `never`. `never`
has no values, size 0, and coerces to every type. A function declared `-> never` whose body can
complete normally is rejected (`AX_TYPE_NEVER_RETURNS`). [0041 §19; 0068 §13-15]

## 3. Integer literals

**AXS-SEM-020 — Literal typing.** A suffixed literal (`42u8`) has the suffix type. A byte literal
`b'a'` has type `u8`. An unsuffixed integer literal gets a fresh *integer type variable* that is
fixed by the expected type of its context (annotation, parameter type, operand of a binary operator
whose other operand has a known type, return type, field type, index position, pattern scrutinee).
An integer type variable still unconstrained at the end of the function body (or const item)
defaults to `i32`. The literal is typed directly at its final type — never typed `i32` and then
converted. An integer type variable can only become an integer type; unifying it with any other type
is `AX_TYPE_MISMATCH`. [tasks/0327 §31; tasks/0494 §6]

```axiom
let a = 10              // i32
let b: u64 = 10         // u64
let c = 10              // u64: fixed by the use below
let d: u64 = c + b
let e = 300 as u8       // operand of `as` has no expected type: 300i32, then 44u8 (AXS-SEM-061)
```

**AXS-SEM-021 — Range check.** After typing, the value of every integer literal must lie in its
type's range; otherwise `AX_TYPE_LITERAL_OUT_OF_RANGE` at the literal (`let x: u8 = 300`). Unary `-`
applied directly to an integer literal (after removing parentheses) is folded first: `-128i8` and
`let m: i32 = -2147483648` are valid; `-129i8` is out of range. A negated literal of an unsigned type
is `AX_TYPE_NEG_UNSIGNED`, except `-0`. [SPEC-01 AXS-LEX-050, AXS-LEX-054; tasks/0334 §34]

**AXS-SEM-022 — No implicit conversions.** Values never change type implicitly: no widening, no
narrowing, no signed/unsigned mixing, no integer↔bool, no integer↔char. Operands of every binary
arithmetic, bitwise and comparison operator have the same type (shift amounts excepted,
AXS-SEM-034). `let y: i64 = x` with `x: i32` is `AX_TYPE_MISMATCH`. [tasks/0327 ANUM-35..37; 0032
§13, §21; 0041 §46]

## 4. Integer operations

**AXS-SEM-030 — Checked arithmetic in every build.** `+`, binary `-`, `*` and unary `-` on integers
compute the mathematical result; if it is outside the range of the operand type the operation
panics with `arithmetic overflow` (§7). There is no build mode, profile or optimisation level in
v0.1 in which these operators wrap. Compound assignments (`+=`, `-=`, `*=`) behave as the operator.
[ADR-0012 §1; 0032 §16; 0041 §42; tasks/0334 §7, ANUM-27 — chosen over the wrapping default of
tasks/0327 §4]

**AXS-SEM-031 — Wrapping and bit intrinsics.** Built-in prelude functions, polymorphic over the
ten integer types `T` (a BOOTSTRAP-SHORTCUT until std wraps them as methods in T069), defined as MIR
operations without an overflow check:

| Call | Result |
|---|---|
| `wrapping_add(a: T, b: T) -> T` | `(a + b) mod 2^N`, read back in `T` |
| `wrapping_sub(a: T, b: T) -> T` | `(a - b) mod 2^N` |
| `wrapping_mul(a: T, b: T) -> T` | `(a * b) mod 2^N` |
| `wrapping_neg(a: T) -> T` | `(0 - a) mod 2^N` (`wrapping_neg(MIN) == MIN`; for unsigned `2^N - a`, 0 for 0) |
| `rotate_left(x: T, n: u32) -> T` | bits rotated left by `n mod N` |
| `rotate_right(x: T, n: u32) -> T` | bits rotated right by `n mod N` |
| `leading_zeros(x: T) -> u32` | number of leading 0 bits of the N-bit pattern (N for 0) |
| `trailing_zeros(x: T) -> u32` | number of trailing 0 bits (N for 0) |
| `count_ones(x: T) -> u32` | number of 1 bits of the N-bit pattern |

For signed `T` the bit pattern is the two's-complement pattern. "mod 2^N, read back in T" means the
unique value of `T` congruent to the mathematical result modulo 2^N. Saturating and `checked_*`
families are library/E12.1. [ADR-0004 §1; tasks/0327 §15; 0032 §17]

**AXS-SEM-032 — Division and remainder.** `a / b` truncates toward zero; `a % b` has the sign of
`a` (or is 0), so `a == (a / b) * b + a % b`. `-7 / 3 == -2`, `-7 % 3 == -1`, `7 % -3 == 1`.
- `b == 0` → panic `division by zero` (for both `/` and `%`).
- signed `MIN / -1` and `MIN % -1` → panic `arithmetic overflow`.
[tasks/0327 §11-13, ANUM-41..44; 0032 §18-19; ADR-0012 §2]

**AXS-SEM-033 — Bitwise operators.** `&`, `|`, `^` on two operands of the same integer type act on
the bit patterns; `~x` inverts every bit of an integer. `&`, `|`, `^` on two `bool` operands are the
logical operations without short-circuit (both operands are evaluated). `!` applies to `bool` only.
[0032 §21; tasks/0327 §15, ANUM-48]

**AXS-SEM-034 — Shifts.** `x << n` and `x >> n`: `x` has any integer type `T` (the result type);
`n` has any integer type (independent of `T`; an unsuffixed literal amount defaults by the normal
rule). If `n < 0` or `n >= N` the operation panics with `shift amount out of range`. Otherwise `<<`
shifts left, discarding bits shifted out (no overflow check on the value), and `>>` is an
arithmetic shift for signed `T` and a logical shift for unsigned `T`. `<<=`, `>>=` likewise.
[tasks/0327 §14, ANUM-45..47; tasks/0334 §14, §16; 0032 §20; 0041 §45]

**AXS-SEM-035 — Comparisons.** `== != < <= > >=` on two operands of the same type, for integer
types (numeric order), `bool` (`false < true`) and `char` (scalar order). In axiom0 these are the
only built-in comparisons: aggregates, enums and `Str` compare through `Eq`/`Ord` impls (derive,
T056; std, T069/T071) or explicit `as` casts of fieldless enums. Comparisons do not chain
(AXS-GRM-051). [0032 §22; 0041 §46]

**AXS-SEM-036 — Short-circuit.** `a && b` evaluates `a`; if it is `false` the result is `false`
and `b` is not evaluated; otherwise the result is `b`. `a || b` evaluates `a`; if it is `true` the
result is `true` and `b` is not evaluated; otherwise the result is `b`. MIR builds both as control
flow (T019). [0032 §4; 0041 §32-33]

**AXS-SEM-037 — Constant expressions.** Constant evaluation (const items, array lengths, T061)
uses exactly these rules. Where a runtime operation would panic, a constant evaluation is a
compile-time error at the offending operation: `AX_CONST_OVERFLOW` (overflow, shift out of range,
invalid `char`), `AX_CONST_DIV_ZERO` (division or remainder by zero). In ordinary (non-constant)
code an operation on constant operands that must panic is *not* an error: it panics at run time,
the optimiser must keep that panic (a lint warning is allowed). [tasks/0327 §9-10, §12, ANUM-43;
tasks/0334 §35]

## 5. Evaluation order

**AXS-SEM-040 — Left to right.** Operands, call arguments, array literal elements, tuple elements
and struct literal fields (in the order written in the literal, not declaration order) are
evaluated left to right, each completely (including its own side effects, moves and panics) before
the next starts. A binary operator evaluates its left operand, then its right operand, then
performs its check (overflow, division, shift) and operation. [0032 §1-3; 0010 §18; 0041 §34]

**AXS-SEM-041 — Calls.** A call evaluates the callee (if it is an expression and not a function
name), then the arguments left to right, then transfers control. A method call `r.m(a, b)`
evaluates the receiver first, then `a`, then `b`. [0041 §35-36]

**AXS-SEM-042 — Places.** For `base[i]`: evaluate the base place, then `i`, then the bounds check
(`0 <= i < len`, otherwise panic `index out of bounds`), then the access. The index operand has type
`usize` (an unsuffixed literal is typed `usize`). Field and tuple-index projections evaluate the
base place only. [0010 §13, §18; 0032 §33; T036]

**AXS-SEM-043 — Assignment.** `place = rhs`: (1) evaluate `rhs` to a value; (2) evaluate the
operands of `place` left to right (base, index expressions) and perform its bounds checks; (3)
drop the old value of the place if it holds one that needs drop (SPEC-12, T049); (4) store the new
value. The right side is therefore always evaluated before the destination is touched; `x =
transform(x)` reads the old `x`. [0032 §7-8; 0041 §37, §39]

**AXS-SEM-044 — Compound assignment.** `place op= rhs` is one operation, not textual expansion:
(1) evaluate `rhs`; (2) evaluate the operands of `place` once, left to right, with bounds checks;
(3) read the place, compute `old op value` with the operator's checks (§4); (4) store. In
`a[next()] += f()`, `f()` runs before `next()`, and each runs exactly once. [0041 §40; ADR-0012 §4]

**AXS-SEM-045 — `let`.** `let p = e` evaluates `e` then binds; `let p = e else { … }` evaluates
`e`, then tests the pattern; the `else` block runs only on mismatch and must diverge
(AXS-GRM-042).

**AXS-SEM-046 — Conditionals and matches.** `if c { a } else { b }` evaluates `c` once and then
exactly one branch. `match s { … }` evaluates `s` once; arms are tried top to bottom; a guard is
evaluated only after its pattern matched, and the next arm is tried if it is `false`. A `while`
condition is evaluated before each iteration. [0041 §9, §14, §23]

## 6. Casts (`as`)

**AXS-SEM-060 — Cast table.** `e as T` is allowed exactly for these source → target pairs;
every other pair is `AX_TYPE_INVALID_CAST` (with a hint naming the closest valid path).
`IntTy` is any of the ten integer types.

| Source | Target | Semantics | Delivered |
|---|---|---|---|
| `IntTy` | `IntTy` | modular conversion, AXS-SEM-061; never panics | T034 |
| `bool` | `IntTy` | `false` → 0, `true` → 1 | T034 |
| `u8` | `char` | the scalar value 0..=255; always valid | T034 |
| `u32` | `char` | **checked**: panics `invalid char value` unless `n <= 0x10FFFF && !(0xD800 <= n && n <= 0xDFFF)` | T034 |
| `char` | `u32`, `i32`, `u64`, `i64`, `usize`, `isize` | the scalar value (lossless) | T034 |
| fieldless `enum` | `IntTy` | the discriminant (AXS-SEM-062) | T038 |
| `*const T` / `*mut T` | `*const U` / `*mut U` | same address, new pointee type | T061a |
| `*const T` / `*mut T` | `usize`, `isize` | the address (oracle: ADR-0002 §5) | T061a |
| `usize`, `isize` | `*const T` / `*mut T` | the address; dereferencing stays `unsafe` | T061a |
| `T` | `T` (same type) | identity | T034 |
| `f32`, `f64` on either side | — | `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` in axiom0 (E12.2) | T034 |

Not allowed: integer → `bool` (write `x != 0`), integer → `enum`, `char` → `u8`/`u16`/`i8`/`i16`
(write `c as u32` and narrow explicitly), other integers → `char` (go through `u32`), anything on
aggregates, views, `Str`, unit. Pointer casts need no `unsafe` block; dereference does (T061a). An
operand of type `never` may be cast to any type. [tasks/0327 §6-7, ANUM-35..40; tasks/0334
§17-18; ADR-0006 §2; ADR-0004 §7; ADR-0012 §5]

**AXS-SEM-061 — Integer conversions.** For integer source `S` and target `T`, `e as T` is the
unique value of `T` congruent to the value of `e` modulo 2^N(T): widening sign-extends a signed
source and zero-extends an unsigned one; narrowing keeps the low N(T) bits; same width reinterprets
the bit pattern (`-1i32 as u32 == 0xFFFF_FFFF`, `300 as u8 == 44`, `0x80u8 as i8 == -128`). `as`
is a numeric conversion, not a bitcast: there is no `as` between types of different kinds other
than the rows above. Checked narrowing (`try_from`) is library code (E12.1).
[tasks/0327 §7; tasks/0334 §17-18 — truncating chosen for `as`, ADR-0012 §5]

**AXS-SEM-062 — Enum discriminants.** In v0.1 a fieldless enum's variants have discriminants 0, 1,
2, … in declaration order (explicit discriminants are deferred, SPEC-02 §12). `e as T` is allowed
when every discriminant fits `T`; otherwise `AX_TYPE_INVALID_CAST`. The in-memory layout of enums
is decided by the layout engine (T035/T038) and is not implied by this rule. [ADR-0004 §7]

## 7. Panic

**AXS-SEM-070 — Panic kinds.** A panic is a language-level abnormal termination. Its message is
fixed by its cause:

| Cause | Message |
|---|---|
| integer overflow (AXS-SEM-030, AXS-SEM-032 `MIN / -1`) | `arithmetic overflow` |
| division or remainder by zero | `division by zero` |
| shift amount out of range | `shift amount out of range` |
| index or sub-range out of bounds | `index out of bounds` |
| `u32 as char` with a non-scalar value | `invalid char value` |
| `assert(c)` with `c == false` | `assertion failed` |
| `unreachable()` reached | `entered unreachable code` |
| `panic(msg)` | the bytes of `msg` |

[0010 §6, §12-13; 0068 §8, §36]

**AXS-SEM-071 — Panic = abort in bootstrap.** axiom0 and the v0.1 runtime implement only the abort
strategy: when a panic happens no further user code runs — no destructors, no cleanup, no unwinding.
The executor writes the line `panic: <message>\n` (UTF-8) to stderr and terminates the process with
exit code **101**. Both executors produce the same exit code and, once the native panic path can
write (T042), the same stderr line; before T042 native panics only set the exit code. The unwind
strategy, panic hooks and backtraces are E13.5 / E17.3. [0010 §7; 0068 §9, §37; ADR-0012 §3]

**AXS-SEM-072 — Built-in failure functions.** Prelude functions (built-ins until std exists):
`assert(c: bool)` (panics when `c` is `false`; there is no `debug_assert` in v0.1),
`unreachable() -> never` (always a checked panic in safe code — never an optimisation assumption),
`panic(msg: Str) -> never` (available once `Str` exists, T041). `trap()` and an unchecked
`unreachable` are not part of v0.1 (E13.1). [0010 §6, §10-12; 0068 §12-13; ADR-0012 §3]

**AXS-SEM-073 — Arithmetic failures are panics, not traps.** Division by zero, `MIN / -1`, overflow,
bad shifts, bounds and `char` failures all use the panic path of AXS-SEM-071. Native code checks the
condition explicitly before the machine operation (for example `idiv` is never executed with a zero
divisor or `MIN / -1`), so no hardware exception is ever the defined behaviour.
[0032 §18; 0010 §16; 0068 §29 (trap) — rejected for one uniform path, ADR-0012 §2]

## 8. Program entry and exit

**AXS-SEM-080 — `main`.** An executable's root module defines exactly one function `main` with no
parameters, no generic parameters, not `unsafe`, not `extern`, and one of the return types `()`
(omitted), `i32`, `u32` or `never`. A missing `main` is `AX_TYPE_MAIN_MISSING`; any other signature
is `AX_TYPE_MAIN_SIGNATURE`. Command-line arguments and the environment are read through the host
interface (ADR-0002), not parameters. The platform entry point (`axiom_start`, T027) is generated
by the linker and calls `main`; `main` is never the ABI entry point. [0263 §6, §11-12, §32;
tasks/0494 §41; SPEC-02 EX-01, EX-10; ADR-0012 §6]

**AXS-SEM-081 — Exit code.** When `main` returns, the drops of its locals have run (SPEC-12) and
the process exits with: 0 for `()`; the 32-bit pattern of the value for `i32` and `u32` (Windows
`ExitProcess(u32)`, so `-1` gives 0xFFFF_FFFF; Linux, E16.9, keeps the low 8 bits). `host.exit(code)`
(ADR-0002) exits immediately without running drops. There are no global destructors (no `static`
items in axiom0). Output written before exit is never lost: v0.1 has no user-space buffering of
stdout/stderr. [0263 §6, §32; ADR-0002 §1]

**AXS-SEM-082 — Exit codes in tests.** Portable run tests expect exit codes in 0..=255. Exit code
101 means "panicked" and is expected only by tests of panics; 124 and 125 accompanied by an
`AX_DRIVER_INTERP_*` or `AX_UNSAFE_INTERP_UB` diagnostic are oracle verdicts (AXS-SEM-090). A run test's program exit code is never
interpreted as a compiler status: the runner compiles in one step and runs in another; inside
`axiom0 run --interp`, a compiler failure is recognisable by its diagnostics on stderr (JSON with
`--json`), an internal compiler error by the ICE banner of T009/T016.

## 9. Oracle limits

**AXS-SEM-090 — Step limit.** The MIR interpreter counts one *step* per executed MIR statement and
per executed terminator. The default limit is **50 000 000** steps (about 5 s at the T021
throughput target, under the runner's 10 s timeout); `--step-limit N` overrides it, `--step-limit 0`
means unlimited. When the limit is reached the interpreter stops, reports `AX_DRIVER_INTERP_STEP_LIMIT`
("step limit of N MIR steps exceeded; rerun with --step-limit") at the span of the statement about
to execute, with the call stack as notes, and exits with code **124**; the runner reports such a
test as TIMEOUT. [T021; 0264 §18]

**AXS-SEM-091 — Call depth limit.** The interpreter allows 100 000 nested calls by default
(`--max-call-depth N`); beyond it, `AX_DRIVER_INTERP_STACK_LIMIT`, exit code 124. Native stack
exhaustion terminates the process with the OS status. Stack exhaustion is outside the differential
contract: no test may depend on it (stack reserve: ADR-0003).

**AXS-SEM-092 — Oracle-detected undefined behaviour.** In `unsafe` code (T061a) the interpreter
detects invalid pointer use, out-of-allocation accesses and use of freed memory and reports
`AX_UNSAFE_INTERP_UB` with exit code **125**. Native behaviour of such a program is undefined; tests of it
run in interp mode only.

## 10. Test cases (normative examples)

Each line: program fragment → expected result in both executors (`exit` = process exit code).

| Id | Program (body of `fn main() -> i32`) | Result | Rules |
|---|---|---|---|
| SEM-T01 | `return 42` | exit 42 | 080, 081 |
| SEM-T02 | `let x: i32 = 2147483647` ↵ `return x + 1` | panic, exit 101 | 030, 071 |
| SEM-T03 | `let x: u8 = 255` ↵ `return wrapping_add(x, 1u8) as i32` | exit 0 | 031, 061 |
| SEM-T04 | `return -7 / 3 + 2` | exit 0 | 032 |
| SEM-T05 | `return -7 % 3 + 1` | exit 0 | 032 |
| SEM-T06 | `let z = 0` ↵ `return 1 / z` | panic, exit 101 | 032, 073 |
| SEM-T07 | `let m: i32 = -2147483648` ↵ `return m / -1` | panic, exit 101 | 021, 032 |
| SEM-T08 | `let n = 32` ↵ `return 1 << n` | panic, exit 101 | 034 |
| SEM-T09 | `return (-16 >> 2) + 4` | exit 0 | 034 |
| SEM-T10 | `return (0x80u8 as i8) as i32 + 128` | exit 0 | 061 |
| SEM-T11 | `return ('ế' as u32 - 0x1EBF) as i32` | exit 0 | 060 |
| SEM-T12 | `let n = 0xD800u32` ↵ `let c = n as char` ↵ `return 0` | panic, exit 101 | 060, 070 |
| SEM-T13 | `return count_ones(0xF0u8) as i32 + leading_zeros(1u32) as i32` | exit 35 | 031 |
| SEM-T14 | `let t = true` ↵ `if false && t { return 1 }` ↵ `return t as i32` | exit 1 | 036, 060 |
| SEM-T15 | `let x: u8 = 300` | compile error `AX_TYPE_LITERAL_OUT_OF_RANGE` | 021 |
| SEM-T16 | `let a: i32 = 1` ↵ `let b: i64 = a` | compile error `AX_TYPE_MISMATCH` | 022 |
| SEM-T17 | `let c = 'a'` ↵ `return (c as u8) as i32` | compile error `AX_TYPE_INVALID_CAST` | 060 |
| SEM-T18 | `return rotate_left(0x81u8, 9) as i32` | exit 3 | 031 |

Evaluation-order test (SEM-T19). It needs `let mut`, compound assignment, arrays and block
expressions (T030–T036), so it belongs to the P5 milestone (T044 conformance). Expected exit 34 in
both modes: the digits are appended in the order 1, 2, 3, 4 (RHS before place, AXS-SEM-043/044);
any other order gives a different number.

```axiom
fn step(acc: i32, d: i32) -> i32 { acc * 10 + d }

fn main() -> i32 {
    let mut a: [2]i32 = [0, 0]
    let mut n = 0
    a[{ n = step(n, 2); 0 }] = { n = step(n, 1); 7 }
    a[{ n = step(n, 4); 1 }] += { n = step(n, 3); 1 }
    n - 1200
}
```
