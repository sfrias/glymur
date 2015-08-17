from collections import OrderedDict
from io import BytesIO
import struct
import sys
import warnings

import numpy as np

from .lib import tiff as _tiflib


TIFF_NOTYPE = 0
TIFF_BYTE = 1
TIFF_ASCII = 2
TIFF_SHORT = 3
TIFF_LONG = 4
TIFF_RATIONAL = 5
TIFF_SBYTE = 6
TIFF_UNDEFINED = 7
TIFF_SSHORT = 8
TIFF_SLONG = 9
TIFF_SRATIONAL = 10
TIFF_FLOAT = 11
TIFF_DOUBLE = 12
TIFF_IFD = 13
TIFF_LONG8 = 16
TIFF_SLONG8 = 17
TIFF_IFD8 = 18

TIFFTAG_IMAGEWIDTH = 256
TIFFTAG_IMAGELENGTH = 257
TIFFTAG_BITSPERSAMPLE = 258
TIFFTAG_PHOTOMETRIC = 262
TIFFTAG_STRIPBYTEOFFSETS = 273
TIFFTAG_SAMPLESPERPIXEL = 277
TIFFTAG_ROWSPERSTRIP = 278
TIFFTAG_STRIPBYTECOUNTS = 279
PHOTOMETRIC_MINISWHITE = 0
PHOTOMETRIC_MINISBLACK = 1
PHOTOMETRIC_RGB = 2
PHOTOMETRIC_PALETTE = 3
PHOTOMETRIC_MASK = 4
PHOTOMETRIC_SEPARATED = 5
PHOTOMETRIC_YCBCR = 6
PHOTOMETRIC_CIELAB = 8
PHOTOMETRIC_ICCLAB = 9
PHOTOMETRIC_ITULAB = 10
PHOTOMETRIC_CFA = 32803
PHOTOMETRIC_LOGL = 32844
PHOTOMETRIC_LOGLUV = 32845

TIFFTAG_SAMPLESPERPIXEL = 277

