"""
Test suite specifically targeting JP2 box layout.
"""
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
import warnings

if sys.hexversion <= 0x03030000:
    from mock import patch
else:
    from unittest.mock import patch

try:
    from libxmp import XMPFiles, XMPIterator
    NO_PYTHON_XMP_TOOLKIT = False
except ImportError:
    NO_PYTHON_XMP_TOOLKIT = True

import numpy as np

import glymur
from glymur import command_line, Jp2k
from glymur.tif2jp2 import Tiff

from .fixtures import DATASRC, opj_data_file, libtiffpic_file, geotiff_file
from .fixtures import WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG


class TestSuite(unittest.TestCase):

    def setUp(self):
        self.geotiff_keys = ['ModelPixelScale', 'ModelTiePoint',
                             'ModelTransformation', 'GeoKeyDirectory',
                             'GeoDoubleParams', 'GeoAsciiParams']

    def assertTiffConversion(self, tiff_filename):
        tiff = Tiff(tiff_filename)
        expdata = tiff[:]

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tiff_filename, jfile.name]):
                with warnings.catch_warnings():
                    # Ignore any warnings, such as the possible presence of
                    # an icc profile
                    warnings.simplefilter("ignore")
                    command_line.tif2jp2_cmd()
                jp2 = Jp2k(jfile.name)
                actdata = jp2[:]
                np.testing.assert_array_equal(expdata, actdata)

                self.assertEquivalentXMP(tiff_filename, jfile.name)

    def assertEquivalentXMP(self, tifffile, jp2file):

        xmpt = XMPFiles(file_path=tifffile).get_xmp()
        xmpj = XMPFiles(file_path=jp2file).get_xmp()

        it = XMPIterator(xmpt, iter_justleafnodes=True)

        for ns, name, expvalue, _ in it:
            if name in ['tiff:Compression', 'tiff:PlanarConfiguration']:
                continue
            if name == 'photoshop:DateCreated':
                # This seems to violate the spec.  DateTime should map to
                # xmp:ModifyDate, not photoshop:DateCreated
                continue
            actvalue = xmpj.get_property(ns, name)
            self.assertEqual(expvalue, actvalue,
                             ns + ":" + name + ' did not test out')

        tf = Tiff(tifffile)
        if 'GeoAsciiParams' in tf.ifd[0].keys():
            jp2 = Jp2k(jp2file)
            exp_uuid = uuid.UUID('b14bf8bd-083d-4b43-a5ae-8cd7d5a6ce03')
            act_uuid = jp2.box[-1].uuid
            self.assertEqual(exp_uuid, act_uuid)

            # These conditions specify a degenerate geotiff
            self.assertEqual(jp2.box[-1].data['ImageLength'], 1)
            self.assertEqual(jp2.box[-1].data['ImageWidth'], 1)
            self.assertEqual(jp2.box[-1].data['BitsPerSample'], 1)
            self.assertEqual(jp2.box[-1].data['PhotometricInterpretation'], 1)
            self.assertEqual(jp2.box[-1].data['StripByteCounts'], 1)

            # Just one pixel, so just one offset
            offset = jp2.box[-1].data['StripOffsets']
            self.assertTrue(isinstance(offset, int))

            # The pixel value must be zero
            self.assertEqual(jp2.box[-1].raw_data[offset], 0)

            # These are not required, but seem like a good idea
            self.assertEqual(jp2.box[-1].data['RowsPerStrip'], 1)
            self.assertEqual(jp2.box[-1].data['SamplesPerPixel'], 1)

            # The geotiff tags just have to match what is in the TIFF
            key_count = 0
            for key in self.geotiff_keys:
                if key in tf.ifd[0].keys():
                    key_count += 1
                    self.assertEqual(tf.ifd[0][key], jp2.box[-1].data[key])

            self.assertTrue(key_count >= 4)


