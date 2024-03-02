#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
from pysmi import error
from pysmi import debug


class AbstractBorrower:
    genTexts = False
    exts = ''

    def __init__(self, reader, genTexts=False):
        """Creates an instance of *Borrower* class.

           Args:
               reader: a *reader* object

           Keyword Args:
               genText: indicates whether this borrower should be looking
                        for transformed MIBs that include human-oriented texts
        """
        if genTexts is not None:
            self.genTexts = genTexts

        self._reader = reader

    def __str__(self):
        return '{}{{{}, genTexts={}, exts={}}}'.format(self.__class__.__name__,
                                                 self._reader, self.genTexts,
                                                 self.exts)

    def setOptions(self, **kwargs):
        self._reader.setOptions(**kwargs)

        for k in kwargs:
            setattr(self, k, kwargs[k])

        return self

    def getData(self, mibname, **options):
        if bool(options.get('genTexts')) != self.genTexts:
            debug.logger & debug.flagBorrower and debug.logger(
                f'skipping incompatible borrower {self} for file {mibname}')
            raise error.PySmiFileNotFoundError(mibname=mibname, reader=self._reader)

        debug.logger & debug.flagBorrower and (
            debug.logger(f'trying to borrow file {mibname} from {self._reader}')
        )

        if 'exts' not in options:
            options['exts'] = self.exts

        return self._reader.getData(mibname, **options)
