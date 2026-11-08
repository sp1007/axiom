# T806 Report — E19.2 `axiomc fmt` CLI (`--check`, `--stdin`), AST equivalence verifier & LSP `textDocument/formatting` integration

STATUS: COMPLETE round=1

## Summary
Implemented the post-format AST equivalence & comment conservation verifier (`compiler/fmt/verify/mod.ax`), the `axiomc fmt` CLI driver (`compiler/driver/fmt_cmd/mod.ax`), LSP `textDocument/formatting` and `textDocument/rangeFormatting` integration (`compiler/lsp/handlers/mod.ax`), and the `tests/run/fmt_cli/` verification suite per `spec/SPEC-101-canonical-formatter.md` and `spec/SPEC-100-lsp-server-ide-engine.md` (`REQ-TOOL-183`, `REQ-TOOL-298`).

## Files changed
- compiler/driver/fmt_cmd/mod.ax
- compiler/fmt/verify/mod.ax
- compiler/lsp/handlers/mod.ax
- tests/run/fmt_cli/ast_equiv_and_comment_verifier.ax
- tests/run/fmt_cli/ast_equiv_and_comment_verifier.stdout
- tests/run/fmt_cli/cli_check_stdin_and_manifest.ax
- tests/run/fmt_cli/cli_check_stdin_and_manifest.stdout
- tests/run/fmt_cli/fmt_cli.test
- tests/run/fmt_cli/fmt_cli_oracle.py
- tests/run/fmt_cli/fmt_cli_probe.ax.in
- tests/run/fmt_cli/lsp_formatting_and_range_edits.ax
- tests/run/fmt_cli/lsp_formatting_and_range_edits.stdout
