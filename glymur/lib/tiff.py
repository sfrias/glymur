import ctypes

import numpy as np

from glymur.config import CONFIG

TIFF = CONFIG['tiff']

# Map libtiff types to ctypes types.
tdata_t = ctypes.c_void_p
tdir_t = ctypes.c_uint16
toff_t = ctypes.c_uint32
tsample_t = ctypes.c_uint16
tsize_t = ctypes.c_int32
ttag_t = ctypes.c_uint32
tstrip_t = ctypes.c_uint32
ttile_t = ctypes.c_uint32

PHOTOMETRIC_MINISWHITE = 0
PHOTOMETRIC_MINISBLAC = 1
PHOTOMETRIC_RGB = 2
PHOTOMETRIC_PALETTE = 3
PHOTOMETRIC_MASK = 4
PHOTOMETRIC_SEPARATED = 5
PHOTOMETRIC_YCBCR = 6
PHOTOMETRIC_CIELAB = 8
PHOTOMETRIC_ICCLAB = 9
PHOTOMETRIC_ITULAB = 10
PHOTOMETRIC_LOGL = 32844
PHOTOMETRIC_LOGLUV = 32845

PLANARCONFIG_CONTIG = 1
PLANARCONFIG_SEPARATE = 2

SAMPLEFORMAT_UINT = 1
SAMPLEFORMAT_INT = 2
SAMPLEFORMAT_IEEEFP = 3
SAMPLEFORMAT_VOID = 4
SAMPLEFORMAT_COMPLEXINT = 5
SAMPLEFORMAT_COMPLEXIEEEFP = 6


def _readEncodedDatatype(bps, fmt):
    """Computes datatype of output image.

    Parameters
    ----------
    bps : int
        bits per sample
    fmt : int
        sample format

    Returns
    -------
    numpy.dtype
        numpy datatype for image data to be returned by either readEncodedTile
        or readEncodedStrip.
    """
    if bps == 8:
        if fmt == SAMPLEFORMAT_INT:
            dtype = np.int8
        else:
            dtype = np.uint8
    elif bps == 16:
        if fmt == SAMPLEFORMAT_INT:
            dtype = np.int16
        else:
            dtype = np.uint16
    elif bps == 32:
        if fmt == SAMPLEFORMAT_IEEEFP:
            dtype = np.float32
        elif fmt == SAMPLEFORMAT_INT:
            dtype = np.int32
        else:
            dtype = np.uint32
    elif bps == 64:
        if fmt == SAMPLEFORMAT_IEEEFP:
            dtype = np.float64
        elif fmt == SAMPLEFORMAT_INT:
            dtype = np.int64
        else:
            dtype = np.uint64
    else:
        msg = "Unsupported BitsPerSample ({bps}) value.".format(bps=bps)
        raise RuntimeError(msg)
    return dtype


def _get_field_char(tif, tag):
    """Single string value, i.e. IMAGEDESCRIPTION"""
    val = ctypes.c_char_p()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_char_p))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    return status, val.value.decode('utf-8')


def _get_field_inknames(tif, tag):
    """INKNAMES special case"""
    status, raw_ink_names = _get_field_char(tif, tag)
    ink_names = raw_ink_names.split(chr(0))
    return ink_names


def _get_field_double(tif, tag):
    """double value, i.e. SMINSAMPLEVALUE"""
    val = ctypes.c_double()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_double))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    return status, val.value


def _get_field_float(tif, tag):
    """double value, i.e. XRESOLUTION"""
    val = ctypes.c_float()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_float))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    return status, val.value


def _get_field_floatp2(tif, tag):
    """2-element floating point field, i.e. WHITEPOINT"""
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    ptype = ctypes.POINTER(ctypes.c_float * 2)
    argtypes.append(ctypes.POINTER(ptype))
    TIFF.TIFFGetField.argtypes = argtypes
    val = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    data = np.zeros(2)
    data[0] = val.contents[0]
    data[1] = val.contents[1]
    return status, data


def _get_field_floatp3(tif, tag):
    """3-element floating point field, i.e. YCBCRCOEFFICIENTS"""
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    ptype = ctypes.POINTER(ctypes.c_float * 3)
    argtypes.append(ctypes.POINTER(ptype))
    TIFF.TIFFGetField.argtypes = argtypes
    val = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    data = np.zeros(3)
    data[0] = val.contents[0]
    data[1] = val.contents[1]
    data[2] = val.contents[2]
    return status, data


