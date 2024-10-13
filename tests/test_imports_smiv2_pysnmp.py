#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from pysmi.parser.smi import parserFactory
from pysmi.codegen.pysnmp import PySnmpCodeGen
from pysmi.codegen.symtable import SymtableCodeGen
from pysmi.reader import CallbackReader
from pysmi.searcher import StubSearcher
from pysmi.writer import CallbackWriter
from pysmi.parser import SmiStarParser
from pysmi.compiler import MibCompiler
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
      ImportedType1, Imported-Type-2, True
        FROM IMPORTED-MIB;

    testObject1 OBJECT-TYPE
        SYNTAX      ImportedType1
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
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
        DISPLAY-HINT "255a"
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
            "255a",
            "bad display hint",
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


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
