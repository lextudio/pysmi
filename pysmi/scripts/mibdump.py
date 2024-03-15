#!/usr/bin/env python
#
# This file is part of pysmi software.
#
# Copyright (c) 2015-2019, Ilya Etingof <etingof@gmail.com>
# License: https://www.pysnmp.com/pysmi/license.html
#
# SNMP SMI/MIB data management tool
#
import os
import sys
import getopt
from pathlib import Path
from pysmi.reader import getReadersFromUrls
from pysmi.searcher import (
    AnyFileSearcher,
    PyFileSearcher,
    PyPackageSearcher,
    StubSearcher,
)
from pysmi.borrower import AnyFileBorrower, PyFileBorrower
from pysmi.writer import PyFileWriter, FileWriter, CallbackWriter
from pysmi.parser import SmiV1CompatParser
from pysmi.codegen import PySnmpCodeGen, JsonCodeGen, NullCodeGen
from pysmi.compiler import MibCompiler
from pysmi import debug
from pysmi import error


def start():
    # sysexits.h
    EX_OK = 0
    EX_USAGE = 64
    EX_SOFTWARE = 70
    EX_MIB_MISSING = 79
    EX_MIB_FAILED = 79

    # Defaults
    verboseFlag = True
    strictFlag = False
    mibSources = []
    doFuzzyMatchingFlag = True
    mibSearchers = []
    mibStubs = []
    mibBorrowers = []
    dstFormat = None
    dstDirectory = None
    cacheDirectory = ""
    nodepsFlag = False
    rebuildFlag = False
    dryrunFlag = False
    genMibTextsFlag = False
    keepTextsLayout = False
    pyCompileFlag = True
    pyOptimizationLevel = 0
    ignoreErrorsFlag = False
    buildIndexFlag = False
    writeMibsFlag = True

    helpMessage = f"""\
    Usage: {sys.argv[0]} [--help]
        [--version]
        [--quiet]
        [--strict]
        [--debug=<{"|".join(sorted(debug.flagMap))}>]
        [--mib-source=<URI>]
        [--mib-searcher=<PATH|PACKAGE>]
        [--mib-stub=<MIB-NAME>]
        [--mib-borrower=<PATH>]
        [--destination-format=<FORMAT>]
        [--destination-directory=<DIRECTORY>]
        [--cache-directory=<DIRECTORY>]
        [--disable-fuzzy-source]
        [--no-dependencies]
        [--no-python-compile]
        [--python-optimization-level]
        [--ignore-errors]
        [--build-index]
        [--rebuild]
        [--dry-run]
        [--no-mib-writes]
        [--generate-mib-texts]
        [--keep-texts-layout]
        <MIB-NAME> [MIB-NAME [...]]]
    Where:
        URI      - file, zip, http, https schemes are supported.
                Use @mib@ placeholder token in URI to refer directly to
                the required MIB module when source does not support
                directory listing (e.g. HTTP).
        FORMAT   - pysnmp, json, null"""


    try:
        opts, inputMibs = getopt.getopt(
            sys.argv[1:],
            "hv",
            [
                "help",
                "version",
                "quiet",
                "strict",
                "debug=",
                "mib-source=",
                "mib-searcher=",
                "mib-stub=",
                "mib-borrower=",
                "destination-format=",
                "destination-directory=",
                "cache-directory=",
                "no-dependencies",
                "no-python-compile",
                "python-optimization-level=",
                "ignore-errors",
                "build-index",
                "rebuild",
                "dry-run",
                "no-mib-writes",
                "generate-mib-texts",
                "disable-fuzzy-source",
                "keep-texts-layout",
            ],
        )

    except getopt.GetoptError:
        if verboseFlag:
            sys.stderr.write(f"ERROR: {sys.exc_info()[1]}{os.linesep}{helpMessage}{os.linesep}")

        sys.exit(EX_USAGE)

    for opt in opts:
        if opt[0] == "-h" or opt[0] == "--help":
            sys.stderr.write(
                f"""\
    Synopsis:
    SNMP SMI/MIB files conversion tool
    Documentation:
    https://www.pysnmp.com/pysmi
    {helpMessage}
    """
            )
            sys.exit(EX_OK)

        if opt[0] == "-v" or opt[0] == "--version":
            from pysmi import __version__

            sys.stderr.write(
                f"""\
    SNMP SMI/MIB library version {__version__}, written by Ilya Etingof <etingof@gmail.com>
    Python interpreter: {sys.version}
    Software documentation and support at https://www.pysnmp.com/pysmi
    {helpMessage}
    """
            )
            sys.exit(EX_OK)

        if opt[0] == "--quiet":
            verboseFlag = False

        if opt[0] == "--strict":
            strictFlag = True

        if opt[0] == "--debug":
            debug.setLogger(debug.Debug(*opt[1].split(",")))

        if opt[0] == "--mib-source":
            mibSources.append(opt[1])

        if opt[0] == "--mib-searcher":
            mibSearchers.append(opt[1])

        if opt[0] == "--mib-stub":
            mibStubs.append(opt[1])

        if opt[0] == "--mib-borrower":
            mibBorrowers.append((opt[1], genMibTextsFlag))

        if opt[0] == "--destination-format":
            dstFormat = opt[1]

        if opt[0] == "--destination-directory":
            dstDirectory = opt[1]

        if opt[0] == "--cache-directory":
            cacheDirectory = opt[1]

        if opt[0] == "--no-dependencies":
            nodepsFlag = True

        if opt[0] == "--no-python-compile":
            pyCompileFlag = False

        if opt[0] == "--python-optimization-level":
            try:
                pyOptimizationLevel = int(opt[1])

            except ValueError:
                sys.stderr.write(
                    f"ERROR: known Python optimization levels: -1, 0, 1, 2{os.linesep}{helpMessage}{os.linesep}"
                )
                sys.exit(EX_USAGE)

        if opt[0] == "--ignore-errors":
            ignoreErrorsFlag = True

        if opt[0] == "--build-index":
            buildIndexFlag = True

        if opt[0] == "--rebuild":
            rebuildFlag = True

        if opt[0] == "--dry-run":
            dryrunFlag = True

        if opt[0] == "--no-mib-writes":
            writeMibsFlag = False

        if opt[0] == "--generate-mib-texts":
            genMibTextsFlag = True

        if opt[0] == "--disable-fuzzy-source":
            doFuzzyMatchingFlag = False

        if opt[0] == "--keep-texts-layout":
            keepTextsLayout = True

    if not mibSources:
        mibSources = [
            "file:///usr/share/snmp/mibs",
            "https://mibs.pysnmp.com/asn1/@mib@",
        ]

    if inputMibs:
        mibSources = (
            sorted(
                {
                    Path(x.replace("file:///", "")).resolve().parent.as_uri()
                    for x in inputMibs
                    if "\\" in x or "/" in x
                }
            )
            + mibSources
        )

        inputMibs = [os.path.basename(os.path.splitext(x)[0]) for x in inputMibs]

    if not inputMibs:
        sys.stderr.write(
            f"ERROR: MIB module names not specified{os.linesep}{helpMessage}{os.linesep}"
        )
        sys.exit(EX_USAGE)

    if not dstFormat:
        dstFormat = "pysnmp"

    if dstFormat == "pysnmp":
        if not mibSearchers:
            mibSearchers = PySnmpCodeGen.defaultMibPackages

        if not mibStubs:
            mibStubs = [
                x for x in PySnmpCodeGen.baseMibs if x not in PySnmpCodeGen.fakeMibs
            ]

        if not mibBorrowers:
            mibBorrowers = [
                ("https://mibs.pysnmp.com:443/mibs/notexts/@mib@", False),
                ("https://mibs.pysnmp.com:443/mibs/fulltexts/@mib@", True),
            ]

        if not dstDirectory:
            dstDirectory = os.path.expanduser("~")
            if sys.platform[:3] == "win":
                dstDirectory = os.path.join(
                    dstDirectory, "PySNMP Configuration", "mibs"
                )
            else:
                dstDirectory = os.path.join(dstDirectory, ".pysnmp", "mibs")

        # Compiler infrastructure

        borrowers = [
            PyFileBorrower(x[1], genTexts=mibBorrowers[x[0]][1])
            for x in enumerate(
                getReadersFromUrls(
                    *[m[0] for m in mibBorrowers], **dict(lowcaseMatching=False)
                )
            )
        ]

        searchers = [PyFileSearcher(dstDirectory)]

        for mibSearcher in mibSearchers:
            searchers.append(PyPackageSearcher(mibSearcher))

        searchers.append(StubSearcher(*mibStubs))

        codeGenerator = PySnmpCodeGen()
        codeGenerator.strictCompliance = strictFlag

        fileWriter = PyFileWriter(dstDirectory).setOptions(
            pyCompile=pyCompileFlag, pyOptimizationLevel=pyOptimizationLevel
        )

    elif dstFormat == "json":
        if not mibStubs:
            mibStubs = JsonCodeGen.baseMibs

        if not mibBorrowers:
            mibBorrowers = [
                ("https://mibs.pysnmp.com/json/notexts/@mib@", False),
                ("https://mibs.pysnmp.com/fulltexts/@mib@", True),
            ]

        if not dstDirectory:
            dstDirectory = os.path.join(".")

        # Compiler infrastructure

        borrowers = [
            AnyFileBorrower(x[1], genTexts=mibBorrowers[x[0]][1]).setOptions(
                exts=[".json"]
            )
            for x in enumerate(
                getReadersFromUrls(
                    *[m[0] for m in mibBorrowers], **dict(lowcaseMatching=False)
                )
            )
        ]

        searchers = [
            AnyFileSearcher(dstDirectory).setOptions(exts=[".json"]),
            StubSearcher(*mibStubs),
        ]

        codeGenerator = JsonCodeGen()
        codeGenerator.strictCompliance = strictFlag

        fileWriter = FileWriter(dstDirectory).setOptions(suffix=".json")

    elif dstFormat == "null":
        if not mibStubs:
            mibStubs = NullCodeGen.baseMibs

        if not mibBorrowers:
            mibBorrowers = [
                ("https://mibs.pysnmp.com/null/notexts/@mib@", False),
                ("https://mibs.pysnmp.com/null/fulltexts/@mib@", True),
            ]

        if not dstDirectory:
            dstDirectory = ""

        # Compiler infrastructure

        codeGenerator = NullCodeGen()

        searchers = [StubSearcher(*mibStubs)]

        borrowers = [
            AnyFileBorrower(x[1], genTexts=mibBorrowers[x[0]][1])
            for x in enumerate(
                getReadersFromUrls(
                    *[m[0] for m in mibBorrowers], **dict(lowcaseMatching=False)
                )
            )
        ]

        fileWriter = CallbackWriter(lambda *x: None)

    else:
        sys.stderr.write(
            f"ERROR: unknown destination format: {dstFormat}{os.linesep}{helpMessage}{os.linesep}"
        )
        sys.exit(EX_USAGE)

    if verboseFlag:
        sys.stderr.write(
            f"""\
Source MIB repositories: {', '.join(mibSources)}
Borrow missing/failed MIBs from: {', '.join([x[0] for x in mibBorrowers if x[1] == genMibTextsFlag])}
Existing/compiled MIB locations: {', '.join(mibSearchers)}
Compiled MIBs destination directory: {dstDirectory}
MIBs excluded from code generation: {', '.join(sorted(mibStubs))}
MIBs to compile: {', '.join(inputMibs)}
Destination format: {dstFormat}
Parser grammar cache directory: {cacheDirectory or "not used"}
Also compile all relevant MIBs: {"no" if nodepsFlag else "yes"}
Rebuild MIBs regardless of age: {"yes" if rebuildFlag else "no"}
Dry run mode: {"yes" if dryrunFlag else "no"}
Create/update MIBs: {"yes" if writeMibsFlag else "no"}
Byte-compile Python modules: {"yes" if dstFormat == "pysnmp" and pyCompileFlag else "no"} (optimization level {"yes" if dstFormat == "pysnmp" and pyOptimizationLevel else "no"})
Ignore compilation errors: {"yes" if ignoreErrorsFlag else "no"}
Generate OID->MIB index: {"yes" if buildIndexFlag else "no"}
Generate texts in MIBs: {"yes" if genMibTextsFlag else "no"}
Keep original texts layout: {"yes" if keepTextsLayout else "no"}
Try various file names while searching for MIB module: {"yes" if doFuzzyMatchingFlag else "no"}
"""
        )

    # Initialize compiler infrastructure

    mibCompiler = MibCompiler(
        SmiV1CompatParser(tempdir=cacheDirectory), codeGenerator, fileWriter
    )

    try:
        mibCompiler.addSources(
            *getReadersFromUrls(*mibSources, **dict(fuzzyMatching=doFuzzyMatchingFlag))
        )

        mibCompiler.addSearchers(*searchers)

        mibCompiler.addBorrowers(*borrowers)

        processed = mibCompiler.compile(
            *inputMibs,
            **dict(
                noDeps=nodepsFlag,
                rebuild=rebuildFlag,
                dryRun=dryrunFlag,
                genTexts=genMibTextsFlag,
                textFilter=keepTextsLayout and (lambda symbol, text: text) or None,
                writeMibs=writeMibsFlag,
                ignoreErrors=ignoreErrorsFlag,
            ),
        )

        safe = {}
        sorted_files = sorted(processed)
        for x in sorted_files:
            if processed[x] != "failed":
                safe[x] = processed[x]

        if buildIndexFlag:
            mibCompiler.buildIndex(safe, dryRun=dryrunFlag, ignoreErrors=True)

    except error.PySmiError:
        sys.stderr.write(f"ERROR: {sys.exc_info()[1]}{os.linesep}")
        sys.exit(EX_SOFTWARE)

    else:
        compiled = [x for x in sorted_files if processed[x] == "compiled"]
        borrowed = [x for x in sorted_files if processed[x] == 'borrowed']
        untouched = [x for x in sorted_files if processed[x] == 'untouched']
        missing = [x for x in sorted_files if processed[x] == 'missing']
        unprocessed = [x for x in sorted_files if processed[x] == 'unprocessed']
        failed = [x for x in sorted_files if processed[x] == 'failed']
        if verboseFlag:
            sys.stdout.write(
                f"{'Would be c' if dryrunFlag else 'C'}reated/updated MIBs: {', '.join([f'{x}{'' if x == processed[x].alias else f' ({processed[x].alias})'}' for x in compiled])}{os.linesep}"
            )
            sys.stdout.write(
                f"Pre-compiled MIBs {'Would be ' if dryrunFlag else ''}borrowed: "
                f"{', '.join([f'{x} ({processed[x].path})' for x in borrowed])}{os.linesep}"
            )
            sys.stdout.write(
                f"Up to date MIBs: {', '.join(x for x in untouched)}{os.linesep}")
            sys.stderr.write(
                f"Missing source MIBs: {f'{os.linesep} '.join(x for x in missing)}{os.linesep}")
            sys.stderr.write(
                f"Ignored MIBs: {', '.join(x for x in unprocessed)}{os.linesep}")
            sys.stderr.write(
                f"Failed MIBs: "
                f"{f'{os.linesep} '.join([f'{x} ({processed[x].error})' for x in failed])}{os.linesep}"
            )


        exitCode = EX_OK

        if len(missing) > 0:
            exitCode = EX_MIB_MISSING

        if len(failed) > 0:
            exitCode = EX_MIB_FAILED

        sys.exit(exitCode)
