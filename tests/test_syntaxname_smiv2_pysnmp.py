#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof; Copyright (c) 2022-2024, others
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys
import textwrap

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from pysmi.parser.smi import parserFactory
from pysmi.codegen.pysnmp import PySnmpCodeGen
from pysmi.codegen.symtable import SymtableCodeGen
from pysnmp.smi.builder import MibBuilder
from pysnmp.smi.view import MibViewController


def decor(func, symbol, klass):
    def inner(self):
        func(self, symbol, klass)

    return inner


class SyntaxNameLocalTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    testObject1 OBJECT-TYPE
        SYNTAX       Integer32
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 1 }

    testObject2 OBJECT-TYPE
        SYNTAX       Integer32 (0..9)
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 2 }

    testObject3 OBJECT-TYPE
        SYNTAX       BITS { value(0), otherValue(1) }
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 3 }

    testObject4 OBJECT-TYPE
        SYNTAX       Integer32
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
        DEFVAL       { 0 }
      ::= { 1 4 4 }

    TestTypeI ::= Integer32
    TestTypeB ::= BITS { value(0), otherValue(1) }

    testObject5 OBJECT-TYPE
        SYNTAX       TestTypeI
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 5 }

    testObject6 OBJECT-TYPE
        SYNTAX       TestTypeI (2..5)
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 6 }

    testObject7 OBJECT-TYPE
        SYNTAX       TestTypeB { value(0) }
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 7 }

    testObject8 OBJECT-TYPE
        SYNTAX       TestTypeI
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
        DEFVAL       { 0 }
      ::= { 1 4 8 }

    TestTCI ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       Integer32

    TestTCB ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       BITS { value(0), otherValue(1) }

    testObject9 OBJECT-TYPE
        SYNTAX       TestTCI
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 9 }

    testObject10 OBJECT-TYPE
        SYNTAX       TestTCI (2..5)
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 10 }

    testObject11 OBJECT-TYPE
        SYNTAX       TestTCB { value(0) }
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 11 }

    testObject12 OBJECT-TYPE
        SYNTAX       TestTCI
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
        DEFVAL       { 0 }
      ::= { 1 4 12 }

    Test-Hyphen-TC ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       Integer32

    testObject13 OBJECT-TYPE
        SYNTAX       Test-Hyphen-TC
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 13 }

    testObject14 OBJECT-TYPE
        SYNTAX       Test-Hyphen-TC (2..5)
        MAX-ACCESS   read-only
        STATUS       current
        DESCRIPTION  "Test object"
      ::= { 1 4 14 }

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(ast, {mibInfo.name: symtable})
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

        self.mibViewController = MibViewController(mibBuilder)

    def protoTestObjectTypeSyntaxName(self, symbol, name):
        self.assertEqual(
            self.ctx[symbol].getSyntax().__class__.__name__,
            name,
            f"bad SYNTAX NAME for {symbol}",
        )

    def protoTestObjectTypeSyntaxClass(self, symbol, name):
        self.assertTrue(
            issubclass(self.ctx[symbol].getSyntax().__class__, self.ctx[name]),
            f"bad SYNTAX CLASS for {symbol}",
        )


syntaxNamesMap = (
    ("1", "Integer32"),
    ("2", "Integer32"),
    ("3", "Bits"),
    ("4", "Integer32"),
    ("5", "TestTypeI"),
    ("6", "TestTypeI"),
    ("7", "TestTypeB"),
    ("8", "TestTypeI"),
    ("9", "TestTCI"),
    ("10", "TestTCI"),
    ("11", "TestTCB"),
    ("12", "TestTCI"),
    ("13", "Test_Hyphen_TC"),
    ("14", "Test_Hyphen_TC"),
)


for n, k in syntaxNamesMap:
    setattr(
        SyntaxNameLocalTestCase,
        "testObjectTypeSyntaxName" + n,
        decor(
            SyntaxNameLocalTestCase.protoTestObjectTypeSyntaxName, f"testObject{n}", k
        ),
    )

    # The class name of the syntax must itself be a symbol that identifies a
    # base class of that syntax.
    setattr(
        SyntaxNameLocalTestCase,
        "testObjectTypeSyntaxClass" + n,
        decor(
            SyntaxNameLocalTestCase.protoTestObjectTypeSyntaxClass, f"testObject{n}", k
        ),
    )


class SyntaxNameImportTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC
      ImportedType1, Imported-Type-2
        FROM IMPORTED-MIB;

    testObject1 OBJECT-TYPE
        SYNTAX      ImportedType1
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 4 1 }

    testObject2 OBJECT-TYPE
        SYNTAX      ImportedType1 (2..5)
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 4 2 }

    testObject3 OBJECT-TYPE
        SYNTAX      ImportedType1
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { 0 }
      ::= { 1 4 3 }

    testObject4 OBJECT-TYPE
        SYNTAX      Imported-Type-2
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 4 4 }

    testObject5 OBJECT-TYPE
        SYNTAX      Imported-Type-2 { value(0) }
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
      ::= { 1 4 5 }

    testObject6 OBJECT-TYPE
        SYNTAX      Imported-Type-2
        MAX-ACCESS  read-only
        STATUS      current
        DESCRIPTION "Test object"
        DEFVAL      { { otherValue } }
      ::= { 1 4 6 }

    END
    """

    IMPORTED_MIB = """
    IMPORTED-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE, Integer32
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    ImportedType1 ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       Integer32

    Imported-Type-2 ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       BITS { value(0), otherValue(1) }

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

    def protoTestObjectTypeSyntaxName(self, symbol, name):
        self.assertEqual(
            self.ctx[symbol].getSyntax().__class__.__name__,
            name,
            f"bad SYNTAX NAME for {symbol}",
        )

    def protoTestObjectTypeSyntaxClass(self, symbol, name):
        self.assertTrue(
            issubclass(self.ctx[symbol].getSyntax().__class__, self.ctx[name]),
            f"bad SYNTAX CLASS for {symbol}",
        )


syntaxNamesMap = (
    ("1", "ImportedType1"),
    ("2", "ImportedType1"),
    ("3", "ImportedType1"),
    ("4", "Imported_Type_2"),
    ("5", "Imported_Type_2"),
    ("6", "Imported_Type_2"),
)


for n, k in syntaxNamesMap:
    setattr(
        SyntaxNameImportTestCase,
        "testObjectTypeSyntaxName" + n,
        decor(
            SyntaxNameImportTestCase.protoTestObjectTypeSyntaxName, f"testObject{n}", k
        ),
    )

    # The class name of the syntax must itself be a symbol that identifies a
    # base class of that syntax.
    setattr(
        SyntaxNameImportTestCase,
        "testObjectTypeSyntaxClass" + n,
        decor(
            SyntaxNameImportTestCase.protoTestObjectTypeSyntaxClass, f"testObject{n}", k
        ),
    )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
