import os
import sys
if sys.hexversion < 0x02070000:
    import unittest2
    unittest = unittest2
else:
    import unittest

import numpy as np

from glymur.lib import tiff

try:
    data_root = os.environ['OPJ_DATA_ROOT']
except KeyError:
    data_root = None
except:
    raise

try:
    tiff_data_root = os.environ['LIBTIFFPIC_DATA_ROOT']
except KeyError:
    tiff_data_root = None
except:
    raise


@unittest.skipIf(tiff_data_root is None,
                 "LIBTIFFPIC_DATA_ROOT environment variable is None.")
@unittest.skipIf(data_root is None,
                 "OPJ_DATA_ROOT environment variable is None.")
class TestSuite(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_checkTile(self):
        # Verify TIFFCheckTile
        # no z, sample
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.checkTile(tif, 511, 383)
        tiff.close(tif)
        self.assertTrue(actual)

    def test_getVersion(self):
        # Verify TIFFGetVersion.
        actual = tiff.getVersion()
        self.assertTrue(actual.startswith('LIBTIFF, Version'))
        self.assertIn('Copyright (c) 1988-1996 Sam Leffler', actual)
        self.assertIn('Copyright (c) 1991-1996 Silicon Graphics, Inc.', actual)

    def test_computeStrip(self):
        # Verify TIFFComputeStrip
        # no z, sample
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.computeStrip(tif, 0)
        tiff.close(tif)
        expected = 0
        self.assertEqual(actual, expected)

    def test_getField_charp(self):
        # Verify TIFFGetField for char string.
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.SOFTWARE)
        tiff.close(tif)
        expected = 'pgx_tool-suite: tif_rgb2xyz, (C)Fraunhofer IIS, 2006'
        self.assertEqual(actual, expected)

    def test_getField_double(self):
        # Verify TIFFGetField for double value
        file = os.path.join(tiff_data_root, 'off_luv24.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.STONITS)
        tiff.close(tif)
        expected = 179
        self.assertEqual(actual, expected)

    def test_getField_exif_offset(self):
        # Verify TIFFGetField for exif IFD offset
        file = os.path.join(tiff_data_root, 'dscf0013.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.EXIFIFD)
        tiff.close(tif)
        expected = 640
        self.assertEqual(actual, expected)

    def test_getField_float3(self):
        # Verify TIFFGetField for 3-element floating point array
        # YCBCRCOEFFICIENTS
        file = os.path.join(tiff_data_root, 'zackthecat.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.YCBCRCOEFFICIENTS)
        tiff.close(tif)
        np.testing.assert_allclose(actual, [0.299, 0.587, 0.114], atol=0.001)

    def test_getField_float6(self):
        # Verify TIFFGetField for 6-element floating point array
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.PRIMARYCHROMATICITIES)
        tiff.close(tif)
        np.testing.assert_allclose(actual, [0.68, 0.32, 0.265, 0.69, 0.15,
                                            0.06], 0.01)

    def test_getField_uint16(self):
        # Verify TIFFGetField for single uint16 value.
        # TIFFTAG_BITSPERSAMPLE = 258
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.BITSPERSAMPLE)
        tiff.close(tif)
        expected = 16
        self.assertEqual(actual, expected)

    def test_getField_uint16_defaulted(self):
        # Verify TIFFGetField for single uint16 value that is defaulted.
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.SAMPLEFORMAT)
        tiff.close(tif)
        expected = tiff.SAMPLEFORMAT_UINT
        self.assertEqual(actual, expected)

    def test_getField_2uint16(self):
        # Verify TIFFGetField for two uint16 values.
        file = os.path.join(tiff_data_root, 'dscf0013.tif')
        tif = tiff.open(file)
        tiff.setDirectory(tif, 1)
        actual = tiff.getField(tif, tiff.YCBCRSUBSAMPLING)
        tiff.close(tif)
        expected = (2, 1)
        self.assertEqual(actual, expected)

    def test_getField_uint32(self):
        # Verify TIFFGetField for single uint32 value.
        # TIFFTAG_IMAGEWIDTH = 256
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_6_2K_24_FULL_CBR_CIRCLE_000.tif')
        tif = tiff.open(file)
        actual = tiff.getField(tif, tiff.IMAGEWIDTH)
        tiff.close(tif)
        expected = 2048
        self.assertEqual(actual, expected)

    def test_computeTile(self):
        # Verify TIFFComputeTile
        # no z, sample
        file = os.path.join(tiff_data_root, 'quad-tile.tif')
        tif = tiff.open(file)
        actual = tiff.computeTile(tif, 0, 0)
        tiff.close(tif)
        expected = 0
        self.assertEqual(actual, expected)

    def test_isTiled(self):
        # Verify TIFFIsTiled
        # tiled case
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        yn = tiff.isTiled(tif)
        tiff.close(tif)
        self.assertFalse(yn)

    def test_lastDirectory(self):
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        yn = tiff.lastDirectory(tif)
        self.assertTrue(yn)
        tiff.close(tif)

    def test_numberOfStrips(self):
        # Verify TIFFNumberOfStrips.
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        actual = tiff.numberOfStrips(tif)
        tiff.close(tif)
        expected = 857
        self.assertEqual(actual, expected)

    def test_numberOfTiles(self):
        file = os.path.join(tiff_data_root, 'quad-tile.tif')
        tif = tiff.open(file)
        actual = tiff.numberOfTiles(tif)
        tiff.close(tif)
        expected = 12
        self.assertEqual(actual, expected)

    def test_readDirectory(self):
        file = os.path.join(tiff_data_root, 'dscf0013.tif')
        tif = tiff.open(file)
        tiff.readDirectory(tif)
        actual = tiff.getField(tif, tiff.IMAGEWIDTH)
        tiff.close(tif)
        expected = 160
        self.assertEqual(actual, expected)

    def test_readEncodedStrip(self):
        file = os.path.join(data_root, 'input', 'nonregression',
                            'flower-rgb-contig-08.tif')
        tif = tiff.open(file)
        rgba_strip = tiff.readRGBAStrip(tif, 0)
        strip = tiff.readEncodedStrip(tif, 0)
        tiff.close(tif)
        np.testing.assert_equal(rgba_strip[:, :, 0:3], strip)

    def test_readEncodedTile(self):
        file = os.path.join(tiff_data_root, 'quad-tile.tif')
        tif = tiff.open(file)
        rgba_tile = tiff.readRGBATile(tif, 0, 0)
        tile = tiff.readEncodedTile(tif, 0)
        tiff.close(tif)
        np.testing.assert_equal(rgba_tile[:, :, 0:3], tile)

    def test_readRGBAImage(self):
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        image = tiff.readRGBAImage(tif)
        tiff.close(tif)
        expected = (857, 2048, 4)
        self.assertEqual(image.shape, expected)

    def test_readRGBAStrip(self):
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        strip = tiff.readEncodedStrip(tif, 0)
        tiff.close(tif)
        self.assertEqual(strip.shape, (1, 2048, 3))

    def test_readRGBATile(self):
        file = os.path.join(tiff_data_root, 'quad-tile.tif')
        tif = tiff.open(file)
        image = tiff.readRGBAImage(tif)
        tile = tiff.readRGBATile(tif, 0, 0)
        tiff.close(tif)
        self.assertEqual(tile.shape, (128, 128, 4))
        np.testing.assert_equal(tile, image[:128, :128, :])

    def test_stripSize(self):
        # Verify TIFFStripSize.
        file = os.path.join(data_root, 'input', 'nonregression',
                            'X_5_2K_24_235_CBR_STEM24_000.tif')
        tif = tiff.open(file)
        actual = tiff.stripSize(tif)
        tiff.close(tif)
        expected = 12288
        self.assertEqual(actual, expected)

    def test_tileSize(self):
        # Verify TIFFTileSize.
        # Strip size = 128 * 128 * 3
        # "divided by two" because of subsampling.
        file = os.path.join(tiff_data_root, 'quad-tile.tif')
        tif = tiff.open(file)
        actual = tiff.tileSize(tif)
        tiff.close(tif)
        expected = 49152
        self.assertEqual(actual, expected)
