"""
The tests here do not correspond directly to the OpenJPEG test suite, but
seem like logical negative tests to add.
"""
import os
import re
import tempfile
import unittest
import warnings

import numpy as np
try:
    import skimage.io
except ImportError:
    pass

from .fixtures import OPJ_DATA_ROOT, opj_data_file, read_image
from .fixtures import NO_READ_BACKEND, NO_READ_BACKEND_MSG
from .fixtures import NO_SKIMAGE_FREEIMAGE_SUPPORT
from .fixtures import WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG
from . import fixtures

from glymur import Jp2k
import glymur


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_OPJ_DATA_ROOT environment variable not set")
class TestSuiteNegativeRead(unittest.TestCase):
    """Test suite for certain negative tests from openjpeg suite."""

    def setUp(self):
        self.jp2file = glymur.data.nemo()
        self.j2kfile = glymur.data.goodstuff()

    def tearDown(self):
        pass

    def test_nr_marker_not_compliant(self):
        """non-compliant marker, should still be able to read"""
        relpath = 'input/nonregression/MarkerIsNotCompliant.j2k'
        jfile = opj_data_file(relpath)
        jp2k = Jp2k(jfile)
        jp2k.get_codestream(header_only=False)
        self.assertTrue(True)
