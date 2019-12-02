"""
Module implementing the forward and backward changers.
"""

# Import other library modules
from . import globals
from . import utils

# TODO: deal with custom features
def apply_modifier(grapheme, modifier):
    """
    Apply a modifier to a grapheme.
    """

    # In case of no modifier, the grapheme is obviously the same
    if not modifier:
        return grapheme

    # See if the (grapheme, modifier) combination has already been computed
    cache_key = tuple([grapheme, modifier])
    if cache_key in globals.APPLYMOD:
        return globals.APPLYMOD[cache_key]

    # Parse the provided modifier
    features = utils.parse_features(modifier)

    # Obtain the phonological descriptors for the base sound
    # TODO: consider redoing the logic, as we don't need to extract values
    #       given that those are already properly organized in the data
    # TODO: build an ipa description no matter what...
    if grapheme not in globals.SOUNDS:
        return "%s%s" % (grapheme, modifier)
    descriptors = list(globals.SOUNDS[grapheme].values())

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
            if globals.FEATURES[value] != globals.FEATURES[feature]
        ]
    descriptors += features["positive"]

    # Obtain the grapheme based on the description
    # TODO: decide if we should just memoize
    descriptors = tuple(sorted(descriptors))
    grapheme = globals.DESC2GRAPH.get(descriptors, None)
    if not grapheme:
        grapheme = utils.descriptors2grapheme(descriptors)

        # TODO: should always return, can we guarantee?
        if grapheme:
            globals.DESC2GRAPH[descriptors] = grapheme
        else:
            # TODO: better order?
            grapheme = "[%s]" % ",".join(descriptors)

    # cache
    globals.APPLYMOD[cache_key] = grapheme

    return grapheme


def forward_translate(sequence, rule):
    """
    Translate an intermediary `ante` to `post` sequence.
    """

    post_seq = []

    for entry in rule["post"]:
        if "ipa" in entry:
            post_seq.append(entry["ipa"])
        elif "back-reference" in entry:
            # Refer to `correspondence`, if specified
            # -1 as back-references as 1-based, and Python lists 0-based
            if "correspondence" in entry:
                # get the alternative index in `ante`
                # NOTE: `post_alts` has [1:-1] for the curly brackets
                # TODO: this is only working with BIPA, should we allow others?
                ante_alts = [
                    alt["ipa"]
                    for alt in rule["ante"][entry["back-reference"] - 1][
                        "alternative"
                    ]
                ]
                post_alts = rule["post"][entry["back-reference"] - 1][
                    "correspondence"
                ][1:-1].split(",")

                idx = ante_alts.index(sequence[entry["back-reference"] - 1])

                post_seq.append(post_alts[idx])
            else:
                token = sequence[entry["back-reference"] - 1]
                post_seq.append(
                    apply_modifier(token, entry.get("modifier", None))
                )
        elif "null" in entry:
            pass

    return post_seq


def check_match(sequence, pattern):
    """
    Check if a sequence matches a given pattern.
    """

    # If there is a length mismatch, it does not match by definition
    if len(sequence) != len(pattern):
        return False

    for token, ref in zip(sequence, pattern):
        if "ipa" in ref:
            ipa = apply_modifier(ref["ipa"], ref["modifier"])
            if token != ipa:
                return False
        elif "boundary" in ref:
            if token != "#":
                return False
        elif "sound_class" in ref:
            # Apply the modifier to all the items in the sound class,
            # so we can check if the `token` is actually there.
            modified = [
                apply_modifier(grapheme, ref["modifier"])
                for grapheme in globals.SOUND_CLASSES[ref["sound_class"]][
                    "graphemes"
                ]
            ]
            modified = sorted({gr for gr in modified if gr})

            if token not in modified:
                return False
        elif "alternative" in ref:
            # Check the sub-match for each alternative -- if one works, it
            # is ok
            alt_matches = [
                check_match([token], [alt]) for alt in ref["alternative"]
            ]
            if not any(alt_matches):
                return False

    return True


def forward(ante_seq, ast, no_boundaries=False):
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
        match = check_match(sub_seq, ast["ante"])
        if match:
            post_seq += forward_translate(sub_seq, ast)
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