def _get_field_floatp6(tif, tag):
    """6-element floating point field"""
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    ptype = ctypes.POINTER(ctypes.c_float * 6)
    argtypes.append(ctypes.POINTER(ptype))
    TIFF.TIFFGetField.argtypes = argtypes
    val = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    data = np.zeros(6)
    data[0] = val.contents[0]
    data[1] = val.contents[1]
    data[2] = val.contents[2]
    data[3] = val.contents[3]
    data[4] = val.contents[4]
    data[5] = val.contents[5]
    return status, data


def _get_field_uint16(tif, tag):
    """Single uint16 value, i.e. BITSPERSAMPLE"""
    ptype = ctypes.c_uint16
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.POINTER(ptype)]
    TIFF.TIFFGetFieldDefaulted.restype = ctypes.c_int32
    TIFF.TIFFGetFieldDefaulted.argtypes = argtypes
    val = ctypes.c_uint16()
    status = TIFF.TIFFGetFieldDefaulted(tif, tag, ctypes.byref(val))
    return status, val.value


def _get_field_2uint16(tif, tag):
    """Single uint16 value, i.e. DOTRANGE"""
    val1 = ctypes.c_uint16()
    val2 = ctypes.c_uint16()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_uint16))
    argtypes.append(ctypes.POINTER(ctypes.c_uint16))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val1),
                                   ctypes.byref(val2))
    return status, (val1.value, val2.value)


def _get_field_uint16_uint16p(tif, tag):
    """Retrieve uint16, uint16 array, i.e. EXTRASAMPLES"""

    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.POINTER(ctypes.c_uint16),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_uint16))]
    TIFF.TIFFGetField.argtypes = argtypes

    val1 = ctypes.c_uint16()
    ptype = ctypes.POINTER(ctypes.c_uint16)
    val2 = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val1),
                                   ctypes.byref(val2))

    nelts = val1.value * 2
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(val2.contents), nelts)
    vals = np.frombuffer(x, np.dtype(np.uint16)).copy()
    return status, vals


def _get_field_uint16_count_uint32_offsets(tif, tag):
    """Retrieve uint16 count, uint32 array, i.e. SUBIFD"""

    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.POINTER(ctypes.c_uint16),
                ctypes.POINTER(ctypes.POINTER(ctypes.c_uint32))]
    TIFF.TIFFGetField.argtypes = argtypes

    val1 = ctypes.c_uint16()
    ptype = ctypes.POINTER(ctypes.c_uint32)
    val2 = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val1),
                                   ctypes.byref(val2))

    nelts = val1.value * 4
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(val2.contents), nelts)
    vals = np.frombuffer(x, np.dtype(np.uint32)).copy()
    return status, vals


def _get_field_3uint16p(tif, tag):
    """Three uint16 arrays, i.e. COLORMAP"""
    bps = getField(tif, BITSPERSAMPLE)
    nelts = 1 << bps

    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    ptype = ctypes.POINTER(ctypes.c_uint16 * nelts)
    argtypes.append(ctypes.POINTER(ptype))
    argtypes.append(ctypes.POINTER(ptype))
    argtypes.append(ctypes.POINTER(ptype))
    TIFF.TIFFGetField.argtypes = argtypes

    pred = ptype()
    pgreen = ptype()
    pblue = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(pred),
                                   ctypes.byref(pgreen), ctypes.byref(pblue))
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(pred.contents),
                                        nelts * 2)
    red = np.frombuffer(x, np.dtype(np.uint16)).copy()[:, np.newaxis]
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(pgreen.contents),
                                        nelts * 2)
    green = np.frombuffer(x, np.dtype(np.uint16)).copy()[:, np.newaxis]
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(pblue.contents),
                                        nelts * 2)
    blue = np.frombuffer(x, np.dtype(np.uint16)).copy()[:, np.newaxis]
    cmap = np.concatenate([red, green, blue], axis=1)
    return status, cmap


def _get_field_int32(tif, tag):
    """Single int32 value, i.e. FAXMODE"""
    val = ctypes.c_int32()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_int32))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    return status, val.value


def _get_field_uint32(tif, tag):
    """Single uint32 value, i.e. IMAGEWIDTH"""
    val = ctypes.c_uint32()
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_uint32))
    TIFF.TIFFGetField.argtypes = argtypes
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    return status, val.value


