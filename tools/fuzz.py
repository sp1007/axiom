#!/usr/bin/env python3
import argparse
import random
import os
import subprocess
import time
import sys
from pathlib import Path
import re

ICE_BANNER_RE = re.compile(rb"^(?:error: )?internal compiler error", re.IGNORECASE | re.MULTILINE)

def is_crash_status(rc):
    return rc is not None and (rc < 0 or rc >= 0xC0000000)

class Fuzzer:
    def __init__(self, opts):
        self.compiler = opts.compiler
        self.iterations = opts.iterations
        self.seed = opts.seed
        self.smoke = opts.smoke
        if self.smoke:
            self.seed = 1
            self.iterations = 2000 # ~60s ? we'll see
        self.rng = random.Random(self.seed)
        self.corpus = []
        self._load_corpus(Path("tests/fuzz"))
        self._load_corpus(Path("tests/lex"))
        self._load_corpus(Path("tests/parse"))
        
        self.temp_file = Path("tests/fuzz/temp_fuzz.ax")
        if not self.temp_file.parent.exists():
            self.temp_file.parent.mkdir(parents=True)
            
        self.keywords = [b'fn', b'struct', b'enum', b'trait', b'let', b'mut', b'if', b'else', b'match', b'loop', b'while', b'for', b'return', b'break', b'continue', b'const', b'static', b'use', b'mod', b'pub', b'{', b'}', b'(', b')', b'[', b']', b';', b':', b',', b'.', b'+', b'-', b'*', b'/', b'=', b'==', b'!=', b'<', b'>', b'<=', b'>=', b'&&', b'||', b'!', b'&', b'|', b'^', b'<<', b'>>', b'as', b'dyn', b'async', b'await', b'comptime', b'view', b'mut_view', b'Self', b'true', b'false']

    def _load_corpus(self, directory):
        if not directory.exists(): return
        for p in directory.rglob("*.ax"):
            if "temp_fuzz" in str(p): continue
            try:
                self.corpus.append(p.read_bytes())
            except Exception:
                pass

    def mutate(self, data):
        choice = self.rng.random()
        if choice < 0.33:
            # Byte mutation
            mut = bytearray(data)
            if not mut: return b""
            for _ in range(self.rng.randint(1, 5)):
                op = self.rng.randint(0, 2)
                idx = self.rng.randint(0, len(mut) - 1)
                if op == 0: # flip
                    mut[idx] ^= self.rng.randint(1, 255)
                elif op == 1: # insert
                    mut.insert(idx, self.rng.randint(0, 255))
                elif op == 2 and len(mut) > 1: # delete
                    del mut[idx]
            return bytes(mut)
        elif choice < 0.66:
            # Token splicing
            tokens = re.split(rb'(\s+)', data)
            if not tokens: return data
            for _ in range(self.rng.randint(1, 3)):
                if len(tokens) > 2:
                    i = self.rng.randint(0, len(tokens)-1)
                    j = self.rng.randint(0, len(tokens)-1)
                    tokens[i], tokens[j] = tokens[j], tokens[i]
            return b"".join(tokens)
        else:
            # Grammar insertion
            mut = bytearray(data)
            if not mut: return b""
            idx = self.rng.randint(0, len(mut))
            kw = self.rng.choice(self.keywords)
            mut = mut[:idx] + b' ' + kw + b' ' + mut[idx:]
            return bytes(mut)

    def run_compiler(self, data):
        self.temp_file.write_bytes(data)
        t0 = time.time()
        try:
            p = subprocess.Popen([self.compiler, "check", "--json", str(self.temp_file)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate(timeout=2.0)
            rc = p.returncode
            elapsed = time.time() - t0
            return rc, out, err, elapsed
        except subprocess.TimeoutExpired:
            p.kill()
            out, err = p.communicate()
            return -1, out, err, 2.0

    def check_result(self, rc, out, err, elapsed, data):
        if elapsed >= 2.0:
            return "TIMEOUT"
        if ICE_BANNER_RE.search(err):
            return "ICE"
        if is_crash_status(rc):
            return f"CRASH_{rc}"
        
        # Check non-determinism
        rc2, out2, err2, elapsed2 = self.run_compiler(data)
        if elapsed2 >= 2.0:
            return "TIMEOUT"
        if rc != rc2 or out != out2 or err != err2:
            return "NONDETERMINISM"
            
        return None

    def minimize(self, data, bug_type):
        print(f"\nFound {bug_type}! Minimizing {len(data)} bytes...")
        current = data
        step = max(1, len(current) // 10)
        
        # simple minimization
        while step > 0:
            i = 0
            improved = False
            while i < len(current):
                candidate = current[:i] + current[i+step:]
                rc, out, err, elapsed = self.run_compiler(candidate)
                bt = self.check_result(rc, out, err, elapsed, candidate)
                if bt == bug_type:
                    current = candidate
                    improved = True
                else:
                    i += step
            if not improved:
                step //= 2
                
        return current

    def run(self):
        if not self.corpus:
            print("No seed corpus found!")
            sys.exit(1)
            
        findings = 0
        start_time = time.time()
        
        for i in range(self.iterations):
            seed_data = self.rng.choice(self.corpus)
            data = self.mutate(seed_data)
            
            rc, out, err, elapsed = self.run_compiler(data)
            bug = self.check_result(rc, out, err, elapsed, data)
            
            if bug:
                findings += 1
                minimized = self.minimize(data, bug)
                name = f"finding_{bug}_{i}.ax"
                Path("tests/fuzz").joinpath(name).write_bytes(minimized)
                print(f"[{i}/{self.iterations}] {bug} saved to tests/fuzz/{name}")
                break # the task says report BLOCKED if bug found. So one bug is enough to stop
                
            if i % 100 == 0:
                now = time.time()
                if self.smoke and (now - start_time) > 55:
                    print("Smoke test time limit reached.")
                    break
        
        if self.temp_file.exists():
            self.temp_file.unlink()
            
        print(f"Fuzzing completed. {findings} findings.")
        if findings > 0:
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--compiler", default="build/axiom0.exe")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--smoke", action="store_true")
    opts = parser.parse_args()
    Fuzzer(opts).run()
