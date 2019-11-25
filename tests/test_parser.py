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
        phdata = alteruphono.utils.read_phonetic_data()

        reference = {
            "p > b": {"ante": [(("ipa", "p"),)], "post": [(("ipa", "b"),)]},
            "p|t r > @1[+voiced] / V _": {
                "ante": [
                    (("modifier", None), ("sound_class", "V")),
                    (("alternative", [{"ipa": "p"}, {"ipa": "t"}]),),
                    (("ipa", "r"),),
                ],
                "post": [
                    (("back-reference", 1),),
                    (("back-reference", 2), ("modifier", "[+voiced]")),
                ],
            },
        }

        for rule, ref in reference.items():
            ret = alteruphono.parse(rule, phdata)
            ret_ante = [tuple(sorted(token.items())) for token in ret["ante"]]
            ret_post = [tuple(sorted(token.items())) for token in ret["post"]]

            assert tuple(ref["ante"]) == tuple(ret_ante)
            assert tuple(ref["post"]) == tuple(ret_post)


if __name__ == "__main__":
    sys.exit(unittest.main())