def _get_field_uint32p_count_offsets(tif, tag):
    """uint32 array depending of number of strips, tiles, i.e. TILEOFFSETS"""
    if isTiled(tif):
        nelts = numberOfTiles(tif)
    else:
        nelts = numberOfStrips(tif)

    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    ptype = ctypes.POINTER(ctypes.c_uint32 * nelts)
    argtypes.append(ctypes.POINTER(ptype))
    TIFF.TIFFGetField.argtypes = argtypes
    val = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val))
    nelts *= 4
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(val.contents), nelts)
    data = np.frombuffer(x, np.dtype(np.uint32)).copy()
    return status, data


def _get_field_uint32_count_uint8_data(tif, tag):
    """uint32 count, void data array, i.e. ICCPROFILE"""
    TIFF.TIFFGetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t]
    argtypes.append(ctypes.POINTER(ctypes.c_uint32))
    argtypes.append(ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)))
    TIFF.TIFFGetField.argtypes = argtypes
    val1 = ctypes.c_uint32()
    ptype = ctypes.POINTER(ctypes.c_uint8)
    val2 = ptype()
    status = TIFF.TIFFGetField(tif, tag, ctypes.byref(val1),
                                   ctypes.byref(val2))
    nelts = val1.value
    x = np.core.multiarray.int_asbuffer(ctypes.addressof(val2.contents), nelts)
    data = np.frombuffer(x, np.dtype(np.uint8)).copy()
    return status, data


def _set_field_char(tif, tag, value):
    """Single string value, i.e. IMAGEDESCRIPTION"""
    TIFF.TIFFSetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.c_char_p]
    TIFF.TIFFSetField.argtypes = argtypes
    status = TIFF.TIFFSetField(tif, tag, value)
    return status


def _set_field_inknames(tif, tag, inknames):
    """INKNAMES"""
    TIFF.TIFFSetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.c_uint32, ctypes.c_char_p]
    TIFF.TIFFSetField.argtypes = argtypes
    inkvalue = inknames[0]
    for ink in inknames[1:3]:
        inkvalue = inkvalue + chr(0) + ink
    status = TIFF.TIFFSetField(tif, tag, len(inkvalue)+1, inkvalue)
    return status


def _set_field_uint16(tif, tag, value):
    """Single uint16 value, i.e. BITSPERSAMPLE"""
    TIFF.TIFFSetField.restype = ctypes.c_int16
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.c_uint16]
    TIFF.TIFFSetField.argtypes = argtypes
    status = TIFF.TIFFSetField(tif, tag, value)
    return status


def _set_field_uint32(tif, tag, value):
    """Single uint32 value, i.e. IMAGEWIDTH"""
    TIFF.TIFFSetField.restype = ctypes.c_int32
    argtypes = [ctypes.c_void_p, ttag_t, ctypes.c_uint32]
    TIFF.TIFFSetField.argtypes = argtypes
    status = TIFF.TIFFSetField(tif, tag, value)
    return status

SUBFILETYPE = 254
IMAGEWIDTH = 256
IMAGELENGTH = 257
BITSPERSAMPLE = 258
COMPRESSION = 259
PHOTOMETRIC = 262
THRESHHOLDING = 263
FILLORDER = 266
DOCUMENTNAME = 269
IMAGEDESCRIPTION = 270
MAKE = 271
MODEL = 272
STRIPOFFSETS = 273
ORIENTATION = 274
SAMPLESPERPIXEL = 277
ROWSPERSTRIP = 278
STRIPBYTECOUNTS = 279
MINSAMPLEVALUE = 280
MAXSAMPLEVALUE = 281
XRESOLUTION = 282
YRESOLUTION = 283
PLANARCONFIG = 284
PAGENAME = 285
XPOSITION = 286
YPOSITION = 287
GROUP3OPTIONS = 292
GROUP4OPTIONS = 293
RESOLUTIONUNIT = 296
PAGENUMBER = 297
SOFTWARE = 305
DATETIME = 306
ARTIST = 315
HOSTCOMPUTER = 316
PREDICTOR = 317
WHITEPOINT = 318
PRIMARYCHROMATICITIES = 319
COLORMAP = 320
HALFTONEHINTS = 321
TILEWIDTH = 322
TILELENGTH = 323
TILEOFFSETS = 324
TILEBYTECOUNTS = 325
BADFAXLINES = 326
CLEANFAXDATA = 327
CONSECUTIVEBADFAXLINES = 328
SUBIFD = 330
INKSET = 332
INKNAMES = 333
NUMBEROFINKS = 334
DOTRANGE = 336
TARGETPRINTER = 337
EXTRASAMPLES = 338
SAMPLEFORMAT = 339
SMINSAMPLEVALUE = 340
SMAXSAMPLEVALUE = 341
JPEGTABLES = 347
REFERENCEBLACKWHITE = 532
YCBCRCOEFFICIENTS = 529
YCBCRSUBSAMPLING = 530
YCBCRPOSITIONING = 531
XMLPACKET = 700
MATTEING = 32995
DATATYPE = 32996
IMAGEDEPTH = 32997
TILEDEPTH = 32998
PIXAR_TEXTUREFORMAT = 33302
PIXAR_WRAPMODES = 33303
COPYRIGHT = 33432
FNUMBER = 33437
RICHTIFFIPTC = 33723
PHOTOSHOP = 34377
EXIFIFD = 34665
ICCPROFILE = 34675
SHUTTERSPEEDVALUE = 37377
STONITS = 37439
FAXMODE = 65536
JPEGQUALITY = 65537
JPEGCOLORMODE = 65538
JPEGTABLESMODE = 65539

