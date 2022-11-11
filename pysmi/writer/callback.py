#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys
from pysmi.writer.base import AbstractWriter
from pysmi import debug
from pysmi import error


class CallbackWriter(AbstractWriter):
    """Invokes user-specified callable and passes transformed
       MIB module to it.

       Note: user callable object signature must be as follows

       .. function:: cbFun(mibname, contents, cbCtx)

    """

    def __init__(self, cbFun, cbCtx=None):
        """Creates an instance of *CallbackWriter* class.

        Args:
            cbFun (callable): user-supplied callable
        Keyword Args:
            cbCtx: user-supplied object passed intact to user callback
        """
        self._cbFun = cbFun
        self._cbCtx = cbCtx

    def __str__(self):
        return f'{self.__class__.__name__}{{"{self._cbFun}"}}'

    def putData(self, mibname, data, comments=(), dryRun=False):
        if dryRun:
            debug.logger & debug.flagWriter and debug.logger('dry run mode')
            return

        try:
            self._cbFun(mibname, data, self._cbCtx)

        except Exception:
            raise error.PySmiWriterError(
                f'user callback {self._cbFun} failure writing {mibname}: {sys.exc_info()[1]}', writer=self)

        debug.logger & debug.flagWriter and debug.logger('user callback for %s succeeded' % mibname)

    def getData(self, filename):
        return ''
