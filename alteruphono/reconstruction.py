# encoding: "utf-8"

"""
Defines class for building reconstruction replacements from ASTs.
"""

# Import `alteruphono` modules
from . import compiler

class ReconsAutomata(compiler.Compiler):
    """
    Compiler for compiling ASTs into sets of reconstruction replacements.
    """

    def __init__(self, debug=False):
        """
        Entry point for the `Graph` class.
        """

        # Call super()
        super().__init__(debug)
