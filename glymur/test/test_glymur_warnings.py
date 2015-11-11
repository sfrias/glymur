"""
Test suite for warnings issued by glymur.
"""
from io import BytesIO
import os
import re
import struct
import sys
import tempfile
import unittest
import warnings

from glymur import Jp2k
import glymur
from glymur.jp2k import InvalidJP2ColourspaceMethodWarning
from glymur.jp2box import InvalidColourspaceMethod
from glymur.jp2box import InvalidICCProfileLengthWarning

from .fixtures import opj_data_file, OPJ_DATA_ROOT
from .fixtures import WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG


@unittest.skipIf(OPJ_DATA_ROOT is None,
                 "OPJ_DATA_ROOT environment variable not set")
@unittest.skipIf(WARNING_INFRASTRUCTURE_ISSUE, WARNING_INFRASTRUCTURE_MSG)
class TestWarningsOpj(unittest.TestCase):
    """Test suite for warnings issued by glymur."""

    def test_exceeded_box_length(self):
        """
        should warn if reading past end of a box

        Verify that a warning is issued if we read past the end of a box
        This file has a palette (pclr) box whose length is impossibly
        short.
        """
        infile = os.path.join(OPJ_DATA_ROOT,
                              'input/nonregression/mem-b2ace68c-1381.jp2')
        regex = re.compile(r'''Encountered\san\sunrecoverable\sValueError\s
                               while\sparsing\sa\sPalette\sbox\sat\sbyte\s
                               offset\s\d+\.\s+The\soriginal\serror\smessage\s
                               was\s"total\ssize\sof\snew\sarray\smust\sbe\s
                               unchanged"''',
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(infile)

    def test_NR_gdal_fuzzer_check_comp_dx_dy_jp2_dump(self):
        """
        Invalid subsampling value.
        """
        lst = ['input', 'nonregression', 'gdal_fuzzer_check_comp_dx_dy.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\ssubsampling\svalue\sfor\scomponent\s
                               \d+:\s+
                               dx=\d+,\s*dy=\d+""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile).get_codestream()

    def test_NR_gdal_fuzzer_assert_in_opj_j2k_read_SQcd_SQcc_patch_jp2(self):
        lst = ['input', 'nonregression',
               'gdal_fuzzer_assert_in_opj_j2k_read_SQcd_SQcc.patch.jp2']
        jfile = opj_data_file('/'.join(lst))
        regex = re.compile(r"""Invalid\scomponent\snumber\s\(\d+\),\s
                               number\sof\scomponents\sis\sonly\s\d+""",
                           re.VERBOSE)
        with self.assertWarnsRegex(UserWarning, regex):
            Jp2k(jfile).get_codestream()

    def test_bad_rsiz(self):
        """Should warn if RSIZ is bad.  Issue196"""
        filename = opj_data_file('input/nonregression/edf_c2_1002767.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid profile'):
            Jp2k(filename).get_codestream()

    def test_bad_wavelet_transform(self):
        """Should warn if wavelet transform is bad.  Issue195"""
        filename = opj_data_file('input/nonregression/edf_c2_10025.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid wavelet transform'):
            Jp2k(filename).get_codestream()

    def test_invalid_progression_order(self):
        """Should still be able to parse even if prog order is invalid."""
        jfile = opj_data_file('input/nonregression/2977.pdf.asan.67.2198.jp2')
        with self.assertWarnsRegex(UserWarning, 'Invalid progression order'):
            Jp2k(jfile).get_codestream()

    def test_tile_height_is_zero(self):
        """Zero tile height should not cause an exception."""
        filename = 'input/nonregression/2539.pdf.SIGFPE.706.1712.jp2'
        filename = opj_data_file(filename)
        with self.assertWarnsRegex(UserWarning, 'Invalid tile dimensions'):
            Jp2k(filename).get_codestream()

    @unittest.skipIf(os.name == "nt", "Temporary file issue on window.")
    def test_unknown_marker_segment(self):
        """Should warn for an unknown marker."""
        # Let's inject a marker segment whose marker does not appear to
        # be valid.  We still parse the file, but warn about the offending
        # marker.
        filename = os.path.join(OPJ_DATA_ROOT, 'input/conformance/p0_01.j2k')
        with tempfile.NamedTemporaryFile(suffix='.j2k') as tfile:
            with open(filename, 'rb') as ifile:
                # Everything up until the first QCD marker.
                read_buffer = ifile.read(45)
                tfile.write(read_buffer)

                # Write the new marker segment, 0xff79 = 65401
                read_buffer = struct.pack('>HHB', int(65401), int(3), int(0))
                tfile.write(read_buffer)

                # Get the rest of the input file.
                read_buffer = ifile.read()
                tfile.write(read_buffer)
                tfile.flush()

                with self.assertWarnsRegex(UserWarning, 'Unrecognized marker'):
                    Jp2k(tfile.name).get_codestream()


class TestWarnings(unittest.TestCase):

    def setUp(self):
        self.jp2file = glymur.data.nemo()

    def test_NR_gdal_fuzzer_check_number_of_tiles(self):
        """
        Has an impossible tiling setup.

        Original test file was input/nonregression
                               /gdal_fuzzer_check_number_of_tiles.jp2
        """
        fp = BytesIO()

        buffer = struct.pack('>H', 47)  # length

        # kwargs = {'rsiz': 1,
        #           'xysiz': (20, 16777236),
        #           'xyosiz': (0, 0),
        #           'xytsiz': (20, 20),
        #           'xytosiz': (0, 0),
        #           'Csiz': 3,
        #           'bitdepth': (8, 8, 8),
        #           'signed':  (False, False, False),
        #           'xyrsiz': ((1, 1, 1), (1, 1, 1)),
        #           'length': 47,
        #           'offset': 2}
        buffer += struct.pack('>HIIIIIIIIH', 1, 20, 16777236, 0, 0, 20, 20,
                              0, 0, 3)
        buffer += struct.pack('>BBBBBBBBB', 7, 1, 1, 7, 1, 1, 7, 1, 1)
        fp.write(buffer)
        fp.seek(0)

        
        exp_warning = glymur.codestream.InvalidNumberOfTilesWarning
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings(record=True) as w:
                segment = glymur.codestream.Codestream._parse_siz_segment(fp)
            assert issubclass(w[-1].category, exp_warning)
        else:
            with self.assertWarns(exp_warning):
                segment = glymur.codestream.Codestream._parse_siz_segment(fp)

    def test_NR_gdal_fuzzer_unchecked_numresolutions_dump(self):
        """
        Has an invalid number of resolutions.

        Original test file was input/nonregression/
                               gdal_fuzzer_unchecked_numresolutions.jp2
        """
        spcod = struct.pack('>BHBBBBBB', 0, 1, 1, 64, 3, 3, 0, 0)
        spcod = bytearray(spcod)
        exp_warning = glymur.codestream.InvalidNumberOfResolutionsWarning
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings(record=True) as w:
                segment = glymur.codestream.CODsegment(0, spcod, 12, 174)
            assert issubclass(w[-1].category, exp_warning)
        else:
            with self.assertWarns(exp_warning):
                segment = glymur.codestream.CODsegment(0, spcod, 12, 174)

    def test_NR_DEC_issue188_beach_64bitsbox_jp2_41_decode(self):
        """
        Has an 'XML ' box instead of 'xml '.  Yes that is pedantic, but it
        really does deserve a warning.

        Original file tested was nonregression/issue188_beach_64bitsbox.jp2

        The best way to test this really is to tack a new box onto the end of
        an existing file.
        """
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jp2') as ofile:
            with open(self.jp2file, 'rb') as ifile:
                ofile.write(ifile.read())

                buffer = struct.pack('>I4s', 32, b'XML ')
                s = "<stuff>goes here</stuff>"
                buffer += s.encode('utf-8')
                ofile.write(buffer)
                ofile.flush()

            if sys.hexversion < 0x03000000:
                with warnings.catch_warnings(record=True) as w:
                    Jp2k(ofile.name)
                assert issubclass(w[-1].category,
                                  glymur.jp2box.UnrecognizedBoxWarning)
            else:
                with self.assertWarns(glymur.jp2box.UnrecognizedBoxWarning):
                    Jp2k(ofile.name)

    def test_truncated_icc_profile(self):
        """
        Validate a warning for a truncated ICC profile
        """
        obj = BytesIO()
        obj.write(b'\x00' * 66)

        # Write a colr box with a truncated ICC profile.
        # profile.
        buffer = struct.pack('>I4s', 47, b'colr')
        buffer += struct.pack('>BBB', 2, 0, 0)

        buffer += b'\x00' * 12 + b'scnr' + b'XYZ ' + b'Lab '
        # Need a date in bytes 24:36
        buffer += struct.pack('>HHHHHH', 1966, 2, 15, 0, 0, 0)
        obj.write(buffer)
        obj.seek(74) 

        # Should be able to read the colr box now
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings(record=True) as w:
                box = glymur.jp2box.ColourSpecificationBox.parse(obj, 66, 47)
                assert issubclass(w[-1].category,
                                  InvalidICCProfileLengthWarning)
        else:
            with self.assertWarns(InvalidICCProfileLengthWarning):
                box = glymur.jp2box.ColourSpecificationBox.parse(obj, 66, 47)
        
    def test_invalid_colour_specification_method(self):
        """
        should not error out with invalid colour specification method
        """
        obj = BytesIO()
        obj.write(b'\x00' * 66)

        # Write a colr box with a bad method (254).  This requires an ICC
        # profile.
        buffer = struct.pack('>I4s', 143, b'colr')
        buffer += struct.pack('>BBB', 254, 0, 0)

        buffer += b'\x00' * 12 + b'scnr' + b'XYZ ' + b'Lab '
        # Need a date in bytes 24:36
        buffer += struct.pack('>HHHHHH', 1966, 2, 15, 0, 0, 0)
        buffer += b'\x00' * 92
        obj.write(buffer)
        obj.seek(74) 

        # Should be able to read the colr box now
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings(record=True) as w:
                box = glymur.jp2box.ColourSpecificationBox.parse(obj, 66, 143)
                assert issubclass(w[-1].category, InvalidColourspaceMethod)
        else:
            with self.assertWarns(glymur.jp2box.InvalidColourspaceMethod):
                box = glymur.jp2box.ColourSpecificationBox.parse(obj, 66, 143)
        
    def test_bad_color_space_specification(self):
        """
        Verify that a warning is issued if the color space method is invalid.

        For JP2, the method must be either 1 or 2.
        """
        jp2 = glymur.Jp2k(self.jp2file)
        jp2.box[2].box[1].method = 3
        if sys.hexversion < 0x03000000:
            with warnings.catch_warnings(record=True) as w:
                jp2._validate()
                assert issubclass(w[-1].category,
                                  InvalidJP2ColourspaceMethodWarning)
        else:
            with self.assertWarns(InvalidJP2ColourspaceMethodWarning):
                jp2._validate()

if __name__ == "__main__":
    unittest.main()
