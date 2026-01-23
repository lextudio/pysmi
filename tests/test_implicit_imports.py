import unittest

from pysmi import error
from pysmi.parser.smi import parserFactory
from pysmi.codegen.symtable import SymtableCodeGen
from pysmi import implicit_imports


BROKEN_MIB = """
BROKEN-MIB DEFINITIONS ::= BEGIN

TestTC ::= TEXTUAL-CONVENTION
    STATUS      current
    DESCRIPTION "Test TC using Opaque without importing it"
    SYNTAX      Opaque (SIZE(4..11))

END
"""


class ImplicitImportTestCase(unittest.TestCase):
    def test_raises_without_implicit_import(self):
        ast = parserFactory()().parse(BROKEN_MIB)[0]
        # ensure no implicit import configured
        implicit_imports.IMPLICIT_IMPORTS.pop("BROKEN-MIB", None)

        with self.assertRaises(error.PySmiSemanticError):
            SymtableCodeGen().gen_code(ast, {})

    def test_succeeds_with_implicit_import(self):
        ast = parserFactory()().parse(BROKEN_MIB)[0]

        # install per-MIB implicit import and ensure cleanup
        prev = implicit_imports.IMPLICIT_IMPORTS.get("BROKEN-MIB")
        implicit_imports.IMPLICIT_IMPORTS["BROKEN-MIB"] = [("SNMPv2-SMI", "Opaque")]
        try:
            mibInfo, symtable = SymtableCodeGen().gen_code(ast, {})
            # SNMPv2-SMI should now be reported as an imported module
            self.assertIn("SNMPv2-SMI", mibInfo.imported)
        finally:
            if prev is None:
                implicit_imports.IMPLICIT_IMPORTS.pop("BROKEN-MIB", None)
            else:
                implicit_imports.IMPLICIT_IMPORTS["BROKEN-MIB"] = prev


if __name__ == "__main__":
    unittest.main()
