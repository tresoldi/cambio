"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from pathlib import Path

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"

# TODO: drop CLTS as a dependency, read directly from files
# TODO: also, remove duplicates (like  ['ãã', 'ãː'])
# Import 3rd party libraries
from pyclts import CLTS

TRANSCRIPTION = CLTS().bipa

def parse_features(text):
    """
    Parse a list of feature definitions and constraints.

    Constraints can be definied inside optional brackets. Features are
    separated by commas, with optional spaces around them, and have a
    leading plus or minus sign (defaulting to plus).

    Parameters
    ----------
    text: string
        A string with the feature constraints specification

    Returns
    -------
    features : dict
        A dictionary with `positive` features, `negative` features,
        and `custom` features.
    """

    # Remove any brackets from the text that was received and strip it.
    # This allows to generalize this function, so if that it can be used
    # in different contexts (parsing both stuff as "[+fricative]" and
    # "+fricative").
    text = text.replace("[", "")
    text = text.replace("]", "")
    text = text.strip()

    # Analyze all features and build a list of positive and negative
    # features; if a feature is not annotated for positive or negative
    # (i.e., no plus or minus sign), we default to positive.
    # TODO: move the whole thing to regular expressions?
    positive = []
    negative = []
    custom = {}
    for feature in text.split(","):
        # Strip once more, as the user might add spaces next to the commas
        feature = feature.strip()

        # Obtain the positivity/negativity of the feature
        if feature[0] == "-":
            negative.append(feature[1:])
        elif feature[0] == "+":
            positive.append(feature[1:])
        else:
            # If there is no custom value (equal sign), assume it is a positive
            # feature; otherwise, just store in `custom`.
            if "=" in feature:
                feature_name, feature_value = feature.split("=")
                custom[feature_name] = feature_value
            else:
                positive.append(feature)

    return {"positive": positive, "negative": negative, "custom": custom}


# TODO: fix documentation
def features2graphemes(feature_str, transsys=None):
    """
    Returns a list of graphemes matching positive and negative features.
    Positive and negative are lists of features as defined in the
    TranscriptionSystem.

    For example, asking for not-rounded and not high front vowels:

    >>> alteruphono.sound_changer.features2sounds(["vowel", "front"], ["rounded", "high"])
    ['ḭːː', 'aa', 'ɛ̯', 'ĩĩ', 'ĕ', ... 'a˞', 'ẽ̞', 'iːː', 'e̯', 'aː', 'ii']

    Parameters
    ----------
    positive : list
        A list of strings with the features to be included.
    negative : list
        A list of strings with the features for be excluded.
    transsys : TranscriptionSystem
        The transcription system to be used.

    Returns
    -------
    sounds : list
        A list of strings with all the graphemes matching the requested
        feature constraints.
    """

    # TODO: drop CLTS dependency
    if not transsys:
        transsys = TRANSCRIPTION

    # Parse the feature string
    features = parse_features(feature_str)

    # Iterate over all sounds in the transcription system
    sounds = []
    for sound in transsys.sounds:
        # Extract all the features of the current sound
        sound_features = transsys[sound].name.split()

        # Check if all positive features are there
        pos_match = all(feat in sound_features for feat in features["positive"])

        # Check if none of the negative features are there
        neg_match = all(
            feat not in sound_features for feat in features["negative"]
        )

        # Accept the sound if it passes both tests
        if pos_match and neg_match:
            sounds.append(sound)

    # For debugging and development purposes, it is best for the
    # list to be sorted. As we are sorting in any case, it is better to
    # do it in reverse length, so that conversion to regular expressions,
    # if necessary, will be transparent.
    sounds.sort(key=lambda item: (-len(item), item))

    return sounds


# TODO: remove hard-coding of fixes, loading internal or external data
# TODO: this will be part of the removal of pyclts dependency
def fix_descriptors(descriptors):
    """
    Fix inconsistenies and problems with pyclts descriptors.
    """

    # Run manual fixes related to pyclts
    if "palatal" in descriptors and "fricative" in descriptors:
        # Fricative palatals are described as alveolo-palatal in pyclts, so
        # replace all of them
        descriptors = [
            feature if feature != "palatal" else "alveolo-palatal"
            for feature in descriptors
        ]

    if "alveolo-palatal" in descriptors and "fricative" in descriptors:
        # TODO: should check if it is not there already
        descriptors.append("sibilant")

    if "alveolar" in descriptors and "fricative" in descriptors:
        # TODO: should check if it is not there already
        descriptors.append("sibilant")

    return descriptors


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
        "CV"), and corresponding descriptions and list of graphemes
        as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sound_classes.tsv"
        filename = filename.as_posix()

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        sound_classes = {
            row["sound_class"]: {
                "description": row["description"],
                "features": row["features"],
                "graphemes": features2graphemes(row["features"]),
            }
            for row in reader
        }

    return sound_classes


def read_sound_features(filename=None):
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
        filename = RESOURCE_DIR / "features_bipa.tsv"
        filename = filename.as_posix()

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        features = {row["value"]: row["feature"] for row in reader}

    return features


def read_sound_changes(filename=None):
    """
    Read sound changes.

    Sound changes are stored in a TSV file holding a list of sound changes.
    Mandatory fields are, besides a unique `ID`,
    `RULE`, `TEST_ANTE`, and `TEST_POST`.
    A floating-point `WEIGHT` may also be specified
    (defaulting to 1.0 for all rules, unless specified).

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the list of sound changes, defaulting
        to the one provided by the library.

    Returns
    -------
    features : dict
        A dictionary of with IDs as keys and sound changes as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sound_changes.tsv"
        filename = filename.as_posix()

    # Read the raw notation adding leading and trailing spaces to source
    # and target, as well as adding capturing parentheses to source (if
    # necessary) and replacing back-reference notation in targets
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        rules = {}
        for row in reader:
            # TODO: join multiple rules (replacing multisegment)
            rule_id = int(row.pop("ID"))
            row["WEIGHT"] = float(row.get("WEIGHT", 1.0))

            rules[rule_id] = row

    return rules


# TODO: properly document
def read_sounds(featsys, filename=None):
    if not filename:
        filename = RESOURCE_DIR / "sounds.tsv"
        filename = filename.as_posix()

    sounds = {}
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            features = row["NAME"].split()

            # TODO: skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            descriptors = {featsys[feat]: feat for feat in features}
            sounds[row["GRAPHEME"]] = descriptors

    return sounds


# TODO: properly document
def read_phonetic_data():
    features = read_sound_features()
    sound_classes = read_sound_classes()
    sounds = read_sounds(features)

    data = {"features": features, "classes": sound_classes, "sounds": sounds}

    return data