_EXIFIMAGE = {
    11: 'ProcessingSoftware',
    254: 'NewSubfileType',
    255: 'SubfileType',
    256: 'ImageWidth',
    257: 'ImageLength',
    258: 'BitsPerSample',
    259: 'Compression',
    262: 'PhotometricInterpretation',
    263: 'Threshholding',
    264: 'CellWidth',
    265: 'CellLength',
    266: 'FillOrder',
    269: 'DocumentName',
    270: 'ImageDescription',
    271: 'Make',
    272: 'Model',
    273: 'StripOffsets',
    274: 'Orientation',
    277: 'SamplesPerPixel',
    278: 'RowsPerStrip',
    279: 'StripByteCounts',
    280: 'MinSampleValue',
    281: 'MaxSampleValue',
    282: 'XResolution',
    283: 'YResolution',
    284: 'PlanarConfiguration',
    285: 'PageName',
    286: 'XPosition',
    287: 'YPosition',
    288: 'FreeOffsets',
    289: 'FreeBytesCounts',
    290: 'GrayResponseUnit',
    291: 'GrayResponseCurve',
    292: 'T4Options',
    293: 'T6Options',
    296: 'ResolutionUnit',
    297: 'PageNumber',
    300: 'ColorResponseUnit',
    301: 'TransferFunction',
    305: 'Software',
    306: 'DateTime',
    315: 'Artist',
    316: 'HostComputer',
    317: 'Predictor',
    318: 'WhitePoint',
    319: 'PrimaryChromaticities',
    320: 'ColorMap',
    321: 'HalftoneHints',
    322: 'TileWidth',
    323: 'TileLength',
    324: 'TileOffsets',
    325: 'TileByteCounts',
    326: 'BadFaxLines',
    327: 'CleanFaxData',
    328: 'ConsecutiveBadFaxLines',
    330: 'SubIFDs',
    332: 'InkSet',
    333: 'InkNames',
    334: 'NumberOfInks',
    336: 'DotRange',
    337: 'TargetPrinter',
    338: 'ExtraSamples',
    339: 'SampleFormat',
    340: 'SMinSampleValue',
    341: 'SMaxSampleValue',
    342: 'TransferRange',
    343: 'ClipPath',
    344: 'XClipPathUnits',
    345: 'YClipPathUnits',
    346: 'Indexed',
    347: 'JPEGTables',
    351: 'OPIProxy',
    512: 'JPEGProc',
    513: 'JPEGInterchangeFormat',
    514: 'JPEGInterchangeFormatLength',
    515: 'JPEGRestartInterval',
    517: 'JPEGLosslessPredictors',
    518: 'JPEGPointTransforms',
    519: 'JPEGQTables',
    520: 'JPEGDCTables',
    521: 'JPEGACTables',
    529: 'YCbCrCoefficients',
    530: 'YCbCrSubSampling',
    531: 'YCbCrPositioning',
    532: 'ReferenceBlackWhite',
    700: 'XMLPacket',
    18246: 'Rating',
    18249: 'RatingPercent',
    32781: 'ImageID',
    32953: 'RefPts',
    32954: 'RegionTackPoint',
    32955: 'RegionWarpCorners',
    32956: 'RegionAffine',
    32995: 'Matteing',
    32996: 'Datatype',
    32997: 'ImageDepth',
    32998: 'TileDepth',
    33421: 'CFARepeatPatternDim',
    33422: 'CFAPattern',
    33423: 'BatteryLevel',
    33432: 'Copyright',
    33434: 'ExposureTime',
    33437: 'FNumber',
    33550: 'ModelPixelScale',
    33723: 'IPTCNAA',
    33918: 'INGRPacketData',
    33922: 'ModelTiePoint',
    34264: 'ModelTransformation',
    34377: 'ImageResources',
    34665: 'ExifTag',
    34675: 'InterColorProfile',
    34735: 'GeoKeyDirectory',
    34736: 'GeoDoubleParams',
    34737: 'GeoAsciiParams',
    34850: 'ExposureProgram',
    34852: 'SpectralSensitivity',
    34853: 'GPSTag',
    34855: 'ISOSpeedRatings',
    34856: 'OECF',
    34857: 'Interlace',
    34858: 'TimeZoneOffset',
    34859: 'SelfTimerMode',
    36864: 'ExifVersion',
    36867: 'DateTimeOriginal',
    36868: 'DateTimeDigitized',
    37122: 'CompressedBitsPerPixel',
    37377: 'ShutterSpeedValue',
    37378: 'ApertureValue',
    37379: 'BrightnessValue',
    37380: 'ExposureBiasValue',
    37381: 'MaxApertureValue',
    37382: 'SubjectDistance',
    37383: 'MeteringMode',
    37384: 'LightSource',
    37385: 'Flash',
    37386: 'FocalLength',
    37387: 'FlashEnergy',
    37388: 'SpatialFrequencyResponse',
    37389: 'Noise',
    37390: 'FocalPlaneXResolution',
    37391: 'FocalPlaneYResolution',
    37392: 'FocalPlaneResolutionUnit',
    37393: 'ImageNumber',
    37394: 'SecurityClassification',
    37395: 'ImageHistory',
    37396: 'SubjectLocation',
    37397: 'ExposureIndex',
    37398: 'TIFFEPStandardID',
    37399: 'SensingMethod',
    37439: 'StoNits',
    37500: 'MakerNote',
    37510: 'UserComment',
    37724: 'ImageSourceData',
    40091: 'XPTitle',
    40092: 'XPComment',
    40093: 'XPAuthor',
    40094: 'XPKeywords',
    40095: 'XPSubject',
    40960: 'FlashpixVersion',
    40961: 'ColorSpace',
    41486: 'FocalPlaneXResolution',
    41487: 'FocalPlaneYResolution',
    41488: 'FocalPlaneResolutionUnit',
    41495: 'SensingMethod',
    41728: 'FileSource',
    41729: 'SceneType',
    41985: 'CustomRendered',
    41986: 'ExposureMode',
    41987: 'WhiteBalance',
    41988: 'DigitalZoomRatio',
    41990: 'SceneCaptureType',
    41991: 'GainControl',
    41992: 'Contrast',
    41993: 'Saturation',
    41994: 'Sharpness',
    42112: 'GDALMetadata',
    50341: 'PrintImageMatching',
    50706: 'DNGVersion',
    50707: 'DNGBackwardVersion',
    50708: 'UniqueCameraModel',
    50709: 'LocalizedCameraModel',
    50710: 'CFAPlaneColor',
    50711: 'CFALayout',
    50712: 'LinearizationTable',
    50713: 'BlackLevelRepeatDim',
    50714: 'BlackLevel',
    50715: 'BlackLevelDeltaH',
    50716: 'BlackLevelDeltaV',
    50717: 'WhiteLevel',
    50718: 'DefaultScale',
    50719: 'DefaultCropOrigin',
    50720: 'DefaultCropSize',
    50721: 'ColorMatrix1',
    50722: 'ColorMatrix2',
    50723: 'CameraCalibration1',
    50724: 'CameraCalibration2',
    50725: 'ReductionMatrix1',
    50726: 'ReductionMatrix2',
    50727: 'AnalogBalance',
    50728: 'AsShotNeutral',
    50729: 'AsShotWhiteXY',
    50730: 'BaselineExposure',
    50731: 'BaselineNoise',
    50732: 'BaselineSharpness',
    50733: 'BayerGreenSplit',
    50734: 'LinearResponseLimit',
    50735: 'CameraSerialNumber',
    50736: 'LensInfo',
    50737: 'ChromaBlurRadius',
    50738: 'AntiAliasStrength',
    50739: 'ShadowScale',
    50740: 'DNGPrivateData',
    50741: 'MakerNoteSafety',
    50778: 'CalibrationIlluminant1',
    50779: 'CalibrationIlluminant2',
    50780: 'BestQualityScale',
    50781: 'RawDataUniqueID',
    50827: 'OriginalRawFileName',
    50828: 'OriginalRawFileData',
    50829: 'ActiveArea',
    50830: 'MaskedAreas',
    50831: 'AsShotICCProfile',
    50832: 'AsShotPreProfileMatrix',
    50833: 'CurrentICCProfile',
    50834: 'CurrentPreProfileMatrix',
    50879: 'ColorimetricReference',
    50931: 'CameraCalibrationSignature',
    50932: 'ProfileCalibrationSignature',
    50934: 'AsShotProfileName',
    50935: 'NoiseReductionApplied',
    50936: 'ProfileName',
    50937: 'ProfileHueSatMapDims',
    50938: 'ProfileHueSatMapData1',
    50939: 'ProfileHueSatMapData2',
    50940: 'ProfileToneCurve',
    50941: 'ProfileEmbedPolicy',
    50942: 'ProfileCopyright',
    50964: 'ForwardMatrix1',
    50965: 'ForwardMatrix2',
    50966: 'PreviewApplicationName',
    50967: 'PreviewApplicationVersion',
    50968: 'PreviewSettingsName',
    50969: 'PreviewSettingsDigest',
    50970: 'PreviewColorSpace',
    50971: 'PreviewDateTime',
    50972: 'RawImageDigest',
    50973: 'OriginalRawFileDigest',
    50974: 'SubTileBlockSize',
    50975: 'RowInterleaveFactor',
    50981: 'ProfileLookTableDims',
    50982: 'ProfileLookTableData',
    51008: 'OpcodeList1',
    51009: 'OpcodeList2',
    51022: 'OpcodeList3',
    51041: 'NoiseProfile'
}

