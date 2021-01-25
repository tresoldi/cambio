"""
Module with functions and values shared across different parts of the library.
"""

import maniphono

# Note that we need to return a list because in the check_match we are retuning
# not only a boolean of whether there is a match, but also the index of the
# backr eference in case there is one (added +1)
# TODO: could deal with the +1 and perhaps only do checks "is True"?
# TODO: to solve the problem of returning lists, perhaps return a match boolean
#       *and* a list of indexes?
# TODO: add type checks for `sequence` and `pattern`, perhaps casting?
def check_match(sequence, pattern):
    """
    Check if a sequence matches a given pattern.
    """

    # If there is a length mismatch, it does not match by definition. Note that
    # standard forward and backward operations will never pass sequences and patterns
    # mismatching in length, but it is worth to keep this check as the method can
    # be invoked directly by users, and the length checking is much faster than
    # performing the entire loop.
    if len(sequence) != len(pattern):
        return [False] * len(sequence)

    # Iterate over pairs of tokens from the sequence and references from the pattern,
    # building a `ret_list`. The latter will contain `False` in case there is no
    # match for a position, or either the index of the backreference or `True` in
    # case of a match.
    # TODO: we could return immediately when a `[False]` is found, instead of
    #       compiling the entire list -- at least it would be faster. No logic depends
    #       on the length of the return list when there is a `False`, but perhaps we
    #       can have just a non-default flag to compile the full list if really wished.
    ret_list = []
    for token, ref in zip(sequence, pattern):
        ret = True
        if ref.type == "choice":
            # Check the sub-match for each alternative; if the alternative is a grapheme,
            # carry any modifier. We need to pass lists recursively to `check_match`
            # because the choice could have multiple segments.
            # TODO: carry modifiers?
            #        alt_matches = [
            #            all(check_match([token], [choice])) for choice in ref.choices
            #        ]

            alt_matches = [check_match([token], [choice])[0] for choice in ref.choices]

            # TODO: address negation
            if not any(alt_matches):
                ret = False
            else:
                ret = alt_matches.index(True) + 1
        elif ref.type == "set":
            # Check if it is a set correspondence, which effectively works as a
            # choice here (but we need to keep track of) which set alternative
            # was matched
            alt_matches = [all(check_match([token], [alt])) for alt in ref.choices]

            # As in this case we need to know which alternative in set had a match,
            # instead of returning a boolean we will return the index of such
            # alternative. To make the logic more transparent, we shift the index
            # of one unit, so that no match will be returned as a zero.
            # Note that this code, following PEG principles, will always the return
            # the index of the first matched element, even if there are more than one.
            if not any(alt_matches):
                ret = False
            else:
                ret = alt_matches.index(True) + 1
        elif ref.type == "segment":
            # TODO: currently working only with monosonic segments
            # If the reference segment is not partial, we can just compare `token` to
            # `ref.segment`; if it is partial, we can compare the sounds in each
            # with the `>=` overloaded operator, which also involves making sure
            # `token` itself is a segment
            if not ref.segment.sounds[0].partial:
                ret = token == ref.segment
            else:
                if not isinstance(token, maniphono.SoundSegment):
                    ret = False
                else:
                    ret = token.sounds[0] >= ref.segment.sounds[0]
        elif ref.type == "boundary":
            ret = str(token) == "#"

        # Append to the return list, so that we carry extra information like which
        # element of a set matched. Most of the time, this list will be composed
        # only of booleans.
        ret_list.append(ret)

    return ret_list
