import importlib.util
import unittest

from pysmi import config, error
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

    def testLarkBackendSupportsMixOfCommasAndSpacesParity(self):
        larkParser = parserFactory(backend="lark", mixOfCommasAndSpaces=True)
        plyParser = parserFactory(mixOfCommasAndSpaces=True)

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { one(1), two(2) three(3), }
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendRejectsEnumCommaSpaceMixWithoutOption(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { one(1) two(2) }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testLarkBackendStrictModeInvalidBinaryStringParity(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testObject OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "bits"
            DEFVAL { '011'B }
         ::= { 1 1 }
        END
        """

        strict_mode = config.STRICT_MODE
        self.addCleanup(setattr, config, "STRICT_MODE", strict_mode)
        config.STRICT_MODE = True

        with self.assertRaises(error.PySmiLexerError):
            larkParser().parse(mib)
        with self.assertRaises(error.PySmiLexerError):
            plyParser().parse(mib)

    def testLarkBackendStrictModeHexStringParity(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testObject OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "hex"
            DEFVAL { '0ABC'H }
         ::= { 1 1 }
        END
        """

        strict_mode = config.STRICT_MODE
        self.addCleanup(setattr, config, "STRICT_MODE", strict_mode)
        config.STRICT_MODE = True

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendSupportsTrailingCommaRelaxationsParity(self):
        larkParser = parserFactory(
            backend="lark",
            commaAtTheEndOfImport=True,
            commaAtTheEndOfSequence=True,
        )
        plyParser = parserFactory(
            commaAtTheEndOfImport=True,
            commaAtTheEndOfSequence=True,
        )

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        IMPORTS
          OBJECT-TYPE,
            FROM SNMPv2-SMI;

        TestEntry ::= SEQUENCE {
          testIndex INTEGER,
        }

        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendRejectsTrailingCommaWithoutOption(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        IMPORTS
          OBJECT-TYPE,
            FROM SNMPv2-SMI;

        TestEntry ::= SEQUENCE {
          testIndex INTEGER,
        }

        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testLarkBackendSupportsSmiV1KeywordsAndIndexParity(self):
        larkParser = parserFactory(
            backend="lark", supportSmiV1Keywords=True, supportIndex=True
        )
        plyParser = parserFactory(supportSmiV1Keywords=True, supportIndex=True)

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testTable OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "table"
            INDEX { INTEGER, OCTET STRING, IpAddress, NetworkAddress }
         ::= { 1 1 }

        MyNet ::= NetworkAddress
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendRejectsSmiV1IndexWithoutOption(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testTable OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "table"
            INDEX { INTEGER }
         ::= { 1 1 }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

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

    def testLarkBackendTypeDeclarationParityWithPly(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyInt ::= INTEGER (0..10|20)
        MyEnum ::= INTEGER { one(1), two(2) }
        MyBits ::= BITS { one(1), two(2) }
        MyIp ::= IpAddress (0..255)
        MyCounter ::= Counter32
        MyOidType ::= OBJECT IDENTIFIER
        MyTc ::= TEXTUAL-CONVENTION
            DISPLAY-HINT "1x:"
            STATUS current
            DESCRIPTION "desc"
            REFERENCE "rfc"
            SYNTAX OCTET STRING (SIZE (1..255))
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendTypeDeclarationTcWithoutOptionalParts(self):
        SmiParser = parserFactory(backend="lark")

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                SmiParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyTc ::= TEXTUAL-CONVENTION
            STATUS current
            DESCRIPTION "desc"
            SYNTAX INTEGER (0..10)
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
                            "typeDeclaration",
                            "MyTc",
                            (
                                "typeDeclarationRHS",
                                None,
                                ("Status", "current"),
                                ("DESCRIPTION", "desc"),
                                None,
                                (
                                    "SimpleSyntax",
                                    "INTEGER",
                                    ("integerSubType", [(0, 10)]),
                                ),
                            ),
                        )
                    ],
                )
            ],
        )

    def testLarkBackendObjectTypeParityWithPly(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        idx OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "idx"
         ::= { 1 1 }

        entry OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "entry"
         ::= { 1 2 }

        testObjectType OBJECT-TYPE
            SYNTAX Integer32
            UNITS "seconds"
            ACCESS read-only
            STATUS current
            DESCRIPTION "Test object"
            REFERENCE "ABC"
            AUGMENTS { entry }
            INDEX { idx, IMPLIED idx }
            DEFVAL { 5 }
         ::= { 1 3 }

        testBits OBJECT-TYPE
            SYNTAX BITS { one(1), two(2) }
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "bits"
            DEFVAL { { one, two } }
         ::= { 1 4 }

        testHex OBJECT-TYPE
            SYNTAX OCTET STRING
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "hex"
            DEFVAL { '0A'H }
         ::= { 1 5 }

        testQuoted OBJECT-TYPE
            SYNTAX OCTET STRING
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "quoted"
            DEFVAL { "abc" }
         ::= { 1 6 }
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendTableSyntaxParityWithPly(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testTable OBJECT-TYPE
            SYNTAX SEQUENCE OF TestEntry
            MAX-ACCESS not-accessible
            STATUS current
            DESCRIPTION "table"
         ::= { 1 1 }

        testEntry OBJECT-TYPE
            SYNTAX TestEntry
            MAX-ACCESS not-accessible
            STATUS current
            DESCRIPTION "row"
            INDEX { testIndex }
         ::= { testTable 1 }

        TestEntry ::= SEQUENCE {
            testIndex INTEGER,
            testName OCTET STRING,
            testIp IpAddress,
            testBits BITS
        }

        testIndex OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "index"
         ::= { testEntry 1 }
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendComplianceAndNotificationParityWithPly(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testModule MODULE-IDENTITY
         LAST-UPDATED "200001100000Z"
         ORGANIZATION "Org"
         CONTACT-INFO "Contact"
         DESCRIPTION "Desc"
         REVISION "200001100000Z"
         DESCRIPTION "Rev desc"
         ::= { 1 10 }

        testNotificationType NOTIFICATION-TYPE
         OBJECTS { testObj1, testObj2 }
         STATUS current
         DESCRIPTION "Notification"
         REFERENCE "nref"
         ::= { 1 11 }

        testObjectGroup OBJECT-GROUP
         OBJECTS { testObj1, testObj2 }
         STATUS current
         DESCRIPTION "Object group"
         REFERENCE "oref"
         ::= { 1 12 }

        testNotificationGroup NOTIFICATION-GROUP
         NOTIFICATIONS { testNotificationType }
         STATUS current
         DESCRIPTION "Notification group"
         REFERENCE "gref"
         ::= { 1 13 }

        testCompliance MODULE-COMPLIANCE
         STATUS current
         DESCRIPTION "Compliance"
         REFERENCE "cref"
         MODULE
          MANDATORY-GROUPS { testObjectGroup }
          GROUP testNotificationGroup
          DESCRIPTION "optional"
         ::= { 1 14 }
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))

    def testLarkBackendTrapAndAgentCapabilitiesParityWithPly(self):
        larkParser = parserFactory(backend="lark")
        plyParser = parserFactory()

        if importlib.util.find_spec("lark") is None:
            with self.assertRaises(error.PySmiError):
                larkParser()
            return

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testId OBJECT IDENTIFIER ::= { 1 3 }

        testObject OBJECT-TYPE
            SYNTAX Integer32
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "Test object"
         ::= { 1 4 }

        testTrap TRAP-TYPE
            ENTERPRISE testId
            VARIABLES { testObject }
            DESCRIPTION "Test trap"
            REFERENCE "Trap ref"
         ::= 1

        testCapability AGENT-CAPABILITIES
            PRODUCT-RELEASE "Test product"
            STATUS current
            DESCRIPTION "test capabilities"
            REFERENCE "test reference"
            SUPPORTS TEST-MIB
            INCLUDES { testSystemGroup }
            VARIATION testSysLevelType
            ACCESS read-only
            DESCRIPTION "Not supported."
         ::= { 1 5 }
        END
        """

        self.assertEqual(larkParser().parse(mib), plyParser().parse(mib))
