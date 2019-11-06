# __init__.py

# Version of the alteruphono package
__version__ = "0.0.1dev"
__author__ = "Tiago Tresoldi"
__email__ = "tresoldi@shh.mpg.de"

# Build the namespace
from alteruphono import compiler
from alteruphono import convert
from alteruphono import utils
from alteruphono.grammar import SOUND_CHANGEParser as Parser

# from alteruphono.sound_changer import apply_rule
