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


class AgentCapabilitiesTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        MODULE-IDENTITY
            FROM SNMPv2-SMI
        AGENT-CAPABILITIES
            FROM SNMPv2-CONF;

    testCapability AGENT-CAPABILITIES
        PRODUCT-RELEASE "Test product"
        STATUS          current
        DESCRIPTION
            "test capabilities"
        REFERENCE       "test reference"

        SUPPORTS        TEST-MIB
        INCLUDES        {
                            testSystemGroup,
                            testNotificationObjectGroup,
                            testNotificationGroup
                        }
        VARIATION       testSysLevelType
        ACCESS          read-only
        DESCRIPTION
            "Not supported."

        VARIATION       testSysLevelType
        ACCESS          read-only
        DESCRIPTION
            "Supported."

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

    def testAgentCapabilitiesSymbol(self):
        self.assertTrue("testCapability" in self.ctx, "symbol not present")

    def testAgentCapabilitiesName(self):
        self.assertEqual(self.ctx["testCapability"].getName(), (1, 3), "bad name")

    def testAgentCapabilitiesStatus(self):
        self.assertEqual(
            self.ctx["testCapability"].getStatus(), "current", "bad STATUS"
        )

    def testAgentCapabilitiesDescription(self):
        self.assertEqual(
            self.ctx["testCapability"].getDescription(),
            "test capabilities",
            "bad DESCRIPTION",
        )

    def testAgentCapabilitiesReference(self):
        self.assertEqual(
            self.ctx["testCapability"].getReference(),
            "test reference",
            "bad REFERENCE",
        )

    # XXX SUPPORTS/INCLUDES/VARIATION/ACCESS not supported by pysnmp

    def testAgentCapabilitiesClass(self):
        self.assertEqual(
            self.ctx["testCapability"].__class__.__name__,
            "AgentCapabilities",
            "bad SYNTAX class",
        )


class AgentCapabilitiesHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        AGENT-CAPABILITIES
            FROM SNMPv2-CONF;

    test-capability AGENT-CAPABILITIES
        PRODUCT-RELEASE "Test product"
        STATUS          current
        DESCRIPTION
            "test capabilities"

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

    def testAgentCapabilitiesSymbol(self):
        self.assertTrue("test_capability" in self.ctx, "symbol not present")

    def testAgentCapabilitiesLabel(self):
        self.assertEqual(
            self.ctx["test_capability"].getLabel(), "test-capability", "bad label"
        )


class AgentCapabilitiesTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        MODULE-IDENTITY
            FROM SNMPv2-SMI
        AGENT-CAPABILITIES
            FROM SNMPv2-CONF;

    testCapability AGENT-CAPABILITIES
        PRODUCT-RELEASE "Test product
    Version 1.0 \\ 2024-08-20"
        STATUS          obsolete
        DESCRIPTION
    "test \\ncapabilities
    \\"
        REFERENCE       "test
    reference"

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

    def testAgentCapabilitiesStatus(self):
        # Use a value other than "current" in this test, as "current" is the
        # default pysnmp value (which could mean the test value was never set).
        self.assertEqual(
            self.ctx["testCapability"].getStatus(), "obsolete", "bad STATUS"
        )

    def testAgentCapabilitiesProductRelease(self):
        self.assertEqual(
            self.ctx["testCapability"].getProductRelease(),
            "Test product\nVersion 1.0 \\ 2024-08-20",
            "bad DESCRIPTION",
        )

    def testAgentCapabilitiesDescription(self):
        self.assertEqual(
            self.ctx["testCapability"].getDescription(),
            "test \\ncapabilities\n\\",
            "bad DESCRIPTION",
        )

    def testAgentCapabilitiesReference(self):
        self.assertEqual(
            self.ctx["testCapability"].getReference(),
            "test\nreference",
            "bad REFERENCE",
        )


class AgentCapabilitiesNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
        MODULE-IDENTITY
            FROM SNMPv2-SMI
        AGENT-CAPABILITIES
            FROM SNMPv2-CONF;

    testCapability AGENT-CAPABILITIES
        PRODUCT-RELEASE "Test product"
        STATUS          deprecated
        DESCRIPTION
            "test capabilities"
        REFERENCE       "test reference"

        SUPPORTS        TEST-MIB
        INCLUDES        {
                            testSystemGroup
                        }
        VARIATION       testSysLevelType
        ACCESS          read-only
        DESCRIPTION
            "Not supported."

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

    def testAgentCapabilitiesStatus(self):
        # "current" is the default pysnmp value, and therefore what we get if
        # we request that texts not be loaded.
        self.assertEqual(
            self.ctx["testCapability"].getStatus(), "current", "bad STATUS"
        )

    def testAgentCapabilitiesDescription(self):
        self.assertEqual(
            self.ctx["testCapability"].getDescription(),
            "",
            "bad DESCRIPTION",
        )

    def testAgentCapabilitiesReference(self):
        self.assertEqual(
            self.ctx["testCapability"].getReference(),
            "",
            "bad REFERENCE",
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
