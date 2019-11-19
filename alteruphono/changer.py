# __init__.py
# encoding: utf-8

"""
Module implementing functions for applying back and forward changes.
"""

import re

def apply_forward(seq, source, target):
    seq = re.replace(source, target, seq)

    return seq

def apply_backward(seq, source, target):
    pass
