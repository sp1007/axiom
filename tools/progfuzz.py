#!/usr/bin/env python3
"""progfuzz: typed-program generator and differential fuzzer for Axiom P7.

Validates that random valid typed programs exercising P7 abstractions (generics,
traits with static dispatch, closures, comptime consts, raw pointers, modules)
execute identically across:
  - MIR interpreter (`axiom0 run --interp`)
  - Native code at -O0 (`axiom0 build -O0 -o <exe>` && `<exe>`)
  - Native code at -O1 (`axiom0 build -O1 -o <exe>` && `<exe>`)
"""

import argparse
import concurrent.futures
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time


def render(data, limit=200):
    if isinstance(data, bytes):
        text = repr(data)
    else:
        text = repr(str(data))
    if len(text) > limit:
        return text[:limit] + "..."
    return text


class ProgramGenerator:
    def __init__(self, rng):
        self.rng = rng

    def gen_pattern_1(self, i):
        # Generic struct + method
        c1 = self.rng.randint(1, 20)
        c2 = self.rng.randint(1, 20)
        decl = f"""struct Box_{i}<T> {{
    val: T,
}}
impl Box_{i}<i32> {{
    fn get_val_{i}(self: view<Box_{i}<i32>>) -> i32 {{
        return self.val;
    }}
}}
fn test_{i}() -> i32 {{
    let b = Box_{i}<i32> {{ val: {c1} }};
    return b.get_val_{i}() + {c2};
}}
"""
        return decl

    def gen_pattern_2(self, i):
        # Trait with static dispatch
        k = self.rng.randint(2, 5)
        bias = self.rng.randint(1, 20)
        val = self.rng.randint(1, 15)
        decl = f"""trait Evaluator_{i} {{
    fn eval_{i}(self: view<Self>, input: i32) -> i32;
}}
struct SimpleEval_{i} {{
    bias: i32,
}}
impl Evaluator_{i} for SimpleEval_{i} {{
    fn eval_{i}(self: view<SimpleEval_{i}>, input: i32) -> i32 {{
        return input * {k} + self.bias;
    }}
}}
fn test_{i}() -> i32 {{
    let e = SimpleEval_{i} {{ bias: {bias} }};
    return e.eval_{i}({val});
}}
"""
        return decl

    def gen_pattern_3(self, i):
        # Trait with default method
        factor = self.rng.randint(2, 6)
        inp = self.rng.randint(1, 10)
        decl = f"""trait BaseMetric_{i} {{
    fn factor_{i}(self: view<Self>) -> i32 {{
        return {factor};
    }}
    fn compute_{i}(self: view<Self>, x: i32) -> i32 {{
        return x * self.factor_{i}();
    }}
}}
struct MetricA_{i} {{
    dummy: i32,
}}
impl BaseMetric_{i} for MetricA_{i} {{}}
fn test_{i}() -> i32 {{
    let m = MetricA_{i} {{ dummy: 0 }};
    return m.compute_{i}({inp});
}}
"""
        return decl

    def gen_pattern_4(self, i):
        # Closure capturing by value
        c1 = self.rng.randint(1, 15)
        c2 = self.rng.randint(1, 15)
        c3 = self.rng.randint(1, 5)
        decl = f"""fn test_{i}() -> i32 {{
    let a = {c1};
    let b = {c2};
    let c = {c3};
    let f1 = |x: i32| -> i32 {{ x + a }};
    let f2 = || -> i32 {{ f1(b) * c }};
    return f2();
}}
"""
        return decl

    def gen_pattern_5(self, i):
        # Closure capturing mutable variable
        init = self.rng.randint(1, 20)
        s1 = self.rng.randint(1, 10)
        s2 = self.rng.randint(1, 10)
        s3 = self.rng.randint(1, 10)
        decl = f"""fn test_{i}() -> i32 {{
    let mut total: i32 = {init};
    let mut step = |s: i32| {{
        total = total + s;
    }};
    step({s1});
    step({s2});
    step({s3});
    return total;
}}
"""
        return decl

    def gen_pattern_6(self, i):
        # Function pointers
        m = self.rng.randint(2, 4)
        a = self.rng.randint(1, 10)
        b = self.rng.randint(1, 15)
        v1 = self.rng.randint(1, 10)
        v2 = self.rng.randint(1, 10)
        decl = f"""fn helper_{i}_1(x: i32) -> i32 {{
    return x * {m} + {a};
}}
fn helper_{i}_2(x: i32) -> i32 {{
    return x + {b};
}}
fn run_fp_{i}(f: fn(i32) -> i32, arg: i32) -> i32 {{
    return f(arg);
}}
fn test_{i}() -> i32 {{
    let fp1: fn(i32) -> i32 = helper_{i}_1;
    let fp2: fn(i32) -> i32 = helper_{i}_2;
    let r1 = run_fp_{i}(fp1, {v1});
    let r2 = run_fp_{i}(fp2, {v2});
    return r1 + r2;
}}
"""
        return decl

    def gen_pattern_7(self, i):
        # Comptime constants and table lookup
        base = self.rng.randint(1, 20)
        offset = self.rng.randint(1, 20)
        t0 = self.rng.randint(1, 30)
        t1 = self.rng.randint(1, 30)
        t2 = self.rng.randint(1, 30)
        t3 = self.rng.randint(1, 30)
        idx = self.rng.randint(0, 3)
        decl = f"""const C_{i}_BASE: i32 = {base};
const C_{i}_OFFSET: i32 = {offset};
const TBL_{i}: [4]i32 = [{t0}, {t1}, {t2}, {t3}];
fn test_{i}() -> i32 {{
    let idx: usize = {idx};
    let val = TBL_{i}[idx];
    return val + C_{i}_BASE + C_{i}_OFFSET;
}}
"""
        return decl

    def gen_pattern_8(self, i):
        # Raw pointers and unsafe array element mutation
        a = self.rng.randint(1, 20)
        b = self.rng.randint(1, 20)
        c = self.rng.randint(1, 20)
        d = self.rng.randint(1, 10)
        decl = f"""fn test_{i}() -> i32 {{
    let mut arr: [3]i32 = [{a}, {b}, {c}];
    unsafe {{
        let p: *mut i32 = address_of_mut(arr[0]);
        *p = *p + {d};
    }}
    return arr[0] + arr[1] + arr[2];
}}
"""
        return decl

    def gen_pattern_9(self, i):
        # Enum matching
        val = self.rng.randint(1, 25)
        decl = f"""enum Status_{i} {{
    Idle,
    Active(i32),
}}
fn test_{i}() -> i32 {{
    let s = Status_{i}.Active({val});
    let mut out: i32 = 0;
    if let Status_{i}.Active(v) = s {{
        out = v * 2;
    }} else {{
        out = 99;
    }}
    return out;
}}
"""
        return decl

    def gen_pattern_10(self, i):
        # While loop and branches
        limit = self.rng.randint(3, 8)
        mult = self.rng.randint(2, 4)
        decl = f"""fn test_{i}() -> i32 {{
    let mut sum: i32 = 0;
    let mut j: i32 = 0;
    while j < {limit} {{
        if j % 2 == 0 {{
            sum = sum + j * {mult};
        }} else {{
            sum = sum + j;
        }}
        j = j + 1;
    }}
    return sum;
}}
"""
        return decl

    def gen_pattern_11(self, i):
        # Generic Option and Result
        v1 = self.rng.randint(1, 20)
        v2 = self.rng.randint(1, 10)
        decl = f"""fn test_{i}() -> i32 {{
    let opt: Option<i32> = Option.Some({v1});
    let res: Result<i32, i32> = Result.Ok({v2});
    let mut acc: i32 = 0;
    if let Option.Some(x) = opt {{
        acc = acc + x;
    }}
    if let Result.Ok(y) = res {{
        acc = acc + y * 3;
    }}
    return acc;
}}
"""
        return decl

    def gen_pattern_12(self, i):
        # Higher-order closure calling trait method
        factor = self.rng.randint(2, 5)
        val = self.rng.randint(1, 15)
        decl = f"""trait Worker_{i} {{
    fn work_{i}(self: view<Self>, a: i32) -> i32;
}}
struct SimpleWorker_{i} {{
    mult: i32,
}}
impl Worker_{i} for SimpleWorker_{i} {{
    fn work_{i}(self: view<SimpleWorker_{i}>, a: i32) -> i32 {{
        return a * self.mult;
    }}
}}
fn test_{i}() -> i32 {{
    let w = SimpleWorker_{i} {{ mult: {factor} }};
    let cl = |x: i32| -> i32 {{ w.work_{i}(x) + 7 }};
    return cl({val});
}}
"""
        return decl

    def generate_batch(self, batch_id, count):
        generators = [
            self.gen_pattern_1,
            self.gen_pattern_2,
            self.gen_pattern_3,
            self.gen_pattern_4,
            self.gen_pattern_5,
            self.gen_pattern_6,
            self.gen_pattern_7,
            self.gen_pattern_8,
            self.gen_pattern_9,
            self.gen_pattern_10,
            self.gen_pattern_11,
            self.gen_pattern_12,
        ]

        parts = [
            "// test: diff",
            f"// progfuzz batch {batch_id}",
            "@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }",
            "",
        ]

        for i in range(count):
            gen = self.rng.choice(generators)
            parts.append(gen(i))

        # Generate main function aggregating test results
        main_fn = [
            "fn main() -> i32 {",
            "    let mut acc: i32 = 42;",
        ]
        for i in range(count):
            main_fn.append(f"    acc = (acc * 31 + test_{i}()) & 0x7fffffff;")
        main_fn.extend([
            "    print_int(acc);",
            "    print(\"\\n\");",
            "    return acc % 100;",
            "}",
        ])
        parts.append("\n".join(main_fn))

        return "\n".join(parts)


