#!/usr/bin/env python3

"""
test_parser
===========

Tests for the parser in the `alteruphono` package.
"""

# Import third-party libraries
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono

# TODO: add failing parses
# TODO: add negation tests


class TestParser(unittest.TestCase):
    """
    Class for `alteruphono` tests related to parsers.
    """

    def test_parse_rule(self):
        tests = [
            {
                "rule": "p > b / _ V",
                "ast": "{'ante': [{'grapheme': 'p'}, {'sound_class': 'V', 'negation': False}], 'post': [{'grapheme': 'b'}, {'backref': 1}]}",
            },
            {
                "rule": "p > b",
                "ast": "{'ante': [{'grapheme': 'p'}], 'post': [{'grapheme': 'b'}]}",
            },
        ]

        parser = alteruphono.Parser(root_rule="rule")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_sequence(self):
        tests = [
            {"rule": "a", "ast": "[{'grapheme': 'a'}]"},
            {
                "rule": "a b ɚ",
                "ast": "[{'grapheme': 'a'}, {'grapheme': 'b'}, {'grapheme': 'ɚ'}]",
            },
            {
                "rule": "a V p|b @1 @2[+stop] :null:",
                "ast": "[{'grapheme': 'a'}, {'sound_class': 'V', 'negation': False}, {'choice': [{'grapheme': 'p'}, {'grapheme': 'b'}]}, {'backref': 0}, {'backref': 1, 'modifier': {'positive': ['stop'], 'negative': [], 'custom': []}}, {'empty': ':null:'}]",
            },
        ]

        parser = alteruphono.Parser(root_rule="sequence")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_segment(self):
        tests = [
            {"rule": "ɚ", "ast": "{'grapheme': 'ɚ'}"},
            {
                "rule": "p|b",
                "ast": "{'choice': [{'grapheme': 'p'}, {'grapheme': 'b'}]}",
            },
            {"rule": "#", "ast": "{'boundary': '#'}"},
            {"rule": "@3", "ast": "{'backref': 2}"},
            {
                "rule": "VCLSSTP",
                "ast": "{'sound_class': 'VCLSSTP', 'negation': False}",
            },
            {"rule": "0", "ast": "{'empty': '0'}"},
        ]

        parser = alteruphono.Parser(root_rule="segment")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_choice(self):
        tests = [
            {
                "rule": "p|b",
                "ast": "{'choice': [{'grapheme': 'p'}, {'grapheme': 'b'}]}",
            },
            {
                "rule": "p|b|0",
                "ast": "{'choice': [{'grapheme': 'p'}, {'grapheme': 'b'}, {'empty': '0'}]}",
            },
            {
                "rule": "p|0|#|@1",
                "ast": "{'choice': [{'grapheme': 'p'}, {'empty': '0'}, {'boundary': '#'}, {'backref': 0}]}",
            },
        ]

        parser = alteruphono.Parser(root_rule="choice")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_sound_class(self):
        tests = [
            {"rule": "C", "ast": "{'sound_class': 'C', 'negation': False}"},
            {"rule": "CS", "ast": "{'sound_class': 'CS', 'negation': False}"},
            {"rule": "H1", "ast": "{'sound_class': 'H1', 'negation': False}"},
            {
                "rule": "C[+voiced]",
                "ast": "{'sound_class': 'C', 'modifier': {'positive': ['voiced'], 'negative': [], 'custom': []}, 'negation': False}",
            },
            {"rule": "H_X", "ast": "{'sound_class': 'H_X', 'negation': False}"},
        ]

        parser = alteruphono.Parser(root_rule="sound_class")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_backref(self):
        tests = [
            {"rule": "@1", "ast": "{'backref': 0}"},
            {
                "rule": "@3[-nasal]",
                "ast": "{'backref': 2, 'modifier': {'positive': [], 'negative': ['nasal'], 'custom': []}}",
            },
        ]

        parser = alteruphono.Parser(root_rule="backref")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_grapheme(self):
        tests = [
            {"rule": "tʃ", "ast": "{'grapheme': 'tʃ'}"},
            {"rule": "kʰʷ", "ast": "{'grapheme': 'kʰʷ'}"},
            {
                "rule": "tʃ[+voiced]",
                "ast": "{'grapheme': 'tʃ', 'modifier': {'positive': ['voiced'], 'negative': [], 'custom': []}}",
            },
        ]

        parser = alteruphono.Parser(root_rule="grapheme")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_feature_key(self):
        tests = [
            {"rule": "voiced", "ast": "voiced"},
            {"rule": "tier03", "ast": "tier03"},
        ]

        parser = alteruphono.Parser(root_rule="feature_key")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_op_feature(self):
        tests = [
            {"rule": "voiced", "ast": "{'feature': 'voiced', 'value': '+'}"},
            {"rule": "+voiced", "ast": "{'feature': 'voiced', 'value': '+'}"},
            {"rule": "-voiced", "ast": "{'feature': 'voiced', 'value': '-'}"},
        ]

        parser = alteruphono.Parser(root_rule="op_feature")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_feature_val(self):
        tests = [
            {
                "rule": "voiced=true",
                "ast": "{'feature': 'voiced', 'value': '+'}",
            }
        ]

        parser = alteruphono.Parser(root_rule="feature_val")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]

    def test_parse_modifier(self):
        tests = [
            {
                "rule": "[+voiced]",
                "ast": "{'positive': ['voiced'], 'negative': [], 'custom': []}",
            },
            {
                "rule": "[feat1,-feat2,feat=true]",
                "ast": "{'positive': ['feat', 'feat1'], 'negative': ['feat2'], 'custom': []}",
            },
        ]

        parser = alteruphono.Parser(root_rule="modifier")
        for test in tests:
            # print(test, "---", '"%s"' % str(parser(test['rule'])))
            assert str(parser(test["rule"])) == test["ast"]


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)