getfielddict = {
    ARTIST:                 _get_field_char,
    BADFAXLINES:            _get_field_uint32,
    BITSPERSAMPLE:          _get_field_uint16,
    CLEANFAXDATA:           _get_field_uint16,
    COLORMAP:               _get_field_3uint16p,
    COMPRESSION:            _get_field_uint16,
    CONSECUTIVEBADFAXLINES: _get_field_uint32,
    COPYRIGHT:              _get_field_char,
    DATATYPE:               _get_field_uint16,
    DATETIME:               _get_field_char,
    DOCUMENTNAME:           _get_field_char,
    DOTRANGE:               _get_field_2uint16,
    EXIFIFD:                _get_field_uint32,
    EXTRASAMPLES:           _get_field_uint16_uint16p,
    FAXMODE:                _get_field_int32,
    FILLORDER:              _get_field_uint16,
    FNUMBER:                _get_field_float,
    GROUP3OPTIONS:          _get_field_uint32,
    GROUP4OPTIONS:          _get_field_uint32,
    HALFTONEHINTS:          _get_field_uint16,
    HOSTCOMPUTER:           _get_field_char,
    ICCPROFILE:             _get_field_uint32_count_uint8_data,
    IMAGEDESCRIPTION:       _get_field_char,
    IMAGEDEPTH:             _get_field_uint32,
    IMAGELENGTH:            _get_field_uint32,
    IMAGEWIDTH:             _get_field_uint32,
    INKNAMES:               _get_field_inknames,
    INKSET:                 _get_field_uint16,
    JPEGCOLORMODE:          _get_field_int32,
    JPEGQUALITY:            _get_field_int32,
    JPEGTABLES:             _get_field_uint32_count_uint8_data,
    JPEGTABLESMODE:         _get_field_int32,
    MAKE:                   _get_field_char,
    MATTEING:               _get_field_uint16,
    MINSAMPLEVALUE:         _get_field_uint16,
    MAXSAMPLEVALUE:         _get_field_uint16,
    MODEL:                  _get_field_char,
    NUMBEROFINKS:           _get_field_uint16,
    ORIENTATION:            _get_field_uint16,
    PAGENAME:               _get_field_char,
    PAGENUMBER:             _get_field_uint16,
    PHOTOMETRIC:            _get_field_uint16,
    PHOTOSHOP:              _get_field_uint32_count_uint8_data,
    PIXAR_TEXTUREFORMAT:    _get_field_char,
    PIXAR_WRAPMODES:        _get_field_char,
    PLANARCONFIG:           _get_field_uint16,
    PREDICTOR:              _get_field_uint16,
    PRIMARYCHROMATICITIES:  _get_field_floatp6,
    REFERENCEBLACKWHITE:    _get_field_floatp6,
    RESOLUTIONUNIT:         _get_field_uint16,
    ROWSPERSTRIP:           _get_field_uint32,
    RICHTIFFIPTC:           _get_field_uint32_count_uint8_data,
    SAMPLEFORMAT:           _get_field_uint16,
    SAMPLESPERPIXEL:        _get_field_uint16,
    SHUTTERSPEEDVALUE:      _get_field_float,  # exif
    SMINSAMPLEVALUE:        _get_field_double,
    SMAXSAMPLEVALUE:        _get_field_double,
    SOFTWARE:               _get_field_char,
    STONITS:                _get_field_double,
    STRIPBYTECOUNTS:        _get_field_uint32p_count_offsets,
    STRIPOFFSETS:           _get_field_uint32p_count_offsets,
    SUBFILETYPE:            _get_field_uint32,
    SUBIFD:                 _get_field_uint16_count_uint32_offsets,
    TARGETPRINTER:          _get_field_char,
    THRESHHOLDING:          _get_field_uint16,
    TILEBYTECOUNTS:         _get_field_uint32p_count_offsets,
    TILEDEPTH:              _get_field_uint32,
    TILELENGTH:             _get_field_uint32,
    TILEOFFSETS:            _get_field_uint32p_count_offsets,
    TILEWIDTH:              _get_field_uint32,
    TILEDEPTH:              _get_field_uint32,
    XMLPACKET:              _get_field_uint32_count_uint8_data,
    WHITEPOINT:             _get_field_floatp2,
    XPOSITION:              _get_field_float,
    XRESOLUTION:            _get_field_float,
    YPOSITION:              _get_field_float,
    YRESOLUTION:            _get_field_float,
    YCBCRCOEFFICIENTS:      _get_field_floatp3,
    YCBCRPOSITIONING:       _get_field_uint16,
    YCBCRSUBSAMPLING:       _get_field_2uint16,
}

