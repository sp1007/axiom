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
         inspect --emit=<stage>    exit code + stdout + stderr for every stage in INSPECT_STAGES
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
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_obj_link_driver_tests as gen  # noqa: E402

REGISTRY = os.path.join(HERE, "known_divergent.txt")
CORPUS_PATTERNS = [
    "tests/run/basic/*.ax",
    "tests/run/parity/**/*.ax",
    "tests/run/control/*.ax",
    "tests/run/closures/*.ax",
    "tests/run/enums/*.ax",
    "tests/run/generics/*.ax",
    "tests/run/loops/*.ax",
    "tests/run/match/*.ax",
    "tests/run/structs/*.ax",
    "tests/run/tuples/*.ax",
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
    result = {
        "rel": rel,
        "problems": [],
        "first_divergent_stage": None,
        "built": 0,
        "rejected": 0,
        "obj_equal": 0,
        "exe_equal": 0,
        "run_equal": 0,
    }
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
    for stage in INSPECT_STAGES:
        args = ["inspect", "--emit=" + stage, "--std-root", std, rel]
        ref_ins = run([axiom0] + args, root)
        got_ins = run([axiomc] + args, root)
        if ref_ins != got_ins:
            parts = []
            if ref_ins[0] != got_ins[0]:
                parts.append("exit code axiom0=%d axiomc=%d" % (ref_ins[0], got_ins[0]))
            if ref_ins[1] != got_ins[1]:
                parts.append("stdout differs")
            if ref_ins[2] != got_ins[2]:
                parts.append("stderr differs")
            result["problems"].append("inspect %s: %s" % (stage, ", ".join(parts)))
            if result["first_divergent_stage"] is None:
                result["first_divergent_stage"] = stage
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


def resolve_prebuilt_axiomc_with_manifest(axiom0, root, bundle_bytes=None):
    """Reuse a prebuilt stage binary only when its `<bin>.inputs.json` manifest matches the current
    `compiler/` + `std/` source hashes and bundle text (T444c, T487 Scope 5); never by mtime.

    Returns `(candidate_path, inputs_hash, None)` on hit, or `(None, None, rebuild_reason)` on miss.
    """
    import json
    tools_dir = os.path.join(root, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import bootstrap as b

    cdir = os.path.dirname(os.path.abspath(axiom0))
    std = os.path.join(root, "std")
    source_files = b.collect_source_hashes(root, std)
    if bundle_bytes is None:
        if b.load_bundle_text is not getattr(b, "_REAL_LOAD_BUNDLE_TEXT", b.load_bundle_text):
            bundle_bytes = b.load_bundle_text(root).encode("utf-8")
        else:
            bundle_bytes = gen.axiomc_bundle_text().encode("utf-8")
    bundle_sha = b.sha256_bytes(bundle_bytes)

    candidates = (
        os.path.join(cdir, "axiomc1.exe"),
        os.path.join(cdir, "axiomc.exe"),
        os.path.join(cdir, "axiomc2.exe"),
        os.path.join(cdir, "dir_stage2_O1", "axiomc2.exe"),
        os.path.join(root, "build", "axiomc1.exe"),
        os.path.join(root, "build", "axiomc.exe"),
        os.path.join(root, "build", "axiomc2.exe"),
        os.path.join(root, "build", "dir_stage2_O1", "axiomc2.exe"),
    )
    first_reason = None
    seen = set()
    for cand in candidates:
        cand_abs = os.path.abspath(cand)
        if cand_abs in seen:
            continue
        seen.add(cand_abs)
        if not os.path.isfile(cand_abs):
            continue
        mp = b.manifest_path(cand_abs)
        if not os.path.isfile(mp):
            if first_reason is None:
                first_reason = "no input manifest next to the previous binary"
            continue
        try:
            with open(mp, "r", encoding="utf-8") as f:
                old = json.load(f)
        except (OSError, ValueError):
            if first_reason is None:
                first_reason = "input manifest unreadable"
            continue
        if not isinstance(old, dict) or old.get("schema") != b.MANIFEST_SCHEMA:
            if first_reason is None:
                first_reason = "input manifest schema changed"
            continue
        kind = old.get("kind") or "stage1"
        producer_sha = old.get("producer_sha256", "")
        if kind == "stage1":
            cand_s0 = os.path.join(os.path.dirname(cand_abs), "axiom0.exe")
            if os.path.isfile(cand_s0):
                producer_sha = b.sha256_file(cand_s0)
        expected = b.make_inputs(kind, source_files, producer_sha, bundle_sha, old.get("flags") or {})
        why = b.reuse_blocker(cand_abs, expected)
        if why is None:
            return cand_abs, expected["inputs_hash"], None
        if first_reason is None:
            first_reason = why
    return None, None, first_reason or "no previous binary"


def resolve_prebuilt_axiomc(axiom0, root, bundle_bytes=None):
    cand, _inputs_hash, _why = resolve_prebuilt_axiomc_with_manifest(axiom0, root, bundle_bytes=bundle_bytes)
    return cand


def main(argv=None):
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.kernel32.SetErrorMode(0x0001 | 0x0002)
        except Exception:
            pass
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args = [a for a in raw_argv if not a.startswith("--")]
    update = "--update-registry" in raw_argv
    if len(args) < 3:
        print(__doc__)
        return 2
    axiom0 = os.path.abspath(args[0])
    tmp = os.path.abspath(args[1])
    root = os.path.abspath(args[2])
    os.makedirs(tmp, exist_ok=True)
    std = os.path.join(root, "std")

    tools_dir = os.path.join(root, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import bootstrap as b

    if b.run_stage_build is not b._REAL_RUN_STAGE_BUILD:
        bundle_bytes = b.load_bundle_text(root).encode("utf-8")
    else:
        bundle_bytes = gen.axiomc_bundle_text().encode("utf-8")

    bundle = os.path.join(tmp, "axiomc_bundle.ax")
    with open(bundle, "wb") as f:
        f.write(bundle_bytes)
    axiomc = os.path.join(tmp, "axiomc.exe")
    prebuilt, inputs_hash, why = resolve_prebuilt_axiomc_with_manifest(axiom0, root, bundle_bytes=bundle_bytes)
    if prebuilt is not None:
        shutil.copy2(prebuilt, axiomc)
        print("REUSED %s (inputs %s)" % (prebuilt, inputs_hash[:16]))
        code, err = 0, b""
    else:
        source_files = b.collect_source_hashes(root, std)
        exp1 = b.make_inputs(
            "stage1",
            source_files,
            b.sha256_file(axiom0) if os.path.isfile(axiom0) else "",
            b.sha256_bytes(bundle_bytes),
            {"opt": "default", "stack_reserve": int(AXIOMC_STACK_RESERVE)},
        )
        if b.run_stage_build is not b._REAL_RUN_STAGE_BUILD:
            r1 = b.run_stage_build(
                "stage1_axiom0_to_axiomc1",
                axiom0,
                bundle,
                axiomc,
                std,
                int(AXIOMC_STACK_RESERVE),
                "default",
                False,
                root,
                b.clean_bootstrap_env(),
            )
            code = r1["rc"]
            err = r1["stderr"].encode("utf-8")
        else:
            code, _out, err = run(
                [axiom0, "build", "--stack-reserve=" + AXIOMC_STACK_RESERVE, "-o", axiomc, bundle], root, 1500
            )
        if code == 0 and os.path.isfile(axiomc):
            b.write_manifest(axiomc, exp1)
            print("REBUILT %s (%s)" % (axiomc, why))
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
        stages = [
            r["first_divergent_stage"] or first_divergent_stage(r["rel"], axiom0, axiomc, root, std)
            for r in diverging
        ]
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
