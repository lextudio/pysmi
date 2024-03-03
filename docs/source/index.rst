.. include:: /includes/_links.rst

SNMP SMI Compiler for Python
============================

.. toctree::
   :maxdepth: 2

The PySMI library and tools are designed to parse, verify and transform
`SNMP SMI`_ MIB modules from their original ASN.1 form into JSON or `PySNMP`_
representation.

This library is highly modular. The top-level component is called
*compiler* and it acts as main user-facing object. Most of other
components are plugged into the *compiler* object prior to its use.

Normally, users ask *compiler* to perform certain transformation of
named MIB modules. The *compiler* will:

* Search its data sources for given MIB module (identified by name)
  noting their last modification times.
* Search compiler-managed repositories of already converted MIB modules
  for modules that are more recent than corresponding source MIB module.
* If freshly transformed MIB module is found, processing stops here.
* Otherwise compiler passes ASN.1 MIB module content to the *lexer*
  component.
* Lexer returns a sequence of tokenized ASN.1 MIB contents. Compiler
  then passes that sequence of tokens to the *parser* component.
* Parser runs LR algorithm on tokenized MIB thus transforming MIB
  contents into Abstract Syntax Tree (AST) and also noting what other
  MIB modules are referred to from the MIB being parsed.
* In case of parser failure, what is usually an indication of broken
  ASN.1 MIB syntax, compiler may attempt to fetch pre-transformed MIB
  contents from configured source. This process is called *borrowing*
  in PySMI.
* In case of successful parser completion, compiler will pass produced
  AST to *code generator* component.
* Code generator walks its input AST and performs actual data
  transformation.
* The above steps may be repeated for each of the MIB modules referred
  to as parser figures out. Once no more unresolved dependencies remain,
  compiler will call its *writer* component to store all transformed MIB
  modules.

The location of ASN.1 MIB modules and flavor of their syntax, as well as
desired transformation format, is determined by respective components
chosen and configured to compiler.

PySMI software is free and open-source. Project source code is hosted at `PySMI GitHub repository`_.
This library is being distributed under 2-clause BSD License.

Quick Start
-----------

You already know something about SNMP SMI and have no courage to dive into
this implementation? Try out quick start page!

.. toctree::
   :maxdepth: 2

   Return to PySNMP Homepage <https://pysnmp.com>
   /quick-start

Documentation
-------------

You can find conceptual and API documentation in the following section.

.. toctree::
   :maxdepth: 2

   /docs/index

Samples
-------

We have a collection of sample scripts to help you get started with PySMI.

.. toctree::
   :maxdepth: 2

   /examples/index

Troubleshooting
---------------

If you are having trouble with PySMI, please check the following section.

.. toctree::
   :maxdepth: 2

   /troubleshooting

Downloads
---------

Best way is usually to

.. code-block:: bash

   pip install pysmi-lextudio

If that does not work for you for some reason, you might need to read the
following page.

.. toctree::
   :maxdepth: 2

   /download

License
-------

.. toctree::
   :maxdepth: 2

   /license

Release Notes
-------------

We maintain the detailed log of changes to our software.

.. toctree::
   :maxdepth: 1

   /changelog

MIB Files Archive
-----------------

The PySMI project maintains a collection of publicly available ASN.1 MIB files
collected over the Internet at `mibs.pysnmp.com`_. You are
welcome to use this MIBs archive however we can't guarantee any degree
of consistency or reliability when it comes to these MIB modules.

The *mibdump* tool as well as many other utilities based on PySMI
are programmed to use this MIB repository for automatic download and
dependency resolution.

You can always reconfigure PySMI to use some other remote MIB repository
instead or in addition to this one.

Contact
-------

In case of questions or troubles using SNMP SMI library, please open up a
`GitHub issue`_ at GitHub or ask on `Stack Overflow`_ .

For other inquiries, please contact `LeXtudio Inc.`_.