setfielddict = {
    ARTIST:                 _set_field_char,
    BITSPERSAMPLE:          _set_field_uint16,
    COPYRIGHT:              _set_field_char,
    DATETIME:               _set_field_char,
    DOCUMENTNAME:           _set_field_char,
    HOSTCOMPUTER:           _set_field_char,
    IMAGEDESCRIPTION:       _set_field_char,
    IMAGELENGTH:            _set_field_uint32,
    IMAGEWIDTH:             _set_field_uint32,
    INKNAMES:               _set_field_inknames,
    MAKE:                   _set_field_char,
    MODEL:                  _set_field_char,
    NUMBEROFINKS:           _set_field_uint16,
    PAGENAME:               _set_field_char,
    PHOTOMETRIC:            _set_field_uint16,
    PIXAR_TEXTUREFORMAT:    _set_field_char,
    PIXAR_WRAPMODES:        _set_field_char,
    PLANARCONFIG:           _set_field_uint16,
    SOFTWARE:               _set_field_char,
    TARGETPRINTER:          _set_field_char,
    SAMPLESPERPIXEL:        _set_field_uint16,
}


def checkTile(tif, x, y, z=0, sample=0):
    """Corresponds to libtiff library routine TIFFCheckTile.

    Verify that x,y,z,sample is within image.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes
    x, y, z, sample : int
        pixel coordinates

    Returns
    -------
    bool
        True if the coordinate is in the image.
    """
    TIFF.TIFFCheckTile.argtypes = [ctypes.c_void_p,
                                       ctypes.c_uint32,
                                       ctypes.c_uint32,
                                       ctypes.c_uint32,
                                       tsample_t]
    TIFF.TIFFCheckTile.restype = ctypes.c_int32
    yn = TIFF.TIFFCheckTile(tif, x, y, z, sample)
    if yn:
        return True
    else:
        return False


def close(tif):
    """Corresponds to libtiff library routine TIFFClose.

    Close a previously opened TIFF file.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes
    """
    TIFF.TIFFClose.argtypes = [ctypes.c_void_p]
    TIFF.TIFFClose(tif)


def getVersion():
    """Corresponds to libtiff library routine TIFFGetVersion.

    Returns
    -------
    str
        library version string
    """
    TIFF.TIFFGetVersion.restype = ctypes.c_char_p
    v = TIFF.TIFFGetVersion()
    return(v.decode('utf-8'))


def computeStrip(tif, row, sample=0):
    """Corresponds to libtiff library routine TIFFComputeStrip.

    Return index of strip containing the row, sample.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    row, sample : int
        Image coordinates.  The sample is only used if the data is organized
        in separate planes.

    Returns
    -------
    int
        Index of the containing strip.
    """
    TIFF.TIFFComputeStrip.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                          tsample_t]
    TIFF.TIFFComputeStrip.restype = tstrip_t
    idx = TIFF.TIFFComputeStrip(tif, row, sample)
    return idx


