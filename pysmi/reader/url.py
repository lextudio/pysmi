#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2020, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
import sys

from urllib import parse as urlparse
from urllib.request import url2pathname
from pysmi.reader.localfile import FileReader
from pysmi.reader.zipreader import ZipReader
from pysmi.reader.httpclient import HttpReader
from pysmi import error


def getReadersFromUrls(*sourceUrls, **options):
    readers = []
    for sourceUrl in sourceUrls:
        mibSource = urlparse.urlparse(sourceUrl)

        if mibSource.scheme in ("", "file", "zip"):
            scheme = mibSource.scheme
            filePath = url2pathname(mibSource.path)
            if scheme != "file" and (
                filePath.endswith(".zip") or filePath.endswith(".ZIP")
            ):
                scheme = "zip"

            else:
                scheme = "file"

            if scheme == "file":
                readers.append(FileReader(filePath).setOptions(**options))
            else:
                readers.append(ZipReader(filePath).setOptions(**options))

        elif mibSource.scheme in ("http", "https"):
            readers.append(HttpReader(sourceUrl).setOptions(**options))

        else:
            raise error.PySmiError("Unsupported URL scheme %s" % sourceUrl)

    return readers
