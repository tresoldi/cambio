#!/usr/bin/env python3
# encoding: utf-8

"""
test_cambio
===========

Tests for the `cambio` package.
"""

# Import third-party libraries
import unittest

# Import the library being test
import cambio

class TestSoundChange(unittest.TestCase):
    """
    Class for `cambio` tests related to sound replacement.
    """

    def test_basic_change(self):
        assert cambio.basic_change("b a b a") == "p a p a"
