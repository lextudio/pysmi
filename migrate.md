# PLY to Lark Migration Plan (PySMI)

## Goals

- Replace PLY-based lexer/parser with Lark.
- Preserve current public behavior and parser API (`parserFactory`, `SmiV1Parser`, `SmiV2Parser`, `SmiV1CompatParser`).
- Preserve AST shape expected by existing codegen and tests.
- Remove `ply` dependency after parity is reached.

## Phase 0: Baseline and safety net

1. Freeze current behavior with tests.
   - Run full test suite and record baseline.
   - Add a dedicated parser parity test module that compares legacy parser output for representative MIB fixtures.
2. Identify high-risk behavior to preserve exactly:
   - Error classes and line numbers (`PySmiLexerError`, `PySmiParserError`).
   - Relaxed dialect options from `parserFactory`/`lexerFactory`.
   - Strict-mode checks (`config.STRICT_MODE`) for binary/hex strings.

## Phase 1: Add Lark scaffolding (no behavior switch yet)

1. Add dependency:
   - Add `lark` to dev/runtime dependencies as needed.
2. Create new modules (in parallel with PLY code):
   - `pysmi/parser/lark_parser.py`
   - `pysmi/parser/grammar/smi_v2.lark`
   - `pysmi/parser/grammar/smi_v1_relaxations.lark` (or template fragments)
3. Keep current parser entry points untouched while new parser is being built.

## Phase 2: Port lexer rules to Lark terminals

1. Map current tokens/literals from `pysmi/lexer/smi.py` into Lark terminals.
2. Recreate keyword handling:
   - Preserve reserved-word mapping (including SMIv1 aliases like `Counter -> COUNTER32`, `Gauge -> GAUGE32`).
3. Recreate lexical edge checks:
   - Forbidden words in uppercase identifiers.
   - Trailing `-` in identifiers.
   - Integer size boundaries (`UNSIGNED32_MAX`, `UNSIGNED64_MAX`).
   - Strict binary/hex string validation.
4. Recreate skip behavior currently implemented with PLY states:
   - `MACRO ... END` skipping behavior.
   - `EXPORTS ... ;` skipping behavior.
   - `CHOICE ... }` skipping behavior.
   - Comment handling (`-- ... newline`).

## Phase 3: Port grammar rules to Lark EBNF

1. Port `SmiV2Parser` grammar methods (`p_*`) into Lark grammar.
2. Keep rule naming stable where possible for transformer readability.
3. Implement a Lark `Transformer` (or `Visitor`) that produces the same tuple/list AST layout as today.
4. Verify critical clauses first:
   - Imports, type declarations, value declarations.
   - ObjectType/ObjectIdentity/Notification/ModuleIdentity/Compliance/Group clauses.
   - DEFVAL-heavy paths (largest test coverage area).

## Phase 4: Port grammar relaxation options

1. Re-implement all current options from `relaxedGrammar`:
   - `supportSmiV1Keywords`
   - `supportIndex`
   - `commaAtTheEndOfImport`
   - `commaAtTheEndOfSequence`
   - `mixOfCommasAndSpaces`
   - `uppercaseIdentifier`
   - `lowcaseIdentifier`
   - `curlyBracesAroundEnterpriseInTrap`
   - `noCells`
2. Keep `parserFactory(**grammarOptions)` API and semantics unchanged.
3. Build grammar composition strategy:
   - Base grammar + optional relaxation fragments, or
   - Programmatic grammar template generation before Lark initialization.

## Phase 5: Compatibility adapter and controlled rollout

1. Introduce `SmiV2ParserLark` with same surface API:
   - `__init__(startSym="mibFile", tempdir="")`
   - `parse(data, **kwargs)`
   - `reset()` (no-op allowed if not needed).
2. Adapt Lark exceptions to existing errors:
   - Convert to `PySmiParserError`/`PySmiLexerError` with meaningful `lineno`.
3. Add a temporary parser selection switch (env var or internal flag) to run both parsers during parity testing.
4. Keep PLY path available until all parity gates pass.

## Phase 6: Validation gates

1. Existing tests must pass unchanged.
2. Add targeted tests for Lark-specific regression risks:
   - Lexical strict-mode checks.
   - Relaxed grammar toggles and combinations.
   - Error line-number parity.
3. Add fixture-based parity tests:
   - Parse same MIB text with PLY and Lark, compare normalized AST.
4. Run performance sanity checks on representative MIB sets.

## Phase 7: Switch default and remove PLY

1. Switch `pysmi/parser/smi.py` to Lark implementation by default.
2. Update compatibility stubs:
   - `pysmi/parser/smiv1.py`
   - `pysmi/parser/smiv2.py`
   - `pysmi/parser/smiv1compat.py`
3. Remove PLY-specific caching paths/notes if obsolete.
4. Remove `ply` from dependencies and lockfile.
5. Update docs mentioning "Ply" and parser table generation/cache behavior.

## Phase 8: Cleanup and hardening

1. Remove dead PLY lexer/parser code after one stable release cycle (or immediately if no compatibility window is needed).
2. Keep parser parity tests to guard future grammar changes.
3. Document contribution workflow for grammar updates (`.lark` + transformer + tests).

## Suggested implementation order (small safe PRs)

1. Add Lark dependency and parser scaffolding.
2. Port lexer terminals + strict checks.
3. Port core grammar + transformer for main clauses.
4. Port relaxations and `parserFactory` compatibility.
5. Add parity test harness and run in CI.
6. Switch default parser.
7. Remove PLY and update docs.

## Definition of done

- All existing tests pass with Lark parser as default.
- New parity tests pass against legacy expectations.
- Public parser APIs and dialect options stay backward-compatible.
- `ply` is removed from project dependencies.
- Docs and changelog updated to reflect Lark parser behavior.
