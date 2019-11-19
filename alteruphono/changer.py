# __init__.py
# encoding: utf-8

"""
Module implementing functions for applying back and forward changes.
"""

import re

# TODO: deal with boundaries when missing
def apply_forward(seq, source, target):
    # prepare `seq`
    seq = " %s " % re.sub("\s+", " ", seq.strip())

    seq = re.sub(source, target, seq)

    return seq.strip()


def apply_backward(seq, source, target):
    pass
