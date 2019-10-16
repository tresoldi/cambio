#!/usr/bin/env python3
# encoding: utf-8

"""
test_alteruphono
================

Tests for the `alteruphono` package.
"""

# Import third-party libraries
import logging
import sys
import unittest

# Import the library being test
import alteruphono

# Setup logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
LOGGER = logging.getLogger("TestLog")


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
        alteruphono.utils.read_sound_features()

    def test_basic_change(self):
        """
        Test basic sound changes.
        """

        assert alteruphono.apply_rule("b a b a", "b", "p") == "p a p a"
        assert alteruphono.apply_rule("b a b a", "t", "p") == "b a b a"

    def test_specific_changes(self):
        # specific changes to trigger 100% coverage
        assert alteruphono.apply_rule("t a d a", "C", "@1[+voiced]") == "d a d a"

        assert alteruphono.apply_rule("ɲ a", "C", "@1[+fricative]") == "ʑ a"

        assert alteruphono.apply_rule("t a", "C", "@1[+fricative]") == "s a"

    def test_random_change(self):
        rules = alteruphono.utils.read_sound_changes()
        alteruphono.utils.random_change(rules)

    def test_default_changes(self):
        """
        Run the embedded test of all default changes.
        """

        # The tests by default have no word borders, we tests both with and
        # without borders (which are added automatically by apply_rule)
        rules = alteruphono.utils.read_sound_changes()
        for rule_id, rule in rules.items():
            test_source, test_target = rule["test"].split("/")

            # Build normal source/target
            test_source = test_source.strip()
            test_target = test_target.strip()

            # Build word-boundary source/target
            test_source_wb = "# %s #" % test_source
            test_target_wb = "# %s #" % test_target

            # Process and assert
            target = alteruphono.apply_rule(test_source, rule["source"], rule["target"])
            target_wb = alteruphono.apply_rule(
                test_source_wb, rule["source"], rule["target"]
            )

            # LOGGER.debug("%s [%s] [%s]", rule_id, target, test_target)
            # LOGGER.debug("%s", str(rule))

            assert target == test_target
            assert target_wb == test_target_wb


if __name__ == "__main__":
    sys.exit(unittest.main())
