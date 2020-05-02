"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from pathlib import Path
import re
import unicodedata

# Import from other modules
# from . import parser
import alteruphono.parser

# Set the resource directory; this requires `zip_safe=False` in setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"


def descriptors2grapheme(descriptors, sounds):
    # make sure we can manipulate these descriptors
    descriptors = list(descriptors)

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
    desc = tuple(sorted(descriptors))
    for sound, feat_dict in sounds.items():
        # Collect all features and confirm if all are there
        # TODO: better to sort when loading the SOUNDS
        features = tuple(sorted(feat_dict.values()))
        if desc == features:
            return sound

    # TODO: fixes in case we missed
    if "breathy" in desc:
        new_desc = [v for v in desc if v != "breathy"]
        new_gr = descriptors2grapheme(new_desc, sounds)
        if new_gr:
            return "%s[breathy]" % new_gr

    if "long" in desc:
        new_desc = [v for v in desc if v != "long"]
        new_gr = descriptors2grapheme(new_desc, sounds)
        if new_gr:
            return "%sː" % new_gr

    return None


# TODO: should cache or pre-process this: if not in list, compute
def features2graphemes(feature_str, sounds):
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

    Returns
    -------
    sounds : list
        A sorted list of all the graphemes matching the requested feature
        constraints.
    """

    # Parse the feature string
    features = alteruphono.parser.parse_features(feature_str)

    # Iterate over all sounds in the transcription system
    graphemes = []
    for grapheme, sound_features in sounds.items():
        # Extract all the features of the current sound
        sound_features = list(sound_features.values())

        # Check if all positive features are there; we can skip
        # immediately if they don't match
        pos_match = all(feat in sound_features for feat in features["positive"])
        if not pos_match:
            continue

        # Check if none of the negative features are there, skipping if not
        neg_match = all(
            feat not in sound_features for feat in features["negative"]
        )
        if not neg_match:
            continue

        # The grapheme passed both tests, add it
        graphemes.append(grapheme)

    # Sort the list, first by inverse length, then alphabetically
    graphemes.sort(key=lambda item: (-len(item), item))

    return tuple(graphemes)


def read_sound_classes(sounds, filename=None):
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
        sound_classes = {}
        for row in csv.DictReader(tsvfile, delimiter="\t"):
            # GRAPHEMES can hold either a list of graphemes separated by
            # a vertical bar or a set of features that will be compiled
            # into graphemes with `sounds`
            # TODO: rename GRAPHEMES column
            # TODO: consider what to do once a `Sound` dataclass is implemented
            if row["GRAPHEMES"]:
                graphemes = tuple(
                    [
                        clear_text(grapheme)
                        for grapheme in row["GRAPHEMES"].split("|")
                    ]
                )
            else:
                graphemes = features2graphemes(row["GRAPHEMES"], sounds)

            sound_classes[row["SOUND_CLASS"]] = {
                "description": row["DESCRIPTION"],
                "features": row["FEATURES"],
                "graphemes": graphemes,
            }

    return sound_classes


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
        for row in csv.DictReader(csvfile, delimiter="\t"):
            grapheme = clear_text(row["GRAPHEME"])
            features = row["NAME"].split()

            # TODO: currently skipping over clusters and tones
            if "from" in features:
                continue
            if "tone" in features:
                continue

            descriptors = {featsys[feat]: feat for feat in features}
            sounds[grapheme] = descriptors

    return sounds


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
        features = {
            row["VALUE"]: row["FEATURE"]
            for row in csv.DictReader(tsvfile, delimiter="\t")
        }

    return features


# TODO: better rename to `load`?
# TODO: allow multiple models, per dictory, perhaps metadata in the future, validation
def read_phonetic_model():
    """
    Return a single data structure with the default phonetic data.

    Returns
    -------
    data : dict
        A dictionary with default sound features (key `features`),
        sound classes (key `classes`), and sound inventory (key `sounds`).
    """

    model = {}
    model["FEATURES"] = read_sound_features()
    model["SOUNDS"] = read_sounds(model["FEATURES"])
    model["SOUND_CLASSES"] = read_sound_classes(model["SOUNDS"])
    model["DESC2GRAPH"] = {}  # check usage
    model["APPLYMOD"] = {}  # check usage

    return model


def read_sound_changes(filename=None):
    """
    Read a list of sound changes.

    Sound changes are stored in a TSV file holding a list of sound changes.
    Mandatory fields are a unique `ID` and the `RULE` itself, plus
    the recommended `TEST_ANTE` and `TEST_POST`. A floating-point `WEIGHT`
    for sampling might also be specified, and will default to 1.0 for
    all rules if not provided.

    Parameters
    ----------
    filename : string
        Path to the TSV file holding the list of sound changes, defaulting
        to the one distributed with the library. Strings are cleaned
        upon loading, which includes Unicode normalization to the NFC form.

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
        rules = {}
        for row in csv.DictReader(csvfile, delimiter="\t"):
            rule_id = int(row.pop("ID"))
            row["RULE"] = clear_text(row["RULE"])
            row["TEST_ANTE"] = clear_text(row["TEST_ANTE"])
            row["TEST_POST"] = clear_text(row["TEST_POST"])
            row["WEIGHT"] = float(row.get("WEIGHT", 1.0))

            # TODO: remove boundary add when proper parsing is done in Model
            row["TEST_ANTE"] = "# %s #" % row["TEST_ANTE"]
            row["TEST_POST"] = "# %s #" % row["TEST_POST"]

            rules[rule_id] = row

    return rules


def clear_text(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
