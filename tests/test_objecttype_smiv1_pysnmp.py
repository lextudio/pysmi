#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof; Copyright 2022-2024, others
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys

try:
    import unittest2 as unittest

except ImportError:
    import unittest

from pysmi.parser.smi import parserFactory
from pysmi.parser.dialect import smi_v1_relaxed
from pysmi.codegen.pysnmp import PySnmpCodeGen
from pysmi.codegen.symtable import SymtableCodeGen
from pysnmp.smi.builder import MibBuilder


class ObjectTypeMibTableTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM RFC-1212;

      testTable OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test table"
      ::= { 1 3 }

      testEntry OBJECT-TYPE
        SYNTAX          TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test row"
        INDEX           { INTEGER }
      ::= { testTable 1 }

      TestEntry ::= SEQUENCE {
            testIndex   INTEGER,
            testValue   OCTET STRING
      }

      testIndex OBJECT-TYPE
        SYNTAX          INTEGER
        ACCESS          read-write
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { testEntry 1 }

      testValue OBJECT-TYPE
        SYNTAX          OCTET STRING
        ACCESS          read-write
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { testEntry 2 }

    END
    """

    def setUp(self):
        ast = parserFactory(**smi_v1_relaxed)().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeTableClass(self):
        self.assertEqual(
            self.ctx["testTable"].__class__.__name__, "MibTable", "bad table class"
        )

    def testObjectTypeTableRowClass(self):
        self.assertEqual(
            self.ctx["testEntry"].__class__.__name__,
            "MibTableRow",
            "bad table row class",
        )

    def testObjectTypeTableColumnClass(self):
        self.assertEqual(
            self.ctx["testIndex"].__class__.__name__,
            "MibTableColumn",
            "bad table column class",
        )

    def testObjectTypeTableColumnAccess(self):
        self.assertEqual(
            self.ctx["testIndex"].getMaxAccess(),
            "read-write",
            "bad table column access",
        )

    def testObjectTypeTableColumnStatus(self):
        self.assertEqual(
            self.ctx["testIndex"].getStatus(), "mandatory", "bad table column status"
        )

    def testObjectTypeTableRowIndex(self):
        self.assertEqual(
            self.ctx["testEntry"].getIndexNames(),
            ((0, "TEST-MIB", "pysmiFakeCol1"),),
            "bad table index",
        )

    def testObjectTypeTableRowIndexClass(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntax(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getSyntax().__class__.__name__,
            "Integer32",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexName(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getName(), (1, 3, 1, 4294967295), "bad index name"
        )

    def testObjectTypeTableRowIndexAccess(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getMaxAccess(),
            "not-accessible",
            "bad index access",
        )

    def testObjectTypeTableRowIndexStatus(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getStatus(), "mandatory", "bad index status"
        )


class ObjectTypeMibTableMultipleIndicesTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM RFC-1212;

      testTable OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test table"
      ::= { 1 3 }

      testEntry OBJECT-TYPE
        SYNTAX          TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test row"
        INDEX           { IpAddress, testIndex, OCTET STRING, NetworkAddress }
      ::= { testTable 3 }

      TestEntry ::= SEQUENCE {
            testIndex   INTEGER,
            testValue   OCTET STRING
      }

      testIndex OBJECT-TYPE
        SYNTAX          INTEGER
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { testEntry 1 }

      testValue OBJECT-TYPE
        SYNTAX          OCTET STRING
        ACCESS          read-write
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { testEntry 2 }

    END
    """

    def setUp(self):
        ast = parserFactory(**smi_v1_relaxed)().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {}, genTexts=True)
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(
            ast, {mibInfo.name: symtable}, genTexts=True
        )
        codeobj = compile(pycode, "test", "exec")

        mibBuilder = MibBuilder()
        mibBuilder.loadTexts = True

        self.ctx = {"mibBuilder": mibBuilder}

        exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeTableRowIndex(self):
        self.assertEqual(
            self.ctx["testEntry"].getIndexNames(),
            (
                (0, "TEST-MIB", "pysmiFakeCol1"),
                (0, "TEST-MIB", "testIndex"),
                (0, "TEST-MIB", "pysmiFakeCol2"),
                (0, "TEST-MIB", "pysmiFakeCol3"),
            ),
            "bad multiple table indices",
        )

    def testObjectTypeTableRowIndexClass1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntax1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getSyntax().__class__.__name__,
            "IpAddress",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexName1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getName(), (1, 3, 3, 4294967295), "bad index name"
        )

    def testObjectTypeTableRowIndexClassTest(self):
        self.assertEqual(
            self.ctx["testIndex"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntaxTest(self):
        self.assertEqual(
            self.ctx["testIndex"].getSyntax().__class__.__name__,
            "Integer32",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexNameTest(self):
        self.assertEqual(
            self.ctx["testIndex"].getName(), (1, 3, 3, 1), "bad index name"
        )

    def testObjectTypeTableRowIndexClass2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntax2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].getSyntax().__class__.__name__,
            "OctetString",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexName2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].getName(), (1, 3, 3, 4294967294), "bad index name"
        )

    def testObjectTypeTableRowIndexClass3(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol3"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntax3(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol3"].getSyntax().__class__.__name__,
            "IpAddress",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexName3(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol3"].getName(), (1, 3, 3, 4294967293), "bad index name"
        )


