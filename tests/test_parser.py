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
                "ante": [alteruphono.parser.TokenIPA("p")],
                "post": [alteruphono.parser.TokenIPA("b")],
            },
            "p|t r > @1[+voiced] / V _": {
                "ante": [
                    alteruphono.parser.TokenSoundClass("V"),
                    alteruphono.parser.TokenAlternative(
                        [
                            alteruphono.parser.TokenIPA("p"),
                            alteruphono.parser.TokenIPA("t"),
                        ]
                    ),
                    alteruphono.parser.TokenIPA("r"),
                ],
                "post": [
                    alteruphono.parser.TokenBackRef(1),
                    alteruphono.parser.TokenBackRef(2, "[+voiced]"),
                ],
            },
        }

        for rule, ref in reference.items():
            ret = alteruphono.Rule(rule)

            assert len(ref["ante"]) == len(ret.ante)
            for ref_ante_tok, ret_ante_tok in zip(ref["ante"], ret.ante):
                assert ref_ante_tok == ret_ante_tok

            assert len(ref["post"]) == len(ret.post)
            for ref_post_tok, ret_post_tok in zip(ref["post"], ret.post):
                assert ref_post_tok == ret_post_tok

    def test_parse_features(self):
        # define tests and references
        reference = {
            "feat1": alteruphono.parser.Features(
                positive=["feat1"], negative=[]
            ),
            "[feat1]": alteruphono.parser.Features(
                positive=["feat1"], negative=[]
            ),
            "[+feat1]": alteruphono.parser.Features(
                positive=["feat1"], negative=[]
            ),
            "[-feat1]": alteruphono.parser.Features(
                positive=[], negative=["feat1"]
            ),
            "[feat1,+feat2,-feat3]": alteruphono.parser.Features(
                positive=["feat1", "feat2"], negative=["feat3"]
            ),
            "[feat1,-feat2,feat3=value,+feat4]": alteruphono.parser.Features(
                positive=["feat1", "feat4"],
                negative=["feat2"],
                custom={"feat3": "value"},
            ),
        }

        for feat_str, ref in reference.items():
            ret = alteruphono.parser.parse_features(feat_str)

            assert ret == ref


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)
