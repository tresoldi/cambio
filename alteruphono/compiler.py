# encoding: utf-8

"""
Defines the Compiler class for iterating over ASTs.
"""

# Import Python libraries
import logging

logging.basicConfig(level=logging.INFO)


class Compiler:
    """
    Defines the `Compiler` class.

    This is used for different ways of iterating over ASTs, trying to
    resuse as much code as possible.
    """

    def __init__(self, debug):
        """
        Entry point for the class.

        The `debug` flag must be used in all classes deriving `Compiler`.
        """

        # pylint: disable=unused-argument,no-self-use
        self.debug = debug

    def compile(self, ast):
        """
        Main compiler method.

        This method is supposed to take any `ast`, including partial ones,
        and return a value appropriate for the class. In case of natural
        language mapping, for example, it will return a textual description
        of the provided AST. The function in intended to call itself
        recusively at different levels.
        """

        # pylint: disable=unused-argument,no-self-use
        if self.debug:
            logging.info(ast)

        if ast.get("ipa"):
            ret = self.compile_ipa(ast)
        elif ast.get("sound_class"):
            ret = self.compile_sound_class(ast)
        elif ast.get("boundary"):
            ret = self.compile_boundary(ast)
        elif ast.get("empty"):
            ret = self.compile_empty(ast)
        elif ast.get("back_ref"):
            ret = self.compile_back_ref(ast)
        elif ast.get("feature_desc"):
            ret = self.compile_feature_desc(ast)
        elif ast.get("alternative"):
            ret = self.compile_alternative(ast)
        elif ast.get("sequence"):
            ret = self.compile_sequence(ast)
        elif ast.get("source") and ast.get("target"):
            ret = self.compile_start(ast)

        # Single return point for the entire function
        return ret

    def compile_ipa(self, ast):
        """
        Compile an `ipa` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_sound_class(self, ast):
        """
        Compile a `sound_class` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_boundary(self, ast):
        """
        Compile a `boundary` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_empty(self, ast):
        """
        Compile an `empty` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_back_ref(self, ast):
        """
        Compile a `back_ref` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_feature_desc(self, ast):
        """
        Compile a `feature_desc` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_alternative(self, ast):
        """
        Compile an `alternative` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_sequence(self, ast):
        """
        Compile a `sequence` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented

    def compile_context(self, ast):
        """
        Compile a `context` ast.

        In most cases, the method should return a tuple of two variables,
        the first for the context preceding the position and the second for
        the one following it.
        """
        # pylint: disable=unused-argument,no-self-use

        return NotImplemented

    def compile_start(self, ast):
        """
        Compile a `start` ast.
        """
        # pylint: disable=unused-argument,no-self-use
        return NotImplemented
