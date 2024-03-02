"""
Borrow pysnmp MIBs on failure
+++++++++++++++++++++++++++++

Look up specific ASN.1 MIBs at configured Web/FTP sites.
If no required MIB is found or its compilation fails for
some reason, attempt to download precompiled version of
failed MIB and store it locally as if we had compiled it.
"""  #
from pysmi.reader import HttpReader
from pysmi.searcher import PyFileSearcher
from pysmi.searcher import StubSearcher
from pysmi.borrower import PyFileBorrower
from pysmi.writer import PyFileWriter
from pysmi.parser import SmiStarParser
from pysmi.codegen import PySnmpCodeGen
from pysmi.compiler import MibCompiler

# from pysmi import debug

# debug.setLogger(debug.Debug('borrower', 'reader', 'searcher'))

inputMibs = ["BORROWED-MIB"]
httpSources = [("mibs.pysnmp.com", 443, "/asn1/@mib@")]
httpBorrowers = [("mibs.pysnmp.com", 443, "/pysnmp/notexts/@mib@")]
dstDirectory = ".pysnmp-mibs"

# Initialize compiler infrastructure

mibCompiler = MibCompiler(SmiStarParser(), PySnmpCodeGen(), PyFileWriter(dstDirectory))

# search for source MIBs at Web sites
mibCompiler.addSources(HttpReader("https://mibs.pysnmp.com/asn1/@mib@"))

# never recompile MIBs with MACROs
mibCompiler.addSearchers(StubSearcher(*PySnmpCodeGen.baseMibs))

# check compiled/borrowed MIBs in our own productions
mibCompiler.addSearchers(PyFileSearcher(dstDirectory))

# search for compiled MIBs at Web sites if source is not available or broken
mibCompiler.addBorrowers(
    *[PyFileBorrower(HttpReader("https://mibs.pysnmp.com/notexts/@mib@"))]
)

# run non-recursive MIB compilation
results = mibCompiler.compile(*inputMibs)

print("Results: %s" % ", ".join([f"{x}:{results[x]}" for x in results]))
