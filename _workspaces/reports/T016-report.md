## Files changed

- bootstrap/axiom0/src/driver/cmd_build.c
- bootstrap/axiom0/src/driver/cmd_check.c
- bootstrap/axiom0/src/driver/cmd_features.c
- bootstrap/axiom0/src/driver/cmd_inspect.c
- bootstrap/axiom0/src/driver/cmd_run.c
- bootstrap/axiom0/src/driver/driver.h
- bootstrap/axiom0/src/driver/emit_ast.c
- bootstrap/axiom0/src/driver/emit_hir.c
- bootstrap/axiom0/src/driver/emit_resolved.c
- bootstrap/axiom0/src/driver/emit_tokens.c
- bootstrap/axiom0/src/driver/pipeline.c
- tests/driver/build_missing_o.test
- tests/driver/build_ok.test
- tests/driver/check_err.test
- tests/driver/check_ok.test
- tests/driver/error.ax
- tests/driver/features.test
- tests/driver/inspect.test
- tests/driver/json.test
- tests/driver/options.test
- tests/driver/run_interp_args.test
- tests/driver/run_ok.test
- tests/driver/test.ax
- tests/driver/time_passes.test
- tests/driver/unknown_opt.test
- tests/driver/version.test

## Pipeline and Option Parsing Architecture

We introduced `ax_options_parse`, which takes a generic array of option tables. This architecture completely decouples the option parser from the specific list of options. A scratch script or a new task can add a test option simply by registering a new `AxOption` table:

```c
const AxOption ax_scratch_opts[] = {
    {"--scratch-mode", AX_OPT_BOOL, &opt_scratch, "scratch option"},
    {NULL, 0, NULL, NULL}
};

const AxOption *const ax_my_opts[] = {
    ax_scratch_opts,
    NULL
};

// We can now call the unchanged parser with our own options:
ax_options_parse(io, argc, argv, ax_my_opts, &pos_argc, &pos_argv, NULL);
```

Similarly, the pipeline executes a linear array of `AxStage` structs. A new stage can be plugged into the array without editing the pipeline execution logic `ax_pipeline_run()`, which just iterates until `stop_after` is reached. If an unavailable stage is requested (like codegen before it's implemented), it gracefully yields `AX_DRIVER_STAGE_NOT_AVAILABLE`.

## Round 1

Fixed the formatting of `## Files changed` list to be literal `- path` per line, included all files previously grouped together on single lines, and added `tests/driver/unknown_opt.test` which was introduced during QA round 0.

STATUS: COMPLETE round=1