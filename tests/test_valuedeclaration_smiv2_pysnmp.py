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
from pysnmp.smi.builder import MibBuilder


class ValueDeclarationTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS

      OBJECT-TYPE
        FROM SNMPv2-SMI;

    -- simple values

    testValue1    OBJECT IDENTIFIER ::= { 1 }
    testValue2    OBJECT IDENTIFIER ::= { testValue1 3 }
    testValue3    OBJECT IDENTIFIER ::= { 1 3 6 1 2 }
    test-value-4  OBJECT IDENTIFIER ::= { 1 4 }
    global        OBJECT IDENTIFIER ::= { 1 5 }
    if            OBJECT IDENTIFIER ::= { global 2 }

    -- testValue01  INTEGER ::= 123
    -- testValue02  INTEGER ::= -123
    -- testValue04  OCTET STRING ::= h'test string'
    -- testValue05  INTEGER ::= testValue01
    -- testValue06  OCTET STRING ::= "test string"
    -- testValue07  OCTET STRING ::= b'010101'

    -- application syntax

    -- testValue03  Integer32 ::= 123
    -- testValue03  Counter32 ::= 123
    -- testValue03  Gauge32 ::= 123
    -- testValue03  Unsigned32 ::= 123
    -- testValue03  TimeTicks ::= 123
    -- testValue03  Opaque ::= "0123"
    -- testValue03  Counter64 ::= 123456789123456789
    -- testValue03  IpAddress ::= "127.0.0.1"

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

    def testValueDeclarationSymbol(self):
        self.assertTrue(
            "testValue1" in self.ctx
            and "testValue2" in self.ctx
            and "testValue3" in self.ctx,
            "symbol not present",
        )

    def testValueDeclarationName1(self):
        self.assertEqual(self.ctx["testValue1"].getName(), (1,), "bad value")

    def testValueDeclarationName2(self):
        self.assertEqual(self.ctx["testValue2"].getName(), (1, 3), "bad value")

    def testValueDeclarationName3(self):
        self.assertEqual(self.ctx["testValue3"].getName(), (1, 3, 6, 1, 2), "bad value")

    def testValueDeclarationLabel3(self):
        self.assertEqual(self.ctx["testValue3"].getLabel(), "testValue3", "bad label")

    def testValueDeclarationName4(self):
        self.assertEqual(self.ctx["test_value_4"].getName(), (1, 4), "bad value")

    def testValueDeclarationLabel4(self):
        self.assertEqual(
            self.ctx["test_value_4"].getLabel(), "test-value-4", "bad label"
        )

    def testValueDeclarationNameReservedKeyword(self):
        self.assertEqual(self.ctx["_pysmi_global"].getName(), (1, 5), "bad value")

    def testValueDeclarationLabelReservedKeyword(self):
        self.assertEqual(self.ctx["_pysmi_global"].getLabel(), "global", "bad label")

    def testValueDeclarationNameReservedKeyword2(self):
        self.assertEqual(self.ctx["_pysmi_if"].getName(), (1, 5, 2), "bad value")

    def testValueDeclarationLabelReservedKeyword2(self):
        self.assertEqual(self.ctx["_pysmi_if"].getLabel(), "if", "bad label")


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
