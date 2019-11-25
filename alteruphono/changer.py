"""
Module implementing the forward and backward changers.
"""

# Import Python standard libraries
from collections import defaultdict

# Import other library modules
from . import utils


def apply_modifier(grapheme, modifier, phdata):
    # In case of no modifier, the grapheme is obsviously the same
    if not modifier:
        return grapheme

    # TODO: We are here assuming that all operations are positive
    #       (i.e., a feature is added or at most replaced), and as
    #       such we are not even extracting the plus or minus sign.
    #       This is forbidding some common operations like removing
    #       aspiration and labialization (which can still be modelled
    #       as direct phoneme mapping, i.e., 'ph > p'). VERY URGENT!
    # TODO: This is also assuming that a single feature is
    #       manipulated; we should allow for more feature operations.
    features = utils.parse_features(modifier)

    # Obtain the phonological descriptors for the base sound
    # TODO: use `sounds`
    descriptors = utils.TRANSCRIPTION[grapheme].name.split()

    # Obtain the feature class for the current `op_feature` (the
    # feature for the current value, in common phonological parlance)
    # and remove all `descriptors` matching it (if any), so that we
    # can append our own descriptor/op_feature, build a new name,
    # and generate a new sound/grapheme from that.
    descriptors = [
        value
        for value in descriptors
        if phdata["features"][value]
        != phdata["features"][features["positive"][0]]
    ]
    descriptors += features["positive"]

    # Fix any problem in the descriptors
    descriptors = utils.fix_descriptors(descriptors)

    # Ask the transcription system for a new grapheme based in the
    # adapted description
    # TODO: remove dependency
    return utils.TRANSCRIPTION[" ".join(descriptors)].grapheme


def forward_translate(sequence, post, phdata):
    post_seq = []

    for entry in post:
        if "ipa" in entry:
            post_seq.append(entry["ipa"])
        elif "back-reference" in entry:
            # -1 as back-references as 1-based, and Python lists 0-based
            # TODO: modifiers!
            token = sequence[entry["back-reference"] - 1]
            post_seq.append(
                apply_modifier(token, entry.get("modifier", None), phdata)
            )
        elif "null" in entry:
            pass
        else:
            # TODO: default, for now just copy
            post_seq.append(entry)

    return post_seq


def check_match(sequence, pattern, phdata):
    # If there is a length mismatch, it does not match by definition
    if len(sequence) != len(pattern):
        return False

    for token, ref in zip(sequence, pattern):
        if "ipa" in ref:
            if token != ref["ipa"]:
                return False
        elif "boundary" in ref:
            if token != "#":
                return False
        elif "sound_class" in ref:
            if token not in phdata["classes"][ref["sound_class"]]["graphemes"]:
                return False
        elif "alternative" in ref:
            # Check the sub-match for each alternative -- if one works, it
            # is ok
            alt_matches = [
                check_match([token], [alt], phdata)
                for alt in ref["alternative"]
            ]
            if not any(alt_matches):
                return False

    return True


# TODO: note about sequences as lists
def forward(ante_seq, ast, phdata):
    # Add boundaries to the sequence if necessary
    # TODO: decide if we keep track of this decision, removing the boundaries
    # before returning
    if ante_seq[0] != "#":
        ante_seq.insert(0, "#")
    if ante_seq[-1] != "#":
        ante_seq.append("#")

    # Iterate over the sequence, checking if subsequences match the
    # specified `ante`. While this could, once more, be perfomed with a
    # list comprehension, for easier conversion to Go it is better to
    # keep it as a dumb loop.
    # TODO: deal with alternatives that can include more than one segment,
    #       which means that we would need to capture more than `len(ante)`
    idx = 0
    post_seq = []
    while True:
        sub_seq = ante_seq[idx : idx + len(ast["ante"])]
        match = check_match(sub_seq, ast["ante"], phdata)
        if match:
            post_seq += forward_translate(sub_seq, ast["post"], phdata)
            idx += len(ast["ante"])
        else:
            post_seq.append(ante_seq[idx])
            idx += 1

        if idx == len(ante_seq):
            break

    return post_seq
