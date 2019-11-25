#!/usr/bin/env python3

"""
test_utils
==========

Tests for the utility functions in the `alteruphono` package.
"""

# Import third-party libraries
import sys
import unittest

# Import the library being test and auxiliary libraries
import alteruphono


class TestUtils(unittest.TestCase):
    """
    Class for `alteruphono` tests related to utility functions.
    """

    def test_features2graphemes(self):
        # using default features
        reference = {
            "vowel,open,front,unrounded,-nasalized,-long,-short": (
                "âˑ̠",
                "a̰ːː",
                "aˑ̟",
                "aˑ̠",
                "a˞ˤ",
                "a˞̟",
                "âˑ",
                "â̠",
                "a̘ˠ",
                "a̙ˠ",
                "a̝ˑ",
                "a̞ˑ",
                "a̤ˑ",
                "a̤ˠ",
                "a̤ˤ",
                "ä̤",
                "ḁˠ",
                "ḁˤ",
                "ḁ̤",
                "ḁ̯",
                "a̰ˑ",
                "a̰ˠ",
                "a̰ˤ",
                "a̹ˑ",
                "aˀ",
                "aˑ",
                "a˞",
                "aˠ",
                "aˤ",
                "â",
                "ā",
                "ă",
                "ä",
                "a̘",
                "a̙",
                "a̝",
                "a̞",
                "a̟",
                "a̠",
                "a̤",
                "ḁ",
                "a̯",
                "a̰",
                "a",
            ),
            "stop,voiceless,long,alveolar,-ejective,-labialized": (
                "tʲʰː",
                "tˀˡː",
                "t̩ʲː",
                "t̻ʰː",
                "tʰː",
                "tʲː",
                "tˠː",
                "tˡː",
                "tˤː",
                "t̩ː",
                "t̻ː",
                "t͈ː",
                "ʰtː",
                "tː",
            ),
            "rounded,unrounded": (),
        }

        features = alteruphono.utils.read_sound_features()
        sounds = alteruphono.utils.read_sounds(features)
        for feat_str, ref in reference.items():
            ret = alteruphono.utils.features2graphemes(feat_str, sounds)
            assert tuple(ret) == ref

    def test_read_sound_classes(self):
        # using default
        sc = alteruphono.utils.read_sound_classes()

        assert len(sc) == 20
        assert sc["K"]["features"] == "velar"
        assert sc["VN"]["description"] == "nasal vowel"
        assert sc["XXX"]["graphemes"] == None

    def test_read_sound_features(self):
        # using default
        feats = alteruphono.utils.read_sound_features()

        assert len(feats) == 130
        assert len(set(feats.values())) == 40
        assert feats["labialized"] == "labialization"

    def test_read_sounds(self):
        # using default
        features = alteruphono.utils.read_sound_features()

        sounds = alteruphono.utils.read_sounds(features)
        assert len(sounds) == 7356
        assert tuple(sorted(sounds["a"].items())) == (
            ("centrality", "front"),
            ("height", "open"),
            ("roundedness", "unrounded"),
            ("type", "vowel"),
        )

    def test_read_sound_changes(self):
        # using default
        changes = alteruphono.utils.read_sound_changes()

        assert len(changes) == 800
        assert changes[13]["RULE"] == "N v|k|s -> n @2"
        assert changes[13]["WEIGHT"] == 1.0
        assert changes[13]["TEST_POST"] == "i m l i n k o"
        assert changes[13]["TEST_ANTE"] == "i m l i m k o"


if __name__ == "__main__":
    sys.exit(unittest.main())
