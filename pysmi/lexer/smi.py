#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
"""Legacy standalone lexer compatibility shim."""

from pysmi import error
from pysmi.lexer.base import AbstractLexer


def _disconnected_message():
    return (
        "Standalone lexer support has been removed. "
        "Use parserFactory() from pysmi.parser.smi."
    )


class SmiV2Lexer(AbstractLexer):
    def __init__(self, *args, **kwargs):
        raise error.PySmiError(_disconnected_message())

    def reset(self):
        raise error.PySmiError(_disconnected_message())


def lexerFactory(**grammarOptions):
    raise error.PySmiError(_disconnected_message())
