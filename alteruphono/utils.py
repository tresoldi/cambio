# encoding: utf-8

# Standard imports
import csv
import itertools
from os import path
import random
import re

# Import from namespace
from . import sound_changer

# Set the resource directory; this is safe as we already added
# `zip_safe=False` to setup.py
_RESOURCE_DIR = path.join(path.dirname(path.dirname(__file__)), "resources")


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
        filename = path.join(_RESOURCE_DIR, "features_bipa.tsv")

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
        filename = path.join(_RESOURCE_DIR, "sound_changes.tsv")

    # Read the raw notation adding leading and trailing spaces to source
    # and target, as well as adding capturing parentheses to source (if
    # necessary) and replacing back-reference notation in targets
    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        rules = {}
        for row in reader:
            rules[row["id"]] = {
                "source": re.sub("\s+", " ", row["source"]),
                "target": re.sub("\s+", " ", row["target"]),
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
    assert len(population) > 0, "Population must not be empty."
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


def random_change(rules):
    # collect ids ands weights
    population = list(rules.keys())
    weights = [rule["weight"] for rule in rules.values()]

    return rules[random_choices(population, weights)[0]]
