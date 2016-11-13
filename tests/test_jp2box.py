"""Test suite specifically targeting JP2 box layout.
"""
# Standard library imports ...
import doctest
from io import BytesIO
import os
import re
import struct
import sys
import tempfile
import unittest
import warnings

# Third party library imports ...
import numpy as np
import pkg_resources as pkg

# Local imports ...
import glymur
from glymur import Jp2k
from glymur.jp2box import ColourSpecificationBox, ContiguousCodestreamBox
from glymur.jp2box import FileTypeBox, ImageHeaderBox, JP2HeaderBox
from glymur.jp2box import JPEG2000SignatureBox, PaletteBox
from glymur.core import COLOR, OPACITY, SRGB, GREYSCALE
from glymur.core import RED, GREEN, BLUE, GREY, WHOLE_IMAGE
from .fixtures import WINDOWS_TMP_FILE_MSG


def docTearDown(doctest_obj):
    glymur.set_option('parse.full_codestream', False)


def load_tests(loader, tests, ignore):
    """Run doc tests as well."""
    if os.name == "nt":
        # Can't do it on windows, temporary file issue.
        return tests
    tests.addTests(doctest.DocTestSuite('glymur.jp2box',
                                        tearDown=docTearDown))
    return tests


@unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
class TestDataEntryURL(unittest.TestCase):
    """Test suite for DataEntryURL boxes."""
    def setUp(self):
        self.jp2file = glymur.data.nemo()

    @unittest.skipIf(re.match("1.5|2",
                              glymur.version.openjpeg_version) is None,
                     "Must have openjpeg 1.5 or higher to run")
    def test_wrap_greyscale(self):
        """A single component should be wrapped as GREYSCALE."""
        j = Jp2k(self.jp2file)
        data = j[:]
        red = data[:, :, 0]

        # Write it back out as a raw codestream.
        with tempfile.NamedTemporaryFile(suffix=".j2k") as tfile1:
            j2k = glymur.Jp2k(tfile1.name, data=red)

            # Ok, now rewrap it as JP2.  The colorspace should be GREYSCALE.
            with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile2:
                jp2 = j2k.wrap(tfile2.name)
                self.assertEqual(jp2.box[2].box[1].colorspace,
                                 glymur.core.GREYSCALE)

    def test_basic_url(self):
        """Just your most basic URL box."""
        # Wrap our j2k file in a JP2 box along with an interior url box.
        jp2 = Jp2k(self.jp2file)

        url = 'http://glymur.readthedocs.org'
        deurl = glymur.jp2box.DataEntryURLBox(0, (0, 0, 0), url)
        boxes = [box for box in jp2.box if box.box_id != 'uuid']
        boxes.append(deurl)
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            jp22 = jp2.wrap(tfile.name, boxes=boxes)

        actdata = [box.box_id for box in jp22.box]
        expdata = ['jP  ', 'ftyp', 'jp2h', 'jp2c', 'url ']
        self.assertEqual(actdata, expdata)
        self.assertEqual(jp22.box[4].version, 0)
        self.assertEqual(jp22.box[4].flag, (0, 0, 0))
        self.assertEqual(jp22.box[4].url, url)

    def test_null_termination(self):
        """I.9.3.2 specifies that location field must be null terminated."""
        jp2 = Jp2k(self.jp2file)

        url = 'http://glymur.readthedocs.org'
        deurl = glymur.jp2box.DataEntryURLBox(0, (0, 0, 0), url)
        boxes = [box for box in jp2.box if box.box_id != 'uuid']
        boxes.append(deurl)
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            jp22 = jp2.wrap(tfile.name, boxes=boxes)

            self.assertEqual(jp22.box[-1].length, 42)

            # Go to the last box.  Seek past the L, T, version,
            # and flag fields.
            with open(tfile.name, 'rb') as f:
                f.seek(jp22.box[-1].offset + 4 + 4 + 1 + 3)

                nbytes = jp22.box[-1].offset + jp22.box[-1].length - f.tell()
                read_url = f.read(nbytes).decode('utf-8')

                self.assertEqual(url + chr(0), read_url)


