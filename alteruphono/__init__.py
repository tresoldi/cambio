# __init__.py

"""
__init__ module for the `alteruphono` package.
"""

# Version of the alteruphono package
__version__ = "0.4"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono.model import Boundary, Focus, Empty, BackRef, Choice, Set, SegmentToken
from alteruphono.parser import Rule, parse_rule, parse_seq_as_rule
from alteruphono.common import check_match
from alteruphono.forward import forward
from alteruphono.backward import backward
