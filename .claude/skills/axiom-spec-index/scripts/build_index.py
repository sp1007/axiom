#!/usr/bin/env python3
"""Build a topic index over docs/base/specs and docs/base/tasks.

Usage: python .claude/skills/axiom-spec-index/scripts/build_index.py [repo_root]
Writes .claude/skills/axiom-spec-index/references/index.md

The corpus is ~1000 markdown files (~37 MB). Agents cannot read it all; this index maps
compiler topics to the files most likely to contain the normative text, and flags the
application-domain documents (AI serving, finance, GUI...) that are out of scope for the compiler.
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
DIRS = ["docs/base/specs", "docs/base/tasks"]
OUT = os.path.join(ROOT, ".claude/skills/axiom-spec-index/references/index.md")

# (topic, regex over filename). Order matters only for display.
TOPICS = [
    ("00 Blueprint / implementation order / bootstrap ladder",
     r"BLUEPRINT|IMPLEMENTATION LADDER|STAGE-0|Stage-0|BOOTSTRAP v0|BOOTSTRAP SUBSET|MINIMAL SELF-HOSTING|Nguyên tắc triển khai|Mục tiêu bootstrap|BOOTSTRAP IMPLEMENTATION ARCHITECTURE|vertical slice|Genesis|HARNESS"),
    ("01 Compiler kernel / IDs / source DB / query engine",
     r"KERNEL|Kernel|QUERY ENGINE|INTERNAL API|COMMON INFRASTRUCTURE|Frontend Architecture|Incremental Compiler Database"),
    ("02 Lexical / tokens",
     r"LEXICAL|Lexical|LEX-|Lexer|LEXER|Token"),
    ("03 Grammar / surface syntax / parser / AST",
     r"SYNTAX|Syntax|Grammar|GRAMMAR|PARSE|Parser|PARSER|AST|Surface|Language Surface|Idiomatic"),
    ("04 Name resolution / modules / packages / visibility",
     r"NAME RESOLUTION|Name Resolution|Module|MODULE|Namespace|Visibility|Import|Package"),
    ("05 HIR / typed HIR / expressions / control flow / patterns",
     r"HIR|Expression|EXPRESSION|Control Flow|CONTROL FLOW|CONTROL-FLOW|Pattern|PATTERN|if` là expression|cleanup"),
    ("06 Type system / inference / generics / traits",
     r"TYPE|Type System|Type Checking|Trait|TRAIT|Generic|GENERIC|Monomorphization|MONOMORPH|Conversions|Callable|Closure|CLOSURE|method"),
    ("07 Ownership / capability / view / drop / memory model",
     r"OWNERSHIP|Ownership|OWN-|CAPABILITY|Capability|CAP-|VIEW|View|DROP|Drop|MEMORY|Memory|Place|PLACE|Borrow|Lifetime|Resource"),
    ("08 MIR / verifier / oracle / interpreter",
     r"MIR|VERIFIER|Verifier|Verification|ORACLE|Oracle|INTERPRETER|Interpreter|SEMANTIC CORE|Semantic Core|Dataflow"),
    ("09 Error / panic / Result / Option",
     r"ERROR|Error|Panic|PANIC|Result|Failure|FAILURE"),
    ("10 Optimizer / OptIR / SSA / LTO / PGO",
     r"OPTIM|Optimi|SSA|Inlining|INLINING|LTO|PGO|Vectoriz|Loop Optimization|Escape Analysis"),
    ("11 LIR / ABI / layout / calling convention",
     r"LIR|ABI|Layout|LAYOUT|Representation|REPRESENTATION|Calling Convention|Struct v0"),
    ("12 x86-64 / machine IR / isel / regalloc / encoder",
     r"X86|x86|Machine IR|MACHINE IR|MACHINE-IR|ISel|INSTRUCTION|REGALLOC|Register Allocation|REGISTER|ENC-|Encoding|ENCODING|Target|TARGET"),
    ("13 Object files / linker / PE-COFF / ELF / startup",
     r"COFF|PE-|PE64|ELF|Object Writer|OBJECT|Linker|LINKER|OBJECTLINK|Startup|STARTUP|Binary|BINARY|UNWIND|CODEVIEW|PDB|MACHO|Image"),
    ("14 Runtime / core / std library / collections / text",
     r"RUNTIME|Runtime|STDLIB|Standard Library|STANDARD LIBRARY|Core Library|Collection|COLLECTION|String|STRING|Text|Iterator|Prelude|Intrinsic|Numeric|NUMERIC"),
    ("15 Concurrency / async / atomics / threads",
     r"CONCURRENCY|Concurrency|ASYNC|Async|ATOMIC|Atomic|THREAD|Thread|FIBER|SCHEDULER|CHANNEL|SYNCHRONIZATION|ARC-"),
    ("16 FFI / interop",
     r"FFI|Interop|INTEROP|extern"),
    ("17 Comptime / reflection / metaprogramming",
     r"COMPTIME|Comptime|comptime|Reflection|REFLECTION|Metaprogramming|CONSTANT EVALUATION"),
    ("18 Testing / conformance / diagnostics / tooling",
     r"CONFORMANCE|Conformance|TEST|Test|Diagnostic|DIAGNOSTIC|Tooling|TOOLING|Debug|DEBUG|Sanitizer|LSP|IDE"),
    ("19 Build system / driver / self-hosting",
     r"Build|BUILD|Driver|DRIVER|TOOLCHAIN|Toolchain|Self-Hosting|SELF-HOSTING|self-hosting|axiomc|Bootstrap Compiler"),
    ("20 Consistency audits / freezes / contradictions",
     r"AUDIT|Audit|FREEZE|Freeze|Consistency|CONSISTENCY|CONTRADICTION|Contradiction|Semantic Freeze|Pass #"),
]

# Application-domain documents: not needed to build the compiler.
OUT_OF_SCOPE = re.compile(
    r"\bAI\b|AGENT|MODEL SERVING|INFERENCE|GUI|Windowing|WINDOW|Rendering|RENDER|AUDIO|Audio|MEDIA|"
    r"FINANCE|TRANSPORT|CORRECTIONS|RETAIL|CONSTRUCTION|GEOSPATIAL|ENVIRONMENT|Clipboard|CLIPBOARD|"
    r"Game Engine|Machine Learning|Neural|Probabilistic|Signal Processing|Scientific|Linear Algebra|"
    r"Distributed|DISTRIBUTED|Cluster|Networking|DATABASE|Document Model|Scripting|Input, Keyboard|"
    r"WIDGETS|COMPOSITOR|APPLICATION|IPC|Crash|LOGGING|REGISTRY|Cryptography|INCIDENT|Graphics|GPU|"
    r"Heterogeneous|Android|ANDROID|JNI|MACHO|Mach-O"
)


def main():
    entries = []
    for d in DIRS:
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for f in sorted(os.listdir(p)):
            if f.endswith(".md"):
                size = os.path.getsize(os.path.join(p, f))
                entries.append((d, f, size))

    lines = [
        "# Axiom spec corpus — topic index (generated)",
        "",
        "Generated by `scripts/build_index.py`. Regenerate after docs change.",
        f"Total files: {len(entries)}. Sizes in KB. Later numbers usually supersede earlier ones on the",
        "same topic (the corpus evolved chronologically); `spec/` (canonical, written by the architect)",
        "supersedes everything here once it exists.",
        "",
        "## Contents",
    ]
    for t, _ in TOPICS:
        lines.append(f"- {t}")
    lines.append("- 99 Unclassified (in-scope)")
    lines.append("- XX Out of scope for the compiler (application domains)")
    lines.append("")

    used = set()
    oos = [(d, f, s) for d, f, s in entries if OUT_OF_SCOPE.search(f)]
    oos_set = {(d, f) for d, f, _ in oos}
    for topic, rx in TOPICS:
        r = re.compile(rx)
        hits = [(d, f, s) for d, f, s in entries if r.search(f) and (d, f) not in oos_set]
        lines.append(f"## {topic}")
        lines.append("")
        for d, f, s in hits:
            used.add((d, f))
            lines.append(f"- `{d}/{f}` ({s // 1024})")
        lines.append("")
    lines.append("## 99 Unclassified (in-scope)")
    lines.append("")
    for d, f, s in entries:
        if (d, f) not in used and (d, f) not in oos_set:
            lines.append(f"- `{d}/{f}` ({s // 1024})")
    lines.append("")
    lines.append("## XX Out of scope for the compiler (application domains)")
    lines.append("")
    for d, f, s in oos:
        lines.append(f"- `{d}/{f}` ({s // 1024})")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {OUT}: {len(entries)} files, {len(oos)} out-of-scope")


if __name__ == "__main__":
    main()
