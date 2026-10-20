#!/usr/bin/env python3
"""End-to-end differential oracle for the self-hosted `axiomc` (T085).

Usage: python axiomc_e2e_oracle.py <axiom0.exe> <tmp-dir> <repo-root> [--update-registry]

Steps
  1. assemble the `axiomc` program (every compiler.* module in Axiom plus the entry point
     compiler.obj_link_driver.main) with gen_obj_link_driver_tests.axiomc_bundle_text();
  2. build it with the stage-0 compiler with the 64 MB stack of ADR-0003:
         axiom0 build --stack-reserve=67108864 -o <tmp>/axiomc.exe bundle.ax
  3. over the corpus (CORPUS_PATTERNS), compare axiomc with axiom0 on identical command lines:
         build -o x.exe            linked PE32+ image bytes + exit code + diagnostics   (-O0 and -O1)
         build --emit=obj -o x.obj COFF object bytes       + exit code + diagnostics   (-O0 and -O1)
     and, for every program both compilers linked, run both executables and compare exit code and
     stdout (the image produced by axiomc is proven runnable, not only byte-identical).
  4. A program is EQUAL when all of that agrees. Programs that are not equal must be listed in
     known_divergent.txt (one `path<TAB>first-divergent-stage` per line): each is a documented gap in
     an earlier port stage, not a hidden failure. The oracle fails when
       - an EQUAL-required program diverges (regression), or
       - a listed program became equal (XPASS: shrink the list), or
       - a listed program no longer exists.
     `--update-registry` rewrites known_divergent.txt from the current behaviour (triage: for every
     diverging program `inspect --emit=<stage>` is compared stage by stage to find the first stage
     whose output differs).

Exit status 0 only when all of the above hold. The last stdout line is the machine-readable summary
`AXIOMC-E2E programs=<n> equal=<e> known_divergent=<d> built=<b> rejected=<r> obj_equal=<o>
exe_equal=<x> run_equal=<u>`.
"""

import concurrent.futures
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_obj_link_driver_tests as gen  # noqa: E402

REGISTRY = os.path.join(HERE, "known_divergent.txt")
CORPUS_PATTERNS = [
    "tests/run/**/*.ax",
    "tests/programs/*.ax",
    "tests/mc/**/*.ax",
    "tests/modules/*/src/main.ax",
    "tests/opt/*.ax",
    "tests/driver/*.ax",
]
INSPECT_STAGES = ["tokens", "ast", "resolved", "hir", "thir", "mir", "lir", "mi", "mc", "obj"]
# Upper bounds only (a hang is still caught by the 1800 s test timeout): the oracle runs 8 programs in
# parallel, and under a loaded runner (full suite, other agents) 120 s / 20 s produced spurious timeouts.
CMD_TIMEOUT = 600
RUN_TIMEOUT = 60
AXIOMC_STACK_RESERVE = "67108864"


def collect_corpus(root):
    found = set()
    for pat in CORPUS_PATTERNS:
        for path in glob.glob(os.path.join(root, pat), recursive=True):
            found.add(os.path.relpath(path, root).replace("\\", "/"))
    return sorted(found)


def run(cmd, cwd, timeout=CMD_TIMEOUT):
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return res.returncode, res.stdout.replace(b"\r\n", b"\n"), res.stderr.replace(b"\r\n", b"\n")
    except subprocess.TimeoutExpired:
        return 124, b"", b"<timeout>"


