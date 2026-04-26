import unittest

from pysmi import config, error
from pysmi.lexer.smi import lexerFactory
from pysmi.parser.smi import parserFactory


class ParserBackendTestCase(unittest.TestCase):
    SIMPLE_MIB = """
    TEST-MIB DEFINITIONS ::= BEGIN
    END
    """

    def testUnknownBackend(self):
        with self.assertRaises(error.PySmiError):
            parserFactory(backend="nope")

    def testPlyBackendDisconnected(self):
        with self.assertRaises(error.PySmiError):
            parserFactory(backend="ply")

    def testPlyLexerDisconnected(self):
        with self.assertRaises(error.PySmiError):
            lexerFactory()

    def testParserBootstrap(self):
        SmiParser = parserFactory()

        ast = SmiParser().parse(self.SIMPLE_MIB)
        self.assertEqual(ast, [("TEST-MIB", None, {}, None)])

    def testParserSupportsMixOfCommasAndSpacesParity(self):
        parser = parserFactory(mixOfCommasAndSpaces=True)
        defaultParser = parserFactory(mixOfCommasAndSpaces=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { one(1), two(2) three(3), }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsEnumCommaSpaceMixWithoutOption(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { one(1) two(2) }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testParserStrictModeInvalidBinaryStringParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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
            parser().parse(mib)
        with self.assertRaises(error.PySmiLexerError):
            defaultParser().parse(mib)

    def testParserStrictModeHexStringParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserMacroClauseParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        OBJECT-TYPE MACRO ::= BEGIN
            TYPE NOTATION ::= "SYNTAX" Syntax
            VALUE NOTATION ::= value (VALUE OBJECT IDENTIFIER)
        END
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserChoiceClauseParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyChoice ::= CHOICE {
            one INTEGER
        }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserSubtypeHexBinaryRangeParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testObjectType OBJECT-TYPE
            SYNTAX Integer32 ('02'H..'03'H | '00000001'B)
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "Test object"
         ::= { 1 3 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserInvalidNestedOidDefvalParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testObjectType OBJECT-TYPE
            SYNTAX OBJECT IDENTIFIER
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "Test object"
            DEFVAL { { 0 0 } }
         ::= { 1 3 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserGaugeAliasAndTrapOptionalPartsParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        IMPORTS
          Gauge
            FROM RFC1155-SMI
          TRAP-TYPE
            FROM RFC-1215;

        testObjectType OBJECT-TYPE
            SYNTAX Gauge
            ACCESS read-only
            STATUS mandatory
            DESCRIPTION "Test object"
         ::= { 1 3 }

        trapBase OBJECT IDENTIFIER ::= { 1 6 }

        testTrap TRAP-TYPE
            ENTERPRISE trapBase
         ::= 2
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserExportsSkipParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        EXPORTS
          OBJECT-TYPE, MODULE-IDENTITY, testValue;

        testValue OBJECT IDENTIFIER ::= { 1 3 6 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTaggedSyntaxParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testObjectType OBJECT-TYPE
            SYNTAX [APPLICATION 0] IMPLICIT INTEGER (0..10)
            MAX-ACCESS read-only
            STATUS current
            DESCRIPTION "Test object"
         ::= { 1 3 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTypeNameSmiKeywordsParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        Integer32 ::= INTEGER (0..10)
        Counter32 ::= INTEGER (0..10)
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTypeNameNetworkAddressParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        NetworkAddress ::= OCTET STRING
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRhsNetworkAddressParityWithAndWithoutOption(self):
        parserDefault = parserFactory()
        defaultDefault = parserFactory()
        parserRelaxed = parserFactory(supportSmiV1Keywords=True)
        defaultRelaxed = parserFactory(supportSmiV1Keywords=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyNet ::= NetworkAddress
        END
        """

        self.assertEqual(parserDefault().parse(mib), defaultDefault().parse(mib))
        self.assertEqual(parserRelaxed().parse(mib), defaultRelaxed().parse(mib))

    def testParserSupportsTrailingCommaRelaxationsParity(self):
        parser = parserFactory(
            commaAtTheEndOfImport=True,
            commaAtTheEndOfSequence=True,
        )
        defaultParser = parserFactory(
            commaAtTheEndOfImport=True,
            commaAtTheEndOfSequence=True,
        )

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsTrailingCommaWithoutOption(self):
        SmiParser = parserFactory()

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

    def testParserSupportsSmiV1KeywordsAndIndexParity(self):
        parser = parserFactory(supportSmiV1Keywords=True, supportIndex=True)
        defaultParser = parserFactory(supportSmiV1Keywords=True, supportIndex=True)

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsSmiV1IndexWithoutOption(self):
        SmiParser = parserFactory()

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

    def testParserSupportsUppercaseIdentifierParity(self):
        parser = parserFactory(uppercaseIdentifier=True)
        defaultParser = parserFactory(uppercaseIdentifier=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { ONE(1), TWO(2) }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsUppercaseIdentifierWithoutOption(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        MyEnum ::= INTEGER { ONE(1) }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testParserSupportsLowcaseIdentifierParity(self):
        parser = parserFactory(lowcaseIdentifier=True)
        defaultParser = parserFactory(lowcaseIdentifier=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        TestNotification NOTIFICATION-TYPE
            STATUS current
            DESCRIPTION "Notification"
         ::= { 1 11 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsLowcaseIdentifierWithoutOption(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        TestNotification NOTIFICATION-TYPE
            STATUS current
            DESCRIPTION "Notification"
         ::= { 1 11 }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testParserSupportsBracedEnterpriseTrapParity(self):
        parser = parserFactory(curlyBracesAroundEnterpriseInTrap=True)
        defaultParser = parserFactory(curlyBracesAroundEnterpriseInTrap=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        trapBase OBJECT IDENTIFIER ::= { 1 6 }

        testTrap TRAP-TYPE
            ENTERPRISE { trapBase }
         ::= 1
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsBracedEnterpriseTrapWithoutOption(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        trapBase OBJECT IDENTIFIER ::= { 1 6 }

        testTrap TRAP-TYPE
            ENTERPRISE { trapBase }
         ::= 1
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testParserSupportsNoCellsParity(self):
        parser = parserFactory(noCells=True)
        defaultParser = parserFactory(noCells=True)

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testCapability AGENT-CAPABILITIES
            PRODUCT-RELEASE "Test product"
            STATUS current
            DESCRIPTION "test capabilities"
            SUPPORTS TEST-MIB
            INCLUDES { testGroup }
            VARIATION testObj
            CREATION-REQUIRES { }
            DESCRIPTION "Not supported."
         ::= { 1 5 }
        END
        """

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserRejectsNoCellsWithoutOption(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        testCapability AGENT-CAPABILITIES
            PRODUCT-RELEASE "Test product"
            STATUS current
            DESCRIPTION "test capabilities"
            SUPPORTS TEST-MIB
            INCLUDES { testGroup }
            VARIATION testObj
            CREATION-REQUIRES { }
            DESCRIPTION "Not supported."
         ::= { 1 5 }
        END
        """

        with self.assertRaises(error.PySmiParserError):
            SmiParser().parse(mib)

    def testParserParsesImportsAndValueDeclaration(self):
        SmiParser = parserFactory()

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

    def testParserForbiddenUppercaseIdentifier(self):
        SmiParser = parserFactory()

        mib = """
        TEST-MIB DEFINITIONS ::= BEGIN
        TRUE OBJECT IDENTIFIER ::= { 1 3 6 }
        END
        """

        with self.assertRaises(error.PySmiLexerError):
            SmiParser().parse(mib)

    def testParserParsesObjectIdentityClause(self):
        SmiParser = parserFactory()

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

    def testParserParsesObjectIdentityClauseWithReference(self):
        SmiParser = parserFactory()

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

    def testParserTypeDeclarationParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTypeDeclarationTcWithoutOptionalParts(self):
        SmiParser = parserFactory()

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

    def testParserObjectTypeParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTableSyntaxParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserComplianceAndNotificationParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))

    def testParserTrapAndAgentCapabilitiesParity(self):
        parser = parserFactory()
        defaultParser = parserFactory()

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

        self.assertEqual(parser().parse(mib), defaultParser().parse(mib))
