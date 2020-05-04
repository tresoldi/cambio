# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package
__version__ = "0.3"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono import utils
from alteruphono.parser import Rule
from alteruphono.model import Model
from alteruphono.sequence import Sequence

# Define essential function for forward and backward
def forward(sequence, rule):
    model = Model()
    return model.forward(sequence, Rule(rule))


def backward(sequence, rule):
    model = Model()
    return model.backward(sequence, Rule(rule))
