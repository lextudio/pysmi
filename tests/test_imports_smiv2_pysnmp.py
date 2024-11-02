#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys
import unittest

from pysmi import error
from pysmi.parser.smi import parserFactory
from pysmi.codegen.pysnmp import PySnmpCodeGen
from pysmi.codegen.symtable import SymtableCodeGen
from pysmi.reader import CallbackReader
from pysmi.searcher import StubSearcher
from pysmi.writer import CallbackWriter
from pysmi.parser import SmiStarParser
from pysmi.compiler import MibCompiler
from pyasn1.type.namedval import NamedValues
from pysnmp.smi.builder import MibBuilder


class ImportClauseTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
     MODULE-IDENTITY, OBJECT-TYPE, Unsigned32, mib-2
        FROM SNMPv2-SMI
     SnmpAdminString
        FROM SNMP-FRAMEWORK-MIB;


    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

    def testModuleImportsRequiredMibs(self):
        self.assertEqual(
            self.mibInfo.imported,
            ("SNMP-FRAMEWORK-MIB", "SNMPv2-CONF", "SNMPv2-SMI", "SNMPv2-TC"),
            "imported MIBs not reported",
        )

    def testModuleCheckImportedSymbol(self):
        self.assertTrue("SnmpAdminString" in self.ctx, "imported symbol not present")


class ImportValueTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      importedValue1, imported-value-2, global
        FROM IMPORTED-MIB;

    testValue1    OBJECT IDENTIFIER ::= { importedValue1 6 }
    test-value-2  OBJECT IDENTIFIER ::= { imported-value-2 7 }
    if            OBJECT IDENTIFIER ::= { global 8 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    importedValue1    OBJECT IDENTIFIER ::= { 1 3 }
    imported-value-2  OBJECT IDENTIFIER ::= { 1 4 }
    global            OBJECT IDENTIFIER ::= { 1 5 }

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testValueDeclarationName1(self):
        self.assertEqual(self.ctx["testValue1"].getName(), (1, 3, 6), "bad value")

    def testValueDeclarationLabel1(self):
        self.assertEqual(self.ctx["testValue1"].getLabel(), "testValue1", "bad label")

    def testValueDeclarationName2(self):
        self.assertEqual(self.ctx["test_value_2"].getName(), (1, 4, 7), "bad value")

    def testValueDeclarationLabel2(self):
        self.assertEqual(
            self.ctx["test_value_2"].getLabel(), "test-value-2", "bad label"
        )

    def testValueDeclarationNameReservedKeyword(self):
        self.assertEqual(self.ctx["_pysmi_if"].getName(), (1, 5, 8), "bad value")

    def testValueDeclarationLabelReservedKeyword(self):
        self.assertEqual(self.ctx["_pysmi_if"].getLabel(), "if", "bad label")


# Note that the following test case relies on leniency with respect to deriving
# textual conventions from other textual conventions, which is disallowed per
# RFC 2579 Sec. 3.5, but widely used in the real world.
class ImportTypeTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC
      ImportedType1,
      Imported-Type-2,
      True,
      ImportedType3
        FROM IMPORTED-MIB;

    testObject1 OBJECT-TYPE
        SYNTAX      ImportedType1
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { '01020304'H }
      ::= { 1 3 }

    Test-Type-2 ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "1x:"
        STATUS       current
        DESCRIPTION  "Test TC with display hint"
        SYNTAX       Imported-Type-2

    test-object-2 OBJECT-TYPE
        SYNTAX      Test-Type-2
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { 'aabbccdd'H }
      ::= { 1 4 }

    False ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "2x:"
        STATUS       current
        DESCRIPTION  "Test TC with display hint"
        SYNTAX       True

    global OBJECT-TYPE
        SYNTAX      True
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 5 }

    if OBJECT-TYPE
        SYNTAX      False
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 6 }

    TestType3 ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "2d:"
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       ImportedType3

    testObject3 OBJECT-TYPE
        SYNTAX      TestType3
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { '000100020003'H }
      ::= { 1 7 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    ImportedType1 ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "1d:"
        STATUS       current
        DESCRIPTION  "Test TC with display hint"
        SYNTAX       OCTET STRING

    Imported-Type-2 ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       OCTET STRING

    True ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       OCTET STRING

    ImportedType3 ::= OCTET STRING

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeName1(self):
        self.assertEqual(self.ctx["testObject1"].getName(), (1, 3), "bad value")

    def testObjectTypeLabel1(self):
        self.assertEqual(self.ctx["testObject1"].getLabel(), "testObject1", "bad label")

    def testObjectTypeDisplayHint1(self):
        self.assertEqual(
            self.ctx["testObject1"].getSyntax().getDisplayHint(),
            "1d:",
            "bad display hint",
        )

    def testObjectTypePrettyValue1(self):
        self.assertEqual(
            self.ctx["testObject1"].getSyntax().prettyPrint(), "1:2:3:4", "bad defval"
        )

    def testObjectTypeName2(self):
        self.assertEqual(self.ctx["test_object_2"].getName(), (1, 4), "bad value")

    def testObjectTypeLabel2(self):
        self.assertEqual(
            self.ctx["test_object_2"].getLabel(), "test-object-2", "bad label"
        )

    def testObjectTypeDisplayHint2(self):
        self.assertEqual(
            self.ctx["test_object_2"].getSyntax().getDisplayHint(),
            "1x:",
            "bad display hint",
        )

    def testObjectTypePrettyValue2(self):
        self.assertEqual(
            self.ctx["test_object_2"].getSyntax().prettyPrint(),
            "aa:bb:cc:dd",
            "bad defval",
        )

    def testObjectTypeNameReservedKeyword1(self):
        self.assertEqual(self.ctx["_pysmi_global"].getName(), (1, 5), "bad value")

    def testObjectTypeLabelReservedKeyword1(self):
        self.assertEqual(self.ctx["_pysmi_global"].getLabel(), "global", "bad label")

    def testObjectTypeDisplayHintReservedKeyword1(self):
        self.assertEqual(
            self.ctx["_pysmi_global"].getSyntax().getDisplayHint(),
            "",
            "bad display hint",
        )

    def testObjectTypeNameReservedKeyword2(self):
        self.assertEqual(self.ctx["_pysmi_if"].getName(), (1, 6), "bad value")

    def testObjectTypeLabelReservedKeyword2(self):
        self.assertEqual(self.ctx["_pysmi_if"].getLabel(), "if", "bad label")

    def testObjectTypeDisplayHintReservedKeyword2(self):
        self.assertEqual(
            self.ctx["_pysmi_if"].getSyntax().getDisplayHint(),
            "2x:",
            "bad display hint",
        )

    def testObjectTypeName3(self):
        self.assertEqual(self.ctx["testObject3"].getName(), (1, 7), "bad value")

    def testObjectTypeLabel3(self):
        self.assertEqual(self.ctx["testObject3"].getLabel(), "testObject3", "bad label")

    def testObjectTypeDisplayHint3(self):
        self.assertEqual(
            self.ctx["testObject3"].getSyntax().getDisplayHint(),
            "2d:",
            "bad display hint",
        )

    def testObjectTypePrettyValue3(self):
        self.assertEqual(
            self.ctx["testObject3"].getSyntax().prettyPrint(), "1:2:3", "bad defval"
        )


class ImportTCEnumUsedByDefvalTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      ImportedType
        FROM IMPORTED-MIB;

    testObject OBJECT-TYPE
        SYNTAX       ImportedType
        MAX-ACCESS   read-write
        STATUS       current
        DESCRIPTION  "Test object"
        DEFVAL       { enabled }
      ::= { 1 4 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    ImportedType ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       INTEGER { enabled(1), disabled(2) }

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeNamedValues(self):
        self.assertEqual(
            self.ctx["testObject"].getSyntax().namedValues,
            NamedValues(("enabled", 1), ("disabled", 2)),
            "bad NAMED VALUES",
        )

    def testObjectTypeSyntax(self):
        self.assertEqual(self.ctx["testObject"].getSyntax(), 1, "bad DEFVAL")


class ImportObjectsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE, NOTIFICATION-TYPE
        FROM SNMPv2-SMI
      OBJECT-GROUP, NOTIFICATION-GROUP, MODULE-COMPLIANCE
        FROM SNMPv2-CONF
      -- For the purpose of this test, the types of these symbols do not matter.
      importedValue1, imported-value-2, global
        FROM IMPORTED-MIB;

    testNotificationType NOTIFICATION-TYPE
        OBJECTS         {
                            importedValue1,
                            imported-value-2,
                            global
                        }
        STATUS          current
        DESCRIPTION     "A collection of test notification types."
      ::= { 1 6 }

    testObjectGroup OBJECT-GROUP
        OBJECTS         {
                            importedValue1,
                            imported-value-2,
                            global
                        }
        STATUS          current
        DESCRIPTION     "A collection of test objects."
      ::= { 1 7 }

    testNotificationGroup NOTIFICATION-GROUP
        NOTIFICATIONS   {
                            importedValue1,
                            imported-value-2,
                            global
                        }
        STATUS          current
        DESCRIPTION     "A collection of test notifications."
      ::= { 1 8 }

    testModuleCompliance MODULE-COMPLIANCE
        STATUS        current
        DESCRIPTION   "This is the MIB compliance statement"
        MODULE        IMPORTED-MIB
        MANDATORY-GROUPS {
            importedValue1,
            imported-value-2,
            nonexistentValue
        }
        GROUP        global
        DESCRIPTION  "Support for these notifications is optional."
      ::= { 1 9 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN

    importedValue1    OBJECT IDENTIFIER ::= { 1 3 }
    imported-value-2  OBJECT IDENTIFIER ::= { 1 4 }
    global            OBJECT IDENTIFIER ::= { 1 5 }  -- a reserved Python keyword

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testNotificationTypeObjects(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getObjects(),
            (
                ("IMPORTED-MIB", "importedValue1"),
                ("IMPORTED-MIB", "imported-value-2"),
                ("IMPORTED-MIB", "global"),
            ),
            "bad OBJECTS",
        )

    def testObjectGroupObjects(self):
        self.assertEqual(
            self.ctx["testObjectGroup"].getObjects(),
            (
                ("IMPORTED-MIB", "importedValue1"),
                ("IMPORTED-MIB", "imported-value-2"),
                ("IMPORTED-MIB", "global"),
            ),
            "bad OBJECTS",
        )

    def testNotificationGroupObjects(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getObjects(),
            (
                ("IMPORTED-MIB", "importedValue1"),
                ("IMPORTED-MIB", "imported-value-2"),
                ("IMPORTED-MIB", "global"),
            ),
            "bad OBJECTS",
        )

    def testModuleComplianceObjects(self):
        self.assertEqual(
            self.ctx["testModuleCompliance"].getObjects(),
            (
                ("IMPORTED-MIB", "importedValue1"),
                ("IMPORTED-MIB", "imported-value-2"),
                # Even if the referenced MIB does not export the value, the
                # resulting object must still consist of the correct MIB and
                # object name.
                ("IMPORTED-MIB", "nonexistentValue"),
                ("IMPORTED-MIB", "global"),
            ),
            "bad OBJECTS",
        )


class ImportObjectIdentifierDefaultTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      importedValue1, imported-value-2, global
        FROM IMPORTED-MIB;

    testObject1 OBJECT-TYPE
        SYNTAX      OBJECT IDENTIFIER
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { importedValue1 }
      ::= { 1 6 }

    testObject2 OBJECT-TYPE
        SYNTAX      OBJECT IDENTIFIER
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { imported-value-2 }
      ::= { 1 7 }

    testObject3 OBJECT-TYPE
        SYNTAX      OBJECT IDENTIFIER
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { global }
      ::= { 1 8 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN

    importedValue1    OBJECT IDENTIFIER ::= { 1 3 }
    imported-value-2  OBJECT IDENTIFIER ::= { 1 4 }
    global            OBJECT IDENTIFIER ::= { 1 5 }  -- a reserved Python keyword

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeSyntax1(self):
        self.assertEqual(
            self.ctx["testObject1"].getSyntax(),
            (1, 3),
            "bad DEFVAL",
        )

    def testObjectTypeSyntax2(self):
        self.assertEqual(
            self.ctx["testObject2"].getSyntax(),
            (1, 4),
            "bad DEFVAL",
        )

    def testObjectTypeSyntax3(self):
        self.assertEqual(
            self.ctx["testObject3"].getSyntax(),
            (1, 5),
            "bad DEFVAL",
        )


class ImportMibTableHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      test-entry, testIndex1, test-index-2, global
        FROM IMPORTED-MIB;

    --
    -- Augmentation
    --

    testTableAug OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntryAug
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test table"
      ::= { 1 4 }

    test-entry-aug OBJECT-TYPE
        SYNTAX          TestEntryAug
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test row"
        AUGMENTS        { test-entry }
      ::= { testTableAug 1 }

    TestEntryAug ::= SEQUENCE {
        testIndexAug    INTEGER
    }

    testIndexAug OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      read-create
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { test-entry-aug 1 }

    --
    -- External indices
    --

    testTableExt OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntryExt
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test table"
      ::= { 1 5 }

    testEntryExt OBJECT-TYPE
        SYNTAX          TestEntryExt
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test row"
        INDEX           { testIndex1, test-index-2, global }
      ::= { testTableExt 1 }

    TestEntryExt ::= SEQUENCE {
        testColumn      OCTET STRING
    }

    testColumn OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-create
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { testEntryExt 1 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testTable OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntry
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test table"
      ::= { 1 3 }

    test-entry OBJECT-TYPE
        SYNTAX          TestEntry
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test row"
        INDEX           { testIndex1, test-index-2, global }
      ::= { testTable 1 }

    TestEntry ::= SEQUENCE {
        testIndex1      INTEGER,
        test-index-2    INTEGER,
        global          OCTET STRING,
        testColumn      INTEGER
    }

    testIndex1 OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { test-entry 1 }

    test-index-2 OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { test-entry 2 }

    global OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      not-accessible
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { test-entry 3 }

    testColumn OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      read-write
        STATUS          current
        DESCRIPTION     "Test column"
      ::= { test-entry 4 }

    END
    """

    def setUp(self):
        self.ctx = {"mibBuilder": MibBuilder()}
        symbolTable = {}

        for mibData in (self.IMPORTED_MIB, self.__class__.__doc__):
            ast = parserFactory()().parse(mibData)[0]
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})

            symbolTable[mibInfo.name] = symtable

            mibInfo, pycode = PySnmpCodeGen().gen_code(ast, dict(symbolTable))
            codeobj = compile(pycode, "test", "exec")
            exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeTableRowAugmentation(self):
        # TODO: provide getAugmentation() method
        try:
            augmentingRows = self.ctx["test_entry"].augmentingRows

        except AttributeError:
            augmentingRows = self.ctx["test_entry"]._augmentingRows

        self.assertEqual(
            list(augmentingRows)[0],
            ("TEST-MIB", "test-entry-aug"),
            "bad AUGMENTS table clause",
        )

    def testObjectTypeTableAugRowIndex(self):
        self.assertEqual(
            self.ctx["test_entry_aug"].getIndexNames(),
            (
                (0, "IMPORTED-MIB", "testIndex1"),
                (0, "IMPORTED-MIB", "test-index-2"),
                (0, "IMPORTED-MIB", "global"),
            ),
            "bad table indices",
        )

    def testObjectTypeTableExtRowIndex(self):
        self.assertEqual(
            self.ctx["testEntryExt"].getIndexNames(),
            (
                (0, "IMPORTED-MIB", "testIndex1"),
                (0, "IMPORTED-MIB", "test-index-2"),
                (0, "IMPORTED-MIB", "global"),
            ),
            "bad table indices",
        )


class ImportSelfTestCase(unittest.TestCase):
    """
    Test-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      someObject
        FROM TEST-MIB;

    END
    """

    def setUp(self):
        self.mibCompiler = MibCompiler(
            SmiStarParser(), PySnmpCodeGen(), CallbackWriter(lambda m, d, c: None)
        )

        self.testMibLoaded = False

        def getMibData(mibname, context):
            if mibname in PySnmpCodeGen.baseMibs:
                return f"{mibname} DEFINITIONS ::= BEGIN\nEND"

            self.assertEqual(mibname, "TEST-MIB", f"unexpected MIB name {mibname}")
            self.assertFalse(self.testMibLoaded, "TEST-MIB was loaded more than once")
            self.testMibLoaded = True
            return self.__class__.__doc__

        self.mibCompiler.add_sources(CallbackReader(getMibData))
        self.mibCompiler.add_searchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    def testCompilerCycleDetection(self):
        results = self.mibCompiler.compile("TEST-MIB", noDeps=True)

        self.assertTrue(self.testMibLoaded, "TEST-MIB was not loaded at all")
        self.assertEqual(results["Test-MIB"], "compiled", "Test-MIB was not compiled")


class ImportCycleTestCase(unittest.TestCase):
    """
    Test-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      someObject
        FROM OTHER-MIB;

    END
    """

    OTHER_MIB = """
    Other-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      otherObject
        FROM TEST-MIB;

    END
    """

    def setUp(self):
        self.mibCompiler = MibCompiler(
            SmiStarParser(), PySnmpCodeGen(), CallbackWriter(lambda m, d, c: None)
        )

        self.testMibLoaded = 0
        self.otherMibLoaded = 0

        def getMibData(mibname, context):
            if mibname in PySnmpCodeGen.baseMibs:
                return f"{mibname} DEFINITIONS ::= BEGIN\nEND"

            if mibname == "OTHER-MIB":
                self.assertFalse(
                    self.otherMibLoaded, "OTHER-MIB was loaded more than once"
                )
                self.otherMibLoaded = True
                return self.OTHER_MIB
            else:
                self.assertEqual(mibname, "TEST-MIB", f"unexpected MIB name {mibname}")
                self.assertFalse(
                    self.testMibLoaded, "TEST-MIB was loaded more than once"
                )
                self.testMibLoaded = True
                return self.__class__.__doc__

        self.mibCompiler.add_sources(CallbackReader(getMibData))
        self.mibCompiler.add_searchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    def testCompilerCycleDetection(self):
        results = self.mibCompiler.compile("TEST-MIB", noDeps=False)

        self.assertTrue(self.testMibLoaded, "TEST-MIB was not loaded at all")
        self.assertTrue(self.otherMibLoaded, "OTHER-MIB was not loaded at all")

        self.assertEqual(results["Test-MIB"], "compiled", "Test-MIB was not compiled")
        self.assertEqual(results["Other-MIB"], "compiled", "Other-MIB was not compiled")


class ImportMissingTestCase(unittest.TestCase):
    """
    Test-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      someObject
        FROM OTHER-MIB;

    END
    """

    def setUp(self):
        self.mibCompiler = MibCompiler(
            SmiStarParser(), PySnmpCodeGen(), CallbackWriter(lambda m, d, c: None)
        )

        self.testMibLoaded = False

        def getMibData(mibname, context):
            if mibname in PySnmpCodeGen.baseMibs:
                return f"{mibname} DEFINITIONS ::= BEGIN\nEND"

            if mibname == "OTHER-MIB":
                raise error.PySmiReaderFileNotFoundError(
                    f"source MIB {mibname} not found", reader=self
                )
            else:
                self.assertEqual(mibname, "TEST-MIB", f"unexpected MIB name {mibname}")
                self.assertFalse(
                    self.testMibLoaded, "TEST-MIB was loaded more than once"
                )
                self.testMibLoaded = True
                return self.__class__.__doc__

        self.mibCompiler.add_sources(CallbackReader(getMibData))
        self.mibCompiler.add_searchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    def testMissingImports(self):
        results = self.mibCompiler.compile("TEST-MIB", noDeps=False)
        # TODO: this test case is invalid right now, as the accurate error reported should point out that OTHER-MIB is missing.
        self.assertEqual(
            results["Test-MIB"], "unprocessed", "Test-MIB was not marked as missing"
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
