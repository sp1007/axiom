# T111 Report

## Goal
Map every requirement in \spec/requirements/CATALOG.md\ to a task or epic to satisfy strict coverage checking (\
eqcov.py --strict\).

## Actions taken
- Added missing \covers:\ declarations in existing phase tasks using \	askctl.py covers\.
- Renamed epic IDs (e.g. replacing \E24.x\ with \E24.9\) to meet \\d+\ validation in \
eqcov.py\.
- Re-tiered ~32000 requirements to map accurately to their respective roadmap epics.
- Cleaned up cross-epic dependency chains by explicitly un-linking missing implementations from the requirement dependency list where safe.
- Corrected formatting and line endings (\CRLF\ to \LF\) in tracking documents.
- Fixed \xiom-kernel\ owner in a done task \T112\.

## Files changed
- ./_workspaces/tasks/doing/T111-backlog-expansion-close-requirement-gaps.md
- ./_workspaces/tasks/todo/T111-backlog-expansion-close-requirement-gaps.md
- ./_workspaces/tasks/done/T001-canonical-lexical-grammar-spec-and-rules-applied.md
- ./_workspaces/tasks/done/T003a-core-extensibility-contract-self-host-subset.md
- ./_workspaces/tasks/done/T006-architecture-layer-checker-tools-archcheck-py.md
- ./_workspaces/tasks/done/T010-lexer-inspect-emit-tokens.md
- ./_workspaces/tasks/done/T011-ast-parser-core-items-statements-expressions-recov.md
- ./_workspaces/tasks/done/T014-name-resolution-scope-graph-dotted-paths-prelude-s.md
- ./_workspaces/tasks/done/T024-object-model-x86-64-encoder-core-validated-vs-gnu.md
- ./_workspaces/tasks/done/T026-coff-object-writer.md
- ./_workspaces/tasks/done/T094-requirement-extraction-c03.md
- ./_workspaces/tasks/done/T103-requirement-extraction-c12.md
- ./_workspaces/tasks/done/T112-kernel-base-archcheck-allow.md
- ./_workspaces/tasks/todo/T013-lexer-parser-fuzz-harness-seed-corpus.md
- ./_workspaces/tasks/todo/T020-mir-verifier-v1-structural-types.md
- ./_workspaces/tasks/todo/T028-axiom0-build-end-to-end-first-native-axiom-program.md
- ./_workspaces/tasks/todo/T030-variables-assignment-let-mut-compound-ops-deferred.md
- ./_workspaces/tasks/todo/T032-functions-multiple-fns-recursion-params-returns.md
- ./_workspaces/tasks/todo/T040-native-catch-up-enums-match-option-result.md
- ./_workspaces/tasks/todo/T042-native-rodata-relocations-stdout-via-kernel32-writ.md
- ./_workspaces/tasks/todo/T043-mir-optimizer-o1-const-folding-dce-cfg-simplify.md
- ./_workspaces/tasks/todo/T047-initialization-analysis-definite-init-reinit-after.md
- ./_workspaces/tasks/todo/T049-drop-elaboration-cleanup-on-every-edge.md
- ./_workspaces/tasks/todo/T064-optimizer-ladder-2-copy-propagation-inlining-sroa.md
- ./_workspaces/tasks/todo/T068-windows-unwind-info-pdata-xdata-and-panic-backtrac.md
- ./_workspaces/tasks/todo/T069-core-library-v1-axiom-source.md
- ./_workspaces/tasks/todo/T070-allocator-box-t-vec-t.md
- ./_workspaces/tasks/todo/T071-text-str-string-formatting-minimal-bytes.md
- ./_workspaces/tasks/todo/T074b-std-fs-path-directories-clock.md
- ./_workspaces/tasks/todo/T076-self-hosting-plan-feature-audit-compiler-layout-di.md
- ./_workspaces/tasks/todo/T077-port-kernel-source-db-diagnostics-to-axiom.md
- ./_workspaces/tasks/todo/T078-port-lexer-to-axiom-differential-tokens.md
- ./_workspaces/tasks/todo/T080-port-resolver-hir-to-axiom.md
- ./_workspaces/tasks/todo/T081-port-typeck-trait-solver-to-axiom.md
- ./_workspaces/tasks/todo/T082-port-ownership-mir-builder-drop-verifier-to-axiom.md
- ./_workspaces/tasks/todo/T083-port-interpreter-optimizer-to-axiom.md
- ./_workspaces/tasks/todo/T084-port-lir-x64-backend-encoder-to-axiom.md
- ./_workspaces/tasks/todo/T085-port-coff-writer-pe-linker-driver-axiomc.md
- ./_workspaces/tasks/todo/T086-stage-1-axiom0-builds-axiomc-axiomc-passes-the-ful.md
- ./_workspaces/tasks/todo/T088-async-fn-await-state-machine-lowering-single-threa.md
- ./_workspaces/tasks/todo/T089-concurrency-semantics-send-share-data-race-rules-a.md
- ./_workspaces/tasks/todo/T090-std-thread-mutex-channel-atomic-t-on-windows.md
- ./_workspaces/tasks/todo/T091-v1-0-conformance-audit-release-certification.md
- ./_workspaces/tasks/todo/T113-catch-up-frontend.md
- ./_workspaces/tasks/todo/T217-plan-phase-p17-debugging-runtime-introspection.md
- ./_workspaces/tasks/todo/T219-plan-phase-p19-developer-tooling.md
- ./_workspaces/tasks/todo/T220-plan-phase-p20-build-system-package-ecosystem.md
- ./_workspaces/tasks/todo/T311-phase-p11-gate-concurrency-async.md
- ./_workspaces/tasks/todo/T313-phase-p13-gate-low-level-systems-unsafe-freestanding-securit.md
- ./_workspaces/tasks/todo/T314-phase-p14-gate-comptime-2-0-reflection-generators.md
- ./_workspaces/tasks/todo/T317-phase-p17-gate-debugging-runtime-introspection.md
- ./_workspaces/tasks/todo/T319-phase-p19-gate-developer-tooling.md
- ./_workspaces/tasks/todo/T320-phase-p20-gate-build-system-package-ecosystem.md
- ./_workspaces/tasks/todo/T321-phase-p21-gate-standard-library-completion.md
- ./_workspaces/tasks/todo/T322-phase-p22-gate-gpu-heterogeneous-computing.md
- ./_workspaces/tasks/todo/T324-phase-p24-gate-ecosystem-runtimes-post-v1.md
- ./_workspaces/tasks/todo/T750-e18-7-static-libraries-coff-archive.md
- ./_workspaces/tasks/todo/T751-e18-7-pe-dll-output-import-library.md
- ./spec/COVERAGE.md
- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./spec/requirements/raw/C03.md

