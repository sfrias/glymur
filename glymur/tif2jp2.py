import datetime
from uuid import UUID
import warnings

try:
    from libxmp import XMPMeta
    from libxmp.consts import XMP_NS_DC as NS_DC
    from libxmp.consts import XMP_NS_EXIF as NS_EXIF
    from libxmp.consts import XMP_NS_TIFF as NS_TIFF
    from libxmp.consts import XMP_NS_XMP as NS_XMP
    _NO_PYTHON_XMP_TOOLKIT = False
except ImportError:
    _NO_PYTHON_XMP_TOOLKIT = True

import numpy as np

from .jp2k import Jp2k
from .jp2box import UUIDBox
from .tiffreader import Tiff, PHOTOMETRIC_SEPARATED, _write_degenerate_geotiff
from .core import LRCP


def tif2jp2(tifffile, jp2file, tilesize=None, prog='LRCP', num_res=None):
    """
    Convert TIFF to JPEG2000

    Parameters
    ----------
    tifffile, jp2file : str
        Paths to input TIFF, output JPEG2000 files
    numres : int
        number of resolutions
    prog : str
        one of "LRCP" "RLCP", "RPCL", "PCRL", "CPRL"
    tilesize : tuple
        tile size in terms of (numrows, numcols), not (X, Y)
    """
    tiff = Tiff(tifffile)

    if tiff.ifd[0]['PhotometricInterpretation'] == PHOTOMETRIC_SEPARATED:
        msg = ("{filename} has a photometric interpretation of SEPARATED, but "
               "JPEG2000 Part 1 core coding system allows only grayscale or "
               "RGB.")
        raise RuntimeError(msg.format(filename=tiff.filename))

    data = tiff[:]

    smallest_side = np.min(data.shape[0:2])
    max_num_res = int(np.log2(smallest_side))
    if max_num_res < num_res:
        msg = "Resetting number of resolutions to {num_res}."
        msg = msg.format(num_res=max_num_res)
        warnings.warn(msg)
        num_res = max_num_res

    if 'InterColorProfile' in tiff.ifd[0].keys():
        msg = 'ICC profile not transfered to {filename}.'
        msg = msg.format(filename=jp2file)
        warnings.warn(msg)

    jp2 = Jp2k(jp2file, data, numres=num_res, prog=prog, tilesize=tilesize)

    # append TIFF metadata as XMP UUID box
    if _NO_PYTHON_XMP_TOOLKIT:
        msg = "The python-xmp-toolkit is not installed.  The TIFF metadata "
        msg += "will not be transferred."
        warnings.warn(msg)
    else:
        xmp = XMPMeta()
        _process_ifd(tiff.ifd[0], xmp)

    xmp_uuid = UUID('be7acfcb-97a9-42e8-9c71-999491e3afac')
    box = UUIDBox(xmp_uuid, str(xmp).encode())
    jp2.append(box)

    # If geotiff, append that metadata as GeoJP2 UUID box
    if 'GeoAsciiParams' in tiff.ifd[0].keys():

        bytes_obj = _write_degenerate_geotiff(tiff)
        with open('/Users/jevans/b.tif', 'wb') as f:
            f.write(bytes_obj.read())
            bytes_obj.seek(0)
        geojp2_uuid = UUID('b14bf8bd-083d-4b43-a5ae-8cd7d5a6ce03')
        box = UUIDBox(geojp2_uuid, bytes_obj.read())
        jp2.append(box)

    return jp2


