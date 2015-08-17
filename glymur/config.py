"""
Configure glymur to use installed libraries if possible.
"""
import ctypes
from ctypes.util import find_library
import os
import platform
import warnings

import sys
if sys.hexversion <= 0x03000000:
    from ConfigParser import SafeConfigParser as ConfigParser
    from ConfigParser import NoOptionError, NoSectionError
else:
    from configparser import ConfigParser
    from configparser import NoOptionError, NoSectionError

# default library locations for MacPorts
_macports_default_location = {'openjp2': '/opt/local/lib/libopenjp2.dylib',
                              'openjpeg': '/opt/local/lib/libopenjpeg.dylib',
                              'tiff': '/opt/local/lib/libtiff.dylib'}


def glymurrc_fname():
    """Return the path to the configuration file.

    Search order:
        1) current working directory
        2) environ var XDG_CONFIG_HOME
        3) $HOME/.config/glymur/glymurrc
    """

    # Current directory.
    fname = os.path.join(os.getcwd(), 'glymurrc')
    if os.path.exists(fname):
        return fname

    confdir = get_configdir()
    if confdir is not None:
        fname = os.path.join(confdir, 'glymurrc')
        if os.path.exists(fname):
            return fname

    # didn't find a configuration file.
    return None


def load_library(libname):
    """
    Load shared library.

    Parameters
    ----------
    library : str
        Path to shared library.

    Returns
    -------
    ctypes.CDLL
        Loaded DLL/shared library.
    """

    path = read_config_file(libname)
    if path is not None:
        return load_library_handle(path)

    # No location specified by the configuration file, must look for it
    # elsewhere.
    path = find_library(libname)

    if path is None:
        # Could not find a library via ctypes
        if platform.system() == 'Darwin':
            # MacPorts
            path = _macports_default_location[libname]

        if path is not None and not os.path.exists(path):
            # the mac/win default location does not exist.
            return None

    return load_library_handle(path)


def load_library_handle(path):
    """
    Load the library, return the ctypes handle.
    """

    if path is None or path in ['None', 'none']:
        # Either could not find a library via ctypes or
        # user-configuration-file, or we could not find it in any of the
        # default locations, or possibly the user intentionally does not want
        # one of the libraries to load.
        return None

    try:
        if os.name == "nt":
            opj_lib = ctypes.windll.LoadLibrary(path)
        else:
            opj_lib = ctypes.CDLL(path)
    except (TypeError, OSError):
        msg = 'The library specified by configuration file at {0} could not '
        msg += 'be loaded.'
        warnings.warn(msg.format(path), UserWarning)
        opj_lib = None

    return opj_lib


def read_config_file(libname):
    """
    Extract library locations from a configuration file.

    Parameters
    ----------
    libname : str
        One of either 'openjp2' or 'openjpeg'

    Returns
    -------
    path : None or str
        None if no location is specified, otherwise a path to the library
    """
    filename = glymurrc_fname()
    if filename is None:
        # There's no library file path to return in this case.
        return None

    # Read the configuration file for the library location.
    parser = ConfigParser()
    parser.read(filename)
    try:
        path = parser.get('library', libname)
    except (NoOptionError, NoSectionError):
        path = None
    return path


def _load_data_source(src):
    """
    Extract data source locations from a configuration file.

    Parameters
    ----------
    src : str
        One of either 'opj_data_root' or 'libtiffpic'

    Returns
    -------
    path : None or str
        None if no location is specified, otherwise a path to the directory.
    """
    filename = glymurrc_fname()
    if filename is None:
        # There's no library file path to return in this case.
        return None

    # Read the configuration file for the library location.
    parser = ConfigParser()
    parser.read(filename)
    try:
        path = parser.get('testdata', src)
    except (NoOptionError, NoSectionError):
        path = None
    return path


def glymur_config():
    """
    Try to ascertain locations of openjp2, openjpeg, tiff libraries.

    Returns
    -------
    config : dict
        dictionary of library handles
    """
    config = {}
    for libname in ['openjp2', 'openjpeg', 'tiff']:
        config[libname] = load_library(libname)
    if config['openjp2'] is None and config['openjpeg'] is None:
        msg = "Neither the openjp2 nor the openjpeg library could be loaded.  "
        warnings.warn(msg)
    return config


def get_configdir():
    """
    Return string representing the configuration directory.

    Default is $HOME/.config/glymur.  You can override this with the
    XDG_CONFIG_HOME environment variable.
    """
    if 'XDG_CONFIG_HOME' in os.environ:
        return os.path.join(os.environ['XDG_CONFIG_HOME'], 'glymur')

    if 'HOME' in os.environ and os.name != 'nt':
        # HOME is set by WinPython to something unusual, so we don't
        # necessarily want that.
        return os.path.join(os.environ['HOME'], '.config', 'glymur')

    # Last stand.  Should handle windows... others?
    return os.path.join(os.path.expanduser('~'), 'glymur')


# This should be the only item that need be referenced from elsewhere.
CONFIG = glymur_config()
