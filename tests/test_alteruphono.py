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
        alteruphono.utils.read_features()

    def test_basic_change(self):
        """
        Test basic sound changes.
        """

        assert (
            alteruphono.apply_rule("b a b a", {"source": "b", "target": "p"})
            == "p a p a"
        )
        assert (
            alteruphono.apply_rule("b a b a", {"source": "t", "target": "p"})
            == "b a b a"
        )

    def test_random_change(self):
        rules = alteruphono.utils.read_sound_changes()
        alteruphono.utils.random_change(rules)

    def test_default_changes(self):
        """
        Run the embedded test of all default changes.
        """

        rules = alteruphono.utils.read_sound_changes()
        for rule_id, rule in rules.items():
            test_source, test_target = rule["test"].split("/")
            test_source = test_source.strip()
            test_target = test_target.strip()

            target = alteruphono.apply_rule(
                test_source, {"source": rule["source"], "target": rule["target"]}
            )
            # LOGGER.debug("%s [%s] [%s]", rule_id, target, test_target)
            # LOGGER.debug("%s", str(rule))
            assert target == test_target


if __name__ == "__main__":
    sys.exit(unittest.main())
