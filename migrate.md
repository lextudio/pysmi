# Parser Migration Status (Completed)

## Summary

- PySMI now uses a single parser backend.
- `lark` is the only parser dependency in active use.
- The legacy PLY parser/lexer implementation has been removed from the source tree.

## Current Behavior

- `pysmi.parser.smi.parserFactory()` is the default parser entry point.
- Parser dialect options (`supportSmiV1Keywords`, `supportIndex`, and related relaxations) are still supported.
- `backend` is no longer required; default behavior should be used.
- Passing `backend="ply"` raises a `PySmiError`.

## Cleanup Done

- Removed `ply` from package dependency metadata.
- Removed archived PLY files (`*.bak`) from the repository.
- Updated parser backend tests to use default parser construction.
- Updated compatibility wrappers to reflect single-backend operation.

## Next Maintenance Guidance

- Keep parser behavior changes covered by regression tests in `tests/test_parser_backend.py`.
- Prefer `parserFactory()` in examples and docs; avoid backend-specific selection in new code.
