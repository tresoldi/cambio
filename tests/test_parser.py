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
from alteruphono.old_parser import *


class TestParser(unittest.TestCase):
    """
    Class for `alteruphono` tests related to parsers.
    """

    def test_dummy(self):
        assert 1 == 1

a = """

    def test_parse(self):
        reference = {
            "p > b": {"ante": [TokenIPA("p")], "post": [TokenIPA("b")]},
            "p|t r > @1[+voiced] / V _": {
                "ante": [
                    TokenSoundClass("V"),
                    TokenAlternative([TokenIPA("p"), TokenIPA("t")]),
                    TokenIPA("r"),
                ],
                "post": [TokenBackRef(1), TokenBackRef(2, "[+voiced]")],
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
            "feat1": Features(positive=["feat1"], negative=[]),
            "[feat1]": Features(positive=["feat1"], negative=[]),
            "[+feat1]": Features(positive=["feat1"], negative=[]),
            "[-feat1]": Features(positive=[], negative=["feat1"]),
            "[feat1,+feat2,-feat3]": Features(
                positive=["feat1", "feat2"], negative=["feat3"]
            ),
            "[feat1,-feat2,feat3=value,+feat4]": Features(
                positive=["feat1", "feat4"],
                negative=["feat2"],
                custom={"feat3": "value"},
            ),
        }

        for feat_str, ref in reference.items():
            ret = alteruphono.old_parser.parse_features(feat_str)

            assert ret == ref
"""

if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)
