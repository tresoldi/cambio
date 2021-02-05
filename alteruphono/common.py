"""
Module with functions and values shared across different parts of the library.
"""

from typing import List, Tuple, Union

from maniphono import Segment, SoundSegment, Sound

from .model import Token, ChoiceToken, SetToken, SegmentToken, BoundaryToken


# Note that we need to return a list because in the check_match we are retuning
# not only a boolean of whether there is a match, but also the index of the
# backr eference in case there is one (added +1)
# TODO: could deal with the +1 and perhaps only do checks "is True"?
# TODO: to solve the problem of returning lists, perhaps return a match boolean
#       *and* a list of indexes?
# TODO: add type checks for `sequence` and `pattern`, perhaps casting?
def check_match(
    sequence: List[Segment], pattern: List[Token]
) -> Tuple[bool, List[Union[Segment, bool, int]]]:
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

    # Iterate over pairs of tokens from the sequence and references from the pattern,
    # building a `ret_list`. The latter will contain `False` in case there is no
    # match for a position, or either the index of the backreference or `True` in
    # case of a match.
    ret_list = []
    for token, ref in zip(sequence, pattern):
        if isinstance(ref, ChoiceToken):
            match_segment = False
            for choice in ref.choices:
                # Matches all segments, such as boundaries and sounds
                match, segment = check_match([token], [choice])
                if match:
                    match_segment = token
                    break
            ret_list.append(match_segment)
        elif isinstance(ref, SetToken):
            # Check if it is a set correspondence, which effectively works as a
            # choice here (but we need to keep track of) which set alternative
            # was matched

            alt_matches = [check_match([token], [alt])[0] for alt in ref.choices]

            if not any(alt_matches):
                ret_list.append(False)
            else:
                ret_list.append(alt_matches.index(True))
        elif isinstance(ref, SegmentToken):
            # TODO: currently working only with monosonic segments
            # If the reference segment is not partial, we can just compare `token` to
            # `ref.segment`; if it is partial, we can compare the sounds in each
            # with the `>=` overloaded operator, which also involves making sure
            # `token` itself is a segment
            if not ref.segment.sounds[0].partial:
                ret_list.append(token == ref.segment)
            else:
                if not isinstance(token, SoundSegment):
                    ret_list.append(False)
                else:
                    ret_list.append(token.sounds[0] >= ref.segment.sounds[0])
        elif isinstance(ref, Sound):
            # TODO: check how similar to the above (ref.type==segment)
            # TODO: check why it is capturing as maniphono.sound.Sound and not SoundSegment
            if not ref.partial:
                ret_list.append(token == ref)
            else:
                if not isinstance(token, SoundSegment):
                    ret_list.append(False)
                else:
                    ret_list.append(token.sounds[0] >= ref)
        elif isinstance(ref, BoundaryToken):
            ret_list.append(str(token) == "#")

    # make sure we treat zeros (that might be indexes) differently fromFalse
    # TODO: return only ret_list and have the user check?
    return all([v is not False for v in ret_list]), ret_list
