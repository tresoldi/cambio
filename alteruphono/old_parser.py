"""
Sound change parser.

This module holds the functions, methods, and data for parsing sound
changes from strings. While it was first specified as a formal grammar,
by means of a Parsing Expression Grammar, it is now implemented "manually",
mostly using simple string manipulations and regular expressions with
no look-behinds. The decision to change was motivated by the growing
complexity of the grammar that had to hold a mutable set of graphemes
and for the plans of expansion/conversion to different programming
languages, trying to diminish the dependency on Python.
"""

# Import Python standard libraries
import re

# Import package
import alteruphono.utils
from alteruphono.ast import AST

# TODO: rename to collect features or something in these lines
def parse_features(modifier):
    """
    Returns
    -------
    features : Features
        A `Features` object, with attributes `.positive` (a list of strings),
        `negative` (a list of strings), and `custom` (a dictionary with
        strings as keys and strings as values).
    """

    # TODO: write properly, currently without custom
    # TODO: rename AST to something more general, out attrib class
    # TODO: rename feature.feature to feature.name or something similar
    positive, negative = [], []
    for feature in modifier:
        if feature.value == "+":
            positive.append(feature.feature)
        elif feature.value == "-":
            negative.append(feature.feature)

    # TODO: while sort? to cache/hash?
    return AST({"positive":sorted(positive),
    "negative":sorted(negative),
    "custom":[]})


# TODO: make just a dictionary? a data class? a named tuple?
class Rule:
    def __init__(self, rule_text, ast):
        self.source = rule_text
        self.ante = ast.ante
        self.post = ast.post
