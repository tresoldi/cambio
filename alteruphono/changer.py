# __init__.py
# encoding: utf-8

"""
Module implementing functions for applying back and forward changes.
"""

import itertools
import re

# TODO: general renaming of source/target to left/right?

# TODO: boundary addition should be optional
# TODO: should keep track of boundary addition in case it happens
def _prepare_sequence(sequence):
    """
    Internal preprocessing function.
    """

    # Strip spaces and add boundary marks if needed
    sequence = sequence.strip()
    if sequence[0] != "#":
        sequence = "# %s" % sequence
    if sequence[-1] != "#":
        sequence = "%s #" % sequence

    # Strip multiple spaces and add leading and trailing spaces for
    # regex matching
    sequence = " %s " % re.sub("\s+", " ", sequence)

    return sequence


# TODO: deal with boundaries when missing
def apply_forward(sequence, source, target):
    sequence = _prepare_sequence(sequence)

    sequence = re.sub(source, target, sequence)

    return sequence.strip()


# TODO: move to `regex` library later, with overlapping findall
# or, at least, use the library to show that the are overlapping
# matches and the rule is ambiguous
# TODO: what about overlapping only in the spaces for segmentation?
# should we duplicate those? -- an alternative is replace all spaces by
# double spaces in sequences and rules, with the exception of leading and
# trailing ones in rules (but it sounds a terrible hack)
def apply_backward(sequence, source, target):
    sequence = _prepare_sequence(sequence)

    # Collecting all the potential proto-forms is, in this engine,
    # a bit tricker given that we have to go around the intention of
    # regular expressions. As we don't allow overlapping matches due to
    # their inherent ambiguity, what we do is to first collect a list
    # of all starting and ending indexes of any match, along with the
    # string actually matched (which can vary from match to match).
    matches = [
        {
            "source": match.group(0),
            "target": re.sub(source, target, match.group(0)),
            "start": match.start(),
            "end": match.end(),
        }
        for match in re.finditer(source, sequence)
    ]

    # Collect list of alternatives iterating over matches
    prev_idx = 0
    alt = []
    for match in matches:
        alt.append([sequence[prev_idx : match["start"]]])
        alt.append([match["source"], match["target"]])
        prev_idx = match["end"]
    alt.append([sequence[prev_idx:]])

    # build alternatives
    sequences = sorted(
        ["".join(subseqs) for subseqs in itertools.product(*alt)]
    )

    return sequences
