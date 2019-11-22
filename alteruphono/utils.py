# encoding: utf-8

"""
Defines auxiliary functions, structures, and data for the library.
"""

# Standard imports
import csv
import itertools
from pathlib import Path
import random
import re

# Import 3rd party libraries
from pyclts import CLTS

TRANSCRIPTION = CLTS().bipa

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
RESOURCE_DIR = Path(__file__).parent.parent / "resources"


def clean_text(text):
    """
    Cleans text, basically removing superflous spaces.
    """

    return re.sub(r"\s+", " ", text).strip()


def clean_regex(regex):
    """
    Cleans a regular expression.
    """

    return " %s " % re.sub(r"\s+", " ", regex).strip()


def parse_features(text):
    """
    Parse a list of feature constraints.

    Constraints can be definied inside optional brackets. Features are
    separated by commas, with optional spaces around them, and have a
    leading plus or minus sign (defaulting to plus).

    Parameters
    ----------
    text: string
        A string with the feature constraints specification

    Returns
    -------
    positive: list
        A list of features to be included.
    negative: list
        A list of features to be excluded.
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
    positive = []
    negative = []
    for feature in text.split(","):
        # Strip once more, as the user might add spaces next to the commas
        feature = feature.strip()

        # Obtain the positivity/negativity of the feature
        if feature[0] == "-":
            negative.append(feature[1:])
        elif feature[0] == "+":
            positive.append(feature[1:])
        else:
            positive.append(feature)

    return positive, negative


# NOTE: This function is used mostly by features2regex()
def features2sounds(positive, negative, transsys):
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

    # Iterate over all sounds in the transcription system
    sounds = []
    for sound in transsys.sounds:
        # Extract all the features of the current sound
        features = transsys[sound].name.split()

        # Check if all positive features are there
        pos_match = all(feat in features for feat in positive)

        # Check if none of the negative features are there
        neg_match = all(feat not in features for feat in negative)

        # Accept the sound if it passes both tests
        if pos_match and neg_match:
            sounds.append(sound)

    return sounds


def features2regex(positive, negative, transsys=None):
    """
    Returns a regex string for matching graphemes according to features.

    Positive and negative are lists of features as defined in the
    TranscriptionSystem.

    For example, asking for not-rounded and not high front vowels:

    >>> alteruphono.sound_changer.features2regex(["vowel", "front"], ["rounded", "high"])
    'ẽ̞ẽ̞|ẽ̞ː|ẽẽ|æ̃æ̃|ãã|a̰ːː|ḭːː|ĩĩ|ɛ̃ɛ̃|" ... "ă|e̤|ɛː|iː|aa|ɛ̯|ii|ḭ|æ|i|ɛ|e|a'

    Parameters
    ----------
    positive : list
        A list of strings with the features to be included.
    negative : list
        A list of strings with the features for be excluded.
    transsys : TranscriptionSystem
        The transcription system to be used, defaulting to BIPA.

    Returns
    -------
    re_or_string : string
        A string with the regular expression matching the requested feature
        constraints. The items are sorted in inverse length order, and
        include disjoints.
    """

    # Use the default transcription system, if none was provided
    if not transsys:
        transsys = TRANSCRIPTION

    # Get the list of sounds and sort it by inverse length, allowing the
    # regular expression engine to correctly match them. There is no need
    # for further sorting withing lenghs, such as alphabetical.
    sounds = features2sounds(positive, negative, transsys)
    sounds.sort(key=lambda item: (-len(item), item))

    # Join all the sounds in a single regular expression string'; note that
    # we *don't* add capturing parentheses here
    re_or_string = "%s" % "|".join(sounds)

    return re_or_string


# TODO: remove hard-coding of fixes, loading internal or external data
def fix_descriptors(descriptors):
    """
    Fix inconsistencies and problems with pyclts descriptors.
    """

    # Run manual fixes related to pyclts
    if "palatal" in descriptors and "fricative" in descriptors:
        # Fricative palatals are described as alveolo-palatal, so
        # replace all of them
        descriptors = [
            feature if feature != "palatal" else "alveolo-palatal"
            for feature in descriptors
        ]

    if "alveolo-palatal" in descriptors and "fricative" in descriptors:
        descriptors.append("sibilant")

    if "alveolar" in descriptors and "fricative" in descriptors:
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
        "C[+voiced]") and corresponding regular expressions as values.
    """

    if not filename:
        filename = RESOURCE_DIR / "sound_classes.tsv"
        filename = filename.as_posix()

    with open(filename) as tsvfile:
        reader = csv.DictReader(tsvfile, delimiter="\t")
        sound_classes = {
            row["sound_class"]: {
                "description": row["description"],
                "regex": features2regex(*parse_features(row["features"])),
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
    Mandatory fields are, besides a unique `id`,
    `source`, `target` and `test`, according to the
    simpler notation. A floating-point `weight` may also be specified
    (defaulting to 1.0 for all rules, in case it is not specified).

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
            rules[row["id"]] = {
                "source": re.sub(r"\s+", " ", row["source"]),
                "target": re.sub(r"\s+", " ", row["target"]),
                "weight": float(row.get("weight", 1.0)),
                "test": row["test"],
            }

    return rules


def random_choices(population, weights=None, cum_weights=None, k=1):
    """
    Return a `k` sized list of elements chosen from `population` with
    replacement and according to a list of weights.

    If a `weights` sequence is specified, selections are made according to the
    relative weights. Alternatively, if a `cum_weights` sequence is given, the
    selections are made according to the cumulative weights. For example, the
    relative weights `[10, 5, 30, 5]` are equivalent to the cumulative weights
    `[10, 15, 45, 50]`. Internally, the relative weights are converted to the
    cumulative weights before making selections, so supplying the cumulative
    weights saves work.

    This function is compatible with the random.choices() function available
    in Python's standard library from version 3.6 on. It can be replaced by
    the standard implementation once the version requirement is updated.

    Parameters
    ----------
    population: list
        A list of elements from which the element(s) will be drawn.

    weights: list
        A list of any numeric type with the relative weight of each element.
        Either `weights` or `cum_weights` must be provided.

    cum_weights: list
        A list of any numeric type with the accumulated weight of each element.
        Either `weights` or `cum_weights` must be provided.

    k: int
        The number of elements to be drawn, with replacement.

    Returns
    -------
    sample: list
        A list of elements randomly drawn according to the specified weights.
    """

    # Assert that (1) the population is not empty, (2) only one type of
    # weight information is provided.
    assert population, "Population must not be empty."
    assert not all(
        (weights, cum_weights)
    ), "Either only weights or only cumulative weights must be provided."

    # If cumulative weights were not provided, build them from `weights`.
    if not cum_weights:
        cum_weights = list(itertools.accumulate(weights))

    # Assert that the lengths of population and cumulative weights match.
    assert len(population) == len(
        cum_weights
    ), "Population and weight lengths do not match."

    # Get a random number and see in which bin it falls. We need to use this
    # logic which is a little more complex than something with randint()
    # in order to allow for floating-point weights.
    rnd = [random.uniform(0, cum_weights[-1]) for r in range(k)]
    less_than = [[cw < r for cw in cum_weights] for r in rnd]

    return [population[lt.index(False)] for lt in less_than]
