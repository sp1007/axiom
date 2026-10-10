import sys, os, subprocess, shutil, tempfile

def main():
    axiom0 = sys.argv[1]
    src_pkg = sys.argv[2]
    std_dir = sys.argv[3]

    with tempfile.TemporaryDirectory() as temp_root:
        dir_a = os.path.join(temp_root, "dir_a")
        dir_b = os.path.join(temp_root, "dir_b")
        pkg_a = os.path.join(dir_a, "pkg")
        pkg_b = os.path.join(dir_b, "pkg")

        shutil.copytree(src_pkg, pkg_a)
        shutil.copytree(src_pkg, pkg_b)

        out_obj_a = os.path.join(dir_a, "out.obj")
        out_obj_b = os.path.join(dir_b, "out.obj")

        # 1. Compile to obj from both directories
        res_a = subprocess.run([axiom0, "build", "--emit=obj", "--std-root", std_dir, "-o", out_obj_a, pkg_a],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_a.returncode != 0:
            print(f"Build in dir_a failed: {res_a.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
            sys.exit(1)

        res_b = subprocess.run([axiom0, "build", "--emit=obj", "--std-root", std_dir, "-o", out_obj_b, pkg_b],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_b.returncode != 0:
            print(f"Build in dir_b failed: {res_b.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
            sys.exit(1)

        # 2. Check byte-identical object files
        with open(out_obj_a, "rb") as fa, open(out_obj_b, "rb") as fb:
            bytes_a = fa.read()
            bytes_b = fb.read()

        if bytes_a != bytes_b:
            print(f"Reproducibility failure: out.obj differ ({len(bytes_a)} vs {len(bytes_b)} bytes)", file=sys.stderr)
            sys.exit(1)

        # 3. Check JSON diagnostics identical and no absolute paths
        json_a = subprocess.run([axiom0, "check", "--json", "--std-root", std_dir, pkg_a],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        json_b = subprocess.run([axiom0, "check", "--json", "--std-root", std_dir, pkg_b],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if json_a.stderr != json_b.stderr:
            print(f"JSON diagnostics differ between directories:\nDir A:\n{json_a.stderr}\nDir B:\n{json_b.stderr}", file=sys.stderr)
            sys.exit(1)

        if dir_a in json_a.stderr or dir_b in json_a.stderr:
            print(f"Absolute path leaked in JSON diagnostics: {json_a.stderr}", file=sys.stderr)
            sys.exit(1)

    print("Reproducibility verification passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
