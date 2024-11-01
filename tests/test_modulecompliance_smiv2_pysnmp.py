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


class ModuleComplianceTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      MODULE-COMPLIANCE
        FROM SNMPv2-CONF;

    testCompliance MODULE-COMPLIANCE
     STATUS      current
     DESCRIPTION  "This is the MIB compliance statement"
     MODULE
      MANDATORY-GROUPS {
       testComplianceInfoGroup,
       testNotificationInfoGroup
      }
      GROUP     testNotificationGroup
      DESCRIPTION
            "Support for these notifications is optional."
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

    def testModuleComplianceSymbol(self):
        self.assertTrue("testCompliance" in self.ctx, "symbol not present")

    def testModuleComplianceName(self):
        self.assertEqual(self.ctx["testCompliance"].getName(), (1, 3), "bad name")

    def testModuleComplianceStatus(self):
        self.assertEqual(
            self.ctx["testCompliance"].getStatus(),
            "current",
            "bad STATUS",
        )

    def testModuleComplianceDescription(self):
        self.assertEqual(
            self.ctx["testCompliance"].getDescription(),
            "This is the MIB compliance statement",
            "bad DESCRIPTION",
        )

    def testModuleComplianceObjects(self):
        self.assertEqual(
            self.ctx["testCompliance"].getObjects(),
            (
                ("TEST-MIB", "testComplianceInfoGroup"),
                ("TEST-MIB", "testNotificationInfoGroup"),
                ("TEST-MIB", "testNotificationGroup"),
            ),
            "bad OBJECTS",
        )

    def testModuleComplianceClass(self):
        self.assertEqual(
            self.ctx["testCompliance"].__class__.__name__,
            "ModuleCompliance",
            "bad SYNTAX class",
        )


class ModuleComplianceHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      MODULE-COMPLIANCE
        FROM SNMPv2-CONF;

    test-compliance MODULE-COMPLIANCE
     STATUS      current
     DESCRIPTION  "This is the MIB compliance statement"
     MODULE
      MANDATORY-GROUPS {
       test-compliance-info-group,
       if                           -- a reserved Python keyword
      }
      GROUP     test-notification-group
      DESCRIPTION
            "Support for these notifications is optional."
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

    def testModuleComplianceSymbol(self):
        self.assertTrue("test_compliance" in self.ctx, "symbol not present")

    def testModuleComplianceLabel(self):
        self.assertEqual(
            self.ctx["test_compliance"].getLabel(), "test-compliance", "bad label"
        )

    def testModuleComplianceObjects(self):
        self.assertEqual(
            self.ctx["test_compliance"].getObjects(),
            (
                ("TEST-MIB", "test-compliance-info-group"),
                ("TEST-MIB", "if"),
                ("TEST-MIB", "test-notification-group"),
            ),
            "bad OBJECTS",
        )


class ModuleComplianceTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      MODULE-COMPLIANCE
        FROM SNMPv2-CONF;

    testCompliance MODULE-COMPLIANCE
     STATUS      deprecated
     DESCRIPTION  "This is the MIB
      compliance statement\\"
     MODULE
      MANDATORY-GROUPS {
       testComplianceInfoGroup,
       testNotificationInfoGroup
      }
      GROUP     testNotificationGroup
      DESCRIPTION
            "Support for these notifications is optional."
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

    def testModuleComplianceStatus(self):
        # Use a value other than "current" in this test, as "current" is the
        # default pysnmp value (which could mean the test value was never set).
        self.assertEqual(
            self.ctx["testCompliance"].getStatus(),
            "deprecated",
            "bad STATUS",
        )

    def testModuleComplianceDescription(self):
        self.assertEqual(
            self.ctx["testCompliance"].getDescription(),
            "This is the MIB\n  compliance statement\\",
            "bad DESCRIPTION",
        )


class ModuleComplianceNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      MODULE-COMPLIANCE
        FROM SNMPv2-CONF;

    testCompliance MODULE-COMPLIANCE
     STATUS      obsolete
     DESCRIPTION  "This is the MIB compliance statement"
     MODULE
      MANDATORY-GROUPS {
       testComplianceInfoGroup,
       testNotificationInfoGroup
      }
      GROUP     testNotificationGroup
      DESCRIPTION
            "Support for these notifications is optional."
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

    def testModuleComplianceStatus(self):
        # "current" is the default pysnmp value, and therefore what we get if
        # we request that texts not be loaded.
        self.assertEqual(
            self.ctx["testCompliance"].getStatus(),
            "current",
            "bad STATUS",
        )

    def testModuleComplianceDescription(self):
        self.assertEqual(
            self.ctx["testCompliance"].getDescription(),
            "",
            "bad DESCRIPTION",
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
