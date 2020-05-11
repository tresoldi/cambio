# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package
__version__ = "0.4"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono import utils
from alteruphono.parser import Parser, AST
from alteruphono.model import Model
from alteruphono.sequence import Sequence
from alteruphono.rule import Rule, make_rule


# Define essential function for forward and backward
def forward(sequence, rule):
    """
    Simple function for performing forward transformation.
    """

    model = Model()

    if isinstance(rule, str):
        parser = Parser()
        rule = make_rule(rule, parser)

    return model.forward(sequence, rule)


def backward(sequence, rule):
    """
    Simple function for performing backward transformation.
    """

    model = Model()

    if isinstance(rule, str):
        parser = Parser()
        rule = make_rule(rule, parser)

    return model.backward(sequence, rule)