def computeTile(tif, x, y, z=0, sample=0):
    """Corresponds to libtiff library routine TIFFComputeTile.

    Return index of tile containing sample.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    x, y : int
        pixel coordinates
    z : int
        depth coordinate, only used if more than one slice
    sample : int
        sample coordinate, only used if data is organized in separate planes.

    Returns
    -------
    int
        Index of the containing tile.
    """
    TIFF.TIFFComputeTile.argtypes = [ctypes.c_void_p,
                                         ctypes.c_uint32,
                                         ctypes.c_uint32,
                                         tsample_t]
    TIFF.TIFFComputeTile.restype = ttile_t
    idx = TIFF.TIFFComputeTile(tif, x, y, z, sample)
    return idx


def getField(tif, tag):
    """Corresponds to libtiff library routine TIFFGetField.

    Return tag value in current directory.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    object
        Tag value.
    """
    status, value = getfielddict[tag](tif, tag)
    if not status:
        raise RuntimeError("Unable to retrieve tag %d." % tag)
    return value


def isTiled(tif):
    """Corresponds to libtiff library routine TIFFIsTiled.

    Determines if image data is tiled.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    bool
        True if current image is tiled.
    """
    TIFF.TIFFIsTiled.argtypes = [ctypes.c_void_p]
    TIFF.TIFFIsTiled.restype = ctypes.c_int32
    yn = TIFF.TIFFIsTiled(tif)
    if yn:
        return True
    else:
        return False


def lastDirectory(tif):
    """Corresponds to libtiff library routine TIFFLastDirectory.

    Determines if the current directory is the last.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    bool
        True if the current directory is the last in the file.
    """
    TIFF.TIFFLastDirectory.argtypes = [ctypes.c_void_p]
    TIFF.TIFFReadDirectory.restype = ctypes.c_int32
    yn = TIFF.TIFFLastDirectory(tif)
    if yn:
        return True
    else:
        return False


def numberOfStrips(tif):
    """Corresponds to libtiff library routine TIFFNumberOfStrips.

    Return number of strips in image.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    int
        Number of strips in image.
    """
    TIFF.TIFFNumberOfStrips.argtypes = [ctypes.c_void_p]
    TIFF.TIFFNumberOfStrips.restype = tstrip_t
    n = TIFF.TIFFNumberOfStrips(tif)
    return n


def numberOfTiles(tif):
    """Corresponds to libtiff library routine TIFFNumberOfTiles.

    Return number of tiles in image.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    int
        Number of tiles in image.
    """
    TIFF.TIFFNumberOfTiles.argtypes = [ctypes.c_void_p]
    TIFF.TIFFNumberOfTiles.restype = ttile_t
    n = TIFF.TIFFNumberOfTiles(tif)
    return n


def open(filename, mode='r'):
    """Corresponds to libtiff library routine TIFFOpen.

    Opens a TIFF file according to the mode.

    Parameters
    ----------
    filename : str
        Path = TIFF file.
    mode : str
        Specifies how the file is to be opened.

    Returns
    -------
    int
        TIFF file pointer via ctypes
    """
    TIFF.TIFFOpen.restype = ctypes.c_void_p
    TIFF.TIFFOpen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    fp = TIFF.TIFFOpen(ctypes.c_char_p(filename.encode()),
                           ctypes.c_char_p(mode.encode()))
    if fp is None:
        raise RuntimeError("Unable to open %s." % filename)
    return fp


def readDirectory(tif):
    """Corresponds to libtiff library routine TIFFReadDirectory.

    Read the next directory.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    """
    TIFF.TIFFReadDirectory.argtypes = [ctypes.c_void_p]
    TIFF.TIFFReadDirectory.restype = ctypes.c_int32
    status = TIFF.TIFFReadDirectory(tif)
    if not status:
        raise RuntimeError("Unable to read next directory")


def readEXIFDirectory(tif, diroff):
    """Corresponds to libtiff library routine TIFFReadEXIFDirectory.

    Reads EXIF IFD.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    diroff :  int
        offset of EXIF IFD
    """
    TIFF.TIFFReadEXIFDirectory.argtypes = [ctypes.c_void_p, toff_t]
    TIFF.TIFFReadEXIFDirectory.restype = ctypes.c_int32
    status = TIFF.TIFFReadEXIFDirectory(tif, diroff)
    if not status:
        raise RuntimeError("Unable to read EXIF directory at %d." % diroff)


