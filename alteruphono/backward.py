import itertools

import maniphono

from .common import check_match


def _backward_translate(sequence, rule, match_list):
    # Collects all information we have on what was matched, in terms of back-references
    # and classes/features, from what we have in the reflex
    value = {}
    no_nulls = [token for token in rule.post if token.type != "null"]
    for post_entry, token in zip(no_nulls, sequence):
        if post_entry.type == "backref":
            # TODO: apply modifier inverse
            value[post_entry.index] = token

    # NOTE: `ante_seq` is here the modified one for reconstruction, not the one in the rule
    ante_seq = []
    for idx, (ante_entry, match) in enumerate(zip(rule.ante, match_list)):
        if ante_entry.type == "choice":
            ante_seq.append(value.get(idx, "C|V"))
        elif ante_entry.type == "set":
            ante_seq.append(value.get(idx, "C|V"))
        elif ante_entry.type == "segment":
            ante_seq.append(ante_entry.segment)

    # Depending on the type of rule that was applied, the `ante_seq` list
    # might at this point have elements expressing more than one
    # sound and expressing alternatives that need to be computed
    # with a product (e.g., `['#'], ['d'], ['i w', 'j u'], ['d'] ['#']`).
    # This correction is performed by the calling function, also allowing
    # to return a `Sequence` instead of a plain string (so that we also
    # deal with missing boundaries, etc.). We also return the unaltered,
    # original `sequence`, expressing cases where no changes were
    # applied.
    return [
        sequence,
        ante_seq,
    ]


# This method makes a copy of the original AST ante-tokens and applies
# the modifiers from the post sequence; in a way, it "fakes" the
# rule being applied, so that something like "d > @1[+voiceless]"
# is transformed in the equivalent "t > @1".
# TODO: add modifiers, as per previous implementarion
def _carry_backref_modifier(ante_token, post_token):
    # we know post_token is a backref here
    if post_token.modifier:
        if ante_token.type == "segment":  # TODO: only monosonic...
            print(ante_token, dir(ante_token))
            return maniphono.SoundSegment(
                ante_token.segment.add_fvalues(post_token.modifier)
            )
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

        match = check_match(sub_seq, post_ast)
        if len(match) == 0:
            break
        elif all(match):
            ante_seqs.append(_backward_translate(sub_seq, rule, match))
            idx += len(post_ast)
        else:
            # TODO: remove these nested lists if possible
            ante_seqs.append([[post_seq[idx]]])
            idx += 1

        if idx == len(post_seq):
            break

    # Computes the product of possibilities
    # TODO: organize and do it properly
    ante_seqs = [candidate for candidate in itertools.product(*ante_seqs)]

    ret = []
    for i, a in enumerate(ante_seqs):
        chain = list(itertools.chain.from_iterable(a))
        chain = [t for t in chain if str(t) != "#"]
        ret.append(chain)

    return ret