# Map TIFF datatype to number of bytes.  Consult tiff.h
_PAYLOAD_SIZE = {
    TIFF_BYTE: 1,
    TIFF_ASCII: 1,
    TIFF_SHORT: 2,
    TIFF_LONG: 4,
    TIFF_RATIONAL: 8,
    TIFF_SBYTE: 1,
    TIFF_UNDEFINED: 1,
    TIFF_SSHORT: 2,
    TIFF_SLONG: 4,
    TIFF_SRATIONAL: 8,
    TIFF_FLOAT: 4,
    TIFF_DOUBLE: 8,
    TIFF_IFD: 4,
    TIFF_LONG8: 8,
    TIFF_SLONG8: 8,
    TIFF_IFD8: 8
}

# Map TIFF datatype to struct module format specifier
_DTYPE_SPECIFIER = {
    TIFF_BYTE: 'B',
    TIFF_SHORT: 'H',
    TIFF_LONG: 'I',
    TIFF_RATIONAL: 'II',
    TIFF_SBYTE: 'b',
    TIFF_UNDEFINED: 'B',
    TIFF_SSHORT: 'h',
    TIFF_SLONG: 'i',
    TIFF_SRATIONAL: 'ii',
    TIFF_FLOAT: 'f',
    TIFF_DOUBLE: 'd',
    TIFF_IFD: 'I',
    TIFF_LONG8: 'Q',
    TIFF_SLONG8: 'q',
    TIFF_IFD8: 'Q'
}


