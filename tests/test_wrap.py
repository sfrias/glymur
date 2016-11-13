"""Test suite specifically targeting wrap method.
"""
# Standard library imports ...
import os
import struct
import tempfile
import unittest

# Third party library imports ...
import numpy as np

# Local imports ...
import glymur
from glymur import Jp2k
from glymur.jp2box import (
    ColourSpecificationBox, ContiguousCodestreamBox, FileTypeBox,
    ImageHeaderBox, JP2HeaderBox, JPEG2000SignatureBox
)
from .fixtures import WINDOWS_TMP_FILE_MSG


@unittest.skipIf(os.name == "nt", WINDOWS_TMP_FILE_MSG)
class TestSuite(unittest.TestCase):
    """Tests for wrap method."""

    def setUp(self):
        self.j2kfile = glymur.data.goodstuff()
        self.jp2file = glymur.data.nemo()
        self.jpxfile = glymur.data.jpxfile()

    def tearDown(self):
        pass

    def verify_wrapped_raw(self, jp2file):
        """Shared fixture"""
        jp2 = Jp2k(jp2file)
        self.assertEqual(len(jp2.box), 4)

        self.assertEqual(jp2.box[0].box_id, 'jP  ')
        self.assertEqual(jp2.box[0].offset, 0)
        self.assertEqual(jp2.box[0].length, 12)
        self.assertEqual(jp2.box[0].longname, 'JPEG 2000 Signature')

        self.assertEqual(jp2.box[1].box_id, 'ftyp')
        self.assertEqual(jp2.box[1].offset, 12)
        self.assertEqual(jp2.box[1].length, 20)
        self.assertEqual(jp2.box[1].longname, 'File Type')

        self.assertEqual(jp2.box[2].box_id, 'jp2h')
        self.assertEqual(jp2.box[2].offset, 32)
        self.assertEqual(jp2.box[2].length, 45)
        self.assertEqual(jp2.box[2].longname, 'JP2 Header')

        self.assertEqual(jp2.box[3].box_id, 'jp2c')
        self.assertEqual(jp2.box[3].offset, 77)
        self.assertEqual(jp2.box[3].length, 115228)

        # jp2h super box
        self.assertEqual(len(jp2.box[2].box), 2)

        self.assertEqual(jp2.box[2].box[0].box_id, 'ihdr')
        self.assertEqual(jp2.box[2].box[0].offset, 40)
        self.assertEqual(jp2.box[2].box[0].length, 22)
        self.assertEqual(jp2.box[2].box[0].longname, 'Image Header')
        self.assertEqual(jp2.box[2].box[0].height, 800)
        self.assertEqual(jp2.box[2].box[0].width, 480)
        self.assertEqual(jp2.box[2].box[0].num_components, 3)
        self.assertEqual(jp2.box[2].box[0].bits_per_component, 8)
        self.assertEqual(jp2.box[2].box[0].signed, False)
        self.assertEqual(jp2.box[2].box[0].compression, 7)
        self.assertEqual(jp2.box[2].box[0].colorspace_unknown, False)
        self.assertEqual(jp2.box[2].box[0].ip_provided, False)

        self.assertEqual(jp2.box[2].box[1].box_id, 'colr')
        self.assertEqual(jp2.box[2].box[1].offset, 62)
        self.assertEqual(jp2.box[2].box[1].length, 15)
        self.assertEqual(jp2.box[2].box[1].longname, 'Colour Specification')
        self.assertEqual(jp2.box[2].box[1].precedence, 0)
        self.assertEqual(jp2.box[2].box[1].approximation, 0)
        self.assertEqual(jp2.box[2].box[1].colorspace, glymur.core.SRGB)
        self.assertIsNone(jp2.box[2].box[1].icc_profile)

    def test_wrap(self):
        """basic test for rewrapping a j2c file, no specified boxes"""
        j2k = Jp2k(self.j2kfile)
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name)
            self.verify_wrapped_raw(tfile.name)

    def test_jpx_to_jp2(self):
        """basic test for rewrapping a jpx file"""
        jpx = Jp2k(self.jpxfile)
        # Use only the signature, file type, header, and 1st codestream.
        lst = [0, 1, 2, 5]
        boxes = [jpx.box[idx] for idx in lst]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            jp2 = jpx.wrap(tfile.name, boxes=boxes)

        # Verify the outer boxes.
        boxes = [box.box_id for box in jp2.box]
        self.assertEqual(boxes, ['jP  ', 'ftyp', 'jp2h', 'jp2c'])

        # Verify the inside boxes.
        boxes = [box.box_id for box in jp2.box[2].box]
        self.assertEqual(boxes, ['ihdr', 'colr', 'pclr', 'cmap'])

        expected_offsets = [0, 12, 40, 887]
        for j, offset in enumerate(expected_offsets):
            self.assertEqual(jp2.box[j].offset, offset)

    def test_wrap_jp2(self):
        """basic test for rewrapping a jp2 file, no specified boxes"""
        j2k = Jp2k(self.jp2file)
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            jp2 = j2k.wrap(tfile.name)
        boxes = [box.box_id for box in jp2.box]
        self.assertEqual(boxes, ['jP  ', 'ftyp', 'jp2h', 'jp2c'])

    def test_wrap_jp2_Lzero(self):
        """Wrap jp2 with jp2c box length is zero"""
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with open(self.jp2file, 'rb') as ifile:
                tfile.write(ifile.read())
            # Rewrite with codestream length as zero.
            tfile.seek(3223)
            tfile.write(struct.pack('>I', 0))
            tfile.flush()
            jp2 = Jp2k(tfile.name)

            with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile2:
                jp2 = jp2.wrap(tfile2.name)
        boxes = [box for box in jp2.box]
        self.assertEqual(boxes[3].length, 1132296)

    def test_wrap_jp2_Lone(self):
        """Wrap jp2 with jp2c box length is 1, implies Q field"""
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with open(self.jp2file, 'rb') as ifile:
                tfile.write(ifile.read(3223))
                # Write new L, T, Q fields
                tfile.write(struct.pack('>I4sQ', 1, b'jp2c', 1132296 + 8))
                # skip over the old L, T fields
                ifile.seek(3231)
                tfile.write(ifile.read())
            tfile.flush()
            jp2 = Jp2k(tfile.name)

            with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile2:
                jp2 = jp2.wrap(tfile2.name)
        boxes = [box for box in jp2.box]
        self.assertEqual(boxes[3].length, 1132296 + 8)

    def test_wrap_compatibility_not_jp2(self):
        """File type compatibility must contain jp2"""
        jp2 = Jp2k(self.jp2file)
        boxes = [box for box in jp2.box]
        boxes[1].compatibility_list = ['jpx ']
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                jp2.wrap(tfile.name, boxes=boxes)

    def test_empty_jp2h(self):
        """JP2H box list cannot be empty."""
        jp2 = Jp2k(self.jp2file)
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            boxes = jp2.box
            # Right here the jp2h superbox has two child boxes.  Empty out that
            # list to trigger the error.
            boxes[2].box = []
            with self.assertRaises(IOError):
                jp2.wrap(tfile.name, boxes=boxes)

    def test_default_layout_with_boxes(self):
        """basic test for rewrapping a jp2 file, boxes specified"""
        j2k = Jp2k(self.j2kfile)
        boxes = [JPEG2000SignatureBox(),
                 FileTypeBox(),
                 JP2HeaderBox(),
                 ContiguousCodestreamBox()]
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)
        boxes[2].box = [ImageHeaderBox(height=height,
                                       width=width,
                                       num_components=num_components),
                        ColourSpecificationBox(colorspace=glymur.core.SRGB)]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            j2k.wrap(tfile.name, boxes=boxes)
            self.verify_wrapped_raw(tfile.name)

    def test_ihdr_not_first_in_jp2h(self):
        """The specification says that ihdr must be the first box in jp2h."""
        j2k = Jp2k(self.j2kfile)
        boxes = [JPEG2000SignatureBox(),
                 FileTypeBox(),
                 JP2HeaderBox(),
                 ContiguousCodestreamBox()]
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)
        boxes[2].box = [ColourSpecificationBox(colorspace=glymur.core.SRGB),
                        ImageHeaderBox(height=height,
                                       width=width,
                                       num_components=num_components)]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_first_boxes_jp_and_ftyp(self):
        """first two boxes must be jP followed by ftyp"""
        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        jp2b = JPEG2000SignatureBox()
        ftyp = FileTypeBox()
        jp2h = JP2HeaderBox()
        jp2c = ContiguousCodestreamBox()
        colr = ColourSpecificationBox(colorspace=glymur.core.SRGB)
        ihdr = ImageHeaderBox(height=height, width=width,
                              num_components=num_components)
        jp2h.box = [ihdr, colr]
        boxes = [ftyp, jp2b, jp2h, jp2c]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_pclr_not_in_jp2h(self):
        """A palette box must reside in a JP2 header box."""
        palette = np.array([[255, 0, 255], [0, 255, 0]], dtype=np.int32)
        bps = (8, 8, 8)
        pclr = glymur.jp2box.PaletteBox(palette=palette,
                                        bits_per_component=bps,
                                        signed=(True, False, True))

        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        jp2b = JPEG2000SignatureBox()
        ftyp = FileTypeBox()
        jp2h = JP2HeaderBox()
        jp2c = ContiguousCodestreamBox()
        colr = ColourSpecificationBox(colorspace=glymur.core.SRGB)
        ihdr = ImageHeaderBox(height=height, width=width,
                              num_components=num_components)
        jp2h.box = [ihdr, colr]
        boxes = [jp2b, ftyp, jp2h, jp2c, pclr]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_jp2h_not_preceeding_jp2c(self):
        """jp2h must precede jp2c"""
        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        jp2b = JPEG2000SignatureBox()
        ftyp = FileTypeBox()
        jp2h = JP2HeaderBox()
        jp2c = ContiguousCodestreamBox()
        colr = ColourSpecificationBox(colorspace=glymur.core.SRGB)
        ihdr = ImageHeaderBox(height=height, width=width,
                              num_components=num_components)
        jp2h.box = [ihdr, colr]
        boxes = [jp2b, ftyp, jp2c, jp2h]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_missing_codestream(self):
        """Need a codestream box in order to call wrap method."""
        j2k = Jp2k(self.j2kfile)
        codestream = j2k.get_codestream()
        height = codestream.segment[1].ysiz
        width = codestream.segment[1].xsiz
        num_components = len(codestream.segment[1].xrsiz)

        jp2k = JPEG2000SignatureBox()
        ftyp = FileTypeBox()
        jp2h = JP2HeaderBox()
        ihdr = ImageHeaderBox(height=height, width=width,
                              num_components=num_components)
        jp2h.box = [ihdr]
        boxes = [jp2k, ftyp, jp2h]
        with tempfile.NamedTemporaryFile(suffix=".jp2") as tfile:
            with self.assertRaises(IOError):
                j2k.wrap(tfile.name, boxes=boxes)

    def test_wrap_jpx_to_jp2_with_unadorned_jpch(self):
        """A JPX file rewrapped with plain jpch is not allowed."""
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile1:
            jpx = Jp2k(self.jpxfile)
            boxes = [jpx.box[0], jpx.box[1], jpx.box[2],
                     glymur.jp2box.ContiguousCodestreamBox()]
            with self.assertRaises(IOError):
                jpx.wrap(tfile1.name, boxes=boxes)

    def test_wrap_jpx_to_jp2_with_incorrect_jp2c_offset(self):
        """Reject A JPX file rewrapped with bad jp2c offset."""
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile1:
            jpx = Jp2k(self.jpxfile)
            jpch = jpx.box[5]

            # The offset should be 902.
            jpch.offset = 901
            jpch.length = 313274
            boxes = [jpx.box[0], jpx.box[1], jpx.box[2], jpch]
            with self.assertRaises(IOError):
                jpx.wrap(tfile1.name, boxes=boxes)

    def test_wrap_jpx_to_jp2_with_correctly_specified_jp2c(self):
        """Accept A JPX file rewrapped with good jp2c."""
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile1:
            jpx = Jp2k(self.jpxfile)
            jpch = jpx.box[5]

            # This time get it right.
            jpch.offset = 903
            jpch.length = 313274
            boxes = [jpx.box[0], jpx.box[1], jpx.box[2], jpch]
            jp2 = jpx.wrap(tfile1.name, boxes=boxes)

        act_ids = [box.box_id for box in jp2.box]
        exp_ids = ['jP  ', 'ftyp', 'jp2h', 'jp2c']
        self.assertEqual(act_ids, exp_ids)

        act_offsets = [box.offset for box in jp2.box]
        exp_offsets = [0, 12, 40, 887]
        self.assertEqual(act_offsets, exp_offsets)

        act_lengths = [box.length for box in jp2.box]
        exp_lengths = [12, 28, 847, 313274]
        self.assertEqual(act_lengths, exp_lengths)

    def test_full_blown_jpx(self):
        """Rewrap a jpx file."""
        with tempfile.NamedTemporaryFile(suffix='.jp2') as tfile1:
            jpx = Jp2k(self.jpxfile)
            idx = (list(range(5)) +
                   list(range(9, 12)) + list(range(6, 9))) + [12]
            boxes = [jpx.box[j] for j in idx]
            jpx2 = jpx.wrap(tfile1.name, boxes=boxes)
            exp_ids = [box.box_id for box in boxes]
            lengths = [box.length for box in jpx.box]
            exp_lengths = [lengths[j] for j in idx]
        act_ids = [box.box_id for box in jpx2.box]
        act_lengths = [box.length for box in jpx2.box]
        self.assertEqual(exp_ids, act_ids)
        self.assertEqual(exp_lengths, act_lengths)