@unittest.skipIf(re.match(r'''0|1|2.0.0''',
                          glymur.version.openjpeg_version) is not None,
                 "Not supported until 2.1")
@unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
class TestChannelDefinition(unittest.TestCase):
    """Test suite for channel definition boxes."""

    @classmethod
    def setUpClass(cls):
        """Need a one_plane plane image for greyscale testing."""
        j2k = Jp2k(glymur.data.goodstuff())
        data = j2k[:]
        # Write the first component back out to file.
        with tempfile.NamedTemporaryFile(suffix=".j2k", delete=False) as tfile:
            Jp2k(tfile.name, data=data[:, :, 0])
            cls.one_plane = tfile.name
        # Write the first two components back out to file.
        with tempfile.NamedTemporaryFile(suffix=".j2k", delete=False) as tfile:
            Jp2k(tfile.name, data=data[:, :, 0:1])
            cls.two_planes = tfile.name
        # Write four components back out to file.
        with tempfile.NamedTemporaryFile(suffix=".j2k", delete=False) as tfile:
            shape = (data.shape[0], data.shape[1], 1)
            alpha = np.zeros((shape), dtype=data.dtype)
            data4 = np.concatenate((data, alpha), axis=2)
            Jp2k(tfile.name, data=data4)
            cls.four_planes = tfile.name

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.one_plane)
        os.unlink(cls.two_planes)
        os.unlink(cls.four_planes)

    def setUp(self):
        self.jp2file = glymur.data.nemo()
        self.j2kfile = glymur.data.goodstuff()

        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        self.jp2b = JPEG2000SignatureBox()
        self.ftyp = FileTypeBox()
        self.jp2h = JP2HeaderBox()
        self.jp2c = ContiguousCodestreamBox()
        self.ihdr = ImageHeaderBox(height=height, width=width,
                                   num_components=num_components)
        self.colr_rgb = ColourSpecificationBox(colorspace=SRGB)
        self.colr_gr = ColourSpecificationBox(colorspace=GREYSCALE)

    def tearDown(self):
        pass

    def test_cdef_no_inputs(self):
        """channel_type and association are required inputs."""
        with self.assertRaises(TypeError):
            glymur.jp2box.ChannelDefinitionBox()

    def test_rgb_with_index(self):
        """Just regular RGB."""
        j2k = Jp2k(self.j2kfile)
        channel_type = [COLOR, COLOR, COLOR]
        association = [RED, GREEN, BLUE]
        cdef = glymur.jp2box.ChannelDefinitionBox(index=[0, 1, 2],
                                                  channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_rgb, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)

            jp2 = Jp2k(tfile.name)
            jp2h = jp2.box[2]
            boxes = [box.box_id for box in jp2h.box]
            self.assertEqual(boxes, ['ihdr', 'colr', 'cdef'])
            self.assertEqual(jp2h.box[2].index, (0, 1, 2))
            self.assertEqual(jp2h.box[2].channel_type,
                             (COLOR, COLOR, COLOR))
            self.assertEqual(jp2h.box[2].association,
                             (RED, GREEN, BLUE))

    def test_rgb(self):
        """Just regular RGB, but don't supply the optional index."""
        j2k = Jp2k(self.j2kfile)
        channel_type = [COLOR, COLOR, COLOR]
        association = [RED, GREEN, BLUE]
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_rgb, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)

            jp2 = Jp2k(tfile.name)
            jp2h = jp2.box[2]
            boxes = [box.box_id for box in jp2h.box]
            self.assertEqual(boxes, ['ihdr', 'colr', 'cdef'])
            self.assertEqual(jp2h.box[2].index, (0, 1, 2))
            self.assertEqual(jp2h.box[2].channel_type,
                             (COLOR, COLOR, COLOR))
            self.assertEqual(jp2h.box[2].association,
                             (RED, GREEN, BLUE))

    def test_rgba(self):
        """Just regular RGBA."""
        j2k = Jp2k(self.four_planes)
        channel_type = (COLOR, COLOR, COLOR, OPACITY)
        association = (RED, GREEN, BLUE, WHOLE_IMAGE)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_rgb, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)

            jp2 = Jp2k(tfile.name)
            jp2h = jp2.box[2]
            boxes = [box.box_id for box in jp2h.box]
            self.assertEqual(boxes, ['ihdr', 'colr', 'cdef'])
            self.assertEqual(jp2h.box[2].index, (0, 1, 2, 3))
            self.assertEqual(jp2h.box[2].channel_type, channel_type)
            self.assertEqual(jp2h.box[2].association, association)

    def test_bad_rgba(self):
        """R, G, and B must be specified."""
        j2k = Jp2k(self.four_planes)
        channel_type = (COLOR, COLOR, OPACITY, OPACITY)
        association = (RED, GREEN, BLUE, WHOLE_IMAGE)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_rgb, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_grey(self):
        """Just regular greyscale."""
        j2k = Jp2k(self.one_plane)
        channel_type = (COLOR,)
        association = (GREY,)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_gr, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)

            jp2 = Jp2k(tfile.name)
            jp2h = jp2.box[2]
            boxes = [box.box_id for box in jp2h.box]
            self.assertEqual(boxes, ['ihdr', 'colr', 'cdef'])
            self.assertEqual(jp2h.box[2].index, (0,))
            self.assertEqual(jp2h.box[2].channel_type, channel_type)
            self.assertEqual(jp2h.box[2].association, association)

    def test_grey_alpha(self):
        """Just regular greyscale plus alpha."""
        j2k = Jp2k(self.two_planes)
        channel_type = (COLOR, OPACITY)
        association = (GREY, WHOLE_IMAGE)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_gr, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)

            jp2 = Jp2k(tfile.name)
            jp2h = jp2.box[2]
            boxes = [box.box_id for box in jp2h.box]
            self.assertEqual(boxes, ['ihdr', 'colr', 'cdef'])
            self.assertEqual(jp2h.box[2].index, (0, 1))
            self.assertEqual(jp2h.box[2].channel_type, channel_type)
            self.assertEqual(jp2h.box[2].association, association)

    def test_bad_grey_alpha(self):
        """A greyscale image with alpha layer must specify a color channel"""
        j2k = Jp2k(self.two_planes)

        channel_type = (OPACITY, OPACITY)
        association = (GREY, WHOLE_IMAGE)

        # This cdef box
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)
        boxes = [self.ihdr, self.colr_gr, cdef]
        self.jp2h.box = boxes
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises((OSError, IOError)):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_only_one_cdef_in_jp2h(self):
        """There can only be one channel definition box in the jp2 header."""
        j2k = Jp2k(self.j2kfile)

        channel_type = (COLOR, COLOR, COLOR)
        association = (RED, GREEN, BLUE)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)

        boxes = [self.ihdr, cdef, self.colr_rgb, cdef]
        self.jp2h.box = boxes

        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]

        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_not_in_jp2h(self):
        """need cdef in jp2h"""
        j2k = Jp2k(self.j2kfile)
        boxes = [self.ihdr, self.colr_rgb]
        self.jp2h.box = boxes

        channel_type = (COLOR, COLOR, COLOR)
        association = (RED, GREEN, BLUE)
        cdef = glymur.jp2box.ChannelDefinitionBox(channel_type=channel_type,
                                                  association=association)

        boxes = [self.jp2b, self.ftyp, self.jp2h, cdef, self.jp2c]

        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises((IOError, OSError)):
                j2k.wrap(tfile.name, boxes=boxes)


