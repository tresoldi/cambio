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
        ast = parser.parse("p > b")
        fw = forward.compile(ast)

        v = alteruphono.apply_forward("# p a #", fw[0], fw[1])

        # TODO: check for resources later
        return v

        filename = alteruphono.utils.RESOURCE_DIR / "sound_changes.tsv"
        with open(filename.as_posix()) as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            for row in reader:
                # TODO: fix issue with segmentation
                if "d+" in row["rule"]:
                    continue
                if "n+" in row["rule"]:
                    continue
                if "i+" in row["rule"]:
                    continue
                if "h+" in row["rule"]:
                    continue
                if "C+" in row["rule"]:
                    continue

                # load source and target reference for this test
                ref_source, ref_target = row["test"].split(" / ")
                ref_source = "# %s #" % ref_source.strip()
                ref_target = "# %s #" % ref_target.strip()

                # Build ast, get fw replacements, and test
                ast = parser.parse(row["rule"])
                fw = forward.compile(ast)
                target = alteruphono.apply_forward(ref_source, fw[0], fw[1])

#                if ref_target == target:
#                    print([ref_target, target], row["rule"], fw, ref_source)
#                    print()

    def test_backward(self):
        # Load the Parser
        parser = alteruphono.Parser(parseinfo=False)

        # Load sound changes and build the compiler
        SOUND_CLASSES = alteruphono.utils.read_sound_classes()
        backward = alteruphono.BackwardAutomata(SOUND_CLASSES)

        # Test rules
        ast = parser.parse("C > b / _ r")
        bw = backward.compile(ast)

        print(bw)
        m = alteruphono.apply_backward("# b r a b i b r e #", bw[0], bw[1])
        print(m)


if __name__ == "__main__":
    unittest.main()
