import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_link_and_run(axiom, src, tmp_obj, expected_exit):
    res1 = subprocess.run([axiom, "build", "--emit=obj", "-o", str(tmp_obj), str(src)])
    if res1.returncode != 0:
        sys.stderr.write(f"FAIL: build --emit=obj failed for {src} (rc={res1.returncode})\n")
        return 1

    tmp_exe = str(tmp_obj)[:-4] + ".exe" if str(tmp_obj).endswith(".obj") else str(tmp_obj) + ".exe"
    res2 = subprocess.run(["gcc", "-nostdlib", "-Wl,--entry=ax_main", str(tmp_obj), "-o", tmp_exe])
    if res2.returncode != 0:
        sys.stderr.write(f"FAIL: gcc cross-link failed for {src} (rc={res2.returncode})\n")
        return 1

    res3 = subprocess.run([tmp_exe])
    if res3.returncode != expected_exit:
        sys.stderr.write(
            f"FAIL: {tmp_exe} exited with {res3.returncode}, expected {expected_exit}\n"
        )
        return 1
    return 0


def main():
    if shutil.which("gcc") is None:
        sys.stderr.write("FAIL: mandatory external tool 'gcc' not on PATH (ADR-0034 section 7)\n")
        sys.exit(1)

    axiom = sys.argv[1]
    tmp_obj = Path(sys.argv[2])
    src = Path(sys.argv[3])

    # 1. Cross-link the basic empty main program (expected exit 0)
    if build_link_and_run(axiom, src, tmp_obj, 0) != 0:
        sys.exit(1)

    # 2. Cross-link the non-trivial self-contained program (.rdata table + calls + arithmetic -> exit 42)
    nontrivial_src = Path(__file__).resolve().parent / "fixtures" / "nontrivial_self_contained.ax"
    nontrivial_obj = tmp_obj.parent / "nontrivial_self_contained.obj"
    if build_link_and_run(axiom, nontrivial_src, nontrivial_obj, 42) != 0:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
