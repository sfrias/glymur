"""These tests are for edge cases where OPENJPEG does not exist, but
OPENJP2 may be present in some form or other.
"""
import contextlib
import ctypes
import os
import sys
import tempfile
import unittest

if sys.hexversion <= 0x03030000:
    from mock import patch
else:
    from unittest.mock import patch

import glymur

from .fixtures import (WARNING_INFRASTRUCTURE_ISSUE,
                       WARNING_INFRASTRUCTURE_MSG,
                       WINDOWS_TMP_FILE_MSG)


def openjp2_not_found_by_ctypes():
    """
    Need to know if openjp2 library can be picked right up by ctypes for one
    of the tests.
    """
    if ctypes.util.find_library('openjp2') is None:
        return True
    else:
        return False


def openjpeg_not_found_by_ctypes():
    """
    Need to know if openjpeg library can be picked right up by ctypes for one
    of the tests.
    """
    if ctypes.util.find_library('openjpeg') is None:
        return True
    else:
        return False


def no_openjpeg_libraries_found_by_ctypes():
    return openjpeg_not_found_by_ctypes() and openjp2_not_found_by_ctypes()


@contextlib.contextmanager
def chdir(dirname=None):
    """
    This context manager restores the value of the current working directory
    (cwd) after the enclosed code block completes or raises an exception.  If a
    directory name is supplied to the context manager then the cwd is changed
    prior to running the code block.

    Shamelessly lifted from
    http://www.astropython.org/snippet/2009/10/chdir-context-manager
    """
    curdir = os.getcwd()
    try:
        if dirname is not None:
            os.chdir(dirname)
        yield
    finally:
        os.chdir(curdir)


@unittest.skipIf(sys.hexversion < 0x03020000,
                 "TemporaryDirectory introduced in 3.2.")
@unittest.skipIf(glymur.lib.openjp2.OPENJP2 is None,
                 "Needs openjp2 library first before these tests make sense.")
class TestSuite(unittest.TestCase):
    """Test suite for configuration file operation."""

    def setUp(self):
        self.jp2file = glymur.data.nemo()

    def test_config_file_via_environ(self):
        """
        Verify that we can read a configuration file set via environ var.

        Make a symlink to the openjp2 library in a temporary directory, then
        point towards that with the XDG_CONFIG_HOME environment variable.
        """
        config = glymur.config.CONFIG
        with tempfile.TemporaryDirectory() as rcdir:

            configdir = os.path.join(rcdir, 'glymur')
            os.mkdir(configdir)
            filename = os.path.join(configdir, 'glymurrc')

            with tempfile.TemporaryDirectory() as libdir:

                src = config['openjp2']._name
                dest = os.path.join(libdir,
                                    os.path.basename(config['openjp2']._name))
                os.symlink(src, dest)

                with open(filename, 'wt') as tfile:
                    tfile.write('[library]\n')
                    line = 'openjp2: {libloc}\n'.format(libloc=dest)
                    tfile.write(line)
                    tfile.flush()
                    with patch.dict('glymur.config.os.environ',
                                    {'XDG_CONFIG_HOME': rcdir}):
                        actual = glymur.config.glymur_config()['openjp2']._name
                        expected = dest
                        self.assertEqual(actual, expected)

    @unittest.skipIf(openjp2_not_found_by_ctypes(),
                     "Needs openjp2 and openjpeg before this test make sense.")
    def test_config_file_without_library_section(self):
        """
        must ignore if no library section
        """
        expected = ctypes.util.find_library('openjp2')
        with tempfile.TemporaryDirectory() as tdir:
            configdir = os.path.join(tdir, 'glymur')
            os.mkdir(configdir)
            fname = os.path.join(configdir, 'glymurrc')
            with open(fname, 'w') as fptr:
                fptr.write('[testing]\n')
                fptr.write('opj_data_root: blah\n')
                fptr.flush()
                with patch.dict('glymur.config.os.environ',
                                {'XDG_CONFIG_HOME': tdir}):
                    actual = glymur.config.glymur_config()['openjp2']._name
                    self.assertEqual(actual, expected)

    def test_xdg_env_config_file_is_bad(self):
        """A non-existant library location should be rejected."""
        with tempfile.TemporaryDirectory() as tdir:
            configdir = os.path.join(tdir, 'glymur')
            os.mkdir(configdir)
            fname = os.path.join(configdir, 'glymurrc')
            with open(fname, 'w') as fptr:
                with tempfile.NamedTemporaryFile(suffix='.dylib') as tfile:
                    fptr.write('[library]\n')
                    fptr.write('openjp2: {0}.not.there\n'.format(tfile.name))
                    fptr.flush()
                    with patch.dict('glymur.config.os.environ',
                                    {'XDG_CONFIG_HOME': tdir}):
                        # Misconfigured new configuration file should
                        # be rejected.
                        regex = 'could not be loaded'
                        with self.assertWarnsRegex(UserWarning, regex):
                            conf = glymur.config.glymur_config()
                            self.assertIsNone(conf['openjp2'])

    @unittest.skipIf((openjpeg_not_found_by_ctypes() and
                      openjp2_not_found_by_ctypes()),
                     "Needs openjp2 and openjpeg before this test make sense.")
    def test_library_specified_as_None(self):
        """Verify that we can stop library from being loaded by using None."""
        with tempfile.TemporaryDirectory() as tdir:
            configdir = os.path.join(tdir, 'glymur')
            os.mkdir(configdir)
            fname = os.path.join(configdir, 'glymurrc')
            with open(fname, 'w') as fptr:
                # Essentially comment out openjp2 and preferentially load
                # openjpeg instead.
                fptr.write('[library]\n')
                fptr.write('openjp2: None\n')
                openjpeg_lib = ctypes.util.find_library('openjpeg')
                msg = 'openjpeg: {openjpeg}\n'
                msg = msg.format(openjpeg=openjpeg_lib)
                fptr.write(msg)
                fptr.flush()

                with patch.dict('os.environ', {'XDG_CONFIG_HOME': tdir}):
                    conf = glymur.config.glymur_config()
                    self.assertIsNone(conf['openjp2'])
                    self.assertIsNotNone(conf['openjpeg'])

    def test_config_file_in_current_directory(self):
        """
        A configuration file in the current directory should be honored.

        Make a symlink to the openjp2 library in a temporary directory, then
        point towards that with the rc file.
        """
        config = glymur.config.CONFIG
        with tempfile.TemporaryDirectory() as libdir:
            # New library location.
            src = config['openjp2']._name
            dest = os.path.join(libdir,
                                os.path.basename(config['openjp2']._name))
            os.symlink(src, dest)

            expected = dest

            with tempfile.TemporaryDirectory() as rcdir:
                # new working directory
                new_config_file = os.path.join(rcdir, 'glymurrc')
                with open(new_config_file, 'w') as fptr:
                    fptr.write('[library]\n')
                    fptr.write('openjp2: {libloc}\n'.format(libloc=expected))
                    fptr.flush()

                    with chdir(rcdir):
                        actual = glymur.config.glymur_config()['openjp2']._name
                        self.assertEqual(actual, expected)
