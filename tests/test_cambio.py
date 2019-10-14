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

# TODO: test all cases in the default rules


class TestSoundChange(unittest.TestCase):
    """
    Class for `cambio` tests related to sound replacement.
    """

    def test_read_rules(self):
        """
        Tests if loading rules works and if the default ones are loadable.
        """

        rules = cambio.utils.read_sound_changes()

    def test_read_additional_data(self):
        """
        Test if additional resources are available and readable.
        """

        # Read sound class definitions
        cambio.utils.read_sound_classes()

        # Read feature definitions
        cambio.utils.read_features()

    def test_basic_change(self):
        """
        Test basic sound changes.
        """

        assert cambio.apply_rule("b a b a", {"source": "b", "target": "p"}) == "p a p a"
        assert cambio.apply_rule("b a b a", {"source": "t", "target": "p"}) == "b a b a"
