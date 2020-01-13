"""
Module implementing the forward and backward changers.
"""

import itertools

# Import other library modules
from . import globals
from . import utils

# TODO: deal with custom features
def apply_modifier(grapheme, modifier, inverse=False):
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

    # Invert features if requested
    # TODO: deal with custom features
    if inverse:
        features["positive"], features["negative"] = (
            features["negative"],
            features["positive"],
        )

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

    # TODO: rename `entry` to `token`? also below
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


# TODO: comment as we return two options, because it might or not apply...
def backward_translate(sequence, rule):
    # Collect all information we have on what was matched,
    # in terms of back-references and classes/features,
    # from what we have in the reflex
    # TODO: could we get a set of potential sources when
    # a modifier is applied (for example, different places of
    # articulation) and get the merge with with source rule
    # (such only labials?)
    value = {}
    no_nulls = [token for token in rule["post"] if "null" not in token]
    for post_entry, token in zip(no_nulls, sequence):
        if "back-reference" in post_entry:
            idx = post_entry["back-reference"]
            value[idx - 1] = apply_modifier(
                token, post_entry.get("modifier", None), inverse=True
            )

    # TODO: note that ante_seq is here the modified one
    ante_seq = []
    for idx, ante_entry in enumerate(rule["ante"]):
        if "ipa" in ante_entry:
            ante_seq.append(ante_entry["ipa"])
        elif "alternative" in ante_entry:
            # build alternative string, for cases when deleted
            # TODO: modifiers etc
            alt_string = "|".join(
                [
                    alt.get("ipa", alt.get("sound_class", "#"))
                    for alt in ante_entry["alternative"]
                ]
            )
            ante_seq.append(value.get(idx, alt_string))
        elif "sound_class" in ante_entry:
            ante_seq.append(value.get(idx, ante_entry["sound_class"]))

    # NOTE: returning `sequence` for the unalterted ("did not apply")
    # option -- should it be added outisde this function? TODO
    return [" ".join(sequence), " ".join(ante_seq)]


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


# TODO: deal with boundaries
def backward(post_seq, ast):
    if post_seq[0] != "#":
        post_seq = ["#"] + post_seq
    if post_seq[-1] != "#":
        post_seq = post_seq + ["#"]

    # remove nulls from `post`, as they would be deleted;
    # then, replace back-references
    def _add_modifier(entry1, entry2):
        v = entry1.copy()
        v["modifier"] = entry2.get("modifier", None)
        return v

    post_ast = [token for token in ast["post"] if "null" not in token]
    post_ast = [
        token
        if "back-reference" not in token
        else _add_modifier(ast["ante"][token["back-reference"] - 1], token)
        for token in post_ast
    ]

    idx = 0
    ante_seqs = []
    while True:
        sub_seq = post_seq[idx : idx + len(post_ast)]
        match = check_match(sub_seq, post_ast)
        if match:
            ante_seqs.append(backward_translate(sub_seq, ast))
            idx += len(post_ast)
        else:
            ante_seqs.append([post_seq[idx]])
            idx += 1

        if idx == len(post_seq):
            break

    # Make sure everything is a list, so we don't iterate over the
    # characters of a string; then, make a list of all possible strings
    def rem_bound(seq):
        if seq[0] == "#":
            seq = seq[1:]
        if seq[-1] == "#":
            seq = seq[:-1]

        return seq.strip()

    ante_seqs = [
        " ".join(candidate) for candidate in itertools.product(*ante_seqs)
    ]
    ante_seqs = [rem_bound(seq) for seq in ante_seqs]

    return ante_seqs
