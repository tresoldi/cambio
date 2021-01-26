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
        return False, [False] * len(sequence)

    # Deal with boundaries: if a boundary is in first position in the pattern, it
    # can only match the first position in the sequence; if it is in the last position
    # in the pattern, it can only match the last position in the sequence. There would
    # be other ways to deal with this issue, including using different symbols for
    # leading/trailing boundary, but it is simpler to just treat this here.
    #    print("PAT", [t.type for t in pattern])
    #    print("SEQ", [t.type for t in sequence])
    #
    #    if pattern[0].type == "boundary" and sequence[0].type != "boundary":
    #        print(">> FALSE")
    #        return False, [False]*len(sequence)
    #    if pattern[-1].type == "boundary" and sequence[-1].type != "boundary":
    #        print(">> FALSE")
    #        return False, [False]*len(sequence)

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
        if ref.type == "choice":
            match_segment = False
            for choice in ref.choices:
                # manually check for boundaries, as the problematic check above willfail
                if choice.type == "boundary":
                    if token.type == "boundary":
                        match_segment = "#"
                        break
                else:
                    match, segment = check_match([token], [choice])
                    if match:
                        match_segment = segment
                        break

            ret_list.append(match_segment)
        elif ref.type == "set":
            # Check if it is a set correspondence, which effectively works as a
            # choice here (but we need to keep track of) which set alternative
            # was matched

            alt_matches = [check_match([token], [alt])[0] for alt in ref.choices]

            if not any(alt_matches):
                ret_list.append(False)
            else:
                ret_list.append(alt_matches.index(True))
        elif ref.type == "segment":
            # TODO: currently working only with monosonic segments
            # If the reference segment is not partial, we can just compare `token` to
            # `ref.segment`; if it is partial, we can compare the sounds in each
            # with the `>=` overloaded operator, which also involves making sure
            # `token` itself is a segment
            if not ref.segment.sounds[0].partial:
                ret_list.append(token == ref.segment)
            else:
                if not isinstance(token, maniphono.SoundSegment):
                    ret_list.append(False)
                else:
                    ret_list.append(token.sounds[0] >= ref.segment.sounds[0])
        elif ref.type == "boundary":
            ret_list.append(str(token) == "#")

        # Append to the return list, so that we carry extra information like which
        # element of a set matched. Most of the time, this list will be composed
        # only of booleans.
        # ret_list.append(ret)

    # make sure we treat zeros (that might be indexes) differently fromFalse
    # TODO: return only ret_list and have the user check?
    return all([v is not False for v in ret_list]), ret_list