def run_one_variant(cmd, timeout=10.0, cwd=None):
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
        )
        return proc.returncode, proc.stdout, proc.stderr, None
    except subprocess.TimeoutExpired:
        return -1, b"", b"TIMEOUT", "timeout"
    except Exception as e:
        return -1, b"", str(e).encode(), str(e)


def test_program(compiler_path, src_path, std_root, tmp_dir):
    compiler = os.path.abspath(compiler_path)
    std_args = ["--std-root", os.path.abspath(std_root)] if std_root and os.path.isdir(std_root) else []

    # 1. Interpreter run
    interp_cmd = [compiler, "run", "--interp"] + std_args + [src_path]
    i_rc, i_out, i_err, i_err_desc = run_one_variant(interp_cmd)
    if i_err_desc:
        return f"interp failed: {i_err_desc}", None
    if i_rc < 0 or i_rc >= 120:
        return f"interp abnormal exit {i_rc}: {render(i_err)}", None

    # 2. Native -O0 build and run
    exe_o0 = os.path.join(tmp_dir, "prog_o0.exe")
    b0_cmd = [compiler, "build", "-O0", "-o", exe_o0] + std_args + [src_path]
    b0_rc, b0_out, b0_err, b0_desc = run_one_variant(b0_cmd)
    if b0_rc != 0:
        return f"native -O0 build failed ({b0_rc}): {render(b0_err)}", None
    if not os.path.exists(exe_o0):
        return "native -O0 build exited 0 but wrote no executable", None

    r0_rc, r0_out, r0_err, r0_desc = run_one_variant([exe_o0])
    if r0_desc:
        return f"native -O0 execution error: {r0_desc}", None

    # 3. Native -O1 build and run
    exe_o1 = os.path.join(tmp_dir, "prog_o1.exe")
    b1_cmd = [compiler, "build", "-O1", "-o", exe_o1] + std_args + [src_path]
    b1_rc, b1_out, b1_err, b1_desc = run_one_variant(b1_cmd)
    if b1_rc != 0:
        return f"native -O1 build failed ({b1_rc}): {render(b1_err)}", None
    if not os.path.exists(exe_o1):
        return "native -O1 build exited 0 but wrote no executable", None

    r1_rc, r1_out, r1_err, r1_desc = run_one_variant([exe_o1])
    if r1_desc:
        return f"native -O1 execution error: {r1_desc}", None

    # Compare exit codes and stdout
    if i_rc != r0_rc:
        return f"exit mismatch: interp={i_rc} != native-O0={r0_rc}", None
    if r0_rc != r1_rc:
        return f"exit mismatch: native-O0={r0_rc} != native-O1={r1_rc}", None

    if i_out != r0_out:
        return f"stdout mismatch: interp={render(i_out)} != native-O0={render(r0_out)}", None
    if r0_out != r1_out:
        return f"stdout mismatch: native-O0={render(r0_out)} != native-O1={render(r1_out)}", None

    return None, (i_rc, i_out)


