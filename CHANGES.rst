Revision 1.6.0, released on Apr 26, 2025
----------------------------------------

- Upgraded to match pysnmp 7.1.16 and above.

Revision 1.5.11, released on Feb 19, 2025
-----------------------------------------

- Fixed version mismatch in package.

Revision 1.5.10, released on Feb 19, 2025
-----------------------------------------

- Improved DEFVAL handling.

Revision 1.5.9, released on Nov 04, 2024
----------------------------------------

- Exposed reference property in MIB objects.

Revision 1.5.8, released on Nov 02, 2024
----------------------------------------

- Fixed fixed-length OCTET STRING handling.

Revision 1.5.7, released on Nov 01, 2024
----------------------------------------

- Various improvements in MIB parsing, including better DEFVAL handling, symbol
  name generation, and more.

Revision 1.5.6, released on Oct 29, 2024
----------------------------------------

- Improved DISPLAY-HINT support.

Revision 1.5.5, released on Oct 21, 2024
----------------------------------------

- Improved BITS type support.

Revision 1.5.4, released on Oct 14, 2024
----------------------------------------

- Fixed a runtime error in pysnmp.

Revision 1.5.3, released on Oct 14, 2024
----------------------------------------

- Fixed a runtime error in pysnmp.

Revision 1.5.2, released on Oct 14, 2024
----------------------------------------

- Fixed a few runtime errors.

Revision 1.5.1, released on Oct 13, 2024
----------------------------------------

- Removed Python 3.8 support.
- Added Python 3.13 support.
- Renamed many items to meet PEP 8 requirements. Compatibility layer is added,
  but will be removed in the next release.
- Fixed a bug that Windows version and user name were not correctly detected.

Revision 1.5.0, released on Sep 02, 2024
----------------------------------------

- Better formatting of texts in MIB documents.
- Reworked on reserved Python keywords handling.
- Fixed TEXTUAL-CONVENTION handling.
- Fixed DEFVAL handling.
- Added cyclic dependency detection.
- Other fixes and improvements for real-world MIBs.

Revision 1.4.4, released on Jul 16, 2024
----------------------------------------

- Removed package postfix. A helper release to enable migration.

Revision 1.4.3, released on Apr 03, 2024
----------------------------------------

- Fixed a bug from code merge.

Revision 1.4.2, released on Mar 25, 2024
----------------------------------------

- Implemented a better strict mode.
- Fixed a bug from code merge.

Revision 1.4.1, released on Mar 17, 2024
----------------------------------------

- Fixed old Python version support.

Revision 1.4.0, released on Mar 17, 2024
----------------------------------------

- Changed compiled Python file header comment style.

Revision 1.3.4, released on Mar 17, 2024
----------------------------------------

- Fixed a Windows path bug.

Revision 1.3.3, released on Mar 04, 2024
----------------------------------------

- Fixed Windows path handling in mibdump.

Revision 1.3.2, released on Feb 03, 2024
----------------------------------------

- Removed an unharmful error.

Revision 1.3.1, released on Feb 03, 2024
----------------------------------------

- Fixed mibdump crash.

Revision 1.3.0, released on Feb 03, 2024
----------------------------------------

- Cherry picked two patches.

Revision 1.2.0, released on Feb 03, 2024
----------------------------------------

- Fixed a JSON output bug.

Revision 1.1.13, released on Feb 11, 2023
-----------------------------------------

- Updated MIB URLs.

Revision 1.1.12, released on Dec 26, 2022
-----------------------------------------

- Migrated to new asn1 repo.
- Bumped minimal Python version to 3.7.

Revision 1.1.11, released on Nov 21, 2022
-----------------------------------------

- Revised documentation to meet the latest version.

Revision 0.4.0, released on XX-03-2020
----------------------------------------

- Introduced Jinja2 templates for code generation.

  This change significantly refactors the way how code generation
  works. Previously, pysmi code generator has been responsible for
  producing a well-formed text document (e.g. JSON or pysnmp).

  With this change, all code generations should be done through
  Jinja2 templates by rendering them in the context of the parsed MIB
  taking shape of the intermediate MIB representation which other parts
  of pysmi provide.

- By way of moving pysnmp code generation to Jinja2 template, the
  Python code layout of pysnmp modules improved dramatically - it
  is just one little step from being PEP8-compliant.

- The template-based pysnmp code generator drops some backward
  compatibility aids that keep Python MIB modules compatible with
  older pysnmp versions. Perhaps in the followup patch we should
  make the Python MIB module failing early and clearly on import
  when it's old pysnmp importing it.

- Jinja does not seem to work well with Python < 2.6 and Python == 3.2.
  Despite pysmi is trying to support those Python versions, it may
  start to fail on them due to Jinja failures.

- Introduced SNMP agent code hooks generation template allowing
  building a functional skeleton of the Python module from a
  given ASN.1 MIB. The tapping points include SMI Managed Object
  read/readnext/write/create and destroy work flows.

Revision 0.3.5, released on XX-03-2020
----------------------------------------

- Added tox runner with a handful of basic jobs
- Copyright notice extended to the year 2020
- Fixed MIB file load by URI on Windows

Revision 0.3.4, released on Apr 14, 2019
----------------------------------------

- Added `implied` key to JSON SNMP table index structure
- Rebased MIB importing code onto `importlib` because `imp` is long
  deprecated
- Fixed Py file borrower to become functional

Revision 0.3.3, released on Dec 29, 2018
----------------------------------------

- Added mibcopy.py documentation
- Copyright notice bumped up to year 2019

Revision 0.3.2, released on Oct 22, 2018
----------------------------------------

