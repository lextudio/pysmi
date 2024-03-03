.. include:: /includes/_links.rst

Quick Start
===========

.. toctree::
   :maxdepth: 2

Once you decide to test out PySMI library on your Linux/Windows/macOS
system, you should start to prepare a test field folder and configure the
Python environment.

Set Up Test Field Folder
------------------------
First, it is recommended that you use `pyenv`_ to manage different Python
versions on this machine. If you are using Windows, you can use `pyenv-win`_.

Next, we assume you are now on macOS/Linux, and the following commands
initialize a folder for us,

.. code-block:: bash

   cd ~
   mkdir test-field
   cd test-field
   pyenv local 3.12
   pip install pipenv
   pipenv install pysmi-lextudio
   pipenv run pip list

Here we created a virtual environment using ``pipenv`` for this folder, and
installed ``pysmi-lextudio`` so that you can move on with the following
sections.

The final command should print out the dependencies and you should be able to
see ``pysmi-lextudio`` version 1.3+ there.

.. note::

   If you haven't installed Python 3.12 with ``pyenv``, you should execute
   ``pyenv install 3.12``.

   To delete the virtual environment for this folder, you can use

   .. code-block:: bash

      pipenv --rm

   It is common that you use another virtual environment tool, such as venv,
   poetry, or conda. Just make sure you use the equivalent commands to set up the
   virtual environment for testing.

   It is highly recommended that you use a Python virtual environment, as it
   makes dependency management and troubleshooting much easier.

Compile MIB Files
-----------------

Next, let's compile some MIB document and play with PySMI ``mibdump`` utility.

.. code-block:: bash

   pipenv run mibdump --generate-mib-texts  --destination-format json IF-MIB

With this simple command, IF-MIB can be easily compiled into JSON format (along with its
dependencies).

.. code-block:: text

   Source MIB repositories: file:///usr/share/snmp/mibs, https://mibs.pysnmp.com/asn1/@mib@
   Borrow missing/failed MIBs from: https://mibs.pysnmp.com/json/fulltexts/@mib@
   Existing/compiled MIB locations:
   Compiled MIBs destination directory: .
   MIBs excluded from code generation: RFC-1212, RFC-1215, RFC1065-SMI, RFC1155-SMI,
   RFC1158-MIB, RFC1213-MIB, SNMPv2-CONF, SNMPv2-SMI, SNMPv2-TC, SNMPv2-TM
   MIBs to compile: IF-MIB
   Destination format: json
   Parser grammar cache directory: not used
   Also compile all relevant MIBs: yes
   Rebuild MIBs regardless of age: yes
   Do not create/update MIBs: no
   Byte-compile Python modules: no (optimization level no)
   Ignore compilation errors: no
   Generate OID->MIB index: no
   Generate texts in MIBs: yes
   Keep original texts layout: no
   Try various filenames while searching for MIB module: yes
   Created/updated MIBs: IANAifType-MIB, IF-MIB, SNMPv2-MIB
   Pre-compiled MIBs borrowed:
   Up to date MIBs: SNMPv2-CONF, SNMPv2-SMI, SNMPv2-TC
   Missing source MIBs:
   Ignored MIBs:
   Failed MIBs:

.. note::
   Behind the scene, related MIB documents are downloaded from our MIB repository
   at `mibs.pysnmp.com`_.

   If you are behind a firewall, you may need to set up a proxy server for
   ``mibdump`` to work properly.

The generated JSON file for `IF-MIB`_ is located in the current folder. You can
see its contents like below,

.. code-block:: json

   {
      "ifMIB": {
          "name": "ifMIB",
          "oid": "1.3.6.1.2.1.31",
          "class": "moduleidentity",
          "revisions": [
            "2007-02-15 00:00",
            "1996-02-28 21:55",
            "1993-11-08 21:55"
          ]
        },
      // ...
      "ifTestTable": {
        "name": "ifTestTable",
        "oid": "1.3.6.1.2.1.31.1.3",
        "nodetype": "table",
        "class": "objecttype",
        "maxaccess": "not-accessible"
      },
      "ifTestEntry": {
        "name": "ifTestEntry",
        "oid": "1.3.6.1.2.1.31.1.3.1",
        "nodetype": "row",
        "class": "objecttype",
        "maxaccess": "not-accessible",
        "augmention": {
          "name": "ifTestEntry",
          "module": "IF-MIB",
          "object": "ifEntry"
        }
      },
      "ifTestId": {
        "name": "ifTestId",
        "oid": "1.3.6.1.2.1.31.1.3.1.1",
        "nodetype": "column",
        "class": "objecttype",
        "syntax": {
          "type": "TestAndIncr",
          "class": "type"
        },
        "maxaccess": "read-write"
      },
      // ...
   }

All aspects of original MIB documents are preserved in the JSON file. This
snippet above is just a small part of the whole file. You can take a look at
the complete `IF-MIB.json`_ file.

Produce JSON Index
------------------
Besides one-to-one MIB conversion, PySMI library can produce JSON index to
facilitate fast MIB information lookup across large collection of MIB files.

For example, JSON index for IP-MIB.json, TCP-MIB.json and UDP-MIB.json modules
would keep information like this:

.. code-block:: json

   {
      "compliance": {
         "1.3.6.1.2.1.48.2.1.1": [
           "IP-MIB"
         ],
         "1.3.6.1.2.1.49.2.1.1": [
           "TCP-MIB"
         ],
         "1.3.6.1.2.1.50.2.1.1": [
           "UDP-MIB"
         ]
      },
      "identity": {
          "1.3.6.1.2.1.48": [
            "IP-MIB"
          ],
          "1.3.6.1.2.1.49": [
            "TCP-MIB"
          ],
          "1.3.6.1.2.1.50": [
            "UDP-MIB"
          ]
      },
      "oids": {
          "1.3.6.1.2.1.4": [
            "IP-MIB"
          ],
          "1.3.6.1.2.1.5": [
            "IP-MIB"
          ],
          "1.3.6.1.2.1.6": [
            "TCP-MIB"
          ],
          "1.3.6.1.2.1.7": [
            "UDP-MIB"
          ],
          "1.3.6.1.2.1.49": [
            "TCP-MIB"
          ],
          "1.3.6.1.2.1.50": [
            "UDP-MIB"
          ]
      }
   }

With this example, ``compliance`` and ``identity`` keys point to
``MODULE-COMPLIANCE`` and ``MODULE-IDENTITY`` MIB objects, ``oids`` lists
top-level OIDs branches defined in MIB modules. You might want to review a
`full index`_ built over thousands of MIBs.

The PySMI library can automatically fetch required MIBs from HTTP sites or
local directories. You could configure any MIB source available to you
(including `mibs.pysnmp.com`_) for that purpose.

References
----------

- :doc:`/docs/mibdump`
- :doc:`/troubleshooting`
- :doc:`/docs/api-reference`
