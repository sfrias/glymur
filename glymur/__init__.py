"""glymur - read, write, and interrogate JPEG 2000 files
"""
import unittest

from glymur import version, config
__version__ = version.version

from .jp2k import Jp2k
from .jp2box import (get_printoptions,
                     set_printoptions,
                     get_parseoptions,
                     set_parseoptions)
from .tif2jp2 import tif2jp2
from . import data


def runtests():
    """Discover and run all tests for the glymur package.
    """
    suite = unittest.defaultTestLoader.discover(__path__[0])
    unittest.TextTestRunner(verbosity=2).run(suite)


__all__ = [__version__, config, Jp2k, get_printoptions, set_printoptions,
           get_parseoptions, set_parseoptions, data, runtests, tif2jp2]
