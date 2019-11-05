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

# Import the library being test and auxiliary libraries
import alteruphono
import tatsu

# Setup logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
LOGGER = logging.getLogger("TestLog")


class TestUtils(unittest.TestCase):
    """
    Class for `alteruphono` tests related to utility functions.
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


# TODO: add negative tests (test if it fails)
class TestParser(unittest.TestCase):
    """
    Class for testing the grammar parsing.
    """

    parser = alteruphono.Parser()

    def test_sound(self):
        # Assert parsing success
        self.parser.parse("a", rule_name="sound")
        self.parser.parse("V", rule_name="sound")
        self.parser.parse("#", rule_name="sound")

        # Assert parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="sound")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="sound")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="sound")

    def test_sound_class(self):
        # Assert parsing success
        self.parser.parse("A", rule_name="sound_class")
        self.parser.parse("*A", rule_name="sound_class")
        self.parser.parse("MYCLASS", rule_name="sound_class")
        self.parser.parse("*MYCLASS", rule_name="sound_class")
        self.parser.parse("MYCLASS[+voiced]", rule_name="sound_class")
        self.parser.parse("*MYCLASS[!voiced,bilabial]", rule_name="sound_class")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="sound_class")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="sound_class")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="sound_class")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("#", rule_name="sound_class")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="sound_class")

        # TODO: should fail
        #with self.assertRaises(tatsu.exceptions.FailedParse):
        #    self.parser.parse("MY-CLASS", rule_name="sound_class")


    def test_ipa(self):
        # Asserts parsing success
        self.parser.parse("e", rule_name="ipa")
        self.parser.parse("*e", rule_name="ipa")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="ipa")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("V", rule_name="ipa")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="ipa")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("#", rule_name="ipa")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="ipa")

    def test_boundary_symbol(self):
        # Asserts parsing success
        self.parser.parse("#", rule_name="boundary_symbol")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="boundary_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("V", rule_name="boundary_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="boundary_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="boundary_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="boundary_symbol")

    def test_position_symbol(self):
        # Asserts parsing success
        self.parser.parse("_", rule_name="position_symbol")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="position_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("V", rule_name="position_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="position_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="position_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="position_symbol")

    def test_empty_symbol(self):
        # Asserts parsing success
        self.parser.parse(":NULL:", rule_name="empty_symbol")
        self.parser.parse("0", rule_name="empty_symbol")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="empty_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("V", rule_name="empty_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="empty_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="empty_symbol")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("_", rule_name="empty_symbol")

    def test_arrow(self):
        # Asserts parsing success
        self.parser.parse("->", rule_name="arrow")
        self.parser.parse("==>", rule_name="arrow")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="arrow")

    def test_slash(self):
        # Asserts parsing success
        self.parser.parse("/", rule_name="slash")
        self.parser.parse("//", rule_name="slash")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="slash")

    def test_alternative(self):
        # Asserts parsing success
        self.parser.parse("a|b|c", rule_name="alternative")
        self.parser.parse("a|V|#", rule_name="alternative")
        self.parser.parse("*S|m[syllabic]|#", rule_name="alternative")
        self.parser.parse("a", rule_name="alternative")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a|", rule_name="alternative")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="alternative")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="alternative")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a|_", rule_name="alternative")

    def test_mapper(self):
        # Asserts parsing success
        self.parser.parse("{a,b,c}", rule_name="mapper")
        self.parser.parse("{a}", rule_name="mapper")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{V}", rule_name="mapper")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{a,}", rule_name="mapper")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{a,b,}", rule_name="mapper")

    def test_backref(self):
        # Asserts parsing success
        self.parser.parse("@1", rule_name="back_ref")
        self.parser.parse("*@3[+voice]", rule_name="back_ref")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="back_ref")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("V", rule_name="back_ref")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="back_ref")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="back_ref")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("_", rule_name="back_ref")

    def test_feature_key(self):
        # Asserts parsing success
        self.parser.parse("abcde", rule_name="feature_key")
        self.parser.parse("feat3", rule_name="feature_key")
        self.parser.parse("feature_name", rule_name="feature_key")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="feature_key")

        # TODO: should raise an exception
        #with self.assertRaises(tatsu.exceptions.FailedParse):
        #    self.parser.parse("feat(ure)", rule_name="feature_key")

    def test_feature(self):
        # Asserts parsing success
        self.parser.parse("feature", rule_name="feature")
        self.parser.parse("+feature", rule_name="feature")
        self.parser.parse("feature=true", rule_name="feature")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("~feature1", rule_name="feature")

        # TODO: should raise an exception
    #    with self.assertRaises(tatsu.exceptions.FailedParse):
    #        self.parser.parse("feature1,feature2", rule_name="feature")
    #    with self.assertRaises(tatsu.exceptions.FailedParse):
    #        self.parser.parse("feature1=value", rule_name="feature")
    #    with self.assertRaises(tatsu.exceptions.FailedParse):
    #        self.parser.parse("feature=", rule_name="feature")
    #    with self.assertRaises(tatsu.exceptions.FailedParse):
    #        self.parser.parse("+feature=true", rule_name="feature")

    def test_feature_desc(self):
        # Asserts parsing success
        self.parser.parse("[high]", rule_name="feature_desc")
        self.parser.parse("[high,rounded]", rule_name="feature_desc")
        self.parser.parse("*[high,rounded]", rule_name="feature_desc")
        self.parser.parse("[+high,-rounded]", rule_name="feature_desc")
        self.parser.parse("[high=true,rounded=false]", rule_name="feature_desc")

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[high", rule_name="feature")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[high,]", rule_name="feature")

    def test_segment(self):
        # Asserts parsing success
        self.parser.parse("t", rule_name="segment")
        self.parser.parse("t|s", rule_name="segment")
        self.parser.parse("#", rule_name="segment")
        self.parser.parse("_", rule_name="segment")
        self.parser.parse(":NULL:", rule_name="segment")
        self.parser.parse("[+high,-rounded]", rule_name="segment")
        self.parser.parse("@1", rule_name="segment")
        self.parser.parse("{t,s}", rule_name="segment")

        # Asserts parsing failure
        # TODO: should be failing
    #    with self.assertRaises(tatsu.exceptions.FailedParse):
    #        self.parser.parse("t+s", rule_name="segment")

    def test_sequence(self):
        # Asserts parsing success
        self.parser.parse("t", rule_name="sequence")
        self.parser.parse("t s", rule_name="sequence")
        self.parser.parse("t|s a _ @1 [+high,-rounded]", rule_name="sequence")

    def test_start(self):
        # Assert parsing success; these are basic tests, the complete
        # ones use the data from the sound change catalog provided
        # with the library
        self.parser.parse("p > b / V _ V", rule_name="start")
        self.parser.parse("p -> b")


class TestSoundChange(unittest.TestCase):
    def test_basic_change(self):
        """
        Test basic sound changes.
        """

        assert alteruphono.apply_rule("b a b a", "b", "p") == "p a p a"
        assert alteruphono.apply_rule("b a b a", "t", "p") == "b a b a"

    def test_specific_changes(self):
        # specific changes to trigger 100% coverage
        assert (
            alteruphono.apply_rule("t a d a", "C", "@1[+voiced]") == "d a d a"
        )

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
            target = alteruphono.apply_rule(
                test_source, rule["source"], rule["target"]
            )
            target_wb = alteruphono.apply_rule(
                test_source_wb, rule["source"], rule["target"]
            )

            #LOGGER.debug("%s [%s] [%s]", rule_id, target, test_target)
            #LOGGER.debug("%s", str(rule))

            assert target == test_target
            assert target_wb == test_target_wb


if __name__ == "__main__":
    sys.exit(unittest.main())
