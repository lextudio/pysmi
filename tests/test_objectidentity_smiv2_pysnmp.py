#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
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


class ObjectIdentityTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        OBJECT-IDENTITY
    FROM SNMPv2-SMI;

    testObject OBJECT-IDENTITY
        STATUS          current
        DESCRIPTION     "Initial version"
        REFERENCE       "ABC"

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

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

    def testObjectIdentitySymbol(self):
        self.assertTrue("testObject" in self.ctx, "symbol not present")

    def testObjectIdentityName(self):
        self.assertEqual(self.ctx["testObject"].getName(), (1, 3), "bad name")

    def testObjectIdentityStatus(self):
        self.assertEqual(self.ctx["testObject"].getStatus(), "current", "bad STATUS")

    def testObjectIdentityDescription(self):
        self.assertEqual(
            self.ctx["testObject"].getDescription(),
            "Initial version",
            "bad DESCRIPTION",
        )

    def testObjectIdentityReference(self):
        self.assertEqual(self.ctx["testObject"].getReference(), "ABC", "bad REFERENCE")

    def testObjectIdentityClass(self):
        self.assertEqual(
            self.ctx["testObject"].__class__.__name__,
            "ObjectIdentity",
            "bad SYNTAX class",
        )


class ObjectIdentityHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        OBJECT-IDENTITY
    FROM SNMPv2-SMI;

    test-object OBJECT-IDENTITY
        STATUS          current
        DESCRIPTION     "Initial version"

     ::= { 1 3 }

    END
    """

    def setUp(self):
        ast = parserFactory()().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(ast, {mibInfo.name: symtable})
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

    def testObjectIdentitySymbol(self):
        self.assertTrue("test_object" in self.ctx, "symbol not present")

    def testObjectIdentityLabel(self):
        self.assertEqual(self.ctx["test_object"].getLabel(), "test-object", "bad label")


class ObjectIdentityTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        OBJECT-IDENTITY
    FROM SNMPv2-SMI;

    testObject OBJECT-IDENTITY
        STATUS          obsolete
        DESCRIPTION     "\\'Initial' version"
        REFERENCE       "
    "

     ::= { 1 3 }

    END
    """

    def setUp(self):
        docstring = textwrap.dedent(self.__class__.__doc__)
        ast = parserFactory()().parse(docstring)[0]
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

    def testObjectIdentityStatus(self):
        # Use a value other than "current" in this test, as "current" is the
        # default pysnmp value (which could mean the test value was never set).
        self.assertEqual(self.ctx["testObject"].getStatus(), "obsolete", "bad STATUS")

    def testObjectIdentityDescription(self):
        self.assertEqual(
            self.ctx["testObject"].getDescription(),
            "\\'Initial' version",
            "bad DESCRIPTION",
        )

    def testObjectIdentityReference(self):
        self.assertEqual(self.ctx["testObject"].getReference(), "\n", "bad REFERENCE")


class ObjectIdentityNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        OBJECT-IDENTITY
    FROM SNMPv2-SMI;

    testObject OBJECT-IDENTITY
        STATUS          deprecated
        DESCRIPTION     "Initial version"
        REFERENCE       "ABC"

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

    def testObjectIdentityStatus(self):
        # "current" is the default pysnmp value, and therefore what we get if
        # we request that texts not be loaded.
        self.assertEqual(self.ctx["testObject"].getStatus(), "current", "bad STATUS")

    def testObjectIdentityDescription(self):
        self.assertEqual(
            self.ctx["testObject"].getDescription(),
            "",
            "bad DESCRIPTION",
        )

    def testObjectIdentityReference(self):
        self.assertEqual(self.ctx["testObject"].getReference(), "", "bad REFERENCE")


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
