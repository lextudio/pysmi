#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
from pysmi import error
from pysmi.parser.base import AbstractParser

try:
    from lark import Lark, Transformer
    from lark.exceptions import UnexpectedInput, VisitError
except ImportError:  # pragma: no cover - exercised in environments without lark
    Lark = None
    Transformer = object
    UnexpectedInput = Exception
    VisitError = Exception

UNSIGNED32_MAX = 4294967295
UNSIGNED64_MAX = 18446744073709551615

FORBIDDEN_WORDS = {
    "ABSENT",
    "ANY",
    "BIT",
    "BOOLEAN",
    "BY",
    "COMPONENT",
    "COMPONENTS",
    "DEFAULT",
    "DEFINED",
    "ENUMERATED",
    "EXPLICIT",
    "EXTERNAL",
    "FALSE",
    "MAX",
    "MIN",
    "MINUS-INFINITY",
    "NULL",
    "OPTIONAL",
    "PLUS-INFINITY",
    "PRESENT",
    "PRIVATE",
    "REAL",
    "SET",
    "TAGS",
    "TRUE",
    "WITH",
}


_SMI_V2_BOOTSTRAP_GRAMMAR = r"""
start: mib_file

mib_file: module*

module: module_name module_oid? "DEFINITIONS" "::=" "BEGIN" exports_clause? linkage_clause? declaration_part? "END"

module_name: UPPERCASE_IDENTIFIER

module_oid: "{" object_identifier "}"

exports_clause: "EXPORTS" export_identifiers? ";"

export_identifiers: fuzzy_lowercase_identifier ("," fuzzy_lowercase_identifier)*

linkage_clause: "IMPORTS" import_stmt+ ";"

import_stmt: import_identifiers "FROM" module_name

import_identifiers: import_identifier ("," import_identifier)*

import_identifier: fuzzy_lowercase_identifier

declaration_part: declaration+

declaration: value_declaration
           | object_identity_clause

value_declaration: fuzzy_lowercase_identifier "OBJECT" "IDENTIFIER" "::=" "{" object_identifier "}"

object_identity_clause: LOWERCASE_IDENTIFIER "OBJECT-IDENTITY" "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" object_identifier "}"

status: LOWERCASE_IDENTIFIER

text: QUOTED_STRING

refer_part: "REFERENCE" text

object_identifier: subidentifiers

subidentifiers: subidentifier+

subidentifier: fuzzy_lowercase_identifier
             | NUMBER
             | LOWERCASE_IDENTIFIER "(" NUMBER ")"

fuzzy_lowercase_identifier: LOWERCASE_IDENTIFIER
                          | UPPERCASE_IDENTIFIER

UPPERCASE_IDENTIFIER: /[A-Z][-A-Za-z0-9]*/
LOWERCASE_IDENTIFIER: /[0-9]*[a-z][-A-Za-z0-9]*/
NUMBER: /-?[0-9]+/
QUOTED_STRING: /\"[^\"]*\"/

COMMENT: /--[^\r\n]*/

%import common.WS
%import common.NEWLINE
%ignore WS
%ignore NEWLINE
%ignore COMMENT
"""


