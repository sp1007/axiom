import re

translations = {
    "RQ-C07-001": "Ownership determines who owns it. Capability determines who can access it. Effect determines what it is doing. Concurrency determines if actions can happen concurrently and in what order.",
    "RQ-C07-002": "The compiler must determine what can be reordered, what cannot be reordered, and when a value is allowed to be observed by another thread.",
    "RQ-C07-003": "Axiom must allow near-ASM power access without turning the language into a CPU-specific instruction set.",
    "RQ-C07-005": "If two different Axiom implementations adhere to the Semantic Kernel, they must observe the same behavior.",
    "RQ-C07-006": "The specification determines semantics while the compiler implementation realizes the specification; the implementation must not dictate language design.",
    "RQ-C07-007": "The core subset must be small enough for rapid initial bootstrap implementation, yet powerful enough to self-host and scale to full Axiom without a compiler redesign.",
    "RQ-C07-008": "The lexer must not only recognize tokens but also preserve enough source information for the compiler to rebuild structure and for tools to work without reparsing the entire file.",
    "RQ-C07-009": "The parser determines syntactic structure, the resolver determines name meaning, the type system determines types, and the verifier determines ownership/capability validity.",
    "RQ-C07-010": "The parser knows what a name looks like; the resolver determines what the name refers to.",
    "RQ-C07-011": "The type system must be powerful enough to prove program correctness while requiring the programmer to write only the necessary type information.",
    "RQ-C07-012": "Traits act as capability/behavior contracts, generics act as compile-time abstractions, and the Trait Solver acts as the engine proving those constraints.",
    "RQ-C07-013": "The compiler must infer as much as possible with certainty, leaving the programmer to write only the information required to resolve ambiguities.",
    "RQ-C07-014": "The compiler must automatically find the correct context-dependent type usage without altering the semantic meaning of the program.",
    "RQ-C07-015": "Axiom must have completely deterministic evaluation semantics at the language level, while the optimizer is allowed to reorder anything unobservable.",
    "RQ-C07-016": "The programmer manipulates values and data structures; the compiler decides when addresses, load/store operations, registers, stack, or memory are needed.",
    "RQ-C07-017": "The programmer writes closures naturally; the compiler decides captures, environment layout, allocation (stack/register/heap), and may completely elide the closure if possible.",
    "RQ-C07-018": "A closure is a callable value with a compiler-generated environment; capture mode, layout, lifetime, and allocation are inferred from its usage.",
    "RQ-C07-019": "Generics act as abstractions at the semantic level; the compiler determines representation and specialization at the codegen level.",
    "RQ-C07-020": "Patterns must not create new ownership semantics; they only describe how the program observes, destructures, or transfers ownership of an existing value.",
    "RQ-C07-021": "The compiler must track how an operation observes or affects the external world without forcing the programmer to write effect annotations for every function.",
    "RQ-C07-022": "Comptime execution must be powerful but must not become a second independent language.",
    "RQ-C07-023": "Pattern matching identifies bound places; the ownership model defines the binding operation.",
    "RQ-C07-024": "A closure is a value with callable behavior and capture state, not a special object/class.",
    "RQ-C07-025": "A generator is a function that produces a state machine implementing the Iterator protocol.",
    "RQ-C07-026": "Scope cleanup and destructors must execute in reverse initialization order.",
    "RQ-C07-028": "The programmer views values and capabilities; the compiler views memory topology.",
    "RQ-C07-029": "Source control flow is structured; the compiler IR has a generalized CFG.",
    "RQ-C07-030": "Functions, methods, generics, closures, and trait abstractions must be completely elidable after compile-time if semantics allow.",
    "RQ-C07-031": "The backend machine model must be powerful enough for modern CPUs while having a clear architecture for future self-hosting.",
    "RQ-C07-032": "The programmer is not required to manage pointers/references for safety, but the compiler must maintain a precise memory model for optimal codegen.",
    "RQ-C07-033": "Axiom LIR must be target-independent; x86-64 is only the first backend implementing target lowering, instruction selection, register allocation, and encoding.",
    "RQ-C07-034": "Each compiler phase is responsible for proving a specific set of invariants.",
    "RQ-C07-035": "Axiom LIR must be proven independent of both register and stack machines.",
    "RQ-C07-036": "The compiler must support portable virtual machine targets with distinct module/linking/runtime contracts.",
    "RQ-C07-037": "The backend may freely choose instruction sequences but must not alter program semantics.",
    "RQ-C07-038": "Debug information describes the relationship between the semantic program and physical machine state without defining program semantics.",
    "RQ-C07-039": "Link-time is a whole-program semantic and codegen optimization boundary that must not alter semantics.",
    "RQ-C07-040": "The bootstrap implementation requires a complete architectural specification.",
    "RQ-C07-041": "The compiler architecture must map to a repository structure that enables immediate implementation while preventing architectural drift.",
    "RQ-C07-042": "Compiler IR must represent semantic facts using structured data rather than implicit conventions or arbitrary pointers.",
    "RQ-C07-043": "Every significant compiler computation must be modeled as a query with explicit dependencies.",
    "RQ-C07-044": "The compiler bootstrap implementation language must be Rust.",
    "RQ-C07-046": "CompilerDB serves as the semantic database; QueryEngine calculates and maintains that database.",
    "RQ-C07-047": "The lexer must not make decisions about whether a newline terminates a statement.",
    "RQ-C07-048": "Names are resolved first; entity semantics are determined by the type system subsequently.",
    "RQ-C07-049": "Type identity is a semantic identity; layout, ABI, and machine representation are derived layers.",
    "RQ-C07-050": "The compiler must quickly, deterministically, and traceably infer correct types despite minimal programmer type annotations.",
    "RQ-C07-051": "Typed HIR represents the semantic elaboration of the source program, not an optimization IR.",
    "RQ-C07-052": "MIR must not re-evaluate semantics already determined by HIR."
}

with open('spec/requirements/raw/C07.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('| RQ-C07-'):
        parts = line.split('|')
        req_id = parts[1].strip()
        if req_id in translations:
            parts[4] = ' ' + translations[req_id] + ' '
            lines[i] = '|'.join(parts)

with open('spec/requirements/raw/C07.md', 'w', encoding='utf-8') as f:
    f.writelines(lines)
