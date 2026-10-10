import os
import sys
import subprocess
import glob
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    bench_dir = root / "tests" / "perf" / "bench"
    csv_file = root / "tests" / "perf" / "baseline.csv"
    compiler = root / "build" / "axiom0.exe"

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()[:7]

    results = []
    
    for ax_file in sorted(bench_dir.glob("*.ax")):
        file_name = ax_file.name
        cmd = [str(compiler), "build", str(ax_file), "-o", "scratch.exe", "--time-passes"]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        
        for line in p.stdout.splitlines():
            if line.startswith("time: "):
                parts = line[6:].strip().split()
                if len(parts) >= 2:
                    pass_name = parts[0]
                    time_str = parts[1]
                    if time_str.endswith("s"):
                        ms = int(float(time_str[:-1]) * 1000)
                        results.append(f"{file_name},{pass_name},{ms},{commit}")

    if not csv_file.exists():
        with open(csv_file, "w") as f:
            f.write("file,pass,milliseconds,commit\n")
            
    with open(csv_file, "a") as f:
        for r in results:
            f.write(r + "\n")

if __name__ == "__main__":
    main()
