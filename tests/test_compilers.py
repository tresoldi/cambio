#!/usr/bin/env python3
# encoding: utf-8

"""
test_compilers
==============

Tests for the compilers in the `alteruphono` package.
"""

# Import third-party libraries
import logging
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono
import tatsu

# Setup logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
LOGGER = logging.getLogger("TestLog")


class TestCompilers(unittest.TestCase):
    """
    Class for `alteruphono` tests related to compilers.
    """

    def test_dummy(self):
        assert 1 == 1


if __name__ == "__main__":
    sys.exit(unittest.main())
