import types
import unittest

from pysmi.parser.smi import parserFactory
from pysmi.codegen.symtable import SymtableCodeGen
from pysmi import implicit_imports


PROBLEM_MIB = """
PROBLEM-MIB DEFINITIONS ::= BEGIN

TestType ::= TEXTUAL-CONVENTION
    STATUS current
    DESCRIPTION "Test textual convention"
    SYNTAX UnknownType

testObject OBJECT-TYPE
    SYNTAX TestType
    MAX-ACCESS read-only
    STATUS current
    DESCRIPTION "Test"
    ::= { 1 3 }

END
"""


class GenCodeRetryImplicitTestCase(unittest.TestCase):
    def test_gen_code_retries_with_implicit_imports(self):
        # Set implicit import mapping for this MIB (won't be applied on first pass)
        prev = implicit_imports.IMPLICIT_IMPORTS.get("PROBLEM-MIB")
        implicit_imports.IMPLICIT_IMPORTS["PROBLEM-MIB"] = [
            ("SNMPv2-TC", "UnknownType")
        ]

        try:
            sc = SymtableCodeGen()
            sc.moduleName[0] = "PROBLEM-MIB"

            # wrap gen_imports to record calls and their apply_implicit flag
            calls = []
            original = SymtableCodeGen.gen_imports

            def wrapped(self, imports, apply_implicit=False):
                calls.append(bool(apply_implicit))
                return original(self, imports, apply_implicit)

            sc.gen_imports = types.MethodType(wrapped, sc)

            ast = parserFactory()().parse(PROBLEM_MIB)[0]

            # Should not raise: first pass fails then retry with implicit imports
            mibInfo, symtable = sc.gen_code(ast, {})

            # Ensure retry occurred (apply_implicit True was used at least once)
            self.assertIn(True, calls)

            # And resulting MIB should list the imported module used for implicit import
            self.assertIn("SNMPv2-TC", mibInfo.imported)

        finally:
            if prev is None:
                implicit_imports.IMPLICIT_IMPORTS.pop("PROBLEM-MIB", None)
            else:
                implicit_imports.IMPLICIT_IMPORTS["PROBLEM-MIB"] = prev


if __name__ == "__main__":
    unittest.main()