class Tiff(object):
    """
    Attributes
    ----------
    endian : str
        Either '<' for little endian or '>' for big endian
    classic : bool
        If True, the file is classic TIFF.  If false, it is BigTIFF.
    ifd_offset : list
        List of byte offsets to IFDs
    ifd : list
        List of IFDs
    tag_entry_num_bytes : int
        4 for classic TIFF, 8 for BigTIFF
    """
    def __init__(self, filename=None, buffer=None):
        self.filename = filename
        self.buffer = buffer

        if self.filename is not None:
            self.fptr = open(self.filename, 'rb')
            self._tptr = _tiflib.open(self.filename)
        else:
            self.fptr = BytesIO(buffer)
            self._tptr = None

        self.ifd_offset = []
        self.ifd = []

        self.parse_header()

        for ifd_offset in self.ifd_offset:
            new_ifd = self.process_ifd(ifd_offset)
            self.ifd.append(new_ifd)

    def __iter__(self):
        self._st_count = -1
        return self

    def __next__(self):
        self._st_count += 1
        if self._st_count >= self._num_strips_tiles:
            raise StopIteration()
        if _tiflib.isTiled(self._tptr):
            data = _tiflib.readEncodedTile(self._tptr, self._st_count)
        else:
            data = _tiflib.readEncodedStrip(self._tptr, self._st_count)
        return data

    def process_ifd(self, offset):
        """
        Process the IFD found at the given byte offset

        Parameters
        ----------
        offset : int
            byte offset from beginning of file

        Returns
        -------
        dict
            IFD (and any subIFDs) at the specified byte offset
        """
        ifd = OrderedDict()

        self.fptr.seek(offset)
        if self.classic:
            buffer = self.fptr.read(2)
            num_tags, = struct.unpack(self.endian + 'H', buffer)
        else:
            buffer = self.fptr.read(8)
            num_tags, = struct.unpack(self.endian + 'Q', buffer)

        buffer = self.fptr.read(num_tags * self.tag_length)

        for j in range(num_tags):
            slc = slice(j * self.tag_length, (j + 1) * self.tag_length)
            tag_number, tag_data = self.process_tag(buffer[slc])
            try:
                key = _EXIFIMAGE[tag_number]
            except KeyError:
                msg = 'Unrecognized TIFF tag:  {tag}'
                warnings.warn(msg.format(tag=tag_number))
                key = str(tag_number)

            if key == 'ExifTag':
                tag_data = self.process_ifd(tag_data)

            ifd[key] = tag_data

        return ifd

    def process_tag(self, buffer):
        """
        Parameters
        ----------
        buffer : byte array
            IFD entry with tag, datatype, number of values, and tag data or
            offset to the tag data
        """
        fmt = 'HHII' if self.classic else 'HHQQ'
        fmt = self.endian + fmt
        tag_num, dtype, nelts, offset = struct.unpack(fmt, buffer)

        if dtype not in _PAYLOAD_SIZE.keys():
            msg = "Invalid tag datatype ({dtype}).".format(dtype=dtype)
            warnings.warn(msg)
            return tag_num, None

        num_bytes = _PAYLOAD_SIZE[dtype] * nelts
        if num_bytes > self.tag_payload_num_bytes:
            # Must seek to the data to actually read it.
            old_position = self.fptr.tell()
            self.fptr.seek(offset)
            tag_data_buffer = self.fptr.read(num_bytes)
            self.fptr.seek(old_position)
        else:
            if self.classic:
                tag_data_buffer = buffer[8:8 + num_bytes]
            else:
                tag_data_buffer = buffer[12:12 + num_bytes]

        if dtype == TIFF_ASCII:
            if sys.hexversion > 0x03000000:
                data = tag_data_buffer.decode('utf-8')
            else:
                data = tag_data_buffer
            data = data.rstrip('\x00')
        else:
            fmt = self.endian + _DTYPE_SPECIFIER[dtype] * nelts
            data = struct.unpack(fmt, tag_data_buffer)

        if dtype in [TIFF_BYTE, TIFF_SHORT, TIFF_LONG, TIFF_SBYTE,
                     TIFF_UNDEFINED, TIFF_SSHORT, TIFF_SLONG, TIFF_FLOAT,
                     TIFF_DOUBLE]:
            if nelts == 1:
                # unpack returns a tuple and there is just one item
                data = data[0]

        return tag_num, data

    def parse_header(self):
        """
        Interpret the TIFF header
        """
        buffer = self.fptr.read(4)

        data = struct.unpack('<BB', buffer[0:2])
        if data[0] == 73 and data[1] == 73:
            # little endian
            self.endian = '<'
        elif data[0] == 77 and data[1] == 77:
            # big endian
            self.endian = '>'
        else:
            msg = "The byte order indication in the TIFF header ({0}) is "
            msg += "invalid.  It should be either {1} or {2}."
            msg = msg.format(buffer[6:8], bytes([73, 73]), bytes([77, 77]))
            raise IOError(msg)

        # Interpret the version number.
        version, = struct.unpack(self.endian + 'H', buffer[2:4])
        self.classic = version == 42
        if self.classic:
            # 12 bytes for classic TIFF tag length
            self.tag_length = 12
            # 4 bytes for the classic TIFF data/offset field
            self.tag_payload_num_bytes = 4
        else:
            # 20 bytes for BigTIFF tag length
            self.tag_length = 20
            # 8 bytes for the BigTIFF data/offset field
            self.tag_payload_num_bytes = 8

        if self.classic:
            buffer = self.fptr.read(4)
            offset, = struct.unpack(self.endian + 'I', buffer)
        else:
            buffer = self.fptr.read(12)
            offset, = struct.unpack(self.endian + 'Q', buffer[4:])
        self.ifd_offset.append(offset)

    def __del__(self):
        if self.fptr is not None:
            self.fptr.close()
        if self._tptr is not None:
            _tiflib.close(self._tptr)

    def __str__(self):
        msg = "TIFF:  {filename}\n"
        msg += "Version:  {version}\n"
        msg += "IFD:  {ifd}\n"

        msg = msg.format(filename=self.filename,
                         version=('Classic' if self.classic else 'BigTIFF'),
                         ifd=self.ifd[0])
        return(msg)

    def __getitem__(self, pargs):

        if isinstance(pargs, int):
            raise RuntimeError("Must supply image coordinates.")

        if pargs is Ellipsis:
            # [...]
            return self._imread()

        if isinstance(pargs, slice) and ((pargs.start is None) and
                                         (pargs.stop is None) and
                                         (pargs.step is None)):
            # [:]
            return self._imread()

    def _imread(self):
        """
        Read TIFF image

        Return
        ----------
        image : ndarray
            image data from file
        """
        ok, emsg = _tiflib.RGBAImageOK(self._tptr)
        photometric = self.ifd[0]['PhotometricInterpretation']
        if photometric == PHOTOMETRIC_YCBCR:
            image = _tiflib.readRGBAImage(self._tptr)
            image = image[:, :, 0:3]
        else:
            dtype = _tiflib._numpy_datatype(self._tptr)

            height = self.ifd[0]['ImageLength']
            width = self.ifd[0]['ImageWidth']
            spp = self.ifd[0]['SamplesPerPixel']
            if spp == 1:
                image = np.zeros((height, width), dtype=dtype)
            else:
                image = np.zeros((height, width, spp), dtype=dtype)

            if _tiflib.isTiled(self._tptr):
                t_height = _tiflib.getField(self._tptr, _tiflib.TILELENGTH)
                t_width = _tiflib.getField(self._tptr, _tiflib.TILEWIDTH)
                num_tile_rows = int(np.ceil(height / t_height))
                num_tile_cols = int(np.ceil(width / t_width))
                tile_num = -1
                for tr in range(num_tile_rows):
                    for tc in range(num_tile_cols):
                        tile_num += 1
                        tile = _tiflib.readEncodedTile(self._tptr, tile_num)

                        if tr == num_tile_rows - 1:
                            # Tiles along the last row may need to be clamped.
                            idx = slice(0, height - t_height * tr)
                            tile = tile[idx, :]

                        if tc == num_tile_cols - 1:
                            # Tiles along the right hand side may need to be
                            # clamped.
                            idx = slice(0, width - t_width * tc)
                            tile = tile[:, idx]

                        ridx = slice(tr * t_height,
                                     min((tr + 1) * t_height, height))
                        cidx = slice(tc * t_width,
                                     min((tc + 1) * t_width, width))

                        image[ridx, cidx] = tile

            else:
                strip_height = _tiflib.getField(self._tptr,
                                                _tiflib.ROWSPERSTRIP)
                num_strips = int(np.ceil(height / strip_height))
                for stripnum in range(num_strips):
                    strip = _tiflib.readEncodedStrip(self._tptr, stripnum)
                    if stripnum == num_strips - 1:
                        ridx = slice(stripnum * strip_height, height)
                        strip = strip[0:(height - stripnum * strip_height), :]
                    else:
                        ridx = slice(stripnum * strip_height,
                                     (stripnum + 1) * strip_height)
                    image[ridx, :] = strip

        return image


