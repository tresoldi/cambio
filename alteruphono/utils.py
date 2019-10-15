# encoding: utf-8

# Standard imports
import csv
from os import path
import re

# Import from namespace
from . import sound_changer

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
_RESOURCE_DIR = path.join(path.dirname(path.dirname(__file__)), "resources")

# TODO: use logging


def read_sound_classes(filename=None):
    """
    Read sound class definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound class definition, defaulting
        to the one provided with the library.

    Returns
    -------
    sound_classes : dict
        A dictionary with sound class names as keys (such as "A" or
        "C[+voiced]") and corresponding regular expressions as values.
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
    Read sound feature definitions.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the sound feature definition, defaulting
        to the one provided with the library and based on the BIPA
        transcription system.

    Returns
    -------
    features : dict
        A dictionary with feature values (such as "devoiced") as keys and
        feature classes (such as "voicing") as values.
    """

    if not filename:
        filename = path.join(_RESOURCE_DIR, "features_bipa.tsv")

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        features = {row["value"]: row["feature"] for row in reader}

    return features


# TODO: add support for weight and examples
# TODO: support for id?
# TODO: document this format
# TODO: add support to the PEG grammar format
def read_sound_changes(filename=None):
    """
    Read sound changes.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the list of sound changes, defaulting
        to the one provided by the library. Mandatory fields are `source` and
        `target`.

    Returns
    -------
    features : list
        A list of dictionaries, with each item representing a sound change.
    """

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
