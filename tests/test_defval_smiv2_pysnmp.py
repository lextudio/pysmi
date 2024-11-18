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


class DefaultIntegerTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 123456 }
     ::= { 1 3 }

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

    def testIntegerDefvalSyntax(self):
        self.assertEqual(self.ctx["testObjectType"].getSyntax(), 123456, "bad DEFVAL")


class DefaultIntegerZeroTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 }

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

    def testIntegerDefvalZeroSyntax(self):
        self.assertEqual(self.ctx["testObjectType"].getSyntax(), 0, "bad DEFVAL")


class DefaultIntegerNegativeTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;


    testObjectType OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -123 }
     ::= { 1 3 }

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

    def testIntegerDefvalSyntaxIsValue(self):
        # This test basically verifies that isValue is working at all, so that
        # we can be sure the assertFalse tests in the extended tests (further
        # below) are meaningful.
        self.assertTrue(self.ctx["testObjectType"].getSyntax().isValue, "bad DEFVAL")

    def testIntegerDefvalNegativeSyntax(self):
        self.assertEqual(self.ctx["testObjectType"].getSyntax(), -123, "bad DEFVAL")


class DefaultIntegerFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectTypeHex OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 'abCD0e'H }
     ::= { 1 3 }

    testObjectTypeBinary OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '11011100'B }
     ::= { 1 4 }

    testObjectTypeString OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "0" }
     ::= { 1 5 }

    testObjectTypeSymbol OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { testObjectTypeString }
     ::= { 1 6 }

    testObjectTypeBrackets OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { 0 } }
     ::= { 1 7 }

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

    def testIntegerDefvalHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex"].getSyntax(), 0xABCD0E, "bad DEFVAL"
        )

    def testIntegerDefvalBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary"].getSyntax(), 220, "bad DEFVAL"
        )

    def testIntegerDefvalStringSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeString"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalSymbolSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeSymbol"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBracketsSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBrackets"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultIntegerValueTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectTypePaddedHex OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00abCD0e'H }
     ::= { 1 3 }

    testObjectTypePaddedBinary OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '0000000011011100'B }
     ::= { 1 4 }

    testObjectTypeZeroHex OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { ''H }
     ::= { 1 5 }

    testObjectTypeZeroBinary OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { ''B }
     ::= { 1 6 }

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

    def testIntegerDefvalPaddedHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypePaddedHex"].getSyntax(), 0xABCD0E, "bad DEFVAL"
        )

    def testIntegerDefvalPaddedBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypePaddedBinary"].getSyntax(), 220, "bad DEFVAL"
        )

    def testIntegerDefvalZeroHexSyntax(self):
        self.assertEqual(self.ctx["testObjectTypeZeroHex"].getSyntax(), 0, "bad DEFVAL")

    def testIntegerDefvalZeroBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeZeroBinary"].getSyntax(), 0, "bad DEFVAL"
        )


class DefaultIntegerConstraintsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectTypeDecimal1 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -3 }
     ::= { 1 3 1 }

    testObjectTypeDecimal2 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -2 }
     ::= { 1 3 2 }

    testObjectTypeDecimal3 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -1 }
     ::= { 1 3 3 }

    testObjectTypeDecimal4 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 4 }

    testObjectTypeDecimal5 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 3 5 }

    testObjectTypeDecimal6 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 2 }
     ::= { 1 3 6 }

    testObjectTypeDecimal7 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 3 }
     ::= { 1 3 7 }

    testObjectTypeDecimal8 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 4 }
     ::= { 1 3 8 }

    testObjectTypeDecimal9 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 5 }
     ::= { 1 3 9 }

    testObjectTypeDecimal10 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 6 }
     ::= { 1 3 10 }

    testObjectTypeDecimal11 OBJECT-TYPE
        SYNTAX          Integer32 (-2..-1 | 3 | 5..6)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 7 }
     ::= { 1 3 11 }

    testObjectTypeHex1 OBJECT-TYPE
        SYNTAX          Integer32 (12345)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '3038'H }
     ::= { 1 4 1 }

    testObjectTypeHex2 OBJECT-TYPE
        SYNTAX          Integer32 (12345)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '3039'H }
     ::= { 1 4 2 }

    testObjectTypeHex3 OBJECT-TYPE
        SYNTAX          Integer32 (12345)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '303A'H }
     ::= { 1 4 3 }

    testObjectTypeHex4 OBJECT-TYPE
        SYNTAX          Integer32 (12345)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '003039'H }
     ::= { 1 4 4 }

    testObjectTypeBinary1 OBJECT-TYPE
        SYNTAX          Integer32 (67..68)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '01000010'B }
     ::= { 1 5 1 }

    testObjectTypeBinary2 OBJECT-TYPE
        SYNTAX          Integer32 (67..68)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '01000011'B }
     ::= { 1 5 2 }

    testObjectTypeBinary3 OBJECT-TYPE
        SYNTAX          Integer32 (67..68)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '0000000001000100'B }
     ::= { 1 5 3 }

    testObjectTypeBinary4 OBJECT-TYPE
        SYNTAX          Integer32 (67..68)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '01000101'B }
     ::= { 1 5 4 }

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

    def testIntegerDefvalDecimalSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal2"].getSyntax(), -2, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal3"].getSyntax(), -1, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntaxIsValue4(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal4"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntaxIsValue5(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal5"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntaxIsValue6(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal6"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntax7(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal7"].getSyntax(), 3, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntaxIsValue8(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal8"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntax9(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal9"].getSyntax(), 5, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntax10(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal10"].getSyntax(), 6, "bad DEFVAL"
        )

    def testIntegerDefvalDecimalSyntaxIsValue11(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal11"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex2"].getSyntax(), 12345, "bad DEFVAL"
        )

    def testIntegerDefvalHexSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexSyntax4(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex4"].getSyntax(), 12345, "bad DEFVAL"
        )

    def testIntegerDefvalBinarySyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinary1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBinarySyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary2"].getSyntax(), 67, "bad DEFVAL"
        )

    def testIntegerDefvalBinarySyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary3"].getSyntax(), 68, "bad DEFVAL"
        )

    def testIntegerDefvalBinarySyntaxIsValue4(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinary4"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultIntegerConstraintsLayersTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    SimpleConstrainedInteger ::= Integer32 (1..2)

    testObjectTypeSimple1 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -1 }
     ::= { 1 3 1 }

    testObjectTypeSimple2 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 2 }

    testObjectTypeSimple3 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 3 3 }

    -- The extra constraints are not correct, as they are not a subset of the
    -- original constraints, but pysmi should deal with them properly.
    testObjectTypeLayeredSimple1 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger (2..3)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 3 4 }

    testObjectTypeLayeredSimple2 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger (2..3)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 2 }
     ::= { 1 3 5 }

    testObjectTypeLayeredSimple3 OBJECT-TYPE
        SYNTAX          SimpleConstrainedInteger (2..3)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 3 }
     ::= { 1 3 6 }

    TextualConstrainedInteger ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       Integer32 (-4..-3)

    testObjectTypeTextual1 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -5 }
     ::= { 1 4 1 }

    testObjectTypeTextual2 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 4 }
     ::= { 1 4 2 }

    testObjectTypeTextual3 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -4 }
     ::= { 1 4 3 }

    testObjectTypeLayeredTextual1 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger (-3..-2)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -4 }
     ::= { 1 4 4 }

    testObjectTypeLayeredTextual2 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger (-3..-2)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -3 }
     ::= { 1 4 5 }

    testObjectTypeLayeredTextual3 OBJECT-TYPE
        SYNTAX          TextualConstrainedInteger (-3..-2)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -2 }
     ::= { 1 4 6 }

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

    def testIntegerDefvalSimpleSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeSimple1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalSimpleSyntaxIsValue2(self):
        self.assertFalse(
            self.ctx["testObjectTypeSimple2"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalSimpleSyntax3(self):
        self.assertEqual(self.ctx["testObjectTypeSimple3"].getSyntax(), 1, "bad DEFVAL")

    def testIntegerDefvalLayeredSimpleSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredSimple1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalLayeredSimpleSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeLayeredSimple2"].getSyntax(), 2, "bad DEFVAL"
        )

    def testIntegerDefvalLayeredSimpleSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredSimple3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalTextualSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeTextual1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalTextualSyntaxIsValue2(self):
        self.assertFalse(
            self.ctx["testObjectTypeTextual2"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalTextualSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeTextual3"].getSyntax(), -4, "bad DEFVAL"
        )

    def testIntegerDefvalLayeredTextualSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredTextual1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalLayeredTextualSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeLayeredTextual2"].getSyntax(), -3, "bad DEFVAL"
        )

    def testIntegerDefvalLayeredTextualSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredTextual3"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultIntegerConstraintsFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE,
      Integer32
        FROM SNMPv2-SMI;

    testObjectTypeHexFormat1 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 3 1 }

    testObjectTypeHexFormat2 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 2 }
     ::= { 1 3 2 }

    testObjectTypeHexFormat3 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 3 }
     ::= { 1 3 3 }

    testObjectTypeHexFormat4 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 4 }
     ::= { 1 3 4 }

    testObjectTypeHexFormat5 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 509 }
     ::= { 1 3 5 }

    testObjectTypeHexFormat6 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 510 }
     ::= { 1 3 6 }

    testObjectTypeHexFormat7 OBJECT-TYPE
        SYNTAX          Integer32 ('02'H..'03'H | '01FE'H)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 511 }
     ::= { 1 3 7 }

    testObjectTypeBinaryFormat1 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 4 1 }

    testObjectTypeBinaryFormat2 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 4 2 }

    testObjectTypeBinaryFormat3 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 2 }
     ::= { 1 4 3 }

    testObjectTypeBinaryFormat4 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 123455 }
     ::= { 1 4 4 }

    testObjectTypeBinaryFormat5 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 123456 }
     ::= { 1 4 5 }

    testObjectTypeBinaryFormat6 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '01E241'H }
     ::= { 1 4 6 }

    testObjectTypeBinaryFormat7 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 123458 }
     ::= { 1 4 7 }

    testObjectTypeBinaryFormat8 OBJECT-TYPE
        SYNTAX          Integer32 ('00000001'B | '00011110001001000000'B..'00011110001001000010'B)
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 123459 }
     ::= { 1 4 8 }

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

    def testIntegerDefvalHexFormatSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat2"].getSyntax(), 2, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat3"].getSyntax(), 3, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntaxIsValue4(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat4"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntaxIsValue5(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat5"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntax6(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat6"].getSyntax(), 510, "bad DEFVAL"
        )

    def testIntegerDefvalHexFormatSyntaxIsValue7(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat7"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat2"].getSyntax(), 1, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntaxIsValue4(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat4"].getSyntax().isValue, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntax5(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat5"].getSyntax(), 123456, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntax6(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat6"].getSyntax(), 123457, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntax7(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat7"].getSyntax(), 123458, "bad DEFVAL"
        )

    def testIntegerDefvalBinaryFormatSyntaxIsValue8(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat8"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultEnumTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          INTEGER  {
                            enable(1),
                            disable(2)
                        }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { enable }
     ::= { 1 3 }

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

    def testEnumDefvalSyntax(self):
        self.assertEqual(self.ctx["testObjectType"].getSyntax(), 1, "bad DEFVAL")


class DefaultEnumNegativeTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          INTEGER  {
                            enable(-1),
                            disable(-2)
                        }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { disable }
     ::= { 1 3 }

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

    def testEnumDefvalNegativeSyntax(self):
        self.assertEqual(self.ctx["testObjectType"].getSyntax(), -2, "bad DEFVAL")


class DefaultEnumFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeDecimal OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 }

    testObjectTypeHex OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '01'H }
     ::= { 1 4 }

    testObjectTypeBinary OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00000010'B }
     ::= { 1 5 }

    testObjectTypeString OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "0" }
     ::= { 1 6 }

    testObjectTypeSymbol OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { testObjectTypeString }
     ::= { 1 7 }

    testObjectTypeBrackets OBJECT-TYPE
        SYNTAX          INTEGER  { enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { disable } }
     ::= { 1 8 }

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

    def testEnumDefvalDecimalSyntax(self):
        self.assertEqual(self.ctx["testObjectTypeDecimal"].getSyntax(), 0, "bad DEFVAL")

    def testEnumDefvalHexSyntax(self):
        self.assertEqual(self.ctx["testObjectTypeHex"].getSyntax(), 1, "bad DEFVAL")

    def testEnumDefvalBinarySyntax(self):
        self.assertEqual(self.ctx["testObjectTypeBinary"].getSyntax(), 2, "bad DEFVAL")

    def testEnumDefvalStringSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeString"].getSyntax().isValue, "bad DEFVAL"
        )

    def testEnumDefvalSymbolSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeSymbol"].getSyntax().isValue, "bad DEFVAL"
        )

    def testEnumDefvalBracketsSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeBrackets"].getSyntax(), 2, "bad DEFVAL"
        )


class DefaultEnumValueTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeBadDecimal OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { -1 }
     ::= { 1 3 }

    testObjectTypeBadHex OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 'FF'H }
     ::= { 1 4 }

    testObjectTypeBadBinary OBJECT-TYPE
        SYNTAX          INTEGER { unknown(0), enable(1), disable(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00000011'B }
     ::= { 1 5 }

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

    def testEnumDefvalBadDecimalSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBadDecimal"].getSyntax().isValue, "bad DEFVAL"
        )

    def testEnumDefvalBadHexSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBadHex"].getSyntax().isValue, "bad DEFVAL"
        )

    def testEnumDefvalBadBinarySyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBadBinary"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultStringTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "test value" }
     ::= { 1 3 }

    testObjectTypeEmpty OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 4 }

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

    def testStringDefvalSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType"].getSyntax(), b"test value", "bad DEFVAL"
        )

    def testStringDefvalEmptySyntax(self):
        self.assertEqual(self.ctx["testObjectTypeEmpty"].getSyntax(), b"", "bad DEFVAL")


class DefaultStringTextTestCase(unittest.TestCase):
    R"""
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "\ntest
    value\" }
     ::= { 1 3 }

    END
    """

    def setUp(self):
        docstring = textwrap.dedent(self.__class__.__doc__)
        ast = parserFactory()().parse(docstring)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

    def testStringDefvalTextSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType"].getSyntax(),
            b"\\ntest\nvalue\\",
            "bad DEFVAL",
        )


class DefaultStringFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeDecimal OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 }

    testObjectTypeHex OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 'abCD'H }
     ::= { 1 4 }

    testObjectTypeBinary OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '000100100011010001010110'B }
     ::= { 1 5 }

    testObjectTypeSymbol OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { testObjectTypeString }
     ::= { 1 6 }

    testObjectTypeBrackets OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { string } }
     ::= { 1 7 }

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

    def testStringDefvalDecimalSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex"].getSyntax(),
            bytes((0xAB, 0xCD)),
            "bad DEFVAL",
        )

    def testStringDefvalBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary"].getSyntax(),
            bytes((0x12, 0x34, 0x56)),
            "bad DEFVAL",
        )

    def testStringDefvalSymbolSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeSymbol"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBracketsSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBrackets"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultStringValueTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeEmptyHex OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { ''H }
     ::= { 1 3 }

    testObjectTypeEmptyBinary OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { ''B }
     ::= { 1 4 }

    testObjectTypePaddedHex OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00abCD'H }
     ::= { 1 5 }

    testObjectTypePaddedBinary OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '0000000000000000000100100011010001010110'B }
     ::= { 1 6 }

    testObjectTypeUnpaddedHex OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '789'H }
     ::= { 1 7 }

    testObjectTypeUnpaddedBinary OBJECT-TYPE
        SYNTAX          OCTET STRING
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '100100011'B }
     ::= { 1 8 }

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

    def testStringDefvalEmptyHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeEmptyHex"].getSyntax(), bytes(), "bad DEFVAL"
        )

    def testStringDefvalEmptyBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeEmptyBinary"].getSyntax(), bytes(), "bad DEFVAL"
        )

    def testStringDefvalPaddedHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypePaddedHex"].getSyntax(),
            bytes((0x00, 0xAB, 0xCD)),
            "bad DEFVAL",
        )

    def testStringDefvalPaddedBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypePaddedBinary"].getSyntax(),
            bytes((0x00, 0x00, 0x12, 0x34, 0x56)),
            "bad DEFVAL",
        )

    def testStringDefvalUnpaddedHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeUnpaddedHex"].getSyntax(),
            bytes((0x07, 0x89)),
            "bad DEFVAL",
        )

    def testStringDefvalUnpaddedBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeUnpaddedBinary"].getSyntax(),
            bytes((0x01, 0x23)),
            "bad DEFVAL",
        )


class DefaultStringConstraintsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeString1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (1..3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 3 1 }

    testObjectTypeString2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (1..3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 3 2 }

    testObjectTypeString3 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (1..3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 3 3 }

    testObjectTypeString4 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (1..3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abc" }
     ::= { 1 3 4 }

    testObjectTypeString5 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (1..3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abcd" }
     ::= { 1 3 5 }

    testObjectTypeZeroString1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (0))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 3 6 }

    testObjectTypeZeroString2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (0))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "x" }
     ::= { 1 3 7 }

    testObjectTypeHex1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (4 | 6))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '414243'H }
     ::= { 1 4 1 }

    testObjectTypeHex2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (4 | 6))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '41424344'H }
     ::= { 1 4 2 }

    testObjectTypeHex3 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (4 | 6))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '4142434445'H }
     ::= { 1 4 3 }

    testObjectTypeHex4 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (4 | 6))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '414243444546'H }
     ::= { 1 4 4 }

    testObjectTypeHex5 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (4 | 6))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '41424344454647'H }
     ::= { 1 4 5 }

    testObjectTypeBinary1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '0011000100110010'B }
     ::= { 1 5 1 }

    testObjectTypeBinary2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '001100010011001000110011'B }
     ::= { 1 5 2 }

    testObjectTypeBinary3 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE (3))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00110001001100100011001100110100'B }
     ::= { 1 5 3 }

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

    def testStringDefvalStringSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeString1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalStringSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeString2"].getSyntax(), b"a", "bad DEFVAL"
        )

    def testStringDefvalStringSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeString3"].getSyntax(), b"ab", "bad DEFVAL"
        )

    def testStringDefvalStringSyntax4(self):
        self.assertEqual(
            self.ctx["testObjectTypeString4"].getSyntax(), b"abc", "bad DEFVAL"
        )

    def testStringDefvalStringSyntaxIsValue5(self):
        self.assertFalse(
            self.ctx["testObjectTypeString5"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalZeroStringSyntax1(self):
        self.assertEqual(
            self.ctx["testObjectTypeZeroString1"].getSyntax(), b"", "bad DEFVAL"
        )

    def testStringDefvalZeroStringSyntaxIsValue2(self):
        self.assertFalse(
            self.ctx["testObjectTypeZeroString2"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalHexSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalHexSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex2"].getSyntax(), b"ABCD", "bad DEFVAL"
        )

    def testStringDefvalHexSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalHexSyntax4(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex4"].getSyntax(), b"ABCDEF", "bad DEFVAL"
        )

    def testStringDefvalHexSyntaxIsValue5(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex5"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinarySyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinary1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinarySyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary2"].getSyntax(), b"123", "bad DEFVAL"
        )

    def testStringDefvalBinarySyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinary3"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultStringConstraintsLayersTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI
      TEXTUAL-CONVENTION
        FROM SNMPv2-TC;

    SimpleConstrainedString ::= OCTET STRING (SIZE (2 | 4))

    testObjectTypeSimple1 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 3 1 }

    testObjectTypeSimple2 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abc" }
     ::= { 1 3 2 }

    testObjectTypeSimple3 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abcd" }
     ::= { 1 3 3 }

    -- The extra constraints are not correct, as they are not a subset of the
    -- original constraints, but pysmi should deal with them properly.
    testObjectTypeLayeredSimple1 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString (SIZE (1..2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 3 4 }

    testObjectTypeLayeredSimple2 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString (SIZE (1..2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 3 5 }

    testObjectTypeLayeredSimple3 OBJECT-TYPE
        SYNTAX          SimpleConstrainedString (SIZE (1..2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abcd" }
     ::= { 1 3 6 }

    TextualConstrainedString ::= TEXTUAL-CONVENTION
        STATUS       current
        DESCRIPTION  "Test TC"
        SYNTAX       OCTET STRING (SIZE (0..1))

    testObjectTypeTextual1 OBJECT-TYPE
        SYNTAX          TextualConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 4 1 }

    testObjectTypeTextual2 OBJECT-TYPE
        SYNTAX          TextualConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 4 2 }

    testObjectTypeTextual3 OBJECT-TYPE
        SYNTAX          TextualConstrainedString
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 4 3 }

    testObjectTypeLayeredTextual1 OBJECT-TYPE
        SYNTAX          TextualConstrainedString (SIZE (0 | 2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 4 4 }

    testObjectTypeLayeredTextual2 OBJECT-TYPE
        SYNTAX          TextualConstrainedString (SIZE (0 | 2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 4 5 }

    testObjectTypeLayeredTextual3 OBJECT-TYPE
        SYNTAX          TextualConstrainedString (SIZE (0 | 2))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 4 6 }

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

    def testStringDefvalSimpleSyntax1(self):
        self.assertEqual(
            self.ctx["testObjectTypeSimple1"].getSyntax(), b"ab", "bad DEFVAL"
        )

    def testStringDefvalSimpleSyntaxIsValue2(self):
        self.assertFalse(
            self.ctx["testObjectTypeSimple2"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalSimpleSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeSimple3"].getSyntax(), b"abcd", "bad DEFVAL"
        )

    def testStringDefvalLayeredSimpleSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredSimple1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalLayeredSimpleSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeLayeredSimple2"].getSyntax(), b"ab", "bad DEFVAL"
        )

    def testStringDefvalLayeredSimpleSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredSimple3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalTextualSyntax1(self):
        self.assertEqual(
            self.ctx["testObjectTypeTextual1"].getSyntax(), b"", "bad DEFVAL"
        )

    def testStringDefvalTextualSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeTextual2"].getSyntax(), b"a", "bad DEFVAL"
        )

    def testStringDefvalTextualSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeTextual3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalLayeredTextualSyntax1(self):
        self.assertEqual(
            self.ctx["testObjectTypeLayeredTextual1"].getSyntax(), b"", "bad DEFVAL"
        )

    def testStringDefvalLayeredTextualSyntaxIsValue2(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredTextual2"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalLayeredTextualSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeLayeredTextual3"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultStringConstraintsFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeHexFormat1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('01'H..'02'H | '03'H))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 3 1 }

    testObjectTypeHexFormat2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('01'H..'02'H | '03'H))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 3 2 }

    testObjectTypeHexFormat3 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('01'H..'02'H | '03'H))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 3 3 }

    testObjectTypeHexFormat4 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('01'H..'02'H | '03'H))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abc" }
     ::= { 1 3 4 }

    testObjectTypeHexFormat5 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('01'H..'02'H | '03'H))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "abcd" }
     ::= { 1 3 5 }

    testObjectTypeBinaryFormat1 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "" }
     ::= { 1 4 1 }

    testObjectTypeBinaryFormat2 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "a" }
     ::= { 1 4 2 }

    testObjectTypeBinaryFormat3 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "ab" }
     ::= { 1 4 3 }

    testObjectTypeBinaryFormat4 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "this is a tes" }
     ::= { 1 4 4 }

    testObjectTypeBinaryFormat5 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "this is a test" }
     ::= { 1 4 5 }

    testObjectTypeBinaryFormat6 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "this is a test!" }
     ::= { 1 4 6 }

    testObjectTypeBinaryFormat7 OBJECT-TYPE
        SYNTAX          OCTET STRING (SIZE ('00000001'B | '00001110'B..'00001111'B))
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "this is a test!?" }
     ::= { 1 4 7 }

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

    def testStringDefvalHexFormatSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalHexFormatSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat2"].getSyntax(), b"a", "bad DEFVAL"
        )

    def testStringDefvalHexFormatSyntax3(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat3"].getSyntax(), b"ab", "bad DEFVAL"
        )

    def testStringDefvalHexFormatSyntax4(self):
        self.assertEqual(
            self.ctx["testObjectTypeHexFormat4"].getSyntax(), b"abc", "bad DEFVAL"
        )

    def testStringDefvalHexFormatSyntaxIsValue5(self):
        self.assertFalse(
            self.ctx["testObjectTypeHexFormat5"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinaryFormatSyntaxIsValue1(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat1"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinaryFormatSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat2"].getSyntax(), b"a", "bad DEFVAL"
        )

    def testStringDefvalBinaryFormatSyntaxIsValue3(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat3"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinaryFormatSyntaxIsValue4(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat4"].getSyntax().isValue, "bad DEFVAL"
        )

    def testStringDefvalBinaryFormatSyntax5(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat5"].getSyntax(),
            b"this is a test",
            "bad DEFVAL",
        )

    def testStringDefvalBinaryFormatSyntax6(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinaryFormat6"].getSyntax(),
            b"this is a test!",
            "bad DEFVAL",
        )

    def testStringDefvalBinaryFormatSyntaxIsValue7(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinaryFormat7"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultBitsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType1 OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { present, absent } }
     ::= { 1 3 }

    testObjectType2 OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { changed } }
     ::= { 1 4 }

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

    def testBitsDefvalSyntax1(self):
        self.assertEqual(
            self.ctx["testObjectType1"].getSyntax(),
            bytes((0xC0,)),
            "bad DEFVAL",
        )

    def testBitsDefvalSyntax2(self):
        self.assertEqual(
            self.ctx["testObjectType2"].getSyntax(),
            bytes((0x20,)),
            "bad DEFVAL",
        )


class DefaultBitsMultiOctetTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          BITS { a(0), b(1), c(2), d(3), e(4), f(5), g(6), h(7), i(8), j(9), k(10), l(11), m(12), n(13), o(14), p(15), q(16) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { b, c, m } }
     ::= { 1 3 }

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

    def testBitsDefvalMultiOctetSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType"].getSyntax(),
            bytes((0x60, 0x08)),
            "bad DEFVAL",
        )


class DefaultBitsEmptySetTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { } }
     ::= { 1 3 }

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

    def testBitsDefvalEmptySyntax(self):
        self.assertEqual(
            self.ctx["testObjectType"].getSyntax(),
            bytes((0x00,)),
            "bad DEFVAL",
        )


class DefaultBitsFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeDecimal OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 1 }
     ::= { 1 3 }

    testObjectTypeHex OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '04'H }
     ::= { 1 4 }

    testObjectTypeBinary OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00000111'B }
     ::= { 1 5 }

    testObjectTypeString OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "0" }
     ::= { 1 6 }

    testObjectTypeSymbol OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { present }
     ::= { 1 7 }

    testObjectTypeBrackets OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { 0 } }
     ::= { 1 8 }

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

    def testBitsDefvalDecimalSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeDecimal"].getSyntax(),
            bytes((0x01,)),
            "bad DEFVAL",
        )

    def testBitsDefvalHexSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeHex"].getSyntax(),
            bytes((0x04,)),
            "bad DEFVAL",
        )

    def testBitsDefvalBinarySyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeBinary"].getSyntax(),
            bytes((0x07,)),
            "bad DEFVAL",
        )

    def testBitsDefvalStringSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeString"].getSyntax().isValue, "bad DEFVAL"
        )

    def testBitsDefvalSymbolSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeSymbol"].getSyntax().isValue, "bad DEFVAL"
        )

    def testBitsDefvalBracketsSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBrackets"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultBitsValueTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeDuplicateLabel OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { absent, absent } }
     ::= { 1 3 }

    testObjectTypeBadLabel OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { unchanged } }
     ::= { 1 4 }

    testObjectTypeOneBadLabel OBJECT-TYPE
        SYNTAX          BITS { present(0), absent(1), changed(2) }
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { present, unchanged, absent } }
     ::= { 1 5 }

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

    def testBitsDefvalDuplicateLabelSyntax(self):
        self.assertEqual(
            self.ctx["testObjectTypeDuplicateLabel"].getSyntax(),
            bytes((0x40,)),
            "bad DEFVAL",
        )

    def testBitsDefvalBadLabelSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBadLabel"].getSyntax().isValue, "bad DEFVAL"
        )

    def testBitsDefvalOneBadLabelSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeOneBadLabel"].getSyntax().isValue, "bad DEFVAL"
        )


class DefaultObjectIdentifierTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE, Integer32
        FROM SNMPv2-SMI;

    testTargetObjectType OBJECT-TYPE
        SYNTAX          Integer32
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test target object"
     ::= { 1 3 }

    testObjectType OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { testTargetObjectType }
     ::= { 1 4 }

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

    def testObjectIdentifierDefvalSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType"].getSyntax(),
            (1, 3),
            "bad DEFVAL",
        )


class DefaultObjectIdentifierInvalidTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectType OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { 0 0 } }
     ::= { 1 3 }

    END
    """

    def testObjectIdentifierDefvalInvalidSyntax(self):
        # The "{{0 0}}" type notation is invalid and currently not supported.
        # This test verifies that such notations can be parsed at all, which
        # is why the parsing is part of the actual test, and why successful
        # instantiation of the syntax is enough here.
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

        self.ctx["testObjectType"].getSyntax()


class DefaultObjectIdentifierHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    test-target-object-type OBJECT IDENTIFIER ::= { 1 3 }
    global                  OBJECT IDENTIFIER ::= { 1 4 }  -- a reserved Python keyword

    testObjectType1 OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { test-target-object-type }
     ::= { 1 5 }

    testObjectType2 OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { global }
     ::= { 1 6 }

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

    def testObjectIdentifierDefvalHyphenSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType1"].getSyntax(),
            (1, 3),
            "bad DEFVAL",
        )

    def testObjectIdentifierDefvalKeywordSyntax(self):
        self.assertEqual(
            self.ctx["testObjectType2"].getSyntax(),
            (1, 4),
            "bad DEFVAL",
        )


class DefaultObjectIdentifierFormatTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM SNMPv2-SMI;

    testObjectTypeDecimal OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { 0 }
     ::= { 1 3 }

    testObjectTypeHex OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00'H }
     ::= { 1 4 }

    testObjectTypeBinary OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { '00000000'B }
     ::= { 1 5 }

    testObjectTypeString OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { "0" }
     ::= { 1 6 }

    testObjectTypeSymbol OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { doesNotExist }
     ::= { 1 7 }

    testObjectTypeBrackets OBJECT-TYPE
        SYNTAX          OBJECT IDENTIFIER
        MAX-ACCESS      read-only
        STATUS          current
        DESCRIPTION     "Test object"
        DEFVAL          { { testObjectTypeSymbol } }
     ::= { 1 8 }

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

    def testObjectIdentifierDefvalDecimalSyntax(self):
        self.assertFalse(
            self.ctx["testObjectTypeDecimal"].getSyntax().isValue, "bad DEFVAL"
        )

    def testObjectIdentifierDefvalHexSyntax(self):
        self.assertFalse(
            self.ctx["testObjectTypeHex"].getSyntax().isValue, "bad DEFVAL"
        )

    def testObjectIdentifierDefvalBinarySyntax(self):
        self.assertFalse(
            self.ctx["testObjectTypeBinary"].getSyntax().isValue, "bad DEFVAL"
        )

    def testObjectIdentifierDefvalStringSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeString"].getSyntax().isValue, "bad DEFVAL"
        )

    def testObjectIdentifierDefvalSymbolSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeSymbol"].getSyntax().isValue, "bad DEFVAL"
        )

    def testObjectIdentifierDefvalBracketsSyntaxIsValue(self):
        self.assertFalse(
            self.ctx["testObjectTypeBrackets"].getSyntax().isValue, "bad DEFVAL"
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
