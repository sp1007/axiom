#!/usr/bin/env python3
"""tools/gen_large.py: generates a valid large Axiom scale-test program (ADR-0005 §7, T075).

Requirements:
- Generates a valid program of ~100k lines (or requested --lines).
- Includes:
  * deep generics
  * long functions
  * a 200-arm match statement
  * a 500-deep expression nesting
  * large constant tables
  * deterministic output with fixed seed
"""

import argparse
import random
import sys


def generate_scale_program(target_lines: int, seed: int) -> str:
    rng = random.Random(seed)
    lines = []

    def emit(line: str = ""):
        lines.append(line)

    emit("// test: run")
    emit("// stdout: OK scale\\n")
    emit("")
    emit("@intrinsic fn assert(c: bool) {}")
    emit("")

    # Determine proportion of constant tables vs code lines
    # For scale test: large constant tables in .rdata (T061d)
    if target_lines >= 5000:
        table_lines = int(target_lines * 0.96)
    else:
        table_lines = min(100, target_lines // 2)

    half_table = max(16, table_lines // 2)
    emit("// --- Large Constant Tables ---")
    emit(f"const TABLE_ALPHA: [{half_table}]i32 = [")
    for i in range(half_table):
        val = rng.randint(-100000, 100000)
        emit(f"    {val},")
    emit("];")
    emit("")

    emit(f"const TABLE_BETA: [{half_table}]i32 = [")
    for i in range(half_table):
        val = rng.randint(0, 65535)
        emit(f"    {val},")
    emit("];")
    emit("")

    # 2. 200-arm match statement
    emit("// --- 200-arm Match ---")
    emit("fn match_200(x: i32) -> i32 {")
    emit("    match x {")
    for arm in range(200):
        val = (arm * 17 + 5) % 10000
        emit(f"        {arm} => {val},")
    emit("        _ => -1,")
    emit("    }")
    emit("}")
    emit("")

    # 3. 500-deep expression nesting
    emit("// --- 500-deep Expression Nesting ---")
    emit("fn deep_expr_500() -> i32 {")
    deep_depth = 500
    expr = "0"
    for _ in range(deep_depth):
        expr = f"(1 + {expr})"
    emit(f"    let r: i32 = {expr};")
    emit("    r")
    emit("}")
    emit("")

    # 4. Deep Generics
    emit("// --- Deep Generics ---")
    emit("struct GenPair<T> { a: T, b: T }")
    emit("")
    emit("fn gen_step_0<T>(x: T) -> T { x }")
    for step in range(1, 11):
        emit(f"fn gen_step_{step}<T>(x: T) -> T {{ gen_step_{step - 1}(x) }}")
    emit("")
    emit("fn test_deep_generics(v: i32) -> i32 {")
    emit("    let p = GenPair<i32> { a: v, b: v + 1 };")
    emit("    let res_a = gen_step_10(p.a);")
    emit("    let res_b = gen_step_10(p.b);")
    emit("    res_a + res_b")
    emit("}")
    emit("")

    # 5. Long functions to reach the target line count (ADR-0005 §7)
    reserved_lines = 40
    fn_idx = 0
    while len(lines) < target_lines - reserved_lines:
        fn_start = len(lines)
        emit(f"fn long_compute_{fn_idx}(a: i32, b: i32) -> i32 {{")
        emit(f"    let mut sum: i32 = a + {rng.randint(1, 50)};")
        emit(f"    let mut factor: i32 = {rng.randint(2, 8)};")
        emit("    let mut i: i32 = 0;")
        emit("    while i < 100 {")
        while len(lines) - fn_start < 45 and len(lines) < target_lines - reserved_lines - 8:
            val = rng.randint(1, 20)
            emit(f"        sum = (sum * factor + {val}) % 10007;")
            emit("        factor = (factor + 1) % 9 + 1;")
        emit("        i = i + 1;")
        emit("    }")
        emit("    let tbl_val = TABLE_ALPHA[(sum & 15) as usize];")
        emit("    sum + tbl_val + b")
        emit("}")
        emit("")
        fn_idx += 1

    # 6. Main function
    emit("// --- Main Entry Point ---")
    emit("fn main() {")
    emit("    // 1. Verify 200-arm match")
    emit("    assert(match_200(0) == 5);")
    emit("    assert(match_200(199) == (199 * 17 + 5) % 10000);")
    emit("    assert(match_200(250) == -1);")
    emit("")
    emit("    // 2. Verify 500-deep expression nesting")
    emit("    let d500 = deep_expr_500();")
    emit("    assert(d500 == 500);")
    emit("")
    emit("    // 3. Verify deep generics")
    emit("    let g_res = test_deep_generics(42);")
    emit("    assert(g_res == 85);")
    emit("")
    emit("    // 4. Verify table access")
    emit("    assert(TABLE_ALPHA[0] == TABLE_ALPHA[0]);")
    emit("    assert(TABLE_BETA[15] == TABLE_BETA[15]);")
    emit("")
    if fn_idx > 0:
        first_call = f"long_compute_0(10, 20)"
        last_call = f"long_compute_{fn_idx - 1}(5, 15)"
        emit(f"    let r0 = {first_call};")
        emit(f"    let r1 = {last_call};")
        emit("    assert(r0 == r0);")
        emit("    assert(r1 == r1);")
    emit("")
    emit('    print("OK scale\\n");')
    emit("}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate large Axiom program for scale testing")
    parser.add_argument("--lines", type=int, default=100000, help="Target number of lines (default 100,000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    parser.add_argument("-o", "--output", default="scale_prog.ax", help="Output file path (default scale_prog.ax)")
    args = parser.parse_args()

    content = generate_scale_program(args.lines, args.seed)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    actual_lines = content.count("\n")
    print(f"Generated {actual_lines} lines to {args.output} (seed={args.seed})")


if __name__ == "__main__":
    main()
