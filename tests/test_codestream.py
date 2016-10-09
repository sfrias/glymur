# -*- coding:  utf-8 -*-
"""
Test suite for codestream oddities
"""

# Standard library imports ...
import os
import unittest
import warnings

# Third party library imports ...
import pkg_resources as pkg

# Local imports ...
from glymur import Jp2k


class TestSuite(unittest.TestCase):
    """Test suite for ICC Profile code."""

    def setUp(self):
        relpath = os.path.join('data', 'p0_03.j2k')
        self.p0_03 = pkg.resource_filename(__name__, relpath)

        relpath = os.path.join('data', 'p0_06.j2k')
        self.p0_06 = pkg.resource_filename(__name__, relpath)

    def test_ppt_segment(self):
        """
        Verify parsing of the PPT segment
        """
        relpath = os.path.join('data', 'p1_06.j2k')
        filename = pkg.resource_filename(__name__, relpath)

        c = Jp2k(filename).get_codestream(header_only=False)
        self.assertEqual(c.segment[6].zppt, 0)

    def test_plt_segment(self):
        """
        Verify parsing of the PLT segment
        """
        relpath = os.path.join('data', 'issue142.j2k')
        filename = pkg.resource_filename(__name__, relpath)

        c = Jp2k(filename).get_codestream(header_only=False)
        self.assertEqual(c.segment[7].zplt, 0)
        self.assertEqual(len(c.segment[7].iplt), 59)

    def test_ppm_segment(self):
        """
        Verify parsing of the PPM segment
        """
        relpath = os.path.join('data', 'edf_c2_1178956.jp2')
        filename = pkg.resource_filename(__name__, relpath)

        with warnings.catch_warnings():
            # Lots of things wrong with this file.
            warnings.simplefilter('ignore')
            j2k = Jp2k(filename)
        c = j2k.get_codestream()
        self.assertEqual(c.segment[2].zppm, 0)
        self.assertEqual(len(c.segment[2].data), 9)

    def test_crg_segment(self):
        """
        Verify parsing of the CRG segment
        """
        j2k = Jp2k(self.p0_03)
        c = j2k.get_codestream()
        self.assertEqual(c.segment[6].xcrg, (65424,))
        self.assertEqual(c.segment[6].ycrg, (32558,))

    def test_rgn_segment(self):
        """
        Verify parsing of the RGN segment
        """
        j2k = Jp2k(self.p0_06)
        c = j2k.get_codestream()
        self.assertEqual(c.segment[-1].crgn, 0)
        self.assertEqual(c.segment[-1].srgn, 0)
        self.assertEqual(c.segment[-1].sprgn, 11)