@unittest.skipIf(NO_PYTHON_XMP_TOOLKIT, "python-xmp-toolkit not detected")
@unittest.skipIf(DATASRC['geotiff'] is None, "geotiff data")
class TestSuiteGeotiff(TestSuite):

    def test_all(self):
        for root, subdirs, geotiff_files in os.walk(DATASRC['geotiff']):
            if len(geotiff_files) == 0:
                continue

            for geotiff in geotiff_files:
                path = os.path.join(root, geotiff)
                tiff = Tiff(path)
                if tiff.ifd[0]['BitsPerSample'] not in [8, 16]:
                    continue
                if ((('SampleFormat' in tiff.ifd[0].keys()) and
                     (tiff.ifd[0]['SampleFormat'] != 1))):
                    # 1 = unsigned
                    continue
                self.assertTiffConversion(path)


@unittest.skipIf(NO_PYTHON_XMP_TOOLKIT, "python-xmp-toolkit not detected")
@unittest.skipIf(DATASRC['opj_data_root'] is None, "No opj data")
class TestSuiteOpj(TestSuite):

    def test_jp2_1(self):
        # 4 channel image, chop off the alpha layer
        tiff_filename = opj_data_file('baseline/conformance/jp2_1.tif')
        self.assertTiffConversion(tiff_filename)

    def test_basn4a08(self):
        """8-bit greyscale image with alpha layer and ICC profile"""
        tiff_filename = opj_data_file('input/nonregression/basn4a08.tif')
        self.assertTiffConversion(tiff_filename)

    def test_flower_rgb_contig_16(self):
        """
        16-bit RGB

        Software is mapped to CreatorTool
        """
        tfile = opj_data_file(os.path.join('input',
                                           'nonregression',
                                           'flower-rgb-contig-16.tif'))
        self.assertTiffConversion(tfile)

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_icc_profile_warning(self):
        tiff_filename = opj_data_file('input/nonregression/basn4a08.tif')

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tiff_filename, jfile.name]):
                with self.assertWarns(UserWarning):
                    command_line.tif2jp2_cmd()

    def test_flower_minisblack_01(self):
        """
        1-bit images are not allowed
        """
        tfile = opj_data_file(os.path.join('input',
                                           'nonregression',
                                           'flower-minisblack-01.tif'))
        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tfile, jfile.name]):
                with self.assertRaises(RuntimeError):
                    command_line.tif2jp2_cmd()


