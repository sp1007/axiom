import sys, os, subprocess, shutil, tempfile

def main():
    axiom0 = sys.argv[1]
    hello_pkg = sys.argv[2]
    std_dir = sys.argv[3] # path to real std

    # Test 1: Missing std diagnostic (AX_DRIVER_NO_STD)
    res1 = subprocess.run([axiom0, "check", "--std-root", "nonexistent_dir_random_9988", hello_pkg],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res1.returncode == 0 or "AX_DRIVER_NO_STD" not in res1.stderr:
        print(f"Test 1 failed: expected AX_DRIVER_NO_STD on missing std root, got rc={res1.returncode}, stderr={res1.stderr}", file=sys.stderr)
        sys.exit(1)

    # Test 2: Flag --std-root works
    res2 = subprocess.run([axiom0, "check", "--std-root", std_dir, hello_pkg],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res2.returncode != 0:
        print(f"Test 2 failed: --std-root {std_dir} failed with rc={res2.returncode}, stderr={res2.stderr}", file=sys.stderr)
        sys.exit(1)

    # Test 3: Environment variable AXIOM_STD works
    env = os.environ.copy()
    env["AXIOM_STD"] = std_dir
    res3 = subprocess.run([axiom0, "check", hello_pkg], env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res3.returncode != 0:
        print(f"Test 3 failed: AXIOM_STD env failed with rc={res3.returncode}, stderr={res3.stderr}", file=sys.stderr)
        sys.exit(1)

    # Test 4: Exe-relative discovery (<exe dir>/../std)
    exe_dir = os.path.dirname(os.path.abspath(axiom0))
    test_std_dir = os.path.join(exe_dir, "..", "std")
    # Verify that <exe dir>/../std exists in the build snapshot
    if os.path.isdir(test_std_dir):
        env_clean = os.environ.copy()
        env_clean.pop("AXIOM_STD", None)
        res4 = subprocess.run([axiom0, "check", hello_pkg], env=env_clean,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res4.returncode != 0:
            print(f"Test 4 failed: exe-relative std discovery failed with rc={res4.returncode}, stderr={res4.stderr}", file=sys.stderr)
            sys.exit(1)

    print("All std-root discovery tests passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
