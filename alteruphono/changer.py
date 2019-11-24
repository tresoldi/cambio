# __init__.py
# encoding: utf-8

"""
Module implementing functions for applying back and forward changes.
"""

import itertools
import re

# TODO: general renaming of source/target to left/right?

# TODO: boundary addition should be optional
# TODO: should keep track of boundary addition in case it happens
def _prepare_sequence(sequence):
    """
    Internal preprocessing function.
    """

    # Strip spaces and add boundary marks if needed
    sequence = sequence.strip()
    if sequence[0] != "#":
        sequence = "# %s" % sequence
    if sequence[-1] != "#":
        sequence = "%s #" % sequence

    # Strip multiple spaces and add leading and trailing spaces for
    # regex matching
    sequence = " %s " % re.sub("\s+", " ", sequence)

    return sequence


# TODO: deal with boundaries when missing
def apply_forward(sequence, source, target):
    # TODO: refactor, import at top, etc.
    from . import utils

    features = utils.read_sound_features()

    sequence = _prepare_sequence(sequence)

    # TODO: make sure it is applying to all matches
    sequence = re.sub(source, target, sequence)

    # Process tokens one by one, consuming any feature manipulation
    # TODO: note on why it is done here, move to .to_regex, etc.
    processed_tokens = []
    for token in sequence.split():
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
            descriptors = utils.TRANSCRIPTION[grapheme].name.split()

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

            # Fix any problem in the descriptors
            descriptors = utils.fix_descriptors(descriptors)

            # Ask the transcription system for a new grapheme based in the
            # adapted description
            processed_tokens.append(
                utils.TRANSCRIPTION[" ".join(descriptors)].grapheme
            )

    # Join the processed tokens
    # TODO: remove boundaries if they were added
    return " ".join(processed_tokens).strip()


# TODO: move to `regex` library later, with overlapping findall
# or, at least, use the library to show that the are overlapping
# matches and the rule is ambiguous
# TODO: what about overlapping only in the spaces for segmentation?
# should we duplicate those? -- an alternative is replace all spaces by
# double spaces in sequences and rules, with the exception of leading and
# trailing ones in rules (but it sounds a terrible hack)
def apply_backward(sequence, source, target):
    sequence = _prepare_sequence(sequence)

    # Collecting all the potential proto-forms is, in this engine,
    # a bit tricker given that we have to go around the intention of
    # regular expressions. As we don't allow overlapping matches due to
    # their inherent ambiguity, what we do is to first collect a list
    # of all starting and ending indexes of any match, along with the
    # string actually matched (which can vary from match to match).
    matches = [
        {
            "source": match.group(0),
            "target": re.sub(source, target, match.group(0)),
            "start": match.start(),
            "end": match.end(),
        }
        for match in re.finditer(source, sequence)
    ]

    # Collect list of alternatives iterating over matches
    prev_idx = 0
    alt = []
    for match in matches:
        alt.append([sequence[prev_idx : match["start"]]])
        alt.append([match["source"], match["target"]])
        prev_idx = match["end"]
    alt.append([sequence[prev_idx:]])

    # build alternatives
    # TODO: remove boundaries if necessary
    sequences = sorted(
        ["".join(subseqs).strip() for subseqs in itertools.product(*alt)]
    )

    return sequences
