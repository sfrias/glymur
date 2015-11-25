"""
The tests defined here roughly correspond to what is in the OpenJPEG test
suite.
"""
import re
import sys
import unittest
import warnings

import numpy as np

import glymur
from glymur import Jp2k
from glymur.jp2box import FileTypeBox, ImageHeaderBox, ColourSpecificationBox

from .fixtures import (OPJ_DATA_ROOT, MetadataBase,
                       WARNING_INFRASTRUCTURE_ISSUE,
                       WARNING_INFRASTRUCTURE_MSG,
                       mse, peak_tolerance, read_pgx, opj_data_file,
                       OPENJPEG_NOT_AVAILABLE, OPENJPEG_NOT_AVAILABLE_MSG)


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(glymur.version.openjpeg_version_tuple[0] != 2,
                 "Feature not supported in glymur until openjpeg 2.0")
class TestSuiteBands(unittest.TestCase):
    """
    Test the read_bands method.
    """
    def test_ETS_C1P1_p1_03_j2k(self):
        jfile = opj_data_file('input/conformance/p1_03.j2k')
        jp2k = Jp2k(jfile)
        jpdata = jp2k.read_bands()

        pgxfile = opj_data_file('baseline/conformance/c1p1_03_0.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[0], pgxdata) < 2)
        self.assertTrue(mse(jpdata[0], pgxdata) < 0.3)

        pgxfile = opj_data_file('baseline/conformance/c1p1_03_1.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[1], pgxdata) < 2)
        self.assertTrue(mse(jpdata[1], pgxdata) < 0.21)

        pgxfile = opj_data_file('baseline/conformance/c1p1_03_2.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[2], pgxdata) <= 1)
        self.assertTrue(mse(jpdata[2], pgxdata) < 0.2)

        pgxfile = opj_data_file('baseline/conformance/c1p1_03_3.pgx')
        pgxdata = read_pgx(pgxfile)
        np.testing.assert_array_equal(jpdata[3], pgxdata)

    def test_ETS_C1P0_p0_05_j2k(self):
        jfile = opj_data_file('input/conformance/p0_05.j2k')
        jp2k = Jp2k(jfile)
        jpdata = jp2k.read_bands()

        pgxfile = opj_data_file('baseline/conformance/c1p0_05_0.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[0], pgxdata) < 2)
        self.assertTrue(mse(jpdata[0], pgxdata) < 0.302)

        pgxfile = opj_data_file('baseline/conformance/c1p0_05_1.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[1], pgxdata) < 2)
        self.assertTrue(mse(jpdata[1], pgxdata) < 0.307)

        pgxfile = opj_data_file('baseline/conformance/c1p0_05_2.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[2], pgxdata) < 2)
        self.assertTrue(mse(jpdata[2], pgxdata) < 0.269)

        pgxfile = opj_data_file('baseline/conformance/c1p0_05_3.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[3], pgxdata) == 0)
        self.assertTrue(mse(jpdata[3], pgxdata) == 0)

    def test_ETS_C1P0_p0_06_j2k(self):
        jfile = opj_data_file('input/conformance/p0_06.j2k')
        jp2k = Jp2k(jfile)
        jpdata = jp2k.read_bands()

        pgxfile = opj_data_file('baseline/conformance/c1p0_06_0.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[0], pgxdata) < 635)
        self.assertTrue(mse(jpdata[0], pgxdata) < 11287)

        pgxfile = opj_data_file('baseline/conformance/c1p0_06_1.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[1], pgxdata) < 403)
        self.assertTrue(mse(jpdata[1], pgxdata) < 6124)

        pgxfile = opj_data_file('baseline/conformance/c1p0_06_2.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[2], pgxdata) < 378)
        self.assertTrue(mse(jpdata[2], pgxdata) < 3968)

        pgxfile = opj_data_file('baseline/conformance/c1p0_06_3.pgx')
        pgxdata = read_pgx(pgxfile)
        self.assertTrue(peak_tolerance(jpdata[3], pgxdata) == 0)
        self.assertTrue(mse(jpdata[3], pgxdata) == 0)

    def test_NR_DEC_merged_jp2_19_decode(self):
        jfile = opj_data_file('input/nonregression/merged.jp2')
        Jp2k(jfile).read_bands()
        self.assertTrue(True)


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(glymur.version.openjpeg_version_tuple[0] < 2,
                 "Tests not passing until 2.0")
class TestSuite2point0(unittest.TestCase):
    """Runs tests introduced in version 2.0 or that pass only in 2.0"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ETS_C1P0_p0_10_j2k(self):
        jfile = opj_data_file('input/conformance/p0_10.j2k')
        jp2k = Jp2k(jfile)
        jpdata = jp2k[:]

        pgxfile = opj_data_file('baseline/conformance/c1p0_10_0.pgx')
        pgxdata = read_pgx(pgxfile)
        np.testing.assert_array_equal(jpdata[:, :, 0], pgxdata)

        pgxfile = opj_data_file('baseline/conformance/c1p0_10_1.pgx')
        pgxdata = read_pgx(pgxfile)
        np.testing.assert_array_equal(jpdata[:, :, 1], pgxdata)

        pgxfile = opj_data_file('baseline/conformance/c1p0_10_2.pgx')
        pgxdata = read_pgx(pgxfile)
        np.testing.assert_array_equal(jpdata[:, :, 2], pgxdata)

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_broken2_jp2_5_decode(self):
        """
        Invalid marker ID on codestream, Null pointer access upon read.
        """
        jfile = opj_data_file('input/nonregression/broken2.jp2')
        regex = re.compile(r'''Invalid\smarker\sid\sencountered\sat\sbyte\s
                               \d+\sin\scodestream:\s*"0x[a-fA-F0-9]{4}"''',
                           re.VERBOSE)
        with self.assertRaises(IOError):
            with self.assertWarnsRegex(UserWarning, regex):
                Jp2k(jfile)[:]

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_broken4_jp2_7_decode(self):
        jfile = opj_data_file('input/nonregression/broken4.jp2')
        with self.assertRaises(IOError):
            with self.assertWarns(UserWarning):
                # invalid number of subbands, bad marker ID
                Jp2k(jfile)[:]
        self.assertTrue(True)

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_kakadu_v4_4_openjpegv2_broken_j2k_16_decode(self):
        # This test actually passes in 1.5, but produces unpleasant warning
        # messages that cannot be turned off?
        relpath = 'input/nonregression/kakadu_v4-4_openjpegv2_broken.j2k'
        jfile = opj_data_file(relpath)
        if glymur.version.openjpeg_version_tuple[0] < 2:
            with self.assertWarns(UserWarning):
                # Incorrect warning issued about tile parts.
                Jp2k(jfile)[:]
        else:
            Jp2k(jfile)[:]
        self.assertTrue(True)


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(re.match(r'''0|1|2.0.0''',
                          glymur.version.openjpeg_version) is not None,
                 "Only supported in 2.0.1 or higher")
class TestSuite2point1(unittest.TestCase):
    """Runs tests introduced in version 2.0+ or that pass only in 2.0+"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_NR_DEC_gdal_fuzzer_unchecked_num_resolutions_jp2_36_decode(self):
        f = 'input/nonregression/gdal_fuzzer_unchecked_numresolutions.jp2'
        jfile = opj_data_file(f)
        with self.assertWarns(UserWarning):
            # Invalid number of resolutions.
            j = Jp2k(jfile)
            with self.assertRaises(IOError):
                j[:]

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_gdal_fuzzer_check_number_of_tiles_jp2_38_decode(self):
        relpath = 'input/nonregression/gdal_fuzzer_check_number_of_tiles.jp2'
        jfile = opj_data_file(relpath)
        with self.assertWarns(UserWarning):
            # Invalid number of tiles.
            j = Jp2k(jfile)
            with self.assertRaises(IOError):
                j[:]

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_gdal_fuzzer_check_comp_dx_dy_jp2_39_decode(self):
        relpath = 'input/nonregression/gdal_fuzzer_check_comp_dx_dy.jp2'
        jfile = opj_data_file(relpath)
        with self.assertWarns(UserWarning):
            # Invalid subsampling value
            with self.assertRaises(IOError):
                Jp2k(jfile)[:]

    def test_NR_DEC_file_409752_jp2_40_decode(self):
        jfile = opj_data_file('input/nonregression/file409752.jp2')
        with self.assertRaises(RuntimeError):
            Jp2k(jfile)[:]

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_p1_04_j2k_57_decode_0p7_backwards_compatibility(self):
        """
        0.7.x usage deprecated
        """
        jfile = opj_data_file('input/conformance/p1_04.j2k')
        jp2k = Jp2k(jfile)
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings():
                # Suppress a warning due to deprecated syntax
                warnings.simplefilter("ignore")
                tdata = jp2k.read(tile=63)  # last tile
        else:
            with self.assertWarns(DeprecationWarning):
                tdata = jp2k.read(tile=63)  # last tile
        odata = jp2k[:]
        np.testing.assert_array_equal(tdata, odata[896:1024, 896:1024])

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_p1_04_j2k_58_decode_0p7_backwards_compatibility(self):
        """
        0.7.x usage deprecated
        """
        jfile = opj_data_file('input/conformance/p1_04.j2k')
        jp2k = Jp2k(jfile)
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings():
                # Suppress a warning due to deprecated syntax
                tdata = jp2k.read(tile=63, rlevel=2)  # last tile
        else:
            with self.assertWarns(DeprecationWarning):
                tdata = jp2k.read(tile=63, rlevel=2)  # last tile
        odata = jp2k[::4, ::4]
        np.testing.assert_array_equal(tdata, odata[224:256, 224:256])

    def test_NR_DEC_p1_04_j2k_58_decode(self):
        jfile = opj_data_file('input/conformance/p1_04.j2k')
        jp2k = Jp2k(jfile)
        tdata = jp2k[896:1024:4, 896:1024:4]  # last tile
        odata = jp2k[::4, ::4]
        np.testing.assert_array_equal(tdata, odata[224:256, 224:256])

    def test_NR_DEC_p1_04_j2k_59_decode(self):
        jfile = opj_data_file('input/conformance/p1_04.j2k')
        jp2k = Jp2k(jfile)
        tdata = jp2k[128:256, 512:640]  # 2nd row, 5th column
        odata = jp2k[:]
        np.testing.assert_array_equal(tdata, odata[128:256, 512:640])

    def test_NR_DEC_p1_04_j2k_60_decode(self):
        jfile = opj_data_file('input/conformance/p1_04.j2k')
        jp2k = Jp2k(jfile)
        tdata = jp2k[128:256:2, 512:640:2]  # 2nd row, 5th column
        odata = jp2k[::2, ::2]
        np.testing.assert_array_equal(tdata, odata[64:128, 256:320])

    @unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
    def test_NR_DEC_jp2_36_decode(self):
        lst = ('input',
               'nonregression',
               'gdal_fuzzer_assert_in_opj_j2k_read_SQcd_SQcc.patch.jp2')
        jfile = opj_data_file('/'.join(lst))
        with self.assertWarns(UserWarning):
            # Invalid component number.
            j = Jp2k(jfile)
            with self.assertRaises(IOError):
                j[:]


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(re.match(r'''0|1|2.0.0''',
                          glymur.version.openjpeg_version) is not None,
                 "Only supported in 2.0.1 or higher")
class TestReadArea(unittest.TestCase):
    """
    Runs tests introduced in version 2.0+ or that pass only in 2.0+

    Specifically for read method with area parameter.
    """
    @classmethod
    def setUpClass(self):

        jfile = opj_data_file('input/conformance/p1_04.j2k')
        self.j2k = Jp2k(jfile)
        self.j2k_data = self.j2k[:]
        self.j2k_half_data = self.j2k[::2, ::2]
        self.j2k_quarter_data = self.j2k[::4, ::4]

        jfile = opj_data_file('input/conformance/p1_06.j2k')
        self.j2k_p1_06 = Jp2k(jfile)

    def test_NR_DEC_p1_04_j2k_43_decode(self):
        actual = self.j2k[:1024, :1024]
        expected = self.j2k_data
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_44_decode(self):
        actual = self.j2k[640:768, 512:640]
        expected = self.j2k_data[640:768, 512:640]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_45_decode(self):
        actual = self.j2k[896:1024, 896:1024]
        expected = self.j2k_data[896:1024, 896:1024]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_46_decode(self):
        actual = self.j2k[500:800, 100:300]
        expected = self.j2k_data[500:800, 100:300]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_47_decode(self):
        actual = self.j2k[520:600, 260:360]
        expected = self.j2k_data[520:600, 260:360]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_48_decode(self):
        actual = self.j2k[520:660, 260:360]
        expected = self.j2k_data[520:660, 260:360]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_49_decode(self):
        actual = self.j2k[520:600, 360:400]
        expected = self.j2k_data[520:600, 360:400]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_50_decode(self):
        actual = self.j2k[:1024:4, :1024:4]
        expected = self.j2k_quarter_data
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_51_decode(self):
        actual = self.j2k[640:768:4, 512:640:4]
        expected = self.j2k_quarter_data[160:192, 128:160]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_52_decode(self):
        actual = self.j2k[896:1024:4, 896:1024:4]
        expected = self.j2k_quarter_data[224:352, 224:352]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_53_decode(self):
        actual = self.j2k[500:800:4, 100:300:4]
        expected = self.j2k_quarter_data[125:200, 25:75]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_54_decode(self):
        actual = self.j2k[520:600:4, 260:360:4]
        expected = self.j2k_quarter_data[130:150, 65:90]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_55_decode(self):
        actual = self.j2k[520:660:4, 260:360:4]
        expected = self.j2k_quarter_data[130:165, 65:90]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_04_j2k_56_decode(self):
        actual = self.j2k[520:600:4, 360:400:4]
        expected = self.j2k_quarter_data[130:150, 90:100]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p1_06_j2k_70_decode(self):
        actual = self.j2k_p1_06[9:12:2, 9:12:2]
        self.assertEqual(actual.shape, (1, 1, 3))

    def test_NR_DEC_p1_06_j2k_71_decode(self):
        actual = self.j2k_p1_06[10:12:2, 4:10:2]
        self.assertEqual(actual.shape, (1, 3, 3))

    def test_NR_DEC_p1_06_j2k_72_decode(self):
        ssdata = self.j2k_p1_06[3:9:2, 3:9:2]
        self.assertEqual(ssdata.shape, (3, 3, 3))

    def test_NR_DEC_p1_06_j2k_73_decode(self):
        ssdata = self.j2k_p1_06[4:7:2, 4:7:2]
        self.assertEqual(ssdata.shape, (2, 2, 3))

    def test_NR_DEC_p1_06_j2k_74_decode(self):
        ssdata = self.j2k_p1_06[4:5:2, 4:5:2]
        self.assertEqual(ssdata.shape, (1, 1, 3))

    def test_NR_DEC_p1_06_j2k_75_decode(self):
        # Image size would be 0 x 0.
        with self.assertRaises((IOError, OSError)):
            self.j2k_p1_06[9:12:4, 9:12:4]

    def test_NR_DEC_p0_04_j2k_85_decode(self):
        actual = self.j2k[:256, :256]
        expected = self.j2k_data[:256, :256]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_86_decode(self):
        actual = self.j2k[:128, 128:256]
        expected = self.j2k_data[:128, 128:256]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_87_decode(self):
        actual = self.j2k[10:200, 50:120]
        expected = self.j2k_data[10:200, 50:120]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_88_decode(self):
        actual = self.j2k[150:210, 10:190]
        expected = self.j2k_data[150:210, 10:190]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_89_decode(self):
        actual = self.j2k[80:150, 100:200]
        expected = self.j2k_data[80:150, 100:200]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_90_decode(self):
        actual = self.j2k[20:50, 150:200]
        expected = self.j2k_data[20:50, 150:200]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_91_decode(self):
        actual = self.j2k[:256:4, :256:4]
        expected = self.j2k_quarter_data[0:64, 0:64]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_92_decode(self):
        actual = self.j2k[:128:4, 128:256:4]
        expected = self.j2k_quarter_data[:32, 32:64]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_93_decode(self):
        actual = self.j2k[10:200:4, 50:120:4]
        expected = self.j2k_quarter_data[3:50, 13:30]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_94_decode(self):
        actual = self.j2k[150:210:4, 10:190:4]
        expected = self.j2k_quarter_data[38:53, 3:48]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_95_decode(self):
        actual = self.j2k[80:150:4, 100:200:4]
        expected = self.j2k_quarter_data[20:38, 25:50]
        np.testing.assert_array_equal(actual, expected)

    def test_NR_DEC_p0_04_j2k_96_decode(self):
        actual = self.j2k[20:50:4, 150:200:4]
        expected = self.j2k_quarter_data[5:13, 38:50]
        np.testing.assert_array_equal(actual, expected)
