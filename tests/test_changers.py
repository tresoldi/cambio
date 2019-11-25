#!/usr/bin/env python3

"""
test_changers
=============

Tests for the changers in the `alteruphono` package.
"""

# Import third-party libraries
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono


class TestChangers(unittest.TestCase):
    """
    Class for `alteruphono` tests related to changers.
    """

    def test_forward_hardcoded(self):
        reference = {
            ("p > b", "# p a p a #"): ("#", "b", "a", "b", "a", "#"),
            ("S > p / _ V", "t i s e"): ("p", "i", "s", "e"),
            ("t[voiced] > s", "t a d a"): ("t", "a", "s", "a"),
        }

        # Read phonetic data
        phdata = alteruphono.utils.read_phonetic_data()

        # Run tests
        for test, ref in reference.items():
            ast = alteruphono.parse(test[0], phdata)
            ante_seq = test[1].split()
            post_seq = alteruphono.forward(ante_seq, ast, phdata)
            assert tuple(post_seq) == ref

    def test_forward_resources(self):
        # Read phonetic data
        phdata = alteruphono.utils.read_phonetic_data()
        sound_changes = alteruphono.utils.read_sound_changes()

        for change_id, change in sorted(sound_changes.items()):
            ast = alteruphono.parse(change["RULE"], phdata)
            test_ante = change["TEST_ANTE"].split()
            test_post = change["TEST_POST"].split()
            post_seq = alteruphono.forward(test_ante, ast, phdata)

            if tuple(test_post) != tuple(post_seq):
                print()
                print(change_id, change["RULE"])
                print("TEST", test_ante)
                print("TEST", test_post)
                print("MINE", post_seq)


if __name__ == "__main__":
    sys.exit(unittest.main())