def readEncodedStrip(tif, stripnum):
    """Corresponds to libtiff library routine TIFFSReadEncodedStrip.

    Reads and decodes a full strip of data.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes
    stripnum : int
        strip number

    Returns
    -------
    ndarray
        image data for the specified strip
    """
    TIFF.TIFFReadEncodedStrip.argtypes = [ctypes.c_void_p,
                                              tstrip_t,
                                              tdata_t,
                                              tsize_t]
    TIFF.TIFFReadEncodedStrip.restype = ctypes.c_int32
    w = getField(tif, IMAGEWIDTH)
    h = min([getField(tif, IMAGELENGTH), getField(tif, ROWSPERSTRIP)])
    bps = getField(tif, BITSPERSAMPLE)
    spp = getField(tif, SAMPLESPERPIXEL)
    fmt = getField(tif, SAMPLEFORMAT)

    dtype = _readEncodedDatatype(bps, fmt)

    if spp == 1:
        image = np.zeros((h, w), dtype=dtype)
    else:
        image = np.zeros((h, w, spp), dtype=dtype)

    nbytes = stripSize(tif)
    buffer = image.ctypes.data_as(ctypes.c_void_p)
    status = TIFF.TIFFReadEncodedStrip(tif, stripnum, buffer, nbytes)
    if not status:
        raise RuntimeError("Unable to read encoded strip.")
    return image


def _numpy_datatype(tif):
    """
    Return the numpy datatype appropriate to the current image.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes

    Returns
    -------
    numpy.dtype
        The numpy datatype appropriate to the current image.
    """
    bps = getField(tif, BITSPERSAMPLE)
    fmt = getField(tif, SAMPLEFORMAT)
    return _readEncodedDatatype(bps, fmt)


def readEncodedTile(tif, tilenum):
    """Corresponds to libtiff library routine TIFFencodedTile.

    Reads and decodes a full tile of data.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes
    tilenum : int
        Zero-based tile number, left-to-right, top-to-bottom

    Returns
    -------
    ndarray
        Image data for the specified tile.
    """
    TIFF.TIFFReadEncodedTile.argtypes = [ctypes.c_void_p,
                                             ttile_t,
                                             tdata_t,
                                             tsize_t]
    TIFF.TIFFReadEncodedTile.restype = ctypes.c_int32
    w = getField(tif, TILEWIDTH)
    h = getField(tif, TILELENGTH)
    bps = getField(tif, BITSPERSAMPLE)
    spp = getField(tif, SAMPLESPERPIXEL)
    fmt = getField(tif, SAMPLEFORMAT)

    dtype = _readEncodedDatatype(bps, fmt)
    if spp == 1:
        image = np.zeros((h, w), dtype=dtype)
    else:
        image = np.zeros((h, w, spp), dtype=dtype)
    nbytes = tileSize(tif)
    buffer = image.ctypes.data_as(ctypes.c_void_p)
    status = TIFF.TIFFReadEncodedTile(tif, tilenum, buffer, nbytes)
    if not status:
        raise RuntimeError("Unable to read encoded tile.")
    return image


def RGBAImageOK(tif):
    """
    Corresponds to libtiff library routine TIFFRGBAImageOK.

    Check if an image can be processed with the RGBA routines.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes

    Returns
    -------
    ok : bool
        True if the image can be processed with the RGBA routines.
    emsg : str
        If ok is False, this string contains the reason.
    """
    TIFF.TIFFRGBAImageOK.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    TIFF.TIFFRGBAImageOK.restype = ctypes.c_int32
    emsg_buffer = ctypes.create_string_buffer(1024)
    status = TIFF.TIFFRGBAImageOK(tif, emsg_buffer)
    ok = True if status == 1 else False
    emsg = emsg_buffer.raw.decode('utf-8').rstrip('\x00')
    return ok, emsg


