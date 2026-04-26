#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import re

from pysmi import config, error
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


_LEGACY_MACRO_RE = re.compile(r"\bMACRO\b(?P<body>.*?)(?P<end>\bEND\b)", re.DOTALL)
_LEGACY_CHOICE_RE = re.compile(r"\bCHOICE\b(?P<body>.*?)(?P<end>\})", re.DOTALL)
_LEGACY_EXPORTS_RE = re.compile(r"\bEXPORTS\b(?P<body>[^;]*);", re.DOTALL)


def _preserve_newlines(text):
    return "".join(ch for ch in text if ch in "\r\n")


def _normalize_legacy_lexer_skips(data):
    # Legacy PLY lexer skips from MACRO..END and CHOICE..} before parsing.
    def _macro_repl(match):
        return "MACRO" + _preserve_newlines(match.group("body")) + "END"

    def _choice_repl(match):
        return "CHOICE" + _preserve_newlines(match.group("body"))

    def _exports_repl(match):
        return "EXPORTS" + _preserve_newlines(match.group("body")) + ";"

    data = _LEGACY_MACRO_RE.sub(_macro_repl, data)
    data = _LEGACY_CHOICE_RE.sub(_choice_repl, data)
    return _LEGACY_EXPORTS_RE.sub(_exports_repl, data)


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

import_identifiers: import_identifiers_regular
                  | import_identifiers_trailing_comma

import_identifiers_regular: import_identifier ("," import_identifier)*

import_identifiers_trailing_comma: import_identifier ("," import_identifier)* ","

import_identifier: fuzzy_lowercase_identifier

declaration_part: declaration+

declaration: value_declaration
           | object_identity_clause
           | type_declaration
           | object_type_clause
           | trap_type_clause
           | module_identity_clause
           | notification_type_clause
           | object_group_clause
           | notification_group_clause
           | module_compliance_clause
           | agent_capabilities_clause
           | macro_clause

value_declaration: fuzzy_lowercase_identifier "OBJECT" "IDENTIFIER" "::=" "{" object_identifier "}"

object_identity_clause: LOWERCASE_IDENTIFIER "OBJECT-IDENTITY" "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" object_identifier "}"

type_declaration: type_name "::=" type_declaration_rhs

type_name: UPPERCASE_IDENTIFIER
         | type_smi

type_smi: type_smi_and_sppi
        | type_smi_only

type_smi_and_sppi: "IpAddress"      -> type_smi_ipaddress
                 | "NetworkAddress" -> type_smi_networkaddress
                 | "TimeTicks"      -> type_smi_timeticks
                 | "Opaque"         -> type_smi_opaque
                 | "Integer32"      -> type_smi_integer32
                 | "Unsigned32"     -> type_smi_unsigned32

type_smi_only: "Counter32" -> type_smi_counter32
             | "Gauge32"   -> type_smi_gauge32
             | "Counter64" -> type_smi_counter64

type_declaration_rhs: syntax                                                                  -> type_decl_rhs_syntax
                    | "TEXTUAL-CONVENTION" display_part? "STATUS" status "DESCRIPTION" text refer_part? "SYNTAX" syntax -> type_decl_rhs_tc
                    | choice_clause                                                           -> type_decl_rhs_choice

choice_clause: "CHOICE"

macro_clause: macro_name "MACRO" "END"

macro_name: "MODULE-IDENTITY"
          | "OBJECT-TYPE"
          | "TRAP-TYPE"
          | "NOTIFICATION-TYPE"
          | "OBJECT-IDENTITY"
          | "TEXTUAL-CONVENTION"
          | "OBJECT-GROUP"
          | "NOTIFICATION-GROUP"
          | "MODULE-COMPLIANCE"
          | "AGENT-CAPABILITIES"

display_part: "DISPLAY-HINT" text

status: LOWERCASE_IDENTIFIER

text: QUOTED_STRING

refer_part: "REFERENCE" text

syntax: object_syntax
      | "BITS" "{" named_bits "}" -> syntax_bits

named_bits: named_bit ("," named_bit)*

named_bit: LOWERCASE_IDENTIFIER "(" NUMBER ")"

object_syntax: simple_syntax
             | conceptual_table
             | row
             | entry_type
             | application_syntax
             | type_tag simple_syntax -> object_syntax_tagged

type_tag: "[" "APPLICATION" NUMBER "]" "IMPLICIT"
        | "[" "UNIVERSAL" NUMBER "]" "IMPLICIT"

conceptual_table: "SEQUENCE" "OF" row

row: UPPERCASE_IDENTIFIER

entry_type: "SEQUENCE" "{" sequence_items "}"

sequence_items: sequence_items_regular
              | sequence_items_trailing_comma

sequence_items_regular: sequence_item ("," sequence_item)*

