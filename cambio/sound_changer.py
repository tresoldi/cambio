# encoding: utf-8

# Import Python libraries
import re

# Import 3rd party libraries
from pyclts import TranscriptionSystem


def parse_features(text):
    """
    Parse a list of feature specifications.
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


def features2sounds(positive, negative, transsys):
    """
    Returns a list of graphemes matching positive and negative features.
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

    The regular expression string is sorted in inverse length order and
    includes disjoints.
    """

    if not transsys:
        transsys = TranscriptionSystem("bipa")

    # Get the list of sounds and sort it by inverse length, allowing the
    # regular expression engine to correctly match them. There is no need
    # for further sorting withing lenghs, such as alphabetical.
    sounds = features2sounds(positive, negative, transsys)
    sounds = sorted(sounds, key=len, reverse=True)

    # Join all the sounds in a single regular expression string'; note that
    # we *don't* add capturing parentheses here
    re_or_string = "%s" % "|".join(sounds)

    return re_or_string


def apply_rule(seq, rule, transsys, sclasses, features):
    # need to replace the longest first...
    for sclass in sorted(sclasses, key=len, reverse=True):
        rule["source"] = rule["source"].replace(sclass, sclasses[sclass])

    # TODO: add borders if necessary
    new_seq = re.sub(rule["source"], rule["target"], " %s " % seq)

    # Process tokens, consuming any feature manipulation
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

            # run fixes
            # TODO: must be much better...
            if "palatal" in descriptors and "fricative" in descriptors:
                descriptors = [
                    feature if feature != "palatal" else "alveolo-palatal"
                    for feature in descriptors
                ]

            if "alveolo-palatal" in descriptors and "fricative" in descriptors:
                descriptors.append("sibilant")
            if "alveolar" in descriptors and "fricative" in descriptors:
                descriptors.append("sibilant")

            new_name = " ".join(descriptors)
            new_sound = transsys[new_name]

            processed_tokens.append(new_sound.grapheme)

    return " ".join(processed_tokens)
