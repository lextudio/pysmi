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


class TrapTypeTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      TRAP-TYPE
        FROM RFC-1215

      OBJECT-TYPE
        FROM RFC1155-SMI;

    testId  OBJECT IDENTIFIER ::= { 1 3 }

    testObject OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      accessible-for-notify
        STATUS          current
        DESCRIPTION     "Test object"
     ::= { 1 3 }

    testTrap     TRAP-TYPE
            ENTERPRISE  testId
            VARIABLES { testObject }
            DESCRIPTION
                    "Test trap"
      ::= 1

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

    def testTrapTypeSymbol(self):
        self.assertTrue("testTrap" in self.ctx, "symbol not present")

    def testTrapTypeName(self):
        self.assertEqual(self.ctx["testTrap"].getName(), (1, 3, 0, 1), "bad name")

    def testTrapTypeDescription(self):
        self.assertEqual(
            self.ctx["testTrap"].getDescription(), "Test trap", "bad DESCRIPTION"
        )

    def testTrapTypeObjects(self):
        self.assertEqual(
            self.ctx["testTrap"].getObjects(),
            (("TEST-MIB", "testObject"),),
            "bad OBJECTS",
        )

    def testTrapTypeClass(self):
        self.assertEqual(
            self.ctx["testTrap"].__class__.__name__,
            "NotificationType",
            "bad SYNTAX class",
        )


class TrapTypeHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      TRAP-TYPE
        FROM RFC-1215

      OBJECT-TYPE
        FROM RFC1155-SMI;

    test-id  OBJECT IDENTIFIER ::= { 1 3 }

    test-object OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      accessible-for-notify
        STATUS          current
        DESCRIPTION     "Test object"
     ::= { 1 3 }

    test-trap     TRAP-TYPE
            ENTERPRISE  test-id
            VARIABLES { test-object }
            DESCRIPTION
                    "Test trap"
      ::= 1

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(ast, {mibInfo.name: symtable})
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

    def testTrapTypeSymbol(self):
        self.assertTrue("test_trap" in self.ctx, "symbol not present")

    def testTrapTypeLabel(self):
        self.assertEqual(self.ctx["test_trap"].getLabel(), "test-trap", "bad label")

    def testTrapTypeObjects(self):
        self.assertEqual(
            self.ctx["test_trap"].getObjects(),
            (("TEST-MIB", "test-object"),),
            "bad OBJECTS",
        )


class TrapTypeTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      TRAP-TYPE
        FROM RFC-1215

      OBJECT-TYPE
        FROM RFC1155-SMI;

    testId  OBJECT IDENTIFIER ::= { 1 3 }

    testObject OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      accessible-for-notify
        STATUS          current
        DESCRIPTION     "Test object"
     ::= { 1 3 }

    testTrap     TRAP-TYPE
            ENTERPRISE  testId
            VARIABLES { testObject }
            DESCRIPTION
                    "Test   \\trap"
      ::= 1

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast,
            {mibInfo.name: symtable},
            genTexts=True,
            textFilter=lambda symbol, text: text,
        )
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

    def testTrapTypeDescription(self):
        self.assertEqual(
            self.ctx["testTrap"].getDescription(), "Test   \\trap", "bad DESCRIPTION"
        )


class TrapTypeNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      TRAP-TYPE
        FROM RFC-1215

      OBJECT-TYPE
        FROM RFC1155-SMI;

    testId  OBJECT IDENTIFIER ::= { 1 3 }

    testObject OBJECT-TYPE
        SYNTAX          INTEGER
        MAX-ACCESS      accessible-for-notify
        STATUS          current
        DESCRIPTION     "Test object"
     ::= { 1 3 }

    testTrap     TRAP-TYPE
            ENTERPRISE  testId
            VARIABLES { testObject }
            DESCRIPTION
                    "Test trap"
      ::= 1

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

    def testTrapTypeDescription(self):
        self.assertEqual(self.ctx["testTrap"].getDescription(), "", "bad DESCRIPTION")


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