@unittest.skipIf(NO_PYTHON_XMP_TOOLKIT, "python-xmp-toolkit not detected")
@unittest.skipIf(DATASRC['libtiffpic'] is None, "No libtiffpic data")
class TestSuiteLibTiffPic(TestSuite):

    def test_no_progression_order(self):
        tiff_filename = libtiffpic_file('quad-jpeg.tif')
        self.assertTiffConversion(tiff_filename)
        tiff = Tiff(tiff_filename)
        expdata = tiff[:]

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tiff_filename, jfile.name]):
                command_line.tif2jp2_cmd()
                jp2 = Jp2k(jfile.name)
                actdata = jp2[:]
                np.testing.assert_array_equal(expdata, actdata)
                self.assertEquivalentXMP(tiff_filename, jfile.name)

                c = jp2.get_codestream()
                self.assertEqual(c.segment[2].spcod[0], glymur.core.LRCP)

    def test_num_resolutions(self):
        tiff_filename = libtiffpic_file('quad-jpeg.tif')
        self.assertTiffConversion(tiff_filename)
        tiff = Tiff(tiff_filename)
        expdata = tiff[:]
        exp_num_res = 3

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', '-n', str(exp_num_res),
                                        tiff_filename, jfile.name]):
                command_line.tif2jp2_cmd()
                jp2 = Jp2k(jfile.name)
                actdata = jp2[:]
                np.testing.assert_array_equal(expdata, actdata)
                self.assertEquivalentXMP(tiff_filename, jfile.name)
    
                c = jp2.get_codestream()
                self.assertEqual(c.segment[2].spcod[4] + 1, exp_num_res)

    def test_num_resolutions_too_high(self):
        tiff_filename = libtiffpic_file('quad-jpeg.tif')
        self.assertTiffConversion(tiff_filename)
        tiff = Tiff(tiff_filename)

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', '-n', '10',
                                        tiff_filename, jfile.name]):
                if sys.hexversion > 0x03000000:
                    # Verify warning about resolutions too high
                    with self.assertWarns(UserWarning):
                        command_line.tif2jp2_cmd()
                else:
                    # Suppress the warning
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        command_line.tif2jp2_cmd()

                jp2 = Jp2k(jfile.name)
    
                # The smallest side is 2^8 < 384 < 2^9,
                # therefore the number of resolutions is 8
                c = jp2.get_codestream()
                self.assertEqual(c.segment[2].spcod[4] + 1, 8)

    def test_tile_size(self):
        tiff_filename = libtiffpic_file('quad-jpeg.tif')
        self.assertTiffConversion(tiff_filename)
        tiff = Tiff(tiff_filename)
        expdata = tiff[:]

        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', '-t', '128', '128', tiff_filename,
                                        jfile.name]):
                command_line.tif2jp2_cmd()
                jp2 = Jp2k(jfile.name)
                actdata = jp2[:]
                np.testing.assert_array_equal(expdata, actdata)
                self.assertEquivalentXMP(tiff_filename, jfile.name)
    
                c = jp2.get_codestream()
                self.assertEqual(c.segment[1].xtsiz, 128)
                self.assertEqual(c.segment[1].ytsiz, 128)

    def test_progression_order_lrcp(self):
        tiff_filename = libtiffpic_file('quad-jpeg.tif')
        self.assertTiffConversion(tiff_filename)
        tiff = Tiff(tiff_filename)
        expdata = tiff[:]

        for prog in ['LRCP', 'RLCP', 'RPCL', 'PCRL', 'CPRL']:
            with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
                with patch('sys.argv', new=['', '-p', prog, tiff_filename,
                                            jfile.name]):
                    command_line.tif2jp2_cmd()
                    jp2 = Jp2k(jfile.name)
                    actdata = jp2[:]
                    np.testing.assert_array_equal(expdata, actdata)
                    self.assertEquivalentXMP(tiff_filename, jfile.name)
    
                    c = jp2.get_codestream()
                    self.assertEqual(c.segment[2].spcod[0],
                                     getattr(glymur.core, prog))

    def test_cramps(self):
        """
        stripped grayscale 8-bit image
        """
        tfile = libtiffpic_file('cramps.tif')
        self.assertTiffConversion(tfile)

    def test_cramps_tile(self):
        """
        tiled grayscale 8-bit image
        """
        tfile = libtiffpic_file('cramps-tile.tif')
        self.assertTiffConversion(tfile)

    def test_dscf0013(self):
        """
        8-bit RGB YCbCr with EXIF
        """
        tfile = libtiffpic_file('dscf0013.tif')
        self.assertTiffConversion(tfile)

    def test_flower_separated_planar_08(self):
        """
        separated images (cmyk) are not allowed
        """
        tfile = libtiffpic_file(os.path.join('depth',
                                             'flower-separated-planar-08.tif'))
        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tfile, jfile.name]):
                with self.assertRaises(RuntimeError):
                    command_line.tif2jp2_cmd()

    def test_caspian(self):
        """
        floating point RGB is not allowed
        """
        tfile = libtiffpic_file('caspian.tif')
        with tempfile.NamedTemporaryFile(suffix='.jp2') as jfile:
            with patch('sys.argv', new=['', tfile, jfile.name]):
                with self.assertRaises(RuntimeError):
                    command_line.tif2jp2_cmd()

    def convert_to_bigtiff(self, classic_file, bigtiff_filename):
        classic_file = libtiffpic_file('quad-lzw.tif')
        cmd = 'tiffcp -8 {input} {output}'.format(input=classic_file,
                                                  output=bigtiff_filename)
        subprocess.check_output(cmd, shell=True)

        tiff = Tiff(bigtiff_filename)
        self.assertFalse(tiff.classic)
