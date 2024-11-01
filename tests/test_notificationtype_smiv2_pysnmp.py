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


class NotificationTypeTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-TYPE
        FROM SNMPv2-SMI;

    testNotificationType NOTIFICATION-TYPE
       OBJECTS         {
                            testChangeConfigType,
                            testChangeConfigValue
                        }
        STATUS          current
        DESCRIPTION
            "A collection of test notification types."
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

    def testNotificationTypeSymbol(self):
        self.assertTrue("testNotificationType" in self.ctx, "symbol not present")

    def testNotificationTypeName(self):
        self.assertEqual(self.ctx["testNotificationType"].getName(), (1, 3), "bad name")

    def testNotificationTypeStatus(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getStatus(), "current", "bad STATUS"
        )

    def testNotificationTypeDescription(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getDescription(),
            "A collection of test notification types.",
            "bad DESCRIPTION",
        )

    def testNotificationTypeObjects(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getObjects(),
            (
                ("TEST-MIB", "testChangeConfigType"),
                ("TEST-MIB", "testChangeConfigValue"),
            ),
            "bad OBJECTS",
        )

    def testNotificationTypeClass(self):
        self.assertEqual(
            self.ctx["testNotificationType"].__class__.__name__,
            "NotificationType",
            "bad SYNTAX class",
        )


class NotificationTypeHyphenTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-TYPE
        FROM SNMPv2-SMI;

    test-notification-type NOTIFICATION-TYPE
       OBJECTS         {
                            test-change-config-type,
                            as                        -- a reserved Python keyword
                        }
        STATUS          current
        DESCRIPTION
            "A collection of test notification types."
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

    def testNotificationTypeSymbol(self):
        self.assertTrue("test_notification_type" in self.ctx, "symbol not present")

    def testNotificationTypeLabel(self):
        self.assertEqual(
            self.ctx["test_notification_type"].getLabel(),
            "test-notification-type",
            "bad name",
        )

    def testNotificationTypeObjects(self):
        self.assertEqual(
            self.ctx["test_notification_type"].getObjects(),
            (
                ("TEST-MIB", "test-change-config-type"),
                ("TEST-MIB", "as"),
            ),
            "bad OBJECTS",
        )


class NotificationTypeTextTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-TYPE
        FROM SNMPv2-SMI;

    testNotificationType NOTIFICATION-TYPE
        OBJECTS         {
                            testChangeConfigType,
                            testChangeConfigValue
                        }
        STATUS          deprecated
        DESCRIPTION
            "A collection of \\ test notification types.\\"
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

    def testNotificationTypeStatus(self):
        # Use a value other than "current" in this test, as "current" is the
        # default pysnmp value (which could mean the test value was never set).
        self.assertEqual(
            self.ctx["testNotificationType"].getStatus(), "deprecated", "bad STATUS"
        )

    def testNotificationTypeDescription(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getDescription(),
            "A collection of \\ test notification types.\\",
            "bad DESCRIPTION",
        )


class NotificationTypeNoLoadTextsTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      NOTIFICATION-TYPE
        FROM SNMPv2-SMI;

    testNotificationType NOTIFICATION-TYPE
       OBJECTS         {
                            testChangeConfigType,
                            testChangeConfigValue
                        }
        STATUS          obsolete
        DESCRIPTION
            "A collection of test notification types."
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

    def testNotificationTypeStatus(self):
        # "current" is the default pysnmp value, and therefore what we get if
        # we request that texts not be loaded.
        self.assertEqual(
            self.ctx["testNotificationType"].getStatus(), "current", "bad STATUS"
        )

    def testNotificationTypeDescription(self):
        self.assertEqual(
            self.ctx["testNotificationType"].getDescription(),
            "",
            "bad DESCRIPTION",
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
