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
           | type_declaration
           | object_type_clause
           | module_identity_clause
           | notification_type_clause
           | object_group_clause
           | notification_group_clause
           | module_compliance_clause

value_declaration: fuzzy_lowercase_identifier "OBJECT" "IDENTIFIER" "::=" "{" object_identifier "}"

object_identity_clause: LOWERCASE_IDENTIFIER "OBJECT-IDENTITY" "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" object_identifier "}"

type_declaration: type_name "::=" type_declaration_rhs

type_name: UPPERCASE_IDENTIFIER

type_declaration_rhs: syntax                                                                  -> type_decl_rhs_syntax
                    | "TEXTUAL-CONVENTION" display_part? "STATUS" status "DESCRIPTION" text refer_part? "SYNTAX" syntax -> type_decl_rhs_tc

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

conceptual_table: "SEQUENCE" "OF" row

row: UPPERCASE_IDENTIFIER

entry_type: "SEQUENCE" "{" sequence_items "}"

sequence_items: sequence_item ("," sequence_item)*

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
                           | "Counter32" any_subtype -> sequence_app_counter32
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
                  | "Counter32"                      -> app_counter32
                  | "Counter32" integer_subtype      -> app_counter32_subtype
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

enum_spec: "{" enum_items "}"

enum_items: enum_item ("," enum_item)*

enum_item: LOWERCASE_IDENTIFIER "(" enum_number ")"

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

bits_value: bit_names?

bit_names: LOWERCASE_IDENTIFIER ("," LOWERCASE_IDENTIFIER)*

object_name: object_identifier

notification_type_clause: LOWERCASE_IDENTIFIER "NOTIFICATION-TYPE" notification_objects_part? "STATUS" status "DESCRIPTION" text refer_part? "::=" "{" notification_name "}"

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

    def type_declaration(self, items):
        return ("typeDeclaration", items[0], items[1])

    def type_name(self, items):
        return items[0]

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

    def conceptual_table(self, items):
        return ("conceptualTable", items[0])

    def row(self, items):
        return ("row", items[0])

    def entry_type(self, items):
        return ("SEQUENCE", items[0])

    def sequence_items(self, items):
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

    def sequence_app_counter32(self, _items):
        return "Counter32"

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

    def app_counter32(self, _items):
        return ("ApplicationSyntax", "Counter32")

    def app_counter32_subtype(self, items):
        return ("ApplicationSyntax", "Counter32", items[0])

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
        return list(items)

    def enum_item(self, items):
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
        return items[0][1][0]

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
