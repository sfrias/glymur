# -*- coding:  utf-8 -*-
"""
Test suite for codestream oddities
"""

# Standard library imports ...
import os
import struct
import tempfile
import unittest
import warnings

# Third party library imports ...
import pkg_resources as pkg

# Local imports ...
import glymur
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


class TestCodestreamRepr(unittest.TestCase):

    def setUp(self):
        self.jp2file = glymur.data.nemo()

    def tearDown(self):
        pass

    def test_soc(self):
        """Test SOC segment repr"""
        segment = glymur.codestream.SOCsegment()
        newseg = eval(repr(segment))
        self.assertEqual(newseg.marker_id, 'SOC')

    def test_siz(self):
        """Test SIZ segment repr"""
        kwargs = {'rsiz': 0,
                  'xysiz': (2592, 1456),
                  'xyosiz': (0, 0),
                  'xytsiz': (2592, 1456),
                  'xytosiz': (0, 0),
                  'Csiz': 3,
                  'bitdepth': (8, 8, 8),
                  'signed': (False, False, False),
                  'xyrsiz': ((1, 1, 1), (1, 1, 1))}
        segment = glymur.codestream.SIZsegment(**kwargs)
        newseg = eval(repr(segment))
        self.assertEqual(newseg.marker_id, 'SIZ')
        self.assertEqual(newseg.xsiz, 2592)
        self.assertEqual(newseg.ysiz, 1456)
        self.assertEqual(newseg.xosiz, 0)
        self.assertEqual(newseg.yosiz, 0)
        self.assertEqual(newseg.xtsiz, 2592)
        self.assertEqual(newseg.ytsiz, 1456)
        self.assertEqual(newseg.xtosiz, 0)
        self.assertEqual(newseg.ytosiz, 0)

        self.assertEqual(newseg.xrsiz, (1, 1, 1))
        self.assertEqual(newseg.yrsiz, (1, 1, 1))
        self.assertEqual(newseg.bitdepth, (8, 8, 8))
        self.assertEqual(newseg.signed, (False, False, False))


class TestCodestream(unittest.TestCase):
    """Test suite for unusual codestream cases."""

    def setUp(self):
        self.jp2file = glymur.data.nemo()
        self.j2kfile = glymur.data.goodstuff()

    def tearDown(self):
        pass

    @unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
    def test_reserved_marker_segment(self):
        """Reserved marker segments are ok."""

        # Some marker segments were reserved in FCD15444-1.  Since that
        # standard is old, some of them may have come into use.
        #
        # Let's inject a reserved marker segment into a file that
        # we know something about to make sure we can still parse it.
        with tempfile.NamedTemporaryFile(suffix='.j2k') as tfile:
            with open(self.j2kfile, 'rb') as ifile:
                # Everything up until the first QCD marker.
                read_buffer = ifile.read(65)
                tfile.write(read_buffer)

                # Write the new marker segment, 0xff6f = 65391
                read_buffer = struct.pack('>HHB', int(65391), int(3), int(0))
                tfile.write(read_buffer)

                # Get the rest of the input file.
                read_buffer = ifile.read()
                tfile.write(read_buffer)
                tfile.flush()

            codestream = Jp2k(tfile.name).get_codestream()

            self.assertEqual(codestream.segment[3].marker_id, '0xff6f')
            self.assertEqual(codestream.segment[3].length, 3)
            self.assertEqual(codestream.segment[3].data, b'\x00')

    def test_siz_segment_ssiz_unsigned(self):
        """ssiz attribute to be removed in future release"""
        j = Jp2k(self.jp2file)
        codestream = j.get_codestream()

        # The ssiz attribute was simply a tuple of raw bytes.
        # The first 7 bits are interpreted as the bitdepth, the MSB determines
        # whether or not it is signed.
        self.assertEqual(codestream.segment[1].ssiz, (7, 7, 7))