class ObjectTypeMultipleMibTablesTestCase(unittest.TestCase):
    """
    TEST-MIB DEFINITIONS ::= BEGIN
    IMPORTS
      OBJECT-TYPE
        FROM RFC-1212;

      testTable OBJECT-TYPE
        SYNTAX          SEQUENCE OF TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test table"
      ::= { 1 3 }

      testEntry OBJECT-TYPE
        SYNTAX          TestEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test row"
        INDEX           { INTEGER }
      ::= { testTable 1 }

      TestEntry ::= SEQUENCE {
            testIndex   INTEGER
      }

      testIndex OBJECT-TYPE
        SYNTAX          INTEGER
        ACCESS          read-write
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { testEntry 1 }

      otherTable OBJECT-TYPE
        SYNTAX          SEQUENCE OF OtherEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test table"
      ::= { 1 4 }

      otherEntry OBJECT-TYPE
        SYNTAX          OtherEntry
        ACCESS          not-accessible
        STATUS          mandatory
        DESCRIPTION     "Test row"
        INDEX           { OCTET STRING }
      ::= { otherTable 1 }

      OtherEntry ::= SEQUENCE {
            otherValue   INTEGER
      }

      otherValue OBJECT-TYPE
        SYNTAX          INTEGER
        ACCESS          read-write
        STATUS          mandatory
        DESCRIPTION     "Test column"
      ::= { otherEntry 2 }

    END
    """

    def setUp(self):
        ast = parserFactory(**smi_v1_relaxed)().parse(self.__class__.__doc__)[0]
        mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})
        self.mibInfo, pycode = PySnmpCodeGen().gen_code(ast, {mibInfo.name: symtable})
        codeobj = compile(pycode, "test", "exec")

        self.ctx = {"mibBuilder": MibBuilder()}

        exec(codeobj, self.ctx, self.ctx)

    def testObjectTypeTableRowIndexClass1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexName1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getName(), (1, 3, 1, 4294967295), "bad index name"
        )

    def testObjectTypeTableRowIndexSyntax1(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol1"].getSyntax().__class__.__name__,
            "Integer32",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexClass2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].__class__.__name__,
            "MibTableColumn",
            "bad index class",
        )

    def testObjectTypeTableRowIndexSyntax2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].getSyntax().__class__.__name__,
            "OctetString",
            "bad index syntax",
        )

    def testObjectTypeTableRowIndexName2(self):
        self.assertEqual(
            self.ctx["pysmiFakeCol2"].getName(), (1, 4, 1, 4294967295), "bad index name"
        )


suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite)