def readRGBAImage(tif):
    """Corresponds to libtiff library routine TIFFReadRGBAImage.

    Reads image as RGBA.

    Parameters
    ----------
    tif : int
       TIFF file pointer via ctypes

    Returns
    -------
    ndarray
        mxnx4 RGBA image
    """
    TIFF.TIFFReadRGBAImage.argtypes = [ctypes.c_void_p,
                                           ctypes.c_uint32,
                                           ctypes.c_uint32,
                                           ctypes.POINTER(ctypes.c_uint32),
                                           ctypes.c_int32]
    TIFF.TIFFReadRGBAImage.restype = ctypes.c_int32
    w = getField(tif, IMAGEWIDTH)
    h = getField(tif, IMAGELENGTH)
    image = np.zeros((h, w, 4), dtype=np.uint8)
    buffer = image.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
    status = TIFF.TIFFReadRGBAImage(tif, w, h, buffer, 0)
    if not status:
        raise RuntimeError("Unable to read RGBA image.")
    return np.flipud(image)


def readRGBAStrip(tif, row):
    """Corresponds to libtiff library routine TIFFReadRGBAStrip.

    Reads strip as RGBA.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    row : int
        coordinate of row contained in desired strip

    Returns
    -------
    ndarray
        mxnx4 RGBA image
    """
    TIFF.TIFFReadRGBAStrip.argtypes = [ctypes.c_void_p,
                                           ctypes.c_uint32,
                                           ctypes.POINTER(ctypes.c_uint32)]
    TIFF.TIFFReadRGBAStrip.restype = ctypes.c_int32
    w = getField(tif, IMAGEWIDTH)
    h = getField(tif, ROWSPERSTRIP)
    strip = np.zeros((h, w, 4), dtype=np.uint8)
    buffer = strip.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
    status = TIFF.TIFFReadRGBAStrip(tif, row, buffer)
    if not status:
        raise RuntimeError("Unable to read RGBA strip.")
    return np.flipud(strip)


def readRGBATile(tif, x, y):
    """Corresponds to libtiff library routine TIFFReadRGBATile.

    Reads image as RGBA.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    x, y : int
        pixel coordinates of upper left hand corner

    Returns
    -------
    ndarray
        mxnx4 RGBA image
    """
    TIFF.TIFFReadRGBATile.argtypes = [ctypes.c_void_p,
                                          ctypes.c_uint32,
                                          ctypes.c_uint32,
                                          ctypes.POINTER(ctypes.c_uint32)]
    TIFF.TIFFReadRGBATile.restype = ctypes.c_int32
    w = getField(tif, TILEWIDTH)
    h = getField(tif, TILELENGTH)
    tile = np.zeros((h, w, 4), dtype=np.uint8)
    buffer = tile.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
    status = TIFF.TIFFReadRGBATile(tif, x, y, buffer)
    if not status:
        raise RuntimeError("Unable to read RGBA tile.")
    return np.flipud(tile)


def setDirectory(tif, dirnum):
    """Corresponds to libtiff library routine TIFFSetDirectory.

    Sets the current directory.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    dirno : int
         directory number
    """
    TIFF.TIFFSetDirectory.argtypes = [ctypes.c_void_p, tdir_t]
    TIFF.TIFFStripSize.restype = ctypes.c_int32
    status = TIFF.TIFFSetDirectory(tif, dirnum)
    if not status:
        msg = "Unable to set directory to {dirnum}.".format(dirnum=dirnum)
        raise RuntimeError(msg)


def setField(tif, tag, data):
    """Corresponds to libtiff library routine TIFFSetField.

    Write tag value in current directory.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes
    tag : int
        numeric value specifying a tag
    value : object
        tag value to write
    """
    status = setfielddict[tag](tif, tag, data)
    if not status:
        raise RuntimeError("Unable to write tag %d." % tag)


def stripSize(tif):
    """Corresponds to libtiff library routine TIFFStripSize.

    Return size of a strip.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    int
        Size of a strip in bytes.
    """
    TIFF.TIFFStripSize.argtypes = [ctypes.c_void_p]
    TIFF.TIFFStripSize.restype = tsize_t
    sz = TIFF.TIFFStripSize(tif)
    return sz


def tileSize(tif):
    """Corresponds to libtiff library routine TIFFTileSize.

    Return size of a tile.

    Parameters
    ----------
    tif : int
        TIFF file pointer via ctypes

    Returns
    -------
    int
        Size of a tile in bytes.
    """
    TIFF.TIFFTileSize.argtypes = [ctypes.c_void_p]
    TIFF.TIFFTileSize.restype = tsize_t
    sz = TIFF.TIFFTileSize(tif)
    return sz
