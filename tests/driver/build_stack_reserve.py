import sys, subprocess, re

axiom = sys.argv[1]
tmp_exe = sys.argv[2]
src = sys.argv[3]

subprocess.run([axiom, "build", "--stack-reserve", "67108864", "-o", tmp_exe, src], check=True)
res = subprocess.run(["objdump", "-p", tmp_exe], capture_output=True, text=True, check=True)
if "04000000" not in res.stdout:
    sys.exit(1)
