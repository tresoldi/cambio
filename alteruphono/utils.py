# encoding: utf-8

# Standard imports
import csv
from os import path
import re

from alteruphono import sound_changer

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
_RESOURCE_DIR = path.join(path.dirname(path.dirname(__file__)), "resources")

# TODO: use logging


def read_sound_classes(filename=None):
    """
    Read sound class definitions.
    """

    if not filename:
        filename = path.join(_RESOURCE_DIR, "sound_classes.tsv")

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        sound_classes = {
            row["sound_class"]: sound_changer.features2regex(
                *sound_changer.parse_features(row["features"])
            )
            for row in reader
        }

    return sound_classes


# TODO: rename to sound features
def read_features(filename=None):
    """
    Read feature definitions.
    """

    if not filename:
        filename = path.join(_RESOURCE_DIR, "features_bipa.tsv")

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        features = {row["value"]: row["feature"] for row in reader}

    return features


# TODO: add support for weight and examples
# TODO: move to named tuple?
def read_sound_changes(filename=None):
    if not filename:
        filename = path.join(_RESOURCE_DIR, "sound_changes.tsv")

    # Read the raw notation adding leading and trailing spaces to source
    # and target, as well as adding capturing parentheses to source (if
    # necessary) and replacing back-reference notation in targets
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        rules = []
        for row in reader:
            source = " %s " % " ".join(
                [
                    "(%s)" % tok if "(" not in tok else tok
                    for tok in row["source"].split()
                ]
            )

            target = " %s " % row["target"].replace("@", "\\")

            rules.append(
                {
                    "source": re.sub("\s+", " ", source),
                    "target": re.sub("\s+", " ", target),
                }
            )

    return rules


# TODO: make a default dict defaulting to the lowest freq
# (or maybe even do a smoothing)
def read_segment_freq(filename=None):
    """
    Returns global frequency distribution for segments.

    This is used in the generation as a starting point for the per-language
    segment frequency, so that results are more "natural".
    """

    if not filename:
        filename = path.join(_RESOURCE_DIR, "segment_freq.tsv")

    freqs = {}
    # TODO: incorporate in enki_data
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for line in reader:
            freqs[line["grapheme"]] = float(line["frequency"])

    return freqs
