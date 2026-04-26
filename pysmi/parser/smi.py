#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
"""SMI parser entry point."""

from pysmi import error
from pysmi.parser.lark_parser import (
    SmiV2Parser as _SmiV2Parser,
    parserFactory as _defaultParserFactory,
)

SmiV2Parser = _SmiV2Parser


def parserFactory(**grammarOptions):
    """Factory function producing parser specializations."""

    backend = grammarOptions.pop("backend", None)
    if backend is None:
        return _defaultParserFactory(**grammarOptions)

    backend = str(backend).lower()

    if backend == "ply":
        raise error.PySmiError("PLY backend has been removed.")

    raise error.PySmiError(f"Unknown parser backend: {backend}")
