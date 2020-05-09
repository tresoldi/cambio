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
from alteruphono.old_parser import _tokens2ast
from alteruphono.sequence import Sequence
from alteruphono.ast import *

# TODO: could read the phonetic data a single time?


class TestChangers(unittest.TestCase):
    """
    Class for `alteruphono` tests related to changers.
    """

    def test_forward_hardcoded(self):
        reference = {
            ("p > b", "# p a p a #"): "# b a b a #",
            ("S > p / _ V", "t i s e"): "# p i s e #",
            ("t[voiced] > s", "t a d a"): "# t a s a #",
            (
                "S[voiceless] a > @1[fricative] a",
                "b a p a t a",
            ): "# b a ɸ a s a #",
            ("p|t a @1|k > p a t", "t a k"): "# p a t #",
#            ("p|d a > @1{b,d} e", "d a p a"): "# d e b e #",
        }

        # test with Model object
        parser = alteruphono.parser.Parser()
        model = alteruphono.Model()
        for test, ref in reference.items():
            rule = alteruphono.Rule(test[0], parser(test[0]))

            ante_seq = test[1].split()
            post_seq = model.forward(ante_seq, rule)

            assert str(post_seq) == ref

    def test_forward_resources(self):
        sound_changes = alteruphono.utils.read_sound_changes()

        parser = alteruphono.parser.Parser()
        model = alteruphono.Model()
        for change_id, change in sorted(sound_changes.items()):
            rule = alteruphono.Rule(change["RULE"], parser(change['RULE']))

            test_ante = change["TEST_ANTE"].split()
            test_post = Sequence(change["TEST_POST"])
            post_seq = model.forward(test_ante, rule)

            assert post_seq == test_post

    def test_backward_hardcoded(self):
        reference = {
            ("p V > b a", "b a r b a"): (
                "# b a r b a #",
                "# b a r p V #",
                "# p V r b a #",
                "# p V r p V #",
            )
        }

        # test with Model object
        parser = alteruphono.parser.Parser()
        model = alteruphono.Model()
        for test, ref in reference.items():
            rule = alteruphono.Rule(test[0], parser(test[0]))

            post_seq = test[1].split()

            ante_seqs = tuple(
                [str(seq) for seq in model.backward(post_seq, rule)]
            )

            assert tuple(ante_seqs) == ref

    def test_backward_resources(self):
        sound_changes = alteruphono.utils.read_sound_changes()

        parser = alteruphono.parser.Parser()
        seq_parser = alteruphono.parser.Parser(root_rule="sequence")
        model = alteruphono.Model()
        for change_id, change in sorted(sound_changes.items()):
            rule = alteruphono.Rule(change["RULE"], parser(change['RULE']))

            test_ante = Sequence(change["TEST_ANTE"])
            test_post = change["TEST_POST"].split()

            ante_seqs = tuple(
                [str(seq) for seq in model.backward(test_post, rule)]
            )

            # TODO: inspect all options returned, including ('# a k u n #', '# a k u p|t|k θ #'

#            for seq in ante_seqs:
#                print([seq])
#                print(seq_parser(seq))

#            ante_asts = [
#                alteruphono.parser._tokens2ast(seq.split(" "))
#                for seq in ante_seqs
#            ]
#            matches = [
#                model.check_match(test_ante, ante_ast) for ante_ast in ante_asts
#            ]
#
#            assert any(matches)


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangers)
    unittest.TextTestRunner(verbosity=2).run(suite)
