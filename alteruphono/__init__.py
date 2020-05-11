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
from alteruphono.parser import parser
from alteruphono.parser.ast import AST
from alteruphono.model import Model, Rule
from alteruphono.sequence import Sequence

# Define essential function for forward and backward
def forward(sequence, rule):
    model = Model()

    if isinstance(rule, str):
        rule = Rule(rule)

    return model.forward(sequence, rule)


def backward(sequence, rule):
    model = Model()

    if isinstance(rule, str):
        rule = Rule(rule)

    return model.backward(sequence, rule)