def read_or_none(path):
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def compare_build(case_id, axiom0, axiomc, root, std, tmp, rel, emit_obj, opt):
    """Run one build on both compilers.

    Returns (message-or-empty, kind, ref_out, got_out, both_built); kind is "built" or "rejected"
    when the two outputs are identical, and both_built tells whether both compilers wrote an output.
    """
    suffix = ".obj" if emit_obj else ".exe"
    ref_out = os.path.join(tmp, "ref_%s_%s%s" % (case_id, opt, suffix))
    got_out = os.path.join(tmp, "got_%s_%s%s" % (case_id, opt, suffix))
    flags = ["--std-root", std]
    if opt == "O1":
        flags.append("-O1")
    if emit_obj:
        flags.append("--emit=obj")
    ref = run([axiom0, "build"] + flags + ["-o", ref_out, rel], root)
    got = run([axiomc, "build"] + flags + ["-o", got_out, rel], root)
    what = "%s %s" % ("obj" if emit_obj else "exe", opt)
    both_built = ref[0] == 0 and got[0] == 0
    if ref[0] != got[0]:
        return "%s: exit code axiom0=%d axiomc=%d" % (what, ref[0], got[0]), None, ref_out, got_out, False
    if ref[2].replace(tmp.encode("utf-8"), b"<tmp>") != got[2].replace(tmp.encode("utf-8"), b"<tmp>"):
        return "%s: diagnostics differ" % what, None, ref_out, got_out, both_built
    if ref[0] != 0:
        return "", "rejected", ref_out, got_out, False
    ref_bytes = read_or_none(ref_out)
    got_bytes = read_or_none(got_out)
    if ref_bytes is None or got_bytes is None:
        return "%s: output file missing" % what, None, ref_out, got_out, False
    if ref_bytes != got_bytes:
        n = min(len(ref_bytes), len(got_bytes))
        first = next((i for i in range(n) if ref_bytes[i] != got_bytes[i]), n)
        return (
            "%s: bytes differ (axiom0 %d, axiomc %d, first difference at offset %d)"
            % (what, len(ref_bytes), len(got_bytes), first),
            None, ref_out, got_out, True,
        )
    return "", "built", ref_out, got_out, True


def first_divergent_stage(rel, axiom0, axiomc, root, std):
    for stage in INSPECT_STAGES:
        args = ["inspect", "--emit=" + stage, "--std-root", std, rel]
        if run([axiom0] + args, root) != run([axiomc] + args, root):
            return stage
    return "backend-build"


def check_program(index, rel, axiom0, axiomc, root, std, tmp):
    case_id = "%03d" % index
    result = {"rel": rel, "problems": [], "built": 0, "rejected": 0, "obj_equal": 0, "exe_equal": 0, "run_equal": 0}
    exe_pair = None
    for opt in ("O0", "O1"):
        for emit_obj in (True, False):
            msg, kind, ref_out, got_out, both_built = compare_build(
                case_id, axiom0, axiomc, root, std, tmp, rel, emit_obj, opt
            )
            if not emit_obj and opt == "O0" and both_built:
                exe_pair = (ref_out, got_out)
            if msg:
                result["problems"].append(msg)
                continue
            if kind == "rejected":
                result["rejected"] += 1
                continue
            result["built"] += 1
            if emit_obj:
                result["obj_equal"] += 1
            else:
                result["exe_equal"] += 1
    # behaviour: both images exist -> run both; they must agree on exit code and stdout.
    behaviour = "no-image"
    if exe_pair is not None:
        ref_run = run([exe_pair[0]], root, RUN_TIMEOUT)
        got_run = run([exe_pair[1]], root, RUN_TIMEOUT)
        if ref_run == got_run:
            behaviour = "same-behaviour"
            result["run_equal"] += 1
        else:
            behaviour = "different-behaviour"
            result["problems"].append(
                "run: axiom0-built rc=%d / axiomc-built rc=%d" % (ref_run[0], got_run[0])
            )
    result["behaviour"] = behaviour
    for opt in ("O0", "O1"):
        for suffix in (".obj", ".exe"):
            for who in ("ref", "got"):
                p = os.path.join(tmp, "%s_%s_%s%s" % (who, case_id, opt, suffix))
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
    result["equal"] = not result["problems"]
    return result