def run_batch_job(batch_args):
    batch_id, count, seed, compiler_path, std_root, keep_temp = batch_args
    rng = random.Random(seed)
    gen = ProgramGenerator(rng)
    code = gen.generate_batch(batch_id, count)

    tmp_dir = tempfile.mkdtemp(prefix=f"progfuzz_{batch_id}_")
    try:
        src_path = os.path.join(tmp_dir, "fuzz.ax")
        with open(src_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(code)

        err, res = test_program(compiler_path, src_path, std_root, tmp_dir)
        if err:
            return batch_id, count, err, code
        return batch_id, count, None, None
    finally:
        if not keep_temp:
            shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Axiom P7 typed program differential fuzzer")
    parser.add_argument("--seed", type=int, default=1, help="PRNG seed")
    parser.add_argument("--iterations", type=int, default=20000, help="Total iterations to test")
    parser.add_argument("--batch-size", type=int, default=25, help="Test cases per generated program")
    parser.add_argument("--compiler", default="build/axiom0.exe", help="Path to axiom0 compiler")
    parser.add_argument("--std-root", default="std", help="Path to std library root")
    parser.add_argument("-j", "--jobs", type=int, default=min(8, os.cpu_count() or 4), help="Parallel worker threads")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files on error")
    opts = parser.parse_args()

    total_iterations = opts.iterations
    batch_size = max(1, opts.batch_size)
    num_batches = (total_iterations + batch_size - 1) // batch_size

    print(f"progfuzz: starting campaign with seed={opts.seed}, iterations={total_iterations}, "
          f"batches={num_batches} (batch_size={batch_size}), workers={opts.jobs}")

    master_rng = random.Random(opts.seed)
    batch_jobs = []
    remaining = total_iterations
    for b_idx in range(num_batches):
        count = min(batch_size, remaining)
        b_seed = master_rng.randint(0, 0x7fffffff)
        batch_jobs.append((b_idx, count, b_seed, opts.compiler, opts.std_root, opts.keep_temp))
        remaining -= count

    t0 = time.time()
    completed_iterations = 0
    findings = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=opts.jobs) as executor:
        futures = {executor.submit(run_batch_job, job): job[0] for job in batch_jobs}
        for future in concurrent.futures.as_completed(futures):
            b_idx = futures[future]
            try:
                batch_id, count, err, code = future.result()
                if err:
                    findings += 1
                    print(f"\n[FINDING #{findings}] in batch {batch_id}: {err}")
                    repro_path = f"progfuzz_repro_batch_{batch_id}.ax"
                    with open(repro_path, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(code)
                    print(f"  Repro saved to {repro_path}")
                else:
                    completed_iterations += count
                    if opts.verbose or completed_iterations % 2000 < batch_size or completed_iterations >= total_iterations:
                        elapsed = time.time() - t0
                        rate = completed_iterations / max(0.001, elapsed)
                        print(f"  [{completed_iterations}/{total_iterations}] iterations tested ({rate:.1f} iter/s, {findings} findings)")
            except Exception as e:
                findings += 1
                print(f"\n[EXCEPTION] in batch {b_idx}: {e}")

    elapsed = time.time() - t0
    print(f"\nCAMPAIGN COMPLETE: {completed_iterations}/{total_iterations} iterations tested in {elapsed:.1f}s.")
    print(f"Total findings: {findings}")

    if findings > 0:
        print(f"FAIL: {findings} discrepancies or crashes found.")
        sys.exit(1)
    else:
        print("PASS: 0 findings across interp, native-O0, native-O1.")
        sys.exit(0)


if __name__ == "__main__":
    main()