sequence_items_trailing_comma: sequence_item ("," sequence_item)* ","

sequence_item: LOWERCASE_IDENTIFIER sequence_syntax

sequence_syntax: "BITS" -> sequence_syntax_bits
               | UPPERCASE_IDENTIFIER any_subtype -> sequence_syntax_upper
               | sequence_object_syntax

sequence_object_syntax: sequence_simple_syntax
                      | sequence_application_syntax

sequence_simple_syntax: "INTEGER" any_subtype -> sequence_simple_integer
                      | "Integer32" any_subtype -> sequence_simple_integer32
                      | "OCTET" "STRING" any_subtype -> sequence_simple_octet_string
                      | "OBJECT" "IDENTIFIER" any_subtype -> sequence_simple_object_identifier

sequence_application_syntax: "IpAddress" any_subtype -> sequence_app_ipaddress
                           | "NetworkAddress" any_subtype -> sequence_app_networkaddress
                           | "Counter" any_subtype -> sequence_app_counter_alias
                           | "Counter32" any_subtype -> sequence_app_counter32
                           | "Gauge" any_subtype -> sequence_app_gauge_alias
                           | "Gauge32" any_subtype -> sequence_app_gauge32
                           | "Unsigned32" any_subtype -> sequence_app_unsigned32
                           | "TimeTicks" any_subtype -> sequence_app_timeticks
                           | "Opaque" -> sequence_app_opaque
                           | "Counter64" any_subtype -> sequence_app_counter64

simple_syntax: "INTEGER"                          -> simple_integer
             | "INTEGER" integer_subtype          -> simple_integer_subtype
             | "INTEGER" enum_spec                -> simple_integer_enum
             | "Integer32"                        -> simple_integer32
             | "Integer32" integer_subtype        -> simple_integer32_subtype
             | UPPERCASE_IDENTIFIER enum_spec     -> simple_upper_enum
             | UPPERCASE_IDENTIFIER integer_subtype -> simple_upper_subtype
             | "OCTET" "STRING"                   -> simple_octet_string
             | "OCTET" "STRING" octet_string_subtype -> simple_octet_string_subtype
             | UPPERCASE_IDENTIFIER octet_string_subtype -> simple_upper_octet_subtype
             | "OBJECT" "IDENTIFIER" any_subtype  -> simple_object_identifier

application_syntax: "IpAddress" any_subtype         -> app_ipaddress
                  | "NetworkAddress" any_subtype     -> app_networkaddress
                  | "Counter"                        -> app_counter_alias
                  | "Counter" integer_subtype        -> app_counter_alias_subtype
                  | "Counter32"                      -> app_counter32
                  | "Counter32" integer_subtype      -> app_counter32_subtype
                  | "Gauge"                          -> app_gauge_alias
                  | "Gauge" integer_subtype          -> app_gauge_alias_subtype
                  | "Gauge32"                        -> app_gauge32
                  | "Gauge32" integer_subtype        -> app_gauge32_subtype
                  | "Unsigned32"                     -> app_unsigned32
                  | "Unsigned32" integer_subtype     -> app_unsigned32_subtype
                  | "TimeTicks" any_subtype          -> app_timeticks
                  | "Opaque"                         -> app_opaque
                  | "Opaque" octet_string_subtype    -> app_opaque_subtype
                  | "Counter64"                      -> app_counter64
                  | "Counter64" integer_subtype      -> app_counter64_subtype

any_subtype: integer_subtype
           | octet_string_subtype
           | enum_spec
           | empty

empty:

integer_subtype: "(" ranges ")"

octet_string_subtype: "(" "SIZE" "(" ranges ")" ")"

ranges: range ("|" range)*

range: value [".." value]

value: NUMBER
     | HEX_STRING
     | BIN_STRING

enum_spec: "{" enum_items "}"

enum_items: enum_item enum_items_rest*

enum_items_rest: "," enum_item -> enum_items_rest_comma
               | enum_item     -> enum_items_rest_space
               | ","           -> enum_items_rest_trailing

enum_item: LOWERCASE_IDENTIFIER "(" enum_number ")"  -> enum_item_lower
         | UPPERCASE_IDENTIFIER "(" enum_number ")"  -> enum_item_upper

enum_number: NUMBER

object_type_clause: LOWERCASE_IDENTIFIER "OBJECT-TYPE" "SYNTAX" syntax units_part? max_or_pib_access_part? "STATUS" status description_clause? refer_part? index_part? mib_index? defval_part? "::=" "{" object_name "}"

units_part: "UNITS" text

max_or_pib_access_part: max_access_part

max_access_part: "MAX-ACCESS" access
               | "ACCESS" access

access: LOWERCASE_IDENTIFIER

description_clause: "DESCRIPTION" text

index_part: "AUGMENTS" "{" entry "}"

mib_index: "INDEX" "{" index_types "}"

