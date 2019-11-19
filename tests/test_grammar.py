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
        assert len(rules) == 800

    def test_read_additional_data(self):
        """
        Test if additional resources are available and readable.
        """

        # Read sound class definitions
        sc = alteruphono.utils.read_sound_classes()
        assert len(sc) == 19
        assert sc['B']['description'] == 'back vowel'
        assert sc['H']['regex'] == "h̃|h̬|ʔh|ʔʲ|ʔʷ|h|ɦ|ʔ"

        # Read feature definitions
        feat = alteruphono.utils.read_sound_features()
        assert len(feat) == 130
        assert feat['long'] == 'duration'


class TestParser(unittest.TestCase):
    """
    Class for testing the grammar parsing.
    """

    parser = alteruphono.Parser()

    def test_sound(self):
        # Assert parsing success
        _ = self.parser.parse("a", rule_name="sound")
        assert _['ipa']['ipa'] == "a"

        _ = self.parser.parse("V", rule_name="sound")
        assert _['sound_class']['sound_class'] == "V"

        _ = self.parser.parse("#", rule_name="sound")
        assert _['boundary']['boundary'] == "#"

        # Assert parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="sound")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="sound")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("0", rule_name="sound")

    def test_sound_class(self):
        # Assert parsing success
        _ = self.parser.parse("A", rule_name="sound_class")
        assert _['sound_class'] == "A"

        _ = self.parser.parse("*A", rule_name="sound_class")
        assert _['sound_class'] == 'A'
        assert _['recons'] == "*"

        _ = self.parser.parse("MYCLASS", rule_name="sound_class")
        assert _['sound_class'] == 'MYCLASS'

        _ = self.parser.parse("*MYCLASS", rule_name="sound_class")
        assert _['sound_class'] == 'MYCLASS'
        assert _['recons'] == "*"

        _ = self.parser.parse("MYCLASS[+voiced]", rule_name="sound_class")
        assert _['sound_class'] == "MYCLASS"
        assert _['modifier']['feature_desc'][0]['value'] == "+"
        assert _['modifier']['feature_desc'][0]['key'] == "voiced"

        _ = self.parser.parse("*MYCLASS[!voiced,bilabial]", rule_name="sound_class")
        assert _['sound_class'] == "MYCLASS"
        assert _['recons'] == "*"
        assert _['modifier']['feature_desc'][0]['value'] == "!"
        assert _['modifier']['feature_desc'][1]['key'] == "bilabial"

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

        # Note that this does not raise an exception, as we are not
        # capturing a `start`, but only a `sound_class`
        _ = self.parser.parse("MY-CLASS", rule_name="sound_class")
        assert _['sound_class'] != "MY-CLASS"

    def test_ipa(self):
        # Asserts parsing success
        _ = self.parser.parse("e", rule_name="ipa")
        assert _['ipa'] == "e"

        _ = self.parser.parse("*e", rule_name="ipa")
        assert _['ipa'] == "e"
        assert _['recons'] == "*"

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
        _ = self.parser.parse("#", rule_name="boundary_symbol")
        assert _['boundary'] == "#"

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
        _ = self.parser.parse("_", rule_name="position_symbol")
        assert _['position'] == "_"

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
        _ = self.parser.parse(":null:", rule_name="empty_symbol")
        assert _['empty'] == ":null:"

        # TODO: check why it is not capturing the zero
#        _ = self.parser.parse("0", rule_name="empty_symbol")
#        assert _['empty'] == "0"

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
        _ = self.parser.parse("->", rule_name="arrow")
        assert _ == "->"
        _ = self.parser.parse("==>", rule_name="arrow")
        assert _ == "==>"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="arrow")

    def test_slash(self):
        # Asserts parsing success
        _ = self.parser.parse("/", rule_name="slash")
        assert _ == "/"
        _ = self.parser.parse("//", rule_name="slash")
        assert _ == "//"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="slash")

    def test_expression(self):
        # Asserts parsing success
        _ = self.parser.parse("a|b|c", rule_name="expression")
        assert len(_['expression']) == 3
        assert _['expression'][0]['ipa']['ipa'] == 'a'

        _ = self.parser.parse("a|V|#", rule_name="expression")
        assert len(_['expression']) == 3
        assert _['expression'][2]['boundary']['boundary'] == '#'

        # TODO: not capturing the modifier in `[syllabic]`
