#!/usr/bin/env python3
# encoding: utf-8

"""
test_alteruphono
================

Tests for the `alteruphono` package.
"""

# Import third-party libraries
import unittest

# Import the library being test
import alteruphono

# TODO: test all cases in the default rules


class TestSoundChange(unittest.TestCase):
    """
    Class for `alteruphono` tests related to sound replacement.
    """

    def test_read_rules(self):
        """
        Tests if loading rules works and if the default ones are loadable.
        """

        rules = alteruphono.utils.read_sound_changes()

    def test_read_additional_data(self):
        """
        Test if additional resources are available and readable.
        """

        # Read sound class definitions
        alteruphono.utils.read_sound_classes()

        # Read feature definitions
        alteruphono.utils.read_features()

    def test_basic_change(self):
        """
        Test basic sound changes.
        """

        assert alteruphono.apply_rule("b a b a", {"source": "b", "target": "p"}) == "p a p a"
        assert alteruphono.apply_rule("b a b a", {"source": "t", "target": "p"}) == "b a b a"


if __name__ == "__main__":
    import sys
    sys.exit(unittest.main())
