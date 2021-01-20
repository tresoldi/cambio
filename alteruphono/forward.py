from .common import check_match


def _forward_translate(sequence, rule, match_list):
    post_seq = []

    # Build a list of indexes from `match_list`, which will be used in sequence in
    # case of sets
    indexes = [v for v in match_list if v is not True]

    # Iterate over all entries
    for entry in rule.post:
        # Note that this will, as intended, skip over `null`s
        # TODO: deal with sound classes
        if entry.type == "segment":
            post_seq.append(entry.segment)
        elif entry.type == "set":
            # The -1 in the `match` index is there to offset the +1 applied by
            # `check_match()`, so that we can differentiate False from zero.
            idx = indexes.pop(0) - 1
            post_seq.append(entry.choices[idx].segment)
        elif entry.type == "backref":
            # TODO: deal with "correspondence"
            # TODO: apply any modifier

            token = sequence[entry.index]
            if entry.modifier:
                # TODO: drop-in solution for the +
                mod = entry.modifier.replace("+", "")
                token.sounds[0] += mod

            post_seq.append(token)

    return post_seq


def forward(ante_seq, rule):
    """
    Apply forward transformation to a sequence given a rule.
    """

    iter_seq = list(ante_seq)

    # Iterate over the sequence, checking if subsequences match the specified `ante`.
    # We operate inside a `while True` loop because we don't allow overlapping
    # matches, and, as such, the `idx` might be updated either with +1 (looking for
    # the next position) or with the match length. While the whole logic could be
    # performed with a more Python list comprehension, for easier conversion to
    # other languages it is better to keep it as dumb loop.
    idx = 0
    post_seq = []
    while True:
        sub_seq = iter_seq[idx : idx + len(rule.ante)]
        match = check_match(sub_seq, rule.ante)
        if all(match):
            post_seq += _forward_translate(sub_seq, rule, match)
            idx += len(rule.ante)
        else:
            post_seq.append(iter_seq[idx])
            idx += 1

        if idx == len(iter_seq):
            break

    # TODO: post_seq should be a sequence, and we should take care of setting
    # .boudaries if necessary

    return post_seq