class _BootstrapAstBuilder(Transformer):
    def UPPERCASE_IDENTIFIER(self, token):
        value = str(token)
        if value in FORBIDDEN_WORDS:
            raise error.PySmiLexerError(f"{value} is forbidden", lineno=token.line)
        if value.endswith("-"):
            raise error.PySmiLexerError(
                f"Identifier should not end with '-': {value}", lineno=token.line
            )
        return value

    def LOWERCASE_IDENTIFIER(self, token):
        value = str(token)
        if value.endswith("-"):
            raise error.PySmiLexerError(
                f"Identifier should not end with '-': {value}", lineno=token.line
            )
        return value

    def NUMBER(self, token):
        value = int(token)
        if abs(value) > UNSIGNED64_MAX:
            raise error.PySmiLexerError(f"Number {value} is too big", lineno=token.line)
        return value

    def start(self, items):
        return ("mibFile", items[0] if items else [])

    def mib_file(self, items):
        return list(items)

    def module_name(self, items):
        return items[0]

    def module_oid(self, items):
        return items[0]

    def linkage_clause(self, items):
        import_dict = {}
        for from_module, symbols in items:
            if from_module in import_dict:
                import_dict[from_module] += symbols
            else:
                import_dict[from_module] = symbols
        return import_dict

    def import_stmt(self, items):
        return (items[1], items[0])

    def import_identifiers(self, items):
        return list(items)

    def import_identifier(self, items):
        return items[0]

    def declaration_part(self, items):
        return list(items)

    def declaration(self, items):
        return items[0]

    def value_declaration(self, items):
        return ("valueDeclaration", items[0], items[1])

    def object_identity_clause(self, items):
        identity = items[0]
        status = items[1]
        description = ("DESCRIPTION", items[2])

        if len(items) == 5:
            reference = items[3]
            oid = items[4]
        else:
            reference = None
            oid = items[3]

        return ("objectIdentityClause", identity, status, description, reference, oid)

    def status(self, items):
        return ("Status", items[0])

    def text(self, items):
        return items[0][1:-1]

    def refer_part(self, items):
        return ("REFERENCE", items[0])

    def object_identifier(self, items):
        return ("objectIdentifier", items[0])

    def subidentifiers(self, items):
        return list(items)

    def subidentifier(self, items):
        if len(items) == 1:
            return items[0]
        return (items[0], items[1])

    def fuzzy_lowercase_identifier(self, items):
        return items[0]

    def module(self, items):
        name = items[0]
        module_oid = None
        imports = {}
        declarations = None

        for item in items[1:]:
            if isinstance(item, tuple) and item and item[0] == "objectIdentifier":
                module_oid = item
            elif isinstance(item, dict):
                imports = item
            elif isinstance(item, list):
                declarations = item

        return (name, module_oid, imports, declarations)


class SmiV2ParserLark(AbstractParser):
    _grammarOptions = {}

    def __init__(self, startSym="mibFile", tempdir=""):
        del tempdir

        if Lark is None:
            raise error.PySmiError(
                "Lark backend requested but dependency 'lark' is not installed"
            )

        if startSym != "mibFile":
            raise error.PySmiError(
                f"Lark backend currently supports startSym='mibFile', got {startSym!r}"
            )

        unsupported = sorted(k for k, v in self._grammarOptions.items() if v)
        if unsupported:
            raise error.PySmiError(
                f"Lark backend does not yet support parser options: {', '.join(unsupported)}"
            )

        self.parser = Lark(
            _SMI_V2_BOOTSTRAP_GRAMMAR,
            parser="lalr",
            start="start",
            lexer="contextual",
        )
        self.transformer = _BootstrapAstBuilder()

    def reset(self):
        return None

    def parse(self, data, **kwargs):
        del kwargs
        try:
            tree = self.parser.parse(data)
        except UnexpectedInput as exc:
            raise error.PySmiParserError(
                f"Bad grammar near offset {exc.pos_in_stream}",
                lineno=exc.line or "?",
            ) from exc

        try:
            ast = self.transformer.transform(tree)
        except VisitError as exc:
            if isinstance(exc.orig_exc, error.PySmiError):
                raise exc.orig_exc from exc
            raise error.PySmiParserError(str(exc), lineno="?") from exc

        if ast and ast[0] == "mibFile" and ast[1]:
            return ast[1]
        return []


relaxedGrammar = {
    "supportSmiV1Keywords": [],
    "supportIndex": [],
    "commaAtTheEndOfImport": [],
    "commaAtTheEndOfSequence": [],
    "mixOfCommasAndSpaces": [],
    "uppercaseIdentifier": [],
    "lowcaseIdentifier": [],
    "curlyBracesAroundEnterpriseInTrap": [],
    "noCells": [],
}


def parserFactory(**grammarOptions):
    for option in grammarOptions:
        if option not in relaxedGrammar:
            raise error.PySmiError(f"Unknown parser relaxation option: {option}")

    return type(
        "SmiLarkParser", (SmiV2ParserLark,), {"_grammarOptions": grammarOptions}
    )
