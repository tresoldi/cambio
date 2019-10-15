# encoding: utf-8

# Import Python libraries
import re

# Import 3rd party libraries
from pyclts import TranscriptionSystem

# Import from the namespace
from . import utils

# Default sound classes, features, and transcription system (some variables
# are only populated at the end of this script, after all functions
# have been defined)
_SOUND_CLASSES = None
_SOUND_FEATURES = None
_TRANSCRIPTION = TranscriptionSystem("bipa")

# TODO: add support for partial match with our notation
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
def features2sounds(positive, negative, transsys=None):
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
        The transcription system to be used, defaulting to BIPA.

    Returns
    -------
    sounds : list
        A list of strings with all the graphemes matching the requested
        feature constraints.
    """

    # Use the default transcription system, if none was provided
    if not transsys:
        transsys = _TRANSCRIPTION

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
        transsys = _TRANSCRIPTION

    # Get the list of sounds and sort it by inverse length, allowing the
    # regular expression engine to correctly match them. There is no need
    # for further sorting withing lenghs, such as alphabetical.
    sounds = features2sounds(positive, negative, transsys)
    sounds = sorted(sounds, key=len, reverse=True)

    # Join all the sounds in a single regular expression string'; note that
    # we *don't* add capturing parentheses here
    re_or_string = "%s" % "|".join(sounds)

    return re_or_string


# TODO: have transsys, sclasses, and features in a single dict
# TODO: deal with repeated spaces?
# TODO: memoization
# TODO: finish documentation
# TODO: comment on borders in `seq`
def apply_rule(seq, rule, transsys=None, sclasses=None, features=None):
    """
    Apply a regular expression rule to a sequence.
    """

    # Use defaults, if not provided
    if not transsys:
        transsys = _TRANSCRIPTION
    if not sclasses:
        sclasses = _SOUND_CLASSES
    if not features:
        features = _SOUND_FEATURES

    # Make a copy of the rule source and apply all class replacements
    # according to the provided definitions.
    # NOTE: We need to replace in inverse length order to avoid partial
    #       matching of class names (which can be longer than one character)
    source = rule["source"]
    for sclass in sorted(sclasses, key=len, reverse=True):
        source = source.replace(sclass, sclasses[sclass])

    # Add word borders if necessary, along with leading and trailing spaces
    if "#" not in seq:
        seq = " # %s # " % seq.strip()
    else:
        seq = " %s " % seq

    # Apply regular expression to sequence; leading and trailing spaces
    # are added to correct manipulation of boundaries
    # TODO: add word borders if necessary
    # TODO: add syllable boundaries if necessary/requested
    # TODO: add support for custom function replacements
    new_seq = re.sub(source, rule["target"], seq)

    # Process tokens one by one, consuming any feature manipulation
    processed_tokens = []
    for token in new_seq.split():
        # If we find brackets in the tokens, consume the feature manipulation;
        # otherwise, just copy the token.
        # TODO: Move to a list comprehension, isolating the feature
        #       manipulation?
        if "[" not in token:
            processed_tokens.append(token)
        else:
            # TODO: We are here assuming that all operations are positive
            #       (i.e., a feature is added or at most replaced), and as
            #       such we are not even extracting the plus or minus sign.
            #       This is forbidding some common operation like removing
            #       aspiration and labialization (which can still be modelled
            #       as direct phoneme mapping, i.e. 'ph -> p'). VERY URGENT!!!
            # TODO: This is also assuming that a single feature is
            #       manipulated; we should allow for more feature operations.
            # TODO: could use or reuse parse_features()?
            grapheme, operation = token[:-1].split("[")
            if operation[0] in "+-":
                op_operator, op_feature = operation[0], operation[1:]
            else:
                op_operator, op_feature = "+", operation

            # Obtain the phonological descriptors for the base sound
            descriptors = transsys[grapheme].name.split()

            # Obtain the feature class for the current `op_feature` (the
            # feature for the current value, in common phonological parlance)
            # and remove all `descriptors` matching it (if any), so that we
            # can append our own descriptor/of_feature, build a new name,
            # and generate a new sound/grapheme from that.
            descriptors = [
                value
                for value in descriptors
                if features[value] != features[op_feature]
            ]
            descriptors.append(op_feature)

            # Run manual fixes related to pyclts
            # TODO: move an independent function, possibly loading external data
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

            # Ask the transcription system for a new grapheme based in the
            # adapted description
            new_sound = transsys[" ".join(descriptors)]

            processed_tokens.append(new_sound.grapheme)

    # Join, also removing borders
    return " ".join([tok for tok in processed_tokens if tok != "#"])


# Load default sound classes and features, if not loaded by this time
_SOUND_CLASSES = utils.read_sound_classes()
_SOUND_FEATURES = utils.read_features()
