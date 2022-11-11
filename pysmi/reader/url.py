#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys

from urllib import parse as urlparse
from pysmi.reader.localfile import FileReader
from pysmi.reader.zipreader import ZipReader
from pysmi.reader.httpclient import HttpReader
from pysmi import error


def getReadersFromUrls(*sourceUrls, **options):
    readers = []
    for sourceUrl in sourceUrls:
        mibSource = urlparse.urlparse(sourceUrl)

        if mibSource.scheme in ('', 'file', 'zip'):
            scheme = mibSource.scheme
            if scheme != 'file' and (mibSource.path.endswith('.zip') or
                                     mibSource.path.endswith('.ZIP')):
                scheme = 'zip'

            else:
                scheme = 'file'

            if scheme == 'file':
                readers.append(FileReader(mibSource.path).setOptions(**options))
            else:
                readers.append(ZipReader(mibSource.path).setOptions(**options))

        elif mibSource.scheme in ('http', 'https'):
            readers.append(HttpReader(sourceUrl).setOptions(**options))

        else:
            raise error.PySmiError('Unsupported URL scheme %s' % sourceUrl)

    return readers
