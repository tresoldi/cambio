import itertools
import copy

import maniphono

from .common import check_match


def _backward_translate(sequence, rule, match_info):
    # Make a copy of the ANTE as a "recons"tructed sequence; this will later be
    # modified by back-references from the sequence that was matched
    recons = []
    set_index = []
    for idx, t in enumerate(rule.ante):
        if t.type == "boundary":
            recons.append(t)
        elif t.type == "segment":
            recons.append(t)
        elif t.type == "choice":
            recons.append(t)
        elif t.type == "set":
            recons.append(t)
            set_index.append(idx)

    # Remove empty tokens that might be in the POST rule (and that are obviously
    # missing from the matched subtring) and iterate over pairs of POST tokens and
    # matched sequence tokens, filling "recons"tructed seq
    no_empty = [token for token in rule.post if token.type != "empty"]
    for post_token, seq_token, match in zip(no_empty, sequence, match_info):
        if post_token.type == "backref":
            recons[post_token.index] = seq_token
        elif post_token.type == "set":
            # grab the index of the next set
            idx = set_index.pop(0)
            recons[idx] = recons[idx].choices[match]

    return [sequence, recons]


# This method makes a copy of the original AST ante-tokens and applies
# the modifiers from the post sequence; in a way, it "fakes" the
# rule being applied, so that something like "d > @1[+voiceless]"
# is transformed in the equivalent "t > @1".
# TODO: add modifiers, as per previous implementarion
def _carry_backref_modifier(ante_token, post_token):
    # we know post_token is a backref here
    if post_token.modifier:
        if ante_token.type == "segment":  # TODO: only monosonic...
            if len(ante_token.segment.sounds) != 1:
                raise ValueError("only monosonic")

            # make a copy
            x = ante_token.segment.sounds[0]
            return x + post_token.modifier

        elif ante_token.type in ["set", "choice"]:
            # TODO: implement
            return ante_token

    # return non-modified
    return ante_token


# TODO: make sure it works with repeated backreferences, such as "V s > @1 z @1",
# which we *cannot* have mapped only as "V z V"
def backward(post_seq, rule):
    # Compute the `post_ast`, applying modifiers and skipping nulls
    post_ast = [token for token in rule.post if token.type != "empty"]

    post_ast = [
        token
        if token.type != "backref"
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
        # TODO: address comment from original implementation
        sub_seq = post_seq[idx : idx + len(post_ast)]

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
        maniphono.Sequence(
            list(itertools.chain.from_iterable(candidate)), boundaries=True
        )
        for candidate in itertools.product(*ante_seqs)
    ]

    return ante_seqs
