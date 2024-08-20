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
        mibInfo, symtable = SymtableCodeGen().genCode(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().genCode(
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

        self.mibCompiler.addSources(CallbackReader(getMibData))
        self.mibCompiler.addSearchers(StubSearcher(*PySnmpCodeGen.baseMibs))

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

        self.mibCompiler.addSources(CallbackReader(getMibData))
        self.mibCompiler.addSearchers(StubSearcher(*PySnmpCodeGen.baseMibs))

    def testCompilerCycleDetection(self):
        results = self.mibCompiler.compile("TEST-MIB", noDeps=False)

        self.assertTrue(self.testMibLoaded, "TEST-MIB was not loaded at all")
        self.assertTrue(self.otherMibLoaded, "OTHER-MIB was not loaded at all")

        self.assertEqual(results["Test-MIB"], "compiled", "Test-MIB was not compiled")
        self.assertEqual(results["Other-MIB"], "compiled", "Other-MIB was not compiled")


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
