"""
Module implementing the forward and backward changers.
"""

# Import other library modules
from . import utils

# TODO: should accept other things besides graphemes
# TODO: deal with custom features
def apply_modifier(grapheme, modifier, phdata):
    """
    Apply a modifier to a grapheme.
    """

    # In case of no modifier, the grapheme is obviously the same
    if not modifier:
        return grapheme

    # Parse the provided modifier
    features = utils.parse_features(modifier)

    # Obtain the phonological descriptors for the base sound
    # TODO: consider redoing the logic, as we don't need to extract values
    #       given that those are already properly organized in the data
    # TODO: build an ipa description no matter what...
    if grapheme not in phdata['sounds']:
        return "%s%s" % (grapheme, modifier)
    descriptors = list(phdata["sounds"][grapheme].values())

    # Remove requested features
    # TODO: write tests
    descriptors = [
        value for value in descriptors if value not in features["negative"]
    ]

    # Remove any descriptor from a feature type we are changing, and add
    # all positive descriptors
    for feature in features["positive"]:
        descriptors = [
            value
            for value in descriptors
            if phdata["features"][value] != phdata["features"][feature]
        ]
    descriptors += features["positive"]

    # Fix any problem in the descriptors
    descriptors = utils.fix_descriptors(descriptors)

    # Ask the transcription system for a new grapheme based in the
    # adapted description
    # TODO: remove dependency
    if 'consonant' in descriptors:
        descriptors = [v for v in descriptors if v != 'consonant'] + ['consonant']
    if 'vowel' in descriptors:
        descriptors = [v for v in descriptors if v != 'vowel'] + ['vowel']

    return utils.TRANSCRIPTION[" ".join(descriptors)].grapheme


def forward_translate(sequence, post, phdata):
    """
    Translate an intermediary `ante` to `post` sequence.
    """

    post_seq = []

    for entry in post:
        if "ipa" in entry:
            post_seq.append(entry["ipa"])
        elif "back-reference" in entry:
            # -1 as back-references as 1-based, and Python lists 0-based
            token = sequence[entry["back-reference"] - 1]
            post_seq.append(
                apply_modifier(token, entry.get("modifier", None), phdata)
            )
        elif "null" in entry:
            pass

    return post_seq


def check_match(sequence, pattern, phdata):
    """
    Check if a sequence matches a given pattern.
    """

    # If there is a length mismatch, it does not match by definition
    if len(sequence) != len(pattern):
        return False

    for token, ref in zip(sequence, pattern):
        if "ipa" in ref:
            ipa = apply_modifier(ref["ipa"], ref["modifier"], phdata)
            if token != ipa:
                return False
        elif "boundary" in ref:
            if token != "#":
                return False
        elif "sound_class" in ref:
            # Apply the modifier to all the items in the sound class,
            # so we can check if the `token` is actually there.
            modified = [
                apply_modifier(grapheme, ref['modifier'], phdata)
                for grapheme in phdata['classes'][ref['sound_class']]['graphemes']
            ]
            modified = sorted(set([gr for gr in modified if gr]))

            if token not in modified:
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


def forward(ante_seq, ast, phdata, no_boundaries=False):
    """
    Apply a sound change in forward direction.

    The function will temporarily add boundaries to the sequence, during
    execution, unless it is explictly told not to with the `no_boundaries`
    flag.

    Parameters
    ----------
    ante_seq : list
        A list with the sequence the rule is being applied to.
    ast : dict
        A dictionary with the `ante` and `post` asts.
    phdata : dict
        A dictionary with the phonological data to be used.
    no_boundaries : bool
        Don't add boundaries to the sequence if missing (default:False)

    Returns
    -------
    post_seq : list
        The sound sequence resulting from the sound change execution.
    """

    # Add boundaries to the sequence if necessary, and keep track of the
    # decision.
    added_lead_bound, added_trail_bound = False, False
    if not no_boundaries:
        if ante_seq[0] != "#":
            ante_seq.insert(0, "#")
            added_lead_bound = True
        if ante_seq[-1] != "#":
            ante_seq.append("#")
            added_trail_bound = True

    # Iterate over the sequence, checking if subsequences match the
    # specified `ante`. While this could, once more, be perfomed with a
    # list comprehension, for easier conversion to Go it is better to
    # keep it as a dumb loop.
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

    # Remove boundaries if they were added
    if added_lead_bound:
        post_seq = post_seq[1:]
    if added_trail_bound:
        post_seq = post_seq[:-1]

    return post_seq
