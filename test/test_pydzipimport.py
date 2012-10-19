"""Tests for `pydzipimport`."""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012 Bradley Froehle <brad.froehle@gmail.com>

#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import imp
import os
import sys
import unittest
import tempfile
import zipfile

from distutils.command.build_ext import build_ext
from distutils.core import Distribution
from distutils.extension import Extension

import pydzipimport

# The filename extension for compiled extension modules.
SO_EXT = [suffix[0] for suffix in imp.get_suffixes()
          if suffix[2] == imp.C_EXTENSION][0]

def prepare_sample_zip(file):
    """Create a zipfile which contains the `sample` package.

    On completion, the contents of `file` will be::

        sample/
        sample/one.py
        sample/__init__.<SO_EXT>
        sample/two.<SO_EXT>

    The extension modules are compiled in a temporary directory.
    """

    src = os.path.join(os.path.dirname(__file__), 'sample')

    zf = zipfile.ZipFile(file, mode='w')

    # Is there an easier way to make an empty directory in the zipfile???
    with tempfile.TemporaryDirectory() as td:
        zf.write(td, 'sample')

    zf.write(os.path.join(src, 'one.py'),
             os.path.join('sample', 'one.py'))

    with tempfile.TemporaryDirectory() as td:
        ## Build the extension modules.
        ## This is more or less the same as running::
        ##   python setup.py build_ext --force
        ## for the following `setup.py` script::
        #
        # from distutils.core import setup
        # from distutils.extension import Extension
        #
        # setup(
        #     packages = ['test_pydzipimport'],
        #     ext_modules = [
        #         Extension("sample.__init__", ["sample/__init__.c"]),
        #         Extension("sample.two", ["sample/two.c"]),
        #         ],
        #     )

        b = build_ext(Distribution())
        b.force = True
        b.finalize_options()
        b.extensions = [
            Extension('sample.__init__', [os.path.join(src, '__init__.c')]),
            Extension('sample.two', [os.path.join(src, 'two.c')]),
            ]
        b.build_temp = td
        b.build_lib = td
        b.run()

        zf.write(b.get_ext_fullpath('sample.__init__'),
                 'sample/__init__' + SO_EXT)
        zf.write(b.get_ext_fullpath('sample.two'),
                 'sample/two' + SO_EXT)

    zf.close()

class TestPydZipImport(unittest.TestCase):
    """Test PydZipImport class."""

    @classmethod
    def setUpClass(cls):
        cls.zf = os.path.join(os.path.dirname(__file__), 'sample.zip')
        prepare_sample_zip(cls.zf)

    def setUp(self):
        self._old_sys_path = list(sys.path)

        # Remove troublesome entries of sys.path:
        for p in ('', os.path.dirname(__file__)):
            if p in sys.path:
                sys.path.remove(p)

        pydzipimport.install()

    def tearDown(self):
        sys.path = self._old_sys_path
        pydzipimport.uninstall()

    def test_import_package(self):
        """Test importing a package in a zipfile."""
        sys.path.insert(0, self.zf)
        base = os.path.join(self.zf, 'sample')

        # Test package (sample/__init__.<SO_EXT>):
        import sample as s

        if not hasattr(s, '__file__'):
            self.fail('Unexpected implicit namespace package: %s' % s.__path__)

        self.assertEqual(s.data, 'sample.__init__')
        self.assertIsInstance(s.__loader__,
                              pydzipimport.TemporaryExtensionFileLoader)
        self.assertEqual(s.__package__, 'sample')
        self.assertEqual(s.__path__, [base])
        self.assertEqual(s.__file__, os.path.join(base, '__init__' + SO_EXT))
        # print(s.__loader__.data.name)

        # Test source module (sample/one.py):
        import sample.one
        self.assertEqual(s.one.data, 'sample.one')
        self.assertEqual(s.one.__package__, 'sample')
        self.assertFalse(hasattr(s.one, '__path__'))
        self.assertEqual(s.one.__file__, os.path.join(base, 'one.py'))

        # Test extension module (sample/two.<SO_EXT>):
        import sample.two
        self.assertEqual(s.two.data, 'sample.two')
        self.assertIsInstance(s.two.__loader__,
                              pydzipimport.TemporaryExtensionFileLoader)
        self.assertEqual(s.two.__package__, 'sample')
        self.assertFalse(hasattr(s.two, '__path__'))
        self.assertEqual(s.two.__file__, os.path.join(base, 'two' + SO_EXT))
        # print(s.two.__loader__.data.name)

    def test_import_source_module(self):
        """Test importing a source module in a zipfile."""
        base = os.path.join(self.zf, 'sample')
        sys.path.insert(0, base)

        import one

        self.assertEqual(one.data, 'sample.one')
        self.assertFalse(one.__package__)
        self.assertEqual(one.__file__, os.path.join(base, 'one.py'))

    def test_import_extension_module(self):
        """Test importing an extension module in a zipfile."""
        base = os.path.join(self.zf, 'sample')
        sys.path.insert(0, base)

        import two

        self.assertEqual(two.data, 'sample.two')
        self.assertIsInstance(two.__loader__,
                              pydzipimport.TemporaryExtensionFileLoader)
        self.assertFalse(two.__package__)
        self.assertEqual(two.__file__, os.path.join(base, 'two' + SO_EXT))
        # print(two.__loader__.data.name)


if __name__ == "__main__":
    unittest.main()
