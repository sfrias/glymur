# -*- coding:  utf-8 -*-
"""
Test suite for codestream oddities
"""

# Standard library imports ...
import os
import unittest

# Third party library imports ...
import pkg_resources as pkg

# Local imports ...
from glymur import Jp2k


class TestSuite(unittest.TestCase):
    """Test suite for ICC Profile code."""

    def setUp(self):
        relpath = os.path.join('data', 'p0_03.j2k')
        self.p0_03 = pkg.resource_filename(__name__, relpath)

    def test_crg_segment(self):
        """
        Verify parsing of the CRG segment
        """
        j2k = Jp2k(self.p0_03)
        c = j2k.get_codestream()
        self.assertEqual(c.segment[6].xcrg, (65424,))
        self.assertEqual(c.segment[6].ycrg, (32558,))
