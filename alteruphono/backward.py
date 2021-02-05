import itertools
from typing import List, Union

from maniphono import SegSequence, Sound, SoundSegment, Segment

from .common import check_match
from .model import Token, BackRefToken, EmptyToken, BoundaryToken, SegmentToken, ChoiceToken, SetToken
from .parser import Rule


def _backward_translate(sequence: List[Segment], rule: Rule, match_info: List[Union[Segment, bool, int]]):
    # Make a copy of the ANTE as a "recons"tructed sequence; this will later be
    # modified by back-references from the sequence that was matched
    recons = []
    set_index = []
    for idx, t in enumerate(rule.ante):
        if isinstance(t, BoundaryToken):
            recons.append(t)
        elif isinstance(t, SegmentToken):
            recons.append(t)
        elif isinstance(t, ChoiceToken):
            recons.append(t)
        elif isinstance(t, SetToken):
            recons.append(t)
            set_index.append(idx)

    # Remove empty tokens that might be in the POST rule (and that are obviously
    # missing from the matched subtring) and iterate over pairs of POST tokens and
    # matched sequence tokens, filling "recons"tructed seq
    no_empty = [token for token in rule.post if not isinstance(token, EmptyToken)]
    for post_token, seq_token, match in zip(no_empty, sequence, match_info):
        if isinstance(post_token, BackRefToken):

            # build modifier to be "inverted"
            # TODO: move this operation to maniphono
            recons[post_token.index] = seq_token
            if post_token.modifier:
                modifiers = []
                for mod in post_token.modifier.split(","):
                    if mod[0] == "-":
                        modifiers.append("+" + mod[1:])
                    elif mod[0] == "+":
                        modifiers.append("-" + mod[1:])
                    else:
                        modifiers.append("-" + mod)

                # TODO: fix this horrible hack that uses graphemes to circumvent difficulties with copies
                gr = str(seq_token)
                snd = Sound(gr)
                snd += ",".join(modifiers)
                recons[post_token.index] = SoundSegment([snd])

        elif isinstance(post_token, SetToken):
            # grab the index of the next set
            idx = set_index.pop(0)
            recons[idx] = recons[idx].choices[match]

    return [sequence, recons]


# This method makes a copy of the original AST ante-tokens and applies
# the modifiers from the post sequence; in a way, it "fakes" the
# rule being applied, so that something like "d > @1[+voiceless]"
# is transformed in the equivalent "t > @1".
def _carry_backref_modifier(ante_token: Token, post_token: Token) -> Token:
    """
    Internal function for applying the modifier of a back-reference to its source.

    @param ante_token:
    @param post_token:
    @return:
    """
    # we know post_token is a backref here
    if post_token.modifier:
        if  isinstance(ante_token, SegmentToken):  # TODO: only
            # monosonic...
            if len(ante_token.segment.sounds) != 1:
                raise ValueError("only monosonic")

            # make a copy
            x = ante_token.segment.sounds[0]
            return x + post_token.modifier

        # TODO: can we join choice and set into a single signature?
        elif isinstance(ante_token, SetToken):
            for choice in ante_token.choices:
                choice.add_modifier(post_token.modifier)

        elif isinstance(ante_token, ChoiceToken):
            for choice in ante_token.choices:
                choice.add_modifier(post_token.modifier)

    # return non-modified
    return ante_token


# TODO: make sure it works with repeated backreferences, such as "V s > @1 z @1",
# which we *cannot* have mapped only as "V z V"
def backward(post_seq: SegSequence, rule: Rule) -> List[SegSequence]:
    # Compute the `post_ast`, applying modifiers and skipping nulls
    post_ast = [token for token in rule.post if not isinstance(token, EmptyToken)]

    post_ast = [
        token
        if not isinstance(token, BackRefToken)
        else _carry_backref_modifier(rule.ante[token.index], token)
        for token in post_ast
    ]

    # Iterate over the sequence, checking if subsequences match the specified `post`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    idx = 0
    ante_seqs = []
    while True:
        # TODO: implement a better subsetting of sequence, as a normal python Sequence
        sub_seq: List[Segment] = [post_seq[i] for i in range(idx, min(len(post_seq), idx + len(post_ast)))]

        match, match_list = check_match(sub_seq, post_ast)

        if len(match_list) == 0:
            break

        if match:
            ante_seqs.append(_backward_translate(sub_seq, rule, match_list))
            idx += len(post_ast)
        else:
            # TODO: remove these nested lists if possible
            ante_seqs.append([[post_seq[idx]]])
            idx += 1

        if idx == len(post_seq):
            break

    # TODO: organize and do it properly
    ante_seqs = [
        SegSequence(
            list(itertools.chain.from_iterable(candidate)), boundaries=True
        )
        for candidate in itertools.product(*ante_seqs)
    ]

    # Due to difficulties in dealing with rules composed only of boundaries (especially
    # when they involve deletions, like `C > :null: / _ #`, we need to make sure no
    # proto-form with internal boundaries are generated here. This code might not seem
    # so elegant, but makes it easier to understand what we are doing, and allows us
    # to follow the established practices of using a single symbol ("#") for both
    # leading and trailing boundaries (compare with regular expressions with "^" and "$")
    filtered = []
    for seq in ante_seqs:
        # Check for internal boundaries
        if not any([isinstance(token, BoundaryToken) for token in seq[1:-1]]):
            filtered.append(seq)

    # TODO: sort using representation?
    # TODO: must take set, as the rule might lead to the same pattern
    return filtered
