"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from pathlib import Path

# Import from other modules
from .parser import parse_features

# TODO: drop CLTS as a dependency, read directly from files
# Import 3rd party libraries
from pyclts import CLTS

TRANSCRIPTION = CLTS().bipa

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"


def descriptors2grapheme(descriptors, phdata):
    # Run manual fixes related to pyclts
    if "palatal" in descriptors and "fricative" in descriptors:
        # Fricative palatals are described as alveolo-palatal in pyclts, so
        # replace all of them
        descriptors = [
            feature if feature != "palatal" else "alveolo-palatal"
            for feature in descriptors
        ]

    if "alveolo-palatal" in descriptors and "fricative" in descriptors:
        if "sibilant" not in descriptors:
            descriptors.append("sibilant")

    if "alveolar" in descriptors and "fricative" in descriptors:
        if "sibilant" not in descriptors:
            descriptors.append("sibilant")

    # TODO: should cache this?
    desc = tuple(sorted(descriptors[:]))
    for sound, feat_dict in phdata["sounds"].items():
        # Collect all features and confirm if all are there
        features = tuple(sorted(feat_dict.values()))
        if desc == features:
            return sound

    # TODO: fixes in case we missed
    if "breathy" in desc:
        new_desc = [v for v in desc if v != "breathy"]
        new_gr = descriptors2grapheme(new_desc, phdata)
        if new_gr:
            return "%s[breathy]" % new_gr

    if "long" in desc:
        new_desc = [v for v in desc if v != "long"]
        new_gr = descriptors2grapheme(new_desc, phdata)
        if new_gr:
            return "%sː" % new_gr

    return None


# TODO: add support/code/example for custom features
def features2graphemes(feature_str, transsys=None):
    """
    Returns a list of graphemes matching a feature description.

    Graphemes are returned according to their definition in the transcription
    system in use. The list of graphemes is sorted first by inverse length
    and then alphabetically, so that it can conveniently be mapped to
    regular expressions.

    For example, asking for not-rounded and not high front vowels:

    >>> alteruphono.utils.features2graphemes("[vowel,front,-rounded,-high]")
    ['ẽ̞ẽ̞', 'ãã', 'a̰ːː', 'ẽẽ', 'e̞e̞', ... 'a', 'e', 'i', 'æ', 'ɛ']

    Parameters
    ----------
    feature_str : string
        A string with the description of feature constraints.
    transsys : TranscriptionSystem
        The transcription system to be used. Defaults to BIPA.

    Returns
    -------
    sounds : list
        A sorted list of all the graphemes matching the requested feature
        constraints.
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

    # Sort the list, first by inverse length, then alphabetically
    sounds.sort(key=lambda item: (-len(item), item))

    return sounds


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


def read_sounds(featsys, filename=None):
    """
    Read sound definitions.

    Parameters
    ----------
    featsys : dict
        The feature system to be used.

    filename : string
        Path to the TSV file holding the sound definition, defaulting
        to the one provided with the library and based on the BIPA
        transcription system.

    Returns
    -------
    sounds : dict
        A dictionary with graphemes (such as "a") as keys and
        feature definitions as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sounds.tsv"
        filename = filename.as_posix()

    sounds = {}
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        for row in reader:
            features = row["NAME"].split()

            # NOTE: currently skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            descriptors = {featsys[feat]: feat for feat in features}
            sounds[row["GRAPHEME"]] = descriptors

    return sounds


def read_phonetic_data():
    """
    Return a single data structure with the default phonetic data.

    Returns
    -------
    data : dict
        A dictionary with default sound features (key `features`),
        sound classes (key `classes`), and sound inventory (key `sounds`).
    """

    features = read_sound_features()
    sound_classes = read_sound_classes()
    sounds = read_sounds(features)

    data = {"features": features, "classes": sound_classes, "sounds": sounds}

    return data


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
            rule_id = int(row.pop("ID"))
            row["WEIGHT"] = float(row.get("WEIGHT", 1.0))

            rules[rule_id] = row

    return rules