def _process_ifd(ifd, xmp):

    for key, value in ifd.items():

        if key == 'Artist':
            xmp.set_property(NS_DC, 'creator', value)
        elif key == 'Copyright':
            xmp.set_property(NS_DC, 'rights', value)

        elif key == 'DateTime':
            # Must be combined with Exif tag SubSecTimeDigitized if it exists
            # and stored in ISO 8601 format.
            modify_date = datetime.datetime.strptime(value.rstrip('\x00'),
                                                     '%Y:%m:%d %H:%M:%S')
            if ((('ExifTag' in ifd.keys()) and
                 ('SubSecTime' in ifd['ExifTag'].keys()))):
                raise RuntimeError('blah')
            else:
                dt = datetime.timedelta()
            modify_date += dt
            xmp.set_property(NS_XMP, 'ModifyDate', modify_date.isoformat())

        elif key == 'DateTimeDigitized':
            # Must be combined with SubSecTimeDigitized if it exists and stored
            # in ISO 8601 format.
            modify_date = datetime.datetime.strptime(value.rstrip('\x00'),
                                                     '%Y:%m:%d %H:%M:%S')
            if 'SubSecTimeDigitized' in ifd.keys():
                raise RuntimeError('blah')
            else:
                dt = datetime.timedelta()
            modify_date += dt
            xmp.set_property(NS_XMP, 'CreateDate', modify_date.isoformat())

        elif key == 'DateTimeOriginal':
            # Must be combined with SubSecTimeOriginal if it exists and stored
            # in ISO 8601 format.
            modify_date = datetime.datetime.strptime(value.rstrip('\x00'),
                                                     '%Y:%m:%d %H:%M:%S')
            if 'SubSecTimeOriginal' in ifd.keys():
                raise RuntimeError('blah')
            else:
                dt = datetime.timedelta()
            modify_date += dt
            xmp.set_property(NS_EXIF, key, modify_date.isoformat())

        elif key == 'ISOSpeedRatings':
            if isinstance(value, int):
                value = [value]
            opts = {'prop_value_is_array': True, 'prop_value_is_ordered': True}
            xmp.append_array_item(NS_EXIF, 'ISOSpeedRatings', str(value[0]),
                                  array_options=opts)
            for item in value[1:]:
                xmp.append_array_item(NS_TIFF, 'ISoSpeedRatings', str(item))

        elif key in ['ExifVersion', 'FlashpixVersion']:
            version_string = ''.join([chr(x) for x in value])
            xmp.set_property(NS_EXIF, key, version_string)

        elif key in ['ApertureValue', 'BrightnessValue', 'ExposureBiasValue',
                     'FocalLength', 'FNumber', 'MaxApertureValue',
                     'ShutterSpeedValue']:
            # Exif tags that map immediately as rationals
            xmp.set_property(NS_EXIF, key, str(value[0]) + '/' + str(value[1]))

        elif key in ['ColorSpace', 'ExposureProgram', 'FileSource',
                     'FocalPlaneResolutionUnit',
                     'MeteringMode', 'SceneType', 'SensingMethod']:
            # Exif tags that immediately map
            xmp.set_property(NS_EXIF, key, str(value))

        elif key in ['ImageWidth', 'ImageLength', 'Make', 'Model',
                     'Orientation', 'PhotometricInterpretation',
                     'ResolutionUnit', 'SamplesPerPixel', 'YCbCrPositioning']:
            xmp.set_property(NS_TIFF, key, str(value))

        elif key in ['XResolution', 'YResolution']:

            xval = str(value[0]) + '/' + str(value[1])
            xmp.set_property(NS_TIFF, key, xval)

        elif key in ['Flash']:

            prefix = xmp.get_prefix_for_namespace(NS_EXIF)

            name = prefix + 'Flash/' + prefix + 'Fired'
            struct_value = (value & 0x01) == 1
            xmp.set_property_bool(NS_EXIF, name, struct_value)

            name = prefix + 'Flash/' + prefix + 'Function'
            struct_value = (value & 0x10) == 1
            xmp.set_property_bool(NS_EXIF, name, struct_value)

            name = prefix + 'Flash/' + prefix + 'Mode'
            struct_value = value >> 3
            xmp.set_property_int(NS_EXIF, name, struct_value)

            name = prefix + 'Flash/' + prefix + 'RedEyeMode'
            struct_value = (value & 0x40) == 1
            xmp.set_property_bool(NS_EXIF, name, struct_value)

            name = prefix + 'Flash/' + prefix + 'Return'
            struct_value = value >> 1
            xmp.set_property_int(NS_EXIF, name, struct_value)

        elif key in ['FocalPlaneXResolution', 'FocalPlaneYResolution']:

            xval = str(value[0]) + '/' + str(value[1])
            xmp.set_property(NS_EXIF, key, xval)

        elif key in ['ReferenceBlackWhite']:

            # ordered array of rationals
            opts = {'prop_value_is_array': True, 'prop_array_is_ordered': True}

            xval = str(value[0]) + '/' + str(value[1])
            xmp.append_array_item(NS_TIFF, key, xval, array_options=opts)

            for j in range(2, len(value), 2):
                xval = str(value[j]) + '/' + str(value[j + 1])
                xmp.append_array_item(NS_TIFF, key, xval)

        elif key in ['BitsPerSample', 'YCbCrSubSampling']:

            opts = {'prop_value_is_array': True, 'prop_array_is_ordered': True}

            if isinstance(value, int):
                xmp.append_array_item(NS_TIFF, key, str(value),
                                      array_options=opts)
            else:
                xmp.append_array_item(NS_TIFF, key, str(value[0]),
                                      array_options=opts)
                for item in value[1:]:
                    xmp.append_array_item(NS_TIFF, key, str(item))

        elif key in ['Software']:
            xmp.set_property(NS_XMP, 'CreatorTool', str(value))
        elif key in ['InterColorProfile']:
            pass
        elif key == 'ExifTag':
            _process_ifd(ifd[key], xmp)
        else:
            pass
