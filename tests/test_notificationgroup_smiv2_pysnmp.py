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


class NotificationGroupTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-GROUP
        FROM SNMPv2-CONF;

    testNotificationGroup NOTIFICATION-GROUP
       NOTIFICATIONS    {
                            testStatusChangeNotify,
                            testClassEventNotify,
                            testThresholdBelowNotify
                        }
        STATUS          current
        DESCRIPTION
            "A collection of test notifications."
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

    def testNotificationGroupSymbol(self):
        self.assertTrue("testNotificationGroup" in self.ctx, "symbol not present")

    def testNotificationGroupName(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getName(), (1, 3), "bad name"
        )

    def testNotificationGroupStatus(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getStatus(),
            "current",
            "bad STATUS",
        )

    def testNotificationGroupDescription(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getDescription(),
            "A collection of test notifications.",
            "bad DESCRIPTION",
        )

    def testNotificationGroupObjects(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getObjects(),
            (
                ("TEST-MIB", "testStatusChangeNotify"),
                ("TEST-MIB", "testClassEventNotify"),
                ("TEST-MIB", "testThresholdBelowNotify"),
            ),
            "bad OBJECTS",
        )

    def testNotificationGroupClass(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].__class__.__name__,
            "NotificationGroup",
            "bad SYNTAX class",
        )


class NotificationGroupHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-GROUP
        FROM SNMPv2-CONF;

    test-notification-group NOTIFICATION-GROUP
       NOTIFICATIONS    {
                            test-status-change-notify
                        }
        STATUS          current
        DESCRIPTION
            "A collection of test notifications."
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

    def testNotificationGroupSymbol(self):
        self.assertTrue("test_notification_group" in self.ctx, "symbol not present")

    def testNotificationGroupLabel(self):
        self.assertEqual(
            self.ctx["test_notification_group"].getLabel(),
            "test-notification-group",
            "bad label",
        )

    def testNotificationGroupObjects(self):
        self.assertEqual(
            self.ctx["test_notification_group"].getObjects(),
            (("TEST-MIB", "test-status-change-notify"),),
            "bad OBJECTS",
        )


class NotificationGroupTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-GROUP
        FROM SNMPv2-CONF;

    testNotificationGroup NOTIFICATION-GROUP
       NOTIFICATIONS    {
                            testStatusChangeNotify,
                            testClassEventNotify,
                            testThresholdBelowNotify
                        }
        STATUS          obsolete
        DESCRIPTION     "A collection of \\n test
     notifications."
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

    def testNotificationGroupStatus(self):
        # Use a value other than "current" in this test, as "current" is the
        # default pysnmp value (which could mean the test value was never set).
        self.assertEqual(
            self.ctx["testNotificationGroup"].getStatus(),
            "obsolete",
            "bad STATUS",
        )

    def testNotificationGroupDescription(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getDescription(),
            "A collection of \\n test\n notifications.",
            "bad DESCRIPTION",
        )


class NotificationGroupNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-GROUP
        FROM SNMPv2-CONF;

    testNotificationGroup NOTIFICATION-GROUP
       NOTIFICATIONS    {
                            testStatusChangeNotify,
                            testClassEventNotify,
                            testThresholdBelowNotify
                        }
        STATUS          deprecated
        DESCRIPTION
            "A collection of test notifications."
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

    def testNotificationGroupStatus(self):
        # "current" is the default pysnmp value, and therefore what we get if
        # we request that texts not be loaded.
        self.assertEqual(
            self.ctx["testNotificationGroup"].getStatus(),
            "current",
            "bad STATUS",
        )

    def testNotificationGroupDescription(self):
        self.assertEqual(
            self.ctx["testNotificationGroup"].getDescription(),
            "",
            "bad DESCRIPTION",
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
