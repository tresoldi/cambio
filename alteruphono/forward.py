"""
Module with functions for forward reconstruction.
"""

from .common import check_match

# TODO: rename match_list to match_info
def _forward_translate(sequence, rule, match_list):
    post_seq = []

    # Build a list of indexes from `match_list`, which will be used in sequence in
    # case of sets. This list is the return value from `check_match()`, which will
    # hold `True` value in all cases except for backreference matches, when it will
    # hold the index of the backreference shifted by one.
    # NOTE: yes, we do need to check with type() because, as the values might be
    # our custom types, the `isinstace(idx, int)` will fail as we implement __add__
    indexes = [idx for idx in match_list if type(idx) == int]

    # Iterate over all entries
    for entry in rule.post:
        # Note that this will, as intended, skip over `null`s
        if entry.type == "segment":
            post_seq.append(entry.segment)
        elif entry.type == "set":
            # The -1 in the `match` index is there to offset the +1 applied by
            # `check_match()`, so that we can differentiate False from zero.
            idx = indexes.pop(0)
            post_seq.append(entry.choices[idx].segment)
        elif entry.type == "backref":
            # TODO: deal with "correspondence"
            # Copy the backreference, adding the modifier (even if empty, the
            # phonomodel would only skip over it)
            token = sequence[entry.index]
            token.add_fvalues(entry.modifier)
            post_seq.append(token)

    return post_seq


def forward(ante_seq, rule):
    """
    Apply forward transformation to a sequence given a rule.
    """

    # Cache the lengths of `ante_seq` and `rule.ante` for speed
    len_seq = len(ante_seq)
    len_rule = len(rule.ante)

    # Iterate over the sequence, checking if subsequences match the specified `ante`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    idx = 0
    post_seq = []
    while True:
        sub_seq = ante_seq[idx : idx + len_rule]

        match, match_info = check_match(sub_seq, rule.ante)
        if match:
            post_seq += _forward_translate(sub_seq, rule, match_info)
            idx += len_rule
        else:
            post_seq.append(ante_seq[idx])
            idx += 1

        if idx == len_seq:
            break

    # TODO: post_seq should be a sequence, and we should take care of setting
    # .boudaries if necessary

    return post_seq
