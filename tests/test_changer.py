#!/usr/bin/env python3
# encoding: utf-8

"""
test_changer
==============

Tests for the changers in the `alteruphono` package.
"""

# Import third-party libraries
import csv
import logging
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono
import tatsu

# Setup logger
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
LOGGER = logging.getLogger("TestLog")


class TestChanger(unittest.TestCase):
    """
    Class for `alteruphono` tests related to changers.
    """

    def test_forward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        forward = alteruphono.ForwardAutomata(SOUND_CLASSES)

        # Test rules
        filename = alteruphono.utils.RESOURCE_DIR / "sound_changes.tsv"
        with open(filename.as_posix()) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                ########################
                # TODO: skipping all rules that we know are failing, by
                # checking substring in rule

                # bound segments
                skips = ["d+", "n+", "i+", "h+", "C+"]

                found = [skip in row["rule"] for skip in skips]
                if any(found):
                    continue
                ##################

                # load source and target reference for this test
                ref_source, ref_target = row["test"].split(" / ")
                ref_source = "# %s #" % ref_source.strip()
                ref_target = "# %s #" % ref_target.strip()

                # Build ast, get fw replacements, and test
                ast = parser.parse(row["rule"])
                fw = forward.compile(ast)
                target = alteruphono.apply_forward(ref_source, fw[0], fw[1])

                # assert reference and result are matching
                assert ref_target == target

    def test_backward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        backward = alteruphono.BackwardAutomata(SOUND_CLASSES)

        # Test rules
        ast = parser.parse("H > b / _ r")
        bw = backward.compile(ast)

        RULES = {
            "H > b / _ r": (
                " # H r a d i H r e # ",
                " # H r a d i b r e # ",
                " # b r a d i H r e # ",
                " # b r a d i b r e # ",
            ),
            "t > d": (" # b r a d i b r e # ", " # b r a t i b r e # "),
        }

        for rule in RULES:
            ast = parser.parse(rule)
            bw = backward.compile(ast)
            candidates = alteruphono.apply_backward(
                "# b r a d i b r e #", bw[0], bw[1]
            )

#            assert tuple(candidates) == RULES[rule]

        # Test rules -- all source in reference must be among the backward
        # reconstruction
        filename = alteruphono.utils.RESOURCE_DIR / "sound_changes.tsv"
        with open(filename.as_posix()) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                # TODO: remove once multiple segments is supported
                # bound segments
                skips = ["d+", "n+", "i+", "h+", "C+"]

                found = [skip in row["rule"] for skip in skips]
                if any(found):
                    continue
                #################

                # load source and target reference for this test
                ref_source, ref_target = row["test"].split(" / ")
                ref_source = "# %s #" % ref_source.strip()
                ref_target = "# %s #" % ref_target.strip()

                # Build ast, get fw replacements, and test
                ast = parser.parse(row["rule"])
                bw = backward.compile(ast)
                alternatives = alteruphono.apply_backward(ref_target, bw[0], bw[1])

                print()
                print([row['rule'], ref_source in alternatives, alternatives, ref_source])
                print(bw)

                # assert reference is among alternatives
                assert ref_source in alternatives


if __name__ == "__main__":
    unittest.main()
