"""
Tests for setting/getting options from inside python
"""
# Standard library imports ...
import unittest
import warnings

# Local imports ...
import glymur


class TestSuite(unittest.TestCase):

    def setUp(self):
        glymur.reset_option('all')

    def tearDown(self):
        glymur.reset_option('all')

    def test_reset_single_option(self):
        """
        Verify a single option can be reset.
        """
        glymur.set_option('print.codestream', True)
        glymur.reset_option('print.codestream')
        self.assertTrue(glymur.get_option('print.codestream'))

    def test_bad_reset(self):
        """
        Verify exception when a bad option is given to reset
        """
        with self.assertRaises(KeyError):
            glymur.reset_option('blah')

    def test_bad_deprecated_print_option(self):
        """
        Verify exception when a bad option is given to old set_printoption
        """
        with self.assertRaises(KeyError):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                glymur.config.set_printoptions(blah='value-blah')
