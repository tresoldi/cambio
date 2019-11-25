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

    def test_parse_features(self):
        # define tests and references
        reference = {
            "feat1": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[feat1]": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[+feat1]": {"positive": ("feat1",), "negative": (), "custom": ()},
            "[-feat1]": {"positive": (), "negative": ("feat1",), "custom": ()},
            "[feat1,+feat2,-feat3]": {
                "positive": ("feat1", "feat2"),
                "negative": ("feat3",),
                "custom": (),
            },
            "[feat1,-feat2,feat3=value,+feat4]": {
                "positive": ("feat1", "feat4"),
                "negative": ("feat2",),
                "custom": (("feat3", "value"),),
            },
        }

        for feat_str, ref in reference.items():
            ret = alteruphono.utils.parse_features(feat_str)
            assert tuple(ret["positive"]) == ref["positive"]
            assert tuple(ret["negative"]) == ref["negative"]
            assert tuple(sorted(ret["custom"].items())) == ref["custom"]

    def test_features2graphemes(self):
        # using default features
        reference = {
            "vowel,open,front,unrounded": (
                "ãã",
                "a̰ːː",
                "ãː",
                "aa",
                "aː",
                "aˑ",
                "a˞",
                "ã",
                "ă",
                "ḁ",
                "a̯",
                "a̰",
                "a",
            ),
            "stop,voiceless,long,-alveolar": (
                "t̪ʰː",
                "t̪ːʰ",
                "kʷː",
                "pʰː",
                "pːʰ",
                "t̪ː",
                "ʈʰː",
                "ʈːʰ",
                "cː",
                "kː",
                "pː",
            ),
            "rounded,unrounded": (),
        }

        for feat_str, ref in reference.items():
            ret = alteruphono.utils.features2graphemes(feat_str)
            assert tuple(ret) == ref

    def test_read_sound_classes(self):
        # using default
        sc = alteruphono.utils.read_sound_classes()

        assert len(sc) == 20
        assert sc["K"]["features"] == "velar"
        assert sc["VN"]["description"] == "nasal vowel"
        assert sc["XXX"]["graphemes"] == ["ãã", "ãː", "aa", "aː"]

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