#        _ = self.parser.parse("*S|m[syllabic]|#", rule_name="expression")
#        print( _['expression'][1])

        _ = self.parser.parse("a", rule_name="expression")
        assert _['expression'][0]['ipa']['ipa'] == "a"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a|", rule_name="expression")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("13", rule_name="expression")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[bilabial,voiced,consonant]", rule_name="expression")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a|_", rule_name="expression")

    def test_mapper(self):
        # Asserts parsing success
        _ = self.parser.parse("{a,b,c}", rule_name="mapper")
        assert len(_['mapper']) == 3
        assert _['mapper'][1]['ipa'] == "b"
        _ = self.parser.parse("{a}", rule_name="mapper")
        assert _['mapper']['ipa'] == "a"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{V}", rule_name="mapper")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{a,}", rule_name="mapper")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("{a,b,}", rule_name="mapper")

    def test_backref(self):
        # Asserts parsing success
        _ = self.parser.parse("@1", rule_name="back_ref")
        assert _['back_ref'] == "1"
        _ = self.parser.parse("*@3[+voice]", rule_name="back_ref")
        assert _['recons'] == "*"
        assert _['back_ref'] == "3"
        assert _['modifier']['feature_desc'][0]['key'] == "voice"

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
        _ = self.parser.parse("abcde", rule_name="feature_key")
        assert _ == "abcde"

        _ = self.parser.parse("feat3", rule_name="feature_key")
        assert _ == "feat3"

        _ = self.parser.parse("feature_name", rule_name="feature_key")
        assert _ == "feature_name"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("a", rule_name="feature_key")

        # Note that this does not raise an exception, as we are not
        # capturing a `start`, but only a `sound_class`
        _ = self.parser.parse("feat(ure)", rule_name="feature_key")
        assert _ != "feat(ure)"

    def test_feature(self):
        # Asserts parsing success
        _ = self.parser.parse("feature", rule_name="feature")
        assert _['key'] == "feature"

        _ = self.parser.parse("+feature", rule_name="feature")
        assert _['key'] == "feature"
        assert _['value'] == "+"

        _ = self.parser.parse("feature=true", rule_name="feature")
        assert _['key'] == "feature"
        assert _['value'] == "true"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("~feature1", rule_name="feature")

        _ = self.parser.parse("feature1,feature2", rule_name="feature")
        assert _['key'] != "feature1,feature2"

        # TODO: the grammar should reject these as incomplete or ambiguous
        _ = self.parser.parse("feature=", rule_name="feature")
        _ = self.parser.parse("+feature=true", rule_name="feature")

    def test_feature_desc(self):
        # Asserts parsing success
        _ = self.parser.parse("[high]", rule_name="feature_desc")
        assert _['feature_desc'][0]['key'] == "high"

        _ = self.parser.parse("[high,rounded]", rule_name="feature_desc")
        assert len(_['feature_desc']) == 2
        assert _['feature_desc'][1]['key'] == "rounded"

        _ = self.parser.parse("*[high,rounded]", rule_name="feature_desc")
        assert _['recons'] == "*"

        _ = self.parser.parse("[+high,-rounded]", rule_name="feature_desc")
        assert _['feature_desc'][0]['value'] == "+"
        assert _['feature_desc'][1]['value'] == "-"

        _ = self.parser.parse("[high=true,rounded=false]", rule_name="feature_desc")
        assert _['feature_desc'][0]['value'] == "true"
        assert _['feature_desc'][1]['value'] == "false"

        # Asserts parsing failure
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[high", rule_name="feature")
        with self.assertRaises(tatsu.exceptions.FailedParse):
            self.parser.parse("[high,]", rule_name="feature")

    def test_segment(self):
        # Asserts parsing success
        _ = self.parser.parse("t", rule_name="segment")
        assert _['expression'][0]['ipa']['ipa'] == "t"

        _ = self.parser.parse("t|s", rule_name="segment")
        assert _['expression'][1]['ipa']['ipa'] == "s"

        _ = self.parser.parse("#", rule_name="segment")
        assert _['expression'][0]['boundary']['boundary'] == "#"

        _ = self.parser.parse("_", rule_name="segment")
        assert _['position'] == "_"

        _ = self.parser.parse(":null:", rule_name="segment")
        assert _['empty'] == ":null:"

        _ = self.parser.parse("[+high,-rounded]", rule_name="segment")
        assert _['feature_desc'][0]['key'] == "high"
        assert _['feature_desc'][1]['value'] == "-"

        _ = self.parser.parse("@1", rule_name="segment")
        assert _['back_ref'] == "1"

        _ = self.parser.parse("{t,s}", rule_name="segment")
        assert len(_['mapper']) == 2
        assert _['mapper'][0]['ipa'] == "t"

        # Note that this does not raise an exception, as we are not
        # capturing a `start`, but only a `sound_class`
        _ = self.parser.parse("t+s", rule_name="segment")
        assert len(_['expression']) != 2

    def test_sequence(self):
        # Asserts parsing success
        _ = self.parser.parse("t", rule_name="sequence")
        assert _['sequence'][0]['expression'][0]['ipa']['ipa'] == "t"

        _ = self.parser.parse("t s", rule_name="sequence")
        assert len(_['sequence']) == 2
        assert _['sequence'][1]['expression'][0]['ipa']['ipa'] == "s"

        _ = self.parser.parse("t|s a _ @1 [+high,-rounded]", rule_name="sequence")
        assert len(_['sequence']) == 4
        assert len(_['sequence'][0]['expression']) == 2
        assert _['sequence'][2]['position'] == "_"

    def test_start(self):
        # Assert parsing success; these are basic tests, the complete
        # ones use the data from the sound change catalog provided
        # with the library
        _ = self.parser.parse("p > b / V _ V", rule_name="start")
        assert "source" in _
        assert "target" in _
        assert "context" in _

        # no context
        _ = self.parser.parse("p -> b")
        assert _['context'] is None

if __name__ == "__main__":
    sys.exit(unittest.main())