index_types: index_type ("," index_type)*

index_type: "IMPLIED" index -> index_type_implied
          | index           -> index_type_plain

index: object_name
     | type_smiv1

type_smiv1: "INTEGER"                    -> type_smiv1_integer
          | "OCTET" "STRING"             -> type_smiv1_octet_string
          | "IpAddress"                  -> type_smiv1_ipaddress
          | "NetworkAddress"             -> type_smiv1_networkaddress

entry: object_name

defval_part: "DEFVAL" "{" defval_value "}"

defval_value: valueof_object_syntax
            | "{" bits_value "}" -> defval_bits

valueof_object_syntax: valueof_simple_syntax

valueof_simple_syntax: NUMBER
                     | HEX_STRING
                     | BIN_STRING
                     | LOWERCASE_IDENTIFIER
                     | QUOTED_STRING
                     | "{" object_identifier_defval "}" -> valueof_simple_oid_defval

object_identifier_defval: subidentifiers_defval

subidentifiers_defval: subidentifier_defval+

subidentifier_defval: NUMBER
                    | LOWERCASE_IDENTIFIER "(" NUMBER ")" -> subidentifier_defval_named

bits_value: bit_names?

bit_names: LOWERCASE_IDENTIFIER ("," LOWERCASE_IDENTIFIER)*

object_name: object_identifier

notification_type_clause: fuzzy_lowercase_identifier "NOTIFICATION-TYPE" notification_objects_part? "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" notification_name "}"

notification_objects_part: "OBJECTS" "{" objects "}"

object_group_clause: LOWERCASE_IDENTIFIER "OBJECT-GROUP" object_group_objects_part "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" object_identifier "}"

object_group_objects_part: "OBJECTS" "{" objects "}"

notifications_part: "NOTIFICATIONS" "{" notifications "}"

notification_group_clause: LOWERCASE_IDENTIFIER "NOTIFICATION-GROUP" notifications_part "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" object_identifier "}"

module_identity_clause: LOWERCASE_IDENTIFIER "MODULE-IDENTITY" subject_categories_part? "LAST-UPDATED" ext_utc_time "ORGANIZATION" text "CONTACT-INFO" text "DESCRIPTION" text revision_part? "::=" "{" object_identifier "}"

subject_categories_part: "SUBJECT-CATEGORIES" "{" subject_categories "}"

subject_categories: category_id ("," category_id)*

category_id: LOWERCASE_IDENTIFIER ["(" NUMBER ")"]

revision_part: revisions

revisions: revision+

revision: "REVISION" ext_utc_time "DESCRIPTION" text

ext_utc_time: QUOTED_STRING

module_compliance_clause: LOWERCASE_IDENTIFIER "MODULE-COMPLIANCE" "STATUS" status "DESCRIPTION" text refer_part? compliance_module_part "::=" "{" object_identifier "}"

compliance_module_part: compliance_modules

compliance_modules: compliance_module+

compliance_module: "MODULE" compliance_module_name mandatory_part? compliance_part?

compliance_module_name: UPPERCASE_IDENTIFIER?

mandatory_part: "MANDATORY-GROUPS" "{" mandatory_groups "}"

mandatory_groups: mandatory_group ("," mandatory_group)*

mandatory_group: object_identifier

compliance_part: compliances

compliances: compliance+

compliance: compliance_group
          | compliance_object

compliance_group: "GROUP" object_identifier "DESCRIPTION" text

compliance_object: "OBJECT" object_name syntax_part? write_syntax_part? access_part? "DESCRIPTION" text

syntax_part: "SYNTAX" syntax

write_syntax_part: "WRITE-SYNTAX" write_syntax

write_syntax: syntax

access_part: "MIN-ACCESS" access

objects: object ("," object)*

object: object_name

notifications: notification ("," notification)*

notification: notification_name

notification_name: object_identifier

trap_type_clause: fuzzy_lowercase_identifier "TRAP-TYPE" enterprise_part var_part descr_part refer_part? "::=" NUMBER

enterprise_part: "ENTERPRISE" object_identifier
               | "ENTERPRISE" "{" object_identifier "}" -> enterprise_braced

var_part: "VARIABLES" "{" var_types "}"
        | empty

var_types: var_type ("," var_type)*

var_type: object_name

descr_part: "DESCRIPTION" text
          | empty

agent_capabilities_clause: LOWERCASE_IDENTIFIER "AGENT-CAPABILITIES" "PRODUCT-RELEASE" text "STATUS" status "DESCRIPTION" text refer_part? module_part_capabilities? "::=" "{" object_identifier "}"

module_part_capabilities: modules_capabilities
                        | empty

modules_capabilities: module_capabilities+

module_capabilities: "SUPPORTS" module_name_capabilities "INCLUDES" "{" capabilities_groups "}" variation_part

