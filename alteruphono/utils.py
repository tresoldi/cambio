"""
Defines auxiliary functions, structures, and data for the library.
"""

# Python standard libraries imports
import csv
from pathlib import Path
import re
import unicodedata

# Import from other modules
from alteruphono.old_parser import parse_features

# Set the resource directory; this requires `zip_safe=False` in setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"

# TODO: should be computed and not coded, see comments in model.py
# TODO: compile the feature description to a Features object
HARD_CODED_INVERSE_MODIFIER = {
    ('ɸ', (('fricative', '+'),)): "p",
    ("t", (("voiceless", "+"),)): "d",
    ("f", (("voiceless", "+"),)): "v",
    ("ɶ", (("rounded", "+"),)): "a",
    ("ĩ", (("nasalized", "+"),)): "i",
    ("t", (("alveolar", "+"),)): "k",
    ("c", (("palatal", "+"),)): "k",
    ("g", (("voiced", "+"),)): "k",
    ("k", (("velar", "+"),)): "p",
    ("ɲ", (("palatal", "+"),)): "n",
    ("d", (("voiced", "+"),)): "t",
    ("b", (("voiced", "+"),)): "p",
    ("b̪",( ("stop", "+"),)): "v",
    ("g", (("stop", "+"),)): "ɣ",
    ("x", (("voiceless", "+"),)): "ɣ",
    ("d̪", (("stop", "+"),)): "ð",
    ("b", (("stop", "+"),)): "β",
    ("t̠", (("post-alveolar", "+"),)): "k",
    ("k", (("voiceless", "+"),)): "g",
}

# Custom package errors, for fuzzing, testing, etc.
class AlteruPhonoError(Exception):
    pass

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
    features = parse_features(feature_str)

    # Iterate over all sounds in the transcription system
    graphemes = []
    for grapheme, sound_features in sounds.items():
        # Extract all the features of the current sound
        sound_features = list(sound_features.values())

        # Check if all positive features are there; we can skip
        # immediately if they don't match
        pos_match = all(feat in sound_features for feat in features.positive)
        if not pos_match:
            continue

        # Check if none of the negative features are there, skipping if not
        neg_match = all(
            feat not in sound_features for feat in features.negative
        )
        if not neg_match:
            continue

        # The grapheme passed both tests, add it
        graphemes.append(grapheme)

    # Sort the list, first by inverse length, then alphabetically
    graphemes.sort(key=lambda item: (-len(item), item))

    return tuple(graphemes)


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

            rules[rule_id] = row

    return rules


def clear_text(text):
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text
