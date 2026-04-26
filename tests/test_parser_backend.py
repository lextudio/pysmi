import importlib.util
import unittest

from pysmi import error
from pysmi.parser.smi import parserFactory


class ParserBackendTestCase(unittest.TestCase):
    SIMPLE_MIB = """
    TEST-MIB DEFINITIONS ::= BEGIN
    END
    """

    def testUnknownBackend(self):
        with self.assertRaises(error.PySmiError):
            parserFactory(backend="nope")

    def testLarkBackendBootstrap(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        ast = SmiParser().parse(self.SIMPLE_MIB)
        self.assertEqual(ast, [("TEST-MIB", None, {}, None)])

    def testLarkBackendRejectsRelaxationOptionsForNow(self):
        SmiParser = parserFactory(backend="lark", supportSmiV1Keywords=True)

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        with self.assertRaises(error.PySmiError):
            SmiParser()

    def testLarkBackendParsesImportsAndValueDeclaration(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB { 1 3 6 } DEFINITIONS ::= BEGIN
        IMPORTS
          OBJECT-TYPE, mib-2
            FROM SNMPv2-SMI
          SnmpAdminString
            FROM SNMP-FRAMEWORK-MIB;

        testValue OBJECT IDENTIFIER ::= { iso(1) org(3) dod(6) }
        END
        """

        ast = SmiParser().parse(mib)
        self.assertEqual(
            ast,
            [
                (
                    "TEST-MIB",
                    ("objectIdentifier", [1, 3, 6]),
                    {
                        "SNMPv2-SMI": ["OBJECT-TYPE", "mib-2"],
                        "SNMP-FRAMEWORK-MIB": ["SnmpAdminString"],
                    },
                    [
                        (
                            "valueDeclaration",
                            "testValue",
                            ("objectIdentifier", [("iso", 1), ("org", 3), ("dod", 6)]),
                        )
                    ],
                )
            ],
        )

    def testLarkBackendForbiddenUppercaseIdentifier(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        TRUE OBJECT IDENTIFIER ::= { 1 3 6 }
        END
        """

        with self.assertRaises(error.PySmiLexerError):
            SmiParser().parse(mib)

    def testLarkBackendParsesObjectIdentityClause(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        myIdentity OBJECT-IDENTITY
            STATUS current
            DESCRIPTION "Identity"
            ::= { 1 3 6 1 }
        END
        """

        ast = SmiParser().parse(mib)
        self.assertEqual(
            ast,
            [
                (
                    "TEST-MIB",
                    None,
                    {},
                    [
                        (
                            "objectIdentityClause",
                            "myIdentity",
                            ("Status", "current"),
                            ("DESCRIPTION", "Identity"),
                            None,
                            ("objectIdentifier", [1, 3, 6, 1]),
                        )
                    ],
                )
            ],
        )

    def testLarkBackendParsesObjectIdentityClauseWithReference(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        myIdentity OBJECT-IDENTITY
            STATUS current
            DESCRIPTION "Identity"
            REFERENCE "RFC"
            ::= { 1 3 6 1 }
        END
        """

        ast = SmiParser().parse(mib)
        self.assertEqual(
            ast,
            [
                (
                    "TEST-MIB",
                    None,
                    {},
                    [
                        (
                            "objectIdentityClause",
                            "myIdentity",
                            ("Status", "current"),
                            ("DESCRIPTION", "Identity"),
                            ("REFERENCE", "RFC"),
                            ("objectIdentifier", [1, 3, 6, 1]),
                        )
                    ],
                )
            ],
        )
