import sys, subprocess, os

def main():
    axiom = sys.argv[1]
    tmp_obj = sys.argv[2]
    src = sys.argv[3]
    
    # 1. compile to obj
    res1 = subprocess.run([axiom, "build", "--emit=obj", "-o", tmp_obj, src])
    if res1.returncode != 0:
        sys.exit(res1.returncode)
        
    # 2. link with gcc
    tmp_exe = tmp_obj.replace(".obj", ".exe")
    res2 = subprocess.run(["gcc", "-nostdlib", "-Wl,--entry=ax_main", tmp_obj, "-o", tmp_exe])
    if res2.returncode != 0:
        sys.exit(res2.returncode)
        
    # 3. run
    res3 = subprocess.run([tmp_exe])
    sys.exit(res3.returncode)

if __name__ == "__main__":
    main()
