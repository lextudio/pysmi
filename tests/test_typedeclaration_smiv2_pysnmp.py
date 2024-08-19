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
from pysnmp.smi.view import MibViewController


class TypeDeclarationTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS

      IpAddress,
      Counter32,
      Gauge32,
      TimeTicks,
      Opaque,
      Integer32,
      Unsigned32,
      Counter64
        FROM SNMPv2-SMI

      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    -- simple types
    TestTypeInteger ::= INTEGER
    TestTypeOctetString ::= OCTET STRING
    TestTypeObjectIdentifier ::= OBJECT IDENTIFIER

    -- application types
    TestTypeIpAddress ::= IpAddress
    TestTypeInteger32 ::= Integer32
    TestTypeCounter32 ::= Counter32
    TestTypeGauge32 ::= Gauge32
    TestTypeTimeTicks ::= TimeTicks
    TestTypeOpaque ::= Opaque
    TestTypeCounter64 ::= Counter64
    TestTypeUnsigned32 ::= Unsigned32

    -- constrained subtypes

    TestTypeEnum ::= INTEGER {
                        noResponse(-1),
                        noError(0),
                        tooBig(1)
                    }
    TestTypeSizeRangeConstraint ::= OCTET STRING (SIZE (0..255))
    TestTypeSizeConstraint ::= OCTET STRING (SIZE (8 | 11))
    TestTypeRangeConstraint ::= INTEGER (0..2)
    TestTypeSingleValueConstraint ::= INTEGER (0|2|4)

    TestTypeBits ::= BITS {
                        sunday(0),
                        monday(1),
                        tuesday(2),
                        wednesday(3),
                        thursday(4),
                        friday(5),
                        saturday(6)
                    }


    TestTextualConvention ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "1x:"
        STATUS       current
        DESCRIPTION
                "Test TC"
        REFERENCE
                "Test reference"
        SYNTAX       OCTET STRING

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().genCode(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().genCode(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

        self.mibViewController = MibViewController(mibBuilder)

    def protoTestSymbol(self, symbol, klass):
        self.assertTrue(symbol in self.ctx, f"symbol {symbol} not present")

    def protoTestClass(self, symbol, klass):
        self.assertEqual(
            self.ctx[symbol].__bases__[0].__name__,
            klass,
            f"expected class {klass}, got {self.ctx[symbol].__bases__[0].__name__} at {symbol}",
        )

    def protoTestExport(self, symbol, klass):
        self.assertEqual(
            self.mibViewController.getTypeName(symbol),
            ("TEST-MIB", symbol),
            f"Symbol {symbol} not exported",
        )

    def testTextualConventionSymbol(self):
        self.assertTrue("TestTextualConvention" in self.ctx, "symbol not present")

    def testTextualConventionDisplayHint(self):
        self.assertEqual(
            self.ctx["TestTextualConvention"]().getDisplayHint(),
            "1x:",
            "bad DISPLAY-HINT",
        )

    def testTextualConventionStatus(self):
        self.assertEqual(
            self.ctx["TestTextualConvention"]().getStatus(), "current", "bad STATUS"
        )

    def testTextualConventionDescription(self):
        self.assertEqual(
            self.ctx["TestTextualConvention"]().getDescription(),
            "Test TC\n",
            "bad DESCRIPTION",
        )

    def testTextualConventionReference(self):
        self.assertEqual(
            self.ctx["TestTextualConvention"]().getReference(),
            "Test reference\n",
            "bad REFERENCE",
        )

    def testTextualConventionClass(self):
        self.assertTrue(
            issubclass(
                self.ctx["TestTextualConvention"], self.ctx["TextualConvention"]
            ),
            "bad SYNTAX class",
        )

    def testTextualConventionExport(self):
        self.assertEqual(
            self.mibViewController.getTypeName("TestTextualConvention"),
            ("TEST-MIB", "TestTextualConvention"),
            f"not exported",
        )


# populate test case class with per-type methods

typesMap = (
    # TODO: Integer/Integer32?
    ("TestTypeInteger", "Integer32"),
    ("TestTypeOctetString", "OctetString"),
    ("TestTypeObjectIdentifier", "ObjectIdentifier"),
    ("TestTypeIpAddress", "IpAddress"),
    ("TestTypeInteger32", "Integer32"),
    ("TestTypeCounter32", "Counter32"),
    ("TestTypeGauge32", "Gauge32"),
    ("TestTypeTimeTicks", "TimeTicks"),
    ("TestTypeOpaque", "Opaque"),
    ("TestTypeCounter64", "Counter64"),
    ("TestTypeUnsigned32", "Unsigned32"),
    ("TestTypeTestTypeEnum", "Integer32"),
    ("TestTypeSizeRangeConstraint", "OctetString"),
    ("TestTypeSizeConstraint", "OctetString"),
    ("TestTypeRangeConstraint", "Integer32"),
    ("TestTypeSingleValueConstraint", "Integer32"),
)


def decor(func, symbol, klass):
    def inner(self):
        func(self, symbol, klass)

    return inner


for s, k in typesMap:
    setattr(
        TypeDeclarationTestCase,
        "testTypeDeclaration" + k + "SymbolTestCase",
        decor(TypeDeclarationTestCase.protoTestSymbol, s, k),
    )
    setattr(
        TypeDeclarationTestCase,
        "testTypeDeclaration" + k + "ClassTestCase",
        decor(TypeDeclarationTestCase.protoTestClass, s, k),
    )
    setattr(
        TypeDeclarationTestCase,
        "testTypeDeclaration" + k + "ExportTestCase",
        decor(TypeDeclarationTestCase.protoTestExport, s, k),
    )


# XXX constraints flavor not checked


class TypeDeclarationHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      Unsigned32
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    Test-Textual-Convention ::= TEXTUAL-CONVENTION
        DISPLAY-HINT "d-2"
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       Unsigned32

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().genCode(ast, {})
        self.mibInfo, pycode = PySnmpCodeGen().genCode(ast, {mibInfo.name: symtable})
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

        self.mibViewController = MibViewController(mibBuilder)

    def testTextualConventionSymbol(self):
        self.assertTrue("Test_Textual_Convention" in self.ctx, "symbol not present")

    def testTextualConventionExport(self):
        self.assertEqual(
            self.mibViewController.getTypeName("Test-Textual-Convention"),
            ("TEST-MIB", "Test-Textual-Convention"),
            f"Symbol not exported",
        )

    def testTextualConventionDisplayHint(self):
        self.assertEqual(
            self.ctx["Test_Textual_Convention"]().getDisplayHint(),
            "d-2",
            "bad DISPLAY-HINT",
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
