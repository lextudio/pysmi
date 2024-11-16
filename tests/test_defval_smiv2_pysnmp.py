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