capabilities_groups: capabilities_group ("," capabilities_group)*

capabilities_group: object_identifier

module_name_capabilities: UPPERCASE_IDENTIFIER [object_identifier]

variation_part: variations
              | empty

variations: variation+

variation: "VARIATION" object_name syntax_part? write_syntax_part? variation_access_part? creation_part? defval_part? "DESCRIPTION" text

variation_access_part: "ACCESS" variation_access

variation_access: LOWERCASE_IDENTIFIER

creation_part: "CREATION-REQUIRES" "{" cells "}"
             | "CREATION-REQUIRES" "{" "}" -> creation_no_cells

cells: cell ("," cell)*

cell: object_name

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
HEX_STRING: /'[0-9a-fA-F]*'[hH]/
BIN_STRING: /'[01]*'[bB]/
QUOTED_STRING: /\"[^\"]*\"/

COMMENT: /--[^\r\n]*/

%import common.WS
%import common.NEWLINE
%ignore WS
%ignore NEWLINE
%ignore COMMENT
"""


class _BootstrapAstBuilder(Transformer):
    def __init__(self, grammarOptions=None):
        super().__init__()
        self._grammarOptions = grammarOptions or {}

    def _enabled(self, option):
        return bool(self._grammarOptions.get(option))

    def UPPERCASE_IDENTIFIER(self, token):
        value = str(token)
        if value in FORBIDDEN_WORDS and not (
            value == "MAX" and self._enabled("supportSmiV1Keywords")
        ):
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

    def BIN_STRING(self, token):
        value = str(token)
        bits = value[1:-2]

        while bits and bits[0] == "0" and len(bits) % 8:
            bits = bits[1:]

            if config.STRICT_MODE and len(bits) % 8:
                raise error.PySmiLexerError(
                    f"Number of 0s and 1s have to divide by 8 in binary string {value}",
                    lineno=token.line,
                )

        return value

    def HEX_STRING(self, token):
        value = str(token)
        digits = value[1:-2]

        while digits and digits[0] == "0" and len(digits) % 2:
            digits = digits[1:]

            if config.STRICT_MODE and len(digits) % 2:
                raise error.PySmiLexerError(
                    f"Number of symbols have to be even in hex string {value}",
                    lineno=token.line,
                )

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
        return items[0]

    def import_identifiers_regular(self, items):
        return list(items)

    def import_identifiers_trailing_comma(self, items):
        if not self._enabled("commaAtTheEndOfImport"):
            raise error.PySmiParserError(
                "Trailing comma in IMPORTS requires commaAtTheEndOfImport option",
                lineno="?",
            )
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

    def type_declaration(self, items):
        return ("typeDeclaration", items[0], items[1])

    def type_name(self, items):
        return items[0]

    def type_smi(self, items):
        return items[0]

    def type_smi_and_sppi(self, items):
        return items[0]

    def type_smi_only(self, items):
        return items[0]

    def type_smi_ipaddress(self, _items):
        return "IpAddress"

    def type_smi_networkaddress(self, _items):
        return "NetworkAddress"

    def type_smi_timeticks(self, _items):
        return "TimeTicks"

    def type_smi_opaque(self, _items):
        return "Opaque"

    def type_smi_integer32(self, _items):
        return "Integer32"

    def type_smi_unsigned32(self, _items):
        return "Unsigned32"

    def type_smi_counter32(self, _items):
        return "Counter32"

    def type_smi_gauge32(self, _items):
        return "Gauge32"

    def type_smi_counter64(self, _items):
        return "Counter64"

    def type_decl_rhs_syntax(self, items):
        return ("typeDeclarationRHS", items[0])

    def type_decl_rhs_tc(self, items):
        display = None
        idx = 0

        if items and isinstance(items[0], tuple) and items[0][0] == "DISPLAY-HINT":
            display = items[0]
            idx = 1

        status = items[idx]
        description = ("DESCRIPTION", items[idx + 1])
        rest = items[idx + 2 :]

        if len(rest) == 1:
            refer = None
            syntax = rest[0]
        else:
            refer = rest[0]
            syntax = rest[1]

        return ("typeDeclarationRHS", display, status, description, refer, syntax)

    def type_decl_rhs_choice(self, _items):
        return None

    def choice_clause(self, _items):
        return "CHOICE"

    def macro_clause(self, _items):
        return None

    def display_part(self, items):
        return ("DISPLAY-HINT", items[0])

    def syntax(self, items):
        return items[0]

    def syntax_bits(self, items):
        return ("BITS", items[0])

    def named_bits(self, items):
        return list(items)

    def named_bit(self, items):
        return (items[0], items[1])

    def object_syntax(self, items):
        return items[0]

    def object_syntax_tagged(self, items):
        return items[-1]

    def type_tag(self, _items):
        return None

    def conceptual_table(self, items):
        return ("conceptualTable", items[0])

    def row(self, items):
        return ("row", items[0])

    def entry_type(self, items):
        return ("SEQUENCE", items[0])

    def sequence_items(self, items):
        return items[0]

    def sequence_items_regular(self, items):
        return list(items)

    def sequence_items_trailing_comma(self, items):
        if not self._enabled("commaAtTheEndOfSequence"):
            raise error.PySmiParserError(
                "Trailing comma in SEQUENCE requires commaAtTheEndOfSequence option",
                lineno="?",
            )
        return list(items)

    def sequence_item(self, items):
        return (items[0], items[1])

    def sequence_syntax_bits(self, _items):
        return "BITS"

    def sequence_syntax_upper(self, items):
        return items[0]

    def sequence_syntax(self, items):
        return items[0]

    def sequence_object_syntax(self, items):
        return items[0]

    def sequence_simple_integer(self, _items):
        return "INTEGER"

    def sequence_simple_integer32(self, _items):
        return "Integer32"

    def sequence_simple_octet_string(self, _items):
        return "OCTET STRING"

    def sequence_simple_object_identifier(self, _items):
        return "OBJECT IDENTIFIER"

    def sequence_app_ipaddress(self, _items):
        return "IpAddress"

    def sequence_app_networkaddress(self, _items):
        return "NetworkAddress"

    def sequence_app_counter_alias(self, _items):
        return "Counter"

    def sequence_app_counter32(self, _items):
        return "Counter32"

    def sequence_app_gauge_alias(self, _items):
        return "Gauge"

    def sequence_app_gauge32(self, _items):
        return "Gauge32"

    def sequence_app_unsigned32(self, _items):
        return "Unsigned32"

    def sequence_app_timeticks(self, _items):
        return "TimeTicks"

    def sequence_app_opaque(self, _items):
        return "Opaque"

    def sequence_app_counter64(self, _items):
        return "Counter64"

    def simple_integer(self, _items):
        return ("SimpleSyntax", "INTEGER")

    def simple_integer_subtype(self, items):
        return ("SimpleSyntax", "INTEGER", items[0])

    def simple_integer_enum(self, items):
        return ("SimpleSyntax", "INTEGER", items[0])

    def simple_integer32(self, _items):
        return ("SimpleSyntax", "Integer32")

    def simple_integer32_subtype(self, items):
        return ("SimpleSyntax", "Integer32", items[0])

    def simple_upper_enum(self, items):
        return ("SimpleSyntax", items[0], items[1])

    def simple_upper_subtype(self, items):
        return ("SimpleSyntax", items[0], items[1])

    def simple_octet_string(self, _items):
        return ("SimpleSyntax", "OCTET STRING")

    def simple_octet_string_subtype(self, items):
        return ("SimpleSyntax", "OCTET STRING", items[0])

    def simple_upper_octet_subtype(self, items):
        return ("SimpleSyntax", items[0], items[1])

    def simple_object_identifier(self, items):
        return ("SimpleSyntax", "OBJECT IDENTIFIER", items[0])

    def app_ipaddress(self, items):
        return ("ApplicationSyntax", "IpAddress", items[0])

    def app_networkaddress(self, items):
        if not self._enabled("supportSmiV1Keywords"):
            subtype = items[0] if items else None
            if subtype is None:
                return ("row", "NetworkAddress")
            return ("SimpleSyntax", "NetworkAddress", subtype)
        return ("ApplicationSyntax", "NetworkAddress", items[0])

    def app_counter_alias(self, _items):
        return ("ApplicationSyntax", "Counter")

    def app_counter_alias_subtype(self, items):
        return ("ApplicationSyntax", "Counter", items[0])

    def app_counter32(self, _items):
        return ("ApplicationSyntax", "Counter32")

    def app_counter32_subtype(self, items):
        return ("ApplicationSyntax", "Counter32", items[0])

    def app_gauge_alias(self, _items):
        return ("ApplicationSyntax", "Gauge")

    def app_gauge_alias_subtype(self, items):
        return ("ApplicationSyntax", "Gauge", items[0])

    def app_gauge32(self, _items):
        return ("ApplicationSyntax", "Gauge32")

    def app_gauge32_subtype(self, items):
        return ("ApplicationSyntax", "Gauge32", items[0])

    def app_unsigned32(self, _items):
        return ("ApplicationSyntax", "Unsigned32")

    def app_unsigned32_subtype(self, items):
        return ("ApplicationSyntax", "Unsigned32", items[0])

    def app_timeticks(self, items):
        return ("ApplicationSyntax", "TimeTicks", items[0])

    def app_opaque(self, _items):
        return ("ApplicationSyntax", "Opaque")

    def app_opaque_subtype(self, items):
        return ("ApplicationSyntax", "Opaque", items[0])

    def app_counter64(self, _items):
        return ("ApplicationSyntax", "Counter64")

    def app_counter64_subtype(self, items):
        return ("ApplicationSyntax", "Counter64", items[0])

    def any_subtype(self, items):
        return items[0] if items else None

    def empty(self, _items):
        return None

    def integer_subtype(self, items):
        return ("integerSubType", items[0])

    def octet_string_subtype(self, items):
        return ("octetStringSubType", items[0])

    def ranges(self, items):
        return list(items)

    def range(self, items):
        if len(items) == 1:
            return (items[0],)
        if len(items) == 2 and items[1] is None:
            return (items[0],)
        return (items[0], items[1])

    def value(self, items):
        return items[0]

    def enum_spec(self, items):
        return ("enumSpec", items[0])

    def enum_items(self, items):
        values = [items[0]]
        used_relaxed = False

        for mode, value in items[1:]:
            if mode == "comma":
                values.append(value)
            elif mode == "space":
                used_relaxed = True
                values.append(value)
            elif mode == "trailing":
                used_relaxed = True

        if used_relaxed and not self._enabled("mixOfCommasAndSpaces"):
            raise error.PySmiParserError(
                "Mixed comma/space enum items require mixOfCommasAndSpaces option",
                lineno="?",
            )
        return values

    def enum_items_rest_comma(self, items):
        return ("comma", items[0])

    def enum_items_rest_space(self, items):
        return ("space", items[0])

    def enum_items_rest_trailing(self, _items):
        return ("trailing", None)

    def enum_item_lower(self, items):
        return (items[0], items[1])

    def enum_item_upper(self, items):
        if not self._enabled("uppercaseIdentifier"):
            raise error.PySmiParserError(
                "Uppercase enum items require uppercaseIdentifier option", lineno="?"
            )
        return (items[0], items[1])

    def enum_number(self, items):
        return items[0]

    def object_type_clause(self, items):
        identity = items[0]
        syntax = items[1]
        units = None
        max_access = None
        status = None
        description = None
        reference = None
        augmentions = None
        mib_index = None
        defval = None
        object_name = items[-1]

        for item in items[2:-1]:
            if isinstance(item, tuple):
                if item and item[0] == "UNITS":
                    units = item
                elif item and item[0] == "MaxAccessPart":
                    max_access = item
                elif item and item[0] == "Status":
                    status = item
                elif item and item[0] == "DESCRIPTION":
                    description = item
                elif item and item[0] == "REFERENCE":
                    reference = item
                elif item and item[0] == "INDEX":
                    mib_index = item
                elif item and item[0] == "DEFVAL":
                    defval = item
            else:
                augmentions = item

        return (
            "objectTypeClause",
            identity,
            syntax,
            units,
            max_access,
            status,
            description,
            reference,
            augmentions,
            mib_index,
            defval,
            object_name,
        )

    def units_part(self, items):
        return ("UNITS", items[0])

    def max_or_pib_access_part(self, items):
        return items[0]

    def max_access_part(self, items):
        return ("MaxAccessPart", items[0])

    def access(self, items):
        return items[0]

    def description_clause(self, items):
        return ("DESCRIPTION", items[0])

    def index_part(self, items):
        return items[0]

    def mib_index(self, items):
        return ("INDEX", items[0])

    def index_types(self, items):
        return list(items)

    def index_type_plain(self, items):
        return (0, items[0])

    def index_type_implied(self, items):
        return (1, items[0])

    def index(self, items):
        item = items[0]
        if isinstance(item, tuple) and item and item[0] == "typeSMIv1":
            if not self._enabled("supportIndex"):
                raise error.PySmiParserError(
                    "SMIv1 index types require supportIndex option", lineno="?"
                )
            return item[1]
        return item[1][0]

    def type_smiv1_integer(self, _items):
        return ("typeSMIv1", "INTEGER")

    def type_smiv1_octet_string(self, _items):
        return ("typeSMIv1", "OCTET STRING")

    def type_smiv1_ipaddress(self, _items):
        return ("typeSMIv1", "IpAddress")

    def type_smiv1_networkaddress(self, _items):
        if not self._enabled("supportSmiV1Keywords"):
            # In non-SMIv1 mode this is just an identifier token in PLY.
            return ("objectIdentifier", ["NetworkAddress"])
        return ("typeSMIv1", "NetworkAddress")

    def entry(self, items):
        return items[0][1][0]

    def defval_part(self, items):
        if items[0] is not None:
            return ("DEFVAL", items[0])
        return None

    def defval_value(self, items):
        return items[0]

    def defval_bits(self, items):
        return items[0]

    def valueof_object_syntax(self, items):
        return items[0]

    def valueof_simple_syntax(self, items):
        value = items[0]
        return value if isinstance(value, int) else str(value)

    def valueof_simple_oid_defval(self, _items):
        # Match legacy PLY behavior: accept invalid nested OID notation
        # in DEFVAL without constructing a concrete value.
        return None

    def object_identifier_defval(self, items):
        return ("objectIdentifier_defval", items[0])

    def subidentifiers_defval(self, items):
        return ("subidentifiers_defval", list(items))

    def subidentifier_defval(self, items):
        return ("subidentifier_defval", items[0])

    def subidentifier_defval_named(self, items):
        return ("subidentifier_defval", items[0], items[1])

    def bits_value(self, items):
        if items:
            return items[0]
        return []

    def bit_names(self, items):
        return ("BitNames", list(items))

    def object_name(self, items):
        return items[0]

    def notification_type_clause(self, items):
        identity = items[0]
        if identity[:1].isupper() and not self._enabled("lowcaseIdentifier"):
            raise error.PySmiParserError(
                "Uppercase notification identifiers require lowcaseIdentifier option",
                lineno="?",
            )
        idx = 1

        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "Objects"
        ):
            objects = items[idx]
            idx += 1
        else:
            objects = []

        status = items[idx]
        description = ("DESCRIPTION", items[idx + 1])
        idx += 2

        if idx < len(items) - 1:
            reference = items[idx]
            idx += 1
        else:
            reference = None

        notification_name = items[idx]

        return (
            "notificationTypeClause",
            identity,
            objects,
            status,
            description,
            reference,
            notification_name,
        )

    def notification_objects_part(self, items):
        return items[0]

    def object_group_clause(self, items):
        identity = items[0]
        objects = items[1]
        status = items[2]
        description = ("DESCRIPTION", items[3])

        if len(items) == 5:
            reference = None
            oid = items[4]
        else:
            reference = items[4]
            oid = items[5]

        return (
            "objectGroupClause",
            identity,
            objects,
            status,
            description,
            reference,
            oid,
        )

    def object_group_objects_part(self, items):
        return items[0]

    def notification_group_clause(self, items):
        identity = items[0]
        notifications = items[1]
        status = items[2]
        description = ("DESCRIPTION", items[3])

        if len(items) == 5:
            reference = None
            oid = items[4]
        else:
            reference = items[4]
            oid = items[5]

        return (
            "notificationGroupClause",
            identity,
            notifications,
            status,
            description,
            reference,
            oid,
        )

    def notifications_part(self, items):
        return items[0]

    def module_identity_clause(self, items):
        filtered = [item for item in items if item is not None]
        identity = filtered[0]
        last_updated = ("LAST-UPDATED", filtered[1])
        organization = ("ORGANIZATION", filtered[2])
        contact_info = ("CONTACT-INFO", filtered[3])
        description = ("DESCRIPTION", filtered[4])

        if len(filtered) == 6:
            revision = None
            oid = filtered[5]
        else:
            revision = filtered[5]
            oid = filtered[6]

        return (
            "moduleIdentityClause",
            identity,
            last_updated,
            organization,
            contact_info,
            description,
            revision,
            oid,
        )

    def subject_categories_part(self, _items):
        return None

    def subject_categories(self, _items):
        return None

    def category_id(self, _items):
        return None

    def revision_part(self, items):
        return items[0]

    def revisions(self, items):
        return ("Revisions", list(items))

    def revision(self, items):
        return (items[0], ("DESCRIPTION", items[1]))

    def ext_utc_time(self, items):
        return items[0][1:-1]

    def module_compliance_clause(self, items):
        identity = items[0]
        status = items[1]
        description = ("DESCRIPTION", items[2])

        if len(items) == 5:
            reference = None
            compliance_modules = items[3]
            oid = items[4]
        else:
            reference = items[3]
            compliance_modules = items[4]
            oid = items[5]

        return (
            "moduleComplianceClause",
            identity,
            status,
            description,
            reference,
            compliance_modules,
            oid,
        )

    def compliance_module_part(self, items):
        return items[0]

    def compliance_modules(self, items):
        return ("ComplianceModules", list(items))

    def compliance_module(self, items):
        module_name = items[0]
        mandatory = None
        compliance = None

        for item in items[1:]:
            if isinstance(item, tuple) and item and item[0] == "MandatoryGroups":
                mandatory = item
            elif isinstance(item, tuple) and item and item[0] == "Compliances":
                compliance = item

        objects = []
        if mandatory:
            objects += mandatory[1]
        if compliance:
            objects += compliance[1]

        return (module_name, objects)

    def compliance_module_name(self, items):
        return items[0] if items else None

    def mandatory_part(self, items):
        return items[0]

    def mandatory_groups(self, items):
        return ("MandatoryGroups", list(items))

    def mandatory_group(self, items):
        return items[0][1][0]

    def compliance_part(self, items):
        return items[0]

    def compliances(self, items):
        values = [item for item in items if item is not None]
        if not values:
            return None
        return ("Compliances", values)

    def compliance(self, items):
        return items[0]

    def compliance_group(self, items):
        return items[0][1][0]

    def compliance_object(self, _items):
        return None

    def syntax_part(self, items):
        return items[0]

    def write_syntax_part(self, items):
        return ("WriteSyntax", items[0])

    def write_syntax(self, items):
        return items[0]

    def access_part(self, items):
        return ("MIN-ACCESS", items[0])

    def objects(self, items):
        return ("Objects", list(items))

    def object(self, items):
        return items[0][1][0]

    def notifications(self, items):
        return ("Notifications", list(items))

    def notification(self, items):
        return items[0][1][0]

    def notification_name(self, items):
        return items[0]

    def trap_type_clause(self, items):
        identity = items[0]
        enterprise = items[1]
        var_part = items[2]
        descr_part = items[3]

        if len(items) == 5:
            refer_part = None
            number = items[4]
        else:
            refer_part = items[4]
            number = items[5]

        return (
            "trapTypeClause",
            identity,
            enterprise,
            var_part,
            descr_part,
            refer_part,
            number,
        )

    def enterprise_part(self, items):
        return items[-1]

    def enterprise_braced(self, items):
        if not self._enabled("curlyBracesAroundEnterpriseInTrap"):
            raise error.PySmiParserError(
                "Braced ENTERPRISE requires curlyBracesAroundEnterpriseInTrap option",
                lineno="?",
            )
        return items[0]

    def var_part(self, items):
        if items and items[0] is not None:
            return items[0]
        return []

    def var_types(self, items):
        return ("VarTypes", list(items))

    def var_type(self, items):
        return items[0][1][0]

    def descr_part(self, items):
        if items and items[0] is not None:
            return ("DESCRIPTION", items[0])
        return None

    def agent_capabilities_clause(self, items):
        identity = items[0]
        product_release = ("PRODUCT-RELEASE", items[1])
        status = items[2]
        description = ("DESCRIPTION", items[3])

        idx = 4
        if (
            idx < len(items)
            and isinstance(items[idx], tuple)
            and items[idx][0] == "REFERENCE"
        ):
            reference = items[idx]
            idx += 1
        else:
            reference = None

        oid = items[-1]

        return (
            "agentCapabilitiesClause",
            identity,
            product_release,
            status,
            description,
            reference,
            oid,
        )

    def module_part_capabilities(self, _items):
        return None

    def modules_capabilities(self, _items):
        return None

    def module_capabilities(self, _items):
        return None

    def capabilities_groups(self, _items):
        return None

    def capabilities_group(self, _items):
        return None

    def module_name_capabilities(self, _items):
        return None

    def variation_part(self, _items):
        return None

    def variations(self, _items):
        return None

    def variation(self, _items):
        return None

    def variation_access_part(self, _items):
        return None

    def variation_access(self, _items):
        return None

    def creation_part(self, _items):
        return None

    def creation_no_cells(self, _items):
        if not self._enabled("noCells"):
            raise error.PySmiParserError(
                "Empty CREATION-REQUIRES requires noCells option", lineno="?"
            )
        return None

    def cells(self, _items):
        return None

    def cell(self, _items):
        return None

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


class SmiV2Parser(AbstractParser):
    _grammarOptions = {}
    _implementedOptions = {
        "supportSmiV1Keywords",
        "supportIndex",
        "commaAtTheEndOfImport",
        "commaAtTheEndOfSequence",
        "mixOfCommasAndSpaces",
        "uppercaseIdentifier",
        "lowcaseIdentifier",
        "curlyBracesAroundEnterpriseInTrap",
        "noCells",
    }

    def __init__(self, startSym="mibFile", tempdir=""):
        del tempdir

        if Lark is None:
            raise error.PySmiError("Parser dependency 'lark' is not installed")

        if startSym != "mibFile":
            raise error.PySmiError(
                f"Parser currently supports startSym='mibFile', got {startSym!r}"
            )

        unsupported = sorted(
            k
            for k, v in self._grammarOptions.items()
            if v and k not in self._implementedOptions
        )
        if unsupported:
            raise error.PySmiError(
                f"Parser does not yet support parser options: {', '.join(unsupported)}"
            )

        self.parser = Lark(
            _SMI_V2_BOOTSTRAP_GRAMMAR,
            parser="lalr",
            start="start",
            lexer="contextual",
        )
        self.transformer = _BootstrapAstBuilder(self._grammarOptions)

    def reset(self):
        return None

    def parse(self, data, **kwargs):
        del kwargs
        data = _normalize_legacy_lexer_skips(data)
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

    return type("SmiParser", (SmiV2Parser,), {"_grammarOptions": grammarOptions})
