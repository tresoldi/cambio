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
from alteruphono import (
    BoundaryToken,
    FocusToken,
    EmptyToken,
    BackRefToken,
    ChoiceToken,
    SetToken,
    SegmentToken,
)


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
                "ante": (SegmentToken("p"), SegmentToken("V")),
                "post": (SegmentToken("b"), BackRefToken(1)),
            },
            {
                "rule": "p > b",
                "ante": (SegmentToken("p"),),
                "post": (SegmentToken("b"),),
            },
        ]

        for test in tests:
            ante, post = alteruphono.parse_rule(test["rule"])
            assert tuple(ante) == test["ante"]
            assert tuple(post) == test["post"]


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParser)
    unittest.TextTestRunner(verbosity=2).run(suite)
