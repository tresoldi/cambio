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
import maniphono


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
            ): "# b a ɸ a sʼ[-ejective] a #",  # TODO: fix with maniphono?
            ("p|t a @1|k > p a t", "t a k"): "# p a t #",
        }

        for test, ref in reference.items():
            rule = alteruphono.Rule(test[0])
            ante = maniphono.parse_sequence(test[1], boundaries=True)
            post = maniphono.parse_sequence(ref, boundaries=True)
            fw = alteruphono.forward(ante, rule)
            fw_str = " ".join([str(v) for v in fw])
            assert fw_str == str(post)

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
        for test, ref in reference.items():
            rule = alteruphono.Rule(test[0])
            # ante = [alteruphono.parse_seq_as_rule(str(r)) for r in ref]
            post = maniphono.parse_sequence(test[1], boundaries=True)

            bw = alteruphono.backward(post, rule)
            bw_strs = tuple([str(b) for b in bw])

            assert bw_strs == ref

    # def test_forward_resources(self):
    #     sound_changes = alteruphono.utils.read_sound_changes()
    #
    #     parser = alteruphono.Parser()
    #     model = alteruphono.Model()
    #     for change_id, change in sorted(sound_changes.items()):
    #         rule = make_rule(change["RULE"], parser)
    #
    #         test_post = Sequence(change["TEST_POST"])
    #         post_seq = model.forward(change["TEST_ANTE"], rule)
    #
    #         assert post_seq == test_post
    #

    #
    # def test_backward_resources(self):
    #     sound_changes = alteruphono.utils.read_sound_changes()
    #
    #     parser = alteruphono.Parser()
    #     seq_parser = alteruphono.parser.Parser(root_rule="sequence")
    #     model = alteruphono.Model()
    #     for change_id, change in sorted(sound_changes.items()):
    #         rule = make_rule(change["RULE"], parser)
    #
    #         test_ante = Sequence(change["TEST_ANTE"])
    #
    #         ante_seqs = tuple(
    #             [str(seq) for seq in model.backward(change["TEST_POST"], rule)]
    #         )
    #
    #         # TODO: inspect all options returned, including
    #         # ('# a k u n #', '# a k u p|t|k θ #'
    #         ante_asts = [seq_parser(seq) for seq in ante_seqs]
    #         matches = [model.check_match(test_ante, ante_ast) for ante_ast in ante_asts]
    #
    #         assert any(matches)


if __name__ == "__main__":
    # Explicitly creating and running a test suite allows to profile
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangers)
    unittest.TextTestRunner(verbosity=2).run(suite)