class TestFileTypeBox(unittest.TestCase):
    """Test suite for ftyp box issues."""

    def setUp(self):
        self.jp2file = glymur.data.nemo()

    def test_bad_brand_on_parse(self):
        """The JP2 file file type box does not contain a valid brand.

        Expect a specific validation error.
        """
        relpath = os.path.join('data', 'issue396.jp2')
        filename = pkg.resource_filename(__name__, relpath)
        with warnings.catch_warnings():
            # Lots of things wrong with this file.
            warnings.simplefilter('ignore')
            with self.assertRaises(IOError):
                Jp2k(filename)

    def test_brand_unknown(self):
        """A ftyp box brand must be 'jp2 ' or 'jpx '."""
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            ftyp = glymur.jp2box.FileTypeBox(brand='jp3')
        with tempfile.TemporaryFile() as tfile:
            with self.assertRaises(IOError):
                ftyp.write(tfile)

    def test_cl_entry_unknown(self):
        """A ftyp box cl list can only contain 'jp2 ', 'jpx ', or 'jpxb'."""
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            # Bad compatibility list item.
            ftyp = glymur.jp2box.FileTypeBox(compatibility_list=['jp3'])
        with tempfile.TemporaryFile() as tfile:
            with self.assertRaises(IOError):
                ftyp.write(tfile)

    @unittest.skipIf(sys.hexversion < 0x03000000,
                     "assertWarns not introduced until 3.2")
    def test_cl_entry_not_utf8(self):
        """A ftyp box cl list entry must be utf-8 decodable."""
        with open(self.jp2file, mode='rb') as f:
            data = f.read()

        # Replace bytes 28-32 with bad utf-8 data
        data = data[:28] + b'\xff\xff\xff\xff' + data[32:]
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile:
            tfile.write(data)
            tfile.flush()

            with self.assertWarns(UserWarning):
                Jp2k(tfile.name)


