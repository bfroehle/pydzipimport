=====================================================
pydzipimport: zipimport with extension module support
=====================================================

Overview
========

The regular ``zipimport`` module is limited to zip archives containing
only regular python source files (``.py``) and compiled byte-code
(``.pyo`` and ``.pyc``).

This module serves as a replacement for ``zipimport`` which allows the
zip archive to contain extension modules (``.so``, ``.pyd``). When the
module is imported, the extension module is deflated into a temporary
directory and then loaded by the usual mechanisms.


Requirements
============

Currently only Python 3.3 or later is supported. There are no additional
dependencies.


Getting Started
===============

Replace the regular ``zipimport.zipimporter`` path hook in
``sys.path_hooks`` with ``pydzipimport.PydZipImporter``.  Then be sure
to clear the path importer cache (``sys.path_importer_cache``) of any
stale entries.

To automate this task, an ``install`` function is provided::

    import pydzipimport
    pydzipimport.install()

Now extension modules contained within a zip file can be imported.