def _write_degenerate_geotiff(tiff):
    '''
    Write degenerate GEOTIFF to place into JPEG2000 file

    Parameters
    ----------
    tiff : Tiff
        Object corresponding to true GEOTIFF file, first IFD.

    Reference
    ---------
    http://www.lizardtech.com/download/geo/geotiff_box.txt
    '''

    ifd = tiff.ifd[0]

    GEOTIFF_TAGS = [('ModelPixelScale', 33550, TIFF_DOUBLE),
                    ('ModelTiePoint', 33922, TIFF_DOUBLE),
                    ('ModelTransformation', 34264, TIFF_DOUBLE),
                    ('GeoKeyDirectory', 34735, TIFF_SHORT),
                    ('GeoDoubleParams', 34736, TIFF_DOUBLE),
                    ('GeoAsciiParams', 34737, TIFF_ASCII)]

    # We always write ImageWidth and ImageHeight
    # Must also have datatype as 8-bit
    # the colorspace must be greyscale
    # there must be a single pixel with a value of zero
    # implies rowspersample, samplesperpixel, stripbytecounts, stripbyteoffsets
    tags_to_write = [(key, tnum, ttype) for (key, tnum, ttype) in GEOTIFF_TAGS
                     if key in ifd.keys()]

    # How many bytes?
    # 8 bytes for the header
    # 2 bytes for the number of entries in the IFD
    # n*12 bytes for the IFD
    # 2 bytes for the offset for the next IFD (doesn't exist)
    # Remember that ImageLength and ImageHeight are always written.
    ifd_proper_num_bytes = 8 + 2 + (len(tags_to_write) + 8) * 12 + 2

    # make the buffer big enough for the TIFF header plus an IFD with all
    # the geotiff tags plus imagewidth and imageheight
    buffer = bytearray(b'0x0' * ifd_proper_num_bytes)

    # keep a second buffer to hold the overflow from tags whose values
    # cannot fit into 4 bytes
    after_buffer = BytesIO()

    # Write the TIFF header
    # Make it little-endian (73-73 ==> 'II'), classic tiff format (42),
    # and the offset to the IFD is the usual 8 bytes.
    struct.pack_into('<BBHI', buffer, 0, 73, 73, 42, 8)

    # Write the number of tags in the IFD.
    struct.pack_into('<H', buffer, 8, len(tags_to_write) + 8)

    # Write the degenerate image width and height
    struct.pack_into('<HHII', buffer, 10,
                     TIFFTAG_IMAGEWIDTH, TIFF_LONG, 1, 1)
    struct.pack_into('<HHII', buffer, 22,
                     TIFFTAG_IMAGELENGTH, TIFF_LONG, 1, 1)
    struct.pack_into('<HHIHH', buffer, 34,
                     TIFFTAG_BITSPERSAMPLE, TIFF_SHORT, 1, 1, 0)
    struct.pack_into('<HHIHH', buffer, 46,
                     TIFFTAG_PHOTOMETRIC, TIFF_SHORT, 1, 1, 0)
    # This must point to the single pixel, which will follow the IFD.
    struct.pack_into('<HHII', buffer, 58,
                     TIFFTAG_STRIPBYTEOFFSETS, TIFF_LONG, 1,
                     ifd_proper_num_bytes)
    struct.pack_into('<HHIHH', buffer, 70,
                     TIFFTAG_SAMPLESPERPIXEL, TIFF_SHORT, 1, 1, 0)
    struct.pack_into('<HHII', buffer, 82,
                     TIFFTAG_ROWSPERSTRIP, TIFF_LONG, 1, 1)
    struct.pack_into('<HHII', buffer, 94,
                     TIFFTAG_STRIPBYTECOUNTS, TIFF_LONG, 1, 1)

    # Write the single pixel as the first value following the IFD.
    abuffer = struct.pack('<B', 0)
    after_buffer.write(abuffer)

    # Write the geotiff-specific tags
    # This offset is where we write the tag into the IFD
    ifd_offset = 106

    # This offset is where we write the tag data that cannot fit into the IFD.
    # Guess what, it will never fit, which makes it easy.  The offset of that
    # first tag datum will follow the single zero pixel.
    after_offset = ifd_proper_num_bytes + 1
    for key, tag_number, tiff_dtype in tags_to_write:
        struct.pack_into('<HHII', buffer, ifd_offset,
                         tag_number, tiff_dtype, len(ifd[key]), after_offset)

        nelts = len(ifd[key])
        if tiff_dtype == TIFF_DOUBLE:
            payload = tuple(x for x in ifd[key])
            abuffer = struct.pack('<' + 'd' * nelts, *payload)
        elif tiff_dtype == TIFF_SHORT:
            payload = tuple(x for x in ifd[key])
            abuffer = struct.pack('<' + 'H' * nelts, *payload)
        else:
            payload = tuple(ord(x) for x in ifd[key])
            abuffer = struct.pack('<' + 'B' * nelts, *payload)

        after_buffer.write(abuffer)

        # The IFD entries are always 12 bytes, so that's the increment.
        ifd_offset += 12

        # The "after" buffer increment depends on what was written.
        after_offset += len(abuffer)

    # Add the offset to the next IFD.  There is no next IFD, but we still need
    # the offset.
    struct.pack_into('<H', buffer, ifd_offset, 0)

    after_buffer.seek(0)
    x = bytes(buffer[:ifd_proper_num_bytes]) + after_buffer.read()
    x = BytesIO(x)
    return x