class TestColourSpecificationBox(unittest.TestCase):
    """Test suite for colr box instantiation."""

    def setUp(self):
        self.j2kfile = glymur.data.goodstuff()

        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        self.jp2b = JPEG2000SignatureBox()
        self.ftyp = FileTypeBox()
        self.jp2h = JP2HeaderBox()
        self.jp2c = ContiguousCodestreamBox()
        self.ihdr = ImageHeaderBox(height=height, width=width,
                                   num_components=num_components)

    def test_bad_method_printing(self):
        """
        A bad method should not cause a printing failure.

        It's enough that it doesn't error out.
        """
        relpath = os.path.join('data', 'issue405.dat')
        filename = pkg.resource_filename(__name__, relpath)
        with open(filename, 'rb') as f:
            f.seek(8)
            with warnings.catch_warnings():
                # Lots of things wrong with this file.
                warnings.simplefilter('ignore')
                box = ColourSpecificationBox.parse(f, length=80, offset=0)
        str(box)

    @unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
    def test_colr_with_out_enum_cspace(self):
        """must supply an enumerated colorspace when writing"""
        j2k = Jp2k(self.j2kfile)

        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        boxes[2].box = [self.ihdr, ColourSpecificationBox(colorspace=None)]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    @unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
    def test_missing_colr_box(self):
        """jp2h must have a colr box"""
        j2k = Jp2k(self.j2kfile)
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        boxes[2].box = [self.ihdr]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    @unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
    def test_bad_approx_jp2_field(self):
        """JP2 has requirements for approx field"""
        j2k = Jp2k(self.j2kfile)
        boxes = [self.jp2b, self.ftyp, self.jp2h, self.jp2c]
        colr = ColourSpecificationBox(colorspace=SRGB, approximation=1)
        boxes[2].box = [self.ihdr, colr]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_default_colr(self):
        """basic colr instantiation"""
        colr = ColourSpecificationBox(colorspace=SRGB)
        self.assertEqual(colr.method, glymur.core.ENUMERATED_COLORSPACE)
        self.assertEqual(colr.precedence, 0)
        self.assertEqual(colr.approximation, 0)
        self.assertEqual(colr.colorspace, SRGB)
        self.assertIsNone(colr.icc_profile)

    def test_colr_with_bad_color(self):
        """colr must have a valid color, strange as though that may sound."""
        colorspace = -1
        approx = 0
        colr = ColourSpecificationBox(colorspace=colorspace,
                                      approximation=approx)
        with tempfile.TemporaryFile() as tfile:
            with self.assertRaises(IOError):
                colr.write(tfile)

    def test_write_colr_with_bad_method(self):
        """
        A colr box has an invalid method.

        Expect an IOError when trying to write to file.
        """
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            colr = ColourSpecificationBox(colorspace=SRGB, method=5)
        with tempfile.TemporaryFile() as tfile:
            with self.assertRaises(IOError):
                colr.write(tfile)


@unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
class TestPaletteBox(unittest.TestCase):
    """Test suite for pclr box instantiation."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_writing_with_different_bitdepths(self):
        """Bitdepths must be the same when writing."""
        palette = np.array([[255, 0, 255], [0, 255, 0]], dtype=np.uint16)
        bps = (8, 16, 8)
        signed = (False, False, False)
        pclr = glymur.jp2box.PaletteBox(palette, bits_per_component=bps,
                                        signed=signed)
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile:
            with self.assertRaises(IOError):
                pclr.write(tfile)

    def test_signed_components(self):
        """
        Palettes with signed components are not supported.
        """
        b = BytesIO()

        # L, T
        b.write(struct.pack('>I4s', 20, b'pclr'))

        # Palette is 2 rows, 3 columns
        ncols = 3
        nrows = 2
        b.write(struct.pack('>HB', nrows, ncols))

        # bits per sample is 8, but signed
        bps = (np.int8(7), np.int8(7), np.int8(7))
        bps_signed = (x | 0x80 for x in bps)
        b.write(struct.pack('BBB', *bps_signed))

        # Write the palette itself.
        #
        buffer = np.int8([[0, 0, 0], [127, 127, 127]])
        b.write(struct.pack('BBB', *buffer[0]))
        b.write(struct.pack('BBB', *buffer[1]))

        # Seek back to point after L, T
        b.seek(8)
        with self.assertRaises(IOError):
            PaletteBox.parse(b, 8, 20)


class TestJp2Boxes(unittest.TestCase):
    """Tests for canonical JP2 boxes."""

    def setUp(self):
        self.jpxfile = glymur.data.jpxfile()

    def test_default_jp2k(self):
        """Should be able to instantiate a JPEG2000SignatureBox"""
        jp2k = glymur.jp2box.JPEG2000SignatureBox()
        self.assertEqual(jp2k.signature, (13, 10, 135, 10))

    def test_default_ftyp(self):
        """Should be able to instantiate a FileTypeBox"""
        ftyp = glymur.jp2box.FileTypeBox()
        self.assertEqual(ftyp.brand, 'jp2 ')
        self.assertEqual(ftyp.minor_version, 0)
        self.assertEqual(ftyp.compatibility_list, ['jp2 '])

    def test_default_ihdr(self):
        """Should be able to instantiate an image header box."""
        ihdr = glymur.jp2box.ImageHeaderBox(height=512, width=256,
                                            num_components=3)
        self.assertEqual(ihdr.height, 512)
        self.assertEqual(ihdr.width, 256)
        self.assertEqual(ihdr.num_components, 3)
        self.assertEqual(ihdr.bits_per_component, 8)
        self.assertFalse(ihdr.signed)
        self.assertFalse(ihdr.colorspace_unknown)

    def test_default_jp2headerbox(self):
        """Should be able to set jp2h boxes."""
        box = JP2HeaderBox()
        box.box = [ImageHeaderBox(height=512, width=256),
                   ColourSpecificationBox(colorspace=glymur.core.GREYSCALE)]
        self.assertTrue(True)

    def test_default_ccodestreambox(self):
        """Raw instantiation should not produce a main_header."""
        box = ContiguousCodestreamBox()
        self.assertEqual(box.box_id, 'jp2c')
        self.assertIsNone(box.codestream)

    def test_codestream_main_header_offset(self):
        """
        main_header_offset is an attribute of the ContiguousCodesStream box
        """
        j = Jp2k(self.jpxfile)
        self.assertEqual(j.box[5].main_header_offset,
                         j.box[5].offset + 8)