def load_registry():
    known = {}
    if os.path.isfile(REGISTRY):
        with open(REGISTRY, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                known[parts[0]] = (parts[1], parts[2] if len(parts) > 2 else "")
    return known


def write_registry(entries):
    with open(REGISTRY, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Programs on which the Axiom `axiomc` is not yet byte-identical to `axiom0` (T085).\n")
        f.write("# Format: <path><TAB><first stage whose `inspect --emit=` output differs><TAB><behaviour>\n")
        f.write("# behaviour: same-behaviour (images differ in bytes but run identically), different-behaviour,\n")
        f.write("# or no-image (axiomc or axiom0 rejects the program or crashes).\n")
        f.write("# Regenerate with: python axiomc_e2e_oracle.py <axiom0> <tmp> <root> --update-registry\n")
        for path in sorted(entries):
            f.write("%s\t%s\t%s\n" % (path, entries[path][0], entries[path][1]))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    update = "--update-registry" in sys.argv
    if len(args) < 3:
        print(__doc__)
        return 2
    axiom0 = os.path.abspath(args[0])
    tmp = os.path.abspath(args[1])
    root = os.path.abspath(args[2])
    os.makedirs(tmp, exist_ok=True)
    std = os.path.join(root, "std")

    bundle = os.path.join(tmp, "axiomc_bundle.ax")
    with open(bundle, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    axiomc = os.path.join(tmp, "axiomc.exe")
    code, _out, err = run(
        [axiom0, "build", "--stack-reserve=" + AXIOMC_STACK_RESERVE, "-o", axiomc, bundle], root, 1500
    )
    if code != 0 or not os.path.isfile(axiomc):
        print("FAIL: axiom0 could not build axiomc (rc=%d): %s" % (code, err[:2000].decode("utf-8", "replace")))
        return 1

    for sub in (["version"], ["--features"], ["help"]):
        if run([axiomc] + sub, root) != run([axiom0] + sub, root):
            print("FAIL: `axiomc %s` output differs from axiom0" % " ".join(sub))
            return 1

    corpus = collect_corpus(root)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [
            pool.submit(check_program, i, rel, axiom0, axiomc, root, std, tmp)
            for i, rel in enumerate(corpus)
        ]
        for fut in futures:
            results.append(fut.result())

    diverging = [r for r in results if not r["equal"]]
    if update:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            stages = list(pool.map(
                lambda r: first_divergent_stage(r["rel"], axiom0, axiomc, root, std), diverging
            ))
        write_registry({r["rel"]: (s, r["behaviour"]) for r, s in zip(diverging, stages)})
        print("registry updated: %d divergent programs" % len(diverging))
        known = load_registry()
    else:
        known = load_registry()

    failures = []
    for r in results:
        listed = r["rel"] in known
        if not r["equal"] and not listed:
            failures.append("REGRESSION %s: %s" % (r["rel"], "; ".join(r["problems"])))
        elif r["equal"] and listed:
            failures.append("XPASS %s is now byte-identical: remove it from known_divergent.txt" % r["rel"])
        elif listed and known[r["rel"]][1] == "same-behaviour" and r["behaviour"] != "same-behaviour":
            failures.append("REGRESSION %s: images used to run identically, now %s" % (r["rel"], r["behaviour"]))
        elif listed and known[r["rel"]][1] != "same-behaviour" and r["behaviour"] == "same-behaviour":
            failures.append("IMPROVED %s now runs identically: update known_divergent.txt (--update-registry)" % r["rel"])
    present = set(corpus)
    for path in sorted(known):
        if path not in present:
            failures.append("STALE %s is listed in known_divergent.txt but is not in the corpus" % path)

    totals = {k: sum(r[k] for r in results) for k in ("built", "rejected", "obj_equal", "exe_equal", "run_equal")}
    same_behaviour = sum(1 for r in results if r["behaviour"] == "same-behaviour")
    images = sum(1 for r in results if r["behaviour"] != "no-image")
    summary = (
        "AXIOMC-E2E programs=%d equal=%d known_divergent=%d built=%d rejected=%d obj_equal=%d exe_equal=%d run_equal=%d images=%d same_behaviour=%d"
        % (
            len(corpus), len(results) - len(diverging), len(diverging),
            totals["built"], totals["rejected"], totals["obj_equal"], totals["exe_equal"], totals["run_equal"], images, same_behaviour,
        )
    )
    for line in failures:
        print(line)
    if failures:
        print("FAIL %d problems" % len(failures))
        print(summary)
        return 1
    print("OK")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
