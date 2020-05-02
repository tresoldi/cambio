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


class TestParser(unittest.TestCase):
    """
    Class for `alteruphono` tests related to parsers.
    """

    def test_parse(self):
        # Read phonetic data
        alteruphono.utils.read_phonetic_model()

        reference = {
            "p > b": {
                "ante": [(("ipa", "p"), ("modifier", None))],
                "post": [(("ipa", "b"), ("modifier", None))],
            },
            "p|t r > @1[+voiced] / V _": {
                "ante": [
                    (("modifier", None), ("sound_class", "V")),
                    (
                        (
                            "alternative",
                            [
                                {"ipa": "p", "modifier": None},
                                {"ipa": "t", "modifier": None},
                            ],
                        ),
                    ),
                    (("ipa", "r"), ("modifier", None)),
                ],
                "post": [
                    (("back-reference", 1),),
                    (("back-reference", 2), ("modifier", "[+voiced]")),
                ],
            },
        }

        for rule, ref in reference.items():
            ret = alteruphono.parse(rule)
            ret_ante = [tuple(sorted(token.items())) for token in ret["ante"]]
            ret_post = [tuple(sorted(token.items())) for token in ret["post"]]

            assert tuple(ref["ante"]) == tuple(ret_ante)
            assert tuple(ref["post"]) == tuple(ret_post)

    def test_parse_features(self):
        # define tests and references
        reference = {
            "feat1": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[feat1]": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[+feat1]": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[-feat1]": {"positive": (), "negative": ("feat1",), "custom": ()},
            "[feat1,+feat2,-feat3]": {
                "positive": ("feat1", "feat2"),
                "negative": ("feat3",),
                "custom": (),
            },
            "[feat1,-feat2,feat3=value,+feat4]": {
                "positive": ("feat1", "feat4"),
                "negative": ("feat2",),
                "custom": (("feat3", "value"),),
            },
        }

        for feat_str, ref in reference.items():
            ret = alteruphono.parser.parse_features(feat_str)
            assert tuple(ret["positive"]) == ref["positive"]
            assert tuple(ret["negative"]) == ref["negative"]
            assert tuple(sorted(ret["custom"].items())) == ref["custom"]


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)
