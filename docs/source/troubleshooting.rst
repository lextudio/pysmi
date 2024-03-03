.. include:: /includes/_links.rst

Troubleshooting
===============

.. toctree::
   :maxdepth: 2

Don't panic when your PySMI application does not work as expected. This
page provides some tips and tricks to troubleshoot your PySMI application.

PySMI Built-in Debugging
-------------------------

If you find your PySMI application behaving unexpectedly, try to enable
a /more or less verbose/ built-in PySMI debugging by adding the
following snippet of code at the beginning of your application:

.. code-block:: python

    from pysmi import debug

    # use specific flags for debugging
    debug.setLogger(debug.Debug('lexer', 'parser', 'compiler'))

    # use 'all' for full debugging
    debug.setLogger(debug.Debug('all'))

Then run your app and watch stderr. The Debug initializer enables debugging
for a particular PySMI subsystem, 'all' enables full debugging. More
specific flags are:

* searcher
* reader
* lexer
* parser
* grammar
* codegen
* writer
* compiler
* borrower

You might refer to PySMI source code to see in which components these
flags are used.

Common Utilities
----------------

While built-in debugging is a good start, you might want to use some other
tools and utilities to troubleshoot your PySMI application so as to gain more
insights.

For example, there are many SMI compilers available on the market. You might
compile your MIBs with another compiler and compare the results. If the other
compiler reports the same errors, then the problem is likely in your MIBs.

Commercial Support
------------------

If you are still stuck, you might want to consider hiring a professional to
help you out.

`LeXtudio Inc.`_ does not only support PySNMP/PySMI ecosystem by maintaining
the GitHub repositories but also offers commercial support such as consulting
services. You can easily open a support ticket via its homepage.

References
----------

- :doc:`/quick-start`
- :doc:`/examples/index`
- :doc:`/docs/api-reference`