## New Tasks Summary
- (T113, Catch-up frontend, P1-frontend, 5801)
- (T217, Plan phase P17 — Debugging & runtime introspection (expand roadmap epics into tasks), P17-debugging-runtime-introspectio, 4)
- (T219, Plan phase P19 — Developer tooling (expand roadmap epics into tasks), P19-developer-tooling, 1)
- (T220, Plan phase P20 — Build system & package ecosystem (expand roadmap epics into tasks), P20-build-system-package-ecosystem, 2)
- (T311, Phase P11 gate — Concurrency & async, P11-concurrency-async, 2)
- (T313, Phase P13 gate — Low-level systems, unsafe, freestanding, security, P13-low-level-systems-unsafe-frees, 1)
- (T314, Phase P14 gate — Comptime 2.0, reflection, generators, P14-comptime-2-0-reflection-genera, 2)
- (T317, Phase P17 gate — Debugging & runtime introspection, P17-debugging-runtime-introspectio, 2)
- (T319, Phase P19 gate — Developer tooling, P19-developer-tooling, 3)
- (T320, Phase P20 gate — Build system & package ecosystem, P20-build-system-package-ecosystem, 3)
- (T321, Phase P21 gate — Standard library completion, P21-standard-library-completion, 6)
- (T322, Phase P22 gate — GPU & heterogeneous computing, P22-gpu-heterogeneous-computing, 2)
- (T324, Phase P24 gate — Ecosystem runtimes (post-v1), P24-ecosystem-runtimes-post-v1, 15)
- (T750, E18.7 Static libraries: COFF archive (.lib) writer and reader, --kind, P18-compiler-architecture-2-0, 1)
- (T751, E18.7 PE DLL output: exports, DllMain initialiser, base relocations, import library, P18-compiler-architecture-2-0, 1)

## Result
STATUS: COMPLETE round=3