- Bumped upper Python version to 3.7 and enabled pip cache
- Exit code indication of the command-line tools aligned with
  sysexits.h to report more useful termination status

Revision 0.3.1, released on Jun 10, 2018
----------------------------------------

- Fixed pysnmp lower version in test-requirements.txt
- Fixed compiler crash when building comments at a platform which
  has broken users/groups databases

Revision 0.3.0, released on Apr 29, 2018
----------------------------------------

- The `mibcopy` tool implemented to copy MIB modules from files with
  potentially messed up names into a directory under canonical MIB
  names picking up the latest MIB revision along the way.
- ZIP archive reader implemented to pull ASN.1 MIB files from .zip
  archives pretty much in the same way as from plain directories
- HTTP/S proxy support added (through respecting `http_proxy` environment
  variable) by switching from `httplib` to `urllib2` internally
- Copyright notice bumped up to year 2018
- Project site in the docs changes from SourceForge to snmplabs.com
- PRODUCT-RELEASE generation added to the JSON code generator
- Added special handling of BITS-like DEFVAL syntax for Integers
  that occurs in buggy MIBs
- Fixed missing REVISIONS generations in MODULE-IDENTITY

Revision 0.2.2, released on Nov 13, 2017
----------------------------------------

- Library documentation refactored and updated
- Fixed malformed Python code being produced by pysnmp code generator

Revision 0.2.1, released on Nov 11, 2017
----------------------------------------

- Added MIB *status*, *product release* and *revision description* set
  calls at pysnmp code generator
- Changed REVISION field format in JSON representation - it is now
  a list of dicts each with *revision* timestamp and *description* text
- MIB REFERENCE fields are only exported if --with-mib-text is on
- Sphinx documentation theme changed to Alabaster
- Multiple fixes to pysnmp codegen not to produce function calls
  with more than 255 parameters

Revision 0.1.4, released on Oct 14, 2017
----------------------------------------

- Fix to SMI lexer to treat tokens starting from a digit as belonging
  to a lower-cased class. This fixes sub-OID parsing bug (specifically,
  802dot3(10006))
- Fix to the mibdump.py local MIB path automatic injection in front
  of existing --mib-sources

Revision 0.1.3, released on May 19, 2017
----------------------------------------

* INET-ADDRESS-MIB configured as pre-built at pysnmp codegen
* JSON codegen produces "nodetype" element for OBJECT-TYPE
* Fix to mibdump.py --destination-directory option
* Fix to pysnmp and JSON code generators to properly refer to MIB module
  defining particular MIB object

Revision 0.1.2, released on Apr 12, 2017
----------------------------------------

* The @mib@ magic in reader's URL template made optional. If it is not present,
  MIB module name is just appended to URL template
* Send User-Agent containing pysmi and Python versions as well as platform
  name.
* Fixed missing STATUS/DISPLAY-HINT/REFERENCE/etc fields generation at pysnmp
  backend when running in the non-full-text mode
* Fixed broken `ordereddict` dependency on Python 2.6-

Revision 0.1.1, released on Mar 30, 2017
----------------------------------------

* Generate REFERENCE and STATUS fields at various SMI objects
* Generate DESCRIPTION field followed REVISION field at MODULE-IDENTITY objects
* Generate PRODUCT-RELEASE field at AGENT-CAPABILITIES objects
* Generated Python source aligned with PEP8
* MIB texts cleaned up by default, --keep-texts-layout preserves original
  formatting
* Fix to the `ordereddict` conditional dependency
* Missing test module recovered
* Failing tests fixed

Revision 0.1.0, released on Mar 25, 2017
----------------------------------------

* JSON code generating backend implemented
* Experimental JSON OID->MIB indices generation implemented
* Package structure flattened for easier use
* Minor refactoring to the test suite
* Source code statically analyzed, hardened and PEP8-ized
* Files closed explicitly to mute ResourceWarnings
* Fixed to Python 2.4 (and aged ply) compatibility
* Added a workaround to avoid generating pysnmp TextualConvention classes
  inheriting from TextualConvention (when MIB defines a TEXTUAL-CONVENTION
  based on another TEXTUAL-CONVENTION as SYNTAX)
* Author's e-mail changed, copyright extended to year 2017

Revision 0.0.7, released on Feb 12, 2016
----------------------------------------

* Crash on existing .py file handling fixed.
* Fix to __doc__ use in setup.py to make -O0 installation mode working.
* Fix to PyPackageSearcher not to fail on broken Python packages.
* Source code pep8'ed
* Copyright added to source files.

Revision 0.0.6, released on Oct 01, 2015
----------------------------------------

* Several typos fixed, source code linted again.
* Some dead code cleaned up.

Revision 0.0.5, released on Sep 28, 2015
----------------------------------------

* Wheel distribution format now supported.
* Handle the case of MIB symbols conflict with Python reserved words.
* Handle binary DEFVAL initializer for INTEGER's.
* Generate LAST-UPDATED at pysnmp code generator.

Revision 0.0.4, released on Jul 01, 2015
----------------------------------------

* Fix to MRO compliance for mixin classes generation at pysnmp backend
* Fix to repeated imports in generated code at pysnmp backend
* Fix to mibdump tool to properly handle the --generate-mib-texts option.
* Fix to Python compile() - optimize flag is valid only past Python 3.1
* Fix to SMIv1 INDEX clause code generation for pysnmp backend.
* Tighten file creation security at pysmi.writer.pyfile

Revision 0.0.3, released on Jun 28, 2015
----------------------------------------

* Two-pass compiler design allows for much accurate code generation.
* Sphinx-based documentation first introduced

Revision 0.0.0, released on Apr 11, 2015
----------------------------------------

* First public release, not fully operational yet
